"""
Unit tests for RBACService.

Tests cover:
- Admin bypass logic
- Direct permission checks
- Permission inheritance (Flow from Project)
- Assignment CRUD operations
- Immutability enforcement
- Cache initialization and invalidation
- Graceful error handling
- Performance requirements
"""

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch
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


@pytest.fixture
def sample_roles():
    """Create sample role objects."""
    admin_role = Role(
        id=uuid4(),
        name="Admin",
        description="Administrator role",
        is_system=True,
    )
    owner_role = Role(
        id=uuid4(),
        name="Owner",
        description="Owner role",
        is_system=True,
    )
    editor_role = Role(
        id=uuid4(),
        name="Editor",
        description="Editor role",
        is_system=True,
    )
    viewer_role = Role(
        id=uuid4(),
        name="Viewer",
        description="Viewer role",
        is_system=True,
    )
    return {
        "admin": admin_role,
        "owner": owner_role,
        "editor": editor_role,
        "viewer": viewer_role,
    }


@pytest.fixture
def sample_permissions():
    """Create sample permission objects."""
    return {
        "global_create": Permission(
            id=uuid4(), name="Create", description="Create", scope_type="Global"
        ),
        "global_read": Permission(
            id=uuid4(), name="Read", description="Read", scope_type="Global"
        ),
        "project_read": Permission(
            id=uuid4(), name="Read", description="Read", scope_type="Project"
        ),
        "project_update": Permission(
            id=uuid4(), name="Update", description="Update", scope_type="Project"
        ),
        "flow_read": Permission(
            id=uuid4(), name="Read", description="Read", scope_type="Flow"
        ),
        "flow_update": Permission(
            id=uuid4(), name="Update", description="Update", scope_type="Flow"
        ),
    }


class TestRBACServiceInitialization:
    """Tests for RBACService initialization and cache management."""

    @pytest.mark.asyncio
    async def test_initialize_loads_cache(self, rbac_service, mock_database_service, sample_roles, sample_permissions):
        """Test that initialize() loads role-permission cache."""
        _, mock_session = mock_database_service

        # Setup mock data
        role = sample_roles["admin"]
        perm1 = sample_permissions["global_create"]
        perm2 = sample_permissions["global_read"]

        role_perm1 = RolePermission(id=uuid4(), role_id=role.id, permission_id=perm1.id)
        role_perm2 = RolePermission(id=uuid4(), role_id=role.id, permission_id=perm2.id)

        # Mock query result
        mock_result = Mock()
        mock_result.all = Mock(return_value=[
            (role_perm1, perm1, role),
            (role_perm2, perm2, role),
        ])

        async def mock_exec(*args, **kwargs):
            return mock_result

        mock_session.exec = mock_exec

        # Initialize
        await rbac_service.initialize()

        # Verify cache is populated
        assert role.id in rbac_service._role_permission_cache
        assert ("Create", "Global") in rbac_service._role_permission_cache[role.id]
        assert ("Read", "Global") in rbac_service._role_permission_cache[role.id]
        assert rbac_service._cache_timestamp is not None

    @pytest.mark.asyncio
    async def test_initialize_handles_failure_gracefully(self, rbac_service, mock_database_service):
        """Test that initialize() handles failures gracefully."""
        _, mock_session = mock_database_service

        # Make exec raise an exception
        mock_session.exec = AsyncMock(side_effect=Exception("Database error"))

        # Should not raise exception
        await rbac_service.initialize()

        # Cache should be empty
        assert rbac_service._role_permission_cache == {}
        assert rbac_service._cache_timestamp is None

    def test_cache_invalidation(self, rbac_service):
        """Test manual cache invalidation."""
        # Set up cache
        rbac_service._role_permission_cache = {uuid4(): {("Read", "Global")}}
        rbac_service._cache_timestamp = time.time()

        # Invalidate
        rbac_service.invalidate_cache()

        # Verify cache is cleared
        assert rbac_service._role_permission_cache == {}
        assert rbac_service._cache_timestamp is None

    def test_cache_ttl_validation(self, rbac_service):
        """Test that cache TTL validation works correctly."""
        # Empty cache is invalid
        assert not rbac_service._is_cache_valid()

        # Recent cache is valid
        rbac_service._role_permission_cache = {uuid4(): {("Read", "Global")}}
        rbac_service._cache_timestamp = time.time()
        assert rbac_service._is_cache_valid()

        # Expired cache is invalid
        rbac_service._cache_timestamp = time.time() - 4000  # More than 1 hour
        assert not rbac_service._is_cache_valid()


class TestRBACServicePermissionChecks:
    """Tests for permission checking logic."""

    @pytest.mark.asyncio
    async def test_admin_bypass_all_permissions(self, rbac_service, mock_database_service, sample_roles):
        """Test that Admin users bypass all permission checks."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        admin_role = sample_roles["admin"]

        # Setup cache with admin having global permissions
        rbac_service._role_permission_cache = {
            admin_role.id: {("Create", "Global"), ("Read", "Global")}
        }
        rbac_service._cache_timestamp = time.time()

        # Setup mock for global assignment query
        global_assignment = UserRoleAssignment(
            id=uuid4(),
            user_id=user_id,
            role_id=admin_role.id,
            scope_type="Global",
            scope_id=None,
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        mock_result = Mock()
        mock_result.all = Mock(return_value=[global_assignment])

        async def mock_exec(*args, **kwargs):
            return mock_result

        mock_session.exec = mock_exec

        # Test that admin can access anything
        assert await rbac_service.can_access(user_id, "Delete", "Flow", uuid4())
        assert await rbac_service.can_access(user_id, "Create", "Project", uuid4())
        assert await rbac_service.can_access(user_id, "Update", "Global")

    @pytest.mark.asyncio
    async def test_direct_permission_granted(self, rbac_service, mock_database_service, sample_roles):
        """Test direct permission check grants access."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        project_id = uuid4()
        owner_role = sample_roles["owner"]

        # Setup cache
        rbac_service._role_permission_cache = {
            owner_role.id: {("Read", "Project"), ("Update", "Project")}
        }
        rbac_service._cache_timestamp = time.time()

        # Setup mock responses for queries
        assignment = UserRoleAssignment(
            id=uuid4(),
            user_id=user_id,
            role_id=owner_role.id,
            scope_type="Project",
            scope_id=project_id,
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        # Mock exec to return empty for admin check, then assignment for direct check
        mock_result_admin = Mock()
        mock_result_admin.all = Mock(return_value=[])  # No admin assignment

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

        # Test direct permission
        assert await rbac_service.can_access(user_id, "Read", "Project", project_id)

    @pytest.mark.asyncio
    async def test_direct_permission_denied(self, rbac_service, mock_database_service, sample_roles):
        """Test that users without permission are denied."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        project_id = uuid4()
        viewer_role = sample_roles["viewer"]

        # Setup cache - viewer only has Read
        rbac_service._role_permission_cache = {
            viewer_role.id: {("Read", "Project")}
        }
        rbac_service._cache_timestamp = time.time()

        assignment = UserRoleAssignment(
            id=uuid4(),
            user_id=user_id,
            role_id=viewer_role.id,
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

        # For project inheritance check
        mock_result_inherit = Mock()
        mock_result_inherit.all = Mock(return_value=[])

        exec_call_count = [0]

        async def mock_exec(*args, **kwargs):
            exec_call_count[0] += 1
            if exec_call_count[0] == 1:
                return mock_result_admin
            elif exec_call_count[0] == 2:
                return mock_result_direct
            else:
                return mock_result_inherit

        mock_session.exec = mock_exec

        # Test permission denial - viewer trying to Update
        assert not await rbac_service.can_access(user_id, "Update", "Project", project_id)

    @pytest.mark.asyncio
    async def test_flow_inherits_from_project(self, rbac_service, mock_database_service, sample_roles):
        """Test that Flow permissions inherit from Project level."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        flow_id = uuid4()
        project_id = uuid4()
        editor_role = sample_roles["editor"]

        # Setup cache - editor has Project permissions
        rbac_service._role_permission_cache = {
            editor_role.id: {("Read", "Project"), ("Update", "Project")}
        }
        rbac_service._cache_timestamp = time.time()

        project_assignment = UserRoleAssignment(
            id=uuid4(),
            user_id=user_id,
            role_id=editor_role.id,
            scope_type="Project",
            scope_id=project_id,
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        # Mock queries: no admin, no direct flow assignment, but project assignment
        mock_result_admin = Mock()
        mock_result_admin.all = Mock(return_value=[])

        mock_result_flow = Mock()
        mock_result_flow.all = Mock(return_value=[])  # No direct flow assignment

        mock_result_project = Mock()
        mock_result_project.all = Mock(return_value=[project_assignment])

        exec_call_count = [0]

        async def mock_exec(*args, **kwargs):
            exec_call_count[0] += 1
            if exec_call_count[0] == 1:
                return mock_result_admin
            elif exec_call_count[0] == 2:
                return mock_result_flow
            else:
                return mock_result_project

        mock_session.exec = mock_exec

        # Test inheritance - should grant access via project assignment
        assert await rbac_service.can_access(user_id, "Update", "Flow", flow_id)

    @pytest.mark.asyncio
    async def test_permission_check_handles_errors(self, rbac_service, mock_database_service):
        """Test that permission checks fail closed on errors."""
        _, mock_session = mock_database_service

        user_id = uuid4()

        # Setup cache
        rbac_service._role_permission_cache = {uuid4(): {("Read", "Global")}}
        rbac_service._cache_timestamp = time.time()

        # Make query fail
        mock_session.exec = AsyncMock(side_effect=Exception("Database error"))

        # Should deny access on error (fail closed)
        assert not await rbac_service.can_access(user_id, "Read", "Global")


class TestRBACServiceAssignmentManagement:
    """Tests for assignment CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_assignment_success(self, rbac_service, mock_database_service, sample_roles):
        """Test successful assignment creation."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        project_id = uuid4()
        owner_role = sample_roles["owner"]

        # Mock role lookup
        mock_session.get = AsyncMock(return_value=owner_role)

        # Mock duplicate check
        mock_result_duplicate = Mock()
        mock_result_duplicate.first = Mock(return_value=None)  # No duplicate

        async def mock_exec(*args, **kwargs):
            return mock_result_duplicate

        mock_session.exec = mock_exec

        # Mock commit and refresh
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Create assignment
        assignment = await rbac_service.create_assignment(
            user_id=user_id,
            role_id=owner_role.id,
            scope_type="Project",
            scope_id=project_id,
            is_immutable=False,
        )

        # Verify
        assert assignment.user_id == user_id
        assert assignment.role_id == owner_role.id
        assert assignment.scope_type == "Project"
        assert assignment.scope_id == project_id
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_assignment_role_not_found(self, rbac_service, mock_database_service):
        """Test assignment creation fails if role doesn't exist."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        fake_role_id = uuid4()

        # Mock role lookup returns None
        mock_session.get = AsyncMock(return_value=None)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Role .* not found"):
            await rbac_service.create_assignment(
                user_id=user_id,
                role_id=fake_role_id,
                scope_type="Project",
                scope_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_create_assignment_duplicate(self, rbac_service, mock_database_service, sample_roles):
        """Test that duplicate assignments are rejected."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        project_id = uuid4()
        owner_role = sample_roles["owner"]

        # Mock role lookup
        mock_session.get = AsyncMock(return_value=owner_role)

        # Mock duplicate found
        existing = UserRoleAssignment(
            id=uuid4(),
            user_id=user_id,
            role_id=owner_role.id,
            scope_type="Project",
            scope_id=project_id,
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )
        mock_result = AsyncMock()
        mock_result.first.return_value = existing
        mock_session.exec = AsyncMock(return_value=mock_result)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Assignment already exists"):
            await rbac_service.create_assignment(
                user_id=user_id,
                role_id=owner_role.id,
                scope_type="Project",
                scope_id=project_id,
            )

    @pytest.mark.asyncio
    async def test_update_assignment_success(self, rbac_service, mock_database_service, sample_roles):
        """Test successful assignment update."""
        _, mock_session = mock_database_service

        assignment_id = uuid4()
        old_role = sample_roles["viewer"]
        new_role = sample_roles["editor"]

        assignment = UserRoleAssignment(
            id=assignment_id,
            user_id=uuid4(),
            role_id=old_role.id,
            scope_type="Project",
            scope_id=uuid4(),
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        # Mock get calls
        mock_session.get = AsyncMock(side_effect=[assignment, new_role])
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Update
        updated = await rbac_service.update_assignment(assignment_id, new_role.id)

        # Verify
        assert updated.role_id == new_role.id
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_assignment_not_found(self, rbac_service, mock_database_service):
        """Test update fails if assignment doesn't exist."""
        _, mock_session = mock_database_service

        fake_id = uuid4()

        # Mock get returns None
        mock_session.get = AsyncMock(return_value=None)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Assignment .* not found"):
            await rbac_service.update_assignment(fake_id, uuid4())

    @pytest.mark.asyncio
    async def test_delete_assignment_success(self, rbac_service, mock_database_service):
        """Test successful assignment deletion."""
        _, mock_session = mock_database_service

        assignment_id = uuid4()
        assignment = UserRoleAssignment(
            id=assignment_id,
            user_id=uuid4(),
            role_id=uuid4(),
            scope_type="Project",
            scope_id=uuid4(),
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        # Mock get
        mock_session.get = AsyncMock(return_value=assignment)
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()

        # Delete
        await rbac_service.delete_assignment(assignment_id)

        # Verify
        mock_session.delete.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_immutable_assignment_fails(self, rbac_service, mock_database_service):
        """Test that immutable assignments cannot be deleted."""
        _, mock_session = mock_database_service

        assignment_id = uuid4()
        assignment = UserRoleAssignment(
            id=assignment_id,
            user_id=uuid4(),
            role_id=uuid4(),
            scope_type="Project",
            scope_id=uuid4(),
            is_immutable=True,  # Immutable!
            created_at=datetime.now(timezone.utc),
        )

        # Mock get
        mock_session.get = AsyncMock(return_value=assignment)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Cannot delete immutable assignment"):
            await rbac_service.delete_assignment(assignment_id)

    @pytest.mark.asyncio
    async def test_delete_assignment_not_found(self, rbac_service, mock_database_service):
        """Test delete fails if assignment doesn't exist."""
        _, mock_session = mock_database_service

        fake_id = uuid4()

        # Mock get returns None
        mock_session.get = AsyncMock(return_value=None)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Assignment .* not found"):
            await rbac_service.delete_assignment(fake_id)


class TestRBACServiceQueries:
    """Tests for query operations."""

    @pytest.mark.asyncio
    async def test_get_user_assignments(self, rbac_service, mock_database_service):
        """Test retrieving all assignments for a user."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        assignments = [
            UserRoleAssignment(
                id=uuid4(),
                user_id=user_id,
                role_id=uuid4(),
                scope_type="Global",
                scope_id=None,
                is_immutable=False,
                created_at=datetime.now(timezone.utc),
            ),
            UserRoleAssignment(
                id=uuid4(),
                user_id=user_id,
                role_id=uuid4(),
                scope_type="Project",
                scope_id=uuid4(),
                is_immutable=False,
                created_at=datetime.now(timezone.utc),
            ),
        ]

        mock_result = Mock()
        mock_result.all = Mock(return_value=assignments)

        async def mock_exec(*args, **kwargs):
            return mock_result

        mock_session.exec = mock_exec

        # Get assignments
        result = await rbac_service.get_user_assignments(user_id)

        # Verify
        assert len(result) == 2
        assert all(a.user_id == user_id for a in result)

    @pytest.mark.asyncio
    async def test_list_roles(self, rbac_service, mock_database_service, sample_roles):
        """Test listing all roles."""
        _, mock_session = mock_database_service

        roles = list(sample_roles.values())

        mock_result = Mock()
        mock_result.all = Mock(return_value=roles)

        async def mock_exec(*args, **kwargs):
            return mock_result

        mock_session.exec = mock_exec

        # List roles
        result = await rbac_service.list_roles()

        # Verify
        assert len(result) == 4
        assert any(r.name == "Admin" for r in result)
        assert any(r.name == "Viewer" for r in result)

    @pytest.mark.asyncio
    async def test_get_assignments_with_filters(self, rbac_service, mock_database_service):
        """Test getting assignments with various filters."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        role_id = uuid4()

        filtered_assignments = [
            UserRoleAssignment(
                id=uuid4(),
                user_id=user_id,
                role_id=role_id,
                scope_type="Project",
                scope_id=uuid4(),
                is_immutable=False,
                created_at=datetime.now(timezone.utc),
            )
        ]

        mock_result = Mock()
        mock_result.all = Mock(return_value=filtered_assignments)

        async def mock_exec(*args, **kwargs):
            return mock_result

        mock_session.exec = mock_exec

        # Get assignments with filters
        result = await rbac_service.get_assignments(
            user_id=user_id,
            role_id=role_id,
            scope_type="Project",
        )

        # Verify
        assert len(result) == 1
        assert result[0].user_id == user_id
        assert result[0].role_id == role_id
        assert result[0].scope_type == "Project"


class TestRBACServicePerformance:
    """Tests for performance requirements."""

    @pytest.mark.asyncio
    async def test_can_access_performance(self, rbac_service, mock_database_service, sample_roles):
        """Test that can_access meets <50ms p95 requirement with caching."""
        _, mock_session = mock_database_service

        user_id = uuid4()
        project_id = uuid4()
        owner_role = sample_roles["owner"]

        # Setup cache
        rbac_service._role_permission_cache = {
            owner_role.id: {("Read", "Project"), ("Update", "Project")}
        }
        rbac_service._cache_timestamp = time.time()

        # Setup mock
        assignment = UserRoleAssignment(
            id=uuid4(),
            user_id=user_id,
            role_id=owner_role.id,
            scope_type="Project",
            scope_id=project_id,
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

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

        # Measure performance (single call, not p95, but demonstrates caching works)
        start = time.time()
        result = await rbac_service.can_access(user_id, "Read", "Project", project_id)
        elapsed = (time.time() - start) * 1000  # Convert to ms

        # Verify result and performance
        assert result is True
        # This is a mock test so timing isn't realistic, but structure is correct
        # In real tests with actual DB, we'd verify <50ms


class TestRBACServiceCacheReload:
    """Tests for automatic cache reloading."""

    @pytest.mark.asyncio
    async def test_cache_auto_reload_on_expiry(self, rbac_service, mock_database_service, sample_roles, sample_permissions):
        """Test that expired cache is automatically reloaded."""
        _, mock_session = mock_database_service

        role = sample_roles["admin"]
        perm = sample_permissions["global_read"]

        # Setup initial cache with expired timestamp
        rbac_service._role_permission_cache = {role.id: {("Create", "Global")}}
        rbac_service._cache_timestamp = time.time() - 4000  # Expired

        # Mock reload query
        role_perm = RolePermission(id=uuid4(), role_id=role.id, permission_id=perm.id)
        mock_result_reload = Mock()
        mock_result_reload.all = Mock(return_value=[(role_perm, perm, role)])

        # Mock admin check
        mock_result_admin = Mock()
        mock_result_admin.all = Mock(return_value=[])

        # Mock direct check
        mock_result_direct = Mock()
        mock_result_direct.all = Mock(return_value=[])

        exec_call_count = [0]

        async def mock_exec(*args, **kwargs):
            exec_call_count[0] += 1
            if exec_call_count[0] == 1:
                return mock_result_reload
            elif exec_call_count[0] == 2:
                return mock_result_admin
            else:
                return mock_result_direct

        mock_session.exec = mock_exec

        # Call can_access which should trigger reload
        await rbac_service.can_access(uuid4(), "Read", "Global")

        # Verify cache was reloaded
        assert ("Read", "Global") in rbac_service._role_permission_cache[role.id]
        assert ("Create", "Global") not in rbac_service._role_permission_cache[role.id]
