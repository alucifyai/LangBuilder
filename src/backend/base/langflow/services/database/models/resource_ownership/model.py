"""
Resource Ownership Model

Tracks ownership of resources for automatic permission inheritance.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Column, DateTime, Field, SQLModel


class ResourceOwnership(SQLModel, table=True):
    """
    Resource Ownership Model

    Tracks who owns a resource. Owners automatically get admin-level
    permissions for their resources.
    """

    __tablename__ = "resource_ownership"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )

    # Resource identification
    resource_type: str = Field(index=True, description="Type of resource (flow, project, etc.)")
    resource_id: str = Field(index=True, description="ID of the resource")

    # Owner identification
    owner_type: str = Field(
        index=True,
        description="Owner principal type (user, team, service_account)",
    )
    owner_id: str = Field(index=True, description="Owner principal ID")

    # Transfer tracking
    transferred_from: str | None = Field(None, description="Previous owner ID")
    transferred_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="When ownership was transferred",
    )
    transferred_by: str | None = Field(None, description="Who initiated the transfer")

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    # Unique constraint: one owner per resource
    class Config:
        # In SQLModel 0.0.8+, use SQLAlchemy's UniqueConstraint
        schema_extra = {
            "unique_together": [("resource_type", "resource_id")]
        }


class OwnershipTransferRequest(SQLModel, table=True):
    """
    Ownership Transfer Request

    Tracks pending ownership transfer requests that require approval.
    """

    __tablename__ = "ownership_transfer_request"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )

    # Resource
    resource_type: str = Field(index=True)
    resource_id: str = Field(index=True)

    # Transfer details
    current_owner_id: str = Field(description="Current owner")
    new_owner_id: str = Field(description="Proposed new owner")
    requested_by: str = Field(description="Who requested the transfer")

    # Status
    status: str = Field(
        default="pending",
        index=True,
        description="pending, approved, rejected, cancelled",
    )

    # Resolution
    approved_by: str | None = Field(None, description="Who approved/rejected")
    resolved_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    rejection_reason: str | None = Field(None)

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Request expiration time",
    )
