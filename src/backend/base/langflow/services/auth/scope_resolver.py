"""Scope resolution utilities for RBAC system.

Implements scope hierarchy and inheritance logic.
PRD Story 2.1 @AC4: Higher-scope grants cascade to lower scopes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.grant import ScopeType


class ScopeResolver:
    """Resolves scope relationships and inheritance.

    The scope hierarchy is (PRD Story 2.1 @AC3):
    Workspace (1) > Project (2) > Environment (3) > Flow (4) > Component (5)

    Higher-scope grants automatically apply to all lower scopes within them.
    """

    # Scope hierarchy (lower rank = higher scope)
    HIERARCHY = {
        "workspace": 1,
        "project": 2,
        "environment": 3,
        "flow": 4,
        "component": 5,
    }

    @classmethod
    def get_scope_rank(cls, scope_type: ScopeType | str) -> int:
        """Get numeric rank of a scope type.

        Args:
            scope_type: Scope type to rank

        Returns:
            Numeric rank (1=highest, 5=lowest)
        """
        return cls.HIERARCHY.get(str(scope_type), 999)

    @classmethod
    def is_higher_scope(cls, scope_a: ScopeType | str, scope_b: ScopeType | str) -> bool:
        """Check if scope_a is higher than scope_b in the hierarchy.

        Args:
            scope_a: First scope type
            scope_b: Second scope type

        Returns:
            True if scope_a is higher than scope_b
        """
        return cls.get_scope_rank(scope_a) < cls.get_scope_rank(scope_b)

    @classmethod
    def get_parent_scopes(cls, scope_type: ScopeType | str) -> list[str]:
        """Get all parent (higher) scopes for a given scope type.

        For example, for "flow", returns ["workspace", "project", "environment"].

        Args:
            scope_type: Scope type to find parents for

        Returns:
            List of parent scope types, ordered from highest to lowest
        """
        current_rank = cls.get_scope_rank(scope_type)
        parents = []

        for scope, rank in sorted(cls.HIERARCHY.items(), key=lambda x: x[1]):
            if rank < current_rank:
                parents.append(scope)

        return parents

    @classmethod
    def get_child_scopes(cls, scope_type: ScopeType | str) -> list[str]:
        """Get all child (lower) scopes for a given scope type.

        For example, for "project", returns ["environment", "flow", "component"].

        Args:
            scope_type: Scope type to find children for

        Returns:
            List of child scope types, ordered from highest to lowest
        """
        current_rank = cls.get_scope_rank(scope_type)
        children = []

        for scope, rank in sorted(cls.HIERARCHY.items(), key=lambda x: x[1]):
            if rank > current_rank:
                children.append(scope)

        return children

    @classmethod
    async def scope_includes(
        cls,
        grant_scope_type: ScopeType | str,
        grant_scope_id: str,
        check_scope_type: ScopeType | str,
        check_scope_id: str,
        db: AsyncSession | None = None,
    ) -> bool:
        """Check if a grant scope includes a check scope.

        A grant scope includes a check scope if:
        1. They are identical (same type and ID)
        2. The grant scope is higher and the check scope is a child resource

        This implementation checks actual parent-child relationships in the database.

        Args:
            grant_scope_type: Type of the grant's scope
            grant_scope_id: ID of the grant's scope
            check_scope_type: Type of the scope being checked
            check_scope_id: ID of the scope being checked
            db: Database session for lookup (required for relationship checking)

        Returns:
            True if grant scope includes check scope

        High Priority Fix #1: Implements production scope inheritance
        Phase 2 Audit Recommendation #1
        """
        # Exact match
        if (str(grant_scope_type) == str(check_scope_type) and
                grant_scope_id == check_scope_id):
            return True

        # Grant scope must be higher than check scope
        if not cls.is_higher_scope(grant_scope_type, check_scope_type):
            return False

        # If no database session, fallback to simplified inheritance
        # This maintains backward compatibility for non-async code
        if db is None:
            return False

        # Check actual parent-child relationships
        try:
            parent_id = await cls._get_parent_id(
                db=db,
                resource_type=check_scope_type,
                resource_id=check_scope_id,
                parent_type=grant_scope_type
            )
            return parent_id == grant_scope_id
        except Exception:
            # If lookup fails, deny access (fail secure)
            return False

    @classmethod
    async def _get_parent_id(
        cls,
        db: AsyncSession,
        resource_type: str,
        resource_id: str,
        parent_type: str,
    ) -> str | None:
        """Get the parent ID of a resource by walking up the hierarchy.

        Maps LangBuilder's actual schema to RBAC hierarchy:
        - "project" maps to Folder (with parent_id)
        - "flow" maps to Flow (with folder_id)
        - "workspace" maps to top-level Folder (parent_id IS NULL)
        - "component" and "environment" not yet implemented in schema

        Args:
            db: Database session
            resource_type: Type of the child resource
            resource_id: ID of the child resource
            parent_type: Type of parent we're looking for

        Returns:
            Parent ID if found, None otherwise

        Note: This maps PRD scope types to actual LangBuilder schema
        """
        from langflow.services.database.models.flow.model import Flow
        from langflow.services.database.models.folder.model import Folder

        resource_type = str(resource_type).lower()
        parent_type = str(parent_type).lower()

        # Flow -> Project/Folder relationship
        if resource_type == "flow":
            stmt = select(Flow.folder_id).where(Flow.id == UUID(resource_id))
            result = await db.execute(stmt)
            folder_id = result.scalar_one_or_none()

            if parent_type == "project":
                # Direct parent: Flow.folder_id
                return str(folder_id) if folder_id else None

            if parent_type == "workspace" and folder_id:
                # Walk up to workspace (top-level folder)
                return await cls._get_workspace_id(db, folder_id)

        # Project/Folder -> Workspace relationship
        elif resource_type == "project":
            if parent_type == "workspace":
                return await cls._get_workspace_id(db, UUID(resource_id))

        # Component -> Flow (not yet in schema, but planned)
        elif resource_type == "component":
            # TODO: When component table exists, add:
            # stmt = select(Component.flow_id).where(Component.id == UUID(resource_id))
            # For now, return None (no component schema yet)
            return None

        return None

    @classmethod
    async def _get_workspace_id(cls, db: AsyncSession, folder_id: UUID) -> str | None:
        """Walk up folder tree to find top-level workspace folder.

        Args:
            db: Database session
            folder_id: Starting folder ID

        Returns:
            Top-level workspace folder ID
        """
        from langflow.services.database.models.folder.model import Folder

        # Walk up parent chain until parent_id IS NULL (workspace)
        current_id = folder_id
        while current_id:
            stmt = select(Folder.parent_id).where(Folder.id == current_id)
            result = await db.execute(stmt)
            parent_id = result.scalar_one_or_none()

            if parent_id is None:
                # Found top-level folder (workspace)
                return str(current_id)

            current_id = parent_id

        # If we get here, the folder wasn't found
        return None

    @classmethod
    def get_scope_path(cls, scope_type: ScopeType | str) -> list[str]:
        """Get the full inheritance path for a scope type.

        Args:
            scope_type: Scope type

        Returns:
            List of scope types from root (workspace) to the given scope
        """
        path = []
        current_rank = cls.get_scope_rank(scope_type)

        for scope, rank in sorted(cls.HIERARCHY.items(), key=lambda x: x[1]):
            if rank <= current_rank:
                path.append(scope)

        return path
