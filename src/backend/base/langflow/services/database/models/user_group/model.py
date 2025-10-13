"""UserGroup and UserGroupMember models for group-based RBAC."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.role_assignment import RoleAssignment
    from langflow.services.database.models.user.model import User
    from langflow.services.database.models.workspace.model import Workspace


class UserGroup(SQLModel, table=True):  # type: ignore[call-arg]
    """User group model for batch role assignments.

    Groups allow assigning roles to multiple users at once.
    When a user is added to a group, they inherit all role assignments of that group.
    """

    __tablename__ = "user_group"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    workspace_id: UUID = Field(foreign_key="workspace.id", nullable=False, index=True)
    name: str = Field(max_length=255, nullable=False, index=True)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = Field(default=True, nullable=False)

    # SCIM integration fields
    external_id: str | None = Field(default=None, max_length=255, index=True)  # IdP group ID
    scim_synced: bool = Field(default=False, nullable=False)

    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    workspace: "Workspace" = Relationship()
    members: list["UserGroupMember"] = Relationship(
        back_populates="group",
        sa_relationship_kwargs={"cascade": "delete"},
    )
    role_assignments: list["RoleAssignment"] = Relationship(
        back_populates="group",
        sa_relationship_kwargs={"cascade": "delete"},
    )

    __table_args__ = (UniqueConstraint("workspace_id", "name", name="uq_workspace_group_name"),)


class UserGroupMember(SQLModel, table=True):  # type: ignore[call-arg]
    """User group membership junction table.

    Links users to groups within a workspace.
    """

    __tablename__ = "user_group_member"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    group_id: UUID = Field(foreign_key="user_group.id", nullable=False, index=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False, index=True)
    is_active: bool = Field(default=True, nullable=False)

    # Audit fields
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    group: "UserGroup" = Relationship(back_populates="members")
    user: "User" = Relationship(back_populates="group_memberships")

    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_user"),)


class UserGroupRead(SQLModel):
    """Schema for reading user group data."""

    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    is_active: bool
    external_id: str | None
    scim_synced: bool
    created_at: datetime
    updated_at: datetime


class UserGroupCreate(SQLModel):
    """Schema for creating a new user group."""

    workspace_id: UUID
    name: str = Field(max_length=255, min_length=1)
    description: str | None = Field(default=None, max_length=1000)
    external_id: str | None = Field(default=None, max_length=255)
    scim_synced: bool | None = Field(default=None)


class UserGroupUpdate(SQLModel):
    """Schema for updating a user group."""

    name: str | None = Field(default=None, max_length=255, min_length=1)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None


class UserGroupMemberRead(SQLModel):
    """Schema for reading user group member data."""

    id: UUID
    group_id: UUID
    user_id: UUID
    is_active: bool
    joined_at: datetime


class UserGroupMemberCreate(SQLModel):
    """Schema for creating a new user group member."""

    user_id: UUID


class UserGroupMemberCreateByIdentifier(SQLModel):
    """Schema for creating a new user group member by username or user_id.

    Supports both user ID (UUID) and username as identifier.
    This provides flexibility for API clients and aligns with PRD requirements.
    """

    user_identifier: str = Field(description="User ID (UUID) or username")
