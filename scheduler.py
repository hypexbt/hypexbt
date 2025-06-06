"""
Tweet scheduler module for the hypexbt Twitter bot.

This module handles scheduling and distributing tweets throughout the day.
"""

import logging
import random
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import asyncio

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.utils.config import Config
from bot.utils.slack import SlackNotifier
from bot.twitter_client import TwitterClient
from bot.data_sources.hyperliquid_client import HyperliquidClient
from bot.data_sources.liquidlaunch_client import LiquidLaunchClient
from bot.data_sources.coingecko_client import CoinGeckoClient
from bot.tweet_generators.hyperliquid_news import HyperliquidNewsTweetGenerator
from bot.tweet_generators.token_launch import TokenLaunchTweetGenerator
from bot.tweet_generators.token_graduation import TokenGraduationTweetGenerator
from bot.tweet_generators.trading_signal import TradingSignalTweetGenerator
from bot.tweet_generators.daily_stats import DailyStatsTweetGenerator
from bot.tweet_generators.token_fundamentals import TokenFundamentalsTweetGenerator

logger = logging.getLogger(__name__)


class TweetScheduler:
    """
    Scheduler for tweets.
    """

    def __init__(self, config: Config):
        """
        Initialize the tweet scheduler.

        Args:
            config: The configuration object.
        """
        self.config = config
        self.scheduler = BackgroundScheduler()

        # Initialize clients
        self.twitter_client = TwitterClient(config)
        self.hyperliquid_client = HyperliquidClient(config)
        self.liquidlaunch_client = LiquidLaunchClient(config)
        self.coingecko_client = CoinGeckoClient(config)
        self.slack_notifier = SlackNotifier(config)

        # Initialize tweet generators
        self.tweet_generators = {
            "hyperliquid_news": HyperliquidNewsTweetGenerator(self.twitter_client),
            "token_launch": TokenLaunchTweetGenerator(self.liquidlaunch_client),
            "token_graduation": TokenGraduationTweetGenerator(self.liquidlaunch_client),
            "trading_signal": TradingSignalTweetGenerator(self.hyperliquid_client),
            "daily_stats": DailyStatsTweetGenerator(self.hyperliquid_client),
            "token_fundamentals": TokenFundamentalsTweetGenerator(
                self.coingecko_client, self.hyperliquid_client
            ),
        }

        # Tweet queue
        self.tweet_queue = []

        # Tweet history
        self.tweet_history = []

        # Tweet count for today
        self.tweet_count_today = 0
        self.last_count_reset = datetime.now().date()

        # Initialize
        self._init_scheduler()

    def _init_scheduler(self):
        """Initialize the scheduler."""
        try:
            # Add job to reset tweet count at midnight
            self.scheduler.add_job(
                self._reset_tweet_count,
                CronTrigger(hour=0, minute=0),
                id="reset_tweet_count",
            )

            # Add job to generate tweet schedule for the day
            self.scheduler.add_job(
                self._generate_tweet_schedule,
                CronTrigger(hour=0, minute=5),
                id="generate_tweet_schedule",
            )

            # Add job to check for real-time trading signals
            self.scheduler.add_job(
                self._check_trading_signals,
                IntervalTrigger(minutes=15),
                id="check_trading_signals",
            )

            # Add job to check for new token launches and graduations
            self.scheduler.add_job(
                self._check_token_events,
                IntervalTrigger(minutes=30),
                id="check_token_events",
            )

            # Add job to process tweet queue
            self.scheduler.add_job(
                self._process_tweet_queue,
                IntervalTrigger(minutes=1),
                id="process_tweet_queue",
            )

            # Generate initial tweet schedule
            self._generate_tweet_schedule()

            logger.info("Tweet scheduler initialized successfully")

        except Exception as e:
            logger.error(
                f"Failed to initialize tweet scheduler: {str(e)}", exc_info=True
            )
            self.slack_notifier.send_error(
                f"Failed to initialize tweet scheduler: {str(e)}"
            )
            raise

    def start(self):
        """Start the scheduler."""
        try:
            self.scheduler.start()
            logger.info("Tweet scheduler started")
        except Exception as e:
            logger.error(f"Failed to start tweet scheduler: {str(e)}", exc_info=True)
            self.slack_notifier.send_error(f"Failed to start tweet scheduler: {str(e)}")
            raise

    def stop(self):
        """Stop the scheduler."""
        try:
            self.scheduler.shutdown()
            logger.info("Tweet scheduler stopped")
        except Exception as e:
            logger.error(f"Failed to stop tweet scheduler: {str(e)}", exc_info=True)

    def _reset_tweet_count(self):
        """Reset the tweet count for the day."""
        self.tweet_count_today = 0
        self.last_count_reset = datetime.now().date()
        logger.info("Reset tweet count for the day")

    def _generate_tweet_schedule(self):
        """Generate a schedule of tweets for the day."""
        try:
            # Check if we need to reset the tweet count
            if datetime.now().date() != self.last_count_reset:
                self._reset_tweet_count()

            # Clear existing schedule
            self.tweet_queue = []

            # Get tweet schedule configuration
            schedule_config = self.config.get_tweet_schedule()
            min_tweets = schedule_config["min_tweets_per_day"]
            max_tweets = schedule_config["max_tweets_per_day"]
            min_interval = schedule_config["min_interval_minutes"]
            max_interval = schedule_config["max_interval_minutes"]
            active_hours_start = schedule_config["active_hours_start"]
            active_hours_end = schedule_config["active_hours_end"]

            # Calculate active hours
            active_hours = []
            current_hour = datetime.now().hour

            if active_hours_start <= active_hours_end:
                active_hours = list(range(active_hours_start, active_hours_end + 1))
            else:
                # Handle wrap around midnight
                active_hours = list(range(active_hours_start, 24)) + list(
                    range(0, active_hours_end + 1)
                )

            # Calculate remaining active hours for today
            remaining_active_hours = [
                hour for hour in active_hours if hour >= current_hour
            ]

            # Calculate number of tweets for today
            num_tweets = random.randint(min_tweets, max_tweets)

            # Adjust for remaining hours
            if len(remaining_active_hours) < len(active_hours):
                num_tweets = max(
                    1, int(num_tweets * len(remaining_active_hours) / len(active_hours))
                )

            # Subtract tweets already sent today
            num_tweets = max(0, num_tweets - self.tweet_count_today)

            logger.info(f"Scheduling {num_tweets} tweets for today")

            if num_tweets == 0:
                return

            # Get tweet distribution
            distribution = self.config.get_tweet_distribution()

            # Calculate number of tweets for each type
            tweet_counts = {}
            remaining = num_tweets

            for tweet_type, pct in distribution.items():
                count = int(num_tweets * pct)
                tweet_counts[tweet_type] = count
                remaining -= count

            # Distribute remaining tweets
            for _ in range(remaining):
                tweet_type = random.choice(list(distribution.keys()))
                tweet_counts[tweet_type] += 1

            # Generate tweet schedule
            now = datetime.now()
            current_time = now

            # Calculate end of active hours today
            if active_hours_end >= current_hour:
                end_time = now.replace(hour=active_hours_end, minute=59, second=59)
            else:
                # Handle wrap around midnight
                end_time = now.replace(hour=23, minute=59, second=59)

            # Calculate available time
            available_minutes = (end_time - current_time).total_seconds() / 60

            # Ensure we have enough time for all tweets
            if available_minutes < num_tweets * min_interval:
                logger.warning(
                    f"Not enough time to schedule all {num_tweets} tweets today"
                )
                num_tweets = int(available_minutes / min_interval)
                logger.info(f"Adjusted to {num_tweets} tweets")

            # Schedule tweets
            for tweet_type, count in tweet_counts.items():
                for _ in range(count):
                    # Calculate random time within active hours
                    minutes_offset = random.randint(
                        0, int(available_minutes - min_interval)
                    )
                    tweet_time = current_time + timedelta(minutes=minutes_offset)

                    # Ensure tweet time is within active hours
                    while tweet_time.hour not in active_hours:
                        minutes_offset = random.randint(
                            0, int(available_minutes - min_interval)
                        )
                        tweet_time = current_time + timedelta(minutes=minutes_offset)

                    # Add to queue
                    self.tweet_queue.append(
                        {"type": tweet_type, "scheduled_time": tweet_time}
                    )

                    # Update current time to ensure minimum interval
                    current_time = tweet_time + timedelta(minutes=min_interval)
                    available_minutes = (end_time - current_time).total_seconds() / 60

                    if available_minutes < min_interval:
                        break

                if available_minutes < min_interval:
                    break

            # Sort queue by scheduled time
            self.tweet_queue.sort(key=lambda x: x["scheduled_time"])

            logger.info(f"Generated tweet schedule with {len(self.tweet_queue)} tweets")

        except Exception as e:
            logger.error(f"Failed to generate tweet schedule: {str(e)}", exc_info=True)
            self.slack_notifier.send_error(
                f"Failed to generate tweet schedule: {str(e)}"
            )

    def _check_trading_signals(self):
        """Check for real-time trading signals."""
        try:
            # Check if we've reached the maximum tweets for today
            if (
                self.tweet_count_today
                >= self.config.get_tweet_schedule()["max_tweets_per_day"]
            ):
                logger.info(
                    "Maximum tweets for today reached, skipping trading signal check"
                )
                return

            # Get metadata to get list of available coins
            metadata = self.hyperliquid_client.get_metadata()
            available_coins = [coin["name"] for coin in metadata[0]["universe"]]

            # Check top coins first
            top_coins = ["BTC", "ETH", "SOL", "AVAX", "MATIC", "LINK"]
            coins_to_check = [coin for coin in top_coins if coin in available_coins]

            # Add some random coins
            other_coins = [coin for coin in available_coins if coin not in top_coins]
            if other_coins:
                coins_to_check.extend(
                    random.sample(other_coins, min(3, len(other_coins)))
                )

            # Check for signals
            for coin in coins_to_check:
                signals = self.hyperliquid_client.calculate_momentum_signals(coin)

                # Check if there's a signal change
                if signals.get("15m_signal_change") or signals.get("1h_signal_change"):
                    # Generate and post tweet
                    tweet_data = self.tweet_generators[
                        "trading_signal"
                    ].generate_tweet()

                    if tweet_data.get("success"):
                        self._post_tweet(tweet_data)

                        # Only post one signal tweet at a time
                        break

        except Exception as e:
            logger.error(f"Failed to check trading signals: {str(e)}", exc_info=True)
            self.slack_notifier.send_error(f"Failed to check trading signals: {str(e)}")

    def _check_token_events(self):
        """Check for new token launches and graduations."""
        try:
            # Check if we've reached the maximum tweets for today
            if (
                self.tweet_count_today
                >= self.config.get_tweet_schedule()["max_tweets_per_day"]
            ):
                logger.info(
                    "Maximum tweets for today reached, skipping token events check"
                )
                return

            # Check for new token launches
            launch_tweet_data = self.tweet_generators["token_launch"].generate_tweet()

            if launch_tweet_data.get("success"):
                self._post_tweet(launch_tweet_data)
                return

            # Check for token graduations
            graduation_tweet_data = self.tweet_generators[
                "token_graduation"
            ].generate_tweet()

            if graduation_tweet_data.get("success"):
                self._post_tweet(graduation_tweet_data)

        except Exception as e:
            logger.error(f"Failed to check token events: {str(e)}", exc_info=True)
            self.slack_notifier.send_error(f"Failed to check token events: {str(e)}")

    def _process_tweet_queue(self):
        """Process the tweet queue."""
        try:
            # Check if we need to reset the tweet count
            if datetime.now().date() != self.last_count_reset:
                self._reset_tweet_count()

            # Check if the queue is empty
            if not self.tweet_queue:
                return

            # Check if we've reached the maximum tweets for today
            if (
                self.tweet_count_today
                >= self.config.get_tweet_schedule()["max_tweets_per_day"]
            ):
                logger.info("Maximum tweets for today reached, clearing queue")
                self.tweet_queue = []
                return

            # Check if it's time to post the next tweet
            now = datetime.now()
            next_tweet = self.tweet_queue[0]

            if now >= next_tweet["scheduled_time"]:
                # Remove from queue
                self.tweet_queue.pop(0)

                # Generate tweet
                tweet_type = next_tweet["type"]

                if tweet_type in self.tweet_generators:
                    tweet_data = self.tweet_generators[tweet_type].generate_tweet()

                    if tweet_data.get("success"):
                        self._post_tweet(tweet_data)
                    else:
                        logger.warning(
                            f"Failed to generate {tweet_type} tweet: {tweet_data.get('error')}"
                        )
                else:
                    logger.warning(f"Unknown tweet type: {tweet_type}")

        except Exception as e:
            logger.error(f"Failed to process tweet queue: {str(e)}", exc_info=True)
            self.slack_notifier.send_error(f"Failed to process tweet queue: {str(e)}")

    def _post_tweet(self, tweet_data: Dict[str, Any]):
        """
        Post a tweet.

        Args:
            tweet_data: The tweet data.
        """
        try:
            action = tweet_data.get("action", "tweet")

            if action == "tweet":
                # Post a new tweet
                response = self.twitter_client.post_tweet(tweet_data.get("tweet_text"))

                logger.info(f"Posted tweet: {tweet_data.get('tweet_text')[:50]}...")

            elif action == "retweet":
                # Retweet
                response = self.twitter_client.retweet(tweet_data.get("tweet_id"))

                logger.info(f"Retweeted tweet {tweet_data.get('tweet_id')}")

            elif action == "quote_tweet":
                # Quote tweet
                response = self.twitter_client.quote_tweet(
                    tweet_data.get("tweet_id"), tweet_data.get("quote_text")
                )

                logger.info(
                    f"Quote tweeted {tweet_data.get('tweet_id')}: {tweet_data.get('quote_text')[:50]}..."
                )

            # Increment tweet count
            self.tweet_count_today += 1

            # Add to history
            self.tweet_history.append(
                {
                    "tweet_data": tweet_data,
                    "timestamp": datetime.now().isoformat(),
                    "response": response,
                }
            )

            # Keep history limited to last 100 tweets
            if len(self.tweet_history) > 100:
                self.tweet_history = self.tweet_history[-100:]

        except Exception as e:
            logger.error(f"Failed to post tweet: {str(e)}", exc_info=True)
            self.slack_notifier.send_error(f"Failed to post tweet: {str(e)}")

    async def start_websocket_streaming(self):
        """Start WebSocket streaming for real-time data."""
        try:
            await self.hyperliquid_client.start_websocket_streaming(
                self._handle_websocket_signal
            )
        except Exception as e:
            logger.error(f"WebSocket streaming error: {str(e)}", exc_info=True)
            self.slack_notifier.send_error(f"WebSocket streaming error: {str(e)}")

    def _handle_websocket_signal(self, signal_data: Dict[str, Any]):
        """
        Handle a trading signal from WebSocket.

        Args:
            signal_data: The signal data.
        """
        try:
            # Check if we've reached the maximum tweets for today
            if (
                self.tweet_count_today
                >= self.config.get_tweet_schedule()["max_tweets_per_day"]
            ):
                logger.info(
                    "Maximum tweets for today reached, ignoring WebSocket signal"
                )
                return

            # Generate tweet from signal
            tweet_data = {
                "success": True,
                "action": "tweet",
                "tweet_text": self._generate_signal_tweet_text(signal_data),
                "coin": signal_data.get("coin"),
                "price": signal_data.get("price"),
                "signal_type": "websocket",
                "source": "trading_signal",
            }

            # Post tweet
            self._post_tweet(tweet_data)

        except Exception as e:
            logger.error(f"Failed to handle WebSocket signal: {str(e)}", exc_info=True)
            self.slack_notifier.send_error(
                f"Failed to handle WebSocket signal: {str(e)}"
            )

    def _generate_signal_tweet_text(self, signal_data: Dict[str, Any]) -> str:
        """
        Generate tweet text for a trading signal.

        Args:
            signal_data: The signal data.

        Returns:
            The tweet text.
        """
        coin = signal_data.get("coin")
        price = signal_data.get("price")
        signal_15m = signal_data.get("15m_signal")
        signal_1h = signal_data.get("1h_signal")

        # Format price with appropriate precision
        if price < 0.1:
            price_str = f"${price:.4f}"
        elif price < 1:
            price_str = f"${price:.3f}"
        elif price < 10:
            price_str = f"${price:.2f}"
        else:
            price_str = f"${price:.1f}"

        # Determine signal type
        if signal_15m == 1 and signal_1h == 1:
            tweet_text = f"🚨 SIGNAL ALERT: $HL-{coin} showing strong bullish momentum! Both 15m and 1h EMAs crossed bullish at {price_str}. Potential long opportunity? #HyperLiquid #TradingSignal"
        elif signal_15m == 1 and signal_1h == -1:
            tweet_text = f"📊 SIGNAL UPDATE: $HL-{coin} showing short-term bullish momentum at {price_str}. 15m EMA crossed up but 1h still bearish. Scalp opportunity? #HyperLiquid #TradingSignal"
        elif signal_15m == -1 and signal_1h == 1:
            tweet_text = f"📊 SIGNAL UPDATE: $HL-{coin} showing long-term bullish momentum at {price_str}. 1h EMA crossed up but 15m still bearish. Swing trade setup? #HyperLiquid #TradingSignal"
        elif signal_15m == -1 and signal_1h == -1:
            tweet_text = f"🚨 SIGNAL ALERT: $HL-{coin} showing strong bearish momentum! Both 15m and 1h EMAs crossed bearish at {price_str}. Potential short opportunity? #HyperLiquid #TradingSignal"
        else:
            tweet_text = f"📊 SIGNAL UPDATE: $HL-{coin} at {price_str} with mixed momentum indicators. No clear trend direction at the moment. #HyperLiquid #TradingSignal"

        # Add disclaimer
        tweet_text += "\n\n⚠️ Not financial advice. DYOR."

        return tweet_text
