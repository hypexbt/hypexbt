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
from src.queue.service import QueueService
from src.queue.jobs.tweet_job import TweetJob

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
    job_id: str | None = None


class EchoResponse(BaseModel):
    echo: str
    timestamp: str
    length: int


class QueueStatsResponse(BaseModel):
    total_jobs: int
    queues: Dict[str, int]
    total_processed: str


def create_app(config: Config) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="hypexbt Twitter Bot API",
        description="REST API for the hypexbt Twitter bot monitoring and management",
        version="1.0.0",
    )

    queue_service = QueueService(config.redis_url)

    # Store services in app state for access by other components
    app.state.queue_service = queue_service
    app.state.config = config

    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup."""
        try:
            await queue_service.connect()
            logger.info("FastAPI server started with Redis queue service")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis during startup: {e}")
            logger.info("FastAPI server started without Redis connection")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        await queue_service.disconnect()
        logger.info("FastAPI server shutdown complete")

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
        # Try to check Redis connection but don't fail if it's down
        redis_status = "unknown"
        try:
            await queue_service.get_queue_stats()
            redis_status = "connected"
        except Exception:
            redis_status = "disconnected"

        return HealthResponse(
            status="healthy",  # Server is healthy even if Redis is down
            timestamp=datetime.utcnow().isoformat(),
            service=f"hypexbt-twitter-bot (redis: {redis_status})",
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
        Trigger a tweet to be added to the Redis queue.
        """
        try:
            job_id = await TweetJob.add_to_queue(
                queue_service, content=request.content, priority=request.priority
            )

            logger.info(f"Tweet job {job_id} queued: {request.content[:50]}...")

            return TweetResponse(
                status="queued",
                message=f"Tweet queued successfully with priority {request.priority}",
                tweet_id=None,
                job_id=job_id,
            )
        except Exception as e:
            logger.error(f"Failed to queue tweet: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to queue tweet: {str(e)}"
            )

    @app.get("/api/queue/stats", response_model=QueueStatsResponse)
    async def queue_stats() -> QueueStatsResponse:
        """Get Redis queue statistics."""
        try:
            stats = await queue_service.get_queue_stats()
            return QueueStatsResponse(**stats)
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get queue stats: {str(e)}"
            )

    @app.get("/api/queue/peek/{priority}")
    async def peek_queue(priority: int, count: int = 5) -> Dict[str, Any]:
        """Peek at jobs in a specific priority queue."""
        try:
            jobs = await queue_service.peek_queue(priority, count)
            return {
                "queue": f"jobs_priority_{priority}",
                "count": len(jobs),
                "jobs": jobs,
            }
        except Exception as e:
            logger.error(f"Failed to peek queue: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to peek queue: {str(e)}"
            )

    @app.delete("/api/queue/clear")
    async def clear_queue(priority: int | None = None) -> Dict[str, Any]:
        """Clear jobs from queue(s)."""
        try:
            cleared = await queue_service.clear_queue(priority)
            return {
                "status": "success",
                "cleared_jobs": cleared,
                "message": f"Cleared {cleared} jobs from {'all queues' if priority is None else f'priority {priority} queue'}",
            }
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to clear queue: {str(e)}"
            )

    @app.get("/api/status", response_model=Dict[str, Any])
    async def status() -> Dict[str, Any]:
        """Detailed status endpoint."""
        try:
            # Check Redis connection
            redis_connected = True
            queue_stats = await queue_service.get_queue_stats()
        except Exception:
            redis_connected = False
            queue_stats = {"error": "Redis not connected"}

        return {
            "service": "hypexbt-twitter-bot",
            "status": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "config_loaded": True,
            "redis_connected": redis_connected,
            "queue_stats": queue_stats,
            "components": {
                "api_server": "running",
                "redis_queue": "connected" if redis_connected else "disconnected",
                "scheduler": "not_implemented",
                "queue_worker": "not_implemented",
            },
            "endpoints": {
                "root": "/",
                "health": "/health",
                "echo": "/api/echo/{message}",
                "tweet": "/api/tweet",
                "queue_stats": "/api/queue/stats",
                "queue_peek": "/api/queue/peek/{priority}",
                "queue_clear": "/api/queue/clear",
                "status": "/api/status",
                "docs": "/docs",
            },
        }

    return app
