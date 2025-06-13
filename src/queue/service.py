"""
Redis queue service for tweet job processing.

This module handles Redis queue operations for tweet jobs with priority support.
"""

import json
import logging
from typing import Any, Dict, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class QueueService:
    """Redis-based queue service for tweet jobs."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379") -> None:
        """Initialize the queue service."""
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        logger.info(f"QueueService initialized with URL: {redis_url}")
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            # Test the connection
            await self.redis.ping()
            logger.info("✅ Connected to Redis successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    async def add_tweet_job(
        self, 
        content: str, 
        priority: int = 3, 
        tweet_type: str = "manual",
        **kwargs: Any
    ) -> str:
        """
        Add a tweet job to the Redis queue.
        
        Args:
            content: Tweet content
            priority: Priority level (1=urgent, 2=high, 3=normal, 4=low)
            tweet_type: Type of tweet (manual, token_launch, etc.)
            **kwargs: Additional job data
            
        Returns:
            Job ID for tracking
        """
        if not self.redis:
            raise RuntimeError("Redis not connected. Call connect() first.")
        
        # Create job data
        job_data = {
            "content": content,
            "priority": priority,
            "tweet_type": tweet_type,
            "timestamp": kwargs.get("timestamp"),
            **kwargs
        }
        
        # Generate job ID
        job_id = await self.redis.incr("tweet_job_counter")
        job_data["job_id"] = str(job_id)
        
        # Queue name based on priority
        queue_name = f"tweets_priority_{priority}"
        
        # Add to Redis list (LPUSH adds to front)
        await self.redis.lpush(queue_name, json.dumps(job_data))
        
        logger.info(f"✅ Added tweet job {job_id} to {queue_name}: {content[:50]}...")
        return str(job_id)
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics about all queues."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        
        stats = {
            "total_jobs": 0,
            "queues": {},
            "total_processed": await self.redis.get("tweet_job_counter") or "0"
        }
        
        # Check each priority queue
        for priority in [1, 2, 3, 4]:
            queue_name = f"tweets_priority_{priority}"
            length = await self.redis.llen(queue_name)
            stats["queues"][queue_name] = length
            stats["total_jobs"] += length
        
        return stats
    
    async def peek_queue(self, priority: int = 3, count: int = 5) -> list[Dict[str, Any]]:
        """
        Peek at jobs in a specific priority queue without removing them.
        
        Args:
            priority: Priority queue to peek at
            count: Number of jobs to peek at
            
        Returns:
            List of job data dictionaries
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")
        
        queue_name = f"tweets_priority_{priority}"
        
        # LRANGE gets items without removing them (0 = start, count-1 = end)
        raw_jobs = await self.redis.lrange(queue_name, 0, count - 1)
        
        jobs = []
        for raw_job in raw_jobs:
            try:
                job_data = json.loads(raw_job)
                jobs.append(job_data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode job data: {e}")
        
        return jobs
    
    async def clear_queue(self, priority: Optional[int] = None) -> int:
        """
        Clear jobs from queue(s).
        
        Args:
            priority: Specific priority queue to clear, or None for all queues
            
        Returns:
            Number of jobs cleared
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")
        
        total_cleared = 0
        
        if priority is not None:
            # Clear specific priority queue
            queue_name = f"tweets_priority_{priority}"
            cleared = await self.redis.delete(queue_name)
            total_cleared += cleared
            logger.info(f"Cleared {cleared} jobs from {queue_name}")
        else:
            # Clear all priority queues
            for p in [1, 2, 3, 4]:
                queue_name = f"tweets_priority_{p}"
                cleared = await self.redis.delete(queue_name)
                total_cleared += cleared
            logger.info(f"Cleared {total_cleared} jobs from all queues")
        
        return total_cleared 