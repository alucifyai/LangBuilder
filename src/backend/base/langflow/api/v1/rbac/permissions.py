"""Permission management API endpoints for RBAC system."""

from fastapi import APIRouter
import uuid
from typing import Union
from pydantic import BaseModel

from langflow.services.database.models.rbac.permission import PermissionRead, ResourceType, PermissionAction


class CheckPermissionRequest(BaseModel):
    """Request model for permission checking."""

    resource_type: str
    action: str
    resource_id: Union[str, None] = None
    workspace_id: Union[str, None] = None
    project_id: Union[str, None] = None
    environment_id: Union[str, None] = None


class PermissionResult(BaseModel):
    """Result model for permission checking."""

    allowed: bool
    reason: Union[str, None] = None
    cached: Union[bool, None] = None


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
    workspace_id: str = "00000000-0000-0000-0000-000000000000",
    limit: int = 10,
) -> list[PermissionRead]:
    """List available permissions in the system."""
    # Return sample permissions for testing the UI with correct types
    sample_permissions = [
        PermissionRead(
            id=str(uuid.uuid4()),
            name="Read Flows",
            code="flows.read",
            description="View and list flows in the workspace",
            category="Flow Management",
            resource_type=ResourceType.FLOW,
            action=PermissionAction.READ,
            scope="*",
            conditions={},
            is_system=True,
            is_dangerous=False,
            requires_mfa=False,
            role_count=0
        ),
        PermissionRead(
            id=str(uuid.uuid4()),
            name="Write Flows",
            code="flows.update",
            description="Create, update, and modify flows",
            category="Flow Management",
            resource_type=ResourceType.FLOW,
            action=PermissionAction.UPDATE,
            scope="*",
            conditions={},
            is_system=True,
            is_dangerous=False,
            requires_mfa=False,
            role_count=0
        ),
        PermissionRead(
            id=str(uuid.uuid4()),
            name="Delete Flows",
            code="flows.delete",
            description="Delete flows from the workspace",
            category="Flow Management",
            resource_type=ResourceType.FLOW,
            action=PermissionAction.DELETE,
            scope="*",
            conditions={},
            is_system=True,
            is_dangerous=True,
            requires_mfa=True,
            role_count=0
        ),
        PermissionRead(
            id=str(uuid.uuid4()),
            name="Execute Flows",
            code="flows.execute",
            description="Run and execute flows",
            category="Flow Management",
            resource_type=ResourceType.FLOW,
            action=PermissionAction.EXECUTE,
            scope="*",
            conditions={},
            is_system=True,
            is_dangerous=False,
            requires_mfa=False,
            role_count=0
        ),
        PermissionRead(
            id=str(uuid.uuid4()),
            name="Read Workspace",
            code="workspace.read",
            description="View workspace information and settings",
            category="Workspace Management",
            resource_type=ResourceType.WORKSPACE,
            action=PermissionAction.READ,
            scope="*",
            conditions={},
            is_system=True,
            is_dangerous=False,
            requires_mfa=False,
            role_count=0
        ),
        PermissionRead(
            id=str(uuid.uuid4()),
            name="Manage Workspace",
            code="workspace.manage",
            description="Modify workspace settings and configuration",
            category="Workspace Management",
            resource_type=ResourceType.WORKSPACE,
            action=PermissionAction.MANAGE,
            scope="*",
            conditions={},
            is_system=True,
            is_dangerous=True,
            requires_mfa=True,
            role_count=0
        ),
        PermissionRead(
            id=str(uuid.uuid4()),
            name="Read Projects",
            code="project.read",
            description="View project information",
            category="Project Management",
            resource_type=ResourceType.PROJECT,
            action=PermissionAction.READ,
            scope="*",
            conditions={},
            is_system=True,
            is_dangerous=False,
            requires_mfa=False,
            role_count=0
        ),
        PermissionRead(
            id=str(uuid.uuid4()),
            name="Create Projects",
            code="project.create",
            description="Create new projects",
            category="Project Management",
            resource_type=ResourceType.PROJECT,
            action=PermissionAction.CREATE,
            scope="*",
            conditions={},
            is_system=True,
            is_dangerous=False,
            requires_mfa=False,
            role_count=0
        )
    ]

    return sample_permissions


@router.post("/check-permission", response_model=PermissionResult)
async def check_permission(
    request: CheckPermissionRequest,
) -> PermissionResult:
    """
    Check if the current user has permission to perform an action on a resource.

    This endpoint evaluates user permissions based on their roles and the
    requested resource/action combination. For now, it returns a simplified
    response to make the frontend work.
    """
    try:
        # For now, implement a simplified permission check
        # In a full RBAC implementation, this would:
        # 1. Get current user from authentication context
        # 2. Query user's roles and permissions
        # 3. Evaluate permission against resource/action/context
        # 4. Return detailed result with reasoning

        # Simple logic: allow most operations for development
        allowed = True
        reason = "Permission granted for development"

        # Example of more restrictive logic (can be enhanced):
        dangerous_actions = ["delete", "destroy", "break_glass"]
        if request.action.lower() in dangerous_actions:
            allowed = False
            reason = f"Action '{request.action}' requires elevated privileges"

        return PermissionResult(
            allowed=allowed,
            reason=reason,
            cached=False
        )

    except Exception as e:
        # Log error and return denied for security
        return PermissionResult(
            allowed=False,
            reason=f"Permission check failed: {str(e)}",
            cached=False
        )
