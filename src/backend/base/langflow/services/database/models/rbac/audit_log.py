from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, Index, Text
from sqlmodel import Field, Relationship, SQLModel

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.workspace import Workspace
    from langflow.services.database.models.user.model import User


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Authentication events
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"

    # Authorization events
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    ACCESS_DENIED = "access_denied"

    # Resource operations
    RESOURCE_CREATED = "resource_created"
    RESOURCE_READ = "resource_read"
    RESOURCE_UPDATED = "resource_updated"
    RESOURCE_DELETED = "resource_deleted"
    RESOURCE_EXPORTED = "resource_exported"
    RESOURCE_IMPORTED = "resource_imported"
    RESOURCE_SHARED = "resource_shared"
    RESOURCE_PUBLISHED = "resource_published"

    # Workspace operations
    WORKSPACE_CREATED = "workspace_created"
    WORKSPACE_UPDATED = "workspace_updated"
    WORKSPACE_DELETED = "workspace_deleted"
    WORKSPACE_USER_ADDED = "workspace_user_added"
    WORKSPACE_USER_REMOVED = "workspace_user_removed"

    # Security events
    SECURITY_ALERT = "security_alert"
    BREAK_GLASS_ACCESS = "break_glass_access"
    IMPERSONATION_START = "impersonation_start"
    IMPERSONATION_END = "impersonation_end"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # System events
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    BACKUP_CREATED = "backup_created"
    RESTORE_PERFORMED = "restore_performed"
    COMPLIANCE_EXPORT = "compliance_export"


class ActorType(str, Enum):
    """Types of actors performing actions."""

    USER = "user"
    SERVICE_ACCOUNT = "service_account"
    SYSTEM = "system"
    API_CLIENT = "api_client"
    SCHEDULER = "scheduler"
    ANONYMOUS = "anonymous"


class AuditOutcome(str, Enum):
    """Outcome of the audited action."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    DENIED = "denied"
    ERROR = "error"


class AuditLogBase(SQLModel):
    """Base model for audit logging."""

    # Event information
    event_type: AuditEventType = Field(index=True)
    action: str = Field(index=True)  # Specific action performed
    outcome: AuditOutcome = Field(index=True)

    # Actor information
    actor_type: ActorType = Field(index=True)
    actor_id: UUIDstr | None = Field(index=True, nullable=True)
    actor_name: str | None = Field(default=None)
    actor_email: str | None = Field(default=None)

    # Target resource
    resource_type: str | None = Field(default=None, index=True)
    resource_id: UUIDstr | None = Field(default=None, index=True)
    resource_name: str | None = Field(default=None)

    # Context
    workspace_id: UUIDstr | None = Field(default=None, index=True)
    project_id: UUIDstr | None = Field(default=None, index=True)
    environment_id: UUIDstr | None = Field(default=None)

    # Request information
    ip_address: str | None = Field(default=None, index=True)
    user_agent: str | None = Field(default=None)
    session_id: str | None = Field(default=None, index=True)
    request_id: str | None = Field(default=None, index=True)
    api_endpoint: str | None = Field(default=None)
    http_method: str | None = Field(default=None)

    # Additional data
    error_message: str | None = Field(default=None, sa_column=Column(Text))
    event_metadata: dict | None = Field(default={}, sa_column=Column(JSON))

    # Compliance fields
    retention_required: bool = Field(default=True)  # For compliance retention
    sensitive_data_accessed: bool = Field(default=False)
    compliance_tags: list[str] | None = Field(default=[], sa_column=Column(JSON))

    # Timestamp (immutable)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)


class AuditLog(AuditLogBase, table=True):  # type: ignore[call-arg]
    """Audit log table for compliance and security monitoring."""

    __tablename__ = "audit_log"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)

    # Relationships (nullable for system events)
    user: User | None = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[AuditLog.actor_id]",
            "primaryjoin": "and_(AuditLog.actor_id == User.id, AuditLog.actor_type == 'user')"
        }
    )

    workspace: Workspace | None = Relationship(
        back_populates="audit_logs",
        sa_relationship_kwargs={
            "foreign_keys": "[AuditLog.workspace_id]"
        }
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_actor", "actor_type", "actor_id"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_workspace", "workspace_id", "timestamp"),
        Index("idx_audit_event", "event_type", "outcome"),
        Index("idx_audit_compliance", "retention_required", "sensitive_data_accessed"),
    )


class AuditLogRead(AuditLogBase):
    """Schema for reading audit log data."""

    id: UUID


class AuditLogFilter(SQLModel):
    """Schema for filtering audit logs."""

    event_types: list[AuditEventType] | None = None
    actor_types: list[ActorType] | None = None
    actor_id: UUID | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None
    workspace_id: UUID | None = None
    project_id: UUID | None = None
    outcome: AuditOutcome | None = None
    ip_address: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    sensitive_data_only: bool = False
    compliance_tags: list[str] | None = None


class AuditLogExport(SQLModel):
    """Schema for audit log export requests."""

    filter: AuditLogFilter
    format: str = "json"  # json, csv, xlsx
    include_metadata: bool = True
    encryption_key: str | None = None  # For encrypted exports
    retention_days: int = 7  # How long to keep the export


class AuditLogSummary(SQLModel):
    """Schema for audit log summary/statistics."""

    period_start: datetime
    period_end: datetime
    total_events: int
    events_by_type: dict[str, int]
    events_by_outcome: dict[str, int]
    unique_actors: int
    unique_resources: int
    failed_attempts: int
    security_alerts: int
    compliance_events: int


class ComplianceReport(SQLModel):
    """Schema for compliance reporting."""

    report_type: str  # SOC2, ISO27001, GDPR, CCPA
    period_start: datetime
    period_end: datetime
    workspace_id: UUID | None = None

    # Report sections
    access_summary: dict | None = Field(default=None, sa_column=Column(JSON))
    permission_changes: list[dict] | None = Field(default=None, sa_column=Column(JSON))
    security_incidents: list[dict] | None = Field(default=None, sa_column=Column(JSON))
    data_access_logs: list[dict] | None = Field(default=None, sa_column=Column(JSON))
    user_activity: dict | None = Field(default=None, sa_column=Column(JSON))

    # Compliance metrics
    total_logins: int = 0
    failed_logins: int = 0
    permission_changes_count: int = 0
    data_exports: int = 0
    security_alerts: int = 0

    # Attestation
    generated_by: str | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by: str | None = None
    approval_date: datetime | None = None
