"""Permission management API endpoints for RBAC system."""

from fastapi import APIRouter
import uuid

from langflow.services.database.models.rbac.permission import PermissionRead, ResourceType, PermissionAction

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