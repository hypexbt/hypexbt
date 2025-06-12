"""
FastAPI server for the hypexbt Twitter bot.

This module provides a simple REST API for monitoring and health checks.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.utils.config import Config

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="hypexbt Twitter Bot API",
    description="REST API for the hypexbt Twitter bot monitoring and management",
    version="1.0.0"
)

# Global config (will be set on startup)
config = None

@app.on_event("startup")
async def startup_event():
    """Initialize the API on startup."""
    global config
    config = Config()
    logger.info("FastAPI server started")

@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint - hello world.
    
    Returns:
        A welcome message.
    """
    return {
        "message": "Hello World! hypexbt Twitter Bot API is running 🚀",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/echo/{message}")
async def echo(message: str) -> Dict[str, Any]:
    """
    Echo endpoint - returns the message back.
    
    Args:
        message: The message to echo back.
        
    Returns:
        The echoed message with metadata.
    """
    return {
        "echo": message,
        "timestamp": datetime.utcnow().isoformat(),
        "length": len(message)
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Health status of the bot.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "hypexbt-twitter-bot",
        "uptime": "running"
    }

@app.get("/status")
async def status() -> Dict[str, Any]:
    """
    Status endpoint with more detailed information.
    
    Returns:
        Detailed status of the bot.
    """
    return {
        "service": "hypexbt-twitter-bot",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "config_loaded": config is not None,
        "endpoints": {
            "root": "/",
            "echo": "/echo/{message}",
            "health": "/health",
            "status": "/status",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 