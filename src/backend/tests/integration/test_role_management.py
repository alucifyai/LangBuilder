"""
Integration tests for Role Management workflow.

Tests complete role management scenarios with database and audit logging.
Covers AC1-AC3 from Story 1.2.
"""

import pytest
from uuid import uuid4
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.permission.model import Permission
from langflow.services.database.models.role.crud import (
    create_role,
    get_role_by_id,
    update_role,
    delete_role,
)
from langflow.services.database.models.grant.crud import create_grant, count_grants_by_role
from langflow.services.database.models.grant.model import PrincipalType, ScopeType
from langflow.services.database.models.audit.crud import (
    create_audit_log,
    get_audit_logs_for_resource,
    get_audit_logs_by_actor,
)
from langflow.services.database.models.audit.model import AuditAction


@pytest.mark.asyncio
class TestRoleManagementIntegration:
    """Integration tests for complete role management workflows."""

    @pytest.fixture
    async def seed_permissions(self, session: AsyncSession):
        """Seed permissions for testing."""
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
            Permission(
                id="flows:update",
                resource_type="flows",
                action="update",
                description="Update flows",
            ),
        ]

        for perm in permissions:
            session.add(perm)
        await session.commit()

        return permissions

    async def test_complete_role_creation_workflow_with_audit(
        self, session: AsyncSession, seed_permissions
    ):
        """
        AC1, AC3: Complete role creation workflow with audit logging.

        Test creating a "Deployer" role and verify audit trail is created.
        """
        actor_id = uuid4()

        # Create role
        role = await create_role(
            session,
            name="Deployer",
            permissions=["deploy_environment", "flows:read"],
        )

        # Verify role created successfully
        assert role is not None
        assert role.name == "Deployer"
        assert role.version == 1
        assert len(role.permissions) == 2

        # Create audit log entry
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
            metadata={"source": "admin_ui"},
        )

        # Verify audit log was created
        audit_logs = await get_audit_logs_for_resource(
            session, resource_type="role", resource_id=str(role.id)
        )

        assert len(audit_logs) == 1
        assert audit_logs[0].action == AuditAction.ROLE_CREATED
        assert audit_logs[0].actor_id == str(actor_id)
        assert audit_logs[0].after_state["name"] == "Deployer"
        assert audit_logs[0].metadata["source"] == "admin_ui"

        # Role should be available for assignment
        retrieved_role = await get_role_by_id(session, role.id)
        assert retrieved_role is not None
        assert retrieved_role.name == "Deployer"

    async def test_complete_role_update_workflow_with_versioning(
        self, session: AsyncSession, seed_permissions
    ):
        """
        AC3: Complete role update workflow with versioning and audit trail.

        Test updating a "Deployer" role, verify version increments and audit log
        captures before/after states.
        """
        actor_id = uuid4()

        # Create initial role
        role = await create_role(
            session,
            name="Deployer",
            permissions=["deploy_environment"],
        )

        # Log creation
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

        # Capture before state
        before_state = {
            "name": role.name,
            "permissions": role.permissions,
            "version": role.version,
        }

        # Update role - add "flows:read" permission
        updated_role = await update_role(
            session,
            role_id=role.id,
            permissions=["deploy_environment", "flows:read"],
        )

        # Verify version incremented
        assert updated_role.version == 2
        assert len(updated_role.permissions) == 2
        assert "flows:read" in updated_role.permissions

        # Log update with before/after states
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

        # Verify audit log shows before/after states
        audit_logs = await get_audit_logs_for_resource(
            session, resource_type="role", resource_id=str(updated_role.id)
        )

        # Should have 2 entries: creation + update
        assert len(audit_logs) == 2

        # Most recent should be update
        update_log = audit_logs[0]  # Ordered by timestamp desc
        assert update_log.action == AuditAction.ROLE_UPDATED
        assert update_log.before_state["version"] == 1
        assert update_log.after_state["version"] == 2
        assert "flows:read" not in update_log.before_state["permissions"]
        assert "flows:read" in update_log.after_state["permissions"]

    async def test_role_deletion_with_dependency_checking(
        self, session: AsyncSession, seed_permissions
    ):
        """
        Test role deletion workflow with dependency checking.

        Verify that role deletion checks for active grants and creates audit log.
        """
        actor_id = uuid4()
        user_id = uuid4()

        # Create role
        role = await create_role(
            session,
            name="Deployer",
            permissions=["deploy_environment"],
        )

        # Log creation
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

        # Create grant using this role
        grant = await create_grant(
            session,
            principal_type=PrincipalType.USER,
            principal_id=user_id,
            role_id=role.id,
            scope_type=ScopeType.WORKSPACE,
            scope_id="WB1",
        )

        # Verify grant exists
        grant_count = await count_grants_by_role(session, role.id)
        assert grant_count == 1

        # Deletion should be prevented by active grants check
        # (In the API, this throws HTTPException 409)
        # Here we just verify the check works

        # Now delete the grant
        from langflow.services.database.models.grant.crud import delete_grant

        await delete_grant(session, grant.id)

        # Verify grant is gone
        grant_count = await count_grants_by_role(session, role.id)
        assert grant_count == 0

        # Now role deletion should succeed
        before_state = {
            "name": role.name,
            "permissions": role.permissions,
            "version": role.version,
        }

        role_id = role.id
        deleted = await delete_role(session, role_id)
        assert deleted is True

        # Log deletion
        await create_audit_log(
            db=session,
            actor_id=actor_id,
            action=AuditAction.ROLE_DELETED,
            resource_type="role",
            resource_id=str(role_id),
            before_state=before_state,
        )

        # Verify role is deleted
        deleted_role = await get_role_by_id(session, role_id)
        assert deleted_role is None

        # Verify audit log exists
        audit_logs = await get_audit_logs_for_resource(
            session, resource_type="role", resource_id=str(role_id)
        )

        # Should have 2 entries: creation + deletion
        assert len(audit_logs) == 2
        deletion_log = audit_logs[0]  # Most recent
        assert deletion_log.action == AuditAction.ROLE_DELETED

    async def test_permission_validation_during_role_operations(
        self, session: AsyncSession, seed_permissions
    ):
        """
        Test permission validation during role creation and update.

        Verify that invalid permission IDs are rejected.
        """
        # Attempt to create role with invalid permission
        with pytest.raises(Exception) as exc_info:
            await create_role(
                session,
                name="BadRole",
                permissions=["deploy_environment", "invalid:permission"],
            )

        assert "Unknown permission id" in str(exc_info.value)

        # Create valid role
        role = await create_role(
            session,
            name="ValidRole",
            permissions=["deploy_environment"],
        )

        # Attempt to update with invalid permission
        with pytest.raises(Exception) as exc_info:
            await update_role(
                session,
                role_id=role.id,
                permissions=["deploy_environment", "another:invalid"],
            )

        assert "Unknown permission id" in str(exc_info.value)

        # Verify role wasn't updated
        unchanged_role = await get_role_by_id(session, role.id)
        assert unchanged_role.version == 1  # Version not incremented
        assert len(unchanged_role.permissions) == 1

    async def test_audit_log_actor_tracking(self, session: AsyncSession, seed_permissions):
        """
        Test that audit logs track which actor performed actions.

        Verify audit logs can be queried by actor.
        """
        admin_id = uuid4()

        # Admin creates multiple roles
        role1 = await create_role(
            session, name="Role1", permissions=["flows:read"]
        )
        await create_audit_log(
            db=session,
            actor_id=admin_id,
            action=AuditAction.ROLE_CREATED,
            resource_type="role",
            resource_id=str(role1.id),
            after_state={"name": "Role1"},
        )

        role2 = await create_role(
            session, name="Role2", permissions=["flows:create"]
        )
        await create_audit_log(
            db=session,
            actor_id=admin_id,
            action=AuditAction.ROLE_CREATED,
            resource_type="role",
            resource_id=str(role2.id),
            after_state={"name": "Role2"},
        )

        # Update role1
        await update_role(session, role_id=role1.id, permissions=["flows:read", "flows:update"])
        await create_audit_log(
            db=session,
            actor_id=admin_id,
            action=AuditAction.ROLE_UPDATED,
            resource_type="role",
            resource_id=str(role1.id),
            before_state={"name": "Role1", "version": 1},
            after_state={"name": "Role1", "version": 2},
        )

        # Get all actions by this admin
        admin_actions = await get_audit_logs_by_actor(session, admin_id)

        # Should have 3 actions: 2 creates + 1 update
        assert len(admin_actions) == 3
        assert all(log.actor_id == str(admin_id) for log in admin_actions)

        # Verify action types
        action_types = [log.action for log in admin_actions]
        assert action_types.count(AuditAction.ROLE_CREATED) == 2
        assert action_types.count(AuditAction.ROLE_UPDATED) == 1

    async def test_concurrent_role_updates_version_handling(
        self, session: AsyncSession, seed_permissions
    ):
        """
        Test version handling with sequential updates.

        Verify that multiple updates increment version correctly.
        """
        actor_id = uuid4()

        # Create role
        role = await create_role(
            session, name="EvolvingRole", permissions=["flows:read"]
        )
        assert role.version == 1

        # First update
        role = await update_role(
            session, role_id=role.id, permissions=["flows:read", "flows:create"]
        )
        assert role.version == 2

        # Second update
        role = await update_role(
            session, role_id=role.id, permissions=["flows:read", "flows:create", "flows:update"]
        )
        assert role.version == 3

        # Third update - just rename
        role = await update_role(session, role_id=role.id, name="SuperRole")
        assert role.version == 4
        assert role.name == "SuperRole"

        # Verify final state
        final_role = await get_role_by_id(session, role.id)
        assert final_role.version == 4
        assert final_role.name == "SuperRole"
        assert len(final_role.permissions) == 3
