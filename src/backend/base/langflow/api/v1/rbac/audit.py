"""Audit log management API endpoints for RBAC system."""

from typing import TYPE_CHECKING
from langflow.schema.serialize import UUIDstr

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select, and_, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime, timedelta

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.api.v1.rbac.dependencies import (
    check_workspace_permission,
    get_permission_engine,
)
from langflow.services.rbac.permission_engine import PermissionEngine
from langflow.services.database.models.rbac.audit_log import (
    AuditLog,
    AuditLogRead,
    AuditLogFilter,
    AuditLogExport,
    AuditLogSummary,
    ComplianceReport,
    AuditEventType,
    ActorType,
    AuditOutcome,
)
from langflow.services.database.models.rbac.workspace import Workspace

if TYPE_CHECKING:
    from langflow.services.database.models.user.model import User

router = APIRouter(
    prefix="/audit",
    tags=["RBAC", "Audit"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource does not exist"},
        422: {"description": "Validation Error - Invalid request data"},
    },
)


@router.get("/logs", response_model=list[AuditLogRead])
async def list_audit_logs(
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace_id: UUIDstr,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    event_type: AuditEventType | None = None,
    actor_type: ActorType | None = None,
    outcome: AuditOutcome | None = None,
    actor_id: UUIDstr | None = None,
    resource_type: str | None = None,
    resource_id: UUIDstr | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    search: str | None = None,
) -> list[AuditLogRead]:
    """List audit logs for a workspace."""
    
    # Check workspace permission - only admins can view audit logs
    await check_workspace_permission(session, current_user, workspace_id, "audit:read")

    statement = select(AuditLog).where(AuditLog.workspace_id == workspace_id)

    # Apply filters
    if event_type:
        statement = statement.where(AuditLog.event_type == event_type)
    
    if actor_type:
        statement = statement.where(AuditLog.actor_type == actor_type)
    
    if outcome:
        statement = statement.where(AuditLog.outcome == outcome)
    
    if actor_id:
        statement = statement.where(AuditLog.actor_id == actor_id)
    
    if resource_type:
        statement = statement.where(AuditLog.resource_type == resource_type)
    
    if resource_id:
        statement = statement.where(AuditLog.resource_id == resource_id)
    
    if start_date:
        statement = statement.where(AuditLog.timestamp >= start_date)
    
    if end_date:
        statement = statement.where(AuditLog.timestamp <= end_date)
    
    if search:
        statement = statement.where(
            or_(
                AuditLog.event_description.ilike(f"%{search}%"),
                AuditLog.details.astext.ilike(f"%{search}%"),
                AuditLog.ip_address.ilike(f"%{search}%"),
                AuditLog.user_agent.ilike(f"%{search}%")
            )
        )

    # Order by timestamp descending (most recent first)
    statement = statement.order_by(AuditLog.timestamp.desc())
    
    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    
    result = await session.exec(statement)
    logs = result.all()

    return [AuditLogRead.model_validate(log) for log in logs]


@router.get("/logs/{log_id}", response_model=AuditLogRead)
async def get_audit_log(
    log_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> AuditLogRead:
    """Get audit log by ID."""
    
    log = await session.get(AuditLog, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )

    # Check workspace permission
    await check_workspace_permission(session, current_user, log.workspace_id, "audit:read")

    return AuditLogRead.model_validate(log)


@router.post("/logs/export", response_model=dict)
async def export_audit_logs(
    export_request: AuditLogExport,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> dict:
    """Export audit logs to various formats."""
    
    # Check workspace permission
    await check_workspace_permission(
        session, current_user, export_request.workspace_id, "audit:export"
    )

    # Build query based on filters
    statement = select(AuditLog).where(AuditLog.workspace_id == export_request.workspace_id)
    
    if export_request.start_date:
        statement = statement.where(AuditLog.timestamp >= export_request.start_date)
    
    if export_request.end_date:
        statement = statement.where(AuditLog.timestamp <= export_request.end_date)
    
    if export_request.event_types:
        statement = statement.where(AuditLog.event_type.in_(export_request.event_types))
    
    if export_request.resource_types:
        statement = statement.where(AuditLog.resource_type.in_(export_request.resource_types))

    # Order by timestamp
    statement = statement.order_by(AuditLog.timestamp.desc())
    
    result = await session.exec(statement)
    logs = result.all()

    # For now, return metadata about the export
    # In a real implementation, this would generate the actual file
    return {
        "export_id": "placeholder-export-id",
        "format": export_request.format,
        "total_records": len(logs),
        "status": "completed",
        "download_url": f"/api/v1/rbac/audit/exports/placeholder-export-id/download",
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
    }


@router.get("/summary", response_model=AuditLogSummary)
async def get_audit_summary(
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace_id: UUIDstr,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> AuditLogSummary:
    """Get audit log summary statistics."""
    
    # Check workspace permission
    await check_workspace_permission(session, current_user, workspace_id, "audit:read")

    # Default to last 30 days if no dates provided
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    # Base query
    base_statement = select(AuditLog).where(
        and_(
            AuditLog.workspace_id == workspace_id,
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        )
    )

    # Count total events
    result = await session.exec(base_statement)
    all_logs = result.all()
    total_events = len(all_logs)

    # Count by event type
    event_type_counts = {}
    for log in all_logs:
        event_type = log.event_type.value if hasattr(log.event_type, 'value') else str(log.event_type)
        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

    # Count by outcome
    successful_events = len([log for log in all_logs if log.outcome == AuditOutcome.SUCCESS])
    failed_events = len([log for log in all_logs if log.outcome == AuditOutcome.FAILURE])

    # Count unique actors
    unique_actors = len(set(log.actor_id for log in all_logs if log.actor_id))

    return AuditLogSummary(
        workspace_id=workspace_id,
        start_date=start_date,
        end_date=end_date,
        total_events=total_events,
        successful_events=successful_events,
        failed_events=failed_events,
        unique_actors=unique_actors,
        event_type_breakdown=event_type_counts,
        top_resources=[],  # Would be calculated from actual data
        risk_indicators=[],  # Would be calculated based on patterns
    )


@router.get("/compliance/report", response_model=ComplianceReport)
async def get_compliance_report(
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace_id: UUIDstr,
    report_type: str = Query("soc2", description="Type of compliance report"),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> ComplianceReport:
    """Generate compliance report."""
    
    # Check workspace permission - only admins can generate compliance reports
    await check_workspace_permission(session, current_user, workspace_id, "audit:compliance")

    # Default to last 90 days for compliance reports
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=90)
    if not end_date:
        end_date = datetime.utcnow()

    # Query audit logs for the period
    statement = select(AuditLog).where(
        and_(
            AuditLog.workspace_id == workspace_id,
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        )
    )
    
    result = await session.exec(statement)
    logs = result.all()

    # Generate compliance metrics based on report type
    compliance_metrics = {
        "total_access_events": len([log for log in logs if log.event_type in [AuditEventType.LOGIN, AuditEventType.LOGOUT]]),
        "failed_access_attempts": len([log for log in logs if log.event_type == AuditEventType.LOGIN and log.outcome == AuditOutcome.FAILURE]),
        "privilege_escalations": len([log for log in logs if log.event_type == AuditEventType.ROLE_ASSIGNED]),
        "data_access_events": len([log for log in logs if "data" in log.event_description.lower()]),
        "configuration_changes": len([log for log in logs if log.event_type in [AuditEventType.ROLE_CREATED, AuditEventType.PERMISSION_GRANTED]]),
    }

    # Generate findings based on patterns
    findings = []
    if compliance_metrics["failed_access_attempts"] > 100:
        findings.append({
            "severity": "medium",
            "category": "access_control",
            "description": f"High number of failed login attempts ({compliance_metrics['failed_access_attempts']}) detected",
            "recommendation": "Review access control policies and consider implementing account lockout"
        })

    return ComplianceReport(
        workspace_id=workspace_id,
        report_type=report_type,
        period_start=start_date,
        period_end=end_date,
        generated_at=datetime.utcnow(),
        generated_by=current_user.id,
        compliance_status="compliant",  # Would be calculated based on actual requirements
        metrics=compliance_metrics,
        findings=findings,
        recommendations=[
            "Regularly review audit logs for suspicious activity",
            "Implement automated alerting for critical events",
            "Conduct periodic access reviews",
        ]
    )


@router.get("/events/types", response_model=list[str])
async def list_event_types(
    session: DbSession,
    current_user: CurrentActiveUser,
) -> list[str]:
    """List all available audit event types."""
    
    # Return all audit event types
    return [event_type.value for event_type in AuditEventType]


@router.get("/actors/types", response_model=list[str])
async def list_actor_types(
    session: DbSession,
    current_user: CurrentActiveUser,
) -> list[str]:
    """List all available actor types."""
    
    # Return all actor types
    return [actor_type.value for actor_type in ActorType]


@router.post("/logs", response_model=AuditLogRead, status_code=status.HTTP_201_CREATED)
async def create_audit_log(
    log_data: dict,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> AuditLogRead:
    """Create a new audit log entry (for system use)."""
    
    # Only superusers or system services can create audit logs directly
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can create audit logs"
        )

    # Create audit log
    audit_log = AuditLog(
        workspace_id=log_data.get("workspace_id"),
        event_type=log_data.get("event_type"),
        event_description=log_data.get("event_description"),
        actor_type=log_data.get("actor_type"),
        actor_id=log_data.get("actor_id"),
        resource_type=log_data.get("resource_type"),
        resource_id=log_data.get("resource_id"),
        outcome=log_data.get("outcome", AuditOutcome.SUCCESS),
        details=log_data.get("details", {}),
        ip_address=log_data.get("ip_address"),
        user_agent=log_data.get("user_agent"),
        timestamp=datetime.utcnow(),
    )
    
    session.add(audit_log)
    await session.commit()
    await session.refresh(audit_log)

    return AuditLogRead.model_validate(audit_log)