"""Role model for RBAC system."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.role_assignment import RoleAssignment
    from langflow.services.database.models.rbac.role_permission import RolePermission


class Role(SQLModel, table=True):  # type: ignore[call-arg]
    """Role model for RBAC.

    Represents a role that can be assigned to users, groups, or service accounts.
    Roles contain a set of permissions through the RolePermission junction table.
    """

    __tablename__ = "role"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    name: str = Field(max_length=255, nullable=False, index=True, unique=True)
    display_name: str = Field(max_length=255, nullable=False)
    description: str | None = Field(default=None, max_length=1000)

    # System roles cannot be modified or deleted
    is_system_role: bool = Field(default=False, nullable=False)

    # Role status
    is_active: bool = Field(default=True, nullable=False)

    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    created_by: UUID | None = Field(default=None, foreign_key="user.id")
    updated_by: UUID | None = Field(default=None, foreign_key="user.id")

    # Relationships
    role_permissions: list["RolePermission"] = Relationship(
        back_populates="role",
        sa_relationship_kwargs={"cascade": "delete"},
    )
    assignments: list["RoleAssignment"] = Relationship(
        back_populates="role",
        sa_relationship_kwargs={"cascade": "delete"},
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate role name format (lowercase, alphanumeric, underscore)."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Role name must contain only alphanumeric characters and underscores")
        if not v.islower():
            raise ValueError("Role name must be lowercase")
        return v


class RoleRead(SQLModel):
    """Schema for reading role data."""

    id: UUID
    name: str
    display_name: str
    description: str | None
    is_system_role: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    updated_by: UUID | None = None


class RoleCreate(SQLModel):
    """Schema for creating a new role."""

    name: str = Field(max_length=255, min_length=3)
    display_name: str = Field(max_length=255, min_length=1)
    description: str | None = Field(default=None, max_length=1000)
    permission_ids: list[UUID] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate role name format."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Role name must contain only alphanumeric characters and underscores")
        if not v.islower():
            raise ValueError("Role name must be lowercase")

        # Prevent creation of reserved system role names
        reserved_names = ["owner", "admin", "editor", "viewer", "service_account", "system", "superuser"]
        if v in reserved_names:
            raise ValueError(f"Role name '{v}' is reserved for system roles")

        return v


class RoleUpdate(SQLModel):
    """Schema for updating a role."""

    display_name: str | None = Field(default=None, max_length=255, min_length=1)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None
    permission_ids: list[UUID] | None = None
