"""RBAC Management API Endpoints.

This module provides admin-only API endpoints for managing role-based access control (RBAC)
assignments in the LangBuilder system. All endpoints require superuser privileges.

Endpoints:
- GET /api/v1/rbac/roles - List all available roles
- GET /api/v1/rbac/assignments - List role assignments with optional filtering
- GET /api/v1/rbac/assignments/{assignment_id} - Get single role assignment
- POST /api/v1/rbac/assignments - Create new role assignment
- PUT /api/v1/rbac/assignments/{assignment_id} - Update existing role assignment
- DELETE /api/v1/rbac/assignments/{assignment_id} - Delete role assignment
- GET /api/v1/rbac/check-permission - Check if current user has permission

Implements PRD Epic 3: Admin UI for RBAC Management (backend support)
"""
# ruff: noqa: ARG001, FAST001, TRY300

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from langbuilder.api.utils import CurrentActiveUser, DbSession
from langbuilder.api.v1.schemas import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
    PermissionCheckRequest,
    PermissionCheckResponse,
)
from langbuilder.services.auth.utils import get_current_active_superuser
from langbuilder.services.database.models.folder.constants import DEFAULT_FOLDER_NAME
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.rbac.model import (
    Role,
    RoleEnum,
    RoleRead,
    ScopeTypeEnum,
    UserRoleAssignment,
)
from langbuilder.services.database.models.user.model import User
from langbuilder.services.deps import get_rbac_service
from langbuilder.services.rbac.service import RBACService

router = APIRouter(prefix="/rbac", tags=["RBAC"])

# API Endpoints
# Note: Request/Response schemas are now defined in langbuilder.api.v1.schemas


@router.get("/roles", response_model=list[RoleRead])
async def list_roles(
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    session: DbSession,
) -> list[Role]:
    """List all available roles.

    Admin-only endpoint per PRD Epic 3 Story 3.1.

    Args:
        current_user: Current authenticated superuser
        session: Database session

    Returns:
        List of all roles in the system

    Raises:
        HTTPException 403: If user is not a superuser
    """
    try:
        result = await session.exec(select(Role))
        roles = result.all()
        return list(roles)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching roles: {e!s}"
        ) from e


@router.get("/assignments", response_model=list[AssignmentResponse])
async def list_assignments(
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    session: DbSession,
    user_id: UUID | None = None,
    role_name: RoleEnum | None = None,
    scope_type: ScopeTypeEnum | None = None,
    scope_id: UUID | None = None,
) -> list[AssignmentResponse]:
    """List role assignments with optional filtering.

    Admin-only endpoint per PRD Epic 3 Story 3.3.
    Supports filtering by user_id, role_name, scope_type, and scope_id.

    Args:
        current_user: Current authenticated superuser
        session: Database session
        user_id: Optional filter by user ID
        role_name: Optional filter by role name
        scope_type: Optional filter by scope type
        scope_id: Optional filter by scope ID

    Returns:
        List of role assignments matching filters

    Raises:
        HTTPException 403: If user is not a superuser
    """
    try:
        stmt = select(UserRoleAssignment).join(Role)

        # Apply filters
        if user_id:
            stmt = stmt.where(UserRoleAssignment.user_id == user_id)
        if role_name:
            stmt = stmt.where(Role.name == role_name)
        if scope_type:
            stmt = stmt.where(UserRoleAssignment.scope_type == scope_type)
        if scope_id:
            stmt = stmt.where(UserRoleAssignment.scope_id == scope_id)

        result = await session.exec(stmt)
        assignments = result.all()

        # Build response with role names
        response = []
        for assignment in assignments:
            # Fetch role to get name
            role = await session.get(Role, assignment.role_id)
            response.append(
                AssignmentResponse(
                    id=assignment.id,
                    user_id=assignment.user_id,
                    role_id=assignment.role_id,
                    role_name=role.name if role else RoleEnum.VIEWER,  # Fallback
                    scope_type=assignment.scope_type,
                    scope_id=assignment.scope_id,
                    is_immutable=assignment.is_immutable,
                    created_at=assignment.created_at.isoformat(),
                )
            )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching assignments: {e!s}"
        ) from e


@router.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    session: DbSession,
) -> AssignmentResponse:
    """Get a single role assignment by ID.

    Admin-only endpoint.

    Args:
        assignment_id: ID of assignment to retrieve
        current_user: Current authenticated superuser
        session: Database session

    Returns:
        Role assignment details

    Raises:
        HTTPException 404: If assignment not found
        HTTPException 403: If user is not a superuser
    """
    try:
        assignment = await session.get(UserRoleAssignment, assignment_id)

        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        # Fetch role to get name
        role = await session.get(Role, assignment.role_id)

        return AssignmentResponse(
            id=assignment.id,
            user_id=assignment.user_id,
            role_id=assignment.role_id,
            role_name=role.name if role else RoleEnum.VIEWER,
            scope_type=assignment.scope_type,
            scope_id=assignment.scope_id,
            is_immutable=assignment.is_immutable,
            created_at=assignment.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching assignment: {e!s}"
        ) from e


@router.post("/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assignment: AssignmentCreate,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    session: DbSession,
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
) -> AssignmentResponse:
    """Create new role assignment.

    Admin-only endpoint per PRD Epic 3 Story 3.2.
    Cannot assign to immutable scopes per PRD Story 1.4.

    Args:
        assignment: Assignment creation request
        current_user: Current authenticated superuser
        session: Database session
        rbac_service: RBAC service for assignment creation

    Returns:
        Created role assignment

    Raises:
        HTTPException 400: If assignment violates constraints (duplicate, immutable scope)
        HTTPException 403: If user is not a superuser
        HTTPException 404: If user or scope not found
    """
    try:
        # Validate user exists
        user = await session.get(User, assignment.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check if attempting to assign to Default Project (immutable)
        if assignment.scope_type == ScopeTypeEnum.PROJECT and assignment.scope_id:
            project = await session.get(Folder, assignment.scope_id)
            if not project:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

            # Check if this is Default Project with existing immutable assignment
            if project.name == DEFAULT_FOLDER_NAME:
                existing_stmt = select(UserRoleAssignment).where(
                    UserRoleAssignment.user_id == assignment.user_id,
                    UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                    UserRoleAssignment.scope_id == assignment.scope_id,
                    UserRoleAssignment.is_immutable == True,  # noqa: E712
                )
                existing_result = await session.exec(existing_stmt)
                if existing_result.first():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot modify Default Project Owner assignment (immutable)",
                    )

        # Create assignment via RBACService
        new_assignment = await rbac_service.assign_role(
            session,
            assignment.user_id,
            assignment.role_name,
            assignment.scope_type,
            assignment.scope_id,
            is_immutable=False,  # Admin-created assignments are not immutable
        )

        # Fetch role to get name
        role = await session.get(Role, new_assignment.role_id)

        return AssignmentResponse(
            id=new_assignment.id,
            user_id=new_assignment.user_id,
            role_id=new_assignment.role_id,
            role_name=role.name if role else assignment.role_name,
            scope_type=new_assignment.scope_type,
            scope_id=new_assignment.scope_id,
            is_immutable=new_assignment.is_immutable,
            created_at=new_assignment.created_at.isoformat(),
        )

    except ValueError as e:
        # RBACService raises ValueError for duplicate assignments or invalid role
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating assignment: {e!s}"
        ) from e


@router.put("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    assignment_update: AssignmentUpdate,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    session: DbSession,
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
) -> AssignmentResponse:
    """Update role in existing assignment.

    Admin-only endpoint per PRD Epic 3 Story 3.2.
    Cannot modify immutable assignments per PRD Story 1.4.

    Args:
        assignment_id: ID of assignment to update
        assignment_update: Update request with new role
        current_user: Current authenticated superuser
        session: Database session
        rbac_service: RBAC service for assignment update

    Returns:
        Updated role assignment

    Raises:
        HTTPException 400: If assignment is immutable
        HTTPException 404: If assignment not found (returns 404 for security)
        HTTPException 403: If user is not a superuser
    """
    try:
        # Check if assignment exists first
        existing = await session.get(UserRoleAssignment, assignment_id)
        if not existing:
            # Return 404 for security (don't leak existence)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        # Update via RBACService (handles immutability check)
        updated_assignment = await rbac_service.update_assignment(
            session,
            assignment_id,
            assignment_update.new_role_name,
        )

        # Fetch role to get name
        role = await session.get(Role, updated_assignment.role_id)

        return AssignmentResponse(
            id=updated_assignment.id,
            user_id=updated_assignment.user_id,
            role_id=updated_assignment.role_id,
            role_name=role.name if role else assignment_update.new_role_name,
            scope_type=updated_assignment.scope_type,
            scope_id=updated_assignment.scope_id,
            is_immutable=updated_assignment.is_immutable,
            created_at=updated_assignment.created_at.isoformat(),
        )

    except ValueError as e:
        # RBACService raises ValueError for immutable assignments
        error_msg = str(e)
        if "immutable" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg) from e
        if "not found" in error_msg.lower():
            # Return 404 for security
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found") from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating assignment: {e!s}"
        ) from e


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    session: DbSession,
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
) -> None:
    """Delete role assignment.

    Admin-only endpoint per PRD Epic 3 Story 3.3.
    Cannot delete immutable assignments per PRD Story 1.4.

    Args:
        assignment_id: ID of assignment to delete
        current_user: Current authenticated superuser
        session: Database session
        rbac_service: RBAC service for assignment deletion

    Raises:
        HTTPException 403: If assignment is immutable
        HTTPException 404: If assignment not found (returns 404 for security)
    """
    try:
        # Check if assignment exists first
        existing = await session.get(UserRoleAssignment, assignment_id)
        if not existing:
            # Return 404 for security (don't leak existence)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        # Delete via RBACService (handles immutability check)
        await rbac_service.remove_role(session, assignment_id)

    except ValueError as e:
        # RBACService raises ValueError for immutable assignments or not found
        error_msg = str(e)
        if "immutable" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg) from e
        if "not found" in error_msg.lower():
            # Return 404 for security
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found") from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting assignment: {e!s}"
        ) from e


@router.post("/check-permission", response_model=PermissionCheckResponse)
async def check_permission(
    request: PermissionCheckRequest,
    current_user: CurrentActiveUser,
    session: DbSession,
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
) -> PermissionCheckResponse:
    """Check if current user has permission for scope.

    Available to all authenticated users (not admin-only).
    Used by frontend to determine UI visibility and capabilities.

    Args:
        request: Permission check request
        current_user: Current authenticated user
        session: Database session
        rbac_service: RBAC service for permission checking

    Returns:
        Permission check result
    """
    try:
        has_permission = await rbac_service.can_access(
            session,
            current_user.id,
            request.permission,
            request.scope_type,
            request.scope_id,
        )

        return PermissionCheckResponse(
            has_permission=has_permission,
            user_id=current_user.id,
            permission=request.permission,
            scope_type=request.scope_type,
            scope_id=request.scope_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error checking permission: {e!s}"
        ) from e
