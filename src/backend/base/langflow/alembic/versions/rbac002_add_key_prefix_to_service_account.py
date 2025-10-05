"""Add key_prefix to ServiceAccount for optimized authentication.

Revision ID: rbac002
Revises: rbac001
Create Date: 2025-10-04 00:00:00.000000

HIGH PRIORITY FIX #2: Optimize ServiceAccount authentication
Phase 2 Audit Recommendation #2

Adds indexed key_prefix field to service_account table for fast API key lookups.
Performance improvement: O(N) hash verification -> O(log N) indexed lookup + O(K) verification
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3a4b5c6d7e8f"
down_revision: str | Sequence[str] | None = "2e587a3e533d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add key_prefix column to service_account table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Check if table exists
    table_names = inspector.get_table_names()
    if "service_account" not in table_names:
        # Table doesn't exist yet (probably running migrations from scratch)
        # The key_prefix field will be created in rbac001 migration
        return

    # Check if column already exists
    columns = [col["name"] for col in inspector.get_columns("service_account")]
    if "key_prefix" in columns:
        # Column already exists, skip
        return

    # Add key_prefix column
    op.add_column(
        "service_account",
        sa.Column("key_prefix", sa.String(length=16), nullable=True)
    )

    # Create index for fast lookups
    op.create_index(
        op.f("ix_service_account_key_prefix"),
        "service_account",
        ["key_prefix"]
    )


def downgrade() -> None:
    """Remove key_prefix column from service_account table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Check if table exists
    table_names = inspector.get_table_names()
    if "service_account" not in table_names:
        return

    # Check if column exists
    columns = [col["name"] for col in inspector.get_columns("service_account")]
    if "key_prefix" not in columns:
        return

    # Drop index first
    indexes = inspector.get_indexes("service_account")
    if any(idx["name"] == "ix_service_account_key_prefix" for idx in indexes):
        op.drop_index(op.f("ix_service_account_key_prefix"), table_name="service_account")

    # Drop column
    op.drop_column("service_account", "key_prefix")
