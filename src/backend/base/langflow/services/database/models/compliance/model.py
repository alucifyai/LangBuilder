"""
Compliance Report Models

Generate compliance reports for SOC2, GDPR, ISO 27001, and custom frameworks.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Column, DateTime, Field, JSON, SQLModel, Text


class ComplianceReport(SQLModel, table=True):
    """
    Compliance Report

    Generated compliance reports for auditing and certification.
    """

    __tablename__ = "compliance_report"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )

    # Report details
    name: str = Field(
        index=True,
        description="Report name",
    )
    report_type: str = Field(
        index=True,
        description="Type: soc2, gdpr, iso27001, hipaa, custom",
    )
    framework_version: str | None = Field(
        None,
        description="Framework version (e.g., SOC2 Type II)",
    )
    description: str | None = Field(
        None,
        sa_column=Column(Text),
        description="Report description",
    )

    # Time period
    period_start: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Report period start",
    )
    period_end: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Report period end",
    )

    # Report status
    status: str = Field(
        default="generating",
        index=True,
        description="Status: generating, completed, failed",
    )
    completion_percentage: int = Field(
        default=0,
        description="Generation progress (0-100)",
    )

    # Report data
    summary: dict | None = Field(
        None,
        sa_column=Column(JSON),
        description="Executive summary with key metrics",
    )
    findings: list[dict] | None = Field(
        None,
        sa_column=Column(JSON),
        description="Compliance findings and violations",
    )
    recommendations: list[dict] | None = Field(
        None,
        sa_column=Column(JSON),
        description="Recommended actions",
    )
    controls: list[dict] | None = Field(
        None,
        sa_column=Column(JSON),
        description="Control effectiveness assessment",
    )
    metrics: dict | None = Field(
        None,
        sa_column=Column(JSON),
        description="Quantitative metrics and KPIs",
    )

    # File outputs
    pdf_path: str | None = Field(
        None,
        description="Path to generated PDF report",
    )
    csv_path: str | None = Field(
        None,
        description="Path to generated CSV data",
    )
    json_path: str | None = Field(
        None,
        description="Path to generated JSON data",
    )
    file_hash: str | None = Field(
        None,
        description="SHA-256 hash of report files",
    )

    # Metadata
    generated_by: str = Field(
        index=True,
        description="User who generated the report",
    )
    organization_id: str | None = Field(
        None,
        index=True,
        description="Organization scope",
    )
    attestation_required: bool = Field(
        default=False,
        description="Whether attestation is required",
    )
    attested_by: str | None = Field(
        None,
        description="User who attested to the report",
    )
    attested_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True)),
        description="When report was attested",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
        index=True,
    )
    completed_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True)),
        description="When generation completed",
    )


class ComplianceControl(SQLModel, table=True):
    """
    Compliance Control

    Individual security control for compliance frameworks.
    """

    __tablename__ = "compliance_control"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )

    # Control details
    control_id: str = Field(
        unique=True,
        index=True,
        description="Control identifier (e.g., CC6.1 for SOC2)",
    )
    framework: str = Field(
        index=True,
        description="Framework: soc2, gdpr, iso27001, etc.",
    )
    category: str = Field(
        description="Control category",
    )
    name: str = Field(
        description="Control name",
    )
    description: str = Field(
        sa_column=Column(Text),
        description="Control description",
    )
    requirements: list[str] = Field(
        default=[],
        sa_column=Column(JSON),
        description="Specific requirements",
    )

    # Implementation
    implementation_status: str = Field(
        default="not_implemented",
        index=True,
        description="Status: not_implemented, in_progress, implemented, validated",
    )
    implementation_notes: str | None = Field(
        None,
        sa_column=Column(Text),
        description="Implementation details",
    )
    responsible_party: str | None = Field(
        None,
        description="Team/person responsible",
    )

    # Evidence
    evidence_required: bool = Field(
        default=True,
        description="Whether evidence is required",
    )
    evidence_items: list[str] | None = Field(
        None,
        sa_column=Column(JSON),
        description="Evidence artifact references",
    )

    # Testing
    last_tested_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True)),
        description="When control was last tested",
    )
    test_frequency_days: int | None = Field(
        None,
        description="Required testing frequency in days",
    )
    test_results: dict | None = Field(
        None,
        sa_column=Column(JSON),
        description="Latest test results",
    )

    # Metadata
    is_active: bool = Field(
        default=True,
        index=True,
        description="Whether control is active",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
