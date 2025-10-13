#!/usr/bin/env python3
"""Script to complete the RBAC Implementation Plan Refined V2 by appending remaining sections.
This addresses all critical, high, and medium priority gaps from the audit.
"""

# Read the current partial plan
with open("docs/RBAC_IMPLEMENTATION_PLAN_REFINED_V2.md") as f:
    existing_content = f.read()

# Define the continuation sections
continuation = """

#### Task 2.2: Implement Permission Caching (Same as v1)

**Scope & Goals:**
In-memory caching with TTL and invalidation to meet performance NFRs.

**Success Criteria:**
- [ ] Cache hits return in ≤10ms (p95)
- [ ] Cache invalidation works on role/assignment/group membership changes
- [ ] TTL expiration works (5 min default)

**Implementation Files:**
```
src/backend/base/langflow/services/rbac/cache.py
```

*Note: Implementation details same as v1.0 plan, Task 2.2*

---

#### Task 2.3: Performance Testing and Optimization (Same as v1)

**Success Criteria:**
- [ ] Uncached permission check ≤100ms p95
- [ ] Cached permission check ≤10ms p95
- [ ] Performance tests include group role aggregation scenarios

*Note: Implementation details same as v1.0 plan, Task 2.3*

---

#### Task 2.4: Write Integration Tests for Permission Evaluation (EXPANDED)

**v2 Additions:**
- Test group role assignments (PRD Story 2.1 @AC1)
- Test workspace and environment scope resolution

**Success Criteria:**
- [ ] All tests from v1.0 pass
- [ ] **Test group role assignment applies to all members** (NEW)
- [ ] **Test workspace grant cascades to projects, environments, flows** (NEW)
- [ ] **Test environment grant restricts to specific environment** (NEW)

*Note: Core implementation from v1.0, plus new test cases for groups and new scopes*

---

### Phase 3: RBAC REST API & Admin Endpoints (EXPANDED)

**Description:** Implement REST API endpoints for RBAC management (roles, permissions, grants, **groups, workspaces, environments, invitations**) following FastAPI patterns. This phase makes RBAC configurable via API before enforcing it in existing endpoints.

**v2 Changes:**
- ✅ Added Task 3.6: Group Management API (NEW)
- ✅ Added Task 3.7: Workspace Management API (NEW)
- ✅ Added Task 3.8: Environment Management API (NEW)
- ✅ Added Task 3.9: Invitation Management API (NEW)

**Scope:**
- RBAC CRUD endpoints (Story 3.2)
- Role assignment endpoints (Story 3.5)
- **Group management endpoints** (NEW - Story 2.1 @AC1-@AC2)
- **Workspace management endpoints** (NEW - multi-tenancy)
- **Environment management endpoints** (NEW - deployment scoping)
- **Invitation management endpoints** (NEW - PRD Story 1.1 @AC6)
- Service account management endpoints
- OpenAPI documentation
- Permission checks on admin endpoints

**Goals:**
- All RBAC entities manageable via REST API
- API follows existing FastAPI/Pydantic patterns
- Admin-only access enforced (superuser or appropriate RBAC permission)
- OpenAPI docs auto-generated
- Ready for frontend integration in Phase 4.5

---

#### Task 3.1: Implement Role Management API (Same as v1)

*Note: Implementation details same as v1.0 plan, Task 3.1*

**Success Criteria:**
- [ ] All criteria from v1.0
- [ ] Endpoints work with workspace context

---

#### Task 3.2: Implement Permission Catalog API (Same as v1)

*Note: Implementation details same as v1.0 plan, Task 3.2*

---

#### Task 3.3: Implement Role Assignment (Grant) API (EXPANDED)

**v2 Additions:**
- Support "group:{name}" principal type
- Validate workspace context for grants

**API Enhancement:**
```python
def parse_principal(principal: str) -> tuple[str, str]:
    \"\"\"
    Parse principal string.

    v2 UPDATED: Now supports groups.

    Formats:
    - user:email@example.com
    - service_account:uuid
    - group:group-name  [NEW v2]
    \"\"\"
    if ":" not in principal:
        raise ValueError("Principal must be in format 'type:identifier'")

    principal_type, principal_id = principal.split(":", 1)

    if principal_type not in ["user", "service_account", "group"]:
        raise ValueError(f"Invalid principal type: {principal_type}")

    return principal_type, principal_id


@router.post("/api/admin/grants/", response_model=GrantRead, status_code=201)
async def create_grant(
    grant_data: GrantCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> GrantRead:
    \"\"\"
    Assign role to user/service account/group at scope (PRD Story 3.5 @AC1).

    v2 UPDATED: Now supports group principals.
    \"\"\"
    # Parse principal
    principal_type, principal_id = parse_principal(grant_data.principal)

    if principal_type == "user":
        user = await get_user_by_email(principal_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        assignee_type = "user"
        user_id = user.id
        service_account_id = None
        group_id = None
    elif principal_type == "service_account":
        sa = await db.get(ServiceAccount, UUID(principal_id))
        if not sa:
            raise HTTPException(status_code=404, detail="Service account not found")
        assignee_type = "service_account"
        user_id = None
        service_account_id = sa.id
        group_id = None
    elif principal_type == "group":  # [NEW v2]
        group = await get_group_by_name(principal_id, db)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        assignee_type = "group"
        user_id = None
        service_account_id = None
        group_id = group.id

    # ... rest of implementation
```

**Success Criteria:**
- [ ] All criteria from v1.0
- [ ] **CREATE grant with group principal works (PRD Story 2.1 @AC1)** (NEW)
- [ ] **DELETE grant revokes group role assignment (PRD Story 2.1 @AC2)** (NEW)
- [ ] **Group grants apply to all group members (verified in integration tests)** (NEW)

---

#### Task 3.4: Implement Service Account Management API (Same as v1)

*Note: Implementation details same as v1.0 plan, Task 3.4*

---

#### Task 3.5: Write Integration Tests for RBAC API (EXPANDED)

**v2 Additions:**
- Test group CRUD endpoints
- Test workspace CRUD endpoints
- Test environment CRUD endpoints
- Test invitation CRUD endpoints

**Success Criteria:**
- [ ] All tests from v1.0 pass
- [ ] **Test group management API endpoints** (NEW)
- [ ] **Test workspace management API endpoints** (NEW)
- [ ] **Test environment management API endpoints** (NEW)
- [ ] **Test invitation management API endpoints** (NEW)

---

#### Task 3.6: Implement Group Management API (NEW v2)

**Scope & Goals:**
CRUD endpoints for user groups and group membership management (PRD Story 2.1 @AC1-@AC2).

**Impact Subgraph from AppGraph:**
```
Interface Nodes (NEW v2):
- group_management_api → REST API for user groups

Logic Nodes (NEW v2):
- create_group_logic → Creates user group
- update_group_logic → Updates group
- delete_group_logic → Deletes group
- add_group_member_logic → Adds user to group
- remove_group_member_logic → Removes user from group
- list_groups_logic → Lists groups
- list_group_members_logic → Lists group members

Edges:
- group_management_api → create_group_logic (invokes)
- group_management_api → add_group_member_logic (invokes)
- group_management_api → remove_group_member_logic (invokes)
- create_group_logic → user_group_entity (creates)
- add_group_member_logic → user_group_member_entity (creates)
- remove_group_member_logic → user_group_member_entity (deletes)
- *_group_logic → audit_log_entity (logs_to)
```

**Architecture & Tech Stack:**
- **Framework**: FastAPI with async def
- **Validation**: Pydantic schemas (UserGroupCreate, UserGroupUpdate, UserGroupRead)
- **Auth**: Requires `group.create` / `group.manage_members` permissions
- **Pattern**: Follow existing API patterns

**API Endpoints:**
```python
# src/backend/base/langflow/api/v1/rbac/groups.py

@router.post("/api/admin/groups/", response_model=UserGroupRead, status_code=201)
async def create_group(
    group_data: UserGroupCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> UserGroupRead:
    \"\"\"Create user group within workspace (PRD Story 2.1).\"\"\"
    # Check permission
    if not current_user.is_superuser:
        allowed, _ = await has_permission(
            current_user.id, "group.create", "workspace", group_data.workspace_id
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Validate workspace exists
    workspace = await db.get(Workspace, group_data.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Validate unique name within workspace
    existing = await db.execute(
        select(UserGroup).where(
            UserGroup.workspace_id == group_data.workspace_id,
            UserGroup.name == group_data.name
        )
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Group name must be unique within workspace")

    # Create group
    group = UserGroup(
        workspace_id=group_data.workspace_id,
        name=group_data.name,
        description=group_data.description,
        created_by=current_user.id
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="group.created",
        resource_type="group",
        resource_id=group.id,
        details={"name": group.name, "workspace_id": str(group.workspace_id)}
    )

    return group


@router.get("/api/admin/groups/", response_model=list[UserGroupRead])
async def list_groups(
    workspace_id: UUID | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> list[UserGroupRead]:
    \"\"\"List user groups, optionally filtered by workspace.\"\"\"
    query = select(UserGroup)

    if workspace_id:
        query = query.where(UserGroup.workspace_id == workspace_id)

    result = await db.execute(query)
    groups = result.scalars().all()
    return groups


@router.post("/api/admin/groups/{group_id}/members", status_code=201)
async def add_group_member(
    group_id: UUID,
    member_data: GroupMemberAdd,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    \"\"\"Add user to group (PRD Story 2.1 @AC1).\"\"\"
    # Check permission
    group = await db.get(UserGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if not current_user.is_superuser:
        allowed, _ = await has_permission(
            current_user.id, "group.manage_members", "workspace", group.workspace_id
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Get user
    user = await get_user_by_email(member_data.user_email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already a member
    existing = await db.execute(
        select(UserGroupMember).where(
            UserGroupMember.group_id == group_id,
            UserGroupMember.user_id == user.id
        )
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="User is already a member")

    # Add member
    member = UserGroupMember(
        group_id=group_id,
        user_id=user.id,
        added_by=current_user.id
    )
    db.add(member)
    await db.commit()

    # Invalidate user cache (group membership changed)
    await invalidate_user_cache(user.id)

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="group_member.added",
        resource_type="group",
        resource_id=group_id,
        details={"user_id": str(user.id), "user_email": member_data.user_email}
    )

    return {"status": "success"}


@router.delete("/api/admin/groups/{group_id}/members/{user_id}", status_code=204)
async def remove_group_member(
    group_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    \"\"\"Remove user from group (PRD Story 2.1 @AC2).\"\"\"
    # Check permission
    group = await db.get(UserGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if not current_user.is_superuser:
        allowed, _ = await has_permission(
            current_user.id, "group.manage_members", "workspace", group.workspace_id
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Find membership
    membership = await db.execute(
        select(UserGroupMember).where(
            UserGroupMember.group_id == group_id,
            UserGroupMember.user_id == user_id
        )
    )
    member = membership.scalar()
    if not member:
        raise HTTPException(status_code=404, detail="User is not a member of this group")

    # Remove member
    await db.delete(member)
    await db.commit()

    # Invalidate user cache
    await invalidate_user_cache(user_id)

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="group_member.removed",
        resource_type="group",
        resource_id=group_id,
        details={"user_id": str(user_id)}
    )


@router.delete("/api/admin/groups/{group_id}", status_code=204)
async def delete_group(
    group_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    \"\"\"Delete group (removes all memberships and role assignments).\"\"\"
    group = await db.get(UserGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check permission
    if not current_user.is_superuser:
        allowed, _ = await has_permission(
            current_user.id, "group.delete", "workspace", group.workspace_id
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Get all members (for cache invalidation)
    members_result = await db.execute(
        select(UserGroupMember.user_id).where(UserGroupMember.group_id == group_id)
    )
    member_user_ids = [row[0] for row in members_result]

    # Delete group (cascade will delete members and role assignments)
    await db.delete(group)
    await db.commit()

    # Invalidate cache for all members
    for user_id in member_user_ids:
        await invalidate_user_cache(user_id)

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="group.deleted",
        resource_type="group",
        resource_id=group_id,
        details={"name": group.name, "member_count": len(member_user_ids)}
    )
```

**Pydantic Schemas:**
```python
class UserGroupCreate(BaseModel):
    workspace_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None

class UserGroupUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None

class UserGroupRead(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    is_active: bool
    external_id: str | None
    scim_synced: bool
    created_at: datetime
    updated_at: datetime

    # Optional: Include members count
    members_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class GroupMemberAdd(BaseModel):
    user_email: str = Field(..., min_length=1)

class UserGroupMemberRead(BaseModel):
    id: UUID
    group_id: UUID
    user_id: UUID
    is_active: bool
    joined_at: datetime

    # Optional: Include user details
    user: UserRead | None = None

    model_config = ConfigDict(from_attributes=True)
```

**Success Criteria:**
- [ ] POST /api/admin/groups/ creates group in workspace (PRD Story 2.1 @AC1)
- [ ] Group name unique within workspace enforced
- [ ] POST /api/admin/groups/{id}/members adds user to group (PRD @AC1)
- [ ] DELETE /api/admin/groups/{id}/members/{user_id} removes user (PRD @AC2)
- [ ] DELETE /api/admin/groups/{id} deletes group and all memberships
- [ ] Group role assignments apply to all members (verified in integration tests)
- [ ] Cache invalidation works on group membership changes
- [ ] Audit log records all group operations
- [ ] OpenAPI docs generated correctly

**Implementation Files:**
```
src/backend/base/langflow/api/v1/rbac/groups.py
src/backend/base/langflow/schema/rbac.py  # Add group schemas
```

---

#### Task 3.7: Implement Workspace Management API (NEW v2)

**Scope & Goals:**
CRUD endpoints for workspaces and workspace membership management.

**Impact Subgraph from AppGraph:**
```
Interface Nodes (NEW v2):
- workspace_management_api → REST API for workspaces

Logic Nodes (NEW v2):
- create_workspace_logic → Creates workspace with creator as owner
- update_workspace_logic → Updates workspace settings
- delete_workspace_logic → Deletes workspace (with safeguards)
- invite_workspace_member_logic → Invites user to workspace
- remove_workspace_member_logic → Removes workspace member
- list_workspaces_logic → Lists user's workspaces

Edges:
- workspace_management_api → create_workspace_logic (invokes)
- workspace_management_api → invite_workspace_member_logic (invokes)
- create_workspace_logic → workspace_entity (creates)
- create_workspace_logic → workspace_member_entity (creates_owner)
- invite_workspace_member_logic → invitation_entity (creates)
- *_workspace_logic → audit_log_entity (logs_to)
```

**API Endpoints:**
```python
# src/backend/base/langflow/api/v1/workspaces.py

@router.post("/api/v1/workspaces/", response_model=WorkspaceRead, status_code=201)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> WorkspaceRead:
    \"\"\"Create workspace with creator as owner.\"\"\"
    # Generate slug from name
    slug = generate_slug(workspace_data.name)

    # Validate slug uniqueness
    existing = await db.execute(
        select(Workspace).where(Workspace.slug == slug)
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Workspace slug must be unique")

    # Create workspace
    workspace = Workspace(
        name=workspace_data.name,
        slug=slug,
        description=workspace_data.description,
        created_by=current_user.id
    )
    db.add(workspace)
    await db.flush()

    # Add creator as owner
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(member)

    await db.commit()
    await db.refresh(workspace)

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="workspace.created",
        resource_type="workspace",
        resource_id=workspace.id,
        details={"name": workspace.name}
    )

    return workspace


@router.get("/api/v1/workspaces/", response_model=list[WorkspaceRead])
async def list_workspaces(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> list[WorkspaceRead]:
    \"\"\"List user's workspaces.\"\"\"
    # Query workspaces where user is a member
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember)
        .where(
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.is_active == True,
            Workspace.is_active == True
        )
    )
    workspaces = result.scalars().all()
    return workspaces


@router.post("/api/v1/workspaces/{workspace_id}/members", status_code=201)
async def invite_workspace_member(
    workspace_id: UUID,
    invite_data: WorkspaceInvite,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    \"\"\"
    Invite user to workspace via email (PRD Story 1.1 @AC5, @AC6).

    Creates invitation that user must accept.
    \"\"\"
    # Check permission
    if not current_user.is_superuser:
        allowed, _ = await has_permission(
            current_user.id, "workspace.invite_users", "workspace", workspace_id
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    workspace = await db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check if user already a member
    existing_user = await get_user_by_email(invite_data.email, db)
    if existing_user:
        existing_member = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == existing_user.id
            )
        )
        if existing_member.scalar():
            raise HTTPException(status_code=400, detail="User is already a workspace member")

    # Create invitation
    invitation = Invitation(
        workspace_id=workspace_id,
        invited_by_user_id=current_user.id,
        email=invite_data.email,
        role_id=invite_data.role_id if invite_data.role_id else None,
        scope_type="workspace",
        scope_id=workspace_id,
        expires_at=datetime.now(UTC) + timedelta(days=7),
        token=secrets.token_urlsafe(32),
        message=invite_data.message
    )
    db.add(invitation)
    await db.commit()

    # Send email notification
    await send_invitation_email(
        to_email=invite_data.email,
        workspace_name=workspace.name,
        inviter_name=current_user.username,
        invitation_token=invitation.token,
        message=invite_data.message
    )

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="workspace_member.invited",
        resource_type="workspace",
        resource_id=workspace_id,
        details={"email": invite_data.email, "invitation_id": str(invitation.id)}
    )

    return {"status": "invited", "invitation_id": str(invitation.id)}


@router.delete("/api/v1/workspaces/{workspace_id}/members/{user_id}", status_code=204)
async def remove_workspace_member(
    workspace_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    \"\"\"Remove member from workspace (owner only).\"\"\"
    # Check permission (owner only)
    if not current_user.is_superuser:
        member = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == current_user.id
            )
        )
        current_member = member.scalar()
        if not current_member or current_member.role != "owner":
            raise HTTPException(status_code=403, detail="Only workspace owners can remove members")

    # Find member to remove
    member_to_remove = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id
        )
    )
    member = member_to_remove.scalar()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Cannot remove last owner
    if member.role == "owner":
        owner_count = await db.execute(
            select(func.count(WorkspaceMember.id)).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == "owner",
                WorkspaceMember.is_active == True
            )
        )
        if owner_count.scalar() <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove last workspace owner")

    await db.delete(member)
    await db.commit()

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="workspace_member.removed",
        resource_type="workspace",
        resource_id=workspace_id,
        details={"removed_user_id": str(user_id)}
    )


@router.delete("/api/v1/workspaces/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: UUID,
    confirm: str = Query(..., description="Must be workspace name to confirm deletion"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    \"\"\"Delete workspace (owner only, with safeguards).\"\"\"
    workspace = await db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check ownership
    if not current_user.is_superuser:
        member = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == current_user.id
            )
        )
        current_member = member.scalar()
        if not current_member or current_member.role != "owner":
            raise HTTPException(status_code=403, detail="Only workspace owners can delete workspace")

    # Confirm deletion
    if confirm != workspace.name:
        raise HTTPException(
            status_code=400,
            detail=f"Confirmation failed. Please provide workspace name '{workspace.name}' to confirm deletion"
        )

    # Cascade delete (projects, flows, etc.)
    await db.delete(workspace)
    await db.commit()

    # Audit log
    await log_audit_event(
        actor_id=current_user.id,
        action="workspace.deleted",
        resource_type="workspace",
        resource_id=workspace_id,
        details={"name": workspace.name}
    )
```

**Success Criteria:**
- [ ] POST /api/v1/workspaces/ creates workspace with creator as owner
- [ ] GET /api/v1/workspaces/ returns user's workspaces only
- [ ] POST /api/v1/workspaces/{id}/members invites user via email (PRD @AC5)
- [ ] Invitation email sent with secure token
- [ ] DELETE /api/v1/workspaces/{id}/members/{user_id} removes member
- [ ] Cannot remove last workspace owner
- [ ] DELETE /api/v1/workspaces/{id} deletes workspace with confirmation
- [ ] Workspace deletion cascades to projects/flows (with safeguards)

**Implementation Files:**
```
src/backend/base/langflow/api/v1/workspaces.py
src/backend/base/langflow/schema/workspace.py
src/backend/base/langflow/services/email/  # Email service
```

---

"""

# Write the continuation
with open("docs/RBAC_IMPLEMENTATION_PLAN_REFINED_V2.md", "w") as f:
    f.write(existing_content + continuation)

print("✅ Added remaining Phase 2 and Phase 3 sections")
print("Next: Run this script again to add Phase 3 tasks 3.8, 3.9, Phase 4, Phase 4.5, and Phases 5-7")
