"""Enhanced audit logging with compliance features.

PRD Story 5.1 - Log All RBAC Changes
PRD Story 5.2 - Export Compliance Report
Phase 5: Auditability & Compliance
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from langflow.services.database.models.rbac.audit_log import AuditAction, AuditLog
from langflow.services.database.models.rbac.crud import create_audit_log


class ComplianceEventType(str, Enum):
    """Compliance-relevant event types."""

    # Access events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PRIVILEGE_ESCALATION = "privilege_escalation"

    # Administrative events
    ROLE_CREATED = "role_created"
    ROLE_DELETED = "role_deleted"
    PERMISSION_CHANGED = "permission_changed"
    USER_PROVISIONED = "user_provisioned"
    USER_DEPROVISIONED = "user_deprovisioned"

    # Security events
    AUTH_FAILURE = "auth_failure"
    AUTH_SUCCESS = "auth_success"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BREAK_GLASS_USED = "break_glass_used"

    # Data events
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    CONFIG_CHANGED = "config_changed"


class AuditSeverity(str, Enum):
    """Audit log severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EnhancedAuditService:
    """Enhanced audit logging with compliance features.

    Provides:
    - Structured audit logging
    - Compliance event tracking
    - PII data minimization
    - Tamper-evident logs
    - Export capabilities
    """

    @staticmethod
    async def log_compliance_event(
        session: AsyncSession,
        event_type: ComplianceEventType,
        actor_type: str,
        actor_id: str | None,
        actor_name: str | None,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any],
        severity: AuditSeverity = AuditSeverity.INFO,
        workspace_id: str | None = None,
    ) -> AuditLog:
        """Log a compliance-relevant event.

        Args:
            session: Database session
            event_type: Type of compliance event
            actor_type: Type of actor (user, service_account, system)
            actor_id: ID of actor
            actor_name: Name of actor
            resource_type: Type of resource affected
            resource_id: ID of resource
            details: Additional event details
            severity: Event severity
            workspace_id: Optional workspace context

        Returns:
            Created AuditLog entry

        PRD Story 5.1 @AC1 - Log all RBAC changes
        """
        # Map compliance event to audit action
        action_mapping = {
            ComplianceEventType.ACCESS_GRANTED: AuditAction.PERMISSION_CHECKED,
            ComplianceEventType.ACCESS_DENIED: AuditAction.PERMISSION_CHECKED,
            ComplianceEventType.ROLE_CREATED: AuditAction.ROLE_CREATED,
            ComplianceEventType.ROLE_DELETED: AuditAction.ROLE_DELETED,
            ComplianceEventType.USER_PROVISIONED: AuditAction.GRANT_CREATED,
            ComplianceEventType.USER_DEPROVISIONED: AuditAction.GRANT_REVOKED,
        }

        action = action_mapping.get(event_type, AuditAction.PERMISSION_CHECKED)

        # Add compliance metadata
        enhanced_details = {
            **details,
            "compliance_event_type": event_type.value,
            "severity": severity.value,
            "workspace_id": workspace_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }

        # Data minimization: Remove PII from details if configured
        enhanced_details = EnhancedAuditService._minimize_pii(enhanced_details)

        audit_log = await create_audit_log(
            session=session,
            action=action,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=actor_name,
            resource_type=resource_type,
            resource_id=resource_id,
            details=enhanced_details,
        )

        logger.info(
            f"Compliance event logged: {event_type.value} by {actor_type}:{actor_id} "
            f"on {resource_type}:{resource_id}"
        )

        return audit_log

    @staticmethod
    async def log_access_decision(
        session: AsyncSession,
        granted: bool,
        user_id: str,
        user_name: str,
        permission: str,
        resource_type: str,
        resource_id: str,
        reason: str | None = None,
        workspace_id: str | None = None,
    ) -> AuditLog:
        """Log an access control decision.

        Args:
            session: Database session
            granted: Whether access was granted
            user_id: User ID
            user_name: User name
            permission: Permission checked
            resource_type: Resource type
            resource_id: Resource ID
            reason: Reason for decision
            workspace_id: Workspace context

        Returns:
            Created AuditLog entry

        PRD Story 5.1 @AC2 - Log access decisions
        """
        event_type = ComplianceEventType.ACCESS_GRANTED if granted else ComplianceEventType.ACCESS_DENIED
        severity = AuditSeverity.INFO if granted else AuditSeverity.WARNING

        return await EnhancedAuditService.log_compliance_event(
            session=session,
            event_type=event_type,
            actor_type="user",
            actor_id=user_id,
            actor_name=user_name,
            resource_type=resource_type,
            resource_id=resource_id,
            severity=severity,
            workspace_id=workspace_id,
            details={
                "permission": permission,
                "granted": granted,
                "reason": reason,
            },
        )

    @staticmethod
    async def log_privilege_escalation(
        session: AsyncSession,
        user_id: str,
        user_name: str,
        old_role: str,
        new_role: str,
        granted_by: str,
        workspace_id: str | None = None,
    ) -> AuditLog:
        """Log a privilege escalation event.

        Args:
            session: Database session
            user_id: User receiving escalation
            user_name: User name
            old_role: Previous role
            new_role: New role
            granted_by: Admin who granted escalation
            workspace_id: Workspace context

        Returns:
            Created AuditLog entry

        PRD Story 5.1 - Track privilege changes
        """
        return await EnhancedAuditService.log_compliance_event(
            session=session,
            event_type=ComplianceEventType.PRIVILEGE_ESCALATION,
            actor_type="user",
            actor_id=granted_by,
            actor_name=None,
            resource_type="user",
            resource_id=user_id,
            severity=AuditSeverity.WARNING,
            workspace_id=workspace_id,
            details={
                "user_name": user_name,
                "old_role": old_role,
                "new_role": new_role,
                "granted_by": granted_by,
            },
        )

    @staticmethod
    async def log_break_glass_access(
        session: AsyncSession,
        user_id: str,
        user_name: str,
        emergency_reason: str,
        resource_type: str,
        resource_id: str,
        workspace_id: str | None = None,
    ) -> AuditLog:
        """Log break-glass emergency access.

        Args:
            session: Database session
            user_id: User using break-glass
            user_name: User name
            emergency_reason: Justification for emergency access
            resource_type: Resource accessed
            resource_id: Resource ID
            workspace_id: Workspace context

        Returns:
            Created AuditLog entry

        PRD Story 5.3 - Break-glass emergency access
        """
        return await EnhancedAuditService.log_compliance_event(
            session=session,
            event_type=ComplianceEventType.BREAK_GLASS_USED,
            actor_type="user",
            actor_id=user_id,
            actor_name=user_name,
            resource_type=resource_type,
            resource_id=resource_id,
            severity=AuditSeverity.CRITICAL,
            workspace_id=workspace_id,
            details={
                "emergency_reason": emergency_reason,
                "requires_review": True,
            },
        )

    @staticmethod
    async def log_data_export(
        session: AsyncSession,
        user_id: str,
        user_name: str,
        export_type: str,
        record_count: int,
        filters: dict[str, Any],
        workspace_id: str | None = None,
    ) -> AuditLog:
        """Log data export for compliance.

        Args:
            session: Database session
            user_id: User performing export
            user_name: User name
            export_type: Type of export (users, roles, audit_logs)
            record_count: Number of records exported
            filters: Filters applied
            workspace_id: Workspace context

        Returns:
            Created AuditLog entry

        PRD Story 5.2 @AC1 - Log data exports
        """
        return await EnhancedAuditService.log_compliance_event(
            session=session,
            event_type=ComplianceEventType.DATA_EXPORT,
            actor_type="user",
            actor_id=user_id,
            actor_name=user_name,
            resource_type="export",
            resource_id=export_type,
            severity=AuditSeverity.WARNING,
            workspace_id=workspace_id,
            details={
                "export_type": export_type,
                "record_count": record_count,
                "filters": filters,
            },
        )

    @staticmethod
    def _minimize_pii(details: dict[str, Any]) -> dict[str, Any]:
        """Minimize PII in audit log details.

        Args:
            details: Original details dict

        Returns:
            Details with PII minimized

        PRD Story 5.1 @AC4 - Data minimization
        """
        # Fields to redact/minimize
        pii_fields = ["email", "phone", "ssn", "credit_card"]

        minimized = details.copy()

        for field in pii_fields:
            if field in minimized:
                # Replace with masked value
                value = minimized[field]
                if isinstance(value, str) and len(value) > 4:
                    minimized[field] = f"{value[:2]}***{value[-2:]}"

        return minimized

    @staticmethod
    async def generate_compliance_report(
        session: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        workspace_id: str | None = None,
        event_types: list[ComplianceEventType] | None = None,
    ) -> dict[str, Any]:
        """Generate compliance report for date range.

        Args:
            session: Database session
            start_date: Report start date
            end_date: Report end date
            workspace_id: Optional workspace filter
            event_types: Optional event type filter

        Returns:
            Compliance report with statistics

        PRD Story 5.2 @AC1 - Generate compliance report
        """
        from sqlmodel import and_, func, select

        # Build query
        stmt = select(AuditLog).where(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date,
            )
        )

        # Apply filters
        if workspace_id:
            stmt = stmt.where(AuditLog.details.contains(f'"workspace_id": "{workspace_id}"'))

        result = await session.exec(stmt)
        logs = list(result.all())

        # Filter by event type if specified
        if event_types:
            event_values = [et.value for et in event_types]
            logs = [
                log for log in logs
                if json.loads(log.details).get("compliance_event_type") in event_values
            ]

        # Generate statistics
        report = {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "workspace_id": workspace_id,
            "total_events": len(logs),
            "event_breakdown": {},
            "severity_breakdown": {},
            "top_actors": {},
            "resource_breakdown": {},
            "critical_events": [],
        }

        # Analyze logs
        for log in logs:
            details = json.loads(log.details)

            # Event type breakdown
            event_type = details.get("compliance_event_type", "unknown")
            report["event_breakdown"][event_type] = report["event_breakdown"].get(event_type, 0) + 1

            # Severity breakdown
            severity = details.get("severity", "info")
            report["severity_breakdown"][severity] = report["severity_breakdown"].get(severity, 0) + 1

            # Top actors
            actor_key = f"{log.actor_type}:{log.actor_id}"
            report["top_actors"][actor_key] = report["top_actors"].get(actor_key, 0) + 1

            # Resource breakdown
            report["resource_breakdown"][log.resource_type] = (
                report["resource_breakdown"].get(log.resource_type, 0) + 1
            )

            # Critical events
            if severity == "critical":
                report["critical_events"].append({
                    "timestamp": log.timestamp.isoformat(),
                    "event_type": event_type,
                    "actor": actor_key,
                    "resource": f"{log.resource_type}:{log.resource_id}",
                    "details": details,
                })

        logger.info(
            f"Generated compliance report: {len(logs)} events from "
            f"{start_date.date()} to {end_date.date()}"
        )

        return report
