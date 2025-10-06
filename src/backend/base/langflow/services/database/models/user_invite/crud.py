"""
CRUD operations for User Invites
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.user_invite.model import InviteStatus, UserInvite


async def create_user_invite(
    db: AsyncSession,
    email: str,
    invited_by: UUID,
    organization_id: str,
    role_ids: list[str],
    expires_in_days: int = 7,
) -> UserInvite:
    """Create a new user invite."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    invite = UserInvite(
        email=email,
        invited_by=str(invited_by),
        organization_id=organization_id,
        role_ids=role_ids,
        expires_at=expires_at,
    )

    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite


async def get_invite_by_id(db: AsyncSession, invite_id: UUID | str) -> UserInvite | None:
    """Get invite by ID."""
    stmt = select(UserInvite).where(UserInvite.id == str(invite_id))
    return (await db.exec(stmt)).first()


async def get_invite_by_token(db: AsyncSession, token: str) -> UserInvite | None:
    """Get invite by token."""
    stmt = select(UserInvite).where(UserInvite.invite_token == token)
    return (await db.exec(stmt)).first()


async def get_invite_by_email(db: AsyncSession, email: str) -> UserInvite | None:
    """Get pending invite by email."""
    stmt = select(UserInvite).where(
        UserInvite.email == email,
        UserInvite.status == InviteStatus.PENDING,
    )
    return (await db.exec(stmt)).first()


async def list_invites(
    db: AsyncSession,
    organization_id: str,
    status: InviteStatus | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[UserInvite]:
    """List invites for an organization."""
    stmt = select(UserInvite).where(UserInvite.organization_id == organization_id)

    if status:
        stmt = stmt.where(UserInvite.status == status)

    stmt = stmt.offset(skip).limit(limit).order_by(UserInvite.created_at.desc())

    return list((await db.exec(stmt)).all())


async def accept_invite(
    db: AsyncSession,
    invite_id: UUID | str,
    user_id: UUID,
) -> UserInvite | None:
    """Mark invite as accepted."""
    invite = await get_invite_by_id(db, invite_id)
    if not invite:
        return None

    invite.status = InviteStatus.ACCEPTED
    invite.accepted_at = datetime.now(timezone.utc)
    invite.accepted_by_user_id = str(user_id)

    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite


async def revoke_invite(
    db: AsyncSession,
    invite_id: UUID | str,
    revoked_by: UUID,
    reason: str | None = None,
) -> UserInvite | None:
    """Revoke an invite."""
    invite = await get_invite_by_id(db, invite_id)
    if not invite:
        return None

    invite.status = InviteStatus.REVOKED
    invite.revoked_at = datetime.now(timezone.utc)
    invite.revoked_by = str(revoked_by)
    invite.revocation_reason = reason

    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite


async def delete_invite(db: AsyncSession, invite_id: UUID | str) -> bool:
    """Delete an invite."""
    invite = await get_invite_by_id(db, invite_id)
    if not invite:
        return False

    await db.delete(invite)
    await db.commit()
    return True


async def cleanup_expired_invites(db: AsyncSession) -> int:
    """Mark expired invites (maintenance task)."""
    now = datetime.now(timezone.utc)
    stmt = select(UserInvite).where(
        UserInvite.expires_at < now,
        UserInvite.status == InviteStatus.PENDING,
    )

    expired_invites = (await db.exec(stmt)).all()
    count = 0

    for invite in expired_invites:
        invite.status = InviteStatus.EXPIRED
        db.add(invite)
        count += 1

    await db.commit()
    return count
