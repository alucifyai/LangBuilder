"""Unit tests for Token Scope Enforcement (PRD Story 4.2).

Tests Task 4.4 - Token Scope Enforcement on API Key Authentication.

Tests the following token scope enforcement features:
- Workspace-scoped tokens: Access to all resources in workspace
- Project-scoped tokens: Access to project and its flows
- Flow-scoped tokens: Access to specific flow only
- Unscoped tokens: Full access (backward compatibility)
- Scope violation detection and denial

Each scope type is tested for:
1. Valid access within scope (allowed)
2. Invalid access outside scope (denied)
3. Scope hierarchy traversal (resource resolution)
4. Edge cases (nonexistent resources, invalid scope types)
"""

from uuid import uuid4

import pytest
from fastapi import HTTPException, Request
from langflow.services.database.models.flow import Flow
from langflow.services.database.models.folder import Folder
from langflow.services.database.models.workspace.model import Workspace
from langflow.services.deps import get_db_service
from langflow.services.rbac.token_scope import (
    attach_api_key_scope_to_request,
    get_resource_project_id,
    get_resource_workspace_id,
    validate_token_scope,
)
from starlette.datastructures import State

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_workspace(client, active_user) -> Workspace:
    """Create a test workspace."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        workspace = Workspace(
            name="Token Scope Test Workspace",
            slug="token-scope-test-workspace",
            description="Workspace for token scope testing",
            created_by=active_user.id,
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


@pytest.fixture
async def test_project(client, test_workspace: Workspace) -> Folder:
    """Create a test project in workspace."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        project = Folder(
            name="Token Scope Test Project",
            description="Project for token scope testing",
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


@pytest.fixture
async def test_flow(client, test_project: Folder) -> Flow:
    """Create a test flow in project."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        flow = Flow(
            name="Token Scope Test Flow",
            description="Flow for token scope testing",
            folder_id=test_project.id,
            data={},
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


@pytest.fixture
def mock_request() -> Request:
    """Create a mock FastAPI request with state."""
    request = Request(scope={"type": "http", "method": "GET", "path": "/", "query_string": b""})
    request._state = State()
    return request


# ============================================================================
# UNSCOPED TOKEN Tests
# ============================================================================


@pytest.mark.asyncio
async def test_unscoped_token_allows_all_access(
    client,
    mock_request: Request,
    test_flow: Flow,
):
    """Test that unscoped tokens (backward compatibility) allow access to any resource."""
    db_manager = get_db_service()

    # Mock unscoped API key (no scope_type or scope_id)
    attach_api_key_scope_to_request(
        request=mock_request,
        workspace_id=None,
        scope_type=None,
        scope_id=None,
        scoped_permissions=None,
    )

    async with db_manager.with_session() as session:
        # Should not raise - unscoped tokens have full access
        await validate_token_scope(
            request=mock_request,
            resource_type="flow",
            resource_id=test_flow.id,
            session=session,
        )


@pytest.mark.asyncio
async def test_no_scope_in_request_allows_access(
    client,
    mock_request: Request,
    test_flow: Flow,
):
    """Test that JWT auth (no API key scope) allows access."""
    db_manager = get_db_service()

    # No scope attached - JWT authentication
    # Don't call attach_api_key_scope_to_request

    async with db_manager.with_session() as session:
        # Should not raise - JWT auth bypasses scope checks
        await validate_token_scope(
            request=mock_request,
            resource_type="flow",
            resource_id=test_flow.id,
            session=session,
        )


# ============================================================================
# WORKSPACE-SCOPED TOKEN Tests
# ============================================================================


@pytest.mark.asyncio
async def test_workspace_scoped_token_allows_project_in_workspace(
    client,
    mock_request: Request,
    test_workspace: Workspace,
    test_project: Folder,
):
    """Test that workspace-scoped token can access projects in that workspace."""
    db_manager = get_db_service()

    # Mock workspace-scoped token
    attach_api_key_scope_to_request(
        request=mock_request,
        workspace_id=test_workspace.id,
        scope_type="workspace",
        scope_id=test_workspace.id,
        scoped_permissions=None,
    )

    async with db_manager.with_session() as session:
        # Should not raise - project is in scoped workspace
        await validate_token_scope(
            request=mock_request,
            resource_type="project",
            resource_id=test_project.id,
            session=session,
        )


@pytest.mark.asyncio
async def test_workspace_scoped_token_allows_flow_in_workspace(
    client,
    mock_request: Request,
    test_workspace: Workspace,
    test_flow: Flow,
):
    """Test that workspace-scoped token can access flows in workspace projects."""
    db_manager = get_db_service()

    # Mock workspace-scoped token
    attach_api_key_scope_to_request(
        request=mock_request,
        workspace_id=test_workspace.id,
        scope_type="workspace",
        scope_id=test_workspace.id,
        scoped_permissions=None,
    )

    async with db_manager.with_session() as session:
        # Should not raise - flow is in project in scoped workspace
        await validate_token_scope(
            request=mock_request,
            resource_type="flow",
            resource_id=test_flow.id,
            session=session,
        )


@pytest.mark.asyncio
async def test_workspace_scoped_token_denies_project_in_different_workspace(
    client,
    mock_request: Request,
    test_project: Folder,
):
    """Test that workspace-scoped token cannot access projects in different workspace."""
    db_manager = get_db_service()

    # Create a different workspace (not the one test_project belongs to)
    different_workspace_id = uuid4()

    # Mock workspace-scoped token for different workspace
    attach_api_key_scope_to_request(
        request=mock_request,
        workspace_id=different_workspace_id,
        scope_type="workspace",
        scope_id=different_workspace_id,
        scoped_permissions=None,
    )

    async with db_manager.with_session() as session:
        # Should raise 403 - project is in different workspace
        with pytest.raises(HTTPException) as exc_info:
            await validate_token_scope(
                request=mock_request,
                resource_type="project",
                resource_id=test_project.id,
                session=session,
            )

        assert exc_info.value.status_code == 403
        assert "workspace" in exc_info.value.detail.lower()


# ============================================================================
# PROJECT-SCOPED TOKEN Tests
# ============================================================================


@pytest.mark.asyncio
async def test_project_scoped_token_allows_project_access(
    client,
    mock_request: Request,
    test_project: Folder,
):
    """Test that project-scoped token can access the scoped project itself."""
    db_manager = get_db_service()

    # Mock project-scoped token
    attach_api_key_scope_to_request(
        request=mock_request,
        workspace_id=test_project.workspace_id,
        scope_type="project",
        scope_id=test_project.id,
        scoped_permissions=None,
    )

    async with db_manager.with_session() as session:
        # Should not raise - accessing the scoped project
        await validate_token_scope(
            request=mock_request,
            resource_type="project",
            resource_id=test_project.id,
            session=session,
        )


@pytest.mark.asyncio
async def test_project_scoped_token_allows_flow_in_project(
    client,
    mock_request: Request,
    test_project: Folder,
    test_flow: Flow,
):
    """Test that project-scoped token can access flows in that project."""
    db_manager = get_db_service()

    # Mock project-scoped token
    attach_api_key_scope_to_request(
        request=mock_request,
        workspace_id=test_project.workspace_id,
        scope_type="project",
        scope_id=test_project.id,
        scoped_permissions=None,
    )

    async with db_manager.with_session() as session:
        # Should not raise - flow is in scoped project
        await validate_token_scope(
            request=mock_request,
            resource_type="flow",
            resource_id=test_flow.id,
            session=session,
        )


@pytest.mark.asyncio
async def test_project_scoped_token_denies_different_project(
    client,
    mock_request: Request,
    test_project: Folder,
):
    """Test that project-scoped token cannot access different project."""
    db_manager = get_db_service()

    # Create a different project ID (not the one in scope)
    different_project_id = uuid4()

    # Mock project-scoped token
    attach_api_key_scope_to_request(
        request=mock_request,
        workspace_id=test_project.workspace_id,
        scope_type="project",
        scope_id=test_project.id,
        scoped_permissions=None,
    )

    async with db_manager.with_session() as session:
        # Should raise 403 - accessing different project
        with pytest.raises(HTTPException) as exc_info:
            await validate_token_scope(
                request=mock_request,
                resource_type="project",
                resource_id=different_project_id,
                session=session,
            )

        assert exc_info.value.status_code == 403
        assert "project" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_project_scoped_token_denies_flow_in_different_project(
    client,
    mock_request: Request,
    test_project: Folder,
    test_workspace: Workspace,
):
    """Test that project-scoped token cannot access flows in different project."""
    db_manager = get_db_service()

    # Create a different project and flow
    async with db_manager.with_session() as session:
        different_project = Folder(
            name="Different Project",
            workspace_id=test_workspace.id,
        )
        session.add(different_project)
        await session.flush()

        different_flow = Flow(
            name="Different Flow",
            folder_id=different_project.id,
            data={},
        )
        session.add(different_flow)
        await session.commit()
        await session.refresh(different_flow)

        different_flow_id = different_flow.id

        # Cleanup
        await session.delete(different_flow)
        await session.delete(different_project)
        await session.commit()

    # Mock project-scoped token (for test_project, not different_project)
    attach_api_key_scope_to_request(
        request=mock_request,
        workspace_id=test_project.workspace_id,
        scope_type="project",
        scope_id=test_project.id,
        scoped_permissions=None,
    )

    async with db_manager.with_session() as session:
        # Should raise 403 - flow is in different project
        with pytest.raises(HTTPException) as exc_info:
            await validate_token_scope(
                request=mock_request,
                resource_type="flow",
                resource_id=different_flow_id,
                session=session,
            )

        assert exc_info.value.status_code == 403
        assert "project" in exc_info.value.detail.lower()


# ============================================================================
# FLOW-SCOPED TOKEN Tests
# ============================================================================


@pytest.mark.asyncio
async def test_flow_scoped_token_allows_flow_access(
    client,
    mock_request: Request,
    test_flow: Flow,
):
    """Test that flow-scoped token can access the scoped flow."""
    db_manager = get_db_service()

    # Mock flow-scoped token
    attach_api_key_scope_to_request(
        request=mock_request,
        workspace_id=None,
        scope_type="flow",
        scope_id=test_flow.id,
        scoped_permissions=None,
    )

    async with db_manager.with_session() as session:
        # Should not raise - accessing the scoped flow
        await validate_token_scope(
            request=mock_request,
            resource_type="flow",
            resource_id=test_flow.id,
            session=session,
        )


@pytest.mark.asyncio
async def test_flow_scoped_token_denies_different_flow(
    client,
    mock_request: Request,
    test_flow: Flow,
):
    """Test that flow-scoped token cannot access different flow."""
    db_manager = get_db_service()

    # Create a different flow ID
    different_flow_id = uuid4()

    # Mock flow-scoped token
    attach_api_key_scope_to_request(
        request=mock_request,
        workspace_id=None,
        scope_type="flow",
        scope_id=test_flow.id,
        scoped_permissions=None,
    )

    async with db_manager.with_session() as session:
        # Should raise 403 - accessing different flow
        with pytest.raises(HTTPException) as exc_info:
            await validate_token_scope(
                request=mock_request,
                resource_type="flow",
                resource_id=different_flow_id,
                session=session,
            )

        assert exc_info.value.status_code == 403
        assert "flow" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_flow_scoped_token_denies_project_access(
    client,
    mock_request: Request,
    test_flow: Flow,
    test_project: Folder,
):
    """Test that flow-scoped token cannot access projects (only the specific flow)."""
    db_manager = get_db_service()

    # Mock flow-scoped token
    attach_api_key_scope_to_request(
        request=mock_request,
        workspace_id=None,
        scope_type="flow",
        scope_id=test_flow.id,
        scoped_permissions=None,
    )

    async with db_manager.with_session() as session:
        # Should raise 403 - flow tokens can only access the specific flow
        with pytest.raises(HTTPException) as exc_info:
            await validate_token_scope(
                request=mock_request,
                resource_type="project",
                resource_id=test_project.id,
                session=session,
            )

        assert exc_info.value.status_code == 403
        assert "flow" in exc_info.value.detail.lower()


# ============================================================================
# SCOPE RESOLUTION HELPER Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_resource_workspace_id_for_workspace(
    client,
    test_workspace: Workspace,
):
    """Test workspace ID resolution for workspace resource."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        workspace_id = await get_resource_workspace_id(
            session=session,
            resource_type="workspace",
            resource_id=test_workspace.id,
        )

        assert workspace_id == test_workspace.id


@pytest.mark.asyncio
async def test_get_resource_workspace_id_for_project(
    client,
    test_workspace: Workspace,
    test_project: Folder,
):
    """Test workspace ID resolution for project resource."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        workspace_id = await get_resource_workspace_id(
            session=session,
            resource_type="project",
            resource_id=test_project.id,
        )

        assert workspace_id == test_workspace.id


@pytest.mark.asyncio
async def test_get_resource_workspace_id_for_flow(
    client,
    test_workspace: Workspace,
    test_flow: Flow,
):
    """Test workspace ID resolution for flow resource (flow -> project -> workspace)."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        workspace_id = await get_resource_workspace_id(
            session=session,
            resource_type="flow",
            resource_id=test_flow.id,
        )

        assert workspace_id == test_workspace.id


@pytest.mark.asyncio
async def test_get_resource_project_id_for_project(
    client,
    test_project: Folder,
):
    """Test project ID resolution for project resource."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        project_id = await get_resource_project_id(
            session=session,
            resource_type="project",
            resource_id=test_project.id,
        )

        assert project_id == test_project.id


@pytest.mark.asyncio
async def test_get_resource_project_id_for_flow(
    client,
    test_project: Folder,
    test_flow: Flow,
):
    """Test project ID resolution for flow resource."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        project_id = await get_resource_project_id(
            session=session,
            resource_type="flow",
            resource_id=test_flow.id,
        )

        assert project_id == test_project.id


# ============================================================================
# EDGE CASE Tests
# ============================================================================


@pytest.mark.asyncio
async def test_invalid_scope_type_raises_403(
    client,
    mock_request: Request,
    test_flow: Flow,
):
    """Test that unknown scope type raises 403 for safety."""
    db_manager = get_db_service()

    # Mock token with invalid scope type
    attach_api_key_scope_to_request(
        request=mock_request,
        workspace_id=None,
        scope_type="invalid_scope_type",
        scope_id=uuid4(),
        scoped_permissions=None,
    )

    async with db_manager.with_session() as session:
        # Should raise 403 - unknown scope type
        with pytest.raises(HTTPException) as exc_info:
            await validate_token_scope(
                request=mock_request,
                resource_type="flow",
                resource_id=test_flow.id,
                session=session,
            )

        assert exc_info.value.status_code == 403
        assert "scope type" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_resource_workspace_id_unknown_type_returns_none():
    """Test that unknown resource type returns None for workspace resolution."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        workspace_id = await get_resource_workspace_id(
            session=session,
            resource_type="unknown_resource_type",
            resource_id=uuid4(),
        )

        assert workspace_id is None


@pytest.mark.asyncio
async def test_get_resource_project_id_unknown_type_returns_none():
    """Test that unknown resource type returns None for project resolution."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        project_id = await get_resource_project_id(
            session=session,
            resource_type="unknown_resource_type",
            resource_id=uuid4(),
        )

        assert project_id is None


@pytest.mark.asyncio
async def test_attach_api_key_scope_to_request_sets_state(
    mock_request: Request,
):
    """Test that attach_api_key_scope_to_request properly sets request.state."""
    workspace_id = uuid4()
    scope_id = uuid4()

    attach_api_key_scope_to_request(
        request=mock_request,
        workspace_id=workspace_id,
        scope_type="project",
        scope_id=scope_id,
        scoped_permissions={"flow.read": True},
    )

    # Verify state was set correctly
    assert hasattr(mock_request.state, "api_key_scope")
    assert mock_request.state.api_key_scope["workspace_id"] == workspace_id
    assert mock_request.state.api_key_scope["scope_type"] == "project"
    assert mock_request.state.api_key_scope["scope_id"] == scope_id
    assert mock_request.state.api_key_scope["scoped_permissions"] == {"flow.read": True}
