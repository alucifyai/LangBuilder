"""
SCIM 2.0 provisioning models
Implements System for Cross-domain Identity Management protocol
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlmodel import Column, Field, JSON, SQLModel


class SCIMUser(SQLModel, table=True):
    """
    SCIM User representation
    Maps to SCIM 2.0 User schema
    """

    __tablename__ = "scim_users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # SCIM external ID from IdP
    external_id: str = Field(index=True, unique=True)
    # LangBuilder user ID (links to users table)
    user_id: UUID | None = Field(default=None, foreign_key="user.id", index=True)
    # SCIM user attributes
    username: str = Field(index=True)
    email: str = Field(index=True, unique=True)
    given_name: str | None = None
    family_name: str | None = None
    display_name: str | None = None
    active: bool = Field(default=True)
    # SCIM metadata
    scim_meta: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    # IdP organization
    organization_id: str | None = Field(default=None, index=True)
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SCIMGroup(SQLModel, table=True):
    """
    SCIM Group representation
    Maps to SCIM 2.0 Group schema
    """

    __tablename__ = "scim_groups"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # SCIM external ID from IdP
    external_id: str = Field(index=True, unique=True)
    # Group attributes
    display_name: str = Field(index=True)
    # Role mapping: this group gets this role in this scope
    mapped_role_id: UUID | None = Field(default=None, foreign_key="role.id")
    mapped_scope_type: str | None = None  # Workspace, Project, etc.
    mapped_scope_id: str | None = None  # The actual resource ID
    # SCIM metadata
    scim_meta: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    # IdP organization
    organization_id: str | None = Field(default=None, index=True)
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SCIMGroupMembership(SQLModel, table=True):
    """
    SCIM Group membership
    Links users to groups
    """

    __tablename__ = "scim_group_memberships"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scim_group_id: UUID = Field(foreign_key="scim_groups.id", index=True)
    scim_user_id: UUID = Field(foreign_key="scim_users.id", index=True)
    # Member attributes
    member_ref: str | None = None  # SCIM member $ref URL
    member_type: str = Field(default="User")  # User or Group
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SCIMProvisioningLog(SQLModel, table=True):
    """
    Audit log for SCIM provisioning events
    """

    __tablename__ = "scim_provisioning_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # Event details
    event_type: str = Field(index=True)  # create_user, update_user, delete_user, etc.
    resource_type: str = Field(index=True)  # User or Group
    external_id: str | None = Field(default=None, index=True)
    # Operation result
    status: str = Field(index=True)  # success, error
    error_message: str | None = None
    # Request/response details
    request_payload: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    response_payload: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    # IdP info
    organization_id: str | None = Field(default=None, index=True)
    idp_source: str | None = None  # Okta, Azure AD, etc.
    # Timestamp
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
