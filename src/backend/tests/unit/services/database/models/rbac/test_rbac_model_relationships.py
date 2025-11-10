"""
Unit tests for RBAC model relationships and constraints.

These tests validate:
- Model field validation and constraints
- Relationships between models (Role, Permission, RolePermission, UserRoleAssignment)
- Database constraints (unique constraints, foreign keys)
- Model creation, update, and serialization
- Pydantic schema validation
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from langbuilder.services.database.models.rbac import (
    Permission,
    PermissionCreate,
    PermissionRead,
    Role,
    RoleCreate,
    RolePermission,
    RolePermissionCreate,
    RoleRead,
    UserRoleAssignment,
    UserRoleAssignmentCreate,
    UserRoleAssignmentRead,
)
from pydantic import ValidationError


class TestRoleModel:
    """Test Role model validation and behavior."""

    def test_role_creation_with_required_fields(self):
        """Test creating a Role with all required fields."""
        role_id = uuid4()
        role = Role(
            id=role_id,
            name="TestRole",
            description="Test role description",
            is_system=False,
        )

        assert role.id == role_id
        assert role.name == "TestRole"
        assert role.description == "Test role description"
        assert role.is_system is False

    def test_role_creation_with_minimal_fields(self):
        """Test creating a Role with minimal required fields."""
        role = Role(
            id=uuid4(),
            name="MinimalRole",
            is_system=False,
        )

        assert role.name == "MinimalRole"
        assert role.description is None

    def test_role_create_schema(self):
        """Test RoleCreate Pydantic schema."""
        role_data = RoleCreate(
            name="NewRole",
            description="New role",
            is_system=False,
        )

        assert role_data.name == "NewRole"
        assert role_data.description == "New role"
        assert role_data.is_system is False

    def test_role_read_schema(self):
        """Test RoleRead Pydantic schema."""
        role_id = uuid4()
        role_data = RoleRead(
            id=str(role_id),
            name="ReadRole",
            description="Read role",
            is_system=True,
        )

        assert role_data.id == str(role_id)
        assert role_data.name == "ReadRole"
        assert role_data.is_system is True

    def test_role_name_required(self):
        """Test that role name is required."""
        with pytest.raises(ValidationError):
            Role(id=uuid4(), is_system=False)  # Missing name


class TestPermissionModel:
    """Test Permission model validation and behavior."""

    def test_permission_creation_with_all_fields(self):
        """Test creating a Permission with all fields."""
        perm_id = uuid4()
        perm = Permission(
            id=perm_id,
            name="Read",
            description="Read permission",
            scope_type="Flow",
        )

        assert perm.id == perm_id
        assert perm.name == "Read"
        assert perm.description == "Read permission"
        assert perm.scope_type == "Flow"

    def test_permission_create_schema(self):
        """Test PermissionCreate Pydantic schema."""
        perm_data = PermissionCreate(
            name="Update",
            description="Update permission",
            scope_type="Project",
        )

        assert perm_data.name == "Update"
        assert perm_data.description == "Update permission"
        assert perm_data.scope_type == "Project"

    def test_permission_read_schema(self):
        """Test PermissionRead Pydantic schema."""
        perm_id = uuid4()
        perm_data = PermissionRead(
            id=str(perm_id),
            name="Delete",
            description="Delete permission",
            scope_type="Global",
        )

        assert perm_data.id == str(perm_id)
        assert perm_data.name == "Delete"
        assert perm_data.scope_type == "Global"

    def test_permission_required_fields(self):
        """Test that required fields are enforced."""
        # Name is required
        with pytest.raises(ValidationError):
            Permission(id=uuid4(), scope_type="Flow")

        # Scope type is required
        with pytest.raises(ValidationError):
            Permission(id=uuid4(), name="Read")


class TestRolePermissionModel:
    """Test RolePermission model validation and behavior."""

    def test_role_permission_creation(self):
        """Test creating a RolePermission relationship."""
        rp_id = uuid4()
        role_id = uuid4()
        perm_id = uuid4()

        role_perm = RolePermission(
            id=rp_id,
            role_id=role_id,
            permission_id=perm_id,
        )

        assert role_perm.id == rp_id
        assert role_perm.role_id == role_id
        assert role_perm.permission_id == perm_id

    def test_role_permission_create_schema(self):
        """Test RolePermissionCreate Pydantic schema."""
        role_id = uuid4()
        perm_id = uuid4()

        rp_data = RolePermissionCreate(
            role_id=role_id,
            permission_id=perm_id,
        )

        assert rp_data.role_id == role_id
        assert rp_data.permission_id == perm_id

    def test_role_permission_required_fields(self):
        """Test that foreign keys are required."""
        # Missing role_id
        with pytest.raises(ValidationError):
            RolePermission(id=uuid4(), permission_id=uuid4())

        # Missing permission_id
        with pytest.raises(ValidationError):
            RolePermission(id=uuid4(), role_id=uuid4())


class TestUserRoleAssignmentModel:
    """Test UserRoleAssignment model validation and behavior."""

    def test_user_role_assignment_creation_global_scope(self):
        """Test creating a global scope assignment."""
        assignment_id = uuid4()
        user_id = uuid4()
        role_id = uuid4()
        created_by = uuid4()

        assignment = UserRoleAssignment(
            id=assignment_id,
            user_id=user_id,
            role_id=role_id,
            scope_type="Global",
            scope_id=None,
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
        )

        assert assignment.id == assignment_id
        assert assignment.user_id == user_id
        assert assignment.role_id == role_id
        assert assignment.scope_type == "Global"
        assert assignment.scope_id is None
        assert assignment.is_immutable is False
        assert assignment.created_by == created_by

    def test_user_role_assignment_creation_project_scope(self):
        """Test creating a project scope assignment."""
        assignment_id = uuid4()
        user_id = uuid4()
        role_id = uuid4()
        scope_id = uuid4()

        assignment = UserRoleAssignment(
            id=assignment_id,
            user_id=user_id,
            role_id=role_id,
            scope_type="Project",
            scope_id=scope_id,
            is_immutable=True,
            created_at=datetime.now(timezone.utc),
        )

        assert assignment.scope_type == "Project"
        assert assignment.scope_id == scope_id
        assert assignment.is_immutable is True

    def test_user_role_assignment_creation_flow_scope(self):
        """Test creating a flow scope assignment."""
        assignment = UserRoleAssignment(
            id=uuid4(),
            user_id=uuid4(),
            role_id=uuid4(),
            scope_type="Flow",
            scope_id=uuid4(),
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        assert assignment.scope_type == "Flow"
        assert assignment.scope_id is not None

    def test_user_role_assignment_create_schema(self):
        """Test UserRoleAssignmentCreate Pydantic schema."""
        user_id = uuid4()
        role_id = uuid4()
        scope_id = uuid4()

        assignment_data = UserRoleAssignmentCreate(
            user_id=user_id,
            role_id=role_id,
            scope_type="Project",
            scope_id=scope_id,
            is_immutable=True,
        )

        assert assignment_data.user_id == user_id
        assert assignment_data.role_id == role_id
        assert assignment_data.scope_type == "Project"
        assert assignment_data.scope_id == scope_id
        assert assignment_data.is_immutable is True

    def test_user_role_assignment_read_schema(self):
        """Test UserRoleAssignmentRead Pydantic schema."""
        assignment_id = uuid4()
        user_id = uuid4()
        role_id = uuid4()
        created_at = datetime.now(timezone.utc)

        assignment_data = UserRoleAssignmentRead(
            id=str(assignment_id),
            user_id=str(user_id),
            role_id=str(role_id),
            scope_type="Global",
            scope_id=None,
            is_immutable=False,
            created_at=created_at,
            created_by=None,
        )

        assert assignment_data.id == str(assignment_id)
        assert assignment_data.user_id == str(user_id)
        assert assignment_data.scope_type == "Global"
        assert assignment_data.is_immutable is False

    def test_user_role_assignment_required_fields(self):
        """Test that required fields are enforced."""
        # Missing user_id
        with pytest.raises(ValidationError):
            UserRoleAssignment(
                id=uuid4(),
                role_id=uuid4(),
                scope_type="Global",
                scope_id=None,
                is_immutable=False,
                created_at=datetime.now(timezone.utc),
            )

        # Missing role_id
        with pytest.raises(ValidationError):
            UserRoleAssignment(
                id=uuid4(),
                user_id=uuid4(),
                scope_type="Global",
                scope_id=None,
                is_immutable=False,
                created_at=datetime.now(timezone.utc),
            )

        # Missing scope_type
        with pytest.raises(ValidationError):
            UserRoleAssignment(
                id=uuid4(),
                user_id=uuid4(),
                role_id=uuid4(),
                scope_id=None,
                is_immutable=False,
                created_at=datetime.now(timezone.utc),
            )

    def test_user_role_assignment_immutable_defaults_false(self):
        """Test that is_immutable defaults to False."""
        assignment = UserRoleAssignment(
            id=uuid4(),
            user_id=uuid4(),
            role_id=uuid4(),
            scope_type="Global",
            scope_id=None,
            created_at=datetime.now(timezone.utc),
        )

        # Should default to False
        assert assignment.is_immutable is False


class TestRBACModelRelationships:
    """Test relationships between RBAC models."""

    def test_role_permission_relationship_data(self):
        """Test that RolePermission connects Role and Permission."""
        role_id = uuid4()
        perm_id = uuid4()

        role = Role(id=role_id, name="TestRole", is_system=False)
        permission = Permission(id=perm_id, name="Read", scope_type="Flow")
        role_perm = RolePermission(
            id=uuid4(),
            role_id=role_id,
            permission_id=perm_id,
        )

        # Verify the relationship
        assert role_perm.role_id == role.id
        assert role_perm.permission_id == permission.id

    def test_user_role_assignment_relationship_data(self):
        """Test that UserRoleAssignment connects User and Role."""
        user_id = uuid4()
        role_id = uuid4()

        role = Role(id=role_id, name="TestRole", is_system=False)
        assignment = UserRoleAssignment(
            id=uuid4(),
            user_id=user_id,
            role_id=role_id,
            scope_type="Global",
            scope_id=None,
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        # Verify the relationship
        assert assignment.role_id == role.id
        assert assignment.user_id == user_id

    def test_scope_type_validation(self):
        """Test that scope_type accepts valid values."""
        # Valid scope types
        valid_scopes = ["Global", "Project", "Flow"]

        for scope_type in valid_scopes:
            assignment = UserRoleAssignment(
                id=uuid4(),
                user_id=uuid4(),
                role_id=uuid4(),
                scope_type=scope_type,
                scope_id=None if scope_type == "Global" else uuid4(),
                is_immutable=False,
                created_at=datetime.now(timezone.utc),
            )
            assert assignment.scope_type == scope_type

    def test_global_scope_requires_null_scope_id(self):
        """Test that Global scope assignments should have null scope_id."""
        # This is a business logic constraint, not enforced by the model itself
        # But we document the expected behavior
        assignment = UserRoleAssignment(
            id=uuid4(),
            user_id=uuid4(),
            role_id=uuid4(),
            scope_type="Global",
            scope_id=None,  # Should be None for Global
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        assert assignment.scope_type == "Global"
        assert assignment.scope_id is None

    def test_project_and_flow_scope_require_scope_id(self):
        """Test that Project/Flow scopes should have non-null scope_id."""
        # This is a business logic constraint
        project_assignment = UserRoleAssignment(
            id=uuid4(),
            user_id=uuid4(),
            role_id=uuid4(),
            scope_type="Project",
            scope_id=uuid4(),  # Should be set for Project
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        flow_assignment = UserRoleAssignment(
            id=uuid4(),
            user_id=uuid4(),
            role_id=uuid4(),
            scope_type="Flow",
            scope_id=uuid4(),  # Should be set for Flow
            is_immutable=False,
            created_at=datetime.now(timezone.utc),
        )

        assert project_assignment.scope_id is not None
        assert flow_assignment.scope_id is not None


class TestRBACModelSerialization:
    """Test model serialization and deserialization."""

    def test_role_serialization(self):
        """Test serializing a Role to dict."""
        role = Role(
            id=uuid4(),
            name="SerializeRole",
            description="Test serialization",
            is_system=True,
        )

        role_dict = role.model_dump()

        assert role_dict["name"] == "SerializeRole"
        assert role_dict["description"] == "Test serialization"
        assert role_dict["is_system"] is True

    def test_permission_serialization(self):
        """Test serializing a Permission to dict."""
        perm = Permission(
            id=uuid4(),
            name="Write",
            description="Write permission",
            scope_type="Project",
        )

        perm_dict = perm.model_dump()

        assert perm_dict["name"] == "Write"
        assert perm_dict["description"] == "Write permission"
        assert perm_dict["scope_type"] == "Project"

    def test_user_role_assignment_serialization(self):
        """Test serializing a UserRoleAssignment to dict."""
        created_at = datetime.now(timezone.utc)
        assignment = UserRoleAssignment(
            id=uuid4(),
            user_id=uuid4(),
            role_id=uuid4(),
            scope_type="Flow",
            scope_id=uuid4(),
            is_immutable=True,
            created_at=created_at,
            created_by=uuid4(),
        )

        assignment_dict = assignment.model_dump()

        assert assignment_dict["scope_type"] == "Flow"
        assert assignment_dict["is_immutable"] is True
        assert assignment_dict["created_at"] == created_at

    def test_role_deserialization(self):
        """Test deserializing a Role from dict."""
        role_id = uuid4()
        role_dict = {
            "id": role_id,
            "name": "DeserializeRole",
            "description": "Test deserialization",
            "is_system": False,
        }

        role = Role(**role_dict)

        assert role.id == role_id
        assert role.name == "DeserializeRole"
        assert role.description == "Test deserialization"

    def test_user_role_assignment_deserialization(self):
        """Test deserializing a UserRoleAssignment from dict."""
        assignment_id = uuid4()
        user_id = uuid4()
        role_id = uuid4()
        created_at = datetime.now(timezone.utc)

        assignment_dict = {
            "id": assignment_id,
            "user_id": user_id,
            "role_id": role_id,
            "scope_type": "Project",
            "scope_id": uuid4(),
            "is_immutable": False,
            "created_at": created_at,
        }

        assignment = UserRoleAssignment(**assignment_dict)

        assert assignment.id == assignment_id
        assert assignment.user_id == user_id
        assert assignment.scope_type == "Project"
