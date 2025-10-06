"""Add audit_log table

Revision ID: 005_add_audit_log
Revises: 004_add_invite_table
Create Date: 2025-10-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_add_audit_log"
down_revision: Union[str, None] = "004_add_invite_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit_log table."""
    op.create_table(
        "auditlog",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("actor_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("action", sa.Enum(
            "role_created",
            "role_updated",
            "role_deleted",
            "grant_created",
            "grant_revoked",
            "permission_created",
            "invite_created",
            "invite_accepted",
            name="auditaction",
        ), nullable=False),
        sa.Column("resource_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("resource_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("before_state", sa.JSON(), nullable=True),
        sa.Column("after_state", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for query performance
    op.create_index(
        op.f("ix_auditlog_timestamp"),
        "auditlog",
        ["timestamp"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auditlog_actor_id"),
        "auditlog",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auditlog_action"),
        "auditlog",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auditlog_resource_type"),
        "auditlog",
        ["resource_type"],
        unique=False,
    )


def downgrade() -> None:
    """Drop audit_log table."""
    op.drop_index(op.f("ix_auditlog_resource_type"), table_name="auditlog")
    op.drop_index(op.f("ix_auditlog_action"), table_name="auditlog")
    op.drop_index(op.f("ix_auditlog_actor_id"), table_name="auditlog")
    op.drop_index(op.f("ix_auditlog_timestamp"), table_name="auditlog")
    op.drop_table("auditlog")
