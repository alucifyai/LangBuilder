"""Quick test to verify RBAC permissions for langbuilder superuser."""
import asyncio
from sqlmodel import select

from langbuilder.services.database.models.user.crud import get_user_by_username
from langbuilder.services.deps import get_db_service
from langbuilder.services.rbac.service import RBACService


async def test_langbuilder_permissions():
    """Test that langbuilder user has Global Admin permissions."""
    db_service = get_db_service()
    async with db_service.with_session() as session:
        # Get the langbuilder user
        user = await get_user_by_username(session, "langbuilder")
        if not user:
            print("❌ ERROR: langbuilder user not found")
            return False

        print(f"✓ Found user: {user.username} (ID: {user.id}, is_superuser: {user.is_superuser})")

    # Initialize RBAC service with database service (not session)
    rbac_service = RBACService(db_service)

    # Test Global Admin permissions (should have access to everything)
    test_cases = [
        ("Create", "Flow", None),
        ("Read", "Flow", None),
        ("Update", "Flow", None),
        ("Delete", "Flow", None),
        ("Create", "Project", None),
        ("Read", "Project", None),
        ("Update", "Project", None),
        ("Delete", "Project", None),
    ]

    all_passed = True
    for permission_name, scope_type, scope_id in test_cases:
        has_permission = await rbac_service.can_access(
            user_id=user.id,
            permission_name=permission_name,
            scope_type=scope_type,
            scope_id=scope_id
        )

        status = "✓" if has_permission else "✗"
        print(f"{status} {permission_name} on {scope_type}: {has_permission}")

        if not has_permission:
            all_passed = False

    print("\n" + "="*50)
    if all_passed:
        print("✅ SUCCESS: All RBAC permissions working correctly!")
        print("The langbuilder user has Global Admin access.")
    else:
        print("❌ FAILURE: Some permissions are missing!")
        print("The Global Admin role assignment may not be working.")
    print("="*50)

    return all_passed


if __name__ == "__main__":
    result = asyncio.run(test_langbuilder_permissions())
    exit(0 if result else 1)
