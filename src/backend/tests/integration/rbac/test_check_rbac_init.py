import pytest
import asyncio

@pytest.mark.asyncio
async def test_check_rbac_initialization(client_session):
    """Check if RBAC data is initialized."""
    from sqlmodel import select
    from langbuilder.services.database.models.rbac import Role, Permission, RolePermission
    
    # Check roles
    roles_stmt = select(Role)
    roles_result = await client_session.exec(roles_stmt)
    roles = roles_result.all()
    print(f"\n=== Found {len(roles)} roles:")
    for r in roles:
        print(f"  {r.name} (id: {r.id})")
    
    # Check permissions
    perms_stmt = select(Permission)
    perms_result = await client_session.exec(perms_stmt)
    perms = perms_result.all()
    print(f"\n=== Found {len(perms)} permissions:")
    for p in perms:
        print(f"  {p.name} ({p.scope_type}) - id: {p.id}")
    
    # Check Owner role permissions
    owner_role = [r for r in roles if r.name == "Owner"]
    if owner_role:
        owner_id = owner_role[0].id
        mappings_stmt = (
            select(RolePermission, Permission)
            .join(Permission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == owner_id)
        )
        mappings_result = await client_session.exec(mappings_stmt)
        mappings = mappings_result.all()
        print(f"\n=== Owner role has {len(mappings)} permissions:")
        for _, perm in mappings:
            print(f"  {perm.name} ({perm.scope_type})")
    
    assert len(roles) == 4, f"Expected 4 roles, got {len(roles)}"
    assert len(perms) == 8, f"Expected 8 permissions, got {len(perms)}"
