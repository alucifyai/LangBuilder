"""Add created_by field to workspace model

Revision ID: 75014ffc833e
Revises: 76de831c80a4
Create Date: 2025-10-12 10:55:56.865295

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.engine.reflection import Inspector
from langflow.utils import migration


# revision identifiers, used by Alembic.
revision: str = '75014ffc833e'
down_revision: Union[str, None] = '76de831c80a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add created_by field to workspace table with backfill from workspace_member owners."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Check if column already exists (for idempotency)
    columns = [col['name'] for col in inspector.get_columns('workspace')]
    if 'created_by' in columns:
        return

    # Step 1: Add created_by column as nullable first
    with op.batch_alter_table('workspace', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_by', sa.UUID(), nullable=True))
        batch_op.create_foreign_key('fk_workspace_created_by', 'user', ['created_by'], ['id'])
        batch_op.create_index('ix_workspace_created_by', ['created_by'], unique=False)

    # Step 2: Backfill created_by from workspace_member where role='owner'
    # Get first owner for each workspace (by joined_at ascending)
    conn.execute(sa.text("""
        UPDATE workspace
        SET created_by = (
            SELECT user_id
            FROM workspace_member
            WHERE workspace_member.workspace_id = workspace.id
              AND workspace_member.role = 'owner'
            ORDER BY workspace_member.joined_at ASC
            LIMIT 1
        )
        WHERE created_by IS NULL
    """))

    # Step 3: For any workspaces without owners (edge case), use first member
    conn.execute(sa.text("""
        UPDATE workspace
        SET created_by = (
            SELECT user_id
            FROM workspace_member
            WHERE workspace_member.workspace_id = workspace.id
            ORDER BY workspace_member.joined_at ASC
            LIMIT 1
        )
        WHERE created_by IS NULL
    """))

    # Step 4: Make created_by NOT NULL (now that all rows have values)
    with op.batch_alter_table('workspace', schema=None) as batch_op:
        batch_op.alter_column('created_by', nullable=False)


def downgrade() -> None:
    """Remove created_by field from workspace table."""
    conn = op.get_bind()

    with op.batch_alter_table('workspace', schema=None) as batch_op:
        batch_op.drop_index('ix_workspace_created_by')
        batch_op.drop_constraint('fk_workspace_created_by', type_='foreignkey')
        batch_op.drop_column('created_by')
