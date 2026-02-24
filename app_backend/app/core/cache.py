# app/core/cache.py
"""Cache management module."""
import logging
from typing import Any, Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis connection pool
redis_pool = None
redis_client = None


def get_redis() -> Optional[redis.Redis]:
    """Get Redis connection."""
    global redis_pool, redis_client

    if not settings.REDIS_HOST:
        return None

    if redis_pool is None:
        try:
            redis_pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                max_connections=20,
            )
            redis_client = redis.Redis(connection_pool=redis_pool)
            # Test connection
            redis_client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            redis_client = None

    return redis_client


def init_redis():
    """Initialize Redis connection."""
    client = get_redis()
    if client:
        logger.info("Redis initialized")
    else:
        logger.warning("Redis not available - cache disabled")
    return client


def close_redis():
    """Close Redis connection."""
    global redis_pool, redis_client
    if redis_pool:
        redis_pool.disconnect()
        redis_pool = None
        redis_client = None
        logger.info("Redis connection closed")


async def get_cache(key: str) -> Optional[Any]:
    """Get value from cache."""
    try:
        client = get_redis()
        if client:
            return client.get(key)
    except Exception:
        pass
    return None


async def set_cache(key: str, value: Any, expire: int = 3600) -> bool:
    """Set value in cache."""
    try:
        client = get_redis()
        if client:
            client.setex(key, expire, value)
            return True
    except Exception:
        pass
    return False


async def delete_cache(key: str) -> bool:
    """Delete value from cache."""
    try:
        client = get_redis()
        if client:
            client.delete(key)
            return True
    except Exception:
        pass
    return False


async def clear_cache_pattern(pattern: str) -> int:
    """Clear cache entries matching pattern."""
    try:
        client = get_redis()
        if client:
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
    except Exception:
        pass
    return 0


async def clear_all_cache() -> bool:
    """Clear all cache."""
    try:
        client = get_redis()
        if client:
            client.flushdb()
            return True
    except Exception:
        pass
    return False


class RedisCache:
    """Redis cache wrapper class."""

    def __init__(self):
        self.client = None

    def connect(self):
        try:
            self.client = get_redis()
            return self.client is not None
        except:
            return False


# Create cache instance
cache = RedisCache()

__all__ = [
    "get_redis",
    "init_redis",
    "close_redis",
    "get_cache",
    "set_cache",
    "delete_cache",
    "clear_cache_pattern",
    "clear_all_cache",
    "cache",
    "redis_client",
]
