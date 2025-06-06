"""
Tests for the Twitter client module.
"""

import unittest
from unittest.mock import patch, MagicMock

from bot.twitter_client import TwitterClient
from bot.utils.config import Config


class TestTwitterClient(unittest.TestCase):
    """Test cases for the Twitter client."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock config
        self.mock_config = MagicMock(spec=Config)
        self.mock_config.get_twitter_credentials.return_value = {
            "api_key": "test_api_key",
            "api_secret": "test_api_secret",
            "bearer_token": "test_bearer_token",
            "access_token": "test_access_token",
            "access_token_secret": "test_access_token_secret",
        }

        # Patch tweepy
        self.tweepy_patcher = patch("bot.twitter_client.tweepy")
        self.mock_tweepy = self.tweepy_patcher.start()

        # Mock tweepy.Client
        self.mock_client = MagicMock()
        self.mock_tweepy.Client.return_value = self.mock_client

        # Mock tweepy.API
        self.mock_api = MagicMock()
        self.mock_tweepy.API.return_value = self.mock_api

        # Create client
        self.client = TwitterClient(self.mock_config)

    def tearDown(self):
        """Tear down test fixtures."""
        self.tweepy_patcher.stop()

    def test_init(self):
        """Test initialization."""
        # Check that tweepy.Client was called with the correct arguments
        self.mock_tweepy.Client.assert_called_once_with(
            bearer_token="test_bearer_token",
            consumer_key="test_api_key",
            consumer_secret="test_api_secret",
            access_token="test_access_token",
            access_token_secret="test_access_token_secret",
        )

        # Check that tweepy.API was called
        self.mock_tweepy.API.assert_called_once()

    def test_post_tweet(self):
        """Test posting a tweet."""
        # Mock response
        mock_response = MagicMock()
        mock_response.data = {"id": "123", "text": "Test tweet"}
        self.mock_client.create_tweet.return_value = mock_response

        # Call method
        result = self.client.post_tweet("Test tweet")

        # Check that create_tweet was called with the correct arguments
        self.mock_client.create_tweet.assert_called_once_with(
            text="Test tweet", media_ids=None
        )

        # Check result
        self.assertEqual(result, {"id": "123", "text": "Test tweet"})

    def test_post_tweet_too_long(self):
        """Test posting a tweet that's too long."""
        # Create a tweet that's too long
        long_tweet = "x" * 281

        # Mock response
        mock_response = MagicMock()
        mock_response.data = {"id": "123", "text": long_tweet[:277] + "..."}
        self.mock_client.create_tweet.return_value = mock_response

        # Call method
        self.client.post_tweet(long_tweet)

        # Check that create_tweet was called with the truncated text
        self.mock_client.create_tweet.assert_called_once_with(
            text=long_tweet[:277] + "...", media_ids=None
        )

    def test_retweet(self):
        """Test retweeting."""
        # Mock response
        mock_response = MagicMock()
        mock_response.data = {"retweeted": True}
        self.mock_client.retweet.return_value = mock_response

        # Call method
        result = self.client.retweet("123")

        # Check that retweet was called with the correct arguments
        self.mock_client.retweet.assert_called_once_with("123")

        # Check result
        self.assertEqual(result, {"retweeted": True})

    def test_quote_tweet(self):
        """Test quote tweeting."""
        # Mock response
        mock_response = MagicMock()
        mock_response.data = {
            "id": "456",
            "text": "Quote tweet https://twitter.com/i/web/status/123",
        }
        self.mock_client.create_tweet.return_value = mock_response

        # Call method
        result = self.client.quote_tweet("123", "Quote tweet")

        # Check that create_tweet was called with the correct arguments
        self.mock_client.create_tweet.assert_called_once_with(
            text="Quote tweet https://twitter.com/i/web/status/123"
        )

        # Check result
        self.assertEqual(
            result,
            {"id": "456", "text": "Quote tweet https://twitter.com/i/web/status/123"},
        )

    def test_get_user_timeline(self):
        """Test getting a user's timeline."""
        # Mock responses
        mock_user = MagicMock()
        mock_user.data.id = "789"
        self.mock_client.get_user.return_value = mock_user

        mock_tweet1 = MagicMock()
        mock_tweet1.id = "1"
        mock_tweet1.text = "Tweet 1"
        mock_tweet1.created_at = "2023-01-01T00:00:00Z"
        mock_tweet1.public_metrics = {"retweet_count": 5, "like_count": 10}

        mock_tweet2 = MagicMock()
        mock_tweet2.id = "2"
        mock_tweet2.text = "Tweet 2"
        mock_tweet2.created_at = "2023-01-02T00:00:00Z"
        mock_tweet2.public_metrics = {"retweet_count": 3, "like_count": 7}

        mock_tweets_response = MagicMock()
        mock_tweets_response.data = [mock_tweet1, mock_tweet2]
        self.mock_client.get_users_tweets.return_value = mock_tweets_response

        # Call method
        result = self.client.get_user_timeline("test_user", count=2)

        # Check that get_user was called with the correct arguments
        self.mock_client.get_user.assert_called_once_with(username="test_user")

        # Check that get_users_tweets was called with the correct arguments
        self.mock_client.get_users_tweets.assert_called_once_with(
            id="789",
            max_results=2,
            tweet_fields=["created_at", "text", "public_metrics"],
        )

        # Check result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "1")
        self.assertEqual(result[0]["text"], "Tweet 1")
        self.assertEqual(result[0]["created_at"], "2023-01-01T00:00:00Z")
        self.assertEqual(
            result[0]["public_metrics"], {"retweet_count": 5, "like_count": 10}
        )
        self.assertEqual(result[1]["id"], "2")
        self.assertEqual(result[1]["text"], "Tweet 2")
        self.assertEqual(result[1]["created_at"], "2023-01-02T00:00:00Z")
        self.assertEqual(
            result[1]["public_metrics"], {"retweet_count": 3, "like_count": 7}
        )


if __name__ == "__main__":
    unittest.main()
