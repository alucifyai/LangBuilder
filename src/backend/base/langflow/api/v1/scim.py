"""SCIM 2.0 API endpoints.

PRD Story 2.3 @AC3 - SCIM provisioning server
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from loguru import logger
from sqlmodel import select

from langflow.api.utils import DbSession
from langflow.services.database.models.scim import (
    SCIMError,
    SCIMGroupCreate,
    SCIMGroupResponse,
    SCIMListResponse,
    SCIMPatchRequest,
    SCIMToken,
    SCIMUserCreate,
    SCIMUserResponse,
)
from langflow.services.scim.scim_service import SCIMService

router = APIRouter(prefix="/scim/v2", tags=["SCIM"])


# SCIM Authentication


async def verify_scim_token(
    authorization: Annotated[str, Header()],
    db: DbSession,
) -> tuple[SCIMToken, str]:
    """Verify SCIM bearer token.

    Args:
        authorization: Authorization header with Bearer token
        db: Database session

    Returns:
        Tuple of (SCIMToken, workspace_id)

    Raises:
        HTTPException: If token is invalid

    PRD Story 2.3 @AC3 - SCIM authentication
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")

    # Hash token for lookup
    import hashlib

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Find token
    stmt = select(SCIMToken).where(
        SCIMToken.token_hash == token_hash, SCIMToken.is_active == True
    )
    result = await db.exec(stmt)
    scim_token = result.first()

    if not scim_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check expiration
    from datetime import datetime, timezone

    if scim_token.expires_at and scim_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last used
    scim_token.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    return scim_token, scim_token.workspace_id


SCIMAuth = Annotated[tuple[SCIMToken, str], Depends(verify_scim_token)]


# SCIM ServiceProviderConfig


@router.get("/ServiceProviderConfig")
async def get_service_provider_config():
    """Get SCIM service provider configuration.

    Returns:
        SCIM service provider config

    PRD Story 2.3 @AC3 - SCIM service provider config
    """
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        "documentationUri": "https://docs.langbuilder.com/scim",
        "patch": {"supported": True},
        "bulk": {"supported": False, "maxOperations": 0, "maxPayloadSize": 0},
        "filter": {"supported": False, "maxResults": 200},
        "changePassword": {"supported": False},
        "sort": {"supported": False},
        "etag": {"supported": False},
        "authenticationSchemes": [
            {
                "name": "OAuth Bearer Token",
                "description": "Authentication scheme using the OAuth Bearer Token",
                "specUri": "https://www.rfc-editor.org/info/rfc6750",
                "type": "oauthbearertoken",
                "primary": True,
            }
        ],
    }


# SCIM ResourceTypes


@router.get("/ResourceTypes")
async def get_resource_types():
    """Get SCIM resource types.

    Returns:
        SCIM resource types

    PRD Story 2.3 @AC3 - SCIM resource types
    """
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 2,
        "Resources": [
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                "id": "User",
                "name": "User",
                "endpoint": "/scim/v2/Users",
                "description": "User account",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
            },
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                "id": "Group",
                "name": "Group",
                "endpoint": "/scim/v2/Groups",
                "description": "Group",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:Group",
            },
        ],
    }


# SCIM Schemas


@router.get("/Schemas")
async def get_schemas():
    """Get SCIM schemas.

    Returns:
        SCIM schemas

    PRD Story 2.3 @AC3 - SCIM schemas
    """
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 2,
        "Resources": [
            {
                "id": "urn:ietf:params:scim:schemas:core:2.0:User",
                "name": "User",
                "description": "User Account",
            },
            {
                "id": "urn:ietf:params:scim:schemas:core:2.0:Group",
                "name": "Group",
                "description": "Group",
            },
        ],
    }


# SCIM Users


@router.post("/Users", response_model=SCIMUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: SCIMUserCreate,
    request: Request,
    db: DbSession,
    auth: SCIMAuth,
):
    """Create user via SCIM.

    Args:
        user_data: SCIM user data
        auth: SCIM authentication

    Returns:
        Created SCIM user

    PRD Story 2.3 @AC3 - SCIM user creation
    """
    scim_token, workspace_id = auth
    scim_service = SCIMService(workspace_id)

    client_ip = request.client.host if request.client else None

    try:
        user = await scim_service.create_user(
            db=db,
            user_data=user_data.model_dump(),
            scim_token_id=scim_token.id,
            ip_address=client_ip,
        )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SCIM user creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User creation failed: {str(e)}",
        )


@router.get("/Users/{user_id}", response_model=SCIMUserResponse)
async def get_user(
    user_id: str,
    db: DbSession,
    auth: SCIMAuth,
):
    """Get user by SCIM ID.

    Args:
        user_id: SCIM user ID
        auth: SCIM authentication

    Returns:
        SCIM user

    PRD Story 2.3 @AC3 - SCIM user retrieval
    """
    _, workspace_id = auth
    scim_service = SCIMService(workspace_id)

    return await scim_service.get_user(db=db, user_id=user_id)


@router.put("/Users/{user_id}", response_model=SCIMUserResponse)
async def update_user(
    user_id: str,
    user_data: SCIMUserCreate,
    request: Request,
    db: DbSession,
    auth: SCIMAuth,
):
    """Update user via SCIM.

    Args:
        user_id: SCIM user ID
        user_data: SCIM user data
        auth: SCIM authentication

    Returns:
        Updated SCIM user

    PRD Story 2.3 @AC3 - SCIM user update
    """
    scim_token, workspace_id = auth
    scim_service = SCIMService(workspace_id)

    client_ip = request.client.host if request.client else None

    return await scim_service.update_user(
        db=db,
        user_id=user_id,
        user_data=user_data.model_dump(),
        scim_token_id=scim_token.id,
        ip_address=client_ip,
    )


@router.patch("/Users/{user_id}", response_model=SCIMUserResponse)
async def patch_user(
    user_id: str,
    patch_data: SCIMPatchRequest,
    request: Request,
    db: DbSession,
    auth: SCIMAuth,
):
    """Patch user via SCIM.

    Args:
        user_id: SCIM user ID
        patch_data: SCIM PATCH operations
        auth: SCIM authentication

    Returns:
        Updated SCIM user

    PRD Story 2.3 @AC3 - SCIM PATCH operation
    """
    scim_token, workspace_id = auth
    scim_service = SCIMService(workspace_id)

    client_ip = request.client.host if request.client else None

    return await scim_service.patch_user(
        db=db,
        user_id=user_id,
        operations=[op.model_dump() for op in patch_data.Operations],
        scim_token_id=scim_token.id,
        ip_address=client_ip,
    )


@router.delete("/Users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    request: Request,
    db: DbSession,
    auth: SCIMAuth,
):
    """Delete user via SCIM.

    Args:
        user_id: SCIM user ID
        auth: SCIM authentication

    PRD Story 2.3 @AC3 - SCIM user deletion
    """
    scim_token, workspace_id = auth
    scim_service = SCIMService(workspace_id)

    client_ip = request.client.host if request.client else None

    await scim_service.delete_user(
        db=db,
        user_id=user_id,
        scim_token_id=scim_token.id,
        ip_address=client_ip,
    )


@router.get("/Users")
async def list_users(
    db: DbSession,
    auth: SCIMAuth,
    startIndex: int = Query(1, ge=1, description="Starting index (1-based)"),
    count: int = Query(100, ge=1, le=200, description="Number of results"),
):
    """List users via SCIM.

    Args:
        auth: SCIM authentication
        startIndex: Starting index (1-based)
        count: Number of results

    Returns:
        SCIM list response

    PRD Story 2.3 @AC3 - SCIM user list
    """
    _, workspace_id = auth
    scim_service = SCIMService(workspace_id)

    return await scim_service.list_users(
        db=db,
        start_index=startIndex,
        count=count,
    )


# SCIM Groups (stub implementation)


@router.post("/Groups", response_model=SCIMGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: SCIMGroupCreate,
    db: DbSession,
    auth: SCIMAuth,
):
    """Create group via SCIM.

    Args:
        group_data: SCIM group data
        auth: SCIM authentication

    Returns:
        Created SCIM group

    PRD Story 2.3 @AC3 - SCIM group creation (stub)
    """
    # TODO: Implement group creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Group provisioning not yet implemented",
    )


@router.get("/Groups/{group_id}", response_model=SCIMGroupResponse)
async def get_group(
    group_id: str,
    db: DbSession,
    auth: SCIMAuth,
):
    """Get group by SCIM ID.

    Args:
        group_id: SCIM group ID
        auth: SCIM authentication

    Returns:
        SCIM group

    PRD Story 2.3 @AC3 - SCIM group retrieval (stub)
    """
    # TODO: Implement group retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Group provisioning not yet implemented",
    )


@router.get("/Groups")
async def list_groups(
    db: DbSession,
    auth: SCIMAuth,
    startIndex: int = Query(1, ge=1),
    count: int = Query(100, ge=1, le=200),
):
    """List groups via SCIM.

    Args:
        auth: SCIM authentication
        startIndex: Starting index
        count: Number of results

    Returns:
        SCIM list response

    PRD Story 2.3 @AC3 - SCIM group list (stub)
    """
    # TODO: Implement group listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Group provisioning not yet implemented",
    )
