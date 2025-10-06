from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from langflow.api.utils import DbSession
from langflow.services.database.models.permission.crud import get_all_permissions
from langflow.services.database.models.permission.model import Permission

router = APIRouter(tags=["Permissions"], prefix="/permissions")


class PermissionResponse(BaseModel):
    """Response model for a permission."""

    id: str
    resource_type: str
    action: str
    description: str


class PermissionsListResponse(BaseModel):
    """Response model for list of permissions."""

    total_count: int
    permissions: list[PermissionResponse]


@router.get("/", response_model=PermissionsListResponse)
async def list_permissions(
    db: DbSession,
) -> PermissionsListResponse:
    """
    Get all available permissions from the catalog.

    This endpoint returns the complete permission catalog that can be used
    when building roles.
    """
    try:
        permissions = await get_all_permissions(db)

        permission_responses = [
            PermissionResponse(
                id=p.id,
                resource_type=p.resource_type,
                action=p.action,
                description=p.description,
            )
            for p in permissions
        ]

        return PermissionsListResponse(
            total_count=len(permission_responses),
            permissions=permission_responses,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
