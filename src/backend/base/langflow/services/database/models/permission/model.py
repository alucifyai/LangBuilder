from sqlmodel import Field, SQLModel


class Permission(SQLModel, table=True):  # type: ignore[call-arg]
    """Permission catalog entry defining available actions on resources."""

    id: str = Field(primary_key=True)  # e.g., "flows:create", "flows:export"
    resource_type: str = Field(index=True)  # e.g., "flows", "components", "projects"
    action: str = Field(index=True)  # e.g., "create", "read", "update", "delete", "export"
    description: str = Field()  # Human-readable description of the permission
