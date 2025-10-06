"""add invite table

Revision ID: 004_rbac_invite
Revises: 003_rbac_grant
Create Date: 2025-10-05 21:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_rbac_invite"
down_revision: Union[str, None] = "003_rbac_grant"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create invite_status enum
    invite_status_enum = sa.Enum("pending", "accepted", "expired", name="invite_status_enum")
    invite_status_enum.create(op.get_bind(), checkfirst=True)

    # Create invite table
    op.create_table(
        "invite",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("inviter_id", sa.String(), nullable=False),
        sa.Column("invitee_email", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("role_id", sa.String(), nullable=False),
        sa.Column("status", invite_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(op.f("ix_invite_inviter_id"), "invite", ["inviter_id"], unique=False)
    op.create_index(op.f("ix_invite_invitee_email"), "invite", ["invitee_email"], unique=False)
    op.create_index(op.f("ix_invite_workspace_id"), "invite", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_invite_role_id"), "invite", ["role_id"], unique=False)
    op.create_index(op.f("ix_invite_status"), "invite", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_invite_status"), table_name="invite")
    op.drop_index(op.f("ix_invite_role_id"), table_name="invite")
    op.drop_index(op.f("ix_invite_workspace_id"), table_name="invite")
    op.drop_index(op.f("ix_invite_invitee_email"), table_name="invite")
    op.drop_index(op.f("ix_invite_inviter_id"), table_name="invite")
    op.drop_table("invite")

    # Drop enum
    sa.Enum(name="invite_status_enum").drop(op.get_bind(), checkfirst=True)
