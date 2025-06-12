#!/usr/bin/env python3
"""
Standalone FastAPI server for testing the echo functionality.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="hypexbt Echo API",
    description="Simple echo server for testing",
    version="1.0.0"
)

@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint - hello world.
    
    Returns:
        A welcome message.
    """
    return {
        "message": "Hello World! hypexbt Echo API is running 🚀",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/echo/{message}")
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
        Health status of the service.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "hypexbt-echo-api"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 