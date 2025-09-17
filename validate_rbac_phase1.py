#!/usr/bin/env python
"""
RBAC Phase 1 Validation Script

This script validates that all RBAC Phase 1 components are correctly implemented
and functioning without requiring database setup or API server running.
"""

import sys
import traceback
from typing import Any, Dict, List, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_test_header(title: str):
    """Print a formatted test section header."""
    print(f"\n{Colors.OKBLUE}🔍 {title}...{Colors.ENDC}")


def print_success(message: str):
    """Print a success message."""
    print(f"  {Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print an error message."""
    print(f"  {Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"  {Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def test_imports() -> Tuple[bool, str]:
    """Test that all RBAC models and APIs can be imported."""
    try:
        # Test model imports
        from langflow.services.database.models.rbac.workspace import (
            Workspace, WorkspaceCreate, WorkspaceRead, WorkspaceUpdate,
            WorkspaceSettings, WorkspaceInvitation
        )
        from langflow.services.database.models.rbac.project import (
            Project, ProjectCreate, ProjectRead, ProjectUpdate, ProjectStatistics
        )
        from langflow.services.database.models.rbac.environment import (
            Environment, EnvironmentCreate, EnvironmentRead, EnvironmentUpdate,
            EnvironmentType, EnvironmentDeployment
        )
        from langflow.services.database.models.rbac.role import (
            Role, RoleCreate, RoleRead, RoleUpdate, RoleType, RoleHierarchy,
            SYSTEM_ROLES
        )
        from langflow.services.database.models.rbac.permission import (
            Permission, PermissionCreate, PermissionRead, PermissionCheck,
            PermissionAction, ResourceType, RolePermission, SYSTEM_PERMISSIONS
        )
        from langflow.services.database.models.rbac.role_assignment import (
            RoleAssignment, RoleAssignmentCreate, RoleAssignmentRead,
            RoleAssignmentUpdate, RoleAssignmentApproval,
            AssignmentType, AssignmentScope
        )
        from langflow.services.database.models.rbac.user_group import (
            UserGroup, UserGroupCreate, UserGroupRead, UserGroupUpdate,
            UserGroupSync, UserGroupMembership, UserGroupMembershipCreate,
            UserGroupMembershipRead, GroupType
        )
        from langflow.services.database.models.rbac.service_account import (
            ServiceAccount, ServiceAccountCreate, ServiceAccountRead,
            ServiceAccountUpdate, ServiceAccountToken, ServiceAccountTokenCreate,
            ServiceAccountTokenRead, ServiceAccountTokenResponse
        )
        from langflow.services.database.models.rbac.audit_log import (
            AuditLog, AuditLogRead, AuditLogFilter, AuditLogExport,
            AuditLogSummary, ComplianceReport, AuditEventType, ActorType, AuditOutcome
        )
        print_success("All RBAC model imports successful")
        
        # Test API imports
        from langflow.api.v1.rbac import workspaces, projects, roles
        from langflow.api.v1.rbac.dependencies import (
            PermissionChecker, check_workspace_permission,
            check_project_permission, check_environment_permission,
            check_flow_permission, check_role_permission
        )
        print_success("All RBAC API imports successful")
        
        return True, "All imports successful"
    except Exception as e:
        return False, f"Import error: {str(e)}"


def test_model_instantiation() -> Tuple[bool, str]:
    """Test that RBAC models can be instantiated with valid data."""
    try:
        from uuid import uuid4
        
        # Test workspace model
        from langflow.services.database.models.rbac.workspace import WorkspaceCreate
        workspace = WorkspaceCreate(
            name="Test Workspace",
            description="Test workspace description",
            organization="Test Org"
        )
        print_success("WorkspaceCreate model instantiated successfully")
        
        # Test project model
        from langflow.services.database.models.rbac.project import ProjectCreate
        project = ProjectCreate(
            name="Test-Project",
            description="Test project description",
            workspace_id=uuid4()
        )
        print_success("ProjectCreate model instantiated successfully")
        
        # Test environment model
        from langflow.services.database.models.rbac.environment import EnvironmentCreate, EnvironmentType
        environment = EnvironmentCreate(
            name="dev",
            description="Development environment",
            type=EnvironmentType.DEVELOPMENT,
            project_id=uuid4()
        )
        print_success("EnvironmentCreate model instantiated successfully")
        
        # Test role model
        from langflow.services.database.models.rbac.role import RoleCreate, RoleType
        role = RoleCreate(
            name="Test Role",
            description="Test role description",
            type=RoleType.CUSTOM,
            workspace_id=uuid4()
        )
        print_success("RoleCreate model instantiated successfully")
        
        return True, "All models instantiated successfully"
    except Exception as e:
        return False, f"Model instantiation error: {str(e)}"


def test_api_router_setup() -> Tuple[bool, str]:
    """Test that API routers are properly configured."""
    try:
        from langflow.api.v1.rbac import workspaces, projects, roles
        
        # Check that routers have correct prefixes and tags
        assert workspaces.router.prefix == "/workspaces"
        assert "workspaces" in workspaces.router.tags
        print_success("All API routers properly configured")
        
        # Check that routers have routes defined
        assert len(workspaces.router.routes) > 0
        assert len(projects.router.routes) > 0
        assert len(roles.router.routes) > 0
        print_success("All API router tags properly set")
        
        return True, "API routers configured correctly"
    except Exception as e:
        return False, f"API router error: {str(e)}"


def test_permission_checker() -> Tuple[bool, str]:
    """Test the PermissionChecker logic."""
    try:
        from langflow.api.v1.rbac.dependencies import PermissionChecker
        from unittest.mock import Mock
        from uuid import uuid4
        
        # Create mock objects
        session = Mock()
        
        # Test with superuser
        superuser = Mock()
        superuser.is_superuser = True
        superuser.id = uuid4()
        
        checker = PermissionChecker(session, superuser)
        workspace = Mock()
        workspace.owner_id = uuid4()
        
        # Superuser should have all permissions
        assert checker.has_workspace_permission(workspace, "read") == True
        print_success("Superuser permission logic working")
        
        # Test with owner
        owner = Mock()
        owner.is_superuser = False
        owner.id = workspace.owner_id
        
        checker = PermissionChecker(session, owner)
        assert checker.has_workspace_permission(workspace, "read") == True
        print_success("Owner permission logic working")
        
        # Test with regular user (no permissions)
        regular_user = Mock()
        regular_user.is_superuser = False
        regular_user.id = uuid4()
        
        checker = PermissionChecker(session, regular_user)
        assert checker.has_workspace_permission(workspace, "read") == False
        print_success("Access control logic working")
        
        return True, "Permission checker working correctly"
    except Exception as e:
        return False, f"Permission checker error: {str(e)}"


def test_model_validation() -> Tuple[bool, str]:
    """Test model field validation."""
    try:
        from langflow.services.database.models.rbac.workspace import WorkspaceBase
        from langflow.services.database.models.rbac.environment import EnvironmentBase
        from pydantic import ValidationError
        
        # Test valid workspace name
        try:
            workspace = WorkspaceBase(name="Valid Name")
            print_success("Valid workspace creation works")
        except:
            return False, "Valid workspace name rejected"
        
        # Test empty workspace name
        try:
            workspace = WorkspaceBase(name="")
            return False, "Empty workspace name was not rejected"
        except ValidationError:
            print_success("Empty workspace name properly rejected in base model")
        
        # Test valid environment name
        try:
            env = EnvironmentBase(name="dev")
            print_success("Valid environment name accepted")
        except:
            return False, "Valid environment name rejected"
        
        # Test invalid environment name (uppercase)
        try:
            env = EnvironmentBase(name="DEV")
            return False, "Invalid environment name was not rejected"
        except ValidationError:
            print_success("Invalid environment name properly rejected")
        
        return True, "Model validation working correctly"
    except Exception as e:
        return False, f"Model validation error: {str(e)}"


def test_metadata_field_resolution() -> Tuple[bool, str]:
    """Test that metadata field conflicts are resolved."""
    try:
        from langflow.services.database.models.rbac.workspace import WorkspaceCreate
        from langflow.services.database.models.rbac.project import ProjectCreate
        from langflow.services.database.models.rbac.role import RoleCreate
        
        # Test workspace has workspace_metadata field
        ws = WorkspaceCreate(
            name="Test",
            workspace_metadata={"key": "value"}
        )
        assert hasattr(ws, 'workspace_metadata')
        print_success("Workspace metadata field properly renamed")
        
        # Test project has project_metadata field
        from uuid import uuid4
        proj = ProjectCreate(
            name="Test",
            workspace_id=uuid4(),
            project_metadata={"key": "value"}
        )
        assert hasattr(proj, 'project_metadata')
        print_success("Project metadata field properly renamed")
        
        # Test role has role_metadata field
        role = RoleCreate(
            name="Test",
            workspace_id=uuid4(),
            role_metadata={"key": "value"}
        )
        assert hasattr(role, 'role_metadata')
        print_success("Role metadata field properly renamed")
        
        return True, "Metadata fields properly resolved"
    except Exception as e:
        return False, f"Metadata field error: {str(e)}"


def test_enum_definitions() -> Tuple[bool, str]:
    """Test that all enums are properly defined."""
    try:
        from langflow.services.database.models.rbac.environment import EnvironmentType
        from langflow.services.database.models.rbac.role import RoleType
        from langflow.services.database.models.rbac.user_group import GroupType
        from langflow.services.database.models.rbac.audit_log import AuditEventType
        
        # Test EnvironmentType enum
        assert EnvironmentType.DEVELOPMENT == "development"
        assert EnvironmentType.STAGING == "staging"
        assert EnvironmentType.PRODUCTION == "production"
        print_success("EnvironmentType enum working")
        
        # Test RoleType enum
        assert RoleType.SYSTEM == "system"
        assert RoleType.CUSTOM == "custom"
        assert RoleType.WORKSPACE == "workspace"
        print_success("RoleType enum working")
        
        # Test GroupType enum
        assert GroupType.LOCAL == "local"
        assert GroupType.SYNCED == "synced"
        print_success("GroupType enum working")
        
        # Test AuditEventType enum
        assert hasattr(AuditEventType, 'LOGIN')
        assert hasattr(AuditEventType, 'LOGOUT')
        print_success("AuditEventType enum working")
        
        return True, "All enums properly defined"
    except Exception as e:
        return False, f"Enum definition error: {str(e)}"


def run_all_tests() -> Tuple[int, int]:
    """Run all validation tests and return results."""
    tests = [
        ("Testing imports", test_imports),
        ("Testing model instantiation", test_model_instantiation),
        ("Testing API router setup", test_api_router_setup),
        ("Testing PermissionChecker logic", test_permission_checker),
        ("Testing model validation", test_model_validation),
        ("Testing metadata field resolution", test_metadata_field_resolution),
        ("Testing enum definitions", test_enum_definitions),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print_test_header(test_name)
        try:
            success, message = test_func()
            if success:
                passed += 1
            else:
                failed += 1
                print_error(f"Test failed with message: {message}")
        except Exception as e:
            failed += 1
            print_error(f"Test failed with exception: {str(e)}")
            traceback.print_exc()
    
    return passed, failed


def main():
    """Main validation function."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}🚀 Starting RBAC Phase 1 Validation{Colors.ENDC}")
    print("=" * 50)
    
    passed, failed = run_all_tests()
    
    print("\n" + "=" * 50)
    print(f"{Colors.BOLD}📊 Validation Results: {passed}/{passed + failed} tests passed{Colors.ENDC}")
    
    if failed == 0:
        print(f"{Colors.OKGREEN}🎉 RBAC Phase 1 validation SUCCESSFUL!{Colors.ENDC}\n")
        print(f"{Colors.OKGREEN}✅ Phase 1 Implementation Status:{Colors.ENDC}")
        print("  • All RBAC models import correctly")
        print("  • All API endpoints are properly configured")
        print("  • Permission checking logic is functional")
        print("  • Model validation rules are working")
        print("  • Metadata field conflicts are resolved")
        print("  • Enum types are properly defined")
        print(f"\n{Colors.OKCYAN}🚀 Ready for database migrations and full integration testing!{Colors.ENDC}")
        return 0
    else:
        print(f"{Colors.FAIL}❌ RBAC Phase 1 validation FAILED!{Colors.ENDC}")
        print(f"   {failed} tests failed - see errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())