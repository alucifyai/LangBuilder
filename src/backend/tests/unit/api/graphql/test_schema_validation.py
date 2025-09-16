"""Tests for GraphQL schema validation and type definitions."""

import pytest
import uuid
from datetime import datetime, timezone
from graphene.test import Client
from graphene import Schema

from langflow.api.graphql.schema import schema
from langflow.api.graphql.types.common import (
    UUID, DateTime, ScopeTypeEnum, AssignmentTypeEnum, RoleTypeEnum,
    PermissionActionEnum, ResourceTypeEnum, AuditEventTypeEnum
)


class TestGraphQLSchemaValidation:
    """Test GraphQL schema validation and introspection."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_schema_is_valid(self):
        """Test that the GraphQL schema is valid."""
        assert isinstance(schema, Schema)
        assert schema.query is not None
        assert schema.mutation is not None
    
    def test_schema_introspection(self):
        """Test schema introspection query."""
        query = '''
            query {
                __schema {
                    types {
                        name
                        kind
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        assert result.data is not None
        assert "__schema" in result.data
        assert "types" in result.data["__schema"]
        
        # Check that our types are in the schema
        type_names = [t["name"] for t in result.data["__schema"]["types"]]
        expected_types = [
            "WorkspaceType", "ProjectType", "EnvironmentType", "RoleType",
            "PermissionType", "RoleAssignmentType", "UserType", "AuditLogType"
        ]
        
        for expected_type in expected_types:
            assert expected_type in type_names
    
    def test_query_type_fields(self):
        """Test that Query type has expected fields."""
        query = '''
            query {
                __schema {
                    queryType {
                        fields {
                            name
                            type {
                                name
                            }
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__schema"]["queryType"]["fields"]]
        expected_fields = [
            "workspace", "workspaces", "project", "projects", "environment",
            "environments", "role", "roles", "user", "users", "auditLogs",
            "checkPermission"
        ]
        
        for expected_field in expected_fields:
            assert expected_field in field_names
    
    def test_mutation_type_fields(self):
        """Test that Mutation type has expected fields."""
        query = '''
            query {
                __schema {
                    mutationType {
                        fields {
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        field_names = [f["name"] for f in result.data["__schema"]["mutationType"]["fields"]]
        expected_mutations = [
            "createWorkspace", "updateWorkspace", "createProject", "createRole",
            "createRoleAssignment", "createUser", "exportAuditLogs"
        ]
        
        for expected_mutation in expected_mutations:
            assert expected_mutation in field_names


class TestCustomScalarTypes:
    """Test custom scalar types."""
    
    def test_uuid_scalar_serialization(self):
        """Test UUID scalar serialization."""
        test_uuid = uuid.uuid4()
        
        # Test with UUID object
        serialized = UUID.serialize(test_uuid)
        assert serialized == str(test_uuid)
        
        # Test with string
        uuid_str = str(test_uuid)
        serialized = UUID.serialize(uuid_str)
        assert serialized == uuid_str
    
    def test_uuid_scalar_parsing(self):
        """Test UUID scalar parsing."""
        test_uuid = uuid.uuid4()
        uuid_str = str(test_uuid)
        
        # Test parse_value
        parsed = UUID.parse_value(uuid_str)
        assert isinstance(parsed, uuid.UUID)
        assert parsed == test_uuid
        
        # Test invalid UUID
        with pytest.raises(ValueError):
            UUID.parse_value("invalid-uuid")
    
    def test_datetime_scalar_serialization(self):
        """Test DateTime scalar serialization."""
        now = datetime.now(timezone.utc)
        
        serialized = DateTime.serialize(now)
        assert isinstance(serialized, str)
        assert "T" in serialized  # ISO format


class TestEnumTypes:
    """Test GraphQL enum types."""
    
    def test_scope_type_enum_values(self):
        """Test ScopeTypeEnum has correct values."""
        expected_values = ["workspace", "project", "environment", "flow", "component"]
        
        # This tests that enum is properly defined
        assert hasattr(ScopeTypeEnum, "WORKSPACE")
        assert hasattr(ScopeTypeEnum, "PROJECT")
        assert hasattr(ScopeTypeEnum, "ENVIRONMENT")
        assert hasattr(ScopeTypeEnum, "FLOW")
        assert hasattr(ScopeTypeEnum, "COMPONENT")
    
    def test_assignment_type_enum_values(self):
        """Test AssignmentTypeEnum has correct values."""
        assert hasattr(AssignmentTypeEnum, "USER")
        assert hasattr(AssignmentTypeEnum, "GROUP")
        assert hasattr(AssignmentTypeEnum, "SERVICE_ACCOUNT")
    
    def test_role_type_enum_values(self):
        """Test RoleTypeEnum has correct values."""
        assert hasattr(RoleTypeEnum, "SYSTEM")
        assert hasattr(RoleTypeEnum, "CUSTOM")
    
    def test_permission_action_enum_values(self):
        """Test PermissionActionEnum has correct values."""
        expected_actions = [
            "CREATE", "READ", "UPDATE", "DELETE", "EXECUTE", "DEPLOY",
            "EXPORT", "IMPORT", "SHARE", "PUBLISH", "MANAGE", "GRANT",
            "REVOKE", "IMPERSONATE", "BREAK_GLASS"
        ]
        
        for action in expected_actions:
            assert hasattr(PermissionActionEnum, action)
    
    def test_resource_type_enum_values(self):
        """Test ResourceTypeEnum has correct values."""
        expected_resources = [
            "WORKSPACE", "PROJECT", "ENVIRONMENT", "FLOW", "COMPONENT",
            "USER", "ROLE", "SERVICE_ACCOUNT", "AUDIT", "SYSTEM"
        ]
        
        for resource in expected_resources:
            assert hasattr(ResourceTypeEnum, resource)
    
    def test_audit_event_type_enum_values(self):
        """Test AuditEventTypeEnum has correct values."""
        expected_events = [
            "LOGIN", "LOGOUT", "LOGIN_FAILED", "PASSWORD_CHANGE",
            "PERMISSION_GRANTED", "PERMISSION_REVOKED", "ACCESS_DENIED",
            "RESOURCE_CREATED", "RESOURCE_UPDATED", "RESOURCE_DELETED"
        ]
        
        for event in expected_events:
            assert hasattr(AuditEventTypeEnum, event)


class TestTypeDefinitions:
    """Test GraphQL type definitions."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_workspace_type_definition(self):
        """Test WorkspaceType definition."""
        query = '''
            query {
                __type(name: "WorkspaceType") {
                    name
                    kind
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
        
        workspace_type = result.data["__type"]
        assert workspace_type["name"] == "WorkspaceType"
        assert workspace_type["kind"] == "OBJECT"
        
        field_names = [f["name"] for f in workspace_type["fields"]]
        expected_fields = [
            "id", "name", "description", "organization", "isActive",
            "settings", "metadata", "tags", "ownerId", "totalProjects",
            "totalUsers", "createdAt", "updatedAt"
        ]
        
        for expected_field in expected_fields:
            assert expected_field in field_names
    
    def test_role_type_definition(self):
        """Test RoleType definition."""
        query = '''
            query {
                __type(name: "RoleType") {
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
        
        role_type = result.data["__type"]
        field_names = [f["name"] for f in role_type["fields"]]
        expected_fields = [
            "id", "name", "description", "type", "priority", "isSystem",
            "parentRoleId", "workspaceId", "permissions", "totalAssignments",
            "effectivePermissions", "createdAt", "updatedAt"
        ]
        
        for expected_field in expected_fields:
            assert expected_field in field_names
    
    def test_permission_type_definition(self):
        """Test PermissionType definition."""
        query = '''
            query {
                __type(name: "PermissionType") {
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
        
        permission_type = result.data["__type"]
        field_names = [f["name"] for f in permission_type["fields"]]
        expected_fields = [
            "id", "name", "description", "resourceType", "action",
            "allowsConditions", "allowsTimeBounds", "allowsIpRestrictions",
            "isSystem", "createdAt"
        ]
        
        for expected_field in expected_fields:
            assert expected_field in field_names
    
    def test_role_assignment_type_definition(self):
        """Test RoleAssignmentType definition."""
        query = '''
            query {
                __type(name: "RoleAssignmentType") {
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
        
        assignment_type = result.data["__type"]
        field_names = [f["name"] for f in assignment_type["fields"]]
        expected_fields = [
            "id", "assignmentType", "userId", "groupId", "serviceAccountId",
            "roleId", "scope", "isActive", "isInherited", "validFrom",
            "validUntil", "conditions", "reason", "assignedAt"
        ]
        
        for expected_field in expected_fields:
            assert expected_field in field_names
    
    def test_user_type_definition(self):
        """Test UserType definition."""
        query = '''
            query {
                __type(name: "UserType") {
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
        
        user_type = result.data["__type"]
        field_names = [f["name"] for f in user_type["fields"]]
        expected_fields = [
            "id", "username", "email", "firstName", "lastName", "displayName",
            "isActive", "isSuperuser", "isVerified", "lastLoginAt",
            "roleAssignments", "groupMemberships", "totalWorkspaces",
            "totalRoles", "effectivePermissions", "createdAt", "updatedAt"
        ]
        
        for expected_field in expected_fields:
            assert expected_field in field_names
    
    def test_audit_log_type_definition(self):
        """Test AuditLogType definition."""
        query = '''
            query {
                __type(name: "AuditLogType") {
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
        
        audit_type = result.data["__type"]
        field_names = [f["name"] for f in audit_type["fields"]]
        expected_fields = [
            "id", "eventType", "action", "outcome", "actorType", "actorId",
            "actorName", "resourceType", "resourceId", "workspaceId",
            "sessionId", "ipAddress", "details", "metadata", "retentionRequired",
            "sensitiveDataAccessed", "riskScore", "timestamp"
        ]
        
        for expected_field in expected_fields:
            assert expected_field in field_names


class TestInputTypes:
    """Test GraphQL input types."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_workspace_create_input_definition(self):
        """Test WorkspaceCreateInput definition."""
        query = '''
            query {
                __type(name: "WorkspaceCreateInput") {
                    name
                    kind
                    inputFields {
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
        
        input_type = result.data["__type"]
        assert input_type["name"] == "WorkspaceCreateInput"
        assert input_type["kind"] == "INPUT_OBJECT"
        
        field_names = [f["name"] for f in input_type["inputFields"]]
        expected_fields = ["name", "description", "organization", "settings", "metadata", "tags"]
        
        for expected_field in expected_fields:
            assert expected_field in field_names
    
    def test_role_create_input_definition(self):
        """Test RoleCreateInput definition."""
        query = '''
            query {
                __type(name: "RoleCreateInput") {
                    name
                    inputFields {
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
        
        input_type = result.data["__type"]
        field_names = [f["name"] for f in input_type["inputFields"]]
        expected_fields = ["name", "description", "workspaceId", "parentRoleId", "priority", "metadata", "tags"]
        
        for expected_field in expected_fields:
            assert expected_field in field_names
    
    def test_role_assignment_create_input_definition(self):
        """Test RoleAssignmentCreateInput definition."""
        query = '''
            query {
                __type(name: "RoleAssignmentCreateInput") {
                    name
                    inputFields {
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
        
        input_type = result.data["__type"]
        field_names = [f["name"] for f in input_type["inputFields"]]
        expected_fields = [
            "userId", "groupId", "serviceAccountId", "roleId", "scopeType",
            "workspaceId", "projectId", "environmentId", "flowId", "reason"
        ]
        
        for expected_field in expected_fields:
            assert expected_field in field_names


class TestResponseTypes:
    """Test GraphQL response types."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_workspace_response_definition(self):
        """Test WorkspaceResponse definition."""
        query = '''
            query {
                __type(name: "WorkspaceResponse") {
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
        
        response_type = result.data["__type"]
        field_names = [f["name"] for f in response_type["fields"]]
        expected_fields = ["success", "errors", "workspace", "validationErrors"]
        
        for expected_field in expected_fields:
            assert expected_field in field_names
    
    def test_workspace_list_response_definition(self):
        """Test WorkspaceListResponse definition."""
        query = '''
            query {
                __type(name: "WorkspaceListResponse") {
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
        
        response_type = result.data["__type"]
        field_names = [f["name"] for f in response_type["fields"]]
        expected_fields = ["workspaces", "totalCount", "hasNextPage"]
        
        for expected_field in expected_fields:
            assert expected_field in field_names


class TestFilterTypes:
    """Test GraphQL filter input types."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_workspace_filter_input_definition(self):
        """Test WorkspaceFilterInput definition."""
        query = '''
            query {
                __type(name: "WorkspaceFilterInput") {
                    name
                    inputFields {
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
        
        filter_type = result.data["__type"]
        field_names = [f["name"] for f in filter_type["inputFields"]]
        expected_fields = [
            "search", "organization", "isActive", "ownerId", "tags",
            "createdAfter", "createdBefore"
        ]
        
        for expected_field in expected_fields:
            assert expected_field in field_names
    
    def test_role_filter_input_definition(self):
        """Test RoleFilterInput definition."""
        query = '''
            query {
                __type(name: "RoleFilterInput") {
                    name
                    inputFields {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        filter_type = result.data["__type"]
        field_names = [f["name"] for f in filter_type["inputFields"]]
        expected_fields = [
            "search", "type", "workspaceId", "isActive", "hasPermissions",
            "tags", "createdAfter", "createdBefore"
        ]
        
        for expected_field in expected_fields:
            assert expected_field in field_names
    
    def test_audit_log_filter_input_definition(self):
        """Test AuditLogFilterInput definition."""
        query = '''
            query {
                __type(name: "AuditLogFilterInput") {
                    name
                    inputFields {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        filter_type = result.data["__type"]
        field_names = [f["name"] for f in filter_type["inputFields"]]
        expected_fields = [
            "eventTypes", "actions", "outcomes", "actorTypes", "actorIds",
            "resourceTypes", "workspaceIds", "startTime", "endTime", "search"
        ]
        
        for expected_field in expected_fields:
            assert expected_field in field_names


@pytest.mark.integration
class TestSchemaIntegration:
    """Test GraphQL schema integration with real queries."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_schema_generates_valid_sdl(self):
        """Test that schema can generate valid SDL."""
        from graphene.utils.schema_printer import print_schema
        
        schema_sdl = print_schema(schema)
        assert isinstance(schema_sdl, str)
        assert len(schema_sdl) > 0
        assert "type Query" in schema_sdl
        assert "type Mutation" in schema_sdl
        assert "type WorkspaceType" in schema_sdl
    
    def test_complex_introspection_query(self):
        """Test complex introspection query."""
        query = '''
            query {
                __schema {
                    queryType {
                        name
                        fields {
                            name
                            args {
                                name
                                type {
                                    name
                                    kind
                                }
                            }
                            type {
                                name
                                kind
                                ofType {
                                    name
                                    kind
                                }
                            }
                        }
                    }
                    mutationType {
                        name
                        fields {
                            name
                            args {
                                name
                                type {
                                    name
                                    kind
                                }
                            }
                        }
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        assert result.data is not None
        
        query_type = result.data["__schema"]["queryType"]
        mutation_type = result.data["__schema"]["mutationType"]
        
        assert query_type["name"] == "Query"
        assert mutation_type["name"] == "Mutation"
        
        # Check that queries have arguments
        workspace_query = next(
            (f for f in query_type["fields"] if f["name"] == "workspace"), None
        )
        assert workspace_query is not None
        assert len(workspace_query["args"]) > 0
        
        # Check that mutations have arguments
        create_workspace = next(
            (f for f in mutation_type["fields"] if f["name"] == "createWorkspace"), None
        )
        assert create_workspace is not None
        assert len(create_workspace["args"]) > 0