from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from langbuilder.schema.serialize import UUIDstr


class RolePermission(SQLModel, table=True):  # type: ignore[call-arg]
    """
    Junction table mapping roles to permissions.

    This table defines the many-to-many relationship between roles and permissions,
    establishing which permissions each role has. For example, Viewer role has only
    Read permission, while Owner role has all CRUD permissions.
    """

    __tablename__ = "role_permission"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    role_id: UUIDstr = Field(foreign_key="role.id", index=True)
    permission_id: UUIDstr = Field(foreign_key="permission.id", index=True)

    # Relationships
    role: "Role" = Relationship(back_populates="role_permissions")  # type: ignore[name-defined]
    permission: "Permission" = Relationship(back_populates="role_permissions")  # type: ignore[name-defined]

    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="unique_role_permission"),)


class RolePermissionCreate(SQLModel):
    """Schema for creating a new role-permission mapping."""

    role_id: UUID = Field()
    permission_id: UUID = Field()


class RolePermissionRead(SQLModel):
    """Schema for reading role-permission mapping data."""

    id: UUID = Field()
    role_id: UUID = Field()
    permission_id: UUID = Field()


class RolePermissionUpdate(SQLModel):
    """Schema for updating role-permission mapping data."""

    role_id: UUID | None = None
    permission_id: UUID | None = None
