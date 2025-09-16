from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, field_validator
from sqlalchemy import JSON, Column, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.project import Project
    from langflow.services.database.models.rbac.role import Role
    from langflow.services.database.models.rbac.role_assignment import RoleAssignment
    from langflow.services.database.models.rbac.audit_log import AuditLog
    from langflow.services.database.models.rbac.user_group import UserGroup
    from langflow.services.database.models.rbac.service_account import ServiceAccount
    from langflow.services.database.models.user.model import User


class WorkspaceSettings(BaseModel):
    """Workspace-specific settings and configurations."""

    sso_enabled: bool = False
    sso_provider: str | None = None
    scim_enabled: bool = False
    max_projects: int | None = None
    max_users: int | None = None
    allowed_domains: list[str] = []
    default_role_id: UUID | None = None
    session_timeout_minutes: int = 1440  # 24 hours default
    ip_allowlist: list[str] = []
    features_enabled: dict[str, bool] = {}
    compliance_settings: dict[str, Any] = {}


class WorkspaceBase(SQLModel):
    """Base workspace model for RBAC hierarchical organization."""

    name: str = Field(index=True, sa_column_kwargs={"unique": False})
    description: str | None = Field(default=None, sa_column=Column(Text))
    organization: str | None = Field(default=None, index=True)

    # Settings and metadata
    settings: dict | None = Field(default_factory=lambda: WorkspaceSettings().model_dump(), sa_column=Column(JSON))
    workspace_metadata: dict | None = Field(default={}, sa_column=Column(JSON))
    tags: list[str] | None = Field(default=[], sa_column=Column(JSON))

    # Status and lifecycle
    is_active: bool = Field(default=True, index=True)
    is_deleted: bool = Field(default=False)
    deletion_requested_at: datetime | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate workspace name is not empty and within length limits."""
        if not v or not v.strip():
            msg = "Workspace name cannot be empty"
            raise ValueError(msg)
        if len(v) > 255:
            msg = "Workspace name cannot exceed 255 characters"
            raise ValueError(msg)
        return v.strip()

    @field_validator("settings", mode="before")
    @classmethod
    def validate_settings(cls, v: dict | None) -> dict:
        """Validate and normalize workspace settings."""
        if v is None:
            return WorkspaceSettings().model_dump()
        # Validate settings structure
        if not isinstance(v, dict):
            msg = "Settings must be a dictionary"
            raise ValueError(msg)
        return v


class Workspace(WorkspaceBase, table=True):  # type: ignore[call-arg]
    """Workspace table for multi-tenant RBAC system."""

    __tablename__ = "workspace"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)

    # Owner relationship
    owner_id: UUIDstr = Field(foreign_key="user.id", index=True)
    owner: User = Relationship(back_populates="owned_workspaces")

    # Relationships
    projects: list[Project] = Relationship(
        back_populates="workspace",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    roles: list[Role] = Relationship(
        back_populates="workspace",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    role_assignments: list[RoleAssignment] = Relationship(
        back_populates="workspace",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    audit_logs: list[AuditLog] = Relationship(
        back_populates="workspace",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    user_groups: list[UserGroup] = Relationship(
        back_populates="workspace",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    service_accounts: list[ServiceAccount] = Relationship(
        back_populates="workspace",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    # Unique constraints
    __table_args__ = (UniqueConstraint("owner_id", "name", name="unique_workspace_name_per_owner"),)


class WorkspaceCreate(SQLModel):
    """Schema for creating a workspace."""

    name: str
    description: str | None = None
    organization: str | None = None
    settings: dict | None = Field(default=None, sa_column=Column(JSON))
    workspace_metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    tags: list[str] | None = None


class WorkspaceRead(WorkspaceBase):
    """Schema for reading workspace data."""

    id: UUID
    owner_id: UUID
    project_count: int | None = None
    user_count: int | None = None
    role_count: int | None = None


class WorkspaceUpdate(SQLModel):
    """Schema for updating workspace data."""

    name: str | None = None
    description: str | None = None
    organization: str | None = None
    settings: dict | None = Field(default=None, sa_column=Column(JSON))
    workspace_metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    tags: list[str] | None = None
    is_active: bool | None = None


class WorkspaceInvitation(SQLModel, table=True):  # type: ignore[call-arg]
    """Workspace invitation model for user onboarding."""

    __tablename__ = "workspace_invitation"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    workspace_id: UUIDstr = Field(foreign_key="workspace.id", index=True)
    email: str = Field(index=True)
    role_id: UUIDstr | None = Field(foreign_key="role.id")

    # Invitation details
    invited_by_id: UUIDstr = Field(foreign_key="user.id")
    invitation_code: str = Field(index=True, unique=True)
    expires_at: datetime = Field()

    # Status
    is_accepted: bool = Field(default=False)
    accepted_at: datetime | None = Field(default=None)
    accepted_by_id: UUIDstr | None = Field(foreign_key="user.id", default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    workspace: "Workspace" = Relationship()
    role: Optional["Role"] = Relationship()
    invited_by: "User" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[WorkspaceInvitation.invited_by_id]",
            "primaryjoin": "WorkspaceInvitation.invited_by_id == User.id"
        }
    )
    accepted_by: User | None = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[WorkspaceInvitation.accepted_by_id]",
            "primaryjoin": "WorkspaceInvitation.accepted_by_id == User.id"
        }
    )
