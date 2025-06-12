"""
Token fundamentals tweet generator for the hypexbt Twitter bot.

This module generates tweets about token fundamental analysis.
"""

import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from src.sources.coingecko_client import CoinGeckoClient
from src.sources.hyperliquid_client import HyperliquidClient

logger = logging.getLogger(__name__)


class TokenFundamentalsTweetGenerator:
    """
    Generator for token fundamentals tweets.
    """

    def __init__(
        self, coingecko_client: CoinGeckoClient, hyperliquid_client: HyperliquidClient
    ):
        """
        Initialize the token fundamentals tweet generator.

        Args:
            coingecko_client: The CoinGecko client.
            hyperliquid_client: The Hyperliquid client.
        """
        self.coingecko_client = coingecko_client
        self.hyperliquid_client = hyperliquid_client

        # Keep track of tweeted tokens to avoid duplicates
        self.tweeted_tokens = {}

        # Initialize with top coins
        self.top_coins = [
            "BTC",
            "ETH",
            "SOL",
            "AVAX",
            "MATIC",
            "LINK",
            "DOGE",
            "SHIB",
            "UNI",
            "AAVE",
        ]

    def generate_tweet(self) -> Dict[str, Any]:
        """
        Generate a tweet about token fundamentals.

        Returns:
            A dictionary with tweet data.
        """
        try:
            # Get metadata to get list of available coins
            metadata = self.hyperliquid_client.get_metadata()
            available_coins = [coin["name"] for coin in metadata[0]["universe"]]

            # Prioritize top coins but include others
            coins_to_check = list(
                set(self.top_coins).intersection(set(available_coins))
            )
            coins_to_check.extend(
                [coin for coin in available_coins if coin not in self.top_coins]
            )

            # Find a coin we haven't tweeted about recently
            selected_coin = None

            for coin in coins_to_check:
                # Check if we've already tweeted about this coin recently
                if coin in self.tweeted_tokens and datetime.now() - self.tweeted_tokens[
                    coin
                ] < timedelta(days=7):
                    continue

                selected_coin = coin
                break

            if not selected_coin:
                logger.warning("No eligible tokens found for fundamentals tweet")
                # Reset the tweeted tokens to allow tweeting about them again
                self.tweeted_tokens = {}
                selected_coin = coins_to_check[0] if coins_to_check else "BTC"

            # Get token fundamentals
            fundamentals = self.coingecko_client.get_token_fundamentals(selected_coin)

            if not fundamentals:
                logger.warning(f"No fundamentals found for {selected_coin}")
                return {
                    "success": False,
                    "error": f"No fundamentals found for {selected_coin}",
                }

            # Update tweeted tokens
            self.tweeted_tokens[selected_coin] = datetime.now()

            # Format fundamentals
            name = fundamentals.get("name", selected_coin)
            symbol = fundamentals.get("symbol", selected_coin).upper()
            current_price = fundamentals.get("current_price")
            market_cap = fundamentals.get("market_cap")
            fully_diluted_valuation = fundamentals.get("fully_diluted_valuation")
            circulating_supply = fundamentals.get("circulating_supply")
            total_supply = fundamentals.get("total_supply")
            price_change_24h = fundamentals.get("price_change_percentage_24h")

            # Format price with appropriate precision
            if current_price:
                if current_price < 0.1:
                    price_str = f"${current_price:.4f}"
                elif current_price < 1:
                    price_str = f"${current_price:.3f}"
                elif current_price < 10:
                    price_str = f"${current_price:.2f}"
                else:
                    price_str = f"${current_price:.1f}"
            else:
                price_str = "N/A"

            # Format market cap with appropriate units
            if market_cap:
                if market_cap >= 1_000_000_000:
                    mcap_str = f"${market_cap / 1_000_000_000:.1f}B"
                elif market_cap >= 1_000_000:
                    mcap_str = f"${market_cap / 1_000_000:.1f}M"
                else:
                    mcap_str = f"${market_cap / 1_000:.1f}K"
            else:
                mcap_str = "N/A"

            # Format FDV with appropriate units
            if fully_diluted_valuation:
                if fully_diluted_valuation >= 1_000_000_000:
                    fdv_str = f"${fully_diluted_valuation / 1_000_000_000:.1f}B"
                elif fully_diluted_valuation >= 1_000_000:
                    fdv_str = f"${fully_diluted_valuation / 1_000_000:.1f}M"
                else:
                    fdv_str = f"${fully_diluted_valuation / 1_000:.1f}K"
            else:
                fdv_str = "N/A"

            # Format circulating supply with appropriate units
            if circulating_supply:
                if circulating_supply >= 1_000_000_000:
                    circ_str = f"{circulating_supply / 1_000_000_000:.1f}B"
                elif circulating_supply >= 1_000_000:
                    circ_str = f"{circulating_supply / 1_000_000:.1f}M"
                else:
                    circ_str = f"{circulating_supply / 1_000:.1f}K"
            else:
                circ_str = "N/A"

            # Format price change
            if price_change_24h:
                if price_change_24h > 0:
                    price_change_str = f"+{price_change_24h:.1f}%"
                else:
                    price_change_str = f"{price_change_24h:.1f}%"
            else:
                price_change_str = "N/A"

            # Generate tweet text
            tweet_templates = [
                f"💡 ${symbol} Token Fundamentals 💡\n\nPrice: {price_str} ({price_change_str} 24h)\nMarket Cap: {mcap_str}\nFully Diluted Value: {fdv_str}\nCirculating Supply: {circ_str}\n\nTrading on @HyperliquidExch! #HyperLiquid #{symbol}",
                f"📊 Quick look at ${symbol} ({name}) 📊\n\nCurrent Price: {price_str}\n24h Change: {price_change_str}\nMarket Cap: {mcap_str}\nFDV: {fdv_str}\nCirc Supply: {circ_str}\n\n#HyperLiquid #{symbol}",
                f"👀 ${symbol} Snapshot 👀\n\nPrice: {price_str}\nDaily Change: {price_change_str}\nMCap: {mcap_str}\nFDV: {fdv_str}\nCirculating: {circ_str}\n\nTrade on @HyperliquidExch! #HyperLiquid",
                f"🔍 ${symbol} Fundamentals 🔍\n\nTrading at: {price_str} ({price_change_str} 24h)\nMarket Cap: {mcap_str}\nFully Diluted: {fdv_str}\nCirc Supply: {circ_str}\n\n#HyperLiquid #{symbol}",
            ]

            tweet_text = random.choice(tweet_templates)

            return {
                "success": True,
                "action": "tweet",
                "tweet_text": tweet_text,
                "token_symbol": symbol,
                "token_name": name,
                "source": "token_fundamentals",
            }

        except Exception as e:
            logger.error(
                f"Failed to generate token fundamentals tweet: {str(e)}", exc_info=True
            )
            return {"success": False, "error": str(e)}
