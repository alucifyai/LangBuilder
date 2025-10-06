"""add permission table

Revision ID: 001_rbac_permission
Revises: fd531f8868b1
Create Date: 2025-10-05 20:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_rbac_permission"
down_revision: Union[str, None] = "fd531f8868b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create permission table
    op.create_table(
        "permission",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create indexes for query performance
    op.create_index(op.f("ix_permission_resource_type"), "permission", ["resource_type"], unique=False)
    op.create_index(op.f("ix_permission_action"), "permission", ["action"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_permission_action"), table_name="permission")
    op.drop_index(op.f("ix_permission_resource_type"), table_name="permission")
    op.drop_table("permission")
