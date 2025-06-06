"""
Hyperliquid news tweet generator for the hypexbt Twitter bot.

This module generates tweets about Hyperliquid news and memes.
"""

import logging
import random
from typing import Dict, List, Any, Optional

from bot.twitter_client import TwitterClient

logger = logging.getLogger(__name__)


class HyperliquidNewsTweetGenerator:
    """
    Generator for Hyperliquid news tweets.
    """

    def __init__(self, twitter_client: TwitterClient):
        """
        Initialize the Hyperliquid news tweet generator.

        Args:
            twitter_client: The Twitter client.
        """
        self.twitter_client = twitter_client

    def generate_tweet(self) -> Dict[str, Any]:
        """
        Generate a tweet about Hyperliquid news or memes.

        Returns:
            A dictionary with tweet data.
        """
        try:
            # Get recent tweets from Hyperliquid accounts
            tweets = self.twitter_client.get_hyperliquid_tweets(count=20)

            if not tweets:
                logger.warning("No Hyperliquid tweets found")
                return {"success": False, "error": "No Hyperliquid tweets found"}

            # Filter out tweets that are replies or have already been retweeted
            eligible_tweets = [
                tweet
                for tweet in tweets
                if not tweet.get("text", "").startswith("@")  # Not a reply
                and tweet.get("public_metrics", {}).get("retweet_count", 0)
                > 0  # Has some engagement
            ]

            if not eligible_tweets:
                logger.warning("No eligible Hyperliquid tweets found")
                return {
                    "success": False,
                    "error": "No eligible Hyperliquid tweets found",
                }

            # Select a random tweet
            selected_tweet = random.choice(eligible_tweets)

            # Decide whether to retweet or quote tweet
            if random.random() < 0.7:  # 70% chance to retweet
                action = "retweet"
            else:  # 30% chance to quote tweet
                action = "quote_tweet"

                # Generate quote text
                quote_texts = [
                    "Check this out from the @HyperliquidExch team! 🔥",
                    "Big news from @HyperliquidExch! 👀",
                    "Interesting update from the Hyperliquid team 👇",
                    "This is bullish for $HLP! 🚀",
                    "Hyperliquid keeps building! 💪",
                    "The future of perp trading is here! 📈",
                    "Hyperliquid ecosystem keeps growing! 🌱",
                    "Anon, you need to see this from @HyperliquidExch! 👇",
                    "Hyperliquid making moves! 🏆",
                    "Bullish development from @HyperliquidExch! 🔥",
                ]
                quote_text = random.choice(quote_texts)

            return {
                "success": True,
                "action": action,
                "tweet_id": selected_tweet.get("id"),
                "tweet_text": selected_tweet.get("text"),
                "quote_text": quote_text if action == "quote_tweet" else None,
                "source": "hyperliquid_news",
            }

        except Exception as e:
            logger.error(
                f"Failed to generate Hyperliquid news tweet: {str(e)}", exc_info=True
            )
            return {"success": False, "error": str(e)}
