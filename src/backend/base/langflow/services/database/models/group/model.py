"""
Group and GroupMembership models for RBAC
Groups allow assigning roles to multiple users at once
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Group(SQLModel, table=True):
    """
    Group model for organizing users
    Enables group-based role assignment
    """

    __tablename__ = "groups"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str | None = None
    organization_id: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GroupMembership(SQLModel, table=True):
    """
    Links users to groups
    A user can be in multiple groups
    """

    __tablename__ = "group_memberships"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    group_id: UUID = Field(foreign_key="groups.id", index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
