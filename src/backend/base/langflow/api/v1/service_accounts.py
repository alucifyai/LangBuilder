"""
Service Accounts and API Tokens API
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.auth.utils import get_current_active_user
from langflow.services.database.models.audit.crud import create_audit_log
from langflow.services.database.models.audit.model import AuditAction
from langflow.services.database.models.service_account.crud import (
    create_api_token,
    create_service_account,
    delete_api_token,
    delete_service_account,
    get_service_account_by_id,
    list_api_tokens,
    list_service_accounts,
    revoke_api_token,
    update_service_account,
)
from langflow.services.database.models.service_account.model import TokenScope
from langflow.services.database.models.user.model import User
from langflow.services.deps import get_session

router = APIRouter(prefix="/service-accounts", tags=["Service Accounts"])


# Request/Response Models
class ServiceAccountCreate(BaseModel):
    """Request to create a service account."""

    name: str = Field(..., description="Service account name")
    description: str | None = Field(None, description="Service account description")
    organization_id: str = Field(..., description="Organization ID")


class ServiceAccountUpdate(BaseModel):
    """Request to update a service account."""

    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ServiceAccountResponse(BaseModel):
    """Service account response."""

    id: str
    name: str
    description: str | None
    organization_id: str
    created_by: str
    is_active: bool
    created_at: str
    updated_at: str
    last_used_at: str | None


class TokenCreateRequest(BaseModel):
    """Request to create an API token."""

    name: str = Field(..., description="Token name/description")
    scopes: list[str] = Field(..., description="List of token scopes")
    expires_in_days: int | None = Field(None, description="Token expiration in days (None = never)")
    # Resource-level scope restriction (Story 4.2)
    scope_type: str | None = Field(None, description="Resource scope type (Workspace, Project, etc.)")
    scope_id: str | None = Field(None, description="Resource scope ID - restricts token to this resource only")


class TokenResponse(BaseModel):
    """API token response (without plaintext token)."""

    id: str
    service_account_id: str
    name: str
    token_prefix: str
    scopes: list[str]
    scope_type: str | None = None
    scope_id: str | None = None
    expires_at: str | None
    last_used_at: str | None
    last_used_ip: str | None
    use_count: int
    is_active: bool
    created_at: str
    created_by: str


class TokenCreateResponse(TokenResponse):
    """API token creation response (includes plaintext token ONCE)."""

    token: str = Field(..., description="Plaintext token - save this, it won't be shown again!")


class TokenRevokeRequest(BaseModel):
    """Request to revoke a token."""

    reason: str | None = Field(None, description="Reason for revocation")


# ============================================================================
# Service Account Endpoints
# ============================================================================


@router.post("", response_model=ServiceAccountResponse, status_code=201)
async def create_service_account_route(
    request: ServiceAccountCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ServiceAccountResponse:
    """
    Create a new service account.

    Service accounts are non-human principals used for API access.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    account = await create_service_account(
        db=db,
        name=request.name,
        organization_id=request.organization_id,
        created_by=current_user.id,
        description=request.description,
    )

    # Audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_CREATED,  # TODO: Add SERVICE_ACCOUNT_CREATED
        resource_type="service_account",
        resource_id=account.id,
        metadata={"name": account.name},
    )

    return ServiceAccountResponse(
        id=account.id,
        name=account.name,
        description=account.description,
        organization_id=account.organization_id,
        created_by=account.created_by,
        is_active=account.is_active,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat(),
        last_used_at=account.last_used_at.isoformat() if account.last_used_at else None,
    )


@router.get("", response_model=list[ServiceAccountResponse])
async def list_service_accounts_route(
    organization_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
    skip: int = 0,
    limit: int = 100,
) -> list[ServiceAccountResponse]:
    """List service accounts for an organization."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    accounts = await list_service_accounts(db, organization_id, skip, limit)

    return [
        ServiceAccountResponse(
            id=account.id,
            name=account.name,
            description=account.description,
            organization_id=account.organization_id,
            created_by=account.created_by,
            is_active=account.is_active,
            created_at=account.created_at.isoformat(),
            updated_at=account.updated_at.isoformat(),
            last_used_at=account.last_used_at.isoformat() if account.last_used_at else None,
        )
        for account in accounts
    ]


@router.get("/{account_id}", response_model=ServiceAccountResponse)
async def get_service_account_route(
    account_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ServiceAccountResponse:
    """Get service account by ID."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    account = await get_service_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Service account not found")

    return ServiceAccountResponse(
        id=account.id,
        name=account.name,
        description=account.description,
        organization_id=account.organization_id,
        created_by=account.created_by,
        is_active=account.is_active,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat(),
        last_used_at=account.last_used_at.isoformat() if account.last_used_at else None,
    )


@router.patch("/{account_id}", response_model=ServiceAccountResponse)
async def update_service_account_route(
    account_id: UUID,
    request: ServiceAccountUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ServiceAccountResponse:
    """Update service account."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    account = await update_service_account(db, account_id, **updates)

    if not account:
        raise HTTPException(status_code=404, detail="Service account not found")

    # Audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_UPDATED,  # TODO: Add SERVICE_ACCOUNT_UPDATED
        resource_type="service_account",
        resource_id=account.id,
        metadata={"updates": list(updates.keys())},
    )

    return ServiceAccountResponse(
        id=account.id,
        name=account.name,
        description=account.description,
        organization_id=account.organization_id,
        created_by=account.created_by,
        is_active=account.is_active,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat(),
        last_used_at=account.last_used_at.isoformat() if account.last_used_at else None,
    )


@router.delete("/{account_id}", status_code=204)
async def delete_service_account_route(
    account_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete service account and all associated tokens."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    success = await delete_service_account(db, account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Service account not found")

    # Audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_DELETED,  # TODO: Add SERVICE_ACCOUNT_DELETED
        resource_type="service_account",
        resource_id=str(account_id),
    )


# ============================================================================
# API Token Endpoints
# ============================================================================


@router.post("/{account_id}/tokens", response_model=TokenCreateResponse, status_code=201)
async def create_api_token_route(
    account_id: UUID,
    request: TokenCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TokenCreateResponse:
    """
    Create a new API token for a service account.

    **IMPORTANT**: The plaintext token is only returned once. Save it securely!
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    # Verify service account exists
    account = await get_service_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Service account not found")

    # Calculate expiration
    expires_at = None
    if request.expires_in_days:
        from datetime import timedelta, timezone

        expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)

    # Create token
    token_record, plaintext_token = await create_api_token(
        db=db,
        service_account_id=account_id,
        name=request.name,
        created_by=current_user.id,
        scopes=request.scopes,
        expires_at=expires_at,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
    )

    # Audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_CREATED,  # TODO: Add API_TOKEN_CREATED
        resource_type="api_token",
        resource_id=token_record.id,
        metadata={
            "service_account_id": str(account_id),
            "name": request.name,
            "scopes": request.scopes,
        },
    )

    return TokenCreateResponse(
        id=token_record.id,
        service_account_id=token_record.service_account_id,
        name=token_record.name,
        token_prefix=token_record.token_prefix,
        scopes=token_record.scopes,
        scope_type=token_record.scope_type,
        scope_id=token_record.scope_id,
        expires_at=token_record.expires_at.isoformat() if token_record.expires_at else None,
        last_used_at=None,
        last_used_ip=None,
        use_count=0,
        is_active=token_record.is_active,
        created_at=token_record.created_at.isoformat(),
        created_by=token_record.created_by,
        token=plaintext_token,  # Only returned once!
    )


@router.get("/{account_id}/tokens", response_model=list[TokenResponse])
async def list_api_tokens_route(
    account_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
    include_revoked: bool = False,
) -> list[TokenResponse]:
    """List API tokens for a service account."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    tokens = await list_api_tokens(db, account_id, include_revoked)

    return [
        TokenResponse(
            id=token.id,
            service_account_id=token.service_account_id,
            name=token.name,
            token_prefix=token.token_prefix,
            scopes=token.scopes,
            expires_at=token.expires_at.isoformat() if token.expires_at else None,
            last_used_at=token.last_used_at.isoformat() if token.last_used_at else None,
            last_used_ip=token.last_used_ip,
            use_count=token.use_count,
            is_active=token.is_active,
            created_at=token.created_at.isoformat(),
            created_by=token.created_by,
        )
        for token in tokens
    ]


@router.post("/{account_id}/tokens/{token_id}/revoke", response_model=TokenResponse)
async def revoke_api_token_route(
    account_id: UUID,
    token_id: UUID,
    request: TokenRevokeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    """Revoke an API token."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    token = await revoke_api_token(db, token_id, current_user.id, request.reason)
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_DELETED,  # TODO: ADD TOKEN_REVOKED
        resource_type="api_token",
        resource_id=token.id,
        metadata={"reason": request.reason},
    )

    return TokenResponse(
        id=token.id,
        service_account_id=token.service_account_id,
        name=token.name,
        token_prefix=token.token_prefix,
        scopes=token.scopes,
        expires_at=token.expires_at.isoformat() if token.expires_at else None,
        last_used_at=token.last_used_at.isoformat() if token.last_used_at else None,
        last_used_ip=token.last_used_ip,
        use_count=token.use_count,
        is_active=token.is_active,
        created_at=token.created_at.isoformat(),
        created_by=token.created_by,
    )


@router.delete("/{account_id}/tokens/{token_id}", status_code=204)
async def delete_api_token_route(
    account_id: UUID,
    token_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete an API token permanently."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    success = await delete_api_token(db, token_id)
    if not success:
        raise HTTPException(status_code=404, detail="Token not found")

    # Audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_DELETED,  # TODO: Add TOKEN_DELETED
        resource_type="api_token",
        resource_id=str(token_id),
    )
