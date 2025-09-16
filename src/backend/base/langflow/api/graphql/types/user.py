"""GraphQL types for User entities enhanced with RBAC."""

import graphene
from graphene import ObjectType, String, Boolean, List, Field, Int, InputObjectType
from typing import TYPE_CHECKING

from .common import (
    UUID, DateTime, BaseResponse, PaginationInput, SortInput, ValidationError
)

if TYPE_CHECKING:
    from .workspace import WorkspaceType
    from .role import RoleType
    from .assignment import RoleAssignmentType


class UserGroupType(ObjectType):
    """User group GraphQL type."""
    
    id = UUID(required=True, description="Group ID")
    name = String(required=True, description="Group name")
    description = String(description="Group description")
    
    # Group properties
    is_system = Boolean(required=True, description="Whether this is a system group")
    is_active = Boolean(required=True, description="Whether group is active")
    
    # SCIM integration
    scim_enabled = Boolean(required=True, description="Whether SCIM sync is enabled")
    scim_external_id = String(description="External SCIM group ID")
    last_scim_sync = DateTime(description="Last SCIM synchronization")
    
    # Workspace association
    workspace_id = UUID(description="Workspace ID (null for global groups)")
    workspace = Field("langflow.api.graphql.types.workspace.WorkspaceType", description="Associated workspace")
    
    # Members
    members = List("UserGroupMembershipType", description="Group members")
    
    # Computed fields
    total_members = Int(description="Total number of members")
    active_members = Int(description="Number of active members")
    
    # Metadata
    metadata = graphene.JSONString(description="Additional group metadata")
    tags = List(String, description="Group tags")
    
    # Audit
    created_by_id = UUID(required=True, description="ID of user who created group")
    created_by = Field("UserType", description="User who created group")
    created_at = DateTime(required=True, description="When group was created")
    updated_at = DateTime(required=True, description="When group was last updated")
    
    def resolve_total_members(self, info):
        """Resolve total number of members."""
        return len(self.members) if self.members else 0
    
    def resolve_active_members(self, info):
        """Resolve number of active members."""
        if not self.members:
            return 0
        return len([m for m in self.members if m.is_active])


class UserGroupMembershipType(ObjectType):
    """User group membership GraphQL type."""
    
    id = UUID(required=True, description="Membership ID")
    user_id = UUID(required=True, description="User ID")
    group_id = UUID(required=True, description="Group ID")
    
    # Membership details
    user = Field("UserType", required=True, description="Member user")
    group = Field(UserGroupType, required=True, description="Group")
    
    # Status
    is_active = Boolean(required=True, description="Whether membership is active")
    role_in_group = String(description="Member role within group")
    
    # SCIM integration
    scim_external_id = String(description="External SCIM membership ID")
    synced_from_scim = Boolean(required=True, description="Whether membership was synced from SCIM")
    
    # Audit
    added_by_id = UUID(required=True, description="ID of user who added member")
    added_by = Field("UserType", description="User who added member")
    added_at = DateTime(required=True, description="When member was added")
    updated_at = DateTime(required=True, description="When membership was last updated")


class UserType(ObjectType):
    """Enhanced User GraphQL type with RBAC relationships."""
    
    id = UUID(required=True, description="User ID")
    username = String(required=True, description="Username")
    email = String(description="Email address")
    
    # Profile
    first_name = String(description="First name")
    last_name = String(description="Last name")
    display_name = String(description="Display name")
    profile_image = String(description="Profile image URL")
    
    # Status
    is_active = Boolean(required=True, description="Whether user is active")
    is_superuser = Boolean(required=True, description="Whether user is a superuser")
    is_verified = Boolean(required=True, description="Whether user email is verified")
    
    # Authentication
    last_login_at = DateTime(description="Last login timestamp")
    password_changed_at = DateTime(description="When password was last changed")
    mfa_enabled = Boolean(required=True, description="Whether MFA is enabled")
    failed_login_attempts = Int(required=True, description="Number of failed login attempts")
    locked_until = DateTime(description="Account lock expiry")
    
    # Preferences
    timezone = String(description="User timezone")
    language = String(description="Preferred language")
    preferences = graphene.JSONString(description="User preferences")
    
    # RBAC Relationships
    owned_workspaces = List("langflow.api.graphql.types.workspace.WorkspaceType", description="Workspaces owned by user")
    workspace_memberships = List("WorkspaceMembershipType", description="Workspace memberships")
    role_assignments = List("langflow.api.graphql.types.assignment.RoleAssignmentType", description="Role assignments")
    group_memberships = List(UserGroupMembershipType, description="Group memberships")
    
    # Computed RBAC fields
    total_workspaces = Int(description="Number of workspaces user has access to")
    total_roles = Int(description="Number of roles assigned to user")
    effective_permissions = List(String, description="All effective permissions")
    highest_role_priority = Int(description="Priority of highest-priority role")
    
    # Activity
    last_activity_at = DateTime(description="Last activity timestamp")
    session_count = Int(description="Number of active sessions")
    
    # Integration
    sso_provider = String(description="SSO provider if user authenticated via SSO")
    sso_external_id = String(description="External SSO user ID")
    scim_external_id = String(description="External SCIM user ID")
    
    # Metadata
    metadata = graphene.JSONString(description="Additional user metadata")
    tags = List(String, description="User tags")
    
    # Timestamps
    created_at = DateTime(required=True, description="When user was created")
    updated_at = DateTime(required=True, description="When user was last updated")
    
    def resolve_display_name(self, info):
        """Resolve display name with fallback logic."""
        if self.display_name:
            return self.display_name
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        return self.username or self.email
    
    def resolve_total_workspaces(self, info):
        """Resolve total number of workspaces."""
        owned = len(self.owned_workspaces) if self.owned_workspaces else 0
        member = len(self.workspace_memberships) if self.workspace_memberships else 0
        return owned + member
    
    def resolve_total_roles(self, info):
        """Resolve total number of roles."""
        return len(self.role_assignments) if self.role_assignments else 0


class WorkspaceMembershipType(ObjectType):
    """Workspace membership details."""
    
    id = UUID(required=True, description="Membership ID")
    user_id = UUID(required=True, description="User ID")
    workspace_id = UUID(required=True, description="Workspace ID")
    
    # Membership details
    user = Field(UserType, required=True, description="Member user")
    workspace = Field("langflow.api.graphql.types.workspace.WorkspaceType", required=True, description="Workspace")
    
    # Status
    is_active = Boolean(required=True, description="Whether membership is active")
    role = String(description="Default role in workspace")
    
    # Audit
    joined_at = DateTime(required=True, description="When user joined workspace")
    invited_by_id = UUID(description="ID of user who invited member")
    invited_by = Field(UserType, description="User who invited member")
    last_activity_at = DateTime(description="Last activity in workspace")


# Input Types

class UserCreateInput(InputObjectType):
    """Input for creating a user."""
    
    username = String(required=True, description="Username")
    email = String(required=True, description="Email address")
    password = String(required=True, description="Password")
    first_name = String(description="First name")
    last_name = String(description="Last name")
    display_name = String(description="Display name")
    is_active = Boolean(default_value=True, description="Whether user is active")
    timezone = String(description="User timezone")
    language = String(description="Preferred language")
    metadata = graphene.JSONString(description="Additional user metadata")
    tags = List(String, description="User tags")


class UserUpdateInput(InputObjectType):
    """Input for updating a user."""
    
    username = String(description="Username")
    email = String(description="Email address")
    first_name = String(description="First name")
    last_name = String(description="Last name")
    display_name = String(description="Display name")
    profile_image = String(description="Profile image URL")
    is_active = Boolean(description="Whether user is active")
    timezone = String(description="User timezone")
    language = String(description="Preferred language")
    preferences = graphene.JSONString(description="User preferences")
    metadata = graphene.JSONString(description="Additional user metadata")
    tags = List(String, description="User tags")


class UserFilterInput(InputObjectType):
    """Input for filtering users."""
    
    search = String(description="Search by username, email, or name")
    email = String(description="Filter by email")
    is_active = Boolean(description="Filter by active status")
    is_superuser = Boolean(description="Filter by superuser status")
    is_verified = Boolean(description="Filter by verification status")
    workspace_id = UUID(description="Filter by workspace membership")
    role_id = UUID(description="Filter by role assignment")
    group_id = UUID(description="Filter by group membership")
    sso_provider = String(description="Filter by SSO provider")
    tags = List(String, description="Filter by tags")
    created_after = DateTime(description="Filter by creation date")
    created_before = DateTime(description="Filter by creation date")
    last_login_after = DateTime(description="Filter by last login")
    last_login_before = DateTime(description="Filter by last login")


class UserGroupCreateInput(InputObjectType):
    """Input for creating a user group."""
    
    name = String(required=True, description="Group name")
    description = String(description="Group description")
    workspace_id = UUID(description="Workspace ID (null for global group)")
    scim_enabled = Boolean(default_value=False, description="Whether SCIM sync is enabled")
    metadata = graphene.JSONString(description="Additional group metadata")
    tags = List(String, description="Group tags")


class UserGroupUpdateInput(InputObjectType):
    """Input for updating a user group."""
    
    name = String(description="Group name")
    description = String(description="Group description")
    is_active = Boolean(description="Whether group is active")
    scim_enabled = Boolean(description="Whether SCIM sync is enabled")
    metadata = graphene.JSONString(description="Additional group metadata")
    tags = List(String, description="Group tags")


class UserGroupMembershipInput(InputObjectType):
    """Input for managing group membership."""
    
    user_id = UUID(required=True, description="User ID")
    role_in_group = String(description="Member role within group")


# Response Types

class UserResponse(BaseResponse):
    """Response for user operations."""
    
    user = Field(UserType, description="The user data")
    validation_errors = List(ValidationError, description="Field validation errors")


class UserListResponse(ObjectType):
    """Response for user list queries."""
    
    users = List(UserType, required=True, description="List of users")
    total_count = Int(required=True, description="Total number of users matching filter")
    has_next_page = Boolean(required=True, description="Whether there are more users")


class UserGroupResponse(BaseResponse):
    """Response for user group operations."""
    
    group = Field(UserGroupType, description="The user group data")
    validation_errors = List(ValidationError, description="Field validation errors")


class UserGroupListResponse(ObjectType):
    """Response for user group list queries."""
    
    groups = List(UserGroupType, required=True, description="List of user groups")
    total_count = Int(required=True, description="Total number of groups matching filter")
    has_next_page = Boolean(required=True, description="Whether there are more groups")


class UserStatsType(ObjectType):
    """User statistics."""
    
    total_users = Int(required=True, description="Total number of users")
    active_users = Int(required=True, description="Number of active users")
    verified_users = Int(required=True, description="Number of verified users")
    superusers = Int(required=True, description="Number of superusers")
    
    # Activity stats
    active_last_day = Int(required=True, description="Users active in last day")
    active_last_week = Int(required=True, description="Users active in last week")
    active_last_month = Int(required=True, description="Users active in last month")
    
    # Authentication stats
    mfa_enabled_users = Int(required=True, description="Users with MFA enabled")
    sso_users = Int(required=True, description="Users authenticated via SSO")
    locked_users = Int(required=True, description="Currently locked users")
    
    # Growth stats
    new_users_last_month = Int(required=True, description="New users in last month")
    user_growth_rate = String(description="User growth rate percentage")


class UserActivityType(ObjectType):
    """User activity information."""
    
    user = Field(UserType, required=True, description="User")
    last_login_at = DateTime(description="Last login timestamp")
    last_activity_at = DateTime(description="Last activity timestamp")
    session_count = Int(required=True, description="Number of active sessions")
    login_count_30d = Int(required=True, description="Login count in last 30 days")
    
    # Recent activity
    recent_actions = List(String, description="Recent actions performed")
    active_workspaces = List(String, description="Recently active workspaces")
    
    # Device info
    last_device = String(description="Last used device")
    last_ip_address = String(description="Last IP address")
    last_location = String(description="Last known location")