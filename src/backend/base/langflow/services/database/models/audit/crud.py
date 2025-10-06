from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.audit.model import AuditAction, AuditLog


async def create_audit_log(
    db: AsyncSession,
    actor_id: UUID,
    action: AuditAction,
    resource_type: str,
    resource_id: str,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """
    Create an audit log entry.

    Args:
        db: Database session
        actor_id: User who performed the action
        action: Type of action performed
        resource_type: Type of resource affected
        resource_id: ID of affected resource
        before_state: State before change (optional)
        after_state: State after change (optional)
        metadata: Additional context (optional)

    Returns:
        Created AuditLog entry
    """
    audit_log = AuditLog(
        actor_id=str(actor_id),
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before_state=before_state,
        after_state=after_state,
        metadata=metadata,
    )

    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)
    return audit_log


async def get_audit_logs_for_resource(
    db: AsyncSession,
    resource_type: str,
    resource_id: str | None = None,
    limit: int = 100,
) -> list[AuditLog]:
    """
    Get audit logs for a specific resource.

    Args:
        db: Database session
        resource_type: Type of resource (e.g., "role", "grant")
        resource_id: Specific resource ID (optional, if None returns all for type)
        limit: Maximum number of entries to return

    Returns:
        List of audit log entries, ordered by timestamp descending
    """
    stmt = select(AuditLog).where(AuditLog.resource_type == resource_type)

    if resource_id:
        stmt = stmt.where(AuditLog.resource_id == resource_id)

    stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(limit)

    result = await db.exec(stmt)
    return list(result.all())


async def get_audit_logs_by_actor(
    db: AsyncSession,
    actor_id: UUID,
    limit: int = 100,
) -> list[AuditLog]:
    """
    Get audit logs for a specific actor.

    Args:
        db: Database session
        actor_id: User who performed actions
        limit: Maximum number of entries to return

    Returns:
        List of audit log entries, ordered by timestamp descending
    """
    stmt = (
        select(AuditLog)
        .where(AuditLog.actor_id == str(actor_id))
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )

    result = await db.exec(stmt)
    return list(result.all())


async def get_audit_logs_by_action(
    db: AsyncSession,
    action: AuditAction,
    limit: int = 100,
) -> list[AuditLog]:
    """
    Get audit logs for a specific action type.

    Args:
        db: Database session
        action: Action type to filter by
        limit: Maximum number of entries to return

    Returns:
        List of audit log entries, ordered by timestamp descending
    """
    stmt = select(AuditLog).where(AuditLog.action == action).order_by(AuditLog.timestamp.desc()).limit(limit)

    result = await db.exec(stmt)
    return list(result.all())


async def get_audit_logs_by_date_range(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    resource_type: str | None = None,
    limit: int = 100,
) -> list[AuditLog]:
    """
    Get audit logs within a date range.

    Args:
        db: Database session
        start_date: Start of date range
        end_date: End of date range
        resource_type: Optional resource type filter
        limit: Maximum number of entries to return

    Returns:
        List of audit log entries, ordered by timestamp descending
    """
    stmt = select(AuditLog).where(AuditLog.timestamp >= start_date).where(AuditLog.timestamp <= end_date)

    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)

    stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(limit)

    result = await db.exec(stmt)
    return list(result.all())
