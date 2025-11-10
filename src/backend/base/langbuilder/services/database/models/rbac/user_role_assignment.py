from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, Index, Relationship, SQLModel, UniqueConstraint

from langbuilder.schema.serialize import UUIDstr


class UserRoleAssignment(SQLModel, table=True):  # type: ignore[call-arg]
    """
    User role assignment model for mapping users to roles with specific scopes.

    This table assigns roles to users for specific scopes (global, project, flow).
    It is the core assignment table that drives all permission checks and supports
    the immutability constraint for Starter Project Owner assignments.

    Attributes:
        id: Unique identifier for the assignment
        user_id: Foreign key to the user being assigned the role
        role_id: Foreign key to the role being assigned
        scope_type: The type of scope for the assignment ("global", "project", "flow")
        scope_id: The ID of the specific scope entity (null for global scope)
        is_immutable: Flag indicating if the assignment cannot be deleted (for Starter Project Owner)
        created_at: Timestamp when the assignment was created
        created_by: User ID of who created this assignment (null for system-generated assignments)
    """

    __tablename__ = "user_role_assignment"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: UUIDstr = Field(foreign_key="user.id", index=True)
    role_id: UUIDstr = Field(foreign_key="role.id", index=True)

    # Polymorphic scope
    scope_type: str = Field(index=True)  # "global", "project", "flow"
    scope_id: UUIDstr | None = Field(default=None, nullable=True, index=True)

    # Immutability tracking (for Starter Project Owner)
    is_immutable: bool = Field(default=False)

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: UUIDstr | None = Field(default=None, nullable=True, foreign_key="user.id")

    # Relationships
    user: "User" = Relationship(  # type: ignore[name-defined]
        back_populates="role_assignments",
        sa_relationship_kwargs={"foreign_keys": "UserRoleAssignment.user_id"}
    )
    role: "Role" = Relationship(back_populates="user_assignments")  # type: ignore[name-defined]

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "scope_type", "scope_id", name="unique_user_role_scope"),
        Index("idx_scope_lookup", "user_id", "scope_type", "scope_id"),
    )


class UserRoleAssignmentCreate(SQLModel):
    """Schema for creating a new user role assignment."""

    user_id: UUID = Field()
    role_id: UUID = Field()
    scope_type: str = Field()
    scope_id: UUID | None = Field(default=None)
    is_immutable: bool = Field(default=False)
    created_by: UUID | None = Field(default=None)


class UserRoleAssignmentRead(SQLModel):
    """Schema for reading user role assignment data."""

    id: UUID = Field()
    user_id: UUID = Field()
    role_id: UUID = Field()
    scope_type: str = Field()
    scope_id: UUID | None = Field(default=None)
    is_immutable: bool = Field()
    created_at: datetime = Field()
    created_by: UUID | None = Field(default=None)


class UserRoleAssignmentUpdate(SQLModel):
    """Schema for updating user role assignment data."""

    user_id: UUID | None = None
    role_id: UUID | None = None
    scope_type: str | None = None
    scope_id: UUID | None = None
    is_immutable: bool | None = None
    created_by: UUID | None = None
