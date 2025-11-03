"""RBAC Service for permission evaluation and role management.

This service provides core RBAC functionality including:
- Permission evaluation with can_access() method
- Admin role bypass logic
- Permission inheritance from Project to Flow
- Efficient batch permission checking for list endpoints
- Role assignment management

The service follows the existing LangBuilder service pattern and integrates
with the RBAC database models from Task 1.1.
"""
# ruff: noqa: E501, BLE001, FBT001, FBT002, TRY300, TC003

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from loguru import logger
from sqlmodel import select

from langbuilder.services.base import Service
from langbuilder.services.database.models.flow.model import Flow
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.rbac.model import (
    Permission,
    PermissionEnum,
    Role,
    RoleEnum,
    RolePermission,
    ScopeTypeEnum,
    UserRoleAssignment,
)

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class RBACService(Service):
    """Core RBAC service for permission evaluation and role management.

    This service implements the permission evaluation logic defined in PRD Epic 2 Story 2.1,
    supporting Admin bypass, direct scope assignments, and project-to-flow inheritance.
    """

    name = "rbac_service"

    def __init__(self):
        """Initialize the RBAC service."""
        super().__init__()

    async def can_access(
        self,
        session: AsyncSession,
        user_id: UUID,
        permission: PermissionEnum,
        scope_type: ScopeTypeEnum,
        scope_id: UUID | None = None,
    ) -> bool:
        """Check if user has permission for scope.

        Logic per PRD Story 2.1:
        1. Admin role → immediate True (global access)
        2. Direct scope assignment → check permission
        3. Flow scope + no direct assignment → check parent Project (inheritance)
        4. No assignment → False

        Args:
            session: Database async session
            user_id: User UUID
            permission: Permission to check (CREATE, READ, UPDATE, DELETE)
            scope_type: Scope level (GLOBAL, PROJECT, FLOW)
            scope_id: Scope ID (None for GLOBAL scope)

        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Step 1: Check if user is Admin (bypass all checks)
            is_admin = await self._is_admin(session, user_id)
            if is_admin:
                logger.debug(f"User {user_id} is Admin, granting access to {permission} on {scope_type}:{scope_id}")
                return True

            # Step 2: Check direct scope assignment
            has_direct_permission = await self._check_direct_permission(
                session, user_id, permission, scope_type, scope_id
            )
            if has_direct_permission is not None:
                logger.debug(
                    f"User {user_id} direct permission check for {permission} on {scope_type}:{scope_id}: {has_direct_permission}"
                )
                return has_direct_permission

            # Step 3: For Flow scope, check parent Project (inheritance)
            if scope_type == ScopeTypeEnum.FLOW and scope_id:
                parent_project_id = await self._get_parent_project_id(session, scope_id)
                if parent_project_id:
                    has_inherited_permission = await self._check_direct_permission(
                        session, user_id, permission, ScopeTypeEnum.PROJECT, parent_project_id
                    )
                    if has_inherited_permission is not None:
                        logger.debug(
                            f"User {user_id} inherited permission from project {parent_project_id} for {permission} on flow {scope_id}: {has_inherited_permission}"
                        )
                        return has_inherited_permission

            # Step 4: No permission found
            logger.debug(f"User {user_id} has no permission for {permission} on {scope_type}:{scope_id}")
            return False

        except Exception as e:
            logger.error(f"Error checking permission for user {user_id}: {e!s}")
            # Fail closed: deny access on error
            return False

    async def _is_admin(self, session: AsyncSession, user_id: UUID) -> bool:
        """Check if user has Admin role (global scope).

        Args:
            session: Database async session
            user_id: User UUID

        Returns:
            True if user is Admin, False otherwise
        """
        stmt = (
            select(UserRoleAssignment)
            .join(Role)
            .where(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.scope_type == ScopeTypeEnum.GLOBAL,
                Role.name == RoleEnum.ADMIN,
            )
        )
        result = await session.exec(stmt)
        admin_assignment = result.first()
        return admin_assignment is not None

    async def _check_direct_permission(
        self,
        session: AsyncSession,
        user_id: UUID,
        permission: PermissionEnum,
        scope_type: ScopeTypeEnum,
        scope_id: UUID | None,
    ) -> bool | None:
        """Check if user has permission via direct role assignment.

        Args:
            session: Database async session
            user_id: User UUID
            permission: Permission to check
            scope_type: Scope level
            scope_id: Scope ID (None for GLOBAL)

        Returns:
            True if has permission, False if has assignment but no permission, None if no assignment
        """
        stmt = (
            select(UserRoleAssignment)
            .join(Role)
            .join(RolePermission)
            .join(Permission)
            .where(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.scope_type == scope_type,
                UserRoleAssignment.scope_id == scope_id,
                Permission.name == permission,
            )
        )
        result = await session.exec(stmt)
        assignment = result.first()

        if assignment is not None:
            return True

        # Check if user has ANY assignment for this scope (but not the specific permission)
        assignment_stmt = select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.scope_type == scope_type,
            UserRoleAssignment.scope_id == scope_id,
        )
        assignment_result = await session.exec(assignment_stmt)
        has_assignment = assignment_result.first() is not None

        # Return False if has assignment but lacks permission, None if no assignment
        return False if has_assignment else None

    async def _get_parent_project_id(self, session: AsyncSession, flow_id: UUID) -> UUID | None:
        """Get parent project ID for a flow.

        Args:
            session: Database async session
            flow_id: Flow UUID

        Returns:
            Parent project UUID or None if flow has no parent
        """
        stmt = select(Flow.folder_id).where(Flow.id == flow_id)
        result = await session.exec(stmt)
        return result.first()

    async def get_accessible_scope_ids(
        self,
        session: AsyncSession,
        user_id: UUID,
        permission: PermissionEnum,
        scope_type: ScopeTypeEnum,
    ) -> list[UUID]:
        """Get all scope IDs user has permission for.

        Used for efficient list filtering to avoid N+1 permission checks.
        Per Modified Node nl0005, this supports batch permission evaluation.

        Args:
            session: Database async session
            user_id: User UUID
            permission: Permission to check (typically READ)
            scope_type: Scope level (PROJECT or FLOW)

        Returns:
            List of scope IDs user can access
        """
        try:
            # Admin gets all IDs
            is_admin = await self._is_admin(session, user_id)
            if is_admin:
                if scope_type == ScopeTypeEnum.PROJECT:
                    stmt = select(Folder.id)
                    result = await session.exec(stmt)
                    return list(result.all())
                if scope_type == ScopeTypeEnum.FLOW:
                    stmt = select(Flow.id)
                    result = await session.exec(stmt)
                    return list(result.all())
                return []

            accessible_ids = []

            # Get direct assignments for this scope type
            stmt = (
                select(UserRoleAssignment.scope_id)
                .join(Role)
                .join(RolePermission)
                .join(Permission)
                .where(
                    UserRoleAssignment.user_id == user_id,
                    UserRoleAssignment.scope_type == scope_type,
                    Permission.name == permission,
                    UserRoleAssignment.scope_id.isnot(None),
                )
            )
            result = await session.exec(stmt)
            direct_ids = list(result.all())
            accessible_ids.extend(direct_ids)

            # For FLOW scope, also include flows inherited from project permissions
            if scope_type == ScopeTypeEnum.FLOW:
                # Get all project IDs user has permission for
                project_stmt = (
                    select(UserRoleAssignment.scope_id)
                    .join(Role)
                    .join(RolePermission)
                    .join(Permission)
                    .where(
                        UserRoleAssignment.user_id == user_id,
                        UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                        Permission.name == permission,
                        UserRoleAssignment.scope_id.isnot(None),
                    )
                )
                project_result = await session.exec(project_stmt)
                project_ids = list(project_result.all())

                # Get all flows in those projects
                if project_ids:
                    flows_stmt = select(Flow.id).where(Flow.folder_id.in_(project_ids))
                    flows_result = await session.exec(flows_stmt)
                    inherited_flow_ids = list(flows_result.all())
                    accessible_ids.extend(inherited_flow_ids)

            # Remove duplicates and return
            return list(set(accessible_ids))

        except Exception as e:
            logger.error(f"Error getting accessible scope IDs for user {user_id}: {e!s}")
            # Fail closed: return empty list on error
            return []

    async def get_user_roles(
        self,
        session: AsyncSession,
        user_id: UUID,
        scope_type: ScopeTypeEnum | None = None,
        scope_id: UUID | None = None,
    ) -> list[UserRoleAssignment]:
        """Get all role assignments for a user, optionally filtered by scope.

        Args:
            session: Database async session
            user_id: User UUID
            scope_type: Optional scope type filter
            scope_id: Optional scope ID filter

        Returns:
            List of UserRoleAssignment instances
        """
        try:
            stmt = select(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)

            if scope_type is not None:
                stmt = stmt.where(UserRoleAssignment.scope_type == scope_type)

            if scope_id is not None:
                stmt = stmt.where(UserRoleAssignment.scope_id == scope_id)

            result = await session.exec(stmt)
            return list(result.all())

        except Exception as e:
            logger.error(f"Error getting user roles for user {user_id}: {e!s}")
            return []

    async def assign_role(
        self,
        session: AsyncSession,
        user_id: UUID,
        role_name: RoleEnum,
        scope_type: ScopeTypeEnum,
        scope_id: UUID | None = None,
        is_immutable: bool = False,
    ) -> UserRoleAssignment:
        """Assign role to user for scope.

        Per PRD Story 1.3: Admin can assign roles.
        Per PRD Story 1.5: Auto-assign Owner on entity creation.

        Args:
            session: Database async session
            user_id: User UUID
            role_name: Role to assign (Admin, Owner, Editor, Viewer)
            scope_type: Scope level (GLOBAL, PROJECT, FLOW)
            scope_id: ID of project or flow (None for GLOBAL)
            is_immutable: True if assignment cannot be modified/deleted (Default Project Owner)

        Returns:
            Created UserRoleAssignment instance

        Raises:
            ValueError: If role not found or assignment already exists
        """
        try:
            # Get role by name
            role_stmt = select(Role).where(Role.name == role_name)
            result = await session.exec(role_stmt)
            role = result.first()

            if not role:
                error_msg = f"Role {role_name} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Check for existing assignment (unique constraint: user_id, scope_type, scope_id)
            existing_stmt = select(UserRoleAssignment).where(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.scope_type == scope_type,
                UserRoleAssignment.scope_id == scope_id,
            )
            existing_result = await session.exec(existing_stmt)
            existing_assignment = existing_result.first()

            if existing_assignment:
                error_msg = f"Assignment already exists for user {user_id} on {scope_type}:{scope_id}"
                logger.warning(error_msg)
                raise ValueError(error_msg)

            # Create assignment
            assignment = UserRoleAssignment(
                user_id=user_id,
                role_id=role.id,
                scope_type=scope_type,
                scope_id=scope_id,
                is_immutable=is_immutable,
            )
            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)

            logger.info(
                f"Assigned role {role_name} to user {user_id} for {scope_type}:{scope_id} (immutable={is_immutable})"
            )
            return assignment

        except ValueError:
            # Re-raise ValueError for caller to handle
            raise
        except Exception as e:
            logger.error(f"Error assigning role to user {user_id}: {e!s}")
            await session.rollback()
            raise

    async def remove_role(
        self,
        session: AsyncSession,
        assignment_id: UUID,
    ) -> None:
        """Remove role assignment.

        Per PRD Story 1.4: Cannot remove immutable assignments (Default Project Owner).

        Args:
            session: Database async session
            assignment_id: UserRoleAssignment UUID to remove

        Raises:
            ValueError: If assignment not found or is immutable
        """
        try:
            # Get assignment
            assignment = await session.get(UserRoleAssignment, assignment_id)

            if not assignment:
                error_msg = f"Assignment {assignment_id} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Check immutability (PRD Story 1.4)
            if assignment.is_immutable:
                error_msg = (
                    f"Cannot remove immutable assignment {assignment_id} "
                    "(Default Project Owner protection per PRD Story 1.4)"
                )
                logger.warning(error_msg)
                raise ValueError(error_msg)

            # Delete assignment
            await session.delete(assignment)
            await session.commit()

            logger.info(
                f"Removed role assignment {assignment_id} for user {assignment.user_id} "
                f"on {assignment.scope_type}:{assignment.scope_id}"
            )

        except ValueError:
            # Re-raise ValueError for caller to handle
            raise
        except Exception as e:
            logger.error(f"Error removing role assignment {assignment_id}: {e!s}")
            await session.rollback()
            raise

    async def update_assignment(
        self,
        session: AsyncSession,
        assignment_id: UUID,
        new_role_name: RoleEnum,
    ) -> UserRoleAssignment:
        """Update role in existing assignment.

        Per PRD Story 1.4: Cannot modify immutable assignments (Default Project Owner).

        Args:
            session: Database async session
            assignment_id: UserRoleAssignment UUID to update
            new_role_name: New role to assign

        Returns:
            Updated UserRoleAssignment instance

        Raises:
            ValueError: If assignment not found, is immutable, or new role not found
        """
        try:
            # Get assignment
            assignment = await session.get(UserRoleAssignment, assignment_id)

            if not assignment:
                error_msg = f"Assignment {assignment_id} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Check immutability
            if assignment.is_immutable:
                error_msg = (
                    f"Cannot modify immutable assignment {assignment_id} "
                    "(Default Project Owner protection per PRD Story 1.4)"
                )
                logger.warning(error_msg)
                raise ValueError(error_msg)

            # Get new role
            new_role_stmt = select(Role).where(Role.name == new_role_name)
            result = await session.exec(new_role_stmt)
            new_role = result.first()

            if not new_role:
                error_msg = f"Role {new_role_name} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Update assignment
            old_role_id = assignment.role_id
            assignment.role_id = new_role.id
            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)

            logger.info(
                f"Updated role assignment {assignment_id} for user {assignment.user_id} "
                f"on {assignment.scope_type}:{assignment.scope_id} from role {old_role_id} to {new_role.id}"
            )
            return assignment

        except ValueError:
            # Re-raise ValueError for caller to handle
            raise
        except Exception as e:
            logger.error(f"Error updating role assignment {assignment_id}: {e!s}")
            await session.rollback()
            raise
