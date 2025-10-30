# RBAC Prototype Integration Plan
## Comprehensive Plan to Sync AppGraph v17 with Prototype Implementation

**Created**: 2025-10-30
**Version**: 1.0
**Author**: Claude Code Analysis

---

## Executive Summary

This document provides a detailed plan to incorporate changes from the RBAC prototype (`~/GB/rbac-prototype`) back into the main LangBuilder AppGraph (`AppGraph_langbuilder_rbac_impact_v17_comprehensive_uidl_all.json`). The analysis reveals that the current LangBuilder codebase has **already implemented** most RBAC components but they are **not yet integrated** with the AdminPage via tabs, which is the primary contribution of the prototype.

### Key Findings

1. **Current LangBuilder Status**: RBAC components exist but are disconnected
   - RBACManagementPage is fully implemented (270 lines)
   - AssignmentListView is fully implemented (255 lines)
   - CreateAssignmentModal is fully implemented (388 lines)
   - NO tab navigation connecting User Management and RBAC Management

2. **Prototype Status**: Next.js implementation with mock data
   - Two-tab layout: User Management + Access Management
   - Mock data (3 users, 3 role assignments)
   - Uses Next.js App Router and modern React patterns

3. **AppGraph v17 Status**: Comprehensive RBAC specification
   - 623 total nodes, 14,232 edges
   - 18 modified nodes, 36 new nodes (including validation)
   - 100% PRD coverage (all 19 stories)
   - AdminPage (ni0001) specifies: "Add RBAC Management tab containing RBACManagementPage component"
   - UIDL compliance with teleporthq.io standard

### Integration Scope

**Primary Change**: Add tab navigation to AdminPage to connect existing User Management and RBAC Management components.

**Impact**: MINIMAL - This is primarily a UI structural change, not a functional change.

---

## Part 1: Detailed Analysis

### 1.1 RBAC Requirements Overview (PRD)

**Source**: `/Users/dongmingjiang/GB/LangBuilder/.alucify/RBAC Requirements Overview.md`

**4 Epics, 19 Stories**:

1. **Epic 1: Core RBAC Data Model** (6 stories)
   - Story 1.1: Define Core Permissions (CRUD) and Scopes (Flow, Project)
   - Story 1.2: Define Default Roles (Admin, Owner, Editor, Viewer)
   - Story 1.3: Implement Core Role Assignment Logic
   - Story 1.4: Default Project Owner Immutability Check
   - Story 1.5: Global Project Creation & New Entity Owner Mutability
   - Story 1.6: Project to Flow Role Extension Rule

2. **Epic 2: RBAC Enforcement Engine** (5 stories)
   - Story 2.1: Core `CanAccess` Authorization Service
   - Story 2.2: Enforce Read/View Permission & List Visibility
   - Story 2.3: Enforce Create Permission
   - Story 2.4: Enforce Update/Edit Permission
   - Story 2.5: Enforce Delete Permission

3. **Epic 3: Admin Management Interface** (5 stories)
   - **Story 3.1: RBAC Management Section in Admin Page** ⬅️ **CRITICAL FOR INTEGRATION**
     - "Admin Page has two tabs now with User Management Section (default) and RBAC Management section"
     - Deep link support: `/admin?tab=rbac` or `/admin/rbac`
   - Story 3.2: Assignment Creation Workflow
   - Story 3.3: Assignment List View and Filtering
   - Story 3.4: Assignment Editing and Removal
   - Story 3.5: Flow Role Inheritance Display Rule

4. **Epic 5: Non-Functional Requirements** (3 stories)
   - Story 5.1: Authorization latency (<50ms p95, assignment API <200ms p95)
   - Story 5.2: System uptime (99.9% availability)
   - Story 5.3: Page readiness (<2.5s p95)

**Critical Requirement (Story 3.1)**:
```
Given: Admin Page exists with User Management section
When: RBAC Management section gets added
Then: Admin Page has TWO TABS
  - User Management Section (default, opens first)
  - RBAC Management section
And: Deep link exists for RBAC management section
```

### 1.2 Architecture Analysis

**Source**: `/Users/dongmingjiang/GB/LangBuilder/.alucify/rbac-architecture-corrected-final.md` (first 400 lines)

**Current Authorization Model** (Critical Clarifications):
- **In-Query Filtering**: Authorization via `WHERE Flow.user_id == user_id` in SQL queries
- **No Superuser Bypass**: `is_superuser` does NOT grant automatic access to flows/projects (only user management)
- **Binary Access**: All-or-nothing ownership (full CRUD on own resources, zero access to others)
- **404 Instead of 403**: Returns "not found" for inaccessible resources

**Folder Naming Clarification**:
- **"Starter Projects"** (plural): System-wide template folder (`STARTER_FOLDER_NAME`), NOT subject to immutability
- **"Starter Project"** (singular): User's default project folder (`DEFAULT_FOLDER_NAME`), Owner role IS immutable

**New RBAC Data Models**:
```python
class Role(SQLModel, table=True):
    id: UUID
    name: str  # Admin, Owner, Editor, Viewer
    description: str | None
    is_global: bool  # True for Admin only
    is_system: bool  # True for all 4 default roles

class Permission(SQLModel, table=True):
    id: UUID
    action: str  # CREATE, READ, UPDATE, DELETE
    scope_type: str  # flow, project
    # Unique constraint: (action, scope_type)

class RolePermission(SQLModel, table=True):
    id: UUID
    role_id: UUID
    permission_id: UUID
    # Unique constraint: (role_id, permission_id)

class UserRoleAssignment(SQLModel, table=True):
    id: UUID
    user_id: UUID
    role_id: UUID
    scope_type: str  # "flow" or "project"
    scope_id: UUID
    is_immutable: bool  # True for default project owner
    created_at: datetime
    # Unique constraint: (user_id, role_id, scope_type, scope_id)
    # Index: (user_id, scope_type, scope_id)
```

**Technology Stack**:
- Backend: Python/FastAPI, SQLModel, AsyncSession
- Frontend: React/TypeScript with shadcn/ui components
- Database: PostgreSQL
- Prototype: Next.js 16 with App Router, React 19, Tailwind CSS 4

### 1.3 Prototype Codebase Analysis

**Source**: `~/GB/rbac-prototype/`

**Directory Structure**:
```
rbac-prototype/
├── app/
│   ├── admin/page.tsx           # AdminPage with tabs ⬅️ KEY CHANGE
│   ├── page.tsx                 # Home (redirects)
│   └── layout.tsx
├── components/
│   ├── authorization/
│   │   └── RBACGuard.tsx        # Permission-based rendering
│   └── rbac/
│       ├── AssignmentListView.tsx
│       └── CreateAssignmentModal.tsx
├── hooks/
│   └── usePermission.ts         # Permission checking hook
└── RBAC_Prototype_UIDL.json     # UIDL specification (115KB)
```

**Key Implementation: AdminPage with Tabs** (`app/admin/page.tsx`):
```typescript
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function AdminPage() {
  return (
    <div className="container mx-auto p-6">
      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">User Management</TabsTrigger>
          <TabsTrigger value="rbac">Access Management</TabsTrigger>
        </TabsList>

        <TabsContent value="users">
          {/* User Management content */}
        </TabsContent>

        <TabsContent value="rbac">
          {/* RBAC Management content */}
        </TabsContent>
      </Tabs>
    </div>
  )
}
```

**Mock Data**:
```typescript
const MOCK_USERS = [
  { id: "1", username: "john_doe", email: "john@example.com", status: "active" },
  { id: "2", username: "jane_smith", email: "jane@example.com", status: "active" },
  { id: "3", username: "bob_wilson", email: "bob@example.com", status: "inactive" }
]

const MOCK_ASSIGNMENTS = [
  { id: "1", username: "john_doe", role: "admin", scope: "global", entityId: "*" },
  { id: "2", username: "jane_smith", role: "editor", scope: "project", entityId: "proj-1" },
  { id: "3", username: "bob_wilson", role: "viewer", scope: "flow", entityId: "flow-1" }
]
```

**Type Definitions**:
```typescript
interface User {
  id: string
  username: string
  email: string
  status: "active" | "inactive"
  createdAt: string
}

interface RoleAssignment {
  id: string
  username: string
  role: "admin" | "editor" | "viewer"
  scope: "global" | "project" | "flow"
  entityId: string
  immutable: boolean
}
```

### 1.4 Original LangBuilder Codebase Analysis

**Source**: `/Users/dongmingjiang/GB/LangBuilder/src/frontend/src/pages/AdminPage/`

**File Structure**:
```
AdminPage/
├── index.tsx                    # Main AdminPage (503 lines) ⬅️ NO TABS
├── RBACManagementPage/
│   ├── index.tsx               # RBAC page (270 lines) ✅ EXISTS
│   ├── AssignmentListView.tsx  # List component (255 lines) ✅ EXISTS
│   └── CreateAssignmentModal.tsx # Creation wizard (388 lines) ✅ EXISTS
└── LoginPage/
    └── index.tsx               # Admin login (86 lines)
```

**Current AdminPage Structure** (`index.tsx`):
```typescript
// NO TABS - Single page layout
export default function AdminPage() {
  return (
    <div className="flex h-full flex-col space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2>Admin Page</h2>
          <p>Navigate through this section to efficiently oversee all application users.</p>
        </div>
        <Button onClick={handleNewUser}>New User</Button>
      </div>

      {/* Search and Filter */}
      <Input placeholder="Search by username" />

      {/* User Table */}
      <Table>
        {/* User rows with inline Active/Superuser toggles */}
      </Table>

      {/* Pagination */}
      <PaginatorComponent />
    </div>
  )
}
```

**CRITICAL FINDING**:
- ❌ NO tabs implementation
- ✅ RBACManagementPage EXISTS but is NOT imported/used
- ✅ All RBAC components are fully implemented
- ✅ Tabs component IS available: `import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"`

**Existing RBAC Components** (Complete and Production-Ready):

1. **RBACManagementPage** (270 lines):
   - Header with title and description
   - "New Assignment" button
   - Available Roles reference card
   - AssignmentListView component
   - Edit Assignment modal
   - Full API integration with real data

2. **AssignmentListView** (255 lines):
   - Three filters: username, role, scope
   - Clear filters button
   - Inheritance info banner
   - Table: User, Role, Scope, Entity, Created, Actions
   - Immutable assignment protection (lock icon)
   - Edit/Delete actions with confirmation modals

3. **CreateAssignmentModal** (388 lines):
   - 4-step wizard:
     1. Select User (from existing users via API)
     2. Select Scope (Project/Flow) and Entity (from real data via API)
     3. Select Role (Admin/Owner/Editor/Viewer with descriptions)
     4. Review and Confirm
   - Progress indicator
   - Validation at each step
   - Edit mode support

**API Integration** (Production-Ready):
```typescript
// User Management
useGetUsers({ skip, limit })
useAddUser(user)
useUpdateUser({ user_id, user })
useDeleteUsers({ user_id })

// RBAC
useGetRoles()
useGetAssignments({ user_id?, role_id?, scope?, scope_id?, skip?, limit? })
usePostAssignment(data)
usePatchAssignment({ assignmentId, data })
useDeleteAssignment(assignmentId)

// Other
useGetFlows()
useGetFolders()
```

### 1.5 AppGraph v17 Analysis

**Source**: `/Users/dongmingjiang/GB/LangBuilder/.alucify/AppGraph_langbuilder_rbac_impact_v17_comprehensive_uidl_all.json`

**Metadata**:
- Version: 4.7-comprehensive-uidl-all
- Generated: 2025-10-25
- Total Nodes: 623
- Total Edges: 14,232
- UIDL Standard: teleporthq.io v1.0
- PRD Coverage: 100% (all 19 stories)
- Production Ready: true

**Node Distribution**:
- Interface: 84 nodes
- Schema: 13 nodes
- Logic: 506 nodes
- Validation: 20 nodes (Gherkin scenarios)

**Impact Analysis Status**:
- Modified: 18 nodes
- New: 36 nodes
- Intact: 569 nodes

**Critical Node: ni0001 (AdminPage)**:
```json
{
  "id": "ni0001",
  "type": "interface",
  "name": "AdminPage",
  "path": "src/frontend/src/pages/AdminPage/index.tsx",
  "prd_references": ["Epic 3 Story 3.1"],
  "impact_analysis_status": "modified",
  "impact_analysis": "Add RBAC Management tab containing RBACManagementPage component. Update navigation to include /admin route with /rbac sub-route.",
  "uidl_conceptual": {
    "name": "AdminPage",
    "stateDefinitions": {
      "inputValue": { "type": "string", "defaultValue": "" },
      "size": { "type": "any", "defaultValue": null },
      "index": { "type": "any", "defaultValue": null },
      "totalRowsCount": { "type": "number", "defaultValue": 0 },
      "filterUserList": { "type": "any", "defaultValue": null }
    }
  }
}
```

**New RBAC Interface Nodes**:

1. **ni0066 - RBACManagementPage**:
   - Route: `/admin` with sub-route `/rbac`
   - Path: `src/frontend/src/pages/AdminPage/RBACManagementPage/index.tsx`
   - PRD: Epic 3 Story 3.1
   - Impact: "New RBAC UI page. Main management interface for role assignments."
   - State: editModalOpen, selectedAssignment, newRoleId
   - Lines: 269

2. **ni0067 - AssignmentListView**:
   - Path: `src/frontend/src/pages/AdminPage/RBACManagementPage/AssignmentListView.tsx`
   - PRD: Epic 3 Story 3.2
   - Impact: "New RBAC UI component. Displays role assignments in filterable table."

3. **ni0068 - CreateAssignmentModal**:
   - Path: `src/frontend/src/pages/AdminPage/RBACManagementPage/CreateAssignmentModal.tsx`
   - PRD: Epic 3 Story 3.3
   - Impact: "New RBAC UI component. Guided wizard for creating role assignments. 4-step workflow."

4. **ni0069 - RBACGuard**:
   - Path: `src/frontend/src/components/authorization/RBACGuard.tsx`
   - PRD: Epic 2 Story 2.2
   - Impact: "New RBAC UI component. Declarative route protection based on permissions."

5. **ni0070 - usePermission**:
   - Path: `src/frontend/src/hooks/usePermission.ts`
   - PRD: Epic 2 Story 2.2
   - Impact: "New RBAC hook. Reusable permission check for UI rendering decisions."

**Modified Nodes (Sample)**:

1. **ni0002 - FlowsPage**: "Add permission-based filtering using usePermission hook"
2. **ni0003 - FlowEditor**: "Add read-only mode support using usePermission hook"
3. **ns0001 - User**: "Add role_assignments relationship to UserRoleAssignment"
4. **nl0101 - create_flow**: "Add auto-assignment of Owner role to creator"
5. **nl0102 - read_flows**: "Replace in-query user_id filtering with permission-based filtering"

---

## Part 2: Gap Analysis

### 2.1 What Prototype Has vs Current Implementation

| Feature | Prototype | Current LangBuilder | AppGraph v17 | Status |
|---------|-----------|-------------------|--------------|---------|
| **Tab Navigation** | ✅ Implemented | ❌ **MISSING** | ✅ Specified | **GAP** |
| User Management Tab | ✅ As default tab | ✅ As single page | ✅ Specified | Needs restructuring |
| Access Management Tab | ✅ As second tab | ❌ Not accessible | ✅ Specified | Needs integration |
| RBACManagementPage | ✅ Mock data | ✅ **Production-ready** | ✅ Specified | Already exists |
| AssignmentListView | ✅ Mock data | ✅ **Production-ready** | ✅ Specified | Already exists |
| CreateAssignmentModal | ✅ 4-step wizard | ✅ **4-step wizard** | ✅ Specified | Already exists |
| RBACGuard | ✅ Mock check | ✅ **Real API** | ✅ Specified | Already exists |
| usePermission hook | ✅ Mock check | ✅ **Real API** | ✅ Specified | Already exists |
| API Integration | ❌ Mock only | ✅ **Full backend** | ✅ Specified | Already exists |
| Data Models | ❌ Mock types | ✅ **SQLModel** | ✅ Specified | Already exists |

### 2.2 Summary

**CRITICAL INSIGHT**: The current LangBuilder codebase has **MORE** than the prototype:
- ✅ All RBAC components are production-ready (not mocks)
- ✅ Full API integration with real backend
- ✅ Complete permission checking and enforcement
- ✅ Immutability protection for default project owner
- ✅ Multi-filter support with server-side filtering

**ONLY MISSING**: Tab navigation structure to connect User Management and RBAC Management

**Prototype Contribution**: Demonstrates the UX pattern for tab-based navigation (reference implementation)

---

## Part 3: Integration Plan

### 3.1 Overview

**Goal**: Add tab navigation to AdminPage to make RBACManagementPage accessible alongside User Management.

**Approach**: Minimal structural change - wrap existing content in tabs component.

**Effort**: LOW (single file change, ~50 lines of code)

**Risk**: MINIMAL (no logic changes, pure UI restructuring)

### 3.2 Implementation Steps

#### Step 1: Modify AdminPage (`src/frontend/src/pages/AdminPage/index.tsx`)

**File**: `/Users/dongmingjiang/GB/LangBuilder/src/frontend/src/pages/AdminPage/index.tsx`

**Changes**:

1. **Import RBACManagementPage and Tabs**:
```typescript
// Add new imports
import RBACManagementPage from "./RBACManagementPage"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
```

2. **Restructure Component**:
```typescript
export default function AdminPage() {
  // Existing state and hooks
  const [inputValue, setInputValue] = useState("")
  const [size, setSize] = useState(null)
  const [index, setIndex] = useState(null)
  const [totalRowsCount, setTotalRowsCount] = useState(0)
  const [filterUserList, setFilterUserList] = useState(null)
  // ... all existing state

  return (
    <div className="flex h-full flex-col space-y-6 p-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <IconComponent name="Shield" className="h-8 w-8" />
            Admin Page
          </h2>
          <p className="text-muted-foreground">
            Manage users and role-based access control for the application
          </p>
        </div>
      </div>

      {/* Tab Navigation */}
      <Tabs defaultValue="users" className="flex-1">
        <TabsList>
          <TabsTrigger value="users">User Management</TabsTrigger>
          <TabsTrigger value="rbac">Access Management</TabsTrigger>
        </TabsList>

        {/* User Management Tab */}
        <TabsContent value="users" className="space-y-4">
          {/* Move all existing AdminPage content here */}
          <div className="flex items-center justify-between">
            <Input
              placeholder="Search by username"
              value={inputValue}
              onChange={handleSearchInput}
              className="max-w-sm"
            />
            <Button onClick={handleNewUser}>
              <IconComponent name="Plus" className="mr-2 h-4 w-4" />
              New User
            </Button>
          </div>

          <Table>
            {/* All existing user table content */}
          </Table>

          <PaginatorComponent
            pageSize={size ?? PAGINATION_SIZE}
            pageIndex={index ?? PAGINATION_PAGE}
            totalRowsCount={totalRowsCount}
            paginate={(pageSize, pageIndex) => {
              setSize(pageSize)
              setIndex(pageIndex)
            }}
          />
        </TabsContent>

        {/* RBAC Management Tab */}
        <TabsContent value="rbac" className="space-y-4">
          <RBACManagementPage />
        </TabsContent>
      </Tabs>

      {/* Modals remain outside tabs */}
      {openUserModal && (
        <UserManagementModal
          open={openUserModal}
          setOpen={setOpenUserModal}
          asChild
        >
          <></>
        </UserManagementModal>
      )}

      {/* Other existing modals */}
    </div>
  )
}
```

**Key Points**:
- ✅ Preserve all existing state and logic
- ✅ Move user management content into first tab
- ✅ Add RBACManagementPage to second tab
- ✅ Keep modals outside tabs (shared across both)
- ✅ Update page description to mention both features
- ✅ Set "users" as default tab (per PRD Story 3.1)

#### Step 2: Update Routing (Optional)

**File**: `/Users/dongmingjiang/GB/LangBuilder/src/App.tsx` (or routing config)

**Purpose**: Support deep linking to RBAC tab per PRD Story 3.1

**Option A: URL Parameter** (Recommended):
```typescript
// In AdminPage, read tab from URL
import { useSearchParams } from "react-router-dom"

export default function AdminPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const defaultTab = searchParams.get("tab") || "users"

  return (
    <Tabs
      defaultValue={defaultTab}
      onValueChange={(value) => setSearchParams({ tab: value })}
    >
      {/* tabs content */}
    </Tabs>
  )
}

// Deep link: /admin?tab=rbac
```

**Option B: Sub-route** (Alternative):
```typescript
// Route configuration
<Route path="/admin">
  <Route index element={<AdminPage defaultTab="users" />} />
  <Route path="rbac" element={<AdminPage defaultTab="rbac" />} />
</Route>

// Deep link: /admin/rbac
```

**Recommendation**: Use Option A (URL parameter) for simplicity and single component management.

#### Step 3: Update AppGraph v17

**File**: `/Users/dongmingjiang/GB/LangBuilder/.alucify/AppGraph_langbuilder_rbac_impact_v17_comprehensive_uidl_all.json`

**Node**: `ni0001 - AdminPage`

**Changes Required**:

1. **Update `impact_analysis_status`**:
   - Change from: `"modified"` (planned)
   - Change to: `"modified"` (implemented) ✅ Already correct

2. **Update `uidl_conceptual`** to reflect tabs:
```json
{
  "id": "ni0001",
  "type": "interface",
  "name": "AdminPage",
  "impact_analysis_status": "modified",
  "impact_analysis": "Add RBAC Management tab containing RBACManagementPage component. Update navigation to include /admin route with /rbac sub-route. IMPLEMENTED.",
  "uidl_conceptual": {
    "name": "AdminPage",
    "node": {
      "type": "element",
      "content": {
        "elementType": "container",
        "semanticType": "page",
        "name": "AdminPage",
        "children": [
          {
            "type": "element",
            "content": {
              "elementType": "Tabs",
              "attrs": {
                "defaultValue": {
                  "type": "static",
                  "content": "users"
                }
              },
              "children": [
                {
                  "type": "element",
                  "content": {
                    "elementType": "TabsList",
                    "children": [
                      {
                        "type": "element",
                        "content": {
                          "elementType": "TabsTrigger",
                          "attrs": { "value": { "type": "static", "content": "users" } },
                          "children": ["User Management"]
                        }
                      },
                      {
                        "type": "element",
                        "content": {
                          "elementType": "TabsTrigger",
                          "attrs": { "value": { "type": "static", "content": "rbac" } },
                          "children": ["Access Management"]
                        }
                      }
                    ]
                  }
                },
                {
                  "type": "element",
                  "content": {
                    "elementType": "TabsContent",
                    "attrs": { "value": { "type": "static", "content": "users" } },
                    "children": [
                      {
                        "type": "dynamic",
                        "content": {
                          "referenceType": "local",
                          "id": "userManagementContent"
                        }
                      }
                    ]
                  }
                },
                {
                  "type": "element",
                  "content": {
                    "elementType": "TabsContent",
                    "attrs": { "value": { "type": "static", "content": "rbac" } },
                    "children": [
                      {
                        "type": "element",
                        "content": {
                          "elementType": "RBACManagementPage",
                          "dependency": "ni0066"
                        }
                      }
                    ]
                  }
                }
              ]
            }
          }
        ]
      }
    },
    "stateDefinitions": {
      "activeTab": {
        "type": "string",
        "defaultValue": "users"
      },
      "inputValue": {
        "type": "string",
        "defaultValue": ""
      },
      "size": {
        "type": "any",
        "defaultValue": null
      },
      "index": {
        "type": "any",
        "defaultValue": null
      },
      "totalRowsCount": {
        "type": "number",
        "defaultValue": 0
      },
      "filterUserList": {
        "type": "any",
        "defaultValue": null
      }
    }
  }
}
```

3. **Add edge**: `ni0001 → ni0066` (composition)
```json
{
  "from": "ni0001",
  "to": "ni0066",
  "type": "composition",
  "label": "contains",
  "impact_analysis_status": "new",
  "description": "AdminPage contains RBACManagementPage as second tab"
}
```

4. **Update metadata**:
```json
{
  "metadata": {
    "version": "4.8-tab-integration",
    "previous_version": "4.7-comprehensive-uidl-all",
    "generated_at": "2025-10-30T[timestamp]",
    "changes": [
      {
        "node": "ni0001",
        "change": "Updated UIDL to include Tabs component structure",
        "implementation_status": "completed"
      },
      {
        "edge": "ni0001 → ni0066",
        "change": "Added composition edge for tab integration",
        "implementation_status": "completed"
      }
    ],
    "statistics": {
      "nodes": {
        "total": 623,
        "by_impact_analysis_status": {
          "modified": 18,
          "intact": 569,
          "new": 36
        }
      },
      "edges": {
        "total": 14233,
        "by_impact_analysis_status": {
          "modified": 0,
          "intact": 14069,
          "new": 164
        }
      }
    }
  }
}
```

#### Step 4: Testing

**Test Cases** (Based on PRD Story 3.1):

1. **Default Tab Display**:
   ```
   Given: User navigates to /admin
   When: Page loads
   Then: User Management tab should be active and visible
   And: Access Management tab should be visible but inactive
   ```

2. **Tab Switching**:
   ```
   Given: User is on User Management tab
   When: User clicks Access Management tab
   Then: RBAC Management content should be displayed
   And: User Management content should be hidden
   And: URL should update to /admin?tab=rbac (if using URL params)
   ```

3. **Deep Linking to RBAC**:
   ```
   Given: User navigates to /admin?tab=rbac
   When: Page loads
   Then: Access Management tab should be active
   And: RBAC Management content should be displayed
   ```

4. **Non-Admin Access**:
   ```
   Given: User is not a superuser/admin
   When: User attempts to access /admin
   Then: ProtectedAdminRoute should redirect to home or show "Access Denied"
   And: Neither tab should be accessible
   ```

5. **Tab State Preservation**:
   ```
   Given: User is on Access Management tab
   And: User creates a new assignment
   When: Assignment modal closes
   Then: User should remain on Access Management tab
   And: Assignment list should refresh
   ```

6. **User Management Functionality**:
   ```
   Given: User is on User Management tab
   When: User performs CRUD operations on users
   Then: All existing functionality should work unchanged
   And: Tab state should remain on User Management
   ```

7. **RBAC Management Functionality**:
   ```
   Given: User is on Access Management tab
   When: User performs CRUD operations on assignments
   Then: All existing RBACManagementPage functionality should work
   And: Tab state should remain on Access Management
   ```

**Automated Tests to Add**:

```typescript
// AdminPage.test.tsx
describe("AdminPage Tabs Integration", () => {
  it("should display User Management tab by default", () => {
    render(<AdminPage />)
    expect(screen.getByRole("tab", { name: "User Management", selected: true }))
      .toBeInTheDocument()
    expect(screen.getByRole("tab", { name: "Access Management", selected: false }))
      .toBeInTheDocument()
  })

  it("should switch to Access Management tab on click", async () => {
    render(<AdminPage />)
    const rbacTab = screen.getByRole("tab", { name: "Access Management" })
    await userEvent.click(rbacTab)

    expect(screen.getByRole("tab", { name: "Access Management", selected: true }))
      .toBeInTheDocument()
    expect(screen.getByText("RBAC Management")).toBeInTheDocument()
  })

  it("should support deep linking to RBAC tab", () => {
    render(<AdminPage />, { route: "/admin?tab=rbac" })

    expect(screen.getByRole("tab", { name: "Access Management", selected: true }))
      .toBeInTheDocument()
    expect(screen.getByText("RBAC Management")).toBeInTheDocument()
  })

  it("should preserve tab state during modal operations", async () => {
    render(<AdminPage />, { route: "/admin?tab=rbac" })

    // Open create assignment modal
    await userEvent.click(screen.getByText("New Assignment"))
    expect(screen.getByText("Create Assignment")).toBeInTheDocument()

    // Close modal
    await userEvent.click(screen.getByLabelText("Close"))

    // Verify still on RBAC tab
    expect(screen.getByRole("tab", { name: "Access Management", selected: true }))
      .toBeInTheDocument()
  })
})
```

#### Step 5: Documentation Updates

**Files to Update**:

1. **README.md** (if exists in AdminPage directory):
   ```markdown
   # Admin Page

   The Admin Page provides centralized management for users and access control.

   ## Features

   ### User Management Tab (Default)
   - Create, read, update, delete users
   - Search and filter by username
   - Toggle user active/inactive status
   - Manage superuser privileges
   - Pagination support

   ### Access Management Tab
   - View all role assignments
   - Create new role assignments (4-step wizard)
   - Filter by user, role, or scope
   - Edit role assignments
   - Delete role assignments (with immutability protection)
   - View available roles reference

   ## Access Control
   - Requires `is_superuser = true`
   - Protected by `ProtectedAdminRoute`
   - Deep linking supported: `/admin?tab=rbac`
   ```

2. **CHANGELOG.md**:
   ```markdown
   # Changelog

   ## [Unreleased]

   ### Added
   - Tab navigation to AdminPage (User Management + Access Management)
   - Deep linking support for RBAC tab via URL parameter
   - Integration of RBACManagementPage into main AdminPage

   ### Changed
   - AdminPage restructured to use Tabs component
   - User Management content moved to first tab
   - Page description updated to reflect both features

   ### Migration Notes
   - No breaking changes
   - Existing `/admin` route behavior unchanged (shows User Management by default)
   - New route `/admin?tab=rbac` provides direct access to RBAC features
   ```

3. **PRD Compliance Matrix** (Add to architecture doc):
   ```markdown
   ## Epic 3 Story 3.1 Compliance

   ✅ **Requirement**: "Admin Page has two tabs now with User Management Section (default) and RBAC Management section"
   - Implementation: Tabs component with `defaultValue="users"`
   - Location: `src/frontend/src/pages/AdminPage/index.tsx`

   ✅ **Requirement**: "Deep link exists for RBAC management section"
   - Implementation: URL parameter `/admin?tab=rbac`
   - Alternative: Sub-route `/admin/rbac` (optional)

   ✅ **Requirement**: "When Admin user accesses Admin Page, she should be able to access RBAC Management section"
   - Implementation: Second tab visible to all admin users

   ✅ **Requirement**: "When non-Admin user accesses Admin Page, she should NOT be able to access RBAC Management section"
   - Implementation: ProtectedAdminRoute prevents access to entire page

   ✅ **Requirement**: "When Admin user tries to access deeplink for RBAC management section, she should be able to access it"
   - Implementation: URL parameter routing to second tab

   ✅ **Requirement**: "When non-Admin user tries to access deeplink, system should display Access Denied"
   - Implementation: ProtectedAdminRoute protection applies to all routes
   ```

---

## Part 4: AppGraph Synchronization Strategy

### 4.1 Node Updates Required

**Summary**: 1 node to modify, 1 edge to add

| Node ID | Type | Name | Current Status | Update Required |
|---------|------|------|----------------|-----------------|
| ni0001 | interface | AdminPage | modified (planned) | Update UIDL to include Tabs structure |

**New Edge**:
- `ni0001 → ni0066` (composition): AdminPage contains RBACManagementPage

### 4.2 UIDL Synchronization

**Current UIDL Issues** (ni0001):
- ❌ Does not include Tabs component structure
- ❌ Does not reference RBACManagementPage (ni0066)
- ✅ Has correct state definitions

**Required UIDL Updates**:
1. Add Tabs component to node hierarchy
2. Add TabsList with two TabsTrigger elements
3. Add two TabsContent elements
4. Add RBACManagementPage reference in second TabsContent
5. Add `activeTab` state definition

**UIDL Formats to Update** (all 3):
1. `uidl_conceptual`: High-level semantic structure
2. `ui_blueprint`: JSX structure mapping
3. `ui_physical`: Complete UIDL-compliant specification

### 4.3 Metadata Updates

**Version Bump**:
- Current: `4.7-comprehensive-uidl-all`
- New: `4.8-tab-integration`

**Statistics**:
- Nodes: 623 (no change)
- Edges: 14,233 (+1)
- Modified nodes: 18 (no change)
- New edges: 164 (+1 from 163)

**Audit Log**:
```json
{
  "change": "Tab integration implementation",
  "date": "2025-10-30",
  "nodes_affected": 1,
  "edges_added": 1,
  "description": "Integrated RBACManagementPage into AdminPage via Tabs component",
  "prd_story": "Epic 3 Story 3.1",
  "implementation_status": "completed"
}
```

### 4.4 Validation Checklist

After AppGraph updates, verify:

- [ ] ni0001 UIDL includes complete Tabs structure
- [ ] ni0001 → ni0066 composition edge exists
- [ ] All 3 UIDL formats updated consistently
- [ ] Metadata version bumped correctly
- [ ] Statistics reflect new edge count
- [ ] Audit log includes change entry
- [ ] No other nodes/edges inadvertently modified
- [ ] JSON syntax is valid (run through JSON validator)
- [ ] UIDL complies with teleporthq.io standard
- [ ] PRD reference (Epic 3 Story 3.1) is accurate

---

## Part 5: Risk Assessment and Mitigation

### 5.1 Risk Matrix

| Risk | Likelihood | Impact | Severity | Mitigation |
|------|------------|--------|----------|------------|
| Tab switching breaks user management functionality | Low | High | Medium | Comprehensive testing, preserve all existing state |
| RBACManagementPage fails to render in tab | Low | High | Medium | Test integration, verify imports |
| Deep linking fails | Medium | Low | Low | Test URL parameter routing, add error handling |
| Modal rendering issues (z-index, position) | Medium | Medium | Medium | Keep modals outside tabs, test all modals |
| State conflicts between tabs | Low | Medium | Low | Separate state for each tab, no shared mutable state |
| Performance degradation | Very Low | Low | Very Low | Tabs use lazy rendering, minimal overhead |
| Routing conflicts | Low | Medium | Low | Test all routes, document routing strategy |
| AppGraph JSON corruption | Very Low | Critical | Medium | Validate JSON before commit, keep backup |

### 5.2 Rollback Plan

**If Integration Fails**:

1. **Git Revert**:
   ```bash
   git revert HEAD  # Revert AdminPage changes
   git push
   ```

2. **Alternative Approach**:
   - Keep AdminPage as User Management only
   - Add separate route `/admin/rbac` for RBACManagementPage
   - Update navigation to include link to RBAC page

3. **Fallback UI**:
   ```typescript
   // Simple navigation without tabs
   <div className="space-y-2">
     <Button onClick={() => navigate("/admin")}>User Management</Button>
     <Button onClick={() => navigate("/admin/rbac")}>Access Management</Button>
   </div>
   ```

### 5.3 Success Criteria

**Implementation Complete When**:

- ✅ AdminPage displays two tabs: User Management and Access Management
- ✅ User Management tab is default and active on `/admin`
- ✅ Access Management tab renders RBACManagementPage
- ✅ Deep link `/admin?tab=rbac` activates Access Management tab
- ✅ All existing user management functionality works unchanged
- ✅ All existing RBAC management functionality works in tab context
- ✅ Tab state persists during modal operations
- ✅ No console errors or warnings
- ✅ All automated tests pass
- ✅ AppGraph v17 updated and validated
- ✅ Documentation updated

---

## Part 6: Timeline and Effort Estimate

### 6.1 Effort Breakdown

| Task | Effort | Assignee | Dependencies |
|------|--------|----------|--------------|
| 1. Modify AdminPage to add tabs | 2-3 hours | Frontend Dev | None |
| 2. Add URL parameter routing | 1 hour | Frontend Dev | Task 1 |
| 3. Test all functionality | 2 hours | QA/Dev | Task 2 |
| 4. Update AppGraph v17 | 2 hours | AppGraph Maintainer | Task 1 |
| 5. Write automated tests | 2 hours | Frontend Dev | Task 1 |
| 6. Update documentation | 1 hour | Tech Writer/Dev | Task 3 |
| 7. Code review and refinement | 1 hour | Team | All tasks |
| **Total** | **11-12 hours** | | |

### 6.2 Recommended Timeline

**Day 1**:
- Morning: Implement tab structure (Task 1)
- Afternoon: Add routing and test manually (Tasks 2-3)

**Day 2**:
- Morning: Update AppGraph (Task 4)
- Afternoon: Write automated tests (Task 5)

**Day 3**:
- Morning: Update documentation (Task 6)
- Afternoon: Code review and merge (Task 7)

**Total Duration**: 3 days (with buffer for unforeseen issues)

---

## Part 7: Additional Recommendations

### 7.1 Future Enhancements

**Not Required for MVP, Consider for Future**:

1. **Tab State Persistence**:
   ```typescript
   // Remember last active tab across sessions
   const [activeTab, setActiveTab] = useLocalStorage("admin-tab", "users")
   ```

2. **Tab Badges**:
   ```tsx
   <TabsTrigger value="users">
     User Management
     <Badge className="ml-2">{userCount}</Badge>
   </TabsTrigger>
   ```

3. **Keyboard Navigation**:
   - Add keyboard shortcuts (Cmd+1 for User Management, Cmd+2 for Access Management)
   - Implement with `useHotkeys` or similar

4. **Loading States**:
   ```tsx
   <TabsContent value="rbac">
     <Suspense fallback={<LoadingSpinner />}>
       <RBACManagementPage />
     </Suspense>
   </TabsContent>
   ```

5. **Analytics**:
   - Track tab switches: `analytics.track("admin_tab_switched", { from, to })`
   - Monitor time spent on each tab

### 7.2 Code Quality Checklist

Before Merge:

- [ ] ESLint passes with no warnings
- [ ] Prettier formatting applied
- [ ] TypeScript types are strict (no `any` where avoidable)
- [ ] All imports are sorted and organized
- [ ] No console.log statements left in code
- [ ] No commented-out code blocks
- [ ] All TODOs addressed or documented
- [ ] Component is properly memoized if needed
- [ ] Accessibility: ARIA labels on tabs
- [ ] Mobile responsive (test on small screens)

### 7.3 Accessibility Considerations

**WCAG 2.1 AA Compliance**:

1. **Keyboard Navigation**:
   - Tabs component should support arrow keys
   - Focus should be visible
   - Tab order should be logical

2. **Screen Reader Support**:
   ```tsx
   <Tabs defaultValue="users" aria-label="Admin navigation">
     <TabsList role="tablist">
       <TabsTrigger
         value="users"
         role="tab"
         aria-selected={activeTab === "users"}
         aria-controls="user-management-panel"
       >
         User Management
       </TabsTrigger>
       <TabsTrigger
         value="rbac"
         role="tab"
         aria-selected={activeTab === "rbac"}
         aria-controls="access-management-panel"
       >
         Access Management
       </TabsTrigger>
     </TabsList>

     <TabsContent
       value="users"
       role="tabpanel"
       id="user-management-panel"
       aria-labelledby="user-management-tab"
     >
       {/* content */}
     </TabsContent>
   </Tabs>
   ```

3. **Focus Management**:
   - When switching tabs, focus should move to tab panel
   - Use `ref` and `focus()` if needed

4. **Color Contrast**:
   - Verify active/inactive tab contrast meets 4.5:1 ratio
   - Test in dark mode if supported

---

## Part 8: Conclusion

### 8.1 Summary

This integration plan provides a comprehensive roadmap to sync the AppGraph v17 specification with the current LangBuilder implementation by adding tab navigation to the AdminPage. The effort required is minimal (11-12 hours over 3 days) because:

1. **RBAC components are already implemented** in production-ready form
2. **Only structural UI change needed**: Add Tabs wrapper
3. **No logic changes required**: All functionality exists and works
4. **Low risk**: Pure UI restructuring, preserves all existing code

The prototype serves as a **UX reference** demonstrating the desired tab-based navigation pattern, which aligns perfectly with the PRD (Epic 3 Story 3.1) and AppGraph specification (ni0001 impact analysis).

### 8.2 Key Takeaways

**Critical Insights**:
1. ✅ Current LangBuilder has MORE than prototype (production vs mock)
2. ❌ Missing only tab navigation structure
3. ✅ AppGraph v17 correctly specifies the required change
4. ✅ PRD requirements fully define the expected behavior
5. ✅ All RBAC components exist and are production-ready

**Recommendation**: **Proceed with Step 1 (modify AdminPage)** immediately. This is a low-risk, high-value change that will:
- Fulfill PRD Epic 3 Story 3.1 ✅
- Complete AppGraph v17 specification ✅
- Improve UX by consolidating admin features ✅
- Require minimal testing (existing tests still valid) ✅

### 8.3 Next Steps

**Immediate Actions**:
1. Review this integration plan with the team
2. Assign tasks to frontend developer and AppGraph maintainer
3. Create feature branch: `feature/admin-page-tabs`
4. Implement Step 1 (AdminPage modification)
5. Test thoroughly (manual + automated)
6. Update AppGraph v17 (Step 3)
7. Create pull request with comprehensive testing
8. Merge and deploy

**Success Metrics**:
- Zero regressions in user management functionality
- RBAC features accessible via second tab
- Deep linking works for both tabs
- All tests pass
- AppGraph v17 fully synchronized with implementation

---

## Appendix A: File References

### Original Langbuilder Files

```
/Users/dongmingjiang/GB/LangBuilder/
├── src/frontend/src/
│   ├── pages/AdminPage/
│   │   ├── index.tsx (503 lines) ⬅️ MODIFY THIS
│   │   ├── RBACManagementPage/
│   │   │   ├── index.tsx (270 lines) ✅ USE THIS
│   │   │   ├── AssignmentListView.tsx (255 lines)
│   │   │   └── CreateAssignmentModal.tsx (388 lines)
│   │   └── LoginPage/index.tsx
│   ├── components/
│   │   ├── ui/tabs.tsx ✅ USE THIS
│   │   └── authorization/
│   │       ├── authAdminGuard.tsx (ProtectedAdminRoute)
│   │       └── RBACGuard.tsx
│   └── hooks/
│       └── usePermission.ts
└── .alucify/
    ├── RBAC Requirements Overview.md
    ├── rbac-architecture-corrected-final.md
    └── AppGraph_langbuilder_rbac_impact_v17_comprehensive_uidl_all.json ⬅️ UPDATE THIS
```

### Prototype Files (Reference Only)

```
/Users/dongmingjiang/GB/rbac-prototype/
├── app/admin/page.tsx ⬅️ REFERENCE FOR TAB STRUCTURE
├── components/rbac/ (Similar to LangBuilder but with mock data)
└── RBAC_Prototype_UIDL.json
```

### Configuration Files

```
- ESLint: /Users/dongmingjiang/GB/LangBuilder/.eslintrc.js
- TypeScript: /Users/dongmingjiang/GB/LangBuilder/tsconfig.json
- Prettier: /Users/dongmingjiang/GB/LangBuilder/.prettierrc
- Package.json: /Users/dongmingjiang/GB/LangBuilder/package.json
```

---

## Appendix B: Code Snippets

### Complete AdminPage Refactor (Simplified)

```typescript
// File: src/frontend/src/pages/AdminPage/index.tsx
import { useState, useEffect } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useSearchParams } from "react-router-dom"
import RBACManagementPage from "./RBACManagementPage"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import PaginatorComponent from "@/components/common/paginatorComponent"
import UserManagementModal from "@/modals/userManagementModal"
import ConfirmationModal from "@/modals/confirmationModal"
import IconComponent from "@/components/common/genericIconComponent"
import { useGetUsers, useAddUser, useUpdateUser, useDeleteUsers } from "@/controllers/API/queries/auth"
import useAlertStore from "@/stores/alertStore"

export default function AdminPage() {
  // Tab state from URL
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get("tab") || "users"

  // Existing state (unchanged)
  const [inputValue, setInputValue] = useState("")
  const [size, setSize] = useState(null)
  const [index, setIndex] = useState(null)
  const [totalRowsCount, setTotalRowsCount] = useState(0)
  const [filterUserList, setFilterUserList] = useState(null)
  const [openUserModal, setOpenUserModal] = useState(false)
  const [openDeleteConfirm, setOpenDeleteConfirm] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)

  // Existing hooks (unchanged)
  const { data: usersData, isLoading } = useGetUsers({ skip: index * size, limit: size })
  const addUserMutation = useAddUser()
  const updateUserMutation = useUpdateUser()
  const deleteUserMutation = useDeleteUsers()
  const setNoticeData = useAlertStore((state) => state.setNoticeData)

  // Existing functions (unchanged)
  const handleSearchInput = (e) => setInputValue(e.target.value)
  const handleNewUser = () => setOpenUserModal(true)
  const handleEditUser = (user) => {
    setSelectedUser(user)
    setOpenUserModal(true)
  }
  const handleDeleteUser = (user) => {
    setSelectedUser(user)
    setOpenDeleteConfirm(true)
  }
  // ... all other existing functions

  return (
    <div className="flex h-full flex-col space-y-6 p-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <IconComponent name="Shield" className="h-8 w-8" />
            Admin Page
          </h2>
          <p className="text-muted-foreground">
            Manage users and role-based access control for the application
          </p>
        </div>
      </div>

      {/* Tab Navigation */}
      <Tabs
        value={activeTab}
        onValueChange={(value) => setSearchParams({ tab: value })}
        className="flex-1"
      >
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="users">User Management</TabsTrigger>
          <TabsTrigger value="rbac">Access Management</TabsTrigger>
        </TabsList>

        {/* User Management Tab */}
        <TabsContent value="users" className="space-y-4 mt-6">
          <div className="flex items-center justify-between">
            <Input
              placeholder="Search by username"
              value={inputValue}
              onChange={handleSearchInput}
              className="max-w-sm"
            />
            <Button onClick={handleNewUser}>
              <IconComponent name="Plus" className="mr-2 h-4 w-4" />
              New User
            </Button>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Username</TableHead>
                  <TableHead>Active</TableHead>
                  <TableHead>Superuser</TableHead>
                  <TableHead>Created At</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {/* Existing table rows */}
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center">Loading...</TableCell>
                  </TableRow>
                ) : filterUserList?.length > 0 ? (
                  filterUserList.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>{user.username}</TableCell>
                      <TableCell>{/* Active toggle */}</TableCell>
                      <TableCell>{/* Superuser toggle */}</TableCell>
                      <TableCell>{new Date(user.create_at).toLocaleDateString()}</TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" onClick={() => handleEditUser(user)}>
                          Edit
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDeleteUser(user)}>
                          Delete
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center">No users found</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          <PaginatorComponent
            pageSize={size ?? 10}
            pageIndex={index ?? 0}
            totalRowsCount={totalRowsCount}
            paginate={(pageSize, pageIndex) => {
              setSize(pageSize)
              setIndex(pageIndex)
            }}
          />
        </TabsContent>

        {/* RBAC Management Tab */}
        <TabsContent value="rbac" className="space-y-4 mt-6">
          <RBACManagementPage />
        </TabsContent>
      </Tabs>

      {/* Modals (outside tabs, shared) */}
      {openUserModal && (
        <UserManagementModal
          open={openUserModal}
          setOpen={setOpenUserModal}
          userData={selectedUser}
          asChild
        >
          <></>
        </UserManagementModal>
      )}

      {openDeleteConfirm && (
        <ConfirmationModal
          open={openDeleteConfirm}
          setOpen={setOpenDeleteConfirm}
          title="Delete User"
          content={`Are you sure you want to delete user "${selectedUser?.username}"?`}
          onConfirm={() => {
            deleteUserMutation.mutate({ user_id: selectedUser.id })
            setOpenDeleteConfirm(false)
          }}
        />
      )}
    </div>
  )
}
```

---

## Appendix C: Testing Checklist

### Manual Testing

- [ ] **User Management Tab**
  - [ ] Default tab active on `/admin`
  - [ ] Search input filters users
  - [ ] "New User" button opens modal
  - [ ] Create user succeeds
  - [ ] Edit user succeeds
  - [ ] Delete user succeeds with confirmation
  - [ ] Active toggle works
  - [ ] Superuser toggle works (superuser only)
  - [ ] Pagination works

- [ ] **Access Management Tab**
  - [ ] Tab switch displays RBAC content
  - [ ] "New Assignment" button opens wizard
  - [ ] 4-step wizard works
  - [ ] Assignment creation succeeds
  - [ ] Assignment list displays correctly
  - [ ] Filters work (user, role, scope)
  - [ ] Edit assignment succeeds
  - [ ] Delete assignment succeeds
  - [ ] Immutable assignments protected

- [ ] **Deep Linking**
  - [ ] `/admin` loads User Management tab
  - [ ] `/admin?tab=users` loads User Management tab
  - [ ] `/admin?tab=rbac` loads Access Management tab
  - [ ] Invalid tab parameter falls back to users

- [ ] **Navigation**
  - [ ] Tab switches update URL
  - [ ] Browser back/forward works
  - [ ] Tab state persists during modal operations
  - [ ] Tab state persists during API calls

- [ ] **Access Control**
  - [ ] Non-superuser redirected from `/admin`
  - [ ] Non-superuser cannot access `/admin?tab=rbac`
  - [ ] Superuser can access both tabs

- [ ] **UI/UX**
  - [ ] No console errors
  - [ ] No visual glitches
  - [ ] Responsive on mobile/tablet
  - [ ] Keyboard navigation works
  - [ ] Focus management correct

### Automated Testing

- [ ] Unit tests for AdminPage component
- [ ] Integration tests for tab switching
- [ ] E2E tests for user workflows
- [ ] E2E tests for RBAC workflows
- [ ] Accessibility tests (axe-core)

---

**END OF INTEGRATION PLAN**

*This document provides a complete roadmap for integrating the RBAC prototype changes into the LangBuilder AppGraph. Follow the steps sequentially for successful implementation.*
