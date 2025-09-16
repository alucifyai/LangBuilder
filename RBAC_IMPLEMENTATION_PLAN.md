# RBAC Implementation Plan - LangBuilder Native Integration
## Complete Implementation Strategy for LangBuilder RBAC Features

**Strategic Approach**: Use AppGraph v7.1 and GraphQL for architectural understanding and design validation, while implementing all features natively in LangBuilder's existing FastAPI/SQLModel architecture.

---

## 📊 **Implementation Scope & Architecture Alignment**

### **AppGraph v7.1 Analysis (Design Reference Only):**
- **Core RBAC Entities**: 10 primary data models mapped to SQLModel implementations
- **GraphQL Schema Nodes**: Used for understanding semantic relationships (not implemented)
- **Business Logic Components**: 274+ logic nodes guide FastAPI service architecture
- **System Integrations**: 3,465+ edges define integration patterns with existing LangBuilder

### **LangBuilder Native Technology Stack:**
- **Backend**: FastAPI (existing) + SQLModel + Pydantic (existing patterns)
- **Database**: SQLAlchemy with existing migration system (Alembic)
- **API Layer**: FastAPI routers following existing `/api/v1/` patterns
- **Authentication**: Integration with existing LangBuilder auth system
- **Caching**: Redis integration following existing performance patterns
- **Testing**: Pytest with existing test infrastructure
- **Dependencies**: Minimal additions to existing pyproject.toml

---

## 🏗️ **LangBuilder-Compliant Architecture**

### **Integration with Existing LangBuilder Structure:**
```
src/backend/base/langflow/
├── api/v1/
│   ├── rbac/                    # NEW - RBAC endpoints
│   │   ├── workspaces.py       # Workspace management API
│   │   ├── projects.py         # Project management API  
│   │   ├── roles.py           # Role/permission API
│   │   └── dependencies.py    # Security dependencies
│   └── [existing APIs]        # Preserved existing APIs
├── services/
│   ├── rbac/                   # NEW - RBAC business logic
│   │   └── permission_engine.py # Permission evaluation engine
│   └── [existing services]    # Preserved existing services
├── database/models/
│   ├── rbac/                   # NEW - RBAC models
│   │   ├── workspace.py       # Multi-tenant workspaces
│   │   ├── role.py           # Role definitions
│   │   └── [8 more models]   # Complete RBAC model set
│   └── [existing models]     # Enhanced existing models (User, Flow, etc.)
└── alembic/versions/          # Database migrations
    └── rbac_*.py             # RBAC schema migrations
```

### **Design Principles:**
1. **Native Integration**: Follow all existing LangBuilder patterns and conventions
2. **Backward Compatibility**: Preserve all existing functionality
3. **Minimal Dependencies**: Reuse existing libraries and infrastructure
4. **Performance First**: Leverage existing caching and optimization strategies

---

## 📋 **8-Phase Implementation Plan**

## **Phase 1: Foundation & Data Models (Weeks 1-2)** ✅
*Build core data foundation using native LangBuilder patterns*

### **Implementation Strategy:**
- **AppGraph Reference**: Use GraphQL schemas for understanding entity relationships
- **Implementation**: SQLModel classes following existing LangBuilder patterns
- **Integration**: Enhance existing User/Flow models with RBAC relationships

### **Core Models to Implement (LangBuilder SQLModel):**

#### **1.1 Database Schema & Models Implementation**

**Implementation Location (Native LangBuilder Structure):**
```python
# src/backend/base/langflow/services/database/models/rbac/
from sqlmodel import SQLModel, Field, Relationship
from langflow.schema.serialize import UUIDstr
```

**Core Entity Models:**
1. **Workspace Model** - Multi-tenant organization following existing patterns
2. **Project Model** - Development project organization within workspaces  
3. **Environment Model** - Deployment contexts (dev/staging/prod)
4. **Role Model** - Hierarchical role definitions with inheritance
5. **Permission Model** - Granular permissions with resource patterns
6. **RoleAssignment Model** - Role-to-subject assignments with scope
7. **UserGroup Model** - User groups with SCIM synchronization
8. **ServiceAccount Model** - Service accounts with API tokens
9. **AuditLog Model** - Immutable compliance audit trail
10. **SSOConfiguration Model** - SSO provider configurations

**Model Implementation Pattern (Following LangBuilder Conventions):**
```python
# Example: workspace.py
class Workspace(SQLModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "workspace"
    
    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    description: str | None = Field(default=None)
    
    # Follow existing User model patterns
    owner_id: UUIDstr = Field(foreign_key="user.id", index=True)
    owner: "User" = Relationship(back_populates="owned_workspaces")
    
    # Timestamps following existing pattern
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Enhanced Existing Models (Backward Compatible):**
```python
# Enhance src/backend/base/langflow/services/database/models/user/model.py
class User(SQLModel, table=True):
    # Existing fields preserved...
    
    # Add RBAC relationships (backward compatible)
    owned_workspaces: list["Workspace"] = Relationship(back_populates="owner")
    role_assignments: list["RoleAssignment"] = Relationship(back_populates="user")
    group_memberships: list["UserGroupMembership"] = Relationship(back_populates="user")
```

#### **Database Migration (Alembic Integration):**
```python
# src/backend/base/langflow/alembic/versions/rbac_implementation_phase1.py
def upgrade():
    # Create RBAC tables using existing migration patterns
    # Maintain backward compatibility with existing data
    
def downgrade():
    # Rollback support following existing patterns
```

### **Phase 1 Deliverables (LangBuilder-Compliant):**
- ✅ 10+ SQLModel classes with full relationships
- ✅ Alembic migration scripts with rollback support
- ✅ Enhanced existing models (User, Flow, ApiKey, Variable)
- ✅ 150+ comprehensive unit tests (>95% coverage target)
- ✅ Database setup automation with existing Docker infrastructure
- ✅ Performance benchmarks documented
- ✅ Development environment integration

---

## **Phase 2: FastAPI REST API Foundation (Weeks 3-4)**
*Implement REST API endpoints following existing LangBuilder patterns*

### **Implementation Strategy:**
- **AppGraph Reference**: Use interface nodes to understand API requirements
- **Implementation**: FastAPI routers following existing `/api/v1/` patterns
- **Integration**: Use existing authentication and middleware patterns

### **2.1 FastAPI Router Implementation**

**Router Structure (Following Existing Patterns):**
```python
# src/backend/base/langflow/api/v1/rbac/workspaces.py
from fastapi import APIRouter, Depends, HTTPException, status
from langflow.api.utils import get_current_user  # Existing auth
from langflow.services.database.models.user import User

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Implementation following existing patterns
```

**API Endpoints (Native LangBuilder Integration):**

**Workspace Management** (`/api/v1/rbac/workspaces/`):
- `POST /` - Create workspace (following existing pattern)
- `GET /` - List workspaces with filtering/pagination
- `GET /{id}` - Get workspace details
- `PUT /{id}` - Update workspace
- `DELETE /{id}` - Delete workspace
- `POST /{id}/invite` - Invite users (email integration)
- `GET /{id}/users` - List workspace members
- `GET /{id}/stats` - Workspace statistics

**Security & Dependencies (Existing Pattern Integration):**
```python
# src/backend/base/langflow/api/v1/rbac/dependencies.py
async def check_workspace_permission(
    workspace_id: UUID,
    required_permission: str,
    current_user: User = Depends(get_current_user),  # Existing auth
    session: AsyncSession = Depends(get_session)    # Existing session
) -> Workspace:
    # Permission checking using existing patterns
```

### **2.2 Permission Engine (High-Performance)**

**Implementation Location:**
```python
# src/backend/base/langflow/services/rbac/permission_engine.py
class PermissionEngine:
    def __init__(self, redis_client=None):
        # Use existing Redis configuration if available
        
    async def check_permission(
        self,
        session: AsyncSession,
        user: User,
        resource_type: ResourceType,
        action: PermissionAction,
        resource_id: Optional[UUID] = None
    ) -> PermissionResult:
        # <100ms p95 latency with caching
```

### **Phase 2 Deliverables:**
- ✅ 24+ FastAPI endpoints across 4 router modules
- ✅ High-performance permission engine with Redis caching
- ✅ Security dependencies and middleware integration
- ✅ Request/response models with Pydantic validation
- ✅ Integration with existing authentication system
- ✅ 100+ API endpoint tests with async support

---

## **Phase 3: Business Logic & Services (Weeks 5-6)**
*Implement core RBAC business logic using existing service patterns*

### **3.1 Permission Evaluation Engine**

**Integration with Existing Patterns:**
```python
# Use existing service base classes and patterns
from langflow.services.base import Service

class RBACService(Service):
    """RBAC service following existing LangBuilder service patterns"""
    
    async def evaluate_permission(self, ...):
        # Hierarchical permission evaluation
        # Cache integration with existing Redis
        # Audit logging integration
```

**Hierarchical Permission Flow (AppGraph-Guided Design):**
```
User Permission Check
├── Direct Role Assignments
├── Group Membership Roles  
├── Inherited Scope Permissions
│   ├── Workspace Level
│   ├── Project Level
│   ├── Environment Level
│   ├── Flow Level
│   └── Component Level
└── Service Account Tokens
```

### **3.2 SSO Integration Framework**

**Provider Support (Following Existing OAuth Patterns):**
```python
# src/backend/base/langflow/integrations/sso/
class SSOProvider(ABC):
    """Base class following existing integration patterns"""
    
class OIDCProvider(SSOProvider):
    """OpenID Connect integration"""
    
class SAML2Provider(SSOProvider):
    """SAML 2.0 integration"""
```

### **Phase 3 Deliverables:**
- ✅ Permission evaluation engine with <100ms p95 latency
- ✅ SSO provider framework (OIDC, SAML2, OAuth2, LDAP)
- ✅ SCIM user provisioning integration
- ✅ Audit logging service with compliance features
- ✅ Role hierarchy and inheritance logic
- ✅ 80+ business logic tests

---

## **Phase 4: Integration & Middleware (Weeks 7-8)**
*Integrate RBAC with existing LangBuilder middleware and authentication*

### **4.1 Middleware Integration**

**Authentication Middleware Enhancement:**
```python
# Integration with existing authentication middleware
@app.middleware("http")
async def rbac_middleware(request: Request, call_next):
    # Enhance existing middleware with RBAC checks
    # Maintain backward compatibility
    response = await call_next(request)
    return response
```

**Permission Checking Integration:**
```python
# Integration with existing dependency injection
async def require_permission(permission: str):
    def dependency(
        current_user: User = Depends(get_current_user),  # Existing
        session = Depends(get_session)                   # Existing
    ):
        # Permission checking logic
    return Depends(dependency)
```

### **4.2 Flow Execution Integration**

**Enhanced Flow Model (Backward Compatible):**
```python
# Add RBAC context to existing Flow execution
class FlowExecution:
    async def execute(self, user_context: RBACContext):
        # Permission checks before execution
        # Audit logging of execution
        # Maintain existing execution logic
```

### **Phase 4 Deliverables:**
- ✅ RBAC middleware integrated with existing auth
- ✅ Flow execution permission integration
- ✅ API endpoint permission enforcement
- ✅ Backward compatibility with existing APIs
- ✅ Performance optimization with caching
- ✅ 60+ integration tests

---

## **Phase 5: Advanced Features (Weeks 9-10)**
*Implement advanced RBAC features using AppGraph design guidance*

### **5.1 Multi-Environment Support**

**Environment Scoping (Following Existing Project Patterns):**
```python
# Integration with existing project/environment concepts
class Environment(SQLModel, table=True):
    project_id: UUIDstr = Field(foreign_key="project.id")
    # Follow existing deployment environment patterns
```

### **5.2 Service Account Management**

**API Token Integration (Existing Pattern):**
```python
# Enhancement of existing ApiKey model
class ServiceAccountToken(APIKey):  # Inherit from existing
    service_account_id: UUIDstr = Field(foreign_key="service_account.id")
    scoped_permissions: list[str] = Field(sa_column=Column(JSON))
```

### **Phase 5 Deliverables:**
- ✅ Multi-environment permission scoping
- ✅ Service account management with token scoping
- ✅ Break-glass emergency access
- ✅ Advanced audit logging with compliance exports
- ✅ Conditional permissions (time, IP, custom)
- ✅ 70+ advanced feature tests

---

## **Phase 6: Frontend Integration (Weeks 11-12)**
*Create admin interfaces using existing LangBuilder UI patterns*

### **6.1 React Component Integration**

**Following Existing Frontend Patterns:**
```typescript
// src/frontend/src/pages/AdminPage/RBAC/
// Follow existing page structure and component patterns
import { useApi } from '@/hooks/useApi';  // Existing hook pattern

export const WorkspaceManagement: React.FC = () => {
    // Use existing API client patterns
    // Follow existing UI component structure
    // Integrate with existing routing
};
```

### **6.2 API Client Integration**

**Frontend API Client (Existing Pattern):**
```typescript
// Integration with existing API client
export class RBACApiClient extends BaseApiClient {
    async getWorkspaces(): Promise<Workspace[]> {
        // Use existing HTTP client patterns
    }
}
```

### **Phase 6 Deliverables:**
- ✅ Admin interface for workspace/role management
- ✅ User assignment and invitation workflows
- ✅ Permission audit and compliance reporting
- ✅ Integration with existing UI components
- ✅ 50+ frontend component tests

---

## **Phase 7: Performance & Security (Weeks 13-14)**
*Optimize performance and enhance security following LangBuilder patterns*

### **7.1 Performance Optimization**

**Cache Integration (Existing Redis):**
```python
# Use existing caching infrastructure
from langflow.services.cache import get_cache

class PermissionCache:
    def __init__(self):
        self.cache = get_cache()  # Existing cache service
```

**Database Optimization (Existing Patterns):**
```python
# Follow existing database optimization patterns
# Use existing query optimization techniques
# Leverage existing indexes and performance monitoring
```

### **Phase 7 Deliverables:**
- ✅ Permission caching with <10ms cache hits
- ✅ Database query optimization
- ✅ Security hardening and vulnerability testing
- ✅ Performance benchmarks and monitoring
- ✅ Load testing with existing tools

---

## **Phase 8: Production Deployment (Weeks 15-16)**
*Deploy using existing LangBuilder deployment infrastructure*

### **8.1 Deployment Integration**

**Docker Integration (Existing Infrastructure):**
```dockerfile
# Enhancement of existing Dockerfile
# Add RBAC-specific environment variables
# Maintain existing deployment patterns
```

**Migration Strategy:**
```python
# Gradual rollout using existing deployment patterns
# Feature flags for progressive enablement
# Rollback procedures using existing infrastructure
```

### **Phase 8 Deliverables:**
- ✅ Production deployment with existing CI/CD
- ✅ Migration scripts and rollback procedures
- ✅ Monitoring and alerting integration
- ✅ Documentation and operator guides
- ✅ Production readiness review

---

## 📊 **Success Metrics & KPIs**

### **Technical Metrics:**
- **Performance**: Permission checks <100ms p95, cached checks <10ms
- **Scalability**: Support 1000+ users per workspace
- **Reliability**: 99.9% uptime, comprehensive error handling
- **Security**: Zero critical vulnerabilities, comprehensive audit trail

### **Business Metrics:**
- **User Adoption**: Admin interface usage and user satisfaction
- **Operational**: Reduced manual access management time
- **Compliance**: SOC2/ISO27001 compliance requirements met

---

## 🔧 **Development Guidelines**

### **Code Quality Standards:**
- **Type Safety**: Full TypeScript/Python type hints following existing patterns
- **Testing**: >95% test coverage using existing test infrastructure
- **Documentation**: Comprehensive inline and API documentation
- **Security**: Security review at each phase using existing security practices

### **Integration Requirements:**
- **Backward Compatibility**: All existing APIs and functionality preserved
- **Migration Path**: Gradual rollout with feature flags
- **Performance**: No degradation of existing system performance
- **Deployment**: Use existing CI/CD and deployment infrastructure

### **Architecture Compliance:**
- **Follow LangBuilder Patterns**: Use existing service, model, and API patterns
- **Minimal Dependencies**: Reuse existing libraries and infrastructure
- **Native Integration**: Deep integration with existing authentication and authorization
- **AppGraph Guidance**: Use GraphQL schemas for design validation only

---

## 🎯 **Phase Completion Criteria**

Each phase includes:
- ✅ **Functional Requirements**: All features implemented and tested
- ✅ **Integration Tests**: End-to-end scenarios validated
- ✅ **Performance Benchmarks**: Latency and throughput targets met
- ✅ **Security Review**: Vulnerability assessment completed
- ✅ **Documentation**: Technical and user documentation updated
- ✅ **Backward Compatibility**: Existing functionality preserved

**Overall Success**: Complete RBAC implementation natively integrated with LangBuilder, maintaining all existing functionality while adding enterprise-grade access control capabilities.