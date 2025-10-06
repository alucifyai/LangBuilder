"""add scim tables

Revision ID: 007_add_scim_tables
Revises: 006_add_group_tables
Create Date: 2025-10-06 01:05:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007_add_scim_tables"
down_revision: Union[str, None] = "006_add_group_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create scim_users table
    op.create_table(
        "scim_users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("given_name", sa.String(), nullable=True),
        sa.Column("family_name", sa.String(), nullable=True),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("scim_meta", sa.JSON(), nullable=True),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
        sa.UniqueConstraint("email"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_scim_users_external_id"), "scim_users", ["external_id"], unique=True)
    op.create_index(op.f("ix_scim_users_user_id"), "scim_users", ["user_id"], unique=False)
    op.create_index(op.f("ix_scim_users_username"), "scim_users", ["username"], unique=False)
    op.create_index(op.f("ix_scim_users_email"), "scim_users", ["email"], unique=True)
    op.create_index(op.f("ix_scim_users_organization_id"), "scim_users", ["organization_id"], unique=False)

    # Create scim_groups table
    op.create_table(
        "scim_groups",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("mapped_role_id", sa.String(), nullable=True),
        sa.Column("mapped_scope_type", sa.String(), nullable=True),
        sa.Column("mapped_scope_id", sa.String(), nullable=True),
        sa.Column("scim_meta", sa.JSON(), nullable=True),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
        sa.ForeignKeyConstraint(["mapped_role_id"], ["role.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_scim_groups_external_id"), "scim_groups", ["external_id"], unique=True)
    op.create_index(op.f("ix_scim_groups_display_name"), "scim_groups", ["display_name"], unique=False)
    op.create_index(op.f("ix_scim_groups_organization_id"), "scim_groups", ["organization_id"], unique=False)

    # Create scim_group_memberships table
    op.create_table(
        "scim_group_memberships",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("scim_group_id", sa.String(), nullable=False),
        sa.Column("scim_user_id", sa.String(), nullable=False),
        sa.Column("member_ref", sa.String(), nullable=True),
        sa.Column("member_type", sa.String(), nullable=False, server_default="User"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["scim_group_id"], ["scim_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scim_user_id"], ["scim_users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_scim_group_memberships_scim_group_id"), "scim_group_memberships", ["scim_group_id"], unique=False)
    op.create_index(op.f("ix_scim_group_memberships_scim_user_id"), "scim_group_memberships", ["scim_user_id"], unique=False)

    # Create scim_provisioning_logs table
    op.create_table(
        "scim_provisioning_logs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("request_payload", sa.JSON(), nullable=True),
        sa.Column("response_payload", sa.JSON(), nullable=True),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.Column("idp_source", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scim_provisioning_logs_event_type"), "scim_provisioning_logs", ["event_type"], unique=False)
    op.create_index(op.f("ix_scim_provisioning_logs_resource_type"), "scim_provisioning_logs", ["resource_type"], unique=False)
    op.create_index(op.f("ix_scim_provisioning_logs_external_id"), "scim_provisioning_logs", ["external_id"], unique=False)
    op.create_index(op.f("ix_scim_provisioning_logs_status"), "scim_provisioning_logs", ["status"], unique=False)
    op.create_index(op.f("ix_scim_provisioning_logs_organization_id"), "scim_provisioning_logs", ["organization_id"], unique=False)
    op.create_index(op.f("ix_scim_provisioning_logs_created_at"), "scim_provisioning_logs", ["created_at"], unique=False)


def downgrade() -> None:
    # Drop scim_provisioning_logs
    op.drop_index(op.f("ix_scim_provisioning_logs_created_at"), table_name="scim_provisioning_logs")
    op.drop_index(op.f("ix_scim_provisioning_logs_organization_id"), table_name="scim_provisioning_logs")
    op.drop_index(op.f("ix_scim_provisioning_logs_status"), table_name="scim_provisioning_logs")
    op.drop_index(op.f("ix_scim_provisioning_logs_external_id"), table_name="scim_provisioning_logs")
    op.drop_index(op.f("ix_scim_provisioning_logs_resource_type"), table_name="scim_provisioning_logs")
    op.drop_index(op.f("ix_scim_provisioning_logs_event_type"), table_name="scim_provisioning_logs")
    op.drop_table("scim_provisioning_logs")

    # Drop scim_group_memberships
    op.drop_index(op.f("ix_scim_group_memberships_scim_user_id"), table_name="scim_group_memberships")
    op.drop_index(op.f("ix_scim_group_memberships_scim_group_id"), table_name="scim_group_memberships")
    op.drop_table("scim_group_memberships")

    # Drop scim_groups
    op.drop_index(op.f("ix_scim_groups_organization_id"), table_name="scim_groups")
    op.drop_index(op.f("ix_scim_groups_display_name"), table_name="scim_groups")
    op.drop_index(op.f("ix_scim_groups_external_id"), table_name="scim_groups")
    op.drop_table("scim_groups")

    # Drop scim_users
    op.drop_index(op.f("ix_scim_users_organization_id"), table_name="scim_users")
    op.drop_index(op.f("ix_scim_users_email"), table_name="scim_users")
    op.drop_index(op.f("ix_scim_users_username"), table_name="scim_users")
    op.drop_index(op.f("ix_scim_users_user_id"), table_name="scim_users")
    op.drop_index(op.f("ix_scim_users_external_id"), table_name="scim_users")
    op.drop_table("scim_users")
