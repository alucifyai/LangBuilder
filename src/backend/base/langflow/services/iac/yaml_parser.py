"""YAML parser for RBAC Infrastructure as Code.

PRD Story 3.3 - Manage Roles via IaC
PRD Story 3.6 - Assign Roles via IaC (YAML/Terraform)
Phase 6: IaC Support
"""

from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator
from loguru import logger


class YAMLParseError(Exception):
    """YAML parsing error."""

    pass


class RolePermission(BaseModel):
    """Role permission definition in YAML."""

    resource_type: str = Field(..., description="Resource type (flow, project, workspace, etc.)")
    actions: list[str] = Field(..., description="List of actions (create, read, update, delete, etc.)")
    scope: str | None = Field(None, description="Optional scope (workspace, project, etc.)")

    @field_validator("actions")
    @classmethod
    def validate_actions(cls, v: list[str]) -> list[str]:
        """Validate actions are not empty."""
        if not v:
            raise ValueError("actions cannot be empty")
        return v


class RoleDefinition(BaseModel):
    """Role definition in YAML."""

    name: str = Field(..., description="Role name (e.g., 'Editor', 'Viewer')")
    description: str | None = Field(None, description="Role description")
    permissions: list[RolePermission] = Field(..., description="List of permissions")
    system_role: bool = Field(False, description="Whether this is a system role")
    inherits_from: list[str] | None = Field(None, description="Parent roles to inherit from")

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: list[RolePermission]) -> list[RolePermission]:
        """Validate permissions are not empty."""
        if not v:
            raise ValueError("permissions cannot be empty")
        return v


class GrantScope(BaseModel):
    """Grant scope definition in YAML."""

    workspace: str | None = Field(None, description="Workspace ID or name")
    project: str | None = Field(None, description="Project ID or name")
    flow: str | None = Field(None, description="Flow ID or name")
    environment: str | None = Field(None, description="Environment ID or name")

    def to_dict(self) -> dict[str, str]:
        """Convert to dict, excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}

    @field_validator("*")
    @classmethod
    def at_least_one_scope(cls, v: Any, info: Any) -> Any:
        """Validate at least one scope is set."""
        # This will be checked in model_validator
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate at least one scope is set."""
        if not any([self.workspace, self.project, self.flow, self.environment]):
            raise ValueError("At least one scope must be specified")


class GrantDefinition(BaseModel):
    """Grant (role assignment) definition in YAML."""

    principal: str = Field(..., description="Principal (user:email, group:name, service_account:name)")
    role: str = Field(..., description="Role name")
    scope: GrantScope = Field(..., description="Grant scope")
    expires_at: str | None = Field(None, description="Expiration timestamp (ISO 8601)")
    description: str | None = Field(None, description="Grant description")

    @field_validator("principal")
    @classmethod
    def validate_principal(cls, v: str) -> str:
        """Validate principal format."""
        if ":" not in v:
            raise ValueError("principal must be in format 'type:identifier' (e.g., 'user:email@example.com')")
        principal_type, identifier = v.split(":", 1)
        if principal_type not in ["user", "group", "service_account"]:
            raise ValueError("principal type must be 'user', 'group', or 'service_account'")
        if not identifier:
            raise ValueError("principal identifier cannot be empty")
        return v


class RBACPolicy(BaseModel):
    """Complete RBAC policy document in YAML."""

    version: str = Field("v1", description="Policy version")
    roles: list[RoleDefinition] | None = Field(None, description="Role definitions")
    grants: list[GrantDefinition] | None = Field(None, description="Role assignments")
    metadata: dict[str, Any] | None = Field(None, description="Optional metadata")


class YAMLParser:
    """Parser for RBAC YAML policies.

    PRD Story 3.3 @AC1 - Apply YAML policy
    PRD Story 3.6 @AC1 - Apply bindings
    """

    @staticmethod
    def parse(yaml_content: str) -> RBACPolicy:
        """Parse YAML content into RBAC policy.

        Args:
            yaml_content: YAML string

        Returns:
            Parsed RBACPolicy

        Raises:
            YAMLParseError: If parsing fails
        """
        try:
            # Parse YAML
            data = yaml.safe_load(yaml_content)
            if data is None:
                raise YAMLParseError("Empty YAML document")

            # Validate with Pydantic
            policy = RBACPolicy(**data)

            logger.info(
                f"Parsed RBAC policy: {len(policy.roles or [])} roles, "
                f"{len(policy.grants or [])} grants"
            )

            return policy

        except yaml.YAMLError as e:
            logger.error(f"YAML syntax error: {e}")
            raise YAMLParseError(f"Invalid YAML syntax: {e}")
        except ValidationError as e:
            logger.error(f"YAML validation error: {e}")
            raise YAMLParseError(f"Invalid RBAC policy: {e}")
        except Exception as e:
            logger.error(f"YAML parse error: {e}")
            raise YAMLParseError(f"Parse error: {e}")

    @staticmethod
    def parse_file(file_path: str) -> RBACPolicy:
        """Parse YAML file into RBAC policy.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed RBACPolicy

        Raises:
            YAMLParseError: If parsing fails
        """
        try:
            with open(file_path, "r") as f:
                yaml_content = f.read()
            return YAMLParser.parse(yaml_content)
        except FileNotFoundError:
            raise YAMLParseError(f"File not found: {file_path}")
        except IOError as e:
            raise YAMLParseError(f"Failed to read file: {e}")

    @staticmethod
    def dump(policy: RBACPolicy) -> str:
        """Dump RBAC policy to YAML string.

        Args:
            policy: RBAC policy

        Returns:
            YAML string
        """
        data = policy.model_dump(exclude_none=True)
        return yaml.safe_dump(data, default_flow_style=False, sort_keys=False)

    @staticmethod
    def validate_roles(policy: RBACPolicy) -> list[str]:
        """Validate role definitions.

        Args:
            policy: RBAC policy

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not policy.roles:
            return errors

        # Check for duplicate role names
        role_names = [role.name for role in policy.roles]
        duplicates = [name for name in role_names if role_names.count(name) > 1]
        if duplicates:
            errors.append(f"Duplicate role names: {', '.join(set(duplicates))}")

        # Check role inheritance references
        for role in policy.roles:
            if role.inherits_from:
                for parent_name in role.inherits_from:
                    if parent_name not in role_names:
                        errors.append(f"Role '{role.name}' inherits from unknown role '{parent_name}'")

        # Check for circular inheritance
        for role in policy.roles:
            if role.inherits_from and YAMLParser._has_circular_inheritance(role, policy.roles):
                errors.append(f"Role '{role.name}' has circular inheritance")

        return errors

    @staticmethod
    def validate_grants(policy: RBACPolicy, existing_roles: list[str] | None = None) -> list[str]:
        """Validate grant definitions.

        Args:
            policy: RBAC policy
            existing_roles: List of existing role names (optional)

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not policy.grants:
            return errors

        # Build role names list
        role_names = existing_roles or []
        if policy.roles:
            role_names.extend([role.name for role in policy.roles])

        # Validate each grant
        for i, grant in enumerate(policy.grants):
            # Check role exists
            if grant.role not in role_names:
                errors.append(f"Grant {i}: role '{grant.role}' not found")

            # Validate expiration timestamp
            if grant.expires_at:
                try:
                    from datetime import datetime

                    datetime.fromisoformat(grant.expires_at.replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"Grant {i}: invalid expires_at timestamp '{grant.expires_at}'")

        return errors

    @staticmethod
    def _has_circular_inheritance(role: RoleDefinition, all_roles: list[RoleDefinition]) -> bool:
        """Check if role has circular inheritance.

        Args:
            role: Role to check
            all_roles: All roles in policy

        Returns:
            True if circular inheritance detected
        """
        visited = set()
        role_map = {r.name: r for r in all_roles}

        def visit(current_role: RoleDefinition) -> bool:
            if current_role.name in visited:
                return True  # Circular dependency
            visited.add(current_role.name)

            if current_role.inherits_from:
                for parent_name in current_role.inherits_from:
                    parent = role_map.get(parent_name)
                    if parent and visit(parent):
                        return True

            visited.remove(current_role.name)
            return False

        return visit(role)


# Example YAML policy
EXAMPLE_YAML = """
version: v1

metadata:
  name: example-rbac-policy
  description: Example RBAC policy for LangBuilder
  created_by: devops-team

roles:
  - name: FlowEditor
    description: Can create and edit flows
    permissions:
      - resource_type: flow
        actions: [create, read, update]
      - resource_type: component
        actions: [read, update]
    system_role: false

  - name: FlowDeployer
    description: Can deploy flows to environments
    permissions:
      - resource_type: flow
        actions: [read]
      - resource_type: environment
        actions: [deploy_environment]
    inherits_from:
      - FlowEditor

grants:
  - principal: user:alice@example.com
    role: FlowEditor
    scope:
      project: PRJ-123
    description: Alice can edit flows in PRJ-123

  - principal: group:DataScience
    role: FlowEditor
    scope:
      workspace: WS-456
    description: Data Science team can edit flows in WS-456

  - principal: service_account:deploy-bot
    role: FlowDeployer
    scope:
      environment: staging
    expires_at: "2025-12-31T23:59:59Z"
    description: Deploy bot can deploy to staging until end of 2025
"""
