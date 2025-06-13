"""
Rate limiter for controlling job execution frequency per job type.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for a specific job type."""
    
    def __init__(
        self, 
        max_per_day: int, 
        max_per_hour: int = None, 
        min_interval_minutes: int = 0
    ) -> None:
        self.max_per_day = max_per_day
        self.max_per_hour = max_per_hour or max_per_day
        self.min_interval = timedelta(minutes=min_interval_minutes)
        
        self.last_execution_time: datetime = None
        self.daily_count = 0
        self.hourly_count = 0
        self.last_hour_reset = datetime.now().replace(minute=0, second=0, microsecond=0)
        self.last_daily_reset = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    def can_execute(self) -> bool:
        """Check if execution is allowed based on rate limits."""
        self._reset_counters()
        
        now = datetime.now()
        
        if self.daily_count >= self.max_per_day:
            logger.debug(f"Daily limit reached: {self.daily_count}/{self.max_per_day}")
            return False
        
        if self.hourly_count >= self.max_per_hour:
            logger.debug(f"Hourly limit reached: {self.hourly_count}/{self.max_per_hour}")
            return False
        
        if self.last_execution_time and self.min_interval.total_seconds() > 0:
            time_since_last = now - self.last_execution_time
            if time_since_last < self.min_interval:
                remaining = self.min_interval - time_since_last
                logger.debug(f"Minimum interval not met, waiting {remaining.total_seconds():.0f}s")
                return False
        
        return True
    
    def record_execution(self) -> None:
        """Record a successful execution."""
        self.last_execution_time = datetime.now()
        self.daily_count += 1
        self.hourly_count += 1
        logger.debug(f"Recorded execution: daily={self.daily_count}, hourly={self.hourly_count}")
    
    def _reset_counters(self) -> None:
        """Reset daily and hourly counters if needed."""
        now = datetime.now()
        
        if now.date() > self.last_daily_reset.date():
            self.daily_count = 0
            self.last_daily_reset = now.replace(hour=0, minute=0, second=0, microsecond=0)
            logger.debug("Daily counter reset")
        
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        if current_hour > self.last_hour_reset:
            self.hourly_count = 0
            self.last_hour_reset = current_hour
            logger.debug("Hourly counter reset")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limiter statistics."""
        self._reset_counters()
        return {
            "daily_count": self.daily_count,
            "max_per_day": self.max_per_day,
            "hourly_count": self.hourly_count,
            "max_per_hour": self.max_per_hour,
            "last_execution": self.last_execution_time.isoformat() if self.last_execution_time else None,
            "can_execute": self.can_execute(),
        } 