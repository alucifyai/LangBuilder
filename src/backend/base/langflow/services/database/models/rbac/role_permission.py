"""RolePermission junction table for many-to-many relationship."""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.permission import Permission
    from langflow.services.database.models.rbac.role import Role


class RolePermission(SQLModel, table=True):  # type: ignore[call-arg]
    """Junction table linking roles to permissions.

    This enables a many-to-many relationship between roles and permissions.
    A role can have multiple permissions, and a permission can be granted to multiple roles.
    """

    __tablename__ = "role_permission"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    role_id: UUID = Field(foreign_key="role.id", nullable=False, index=True)
    permission_id: UUID = Field(foreign_key="permission.id", nullable=False, index=True)

    # Relationships
    role: "Role" = Relationship(back_populates="role_permissions")
    permission: "Permission" = Relationship(back_populates="role_permissions")

    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)
