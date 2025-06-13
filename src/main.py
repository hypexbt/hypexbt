#!/usr/bin/env python3
"""
Main entry point for the hypexbt Twitter bot.

This module provides a single-container application that runs:
- FastAPI server for external webhooks
- APScheduler for background jobs
- Redis queue worker for tweet processing
- All data source integrations
"""

import argparse
import asyncio
import logging
import sys
from typing import Any

from src.utils.config import Config
from src.utils.logging_setup import setup_logging


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="hypexbt Twitter Bot - Single Container Architecture"
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the logging level",
    )
    
    parser.add_argument(
        "--log-file",
        help="Log file path (optional)",
    )
    
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Environment file path",
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="API server host",
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server port",
    )
    
    return parser.parse_args()


async def run_application(config: Config, host: str, port: int) -> None:
    """Run the complete application with all components."""
    logger = logging.getLogger(__name__)
    logger.info("Starting hypexbt Twitter Bot application")
    
    try:
        # Import components (lazy import to avoid circular dependencies)
        from src.api.server import create_app
        from src.agent.scheduler import TweetScheduler
        from src.queue.worker import Worker
        
        # Initialize components
        logger.info("Initializing components...")
        
        # Create FastAPI app
        app = create_app(config)
        
        # Initialize scheduler and worker
        scheduler = TweetScheduler(config)
        worker = Worker(config)
        
        # Start background components
        logger.info("Starting background components...")
        await scheduler.start()
        await worker.start()
        
        # Start API server
        logger.info(f"Starting API server on {host}:{port}")
        import uvicorn
        
        # Run uvicorn in a way that allows graceful shutdown
        server_config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level=config.log_level.lower(),
        )
        server = uvicorn.Server(server_config)
        
        # This will run until interrupted
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        raise
    finally:
        # Cleanup
        logger.info("Shutting down components...")
        if 'scheduler' in locals():
            await scheduler.shutdown()
        if 'worker' in locals():
            await worker.shutdown()
        logger.info("Application shutdown complete")


async def main() -> None:
    """Main entry point."""
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    # Load configuration
    try:
        config = Config(args.env_file)
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Run the application
    try:
        await run_application(config, args.host, args.port)
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 