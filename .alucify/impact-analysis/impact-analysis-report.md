# Impact Analysis Report

## Executive Summary

| Metric | Value | Risk Level |
|--------|-------|------------|
| Overall Blast Radius | 5.64% (34/603 nodes) | Low |
| Regression Testing Risk | 100.0% uncovered | Critical |
| Data Integrity Risk | 55.56% schemas impacted | Critical |
| Backward Compatibility Risk | 11.54% APIs modified | Low |

### Key Findings
- **Low Blast Radius**: Only 5.64% of implementation nodes are impacted, indicating a well-scoped RBAC feature
- **Critical Regression Risk**: All 18 modified nodes lack documented test coverage and require testing attention
- **Schema Impact**: 7 new schema nodes added for RBAC data model (RolePermission, RoleAssignment, EntityScope)
- **New Components**: 16 new interface/schema/logic nodes added for RBAC functionality

### Recommendations
1. **Priority 1**: Establish test coverage for all 18 modified nodes, focusing on high-connectivity logic nodes
2. **Priority 2**: Create integration tests for new schema entities (RolePermission, RoleAssignment, EntityScope)
3. **Priority 3**: Implement E2E tests for new RBAC admin interface components (RBACManagementPage, AssignmentFormModal)

---

## Report Metadata

- **Codebase**: LangBuilder
- **AppGraph Source**: /Users/dongmingjiang/Alucify/LangBuilder/.alucify/appgraph-with-prd-impact.json
- **Analysis Date**: 2026-01-25T12:22:59.390489
- **Total Epics**: 4
- **Total Stories**: 19
- **Total Functional Requirements Covered**: 21

### Stories Covered in this Codebase

| Story | Story Name | FRs Covered | Impl. Nodes | Validation Nodes | Validates (Total) | Validates (Other Stories) |
|-------|------------|-------------|-------------|------------------|-------------------|---------------------------|
| Story 1.1 | Define & Persist Core Permissions and Sc... | FR1.1, FR1.2 | 2 | 1 | 3 | 1 |
| Story 1.2 | Define & Persist Default Roles and Mappi... | FR1.3, FR1.4 | 1 | 1 | 3 | 2 |
| Story 1.3 | Implement Core Role Assignment Logic | FR1.5 | 4 | 1 | 7 | 4 |
| Story 1.4 | Default Project Owner Immutability Check | FR1.6 | 1 | 1 | 4 | 3 |
| Story 1.5 | Global Project Creation & New Entity Own... | FR1.7 | 2 | 1 | 4 | 2 |
| Story 1.6 | Define Project to Flow Role Extension Ru... | FR1.8 | 2 | 1 | 4 | 2 |
| Story 2.1 | Core CanAccess Authorization Service | FR2.1 | 1 | 1 | 5 | 4 |
| Story 2.2 | Enforce Read/View Permission & List Visi... | FR2.2 | 10 | 1 | 13 | 3 |
| Story 2.3 | Enforce Create Permission on Projects & ... | FR2.3 | 0 | 1 | 8 | 8 |
| Story 2.4 | Enforce Update/Edit Permission for Proje... | FR2.4 | 2 | 1 | 8 | 6 |
| Story 2.5 | Enforce Delete Permission for Projects &... | FR2.5 | 2 | 1 | 8 | 6 |
| Story 3.1 | RBAC Management Section in the Admin Pag... | FR3.1 | 2 | 1 | 4 | 2 |
| Story 3.2 | Assignment Creation Workflow (New Roles) | FR3.2 | 2 | 1 | 6 | 4 |
| Story 3.3 | Assignment List View and Filtering | FR3.3 | 2 | 1 | 4 | 2 |
| Story 3.4 | Assignment Editing and Removal | FR3.4 | 1 | 1 | 5 | 4 |
| Story 3.5 | Flow Role Inheritance Display Rule | FR3.5 | 0 | 1 | 3 | 3 |
| Story 5.1 | Role Assignment and Enforcement Latency | FR5.1 | 0 | 2 | 7 | 7 |
| Story 5.2 | System Uptime and Availability | FR5.2 | 0 | 1 | 7 | 7 |
| Story 5.3 | Readiness Time (Initial Load) | FR5.3 | 0 | 1 | 4 | 4 |

**Legend**:
- **Impl. Nodes**: Interface, Schema, and Logic nodes directly belonging to this story
- **Validation Nodes**: Gherkin test specifications for this story's acceptance criteria
- **Validates (Total)**: Total nodes referenced by this story's validation nodes (validates_nodes + depends_on_nodes)
- **Validates (Other Stories)**: Nodes that belong to OTHER stories but are validated/depended on by this story's tests

---

## Project-Level Metrics

### 1. Blast Radius

**Overall**: 5.64% of nodes impacted (34/603)

#### By Layer

| Layer | Total | New | Modified | Impacted | Percentage |
|-------|-------|-----|----------|----------|------------|
| Interface | 84 | 5 | 3 | 8 | 9.52% |
| Schema | 13 | 4 | 3 | 7 | 53.85% |
| Logic | 506 | 7 | 12 | 19 | 3.75% |

#### User Flow Impact

- **Total Navigation Paths**: 20
- **Affected Flows**: 7

<details>
<summary>Affected Flow Details</summary>

| Flow | Source | Target | Impact Status |
|------|--------|--------|---------------|
| eii0030 | ni0009 | ni0021 | intact |
| eii0031 | ni0009 | ni0015 | intact |
| eii0032 | ni0021 | ni0009 | intact |
| eii0043 | ni0020 | ni0009 | intact |
| eii0044 | ni0001 | ni0013 | intact |
| eii0050 | ni0001 | ni0016 | intact |
| eii0052 | ni0009 | ni0020 | intact |

</details>

### 2. Regression Testing Risk

**Risk Level**: Critical
**Uncovered Modified Nodes**: 18/18 (100.0%)

#### By Node Type

| Type | Modified | Uncovered | Coverage Gap |
|------|----------|-----------|--------------|
| Interface | 3 | 3 | 100.0% |
| Schema | 3 | 3 | 100.0% |
| Logic | 12 | 12 | 100.0% |

<details>
<summary>Nodes Requiring Test Coverage</summary>

| Node ID | Name | Type | Path |
|---------|------|------|------|
| ni0001 | AdminPage | interface | src/frontend/src/pages/AdminPage/index.tsx |
| ni0006 | CollectionPage | interface | src/frontend/src/pages/MainPage/pages/main-page.ts |
| ni0009 | FlowPage | interface | src/frontend/src/pages/FlowPage/index.tsx |
| ns0001 | User | schema | src/backend/base/langbuilder/services/database/mod |
| ns0002 | Flow | schema | src/backend/base/langbuilder/services/database/mod |
| ns0003 | Folder | schema | src/backend/base/langbuilder/services/database/mod |
| nl0004 | Create Flow Endpoint Handler | logic | src/backend/base/langbuilder/api/v1/flows.py |
| nl0005 | List Flows Endpoint Handler | logic | src/backend/base/langbuilder/api/v1/flows.py |
| nl0007 | Get Flow by ID Endpoint Handle | logic | src/backend/base/langbuilder/api/v1/flows.py |
| nl0009 | Update Flow Endpoint Handler | logic | src/backend/base/langbuilder/api/v1/flows.py |
| nl0010 | Delete Flow Endpoint Handler | logic | src/backend/base/langbuilder/api/v1/flows.py |
| nl0012 | Upload Flows Endpoint Handler | logic | src/backend/base/langbuilder/api/v1/flows.py |
| nl0042 | Create Project Endpoint Handle | logic | src/backend/base/langbuilder/api/v1/projects.py |
| nl0043 | List Projects Endpoint Handler | logic | src/backend/base/langbuilder/api/v1/projects.py |
| nl0044 | Get Project by ID Endpoint Han | logic | src/backend/base/langbuilder/api/v1/projects.py |
| nl0045 | Update Project Endpoint Handle | logic | src/backend/base/langbuilder/api/v1/projects.py |
| nl0046 | Delete Project Endpoint Handle | logic | src/backend/base/langbuilder/api/v1/projects.py |
| nl0061 | Build Flow Endpoint Handler | logic | src/backend/base/langbuilder/api/v1/chat.py |

</details>

### 3. Data Integrity & Migration Risk

**Risk Level**: Critical
**Impacted Schemas**: 7/13 (53.85%)
**Weighted Risk Score**: 55.56%

#### Schema Impact Details

| Schema | Impact | Edge Count | Weight | Requires Migration | Cascade Impact |
|--------|--------|------------|--------|-------------------|----------------|
| User | modified | 66 | 3.0× | True | 5 nodes |
| Flow | modified | 198 | 3.0× | True | 3 nodes |
| Folder | modified | 49 | 3.0× | True | 2 nodes |
| Role | new | 12 | 2.0× | False | 0 nodes |
| Permission | new | 13 | 2.0× | False | 0 nodes |
| RolePermission | new | 7 | 1.5× | False | 0 nodes |
| UserRoleAssignment | new | 17 | 3.0× | False | 0 nodes |

### 4. Backward Compatibility Risk

**Risk Level**: Low
**Modified APIs**: 12/104 (11.54%)
**Breaking Changes**: 0

#### Breaking Changes

| API | Impact Summary | Consumers Affected |
|-----|----------------|-------------------|
| *None* | - | - |

#### Non-Breaking Changes

| API | Impact Summary | Consumers Affected |
|-----|----------------|-------------------|
| Create Flow Endpoint Handler | Add auto-assignment of Owner role to creator with  | 14 |
| List Flows Endpoint Handler | Replace in-query user_id filtering with permission | 14 |
| Get Flow by ID Endpoint Handler | Replace in-query user_id filtering with can_access | 14 |
| Update Flow Endpoint Handler | Replace in-query user_id filtering with can_access | 14 |
| Delete Flow Endpoint Handler | Replace in-query user_id filtering with can_access | 14 |
| Upload Flows Endpoint Handler | Add can_access(UPDATE, PROJECT, folder_id) check f | 0 |
| Create Project Endpoint Handler | Add auto-assignment of Owner role with is_immutabl | 6 |
| List Projects Endpoint Handler | Replace in-query user_id filtering with permission | 6 |
| Get Project by ID Endpoint Handler | Replace in-query user_id filtering with can_access | 6 |
| Update Project Endpoint Handler | Replace in-query user_id filtering with can_access | 6 |
| Delete Project Endpoint Handler | Replace in-query user_id filtering with can_access | 6 |
| Build Flow Endpoint Handler | Add can_access(READ, FLOW, flow_id) check. Flow ex | 8 |

---

## Epic-Level Metrics

### Epic: Epic 1 - Core RBAC Data Model and Default Assignment

| Metric | Value | Risk Level |
|--------|-------|------------|
| Blast Radius | 91.67% | - |
| Regression Testing Risk | 100.0% | Critical |
| Data Integrity Risk | 100.0% | Critical |
| Backward Compatibility Risk | 0.96% | Low |

**Stories in this Epic**: 6

<details>
<summary>Impacted Nodes</summary>

| Node | Type | Impact | Summary |
|------|------|--------|---------|
| Role | schema | new | New RBAC schema node. Defines 4 predefin |
| Permission | schema | new | New RBAC schema node. Defines 8 base per |
| RolePermission | schema | new | New RBAC schema node. Maps roles to perm |
| UserRoleAssignment | schema | new | New RBAC schema node. Core assignment lo |
| RBACService | logic | new | New RBAC core service. Provides can_acce |
| POST /api/v1/rbac/assignments | logic | new | New RBAC API endpoint. Create new role a |
| DELETE /api/v1/rbac/assignment | logic | new | New RBAC API endpoint. Delete role assig |
| User | schema | modified | Add role_assignments relationship to Use |
| Flow | schema | modified | No structural changes. Permission checks |
| Folder | schema | modified | No structural changes. Requires immutabi |
| Create Flow Endpoint Handler | logic | modified | Add auto-assignment of Owner role to cre |

</details>

### Epic: Epic 2 - RBAC Enforcement Engine & Runtime Checks

| Metric | Value | Risk Level |
|--------|-------|------------|
| Blast Radius | 66.67% | - |
| Regression Testing Risk | 100.0% | Critical |
| Data Integrity Risk | 0% | Low |
| Backward Compatibility Risk | 4.81% | Low |

**Stories in this Epic**: 5

<details>
<summary>Impacted Nodes</summary>

| Node | Type | Impact | Summary |
|------|------|--------|---------|
| GET /api/v1/rbac/check-permiss | logic | new | New RBAC API endpoint. Check if current  |
| RBACGuard | interface | new | New RBAC UI component. Declarative route |
| usePermission | interface | new | New RBAC hook. Reusable permission check |
| CollectionPage | interface | modified | Add permission-based filtering using use |
| FlowPage | interface | modified | Add read-only mode support using usePerm |
| List Flows Endpoint Handler | logic | modified | Replace in-query user_id filtering with  |
| Get Flow by ID Endpoint Handle | logic | modified | Replace in-query user_id filtering with  |
| Update Flow Endpoint Handler | logic | modified | Replace in-query user_id filtering with  |
| Delete Flow Endpoint Handler | logic | modified | Replace in-query user_id filtering with  |
| Upload Flows Endpoint Handler | logic | modified | Add can_access(UPDATE, PROJECT, folder_i |

</details>

### Epic: Epic 3 - Web-based Admin Management Interface

| Metric | Value | Risk Level |
|--------|-------|------------|
| Blast Radius | 100.0% | - |
| Regression Testing Risk | 100.0% | Critical |
| Data Integrity Risk | 0% | Low |
| Backward Compatibility Risk | 0.0% | Low |

**Stories in this Epic**: 5

<details>
<summary>Impacted Nodes</summary>

| Node | Type | Impact | Summary |
|------|------|--------|---------|
| GET /api/v1/rbac/roles | logic | new | New RBAC API endpoint. List all availabl |
| GET /api/v1/rbac/assignments | logic | new | New RBAC API endpoint. List role assignm |
| PATCH /api/v1/rbac/assignments | logic | new | New RBAC API endpoint. Update role assig |
| RBACManagementPage | interface | new | New RBAC UI page. Main management interf |
| AssignmentListView | interface | new | New RBAC UI component. Displays role ass |
| CreateAssignmentModal | interface | new | New RBAC UI component. Guided wizard for |
| AdminPage | interface | modified | Add RBAC Management tab containing RBACM |

</details>

### Epic: Epic 5 - Non-Functional Requirements

| Metric | Value | Risk Level |
|--------|-------|------------|
| Blast Radius | 0% | - |
| Regression Testing Risk | 0% | Low |
| Data Integrity Risk | 0% | Low |
| Backward Compatibility Risk | 0.0% | Low |

**Stories in this Epic**: 3

<details>
<summary>Impacted Nodes</summary>

| Node | Type | Impact | Summary |
|------|------|--------|---------|
| *None* | - | - | - |

</details>

---

## Cross-Story Validation Matrix

This section shows how validation nodes in one story reference and validate implementation nodes from other stories.
This is important for understanding test coverage dependencies and integration testing requirements.

### Summary

- **Total Cross-Story Validations**: 74 nodes validated across story boundaries
- **Stories with Cross-Validation**: 19

### Most Validated Stories (nodes validated by other stories' tests)

| Story | Nodes Validated by Other Stories |
|-------|----------------------------------|
| Story 1.3 | 28 |
| Story 1.1 | 14 |
| Story 2.2 | 11 |
| Story 2.1 | 7 |
| Story 3.4 | 4 |

### Most Validating Stories (stories that validate nodes from other stories)

| Story | Validates From Other Stories | From Stories |
|-------|------------------------------|--------------|
| Story 2.3 | 8 nodes | Story 1.5, Story 2.2, Story 2.1, Story 1.3, Story 1.1 |
| Story 5.1 | 7 nodes | Story 1.1, Story 2.1, Story 1.3, Story 3.4 |
| Story 5.2 | 7 nodes | Story 3.4, Story 1.3, Story 1.4, Story 2.1, Story 3.2, Story 3.3 |
| Story 2.4 | 6 nodes | Story 2.2, Story 1.3, Story 1.1, Story 2.1 |
| Story 2.5 | 6 nodes | Story 2.2, Story 2.1, Story 1.3, Story 1.1 |

### Cross-Story Validation Details

<details>
<summary>Full Cross-Story Validation Matrix</summary>

#### Story 3.1 validates nodes from:
**From Story 1.1:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0010` | Role | schema |

**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0504` | RBACService | logic |

#### Story 2.2 validates nodes from:
**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0504` | RBACService | logic |

**From Story 1.1:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0011` | Permission | schema |

**From Story 2.1:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0510` | GET /api/v1/rbac/check-permission | logic |

#### Story 1.3 validates nodes from:
**From Story 3.4:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0508` | PATCH /api/v1/rbac/assignments/{id} | logic |

**From Story 1.1:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0010` | Role | schema |
| `ns0011` | Permission | schema |

**From Story 1.4:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0509` | DELETE /api/v1/rbac/assignments/{id} | logic |

#### Story 1.6 validates nodes from:
**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0013` | UserRoleAssignment | schema |
| `nl0504` | RBACService | logic |

#### Story 1.5 validates nodes from:
**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0013` | UserRoleAssignment | schema |
| `nl0504` | RBACService | logic |

#### Story 2.4 validates nodes from:
**From Story 2.2:**
| Node ID | Name | Type |
|---------|------|------|
| `ni0086` | RBACGuard | interface |
| `ni0087` | usePermission | interface |
| `ni0009` | FlowPage | interface |

**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0504` | RBACService | logic |

**From Story 1.1:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0011` | Permission | schema |

**From Story 2.1:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0510` | GET /api/v1/rbac/check-permission | logic |

#### Story 2.5 validates nodes from:
**From Story 2.2:**
| Node ID | Name | Type |
|---------|------|------|
| `ni0006` | CollectionPage | interface |
| `ni0087` | usePermission | interface |
| `ni0086` | RBACGuard | interface |

**From Story 2.1:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0510` | GET /api/v1/rbac/check-permission | logic |

**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0504` | RBACService | logic |

**From Story 1.1:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0011` | Permission | schema |

#### Story 1.1 validates nodes from:
**From Story 1.2:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0012` | RolePermission | schema |

#### Story 1.2 validates nodes from:
**From Story 1.1:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0010` | Role | schema |
| `ns0011` | Permission | schema |

#### Story 3.2 validates nodes from:
**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0507` | POST /api/v1/rbac/assignments | logic |
| `ns0013` | UserRoleAssignment | schema |
| `nl0504` | RBACService | logic |

**From Story 1.1:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0010` | Role | schema |

#### Story 3.3 validates nodes from:
**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0013` | UserRoleAssignment | schema |
| `nl0504` | RBACService | logic |

#### Story 3.4 validates nodes from:
**From Story 3.3:**
| Node ID | Name | Type |
|---------|------|------|
| `ni0084` | AssignmentListView | interface |

**From Story 1.4:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0509` | DELETE /api/v1/rbac/assignments/{id} | logic |

**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0013` | UserRoleAssignment | schema |
| `nl0504` | RBACService | logic |

#### Story 1.4 validates nodes from:
**From Story 3.4:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0508` | PATCH /api/v1/rbac/assignments/{id} | logic |

**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0013` | UserRoleAssignment | schema |
| `nl0504` | RBACService | logic |

#### Story 2.1 validates nodes from:
**From Story 1.1:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0010` | Role | schema |
| `ns0011` | Permission | schema |

**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0013` | UserRoleAssignment | schema |
| `nl0504` | RBACService | logic |

#### Story 2.3 validates nodes from:
**From Story 1.5:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0013` | Batch Delete Flows Endpoint Handler | logic |
| `nl0004` | Create Flow Endpoint Handler | logic |

**From Story 2.2:**
| Node ID | Name | Type |
|---------|------|------|
| `ni0006` | CollectionPage | interface |
| `ni0087` | usePermission | interface |
| `ni0086` | RBACGuard | interface |

**From Story 2.1:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0510` | GET /api/v1/rbac/check-permission | logic |

**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0504` | RBACService | logic |

**From Story 1.1:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0011` | Permission | schema |

#### Story 3.5 validates nodes from:
**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0013` | UserRoleAssignment | schema |
| `nl0504` | RBACService | logic |

**From Story 3.3:**
| Node ID | Name | Type |
|---------|------|------|
| `ni0084` | AssignmentListView | interface |

#### Story 5.1 validates nodes from:
**From Story 1.1:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0010` | Role | schema |
| `ns0011` | Permission | schema |

**From Story 2.1:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0510` | GET /api/v1/rbac/check-permission | logic |

**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `ns0013` | UserRoleAssignment | schema |
| `nl0504` | RBACService | logic |
| `nl0507` | POST /api/v1/rbac/assignments | logic |

**From Story 3.4:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0508` | PATCH /api/v1/rbac/assignments/{id} | logic |

#### Story 5.2 validates nodes from:
**From Story 3.4:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0508` | PATCH /api/v1/rbac/assignments/{id} | logic |

**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0507` | POST /api/v1/rbac/assignments | logic |
| `nl0504` | RBACService | logic |

**From Story 1.4:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0509` | DELETE /api/v1/rbac/assignments/{id} | logic |

**From Story 2.1:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0510` | GET /api/v1/rbac/check-permission | logic |

**From Story 3.2:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0505` | GET /api/v1/rbac/roles | logic |

**From Story 3.3:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0506` | GET /api/v1/rbac/assignments | logic |

#### Story 5.3 validates nodes from:
**From Story 2.2:**
| Node ID | Name | Type |
|---------|------|------|
| `ni0006` | CollectionPage | interface |
| `ni0009` | FlowPage | interface |

**From Story 2.1:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0510` | GET /api/v1/rbac/check-permission | logic |

**From Story 1.3:**
| Node ID | Name | Type |
|---------|------|------|
| `nl0504` | RBACService | logic |


</details>

---

## Story-Level Metrics

### Story: Story 1.1 - Define & Persist Core Permissions and Scopes
**Epic**: Epic 1
**Functional Requirements**: FR1.1, FR1.2
**Acceptance Criteria**: AC01

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 2 |
| New Implementation Nodes | 2 |
| Modified Implementation Nodes | 0 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 3 (1 from other stories) |
| Schema Impact | 2 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Core RBAC Entities Definition** (AC01): new
  - **Validates** (3 nodes):
    - `ns0010` **Role** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0011` **Permission** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0012` **RolePermission** (schema) → *Story 1.2*: Define & Persist Default Roles
  - **Depends on** (3 nodes):
    - `ns0010` **Role** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0011` **Permission** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0012` **RolePermission** (schema) → *Story 1.2*: Define & Persist Default Roles

**Cross-Story Validation Summary**:
This story's test specifications validate **3** nodes total:
- **3** implementation nodes (interface/schema/logic)
- **1** from other stories

**Validated Nodes by Story**:
*From Story 1.2* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0012` | RolePermission | schema | new | validates |

*From Story 1.1* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0010` | Role | schema | new | validates |
| `ns0011` | Permission | schema | new | validates |


**Impacted Implementation Nodes**:
- **Role** (schema): New RBAC schema node. Defines 4 predefined roles with permis
- **Permission** (schema): New RBAC schema node. Defines 8 base permissions (4 actions 

### Story: Story 1.2 - Define & Persist Default Roles and Mappings
**Epic**: Epic 1
**Functional Requirements**: FR1.3, FR1.4
**Acceptance Criteria**: AC01, AC02

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 1 |
| New Implementation Nodes | 1 |
| Modified Implementation Nodes | 0 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 3 (2 from other stories) |
| Schema Impact | 1 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Default Roles and Permission Mappings** (AC01): new
  - **Validates** (3 nodes):
    - `ns0010` **Role** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0011` **Permission** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0012` **RolePermission** (schema) → *Story 1.2*: Define & Persist Default Roles
  - **Depends on** (3 nodes):
    - `ns0010` **Role** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0011` **Permission** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0012` **RolePermission** (schema) → *Story 1.2*: Define & Persist Default Roles

**Cross-Story Validation Summary**:
This story's test specifications validate **3** nodes total:
- **3** implementation nodes (interface/schema/logic)
- **2** from other stories

**Validated Nodes by Story**:
*From Story 1.2* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0012` | RolePermission | schema | new | validates |

*From Story 1.1* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0010` | Role | schema | new | validates |
| `ns0011` | Permission | schema | new | validates |


**Impacted Implementation Nodes**:
- **RolePermission** (schema): New RBAC schema node. Maps roles to permissions. Unique cons

### Story: Story 1.3 - Implement Core Role Assignment Logic
**Epic**: Epic 1
**Functional Requirements**: FR1.5
**Acceptance Criteria**: AC03, AC01

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 4 |
| New Implementation Nodes | 3 |
| Modified Implementation Nodes | 1 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 7 (4 from other stories) |
| Schema Impact | 2 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Role Assignment Logic** (AC01): new
  - **Validates** (5 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `nl0507` **POST /api/v1/rbac/assignments** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `nl0508` **PATCH /api/v1/rbac/assignments** (logic) → *Story 3.4*: Assignment Editing and Removal
    - `nl0509` **DELETE /api/v1/rbac/assignment** (logic) → *Story 1.4*: Default Project Owner Immutabi
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment
  - **Depends on** (4 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ns0010` **Role** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0011` **Permission** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment

**Cross-Story Validation Summary**:
This story's test specifications validate **7** nodes total:
- **7** implementation nodes (interface/schema/logic)
- **4** from other stories

**Validated Nodes by Story**:
*From Story 3.4* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0508` | PATCH /api/v1/rbac/assignments | logic | new | validates |

*From Story 1.3* (3 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0507` | POST /api/v1/rbac/assignments | logic | new | validates |
| `nl0504` | RBACService | logic | new | validates |
| `ns0013` | UserRoleAssignment | schema | new | validates |

*From Story 1.1* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0010` | Role | schema | new | depends_on |
| `ns0011` | Permission | schema | new | depends_on |

*From Story 1.4* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0509` | DELETE /api/v1/rbac/assignment | logic | new | validates |


**Impacted Implementation Nodes**:
- **UserRoleAssignment** (schema): New RBAC schema node. Core assignment logic with scope inher
- **RBACService** (logic): New RBAC core service. Provides can_access() for authorizati
- **POST /api/v1/rbac/assignments** (logic): New RBAC API endpoint. Create new role assignment. Admin onl
- **User** (schema): Add role_assignments relationship to UserRoleAssignment. Mai

### Story: Story 1.4 - Default Project Owner Immutability Check
**Epic**: Epic 1
**Functional Requirements**: FR1.6
**Acceptance Criteria**: AC01, AC04

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 1 |
| New Implementation Nodes | 1 |
| Modified Implementation Nodes | 0 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 4 (3 from other stories) |
| Schema Impact | 0 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Starter Project Owner Immutability** (AC01): new
  - **Validates** (4 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `nl0508` **PATCH /api/v1/rbac/assignments** (logic) → *Story 3.4*: Assignment Editing and Removal
    - `nl0509` **DELETE /api/v1/rbac/assignment** (logic) → *Story 1.4*: Default Project Owner Immutabi
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment
  - **Depends on** (2 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment

**Cross-Story Validation Summary**:
This story's test specifications validate **4** nodes total:
- **4** implementation nodes (interface/schema/logic)
- **3** from other stories

**Validated Nodes by Story**:
*From Story 3.4* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0508` | PATCH /api/v1/rbac/assignments | logic | new | validates |

*From Story 1.4* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0509` | DELETE /api/v1/rbac/assignment | logic | new | validates |

*From Story 1.3* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0013` | UserRoleAssignment | schema | new | validates |
| `nl0504` | RBACService | logic | new | validates |


**Impacted Implementation Nodes**:
- **DELETE /api/v1/rbac/assignments/{id}** (logic): New RBAC API endpoint. Delete role assignment. Admin only. C

### Story: Story 1.5 - Global Project Creation & New Entity Owner Mutability
**Epic**: Epic 1
**Functional Requirements**: FR1.7
**Acceptance Criteria**: AC01, AC05

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 1 |
| New Implementation Nodes | 0 |
| Modified Implementation Nodes | 1 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 4 (2 from other stories) |
| Schema Impact | 0 |
| API Impact | 1 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Project Creation and Owner Assignment** (AC01): new
  - **Validates** (3 nodes):
    - `nl0004` **Create Flow Endpoint Handler** (logic) → *Story 1.5*: Global Project Creation & New 
    - `nl0013` **Batch Delete Flows Endpoint Ha** (logic) → *Story 1.5*: Global Project Creation & New 
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
  - **Depends on** (4 nodes):
    - `nl0004` **Create Flow Endpoint Handler** (logic) → *Story 1.5*: Global Project Creation & New 
    - `nl0013` **Batch Delete Flows Endpoint Ha** (logic) → *Story 1.5*: Global Project Creation & New 
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment

**Cross-Story Validation Summary**:
This story's test specifications validate **4** nodes total:
- **4** implementation nodes (interface/schema/logic)
- **2** from other stories

**Validated Nodes by Story**:
*From Story 1.5* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0013` | Batch Delete Flows Endpoint Ha | logic | intact | validates |
| `nl0004` | Create Flow Endpoint Handler | logic | modified | validates |

*From Story 1.3* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0013` | UserRoleAssignment | schema | new | depends_on |
| `nl0504` | RBACService | logic | new | validates |


**Impacted Implementation Nodes**:
- **Create Flow Endpoint Handler** (logic): Add auto-assignment of Owner role to creator with rollback o

### Story: Story 1.6 - Define Project to Flow Role Extension Rule
**Epic**: Epic 1
**Functional Requirements**: FR1.8
**Acceptance Criteria**: AC01, AC06

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 2 |
| New Implementation Nodes | 0 |
| Modified Implementation Nodes | 2 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 4 (2 from other stories) |
| Schema Impact | 2 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Project Role Inheritance Logic** (AC01): new
  - **Validates** (2 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment
  - **Depends on** (4 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ns0002` **Flow** (schema) → *Story 1.6*: Define Project to Flow Role Ex
    - `ns0003` **Folder** (schema) → *Story 1.6*: Define Project to Flow Role Ex
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment

**Cross-Story Validation Summary**:
This story's test specifications validate **4** nodes total:
- **4** implementation nodes (interface/schema/logic)
- **2** from other stories

**Validated Nodes by Story**:
*From Story 1.6* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0003` | Folder | schema | modified | depends_on |
| `ns0002` | Flow | schema | modified | depends_on |

*From Story 1.3* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0013` | UserRoleAssignment | schema | new | validates |
| `nl0504` | RBACService | logic | new | validates |


**Impacted Implementation Nodes**:
- **Flow** (schema): No structural changes. Permission checks via UserRoleAssignm
- **Folder** (schema): No structural changes. Requires immutability check for User'

### Story: Story 2.1 - Core CanAccess Authorization Service
**Epic**: Epic 2
**Functional Requirements**: FR2.1
**Acceptance Criteria**: AC01, AC07

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 1 |
| New Implementation Nodes | 1 |
| Modified Implementation Nodes | 0 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 5 (4 from other stories) |
| Schema Impact | 0 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify CanAccess Authorization Logic** (AC01): new
  - **Validates** (2 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `nl0510` **GET /api/v1/rbac/check-permiss** (logic) → *Story 2.1*: Core CanAccess Authorization S
  - **Depends on** (4 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ns0010` **Role** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0011` **Permission** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment

**Cross-Story Validation Summary**:
This story's test specifications validate **5** nodes total:
- **5** implementation nodes (interface/schema/logic)
- **4** from other stories

**Validated Nodes by Story**:
*From Story 1.1* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0010` | Role | schema | new | depends_on |
| `ns0011` | Permission | schema | new | depends_on |

*From Story 2.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0510` | GET /api/v1/rbac/check-permiss | logic | new | validates |

*From Story 1.3* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0013` | UserRoleAssignment | schema | new | depends_on |
| `nl0504` | RBACService | logic | new | validates |


**Impacted Implementation Nodes**:
- **GET /api/v1/rbac/check-permission** (logic): New RBAC API endpoint. Check if current user has specific pe

### Story: Story 2.2 - Enforce Read/View Permission & List Visibility
**Epic**: Epic 2
**Functional Requirements**: FR2.2
**Acceptance Criteria**: AC01, AC08

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 7 |
| New Implementation Nodes | 2 |
| Modified Implementation Nodes | 5 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 13 (3 from other stories) |
| Schema Impact | 0 |
| API Impact | 3 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Read Permission and List Filtering** (AC01): new
  - **Validates** (10 nodes):
    - `nl0005` **List Flows Endpoint Handler** (logic) → *Story 2.2*: Enforce Read/View Permission &
    - `nl0007` **Get Flow by ID Endpoint Handle** (logic) → *Story 2.2*: Enforce Read/View Permission &
    - `nl0014` **Download Flows Endpoint Handle** (logic) → *Story 2.2*: Enforce Read/View Permission &
    - `nl0015` **Get Basic Examples Endpoint Ha** (logic) → *Story 2.2*: Enforce Read/View Permission &
    - `nl0012` **Upload Flows Endpoint Handler** (logic) → *Story 2.2*: Enforce Read/View Permission &
    - `nl0100` **Create Tables with Retry** (logic) → *Story 2.2*: Enforce Read/View Permission &
    - `ni0006` **CollectionPage** (interface) → *Story 2.2*: Enforce Read/View Permission &
    - `ni0009` **FlowPage** (interface) → *Story 2.2*: Enforce Read/View Permission &
    - `ni0086` **RBACGuard** (interface) → *Story 2.2*: Enforce Read/View Permission &
    - `ni0087` **usePermission** (interface) → *Story 2.2*: Enforce Read/View Permission &
  - **Depends on** (3 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `nl0510` **GET /api/v1/rbac/check-permiss** (logic) → *Story 2.1*: Core CanAccess Authorization S
    - `ns0011` **Permission** (schema) → *Story 1.1*: Define & Persist Core Permissi

**Cross-Story Validation Summary**:
This story's test specifications validate **13** nodes total:
- **13** implementation nodes (interface/schema/logic)
- **3** from other stories

**Validated Nodes by Story**:
*From Story 2.2* (10 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ni0006` | CollectionPage | interface | modified | validates |
| `nl0007` | Get Flow by ID Endpoint Handle | logic | modified | validates |
| `ni0009` | FlowPage | interface | modified | validates |
| `nl0100` | Create Tables with Retry | logic | intact | validates |
| `nl0014` | Download Flows Endpoint Handle | logic | intact | validates |
| `nl0005` | List Flows Endpoint Handler | logic | modified | validates |
| `ni0086` | RBACGuard | interface | new | validates |
| `nl0012` | Upload Flows Endpoint Handler | logic | modified | validates |
| `ni0087` | usePermission | interface | new | validates |
| `nl0015` | Get Basic Examples Endpoint Ha | logic | intact | validates |

*From Story 1.3* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0504` | RBACService | logic | new | depends_on |

*From Story 1.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0011` | Permission | schema | new | depends_on |

*From Story 2.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0510` | GET /api/v1/rbac/check-permiss | logic | new | depends_on |


**Impacted Implementation Nodes**:
- **RBACGuard** (interface): New RBAC UI component. Declarative route protection based on
- **usePermission** (interface): New RBAC hook. Reusable permission check for UI rendering de
- **CollectionPage** (interface): Add permission-based filtering using usePermission hook. Hid
- **FlowPage** (interface): Add read-only mode support using usePermission hook. Disable
- **List Flows Endpoint Handler** (logic): Replace in-query user_id filtering with permission-based fil
- **Get Flow by ID Endpoint Handler** (logic): Replace in-query user_id filtering with can_access(READ, FLO
- **Upload Flows Endpoint Handler** (logic): Add can_access(UPDATE, PROJECT, folder_id) check for import 

### Story: Story 2.3 - Enforce Create Permission on Projects & Flows
**Epic**: Epic 2
**Functional Requirements**: FR2.3
**Acceptance Criteria**: AC01

**Note**: This story contains only validation/test specifications (no implementation nodes)

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 0 |
| New Implementation Nodes | 0 |
| Modified Implementation Nodes | 0 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 8 (8 from other stories) |
| Schema Impact | 0 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Create Permission Enforcement** (AC01): new
  - **Validates** (5 nodes):
    - `nl0004` **Create Flow Endpoint Handler** (logic) → *Story 1.5*: Global Project Creation & New 
    - `nl0013` **Batch Delete Flows Endpoint Ha** (logic) → *Story 1.5*: Global Project Creation & New 
    - `ni0006` **CollectionPage** (interface) → *Story 2.2*: Enforce Read/View Permission &
    - `ni0086` **RBACGuard** (interface) → *Story 2.2*: Enforce Read/View Permission &
    - `ni0087` **usePermission** (interface) → *Story 2.2*: Enforce Read/View Permission &
  - **Depends on** (3 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `nl0510` **GET /api/v1/rbac/check-permiss** (logic) → *Story 2.1*: Core CanAccess Authorization S
    - `ns0011` **Permission** (schema) → *Story 1.1*: Define & Persist Core Permissi

**Cross-Story Validation Summary**:
This story's test specifications validate **8** nodes total:
- **8** implementation nodes (interface/schema/logic)
- **8** from other stories

**Validated Nodes by Story**:
*From Story 1.5* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0013` | Batch Delete Flows Endpoint Ha | logic | intact | validates |
| `nl0004` | Create Flow Endpoint Handler | logic | modified | validates |

*From Story 2.2* (3 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ni0006` | CollectionPage | interface | modified | validates |
| `ni0087` | usePermission | interface | new | validates |
| `ni0086` | RBACGuard | interface | new | validates |

*From Story 2.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0510` | GET /api/v1/rbac/check-permiss | logic | new | depends_on |

*From Story 1.3* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0504` | RBACService | logic | new | depends_on |

*From Story 1.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0011` | Permission | schema | new | depends_on |


### Story: Story 2.4 - Enforce Update/Edit Permission for Projects & Flows
**Epic**: Epic 2
**Functional Requirements**: FR2.4
**Acceptance Criteria**: AC10, AC01

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 1 |
| New Implementation Nodes | 0 |
| Modified Implementation Nodes | 1 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 8 (6 from other stories) |
| Schema Impact | 0 |
| API Impact | 1 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Update Permission Enforcement** (AC01): new
  - **Validates** (5 nodes):
    - `nl0009` **Update Flow Endpoint Handler** (logic) → *Story 2.4*: Enforce Update/Edit Permission
    - `nl0017` **Get Current User Endpoint Hand** (logic) → *Story 2.4*: Enforce Update/Edit Permission
    - `ni0009` **FlowPage** (interface) → *Story 2.2*: Enforce Read/View Permission &
    - `ni0086` **RBACGuard** (interface) → *Story 2.2*: Enforce Read/View Permission &
    - `ni0087` **usePermission** (interface) → *Story 2.2*: Enforce Read/View Permission &
  - **Depends on** (3 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `nl0510` **GET /api/v1/rbac/check-permiss** (logic) → *Story 2.1*: Core CanAccess Authorization S
    - `ns0011` **Permission** (schema) → *Story 1.1*: Define & Persist Core Permissi

**Cross-Story Validation Summary**:
This story's test specifications validate **8** nodes total:
- **8** implementation nodes (interface/schema/logic)
- **6** from other stories

**Validated Nodes by Story**:
*From Story 2.2* (3 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ni0086` | RBACGuard | interface | new | validates |
| `ni0087` | usePermission | interface | new | validates |
| `ni0009` | FlowPage | interface | modified | validates |

*From Story 2.4* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0017` | Get Current User Endpoint Hand | logic | intact | validates |
| `nl0009` | Update Flow Endpoint Handler | logic | modified | validates |

*From Story 1.3* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0504` | RBACService | logic | new | depends_on |

*From Story 1.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0011` | Permission | schema | new | depends_on |

*From Story 2.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0510` | GET /api/v1/rbac/check-permiss | logic | new | depends_on |


**Impacted Implementation Nodes**:
- **Update Flow Endpoint Handler** (logic): Replace in-query user_id filtering with can_access(UPDATE, F

### Story: Story 2.5 - Enforce Delete Permission for Projects & Flows
**Epic**: Epic 2
**Functional Requirements**: FR2.5
**Acceptance Criteria**: AC01, AC11

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 1 |
| New Implementation Nodes | 0 |
| Modified Implementation Nodes | 1 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 8 (6 from other stories) |
| Schema Impact | 0 |
| API Impact | 1 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Delete Permission Enforcement** (AC01): new
  - **Validates** (5 nodes):
    - `nl0010` **Delete Flow Endpoint Handler** (logic) → *Story 2.5*: Enforce Delete Permission for 
    - `nl0018` **List All Users Endpoint Handle** (logic) → *Story 2.5*: Enforce Delete Permission for 
    - `ni0006` **CollectionPage** (interface) → *Story 2.2*: Enforce Read/View Permission &
    - `ni0086` **RBACGuard** (interface) → *Story 2.2*: Enforce Read/View Permission &
    - `ni0087` **usePermission** (interface) → *Story 2.2*: Enforce Read/View Permission &
  - **Depends on** (3 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `nl0510` **GET /api/v1/rbac/check-permiss** (logic) → *Story 2.1*: Core CanAccess Authorization S
    - `ns0011` **Permission** (schema) → *Story 1.1*: Define & Persist Core Permissi

**Cross-Story Validation Summary**:
This story's test specifications validate **8** nodes total:
- **8** implementation nodes (interface/schema/logic)
- **6** from other stories

**Validated Nodes by Story**:
*From Story 2.2* (3 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ni0006` | CollectionPage | interface | modified | validates |
| `ni0087` | usePermission | interface | new | validates |
| `ni0086` | RBACGuard | interface | new | validates |

*From Story 2.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0510` | GET /api/v1/rbac/check-permiss | logic | new | depends_on |

*From Story 2.5* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0010` | Delete Flow Endpoint Handler | logic | modified | validates |
| `nl0018` | List All Users Endpoint Handle | logic | intact | validates |

*From Story 1.3* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0504` | RBACService | logic | new | depends_on |

*From Story 1.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0011` | Permission | schema | new | depends_on |


**Impacted Implementation Nodes**:
- **Delete Flow Endpoint Handler** (logic): Replace in-query user_id filtering with can_access(DELETE, F

### Story: Story 3.1 - RBAC Management Section in the Admin Page
**Epic**: Epic 3
**Functional Requirements**: FR3.1
**Acceptance Criteria**: AC01, AC19

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 2 |
| New Implementation Nodes | 1 |
| Modified Implementation Nodes | 1 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 4 (2 from other stories) |
| Schema Impact | 0 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify RBAC Management Section Access** (AC01): new
  - **Validates** (2 nodes):
    - `ni0001` **AdminPage** (interface) → *Story 3.1*: RBAC Management Section in the
    - `ni0083` **RBACManagementPage** (interface) → *Story 3.1*: RBAC Management Section in the
  - **Depends on** (2 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ns0010` **Role** (schema) → *Story 1.1*: Define & Persist Core Permissi

**Cross-Story Validation Summary**:
This story's test specifications validate **4** nodes total:
- **4** implementation nodes (interface/schema/logic)
- **2** from other stories

**Validated Nodes by Story**:
*From Story 1.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0010` | Role | schema | new | depends_on |

*From Story 1.3* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0504` | RBACService | logic | new | depends_on |

*From Story 3.1* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ni0083` | RBACManagementPage | interface | new | validates |
| `ni0001` | AdminPage | interface | modified | validates |


**Impacted Implementation Nodes**:
- **RBACManagementPage** (interface): New RBAC UI page. Main management interface for role assignm
- **AdminPage** (interface): Add RBAC Management tab containing RBACManagementPage compon

### Story: Story 3.2 - Assignment Creation Workflow (New Roles)
**Epic**: Epic 3
**Functional Requirements**: FR3.2
**Acceptance Criteria**: AC01, AC20

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 2 |
| New Implementation Nodes | 2 |
| Modified Implementation Nodes | 0 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 6 (4 from other stories) |
| Schema Impact | 0 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Assignment Creation Workflow** (AC01): new
  - **Validates** (3 nodes):
    - `ni0085` **CreateAssignmentModal** (interface) → *Story 3.2*: Assignment Creation Workflow (
    - `nl0505` **GET /api/v1/rbac/roles** (logic) → *Story 3.2*: Assignment Creation Workflow (
    - `nl0507` **POST /api/v1/rbac/assignments** (logic) → *Story 1.3*: Implement Core Role Assignment
  - **Depends on** (3 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ns0010` **Role** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment

**Cross-Story Validation Summary**:
This story's test specifications validate **6** nodes total:
- **6** implementation nodes (interface/schema/logic)
- **4** from other stories

**Validated Nodes by Story**:
*From Story 3.2* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ni0085` | CreateAssignmentModal | interface | new | validates |
| `nl0505` | GET /api/v1/rbac/roles | logic | new | validates |

*From Story 1.3* (3 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0507` | POST /api/v1/rbac/assignments | logic | new | validates |
| `ns0013` | UserRoleAssignment | schema | new | depends_on |
| `nl0504` | RBACService | logic | new | depends_on |

*From Story 1.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0010` | Role | schema | new | depends_on |


**Impacted Implementation Nodes**:
- **GET /api/v1/rbac/roles** (logic): New RBAC API endpoint. List all available roles (Admin, Owne
- **CreateAssignmentModal** (interface): New RBAC UI component. Guided wizard for creating role assig

### Story: Story 3.3 - Assignment List View and Filtering
**Epic**: Epic 3
**Functional Requirements**: FR3.3
**Acceptance Criteria**: AC01, AC21

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 2 |
| New Implementation Nodes | 2 |
| Modified Implementation Nodes | 0 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 4 (2 from other stories) |
| Schema Impact | 0 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Assignment List and Filtering** (AC01): new
  - **Validates** (2 nodes):
    - `ni0084` **AssignmentListView** (interface) → *Story 3.3*: Assignment List View and Filte
    - `nl0506` **GET /api/v1/rbac/assignments** (logic) → *Story 3.3*: Assignment List View and Filte
  - **Depends on** (2 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment

**Cross-Story Validation Summary**:
This story's test specifications validate **4** nodes total:
- **4** implementation nodes (interface/schema/logic)
- **2** from other stories

**Validated Nodes by Story**:
*From Story 1.3* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0013` | UserRoleAssignment | schema | new | depends_on |
| `nl0504` | RBACService | logic | new | depends_on |

*From Story 3.3* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ni0084` | AssignmentListView | interface | new | validates |
| `nl0506` | GET /api/v1/rbac/assignments | logic | new | validates |


**Impacted Implementation Nodes**:
- **GET /api/v1/rbac/assignments** (logic): New RBAC API endpoint. List role assignments with optional f
- **AssignmentListView** (interface): New RBAC UI component. Displays role assignments in filterab

### Story: Story 3.4 - Assignment Editing and Removal
**Epic**: Epic 3
**Functional Requirements**: FR3.4
**Acceptance Criteria**: AC01, AC22

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 1 |
| New Implementation Nodes | 1 |
| Modified Implementation Nodes | 0 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 5 (4 from other stories) |
| Schema Impact | 0 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Assignment Edit and Delete** (AC01): new
  - **Validates** (3 nodes):
    - `ni0084` **AssignmentListView** (interface) → *Story 3.3*: Assignment List View and Filte
    - `nl0508` **PATCH /api/v1/rbac/assignments** (logic) → *Story 3.4*: Assignment Editing and Removal
    - `nl0509` **DELETE /api/v1/rbac/assignment** (logic) → *Story 1.4*: Default Project Owner Immutabi
  - **Depends on** (2 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment

**Cross-Story Validation Summary**:
This story's test specifications validate **5** nodes total:
- **5** implementation nodes (interface/schema/logic)
- **4** from other stories

**Validated Nodes by Story**:
*From Story 3.3* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ni0084` | AssignmentListView | interface | new | validates |

*From Story 3.4* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0508` | PATCH /api/v1/rbac/assignments | logic | new | validates |

*From Story 1.4* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0509` | DELETE /api/v1/rbac/assignment | logic | new | validates |

*From Story 1.3* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0013` | UserRoleAssignment | schema | new | depends_on |
| `nl0504` | RBACService | logic | new | depends_on |


**Impacted Implementation Nodes**:
- **PATCH /api/v1/rbac/assignments/{id}** (logic): New RBAC API endpoint. Update role assignment (change role).

### Story: Story 3.5 - Flow Role Inheritance Display Rule
**Epic**: Epic 3
**Functional Requirements**: FR3.5
**Acceptance Criteria**: AC01

**Note**: This story contains only validation/test specifications (no implementation nodes)

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 0 |
| New Implementation Nodes | 0 |
| Modified Implementation Nodes | 0 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 3 (3 from other stories) |
| Schema Impact | 0 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Flow Role Inheritance Display** (AC01): new
  - **Validates** (1 nodes):
    - `ni0084` **AssignmentListView** (interface) → *Story 3.3*: Assignment List View and Filte
  - **Depends on** (2 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment

**Cross-Story Validation Summary**:
This story's test specifications validate **3** nodes total:
- **3** implementation nodes (interface/schema/logic)
- **3** from other stories

**Validated Nodes by Story**:
*From Story 1.3* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0013` | UserRoleAssignment | schema | new | depends_on |
| `nl0504` | RBACService | logic | new | depends_on |

*From Story 3.3* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ni0084` | AssignmentListView | interface | new | validates |


### Story: Story 5.1 - Role Assignment and Enforcement Latency
**Epic**: Epic 5
**Functional Requirements**: FR5.1
**Acceptance Criteria**: AC01 - CanAccess Latency, AC02 - Assignment Latency

**Note**: This story contains only validation/test specifications (no implementation nodes)

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 0 |
| New Implementation Nodes | 0 |
| Modified Implementation Nodes | 0 |
| Validation Nodes (Test Specs) | 2 (2 new) |
| Nodes Validated by This Story | 7 (7 from other stories) |
| Schema Impact | 0 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify CanAccess Check Latency** (AC01 - CanAccess Latency): new
  - **Validates** (2 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `nl0510` **GET /api/v1/rbac/check-permiss** (logic) → *Story 2.1*: Core CanAccess Authorization S
  - **Depends on** (4 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ns0010` **Role** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0011` **Permission** (schema) → *Story 1.1*: Define & Persist Core Permissi
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment
- **Verify Assignment Creation Latency** (AC02 - Assignment Latency): new
  - **Validates** (2 nodes):
    - `nl0507` **POST /api/v1/rbac/assignments** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `nl0508` **PATCH /api/v1/rbac/assignments** (logic) → *Story 3.4*: Assignment Editing and Removal
  - **Depends on** (2 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ns0013` **UserRoleAssignment** (schema) → *Story 1.3*: Implement Core Role Assignment

**Cross-Story Validation Summary**:
This story's test specifications validate **7** nodes total:
- **7** implementation nodes (interface/schema/logic)
- **7** from other stories

**Validated Nodes by Story**:
*From Story 1.1* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0010` | Role | schema | new | depends_on |
| `ns0011` | Permission | schema | new | depends_on |

*From Story 2.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0510` | GET /api/v1/rbac/check-permiss | logic | new | validates |

*From Story 1.3* (3 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ns0013` | UserRoleAssignment | schema | new | depends_on |
| `nl0504` | RBACService | logic | new | validates |
| `nl0507` | POST /api/v1/rbac/assignments | logic | new | validates |

*From Story 3.4* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0508` | PATCH /api/v1/rbac/assignments | logic | new | validates |


### Story: Story 5.2 - System Uptime and Availability
**Epic**: Epic 5
**Functional Requirements**: FR5.2
**Acceptance Criteria**: AC01

**Note**: This story contains only validation/test specifications (no implementation nodes)

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 0 |
| New Implementation Nodes | 0 |
| Modified Implementation Nodes | 0 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 7 (7 from other stories) |
| Schema Impact | 0 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify System Availability** (AC01): new
  - **Validates** (7 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `nl0505` **GET /api/v1/rbac/roles** (logic) → *Story 3.2*: Assignment Creation Workflow (
    - `nl0506` **GET /api/v1/rbac/assignments** (logic) → *Story 3.3*: Assignment List View and Filte
    - `nl0507` **POST /api/v1/rbac/assignments** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `nl0508` **PATCH /api/v1/rbac/assignments** (logic) → *Story 3.4*: Assignment Editing and Removal
    - `nl0509` **DELETE /api/v1/rbac/assignment** (logic) → *Story 1.4*: Default Project Owner Immutabi
    - `nl0510` **GET /api/v1/rbac/check-permiss** (logic) → *Story 2.1*: Core CanAccess Authorization S
  - **Depends on** (0 nodes):
    *(none)*

**Cross-Story Validation Summary**:
This story's test specifications validate **7** nodes total:
- **7** implementation nodes (interface/schema/logic)
- **7** from other stories

**Validated Nodes by Story**:
*From Story 3.4* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0508` | PATCH /api/v1/rbac/assignments | logic | new | validates |

*From Story 1.3* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0507` | POST /api/v1/rbac/assignments | logic | new | validates |
| `nl0504` | RBACService | logic | new | validates |

*From Story 1.4* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0509` | DELETE /api/v1/rbac/assignment | logic | new | validates |

*From Story 2.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0510` | GET /api/v1/rbac/check-permiss | logic | new | validates |

*From Story 3.2* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0505` | GET /api/v1/rbac/roles | logic | new | validates |

*From Story 3.3* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0506` | GET /api/v1/rbac/assignments | logic | new | validates |


### Story: Story 5.3 - Readiness Time (Initial Load)
**Epic**: Epic 5
**Functional Requirements**: FR5.3
**Acceptance Criteria**: AC01

**Note**: This story contains only validation/test specifications (no implementation nodes)

| Metric | Value |
|--------|-------|
| Implementation Nodes Impacted | 0 |
| New Implementation Nodes | 0 |
| Modified Implementation Nodes | 0 |
| Validation Nodes (Test Specs) | 1 (1 new) |
| Nodes Validated by This Story | 4 (4 from other stories) |
| Schema Impact | 0 |
| API Impact | 0 |

**Validation Nodes (Gherkin Test Specifications)**:
- **Verify Editor Load Time with RBAC** (AC01): new
  - **Validates** (3 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `ni0006` **CollectionPage** (interface) → *Story 2.2*: Enforce Read/View Permission &
    - `ni0009` **FlowPage** (interface) → *Story 2.2*: Enforce Read/View Permission &
  - **Depends on** (2 nodes):
    - `nl0504` **RBACService** (logic) → *Story 1.3*: Implement Core Role Assignment
    - `nl0510` **GET /api/v1/rbac/check-permiss** (logic) → *Story 2.1*: Core CanAccess Authorization S

**Cross-Story Validation Summary**:
This story's test specifications validate **4** nodes total:
- **4** implementation nodes (interface/schema/logic)
- **4** from other stories

**Validated Nodes by Story**:
*From Story 2.2* (2 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `ni0006` | CollectionPage | interface | modified | validates |
| `ni0009` | FlowPage | interface | modified | validates |

*From Story 2.1* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0510` | GET /api/v1/rbac/check-permiss | logic | new | depends_on |

*From Story 1.3* (1 nodes):
| Node ID | Name | Type | Impact Status | Relationship |
|---------|------|------|---------------|--------------|
| `nl0504` | RBACService | logic | new | validates |


---

## Detailed Node Impact List

### New Nodes

| ID | Name | Type | Story | FRs | Summary |
|----|------|------|-------|-----|---------|
| ns0010 | Role | schema | Story 1.1 | FR1.1, FR1.2 | New RBAC schema node. Defines 4 predefin |
| ns0011 | Permission | schema | Story 1.1 | FR1.1, FR1.2 | New RBAC schema node. Defines 8 base per |
| ns0012 | RolePermission | schema | Story 1.2 | FR1.3, FR1.4 | New RBAC schema node. Maps roles to perm |
| ns0013 | UserRoleAssignment | schema | Story 1.3 | FR1.5 | New RBAC schema node. Core assignment lo |
| nl0504 | RBACService | logic | Story 1.3 | FR1.5 | New RBAC core service. Provides can_acce |
| nl0505 | GET /api/v1/rbac/roles | logic | Story 3.2 | FR3.2 | New RBAC API endpoint. List all availabl |
| nl0506 | GET /api/v1/rbac/assignme | logic | Story 3.3 | FR3.3 | New RBAC API endpoint. List role assignm |
| nl0507 | POST /api/v1/rbac/assignm | logic | Story 1.3 | FR1.5 | New RBAC API endpoint. Create new role a |
| nl0508 | PATCH /api/v1/rbac/assign | logic | Story 3.4 | FR3.4 | New RBAC API endpoint. Update role assig |
| nl0509 | DELETE /api/v1/rbac/assig | logic | Story 1.4 | FR1.6 | New RBAC API endpoint. Delete role assig |
| nl0510 | GET /api/v1/rbac/check-pe | logic | Story 2.1 | FR2.1 | New RBAC API endpoint. Check if current  |
| ni0083 | RBACManagementPage | interface | Story 3.1 | FR3.1 | New RBAC UI page. Main management interf |
| ni0084 | AssignmentListView | interface | Story 3.3 | FR3.3 | New RBAC UI component. Displays role ass |
| ni0085 | CreateAssignmentModal | interface | Story 3.2 | FR3.2 | New RBAC UI component. Guided wizard for |
| ni0086 | RBACGuard | interface | Story 2.2 | FR2.2 | New RBAC UI component. Declarative route |
| ni0087 | usePermission | interface | Story 2.2 | FR2.2 | New RBAC hook. Reusable permission check |

### Modified Nodes

| ID | Name | Type | Story | FRs | Summary |
|----|------|------|-------|-----|---------|
| ni0001 | AdminPage | interface | Story 3.1 | FR3.1 | Add RBAC Management tab containing RBACM |
| ni0006 | CollectionPage | interface | Story 2.2 | FR2.2 | Add permission-based filtering using use |
| ni0009 | FlowPage | interface | Story 2.2 | FR2.2 | Add read-only mode support using usePerm |
| ns0001 | User | schema | Story 1.3 | FR1.5 | Add role_assignments relationship to Use |
| ns0002 | Flow | schema | Story 1.6 | FR1.8 | No structural changes. Permission checks |
| ns0003 | Folder | schema | Story 1.6 | FR1.8 | No structural changes. Requires immutabi |
| nl0004 | Create Flow Endpoint Hand | logic | Story 1.5 | FR1.7 | Add auto-assignment of Owner role to cre |
| nl0005 | List Flows Endpoint Handl | logic | Story 2.2 | FR2.2 | Replace in-query user_id filtering with  |
| nl0007 | Get Flow by ID Endpoint H | logic | Story 2.2 | FR2.2 | Replace in-query user_id filtering with  |
| nl0009 | Update Flow Endpoint Hand | logic | Story 2.4 | FR2.4 | Replace in-query user_id filtering with  |
| nl0010 | Delete Flow Endpoint Hand | logic | Story 2.5 | FR2.5 | Replace in-query user_id filtering with  |
| nl0012 | Upload Flows Endpoint Han | logic | Story 2.2 | FR2.2 | Add can_access(UPDATE, PROJECT, folder_i |
| nl0042 | Create Project Endpoint H | logic | - | - | Add auto-assignment of Owner role with i |
| nl0043 | List Projects Endpoint Ha | logic | - | - | Replace in-query user_id filtering with  |
| nl0044 | Get Project by ID Endpoin | logic | - | - | Replace in-query user_id filtering with  |
| nl0045 | Update Project Endpoint H | logic | - | - | Replace in-query user_id filtering with  |
| nl0046 | Delete Project Endpoint H | logic | - | - | Replace in-query user_id filtering with  |
| nl0061 | Build Flow Endpoint Handl | logic | - | - | Add can_access(READ, FLOW, flow_id) chec |

---

## Risk Heatmap

| Epic | Blast Radius | Regression Risk | Data Risk | API Risk | Overall |
|------|--------------|-----------------|-----------|----------|---------|
| Core RBAC Data Model and Default As | High | Critical | Critical | Low | Critical |
| RBAC Enforcement Engine & Runtime C | High | Critical | Low | Low | Critical |
| Web-based Admin Management Interfac | High | Critical | Low | Low | Critical |
| Non-Functional Requirements | Low | Low | Low | Low | Low |

---

## Appendix: Raw Metrics Data

See `.alucify/impact-analysis/impact-analysis-data.json` for complete metric data in JSON format.
