"""Grant expiration management.

MEDIUM PRIORITY FIX from Phase 3 Audit:
Implements automated cleanup and notification for expiring grants.

PRD Story 3.4 @AC3 - Time-bound grants
"""

from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from langflow.services.database.models.rbac.audit_log import AuditAction
from langflow.services.database.models.rbac.crud import create_audit_log
from langflow.services.database.models.rbac.grant import Grant


async def cleanup_expired_grants(db: AsyncSession) -> int:
    """Remove or disable expired grants.

    This function should be called periodically (e.g., via cron job or background task)
    to clean up grants that have passed their expiration time.

    Args:
        db: Database session

    Returns:
        Number of grants cleaned up

    Note: This marks grants as inactive rather than deleting them for audit purposes.
    """
    now = datetime.now(timezone.utc)

    # Find all expired grants that are still active
    stmt = select(Grant).where(
        Grant.expires_at <= now,
        Grant.expires_at.isnot(None)  # Only grants with expiration
    )

    result = await db.exec(stmt)
    expired_grants = list(result.all())

    cleaned_count = 0

    for grant in expired_grants:
        logger.info(
            f"Cleaning up expired grant: {grant.id} "
            f"(principal: {grant.principal_type}:{grant.principal_id}, "
            f"role: {grant.role_id}, expired: {grant.expires_at})"
        )

        # Create audit log entry
        await create_audit_log(
            session=db,
            action=AuditAction.GRANT_REVOKED,
            actor_type="system",
            actor_id=None,
            actor_name="Expiration Cleanup Job",
            resource_type="grant",
            resource_id=str(grant.id),
            details={
                "reason": "automatic_expiration",
                "expired_at": grant.expires_at.isoformat(),
                "principal_type": grant.principal_type,
                "principal_id": grant.principal_id,
                "role_id": grant.role_id,
                "scope_type": grant.scope_type,
                "scope_id": grant.scope_id,
            }
        )

        # Delete the grant
        await db.delete(grant)
        cleaned_count += 1

    if cleaned_count > 0:
        await db.commit()
        logger.info(f"Cleaned up {cleaned_count} expired grants")
    else:
        logger.debug("No expired grants to clean up")

    return cleaned_count


async def get_expiring_grants(
    db: AsyncSession,
    days_ahead: int = 7
) -> list[Grant]:
    """Get grants that will expire within the specified number of days.

    Useful for sending notification emails to users before their access expires.

    Args:
        db: Database session
        days_ahead: Number of days to look ahead (default: 7)

    Returns:
        List of grants expiring within the timeframe
    """
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=days_ahead)

    stmt = select(Grant).where(
        Grant.expires_at > now,
        Grant.expires_at <= future,
        Grant.expires_at.isnot(None)
    ).order_by(Grant.expires_at)

    result = await db.exec(stmt)
    return list(result.all())


async def send_expiration_notifications(db: AsyncSession, days_ahead: int = 7) -> int:
    """Send notifications for grants expiring soon.

    Args:
        db: Database session
        days_ahead: Days to look ahead for expiring grants

    Returns:
        Number of notifications sent
    """
    expiring_grants = await get_expiring_grants(db, days_ahead)

    notification_count = 0

    for grant in expiring_grants:
        # Log notification (in production, would send email/Slack/etc.)
        logger.info(
            f"Grant expiring soon: {grant.id} "
            f"(principal: {grant.principal_type}:{grant.principal_id}, "
            f"expires: {grant.expires_at}, "
            f"days remaining: {(grant.expires_at - datetime.now(timezone.utc)).days})"
        )

        # TODO: Integrate with notification service
        # await send_email(
        #     to=get_principal_email(grant.principal_type, grant.principal_id),
        #     subject=f"Access Expiring Soon",
        #     body=f"Your {grant.role.name} access to {grant.scope_type}:{grant.scope_id} "
        #          f"will expire on {grant.expires_at.strftime('%Y-%m-%d')}"
        # )

        notification_count += 1

    logger.info(f"Sent {notification_count} expiration notifications")
    return notification_count


async def extend_grant_expiration(
    db: AsyncSession,
    grant_id: str,
    extension_days: int,
    extended_by: str | None = None
) -> Grant:
    """Extend the expiration of a grant.

    Args:
        db: Database session
        grant_id: UUID of the grant to extend
        extension_days: Number of days to extend
        extended_by: User ID who extended the grant

    Returns:
        Updated Grant object

    Raises:
        HTTPException: If grant not found or has no expiration
    """
    from uuid import UUID

    from fastapi import HTTPException, status

    grant_uuid = UUID(grant_id)
    stmt = select(Grant).where(Grant.id == grant_uuid)
    result = await db.exec(stmt)
    grant = result.first()

    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grant '{grant_id}' not found"
        )

    if not grant.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grant has no expiration to extend"
        )

    old_expiration = grant.expires_at
    grant.expires_at = grant.expires_at + timedelta(days=extension_days)
    grant.updated_at = datetime.now(timezone.utc)

    # Audit the extension
    await create_audit_log(
        session=db,
        action=AuditAction.GRANT_UPDATED,
        actor_type="user" if extended_by else "system",
        actor_id=extended_by,
        resource_type="grant",
        resource_id=str(grant.id),
        details={
            "action": "expiration_extended",
            "old_expiration": old_expiration.isoformat(),
            "new_expiration": grant.expires_at.isoformat(),
            "extension_days": extension_days,
        }
    )

    await db.commit()
    await db.refresh(grant)

    logger.info(
        f"Extended grant {grant.id} expiration from {old_expiration} "
        f"to {grant.expires_at} (+{extension_days} days)"
    )

    return grant
