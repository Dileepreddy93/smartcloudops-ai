#!/usr/bin/env python3
"""
SmartCloudOps AI - Cache Service
===============================

Comprehensive caching service with Redis and memory fallback.
Enhanced for production use with unified configuration.
"""


import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class CacheService:
    """Comprehensive caching service with Redis and memory fallback."""

    def __init__(self, redis_url: Optional[str] = None, max_connections: int = 10):
        """Initialize cache service."""
        self.redis_client = None
        self.memory_cache = {}
        self.cache_stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}
        self.max_connections = max_connections

        # Try to connect to Redis
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    max_connections=max_connections,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    decode_responses=True,
                )
                # Test connection
                self.redis_client.ping()
                logger.info("✅ Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using memory cache.")
                self.redis_client = None

        if not self.redis_client:
            logger.info("Using in-memory cache")

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments."""
        # Create a hash of the arguments
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"smartcloudops:{prefix}:{key_hash}"

    def _serialize_value(self, value: Any) -> str:
        """Serialize value for caching."""
        if isinstance(value, (dict, list, str, int, float, bool)):
            return json.dumps(value, default=str)
        else:
            return str(value)

    def _deserialize_value(self, value: str) -> Any:
        """Deserialize cached value."""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            if self.redis_client:
                # Try Redis first
                value = self.redis_client.get(key)
                if value is not None:
                    self.cache_stats["hits"] += 1
                    return self._deserialize_value(value)

            # Fall back to memory cache
            if key in self.memory_cache:
                item = self.memory_cache[key]
                if item["expires_at"] > time.time():
                    self.cache_stats["hits"] += 1
                    return item["value"]
                else:
                    # Expired, remove it
                    del self.memory_cache[key]

            self.cache_stats["misses"] += 1
            return default

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return default

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL."""
        try:
            serialized_value = self._serialize_value(value)

            if self.redis_client:
                # Try Redis first
                success = self.redis_client.setex(key, ttl, serialized_value)
                if success:
                    self.cache_stats["sets"] += 1
                    return True

            # Fall back to memory cache
            self.memory_cache[key] = {"value": value, "expires_at": time.time() + ttl}
            self.cache_stats["sets"] += 1
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            if self.redis_client:
                # Try Redis first
                result = self.redis_client.delete(key)
                if result > 0:
                    self.cache_stats["deletes"] += 1
                    return True

            # Fall back to memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
                self.cache_stats["deletes"] += 1
                return True

            return False

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if self.redis_client:
                return bool(self.redis_client.exists(key))

            # Fall back to memory cache
            if key in self.memory_cache:
                item = self.memory_cache[key]
                if item["expires_at"] > time.time():
                    return True
                else:
                    # Expired, remove it
                    del self.memory_cache[key]

            return False

        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False

    def clear(self, pattern: str = "smartcloudops:*") -> int:
        """Clear cache entries matching pattern."""
        try:
            deleted_count = 0

            if self.redis_client:
                # Clear Redis cache
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted_count = self.redis_client.delete(*keys)

            # Clear memory cache
            memory_keys = [k for k in self.memory_cache.keys() if k.startswith(pattern.replace("*", ""))]
            for key in memory_keys:
                del self.memory_cache[key]
                deleted_count += 1

            return deleted_count

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "sets": self.cache_stats["sets"],
            "deletes": self.cache_stats["deletes"],
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "memory_cache_size": len(self.memory_cache),
            "redis_available": self.redis_client is not None,
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on cache service."""
        try:
            if self.redis_client:
                # Test Redis connection
                self.redis_client.ping()
                redis_status = "healthy"
            else:
                redis_status = "unavailable"

            # Test memory cache
            test_key = "health_check_test"
            test_value = {"timestamp": datetime.now(timezone.utc).isoformat()}

            # Test set and get
            set_success = self.set(test_key, test_value, ttl=10)
            retrieved_value = self.get(test_key)
            get_success = retrieved_value == test_value

            # Clean up
            self.delete(test_key)

            return {
                "status": "healthy" if set_success and get_success else "unhealthy",
                "redis": redis_status,
                "memory_cache": "healthy" if set_success and get_success else "unhealthy",
                "test_passed": set_success and get_success,
                "stats": self.get_stats(),
            }

        except Exception as e:
            logger.error(f"Cache health check error: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "redis": "unavailable",
                "memory_cache": "unavailable",
                "test_passed": False,
            }

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        try:
            if self.redis_client:
                # Get Redis memory info
                info = self.redis_client.info("memory")
                return {
                    "redis_used_memory": info.get("used_memory_human", "unknown"),
                    "redis_used_memory_peak": info.get("used_memory_peak_human", "unknown"),
                    "redis_used_memory_rss": info.get("used_memory_rss_human", "unknown"),
                }
            else:
                # Estimate memory cache usage
                memory_size = sum(len(str(v)) for v in self.memory_cache.values())
                return {
                    "memory_cache_entries": len(self.memory_cache),
                    "memory_cache_size_bytes": memory_size,
                    "memory_cache_size_human": f"{memory_size / 1024:.2f} KB",
                }
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {"error": str(e)}


# Global cache service instance
cache_service = CacheService()


def cached(prefix: str, ttl: int = 300):
    """Decorator for caching function results."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_service._generate_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {cache_key}, cached result")

            return result

        return wrapper

    return decorator


def cache_invalidate(prefix: str):
    """Decorator for invalidating cache after function execution."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function
            result = func(*args, **kwargs)

            # Invalidate cache
            pattern = f"smartcloudops:{prefix}:*"
            deleted_count = cache_service.clear(pattern)
            logger.debug(f"Invalidated {deleted_count} cache entries for pattern {pattern}")

            return result

        return wrapper

    return decorator


# Cache configurations for different data types
CACHE_CONFIGS = {
    "health_check": {"ttl": 60},  # 1 minute
    "metrics": {"ttl": 30},  # 30 seconds
    "ml_prediction": {"ttl": 300},  # 5 minutes
    "user_data": {"ttl": 1800},  # 30 minutes
    "api_keys": {"ttl": 3600},  # 1 hour
    "system_config": {"ttl": 7200},  # 2 hours
}


def get_cache_service() -> CacheService:
    """Get cache service instance."""
    return cache_service


def is_cache_available() -> bool:
    """Check if cache is available."""
    return cache_service.redis_client is not None or len(cache_service.memory_cache) >= 0


# Export functions for easy import
__all__ = [
    "CacheService",
    "cache_service",
    "get_cache_service",
    "is_cache_available",
    "cached",
    "cache_invalidate",
    "CACHE_CONFIGS",
]
