"""add grant table

Revision ID: 003_rbac_grant
Revises: 002_rbac_role
Create Date: 2025-10-05 20:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_rbac_grant"
down_revision: Union[str, None] = "002_rbac_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create principal_type enum
    principal_type_enum = sa.Enum(
        "user", "group", "service_account", name="principal_type_enum"
    )
    principal_type_enum.create(op.get_bind(), checkfirst=True)

    # Create scope_type enum
    scope_type_enum = sa.Enum(
        "workspace", "project", "environment", "flow", "component", name="scope_type_enum"
    )
    scope_type_enum.create(op.get_bind(), checkfirst=True)

    # Create grant table
    op.create_table(
        "grant",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("principal_type", principal_type_enum, nullable=False),
        sa.Column("principal_id", sa.String(), nullable=False),
        sa.Column("role_id", sa.String(), nullable=False),
        sa.Column("scope_type", scope_type_enum, nullable=False),
        sa.Column("scope_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for query performance
    op.create_index(op.f("ix_grant_principal_type"), "grant", ["principal_type"], unique=False)
    op.create_index(op.f("ix_grant_principal_id"), "grant", ["principal_id"], unique=False)
    op.create_index(op.f("ix_grant_role_id"), "grant", ["role_id"], unique=False)
    op.create_index(op.f("ix_grant_scope_type"), "grant", ["scope_type"], unique=False)
    op.create_index(op.f("ix_grant_scope_id"), "grant", ["scope_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_grant_scope_id"), table_name="grant")
    op.drop_index(op.f("ix_grant_scope_type"), table_name="grant")
    op.drop_index(op.f("ix_grant_role_id"), table_name="grant")
    op.drop_index(op.f("ix_grant_principal_id"), table_name="grant")
    op.drop_index(op.f("ix_grant_principal_type"), table_name="grant")
    op.drop_table("grant")

    # Drop enums
    sa.Enum(name="scope_type_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="principal_type_enum").drop(op.get_bind(), checkfirst=True)
