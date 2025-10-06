"""
API endpoints for Enhanced Audit Logs
"""

import csv
import io
import json
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.audit_log import crud
from langflow.services.database.models.audit_log.model import AuditLog, AuditLogExport
from langflow.services.deps import get_session

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


# Request/Response Models
class CreateAuditLogRequest(BaseModel):
    """Request to create an audit log entry."""

    event_type: str = Field(..., description="Event type")
    action: str = Field(..., description="Action taken")
    actor_id: str | None = Field(None, description="Actor ID")
    actor_type: str | None = Field(None, description="Actor type")
    actor_email: str | None = Field(None, description="Actor email")
    target_id: str | None = Field(None, description="Target resource ID")
    target_type: str | None = Field(None, description="Target resource type")
    target_name: str | None = Field(None, description="Target name")
    organization_id: str | None = Field(None, description="Organization ID")
    workspace_id: str | None = Field(None, description="Workspace ID")
    ip_address: str | None = Field(None, description="IP address")
    user_agent: str | None = Field(None, description="User agent")
    session_id: str | None = Field(None, description="Session ID")
    request_id: str | None = Field(None, description="Request ID")
    severity: str = Field("info", description="Severity level")
    status: str = Field("success", description="Status")
    changes: dict | None = Field(None, description="Changes made")
    metadata: dict | None = Field(None, description="Additional metadata")
    error_code: str | None = Field(None, description="Error code")
    error_message: str | None = Field(None, description="Error message")
    compliance_tags: list[str] | None = Field(None, description="Compliance tags")
    retention_days: int | None = Field(None, description="Retention period")


class AuditLogResponse(BaseModel):
    """Response with audit log details."""

    id: str
    event_type: str
    action: str
    severity: str
    status: str
    actor_id: str | None
    actor_type: str | None
    actor_email: str | None
    target_id: str | None
    target_type: str | None
    target_name: str | None
    organization_id: str | None
    workspace_id: str | None
    ip_address: str | None
    user_agent: str | None
    session_id: str | None
    request_id: str | None
    changes: dict | None
    metadata: dict | None
    error_code: str | None
    error_message: str | None
    compliance_tags: list[str] | None
    retention_days: int | None
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Response with paginated audit logs."""

    logs: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


class SecurityEventsSummary(BaseModel):
    """Summary of security events."""

    total_events: int
    critical_count: int
    error_count: int
    warning_count: int
    failed_auth_count: int
    events: list[AuditLogResponse]


class ExportAuditLogsRequest(BaseModel):
    """Request to export audit logs."""

    export_type: str = Field(..., description="Export type (compliance, security, investigation)")
    format: str = Field("json", description="Export format (json, csv)")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    filters: dict | None = Field(None, description="Additional filters")
    reason: str | None = Field(None, description="Reason for export")


class AuditLogExportResponse(BaseModel):
    """Response with export details."""

    id: str
    export_type: str
    format: str
    start_date: datetime
    end_date: datetime
    record_count: int
    file_hash: str | None
    exported_by: str
    reason: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# Endpoints
@router.post("", response_model=AuditLogResponse, status_code=status.HTTP_201_CREATED)
async def create_audit_log_entry(
    request: CreateAuditLogRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> AuditLog:
    """
    Create an audit log entry.
    Typically called internally by the system, but can be used for manual logging.
    """
    log_entry = await crud.create_audit_log(
        db=db,
        event_type=request.event_type,
        action=request.action,
        actor_id=request.actor_id,
        actor_type=request.actor_type,
        actor_email=request.actor_email,
        target_id=request.target_id,
        target_type=request.target_type,
        target_name=request.target_name,
        organization_id=request.organization_id,
        workspace_id=request.workspace_id,
        ip_address=request.ip_address,
        user_agent=request.user_agent,
        session_id=request.session_id,
        request_id=request.request_id,
        severity=request.severity,
        status=request.status,
        changes=request.changes,
        metadata=request.metadata,
        error_code=request.error_code,
        error_message=request.error_message,
        compliance_tags=request.compliance_tags,
        retention_days=request.retention_days,
    )
    return log_entry


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs_route(
    db: Annotated[AsyncSession, Depends(get_session)],
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
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    # TODO: Add current_user dependency and permission check
) -> AuditLogListResponse:
    """
    List audit logs with filtering and pagination.
    Requires admin or audit viewer permissions.
    """
    logs, total = await crud.list_audit_logs(
        db=db,
        event_type=event_type,
        action=action,
        actor_id=actor_id,
        target_id=target_id,
        target_type=target_type,
        organization_id=organization_id,
        workspace_id=workspace_id,
        severity=severity,
        status=status,
        ip_address=ip_address,
        start_date=start_date,
        end_date=end_date,
        search=search,
        limit=limit,
        offset=offset,
    )

    return AuditLogListResponse(
        logs=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency and permission check
) -> AuditLog:
    """
    Get a specific audit log entry.
    Requires admin or audit viewer permissions.
    """
    log_entry = await crud.get_audit_log_by_id(db, log_id)
    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log {log_id} not found",
        )
    return log_entry


@router.get("/actor/{actor_id}", response_model=list[AuditLogResponse])
async def get_audit_logs_by_actor_route(
    actor_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(100, le=1000),
    # TODO: Add current_user dependency and permission check
) -> list[AuditLog]:
    """
    Get audit logs for a specific actor.
    Requires admin permissions.
    """
    return await crud.get_audit_logs_by_actor(db, actor_id, limit=limit)


@router.get("/target/{target_id}", response_model=list[AuditLogResponse])
async def get_audit_logs_by_target_route(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    target_type: str | None = None,
    limit: int = Query(100, le=1000),
    # TODO: Add current_user dependency and permission check
) -> list[AuditLog]:
    """
    Get audit logs for a specific target resource.
    Requires admin permissions.
    """
    return await crud.get_audit_logs_by_target(db, target_id, target_type=target_type, limit=limit)


@router.get("/security/events", response_model=SecurityEventsSummary)
async def get_security_events_route(
    db: Annotated[AsyncSession, Depends(get_session)],
    hours: int = Query(24, ge=1, le=168),
    # TODO: Add current_user dependency and permission check
) -> SecurityEventsSummary:
    """
    Get security-relevant events (failures, high severity, etc.).
    Requires admin or security permissions.
    """
    events = await crud.get_security_events(db, hours=hours)

    critical_count = sum(1 for e in events if e.severity == "critical")
    error_count = sum(1 for e in events if e.severity == "error")
    warning_count = sum(1 for e in events if e.severity == "warning")
    failed_auth_count = sum(1 for e in events if e.event_type == "auth" and e.status == "failure")

    return SecurityEventsSummary(
        total_events=len(events),
        critical_count=critical_count,
        error_count=error_count,
        warning_count=warning_count,
        failed_auth_count=failed_auth_count,
        events=[AuditLogResponse.model_validate(e) for e in events],
    )


@router.get("/security/failed-auth")
async def get_failed_auth_attempts_route(
    db: Annotated[AsyncSession, Depends(get_session)],
    hours: int = Query(24, ge=1, le=168),
    min_attempts: int = Query(3, ge=1),
    # TODO: Add current_user dependency and permission check
) -> dict:
    """
    Get failed authentication attempts grouped by IP.
    Useful for security monitoring and threat detection.
    Requires security permissions.
    """
    failed_by_ip = await crud.get_failed_authentication_attempts(
        db, hours=hours, min_attempts=min_attempts
    )

    # Convert to serializable format
    result = {}
    for ip, attempts in failed_by_ip.items():
        result[ip] = {
            "count": len(attempts),
            "first_attempt": attempts[-1].timestamp.isoformat(),
            "last_attempt": attempts[0].timestamp.isoformat(),
            "attempts": [AuditLogResponse.model_validate(a) for a in attempts[:10]],  # Limit to 10
        }

    return result


@router.post("/export")
async def export_audit_logs_route(
    request: ExportAuditLogsRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> Response:
    """
    Export audit logs in specified format.
    Creates an export record for compliance tracking.
    Requires admin permissions.
    """
    # TODO: Get current user ID
    exported_by = "system"

    # Fetch logs based on date range and filters
    logs, total = await crud.list_audit_logs(
        db=db,
        start_date=request.start_date,
        end_date=request.end_date,
        limit=10000,  # Max export size
    )

    # Create export record
    export_record = await crud.create_audit_export(
        db=db,
        export_type=request.export_type,
        format=request.format,
        start_date=request.start_date,
        end_date=request.end_date,
        exported_by=exported_by,
        filters=request.filters,
        record_count=len(logs),
        reason=request.reason,
    )

    # Generate export file
    if request.format == "csv":
        # CSV export
        output = io.StringIO()
        if logs:
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "id",
                    "timestamp",
                    "event_type",
                    "action",
                    "actor_email",
                    "target_type",
                    "target_name",
                    "status",
                    "severity",
                    "ip_address",
                ],
            )
            writer.writeheader()
            for log in logs:
                writer.writerow(
                    {
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat(),
                        "event_type": log.event_type,
                        "action": log.action,
                        "actor_email": log.actor_email or "",
                        "target_type": log.target_type or "",
                        "target_name": log.target_name or "",
                        "status": log.status,
                        "severity": log.severity,
                        "ip_address": log.ip_address or "",
                    }
                )

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="audit_logs_{export_record.id}.csv"'},
        )
    else:
        # JSON export (default)
        export_data = {
            "export_id": export_record.id,
            "export_type": request.export_type,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "record_count": len(logs),
            "logs": [AuditLogResponse.model_validate(log).model_dump() for log in logs],
        }

        return Response(
            content=json.dumps(export_data, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="audit_logs_{export_record.id}.json"'},
        )


@router.get("/exports/history", response_model=list[AuditLogExportResponse])
async def list_audit_exports_route(
    db: Annotated[AsyncSession, Depends(get_session)],
    exported_by: str | None = None,
    export_type: str | None = None,
    limit: int = Query(50, le=200),
    # TODO: Add current_user dependency and permission check
) -> list[AuditLogExport]:
    """
    List audit log export history.
    Requires admin permissions.
    """
    return await crud.list_audit_exports(
        db=db, exported_by=exported_by, export_type=export_type, limit=limit
    )


@router.post("/cleanup")
async def cleanup_old_audit_logs_route(
    db: Annotated[AsyncSession, Depends(get_session)],
    retention_days: int = Query(90, ge=30, le=365),
    # TODO: Add current_user dependency and permission check
) -> dict:
    """
    Clean up old audit logs based on retention policy.
    Should be run by a scheduled job.
    Requires admin permissions.
    """
    deleted_count = await crud.cleanup_old_audit_logs(db, default_retention_days=retention_days)

    return {
        "deleted_count": deleted_count,
        "message": f"Deleted {deleted_count} audit log(s) older than {retention_days} days",
    }
