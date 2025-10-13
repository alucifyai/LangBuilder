"""ServiceAccount model for RBAC system."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.api_key.model import ApiKey
    from langflow.services.database.models.rbac.role_assignment import RoleAssignment


class ServiceAccount(SQLModel, table=True):  # type: ignore[call-arg]
    """Service account model for programmatic access.

    Service accounts are non-human identities used for programmatic access to the system.
    They can be assigned roles just like users and can have scoped API tokens.
    """

    __tablename__ = "service_account"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    name: str = Field(max_length=255, nullable=False, index=True, unique=True)
    display_name: str = Field(max_length=255, nullable=False)
    description: str | None = Field(default=None, max_length=1000)

    # Workspace scoping (multi-tenancy)
    workspace_id: UUID = Field(foreign_key="workspace.id", nullable=False, index=True)

    # Service account status
    is_active: bool = Field(default=True, nullable=False)

    # Audit fields
    created_by_user_id: UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    role_assignments: list["RoleAssignment"] = Relationship(
        back_populates="service_account",
        sa_relationship_kwargs={"cascade": "delete"},
    )
    api_keys: list["ApiKey"] = Relationship(
        back_populates="service_account",
        sa_relationship_kwargs={"cascade": "delete"},
    )


class ServiceAccountRead(SQLModel):
    """Schema for reading service account data."""

    id: UUID
    name: str
    display_name: str
    description: str | None
    workspace_id: UUID
    is_active: bool
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class ServiceAccountCreate(SQLModel):
    """Schema for creating a new service account."""

    name: str = Field(max_length=255, min_length=3)
    display_name: str = Field(max_length=255, min_length=1)
    description: str | None = Field(default=None, max_length=1000)
    workspace_id: UUID


class ServiceAccountUpdate(SQLModel):
    """Schema for updating a service account."""

    display_name: str | None = Field(default=None, max_length=255, min_length=1)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None
