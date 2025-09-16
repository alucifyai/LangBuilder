"""Main GraphQL schema for RBAC system."""

import graphene
from graphene import ObjectType, Field, List, String, Boolean, Int

# Import all types
from .types.common import (
    UUID, DateTime, PaginationInput, SortInput, BaseResponse,
    ScopeTypeEnum, AssignmentTypeEnum, RoleTypeEnum, PermissionActionEnum,
    ResourceTypeEnum, AuditEventTypeEnum, AuditActorTypeEnum, SSOProviderTypeEnum
)
from .types.workspace import (
    WorkspaceType, WorkspaceInvitationType, WorkspaceCreateInput, WorkspaceUpdateInput,
    WorkspaceFilterInput, WorkspaceInviteInput, WorkspaceResponse, WorkspaceListResponse,
    WorkspaceInvitationResponse, WorkspaceStatsType, WorkspaceStatsResponse
)
from .types.project import (
    ProjectType, ProjectContributorType, ProjectTemplateType, ProjectCreateInput,
    ProjectUpdateInput, ProjectFilterInput, ProjectContributorAddInput,
    ProjectContributorUpdateInput, ProjectResponse, ProjectListResponse,
    ProjectContributorResponse, ProjectTemplateListResponse, ProjectStatsType,
    ProjectDeploymentType
)
from .types.environment import (
    EnvironmentType, EnvironmentVariableType, EnvironmentDeploymentType,
    EnvironmentCreateInput, EnvironmentUpdateInput, EnvironmentFilterInput,
    EnvironmentVariableCreateInput, EnvironmentVariableUpdateInput,
    EnvironmentDeployInput, EnvironmentResponse, EnvironmentListResponse,
    EnvironmentVariableResponse, EnvironmentDeploymentResponse,
    EnvironmentStatsType, EnvironmentHealthType
)
from .types.role import (
    RoleType, PermissionType, RolePermissionType, RoleCreateInput, RoleUpdateInput,
    RolePermissionAssignInput, RoleFilterInput, PermissionFilterInput,
    RoleResponse, RoleListResponse, PermissionResponse, PermissionListResponse,
    RolePermissionResponse, RoleHierarchyType, RoleStatsType
)
from .types.assignment import (
    RoleAssignmentType, RoleAssignmentScopeType, RoleAssignmentCreateInput,
    RoleAssignmentUpdateInput, RoleAssignmentFilterInput, BulkRoleAssignmentInput,
    RoleAssignmentResponse, RoleAssignmentListResponse, BulkRoleAssignmentResponse,
    RoleAssignmentStatsType, AssignmentApprovalType
)
from .types.user import (
    UserType, UserGroupType, UserGroupMembershipType, WorkspaceMembershipType,
    UserCreateInput, UserUpdateInput, UserFilterInput, UserGroupCreateInput,
    UserGroupUpdateInput, UserGroupMembershipInput, UserResponse, UserListResponse,
    UserGroupResponse, UserGroupListResponse, UserStatsType, UserActivityType
)
from .types.audit import (
    AuditLogType, AuditLogMetricsType, AuditLogFilterInput, AuditLogExportInput,
    AuditComplianceReportInput, AuditLogResponse, AuditLogListResponse,
    AuditLogExportResponse, AuditComplianceReportResponse, AuditAlertType,
    AuditRetentionPolicyType
)


class Query(ObjectType):
    """GraphQL Query root for RBAC system."""
    
    # Workspace queries
    workspace = Field(
        WorkspaceType,
        id=UUID(required=True),
        description="Get workspace by ID"
    )
    workspaces = Field(
        WorkspaceListResponse,
        filter=WorkspaceFilterInput(),
        pagination=PaginationInput(),
        sort=List(SortInput),
        description="List workspaces with filtering"
    )
    workspace_stats = Field(
        WorkspaceStatsResponse,
        workspace_id=UUID(required=True),
        period_days=Int(default_value=30),
        description="Get workspace statistics"
    )
    
    # Project queries
    project = Field(
        ProjectType,
        id=UUID(required=True),
        description="Get project by ID"
    )
    projects = Field(
        ProjectListResponse,
        filter=ProjectFilterInput(),
        pagination=PaginationInput(),
        sort=List(SortInput),
        description="List projects with filtering"
    )
    project_templates = Field(
        ProjectTemplateListResponse,
        category=String(),
        pagination=PaginationInput(),
        description="List project templates"
    )
    project_stats = Field(
        ProjectStatsType,
        project_id=UUID(required=True),
        description="Get project statistics"
    )
    
    # Environment queries
    environment = Field(
        EnvironmentType,
        id=UUID(required=True),
        description="Get environment by ID"
    )
    environments = Field(
        EnvironmentListResponse,
        filter=EnvironmentFilterInput(),
        pagination=PaginationInput(),
        sort=List(SortInput),
        description="List environments with filtering"
    )
    environment_stats = Field(
        EnvironmentStatsType,
        environment_id=UUID(required=True),
        description="Get environment statistics"
    )
    environment_health = Field(
        EnvironmentHealthType,
        environment_id=UUID(required=True),
        description="Get environment health status"
    )
    
    # Role and permission queries
    role = Field(
        RoleType,
        id=UUID(required=True),
        description="Get role by ID"
    )
    roles = Field(
        RoleListResponse,
        filter=RoleFilterInput(),
        pagination=PaginationInput(),
        sort=List(SortInput),
        description="List roles with filtering"
    )
    role_hierarchy = Field(
        List(RoleHierarchyType),
        workspace_id=UUID(),
        description="Get role hierarchy for workspace"
    )
    role_stats = Field(
        List(RoleStatsType),
        workspace_id=UUID(),
        description="Get role usage statistics"
    )
    
    permission = Field(
        PermissionType,
        id=UUID(required=True),
        description="Get permission by ID"
    )
    permissions = Field(
        PermissionListResponse,
        filter=PermissionFilterInput(),
        pagination=PaginationInput(),
        sort=List(SortInput),
        description="List permissions with filtering"
    )
    
    # Role assignment queries
    role_assignment = Field(
        RoleAssignmentType,
        id=UUID(required=True),
        description="Get role assignment by ID"
    )
    role_assignments = Field(
        RoleAssignmentListResponse,
        filter=RoleAssignmentFilterInput(),
        pagination=PaginationInput(),
        sort=List(SortInput),
        description="List role assignments with filtering"
    )
    role_assignment_stats = Field(
        RoleAssignmentStatsType,
        workspace_id=UUID(),
        description="Get role assignment statistics"
    )
    
    # User queries
    user = Field(
        UserType,
        id=UUID(required=True),
        description="Get user by ID"
    )
    users = Field(
        UserListResponse,
        filter=UserFilterInput(),
        pagination=PaginationInput(),
        sort=List(SortInput),
        description="List users with filtering"
    )
    user_stats = Field(
        UserStatsType,
        workspace_id=UUID(),
        description="Get user statistics"
    )
    user_activity = Field(
        List(UserActivityType),
        user_ids=List(UUID),
        workspace_id=UUID(),
        description="Get user activity information"
    )
    
    # User group queries
    user_group = Field(
        UserGroupType,
        id=UUID(required=True),
        description="Get user group by ID"
    )
    user_groups = Field(
        UserGroupListResponse,
        workspace_id=UUID(),
        pagination=PaginationInput(),
        description="List user groups"
    )
    
    # Audit queries
    audit_log = Field(
        AuditLogType,
        id=UUID(required=True),
        description="Get audit log entry by ID"
    )
    audit_logs = Field(
        AuditLogListResponse,
        filter=AuditLogFilterInput(),
        pagination=PaginationInput(),
        sort=List(SortInput),
        description="List audit logs with filtering"
    )
    audit_alerts = Field(
        List(AuditAlertType),
        workspace_id=UUID(),
        severity=String(),
        status=String(),
        description="List audit alerts"
    )
    audit_retention_policies = Field(
        List(AuditRetentionPolicyType),
        workspace_id=UUID(),
        description="List audit retention policies"
    )
    
    # Permission checking
    check_permission = Field(
        "langflow.api.graphql.types.common.PermissionCheck",
        user_id=UUID(required=True),
        resource_type=ResourceTypeEnum(required=True),
        action=PermissionActionEnum(required=True),
        resource_id=UUID(),
        scope_type=ScopeTypeEnum(),
        scope_id=UUID(),
        description="Check if user has specific permission"
    )
    
    check_bulk_permissions = Field(
        List("langflow.api.graphql.types.common.PermissionCheck"),
        user_id=UUID(required=True),
        permission_requests=List(String, required=True),  # JSON encoded permission requests
        description="Check multiple permissions at once"
    )


class Mutation(ObjectType):
    """GraphQL Mutation root for RBAC system."""
    
    # Workspace mutations
    create_workspace = Field(
        WorkspaceResponse,
        input=WorkspaceCreateInput(required=True),
        description="Create a new workspace"
    )
    update_workspace = Field(
        WorkspaceResponse,
        id=UUID(required=True),
        input=WorkspaceUpdateInput(required=True),
        description="Update workspace"
    )
    delete_workspace = Field(
        BaseResponse,
        id=UUID(required=True),
        force=Boolean(default_value=False),
        description="Delete workspace"
    )
    invite_user_to_workspace = Field(
        WorkspaceInvitationResponse,
        workspace_id=UUID(required=True),
        input=WorkspaceInviteInput(required=True),
        description="Invite user to workspace"
    )
    
    # Project mutations
    create_project = Field(
        ProjectResponse,
        input=ProjectCreateInput(required=True),
        description="Create a new project"
    )
    update_project = Field(
        ProjectResponse,
        id=UUID(required=True),
        input=ProjectUpdateInput(required=True),
        description="Update project"
    )
    delete_project = Field(
        BaseResponse,
        id=UUID(required=True),
        description="Delete project"
    )
    add_project_contributor = Field(
        ProjectContributorResponse,
        project_id=UUID(required=True),
        input=ProjectContributorAddInput(required=True),
        description="Add contributor to project"
    )
    
    # Environment mutations
    create_environment = Field(
        EnvironmentResponse,
        input=EnvironmentCreateInput(required=True),
        description="Create a new environment"
    )
    update_environment = Field(
        EnvironmentResponse,
        id=UUID(required=True),
        input=EnvironmentUpdateInput(required=True),
        description="Update environment"
    )
    delete_environment = Field(
        BaseResponse,
        id=UUID(required=True),
        description="Delete environment"
    )
    deploy_to_environment = Field(
        EnvironmentDeploymentResponse,
        environment_id=UUID(required=True),
        input=EnvironmentDeployInput(required=True),
        description="Deploy to environment"
    )
    create_environment_variable = Field(
        EnvironmentVariableResponse,
        environment_id=UUID(required=True),
        input=EnvironmentVariableCreateInput(required=True),
        description="Create environment variable"
    )
    
    # Role mutations
    create_role = Field(
        RoleResponse,
        input=RoleCreateInput(required=True),
        description="Create a new role"
    )
    update_role = Field(
        RoleResponse,
        id=UUID(required=True),
        input=RoleUpdateInput(required=True),
        description="Update role"
    )
    delete_role = Field(
        BaseResponse,
        id=UUID(required=True),
        description="Delete role"
    )
    assign_permission_to_role = Field(
        RolePermissionResponse,
        role_id=UUID(required=True),
        input=RolePermissionAssignInput(required=True),
        description="Assign permission to role"
    )
    revoke_permission_from_role = Field(
        BaseResponse,
        role_id=UUID(required=True),
        permission_id=UUID(required=True),
        description="Revoke permission from role"
    )
    initialize_system_roles = Field(
        BaseResponse,
        description="Initialize system roles and permissions"
    )
    
    # Role assignment mutations
    create_role_assignment = Field(
        RoleAssignmentResponse,
        input=RoleAssignmentCreateInput(required=True),
        description="Create role assignment"
    )
    update_role_assignment = Field(
        RoleAssignmentResponse,
        id=UUID(required=True),
        input=RoleAssignmentUpdateInput(required=True),
        description="Update role assignment"
    )
    delete_role_assignment = Field(
        BaseResponse,
        id=UUID(required=True),
        description="Delete role assignment"
    )
    create_bulk_role_assignments = Field(
        BulkRoleAssignmentResponse,
        input=BulkRoleAssignmentInput(required=True),
        description="Create multiple role assignments"
    )
    
    # User mutations
    create_user = Field(
        UserResponse,
        input=UserCreateInput(required=True),
        description="Create a new user"
    )
    update_user = Field(
        UserResponse,
        id=UUID(required=True),
        input=UserUpdateInput(required=True),
        description="Update user"
    )
    delete_user = Field(
        BaseResponse,
        id=UUID(required=True),
        description="Delete user"
    )
    activate_user = Field(
        UserResponse,
        id=UUID(required=True),
        description="Activate user account"
    )
    deactivate_user = Field(
        UserResponse,
        id=UUID(required=True),
        description="Deactivate user account"
    )
    
    # User group mutations
    create_user_group = Field(
        UserGroupResponse,
        input=UserGroupCreateInput(required=True),
        description="Create a new user group"
    )
    update_user_group = Field(
        UserGroupResponse,
        id=UUID(required=True),
        input=UserGroupUpdateInput(required=True),
        description="Update user group"
    )
    delete_user_group = Field(
        BaseResponse,
        id=UUID(required=True),
        description="Delete user group"
    )
    add_user_to_group = Field(
        BaseResponse,
        group_id=UUID(required=True),
        input=UserGroupMembershipInput(required=True),
        description="Add user to group"
    )
    remove_user_from_group = Field(
        BaseResponse,
        group_id=UUID(required=True),
        user_id=UUID(required=True),
        description="Remove user from group"
    )
    
    # Audit mutations
    export_audit_logs = Field(
        AuditLogExportResponse,
        input=AuditLogExportInput(required=True),
        description="Export audit logs"
    )
    generate_compliance_report = Field(
        AuditComplianceReportResponse,
        input=AuditComplianceReportInput(required=True),
        description="Generate compliance report"
    )


# Main schema
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    types=[
        # Ensure all types are included in schema
        WorkspaceType, ProjectType, EnvironmentType, RoleType, PermissionType,
        RoleAssignmentType, UserType, UserGroupType, AuditLogType,
        
        # Enums
        ScopeTypeEnum, AssignmentTypeEnum, RoleTypeEnum, PermissionActionEnum,
        ResourceTypeEnum, AuditEventTypeEnum, AuditActorTypeEnum, SSOProviderTypeEnum
    ]
)


# Schema validation utilities
def validate_schema():
    """Validate the GraphQL schema definition."""
    try:
        # Test schema introspection
        from graphene.test import Client
        client = Client(schema)
        
        # Test basic introspection query
        result = client.execute('''
            query {
                __schema {
                    types {
                        name
                        kind
                    }
                }
            }
        ''')
        
        if result.errors:
            raise Exception(f"Schema validation failed: {result.errors}")
        
        print("✅ GraphQL schema validation passed")
        return True
        
    except Exception as e:
        print(f"❌ GraphQL schema validation failed: {e}")
        return False


# Schema documentation generator
def generate_schema_docs():
    """Generate GraphQL schema documentation."""
    from graphene.utils.schema_printer import print_schema
    
    schema_sdl = print_schema(schema)
    
    # Write to file
    with open("graphql_schema.graphql", "w") as f:
        f.write(schema_sdl)
    
    print("📝 GraphQL schema documentation generated: graphql_schema.graphql")
    return schema_sdl


if __name__ == "__main__":
    # Validate schema when run directly
    validate_schema()
    generate_schema_docs()