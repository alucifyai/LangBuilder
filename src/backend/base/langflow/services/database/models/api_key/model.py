from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import JSON, Column
from sqlmodel import DateTime, Field, Relationship, SQLModel, func

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.service_account import ServiceAccount
    from langflow.services.database.models.user.model import User


def utc_now():
    return datetime.now(timezone.utc)


class ApiKeyBase(SQLModel):
    name: str | None = Field(index=True, nullable=True, default=None)
    last_used_at: datetime | None = Field(default=None, nullable=True)
    total_uses: int = Field(default=0)
    is_active: bool = Field(default=True)

    # RBAC scope fields
    workspace_id: UUID | None = Field(default=None, nullable=True, foreign_key="workspace.id", index=True)
    scope_type: str | None = Field(default=None, nullable=True, max_length=50)  # workspace, project, flow
    scope_id: UUID | None = Field(default=None, nullable=True, index=True)
    scoped_permissions: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON, default=None, nullable=True)
    )  # Explicit permission list for this token


class ApiKey(ApiKeyBase, table=True):  # type: ignore[call-arg]
    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    api_key: str = Field(index=True, unique=True)

    # Owner relationship (user or service account)
    user_id: UUIDstr | None = Field(default=None, nullable=True, index=True, foreign_key="user.id")
    service_account_id: UUID | None = Field(default=None, nullable=True, index=True, foreign_key="service_account.id")

    user: "User" = Relationship(back_populates="api_keys")
    service_account: "ServiceAccount" = Relationship(back_populates="api_keys")


class ApiKeyCreate(ApiKeyBase):
    api_key: str | None = None
    user_id: UUIDstr | None = None
    created_at: datetime | None = Field(default_factory=utc_now)

    @field_validator("created_at", mode="before")
    @classmethod
    def set_created_at(cls, v):
        return v or utc_now()


class UnmaskedApiKeyRead(ApiKeyBase):
    id: UUIDstr
    api_key: str = Field()
    user_id: UUIDstr = Field()


class ApiKeyRead(ApiKeyBase):
    id: UUIDstr
    api_key: str = Field(schema_extra={"validate_default": True})
    user_id: UUIDstr = Field()
    created_at: datetime = Field()

    @field_validator("api_key")
    @classmethod
    def mask_api_key(cls, v) -> str:
        # This validator will always run, and will mask the API key
        return f"{v[:8]}{'*' * (len(v) - 8)}"
