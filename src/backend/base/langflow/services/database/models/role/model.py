from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from langflow.schema.serialize import UUIDstr


class Role(SQLModel, table=True):  # type: ignore[call-arg]
    """Role definition with a set of permissions."""

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    name: str = Field(unique=True, index=True)  # e.g., "Editor", "Deployer"
    permissions: list[str] | None = Field(
        sa_column=Column(JSON, default=list, nullable=False),
        description="List of permission IDs from the permission catalog",
    )
    version: int = Field(default=1, description="Version number for audit trail")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def validate_permissions(self, permission_ids: set[str]) -> tuple[bool, list[str]]:
        """
        Validate that all permissions in this role exist in the permission catalog.

        Args:
            permission_ids: Set of valid permission IDs from the permission catalog

        Returns:
            Tuple of (is_valid, list of unknown permission IDs)
        """
        if not self.permissions:
            return True, []

        unknown_permissions = [p for p in self.permissions if p not in permission_ids]
        return len(unknown_permissions) == 0, unknown_permissions
