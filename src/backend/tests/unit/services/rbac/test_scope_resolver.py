"""Unit tests for RBAC scope resolution."""

from uuid import uuid4

import pytest
from langflow.services.database.models.environment import Environment
from langflow.services.database.models.flow import Flow
from langflow.services.database.models.folder import Folder
from langflow.services.database.models.workspace import Workspace
from langflow.services.rbac.scope_resolver import ScopeResolver


@pytest.fixture
async def workspace(async_session):
    """Create a test workspace."""
    workspace = Workspace(
        name="Test Workspace",
        slug="test-workspace",
    )
    async_session.add(workspace)
    await async_session.commit()
    await async_session.refresh(workspace)
    return workspace


@pytest.fixture
async def project(async_session, workspace):
    """Create a test project."""
    project = Folder(
        name="Test Project",
        user_id=uuid4(),
        workspace_id=workspace.id,
    )
    async_session.add(project)
    await async_session.commit()
    await async_session.refresh(project)
    return project


@pytest.fixture
async def environment(async_session, project):
    """Create a test environment."""
    environment = Environment(
        project_id=project.id,
        name="Test Environment",
        environment_type="development",
    )
    async_session.add(environment)
    await async_session.commit()
    await async_session.refresh(environment)
    return environment


@pytest.fixture
async def flow_in_environment(async_session, project, environment):
    """Create a flow in an environment."""
    flow = Flow(
        name="Test Flow in Environment",
        data={},
        folder_id=project.id,
        environment_id=environment.id,
        user_id=uuid4(),
    )
    async_session.add(flow)
    await async_session.commit()
    await async_session.refresh(flow)
    return flow


@pytest.fixture
async def flow_in_project(async_session, project):
    """Create a flow directly in project (no environment)."""
    flow = Flow(
        name="Test Flow in Project",
        data={},
        folder_id=project.id,
        environment_id=None,
        user_id=uuid4(),
    )
    async_session.add(flow)
    await async_session.commit()
    await async_session.refresh(flow)
    return flow


@pytest.fixture
def scope_resolver(async_session):
    """Create a scope resolver instance."""
    return ScopeResolver(async_session)


class TestScopeResolver:
    """Test suite for ScopeResolver class."""

    @pytest.mark.asyncio
    async def test_resolve_workspace_scope(
        self,
        scope_resolver,
        workspace,
    ):
        """Test resolving scope chain for workspace (top level)."""
        chain = await scope_resolver.resolve_scope_chain(
            resource_type="workspace",
            resource_id=workspace.id,
        )

        # Workspace is top level, chain should just contain itself
        assert len(chain) == 1
        assert chain[0] == ("workspace", workspace.id)

    @pytest.mark.asyncio
    async def test_resolve_project_scope(
        self,
        scope_resolver,
        project,
        workspace,
    ):
        """Test resolving scope chain for project."""
        chain = await scope_resolver.resolve_scope_chain(
            resource_type="project",
            resource_id=project.id,
        )

        # Should be: project → workspace
        assert len(chain) == 2
        assert chain[0] == ("project", project.id)
        assert chain[1] == ("workspace", workspace.id)

    @pytest.mark.asyncio
    async def test_resolve_environment_scope(
        self,
        scope_resolver,
        environment,
        project,
        workspace,
    ):
        """Test resolving scope chain for environment."""
        chain = await scope_resolver.resolve_scope_chain(
            resource_type="environment",
            resource_id=environment.id,
        )

        # Should be: environment → project → workspace
        assert len(chain) == 3
        assert chain[0] == ("environment", environment.id)
        assert chain[1] == ("project", project.id)
        assert chain[2] == ("workspace", workspace.id)

    @pytest.mark.asyncio
    async def test_resolve_flow_in_environment_scope(
        self,
        scope_resolver,
        flow_in_environment,
        environment,
        project,
        workspace,
    ):
        """Test resolving scope chain for flow in environment."""
        chain = await scope_resolver.resolve_scope_chain(
            resource_type="flow",
            resource_id=flow_in_environment.id,
        )

        # Should be: flow → environment → project → workspace
        assert len(chain) == 4
        assert chain[0] == ("flow", flow_in_environment.id)
        assert chain[1] == ("environment", environment.id)
        assert chain[2] == ("project", project.id)
        assert chain[3] == ("workspace", workspace.id)

    @pytest.mark.asyncio
    async def test_resolve_flow_in_project_scope(
        self,
        scope_resolver,
        flow_in_project,
        project,
        workspace,
    ):
        """Test resolving scope chain for flow directly in project (no environment)."""
        chain = await scope_resolver.resolve_scope_chain(
            resource_type="flow",
            resource_id=flow_in_project.id,
        )

        # Should be: flow → project → workspace (skip environment)
        assert len(chain) == 3
        assert chain[0] == ("flow", flow_in_project.id)
        assert chain[1] == ("project", project.id)
        assert chain[2] == ("workspace", workspace.id)

    @pytest.mark.asyncio
    async def test_resolve_component_scope(
        self,
        scope_resolver,
        async_session,
        flow_in_project,
        project,
        workspace,
    ):
        """Test resolving scope chain for component."""
        # Add a component to the flow's data
        component_id = uuid4()
        flow_in_project.data = {
            "nodes": [
                {
                    "id": str(component_id),
                    "type": "test_component",
                }
            ]
        }
        async_session.add(flow_in_project)
        await async_session.commit()

        chain = await scope_resolver.resolve_scope_chain(
            resource_type="component",
            resource_id=component_id,
        )

        # Should be: component → flow → project → workspace
        assert len(chain) == 4
        assert chain[0] == ("component", component_id)
        assert chain[1] == ("flow", flow_in_project.id)
        assert chain[2] == ("project", project.id)
        assert chain[3] == ("workspace", workspace.id)

    @pytest.mark.asyncio
    async def test_resolve_component_in_environment_flow_scope(
        self,
        scope_resolver,
        async_session,
        flow_in_environment,
        environment,
        project,
        workspace,
    ):
        """Test resolving scope chain for component in environment flow."""
        # Add a component to the flow's data
        component_id = uuid4()
        flow_in_environment.data = {
            "nodes": [
                {
                    "id": str(component_id),
                    "type": "test_component",
                }
            ]
        }
        async_session.add(flow_in_environment)
        await async_session.commit()

        chain = await scope_resolver.resolve_scope_chain(
            resource_type="component",
            resource_id=component_id,
        )

        # Should be: component → flow → environment → project → workspace
        assert len(chain) == 5
        assert chain[0] == ("component", component_id)
        assert chain[1] == ("flow", flow_in_environment.id)
        assert chain[2] == ("environment", environment.id)
        assert chain[3] == ("project", project.id)
        assert chain[4] == ("workspace", workspace.id)

    @pytest.mark.asyncio
    async def test_get_workspace_id_for_resource(
        self,
        scope_resolver,
        flow_in_project,
        workspace,
    ):
        """Test convenience method to get workspace ID."""
        workspace_id = await scope_resolver.get_workspace_id_for_resource(
            resource_type="flow",
            resource_id=flow_in_project.id,
        )

        assert workspace_id == workspace.id

    @pytest.mark.asyncio
    async def test_invalid_resource_type(
        self,
        scope_resolver,
    ):
        """Test error handling for invalid resource type."""
        with pytest.raises(ValueError, match="Invalid resource_type"):
            await scope_resolver.resolve_scope_chain(
                resource_type="invalid_type",
                resource_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_nonexistent_resource(
        self,
        scope_resolver,
    ):
        """Test error handling for nonexistent resource."""
        nonexistent_id = uuid4()

        with pytest.raises(ValueError, match="not found"):
            await scope_resolver.resolve_scope_chain(
                resource_type="flow",
                resource_id=nonexistent_id,
            )

    @pytest.mark.asyncio
    async def test_project_without_workspace_error(
        self,
        scope_resolver,
        async_session,
    ):
        """Test error when project has no workspace_id."""
        # Create project without workspace (invalid state)
        project = Folder(
            name="Orphan Project",
            user_id=uuid4(),
            workspace_id=None,  # Invalid
        )
        async_session.add(project)
        await async_session.commit()
        await async_session.refresh(project)

        with pytest.raises(ValueError, match="has no workspace_id"):
            await scope_resolver.resolve_scope_chain(
                resource_type="project",
                resource_id=project.id,
            )

    @pytest.mark.asyncio
    async def test_component_not_found_in_flows(
        self,
        scope_resolver,
    ):
        """Test error when component ID doesn't exist in any flow."""
        nonexistent_component_id = uuid4()

        with pytest.raises(ValueError, match="not found or has no parent flow"):
            await scope_resolver.resolve_scope_chain(
                resource_type="component",
                resource_id=nonexistent_component_id,
            )

    @pytest.mark.asyncio
    async def test_scope_chain_ordering(
        self,
        scope_resolver,
        flow_in_environment,
        environment,
        project,
        workspace,
    ):
        """Test scope chain is ordered from specific to broad."""
        chain = await scope_resolver.resolve_scope_chain(
            resource_type="flow",
            resource_id=flow_in_environment.id,
        )

        # Verify ordering: most specific first, broadest last
        scope_types = [scope_type for scope_type, _ in chain]
        expected_order = ["flow", "environment", "project", "workspace"]

        assert scope_types == expected_order
