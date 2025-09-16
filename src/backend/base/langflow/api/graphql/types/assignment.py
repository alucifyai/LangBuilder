"""GraphQL types for Role Assignment entities."""

import graphene
from graphene import ObjectType, String, Boolean, List, Field, Int, InputObjectType
from typing import TYPE_CHECKING

from .common import (
    UUID, DateTime, BaseResponse, PaginationInput, SortInput, ValidationError,
    ScopeTypeEnum, AssignmentTypeEnum
)

if TYPE_CHECKING:
    from .user import UserType
    from .role import RoleType
    from .workspace import WorkspaceType
    from .project import ProjectType
    from .environment import EnvironmentType


class RoleAssignmentScopeType(ObjectType):
    """Role assignment scope information."""
    
    scope_type = ScopeTypeEnum(required=True, description="Type of scope")
    
    # Hierarchical scope IDs (one will be populated based on scope_type)
    workspace_id = UUID(description="Workspace ID")
    project_id = UUID(description="Project ID")
    environment_id = UUID(description="Environment ID")
    flow_id = UUID(description="Flow ID")
    component_id = UUID(description="Component ID")
    
    # Scope names for display
    scope_name = String(description="Name of the scoped resource")
    scope_path = String(description="Full hierarchical path")
    
    # Resolved scope objects
    workspace = Field("langflow.api.graphql.types.workspace.WorkspaceType", description="Workspace object")
    project = Field("langflow.api.graphql.types.project.ProjectType", description="Project object")
    environment = Field("langflow.api.graphql.types.environment.EnvironmentType", description="Environment object")


class RoleAssignmentType(ObjectType):
    """Role assignment GraphQL type."""
    
    id = UUID(required=True, description="Assignment ID")
    
    # Assignment target
    assignment_type = AssignmentTypeEnum(required=True, description="Type of assignee")
    user_id = UUID(description="User ID (if assignment_type is USER)")
    group_id = UUID(description="Group ID (if assignment_type is GROUP)")
    service_account_id = UUID(description="Service account ID (if assignment_type is SERVICE_ACCOUNT)")
    
    # Role and scope
    role_id = UUID(required=True, description="Role ID")
    role = Field("langflow.api.graphql.types.role.RoleType", required=True, description="Assigned role")
    scope = Field(RoleAssignmentScopeType, required=True, description="Assignment scope")
    
    # Assignment status
    is_active = Boolean(required=True, description="Whether assignment is active")
    is_inherited = Boolean(required=True, description="Whether assignment is inherited from parent scope")
    
    # Temporal constraints
    valid_from = DateTime(description="When assignment becomes valid")
    valid_until = DateTime(description="When assignment expires")
    
    # Conditional constraints
    conditions = graphene.JSONString(description="Conditional logic for assignment")
    ip_restrictions = List(String, description="IP address restrictions")
    time_restrictions = graphene.JSONString(description="Time-based restrictions")
    
    # Assignment metadata
    reason = String(description="Reason for assignment")
    assigned_by_id = UUID(required=True, description="ID of user who made assignment")
    assigned_by = Field("langflow.api.graphql.types.user.UserType", description="User who made assignment")
    approved_by_id = UUID(description="ID of user who approved assignment")
    approved_by = Field("langflow.api.graphql.types.user.UserType", description="User who approved assignment")
    approval_date = DateTime(description="When assignment was approved")
    
    # Resolved assignee objects
    user = Field("langflow.api.graphql.types.user.UserType", description="Assigned user")
    group = Field("UserGroupType", description="Assigned group")
    service_account = Field("ServiceAccountType", description="Assigned service account")
    
    # Computed fields
    assignee_name = String(description="Display name of assignee")
    effective_permissions = List(String, description="Effective permissions from this assignment")
    
    # Timestamps
    assigned_at = DateTime(required=True, description="When assignment was created")
    updated_at = DateTime(required=True, description="When assignment was last updated")
    last_used_at = DateTime(description="When assignment was last used for permission check")
    
    def resolve_assignee_name(self, info):
        """Resolve display name of assignee."""
        if self.assignment_type == "user" and self.user:
            return self.user.username or self.user.email
        elif self.assignment_type == "group" and self.group:
            return self.group.name
        elif self.assignment_type == "service_account" and self.service_account:
            return self.service_account.name
        return "Unknown"
    
    def resolve_effective_permissions(self, info):
        """Resolve effective permissions from this assignment."""
        if not self.role or not self.role.permissions:
            return []
        return [f"{p.permission.resource_type}:{p.permission.action}" for p in self.role.permissions]


# Input Types

class RoleAssignmentCreateInput(InputObjectType):
    """Input for creating a role assignment."""
    
    # Assignee (exactly one must be provided)
    user_id = UUID(description="User ID to assign role to")
    group_id = UUID(description="Group ID to assign role to")
    service_account_id = UUID(description="Service account ID to assign role to")
    
    # Role and scope
    role_id = UUID(required=True, description="Role ID to assign")
    scope_type = ScopeTypeEnum(required=True, description="Type of scope")
    workspace_id = UUID(description="Workspace ID (required for workspace scope)")
    project_id = UUID(description="Project ID (required for project scope)")
    environment_id = UUID(description="Environment ID (required for environment scope)")
    flow_id = UUID(description="Flow ID (required for flow scope)")
    component_id = UUID(description="Component ID (required for component scope)")
    
    # Constraints
    valid_from = DateTime(description="When assignment becomes valid")
    valid_until = DateTime(description="When assignment expires")
    conditions = graphene.JSONString(description="Conditional logic for assignment")
    ip_restrictions = List(String, description="IP address restrictions")
    time_restrictions = graphene.JSONString(description="Time-based restrictions")
    
    # Metadata
    reason = String(description="Reason for assignment")
    requires_approval = Boolean(default_value=False, description="Whether assignment requires approval")


class RoleAssignmentUpdateInput(InputObjectType):
    """Input for updating a role assignment."""
    
    is_active = Boolean(description="Whether assignment is active")
    valid_from = DateTime(description="When assignment becomes valid")
    valid_until = DateTime(description="When assignment expires")
    conditions = graphene.JSONString(description="Conditional logic for assignment")
    ip_restrictions = List(String, description="IP address restrictions")
    time_restrictions = graphene.JSONString(description="Time-based restrictions")
    reason = String(description="Updated reason for assignment")


class RoleAssignmentFilterInput(InputObjectType):
    """Input for filtering role assignments."""
    
    assignment_type = AssignmentTypeEnum(description="Filter by assignee type")
    user_id = UUID(description="Filter by user")
    group_id = UUID(description="Filter by group")
    service_account_id = UUID(description="Filter by service account")
    role_id = UUID(description="Filter by role")
    scope_type = ScopeTypeEnum(description="Filter by scope type")
    workspace_id = UUID(description="Filter by workspace")
    project_id = UUID(description="Filter by project")
    environment_id = UUID(description="Filter by environment")
    flow_id = UUID(description="Filter by flow")
    is_active = Boolean(description="Filter by active status")
    is_inherited = Boolean(description="Filter by inherited status")
    expires_after = DateTime(description="Filter by expiration date")
    expires_before = DateTime(description="Filter by expiration date")
    assigned_after = DateTime(description="Filter by assignment date")
    assigned_before = DateTime(description="Filter by assignment date")


class BulkRoleAssignmentInput(InputObjectType):
    """Input for bulk role assignment operations."""
    
    # Multiple assignees
    user_ids = List(UUID, description="User IDs to assign role to")
    group_ids = List(UUID, description="Group IDs to assign role to")
    service_account_ids = List(UUID, description="Service account IDs to assign role to")
    
    # Role and scope
    role_id = UUID(required=True, description="Role ID to assign")
    scope_type = ScopeTypeEnum(required=True, description="Type of scope")
    workspace_id = UUID(description="Workspace ID")
    project_id = UUID(description="Project ID")
    environment_id = UUID(description="Environment ID")
    flow_id = UUID(description="Flow ID")
    component_id = UUID(description="Component ID")
    
    # Constraints
    valid_from = DateTime(description="When assignments become valid")
    valid_until = DateTime(description="When assignments expire")
    reason = String(description="Reason for assignments")


# Response Types

class RoleAssignmentResponse(BaseResponse):
    """Response for role assignment operations."""
    
    assignment = Field(RoleAssignmentType, description="The role assignment data")
    validation_errors = List(ValidationError, description="Field validation errors")


class RoleAssignmentListResponse(ObjectType):
    """Response for role assignment list queries."""
    
    assignments = List(RoleAssignmentType, required=True, description="List of role assignments")
    total_count = Int(required=True, description="Total number of assignments matching filter")
    has_next_page = Boolean(required=True, description="Whether there are more assignments")


class BulkRoleAssignmentResponse(BaseResponse):
    """Response for bulk role assignment operations."""
    
    assignments = List(RoleAssignmentType, description="Created assignments")
    successful_count = Int(required=True, description="Number of successful assignments")
    failed_count = Int(required=True, description="Number of failed assignments")
    errors = List(String, description="Error messages for failed assignments")


class RoleAssignmentStatsType(ObjectType):
    """Role assignment statistics."""
    
    total_assignments = Int(required=True, description="Total number of assignments")
    active_assignments = Int(required=True, description="Number of active assignments")
    expired_assignments = Int(required=True, description="Number of expired assignments")
    pending_approval = Int(required=True, description="Number of assignments pending approval")
    
    # By type
    user_assignments = Int(required=True, description="Number of user assignments")
    group_assignments = Int(required=True, description="Number of group assignments")
    service_account_assignments = Int(required=True, description="Number of service account assignments")
    
    # By scope
    workspace_assignments = Int(required=True, description="Number of workspace-scoped assignments")
    project_assignments = Int(required=True, description="Number of project-scoped assignments")
    environment_assignments = Int(required=True, description="Number of environment-scoped assignments")
    flow_assignments = Int(required=True, description="Number of flow-scoped assignments")
    component_assignments = Int(required=True, description="Number of component-scoped assignments")


class AssignmentApprovalType(ObjectType):
    """Assignment approval workflow."""
    
    id = UUID(required=True, description="Approval ID")
    assignment_id = UUID(required=True, description="Assignment ID")
    assignment = Field(RoleAssignmentType, required=True, description="Assignment being approved")
    
    status = String(required=True, description="Approval status")
    requested_by_id = UUID(required=True, description="ID of user who requested approval")
    requested_by = Field("langflow.api.graphql.types.user.UserType", description="User who requested approval")
    
    # Approval decision
    approved_by_id = UUID(description="ID of user who approved/denied")
    approved_by = Field("langflow.api.graphql.types.user.UserType", description="User who approved/denied")
    decision_reason = String(description="Reason for approval decision")
    
    # Timestamps
    requested_at = DateTime(required=True, description="When approval was requested")
    decided_at = DateTime(description="When decision was made")
    expires_at = DateTime(description="When approval request expires")