import pytest
import asyncio
from uuid import uuid4
from sqlmodel import select

@pytest.mark.asyncio
async def test_debug_role_assignment(client, client_session, active_user, test_project, roles):
    """Debug test to check if role assignments are visible."""
    from langbuilder.services.database.models.rbac import UserRoleAssignment
    
    # Check what's in the database after fixture setup
    stmt = select(UserRoleAssignment).where(UserRoleAssignment.user_id == active_user.id)
    result = await client_session.exec(stmt)
    assignments = result.all()
    
    print(f"\n=== Active user: {active_user.id}")
    print(f"=== Test project: {test_project.id}")
    print(f"=== Found {len(assignments)} assignments for active_user:")
    for a in assignments:
        role = roles.get(str(a.role_id))
        print(f"    - Role: {a.role_id}, Scope: {a.scope_type}, Scope ID: {a.scope_id}")
    
    # Now check with a fresh session like the API would
    from langbuilder.services.deps import get_db_service
    db_service = get_db_service()
    async with db_service.with_session() as fresh_session:
        stmt2 = select(UserRoleAssignment).where(UserRoleAssignment.user_id == active_user.id)
        result2 = await fresh_session.exec(stmt2)
        fresh_assignments = result2.all()
        print(f"\n=== With fresh session: Found {len(fresh_assignments)} assignments")
        for a in fresh_assignments:
            print(f"    - Role: {a.role_id}, Scope: {a.scope_type}, Scope ID: {a.scope_id}")
    
    assert len(assignments) > 0, "Should have at least one assignment from test_project fixture"
    assert len(fresh_assignments) > 0, "Fresh session should see the assignments too"
