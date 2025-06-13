"""
Job factory for creating typed jobs from parameters.
"""

import logging
from typing import Any, Dict, Type, Tuple

from .base import BaseJob, BaseJobParams
from .tweet_job import TweetJob, TweetJobParams

logger = logging.getLogger(__name__)


class JobFactory:
    """Factory for creating jobs from parameters with type safety."""
    
    _job_registry: Dict[str, Tuple[Type[BaseJob], Type[BaseJobParams]]] = {
        "tweet": (TweetJob, TweetJobParams),
    }
    
    @classmethod
    def create_job(cls, job_data: Dict[str, Any], config: Any, clients: Any) -> BaseJob:
        """
        Create a job from parameters with validation.
        
        Args:
            job_data: Raw job parameters from Redis
            config: Application configuration
            clients: Client dependencies
            
        Returns:
            Validated job instance ready for execution
            
        Raises:
            ValueError: If job_type is unknown or validation fails
        """
        job_type = job_data.get("job_type")
        
        if job_type not in cls._job_registry:
            raise ValueError(f"Unknown job type: {job_type}")
        
        job_class, params_class = cls._job_registry[job_type]
        
        try:
            params = params_class(**job_data)
            job = job_class(params, config, clients)
            logger.debug(f"Created {job_type} job with params: {params}")
            return job
        except Exception as e:
            logger.error(f"Failed to create {job_type} job: {e}")
            raise ValueError(f"Invalid job parameters for {job_type}: {e}") from e
    
    @classmethod
    def register_job_type(
        cls, 
        job_type: str, 
        job_class: Type[BaseJob], 
        params_class: Type[BaseJobParams]
    ) -> None:
        """Register a new job type."""
        cls._job_registry[job_type] = (job_class, params_class)
        logger.info(f"Registered job type: {job_type}")
    
    @classmethod
    def get_supported_job_types(cls) -> list[str]:
        """Get list of supported job types."""
        return list(cls._job_registry.keys()) 