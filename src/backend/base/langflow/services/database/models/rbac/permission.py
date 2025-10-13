"""Permission model for RBAC system."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.role_permission import RolePermission


class Permission(SQLModel, table=True):  # type: ignore[call-arg]
    """Permission model for RBAC.

    Represents a specific permission that can be granted to roles.
    Permissions are defined by resource_type (e.g., "flow", "project") and action (e.g., "create", "read").
    """

    __tablename__ = "permission"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)

    # Permission identifier: "resource_type.action" (e.g., "flow.create", "project.delete")
    name: str = Field(max_length=200, nullable=False, index=True, unique=True)
    resource_type: str = Field(max_length=100, nullable=False, index=True)
    action: str = Field(max_length=100, nullable=False, index=True)

    # Human-readable description
    display_name: str = Field(max_length=255, nullable=False)
    description: str | None = Field(default=None, max_length=1000)

    # Scope level: GLOBAL, WORKSPACE, PROJECT, ENVIRONMENT, FLOW, COMPONENT
    scope_level: str = Field(max_length=50, nullable=False, index=True)

    # Permission status and type
    is_active: bool = Field(default=True, nullable=False)
    is_system_permission: bool = Field(default=False, nullable=False, index=True)

    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    role_permissions: list["RolePermission"] = Relationship(
        back_populates="permission",
        sa_relationship_kwargs={"cascade": "delete"},
    )

    __table_args__ = (UniqueConstraint("resource_type", "action", name="uq_permission_resource_action"),)


class PermissionRead(SQLModel):
    """Schema for reading permission data."""

    id: UUID
    name: str
    resource_type: str
    action: str
    display_name: str
    description: str | None
    scope_level: str
    is_active: bool
    is_system_permission: bool
    created_at: datetime


class PermissionCreate(SQLModel):
    """Schema for creating a new permission."""

    name: str = Field(max_length=200, min_length=1)
    resource_type: str = Field(max_length=100, min_length=1)
    action: str = Field(max_length=100, min_length=1)
    display_name: str = Field(max_length=255, min_length=1)
    description: str | None = Field(default=None, max_length=1000)
    scope_level: str = Field(max_length=50, min_length=1)
    is_system_permission: bool = Field(default=False)
