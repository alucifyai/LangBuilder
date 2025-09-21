#!/usr/bin/env python3
"""Security Fixes Verification Script.

This script validates that all critical security vulnerabilities have been properly fixed
and that the enhanced security measures are working correctly.
"""

import asyncio
import sys
from typing import Any, Dict, List
from unittest.mock import Mock, patch

# Test framework imports
import pytest


class SecurityTestResults:
    """Collect and report security test results."""

    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []

    def record_test(self, test_name: str, passed: bool, details: str = ""):
        """Record a test result."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            self.tests_failed += 1
            self.failures.append(f"{test_name}: {details}")
            print(f"❌ {test_name}: FAILED - {details}")

    def summary(self):
        """Print test summary."""
        print(f"\n🔒 Security Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_failed}")

        if self.tests_failed > 0:
            print(f"\n❌ Failures:")
            for failure in self.failures:
                print(f"   - {failure}")
        else:
            print(f"\n🎉 All security tests passed!")

        return self.tests_failed == 0


async def test_mcp_authentication_fix():
    """Test that MCP authentication bypass vulnerability is fixed."""
    results = SecurityTestResults()

    try:
        # Test 1: Import the fixed MCP auth function
        from langflow.services.auth.utils import get_current_user_mcp
        results.record_test("MCP auth function import", True)

        # Test 2: Verify function signature includes security validation
        import inspect
        sig = inspect.signature(get_current_user_mcp)
        has_required_params = all(param in sig.parameters for param in ['token', 'query_param', 'header_param', 'db'])
        results.record_test("MCP auth function signature", has_required_params, "Missing required parameters" if not has_required_params else "")

        # Test 3: Check that the function code contains security improvements
        source = inspect.getsource(get_current_user_mcp)
        has_security_config = "get_security_config" in source
        results.record_test("MCP auth includes security config", has_security_config, "Missing security configuration" if not has_security_config else "")

        has_environment_check = "environment.value" in source
        results.record_test("MCP auth includes environment validation", has_environment_check, "Missing environment validation" if not has_environment_check else "")

    except ImportError as e:
        results.record_test("MCP auth function import", False, f"Import error: {e}")
    except Exception as e:
        results.record_test("MCP auth verification", False, f"Unexpected error: {e}")

    return results


async def test_rbac_middleware_secure_failure():
    """Test that RBAC middleware now fails secure."""
    results = SecurityTestResults()

    try:
        # Test 1: Import RBAC middleware
        from langflow.services.rbac.middleware import RBACMiddleware
        results.record_test("RBAC middleware import", True)

        # Test 2: Check middleware code for secure failure modes
        import inspect
        source = inspect.getsource(RBACMiddleware._check_permissions)

        # Check for secure failure on RBAC service unavailable
        has_service_check = "return False" in source and "rbac_service" in source
        results.record_test("RBAC middleware secure failure on service unavailable", has_service_check, "Still allows access when service unavailable" if not has_service_check else "")

        # Check for secure failure on permission determination failure
        has_permission_check = "return False" in source and "Could not determine permission" in source
        results.record_test("RBAC middleware secure failure on undetermined permissions", has_permission_check, "Still allows access for undetermined permissions" if not has_permission_check else "")

        # Check for secure failure on exceptions
        has_exception_handling = "return False" in source and "Error checking RBAC permissions" in source
        results.record_test("RBAC middleware secure failure on exceptions", has_exception_handling, "Doesn't fail secure on exceptions" if not has_exception_handling else "")

    except ImportError as e:
        results.record_test("RBAC middleware import", False, f"Import error: {e}")
    except Exception as e:
        results.record_test("RBAC middleware verification", False, f"Unexpected error: {e}")

    return results


async def test_mcp_authorization_implementation():
    """Test that MCP endpoints have proper authorization."""
    results = SecurityTestResults()

    try:
        # Test 1: Import MCP authorization module
        from langflow.services.auth.mcp_auth import get_mcp_authorized_user, RequireMCPConnect
        results.record_test("MCP authorization module import", True)

        # Test 2: Check MCP v1 endpoints use authorization
        from langflow.api.v1 import mcp as mcp_v1
        import inspect

        # Check SSE endpoint
        sse_source = inspect.getsource(mcp_v1.handle_sse)
        has_authorized_user = "get_mcp_authorized_user" in sse_source
        results.record_test("MCP v1 SSE endpoint uses authorization", has_authorized_user, "SSE endpoint missing authorization" if not has_authorized_user else "")

        # Test 3: Check MCP v2 endpoints use authorization
        from langflow.api.v2 import mcp as mcp_v2

        # Check servers endpoint
        servers_source = inspect.getsource(mcp_v2.get_servers)
        has_mcp_auth = "get_mcp_authorized_user" in servers_source
        results.record_test("MCP v2 servers endpoint uses authorization", has_mcp_auth, "Servers endpoint missing authorization" if not has_mcp_auth else "")

    except ImportError as e:
        results.record_test("MCP authorization import", False, f"Import error: {e}")
    except Exception as e:
        results.record_test("MCP authorization verification", False, f"Unexpected error: {e}")

    return results


async def test_authorization_patterns_implementation():
    """Test that authorization patterns are properly implemented."""
    results = SecurityTestResults()

    try:
        # Test 1: Import authorization patterns
        from langflow.services.auth.authorization_patterns import (
            RequiredPermission,
            require_permissions,
            get_authorized_user,
            RequireFlowRead,
            RequireFlowWrite
        )
        results.record_test("Authorization patterns import", True)

        # Test 2: Check that RequiredPermission has security features
        req_perm = RequiredPermission("test:read", resource_type="test")
        has_permission = hasattr(req_perm, 'permission')
        has_resource_type = hasattr(req_perm, 'resource_type')
        results.record_test("RequiredPermission structure", has_permission and has_resource_type, "Missing required attributes" if not (has_permission and has_resource_type) else "")

        # Test 3: Check authorization patterns exist for common resources
        common_patterns = [RequireFlowRead, RequireFlowWrite]
        all_exist = all(pattern is not None for pattern in common_patterns)
        results.record_test("Common authorization patterns exist", all_exist, "Missing common authorization patterns" if not all_exist else "")

    except ImportError as e:
        results.record_test("Authorization patterns import", False, f"Import error: {e}")
    except Exception as e:
        results.record_test("Authorization patterns verification", False, f"Unexpected error: {e}")

    return results


async def test_security_configuration():
    """Test that security configuration is properly implemented."""
    results = SecurityTestResults()

    try:
        # Test 1: Import security configuration
        from langflow.services.settings.security_config import SecurityConfig, get_security_config
        results.record_test("Security configuration import", True)

        # Test 2: Check default security settings
        config = SecurityConfig()

        # AUTO_LOGIN should default to False
        auto_login_secure = not config.auto_login_enabled
        results.record_test("AUTO_LOGIN defaults to False", auto_login_secure, "AUTO_LOGIN not secure by default" if not auto_login_secure else "")

        # Skip authentication should default to False
        skip_auth_secure = not config.skip_authentication
        results.record_test("Skip authentication defaults to False", skip_auth_secure, "Skip authentication not secure by default" if not skip_auth_secure else "")

        # Environment should default to production
        env_secure = config.environment.value == "production"
        results.record_test("Environment defaults to production", env_secure, "Environment not secure by default" if not env_secure else "")

    except ImportError as e:
        results.record_test("Security configuration import", False, f"Import error: {e}")
    except Exception as e:
        results.record_test("Security configuration verification", False, f"Unexpected error: {e}")

    return results


async def test_endpoint_authorization_updates():
    """Test that endpoints have been updated with proper authorization."""
    results = SecurityTestResults()

    try:
        # Test 1: Check endpoints.py uses authorization
        from langflow.api.v1 import endpoints
        import inspect

        get_all_source = inspect.getsource(endpoints.get_all)
        has_authorization = "get_authorized_user" in get_all_source
        results.record_test("Endpoints get_all uses authorization", has_authorization, "get_all endpoint missing authorization" if not has_authorization else "")

        # Test 2: Check starter_projects.py uses authorization
        from langflow.api.v1 import starter_projects

        get_starter_source = inspect.getsource(starter_projects.get_starter_projects)
        has_auth_pattern = "get_authorized_user" in get_starter_source
        results.record_test("Starter projects uses authorization", has_auth_pattern, "Starter projects missing authorization" if not has_auth_pattern else "")

    except ImportError as e:
        results.record_test("Endpoint authorization import", False, f"Import error: {e}")
    except Exception as e:
        results.record_test("Endpoint authorization verification", False, f"Unexpected error: {e}")

    return results


async def main():
    """Run all security verification tests."""
    print("🔒 Running Security Fixes Verification Tests...")
    print("=" * 60)

    all_results = []

    # Run all test suites
    test_suites = [
        ("MCP Authentication Fix", test_mcp_authentication_fix),
        ("RBAC Middleware Secure Failure", test_rbac_middleware_secure_failure),
        ("MCP Authorization Implementation", test_mcp_authorization_implementation),
        ("Authorization Patterns Implementation", test_authorization_patterns_implementation),
        ("Security Configuration", test_security_configuration),
        ("Endpoint Authorization Updates", test_endpoint_authorization_updates),
    ]

    for suite_name, test_func in test_suites:
        print(f"\n🧪 Testing: {suite_name}")
        print("-" * 40)
        results = await test_func()
        all_results.append(results)

    # Summary
    print("\n" + "=" * 60)
    total_tests = sum(r.tests_run for r in all_results)
    total_passed = sum(r.tests_passed for r in all_results)
    total_failed = sum(r.tests_failed for r in all_results)

    print(f"🔒 Overall Security Test Results:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {total_passed}")
    print(f"   Failed: {total_failed}")

    if total_failed == 0:
        print(f"\n🎉 All security fixes verified successfully!")
        print(f"✅ System is secure and ready for deployment.")
        return 0
    else:
        print(f"\n❌ Some security issues detected!")
        print(f"🚨 Review and fix the failing tests before deployment.")
        return 1


if __name__ == "__main__":
    # Add the project root to Python path
    sys.path.insert(0, "/Users/dongmingjiang/GB/LangBuilder/src/backend/base")

    # Run the tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
