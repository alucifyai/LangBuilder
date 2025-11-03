# Task 1.4: RBACService Core Logic Implementation

## Task Information
- **Phase**: Phase 1 - RBAC Data Model and Backend Services
- **Task ID**: Task 1.4
- **Task Name**: Implement RBACService with can_access() Method
- **Implementation Date**: 2025-11-01
- **Status**: COMPLETED

## Scope and Goals
Create the RBACService following the existing service pattern with factory instantiation. Implement the core `can_access()` authorization method that evaluates user permissions with support for Admin bypass, direct scope assignments, and project-to-flow inheritance per PRD Epic 2 Story 2.1.

## Impact Subgraph (from Implementation Plan)
- **New Nodes**:
  - nl0504: RBACService (logic node)
- **Modified Nodes**: None
- **Edges**:
  - e14005: nl0504 (RBACService) → ns0010 (Role) [dependency]
  - e14006: nl0504 (RBACService) → ns0011 (Permission) [dependency]
  - e14007: nl0504 (RBACService) → ns0013 (UserRoleAssignment) [dependency]

## Implementation Summary

### Files Created
1. `/Users/Arnab/Documents/GitHub/Alucify_LangBuilder/LangBuilder/src/backend/base/langbuilder/services/rbac/service.py` - RBACService implementation with core permission evaluation logic
2. `/Users/Arnab/Documents/GitHub/Alucify_LangBuilder/LangBuilder/src/backend/base/langbuilder/services/rbac/factory.py` - RBACServiceFactory following singleton pattern
3. `/Users/Arnab/Documents/GitHub/Alucify_LangBuilder/LangBuilder/src/backend/base/langbuilder/services/rbac/__init__.py` - Module initialization file

### Files Modified
1. `/Users/Arnab/Documents/GitHub/Alucify_LangBuilder/LangBuilder/src/backend/base/langbuilder/services/schema.py` - Added RBAC_SERVICE to ServiceType enum
2. `/Users/Arnab/Documents/GitHub/Alucify_LangBuilder/LangBuilder/src/backend/base/langbuilder/services/deps.py` - Added get_rbac_service() dependency injection function and type import

### Test Files Created
1. `/Users/Arnab/Documents/GitHub/Alucify_LangBuilder/LangBuilder/src/backend/tests/unit/test_rbac_service.py` - Comprehensive unit tests (16 test cases, all passing)

## Implementation Details

### RBACService Core Methods

#### 1. can_access()
The primary permission evaluation method implementing the 4-step logic from PRD Story 2.1:

**Signature:**
```python
async def can_access(
    self,
    session: AsyncSession,
    user_id: UUID,
    permission: PermissionEnum,
    scope_type: ScopeTypeEnum,
    scope_id: UUID | None = None,
) -> bool
```

**Logic Flow:**
1. **Step 1 - Admin Bypass**: Check if user has Admin role (global scope) - returns `True` immediately
2. **Step 2 - Direct Permission Check**: Check if user has direct role assignment for the scope with the requested permission
3. **Step 3 - Inheritance**: For FLOW scope without direct assignment, check parent PROJECT permission
4. **Step 4 - Deny Access**: Return `False` if no permission found

**Error Handling:**
- Fail closed: Returns `False` on any exception
- All exceptions are logged for debugging

#### 2. get_accessible_scope_ids()
Batch permission filtering method for efficient list endpoint queries.

**Signature:**
```python
async def get_accessible_scope_ids(
    self,
    session: AsyncSession,
    user_id: UUID,
    permission: PermissionEnum,
    scope_type: ScopeTypeEnum,
) -> list[UUID]
```

**Features:**
- Admin users get all scope IDs
- Regular users get IDs from direct assignments
- FLOW scope includes flows inherited from PROJECT permissions
- Returns empty list on error (fail closed)

#### 3. get_user_roles()
Query method for retrieving user role assignments with optional filtering.

**Signature:**
```python
async def get_user_roles(
    self,
    session: AsyncSession,
    user_id: UUID,
    scope_type: ScopeTypeEnum | None = None,
    scope_id: UUID | None = None,
) -> list[UserRoleAssignment]
```

**Features:**
- Retrieve all assignments for a user
- Optional filtering by scope_type
- Optional filtering by specific scope_id
- Returns empty list on error

### Helper Methods

#### _is_admin()
Checks if user has Admin role with global scope.

#### _check_direct_permission()
Checks if user has permission via direct role assignment. Returns:
- `True` if has permission
- `False` if has assignment but lacks permission
- `None` if no assignment exists

#### _get_parent_project_id()
Retrieves the parent project ID for a given flow.

## Architecture & Tech Stack

### Framework
- **Service Pattern**: Follows existing LangBuilder service factory pattern
- **Async/Await**: All methods use async/await for database operations
- **Dependency Injection**: Registered with ServiceManager and accessible via get_rbac_service()

### Dependencies
- SQLModel for database queries
- AsyncSession for async database operations
- Loguru for logging
- RBAC models from Task 1.1 (Role, Permission, RolePermission, UserRoleAssignment)
- Flow and Folder models for parent relationship queries

### Service Registration
The RBACService is registered with the ServiceManager using the factory pattern:
- Singleton factory instance
- Automatic discovery via ServiceType enum
- Available as dependency injection via `get_rbac_service()`

## Test Coverage Summary

### Test Classes
1. **TestRBACServiceCanAccess** - 7 tests covering permission evaluation logic
2. **TestRBACServiceGetAccessibleScopeIds** - 4 tests covering batch permission filtering
3. **TestRBACServiceGetUserRoles** - 3 tests covering role query functionality
4. **TestRBACServiceEdgeCases** - 3 tests covering error handling and edge cases

### Test Results
```
16 passed in 0.29s
```

### Key Test Scenarios Covered
- Admin bypass grants access to all resources
- Direct project permission grants access
- Flow inherits permissions from parent project
- Direct flow permission overrides project inheritance
- Users without permissions are denied access
- Role without specific permission denies that action
- Admin gets all scope IDs for batch filtering
- Non-admin users get only assigned scope IDs
- Flow scope IDs include inherited from project permissions
- Users with no permissions get empty list
- Retrieve all user roles
- Filter user roles by scope type
- Filter user roles by specific scope ID
- Nonexistent user has no access
- Flows without parent project don't inherit permissions
- Nonexistent user returns empty role list

### Test Notes
- Tests use seeded RBAC data from Task 1.3 (roles and permissions)
- Helper function `get_seeded_role()` retrieves pre-seeded roles
- All tests use unique usernames to avoid conflicts
- Tests cover all 4 steps of the permission evaluation logic

## Success Criteria Validation

### Checklist from Implementation Plan

- [X] RBACService follows existing service factory pattern
  - Factory class created with singleton pattern
  - Service registered in ServiceType enum
  - Dependency injection function added to deps.py

- [X] can_access() method implemented with all logic per PRD Story 2.1
  - Step 1: Admin role bypass implemented
  - Step 2: Direct scope permission check implemented
  - Step 3: Flow-to-Project inheritance implemented
  - Step 4: No permission returns False

- [X] Admin role bypass works (returns True immediately)
  - Verified in test: `test_admin_bypass_grants_access`

- [X] Direct scope permission check works
  - Verified in tests: `test_direct_project_permission_grants_access`

- [X] Flow-to-Project inheritance works
  - Verified in test: `test_flow_inherits_from_project_permission`
  - Verified in test: `test_direct_flow_permission_overrides_project_inheritance`

- [X] get_accessible_scope_ids() method for list filtering
  - Implemented with Admin support and inheritance
  - Verified in 4 test cases

- [X] Service registered in service manager
  - Added to ServiceType enum as RBAC_SERVICE
  - Auto-discovered by ServiceManager.get_factories()

- [X] get_rbac_service() dependency injection function added
  - Added to deps.py
  - Returns RBACService instance via ServiceManager

- [X] All methods use async/await pattern
  - All methods are async
  - All database operations use await

- [X] Type hints for all parameters and return values
  - All methods have complete type hints
  - Uses UUID, PermissionEnum, ScopeTypeEnum, AsyncSession types

- [X] Docstrings explaining each method
  - Module-level docstring
  - Class docstring
  - Method docstrings with Args, Returns sections
  - Helper method docstrings

## Integration Validation

- [X] Integrates with existing code
  - Uses existing RBAC models from Task 1.1
  - Uses existing Flow and Folder models
  - Follows existing service patterns (SettingsService, DatabaseService, etc.)

- [X] Follows existing patterns
  - Service factory pattern matches SettingsServiceFactory
  - Dependency injection matches get_settings_service()
  - Async session usage matches existing CRUD operations

- [X] Uses correct tech stack
  - SQLModel for ORM queries
  - AsyncSession for database operations
  - Loguru for logging
  - FastAPI service pattern

- [X] Placed in correct locations
  - Service in `src/backend/base/langbuilder/services/rbac/service.py`
  - Factory in `src/backend/base/langbuilder/services/rbac/factory.py`
  - Tests in `src/backend/tests/unit/test_rbac_service.py`

## Performance Considerations

### can_access() Performance
- **Design**: Single database query per permission check
- **Admin Bypass**: Optimized with early return (Step 1)
- **Direct Check**: Single join query across RBAC tables
- **Inheritance**: Only triggered for FLOW scope without direct assignment
- **Expected Latency**: <50ms p95 (as per Risk Assessment in implementation plan)

### get_accessible_scope_ids() Performance
- **Design**: Minimizes database round trips
- **Admin Path**: Single query for all scope IDs
- **Regular Path**: Two queries (direct + inherited) with in-memory deduplication
- **Use Case**: Prevents N+1 queries in list endpoints

### Future Optimization Opportunities
- Add database indexes on UserRoleAssignment (user_id, scope_type, scope_id)
- Consider caching Admin status for frequently-checked users
- Batch permission checks for multiple scopes in single query

## Known Issues or Follow-ups

None. Task completed successfully with all success criteria met.

## Notes

### Permission Inheritance Behavior
- Flow permissions inherit from parent PROJECT unless overridden
- Direct FLOW role assignment takes precedence over inherited PROJECT role
- Flows without parent project (folder_id = NULL) do not inherit any permissions

### Admin Role Behavior
- Admin role is assigned with GLOBAL scope (scope_id = NULL)
- Admin users bypass all permission checks (always return True)
- Admin users see all resources in get_accessible_scope_ids()

### Error Handling Philosophy
- **Fail Closed**: All methods return restrictive results (False, empty list) on errors
- **Logging**: All exceptions are logged for debugging
- **No User-Facing Errors**: Methods never raise exceptions to callers

### Dependencies on Previous Tasks
- Task 1.1: RBAC database models and CRUD operations
- Task 1.2: Database tables created via Alembic migration
- Task 1.3: Seeded roles and permissions (Admin, Owner, Editor, Viewer)

## Next Steps

The following tasks depend on Task 1.4 completion:
- **Task 2.1**: Create RBAC Management API Endpoints (will use RBACService)
- **Task 2.2**: Integrate Permission Checks in Flow CRUD (will call can_access())
- **Task 2.3**: Integrate Permission Checks in Project CRUD (will call can_access())
- **Task 3.2**: Create usePermission React Hook (will call RBAC API endpoints)

## Validation Commands

Run the unit tests:
```bash
uv run pytest src/backend/tests/unit/test_rbac_service.py -v
```

Expected output:
```
16 passed in 0.29s
```

## References

- **PRD**: Epic 2 Story 2.1 (Permission Evaluation Logic)
- **Implementation Plan**: `.alucify/implementation-plans/rbac-mvp-implementation-plan-v3.md`
- **AppGraph**: `.alucify/appgraph.json` (node nl0504)
- **Task 1.1**: RBAC Models Implementation
- **Task 1.3**: RBAC Data Seeding
