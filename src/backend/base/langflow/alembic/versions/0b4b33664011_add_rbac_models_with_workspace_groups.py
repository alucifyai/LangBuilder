"""Add RBAC models with workspace, groups, and environments

Revision ID: 0b4b33664011
Revises: fd531f8868b1
Create Date: 2025-10-11 12:00:00.000000

This migration adds comprehensive RBAC support including:
- Core RBAC: Role, Permission, RolePermission, RoleAssignment, ServiceAccount, AuditLog, SSOIntegration
- Multi-tenancy: Workspace, WorkspaceMember
- Group management: UserGroup, UserGroupMember
- Environment scoping: Environment
- User invitations: Invitation
- Modified tables: ApiKey, Folder, Flow to support RBAC

Data Migration Strategy:
- Creates "Default Workspace" for existing installations
- Assigns all existing users as owners of default workspace
- Assigns all existing folders to default workspace
"""

import json
from datetime import datetime, timezone
from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision: str = "0b4b33664011"
down_revision: Union[str, None] = "fd531f8868b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all RBAC tables and perform data migration."""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    existing_tables = inspector.get_table_names()

    # ====================
    # 1. CREATE NEW TABLES
    # ====================

    # Workspace table (top-level tenant isolation)
    if "workspace" not in existing_tables:
        op.create_table(
            "workspace",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("slug", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=1000), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("settings", sa.JSON(), nullable=False),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_workspace")),
            sa.UniqueConstraint("slug", name=op.f("uq_workspace_slug")),
        )
        op.create_index(op.f("ix_workspace_name"), "workspace", ["name"], unique=False)

    # WorkspaceMember table (workspace membership junction)
    if "workspace_member" not in existing_tables:
        op.create_table(
            "workspace_member",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("workspace_id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_workspace_member_user_id_user")),
            sa.ForeignKeyConstraint(
                ["workspace_id"], ["workspace.id"], name=op.f("fk_workspace_member_workspace_id_workspace")
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_workspace_member")),
            sa.UniqueConstraint("workspace_id", "user_id", name=op.f("uq_workspace_member_workspace_id")),
        )
        op.create_index(op.f("ix_workspace_member_user_id"), "workspace_member", ["user_id"], unique=False)
        op.create_index(
            op.f("ix_workspace_member_workspace_id"), "workspace_member", ["workspace_id"], unique=False
        )

    # UserGroup table (groups for batch role assignments)
    if "user_group" not in existing_tables:
        op.create_table(
            "user_group",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("workspace_id", sa.UUID(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=1000), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("external_id", sa.String(length=255), nullable=True),
            sa.Column("scim_synced", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["workspace_id"], ["workspace.id"], name=op.f("fk_user_group_workspace_id_workspace")
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_user_group")),
            sa.UniqueConstraint("workspace_id", "name", name=op.f("uq_user_group_workspace_id")),
        )
        op.create_index(op.f("ix_user_group_external_id"), "user_group", ["external_id"], unique=False)
        op.create_index(op.f("ix_user_group_name"), "user_group", ["name"], unique=False)
        op.create_index(op.f("ix_user_group_workspace_id"), "user_group", ["workspace_id"], unique=False)

    # UserGroupMember table (group membership junction)
    if "user_group_member" not in existing_tables:
        op.create_table(
            "user_group_member",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("group_id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["group_id"], ["user_group.id"], name=op.f("fk_user_group_member_group_id_user_group")
            ),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_user_group_member_user_id_user")),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_user_group_member")),
            sa.UniqueConstraint("group_id", "user_id", name=op.f("uq_user_group_member_group_id")),
        )
        op.create_index(op.f("ix_user_group_member_group_id"), "user_group_member", ["group_id"], unique=False)
        op.create_index(op.f("ix_user_group_member_user_id"), "user_group_member", ["user_id"], unique=False)

    # Role table (customizable roles)
    if "role" not in existing_tables:
        op.create_table(
            "role",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=1000), nullable=True),
            sa.Column("is_system_role", sa.Boolean(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_role")),
            sa.UniqueConstraint("name", name=op.f("uq_role_name")),
        )
        op.create_index(op.f("ix_role_is_system_role"), "role", ["is_system_role"], unique=False)
        op.create_index(op.f("ix_role_name"), "role", ["name"], unique=False)

    # Permission table (granular permission catalog)
    if "permission" not in existing_tables:
        op.create_table(
            "permission",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("resource_type", sa.String(length=100), nullable=False),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=1000), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_permission")),
            sa.UniqueConstraint("resource_type", "action", name=op.f("uq_permission_resource_type")),
        )
        op.create_index(op.f("ix_permission_resource_type"), "permission", ["resource_type"], unique=False)

    # RolePermission table (role-permission junction)
    if "role_permission" not in existing_tables:
        op.create_table(
            "role_permission",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("role_id", sa.UUID(), nullable=False),
            sa.Column("permission_id", sa.UUID(), nullable=False),
            sa.ForeignKeyConstraint(
                ["permission_id"], ["permission.id"], name=op.f("fk_role_permission_permission_id_permission")
            ),
            sa.ForeignKeyConstraint(["role_id"], ["role.id"], name=op.f("fk_role_permission_role_id_role")),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_role_permission")),
            sa.UniqueConstraint("role_id", "permission_id", name=op.f("uq_role_permission_role_id")),
        )

    # ServiceAccount table (non-human identities)
    if "service_account" not in existing_tables:
        op.create_table(
            "service_account",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=1000), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_by_user_id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["created_by_user_id"], ["user.id"], name=op.f("fk_service_account_created_by_user_id_user")
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_service_account")),
            sa.UniqueConstraint("name", name=op.f("uq_service_account_name")),
        )
        op.create_index(
            op.f("ix_service_account_created_by_user_id"), "service_account", ["created_by_user_id"], unique=False
        )
        op.create_index(op.f("ix_service_account_name"), "service_account", ["name"], unique=False)

    # RoleAssignment table (assigns roles to users/service accounts/groups at scopes)
    if "role_assignment" not in existing_tables:
        op.create_table(
            "role_assignment",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("role_id", sa.UUID(), nullable=False),
            sa.Column("assignee_type", sa.String(length=50), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=True),
            sa.Column("service_account_id", sa.UUID(), nullable=True),
            sa.Column("group_id", sa.UUID(), nullable=True),
            sa.Column("scope_type", sa.String(length=50), nullable=False),
            sa.Column("scope_id", sa.UUID(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.CheckConstraint(
                "(assignee_type = 'user' AND user_id IS NOT NULL AND service_account_id IS NULL AND group_id IS NULL) OR "
                "(assignee_type = 'service_account' AND service_account_id IS NOT NULL AND user_id IS NULL AND group_id IS NULL) OR "
                "(assignee_type = 'group' AND group_id IS NOT NULL AND user_id IS NULL AND service_account_id IS NULL)",
                name=op.f("ck_role_assignment_ck_assignee_type_consistency"),
            ),
            sa.ForeignKeyConstraint(
                ["group_id"], ["user_group.id"], name=op.f("fk_role_assignment_group_id_user_group")
            ),
            sa.ForeignKeyConstraint(["role_id"], ["role.id"], name=op.f("fk_role_assignment_role_id_role")),
            sa.ForeignKeyConstraint(
                ["service_account_id"],
                ["service_account.id"],
                name=op.f("fk_role_assignment_service_account_id_service_account"),
            ),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_role_assignment_user_id_user")),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_role_assignment")),
        )
        op.create_index(
            op.f("ix_role_assignment_assignee_type"), "role_assignment", ["assignee_type"], unique=False
        )
        op.create_index(op.f("ix_role_assignment_group_id"), "role_assignment", ["group_id"], unique=False)
        op.create_index(op.f("ix_role_assignment_role_id"), "role_assignment", ["role_id"], unique=False)
        op.create_index(op.f("ix_role_assignment_scope_id"), "role_assignment", ["scope_id"], unique=False)
        op.create_index(
            "ix_role_assignment_scope", "role_assignment", ["scope_type", "scope_id"], unique=False
        )  # Composite index
        op.create_index(
            op.f("ix_role_assignment_service_account_id"), "role_assignment", ["service_account_id"], unique=False
        )
        op.create_index(op.f("ix_role_assignment_user_id"), "role_assignment", ["user_id"], unique=False)

    # Environment table (deployment environment scoping)
    if "environment" not in existing_tables:
        op.create_table(
            "environment",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("project_id", sa.UUID(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("environment_type", sa.String(length=50), nullable=False),
            sa.Column("description", sa.String(length=1000), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["project_id"], ["folder.id"], name=op.f("fk_environment_project_id_folder")),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_environment")),
            sa.UniqueConstraint("project_id", "name", name=op.f("uq_environment_project_id")),
        )
        op.create_index(
            op.f("ix_environment_environment_type"), "environment", ["environment_type"], unique=False
        )
        op.create_index(op.f("ix_environment_project_id"), "environment", ["project_id"], unique=False)

    # Invitation table (user invitation workflow)
    if "invitation" not in existing_tables:
        op.create_table(
            "invitation",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("workspace_id", sa.UUID(), nullable=False),
            sa.Column("invited_by_user_id", sa.UUID(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("invited_user_id", sa.UUID(), nullable=True),
            sa.Column("role_id", sa.UUID(), nullable=True),
            sa.Column("scope_type", sa.String(length=50), nullable=False),
            sa.Column("scope_id", sa.UUID(), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("message", sa.String(length=1000), nullable=True),
            sa.Column("token", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["invited_by_user_id"], ["user.id"], name=op.f("fk_invitation_invited_by_user_id_user")
            ),
            sa.ForeignKeyConstraint(
                ["invited_user_id"], ["user.id"], name=op.f("fk_invitation_invited_user_id_user")
            ),
            sa.ForeignKeyConstraint(["role_id"], ["role.id"], name=op.f("fk_invitation_role_id_role")),
            sa.ForeignKeyConstraint(
                ["workspace_id"], ["workspace.id"], name=op.f("fk_invitation_workspace_id_workspace")
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_invitation")),
            sa.UniqueConstraint("token", name=op.f("uq_invitation_token")),
        )
        op.create_index(op.f("ix_invitation_email"), "invitation", ["email"], unique=False)
        op.create_index(op.f("ix_invitation_status"), "invitation", ["status"], unique=False)
        op.create_index(op.f("ix_invitation_token"), "invitation", ["token"], unique=False)
        op.create_index(op.f("ix_invitation_workspace_id"), "invitation", ["workspace_id"], unique=False)

    # AuditLog table (immutable audit trail)
    if "audit_log" not in existing_tables:
        op.create_table(
            "audit_log",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("event_type", sa.String(length=100), nullable=False),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("resource_type", sa.String(length=100), nullable=True),
            sa.Column("resource_id", sa.UUID(), nullable=True),
            sa.Column("actor_type", sa.String(length=50), nullable=False),
            sa.Column("actor_id", sa.UUID(), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("details", sa.JSON(), nullable=True),
            sa.Column("ip_address", sa.String(length=100), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log")),
        )
        op.create_index(op.f("ix_audit_log_actor_id"), "audit_log", ["actor_id"], unique=False)
        op.create_index(op.f("ix_audit_log_event_type"), "audit_log", ["event_type"], unique=False)
        op.create_index(op.f("ix_audit_log_resource_id"), "audit_log", ["resource_id"], unique=False)

    # SSOIntegration table (SSO provider configuration)
    if "sso_integration" not in existing_tables:
        op.create_table(
            "sso_integration",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=False),
            sa.Column("provider_type", sa.String(length=50), nullable=False),
            sa.Column("config", sa.JSON(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_by_user_id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["created_by_user_id"], ["user.id"], name=op.f("fk_sso_integration_created_by_user_id_user")
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_sso_integration")),
            sa.UniqueConstraint("name", name=op.f("uq_sso_integration_name")),
        )
        op.create_index(
            op.f("ix_sso_integration_created_by_user_id"), "sso_integration", ["created_by_user_id"], unique=False
        )
        op.create_index(op.f("ix_sso_integration_name"), "sso_integration", ["name"], unique=False)

    # ===================================
    # 2. MODIFY EXISTING TABLES (add RBAC columns)
    # ===================================

    # Add RBAC fields to api_key table (only if table exists)
    if "api_key" in existing_tables:
        # Check which columns already exist
        api_key_columns = [col['name'] for col in inspector.get_columns('api_key')]
        columns_to_add = []

        if 'workspace_id' not in api_key_columns:
            columns_to_add.append('workspace_id')
        if 'scope_type' not in api_key_columns:
            columns_to_add.append('scope_type')
        if 'scope_id' not in api_key_columns:
            columns_to_add.append('scope_id')
        if 'scoped_permissions' not in api_key_columns:
            columns_to_add.append('scoped_permissions')
        if 'service_account_id' not in api_key_columns:
            columns_to_add.append('service_account_id')

        if columns_to_add:
            print(f"[RBAC Migration] Adding RBAC columns to api_key table: {columns_to_add}...")
            with op.batch_alter_table("api_key", schema=None) as batch_op:
                if 'workspace_id' in columns_to_add:
                    batch_op.add_column(sa.Column("workspace_id", sa.UUID(), nullable=True))
                    batch_op.create_index(batch_op.f("ix_api_key_workspace_id"), ["workspace_id"], unique=False)
                    batch_op.create_foreign_key(
                        batch_op.f("fk_api_key_workspace_id_workspace"), "workspace", ["workspace_id"], ["id"]
                    )
                if 'scope_type' in columns_to_add:
                    batch_op.add_column(sa.Column("scope_type", sa.String(length=50), nullable=True))
                if 'scope_id' in columns_to_add:
                    batch_op.add_column(sa.Column("scope_id", sa.UUID(), nullable=True))
                    batch_op.create_index(batch_op.f("ix_api_key_scope_id"), ["scope_id"], unique=False)
                if 'scoped_permissions' in columns_to_add:
                    batch_op.add_column(sa.Column("scoped_permissions", sa.JSON(), nullable=True))
                if 'service_account_id' in columns_to_add:
                    batch_op.add_column(sa.Column("service_account_id", sa.UUID(), nullable=True))
                    batch_op.create_index(batch_op.f("ix_api_key_service_account_id"), ["service_account_id"], unique=False)
                    batch_op.create_foreign_key(
                        batch_op.f("fk_api_key_service_account_id_service_account"),
                        "service_account",
                        ["service_account_id"],
                        ["id"],
                    )
        else:
            print("[RBAC Migration] All RBAC columns already exist in api_key table, skipping")
    else:
        print("[RBAC Migration] api_key table does not exist, skipping column additions")

    # Add workspace_id to folder table (nullable initially for data migration, only if table exists)
    if "folder" in existing_tables:
        # Check if workspace_id column already exists
        folder_columns = [col['name'] for col in inspector.get_columns('folder')]
        if 'workspace_id' not in folder_columns:
            print("[RBAC Migration] Adding workspace_id column to folder table...")
            with op.batch_alter_table("folder", schema=None) as batch_op:
                batch_op.add_column(sa.Column("workspace_id", sa.UUID(), nullable=True))
                batch_op.create_index(batch_op.f("ix_folder_workspace_id"), ["workspace_id"], unique=False)
        else:
            print("[RBAC Migration] workspace_id column already exists in folder table, skipping")
    else:
        print("[RBAC Migration] folder table does not exist, skipping column additions")

    # Add environment_id to flow table (nullable permanently for backward compat, only if table exists)
    if "flow" in existing_tables:
        # Check if environment_id column already exists
        flow_columns = [col['name'] for col in inspector.get_columns('flow')]
        if 'environment_id' not in flow_columns:
            print("[RBAC Migration] Adding environment_id column to flow table...")
            with op.batch_alter_table("flow", schema=None) as batch_op:
                batch_op.add_column(sa.Column("environment_id", sa.UUID(), nullable=True))
                batch_op.create_index(batch_op.f("ix_flow_environment_id"), ["environment_id"], unique=False)
                batch_op.create_foreign_key(
                    batch_op.f("fk_flow_environment_id_environment"), "environment", ["environment_id"], ["id"]
                )
        else:
            print("[RBAC Migration] environment_id column already exists in flow table, skipping")
    else:
        print("[RBAC Migration] flow table does not exist, skipping column additions")

    # ===================================
    # 3. DATA MIGRATION - Create Default Workspace for Existing Users
    # ===================================

    session = Session(bind=bind)
    try:
        # Check if any users exist
        result = session.execute(text("SELECT COUNT(*) as count FROM user"))
        row = result.fetchone()
        existing_users = row[0] if row else 0

        if existing_users > 0:
            print(f"[RBAC Migration] Found {existing_users} existing users, creating default workspace...")

            # Create default workspace
            default_workspace_id = str(uuid4())
            now = datetime.now(timezone.utc)

            session.execute(
                text(
                    """
                INSERT INTO workspace (id, name, slug, description, is_active, created_at, updated_at, settings)
                VALUES (:id, :name, :slug, :description, :is_active, :created_at, :updated_at, :settings)
            """
                ),
                {
                    "id": default_workspace_id,
                    "name": "Default Workspace",
                    "slug": "default",
                    "description": "Auto-created workspace for existing users during RBAC migration",
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                    "settings": json.dumps({}),
                },
            )
            print(f"[RBAC Migration] Created default workspace with ID: {default_workspace_id}")

            # Assign all existing users as owners of default workspace
            if bind.dialect.name == "postgresql":
                print("[RBAC Migration] Using PostgreSQL bulk insert for workspace members...")
                session.execute(
                    text(
                        """
                    INSERT INTO workspace_member (id, workspace_id, user_id, role, is_active, joined_at)
                    SELECT gen_random_uuid(), :workspace_id, id, 'owner', true, :joined_at
                    FROM "user"
                """
                    ),
                    {"workspace_id": default_workspace_id, "joined_at": now},
                )
            else:  # SQLite
                # For SQLite, we need to insert one by one
                print("[RBAC Migration] Using SQLite individual inserts for workspace members...")
                users_result = session.execute(text("SELECT id FROM user"))
                users = users_result.fetchall()
                for idx, user_row in enumerate(users, 1):
                    try:
                        session.execute(
                            text(
                                """
                            INSERT INTO workspace_member (id, workspace_id, user_id, role, is_active, joined_at)
                            VALUES (:id, :workspace_id, :user_id, 'owner', 1, :joined_at)
                        """
                            ),
                            {
                                "id": str(uuid4()),
                                "workspace_id": default_workspace_id,
                                "user_id": str(user_row[0]),
                                "joined_at": now,
                            },
                        )
                        if idx % 100 == 0:
                            print(f"[RBAC Migration] Processed {idx}/{len(users)} users...")
                    except Exception as e:
                        print(f"[RBAC Migration] Error assigning user {user_row[0]} to workspace: {e}")
                        raise

            # Assign all existing folders to default workspace
            print("[RBAC Migration] Assigning folders to default workspace...")
            result = session.execute(text("SELECT COUNT(*) FROM folder WHERE workspace_id IS NULL"))
            folders_to_migrate = result.scalar()
            print(f"[RBAC Migration] Found {folders_to_migrate} folders to migrate...")

            session.execute(
                text("UPDATE folder SET workspace_id = :workspace_id WHERE workspace_id IS NULL"),
                {"workspace_id": default_workspace_id},
            )

            session.commit()
            print("[RBAC Migration] Data migration committed successfully")

            # ===================================
            # 4. DATA MIGRATION VALIDATION
            # ===================================
            print("[RBAC Migration] Validating data migration...")

            # Verify all users are assigned to workspace
            result = session.execute(
                text("SELECT COUNT(*) FROM workspace_member WHERE workspace_id = :wid"),
                {"wid": default_workspace_id}
            )
            member_count = result.scalar()

            if member_count != existing_users:
                error_msg = f"User migration failed: {existing_users} users but {member_count} workspace members"
                print(f"[RBAC Migration] VALIDATION FAILED: {error_msg}")
                raise ValueError(error_msg)
            print(f"[RBAC Migration] ✓ All {existing_users} users successfully assigned to workspace")

            # Verify all folders are assigned to workspace
            result = session.execute(text("SELECT COUNT(*) FROM folder WHERE workspace_id IS NULL"))
            unassigned_folders = result.scalar()

            if unassigned_folders > 0:
                error_msg = f"Folder migration incomplete: {unassigned_folders} folders still unassigned"
                print(f"[RBAC Migration] VALIDATION FAILED: {error_msg}")
                raise ValueError(error_msg)

            result = session.execute(
                text("SELECT COUNT(*) FROM folder WHERE workspace_id = :wid"),
                {"wid": default_workspace_id}
            )
            assigned_folders = result.scalar()
            print(f"[RBAC Migration] ✓ All {assigned_folders} folders successfully assigned to workspace")

            # Verify workspace exists and is active
            result = session.execute(
                text("SELECT is_active FROM workspace WHERE id = :wid"),
                {"wid": default_workspace_id}
            )
            workspace_active = result.scalar()

            if not workspace_active:
                error_msg = "Default workspace was created but is not active"
                print(f"[RBAC Migration] VALIDATION FAILED: {error_msg}")
                raise ValueError(error_msg)
            print("[RBAC Migration] ✓ Default workspace is active")

            print("[RBAC Migration] ✓ All validations passed successfully")
        else:
            print("[RBAC Migration] No existing users found, skipping default workspace creation")
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

    # Make workspace_id non-nullable after data migration (only if folder table exists and column exists)
    if "folder" in existing_tables:
        folder_columns_info = inspector.get_columns('folder')
        workspace_col = next((col for col in folder_columns_info if col['name'] == 'workspace_id'), None)

        if workspace_col:
            # Check both foreign key and nullability
            folder_fks = inspector.get_foreign_keys('folder')
            fk_exists = any(fk['name'] == 'fk_folder_workspace_id_workspace' for fk in folder_fks)
            is_nullable = workspace_col.get('nullable', True)

            # Only need to add foreign key if it doesn't exist (keep column nullable per model definition)
            needs_update = not fk_exists

            if needs_update:
                print("[RBAC Migration] Adding foreign key to folder.workspace_id (keeping nullable=True per model)...")
                with op.batch_alter_table("folder", schema=None) as batch_op:
                    batch_op.create_foreign_key(
                        batch_op.f("fk_folder_workspace_id_workspace"), "workspace", ["workspace_id"], ["id"]
                    )
            else:
                print("[RBAC Migration] folder.workspace_id setup is complete (nullable with FK), skipping")
        else:
            print("[RBAC Migration] workspace_id column doesn't exist in folder table, skipping foreign key setup")


def downgrade() -> None:
    """Drop all RBAC tables and columns (reverse migration)."""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    existing_tables = inspector.get_table_names()

    # Drop foreign keys and columns from modified tables
    with op.batch_alter_table("flow", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_flow_environment_id_environment"), type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_flow_environment_id"))
        batch_op.drop_column("environment_id")

    with op.batch_alter_table("folder", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_folder_workspace_id_workspace"), type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_folder_workspace_id"))
        batch_op.drop_column("workspace_id")

    with op.batch_alter_table("api_key", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_api_key_workspace_id_workspace"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_api_key_service_account_id_service_account"), type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_api_key_workspace_id"))
        batch_op.drop_index(batch_op.f("ix_api_key_service_account_id"))
        batch_op.drop_index(batch_op.f("ix_api_key_scope_id"))
        batch_op.drop_column("service_account_id")
        batch_op.drop_column("scoped_permissions")
        batch_op.drop_column("scope_id")
        batch_op.drop_column("scope_type")
        batch_op.drop_column("workspace_id")

    # Drop RBAC tables in reverse dependency order
    if "sso_integration" in existing_tables:
        op.drop_index(op.f("ix_sso_integration_name"), table_name="sso_integration")
        op.drop_index(op.f("ix_sso_integration_created_by_user_id"), table_name="sso_integration")
        op.drop_table("sso_integration")

    if "audit_log" in existing_tables:
        op.drop_index(op.f("ix_audit_log_resource_id"), table_name="audit_log")
        op.drop_index(op.f("ix_audit_log_event_type"), table_name="audit_log")
        op.drop_index(op.f("ix_audit_log_actor_id"), table_name="audit_log")
        op.drop_table("audit_log")

    if "invitation" in existing_tables:
        op.drop_index(op.f("ix_invitation_workspace_id"), table_name="invitation")
        op.drop_index(op.f("ix_invitation_token"), table_name="invitation")
        op.drop_index(op.f("ix_invitation_status"), table_name="invitation")
        op.drop_index(op.f("ix_invitation_email"), table_name="invitation")
        op.drop_table("invitation")

    if "environment" in existing_tables:
        op.drop_index(op.f("ix_environment_project_id"), table_name="environment")
        op.drop_index(op.f("ix_environment_environment_type"), table_name="environment")
        op.drop_table("environment")

    if "role_assignment" in existing_tables:
        op.drop_index(op.f("ix_role_assignment_user_id"), table_name="role_assignment")
        op.drop_index(op.f("ix_role_assignment_service_account_id"), table_name="role_assignment")
        op.drop_index("ix_role_assignment_scope", table_name="role_assignment")
        op.drop_index(op.f("ix_role_assignment_scope_id"), table_name="role_assignment")
        op.drop_index(op.f("ix_role_assignment_role_id"), table_name="role_assignment")
        op.drop_index(op.f("ix_role_assignment_group_id"), table_name="role_assignment")
        op.drop_index(op.f("ix_role_assignment_assignee_type"), table_name="role_assignment")
        op.drop_table("role_assignment")

    if "service_account" in existing_tables:
        op.drop_index(op.f("ix_service_account_name"), table_name="service_account")
        op.drop_index(op.f("ix_service_account_created_by_user_id"), table_name="service_account")
        op.drop_table("service_account")

    if "role_permission" in existing_tables:
        op.drop_table("role_permission")

    if "permission" in existing_tables:
        op.drop_index(op.f("ix_permission_resource_type"), table_name="permission")
        op.drop_table("permission")

    if "role" in existing_tables:
        op.drop_index(op.f("ix_role_name"), table_name="role")
        op.drop_index(op.f("ix_role_is_system_role"), table_name="role")
        op.drop_table("role")

    if "user_group_member" in existing_tables:
        op.drop_index(op.f("ix_user_group_member_user_id"), table_name="user_group_member")
        op.drop_index(op.f("ix_user_group_member_group_id"), table_name="user_group_member")
        op.drop_table("user_group_member")

    if "user_group" in existing_tables:
        op.drop_index(op.f("ix_user_group_workspace_id"), table_name="user_group")
        op.drop_index(op.f("ix_user_group_name"), table_name="user_group")
        op.drop_index(op.f("ix_user_group_external_id"), table_name="user_group")
        op.drop_table("user_group")

    if "workspace_member" in existing_tables:
        op.drop_index(op.f("ix_workspace_member_workspace_id"), table_name="workspace_member")
        op.drop_index(op.f("ix_workspace_member_user_id"), table_name="workspace_member")
        op.drop_table("workspace_member")

    if "workspace" in existing_tables:
        op.drop_index(op.f("ix_workspace_name"), table_name="workspace")
        op.drop_table("workspace")
