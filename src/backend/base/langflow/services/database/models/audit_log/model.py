"""
Enhanced Audit Log Model

Comprehensive audit logging for compliance and security monitoring.
Tracks all administrative actions, access events, and security-relevant changes.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Column, DateTime, Field, JSON, SQLModel, Text


class AuditLog(SQLModel, table=True):
    """
    Enhanced Audit Log Model

    Records all security-relevant events including:
    - Authentication events (login, logout, failed attempts)
    - Authorization changes (role/permission grants/revokes)
    - Resource access (read, write, delete operations)
    - Configuration changes (SSO, settings modifications)
    - Administrative actions (user management, etc.)
    """

    __tablename__ = "audit_log"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )

    # Event classification
    event_type: str = Field(
        index=True,
        description="Type of event (auth, access, admin, config, security)",
    )
    action: str = Field(
        index=True,
        description="Specific action taken (login, grant_role, delete_user, etc.)",
    )
    severity: str = Field(
        default="info",
        index=True,
        description="Event severity (info, warning, error, critical)",
    )
    status: str = Field(
        default="success",
        index=True,
        description="Action status (success, failure, partial)",
    )

    # Actor information
    actor_id: str | None = Field(
        None,
        index=True,
        description="User/service account who performed the action",
    )
    actor_type: str | None = Field(
        None,
        description="Type of actor (user, service_account, system)",
    )
    actor_email: str | None = Field(
        None,
        index=True,
        description="Email of the actor (for correlation)",
    )

    # Target information
    target_id: str | None = Field(
        None,
        index=True,
        description="ID of the resource being acted upon",
    )
    target_type: str | None = Field(
        None,
        index=True,
        description="Type of target (user, role, grant, flow, etc.)",
    )
    target_name: str | None = Field(
        None,
        description="Human-readable name of target",
    )

    # Context
    organization_id: str | None = Field(
        None,
        index=True,
        description="Organization context",
    )
    workspace_id: str | None = Field(
        None,
        index=True,
        description="Workspace context",
    )

    # Request details
    ip_address: str | None = Field(
        None,
        index=True,
        description="IP address of request origin",
    )
    user_agent: str | None = Field(
        None,
        description="User agent string",
    )
    session_id: str | None = Field(
        None,
        index=True,
        description="Session identifier",
    )
    request_id: str | None = Field(
        None,
        index=True,
        description="Request correlation ID",
    )

    # Change tracking
    changes: dict | None = Field(
        None,
        sa_column=Column(JSON),
        description="Before/after values for modifications",
    )
    metadata: dict | None = Field(
        None,
        sa_column=Column(JSON),
        description="Additional context data",
    )

    # Error information (for failed events)
    error_code: str | None = Field(
        None,
        description="Error code if action failed",
    )
    error_message: str | None = Field(
        None,
        sa_column=Column(Text),
        description="Error details if action failed",
    )

    # Compliance fields
    compliance_tags: list[str] | None = Field(
        None,
        sa_column=Column(JSON),
        description="Compliance categories (GDPR, SOC2, HIPAA, etc.)",
    )
    retention_days: int | None = Field(
        None,
        description="Required retention period in days",
    )

    # Timestamp
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
        index=True,
    )

    # Search optimization
    search_text: str | None = Field(
        None,
        sa_column=Column(Text),
        description="Concatenated searchable text for full-text search",
    )


class AuditLogExport(SQLModel, table=True):
    """
    Audit Log Export Tracking

    Tracks when audit logs are exported for compliance purposes.
    """

    __tablename__ = "audit_log_export"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )

    # Export details
    export_type: str = Field(
        description="Type of export (compliance, security, investigation)",
    )
    format: str = Field(
        description="Export format (json, csv, pdf)",
    )
    file_path: str | None = Field(
        None,
        description="Path to exported file",
    )
    file_hash: str | None = Field(
        None,
        description="SHA-256 hash of exported file for integrity",
    )

    # Query parameters
    start_date: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Start of export time range",
    )
    end_date: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="End of export time range",
    )
    filters: dict | None = Field(
        None,
        sa_column=Column(JSON),
        description="Filters applied to export",
    )
    record_count: int = Field(
        default=0,
        description="Number of records exported",
    )

    # Export metadata
    exported_by: str = Field(
        index=True,
        description="User who performed export",
    )
    reason: str | None = Field(
        None,
        sa_column=Column(Text),
        description="Reason for export (compliance audit, investigation, etc.)",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
