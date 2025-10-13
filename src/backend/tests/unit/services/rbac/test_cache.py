"""Unit tests for RBAC permission caching."""

from uuid import uuid4

import pytest
from langflow.services.rbac.cache import PermissionCache, get_permission_cache, reset_permission_cache


class TestPermissionCache:
    """Test suite for PermissionCache class."""

    def test_cache_initialization(self):
        """Test cache is initialized with correct parameters."""
        cache = PermissionCache(maxsize=1000, ttl=60)

        assert cache._maxsize == 1000
        assert cache._ttl == 60
        assert len(cache._cache) == 0

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = PermissionCache(maxsize=100, ttl=60)

        user_id = uuid4()
        permission = "flow.read"
        resource_type = "flow"
        resource_id = uuid4()

        # Initially should return None (cache miss)
        result = await cache.get(user_id, permission, resource_type, resource_id)
        assert result is None

        # Set value in cache
        await cache.set(user_id, permission, resource_type, resource_id, True)

        # Should now return cached value
        result = await cache.get(user_id, permission, resource_type, resource_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_cache_stores_false_values(self):
        """Test cache correctly stores False (deny) results."""
        cache = PermissionCache(maxsize=100, ttl=60)

        user_id = uuid4()
        permission = "flow.delete"
        resource_type = "flow"
        resource_id = uuid4()

        # Set False value
        await cache.set(user_id, permission, resource_type, resource_id, False)

        # Should return False, not None
        result = await cache.get(user_id, permission, resource_type, resource_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_cache_invalidate_user(self):
        """Test invalidating all cache entries for a user."""
        cache = PermissionCache(maxsize=100, ttl=60)

        user_id = uuid4()
        other_user_id = uuid4()

        # Set multiple entries for user
        await cache.set(user_id, "flow.read", "flow", uuid4(), True)
        await cache.set(user_id, "flow.update", "flow", uuid4(), True)
        await cache.set(user_id, "project.read", "project", uuid4(), True)

        # Set entries for other user
        await cache.set(other_user_id, "flow.read", "flow", uuid4(), True)

        # Invalidate user's cache
        count = await cache.invalidate_user(user_id)

        assert count == 3  # Should have invalidated 3 entries

        # User's entries should be gone
        result = await cache.get(user_id, "flow.read", "flow", uuid4())
        assert result is None

        # Other user's entries should remain
        # (This is a simplified test; in reality we'd need to track the specific resource_id)

    @pytest.mark.asyncio
    async def test_cache_invalidate_resource(self):
        """Test invalidating cache entries for a specific resource."""
        cache = PermissionCache(maxsize=100, ttl=60)

        resource_id = uuid4()
        resource_type = "flow"

        user1 = uuid4()
        user2 = uuid4()

        # Set entries for same resource, different users
        await cache.set(user1, "flow.read", resource_type, resource_id, True)
        await cache.set(user2, "flow.read", resource_type, resource_id, True)

        # Set entries for different resource
        other_resource_id = uuid4()
        await cache.set(user1, "flow.read", resource_type, other_resource_id, True)

        # Invalidate resource
        count = await cache.invalidate_resource(resource_type, resource_id)

        assert count == 2  # Should have invalidated 2 entries

        # Resource entries should be gone
        result = await cache.get(user1, "flow.read", resource_type, resource_id)
        assert result is None

        result = await cache.get(user2, "flow.read", resource_type, resource_id)
        assert result is None

        # Other resource entry should remain
        result = await cache.get(user1, "flow.read", resource_type, other_resource_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_cache_invalidate_role(self):
        """Test invalidating entire cache on role change."""
        cache = PermissionCache(maxsize=100, ttl=60)

        # Add several entries
        await cache.set(uuid4(), "flow.read", "flow", uuid4(), True)
        await cache.set(uuid4(), "flow.update", "flow", uuid4(), True)
        await cache.set(uuid4(), "project.read", "project", uuid4(), True)

        # Invalidate role (clears entire cache)
        role_id = uuid4()
        count = await cache.invalidate_role(role_id)

        assert count == 3  # Should have cleared all entries
        assert len(cache._cache) == 0

    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """Test clearing entire cache."""
        cache = PermissionCache(maxsize=100, ttl=60)

        # Add several entries
        await cache.set(uuid4(), "flow.read", "flow", uuid4(), True)
        await cache.set(uuid4(), "flow.update", "flow", uuid4(), True)
        await cache.set(uuid4(), "project.read", "project", uuid4(), True)

        assert len(cache._cache) == 3

        # Clear cache
        count = await cache.clear()

        assert count == 3
        assert len(cache._cache) == 0

    def test_cache_get_stats(self):
        """Test getting cache statistics."""
        cache = PermissionCache(maxsize=1000, ttl=300)

        stats = cache.get_stats()

        assert stats["size"] == 0
        assert stats["maxsize"] == 1000
        assert stats["ttl_seconds"] == 300

    @pytest.mark.asyncio
    async def test_cache_key_uniqueness(self):
        """Test that different parameters create unique cache keys."""
        cache = PermissionCache(maxsize=100, ttl=60)

        user_id = uuid4()
        resource_id = uuid4()

        # Set different permissions
        await cache.set(user_id, "flow.read", "flow", resource_id, True)
        await cache.set(user_id, "flow.update", "flow", resource_id, False)

        # Should retrieve correct values
        result_read = await cache.get(user_id, "flow.read", "flow", resource_id)
        result_update = await cache.get(user_id, "flow.update", "flow", resource_id)

        assert result_read is True
        assert result_update is False

    @pytest.mark.asyncio
    async def test_cache_different_resource_types(self):
        """Test cache handles different resource types correctly."""
        cache = PermissionCache(maxsize=100, ttl=60)

        user_id = uuid4()
        resource_id = uuid4()

        # Same ID but different resource types
        await cache.set(user_id, "read", "flow", resource_id, True)
        await cache.set(user_id, "read", "project", resource_id, False)

        # Should retrieve correct values based on resource type
        flow_result = await cache.get(user_id, "read", "flow", resource_id)
        project_result = await cache.get(user_id, "read", "project", resource_id)

        assert flow_result is True
        assert project_result is False


class TestGlobalCacheInstance:
    """Test suite for global cache instance management."""

    def test_get_permission_cache_singleton(self):
        """Test that get_permission_cache returns singleton instance."""
        reset_permission_cache()  # Start fresh

        cache1 = get_permission_cache()
        cache2 = get_permission_cache()

        assert cache1 is cache2  # Should be same instance

    def test_reset_permission_cache(self):
        """Test resetting global cache instance."""
        cache1 = get_permission_cache()
        reset_permission_cache()
        cache2 = get_permission_cache()

        assert cache1 is not cache2  # Should be different instances

    def test_get_permission_cache_with_custom_params(self):
        """Test custom parameters only apply on first call."""
        reset_permission_cache()  # Start fresh

        # First call with custom params
        cache1 = get_permission_cache(maxsize=500, ttl=120)

        assert cache1._maxsize == 500
        assert cache1._ttl == 120

        # Second call with different params should return same instance
        cache2 = get_permission_cache(maxsize=1000, ttl=300)

        assert cache2 is cache1  # Same instance
        assert cache2._maxsize == 500  # Original params
        assert cache2._ttl == 120
