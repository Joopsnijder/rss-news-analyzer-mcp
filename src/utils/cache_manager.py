"""
Generic cache management functionality.
"""

import os
import json
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class CacheManager:
    """Base class for cache management with TTL support."""

    def __init__(self, cache_file: str, ttl_hours: int = 24):
        """
        Initialize cache manager.

        Args:
            cache_file (str): Path to the cache file
            ttl_hours (int): Time-to-live in hours (default: 24)
        """
        self.cache_file = cache_file
        self.ttl_hours = ttl_hours

    def _get_cache_file_path(self) -> str:
        """Return the path to the cache file."""
        if os.path.isabs(self.cache_file):
            return self.cache_file
        return os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            self.cache_file,
        )

    def _is_cache_valid(self, cache_data: Dict[str, Any]) -> bool:
        """Check if cache data is valid and within TTL."""
        try:
            cache_time = datetime.fromisoformat(cache_data.get("timestamp", ""))
            return datetime.now() - cache_time < timedelta(hours=self.ttl_hours)
        except (ValueError, KeyError):
            return False

    def read_cache(self) -> Optional[Dict[str, Any]]:
        """Read and return cache data if valid, otherwise return None."""
        cache_file_path = self._get_cache_file_path()
        if not os.path.exists(cache_file_path):
            return None

        try:
            with open(cache_file_path, "r") as f:
                cache_data = json.load(f)
                return cache_data if self._is_cache_valid(cache_data) else None
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Warning: Cache error: {e}", file=sys.stderr)
            return None

    def write_cache(self, data: str) -> None:
        """Write data to cache file."""
        try:
            cache_data = {"timestamp": datetime.now().isoformat(), "data": data}
            cache_file_path = self._get_cache_file_path()

            # Ensure directory exists
            os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)

            with open(cache_file_path, "w") as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"Warning: Failed to write cache: {e}", file=sys.stderr)

    def clear_cache(self) -> None:
        """Clear the cache file."""
        cache_file_path = self._get_cache_file_path()
        if os.path.exists(cache_file_path):
            try:
                os.remove(cache_file_path)
            except Exception as e:
                print(f"Warning: Failed to clear cache: {e}", file=sys.stderr)
