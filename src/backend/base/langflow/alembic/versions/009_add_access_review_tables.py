"""add access review tables

Revision ID: 009_add_access_review_tables
Revises: 008_add_compliance_tables
Create Date: 2025-10-06 01:15:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009_add_access_review_tables"
down_revision: Union[str, None] = "008_add_compliance_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create access_review_campaigns table
    op.create_table(
        "access_review_campaigns",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("auto_revoke_on_no_response", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reviewed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revoked_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("compliance_framework", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_access_review_campaigns_status"), "access_review_campaigns", ["status"], unique=False)
    op.create_index(op.f("ix_access_review_campaigns_organization_id"), "access_review_campaigns", ["organization_id"], unique=False)
    op.create_index(op.f("ix_access_review_campaigns_created_at"), "access_review_campaigns", ["created_at"], unique=False)

    # Create access_review_items table
    op.create_table(
        "access_review_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("campaign_id", sa.String(), nullable=False),
        sa.Column("grant_id", sa.String(), nullable=False),
        sa.Column("principal_type", sa.String(), nullable=False),
        sa.Column("principal_id", sa.String(), nullable=False),
        sa.Column("principal_email", sa.String(), nullable=True),
        sa.Column("role_name", sa.String(), nullable=False),
        sa.Column("scope_type", sa.String(), nullable=False),
        sa.Column("scope_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("last_access_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewer_id", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_decision", sa.String(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["campaign_id"], ["access_review_campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["grant_id"], ["grant.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_access_review_items_campaign_id"), "access_review_items", ["campaign_id"], unique=False)
    op.create_index(op.f("ix_access_review_items_status"), "access_review_items", ["status"], unique=False)
    op.create_index(op.f("ix_access_review_items_principal_id"), "access_review_items", ["principal_id"], unique=False)

    # Create access_anomalies table
    op.create_table(
        "access_anomalies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("anomaly_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("principal_type", sa.String(), nullable=False),
        sa.Column("principal_id", sa.String(), nullable=False),
        sa.Column("principal_email", sa.String(), nullable=True),
        sa.Column("resource_type", sa.String(), nullable=True),
        sa.Column("resource_id", sa.String(), nullable=True),
        sa.Column("detection_details", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("resolved_by", sa.String(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.String(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_access_anomalies_anomaly_type"), "access_anomalies", ["anomaly_type"], unique=False)
    op.create_index(op.f("ix_access_anomalies_severity"), "access_anomalies", ["severity"], unique=False)
    op.create_index(op.f("ix_access_anomalies_status"), "access_anomalies", ["status"], unique=False)
    op.create_index(op.f("ix_access_anomalies_principal_id"), "access_anomalies", ["principal_id"], unique=False)
    op.create_index(op.f("ix_access_anomalies_detected_at"), "access_anomalies", ["detected_at"], unique=False)
    op.create_index(op.f("ix_access_anomalies_organization_id"), "access_anomalies", ["organization_id"], unique=False)


def downgrade() -> None:
    # Drop access_anomalies
    op.drop_index(op.f("ix_access_anomalies_organization_id"), table_name="access_anomalies")
    op.drop_index(op.f("ix_access_anomalies_detected_at"), table_name="access_anomalies")
    op.drop_index(op.f("ix_access_anomalies_principal_id"), table_name="access_anomalies")
    op.drop_index(op.f("ix_access_anomalies_status"), table_name="access_anomalies")
    op.drop_index(op.f("ix_access_anomalies_severity"), table_name="access_anomalies")
    op.drop_index(op.f("ix_access_anomalies_anomaly_type"), table_name="access_anomalies")
    op.drop_table("access_anomalies")

    # Drop access_review_items
    op.drop_index(op.f("ix_access_review_items_principal_id"), table_name="access_review_items")
    op.drop_index(op.f("ix_access_review_items_status"), table_name="access_review_items")
    op.drop_index(op.f("ix_access_review_items_campaign_id"), table_name="access_review_items")
    op.drop_table("access_review_items")

    # Drop access_review_campaigns
    op.drop_index(op.f("ix_access_review_campaigns_created_at"), table_name="access_review_campaigns")
    op.drop_index(op.f("ix_access_review_campaigns_organization_id"), table_name="access_review_campaigns")
    op.drop_index(op.f("ix_access_review_campaigns_status"), table_name="access_review_campaigns")
    op.drop_table("access_review_campaigns")
