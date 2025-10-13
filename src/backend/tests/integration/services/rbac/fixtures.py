"""Reusable test fixtures for RBAC integration tests.

Provides helper functions and pytest fixtures for creating test data:
- Users, workspaces, projects, flows
- Roles, permissions, and role assignments
- Test scenarios for PRD acceptance criteria
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from langflow.services.database.models.flow import Flow
from langflow.services.database.models.folder import Folder
from langflow.services.database.models.rbac import Permission, Role, RoleAssignment, RolePermission
from langflow.services.database.models.user import User
from langflow.services.database.models.user_group import UserGroup, UserGroupMember
from langflow.services.database.models.workspace import Workspace
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

# ============================================================================
# Workspace Fixtures
# ============================================================================


@pytest.fixture
async def test_workspace(async_session: AsyncSession) -> Workspace:
    """Create a test workspace."""
    workspace = Workspace(
        name="Test Workspace",
        slug="test-workspace",
        description="Workspace for integration tests",
    )
    async_session.add(workspace)
    await async_session.commit()
    await async_session.refresh(workspace)
    return workspace


# ============================================================================
# User Fixtures
# ============================================================================


@pytest.fixture
async def test_user_jo(async_session: AsyncSession) -> User:
    """Create test user 'Jo'."""
    user = User(
        username=f"jo_{uuid4().hex[:8]}@test.com",
        password="hashed_password",
        is_active=True,
        is_superuser=False,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def test_user_mia(async_session: AsyncSession) -> User:
    """Create test user 'Mia'."""
    user = User(
        username=f"mia_{uuid4().hex[:8]}@test.com",
        password="hashed_password",
        is_active=True,
        is_superuser=False,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def test_user_lee(async_session: AsyncSession) -> User:
    """Create test user 'Lee'."""
    user = User(
        username=f"lee_{uuid4().hex[:8]}@test.com",
        password="hashed_password",
        is_active=True,
        is_superuser=False,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def test_user_kai(async_session: AsyncSession) -> User:
    """Create test user 'Kai' (typically used for deny-by-default tests)."""
    user = User(
        username=f"kai_{uuid4().hex[:8]}@test.com",
        password="hashed_password",
        is_active=True,
        is_superuser=False,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


# ============================================================================
# Project (Folder) Fixtures
# ============================================================================


@pytest.fixture
async def test_project(async_session: AsyncSession, test_workspace: Workspace) -> Folder:
    """Create a test project (folder)."""
    project = Folder(
        name="Test Project",
        user_id=uuid4(),
        workspace_id=test_workspace.id,
    )
    async_session.add(project)
    await async_session.commit()
    await async_session.refresh(project)
    return project


# ============================================================================
# Flow Fixtures
# ============================================================================


@pytest.fixture
async def test_flow(async_session: AsyncSession, test_project: Folder) -> Flow:
    """Create a test flow."""
    flow = Flow(
        name="Test Flow",
        data={"nodes": [], "edges": []},
        folder_id=test_project.id,
        user_id=uuid4(),
    )
    async_session.add(flow)
    await async_session.commit()
    await async_session.refresh(flow)
    return flow


# ============================================================================
# Permission Fixtures
# ============================================================================


@pytest.fixture
async def permission_flow_read(async_session: AsyncSession) -> Permission:
    """Get or create flow.read permission."""
    stmt = select(Permission).where(
        Permission.resource_type == "flow",
        Permission.action == "read",
    )
    result = await async_session.exec(stmt)
    permission = result.first()

    if not permission:
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
async def permission_flow_update(async_session: AsyncSession) -> Permission:
    """Get or create flow.update permission."""
    stmt = select(Permission).where(
        Permission.resource_type == "flow",
        Permission.action == "update",
    )
    result = await async_session.exec(stmt)
    permission = result.first()

    if not permission:
        permission = Permission(
            resource_type="flow",
            action="update",
            display_name="Update Flow",
            description="Permission to update flows",
        )
        async_session.add(permission)
        await async_session.commit()
        await async_session.refresh(permission)

    return permission


@pytest.fixture
async def permission_flow_export(async_session: AsyncSession) -> Permission:
    """Get or create flow.export permission."""
    stmt = select(Permission).where(
        Permission.resource_type == "flow",
        Permission.action == "export",
    )
    result = await async_session.exec(stmt)
    permission = result.first()

    if not permission:
        permission = Permission(
            resource_type="flow",
            action="export",
            display_name="Export Flow",
            description="Permission to export flows",
        )
        async_session.add(permission)
        await async_session.commit()
        await async_session.refresh(permission)

    return permission


# ============================================================================
# Role Fixtures
# ============================================================================


@pytest.fixture
async def role_viewer(async_session: AsyncSession, permission_flow_read: Permission) -> Role:
    """Create or get viewer role (flow.read only)."""
    stmt = select(Role).where(Role.name == "viewer")
    result = await async_session.exec(stmt)
    role = result.first()

    if not role:
        role = Role(
            name="viewer",
            display_name="Viewer",
            description="Can read flows",
        )
        async_session.add(role)
        await async_session.commit()
        await async_session.refresh(role)

        # Link permission
        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission_flow_read.id,
        )
        async_session.add(role_permission)
        await async_session.commit()

    return role


@pytest.fixture
async def role_editor(
    async_session: AsyncSession,
    permission_flow_read: Permission,
    permission_flow_update: Permission,
) -> Role:
    """Create or get editor role (flow.read + flow.update)."""
    stmt = select(Role).where(Role.name == "editor")
    result = await async_session.exec(stmt)
    role = result.first()

    if not role:
        role = Role(
            name="editor",
            display_name="Editor",
            description="Can read and update flows",
        )
        async_session.add(role)
        await async_session.commit()
        await async_session.refresh(role)

        # Link permissions
        for permission in [permission_flow_read, permission_flow_update]:
            role_permission = RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )
            async_session.add(role_permission)
        await async_session.commit()

    return role


@pytest.fixture
async def role_exporter(async_session: AsyncSession, permission_flow_export: Permission) -> Role:
    """Create or get exporter role (flow.export only)."""
    stmt = select(Role).where(Role.name == "exporter")
    result = await async_session.exec(stmt)
    role = result.first()

    if not role:
        role = Role(
            name="exporter",
            display_name="Exporter",
            description="Can export flows",
        )
        async_session.add(role)
        await async_session.commit()
        await async_session.refresh(role)

        # Link permission
        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission_flow_export.id,
        )
        async_session.add(role_permission)
        await async_session.commit()

    return role


# ============================================================================
# Helper Functions
# ============================================================================


async def create_user(async_session: AsyncSession, username: str) -> User:
    """Helper to create a user."""
    user = User(
        username=f"{username}_{uuid4().hex[:8]}@test.com",
        password="hashed_password",
        is_active=True,
        is_superuser=False,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


async def create_workspace(async_session: AsyncSession, name: str, slug: str | None = None) -> Workspace:
    """Helper to create a workspace."""
    if not slug:
        slug = name.lower().replace(" ", "-")

    workspace = Workspace(
        name=name,
        slug=slug,
        description=f"Test workspace: {name}",
    )
    async_session.add(workspace)
    await async_session.commit()
    await async_session.refresh(workspace)
    return workspace


async def create_project(
    async_session: AsyncSession,
    name: str,
    workspace_id: UUID,
    user_id: UUID | None = None,
) -> Folder:
    """Helper to create a project (folder)."""
    if not user_id:
        user_id = uuid4()

    project = Folder(
        name=name,
        user_id=user_id,
        workspace_id=workspace_id,
    )
    async_session.add(project)
    await async_session.commit()
    await async_session.refresh(project)
    return project


async def create_flow(
    async_session: AsyncSession,
    name: str,
    project_id: UUID,
    user_id: UUID | None = None,
) -> Flow:
    """Helper to create a flow."""
    if not user_id:
        user_id = uuid4()

    flow = Flow(
        name=name,
        data={"nodes": [], "edges": []},
        folder_id=project_id,
        user_id=user_id,
    )
    async_session.add(flow)
    await async_session.commit()
    await async_session.refresh(flow)
    return flow


async def create_permission(
    async_session: AsyncSession,
    resource_type: str,
    action: str,
    display_name: str | None = None,
) -> Permission:
    """Helper to create a permission."""
    # Check if permission already exists
    stmt = select(Permission).where(
        Permission.resource_type == resource_type,
        Permission.action == action,
    )
    result = await async_session.exec(stmt)
    existing = result.first()
    if existing:
        return existing

    if not display_name:
        display_name = f"{action.title()} {resource_type.title()}"

    permission = Permission(
        resource_type=resource_type,
        action=action,
        display_name=display_name,
        description=f"Permission to {action} {resource_type}",
    )
    async_session.add(permission)
    await async_session.commit()
    await async_session.refresh(permission)
    return permission


async def create_role(
    async_session: AsyncSession,
    name: str,
    permissions: list[str],
    display_name: str | None = None,
) -> Role:
    """Helper to create a role with permissions.

    Args:
        async_session: Database session
        name: Role name (e.g., "editor")
        permissions: List of permission strings (e.g., ["flow.read", "flow.update"])
        display_name: Optional display name

    Returns:
        Created role with permissions linked
    """
    # Check if role already exists
    stmt = select(Role).where(Role.name == name)
    result = await async_session.exec(stmt)
    existing_role = result.first()
    if existing_role:
        return existing_role

    if not display_name:
        display_name = name.title()

    role = Role(
        name=name,
        display_name=display_name,
        description=f"Test role: {name}",
    )
    async_session.add(role)
    await async_session.commit()
    await async_session.refresh(role)

    # Link permissions
    for perm_str in permissions:
        resource_type, action = perm_str.split(".")
        permission = await create_permission(async_session, resource_type, action)

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
        )
        async_session.add(role_permission)

    await async_session.commit()
    return role


async def assign_role(
    async_session: AsyncSession,
    user: User,
    role: Role,
    scope_type: str,
    scope_id: UUID,
    expires_at: datetime | None = None,
    is_active: bool = True,
) -> RoleAssignment:
    """Helper to assign a role to a user.

    Args:
        async_session: Database session
        user: User to assign role to
        role: Role to assign
        scope_type: Scope type (e.g., "workspace", "project", "flow")
        scope_id: ID of the scoped resource
        expires_at: Optional expiration time
        is_active: Whether assignment is active

    Returns:
        Created role assignment
    """
    assignment = RoleAssignment(
        role_id=role.id,
        assignee_type="user",
        user_id=user.id,
        scope_type=scope_type,
        scope_id=scope_id,
        expires_at=expires_at,
        is_active=is_active,
    )
    async_session.add(assignment)
    await async_session.commit()
    await async_session.refresh(assignment)
    return assignment


async def create_user_group(
    async_session: AsyncSession,
    workspace: Workspace,
    name: str,
    members: list[User] | None = None,
) -> UserGroup:
    """Helper to create a user group with members.

    Args:
        async_session: Database session
        workspace: Workspace the group belongs to
        name: Group name
        members: Optional list of users to add as members

    Returns:
        Created user group
    """
    group = UserGroup(
        workspace_id=workspace.id,
        name=name,
        description=f"Test group: {name}",
    )
    async_session.add(group)
    await async_session.commit()
    await async_session.refresh(group)

    # Add members if provided
    if members:
        for user in members:
            membership = UserGroupMember(
                group_id=group.id,
                user_id=user.id,
                is_active=True,
            )
            async_session.add(membership)
        await async_session.commit()

    return group


async def create_expired_role_assignment(
    async_session: AsyncSession,
    user: User,
    role: Role,
    scope_type: str,
    scope_id: UUID,
) -> RoleAssignment:
    """Helper to create an expired role assignment (for testing expiration)."""
    expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
    return await assign_role(
        async_session,
        user,
        role,
        scope_type,
        scope_id,
        expires_at=expired_time,
        is_active=True,
    )


async def create_inactive_role_assignment(
    async_session: AsyncSession,
    user: User,
    role: Role,
    scope_type: str,
    scope_id: UUID,
) -> RoleAssignment:
    """Helper to create an inactive role assignment (for testing active flag)."""
    return await assign_role(
        async_session,
        user,
        role,
        scope_type,
        scope_id,
        is_active=False,
    )
