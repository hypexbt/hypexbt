"""
Hyperliquid API client module for the hypexbt Twitter bot.

This module handles interactions with the Hyperliquid API to fetch market data
and calculate trading signals.
"""

import logging
import time
import json
import asyncio
import random
import websockets
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta

import requests
import pandas as pd
import numpy as np
# import talib  # Commented out for testing

from src.utils.config import Config

logger = logging.getLogger(__name__)


class HyperliquidClient:
    """
    Client for interacting with the Hyperliquid API.
    """

    def __init__(self, config: Config):
        """
        Initialize the Hyperliquid client.

        Args:
            config: The configuration object.
        """
        self.config = config
        self.api_url = config.get_api_endpoints()["hyperliquid"]

        # Rate limiting
        self.last_request_time = None
        self.min_request_interval = 0.5  # seconds between requests

        # Cache for metadata
        self.metadata = None
        self.metadata_timestamp = None

        # Cache for candles
        self.candle_cache = {}

        # Initialize
        self._init_client()

    def _init_client(self):
        """Initialize the client and fetch initial data."""
        try:
            # Fetch metadata
            self.get_metadata()
            logger.info("Hyperliquid client initialized successfully")

        except Exception as e:
            logger.error(
                f"Failed to initialize Hyperliquid client: {str(e)}", exc_info=True
            )
            raise

    def _make_request(
        self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the Hyperliquid API with rate limiting.

        Args:
            endpoint: The API endpoint to call.
            method: The HTTP method to use.
            data: The request data for POST requests.

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

            if method.upper() == "GET":
                response = requests.get(url)
            else:
                response = requests.post(url, json=data)

            # Update last request time
            self.last_request_time = time.time()

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"API request failed: {str(e)}", exc_info=True)
            raise

    def get_metadata(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get metadata about available assets.

        Args:
            force_refresh: Whether to force a refresh of the cached metadata.

        Returns:
            The metadata.
        """
        # Check if we have cached metadata and it's still fresh (less than 1 hour old)
        if (
            not force_refresh
            and self.metadata is not None
            and self.metadata_timestamp is not None
            and datetime.now() - self.metadata_timestamp < timedelta(hours=1)
        ):
            return self.metadata

        try:
            # Fetch metadata
            response = self._make_request("/info")

            # Cache the response
            self.metadata = response
            self.metadata_timestamp = datetime.now()

            logger.info("Fetched metadata from Hyperliquid")
            return response

        except Exception as e:
            logger.error(f"Failed to fetch metadata: {str(e)}", exc_info=True)
            if self.metadata is not None:
                logger.info("Using cached metadata")
                return self.metadata
            raise

    def get_candles(
        self, coin: str, interval: str = "15m", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get candles for a coin.

        Args:
            coin: The coin symbol.
            interval: The candle interval (1m, 5m, 15m, 1h, 4h, 1d).
            limit: The number of candles to fetch.

        Returns:
            The candles.
        """
        try:
            # Fetch candles
            response = self._make_request(
                f"/candles_snapshot?coin={coin}&interval={interval}&limit={limit}"
            )

            # Cache the response
            cache_key = f"{coin}_{interval}"
            self.candle_cache[cache_key] = {
                "candles": response,
                "timestamp": datetime.now(),
            }

            logger.info(f"Fetched {len(response)} {interval} candles for {coin}")
            return response

        except Exception as e:
            logger.error(f"Failed to fetch candles for {coin}: {str(e)}", exc_info=True)

            # Check if we have cached candles
            cache_key = f"{coin}_{interval}"
            if cache_key in self.candle_cache:
                logger.info(f"Using cached candles for {coin}")
                return self.candle_cache[cache_key]["candles"]

            raise

    def get_ticker(self, coin: str) -> Dict[str, Any]:
        """
        Get ticker data for a coin.

        Args:
            coin: The coin symbol.

        Returns:
            The ticker data.
        """
        try:
            # Fetch ticker
            response = self._make_request(f"/ticker?coin={coin}")

            logger.info(f"Fetched ticker for {coin}")
            return response

        except Exception as e:
            logger.error(f"Failed to fetch ticker for {coin}: {str(e)}", exc_info=True)
            raise

    def get_funding_rates(self, coin: str) -> Dict[str, Any]:
        """
        Get funding rates for a coin.

        Args:
            coin: The coin symbol.

        Returns:
            The funding rates.
        """
        try:
            # Fetch funding rates
            response = self._make_request(f"/funding_rates?coin={coin}")

            logger.info(f"Fetched funding rates for {coin}")
            return response

        except Exception as e:
            logger.error(
                f"Failed to fetch funding rates for {coin}: {str(e)}", exc_info=True
            )
            raise

    def get_daily_stats(self) -> Dict[str, Any]:
        """
        Get daily statistics for Hyperliquid.

        Returns:
            A dictionary with daily statistics.
        """
        try:
            # Get metadata to get list of available coins
            metadata = self.get_metadata()
            available_coins = [coin["name"] for coin in metadata[0]["universe"]]

            # Initialize stats
            stats = {
                "total_volume_24h": 0,
                "total_open_interest": 0,
                "top_gainers": [],
                "top_losers": [],
                "timestamp": datetime.now().isoformat(),
            }

            # Fetch data for each coin
            for coin in available_coins:
                try:
                    # Get ticker
                    ticker = self.get_ticker(coin)

                    # Extract data
                    price = float(ticker.get("midPrice", 0))
                    change_24h = float(ticker.get("change24h", 0))
                    volume_24h = float(ticker.get("volume24h", 0))
                    open_interest = float(ticker.get("openInterest", 0))

                    # Add to totals
                    stats["total_volume_24h"] += volume_24h
                    stats["total_open_interest"] += open_interest

                    # Add to gainers/losers
                    coin_data = {
                        "coin": coin,
                        "price": price,
                        "change_pct": change_24h * 100,
                        "volume_24h": volume_24h,
                        "open_interest": open_interest,
                    }

                    if change_24h > 0:
                        stats["top_gainers"].append(coin_data)
                    else:
                        stats["top_losers"].append(coin_data)

                except Exception as e:
                    logger.warning(f"Failed to fetch data for {coin}: {str(e)}")
                    continue

            # Sort gainers and losers
            stats["top_gainers"].sort(key=lambda x: x["change_pct"], reverse=True)
            stats["top_losers"].sort(key=lambda x: x["change_pct"])

            logger.info("Fetched daily stats")
            return stats

        except Exception as e:
            logger.error(f"Failed to fetch daily stats: {str(e)}", exc_info=True)
            raise

    def calculate_momentum_signals(self, coin: str) -> Dict[str, Any]:
        """
        Calculate momentum signals for a coin.

        Args:
            coin: The coin symbol.

        Returns:
            A dictionary with momentum signals.
        """
        try:
            # Get current price
            ticker = self.get_ticker(coin)
            current_price = float(ticker.get("midPrice", 0))

            # Get 15m candles
            candles_15m = self.get_candles(coin, interval="15m", limit=100)

            # Get 1h candles
            candles_1h = self.get_candles(coin, interval="1h", limit=100)

            # Calculate signals
            signal_15m = self._calculate_ema_signal(candles_15m)
            signal_1h = self._calculate_ema_signal(candles_1h)

            # Check for signal changes
            signal_15m_change = self._check_signal_change(candles_15m, signal_15m)
            signal_1h_change = self._check_signal_change(candles_1h, signal_1h)

            return {
                "coin": coin,
                "price": current_price,
                "15m_signal": signal_15m,
                "15m_signal_change": signal_15m_change,
                "1h_signal": signal_1h,
                "1h_signal_change": signal_1h_change,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(
                f"Failed to calculate momentum signals for {coin}: {str(e)}",
                exc_info=True,
            )
            raise

    def _calculate_ema_signal(self, candles: List[Dict[str, Any]]) -> int:
        """
        Calculate EMA signal from candles.

        Args:
            candles: The candles.

        Returns:
            1 for bullish, -1 for bearish, 0 for neutral.
        """
        try:
            # Convert candles to DataFrame
            df = pd.DataFrame(candles)

            # Extract close prices
            close_prices = df["close"].astype(float).values

            # Calculate EMAs manually for testing
            # In production, use talib.EMA
            ema_fast = self._calculate_ema(close_prices, 9)
            ema_slow = self._calculate_ema(close_prices, 21)

            # Calculate signal
            if ema_fast[-1] > ema_slow[-1]:
                return 1  # Bullish
            elif ema_fast[-1] < ema_slow[-1]:
                return -1  # Bearish
            else:
                return 0  # Neutral

        except Exception as e:
            logger.error(f"Failed to calculate EMA signal: {str(e)}", exc_info=True)
            return 0

    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate EMA manually.

        Args:
            prices: The price array.
            period: The EMA period.

        Returns:
            The EMA values.
        """
        ema = np.zeros_like(prices)
        ema[0] = prices[0]

        multiplier = 2 / (period + 1)

        for i in range(1, len(prices)):
            ema[i] = (prices[i] - ema[i - 1]) * multiplier + ema[i - 1]

        return ema

    def _check_signal_change(
        self, candles: List[Dict[str, Any]], current_signal: int
    ) -> bool:
        """
        Check if the signal has changed in the last candle.

        Args:
            candles: The candles.
            current_signal: The current signal.

        Returns:
            True if the signal has changed, False otherwise.
        """
        try:
            # Convert candles to DataFrame
            df = pd.DataFrame(candles)

            # Extract close prices
            close_prices = df["close"].astype(float).values

            # Calculate EMAs manually for testing
            # In production, use talib.EMA
            ema_fast = self._calculate_ema(close_prices, 9)
            ema_slow = self._calculate_ema(close_prices, 21)

            # Calculate previous signal
            if ema_fast[-2] > ema_slow[-2]:
                previous_signal = 1  # Bullish
            elif ema_fast[-2] < ema_slow[-2]:
                previous_signal = -1  # Bearish
            else:
                previous_signal = 0  # Neutral

            # Check if signal has changed
            return previous_signal != current_signal

        except Exception as e:
            logger.error(f"Failed to check signal change: {str(e)}", exc_info=True)
            return False

    async def start_websocket_streaming(
        self, callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Start WebSocket streaming for real-time data.

        Args:
            callback: The callback function to call when a signal is detected.
        """
        try:
            # Get metadata to get list of available coins
            metadata = self.get_metadata()
            available_coins = [coin["name"] for coin in metadata[0]["universe"]]

            # Prioritize top coins
            top_coins = ["BTC", "ETH", "SOL", "AVAX", "MATIC", "LINK"]
            coins_to_stream = [coin for coin in top_coins if coin in available_coins]

            # Add some other coins
            other_coins = [coin for coin in available_coins if coin not in top_coins]
            if other_coins:
                coins_to_stream.extend(
                    random.sample(other_coins, min(5, len(other_coins)))
                )

            # WebSocket URL
            ws_url = self.api_url.replace("http", "ws") + "/ws"

            # Connect to WebSocket
            async with websockets.connect(ws_url) as websocket:
                # Subscribe to candles for each coin
                for coin in coins_to_stream:
                    subscribe_message = {
                        "method": "subscribe",
                        "subscription": {
                            "type": "candle",
                            "coin": coin,
                            "interval": "15m",
                        },
                    }
                    await websocket.send(json.dumps(subscribe_message))

                    subscribe_message = {
                        "method": "subscribe",
                        "subscription": {
                            "type": "candle",
                            "coin": coin,
                            "interval": "1h",
                        },
                    }
                    await websocket.send(json.dumps(subscribe_message))

                logger.info(f"Subscribed to candles for {len(coins_to_stream)} coins")

                # Process messages
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)

                    # Check if it's a candle update
                    if "candle" in data:
                        coin = data.get("coin")
                        interval = data.get("interval")

                        # Calculate signals
                        if coin in coins_to_stream:
                            try:
                                # Get current signals
                                signals = self.calculate_momentum_signals(coin)

                                # Check if there's a signal change
                                if signals.get("15m_signal_change") or signals.get(
                                    "1h_signal_change"
                                ):
                                    # Call callback
                                    callback(signals)
                            except Exception as e:
                                logger.error(
                                    f"Failed to process candle update for {coin}: {str(e)}",
                                    exc_info=True,
                                )

        except Exception as e:
            logger.error(f"WebSocket streaming error: {str(e)}", exc_info=True)
            raise
