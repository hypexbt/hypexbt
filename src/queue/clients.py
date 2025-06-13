"""
Client container for job dependencies.
"""

from typing import Any

from src.messaging.twitter_client import TwitterClient


class ClientContainer:
    """Container for all client dependencies used by jobs."""
    
    def __init__(self, config: Any) -> None:
        self.config = config
        self._twitter_client = None
    
    @property
    def twitter(self) -> TwitterClient:
        """Get Twitter client (lazy initialization)."""
        if self._twitter_client is None:
            self._twitter_client = TwitterClient(self.config)
        return self._twitter_client 