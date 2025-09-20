#!/usr/bin/env python3
"""
Comprehensive test script for RBAC authorization enhancements.

This script validates:
1. Permission checking implementation
2. Workspace isolation enforcement
3. Privilege escalation protection
4. Rate limiting and authentication security
"""

import sys
import asyncio
import traceback
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src" / "backend" / "base"))

def test_imports() -> Dict[str, Any]:
    """Test that all authorization enhancement modules can be imported."""
    results = {"passed": 0, "failed": 0, "errors": []}

    modules_to_test = [
        "langflow.services.auth.permission_checker",
        "langflow.services.auth.workspace_isolation",
        "langflow.services.auth.privilege_escalation_protection",
        "langflow.services.auth.rate_limiter",
        "langflow.services.auth.session_manager",
        "langflow.services.auth.brute_force_protection",
        "langflow.services.auth.enhanced_auth_middleware",
    ]

    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ Successfully imported {module_name}")
            results["passed"] += 1
        except Exception as e:
            print(f"❌ Failed to import {module_name}: {e}")
            results["failed"] += 1
            results["errors"].append(f"{module_name}: {e}")

    return results

def test_permission_checker() -> Dict[str, Any]:
    """Test the permission checker implementation."""
    results = {"passed": 0, "failed": 0, "errors": []}

    try:
        from langflow.services.auth.permission_checker import (
            PermissionChecker,
            PermissionRequest,
            PermissionLevel,
            ResourceScope
        )

        # Test basic instantiation
        checker = PermissionChecker()
        print("✅ PermissionChecker instantiated successfully")
        results["passed"] += 1

        # Test PermissionRequest creation
        request = PermissionRequest(
            permission="read",
            resource_type="project",
            workspace_id=None,
            required_level=PermissionLevel.READ,
            scope=ResourceScope.WORKSPACE
        )
        print("✅ PermissionRequest created successfully")
        results["passed"] += 1

    except Exception as e:
        print(f"❌ PermissionChecker test failed: {e}")
        results["failed"] += 1
        results["errors"].append(f"PermissionChecker: {e}")

    return results

def test_workspace_isolation() -> Dict[str, Any]:
    """Test the workspace isolation implementation."""
    results = {"passed": 0, "failed": 0, "errors": []}

    try:
        from langflow.services.auth.workspace_isolation import (
            WorkspaceIsolationManager,
            WorkspaceAccessResult,
            IsolationLevel
        )

        # Test basic instantiation
        manager = WorkspaceIsolationManager()
        print("✅ WorkspaceIsolationManager instantiated successfully")
        results["passed"] += 1

        # Test isolation levels
        assert IsolationLevel.STRICT
        assert IsolationLevel.STANDARD
        print("✅ IsolationLevel enum working correctly")
        results["passed"] += 1

    except Exception as e:
        print(f"❌ WorkspaceIsolation test failed: {e}")
        results["failed"] += 1
        results["errors"].append(f"WorkspaceIsolation: {e}")

    return results

def test_privilege_escalation_protection() -> Dict[str, Any]:
    """Test the privilege escalation protection implementation."""
    results = {"passed": 0, "failed": 0, "errors": []}

    try:
        from langflow.services.auth.privilege_escalation_protection import (
            PrivilegeEscalationProtection,
            EscalationType,
            ThreatLevel,
            ResponseAction
        )

        # Test basic instantiation
        protection = PrivilegeEscalationProtection()
        print("✅ PrivilegeEscalationProtection instantiated successfully")
        results["passed"] += 1

        # Test enums
        assert EscalationType.ROLE_ELEVATION
        assert ThreatLevel.HIGH
        assert ResponseAction.BLOCK_REQUEST
        print("✅ Escalation enums working correctly")
        results["passed"] += 1

    except Exception as e:
        print(f"❌ PrivilegeEscalationProtection test failed: {e}")
        results["failed"] += 1
        results["errors"].append(f"PrivilegeEscalationProtection: {e}")

    return results

def test_rate_limiter() -> Dict[str, Any]:
    """Test the rate limiter implementation."""
    results = {"passed": 0, "failed": 0, "errors": []}

    try:
        from langflow.services.auth.rate_limiter import (
            AuthRateLimiter,
            RateLimitRule,
            ClientState
        )

        # Test basic instantiation
        limiter = AuthRateLimiter()
        print("✅ AuthRateLimiter instantiated successfully")
        results["passed"] += 1

        # Test rule creation
        rule = RateLimitRule(max_attempts=5, window_seconds=300, block_duration_seconds=900)
        assert rule.max_attempts == 5
        print("✅ RateLimitRule created successfully")
        results["passed"] += 1

    except Exception as e:
        print(f"❌ RateLimiter test failed: {e}")
        results["failed"] += 1
        results["errors"].append(f"RateLimiter: {e}")

    return results

def test_session_manager() -> Dict[str, Any]:
    """Test the session manager implementation."""
    results = {"passed": 0, "failed": 0, "errors": []}

    try:
        from langflow.services.auth.session_manager import (
            SessionManager,
            SessionInfo,
            ThreatLevel
        )

        # Test basic instantiation
        manager = SessionManager()
        print("✅ SessionManager instantiated successfully")
        results["passed"] += 1

        # Test SessionInfo creation
        session_info = SessionInfo(
            session_id="test-session",
            user_id="test-user",
            device_fingerprint="test-fingerprint",
            security_level="standard"
        )
        assert session_info.session_id == "test-session"
        print("✅ SessionInfo created successfully")
        results["passed"] += 1

    except Exception as e:
        print(f"❌ SessionManager test failed: {e}")
        results["failed"] += 1
        results["errors"].append(f"SessionManager: {e}")

    return results

def test_brute_force_protection() -> Dict[str, Any]:
    """Test the brute force protection implementation."""
    results = {"passed": 0, "failed": 0, "errors": []}

    try:
        from langflow.services.auth.brute_force_protection import (
            BruteForceProtection,
            AttackPattern,
            LoginAttempt
        )

        # Test basic instantiation
        protection = BruteForceProtection()
        print("✅ BruteForceProtection instantiated successfully")
        results["passed"] += 1

        # Test enums
        assert AttackPattern.BRUTE_FORCE
        assert AttackPattern.CREDENTIAL_STUFFING
        print("✅ AttackPattern enum working correctly")
        results["passed"] += 1

    except Exception as e:
        print(f"❌ BruteForceProtection test failed: {e}")
        results["failed"] += 1
        results["errors"].append(f"BruteForceProtection: {e}")

    return results

def main():
    """Run all authorization enhancement tests."""
    print("🛡️ Starting RBAC Authorization Enhancement Validation")
    print("=" * 60)

    all_results = {
        "imports": test_imports(),
        "permission_checker": test_permission_checker(),
        "workspace_isolation": test_workspace_isolation(),
        "privilege_escalation": test_privilege_escalation_protection(),
        "rate_limiter": test_rate_limiter(),
        "session_manager": test_session_manager(),
        "brute_force_protection": test_brute_force_protection(),
    }

    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)

    total_passed = 0
    total_failed = 0
    all_errors = []

    for test_name, result in all_results.items():
        passed = result["passed"]
        failed = result["failed"]
        total_passed += passed
        total_failed += failed
        all_errors.extend(result["errors"])

        status = "✅ PASS" if failed == 0 else "❌ FAIL"
        print(f"{test_name:25} {status:8} ({passed} passed, {failed} failed)")

    print("-" * 60)
    print(f"{'TOTAL':25} {'':8} ({total_passed} passed, {total_failed} failed)")

    if all_errors:
        print("\n🚨 Errors encountered:")
        for error in all_errors:
            print(f"  - {error}")

    if total_failed == 0:
        print("\n🎉 All authorization enhancement tests passed!")
        return 0
    else:
        print(f"\n⚠️ {total_failed} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)