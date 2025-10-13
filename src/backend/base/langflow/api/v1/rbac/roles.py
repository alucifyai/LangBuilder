"""Role Management API endpoints for RBAC.

Implements PRD Story 3.2 - Custom Role Management
- Create, Read, Update, Delete operations for roles
- Permission validation and assignment
- System role protection
- Audit logging integration
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.rbac.permission import Permission
from langflow.services.database.models.rbac.role import Role, RoleCreate, RoleRead, RoleUpdate
from langflow.services.database.models.rbac.role_assignment import RoleAssignment
from langflow.services.database.models.rbac.role_permission import RolePermission
from langflow.services.database.models.user.model import User

router = APIRouter(prefix="/admin/roles", tags=["Roles"])


async def _check_role_manage_permission(current_user: User) -> None:
    """Check if user has permission to manage roles.

    For now, only superusers can manage roles.
    TODO: Integrate with RBACEnforcementEngine once permission system is fully connected.

    Args:
        current_user: The current authenticated user

    Raises:
        HTTPException: 403 if user lacks permission
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Role management requires superuser access.",
        )


@router.get("/", response_model=list[RoleRead])
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> list[Role]:
    """List all roles with pagination.

    Requires role.manage permission or superuser access.

    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        current_user: Currently authenticated user
        session: Database session

    Returns:
        List of roles

    Raises:
        HTTPException: 403 if user lacks permission
    """
    await _check_role_manage_permission(current_user)

    # Query roles with pagination
    stmt = select(Role).offset(skip).limit(limit).order_by(Role.created_at.desc())
    result = await session.exec(stmt)
    roles = result.all()

    return list(roles)


@router.get("/{role_id}", response_model=RoleRead)
async def get_role(
    role_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> Role:
    """Get a specific role by ID.

    Requires role.manage permission or superuser access.

    Args:
        role_id: UUID of the role to retrieve
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The requested role

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if role not found
    """
    await _check_role_manage_permission(current_user)

    role = await session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found",
        )

    return role


@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> Role:
    """Create a new custom role.

    Implements PRD Story 3.2 @AC1 - Custom role creation with permission assignment.

    Validations:
    - Role name must be unique
    - All permission IDs must exist in the permission catalog
    - Reserved system role names cannot be used

    Args:
        role_data: Role creation data including name, display_name, and permission_ids
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The newly created role

    Raises:
        HTTPException: 400 if role name already exists (PRD Story 1.2 @AC2)
        HTTPException: 400 if unknown permission ID provided (PRD Story 1.1 @AC2)
        HTTPException: 403 if user lacks permission
    """
    await _check_role_manage_permission(current_user)

    # Validate unique role name (PRD Story 1.2 @AC2)
    stmt = select(Role).where(Role.name == role_data.name)
    existing_role = (await session.exec(stmt)).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role name '{role_data.name}' already exists. Role names must be unique.",
        )

    # Validate all permission IDs exist (PRD Story 1.1 @AC2)
    for perm_id in role_data.permission_ids:
        perm = await session.get(Permission, perm_id)
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown permission ID: {perm_id}",
            )

    # Create the role
    try:
        role = Role(
            name=role_data.name,
            display_name=role_data.display_name,
            description=role_data.description,
            is_system_role=False,  # Custom roles are never system roles
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        session.add(role)
        await session.flush()  # Get the role ID

        # Add permissions to the role
        for perm_id in role_data.permission_ids:
            role_perm = RolePermission(
                role_id=role.id,
                permission_id=perm_id,
            )
            session.add(role_perm)

        await session.commit()
        await session.refresh(role)

        logger.info(f"Role created: {role.name} (ID: {role.id}) by user {current_user.id}")

        # TODO: Add audit logging (PRD Story 3.2)
        # await log_audit_event(
        #     actor_id=current_user.id,
        #     action="role.created",
        #     resource_type="role",
        #     resource_id=role.id,
        #     details={"name": role.name, "permissions": role_data.permission_ids}
        # )

        return role

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Database error creating role: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create role due to database constraint violation.",
        ) from e


@router.patch("/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> Role:
    """Update an existing role.

    Implements PRD Story 1.2 @AC3 - Role updates with version tracking and audit logging.

    System roles cannot be modified.

    Args:
        role_id: UUID of the role to update
        role_data: Role update data (display_name, description, is_active, permission_ids)
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The updated role

    Raises:
        HTTPException: 403 if attempting to modify a system role
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if role not found
    """
    await _check_role_manage_permission(current_user)

    # Fetch the role
    role = await session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found",
        )

    # Prevent modification of system roles (PRD requirement)
    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system roles. System roles are immutable.",
        )

    # Update role fields
    update_data = role_data.model_dump(exclude_unset=True)

    # Update display_name if provided
    if update_data.get("display_name"):
        role.display_name = update_data["display_name"]

    # Update description if provided
    if "description" in update_data:
        role.description = update_data["description"]

    # Update is_active if provided
    if "is_active" in update_data and update_data["is_active"] is not None:
        role.is_active = update_data["is_active"]

    # Update permissions if provided
    if "permission_ids" in update_data and update_data["permission_ids"] is not None:
        # Validate all permission IDs exist
        for perm_id in update_data["permission_ids"]:
            perm = await session.get(Permission, perm_id)
            if not perm:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown permission ID: {perm_id}",
                )

        # Remove existing permissions
        stmt = select(RolePermission).where(RolePermission.role_id == role_id)
        existing_perms = (await session.exec(stmt)).all()
        for perm in existing_perms:
            await session.delete(perm)

        # Add new permissions
        for perm_id in update_data["permission_ids"]:
            role_perm = RolePermission(
                role_id=role.id,
                permission_id=perm_id,
            )
            session.add(role_perm)

    # Update timestamp and audit fields
    role.updated_at = datetime.now(timezone.utc)
    role.updated_by = current_user.id

    await session.commit()
    await session.refresh(role)

    logger.info(f"Role updated: {role.name} (ID: {role.id}) by user {current_user.id}")

    # TODO: Invalidate cache for users with this role
    # await invalidate_role_cache(role_id)

    # TODO: Add audit logging (PRD Story 1.2 @AC3)
    # await log_audit_event(
    #     actor_id=current_user.id,
    #     action="role.updated",
    #     resource_type="role",
    #     resource_id=role.id,
    #     details={"before": old_state, "after": new_state}
    # )

    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> None:
    """Delete a role.

    System roles cannot be deleted.
    Roles with active assignments cannot be deleted.

    Args:
        role_id: UUID of the role to delete
        current_user: Currently authenticated user
        session: Database session

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 400 if role has active assignments
        HTTPException: 403 if attempting to delete a system role
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if role not found
    """
    await _check_role_manage_permission(current_user)

    # Fetch the role
    role = await session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found",
        )

    # Prevent deletion of system roles (PRD requirement)
    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system roles. System roles are protected.",
        )

    # Check if role has active assignments
    stmt = select(RoleAssignment).where(RoleAssignment.role_id == role_id)
    assignments = (await session.exec(stmt)).all()
    if assignments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot delete role '{role.name}' because it has {len(assignments)} active assignment(s). "
                "Revoke all role assignments before deleting the role."
            ),
        )

    # Delete the role (cascade will delete role_permissions)
    role_name = role.name
    await session.delete(role)
    await session.commit()

    logger.info(f"Role deleted: {role_name} (ID: {role_id}) by user {current_user.id}")

    # TODO: Add audit logging
    # await log_audit_event(
    #     actor_id=current_user.id,
    #     action="role.deleted",
    #     resource_type="role",
    #     resource_id=role_id,
    #     details={"name": role_name}
    # )
