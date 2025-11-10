"""
RBAC API Router for managing role-based access control.

This module provides REST endpoints for RBAC management operations:
- List roles
- Manage role assignments (CRUD)
- Check permissions (single and batch)

All management endpoints require Admin role. Permission check endpoints
are available to all authenticated users.
"""

from datetime import datetime
from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, field_validator
from sqlmodel.ext.asyncio.session import AsyncSession

from langbuilder.api.utils import CurrentActiveUser, DbSession
from langbuilder.services.database.models.rbac import (
    Role,
    UserRoleAssignment,
)
from langbuilder.services.database.models.user.model import User
from langbuilder.services.deps import get_service
from langbuilder.services.rbac.factory import RBACServiceFactory
from langbuilder.services.rbac.service import RBACService
from langbuilder.services.schema import ServiceType

router = APIRouter(tags=["RBAC"], prefix="/rbac")


# ============================================================================
# Pydantic Schemas
# ============================================================================


class RoleResponse(BaseModel):
    """Response schema for Role."""

    id: str
    name: str
    description: Optional[str] = None
    is_system: bool

    model_config = ConfigDict(from_attributes=True)

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, value: Any) -> str:
        """Convert UUID objects to strings."""
        return str(value)


class AssignmentResponse(BaseModel):
    """Response schema for UserRoleAssignment with enriched data."""

    id: str
    user_id: str
    user_name: Optional[str] = None  # Enriched: username
    role_id: str
    role_name: Optional[str] = None  # Enriched: role name (Admin, Owner, etc.)
    scope_type: str
    scope_id: Optional[str] = None
    scope_name: Optional[str] = None  # Enriched: project/flow name
    is_immutable: bool
    created_at: datetime
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('id', 'user_id', 'role_id', 'scope_id', 'created_by', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, value: Any) -> Optional[str]:
        """Convert UUID objects to strings."""
        if value is None:
            return None
        return str(value)


class AssignmentCreate(BaseModel):
    """Request schema for creating a new assignment."""

    user_id: UUID
    role_id: UUID
    scope_type: str
    scope_id: Optional[UUID] = None
    is_immutable: bool = False


class AssignmentUpdate(BaseModel):
    """Request schema for updating an assignment."""

    role_id: UUID


class PermissionCheckRequest(BaseModel):
    """Request schema for checking a single permission."""

    permission: str
    scope_type: str
    scope_id: Optional[UUID] = None


class PermissionCheckResponse(BaseModel):
    """Response schema for permission check."""

    allowed: bool


class BatchResource(BaseModel):
    """Resource identifier for batch permission checks."""

    id: str
    scope_type: str
    scope_id: Optional[str] = None


class PermissionCheckBatchRequest(BaseModel):
    """Request schema for batch permission checks."""

    permission: str
    resources: list[BatchResource]


class PermissionCheckBatchResponse(BaseModel):
    """Response schema for batch permission checks."""

    results: dict[str, bool]


# ============================================================================
# Dependencies
# ============================================================================


def get_rbac_service() -> RBACService:
    """
    Get RBACService instance from service manager.

    Returns:
        RBACService: The RBAC service instance

    Raises:
        HTTPException: If service cannot be retrieved
    """
    try:
        service = get_service(ServiceType.RBAC_SERVICE, RBACServiceFactory())
        if not service:
            raise HTTPException(
                status_code=500,
                detail="RBAC service not available",
            )
        return service
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get RBAC service: {str(exc)}",
        ) from exc


async def require_admin(
    current_user: CurrentActiveUser,
    session: DbSession,
) -> User:
    """
    Require Admin role for endpoint access.

    Checks if the current user has Admin role by verifying they have at least one
    role assignment with scope_type="Global". Superusers bypass this check and
    are always granted admin access.

    Args:
        current_user: The authenticated user from get_current_active_user
        session: Database session

    Returns:
        User: The current user if they have Admin role or are a superuser

    Raises:
        HTTPException: 403 if user does not have Admin role and is not a superuser
    """
    # Superusers always have admin access, bypassing RBAC
    if current_user.is_superuser:
        return current_user

    rbac_service = get_rbac_service()

    # Check if user has Admin role by looking for any Global scope assignment
    # Admin role is defined as having any permission with scope_type="Global"
    user_assignments = await rbac_service.get_user_assignments(current_user.id)

    has_admin_role = any(
        assignment.scope_type == "Global"  # Note: uppercase "Global"
        for assignment in user_assignments
    )

    if not has_admin_role:
        raise HTTPException(
            status_code=403,
            detail="Admin access required for RBAC management operations",
        )

    return current_user


# Type alias for admin dependency
AdminUser = Annotated[User, Depends(require_admin)]


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    admin_user: AdminUser,
) -> list[Role]:
    """
    List all available roles.

    Requires Admin role.

    Args:
        admin_user: Authenticated admin user (dependency)

    Returns:
        List of all Role objects

    Raises:
        HTTPException: 403 if not admin, 500 on error
    """
    try:
        rbac_service = get_rbac_service()
        roles = await rbac_service.list_roles()
        return roles
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list roles: {str(exc)}",
        ) from exc


@router.get("/assignments", response_model=list[AssignmentResponse])
async def list_assignments(
    admin_user: AdminUser,
    session: DbSession,
    user_id: Optional[UUID] = None,
    role_id: Optional[UUID] = None,
    scope_type: Optional[str] = None,
) -> list[AssignmentResponse]:
    """
    List role assignments with optional filtering and enriched data.

    Requires Admin role. Returns assignments with user names, role names,
    and scope names (project/flow names) for better UI display.

    Args:
        admin_user: Authenticated admin user (dependency)
        session: Database session (dependency)
        user_id: Optional user ID to filter by
        role_id: Optional role ID to filter by
        scope_type: Optional scope type to filter by

    Returns:
        List of enriched AssignmentResponse objects

    Raises:
        HTTPException: 403 if not admin, 500 on error
    """
    try:
        from sqlmodel import select
        from langbuilder.services.database.models.flow.model import Flow
        from langbuilder.services.database.models.folder.model import Folder

        rbac_service = get_rbac_service()
        assignments = await rbac_service.get_assignments(
            user_id=user_id,
            role_id=role_id,
            scope_type=scope_type,
        )

        # Filter out immutable assignments (Starter Project ownership)
        assignments = [a for a in assignments if not a.is_immutable]

        # Preload all entities into dictionaries for efficient lookup
        # Get all users
        users_result = await session.execute(select(User))
        users_dict = {str(u.id): u for u in users_result.scalars().all()}

        # Get all roles
        roles_result = await session.execute(select(Role))
        roles_dict = {str(r.id): r for r in roles_result.scalars().all()}

        # Get all folders (projects)
        folders_result = await session.execute(select(Folder))
        folders_dict = {str(f.id): f for f in folders_result.scalars().all()}

        # Get all flows
        flows_result = await session.execute(select(Flow))
        flows_dict = {str(f.id): f for f in flows_result.scalars().all()}

        # Enrich assignments with user names, role names, and scope names
        enriched_assignments = []
        for assignment in assignments:
            # Get user name
            user = users_dict.get(str(assignment.user_id))
            user_name = user.username if user else None

            # Get role name
            role = roles_dict.get(str(assignment.role_id))
            role_name = role.name if role else None

            # Get scope name (project or flow name)
            scope_name = None
            if assignment.scope_id:
                if assignment.scope_type == "Project":
                    folder = folders_dict.get(str(assignment.scope_id))
                    scope_name = folder.name if folder else None
                elif assignment.scope_type == "Flow":
                    flow = flows_dict.get(str(assignment.scope_id))
                    scope_name = flow.name if flow else None

            # Build enriched response
            enriched = AssignmentResponse(
                id=str(assignment.id),
                user_id=str(assignment.user_id),
                user_name=user_name,
                role_id=str(assignment.role_id),
                role_name=role_name,
                scope_type=assignment.scope_type,
                scope_id=str(assignment.scope_id) if assignment.scope_id else None,
                scope_name=scope_name,
                is_immutable=assignment.is_immutable,
                created_at=assignment.created_at,
                created_by=str(assignment.created_by) if assignment.created_by else None,
            )
            enriched_assignments.append(enriched)

        return enriched_assignments
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list assignments: {str(exc)}",
        ) from exc


@router.post("/assignments", response_model=AssignmentResponse, status_code=201)
async def create_assignment(
    assignment: AssignmentCreate,
    admin_user: AdminUser,
    session: DbSession,
) -> UserRoleAssignment:
    """
    Create a new role assignment.

    Requires Admin role.

    Args:
        assignment: Assignment creation data
        admin_user: Authenticated admin user (dependency)
        session: Database session (dependency)

    Returns:
        The created UserRoleAssignment

    Raises:
        HTTPException: 400 if validation fails, 403 if not admin, 500 on error
    """
    try:
        from sqlmodel import select

        rbac_service = get_rbac_service()

        # Skip validation - let the RBAC service handle it
        # The service will validate during assignment creation

        # Create assignment
        new_assignment = await rbac_service.create_assignment(
            user_id=assignment.user_id,
            role_id=assignment.role_id,
            scope_type=assignment.scope_type,
            scope_id=assignment.scope_id,
            is_immutable=assignment.is_immutable,
            created_by=admin_user.id,
        )

        return new_assignment

    except ValueError as exc:
        # RBACService raises ValueError for business logic errors
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create assignment: {str(exc)}",
        ) from exc


@router.patch("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    assignment_update: AssignmentUpdate,
    admin_user: AdminUser,
    session: DbSession,
) -> UserRoleAssignment:
    """
    Update an existing role assignment to a different role.

    Cannot update immutable assignments. Requires Admin role.

    Args:
        assignment_id: The assignment ID to update
        assignment_update: Update data with new role_id
        admin_user: Authenticated admin user (dependency)
        session: Database session (dependency)

    Returns:
        The updated UserRoleAssignment

    Raises:
        HTTPException: 400 if immutable or validation fails, 404 if not found, 403 if not admin
    """
    try:
        from sqlmodel import select

        rbac_service = get_rbac_service()

        # Convert UUIDs to strings for database lookup
        assignment_id_str = str(assignment_id)
        role_id_str = str(assignment_update.role_id)

        # Get existing assignment to check immutability
        assignment_stmt = select(UserRoleAssignment).where(UserRoleAssignment.id == assignment_id_str)
        assignment_result = await session.execute(assignment_stmt)
        existing_assignment = assignment_result.scalar_one_or_none()
        if not existing_assignment:
            raise HTTPException(
                status_code=404,
                detail=f"Assignment {assignment_id} not found",
            )

        # Check if assignment is immutable
        if existing_assignment.is_immutable:
            raise HTTPException(
                status_code=400,
                detail="Cannot modify immutable assignment (e.g., Starter Project Owner role)",
            )

        # Validate new role exists
        role_stmt = select(Role).where(Role.id == role_id_str)
        role_result = await session.execute(role_stmt)
        role = role_result.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=400,
                detail=f"Role {assignment_update.role_id} not found",
            )

        # Update assignment
        updated_assignment = await rbac_service.update_assignment(
            assignment_id=assignment_id,
            role_id=assignment_update.role_id,
        )

        return updated_assignment

    except ValueError as exc:
        # RBACService raises ValueError for business logic errors
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update assignment: {str(exc)}",
        ) from exc


@router.delete("/assignments/{assignment_id}", status_code=204)
async def delete_assignment(
    assignment_id: UUID,
    admin_user: AdminUser,
    session: DbSession,
) -> None:
    """
    Delete a role assignment.

    Cannot delete immutable assignments. Requires Admin role.

    Args:
        assignment_id: The assignment ID to delete
        admin_user: Authenticated admin user (dependency)
        session: Database session (dependency)

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 400 if immutable, 404 if not found, 403 if not admin
    """
    try:
        from sqlmodel import select

        rbac_service = get_rbac_service()

        # Convert UUID to string for database lookup
        assignment_id_str = str(assignment_id)

        # Get assignment to check immutability
        # Workaround for UUID type issues: scan all and match by string comparison
        all_assignments_stmt = select(UserRoleAssignment)
        all_assignments_result = await session.execute(all_assignments_stmt)
        all_assignments = all_assignments_result.scalars().all()

        assignment = None
        for a in all_assignments:
            if str(a.id) == assignment_id_str:
                assignment = a
                break

        if not assignment:
            raise HTTPException(
                status_code=404,
                detail=f"Assignment {assignment_id} not found",
            )

        # Check if assignment is immutable
        if assignment.is_immutable:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete immutable assignment (e.g., Starter Project Owner role)",
            )

        # Check if this is the last Admin role assignment
        # Note: We allow deletion if there's at least one active superuser who can manage the system
        # Get the Admin role once
        admin_role_stmt = select(Role).where(Role.name == "Admin")
        admin_role_result = await session.execute(admin_role_stmt)
        admin_role = admin_role_result.scalar_one_or_none()

        # If the assignment being deleted is an Admin role, check if it's the last one
        if admin_role and str(assignment.role_id) == str(admin_role.id):
            # Count Admin assignments excluding the one being deleted
            admin_assignments = [
                a for a in all_assignments
                if str(a.role_id) == str(admin_role.id) and str(a.id) != assignment_id_str
            ]

            # Check if there are any active superusers who can still manage the system
            superuser_stmt = select(User).where(User.is_superuser == True, User.is_active == True)
            superuser_result = await session.execute(superuser_stmt)
            active_superusers = superuser_result.scalars().all()

            # Block deletion only if it's the last Admin AND there are no active superusers
            if len(admin_assignments) == 0 and len(active_superusers) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete the last Admin role assignment. At least one Admin or active Superuser must exist to manage the system.",
                )

        # Delete assignment
        await rbac_service.delete_assignment(assignment_id)

    except ValueError as exc:
        # RBACService raises ValueError for business logic errors
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete assignment: {str(exc)}",
        ) from exc


@router.get("/check-permission", response_model=PermissionCheckResponse)
async def check_permission(
    permission: str,
    scope_type: str,
    current_user: CurrentActiveUser,
    scope_id: Optional[UUID] = None,
) -> PermissionCheckResponse:
    """
    Check if the current user has a specific permission.

    Available to all authenticated users (not admin-only).

    Args:
        permission: The permission name to check (e.g., "Read", "Update", "Delete")
        scope_type: The scope type (e.g., "Flow", "Project", "Global")
        current_user: Authenticated user (dependency)
        scope_id: Optional scope ID for project/flow scopes

    Returns:
        PermissionCheckResponse with allowed=True/False

    Raises:
        HTTPException: 500 on error
    """
    try:
        rbac_service = get_rbac_service()

        allowed = await rbac_service.can_access(
            user_id=current_user.id,
            permission_name=permission,
            scope_type=scope_type,
            scope_id=scope_id,
        )

        return PermissionCheckResponse(allowed=allowed)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check permission: {str(exc)}",
        ) from exc


@router.post("/check-permissions-batch", response_model=PermissionCheckBatchResponse)
async def check_permissions_batch(
    request: PermissionCheckBatchRequest,
    current_user: CurrentActiveUser,
) -> PermissionCheckBatchResponse:
    """
    Check permission for multiple resources in a single request.

    This endpoint optimizes list view queries by reducing N individual
    permission checks to a single API call. Available to all authenticated users.

    Args:
        request: Batch permission check request with permission and resources
        current_user: Authenticated user (dependency)

    Returns:
        PermissionCheckBatchResponse with results dict mapping resource.id -> bool

    Raises:
        HTTPException: 500 on error
    """
    try:
        rbac_service = get_rbac_service()

        results: dict[str, bool] = {}

        # Check permission for each resource
        for resource in request.resources:
            # Convert scope_id from string to UUID if present
            scope_id = UUID(resource.scope_id) if resource.scope_id else None

            allowed = await rbac_service.can_access(
                user_id=current_user.id,
                permission_name=request.permission,
                scope_type=resource.scope_type,
                scope_id=scope_id,
            )

            results[resource.id] = allowed

        return PermissionCheckBatchResponse(results=results)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check permissions batch: {str(exc)}",
        ) from exc
