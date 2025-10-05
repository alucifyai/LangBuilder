"""Audit log query API endpoints.

Provides read-only access to RBAC audit logs.
PRD Story 5.1 - Log All RBAC Changes
PRD Story 5.2 - Export Compliance Report
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.api.v1.rbac.dependencies import RequireAuditLogRead
from langflow.services.database.models.rbac.audit_log import AuditLogRead
from langflow.services.database.models.rbac.crud import get_audit_log_by_id, list_audit_logs

router = APIRouter()


@router.get("", response_model=list[AuditLogRead])
async def get_audit_logs(
    db: DbSession,
    current_user: CurrentActiveUser,
    _perm: RequireAuditLogRead,
    action: str | None = Query(None, description="Filter by action type"),
    actor_id: str | None = Query(None, description="Filter by actor (user) ID"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    resource_id: str | None = Query(None, description="Filter by resource ID"),
    start_date: datetime | None = Query(None, description="Filter logs after this date (ISO 8601)"),
    end_date: datetime | None = Query(None, description="Filter logs before this date (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
):
    """Query audit logs with filters.

    Query Parameters (all optional):
    - action: Filter by audit action (e.g., "GRANT_CREATED", "ROLE_UPDATED")
    - actor_id: Filter by who performed the action
    - resource_type: Filter by resource type (e.g., "grant", "role")
    - resource_id: Filter by specific resource ID
    - start_date: Filter logs after this date (ISO 8601 format)
    - end_date: Filter logs before this date (ISO 8601 format)
    - limit: Max results (1-1000, default 100)
    - offset: Pagination offset (default 0)

    Returns:
        List of AuditLog objects (sorted by timestamp desc)

    Examples:
    - Recent grant changes: `?action=GRANT_CREATED&limit=50`
    - All actions by admin: `?actor_id={admin_user_id}`
    - Role modifications: `?resource_type=role&action=ROLE_UPDATED`
    - Date range: `?start_date=2025-01-01T00:00:00Z&end_date=2025-12-31T23:59:59Z`

    Requires: 'audit_log:read' permission
    PRD Story 5.1 @AC2 - Query audit logs
    PRD Story 5.2 @AC1 - Export user access report
    PRD Story 5.2 @AC3 - Filter by date range (HIGH PRIORITY FIX from Phase 3 Audit)
    """
    logs = await list_audit_logs(
        db=db,
        action=action,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return [AuditLogRead.model_validate(log, from_attributes=True) for log in logs]


@router.get("/{audit_log_id}", response_model=AuditLogRead)
async def get_audit_log(
    audit_log_id: UUID,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Get a specific audit log entry by ID.

    Args:
        audit_log_id: UUID of the audit log entry

    Returns:
        AuditLog object

    Raises:
        404: Audit log entry not found

    Note: Requires 'audit_log:read' permission
    """
    # TODO Phase 3: Add permission check

    log = await get_audit_log_by_id(db, audit_log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log '{audit_log_id}' not found",
        )
    return AuditLogRead.model_validate(log, from_attributes=True)
