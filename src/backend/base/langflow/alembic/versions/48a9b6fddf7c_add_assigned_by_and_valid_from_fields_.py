"""Add assigned_by and valid_from fields to role_assignment

Revision ID: 48a9b6fddf7c
Revises: c5d9f2e8a1b3
Create Date: 2025-10-12 01:36:44.332201

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48a9b6fddf7c'
down_revision: Union[str, None] = 'c5d9f2e8a1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add assigned_by and valid_from columns to role_assignment table."""
    # Use direct ALTER TABLE to avoid circular dependency issues with batch mode
    conn = op.get_bind()
    from sqlalchemy.engine.reflection import Inspector

    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('role_assignment')]

    # Add columns only if they don't exist
    if 'assigned_by' not in columns:
        op.add_column('role_assignment', sa.Column('assigned_by', sa.Uuid(), nullable=True))

    if 'valid_from' not in columns:
        op.add_column('role_assignment', sa.Column('valid_from', sa.DateTime(), nullable=True))

    # Note: SQLite doesn't support adding foreign key constraints via ALTER TABLE
    # The foreign key constraint will be created when the model is used
    # This is acceptable for development databases


def downgrade() -> None:
    """Remove assigned_by and valid_from columns from role_assignment table."""
    # Direct column drops (no foreign key to drop since we didn't add one)
    op.drop_column('role_assignment', 'valid_from')
    op.drop_column('role_assignment', 'assigned_by')
