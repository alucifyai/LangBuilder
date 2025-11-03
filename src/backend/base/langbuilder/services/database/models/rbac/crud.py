"""CRUD operations for RBAC models.

This module provides async database operations for Role, Permission, RolePermission,
and UserRoleAssignment models. All operations follow the async/await pattern and use
SQLModel with AsyncSession for database interactions.
"""
# ruff: noqa: FBT001, FBT002, TRY300

from uuid import UUID

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langbuilder.services.database.models.rbac.model import (
    Permission,
    PermissionEnum,
    Role,
    RoleEnum,
    RolePermission,
    ScopeTypeEnum,
    UserRoleAssignment,
    UserRoleAssignmentCreate,
    UserRoleAssignmentUpdate,
)

# Role CRUD operations


async def get_role_by_id(db: AsyncSession, role_id: UUID) -> Role | None:
    """Get role by ID.

    Args:
        db: Database session
        role_id: Role UUID

    Returns:
        Role instance or None if not found
    """
    stmt = select(Role).where(Role.id == role_id)
    return (await db.exec(stmt)).first()


async def get_role_by_name(db: AsyncSession, role_name: RoleEnum) -> Role | None:
    """Get role by name.

    Args:
        db: Database session
        role_name: Role name enum value

    Returns:
        Role instance or None if not found
    """
    stmt = select(Role).where(Role.name == role_name)
    return (await db.exec(stmt)).first()


async def get_all_roles(db: AsyncSession) -> list[Role]:
    """Get all roles.

    Args:
        db: Database session

    Returns:
        List of all Role instances
    """
    stmt = select(Role)
    result = await db.exec(stmt)
    return list(result.all())


# Permission CRUD operations


async def get_permission_by_id(db: AsyncSession, permission_id: UUID) -> Permission | None:
    """Get permission by ID.

    Args:
        db: Database session
        permission_id: Permission UUID

    Returns:
        Permission instance or None if not found
    """
    stmt = select(Permission).where(Permission.id == permission_id)
    return (await db.exec(stmt)).first()


async def get_permission_by_name(db: AsyncSession, permission_name: PermissionEnum) -> Permission | None:
    """Get permission by name.

    Args:
        db: Database session
        permission_name: Permission name enum value

    Returns:
        Permission instance or None if not found
    """
    stmt = select(Permission).where(Permission.name == permission_name)
    return (await db.exec(stmt)).first()


async def get_all_permissions(db: AsyncSession) -> list[Permission]:
    """Get all permissions.

    Args:
        db: Database session

    Returns:
        List of all Permission instances
    """
    stmt = select(Permission)
    result = await db.exec(stmt)
    return list(result.all())


# RolePermission CRUD operations


async def get_role_permissions(db: AsyncSession, role_id: UUID) -> list[RolePermission]:
    """Get all permissions for a specific role.

    Args:
        db: Database session
        role_id: Role UUID

    Returns:
        List of RolePermission instances for the role
    """
    stmt = select(RolePermission).where(RolePermission.role_id == role_id)
    result = await db.exec(stmt)
    return list(result.all())


async def get_permissions_for_role(db: AsyncSession, role_id: UUID) -> list[Permission]:
    """Get Permission entities for a specific role.

    Args:
        db: Database session
        role_id: Role UUID

    Returns:
        List of Permission instances granted to the role
    """
    stmt = select(Permission).join(RolePermission).where(RolePermission.role_id == role_id)
    result = await db.exec(stmt)
    return list(result.all())


# UserRoleAssignment CRUD operations


async def get_assignment_by_id(db: AsyncSession, assignment_id: UUID) -> UserRoleAssignment | None:
    """Get user role assignment by ID.

    Args:
        db: Database session
        assignment_id: Assignment UUID

    Returns:
        UserRoleAssignment instance or None if not found
    """
    stmt = select(UserRoleAssignment).where(UserRoleAssignment.id == assignment_id)
    return (await db.exec(stmt)).first()


async def get_user_assignments(db: AsyncSession, user_id: UUID) -> list[UserRoleAssignment]:
    """Get all role assignments for a specific user.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        List of UserRoleAssignment instances for the user
    """
    stmt = select(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)
    result = await db.exec(stmt)
    return list(result.all())


async def get_user_assignment_for_scope(
    db: AsyncSession,
    user_id: UUID,
    scope_type: ScopeTypeEnum,
    scope_id: UUID | None = None,
) -> UserRoleAssignment | None:
    """Get user role assignment for a specific scope.

    Args:
        db: Database session
        user_id: User UUID
        scope_type: Scope type (GLOBAL, PROJECT, FLOW)
        scope_id: Scope ID (None for GLOBAL scope)

    Returns:
        UserRoleAssignment instance or None if not found
    """
    stmt = select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.scope_type == scope_type,
        UserRoleAssignment.scope_id == scope_id,
    )
    return (await db.exec(stmt)).first()


async def create_assignment(
    db: AsyncSession,
    assignment_data: UserRoleAssignmentCreate,
    is_immutable: bool = False,
) -> UserRoleAssignment:
    """Create a new user role assignment.

    Args:
        db: Database session
        assignment_data: Assignment creation data
        is_immutable: Whether assignment is immutable (Default Project Owner)

    Returns:
        Created UserRoleAssignment instance

    Raises:
        HTTPException: If assignment creation fails due to integrity constraints
    """
    try:
        assignment = UserRoleAssignment(
            user_id=assignment_data.user_id,
            role_id=assignment_data.role_id,
            scope_type=assignment_data.scope_type,
            scope_id=assignment_data.scope_id,
            is_immutable=is_immutable,
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Error creating role assignment: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Assignment already exists or invalid foreign key: {e!s}",
        ) from e


async def update_assignment(
    db: AsyncSession,
    assignment: UserRoleAssignment,
    update_data: UserRoleAssignmentUpdate,
) -> UserRoleAssignment:
    """Update a user role assignment.

    Args:
        db: Database session
        assignment: UserRoleAssignment instance to update
        update_data: Update data

    Returns:
        Updated UserRoleAssignment instance

    Raises:
        HTTPException: If assignment is immutable or update fails
    """
    if assignment.is_immutable:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify immutable assignment (Default Project Owner)",
        )

    try:
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(assignment, key, value)

        await db.commit()
        await db.refresh(assignment)
        return assignment
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Error updating role assignment: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role assignment update: {e!s}",
        ) from e


async def delete_assignment(db: AsyncSession, assignment: UserRoleAssignment) -> None:
    """Delete a user role assignment.

    Args:
        db: Database session
        assignment: UserRoleAssignment instance to delete

    Raises:
        HTTPException: If assignment is immutable
    """
    if assignment.is_immutable:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete immutable assignment (Default Project Owner)",
        )

    try:
        await db.delete(assignment)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting role assignment: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete assignment: {e!s}",
        ) from e


async def get_all_assignments(db: AsyncSession) -> list[UserRoleAssignment]:
    """Get all user role assignments.

    Args:
        db: Database session

    Returns:
        List of all UserRoleAssignment instances
    """
    stmt = select(UserRoleAssignment)
    result = await db.exec(stmt)
    return list(result.all())


async def get_assignments_by_scope(
    db: AsyncSession,
    scope_type: ScopeTypeEnum,
    scope_id: UUID | None = None,
) -> list[UserRoleAssignment]:
    """Get all assignments for a specific scope.

    Args:
        db: Database session
        scope_type: Scope type (GLOBAL, PROJECT, FLOW)
        scope_id: Scope ID (None for GLOBAL scope)

    Returns:
        List of UserRoleAssignment instances for the scope
    """
    stmt = select(UserRoleAssignment).where(
        UserRoleAssignment.scope_type == scope_type,
        UserRoleAssignment.scope_id == scope_id,
    )
    result = await db.exec(stmt)
    return list(result.all())
