"""
Token graduation tweet generator for the hypexbt Twitter bot.

This module generates tweets about token graduations/migrations on LiquidLaunch.
"""

import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from bot.data_sources.liquidlaunch_client import LiquidLaunchClient

logger = logging.getLogger(__name__)


class TokenGraduationTweetGenerator:
    """
    Generator for token graduation tweets.
    """

    def __init__(self, liquidlaunch_client: LiquidLaunchClient):
        """
        Initialize the token graduation tweet generator.

        Args:
            liquidlaunch_client: The LiquidLaunch client.
        """
        self.liquidlaunch_client = liquidlaunch_client

        # Keep track of tweeted graduations to avoid duplicates
        self.tweeted_graduations = set()

    def generate_tweet(self) -> Dict[str, Any]:
        """
        Generate a tweet about a token graduation/migration.

        Returns:
            A dictionary with tweet data.
        """
        try:
            # Get recent token graduations
            graduations = self.liquidlaunch_client.get_token_graduations(
                force_refresh=True
            )

            if not graduations:
                logger.warning("No token graduations found")
                return {"success": False, "error": "No token graduations found"}

            # Filter out graduations that have already been tweeted
            eligible_graduations = [
                graduation
                for graduation in graduations
                if graduation.get("token_symbol") not in self.tweeted_graduations
            ]

            if not eligible_graduations:
                logger.warning("No new token graduations found")
                return {"success": False, "error": "No new token graduations found"}

            # Select the most recent graduation
            selected_graduation = eligible_graduations[0]

            # Add to tweeted graduations
            self.tweeted_graduations.add(selected_graduation.get("token_symbol"))

            # Generate tweet text
            tweet_texts = [
                f"🎓 Token Graduation Alert! ${selected_graduation.get('token_symbol')} has graduated from @LiquidLaunchHL and is now available for trading on @HyperliquidExch! Congrats to the team! #HyperLiquid #LiquidLaunch",
                f"🚀 ${selected_graduation.get('token_symbol')} has successfully migrated from LiquidLaunch to the main HyperLiquid exchange! Trading is now live! #HyperLiquid #LiquidLaunch",
                f"🔄 Migration complete! ${selected_graduation.get('token_symbol')} ({selected_graduation.get('token_name')}) has moved from LiquidLaunch to @HyperliquidExch - trading now available! #HyperLiquid #LiquidLaunch",
                f"📈 ${selected_graduation.get('token_symbol')} has officially graduated! Now trading on the main @HyperliquidExch platform. From LiquidLaunch to the big leagues! #HyperLiquid #LiquidLaunch",
                f"🏆 Another successful token journey! ${selected_graduation.get('token_symbol')} has completed its LiquidLaunch phase and is now trading on HyperLiquid Exchange! #HyperLiquid #LiquidLaunch",
            ]

            tweet_text = random.choice(tweet_texts)

            return {
                "success": True,
                "action": "tweet",
                "tweet_text": tweet_text,
                "token_symbol": selected_graduation.get("token_symbol"),
                "token_name": selected_graduation.get("token_name"),
                "source": "token_graduation",
            }

        except Exception as e:
            logger.error(
                f"Failed to generate token graduation tweet: {str(e)}", exc_info=True
            )
            return {"success": False, "error": str(e)}
