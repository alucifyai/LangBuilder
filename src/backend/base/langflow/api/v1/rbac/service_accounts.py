"""Service Account management API endpoints for RBAC system."""

from typing import TYPE_CHECKING
from langflow.schema.serialize import UUIDstr

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.api.v1.rbac.dependencies import (
    check_workspace_permission,
    get_permission_engine,
)
from langflow.services.rbac.permission_engine import PermissionEngine
from langflow.services.database.models.rbac.service_account import (
    ServiceAccount,
    ServiceAccountCreate,
    ServiceAccountRead,
    ServiceAccountUpdate,
    ServiceAccountToken,
    ServiceAccountTokenCreate,
    ServiceAccountTokenRead,
    ServiceAccountTokenResponse,
)
from langflow.services.database.models.rbac.workspace import Workspace

if TYPE_CHECKING:
    from langflow.services.database.models.user.model import User

router = APIRouter(
    prefix="/service-accounts",
    tags=["RBAC", "Service Accounts"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource does not exist"},
        422: {"description": "Validation Error - Invalid request data"},
    },
)


@router.get("/", response_model=list[ServiceAccountRead])
async def list_service_accounts(
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace_id: UUIDstr,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    is_active: bool | None = None,
) -> list[ServiceAccountRead]:
    """List service accounts in a workspace."""
    
    # Check workspace permission
    await check_workspace_permission(session, current_user, workspace_id, "service_account:read")

    statement = select(ServiceAccount).where(ServiceAccount.workspace_id == workspace_id)

    # Apply filters
    if search:
        statement = statement.where(
            (ServiceAccount.name.ilike(f"%{search}%")) |
            (ServiceAccount.description.ilike(f"%{search}%"))
        )

    if is_active is not None:
        statement = statement.where(ServiceAccount.is_active == is_active)

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    
    result = await session.exec(statement)
    service_accounts = result.all()

    return [ServiceAccountRead.model_validate(sa) for sa in service_accounts]


@router.post("/", response_model=ServiceAccountRead, status_code=status.HTTP_201_CREATED)
async def create_service_account(
    service_account_data: ServiceAccountCreate,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> ServiceAccountRead:
    """Create a new service account."""
    
    # Check workspace permission
    await check_workspace_permission(
        session, current_user, service_account_data.workspace_id, "service_account:create"
    )

    # Verify workspace exists
    workspace = await session.get(Workspace, service_account_data.workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Check for duplicate name in workspace
    statement = select(ServiceAccount).where(
        and_(
            ServiceAccount.workspace_id == service_account_data.workspace_id,
            ServiceAccount.name == service_account_data.name
        )
    )
    result = await session.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service account with this name already exists in workspace"
        )

    # Create service account
    service_account = ServiceAccount(
        **service_account_data.model_dump(),
        created_by=current_user.id
    )
    
    session.add(service_account)
    await session.commit()
    await session.refresh(service_account)

    return ServiceAccountRead.model_validate(service_account)


@router.get("/{service_account_id}", response_model=ServiceAccountRead)
async def get_service_account(
    service_account_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> ServiceAccountRead:
    """Get service account by ID."""
    
    service_account = await session.get(ServiceAccount, service_account_id)
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, service_account.workspace_id, "service_account:read"
    )

    return ServiceAccountRead.model_validate(service_account)


@router.put("/{service_account_id}", response_model=ServiceAccountRead)
async def update_service_account(
    service_account_id: UUIDstr,
    service_account_data: ServiceAccountUpdate,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> ServiceAccountRead:
    """Update service account."""
    
    service_account = await session.get(ServiceAccount, service_account_id)
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, service_account.workspace_id, "service_account:update"
    )

    # Update fields
    update_data = service_account_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service_account, field, value)

    await session.commit()
    await session.refresh(service_account)

    return ServiceAccountRead.model_validate(service_account)


@router.delete("/{service_account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_account(
    service_account_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> None:
    """Delete service account."""
    
    service_account = await session.get(ServiceAccount, service_account_id)
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, service_account.workspace_id, "service_account:delete"
    )

    await session.delete(service_account)
    await session.commit()


@router.post("/{service_account_id}/tokens", response_model=ServiceAccountTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_service_account_token(
    service_account_id: UUIDstr,
    token_data: ServiceAccountTokenCreate,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> ServiceAccountTokenResponse:
    """Create a new token for service account."""
    
    service_account = await session.get(ServiceAccount, service_account_id)
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, service_account.workspace_id, "service_account:update"
    )

    # Create token
    import secrets
    import hashlib
    from datetime import datetime, timedelta
    
    # Generate token
    token_value = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token_value.encode()).hexdigest()
    
    # Set expiry if provided
    expires_at = None
    if token_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=token_data.expires_in_days)

    token = ServiceAccountToken(
        service_account_id=service_account_id,
        name=token_data.name,
        description=token_data.description,
        token_hash=token_hash,
        expires_at=expires_at,
        scopes=token_data.scopes,
        ip_restrictions=token_data.ip_restrictions,
        created_by=current_user.id
    )
    
    session.add(token)
    await session.commit()
    await session.refresh(token)

    return ServiceAccountTokenResponse(
        id=token.id,
        name=token.name,
        description=token.description,
        token=token_value,  # Only returned on creation
        expires_at=token.expires_at,
        scopes=token.scopes,
        ip_restrictions=token.ip_restrictions,
        created_at=token.created_at,
        created_by=token.created_by
    )


@router.get("/{service_account_id}/tokens", response_model=list[ServiceAccountTokenRead])
async def list_service_account_tokens(
    service_account_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[ServiceAccountTokenRead]:
    """List tokens for service account."""
    
    service_account = await session.get(ServiceAccount, service_account_id)
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, service_account.workspace_id, "service_account:read"
    )

    statement = select(ServiceAccountToken).where(
        ServiceAccountToken.service_account_id == service_account_id
    ).offset(skip).limit(limit)
    
    result = await session.exec(statement)
    tokens = result.all()

    return [ServiceAccountTokenRead.model_validate(token) for token in tokens]


@router.delete("/{service_account_id}/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_account_token(
    service_account_id: UUIDstr,
    token_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> None:
    """Delete service account token."""
    
    service_account = await session.get(ServiceAccount, service_account_id)
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, service_account.workspace_id, "service_account:update"
    )

    token = await session.get(ServiceAccountToken, token_id)
    if not token or token.service_account_id != service_account_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )

    await session.delete(token)
    await session.commit()