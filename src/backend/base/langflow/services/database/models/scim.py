"""SCIM (System for Cross-domain Identity Management) models.

PRD Story 2.2 - Enterprise SSO Integration
PRD Story 2.3 @AC3 - Support SCIM provisioning
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlmodel import Column, Field as SQLField, Relationship, SQLModel

from langflow.services.database.models.base import TimestampedBase

if TYPE_CHECKING:
    from langflow.services.database.models.user.model import User


class SCIMResourceType(str, Enum):
    """SCIM resource types."""

    USER = "User"
    GROUP = "Group"


class SCIMProvisioningStatus(str, Enum):
    """SCIM provisioning status."""

    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class SCIMToken(TimestampedBase, table=True):
    """SCIM authentication token.

    Bearer tokens for authenticating SCIM requests from IdP.
    PRD Story 2.3 @AC3 - SCIM authentication
    """

    __tablename__ = "scim_token"

    id: UUID = SQLField(default_factory=uuid4, primary_key=True, index=True)
    workspace_id: str = SQLField(index=True, description="Workspace this token belongs to")
    name: str = SQLField(description="Human-readable name for this token")
    token_hash: str = SQLField(unique=True, index=True, description="Hashed bearer token")
    token_prefix: str = SQLField(index=True, description="First 8 chars of token for identification")

    # Scopes and permissions
    scopes: str = SQLField(
        default="user:read user:write group:read group:write",
        description="Space-separated SCIM scopes",
    )

    # Token metadata
    is_active: bool = SQLField(default=True, description="Whether token is active")
    expires_at: datetime | None = SQLField(default=None, description="Token expiration (null = never)")
    last_used_at: datetime | None = SQLField(default=None, description="Last time token was used")


class SCIMExternalMapping(TimestampedBase, table=True):
    """Maps external SCIM resources to internal users/groups.

    Tracks the relationship between IdP identities and LangBuilder entities.
    PRD Story 2.3 @AC3 - External identity mapping
    """

    __tablename__ = "scim_external_mapping"

    id: UUID = SQLField(default_factory=uuid4, primary_key=True, index=True)
    workspace_id: str = SQLField(index=True, description="Workspace")

    # External identity
    external_id: str = SQLField(index=True, description="External ID from IdP")
    resource_type: SCIMResourceType = SQLField(description="Type of resource (User or Group)")

    # Internal mapping
    internal_id: UUID = SQLField(description="Internal user or group ID")

    # Provisioning status
    status: SCIMProvisioningStatus = SQLField(
        default=SCIMProvisioningStatus.ACTIVE,
        description="Provisioning status",
    )

    # Metadata
    external_data: str | None = SQLField(
        default=None,
        description="JSON snapshot of external resource data",
    )


class SCIMProvisioningLog(TimestampedBase, table=True):
    """Log of SCIM provisioning operations.

    Audit trail for all SCIM operations (create, update, delete).
    PRD Story 5.1 - Audit SCIM operations
    """

    __tablename__ = "scim_provisioning_log"

    id: UUID = SQLField(default_factory=uuid4, primary_key=True, index=True)
    workspace_id: str = SQLField(index=True, description="Workspace")

    # Operation details
    operation: str = SQLField(description="SCIM operation (POST, PUT, PATCH, DELETE)")
    resource_type: SCIMResourceType = SQLField(description="Resource type")
    external_id: str = SQLField(index=True, description="External ID")
    internal_id: UUID | None = SQLField(default=None, description="Internal ID if mapped")

    # Request metadata
    scim_token_id: UUID = SQLField(foreign_key="scim_token.id", description="Token used")
    ip_address: str | None = SQLField(default=None, description="Client IP")

    # Result
    success: bool = SQLField(description="Whether operation succeeded")
    error_message: str | None = SQLField(default=None, description="Error message if failed")

    # Data
    request_data: str | None = SQLField(default=None, description="SCIM request body (JSON)")
    response_data: str | None = SQLField(default=None, description="SCIM response body (JSON)")


# Pydantic models for SCIM 2.0 API responses


class SCIMMeta(BaseModel):
    """SCIM resource metadata."""

    resourceType: str
    created: datetime | None = None
    lastModified: datetime | None = None
    location: str | None = None


class SCIMEmail(BaseModel):
    """SCIM email address."""

    value: str
    type: str = "work"
    primary: bool = True


class SCIMName(BaseModel):
    """SCIM user name."""

    formatted: str | None = None
    familyName: str | None = None
    givenName: str | None = None


class SCIMUserResponse(BaseModel):
    """SCIM 2.0 User resource response.

    PRD Story 2.3 @AC3 - SCIM User schema
    """

    schemas: list[str] = ["urn:ietf:params:scim:schemas:core:2.0:User"]
    id: str
    externalId: str | None = None
    userName: str
    name: SCIMName | None = None
    emails: list[SCIMEmail] = []
    active: bool = True
    meta: SCIMMeta


class SCIMMember(BaseModel):
    """SCIM group member."""

    value: str  # User ID
    display: str | None = None  # User display name
    type: str = "User"


class SCIMGroupResponse(BaseModel):
    """SCIM 2.0 Group resource response.

    PRD Story 2.3 @AC3 - SCIM Group schema
    """

    schemas: list[str] = ["urn:ietf:params:scim:schemas:core:2.0:Group"]
    id: str
    externalId: str | None = None
    displayName: str
    members: list[SCIMMember] = []
    meta: SCIMMeta


class SCIMListResponse(BaseModel):
    """SCIM 2.0 list response."""

    schemas: list[str] = ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    totalResults: int
    startIndex: int
    itemsPerPage: int
    Resources: list[SCIMUserResponse | SCIMGroupResponse]


class SCIMError(BaseModel):
    """SCIM 2.0 error response."""

    schemas: list[str] = ["urn:ietf:params:scim:api:messages:2.0:Error"]
    status: str
    detail: str | None = None


class SCIMUserCreate(BaseModel):
    """SCIM User creation request."""

    schemas: list[str]
    externalId: str | None = None
    userName: str
    name: SCIMName | None = None
    emails: list[SCIMEmail] = []
    active: bool = True


class SCIMGroupCreate(BaseModel):
    """SCIM Group creation request."""

    schemas: list[str]
    externalId: str | None = None
    displayName: str
    members: list[SCIMMember] = []


class SCIMPatchOp(BaseModel):
    """SCIM PATCH operation."""

    op: str  # "add", "remove", "replace"
    path: str | None = None
    value: dict | list | str | bool | None = None


class SCIMPatchRequest(BaseModel):
    """SCIM PATCH request."""

    schemas: list[str] = ["urn:ietf:params:scim:api:messages:2.0:PatchOp"]
    Operations: list[SCIMPatchOp]
