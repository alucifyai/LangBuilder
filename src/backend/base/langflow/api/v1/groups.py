"""
Group Management API
Endpoints for creating and managing user groups
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.group import (
    Group,
    add_user_to_group,
    create_group,
    delete_group,
    get_group,
    get_group_by_name,
    get_group_members,
    get_user_groups,
    list_groups,
    remove_user_from_group,
    update_group,
)
from langflow.services.deps import get_session

router = APIRouter(prefix="/groups", tags=["Groups"])


# Request/Response models
class CreateGroupRequest(BaseModel):
    """Request to create a group"""

    name: str
    description: str | None = None
    organization_id: str | None = None


class UpdateGroupRequest(BaseModel):
    """Request to update a group"""

    name: str | None = None
    description: str | None = None


class GroupResponse(BaseModel):
    """Group response"""

    id: str
    name: str
    description: str | None
    organization_id: str | None
    created_at: str
    updated_at: str


class AddMemberRequest(BaseModel):
    """Request to add member to group"""

    user_id: str


def group_to_response(group: Group) -> GroupResponse:
    """Convert Group to response"""
    return GroupResponse(
        id=str(group.id),
        name=group.name,
        description=group.description,
        organization_id=group.organization_id,
        created_at=group.created_at.isoformat(),
        updated_at=group.updated_at.isoformat(),
    )


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group_endpoint(
    request: CreateGroupRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new group
    """
    # Check if group name already exists
    existing = await get_group_by_name(session, request.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Group with name '{request.name}' already exists",
        )

    group = await create_group(
        session=session,
        name=request.name,
        description=request.description,
        organization_id=request.organization_id,
    )

    return group_to_response(group)


@router.get("", response_model=list[GroupResponse])
async def list_groups_endpoint(
    organization_id: str | None = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """
    List all groups
    """
    groups = await list_groups(
        session=session,
        organization_id=organization_id,
        limit=limit,
    )
    return [group_to_response(g) for g in groups]


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group_endpoint(
    group_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get a group by ID
    """
    group = await get_group(session, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )

    return group_to_response(group)


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group_endpoint(
    group_id: UUID,
    request: UpdateGroupRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Update a group
    """
    group = await get_group(session, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )

    # Check name uniqueness if updating name
    if request.name and request.name != group.name:
        existing = await get_group_by_name(session, request.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Group with name '{request.name}' already exists",
            )

    group = await update_group(
        session=session,
        group=group,
        name=request.name,
        description=request.description,
    )

    return group_to_response(group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group_endpoint(
    group_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a group
    """
    group = await get_group(session, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )

    await delete_group(session, group)


@router.post("/{group_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member_endpoint(
    group_id: UUID,
    request: AddMemberRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Add a user to a group
    """
    group = await get_group(session, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )

    try:
        user_id = UUID(request.user_id)
        await add_user_to_group(session, group_id, user_id)
        return {"message": "User added to group"}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_endpoint(
    group_id: UUID,
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Remove a user from a group
    """
    group = await get_group(session, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )

    await remove_user_from_group(session, group_id, user_id)


@router.get("/{group_id}/members", response_model=list[str])
async def get_group_members_endpoint(
    group_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get all members of a group
    """
    group = await get_group(session, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )

    member_ids = await get_group_members(session, group_id)
    return [str(uid) for uid in member_ids]


@router.get("/users/{user_id}/groups", response_model=list[str])
async def get_user_groups_endpoint(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get all groups a user belongs to
    """
    group_ids = await get_user_groups(session, user_id)
    return [str(gid) for gid in group_ids]
