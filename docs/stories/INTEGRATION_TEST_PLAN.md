# RBAC Integration Test Plan

## Overview

This document outlines integration testing requirements to verify RBAC is fully functional.

## Test Categories

### 1. Database Migrations ✅

**Status**: Complete (4 migrations created)

**Files**:
- `006_add_group_tables.py` - Groups and GroupMemberships
- `007_add_scim_tables.py` - SCIM provisioning tables
- `008_add_compliance_tables.py` - Compliance reporting tables
- `009_add_access_review_tables.py` - Access review tables

**Test**: Run migration up/down to verify tables are created correctly

```bash
cd src/backend/base
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

### 2. API Router Registration ✅

**Status**: Complete (3 routers registered)

**Registered APIs**:
- ✅ `/api/v1/groups` - Group management (Story 2.1)
- ✅ `/api/v1/iac` - Infrastructure as Code (Story 3.6)
- ✅ `/api/v1/scim/v2` - SCIM provisioning (Story 2.3)
- ✅ `/api/v1/compliance` - Compliance reports (Story 5.2)
- ✅ `/api/v1/access-reviews` - Access reviews

**Files Modified**:
- `src/backend/base/langflow/api/v1/__init__.py` - Added imports
- `src/backend/base/langflow/api/router.py` - Added router registrations

**Test**: Start server and verify endpoints are accessible

```bash
curl http://localhost:7860/api/v1/groups
curl http://localhost:7860/api/v1/iac
curl http://localhost:7860/api/v1/scim/v2/Users
```

### 3. Group-Based Permissions ✅

**Status**: Test created

**File**: `src/backend/tests/integration/test_group_based_permissions.py`

**Test Scenarios**:
1. ✅ User inherits permissions via group membership
2. ✅ User has both direct and group-based grants
3. ✅ User loses permissions when removed from group
4. ✅ User in multiple groups accumulates permissions

**Run**:
```bash
pytest src/backend/tests/integration/test_group_based_permissions.py -v
```

### 4. End-to-End Workflows (Manual Testing)

#### Workflow 1: Create Group and Assign Permissions

**Steps**:
1. Create a role "Project Editor" with permissions: `flows:read`, `flows:create`, `flows:update`
2. Create a group "Project Editors Team"
3. Grant "Project Editor" role to group at PROJECT scope (project_id=PRJ123)
4. Create a user alice@example.com
5. Add alice to "Project Editors Team"
6. Verify alice can read/create/update flows in PRJ123
7. Verify alice CANNOT delete flows (no flows:delete permission)
8. Verify alice CANNOT access flows in other projects

**Expected**: All verifications pass

#### Workflow 2: SCIM Provisioning

**Steps**:
1. Send SCIM POST request to create user bob@example.com
2. Verify SCIM user created in `scim_users` table
3. Verify internal User created and linked
4. Send SCIM POST to create group "Engineering"
5. Map "Engineering" to role "Developer" at Workspace scope
6. Add bob to "Engineering" via SCIM group membership
7. Verify bob has "Developer" permissions

**Expected**: SCIM sync creates users, groups, and permissions correctly

#### Workflow 3: IaC Policy Application

**Steps**:
1. Create YAML policy file:
```yaml
roles:
  - name: DataScientist
    permissions:
      - flows:read
      - flows:create
      - flows:execute

grants:
  - principal: group:DataScientists
    role: DataScientist
    scope: workspace:WS001
```

2. POST to `/api/v1/iac/apply` with YAML content
3. Verify role "DataScientist" created
4. Verify grant created for group "DataScientists"
5. Add user carol to "DataScientists" group
6. Verify carol has flow execute permissions in WS001

**Expected**: IaC creates roles and grants declaratively

#### Workflow 4: Compliance Report Generation

**Steps**:
1. Create compliance report for SOC2 framework
2. Set date range: 2025-01-01 to 2025-03-31
3. Generate report
4. Verify report includes:
   - List of all roles and their permissions
   - List of all grants (who has what access)
   - Access review status
   - Anomaly detection findings
5. Export report as JSON
6. Verify required attestation signature

**Expected**: Compliance report contains all required audit data

#### Workflow 5: Access Review Campaign

**Steps**:
1. Create access review campaign "Q1 2025 Review"
2. Set auto-revoke if no response: true
3. Campaign generates review items for all active grants
4. Manager reviews and approves alice's access
5. Manager does NOT respond to bob's access item
6. Campaign ends
7. Verify bob's grant is revoked (auto-revoke)
8. Verify alice's grant remains active

**Expected**: Access review enforces periodic recertification

### 5. Permission Enforcement in APIs

**Test**: Verify API endpoints actually check permissions

**Scenarios**:

1. **Flow API** (`/api/v1/flows`)
   - User with `flows:read` can GET flows
   - User without `flows:create` gets 403 on POST
   - User with scoped grant can only access flows in their scope

2. **Project API** (`/api/v1/projects`)
   - User with `projects:admin` can create projects
   - User with `projects:read` cannot delete projects

3. **Role API** (`/api/v1/roles`)
   - Only users with `roles:manage` can create/update roles
   - All users can list roles (read-only)

**Run**:
```bash
pytest src/backend/tests/integration/test_rbac_enforcement.py -v
```

### 6. Scope Hierarchy Validation

**Test**: Verify scope inheritance works correctly

**Scenarios**:

1. User granted `flows:read` at WORKSPACE level can read flows in ALL projects/environments in that workspace
2. User granted `flows:create` at PROJECT level can create flows ONLY in that project
3. User granted `flows:delete` at FLOW level can delete ONLY that specific flow

**Expected**: Higher scope grants cascade to lower scopes

### 7. Deny-by-Default Verification

**Test**: Ensure no implicit permissions exist

**Scenario**:
1. Create user with NO grants
2. Attempt to access ANY resource
3. Verify ALL requests return 403 Forbidden

**Expected**: Zero permissions without explicit grant

## Test Execution Checklist

- [ ] Run database migrations (up/down/up)
- [ ] Start backend server and verify API routes
- [ ] Run pytest for group-based permissions
- [ ] Manual test: Create group workflow
- [ ] Manual test: SCIM provisioning
- [ ] Manual test: IaC policy application
- [ ] Manual test: Compliance report
- [ ] Manual test: Access review campaign
- [ ] Run pytest for API permission enforcement
- [ ] Verify scope hierarchy
- [ ] Verify deny-by-default

## Success Criteria

**RBAC is production-ready when**:

1. ✅ All migrations run without errors
2. ✅ All API endpoints are accessible
3. ✅ All pytest tests pass (100%)
4. ✅ Manual workflows complete successfully
5. ✅ No permission bypass vulnerabilities found
6. ✅ Scope inheritance works correctly
7. ✅ Deny-by-default is enforced

## Known Gaps

1. **Story 4.2 - Token Scope Enforcement**
   - Service account tokens do NOT have resource-level scopes
   - Need to add `scope_type` and `scope_id` to APIToken model
   - Estimated: 2-3 days

## Next Steps

1. Complete integration testing (Items 1-7 above)
2. Fix any failing tests
3. Implement Story 4.2 (token scoping)
4. Final end-to-end validation
5. Mark RBAC as production-ready
