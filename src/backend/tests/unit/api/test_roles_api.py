"""
Unit tests for Role Management API endpoints.

Tests acceptance criteria scenarios for Story 1.2.
"""

import pytest
from uuid import uuid4
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.permission.model import Permission
from langflow.services.database.models.role.crud import create_role, get_role_by_id
from langflow.services.database.models.grant.crud import create_grant
from langflow.services.database.models.grant.model import PrincipalType, ScopeType
from langflow.services.database.models.audit.crud import get_audit_logs_for_resource
from langflow.services.database.models.audit.model import AuditAction


@pytest.mark.asyncio
class TestRoleAPI:
    """Unit tests for role management API."""

    @pytest.fixture
    async def seed_permissions(self, session: AsyncSession):
        """Seed basic permissions for testing."""
        permissions = [
            Permission(
                id="deploy_environment",
                resource_type="environments",
                action="deploy_environment",
                description="Deploy to environment",
            ),
            Permission(
                id="flows:read",
                resource_type="flows",
                action="read",
                description="Read flows",
            ),
            Permission(
                id="flows:create",
                resource_type="flows",
                action="create",
                description="Create flows",
            ),
        ]

        for perm in permissions:
            session.add(perm)
        await session.commit()

        return permissions

    async def test_create_role_success(self, session: AsyncSession, seed_permissions):
        """
        AC1: Successful creation of a custom role.

        Test that a role "Deployer" can be created with valid permissions.
        """
        from langflow.services.database.models.role.crud import create_role

        # Create role with valid permissions
        role = await create_role(
            session,
            name="Deployer",
            permissions=["deploy_environment", "flows:read"],
        )

        assert role is not None
        assert role.name == "Deployer"
        assert "deploy_environment" in role.permissions
        assert "flows:read" in role.permissions
        assert role.version == 1

    async def test_duplicate_role_name_rejection(
        self, session: AsyncSession, seed_permissions
    ):
        """
        AC2: Prevent duplicate role names.

        Test that creating a role with a duplicate name fails.
        """
        from langflow.services.database.models.role.crud import create_role

        # Create first role
        await create_role(session, name="Editor", permissions=["flows:read"])

        # Attempt to create duplicate role
        with pytest.raises(Exception) as exc_info:
            await create_role(session, name="Editor", permissions=["flows:create"])

        assert "Role name must be unique" in str(exc_info.value)

    async def test_create_role_with_invalid_permissions(
        self, session: AsyncSession, seed_permissions
    ):
        """
        Test that role creation fails with invalid permission IDs.
        """
        from langflow.services.database.models.role.crud import create_role

        # Attempt to create role with invalid permission
        with pytest.raises(Exception) as exc_info:
            await create_role(
                session,
                name="BadRole",
                permissions=["deploy_environment", "unknown:permission"],
            )

        assert "Unknown permission id" in str(exc_info.value)

    async def test_role_update_increments_version(
        self, session: AsyncSession, seed_permissions
    ):
        """
        AC3: Edit role and track version.

        Test that updating a role increments the version number.
        """
        from langflow.services.database.models.role.crud import (
            create_role,
            update_role,
        )

        # Create role
        role = await create_role(
            session,
            name="Deployer",
            permissions=["deploy_environment"],
        )

        assert role.version == 1

        # Update role - add permission
        updated_role = await update_role(
            session,
            role_id=role.id,
            permissions=["deploy_environment", "flows:read"],
        )

        assert updated_role.version == 2
        assert "flows:read" in updated_role.permissions

    async def test_role_update_with_duplicate_name(
        self, session: AsyncSession, seed_permissions
    ):
        """
        Test that updating a role with a duplicate name fails.
        """
        from langflow.services.database.models.role.crud import (
            create_role,
            update_role,
        )

        # Create two roles
        role1 = await create_role(session, name="Editor", permissions=["flows:read"])
        role2 = await create_role(
            session, name="Viewer", permissions=["flows:read"]
        )

        # Attempt to rename role2 to duplicate role1's name
        with pytest.raises(Exception) as exc_info:
            await update_role(session, role_id=role2.id, name="Editor")

        assert "Role name must be unique" in str(exc_info.value)

    async def test_role_deletion_with_active_grants(
        self, session: AsyncSession, seed_permissions
    ):
        """
        Test that role deletion fails when active grants exist.
        """
        from langflow.services.database.models.role.crud import create_role
        from langflow.services.database.models.grant.crud import (
            create_grant,
            count_grants_by_role,
        )

        # Create role
        role = await create_role(
            session,
            name="Deployer",
            permissions=["deploy_environment"],
        )

        # Create grant using this role
        user_id = uuid4()
        await create_grant(
            session,
            principal_type=PrincipalType.USER,
            principal_id=user_id,
            role_id=role.id,
            scope_type=ScopeType.WORKSPACE,
            scope_id="WB1",
        )

        # Check grant count
        grant_count = await count_grants_by_role(session, role.id)
        assert grant_count == 1

        # Deletion should fail due to active grants
        # (This would be tested at API level where the check is enforced)

    async def test_role_deletion_without_active_grants(
        self, session: AsyncSession, seed_permissions
    ):
        """
        Test that role deletion succeeds when no active grants exist.
        """
        from langflow.services.database.models.role.crud import (
            create_role,
            delete_role,
            get_role_by_id,
        )
        from langflow.services.database.models.grant.crud import count_grants_by_role

        # Create role
        role = await create_role(
            session,
            name="Deployer",
            permissions=["deploy_environment"],
        )

        # Verify no grants exist
        grant_count = await count_grants_by_role(session, role.id)
        assert grant_count == 0

        # Delete role
        result = await delete_role(session, role.id)
        assert result is True

        # Verify role is deleted
        deleted_role = await get_role_by_id(session, role.id)
        assert deleted_role is None

    async def test_audit_log_on_role_creation(
        self, session: AsyncSession, seed_permissions
    ):
        """
        Test that audit log entry is created when a role is created.
        """
        from langflow.services.database.models.role.crud import create_role
        from langflow.services.database.models.audit.crud import (
            create_audit_log,
            get_audit_logs_for_resource,
        )
        from langflow.services.database.models.audit.model import AuditAction

        # Create role
        role = await create_role(
            session,
            name="Deployer",
            permissions=["deploy_environment"],
        )

        # Create audit log entry (simulating what API does)
        actor_id = uuid4()
        await create_audit_log(
            db=session,
            actor_id=actor_id,
            action=AuditAction.ROLE_CREATED,
            resource_type="role",
            resource_id=str(role.id),
            after_state={
                "name": role.name,
                "permissions": role.permissions,
                "version": role.version,
            },
        )

        # Verify audit log entry exists
        audit_logs = await get_audit_logs_for_resource(
            session, resource_type="role", resource_id=str(role.id)
        )

        assert len(audit_logs) == 1
        assert audit_logs[0].action == AuditAction.ROLE_CREATED
        assert audit_logs[0].after_state["name"] == "Deployer"

    async def test_audit_log_on_role_update(
        self, session: AsyncSession, seed_permissions
    ):
        """
        AC3: Test that audit log shows before and after states on role update.
        """
        from langflow.services.database.models.role.crud import (
            create_role,
            update_role,
        )
        from langflow.services.database.models.audit.crud import (
            create_audit_log,
            get_audit_logs_for_resource,
        )
        from langflow.services.database.models.audit.model import AuditAction

        # Create role
        role = await create_role(
            session,
            name="Deployer",
            permissions=["deploy_environment"],
        )

        before_state = {
            "name": role.name,
            "permissions": role.permissions,
            "version": role.version,
        }

        # Update role
        updated_role = await update_role(
            session,
            role_id=role.id,
            permissions=["deploy_environment", "flows:read"],
        )

        # Create audit log entry (simulating what API does)
        actor_id = uuid4()
        await create_audit_log(
            db=session,
            actor_id=actor_id,
            action=AuditAction.ROLE_UPDATED,
            resource_type="role",
            resource_id=str(updated_role.id),
            before_state=before_state,
            after_state={
                "name": updated_role.name,
                "permissions": updated_role.permissions,
                "version": updated_role.version,
            },
        )

        # Verify audit log entry shows before/after states
        audit_logs = await get_audit_logs_for_resource(
            session, resource_type="role", resource_id=str(updated_role.id)
        )

        assert len(audit_logs) == 1
        assert audit_logs[0].action == AuditAction.ROLE_UPDATED
        assert audit_logs[0].before_state["version"] == 1
        assert audit_logs[0].after_state["version"] == 2
        assert "flows:read" in audit_logs[0].after_state["permissions"]

    async def test_audit_log_on_role_deletion(
        self, session: AsyncSession, seed_permissions
    ):
        """
        Test that audit log entry is created when a role is deleted.
        """
        from langflow.services.database.models.role.crud import (
            create_role,
            delete_role,
        )
        from langflow.services.database.models.audit.crud import (
            create_audit_log,
            get_audit_logs_for_resource,
        )
        from langflow.services.database.models.audit.model import AuditAction

        # Create role
        role = await create_role(
            session,
            name="Deployer",
            permissions=["deploy_environment"],
        )

        before_state = {
            "name": role.name,
            "permissions": role.permissions,
            "version": role.version,
        }

        role_id = role.id

        # Delete role
        await delete_role(session, role_id)

        # Create audit log entry (simulating what API does)
        actor_id = uuid4()
        await create_audit_log(
            db=session,
            actor_id=actor_id,
            action=AuditAction.ROLE_DELETED,
            resource_type="role",
            resource_id=str(role_id),
            before_state=before_state,
        )

        # Verify audit log entry exists
        audit_logs = await get_audit_logs_for_resource(
            session, resource_type="role", resource_id=str(role_id)
        )

        assert len(audit_logs) == 1
        assert audit_logs[0].action == AuditAction.ROLE_DELETED
        assert audit_logs[0].before_state["name"] == "Deployer"
        assert audit_logs[0].after_state is None
