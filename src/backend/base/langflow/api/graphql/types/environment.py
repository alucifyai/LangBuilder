"""GraphQL types for Environment entities."""

import graphene
from graphene import ObjectType, String, Boolean, List, Field, Int, InputObjectType
from typing import TYPE_CHECKING

from .common import (
    UUID, DateTime, BaseResponse, PaginationInput, SortInput, ValidationError
)

if TYPE_CHECKING:
    from .project import ProjectType
    from .user import UserType


class EnvironmentType(ObjectType):
    """Environment GraphQL type."""
    
    id = UUID(required=True, description="Environment ID")
    name = String(required=True, description="Environment name")
    description = String(description="Environment description")
    
    # Hierarchy
    project_id = UUID(required=True, description="Parent project ID")
    project = Field("langflow.api.graphql.types.project.ProjectType", required=True, description="Parent project")
    
    # Environment type and purpose
    environment_type = String(required=True, description="Environment type (development, staging, production)")
    purpose = String(description="Environment purpose description")
    
    # Ownership
    owner_id = UUID(required=True, description="Environment owner user ID")
    owner = Field("langflow.api.graphql.types.user.UserType", required=True, description="Environment owner")
    
    # Status
    is_active = Boolean(required=True, description="Whether environment is active")
    is_default = Boolean(required=True, description="Whether this is the default environment")
    deployment_status = String(required=True, description="Current deployment status")
    
    # Configuration
    runtime_config = graphene.JSONString(description="Runtime configuration")
    environment_variables = graphene.JSONString(description="Environment variables")
    secrets = List(String, description="Secret names (values not exposed)")
    
    # Resource management
    resource_limits = graphene.JSONString(description="Resource limits configuration")
    auto_scaling_config = graphene.JSONString(description="Auto-scaling configuration")
    
    # Networking and access
    public_url = String(description="Public URL if environment is exposed")
    custom_domain = String(description="Custom domain if configured")
    ssl_enabled = Boolean(required=True, description="Whether SSL is enabled")
    ip_whitelist = List(String, description="IP whitelist for access control")
    
    # Collections
    flows = List("FlowType", description="Flows deployed in environment")
    deployments = List("EnvironmentDeploymentType", description="Deployment history")
    variables = List("EnvironmentVariableType", description="Environment-scoped variables")
    
    # Computed fields
    total_flows = Int(description="Number of flows in environment")
    total_deployments = Int(description="Number of deployments")
    current_deployment_id = UUID(description="Current active deployment ID")
    
    # Health and monitoring
    health_status = String(description="Overall health status")
    last_health_check = DateTime(description="Last health check timestamp")
    uptime_percentage = String(description="Uptime percentage")
    
    # Activity
    last_deployment_at = DateTime(description="Last deployment timestamp")
    last_activity_at = DateTime(description="Last activity timestamp")
    
    # Metadata
    metadata = graphene.JSONString(description="Additional environment metadata")
    tags = List(String, description="Environment tags")
    
    # Timestamps
    created_at = DateTime(required=True, description="When environment was created")
    updated_at = DateTime(required=True, description="When environment was last updated")
    
    def resolve_total_flows(self, info):
        """Resolve total number of flows."""
        return len(self.flows) if self.flows else 0
    
    def resolve_total_deployments(self, info):
        """Resolve total number of deployments."""
        return len(self.deployments) if self.deployments else 0


class EnvironmentVariableType(ObjectType):
    """Environment variable GraphQL type."""
    
    id = UUID(required=True, description="Variable ID")
    environment_id = UUID(required=True, description="Environment ID")
    
    # Variable details
    name = String(required=True, description="Variable name")
    value = String(description="Variable value (redacted for secrets)")
    is_secret = Boolean(required=True, description="Whether variable is a secret")
    description = String(description="Variable description")
    
    # Configuration
    type = String(required=True, description="Variable type (string, number, boolean, json)")
    default_value = String(description="Default value")
    validation_pattern = String(description="Validation regex pattern")
    
    # Access control
    access_level = String(required=True, description="Access level (public, protected, secret)")
    required_permissions = List(String, description="Permissions required to read value")
    
    # Relationships
    environment = Field(EnvironmentType, required=True, description="Parent environment")
    
    # Audit
    created_by_id = UUID(required=True, description="ID of user who created variable")
    created_by = Field("langflow.api.graphql.types.user.UserType", description="User who created variable")
    updated_by_id = UUID(description="ID of user who last updated variable")
    updated_by = Field("langflow.api.graphql.types.user.UserType", description="User who last updated variable")
    
    # Timestamps
    created_at = DateTime(required=True, description="When variable was created")
    updated_at = DateTime(required=True, description="When variable was last updated")


class EnvironmentDeploymentType(ObjectType):
    """Environment deployment GraphQL type."""
    
    id = UUID(required=True, description="Deployment ID")
    environment_id = UUID(required=True, description="Environment ID")
    
    # Deployment details
    environment = Field(EnvironmentType, required=True, description="Environment")
    version = String(required=True, description="Deployment version")
    commit_hash = String(description="Git commit hash")
    
    # Status and lifecycle
    status = String(required=True, description="Deployment status")
    phase = String(required=True, description="Current deployment phase")
    progress_percentage = Int(description="Deployment progress percentage")
    
    # Configuration
    config = graphene.JSONString(description="Deployment configuration")
    runtime_config = graphene.JSONString(description="Runtime configuration")
    resource_allocation = graphene.JSONString(description="Resource allocation")
    
    # Deployment results
    deployed_flows = List(String, description="Successfully deployed flow IDs")
    failed_flows = List(String, description="Failed flow IDs")
    rollback_deployment_id = UUID(description="Previous deployment to rollback to")
    
    # Monitoring
    health_checks = graphene.JSONString(description="Health check configuration")
    monitoring_config = graphene.JSONString(description="Monitoring configuration")
    alerts_config = graphene.JSONString(description="Alerts configuration")
    
    # Logs and output
    deployment_logs = String(description="Deployment logs")
    error_message = String(description="Error message if deployment failed")
    warnings = List(String, description="Deployment warnings")
    
    # Audit
    deployed_by_id = UUID(required=True, description="ID of user who initiated deployment")
    deployed_by = Field("langflow.api.graphql.types.user.UserType", description="User who initiated deployment")
    approved_by_id = UUID(description="ID of user who approved deployment")
    approved_by = Field("langflow.api.graphql.types.user.UserType", description="User who approved deployment")
    
    # Timestamps
    initiated_at = DateTime(required=True, description="When deployment was initiated")
    started_at = DateTime(description="When deployment started")
    completed_at = DateTime(description="When deployment completed")
    failed_at = DateTime(description="When deployment failed")
    
    # Runtime metrics
    startup_time_ms = Int(description="Startup time in milliseconds")
    resource_usage = graphene.JSONString(description="Resource usage metrics")
    performance_metrics = graphene.JSONString(description="Performance metrics")


# Input Types

class EnvironmentCreateInput(InputObjectType):
    """Input for creating an environment."""
    
    name = String(required=True, description="Environment name")
    description = String(description="Environment description")
    project_id = UUID(required=True, description="Parent project ID")
    environment_type = String(required=True, description="Environment type")
    purpose = String(description="Environment purpose description")
    
    # Configuration
    runtime_config = graphene.JSONString(description="Runtime configuration")
    environment_variables = graphene.JSONString(description="Environment variables")
    resource_limits = graphene.JSONString(description="Resource limits configuration")
    auto_scaling_config = graphene.JSONString(description="Auto-scaling configuration")
    
    # Networking
    custom_domain = String(description="Custom domain")
    ssl_enabled = Boolean(default_value=True, description="Whether SSL is enabled")
    ip_whitelist = List(String, description="IP whitelist for access control")
    
    # Metadata
    metadata = graphene.JSONString(description="Additional environment metadata")
    tags = List(String, description="Environment tags")


class EnvironmentUpdateInput(InputObjectType):
    """Input for updating an environment."""
    
    name = String(description="Environment name")
    description = String(description="Environment description")
    purpose = String(description="Environment purpose description")
    is_active = Boolean(description="Whether environment is active")
    is_default = Boolean(description="Whether this is the default environment")
    
    # Configuration
    runtime_config = graphene.JSONString(description="Runtime configuration")
    environment_variables = graphene.JSONString(description="Environment variables")
    resource_limits = graphene.JSONString(description="Resource limits configuration")
    auto_scaling_config = graphene.JSONString(description="Auto-scaling configuration")
    
    # Networking
    custom_domain = String(description="Custom domain")
    ssl_enabled = Boolean(description="Whether SSL is enabled")
    ip_whitelist = List(String, description="IP whitelist for access control")
    
    # Metadata
    metadata = graphene.JSONString(description="Additional environment metadata")
    tags = List(String, description="Environment tags")


class EnvironmentVariableCreateInput(InputObjectType):
    """Input for creating environment variable."""
    
    name = String(required=True, description="Variable name")
    value = String(required=True, description="Variable value")
    is_secret = Boolean(default_value=False, description="Whether variable is a secret")
    description = String(description="Variable description")
    type = String(default_value="string", description="Variable type")
    access_level = String(default_value="public", description="Access level")
    validation_pattern = String(description="Validation regex pattern")


class EnvironmentVariableUpdateInput(InputObjectType):
    """Input for updating environment variable."""
    
    value = String(description="Variable value")
    description = String(description="Variable description")
    access_level = String(description="Access level")
    validation_pattern = String(description="Validation regex pattern")


class EnvironmentFilterInput(InputObjectType):
    """Input for filtering environments."""
    
    search = String(description="Search by name or description")
    project_id = UUID(description="Filter by project")
    environment_type = String(description="Filter by environment type")
    owner_id = UUID(description="Filter by owner")
    is_active = Boolean(description="Filter by active status")
    is_default = Boolean(description="Filter by default status")
    deployment_status = String(description="Filter by deployment status")
    health_status = String(description="Filter by health status")
    tags = List(String, description="Filter by tags")
    created_after = DateTime(description="Filter by creation date")
    created_before = DateTime(description="Filter by creation date")
    last_activity_after = DateTime(description="Filter by last activity")
    last_activity_before = DateTime(description="Filter by last activity")


class EnvironmentDeployInput(InputObjectType):
    """Input for deploying to environment."""
    
    version = String(description="Deployment version")
    commit_hash = String(description="Git commit hash to deploy")
    flow_ids = List(UUID, description="Specific flows to deploy (all if not specified)")
    config_overrides = graphene.JSONString(description="Configuration overrides")
    skip_validation = Boolean(default_value=False, description="Skip pre-deployment validation")
    rollback_on_failure = Boolean(default_value=True, description="Rollback on deployment failure")


# Response Types

class EnvironmentResponse(BaseResponse):
    """Response for environment operations."""
    
    environment = Field(EnvironmentType, description="The environment data")
    validation_errors = List(ValidationError, description="Field validation errors")


class EnvironmentListResponse(ObjectType):
    """Response for environment list queries."""
    
    environments = List(EnvironmentType, required=True, description="List of environments")
    total_count = Int(required=True, description="Total number of environments matching filter")
    has_next_page = Boolean(required=True, description="Whether there are more environments")


class EnvironmentVariableResponse(BaseResponse):
    """Response for environment variable operations."""
    
    variable = Field(EnvironmentVariableType, description="The environment variable data")
    validation_errors = List(ValidationError, description="Field validation errors")


class EnvironmentDeploymentResponse(BaseResponse):
    """Response for environment deployment operations."""
    
    deployment = Field(EnvironmentDeploymentType, description="The deployment data")
    validation_errors = List(ValidationError, description="Field validation errors")


class EnvironmentStatsType(ObjectType):
    """Environment statistics."""
    
    environment = Field(EnvironmentType, required=True, description="Environment")
    
    # Deployment stats
    total_deployments = Int(required=True, description="Total number of deployments")
    successful_deployments = Int(required=True, description="Number of successful deployments")
    failed_deployments = Int(required=True, description="Number of failed deployments")
    deployment_success_rate = String(description="Deployment success rate percentage")
    avg_deployment_time_minutes = Int(description="Average deployment time in minutes")
    
    # Flow stats
    total_flows = Int(required=True, description="Number of flows in environment")
    active_flows = Int(required=True, description="Number of active flows")
    flow_executions_30d = Int(required=True, description="Flow executions in last 30 days")
    avg_execution_time_ms = Int(description="Average execution time in milliseconds")
    
    # Resource usage
    current_cpu_usage = String(description="Current CPU usage percentage")
    current_memory_usage = String(description="Current memory usage percentage")
    storage_used_mb = Int(required=True, description="Storage used in MB")
    
    # Availability
    uptime_30d = String(description="Uptime percentage in last 30 days")
    downtime_incidents_30d = Int(required=True, description="Downtime incidents in last 30 days")
    last_outage_at = DateTime(description="Last outage timestamp")
    
    # Performance
    avg_response_time_ms = Int(description="Average response time in milliseconds")
    error_rate_30d = String(description="Error rate in last 30 days")
    throughput_30d = Int(description="Requests processed in last 30 days")


class EnvironmentHealthType(ObjectType):
    """Environment health information."""
    
    environment = Field(EnvironmentType, required=True, description="Environment")
    overall_status = String(required=True, description="Overall health status")
    
    # Component health
    api_status = String(required=True, description="API health status")
    database_status = String(required=True, description="Database health status")
    storage_status = String(required=True, description="Storage health status")
    network_status = String(required=True, description="Network health status")
    
    # Detailed checks
    health_checks = List("HealthCheckType", description="Individual health checks")
    
    # Metrics
    response_time_ms = Int(description="Health check response time")
    last_check_at = DateTime(required=True, description="Last health check timestamp")
    next_check_at = DateTime(description="Next scheduled health check")
    
    # Issues
    active_issues = List(String, description="Active health issues")
    warnings = List(String, description="Health warnings")
    recommendations = List(String, description="Health improvement recommendations")


class HealthCheckType(ObjectType):
    """Individual health check result."""
    
    name = String(required=True, description="Health check name")
    status = String(required=True, description="Check status (healthy, warning, critical)")
    message = String(description="Check result message")
    details = graphene.JSONString(description="Detailed check results")
    duration_ms = Int(description="Check duration in milliseconds")
    last_run_at = DateTime(required=True, description="When check was last run")
    
    # Thresholds
    warning_threshold = String(description="Warning threshold")
    critical_threshold = String(description="Critical threshold")
    current_value = String(description="Current measured value")