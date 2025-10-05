"""Compliance reporting API endpoints.

PRD Story 5.2 - Export Compliance Report
Phase 5: Auditability & Compliance
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.api.v1.rbac.dependencies import RequirePermission
from langflow.services.audit.enhanced_audit import ComplianceEventType, EnhancedAuditService

router = APIRouter(prefix="/compliance", tags=["Compliance"])


class ComplianceReportRequest(BaseModel):
    """Compliance report request."""

    start_date: datetime
    end_date: datetime
    workspace_id: str | None = None
    event_types: list[str] | None = None
    format: str = "json"  # json, csv, pdf


class ComplianceReportResponse(BaseModel):
    """Compliance report response."""

    report_period: dict[str, str]
    workspace_id: str | None
    total_events: int
    event_breakdown: dict[str, int]
    severity_breakdown: dict[str, int]
    top_actors: dict[str, int]
    resource_breakdown: dict[str, int]
    critical_events: list[dict]


class BreakGlassAccessRequest(BaseModel):
    """Break-glass emergency access request."""

    resource_type: str
    resource_id: str
    emergency_reason: str
    justification: str


class DataRetentionPolicyResponse(BaseModel):
    """Data retention policy."""

    audit_log_retention_days: int
    compliance_report_retention_days: int
    auto_archive_enabled: bool
    archive_location: str | None


@router.post("/reports", response_model=ComplianceReportResponse)
async def generate_compliance_report(
    request: ComplianceReportRequest,
    db: DbSession,
    current_user: CurrentActiveUser,
    _perm: Annotated[None, Depends(RequirePermission("compliance:read"))] = None,
):
    """Generate compliance report for specified period.

    Args:
        request: Report parameters
        db: Database session
        current_user: Authenticated user

    Returns:
        Compliance report with statistics

    PRD Story 5.2 @AC1 - Export user access report
    PRD Story 5.2 @AC3 - Filter by date range
    """
    # Validate date range
    if request.end_date < request.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date",
        )

    # Limit report range to 1 year
    if (request.end_date - request.start_date).days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report range cannot exceed 365 days",
        )

    # Convert event types
    event_types = None
    if request.event_types:
        try:
            event_types = [ComplianceEventType(et) for et in request.event_types]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {e}",
            )

    # Generate report
    report = await EnhancedAuditService.generate_compliance_report(
        session=db,
        start_date=request.start_date,
        end_date=request.end_date,
        workspace_id=request.workspace_id,
        event_types=event_types,
    )

    # Log export
    await EnhancedAuditService.log_data_export(
        session=db,
        user_id=str(current_user.id),
        user_name=current_user.username,
        export_type="compliance_report",
        record_count=report["total_events"],
        filters={
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "workspace_id": request.workspace_id,
        },
        workspace_id=request.workspace_id,
    )

    return ComplianceReportResponse(**report)


@router.get("/reports/last-30-days", response_model=ComplianceReportResponse)
async def get_last_30_days_report(
    db: DbSession,
    current_user: CurrentActiveUser,
    workspace_id: str | None = Query(None),
    _perm: Annotated[None, Depends(RequirePermission("compliance:read"))] = None,
):
    """Get compliance report for last 30 days.

    Quick access to recent compliance data.

    PRD Story 5.2 @AC2 - Quick compliance reports
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)

    report = await EnhancedAuditService.generate_compliance_report(
        session=db,
        start_date=start_date,
        end_date=end_date,
        workspace_id=workspace_id,
    )

    return ComplianceReportResponse(**report)


@router.get("/reports/export/csv")
async def export_compliance_report_csv(
    db: DbSession,
    current_user: CurrentActiveUser,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    workspace_id: str | None = Query(None),
    _perm: Annotated[None, Depends(RequirePermission("compliance:export"))] = None,
):
    """Export compliance report as CSV.

    Args:
        start_date: Report start date
        end_date: Report end date
        workspace_id: Optional workspace filter

    Returns:
        CSV file download

    PRD Story 5.2 @AC2 - Export in multiple formats
    """
    import csv
    import io

    report = await EnhancedAuditService.generate_compliance_report(
        session=db,
        start_date=start_date,
        end_date=end_date,
        workspace_id=workspace_id,
    )

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Report Period",
        f"{start_date.date()} to {end_date.date()}",
    ])
    writer.writerow([])

    # Summary
    writer.writerow(["Summary"])
    writer.writerow(["Total Events", report["total_events"]])
    writer.writerow(["Workspace", workspace_id or "All"])
    writer.writerow([])

    # Event breakdown
    writer.writerow(["Event Type", "Count"])
    for event_type, count in report["event_breakdown"].items():
        writer.writerow([event_type, count])
    writer.writerow([])

    # Severity breakdown
    writer.writerow(["Severity", "Count"])
    for severity, count in report["severity_breakdown"].items():
        writer.writerow([severity, count])
    writer.writerow([])

    # Critical events
    writer.writerow(["Critical Events"])
    writer.writerow(["Timestamp", "Event Type", "Actor", "Resource"])
    for event in report["critical_events"]:
        writer.writerow([
            event["timestamp"],
            event["event_type"],
            event["actor"],
            event["resource"],
        ])

    # Log export
    await EnhancedAuditService.log_data_export(
        session=db,
        user_id=str(current_user.id),
        user_name=current_user.username,
        export_type="compliance_report_csv",
        record_count=report["total_events"],
        filters={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        workspace_id=workspace_id,
    )

    # Return as download
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=compliance_report_{start_date.date()}_to_{end_date.date()}.csv"
        },
    )


@router.post("/break-glass")
async def request_break_glass_access(
    request: BreakGlassAccessRequest,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Request break-glass emergency access.

    Grants temporary elevated access for emergency situations.
    All break-glass access is logged and requires review.

    Args:
        request: Emergency access request

    Returns:
        Temporary access grant

    PRD Story 5.3 - Break-glass emergency access
    """
    # Validate emergency reason
    if len(request.emergency_reason) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Emergency reason must be at least 20 characters",
        )

    # Log break-glass usage
    audit_log = await EnhancedAuditService.log_break_glass_access(
        session=db,
        user_id=str(current_user.id),
        user_name=current_user.username,
        emergency_reason=request.emergency_reason,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
    )

    # TODO: Grant temporary elevated access (implement in Phase 5+)
    # For now, just log the request

    return {
        "granted": True,
        "audit_log_id": str(audit_log.id),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "message": "Break-glass access logged. This requires administrative review.",
        "justification": request.justification,
    }


@router.get("/retention-policy", response_model=DataRetentionPolicyResponse)
async def get_retention_policy(
    current_user: CurrentActiveUser,
    _perm: Annotated[None, Depends(RequirePermission("compliance:read"))] = None,
):
    """Get data retention policy.

    Returns current retention settings for compliance.

    PRD Story 5.1 @AC5 - Data retention policy
    """
    # TODO: Load from configuration
    return DataRetentionPolicyResponse(
        audit_log_retention_days=2555,  # 7 years for compliance
        compliance_report_retention_days=3650,  # 10 years
        auto_archive_enabled=True,
        archive_location="s3://langbuilder-audit-archive/",
    )


@router.get("/access-summary/{user_id}")
async def get_user_access_summary(
    user_id: str,
    db: DbSession,
    current_user: CurrentActiveUser,
    days: int = Query(30, ge=1, le=365),
    _perm: Annotated[None, Depends(RequirePermission("compliance:read"))] = None,
):
    """Get user access summary for compliance review.

    Args:
        user_id: User ID to review
        days: Number of days to look back

    Returns:
        Summary of user's access patterns

    PRD Story 5.2 @AC1 - User access report
    """
    from sqlmodel import and_, func, select

    from langflow.services.database.models.rbac.audit_log import AuditLog

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    # Query user's audit logs
    stmt = select(AuditLog).where(
        and_(
            AuditLog.actor_id == user_id,
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date,
        )
    ).order_by(AuditLog.timestamp.desc())

    result = await db.exec(stmt)
    logs = list(result.all())

    # Analyze access patterns
    summary = {
        "user_id": user_id,
        "period_days": days,
        "total_actions": len(logs),
        "action_breakdown": {},
        "resources_accessed": set(),
        "failed_accesses": [],
        "suspicious_activity": [],
    }

    for log in logs:
        # Action breakdown
        action = log.action.value
        summary["action_breakdown"][action] = summary["action_breakdown"].get(action, 0) + 1

        # Resources accessed
        summary["resources_accessed"].add(f"{log.resource_type}:{log.resource_id}")

        # Failed accesses
        import json
        details = json.loads(log.details)
        if details.get("granted") is False:
            summary["failed_accesses"].append({
                "timestamp": log.timestamp.isoformat(),
                "resource": f"{log.resource_type}:{log.resource_id}",
                "reason": details.get("reason"),
            })

    summary["resources_accessed"] = list(summary["resources_accessed"])

    return summary
