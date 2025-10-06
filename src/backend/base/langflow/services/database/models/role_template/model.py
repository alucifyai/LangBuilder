"""
Role Template Model

Pre-defined role templates for quick role creation.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Column, DateTime, Field, SQLModel, Text
from sqlalchemy import JSON


class RoleTemplate(SQLModel, table=True):
    """
    Role Template Model

    Pre-defined templates for creating roles with standard permission sets.
    Examples: Viewer, Editor, Admin, Developer, etc.
    """

    __tablename__ = "role_template"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )

    # Template details
    name: str = Field(unique=True, index=True, description="Template name (e.g., 'Viewer', 'Editor')")
    display_name: str = Field(description="Human-readable display name")
    description: str = Field(
        sa_column=Column(Text),
        description="Template description",
    )

    # Template icon/category
    category: str = Field(
        default="standard",
        description="Template category (standard, custom, advanced)",
    )
    icon: str | None = Field(None, description="Icon name for UI")

    # Permissions
    permissions: list[str] = Field(
        sa_column=Column(JSON, nullable=False),
        description="List of permissions included in this template",
    )

    # Metadata
    is_system: bool = Field(
        default=False,
        description="System template (cannot be deleted)",
    )
    is_active: bool = Field(
        default=True,
        index=True,
        description="Is template active/visible",
    )

    # Usage tracking
    usage_count: int = Field(
        default=0,
        description="Number of times this template has been used",
    )

    # Versioning
    version: int = Field(default=1, description="Template version")

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    created_by: str | None = Field(None, description="User who created template")
