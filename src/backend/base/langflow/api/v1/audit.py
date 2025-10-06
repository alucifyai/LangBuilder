from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.audit.crud import (
    get_audit_logs_by_action,
    get_audit_logs_by_actor,
    get_audit_logs_by_date_range,
    get_audit_logs_for_resource,
)
from langflow.services.database.models.audit.model import AuditAction, AuditLog

router = APIRouter(tags=["Audit"], prefix="/audit")


# Response Schemas
class AuditLogResponse(BaseModel):
    """Response schema for audit log entry."""

    id: UUID
    timestamp: datetime
    actor_id: UUID
    action: AuditAction
    resource_type: str
    resource_id: str
    before_state: dict[str, Any] | None
    after_state: dict[str, Any] | None
    metadata: dict[str, Any] | None


class AuditLogsListResponse(BaseModel):
    """Response schema for list of audit logs."""

    total_count: int
    logs: list[AuditLogResponse]


# Helper function to check admin privileges
async def require_admin(current_user: CurrentActiveUser) -> None:
    """
    Check if current user is an admin.

    Raises:
        HTTPException: 403 if user is not an admin
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="admin_required: Only administrators can view audit logs",
        )


def audit_log_to_response(log: AuditLog) -> AuditLogResponse:
    """Convert AuditLog model to response schema."""
    return AuditLogResponse(
        id=UUID(log.id),
        timestamp=log.timestamp,
        actor_id=UUID(log.actor_id),
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        before_state=log.before_state,
        after_state=log.after_state,
        metadata=log.metadata,
    )


@router.get("/", response_model=AuditLogsListResponse)
async def list_audit_logs(
    current_user: CurrentActiveUser,
    db: DbSession,
    resource_type: str | None = Query(None, description="Filter by resource type (e.g., 'role', 'grant')"),
    resource_id: str | None = Query(None, description="Filter by specific resource ID"),
    action: AuditAction | None = Query(None, description="Filter by action type"),
    actor_id: UUID | None = Query(None, description="Filter by actor (user) ID"),
    start_date: datetime | None = Query(None, description="Filter by start date (ISO 8601)"),
    end_date: datetime | None = Query(None, description="Filter by end date (ISO 8601)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of entries to return"),
) -> AuditLogsListResponse:
    """
    List audit logs with optional filtering.

    Requires admin privileges.

    Query parameters allow filtering by:
    - resource_type + resource_id: Get logs for specific resource
    - action: Get logs for specific action type
    - actor_id: Get logs for specific user
    - start_date + end_date: Get logs within date range
    """
    await require_admin(current_user)

    logs: list[AuditLog] = []

    # Priority order for filters
    if resource_type and resource_id:
        # Filter by specific resource
        logs = await get_audit_logs_for_resource(db, resource_type, resource_id, limit)
    elif resource_type and not resource_id:
        # Filter by resource type only
        logs = await get_audit_logs_for_resource(db, resource_type, None, limit)
    elif action:
        # Filter by action type
        logs = await get_audit_logs_by_action(db, action, limit)
    elif actor_id:
        # Filter by actor
        logs = await get_audit_logs_by_actor(db, actor_id, limit)
    elif start_date and end_date:
        # Filter by date range
        logs = await get_audit_logs_by_date_range(db, start_date, end_date, resource_type, limit)
    else:
        # No filters - return recent logs for all resource types
        # Default to role logs if no filters specified
        logs = await get_audit_logs_for_resource(db, "role", None, limit)

    return AuditLogsListResponse(
        total_count=len(logs),
        logs=[audit_log_to_response(log) for log in logs],
    )


@router.get("/{audit_id}", response_model=AuditLogResponse)
async def get_audit_log(
    audit_id: UUID,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> AuditLogResponse:
    """
    Get a specific audit log entry by ID.

    Requires admin privileges.

    Args:
        audit_id: Audit log entry ID

    Returns:
        Audit log entry

    Raises:
        HTTPException:
            - 403 if not admin
            - 404 if audit log not found
    """
    await require_admin(current_user)

    # Get audit log by ID
    from sqlmodel import select

    stmt = select(AuditLog).where(AuditLog.id == str(audit_id))
    result = await db.exec(stmt)
    log = result.first()

    if not log:
        raise HTTPException(status_code=404, detail="Audit log entry not found")

    return audit_log_to_response(log)
