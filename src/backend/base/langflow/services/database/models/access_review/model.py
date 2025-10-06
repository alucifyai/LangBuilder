"""
Access Review Models

Periodic access certification and review for compliance.
Supports SOC2, ISO 27001, and other compliance frameworks.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Column, DateTime, Field, JSON, SQLModel, Text


class AccessReviewCampaign(SQLModel, table=True):
    """
    Access Review Campaign

    A periodic review of user access rights for compliance certification.
    Reviewers must certify or revoke access for users in their scope.
    """

    __tablename__ = "access_review_campaign"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )

    # Campaign details
    name: str = Field(
        index=True,
        description="Campaign name (e.g., 'Q1 2025 Access Review')",
    )
    description: str | None = Field(
        None,
        sa_column=Column(Text),
        description="Campaign description and instructions",
    )
    campaign_type: str = Field(
        default="periodic",
        description="Type: periodic, event-driven, investigation",
    )

    # Scope
    scope_type: str = Field(
        description="Scope: organization, workspace, role, user",
    )
    scope_id: str | None = Field(
        None,
        description="ID of scoped resource (if applicable)",
    )
    include_filters: dict | None = Field(
        None,
        sa_column=Column(JSON),
        description="Filters for including grants (e.g., role_ids, permission_scopes)",
    )
    exclude_filters: dict | None = Field(
        None,
        sa_column=Column(JSON),
        description="Filters for excluding grants",
    )

    # Schedule
    start_date: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="When review campaign starts",
    )
    due_date: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="When reviews must be completed",
    )
    is_recurring: bool = Field(
        default=False,
        description="Whether this is a recurring review",
    )
    recurrence_interval_days: int | None = Field(
        None,
        description="Recurrence interval in days (if recurring)",
    )

    # Status
    status: str = Field(
        default="draft",
        index=True,
        description="Status: draft, active, completed, cancelled",
    )
    total_items: int = Field(
        default=0,
        description="Total access items to review",
    )
    reviewed_items: int = Field(
        default=0,
        description="Number of items reviewed",
    )
    approved_items: int = Field(
        default=0,
        description="Number of items approved",
    )
    revoked_items: int = Field(
        default=0,
        description="Number of items revoked",
    )

    # Ownership
    created_by: str = Field(
        index=True,
        description="User who created the campaign",
    )
    reviewers: list[str] = Field(
        default=[],
        sa_column=Column(JSON),
        description="List of reviewer user IDs",
    )

    # Metadata
    compliance_framework: str | None = Field(
        None,
        description="Compliance framework (SOC2, ISO27001, etc.)",
    )
    auto_revoke_on_no_response: bool = Field(
        default=False,
        description="Auto-revoke access if not reviewed by due date",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    completed_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True)),
        description="When campaign was completed",
    )


class AccessReviewItem(SQLModel, table=True):
    """
    Access Review Item

    Individual access grant requiring review within a campaign.
    """

    __tablename__ = "access_review_item"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )

    # Campaign reference
    campaign_id: str = Field(
        foreign_key="access_review_campaign.id",
        index=True,
        description="Parent review campaign",
    )

    # Access being reviewed
    grant_id: str = Field(
        foreign_key="grant.id",
        index=True,
        description="Grant being reviewed",
    )
    principal_id: str = Field(
        index=True,
        description="User/service account with access",
    )
    principal_email: str | None = Field(
        None,
        description="Principal email for display",
    )
    role_id: str = Field(
        description="Role being reviewed",
    )
    role_name: str | None = Field(
        None,
        description="Role name for display",
    )
    resource_type: str | None = Field(
        None,
        description="Resource type (workspace, project, etc.)",
    )
    resource_id: str | None = Field(
        None,
        description="Resource ID",
    )

    # Review details
    status: str = Field(
        default="pending",
        index=True,
        description="Status: pending, approved, revoked, escalated",
    )
    reviewer_id: str | None = Field(
        None,
        index=True,
        description="Assigned reviewer",
    )
    reviewed_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True)),
        description="When review was completed",
    )
    decision: str | None = Field(
        None,
        description="Decision: approve, revoke, modify",
    )
    justification: str | None = Field(
        None,
        sa_column=Column(Text),
        description="Reviewer's justification for decision",
    )

    # Context for review
    last_used_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True)),
        description="When access was last used",
    )
    usage_count: int = Field(
        default=0,
        description="Number of times access was used",
    )
    anomaly_score: float | None = Field(
        None,
        description="Anomaly detection score (0-1, higher = more suspicious)",
    )
    anomaly_reasons: list[str] | None = Field(
        None,
        sa_column=Column(JSON),
        description="Reasons for anomaly flag",
    )
    risk_level: str = Field(
        default="low",
        description="Risk level: low, medium, high, critical",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class AccessAnomaly(SQLModel, table=True):
    """
    Access Anomaly Detection

    Automatically detected unusual access patterns for investigation.
    """

    __tablename__ = "access_anomaly"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )

    # Anomaly classification
    anomaly_type: str = Field(
        index=True,
        description="Type: unused_access, privilege_escalation, unusual_pattern, dormant_user",
    )
    severity: str = Field(
        default="medium",
        index=True,
        description="Severity: low, medium, high, critical",
    )
    confidence: float = Field(
        description="Confidence score (0-1)",
    )

    # Subject
    principal_id: str = Field(
        index=True,
        description="User/service account with anomaly",
    )
    principal_email: str | None = Field(
        None,
        description="Principal email",
    )
    grant_id: str | None = Field(
        None,
        index=True,
        description="Specific grant with anomaly (if applicable)",
    )

    # Details
    title: str = Field(
        description="Short description of anomaly",
    )
    description: str = Field(
        sa_column=Column(Text),
        description="Detailed explanation",
    )
    evidence: dict | None = Field(
        None,
        sa_column=Column(JSON),
        description="Supporting evidence (usage stats, patterns, etc.)",
    )
    recommendations: list[str] | None = Field(
        None,
        sa_column=Column(JSON),
        description="Recommended actions",
    )

    # Status
    status: str = Field(
        default="open",
        index=True,
        description="Status: open, investigating, resolved, false_positive",
    )
    assigned_to: str | None = Field(
        None,
        index=True,
        description="Security analyst assigned",
    )
    resolved_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True)),
        description="When anomaly was resolved",
    )
    resolution_notes: str | None = Field(
        None,
        sa_column=Column(Text),
        description="Resolution details",
    )

    # Timestamps
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
