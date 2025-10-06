"""
CRUD operations for Temporary Grants
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.grant.crud import revoke_grant
from langflow.services.database.models.temporary_grant.model import TemporaryGrant


async def create_temporary_grant(
    db: AsyncSession,
    grant_id: UUID | str,
    expires_at: datetime,
    created_by: UUID | str,
    starts_at: datetime | None = None,
    auto_revoke: bool = True,
    notify_before_expiry: bool = True,
    notification_hours: int = 24,
    max_extensions: int | None = None,
    reason: str | None = None,
) -> TemporaryGrant:
    """Create a temporary grant."""
    temp_grant = TemporaryGrant(
        grant_id=str(grant_id),
        starts_at=starts_at or datetime.now(timezone.utc),
        expires_at=expires_at,
        created_by=str(created_by),
        auto_revoke=auto_revoke,
        notify_before_expiry=notify_before_expiry,
        notification_hours=notification_hours,
        max_extensions=max_extensions,
        reason=reason,
    )

    db.add(temp_grant)
    await db.commit()
    await db.refresh(temp_grant)
    return temp_grant


async def get_temporary_grant_by_id(
    db: AsyncSession,
    temp_grant_id: UUID | str,
) -> TemporaryGrant | None:
    """Get temporary grant by ID."""
    stmt = select(TemporaryGrant).where(TemporaryGrant.id == str(temp_grant_id))
    return (await db.exec(stmt)).first()


async def get_temporary_grant_by_grant_id(
    db: AsyncSession,
    grant_id: UUID | str,
) -> TemporaryGrant | None:
    """Get temporary grant by base grant ID."""
    stmt = select(TemporaryGrant).where(TemporaryGrant.grant_id == str(grant_id))
    return (await db.exec(stmt)).first()


async def list_temporary_grants(
    db: AsyncSession,
    include_expired: bool = False,
) -> list[TemporaryGrant]:
    """List temporary grants."""
    stmt = select(TemporaryGrant)

    if not include_expired:
        stmt = stmt.where(TemporaryGrant.is_expired == False)  # noqa: E712

    stmt = stmt.order_by(TemporaryGrant.expires_at)
    return list((await db.exec(stmt)).all())


async def list_expiring_soon(
    db: AsyncSession,
    hours: int = 24,
) -> list[TemporaryGrant]:
    """List grants expiring within specified hours."""
    cutoff = datetime.now(timezone.utc) + timedelta(hours=hours)
    stmt = (
        select(TemporaryGrant)
        .where(TemporaryGrant.is_expired == False)  # noqa: E712
        .where(TemporaryGrant.expires_at <= cutoff)
        .where(TemporaryGrant.notified_at == None)  # noqa: E711
        .where(TemporaryGrant.notify_before_expiry == True)  # noqa: E712
    )
    return list((await db.exec(stmt)).all())


async def list_expired_grants(
    db: AsyncSession,
) -> list[TemporaryGrant]:
    """List grants that have expired but haven't been processed."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(TemporaryGrant)
        .where(TemporaryGrant.is_expired == False)  # noqa: E712
        .where(TemporaryGrant.expires_at <= now)
    )
    return list((await db.exec(stmt)).all())


async def extend_temporary_grant(
    db: AsyncSession,
    temp_grant_id: UUID | str,
    new_expires_at: datetime,
    extended_by: UUID | str,
) -> TemporaryGrant | None:
    """Extend a temporary grant's expiration."""
    temp_grant = await get_temporary_grant_by_id(db, temp_grant_id)
    if not temp_grant:
        return None

    # Check max extensions
    if temp_grant.max_extensions is not None:
        if temp_grant.extension_count >= temp_grant.max_extensions:
            return None

    # Cannot extend expired grants
    if temp_grant.is_expired:
        return None

    temp_grant.expires_at = new_expires_at
    temp_grant.extension_count += 1
    temp_grant.extended_by = str(extended_by)
    temp_grant.updated_at = datetime.now(timezone.utc)

    # Reset notification if it was already sent
    temp_grant.notified_at = None

    db.add(temp_grant)
    await db.commit()
    await db.refresh(temp_grant)
    return temp_grant


async def mark_notified(
    db: AsyncSession,
    temp_grant_id: UUID | str,
) -> None:
    """Mark that expiration notification was sent."""
    temp_grant = await get_temporary_grant_by_id(db, temp_grant_id)
    if temp_grant:
        temp_grant.notified_at = datetime.now(timezone.utc)
        db.add(temp_grant)
        await db.commit()


async def expire_grant(
    db: AsyncSession,
    temp_grant_id: UUID | str,
    revoke_base_grant: bool = True,
) -> TemporaryGrant | None:
    """Expire a temporary grant and optionally revoke the base grant."""
    temp_grant = await get_temporary_grant_by_id(db, temp_grant_id)
    if not temp_grant:
        return None

    # Mark as expired
    temp_grant.is_expired = True
    temp_grant.expired_at = datetime.now(timezone.utc)
    temp_grant.updated_at = datetime.now(timezone.utc)

    db.add(temp_grant)

    # Revoke base grant if configured
    if revoke_base_grant and temp_grant.auto_revoke:
        await revoke_grant(db, temp_grant.grant_id)

    await db.commit()
    await db.refresh(temp_grant)
    return temp_grant


async def process_expired_grants(
    db: AsyncSession,
) -> int:
    """
    Process all expired grants.
    Returns count of grants processed.
    """
    expired_grants = await list_expired_grants(db)
    count = 0

    for temp_grant in expired_grants:
        await expire_grant(db, temp_grant.id, revoke_base_grant=temp_grant.auto_revoke)
        count += 1

    return count


async def delete_temporary_grant(
    db: AsyncSession,
    temp_grant_id: UUID | str,
) -> bool:
    """Delete temporary grant tracking (does not affect base grant)."""
    temp_grant = await get_temporary_grant_by_id(db, temp_grant_id)
    if not temp_grant:
        return False

    await db.delete(temp_grant)
    await db.commit()
    return True
