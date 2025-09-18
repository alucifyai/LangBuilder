# Phase 5 RBAC Advanced Features - Implementation Documentation

## Overview

This document provides comprehensive documentation for the Phase 5 RBAC Advanced Features implementation in LangBuilder. Phase 5 introduces enterprise-grade security features including multi-environment permission scoping, service account management, break-glass emergency access, and advanced compliance capabilities.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [API Reference](#api-reference)
4. [Service Account Management](#service-account-management)
5. [Multi-Environment Support](#multi-environment-support)
6. [Break-Glass Emergency Access](#break-glass-emergency-access)
7. [Compliance and Audit](#compliance-and-audit)
8. [Integration Guide](#integration-guide)
9. [Configuration](#configuration)
10. [Performance Considerations](#performance-considerations)

## Architecture Overview

### System Design

Phase 5 extends the existing RBAC infrastructure with advanced security features:

```
┌─────────────────────────────────────────────────────────────┐
│                     LangBuilder RBAC System                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Phase 5 Advanced Features               │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │                                                      │  │
│  │  ┌────────────────┐  ┌────────────────────────┐    │  │
│  │  │  Multi-Env     │  │  Service Account      │    │  │
│  │  │  Permissions   │  │  Management           │    │  │
│  │  └────────────────┘  └────────────────────────┘    │  │
│  │                                                      │  │
│  │  ┌────────────────┐  ┌────────────────────────┐    │  │
│  │  │  Break-Glass   │  │  Advanced Audit       │    │  │
│  │  │  Access        │  │  & Compliance         │    │  │
│  │  └────────────────┘  └────────────────────────┘    │  │
│  │                                                      │  │
│  │  ┌─────────────────────────────────────────────┐    │  │
│  │  │      Conditional Permission Engine          │    │  │
│  │  └─────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Existing RBAC Infrastructure (Ph 1-4)      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **AdvancedRBACFeaturesService** - Core service orchestrating all Phase 5 features
2. **Environment Model** - Multi-environment permission scoping
3. **ServiceAccount Model** - Automated access with scoped tokens
4. **ConditionalPermissionContext** - Request evaluation context
5. **ComplianceReportGenerator** - SOC2, ISO27001, GDPR, CCPA reporting

## Core Components

### AdvancedRBACFeaturesService

Located at: `src/backend/base/langflow/services/rbac/advanced_features_service.py`

**Key Methods:**

```python
# Check environment-specific permissions
async def check_environment_permission(
    session: AsyncSession,
    user: User,
    environment_id: str,
    action: str,
    context: ConditionalPermissionContext | None = None
) -> bool

# Create service account with scoped token
async def create_service_account_with_token(
    session: AsyncSession,
    name: str,
    workspace_id: str,
    created_by_id: str,
    scoped_permissions: list[str] | None = None,
    scope_type: str | None = None,
    scope_id: str | None = None
) -> tuple[ServiceAccount, str]

# Evaluate break-glass access request
async def evaluate_break_glass_access(
    session: AsyncSession,
    user: User,
    resource_id: str,
    resource_type: str,
    justification: str,
    duration_minutes: int = 60
) -> BreakGlassAccessResult

# Generate compliance report
async def generate_compliance_report(
    session: AsyncSession,
    report_type: str,
    workspace_id: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None
) -> dict[str, Any]
```

### Database Models

#### Environment Model

```python
class Environment(SQLModel):
    id: UUID
    name: str
    environment_type: EnvironmentType
    workspace_id: UUID
    is_production: bool
    allowed_actions: list[str]
    restricted_resources: list[str]
    require_mfa: bool
    require_approval: bool
    allowed_ip_ranges: list[str]
    allowed_time_windows: list[str]
```

#### ServiceAccount Model

```python
class ServiceAccount(SQLModel):
    id: UUID
    name: str
    workspace_id: UUID
    service_type: str  # api, webhook, integration, bot
    token_prefix: str
    max_tokens: int
    token_expiry_days: int
    allowed_ips: list[str]
    allowed_permissions: list[str]
    is_active: bool
```

## API Reference

### Base URL

```
/api/v1/rbac-advanced
```

### Endpoints

#### 1. Check Environment Permission

```http
POST /environment/check-permission
Content-Type: application/json
Authorization: Bearer {token}

{
    "environment_id": "uuid",
    "action": "deploy",
    "context": {
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "has_mfa": true,
        "risk_score": 0.2
    }
}

Response:
{
    "allowed": true,
    "reason": "Permission granted",
    "conditions_met": ["ip_allowed", "mfa_verified"],
    "conditions_failed": []
}
```

#### 2. Create Service Account with Token

```http
POST /service-account/create-with-token
Content-Type: application/json
Authorization: Bearer {token}

{
    "name": "github-integration",
    "workspace_id": "uuid",
    "service_type": "integration",
    "integration_name": "github",
    "scoped_permissions": ["flows:read", "flows:execute"],
    "scope_type": "workspace",
    "scope_id": "uuid",
    "allowed_ips": ["192.168.0.0/24"],
    "token_expiry_days": 90
}

Response:
{
    "service_account": {
        "id": "uuid",
        "name": "github-integration",
        "service_type": "integration"
    },
    "token": {
        "id": "uuid",
        "token": "sa_abc123...",  // Only shown once
        "token_prefix": "sa_abc1",
        "expires_at": "2024-03-15T00:00:00Z"
    }
}
```

#### 3. Request Break-Glass Access

```http
POST /break-glass/request-access
Content-Type: application/json
Authorization: Bearer {token}

{
    "resource_id": "uuid",
    "resource_type": "production_database",
    "justification": "Critical production issue #12345",
    "duration_minutes": 60,
    "approver_ids": ["uuid1", "uuid2"]
}

Response:
{
    "request_id": "uuid",
    "status": "approved",
    "access_token": "temp_token_xyz",
    "expires_at": "2024-01-15T13:00:00Z",
    "audit_log_id": "uuid"
}
```

#### 4. Generate Compliance Report

```http
POST /compliance/generate-report
Content-Type: application/json
Authorization: Bearer {token}

{
    "report_type": "SOC2",  // SOC2, ISO27001, GDPR, CCPA
    "workspace_id": "uuid",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "include_details": true
}

Response:
{
    "report_id": "uuid",
    "report_type": "SOC2",
    "period": {
        "start": "2024-01-01",
        "end": "2024-01-31"
    },
    "summary": {
        "controls_tested": 15,
        "controls_passed": 14,
        "controls_failed": 1,
        "compliance_score": 0.93
    },
    "details": [...],
    "generated_at": "2024-02-01T10:00:00Z"
}
```

## Service Account Management

### Creating Service Accounts

Service accounts enable automated access for integrations, CI/CD pipelines, and external systems.

```python
from langflow.services.rbac.advanced_features_service import get_advanced_rbac_service

# Create service account for GitHub Actions
service_account, token = await service.create_service_account_with_token(
    session=session,
    name="github-actions-prod",
    workspace_id=workspace_id,
    created_by_id=user_id,
    service_type="integration",
    integration_name="github",
    scoped_permissions=["flows:read", "flows:execute", "deployments:create"],
    scope_type="environment",
    scope_id=production_env_id,
    allowed_ips=["140.82.112.0/20"],  # GitHub Actions IP range
    token_expiry_days=365
)

# Token is returned only once - store securely
print(f"Service Account Token: {token}")
```

### Token Scoping

Tokens can be scoped at multiple levels:

1. **Workspace Scope** - Access to entire workspace
2. **Project Scope** - Access to specific project
3. **Environment Scope** - Access to specific environment
4. **Resource Scope** - Access to specific resources

### Token Validation

```python
# Validate token scope for specific action
is_valid = await service.validate_service_account_token_scope(
    session=session,
    token_hash=hashed_token,
    required_permission="flows:execute",
    scope_type="environment",
    scope_id=environment_id
)
```

## Multi-Environment Support

### Environment Types

```python
class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    QA = "qa"
    SANDBOX = "sandbox"
    CUSTOM = "custom"
```

### Environment-Specific Permissions

Configure permissions per environment:

```python
# Production environment - restrictive
production_env = Environment(
    name="Production",
    environment_type=EnvironmentType.PRODUCTION,
    is_production=True,
    allowed_actions=["read", "execute"],
    restricted_resources=["admin_panel", "billing"],
    require_mfa=True,
    require_approval=True,
    allowed_ip_ranges=["10.0.0.0/8"],
    allowed_time_windows=["09:00-17:00 UTC"]
)

# Development environment - permissive
dev_env = Environment(
    name="Development",
    environment_type=EnvironmentType.DEVELOPMENT,
    is_production=False,
    allowed_actions=["*"],
    restricted_resources=[],
    require_mfa=False,
    require_approval=False
)
```

## Break-Glass Emergency Access

### When to Use

Break-glass access should be used only for:
- Critical production incidents
- Security emergencies
- Time-sensitive issues when normal approvers are unavailable

### Request Process

```python
# Request emergency access
result = await service.evaluate_break_glass_access(
    session=session,
    user=user,
    resource_id=production_db_id,
    resource_type="database",
    justification="Database corruption affecting 1000+ users - Incident #12345",
    duration_minutes=60,
    approver_ids=[manager_id, security_team_id]
)

if result.granted:
    # Use temporary elevated access
    temp_token = result.access_token
    expires_at = result.expires_at
    
    # All actions are logged
    audit_log_id = result.audit_log_id
```

### Audit Trail

All break-glass access is logged with:
- Requester identity
- Justification provided
- Resources accessed
- Actions performed
- Duration of access
- Approval chain

## Compliance and Audit

### Supported Standards

1. **SOC2 Type II** - Security controls audit
2. **ISO 27001** - Information security management
3. **GDPR** - EU data protection
4. **CCPA** - California privacy rights

### Generating Reports

```python
# Generate SOC2 compliance report
report = await service.generate_compliance_report(
    session=session,
    report_type="SOC2",
    workspace_id=workspace_id,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)

# Report includes:
# - Access control effectiveness
# - Permission usage patterns
# - Security incidents
# - Policy violations
# - Remediation actions
```

### Audit Logging

All security-relevant events are logged:

```python
await service._log_audit_event(
    session=session,
    event_type="permission_check",
    actor_id=user_id,
    resource_id=resource_id,
    action="deploy",
    result="denied",
    context={
        "environment": "production",
        "reason": "MFA not verified",
        "ip_address": request_ip
    }
)
```

## Integration Guide

### With Existing RBAC

Phase 5 seamlessly integrates with existing RBAC:

```python
from langflow.services.rbac.service import RBACService
from langflow.services.rbac.advanced_features_service import get_advanced_rbac_service

# Standard permission check
rbac_service = get_rbac_service()
has_permission = await rbac_service.check_permission(
    session, user, "flows:read", workspace_id
)

# Enhanced with environment context
advanced_service = get_advanced_rbac_service()
has_env_permission = await advanced_service.check_environment_permission(
    session, user, production_env_id, "deploy", context
)
```

### With Flow Execution

```python
from langflow.services.rbac.advanced_features_service import ConditionalPermissionContext

# Build context for flow execution
context = ConditionalPermissionContext(
    request_time=datetime.now(timezone.utc),
    ip_address=request.client.host,
    user_agent=request.headers.get("User-Agent"),
    has_mfa=user.mfa_verified,
    risk_score=calculate_risk_score(user, request),
    custom_attributes={"flow_sensitivity": "high"}
)

# Check permission with context
if await advanced_service.check_environment_permission(
    session, user, env_id, "flows:execute", context
):
    # Execute flow
    result = await flow_service.execute(flow_id)
```

## Configuration

### Environment Variables

```bash
# Service Account Configuration
RBAC_SERVICE_ACCOUNT_MAX_TOKENS=10
RBAC_SERVICE_ACCOUNT_TOKEN_LENGTH=64
RBAC_SERVICE_ACCOUNT_DEFAULT_EXPIRY_DAYS=365

# Break-Glass Configuration
RBAC_BREAK_GLASS_MAX_DURATION_MINUTES=240
RBAC_BREAK_GLASS_REQUIRE_APPROVAL=true
RBAC_BREAK_GLASS_AUTO_APPROVE_THRESHOLD=0.9

# Compliance Configuration
RBAC_COMPLIANCE_RETENTION_DAYS=2555  # 7 years
RBAC_COMPLIANCE_ENCRYPT_REPORTS=true

# Performance Configuration
RBAC_CACHE_TTL_SECONDS=300
RBAC_MAX_CONCURRENT_CHECKS=100
```

### Database Configuration

Ensure proper indexes for performance:

```sql
-- Environment permissions index
CREATE INDEX idx_env_perm_lookup 
ON environment_permission(environment_id, user_id, permission);

-- Service account token index
CREATE INDEX idx_sa_token_lookup 
ON service_account_token(token_hash, is_active);

-- Audit log index
CREATE INDEX idx_audit_timestamp 
ON audit_log(created_at DESC, event_type);
```

## Performance Considerations

### Optimization Strategies

1. **Caching** - Permission decisions cached for 5 minutes
2. **Connection Pooling** - Reuse database connections
3. **Async Operations** - All I/O operations are async
4. **Batch Processing** - Bulk permission checks supported
5. **Index Optimization** - Proper database indexes

### Performance Metrics

Target performance (p95 latency):
- Permission check: <100ms
- Token validation: <50ms
- Report generation: <5s
- Break-glass evaluation: <200ms

### Monitoring

Key metrics to monitor:
- Permission check latency
- Cache hit rate
- Token validation failures
- Break-glass access frequency
- Compliance report generation time

## Security Considerations

### Best Practices

1. **Token Security**
   - Store tokens securely (never in plain text)
   - Rotate tokens regularly
   - Use strong entropy for token generation
   - Implement token revocation

2. **Network Security**
   - Enforce IP restrictions for service accounts
   - Use TLS for all API communications
   - Implement rate limiting
   - Monitor for anomalous access patterns

3. **Audit Security**
   - Protect audit logs from tampering
   - Implement log retention policies
   - Forward logs to SIEM systems
   - Regular audit log reviews

4. **Break-Glass Security**
   - Require strong justification
   - Implement approval workflows
   - Time-bound access only
   - Comprehensive audit trail
   - Regular review of break-glass usage

## Troubleshooting

### Common Issues

1. **Permission Denied in Production**
   - Check MFA status
   - Verify IP restrictions
   - Check time windows
   - Review environment configuration

2. **Service Account Token Invalid**
   - Check token expiration
   - Verify IP restrictions
   - Check scope alignment
   - Review token revocation status

3. **Break-Glass Access Denied**
   - Verify user has break-glass permission
   - Check justification requirements
   - Verify approver availability
   - Review security policies

4. **Compliance Report Generation Fails**
   - Check date range validity
   - Verify workspace access
   - Check audit log availability
   - Review report permissions

### Debug Logging

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger("langflow.services.rbac").setLevel(logging.DEBUG)
```

## Migration Guide

### From Phase 4 to Phase 5

1. **Database Migration**
   ```bash
   alembic upgrade head
   ```

2. **Update Configuration**
   - Add Phase 5 environment variables
   - Configure service account settings
   - Set compliance requirements

3. **Update Permissions**
   - Grant break-glass permissions to admins
   - Configure environment-specific permissions
   - Set up service account permissions

4. **Testing**
   - Run Phase 5 validation script
   - Test service account creation
   - Verify break-glass access
   - Generate sample compliance reports

## Appendix

### Permission Matrix

| Feature | Required Permission | Scope |
|---------|-------------------|-------|
| Check environment permission | `environments:read` | Workspace |
| Create service account | `service_accounts:create` | Workspace |
| Generate token | `service_accounts:manage` | Workspace |
| Request break-glass | `break_glass:request` | Global |
| Approve break-glass | `break_glass:approve` | Global |
| Generate compliance report | `compliance:generate` | Workspace |

### Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| RBAC_5001 | Invalid environment | Check environment exists |
| RBAC_5002 | Service account limit exceeded | Increase max_tokens limit |
| RBAC_5003 | Token expired | Generate new token |
| RBAC_5004 | Break-glass denied | Check permissions and justification |
| RBAC_5005 | Compliance report failed | Verify report type and date range |

### Related Documentation

- [RBAC Implementation Plan](../RBAC_IMPLEMENTATION_PLAN.md)
- [Phase 1-4 Documentation](./PHASE1-4_DOCUMENTATION.md)
- [API Reference](../api/README.md)
- [Security Guidelines](../security/GUIDELINES.md)

---

*Last Updated: January 2024*
*Version: 1.0.0*
*Status: Production Ready*