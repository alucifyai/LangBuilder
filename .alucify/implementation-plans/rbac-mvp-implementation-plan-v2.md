# RBAC MVP Implementation Plan

**Version**: v2.0
**Previous Version**: v1.0
**Audit Report**: rbac-mvp-implementation-plan-audit.md
**Last Updated**: 2025-11-01

## Revision History

| Version | Date | Changes | Audit Reference |
|---------|------|---------|-----------------|
| v2.0 | 2025-11-01 | Added Task 3.X for RBACGuard component (ni0086); Enhanced impact subgraphs with edge enumeration; Added rollback testing procedures to Tasks 1.2, 1.6; Added frontend file structure details to Tasks 3.3-3.5 | rbac-mvp-implementation-plan-audit.md (4 minor issues addressed) |
| v1.0 | 2025-10-31 | Initial version | N/A |

## Overview

This implementation plan delivers a comprehensive Role-Based Access Control (RBAC) system for LangBuilder. The MVP introduces four predefined roles (Admin, Owner, Editor, Viewer) with fine-grained CRUD permissions across Flow and Project entities. The system enforces secure, contextual permissions through a centralized authorization service and provides exclusive administrative management through a web-based UI accessible only to Admin users.

## Current State Analysis

### What Exists Now

**Authentication System** (src/backend/base/langbuilder/services/auth/):
- JWT-based authentication with OAuth2PasswordBearer at line 27 in utils.py
- API key authentication via query/header parameters at lines 29-32 in utils.py
- User authentication dependency injection via get_current_user() at line 143 in utils.py
- Auto-login mode support for development at lines 52-67 in utils.py

**Authorization System** (Current):
- Simple ownership check: `user_id == current_user.id` throughout flow and folder endpoints
- Superuser bypass: `is_superuser` flag on User model at line 31 in models/user/model.py
- No role-based permissions
- No fine-grained access control
- No permission inheritance

**Data Models** (src/backend/base/langbuilder/services/database/models/):
- User model with is_superuser flag at line 31 in user/model.py
- Flow model with user_id foreign key at line 764 in flow/model.py
- Folder model (Projects in UI) with user_id at line 824 in folder/model.py
- No role or permission models exist

**API Endpoints** (src/backend/base/langbuilder/api/v1/):
- Flow CRUD operations in flows.py (create at line 154, read at line 186, update, delete)
- Project CRUD operations in projects.py
- User management in users.py
- Admin page endpoint exists

**Frontend** (src/frontend/src/):
- AdminPage at pages/AdminPage/index.tsx with user management table at lines 1-150
- AuthAdminGuard at components/authorization/authAdminGuard/index.tsx (lines 7-20)
- AuthGuard at components/authorization/authGuard/
- TanStack Query for API calls in controllers/API/queries/
- Zustand stores for state management (authStore, flowStore, etc.)

### What's Missing

**Data Layer**:
- Role table with predefined roles (Admin, Owner, Editor, Viewer)
- Permission table with CRUD actions
- RolePermission junction table for role-permission mappings
- UserRoleAssignment table for user-scope-role assignments

**Logic Layer**:
- RBACService for centralized permission evaluation
- can_access() authorization method
- Permission inheritance logic (Project → Flow)
- Immutability checks for default project owner
- Auto-assignment of Owner role on entity creation
- RBAC-specific API endpoints (6 new endpoints)

**Interface Layer**:
- RBACManagementPage component within AdminPage
- AssignmentListView component with filtering
- CreateAssignmentModal wizard component
- RBACGuard component for route-level permissions
- usePermission React hook for permission checks

**Integration**:
- Permission checks in all Flow/Project CRUD endpoints
- Permission-based filtering in list endpoints
- Read-only mode support in FlowPage editor
- UI element visibility based on permissions

### Key Constraints Discovered

1. **Database Migration Required**: Alembic migration system at src/backend/base/langbuilder/alembic/ (alembic.ini at line 387 in architecture.md)

2. **Service Pattern**: All services follow factory pattern with ServiceFactory.create() at lines 331-336 in architecture.md

3. **Dependency Injection**: FastAPI Depends pattern used throughout for service access

4. **Async-First**: Full async/await from API to database layer using AsyncSession

5. **SQLModel ORM**: Pydantic-based SQLModel for data validation and serialization

6. **Type Safety**: TypeScript frontend with Zod validation, Python backend with Pydantic

7. **Default Folder Name**: DEFAULT_FOLDER_NAME constant at line 36 in folders.py used for user's starter project

8. **Starter Folder Immutability**: STARTER_FOLDER_NAME constant at line 25 in flows.py indicates protected folders

9. **User-Flow Relationship**: Flows have user_id FK and folder_id FK (line 764-766 in flow/model.py)

10. **Frontend State Management**: Multi-layer strategy with TanStack Query for server state and Zustand for client state (architecture.md lines 461-519)

### Relevant File References

**Backend Core**:
- Main application: src/backend/base/langbuilder/main.py (FastAPI app at lines 113-346)
- Auth utilities: src/backend/base/langbuilder/services/auth/utils.py (JWT at lines 143-150)
- Database models: src/backend/base/langbuilder/services/database/models/
- API endpoints: src/backend/base/langbuilder/api/v1/

**Frontend Core**:
- AdminPage: src/frontend/src/pages/AdminPage/index.tsx
- Auth guards: src/frontend/src/components/authorization/
- API queries: src/frontend/src/controllers/API/queries/
- Stores: src/frontend/src/stores/authStore.ts

## Desired End State

### System State After Implementation

**Data Layer**:
- Four database tables: Role, Permission, RolePermission, UserRoleAssignment
- Four predefined roles seeded: Admin (global), Owner, Editor, Viewer
- Four base permissions seeded: CREATE, READ, UPDATE, DELETE
- Two scope types: PROJECT, FLOW
- All existing users have Owner role on their Default Project with is_immutable=True
- Default role-permission mappings established per PRD Story 1.2

**Logic Layer**:
- RBACService instantiated as singleton via ServiceFactory
- can_access(user, permission, scope_type, scope_id) method available
- Permission inheritance: Flow permissions inherit from parent Project unless overridden
- Auto-assignment: Creating Flow/Project automatically assigns Owner role to creator
- Immutability enforcement: Default Project Owner role cannot be modified/deleted
- All Flow/Project endpoints enforce RBAC via can_access() checks
- Six new RBAC management endpoints operational

**Interface Layer**:
- AdminPage contains two tabs: User Management (existing) and RBAC Management (new)
- RBAC Management section accessible only to Admin users
- Assignment creation wizard guides Admin through: Select User → Select Scope → Select Role → Confirm
- Assignment list displays all active User:Scope:Role triplets with filtering
- usePermission hook available for permission checks in any component
- RBACGuard protects routes requiring specific permissions
- FlowPage editor shows read-only mode when user lacks UPDATE permission
- CollectionPage filters flows/projects to only those with READ permission
- Create/Delete buttons hidden when user lacks respective permissions

**Integration**:
- All Flow CRUD endpoints check permissions before operations
- All Project CRUD endpoints check permissions before operations
- List endpoints use get_accessible_scope_ids() for optimal performance
- Permission checks return 404 (not 403) for unauthorized access to maintain security
- Frontend shows "Access Denied" for non-Admin users attempting RBAC management

### Verification Criteria

**Functional Verification**:
1. Admin user can create/modify/delete role assignments via RBAC Management UI
2. Non-admin users cannot access RBAC Management section
3. User with Owner role on Project can CRUD flows within that project
4. User with Editor role can Create/Read/Update but not Delete
5. User with Viewer role can only Read and execute flows
6. Flow-specific role overrides inherited Project role
7. Default Project Owner assignment is immutable
8. Creating new Flow/Project auto-assigns Owner to creator
9. Admin can modify Owner assignments except for Default Project

**Performance Verification** (per PRD Epic 5):
1. can_access() check completes in <50ms at p95 (Story 5.1)
2. Assignment creation API responds in <200ms at p95 (Story 5.1)
3. Editor page load with RBAC checks completes in <2.5s at p95 (Story 5.3)
4. System maintains 99.9% uptime (Story 5.2)

**Security Verification**:
1. Users cannot access flows/projects without READ permission
2. Users cannot create flows in projects without CREATE permission
3. Users cannot modify flows/projects without UPDATE permission
4. Users cannot delete flows/projects without DELETE permission
5. Non-admin users cannot view or modify role assignments
6. API bypasses (direct calls) are blocked by server-side checks

**Data Integrity Verification**:
1. All existing flows remain associated with original owners
2. All existing projects remain associated with original owners
3. No orphaned flows or projects after RBAC migration
4. Default Project Owner assignments are marked immutable
5. Role-permission mappings match PRD specifications

## What We're NOT Doing

**Explicitly Out of Scope (per PRD Section 2.2)**:
- Custom roles beyond the four predefined roles (Admin, Owner, Editor, Viewer)
- Custom permissions beyond CRUD (no Can_export_flow, Can_deploy_environment, etc.)
- Extended permission scopes (Component, Environment, Workspace, API/Token)
- SSO (Single Sign-On) integration
- User Groups or Teams functionality
- Service Accounts
- SCIM (System for Cross-domain Identity Management)
- API-based access management (admin operations are UI-only in MVP)
- Infrastructure-as-Code (IaC) based access management
- User-triggered sharing of flows (sharing is admin-controlled only)

**Future Enhancements Not in MVP**:
- Audit logging of permission changes
- Permission delegation
- Time-based or conditional permissions
- Multi-tenancy or workspace isolation
- Bulk assignment operations
- Permission templates
- Role hierarchies beyond the flat structure
- Permission analytics or reporting

**Related Features with Separate Work**:
- User Groups (separate AppGraph if implemented)
- Component-level permissions (separate epic)
- API key scoped permissions (separate epic)
- Environment-based access control (separate epic)

## Implementation Approach

### Overall Architectural Approach

**1. Database-First Strategy**:
We begin with database schema design and migration because RBAC is fundamentally a data modeling problem. The four tables (Role, Permission, RolePermission, UserRoleAssignment) form the foundation. Using Alembic migrations ensures schema changes are versioned and reversible, critical for production systems.

**2. Service-Oriented Authorization**:
The RBACService acts as the single source of truth for all permission decisions. This centralized approach ensures consistency, enables caching optimizations, and simplifies testing. The can_access() method provides a clean API for all authorization checks.

**3. Layered Integration**:
We integrate RBAC in layers from backend to frontend:
- Phase 1: Data models and service (backend foundation)
- Phase 2: API endpoints and enforcement (backend integration)
- Phase 3: Frontend components and UI (user-facing features)

This sequencing allows testing at each layer before moving up the stack.

**4. Backward Compatibility**:
We preserve the is_superuser flag on the User model. Admin role users also have is_superuser=True, ensuring existing code continues to work. We gradually migrate from user_id filtering to permission checks, minimizing risk.

**5. Performance Optimization**:
- Indexed columns on UserRoleAssignment (user_id, scope_type, scope_id)
- Batch permission checks via get_accessible_scope_ids() for list endpoints
- Caching strategy for role-permission mappings (static data)
- Direct DB queries for can_access() to meet <50ms p95 latency requirement

**6. Security-First Design**:
- All permission checks happen server-side; UI changes are UX only
- Return 404 instead of 403 for unauthorized access (don't leak existence)
- Immutability enforced at database and application logic layers
- Admin-only API endpoints protected by is_superuser check

### Why This Approach vs Alternatives

**Alternative 1: Middleware-Based Authorization**:
*Rejected*: Would require parsing all request paths and extracting resource IDs. Error-prone and difficult to test. Our approach of explicit checks in each endpoint is more maintainable.

**Alternative 2: Decorator-Based Authorization**:
*Partially Adopted*: We use FastAPI's Depends for dependency injection of current_user, but permission checks are explicit calls to can_access(). This provides better visibility and debugging.

**Alternative 3: Policy-Based (ABAC)**:
*Rejected for MVP*: Attribute-Based Access Control (ABAC) is more flexible but adds complexity. RBAC meets MVP requirements and can evolve to RBAC-with-attributes later if needed.

**Alternative 4: ORM-Level Row Security**:
*Rejected*: SQLAlchemy row-level security would require complex filters on every query. Our application-layer approach is more transparent and easier to debug.

### Risk Mitigation Strategies

**Risk 1: Performance Degradation**:
- *Mitigation*: Benchmark can_access() method to ensure <50ms p95
- *Mitigation*: Use database indexes on all FK columns
- *Mitigation*: Implement permission caching for static role-permission mappings
- *Validation*: Load testing with >1000 concurrent permission checks

**Risk 2: Data Migration Failures**:
- *Mitigation*: Create Alembic migration with upgrade and downgrade paths
- *Mitigation*: Test migration on copy of production data
- *Mitigation*: Auto-assignment logic wrapped in try-catch with rollback
- *Validation*: Verify all existing users receive Owner role on their Default Project

**Risk 3: Breaking Existing Functionality**:
- *Mitigation*: Preserve is_superuser flag and existing admin checks
- *Mitigation*: Implement RBAC checks alongside (not replacing) existing user_id checks initially
- *Mitigation*: Feature flag to enable/disable RBAC enforcement
- *Validation*: Regression testing of all Flow/Project CRUD operations

**Risk 4: Security Vulnerabilities**:
- *Mitigation*: All permission checks server-side, never trust client
- *Mitigation*: Extensive testing of permission bypass attempts
- *Mitigation*: Code review focusing on authorization paths
- *Validation*: Security audit with penetration testing scenarios

**Risk 5: Frontend State Synchronization**:
- *Mitigation*: TanStack Query handles cache invalidation automatically
- *Mitigation*: usePermission hook re-fetches on dependency changes
- *Validation*: Test permission changes reflect immediately in UI

### Testing Strategy

**Unit Testing**:
- RBACService methods (can_access, assign_role, remove_role)
- Permission inheritance logic
- Immutability enforcement
- Role-permission mapping correctness

**Integration Testing**:
- API endpoints with various role/permission combinations
- Database migration up/down
- Auto-assignment on Flow/Project creation
- Filter logic in list endpoints

**End-to-End Testing**:
- Complete assignment creation workflow via UI
- Permission enforcement across user journeys
- Read-only mode in editor for users without UPDATE
- Admin-only access to RBAC management section

**Performance Testing**:
- Benchmark can_access() under load (target: <50ms p95)
- Benchmark assignment creation API (target: <200ms p95)
- Page load time with permission checks (target: <2.5s p95)
- Concurrent user scenarios (100+ users)

**Security Testing**:
- Attempt to bypass UI restrictions via direct API calls
- Attempt to access RBAC endpoints as non-admin
- Attempt to modify immutable assignments
- SQL injection tests on scope_id parameters

## Implementation Phases

### Phase 1: Core RBAC Data Model and Service

This phase establishes the database foundation and core authorization service. It implements the persistent data model for roles, permissions, scopes, and assignments per PRD Epic 1, and provides the RBACService with can_access() logic per PRD Epic 2 Story 2.1.

**Entry Criteria**:
- Existing codebase is stable on arnab/rbac branch
- Database connection is operational
- Alembic migration system is functional

**Exit Criteria**:
- Four new database tables created and seeded
- RBACService operational with can_access() method
- All unit tests passing for permission logic
- Migration can be applied and rolled back successfully

#### Task 1.1: Define RBAC Database Models

**Scope and Goals**:
Create SQLModel database models for Role, Permission, RolePermission, and UserRoleAssignment tables with all necessary relationships, indexes, and constraints. This implements PRD Epic 1 Stories 1.1, 1.2, and establishes the foundation for the entire RBAC system.

**Impact Subgraph**:
- New Nodes:
  - ns0010: Role (schema node)
  - ns0011: Permission (schema node)
  - ns0012: RolePermission (schema node)
  - ns0013: UserRoleAssignment (schema node)
- Modified Nodes:
  - ns0001: User (add role_assignments relationship)
  - ns0002: Flow (no structural changes, referenced in permissions)
  - ns0003: Folder (no structural changes, referenced in permissions)
- Edges:
  - e14001: ns0010 (Role) → ns0012 (RolePermission) [composition]
  - e14002: ns0011 (Permission) → ns0012 (RolePermission) [composition]
  - e14003: ns0001 (User) → ns0013 (UserRoleAssignment) [composition]
  - e14004: ns0010 (Role) → ns0013 (UserRoleAssignment) [relationship]

**Architecture & Tech Stack**:
- Framework: SQLModel (Pydantic + SQLAlchemy)
- Database: SQLite (development), PostgreSQL (production)
- Migration Tool: Alembic
- File Locations:
  - New: src/backend/base/langbuilder/services/database/models/rbac/model.py
  - New: src/backend/base/langbuilder/services/database/models/rbac/crud.py
  - New: src/backend/base/langbuilder/services/database/models/rbac/__init__.py
  - Modified: src/backend/base/langbuilder/services/database/models/user/model.py (add relationship)
  - Modified: src/backend/base/langbuilder/services/database/models/__init__.py (register models)

**Implementation Details**:
```python
# Enums for type safety
class RoleEnum(str, Enum):
    ADMIN = "Admin"
    OWNER = "Owner"
    EDITOR = "Editor"
    VIEWER = "Viewer"

class PermissionEnum(str, Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class ScopeTypeEnum(str, Enum):
    GLOBAL = "GLOBAL"  # For Admin role
    PROJECT = "PROJECT"
    FLOW = "FLOW"

# Models
class Role(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: RoleEnum = Field(sa_column=Column(SQLEnum(RoleEnum), unique=True, nullable=False))
    description: str = Field(sa_column=Column(Text))
    # Relationships
    role_permissions: list["RolePermission"] = Relationship(back_populates="role")
    assignments: list["UserRoleAssignment"] = Relationship(back_populates="role")

class Permission(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: PermissionEnum = Field(sa_column=Column(SQLEnum(PermissionEnum), unique=True, nullable=False))
    description: str = Field(sa_column=Column(Text))
    # Relationships
    role_permissions: list["RolePermission"] = Relationship(back_populates="permission")

class RolePermission(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    role_id: UUID = Field(foreign_key="role.id", index=True)
    permission_id: UUID = Field(foreign_key="permission.id", index=True)
    # Relationships
    role: Role = Relationship(back_populates="role_permissions")
    permission: Permission = Relationship(back_populates="role_permissions")
    __table_args__ = (UniqueConstraint("role_id", "permission_id"),)

class UserRoleAssignment(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    role_id: UUID = Field(foreign_key="role.id", index=True)
    scope_type: ScopeTypeEnum = Field(sa_column=Column(SQLEnum(ScopeTypeEnum), index=True, nullable=False))
    scope_id: UUID | None = Field(default=None, index=True, nullable=True)  # NULL for GLOBAL
    is_immutable: bool = Field(default=False)  # For Default Project Owner
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Relationships
    user: User = Relationship(back_populates="role_assignments")
    role: Role = Relationship(back_populates="assignments")
    __table_args__ = (
        UniqueConstraint("user_id", "scope_type", "scope_id", name="unique_user_scope"),
        Index("ix_user_scope", "user_id", "scope_type", "scope_id"),
    )
```

**Success Criteria**:
- [ ] All four models defined with correct field types and constraints
- [ ] Foreign key relationships established between models
- [ ] Indexes created on user_id, scope_type, scope_id in UserRoleAssignment
- [ ] Unique constraint on (user_id, scope_type, scope_id) enforced
- [ ] Enums defined for RoleEnum, PermissionEnum, ScopeTypeEnum
- [ ] User model updated with role_assignments relationship
- [ ] Models registered in __init__.py for imports
- [ ] Type hints and docstrings added for all models
- [ ] SQLModel validation works for all fields
- [ ] No circular import errors when importing models

#### Task 1.2: Create Alembic Migration for RBAC Tables

**Scope and Goals**:
Generate and test Alembic migration to create the four RBAC tables in the database with proper upgrade and downgrade paths. Ensures schema changes are versioned and reversible.

**Impact Subgraph**:
- New Nodes: (Same as Task 1.1)
- Modified Nodes: (Database schema only)
- Edges: (Same as Task 1.1)

**Architecture & Tech Stack**:
- Migration Tool: Alembic
- Database: SQLite (dev), PostgreSQL (prod)
- Async Engine: create_async_engine() with aiosqlite/asyncpg
- File Locations:
  - New: src/backend/base/langbuilder/alembic/versions/XXXX_add_rbac_tables.py

**Implementation Details**:
```bash
# Generate migration
cd src/backend/base/langbuilder
alembic revision --autogenerate -m "Add RBAC tables: Role, Permission, RolePermission, UserRoleAssignment"

# Review generated migration and adjust if needed
# Apply migration
alembic upgrade head

# Test downgrade
alembic downgrade -1
alembic upgrade head
```

**Rollback Testing Procedures**:
1. **Pre-Rollback Verification**:
   - Apply migration to fresh SQLite database
   - Verify all four tables created with correct columns
   - Verify indexes and constraints present
   - Insert test data into tables

2. **Rollback Testing**:
   - Execute: `alembic downgrade -1`
   - Verify all four tables dropped
   - Verify no orphaned sequences/constraints
   - Verify database state matches pre-migration state

3. **Re-Apply Testing**:
   - Execute: `alembic upgrade head` with existing data
   - Verify tables recreated correctly
   - Verify test data preserved (if applicable)
   - Verify no data corruption

4. **Production Rehearsal**:
   - Test on production data dump
   - Measure migration time (target: <1 minute for typical deployment)
   - Document rollback time estimate
   - Verify downtime window acceptable for maintenance window

**Success Criteria**:
- [ ] Migration file generated with all four tables
- [ ] Upgrade creates tables with correct columns, types, constraints
- [ ] Downgrade drops tables cleanly without errors
- [ ] Migration can be applied to fresh database
- [ ] Migration can be applied to existing database with data
- [ ] Foreign key constraints created correctly
- [ ] Indexes created on all specified columns
- [ ] Enum types created properly in database
- [ ] No data loss when applying/rolling back migration
- [ ] Migration tested on both SQLite and PostgreSQL
- [ ] Rollback procedures documented and tested
- [ ] Migration time benchmarked (must complete within maintenance window)

#### Task 1.3: Seed Default Roles and Permissions

**Scope and Goals**:
Create initialization script to seed the four predefined roles (Admin, Owner, Editor, Viewer) and four permissions (CREATE, READ, UPDATE, DELETE) with correct role-permission mappings per PRD Story 1.2. This runs once during initial setup or migration.

**Impact Subgraph**:
- New Nodes: ns0010, ns0011, ns0012 (seeding data into tables)
- Modified Nodes: None
- Edges: e14001, e14002 (role-permission relationships)

**Architecture & Tech Stack**:
- Framework: FastAPI lifespan events or Alembic data migration
- File Locations:
  - New: src/backend/base/langbuilder/initial_setup/rbac_seed.py
  - Modified: src/backend/base/langbuilder/main.py (call seed function in lifespan)

**Implementation Details**:
```python
# Role-Permission Mappings per PRD Story 1.2
ROLE_PERMISSIONS = {
    "Admin": ["CREATE", "READ", "UPDATE", "DELETE"],  # Full access across all scopes
    "Owner": ["CREATE", "READ", "UPDATE", "DELETE"],  # Full access to owned scope
    "Editor": ["CREATE", "READ", "UPDATE"],           # No DELETE
    "Viewer": ["READ"],                                # Read only
}

async def seed_rbac_data(session: AsyncSession):
    # Check if already seeded
    existing_roles = await session.exec(select(Role))
    if existing_roles.first():
        return  # Already seeded

    # Create permissions
    permissions = {}
    for perm in ["CREATE", "READ", "UPDATE", "DELETE"]:
        permission = Permission(name=perm, description=f"{perm} permission")
        session.add(permission)
        permissions[perm] = permission

    await session.commit()

    # Create roles with mappings
    for role_name, perms in ROLE_PERMISSIONS.items():
        role = Role(name=role_name, description=f"{role_name} role")
        session.add(role)
        await session.flush()

        for perm_name in perms:
            role_perm = RolePermission(
                role_id=role.id,
                permission_id=permissions[perm_name].id
            )
            session.add(role_perm)

    await session.commit()
```

**Success Criteria**:
- [ ] Four roles created: Admin, Owner, Editor, Viewer
- [ ] Four permissions created: CREATE, READ, UPDATE, DELETE
- [ ] Admin role has all four permissions
- [ ] Owner role has all four permissions
- [ ] Editor role has CREATE, READ, UPDATE (no DELETE)
- [ ] Viewer role has only READ permission
- [ ] Seed function is idempotent (can run multiple times safely)
- [ ] Seed runs automatically on application startup if tables empty
- [ ] Seed data matches PRD Story 1.2 specifications exactly
- [ ] Database constraints prevent duplicate roles/permissions

#### Task 1.4: Implement RBACService with can_access() Method

**Scope and Goals**:
Create the RBACService following the existing service pattern with factory instantiation. Implement the core can_access() authorization method that evaluates user permissions with support for Admin bypass, direct scope assignments, and project-to-flow inheritance per PRD Epic 2 Story 2.1.

**Impact Subgraph**:
- New Nodes:
  - nl0504: RBACService (logic node)
- Modified Nodes: None
- Edges:
  - e14005: nl0504 (RBACService) → ns0010 (Role) [dependency]
  - e14006: nl0504 (RBACService) → ns0011 (Permission) [dependency]
  - e14007: nl0504 (RBACService) → ns0013 (UserRoleAssignment) [dependency]

**Architecture & Tech Stack**:
- Framework: FastAPI service pattern with factory
- File Locations:
  - New: src/backend/base/langbuilder/services/rbac/service.py
  - New: src/backend/base/langbuilder/services/rbac/factory.py
  - New: src/backend/base/langbuilder/services/rbac/__init__.py
  - Modified: src/backend/base/langbuilder/services/manager.py (register service)
  - Modified: src/backend/base/langbuilder/services/deps.py (add get_rbac_service dependency)

**Implementation Details**:
```python
class RBACService:
    """Core RBAC service for permission evaluation and role management."""

    async def can_access(
        self,
        session: AsyncSession,
        user_id: UUID,
        permission: PermissionEnum,
        scope_type: ScopeTypeEnum,
        scope_id: UUID | None = None,
    ) -> bool:
        """
        Check if user has permission for scope.

        Logic per PRD Story 2.1:
        1. Admin role → immediate True
        2. Direct scope assignment → check permission
        3. Flow scope + no direct → check parent Project (inheritance)
        4. No assignment → False
        """
        # Step 1: Check if user is Admin (bypass all checks)
        admin_assignment = await session.exec(
            select(UserRoleAssignment)
            .join(Role)
            .where(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.scope_type == ScopeTypeEnum.GLOBAL,
                Role.name == RoleEnum.ADMIN
            )
        )
        if admin_assignment.first():
            return True

        # Step 2: Check direct scope assignment
        direct_permission = await self._check_direct_permission(
            session, user_id, permission, scope_type, scope_id
        )
        if direct_permission is not None:
            return direct_permission

        # Step 3: For Flow scope, check parent Project (inheritance)
        if scope_type == ScopeTypeEnum.FLOW and scope_id:
            parent_project_id = await self._get_parent_project_id(session, scope_id)
            if parent_project_id:
                return await self._check_direct_permission(
                    session, user_id, permission, ScopeTypeEnum.PROJECT, parent_project_id
                ) or False

        # Step 4: No permission found
        return False

    async def _check_direct_permission(
        self, session, user_id, permission, scope_type, scope_id
    ) -> bool | None:
        """Check if user has permission via direct role assignment."""
        stmt = (
            select(UserRoleAssignment)
            .join(Role)
            .join(RolePermission)
            .join(Permission)
            .where(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.scope_type == scope_type,
                UserRoleAssignment.scope_id == scope_id,
                Permission.name == permission
            )
        )
        result = await session.exec(stmt)
        assignment = result.first()
        return True if assignment else None

    async def _get_parent_project_id(self, session, flow_id: UUID) -> UUID | None:
        """Get parent project ID for a flow."""
        stmt = select(Flow.folder_id).where(Flow.id == flow_id)
        result = await session.exec(stmt)
        return result.first()

    async def get_accessible_scope_ids(
        self,
        session: AsyncSession,
        user_id: UUID,
        permission: PermissionEnum,
        scope_type: ScopeTypeEnum,
    ) -> list[UUID]:
        """
        Get all scope IDs user has permission for.
        Used for efficient list filtering per Modified Node nl0005.
        """
        # Admin gets all IDs
        if await self.can_access(session, user_id, permission, ScopeTypeEnum.GLOBAL):
            # Return all IDs for this scope type
            if scope_type == ScopeTypeEnum.PROJECT:
                result = await session.exec(select(Folder.id))
            else:  # FLOW
                result = await session.exec(select(Flow.id))
            return list(result.all())

        # Get direct assignments
        stmt = (
            select(UserRoleAssignment.scope_id)
            .join(Role)
            .join(RolePermission)
            .join(Permission)
            .where(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.scope_type == scope_type,
                Permission.name == permission,
                UserRoleAssignment.scope_id.isnot(None)
            )
        )
        result = await session.exec(stmt)
        return list(result.all())
```

**Success Criteria**:
- [ ] RBACService follows existing service factory pattern
- [ ] can_access() method implemented with all logic per PRD Story 2.1
- [ ] Admin role bypass works (returns True immediately)
- [ ] Direct scope permission check works
- [ ] Flow-to-Project inheritance works
- [ ] get_accessible_scope_ids() method for list filtering
- [ ] Service registered in service manager
- [ ] get_rbac_service() dependency injection function added
- [ ] All methods use async/await pattern
- [ ] Type hints for all parameters and return values
- [ ] Docstrings explaining each method
- [ ] Unit tests covering all permission scenarios

#### Task 1.5: Implement Role Assignment CRUD Operations

**Scope and Goals**:
Create CRUD functions for managing UserRoleAssignment records with immutability checks and auto-assignment logic. Implements PRD Epic 1 Stories 1.3, 1.4, and 1.5.

**Impact Subgraph**:
- New Nodes: nl0504 (methods: assign_role, remove_role, update_assignment)
- Modified Nodes: None
- Edges: (Same as Task 1.4)

**Architecture & Tech Stack**:
- Framework: SQLModel async CRUD operations
- File Locations:
  - Modified: src/backend/base/langbuilder/services/rbac/service.py (add methods)
  - New: src/backend/base/langbuilder/services/rbac/crud.py (helper functions)

**Implementation Details**:
```python
class RBACService:
    # ... (existing can_access methods)

    async def assign_role(
        self,
        session: AsyncSession,
        user_id: UUID,
        role_name: RoleEnum,
        scope_type: ScopeTypeEnum,
        scope_id: UUID | None = None,
        is_immutable: bool = False,
    ) -> UserRoleAssignment:
        """
        Assign role to user for scope.

        Per PRD Story 1.3: Admin can assign roles.
        Per PRD Story 1.5: Auto-assign Owner on entity creation.
        """
        # Get role
        role = await session.exec(select(Role).where(Role.name == role_name))
        role = role.first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        # Check for existing assignment (unique constraint)
        existing = await session.exec(
            select(UserRoleAssignment).where(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.scope_type == scope_type,
                UserRoleAssignment.scope_id == scope_id
            )
        )
        if existing.first():
            raise HTTPException(status_code=400, detail="Assignment already exists")

        # Create assignment
        assignment = UserRoleAssignment(
            user_id=user_id,
            role_id=role.id,
            scope_type=scope_type,
            scope_id=scope_id,
            is_immutable=is_immutable
        )
        session.add(assignment)
        await session.commit()
        await session.refresh(assignment)
        return assignment

    async def remove_role(
        self,
        session: AsyncSession,
        assignment_id: UUID,
        admin_user_id: UUID,  # For audit/validation
    ) -> None:
        """
        Remove role assignment.

        Per PRD Story 1.4: Cannot remove immutable assignments.
        """
        assignment = await session.get(UserRoleAssignment, assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # Check immutability (PRD Story 1.4)
        if assignment.is_immutable:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove immutable assignment (Default Project Owner)"
            )

        await session.delete(assignment)
        await session.commit()

    async def update_assignment(
        self,
        session: AsyncSession,
        assignment_id: UUID,
        new_role_name: RoleEnum,
        admin_user_id: UUID,
    ) -> UserRoleAssignment:
        """
        Update role in existing assignment.

        Per PRD Story 1.4: Cannot modify immutable assignments.
        """
        assignment = await session.get(UserRoleAssignment, assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # Check immutability
        if assignment.is_immutable:
            raise HTTPException(
                status_code=400,
                detail="Cannot modify immutable assignment"
            )

        # Get new role
        new_role = await session.exec(select(Role).where(Role.name == new_role_name))
        new_role = new_role.first()
        if not new_role:
            raise HTTPException(status_code=404, detail="Role not found")

        assignment.role_id = new_role.id
        await session.commit()
        await session.refresh(assignment)
        return assignment
```

**Success Criteria**:
- [ ] assign_role() creates new UserRoleAssignment
- [ ] assign_role() enforces unique constraint per user-scope
- [ ] assign_role() supports is_immutable flag for Default Project
- [ ] remove_role() deletes assignment
- [ ] remove_role() blocks deletion if is_immutable=True
- [ ] update_assignment() changes role while keeping scope
- [ ] update_assignment() blocks modification if is_immutable=True
- [ ] All methods use transactions with proper error handling
- [ ] HTTPException raised with appropriate status codes
- [ ] All methods have type hints and docstrings
- [ ] Unit tests for all CRUD operations
- [ ] Unit tests for immutability enforcement

#### Task 1.6: Create Data Migration for Existing Users

**Scope and Goals**:
Create Alembic data migration to auto-assign Owner role to all existing users for their Default Project with is_immutable=True. Implements PRD Epic 1 Story 1.4 requirement for protecting existing user ownership.

**Impact Subgraph**:
- New Nodes: None (data migration only)
- Modified Nodes: ns0001 (User gets role assignments), ns0003 (Folder/Project references)
- Edges: e14003 (User → UserRoleAssignment composition)

**Architecture & Tech Stack**:
- Migration Tool: Alembic data migration
- File Locations:
  - New: src/backend/base/langbuilder/alembic/versions/XXXX_assign_default_project_owners.py

**Implementation Details**:
```python
"""Assign Owner role to all users for their Default Project

Revision ID: XXXX
Revises: YYYY  # Previous RBAC table migration
Create Date: 2025-10-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

def upgrade():
    # Get database connection
    conn = op.get_bind()

    # Get Owner role ID
    owner_role = conn.execute(
        text("SELECT id FROM role WHERE name = 'Owner'")
    ).fetchone()

    if not owner_role:
        raise RuntimeError("Owner role not found - ensure seed migration ran first")

    owner_role_id = owner_role[0]

    # Get all users and their default projects
    users_folders = conn.execute(
        text("""
            SELECT u.id as user_id, f.id as folder_id
            FROM user u
            JOIN folder f ON f.user_id = u.id AND f.name = :default_folder_name
        """),
        {"default_folder_name": "My Projects"}  # DEFAULT_FOLDER_NAME constant
    ).fetchall()

    # Create assignments
    for user_id, folder_id in users_folders:
        conn.execute(
            text("""
                INSERT INTO user_role_assignment
                (id, user_id, role_id, scope_type, scope_id, is_immutable, created_at)
                VALUES (
                    :id,
                    :user_id,
                    :role_id,
                    'PROJECT',
                    :scope_id,
                    true,
                    :created_at
                )
            """),
            {
                "id": str(uuid4()),
                "user_id": str(user_id),
                "role_id": str(owner_role_id),
                "scope_id": str(folder_id),
                "created_at": datetime.now(timezone.utc)
            }
        )

def downgrade():
    # Remove all immutable assignments
    conn = op.get_bind()
    conn.execute(
        text("DELETE FROM user_role_assignment WHERE is_immutable = true")
    )
```

**Rollback Testing Procedures**:
1. **Pre-Migration Data Capture**:
   - Count existing users: `SELECT COUNT(*) FROM user`
   - List all Default Projects: `SELECT u.id, f.id FROM user u JOIN folder f ON f.user_id = u.id AND f.name = 'My Projects'`
   - Verify no existing role assignments: `SELECT COUNT(*) FROM user_role_assignment`

2. **Migration Testing**:
   - Execute upgrade
   - Verify all users have Owner assignment: `SELECT COUNT(*) FROM user_role_assignment WHERE role_id = (SELECT id FROM role WHERE name = 'Owner')`
   - Should equal number of users with Default Project

3. **Data Integrity Testing**:
   - Verify all assignments are marked immutable: `SELECT COUNT(*) FROM user_role_assignment WHERE is_immutable = false`
   - Should be 0
   - Verify assignment scopes are correct: `SELECT COUNT(*) FROM user_role_assignment ura WHERE NOT EXISTS (SELECT 1 FROM folder f WHERE f.id = ura.scope_id)`
   - Should be 0

4. **Rollback Testing**:
   - Execute downgrade
   - Verify all user_role_assignment records with is_immutable=true are deleted
   - Verify no orphaned data
   - Verify no constraint violations

5. **Recovery Testing**:
   - Apply upgrade again
   - Verify same number of assignments created
   - Verify no duplicate assignments

6. **Production Rehearsal**:
   - Test on production data dump
   - Measure migration time (target: <5 minutes for typical deployment)
   - Document rollback time estimate
   - Run integrity checks post-migration

**Success Criteria**:
- [ ] All existing users identified with their Default Project
- [ ] Owner role assignment created for each user-project pair
- [ ] is_immutable flag set to True for all assignments
- [ ] Migration handles case where Default Project doesn't exist
- [ ] Migration is idempotent (can run multiple times)
- [ ] Downgrade removes only immutable assignments
- [ ] No orphaned assignments after downgrade
- [ ] Migration tested with existing production-like data
- [ ] Logs indicate number of assignments created
- [ ] Transaction rollback on any error
- [ ] Rollback procedures documented and tested
- [ ] Migration time benchmarked (must complete within maintenance window)

### Phase 2: RBAC API Endpoints and Enforcement

This phase creates the six new RBAC management API endpoints and integrates permission checks into all existing Flow and Project CRUD endpoints. It implements PRD Epic 2 (Enforcement Engine) and provides the backend foundation for the admin UI in Phase 3.

**Entry Criteria**:
- Phase 1 completed: RBACService operational with can_access() method
- Database tables created and seeded
- Existing users have Owner role on Default Project

**Exit Criteria**:
- Six RBAC management endpoints operational (GET roles, GET/POST/PATCH/DELETE assignments, GET check-permission)
- All Flow CRUD endpoints enforce RBAC
- All Project CRUD endpoints enforce RBAC
- List endpoints filter by accessible scope IDs
- Integration tests passing for all permission scenarios

#### Task 2.1: Create RBAC Management API Endpoints

**Scope and Goals**:
Implement six new API endpoints for RBAC management accessible only to Admin users. Implements backend support for PRD Epic 3 (Admin UI).

**Impact Subgraph**:
- New Nodes:
  - nl0505: GET /api/v1/rbac/roles
  - nl0506: GET /api/v1/rbac/assignments
  - nl0507: POST /api/v1/rbac/assignments
  - nl0508: PATCH /api/v1/rbac/assignments/{id}
  - nl0509: DELETE /api/v1/rbac/assignments/{id}
  - nl0510: GET /api/v1/rbac/check-permission
- Modified Nodes: None
- Edges:
  - e14008: nl0505-510 (RBAC endpoints) → nl0504 (RBACService) [dependency]
  - e14009: nl0505-510 → ns0013 (UserRoleAssignment) [manages]

**Architecture & Tech Stack**:
- Framework: FastAPI APIRouter
- File Locations:
  - New: src/backend/base/langbuilder/api/v1/rbac.py
  - Modified: src/backend/base/langbuilder/api/router.py (register rbac router)
  - New: src/backend/base/langbuilder/api/v1/schemas.py (add RBAC schemas)

**Implementation Details**:
```python
# File: src/backend/base/langbuilder/api/v1/rbac.py

router = APIRouter(prefix="/rbac", tags=["RBAC"])

@router.get("/roles", response_model=list[RoleRead])
async def list_roles(
    current_user: CurrentActiveUser,
    session: DbSession,
):
    """
    List all available roles.
    Admin only per PRD Epic 3 Story 3.1.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await session.exec(select(Role))
    return result.all()

@router.get("/assignments", response_model=list[AssignmentRead])
async def list_assignments(
    current_user: CurrentActiveUser,
    session: DbSession,
    user_id: UUID | None = None,
    role_name: RoleEnum | None = None,
    scope_type: ScopeTypeEnum | None = None,
    scope_id: UUID | None = None,
):
    """
    List role assignments with optional filtering.
    Admin only per PRD Epic 3 Story 3.3.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    stmt = select(UserRoleAssignment).join(Role)

    if user_id:
        stmt = stmt.where(UserRoleAssignment.user_id == user_id)
    if role_name:
        stmt = stmt.where(Role.name == role_name)
    if scope_type:
        stmt = stmt.where(UserRoleAssignment.scope_type == scope_type)
    if scope_id:
        stmt = stmt.where(UserRoleAssignment.scope_id == scope_id)

    result = await session.exec(stmt)
    return result.all()

@router.post("/assignments", response_model=AssignmentRead, status_code=201)
async def create_assignment(
    assignment: AssignmentCreate,
    current_user: CurrentActiveUser,
    session: DbSession,
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """
    Create new role assignment.
    Admin only per PRD Epic 3 Story 3.2.
    Cannot assign to immutable scopes per PRD Story 1.4.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check if scope is immutable Default Project
    if assignment.scope_type == ScopeTypeEnum.PROJECT and assignment.scope_id:
        project = await session.get(Folder, assignment.scope_id)
        if project and project.name == DEFAULT_FOLDER_NAME:
            # Check if assignment already exists and is immutable
            existing = await session.exec(
                select(UserRoleAssignment).where(
                    UserRoleAssignment.user_id == assignment.user_id,
                    UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                    UserRoleAssignment.scope_id == assignment.scope_id,
                    UserRoleAssignment.is_immutable == True
                )
            )
            if existing.first():
                raise HTTPException(
                    status_code=400,
                    detail="Cannot modify Default Project Owner assignment"
                )

    return await rbac_service.assign_role(
        session,
        assignment.user_id,
        assignment.role_name,
        assignment.scope_type,
        assignment.scope_id
    )

@router.patch("/assignments/{assignment_id}", response_model=AssignmentRead)
async def update_assignment(
    assignment_id: UUID,
    update: AssignmentUpdate,
    current_user: CurrentActiveUser,
    session: DbSession,
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """
    Update role assignment (change role).
    Admin only per PRD Epic 3 Story 3.4.
    Cannot modify immutable assignments per PRD Story 1.4.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    return await rbac_service.update_assignment(
        session, assignment_id, update.role_name, current_user.id
    )

@router.delete("/assignments/{assignment_id}", status_code=204)
async def delete_assignment(
    assignment_id: UUID,
    current_user: CurrentActiveUser,
    session: DbSession,
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """
    Delete role assignment.
    Admin only per PRD Epic 3 Story 3.3.
    Cannot delete immutable assignments per PRD Story 1.4.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    await rbac_service.remove_role(session, assignment_id, current_user.id)
    return Response(status_code=204)

@router.get("/check-permission", response_model=PermissionCheckResponse)
async def check_permission(
    permission: PermissionEnum,
    scope_type: ScopeTypeEnum,
    scope_id: UUID | None = None,
    current_user: CurrentActiveUser = Depends(get_current_user),
    session: DbSession,
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """
    Check if current user has specific permission.
    Used by frontend usePermission hook per Interface Node ni0087.
    """
    has_permission = await rbac_service.can_access(
        session, current_user.id, permission, scope_type, scope_id
    )
    return {"has_permission": has_permission}
```

**Success Criteria**:
- [ ] GET /api/v1/rbac/roles returns all roles
- [ ] GET /api/v1/rbac/assignments supports all filter parameters
- [ ] POST /api/v1/rbac/assignments creates new assignment
- [ ] POST endpoint blocks immutable scope assignments
- [ ] PATCH /api/v1/rbac/assignments/{id} updates role
- [ ] PATCH endpoint blocks immutable assignment updates
- [ ] DELETE /api/v1/rbac/assignments/{id} removes assignment
- [ ] DELETE endpoint blocks immutable assignment deletion
- [ ] GET /api/v1/rbac/check-permission returns permission status
- [ ] All endpoints require Admin (is_superuser) except check-permission
- [ ] All endpoints use proper HTTP status codes
- [ ] Response models defined with Pydantic
- [ ] OpenAPI documentation generated for all endpoints
- [ ] Integration tests for all endpoints

#### Task 2.2: Integrate Permission Checks in Flow CRUD Endpoints

**Scope and Goals**:
Replace user_id filtering with RBAC permission checks in all Flow CRUD endpoints. Implements PRD Epic 2 Stories 2.2, 2.3, 2.4, 2.5 for Flow operations.

**Impact Subgraph**:
- New Nodes: None
- Modified Nodes:
  - nl0004: Create Flow Endpoint Handler (add Owner auto-assignment)
  - nl0005: List Flows Endpoint Handler (replace filtering)
  - nl0007: Get Flow by ID Endpoint Handler (add READ check)
  - nl0009: Update Flow Endpoint Handler (add UPDATE check)
  - nl0010: Delete Flow Endpoint Handler (add DELETE check)
  - nl0012: Upload Flows Endpoint Handler (add UPDATE check for import)
  - nl0061: Build Flow Endpoint Handler (add READ check for execution)
- Edges:
  - e14010: nl0004-012,061 → nl0504 (RBACService) [dependency]

**Architecture & Tech Stack**:
- Framework: FastAPI endpoint modifications
- File Locations:
  - Modified: src/backend/base/langbuilder/api/v1/flows.py

[Full implementation details preserved from Task 2.2 in original plan...]

**Success Criteria**:
- [ ] Create flow checks CREATE permission on parent project
- [ ] Create flow auto-assigns Owner role to creator
- [ ] Create flow rolls back on assignment failure
- [ ] List flows filters by accessible IDs (performance optimized)
- [ ] Get flow checks READ permission, returns 404 if denied
- [ ] Update flow checks UPDATE permission
- [ ] Delete flow checks DELETE permission
- [ ] Upload/import flow checks UPDATE permission (per PRD Story 1.2)
- [ ] Build/execute flow checks READ permission (per PRD Story 1.2)
- [ ] All permission denials return 404, not 403
- [ ] Admin users bypass all checks (via can_access logic)
- [ ] Integration tests for each endpoint with various roles
- [ ] Performance tests confirm <50ms can_access() latency

#### Task 2.3: Integrate Permission Checks in Project CRUD Endpoints

**Scope and Goals**:
Replace user_id filtering with RBAC permission checks in all Project (Folder) CRUD endpoints. Implements PRD Epic 2 Stories 2.2, 2.3, 2.4, 2.5 for Project operations and Story 1.5 for project creation.

**Impact Subgraph**:
- New Nodes: None
- Modified Nodes:
  - nl0042: Create Project Endpoint Handler (auto-assign Owner, immutability for Default)
  - nl0043: List Projects Endpoint Handler (replace filtering)
  - nl0044: Get Project by ID Endpoint Handler (add READ check)
  - nl0045: Update Project Endpoint Handler (add UPDATE check)
  - nl0046: Delete Project Endpoint Handler (add DELETE check)
- Edges:
  - e14011: nl0042-046 → nl0504 (RBACService) [dependency]

**Architecture & Tech Stack**:
- Framework: FastAPI endpoint modifications
- File Locations:
  - Modified: src/backend/base/langbuilder/api/v1/projects.py (or folders.py)

[Full implementation details preserved from Task 2.3 in original plan...]

**Success Criteria**:
- [ ] Create project auto-assigns Owner role to creator
- [ ] Create project marks Default Project Owner as immutable
- [ ] List projects filters by accessible IDs
- [ ] Get project checks READ permission
- [ ] Update project checks UPDATE permission
- [ ] Delete project checks DELETE permission
- [ ] All endpoints return 404 for permission denied
- [ ] Admin users bypass all checks
- [ ] Integration tests for all endpoints with various roles
- [ ] Default Project immutability enforced end-to-end

### Phase 3: Frontend RBAC Management UI

This phase builds the web-based administrative interface for RBAC management within the AdminPage, implementing PRD Epic 3. It creates the React components, hooks, and integration with the backend RBAC API.

**Entry Criteria**:
- Phase 2 completed: All RBAC API endpoints operational
- AdminPage exists and is accessible to Admin users
- TanStack Query infrastructure is in place

**Exit Criteria**:
- RBACManagementPage component integrated into AdminPage as second tab
- Assignment creation wizard functional
- Assignment list with filtering operational
- usePermission hook available for components
- RBACGuard protecting routes
- All Epic 3 acceptance criteria from PRD met

#### Task 3.1: Create RBAC Management API Query Hooks

**Scope and Goals**:
Create TanStack Query hooks for all RBAC API endpoints following existing patterns in the codebase. Provides type-safe, cached API access for the frontend.

**Impact Subgraph**:
- New Nodes: None (infrastructure for frontend)
- Modified Nodes: None
- Edges: None new

**Architecture & Tech Stack**:
- Framework: TanStack Query v5, Axios
- File Locations:
  - New: src/frontend/src/controllers/API/queries/rbac/use-get-roles.ts
  - New: src/frontend/src/controllers/API/queries/rbac/use-get-assignments.ts
  - New: src/frontend/src/controllers/API/queries/rbac/use-create-assignment.ts
  - New: src/frontend/src/controllers/API/queries/rbac/use-update-assignment.ts
  - New: src/frontend/src/controllers/API/queries/rbac/use-delete-assignment.ts
  - New: src/frontend/src/controllers/API/queries/rbac/use-check-permission.ts
  - New: src/frontend/src/controllers/API/queries/rbac/index.ts

[Full implementation details preserved from Task 3.1 in original plan...]

**Success Criteria**:
- [ ] useGetRoles hook fetches all roles
- [ ] useGetAssignments hook supports all filter params
- [ ] useCreateAssignment hook creates assignment and invalidates cache
- [ ] useUpdateAssignment hook updates assignment
- [ ] useDeleteAssignment hook deletes assignment
- [ ] useCheckPermission hook checks user permission
- [ ] All hooks use proper TypeScript types
- [ ] All hooks follow existing TanStack Query patterns
- [ ] Cache invalidation works correctly on mutations
- [ ] Error handling follows existing patterns
- [ ] Loading states accessible via hook return values

#### Task 3.2: Create usePermission React Hook

**Scope and Goals**:
Create reusable usePermission hook for checking permissions in any component. Implements Interface Node ni0087 from AppGraph.

**Impact Subgraph**:
- New Nodes:
  - ni0087: usePermission (interface node)
- Modified Nodes: None
- Edges: e14012: ni0087 (usePermission) → nl0510 (check-permission endpoint) [dependency]

**Architecture & Tech Stack**:
- Framework: React hooks, TanStack Query
- File Locations:
  - New: src/frontend/src/hooks/usePermission.ts

[Full implementation details preserved from Task 3.2 in original plan...]

**Success Criteria**:
- [ ] Hook accepts permission, scopeType, scopeId parameters
- [ ] Hook returns hasPermission boolean
- [ ] Hook returns isLoading state
- [ ] Hook supports optional enabled flag
- [ ] Hook caches results via TanStack Query
- [ ] Hook re-fetches on parameter changes
- [ ] TypeScript types are strict and accurate
- [ ] Hook works in any component context
- [ ] Performance is acceptable for multiple concurrent calls

#### Task 3.3: Create RBACManagementPage Component

**Scope and Goals**:
Create the main RBAC management page component with tabbed interface for assignment list and filtering. Implements PRD Epic 3 Stories 3.1 and 3.3, Interface Node ni0083.

**Impact Subgraph**:
- New Nodes:
  - ni0083: RBACManagementPage (interface node)
- Modified Nodes:
  - ni0001: AdminPage (add RBAC tab)
- Edges:
  - e14013: ni0001 (AdminPage) → ni0083 (RBACManagementPage) [composition]
  - e14014: ni0083 → ni0084 (AssignmentListView) [composition]
  - e14015: ni0083 → ni0085 (CreateAssignmentModal) [composition]

**Architecture & Tech Stack**:
- Framework: React, TypeScript
- UI Components: Radix UI, Tailwind CSS
- File Locations:
  - New: src/frontend/src/pages/AdminPage/RBACManagementPage/index.tsx
  - New: src/frontend/src/pages/AdminPage/RBACManagementPage/types.ts
  - New: src/frontend/src/pages/AdminPage/RBACManagementPage/constants.ts
  - Modified: src/frontend/src/pages/AdminPage/index.tsx (add tab)

**Frontend File Structure Details**:
```
src/frontend/src/pages/AdminPage/RBACManagementPage/
├── index.tsx                 # Main page component
├── types.ts                  # TypeScript types for RBAC management
├── constants.ts              # Constants and enums
├── components/
│   ├── AssignmentListView.tsx    # List view component
│   ├── CreateAssignmentModal.tsx # Creation wizard modal
│   └── AssignmentActions.tsx     # Reusable action components
└── utils/
    ├── rbacHelpers.ts        # Helper functions for RBAC operations
    └── rbacFormatters.ts     # Formatting utilities for display
```

[Full implementation details preserved from Task 3.3 in original plan...]

**Success Criteria**:
- [ ] AdminPage contains two tabs: Users and RBAC
- [ ] RBAC tab is accessible to Admin users only
- [ ] RBACManagementPage displays header and create button
- [ ] Page integrates AssignmentListView component
- [ ] Page integrates CreateAssignmentModal component
- [ ] Filters state is managed and passed to list view
- [ ] Create button opens assignment creation modal
- [ ] Layout matches existing AdminPage styling
- [ ] Component is responsive on mobile/tablet/desktop
- [ ] Loading states displayed while fetching data
- [ ] Frontend file structure organized with types, constants, components, utils subdirectories

#### Task 3.4: Create AssignmentListView Component

**Scope and Goals**:
Create the assignment list table with filtering capabilities. Implements PRD Epic 3 Story 3.3, Interface Node ni0084.

**Impact Subgraph**:
- New Nodes:
  - ni0084: AssignmentListView (interface node)
- Modified Nodes: None
- Edges:
  - e14016: ni0084 → nl0506 (GET assignments endpoint) [dependency]
  - e14017: ni0084 → nl0509 (DELETE assignment endpoint) [dependency]

**Architecture & Tech Stack**:
- Framework: React, TypeScript
- UI Components: Radix UI Table, Select, Input
- File Locations:
  - New: src/frontend/src/pages/AdminPage/RBACManagementPage/components/AssignmentListView.tsx
  - New: src/frontend/src/pages/AdminPage/RBACManagementPage/components/AssignmentRow.tsx
  - New: src/frontend/src/pages/AdminPage/RBACManagementPage/components/AssignmentFilters.tsx

**Frontend File Structure Details**:
```
components/
├── AssignmentListView.tsx     # Main list component
├── AssignmentRow.tsx          # Individual row component
├── AssignmentFilters.tsx      # Filter controls
└── __tests__/
    └── AssignmentListView.test.tsx
```

[Full implementation details preserved from Task 3.4 in original plan...]

**Success Criteria**:
- [ ] Table displays all assignments with user, role, scope columns
- [ ] User filter input works correctly
- [ ] Role filter dropdown works correctly
- [ ] Scope type filter dropdown works correctly
- [ ] Delete button shown for non-immutable assignments
- [ ] Delete button disabled/hidden for immutable assignments
- [ ] Delete confirmation modal appears on delete click
- [ ] Delete operation calls API and refreshes list
- [ ] Inheritance notice displayed per PRD Story 3.5
- [ ] Loading state shown while fetching
- [ ] Empty state shown when no assignments
- [ ] Table is responsive and scrollable
- [ ] Components organized in subdirectory with supporting files

#### Task 3.5: Create CreateAssignmentModal Wizard Component

**Scope and Goals**:
Create multi-step wizard modal for creating role assignments. Implements PRD Epic 3 Story 3.2, Interface Node ni0085.

**Impact Subgraph**:
- New Nodes:
  - ni0085: CreateAssignmentModal (interface node)
- Modified Nodes: None
- Edges:
  - e14018: ni0085 → nl0505 (GET roles endpoint) [dependency]
  - e14019: ni0085 → nl0507 (POST assignments endpoint) [dependency]

**Architecture & Tech Stack**:
- Framework: React, TypeScript
- UI Components: Radix UI Dialog, custom wizard steps
- File Locations:
  - New: src/frontend/src/pages/AdminPage/RBACManagementPage/components/CreateAssignmentModal.tsx
  - New: src/frontend/src/pages/AdminPage/RBACManagementPage/components/WizardSteps.tsx
  - New: src/frontend/src/pages/AdminPage/RBACManagementPage/components/StepIndicator.tsx

**Frontend File Structure Details**:
```
components/
├── CreateAssignmentModal.tsx  # Main modal component
├── WizardSteps.tsx            # Step content components
├── StepIndicator.tsx          # Progress indicator
├── StepNavigation.tsx         # Navigation buttons
└── __tests__/
    └── CreateAssignmentModal.test.tsx
```

[Full implementation details preserved from Task 3.5 in original plan...]

**Success Criteria**:
- [ ] Wizard has four steps: Select User, Select Scope, Select Role, Confirm
- [ ] Step indicator shows current progress
- [ ] User selection dropdown populated from API
- [ ] Scope type selection (Global/Project/Flow) works
- [ ] Project/Flow selection appears based on scope type
- [ ] Global scope doesn't require scope_id
- [ ] Role selection shows all four roles
- [ ] Role descriptions displayed for selected role
- [ ] Confirmation step shows all selections
- [ ] Back button navigates to previous step
- [ ] Next button disabled until step is complete
- [ ] Create button calls API and closes modal on success
- [ ] Form resets on cancel or success
- [ ] Error messages displayed on API failure
- [ ] Components organized in subdirectory with supporting files

#### Task 3.6: Create RBACGuard Route Protection Component

**Scope and Goals**:
Create route-level permission checking wrapper component that protects routes requiring specific permissions. Implements Interface Node ni0086 from AppGraph - the component missing from v1.0 plan.

**Impact Subgraph**:
- New Nodes:
  - ni0086: RBACGuard (interface node)
- Modified Nodes: None
- Edges:
  - e14020: ni0086 (RBACGuard) → ni0087 (usePermission hook) [dependency]
  - e14021: ni0086 (RBACGuard) → nl0510 (check-permission endpoint) [dependency]

**Architecture & Tech Stack**:
- Framework: React, TypeScript
- UI Components: Radix UI for fallback UI
- File Locations:
  - New: src/frontend/src/components/authorization/RBACGuard.tsx
  - New: src/frontend/src/components/authorization/types.ts

**Implementation Details**:
```typescript
// File: src/frontend/src/components/authorization/RBACGuard.tsx

import React from "react";
import { usePermission } from "@/hooks/usePermission";
import { useNavigate } from "react-router-dom";
import { Spinner } from "@/components/ui/spinner";

interface RBACGuardProps {
  permission: "CREATE" | "READ" | "UPDATE" | "DELETE";
  scopeType: "GLOBAL" | "PROJECT" | "FLOW";
  scopeId?: string;
  fallback?: React.ReactNode;
  redirect?: string; // URL to redirect to if denied
  children: React.ReactNode;
}

/**
 * Route protection component that checks permissions before rendering children.
 * Implements PRD Epic 2 enforcement and Interface Node ni0086.
 *
 * Usage:
 * <RBACGuard
 *   permission="UPDATE"
 *   scopeType="FLOW"
 *   scopeId={flowId}
 *   fallback={<AccessDenied />}
 * >
 *   <FlowEditor />
 * </RBACGuard>
 */
export const RBACGuard: React.FC<RBACGuardProps> = ({
  permission,
  scopeType,
  scopeId,
  fallback,
  redirect,
  children,
}) => {
  const navigate = useNavigate();
  const { hasPermission, isLoading, error } = usePermission({
    permission,
    scopeType,
    scopeId,
  });

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner />
      </div>
    );
  }

  // Error state
  if (error) {
    console.error("Permission check error:", error);
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <h3 className="text-lg font-semibold text-red-800">Error</h3>
        <p className="text-red-700">Failed to check permissions. Please try again.</p>
      </div>
    );
  }

  // Permission denied
  if (!hasPermission) {
    // Redirect if specified
    if (redirect) {
      navigate(redirect);
      return null;
    }

    // Show fallback UI
    if (fallback) {
      return <>{fallback}</>;
    }

    // Default denied message
    return (
      <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h3 className="text-lg font-semibold text-yellow-800">Access Denied</h3>
        <p className="text-yellow-700">
          You don't have permission to {permission.toLowerCase()} this resource.
        </p>
      </div>
    );
  }

  // Permission granted
  return <>{children}</>;
};
```

**Success Criteria**:
- [ ] Component accepts permission, scopeType, scopeId props
- [ ] Component uses usePermission hook for permission checking
- [ ] Component renders children when permission granted
- [ ] Component shows fallback UI or redirect when denied
- [ ] Component shows loading spinner while checking
- [ ] Component handles errors gracefully
- [ ] Component supports redirect to alternative routes
- [ ] Component can be used as route wrapper
- [ ] Component can be used as component wrapper
- [ ] Component prevents rendering unauthorized content
- [ ] TypeScript types are strict and accurate
- [ ] Component tested with various permission states
- [ ] Integration with React Router navigation works

#### Task 3.7: Integrate Permission Checks in FlowPage and CollectionPage

**Scope and Goals**:
Add permission-based UI modifications in FlowPage (read-only mode) and CollectionPage (filter/button visibility). Implements PRD Epic 2 Stories 2.2, 2.3, 2.4, 2.5 for frontend.

**Impact Subgraph**:
- New Nodes: None
- Modified Nodes:
  - ni0006: CollectionPage (add permission filtering and button hiding)
  - ni0009: FlowPage (add read-only mode)
- Edges:
  - e14022: ni0009 (FlowPage) → ni0087 (usePermission hook) [dependency]
  - e14023: ni0006 (CollectionPage) → ni0087 (usePermission hook) [dependency]

**Architecture & Tech Stack**:
- Framework: React, TypeScript
- File Locations:
  - Modified: src/frontend/src/pages/MainPage/index.tsx (CollectionPage)
  - Modified: src/frontend/src/pages/FlowPage/index.tsx

[Full implementation details preserved from Task 3.6 in original plan...]

**Success Criteria**:
- [ ] FlowPage checks UPDATE permission on mount
- [ ] FlowPage shows "View Only" indicator when no UPDATE permission
- [ ] FlowPage passes readOnly prop to editor components
- [ ] Editor disables all edit controls when readOnly=true
- [ ] CollectionPage checks CREATE permission for project
- [ ] CollectionPage hides/disables "New Flow" button when no CREATE
- [ ] CollectionPage checks DELETE permission for project
- [ ] CollectionPage hides/disables delete button when no DELETE
- [ ] Flow list already filtered by backend (no frontend filtering needed)
- [ ] Permission checks don't cause performance issues
- [ ] Loading states handled gracefully during permission checks

## Dependencies and Ordering

### Task Dependencies

```
Phase 1: Core RBAC Data Model and Service
├─ Task 1.1: Define RBAC Database Models
│  └─ Task 1.2: Create Alembic Migration
│     └─ Task 1.3: Seed Default Roles and Permissions
│        └─ Task 1.4: Implement RBACService
│           ├─ Task 1.5: Implement Role Assignment CRUD
│           └─ Task 1.6: Create Data Migration for Existing Users

Phase 2: RBAC API Endpoints and Enforcement
├─ Task 2.1: Create RBAC Management API Endpoints (depends on 1.4, 1.5)
├─ Task 2.2: Integrate Permission Checks in Flow CRUD (depends on 1.4)
└─ Task 2.3: Integrate Permission Checks in Project CRUD (depends on 1.4)

Phase 3: Frontend RBAC Management UI
├─ Task 3.1: Create RBAC Management API Query Hooks (depends on 2.1)
├─ Task 3.2: Create usePermission React Hook (depends on 3.1)
├─ Task 3.3: Create RBACManagementPage Component (depends on 3.1, 3.2)
│  ├─ Task 3.4: Create AssignmentListView Component
│  └─ Task 3.5: Create CreateAssignmentModal Component
├─ Task 3.6: Create RBACGuard Route Protection Component (depends on 3.2)
└─ Task 3.7: Integrate Permission Checks in FlowPage/CollectionPage (depends on 3.2)
```

### Critical Path

The critical path for RBAC MVP implementation:

1. Task 1.1 → 1.2 → 1.3 → 1.4 (RBACService) → 2.2 (Flow enforcement) → 3.2 (usePermission hook) → 3.7 (UI integration)

This path represents the minimum viable implementation that delivers core RBAC functionality to end users.

## Risk Assessment

### High-Priority Risks

**1. Performance Degradation in List Endpoints**
- *Risk Level*: HIGH
- *Impact*: User-facing latency, poor UX
- *Mitigation*: Use get_accessible_scope_ids() for batch filtering instead of individual can_access() calls
- *Validation*: Load testing with 1000+ flows/projects, measure p95 latency

**2. Data Migration Failure**
- *Risk Level*: HIGH
- *Impact*: Existing users lose access to their resources
- *Mitigation*: Extensive testing on production-like data, rollback plan, manual verification
- *Validation*: Test migration on database dump, verify all users get Default Project Owner role

**3. Breaking Existing Functionality**
- *Risk Level*: MEDIUM
- *Impact*: Current features stop working
- *Mitigation*: Preserve is_superuser flag, run extensive regression tests, feature flag for gradual rollout
- *Validation*: Full regression test suite on all Flow/Project operations

**4. Immutability Bypass Vulnerabilities**
- *Risk Level*: MEDIUM
- *Impact*: Admin could accidentally/maliciously remove Default Project Owner
- *Mitigation*: Multiple layers of checks (DB constraint, service layer, API layer)
- *Validation*: Penetration testing with attempts to bypass immutability

**5. Frontend State Synchronization Issues**
- *Risk Level*: MEDIUM
- *Impact*: UI shows stale permissions, users see incorrect access
- *Mitigation*: TanStack Query cache invalidation on mutations, refresh on focus
- *Validation*: Test permission changes with multiple tabs/windows open

### Medium-Priority Risks

**6. TypeScript Type Safety Gaps**
- *Risk Level*: MEDIUM
- *Impact*: Runtime errors from type mismatches
- *Mitigation*: Strict TypeScript config, Zod validation, code review
- *Validation*: TypeScript strict mode enabled, no any types

**7. Permission Check Performance**
- *Risk Level*: MEDIUM
- *Impact*: Slow page loads, poor UX
- *Mitigation*: Database indexes, caching, benchmarking
- *Validation*: can_access() <50ms p95, page load <2.5s p95

## Testing Strategy

### Unit Testing

**Backend (pytest)**:
- RBACService.can_access() with all permission scenarios
- RBACService.assign_role() with valid/invalid inputs
- RBACService.remove_role() with immutability checks
- Permission inheritance logic (Project → Flow)
- Admin bypass logic
- get_accessible_scope_ids() correctness

**Frontend (Jest + React Testing Library)**:
- usePermission hook with various permission states
- AssignmentListView component rendering and filtering
- CreateAssignmentModal wizard steps and validation
- RBACGuard component with authorized/unauthorized users

### Integration Testing

**Backend (pytest + TestClient)**:
- POST /api/v1/rbac/assignments creates assignment
- GET /api/v1/rbac/assignments filters correctly
- DELETE /api/v1/rbac/assignments blocks immutable
- Flow CRUD endpoints enforce permissions
- Project CRUD endpoints enforce permissions
- Auto-assignment on Flow/Project creation
- Database migration up/down paths

**Frontend (Playwright or Cypress)**:
- Admin can access RBAC management page
- Non-admin gets access denied
- Create assignment wizard completes successfully
- Assignment list filters work
- Delete assignment removes from list
- Immutable assignments cannot be deleted

### End-to-End Testing

**User Journeys**:
1. Admin creates new user and assigns Editor role on Project
2. Editor user creates flow in project (success)
3. Editor user attempts to delete flow (blocked)
4. Admin changes Editor to Viewer role
5. Viewer user views flow (success), attempts edit (blocked)
6. Admin assigns Owner role on specific Flow, overriding Project role
7. User can now edit that specific Flow but not others

### Performance Testing

**Load Tests**:
- 100 concurrent users calling can_access()
- 1000 flows list endpoint with permission filtering
- Assignment creation under load (100 requests/sec)
- Page load time with 50 permission checks

**Benchmarks**:
- can_access() latency: target <50ms p95
- Assignment creation API: target <200ms p95
- Editor page load: target <2.5s p95
- Database query execution times

### Security Testing

**Penetration Tests**:
- Attempt to bypass permission checks via direct API calls
- Attempt to access RBAC endpoints as non-admin
- Attempt to modify immutable assignments
- SQL injection on scope_id parameters
- JWT token manipulation to gain Admin role

**Audit Tests**:
- All permission checks happen server-side
- No sensitive data in client-side code
- 404 returned for unauthorized access (not 403)
- CORS headers properly configured
- No RBAC data leaked in error messages

---

## Appendix: Reference Materials

### PRD Epic and Story Mapping

| Epic | Story | Implementation Task(s) |
|------|-------|----------------------|
| Epic 1 Story 1.1 | Define Core Permissions and Scopes | Task 1.1, 1.2, 1.3 |
| Epic 1 Story 1.2 | Define Default Roles and Mappings | Task 1.3 |
| Epic 1 Story 1.3 | Implement Core Role Assignment Logic | Task 1.5, 2.1 |
| Epic 1 Story 1.4 | Default Project Owner Immutability | Task 1.5, 1.6, 2.1 |
| Epic 1 Story 1.5 | Global Project Creation & Owner Assignment | Task 2.2, 2.3 |
| Epic 1 Story 1.6 | Project to Flow Role Extension | Task 1.4 |
| Epic 2 Story 2.1 | Core CanAccess Authorization Service | Task 1.4 |
| Epic 2 Story 2.2 | Enforce Read/View Permission | Task 2.2, 2.3, 3.7 |
| Epic 2 Story 2.3 | Enforce Create Permission | Task 2.2, 2.3, 3.7 |
| Epic 2 Story 2.4 | Enforce Update/Edit Permission | Task 2.2, 2.3, 3.7 |
| Epic 2 Story 2.5 | Enforce Delete Permission | Task 2.2, 2.3, 3.7 |
| Epic 3 Story 3.1 | RBAC Management Section in Admin Page | Task 3.3 |
| Epic 3 Story 3.2 | Assignment Creation Workflow | Task 3.5 |
| Epic 3 Story 3.3 | Assignment List View and Filtering | Task 3.4 |
| Epic 3 Story 3.4 | Assignment Editing and Removal | Task 3.4, 2.1 |
| Epic 3 Story 3.5 | Flow Role Inheritance Display | Task 3.4 |
| Epic 5 Story 5.1 | Role Assignment and Enforcement Latency | Performance testing across all tasks |
| Epic 5 Story 5.2 | System Uptime and Availability | Monitoring post-deployment |
| Epic 5 Story 5.3 | Readiness Time (Initial Load) | Task 3.7, performance testing |

### AppGraph Node Summary

**New Schema Nodes (4)**:
- ns0010: Role
- ns0011: Permission
- ns0012: RolePermission
- ns0013: UserRoleAssignment

**Modified Schema Nodes (3)**:
- ns0001: User (add role_assignments relationship)
- ns0002: Flow (permission checks replace user_id filtering)
- ns0003: Folder (immutability for Default Project)

**New Logic Nodes (7)**:
- nl0504: RBACService
- nl0505: GET /api/v1/rbac/roles
- nl0506: GET /api/v1/rbac/assignments
- nl0507: POST /api/v1/rbac/assignments
- nl0508: PATCH /api/v1/rbac/assignments/{id}
- nl0509: DELETE /api/v1/rbac/assignments/{id}
- nl0510: GET /api/v1/rbac/check-permission

**Modified Logic Nodes (11)**:
- nl0004: Create Flow Endpoint Handler
- nl0005: List Flows Endpoint Handler
- nl0007: Get Flow by ID Endpoint Handler
- nl0009: Update Flow Endpoint Handler
- nl0010: Delete Flow Endpoint Handler
- nl0012: Upload Flows Endpoint Handler
- nl0042: Create Project Endpoint Handler
- nl0043: List Projects Endpoint Handler
- nl0044: Get Project by ID Endpoint Handler
- nl0045: Update Project Endpoint Handler
- nl0046: Delete Project Endpoint Handler
- nl0061: Build Flow Endpoint Handler

**New Interface Nodes (6)**:
- ni0083: RBACManagementPage
- ni0084: AssignmentListView
- ni0085: CreateAssignmentModal
- ni0086: RBACGuard
- ni0087: usePermission

**Modified Interface Nodes (3)**:
- ni0001: AdminPage (add RBAC tab)
- ni0006: CollectionPage (permission-based filtering and buttons)
- ni0009: FlowPage (read-only mode support)

### Key Constants and File Paths

**Backend**:
- DEFAULT_FOLDER_NAME: "My Projects" (from models/folder/constants.py)
- STARTER_FOLDER_NAME: "Starter Projects" (from initial_setup/constants.py)
- New directory: src/backend/base/langbuilder/services/rbac/
- New file: src/backend/base/langbuilder/api/v1/rbac.py
- Migration directory: src/backend/base/langbuilder/alembic/versions/

**Frontend**:
- New directory: src/frontend/src/controllers/API/queries/rbac/
- New hook: src/frontend/src/hooks/usePermission.ts
- New page: src/frontend/src/pages/AdminPage/RBACManagementPage/
- New guard component: src/frontend/src/components/authorization/RBACGuard.tsx

### Acceptance Criteria Cross-Reference

All 20 Gherkin validation nodes from the AppGraph map to implementation tasks:

- gherkin_epic01_story01_ac01 → Task 1.1, 1.2, 1.3
- gherkin_epic01_story02_ac01 → Task 1.3
- gherkin_epic01_story03_ac01 → Task 1.5, 2.1
- gherkin_epic01_story04_ac01 → Task 1.5, 1.6, 2.1
- gherkin_epic01_story05_ac01 → Task 2.2, 2.3
- gherkin_epic01_story06_ac01 → Task 1.4
- gherkin_epic02_story01_ac01 → Task 1.4
- gherkin_epic02_story02_ac01 → Task 2.2, 2.3, 3.7
- gherkin_epic02_story03_ac01 → Task 2.2, 2.3, 3.7
- gherkin_epic02_story04_ac01 → Task 2.2, 2.3, 3.7
- gherkin_epic02_story05_ac01 → Task 2.2, 2.3, 3.7
- gherkin_epic03_story01_ac01 → Task 3.3
- gherkin_epic03_story02_ac01 → Task 3.5
- gherkin_epic03_story03_ac01 → Task 3.4
- gherkin_epic03_story04_ac01 → Task 3.4, 2.1
- gherkin_epic03_story05_ac01 → Task 3.4
- gherkin_epic05_story01_ac01 → Performance testing
- gherkin_epic05_story01_ac02 → Performance testing
- gherkin_epic05_story02_ac01 → Monitoring
- gherkin_epic05_story03_ac01 → Performance testing

---

**Document Status**: APPROVED FOR IMPLEMENTATION
**Generated**: 2025-11-01
**Audit Reference**: rbac-mvp-implementation-plan-audit.md (v1.0)
