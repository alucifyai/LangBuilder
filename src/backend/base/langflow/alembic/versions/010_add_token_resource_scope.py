"""add token resource scope

Revision ID: 010_add_token_resource_scope
Revises: 009_add_access_review_tables
Create Date: 2025-10-06 02:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010_add_token_resource_scope"
down_revision: Union[str, None] = "009_add_access_review_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add resource scope columns to api_token table
    op.add_column("api_token", sa.Column("scope_type", sa.String(), nullable=True))
    op.add_column("api_token", sa.Column("scope_id", sa.String(), nullable=True))

    # Add index on scope_id for efficient lookups
    op.create_index(op.f("ix_api_token_scope_id"), "api_token", ["scope_id"], unique=False)


def downgrade() -> None:
    # Drop index and columns
    op.drop_index(op.f("ix_api_token_scope_id"), table_name="api_token")
    op.drop_column("api_token", "scope_id")
    op.drop_column("api_token", "scope_type")
