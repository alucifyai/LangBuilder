"""add compliance tables

Revision ID: 008_add_compliance_tables
Revises: 007_add_scim_tables
Create Date: 2025-10-06 01:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008_add_compliance_tables"
down_revision: Union[str, None] = "007_add_scim_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create compliance_reports table
    op.create_table(
        "compliance_reports",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("report_type", sa.String(), nullable=False),
        sa.Column("framework_version", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("completion_percentage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("findings", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("controls", sa.JSON(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("generated_by", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.Column("attestation_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("attested_by", sa.String(), nullable=True),
        sa.Column("attested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_compliance_reports_report_type"), "compliance_reports", ["report_type"], unique=False)
    op.create_index(op.f("ix_compliance_reports_status"), "compliance_reports", ["status"], unique=False)
    op.create_index(op.f("ix_compliance_reports_organization_id"), "compliance_reports", ["organization_id"], unique=False)
    op.create_index(op.f("ix_compliance_reports_created_at"), "compliance_reports", ["created_at"], unique=False)

    # Create compliance_controls table
    op.create_table(
        "compliance_controls",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("control_id", sa.String(), nullable=False),
        sa.Column("framework", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("requirements", sa.JSON(), nullable=False),
        sa.Column("implementation_status", sa.String(), nullable=False, server_default="not_implemented"),
        sa.Column("implementation_notes", sa.String(), nullable=True),
        sa.Column("responsible_party", sa.String(), nullable=True),
        sa.Column("evidence_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("evidence_items", sa.JSON(), nullable=True),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("test_frequency_days", sa.Integer(), nullable=True),
        sa.Column("test_results", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("control_id", "framework", name="uq_control_framework"),
    )
    op.create_index(op.f("ix_compliance_controls_framework"), "compliance_controls", ["framework"], unique=False)
    op.create_index(op.f("ix_compliance_controls_category"), "compliance_controls", ["category"], unique=False)
    op.create_index(op.f("ix_compliance_controls_implementation_status"), "compliance_controls", ["implementation_status"], unique=False)
    op.create_index(op.f("ix_compliance_controls_is_active"), "compliance_controls", ["is_active"], unique=False)


def downgrade() -> None:
    # Drop compliance_controls
    op.drop_index(op.f("ix_compliance_controls_is_active"), table_name="compliance_controls")
    op.drop_index(op.f("ix_compliance_controls_implementation_status"), table_name="compliance_controls")
    op.drop_index(op.f("ix_compliance_controls_category"), table_name="compliance_controls")
    op.drop_index(op.f("ix_compliance_controls_framework"), table_name="compliance_controls")
    op.drop_table("compliance_controls")

    # Drop compliance_reports
    op.drop_index(op.f("ix_compliance_reports_created_at"), table_name="compliance_reports")
    op.drop_index(op.f("ix_compliance_reports_organization_id"), table_name="compliance_reports")
    op.drop_index(op.f("ix_compliance_reports_status"), table_name="compliance_reports")
    op.drop_index(op.f("ix_compliance_reports_report_type"), table_name="compliance_reports")
    op.drop_table("compliance_reports")
