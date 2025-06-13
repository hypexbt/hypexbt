"""
FastAPI server for the hypexbt Twitter bot.

This module provides the REST API endpoints for external webhooks,
monitoring, and queue management.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.utils.config import Config

logger = logging.getLogger(__name__)


# Simple Pydantic models for API requests/responses
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    version: str


class TweetRequest(BaseModel):
    content: str
    priority: int = 3  # Default to normal priority
    tweet_type: str = "manual"


class TweetResponse(BaseModel):
    status: str
    message: str
    tweet_id: str | None = None


class EchoResponse(BaseModel):
    echo: str
    timestamp: str
    length: int


def create_app(config: Config) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="hypexbt Twitter Bot API",
        description="REST API for the hypexbt Twitter bot monitoring and management",
        version="1.0.0",
    )

    @app.get("/", response_model=Dict[str, Any])
    async def root() -> Dict[str, Any]:
        """Root endpoint - welcome message."""
        return {
            "message": "hypexbt Twitter Bot API is running 🚀",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """Health check endpoint for monitoring."""
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            service="hypexbt-twitter-bot",
            version="1.0.0",
        )

    @app.get("/api/echo/{message}", response_model=EchoResponse)
    async def echo(message: str) -> EchoResponse:
        """Echo endpoint for testing."""
        return EchoResponse(
            echo=message,
            timestamp=datetime.utcnow().isoformat(),
            length=len(message),
        )

    @app.post("/api/tweet", response_model=TweetResponse)
    async def trigger_tweet(request: TweetRequest) -> TweetResponse:
        """
        Trigger a tweet to be added to the queue.
        
        This endpoint will eventually add tweets to the Redis queue,
        but for now it just returns a success response.
        """
        logger.info(f"Tweet request received: {request.content[:50]}...")
        
        # TODO: Add to Redis queue
        # For now, just return success
        return TweetResponse(
            status="queued",
            message=f"Tweet queued successfully with priority {request.priority}",
            tweet_id=None,  # Will be set when actually posted
        )

    @app.get("/api/status", response_model=Dict[str, Any])
    async def status() -> Dict[str, Any]:
        """Detailed status endpoint."""
        return {
            "service": "hypexbt-twitter-bot",
            "status": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "config_loaded": True,
            "redis_connected": False,  # TODO: Check Redis connection
            "components": {
                "api_server": "running",
                "scheduler": "not_implemented",
                "queue_worker": "not_implemented",
            },
            "endpoints": {
                "root": "/",
                "health": "/health",
                "echo": "/api/echo/{message}",
                "tweet": "/api/tweet",
                "status": "/api/status",
                "docs": "/docs",
            },
        }

    return app 