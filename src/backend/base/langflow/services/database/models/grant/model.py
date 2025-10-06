from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from langflow.schema.serialize import UUIDstr


class PrincipalType(str, Enum):
    """Type of principal (identity) that can be granted a role."""

    USER = "user"
    GROUP = "group"
    SERVICE_ACCOUNT = "service_account"


class ScopeType(str, Enum):
    """Type of scope where a role can be assigned."""

    WORKSPACE = "workspace"
    PROJECT = "project"
    ENVIRONMENT = "environment"
    FLOW = "flow"
    COMPONENT = "component"


class Grant(SQLModel, table=True):  # type: ignore[call-arg]
    """
    Role assignment (grant) to a principal at a specific scope.

    Represents: "Principal X has Role Y at Scope Z"
    Example: "User alice@example.com has Editor role at Project PRJ1"
    """

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)

    # Principal (who gets the role)
    principal_type: PrincipalType = Field(index=True)
    principal_id: UUIDstr = Field(index=True)  # user_id, group_id, or service_account_id

    # Role assignment
    role_id: UUIDstr = Field(index=True)  # Reference to Role table

    # Scope (where the role applies)
    scope_type: ScopeType = Field(index=True)
    scope_id: str = Field(index=True)  # workspace_id, project_id, flow_id, etc.

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = Field(default=None, nullable=True)  # For time-bound grants
