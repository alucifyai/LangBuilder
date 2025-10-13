"""Permission caching for RBAC enforcement.

This module provides caching functionality for permission evaluation results,
significantly improving performance by avoiding repeated database queries.
"""

import logging
from typing import Any
from uuid import UUID

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class PermissionCache:
    """Thread-safe permission cache with TTL and invalidation support.

    Uses cachetools.TTLCache for automatic expiration of cached entries.
    Provides methods for cache invalidation when roles or assignments change.

    Default TTL is 5 minutes (300 seconds), configurable via environment variable.
    """

    def __init__(self, maxsize: int = 10000, ttl: int = 300):
        """Initialize the permission cache.

        Args:
            maxsize: Maximum number of entries in cache (default 10,000)
            ttl: Time-to-live in seconds for cache entries (default 300 = 5 minutes)
        """
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._maxsize = maxsize
        self._ttl = ttl
        logger.info(f"Initialized PermissionCache with maxsize={maxsize}, ttl={ttl}s")

    def _make_key(
        self,
        user_id: UUID,
        permission: str,
        resource_type: str,
        resource_id: UUID,
    ) -> str:
        """Create cache key from permission check parameters.

        Args:
            user_id: User or service account ID
            permission: Permission string (e.g., "flow.read")
            resource_type: Type of resource (e.g., "flow")
            resource_id: Resource UUID

        Returns:
            Cache key string
        """
        return f"perm:{user_id}:{permission}:{resource_type}:{resource_id}"

    async def get(
        self,
        user_id: UUID,
        permission: str,
        resource_type: str,
        resource_id: UUID,
    ) -> bool | None:
        """Get cached permission result.

        Args:
            user_id: User or service account ID
            permission: Permission string
            resource_type: Type of resource
            resource_id: Resource UUID

        Returns:
            Cached boolean result, or None if not in cache
        """
        key = self._make_key(user_id, permission, resource_type, resource_id)
        result = self._cache.get(key)

        if result is not None:
            logger.debug(f"Cache HIT: {key} = {result}")
        else:
            logger.debug(f"Cache MISS: {key}")

        return result

    async def set(
        self,
        user_id: UUID,
        permission: str,
        resource_type: str,
        resource_id: UUID,
        value: bool,
    ) -> None:
        """Set cached permission result.

        Args:
            user_id: User or service account ID
            permission: Permission string
            resource_type: Type of resource
            resource_id: Resource UUID
            value: Permission result to cache
        """
        key = self._make_key(user_id, permission, resource_type, resource_id)
        self._cache[key] = value
        logger.debug(f"Cache SET: {key} = {value}")

    async def invalidate_user(self, user_id: UUID) -> int:
        """Invalidate all cached permissions for a user.

        Should be called when:
        - User's role assignment changes
        - User joins/leaves a group
        - User's group's role assignment changes

        Args:
            user_id: User ID to invalidate

        Returns:
            Number of entries invalidated
        """
        user_prefix = f"perm:{user_id}:"
        keys_to_delete = [key for key in self._cache.keys() if str(key).startswith(user_prefix)]

        count = 0
        for key in keys_to_delete:
            del self._cache[key]
            count += 1

        if count > 0:
            logger.info(f"Invalidated {count} cache entries for user {user_id}")

        return count

    async def invalidate_role(self, role_id: UUID) -> int:
        """Invalidate all cached permissions for users with a specific role.

        Should be called when:
        - Role's permissions are modified
        - Role is deleted

        Note: This is a coarse-grained invalidation that clears the entire cache.
        In production, you may want to track role → user mappings for finer control.

        Args:
            role_id: Role ID whose assignments should be invalidated

        Returns:
            Number of entries invalidated
        """
        # For MVP, we clear entire cache on role permission changes
        # In production, maintain role → user mapping for targeted invalidation
        count = len(self._cache)
        self._cache.clear()

        if count > 0:
            logger.warning(
                f"Invalidated entire cache ({count} entries) due to role {role_id} modification. "
                "Consider implementing role → user mapping for targeted invalidation."
            )

        return count

    async def invalidate_resource(
        self,
        resource_type: str,
        resource_id: UUID,
    ) -> int:
        """Invalidate all cached permissions for a specific resource.

        Should be called when:
        - Resource-scoped role assignments change
        - Resource is moved to different workspace/project

        Args:
            resource_type: Type of resource
            resource_id: Resource UUID

        Returns:
            Number of entries invalidated
        """
        resource_suffix = f":{resource_type}:{resource_id}"
        keys_to_delete = [key for key in self._cache.keys() if str(key).endswith(resource_suffix)]

        count = 0
        for key in keys_to_delete:
            del self._cache[key]
            count += 1

        if count > 0:
            logger.info(f"Invalidated {count} cache entries for {resource_type} {resource_id}")

        return count

    async def clear(self) -> int:
        """Clear entire cache.

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()

        if count > 0:
            logger.info(f"Cleared entire permission cache ({count} entries)")

        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics including size, capacity, TTL
        """
        return {
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "ttl_seconds": self._ttl,
            "hit_rate": None,  # cachetools doesn't track hit rate, would need custom wrapper
        }


# Global cache instance
# In production, this could be replaced with Redis for multi-instance deployments
_global_cache: PermissionCache | None = None


def get_permission_cache(maxsize: int = 10000, ttl: int = 300) -> PermissionCache:
    """Get or create the global permission cache instance.

    Args:
        maxsize: Maximum cache size (only used on first call)
        ttl: Time-to-live in seconds (only used on first call)

    Returns:
        Global PermissionCache instance
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = PermissionCache(maxsize=maxsize, ttl=ttl)

    return _global_cache


def reset_permission_cache() -> None:
    """Reset the global permission cache.

    Useful for testing and initialization.
    """
    global _global_cache
    _global_cache = None
