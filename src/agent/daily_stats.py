"""
Daily stats tweet generator for the hypexbt Twitter bot.

This module generates tweets about daily Hyperliquid statistics.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Any

from src.sources.hyperliquid_client import HyperliquidClient

logger = logging.getLogger(__name__)


class DailyStatsTweetGenerator:
    """
    Generator for daily stats tweets.
    """

    def __init__(self, hyperliquid_client: HyperliquidClient):
        """
        Initialize the daily stats tweet generator.

        Args:
            hyperliquid_client: The Hyperliquid client.
        """
        self.hyperliquid_client = hyperliquid_client

        # Keep track of last tweet time to avoid tweeting too frequently
        self.last_tweet_time = None

    def generate_tweet(self) -> dict[str, Any]:
        """
        Generate a tweet about daily Hyperliquid statistics.

        Returns:
            A dictionary with tweet data.
        """
        try:
            # Check if we've already tweeted recently
            if (
                self.last_tweet_time is not None
                and datetime.now() - self.last_tweet_time < timedelta(hours=12)
            ):
                logger.info("Daily stats tweet already sent recently")
                return {
                    "success": False,
                    "error": "Daily stats tweet already sent recently",
                }

            # Get daily stats
            stats = self.hyperliquid_client.get_daily_stats()

            if not stats:
                logger.warning("No daily stats found")
                return {"success": False, "error": "No daily stats found"}

            # Format stats
            total_volume = stats.get("total_volume_24h", 0)
            total_oi = stats.get("total_open_interest", 0)
            top_gainers = stats.get("top_gainers", [])
            top_losers = stats.get("top_losers", [])

            # Format volume and OI with appropriate units
            if total_volume >= 1_000_000_000:
                volume_str = f"${total_volume / 1_000_000_000:.1f}B"
            elif total_volume >= 1_000_000:
                volume_str = f"${total_volume / 1_000_000:.1f}M"
            else:
                volume_str = f"${total_volume / 1_000:.1f}K"

            if total_oi >= 1_000_000_000:
                oi_str = f"${total_oi / 1_000_000_000:.1f}B"
            elif total_oi >= 1_000_000:
                oi_str = f"${total_oi / 1_000_000:.1f}M"
            else:
                oi_str = f"${total_oi / 1_000:.1f}K"

            # Format top gainers and losers
            gainers_str = ""
            if top_gainers:
                gainers_str = "📈 Top gainers:\n"
                for i, gainer in enumerate(top_gainers[:3], 1):
                    gainers_str += f"{i}. ${gainer.get('coin')}: +{gainer.get('change_pct', 0):.1f}%\n"

            losers_str = ""
            if top_losers:
                losers_str = "📉 Top losers:\n"
                for i, loser in enumerate(top_losers[:3], 1):
                    losers_str += f"{i}. ${loser.get('coin')}: {loser.get('change_pct', 0):.1f}%\n"

            # Generate tweet text
            tweet_templates = [
                f"📊 Daily @HyperliquidExch Stats 📊\n\n24h Volume: {volume_str}\nOpen Interest: {oi_str}\n\n{gainers_str}\n{losers_str}\n#HyperLiquid #DailyStats",
                f"🔥 Hyperliquid is popping off, anon! 🔥\n\n24h Volume: {volume_str}\nTotal OI: {oi_str}\n\n{gainers_str}\n{losers_str}\n#HyperLiquid #DailyStats",
                f"👀 Check out today's @HyperliquidExch numbers!\n\nVolume: {volume_str} (24h)\nOI: {oi_str}\n\n{gainers_str}\n{losers_str}\n#HyperLiquid #DailyStats",
                f"💹 Hyperliquid Daily Metrics 💹\n\n24h Trading Volume: {volume_str}\nTotal Open Interest: {oi_str}\n\n{gainers_str}\n{losers_str}\n#HyperLiquid #DailyStats",
            ]

            tweet_text = random.choice(tweet_templates)

            # Update last tweet time
            self.last_tweet_time = datetime.now()

            return {
                "success": True,
                "action": "tweet",
                "tweet_text": tweet_text,
                "volume": total_volume,
                "open_interest": total_oi,
                "source": "daily_stats",
            }

        except Exception as e:
            logger.error(f"Failed to generate daily stats tweet: {e!s}", exc_info=True)
            return {"success": False, "error": str(e)}
