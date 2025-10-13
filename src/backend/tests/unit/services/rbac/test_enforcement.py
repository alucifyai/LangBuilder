"""Unit tests for RBAC enforcement engine."""

from datetime import datetime, timedelta, timezone
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
        name="Test Workspace",
        slug="test-workspace",
        description="Test workspace for RBAC tests",
    )
    async_session.add(workspace)
    await async_session.commit()
    await async_session.refresh(workspace)
    return workspace


@pytest.fixture
async def user(async_session):
    """Create a test user."""
    user = User(
        username="testuser",
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
        name="Test Project",
        user_id=uuid4(),  # Placeholder user
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
        name="Test Flow",
        data={},
        folder_id=project.id,
        user_id=uuid4(),  # Placeholder user
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
        name="test_role",
        display_name="Test Role",
        description="Test role",
    )
    async_session.add(role)
    await async_session.commit()
    await async_session.refresh(role)

    # Add permission to role
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
    reset_permission_cache()  # Start with clean cache for each test
    return RBACEnforcementEngine(async_session)


class TestRBACEnforcementEngine:
    """Test suite for RBACEnforcementEngine class."""

    @pytest.mark.asyncio
    async def test_deny_by_default(self, enforcement_engine, user, flow):
        """Test deny-by-default: user with no assignments has no permissions."""
        has_perm = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        assert has_perm is False

    @pytest.mark.asyncio
    async def test_direct_user_assignment_grants_permission(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
        role,
    ):
        """Test user with direct role assignment has permission."""
        # Assign role to user at flow scope
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # User should now have permission
        has_perm = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        assert has_perm is True

    @pytest.mark.asyncio
    async def test_permission_inheritance_from_workspace(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
        workspace,
        role,
    ):
        """Test permission inheritance: workspace grant applies to flow."""
        # Assign role to user at workspace scope
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="workspace",
            scope_id=workspace.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # User should have permission on flow (inherits from workspace)
        has_perm = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        assert has_perm is True

    @pytest.mark.asyncio
    async def test_permission_inheritance_from_project(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
        project,
        role,
    ):
        """Test permission inheritance: project grant applies to flow."""
        # Assign role to user at project scope
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="project",
            scope_id=project.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # User should have permission on flow
        has_perm = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        assert has_perm is True

    @pytest.mark.asyncio
    async def test_group_role_assignment(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
        workspace,
        role,
    ):
        """Test user gets permissions through group membership."""
        # Create a user group
        group = UserGroup(
            workspace_id=workspace.id,
            name="test_group",
            description="Test group",
        )
        async_session.add(group)
        await async_session.commit()
        await async_session.refresh(group)

        # Add user to group
        membership = UserGroupMember(
            group_id=group.id,
            user_id=user.id,
            is_active=True,
        )
        async_session.add(membership)
        await async_session.commit()

        # Assign role to group at workspace scope
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="group",
            group_id=group.id,
            scope_type="workspace",
            scope_id=workspace.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # User should have permission through group membership
        has_perm = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        assert has_perm is True

    @pytest.mark.asyncio
    async def test_inactive_group_membership_no_permission(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
        workspace,
        role,
    ):
        """Test inactive group membership doesn't grant permissions."""
        # Create group and add inactive membership
        group = UserGroup(
            workspace_id=workspace.id,
            name="test_group",
            description="Test group",
        )
        async_session.add(group)
        await async_session.commit()
        await async_session.refresh(group)

        membership = UserGroupMember(
            group_id=group.id,
            user_id=user.id,
            is_active=False,  # Inactive
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

        # User should NOT have permission (inactive membership)
        has_perm = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        assert has_perm is False

    @pytest.mark.asyncio
    async def test_expired_assignment_no_permission(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
        role,
    ):
        """Test expired role assignment doesn't grant permissions."""
        # Create expired assignment
        expired_time = datetime.now(timezone.utc) - timedelta(days=1)
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
            expires_at=expired_time,
        )
        async_session.add(assignment)
        await async_session.commit()

        # User should NOT have permission (expired assignment)
        has_perm = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        assert has_perm is False

    @pytest.mark.asyncio
    async def test_inactive_assignment_no_permission(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
        role,
    ):
        """Test inactive role assignment doesn't grant permissions."""
        # Create inactive assignment
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
            is_active=False,
        )
        async_session.add(assignment)
        await async_session.commit()

        # User should NOT have permission
        has_perm = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        assert has_perm is False

    @pytest.mark.asyncio
    async def test_caching_works(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
        role,
    ):
        """Test permission results are cached."""
        # Assign role
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # First call - should hit database
        has_perm1 = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Second call - should hit cache
        has_perm2 = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        assert has_perm1 is True
        assert has_perm2 is True

        # Verify cache has entry
        cached_result = await enforcement_engine.cache.get(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )
        assert cached_result is True

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_user_change(
        self,
        enforcement_engine,
        user,
        flow,
    ):
        """Test cache invalidation when user permissions change."""
        # Check permission (should be False and cached)
        has_perm1 = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )
        assert has_perm1 is False

        # Invalidate user cache
        await enforcement_engine.invalidate_user_cache(user.id)

        # Verify cache is cleared
        cached_result = await enforcement_engine.cache.get(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )
        assert cached_result is None

    @pytest.mark.asyncio
    async def test_wildcard_permission_matching(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
    ):
        """Test wildcard permissions like 'flow.*' grant specific permissions."""
        # Create wildcard permission
        wildcard_perm = Permission(
            resource_type="flow",
            action="*",
            display_name="All Flow Actions",
            description="All flow permissions",
        )
        async_session.add(wildcard_perm)
        await async_session.commit()
        await async_session.refresh(wildcard_perm)

        # Create role with wildcard permission
        role = Role(
            name="flow_admin",
            display_name="Flow Admin",
        )
        async_session.add(role)
        await async_session.commit()
        await async_session.refresh(role)

        role_perm = RolePermission(
            role_id=role.id,
            permission_id=wildcard_perm.id,
        )
        async_session.add(role_perm)
        await async_session.commit()

        # Assign role to user
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # User should have any flow permission
        has_read = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )
        assert has_read is True

    @pytest.mark.asyncio
    async def test_get_user_permissions_for_resource(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
        permission,
        role,
    ):
        """Test getting all permissions user has on a resource."""
        # Assign role to user
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Get all permissions
        permissions = await enforcement_engine.get_user_permissions_for_resource(
            user_id=user.id,
            resource_type="flow",
            resource_id=flow.id,
        )

        assert "flow.read" in permissions

    @pytest.mark.asyncio
    async def test_check_resource_access_convenience_method(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
        role,
    ):
        """Test check_resource_access convenience method."""
        # Assign role
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Use convenience method
        can_read = await enforcement_engine.check_resource_access(
            user_id=user.id,
            action="read",
            resource_type="flow",
            resource_id=flow.id,
        )

        assert can_read is True

    @pytest.mark.asyncio
    async def test_closest_scope_wins_project_overrides_workspace(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
        project,
        workspace,
    ):
        """Test closest scope wins: project role overrides workspace role.

        This test explicitly verifies that when a user has conflicting roles at different
        scopes, the role at the closest (most specific) scope takes precedence.
        """
        # Create viewer role with only read permission
        read_perm = Permission(
            resource_type="flow",
            action="read",
            display_name="Read Flow",
            description="Permission to read flows",
        )
        async_session.add(read_perm)
        await async_session.commit()
        await async_session.refresh(read_perm)

        viewer_role = Role(
            name="viewer_role",
            display_name="Viewer",
            description="Read-only access",
        )
        async_session.add(viewer_role)
        await async_session.commit()
        await async_session.refresh(viewer_role)

        viewer_perm = RolePermission(
            role_id=viewer_role.id,
            permission_id=read_perm.id,
        )
        async_session.add(viewer_perm)
        await async_session.commit()

        # Create editor role with read and update permissions
        update_perm = Permission(
            resource_type="flow",
            action="update",
            display_name="Update Flow",
            description="Permission to update flows",
        )
        async_session.add(update_perm)
        await async_session.commit()
        await async_session.refresh(update_perm)

        editor_role = Role(
            name="editor_role",
            display_name="Editor",
            description="Read and write access",
        )
        async_session.add(editor_role)
        await async_session.commit()
        await async_session.refresh(editor_role)

        editor_read_perm = RolePermission(
            role_id=editor_role.id,
            permission_id=read_perm.id,
        )
        async_session.add(editor_read_perm)

        editor_update_perm = RolePermission(
            role_id=editor_role.id,
            permission_id=update_perm.id,
        )
        async_session.add(editor_update_perm)
        await async_session.commit()

        # Assign viewer role at workspace scope (broader)
        workspace_assignment = RoleAssignment(
            role_id=viewer_role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="workspace",
            scope_id=workspace.id,
        )
        async_session.add(workspace_assignment)

        # Assign editor role at project scope (closer/more specific)
        project_assignment = RoleAssignment(
            role_id=editor_role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="project",
            scope_id=project.id,
        )
        async_session.add(project_assignment)
        await async_session.commit()

        # User should have update permission from project editor role
        has_update = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.update",
            resource_type="flow",
            resource_id=flow.id,
        )
        assert has_update is True

        # User should also have read permission (from both roles, but project wins)
        has_read = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )
        assert has_read is True

    @pytest.mark.asyncio
    async def test_multiple_group_memberships_aggregate_permissions(
        self,
        enforcement_engine,
        async_session,
        user,
        flow,
        workspace,
    ):
        """Test user in multiple groups receives aggregated permissions.

        Verifies that when a user is a member of multiple groups, they receive
        the union of permissions from all group role assignments.
        """
        # Create read permission
        read_perm = Permission(
            resource_type="flow",
            action="read",
            display_name="Read Flow",
            description="Permission to read flows",
        )
        async_session.add(read_perm)
        await async_session.commit()
        await async_session.refresh(read_perm)

        # Create update permission
        update_perm = Permission(
            resource_type="flow",
            action="update",
            display_name="Update Flow",
            description="Permission to update flows",
        )
        async_session.add(update_perm)
        await async_session.commit()
        await async_session.refresh(update_perm)

        # Create reader role with only read permission
        reader_role = Role(
            name="reader_role",
            display_name="Reader",
            description="Read-only role",
        )
        async_session.add(reader_role)
        await async_session.commit()
        await async_session.refresh(reader_role)

        reader_perm = RolePermission(
            role_id=reader_role.id,
            permission_id=read_perm.id,
        )
        async_session.add(reader_perm)
        await async_session.commit()

        # Create updater role with only update permission
        updater_role = Role(
            name="updater_role",
            display_name="Updater",
            description="Update-only role",
        )
        async_session.add(updater_role)
        await async_session.commit()
        await async_session.refresh(updater_role)

        updater_perm = RolePermission(
            role_id=updater_role.id,
            permission_id=update_perm.id,
        )
        async_session.add(updater_perm)
        await async_session.commit()

        # Create Group A with reader role
        group_a = UserGroup(
            workspace_id=workspace.id,
            name="readers_group",
            description="Readers group",
        )
        async_session.add(group_a)
        await async_session.commit()
        await async_session.refresh(group_a)

        membership_a = UserGroupMember(
            group_id=group_a.id,
            user_id=user.id,
            is_active=True,
        )
        async_session.add(membership_a)
        await async_session.commit()

        group_a_assignment = RoleAssignment(
            role_id=reader_role.id,
            assignee_type="group",
            group_id=group_a.id,
            scope_type="workspace",
            scope_id=workspace.id,
        )
        async_session.add(group_a_assignment)
        await async_session.commit()

        # Create Group B with updater role
        group_b = UserGroup(
            workspace_id=workspace.id,
            name="updaters_group",
            description="Updaters group",
        )
        async_session.add(group_b)
        await async_session.commit()
        await async_session.refresh(group_b)

        membership_b = UserGroupMember(
            group_id=group_b.id,
            user_id=user.id,
            is_active=True,
        )
        async_session.add(membership_b)
        await async_session.commit()

        group_b_assignment = RoleAssignment(
            role_id=updater_role.id,
            assignee_type="group",
            group_id=group_b.id,
            scope_type="workspace",
            scope_id=workspace.id,
        )
        async_session.add(group_b_assignment)
        await async_session.commit()

        # User should have read permission from Group A
        has_read = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )
        assert has_read is True

        # User should have update permission from Group B
        has_update = await enforcement_engine.has_permission(
            user_id=user.id,
            permission="flow.update",
            resource_type="flow",
            resource_id=flow.id,
        )
        assert has_update is True

        # Verify permissions are aggregated correctly
        all_permissions = await enforcement_engine.get_user_permissions_for_resource(
            user_id=user.id,
            resource_type="flow",
            resource_id=flow.id,
        )
        assert "flow.read" in all_permissions
        assert "flow.update" in all_permissions
