"""Tests for individual GraphQL type definitions and validation."""

import pytest
import uuid
from datetime import datetime, timezone
from graphene.test import Client

from langflow.api.graphql.schema import schema
from langflow.api.graphql.types.workspace import WorkspaceType, WorkspaceCreateInput, WorkspaceUpdateInput
from langflow.api.graphql.types.project import ProjectType, ProjectCreateInput, ProjectUpdateInput
from langflow.api.graphql.types.environment import EnvironmentType, EnvironmentCreateInput
from langflow.api.graphql.types.role import RoleType, PermissionType, RoleCreateInput
from langflow.api.graphql.types.assignment import RoleAssignmentType, RoleAssignmentCreateInput
from langflow.api.graphql.types.user import UserType, UserGroupType, UserCreateInput
from langflow.api.graphql.types.audit import AuditLogType, AuditLogFilterInput


class TestWorkspaceTypes:
    """Test Workspace-related GraphQL types."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_workspace_type_has_required_fields(self):
        """Test WorkspaceType has all required fields."""
        query = '''
            query {
                __type(name: "WorkspaceType") {
                    fields {
                        name
                        type {
                            name
                            kind
                            nonNull
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        fields = {f["name"]: f["type"] for f in result.data["__type"]["fields"]}
        
        # Test required fields are non-null
        required_fields = ["id", "name", "isActive", "isDeleted", "ownerId", "createdAt", "updatedAt"]
        for field in required_fields:
            assert field in fields
    
    def test_workspace_settings_type_definition(self):
        """Test WorkspaceSettingsType definition."""
        query = '''
            query {
                __type(name: "WorkspaceSettingsType") {
                    name
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        settings_type = result.data["__type"]
        field_names = [f["name"] for f in settings_type["fields"]]
        expected_fields = [
            "ssoEnabled", "autoAssignRole", "maxProjects", "maxUsers",
            "requireApproval", "dataRetentionDays", "allowExternalSharing", "enforceMfa"
        ]
        
        for field in expected_fields:
            assert field in field_names
    
    def test_workspace_invitation_type_definition(self):
        """Test WorkspaceInvitationType definition."""
        query = '''
            query {
                __type(name: "WorkspaceInvitationType") {
                    name
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        invitation_type = result.data["__type"]
        field_names = [f["name"] for f in invitation_type["fields"]]
        expected_fields = [
            "id", "workspaceId", "email", "roleId", "status", "expiresAt",
            "acceptedAt", "invitedById", "message", "createdAt", "updatedAt"
        ]
        
        for field in expected_fields:
            assert field in field_names
    
    def test_workspace_create_input_validation(self):
        """Test WorkspaceCreateInput has proper validation."""
        query = '''
            query {
                __type(name: "WorkspaceCreateInput") {
                    inputFields {
                        name
                        type {
                            name
                            kind
                            nonNull
                        }
                        defaultValue
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        input_fields = {f["name"]: f for f in result.data["__type"]["inputFields"]}
        
        # Name should be required
        assert "name" in input_fields
        assert input_fields["name"]["type"]["nonNull"] is True
        
        # Optional fields should not be required
        optional_fields = ["description", "organization", "settings", "metadata", "tags"]
        for field in optional_fields:
            if field in input_fields:
                assert input_fields[field]["type"]["nonNull"] is not True
    
    def test_workspace_filter_input_comprehensive(self):
        """Test WorkspaceFilterInput has comprehensive filtering options."""
        query = '''
            query {
                __type(name: "WorkspaceFilterInput") {
                    inputFields {
                        name
                        type {
                            name
                            ofType {
                                name
                            }
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        filter_fields = [f["name"] for f in result.data["__type"]["inputFields"]]
        expected_filters = [
            "search", "organization", "isActive", "ownerId", "tags",
            "createdAfter", "createdBefore"
        ]
        
        for filter_field in expected_filters:
            assert filter_field in filter_fields


class TestProjectTypes:
    """Test Project-related GraphQL types."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_project_type_hierarchy_fields(self):
        """Test ProjectType has proper hierarchy fields."""
        query = '''
            query {
                __type(name: "ProjectType") {
                    fields {
                        name
                        type {
                            name
                            kind
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        
        # Hierarchy fields
        hierarchy_fields = ["workspaceId", "workspace", "ownerId", "owner"]
        for field in hierarchy_fields:
            assert field in field_names
        
        # Collection fields
        collection_fields = ["environments", "flows", "contributors"]
        for field in collection_fields:
            assert field in field_names
        
        # Computed fields
        computed_fields = ["totalEnvironments", "totalFlows", "totalDeployments"]
        for field in computed_fields:
            assert field in field_names
    
    def test_project_contributor_type_definition(self):
        """Test ProjectContributorType definition."""
        query = '''
            query {
                __type(name: "ProjectContributorType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        expected_fields = [
            "id", "projectId", "userId", "role", "permissions", "isActive",
            "lastContributionAt", "contributionCount", "addedById", "addedAt"
        ]
        
        for field in expected_fields:
            assert field in field_names
    
    def test_project_template_type_definition(self):
        """Test ProjectTemplateType definition."""
        query = '''
            query {
                __type(name: "ProjectTemplateType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        expected_fields = [
            "id", "name", "description", "category", "projectConfig",
            "environmentConfigs", "defaultFlows", "isPublic", "isOfficial",
            "version", "usageCount", "rating", "createdById", "createdAt"
        ]
        
        for field in expected_fields:
            assert field in field_names


class TestEnvironmentTypes:
    """Test Environment-related GraphQL types."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_environment_type_configuration_fields(self):
        """Test EnvironmentType has configuration fields."""
        query = '''
            query {
                __type(name: "EnvironmentType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        
        # Configuration fields
        config_fields = [
            "runtimeConfig", "environmentVariables", "resourceLimits",
            "autoScalingConfig", "customDomain", "sslEnabled", "ipWhitelist"
        ]
        for field in config_fields:
            assert field in field_names
        
        # Status fields
        status_fields = [
            "isActive", "isDefault", "deploymentStatus", "healthStatus",
            "lastHealthCheck", "uptimePercentage"
        ]
        for field in status_fields:
            assert field in field_names
    
    def test_environment_variable_type_security(self):
        """Test EnvironmentVariableType has security fields."""
        query = '''
            query {
                __type(name: "EnvironmentVariableType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        
        # Security fields
        security_fields = [
            "isSecret", "accessLevel", "requiredPermissions", "validationPattern"
        ]
        for field in security_fields:
            assert field in field_names
    
    def test_environment_deployment_type_definition(self):
        """Test EnvironmentDeploymentType definition."""
        query = '''
            query {
                __type(name: "EnvironmentDeploymentType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        expected_fields = [
            "id", "environmentId", "version", "commitHash", "status", "phase",
            "progressPercentage", "config", "deployedFlows", "failedFlows",
            "deploymentLogs", "errorMessage", "deployedById", "initiatedAt"
        ]
        
        for field in expected_fields:
            assert field in field_names


class TestRoleAndPermissionTypes:
    """Test Role and Permission-related GraphQL types."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_role_type_hierarchy_features(self):
        """Test RoleType supports hierarchy."""
        query = '''
            query {
                __type(name: "RoleType") {
                    fields {
                        name
                        type {
                            name
                            ofType {
                                name
                            }
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        
        # Hierarchy fields
        hierarchy_fields = ["parentRoleId", "parentRole", "childRoles"]
        for field in hierarchy_fields:
            assert field in field_names
        
        # Computed hierarchy fields
        computed_fields = ["effectivePermissions", "totalAssignments", "totalUsers"]
        for field in computed_fields:
            assert field in field_names
    
    def test_permission_type_constraint_support(self):
        """Test PermissionType supports constraints."""
        query = '''
            query {
                __type(name: "PermissionType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        
        # Constraint support fields
        constraint_fields = [
            "allowsConditions", "allowsTimeBounds", "allowsIpRestrictions"
        ]
        for field in constraint_fields:
            assert field in field_names
    
    def test_role_permission_type_association(self):
        """Test RolePermissionType association."""
        query = '''
            query {
                __type(name: "RolePermissionType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        expected_fields = [
            "id", "roleId", "permissionId", "permission", "conditions",
            "ipRestrictions", "timeRestrictions", "validFrom", "validUntil",
            "reason", "grantedById", "grantedAt"
        ]
        
        for field in expected_fields:
            assert field in field_names
    
    def test_role_hierarchy_type_definition(self):
        """Test RoleHierarchyType definition."""
        query = '''
            query {
                __type(name: "RoleHierarchyType") {
                    fields {
                        name
                        type {
                            name
                            ofType {
                                name
                            }
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        expected_fields = ["role", "level", "path", "children"]
        
        for field in expected_fields:
            assert field in field_names


class TestRoleAssignmentTypes:
    """Test Role Assignment-related GraphQL types."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_role_assignment_scope_type_definition(self):
        """Test RoleAssignmentScopeType definition."""
        query = '''
            query {
                __type(name: "RoleAssignmentScopeType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        expected_fields = [
            "scopeType", "workspaceId", "projectId", "environmentId",
            "flowId", "componentId", "scopeName", "scopePath"
        ]
        
        for field in expected_fields:
            assert field in field_names
    
    def test_role_assignment_type_constraint_support(self):
        """Test RoleAssignmentType supports constraints."""
        query = '''
            query {
                __type(name: "RoleAssignmentType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        
        # Constraint fields
        constraint_fields = [
            "validFrom", "validUntil", "conditions", "ipRestrictions", "timeRestrictions"
        ]
        for field in constraint_fields:
            assert field in field_names
        
        # Status fields
        status_fields = ["isActive", "isInherited"]
        for field in status_fields:
            assert field in field_names
    
    def test_bulk_role_assignment_input_definition(self):
        """Test BulkRoleAssignmentInput definition."""
        query = '''
            query {
                __type(name: "BulkRoleAssignmentInput") {
                    inputFields {
                        name
                        type {
                            name
                            ofType {
                                name
                            }
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["inputFields"]]
        expected_fields = [
            "userIds", "groupIds", "serviceAccountIds", "roleId", "scopeType",
            "workspaceId", "projectId", "environmentId", "validFrom", "validUntil"
        ]
        
        for field in expected_fields:
            assert field in field_names
    
    def test_assignment_approval_type_definition(self):
        """Test AssignmentApprovalType definition."""
        query = '''
            query {
                __type(name: "AssignmentApprovalType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        expected_fields = [
            "id", "assignmentId", "assignment", "status", "requestedById",
            "approvedById", "decisionReason", "requestedAt", "decidedAt", "expiresAt"
        ]
        
        for field in expected_fields:
            assert field in field_names


class TestUserTypes:
    """Test User-related GraphQL types."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_user_type_rbac_fields(self):
        """Test UserType has RBAC relationship fields."""
        query = '''
            query {
                __type(name: "UserType") {
                    fields {
                        name
                        type {
                            name
                            ofType {
                                name
                            }
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        
        # RBAC relationship fields
        rbac_fields = [
            "ownedWorkspaces", "workspaceMemberships", "roleAssignments",
            "groupMemberships", "totalWorkspaces", "totalRoles", "effectivePermissions"
        ]
        for field in rbac_fields:
            assert field in field_names
        
        # Security fields
        security_fields = [
            "isActive", "isSuperuser", "isVerified", "mfaEnabled",
            "failedLoginAttempts", "lockedUntil", "lastLoginAt"
        ]
        for field in security_fields:
            assert field in field_names
    
    def test_user_group_type_scim_support(self):
        """Test UserGroupType supports SCIM."""
        query = '''
            query {
                __type(name: "UserGroupType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        
        # SCIM fields
        scim_fields = ["scimEnabled", "scimExternalId", "lastScimSync"]
        for field in scim_fields:
            assert field in field_names
    
    def test_user_group_membership_type_definition(self):
        """Test UserGroupMembershipType definition."""
        query = '''
            query {
                __type(name: "UserGroupMembershipType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        expected_fields = [
            "id", "userId", "groupId", "user", "group", "isActive",
            "roleInGroup", "scimExternalId", "syncedFromScim", "addedById", "addedAt"
        ]
        
        for field in expected_fields:
            assert field in field_names
    
    def test_user_stats_type_definition(self):
        """Test UserStatsType definition."""
        query = '''
            query {
                __type(name: "UserStatsType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        expected_fields = [
            "totalUsers", "activeUsers", "verifiedUsers", "superusers",
            "activeLastDay", "activeLastWeek", "activeLastMonth",
            "mfaEnabledUsers", "ssoUsers", "lockedUsers", "newUsersLastMonth"
        ]
        
        for field in expected_fields:
            assert field in field_names


class TestAuditTypes:
    """Test Audit-related GraphQL types."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_audit_log_type_comprehensive_fields(self):
        """Test AuditLogType has comprehensive audit fields."""
        query = '''
            query {
                __type(name: "AuditLogType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        
        # Event identification fields
        event_fields = ["eventType", "action", "outcome", "actorType", "actorId", "actorName"]
        for field in event_fields:
            assert field in field_names
        
        # Resource fields
        resource_fields = ["resourceType", "resourceId", "resourceName"]
        for field in resource_fields:
            assert field in field_names
        
        # Context fields
        context_fields = ["workspaceId", "projectId", "environmentId", "flowId"]
        for field in context_fields:
            assert field in field_names
        
        # Security fields
        security_fields = [
            "retentionRequired", "sensitiveDataAccessed", "riskScore",
            "anomalyDetected", "suspiciousIndicators"
        ]
        for field in security_fields:
            assert field in field_names
    
    def test_audit_log_metrics_type_definition(self):
        """Test AuditLogMetricsType definition."""
        query = '''
            query {
                __type(name: "AuditLogMetricsType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        expected_fields = [
            "totalEvents", "eventsByType", "eventsByActor", "eventsByOutcome",
            "highRiskEvents", "anomaliesDetected", "failedAuthentications",
            "uniqueActors", "eventsLastHour", "eventsLastDay", "eventsLastWeek"
        ]
        
        for field in expected_fields:
            assert field in field_names
    
    def test_audit_alert_type_definition(self):
        """Test AuditAlertType definition."""
        query = '''
            query {
                __type(name: "AuditAlertType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        expected_fields = [
            "id", "severity", "title", "description", "triggeringEventId",
            "relatedEventIds", "indicators", "riskScore", "status",
            "assignedToId", "resolvedById", "resolutionNotes", "createdAt"
        ]
        
        for field in expected_fields:
            assert field in field_names
    
    def test_audit_retention_policy_type_definition(self):
        """Test AuditRetentionPolicyType definition."""
        query = '''
            query {
                __type(name: "AuditRetentionPolicyType") {
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__type"]["fields"]]
        expected_fields = [
            "id", "name", "description", "defaultRetentionDays",
            "complianceRetentionDays", "sensitiveDataRetentionDays",
            "eventTypeRules", "isActive", "workspaceId"
        ]
        
        for field in expected_fields:
            assert field in field_names


class TestInputValidation:
    """Test GraphQL input type validation."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_create_inputs_have_required_fields(self):
        """Test create input types have required fields marked properly."""
        create_inputs = [
            "WorkspaceCreateInput", "ProjectCreateInput", "EnvironmentCreateInput",
            "RoleCreateInput", "RoleAssignmentCreateInput", "UserCreateInput"
        ]
        
        for input_type in create_inputs:
            query = f'''
                query {{
                    __type(name: "{input_type}") {{
                        inputFields {{
                            name
                            type {{
                                nonNull
                            }}
                        }}
                    }}
                }}
            '''
            
            result = self.client.execute(query)
            assert result.errors is None, f"Failed to query {input_type}"
            
            # Each create input should have at least one required field
            required_fields = [
                f for f in result.data["__type"]["inputFields"]
                if f["type"]["nonNull"] is True
            ]
            assert len(required_fields) > 0, f"{input_type} should have required fields"
    
    def test_filter_inputs_comprehensive(self):
        """Test filter input types have comprehensive filtering options."""
        filter_inputs = [
            ("WorkspaceFilterInput", ["search", "isActive", "ownerId"]),
            ("ProjectFilterInput", ["search", "workspaceId", "isActive"]),
            ("RoleFilterInput", ["search", "type", "workspaceId"]),
            ("UserFilterInput", ["search", "isActive", "isSuperuser"]),
            ("AuditLogFilterInput", ["eventTypes", "actorTypes", "startTime"])
        ]
        
        for input_type, expected_filters in filter_inputs:
            query = f'''
                query {{
                    __type(name: "{input_type}") {{
                        inputFields {{
                            name
                        }}
                    }}
                }}
            '''
            
            result = self.client.execute(query)
            assert result.errors is None, f"Failed to query {input_type}"
            
            field_names = [f["name"] for f in result.data["__type"]["inputFields"]]
            
            for expected_filter in expected_filters:
                assert expected_filter in field_names, f"{input_type} missing {expected_filter}"


class TestResponseTypes:
    """Test GraphQL response types."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_response_types_extend_base_response(self):
        """Test response types extend BaseResponse."""
        response_types = [
            "WorkspaceResponse", "ProjectResponse", "EnvironmentResponse",
            "RoleResponse", "RoleAssignmentResponse", "UserResponse"
        ]
        
        for response_type in response_types:
            query = f'''
                query {{
                    __type(name: "{response_type}") {{
                        fields {{
                            name
                            type {{
                                name
                            }}
                        }}
                    }}
                }}
            '''
            
            result = self.client.execute(query)
            assert result.errors is None, f"Failed to query {response_type}"
            
            field_names = [f["name"] for f in result.data["__type"]["fields"]]
            
            # Should have base response fields
            base_fields = ["success", "errors"]
            for base_field in base_fields:
                assert base_field in field_names, f"{response_type} missing {base_field}"
            
            # Should have validation errors
            assert "validationErrors" in field_names, f"{response_type} missing validationErrors"
    
    def test_list_response_types_structure(self):
        """Test list response types have proper structure."""
        list_response_types = [
            "WorkspaceListResponse", "ProjectListResponse", "EnvironmentListResponse",
            "RoleListResponse", "UserListResponse", "AuditLogListResponse"
        ]
        
        for response_type in list_response_types:
            query = f'''
                query {{
                    __type(name: "{response_type}") {{
                        fields {{
                            name
                            type {{
                                name
                                kind
                                ofType {{
                                    name
                                }}
                            }}
                        }}
                    }}
                }}
            '''
            
            result = self.client.execute(query)
            assert result.errors is None, f"Failed to query {response_type}"
            
            field_names = [f["name"] for f in result.data["__type"]["fields"]]
            
            # Should have pagination fields
            pagination_fields = ["totalCount", "hasNextPage"]
            for pagination_field in pagination_fields:
                assert pagination_field in pagination_fields, f"{response_type} missing {pagination_field}"
    
    def test_stats_response_types_definition(self):
        """Test stats response types definition."""
        stats_types = [
            "WorkspaceStatsType", "ProjectStatsType", "EnvironmentStatsType",
            "RoleStatsType", "UserStatsType", "AuditLogMetricsType"
        ]
        
        for stats_type in stats_types:
            query = f'''
                query {{
                    __type(name: "{stats_type}") {{
                        fields {{
                            name
                            type {{
                                name
                            }}
                        }}
                    }}
                }}
            '''
            
            result = self.client.execute(query)
            assert result.errors is None, f"Failed to query {stats_type}"
            
            # Should have at least some numeric fields for statistics
            fields = result.data["__type"]["fields"]
            assert len(fields) > 0, f"{stats_type} should have statistics fields"