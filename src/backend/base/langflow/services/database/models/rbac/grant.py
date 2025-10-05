"""Grant model for RBAC system.

Implements Story 2.1 - Assign Roles to Users and Groups within a Scope,
and Story 3.4/3.5 - Assign Roles via Admin UI and API from PRD.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.group import Group
    from langflow.services.database.models.rbac.role import Role
    from langflow.services.database.models.rbac.service_account import ServiceAccount
    from langflow.services.database.models.user.model import User


def utc_now():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class PrincipalType(str, Enum):
    """Type of principal (entity receiving the grant)."""

    USER = "user"
    GROUP = "group"
    SERVICE_ACCOUNT = "service_account"


class ScopeType(str, Enum):
    """Scope types for permission grants.

    Based on PRD Story 2.1 @AC3 - Static scope hierarchy:
    Workspace (1) > Project (2) > Environment (3) > Flow (4) > Component (5)
    """

    WORKSPACE = "workspace"
    PROJECT = "project"
    ENVIRONMENT = "environment"
    FLOW = "flow"
    COMPONENT = "component"


class GrantBase(SQLModel):
    """Base grant model."""

    # Principal (who receives the grant)
    principal_type: PrincipalType = Field(
        index=True, description="Type of principal: user, group, or service_account"
    )
    principal_id: UUIDstr = Field(index=True, description="ID of the user, group, or service account")

    # Role being granted
    role_id: UUIDstr = Field(index=True, foreign_key="role.id", description="Role being assigned")

    # Scope (where the grant applies)
    scope_type: ScopeType = Field(index=True, description="Type of scope: workspace, project, environment, etc.")
    scope_id: str = Field(
        index=True,
        description="ID of the scoped resource (workspace_id, project_id, flow_id, etc.)",
    )

    # Time-bound grants (PRD Story 3.4 @AC3 - optional but valuable)
    expires_at: datetime | None = Field(
        default=None, nullable=True, description="Optional expiration time for temporary grants"
    )

    # Additional metadata
    metadata_: dict | None = Field(
        default=None, sa_column=Column("metadata", JSON), description="Additional grant metadata"
    )


class Grant(GrantBase, table=True):  # type: ignore[call-arg]
    """Grant table - assigns roles to principals at specific scopes.

    PRD Story 2.1:
    - @AC1: Assign role to group within scope
    - @AC2: Remove role assignment
    - @AC4: Higher-scope grants cascade to lower scopes (inheritance)
    - @AC7-@AC9: Component-level, Environment-level, and Token scope enforcement
    """

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    created_by: UUIDstr | None = Field(default=None, nullable=True, description="User ID who created this grant")

    # Relationships
    role: "Role" = Relationship(back_populates="grants")

    # Optional relationships for easier querying
    user_id: UUIDstr | None = Field(default=None, foreign_key="user.id", nullable=True)
    user: "User | None" = Relationship(back_populates="grants")

    # TODO: Re-enable when Group model is implemented
    # group_id: UUIDstr | None = Field(default=None, foreign_key="group.id", nullable=True)
    # group: "Group | None" = Relationship(back_populates="grants")

    service_account_id: UUIDstr | None = Field(default=None, foreign_key="service_account.id", nullable=True)
    service_account: "ServiceAccount | None" = Relationship(back_populates="grants")

    def __init__(self, **data):
        """Initialize grant and set principal foreign key based on principal_type."""
        super().__init__(**data)
        # Set the appropriate foreign key based on principal_type
        if self.principal_type == PrincipalType.USER:
            self.user_id = self.principal_id
        # TODO: Re-enable when Group model is implemented
        # elif self.principal_type == PrincipalType.GROUP:
        #     self.group_id = self.principal_id
        elif self.principal_type == PrincipalType.SERVICE_ACCOUNT:
            self.service_account_id = self.principal_id


class GrantCreate(GrantBase):
    """Schema for creating a new grant.

    PRD Story 3.4 @AC1: Assign role to user at project scope
    PRD Story 3.5 @AC1: Create grant via API
    """

    created_by: UUIDstr | None = None


class GrantRead(GrantBase):
    """Schema for reading grant data in API responses."""

    id: UUIDstr
    created_at: datetime
    created_by: UUIDstr | None
    role_name: str | None = Field(default=None, description="Role name for easier display")


class GrantUpdate(SQLModel):
    """Schema for updating an existing grant.

    PRD Story 3.4 @AC3: Update expiration time for time-bound grants
    """

    expires_at: datetime | None = None
    metadata_: dict | None = Field(default=None, alias="metadata")
