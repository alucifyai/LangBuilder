"""
Seed the permission catalog with CRUD and extended permissions.

This script populates the permission table with the initial set of permissions
required for the RBAC system.
"""

from sqlmodel import Session

from langflow.services.database.models.permission.model import Permission


def seed_permissions(session: Session) -> None:
    """Seed the permission catalog with CRUD and extended permissions."""
    permissions = [
        # CRUD permissions for flows
        Permission(
            id="flows:create",
            resource_type="flows",
            action="create",
            description="Create new flows",
        ),
        Permission(
            id="flows:read",
            resource_type="flows",
            action="read",
            description="Read/view flows",
        ),
        Permission(
            id="flows:update",
            resource_type="flows",
            action="update",
            description="Update existing flows",
        ),
        Permission(
            id="flows:delete",
            resource_type="flows",
            action="delete",
            description="Delete flows",
        ),
        # CRUD permissions for components
        Permission(
            id="components:create",
            resource_type="components",
            action="create",
            description="Create new components",
        ),
        Permission(
            id="components:read",
            resource_type="components",
            action="read",
            description="Read/view components",
        ),
        Permission(
            id="components:update",
            resource_type="components",
            action="update",
            description="Update existing components",
        ),
        Permission(
            id="components:delete",
            resource_type="components",
            action="delete",
            description="Delete components",
        ),
        # CRUD permissions for folders (projects)
        Permission(
            id="folders:create",
            resource_type="folders",
            action="create",
            description="Create new folders/projects",
        ),
        Permission(
            id="folders:read",
            resource_type="folders",
            action="read",
            description="Read/view folders/projects",
        ),
        Permission(
            id="folders:update",
            resource_type="folders",
            action="update",
            description="Update existing folders/projects",
        ),
        Permission(
            id="folders:delete",
            resource_type="folders",
            action="delete",
            description="Delete folders/projects",
        ),
        # CRUD permissions for users
        Permission(
            id="users:create",
            resource_type="users",
            action="create",
            description="Create new users",
        ),
        Permission(
            id="users:read",
            resource_type="users",
            action="read",
            description="Read/view user information",
        ),
        Permission(
            id="users:update",
            resource_type="users",
            action="update",
            description="Update existing users",
        ),
        Permission(
            id="users:delete",
            resource_type="users",
            action="delete",
            description="Delete users",
        ),
        # Extended permissions
        Permission(
            id="flows:export_flow",
            resource_type="flows",
            action="export_flow",
            description="Export flows to external formats",
        ),
        Permission(
            id="environments:deploy_environment",
            resource_type="environments",
            action="deploy_environment",
            description="Deploy flows to environments",
        ),
        Permission(
            id="workspaces:invite_users",
            resource_type="workspaces",
            action="invite_users",
            description="Invite users to workspaces",
        ),
        Permission(
            id="components:modify_component_settings",
            resource_type="components",
            action="modify_component_settings",
            description="Modify component settings",
        ),
        Permission(
            id="api_keys:manage_tokens",
            resource_type="api_keys",
            action="manage_tokens",
            description="Manage API tokens",
        ),
    ]

    # Add all permissions to the session
    for permission in permissions:
        # Check if permission already exists to avoid duplicates
        existing = session.get(Permission, permission.id)
        if not existing:
            session.add(permission)

    session.commit()
    print(f"Seeded {len(permissions)} permissions successfully")


if __name__ == "__main__":
    # This would be called from database initialization
    # For now, this is a standalone script that requires database connection
    print("Permission seeding script ready. Use from database initialization context.")
