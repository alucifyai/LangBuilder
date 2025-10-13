"""Performance validation tests for RBAC system.

This module validates that RBAC performance meets NFR requirements:
- Cached permission check ≤10ms p95
- Uncached permission check ≤100ms p95

Uses manual timing rather than pytest-benchmark to avoid async event loop conflicts.
"""

import statistics
import time
from uuid import uuid4

import pytest
from langflow.services.database.models.flow import Flow
from langflow.services.database.models.folder import Folder
from langflow.services.database.models.rbac import (
    Permission,
    Role,
    RoleAssignment,
    RolePermission,
)
from langflow.services.database.models.user import User
from langflow.services.database.models.user_group import UserGroup, UserGroupMember
from langflow.services.database.models.workspace import Workspace
from langflow.services.rbac.cache import reset_permission_cache
from langflow.services.rbac.enforcement import RBACEnforcementEngine


@pytest.fixture
async def workspace(async_session):
    """Create a test workspace."""
    workspace = Workspace(
        name="Perf Test Workspace",
        slug="perf-test-workspace",
        description="Performance test workspace",
    )
    async_session.add(workspace)
    await async_session.commit()
    await async_session.refresh(workspace)
    return workspace


@pytest.fixture
async def user(async_session):
    """Create a test user."""
    user = User(
        username=f"perfuser_{uuid4().hex[:8]}",
        password="hashed_password",
        is_active=True,
        is_superuser=False,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def project(async_session, workspace):
    """Create a test project (folder)."""
    project = Folder(
        name="Perf Test Project",
        user_id=uuid4(),
        workspace_id=workspace.id,
    )
    async_session.add(project)
    await async_session.commit()
    await async_session.refresh(project)
    return project


@pytest.fixture
async def flow(async_session, project):
    """Create a test flow."""
    flow = Flow(
        name="Perf Test Flow",
        data={},
        folder_id=project.id,
        user_id=uuid4(),
    )
    async_session.add(flow)
    await async_session.commit()
    await async_session.refresh(flow)
    return flow


@pytest.fixture
async def permission(async_session):
    """Create a test permission."""
    permission = Permission(
        resource_type="flow",
        action="read",
        display_name="Read Flow",
        description="Permission to read flows",
    )
    async_session.add(permission)
    await async_session.commit()
    await async_session.refresh(permission)
    return permission


@pytest.fixture
async def role(async_session, permission):
    """Create a test role with a permission."""
    role = Role(
        name=f"perf_role_{uuid4().hex[:8]}",
        display_name="Performance Test Role",
        description="Role for performance testing",
    )
    async_session.add(role)
    await async_session.commit()
    await async_session.refresh(role)

    role_permission = RolePermission(
        role_id=role.id,
        permission_id=permission.id,
    )
    async_session.add(role_permission)
    await async_session.commit()

    return role


@pytest.fixture
def enforcement_engine(async_session):
    """Create an enforcement engine instance."""
    reset_permission_cache()
    return RBACEnforcementEngine(async_session)


class TestPerformanceValidation:
    """Performance validation tests using manual timing."""

    @pytest.mark.asyncio
    async def test_cached_permission_check_performance(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
        role,
    ):
        """Validate cached permission check meets NFR (≤10ms p95).

        NFR Requirement: Cached permission check ≤10ms p95
        """
        # Setup: Assign role to user
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Prime cache
        await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Run 100 iterations to get p95
        durations = []
        for _ in range(100):
            start = time.perf_counter()
            result = await enforcement_engine.has_permission(
                user_id=user.id,
                permission="flow.read",
                resource_type="flow",
                resource_id=flow.id,
            )
            duration = (time.perf_counter() - start) * 1000  # Convert to ms
            durations.append(duration)
            assert result is True

        # Calculate statistics
        p50 = statistics.median(durations)
        p95 = statistics.quantiles(durations, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(durations, n=100)[98]  # 99th percentile
        mean = statistics.mean(durations)
        max_duration = max(durations)

        print("\n=== Cached Permission Check Performance ===")
        print(f"Mean: {mean:.2f}ms")
        print(f"P50 (median): {p50:.2f}ms")
        print(f"P95: {p95:.2f}ms")
        print(f"P99: {p99:.2f}ms")
        print(f"Max: {max_duration:.2f}ms")
        print(f"Samples: {len(durations)}")

        # Validate NFR requirement
        assert p95 < 10.0, f"P95 latency {p95:.2f}ms exceeds NFR requirement of 10ms"
        print(f"✅ NFR MET: P95 latency {p95:.2f}ms is under 10ms requirement")

    @pytest.mark.asyncio
    async def test_uncached_permission_check_performance(
        self,
        async_session,
        user,
        flow,
        role,
    ):
        """Validate uncached permission check meets NFR (≤100ms p95).

        NFR Requirement: Uncached permission check ≤100ms p95
        """
        # Setup: Assign role to user
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Run 50 iterations with fresh cache each time
        durations = []
        for _ in range(50):
            # Reset cache for each iteration to simulate cold cache
            reset_permission_cache()
            engine = RBACEnforcementEngine(async_session)

            start = time.perf_counter()
            result = await engine.has_permission(
                user_id=user.id,
                permission="flow.read",
                resource_type="flow",
                resource_id=flow.id,
            )
            duration = (time.perf_counter() - start) * 1000  # Convert to ms
            durations.append(duration)
            assert result is True

        # Calculate statistics
        p50 = statistics.median(durations)
        p95 = statistics.quantiles(durations, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else max(durations)
        mean = statistics.mean(durations)
        max_duration = max(durations)

        print("\n=== Uncached Permission Check Performance ===")
        print(f"Mean: {mean:.2f}ms")
        print(f"P50 (median): {p50:.2f}ms")
        print(f"P95: {p95:.2f}ms")
        print(f"P99: {p99:.2f}ms")
        print(f"Max: {max_duration:.2f}ms")
        print(f"Samples: {len(durations)}")

        # Validate NFR requirement
        assert p95 < 100.0, f"P95 latency {p95:.2f}ms exceeds NFR requirement of 100ms"
        print(f"✅ NFR MET: P95 latency {p95:.2f}ms is under 100ms requirement")

    @pytest.mark.asyncio
    async def test_permission_check_with_scope_inheritance_performance(
        self,
        async_session,
        user,
        flow,
        workspace,
        role,
    ):
        """Validate performance with scope inheritance (workspace → flow).

        Tests worst-case scope chain traversal performance.
        """
        # Setup: Assign role at workspace scope (broadest)
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="workspace",
            scope_id=workspace.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Run 50 iterations with fresh cache
        durations = []
        for _ in range(50):
            reset_permission_cache()
            engine = RBACEnforcementEngine(async_session)

            start = time.perf_counter()
            result = await engine.has_permission(
                user_id=user.id,
                permission="flow.read",
                resource_type="flow",
                resource_id=flow.id,
            )
            duration = (time.perf_counter() - start) * 1000
            durations.append(duration)
            assert result is True

        p95 = statistics.quantiles(durations, n=20)[18]
        mean = statistics.mean(durations)

        print("\n=== Scope Inheritance Performance ===")
        print(f"Mean: {mean:.2f}ms")
        print(f"P95: {p95:.2f}ms")

        # Should still meet uncached NFR
        assert p95 < 100.0, f"P95 latency {p95:.2f}ms exceeds 100ms"
        print(f"✅ Scope inheritance P95 latency {p95:.2f}ms is acceptable")

    @pytest.mark.asyncio
    async def test_permission_check_with_group_membership_performance(
        self,
        async_session,
        user,
        flow,
        workspace,
        role,
    ):
        """Validate performance with group-based permissions."""
        # Setup: Create group and add user
        group = UserGroup(
            workspace_id=workspace.id,
            name=f"perf_group_{uuid4().hex[:8]}",
            description="Performance test group",
        )
        async_session.add(group)
        await async_session.commit()
        await async_session.refresh(group)

        membership = UserGroupMember(
            group_id=group.id,
            user_id=user.id,
            is_active=True,
        )
        async_session.add(membership)
        await async_session.commit()

        # Assign role to group
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="group",
            group_id=group.id,
            scope_type="workspace",
            scope_id=workspace.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Run 50 iterations with fresh cache
        durations = []
        for _ in range(50):
            reset_permission_cache()
            engine = RBACEnforcementEngine(async_session)

            start = time.perf_counter()
            result = await engine.has_permission(
                user_id=user.id,
                permission="flow.read",
                resource_type="flow",
                resource_id=flow.id,
            )
            duration = (time.perf_counter() - start) * 1000
            durations.append(duration)
            assert result is True

        p95 = statistics.quantiles(durations, n=20)[18]
        mean = statistics.mean(durations)

        print("\n=== Group Membership Performance ===")
        print(f"Mean: {mean:.2f}ms")
        print(f"P95: {p95:.2f}ms")

        # Should still meet uncached NFR
        assert p95 < 100.0, f"P95 latency {p95:.2f}ms exceeds 100ms"
        print(f"✅ Group membership P95 latency {p95:.2f}ms is acceptable")

    @pytest.mark.asyncio
    async def test_cache_operations_performance(self):
        """Validate cache operations are fast (<1ms)."""
        from langflow.services.rbac.cache import PermissionCache

        reset_permission_cache()
        cache = PermissionCache(maxsize=10000, ttl=300)

        user_id = uuid4()
        resource_id = uuid4()

        # Test key generation (synchronous)
        durations = []
        for _ in range(1000):
            start = time.perf_counter()
            key = cache._make_key(user_id, "flow.read", "flow", resource_id)
            duration = (time.perf_counter() - start) * 1000
            durations.append(duration)

        mean = statistics.mean(durations)
        p95 = statistics.quantiles(durations, n=20)[18]

        print("\n=== Cache Key Generation Performance ===")
        print(f"Mean: {mean:.4f}ms")
        print(f"P95: {p95:.4f}ms")

        assert p95 < 1.0, f"Cache key generation too slow: {p95:.4f}ms"
        print(f"✅ Cache key generation P95 {p95:.4f}ms < 1ms")

        # Test cache get/set (async)
        durations_set = []
        durations_get = []
        for _ in range(100):
            # Set
            start = time.perf_counter()
            await cache.set(user_id, "flow.read", "flow", resource_id, True)
            duration = (time.perf_counter() - start) * 1000
            durations_set.append(duration)

            # Get
            start = time.perf_counter()
            result = await cache.get(user_id, "flow.read", "flow", resource_id)
            duration = (time.perf_counter() - start) * 1000
            durations_get.append(duration)

        mean_set = statistics.mean(durations_set)
        p95_set = statistics.quantiles(durations_set, n=20)[18]
        mean_get = statistics.mean(durations_get)
        p95_get = statistics.quantiles(durations_get, n=20)[18]

        print("\n=== Cache Set Performance ===")
        print(f"Mean: {mean_set:.4f}ms")
        print(f"P95: {p95_set:.4f}ms")

        print("\n=== Cache Get Performance ===")
        print(f"Mean: {mean_get:.4f}ms")
        print(f"P95: {p95_get:.4f}ms")

        assert p95_set < 1.0, f"Cache set too slow: {p95_set:.4f}ms"
        assert p95_get < 1.0, f"Cache get too slow: {p95_get:.4f}ms"
        print("✅ Cache operations P95 < 1ms")
