"""Add RBAC models Phase 1 - Core RBAC schema (Roles, Permissions, Grants, Groups, ServiceAccounts, AuditLog).

Revision ID: rbac001
Revises: fd531f8868b1
Create Date: 2025-10-04 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2e587a3e533d"
down_revision: str | Sequence[str] | None = "3162e83e485f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add RBAC models and update existing models for RBAC support."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()

    # 1. Create Permission table
    if "permission" not in table_names:
        op.create_table(
            "permission",
            sa.Column("id", sa.String(), nullable=False, primary_key=True),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("resource_type", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_permission_action"), "permission", ["action"])
        op.create_index(op.f("ix_permission_resource_type"), "permission", ["resource_type"])

    # 2. Create Role table
    if "role" not in table_names:
        op.create_table(
            "role",
            sa.Column("id", sa.String(), nullable=False, primary_key=True),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("permissions", sa.JSON(), nullable=False),
            sa.Column("is_system_role", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name", name="unique_role_name"),
        )
        op.create_index(op.f("ix_role_name"), "role", ["name"])

    # 3. Create Group table - DISABLED
    # TODO: Re-enable when Group model is fully implemented with many-to-many relationships
    # if "group" not in table_names:
    #     op.create_table(
    #         "group",
    #         sa.Column("id", sa.String(), nullable=False, primary_key=True),
    #         sa.Column("name", sa.String(), nullable=False, unique=True),
    #         sa.Column("description", sa.String(), nullable=True),
    #         sa.Column("external_id", sa.String(), nullable=True),
    #         sa.Column("metadata", sa.JSON(), nullable=True),
    #         sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    #         sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    #         sa.PrimaryKeyConstraint("id"),
    #         sa.UniqueConstraint("name", name="unique_group_name"),
    #     )
    #     op.create_index(op.f("ix_group_name"), "group", ["name"])
    #     op.create_index(op.f("ix_group_external_id"), "group", ["external_id"])

    # 4. Create ServiceAccount table
    if "service_account" not in table_names:
        op.create_table(
            "service_account",
            sa.Column("id", sa.String(), nullable=False, primary_key=True),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("metadata", sa.JSON(), nullable=True),
            # NOTE: Hashed API key storage (RBAC_PHASE1_AUDIT_REPORT CONCERN #1)
            sa.Column("api_key_hash", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by", sa.String(), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name", name="unique_service_account_name"),
            sa.ForeignKeyConstraint(
                ["created_by"],
                ["user.id"],
            ),
        )
        op.create_index(op.f("ix_service_account_name"), "service_account", ["name"])
        op.create_index(op.f("ix_service_account_api_key_hash"), "service_account", ["api_key_hash"])

    # 5. Create Grant table
    if "grant" not in table_names:
        op.create_table(
            "grant",
            sa.Column("id", sa.String(), nullable=False, primary_key=True),
            sa.Column("principal_type", sa.String(), nullable=False),
            sa.Column("principal_id", sa.String(), nullable=False),
            sa.Column("role_id", sa.String(), nullable=False),
            sa.Column("scope_type", sa.String(), nullable=False),
            sa.Column("scope_id", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by", sa.String(), nullable=True),
            # Foreign keys for easier querying
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("group_id", sa.String(), nullable=True),
            sa.Column("service_account_id", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["role_id"],
                ["role.id"],
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["user.id"],
            ),
            sa.ForeignKeyConstraint(
                ["group_id"],
                ["group.id"],
            ),
            sa.ForeignKeyConstraint(
                ["service_account_id"],
                ["service_account.id"],
            ),
        )
        op.create_index(op.f("ix_grant_principal_type"), "grant", ["principal_type"])
        op.create_index(op.f("ix_grant_principal_id"), "grant", ["principal_id"])
        op.create_index(op.f("ix_grant_role_id"), "grant", ["role_id"])
        op.create_index(op.f("ix_grant_scope_type"), "grant", ["scope_type"])
        op.create_index(op.f("ix_grant_scope_id"), "grant", ["scope_id"])
        # Composite indexes for common query patterns (Audit Report RECOMMENDATIONS #4, #5)
        op.create_index("ix_grant_principal_lookup", "grant", ["principal_type", "principal_id"])
        op.create_index("ix_grant_scope_lookup", "grant", ["scope_type", "scope_id"])

    # 6. Create user_group association table - DISABLED
    # TODO: Re-enable when Group model is fully implemented
    # if "user_group" not in table_names:
    #     op.create_table(
    #         "user_group",
    #         sa.Column("user_id", sa.String(), nullable=False),
    #         sa.Column("group_id", sa.String(), nullable=False),
    #         sa.PrimaryKeyConstraint("user_id", "group_id"),
    #         sa.ForeignKeyConstraint(
    #             ["user_id"],
    #             ["user.id"],
    #         ),
    #         sa.ForeignKeyConstraint(
    #             ["group_id"],
    #             ["group.id"],
    #         ),
    #     )

    # 7. Create AuditLog table
    if "audit_log" not in table_names:
        op.create_table(
            "audit_log",
            sa.Column("id", sa.String(), nullable=False, primary_key=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("actor_type", sa.String(), nullable=False),
            sa.Column("actor_id", sa.String(), nullable=True),
            sa.Column("actor_name", sa.String(), nullable=True),
            sa.Column("resource_type", sa.String(), nullable=True),
            sa.Column("resource_id", sa.String(), nullable=True),
            sa.Column("details", sa.JSON(), nullable=True),
            sa.Column("result", sa.String(), nullable=True),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("ip_address", sa.String(), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_audit_log_timestamp"), "audit_log", ["timestamp"])
        op.create_index(op.f("ix_audit_log_action"), "audit_log", ["action"])
        op.create_index(op.f("ix_audit_log_actor_id"), "audit_log", ["actor_id"])
        op.create_index(op.f("ix_audit_log_resource_type"), "audit_log", ["resource_type"])
        op.create_index(op.f("ix_audit_log_resource_id"), "audit_log", ["resource_id"])

    # 8. Update ApiKey table to add RBAC scope support
    if "apikey" in table_names:
        column_names = [column["name"] for column in inspector.get_columns("apikey")]
        with op.batch_alter_table("apikey", schema=None) as batch_op:
            if "scope_type" not in column_names:
                batch_op.add_column(sa.Column("scope_type", sa.String(), nullable=True))
            if "scope_id" not in column_names:
                batch_op.add_column(sa.Column("scope_id", sa.String(), nullable=True))
            if "permissions" not in column_names:
                batch_op.add_column(sa.Column("permissions", sa.JSON(), nullable=True))

        # Add indexes if they don't exist
        existing_indexes = [idx["name"] for idx in inspector.get_indexes("apikey")]
        if "ix_apikey_scope_type" not in existing_indexes:
            op.create_index(op.f("ix_apikey_scope_type"), "apikey", ["scope_type"])
        if "ix_apikey_scope_id" not in existing_indexes:
            op.create_index(op.f("ix_apikey_scope_id"), "apikey", ["scope_id"])


def downgrade() -> None:
    """Remove RBAC models and revert changes to existing models."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()

    # Drop indexes and columns from apikey table
    if "apikey" in table_names:
        try:
            op.drop_index(op.f("ix_apikey_scope_type"), table_name="apikey")
        except Exception:
            pass
        try:
            op.drop_index(op.f("ix_apikey_scope_id"), table_name="apikey")
        except Exception:
            pass

        column_names = [column["name"] for column in inspector.get_columns("apikey")]
        with op.batch_alter_table("apikey", schema=None) as batch_op:
            if "scope_type" in column_names:
                batch_op.drop_column("scope_type")
            if "scope_id" in column_names:
                batch_op.drop_column("scope_id")
            if "permissions" in column_names:
                batch_op.drop_column("permissions")

    # Drop RBAC tables in reverse order of creation
    if "audit_log" in table_names:
        op.drop_table("audit_log")

    if "user_group" in table_names:
        op.drop_table("user_group")

    if "grant" in table_names:
        op.drop_table("grant")

    if "service_account" in table_names:
        op.drop_table("service_account")

    if "group" in table_names:
        op.drop_table("group")

    if "role" in table_names:
        op.drop_table("role")

    if "permission" in table_names:
        op.drop_table("permission")
