"""
Tests for the TweetScheduler module.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.core.scheduler import TweetScheduler
from src.utils.config import Config


class TestTweetScheduler(unittest.TestCase):
    """Test cases for the tweet scheduler."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock config
        self.mock_config = MagicMock(spec=Config)
        self.mock_config.get_tweet_schedule.return_value = {
            "min_tweets_per_day": 10,
            "max_tweets_per_day": 20,
            "min_interval_minutes": 30,
            "max_interval_minutes": 180,
            "active_hours_start": 0,
            "active_hours_end": 23,
        }
        self.mock_config.get_tweet_distribution.return_value = {
            "hyperliquid_news": 0.15,
            "token_launches": 0.20,
            "token_graduations": 0.20,
            "trading_signals": 0.15,
            "daily_stats": 0.15,
            "token_fundamentals": 0.15,
        }

        # Patch clients and generators
        self.patches = []

        # Patch TwitterClient initialization
        self.twitter_client_patcher = patch("src.core.scheduler.TwitterClient")
        self.mock_twitter_client_class = self.twitter_client_patcher.start()
        self.mock_twitter_client = MagicMock()
        self.mock_twitter_client_class.return_value = self.mock_twitter_client

        # Patch HyperliquidClient initialization
        self.hyperliquid_client_patcher = patch("src.core.scheduler.HyperliquidClient")
        self.mock_hyperliquid_client_class = self.hyperliquid_client_patcher.start()
        self.mock_hyperliquid_client = MagicMock()
        self.mock_hyperliquid_client_class.return_value = self.mock_hyperliquid_client

        # Patch LiquidLaunchClient initialization
        self.liquidlaunch_client_patcher = patch(
            "src.core.scheduler.LiquidLaunchClient"
        )
        self.mock_liquidlaunch_client_class = self.liquidlaunch_client_patcher.start()
        self.mock_liquidlaunch_client = MagicMock()
        self.mock_liquidlaunch_client_class.return_value = self.mock_liquidlaunch_client

        # Patch CoinGeckoClient initialization
        self.coingecko_client_patcher = patch("src.core.scheduler.CoinGeckoClient")
        self.mock_coingecko_client_class = self.coingecko_client_patcher.start()
        self.mock_coingecko_client = MagicMock()
        self.mock_coingecko_client_class.return_value = self.mock_coingecko_client

        # Patch TweetScheduler initialization
        self.scheduler_patcher = patch("src.agent.scheduler.TweetScheduler.__init__")
        self.mock_scheduler_init = self.scheduler_patcher.start()
        self.mock_scheduler_init.return_value = None

        for generator in [
            "hyperliquid_news",
            "token_launch",
            "token_graduation",
            "trading_signal",
            "daily_stats",
            "token_fundamentals",
        ]:
            patcher = patch(
                f"src.core.scheduler.{generator.split('_')[0].capitalize()}{generator.split('_')[1].capitalize()}TweetGenerator"
            )
            self.patches.append(patcher)
            setattr(self, f"mock_{generator}_generator_class", patcher.start())
            setattr(self, f"mock_{generator}_generator", MagicMock())
            getattr(self, f"mock_{generator}_generator_class").return_value = getattr(
                self, f"mock_{generator}_generator"
            )

        # Patch scheduler
        self.scheduler_patcher = patch("src.core.scheduler.BackgroundScheduler")
        self.mock_scheduler_class = self.scheduler_patcher.start()
        self.mock_scheduler = MagicMock()
        self.mock_scheduler_class.return_value = self.mock_scheduler

        # Create scheduler
        self.tweet_scheduler = TweetScheduler(self.mock_config)

    def tearDown(self):
        """Tear down test fixtures."""
        self.scheduler_patcher.stop()
        for patcher in self.patches:
            patcher.stop()

    def test_init(self):
        """Test initialization."""
        # Check that scheduler was initialized
        self.mock_scheduler_class.assert_called_once()

        # Check that clients were initialized
        self.mock_twitter_client_class.assert_called_once_with(self.mock_config)
        self.mock_hyperliquid_client_class.assert_called_once_with(self.mock_config)
        self.mock_liquidlaunch_client_class.assert_called_once_with(self.mock_config)
        self.mock_coingecko_client_class.assert_called_once_with(self.mock_config)

        # Check that generators were initialized
        self.mock_hyperliquid_news_generator_class.assert_called_once_with(
            self.mock_twitter_client
        )
        self.mock_token_launch_generator_class.assert_called_once_with(
            self.mock_liquidlaunch_client
        )
        self.mock_token_graduation_generator_class.assert_called_once_with(
            self.mock_liquidlaunch_client
        )
        self.mock_trading_signal_generator_class.assert_called_once_with(
            self.mock_hyperliquid_client
        )
        self.mock_daily_stats_generator_class.assert_called_once_with(
            self.mock_hyperliquid_client
        )
        self.mock_token_fundamentals_generator_class.assert_called_once_with(
            self.mock_coingecko_client, self.mock_hyperliquid_client
        )

        # Check that jobs were added to scheduler
        self.assertEqual(self.mock_scheduler.add_job.call_count, 5)

        self.mock_config.assert_called_once()

    def test_generate_tweet_schedule(self):
        """Test generating a tweet schedule."""
        # Call method
        self.tweet_scheduler._generate_tweet_schedule()

        # Check that tweet queue was populated
        self.assertGreater(len(self.tweet_scheduler.tweet_queue), 0)

        # Check that tweets are scheduled within active hours
        active_hours = list(
            range(
                self.mock_config.get_tweet_schedule()["active_hours_start"],
                self.mock_config.get_tweet_schedule()["active_hours_end"] + 1,
            )
        )

        for tweet in self.tweet_scheduler.tweet_queue:
            self.assertIn(tweet["scheduled_time"].hour, active_hours)

    def test_tweet_count_limit(self):
        """Test that tweet count is limited to max_tweets_per_day."""
        # Set tweet count to max
        self.tweet_scheduler.tweet_count_today = self.mock_config.get_tweet_schedule()[
            "max_tweets_per_day"
        ]

        # Call method
        self.tweet_scheduler._generate_tweet_schedule()

        # Check that no tweets were scheduled
        self.assertEqual(len(self.tweet_scheduler.tweet_queue), 0)

    def test_post_tweet(self):
        """Test posting a tweet."""
        # Mock tweet data
        tweet_data = {"action": "tweet", "tweet_text": "Test tweet", "source": "test"}

        # Mock response
        self.mock_twitter_client.post_tweet.return_value = {
            "id": "123",
            "text": "Test tweet",
        }

        # Call method
        self.tweet_scheduler._post_tweet(tweet_data)

        # Check that post_tweet was called with the correct arguments
        self.mock_twitter_client.post_tweet.assert_called_once_with("Test tweet")

        # Check that tweet count was incremented
        self.assertEqual(self.tweet_scheduler.tweet_count_today, 1)

        # Check that tweet was added to history
        self.assertEqual(len(self.tweet_scheduler.tweet_history), 1)
        self.assertEqual(
            self.tweet_scheduler.tweet_history[0]["tweet_data"], tweet_data
        )

    def test_reset_tweet_count(self):
        """Test resetting the tweet count."""
        # Set tweet count
        self.tweet_scheduler.tweet_count_today = 10

        # Call method
        self.tweet_scheduler._reset_tweet_count()

        # Check that tweet count was reset
        self.assertEqual(self.tweet_scheduler.tweet_count_today, 0)

        # Check that last count reset was updated
        self.assertEqual(self.tweet_scheduler.last_count_reset, datetime.now().date())

    def test_process_tweet_queue(self):
        """Test processing the tweet queue."""
        # Add a tweet to the queue
        self.tweet_scheduler.tweet_queue = [
            {
                "type": "hyperliquid_news",
                "scheduled_time": datetime.now() - timedelta(minutes=1),
            }
        ]

        # Mock generator
        self.mock_hyperliquid_news_generator.generate_tweet.return_value = {
            "success": True,
            "action": "tweet",
            "tweet_text": "Test tweet",
            "source": "hyperliquid_news",
        }

        # Mock post_tweet
        self.tweet_scheduler._post_tweet = MagicMock()

        # Call method
        self.tweet_scheduler._process_tweet_queue()

        # Check that generate_tweet was called
        self.mock_hyperliquid_news_generator.generate_tweet.assert_called_once()

        # Check that post_tweet was called
        self.tweet_scheduler._post_tweet.assert_called_once()

        # Check that tweet was removed from queue
        self.assertEqual(len(self.tweet_scheduler.tweet_queue), 0)

    def test_process_tweet_queue_max_tweets(self):
        """Test processing the tweet queue when max tweets is reached."""
        # Add a tweet to the queue
        self.tweet_scheduler.tweet_queue = [
            {
                "type": "hyperliquid_news",
                "scheduled_time": datetime.now() - timedelta(minutes=1),
            }
        ]

        # Set tweet count to max
        self.tweet_scheduler.tweet_count_today = self.mock_config.get_tweet_schedule()[
            "max_tweets_per_day"
        ]

        # Call method
        self.tweet_scheduler._process_tweet_queue()

        # Check that queue was cleared
        self.assertEqual(len(self.tweet_scheduler.tweet_queue), 0)

        # Check that generate_tweet was not called
        self.mock_hyperliquid_news_generator.generate_tweet.assert_not_called()


if __name__ == "__main__":
    unittest.main()
