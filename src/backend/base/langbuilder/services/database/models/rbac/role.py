from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from langbuilder.schema.serialize import UUIDstr


class Role(SQLModel, table=True):  # type: ignore[call-arg]
    """
    Role model representing a collection of permissions.

    Roles define user access levels (Admin, Owner, Editor, Viewer) and contain
    sets of permissions that determine what actions users can perform.
    System roles (is_system=True) are predefined and cannot be deleted.
    """

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    name: str = Field(unique=True, index=True)  # "Admin", "Owner", "Editor", "Viewer"
    description: str | None = Field(default=None, nullable=True)
    is_system: bool = Field(default=True)  # Prevents deletion of predefined roles

    # Relationships
    role_permissions: list["RolePermission"] = Relationship(back_populates="role")  # type: ignore[name-defined]
    user_assignments: list["UserRoleAssignment"] = Relationship(back_populates="role")  # type: ignore[name-defined]


class RoleCreate(SQLModel):
    """Schema for creating a new role."""

    name: str = Field()
    description: str | None = Field(default=None)
    is_system: bool = Field(default=False)


class RoleRead(SQLModel):
    """Schema for reading role data."""

    id: UUID = Field()
    name: str = Field()
    description: str | None = Field(default=None)
    is_system: bool = Field()


class RoleUpdate(SQLModel):
    """Schema for updating role data."""

    name: str | None = None
    description: str | None = None
    is_system: bool | None = None
