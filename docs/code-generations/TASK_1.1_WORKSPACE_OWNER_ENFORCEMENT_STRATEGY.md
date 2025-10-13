# Workspace Owner Enforcement Strategy

**Document Type:** Implementation Guidance for Task 1.4 (API Layer)
**Related Gap:** GAP-001 from TASK_1.1_IMPLEMENTATION_AUDIT.md
**Priority:** HIGH
**Date:** 2025-10-11

---

## Overview

This document provides implementation guidance for enforcing the **single owner per workspace** constraint identified in the Task 1.1 audit. Per the RBAC Implementation Plan V3 Final, line 374, "Workspace model enforces single owner on creation."

**Current Status:**
- ✅ Database models support workspace ownership via `WorkspaceMember.role` field
- ✅ WorkspaceMember has role validation (`owner`/`admin`/`member`)
- ⚠️ No business logic enforcement yet (by design - belongs in API layer)

---

## Why API-Level Enforcement (Not Model-Level)

**Rationale:**
1. **Separation of Concerns:** Database models define structure; API endpoints enforce business rules
2. **Flexibility:** Allows for future edge cases (e.g., owner transfer during maintenance)
3. **Better Error Messages:** API layer can provide context-aware error messages
4. **Transaction Control:** API layer can orchestrate complex multi-step operations atomically

**Pattern in Existing Codebase:**
- Flow ownership: Enforced in `src/backend/base/langflow/api/v1/flows.py` (not in model)
- Folder permissions: Enforced in `src/backend/base/langflow/api/v1/projects.py`

---

## Implementation Location: Task 1.4 (API Layer)

**Target File:** `src/backend/base/langflow/api/v1/workspaces.py` (to be created)

**Enforcement Points:**
1. Workspace creation (POST /api/v1/workspaces/)
2. Member addition (POST /api/v1/workspaces/{id}/members)
3. Member role update (PATCH /api/v1/workspaces/{id}/members/{member_id})
4. Member deletion (DELETE /api/v1/workspaces/{id}/members/{member_id})

---

## Enforcement Rules

### Rule 1: Workspace Creation Must Have Exactly One Owner

**Behavior:**
- When creating a workspace, automatically create a `WorkspaceMember` with role='owner' for the creating user
- Do not allow API callers to specify initial members without an owner

**Implementation Pattern:**
```python
@router.post("/", response_model=WorkspaceRead, status_code=201)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new workspace with the current user as owner."""
    # Create workspace
    workspace = Workspace.model_validate(workspace_data)
    session.add(workspace)
    await session.flush()  # Get workspace.id

    # Automatically add creator as owner
    owner_member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role="owner",
    )
    session.add(owner_member)

    await session.commit()
    await session.refresh(workspace)
    return workspace
```

### Rule 2: Cannot Remove Last Owner

**Behavior:**
- When deleting a workspace member, check if they are the last owner
- If so, reject the operation with HTTP 400 Bad Request

**Implementation Pattern:**
```python
@router.delete("/workspaces/{workspace_id}/members/{member_id}", status_code=204)
async def remove_workspace_member(
    workspace_id: UUID,
    member_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove a member from a workspace."""
    # Fetch the member
    member = await session.get(WorkspaceMember, member_id)
    if not member or member.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Member not found")

    # If removing an owner, ensure at least one owner remains
    if member.role == "owner":
        owner_count = await session.scalar(
            select(func.count())
            .select_from(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == "owner",
                WorkspaceMember.is_active == True,
            )
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove the last owner from a workspace. Transfer ownership first.",
            )

    # Check permissions (must be owner to remove members)
    await check_workspace_permission(session, current_user.id, workspace_id, "workspace:member:delete")

    await session.delete(member)
    await session.commit()
```

### Rule 3: Cannot Change Last Owner Role to Non-Owner

**Behavior:**
- When updating a member's role from 'owner' to 'admin'/'member', verify another owner exists

**Implementation Pattern:**
```python
@router.patch("/workspaces/{workspace_id}/members/{member_id}", response_model=WorkspaceMemberRead)
async def update_workspace_member_role(
    workspace_id: UUID,
    member_id: UUID,
    update_data: WorkspaceMemberUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a workspace member's role."""
    member = await session.get(WorkspaceMember, member_id)
    if not member or member.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Member not found")

    # If changing owner to non-owner, ensure at least one owner remains
    if member.role == "owner" and update_data.role in ["admin", "member"]:
        owner_count = await session.scalar(
            select(func.count())
            .select_from(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == "owner",
                WorkspaceMember.is_active == True,
            )
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot demote the last owner. Promote another member to owner first.",
            )

    # Check permissions
    await check_workspace_permission(session, current_user.id, workspace_id, "workspace:member:update")

    member.role = update_data.role
    member.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(member)
    return member
```

### Rule 4: Allow Owner Transfer

**Behavior:**
- Special endpoint for atomic owner transfer
- Promotes new owner and optionally demotes old owner

**Implementation Pattern:**
```python
@router.post("/workspaces/{workspace_id}/transfer-ownership", response_model=WorkspaceRead)
async def transfer_workspace_ownership(
    workspace_id: UUID,
    new_owner_id: UUID,
    demote_current: bool = True,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Transfer workspace ownership to another member."""
    # Verify current user is an owner
    current_member = await session.scalar(
        select(WorkspaceMember)
        .where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.role == "owner",
        )
    )
    if not current_member:
        raise HTTPException(status_code=403, detail="Only owners can transfer ownership")

    # Verify new owner is a member
    new_member = await session.scalar(
        select(WorkspaceMember)
        .where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == new_owner_id,
        )
    )
    if not new_member:
        raise HTTPException(status_code=404, detail="New owner must be a workspace member")

    # Atomic transfer
    new_member.role = "owner"
    if demote_current:
        current_member.role = "admin"

    await session.commit()

    workspace = await session.get(Workspace, workspace_id)
    return workspace
```

---

## Validation Testing Strategy

**Unit Tests (in test_workspace_api.py):**
1. `test_create_workspace_auto_assigns_owner()` - Verify owner is automatically created
2. `test_cannot_remove_last_owner()` - Verify rejection with HTTP 400
3. `test_cannot_demote_last_owner()` - Verify role change rejection
4. `test_transfer_ownership_success()` - Verify atomic transfer works
5. `test_transfer_ownership_permission_denied()` - Verify only owners can transfer
6. `test_multiple_owners_allowed()` - Verify can have >1 owner
7. `test_can_remove_owner_when_multiple_exist()` - Verify deletion with multiple owners

**Integration Tests:**
1. Create workspace → Verify owner exists in database
2. Multi-step: Create workspace → Add 2nd owner → Remove 1st owner → Success
3. Multi-step: Create workspace → Try remove owner → Fails → Add 2nd owner → Remove 1st → Success

---

## Error Messages

**Consistent, User-Friendly Error Messages:**

| Scenario | HTTP Status | Error Message |
|----------|-------------|---------------|
| Remove last owner | 400 Bad Request | "Cannot remove the last owner from a workspace. Transfer ownership first." |
| Demote last owner | 400 Bad Request | "Cannot demote the last owner. Promote another member to owner first." |
| Transfer by non-owner | 403 Forbidden | "Only workspace owners can transfer ownership." |
| Transfer to non-member | 404 Not Found | "New owner must be a workspace member. Invite them first." |

---

## Database Constraints (Optional Enhancement)

**Note:** The current implementation does **not** enforce this at the database level (by design). However, for defense-in-depth, consider adding a database constraint in a future migration:

```sql
-- PostgreSQL check constraint (complex, not recommended initially)
ALTER TABLE workspace
ADD CONSTRAINT workspace_must_have_owner
CHECK (
    EXISTS (
        SELECT 1 FROM workspace_member
        WHERE workspace_member.workspace_id = workspace.id
          AND workspace_member.role = 'owner'
          AND workspace_member.is_active = true
    )
);
```

**⚠️ Warning:** This constraint is **complex** and can cause deadlocks. Prefer API-level enforcement for now.

---

## Audit Logging

**Workspace Owner Events to Log:**

| Event | When | Example Details |
|-------|------|-----------------|
| `workspace.create` | Workspace created | `{"workspace_id": "...", "owner_id": "..."}` |
| `workspace.member.add` | Member added | `{"member_id": "...", "role": "owner"}` |
| `workspace.member.remove` | Member removed | `{"member_id": "...", "was_owner": true}` |
| `workspace.ownership.transfer` | Ownership transferred | `{"from_user_id": "...", "to_user_id": "..."}` |

---

## Migration Strategy

**For Existing Workspaces (if any):**

When migrating existing data, ensure all workspaces have at least one owner:

```sql
-- Check for workspaces without owners
SELECT w.id, w.name
FROM workspace w
LEFT JOIN workspace_member wm ON wm.workspace_id = w.id AND wm.role = 'owner'
WHERE wm.id IS NULL;

-- Auto-assign creator as owner (if user_id is tracked somewhere)
-- Or manually assign first member as owner:
UPDATE workspace_member
SET role = 'owner'
WHERE id IN (
    SELECT DISTINCT ON (workspace_id) id
    FROM workspace_member
    WHERE workspace_id IN (
        SELECT w.id FROM workspace w
        LEFT JOIN workspace_member wm ON wm.workspace_id = w.id AND wm.role = 'owner'
        WHERE wm.id IS NULL
    )
    ORDER BY workspace_id, joined_at ASC
);
```

---

## Success Criteria for Task 1.4

**Acceptance Criteria (matches RBAC Implementation Plan v3.0 success criteria):**
- [ ] Workspace creation automatically assigns creator as owner
- [ ] Cannot delete last workspace owner (returns HTTP 400)
- [ ] Cannot demote last workspace owner (returns HTTP 400)
- [ ] Can transfer ownership atomically
- [ ] Unit tests cover all edge cases (7 tests minimum)
- [ ] Integration tests verify end-to-end behavior
- [ ] Audit logs capture all ownership changes

---

## References

**Related Documents:**
- `docs/implementation-plans/RBAC_IMPLEMENTATION_PLAN_V3_FINAL.md` - Lines 374, 426-460
- `docs/code-generations/TASK_1.1_IMPLEMENTATION_AUDIT.md` - GAP-001 (lines 258-284)
- `src/backend/base/langflow/api/v1/projects.py` - Existing permission enforcement pattern

**AppGraph Nodes (v7.1):**
- **Logic Node:** `Workspace_Creation_Logic` - Handles workspace creation with owner assignment
- **Logic Node:** `Workspace_Member_Management_Logic` - Handles member CRUD with owner enforcement
- **Edge:** `user_entity → workspace_member_entity` (has_workspace_memberships)
- **Edge:** `workspace_entity → workspace_member_entity` (has_members)

---

## Implementation Timeline

**Task 1.4: RBAC API Endpoints (Workspaces)**
- Estimated: 8-12 hours
- Dependencies: Task 1.2 (migration), Task 1.3 (AuthorizationService)
- Deliverables:
  - `src/backend/base/langflow/api/v1/workspaces.py` (CRUD + member management)
  - `src/backend/tests/unit/api/test_workspace_api.py` (unit tests)
  - `src/backend/tests/integration/test_workspace_integration.py` (integration tests)

---

## Conclusion

**Summary:**
The workspace owner enforcement strategy follows existing codebase patterns by implementing business logic in the API layer rather than the model layer. This approach provides flexibility, better error messages, and clear separation of concerns.

**Key Takeaway:**
While the database models **support** workspace ownership (via `WorkspaceMember.role`), the actual **enforcement** of "exactly one owner" will be implemented in Task 1.4 (API Layer), not in Task 1.1 (Model Layer).

**Status:**
✅ **Model-level foundation complete** (Task 1.1)
⏳ **API-level enforcement pending** (Task 1.4)

---

**End of Document**
