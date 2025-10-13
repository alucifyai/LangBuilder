"""Add created_by and updated_by to role table

Revision ID: 1b16e3cd2714
Revises: 88da2a1f7a68
Create Date: 2025-10-11 23:24:23.681026

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '1b16e3cd2714'
down_revision: Union[str, None] = '88da2a1f7a68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add audit fields created_by and updated_by to role table."""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)

    # Check if role table exists
    existing_tables = inspector.get_table_names()
    if "role" not in existing_tables:
        print("[Audit Fields Migration] role table does not exist, skipping")
        return

    # Check which columns already exist
    role_columns = [col['name'] for col in inspector.get_columns('role')]

    with op.batch_alter_table('role', schema=None) as batch_op:
        # Add created_by if it doesn't exist
        if 'created_by' not in role_columns:
            print("[Audit Fields Migration] Adding created_by column to role table...")
            batch_op.add_column(sa.Column('created_by', sa.UUID(), nullable=True))
            batch_op.create_foreign_key('fk_role_created_by_user', 'user', ['created_by'], ['id'])
        else:
            print("[Audit Fields Migration] created_by column already exists, skipping")

        # Add updated_by if it doesn't exist
        if 'updated_by' not in role_columns:
            print("[Audit Fields Migration] Adding updated_by column to role table...")
            batch_op.add_column(sa.Column('updated_by', sa.UUID(), nullable=True))
            batch_op.create_foreign_key('fk_role_updated_by_user', 'user', ['updated_by'], ['id'])
        else:
            print("[Audit Fields Migration] updated_by column already exists, skipping")


def downgrade() -> None:
    """Remove audit fields created_by and updated_by from role table."""
    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.drop_constraint('fk_role_updated_by_user', type_='foreignkey')
        batch_op.drop_constraint('fk_role_created_by_user', type_='foreignkey')
        batch_op.drop_column('updated_by')
        batch_op.drop_column('created_by')
