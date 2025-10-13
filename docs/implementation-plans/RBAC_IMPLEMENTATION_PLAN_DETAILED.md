# Granular Access Control & RBAC Implementation Plan

## Overview

This document provides a comprehensive, phased implementation plan for adding enterprise-grade Role-Based Access Control (RBAC) to LangBuilder. The implementation follows the PRD requirements documented in `docs/PRD _ Granular Access Control & RBAC – LangBuilder.md` and is guided by the AppGraph v7_1 (`docs/langbuilder_app_graph_v7_1_complete_implementation.json`) which contains detailed nodes, edges, and implementation specifications.

**What We're Implementing:**
- Fine-grained permission system (CRUD + 12 extended permissions)
- Custom role management with hierarchical scope system
- SSO/SCIM integration for enterprise identity management
- Service accounts with scoped API tokens
- Comprehensive audit logging for compliance
- Admin UI and REST API for RBAC management
- Infrastructure-as-Code (YAML/Terraform) support

**Why This Matters:**
Current LangBuilder has only binary permissions (superuser vs regular user). Enterprise customers need:
- Multi-tenant workspace isolation
- Team collaboration with least-privilege access
- Compliance-ready audit trails
- Integration with corporate identity providers
- Automated user provisioning/deprovisioning

## Current State Analysis

### What Exists Now

**Authentication System (src/backend/base/langflow/services/auth/utils.py)**
- JWT-based authentication with OAuth2 password flow
- API key authentication (header/query param)
- Auto-login mode for development
- **LIMITATION**: No authorization beyond `is_superuser` flag

**Database Models (src/backend/base/langflow/services/database/models/)**
- **User**: Basic fields (id, username, password_hash, is_superuser, is_active)
- **Folder**: Projects with hierarchical structure, unused `auth_settings` JSON field
- **Flow**: Workflows with binary access_type (PRIVATE/PUBLIC)
- **ApiKey**: User-scoped tokens, no resource or permission scoping
- **Variable**: Global variables per user, no project scoping

**API Endpoints (src/backend/base/langflow/api/v1/)**
- Login/logout, user CRUD, project CRUD, flow CRUD
- Basic authorization: `user_id == resource.user_id OR is_superuser`
- No RBAC endpoints

**Frontend (src/frontend/src/)**
- Auth context with JWT tokens
- Binary `isAdmin` flag for UI element visibility
- No permission-aware components

### What's Missing

**Critical Gaps:**
1. **No Permission System**: Cannot define or check granular permissions
2. **No Multi-Tenancy**: Users can only access their own resources or everything (if superuser)
3. **No Scope Hierarchy**: Missing Workspace, Environment concepts from PRD
4. **No Audit Logging**: No immutable trail of access decisions or RBAC changes
5. **No SSO/SCIM**: Cannot integrate with corporate identity providers
6. **No Service Accounts**: Cannot scope programmatic access to specific resources

**Database Models Needed:**
- Role, Permission, RolePermission, RoleAssignment
- ServiceAccount, AuditLog, SSOIntegration
- Workspace (new concept), Environment (new concept)

**Services Needed:**
- RBAC Enforcement Engine with permission evaluation
- Scope Resolver for hierarchical permission inheritance
- SSO Handler (SAML 2.0, OIDC)
- SCIM Provisioning Service
- Audit Logger with async writes

###Key Discoveries

1. **Folder.auth_settings field exists but unused** (src/backend/base/langflow/services/database/models/folder/model.py:14-18)
   - Can be leveraged for project-level RBAC configuration
   - Avoids breaking schema changes

2. **Flow.access_type binary flag insufficient** (src/backend/base/langflow/services/database/models/flow/model.py)
   - Need to replace with RBAC permission checks
   - Must maintain backward compatibility during migration

3. **ApiKey model lacks scope fields** (src/backend/base/langflow/services/database/models/api_key/model.py)
   - Need to add: scope_type, scope_id, scoped_permissions, workspace_id
   - Enables PRD Story 4.2 (Token Scope Enforcement)

4. **Component-level permissions challenging** (PRD Story 2.1 @AC7)
   - Components embedded in Flow.data JSON, not separate DB entities
   - **Decision**: Use flow-level permissions + component_id filtering in enforcement logic

5. **Environment concept missing entirely**
   - PRD defines Workspace > Project > Environment > Flow > Component hierarchy
   - Need to add Environment model or map to existing concepts

## Desired End State

### Specification

**Permission Model:**
- Permission catalog with 13 base permissions (CRUD + export_flow, deploy_environment, invite_users, modify_component_settings, manage_tokens, manage_roles, manage_users, view_audit, manage_settings)
- Permission evaluation: ≤100ms p95 (≤10ms cached)
- Deny-by-default with explicit deny precedence

**Scope Hierarchy:**
```
Workspace (top-level org unit)
  └── Project (Folder model renamed conceptually)
      └── Environment (dev, staging, prod)
          └── Flow (workflow)
              └── Component (nodes in flow)
```

**Role System:**
- System roles: Owner, Admin, Editor, Viewer, ServiceAccount
- Custom roles with permission composition
- Role versioning and audit trail

**Identity & Access:**
- SSO via SAML 2.0 / OIDC
- SCIM 2.0 automated provisioning
- Service accounts with scoped tokens
- API keys with resource/permission scoping

**Audit & Compliance:**
- Immutable audit log (every RBAC decision and configuration change)
- Exportable compliance reports (CSV/JSON)
- GDPR/CCPA data minimization
- SOC 2 / ISO 27001 controls

**Management Interfaces:**
- Admin UI for role/permission/grant management
- REST API for programmatic RBAC
- YAML/Terraform IaC support

### Verification Criteria

Implementation complete when:
1. ✅ All PRD user stories pass Gherkin acceptance criteria tests
2. ✅ Permission evaluation meets performance NFRs (≤100ms p95)
3. ✅ Zero regression in existing user-owned resource access
4. ✅ SSO login works with at least one IdP (Okta/Auth0)
5. ✅ SCIM sync creates/updates/deletes users correctly
6. ✅ Audit log captures all RBAC events immutably
7. ✅ Admin UI allows role creation and assignment
8. ✅ API documentation (OpenAPI) includes all RBAC endpoints
9. ✅ Unit test coverage ≥85% for new RBAC code
10. ✅ Integration tests validate end-to-end permission flows

## What We're NOT Doing

**Explicitly Out of Scope:**

1. **Fine-grained component permissions** - We will implement flow-level permissions only. Component-level filtering can be added in Phase 7 if needed.

2. **Single Logout (SLO)** - SSO login only. SLO marked as optional in PRD @AC10 and crossed out.

3. **OPA/Rego policy engine** - Using custom Python evaluation engine. OPA integration is extensibility feature (NFR 5.7) for future.

4. **Time-boxed grants** - Optional feature (Story 3.4 @AC3). Can be added later.

5. **Break-glass emergency access** - Compliance feature (Story 2.2 @AC11) deferred to Phase 6.

6. **SIEM/SOC webhook integration** - Extensibility feature (NFR 5.7) deferred.

7. **Migration of existing user-owned resources to workspace model** - Existing users retain access via implicit Owner role. Full migration is data migration task, not RBAC implementation.

8. **UI redesign** - RBAC UI added to existing AdminPage, no redesign of other pages.

## Implementation Approach

**Strategy: Incremental, Backwards-Compatible Rollout**

We will build RBAC in parallel with existing authorization, allowing gradual migration:

1. **Phase 1**: Database foundation - Add RBAC models without touching existing auth
2. **Phase 2**: Permission evaluation engine - Callable but not enforced
3. **Phase 3**: API layer - RBAC endpoints + middleware (opt-in per endpoint)
4. **Phase 4**: Enforcement - Gradually replace `is_superuser` checks with RBAC
5. **Phase 5**: Identity integration - SSO/SCIM for new users
6. **Phase 6**: Audit & compliance - Immutable logging and reporting
7. **Phase 7**: IaC & advanced features - YAML/Terraform, advanced scope rules

**Key Principles:**
- **No breaking changes**: Existing users/flows/tokens continue working
- **Feature flags**: RBAC features gated behind `LANGFLOW_ENABLE_RBAC` env var initially
- **Test-driven**: Write tests before implementation for each story
- **Incremental deployment**: Each phase deployable independently
- **Performance focus**: Caching strategy from day 1

## Implementation Phases

### Phase 1: Database Foundation & Core Models

**Description:** Establish the database schema for RBAC without modifying existing authentication flows. This phase creates all new models and relationships, generates Alembic migrations, and seeds system roles and permissions.

**Scope:**
- New database models: Role, Permission, RolePermission, RoleAssignment, ServiceAccount, AuditLog, SSOIntegration
- Modified models: User (add relationships), ApiKey (add scope fields), Folder (leverage auth_settings)
- Alembic migrations with backward compatibility
- System data seeding (system roles and permission catalog)

**Goals:**
- RBAC tables exist in database
- Backward compatibility: no impact on existing auth flows
- System roles and permissions seeded on first run
- Ready for permission evaluation logic in Phase 2

#### Task 1.1: Define RBAC Database Models

**Scope & Goals:**
Create SQLModel definitions for all RBAC entities following codebase patterns.

**Impact Subgraph from AppGraph:**
```
Schema Nodes (NEW):
- role_entity → Defines customizable roles with hierarchy
- permission_entity → Granular permission catalog
- role_permission_entity → Junction table linking roles to permissions
- role_assignment_entity → Assigns roles to users/service accounts at scopes
- service_account_entity → Non-human identities for programmatic access
- audit_log_entity → Immutable audit trail
- sso_integration_entity → SSO provider configuration

Schema Nodes (MODIFIED):
- api_key_entity → Add scope_type, scope_id, scoped_permissions, workspace_id, service_account_id
- user_entity → Add role_assignments relationship
- folder_entity → Leverage auth_settings for project-level RBAC config

Edges:
- role_entity → role_permission_entity (has_permissions)
- role_entity → role_assignment_entity (assigned_to)
- permission_entity → role_permission_entity (granted_in)
- user_entity → role_assignment_entity (has_role_assignments)
- service_account_entity → role_assignment_entity (has_role_assignments)
- service_account_entity → api_key_entity (has_tokens)
- audit_log_entity → user_entity (logged_by)
```

**Architecture & Tech Stack:**
- **ORM**: SQLModel (Pydantic + SQLAlchemy) with async support
- **Database**: PostgreSQL (production), SQLite (dev)
- **Migration Tool**: Alembic
- **Validation**: Pydantic v2
- **Pattern**: Follow existing models in `src/backend/base/langflow/services/database/models/`

**Success Criteria:**
- [ ] All 7 new models defined with proper types and relationships
- [ ] Modified models (User, ApiKey, Folder) updated with new fields
- [ ] All relationships defined with proper back_populates
- [ ] Pydantic validators for business rules (e.g., system roles immutable)
- [ ] Models pass type checking (`make lint`)
- [ ] No circular import dependencies

**Implementation Files:**
```
src/backend/base/langflow/services/database/models/rbac/
├── __init__.py
├── role.py              # Role, RoleRead, RoleCreate, RoleUpdate
├── permission.py        # Permission, PermissionRead, PermissionCreate
├── role_permission.py   # RolePermission junction table
├── role_assignment.py   # RoleAssignment with scope constraints
├── service_account.py   # ServiceAccount model
├── audit_log.py         # AuditLog immutable model
└── sso_integration.py   # SSOIntegration for SSO/SCIM config
```

**Modified Files:**
```
src/backend/base/langflow/services/database/models/user/model.py
src/backend/base/langflow/services/database/models/api_key/model.py
src/backend/base/langflow/services/database/models/folder/model.py
```

#### Task 1.2: Create Alembic Database Migrations

**Scope & Goals:**
Generate and test Alembic migrations for RBAC schema changes.

**Impact Subgraph from AppGraph:**
```
Logic Nodes:
- database_migration_logic → Handles schema evolution
- backward_compatibility_checker → Ensures no breaking changes

Edges:
- database_migration_logic → role_entity (creates_table)
- database_migration_logic → permission_entity (creates_table)
- database_migration_logic → role_permission_entity (creates_table)
- database_migration_logic → role_assignment_entity (creates_table)
- database_migration_logic → service_account_entity (creates_table)
- database_migration_logic → audit_log_entity (creates_table)
- database_migration_logic → sso_integration_entity (creates_table)
- database_migration_logic → api_key_entity (alters_table)
- database_migration_logic → user_entity (alters_table)
```

**Architecture & Tech Stack:**
- **Migration Tool**: Alembic
- **Pattern**: Auto-generate then manually review
- **Command**: `cd src/backend/base/langflow && alembic revision --autogenerate -m "Add RBAC models"`
- **Constraints**: Must work with both PostgreSQL and SQLite

**Success Criteria:**
- [ ] Migration generates all new tables with indexes
- [ ] Foreign key constraints properly defined
- [ ] Unique constraints on composite keys (e.g., role_id + permission_id)
- [ ] Nullable fields correct (e.g., RoleAssignment.user_id nullable for service accounts)
- [ ] Migration reversible (`alembic downgrade` works)
- [ ] Migration tested on fresh database and existing database
- [ ] No data loss on existing tables

**Implementation Files:**
```
src/backend/base/langflow/alembic/versions/XXXX_add_rbac_models.py
```

**Testing:**
```bash
# Fresh database
rm langflow.db
alembic upgrade head
# Verify all tables created

# Existing database
cp langflow.db langflow.db.backup
alembic upgrade head
# Verify existing data intact

# Rollback
alembic downgrade -1
# Verify clean rollback
```

#### Task 1.3: Seed System Roles and Permissions

**Scope & Goals:**
Create initialization logic to populate permission catalog and system roles on first run.

**Impact Subgraph from AppGraph:**
```
Logic Nodes:
- system_initialization_flow → Runs on app startup
- permission_catalog_seeder → Populates permission table
- system_role_seeder → Creates Owner, Admin, Editor, Viewer, ServiceAccount roles

Edges:
- system_initialization_flow → permission_catalog_seeder (executes)
- system_initialization_flow → system_role_seeder (executes)
- permission_catalog_seeder → permission_entity (creates_records)
- system_role_seeder → role_entity (creates_records)
- system_role_seeder → role_permission_entity (creates_records)
```

**Architecture & Tech Stack:**
- **Pattern**: Startup script in `main.py` or dedicated `initialization.py`
- **Idempotency**: Check if seeding already done (e.g., SELECT COUNT(*) FROM permission)
- **Data**: Define permissions and roles in Python constants or YAML config

**Permission Catalog (PRD Story 1.1):**
```python
PERMISSIONS = [
    # CRUD operations
    ("flow.create", "Create Flow", "FLOW", "CREATE", "PROJECT"),
    ("flow.read", "Read Flow", "FLOW", "READ", "FLOW"),
    ("flow.update", "Update Flow", "FLOW", "UPDATE", "FLOW"),
    ("flow.delete", "Delete Flow", "FLOW", "DELETE", "FLOW"),
    ("flow.execute", "Execute Flow", "FLOW", "EXECUTE", "FLOW"),

    # Extended permissions
    ("flow.export", "Export Flow", "FLOW", "EXPORT", "FLOW"),
    ("environment.deploy", "Deploy to Environment", "ENVIRONMENT", "DEPLOY", "ENVIRONMENT"),
    ("workspace.invite_users", "Invite Users", "WORKSPACE", "INVITE", "WORKSPACE"),
    ("component.modify_settings", "Modify Component Settings", "COMPONENT", "UPDATE", "COMPONENT"),
    ("api_token.manage", "Manage API Tokens", "API_TOKEN", "MANAGE_TOKENS", "PROJECT"),
    ("role.manage", "Manage Roles", "ROLE", "MANAGE_ROLES", "WORKSPACE"),
    ("user.manage", "Manage Users", "USER", "MANAGE_USERS", "WORKSPACE"),
    ("audit.view", "View Audit Logs", "SYSTEM", "VIEW_AUDIT", "WORKSPACE"),
    # ... (full catalog from PRD)
]
```

**System Roles (PRD Story 1.2):**
```python
SYSTEM_ROLES = {
    "owner": {
        "display_name": "Owner",
        "description": "Full access to all resources in scope",
        "permissions": ["*"],  # All permissions
    },
    "admin": {
        "display_name": "Admin",
        "description": "Manage users, roles, and settings",
        "permissions": ["*.read", "*.update", "user.manage", "role.manage", "audit.view"],
    },
    "editor": {
        "display_name": "Editor",
        "description": "Create and edit flows, deploy to environments",
        "permissions": ["flow.*", "component.*", "environment.deploy"],
    },
    "viewer": {
        "display_name": "Viewer",
        "description": "Read-only access to flows and components",
        "permissions": ["flow.read", "component.read"],
    },
    "service_account": {
        "display_name": "Service Account",
        "description": "Programmatic access with token-scoped permissions",
        "permissions": [],  # Permissions assigned per service account
    },
}
```

**Success Criteria:**
- [ ] Permission catalog seeded with all 13+ base permissions
- [ ] 5 system roles created with correct permission assignments
- [ ] Seeding is idempotent (can run multiple times safely)
- [ ] Seeding runs automatically on first app startup
- [ ] System roles marked as `is_system_role=True` (immutable)
- [ ] Logging indicates successful seeding

**Implementation Files:**
```
src/backend/base/langflow/services/rbac/
├── __init__.py
├── initialization.py    # Seeding logic
└── constants.py         # Permission and role definitions
```

**Modified Files:**
```
src/backend/base/langflow/main.py  # Add startup event handler
```

#### Task 1.4: Write Unit Tests for RBAC Models

**Scope & Goals:**
Comprehensive unit tests for model validation, relationships, and constraints.

**Impact Subgraph from AppGraph:**
```
Test Nodes (NEW):
- test_role_model → Validates Role model
- test_permission_model → Validates Permission model
- test_role_permission_model → Validates junction table
- test_role_assignment_model → Validates assignments with scopes
- test_service_account_model → Validates service account model
- test_audit_log_model → Validates immutable audit log
- test_sso_integration_model → Validates SSO config model

Edges:
- test_role_model → role_entity (tests)
- test_permission_model → permission_entity (tests)
- test_role_permission_model → role_permission_entity (tests)
- test_role_assignment_model → role_assignment_entity (tests)
- test_service_account_model → service_account_entity (tests)
```

**Architecture & Tech Stack:**
- **Framework**: pytest with pytest-asyncio
- **Pattern**: Follow `src/backend/tests/base.py` patterns
- **Fixtures**: Use `client` fixture for async database session
- **Coverage Target**: ≥90% for new models

**Success Criteria:**
- [ ] Test model creation with valid data
- [ ] Test validation errors (e.g., duplicate role names)
- [ ] Test relationships (e.g., role.permissions works)
- [ ] Test unique constraints (e.g., cannot duplicate role-permission pair)
- [ ] Test cascade deletes (e.g., deleting role deletes assignments)
- [ ] Test system role immutability (cannot update/delete system roles)
- [ ] All tests pass: `make unit_tests`
- [ ] Test coverage ≥90%: `make coverage`

**Implementation Files:**
```
src/backend/tests/unit/services/database/models/rbac/
├── test_role.py
├── test_permission.py
├── test_role_permission.py
├── test_role_assignment.py
├── test_service_account.py
├── test_audit_log.py
└── test_sso_integration.py
```

---

### Phase 2: Permission Evaluation Engine

**Description:** Build the core RBAC enforcement engine that evaluates whether a user/service account has permission to perform an action on a resource. This phase implements scope resolution, permission inheritance, caching, and performance optimization.

**Scope:**
- Permission evaluation engine with deny-by-default logic
- Scope hierarchy resolver (Workspace > Project > Environment > Flow > Component)
- Permission caching with invalidation
- Performance testing (NFR: ≤100ms p95, ≤10ms cached)

**Goals:**
- Callable permission check API: `has_permission(user, action, resource, scope)`
- Scope inheritance working (workspace grant flows to project/flow)
- Cache hits achieve ≤10ms latency
- Uncached checks achieve ≤100ms p95 latency
- Ready for integration into API endpoints in Phase 3

#### Task 2.1: Implement Permission Evaluation Engine

**Scope & Goals:**
Core logic to evaluate effective permissions considering user roles, group memberships, scope hierarchy, and deny-by-default rules.

**Impact Subgraph from AppGraph:**
```
Logic Nodes (NEW):
- rbac_enforcement_engine → Core permission evaluation
- scope_resolver → Resolves hierarchical scope inheritance
- permission_cache_manager → In-memory permission cache
- deny_by_default_enforcer → Deny-by-default logic

Edges:
- rbac_enforcement_engine → scope_resolver (uses)
- rbac_enforcement_engine → permission_cache_manager (checks_cache)
- rbac_enforcement_engine → role_assignment_entity (queries)
- rbac_enforcement_engine → role_permission_entity (queries)
- scope_resolver → workspace_entity (traverses)
- scope_resolver → project_entity (traverses)
- scope_resolver → flow_entity (traverses)
```

**Architecture & Tech Stack:**
- **Language**: Python async
- **Cache**: Python `lru_cache` or `cachetools` (Redis optional for multi-instance)
- **Database**: Async SQLAlchemy queries
- **Performance**: Batch queries, eager loading, query optimization

**Permission Evaluation Algorithm (PRD Story 2.1 @AC3-AC9):**
```python
async def has_permission(
    user_id: UUID,
    action: str,  # e.g., "flow.read"
    resource_type: str,  # e.g., "flow"
    resource_id: UUID,
    scope_type: str = "flow",  # e.g., "workspace", "project", "flow"
) -> tuple[bool, str]:  # (allowed, reason)
    """
    Evaluate permission with scope hierarchy and caching.

    Returns (True, "allowed") or (False, "denied:<reason>")
    """
    # 1. Check cache
    cache_key = (user_id, action, resource_type, resource_id)
    if cached := await cache_get(cache_key):
        return cached

    # 2. Get user's role assignments at this scope and ancestor scopes
    assignments = await get_effective_assignments(user_id, resource_id, scope_type)

    # 3. For each assignment, check if role grants the permission
    for assignment in assignments:
        role_permissions = await get_role_permissions(assignment.role_id)

        for role_perm in role_permissions:
            if matches_permission(role_perm, action, resource_type):
                if role_perm.granted:
                    # Allow
                    result = (True, "allowed")
                    await cache_set(cache_key, result, ttl=300)
                    return result
                else:
                    # Explicit deny
                    result = (False, f"denied:explicit_deny:{role_perm.id}")
                    await cache_set(cache_key, result, ttl=300)
                    return result

    # 4. Deny by default
    result = (False, "denied:no_matching_grant")
    await cache_set(cache_key, result, ttl=300)
    return result
```

**Scope Resolution Algorithm (PRD Story 2.1 @AC3, @AC4, @AC5):**
```python
async def get_effective_assignments(
    user_id: UUID,
    resource_id: UUID,
    scope_type: str
) -> list[RoleAssignment]:
    """
    Get user's role assignments at this scope and all ancestor scopes.

    Scope hierarchy: Workspace > Project > Environment > Flow > Component

    Example: If checking flow permission, also check project and workspace.
    """
    # 1. Get resource's scope hierarchy
    scope_chain = await resolve_scope_chain(resource_id, scope_type)
    # Example: [
    #   (workspace_id, "workspace"),
    #   (project_id, "project"),
    #   (flow_id, "flow")
    # ]

    # 2. Query assignments at all scope levels
    assignments = []
    for scope_id, scope_level in scope_chain:
        scope_assignments = await db.execute(
            select(RoleAssignment)
            .where(
                RoleAssignment.user_id == user_id,
                RoleAssignment.scope_type == scope_level,
                RoleAssignment.scope_id == scope_id,
                RoleAssignment.is_active == True,
                RoleAssignment.valid_until > datetime.utcnow()  # Not expired
            )
        )
        assignments.extend(scope_assignments)

    # 3. Order by specificity (flow > project > workspace)
    # Closest scope wins (PRD @AC5)
    assignments.sort(key=lambda a: scope_chain.index((a.scope_id, a.scope_type)))

    return assignments
```

**Success Criteria:**
- [ ] `has_permission()` returns correct bool for granted/denied cases
- [ ] Scope inheritance works (workspace grant flows to flow)
- [ ] Closest scope wins (flow grant overrides workspace grant)
- [ ] Explicit deny takes precedence over allow
- [ ] Deny-by-default works (no grant = denied)
- [ ] Expired assignments ignored (valid_until check)
- [ ] Service account permissions evaluated correctly
- [ ] Unit tests cover all logic branches

**Implementation Files:**
```
src/backend/base/langflow/services/rbac/
├── enforcer.py          # Permission evaluation engine
├── scope_resolver.py    # Scope hierarchy resolution
└── cache.py             # Permission cache manager
```

#### Task 2.2: Implement Permission Caching

**Scope & Goals:**
In-memory caching with TTL and invalidation to meet performance NFRs.

**Impact Subgraph from AppGraph:**
```
Logic Nodes:
- permission_cache_manager → Manages permission cache
- cache_invalidator → Invalidates cache on role/assignment changes

Edges:
- permission_cache_manager → rbac_enforcement_engine (serves_cache_to)
- cache_invalidator → permission_cache_manager (invalidates)
- role_assignment_change_event → cache_invalidator (triggers)
- role_permission_change_event → cache_invalidator (triggers)
```

**Architecture & Tech Stack:**
- **Cache Implementation**: `cachetools.TTLCache` (thread-safe, TTL support)
- **Optional**: Redis for multi-instance deployments
- **Invalidation Strategy**: Event-based (on role/assignment changes)
- **TTL**: 5 minutes default (configurable)

**Cache Key Design:**
```python
cache_key = (
    user_id: UUID,
    action: str,
    resource_type: str,
    resource_id: UUID
)
# Example: (uuid-123, "flow.read", "flow", uuid-456)
```

**Invalidation Strategy:**
```python
# Invalidate entire user cache on:
# - User role assignment changed
# - User's role permissions changed
# - User's group membership changed

async def invalidate_user_cache(user_id: UUID):
    """Remove all cached permissions for user."""
    cache.clear_pattern(f"perm:{user_id}:*")

# Register event listeners
@event_listener("role_assignment_created")
@event_listener("role_assignment_revoked")
async def on_role_assignment_change(assignment: RoleAssignment):
    await invalidate_user_cache(assignment.user_id)

@event_listener("role_permission_updated")
async def on_role_permission_change(role_id: UUID):
    # Invalidate all users with this role
    users = await get_users_with_role(role_id)
    for user in users:
        await invalidate_user_cache(user.id)
```

**Success Criteria:**
- [ ] Cache hits return in ≤10ms (p95)
- [ ] Cache miss falls back to database correctly
- [ ] Cache invalidation works on role/assignment changes
- [ ] TTL expiration works (5 min default)
- [ ] Cache size bounded (LRU eviction)
- [ ] Performance tests validate NFRs

**Implementation Files:**
```
src/backend/base/langflow/services/rbac/cache.py
```

#### Task 2.3: Performance Testing and Optimization

**Scope & Goals:**
Validate permission evaluation meets NFR performance requirements (≤100ms p95 uncached, ≤10ms cached).

**Impact Subgraph from AppGraph:**
```
Test Nodes:
- test_permission_evaluation_performance → Validates latency
- test_cache_hit_performance → Validates cache speed
- test_scope_resolution_performance → Validates hierarchy traversal

Edges:
- test_permission_evaluation_performance → rbac_enforcement_engine (tests)
- test_cache_hit_performance → permission_cache_manager (tests)
- test_scope_resolution_performance → scope_resolver (tests)
```

**Architecture & Tech Stack:**
- **Tool**: `pytest-benchmark` for microbenchmarks
- **Tool**: Locust for load testing
- **Profiling**: `cProfile` for bottleneck identification
- **Optimization**: Query optimization, eager loading, batch queries

**Performance Test Scenarios:**
```python
@pytest.mark.benchmark
async def test_permission_check_uncached(benchmark):
    """Permission check from database (cold cache)."""
    result = await benchmark(
        has_permission,
        user_id=test_user_id,
        action="flow.read",
        resource_type="flow",
        resource_id=test_flow_id
    )
    assert benchmark.stats.max < 0.100  # ≤100ms

@pytest.mark.benchmark
async def test_permission_check_cached(benchmark):
    """Permission check from cache (warm cache)."""
    # Prime cache
    await has_permission(test_user_id, "flow.read", "flow", test_flow_id)

    result = await benchmark(
        has_permission,
        user_id=test_user_id,
        action="flow.read",
        resource_type="flow",
        resource_id=test_flow_id
    )
    assert benchmark.stats.max < 0.010  # ≤10ms
```

**Optimization Checklist:**
- [ ] Batch role assignment queries (single query for all scopes)
- [ ] Eager load relationships (role.permissions)
- [ ] Database indexes on foreign keys (user_id, role_id, scope_id)
- [ ] Use `selectinload` for N+1 query prevention
- [ ] Compile regex patterns once for permission matching
- [ ] Use database query planner to optimize queries

**Success Criteria:**
- [ ] Uncached permission check ≤100ms p95
- [ ] Cached permission check ≤10ms p95
- [ ] Benchmark tests pass consistently
- [ ] Load test (1000 concurrent users) maintains latency
- [ ] Profiling shows no obvious bottlenecks

**Implementation Files:**
```
src/backend/tests/unit/services/rbac/
├── test_enforcer_performance.py
└── test_cache_performance.py
```

#### Task 2.4: Write Integration Tests for Permission Evaluation

**Scope & Goals:**
End-to-end tests validating permission evaluation with real database.

**Impact Subgraph from AppGraph:**
```
Test Nodes:
- test_permission_evaluation_integration → End-to-end permission tests
- test_scope_inheritance_integration → Tests hierarchical permissions
- test_deny_by_default_integration → Tests default deny

Edges:
- test_permission_evaluation_integration → rbac_enforcement_engine (tests)
- test_permission_evaluation_integration → database (uses)
```

**Architecture & Tech Stack:**
- **Framework**: pytest with async database fixtures
- **Database**: In-memory SQLite for tests
- **Pattern**: Arrange-Act-Assert with realistic scenarios

**Test Scenarios (PRD Acceptance Criteria):**

**Story 1.1 @AC3: Export flow requires export_flow permission**
```python
async def test_export_flow_permission(client, db_session):
    # Arrange
    user_jo = await create_user("jo@test.com")
    flow_f123 = await create_flow("F123")
    role = await create_role("exporter", ["flow.export"])
    await assign_role(user_jo, role, scope_type="flow", scope_id=flow_f123.id)

    # Act & Assert: Allowed with permission
    allowed, reason = await has_permission(user_jo.id, "flow.export", "flow", flow_f123.id)
    assert allowed == True

    # Act & Assert: Denied without permission on different flow
    flow_f124 = await create_flow("F124")
    allowed, reason = await has_permission(user_jo.id, "flow.export", "flow", flow_f124.id)
    assert allowed == False
    assert "no_matching_grant" in reason
```

**Story 2.1 @AC4: Higher-scope grants cascade to lower scopes**
```python
async def test_workspace_grant_cascades_to_flow(client, db_session):
    # Arrange
    workspace = await create_workspace("WB1")
    project = await create_project("PRJ1", workspace_id=workspace.id)
    flow = await create_flow("Flow1", project_id=project.id)
    user_mia = await create_user("mia@test.com")
    role_editor = await get_role("editor")  # Has flow.update
    await assign_role(user_mia, role_editor, scope_type="workspace", scope_id=workspace.id)

    # Act
    allowed, reason = await has_permission(user_mia.id, "flow.update", "flow", flow.id)

    # Assert: Workspace grant allows flow edit
    assert allowed == True
    assert reason == "allowed"
```

**Story 2.1 @AC5: Closest scope wins**
```python
async def test_closest_scope_overrides(client, db_session):
    # Arrange
    workspace = await create_workspace("WB1")
    project = await create_project("PRJ2", workspace_id=workspace.id)
    flow = await create_flow("Flow1", project_id=project.id)
    user_lee = await create_user("lee@test.com")

    viewer_role = await get_role("viewer")  # Only flow.read
    editor_role = await get_role("editor")  # flow.read + flow.update

    await assign_role(user_lee, viewer_role, scope_type="workspace", scope_id=workspace.id)
    await assign_role(user_lee, editor_role, scope_type="project", scope_id=project.id)

    # Act
    allowed, reason = await has_permission(user_lee.id, "flow.update", "flow", flow.id)

    # Assert: Project-level editor grant overrides workspace viewer
    assert allowed == True
```

**Story 4.1 @AC1: Deny by default**
```python
async def test_deny_by_default(client, db_session):
    # Arrange
    user_kai = await create_user("kai@test.com")
    project_prj1 = await create_project("PRJ1")
    flow = await create_flow("Flow1", project_id=project_prj1.id)
    # Note: No role assigned to kai

    # Act
    allowed, reason = await has_permission(user_kai.id, "flow.read", "flow", flow.id)

    # Assert: Denied without any role
    assert allowed == False
    assert "no_matching_grant" in reason
```

**Success Criteria:**
- [ ] All PRD Story 1.1 acceptance criteria pass
- [ ] All PRD Story 2.1 acceptance criteria pass
- [ ] All PRD Story 4.1 acceptance criteria pass
- [ ] Tests cover edge cases (expired grants, inactive roles, null scopes)
- [ ] Integration tests run in CI pipeline
- [ ] Test data fixtures reusable across tests

**Implementation Files:**
```
src/backend/tests/integration/services/rbac/
├── test_permission_evaluation.py
├── test_scope_inheritance.py
├── test_deny_by_default.py
└── fixtures.py  # Reusable test data
```

---

### Phase 3: RBAC REST API & Admin Endpoints

**Description:** Implement REST API endpoints for RBAC management (roles, permissions, grants, groups, service accounts) following FastAPI patterns. This phase makes RBAC configurable via API before enforcing it in existing endpoints.

**Scope:**
- RBAC CRUD endpoints (Story 3.1, 3.2)
- Role assignment endpoints (Story 3.4, 3.5)
- Group management endpoints
- Service account management endpoints
- OpenAPI documentation
- Permission checks on admin endpoints (admin-only access)

**Goals:**
- All RBAC entities manageable via REST API
- API follows existing FastAPI/Pydantic patterns
- Admin-only access enforced (superuser or role.manage permission)
- OpenAPI docs auto-generated
- Ready for frontend integration in Phase 4

#### Task 3.1: Implement Role Management API

**Scope & Goals:**
CRUD endpoints for role management (Story 3.2 @AC1).

**Impact Subgraph from AppGraph:**
```
Interface Nodes (NEW):
- role_management_api → REST API for roles

Logic Nodes:
- create_role_logic → Creates custom role
- update_role_logic → Updates role (creates new version)
- delete_role_logic → Deletes role (prevents system role deletion)
- list_roles_logic → Lists all roles
- get_role_logic → Gets single role

Edges:
- role_management_api → create_role_logic (invokes)
- role_management_api → update_role_logic (invokes)
- role_management_api → delete_role_logic (invokes)
- role_management_api → list_roles_logic (invokes)
- role_management_api → get_role_logic (invokes)
- create_role_logic → role_entity (creates)
- update_role_logic → role_entity (updates)
- delete_role_logic → role_entity (deletes)
- *_logic → audit_log_entity (logs_to)
```

**Architecture & Tech Stack:**
- **Framework**: FastAPI with async def
- **Validation**: Pydantic schemas (RoleCreate, RoleUpdate, RoleRead)
- **Auth**: Requires `role.manage` permission or `is_superuser`
- **Pattern**: Follow `src/backend/base/langflow/api/v1/users.py` patterns

**API Endpoints (PRD Story 3.2):**
```python
# src/backend/base/langflow/api/v1/rbac/roles.py

@router.get("/api/admin/roles/", response_model=list[RoleRead])
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> list[RoleRead]:
    """List all roles. Requires role.manage permission."""
    # Check permission
    if not current_user.is_superuser:
        allowed, reason = await has_permission(
            current_user.id, "role.manage", "role", None
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Query roles
    result = await db.execute(
        select(Role).offset(skip).limit(limit)
    )
    roles = result.scalars().all()
    return roles

@router.post("/api/admin/roles/", response_model=RoleRead, status_code=201)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> RoleRead:
    """
    Create custom role (PRD Story 3.2 @AC1).

    Validates:
    - Unique role name
    - All permission IDs exist in catalog
    """
    # Check permission
    if not current_user.is_superuser:
        allowed, reason = await has_permission(
            current_user.id, "role.manage", "role", None
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Validate unique name
    existing = await db.execute(
        select(Role).where(Role.name == role_data.name)
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Role name must be unique")

    # Validate permissions exist
    for perm_id in role_data.permission_ids:
        perm = await db.get(Permission, perm_id)
        if not perm:
            raise HTTPException(status_code=400, detail=f"Unknown permission id: {perm_id}")

    # Create role
    role = Role(
        name=role_data.name,
        display_name=role_data.display_name,
        description=role_data.description,
        is_system_role=False,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    db.add(role)
    await db.flush()

    # Add permissions
    for perm_id in role_data.permission_ids:
        role_perm = RolePermission(
            role_id=role.id,
            permission_id=perm_id,
            granted=True,
            granted_by=current_user.id
        )
        db.add(role_perm)

    await db.commit()
    await db.refresh(role)

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="role.created",
        resource_type="role",
        resource_id=role.id,
        details={"name": role.name}
    )

    return role

@router.get("/api/admin/roles/{role_id}", response_model=RoleRead)
async def get_role(
    role_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> RoleRead:
    """Get role by ID."""
    # Check permission (same as list)
    # ...

    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.patch("/api/admin/roles/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> RoleRead:
    """
    Update role and create new version (PRD Story 1.2 @AC3).

    System roles cannot be updated.
    """
    # Check permission
    # ...

    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role.is_system_role:
        raise HTTPException(status_code=403, detail="Cannot modify system roles")

    # Update fields
    if role_data.display_name:
        role.display_name = role_data.display_name
    if role_data.description:
        role.description = role_data.description
    role.updated_by = current_user.id
    role.updated_at = datetime.utcnow()

    # Update permissions if provided
    if role_data.permission_ids is not None:
        # Remove old permissions
        await db.execute(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )
        # Add new permissions
        for perm_id in role_data.permission_ids:
            role_perm = RolePermission(
                role_id=role.id,
                permission_id=perm_id,
                granted=True,
                granted_by=current_user.id
            )
            db.add(role_perm)

    await db.commit()
    await db.refresh(role)

    # Invalidate cache for users with this role
    await invalidate_role_cache(role_id)

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="role.updated",
        resource_type="role",
        resource_id=role.id,
        details={"before": old_state, "after": new_state}
    )

    return role

@router.delete("/api/admin/roles/{role_id}", status_code=204)
async def delete_role(
    role_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Delete role. System roles cannot be deleted.
    """
    # Check permission
    # ...

    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role.is_system_role:
        raise HTTPException(status_code=403, detail="Cannot delete system roles")

    # Check if role is assigned
    assignments = await db.execute(
        select(RoleAssignment).where(RoleAssignment.role_id == role_id)
    )
    if assignments.scalar():
        raise HTTPException(
            status_code=400,
            detail="Cannot delete role with active assignments. Revoke assignments first."
        )

    await db.delete(role)
    await db.commit()

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="role.deleted",
        resource_type="role",
        resource_id=role_id
    )
```

**Pydantic Schemas:**
```python
# src/backend/base/langflow/schema/rbac.py

class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    permission_ids: list[UUID] = Field(default_factory=list)

class RoleUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    permission_ids: list[UUID] | None = None

class RoleRead(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: str | None
    is_system_role: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID

    # Optional: Include permissions
    permissions: list[PermissionRead] = []

    model_config = ConfigDict(from_attributes=True)
```

**Success Criteria:**
- [ ] POST /api/admin/roles/ creates role (PRD @AC1)
- [ ] Duplicate role name returns 400 error (PRD Story 1.2 @AC2)
- [ ] Unknown permission ID returns 400 error (PRD Story 1.1 @AC2)
- [ ] PATCH /api/admin/roles/{id} updates role and logs audit (PRD @AC3)
- [ ] DELETE /api/admin/roles/{id} deletes role
- [ ] Cannot update/delete system roles (403 error)
- [ ] Endpoints require admin permission (403 if insufficient)
- [ ] OpenAPI docs generated correctly

**Implementation Files:**
```
src/backend/base/langflow/api/v1/rbac/
├── __init__.py
└── roles.py

src/backend/base/langflow/schema/
└── rbac.py  # Pydantic schemas
```

#### Task 3.2: Implement Permission Catalog API

**Scope & Goals:**
Read-only endpoint to list available permissions (Story 1.1).

**Impact Subgraph from AppGraph:**
```
Interface Nodes:
- permission_catalog_api → REST API to list permissions

Logic Nodes:
- list_permissions_logic → Lists all available permissions

Edges:
- permission_catalog_api → list_permissions_logic (invokes)
- list_permissions_logic → permission_entity (reads)
```

**API Endpoint:**
```python
# src/backend/base/langflow/api/v1/rbac/permissions.py

@router.get("/api/admin/permissions/", response_model=list[PermissionRead])
async def list_permissions(
    resource_type: str | None = None,
    action: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> list[PermissionRead]:
    """
    List available permissions (PRD Story 1.1 @AC1).

    Query params:
    - resource_type: Filter by resource (e.g., "flow")
    - action: Filter by action (e.g., "read")
    """
    query = select(Permission)

    if resource_type:
        query = query.where(Permission.resource_type == resource_type)
    if action:
        query = query.where(Permission.action == action)

    result = await db.execute(query)
    permissions = result.scalars().all()
    return permissions
```

**Pydantic Schema:**
```python
class PermissionRead(BaseModel):
    id: UUID
    name: str  # e.g., "flow.export"
    display_name: str  # e.g., "Export Flow"
    description: str | None
    resource_type: str  # FLOW, COMPONENT, etc.
    action: str  # CREATE, READ, EXPORT, etc.
    scope_level: str  # GLOBAL, WORKSPACE, PROJECT, FLOW, etc.
    is_system_permission: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

**Success Criteria:**
- [ ] GET /api/admin/permissions/ returns full catalog
- [ ] Filter by resource_type works
- [ ] Filter by action works
- [ ] Response includes all permission metadata
- [ ] Endpoint accessible to all authenticated users (read-only)

**Implementation Files:**
```
src/backend/base/langflow/api/v1/rbac/permissions.py
```

#### Task 3.3: Implement Role Assignment (Grant) API

**Scope & Goals:**
Assign and revoke roles to users/service accounts at specific scopes (Story 3.5).

**Impact Subgraph from AppGraph:**
```
Interface Nodes:
- grant_management_api → REST API for role assignments

Logic Nodes:
- create_grant_logic → Assigns role to principal at scope
- revoke_grant_logic → Removes role assignment
- list_grants_logic → Lists role assignments

Edges:
- grant_management_api → create_grant_logic (invokes)
- grant_management_api → revoke_grant_logic (invokes)
- grant_management_api → list_grants_logic (invokes)
- create_grant_logic → role_assignment_entity (creates)
- revoke_grant_logic → role_assignment_entity (deletes)
- *_grant_logic → audit_log_entity (logs_to)
- *_grant_logic → permission_cache_manager (invalidates_cache)
```

**API Endpoints (PRD Story 3.5):**
```python
# src/backend/base/langflow/api/v1/rbac/grants.py

@router.post("/api/admin/grants/", response_model=GrantRead, status_code=201)
async def create_grant(
    grant_data: GrantCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> GrantRead:
    """
    Assign role to user/service account at scope (PRD Story 3.5 @AC1).

    Example:
    {
        "principal": "user:carol@acme.com",
        "role_id": "uuid-123",
        "scope": {"project": "PRJ1"}
    }
    """
    # Check permission (requires role.manage at scope or higher)
    # ...

    # Parse principal (user:email or service_account:id)
    principal_type, principal_id = parse_principal(grant_data.principal)

    if principal_type == "user":
        user = await get_user_by_email(principal_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        assignee_type = "USER"
        user_id = user.id
        service_account_id = None
    elif principal_type == "service_account":
        sa = await db.get(ServiceAccount, UUID(principal_id))
        if not sa:
            raise HTTPException(status_code=404, detail="Service account not found")
        assignee_type = "SERVICE_ACCOUNT"
        user_id = None
        service_account_id = sa.id
    else:
        raise HTTPException(status_code=400, detail="Invalid principal format")

    # Validate role exists
    role = await db.get(Role, grant_data.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Parse scope (e.g., {"project": "PRJ1"})
    scope_type, scope_id = parse_scope(grant_data.scope)

    # Check for duplicate grant
    existing = await db.execute(
        select(RoleAssignment).where(
            RoleAssignment.role_id == grant_data.role_id,
            RoleAssignment.assignee_type == assignee_type,
            RoleAssignment.user_id == user_id,
            RoleAssignment.service_account_id == service_account_id,
            RoleAssignment.scope_type == scope_type,
            RoleAssignment.scope_id == scope_id
        )
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Grant already exists")

    # Create grant
    grant = RoleAssignment(
        role_id=grant_data.role_id,
        assignee_type=assignee_type,
        user_id=user_id,
        service_account_id=service_account_id,
        scope_type=scope_type,
        scope_id=scope_id,
        valid_from=grant_data.valid_from or datetime.utcnow(),
        valid_until=grant_data.valid_until,
        assigned_by=current_user.id
    )
    db.add(grant)
    await db.commit()
    await db.refresh(grant)

    # Invalidate cache
    if user_id:
        await invalidate_user_cache(user_id)

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="grant.created",
        resource_type="grant",
        resource_id=grant.id,
        details={
            "principal": grant_data.principal,
            "role": role.name,
            "scope": grant_data.scope
        }
    )

    return grant

@router.delete("/api/admin/grants/{grant_id}", status_code=204)
async def revoke_grant(
    grant_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """Revoke role assignment (PRD Story 3.5 @AC2)."""
    # Check permission
    # ...

    grant = await db.get(RoleAssignment, grant_id)
    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")

    # Invalidate cache before deletion
    if grant.user_id:
        await invalidate_user_cache(grant.user_id)

    await db.delete(grant)
    await db.commit()

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="grant.revoked",
        resource_type="grant",
        resource_id=grant_id
    )

@router.get("/api/admin/grants/", response_model=list[GrantRead])
async def list_grants(
    principal: str | None = None,
    role_id: UUID | None = None,
    scope_type: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> list[GrantRead]:
    """
    List role assignments with filters.

    Query params:
    - principal: Filter by user:email or service_account:id
    - role_id: Filter by role
    - scope_type: Filter by scope (workspace, project, flow)
    """
    query = select(RoleAssignment)

    if principal:
        principal_type, principal_id = parse_principal(principal)
        if principal_type == "user":
            user = await get_user_by_email(principal_id, db)
            query = query.where(RoleAssignment.user_id == user.id)
        elif principal_type == "service_account":
            query = query.where(RoleAssignment.service_account_id == UUID(principal_id))

    if role_id:
        query = query.where(RoleAssignment.role_id == role_id)

    if scope_type:
        query = query.where(RoleAssignment.scope_type == scope_type)

    result = await db.execute(query)
    grants = result.scalars().all()
    return grants
```

**Pydantic Schemas:**
```python
class GrantCreate(BaseModel):
    principal: str  # "user:email@acme.com" or "service_account:uuid"
    role_id: UUID
    scope: dict[str, str]  # {"project": "PRJ1"} or {"workspace": "WB1"}
    valid_from: datetime | None = None
    valid_until: datetime | None = None  # Optional expiration

class GrantRead(BaseModel):
    id: UUID
    role_id: UUID
    assignee_type: str  # USER or SERVICE_ACCOUNT
    user_id: UUID | None
    service_account_id: UUID | None
    scope_type: str
    scope_id: str
    valid_from: datetime
    valid_until: datetime | None
    is_active: bool
    assigned_at: datetime
    assigned_by: UUID

    # Optional: Include role details
    role: RoleRead | None = None

    model_config = ConfigDict(from_attributes=True)
```

**Success Criteria:**
- [ ] POST /api/admin/grants/ creates grant (PRD @AC1)
- [ ] Response includes grant_id
- [ ] GET /api/admin/grants/{id} returns grant
- [ ] DELETE /api/admin/grants/{id} revokes grant (PRD @AC2)
- [ ] Cache invalidated on grant create/revoke
- [ ] Audit log entries created for all operations
- [ ] Filter by principal/role/scope works

**Implementation Files:**
```
src/backend/base/langflow/api/v1/rbac/grants.py
```

#### Task 3.4: Implement Service Account Management API

**Scope & Goals:**
Create and manage service accounts with scoped permissions (Story 2.4).

**Impact Subgraph from AppGraph:**
```
Interface Nodes:
- service_account_management_api → REST API for service accounts

Logic Nodes:
- create_service_account_logic → Creates service account
- generate_service_account_token_logic → Generates scoped API token
- delete_service_account_logic → Deletes service account

Edges:
- service_account_management_api → create_service_account_logic (invokes)
- create_service_account_logic → service_account_entity (creates)
- generate_service_account_token_logic → api_key_entity (creates)
- generate_service_account_token_logic → service_account_entity (links_to)
```

**API Endpoints (PRD Story 2.4):**
```python
# src/backend/base/langflow/api/v1/rbac/service_accounts.py

@router.post("/api/admin/service_accounts/", response_model=ServiceAccountRead, status_code=201)
async def create_service_account(
    sa_data: ServiceAccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> ServiceAccountRead:
    """
    Create service account (PRD Story 2.4 @AC1).

    Example:
    {
        "name": "ci-bot",
        "description": "CI/CD pipeline bot",
        "workspace_id": "uuid-123",
        "role_id": "uuid-456",  # Role to assign
        "scope": {"workspace": "WB1"}
    }
    """
    # Check permission (requires admin in workspace)
    # ...

    # Validate workspace exists
    workspace = await db.get(Workspace, sa_data.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Create service account
    sa = ServiceAccount(
        name=sa_data.name,
        description=sa_data.description,
        workspace_id=sa_data.workspace_id,
        created_by=current_user.id
    )
    db.add(sa)
    await db.flush()

    # Assign role if provided
    if sa_data.role_id and sa_data.scope:
        scope_type, scope_id = parse_scope(sa_data.scope)
        grant = RoleAssignment(
            role_id=sa_data.role_id,
            assignee_type="SERVICE_ACCOUNT",
            service_account_id=sa.id,
            scope_type=scope_type,
            scope_id=scope_id,
            assigned_by=current_user.id
        )
        db.add(grant)

    await db.commit()
    await db.refresh(sa)

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="service_account.created",
        resource_type="service_account",
        resource_id=sa.id
    )

    return sa

@router.post("/api/admin/service_accounts/{sa_id}/tokens", response_model=TokenResponse, status_code=201)
async def create_service_account_token(
    sa_id: UUID,
    token_data: TokenCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> TokenResponse:
    """
    Generate API token for service account.

    Token inherits service account's role permissions scoped to specified resource.
    """
    # Check permission
    # ...

    sa = await db.get(ServiceAccount, sa_id)
    if not sa:
        raise HTTPException(status_code=404, detail="Service account not found")

    # Generate token
    token_value = secrets.token_urlsafe(32)
    token_hash = hash_token(token_value)

    api_key = ApiKey(
        api_key=token_hash,
        name=token_data.name or f"{sa.name} token",
        service_account_id=sa.id,
        user_id=None,  # Service account token
        scoped_permissions=token_data.scoped_permissions or [],
        scope_type=token_data.scope_type,
        scope_id=token_data.scope_id,
        workspace_id=sa.workspace_id
    )
    db.add(api_key)
    await db.commit()

    # Return token value (only time it's visible)
    return TokenResponse(
        id=api_key.id,
        token=f"lgs_{token_value}",  # lgs = LangBuilder Service
        name=api_key.name,
        created_at=api_key.created_at
    )

@router.delete("/api/admin/service_accounts/{sa_id}", status_code=204)
async def delete_service_account(
    sa_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """Delete service account and all its tokens."""
    # Check permission
    # ...

    sa = await db.get(ServiceAccount, sa_id)
    if not sa:
        raise HTTPException(status_code=404, detail="Service account not found")

    # Delete all tokens (cascade should handle, but explicit is better)
    await db.execute(
        delete(ApiKey).where(ApiKey.service_account_id == sa_id)
    )

    # Delete role assignments
    await db.execute(
        delete(RoleAssignment).where(RoleAssignment.service_account_id == sa_id)
    )

    await db.delete(sa)
    await db.commit()

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="service_account.deleted",
        resource_type="service_account",
        resource_id=sa_id
    )
```

**Pydantic Schemas:**
```python
class ServiceAccountCreate(BaseModel):
    name: str
    description: str | None = None
    workspace_id: UUID
    role_id: UUID | None = None  # Optional initial role
    scope: dict[str, str] | None = None  # Scope for initial role

class ServiceAccountRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool
    workspace_id: UUID
    created_at: datetime
    created_by: UUID
    last_used_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

class TokenCreate(BaseModel):
    name: str | None = None
    scoped_permissions: list[str] | None = None  # Optional permission filter
    scope_type: str | None = None  # workspace, project, etc.
    scope_id: str | None = None

class TokenResponse(BaseModel):
    id: UUID
    token: str  # Only visible on creation
    name: str
    created_at: datetime
```

**Success Criteria:**
- [ ] POST /api/admin/service_accounts/ creates account (PRD @AC1)
- [ ] Service account scoped to workspace
- [ ] POST /tokens generates API token
- [ ] Token inherits service account permissions
- [ ] Token cannot access outside workspace (PRD @AC1)
- [ ] DELETE deletes account and tokens
- [ ] Audit log entries created

**Implementation Files:**
```
src/backend/base/langflow/api/v1/rbac/service_accounts.py
```

#### Task 3.5: Write Integration Tests for RBAC API

**Scope & Goals:**
End-to-end API tests validating RBAC management endpoints.

**Impact Subgraph from AppGraph:**
```
Test Nodes:
- test_role_api_integration → Tests role CRUD
- test_grant_api_integration → Tests grant CRUD
- test_service_account_api_integration → Tests service account CRUD

Edges:
- test_role_api_integration → role_management_api (tests)
- test_grant_api_integration → grant_management_api (tests)
- test_service_account_api_integration → service_account_management_api (tests)
```

**Test Scenarios:**

**Story 3.2 @AC1: Create role via API**
```python
async def test_create_role_via_api(client, admin_headers):
    """PRD Story 3.2 @AC1: Create role via API"""
    response = await client.post(
        "/api/admin/roles/",
        json={
            "name": "QALead",
            "display_name": "QA Lead",
            "description": "QA team lead role",
            "permission_ids": [str(read_perm_id), str(deploy_perm_id)]
        },
        headers=admin_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "QALead"
    role_id = data["id"]

    # Verify GET returns same data
    get_response = await client.get(f"/api/admin/roles/{role_id}", headers=admin_headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "QALead"
```

**Story 3.5 @AC1: Create grant via API**
```python
async def test_create_grant_via_api(client, admin_headers, db_session):
    """PRD Story 3.5 @AC1: Assign role via API"""
    # Arrange
    user_carol = await create_user("carol@acme.com", db_session)
    role_editor = await get_role("editor", db_session)
    project_prj1 = await create_project("PRJ1", db_session)

    # Act
    response = await client.post(
        "/api/admin/grants/",
        json={
            "principal": "user:carol@acme.com",
            "role_id": str(role_editor.id),
            "scope": {"project": str(project_prj1.id)}
        },
        headers=admin_headers
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    grant_id = data["id"]

    # Verify GET shows grant
    get_response = await client.get(f"/api/admin/grants/{grant_id}", headers=admin_headers)
    assert get_response.status_code == 200
    assert get_response.json()["role_id"] == str(role_editor.id)
```

**Story 3.5 @AC2: Revoke grant via API**
```python
async def test_revoke_grant_via_api(client, admin_headers, db_session):
    """PRD Story 3.5 @AC2: Revoke grant via API"""
    # Arrange: Create grant first
    grant = await create_grant_in_db(
        user_id=test_user_id,
        role_id=editor_role_id,
        scope_type="project",
        scope_id=project_id,
        db_session=db_session
    )

    # Act: Revoke
    response = await client.delete(
        f"/api/admin/grants/{grant.id}",
        headers=admin_headers
    )

    # Assert
    assert response.status_code == 204

    # Verify GET returns 404
    get_response = await client.get(f"/api/admin/grants/{grant.id}", headers=admin_headers)
    assert get_response.status_code == 404
```

**Success Criteria:**
- [ ] All PRD Story 3.2 tests pass (role API)
- [ ] All PRD Story 3.5 tests pass (grant API)
- [ ] Service account API tests pass
- [ ] Permission API tests pass
- [ ] 401/403 tests pass (unauthorized/forbidden)
- [ ] Validation error tests pass (400 errors)
- [ ] Integration tests run in CI

**Implementation Files:**
```
src/backend/tests/integration/api/v1/rbac/
├── test_roles_api.py
├── test_grants_api.py
├── test_service_accounts_api.py
└── test_permissions_api.py
```

---

### Phase 4: Enforce RBAC in Existing Endpoints

**Description:** Integrate RBAC enforcement into existing resource endpoints (flows, projects, components, users). This phase replaces binary `is_superuser` checks with fine-grained permission checks.

**Scope:**
- Add RBAC middleware to existing endpoints
- Replace `user_id == resource.user_id OR is_superuser` with permission checks
- Implement all PRD permission enforcement stories (1.1 @AC3-AC8, 4.2)
- Maintain backward compatibility for existing users

**Goals:**
- All resource operations gated by RBAC permissions
- Existing user-owned resources still accessible (implicit Owner role)
- Zero regression for existing users
- PRD acceptance criteria pass for enforcement stories

#### Task 4.1: Implement RBAC FastAPI Dependency

**Scope & Goals:**
Create reusable FastAPI dependency for permission checking.

**Impact Subgraph from AppGraph:**
```
Logic Nodes:
- rbac_middleware_dependency → FastAPI dependency for permission checks
- require_permission_decorator → Decorator for endpoint protection

Edges:
- rbac_middleware_dependency → rbac_enforcement_engine (invokes)
- require_permission_decorator → rbac_middleware_dependency (uses)
- *_api_endpoint → require_permission_decorator (depends_on)
```

**Architecture & Tech Stack:**
- **Pattern**: FastAPI Depends() injectable
- **Integration**: Works with existing `get_current_active_user` dependency
- **Reusable**: Can be applied to any endpoint

**Implementation:**
```python
# src/backend/base/langflow/services/rbac/dependencies.py

from fastapi import Depends, HTTPException, status
from typing import Callable

def require_permission(
    action: str,
    resource_type: str,
    resource_id_param: str = "id",  # Path param name for resource ID
    scope_type: str | None = None
) -> Callable:
    """
    FastAPI dependency factory for permission checking.

    Usage:
        @router.patch("/api/v1/flows/{flow_id}")
        async def update_flow(
            flow_id: UUID,
            flow_data: FlowUpdate,
            _: None = Depends(require_permission("flow.update", "flow", "flow_id"))
        ):
            # If we reach here, user has permission
            ...

    Args:
        action: Permission action (e.g., "flow.update")
        resource_type: Resource type (e.g., "flow")
        resource_id_param: Path param name containing resource ID
        scope_type: Explicit scope type (default: infer from resource_type)
    """
    async def permission_checker(
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_session)
    ) -> None:
        # Extract resource ID from path params
        resource_id = request.path_params.get(resource_id_param)
        if not resource_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing resource ID parameter: {resource_id_param}"
            )

        # Convert to UUID if needed
        try:
            resource_uuid = UUID(resource_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format: {resource_id}"
            )

        # Check permission
        allowed, reason = await has_permission(
            user_id=current_user.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_uuid,
            scope_type=scope_type or resource_type
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {reason}"
            )

        # Permission granted, endpoint can proceed
        return None

    return permission_checker


# Convenience decorators for common operations
def require_read(resource_type: str, resource_id_param: str = "id"):
    return require_permission(f"{resource_type}.read", resource_type, resource_id_param)

def require_update(resource_type: str, resource_id_param: str = "id"):
    return require_permission(f"{resource_type}.update", resource_type, resource_id_param)

def require_delete(resource_type: str, resource_id_param: str = "id"):
    return require_permission(f"{resource_type}.delete", resource_type, resource_id_param)
```

**Success Criteria:**
- [ ] Dependency extracts resource ID from path params
- [ ] Calls `has_permission()` with correct arguments
- [ ] Returns 403 if permission denied
- [ ] Returns None if permission granted (allows endpoint to proceed)
- [ ] Works with async endpoints
- [ ] Reusable across multiple endpoints

**Implementation Files:**
```
src/backend/base/langflow/services/rbac/dependencies.py
```

#### Task 4.2: Enforce Permissions on Flow Endpoints

**Scope & Goals:**
Add RBAC checks to flow CRUD and execution endpoints (Story 1.1 @AC3, @AC4).

**Impact Subgraph from AppGraph:**
```
Logic Nodes (MODIFIED):
- create_flow_endpoint → Add flow.create permission check
- read_flow_endpoint → Add flow.read permission check
- update_flow_endpoint → Add flow.update permission check
- delete_flow_endpoint → Add flow.delete permission check
- export_flow_endpoint → Add flow.export permission check (PRD @AC3)
- execute_flow_endpoint → Add flow.execute permission check

Edges (NEW):
- create_flow_endpoint → rbac_enforcement_engine (checks_permission)
- read_flow_endpoint → rbac_enforcement_engine (checks_permission)
- update_flow_endpoint → rbac_enforcement_engine (checks_permission)
- delete_flow_endpoint → rbac_enforcement_engine (checks_permission)
- export_flow_endpoint → rbac_enforcement_engine (checks_permission)
- execute_flow_endpoint → rbac_enforcement_engine (checks_permission)
```

**Modified Endpoints:**
```python
# src/backend/base/langflow/api/v1/flows.py

# BEFORE (existing code):
@router.patch("/api/v1/flows/{flow_id}", response_model=FlowRead)
async def update_flow(
    flow_id: UUID,
    flow_data: FlowUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> FlowRead:
    """Update flow. Currently checks: user owns flow OR is superuser."""
    flow = await db.get(Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    # OLD AUTHORIZATION (too permissive):
    if flow.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    # ... update logic ...

# AFTER (with RBAC):
@router.patch("/api/v1/flows/{flow_id}", response_model=FlowRead)
async def update_flow(
    flow_id: UUID,
    flow_data: FlowUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
    _: None = Depends(require_update("flow", "flow_id"))  # NEW: RBAC check
) -> FlowRead:
    """Update flow. Requires flow.update permission."""
    flow = await db.get(Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    # NO LONGER NEEDED: RBAC dependency already checked permission
    # if flow.user_id != current_user.id and not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="Not authorized")

    # ... update logic ...

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="flow.updated",
        resource_type="flow",
        resource_id=flow_id
    )

    return flow
```

**Export Flow Endpoint (PRD Story 1.1 @AC3):**
```python
@router.post("/api/v1/flows/{flow_id}/export", response_model=dict)
async def export_flow(
    flow_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
    _: None = Depends(require_permission("flow.export", "flow", "flow_id"))  # Specific permission
) -> dict:
    """
    Export flow as JSON (PRD Story 1.1 @AC3).
    Requires flow.export permission.
    """
    flow = await db.get(Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    # Export logic
    exported_data = {
        "id": str(flow.id),
        "name": flow.name,
        "data": flow.data,
        "description": flow.description,
        "exported_at": datetime.utcnow().isoformat()
    }

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="flow.exported",
        resource_type="flow",
        resource_id=flow_id
    )

    return exported_data
```

**All Flow Endpoints to Modify:**
- `POST /api/v1/flows/` → Add `flow.create` permission check
- `GET /api/v1/flows/{flow_id}` → Add `flow.read` permission check
- `PATCH /api/v1/flows/{flow_id}` → Add `flow.update` permission check
- `DELETE /api/v1/flows/{flow_id}` → Add `flow.delete` permission check
- `POST /api/v1/flows/{flow_id}/export` → Add `flow.export` permission check (NEW endpoint or modify existing)
- `POST /api/v1/flows/{flow_id}/run` → Add `flow.execute` permission check

**Success Criteria:**
- [ ] All flow endpoints check RBAC permissions
- [ ] PRD Story 1.1 @AC3 passes (export requires flow.export)
- [ ] User with permission can access flow
- [ ] User without permission gets 403
- [ ] Backward compatibility: users still access their own flows (implicit Owner role)
- [ ] Audit log entries created for flow operations

**Implementation Files (Modified):**
```
src/backend/base/langflow/api/v1/flows.py
```

#### Task 4.3: Enforce Permissions on Project (Folder) Endpoints

**Scope & Goals:**
Add RBAC checks to project CRUD endpoints.

**Impact Subgraph from AppGraph:**
```
Logic Nodes (MODIFIED):
- create_project_endpoint → Add project.create permission check
- read_project_endpoint → Add project.read permission check
- update_project_endpoint → Add project.update permission check
- delete_project_endpoint → Add project.delete permission check

Edges (NEW):
- *_project_endpoint → rbac_enforcement_engine (checks_permission)
```

**Modified Endpoints:**
```python
# src/backend/base/langflow/api/v1/projects.py

@router.post("/api/v1/projects/", response_model=ProjectRead, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
    _: None = Depends(require_permission("project.create", "workspace", "workspace_id"))  # Check workspace permission
) -> ProjectRead:
    """Create project. Requires project.create permission in workspace."""
    # ... create logic ...

@router.patch("/api/v1/projects/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
    _: None = Depends(require_update("project", "project_id"))
) -> ProjectRead:
    """Update project. Requires project.update permission."""
    # ... update logic ...

@router.delete("/api/v1/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
    _: None = Depends(require_delete("project", "project_id"))
):
    """Delete project. Requires project.delete permission."""
    # ... delete logic ...
```

**Success Criteria:**
- [ ] All project endpoints check RBAC permissions
- [ ] User with permission can access project
- [ ] User without permission gets 403
- [ ] Audit log entries created

**Implementation Files (Modified):**
```
src/backend/base/langflow/api/v1/projects.py
```

#### Task 4.4: Enforce Token Scope on API Key Authentication

**Scope & Goals:**
Implement token scope enforcement (PRD Story 4.2).

**Impact Subgraph from AppGraph:**
```
Logic Nodes (MODIFIED):
- api_key_authentication_logic → Add scope validation
- token_scope_enforcer → Validates token scope matches request resource

Edges:
- api_key_authentication_logic → token_scope_enforcer (validates_via)
- token_scope_enforcer → api_key_entity (reads_scope_from)
```

**Modified Authentication Logic:**
```python
# src/backend/base/langflow/services/auth/utils.py

async def get_current_user_from_api_key(
    api_key: str = Security(api_key_security),
    db: AsyncSession = Depends(get_session)
) -> User:
    """
    Authenticate via API key and enforce token scope (PRD Story 4.2).
    """
    # Hash and lookup key
    key_hash = hash_token(api_key)
    result = await db.execute(
        select(ApiKey).where(ApiKey.api_key == key_hash, ApiKey.is_active == True)
    )
    api_key_record = result.scalar()

    if not api_key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Update last used
    api_key_record.last_used_at = datetime.utcnow()
    api_key_record.total_uses += 1
    await db.commit()

    # NEW: Attach token scope to request context for later validation
    request.state.api_key_scope = {
        "scope_type": api_key_record.scope_type,
        "scope_id": api_key_record.scope_id,
        "scoped_permissions": api_key_record.scoped_permissions,
        "workspace_id": api_key_record.workspace_id
    }

    # Return user (or service account)
    if api_key_record.user_id:
        user = await db.get(User, api_key_record.user_id)
        return user
    elif api_key_record.service_account_id:
        sa = await db.get(ServiceAccount, api_key_record.service_account_id)
        # Create synthetic User object for service account
        return User(
            id=sa.id,
            username=f"sa:{sa.name}",
            is_active=sa.is_active,
            is_superuser=False
        )
    else:
        raise HTTPException(status_code=401, detail="API key not associated with user or service account")


async def validate_token_scope(
    request: Request,
    resource_type: str,
    resource_id: UUID
) -> None:
    """
    Validate that API token scope allows access to this resource (PRD Story 4.2 @AC1).

    Raises HTTPException(403) if token scope violation.
    """
    # Check if request is authenticated via API key
    if not hasattr(request.state, "api_key_scope"):
        # Not API key auth, skip token scope check
        return

    token_scope = request.state.api_key_scope

    # If token has no scope limits, allow all (backward compatibility)
    if not token_scope.get("scope_type"):
        return

    # Validate resource is within token scope
    # Example: Token scoped to project=PRJ1 can only access flows/components in PRJ1

    if token_scope["scope_type"] == "project":
        # Check if resource belongs to this project
        resource_project_id = await get_resource_project_id(resource_type, resource_id, db)
        if resource_project_id != UUID(token_scope["scope_id"]):
            raise HTTPException(
                status_code=403,
                detail="token_scope_violation: Resource outside token scope"
            )

    elif token_scope["scope_type"] == "workspace":
        # Check if resource belongs to this workspace
        resource_workspace_id = await get_resource_workspace_id(resource_type, resource_id, db)
        if resource_workspace_id != UUID(token_scope["workspace_id"]):
            raise HTTPException(
                status_code=403,
                detail="token_scope_violation: Resource outside token scope"
            )

    # ... handle other scope types ...
```

**Integrate into RBAC Dependency:**
```python
# src/backend/base/langflow/services/rbac/dependencies.py

async def permission_checker(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> None:
    # ... existing permission check ...

    # NEW: Validate token scope if API key auth
    await validate_token_scope(request, resource_type, resource_uuid)

    # Permission granted
    return None
```

**Success Criteria:**
- [ ] PRD Story 4.2 @AC1 passes (scoped token works only in scope)
- [ ] Token scoped to PRJ1 can access flows in PRJ1
- [ ] Token scoped to PRJ1 cannot access flows in PRJ2 (403 error)
- [ ] Backward compatibility: unscoped tokens still work
- [ ] Service account tokens respect scope
- [ ] Audit log records token scope violations

**Implementation Files (Modified):**
```
src/backend/base/langflow/services/auth/utils.py
src/backend/base/langflow/services/rbac/dependencies.py
```

#### Task 4.5: Write Integration Tests for RBAC Enforcement

**Scope & Goals:**
End-to-end tests validating RBAC enforcement on resource endpoints.

**Test Scenarios:**

**Story 1.1 @AC3: Export flow requires permission**
```python
async def test_export_flow_requires_permission(client, db_session):
    """PRD Story 1.1 @AC3: Export requires flow.export"""
    # Arrange
    user_jo = await create_user("jo@test.com", db_session)
    flow_f123 = await create_flow("F123", owner=user_jo, db_session)
    role_exporter = await create_role("exporter", ["flow.export"], db_session)
    await assign_role(user_jo, role_exporter, scope_type="flow", scope_id=flow_f123.id, db_session)

    jo_headers = await get_auth_headers(user_jo, client)

    # Act: Export with permission
    response = await client.post(f"/api/v1/flows/{flow_f123.id}/export", headers=jo_headers)

    # Assert: Success
    assert response.status_code == 200

    # Act: Export different flow without permission
    flow_f124 = await create_flow("F124", db_session)
    response = await client.post(f"/api/v1/flows/{flow_f124.id}/export", headers=jo_headers)

    # Assert: Denied
    assert response.status_code == 403
    assert "permission_required" in response.json()["detail"]
```

**Story 4.2 @AC1: Token scope enforcement**
```python
async def test_token_scope_enforcement(client, db_session):
    """PRD Story 4.2 @AC1: Scoped token access"""
    # Arrange
    user_pat = await create_user("pat@test.com", db_session)
    project_prj1 = await create_project("PRJ1", owner=user_pat, db_session)
    project_prj2 = await create_project("PRJ2", owner=user_pat, db_session)
    flow_in_prj1 = await create_flow("Flow1", project=project_prj1, db_session)
    flow_in_prj2 = await create_flow("Flow2", project=project_prj2, db_session)

    # Create token scoped to PRJ1
    token = await create_api_key(
        user=user_pat,
        scoped_permissions=["flow.read"],
        scope_type="project",
        scope_id=project_prj1.id,
        db_session=db_session
    )
    token_headers = {"x-api-key": token.api_key}

    # Act: Read flow in PRJ1
    response = await client.get(f"/api/v1/flows/{flow_in_prj1.id}", headers=token_headers)

    # Assert: Success
    assert response.status_code == 200

    # Act: Read flow in PRJ2
    response = await client.get(f"/api/v1/flows/{flow_in_prj2.id}", headers=token_headers)

    # Assert: Denied (outside token scope)
    assert response.status_code == 403
    assert "token_scope_violation" in response.json()["detail"]
```

**Success Criteria:**
- [ ] All PRD Story 1.1 enforcement tests pass (@AC3-@AC8)
- [ ] All PRD Story 4.2 tests pass (token scope)
- [ ] Tests cover positive cases (permission granted)
- [ ] Tests cover negative cases (permission denied)
- [ ] Tests validate audit log entries created

**Implementation Files:**
```
src/backend/tests/integration/api/v1/
├── test_flows_rbac.py
├── test_projects_rbac.py
└── test_token_scope.py
```

---

### Phase 5: Identity Integration (SSO/SCIM)

**Description:** Implement SSO authentication (SAML 2.0, OIDC) and SCIM provisioning for enterprise identity management.

**Scope:**
- SSO login via SAML 2.0 and OIDC (Story 2.2)
- SCIM 2.0 server endpoints for user/group provisioning (Story 2.3)
- IdP configuration UI
- Attribute mapping (email, name, groups → roles)

**Goals:**
- Users can log in via SSO
- IdP manages user lifecycle (create/update/delete)
- Groups synced from IdP and mapped to roles
- MFA enforced at IdP level
- PRD Stories 2.2 and 2.3 acceptance criteria pass

**Note:** This phase is complex and requires careful security considerations. Implementation details omitted for brevity, but would follow similar pattern as previous phases.

---

### Phase 6: Audit Logging & Compliance

**Description:** Implement comprehensive audit logging for all RBAC operations and resource access decisions.

**Scope:**
- Immutable audit log table (Story 5.1)
- Async audit logging to avoid performance impact
- Audit log query API (Story 5.2)
- Compliance report generation (CSV/JSON export)
- GDPR/CCPA data minimization (mask PII)

**Goals:**
- All RBAC changes logged immutably
- All access decisions logged (configurable granularity)
- Audit logs queryable via API
- Compliance reports exportable
- PRD Stories 5.1 and 5.2 acceptance criteria pass

**Note:** Implementation details omitted for brevity.

---

### Phase 7: Infrastructure-as-Code & Advanced Features

**Description:** Enable RBAC management via YAML/Terraform for GitOps workflows.

**Scope:**
- YAML format for roles, grants (Story 3.3, 3.6)
- CLI command to apply RBAC config from YAML
- Terraform provider (optional)
- Break-glass emergency access (Story 2.2 @AC11)
- Time-boxed grants (Story 3.4 @AC3)

**Goals:**
- RBAC policies declarative and version-controlled
- `langflow rbac apply -f rbac.yaml` applies config
- PRD Stories 3.3 and 3.6 acceptance criteria pass

**Note:** Implementation details omitted for brevity.

---

## Summary

This implementation plan provides a comprehensive, phased approach to implementing enterprise-grade RBAC in LangBuilder. Each phase builds incrementally on the previous one, allowing for testing, validation, and deployment without breaking existing functionality.

**Key Success Factors:**
1. **Incremental rollout**: Each phase deployable independently
2. **Backward compatibility**: Existing users unaffected
3. **Test-driven**: Write tests before implementation
4. **Performance focus**: Caching and optimization from day 1
5. **Security-first**: Deny-by-default, audit logging, token scoping

**Estimated Timeline** (rough, for planning):
- Phase 1 (Database): 2-3 weeks
- Phase 2 (Evaluation Engine): 2-3 weeks
- Phase 3 (API Layer): 2-3 weeks
- Phase 4 (Enforcement): 2-3 weeks
- Phase 5 (SSO/SCIM): 4-6 weeks (complex)
- Phase 6 (Audit & Compliance): 2-3 weeks
- Phase 7 (IaC & Advanced): 2-3 weeks

**Total Estimated Timeline**: 16-24 weeks (4-6 months) for full implementation.

**Next Steps:**
1. Review and approve this plan
2. Set up development environment
3. Begin Phase 1 implementation
4. Establish CI/CD pipeline for RBAC tests
5. Schedule regular checkpoints with stakeholders
