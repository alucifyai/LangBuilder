"""add role table

Revision ID: 002_rbac_role
Revises: 001_rbac_permission
Create Date: 2025-10-05 20:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_rbac_role"
down_revision: Union[str, None] = "001_rbac_permission"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create role table
    op.create_table(
        "role",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    # Create index for role name
    op.create_index(op.f("ix_role_name"), "role", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_role_name"), table_name="role")
    op.drop_table("role")
