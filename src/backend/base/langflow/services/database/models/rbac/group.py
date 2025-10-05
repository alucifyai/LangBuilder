"""Group model for RBAC system.

Implements Story 2.1 - Assign Roles to Users and Groups and
Story 2.3 - Provision Users and Groups via SSO/SCIM from PRD.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import JSON, Column, ForeignKey, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, Relationship, SQLModel

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.grant import Grant
    from langflow.services.database.models.user.model import User


def utc_now():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


# Association table for many-to-many relationship between User and Group
user_group_association = Table(
    "user_group",
    SQLModel.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True),
    Column("group_id", UUID(as_uuid=True), ForeignKey("group.id"), primary_key=True),
)


class GroupBase(SQLModel):
    """Base group model."""

    name: str = Field(index=True, unique=True, description="Unique group name (e.g., 'Data Team', 'Platform')")
    description: str | None = Field(default=None, description="Human-readable description of the group")
    external_id: str | None = Field(
        default=None,
        index=True,
        nullable=True,
        description="External IdP group ID for SCIM synchronization",
    )
    metadata_: dict | None = Field(
        default=None,
        sa_column=Column("metadata", JSON),
        description="Additional metadata (e.g., IdP attributes)",
    )


class Group(GroupBase, table=True):  # type: ignore[call-arg]
    """Group table for organizing users.

    Groups can be assigned roles, and all group members inherit those roles.

    PRD Story 2.1 @AC1: Assign role to group within scope
    PRD Story 2.3 @AC3: Group membership drives roles
    """

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)

    # Relationships
    members: list["User"] = Relationship(
        back_populates="groups",
        link_model=user_group_association,
    )
    grants: list["Grant"] = Relationship(
        back_populates="group",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    __table_args__ = (UniqueConstraint("name", name="unique_group_name"),)


class GroupCreate(GroupBase):
    """Schema for creating a new group."""

    member_ids: list[UUIDstr] | None = Field(
        default=None, description="Initial list of user IDs to add to group"
    )


class GroupRead(GroupBase):
    """Schema for reading group data in API responses."""

    id: UUIDstr
    created_at: datetime
    updated_at: datetime
    member_count: int | None = Field(default=None, description="Number of members in the group")


class GroupUpdate(SQLModel):
    """Schema for updating an existing group."""

    name: str | None = None
    description: str | None = None
    external_id: str | None = None
    metadata_: dict | None = Field(default=None, alias="metadata")
    add_member_ids: list[UUIDstr] | None = Field(default=None, description="User IDs to add to the group")
    remove_member_ids: list[UUIDstr] | None = Field(default=None, description="User IDs to remove from the group")
