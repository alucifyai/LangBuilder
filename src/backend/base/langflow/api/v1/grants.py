"""
Grant Management API

Provides endpoints for assigning and managing role grants (role assignments to principals within scopes).
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.audit.crud import create_audit_log
from langflow.services.database.models.audit.model import AuditAction
from langflow.services.database.models.grant.crud import (
    count_grants_by_role,
    create_grant,
    delete_grant,
    get_grant_by_id,
    get_grants_for_principal,
    get_grants_for_scope,
)
from langflow.services.database.models.grant.model import Grant, PrincipalType, ScopeType
from langflow.services.database.models.role.crud import get_role_by_id
from langflow.services.database.models.user.crud import get_user_by_id

router = APIRouter(prefix="/grants", tags=["Grants"])


# Pydantic schemas
class GrantCreate(BaseModel):
    """Schema for creating a new grant."""

    principal_type: PrincipalType
    principal_id: str
    role_id: str
    scope_type: ScopeType
    scope_id: str
    expires_at: datetime | None = None


class GrantUpdate(BaseModel):
    """Schema for updating a grant."""

    expires_at: datetime | None = None
    scope_type: ScopeType | None = None
    scope_id: str | None = None


class GrantResponse(BaseModel):
    """Schema for grant response."""

    id: str
    principal_type: PrincipalType
    principal_id: str
    role_id: str
    scope_type: ScopeType
    scope_id: str
    created_at: datetime
    expires_at: datetime | None

    @classmethod
    def from_grant(cls, grant: Grant) -> "GrantResponse":
        """Convert Grant model to response schema."""
        return cls(
            id=str(grant.id),
            principal_type=grant.principal_type,
            principal_id=str(grant.principal_id),
            role_id=str(grant.role_id),
            scope_type=grant.scope_type,
            scope_id=grant.scope_id,
            created_at=grant.created_at,
            expires_at=grant.expires_at,
        )


class GrantsListResponse(BaseModel):
    """Schema for list grants response."""

    grants: list[GrantResponse]


# Helper function
async def require_admin(user: CurrentActiveUser):
    """Ensure user is an admin."""
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin privileges required")


# API endpoints
@router.post("/", response_model=GrantResponse, status_code=201)
async def create_grant_route(
    req: GrantCreate,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> GrantResponse:
    """
    Create a new grant (role assignment).

    Requires admin privileges.
    """
    await require_admin(current_user)

    # Validate role exists
    role = await get_role_by_id(db, UUID(req.role_id))
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Validate principal exists (for users)
    if req.principal_type == PrincipalType.USER:
        principal_user = await get_user_by_id(db, UUID(req.principal_id))
        if not principal_user:
            raise HTTPException(status_code=404, detail="User not found")

    # Create grant
    grant = await create_grant(
        db=db,
        principal_type=req.principal_type,
        principal_id=UUID(req.principal_id),
        role_id=UUID(req.role_id),
        scope_type=req.scope_type,
        scope_id=req.scope_id,
        expires_at=req.expires_at,
    )

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_CREATED,
        resource_type="grant",
        resource_id=str(grant.id),
        after_state={
            "principal_type": grant.principal_type,
            "principal_id": grant.principal_id,
            "role_id": grant.role_id,
            "scope_type": grant.scope_type,
            "scope_id": grant.scope_id,
            "expires_at": grant.expires_at.isoformat() if grant.expires_at else None,
        },
    )

    return GrantResponse.from_grant(grant)


@router.get("/{grant_id}", response_model=GrantResponse)
async def get_grant_route(
    grant_id: str,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> GrantResponse:
    """
    Get a specific grant by ID.

    Requires admin privileges.
    """
    await require_admin(current_user)

    grant = await get_grant_by_id(db, UUID(grant_id))
    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")

    return GrantResponse.from_grant(grant)


@router.get("/", response_model=GrantsListResponse)
async def list_grants_route(
    current_user: CurrentActiveUser,
    db: DbSession,
    principal_type: Annotated[PrincipalType | None, Query()] = None,
    principal_id: Annotated[str | None, Query()] = None,
    scope_type: Annotated[ScopeType | None, Query()] = None,
    scope_id: Annotated[str | None, Query()] = None,
    role_id: Annotated[str | None, Query()] = None,
) -> GrantsListResponse:
    """
    List grants with optional filtering.

    Requires admin privileges.

    Query parameters:
    - principal_type: Filter by principal type (user, group, service_account)
    - principal_id: Filter by principal ID
    - scope_type: Filter by scope type (workspace, project, environment, flow, component)
    - scope_id: Filter by scope ID
    - role_id: Filter by role ID
    """
    await require_admin(current_user)

    # Start with all grants query
    if principal_type and principal_id:
        grants = await get_grants_for_principal(db, principal_type, UUID(principal_id))
    elif scope_type and scope_id:
        grants = await get_grants_for_scope(db, scope_type, scope_id)
    else:
        # Get all grants (no specific filter)
        from sqlmodel import select

        stmt = select(Grant)

        # Apply filters
        if principal_type:
            stmt = stmt.where(Grant.principal_type == principal_type)
        if principal_id:
            stmt = stmt.where(Grant.principal_id == principal_id)
        if scope_type:
            stmt = stmt.where(Grant.scope_type == scope_type)
        if scope_id:
            stmt = stmt.where(Grant.scope_id == scope_id)
        if role_id:
            stmt = stmt.where(Grant.role_id == role_id)

        # Filter out expired grants
        now = datetime.now()
        stmt = stmt.where((Grant.expires_at.is_(None)) | (Grant.expires_at > now))

        result = await db.exec(stmt)
        grants = list(result.all())

    return GrantsListResponse(grants=[GrantResponse.from_grant(g) for g in grants])


@router.patch("/{grant_id}", response_model=GrantResponse)
async def update_grant_route(
    grant_id: str,
    req: GrantUpdate,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> GrantResponse:
    """
    Update a grant (change expiration or scope).

    Requires admin privileges.
    """
    await require_admin(current_user)

    # Get existing grant
    grant = await get_grant_by_id(db, UUID(grant_id))
    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")

    # Capture before state
    before_state = {
        "scope_type": grant.scope_type,
        "scope_id": grant.scope_id,
        "expires_at": grant.expires_at.isoformat() if grant.expires_at else None,
    }

    # Update fields
    if req.expires_at is not None:
        grant.expires_at = req.expires_at
    if req.scope_type is not None:
        grant.scope_type = req.scope_type
    if req.scope_id is not None:
        grant.scope_id = req.scope_id

    db.add(grant)
    await db.commit()
    await db.refresh(grant)

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_UPDATED,
        resource_type="grant",
        resource_id=str(grant.id),
        before_state=before_state,
        after_state={
            "scope_type": grant.scope_type,
            "scope_id": grant.scope_id,
            "expires_at": grant.expires_at.isoformat() if grant.expires_at else None,
        },
    )

    return GrantResponse.from_grant(grant)


@router.delete("/{grant_id}", status_code=204)
async def revoke_grant_route(
    grant_id: str,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> None:
    """
    Revoke a grant (delete).

    Requires admin privileges.
    """
    await require_admin(current_user)

    # Get grant for audit log
    grant = await get_grant_by_id(db, UUID(grant_id))
    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")

    # Delete grant
    success = await delete_grant(db, UUID(grant_id))
    if not success:
        raise HTTPException(status_code=500, detail="Failed to revoke grant")

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_REVOKED,
        resource_type="grant",
        resource_id=grant_id,
        before_state={
            "principal_type": grant.principal_type,
            "principal_id": grant.principal_id,
            "role_id": grant.role_id,
            "scope_type": grant.scope_type,
            "scope_id": grant.scope_id,
            "expires_at": grant.expires_at.isoformat() if grant.expires_at else None,
        },
    )


@router.get("/principal/{principal_type}/{principal_id}", response_model=GrantsListResponse)
async def list_grants_for_principal_route(
    principal_type: PrincipalType,
    principal_id: str,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> GrantsListResponse:
    """
    Get all grants for a specific principal (user, group, or service account).

    Requires admin privileges.
    """
    await require_admin(current_user)

    grants = await get_grants_for_principal(db, principal_type, UUID(principal_id))
    return GrantsListResponse(grants=[GrantResponse.from_grant(g) for g in grants])


@router.get("/scope/{scope_type}/{scope_id}", response_model=GrantsListResponse)
async def list_grants_for_scope_route(
    scope_type: ScopeType,
    scope_id: str,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> GrantsListResponse:
    """
    Get all grants for a specific scope (workspace, project, etc.).

    Requires admin privileges.
    """
    await require_admin(current_user)

    grants = await get_grants_for_scope(db, scope_type, scope_id)
    return GrantsListResponse(grants=[GrantResponse.from_grant(g) for g in grants])
