"""Scope resolution for hierarchical RBAC permission checks.

This module provides scope chain resolution functionality for the RBAC system,
resolving the hierarchy from a resource up to its workspace:
    Component → Flow → Environment → Project → Workspace
"""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

if TYPE_CHECKING:
    from langflow.services.database.models.flow.model import Flow


class ScopeResolver:
    """Resolves scope chains for RBAC permission evaluation.

    The scope hierarchy is: workspace > project > environment > flow > component.
    Scope chain resolution walks from a resource up to its workspace,
    enabling permission inheritance from broader scopes.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the scope resolver.

        Args:
            session: Async database session for querying
        """
        self.session = session

    async def resolve_scope_chain(
        self,
        resource_type: str,
        resource_id: UUID,
    ) -> list[tuple[str, UUID]]:
        """Resolve full scope chain from resource to workspace.

        Walks the scope hierarchy from the given resource up to its workspace.
        Returns list ordered from most specific (resource) to broadest (workspace).

        Examples:
            Component C1 in Flow F1 in Project P1 in Workspace W1:
            [("component", C1), ("flow", F1), ("project", P1), ("workspace", W1)]

            Flow F2 in Environment E1 in Project P2 in Workspace W2:
            [("flow", F2), ("environment", E1), ("project", P2), ("workspace", W2)]

            Project P3 in Workspace W3:
            [("project", P3), ("workspace", W3)]

        Args:
            resource_type: Type of resource ("component", "flow", "environment", "project", "workspace")
            resource_id: UUID of the resource

        Returns:
            List of (scope_type, scope_id) tuples from specific to broad

        Raises:
            ValueError: If resource_type is invalid or resource not found
        """
        # Import here to avoid circular imports
        from langflow.services.database.models.environment.model import Environment
        from langflow.services.database.models.flow.model import Flow
        from langflow.services.database.models.folder.model import Folder

        chain: list[tuple[str, UUID]] = [(resource_type, resource_id)]

        if resource_type == "component":
            # Component → Flow → (Environment) → Project → Workspace
            flow = await self._get_flow_for_component(resource_id)
            if not flow:
                raise ValueError(f"Component {resource_id} not found or has no parent flow")

            chain.append(("flow", flow.id))

            # Check if flow is in an environment
            if flow.environment_id:
                chain.append(("environment", flow.environment_id))
                environment = await self.session.get(Environment, flow.environment_id)
                if not environment:
                    raise ValueError(f"Environment {flow.environment_id} not found")
                chain.append(("project", environment.project_id))
            else:
                # Flow not in environment, directly in project
                chain.append(("project", flow.folder_id))

            # Get project and add workspace
            project = await self.session.get(Folder, chain[-1][1])
            if not project:
                raise ValueError(f"Project {chain[-1][1]} not found")
            if not project.workspace_id:
                raise ValueError(f"Project {project.id} has no workspace_id")
            chain.append(("workspace", project.workspace_id))

        elif resource_type == "flow":
            # Flow → (Environment) → Project → Workspace
            flow = await self.session.get(Flow, resource_id)
            if not flow:
                raise ValueError(f"Flow {resource_id} not found")

            # Check if flow is in an environment
            if flow.environment_id:
                chain.append(("environment", flow.environment_id))
                environment = await self.session.get(Environment, flow.environment_id)
                if not environment:
                    raise ValueError(f"Environment {flow.environment_id} not found")
                chain.append(("project", environment.project_id))
            else:
                # Flow not in environment, directly in project
                chain.append(("project", flow.folder_id))

            # Get project and add workspace
            project = await self.session.get(Folder, chain[-1][1])
            if not project:
                raise ValueError(f"Project {chain[-1][1]} not found")
            if not project.workspace_id:
                raise ValueError(f"Project {project.id} has no workspace_id")
            chain.append(("workspace", project.workspace_id))

        elif resource_type == "environment":
            # Environment → Project → Workspace
            environment = await self.session.get(Environment, resource_id)
            if not environment:
                raise ValueError(f"Environment {resource_id} not found")

            chain.append(("project", environment.project_id))
            project = await self.session.get(Folder, environment.project_id)
            if not project:
                raise ValueError(f"Project {environment.project_id} not found")
            if not project.workspace_id:
                raise ValueError(f"Project {project.id} has no workspace_id")
            chain.append(("workspace", project.workspace_id))

        elif resource_type == "project":
            # Project → Workspace
            project = await self.session.get(Folder, resource_id)
            if not project:
                raise ValueError(f"Project {resource_id} not found")
            if not project.workspace_id:
                raise ValueError(f"Project {resource_id} has no workspace_id")
            chain.append(("workspace", project.workspace_id))

        elif resource_type == "workspace":
            # Already at top level, no need to walk up
            pass

        else:
            raise ValueError(
                f"Invalid resource_type: {resource_type}. "
                f"Must be one of: component, flow, environment, project, workspace"
            )

        return chain

    async def _get_flow_for_component(self, component_id: UUID) -> "Flow | None":
        """Get the flow containing a component.

        Components are embedded in Flow.data JSON, not separate DB entities.
        This method searches all flows for the component ID.

        Args:
            component_id: UUID of the component

        Returns:
            Flow containing the component, or None if not found

        Note:
            This is a simplified implementation. In production, you may want to:
            - Index component IDs for faster lookup
            - Cache component → flow mappings
            - Use JSON query operators for more efficient search
        """
        from langflow.services.database.models.flow.model import Flow

        # Query all flows and check their data JSON for the component
        # This is inefficient but works for MVP. Consider indexing in production.
        result = await self.session.execute(select(Flow))
        flows = result.scalars().all()

        # Search for component in each flow's data
        for flow in flows:
            if flow.data and isinstance(flow.data, dict):
                # Check if component_id exists in the flow's node list
                nodes = flow.data.get("nodes", [])
                for node in nodes:
                    if isinstance(node, dict) and str(node.get("id")) == str(component_id):
                        return flow

        return None

    async def get_workspace_id_for_resource(
        self,
        resource_type: str,
        resource_id: UUID,
    ) -> UUID:
        """Get the workspace ID for any resource.

        Convenience method to quickly get workspace ID without full chain.

        Args:
            resource_type: Type of resource
            resource_id: UUID of the resource

        Returns:
            Workspace UUID

        Raises:
            ValueError: If resource not found or has no workspace
        """
        chain = await self.resolve_scope_chain(resource_type, resource_id)

        # Find workspace in chain (should always be last)
        for scope_type, scope_id in chain:
            if scope_type == "workspace":
                return scope_id

        raise ValueError(f"No workspace found for {resource_type} {resource_id}")
