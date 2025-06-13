"""
Base job interface for the generic worker system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class BaseJobParams(BaseModel):
    """Base parameters for all job types."""
    job_type: str
    priority: int = Field(default=3, ge=1, le=4)
    created_at: Optional[str] = None


class BaseJob(ABC):
    """Base class for all job types."""
    
    def __init__(self, params: BaseJobParams, config: Any, clients: Any) -> None:
        self.params = params
        self.config = config
        self.clients = clients
    
    @abstractmethod
    async def execute(self) -> bool:
        """Execute the job and return success status."""
        pass
    
    @abstractmethod
    def get_rate_limit_key(self) -> str:
        """Get the rate limiting key for this job type."""
        pass
    
    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration for this job type."""
        return {
            "max_retries": 3,
            "backoff_multiplier": 2,
            "base_delay_seconds": 60
        } 