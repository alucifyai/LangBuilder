"""Unit tests for RBAC database models and CRUD operations.

This module tests the Role, Permission, RolePermission, and UserRoleAssignment models,
including all CRUD operations, relationships, constraints, and edge cases.
"""
# ruff: noqa: S106

from uuid import uuid4

import pytest
from langbuilder.services.database.models.rbac import (
    Permission,
    PermissionEnum,
    Role,
    RoleEnum,
    RolePermission,
    ScopeTypeEnum,
    UserRoleAssignment,
    UserRoleAssignmentCreate,
    UserRoleAssignmentUpdate,
    create_assignment,
    delete_assignment,
    get_all_assignments,
    get_all_permissions,
    get_all_roles,
    get_assignment_by_id,
    get_assignments_by_scope,
    get_permission_by_id,
    get_permission_by_name,
    get_permissions_for_role,
    get_role_by_id,
    get_role_by_name,
    get_role_permissions,
    get_user_assignment_for_scope,
    get_user_assignments,
    update_assignment,
)
from langbuilder.services.database.models.user import User
from langbuilder.services.database.utils import session_getter
from langbuilder.services.deps import get_db_service
from sqlalchemy.exc import IntegrityError
from sqlmodel import select


class TestRoleModel:
    """Test Role model and operations."""

    @pytest.mark.asyncio
    async def test_create_role(self):
        """Test creating a role with all fields."""
        async with session_getter(get_db_service()) as session:
            role = Role(
                name=RoleEnum.OWNER,
                description="Full CRUD access to owned scope",
            )
            session.add(role)
            await session.commit()
            await session.refresh(role)

            assert role.id is not None
            assert role.name == RoleEnum.OWNER
            assert role.description == "Full CRUD access to owned scope"

    @pytest.mark.asyncio
    async def test_role_unique_name_constraint(self):
        """Test that role names must be unique."""
        async with session_getter(get_db_service()) as session:
            role1 = Role(name=RoleEnum.EDITOR, description="First editor role")
            session.add(role1)
            await session.commit()

            role2 = Role(name=RoleEnum.EDITOR, description="Duplicate editor role")
            session.add(role2)

            with pytest.raises(IntegrityError):
                await session.commit()

    @pytest.mark.asyncio
    async def test_get_role_by_id(self):
        """Test retrieving role by ID."""
        async with session_getter(get_db_service()) as session:
            role = Role(name=RoleEnum.VIEWER, description="Read-only access")
            session.add(role)
            await session.commit()
            await session.refresh(role)

            retrieved = await get_role_by_id(session, role.id)
            assert retrieved is not None
            assert retrieved.id == role.id
            assert retrieved.name == RoleEnum.VIEWER

    @pytest.mark.asyncio
    async def test_get_role_by_name(self):
        """Test retrieving role by name."""
        async with session_getter(get_db_service()) as session:
            role = Role(name=RoleEnum.ADMIN, description="Global admin access")
            session.add(role)
            await session.commit()

            retrieved = await get_role_by_name(session, RoleEnum.ADMIN)
            assert retrieved is not None
            assert retrieved.name == RoleEnum.ADMIN

    @pytest.mark.asyncio
    async def test_get_all_roles(self):
        """Test retrieving all roles."""
        async with session_getter(get_db_service()) as session:
            roles = [
                Role(name=RoleEnum.ADMIN, description="Admin"),
                Role(name=RoleEnum.OWNER, description="Owner"),
            ]
            for role in roles:
                session.add(role)
            await session.commit()

            all_roles = await get_all_roles(session)
            assert len(all_roles) >= 2
            role_names = {r.name for r in all_roles}
            assert RoleEnum.ADMIN in role_names
            assert RoleEnum.OWNER in role_names


class TestPermissionModel:
    """Test Permission model and operations."""

    @pytest.mark.asyncio
    async def test_create_permission(self):
        """Test creating a permission."""
        async with session_getter(get_db_service()) as session:
            permission = Permission(
                name=PermissionEnum.CREATE,
                description="Create new entities",
            )
            session.add(permission)
            await session.commit()
            await session.refresh(permission)

            assert permission.id is not None
            assert permission.name == PermissionEnum.CREATE
            assert permission.description == "Create new entities"

    @pytest.mark.asyncio
    async def test_permission_unique_name_constraint(self):
        """Test that permission names must be unique."""
        async with session_getter(get_db_service()) as session:
            perm1 = Permission(name=PermissionEnum.READ, description="First read")
            session.add(perm1)
            await session.commit()

            perm2 = Permission(name=PermissionEnum.READ, description="Duplicate read")
            session.add(perm2)

            with pytest.raises(IntegrityError):
                await session.commit()

    @pytest.mark.asyncio
    async def test_get_permission_by_id(self):
        """Test retrieving permission by ID."""
        async with session_getter(get_db_service()) as session:
            permission = Permission(name=PermissionEnum.UPDATE, description="Update entities")
            session.add(permission)
            await session.commit()
            await session.refresh(permission)

            retrieved = await get_permission_by_id(session, permission.id)
            assert retrieved is not None
            assert retrieved.id == permission.id
            assert retrieved.name == PermissionEnum.UPDATE

    @pytest.mark.asyncio
    async def test_get_permission_by_name(self):
        """Test retrieving permission by name."""
        async with session_getter(get_db_service()) as session:
            permission = Permission(name=PermissionEnum.DELETE, description="Delete entities")
            session.add(permission)
            await session.commit()

            retrieved = await get_permission_by_name(session, PermissionEnum.DELETE)
            assert retrieved is not None
            assert retrieved.name == PermissionEnum.DELETE

    @pytest.mark.asyncio
    async def test_get_all_permissions(self):
        """Test retrieving all permissions."""
        async with session_getter(get_db_service()) as session:
            permissions = [
                Permission(name=PermissionEnum.CREATE, description="Create"),
                Permission(name=PermissionEnum.READ, description="Read"),
            ]
            for perm in permissions:
                session.add(perm)
            await session.commit()

            all_perms = await get_all_permissions(session)
            assert len(all_perms) >= 2
            perm_names = {p.name for p in all_perms}
            assert PermissionEnum.CREATE in perm_names
            assert PermissionEnum.READ in perm_names


class TestRolePermissionModel:
    """Test RolePermission model and operations."""

    @pytest.mark.asyncio
    async def test_create_role_permission(self):
        """Test creating a role-permission mapping."""
        async with session_getter(get_db_service()) as session:
            role = Role(name=RoleEnum.OWNER, description="Owner role")
            permission = Permission(name=PermissionEnum.CREATE, description="Create permission")
            session.add(role)
            session.add(permission)
            await session.commit()
            await session.refresh(role)
            await session.refresh(permission)

            role_perm = RolePermission(role_id=role.id, permission_id=permission.id)
            session.add(role_perm)
            await session.commit()
            await session.refresh(role_perm)

            assert role_perm.id is not None
            assert role_perm.role_id == role.id
            assert role_perm.permission_id == permission.id

    @pytest.mark.asyncio
    async def test_role_permission_unique_constraint(self):
        """Test unique constraint on role_id + permission_id."""
        async with session_getter(get_db_service()) as session:
            role = Role(name=RoleEnum.EDITOR, description="Editor role")
            permission = Permission(name=PermissionEnum.UPDATE, description="Update permission")
            session.add(role)
            session.add(permission)
            await session.commit()
            await session.refresh(role)
            await session.refresh(permission)

            rp1 = RolePermission(role_id=role.id, permission_id=permission.id)
            session.add(rp1)
            await session.commit()

            rp2 = RolePermission(role_id=role.id, permission_id=permission.id)
            session.add(rp2)

            with pytest.raises(IntegrityError):
                await session.commit()

    @pytest.mark.asyncio
    async def test_get_role_permissions(self):
        """Test retrieving all permissions for a role."""
        async with session_getter(get_db_service()) as session:
            role = Role(name=RoleEnum.VIEWER, description="Viewer role")
            perm1 = Permission(name=PermissionEnum.READ, description="Read")
            session.add(role)
            session.add(perm1)
            await session.commit()
            await session.refresh(role)
            await session.refresh(perm1)

            role_perm = RolePermission(role_id=role.id, permission_id=perm1.id)
            session.add(role_perm)
            await session.commit()

            role_perms = await get_role_permissions(session, role.id)
            assert len(role_perms) == 1
            assert role_perms[0].role_id == role.id
            assert role_perms[0].permission_id == perm1.id

    @pytest.mark.asyncio
    async def test_get_permissions_for_role(self):
        """Test retrieving Permission entities for a role."""
        async with session_getter(get_db_service()) as session:
            role = Role(name=RoleEnum.OWNER, description="Owner")
            perm1 = Permission(name=PermissionEnum.CREATE, description="Create")
            perm2 = Permission(name=PermissionEnum.READ, description="Read")
            session.add(role)
            session.add(perm1)
            session.add(perm2)
            await session.commit()
            await session.refresh(role)
            await session.refresh(perm1)
            await session.refresh(perm2)

            session.add(RolePermission(role_id=role.id, permission_id=perm1.id))
            session.add(RolePermission(role_id=role.id, permission_id=perm2.id))
            await session.commit()

            permissions = await get_permissions_for_role(session, role.id)
            assert len(permissions) == 2
            perm_names = {p.name for p in permissions}
            assert PermissionEnum.CREATE in perm_names
            assert PermissionEnum.READ in perm_names


class TestUserRoleAssignmentModel:
    """Test UserRoleAssignment model and operations."""

    @pytest.mark.asyncio
    async def test_create_user_role_assignment(self):
        """Test creating a user role assignment."""
        async with session_getter(get_db_service()) as session:
            # Create user
            user = User(username="testuser", password="password", is_active=True)
            session.add(user)

            # Create role
            role = Role(name=RoleEnum.OWNER, description="Owner")
            session.add(role)

            await session.commit()
            await session.refresh(user)
            await session.refresh(role)

            # Create assignment
            project_id = uuid4()
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=project_id,
                is_immutable=False,
            )
            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)

            assert assignment.id is not None
            assert assignment.user_id == user.id
            assert assignment.role_id == role.id
            assert assignment.scope_type == ScopeTypeEnum.PROJECT
            assert assignment.scope_id == project_id
            assert assignment.is_immutable is False
            assert assignment.created_at is not None

    @pytest.mark.asyncio
    async def test_assignment_unique_constraint(self):
        """Test unique constraint on user_id + scope_type + scope_id."""
        async with session_getter(get_db_service()) as session:
            user = User(username="uniqueuser", password="password", is_active=True)
            role = Role(name=RoleEnum.EDITOR, description="Editor")
            session.add(user)
            session.add(role)
            await session.commit()
            await session.refresh(user)
            await session.refresh(role)

            project_id = uuid4()

            # First assignment
            assignment1 = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=project_id,
            )
            session.add(assignment1)
            await session.commit()

            # Duplicate assignment (same user, scope_type, scope_id)
            assignment2 = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=project_id,
            )
            session.add(assignment2)

            with pytest.raises(IntegrityError):
                await session.commit()

    @pytest.mark.asyncio
    async def test_global_scope_assignment(self):
        """Test creating a global scope assignment (Admin role)."""
        async with session_getter(get_db_service()) as session:
            user = User(username="adminuser", password="password", is_active=True, is_superuser=True)
            role = Role(name=RoleEnum.ADMIN, description="Admin")
            session.add(user)
            session.add(role)
            await session.commit()
            await session.refresh(user)
            await session.refresh(role)

            # Global scope has scope_id = None
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.GLOBAL,
                scope_id=None,
            )
            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)

            assert assignment.scope_type == ScopeTypeEnum.GLOBAL
            assert assignment.scope_id is None

    @pytest.mark.asyncio
    async def test_get_user_assignments(self):
        """Test retrieving all assignments for a user."""
        async with session_getter(get_db_service()) as session:
            user = User(username="multiassignuser", password="password", is_active=True)
            role1 = Role(name=RoleEnum.OWNER, description="Owner")
            role2 = Role(name=RoleEnum.VIEWER, description="Viewer")
            session.add(user)
            session.add(role1)
            session.add(role2)
            await session.commit()
            await session.refresh(user)
            await session.refresh(role1)
            await session.refresh(role2)

            project1 = uuid4()
            project2 = uuid4()

            assignment1 = UserRoleAssignment(
                user_id=user.id,
                role_id=role1.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=project1,
            )
            assignment2 = UserRoleAssignment(
                user_id=user.id,
                role_id=role2.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=project2,
            )
            session.add(assignment1)
            session.add(assignment2)
            await session.commit()

            assignments = await get_user_assignments(session, user.id)
            assert len(assignments) == 2
            scope_ids = {a.scope_id for a in assignments}
            assert project1 in scope_ids
            assert project2 in scope_ids

    @pytest.mark.asyncio
    async def test_get_user_assignment_for_scope(self):
        """Test retrieving assignment for specific scope."""
        async with session_getter(get_db_service()) as session:
            user = User(username="scopeuser", password="password", is_active=True)
            role = Role(name=RoleEnum.EDITOR, description="Editor")
            session.add(user)
            session.add(role)
            await session.commit()
            await session.refresh(user)
            await session.refresh(role)

            flow_id = uuid4()
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.FLOW,
                scope_id=flow_id,
            )
            session.add(assignment)
            await session.commit()

            retrieved = await get_user_assignment_for_scope(session, user.id, ScopeTypeEnum.FLOW, flow_id)
            assert retrieved is not None
            assert retrieved.scope_type == ScopeTypeEnum.FLOW
            assert retrieved.scope_id == flow_id

    @pytest.mark.asyncio
    async def test_create_assignment_crud(self):
        """Test create_assignment CRUD function."""
        async with session_getter(get_db_service()) as session:
            user = User(username="cruduser", password="password", is_active=True)
            role = Role(name=RoleEnum.OWNER, description="Owner")
            session.add(user)
            session.add(role)
            await session.commit()
            await session.refresh(user)
            await session.refresh(role)

            project_id = uuid4()
            assignment_data = UserRoleAssignmentCreate(
                user_id=user.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=project_id,
            )

            assignment = await create_assignment(session, assignment_data, is_immutable=False)
            assert assignment.id is not None
            assert assignment.user_id == user.id
            assert assignment.is_immutable is False

    @pytest.mark.asyncio
    async def test_update_assignment_crud(self):
        """Test update_assignment CRUD function."""
        async with session_getter(get_db_service()) as session:
            user = User(username="updateuser", password="password", is_active=True)
            role1 = Role(name=RoleEnum.EDITOR, description="Editor")
            role2 = Role(name=RoleEnum.VIEWER, description="Viewer")
            session.add(user)
            session.add(role1)
            session.add(role2)
            await session.commit()
            await session.refresh(user)
            await session.refresh(role1)
            await session.refresh(role2)

            project_id = uuid4()
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role1.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=project_id,
            )
            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)

            update_data = UserRoleAssignmentUpdate(role_id=role2.id)
            updated = await update_assignment(session, assignment, update_data)
            assert updated.role_id == role2.id

    @pytest.mark.asyncio
    async def test_update_immutable_assignment_raises_error(self):
        """Test that updating immutable assignment raises error."""
        async with session_getter(get_db_service()) as session:
            user = User(username="immutableuser", password="password", is_active=True)
            role = Role(name=RoleEnum.OWNER, description="Owner")
            session.add(user)
            session.add(role)
            await session.commit()
            await session.refresh(user)
            await session.refresh(role)

            project_id = uuid4()
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=project_id,
                is_immutable=True,
            )
            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)

            update_data = UserRoleAssignmentUpdate(role_id=role.id)
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await update_assignment(session, assignment, update_data)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_assignment_crud(self):
        """Test delete_assignment CRUD function."""
        async with session_getter(get_db_service()) as session:
            user = User(username="deleteuser", password="password", is_active=True)
            role = Role(name=RoleEnum.VIEWER, description="Viewer")
            session.add(user)
            session.add(role)
            await session.commit()
            await session.refresh(user)
            await session.refresh(role)

            project_id = uuid4()
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=project_id,
            )
            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)

            assignment_id = assignment.id
            await delete_assignment(session, assignment)

            # Verify deletion
            retrieved = await get_assignment_by_id(session, assignment_id)
            assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_immutable_assignment_raises_error(self):
        """Test that deleting immutable assignment raises error."""
        async with session_getter(get_db_service()) as session:
            user = User(username="deleteimmutableuser", password="password", is_active=True)
            role = Role(name=RoleEnum.OWNER, description="Owner")
            session.add(user)
            session.add(role)
            await session.commit()
            await session.refresh(user)
            await session.refresh(role)

            project_id = uuid4()
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=project_id,
                is_immutable=True,
            )
            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await delete_assignment(session, assignment)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_assignments_by_scope(self):
        """Test retrieving all assignments for a specific scope."""
        async with session_getter(get_db_service()) as session:
            user1 = User(username="scopeuser1", password="password", is_active=True)
            user2 = User(username="scopeuser2", password="password", is_active=True)
            role = Role(name=RoleEnum.EDITOR, description="Editor")
            session.add(user1)
            session.add(user2)
            session.add(role)
            await session.commit()
            await session.refresh(user1)
            await session.refresh(user2)
            await session.refresh(role)

            project_id = uuid4()

            assignment1 = UserRoleAssignment(
                user_id=user1.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=project_id,
            )
            assignment2 = UserRoleAssignment(
                user_id=user2.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=project_id,
            )
            session.add(assignment1)
            session.add(assignment2)
            await session.commit()

            assignments = await get_assignments_by_scope(session, ScopeTypeEnum.PROJECT, project_id)
            assert len(assignments) == 2
            user_ids = {a.user_id for a in assignments}
            assert user1.id in user_ids
            assert user2.id in user_ids

    @pytest.mark.asyncio
    async def test_get_all_assignments(self):
        """Test retrieving all assignments across all users."""
        async with session_getter(get_db_service()) as session:
            # Create two users with assignments
            user1 = User(username="alluser1", password="password", is_active=True)
            user2 = User(username="alluser2", password="password", is_active=True)
            role = Role(name=RoleEnum.VIEWER, description="Viewer")
            session.add_all([user1, user2, role])
            await session.commit()
            await session.refresh(user1)
            await session.refresh(user2)
            await session.refresh(role)

            # Create assignments for both users
            assignment1 = UserRoleAssignment(
                user_id=user1.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=uuid4(),
            )
            assignment2 = UserRoleAssignment(
                user_id=user2.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=uuid4(),
            )
            session.add_all([assignment1, assignment2])
            await session.commit()

            # Retrieve all assignments
            all_assignments = await get_all_assignments(session)
            assert len(all_assignments) >= 2
            user_ids = {a.user_id for a in all_assignments}
            assert user1.id in user_ids
            assert user2.id in user_ids


class TestRBACRelationships:
    """Test relationships between RBAC models."""

    @pytest.mark.asyncio
    async def test_role_to_role_permissions_relationship(self):
        """Test Role to RolePermission relationship."""
        async with session_getter(get_db_service()) as session:
            role = Role(name=RoleEnum.OWNER, description="Owner")
            perm = Permission(name=PermissionEnum.CREATE, description="Create")
            session.add(role)
            session.add(perm)
            await session.commit()
            await session.refresh(role)
            await session.refresh(perm)

            role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
            session.add(role_perm)
            await session.commit()

            # Refresh to load relationships
            await session.refresh(role)
            stmt = select(Role).where(Role.id == role.id)
            loaded_role = (await session.exec(stmt)).first()

            # Note: Relationship loading depends on SQLModel configuration
            # This verifies the foreign key constraint works
            assert loaded_role is not None
            assert loaded_role.id == role.id

    @pytest.mark.asyncio
    async def test_user_to_role_assignments_relationship(self):
        """Test User to UserRoleAssignment relationship."""
        async with session_getter(get_db_service()) as session:
            user = User(username="reluser", password="password", is_active=True)
            role = Role(name=RoleEnum.VIEWER, description="Viewer")
            session.add(user)
            session.add(role)
            await session.commit()
            await session.refresh(user)
            await session.refresh(role)

            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=uuid4(),
            )
            session.add(assignment)
            await session.commit()

            # Verify relationship via query
            assignments = await get_user_assignments(session, user.id)
            assert len(assignments) == 1
            assert assignments[0].user_id == user.id
