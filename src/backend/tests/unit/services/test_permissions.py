"""Unit tests for Permission Enforcement Service."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from langflow.services.auth.permissions import (
    PermissionDenied,
    check_permission,
    require_permission,
    get_user_permissions,
    check_any_permission,
    check_all_permissions,
    get_scope_rank,
)
from langflow.services.database.models.grant.model import PrincipalType, ScopeType


@pytest.mark.asyncio
async def test_superuser_has_all_permissions(session, active_user):
    """Test that superusers have all permissions."""
    active_user.is_superuser = True

    has_perm = await check_permission(
        db=session,
        user=active_user,
        permission="flows:delete",
        scope_type=ScopeType.FLOW,
        scope_id="any-flow",
    )

    assert has_perm is True


@pytest.mark.asyncio
async def test_user_without_grant_denied(session, active_user):
    """Test that users without grants are denied."""
    active_user.is_superuser = False

    has_perm = await check_permission(
        db=session,
        user=active_user,
        permission="flows:read",
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    assert has_perm is False


@pytest.mark.asyncio
async def test_user_with_exact_grant_allowed(session, active_user):
    """Test that users with exact matching grants are allowed."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    active_user.is_superuser = False

    # Create role with permission
    role = await create_role(session, name="Reader", permissions=["flows:read"])

    # Grant role to user at specific flow
    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    # Check permission at same flow
    has_perm = await check_permission(
        db=session,
        user=active_user,
        permission="flows:read",
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    assert has_perm is True


@pytest.mark.asyncio
async def test_user_with_higher_scope_grant_allowed(session, active_user):
    """Test that grants at higher scopes cascade down."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    active_user.is_superuser = False

    # Create role with permission
    role = await create_role(session, name="Reader", permissions=["flows:read"])

    # Grant role at workspace level
    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.WORKSPACE,
        scope_id="workspace-1",
    )

    # Check permission at project level (lower scope)
    has_perm = await check_permission(
        db=session,
        user=active_user,
        permission="flows:read",
        scope_type=ScopeType.PROJECT,
        scope_id="project-1",
    )

    assert has_perm is True


@pytest.mark.asyncio
async def test_user_with_lower_scope_grant_denied_at_higher(session, active_user):
    """Test that grants at lower scopes don't grant access to higher scopes."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    active_user.is_superuser = False

    # Create role with permission
    role = await create_role(session, name="Reader", permissions=["flows:read"])

    # Grant role at flow level (low scope)
    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    # Check permission at workspace level (higher scope)
    has_perm = await check_permission(
        db=session,
        user=active_user,
        permission="flows:read",
        scope_type=ScopeType.WORKSPACE,
        scope_id="workspace-1",
    )

    assert has_perm is False


@pytest.mark.asyncio
async def test_expired_grant_denied(session, active_user):
    """Test that expired grants don't grant permissions."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    active_user.is_superuser = False

    # Create role with permission
    role = await create_role(session, name="Reader", permissions=["flows:read"])

    # Create expired grant
    expired_time = datetime.now(timezone.utc) - timedelta(days=1)
    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
        expires_at=expired_time,
    )

    has_perm = await check_permission(
        db=session,
        user=active_user,
        permission="flows:read",
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    assert has_perm is False


@pytest.mark.asyncio
async def test_require_permission_raises_on_denial(session, active_user):
    """Test that require_permission raises PermissionDenied."""
    active_user.is_superuser = False

    with pytest.raises(PermissionDenied) as exc_info:
        await require_permission(
            db=session,
            user=active_user,
            permission="flows:delete",
            scope_type=ScopeType.FLOW,
            scope_id="flow-1",
        )

    assert "flows:delete" in str(exc_info.value)
    assert exc_info.value.required_permission == "flows:delete"


@pytest.mark.asyncio
async def test_require_permission_succeeds_with_grant(session, active_user):
    """Test that require_permission doesn't raise with proper grant."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    active_user.is_superuser = False

    role = await create_role(session, name="Admin", permissions=["flows:delete"])
    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    # Should not raise
    await require_permission(
        db=session,
        user=active_user,
        permission="flows:delete",
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )


@pytest.mark.asyncio
async def test_get_user_permissions(session, active_user):
    """Test getting all permissions a user has at a scope."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    active_user.is_superuser = False

    role1 = await create_role(session, name="Reader", permissions=["flows:read"])
    role2 = await create_role(session, name="Writer", permissions=["flows:write", "flows:update"])

    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role1.id,
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role2.id,
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    permissions = await get_user_permissions(
        db=session,
        user=active_user,
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    assert "flows:read" in permissions
    assert "flows:write" in permissions
    assert "flows:update" in permissions


@pytest.mark.asyncio
async def test_check_any_permission(session, active_user):
    """Test checking if user has any of multiple permissions."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    active_user.is_superuser = False

    role = await create_role(session, name="Reader", permissions=["flows:read"])
    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    # User has flows:read, so should return True
    has_any = await check_any_permission(
        db=session,
        user=active_user,
        permissions=["flows:read", "flows:write"],
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    assert has_any is True

    # User doesn't have any of these
    has_any = await check_any_permission(
        db=session,
        user=active_user,
        permissions=["flows:write", "flows:delete"],
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    assert has_any is False


@pytest.mark.asyncio
async def test_check_all_permissions(session, active_user):
    """Test checking if user has all of multiple permissions."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    active_user.is_superuser = False

    role = await create_role(
        session, name="Editor", permissions=["flows:read", "flows:write"]
    )
    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    # User has both
    has_all = await check_all_permissions(
        db=session,
        user=active_user,
        permissions=["flows:read", "flows:write"],
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    assert has_all is True

    # User doesn't have flows:delete
    has_all = await check_all_permissions(
        db=session,
        user=active_user,
        permissions=["flows:read", "flows:delete"],
        scope_type=ScopeType.FLOW,
        scope_id="flow-1",
    )

    assert has_all is False


def test_scope_hierarchy():
    """Test scope rank ordering."""
    assert get_scope_rank(ScopeType.WORKSPACE) < get_scope_rank(ScopeType.PROJECT)
    assert get_scope_rank(ScopeType.PROJECT) < get_scope_rank(ScopeType.ENVIRONMENT)
    assert get_scope_rank(ScopeType.ENVIRONMENT) < get_scope_rank(ScopeType.FLOW)
    assert get_scope_rank(ScopeType.FLOW) < get_scope_rank(ScopeType.COMPONENT)
