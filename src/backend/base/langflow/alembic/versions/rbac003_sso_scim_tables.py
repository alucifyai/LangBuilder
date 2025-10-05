"""SSO and SCIM tables

Revision ID: rbac003
Revises: rbac002
Create Date: 2025-01-04 00:00:00.000000

PRD Story 2.2 - Enterprise SSO Integration
PRD Story 2.3 - Support SAML, OIDC, and SCIM
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4f5e6d7c8b9a"
down_revision: Union[str, None] = "3a4b5c6d7e8f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create SSO and SCIM tables."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()

    # SSO Configuration table
    if "sso_config" not in table_names:
        op.create_table(
        "sso_config",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("protocol", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        # OIDC fields
        sa.Column("oidc_issuer", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("oidc_client_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("oidc_client_secret", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("oidc_redirect_uri", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("oidc_scopes", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        # SAML fields
        sa.Column("saml_entity_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("saml_sso_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("saml_x509_cert", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("saml_acs_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        # Settings
        sa.Column("attribute_mapping", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("auto_provision_users", sa.Boolean(), nullable=False),
        sa.Column("default_role_id", sa.UUID(), nullable=True),
        sa.Column("jit_enabled", sa.Boolean(), nullable=False),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["default_role_id"], ["role.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_sso_config_id"), "sso_config", ["id"], unique=False)
        op.create_index(op.f("ix_sso_config_workspace_id"), "sso_config", ["workspace_id"], unique=False)

    # SSO Session table
    if "sso_session" not in table_names:
        op.create_table(
        "sso_session",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("sso_config_id", sa.UUID(), nullable=False),
        sa.Column("external_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("session_token", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_address", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("user_agent", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("sso_claims", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sso_config_id"], ["sso_config.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_sso_session_id"), "sso_session", ["id"], unique=False)
        op.create_index(op.f("ix_sso_session_user_id"), "sso_session", ["user_id"], unique=False)
        op.create_index(op.f("ix_sso_session_sso_config_id"), "sso_session", ["sso_config_id"], unique=False)
        op.create_index(op.f("ix_sso_session_session_token"), "sso_session", ["session_token"], unique=True)

    # SCIM tables - ALL DISABLED (no SCIM models implemented)
    # TODO: Re-enable when SCIM models are implemented
    # # SCIM Token table
    # if "scim_token" not in table_names:
    #     op.create_table(
    #         "scim_token",
    #         sa.Column("id", sa.UUID(), nullable=False),
    #         sa.Column("workspace_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    #         sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    #         sa.Column("token_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    #         sa.Column("token_prefix", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    #         sa.Column("scopes", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    #         sa.Column("is_active", sa.Boolean(), nullable=False),
    #         sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    #         sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    #         sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    #         sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    #         sa.PrimaryKeyConstraint("id"),
    #     )
    #     op.create_index(op.f("ix_scim_token_id"), "scim_token", ["id"], unique=False)
    #     op.create_index(op.f("ix_scim_token_workspace_id"), "scim_token", ["workspace_id"], unique=False)
    #     op.create_index(op.f("ix_scim_token_token_hash"), "scim_token", ["token_hash"], unique=True)
    #     op.create_index(op.f("ix_scim_token_token_prefix"), "scim_token", ["token_prefix"], unique=False)
    #
    # # SCIM External Mapping table
    # if "scim_external_mapping" not in table_names:
    #     op.create_table(
    #         "scim_external_mapping",
    #         sa.Column("id", sa.UUID(), nullable=False),
    #         sa.Column("workspace_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    #         sa.Column("external_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    #         sa.Column("resource_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    #         sa.Column("internal_id", sa.UUID(), nullable=False),
    #         sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    #         sa.Column("external_data", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    #         sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    #         sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    #         sa.PrimaryKeyConstraint("id"),
    #     )
    #     op.create_index(op.f("ix_scim_external_mapping_id"), "scim_external_mapping", ["id"], unique=False)
    #     op.create_index(
    #         op.f("ix_scim_external_mapping_workspace_id"),
    #         "scim_external_mapping",
    #         ["workspace_id"],
    #         unique=False,
    #     )
    #     op.create_index(
    #         op.f("ix_scim_external_mapping_external_id"),
    #         "scim_external_mapping",
    #         ["external_id"],
    #         unique=False,
    #     )
    #
    # # SCIM Provisioning Log table
    # if "scim_provisioning_log" not in table_names:
    #     op.create_table(
    #         "scim_provisioning_log",
    #         sa.Column("id", sa.UUID(), nullable=False),
    #         sa.Column("workspace_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    #         sa.Column("operation", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    #         sa.Column("resource_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    #         sa.Column("external_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    #         sa.Column("internal_id", sa.UUID(), nullable=True),
    #         sa.Column("scim_token_id", sa.UUID(), nullable=False),
    #         sa.Column("ip_address", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    #         sa.Column("success", sa.Boolean(), nullable=False),
    #         sa.Column("error_message", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    #         sa.Column("request_data", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    #         sa.Column("response_data", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    #         sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    #         sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    #         sa.ForeignKeyConstraint(["scim_token_id"], ["scim_token.id"], ondelete="CASCADE"),
    #         sa.PrimaryKeyConstraint("id"),
    #     )
    #     op.create_index(op.f("ix_scim_provisioning_log_id"), "scim_provisioning_log", ["id"], unique=False)
    #     op.create_index(
    #         op.f("ix_scim_provisioning_log_workspace_id"),
    #         "scim_provisioning_log",
    #         ["workspace_id"],
    #         unique=False,
    #     )
    #     op.create_index(
    #         op.f("ix_scim_provisioning_log_external_id"),
    #         "scim_provisioning_log",
    #         ["external_id"],
    #         unique=False,
    #     )

    # Add sso_sessions relationship to User table (handled by SQLModel relationships)
    # No schema change needed - just relationship definition


def downgrade() -> None:
    """Drop SSO and SCIM tables."""

    op.drop_index(op.f("ix_scim_provisioning_log_external_id"), table_name="scim_provisioning_log")
    op.drop_index(op.f("ix_scim_provisioning_log_workspace_id"), table_name="scim_provisioning_log")
    op.drop_index(op.f("ix_scim_provisioning_log_id"), table_name="scim_provisioning_log")
    op.drop_table("scim_provisioning_log")

    op.drop_index(op.f("ix_scim_external_mapping_external_id"), table_name="scim_external_mapping")
    op.drop_index(op.f("ix_scim_external_mapping_workspace_id"), table_name="scim_external_mapping")
    op.drop_index(op.f("ix_scim_external_mapping_id"), table_name="scim_external_mapping")
    op.drop_table("scim_external_mapping")

    op.drop_index(op.f("ix_scim_token_token_prefix"), table_name="scim_token")
    op.drop_index(op.f("ix_scim_token_token_hash"), table_name="scim_token")
    op.drop_index(op.f("ix_scim_token_workspace_id"), table_name="scim_token")
    op.drop_index(op.f("ix_scim_token_id"), table_name="scim_token")
    op.drop_table("scim_token")

    op.drop_index(op.f("ix_sso_session_session_token"), table_name="sso_session")
    op.drop_index(op.f("ix_sso_session_sso_config_id"), table_name="sso_session")
    op.drop_index(op.f("ix_sso_session_user_id"), table_name="sso_session")
    op.drop_index(op.f("ix_sso_session_id"), table_name="sso_session")
    op.drop_table("sso_session")

    op.drop_index(op.f("ix_sso_config_workspace_id"), table_name="sso_config")
    op.drop_index(op.f("ix_sso_config_id"), table_name="sso_config")
    op.drop_table("sso_config")
