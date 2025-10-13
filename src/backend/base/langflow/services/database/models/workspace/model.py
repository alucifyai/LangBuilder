"""Workspace and WorkspaceMember models for multi-tenancy."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.folder.model import Folder
    from langflow.services.database.models.user.model import User


class Workspace(SQLModel, table=True):  # type: ignore[call-arg]
    """Workspace model for multi-tenant isolation.

    Represents the top-level organizational unit in the system.
    All projects (folders) belong to a workspace.
    """

    __tablename__ = "workspace"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    name: str = Field(max_length=255, nullable=False, index=True)
    slug: str = Field(max_length=255, unique=True, nullable=False, index=True)  # URL-safe identifier
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = Field(default=True, nullable=False)

    # Audit fields
    created_by: UUID = Field(foreign_key="user.id", nullable=False, index=True)  # User who created the workspace
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    # Settings (RBAC config, SSO config, etc.)
    settings: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, default=dict, nullable=False))

    # Relationships
    members: list["WorkspaceMember"] = Relationship(
        back_populates="workspace",
        sa_relationship_kwargs={"cascade": "delete"},
    )
    projects: list["Folder"] = Relationship(back_populates="workspace")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format (lowercase, alphanumeric, hyphen)."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Slug must contain only alphanumeric characters, hyphens, and underscores")
        if not v.islower():
            raise ValueError("Slug must be lowercase")
        return v


class WorkspaceMember(SQLModel, table=True):  # type: ignore[call-arg]
    """Workspace membership junction table.

    Links users to workspaces with role information (owner, admin, member).
    """

    __tablename__ = "workspace_member"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    workspace_id: UUID = Field(foreign_key="workspace.id", nullable=False, index=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False, index=True)
    role: str = Field(default="member", max_length=50, nullable=False)  # owner, admin, member
    is_active: bool = Field(default=True, nullable=False)

    # Audit fields
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    workspace: "Workspace" = Relationship(back_populates="members")
    user: "User" = Relationship(back_populates="workspace_memberships")

    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),)


class WorkspaceRead(SQLModel):
    """Schema for reading workspace data."""

    id: UUID
    name: str
    slug: str
    description: str | None
    is_active: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    settings: dict[str, Any]


class WorkspaceCreate(SQLModel):
    """Schema for creating a new workspace."""

    name: str = Field(max_length=255, min_length=1)
    slug: str | None = Field(default=None, max_length=255)  # Optional - auto-generated from name if not provided
    description: str | None = Field(default=None, max_length=1000)
    settings: dict[str, Any] | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None) -> str | None:
        """Validate slug format."""
        if v is None:
            return v
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Slug must contain only alphanumeric characters, hyphens, and underscores")
        if not v.islower():
            raise ValueError("Slug must be lowercase")
        return v


class WorkspaceUpdate(SQLModel):
    """Schema for updating a workspace."""

    name: str | None = Field(default=None, max_length=255, min_length=1)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None
    settings: dict[str, Any] | None = None


class WorkspaceMemberRead(SQLModel):
    """Schema for reading workspace member data."""

    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: str
    is_active: bool
    joined_at: datetime


class WorkspaceMemberCreate(SQLModel):
    """Schema for creating a new workspace member."""

    user_id: UUID
    role: str = Field(default="member")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is one of the allowed values."""
        allowed = {"owner", "admin", "member"}
        if v not in allowed:
            msg = f"role must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return v


class WorkspaceInvite(SQLModel):
    """Schema for inviting a user to a workspace via email.

    Used by POST /api/v1/workspaces/{id}/members endpoint.
    Creates an Invitation record that the user must accept.
    """

    email: str = Field(max_length=255, min_length=3, description="Email address of user to invite")
    role_id: UUID | None = Field(default=None, description="Optional role to assign upon acceptance")
    message: str | None = Field(default=None, max_length=1000, description="Optional invitation message")
