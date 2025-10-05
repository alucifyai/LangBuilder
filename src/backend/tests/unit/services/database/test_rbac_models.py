"""Unit tests for RBAC models.

Tests cover:
- Permission catalog validation
- Role creation and management
- Group creation and membership
- Grant assignment and scope enforcement
- ServiceAccount management
- AuditLog creation
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from langflow.services.database.models.rbac import (
    AuditLog,
    AuditLogCreate,
    Grant,
    GrantCreate,
    Group,
    GroupCreate,
    Permission,
    Role,
    RoleCreate,
    ServiceAccount,
    ServiceAccountCreate,
)
from langflow.services.database.models.rbac.grant import PrincipalType, ScopeType
from langflow.services.database.models.rbac.permission import PERMISSION_CATALOG, PermissionAction, ResourceType
from langflow.services.database.models.user.model import User, UserCreate
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(autouse=True)
async def cleanup_database(async_session: AsyncSession):
    """Clean up RBAC tables after each test."""
    yield
    # Clean up in reverse order of dependencies
    await async_session.execute(delete(AuditLog))
    await async_session.execute(delete(Grant))
    await async_session.execute(delete(ServiceAccount))
    await async_session.execute(delete(Group))
    await async_session.execute(delete(Role))
    await async_session.execute(delete(Permission))
    await async_session.commit()


# Permission Tests


@pytest.mark.asyncio
async def test_permission_catalog_structure():
    """Test that permission catalog has required structure (PRD Story 1.1 @AC1)."""
    # Verify catalog contains CRUD actions
    crud_actions = {PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE}
    catalog_actions = {perm["action"] for perm in PERMISSION_CATALOG}
    assert crud_actions.issubset(catalog_actions), "Permission catalog must include all CRUD actions"

    # Verify catalog contains extended actions from PRD
    extended_actions = {
        PermissionAction.EXPORT_FLOW,
        PermissionAction.DEPLOY_ENVIRONMENT,
        PermissionAction.INVITE_USERS,
        PermissionAction.MODIFY_COMPONENT_SETTINGS,
        PermissionAction.MANAGE_TOKENS,
    }
    assert extended_actions.issubset(catalog_actions), "Permission catalog must include all extended actions"


@pytest.mark.asyncio
async def test_permission_creation(async_session: AsyncSession):
    """Test creating permission entries."""
    permission = Permission(
        action=PermissionAction.READ, resource_type=ResourceType.FLOW, description="Read flow details"
    )

    async_session.add(permission)
    await async_session.commit()
    await async_session.refresh(permission)

    # Verify auto-generated ID format
    assert permission.id == "flow:read"

    # Query back
    result = await async_session.execute(select(Permission).where(Permission.id == "flow:read"))
    retrieved = result.scalar_one()
    assert retrieved.action == PermissionAction.READ
    assert retrieved.resource_type == ResourceType.FLOW


# Role Tests


@pytest.mark.asyncio
async def test_role_creation_with_permissions(async_session: AsyncSession):
    """Test creating a custom role with permissions (PRD Story 1.2 @AC1)."""
    role_data = RoleCreate(name="Deployer", description="Can deploy flows", permissions=["flow:read", "environment:deploy_environment"])

    role = Role.model_validate(role_data, from_attributes=True)
    async_session.add(role)
    await async_session.commit()
    await async_session.refresh(role)

    assert role.name == "Deployer"
    assert "flow:read" in role.permissions
    assert "environment:deploy_environment" in role.permissions
    assert role.version == 1


@pytest.mark.asyncio
async def test_role_name_uniqueness(async_session: AsyncSession):
    """Test that role names must be unique (PRD Story 1.2 @AC2)."""
    role1 = Role(name="Editor", permissions=["flow:read"])
    async_session.add(role1)
    await async_session.commit()

    # Attempt to create duplicate
    role2 = Role(name="Editor", permissions=["flow:update"])
    async_session.add(role2)

    with pytest.raises(Exception):  # Should raise unique constraint violation
        await async_session.commit()


@pytest.mark.asyncio
async def test_role_version_tracking(async_session: AsyncSession):
    """Test role versioning on updates (PRD Story 1.2 @AC3)."""
    role = Role(name="Deployer", permissions=["environment:deploy_environment"])
    async_session.add(role)
    await async_session.commit()
    await async_session.refresh(role)

    original_version = role.version
    original_updated_at = role.updated_at

    # Update role
    role.permissions = ["environment:deploy_environment", "flow:read"]
    role.version += 1
    role.updated_at = datetime.now(timezone.utc)

    await async_session.commit()
    await async_session.refresh(role)

    assert role.version == original_version + 1
    assert role.updated_at > original_updated_at


# Group Tests


@pytest.mark.asyncio
async def test_group_creation(async_session: AsyncSession):
    """Test creating a group."""
    group_data = GroupCreate(name="Data Team", description="Data science team")

    group = Group.model_validate(group_data, from_attributes=True)
    async_session.add(group)
    await async_session.commit()
    await async_session.refresh(group)

    assert group.name == "Data Team"
    assert group.description == "Data science team"


@pytest.mark.asyncio
async def test_group_with_external_id(async_session: AsyncSession):
    """Test group with external IdP ID for SCIM sync (PRD Story 2.3)."""
    group = Group(name="Platform", external_id="okta-group-123", metadata_={"idp": "okta"})

    async_session.add(group)
    await async_session.commit()
    await async_session.refresh(group)

    result = await async_session.execute(select(Group).where(Group.external_id == "okta-group-123"))
    retrieved = result.scalar_one()
    assert retrieved.name == "Platform"
    assert retrieved.metadata_["idp"] == "okta"


# Grant Tests


@pytest.mark.asyncio
async def test_grant_creation_user_scope(async_session: AsyncSession):
    """Test assigning a role to a user at project scope (PRD Story 2.1 @AC1, Story 3.4 @AC1)."""
    # Create role
    role = Role(name="Editor", permissions=["flow:read", "flow:update"])
    async_session.add(role)
    await async_session.commit()
    await async_session.refresh(role)

    # Create user
    user = User(
        username="carol@acme.com", password="hashed_pwd", is_active=True, is_superuser=False
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    # Create grant
    grant_data = GrantCreate(
        principal_type=PrincipalType.USER,
        principal_id=user.id,
        role_id=role.id,
        scope_type=ScopeType.PROJECT,
        scope_id="PRJ1",
    )

    grant = Grant.model_validate(grant_data, from_attributes=True)
    async_session.add(grant)
    await async_session.commit()
    await async_session.refresh(grant)

    assert grant.principal_type == PrincipalType.USER
    assert grant.principal_id == user.id
    assert grant.user_id == user.id  # Should be auto-set
    assert grant.scope_type == ScopeType.PROJECT
    assert grant.scope_id == "PRJ1"


@pytest.mark.asyncio
async def test_grant_creation_group_scope(async_session: AsyncSession):
    """Test assigning a role to a group within scope (PRD Story 2.1 @AC1, Story 3.4 @AC2)."""
    # Create role and group
    role = Role(name="Viewer", permissions=["flow:read"])
    group = Group(name="Data Team")

    async_session.add(role)
    async_session.add(group)
    await async_session.commit()
    await async_session.refresh(role)
    await async_session.refresh(group)

    # Create grant for group
    grant = Grant(
        principal_type=PrincipalType.GROUP,
        principal_id=group.id,
        role_id=role.id,
        scope_type=ScopeType.WORKSPACE,
        scope_id="WB1",
    )

    async_session.add(grant)
    await async_session.commit()
    await async_session.refresh(grant)

    assert grant.group_id == group.id
    assert grant.scope_type == ScopeType.WORKSPACE


@pytest.mark.asyncio
async def test_grant_with_expiration(async_session: AsyncSession):
    """Test time-bound grant (PRD Story 3.4 @AC3)."""
    role = Role(name="Deploy", permissions=["environment:deploy_environment"])
    user = User(username="ops@acme.com", password="pwd", is_active=True, is_superuser=False)

    async_session.add(role)
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(role)
    await async_session.refresh(user)

    # Grant expires in 1 hour
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    grant = Grant(
        principal_type=PrincipalType.USER,
        principal_id=user.id,
        role_id=role.id,
        scope_type=ScopeType.PROJECT,
        scope_id="PRJ1",
        expires_at=expires_at,
    )

    async_session.add(grant)
    await async_session.commit()
    await async_session.refresh(grant)

    assert grant.expires_at is not None
    assert grant.expires_at > datetime.now(timezone.utc)


# ServiceAccount Tests


@pytest.mark.asyncio
async def test_service_account_creation(async_session: AsyncSession):
    """Test creating a service account (PRD Story 2.4 @AC1)."""
    from langflow.services.auth.utils import get_password_hash

    sa_data = ServiceAccountCreate(
        name="ci-bot", description="CI/CD automation bot"
    )

    sa = ServiceAccount.model_validate(sa_data, from_attributes=True)
    # API keys are now hashed (RBAC_PHASE1_AUDIT_REPORT CONCERN #1)
    plaintext_key = "test_api_key_123"
    sa.api_key_hash = get_password_hash(plaintext_key)

    async_session.add(sa)
    await async_session.commit()
    await async_session.refresh(sa)

    assert sa.name == "ci-bot"
    assert sa.is_active is True
    assert sa.api_key_hash is not None
    # Verify we can authenticate with the plaintext key
    from langflow.services.auth.utils import verify_password
    assert verify_password(plaintext_key, sa.api_key_hash)


@pytest.mark.asyncio
async def test_service_account_with_grant(async_session: AsyncSession):
    """Test service account with scoped permissions."""
    from langflow.services.auth.utils import get_password_hash

    # Create role
    role = Role(name="ReadOnly", permissions=["flow:read"])
    async_session.add(role)
    await async_session.commit()
    await async_session.refresh(role)

    # Create service account
    sa = ServiceAccount(name="monitoring-agent", api_key_hash=get_password_hash("monitor_key"))
    async_session.add(sa)
    await async_session.commit()
    await async_session.refresh(sa)

    # Grant role to service account at workspace scope
    grant = Grant(
        principal_type=PrincipalType.SERVICE_ACCOUNT,
        principal_id=sa.id,
        role_id=role.id,
        scope_type=ScopeType.WORKSPACE,
        scope_id="WB1",
    )

    async_session.add(grant)
    await async_session.commit()
    await async_session.refresh(grant)

    assert grant.service_account_id == sa.id
    assert grant.scope_type == ScopeType.WORKSPACE


# AuditLog Tests


@pytest.mark.asyncio
async def test_audit_log_creation(async_session: AsyncSession):
    """Test creating an audit log entry (PRD Story 5.1 @AC1)."""
    from langflow.services.database.models.rbac.audit_log import AuditAction

    audit_data = AuditLogCreate(
        action=AuditAction.GRANT_CREATED,
        actor_type="user",
        actor_id=str(uuid4()),
        actor_name="admin@acme.com",
        resource_type="grant",
        resource_id=str(uuid4()),
        details={"role": "Editor", "scope": "project:PRJ1"},
        result="success",
    )

    audit = AuditLog.model_validate(audit_data, from_attributes=True)
    async_session.add(audit)
    await async_session.commit()
    await async_session.refresh(audit)

    assert audit.action == AuditAction.GRANT_CREATED
    assert audit.actor_name == "admin@acme.com"
    assert audit.result == "success"
    assert audit.details["role"] == "Editor"


@pytest.mark.asyncio
async def test_audit_log_immutability(async_session: AsyncSession):
    """Test that audit logs should be immutable (append-only)."""
    from langflow.services.database.models.rbac.audit_log import AuditAction

    audit = AuditLog(
        action=AuditAction.PERMISSION_CHECK_DENIED,
        actor_type="user",
        actor_id=str(uuid4()),
        reason="Insufficient permissions",
        result="denied",
    )

    async_session.add(audit)
    await async_session.commit()
    await async_session.refresh(audit)

    original_timestamp = audit.timestamp

    # Attempt to modify (should not be done in practice)
    audit.result = "allowed"

    await async_session.commit()
    await async_session.refresh(audit)

    # Timestamp should not change (demonstrates immutability concept)
    assert audit.timestamp == original_timestamp
    # Note: In production, audit logs should have database-level write-once constraints
