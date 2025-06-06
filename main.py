#!/usr/bin/env python3
"""
hypexbt Twitter Bot

A Twitter bot that tweets about Hyperliquid news, token launches, trading signals,
daily stats, and token fundamentals.
"""
import os
import sys
import logging
import argparse
import asyncio
from pathlib import Path

from bot.utils.config import Config
from bot.utils.logging_setup import setup_logging
from bot.scheduler import TweetScheduler

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="hypexbt Twitter Bot")
    parser.add_argument("--env-file", type=str, help="Path to .env file")
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    parser.add_argument("--log-file", type=str, help="Path to log file")
    parser.add_argument(
        "--mode",
        type=str,
        default="scheduler",
        choices=["scheduler", "websocket"],
        help="Bot mode",
    )

    return parser.parse_args()


async def run_websocket_mode(config):
    """Run the bot in WebSocket mode."""
    logger.info("Starting bot in WebSocket mode")

    # Initialize scheduler
    scheduler = TweetScheduler(config)

    # Start WebSocket streaming
    await scheduler.start_websocket_streaming()


def run_scheduler_mode(config):
    """Run the bot in scheduler mode."""
    logger.info("Starting bot in scheduler mode")

    # Initialize scheduler
    scheduler = TweetScheduler(config)

    # Start scheduler
    scheduler.start()

    try:
        # Keep the main thread alive
        while True:
            import time

            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping bot")
        scheduler.stop()


async def main():
    """Main entry point."""
    # Parse arguments
    args = parse_args()

    # Setup logging
    setup_logging(args.log_level, args.log_file)

    # Load configuration
    config = Config(args.env_file)

    # Run in specified mode
    if args.mode == "websocket":
        await run_websocket_mode(config)
    else:
        run_scheduler_mode(config)


if __name__ == "__main__":
    # Run the main function
    if sys.version_info >= (3, 7):
        asyncio.run(main())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
