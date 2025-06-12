"""
Twitter client module for the hypexbt Twitter bot.

This module handles interactions with the Twitter API for posting tweets,
retweeting, and fetching tweets from other accounts.
"""

import logging
import time
import random
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

import tweepy

from src.utils.config import Config

logger = logging.getLogger(__name__)


class TwitterClient:
    """
    Client for interacting with the Twitter API.
    """

    def __init__(self, config: Config):
        """
        Initialize the Twitter client.

        Args:
            config: The configuration object.
        """
        self.config = config
        self.api_key = config.get_twitter_credentials()["api_key"]
        self.api_secret = config.get_twitter_credentials()["api_secret"]
        self.bearer_token = config.get_twitter_credentials()["bearer_token"]

        # Initialize API clients
        self._init_client()

    def _init_client(self):
        """Initialize the Twitter API clients."""
        try:
            # Initialize v1 client (for compatibility with some operations)
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.config.get_twitter_credentials().get("access_token"),
                self.config.get_twitter_credentials().get("access_token_secret"),
            )
            self.api_v1 = tweepy.API(auth)

            # Initialize v2 client
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.config.get_twitter_credentials().get("access_token"),
                access_token_secret=self.config.get_twitter_credentials().get(
                    "access_token_secret"
                ),
            )

            logger.info("Twitter client initialized successfully")

        except Exception as e:
            logger.error(
                f"Failed to initialize Twitter client: {str(e)}", exc_info=True
            )
            raise

    def post_tweet(self, text: str, media_ids: List[str] = None) -> Dict[str, Any]:
        """
        Post a tweet.

        Args:
            text: The tweet text.
            media_ids: Optional list of media IDs to attach to the tweet.

        Returns:
            The response from the Twitter API.
        """
        try:
            # Check tweet length
            if len(text) > 280:
                logger.warning(f"Tweet text exceeds 280 characters, truncating: {text}")
                text = text[:277] + "..."

            # Post the tweet
            response = self.client.create_tweet(text=text, media_ids=media_ids)

            logger.info(f"Posted tweet: {text[:50]}...")
            return response.data

        except Exception as e:
            logger.error(f"Failed to post tweet: {str(e)}", exc_info=True)
            raise

    def retweet(self, tweet_id: str) -> Dict[str, Any]:
        """
        Retweet a tweet.

        Args:
            tweet_id: The ID of the tweet to retweet.

        Returns:
            The response from the Twitter API.
        """
        try:
            # Retweet
            response = self.client.retweet(tweet_id)

            logger.info(f"Retweeted tweet {tweet_id}")
            return response.data

        except Exception as e:
            logger.error(f"Failed to retweet {tweet_id}: {str(e)}", exc_info=True)
            raise

    def quote_tweet(self, tweet_id: str, text: str) -> Dict[str, Any]:
        """
        Quote tweet.

        Args:
            tweet_id: The ID of the tweet to quote.
            text: The text to add to the quote.

        Returns:
            The response from the Twitter API.
        """
        try:
            # Get the tweet URL
            tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"

            # Check tweet length
            if len(text) + len(tweet_url) + 1 > 280:  # +1 for space
                logger.warning(
                    f"Quote tweet text exceeds 280 characters, truncating: {text}"
                )
                text = text[: 277 - len(tweet_url)] + "..."

            # Post the quote tweet
            response = self.client.create_tweet(text=f"{text} {tweet_url}")

            logger.info(f"Quote tweeted {tweet_id}: {text[:50]}...")
            return response.data

        except Exception as e:
            logger.error(f"Failed to quote tweet {tweet_id}: {str(e)}", exc_info=True)
            raise

    def get_user_timeline(self, username: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get tweets from a user's timeline.

        Args:
            username: The Twitter username.
            count: The number of tweets to fetch.

        Returns:
            A list of tweets.
        """
        try:
            # Get user ID
            user = self.client.get_user(username=username)
            user_id = user.data.id

            # Get timeline
            response = self.client.get_users_tweets(
                id=user_id,
                max_results=count,
                tweet_fields=["created_at", "text", "public_metrics"],
            )

            tweets = []
            if response.data:
                for tweet in response.data:
                    tweets.append(
                        {
                            "id": tweet.id,
                            "text": tweet.text,
                            "created_at": tweet.created_at,
                            "public_metrics": tweet.public_metrics,
                        }
                    )

            logger.info(f"Fetched {len(tweets)} tweets from @{username}")
            return tweets

        except Exception as e:
            logger.error(
                f"Failed to fetch tweets from @{username}: {str(e)}", exc_info=True
            )
            return []

    def search_tweets(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Search for tweets.

        Args:
            query: The search query.
            count: The number of tweets to fetch.

        Returns:
            A list of tweets.
        """
        try:
            # Search tweets
            response = self.client.search_recent_tweets(
                query=query,
                max_results=count,
                tweet_fields=["created_at", "text", "public_metrics", "author_id"],
            )

            tweets = []
            if response.data:
                for tweet in response.data:
                    tweets.append(
                        {
                            "id": tweet.id,
                            "text": tweet.text,
                            "created_at": tweet.created_at,
                            "public_metrics": tweet.public_metrics,
                            "author_id": tweet.author_id,
                        }
                    )

            logger.info(f"Searched for '{query}', found {len(tweets)} tweets")
            return tweets

        except Exception as e:
            logger.error(
                f"Failed to search tweets for '{query}': {str(e)}", exc_info=True
            )
            return []

    def upload_media(self, media_path: str) -> str:
        """
        Upload media to Twitter.

        Args:
            media_path: The path to the media file.

        Returns:
            The media ID.
        """
        try:
            # Upload media
            media = self.api_v1.media_upload(media_path)

            logger.info(f"Uploaded media {media_path}, got media ID {media.media_id}")
            return media.media_id

        except Exception as e:
            logger.error(
                f"Failed to upload media {media_path}: {str(e)}", exc_info=True
            )
            raise

    def get_hyperliquid_tweets(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get tweets from Hyperliquid accounts.

        Args:
            count: The number of tweets to fetch.

        Returns:
            A list of tweets.
        """
        try:
            # Get tweets from both accounts
            hyperliquid_tweets = self.get_user_timeline(
                username="HyperliquidExch", count=count
            )
            hyperliquid_labs_tweets = self.get_user_timeline(
                username="HyperliquidLabs", count=count
            )

            # Combine and sort by created_at
            all_tweets = hyperliquid_tweets + hyperliquid_labs_tweets
            all_tweets.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            # Return the latest tweets
            return all_tweets[:count]

        except Exception as e:
            logger.error(f"Failed to fetch Hyperliquid tweets: {str(e)}", exc_info=True)
            return []

    def get_liquidlaunch_tweets(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get tweets from LiquidLaunch account.

        Args:
            count: The number of tweets to fetch.

        Returns:
            A list of tweets.
        """
        try:
            # Get tweets
            return self.get_user_timeline(username="LiquidLaunchHL", count=count)

        except Exception as e:
            logger.error(
                f"Failed to fetch LiquidLaunch tweets: {str(e)}", exc_info=True
            )
            return []

    def is_rate_limited(self) -> bool:
        """
        Check if the client is rate limited.

        Returns:
            True if rate limited, False otherwise.
        """
        try:
            # Try to fetch a single tweet
            self.client.get_users_tweets(id=self.client.get_me().data.id, max_results=1)
            return False
        except tweepy.TooManyRequests:
            return True
        except:
            return False
