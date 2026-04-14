# app/utils/cache/eviction.py
"""
Cache eviction policies

Implements various eviction strategies for cache management:
- LRU (Least Recently Used)
- LFU (Least Frequently Used) with decay
- TTL (Time To Live)
"""
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Generic, Optional, TypeVar

T = TypeVar("T")


class EvictionPolicy(ABC, Generic[T]):
    """Abstract base class for eviction policies"""

    @abstractmethod
    def add(self, key: str, value: T) -> None:
        """Add value to policy tracking"""
        pass

    @abstractmethod
    def access(self, key: str) -> None:
        """Update access information for value"""
        pass

    @abstractmethod
    def remove(self, key: str) -> None:
        """Remove value from policy tracking"""
        pass

    @abstractmethod
    def get_eviction_candidate(self) -> Optional[str]:
        """Get key to evict according to policy"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Reset the policy"""
        pass


class LRUPolicy(EvictionPolicy[T]):
    """Least Recently Used (LRU) eviction policy"""

    def __init__(self):
        self.access_times: Dict[str, float] = {}
        self._lock = threading.RLock()

    def add(self, key: str, value: T) -> None:
        with self._lock:
            self.access_times[key] = time.time()

    def access(self, key: str) -> None:
        with self._lock:
            if key in self.access_times:
                self.access_times[key] = time.time()

    def remove(self, key: str) -> None:
        with self._lock:
            if key in self.access_times:
                del self.access_times[key]

    def get_eviction_candidate(self) -> Optional[str]:
        with self._lock:
            if not self.access_times:
                return None
            return min(self.access_times.items(), key=lambda x: x[1])[0]

    def clear(self) -> None:
        with self._lock:
            self.access_times.clear()


class LFUPolicy(EvictionPolicy[T]):
    """Least Frequently Used (LFU) eviction policy with decay support"""

    def __init__(self, decay_factor: float = 0.95, decay_period: int = 3600):
        """
        Initialize LFU policy

        Args:
            decay_factor: Decay factor for old frequencies (0-1)
            decay_period: Time in seconds between decays
        """
        self.access_counts: Dict[str, float] = {}  # Float values to support decay
        self.last_decay_time = time.time()
        self.decay_factor = decay_factor
        self.decay_period = decay_period
        self._lock = threading.RLock()

    def add(self, key: str, value: T) -> None:
        with self._lock:
            self._check_decay()
            self.access_counts[key] = self.access_counts.get(key, 0) + 1

    def access(self, key: str) -> None:
        with self._lock:
            self._check_decay()
            if key in self.access_counts:
                self.access_counts[key] += 1

    def remove(self, key: str) -> None:
        with self._lock:
            if key in self.access_counts:
                del self.access_counts[key]

    def get_eviction_candidate(self) -> Optional[str]:
        with self._lock:
            if not self.access_counts:
                return None

            # Sort by usage count from lowest to highest
            return min(self.access_counts.items(), key=lambda x: x[1])[0]

    def _check_decay(self) -> None:
        """Check if usage values should be decayed"""
        now = time.time()
        time_since_decay = now - self.last_decay_time

        # If enough time has passed since last decay
        if time_since_decay >= self.decay_period:
            # Apply decay to all values
            for key in self.access_counts:
                self.access_counts[key] *= self.decay_factor

            # Update last decay time
            self.last_decay_time = now

    def clear(self) -> None:
        with self._lock:
            self.access_counts.clear()
            self.last_decay_time = time.time()


class TTLPolicy(EvictionPolicy[T]):
    """Time-To-Live (TTL) eviction policy"""

    def __init__(self):
        self.expiry_times: Dict[str, float] = {}
        self._lock = threading.RLock()

    def add(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        with self._lock:
            if ttl is not None and ttl > 0:
                self.expiry_times[key] = time.time() + ttl

    def access(self, key: str) -> None:
        # No update needed for TTL
        pass

    def remove(self, key: str) -> None:
        with self._lock:
            if key in self.expiry_times:
                del self.expiry_times[key]

    def get_eviction_candidate(self) -> Optional[str]:
        with self._lock:
            # Remove expired keys
            now = time.time()
            expired_keys = [k for k, t in self.expiry_times.items() if t <= now]

            for key in expired_keys:
                del self.expiry_times[key]

            # If keys remain, return the closest to expiration
            if not self.expiry_times:
                return None

            return min(self.expiry_times.items(), key=lambda x: x[1])[0]

    def is_expired(self, key: str) -> bool:
        """Check if a key has expired"""
        with self._lock:
            if key in self.expiry_times:
                return time.time() > self.expiry_times[key]
            return False

    def clear(self) -> None:
        with self._lock:
            self.expiry_times.clear()


class PolicyFactory:
    """Factory for creating eviction policies by name"""

    @staticmethod
    def create(policy_name: str) -> EvictionPolicy:
        """
        Create eviction policy by name

        Args:
            policy_name: Policy name ("lru", "lfu", "ttl")

        Returns:
            EvictionPolicy: Eviction policy instance

        Raises:
            ValueError: If policy name is unknown
        """
        policy_name = policy_name.lower()

        if policy_name == "lru":
            return LRUPolicy()
        elif policy_name == "lfu":
            return LFUPolicy()
        elif policy_name == "ttl":
            return TTLPolicy()
        else:
            raise ValueError(f"Unknown eviction policy: {policy_name}")


# Export main components
__all__ = ["EvictionPolicy", "LRUPolicy", "LFUPolicy", "TTLPolicy", "PolicyFactory"]
