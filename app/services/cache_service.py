#!/usr/bin/env python3
"""
SmartCloudOps AI - Cache Service
================================

Caching service with Redis support and in-memory fallback.
"""




import logging
import time
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..utils.exceptions import ServiceUnavailableError
from .base_service import BaseService

logger = logging.getLogger(__name__)


class CacheService(BaseService):
    """Service for caching data with Redis support and in-memory fallback."""

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.redis_client = None
        self.memory_cache = {}
        self.use_redis = self.get_config("use_redis", True)
        self.redis_url = self.get_config("redis_url", "redis://localhost:6379")
        self.default_ttl = self.get_config("default_ttl", 3600)  # 1 hour
        self.max_memory_size = self.get_config("max_memory_size", 1000)  # Max items in memory cache

    def _initialize_service(self) -> None:
        """Initialize the cache service."""
        if self.use_redis:
            try:
                import redis

                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed, falling back to memory cache: {e}")
                self.use_redis = False
                self.redis_client = None

        if not self.use_redis:
            logger.info("Using in-memory cache")
            self._cleanup_memory_cache()

    def _cleanup_memory_cache(self) -> None:
        """Clean up expired items from memory cache."""
        current_time = time.time()
        expired_keys = []

        for key, (value, expiry) in self.memory_cache.items():
            if expiry and current_time > expiry:
                expired_keys.append(key)

        for key in expired_keys:
            del self.memory_cache[key]

        # If cache is too large, remove oldest items
        if len(self.memory_cache) > self.max_memory_size:
            sorted_items = sorted(self.memory_cache.items(), key=lambda x: x[1][1] or 0)
            items_to_remove = len(sorted_items) - self.max_memory_size
            for i in range(items_to_remove):
                del self.memory_cache[sorted_items[i][0]]

    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage."""
        if isinstance(value, (dict, list, str, int, float, bool)):
            return json.dumps(value)
        return str(value)

    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from storage."""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            if self.use_redis and self.redis_client:
                value = self.redis_client.get(key)
                if value is not None:
                    return self._deserialize_value(value)
            else:
                self._cleanup_memory_cache()
                if key in self.memory_cache:
                    value, expiry = self.memory_cache[key]
                    if not expiry or time.time() <= expiry:
                        return value
                    else:
                        del self.memory_cache[key]

            return default
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            serialized_value = self._serialize_value(value)
            ttl = ttl or self.default_ttl

            if self.use_redis and self.redis_client:
                return self.redis_client.setex(key, ttl, serialized_value)
            else:
                self._cleanup_memory_cache()
                expiry = time.time() + ttl if ttl > 0 else None
                self.memory_cache[key] = (value, expiry)
                return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            if self.use_redis and self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                self._cleanup_memory_cache()
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if self.use_redis and self.redis_client:
                return bool(self.redis_client.exists(key))
            else:
                self._cleanup_memory_cache()
                if key in self.memory_cache:
                    value, expiry = self.memory_cache[key]
                    if not expiry or time.time() <= expiry:
                        return True
                    else:
                        del self.memory_cache[key]
                return False
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False

    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for existing key."""
        try:
            if self.use_redis and self.redis_client:
                return bool(self.redis_client.expire(key, ttl))
            else:
                self._cleanup_memory_cache()
                if key in self.memory_cache:
                    value, _ = self.memory_cache[key]
                    expiry = time.time() + ttl if ttl > 0 else None
                    self.memory_cache[key] = (value, expiry)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error setting expiration for cache key {key}: {e}")
            return False

    def ttl(self, key: str) -> int:
        """Get remaining TTL for key."""
        try:
            if self.use_redis and self.redis_client:
                return self.redis_client.ttl(key)
            else:
                self._cleanup_memory_cache()
                if key in self.memory_cache:
                    value, expiry = self.memory_cache[key]
                    if expiry:
                        remaining = int(expiry - time.time())
                        return max(0, remaining)
                return -1
        except Exception as e:
            logger.error(f"Error getting TTL for cache key {key}: {e}")
            return -1

    def clear(self) -> bool:
        """Clear all cache."""
        try:
            if self.use_redis and self.redis_client:
                return bool(self.redis_client.flushdb())
            else:
                self.memory_cache.clear()
                return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        try:
            if self.use_redis and self.redis_client:
                return self.redis_client.keys(pattern)
            else:
                self._cleanup_memory_cache()
                import fnmatch

                return [key for key in self.memory_cache.keys() if fnmatch.fnmatch(key, pattern)]
        except Exception as e:
            logger.error(f"Error getting cache keys: {e}")
            return []

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value."""
        try:
            if self.use_redis and self.redis_client:
                return self.redis_client.incr(key, amount)
            else:
                current_value = self.get(key, 0)
                if isinstance(current_value, (int, float)):
                    new_value = current_value + amount
                    self.set(key, new_value)
                    return new_value
                return 0
        except Exception as e:
            logger.error(f"Error incrementing cache key {key}: {e}")
            return 0

    def get_or_set(self, key: str, default_func, ttl: Optional[int] = None) -> Any:
        """Get value from cache or set default if not exists."""
        value = self.get(key)
        if value is None:
            value = default_func()
            self.set(key, value, ttl)
        return value

    def cache_function(self, ttl: Optional[int] = None, key_prefix: str = ""):
        """Decorator to cache function results."""

        def decorator(func):
            def wrapper(*args, **kwargs):
                # Create cache key from function name and arguments
                cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

                # Try to get from cache
                result = self.get(cache_key)
                if result is not None:
                    return result

                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result

            return wrapper

        return decorator

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            if self.use_redis and self.redis_client:
                info = self.redis_client.info()
                return {
                    "type": "redis",
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                }
            else:
                self._cleanup_memory_cache()
                return {
                    "type": "memory",
                    "total_keys": len(self.memory_cache),
                    "max_size": self.max_memory_size,
                    "usage_percent": (len(self.memory_cache) / self.max_memory_size) * 100,
                }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"type": "unknown", "error": str(e)}
