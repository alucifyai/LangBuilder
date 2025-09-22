"""Role Assignment management API endpoints for RBAC system."""

from fastapi import APIRouter

from langflow.services.database.models.rbac.role_assignment import RoleAssignmentRead

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
    workspace_id: str = "00000000-0000-0000-0000-000000000000",
    limit: int = 10,
) -> list[RoleAssignmentRead]:
    """List role assignments in a workspace."""
    # Simple test endpoint
    return []
