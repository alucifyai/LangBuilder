"""add group tables

Revision ID: 006_add_group_tables
Revises: 005_add_audit_log_table
Create Date: 2025-10-06 01:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_add_group_tables"
down_revision: Union[str, None] = "005_add_audit_log_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create groups table
    op.create_table(
        "groups",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_groups_name"), "groups", ["name"], unique=True)
    op.create_index(op.f("ix_groups_organization_id"), "groups", ["organization_id"], unique=False)

    # Create group_memberships table
    op.create_table(
        "group_memberships",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("group_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_group_memberships_group_id"), "group_memberships", ["group_id"], unique=False)
    op.create_index(op.f("ix_group_memberships_user_id"), "group_memberships", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_group_memberships_user_id"), table_name="group_memberships")
    op.drop_index(op.f("ix_group_memberships_group_id"), table_name="group_memberships")
    op.drop_table("group_memberships")

    op.drop_index(op.f("ix_groups_organization_id"), table_name="groups")
    op.drop_index(op.f("ix_groups_name"), table_name="groups")
    op.drop_table("groups")
