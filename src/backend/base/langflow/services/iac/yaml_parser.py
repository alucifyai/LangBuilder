"""
Infrastructure-as-Code (IaC) YAML Parser
Parses YAML definitions for roles and grants
"""

from typing import Any

import yaml
from pydantic import BaseModel, Field, validator


class YAMLRoleDefinition(BaseModel):
    """YAML role definition schema"""

    name: str
    description: str | None = None
    permissions: list[str] = Field(default_factory=list)
    allowed_scopes: list[str] | None = None
    metadata: dict[str, Any] | None = None


class YAMLScopeDefinition(BaseModel):
    """YAML scope definition"""

    workspace: str | None = None
    project: str | None = None
    environment: str | None = None
    flow: str | None = None
    component: str | None = None

    @validator("*", pre=True, always=True)
    def validate_exactly_one_scope(cls, v, values, field):
        """Ensure exactly one scope type is specified"""
        non_none_count = sum(1 for val in values.values() if val is not None)
        if v is not None:
            non_none_count += 1
        if non_none_count > 1:
            msg = "Only one scope type can be specified"
            raise ValueError(msg)
        return v

    def to_scope_tuple(self) -> tuple[str, str]:
        """Convert to (scope_type, scope_id) tuple"""
        if self.workspace:
            return ("Workspace", self.workspace)
        if self.project:
            return ("Project", self.project)
        if self.environment:
            return ("Environment", self.environment)
        if self.flow:
            return ("Flow", self.flow)
        if self.component:
            return ("Component", self.component)
        msg = "At least one scope must be specified"
        raise ValueError(msg)


class YAMLGrantDefinition(BaseModel):
    """YAML grant/binding definition schema"""

    principal: str  # Format: "user:email" or "group:name" or "service_account:id"
    role: str  # Role name
    scope: YAMLScopeDefinition
    expires_at: str | None = None  # ISO 8601 datetime string
    justification: str | None = None

    def parse_principal(self) -> tuple[str, str]:
        """Parse principal into (type, id)"""
        parts = self.principal.split(":", 1)
        if len(parts) != 2:
            msg = f"Invalid principal format: {self.principal}. Expected 'type:id'"
            raise ValueError(msg)

        principal_type, principal_id = parts
        if principal_type not in ("user", "group", "service_account"):
            msg = f"Invalid principal type: {principal_type}"
            raise ValueError(msg)

        return (principal_type, principal_id)


class YAMLPolicyDefinition(BaseModel):
    """
    Complete YAML policy definition
    Supports both roles and grants in a single file
    """

    version: str = "v1"  # Policy schema version
    roles: list[YAMLRoleDefinition] = Field(default_factory=list)
    grants: list[YAMLGrantDefinition] = Field(default_factory=list)


def parse_yaml_policy(yaml_content: str) -> YAMLPolicyDefinition:
    """
    Parse YAML policy file
    Returns validated policy definition
    """
    try:
        data = yaml.safe_load(yaml_content)
        return YAMLPolicyDefinition(**data)
    except yaml.YAMLError as e:
        msg = f"Invalid YAML syntax: {e}"
        raise ValueError(msg) from e
    except Exception as e:
        msg = f"Invalid policy format: {e}"
        raise ValueError(msg) from e


def parse_yaml_roles(yaml_content: str) -> list[YAMLRoleDefinition]:
    """
    Parse roles-only YAML file
    Legacy format support
    """
    try:
        data = yaml.safe_load(yaml_content)

        # Support both:
        # 1. { roles: [...] }
        # 2. [ ... ] (list of roles directly)
        if isinstance(data, dict) and "roles" in data:
            roles_data = data["roles"]
        elif isinstance(data, list):
            roles_data = data
        else:
            msg = "YAML must contain 'roles' key or be a list of roles"
            raise ValueError(msg)

        return [YAMLRoleDefinition(**role) for role in roles_data]
    except yaml.YAMLError as e:
        msg = f"Invalid YAML syntax: {e}"
        raise ValueError(msg) from e
    except Exception as e:
        msg = f"Invalid roles format: {e}"
        raise ValueError(msg) from e


def parse_yaml_grants(yaml_content: str) -> list[YAMLGrantDefinition]:
    """
    Parse grants-only YAML file
    Legacy format support
    """
    try:
        data = yaml.safe_load(yaml_content)

        # Support both:
        # 1. { grants: [...] }
        # 2. [ ... ] (list of grants directly)
        if isinstance(data, dict) and "grants" in data:
            grants_data = data["grants"]
        elif isinstance(data, list):
            grants_data = data
        else:
            msg = "YAML must contain 'grants' key or be a list of grants"
            raise ValueError(msg)

        return [YAMLGrantDefinition(**grant) for grant in grants_data]
    except yaml.YAMLError as e:
        msg = f"Invalid YAML syntax: {e}"
        raise ValueError(msg) from e
    except Exception as e:
        msg = f"Invalid grants format: {e}"
        raise ValueError(msg) from e
