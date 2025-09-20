# RBAC Phase 1 Validation Strategy

This document outlines a comprehensive testing and validation strategy for the RBAC Phase 1 implementation in LangBuilder.

## Overview

RBAC Phase 1 includes:
- ✅ Core data models (Workspace, Project, Environment, Role, Permission, etc.)
- ✅ API endpoints for workspace and role management
- ✅ Basic permission checking infrastructure
- ✅ Database migrations and schema setup

## Testing Levels

### 1. Unit Tests (Most Important)

#### Core Model Tests
- **Database Models**: Test all RBAC model validations, relationships, and constraints
- **Business Logic**: Test permission checking logic, role hierarchy, user assignments
- **Data Integrity**: Test unique constraints, foreign keys, cascading deletes

#### API Endpoint Tests
- **Authentication**: Test endpoint security and user authentication
- **Authorization**: Test permission-based access control
- **CRUD Operations**: Test create, read, update, delete for all resources
- **Error Handling**: Test proper error responses and status codes

#### Service Layer Tests
- **Permission Checker**: Test the core PermissionChecker class logic
- **Role Assignment**: Test role assignment and revocation logic
- **Workspace Management**: Test workspace creation, deletion, user management

### 2. Integration Tests

#### API Integration
- **End-to-End API Flows**: Test complete user workflows
- **Cross-Service Communication**: Test interaction between RBAC and existing systems
- **Database Transactions**: Test data consistency across operations

#### Authentication Integration
- **User Session Management**: Test user authentication with RBAC
- **API Key Integration**: Test service account API key authentication
- **Permission Inheritance**: Test workspace → project → environment permission flow

### 3. Manual Testing

#### User Interface Testing
- **Frontend Integration**: Test UI components for workspace/role management
- **User Experience**: Test realistic user workflows and edge cases
- **Error Messages**: Test user-friendly error handling

#### Security Testing
- **Access Control**: Manually verify permission boundaries
- **Privilege Escalation**: Test that users cannot exceed granted permissions
- **Data Isolation**: Test that users only see data they have access to

## Validation Categories

### A. Functional Validation

#### 1. Data Model Validation
```bash
# Test database models and relationships
pytest src/backend/tests/unit/database/ -v
pytest src/backend/tests/unit/services/database/ -v
```

#### 2. API Endpoint Validation
```bash
# Test RBAC API endpoints
pytest src/backend/tests/unit/api/v1/rbac/ -v
pytest src/backend/tests/integration/ -k rbac -v
```

#### 3. Permission Logic Validation
```bash
# Test permission checking and authorization
pytest src/backend/tests/unit/services/ -k permission -v
pytest src/backend/tests/unit/services/ -k rbac -v
```

### B. Security Validation

#### 1. Access Control Testing
- **Workspace Isolation**: Users can only access their own workspaces
- **Project Boundaries**: Users respect project-level permissions
- **Role Enforcement**: Users cannot perform actions beyond their role
- **API Security**: All endpoints require proper authentication

#### 2. Data Protection Testing
- **SQL Injection**: Test that ORM prevents SQL injection
- **Mass Assignment**: Test that sensitive fields cannot be mass-assigned
- **Information Disclosure**: Test that error messages don't leak sensitive data

### C. Performance Validation

#### 1. Database Performance
- **Query Efficiency**: Test that permission checks don't cause N+1 queries
- **Index Usage**: Verify proper database indexing for RBAC queries
- **Bulk Operations**: Test performance with large numbers of users/roles

#### 2. API Performance
- **Response Times**: Test that RBAC endpoints respond quickly
- **Concurrent Access**: Test system behavior under concurrent user load

## Testing Commands

### Run All RBAC Tests
```bash
# Run all RBAC-related tests
pytest src/backend/tests/ -k rbac -v

# Run with coverage
pytest src/backend/tests/ -k rbac --cov=src/backend/base/langflow/api/v1/rbac --cov=src/backend/base/langflow/services/database/models/rbac
```

### Run Specific Test Categories
```bash
# Model tests
pytest src/backend/tests/unit/database/ -v

# API tests
pytest src/backend/tests/unit/api/v1/rbac/ -v

# Service tests
pytest src/backend/tests/unit/services/ -k rbac -v

# Integration tests
pytest src/backend/tests/integration/ -k rbac -v
```

### Run Tests with Different Options
```bash
# Quick test run (exclude slow tests)
pytest src/backend/tests/unit/api/v1/rbac/ -v -m "not slow"

# Run with debugging
pytest src/backend/tests/unit/api/v1/rbac/ -v -s --tb=short

# Parallel execution
pytest src/backend/tests/ -k rbac -n auto
```

## Manual Testing Scenarios

### Scenario 1: Workspace Management
1. **Create Workspace**: User creates a new workspace
2. **Invite Users**: Owner invites users to workspace with different roles
3. **Manage Projects**: Users create projects within workspace boundaries
4. **Permission Testing**: Verify users can only access appropriate resources

### Scenario 2: Role-Based Access
1. **Role Assignment**: Assign different roles to users
2. **Permission Boundaries**: Test that users respect role limitations
3. **Role Modification**: Update user roles and verify access changes
4. **Role Removal**: Remove roles and verify access revocation

### Scenario 3: Multi-Tenant Isolation
1. **Multiple Workspaces**: Create multiple workspaces with different users
2. **Data Isolation**: Verify users cannot access other workspace data
3. **Cross-Workspace**: Test that operations respect workspace boundaries

## Database Validation

### Schema Validation
```bash
# Check database migrations
uv run alembic check

# Run migrations in test environment
uv run alembic upgrade head

# Verify table creation
python -c "from langflow.services.database.models.rbac import *; print('Models imported successfully')"
```

### Data Integrity Tests
```python
# Test in Python shell
from langflow.services.database.models.rbac import *
from sqlmodel import Session, create_engine

# Create test data and verify constraints
engine = create_engine("sqlite:///test.db")
with Session(engine) as session:
    # Test workspace creation
    workspace = Workspace(name="test", owner_id="user123")
    session.add(workspace)
    session.commit()

    # Test project creation
    project = Project(name="test", workspace_id=workspace.id, owner_id="user123")
    session.add(project)
    session.commit()
```

## Security Validation Checklist

### Authentication Security
- [ ] All RBAC endpoints require authentication
- [ ] Invalid tokens are properly rejected
- [ ] Session management works correctly
- [ ] API keys have proper scope restrictions

### Authorization Security
- [ ] Users cannot access resources outside their workspace
- [ ] Users cannot perform actions beyond their role
- [ ] System roles cannot be modified by non-superusers
- [ ] Permission checks are enforced at all levels

### Data Security
- [ ] Sensitive data is not logged or exposed in errors
- [ ] Database queries use parameterization
- [ ] User input is properly validated
- [ ] Audit logs capture security-relevant events

## Performance Validation

### Database Performance Tests
```python
# Test permission query performance
import time
from langflow.api.v1.rbac.dependencies import PermissionChecker

start = time.time()
# Simulate 1000 permission checks
for i in range(1000):
    checker.has_workspace_permission(workspace, "read")
end = time.time()

print(f"1000 permission checks took {end - start:.2f} seconds")
```

### Load Testing
```bash
# Use locust for load testing (if available)
locust -f src/backend/tests/locust/rbac_load_test.py --host=http://localhost:7860
```

## Validation Success Criteria

### Phase 1 is considered successfully implemented if:

1. **All Tests Pass**: All unit, integration, and manual tests pass
2. **Security Requirements Met**: All security validation items checked
3. **Performance Acceptable**: Permission checks < 10ms, API responses < 200ms
4. **Database Integrity**: All constraints enforced, migrations work correctly
5. **API Functionality**: All RBAC endpoints work as documented
6. **User Experience**: Manual testing scenarios complete successfully

## Next Steps After Validation

1. **Performance Optimization**: Address any performance bottlenecks found
2. **Security Hardening**: Address any security issues discovered
3. **Documentation Updates**: Update API documentation based on testing
4. **Integration Planning**: Plan integration with frontend and existing features
5. **Phase 2 Planning**: Begin planning for advanced RBAC features

## Testing Infrastructure Requirements

### Required Tools
- pytest (unit testing)
- httpx (API testing)
- SQLModel/SQLAlchemy (database testing)
- faker (test data generation)
- respx (HTTP mocking)

### Test Environment Setup
```bash
# Set up test environment
export LANGFLOW_DATABASE_URL="sqlite:///test.db"
export LANGFLOW_SECRET_KEY="test-secret-key"
export LANGFLOW_SUPERUSER_PASSWORD="test-password"

# Run database migrations
uv run alembic upgrade head

# Run test suite
pytest src/backend/tests/ -k rbac -v
```

This comprehensive validation strategy ensures that RBAC Phase 1 is thoroughly tested and ready for production use.