"""Role Assignment management API endpoints for RBAC system."""

from typing import TYPE_CHECKING
from langflow.schema.serialize import UUIDstr

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select, and_, or_
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.api.v1.rbac.dependencies import (
    check_workspace_permission,
    get_permission_engine,
)
from langflow.services.rbac.permission_engine import PermissionEngine
from langflow.services.database.models.rbac.role_assignment import (
    RoleAssignment,
    RoleAssignmentCreate,
    RoleAssignmentRead,
    RoleAssignmentUpdate,
    RoleAssignmentApproval,
    AssignmentType,
    AssignmentScope,
)
from langflow.services.database.models.rbac.role import Role
from langflow.services.database.models.rbac.workspace import Workspace

if TYPE_CHECKING:
    from langflow.services.database.models.user.model import User

router = APIRouter(
    prefix="/role-assignments",
    tags=["RBAC", "Role Assignments"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource does not exist"},
        422: {"description": "Validation Error - Invalid request data"},
    },
)


@router.get("/", response_model=list[RoleAssignmentRead])
async def list_role_assignments(
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace_id: UUIDstr,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: UUIDstr | None = None,
    role_id: UUIDstr | None = None,
    assignment_type: AssignmentType | None = None,
    scope: AssignmentScope | None = None,
    is_active: bool | None = None,
) -> list[RoleAssignmentRead]:
    """List role assignments in a workspace."""
    
    # Check workspace permission
    await check_workspace_permission(session, current_user, workspace_id, "role_assignment:read")

    statement = select(RoleAssignment).where(RoleAssignment.workspace_id == workspace_id)

    # Apply filters
    if user_id:
        statement = statement.where(RoleAssignment.user_id == user_id)

    if role_id:
        statement = statement.where(RoleAssignment.role_id == role_id)

    if assignment_type:
        statement = statement.where(RoleAssignment.assignment_type == assignment_type)

    if scope:
        statement = statement.where(RoleAssignment.scope == scope)

    if is_active is not None:
        statement = statement.where(RoleAssignment.is_active == is_active)

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    
    result = await session.exec(statement)
    assignments = result.all()

    return [RoleAssignmentRead.model_validate(assignment) for assignment in assignments]


@router.post("/", response_model=RoleAssignmentRead, status_code=status.HTTP_201_CREATED)
async def create_role_assignment(
    assignment_data: RoleAssignmentCreate,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> RoleAssignmentRead:
    """Create a new role assignment."""
    
    # Check workspace permission
    await check_workspace_permission(
        session, current_user, assignment_data.workspace_id, "role_assignment:create"
    )

    # Verify workspace exists
    workspace = await session.get(Workspace, assignment_data.workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Verify role exists
    role = await session.get(Role, assignment_data.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Check for duplicate assignment
    statement = select(RoleAssignment).where(
        and_(
            RoleAssignment.workspace_id == assignment_data.workspace_id,
            RoleAssignment.user_id == assignment_data.user_id,
            RoleAssignment.role_id == assignment_data.role_id,
            RoleAssignment.scope == assignment_data.scope,
            RoleAssignment.scope_id == assignment_data.scope_id,
            RoleAssignment.is_active == True
        )
    )
    result = await session.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has this role assignment with the same scope"
        )

    # Create role assignment
    assignment = RoleAssignment(
        **assignment_data.model_dump(),
        assigned_by=current_user.id
    )
    
    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)

    return RoleAssignmentRead.model_validate(assignment)


@router.get("/{assignment_id}", response_model=RoleAssignmentRead)
async def get_role_assignment(
    assignment_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> RoleAssignmentRead:
    """Get role assignment by ID."""
    
    assignment = await session.get(RoleAssignment, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role assignment not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, assignment.workspace_id, "role_assignment:read"
    )

    return RoleAssignmentRead.model_validate(assignment)


@router.put("/{assignment_id}", response_model=RoleAssignmentRead)
async def update_role_assignment(
    assignment_id: UUIDstr,
    assignment_data: RoleAssignmentUpdate,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> RoleAssignmentRead:
    """Update role assignment."""
    
    assignment = await session.get(RoleAssignment, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role assignment not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, assignment.workspace_id, "role_assignment:update"
    )

    # Update fields
    update_data = assignment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)

    await session.commit()
    await session.refresh(assignment)

    return RoleAssignmentRead.model_validate(assignment)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role_assignment(
    assignment_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> None:
    """Delete role assignment (deactivate)."""
    
    assignment = await session.get(RoleAssignment, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role assignment not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, assignment.workspace_id, "role_assignment:delete"
    )

    # Soft delete by setting is_active to False
    assignment.is_active = False
    await session.commit()


@router.get("/user/{user_id}", response_model=list[RoleAssignmentRead])
async def list_user_role_assignments(
    user_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace_id: UUIDstr | None = None,
    include_inherited: bool = Query(True, description="Include inherited role assignments"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[RoleAssignmentRead]:
    """List all role assignments for a specific user."""
    
    # If workspace_id is provided, check permission for that workspace
    # Otherwise, user can only see their own assignments
    if workspace_id:
        await check_workspace_permission(session, current_user, workspace_id, "role_assignment:read")
        statement = select(RoleAssignment).where(
            and_(
                RoleAssignment.user_id == user_id,
                RoleAssignment.workspace_id == workspace_id,
                RoleAssignment.is_active == True
            )
        )
    else:
        # Users can only see their own assignments unless they're superuser
        if user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view your own role assignments"
            )
        statement = select(RoleAssignment).where(
            and_(
                RoleAssignment.user_id == user_id,
                RoleAssignment.is_active == True
            )
        )

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    
    result = await session.exec(statement)
    assignments = result.all()

    return [RoleAssignmentRead.model_validate(assignment) for assignment in assignments]


@router.post("/{assignment_id}/approve", response_model=RoleAssignmentRead)
async def approve_role_assignment(
    assignment_id: UUIDstr,
    approval_data: RoleAssignmentApproval,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> RoleAssignmentRead:
    """Approve a pending role assignment."""
    
    assignment = await session.get(RoleAssignment, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role assignment not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, assignment.workspace_id, "role_assignment:approve"
    )

    # Update approval status
    from datetime import datetime
    assignment.approved_by = current_user.id
    assignment.approved_at = datetime.utcnow()
    assignment.approval_reason = approval_data.reason
    assignment.is_active = True

    await session.commit()
    await session.refresh(assignment)

    return RoleAssignmentRead.model_validate(assignment)


@router.post("/{assignment_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_role_assignment(
    assignment_id: UUIDstr,
    approval_data: RoleAssignmentApproval,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> None:
    """Reject a pending role assignment."""
    
    assignment = await session.get(RoleAssignment, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role assignment not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, assignment.workspace_id, "role_assignment:approve"
    )

    # Update rejection status
    from datetime import datetime
    assignment.approved_by = current_user.id
    assignment.approved_at = datetime.utcnow()
    assignment.approval_reason = approval_data.reason
    assignment.is_active = False

    await session.commit()


@router.get("/pending", response_model=list[RoleAssignmentRead])
async def list_pending_assignments(
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace_id: UUIDstr,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[RoleAssignmentRead]:
    """List pending role assignments requiring approval."""
    
    # Check workspace permission
    await check_workspace_permission(session, current_user, workspace_id, "role_assignment:approve")

    statement = select(RoleAssignment).where(
        and_(
            RoleAssignment.workspace_id == workspace_id,
            RoleAssignment.approved_by.is_(None),
            RoleAssignment.is_active == False
        )
    ).offset(skip).limit(limit)
    
    result = await session.exec(statement)
    assignments = result.all()

    return [RoleAssignmentRead.model_validate(assignment) for assignment in assignments]


@router.post("/bulk", response_model=list[RoleAssignmentRead], status_code=status.HTTP_201_CREATED)
async def bulk_create_role_assignments(
    assignments_data: list[RoleAssignmentCreate],
    session: DbSession,
    current_user: CurrentActiveUser,
) -> list[RoleAssignmentRead]:
    """Create multiple role assignments at once."""
    
    if len(assignments_data) > 50:  # Reasonable bulk limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 role assignments allowed per bulk operation"
        )

    created_assignments = []
    
    for assignment_data in assignments_data:
        try:
            # Check workspace permission for each assignment
            await check_workspace_permission(
                session, current_user, assignment_data.workspace_id, "role_assignment:create"
            )

            # Create assignment
            assignment = RoleAssignment(
                **assignment_data.model_dump(),
                assigned_by=current_user.id
            )
            
            session.add(assignment)
            created_assignments.append(assignment)
            
        except Exception as e:
            # If any assignment fails, rollback all
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create role assignment: {str(e)}"
            )

    await session.commit()
    
    # Refresh all assignments
    for assignment in created_assignments:
        await session.refresh(assignment)

    return [RoleAssignmentRead.model_validate(assignment) for assignment in created_assignments]