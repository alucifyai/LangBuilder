"""Add default_project_id to User

Revision ID: e8f9a3b2c1d0
Revises: 19db92f8586c
Create Date: 2025-11-06 00:00:00.000000

"""

from typing import Optional, Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e8f9a3b2c1d0"
down_revision: Union[str, None] = "19db92f8586c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add default_project_id column to user table."""
    # Add default_project_id column without foreign key constraint to avoid circular dependency
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("default_project_id", sa.String(), nullable=True)
        )


def downgrade() -> None:
    """Remove default_project_id column from user table."""
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("default_project_id")
