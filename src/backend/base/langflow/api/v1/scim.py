"""
SCIM 2.0 API Endpoints
System for Cross-domain Identity Management
Implements RFC 7643 and RFC 7644
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.scim import (
    SCIMGroup,
    SCIMUser,
    create_scim_group,
    create_scim_group_membership,
    create_scim_user,
    delete_scim_group,
    delete_scim_user,
    get_scim_group_by_external_id,
    get_scim_user_by_external_id,
    list_scim_groups,
    list_scim_users,
    log_scim_event,
    update_scim_group,
    update_scim_user,
)
from langflow.services.deps import get_session

router = APIRouter(prefix="/scim/v2", tags=["SCIM"])


# SCIM 2.0 Schema models
class SCIMUserName(BaseModel):
    """SCIM User name schema"""

    formatted: str | None = None
    familyName: str | None = None
    givenName: str | None = None
    middleName: str | None = None
    honorificPrefix: str | None = None
    honorificSuffix: str | None = None


class SCIMEmail(BaseModel):
    """SCIM Email schema"""

    value: str
    type: str = "work"
    primary: bool = True


class SCIMMeta(BaseModel):
    """SCIM Meta schema"""

    resourceType: str
    created: str | None = None
    lastModified: str | None = None
    location: str | None = None


class SCIMUserRequest(BaseModel):
    """SCIM User creation/update request"""

    schemas: list[str] = ["urn:ietf:params:scim:schemas:core:2.0:User"]
    externalId: str
    userName: str
    name: SCIMUserName | None = None
    displayName: str | None = None
    emails: list[SCIMEmail]
    active: bool = True


class SCIMUserResponse(BaseModel):
    """SCIM User response"""

    schemas: list[str] = ["urn:ietf:params:scim:schemas:core:2.0:User"]
    id: str
    externalId: str
    userName: str
    name: SCIMUserName | None = None
    displayName: str | None = None
    emails: list[SCIMEmail]
    active: bool
    meta: SCIMMeta


class SCIMGroupMember(BaseModel):
    """SCIM Group member"""

    value: str  # User ID
    ref: str = Field(alias="$ref")  # User resource URL
    type: str = "User"


class SCIMGroupRequest(BaseModel):
    """SCIM Group creation/update request"""

    schemas: list[str] = ["urn:ietf:params:scim:schemas:core:2.0:Group"]
    externalId: str
    displayName: str
    members: list[SCIMGroupMember] | None = None


class SCIMGroupResponse(BaseModel):
    """SCIM Group response"""

    schemas: list[str] = ["urn:ietf:params:scim:schemas:core:2.0:Group"]
    id: str
    externalId: str
    displayName: str
    members: list[SCIMGroupMember] | None = None
    meta: SCIMMeta


class SCIMListResponse(BaseModel):
    """SCIM List response"""

    schemas: list[str] = ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    totalResults: int
    startIndex: int = 1
    itemsPerPage: int
    Resources: list[Any]


class SCIMError(BaseModel):
    """SCIM Error response"""

    schemas: list[str] = ["urn:ietf:params:scim:api:messages:2.0:Error"]
    detail: str
    status: int


def scim_user_to_response(user: SCIMUser, base_url: str = "/api/v1") -> SCIMUserResponse:
    """Convert SCIMUser to SCIM response"""
    return SCIMUserResponse(
        id=str(user.id),
        externalId=user.external_id,
        userName=user.username,
        name=SCIMUserName(
            givenName=user.given_name,
            familyName=user.family_name,
        )
        if user.given_name or user.family_name
        else None,
        displayName=user.display_name,
        emails=[SCIMEmail(value=user.email, type="work", primary=True)],
        active=user.active,
        meta=SCIMMeta(
            resourceType="User",
            created=user.created_at.isoformat() if user.created_at else None,
            lastModified=user.updated_at.isoformat() if user.updated_at else None,
            location=f"{base_url}/scim/v2/Users/{user.id}",
        ),
    )


def scim_group_to_response(group: SCIMGroup, base_url: str = "/api/v1") -> SCIMGroupResponse:
    """Convert SCIMGroup to SCIM response"""
    return SCIMGroupResponse(
        id=str(group.id),
        externalId=group.external_id,
        displayName=group.display_name,
        members=None,  # TODO: populate from memberships
        meta=SCIMMeta(
            resourceType="Group",
            created=group.created_at.isoformat() if group.created_at else None,
            lastModified=group.updated_at.isoformat() if group.updated_at else None,
            location=f"{base_url}/scim/v2/Groups/{group.id}",
        ),
    )


# User endpoints
@router.post("/Users", response_model=SCIMUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(request: SCIMUserRequest, session: AsyncSession = Depends(get_session)):
    """
    SCIM 2.0 Create User
    Provisions a new user from IdP
    """
    try:
        # Extract email
        email = request.emails[0].value if request.emails else request.userName

        # Create SCIM user
        scim_user = await create_scim_user(
            session=session,
            external_id=request.externalId,
            username=request.userName,
            email=email,
            given_name=request.name.givenName if request.name else None,
            family_name=request.name.familyName if request.name else None,
            display_name=request.displayName,
            active=request.active,
        )

        # Log event
        await log_scim_event(
            session=session,
            event_type="create_user",
            resource_type="User",
            status="success",
            external_id=request.externalId,
        )

        return scim_user_to_response(scim_user)
    except Exception as e:
        # Log error
        await log_scim_event(
            session=session,
            event_type="create_user",
            resource_type="User",
            status="error",
            external_id=request.externalId,
            error_message=str(e),
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/Users/{user_id}", response_model=SCIMUserResponse)
async def get_user(user_id: UUID, session: AsyncSession = Depends(get_session)):
    """
    SCIM 2.0 Get User
    Retrieve user by ID
    """
    # For SCIM, we use external_id as the lookup key
    scim_user = await get_scim_user_by_external_id(session, str(user_id))
    if not scim_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return scim_user_to_response(scim_user)


@router.put("/Users/{user_id}", response_model=SCIMUserResponse)
async def update_user(
    user_id: str, request: SCIMUserRequest, session: AsyncSession = Depends(get_session)
):
    """
    SCIM 2.0 Update User
    Full update (replace) user
    """
    try:
        scim_user = await get_scim_user_by_external_id(session, user_id)
        if not scim_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        email = request.emails[0].value if request.emails else None

        scim_user = await update_scim_user(
            session=session,
            scim_user=scim_user,
            username=request.userName,
            email=email,
            given_name=request.name.givenName if request.name else None,
            family_name=request.name.familyName if request.name else None,
            display_name=request.displayName,
            active=request.active,
        )

        await log_scim_event(
            session=session,
            event_type="update_user",
            resource_type="User",
            status="success",
            external_id=user_id,
        )

        return scim_user_to_response(scim_user)
    except HTTPException:
        raise
    except Exception as e:
        await log_scim_event(
            session=session,
            event_type="update_user",
            resource_type="User",
            status="error",
            external_id=user_id,
            error_message=str(e),
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/Users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, session: AsyncSession = Depends(get_session)):
    """
    SCIM 2.0 Delete User
    Soft-delete user (deactivate)
    """
    try:
        scim_user = await get_scim_user_by_external_id(session, user_id)
        if not scim_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        await delete_scim_user(session, scim_user)

        await log_scim_event(
            session=session,
            event_type="delete_user",
            resource_type="User",
            status="success",
            external_id=user_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        await log_scim_event(
            session=session,
            event_type="delete_user",
            resource_type="User",
            status="error",
            external_id=user_id,
            error_message=str(e),
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/Users", response_model=SCIMListResponse)
async def list_users(
    startIndex: int = 1, count: int = 100, session: AsyncSession = Depends(get_session)
):
    """
    SCIM 2.0 List Users
    List all users with pagination
    """
    users = await list_scim_users(session, limit=count)
    return SCIMListResponse(
        totalResults=len(users),
        startIndex=startIndex,
        itemsPerPage=len(users),
        Resources=[scim_user_to_response(u).dict() for u in users],
    )


# Group endpoints
@router.post("/Groups", response_model=SCIMGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(request: SCIMGroupRequest, session: AsyncSession = Depends(get_session)):
    """
    SCIM 2.0 Create Group
    Provisions a new group from IdP
    """
    try:
        scim_group = await create_scim_group(
            session=session, external_id=request.externalId, display_name=request.displayName
        )

        # Add members if provided
        if request.members:
            for member in request.members:
                member_user = await get_scim_user_by_external_id(session, member.value)
                if member_user:
                    await create_scim_group_membership(
                        session=session,
                        scim_group_id=scim_group.id,
                        scim_user_id=member_user.id,
                        member_ref=member.ref,
                        member_type=member.type,
                    )

        await log_scim_event(
            session=session,
            event_type="create_group",
            resource_type="Group",
            status="success",
            external_id=request.externalId,
        )

        return scim_group_to_response(scim_group)
    except Exception as e:
        await log_scim_event(
            session=session,
            event_type="create_group",
            resource_type="Group",
            status="error",
            external_id=request.externalId,
            error_message=str(e),
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/Groups/{group_id}", response_model=SCIMGroupResponse)
async def get_group(group_id: str, session: AsyncSession = Depends(get_session)):
    """
    SCIM 2.0 Get Group
    Retrieve group by ID
    """
    scim_group = await get_scim_group_by_external_id(session, group_id)
    if not scim_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    return scim_group_to_response(scim_group)


@router.put("/Groups/{group_id}", response_model=SCIMGroupResponse)
async def update_group(
    group_id: str, request: SCIMGroupRequest, session: AsyncSession = Depends(get_session)
):
    """
    SCIM 2.0 Update Group
    Full update (replace) group
    """
    try:
        scim_group = await get_scim_group_by_external_id(session, group_id)
        if not scim_group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

        scim_group = await update_scim_group(
            session=session, scim_group=scim_group, display_name=request.displayName
        )

        await log_scim_event(
            session=session,
            event_type="update_group",
            resource_type="Group",
            status="success",
            external_id=group_id,
        )

        return scim_group_to_response(scim_group)
    except HTTPException:
        raise
    except Exception as e:
        await log_scim_event(
            session=session,
            event_type="update_group",
            resource_type="Group",
            status="error",
            external_id=group_id,
            error_message=str(e),
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/Groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: str, session: AsyncSession = Depends(get_session)):
    """
    SCIM 2.0 Delete Group
    Delete group
    """
    try:
        scim_group = await get_scim_group_by_external_id(session, group_id)
        if not scim_group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

        await delete_scim_group(session, scim_group)

        await log_scim_event(
            session=session,
            event_type="delete_group",
            resource_type="Group",
            status="success",
            external_id=group_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        await log_scim_event(
            session=session,
            event_type="delete_group",
            resource_type="Group",
            status="error",
            external_id=group_id,
            error_message=str(e),
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/Groups", response_model=SCIMListResponse)
async def list_groups(
    startIndex: int = 1, count: int = 100, session: AsyncSession = Depends(get_session)
):
    """
    SCIM 2.0 List Groups
    List all groups with pagination
    """
    groups = await list_scim_groups(session, limit=count)
    return SCIMListResponse(
        totalResults=len(groups),
        startIndex=startIndex,
        itemsPerPage=len(groups),
        Resources=[scim_group_to_response(g).dict() for g in groups],
    )
