"""Audit logging utility for RBAC operations.

This module provides functions for logging RBAC-related events to the audit log
for compliance, security auditing, and operational monitoring.
"""

from typing import Any
from uuid import UUID

from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.rbac.audit_log import AuditLog


async def log_audit_event(
    session: AsyncSession,
    *,
    actor_id: UUID,
    action: str,
    resource_type: str,
    resource_id: UUID | None = None,
    actor_type: str = "user",
    status: str = "success",
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog | None:
    """Log an audit event to the database.

    Args:
        session: Database session
        actor_id: ID of the user/service account performing the action
        action: Action performed (e.g., "service_account.created", "role.assigned")
        resource_type: Type of resource (e.g., "service_account", "role", "grant")
        resource_id: ID of the affected resource (optional)
        actor_type: Type of actor ("user", "service_account", "system")
        status: Status of the action ("success", "failure", "denied")
        details: Additional context (optional)
        ip_address: IP address of the actor (optional)
        user_agent: User agent string (optional)

    Returns:
        AuditLog: The created audit log entry, or None if logging failed

    Example:
        ```python
        await log_audit_event(
            session=session,
            actor_id=current_user.id,
            action="service_account.created",
            resource_type="service_account",
            resource_id=sa.id,
            details={"name": sa.name, "workspace_id": str(sa.workspace_id)}
        )
        ```
    """
    try:
        # Extract event_type from action (e.g., "service_account.created" -> "service_account")
        event_type = action.split(".")[0] if "." in action else action

        audit_entry = AuditLog(
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_type=actor_type,
            actor_id=actor_id,
            status=status,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        session.add(audit_entry)
        await session.flush()  # Flush to get ID, but don't commit yet

        logger.info(
            f"Audit event logged: {action} by {actor_type}:{actor_id} "
            f"on {resource_type}:{resource_id} - {status}"
        )

        return audit_entry

    except Exception as e:
        # Audit logging should not block operations
        # Log the error but don't raise - graceful degradation
        logger.error(f"Failed to log audit event '{action}': {e}")
        return None


async def log_audit_event_safe(
    session: AsyncSession,
    *,
    actor_id: UUID,
    action: str,
    resource_type: str,
    resource_id: UUID | None = None,
    actor_type: str = "user",
    status: str = "success",
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Safe wrapper for log_audit_event that never raises exceptions.

    This version is completely non-blocking and will not affect the main operation
    even if audit logging fails. Use this when audit logging should be best-effort.

    Args:
        Same as log_audit_event

    Returns:
        None
    """
    try:
        await log_audit_event(
            session=session,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_type=actor_type,
            status=status,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        # Completely suppress audit logging errors
        logger.warning(f"Audit logging failed for action '{action}': {e}")
