"""
Tests for tweet generator modules.
"""

import unittest
from unittest.mock import Mock

from src.agent.daily_stats import DailyStatsTweetGenerator
from src.agent.hyperliquid_news import HyperliquidNewsTweetGenerator
from src.agent.token_fundamentals import TokenFundamentalsTweetGenerator
from src.agent.token_graduation import TokenGraduationTweetGenerator
from src.agent.token_launch import TokenLaunchTweetGenerator
from src.agent.trading_signal import TradingSignalTweetGenerator


class TestTweetGenerators(unittest.TestCase):
    """Test cases for the tweet generators."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock clients
        self.mock_twitter_client = Mock()
        self.mock_hyperliquid_client = Mock()
        self.mock_liquidlaunch_client = Mock()
        self.mock_coingecko_client = Mock()

        # Create generators
        self.hyperliquid_news_generator = HyperliquidNewsTweetGenerator(
            self.mock_twitter_client
        )
        self.token_launch_generator = TokenLaunchTweetGenerator(
            self.mock_liquidlaunch_client
        )
        self.token_graduation_generator = TokenGraduationTweetGenerator(
            self.mock_liquidlaunch_client
        )
        self.trading_signal_generator = TradingSignalTweetGenerator(
            self.mock_hyperliquid_client
        )
        self.daily_stats_generator = DailyStatsTweetGenerator(
            self.mock_hyperliquid_client
        )
        self.token_fundamentals_generator = TokenFundamentalsTweetGenerator(
            self.mock_coingecko_client, self.mock_hyperliquid_client
        )

    def test_hyperliquid_news_tweet_length(self):
        """Test that Hyperliquid news tweets are within the character limit."""
        # Mock get_hyperliquid_tweets
        self.mock_twitter_client.get_hyperliquid_tweets.return_value = [
            {
                "id": "123",
                "text": "This is a test tweet from Hyperliquid",
                "created_at": "2023-01-01T00:00:00Z",
                "public_metrics": {"retweet_count": 5, "like_count": 10},
            }
        ]

        # Generate tweet
        tweet_data = self.hyperliquid_news_generator.generate_tweet()

        # Check that tweet was generated successfully
        self.assertTrue(tweet_data["success"])

        # Check tweet length for retweet
        if tweet_data["action"] == "retweet":
            # No text to check for retweets
            pass

        # Check tweet length for quote tweet
        elif tweet_data["action"] == "quote_tweet":
            # Calculate total length (quote text + URL)
            quote_text = tweet_data["quote_text"]
            tweet_url = f"https://twitter.com/i/web/status/{tweet_data['tweet_id']}"
            total_length = len(quote_text) + len(tweet_url) + 1  # +1 for space

            # Check that total length is within limit
            self.assertLessEqual(total_length, 280)

    def test_token_launch_tweet_length(self):
        """Test that token launch tweets are within the character limit."""
        # Mock get_token_launches
        self.mock_liquidlaunch_client.get_token_launches.return_value = [
            {
                "token_name": "Test Token",
                "token_symbol": "TEST",
                "tweet_id": "123",
                "tweet_text": "New token launch: Test Token (TEST)",
                "created_at": "2023-01-01T00:00:00Z",
                "type": "launch",
            }
        ]

        # Generate tweet
        tweet_data = self.token_launch_generator.generate_tweet()

        # Check that tweet was generated successfully
        self.assertTrue(tweet_data["success"])

        # Check tweet length
        self.assertLessEqual(len(tweet_data["tweet_text"]), 280)

    def test_token_graduation_tweet_length(self):
        """Test that token graduation tweets are within the character limit."""
        # Mock get_token_graduations
        self.mock_liquidlaunch_client.get_token_graduations.return_value = [
            {
                "token_name": "Test Token",
                "token_symbol": "TEST",
                "tweet_id": "123",
                "tweet_text": "Token graduation: Test Token (TEST)",
                "created_at": "2023-01-01T00:00:00Z",
                "type": "graduation",
            }
        ]

        # Generate tweet
        tweet_data = self.token_graduation_generator.generate_tweet()

        # Check that tweet was generated successfully
        self.assertTrue(tweet_data["success"])

        # Check tweet length
        self.assertLessEqual(len(tweet_data["tweet_text"]), 280)

    def test_trading_signal_tweet_length(self):
        """Test that trading signal tweets are within the character limit."""
        # Mock get_metadata
        self.mock_hyperliquid_client.get_metadata.return_value = [
            {"universe": [{"name": "BTC"}, {"name": "ETH"}]}
        ]

        # Mock calculate_momentum_signals
        self.mock_hyperliquid_client.calculate_momentum_signals.return_value = {
            "coin": "BTC",
            "price": 50000,
            "15m_signal": 1,
            "15m_signal_change": True,
            "1h_signal": 1,
            "1h_signal_change": True,
            "timestamp": "2023-01-01T00:00:00Z",
        }

        # Generate tweet
        tweet_data = self.trading_signal_generator.generate_tweet()

        # Check that tweet was generated successfully
        self.assertTrue(tweet_data["success"])

        # Check tweet length
        self.assertLessEqual(len(tweet_data["tweet_text"]), 280)

    def test_daily_stats_tweet_length(self):
        """Test that daily stats tweets are within the character limit."""
        # Mock get_daily_stats
        self.mock_hyperliquid_client.get_daily_stats.return_value = {
            "total_volume_24h": 1000000000,
            "total_open_interest": 500000000,
            "top_gainers": [
                {"coin": "BTC", "price": 50000, "change_pct": 5.0},
                {"coin": "ETH", "price": 3000, "change_pct": 4.0},
                {"coin": "SOL", "price": 100, "change_pct": 3.0},
            ],
            "top_losers": [
                {"coin": "DOGE", "price": 0.1, "change_pct": -2.0},
                {"coin": "SHIB", "price": 0.00001, "change_pct": -3.0},
                {"coin": "LINK", "price": 20, "change_pct": -4.0},
            ],
            "timestamp": "2023-01-01T00:00:00Z",
        }

        # Generate tweet
        tweet_data = self.daily_stats_generator.generate_tweet()

        # Check that tweet was generated successfully
        self.assertTrue(tweet_data["success"])

        # Check tweet length
        self.assertLessEqual(len(tweet_data["tweet_text"]), 280)

    def test_token_fundamentals_tweet_length(self):
        """Test that token fundamentals tweets are within the character limit."""
        # Mock get_metadata
        self.mock_hyperliquid_client.get_metadata.return_value = [
            {"universe": [{"name": "BTC"}, {"name": "ETH"}]}
        ]

        # Mock get_token_fundamentals
        self.mock_coingecko_client.get_token_fundamentals.return_value = {
            "name": "Bitcoin",
            "symbol": "btc",
            "current_price": 50000,
            "market_cap": 1000000000000,
            "fully_diluted_valuation": 1100000000000,
            "circulating_supply": 19000000,
            "total_supply": 21000000,
            "price_change_percentage_24h": 2.5,
        }

        # Generate tweet
        tweet_data = self.token_fundamentals_generator.generate_tweet()

        # Check that tweet was generated successfully
        self.assertTrue(tweet_data["success"])

        # Check tweet length
        self.assertLessEqual(len(tweet_data["tweet_text"]), 280)


if __name__ == "__main__":
    unittest.main()
