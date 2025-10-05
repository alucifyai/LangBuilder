"""Role model for RBAC system.

Implements Story 1.2 - Create and Manage Custom Roles from PRD.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.grant import Grant


def utc_now():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class RoleBase(SQLModel):
    """Base role model."""

    name: str = Field(index=True, unique=True, description="Unique role name (e.g., 'Deployer', 'Editor')")
    description: str | None = Field(default=None, description="Human-readable description of the role")
    permissions: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="List of permission IDs (e.g., ['flow:read', 'flow:export_flow'])",
    )
    is_system_role: bool = Field(
        default=False, description="System-defined roles cannot be deleted (e.g., 'Admin', 'Viewer')"
    )


class Role(RoleBase, table=True):  # type: ignore[call-arg]
    """Role definition table.

    Roles are collections of permissions that can be assigned to users/groups.

    PRD Story 1.2:
    - @AC1: Create custom roles with specific permissions
    - @AC2: Role names must be unique
    - @AC3: Track role versions (via updated_at timestamp)
    """

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
    version: int = Field(default=1, description="Role version number (incremented on updates)")

    # Relationships
    grants: list["Grant"] = Relationship(
        back_populates="role",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    __table_args__ = (UniqueConstraint("name", name="unique_role_name"),)


class RoleCreate(RoleBase):
    """Schema for creating a new role."""

    pass


class RoleRead(RoleBase):
    """Schema for reading role data in API responses."""

    id: UUIDstr
    created_at: datetime
    updated_at: datetime
    version: int


class RoleUpdate(SQLModel):
    """Schema for updating an existing role.

    PRD Story 1.2 @AC3: When permissions are modified, increment version
    and log the change to audit log.
    """

    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None


# System-defined roles (cannot be deleted)
SYSTEM_ROLES: list[dict] = [
    {
        "name": "Admin",
        "description": "Full system access",
        "permissions": [
            # All workspace permissions
            "workspace:create",
            "workspace:read",
            "workspace:update",
            "workspace:delete",
            "workspace:invite_users",
            # All project permissions
            "project:create",
            "project:read",
            "project:update",
            "project:delete",
            # All environment permissions
            "environment:create",
            "environment:read",
            "environment:update",
            "environment:delete",
            "environment:deploy_environment",
            # All flow permissions
            "flow:create",
            "flow:read",
            "flow:update",
            "flow:delete",
            "flow:export_flow",
            # All component permissions
            "component:create",
            "component:read",
            "component:update",
            "component:delete",
            "component:modify_component_settings",
            # All user permissions
            "user:create",
            "user:read",
            "user:update",
            "user:delete",
            "user:invite_users",
            # All API key permissions
            "apikey:create",
            "apikey:read",
            "apikey:update",
            "apikey:delete",
            "apikey:manage_tokens",
        ],
        "is_system_role": True,
    },
    {
        "name": "Editor",
        "description": "Can create and edit flows and components",
        "permissions": [
            "workspace:read",
            "project:create",
            "project:read",
            "project:update",
            "environment:read",
            "flow:create",
            "flow:read",
            "flow:update",
            "flow:delete",
            "component:create",
            "component:read",
            "component:update",
            "component:modify_component_settings",
        ],
        "is_system_role": True,
    },
    {
        "name": "Viewer",
        "description": "Read-only access",
        "permissions": [
            "workspace:read",
            "project:read",
            "environment:read",
            "flow:read",
            "component:read",
            "user:read",
        ],
        "is_system_role": True,
    },
    {
        "name": "Deployer",
        "description": "Can deploy to environments",
        "permissions": [
            "workspace:read",
            "project:read",
            "environment:read",
            "environment:deploy_environment",
            "flow:read",
        ],
        "is_system_role": True,
    },
]
