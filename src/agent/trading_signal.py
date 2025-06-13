"""
Trading signal tweet generator for the hypexbt Twitter bot.

This module generates tweets about trading signals and technical analysis.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Any

from src.sources.hyperliquid_client import HyperliquidClient

logger = logging.getLogger(__name__)


class TradingSignalTweetGenerator:
    """
    Generator for trading signal tweets.
    """

    def __init__(self, hyperliquid_client: HyperliquidClient):
        """
        Initialize the trading signal tweet generator.

        Args:
            hyperliquid_client: The Hyperliquid client.
        """
        self.hyperliquid_client = hyperliquid_client

        # Keep track of tweeted signals to avoid duplicates
        self.tweeted_signals = {}

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

    def generate_tweet(self) -> dict[str, Any]:
        """
        Generate a tweet about a trading signal.

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

            # Find a coin with a signal change
            signal_found = False
            selected_signal = None

            for coin in coins_to_check:
                # Check if we've already tweeted about this coin recently
                if (
                    coin in self.tweeted_signals
                    and datetime.now() - self.tweeted_signals[coin]
                    < timedelta(hours=12)
                ):
                    continue

                # Calculate momentum signals
                signals = self.hyperliquid_client.calculate_momentum_signals(coin)

                # Check if there's a signal change
                if signals.get("15m_signal_change") or signals.get("1h_signal_change"):
                    signal_found = True
                    selected_signal = signals

                    # Update tweeted signals
                    self.tweeted_signals[coin] = datetime.now()
                    break

            if not signal_found:
                logger.warning("No new trading signals found")
                return {"success": False, "error": "No new trading signals found"}

            # Generate tweet text based on the signal
            coin = selected_signal.get("coin")
            price = selected_signal.get("price")
            signal_15m = selected_signal.get("15m_signal")
            signal_1h = selected_signal.get("1h_signal")

            # Determine signal type
            if signal_15m == 1 and signal_1h == 1:
                signal_type = "strong_bullish"
            elif signal_15m == 1 and signal_1h == -1:
                signal_type = "mixed_short_term_bullish"
            elif signal_15m == -1 and signal_1h == 1:
                signal_type = "mixed_long_term_bullish"
            elif signal_15m == -1 and signal_1h == -1:
                signal_type = "strong_bearish"
            else:
                signal_type = "neutral"

            # Format price with appropriate precision
            if price < 0.1:
                price_str = f"${price:.4f}"
            elif price < 1:
                price_str = f"${price:.3f}"
            elif price < 10:
                price_str = f"${price:.2f}"
            else:
                price_str = f"${price:.1f}"

            # Generate tweet text based on signal type
            if signal_type == "strong_bullish":
                tweet_texts = [
                    f"📈 SIGNAL ALERT: $HL-{coin} showing strong bullish momentum! Both 15m and 1h EMAs crossed bullish at {price_str}. Potential long opportunity? #HyperLiquid #TradingSignal",
                    f"🚀 $HL-{coin} momentum turning bullish! 15m and 1h indicators both positive at {price_str}. Keep an eye on this one, anon! #HyperLiquid #TradingSignal",
                    f"💚 Double bullish signal on $HL-{coin}! Short and long timeframes aligned at {price_str}. Trend reversal in progress? #HyperLiquid #TradingSignal",
                ]
            elif signal_type == "mixed_short_term_bullish":
                tweet_texts = [
                    f"📊 SIGNAL UPDATE: $HL-{coin} showing short-term bullish momentum at {price_str}. 15m EMA crossed up but 1h still bearish. Scalp opportunity? #HyperLiquid #TradingSignal",
                    f"⚠️ Mixed signals on $HL-{coin} at {price_str} - bullish on 15m timeframe but bearish on 1h. Short-term traders might find opportunities here. #HyperLiquid #TradingSignal",
                    f"🔍 $HL-{coin} short-term momentum shift at {price_str}! 15m indicators turned bullish while 1h remains bearish. Watch for confirmation. #HyperLiquid #TradingSignal",
                ]
            elif signal_type == "mixed_long_term_bullish":
                tweet_texts = [
                    f"📊 SIGNAL UPDATE: $HL-{coin} showing long-term bullish momentum at {price_str}. 1h EMA crossed up but 15m still bearish. Swing trade setup? #HyperLiquid #TradingSignal",
                    f"⚠️ Mixed signals on $HL-{coin} at {price_str} - bearish on 15m timeframe but bullish on 1h. Longer-term traders might find value here. #HyperLiquid #TradingSignal",
                    f"🔍 $HL-{coin} long-term momentum shift at {price_str}! 1h indicators turned bullish while 15m remains bearish. Patience might pay off. #HyperLiquid #TradingSignal",
                ]
            elif signal_type == "strong_bearish":
                tweet_texts = [
                    f"📉 SIGNAL ALERT: $HL-{coin} showing strong bearish momentum! Both 15m and 1h EMAs crossed bearish at {price_str}. Potential short opportunity? #HyperLiquid #TradingSignal",
                    f"🔴 $HL-{coin} momentum turning bearish! 15m and 1h indicators both negative at {price_str}. Caution advised for longs. #HyperLiquid #TradingSignal",
                    f"⚠️ Double bearish signal on $HL-{coin}! Short and long timeframes aligned at {price_str}. Trend reversal in progress? #HyperLiquid #TradingSignal",
                ]
            else:
                tweet_texts = [
                    f"📊 SIGNAL UPDATE: $HL-{coin} showing neutral momentum at {price_str}. Mixed signals across timeframes. Wait for clearer direction? #HyperLiquid #TradingSignal",
                    f"⚖️ $HL-{coin} at {price_str} with conflicting momentum indicators. No clear trend direction at the moment. #HyperLiquid #TradingSignal",
                    f"🔍 Monitoring $HL-{coin} at {price_str} - momentum indicators showing indecision. Wait for confirmation before entry. #HyperLiquid #TradingSignal",
                ]

            tweet_text = random.choice(tweet_texts)

            # Add disclaimer
            tweet_text += "\n\n⚠️ Not financial advice. DYOR."

            return {
                "success": True,
                "action": "tweet",
                "tweet_text": tweet_text,
                "coin": coin,
                "price": price,
                "signal_type": signal_type,
                "source": "trading_signal",
            }

        except Exception as e:
            logger.error(
                f"Failed to generate trading signal tweet: {e!s}", exc_info=True
            )
            return {"success": False, "error": str(e)}
