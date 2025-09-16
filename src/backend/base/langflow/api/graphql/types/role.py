"""GraphQL types for Role and Permission entities."""

import graphene
from graphene import ObjectType, String, Boolean, List, Field, Int, InputObjectType
from typing import TYPE_CHECKING

from .common import (
    UUID, DateTime, BaseResponse, PaginationInput, SortInput, ValidationError,
    RoleTypeEnum, PermissionActionEnum, ResourceTypeEnum, ScopeTypeEnum
)

if TYPE_CHECKING:
    from .user import UserType
    from .workspace import WorkspaceType


class PermissionType(ObjectType):
    """Permission GraphQL type."""
    
    id = UUID(required=True, description="Permission ID")
    name = String(required=True, description="Permission name")
    description = String(description="Permission description")
    
    # Permission classification
    resource_type = ResourceTypeEnum(required=True, description="Type of resource")
    action = PermissionActionEnum(required=True, description="Action that can be performed")
    
    # Constraints
    allows_conditions = Boolean(required=True, description="Whether permission supports conditions")
    allows_time_bounds = Boolean(required=True, description="Whether permission supports time constraints")
    allows_ip_restrictions = Boolean(required=True, description="Whether permission supports IP restrictions")
    
    # System info
    is_system = Boolean(required=True, description="Whether this is a system permission")
    created_at = DateTime(required=True, description="When permission was created")


class RolePermissionType(ObjectType):
    """Role-Permission association with constraints."""
    
    id = UUID(required=True, description="Association ID")
    role_id = UUID(required=True, description="Role ID")
    permission_id = UUID(required=True, description="Permission ID")
    
    # Permission details
    permission = Field(PermissionType, required=True, description="Permission details")
    
    # Constraints
    conditions = graphene.JSONString(description="Conditional logic for permission")
    ip_restrictions = List(String, description="IP address restrictions")
    time_restrictions = graphene.JSONString(description="Time-based restrictions")
    
    # Temporal constraints
    valid_from = DateTime(description="When permission becomes valid")
    valid_until = DateTime(description="When permission expires")
    
    # Assignment metadata
    reason = String(description="Reason for granting permission")
    granted_by_id = UUID(required=True, description="ID of user who granted permission")
    granted_by = Field("langflow.api.graphql.types.user.UserType", description="User who granted permission")
    granted_at = DateTime(required=True, description="When permission was granted")


class RoleType(ObjectType):
    """Role GraphQL type."""
    
    id = UUID(required=True, description="Role ID")
    name = String(required=True, description="Role name")
    description = String(description="Role description")
    
    # Role classification
    type = RoleTypeEnum(required=True, description="Role type (system or custom)")
    priority = Int(required=True, description="Role priority for conflict resolution")
    is_system = Boolean(required=True, description="Whether this is a system role")
    
    # Hierarchy
    parent_role_id = UUID(description="Parent role ID for inheritance")
    parent_role = Field("RoleType", description="Parent role")
    child_roles = List("RoleType", description="Child roles")
    
    # Workspace association
    workspace_id = UUID(description="Workspace ID (null for system roles)")
    workspace = Field("langflow.api.graphql.types.workspace.WorkspaceType", description="Associated workspace")
    
    # Version control
    version = Int(required=True, description="Role definition version")
    is_active = Boolean(required=True, description="Whether role is active")
    
    # Permissions
    permissions = List(RolePermissionType, description="Permissions granted to role")
    
    # Computed fields
    total_assignments = Int(description="Total number of assignments")
    effective_permissions = List(String, description="All effective permissions including inherited")
    total_users = Int(description="Number of users with this role")
    
    # Metadata
    metadata = graphene.JSONString(description="Additional role metadata")
    tags = List(String, description="Role tags")
    
    # Audit
    created_by_id = UUID(required=True, description="ID of user who created role")
    created_by = Field("langflow.api.graphql.types.user.UserType", description="User who created role")
    created_at = DateTime(required=True, description="When role was created")
    updated_at = DateTime(required=True, description="When role was last updated")
    
    def resolve_total_assignments(self, info):
        """Resolve total number of role assignments."""
        return len(self.assignments) if hasattr(self, 'assignments') and self.assignments else 0
    
    def resolve_effective_permissions(self, info):
        """Resolve all effective permissions including inherited ones."""
        # This would include logic to traverse parent roles and collect permissions
        permissions = []
        if self.permissions:
            permissions.extend([f"{p.permission.resource_type}:{p.permission.action}" for p in self.permissions])
        return permissions
    
    def resolve_total_users(self, info):
        """Resolve number of users with this role."""
        if not hasattr(self, 'assignments'):
            return 0
        return len([a for a in self.assignments if a.assignment_type == "user"])


# Input Types

class RoleCreateInput(InputObjectType):
    """Input for creating a role."""
    
    name = String(required=True, description="Role name")
    description = String(description="Role description")
    workspace_id = UUID(description="Workspace ID (null for system roles)")
    parent_role_id = UUID(description="Parent role ID for inheritance")
    priority = Int(description="Role priority (auto-assigned if not provided)")
    metadata = graphene.JSONString(description="Additional role metadata")
    tags = List(String, description="Role tags")


class RoleUpdateInput(InputObjectType):
    """Input for updating a role."""
    
    name = String(description="Role name")
    description = String(description="Role description")
    parent_role_id = UUID(description="Parent role ID for inheritance")
    priority = Int(description="Role priority")
    is_active = Boolean(description="Whether role is active")
    metadata = graphene.JSONString(description="Additional role metadata")
    tags = List(String, description="Role tags")


class RolePermissionAssignInput(InputObjectType):
    """Input for assigning permission to role."""
    
    permission_id = UUID(required=True, description="Permission ID")
    conditions = graphene.JSONString(description="Conditional logic for permission")
    ip_restrictions = List(String, description="IP address restrictions")
    time_restrictions = graphene.JSONString(description="Time-based restrictions")
    valid_from = DateTime(description="When permission becomes valid")
    valid_until = DateTime(description="When permission expires")
    reason = String(description="Reason for granting permission")


class RoleFilterInput(InputObjectType):
    """Input for filtering roles."""
    
    search = String(description="Search by name or description")
    type = RoleTypeEnum(description="Filter by role type")
    workspace_id = UUID(description="Filter by workspace")
    is_active = Boolean(description="Filter by active status")
    has_permissions = List(String, description="Filter by permissions")
    tags = List(String, description="Filter by tags")
    created_after = DateTime(description="Filter by creation date")
    created_before = DateTime(description="Filter by creation date")


class PermissionFilterInput(InputObjectType):
    """Input for filtering permissions."""
    
    search = String(description="Search by name or description")
    resource_type = ResourceTypeEnum(description="Filter by resource type")
    action = PermissionActionEnum(description="Filter by action")
    is_system = Boolean(description="Filter by system permissions")


# Response Types

class RoleResponse(BaseResponse):
    """Response for role operations."""
    
    role = Field(RoleType, description="The role data")
    validation_errors = List(ValidationError, description="Field validation errors")


class RoleListResponse(ObjectType):
    """Response for role list queries."""
    
    roles = List(RoleType, required=True, description="List of roles")
    total_count = Int(required=True, description="Total number of roles matching filter")
    has_next_page = Boolean(required=True, description="Whether there are more roles")


class PermissionResponse(BaseResponse):
    """Response for permission operations."""
    
    permission = Field(PermissionType, description="The permission data")
    validation_errors = List(ValidationError, description="Field validation errors")


class PermissionListResponse(ObjectType):
    """Response for permission list queries."""
    
    permissions = List(PermissionType, required=True, description="List of permissions")
    total_count = Int(required=True, description="Total number of permissions matching filter")
    has_next_page = Boolean(required=True, description="Whether there are more permissions")


class RolePermissionResponse(BaseResponse):
    """Response for role permission assignment operations."""
    
    role_permission = Field(RolePermissionType, description="The role permission assignment")
    validation_errors = List(ValidationError, description="Field validation errors")


class RoleHierarchyType(ObjectType):
    """Role hierarchy visualization."""
    
    role = Field(RoleType, required=True, description="The role")
    level = Int(required=True, description="Hierarchy level (0 = root)")
    path = List(String, required=True, description="Path from root to this role")
    children = List("RoleHierarchyType", description="Child roles")


class RoleStatsType(ObjectType):
    """Role usage statistics."""
    
    role = Field(RoleType, required=True, description="The role")
    total_assignments = Int(required=True, description="Total number of assignments")
    active_assignments = Int(required=True, description="Number of active assignments")
    user_assignments = Int(required=True, description="Number of user assignments")
    group_assignments = Int(required=True, description="Number of group assignments")
    service_account_assignments = Int(required=True, description="Number of service account assignments")
    last_assigned_at = DateTime(description="When role was last assigned")
    most_common_scope = String(description="Most common assignment scope")