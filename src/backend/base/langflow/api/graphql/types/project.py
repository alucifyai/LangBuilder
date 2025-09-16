"""GraphQL types for Project entities."""

import graphene
from graphene import ObjectType, String, Boolean, List, Field, Int, InputObjectType
from typing import TYPE_CHECKING

from .common import (
    UUID, DateTime, BaseResponse, PaginationInput, SortInput, ValidationError
)

if TYPE_CHECKING:
    from .workspace import WorkspaceType
    from .user import UserType
    from .environment import EnvironmentType


class ProjectType(ObjectType):
    """Project GraphQL type."""
    
    id = UUID(required=True, description="Project ID")
    name = String(required=True, description="Project name")
    description = String(description="Project description")
    
    # Hierarchy
    workspace_id = UUID(required=True, description="Parent workspace ID")
    workspace = Field("langflow.api.graphql.types.workspace.WorkspaceType", required=True, description="Parent workspace")
    
    # Ownership
    owner_id = UUID(required=True, description="Project owner user ID")
    owner = Field("langflow.api.graphql.types.user.UserType", required=True, description="Project owner")
    
    # Project settings
    is_active = Boolean(required=True, description="Whether project is active")
    is_public = Boolean(required=True, description="Whether project is publicly visible")
    auto_deploy_enabled = Boolean(required=True, description="Whether auto-deployment is enabled")
    
    # Repository integration
    repository_url = String(description="Git repository URL")
    repository_branch = String(description="Default repository branch")
    repository_path = String(description="Path within repository")
    repository_credentials_id = UUID(description="Credentials for repository access")
    
    # Deployment configuration
    default_environment_id = UUID(description="Default environment for deployments")
    deployment_config = graphene.JSONString(description="Deployment configuration")
    resource_limits = graphene.JSONString(description="Resource limits configuration")
    
    # Collections
    environments = List("langflow.api.graphql.types.environment.EnvironmentType", description="Project environments")
    flows = List("FlowType", description="Flows in project")
    
    # Computed fields
    total_environments = Int(description="Number of environments")
    total_flows = Int(description="Number of flows")
    total_deployments = Int(description="Number of deployments")
    last_deployment_at = DateTime(description="Last deployment timestamp")
    
    # Collaboration
    contributors = List("ProjectContributorType", description="Project contributors")
    
    # Metadata
    metadata = graphene.JSONString(description="Additional project metadata")
    tags = List(String, description="Project tags")
    
    # Timestamps
    created_at = DateTime(required=True, description="When project was created")
    updated_at = DateTime(required=True, description="When project was last updated")
    last_activity_at = DateTime(description="Last activity in project")
    
    def resolve_total_environments(self, info):
        """Resolve total number of environments."""
        return len(self.environments) if self.environments else 0
    
    def resolve_total_flows(self, info):
        """Resolve total number of flows."""
        return len(self.flows) if self.flows else 0


class ProjectContributorType(ObjectType):
    """Project contributor information."""
    
    id = UUID(required=True, description="Contributor ID")
    project_id = UUID(required=True, description="Project ID")
    user_id = UUID(required=True, description="User ID")
    
    # Contributor details
    project = Field(ProjectType, required=True, description="Project")
    user = Field("langflow.api.graphql.types.user.UserType", required=True, description="Contributor user")
    
    # Permissions
    role = String(required=True, description="Contributor role")
    permissions = List(String, description="Specific permissions")
    
    # Status
    is_active = Boolean(required=True, description="Whether contributor is active")
    
    # Activity
    last_contribution_at = DateTime(description="Last contribution timestamp")
    contribution_count = Int(required=True, description="Number of contributions")
    
    # Audit
    added_by_id = UUID(required=True, description="ID of user who added contributor")
    added_by = Field("langflow.api.graphql.types.user.UserType", description="User who added contributor")
    added_at = DateTime(required=True, description="When contributor was added")


class ProjectTemplateType(ObjectType):
    """Project template for quick setup."""
    
    id = UUID(required=True, description="Template ID")
    name = String(required=True, description="Template name")
    description = String(description="Template description")
    category = String(required=True, description="Template category")
    
    # Template content
    project_config = graphene.JSONString(required=True, description="Project configuration template")
    environment_configs = graphene.JSONString(description="Environment configurations")
    default_flows = graphene.JSONString(description="Default flows to create")
    
    # Template metadata
    is_public = Boolean(required=True, description="Whether template is publicly available")
    is_official = Boolean(required=True, description="Whether template is officially supported")
    version = String(required=True, description="Template version")
    
    # Usage stats
    usage_count = Int(required=True, description="Number of times template was used")
    rating = String(description="Average rating")
    
    # Author
    created_by_id = UUID(required=True, description="Template author ID")
    created_by = Field("langflow.api.graphql.types.user.UserType", description="Template author")
    
    # Timestamps
    created_at = DateTime(required=True, description="When template was created")
    updated_at = DateTime(required=True, description="When template was last updated")


# Input Types

class ProjectCreateInput(InputObjectType):
    """Input for creating a project."""
    
    name = String(required=True, description="Project name")
    description = String(description="Project description")
    workspace_id = UUID(required=True, description="Parent workspace ID")
    
    # Settings
    is_public = Boolean(default_value=False, description="Whether project is publicly visible")
    auto_deploy_enabled = Boolean(default_value=False, description="Whether auto-deployment is enabled")
    
    # Repository
    repository_url = String(description="Git repository URL")
    repository_branch = String(description="Default repository branch")
    repository_path = String(description="Path within repository")
    repository_credentials_id = UUID(description="Credentials for repository access")
    
    # Configuration
    deployment_config = graphene.JSONString(description="Deployment configuration")
    resource_limits = graphene.JSONString(description="Resource limits configuration")
    
    # Metadata
    metadata = graphene.JSONString(description="Additional project metadata")
    tags = List(String, description="Project tags")
    
    # Template
    template_id = UUID(description="Template to use for project setup")


class ProjectUpdateInput(InputObjectType):
    """Input for updating a project."""
    
    name = String(description="Project name")
    description = String(description="Project description")
    is_active = Boolean(description="Whether project is active")
    is_public = Boolean(description="Whether project is publicly visible")
    auto_deploy_enabled = Boolean(description="Whether auto-deployment is enabled")
    
    # Repository
    repository_url = String(description="Git repository URL")
    repository_branch = String(description="Default repository branch")
    repository_path = String(description="Path within repository")
    repository_credentials_id = UUID(description="Credentials for repository access")
    
    # Configuration
    default_environment_id = UUID(description="Default environment for deployments")
    deployment_config = graphene.JSONString(description="Deployment configuration")
    resource_limits = graphene.JSONString(description="Resource limits configuration")
    
    # Metadata
    metadata = graphene.JSONString(description="Additional project metadata")
    tags = List(String, description="Project tags")


class ProjectFilterInput(InputObjectType):
    """Input for filtering projects."""
    
    search = String(description="Search by name or description")
    workspace_id = UUID(description="Filter by workspace")
    owner_id = UUID(description="Filter by owner")
    is_active = Boolean(description="Filter by active status")
    is_public = Boolean(description="Filter by public visibility")
    auto_deploy_enabled = Boolean(description="Filter by auto-deploy setting")
    has_repository = Boolean(description="Filter by repository presence")
    tags = List(String, description="Filter by tags")
    created_after = DateTime(description="Filter by creation date")
    created_before = DateTime(description="Filter by creation date")
    last_activity_after = DateTime(description="Filter by last activity")
    last_activity_before = DateTime(description="Filter by last activity")


class ProjectContributorAddInput(InputObjectType):
    """Input for adding project contributor."""
    
    user_id = UUID(required=True, description="User ID to add as contributor")
    role = String(required=True, description="Contributor role")
    permissions = List(String, description="Specific permissions to grant")


class ProjectContributorUpdateInput(InputObjectType):
    """Input for updating project contributor."""
    
    role = String(description="Contributor role")
    permissions = List(String, description="Specific permissions to grant")
    is_active = Boolean(description="Whether contributor is active")


# Response Types

class ProjectResponse(BaseResponse):
    """Response for project operations."""
    
    project = Field(ProjectType, description="The project data")
    validation_errors = List(ValidationError, description="Field validation errors")


class ProjectListResponse(ObjectType):
    """Response for project list queries."""
    
    projects = List(ProjectType, required=True, description="List of projects")
    total_count = Int(required=True, description="Total number of projects matching filter")
    has_next_page = Boolean(required=True, description="Whether there are more projects")


class ProjectContributorResponse(BaseResponse):
    """Response for project contributor operations."""
    
    contributor = Field(ProjectContributorType, description="The contributor data")
    validation_errors = List(ValidationError, description="Field validation errors")


class ProjectTemplateListResponse(ObjectType):
    """Response for project template list queries."""
    
    templates = List(ProjectTemplateType, required=True, description="List of project templates")
    total_count = Int(required=True, description="Total number of templates")
    categories = List(String, required=True, description="Available template categories")


class ProjectStatsType(ObjectType):
    """Project statistics."""
    
    project = Field(ProjectType, required=True, description="Project")
    
    # Counts
    total_environments = Int(required=True, description="Number of environments")
    total_flows = Int(required=True, description="Number of flows")
    total_deployments = Int(required=True, description="Number of deployments")
    total_contributors = Int(required=True, description="Number of contributors")
    
    # Activity
    executions_last_30d = Int(required=True, description="Flow executions in last 30 days")
    deployments_last_30d = Int(required=True, description="Deployments in last 30 days")
    commits_last_30d = Int(required=True, description="Repository commits in last 30 days")
    active_contributors_30d = Int(required=True, description="Active contributors in last 30 days")
    
    # Resource usage
    storage_used_mb = Int(required=True, description="Storage used in MB")
    compute_hours_30d = Int(required=True, description="Compute hours used in last 30 days")
    api_calls_30d = Int(required=True, description="API calls in last 30 days")
    
    # Health
    success_rate_30d = String(description="Success rate in last 30 days")
    avg_execution_time_ms = Int(description="Average execution time in milliseconds")
    error_rate_30d = String(description="Error rate in last 30 days")


class ProjectDeploymentType(ObjectType):
    """Project deployment information."""
    
    id = UUID(required=True, description="Deployment ID")
    project_id = UUID(required=True, description="Project ID")
    environment_id = UUID(required=True, description="Environment ID")
    
    # Deployment details
    project = Field(ProjectType, required=True, description="Project")
    environment = Field("langflow.api.graphql.types.environment.EnvironmentType", required=True, description="Environment")
    
    # Deployment info
    version = String(required=True, description="Deployment version")
    commit_hash = String(description="Git commit hash")
    status = String(required=True, description="Deployment status")
    
    # Configuration
    config = graphene.JSONString(description="Deployment configuration")
    resource_allocation = graphene.JSONString(description="Resource allocation")
    
    # Metrics
    health_status = String(description="Health check status")
    uptime_percentage = String(description="Uptime percentage")
    last_health_check = DateTime(description="Last health check timestamp")
    
    # Audit
    deployed_by_id = UUID(required=True, description="ID of user who deployed")
    deployed_by = Field("langflow.api.graphql.types.user.UserType", description="User who deployed")
    deployed_at = DateTime(required=True, description="When deployment was created")
    
    # Runtime info
    started_at = DateTime(description="When deployment started")
    stopped_at = DateTime(description="When deployment stopped")
    last_activity_at = DateTime(description="Last activity timestamp")