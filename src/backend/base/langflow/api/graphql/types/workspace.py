"""GraphQL types for Workspace entities."""

import graphene
from graphene import ObjectType, String, Boolean, List, Field, Int, InputObjectType
from typing import TYPE_CHECKING

from .common import (
    UUID, DateTime, BaseResponse, PaginationInput, SortInput, ValidationError
)

if TYPE_CHECKING:
    from .user import UserType
    from .project import ProjectType
    from .role import RoleType


class WorkspaceSettingsType(graphene.ObjectType):
    """Workspace settings configuration."""
    
    sso_enabled = Boolean(description="Whether SSO is enabled for this workspace")
    auto_assign_role = String(description="Default role for new users")
    max_projects = Int(description="Maximum number of projects allowed")
    max_users = Int(description="Maximum number of users allowed")
    require_approval = Boolean(description="Whether new user requests require approval")
    data_retention_days = Int(description="Data retention period in days")
    allow_external_sharing = Boolean(description="Whether external sharing is allowed")
    enforce_mfa = Boolean(description="Whether MFA is required")


class WorkspaceType(ObjectType):
    """Workspace GraphQL type."""
    
    id = UUID(required=True, description="Unique workspace identifier")
    name = String(required=True, description="Workspace name")
    description = String(description="Workspace description")
    organization = String(description="Organization name")
    
    # Status and metadata
    is_active = Boolean(required=True, description="Whether workspace is active")
    is_deleted = Boolean(required=True, description="Whether workspace is soft-deleted")
    deletion_requested_at = DateTime(description="When deletion was requested")
    
    # Configuration
    settings = Field(WorkspaceSettingsType, description="Workspace settings")
    metadata = graphene.JSONString(description="Additional metadata")
    tags = List(String, description="Workspace tags")
    
    # Relationships
    owner_id = UUID(required=True, description="Workspace owner user ID")
    owner = Field("langflow.api.graphql.types.user.UserType", description="Workspace owner")
    
    # Collections
    projects = List("langflow.api.graphql.types.project.ProjectType", description="Projects in workspace")
    users = List("langflow.api.graphql.types.user.UserType", description="Users in workspace")
    roles = List("langflow.api.graphql.types.role.RoleType", description="Custom roles in workspace")
    invitations = List("WorkspaceInvitationType", description="Pending invitations")
    
    # Computed fields
    total_projects = Int(description="Total number of projects")
    total_users = Int(description="Total number of users")
    total_flows = Int(description="Total number of flows")
    
    # Timestamps
    created_at = DateTime(required=True, description="When workspace was created")
    updated_at = DateTime(required=True, description="When workspace was last updated")
    
    def resolve_total_projects(self, info):
        """Resolve total number of projects."""
        return len(self.projects) if self.projects else 0
    
    def resolve_total_users(self, info):
        """Resolve total number of users."""
        return len(self.users) if self.users else 0
    
    def resolve_total_flows(self, info):
        """Resolve total number of flows across all projects."""
        if not self.projects:
            return 0
        return sum(len(project.flows) for project in self.projects if project.flows)


class WorkspaceInvitationType(ObjectType):
    """Workspace invitation GraphQL type."""
    
    id = UUID(required=True, description="Invitation ID")
    workspace_id = UUID(required=True, description="Workspace ID")
    email = String(required=True, description="Invited user email")
    role_id = UUID(description="Role to assign to invited user")
    
    # Status
    status = String(required=True, description="Invitation status")
    expires_at = DateTime(description="When invitation expires")
    accepted_at = DateTime(description="When invitation was accepted")
    
    # Metadata
    invited_by_id = UUID(required=True, description="ID of user who sent invitation")
    invited_by = Field("langflow.api.graphql.types.user.UserType", description="User who sent invitation")
    message = String(description="Optional invitation message")
    
    # Timestamps
    created_at = DateTime(required=True, description="When invitation was created")
    updated_at = DateTime(required=True, description="When invitation was last updated")


# Input Types

class WorkspaceCreateInput(InputObjectType):
    """Input for creating a workspace."""
    
    name = String(required=True, description="Workspace name")
    description = String(description="Workspace description")
    organization = String(description="Organization name")
    settings = graphene.JSONString(description="Workspace settings")
    metadata = graphene.JSONString(description="Additional metadata")
    tags = List(String, description="Workspace tags")


class WorkspaceUpdateInput(InputObjectType):
    """Input for updating a workspace."""
    
    name = String(description="Workspace name")
    description = String(description="Workspace description")
    organization = String(description="Organization name")
    settings = graphene.JSONString(description="Workspace settings")
    metadata = graphene.JSONString(description="Additional metadata")
    tags = List(String, description="Workspace tags")
    is_active = Boolean(description="Whether workspace is active")


class WorkspaceFilterInput(InputObjectType):
    """Input for filtering workspaces."""
    
    search = String(description="Search by name or description")
    organization = String(description="Filter by organization")
    is_active = Boolean(description="Filter by active status")
    owner_id = UUID(description="Filter by owner")
    tags = List(String, description="Filter by tags")
    created_after = DateTime(description="Filter by creation date")
    created_before = DateTime(description="Filter by creation date")


class WorkspaceInviteInput(InputObjectType):
    """Input for inviting users to workspace."""
    
    email = String(required=True, description="Email of user to invite")
    role_id = UUID(description="Role to assign to invited user")
    message = String(description="Optional invitation message")
    expires_in_hours = Int(default_value=168, description="Invitation expiry in hours (default: 7 days)")


# Response Types

class WorkspaceResponse(BaseResponse):
    """Response for workspace operations."""
    
    workspace = Field(WorkspaceType, description="The workspace data")
    validation_errors = List(ValidationError, description="Field validation errors")


class WorkspaceListResponse(ObjectType):
    """Response for workspace list queries."""
    
    workspaces = List(WorkspaceType, required=True, description="List of workspaces")
    total_count = Int(required=True, description="Total number of workspaces matching filter")
    has_next_page = Boolean(required=True, description="Whether there are more workspaces")


class WorkspaceInvitationResponse(BaseResponse):
    """Response for workspace invitation operations."""
    
    invitation = Field(WorkspaceInvitationType, description="The invitation data")
    validation_errors = List(ValidationError, description="Field validation errors")


class WorkspaceStatsType(ObjectType):
    """Workspace statistics."""
    
    total_projects = Int(required=True, description="Total number of projects")
    total_users = Int(required=True, description="Total number of users")
    total_flows = Int(required=True, description="Total number of flows")
    total_executions = Int(required=True, description="Total number of flow executions")
    active_users_30d = Int(required=True, description="Active users in last 30 days")
    storage_used_mb = Int(required=True, description="Storage used in MB")
    api_calls_30d = Int(required=True, description="API calls in last 30 days")


class WorkspaceStatsResponse(ObjectType):
    """Response for workspace statistics."""
    
    stats = Field(WorkspaceStatsType, required=True, description="Workspace statistics")
    period_start = DateTime(required=True, description="Statistics period start")
    period_end = DateTime(required=True, description="Statistics period end")