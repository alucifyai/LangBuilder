# Terraform Provider for LangBuilder RBAC

Terraform provider for managing LangBuilder RBAC resources (roles, grants, permissions).

## Features

- **Data Sources**: Read existing RBAC resources
  - `langbuilder_role` - Read role definitions
  - `langbuilder_grant` - Read grant assignments
  - `langbuilder_permission` - Read permission catalog

- **Resources**: Manage RBAC resources
  - `langbuilder_role` - Create and manage roles
  - `langbuilder_grant` - Create and manage grants (role assignments)

- **Import from YAML**: Apply entire RBAC policies from YAML files

## Installation

```hcl
terraform {
  required_providers {
    langbuilder = {
      source  = "langbuilder/langbuilder"
      version = "~> 1.0"
    }
  }
}

provider "langbuilder" {
  api_url = "https://langbuilder.example.com/api/v1"
  api_token = var.langbuilder_api_token
}
```

## Usage Examples

### Create a Role

```hcl
resource "langbuilder_role" "flow_editor" {
  name        = "FlowEditor"
  description = "Can create and edit flows"

  permission {
    resource_type = "flow"
    actions       = ["create", "read", "update"]
  }

  permission {
    resource_type = "component"
    actions       = ["read", "update"]
  }
}
```

### Create a Grant

```hcl
resource "langbuilder_grant" "alice_flow_editor" {
  principal = "user:alice@example.com"
  role_id   = langbuilder_role.flow_editor.id

  scope = {
    project = "PRJ-123"
  }

  description = "Alice can edit flows in PRJ-123"
}
```

### Time-Bound Grant

```hcl
resource "langbuilder_grant" "deploy_bot_staging" {
  principal = "service_account:deploy-bot"
  role_name = "FlowDeployer"

  scope = {
    environment = "staging"
  }

  expires_at  = "2025-12-31T23:59:59Z"
  description = "Deploy bot can deploy to staging until end of 2025"
}
```

### Read Existing Role

```hcl
data "langbuilder_role" "admin" {
  name = "Admin"
}

output "admin_permissions" {
  value = data.langbuilder_role.admin.permissions
}
```

### Apply YAML Policy

```hcl
resource "langbuilder_policy_apply" "rbac_policy" {
  yaml_file = file("${path.module}/rbac-policy.yaml")
  prune     = true  # Remove grants not in policy
}
```

## Data Source Reference

### `langbuilder_role`

Read an existing role by name or ID.

**Arguments**:
- `id` (Optional) - Role ID
- `name` (Optional) - Role name (exactly one of `id` or `name` must be specified)

**Attributes**:
- `id` - Role ID
- `name` - Role name
- `description` - Role description
- `permissions` - List of permissions
  - `resource_type` - Resource type
  - `actions` - List of actions
- `system_role` - Whether this is a system role
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### `langbuilder_grant`

Read an existing grant by ID.

**Arguments**:
- `id` - Grant ID

**Attributes**:
- `id` - Grant ID
- `principal` - Principal (user:email, group:name, service_account:name)
- `role_id` - Role ID
- `role_name` - Role name
- `scope` - Grant scope
  - `workspace` - Workspace ID
  - `project` - Project ID
  - `flow` - Flow ID
  - `environment` - Environment ID
- `expires_at` - Expiration timestamp
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### `langbuilder_permission`

Read permission catalog.

**Arguments**: None

**Attributes**:
- `permissions` - List of all permissions
  - `id` - Permission ID
  - `resource_type` - Resource type
  - `action` - Action
  - `description` - Permission description

## Resource Reference

### `langbuilder_role`

Create and manage a role.

**Arguments**:
- `name` (Required) - Role name
- `description` (Optional) - Role description
- `permission` (Required) - List of permissions
  - `resource_type` (Required) - Resource type
  - `actions` (Required) - List of actions
- `system_role` (Optional) - Whether this is a system role (default: false)

**Attributes**: Same as data source

### `langbuilder_grant`

Create and manage a grant (role assignment).

**Arguments**:
- `principal` (Required) - Principal in format `type:identifier`
  - `user:email@example.com`
  - `group:group-name`
  - `service_account:account-name`
- `role_id` (Optional) - Role ID (one of `role_id` or `role_name` required)
- `role_name` (Optional) - Role name (one of `role_id` or `role_name` required)
- `scope` (Required) - Grant scope (at least one scope level required)
  - `workspace` (Optional) - Workspace ID
  - `project` (Optional) - Project ID
  - `flow` (Optional) - Flow ID
  - `environment` (Optional) - Environment ID
- `expires_at` (Optional) - Expiration timestamp (ISO 8601 format)
- `description` (Optional) - Grant description

**Attributes**: Same as data source

### `langbuilder_policy_apply`

Apply an RBAC policy from YAML file.

**Arguments**:
- `yaml_content` (Optional) - YAML policy content (one of `yaml_content` or `yaml_file` required)
- `yaml_file` (Optional) - Path to YAML policy file (one of `yaml_content` or `yaml_file` required)
- `prune` (Optional) - Remove grants not in policy (default: false)

**Attributes**:
- `roles_created` - Number of roles created
- `roles_updated` - Number of roles updated
- `grants_created` - Number of grants created
- `grants_updated` - Number of grants updated
- `grants_removed` - Number of grants removed (if prune=true)
- `last_applied` - Last apply timestamp

## Provider Configuration

**Arguments**:
- `api_url` (Required) - LangBuilder API URL (can use `LANGBUILDER_API_URL` env var)
- `api_token` (Required) - API authentication token (can use `LANGBUILDER_API_TOKEN` env var)
- `insecure_skip_verify` (Optional) - Skip TLS verification (default: false)

## Building the Provider

```bash
go build -o terraform-provider-langbuilder
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

See [LICENSE](LICENSE) for details.
