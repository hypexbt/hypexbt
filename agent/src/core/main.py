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

from src.utils.config import Config
from src.utils.logging_setup import setup_logging
from src.core.scheduler import TweetScheduler

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
        choices=["scheduler", "websocket", "api"],
        help="Bot mode",
    )
    parser.add_argument("--host", type=str, default="0.0.0.0", help="API host (for api mode)")
    parser.add_argument("--port", type=int, default=8000, help="API port (for api mode)")

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


def run_api_mode(host: str, port: int):
    """Run the bot in API mode."""
    logger.info(f"Starting API server on {host}:{port}")
    
    try:
        import uvicorn
        from src.api.main import app
        
        uvicorn.run(app, host=host, port=port)
    except ImportError:
        logger.error("FastAPI/uvicorn not installed. Install with: pip install fastapi uvicorn")
        sys.exit(1)


async def main():
    """Main entry point."""
    # Parse arguments
    args = parse_args()

    # Setup logging
    setup_logging(args.log_level, args.log_file)

    # Load configuration (not needed for API mode)
    if args.mode != "api":
        config = Config(args.env_file)

    # Run in specified mode
    if args.mode == "websocket":
        await run_websocket_mode(config)
    elif args.mode == "api":
        run_api_mode(args.host, args.port)
    else:
        run_scheduler_mode(config)


if __name__ == "__main__":
    # Run the main function
    if sys.version_info >= (3, 7):
        asyncio.run(main())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
