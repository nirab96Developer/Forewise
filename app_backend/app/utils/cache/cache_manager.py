# app/utils/cache/cache_manager.py
"""
Cache management service with Redis and local cache support

Provides fast in-memory storage with remote storage backup,
TTL management, namespaces, and statistics.
"""
import asyncio
import hashlib
import json
import logging
import threading
import time
from datetime import date, datetime
from functools import wraps
from typing import (Any, Callable, Dict, List, Optional, TypeVar, Union)

import redis

try:
    import orjson

    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False

    # Create a simple module-like object as fallback
    class OrjsonFallback:
        def dumps(self, obj, default=None):
            return json.dumps(obj, default=default).encode("utf-8")

        def loads(self, s):
            if isinstance(s, bytes):
                return json.loads(s.decode("utf-8"))
            return json.loads(s)

    orjson = OrjsonFallback()

try:
    from redis import asyncio as aioredis

    HAS_AIOREDIS = True
except ImportError:
    HAS_AIOREDIS = False

# Import eviction policies if available
try:
    from app.utils.cache.eviction import (EvictionPolicy, PolicyFactory,
                                          TTLPolicy)

    HAS_EVICTION = True
except ImportError:
    HAS_EVICTION = False

    # Simple fallback
    class EvictionPolicy:
        def add(self, key: str, value: Any, ttl: Optional[int] = None):
            pass

        def remove(self, key: str):
            pass

        def access(self, key: str):
            pass

        def get_eviction_candidate(self) -> Optional[str]:
            return None

        def clear(self):
            pass

    class TTLPolicy(EvictionPolicy):
        pass

    class PolicyFactory:
        @staticmethod
        def create(policy: str) -> EvictionPolicy:
            return EvictionPolicy()


# Logger setup
logger = logging.getLogger(__name__)

# Generic type for cache value
T = TypeVar("T")


def _json_serializer(obj: Any) -> Any:
    """Special serializer for objects not supported by standard JSON"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    if hasattr(obj, "model_dump") and callable(obj.model_dump):  # Pydantic v2
        return obj.model_dump()
    if hasattr(obj, "dict") and callable(obj.dict):  # Pydantic v1
        return obj.dict()
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return obj.to_dict()
    if hasattr(obj, "__str__"):
        return str(obj)
    return str(obj)


def _safe_json_dumps(obj: Any) -> str:
    """Safe conversion to JSON format with special case handling"""
    if HAS_ORJSON:
        try:
            return orjson.dumps(obj, default=_json_serializer).decode("utf-8")
        except (TypeError, ValueError):
            pass

    try:
        return json.dumps(obj, default=_json_serializer)
    except (TypeError, ValueError, OverflowError):
        return str(obj)


def _safe_json_loads(json_str: str) -> Any:
    """Safe JSON string decoding"""
    if HAS_ORJSON:
        try:
            return orjson.loads(json_str)
        except (TypeError, ValueError):
            pass

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return json_str


def _get_loop_safe():
    """Get event loop safely for all Python versions"""
    try:
        return asyncio.get_running_loop()
    except (RuntimeError, AttributeError):
        return asyncio.get_event_loop()


class CacheService:
    """
    Cache service with Redis and local cache support

    Provides fast in-memory storage with remote storage backup,
    TTL management, namespaces, and statistics.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        max_local_size: int = 1000,
        default_ttl: int = 3600,
        namespace_ttls: Optional[Dict[str, int]] = None,
        protected_namespaces: Optional[List[str]] = None,
        rate_limit_per_second: int = 100,
        auto_cleanup_interval: int = 300,
        admin_token: Optional[str] = None,
        eviction_policy: str = "lru",  # "lru", "lfu", or "ttl"
    ):
        """
        Initialize cache service

        Args:
            redis_url: Redis connection URL (Optional)
            max_local_size: Maximum size of local cache
            default_ttl: Default expiration time in seconds
            namespace_ttls: Specific TTL per namespace
            protected_namespaces: Namespaces protected from deletion
            rate_limit_per_second: Maximum operations per second for Redis
            auto_cleanup_interval: Time in seconds between automatic cleanups
            admin_token: Token for sensitive operations authentication
            eviction_policy: Eviction policy ("lru", "lfu", or "ttl")
        """
        self.default_ttl = default_ttl
        self.max_local_size = max_local_size
        self.admin_token = admin_token
        self.eviction_policy_name = eviction_policy

        # TTL management by namespace
        self.namespace_ttls = namespace_ttls or {}

        # Protected namespaces list
        self.protected_namespaces = set(protected_namespaces or [])

        # Redis rate limiting
        self.rate_limit_per_second = rate_limit_per_second
        self.rate_limit_tokens = rate_limit_per_second
        self.rate_limit_last_check = time.time()
        self.rate_limit_lock = threading.RLock()

        # Initialize local cache
        self.local_cache: Dict[str, Any] = {}
        self.ttl_map: Dict[str, float] = {}
        self.access_times: Dict[str, float] = {}
        self.access_counts: Dict[str, int] = {}
        self.item_metadata: Dict[str, Dict[str, Any]] = {}

        # Initialize eviction policy
        if HAS_EVICTION:
            self.eviction_policy = PolicyFactory.create(eviction_policy)
        else:
            self.eviction_policy = EvictionPolicy()
            logger.warning("Eviction policies not available, using simple fallback")

        # Locks for race prevention
        self._locks: Dict[str, threading.RLock] = {}
        self._global_lock = threading.RLock()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.local_hits = 0
        self.redis_hits = 0
        self.set_count = 0
        self.delete_count = 0
        self.errors = 0
        self.refreshes = 0

        # Namespace statistics
        self.namespace_stats: Dict[str, Dict[str, int]] = {}

        # Initialize Redis connection if needed
        self.redis_client = None
        self.async_redis = None
        self.redis_enabled = False
        self.redis_errors = 0
        self.async_redis_enabled = False

        if redis_url:
            self._connect_redis(redis_url)

        # Start automatic cleanup if configured
        if auto_cleanup_interval > 0:
            self.start_auto_cleanup(auto_cleanup_interval)

    def _connect_redis(self, redis_url: str) -> None:
        """Connect to Redis server"""
        try:
            self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            self.redis_enabled = True
            logger.info("Redis cache initialized successfully")
        except redis.RedisError as e:
            self.redis_errors += 1
            logger.warning(
                f"Failed to connect to Redis: {str(e)}. Using local cache only."
            )

    async def init_async(self, redis_url: Optional[str] = None) -> None:
        """Asynchronous initialization of Redis connection"""
        if not HAS_AIOREDIS:
            logger.warning(
                "aioredis not installed, async operations will fallback to sync"
            )
            return

        if redis_url:
            try:
                self.async_redis = await aioredis.from_url(
                    redis_url, decode_responses=True
                )
                await self.async_redis.ping()
                self.async_redis_enabled = True
                logger.info("Async Redis connection established successfully")
            except Exception as e:
                self.redis_errors += 1
                logger.warning(f"Failed to connect to Redis asynchronously: {str(e)}")

    def _get_ttl_for_namespace(
        self, namespace: Optional[str], expire: Optional[int] = None
    ) -> Optional[int]:
        """Get appropriate TTL by namespace"""
        if expire is not None:
            return expire

        if namespace and namespace in self.namespace_ttls:
            return self.namespace_ttls[namespace]

        return self.default_ttl if self.default_ttl > 0 else None

    def _check_rate_limit(self) -> bool:
        """Check rate limit for Redis calls"""
        with self.rate_limit_lock:
            current_time = time.time()
            time_passed = current_time - self.rate_limit_last_check

            # Refresh tokens
            self.rate_limit_tokens = min(
                self.rate_limit_per_second,
                self.rate_limit_tokens + time_passed * self.rate_limit_per_second,
            )

            self.rate_limit_last_check = current_time

            if self.rate_limit_tokens < 1:
                return False

            self.rate_limit_tokens -= 1
            return True

    def _get_namespace_lock(self, namespace: str) -> threading.RLock:
        """Get lock object by namespace"""
        with self._global_lock:
            if namespace not in self._locks:
                self._locks[namespace] = threading.RLock()
            return self._locks[namespace]

    def _update_namespace_stats(self, namespace: Optional[str], stat_type: str) -> None:
        """Update statistics by namespace"""
        ns = namespace or "_default"

        with self._global_lock:
            if ns not in self.namespace_stats:
                self.namespace_stats[ns] = {
                    "hits": 0,
                    "misses": 0,
                    "sets": 0,
                    "deletes": 0,
                    "errors": 0,
                    "refreshes": 0,
                }

            if stat_type in self.namespace_stats[ns]:
                self.namespace_stats[ns][stat_type] += 1

    def _build_key(self, key: str, namespace: Optional[str] = None) -> str:
        """Build key with Optional namespace"""
        if namespace:
            return f"{namespace}:{key}"
        return key

    def get(
        self,
        key: str,
        default: Any = None,
        namespace: Optional[str] = None,
        refresh_func: Optional[Callable[[Any], Any]] = None,
        max_age: Optional[int] = None,
    ) -> Any:
        """Get value from cache"""
        full_key = self._build_key(key, namespace)

        # Check in local cache
        if full_key in self.local_cache:
            # Check expiration
            if self._is_expired(full_key):
                self._local_delete(full_key)
            else:
                # Update access time
                self.access_times[full_key] = time.time()
                self.eviction_policy.access(full_key)

                value = self.local_cache[full_key]

                # Check max_age if defined
                if max_age is not None and refresh_func is not None:
                    now = time.time()
                    last_update = self.item_metadata.get(full_key, {}).get(
                        "last_update", 0
                    )

                    if now - last_update > max_age:
                        # Value too old, refresh it
                        try:
                            new_value = refresh_func(value)
                            if new_value is not None:
                                self._local_set(full_key, new_value)
                                self.refreshes += 1
                                self._update_namespace_stats(namespace, "refreshes")
                                return new_value
                        except Exception as e:
                            logger.warning(
                                f"Error refreshing cache for {full_key}: {str(e)}"
                            )

                self.hits += 1
                self.local_hits += 1
                self._update_namespace_stats(namespace, "hits")
                return value

        # If Redis is active, try to find there
        if self.redis_enabled and self.redis_client and self._check_rate_limit():
            try:
                redis_value = self.redis_client.get(full_key)

                if redis_value is not None:
                    # Decode value
                    try:
                        value = _safe_json_loads(redis_value)
                    except:
                        value = redis_value

                    # Save also in local cache
                    self._local_set(full_key, value)

                    # Save metadata
                    self.item_metadata[full_key] = {
                        "last_update": time.time(),
                        "source": "redis",
                    }

                    # Get TTL from Redis
                    ttl = self.redis_client.ttl(full_key)
                    if ttl > 0:
                        self.ttl_map[full_key] = time.time() + ttl

                    self.hits += 1
                    self.redis_hits += 1
                    self._update_namespace_stats(namespace, "hits")
                    return value
            except redis.RedisError as e:
                self.errors += 1
                self.redis_errors += 1
                self._update_namespace_stats(namespace, "errors")
                logger.warning(f"Redis error in get: {str(e)}")

        # If we got here and refresh function is defined, try to use it
        if refresh_func is not None:
            try:
                new_value = refresh_func(default)
                if new_value is not None:
                    self.set(key, new_value, namespace=namespace)
                    self.refreshes += 1
                    self._update_namespace_stats(namespace, "refreshes")
                    return new_value
            except Exception as e:
                logger.warning(f"Error in refresh_func for {full_key}: {str(e)}")

        # Value not found anywhere
        self.misses += 1
        self._update_namespace_stats(namespace, "misses")
        return default

    def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> bool:
        """Save value in cache"""
        full_key = self._build_key(key, namespace)

        # Get appropriate TTL by namespace if not explicitly defined
        ttl = self._get_ttl_for_namespace(namespace, expire)

        # Save in local cache
        self._local_set(full_key, value, ttl)

        # Save metadata
        self.item_metadata[full_key] = {"last_update": time.time(), "source": "direct"}

        # Save in Redis if active
        if self.redis_enabled and self.redis_client and self._check_rate_limit():
            try:
                # Convert value to JSON safely
                json_value = _safe_json_dumps(value)

                # Save in Redis
                if ttl is not None:
                    self.redis_client.setex(full_key, ttl, json_value)
                else:
                    self.redis_client.set(full_key, json_value)
            except redis.RedisError as e:
                self.errors += 1
                self.redis_errors += 1
                logger.warning(f"Redis error in set: {str(e)}")

        self.set_count += 1
        self._update_namespace_stats(namespace, "sets")
        return True

    def delete(self, key: str, namespace: Optional[str] = None) -> bool:
        """Delete value from cache"""
        full_key = self._build_key(key, namespace)
        success = False

        # Delete from local cache
        if self._local_delete(full_key):
            success = True

        # Delete from Redis if active
        if self.redis_enabled and self.redis_client and self._check_rate_limit():
            try:
                if self.redis_client.delete(full_key) > 0:
                    success = True
            except redis.RedisError as e:
                self.errors += 1
                self.redis_errors += 1
                self._update_namespace_stats(namespace, "errors")
                logger.warning(f"Redis error in delete: {str(e)}")

        self.delete_count += 1
        self._update_namespace_stats(namespace, "deletes")
        return success

    def exists(self, key: str, namespace: Optional[str] = None) -> bool:
        """Check if value exists in cache"""
        full_key = self._build_key(key, namespace)

        # Check in local cache
        if full_key in self.local_cache:
            # Check expiration
            if self._is_expired(full_key):
                self._local_delete(full_key)
                return False
            return True

        # Check in Redis if active
        if self.redis_enabled and self.redis_client and self._check_rate_limit():
            try:
                return bool(self.redis_client.exists(full_key))
            except redis.RedisError as e:
                self.errors += 1
                self.redis_errors += 1
                self._update_namespace_stats(namespace, "errors")
                logger.warning(f"Redis error in exists: {str(e)}")

        return False

    def flush_namespace(
        self,
        namespace: str,
        admin_mode: bool = False,
        admin_token: Optional[str] = None,
    ) -> int:
        """Clear all values in a specific namespace"""
        # Check permissions
        if namespace in self.protected_namespaces:
            if not admin_mode and admin_token != self.admin_token:
                logger.warning(
                    f"Attempt to flush protected namespace {namespace} without proper authentication"
                )
                return 0

        count = 0

        # Clear in local cache
        prefix = f"{namespace}:"
        keys_to_delete = [k for k in self.local_cache.keys() if k.startswith(prefix)]

        for key in keys_to_delete:
            self._local_delete(key)
            count += 1

        # Clear in Redis if active - use SCAN instead of KEYS for safety
        if self.redis_enabled and self.redis_client:
            try:
                cursor = 0
                namespace_pattern = f"{prefix}*"
                batch_size = 100

                while True:
                    cursor, keys = self.redis_client.scan(
                        cursor=cursor, match=namespace_pattern, count=batch_size
                    )

                    if keys:
                        deleted = self.redis_client.delete(*keys)
                        count += deleted

                    if cursor == 0:
                        break
            except redis.RedisError as e:
                self.errors += 1
                self.redis_errors += 1
                self._update_namespace_stats(namespace, "errors")
                logger.warning(f"Redis error in flush_namespace: {str(e)}")

        return count

    def flush_all(self, admin_token: Optional[str] = None) -> bool:
        """Clear all values in cache"""
        # Verify permissions
        if admin_token != self.admin_token and self.admin_token is not None:
            logger.warning("Unauthorized attempt to flush all cache")
            return False

        # Clear local cache
        self.local_cache.clear()
        self.ttl_map.clear()
        self.access_times.clear()
        self.access_counts.clear()
        self.item_metadata.clear()

        # Clear eviction policy
        self.eviction_policy.clear()

        # Clear namespace statistics
        with self._global_lock:
            for ns in self.namespace_stats:
                for stat in self.namespace_stats[ns]:
                    self.namespace_stats[ns][stat] = 0

        # Clear Redis if active
        if self.redis_enabled and self.redis_client:
            try:
                self.redis_client.flushdb()
            except redis.RedisError as e:
                self.errors += 1
                self.redis_errors += 1
                logger.warning(f"Redis error in flush_all: {str(e)}")
                return False

        return True

    def _evict_entry(self) -> None:
        """Evict value from local cache according to selected eviction policy"""
        key_to_evict = self.eviction_policy.get_eviction_candidate()

        if key_to_evict is not None:
            self._local_delete(key_to_evict)

    def _local_set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Save value in local cache"""
        # Make room if cache is full
        if len(self.local_cache) >= self.max_local_size and key not in self.local_cache:
            self._evict_entry()

        # Save value
        self.local_cache[key] = value
        self.access_times[key] = time.time()
        self.access_counts[key] = self.access_counts.get(key, 0) + 1

        # Update eviction policy
        if isinstance(self.eviction_policy, TTLPolicy):
            self.eviction_policy.add(key, value, expire)
        else:
            self.eviction_policy.add(key, value)

        # Set expiration time
        if expire is not None and expire > 0:
            self.ttl_map[key] = time.time() + expire

    def _local_delete(self, key: str) -> bool:
        """Delete value from local cache"""
        if key in self.local_cache:
            del self.local_cache[key]

            if key in self.ttl_map:
                del self.ttl_map[key]

            if key in self.access_times:
                del self.access_times[key]

            if key in self.access_counts:
                del self.access_counts[key]

            if key in self.item_metadata:
                del self.item_metadata[key]

            # Update eviction policy
            self.eviction_policy.remove(key)

            return True

        return False

    def _is_expired(self, key: str) -> bool:
        """Check if value has expired"""
        if key in self.ttl_map:
            return time.time() > self.ttl_map[key]

        return False

    def cleanup_expired(self) -> int:
        """Clean up expired values"""
        count = 0
        now = time.time()

        # Find expired keys
        expired_keys = [k for k, t in self.ttl_map.items() if t <= now]

        # Delete values
        for key in expired_keys:
            self._local_delete(key)
            count += 1

        return count

    def start_auto_cleanup(self, interval_seconds: int = 300) -> None:
        """Start background process for automatic cleanup of expired values"""

        def cleanup_thread():
            """Automatic cleanup process function"""
            while True:
                try:
                    count = self.cleanup_expired()
                    if count > 0:
                        logger.debug(f"Auto-cleanup removed {count} expired entries")
                except Exception as e:
                    logger.error(f"Error in auto-cleanup: {str(e)}")
                time.sleep(interval_seconds)

        # Start cleanup process as background thread
        thread = threading.Thread(target=cleanup_thread, daemon=True)
        thread.start()
        logger.info(f"Started auto-cleanup thread, interval: {interval_seconds}s")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache activity statistics"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "local_hits": self.local_hits,
            "redis_hits": self.redis_hits,
            "set_count": self.set_count,
            "delete_count": self.delete_count,
            "errors": self.errors,
            "redis_errors": self.redis_errors,
            "refreshes": self.refreshes,
            "rate_limit_tokens": self.rate_limit_tokens,
        }

    def health_check(self) -> Dict[str, Any]:
        """Check cache health"""
        stats = self.get_stats()

        health_info = {
            "local_cache_size": len(self.local_cache),
            "local_cache_max_size": self.max_local_size,
            "local_cache_usage": len(self.local_cache) / self.max_local_size
            if self.max_local_size > 0
            else 0,
            "ttl_entries": len(self.ttl_map),
            "stats": stats,
            "redis_enabled": self.redis_enabled,
            "redis_errors": self.redis_errors,
            "namespaces": self.get_namespaces(),
            "namespace_stats": self.namespace_stats,
            "eviction_policy": self.eviction_policy_name,
        }

        # Check Redis if available
        if self.redis_enabled and self.redis_client:
            try:
                redis_info = self.redis_client.info()
                health_info["redis_status"] = "connected"
                health_info["redis_used_memory"] = redis_info.get(
                    "used_memory_human", "unknown"
                )
                health_info["redis_clients"] = redis_info.get(
                    "connected_clients", "unknown"
                )
            except redis.RedisError as e:
                health_info["redis_status"] = "error"
                health_info["redis_error"] = str(e)
                self.redis_errors += 1
        else:
            health_info["redis_status"] = "disabled"

        return health_info

    def get_namespaces(self) -> List[str]:
        """Get list of existing namespaces in cache"""
        namespaces = set()

        # Extract namespaces from local_cache
        for key in self.local_cache:
            parts = key.split(":", 1)
            if len(parts) > 1:
                namespaces.add(parts[0])

        # Extract namespaces from Redis
        if self.redis_enabled and self.redis_client and self._check_rate_limit():
            try:
                cursor = 0

                while True:
                    cursor, keys = self.redis_client.scan(cursor=cursor, count=100)
                    for key in keys:
                        parts = key.split(":", 1)
                        if len(parts) > 1:
                            namespaces.add(parts[0])

                    if cursor == 0:
                        break
            except redis.RedisError as e:
                logger.warning(f"Redis error in get_namespaces: {str(e)}")

        return list(namespaces)

    # Async methods
    async def aget(
        self, key: str, default: Any = None, namespace: Optional[str] = None
    ) -> Any:
        """Async version of get"""
        # For now, fallback to sync version
        loop = _get_loop_safe()
        return await loop.run_in_executor(None, self.get, key, default, namespace)

    async def aset(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> bool:
        """Async version of set"""
        # For now, fallback to sync version
        loop = _get_loop_safe()
        return await loop.run_in_executor(None, self.set, key, value, expire, namespace)

    async def adelete(self, key: str, namespace: Optional[str] = None) -> bool:
        """Async version of delete"""
        # For now, fallback to sync version
        loop = _get_loop_safe()
        return await loop.run_in_executor(None, self.delete, key, namespace)


# Create singleton instance of cache service
def get_cache_service() -> CacheService:
    """Get cache service instance"""
    from app.core.config import settings

    return CacheService(
        redis_url=getattr(settings, "REDIS_URL", None),
        max_local_size=getattr(settings, "CACHE_MAX_LOCAL_SIZE", 1000),
        default_ttl=getattr(settings, "CACHE_DEFAULT_TTL", 3600),
        namespace_ttls=getattr(settings, "CACHE_NAMESPACE_TTLS", {}),
        protected_namespaces=getattr(
            settings, "CACHE_PROTECTED_NAMESPACES", ["auth", "session", "config"]
        ),
        rate_limit_per_second=getattr(settings, "CACHE_REDIS_RATE_LIMIT", 100),
        auto_cleanup_interval=getattr(settings, "CACHE_AUTO_CLEANUP_INTERVAL", 300),
        admin_token=getattr(settings, "CACHE_ADMIN_TOKEN", None),
        eviction_policy=getattr(settings, "CACHE_EVICTION_POLICY", "lru"),
    )


# ---------------------------------------------------------------------------------
# Decorators for convenient cache usage
# ---------------------------------------------------------------------------------


def cached(
    expire: Optional[int] = None,
    namespace: Optional[str] = None,
    key_prefix: str = "",
    use_hash: bool = True,
    max_age: Optional[int] = None,
):
    """
    Decorator to cache function results

    Args:
        expire: Expiration time in seconds
        namespace: Optional namespace
        key_prefix: Key prefix
        use_hash: Whether to use MD5 hashing for key creation
        max_age: Maximum age before automatic refresh

    Returns:
        Callable: Decorator
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create key from parameters
            if use_hash:
                # Create hashed key from all parameters
                key_repr = f"{key_prefix or func.__name__}:{repr(args)}:{repr(sorted(kwargs.items()))}"
                cache_key = hashlib.md5(key_repr.encode()).hexdigest()
            else:
                # Create string key from all parameters
                key_parts = [key_prefix or func.__name__]

                # Add arguments to key
                for arg in args:
                    key_parts.append(str(arg))

                # Add keyword arguments
                kwarg_parts = []
                for k, v in sorted(kwargs.items()):
                    kwarg_parts.append(f"{k}={v}")

                if kwarg_parts:
                    key_parts.append(",".join(kwarg_parts))

                # Create full key
                cache_key = ":".join(key_parts)

            # Get cache instance
            cache = get_cache_service()

            # Refresh function if needed
            def refresh_function(current_value):
                return func(*args, **kwargs)

            # Check in cache
            result = cache.get(
                cache_key,
                namespace=namespace,
                refresh_func=refresh_function if max_age is not None else None,
                max_age=max_age,
            )

            # If not found, calculate and cache
            if result is None:
                result = func(*args, **kwargs)

                # Check that result is valid
                if result is not None:
                    cache.set(cache_key, result, expire=expire, namespace=namespace)

            return result

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create key from parameters
            if use_hash:
                key_repr = f"{key_prefix or func.__name__}:{repr(args)}:{repr(sorted(kwargs.items()))}"
                cache_key = hashlib.md5(key_repr.encode()).hexdigest()
            else:
                key_parts = [key_prefix or func.__name__]
                for arg in args:
                    key_parts.append(str(arg))
                kwarg_parts = []
                for k, v in sorted(kwargs.items()):
                    kwarg_parts.append(f"{k}={v}")
                if kwarg_parts:
                    key_parts.append(",".join(kwarg_parts))
                cache_key = ":".join(key_parts)

            # Get cache instance
            cache = get_cache_service()

            # Check in cache
            result = await cache.aget(cache_key, namespace=namespace)

            # If not found, calculate and cache
            if result is None:
                result = await func(*args, **kwargs)
                if result is not None:
                    await cache.aset(
                        cache_key, result, expire=expire, namespace=namespace
                    )

            return result

        # Choose appropriate function version
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

    return decorator


def invalidate_cache(
    keys: Union[List[str], Callable[..., List[str]]], namespace: Optional[str] = None
):
    """
    Decorator to invalidate cache values

    Args:
        keys: Keys to invalidate or function returning keys by parameters
        namespace: Optional namespace

    Returns:
        Callable: Decorator
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function
            result = func(*args, **kwargs)

            # Get cache instance
            cache = get_cache_service()

            # Invalidate keys
            keys_to_invalidate = keys(*args, **kwargs) if callable(keys) else keys
            for key in keys_to_invalidate:
                cache.delete(key, namespace=namespace)

            return result

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Execute function
            result = await func(*args, **kwargs)

            # Get cache instance
            cache = get_cache_service()

            # Invalidate keys
            keys_to_invalidate = keys(*args, **kwargs) if callable(keys) else keys
            for key in keys_to_invalidate:
                await cache.adelete(key, namespace=namespace)

            return result

        # Choose appropriate function version
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

    return decorator


# Export main components
__all__ = ["CacheService", "get_cache_service", "cached", "invalidate_cache"]
