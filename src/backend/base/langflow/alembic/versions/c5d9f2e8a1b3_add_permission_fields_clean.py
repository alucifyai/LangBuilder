"""Add name, scope_level, and is_system_permission fields to Permission table (clean migration)

Revision ID: c5d9f2e8a1b3
Revises: 1b16e3cd2714
Create Date: 2025-10-12 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'c5d9f2e8a1b3'
down_revision: Union[str, None] = '1b16e3cd2714'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add name, scope_level, and is_system_permission fields to permission table."""
    # Get database connection
    conn = op.get_bind()

    # Step 1: Add columns (use raw SQL to check existence - avoids inspector deadlock)
    # Try to add columns, ignore if they already exist
    try:
        with op.batch_alter_table('permission', schema=None) as batch_op:
            batch_op.add_column(sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True))
    except sa.exc.OperationalError:
        pass  # Column already exists

    try:
        with op.batch_alter_table('permission', schema=None) as batch_op:
            batch_op.add_column(sa.Column('scope_level', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True))
    except sa.exc.OperationalError:
        pass  # Column already exists

    try:
        with op.batch_alter_table('permission', schema=None) as batch_op:
            batch_op.add_column(sa.Column('is_system_permission', sa.Boolean(), nullable=True, server_default='0'))
    except sa.exc.OperationalError:
        pass  # Column already exists

    # Step 2: Populate data (safe to run multiple times due to WHERE clauses)
    conn.execute(
        sa.text("UPDATE permission SET name = resource_type || '.' || action WHERE name IS NULL")
    )
    conn.execute(
        sa.text("""
            UPDATE permission
            SET scope_level = CASE
                WHEN resource_type = 'flow' THEN 'FLOW'
                WHEN resource_type = 'component' THEN 'COMPONENT'
                WHEN resource_type = 'project' THEN 'PROJECT'
                WHEN resource_type = 'workspace' THEN 'WORKSPACE'
                ELSE 'GLOBAL'
            END
            WHERE scope_level IS NULL
        """)
    )
    conn.execute(
        sa.text("UPDATE permission SET is_system_permission = 1 WHERE is_system_permission IS NULL")
    )

    # Step 3: Make columns non-nullable and add indexes
    try:
        with op.batch_alter_table('permission', schema=None) as batch_op:
            batch_op.alter_column('name', existing_type=sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False)
            batch_op.create_index(batch_op.f('ix_permission_name'), ['name'], unique=True)
    except (sa.exc.OperationalError, sa.exc.ProgrammingError):
        pass  # Already done

    try:
        with op.batch_alter_table('permission', schema=None) as batch_op:
            batch_op.alter_column('scope_level', existing_type=sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False)
            batch_op.create_index(batch_op.f('ix_permission_scope_level'), ['scope_level'], unique=False)
    except (sa.exc.OperationalError, sa.exc.ProgrammingError):
        pass  # Already done

    try:
        with op.batch_alter_table('permission', schema=None) as batch_op:
            batch_op.alter_column('is_system_permission', existing_type=sa.Boolean(), nullable=False, server_default=None)
            batch_op.create_index(batch_op.f('ix_permission_is_system_permission'), ['is_system_permission'], unique=False)
    except (sa.exc.OperationalError, sa.exc.ProgrammingError):
        pass  # Already done


def downgrade() -> None:
    """Remove name, scope_level, and is_system_permission fields from permission table."""
    with op.batch_alter_table('permission', schema=None) as batch_op:
        # Drop indexes
        try:
            batch_op.drop_index(batch_op.f('ix_permission_is_system_permission'))
        except:
            pass
        try:
            batch_op.drop_index(batch_op.f('ix_permission_scope_level'))
        except:
            pass
        try:
            batch_op.drop_index(batch_op.f('ix_permission_name'))
        except:
            pass

        # Drop columns
        try:
            batch_op.drop_column('is_system_permission')
        except:
            pass
        try:
            batch_op.drop_column('scope_level')
        except:
            pass
        try:
            batch_op.drop_column('name')
        except:
            pass
