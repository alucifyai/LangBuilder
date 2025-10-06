from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.invite.crud import (
    accept_invite,
    create_invite,
    get_pending_invites_for_email,
)
from langflow.services.database.models.invite.model import Invite

router = APIRouter(tags=["Invites"], prefix="/invites")


class InviteCreateRequest(BaseModel):
    """Request to create an invitation."""

    invitee_email: EmailStr
    workspace_id: str
    role_id: UUID


class InviteResponse(BaseModel):
    """Response model for an invitation."""

    id: str
    inviter_id: str
    invitee_email: str
    workspace_id: str
    role_id: str
    status: str
    created_at: str
    expires_at: str


@router.post("/", response_model=InviteResponse)
async def create_invite_route(
    request: InviteCreateRequest,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> InviteResponse:
    """
    Create a new invitation.

    Requires invite_users permission at the workspace scope.
    """
    try:
        invite = await create_invite(
            db=db,
            inviter_id=current_user.id,
            invitee_email=request.invitee_email,
            workspace_id=request.workspace_id,
            role_id=request.role_id,
        )

        return InviteResponse(
            id=str(invite.id),
            inviter_id=str(invite.inviter_id),
            invitee_email=invite.invitee_email,
            workspace_id=invite.workspace_id,
            role_id=str(invite.role_id),
            status=invite.status,
            created_at=invite.created_at.isoformat(),
            expires_at=invite.expires_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{invite_id}/accept")
async def accept_invite_route(
    invite_id: UUID,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> dict:
    """
    Accept an invitation.

    Only the invited user (matching email) can accept.
    """
    try:
        success = await accept_invite(
            db=db,
            invite_id=invite_id,
            accepting_user_email=current_user.username,  # Assuming username is email
        )

        return {"success": success, "message": "Invitation accepted successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/pending", response_model=list[InviteResponse])
async def get_my_pending_invites(
    current_user: CurrentActiveUser,
    db: DbSession,
) -> list[InviteResponse]:
    """Get all pending invitations for the current user's email."""
    try:
        invites = await get_pending_invites_for_email(
            db=db,
            email=current_user.username,  # Assuming username is email
        )

        return [
            InviteResponse(
                id=str(invite.id),
                inviter_id=str(invite.inviter_id),
                invitee_email=invite.invitee_email,
                workspace_id=invite.workspace_id,
                role_id=str(invite.role_id),
                status=invite.status,
                created_at=invite.created_at.isoformat(),
                expires_at=invite.expires_at.isoformat(),
            )
            for invite in invites
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
