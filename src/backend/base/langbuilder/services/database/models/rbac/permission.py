from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from langbuilder.schema.serialize import UUIDstr


class Permission(SQLModel, table=True):  # type: ignore[call-arg]
    """
    Permission model representing CRUD actions applicable to entity types.

    Permissions define granular access control actions (Create, Read, Update, Delete)
    that can be applied to specific scope types (Flow, Project, Global).
    """

    __table_args__ = (
        {"sqlite_autoincrement": True},  # For SQLite compatibility
    )

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    name: str = Field(index=True)  # "Create", "Read", "Update", "Delete" - not globally unique
    description: str | None = Field(default=None, nullable=True)
    scope_type: str = Field(index=True)  # "Flow", "Project", "Global"

    # Relationships
    role_permissions: list["RolePermission"] = Relationship(back_populates="permission")  # type: ignore[name-defined]


class PermissionCreate(SQLModel):
    """Schema for creating a new permission."""

    name: str = Field()
    description: str | None = Field(default=None)
    scope_type: str = Field()


class PermissionRead(SQLModel):
    """Schema for reading permission data."""

    id: UUID = Field()
    name: str = Field()
    description: str | None = Field(default=None)
    scope_type: str = Field()


class PermissionUpdate(SQLModel):
    """Schema for updating permission data."""

    name: str | None = None
    description: str | None = None
    scope_type: str | None = None
