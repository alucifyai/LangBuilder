"""Permission model for RBAC system.

Implements Story 1.1 - Permission Catalog (CRUD + Extended) from PRD.
"""

from enum import Enum

from sqlmodel import Field, SQLModel

from langflow.schema.serialize import UUIDstr


class PermissionAction(str, Enum):
    """Permission actions catalog.

    Based on PRD Story 1.1 @AC1:
    - CRUD actions: create, read, update, delete
    - Extended actions: export_flow, deploy_environment, invite_users,
      modify_component_settings, manage_tokens
    """

    # CRUD actions
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    # Extended actions (PRD Story 1.1 @AC1)
    EXPORT_FLOW = "export_flow"
    DEPLOY_ENVIRONMENT = "deploy_environment"
    INVITE_USERS = "invite_users"
    MODIFY_COMPONENT_SETTINGS = "modify_component_settings"
    MANAGE_TOKENS = "manage_tokens"


class ResourceType(str, Enum):
    """Resource types that permissions can be applied to.

    Based on PRD scope hierarchy (Story 2.1 @AC3):
    - Workspace (rank 1)
    - Project (rank 2)
    - Environment (rank 3)
    - Flow (rank 4)
    - Component (rank 5)
    """

    WORKSPACE = "workspace"
    PROJECT = "project"
    ENVIRONMENT = "environment"
    FLOW = "flow"
    COMPONENT = "component"
    USER = "user"
    APIKEY = "apikey"


class PermissionBase(SQLModel):
    """Base permission model."""

    action: PermissionAction = Field(index=True, description="Permission action (e.g., 'read', 'export_flow')")
    resource_type: ResourceType = Field(index=True, description="Resource type this permission applies to")
    description: str | None = Field(default=None, description="Human-readable description of the permission")


class Permission(PermissionBase, table=True):  # type: ignore[call-arg]
    """Permission catalog table.

    Permissions are defined by the system and are not user-editable.
    They form the building blocks for Role definitions.

    PRD Story 1.1 @AC2: Role builder only accepts known permission IDs.
    """

    id: str = Field(
        primary_key=True,
        description="Permission ID in format '<resource_type>:<action>' (e.g., 'flow:read', 'flow:export_flow')",
    )

    def __init__(self, **data):
        """Initialize permission with auto-generated ID."""
        if "id" not in data and "action" in data and "resource_type" in data:
            data["id"] = f"{data['resource_type']}:{data['action']}"
        super().__init__(**data)


class PermissionRead(PermissionBase):
    """Permission read schema for API responses."""

    id: str


# Predefined permission catalog (PRD Story 1.1 @AC1)
PERMISSION_CATALOG: list[dict] = [
    # Workspace permissions
    {"action": PermissionAction.CREATE, "resource_type": ResourceType.WORKSPACE, "description": "Create workspaces"},
    {"action": PermissionAction.READ, "resource_type": ResourceType.WORKSPACE, "description": "View workspace details"},
    {
        "action": PermissionAction.UPDATE,
        "resource_type": ResourceType.WORKSPACE,
        "description": "Modify workspace settings",
    },
    {
        "action": PermissionAction.DELETE,
        "resource_type": ResourceType.WORKSPACE,
        "description": "Delete workspaces",
    },
    {
        "action": PermissionAction.INVITE_USERS,
        "resource_type": ResourceType.WORKSPACE,
        "description": "Invite users to workspace",
    },
    # Project permissions
    {"action": PermissionAction.CREATE, "resource_type": ResourceType.PROJECT, "description": "Create projects"},
    {"action": PermissionAction.READ, "resource_type": ResourceType.PROJECT, "description": "View project details"},
    {"action": PermissionAction.UPDATE, "resource_type": ResourceType.PROJECT, "description": "Modify project settings"},
    {"action": PermissionAction.DELETE, "resource_type": ResourceType.PROJECT, "description": "Delete projects"},
    # Environment permissions
    {
        "action": PermissionAction.CREATE,
        "resource_type": ResourceType.ENVIRONMENT,
        "description": "Create environments",
    },
    {"action": PermissionAction.READ, "resource_type": ResourceType.ENVIRONMENT, "description": "View environments"},
    {
        "action": PermissionAction.UPDATE,
        "resource_type": ResourceType.ENVIRONMENT,
        "description": "Modify environments",
    },
    {
        "action": PermissionAction.DELETE,
        "resource_type": ResourceType.ENVIRONMENT,
        "description": "Delete environments",
    },
    {
        "action": PermissionAction.DEPLOY_ENVIRONMENT,
        "resource_type": ResourceType.ENVIRONMENT,
        "description": "Deploy to environment",
    },
    # Flow permissions
    {"action": PermissionAction.CREATE, "resource_type": ResourceType.FLOW, "description": "Create flows"},
    {"action": PermissionAction.READ, "resource_type": ResourceType.FLOW, "description": "View flow details"},
    {"action": PermissionAction.UPDATE, "resource_type": ResourceType.FLOW, "description": "Modify flows"},
    {"action": PermissionAction.DELETE, "resource_type": ResourceType.FLOW, "description": "Delete flows"},
    {"action": PermissionAction.EXPORT_FLOW, "resource_type": ResourceType.FLOW, "description": "Export flows"},
    # Component permissions
    {"action": PermissionAction.CREATE, "resource_type": ResourceType.COMPONENT, "description": "Create components"},
    {"action": PermissionAction.READ, "resource_type": ResourceType.COMPONENT, "description": "View components"},
    {
        "action": PermissionAction.UPDATE,
        "resource_type": ResourceType.COMPONENT,
        "description": "Modify components",
    },
    {
        "action": PermissionAction.DELETE,
        "resource_type": ResourceType.COMPONENT,
        "description": "Delete components",
    },
    {
        "action": PermissionAction.MODIFY_COMPONENT_SETTINGS,
        "resource_type": ResourceType.COMPONENT,
        "description": "Modify component settings",
    },
    # User permissions
    {"action": PermissionAction.CREATE, "resource_type": ResourceType.USER, "description": "Create users"},
    {"action": PermissionAction.READ, "resource_type": ResourceType.USER, "description": "View user details"},
    {"action": PermissionAction.UPDATE, "resource_type": ResourceType.USER, "description": "Modify user details"},
    {"action": PermissionAction.DELETE, "resource_type": ResourceType.USER, "description": "Delete users"},
    {
        "action": PermissionAction.INVITE_USERS,
        "resource_type": ResourceType.USER,
        "description": "Invite new users",
    },
    # API Key permissions
    {"action": PermissionAction.CREATE, "resource_type": ResourceType.APIKEY, "description": "Create API keys"},
    {"action": PermissionAction.READ, "resource_type": ResourceType.APIKEY, "description": "View API keys"},
    {"action": PermissionAction.UPDATE, "resource_type": ResourceType.APIKEY, "description": "Modify API keys"},
    {"action": PermissionAction.DELETE, "resource_type": ResourceType.APIKEY, "description": "Delete API keys"},
    {
        "action": PermissionAction.MANAGE_TOKENS,
        "resource_type": ResourceType.APIKEY,
        "description": "Manage API tokens",
    },
]
