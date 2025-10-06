"""
CRUD operations for Role Templates
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.role_template.model import RoleTemplate


async def create_role_template(
    db: AsyncSession,
    name: str,
    display_name: str,
    description: str,
    permissions: list[str],
    created_by: UUID | str | None = None,
    category: str = "standard",
    icon: str | None = None,
    is_system: bool = False,
) -> RoleTemplate:
    """Create a role template."""
    template = RoleTemplate(
        name=name,
        display_name=display_name,
        description=description,
        permissions=permissions,
        category=category,
        icon=icon,
        is_system=is_system,
        created_by=str(created_by) if created_by else None,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


async def get_role_template_by_id(
    db: AsyncSession,
    template_id: UUID | str,
) -> RoleTemplate | None:
    """Get role template by ID."""
    stmt = select(RoleTemplate).where(RoleTemplate.id == str(template_id))
    return (await db.exec(stmt)).first()


async def get_role_template_by_name(
    db: AsyncSession,
    name: str,
) -> RoleTemplate | None:
    """Get role template by name."""
    stmt = select(RoleTemplate).where(RoleTemplate.name == name)
    return (await db.exec(stmt)).first()


async def list_role_templates(
    db: AsyncSession,
    category: str | None = None,
    active_only: bool = True,
) -> list[RoleTemplate]:
    """List role templates."""
    stmt = select(RoleTemplate)

    if category:
        stmt = stmt.where(RoleTemplate.category == category)

    if active_only:
        stmt = stmt.where(RoleTemplate.is_active == True)  # noqa: E712

    stmt = stmt.order_by(RoleTemplate.usage_count.desc(), RoleTemplate.name)
    return list((await db.exec(stmt)).all())


async def update_role_template(
    db: AsyncSession,
    template_id: UUID | str,
    **updates,
) -> RoleTemplate | None:
    """Update role template."""
    template = await get_role_template_by_id(db, template_id)
    if not template:
        return None

    # Don't allow updating system templates
    if template.is_system and not updates.get("allow_system_update", False):
        return None

    for key, value in updates.items():
        if hasattr(template, key) and key != "allow_system_update":
            setattr(template, key, value)

    template.updated_at = datetime.now(timezone.utc)
    template.version += 1

    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


async def delete_role_template(
    db: AsyncSession,
    template_id: UUID | str,
) -> bool:
    """Delete role template (cannot delete system templates)."""
    template = await get_role_template_by_id(db, template_id)
    if not template or template.is_system:
        return False

    await db.delete(template)
    await db.commit()
    return True


async def increment_template_usage(
    db: AsyncSession,
    template_id: UUID | str,
) -> None:
    """Increment usage count for a template."""
    template = await get_role_template_by_id(db, template_id)
    if template:
        template.usage_count += 1
        db.add(template)
        await db.commit()


async def seed_system_templates(db: AsyncSession) -> None:
    """Seed default system role templates."""
    system_templates = [
        {
            "name": "viewer",
            "display_name": "Viewer",
            "description": "Read-only access to all resources",
            "permissions": [
                "flows:read",
                "projects:read",
                "components:read",
            ],
            "category": "standard",
            "icon": "Eye",
            "is_system": True,
        },
        {
            "name": "editor",
            "display_name": "Editor",
            "description": "Full edit access to resources without admin privileges",
            "permissions": [
                "flows:read",
                "flows:write",
                "flows:execute",
                "projects:read",
                "projects:write",
                "components:read",
                "components:write",
            ],
            "category": "standard",
            "icon": "Edit",
            "is_system": True,
        },
        {
            "name": "admin",
            "display_name": "Admin",
            "description": "Full administrative access including user management",
            "permissions": [
                "flows:read",
                "flows:write",
                "flows:execute",
                "flows:delete",
                "projects:read",
                "projects:write",
                "projects:delete",
                "components:read",
                "components:write",
                "components:delete",
                "users:read",
                "users:write",
                "roles:read",
                "roles:write",
            ],
            "category": "standard",
            "icon": "Shield",
            "is_system": True,
        },
        {
            "name": "developer",
            "display_name": "Developer",
            "description": "Development access with execution and testing permissions",
            "permissions": [
                "flows:read",
                "flows:write",
                "flows:execute",
                "components:read",
                "components:write",
            ],
            "category": "standard",
            "icon": "Code",
            "is_system": True,
        },
    ]

    for template_data in system_templates:
        existing = await get_role_template_by_name(db, template_data["name"])
        if not existing:
            await create_role_template(db=db, **template_data)
