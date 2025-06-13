"""
Queue worker for processing any type of job.

This module handles Redis queue processing with rate limiting, retry logic, 
and error handling for any job type that implements the BaseJob interface.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from src.queue.clients import ClientContainer
from src.queue.jobs.factory import JobFactory
from src.queue.rate_limiter import RateLimiter
from src.queue.service import QueueService
from src.utils.config import Config

logger = logging.getLogger(__name__)


class Worker:
    """Worker that processes any job type from Redis queues."""
    
    def __init__(self, config: Config) -> None:
        self.config = config
        self.queue_service = QueueService(config.redis_url)
        self.clients = ClientContainer(config)
        self.running = False
        self.worker_task: Optional[asyncio.Task] = None
        
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self._setup_rate_limiters()
        
        logger.info("Worker initialized")
    
    def _setup_rate_limiters(self) -> None:
        """Setup rate limiters for different job types."""
        tweet_schedule = self.config.get_tweet_schedule()
        
        # Very conservative rate limiting to avoid spamming Twitter
        self.rate_limiters["tweet"] = RateLimiter(
            max_per_day=tweet_schedule["max_tweets_per_day"],
            max_per_hour=1,  # Only 1 tweet per hour max
            min_interval_minutes=tweet_schedule["min_interval_minutes"]
        )
    
    async def start(self) -> None:
        if self.running:
            logger.warning("Worker is already running")
            return
        
        try:
            await self.queue_service.connect()
            
            self.running = True
            self.worker_task = asyncio.create_task(self._worker_loop())
            
            logger.info("✅ Worker started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start Worker: {e}", exc_info=True)
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        logger.info("Shutting down Worker...")
        
        self.running = False
        
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        if self.queue_service:
            await self.queue_service.disconnect()
        
        logger.info("Worker shutdown complete")
    
    async def _worker_loop(self) -> None:
        logger.info("Starting worker loop")
        
        while self.running:
            try:
                job_data = await self._get_next_job()
                
                if job_data:
                    await self._process_job(job_data)
                else:
                    retry_jobs = await self.queue_service.get_retry_jobs(1)
                    if retry_jobs:
                        logger.info("Processing retry job")
                        await self._process_job(retry_jobs[0])
                    else:
                        await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                logger.info("Worker loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(60)
        
        logger.info("Worker loop ended")
    
    async def _get_next_job(self) -> Optional[Dict[str, Any]]:
        for priority in [1, 2, 3, 4]:
            queue_name = f"jobs_priority_{priority}"
            
            try:
                result = await self.queue_service.redis.brpop(queue_name, timeout=1)
                
                if result:
                    _, job_json = result
                    job_data = json.loads(job_json)
                    logger.info(f"Got job {job_data.get('job_id')} from {queue_name}")
                    return job_data
                    
            except Exception as e:
                logger.error(f"Error getting job from {queue_name}: {e}")
        
        return None
    
    async def _process_job(self, job_data: Dict[str, Any]) -> None:
        job_id = job_data.get("job_id", "unknown")
        job_type = job_data.get("job_type", "unknown")
        
        logger.info(f"Processing job {job_id}: {job_type}")
        
        try:
            job = JobFactory.create_job(job_data, self.config, self.clients)
            
            rate_limiter = self._get_rate_limiter(job.get_rate_limit_key())
            if not rate_limiter.can_execute():
                logger.debug(f"Rate limit exceeded for {job.get_rate_limit_key()}, adding to retry queue")
                await self._handle_failed_job(job_data, "Rate limit exceeded")
                return
            
            success = await job.execute()
            
            if success:
                rate_limiter.record_execution()
                logger.info(f"✅ Successfully executed job {job_id}")
            else:
                await self._handle_failed_job(job_data, "Job execution returned False")
                
        except ValueError as e:
            logger.error(f"Invalid job {job_id}: {e}")
            await self._handle_failed_job(job_data, str(e))
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
            await self._handle_failed_job(job_data, str(e))
    
    def _get_rate_limiter(self, rate_limit_key: str) -> RateLimiter:
        if rate_limit_key not in self.rate_limiters:
            # Very conservative defaults for any new job types
            self.rate_limiters[rate_limit_key] = RateLimiter(
                max_per_day=10,  # Very low daily limit
                max_per_hour=1,  # Only 1 per hour
                min_interval_minutes=60  # Minimum 1 hour between executions
            )
            logger.info(f"Created conservative rate limiter for {rate_limit_key}")
        
        return self.rate_limiters[rate_limit_key]
    
    async def _handle_failed_job(self, job_data: Dict[str, Any], error_msg: str) -> None:
        job_id = job_data.get("job_id", "unknown")
        retry_count = job_data.get("retry_count", 0)
        max_retries = 1
        
        logger.warning(f"Job {job_id} failed: {error_msg} (retry {retry_count}/{max_retries})")
        
        if retry_count < max_retries:
            retry_delay = 300  # 5 minute delay for retry (much longer)
            job_data["retry_count"] = retry_count + 1
            job_data["retry_after"] = (datetime.now() + timedelta(seconds=retry_delay)).isoformat()
            job_data["last_error"] = error_msg
            
            await self.queue_service.redis.lpush("jobs_retry", json.dumps(job_data))
            logger.info(f"Job {job_id} added to retry queue, will retry in {retry_delay}s")
        else:
            job_data["final_error"] = error_msg
            job_data["failed_at"] = datetime.now().isoformat()
            
            await self.queue_service.redis.lpush("jobs_dead_letter", json.dumps(job_data))
            logger.error(f"Job {job_id} moved to dead letter queue after {max_retries} retries")
    
    async def get_worker_stats(self) -> Dict[str, Any]:
        """Get worker and rate limiter statistics."""
        stats = {
            "running": self.running,
            "supported_job_types": JobFactory.get_supported_job_types(),
            "rate_limiters": {}
        }
        
        for key, limiter in self.rate_limiters.items():
            stats["rate_limiters"][key] = limiter.get_stats()
        
        return stats 