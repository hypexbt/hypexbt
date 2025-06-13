#!/usr/bin/env python3
"""
Test script to verify queue integration works end-to-end.
"""

import asyncio
import logging
from src.utils.config import Config
from src.queue.service import QueueService
from src.queue.jobs.tweet_job import TweetJob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_queue_integration():
    """Test the complete queue integration."""
    logger.info("🧪 Testing queue integration...")
    
    config = Config()
    queue_service = QueueService(config.redis_url)
    
    try:
        await queue_service.connect()
        logger.info("✅ Connected to Redis")
        
        # Add a test tweet job
        job_id = await TweetJob.add_to_queue(
            queue_service,
            content="Testing the queue system! 🚀 This is a test tweet.",
            priority=1  # High priority for testing
        )
        
        logger.info(f"✅ Added tweet job: {job_id}")
        
        # Check queue stats
        stats = await queue_service.get_queue_stats()
        logger.info(f"📊 Queue stats: {stats}")
        
        # Peek at the job
        jobs = await queue_service.peek_queue(priority=1, count=1)
        if jobs:
            logger.info(f"👀 Job in queue: {jobs[0]}")
        else:
            logger.warning("❌ No jobs found in queue")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise
    finally:
        await queue_service.disconnect()
        logger.info("🔌 Disconnected from Redis")


if __name__ == "__main__":
    asyncio.run(test_queue_integration()) 