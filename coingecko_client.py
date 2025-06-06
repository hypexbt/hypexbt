"""
CoinGecko API client module for the hypexbt Twitter bot.

This module handles interactions with the CoinGecko API to fetch token fundamentals.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

import requests

from bot.utils.config import Config

logger = logging.getLogger(__name__)


class CoinGeckoClient:
    """
    Client for interacting with the CoinGecko API.
    """

    def __init__(self, config: Config):
        """
        Initialize the CoinGecko client.

        Args:
            config: The configuration object.
        """
        self.config = config
        self.api_url = config.get_api_endpoints()["coingecko"]

        # Rate limiting
        self.last_request_time = None
        self.min_request_interval = (
            1.5  # seconds between requests (to avoid rate limiting)
        )

        # Cache for coin list
        self.coin_list = None
        self.coin_list_timestamp = None

        # Cache for coin data
        self.coin_data_cache = {}

        # Initialize
        self._init_client()

    def _init_client(self):
        """Initialize the client and fetch initial data."""
        try:
            # Fetch coin list
            self.get_coin_list()
            logger.info("CoinGecko client initialized successfully")

        except Exception as e:
            logger.error(
                f"Failed to initialize CoinGecko client: {str(e)}", exc_info=True
            )
            raise

    def _make_request(
        self, endpoint: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the CoinGecko API with rate limiting.

        Args:
            endpoint: The API endpoint to call.
            params: The request parameters.

        Returns:
            The response from the API.
        """
        # Apply rate limiting
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)

        try:
            url = f"{self.api_url}{endpoint}"
            response = requests.get(url, params=params)

            # Update last request time
            self.last_request_time = time.time()

            # Check for rate limiting
            if response.status_code == 429:
                logger.warning("Rate limited by CoinGecko API, waiting and retrying...")
                time.sleep(60)  # Wait for 60 seconds
                return self._make_request(endpoint, params)

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"API request failed: {str(e)}", exc_info=True)
            raise

    def get_coin_list(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get the list of all coins from CoinGecko.

        Args:
            force_refresh: Whether to force a refresh of the cached coin list.

        Returns:
            The list of coins.
        """
        # Check if we have cached coin list and it's still fresh (less than 1 day old)
        if (
            not force_refresh
            and self.coin_list is not None
            and self.coin_list_timestamp is not None
            and datetime.now() - self.coin_list_timestamp < timedelta(days=1)
        ):
            return self.coin_list

        try:
            # Fetch coin list
            response = self._make_request("/coins/list", {"include_platform": "true"})

            # Cache the response
            self.coin_list = response
            self.coin_list_timestamp = datetime.now()

            logger.info(f"Fetched {len(response)} coins from CoinGecko")
            return response

        except Exception as e:
            logger.error(f"Failed to fetch coin list: {str(e)}", exc_info=True)
            if self.coin_list is not None:
                logger.info("Using cached coin list")
                return self.coin_list
            raise

    def search_coin_id(self, symbol: str) -> Optional[str]:
        """
        Search for a coin ID by symbol.

        Args:
            symbol: The coin symbol to search for.

        Returns:
            The coin ID, or None if not found.
        """
        try:
            # Get coin list
            coin_list = self.get_coin_list()

            # Search for the coin by symbol
            symbol = symbol.lower()
            matching_coins = [
                coin for coin in coin_list if coin.get("symbol", "").lower() == symbol
            ]

            if matching_coins:
                # Sort by market cap (if available) or use the first one
                return matching_coins[0].get("id")

            return None

        except Exception as e:
            logger.error(f"Failed to search for coin ID: {str(e)}", exc_info=True)
            return None

    def get_coin_data(
        self, coin_id: str, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get detailed data for a specific coin.

        Args:
            coin_id: The CoinGecko coin ID.
            force_refresh: Whether to force a refresh of the cached coin data.

        Returns:
            The coin data.
        """
        # Check if we have cached coin data and it's still fresh (less than 1 hour old)
        if (
            not force_refresh
            and coin_id in self.coin_data_cache
            and "timestamp" in self.coin_data_cache[coin_id]
            and datetime.now() - self.coin_data_cache[coin_id]["timestamp"]
            < timedelta(hours=1)
        ):
            return self.coin_data_cache[coin_id]

        try:
            # Fetch coin data
            response = self._make_request(
                f"/coins/{coin_id}",
                {
                    "localization": "false",
                    "tickers": "false",
                    "market_data": "true",
                    "community_data": "true",
                    "developer_data": "false",
                },
            )

            # Add timestamp
            response["timestamp"] = datetime.now()

            # Cache the response
            self.coin_data_cache[coin_id] = response

            logger.info(f"Fetched data for coin {coin_id}")
            return response

        except Exception as e:
            logger.error(
                f"Failed to fetch coin data for {coin_id}: {str(e)}", exc_info=True
            )
            if coin_id in self.coin_data_cache:
                logger.info(f"Using cached data for coin {coin_id}")
                return self.coin_data_cache[coin_id]
            raise

    def get_token_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Get token fundamentals by symbol.

        Args:
            symbol: The token symbol.

        Returns:
            A dictionary with token fundamentals.
        """
        try:
            # Search for the coin ID
            coin_id = self.search_coin_id(symbol)
            if not coin_id:
                logger.warning(f"Could not find coin ID for symbol {symbol}")
                return {}

            # Get coin data
            coin_data = self.get_coin_data(coin_id)

            # Extract fundamentals
            market_data = coin_data.get("market_data", {})

            fundamentals = {
                "name": coin_data.get("name", ""),
                "symbol": coin_data.get("symbol", "").upper(),
                "current_price": market_data.get("current_price", {}).get("usd"),
                "market_cap": market_data.get("market_cap", {}).get("usd"),
                "fully_diluted_valuation": market_data.get(
                    "fully_diluted_valuation", {}
                ).get("usd"),
                "circulating_supply": market_data.get("circulating_supply"),
                "total_supply": market_data.get("total_supply"),
                "max_supply": market_data.get("max_supply"),
                "ath": market_data.get("ath", {}).get("usd"),
                "ath_change_percentage": market_data.get(
                    "ath_change_percentage", {}
                ).get("usd"),
                "ath_date": market_data.get("ath_date", {}).get("usd"),
                "price_change_percentage_24h": market_data.get(
                    "price_change_percentage_24h"
                ),
                "price_change_percentage_7d": market_data.get(
                    "price_change_percentage_7d"
                ),
                "price_change_percentage_30d": market_data.get(
                    "price_change_percentage_30d"
                ),
                "description": coin_data.get("description", {}).get("en", ""),
                "links": {
                    "homepage": coin_data.get("links", {}).get("homepage", []),
                    "twitter_screen_name": coin_data.get("links", {}).get(
                        "twitter_screen_name"
                    ),
                    "telegram_channel_identifier": coin_data.get("links", {}).get(
                        "telegram_channel_identifier"
                    ),
                    "repos_url": coin_data.get("links", {})
                    .get("repos_url", {})
                    .get("github", []),
                },
            }

            logger.info(f"Fetched fundamentals for {symbol}")
            return fundamentals

        except Exception as e:
            logger.error(
                f"Failed to fetch token fundamentals for {symbol}: {str(e)}",
                exc_info=True,
            )
            return {}
