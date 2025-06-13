"""
Configuration module for the hypexbt Twitter bot.

This module handles loading and managing configuration from environment variables.
"""

import logging
import os

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """
    Configuration manager for the application.
    """

    def __init__(self, env_file: str = None):
        """
        Initialize the configuration.

        Args:
            env_file: Path to the .env file.
        """
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        self._validate_config()

    @property
    def log_level(self) -> str:
        """Get the logging level."""
        return os.getenv("LOG_LEVEL", "INFO").upper()

    @property
    def redis_url(self) -> str:
        """Get the Redis URL."""
        return os.getenv("REDIS_URL", "redis://localhost:6379")

    def _validate_config(self):
        """Validate that required configuration is present."""
        required_vars = [
            "X_API_KEY",
            "X_API_SECRET",
            "X_BEARER_TOKEN",
            "X_ACCESS_TOKEN",
            "X_ACCESS_TOKEN_SECRET",
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            logger.warning(f"Missing required environment variables: {missing_vars}")

    def get_twitter_credentials(self) -> dict[str, str]:
        """Get Twitter API credentials."""
        return {
            "api_key": os.getenv("X_API_KEY", ""),
            "api_secret": os.getenv("X_API_SECRET", ""),
            "bearer_token": os.getenv("X_BEARER_TOKEN", ""),
            "access_token": os.getenv("X_ACCESS_TOKEN", ""),
            "access_token_secret": os.getenv("X_ACCESS_TOKEN_SECRET", ""),
        }

    def get_api_endpoints(self) -> dict[str, str]:
        """Get API endpoint configurations."""
        return {
            "hyperliquid": os.getenv("HL_API_URL", "https://api.hyperliquid.xyz"),
            "coingecko": os.getenv("COINGECKO_API", "https://api.coingecko.com/api/v3"),
        }

    def get_tweet_schedule(self) -> dict[str, int]:
        """Get tweet scheduling configuration."""
        return {
            "min_tweets_per_day": int(os.getenv("MIN_TWEETS_PER_DAY", "10")),
            "max_tweets_per_day": int(os.getenv("MAX_TWEETS_PER_DAY", "20")),
            "min_interval_minutes": int(os.getenv("MIN_INTERVAL_MINUTES", "30")),
            "max_interval_minutes": int(os.getenv("MAX_INTERVAL_MINUTES", "180")),
            "active_hours_start": int(os.getenv("ACTIVE_HOURS_START", "0")),
            "active_hours_end": int(os.getenv("ACTIVE_HOURS_END", "23")),
        }

    def get_content_distribution(self) -> dict[str, int]:
        """Get content distribution percentages."""
        return {
            "hyperliquid_news": int(os.getenv("HYPERLIQUID_NEWS_PCT", "15")),
            "token_launches": int(os.getenv("TOKEN_LAUNCHES_PCT", "20")),
            "token_graduations": int(os.getenv("TOKEN_GRADUATIONS_PCT", "20")),
            "trading_signals": int(os.getenv("TRADING_SIGNALS_PCT", "15")),
            "daily_stats": int(os.getenv("DAILY_STATS_PCT", "15")),
            "token_fundamentals": int(os.getenv("TOKEN_FUNDAMENTALS_PCT", "15")),
        }

    @property
    def use_live_twitter(self) -> bool:
        """Check if live Twitter API should be used."""
        return os.getenv("USE_LIVE_TWITTER", "false").lower() in ("true", "1", "yes", "on")
