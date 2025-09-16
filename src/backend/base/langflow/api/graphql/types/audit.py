"""GraphQL types for Audit Log entities."""

import graphene
from graphene import ObjectType, String, Boolean, List, Field, Int, InputObjectType
from typing import TYPE_CHECKING

from .common import (
    UUID, DateTime, BaseResponse, PaginationInput, SortInput, ValidationError,
    AuditEventTypeEnum, AuditActorTypeEnum, ResourceTypeEnum
)

if TYPE_CHECKING:
    from .user import UserType
    from .workspace import WorkspaceType


class AuditLogType(ObjectType):
    """Audit log entry GraphQL type."""
    
    id = UUID(required=True, description="Audit log entry ID")
    
    # Event identification
    event_type = AuditEventTypeEnum(required=True, description="Type of event")
    action = String(required=True, description="Specific action performed")
    outcome = String(required=True, description="Event outcome (success, failure, etc.)")
    
    # Actor information
    actor_type = AuditActorTypeEnum(required=True, description="Type of actor")
    actor_id = UUID(description="Actor ID (user, service account, etc.)")
    actor_name = String(description="Actor display name")
    actor_email = String(description="Actor email (for users)")
    
    # Resource information
    resource_type = ResourceTypeEnum(description="Type of resource affected")
    resource_id = UUID(description="ID of resource affected")
    resource_name = String(description="Name of resource affected")
    
    # Context
    workspace_id = UUID(description="Workspace context")
    workspace = Field("langflow.api.graphql.types.workspace.WorkspaceType", description="Workspace object")
    project_id = UUID(description="Project context")
    environment_id = UUID(description="Environment context")
    flow_id = UUID(description="Flow context")
    
    # Session and request info
    session_id = UUID(description="Session ID")
    request_id = String(description="Request ID for tracing")
    ip_address = String(description="Source IP address")
    user_agent = String(description="User agent string")
    
    # Event details
    details = graphene.JSONString(description="Detailed event information")
    metadata = graphene.JSONString(description="Additional metadata")
    
    # Changes tracking
    before_state = graphene.JSONString(description="State before change")
    after_state = graphene.JSONString(description="State after change")
    changed_fields = List(String, description="Fields that were changed")
    
    # Compliance and retention
    retention_required = Boolean(required=True, description="Whether this log must be retained for compliance")
    sensitive_data_accessed = Boolean(required=True, description="Whether sensitive data was accessed")
    compliance_tags = List(String, description="Compliance framework tags (SOC2, GDPR, etc.)")
    
    # Risk and security
    risk_score = Int(description="Risk score for this event (0-100)")
    anomaly_detected = Boolean(required=True, description="Whether anomalous behavior was detected")
    suspicious_indicators = List(String, description="Indicators of suspicious activity")
    
    # Timestamps
    timestamp = DateTime(required=True, description="When event occurred")
    ingested_at = DateTime(required=True, description="When log was ingested")
    
    # Computed fields
    actor_display_name = String(description="Formatted actor name")
    event_summary = String(description="Human-readable event summary")
    
    def resolve_actor_display_name(self, info):
        """Resolve formatted actor display name."""
        if self.actor_type == "user":
            return self.actor_name or self.actor_email or f"User {self.actor_id}"
        elif self.actor_type == "service_account":
            return f"Service Account: {self.actor_name or self.actor_id}"
        elif self.actor_type == "system":
            return "System"
        return "Unknown"
    
    def resolve_event_summary(self, info):
        """Resolve human-readable event summary."""
        actor = self.resolve_actor_display_name(info)
        action = self.action.replace("_", " ").title()
        
        if self.resource_type and self.resource_name:
            return f"{actor} {action} {self.resource_type} '{self.resource_name}'"
        elif self.resource_type:
            return f"{actor} {action} {self.resource_type}"
        else:
            return f"{actor} {action}"


class AuditLogMetricsType(ObjectType):
    """Audit log metrics and statistics."""
    
    total_events = Int(required=True, description="Total number of events")
    events_by_type = graphene.JSONString(required=True, description="Event count by type")
    events_by_actor = graphene.JSONString(required=True, description="Event count by actor type")
    events_by_outcome = graphene.JSONString(required=True, description="Event count by outcome")
    
    # Risk metrics
    high_risk_events = Int(required=True, description="Number of high-risk events")
    anomalies_detected = Int(required=True, description="Number of anomalies detected")
    failed_authentications = Int(required=True, description="Number of failed authentication attempts")
    
    # Activity metrics
    unique_actors = Int(required=True, description="Number of unique actors")
    peak_activity_hour = String(description="Hour with peak activity")
    most_active_user = String(description="Most active user")
    
    # Time-based metrics
    events_last_hour = Int(required=True, description="Events in last hour")
    events_last_day = Int(required=True, description="Events in last day")
    events_last_week = Int(required=True, description="Events in last week")


# Input Types

class AuditLogFilterInput(InputObjectType):
    """Input for filtering audit logs."""
    
    # Event filters
    event_types = List(AuditEventTypeEnum, description="Filter by event types")
    actions = List(String, description="Filter by specific actions")
    outcomes = List(String, description="Filter by outcomes")
    
    # Actor filters
    actor_types = List(AuditActorTypeEnum, description="Filter by actor types")
    actor_ids = List(UUID, description="Filter by specific actors")
    actor_email = String(description="Filter by actor email")
    
    # Resource filters
    resource_types = List(ResourceTypeEnum, description="Filter by resource types")
    resource_ids = List(UUID, description="Filter by specific resources")
    
    # Context filters
    workspace_ids = List(UUID, description="Filter by workspaces")
    project_ids = List(UUID, description="Filter by projects")
    environment_ids = List(UUID, description="Filter by environments")
    flow_ids = List(UUID, description="Filter by flows")
    
    # Session filters
    session_ids = List(UUID, description="Filter by session IDs")
    ip_addresses = List(String, description="Filter by IP addresses")
    
    # Compliance filters
    retention_required = Boolean(description="Filter by retention requirement")
    sensitive_data_accessed = Boolean(description="Filter by sensitive data access")
    compliance_tags = List(String, description="Filter by compliance tags")
    
    # Risk filters
    min_risk_score = Int(description="Minimum risk score")
    max_risk_score = Int(description="Maximum risk score")
    anomaly_detected = Boolean(description="Filter by anomaly detection")
    
    # Time filters
    start_time = DateTime(description="Start of time range")
    end_time = DateTime(description="End of time range")
    last_n_hours = Int(description="Last N hours")
    last_n_days = Int(description="Last N days")
    
    # Text search
    search = String(description="Full-text search in event details")


class AuditLogExportInput(InputObjectType):
    """Input for exporting audit logs."""
    
    format = String(required=True, description="Export format (csv, json, pdf)")
    filters = Field(AuditLogFilterInput, description="Filters to apply")
    include_sensitive = Boolean(default_value=False, description="Whether to include sensitive data")
    include_metadata = Boolean(default_value=True, description="Whether to include metadata")
    compress = Boolean(default_value=False, description="Whether to compress export")


class AuditComplianceReportInput(InputObjectType):
    """Input for generating compliance reports."""
    
    framework = String(required=True, description="Compliance framework (SOC2, GDPR, HIPAA, etc.)")
    start_date = DateTime(required=True, description="Report start date")
    end_date = DateTime(required=True, description="Report end date")
    include_recommendations = Boolean(default_value=True, description="Include security recommendations")
    workspace_ids = List(UUID, description="Limit to specific workspaces")


# Response Types

class AuditLogResponse(BaseResponse):
    """Response for audit log operations."""
    
    log_entry = Field(AuditLogType, description="The audit log entry")
    validation_errors = List(ValidationError, description="Field validation errors")


class AuditLogListResponse(ObjectType):
    """Response for audit log list queries."""
    
    logs = List(AuditLogType, required=True, description="List of audit log entries")
    total_count = Int(required=True, description="Total number of logs matching filter")
    has_next_page = Boolean(required=True, description="Whether there are more logs")
    
    # Aggregations
    metrics = Field(AuditLogMetricsType, description="Metrics for the filtered logs")


class AuditLogExportResponse(BaseResponse):
    """Response for audit log export operations."""
    
    export_id = UUID(description="Export job ID")
    download_url = String(description="URL to download export file")
    file_size_bytes = Int(description="Size of export file in bytes")
    record_count = Int(description="Number of records in export")
    expires_at = DateTime(description="When download URL expires")


class AuditComplianceReportResponse(BaseResponse):
    """Response for compliance report generation."""
    
    report_id = UUID(description="Report ID")
    download_url = String(description="URL to download report")
    framework = String(required=True, description="Compliance framework")
    period_start = DateTime(required=True, description="Report period start")
    period_end = DateTime(required=True, description="Report period end")
    
    # Report summary
    total_events = Int(required=True, description="Total events in period")
    compliance_score = Int(description="Compliance score (0-100)")
    violations_found = Int(required=True, description="Number of policy violations")
    recommendations_count = Int(required=True, description="Number of recommendations")
    
    generated_at = DateTime(required=True, description="When report was generated")
    expires_at = DateTime(description="When report expires")


class AuditAlertType(ObjectType):
    """Audit alert for suspicious activity."""
    
    id = UUID(required=True, description="Alert ID")
    severity = String(required=True, description="Alert severity (low, medium, high, critical)")
    title = String(required=True, description="Alert title")
    description = String(required=True, description="Alert description")
    
    # Related events
    triggering_event_id = UUID(required=True, description="Event that triggered alert")
    triggering_event = Field(AuditLogType, description="Event that triggered alert")
    related_event_ids = List(UUID, description="Related event IDs")
    
    # Alert details
    indicators = List(String, description="Suspicious indicators")
    risk_score = Int(required=True, description="Risk score (0-100)")
    false_positive_likelihood = Int(description="Likelihood of false positive (0-100)")
    
    # Response
    status = String(required=True, description="Alert status (open, investigating, resolved, false_positive)")
    assigned_to_id = UUID(description="ID of user assigned to investigate")
    assigned_to = Field("langflow.api.graphql.types.user.UserType", description="User assigned to investigate")
    
    # Resolution
    resolved_by_id = UUID(description="ID of user who resolved alert")
    resolved_by = Field("langflow.api.graphql.types.user.UserType", description="User who resolved alert")
    resolution_notes = String(description="Resolution notes")
    
    # Timestamps
    created_at = DateTime(required=True, description="When alert was created")
    updated_at = DateTime(required=True, description="When alert was last updated")
    resolved_at = DateTime(description="When alert was resolved")


class AuditRetentionPolicyType(ObjectType):
    """Audit log retention policy."""
    
    id = UUID(required=True, description="Policy ID")
    name = String(required=True, description="Policy name")
    description = String(description="Policy description")
    
    # Retention rules
    default_retention_days = Int(required=True, description="Default retention period")
    compliance_retention_days = Int(required=True, description="Compliance log retention period")
    sensitive_data_retention_days = Int(required=True, description="Sensitive data log retention period")
    
    # Event-specific rules
    event_type_rules = graphene.JSONString(description="Retention rules by event type")
    
    # Policy status
    is_active = Boolean(required=True, description="Whether policy is active")
    workspace_id = UUID(description="Workspace ID (null for global policy)")
    
    # Audit
    created_by_id = UUID(required=True, description="ID of user who created policy")
    created_at = DateTime(required=True, description="When policy was created")
    updated_at = DateTime(required=True, description="When policy was last updated")