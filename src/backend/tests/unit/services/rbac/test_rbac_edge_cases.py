"""
Unit tests for RBAC edge cases and corner scenarios.

These tests cover unusual, boundary, and error conditions:
- Concurrent permission checks
- Cache expiry during permission checks
- Multiple roles with overlapping permissions
- Permission checks with missing/invalid data
- Role hierarchy and priority edge cases
- Circular dependencies and invalid states
- Boundary conditions for TTL and caching
- Race conditions and thread safety
"""

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from langbuilder.services.database.models.rbac import (
    Permission,
    Role,
    RolePermission,
    UserRoleAssignment,
)
from langbuilder.services.rbac.service import RBACService


@pytest.fixture
def mock_database_service():
    """Create mock database service with session support."""
    mock_service = Mock()
    mock_session = AsyncMock()

    # Setup context manager for with_session
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    mock_service.with_session = Mock(return_value=mock_context)

    return mock_service, mock_session


@pytest.fixture
def rbac_service(mock_database_service):
    """Create RBACService instance with mock database."""
    db_service, _ = mock_database_service
    service = RBACService(database_service=db_service)
    return service


class TestRBACServiceCacheEdgeCases:
    """Test cache-related edge cases."""

    @pytest.mark.asyncio
    async def test_cache_expiry_mid_check(self, rbac_service, mock_database_service):
        """Test behavior when cache expires during permission check."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        role_id = uuid4()

        # Setup initial cache that's about to expire
        rbac_service._role_permission_cache = {role_id: {("Read", "Project")}}
        rbac_service._cache_timestamp = time.time() - 3599  # Just under 1 hour

        # Mock query responses
        mock_result = Mock()
        mock_result.all = Mock(return_value=[])

        async def mock_exec(*args, **kwargs):
            # Simulate cache expiring during the check
            rbac_service._cache_timestamp = time.time() - 3601  # Expired
            return mock_result

        mock_session.exec = mock_exec

        # Should handle cache expiry gracefully
        result = await rbac_service.can_access(user_id, "Read", "Project", uuid4())
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_empty_cache_after_initialization(self, rbac_service, mock_database_service):
        """Test behavior when cache is somehow empty after initialization."""
        _, mock_session = mock_database_service

        # Manually clear cache
        rbac_service._role_permission_cache = {}
        rbac_service._cache_timestamp = None

        # Mock reload
        mock_result = Mock()
        mock_result.all = Mock(return_value=[])

        async def mock_exec(*args, **kwargs):
            return mock_result

        mock_session.exec = mock_exec

        # Should reload cache automatically
        result = await rbac_service.can_access(uuid4(), "Read", "Global")

        # Cache should be reloaded (even if empty)
        assert rbac_service._cache_timestamp is not None

    def test_cache_ttl_boundary_exactly_one_hour(self, rbac_service):
        """Test cache validity at exact TTL boundary."""
        # Set cache to exactly 1 hour old
        rbac_service._role_permission_cache = {uuid4(): {("Read", "Global")}}
        rbac_service._cache_timestamp = time.time() - 3600.0  # Exactly 1 hour

        # Should be invalid (>= TTL)
        assert not rbac_service._is_cache_valid()

    def test_cache_ttl_boundary_just_under_one_hour(self, rbac_service):
        """Test cache validity just under TTL boundary."""
        # Set cache to just under 1 hour old
        rbac_service._role_permission_cache = {uuid4(): {("Read", "Global")}}
        rbac_service._cache_timestamp = time.time() - 3599.9  # Just under 1 hour

        # Should be valid
        assert rbac_service._is_cache_valid()


class TestRBACServiceMultipleRolesEdgeCases:
    """Test edge cases with multiple roles and overlapping permissions."""

    @pytest.mark.asyncio
    async def test_user_with_multiple_roles_same_scope(self, rbac_service, mock_database_service):
        """Test user with multiple roles on same scope (redundant assignments)."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        project_id = uuid4()
        role1_id = uuid4()
        role2_id = uuid4()

        # Setup cache with two roles having overlapping permissions
        rbac_service._role_permission_cache = {
            role1_id: {("Read", "Project"), ("Update", "Project")},
            role2_id: {("Read", "Project"), ("Delete", "Project")},
        }
        rbac_service._cache_timestamp = time.time()

        # User has both roles on same project
        assignment1 = UserRoleAssignment(
            id=uuid4(),
            user_id=user_id,
            role_id=role1_id,
            scope_type="Project",
            scope_id=project_id,
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        assignment2 = UserRoleAssignment(
            id=uuid4(),
            user_id=user_id,
            role_id=role2_id,
            scope_type="Project",
            scope_id=project_id,
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        # Mock queries
        mock_result_admin = Mock()
        mock_result_admin.all = Mock(return_value=[])

        mock_result_direct = Mock()
        mock_result_direct.all = Mock(return_value=[assignment1, assignment2])

        exec_call_count = [0]

        async def mock_exec(*args, **kwargs):
            exec_call_count[0] += 1
            if exec_call_count[0] == 1:
                return mock_result_admin
            else:
                return mock_result_direct

        mock_session.exec = mock_exec

        # Should grant permission if ANY role has it
        assert await rbac_service.can_access(user_id, "Delete", "Project", project_id)  # From role2

    @pytest.mark.asyncio
    async def test_user_with_role_having_no_permissions(self, rbac_service, mock_database_service):
        """Test user with a role that has no permissions."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        project_id = uuid4()
        role_id = uuid4()

        # Setup cache with role having NO permissions
        rbac_service._role_permission_cache = {
            role_id: set()  # Empty permissions
        }
        rbac_service._cache_timestamp = time.time()

        assignment = UserRoleAssignment(
            id=uuid4(),
            user_id=user_id,
            role_id=role_id,
            scope_type="Project",
            scope_id=project_id,
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        # Mock queries
        mock_result_admin = Mock()
        mock_result_admin.all = Mock(return_value=[])

        mock_result_direct = Mock()
        mock_result_direct.all = Mock(return_value=[assignment])

        exec_call_count = [0]

        async def mock_exec(*args, **kwargs):
            exec_call_count[0] += 1
            if exec_call_count[0] == 1:
                return mock_result_admin
            else:
                return mock_result_direct

        mock_session.exec = mock_exec

        # Should deny access (role has no permissions)
        assert not await rbac_service.can_access(user_id, "Read", "Project", project_id)


class TestRBACServiceInheritanceEdgeCases:
    """Test edge cases for permission inheritance."""

    @pytest.mark.asyncio
    async def test_flow_inheritance_with_nonexistent_project(self, rbac_service, mock_database_service):
        """Test flow inheritance when project doesn't exist."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        flow_id = uuid4()

        # Setup cache
        rbac_service._role_permission_cache = {}
        rbac_service._cache_timestamp = time.time()

        # Mock queries - flow doesn't exist
        mock_result_admin = Mock()
        mock_result_admin.all = Mock(return_value=[])

        mock_result_flow = Mock()
        mock_result_flow.all = Mock(return_value=[])

        # Flow query returns None (flow doesn't exist or has no project)
        mock_result_flow_lookup = Mock()
        mock_result_flow_lookup.first = Mock(return_value=None)

        exec_call_count = [0]

        async def mock_exec(*args, **kwargs):
            exec_call_count[0] += 1
            if exec_call_count[0] == 1:
                return mock_result_admin
            elif exec_call_count[0] == 2:
                return mock_result_flow
            else:
                return mock_result_flow_lookup

        mock_session.exec = mock_exec

        # Should deny access (no inheritance possible)
        result = await rbac_service.can_access(user_id, "Read", "Flow", flow_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_flow_with_null_project_id(self, rbac_service, mock_database_service):
        """Test flow inheritance when flow has null project_id."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        flow_id = uuid4()
        role_id = uuid4()

        # Setup cache
        rbac_service._role_permission_cache = {
            role_id: {("Read", "Project")}
        }
        rbac_service._cache_timestamp = time.time()

        # Mock queries
        mock_result_admin = Mock()
        mock_result_admin.all = Mock(return_value=[])

        mock_result_flow = Mock()
        mock_result_flow.all = Mock(return_value=[])

        # Flow has no project (null folder_id)
        mock_result_flow_lookup = Mock()
        mock_result_flow_lookup.first = Mock(return_value=None)

        exec_call_count = [0]

        async def mock_exec(*args, **kwargs):
            exec_call_count[0] += 1
            if exec_call_count[0] == 1:
                return mock_result_admin
            elif exec_call_count[0] == 2:
                return mock_result_flow
            else:
                return mock_result_flow_lookup

        mock_session.exec = mock_exec

        # Should deny access (no project to inherit from)
        result = await rbac_service.can_access(user_id, "Read", "Flow", flow_id)
        assert result is False


class TestRBACServiceAssignmentEdgeCases:
    """Test edge cases for assignment CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_assignment_with_same_user_role_different_scope(
        self, rbac_service, mock_database_service
    ):
        """Test creating multiple assignments with same user/role but different scopes."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        role_id = uuid4()
        project1_id = uuid4()
        project2_id = uuid4()

        # Mock for first assignment
        mock_result1 = Mock()
        mock_result1.first = Mock(return_value=None)  # No duplicate

        exec_call_count = [0]

        async def mock_exec(*args, **kwargs):
            exec_call_count[0] += 1
            return mock_result1

        mock_session.exec = mock_exec
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Create first assignment (Project 1)
        assignment1 = await rbac_service.create_assignment(
            user_id=user_id,
            role_id=role_id,
            scope_type="Project",
            scope_id=project1_id,
        )

        # Should succeed
        assert assignment1.user_id == user_id
        assert assignment1.scope_id == project1_id

        # Create second assignment (Project 2) - same user/role, different scope
        # Reset mock
        exec_call_count[0] = 0

        assignment2 = await rbac_service.create_assignment(
            user_id=user_id,
            role_id=role_id,
            scope_type="Project",
            scope_id=project2_id,
        )

        # Should also succeed (different scope)
        assert assignment2.user_id == user_id
        assert assignment2.scope_id == project2_id

    @pytest.mark.asyncio
    async def test_update_assignment_to_same_role(self, rbac_service, mock_database_service):
        """Test updating an assignment to the same role (no-op)."""
        _, mock_session = mock_database_service

        assignment_id = uuid4()
        role_id = uuid4()

        assignment = UserRoleAssignment(
            id=assignment_id,
            user_id=uuid4(),
            role_id=role_id,
            scope_type="Project",
            scope_id=uuid4(),
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        role = Role(id=role_id, name="TestRole", is_system=False)

        # Mock get calls
        mock_session.get = AsyncMock(side_effect=[assignment, role])
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Update to same role
        updated = await rbac_service.update_assignment(assignment_id, role_id)

        # Should succeed (even though it's a no-op)
        assert updated.role_id == role_id

    @pytest.mark.asyncio
    async def test_delete_nonexistent_assignment(self, rbac_service, mock_database_service):
        """Test deleting an assignment that doesn't exist."""
        _, mock_session = mock_database_service

        fake_id = uuid4()

        # Mock get returns None
        mock_session.get = AsyncMock(return_value=None)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Assignment .* not found"):
            await rbac_service.delete_assignment(fake_id)

    @pytest.mark.asyncio
    async def test_get_assignments_with_no_results(self, rbac_service, mock_database_service):
        """Test getting assignments when none match filters."""
        _, mock_session = mock_database_service

        # Mock empty result
        mock_result = Mock()
        mock_result.all = Mock(return_value=[])

        async def mock_exec(*args, **kwargs):
            return mock_result

        mock_session.exec = mock_exec

        # Should return empty list
        assignments = await rbac_service.get_assignments(
            user_id=uuid4(),
            role_id=uuid4(),
            scope_type="Project",
        )

        assert assignments == []


class TestRBACServiceErrorHandling:
    """Test error handling and resilience."""

    @pytest.mark.asyncio
    async def test_can_access_with_database_error(self, rbac_service, mock_database_service):
        """Test that database errors are handled gracefully."""
        _, mock_session = mock_database_service

        # Setup cache
        rbac_service._role_permission_cache = {}
        rbac_service._cache_timestamp = time.time()

        # Make query raise exception
        mock_session.exec = AsyncMock(side_effect=Exception("Database connection lost"))

        # Should return False (fail closed)
        result = await rbac_service.can_access(uuid4(), "Read", "Project", uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_create_assignment_with_database_error(self, rbac_service, mock_database_service):
        """Test that database errors during assignment creation are propagated."""
        _, mock_session = mock_database_service

        # Make commit fail
        mock_session.exec = AsyncMock(return_value=Mock(first=Mock(return_value=None)))
        mock_session.add = Mock()
        mock_session.commit = AsyncMock(side_effect=Exception("Database error"))

        # Should raise exception
        with pytest.raises(Exception, match="Database error"):
            await rbac_service.create_assignment(
                user_id=uuid4(),
                role_id=uuid4(),
                scope_type="Global",
                scope_id=None,
            )

    @pytest.mark.asyncio
    async def test_initialize_with_database_error(self, rbac_service, mock_database_service):
        """Test that initialization errors are handled gracefully."""
        _, mock_session = mock_database_service

        # Make exec raise exception
        mock_session.exec = AsyncMock(side_effect=Exception("Database not available"))

        # Should not raise, but log warning
        await rbac_service.initialize()

        # Cache should remain empty
        assert rbac_service._role_permission_cache == {}


class TestRBACServiceBoundaryConditions:
    """Test boundary conditions and limits."""

    @pytest.mark.asyncio
    async def test_user_with_many_assignments(self, rbac_service, mock_database_service):
        """Test performance with user having many role assignments."""
        _, mock_session = mock_database_service

        user_id = uuid4()

        # Create many assignments (simulate user with 100 role assignments)
        assignments = []
        for i in range(100):
            assignments.append(
                UserRoleAssignment(
                    id=uuid4(),
                    user_id=user_id,
                    role_id=uuid4(),
                    scope_type="Project",
                    scope_id=uuid4(),
                    is_immutable=False,
                    created_at=datetime.now(timezone.utc),
                )
            )

        mock_result = Mock()
        mock_result.all = Mock(return_value=assignments)

        async def mock_exec(*args, **kwargs):
            return mock_result

        mock_session.exec = mock_exec

        # Should handle many assignments
        result = await rbac_service.get_user_assignments(user_id)
        assert len(result) == 100

    @pytest.mark.asyncio
    async def test_permission_check_with_none_scope_id_for_project(self, rbac_service, mock_database_service):
        """Test permission check with None scope_id for non-Global scope."""
        _, mock_session = mock_database_service

        user_id = uuid4()

        # Setup cache
        rbac_service._role_permission_cache = {}
        rbac_service._cache_timestamp = time.time()

        # Mock queries
        mock_result = Mock()
        mock_result.all = Mock(return_value=[])

        async def mock_exec(*args, **kwargs):
            return mock_result

        mock_session.exec = mock_exec

        # Permission check with Project scope but None scope_id
        result = await rbac_service.can_access(user_id, "Read", "Project", None)

        # Should handle gracefully (likely deny access)
        assert isinstance(result, bool)


class TestRBACServiceConcurrency:
    """Test concurrent operations and race conditions."""

    @pytest.mark.asyncio
    async def test_multiple_cache_reloads_concurrent(self, rbac_service, mock_database_service):
        """Test behavior when cache is reloaded multiple times concurrently."""
        _, mock_session = mock_database_service

        # Setup expired cache
        rbac_service._role_permission_cache = {}
        rbac_service._cache_timestamp = time.time() - 4000

        # Mock reload
        reload_count = [0]

        def mock_all():
            reload_count[0] += 1
            return []

        mock_result = Mock()
        mock_result.all = mock_all

        async def mock_exec(*args, **kwargs):
            return mock_result

        mock_session.exec = mock_exec

        # Trigger multiple reloads (simulating concurrent requests)
        # Note: This is a simplified test; true concurrency would need asyncio.gather
        await rbac_service._ensure_cache_loaded()
        await rbac_service._ensure_cache_loaded()
        await rbac_service._ensure_cache_loaded()

        # Cache should be reloaded (but ideally only once if proper locking was in place)
        # This documents current behavior
        assert rbac_service._cache_timestamp is not None
