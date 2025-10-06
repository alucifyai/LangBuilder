"""
User Invites API
"""

from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.auth.utils import get_current_active_user, get_password_hash
from langflow.services.database.models.audit.crud import create_audit_log
from langflow.services.database.models.audit.model import AuditAction
from langflow.services.database.models.grant.crud import create_grant
from langflow.services.database.models.user.crud import create_user
from langflow.services.database.models.user.model import User
from langflow.services.database.models.user_invite.crud import (
    accept_invite,
    create_user_invite,
    delete_invite,
    get_invite_by_token,
    list_invites,
    revoke_invite,
)
from langflow.services.database.models.user_invite.model import InviteStatus
from langflow.services.deps import get_session

router = APIRouter(prefix="/invites", tags=["User Invites"])


# Request/Response Models
class InviteCreate(BaseModel):
    """Request to create a user invite."""

    email: EmailStr = Field(..., description="Invitee email address")
    role_ids: list[str] = Field(..., description="List of role IDs to assign")
    expires_in_days: int = Field(default=7, description="Days until invite expires")


class InviteResponse(BaseModel):
    """User invite response."""

    id: str
    email: str
    invited_by: str
    organization_id: str
    role_ids: list[str]
    status: InviteStatus
    invite_url: str
    created_at: str
    expires_at: str
    accepted_at: str | None = None
    revoked_at: str | None = None


class AcceptInviteRequest(BaseModel):
    """Request to accept an invite."""

    username: str = Field(..., description="Desired username")
    password: str = Field(..., min_length=8, description="Password")


class RevokeInviteRequest(BaseModel):
    """Request to revoke an invite."""

    reason: str | None = Field(None, description="Reason for revocation")


# Endpoints
@router.post("", response_model=InviteResponse, status_code=201)
async def create_invite(
    request: InviteCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> InviteResponse:
    """Create a new user invite."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    # Create invite
    invite = await create_user_invite(
        db=db,
        email=request.email,
        invited_by=current_user.id,
        organization_id="default",  # TODO: Get from user context
        role_ids=request.role_ids,
        expires_in_days=request.expires_in_days,
    )

    # Audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_CREATED,  # TODO: Add INVITE_CREATED
        resource_type="user_invite",
        resource_id=invite.id,
        metadata={"email": invite.email, "role_ids": invite.role_ids},
    )

    # Generate invite URL
    invite_url = f"{request.email}?token={invite.invite_token}"  # Simplified

    return InviteResponse(
        id=invite.id,
        email=invite.email,
        invited_by=invite.invited_by,
        organization_id=invite.organization_id,
        role_ids=invite.role_ids,
        status=invite.status,
        invite_url=invite_url,
        created_at=invite.created_at.isoformat(),
        expires_at=invite.expires_at.isoformat(),
        accepted_at=invite.accepted_at.isoformat() if invite.accepted_at else None,
        revoked_at=invite.revoked_at.isoformat() if invite.revoked_at else None,
    )


@router.get("", response_model=list[InviteResponse])
async def list_invites_route(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
    status: InviteStatus | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[InviteResponse]:
    """List invites for the organization."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    invites = await list_invites(db, "default", status, skip, limit)

    return [
        InviteResponse(
            id=invite.id,
            email=invite.email,
            invited_by=invite.invited_by,
            organization_id=invite.organization_id,
            role_ids=invite.role_ids,
            status=invite.status,
            invite_url=f"{invite.email}?token={invite.invite_token}",
            created_at=invite.created_at.isoformat(),
            expires_at=invite.expires_at.isoformat(),
            accepted_at=invite.accepted_at.isoformat() if invite.accepted_at else None,
            revoked_at=invite.revoked_at.isoformat() if invite.revoked_at else None,
        )
        for invite in invites
    ]


@router.post("/{token}/accept", response_model=dict)
async def accept_invite_route(
    token: str,
    request: AcceptInviteRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Accept an invite and create user account."""
    invite = await get_invite_by_token(db, token)

    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    if invite.status != InviteStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Invite is {invite.status}")

    # Create user
    user_data = {
        "username": request.username,
        "password": get_password_hash(request.password),
        "email": invite.email,
        "is_active": True,
        "is_superuser": False,
    }

    new_user = await create_user(db, **user_data)

    # Assign roles via grants
    for role_id in invite.role_ids:
        await create_grant(
            db=db,
            role_id=UUID(role_id),
            principal_type="user",
            principal_id=new_user.id,
            scope_type="workspace",
            scope_id="default",
            granted_by=UUID(invite.invited_by),
        )

    # Mark invite as accepted
    await accept_invite(db, invite.id, new_user.id)

    # Audit log
    await create_audit_log(
        db=db,
        actor_id=new_user.id,
        action=AuditAction.GRANT_CREATED,  # TODO: Add INVITE_ACCEPTED
        resource_type="user_invite",
        resource_id=invite.id,
        metadata={"user_id": str(new_user.id)},
    )

    return {"message": "Invite accepted", "user_id": str(new_user.id)}


@router.post("/{invite_id}/revoke", response_model=InviteResponse)
async def revoke_invite_route(
    invite_id: UUID,
    request: RevokeInviteRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> InviteResponse:
    """Revoke an invite."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    invite = await revoke_invite(db, invite_id, current_user.id, request.reason)

    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    # Audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_DELETED,  # TODO: Add INVITE_REVOKED
        resource_type="user_invite",
        resource_id=invite.id,
        metadata={"reason": request.reason},
    )

    return InviteResponse(
        id=invite.id,
        email=invite.email,
        invited_by=invite.invited_by,
        organization_id=invite.organization_id,
        role_ids=invite.role_ids,
        status=invite.status,
        invite_url=f"{invite.email}?token={invite.invite_token}",
        created_at=invite.created_at.isoformat(),
        expires_at=invite.expires_at.isoformat(),
        accepted_at=invite.accepted_at.isoformat() if invite.accepted_at else None,
        revoked_at=invite.revoked_at.isoformat() if invite.revoked_at else None,
    )


@router.delete("/{invite_id}", status_code=204)
async def delete_invite_route(
    invite_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete an invite."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    success = await delete_invite(db, invite_id)
    if not success:
        raise HTTPException(status_code=404, detail="Invite not found")

    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_DELETED,
        resource_type="user_invite",
        resource_id=str(invite_id),
    )
