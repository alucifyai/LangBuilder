"""RoleAssignment model for RBAC system."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import CheckConstraint, Index
from sqlmodel import Field, Relationship, SQLModel

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.role import Role
    from langflow.services.database.models.rbac.service_account import ServiceAccount
    from langflow.services.database.models.user.model import User
    from langflow.services.database.models.user_group.model import UserGroup


class RoleAssignment(SQLModel, table=True):  # type: ignore[call-arg]
    """Role assignment model.

    Assigns a role to a principal (user, service account, or group) at a specific scope.
    The scope hierarchy is: workspace > project > environment > flow > component.
    """

    __tablename__ = "role_assignment"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    role_id: UUID = Field(foreign_key="role.id", nullable=False, index=True)

    # Principal (user, service account, or GROUP)
    assignee_type: str = Field(nullable=False, index=True)  # "user", "service_account", "group"
    user_id: UUID | None = Field(foreign_key="user.id", nullable=True, index=True)
    service_account_id: UUID | None = Field(foreign_key="service_account.id", nullable=True, index=True)
    group_id: UUID | None = Field(foreign_key="user_group.id", nullable=True, index=True)

    # Scope (workspace, project, environment, flow, component)
    scope_type: str = Field(nullable=False, index=True)
    scope_id: UUID = Field(nullable=False, index=True)

    # Lifecycle
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at: datetime | None = Field(default=None, nullable=True)  # For time-boxed grants (Phase 7)

    # Audit and scheduling fields
    assigned_by: UUID | None = Field(default=None, foreign_key="user.id", nullable=True)  # Who created the grant
    valid_from: datetime | None = Field(default=None, nullable=True)  # When grant becomes active

    # Relationships
    role: "Role" = Relationship(back_populates="assignments")
    user: "User" = Relationship(
        back_populates="role_assignments",
        sa_relationship_kwargs={"foreign_keys": "[RoleAssignment.user_id]"},
    )
    service_account: "ServiceAccount" = Relationship(back_populates="role_assignments")
    group: "UserGroup" = Relationship(back_populates="role_assignments")

    __table_args__ = (
        CheckConstraint(
            "(assignee_type = 'user' AND user_id IS NOT NULL AND service_account_id IS NULL AND group_id IS NULL) OR "
            "(assignee_type = 'service_account' AND service_account_id IS NOT NULL AND user_id IS NULL AND group_id IS NULL) OR "
            "(assignee_type = 'group' AND group_id IS NOT NULL AND user_id IS NULL AND service_account_id IS NULL)",
            name="ck_assignee_type_consistency",
        ),
        Index("ix_role_assignment_scope", "scope_type", "scope_id"),
    )


class RoleAssignmentRead(SQLModel):
    """Schema for reading role assignment data."""

    id: UUID
    role_id: UUID
    assignee_type: str
    user_id: UUID | None
    service_account_id: UUID | None
    group_id: UUID | None
    scope_type: str
    scope_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    assigned_by: UUID | None = None
    valid_from: datetime | None = None


class RoleAssignmentCreate(SQLModel):
    """Schema for creating a new role assignment."""

    role_id: UUID
    assignee_type: str
    user_id: UUID | None = None
    service_account_id: UUID | None = None
    group_id: UUID | None = None
    scope_type: str
    scope_id: UUID
    expires_at: datetime | None = None

    @field_validator("assignee_type")
    @classmethod
    def validate_assignee_type(cls, v: str) -> str:
        """Validate assignee type is one of the allowed values."""
        allowed = {"user", "service_account", "group"}
        if v not in allowed:
            msg = f"assignee_type must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return v

    @field_validator("scope_type")
    @classmethod
    def validate_scope_type(cls, v: str) -> str:
        """Validate scope type is one of the allowed values."""
        allowed = {"workspace", "project", "environment", "flow", "component"}
        if v not in allowed:
            msg = f"scope_type must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return v

    def model_post_init(self, __context) -> None:
        """Validate that exactly one principal is set based on assignee_type."""
        if self.assignee_type == "user" and self.user_id is None:
            raise ValueError("user_id must be set when assignee_type is 'user'")
        if self.assignee_type == "service_account" and self.service_account_id is None:
            raise ValueError("service_account_id must be set when assignee_type is 'service_account'")
        if self.assignee_type == "group" and self.group_id is None:
            raise ValueError("group_id must be set when assignee_type is 'group'")

        # Ensure only one principal is set
        principals_set = sum([self.user_id is not None, self.service_account_id is not None, self.group_id is not None])
        if principals_set != 1:
            raise ValueError("Exactly one of user_id, service_account_id, or group_id must be set")
