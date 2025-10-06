"""
CRUD operations for Enhanced Audit Logs
"""

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.audit_log.model import AuditLog, AuditLogExport


async def create_audit_log(
    db: AsyncSession,
    event_type: str,
    action: str,
    actor_id: str | None = None,
    actor_type: str | None = None,
    actor_email: str | None = None,
    target_id: str | None = None,
    target_type: str | None = None,
    target_name: str | None = None,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    session_id: str | None = None,
    request_id: str | None = None,
    severity: str = "info",
    status: str = "success",
    changes: dict | None = None,
    metadata: dict | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    compliance_tags: list[str] | None = None,
    retention_days: int | None = None,
) -> AuditLog:
    """Create an audit log entry."""
    # Build search text for full-text search
    search_parts = [
        event_type,
        action,
        actor_email or "",
        target_name or "",
        target_type or "",
    ]
    search_text = " ".join(filter(None, search_parts)).lower()

    log_entry = AuditLog(
        event_type=event_type,
        action=action,
        severity=severity,
        status=status,
        actor_id=actor_id,
        actor_type=actor_type,
        actor_email=actor_email,
        target_id=target_id,
        target_type=target_type,
        target_name=target_name,
        organization_id=organization_id,
        workspace_id=workspace_id,
        ip_address=ip_address,
        user_agent=user_agent,
        session_id=session_id,
        request_id=request_id,
        changes=changes,
        metadata=metadata,
        error_code=error_code,
        error_message=error_message,
        compliance_tags=compliance_tags,
        retention_days=retention_days,
        search_text=search_text,
    )

    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    return log_entry


async def get_audit_log_by_id(
    db: AsyncSession,
    log_id: UUID | str,
) -> AuditLog | None:
    """Get audit log entry by ID."""
    stmt = select(AuditLog).where(AuditLog.id == str(log_id))
    return (await db.exec(stmt)).first()


async def list_audit_logs(
    db: AsyncSession,
    event_type: str | None = None,
    action: str | None = None,
    actor_id: str | None = None,
    target_id: str | None = None,
    target_type: str | None = None,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    ip_address: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    """
    List audit logs with filtering.
    Returns (logs, total_count).
    """
    stmt = select(AuditLog)
    count_stmt = select(AuditLog)

    # Apply filters
    if event_type:
        stmt = stmt.where(AuditLog.event_type == event_type)
        count_stmt = count_stmt.where(AuditLog.event_type == event_type)

    if action:
        stmt = stmt.where(AuditLog.action == action)
        count_stmt = count_stmt.where(AuditLog.action == action)

    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
        count_stmt = count_stmt.where(AuditLog.actor_id == actor_id)

    if target_id:
        stmt = stmt.where(AuditLog.target_id == target_id)
        count_stmt = count_stmt.where(AuditLog.target_id == target_id)

    if target_type:
        stmt = stmt.where(AuditLog.target_type == target_type)
        count_stmt = count_stmt.where(AuditLog.target_type == target_type)

    if organization_id:
        stmt = stmt.where(AuditLog.organization_id == organization_id)
        count_stmt = count_stmt.where(AuditLog.organization_id == organization_id)

    if workspace_id:
        stmt = stmt.where(AuditLog.workspace_id == workspace_id)
        count_stmt = count_stmt.where(AuditLog.workspace_id == workspace_id)

    if severity:
        stmt = stmt.where(AuditLog.severity == severity)
        count_stmt = count_stmt.where(AuditLog.severity == severity)

    if status:
        stmt = stmt.where(AuditLog.status == status)
        count_stmt = count_stmt.where(AuditLog.status == status)

    if ip_address:
        stmt = stmt.where(AuditLog.ip_address == ip_address)
        count_stmt = count_stmt.where(AuditLog.ip_address == ip_address)

    if start_date:
        stmt = stmt.where(AuditLog.timestamp >= start_date)
        count_stmt = count_stmt.where(AuditLog.timestamp >= start_date)

    if end_date:
        stmt = stmt.where(AuditLog.timestamp <= end_date)
        count_stmt = count_stmt.where(AuditLog.timestamp <= end_date)

    if search:
        search_lower = search.lower()
        stmt = stmt.where(AuditLog.search_text.contains(search_lower))
        count_stmt = count_stmt.where(AuditLog.search_text.contains(search_lower))

    # Get total count
    total_count = len(list((await db.exec(count_stmt)).all()))

    # Apply ordering, limit, offset
    stmt = stmt.order_by(AuditLog.timestamp.desc())
    stmt = stmt.offset(offset).limit(limit)

    logs = list((await db.exec(stmt)).all())
    return logs, total_count


async def get_audit_logs_by_actor(
    db: AsyncSession,
    actor_id: str,
    limit: int = 100,
) -> list[AuditLog]:
    """Get audit logs for a specific actor."""
    stmt = (
        select(AuditLog)
        .where(AuditLog.actor_id == actor_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )
    return list((await db.exec(stmt)).all())


async def get_audit_logs_by_target(
    db: AsyncSession,
    target_id: str,
    target_type: str | None = None,
    limit: int = 100,
) -> list[AuditLog]:
    """Get audit logs for a specific target resource."""
    stmt = select(AuditLog).where(AuditLog.target_id == target_id)

    if target_type:
        stmt = stmt.where(AuditLog.target_type == target_type)

    stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(limit)
    return list((await db.exec(stmt)).all())


async def get_failed_authentication_attempts(
    db: AsyncSession,
    hours: int = 24,
    min_attempts: int = 3,
) -> dict[str, list[AuditLog]]:
    """
    Get failed authentication attempts grouped by IP/actor.
    Useful for security monitoring and anomaly detection.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    stmt = (
        select(AuditLog)
        .where(AuditLog.event_type == "auth")
        .where(AuditLog.status == "failure")
        .where(AuditLog.timestamp >= cutoff)
        .order_by(AuditLog.timestamp.desc())
    )

    failed_attempts = list((await db.exec(stmt)).all())

    # Group by IP address
    by_ip: dict[str, list[AuditLog]] = {}
    for attempt in failed_attempts:
        if attempt.ip_address:
            if attempt.ip_address not in by_ip:
                by_ip[attempt.ip_address] = []
            by_ip[attempt.ip_address].append(attempt)

    # Filter to only IPs with minimum attempts
    return {ip: attempts for ip, attempts in by_ip.items() if len(attempts) >= min_attempts}


async def get_security_events(
    db: AsyncSession,
    hours: int = 24,
) -> list[AuditLog]:
    """Get security-relevant events (high severity, failures, etc.)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    stmt = (
        select(AuditLog)
        .where(AuditLog.timestamp >= cutoff)
        .where(
            or_(
                AuditLog.severity.in_(["warning", "error", "critical"]),
                AuditLog.status == "failure",
                AuditLog.event_type == "security",
            )
        )
        .order_by(AuditLog.timestamp.desc())
    )
    return list((await db.exec(stmt)).all())


async def cleanup_old_audit_logs(
    db: AsyncSession,
    default_retention_days: int = 90,
) -> int:
    """
    Clean up old audit logs based on retention policies.
    Returns count of deleted records.
    """
    # Delete logs past their retention period
    cutoff = datetime.now(timezone.utc) - timedelta(days=default_retention_days)

    # For logs with custom retention, use that; otherwise use default
    stmt = select(AuditLog).where(
        or_(
            and_(
                AuditLog.retention_days != None,  # noqa: E711
                AuditLog.timestamp
                <= datetime.now(timezone.utc) - timedelta(days=AuditLog.retention_days),
            ),
            and_(AuditLog.retention_days == None, AuditLog.timestamp <= cutoff),  # noqa: E711
        )
    )

    old_logs = list((await db.exec(stmt)).all())
    count = len(old_logs)

    for log in old_logs:
        await db.delete(log)

    await db.commit()
    return count


# Export tracking


async def create_audit_export(
    db: AsyncSession,
    export_type: str,
    format: str,
    start_date: datetime,
    end_date: datetime,
    exported_by: str,
    filters: dict | None = None,
    record_count: int = 0,
    file_path: str | None = None,
    file_hash: str | None = None,
    reason: str | None = None,
) -> AuditLogExport:
    """Create an audit log export record."""
    export_record = AuditLogExport(
        export_type=export_type,
        format=format,
        start_date=start_date,
        end_date=end_date,
        exported_by=exported_by,
        filters=filters,
        record_count=record_count,
        file_path=file_path,
        file_hash=file_hash,
        reason=reason,
    )

    db.add(export_record)
    await db.commit()
    await db.refresh(export_record)
    return export_record


async def list_audit_exports(
    db: AsyncSession,
    exported_by: str | None = None,
    export_type: str | None = None,
    limit: int = 50,
) -> list[AuditLogExport]:
    """List audit log exports."""
    stmt = select(AuditLogExport)

    if exported_by:
        stmt = stmt.where(AuditLogExport.exported_by == exported_by)

    if export_type:
        stmt = stmt.where(AuditLogExport.export_type == export_type)

    stmt = stmt.order_by(AuditLogExport.created_at.desc()).limit(limit)
    return list((await db.exec(stmt)).all())
