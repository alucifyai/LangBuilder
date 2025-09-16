"""Common GraphQL types and scalars for RBAC system."""

import graphene
from graphene import DateTime as GrapheneDateTime, String, Boolean, ObjectType, InputObjectType, List
from typing import Any
import uuid
from datetime import datetime


class UUID(graphene.Scalar):
    """UUID scalar type."""
    
    @staticmethod
    def serialize(uuid_value: Any) -> str:
        """Serialize UUID to string."""
        if isinstance(uuid_value, uuid.UUID):
            return str(uuid_value)
        if isinstance(uuid_value, str):
            return uuid_value
        raise ValueError(f"Cannot serialize {type(uuid_value)} as UUID")
    
    @staticmethod
    def parse_literal(node: Any) -> uuid.UUID:
        """Parse UUID from AST literal."""
        if hasattr(node, 'value'):
            return uuid.UUID(node.value)
        raise ValueError("Invalid UUID literal")
    
    @staticmethod
    def parse_value(value: str) -> uuid.UUID:
        """Parse UUID from input value."""
        try:
            return uuid.UUID(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid UUID: {value}") from e


class DateTime(GrapheneDateTime):
    """Enhanced DateTime scalar with timezone support."""
    
    @staticmethod
    def serialize(dt: Any) -> str:
        """Serialize datetime to ISO format."""
        if isinstance(dt, datetime):
            return dt.isoformat()
        return str(dt)


class ScopeTypeEnum(graphene.Enum):
    """Hierarchical scope types for permission assignments."""
    
    WORKSPACE = "workspace"
    PROJECT = "project"
    ENVIRONMENT = "environment"
    FLOW = "flow"
    COMPONENT = "component"


class AssignmentTypeEnum(graphene.Enum):
    """Types of entities that can be assigned roles."""
    
    USER = "user"
    GROUP = "group"
    SERVICE_ACCOUNT = "service_account"


class RoleTypeEnum(graphene.Enum):
    """Role classification types."""
    
    SYSTEM = "system"
    CUSTOM = "custom"


class PermissionActionEnum(graphene.Enum):
    """Available permission actions."""
    
    # Basic CRUD operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    
    # Extended operations (from PRD)
    EXECUTE = "execute"
    DEPLOY = "deploy"
    EXPORT = "export"
    IMPORT = "import"
    SHARE = "share"
    PUBLISH = "publish"
    MANAGE = "manage"
    GRANT = "grant"
    REVOKE = "revoke"
    IMPERSONATE = "impersonate"
    BREAK_GLASS = "break_glass"


class ResourceTypeEnum(graphene.Enum):
    """Resource types for permissions."""
    
    WORKSPACE = "workspace"
    PROJECT = "project"
    ENVIRONMENT = "environment"
    FLOW = "flow"
    COMPONENT = "component"
    USER = "user"
    ROLE = "role"
    SERVICE_ACCOUNT = "service_account"
    AUDIT = "audit"
    SYSTEM = "system"


class AuditEventTypeEnum(graphene.Enum):
    """Audit event types for logging."""
    
    # Authentication events
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    
    # Authorization events
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    ACCESS_DENIED = "access_denied"
    
    # Resource operations
    RESOURCE_CREATED = "resource_created"
    RESOURCE_UPDATED = "resource_updated"
    RESOURCE_DELETED = "resource_deleted"
    
    # Role operations
    ROLE_ASSIGNED = "role_assigned"
    ROLE_UNASSIGNED = "role_unassigned"
    ROLE_CREATED = "role_created"
    ROLE_UPDATED = "role_updated"
    ROLE_DELETED = "role_deleted"
    
    # Security events
    BREAK_GLASS_ACCESS = "break_glass_access"
    IMPERSONATION_START = "impersonation_start"
    IMPERSONATION_END = "impersonation_end"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # SSO events
    SSO_LOGIN = "sso_login"
    SSO_LOGOUT = "sso_logout"
    SSO_ERROR = "sso_error"


class AuditActorTypeEnum(graphene.Enum):
    """Types of actors that can perform audited actions."""
    
    USER = "user"
    SERVICE_ACCOUNT = "service_account"
    SYSTEM = "system"
    ANONYMOUS = "anonymous"


class SSOProviderTypeEnum(graphene.Enum):
    """SSO provider types."""
    
    OIDC = "oidc"
    SAML2 = "saml2"
    OAUTH2 = "oauth2"
    LDAP = "ldap"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    OKTA = "okta"
    AUTH0 = "auth0"
    CUSTOM = "custom"


class SSOStatusEnum(graphene.Enum):
    """SSO configuration status."""
    
    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPRECATED = "deprecated"


class PaginationInput(InputObjectType):
    """Input type for pagination."""
    
    skip = graphene.Int(default_value=0, description="Number of items to skip")
    limit = graphene.Int(default_value=100, description="Maximum number of items to return")


class SortOrder(graphene.Enum):
    """Sort order for queries."""
    
    ASC = "asc"
    DESC = "desc"


class SortInput(InputObjectType):
    """Input type for sorting."""
    
    field = String(required=True, description="Field to sort by")
    order = SortOrder(default_value=SortOrder.ASC, description="Sort order")


class BaseResponse(ObjectType):
    """Base response type for mutations."""
    
    success = Boolean(required=True, description="Whether the operation was successful")
    errors = List(String, description="List of error messages if operation failed")


class ValidationError(graphene.ObjectType):
    """Validation error details."""
    
    field = String(required=True, description="Field that failed validation")
    message = String(required=True, description="Error message")
    code = String(description="Error code")


class PermissionScope(ObjectType):
    """Permission scope information."""
    
    scope_type = ScopeTypeEnum(required=True, description="Type of scope")
    scope_id = UUID(description="ID of the scoped resource")
    scope_name = String(description="Name of the scoped resource")
    inherited = Boolean(required=True, description="Whether permission is inherited from parent scope")


class PermissionCheck(ObjectType):
    """Result of a permission check."""
    
    granted = Boolean(required=True, description="Whether permission is granted")
    reason = String(description="Reason for the decision")
    scope = PermissionScope(description="Scope where permission was found")
    cached = Boolean(required=True, description="Whether result was cached")