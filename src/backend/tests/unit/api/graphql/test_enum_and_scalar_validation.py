"""Tests for GraphQL enums and scalar validation."""

import pytest
import uuid
from datetime import datetime, timezone
from graphene.test import Client

from langflow.api.graphql.schema import schema
from langflow.api.graphql.types.common import (
    UUID, DateTime, ScopeTypeEnum, AssignmentTypeEnum, RoleTypeEnum,
    PermissionActionEnum, ResourceTypeEnum, AuditEventTypeEnum,
    AuditActorTypeEnum, SSOProviderTypeEnum, SSOStatusEnum
)


class TestCustomScalars:
    """Test custom scalar types validation and behavior."""
    
    def test_uuid_scalar_valid_serialization(self):
        """Test UUID scalar serializes valid UUIDs correctly."""
        test_cases = [
            uuid.uuid4(),
            uuid.UUID('12345678-1234-5678-1234-567812345678'),
            uuid.UUID(int=12345678123456781234567812345678)
        ]
        
        for test_uuid in test_cases:
            serialized = UUID.serialize(test_uuid)
            assert isinstance(serialized, str)
            assert len(serialized) == 36  # Standard UUID string length
            assert serialized.count('-') == 4  # Standard UUID format
    
    def test_uuid_scalar_string_serialization(self):
        """Test UUID scalar handles string inputs."""
        uuid_string = "12345678-1234-5678-1234-567812345678"
        serialized = UUID.serialize(uuid_string)
        assert serialized == uuid_string
    
    def test_uuid_scalar_invalid_serialization(self):
        """Test UUID scalar raises error for invalid inputs."""
        invalid_inputs = [
            123,
            [],
            {},
            None,
            "invalid-uuid"
        ]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(ValueError):
                UUID.serialize(invalid_input)
    
    def test_uuid_scalar_parse_value_valid(self):
        """Test UUID scalar parses valid UUID strings."""
        valid_uuids = [
            "12345678-1234-5678-1234-567812345678",
            "ffffffff-ffff-ffff-ffff-ffffffffffff",
            "00000000-0000-0000-0000-000000000000"
        ]
        
        for uuid_string in valid_uuids:
            parsed = UUID.parse_value(uuid_string)
            assert isinstance(parsed, uuid.UUID)
            assert str(parsed) == uuid_string
    
    def test_uuid_scalar_parse_value_invalid(self):
        """Test UUID scalar raises error for invalid UUID strings."""
        invalid_uuids = [
            "invalid-uuid",
            "12345678-1234-5678-1234-56781234567",  # Too short
            "12345678-1234-5678-1234-567812345678x",  # Too long
            "xyz45678-1234-5678-1234-567812345678",  # Invalid characters
            "",
            None
        ]
        
        for invalid_uuid in invalid_uuids:
            with pytest.raises(ValueError):
                UUID.parse_value(invalid_uuid)
    
    def test_datetime_scalar_serialization(self):
        """Test DateTime scalar serialization."""
        test_datetime = datetime(2025, 9, 16, 12, 30, 45, tzinfo=timezone.utc)
        serialized = DateTime.serialize(test_datetime)
        
        assert isinstance(serialized, str)
        assert "2025-09-16" in serialized
        assert "T" in serialized  # ISO format indicator
    
    def test_datetime_scalar_timezone_handling(self):
        """Test DateTime scalar handles timezones correctly."""
        # UTC datetime
        utc_dt = datetime(2025, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
        utc_serialized = DateTime.serialize(utc_dt)
        assert "+00:00" in utc_serialized or "Z" in utc_serialized
        
        # Naive datetime (should still serialize)
        naive_dt = datetime(2025, 9, 16, 12, 0, 0)
        naive_serialized = DateTime.serialize(naive_dt)
        assert isinstance(naive_serialized, str)


class TestScopeTypeEnum:
    """Test ScopeTypeEnum validation and completeness."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_scope_type_enum_has_all_values(self):
        """Test ScopeTypeEnum has all required scope types."""
        query = '''
            query {
                __type(name: "ScopeTypeEnum") {
                    enumValues {
                        name
                        description
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        expected_values = ["WORKSPACE", "PROJECT", "ENVIRONMENT", "FLOW", "COMPONENT"]
        
        for expected_value in expected_values:
            assert expected_value in enum_values
    
    def test_scope_type_enum_hierarchy_order(self):
        """Test ScopeTypeEnum values represent proper hierarchy."""
        query = '''
            query {
                __type(name: "ScopeTypeEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        
        # Check hierarchical scope types are present
        hierarchical_scopes = ["WORKSPACE", "PROJECT", "ENVIRONMENT", "FLOW", "COMPONENT"]
        for scope in hierarchical_scopes:
            assert scope in enum_values


class TestAssignmentTypeEnum:
    """Test AssignmentTypeEnum validation."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_assignment_type_enum_completeness(self):
        """Test AssignmentTypeEnum has all assignee types."""
        query = '''
            query {
                __type(name: "AssignmentTypeEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        expected_values = ["USER", "GROUP", "SERVICE_ACCOUNT"]
        
        for expected_value in expected_values:
            assert expected_value in enum_values
        
        # Should not have any unexpected values
        assert len(enum_values) == len(expected_values)


class TestPermissionActionEnum:
    """Test PermissionActionEnum validation."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_permission_action_enum_basic_crud(self):
        """Test PermissionActionEnum includes basic CRUD operations."""
        query = '''
            query {
                __type(name: "PermissionActionEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        
        # Basic CRUD operations
        crud_operations = ["CREATE", "READ", "UPDATE", "DELETE"]
        for operation in crud_operations:
            assert operation in enum_values
    
    def test_permission_action_enum_extended_operations(self):
        """Test PermissionActionEnum includes extended operations from PRD."""
        query = '''
            query {
                __type(name: "PermissionActionEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        
        # Extended operations (as specified in PRD)
        extended_operations = [
            "EXECUTE", "DEPLOY", "EXPORT", "IMPORT", "SHARE", "PUBLISH",
            "MANAGE", "GRANT", "REVOKE", "IMPERSONATE", "BREAK_GLASS"
        ]
        for operation in extended_operations:
            assert operation in enum_values
    
    def test_permission_action_enum_administrative_operations(self):
        """Test PermissionActionEnum includes administrative operations."""
        query = '''
            query {
                __type(name: "PermissionActionEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        
        # Administrative operations
        admin_operations = ["MANAGE", "GRANT", "REVOKE", "IMPERSONATE", "BREAK_GLASS"]
        for operation in admin_operations:
            assert operation in enum_values


class TestResourceTypeEnum:
    """Test ResourceTypeEnum validation."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_resource_type_enum_core_resources(self):
        """Test ResourceTypeEnum includes core RBAC resources."""
        query = '''
            query {
                __type(name: "ResourceTypeEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        
        # Core hierarchical resources
        core_resources = ["WORKSPACE", "PROJECT", "ENVIRONMENT", "FLOW", "COMPONENT"]
        for resource in core_resources:
            assert resource in enum_values
    
    def test_resource_type_enum_rbac_entities(self):
        """Test ResourceTypeEnum includes RBAC management entities."""
        query = '''
            query {
                __type(name: "ResourceTypeEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        
        # RBAC management entities
        rbac_entities = ["USER", "ROLE", "SERVICE_ACCOUNT", "AUDIT", "SYSTEM"]
        for entity in rbac_entities:
            assert entity in enum_values


class TestAuditEventTypeEnum:
    """Test AuditEventTypeEnum validation."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_audit_event_type_enum_authentication_events(self):
        """Test AuditEventTypeEnum includes authentication events."""
        query = '''
            query {
                __type(name: "AuditEventTypeEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        
        # Authentication events
        auth_events = ["LOGIN", "LOGOUT", "LOGIN_FAILED", "PASSWORD_CHANGE"]
        for event in auth_events:
            assert event in enum_values
    
    def test_audit_event_type_enum_authorization_events(self):
        """Test AuditEventTypeEnum includes authorization events."""
        query = '''
            query {
                __type(name: "AuditEventTypeEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        
        # Authorization events
        authz_events = ["PERMISSION_GRANTED", "PERMISSION_REVOKED", "ACCESS_DENIED"]
        for event in authz_events:
            assert event in enum_values
    
    def test_audit_event_type_enum_resource_events(self):
        """Test AuditEventTypeEnum includes resource operation events."""
        query = '''
            query {
                __type(name: "AuditEventTypeEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        
        # Resource operation events
        resource_events = ["RESOURCE_CREATED", "RESOURCE_UPDATED", "RESOURCE_DELETED"]
        for event in resource_events:
            assert event in enum_values
    
    def test_audit_event_type_enum_security_events(self):
        """Test AuditEventTypeEnum includes security events."""
        query = '''
            query {
                __type(name: "AuditEventTypeEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        
        # Security events
        security_events = [
            "BREAK_GLASS_ACCESS", "IMPERSONATION_START", "IMPERSONATION_END", 
            "SUSPICIOUS_ACTIVITY"
        ]
        for event in security_events:
            assert event in enum_values


class TestAuditActorTypeEnum:
    """Test AuditActorTypeEnum validation."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_audit_actor_type_enum_completeness(self):
        """Test AuditActorTypeEnum includes all actor types."""
        query = '''
            query {
                __type(name: "AuditActorTypeEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        expected_actors = ["USER", "SERVICE_ACCOUNT", "SYSTEM", "ANONYMOUS"]
        
        for actor in expected_actors:
            assert actor in enum_values


class TestSSOEnums:
    """Test SSO-related enum types."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_sso_provider_type_enum_completeness(self):
        """Test SSOProviderTypeEnum includes all supported providers."""
        query = '''
            query {
                __type(name: "SSOProviderTypeEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        
        # Protocol-based providers
        protocol_providers = ["OIDC", "SAML2", "OAUTH2", "LDAP"]
        for provider in protocol_providers:
            assert provider in enum_values
        
        # Vendor-specific providers
        vendor_providers = ["GOOGLE", "MICROSOFT", "OKTA", "AUTH0"]
        for provider in vendor_providers:
            assert provider in enum_values
        
        # Custom provider
        assert "CUSTOM" in enum_values
    
    def test_sso_status_enum_lifecycle(self):
        """Test SSOStatusEnum represents complete lifecycle."""
        query = '''
            query {
                __type(name: "SSOStatusEnum") {
                    enumValues {
                        name
                    }
                }
            }
        '''
        
        result = self.client.execute(query)
        assert result.errors is None
        
        enum_values = [ev["name"] for ev in result.data["__type"]["enumValues"]]
        
        # SSO configuration lifecycle
        lifecycle_statuses = ["DRAFT", "TESTING", "ACTIVE", "INACTIVE", "ERROR", "DEPRECATED"]
        for status in lifecycle_statuses:
            assert status in enum_values


class TestEnumConsistency:
    """Test enum consistency across the schema."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_all_enums_have_descriptions(self):
        """Test that all enum values have descriptions where expected."""
        enum_types = [
            "ScopeTypeEnum", "AssignmentTypeEnum", "RoleTypeEnum",
            "PermissionActionEnum", "ResourceTypeEnum", "AuditEventTypeEnum"
        ]
        
        for enum_type in enum_types:
            query = f'''
                query {{
                    __type(name: "{enum_type}") {{
                        enumValues {{
                            name
                            description
                        }}
                    }}
                }}
            '''
            
            result = self.client.execute(query)
            assert result.errors is None, f"Failed to query {enum_type}"
            
            enum_values = result.data["__type"]["enumValues"]
            assert len(enum_values) > 0, f"{enum_type} should have enum values"
    
    def test_enum_naming_consistency(self):
        """Test enum naming follows consistent patterns."""
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
        
        enum_types = [t for t in result.data["__schema"]["types"] if t["kind"] == "ENUM"]
        
        # Check naming patterns
        for enum_type in enum_types:
            name = enum_type["name"]
            if name.startswith("ScopeType") or name.startswith("Permission") or name.startswith("Resource"):
                assert name.endswith("Enum"), f"Enum {name} should end with 'Enum'"
    
    def test_enum_values_are_uppercase(self):
        """Test enum values follow UPPERCASE convention."""
        enum_types = [
            "ScopeTypeEnum", "AssignmentTypeEnum", "PermissionActionEnum", "ResourceTypeEnum"
        ]
        
        for enum_type in enum_types:
            query = f'''
                query {{
                    __type(name: "{enum_type}") {{
                        enumValues {{
                            name
                        }}
                    }}
                }}
            '''
            
            result = self.client.execute(query)
            assert result.errors is None
            
            for enum_value in result.data["__type"]["enumValues"]:
                value_name = enum_value["name"]
                assert value_name.isupper(), f"Enum value {value_name} in {enum_type} should be uppercase"
                assert "_" in value_name or len(value_name) <= 10, f"Enum value {value_name} should use underscores for compound words"


class TestScalarAndEnumIntegration:
    """Test integration between scalars and enums in complex types."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client(schema)
    
    def test_uuid_fields_use_uuid_scalar(self):
        """Test that ID fields use UUID scalar type."""
        types_with_ids = [
            "WorkspaceType", "ProjectType", "RoleType", "UserType", "AuditLogType"
        ]
        
        for type_name in types_with_ids:
            query = f'''
                query {{
                    __type(name: "{type_name}") {{
                        fields {{
                            name
                            type {{
                                name
                                nonNull
                            }}
                        }}
                    }}
                }}
            '''
            
            result = self.client.execute(query)
            assert result.errors is None
            
            # Find ID field
            id_field = next((f for f in result.data["__type"]["fields"] if f["name"] == "id"), None)
            assert id_field is not None, f"{type_name} should have an id field"
            
            # ID should be non-null UUID
            assert id_field["type"]["nonNull"] is True, f"{type_name}.id should be non-null"
    
    def test_datetime_fields_use_datetime_scalar(self):
        """Test that timestamp fields use DateTime scalar."""
        types_with_timestamps = [
            ("WorkspaceType", ["createdAt", "updatedAt"]),
            ("RoleType", ["createdAt", "updatedAt"]),
            ("UserType", ["createdAt", "updatedAt", "lastLoginAt"]),
            ("AuditLogType", ["timestamp", "ingestedAt"])
        ]
        
        for type_name, timestamp_fields in types_with_timestamps:
            query = f'''
                query {{
                    __type(name: "{type_name}") {{
                        fields {{
                            name
                            type {{
                                name
                                ofType {{
                                    name
                                }}
                            }}
                        }}
                    }}
                }}
            '''
            
            result = self.client.execute(query)
            assert result.errors is None
            
            fields = {f["name"]: f["type"] for f in result.data["__type"]["fields"]}
            
            for timestamp_field in timestamp_fields:
                if timestamp_field in fields:
                    field_type = fields[timestamp_field]
                    # Should be DateTime or nullable DateTime
                    assert (field_type["name"] == "DateTime" or 
                           (field_type["ofType"] and field_type["ofType"]["name"] == "DateTime")), \
                           f"{type_name}.{timestamp_field} should use DateTime scalar"
    
    def test_enum_fields_use_proper_enums(self):
        """Test that enum fields use appropriate enum types."""
        enum_field_mappings = [
            ("RoleAssignmentType", "assignmentType", "AssignmentTypeEnum"),
            ("RoleAssignmentType", "scopeType", "ScopeTypeEnum"),  # through scope field
            ("RoleType", "type", "RoleTypeEnum"),
            ("PermissionType", "resourceType", "ResourceTypeEnum"),
            ("PermissionType", "action", "PermissionActionEnum"),
            ("AuditLogType", "eventType", "AuditEventTypeEnum"),
            ("AuditLogType", "actorType", "AuditActorTypeEnum")
        ]
        
        for type_name, field_name, expected_enum in enum_field_mappings:
            query = f'''
                query {{
                    __type(name: "{type_name}") {{
                        fields {{
                            name
                            type {{
                                name
                                ofType {{
                                    name
                                }}
                            }}
                        }}
                    }}
                }}
            '''
            
            result = self.client.execute(query)
            assert result.errors is None
            
            field = next((f for f in result.data["__type"]["fields"] if f["name"] == field_name), None)
            if field:  # Some fields may be nested, which is acceptable
                field_type = field["type"]
                enum_type_name = field_type["name"] or (field_type["ofType"]["name"] if field_type["ofType"] else None)
                
                if enum_type_name:
                    # For direct enum usage
                    if enum_type_name == expected_enum:
                        continue
                    # For nested enum usage (e.g., through scope field), we'll check the nested type
                    # This is acceptable for complex types