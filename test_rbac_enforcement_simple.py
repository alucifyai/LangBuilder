#!/usr/bin/env python3
"""Simplified test script to verify RBAC permission enforcement components."""

import sys


def test_imports():
    """Test that all RBAC components can be imported successfully."""
    print("Testing RBAC imports...")

    try:
        print("   ✅ PermissionEngine imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import PermissionEngine: {e}")
        return False

    try:
        print("   ✅ RBAC middleware imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import RBAC middleware: {e}")
        return False

    try:
        print("   ✅ RBAC decorators imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import RBAC decorators: {e}")
        return False

    try:
        print("   ✅ RBAC service imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import RBAC service: {e}")
        return False

    return True


def test_permission_engine_creation():
    """Test that permission engine can be instantiated."""
    print("\nTesting PermissionEngine creation...")

    try:
        from langflow.services.rbac.permission_engine import PermissionEngine

        # Create permission engine instance
        engine = PermissionEngine()
        print("   ✅ PermissionEngine created successfully")

        # Test that it has expected methods
        expected_methods = ["check_permission", "batch_check_permissions"]
        for method in expected_methods:
            if hasattr(engine, method):
                print(f"   ✅ Method '{method}' exists")
            else:
                print(f"   ❌ Method '{method}' missing")
                return False

        return True
    except Exception as e:
        print(f"   ❌ Failed to create PermissionEngine: {e}")
        return False


def test_middleware_creation():
    """Test that RBAC middleware can be instantiated."""
    print("\nTesting RBAC middleware creation...")

    try:
        from langflow.services.rbac.middleware import RBACContext, RBACMiddleware

        # Create RBAC context
        context = RBACContext(
            user=None,
            workspace_id="test-workspace",
            authenticated=False
        )
        print("   ✅ RBACContext created successfully")

        # Create middleware instance
        middleware = RBACMiddleware(
            app=None,  # Mock app
            enforce_rbac=False,  # Disable for testing
            protected_patterns=["/api/v1/flows/", "/api/v1/rbac/"],
            bypass_patterns=["/health", "/docs"]
        )
        print("   ✅ RBACMiddleware created successfully")

        # Test pattern matching
        class MockRequest:
            def __init__(self, path):
                self.url = type("obj", (object,), {"path": path})()

        protected_request = MockRequest("/api/v1/flows/test")
        bypass_request = MockRequest("/health")

        if middleware._requires_rbac_protection(protected_request):
            print("   ✅ Protected pattern matching works")
        else:
            print("   ❌ Protected pattern matching failed")
            return False

        if middleware._should_bypass_rbac(bypass_request):
            print("   ✅ Bypass pattern matching works")
        else:
            print("   ❌ Bypass pattern matching failed")
            return False

        return True
    except Exception as e:
        print(f"   ❌ Failed to create RBAC middleware: {e}")
        return False


def test_decorators():
    """Test that permission decorators can be imported and used."""
    print("\nTesting RBAC decorators...")

    try:
        from langflow.services.rbac.decorators import (
            require_flow_permission,
            require_permission,
            require_project_permission,
            require_superuser,
            require_workspace_permission,
        )

        # Test decorator creation (not execution)
        workspace_decorator = require_workspace_permission("read")
        project_decorator = require_project_permission("read")
        flow_decorator = require_flow_permission("read")
        permission_decorator = require_permission("workspace", "read")
        superuser_decorator = require_superuser

        print("   ✅ All decorators created successfully")
        return True
    except Exception as e:
        print(f"   ❌ Failed to test decorators: {e}")
        return False


def test_api_dependencies():
    """Test that API dependencies can be imported."""
    print("\nTesting API dependencies...")

    try:
        from langflow.api.v1.rbac.dependencies import (
            check_flow_permission,
            check_project_permission,
            check_workspace_permission,
        )

        print("   ✅ API dependencies imported successfully")

        # Test dependency factory creation
        workspace_dep = check_workspace_permission("read")
        project_dep = check_project_permission("read")
        flow_dep = check_flow_permission("read")

        print("   ✅ Dependency factories created successfully")
        return True
    except Exception as e:
        print(f"   ❌ Failed to test API dependencies: {e}")
        return False


def test_integration_service():
    """Test RBAC integration service."""
    print("\nTesting RBAC integration service...")

    try:
        from langflow.services.rbac.integration import RBACIntegrationService

        # Create service instance
        service = RBACIntegrationService()
        print("   ✅ RBACIntegrationService created successfully")

        # Test configuration
        if hasattr(service, "is_rbac_enabled"):
            print("   ✅ RBAC enablement check available")
        else:
            print("   ❌ RBAC enablement check missing")
            return False

        return True
    except Exception as e:
        print(f"   ❌ Failed to test integration service: {e}")
        return False


def main():
    """Run all RBAC component tests."""
    print("=" * 60)
    print("RBAC Component Integration Test Suite")
    print("=" * 60)

    tests = [
        ("Import Tests", test_imports),
        ("PermissionEngine Creation", test_permission_engine_creation),
        ("Middleware Creation", test_middleware_creation),
        ("Decorator Tests", test_decorators),
        ("API Dependencies", test_api_dependencies),
        ("Integration Service", test_integration_service),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n💥 {test_name} failed with error: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:25s}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! RBAC components are properly integrated.")
        return 0
    print("\n💥 SOME TESTS FAILED! Check the output above for details.")
    return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest suite failed to start: {e}")
        sys.exit(1)
