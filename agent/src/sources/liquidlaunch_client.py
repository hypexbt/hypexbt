"""
LiquidLaunch API client module for the hypexbt Twitter bot.

This module handles interactions with LiquidLaunch APIs to fetch token launch
and graduation data.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any

from src.messaging.twitter_client import TwitterClient
from src.utils.config import Config

logger = logging.getLogger(__name__)


class LiquidLaunchClient:
    """
    Client for fetching data from LiquidLaunch.
    """

    def __init__(self, config: Config):
        """
        Initialize the LiquidLaunch client.

        Args:
            config: The configuration object.
        """
        self.config = config

        # Initialize Twitter client for fetching tweets
        self.twitter_client = TwitterClient(config)

        # Cache for token launches and graduations
        self.token_launches_cache = []
        self.token_launches_timestamp = None

        self.token_graduations_cache = []
        self.token_graduations_timestamp = None

        # Initialize
        self._init_client()

    def _init_client(self):
        """Initialize the client and fetch initial data."""
        try:
            # Fetch initial data
            self.get_token_launches()
            self.get_token_graduations()

            logger.info("LiquidLaunch client initialized successfully")

        except Exception as e:
            logger.error(
                f"Failed to initialize LiquidLaunch client: {e!s}", exc_info=True
            )
            # Don't raise, as this is not critical

    def get_token_launches(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """
        Get recent token launches.

        Args:
            force_refresh: Whether to force a refresh of the cached data.

        Returns:
            A list of token launches.
        """
        # Check if we have cached data and it's still fresh (less than 1 hour old)
        if (
            not force_refresh
            and self.token_launches_cache
            and self.token_launches_timestamp is not None
            and datetime.now() - self.token_launches_timestamp < timedelta(hours=1)
        ):
            return self.token_launches_cache

        try:
            # Fetch tweets from LiquidLaunch account
            tweets = self.twitter_client.get_liquidlaunch_tweets(count=50)

            # Filter tweets about token launches
            launch_keywords = [
                "launch",
                "listing",
                "new token",
                "now available",
                "just added",
                "trading now",
            ]

            launches = []

            for tweet in tweets:
                text = tweet.get("text", "").lower()

                # Check if tweet is about a token launch
                if any(keyword in text for keyword in launch_keywords):
                    # Extract token symbol
                    symbol_match = re.search(r"\$([A-Za-z0-9]+)", text)
                    if symbol_match:
                        symbol = symbol_match.group(1).upper()

                        # Extract token name (more complex, might not always work)
                        name_match = re.search(
                            r"([A-Za-z0-9\s]+)\s+\(\$" + symbol + r"\)",
                            tweet.get("text", ""),
                        )
                        name = name_match.group(1).strip() if name_match else symbol

                        launches.append(
                            {
                                "token_symbol": symbol,
                                "token_name": name,
                                "tweet_id": tweet.get("id"),
                                "tweet_text": tweet.get("text"),
                                "created_at": tweet.get("created_at"),
                                "type": "launch",
                            }
                        )

            # Sort by created_at (newest first)
            launches.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            # Cache the results
            self.token_launches_cache = launches
            self.token_launches_timestamp = datetime.now()

            logger.info(f"Fetched {len(launches)} token launches from LiquidLaunch")
            return launches

        except Exception as e:
            logger.error(f"Failed to fetch token launches: {e!s}", exc_info=True)
            if self.token_launches_cache:
                logger.info("Using cached token launches")
                return self.token_launches_cache
            return []

    def get_token_graduations(
        self, force_refresh: bool = False
    ) -> list[dict[str, Any]]:
        """
        Get recent token graduations/migrations.

        Args:
            force_refresh: Whether to force a refresh of the cached data.

        Returns:
            A list of token graduations.
        """
        # Check if we have cached data and it's still fresh (less than 1 hour old)
        if (
            not force_refresh
            and self.token_graduations_cache
            and self.token_graduations_timestamp is not None
            and datetime.now() - self.token_graduations_timestamp < timedelta(hours=1)
        ):
            return self.token_graduations_cache

        try:
            # Fetch tweets from LiquidLaunch account
            tweets = self.twitter_client.get_liquidlaunch_tweets(count=50)

            # Filter tweets about token graduations
            graduation_keywords = [
                "graduation",
                "graduated",
                "migrat",
                "moving to",
                "now on hyperliquid",
                "now trading on",
            ]

            graduations = []

            for tweet in tweets:
                text = tweet.get("text", "").lower()

                # Check if tweet is about a token graduation
                if any(keyword in text for keyword in graduation_keywords):
                    # Extract token symbol
                    symbol_match = re.search(r"\$([A-Za-z0-9]+)", text)
                    if symbol_match:
                        symbol = symbol_match.group(1).upper()

                        # Extract token name (more complex, might not always work)
                        name_match = re.search(
                            r"([A-Za-z0-9\s]+)\s+\(\$" + symbol + r"\)",
                            tweet.get("text", ""),
                        )
                        name = name_match.group(1).strip() if name_match else symbol

                        graduations.append(
                            {
                                "token_symbol": symbol,
                                "token_name": name,
                                "tweet_id": tweet.get("id"),
                                "tweet_text": tweet.get("text"),
                                "created_at": tweet.get("created_at"),
                                "type": "graduation",
                            }
                        )

            # Sort by created_at (newest first)
            graduations.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            # Cache the results
            self.token_graduations_cache = graduations
            self.token_graduations_timestamp = datetime.now()

            logger.info(
                f"Fetched {len(graduations)} token graduations from LiquidLaunch"
            )
            return graduations

        except Exception as e:
            logger.error(f"Failed to fetch token graduations: {e!s}", exc_info=True)
            if self.token_graduations_cache:
                logger.info("Using cached token graduations")
                return self.token_graduations_cache
            return []

    def get_token_info(self, symbol: str) -> dict[str, Any]:
        """
        Get information about a token.

        Args:
            symbol: The token symbol.

        Returns:
            A dictionary with token information.
        """
        try:
            # Try to find the token in launches
            for launch in self.get_token_launches():
                if launch.get("token_symbol") == symbol:
                    return launch

            # Try to find the token in graduations
            for graduation in self.get_token_graduations():
                if graduation.get("token_symbol") == symbol:
                    return graduation

            logger.warning(f"Token {symbol} not found in LiquidLaunch data")
            return {}

        except Exception as e:
            logger.error(f"Failed to get token info for {symbol}: {e!s}", exc_info=True)
            return {}
