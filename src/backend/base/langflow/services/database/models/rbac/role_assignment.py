from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import JSON, Column, Index, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.workspace import Workspace
    from langflow.services.database.models.rbac.project import Project
    from langflow.services.database.models.rbac.environment import Environment
    from langflow.services.database.models.rbac.role import Role
    from langflow.services.database.models.rbac.user_group import UserGroup
    from langflow.services.database.models.user.model import User
    from langflow.services.database.models.flow.model import Flow


class AssignmentType(str, Enum):
    """Type of role assignment."""

    USER = "user"
    GROUP = "group"
    SERVICE_ACCOUNT = "service_account"
    API_TOKEN = "api_token"


class AssignmentScope(str, Enum):
    """Scope level for role assignment."""

    WORKSPACE = "workspace"
    PROJECT = "project"
    ENVIRONMENT = "environment"
    FLOW = "flow"
    COMPONENT = "component"


class RoleAssignmentBase(SQLModel):
    """Base model for role assignments."""

    # Assignment type and scope
    assignment_type: AssignmentType = Field(index=True)
    scope_type: AssignmentScope = Field(index=True)

    # Assignment metadata
    is_active: bool = Field(default=True, index=True)
    is_inherited: bool = Field(default=False)  # Inherited from parent scope

    # Temporal constraints
    valid_from: datetime | None = Field(default=None)
    valid_until: datetime | None = Field(default=None)

    # Conditions and restrictions
    conditions: dict | None = Field(default={}, sa_column=Column(JSON))
    ip_restrictions: list[str] | None = Field(default=[], sa_column=Column(JSON))
    time_restrictions: dict | None = Field(default={}, sa_column=Column(JSON))  # e.g., business hours only

    # Assignment details
    reason: str | None = Field(default=None, sa_column=Column(Text))
    approved_by_id: UUIDstr | None = Field(default=None)
    approval_date: datetime | None = Field(default=None)

    # Timestamps
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("valid_until")
    @classmethod
    def validate_valid_until(cls, v: datetime | None, values) -> datetime | None:
        if v is not None and "valid_from" in values:
            valid_from = values.get("valid_from")
            if valid_from and v <= valid_from:
                raise ValueError("valid_until must be after valid_from")
        return v


class RoleAssignment(RoleAssignmentBase, table=True):  # type: ignore[call-arg]
    """Role assignment table linking users/groups to roles with scope."""

    __tablename__ = "role_assignment"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)

    # Role relationship
    role_id: UUIDstr = Field(foreign_key="role.id", index=True)
    role: "Role" = Relationship(back_populates="role_assignments")

    # Assignee (user, group, or service account)
    user_id: UUIDstr | None = Field(foreign_key="user.id", index=True, nullable=True)
    group_id: UUIDstr | None = Field(foreign_key="user_group.id", index=True, nullable=True)
    service_account_id: UUIDstr | None = Field(foreign_key="service_account.id", index=True, nullable=True)

    # Scope relationships (hierarchical)
    workspace_id: UUIDstr | None = Field(foreign_key="workspace.id", index=True, nullable=True)
    project_id: UUIDstr | None = Field(foreign_key="project.id", index=True, nullable=True)
    environment_id: UUIDstr | None = Field(foreign_key="environment.id", index=True, nullable=True)
    flow_id: UUIDstr | None = Field(foreign_key="flow.id", index=True, nullable=True)
    component_id: UUIDstr | None = Field(default=None, index=True)  # Component doesn't have a table yet

    # Assignment tracking
    assigned_by_id: UUIDstr = Field(foreign_key="user.id")

    # Relationships
    user: User | None = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[RoleAssignment.user_id]",
            "primaryjoin": "RoleAssignment.user_id == User.id"
        }
    )
    group: UserGroup | None = Relationship(back_populates="role_assignments")
    workspace: Workspace | None = Relationship(back_populates="role_assignments")
    project: Project | None = Relationship(back_populates="role_assignments")
    environment: Environment | None = Relationship(back_populates="role_assignments")
    flow: Flow | None = Relationship(back_populates="role_assignments")

    assigned_by: "User" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[RoleAssignment.assigned_by_id]",
            "primaryjoin": "RoleAssignment.assigned_by_id == User.id"
        }
    )
    approved_by: User | None = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[RoleAssignment.approved_by_id]",
            "primaryjoin": "RoleAssignment.approved_by_id == User.id"
        }
    )

    # Indexes for performance
    __table_args__ = (
        # Unique constraint to prevent duplicate assignments
        UniqueConstraint(
            "role_id", "user_id", "workspace_id", "project_id",
            "environment_id", "flow_id", "component_id",
            name="unique_role_assignment"
        ),
        # Performance indexes
        Index("idx_user_workspace", "user_id", "workspace_id"),
        Index("idx_user_project", "user_id", "project_id"),
        Index("idx_group_workspace", "group_id", "workspace_id"),
        Index("idx_active_assignments", "is_active", "assignment_type"),
    )


class RoleAssignmentCreate(SQLModel):
    """Schema for creating a role assignment."""

    role_id: UUID
    assignment_type: AssignmentType
    scope_type: AssignmentScope

    # Assignee (one of these must be provided)
    user_id: UUID | None = None
    group_id: UUID | None = None
    service_account_id: UUID | None = None

    # Scope (based on scope_type)
    workspace_id: UUID | None = None
    project_id: UUID | None = None
    environment_id: UUID | None = None
    flow_id: UUID | None = None
    component_id: UUID | None = None

    # Optional fields
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    conditions: dict | None = Field(default=None, sa_column=Column(JSON))
    ip_restrictions: list[str] | None = None
    time_restrictions: dict | None = Field(default=None, sa_column=Column(JSON))
    reason: str | None = None

    @field_validator("user_id")
    @classmethod
    def validate_assignee(cls, v, values):
        # Ensure exactly one assignee type is provided
        assignees = [
            values.get("user_id"),
            values.get("group_id"),
            values.get("service_account_id")
        ]
        non_null = [a for a in assignees if a is not None]
        if len(non_null) != 1:
            raise ValueError("Exactly one of user_id, group_id, or service_account_id must be provided")
        return v


class RoleAssignmentRead(RoleAssignmentBase):
    """Schema for reading role assignment data."""

    id: UUID
    role_id: UUID
    role_name: str | None = None

    # Assignee
    user_id: UUID | None
    user_name: str | None = None
    group_id: UUID | None
    group_name: str | None = None
    service_account_id: UUID | None
    service_account_name: str | None = None

    # Scope
    workspace_id: UUID | None
    workspace_name: str | None = None
    project_id: UUID | None
    project_name: str | None = None
    environment_id: UUID | None
    environment_name: str | None = None
    flow_id: UUID | None
    flow_name: str | None = None
    component_id: UUID | None

    # Assignment info
    assigned_by_id: UUID
    assigned_by_name: str | None = None
    approved_by_id: UUID | None
    approved_by_name: str | None = None


class RoleAssignmentUpdate(SQLModel):
    """Schema for updating a role assignment."""

    is_active: bool | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    conditions: dict | None = Field(default=None, sa_column=Column(JSON))
    ip_restrictions: list[str] | None = None
    time_restrictions: dict | None = Field(default=None, sa_column=Column(JSON))
    reason: str | None = None
    approved_by_id: UUID | None = None
    approval_date: datetime | None = None


class RoleAssignmentApproval(SQLModel):
    """Schema for approving a role assignment."""

    assignment_id: UUID
    approved: bool
    reason: str | None = None
    conditions: dict | None = Field(default=None, sa_column=Column(JSON))
    valid_until: datetime | None = None
