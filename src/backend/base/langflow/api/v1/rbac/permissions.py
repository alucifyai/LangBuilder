"""Permission management API endpoints for RBAC system."""

# NO future annotations per Phase 1 requirements
# from __future__ import annotations

from typing import TYPE_CHECKING
from langflow.schema.serialize import UUIDstr

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.api.v1.rbac.dependencies import get_permission_engine
from langflow.services.rbac.permission_engine import PermissionEngine
from langflow.services.database.models.rbac.permission import (
    Permission,
    PermissionRead,
    SYSTEM_PERMISSIONS,
)
if TYPE_CHECKING:
    from langflow.services.database.models.user.model import User

router = APIRouter(
    prefix="/permissions",
    tags=["RBAC", "Permissions"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource does not exist"},
        422: {"description": "Validation Error - Invalid request data"},
    },
)


@router.get("/", response_model=list[PermissionRead])
async def list_permissions(
    session: DbSession,
    current_user: CurrentActiveUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    resource_type: str | None = None,
    action: str | None = None,
) -> list[PermissionRead]:
    """List available permissions in the system."""
    
    # Only superusers can list all permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can list permissions"
        )

    statement = select(Permission)

    # Apply filters
    if search:
        statement = statement.where(
            (Permission.name.ilike(f"%{search}%")) |
            (Permission.description.ilike(f"%{search}%")) |
            (Permission.code.ilike(f"%{search}%"))
        )

    if resource_type:
        statement = statement.where(Permission.resource_type == resource_type)

    if action:
        statement = statement.where(Permission.action == action)

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    
    result = await session.exec(statement)
    permissions = result.all()

    return [PermissionRead.model_validate(permission) for permission in permissions]


@router.get("/{permission_id}", response_model=PermissionRead)
async def get_permission(
    permission_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> PermissionRead:
    """Get permission by ID."""
    
    # Only superusers can view permission details
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can view permission details"
        )

    permission = await session.get(Permission, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )

    return PermissionRead.model_validate(permission)


@router.post("/check", response_model=dict)
async def check_permission(
    permission_check: dict,
    session: DbSession,
    current_user: CurrentActiveUser,
    permission_engine: PermissionEngine = Depends(get_permission_engine),
) -> dict:
    """Check if current user has a specific permission."""
    
    resource_type = permission_check.get("resource_type")
    action = permission_check.get("action")
    resource_id = permission_check.get("resource_id")
    workspace_id = permission_check.get("workspace_id")
    project_id = permission_check.get("project_id")
    environment_id = permission_check.get("environment_id")

    if not resource_type or not action:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="resource_type and action are required"
        )

    # Check permission using the permission engine
    result = await permission_engine.check_permission(
        session=session,
        user=current_user,
        resource_type=resource_type,
        action=action,
        resource_id=UUIDstr(resource_id) if resource_id else None,
        workspace_id=UUIDstr(workspace_id) if workspace_id else None,
        project_id=UUIDstr(project_id) if project_id else None,
        environment_id=UUIDstr(environment_id) if environment_id else None,
    )

    return {
        "allowed": result.allowed,
        "reason": result.reason,
        "cached": result.cached,
    }


@router.post("/batch-check", response_model=list[dict])
async def batch_check_permissions(
    permission_checks: list[dict],
    session: DbSession,
    current_user: CurrentActiveUser,
    permission_engine: PermissionEngine = Depends(get_permission_engine),
) -> list[dict]:
    """Check multiple permissions at once for better performance."""
    
    if len(permission_checks) > 50:  # Reasonable batch limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 permission checks allowed per batch"
        )

    results = []
    
    for check in permission_checks:
        resource_type = check.get("resource_type")
        action = check.get("action")
        resource_id = check.get("resource_id")
        workspace_id = check.get("workspace_id")
        project_id = check.get("project_id")
        environment_id = check.get("environment_id")

        if not resource_type or not action:
            results.append({
                "allowed": False,
                "reason": "Invalid request: resource_type and action are required",
                "cached": False,
            })
            continue

        try:
            # Check permission using the permission engine
            result = await permission_engine.check_permission(
                session=session,
                user=current_user,
                resource_type=resource_type,
                action=action,
                resource_id=UUIDstr(resource_id) if resource_id else None,
                workspace_id=UUIDstr(workspace_id) if workspace_id else None,
                project_id=UUIDstr(project_id) if project_id else None,
                environment_id=UUIDstr(environment_id) if environment_id else None,
            )

            results.append({
                "allowed": result.allowed,
                "reason": result.reason,
                "cached": result.cached,
            })
        except Exception as e:
            results.append({
                "allowed": False,
                "reason": f"Error checking permission: {str(e)}",
                "cached": False,
            })

    return results


@router.post("/initialize-system-permissions", status_code=status.HTTP_201_CREATED)
async def initialize_system_permissions(
    session: DbSession,
    current_user: CurrentActiveUser,
) -> dict:
    """Initialize system permissions."""
    
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can initialize system permissions"
        )

    created_permissions = 0

    # Create system permissions
    for perm_data in SYSTEM_PERMISSIONS:
        statement = select(Permission).where(Permission.code == perm_data["code"])
        result = await session.exec(statement)
        existing = result.first()

        if not existing:
            permission = Permission(
                **perm_data,
                is_system=True
            )
            session.add(permission)
            created_permissions += 1

    await session.commit()

    return {
        "message": "System permissions initialized",
        "permissions_created": created_permissions
    }


@router.get("/resource-types", response_model=list[str])
async def list_resource_types(
    session: DbSession,
    current_user: CurrentActiveUser,
) -> list[str]:
    """List available resource types."""
    
    statement = select(Permission.resource_type).distinct()
    result = await session.exec(statement)
    resource_types = result.all()

    return sorted([rt for rt in resource_types if rt])


@router.get("/actions", response_model=list[str])
async def list_actions(
    session: DbSession,
    current_user: CurrentActiveUser,
    resource_type: str | None = Query(None),
) -> list[str]:
    """List available actions, optionally filtered by resource type."""
    
    statement = select(Permission.action).distinct()
    
    if resource_type:
        statement = statement.where(Permission.resource_type == resource_type)
    
    result = await session.exec(statement)
    actions = result.all()

    return sorted([action for action in actions if action])