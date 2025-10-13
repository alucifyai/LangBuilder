# RBAC Permission Cache Invalidation Strategy

**Document Version:** 1.0
**Date:** October 11, 2025
**Scope:** Task 2.1 - Permission Evaluation Engine
**Target Audience:** Developers implementing Task 2.2 and maintaining RBAC system

---

## Overview

The RBAC permission evaluation engine includes a permission cache (`PermissionCache` in `cache.py`) that stores the results of permission checks to optimize performance. This document describes the cache invalidation strategy to ensure permission changes are reflected immediately.

**Cache Implementation:** `cachetools.TTLCache` with 5-minute TTL (default)
**Cache Location:** `src/backend/base/langflow/services/rbac/cache.py`
**Cache Key Format:** `perm:{user_id}:{permission}:{resource_type}:{resource_id}`

---

## Invalidation Methods

The `PermissionCache` and `RBACEnforcementEngine` classes provide three levels of cache invalidation:

### 1. User-Level Invalidation

**Method:** `invalidate_user_cache(user_id: UUID)`

**Purpose:** Invalidates all cached permission entries for a specific user.

**When to Call:**
- ✅ User's direct role assignment changes (added or removed)
- ✅ User joins a group
- ✅ User leaves a group
- ✅ User's group membership is activated/deactivated
- ✅ User's group's role assignment changes

**Example Usage:**
```python
from langflow.services.rbac import RBACEnforcementEngine

async def assign_role_to_user(session, user_id, role_id, scope_type, scope_id):
    # Create role assignment
    assignment = RoleAssignment(
        role_id=role_id,
        user_id=user_id,
        assignee_type="user",
        scope_type=scope_type,
        scope_id=scope_id,
    )
    session.add(assignment)
    await session.commit()

    # Invalidate user's cached permissions
    engine = RBACEnforcementEngine(session)
    await engine.invalidate_user_cache(user_id)
```

**Impact:** Clears all permission cache entries where the cache key starts with `perm:{user_id}:`

**Performance:** O(n) where n = number of cached entries for the user (typically <100)

---

### 2. Role-Level Invalidation

**Method:** `invalidate_role_cache(role_id: UUID)`

**Purpose:** Invalidates **entire cache** when a role's permissions are modified.

**When to Call:**
- ✅ Role's permissions are added or removed
- ✅ Role is deleted
- ✅ Role permissions are modified (wildcard changes, etc.)

**Example Usage:**
```python
from langflow.services.rbac import RBACEnforcementEngine

async def add_permission_to_role(session, role_id, permission_id):
    # Add permission to role
    role_permission = RolePermission(
        role_id=role_id,
        permission_id=permission_id,
    )
    session.add(role_permission)
    await session.commit()

    # Invalidate entire cache
    engine = RBACEnforcementEngine(session)
    await engine.invalidate_role_cache(role_id)
```

**Impact:** **Clears entire cache** (coarse-grained invalidation)

**Rationale:** Tracking all users with a specific role is complex. For MVP, we clear the entire cache on role changes since role permission changes are infrequent.

**Performance:** O(n) where n = total cache size (typically <10,000 entries)

**Warning:** This is the most expensive invalidation operation. Consider implementing role → user mapping for targeted invalidation in production.

**Future Optimization:**
```python
# Future enhancement (Task 2.3+)
async def invalidate_role_cache_targeted(role_id: UUID):
    # Query all users/groups with this role
    users_with_role = await get_users_with_role(role_id)
    groups_with_role = await get_groups_with_role(role_id)

    # Invalidate only affected users
    for user_id in users_with_role:
        await invalidate_user_cache(user_id)

    # Invalidate all users in affected groups
    for group_id in groups_with_role:
        group_members = await get_group_members(group_id)
        for user_id in group_members:
            await invalidate_user_cache(user_id)
```

---

### 3. Resource-Level Invalidation

**Method:** `invalidate_resource_cache(resource_type: str, resource_id: UUID)`

**Purpose:** Invalidates all cached permission entries for a specific resource.

**When to Call:**
- ✅ Resource-scoped role assignment changes (e.g., role assigned at flow scope)
- ✅ Resource is moved to different workspace/project (scope chain changes)
- ✅ Resource is deleted

**Example Usage:**
```python
from langflow.services.rbac import RBACEnforcementEngine

async def move_flow_to_different_project(session, flow_id, new_project_id):
    # Update flow's project
    flow = await session.get(Flow, flow_id)
    flow.folder_id = new_project_id
    session.add(flow)
    await session.commit()

    # Invalidate resource cache (scope chain changed)
    engine = RBACEnforcementEngine(session)
    await engine.invalidate_resource_cache("flow", flow_id)
```

**Impact:** Clears all permission cache entries where the cache key ends with `:{resource_type}:{resource_id}`

**Performance:** O(n) where n = number of users who have checked permissions on this resource (typically <100)

---

## Event-Based Invalidation (Task 2.2)

**Current State:** Manual invalidation methods are implemented in Task 2.1.

**Task 2.2 Scope:** Wire up automatic invalidation via event listeners.

### Recommended Event Listeners for Task 2.2

#### Database Events

```python
from sqlalchemy import event
from langflow.services.database.models.rbac import RoleAssignment, RolePermission
from langflow.services.rbac import get_enforcement_engine

# User role assignment events
@event.listens_for(RoleAssignment, 'after_insert')
async def on_role_assignment_created(mapper, connection, target):
    engine = get_enforcement_engine()
    if target.assignee_type == "user":
        await engine.invalidate_user_cache(target.user_id)
    elif target.assignee_type == "group":
        # Invalidate all users in the group
        group_members = await get_group_members(target.group_id)
        for member_user_id in group_members:
            await engine.invalidate_user_cache(member_user_id)

@event.listens_for(RoleAssignment, 'after_delete')
async def on_role_assignment_deleted(mapper, connection, target):
    # Same logic as after_insert
    ...

@event.listens_for(RoleAssignment, 'after_update')
async def on_role_assignment_updated(mapper, connection, target):
    # Handle is_active or expires_at changes
    ...

# Role permission events
@event.listens_for(RolePermission, 'after_insert')
@event.listens_for(RolePermission, 'after_delete')
async def on_role_permissions_changed(mapper, connection, target):
    engine = get_enforcement_engine()
    await engine.invalidate_role_cache(target.role_id)

# Group membership events
@event.listens_for(UserGroupMember, 'after_insert')
@event.listens_for(UserGroupMember, 'after_delete')
@event.listens_for(UserGroupMember, 'after_update')
async def on_group_membership_changed(mapper, connection, target):
    engine = get_enforcement_engine()
    await engine.invalidate_user_cache(target.user_id)

# Resource movement events
@event.listens_for(Flow, 'after_update')
async def on_flow_moved(mapper, connection, target):
    if target.folder_id_changed or target.environment_id_changed:
        engine = get_enforcement_engine()
        await engine.invalidate_resource_cache("flow", target.id)
```

#### API Endpoint Integration

For endpoints that modify RBAC state:

```python
@router.post("/role-assignments")
async def create_role_assignment(
    assignment: RoleAssignmentCreate,
    session: AsyncSession = Depends(get_session),
    engine: RBACEnforcementEngine = Depends(get_enforcement_engine),
):
    # Create assignment
    db_assignment = RoleAssignment(**assignment.dict())
    session.add(db_assignment)
    await session.commit()

    # Invalidate cache
    if assignment.assignee_type == "user":
        await engine.invalidate_user_cache(assignment.user_id)
    elif assignment.assignee_type == "group":
        # Invalidate all group members
        members = await get_group_members(session, assignment.group_id)
        for member in members:
            await engine.invalidate_user_cache(member.user_id)

    return db_assignment
```

---

## Invalidation Decision Tree

Use this flowchart to determine which invalidation method to call:

```
START
  |
  ├─ Did a user's role assignment change?
  │   └─ YES → invalidate_user_cache(user_id)
  |
  ├─ Did a user join/leave a group?
  │   └─ YES → invalidate_user_cache(user_id)
  |
  ├─ Did a group membership status change (is_active)?
  │   └─ YES → invalidate_user_cache(user_id)
  |
  ├─ Did a group's role assignment change?
  │   └─ YES → invalidate_user_cache() for all group members
  |
  ├─ Did a role's permissions change?
  │   └─ YES → invalidate_role_cache(role_id)
  |
  ├─ Was a role deleted?
  │   └─ YES → invalidate_role_cache(role_id)
  |
  ├─ Did a resource-scoped assignment change?
  │   └─ YES → invalidate_resource_cache(resource_type, resource_id)
  |
  ├─ Did a resource move to different workspace/project?
  │   └─ YES → invalidate_resource_cache(resource_type, resource_id)
  |
  └─ Was a resource deleted?
      └─ YES → invalidate_resource_cache(resource_type, resource_id)
```

---

## Performance Considerations

### Cache Hit Rate

**Expected:** >90% cache hit rate in production

**Monitoring:**
```python
# Add metrics collection (Task 2.3+)
cache_stats = engine.cache.get_stats()
hit_rate = cache_stats["hits"] / (cache_stats["hits"] + cache_stats["misses"])
```

### Invalidation Frequency

**Typical Frequencies:**
- User-level: 10-50 times per hour per active workspace
- Role-level: 1-5 times per day (infrequent)
- Resource-level: 50-200 times per hour per active workspace

### TTL vs Manual Invalidation

**TTL (Time-To-Live):**
- **Default:** 300 seconds (5 minutes)
- **Purpose:** Automatic cleanup, fallback for missed invalidation
- **Trade-off:** Stale data possible for up to 5 minutes if invalidation missed

**Manual Invalidation:**
- **Purpose:** Immediate consistency
- **Trade-off:** Requires careful implementation to catch all state changes

**Recommendation:** Use both - TTL as safety net, manual invalidation for immediate consistency.

---

## Testing Invalidation

### Unit Test Example

```python
@pytest.mark.asyncio
async def test_cache_invalidation_on_role_assignment_change():
    """Test cache is invalidated when user role assignment changes."""
    # 1. Check permission (cache miss, caches result)
    has_perm_before = await engine.has_permission(user_id, "flow.read", "flow", flow_id)
    assert has_perm_before is False

    # 2. Assign role to user
    assignment = RoleAssignment(role_id=role_id, user_id=user_id, ...)
    session.add(assignment)
    await session.commit()

    # 3. Invalidate cache
    await engine.invalidate_user_cache(user_id)

    # 4. Check permission again (cache miss, queries DB)
    has_perm_after = await engine.has_permission(user_id, "flow.read", "flow", flow_id)
    assert has_perm_after is True  # Should see new assignment
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_permission_change_reflects_immediately():
    """Test permission changes reflect immediately after invalidation."""
    # User has no permissions
    can_read_before = await engine.check_resource_access(user_id, "read", "flow", flow_id)
    assert can_read_before is False

    # Assign reader role via API endpoint (should auto-invalidate)
    response = await client.post(
        "/api/v1/role-assignments",
        json={"user_id": str(user_id), "role_id": str(reader_role_id), ...}
    )
    assert response.status_code == 200

    # Permission should be granted immediately (no cache staleness)
    can_read_after = await engine.check_resource_access(user_id, "read", "flow", flow_id)
    assert can_read_after is True
```

---

## Common Pitfalls

### ❌ Pitfall 1: Forgetting to Invalidate After Group Membership Changes

```python
# WRONG - Cache not invalidated
async def add_user_to_group(session, user_id, group_id):
    membership = UserGroupMember(user_id=user_id, group_id=group_id)
    session.add(membership)
    await session.commit()
    # BUG: User won't see group permissions until cache expires (5 min)

# CORRECT
async def add_user_to_group(session, user_id, group_id, engine):
    membership = UserGroupMember(user_id=user_id, group_id=group_id)
    session.add(membership)
    await session.commit()
    await engine.invalidate_user_cache(user_id)  # ✅
```

### ❌ Pitfall 2: Using Wrong Invalidation Method

```python
# WRONG - Should invalidate user, not resource
async def grant_workspace_admin(session, user_id, workspace_id, engine):
    assignment = RoleAssignment(...)
    session.add(assignment)
    await session.commit()
    await engine.invalidate_resource_cache("workspace", workspace_id)  # ❌
    # This invalidates workspace cache, not user cache

# CORRECT
async def grant_workspace_admin(session, user_id, workspace_id, engine):
    assignment = RoleAssignment(...)
    session.add(assignment)
    await session.commit()
    await engine.invalidate_user_cache(user_id)  # ✅
```

### ❌ Pitfall 3: Forgetting Group Members on Group Assignment

```python
# WRONG - Only invalidates group, not members
async def assign_role_to_group(session, group_id, role_id, engine):
    assignment = RoleAssignment(group_id=group_id, role_id=role_id, ...)
    session.add(assignment)
    await session.commit()
    # BUG: Group members won't see new permissions until cache expires

# CORRECT
async def assign_role_to_group(session, group_id, role_id, engine):
    assignment = RoleAssignment(group_id=group_id, role_id=role_id, ...)
    session.add(assignment)
    await session.commit()

    # Invalidate all group members
    members = await session.execute(
        select(UserGroupMember.user_id)
        .where(UserGroupMember.group_id == group_id, UserGroupMember.is_active == True)
    )
    for (user_id,) in members:
        await engine.invalidate_user_cache(user_id)  # ✅
```

---

## Redis Integration (Future)

For multi-instance deployments, replace in-memory cache with Redis:

```python
# Future implementation (post-MVP)
import redis.asyncio as redis

class RedisPermissionCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.ttl = 300  # 5 minutes

    async def get(self, user_id, permission, resource_type, resource_id):
        key = f"perm:{user_id}:{permission}:{resource_type}:{resource_id}"
        value = await self.redis.get(key)
        return bool(int(value)) if value else None

    async def set(self, user_id, permission, resource_type, resource_id, value):
        key = f"perm:{user_id}:{permission}:{resource_type}:{resource_id}"
        await self.redis.setex(key, self.ttl, int(value))

    async def invalidate_user(self, user_id):
        # Use Redis SCAN to find and delete user keys
        pattern = f"perm:{user_id}:*"
        async for key in self.redis.scan_iter(pattern):
            await self.redis.delete(key)

    # Pub/sub for cache invalidation across instances
    async def publish_invalidation(self, user_id):
        await self.redis.publish("rbac:invalidate:user", str(user_id))
```

---

## Summary

**Key Takeaways:**
1. ✅ Use `invalidate_user_cache()` for user-level changes (most common)
2. ✅ Use `invalidate_role_cache()` for role permission changes (rare, expensive)
3. ✅ Use `invalidate_resource_cache()` for resource movements (moderate)
4. ✅ **Always invalidate after state changes** - never rely solely on TTL
5. ✅ When in doubt, invalidate more rather than less (correctness > performance)

**For Task 2.2 Implementers:**
- Wire up event listeners for automatic invalidation
- Test invalidation thoroughly (unit + integration tests)
- Monitor cache hit rate in production
- Consider implementing targeted role invalidation (optimization)

**For Future Maintainers:**
- Follow this strategy when adding new RBAC features
- Update this document if invalidation strategy changes
- Consider Redis for multi-instance deployments

---

**Document Owner:** RBAC Team
**Last Updated:** October 11, 2025
**Next Review:** Task 2.2 Completion
