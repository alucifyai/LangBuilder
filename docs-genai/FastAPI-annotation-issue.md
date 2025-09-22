# FastAPI Dependency Injection and Annotation Issues

## Initial Question

In `/src/api/v1/projects.py` line 112, why does:
```python
current_user: CurrentActiveUser,
```
work with utils.py definition:
```python
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
```

But if I change to line 113:
```python
current_user: Annotated[CurrentActiveUser, Depends(get_authorized_user)],
```
The API stops working?

In authorization_pattern.py, we have:
```python
async def get_authorized_user(
    context: Annotated[RuntimeEnforcementContext, Depends(get_enhanced_enforcement_context)],
) -> CurrentActiveUser:
```

Will the context be injected as well from the API's context annotation, or does it just follow the Depends structure?

## Answer: FastAPI Dependency Injection Patterns

### Why the first version works:

```python
current_user: CurrentActiveUser,
```

Where `CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]`

This works because `CurrentActiveUser` is **already a complete dependency annotation**. FastAPI sees the `Annotated[User, Depends(get_current_active_user)]` and knows exactly what to inject.

### Why the second version breaks:

```python
current_user: Annotated[CurrentActiveUser, Depends(get_authorized_user)],
```

This creates a **nested dependency annotation** that becomes:
```python
Annotated[
    Annotated[User, Depends(get_current_active_user)],  # CurrentActiveUser
    Depends(get_authorized_user)                        # Additional dependency
]
```

This confuses FastAPI because you're trying to apply `Depends(get_authorized_user)` to something that's already a dependency annotation.

### The correct way to use `get_authorized_user`:

Since `get_authorized_user` returns `CurrentActiveUser` (which is the `User` type), you should use:

```python
current_user: Annotated[User, Depends(get_authorized_user)],
```

**NOT:**
```python
current_user: Annotated[CurrentActiveUser, Depends(get_authorized_user)],  # Double wrapping!
```

## Context Injection and Dependency Resolution

### Yes, context will be injected automatically!

FastAPI's dependency injection follows this pattern:

1. **When `get_authorized_user` is called as a dependency**, FastAPI analyzes its signature
2. **It sees that `context` parameter needs `RuntimeEnforcementContext`**
3. **It automatically calls `get_enhanced_enforcement_context()` to provide that parameter**
4. **This happens recursively** - if `get_enhanced_enforcement_context` needs other dependencies, those get injected too

## What `get_enhanced_enforcement_context()` Actually Does

### Function Signature and Purpose
```python
async def get_enhanced_enforcement_context(
    request: Request,
    session: Annotated[DbSession, Depends()],
    current_user: Annotated[CurrentActiveUser, Depends()],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> RuntimeEnforcementContext:
```

### Authentication and Context Building

**Yes, `get_enhanced_enforcement_context()` does check JWT tokens and API keys**, but in a different way than `get_current_active_user`:

#### 1. **Leverages Existing Authentication**
```python
current_user: Annotated[CurrentActiveUser, Depends()],
```
- This parameter **depends on the full authentication chain**
- `CurrentActiveUser` → `get_current_active_user` → `get_current_user`
- So JWT tokens and API keys are **already validated** when this function runs

#### 2. **Extracts Additional Authentication Context**
```python
# Extract API key from multiple sources
api_key = None
if credentials:
    api_key = credentials.credentials  # From Authorization header
else:
    api_key = request.headers.get("x-api-key") or request.query_params.get("x-api-key")
```

#### 3. **Builds Resource Context**
```python
# Extract resource context from URL path parameters
workspace_id = request.path_params.get("workspace_id")
project_id = request.path_params.get("project_id")
environment_id = request.path_params.get("environment_id")
flow_id = request.path_params.get("flow_id")
```

#### 4. **Creates Runtime Enforcement Context**
```python
return await enforcement_service.create_enforcement_context(
    session=session,
    api_key=api_key,
    user=current_user,  # Already authenticated user
    workspace_id=UUID(workspace_id) if workspace_id else None,
    project_id=UUID(project_id) if project_id else None,
    environment_id=UUID(environment_id) if environment_id else None,
    request_path=request.url.path,
    request_method=request.method,
)
```

## How `get_authorized_user` Uses the Context

```python
async def get_authorized_user(
    context: Annotated[RuntimeEnforcementContext, Depends(get_enhanced_enforcement_context)],
) -> CurrentActiveUser:
    """Get current user with basic authorization validation."""
    if not context.user or not context.user.is_active:
        raise AuthorizationError("User not authenticated or inactive")
    return context.user
```

### Authentication Flow Comparison

#### `get_current_active_user` (Simple Authentication):
1. Extract JWT token or API key from request
2. Validate token/key against database
3. Return user if valid and active
4. **Direct authentication validation**

#### `get_authorized_user` (Enhanced Authentication + Authorization):
1. **Relies on `get_enhanced_enforcement_context`** which:
   - Uses `CurrentActiveUser` (already authenticated via `get_current_active_user`)
   - Extracts additional context (API keys, resource IDs, request info)
   - Builds comprehensive enforcement context for RBAC
2. **Validates the context.user is active**
3. **Returns the same user but with RBAC context available**

### Key Differences

| Aspect | `get_current_active_user` | `get_authorized_user` |
|--------|-------------------------|---------------------|
| **Authentication** | Direct JWT/API key validation | Inherits from `CurrentActiveUser` dependency |
| **Context** | Basic user authentication | Enhanced RBAC enforcement context |
| **Purpose** | Simple auth check | Auth + authorization preparation |
| **Performance** | Faster (fewer dependencies) | Slower (builds full RBAC context) |
| **Use Case** | Basic authenticated endpoints | RBAC-enabled endpoints |

## Summary

- **`get_enhanced_enforcement_context()` does NOT duplicate authentication** - it builds on already-authenticated users
- **JWT tokens and API keys are validated by the underlying `CurrentActiveUser` dependency**
- **The context provides additional RBAC information** like resource IDs, request metadata, and enforcement capabilities
- **Context injection happens automatically** through FastAPI's dependency system
- **Use `Annotated[User, Depends(get_authorized_user)]`** for RBAC-enabled endpoints, not double-wrapped annotations

This design allows for layered security where basic authentication is handled at the lower level, and enhanced authorization context is built on top for RBAC-enabled endpoints.