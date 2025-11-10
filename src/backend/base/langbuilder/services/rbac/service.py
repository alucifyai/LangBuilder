"""
RBAC Service for managing role-based access control.

This service provides core permission evaluation logic for the RBAC MVP,
including the can_access() method used by authorization decorators.
Implements Project-to-Flow permission inheritance and Admin bypass logic.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from uuid import UUID

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langbuilder.services.base import Service
from langbuilder.services.database.models.rbac import (
    Permission,
    Role,
    RolePermission,
    UserRoleAssignment,
)

if TYPE_CHECKING:
    from langbuilder.services.database.service import DatabaseService


class RBACService(Service):
    """
    Service for role-based access control operations.

    Provides methods for:
    - Permission checking with inheritance and Admin bypass
    - User role assignment management
    - Role and permission queries
    - In-memory caching for role-permission mappings
    """

    name = "rbac_service"

    def __init__(self, database_service: DatabaseService):
        """
        Initialize RBAC service with database dependency.

        Args:
            database_service: Database service for accessing RBAC models
        """
        self.database_service = database_service
        # Cache for role-permission mappings: {role_id: {(permission_name, scope_type)}}
        self._role_permission_cache: dict[UUID, set[tuple[str, str]]] = {}
        # Cache for role names: {role_id: role_name}
        self._role_name_cache: dict[UUID, str] = {}
        self._cache_timestamp: float | None = None
        self._cache_ttl: float = 3600.0  # 1 hour TTL in seconds

    async def initialize(self) -> None:
        """
        Initialize the RBAC service by loading role-permission cache.

        This should be called during application startup to warm the cache.
        Gracefully handles failures by logging warnings and continuing.
        """
        try:
            await self._load_role_permission_cache()
            logger.info("RBACService initialized successfully with role-permission cache")
        except Exception as exc:
            logger.warning(f"Failed to initialize RBAC cache, will load on first access: {exc}")

    async def _load_role_permission_cache(self) -> None:
        """
        Load role-permission mappings into memory cache.

        Builds a dictionary mapping role_id to a set of (permission_name, scope_type) tuples.
        This cache is used to optimize permission checks.
        """
        async with self.database_service.with_session() as session:
            # Query all role-permission mappings with their associated permission details
            statement = (
                select(RolePermission, Permission, Role)
                .join(Permission, RolePermission.permission_id == Permission.id)
                .join(Role, RolePermission.role_id == Role.id)
            )
            result = await session.exec(statement)
            rows = result.all()

            # Build caches: {role_id: {(permission_name, scope_type)}} and {role_id: role_name}
            cache: dict[UUID, set[tuple[str, str]]] = {}
            name_cache: dict[UUID, str] = {}
            for role_perm, permission, role in rows:
                if role.id not in cache:
                    cache[role.id] = set()
                    name_cache[role.id] = role.name
                cache[role.id].add((permission.name, permission.scope_type))

            self._role_permission_cache = cache
            self._role_name_cache = name_cache
            self._cache_timestamp = time.time()
            logger.debug(f"Loaded role-permission cache with {len(cache)} roles")

    def _is_cache_valid(self) -> bool:
        """
        Check if the cache is still valid based on TTL.

        Returns:
            bool: True if cache exists and is within TTL, False otherwise
        """
        if not self._role_permission_cache or self._cache_timestamp is None:
            return False
        elapsed = time.time() - self._cache_timestamp
        return elapsed < self._cache_ttl

    async def _ensure_cache_loaded(self) -> None:
        """
        Ensure cache is loaded and valid, reload if necessary.

        This method checks cache validity and reloads if expired or missing.
        """
        if not self._is_cache_valid():
            await self._load_role_permission_cache()

    def invalidate_cache(self) -> None:
        """
        Manually invalidate the role-permission cache.

        Call this when role-permission mappings are modified (not in MVP, but for future use).
        """
        self._role_permission_cache = {}
        self._role_name_cache = {}
        self._cache_timestamp = None
        logger.info("RBAC cache invalidated")

    def _role_has_permission(self, role_id: UUID, permission_name: str, scope_type: str) -> bool:
        """
        Check if a role has a specific permission for a scope type (using cache).

        Args:
            role_id: The role ID to check
            permission_name: The permission name (e.g., "Read", "Update")
            scope_type: The scope type (e.g., "Flow", "Project", "Global")

        Returns:
            bool: True if role has the permission, False otherwise
        """
        role_perms = self._role_permission_cache.get(role_id, set())
        return (permission_name, scope_type) in role_perms

    def _get_role_name_from_cache(self, role_id: UUID) -> str | None:
        """
        Get role name from cache by role ID.

        Args:
            role_id: The role ID to look up

        Returns:
            str | None: Role name if found in cache, None otherwise
        """
        return self._role_name_cache.get(role_id)

    async def _is_user_admin(self, user_id: UUID, session: AsyncSession) -> bool:
        """
        Check if user has global Admin role.

        An Admin user is one who has:
        - A Global scope assignment (scope_type="Global", scope_id=None)
        - With a role named "Admin"

        Args:
            user_id: The user ID to check
            session: Database session

        Returns:
            bool: True if user is admin, False otherwise
        """
        # Get all Global scope assignments for this user
        statement = (
            select(UserRoleAssignment)
            .where(UserRoleAssignment.user_id == user_id)
            .where(UserRoleAssignment.scope_type == "Global")
            .where(UserRoleAssignment.scope_id.is_(None))
        )
        result = await session.exec(statement)
        global_assignments = result.all()

        logger.debug(f"Checking admin for user {user_id}: found {len(global_assignments)} Global assignments")

        # For each Global assignment, check if the role is "Admin"
        # Use the cache to look up role names instead of JOIN
        for assignment in global_assignments:
            role_id = assignment.role_id
            # Look up role in cache
            role_name = self._get_role_name_from_cache(role_id)
            logger.debug(f"  Assignment role_id {role_id} -> {role_name}")
            if role_name == "Admin":
                logger.debug(f"  User {user_id} IS admin!")
                return True

        logger.debug(f"  User {user_id} is NOT admin")
        return False

    async def can_access(
        self,
        user_id: UUID,
        permission_name: str,
        scope_type: str,
        scope_id: UUID | None = None,
    ) -> bool:
        """
        Check if a user has a specific permission for a given scope.

        Permission check logic (per PRD 2.1):
        1. If user is Admin (Global assignment with any Admin permission) -> return True
        2. Check for direct scope assignment (Global/Project/Flow)
        3. If scope_type is "Flow" and no direct assignment, check inherited Project role
        4. Return False if no permission found

        Args:
            user_id: The user ID to check
            permission_name: The permission name (e.g., "Read", "Update", "Delete", "Create")
            scope_type: The scope type (e.g., "Flow", "Project", "Global")
            scope_id: Optional scope ID for project/flow scopes

        Returns:
            bool: True if user has permission, False otherwise
        """
        try:
            # Ensure cache is loaded
            await self._ensure_cache_loaded()

            async with self.database_service.with_session() as session:
                # Step 1: Check if user is Admin (bypass all checks)
                if await self._is_user_admin(user_id, session):
                    logger.debug(f"User {user_id} is Admin, granting access")
                    return True

                # Step 2: Check for direct scope assignment
                direct_assignment = await self._check_direct_assignment(
                    user_id, permission_name, scope_type, scope_id, session
                )
                if direct_assignment:
                    return True

                # Step 3: If scope_type is "Flow", check inherited Project permission
                if scope_type == "Flow" and scope_id is not None:
                    # For Flow scope, we need to get the project_id from the Flow
                    # In MVP, we check for Project-level permissions
                    # Note: This requires project_id to be available. For now, we'll
                    # implement inheritance by checking if user has Project-level role
                    # with the same permission. This is simplified for MVP.
                    project_assignment = await self._check_project_inheritance(
                        user_id, permission_name, scope_id, session
                    )
                    if project_assignment:
                        return True

                # Step 4: No permission found
                return False

        except Exception as exc:
            logger.error(f"Error checking permission for user {user_id}: {exc}")
            # Fail closed - deny access on errors
            return False

    async def _check_direct_assignment(
        self,
        user_id: UUID,
        permission_name: str,
        scope_type: str,
        scope_id: UUID | None,
        session: AsyncSession,
    ) -> bool:
        """
        Check if user has direct assignment with the required permission.

        Args:
            user_id: The user ID
            permission_name: The permission name
            scope_type: The scope type
            scope_id: The scope ID (optional for global)
            session: Database session

        Returns:
            bool: True if user has direct assignment with permission
        """
        # Build query for assignments matching the scope
        statement = select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.scope_type == scope_type,
        )

        # Add scope_id condition based on scope_type
        if scope_type == "Global":
            statement = statement.where(UserRoleAssignment.scope_id.is_(None))
        else:
            statement = statement.where(UserRoleAssignment.scope_id == scope_id)

        result = await session.exec(statement)
        assignments = result.all()

        # Check if any of these assignments' roles have the required permission
        for assignment in assignments:
            if self._role_has_permission(assignment.role_id, permission_name, scope_type):
                return True

        return False

    async def _check_project_inheritance(
        self,
        user_id: UUID,
        permission_name: str,
        flow_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """
        Check if user has inherited Project-level permission for a Flow.

        This implements the Project-to-Flow permission inheritance:
        If a user has a Project-level role with the permission, they also
        have it for all Flows within that Project.

        SECURITY: This method now correctly verifies that the flow belongs to
        the specific project before granting inherited permission, preventing
        cross-project permission leakage.

        Args:
            user_id: The user ID
            permission_name: The permission name
            flow_id: The flow ID
            session: Database session

        Returns:
            bool: True if user has inherited permission from Project that contains the flow
        """
        # Step 1: Get the project_id (folder_id) for this flow
        from langbuilder.services.database.models.flow.model import Flow

        flow_stmt = select(Flow.folder_id).where(Flow.id == flow_id)
        result = await session.exec(flow_stmt)
        project_id = result.first()

        # If flow doesn't exist or doesn't belong to a project, no inheritance
        if not project_id:
            return False

        # Step 2: Check if user has project-level assignment for THIS SPECIFIC PROJECT
        statement = (
            select(UserRoleAssignment)
            .where(UserRoleAssignment.user_id == user_id)
            .where(UserRoleAssignment.scope_type == "Project")
            .where(UserRoleAssignment.scope_id == project_id)
        )
        result = await session.exec(statement)
        project_assignments = result.all()

        # Step 3: Check if any of these project assignments have the required permission
        for assignment in project_assignments:
            if self._role_has_permission(assignment.role_id, permission_name, "Project"):
                return True

        return False

    async def get_user_assignments(self, user_id: UUID) -> list[UserRoleAssignment]:
        """
        Get all role assignments for a specific user.

        Args:
            user_id: The user ID

        Returns:
            List of UserRoleAssignment objects
        """
        async with self.database_service.with_session() as session:
            statement = select(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)
            result = await session.exec(statement)
            return result.all()

    async def create_assignment(
        self,
        user_id: UUID,
        role_id: UUID,
        scope_type: str,
        scope_id: UUID | None = None,
        is_immutable: bool = False,
        created_by: UUID | None = None,
    ) -> UserRoleAssignment:
        """
        Create a new user role assignment.

        Args:
            user_id: The user ID
            role_id: The role ID to assign
            scope_type: The scope type ("Global", "Project", "Flow")
            scope_id: The scope ID (None for Global)
            is_immutable: Whether the assignment cannot be deleted
            created_by: User ID who created this assignment

        Returns:
            The created UserRoleAssignment

        Raises:
            ValueError: If assignment already exists or parameters are invalid
        """
        async with self.database_service.with_session() as session:
            # Note: Role validation is handled by database foreign key constraint
            # Direct query validation causes SQLAlchemy binding issues with UUIDstr type
            # The database will raise an error if an invalid role_id is provided

            # Check for duplicate assignment
            statement = (
                select(UserRoleAssignment)
                .where(UserRoleAssignment.user_id == user_id)
                .where(UserRoleAssignment.role_id == role_id)
                .where(UserRoleAssignment.scope_type == scope_type)
            )
            if scope_type == "Global":
                statement = statement.where(UserRoleAssignment.scope_id.is_(None))
            else:
                statement = statement.where(UserRoleAssignment.scope_id == scope_id)

            result = await session.exec(statement)
            existing = result.first()
            if existing:
                msg = f"Assignment already exists for user {user_id}, role {role_id}, scope {scope_type}:{scope_id}"
                raise ValueError(msg)

            # Create new assignment
            assignment = UserRoleAssignment(
                user_id=user_id,
                role_id=role_id,
                scope_type=scope_type,
                scope_id=scope_id,
                is_immutable=is_immutable,
                created_by=created_by,
            )
            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)

            logger.info(
                f"Created assignment: user={user_id}, role={role_id}, "
                f"scope={scope_type}:{scope_id}, immutable={is_immutable}"
            )
            return assignment

    async def update_assignment(self, assignment_id: UUID, role_id: UUID) -> UserRoleAssignment:
        """
        Update an existing role assignment to a different role.

        Args:
            assignment_id: The assignment ID to update
            role_id: The new role ID

        Returns:
            The updated UserRoleAssignment

        Raises:
            ValueError: If assignment not found or role not found
        """
        # Ensure cache is loaded for role validation
        await self._ensure_cache_loaded()

        # Validate new role exists using cache
        role_name = self._get_role_name_from_cache(role_id)
        if not role_name:
            msg = f"Role {role_id} not found"
            raise ValueError(msg)

        async with self.database_service.with_session() as session:
            # Get existing assignment
            assignment = await session.get(UserRoleAssignment, assignment_id)
            if not assignment:
                msg = f"Assignment {assignment_id} not found"
                raise ValueError(msg)

            # Update role
            assignment.role_id = role_id
            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)

            logger.info(f"Updated assignment {assignment_id} to role {role_id}")
            return assignment

    async def delete_assignment(self, assignment_id: UUID) -> None:
        """
        Delete a role assignment.

        Args:
            assignment_id: The assignment ID to delete

        Raises:
            ValueError: If assignment not found or is immutable
        """
        from sqlmodel import select

        async with self.database_service.with_session() as session:
            # Get assignment by scanning all and matching - workaround for UUID type issues
            all_assignments_result = await session.exec(select(UserRoleAssignment))
            all_assignments = all_assignments_result.all()

            assignment = None
            for a in all_assignments:
                if str(a.id) == str(assignment_id):
                    assignment = a
                    break

            if not assignment:
                msg = f"Assignment {assignment_id} not found"
                raise ValueError(msg)

            # Check immutability
            if assignment.is_immutable:
                msg = f"Cannot delete immutable assignment {assignment_id}"
                raise ValueError(msg)

            # Delete assignment
            await session.delete(assignment)
            await session.commit()

            logger.info(f"Deleted assignment {assignment_id}")

    async def list_roles(self) -> list[Role]:
        """
        Get all available roles.

        Returns:
            List of Role objects
        """
        async with self.database_service.with_session() as session:
            statement = select(Role)
            result = await session.exec(statement)
            return result.all()

    async def get_assignments(
        self,
        user_id: UUID | None = None,
        role_id: UUID | None = None,
        scope_type: str | None = None,
    ) -> list[UserRoleAssignment]:
        """
        Get role assignments with optional filtering.

        Args:
            user_id: Optional user ID to filter by
            role_id: Optional role ID to filter by
            scope_type: Optional scope type to filter by

        Returns:
            List of UserRoleAssignment objects matching filters
        """
        async with self.database_service.with_session() as session:
            statement = select(UserRoleAssignment)

            # Apply filters
            if user_id:
                statement = statement.where(UserRoleAssignment.user_id == user_id)
            if role_id:
                statement = statement.where(UserRoleAssignment.role_id == role_id)
            if scope_type:
                statement = statement.where(UserRoleAssignment.scope_type == scope_type)

            result = await session.exec(statement)
            return result.all()
