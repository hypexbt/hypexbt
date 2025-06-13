"""
Tweet job implementation for posting regular tweets.
"""

import logging
from typing import List, Literal, Optional, Any

from pydantic import Field

from .base import BaseJob, BaseJobParams

logger = logging.getLogger(__name__)


class TweetJobParams(BaseJobParams):
    """Parameters for tweet jobs."""
    job_type: Literal["tweet"] = "tweet"
    content: str = Field(min_length=1, max_length=280)
    media_ids: Optional[List[str]] = None


class TweetJob(BaseJob):
    """Job for posting tweets via Twitter API."""
    
    def __init__(self, params: TweetJobParams, config, clients) -> None:
        super().__init__(params, config, clients)
        self.twitter_client = clients.twitter
    
    async def execute(self) -> bool:
        """Execute the tweet job."""
        try:
            self.twitter_client.post_tweet(
                self.params.content, 
                self.params.media_ids
            )
            logger.info(f"Posted tweet: {self.params.content[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return False
    
    def get_rate_limit_key(self) -> str:
        """Get rate limiting key for tweets."""
        return "tweet"
    
    def get_retry_config(self) -> dict:
        """Get retry configuration for tweet jobs."""
        return {
            "max_retries": 3,
            "backoff_multiplier": 2,
            "base_delay_seconds": 60
        }
    
    @classmethod
    async def add_to_queue(
        cls,
        queue_service: Any,
        content: str,
        priority: int = 3,
        media_ids: Optional[List[str]] = None,
        **kwargs: Any
    ) -> str:
        """
        Create and add a tweet job to the queue.
        
        Args:
            queue_service: Queue service instance
            content: Tweet content
            priority: Priority level (1=urgent, 2=high, 3=normal, 4=low)
            media_ids: Optional media IDs to attach
            **kwargs: Additional parameters
            
        Returns:
            Job ID for tracking
        """
        job_params = TweetJobParams(
            content=content,
            media_ids=media_ids,
            **kwargs
        )
        
        return await queue_service.add_job(
            job_params.model_dump(),
            priority=priority
        ) 