#!/usr/bin/env python3
"""Test script to check RBAC roles endpoint."""
import asyncio
import sys
sys.path.insert(0, '/Users/Arnab/Documents/GitHub/CG_LangBuilder/LangBuilder/src/backend/base')

from langbuilder.services.database.service import DatabaseService
from langbuilder.services.rbac.service import RBACService
from langbuilder.services.deps import get_db_service

async def test_list_roles():
    """Test listing roles from RBAC service."""
    try:
        # Create database service
        db_service = get_db_service()

        # Create RBAC service
        rbac_service = RBACService(db_service)

        # Get all roles
        print("Fetching roles...")
        roles = await rbac_service.list_roles()

        print(f"\nFound {len(roles)} roles:")
        for role in roles:
            print(f"\nRole: {role.id}")
            print(f"  name: {role.name}")
            print(f"  description: {role.description}")
            print(f"  is_system: {role.is_system}")
            print(f"  type(id): {type(role.id).__name__}")

            # Try to convert to RoleResponse to see if validation works
            try:
                from langbuilder.api.v1.rbac import RoleResponse
                response = RoleResponse.model_validate(role, from_attributes=True)
                print(f"  ✅ Validated successfully as RoleResponse")
                print(f"  Response id: {response.id} (type: {type(response.id).__name__})")
            except Exception as e:
                print(f"  ❌ Validation failed: {e}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_list_roles())
