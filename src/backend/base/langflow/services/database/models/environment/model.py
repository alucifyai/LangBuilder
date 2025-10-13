"""Environment model for deployment scoping."""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.flow.model import Flow
    from langflow.services.database.models.folder.model import Folder


class EnvironmentType(str, Enum):
    """Environment types for deployment stages."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Environment(SQLModel, table=True):  # type: ignore[call-arg]
    """Environment model for deployment scoping.

    Environments represent deployment stages (dev/staging/prod) within a project.
    Flows can be deployed to specific environments for isolation and testing.
    """

    __tablename__ = "environment"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    project_id: UUID = Field(foreign_key="folder.id", nullable=False, index=True)  # Note: folder = project
    name: str = Field(max_length=255, nullable=False)
    environment_type: str = Field(nullable=False, index=True)  # development, staging, production
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = Field(default=True, nullable=False)

    # Deployment configuration
    config: dict[str, Any] = Field(sa_column=Column(JSON, default=dict, nullable=False))

    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    project: "Folder" = Relationship(back_populates="environments")
    flows: list["Flow"] = Relationship(back_populates="environment")

    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_project_environment_name"),)


class EnvironmentRead(SQLModel):
    """Schema for reading environment data."""

    id: UUID
    project_id: UUID
    name: str
    environment_type: str
    description: str | None
    is_active: bool
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class EnvironmentCreate(SQLModel):
    """Schema for creating a new environment."""

    name: str = Field(max_length=255, min_length=1)
    environment_type: str
    description: str | None = Field(default=None, max_length=1000)
    config: dict[str, Any] | None = None

    @field_validator("environment_type")
    @classmethod
    def validate_environment_type(cls, v: str) -> str:
        """Validate environment type is one of the allowed values."""
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            msg = f"environment_type must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return v

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate config structure to prevent DoS attacks.

        Prevents deeply nested configs that could cause performance issues
        or memory exhaustion when processing or storing the configuration.
        """
        if v is None:
            return v

        def check_depth(obj: Any, depth: int = 0, max_depth: int = 5) -> None:
            """Recursively check nesting depth of config object."""
            if depth > max_depth:
                msg = f"Config nesting depth cannot exceed {max_depth} levels"
                raise ValueError(msg)

            if isinstance(obj, dict):
                for value in obj.values():
                    check_depth(value, depth + 1, max_depth)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, depth + 1, max_depth)

        check_depth(v)
        return v


class EnvironmentUpdate(SQLModel):
    """Schema for updating an environment."""

    name: str | None = Field(default=None, max_length=255, min_length=1)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None
    config: dict[str, Any] | None = None

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate config structure to prevent DoS attacks.

        Prevents deeply nested configs that could cause performance issues
        or memory exhaustion when processing or storing the configuration.
        """
        if v is None:
            return v

        def check_depth(obj: Any, depth: int = 0, max_depth: int = 5) -> None:
            """Recursively check nesting depth of config object."""
            if depth > max_depth:
                msg = f"Config nesting depth cannot exceed {max_depth} levels"
                raise ValueError(msg)

            if isinstance(obj, dict):
                for value in obj.values():
                    check_depth(value, depth + 1, max_depth)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, depth + 1, max_depth)

        check_depth(v)
        return v
