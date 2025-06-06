"""
Token launch tweet generator for the hypexbt Twitter bot.

This module generates tweets about new token launches on LiquidLaunch.
"""

import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from bot.data_sources.liquidlaunch_client import LiquidLaunchClient

logger = logging.getLogger(__name__)


class TokenLaunchTweetGenerator:
    """
    Generator for token launch tweets.
    """

    def __init__(self, liquidlaunch_client: LiquidLaunchClient):
        """
        Initialize the token launch tweet generator.

        Args:
            liquidlaunch_client: The LiquidLaunch client.
        """
        self.liquidlaunch_client = liquidlaunch_client

        # Keep track of tweeted launches to avoid duplicates
        self.tweeted_launches = set()

    def generate_tweet(self) -> Dict[str, Any]:
        """
        Generate a tweet about a new token launch.

        Returns:
            A dictionary with tweet data.
        """
        try:
            # Get recent token launches
            launches = self.liquidlaunch_client.get_token_launches(force_refresh=True)

            if not launches:
                logger.warning("No token launches found")
                return {"success": False, "error": "No token launches found"}

            # Filter out launches that have already been tweeted
            eligible_launches = [
                launch
                for launch in launches
                if launch.get("token_symbol") not in self.tweeted_launches
            ]

            if not eligible_launches:
                logger.warning("No new token launches found")
                return {"success": False, "error": "No new token launches found"}

            # Select the most recent launch
            selected_launch = eligible_launches[0]

            # Add to tweeted launches
            self.tweeted_launches.add(selected_launch.get("token_symbol"))

            # Generate tweet text
            tweet_texts = [
                f"🚀 Fresh Token Launch Alert! ${selected_launch.get('token_symbol')} ({selected_launch.get('token_name')}) just launched on @LiquidLaunchHL! Get in early, anon! #HyperLiquid #LiquidLaunch",
                f"💎 New gem alert! ${selected_launch.get('token_symbol')} has just launched on LiquidLaunch! Early birds get the alpha 👀 #HyperLiquid #LiquidLaunch",
                f"🔥 ${selected_launch.get('token_symbol')} just dropped on @LiquidLaunchHL! Another fresh token for the HyperEVM ecosystem! Who's aping in? #HyperLiquid #LiquidLaunch",
                f"📢 Attention HyperLiquid fam! ${selected_launch.get('token_symbol')} ({selected_launch.get('token_name')}) is now live on LiquidLaunch! Early liquidity looking juicy 💦 #HyperLiquid #LiquidLaunch",
                f"🆕 Fresh token just launched! ${selected_launch.get('token_symbol')} is now available on @LiquidLaunchHL - another exciting project in the HyperLiquid ecosystem! #HyperLiquid #LiquidLaunch",
            ]

            tweet_text = random.choice(tweet_texts)

            return {
                "success": True,
                "action": "tweet",
                "tweet_text": tweet_text,
                "token_symbol": selected_launch.get("token_symbol"),
                "token_name": selected_launch.get("token_name"),
                "source": "token_launch",
            }

        except Exception as e:
            logger.error(
                f"Failed to generate token launch tweet: {str(e)}", exc_info=True
            )
            return {"success": False, "error": str(e)}
