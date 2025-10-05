"""Permission caching layer for RBAC system.

Implements caching for permission checks to reduce database queries.
Supports both in-memory (LRU) and Redis caching strategies.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from uuid import UUID

    from langflow.services.database.models.rbac.grant import PrincipalType, ScopeType


class PermissionCache:
    """Permission evaluation cache.

    Caches permission check results to avoid repeated database queries.
    Cache entries are invalidated when grants are created/updated/deleted.
    """

    def __init__(self, cache_ttl: int = 300, use_redis: bool = False):
        """Initialize permission cache.

        Args:
            cache_ttl: Time-to-live for cache entries in seconds (default: 5 minutes)
            use_redis: Whether to use Redis for distributed caching (default: False)
        """
        self.cache_ttl = cache_ttl
        self.use_redis = use_redis
        self._redis_client = None

        if use_redis:
            try:
                import redis

                # Try to connect to Redis
                # In production, these should come from settings
                self._redis_client = redis.Redis(
                    host="localhost",
                    port=6379,
                    db=0,
                    decode_responses=True,
                )
                self._redis_client.ping()
                logger.info("Permission cache using Redis")
            except Exception as e:
                logger.warning(f"Redis connection failed, falling back to in-memory cache: {e}")
                self._redis_client = None
                self.use_redis = False

        if not self.use_redis:
            logger.info("Permission cache using in-memory LRU")

    def _make_cache_key(
        self,
        principal_type: PrincipalType | str,
        principal_id: UUID | str,
        permission: str,
        scope_type: ScopeType | str,
        scope_id: str,
    ) -> str:
        """Generate cache key for a permission check.

        Args:
            principal_type: Type of principal
            principal_id: ID of the principal
            permission: Permission being checked
            scope_type: Type of scope
            scope_id: ID of the scoped resource

        Returns:
            Cache key string
        """
        key_data = {
            "principal_type": str(principal_type),
            "principal_id": str(principal_id),
            "permission": permission,
            "scope_type": str(scope_type),
            "scope_id": scope_id,
        }
        key_json = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_json.encode()).hexdigest()[:16]
        return f"perm:{key_hash}"

    async def get(
        self,
        principal_type: PrincipalType | str,
        principal_id: UUID | str,
        permission: str,
        scope_type: ScopeType | str,
        scope_id: str,
    ) -> bool | None:
        """Get cached permission check result.

        Args:
            principal_type: Type of principal
            principal_id: ID of the principal
            permission: Permission being checked
            scope_type: Type of scope
            scope_id: ID of the scoped resource

        Returns:
            Cached result (True/False) or None if not cached
        """
        key = self._make_cache_key(principal_type, principal_id, permission, scope_type, scope_id)

        if self.use_redis and self._redis_client:
            try:
                value = self._redis_client.get(key)
                if value is not None:
                    logger.debug(f"Permission cache HIT (Redis): {key}")
                    return value == "1"
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        # Fall back to in-memory cache
        return self._get_from_memory(key)

    async def set(
        self,
        principal_type: PrincipalType | str,
        principal_id: UUID | str,
        permission: str,
        scope_type: ScopeType | str,
        scope_id: str,
        result: bool,
    ) -> None:
        """Set cached permission check result.

        Args:
            principal_type: Type of principal
            principal_id: ID of the principal
            permission: Permission being checked
            scope_type: Type of scope
            scope_id: ID of the scoped resource
            result: Permission check result to cache
        """
        key = self._make_cache_key(principal_type, principal_id, permission, scope_type, scope_id)

        if self.use_redis and self._redis_client:
            try:
                self._redis_client.setex(
                    key,
                    self.cache_ttl,
                    "1" if result else "0",
                )
                logger.debug(f"Permission cache SET (Redis): {key} = {result}")
                return
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")

        # Fall back to in-memory cache
        self._set_in_memory(key, result)

    async def invalidate_principal(
        self,
        principal_type: PrincipalType | str,
        principal_id: UUID | str,
    ) -> None:
        """Invalidate all cache entries for a principal.

        Should be called when:
        - A grant is created/deleted for the principal
        - A user joins/leaves a group
        - A role's permissions are modified

        Args:
            principal_type: Type of principal
            principal_id: ID of the principal
        """
        if self.use_redis and self._redis_client:
            try:
                # In Redis, we'd need to track principal keys or use a different key structure
                # For now, we flush the entire permission cache
                # In production, use key prefixes like "perm:user:{user_id}:*"
                pattern = "perm:*"
                cursor = 0
                while True:
                    cursor, keys = self._redis_client.scan(cursor, match=pattern, count=100)
                    if keys:
                        self._redis_client.delete(*keys)
                    if cursor == 0:
                        break
                logger.debug(f"Permission cache INVALIDATE (Redis): {principal_type}:{principal_id}")
            except Exception as e:
                logger.warning(f"Redis invalidation failed: {e}")

        # For in-memory cache, clear everything
        # (LRU cache doesn't support selective invalidation)
        self._clear_memory_cache()

    async def invalidate_all(self) -> None:
        """Invalidate entire permission cache.

        Should be called when:
        - System roles are modified
        - Permission catalog is updated
        - Major RBAC configuration changes

        Use sparingly as it impacts all users.
        """
        if self.use_redis and self._redis_client:
            try:
                pattern = "perm:*"
                cursor = 0
                while True:
                    cursor, keys = self._redis_client.scan(cursor, match=pattern, count=100)
                    if keys:
                        self._redis_client.delete(*keys)
                    if cursor == 0:
                        break
                logger.info("Permission cache INVALIDATE ALL (Redis)")
            except Exception as e:
                logger.warning(f"Redis invalidation failed: {e}")

        self._clear_memory_cache()

    @staticmethod
    @lru_cache(maxsize=1000)
    def _get_from_memory(key: str) -> bool | None:
        """Get from in-memory LRU cache.

        Note: This is a static method with LRU cache decorator.
        Returns None for cache misses.
        """
        # LRU cache stores function call results
        # We use a sentinel pattern - if this function is called,
        # it's a cache miss (we only store in _cached_results dict)
        return _MEMORY_CACHE.get(key)

    @staticmethod
    def _set_in_memory(key: str, value: bool) -> None:
        """Set in in-memory cache."""
        _MEMORY_CACHE[key] = value
        logger.debug(f"Permission cache SET (memory): {key} = {value}")

    @staticmethod
    def _clear_memory_cache() -> None:
        """Clear in-memory cache."""
        _MEMORY_CACHE.clear()
        # Also clear LRU cache
        PermissionCache._get_from_memory.cache_clear()
        logger.info("Permission cache CLEARED (memory)")


# Global in-memory cache dictionary
# In production, consider using a proper cache library like cachetools
_MEMORY_CACHE: dict[str, bool] = {}


# Singleton instance for easy access
_cache_instance: PermissionCache | None = None


def get_permission_cache(cache_ttl: int = 300, use_redis: bool = False) -> PermissionCache:
    """Get singleton permission cache instance.

    Args:
        cache_ttl: Time-to-live for cache entries in seconds
        use_redis: Whether to use Redis for distributed caching

    Returns:
        PermissionCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = PermissionCache(cache_ttl=cache_ttl, use_redis=use_redis)
    return _cache_instance
