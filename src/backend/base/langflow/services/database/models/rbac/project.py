from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import JSON, Column, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.workspace import Workspace
    from langflow.services.database.models.rbac.environment import Environment
    from langflow.services.database.models.rbac.role_assignment import RoleAssignment
    from langflow.services.database.models.flow.model import Flow
    from langflow.services.database.models.user.model import User


class ProjectBase(SQLModel):
    """Base project model for organizing flows within a workspace."""

    name: str = Field(index=True)
    description: str | None = Field(default=None, sa_column=Column(Text))

    # Project metadata
    repository_url: str | None = Field(default=None)
    documentation_url: str | None = Field(default=None)
    tags: list[str] | None = Field(default=[], sa_column=Column(JSON))
    metadata: dict | None = Field(default={}, sa_column=Column(JSON))

    # Project settings
    default_environment_id: UUIDstr | None = Field(default=None)
    auto_deploy_enabled: bool = Field(default=False)
    retention_days: int = Field(default=30)  # Data retention policy

    # Status
    is_active: bool = Field(default=True, index=True)
    is_archived: bool = Field(default=False)
    archived_at: datetime | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Project name cannot be empty")
        if len(v) > 255:
            raise ValueError("Project name cannot exceed 255 characters")
        # Validate project name format (alphanumeric, hyphens, underscores)
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Project name must contain only letters, numbers, hyphens, and underscores")
        return v.strip()


class Project(ProjectBase, table=True):  # type: ignore[call-arg]
    """Project table for organizing flows and environments."""

    __tablename__ = "project"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)

    # Workspace relationship
    workspace_id: UUIDstr = Field(foreign_key="workspace.id", index=True)
    workspace: "Workspace" = Relationship(back_populates="projects")

    # Owner relationship
    owner_id: UUIDstr = Field(foreign_key="user.id", index=True)
    owner: "User" = Relationship(back_populates="owned_projects")

    # Relationships
    environments: list["Environment"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    flows: list["Flow"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    role_assignments: list["RoleAssignment"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # Unique constraints
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="unique_project_name_per_workspace"),
    )


class ProjectCreate(SQLModel):
    """Schema for creating a project."""

    name: str
    description: str | None = None
    workspace_id: UUID
    repository_url: str | None = None
    documentation_url: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    auto_deploy_enabled: bool = False
    retention_days: int = 30


class ProjectRead(ProjectBase):
    """Schema for reading project data."""

    id: UUID
    workspace_id: UUID
    owner_id: UUID
    environment_count: int | None = None
    flow_count: int | None = None
    last_deployed_at: datetime | None = None


class ProjectUpdate(SQLModel):
    """Schema for updating project data."""

    name: str | None = None
    description: str | None = None
    repository_url: str | None = None
    documentation_url: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    default_environment_id: UUID | None = None
    auto_deploy_enabled: bool | None = None
    retention_days: int | None = None
    is_active: bool | None = None
    is_archived: bool | None = None


class ProjectStatistics(BaseModel):
    """Project statistics and metrics."""

    project_id: UUID
    total_flows: int = 0
    active_flows: int = 0
    total_environments: int = 0
    active_environments: int = 0
    total_deployments: int = 0
    successful_deployments: int = 0
    failed_deployments: int = 0
    last_deployment_at: datetime | None = None
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time_ms: float | None = None
    storage_used_bytes: int = 0
    api_calls_count: int = 0
    unique_users_count: int = 0
