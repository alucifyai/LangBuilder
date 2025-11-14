#!/usr/bin/env python3
"""Test script to check RBAC assignments endpoint."""
import asyncio
import sys
sys.path.insert(0, '/Users/Arnab/Documents/GitHub/CG_LangBuilder/LangBuilder/src/backend/base')

from langbuilder.services.database.service import DatabaseService
from langbuilder.services.rbac.service import RBACService
from langbuilder.services.deps import session_scope

async def test_get_assignments():
    """Test getting assignments from RBAC service."""
    try:
        # Create database service
        from langbuilder.services.deps import get_db_service
        db_service = get_db_service()

        # Create RBAC service
        rbac_service = RBACService(db_service)

        # Get all assignments
        print("Fetching assignments...")
        assignments = await rbac_service.get_assignments()

        print(f"\nFound {len(assignments)} assignments:")
        for assignment in assignments:
            print(f"\nAssignment: {assignment.id}")
            print(f"  user_id: {assignment.user_id} (type: {type(assignment.user_id).__name__})")
            print(f"  role_id: {assignment.role_id} (type: {type(assignment.role_id).__name__})")
            print(f"  scope_type: {assignment.scope_type}")
            print(f"  scope_id: {assignment.scope_id}")
            print(f"  is_immutable: {assignment.is_immutable}")
            print(f"  created_at: {assignment.created_at} (type: {type(assignment.created_at).__name__})")
            print(f"  created_by: {assignment.created_by}")

            # Try to convert to dict to see if that works
            try:
                from langbuilder.api.v1.rbac import AssignmentResponse
                response = AssignmentResponse.model_validate(assignment, from_attributes=True)
                print(f"  ✅ Validated successfully")
            except Exception as e:
                print(f"  ❌ Validation failed: {e}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_get_assignments())
