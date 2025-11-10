"""
Unit tests for RBAC models (Permission, Role, RolePermission, and UserRoleAssignment).

These tests verify model creation, validation, schema operations,
and database constraints for the Role-Based Access Control system.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from langbuilder.services.database.models.rbac import (
    Permission,
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
    Role,
    RoleCreate,
    RoleRead,
    RoleUpdate,
    RolePermission,
    RolePermissionCreate,
    RolePermissionRead,
    RolePermissionUpdate,
    UserRoleAssignment,
    UserRoleAssignmentCreate,
    UserRoleAssignmentRead,
    UserRoleAssignmentUpdate,
)
from langbuilder.services.database.models.user.model import User
from langbuilder.services.auth.utils import get_password_hash
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select


# Permission Model Tests


@pytest.mark.asyncio
async def test_permission_creation_basic(async_session: AsyncSession):
    """Test basic permission creation with all required fields."""
    permission = Permission(
        name="Create",
        description="Allows creation of resources",
        scope_type="Flow",
    )

    async_session.add(permission)
    await async_session.commit()
    await async_session.refresh(permission)

    assert permission.id is not None
    assert isinstance(permission.id, UUID)
    assert permission.name == "Create"
    assert permission.description == "Allows creation of resources"
    assert permission.scope_type == "Flow"


@pytest.mark.asyncio
async def test_permission_creation_minimal(async_session: AsyncSession):
    """Test permission creation with minimal fields (no description)."""
    permission = Permission(
        name="Read",
        scope_type="Project",
    )

    async_session.add(permission)
    await async_session.commit()
    await async_session.refresh(permission)

    assert permission.id is not None
    assert permission.name == "Read"
    assert permission.description is None
    assert permission.scope_type == "Project"


@pytest.mark.asyncio
async def test_permission_name_not_globally_unique(async_session: AsyncSession):
    """Test that permission names can be reused across different scope types."""
    permission1 = Permission(name="Update", scope_type="Flow")
    async_session.add(permission1)
    await async_session.commit()

    # Create another permission with the same name but different scope_type
    # This should succeed since names are only unique within a scope_type
    permission2 = Permission(name="Update", scope_type="Project")
    async_session.add(permission2)
    await async_session.commit()  # Should not raise IntegrityError

    # Verify both were created
    from sqlmodel import select
    stmt = select(Permission).where(Permission.name == "Update")
    result = await async_session.exec(stmt)
    permissions = result.all()
    assert len(permissions) == 2
    assert {p.scope_type for p in permissions} == {"Flow", "Project"}


@pytest.mark.asyncio
async def test_permission_name_indexed(async_session: AsyncSession):
    """Test that permission name is indexed for efficient queries."""
    # Create multiple permissions
    permissions = [
        Permission(name=f"Permission_{i}", scope_type="Flow")
        for i in range(10)
    ]
    for p in permissions:
        async_session.add(p)
    await async_session.commit()

    # Query by name should be efficient due to index
    stmt = select(Permission).where(Permission.name == "Permission_5")
    result = await async_session.exec(stmt)
    permission = result.first()

    assert permission is not None
    assert permission.name == "Permission_5"


@pytest.mark.asyncio
async def test_permission_scope_type_indexed(async_session: AsyncSession):
    """Test that scope_type is indexed for efficient queries."""
    # Create permissions with different scope types
    permissions = [
        Permission(name=f"Perm_Flow_{i}", scope_type="Flow") for i in range(5)
    ] + [
        Permission(name=f"Perm_Project_{i}", scope_type="Project") for i in range(5)
    ]
    for p in permissions:
        async_session.add(p)
    await async_session.commit()

    # Query by scope_type should be efficient due to index
    stmt = select(Permission).where(Permission.scope_type == "Flow")
    result = await async_session.exec(stmt)
    flow_permissions = result.all()

    assert len(flow_permissions) == 5
    assert all(p.scope_type == "Flow" for p in flow_permissions)


@pytest.mark.asyncio
async def test_permission_default_id_generation(async_session: AsyncSession):
    """Test that permission IDs are auto-generated as UUIDs."""
    permission1 = Permission(name="Delete", scope_type="Global")
    permission2 = Permission(name="Archive", scope_type="Global")

    async_session.add(permission1)
    async_session.add(permission2)
    await async_session.commit()

    assert permission1.id != permission2.id
    assert isinstance(permission1.id, UUID)
    assert isinstance(permission2.id, UUID)


def test_permission_create_schema():
    """Test PermissionCreate schema validation."""
    permission_create = PermissionCreate(
        name="Create",
        description="Create permission",
        scope_type="Flow",
    )

    assert permission_create.name == "Create"
    assert permission_create.description == "Create permission"
    assert permission_create.scope_type == "Flow"


def test_permission_create_schema_minimal():
    """Test PermissionCreate schema with minimal fields."""
    permission_create = PermissionCreate(
        name="Read",
        scope_type="Project",
    )

    assert permission_create.name == "Read"
    assert permission_create.description is None
    assert permission_create.scope_type == "Project"


def test_permission_read_schema():
    """Test PermissionRead schema validation."""
    permission_id = uuid4()
    permission_read = PermissionRead(
        id=permission_id,
        name="Update",
        description="Update permission",
        scope_type="Flow",
    )

    assert permission_read.id == permission_id
    assert permission_read.name == "Update"
    assert permission_read.description == "Update permission"
    assert permission_read.scope_type == "Flow"


def test_permission_update_schema_all_fields():
    """Test PermissionUpdate schema with all fields."""
    permission_update = PermissionUpdate(
        name="NewName",
        description="New description",
        scope_type="NewScope",
    )

    assert permission_update.name == "NewName"
    assert permission_update.description == "New description"
    assert permission_update.scope_type == "NewScope"


def test_permission_update_schema_partial():
    """Test PermissionUpdate schema with partial updates."""
    permission_update = PermissionUpdate(name="NewName")

    assert permission_update.name == "NewName"
    assert permission_update.description is None
    assert permission_update.scope_type is None


def test_permission_update_schema_empty():
    """Test PermissionUpdate schema with no fields."""
    permission_update = PermissionUpdate()

    assert permission_update.name is None
    assert permission_update.description is None
    assert permission_update.scope_type is None


# Role Model Tests


@pytest.mark.asyncio
async def test_role_creation_basic(async_session: AsyncSession):
    """Test basic role creation with all required fields."""
    role = Role(
        name="Admin",
        description="Administrator role with full access",
        is_system=True,
    )

    async_session.add(role)
    await async_session.commit()
    await async_session.refresh(role)

    assert role.id is not None
    assert isinstance(role.id, UUID)
    assert role.name == "Admin"
    assert role.description == "Administrator role with full access"
    assert role.is_system is True


@pytest.mark.asyncio
async def test_role_creation_minimal(async_session: AsyncSession):
    """Test role creation with minimal fields."""
    role = Role(name="CustomRole")

    async_session.add(role)
    await async_session.commit()
    await async_session.refresh(role)

    assert role.id is not None
    assert role.name == "CustomRole"
    assert role.description is None
    assert role.is_system is True  # Default value


@pytest.mark.asyncio
async def test_role_creation_non_system(async_session: AsyncSession):
    """Test role creation with is_system=False."""
    role = Role(
        name="CustomEditor",
        description="Custom editor role",
        is_system=False,
    )

    async_session.add(role)
    await async_session.commit()
    await async_session.refresh(role)

    assert role.is_system is False


@pytest.mark.asyncio
async def test_role_unique_name_constraint(async_session: AsyncSession):
    """Test that role names must be unique."""
    role1 = Role(name="Owner", is_system=True)
    async_session.add(role1)
    await async_session.commit()

    # Try to create another role with the same name
    role2 = Role(name="Owner", is_system=False)
    async_session.add(role2)

    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_role_name_indexed(async_session: AsyncSession):
    """Test that role name is indexed for efficient queries."""
    # Create multiple roles
    roles = [
        Role(name=f"Role_{i}", is_system=False)
        for i in range(10)
    ]
    for r in roles:
        async_session.add(r)
    await async_session.commit()

    # Query by name should be efficient due to index
    stmt = select(Role).where(Role.name == "Role_5")
    result = await async_session.exec(stmt)
    role = result.first()

    assert role is not None
    assert role.name == "Role_5"


@pytest.mark.asyncio
async def test_role_default_id_generation(async_session: AsyncSession):
    """Test that role IDs are auto-generated as UUIDs."""
    role1 = Role(name="Editor", is_system=True)
    role2 = Role(name="Viewer", is_system=True)

    async_session.add(role1)
    async_session.add(role2)
    await async_session.commit()

    assert role1.id != role2.id
    assert isinstance(role1.id, UUID)
    assert isinstance(role2.id, UUID)


@pytest.mark.asyncio
async def test_role_is_system_flag(async_session: AsyncSession):
    """Test is_system flag for system vs custom roles."""
    system_role = Role(name="SystemRole", is_system=True)
    custom_role = Role(name="CustomRole", is_system=False)

    async_session.add(system_role)
    async_session.add(custom_role)
    await async_session.commit()

    # Query system roles
    stmt = select(Role).where(Role.is_system == True)  # noqa: E712
    result = await async_session.exec(stmt)
    system_roles = result.all()

    assert any(r.name == "SystemRole" for r in system_roles)


def test_role_create_schema():
    """Test RoleCreate schema validation."""
    role_create = RoleCreate(
        name="Admin",
        description="Admin role",
        is_system=True,
    )

    assert role_create.name == "Admin"
    assert role_create.description == "Admin role"
    assert role_create.is_system is True


def test_role_create_schema_default_is_system():
    """Test RoleCreate schema with default is_system value."""
    role_create = RoleCreate(
        name="CustomRole",
        description="Custom role",
    )

    assert role_create.is_system is False  # Default for Create schema


def test_role_create_schema_minimal():
    """Test RoleCreate schema with minimal fields."""
    role_create = RoleCreate(name="MinimalRole")

    assert role_create.name == "MinimalRole"
    assert role_create.description is None


def test_role_read_schema():
    """Test RoleRead schema validation."""
    role_id = uuid4()
    role_read = RoleRead(
        id=role_id,
        name="Owner",
        description="Owner role",
        is_system=True,
    )

    assert role_read.id == role_id
    assert role_read.name == "Owner"
    assert role_read.description == "Owner role"
    assert role_read.is_system is True


def test_role_update_schema_all_fields():
    """Test RoleUpdate schema with all fields."""
    role_update = RoleUpdate(
        name="NewRoleName",
        description="New description",
        is_system=False,
    )

    assert role_update.name == "NewRoleName"
    assert role_update.description == "New description"
    assert role_update.is_system is False


def test_role_update_schema_partial():
    """Test RoleUpdate schema with partial updates."""
    role_update = RoleUpdate(description="Updated description")

    assert role_update.name is None
    assert role_update.description == "Updated description"
    assert role_update.is_system is None


def test_role_update_schema_empty():
    """Test RoleUpdate schema with no fields."""
    role_update = RoleUpdate()

    assert role_update.name is None
    assert role_update.description is None
    assert role_update.is_system is None


# Integration Tests


@pytest.mark.asyncio
async def test_create_complete_rbac_set(async_session: AsyncSession):
    """Test creating a complete set of RBAC entities."""
    # Create permissions for Flow scope
    flow_permissions = [
        Permission(name="Flow:Create", scope_type="Flow", description="Create flows"),
        Permission(name="Flow:Read", scope_type="Flow", description="Read flows"),
        Permission(name="Flow:Update", scope_type="Flow", description="Update flows"),
        Permission(name="Flow:Delete", scope_type="Flow", description="Delete flows"),
    ]

    # Create permissions for Project scope
    project_permissions = [
        Permission(name="Project:Create", scope_type="Project", description="Create projects"),
        Permission(name="Project:Read", scope_type="Project", description="Read projects"),
        Permission(name="Project:Update", scope_type="Project", description="Update projects"),
        Permission(name="Project:Delete", scope_type="Project", description="Delete projects"),
    ]

    # Create roles
    roles = [
        Role(name="Admin", description="Full system access", is_system=True),
        Role(name="Owner", description="Owner of resources", is_system=True),
        Role(name="Editor", description="Can edit resources", is_system=True),
        Role(name="Viewer", description="Can view resources", is_system=True),
    ]

    # Add all to database
    for permission in flow_permissions + project_permissions:
        async_session.add(permission)
    for role in roles:
        async_session.add(role)

    await async_session.commit()

    # Verify all entities were created
    permission_count = len((await async_session.exec(select(Permission))).all())
    role_count = len((await async_session.exec(select(Role))).all())

    assert permission_count == 8
    assert role_count == 4


@pytest.mark.asyncio
async def test_query_permissions_by_scope(async_session: AsyncSession):
    """Test querying permissions by scope type."""
    # Create permissions with different scopes
    permissions = [
        Permission(name="Global:Admin", scope_type="Global"),
        Permission(name="Flow:Create", scope_type="Flow"),
        Permission(name="Flow:Read", scope_type="Flow"),
        Permission(name="Project:Create", scope_type="Project"),
    ]

    for permission in permissions:
        async_session.add(permission)
    await async_session.commit()

    # Query Flow permissions
    stmt = select(Permission).where(Permission.scope_type == "Flow")
    flow_perms = (await async_session.exec(stmt)).all()

    assert len(flow_perms) == 2
    assert all(p.scope_type == "Flow" for p in flow_perms)


@pytest.mark.asyncio
async def test_query_system_roles(async_session: AsyncSession):
    """Test querying system vs custom roles."""
    # Create mix of system and custom roles
    roles = [
        Role(name="Admin", is_system=True),
        Role(name="Owner", is_system=True),
        Role(name="CustomRole1", is_system=False),
        Role(name="CustomRole2", is_system=False),
    ]

    for role in roles:
        async_session.add(role)
    await async_session.commit()

    # Query system roles
    stmt = select(Role).where(Role.is_system == True)  # noqa: E712
    system_roles = (await async_session.exec(stmt)).all()

    assert len(system_roles) == 2
    assert all(r.is_system for r in system_roles)

    # Query custom roles
    stmt = select(Role).where(Role.is_system == False)  # noqa: E712
    custom_roles = (await async_session.exec(stmt)).all()

    assert len(custom_roles) == 2
    assert not any(r.is_system for r in custom_roles)


@pytest.mark.asyncio
async def test_permission_update_in_database(async_session: AsyncSession):
    """Test updating a permission in the database."""
    # Create permission
    permission = Permission(name="TestPerm", scope_type="Flow", description="Original")
    async_session.add(permission)
    await async_session.commit()
    permission_id = permission.id

    # Update permission
    permission.description = "Updated description"
    permission.scope_type = "Project"
    await async_session.commit()
    await async_session.refresh(permission)

    # Verify update
    assert permission.id == permission_id
    assert permission.description == "Updated description"
    assert permission.scope_type == "Project"


@pytest.mark.asyncio
async def test_role_update_in_database(async_session: AsyncSession):
    """Test updating a role in the database."""
    # Create role
    role = Role(name="TestRole", description="Original", is_system=False)
    async_session.add(role)
    await async_session.commit()
    role_id = role.id

    # Update role
    role.description = "Updated description"
    role.is_system = True
    await async_session.commit()
    await async_session.refresh(role)

    # Verify update
    assert role.id == role_id
    assert role.description == "Updated description"
    assert role.is_system is True


@pytest.mark.asyncio
async def test_permission_deletion(async_session: AsyncSession):
    """Test deleting a permission from the database."""
    # Create permission
    permission = Permission(name="DeleteMe", scope_type="Flow")
    async_session.add(permission)
    await async_session.commit()
    permission_id = permission.id

    # Delete permission
    await async_session.delete(permission)
    await async_session.commit()

    # Verify deletion
    stmt = select(Permission).where(Permission.id == permission_id)
    result = await async_session.exec(stmt)
    deleted_permission = result.first()

    assert deleted_permission is None


@pytest.mark.asyncio
async def test_role_deletion(async_session: AsyncSession):
    """Test deleting a role from the database."""
    # Create role
    role = Role(name="DeleteMe", is_system=False)
    async_session.add(role)
    await async_session.commit()
    role_id = role.id

    # Delete role
    await async_session.delete(role)
    await async_session.commit()

    # Verify deletion
    stmt = select(Role).where(Role.id == role_id)
    result = await async_session.exec(stmt)
    deleted_role = result.first()

    assert deleted_role is None


# RolePermission Model Tests


@pytest.mark.asyncio
async def test_role_permission_creation_basic(async_session: AsyncSession):
    """Test basic role-permission mapping creation."""
    # Create role and permission first
    role = Role(name="Editor", is_system=True)
    permission = Permission(name="Update", scope_type="Flow")
    async_session.add(role)
    async_session.add(permission)
    await async_session.commit()

    # Create role-permission mapping
    role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
    async_session.add(role_permission)
    await async_session.commit()
    await async_session.refresh(role_permission)

    assert role_permission.id is not None
    assert isinstance(role_permission.id, UUID)
    assert role_permission.role_id == role.id
    assert role_permission.permission_id == permission.id


@pytest.mark.asyncio
async def test_role_permission_unique_constraint(async_session: AsyncSession):
    """Test that duplicate role-permission mappings are prevented."""
    # Create role and permission
    role = Role(name="Viewer", is_system=True)
    permission = Permission(name="Read", scope_type="Flow")
    async_session.add(role)
    async_session.add(permission)
    await async_session.commit()

    # Create first mapping
    role_permission1 = RolePermission(role_id=role.id, permission_id=permission.id)
    async_session.add(role_permission1)
    await async_session.commit()

    # Try to create duplicate mapping
    role_permission2 = RolePermission(role_id=role.id, permission_id=permission.id)
    async_session.add(role_permission2)

    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_role_permission_foreign_key_constraints(async_session: AsyncSession):
    """Test that foreign key constraints are properly defined."""
    # Create a valid role and permission
    role = Role(name="TestRole", is_system=True)
    permission = Permission(name="TestPerm", scope_type="Flow")
    async_session.add(role)
    async_session.add(permission)
    await async_session.commit()

    # Create a valid role-permission mapping
    role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
    async_session.add(role_permission)
    await async_session.commit()
    await async_session.refresh(role_permission)

    # Verify the foreign key relationships are properly established
    assert role_permission.role_id == role.id
    assert role_permission.permission_id == permission.id

    # Verify that we can query the mapping by foreign keys
    stmt = select(RolePermission).where(
        RolePermission.role_id == role.id,
        RolePermission.permission_id == permission.id
    )
    result = await async_session.exec(stmt)
    found_mapping = result.first()
    assert found_mapping is not None
    assert found_mapping.id == role_permission.id


@pytest.mark.asyncio
async def test_role_permission_relationship_traversal_from_role(async_session: AsyncSession):
    """Test traversing from role to permissions through role_permissions."""
    # Create role
    role = Role(name="Owner", is_system=True)
    async_session.add(role)
    await async_session.commit()

    # Create permissions
    permissions = [
        Permission(name="Create", scope_type="Flow"),
        Permission(name="Read", scope_type="Flow"),
        Permission(name="Update", scope_type="Flow"),
        Permission(name="Delete", scope_type="Flow"),
    ]
    for perm in permissions:
        async_session.add(perm)
    await async_session.commit()

    # Create role-permission mappings
    for perm in permissions:
        role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
        async_session.add(role_perm)
    await async_session.commit()

    # Query role with eager loading of relationships
    stmt = select(Role).where(Role.id == role.id).options(selectinload(Role.role_permissions))
    result = await async_session.exec(stmt)
    role = result.first()

    # Verify relationship traversal
    assert len(role.role_permissions) == 4
    assert all(isinstance(rp, RolePermission) for rp in role.role_permissions)
    assert all(rp.role_id == role.id for rp in role.role_permissions)


@pytest.mark.asyncio
async def test_role_permission_relationship_traversal_from_permission(async_session: AsyncSession):
    """Test traversing from permission to roles through role_permissions."""
    # Create permission
    permission = Permission(name="Execute", scope_type="Flow")
    async_session.add(permission)
    await async_session.commit()

    # Create roles
    roles = [
        Role(name="Admin", is_system=True),
        Role(name="Owner", is_system=True),
        Role(name="Editor", is_system=True),
    ]
    for role in roles:
        async_session.add(role)
    await async_session.commit()

    # Create role-permission mappings
    for role in roles:
        role_perm = RolePermission(role_id=role.id, permission_id=permission.id)
        async_session.add(role_perm)
    await async_session.commit()

    # Query permission with eager loading of relationships
    stmt = select(Permission).where(Permission.id == permission.id).options(selectinload(Permission.role_permissions))
    result = await async_session.exec(stmt)
    permission = result.first()

    # Verify relationship traversal
    assert len(permission.role_permissions) == 3
    assert all(isinstance(rp, RolePermission) for rp in permission.role_permissions)
    assert all(rp.permission_id == permission.id for rp in permission.role_permissions)


@pytest.mark.asyncio
async def test_role_permission_bidirectional_relationship(async_session: AsyncSession):
    """Test bidirectional relationship between role and permission."""
    # Create role and permission
    role = Role(name="Editor", is_system=True)
    permission = Permission(name="Update", scope_type="Project")
    async_session.add(role)
    async_session.add(permission)
    await async_session.commit()

    # Create role-permission mapping
    role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
    async_session.add(role_permission)
    await async_session.commit()
    await async_session.refresh(role_permission)

    # Query with eager loading
    stmt_role = select(Role).where(Role.id == role.id).options(selectinload(Role.role_permissions))
    result_role = await async_session.exec(stmt_role)
    role = result_role.first()

    stmt_perm = select(Permission).where(Permission.id == permission.id).options(selectinload(Permission.role_permissions))
    result_perm = await async_session.exec(stmt_perm)
    permission = result_perm.first()

    # Verify bidirectional relationship
    assert len(role.role_permissions) == 1
    assert role.role_permissions[0].permission_id == permission.id

    assert len(permission.role_permissions) == 1
    assert permission.role_permissions[0].role_id == role.id


@pytest.mark.asyncio
async def test_role_permission_indexes(async_session: AsyncSession):
    """Test that role_id and permission_id are indexed for efficient queries."""
    # Create multiple roles and permissions
    roles = [Role(name=f"Role_{i}", is_system=False) for i in range(5)]
    permissions = [Permission(name=f"Perm_{i}", scope_type="Flow") for i in range(5)]

    for role in roles:
        async_session.add(role)
    for perm in permissions:
        async_session.add(perm)
    await async_session.commit()

    # Create role-permission mappings
    for role in roles:
        for perm in permissions:
            rp = RolePermission(role_id=role.id, permission_id=perm.id)
            async_session.add(rp)
    await async_session.commit()

    # Query by role_id (should use index)
    stmt = select(RolePermission).where(RolePermission.role_id == roles[0].id)
    result = await async_session.exec(stmt)
    role_perms = result.all()
    assert len(role_perms) == 5

    # Query by permission_id (should use index)
    stmt = select(RolePermission).where(RolePermission.permission_id == permissions[0].id)
    result = await async_session.exec(stmt)
    perm_roles = result.all()
    assert len(perm_roles) == 5


@pytest.mark.asyncio
async def test_role_permission_deletion(async_session: AsyncSession):
    """Test deleting a role-permission mapping."""
    # Create role and permission
    role = Role(name="Temp", is_system=False)
    permission = Permission(name="TempPerm", scope_type="Global")
    async_session.add(role)
    async_session.add(permission)
    await async_session.commit()

    # Create mapping
    role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
    async_session.add(role_permission)
    await async_session.commit()
    mapping_id = role_permission.id

    # Delete mapping
    await async_session.delete(role_permission)
    await async_session.commit()

    # Verify deletion
    stmt = select(RolePermission).where(RolePermission.id == mapping_id)
    result = await async_session.exec(stmt)
    deleted_mapping = result.first()
    assert deleted_mapping is None


@pytest.mark.asyncio
async def test_role_permission_default_id_generation(async_session: AsyncSession):
    """Test that role-permission IDs are auto-generated as UUIDs."""
    # Create role and permission
    role = Role(name="TestRole", is_system=True)
    permission1 = Permission(name="TestPerm1", scope_type="Flow")
    permission2 = Permission(name="TestPerm2", scope_type="Flow")
    async_session.add(role)
    async_session.add(permission1)
    async_session.add(permission2)
    await async_session.commit()

    # Create mappings
    rp1 = RolePermission(role_id=role.id, permission_id=permission1.id)
    rp2 = RolePermission(role_id=role.id, permission_id=permission2.id)
    async_session.add(rp1)
    async_session.add(rp2)
    await async_session.commit()

    assert rp1.id != rp2.id
    assert isinstance(rp1.id, UUID)
    assert isinstance(rp2.id, UUID)


def test_role_permission_create_schema():
    """Test RolePermissionCreate schema validation."""
    role_id = uuid4()
    permission_id = uuid4()
    rp_create = RolePermissionCreate(role_id=role_id, permission_id=permission_id)

    assert rp_create.role_id == role_id
    assert rp_create.permission_id == permission_id


def test_role_permission_read_schema():
    """Test RolePermissionRead schema validation."""
    rp_id = uuid4()
    role_id = uuid4()
    permission_id = uuid4()
    rp_read = RolePermissionRead(id=rp_id, role_id=role_id, permission_id=permission_id)

    assert rp_read.id == rp_id
    assert rp_read.role_id == role_id
    assert rp_read.permission_id == permission_id


def test_role_permission_update_schema_all_fields():
    """Test RolePermissionUpdate schema with all fields."""
    role_id = uuid4()
    permission_id = uuid4()
    rp_update = RolePermissionUpdate(role_id=role_id, permission_id=permission_id)

    assert rp_update.role_id == role_id
    assert rp_update.permission_id == permission_id


def test_role_permission_update_schema_partial():
    """Test RolePermissionUpdate schema with partial updates."""
    role_id = uuid4()
    rp_update = RolePermissionUpdate(role_id=role_id)

    assert rp_update.role_id == role_id
    assert rp_update.permission_id is None


def test_role_permission_update_schema_empty():
    """Test RolePermissionUpdate schema with no fields."""
    rp_update = RolePermissionUpdate()

    assert rp_update.role_id is None
    assert rp_update.permission_id is None


# Integration Tests for RolePermission


@pytest.mark.asyncio
async def test_complete_rbac_setup_with_mappings(async_session: AsyncSession):
    """Test creating a complete RBAC setup with role-permission mappings."""
    # Create permissions
    permissions = [
        Permission(name="Flow:Create", scope_type="Flow", description="Create flows"),
        Permission(name="Flow:Read", scope_type="Flow", description="Read flows"),
        Permission(name="Flow:Update", scope_type="Flow", description="Update flows"),
        Permission(name="Flow:Delete", scope_type="Flow", description="Delete flows"),
    ]
    for perm in permissions:
        async_session.add(perm)
    await async_session.commit()

    # Create roles
    admin = Role(name="Admin", description="Full access", is_system=True)
    owner = Role(name="Owner", description="Owner access", is_system=True)
    editor = Role(name="Editor", description="Edit access", is_system=True)
    viewer = Role(name="Viewer", description="View access", is_system=True)

    async_session.add(admin)
    async_session.add(owner)
    async_session.add(editor)
    async_session.add(viewer)
    await async_session.commit()

    # Map permissions to roles
    # Admin and Owner get all permissions
    for role in [admin, owner]:
        for perm in permissions:
            rp = RolePermission(role_id=role.id, permission_id=perm.id)
            async_session.add(rp)

    # Editor gets Create, Read, Update (not Delete)
    for perm in permissions[:3]:
        rp = RolePermission(role_id=editor.id, permission_id=perm.id)
        async_session.add(rp)

    # Viewer gets only Read
    rp = RolePermission(role_id=viewer.id, permission_id=permissions[1].id)
    async_session.add(rp)

    await async_session.commit()

    # Query roles with eager loading to verify mappings
    stmt_admin = select(Role).where(Role.id == admin.id).options(selectinload(Role.role_permissions))
    stmt_owner = select(Role).where(Role.id == owner.id).options(selectinload(Role.role_permissions))
    stmt_editor = select(Role).where(Role.id == editor.id).options(selectinload(Role.role_permissions))
    stmt_viewer = select(Role).where(Role.id == viewer.id).options(selectinload(Role.role_permissions))

    admin = (await async_session.exec(stmt_admin)).first()
    owner = (await async_session.exec(stmt_owner)).first()
    editor = (await async_session.exec(stmt_editor)).first()
    viewer = (await async_session.exec(stmt_viewer)).first()

    assert len(admin.role_permissions) == 4
    assert len(owner.role_permissions) == 4
    assert len(editor.role_permissions) == 3
    assert len(viewer.role_permissions) == 1


@pytest.mark.asyncio
async def test_query_permissions_by_role(async_session: AsyncSession):
    """Test querying all permissions for a specific role."""
    # Create role and permissions
    role = Role(name="TestRole", is_system=True)
    permissions = [
        Permission(name=f"TestPerm_{i}", scope_type="Flow") for i in range(3)
    ]
    async_session.add(role)
    for perm in permissions:
        async_session.add(perm)
    await async_session.commit()

    # Create mappings
    for perm in permissions:
        rp = RolePermission(role_id=role.id, permission_id=perm.id)
        async_session.add(rp)
    await async_session.commit()

    # Query all permissions for the role
    stmt = select(RolePermission).where(RolePermission.role_id == role.id)
    result = await async_session.exec(stmt)
    role_perms = result.all()

    assert len(role_perms) == 3
    assert all(rp.role_id == role.id for rp in role_perms)


@pytest.mark.asyncio
async def test_query_roles_by_permission(async_session: AsyncSession):
    """Test querying all roles that have a specific permission."""
    # Create permission and roles
    permission = Permission(name="SharedPerm", scope_type="Flow")
    roles = [Role(name=f"TestRole_{i}", is_system=False) for i in range(3)]
    async_session.add(permission)
    for role in roles:
        async_session.add(role)
    await async_session.commit()

    # Create mappings
    for role in roles:
        rp = RolePermission(role_id=role.id, permission_id=permission.id)
        async_session.add(rp)
    await async_session.commit()

    # Query all roles for the permission
    stmt = select(RolePermission).where(RolePermission.permission_id == permission.id)
    result = await async_session.exec(stmt)
    perm_roles = result.all()

    assert len(perm_roles) == 3
    assert all(rp.permission_id == permission.id for rp in perm_roles)


# UserRoleAssignment Model Tests


@pytest.mark.asyncio
async def test_user_role_assignment_creation_basic(async_session: AsyncSession):
    """Test basic user role assignment creation with all required fields."""
    # Create user and role first
    user = User(username="testuser", password=get_password_hash("password"), is_active=True)
    role = Role(name="Owner", is_system=True)
    async_session.add(user)
    async_session.add(role)
    await async_session.commit()

    # Create user role assignment
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="project",
        scope_id=uuid4(),
        is_immutable=False,
    )
    async_session.add(assignment)
    await async_session.commit()
    await async_session.refresh(assignment)

    assert assignment.id is not None
    assert isinstance(assignment.id, UUID)
    assert assignment.user_id == user.id
    assert assignment.role_id == role.id
    assert assignment.scope_type == "project"
    assert assignment.scope_id is not None
    assert assignment.is_immutable is False
    assert assignment.created_at is not None
    assert isinstance(assignment.created_at, datetime)
    assert assignment.created_by is None


@pytest.mark.asyncio
async def test_user_role_assignment_global_scope(async_session: AsyncSession):
    """Test user role assignment with global scope (null scope_id)."""
    # Create user and role
    user = User(username="globaluser", password=get_password_hash("password"), is_active=True)
    role = Role(name="Admin", is_system=True)
    async_session.add(user)
    async_session.add(role)
    await async_session.commit()

    # Create global scope assignment
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="global",
        scope_id=None,
        is_immutable=False,
    )
    async_session.add(assignment)
    await async_session.commit()
    await async_session.refresh(assignment)

    assert assignment.scope_type == "global"
    assert assignment.scope_id is None


@pytest.mark.asyncio
async def test_user_role_assignment_project_scope(async_session: AsyncSession):
    """Test user role assignment with project scope."""
    # Create user and role
    user = User(username="projectuser", password=get_password_hash("password"), is_active=True)
    role = Role(name="Editor", is_system=True)
    async_session.add(user)
    async_session.add(role)
    await async_session.commit()

    # Create project scope assignment
    project_id = uuid4()
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="project",
        scope_id=project_id,
        is_immutable=False,
    )
    async_session.add(assignment)
    await async_session.commit()
    await async_session.refresh(assignment)

    assert assignment.scope_type == "project"
    assert assignment.scope_id == project_id


@pytest.mark.asyncio
async def test_user_role_assignment_flow_scope(async_session: AsyncSession):
    """Test user role assignment with flow scope."""
    # Create user and role
    user = User(username="flowuser", password=get_password_hash("password"), is_active=True)
    role = Role(name="Viewer", is_system=True)
    async_session.add(user)
    async_session.add(role)
    await async_session.commit()

    # Create flow scope assignment
    flow_id = uuid4()
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="flow",
        scope_id=flow_id,
        is_immutable=False,
    )
    async_session.add(assignment)
    await async_session.commit()
    await async_session.refresh(assignment)

    assert assignment.scope_type == "flow"
    assert assignment.scope_id == flow_id


@pytest.mark.asyncio
async def test_user_role_assignment_immutable_flag(async_session: AsyncSession):
    """Test user role assignment with is_immutable flag set to True."""
    # Create user and role
    user = User(username="immutableuser", password=get_password_hash("password"), is_active=True)
    role = Role(name="Owner", is_system=True)
    async_session.add(user)
    async_session.add(role)
    await async_session.commit()

    # Create immutable assignment (e.g., Starter Project Owner)
    project_id = uuid4()
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="project",
        scope_id=project_id,
        is_immutable=True,
    )
    async_session.add(assignment)
    await async_session.commit()
    await async_session.refresh(assignment)

    assert assignment.is_immutable is True


@pytest.mark.asyncio
async def test_user_role_assignment_with_created_by(async_session: AsyncSession):
    """Test user role assignment with created_by field."""
    # Create users and role
    user1 = User(username="user1", password=get_password_hash("password"), is_active=True)
    user2 = User(username="user2", password=get_password_hash("password"), is_active=True)
    role = Role(name="Editor", is_system=True)
    async_session.add(user1)
    async_session.add(user2)
    async_session.add(role)
    await async_session.commit()

    # Create assignment with created_by
    assignment = UserRoleAssignment(
        user_id=user1.id,
        role_id=role.id,
        scope_type="project",
        scope_id=uuid4(),
        is_immutable=False,
        created_by=user2.id,
    )
    async_session.add(assignment)
    await async_session.commit()
    await async_session.refresh(assignment)

    assert assignment.created_by == user2.id


@pytest.mark.asyncio
async def test_user_role_assignment_unique_constraint(async_session: AsyncSession):
    """Test that duplicate user-role-scope assignments are prevented."""
    # Create user and role
    user = User(username="uniqueuser", password=get_password_hash("password"), is_active=True)
    role = Role(name="Owner", is_system=True)
    async_session.add(user)
    async_session.add(role)
    await async_session.commit()

    # Create first assignment
    project_id = uuid4()
    assignment1 = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="project",
        scope_id=project_id,
        is_immutable=False,
    )
    async_session.add(assignment1)
    await async_session.commit()

    # Try to create duplicate assignment
    assignment2 = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="project",
        scope_id=project_id,
        is_immutable=False,
    )
    async_session.add(assignment2)

    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_user_role_assignment_foreign_key_constraints(async_session: AsyncSession):
    """Test that foreign key constraints are properly defined."""
    # Create user and role
    user = User(username="fkuser", password=get_password_hash("password"), is_active=True)
    role = Role(name="Editor", is_system=True)
    async_session.add(user)
    async_session.add(role)
    await async_session.commit()

    # Create assignment
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="global",
        scope_id=None,
        is_immutable=False,
    )
    async_session.add(assignment)
    await async_session.commit()
    await async_session.refresh(assignment)

    # Verify foreign key relationships
    assert assignment.user_id == user.id
    assert assignment.role_id == role.id

    # Verify we can query by foreign keys
    stmt = select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == user.id,
        UserRoleAssignment.role_id == role.id
    )
    result = await async_session.exec(stmt)
    found_assignment = result.first()
    assert found_assignment is not None
    assert found_assignment.id == assignment.id


@pytest.mark.asyncio
async def test_user_role_assignment_relationship_from_user(async_session: AsyncSession):
    """Test traversing from user to assignments."""
    # Create user and roles
    user = User(username="reluser", password=get_password_hash("password"), is_active=True)
    role1 = Role(name="Owner", is_system=True)
    role2 = Role(name="Editor", is_system=True)
    async_session.add(user)
    async_session.add(role1)
    async_session.add(role2)
    await async_session.commit()

    # Create multiple assignments for the user
    assignment1 = UserRoleAssignment(
        user_id=user.id,
        role_id=role1.id,
        scope_type="project",
        scope_id=uuid4(),
        is_immutable=False,
    )
    assignment2 = UserRoleAssignment(
        user_id=user.id,
        role_id=role2.id,
        scope_type="flow",
        scope_id=uuid4(),
        is_immutable=False,
    )
    async_session.add(assignment1)
    async_session.add(assignment2)
    await async_session.commit()

    # Query user with eager loading
    stmt = select(User).where(User.id == user.id).options(selectinload(User.role_assignments))
    result = await async_session.exec(stmt)
    user = result.first()

    # Verify relationship traversal
    assert len(user.role_assignments) == 2
    assert all(isinstance(a, UserRoleAssignment) for a in user.role_assignments)
    assert all(a.user_id == user.id for a in user.role_assignments)


@pytest.mark.asyncio
async def test_user_role_assignment_relationship_from_role(async_session: AsyncSession):
    """Test traversing from role to assignments."""
    # Create users and role
    user1 = User(username="user1rel", password=get_password_hash("password"), is_active=True)
    user2 = User(username="user2rel", password=get_password_hash("password"), is_active=True)
    role = Role(name="Viewer", is_system=True)
    async_session.add(user1)
    async_session.add(user2)
    async_session.add(role)
    await async_session.commit()

    # Create assignments for multiple users with same role
    assignment1 = UserRoleAssignment(
        user_id=user1.id,
        role_id=role.id,
        scope_type="project",
        scope_id=uuid4(),
        is_immutable=False,
    )
    assignment2 = UserRoleAssignment(
        user_id=user2.id,
        role_id=role.id,
        scope_type="project",
        scope_id=uuid4(),
        is_immutable=False,
    )
    async_session.add(assignment1)
    async_session.add(assignment2)
    await async_session.commit()

    # Query role with eager loading
    stmt = select(Role).where(Role.id == role.id).options(selectinload(Role.user_assignments))
    result = await async_session.exec(stmt)
    role = result.first()

    # Verify relationship traversal
    assert len(role.user_assignments) == 2
    assert all(isinstance(a, UserRoleAssignment) for a in role.user_assignments)
    assert all(a.role_id == role.id for a in role.user_assignments)


@pytest.mark.asyncio
async def test_user_role_assignment_bidirectional_relationship(async_session: AsyncSession):
    """Test bidirectional relationship between user, role, and assignment."""
    # Create user and role
    user = User(username="biuser", password=get_password_hash("password"), is_active=True)
    role = Role(name="Owner", is_system=True)
    async_session.add(user)
    async_session.add(role)
    await async_session.commit()

    # Create assignment
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="global",
        scope_id=None,
        is_immutable=False,
    )
    async_session.add(assignment)
    await async_session.commit()
    await async_session.refresh(assignment)

    # Query with eager loading
    stmt_user = select(User).where(User.id == user.id).options(selectinload(User.role_assignments))
    result_user = await async_session.exec(stmt_user)
    user = result_user.first()

    stmt_role = select(Role).where(Role.id == role.id).options(selectinload(Role.user_assignments))
    result_role = await async_session.exec(stmt_role)
    role = result_role.first()

    # Verify bidirectional relationships
    assert len(user.role_assignments) == 1
    assert user.role_assignments[0].role_id == role.id

    assert len(role.user_assignments) == 1
    assert role.user_assignments[0].user_id == user.id


@pytest.mark.asyncio
async def test_user_role_assignment_indexes(async_session: AsyncSession):
    """Test that user_id, role_id, scope_type, and scope_id are indexed."""
    # Create users and roles
    users = [
        User(username=f"idxuser{i}", password=get_password_hash("password"), is_active=True)
        for i in range(3)
    ]
    roles = [Role(name=f"IdxRole{i}", is_system=False) for i in range(3)]

    for user in users:
        async_session.add(user)
    for role in roles:
        async_session.add(role)
    await async_session.commit()

    # Create assignments
    project_id = uuid4()
    for user in users:
        for role in roles:
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type="project",
                scope_id=project_id,
                is_immutable=False,
            )
            async_session.add(assignment)
    await async_session.commit()

    # Query by user_id (should use index)
    stmt = select(UserRoleAssignment).where(UserRoleAssignment.user_id == users[0].id)
    result = await async_session.exec(stmt)
    user_assignments = result.all()
    assert len(user_assignments) == 3

    # Query by role_id (should use index)
    stmt = select(UserRoleAssignment).where(UserRoleAssignment.role_id == roles[0].id)
    result = await async_session.exec(stmt)
    role_assignments = result.all()
    assert len(role_assignments) == 3

    # Query by scope_type (should use index)
    stmt = select(UserRoleAssignment).where(UserRoleAssignment.scope_type == "project")
    result = await async_session.exec(stmt)
    project_assignments = result.all()
    assert len(project_assignments) == 9

    # Query by scope_id (should use index)
    stmt = select(UserRoleAssignment).where(UserRoleAssignment.scope_id == project_id)
    result = await async_session.exec(stmt)
    scope_assignments = result.all()
    assert len(scope_assignments) == 9


@pytest.mark.asyncio
async def test_user_role_assignment_composite_index_lookup(async_session: AsyncSession):
    """Test the composite index for permission check queries."""
    # Create user and roles
    user = User(username="lookupuser", password=get_password_hash("password"), is_active=True)
    role1 = Role(name="Role1", is_system=False)
    role2 = Role(name="Role2", is_system=False)
    async_session.add(user)
    async_session.add(role1)
    async_session.add(role2)
    await async_session.commit()

    # Create assignments for different scopes
    project_id = uuid4()
    flow_id = uuid4()

    assignments = [
        UserRoleAssignment(user_id=user.id, role_id=role1.id, scope_type="global", scope_id=None),
        UserRoleAssignment(user_id=user.id, role_id=role2.id, scope_type="project", scope_id=project_id),
        UserRoleAssignment(user_id=user.id, role_id=role1.id, scope_type="flow", scope_id=flow_id),
    ]
    for assignment in assignments:
        async_session.add(assignment)
    await async_session.commit()

    # Test composite index query (user_id + scope_type + scope_id)
    stmt = select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == user.id,
        UserRoleAssignment.scope_type == "project",
        UserRoleAssignment.scope_id == project_id,
    )
    result = await async_session.exec(stmt)
    found_assignments = result.all()

    assert len(found_assignments) == 1
    assert found_assignments[0].role_id == role2.id


@pytest.mark.asyncio
async def test_user_role_assignment_deletion(async_session: AsyncSession):
    """Test deleting a user role assignment."""
    # Create user and role
    user = User(username="deluser", password=get_password_hash("password"), is_active=True)
    role = Role(name="TempRole", is_system=False)
    async_session.add(user)
    async_session.add(role)
    await async_session.commit()

    # Create assignment
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="global",
        scope_id=None,
        is_immutable=False,
    )
    async_session.add(assignment)
    await async_session.commit()
    assignment_id = assignment.id

    # Delete assignment
    await async_session.delete(assignment)
    await async_session.commit()

    # Verify deletion
    stmt = select(UserRoleAssignment).where(UserRoleAssignment.id == assignment_id)
    result = await async_session.exec(stmt)
    deleted_assignment = result.first()
    assert deleted_assignment is None


@pytest.mark.asyncio
async def test_user_role_assignment_default_id_generation(async_session: AsyncSession):
    """Test that assignment IDs are auto-generated as UUIDs."""
    # Create user and role
    user = User(username="uuiduser", password=get_password_hash("password"), is_active=True)
    role = Role(name="UUIDRole", is_system=True)
    async_session.add(user)
    async_session.add(role)
    await async_session.commit()

    # Create two assignments
    assignment1 = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="project",
        scope_id=uuid4(),
        is_immutable=False,
    )
    assignment2 = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="flow",
        scope_id=uuid4(),
        is_immutable=False,
    )
    async_session.add(assignment1)
    async_session.add(assignment2)
    await async_session.commit()

    assert assignment1.id != assignment2.id
    assert isinstance(assignment1.id, UUID)
    assert isinstance(assignment2.id, UUID)


@pytest.mark.asyncio
async def test_user_role_assignment_created_at_default(async_session: AsyncSession):
    """Test that created_at is automatically set."""
    # Create user and role
    user = User(username="timeuser", password=get_password_hash("password"), is_active=True)
    role = Role(name="TimeRole", is_system=True)
    async_session.add(user)
    async_session.add(role)
    await async_session.commit()

    # Create first assignment
    assignment1 = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="global",
        scope_id=None,
        is_immutable=False,
    )
    async_session.add(assignment1)
    await async_session.commit()
    await async_session.refresh(assignment1)

    # Create second assignment a moment later
    assignment2 = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        scope_type="project",
        scope_id=uuid4(),
        is_immutable=False,
    )
    async_session.add(assignment2)
    await async_session.commit()
    await async_session.refresh(assignment2)

    # Verify both have created_at automatically set
    assert assignment1.created_at is not None
    assert isinstance(assignment1.created_at, datetime)
    assert assignment2.created_at is not None
    assert isinstance(assignment2.created_at, datetime)
    # Second should be same or later than first
    assert assignment2.created_at >= assignment1.created_at


def test_user_role_assignment_create_schema():
    """Test UserRoleAssignmentCreate schema validation."""
    user_id = uuid4()
    role_id = uuid4()
    scope_id = uuid4()
    created_by = uuid4()

    assignment_create = UserRoleAssignmentCreate(
        user_id=user_id,
        role_id=role_id,
        scope_type="project",
        scope_id=scope_id,
        is_immutable=True,
        created_by=created_by,
    )

    assert assignment_create.user_id == user_id
    assert assignment_create.role_id == role_id
    assert assignment_create.scope_type == "project"
    assert assignment_create.scope_id == scope_id
    assert assignment_create.is_immutable is True
    assert assignment_create.created_by == created_by


def test_user_role_assignment_create_schema_minimal():
    """Test UserRoleAssignmentCreate schema with minimal fields."""
    user_id = uuid4()
    role_id = uuid4()

    assignment_create = UserRoleAssignmentCreate(
        user_id=user_id,
        role_id=role_id,
        scope_type="global",
    )

    assert assignment_create.user_id == user_id
    assert assignment_create.role_id == role_id
    assert assignment_create.scope_type == "global"
    assert assignment_create.scope_id is None
    assert assignment_create.is_immutable is False
    assert assignment_create.created_by is None


def test_user_role_assignment_read_schema():
    """Test UserRoleAssignmentRead schema validation."""
    assignment_id = uuid4()
    user_id = uuid4()
    role_id = uuid4()
    scope_id = uuid4()
    created_by = uuid4()
    created_at = datetime.now(timezone.utc)

    assignment_read = UserRoleAssignmentRead(
        id=assignment_id,
        user_id=user_id,
        role_id=role_id,
        scope_type="flow",
        scope_id=scope_id,
        is_immutable=False,
        created_at=created_at,
        created_by=created_by,
    )

    assert assignment_read.id == assignment_id
    assert assignment_read.user_id == user_id
    assert assignment_read.role_id == role_id
    assert assignment_read.scope_type == "flow"
    assert assignment_read.scope_id == scope_id
    assert assignment_read.is_immutable is False
    assert assignment_read.created_at == created_at
    assert assignment_read.created_by == created_by


def test_user_role_assignment_update_schema_all_fields():
    """Test UserRoleAssignmentUpdate schema with all fields."""
    user_id = uuid4()
    role_id = uuid4()
    scope_id = uuid4()
    created_by = uuid4()

    assignment_update = UserRoleAssignmentUpdate(
        user_id=user_id,
        role_id=role_id,
        scope_type="project",
        scope_id=scope_id,
        is_immutable=True,
        created_by=created_by,
    )

    assert assignment_update.user_id == user_id
    assert assignment_update.role_id == role_id
    assert assignment_update.scope_type == "project"
    assert assignment_update.scope_id == scope_id
    assert assignment_update.is_immutable is True
    assert assignment_update.created_by == created_by


def test_user_role_assignment_update_schema_partial():
    """Test UserRoleAssignmentUpdate schema with partial updates."""
    assignment_update = UserRoleAssignmentUpdate(is_immutable=True)

    assert assignment_update.user_id is None
    assert assignment_update.role_id is None
    assert assignment_update.scope_type is None
    assert assignment_update.scope_id is None
    assert assignment_update.is_immutable is True
    assert assignment_update.created_by is None


def test_user_role_assignment_update_schema_empty():
    """Test UserRoleAssignmentUpdate schema with no fields."""
    assignment_update = UserRoleAssignmentUpdate()

    assert assignment_update.user_id is None
    assert assignment_update.role_id is None
    assert assignment_update.scope_type is None
    assert assignment_update.scope_id is None
    assert assignment_update.is_immutable is None
    assert assignment_update.created_by is None


# Integration Tests for UserRoleAssignment


@pytest.mark.asyncio
async def test_complete_rbac_setup_with_user_assignments(async_session: AsyncSession):
    """Test creating a complete RBAC setup including user role assignments."""
    # Create permissions
    permissions = [
        Permission(name="Flow:Create", scope_type="Flow"),
        Permission(name="Flow:Read", scope_type="Flow"),
        Permission(name="Flow:Update", scope_type="Flow"),
        Permission(name="Flow:Delete", scope_type="Flow"),
    ]
    for perm in permissions:
        async_session.add(perm)
    await async_session.commit()

    # Create roles
    admin = Role(name="Admin", is_system=True)
    owner = Role(name="Owner", is_system=True)
    editor = Role(name="Editor", is_system=True)
    viewer = Role(name="Viewer", is_system=True)
    async_session.add(admin)
    async_session.add(owner)
    async_session.add(editor)
    async_session.add(viewer)
    await async_session.commit()

    # Create role-permission mappings
    for role in [admin, owner]:
        for perm in permissions:
            rp = RolePermission(role_id=role.id, permission_id=perm.id)
            async_session.add(rp)
    await async_session.commit()

    # Create users
    user1 = User(username="admin_user", password=get_password_hash("password"), is_active=True)
    user2 = User(username="project_owner", password=get_password_hash("password"), is_active=True)
    user3 = User(username="project_editor", password=get_password_hash("password"), is_active=True)
    async_session.add(user1)
    async_session.add(user2)
    async_session.add(user3)
    await async_session.commit()

    # Create user role assignments
    # Admin with global scope
    assignment1 = UserRoleAssignment(
        user_id=user1.id,
        role_id=admin.id,
        scope_type="global",
        scope_id=None,
        is_immutable=False,
    )
    # Owner with project scope
    project_id = uuid4()
    assignment2 = UserRoleAssignment(
        user_id=user2.id,
        role_id=owner.id,
        scope_type="project",
        scope_id=project_id,
        is_immutable=True,  # Starter project owner
    )
    # Editor with project scope
    assignment3 = UserRoleAssignment(
        user_id=user3.id,
        role_id=editor.id,
        scope_type="project",
        scope_id=project_id,
        is_immutable=False,
    )
    async_session.add(assignment1)
    async_session.add(assignment2)
    async_session.add(assignment3)
    await async_session.commit()

    # Verify complete setup
    stmt = select(UserRoleAssignment)
    result = await async_session.exec(stmt)
    all_assignments = result.all()
    assert len(all_assignments) == 3

    # Verify user1 has global admin
    stmt = select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == user1.id,
        UserRoleAssignment.scope_type == "global"
    )
    result = await async_session.exec(stmt)
    admin_assignment = result.first()
    assert admin_assignment is not None
    assert admin_assignment.role_id == admin.id

    # Verify user2 has immutable project owner
    stmt = select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == user2.id,
        UserRoleAssignment.is_immutable == True  # noqa: E712
    )
    result = await async_session.exec(stmt)
    owner_assignment = result.first()
    assert owner_assignment is not None
    assert owner_assignment.role_id == owner.id
    assert owner_assignment.scope_id == project_id


@pytest.mark.asyncio
async def test_query_user_assignments_by_scope(async_session: AsyncSession):
    """Test querying user assignments filtered by scope."""
    # Create user and roles
    user = User(username="scopeuser", password=get_password_hash("password"), is_active=True)
    role1 = Role(name="Role1", is_system=False)
    role2 = Role(name="Role2", is_system=False)
    role3 = Role(name="Role3", is_system=False)
    async_session.add(user)
    async_session.add(role1)
    async_session.add(role2)
    async_session.add(role3)
    await async_session.commit()

    # Create assignments with different scopes
    project_id = uuid4()
    flow_id = uuid4()
    assignments = [
        UserRoleAssignment(user_id=user.id, role_id=role1.id, scope_type="global", scope_id=None),
        UserRoleAssignment(user_id=user.id, role_id=role2.id, scope_type="project", scope_id=project_id),
        UserRoleAssignment(user_id=user.id, role_id=role3.id, scope_type="flow", scope_id=flow_id),
    ]
    for assignment in assignments:
        async_session.add(assignment)
    await async_session.commit()

    # Query global assignments
    stmt = select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == user.id,
        UserRoleAssignment.scope_type == "global"
    )
    result = await async_session.exec(stmt)
    global_assignments = result.all()
    assert len(global_assignments) == 1
    assert global_assignments[0].scope_type == "global"

    # Query project assignments
    stmt = select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == user.id,
        UserRoleAssignment.scope_type == "project",
        UserRoleAssignment.scope_id == project_id
    )
    result = await async_session.exec(stmt)
    project_assignments = result.all()
    assert len(project_assignments) == 1
    assert project_assignments[0].scope_type == "project"
    assert project_assignments[0].scope_id == project_id


@pytest.mark.asyncio
async def test_query_immutable_assignments(async_session: AsyncSession):
    """Test querying immutable assignments (Starter Project Owners)."""
    # Create users and role
    user1 = User(username="immuser1", password=get_password_hash("password"), is_active=True)
    user2 = User(username="immuser2", password=get_password_hash("password"), is_active=True)
    role = Role(name="Owner", is_system=True)
    async_session.add(user1)
    async_session.add(user2)
    async_session.add(role)
    await async_session.commit()

    # Create assignments with different immutability
    project_id = uuid4()
    assignment1 = UserRoleAssignment(
        user_id=user1.id,
        role_id=role.id,
        scope_type="project",
        scope_id=project_id,
        is_immutable=True,
    )
    assignment2 = UserRoleAssignment(
        user_id=user2.id,
        role_id=role.id,
        scope_type="project",
        scope_id=uuid4(),
        is_immutable=False,
    )
    async_session.add(assignment1)
    async_session.add(assignment2)
    await async_session.commit()

    # Query immutable assignments
    stmt = select(UserRoleAssignment).where(UserRoleAssignment.is_immutable == True)  # noqa: E712
    result = await async_session.exec(stmt)
    immutable_assignments = result.all()

    assert len(immutable_assignments) == 1
    assert immutable_assignments[0].user_id == user1.id
    assert immutable_assignments[0].is_immutable is True


@pytest.mark.asyncio
async def test_user_role_assignment_update_in_database(async_session: AsyncSession):
    """Test updating a user role assignment in the database."""
    # Create user and roles
    user = User(username="updateuser", password=get_password_hash("password"), is_active=True)
    role1 = Role(name="Role1", is_system=False)
    role2 = Role(name="Role2", is_system=False)
    async_session.add(user)
    async_session.add(role1)
    async_session.add(role2)
    await async_session.commit()

    # Create assignment
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role1.id,
        scope_type="project",
        scope_id=uuid4(),
        is_immutable=False,
    )
    async_session.add(assignment)
    await async_session.commit()
    assignment_id = assignment.id

    # Update assignment to different role
    assignment.role_id = role2.id
    assignment.is_immutable = True
    await async_session.commit()
    await async_session.refresh(assignment)

    # Verify update
    assert assignment.id == assignment_id
    assert assignment.role_id == role2.id
    assert assignment.is_immutable is True
