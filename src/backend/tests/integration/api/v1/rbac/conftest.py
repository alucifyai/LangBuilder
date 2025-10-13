"""Shared fixtures for RBAC API integration tests.

This module provides common fixtures for testing RBAC API endpoints:
- Database setup and teardown
- Test users with various permissions
- Test roles, permissions, and workspaces
- Authentication headers
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from langflow.services.database.models.flow import Flow
from langflow.services.database.models.folder import Folder
from langflow.services.database.models.rbac import Permission, Role, RoleAssignment, RolePermission
from langflow.services.database.models.workspace import Workspace
from langflow.services.deps import get_db_service
from sqlmodel import select

# ============================================================================
# Workspace Fixtures
# ============================================================================


@pytest.fixture
async def test_workspace(client):
    """Create a test workspace for API integration tests."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        workspace = Workspace(
            name="Test Workspace API",
            slug=f"test-workspace-api-{uuid4().hex[:8]}",
            description="Workspace for API integration testing",
            is_active=True,
        )
        session.add(workspace)
        await session.commit()
        await session.refresh(workspace)

    yield workspace

    # Cleanup
    async with db_manager.with_session() as session:
        workspace_db = await session.get(Workspace, workspace.id)
        if workspace_db:
            await session.delete(workspace_db)
        await session.commit()


# ============================================================================
# Project (Folder) Fixtures
# ============================================================================


@pytest.fixture
async def test_project(client, test_workspace, active_super_user):
    """Create a test project (folder) for API integration tests."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        project = Folder(
            name="Test Project API",
            user_id=active_super_user.id,
            workspace_id=test_workspace.id,
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

    yield project

    # Cleanup
    async with db_manager.with_session() as session:
        project_db = await session.get(Folder, project.id)
        if project_db:
            await session.delete(project_db)
        await session.commit()


# ============================================================================
# Flow Fixtures
# ============================================================================


@pytest.fixture
async def test_flow(client, test_project, active_super_user):
    """Create a test flow for API integration tests."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        flow = Flow(
            name="Test Flow API",
            data={"nodes": [], "edges": []},
            folder_id=test_project.id,
            user_id=active_super_user.id,
        )
        session.add(flow)
        await session.commit()
        await session.refresh(flow)

    yield flow

    # Cleanup
    async with db_manager.with_session() as session:
        flow_db = await session.get(Flow, flow.id)
        if flow_db:
            await session.delete(flow_db)
        await session.commit()


# ============================================================================
# Permission Fixtures
# ============================================================================


@pytest.fixture
async def test_permissions(client):
    """Create test permissions in the database for API integration tests."""
    db_manager = get_db_service()
    permissions = []

    async with db_manager.with_session() as session:
        # Create test permissions
        perm_configs = [
            ("flow", "read", "Read Flow", "Allows reading flows"),
            ("flow", "update", "Update Flow", "Allows updating flows"),
            ("flow", "delete", "Delete Flow", "Allows deleting flows"),
            ("flow", "export", "Export Flow", "Allows exporting flows"),
        ]

        for resource_type, action, display_name, description in perm_configs:
            # Check if permission already exists
            stmt = select(Permission).where(
                Permission.resource_type == resource_type,
                Permission.action == action,
            )
            result = await session.exec(stmt)
            perm = result.first()

            if not perm:
                perm = Permission(
                    name=f"{resource_type}.{action}",
                    resource_type=resource_type,
                    action=action,
                    display_name=display_name,
                    description=description,
                    scope_level="FLOW",
                    is_active=True,
                    is_system_permission=True,
                )
                session.add(perm)

        await session.commit()

        # Re-fetch all permissions
        for resource_type, action, _, _ in perm_configs:
            stmt = select(Permission).where(
                Permission.resource_type == resource_type,
                Permission.action == action,
            )
            result = await session.exec(stmt)
            perm = result.first()
            if perm:
                await session.refresh(perm)
                permissions.append(perm)

    yield permissions

    # Cleanup
    async with db_manager.with_session() as session:
        for perm in permissions:
            perm_db = await session.get(Permission, perm.id)
            if perm_db:
                await session.delete(perm_db)
        await session.commit()


# ============================================================================
# Role Fixtures
# ============================================================================


@pytest.fixture
async def test_role_viewer(client, test_permissions):
    """Create a viewer role with read permission."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        role = Role(
            name=f"api_viewer_{uuid4().hex[:8]}",
            display_name="API Test Viewer",
            description="Test viewer role for API integration tests",
            is_system_role=False,
            is_active=True,
        )
        session.add(role)
        await session.flush()

        # Add read permission to role
        read_perm = test_permissions[0]  # flow.read
        role_perm = RolePermission(role_id=role.id, permission_id=read_perm.id)
        session.add(role_perm)

        await session.commit()
        await session.refresh(role)

    yield role

    # Cleanup
    async with db_manager.with_session() as session:
        role_db = await session.get(Role, role.id)
        if role_db:
            await session.delete(role_db)
        await session.commit()


@pytest.fixture
async def test_role_editor(client, test_permissions):
    """Create an editor role with read and update permissions."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        role = Role(
            name=f"api_editor_{uuid4().hex[:8]}",
            display_name="API Test Editor",
            description="Test editor role for API integration tests",
            is_system_role=False,
            is_active=True,
        )
        session.add(role)
        await session.flush()

        # Add read and update permissions to role
        for perm in test_permissions[:2]:  # flow.read, flow.update
            role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
            session.add(role_perm)

        await session.commit()
        await session.refresh(role)

    yield role

    # Cleanup
    async with db_manager.with_session() as session:
        role_db = await session.get(Role, role.id)
        if role_db:
            await session.delete(role_db)
        await session.commit()


# ============================================================================
# Helper Functions
# ============================================================================


async def create_role_assignment(
    session,
    user_id: UUID,
    role_id: UUID,
    scope_type: str,
    scope_id: UUID,
    expires_at: datetime | None = None,
    is_active: bool = True,
) -> RoleAssignment:
    """Helper function to create a role assignment."""
    assignment = RoleAssignment(
        role_id=role_id,
        assignee_type="user",
        user_id=user_id,
        scope_type=scope_type,
        scope_id=scope_id,
        expires_at=expires_at,
        is_active=is_active,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)
    return assignment
