"""Service Account Management API endpoints for RBAC.

Implements PRD Story 2.4 - Service Account Management
- Create, Read, Update, Delete operations for service accounts
- Token generation with scoped permissions
- Service account lifecycle management
- Audit logging integration

AppGraph Impact Subgraph:
- service_account_management_api → REST API for service accounts
- create_service_account_logic → Creates service account
- generate_service_account_token_logic → Generates scoped API token
- delete_service_account_logic → Deletes service account
"""

import secrets
from datetime import datetime, timezone
from hashlib import sha256
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlmodel import select

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.api_key.model import ApiKey
from langflow.services.database.models.rbac.role import Role
from langflow.services.database.models.rbac.role_assignment import RoleAssignment
from langflow.services.database.models.rbac.service_account import (
    ServiceAccount,
    ServiceAccountCreate,
    ServiceAccountRead,
    ServiceAccountUpdate,
)
from langflow.services.database.models.workspace.model import Workspace
from langflow.services.rbac.audit import log_audit_event_safe

router = APIRouter(prefix="/service-accounts", tags=["Service Accounts"])


# ============================================================================
# Helper Functions
# ============================================================================


def hash_token(token: str) -> str:
    """Hash a token using SHA256.

    Args:
        token: Plain text token to hash

    Returns:
        Hexadecimal hash string
    """
    return sha256(token.encode()).hexdigest()


async def _check_service_account_manage_permission(current_user: CurrentActiveUser) -> None:
    """Check if user has permission to manage service accounts.

    For now, only superusers can manage service accounts.
    TODO: Integrate with RBACEnforcementEngine once permission system is fully connected.

    Args:
        current_user: The current authenticated user

    Raises:
        HTTPException: 403 if user lacks permission
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Service account management requires superuser access.",
        )


# ============================================================================
# Pydantic Schemas
# ============================================================================


class ServiceAccountCreateExtended(ServiceAccountCreate):
    """Extended schema for creating a service account with optional role assignment.

    PRD Story 2.4 @AC1
    """

    role_id: UUID | None = None  # Optional initial role to assign
    scope: dict[str, str] | None = None  # Scope for initial role (required if role_id provided)

    @model_validator(mode="after")
    def validate_role_scope(self):
        """Validate that scope is provided if role_id is specified."""
        if self.role_id and not self.scope:
            raise ValueError("scope is required when role_id is provided")
        return self


class ServiceAccountReadExtended(ServiceAccountRead):
    """Extended schema with additional metadata.

    Includes token count and assigned roles count.
    """

    token_count: int = 0  # Number of active API tokens
    role_count: int = 0  # Number of assigned roles

    model_config = ConfigDict(from_attributes=True)


class TokenCreate(BaseModel):
    """Schema for creating an API token for a service account.

    PRD Story 2.4 @AC2
    """

    name: str | None = None  # Optional name for the token
    expires_days: int | None = Field(default=None, ge=1, le=365)  # Token expiration in days

    # Token scoping fields (optional - restrict token permissions)
    scoped_permissions: list[str] | None = None  # Subset of SA permissions
    scope_type: str | None = None  # workspace, project, flow, etc.
    scope_id: UUID | None = None  # ID of the scoped resource

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for token creation response.

    NOTE: Token value is only returned once during creation.
    """

    id: UUID
    token: str  # Full token value (only visible on creation)
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenRead(BaseModel):
    """Schema for reading token metadata (without token value)."""

    id: UUID
    name: str | None
    last_used_at: datetime | None
    total_uses: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/", response_model=ServiceAccountReadExtended, status_code=status.HTTP_201_CREATED)
async def create_service_account(
    sa_data: ServiceAccountCreateExtended,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> ServiceAccountReadExtended:
    """Create a new service account.

    Implements PRD Story 2.4 @AC1 - Create service account with optional role assignment.

    Example request body:
    ```json
    {
        "name": "ci-bot",
        "display_name": "CI/CD Pipeline Bot",
        "description": "Automated deployment service account",
        "role_id": "550e8400-e29b-41d4-a716-446655440000",
        "scope": {"workspace": "550e8400-e29b-41d4-a716-446655440001"}
    }
    ```

    Args:
        sa_data: Service account creation data
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The newly created service account

    Raises:
        HTTPException: 400 if validation fails or name already exists
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if role not found
    """
    await _check_service_account_manage_permission(current_user)

    # Validate workspace exists (critical for multi-tenancy)
    workspace = await session.get(Workspace, sa_data.workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with ID {sa_data.workspace_id} not found",
        )

    # Check if service account name already exists
    stmt = select(ServiceAccount).where(ServiceAccount.name == sa_data.name)
    existing = (await session.exec(stmt)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service account with name '{sa_data.name}' already exists",
        )

    # Validate role exists if provided
    if sa_data.role_id:
        role = await session.get(Role, sa_data.role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {sa_data.role_id} not found",
            )

    # Create service account with workspace scoping
    sa = ServiceAccount(
        name=sa_data.name,
        display_name=sa_data.display_name,
        description=sa_data.description,
        workspace_id=sa_data.workspace_id,  # ✅ ADD workspace scoping
        is_active=True,
        created_by_user_id=current_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(sa)
    await session.flush()  # Get sa.id for role assignment

    # Assign initial role if provided
    if sa_data.role_id and sa_data.scope:
        # Parse scope
        from langflow.api.v1.rbac.grants import parse_scope

        try:
            scope_type, scope_id = parse_scope(sa_data.scope)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scope format: {e!s}",
            ) from e

        # Create role assignment
        grant = RoleAssignment(
            role_id=sa_data.role_id,
            assignee_type="service_account",
            service_account_id=sa.id,
            user_id=None,
            group_id=None,
            scope_type=scope_type,
            scope_id=scope_id,
            is_active=True,
            assigned_by=current_user.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(grant)

    await session.commit()
    await session.refresh(sa)

    # ✅ Audit logging
    await log_audit_event_safe(
        session=session,
        actor_id=current_user.id,
        action="service_account.created",
        resource_type="service_account",
        resource_id=sa.id,
        details={
            "name": sa.name,
            "workspace_id": str(sa.workspace_id),
            "role_id": str(sa_data.role_id) if sa_data.role_id else None,
        },
    )

    logger.info(
        f"Service account created: '{sa.name}' (ID: {sa.id}) by user {current_user.id}"
        + (f" with role {sa_data.role_id}" if sa_data.role_id else "")
    )

    # Build response
    response = ServiceAccountReadExtended.model_validate(sa)
    response.token_count = 0
    response.role_count = 1 if sa_data.role_id else 0

    return response


@router.get("/", response_model=list[ServiceAccountReadExtended])
async def list_service_accounts(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of records to return"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> list[ServiceAccountReadExtended]:
    """List service accounts with pagination.

    Args:
        skip: Pagination offset
        limit: Max results
        is_active: Optional filter by active status
        current_user: Currently authenticated user
        session: Database session

    Returns:
        List of service accounts

    Raises:
        HTTPException: 403 if user lacks permission
    """
    await _check_service_account_manage_permission(current_user)

    # Build query
    stmt = select(ServiceAccount)

    if is_active is not None:
        stmt = stmt.where(ServiceAccount.is_active == is_active)

    stmt = stmt.offset(skip).limit(limit).order_by(ServiceAccount.created_at.desc())

    # Execute query
    result = await session.exec(stmt)
    service_accounts = result.all()

    # Build response with counts
    response_list = []
    for sa in service_accounts:
        # Count tokens
        token_stmt = select(ApiKey).where(ApiKey.service_account_id == sa.id, ApiKey.is_active == True)  # noqa: E712
        token_result = await session.exec(token_stmt)
        token_count = len(token_result.all())

        # Count roles
        role_stmt = select(RoleAssignment).where(
            RoleAssignment.service_account_id == sa.id, RoleAssignment.is_active == True  # noqa: E712
        )
        role_result = await session.exec(role_stmt)
        role_count = len(role_result.all())

        sa_read = ServiceAccountReadExtended.model_validate(sa)
        sa_read.token_count = token_count
        sa_read.role_count = role_count
        response_list.append(sa_read)

    logger.debug(f"User {current_user.id} listed {len(response_list)} service accounts")

    return response_list


@router.get("/{sa_id}", response_model=ServiceAccountReadExtended)
async def get_service_account(
    sa_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> ServiceAccountReadExtended:
    """Get a specific service account by ID.

    Args:
        sa_id: Service account ID
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The requested service account

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if service account not found
    """
    await _check_service_account_manage_permission(current_user)

    sa = await session.get(ServiceAccount, sa_id)
    if not sa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service account with ID {sa_id} not found",
        )

    # Count tokens
    token_stmt = select(ApiKey).where(ApiKey.service_account_id == sa_id, ApiKey.is_active == True)  # noqa: E712
    token_result = await session.exec(token_stmt)
    token_count = len(token_result.all())

    # Count roles
    role_stmt = select(RoleAssignment).where(
        RoleAssignment.service_account_id == sa_id, RoleAssignment.is_active == True  # noqa: E712
    )
    role_result = await session.exec(role_stmt)
    role_count = len(role_result.all())

    sa_read = ServiceAccountReadExtended.model_validate(sa)
    sa_read.token_count = token_count
    sa_read.role_count = role_count

    return sa_read


@router.patch("/{sa_id}", response_model=ServiceAccountRead)
async def update_service_account(
    sa_id: UUID,
    sa_update: ServiceAccountUpdate,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> ServiceAccountRead:
    """Update a service account.

    Only display_name, description, and is_active can be updated.
    Name cannot be changed once created.

    Args:
        sa_id: Service account ID
        sa_update: Update data
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The updated service account

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if service account not found
    """
    await _check_service_account_manage_permission(current_user)

    sa = await session.get(ServiceAccount, sa_id)
    if not sa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service account with ID {sa_id} not found",
        )

    # Update fields
    update_data = sa_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sa, field, value)

    sa.updated_at = datetime.now(timezone.utc)

    session.add(sa)
    await session.commit()
    await session.refresh(sa)

    logger.info(f"Service account updated: '{sa.name}' (ID: {sa_id}) by user {current_user.id}")

    return ServiceAccountRead.model_validate(sa)


@router.delete("/{sa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_account(
    sa_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> None:
    """Delete a service account.

    Deletes the service account and all associated tokens and role assignments.
    This operation is irreversible.

    Implements PRD Story 2.4 @AC3 - Delete service account.

    Args:
        sa_id: Service account ID
        current_user: Currently authenticated user
        session: Database session

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if service account not found
    """
    await _check_service_account_manage_permission(current_user)

    sa = await session.get(ServiceAccount, sa_id)
    if not sa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service account with ID {sa_id} not found",
        )

    sa_name = sa.name

    # Delete service account (cascade will handle tokens and role assignments)
    await session.delete(sa)
    await session.commit()

    # ✅ Audit logging
    await log_audit_event_safe(
        session=session,
        actor_id=current_user.id,
        action="service_account.deleted",
        resource_type="service_account",
        resource_id=sa_id,
        details={"name": sa_name},
    )

    logger.info(f"Service account deleted: '{sa_name}' (ID: {sa_id}) by user {current_user.id}")


# ============================================================================
# Token Management Endpoints
# ============================================================================


@router.post("/{sa_id}/tokens", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def create_service_account_token(
    sa_id: UUID,
    token_data: TokenCreate,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> TokenResponse:
    """Generate a new API token for a service account.

    Implements PRD Story 2.4 @AC2 - Generate scoped API token.

    The token inherits all permissions from the service account's role assignments.
    Token value is only returned once and cannot be retrieved again.

    Example request body:
    ```json
    {
        "name": "Production Deployment Token",
        "expires_days": 90
    }
    ```

    Args:
        sa_id: Service account ID
        token_data: Token creation data
        current_user: Currently authenticated user
        session: Database session

    Returns:
        Token response with the generated token value (only visible once)

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if service account not found
    """
    await _check_service_account_manage_permission(current_user)

    # Verify service account exists and is active
    sa = await session.get(ServiceAccount, sa_id)
    if not sa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service account with ID {sa_id} not found",
        )

    if not sa.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service account '{sa.name}' is not active",
        )

    # Generate secure token
    token_value = secrets.token_urlsafe(32)  # 32 bytes = 256 bits
    token_hash = hash_token(token_value)

    # Create API key with scoping
    api_key = ApiKey(
        api_key=token_hash,
        name=token_data.name or f"{sa.name} token",
        service_account_id=sa_id,
        user_id=None,  # Service account token, not user token
        is_active=True,
        total_uses=0,
        created_at=datetime.now(timezone.utc),
        # ✅ Token scoping fields
        workspace_id=sa.workspace_id,  # Inherit workspace from SA
        scope_type=token_data.scope_type,  # Optional restriction
        scope_id=token_data.scope_id,  # Optional restriction
        scoped_permissions={"permissions": token_data.scoped_permissions} if token_data.scoped_permissions else None,
    )

    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    # ✅ Audit logging
    await log_audit_event_safe(
        session=session,
        actor_id=current_user.id,
        action="service_account.token_generated",
        resource_type="service_account",
        resource_id=sa_id,
        details={
            "token_id": str(api_key.id),
            "token_name": api_key.name,
            "scope_type": token_data.scope_type,
            "scope_id": str(token_data.scope_id) if token_data.scope_id else None,
        },
    )

    logger.info(
        f"API token created for service account '{sa.name}' (ID: {sa_id}) "
        f"by user {current_user.id} - Token ID: {api_key.id}"
    )

    # Return token value with lgs_ prefix (LangBuilder Service)
    return TokenResponse(
        id=api_key.id, token=f"lgs_{token_value}", name=api_key.name or "", created_at=api_key.created_at
    )


@router.get("/{sa_id}/tokens", response_model=list[TokenRead])
async def list_service_account_tokens(
    sa_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> list[TokenRead]:
    """List all API tokens for a service account.

    Returns metadata about tokens, but not the token values themselves.

    Args:
        sa_id: Service account ID
        current_user: Currently authenticated user
        session: Database session

    Returns:
        List of token metadata

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if service account not found
    """
    await _check_service_account_manage_permission(current_user)

    # Verify service account exists
    sa = await session.get(ServiceAccount, sa_id)
    if not sa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service account with ID {sa_id} not found",
        )

    # Get all tokens for this service account
    stmt = select(ApiKey).where(ApiKey.service_account_id == sa_id).order_by(ApiKey.created_at.desc())
    result = await session.exec(stmt)
    tokens = result.all()

    return [TokenRead.model_validate(token) for token in tokens]


@router.delete("/{sa_id}/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_service_account_token(
    sa_id: UUID,
    token_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> None:
    """Revoke (delete) an API token for a service account.

    Args:
        sa_id: Service account ID
        token_id: Token ID to revoke
        current_user: Currently authenticated user
        session: Database session

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if service account or token not found
    """
    await _check_service_account_manage_permission(current_user)

    # Verify service account exists
    sa = await session.get(ServiceAccount, sa_id)
    if not sa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service account with ID {sa_id} not found",
        )

    # Get token and verify it belongs to this service account
    token = await session.get(ApiKey, token_id)
    if not token or token.service_account_id != sa_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token with ID {token_id} not found for service account {sa_id}",
        )

    token_name = token.name

    # Delete token
    await session.delete(token)
    await session.commit()

    # ✅ Audit logging
    await log_audit_event_safe(
        session=session,
        actor_id=current_user.id,
        action="service_account.token_revoked",
        resource_type="service_account",
        resource_id=sa_id,
        details={"token_id": str(token_id), "token_name": token_name},
    )

    logger.info(
        f"API token revoked for service account '{sa.name}' (ID: {sa_id}) "
        f"by user {current_user.id} - Token ID: {token_id}"
    )
