"""RBAC (Role-Based Access Control) database models.

This module implements the core RBAC data model for LangBuilder, providing:
- Role: Predefined roles (Admin, Owner, Editor, Viewer) with permission sets
- Permission: Base CRUD permissions applicable to Flow and Project scopes
- RolePermission: Junction table mapping roles to their permissions
- UserRoleAssignment: Assigns roles to users for specific scopes with inheritance support

The RBAC system supports:
- Four predefined roles with distinct permission sets
- Permission inheritance from Project to Flow (with override capability)
- Immutable assignments (e.g., Default Project Owner)
- Global, Project, and Flow scope assignments
"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, Index, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from langbuilder.services.database.models.user.model import User


class RoleEnum(str, Enum):
    """Enumeration of predefined roles in the RBAC system.

    Roles define permission sets that can be assigned to users:
    - Admin: Global administrative access to all resources and RBAC management
    - Owner: Full CRUD permissions on assigned scope
    - Editor: Create, Read, Update permissions (no Delete)
    - Viewer: Read-only access and flow execution capability
    """

    ADMIN = "Admin"
    OWNER = "Owner"
    EDITOR = "Editor"
    VIEWER = "Viewer"


class PermissionEnum(str, Enum):
    """Enumeration of base CRUD permissions.

    Permissions represent atomic actions:
    - CREATE: Create new entities (flows, projects)
    - READ: View entities and execute flows
    - UPDATE: Modify existing entities and import flows
    - DELETE: Remove entities
    """

    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class ScopeTypeEnum(str, Enum):
    """Enumeration of permission scope types.

    Scopes define the level at which roles are assigned:
    - GLOBAL: System-wide access (Admin role only)
    - PROJECT: Project-level access (inherited by contained flows)
    - FLOW: Flow-level access (overrides inherited project permissions)
    """

    GLOBAL = "GLOBAL"
    PROJECT = "PROJECT"
    FLOW = "FLOW"


class Role(SQLModel, table=True):  # type: ignore[call-arg]
    """Role entity representing predefined roles in the RBAC system.

    Roles are immutable system entities that define permission sets.
    MVP includes 4 roles: Admin (global), Owner (CRUD), Editor (CRU), Viewer (R).

    Attributes:
        id: Unique identifier for the role
        name: Role name (Admin, Owner, Editor, Viewer)
        description: Human-readable description of role capabilities
        role_permissions: List of permissions granted to this role
        assignments: List of user assignments for this role
    """

    __tablename__ = "role"  # type: ignore[assignment]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: RoleEnum = Field(sa_column=Column(SQLEnum(RoleEnum), unique=True, nullable=False, index=True))
    description: str = Field(sa_column=Column(Text))

    # Relationships
    role_permissions: list["RolePermission"] = Relationship(back_populates="role")
    assignments: list["UserRoleAssignment"] = Relationship(back_populates="role")


class Permission(SQLModel, table=True):  # type: ignore[call-arg]
    """Permission entity representing base CRUD actions.

    Permissions are atomic actions (CRUD) that can be granted to roles.
    Each permission is unique by name.

    Attributes:
        id: Unique identifier for the permission
        name: Permission name (CREATE, READ, UPDATE, DELETE)
        description: Human-readable description of permission
        role_permissions: List of role mappings for this permission
    """

    __tablename__ = "permission"  # type: ignore[assignment]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: PermissionEnum = Field(sa_column=Column(SQLEnum(PermissionEnum), unique=True, nullable=False, index=True))
    description: str = Field(sa_column=Column(Text))

    # Relationships
    role_permissions: list["RolePermission"] = Relationship(back_populates="permission")


class RolePermission(SQLModel, table=True):  # type: ignore[call-arg]
    """Junction table mapping roles to their permissions.

    Defines which permissions each role has:
    - Admin: All permissions (CRUD)
    - Owner: All permissions (CRUD)
    - Editor: Create, Read, Update (no Delete)
    - Viewer: Read only

    Attributes:
        id: Unique identifier
        role_id: Foreign key to Role
        permission_id: Foreign key to Permission
        role: Role entity relationship
        permission: Permission entity relationship
    """

    __tablename__ = "rolepermission"  # type: ignore[assignment]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    role_id: UUID = Field(foreign_key="role.id", index=True)
    permission_id: UUID = Field(foreign_key="permission.id", index=True)

    # Relationships
    role: Role = Relationship(back_populates="role_permissions")
    permission: Permission = Relationship(back_populates="role_permissions")

    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="unique_role_permission"),)


class UserRoleAssignment(SQLModel, table=True):  # type: ignore[call-arg]
    """User role assignment with scope-based permissions.

    Assigns a role to a user for a specific scope (global, project, or flow).
    Supports permission inheritance: project roles are inherited by flows unless overridden.

    Key features:
    - Admin role uses GLOBAL scope (scope_id is NULL)
    - Project roles are inherited by flows within that project
    - Flow roles override inherited project roles
    - Default Project Owner assignments are immutable (is_immutable=True)

    Attributes:
        id: Unique identifier
        user_id: Foreign key to User
        role_id: Foreign key to Role
        scope_type: Scope level (GLOBAL, PROJECT, FLOW)
        scope_id: ID of project or flow (NULL for GLOBAL)
        is_immutable: True if assignment cannot be modified/deleted (Default Project Owner)
        created_at: Assignment creation timestamp
        user: User entity relationship
        role: Role entity relationship
    """

    __tablename__ = "userroleassignment"  # type: ignore[assignment]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    role_id: UUID = Field(foreign_key="role.id", index=True)
    scope_type: ScopeTypeEnum = Field(sa_column=Column(SQLEnum(ScopeTypeEnum), index=True, nullable=False))
    scope_id: UUID | None = Field(default=None, index=True, nullable=True)
    is_immutable: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    user: "User" = Relationship(back_populates="role_assignments")
    role: Role = Relationship(back_populates="assignments")

    __table_args__ = (
        UniqueConstraint("user_id", "scope_type", "scope_id", name="unique_user_scope"),
        Index("ix_user_scope", "user_id", "scope_type", "scope_id"),
    )


# Pydantic models for API schemas


class RoleRead(SQLModel):
    """Schema for reading Role entities."""

    id: UUID
    name: RoleEnum
    description: str


class PermissionRead(SQLModel):
    """Schema for reading Permission entities."""

    id: UUID
    name: PermissionEnum
    description: str


class RolePermissionRead(SQLModel):
    """Schema for reading RolePermission mappings."""

    id: UUID
    role_id: UUID
    permission_id: UUID


class UserRoleAssignmentCreate(SQLModel):
    """Schema for creating UserRoleAssignment entities."""

    user_id: UUID
    role_id: UUID
    scope_type: ScopeTypeEnum
    scope_id: UUID | None = None


class UserRoleAssignmentRead(SQLModel):
    """Schema for reading UserRoleAssignment entities."""

    id: UUID
    user_id: UUID
    role_id: UUID
    scope_type: ScopeTypeEnum
    scope_id: UUID | None
    is_immutable: bool
    created_at: datetime


class UserRoleAssignmentUpdate(SQLModel):
    """Schema for updating UserRoleAssignment entities."""

    role_id: UUID | None = None
