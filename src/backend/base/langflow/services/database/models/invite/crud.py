from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.auth.rbac import check_permission
from langflow.services.database.models.grant.crud import create_grant
from langflow.services.database.models.grant.model import PrincipalType, ScopeType
from langflow.services.database.models.invite.model import Invite, InviteStatus
from langflow.services.database.models.user.crud import get_user_by_username


async def create_invite(
    db: AsyncSession,
    inviter_id: UUID,
    invitee_email: str,
    workspace_id: str,
    role_id: UUID,
) -> Invite:
    """
    Create a new invitation.

    Args:
        db: Database session
        inviter_id: User ID of inviter
        invitee_email: Email of person being invited
        workspace_id: Workspace they're being invited to
        role_id: Role they'll receive

    Returns:
        Created Invite

    Raises:
        HTTPException: If inviter lacks invite_users permission
    """
    # RBAC: Check if inviter has invite_users permission at workspace scope
    has_permission = await check_permission(
        db=db,
        user_id=inviter_id,
        action="invite_users",
        resource_type="workspaces",
        resource_id=workspace_id,
        scope_type=ScopeType.WORKSPACE,
        scope_id=workspace_id,
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission_required:invite_users",
        )

    invite = Invite(
        inviter_id=str(inviter_id),
        invitee_email=invitee_email,
        workspace_id=workspace_id,
        role_id=str(role_id),
    )

    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite


async def accept_invite(
    db: AsyncSession,
    invite_id: UUID,
    accepting_user_email: str,
) -> bool:
    """
    Accept an invitation and create grant.

    Args:
        db: Database session
        invite_id: ID of invite to accept
        accepting_user_email: Email of user accepting

    Returns:
        True if accepted successfully

    Raises:
        HTTPException: If invite invalid or user not authorized
    """
    if isinstance(invite_id, str):
        invite_id = UUID(invite_id)

    # Get invite
    stmt = select(Invite).where(Invite.id == invite_id)
    invite = (await db.exec(stmt)).first()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found",
        )

    # Check if user can accept (correct email, not expired, pending)
    if not invite.can_accept(accepting_user_email):
        if invite.invitee_email.lower() != accepting_user_email.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="invite_not_for_user",
            )
        if invite.is_expired():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invite has expired",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invite cannot be accepted (status: {invite.status})",
        )

    # Get user by email
    user = await get_user_by_username(db, accepting_user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found. Please sign up first.",
        )

    # Create grant (role assignment)
    await create_grant(
        db=db,
        principal_type=PrincipalType.USER,
        principal_id=user.id,
        role_id=UUID(invite.role_id),
        scope_type=ScopeType.WORKSPACE,
        scope_id=invite.workspace_id,
    )

    # Update invite status
    invite.status = InviteStatus.ACCEPTED
    await db.commit()

    return True


async def get_pending_invites_for_email(
    db: AsyncSession,
    email: str,
) -> list[Invite]:
    """Get all pending, non-expired invites for an email."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(Invite)
        .where(Invite.invitee_email == email)
        .where(Invite.status == InviteStatus.PENDING)
        .where(Invite.expires_at > now)
    )
    result = await db.exec(stmt)
    return list(result.all())
