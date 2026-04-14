# app/utils/cache/redis_client.py
"""
Redis client wrapper for caching and session management
"""
import json
import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client wrapper with connection pooling and helper methods
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        password: Optional[str] = None,
        decode_responses: bool = True,
        max_connections: int = 50,
    ):
        """
        Initialize Redis client

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            decode_responses: Whether to decode responses to strings
            max_connections: Maximum number of connections in pool
        """
        self.host = host or settings.REDIS_HOST
        self.port = port or settings.REDIS_PORT
        self.db = db or settings.REDIS_DB
        self.password = password or settings.REDIS_PASSWORD

        # Create connection pool
        self.pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=decode_responses,
            max_connections=max_connections,
        )

        # Create Redis client
        self._client = redis.Redis(connection_pool=self.pool)
        self._connected = False

        # Test connection
        try:
            self._client.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except redis.ConnectionError as e:
            logger.warning(f"Could not connect to Redis: {str(e)}")
            self._connected = False

    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        try:
            self._client.ping()
            self._connected = True
            return True
        except:
            self._connected = False
            return False

    @contextmanager
    def pipeline(self):
        """Get a Redis pipeline for batch operations"""
        pipe = self._client.pipeline()
        try:
            yield pipe
            pipe.execute()
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            raise

    # Basic operations

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from Redis"""
        if not self._connected:
            return default

        try:
            value = self._client.get(key)
            if value is None:
                return default

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except:
                return value
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            return default

    def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set value in Redis

        Args:
            key: Key name
            value: Value to store
            ex: Expiry time in seconds
            px: Expiry time in milliseconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists

        Returns:
            bool: Success status
        """
        if not self._connected:
            return False

        try:
            # Serialize value if needed
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            return self._client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")
            return False

    def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        if not self._connected:
            return 0

        try:
            return self._client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis delete error: {str(e)}")
            return 0

    def exists(self, *keys: str) -> int:
        """Check if keys exist"""
        if not self._connected:
            return 0

        try:
            return self._client.exists(*keys)
        except Exception as e:
            logger.error(f"Redis exists error: {str(e)}")
            return 0

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiry time for a key"""
        if not self._connected:
            return False

        try:
            return self._client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis expire error: {str(e)}")
            return False

    def ttl(self, key: str) -> int:
        """Get time to live for a key"""
        if not self._connected:
            return -2

        try:
            return self._client.ttl(key)
        except Exception as e:
            logger.error(f"Redis ttl error: {str(e)}")
            return -2

    # Hash operations

    def hget(self, name: str, key: str) -> Optional[str]:
        """Get value from hash"""
        if not self._connected:
            return None

        try:
            return self._client.hget(name, key)
        except Exception as e:
            logger.error(f"Redis hget error: {str(e)}")
            return None

    def hset(self, name: str, key: str, value: Any) -> int:
        """Set value in hash"""
        if not self._connected:
            return 0

        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self._client.hset(name, key, value)
        except Exception as e:
            logger.error(f"Redis hset error: {str(e)}")
            return 0

    def hgetall(self, name: str) -> Dict[str, str]:
        """Get all values from hash"""
        if not self._connected:
            return {}

        try:
            return self._client.hgetall(name)
        except Exception as e:
            logger.error(f"Redis hgetall error: {str(e)}")
            return {}

    def hdel(self, name: str, *keys: str) -> int:
        """Delete keys from hash"""
        if not self._connected:
            return 0

        try:
            return self._client.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Redis hdel error: {str(e)}")
            return 0

    def hincrby(self, name: str, key: str, amount: int = 1) -> int:
        """Increment hash value"""
        if not self._connected:
            return 0

        try:
            return self._client.hincrby(name, key, amount)
        except Exception as e:
            logger.error(f"Redis hincrby error: {str(e)}")
            return 0

    # List operations

    def lpush(self, key: str, *values: Any) -> int:
        """Push values to the left of list"""
        if not self._connected:
            return 0

        try:
            # Serialize values if needed
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(value)

            return self._client.lpush(key, *serialized_values)
        except Exception as e:
            logger.error(f"Redis lpush error: {str(e)}")
            return 0

    def rpush(self, key: str, *values: Any) -> int:
        """Push values to the right of list"""
        if not self._connected:
            return 0

        try:
            # Serialize values if needed
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(value)

            return self._client.rpush(key, *serialized_values)
        except Exception as e:
            logger.error(f"Redis rpush error: {str(e)}")
            return 0

    def lpop(self, key: str) -> Optional[str]:
        """Pop value from the left of list"""
        if not self._connected:
            return None

        try:
            return self._client.lpop(key)
        except Exception as e:
            logger.error(f"Redis lpop error: {str(e)}")
            return None

    def rpop(self, key: str) -> Optional[str]:
        """Pop value from the right of list"""
        if not self._connected:
            return None

        try:
            return self._client.rpop(key)
        except Exception as e:
            logger.error(f"Redis rpop error: {str(e)}")
            return None

    def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Get range of values from list"""
        if not self._connected:
            return []

        try:
            return self._client.lrange(key, start, end)
        except Exception as e:
            logger.error(f"Redis lrange error: {str(e)}")
            return []

    def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim list to specified range"""
        if not self._connected:
            return False

        try:
            return self._client.ltrim(key, start, end)
        except Exception as e:
            logger.error(f"Redis ltrim error: {str(e)}")
            return False

    # Set operations

    def sadd(self, key: str, *values: Any) -> int:
        """Add values to set"""
        if not self._connected:
            return 0

        try:
            return self._client.sadd(key, *values)
        except Exception as e:
            logger.error(f"Redis sadd error: {str(e)}")
            return 0

    def srem(self, key: str, *values: Any) -> int:
        """Remove values from set"""
        if not self._connected:
            return 0

        try:
            return self._client.srem(key, *values)
        except Exception as e:
            logger.error(f"Redis srem error: {str(e)}")
            return 0

    def smembers(self, key: str) -> set:
        """Get all members of set"""
        if not self._connected:
            return set()

        try:
            return self._client.smembers(key)
        except Exception as e:
            logger.error(f"Redis smembers error: {str(e)}")
            return set()

    def sismember(self, key: str, value: Any) -> bool:
        """Check if value is member of set"""
        if not self._connected:
            return False

        try:
            return self._client.sismember(key, value)
        except Exception as e:
            logger.error(f"Redis sismember error: {str(e)}")
            return False

    # Cache helpers

    def cache_get_or_set(
        self, key: str, func: callable, ttl: int = 300, *args, **kwargs
    ) -> Any:
        """
        Get from cache or compute and set

        Args:
            key: Cache key
            func: Function to compute value if not in cache
            ttl: Time to live in seconds
            *args, **kwargs: Arguments for func

        Returns:
            Cached or computed value
        """
        # Try to get from cache
        cached = self.get(key)
        if cached is not None:
            return cached

        # Compute value
        value = func(*args, **kwargs)

        # Store in cache
        self.set(key, value, ex=ttl)

        return value

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self._connected:
            return 0

        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis clear_pattern error: {str(e)}")
            return 0

    def close(self):
        """Close Redis connection"""
        if self._client:
            self._client.close()
            self._connected = False


# Singleton instance
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Get Redis client instance"""
    global _redis_client

    if _redis_client is None:
        _redis_client = RedisClient()

    return _redis_client


# Export
__all__ = ["RedisClient", "get_redis_client"]
