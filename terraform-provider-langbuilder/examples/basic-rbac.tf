# Example Terraform configuration for LangBuilder RBAC
#
# This example demonstrates:
# - Creating custom roles
# - Assigning roles to users
# - Time-bound grants
# - Scope-based permissions

terraform {
  required_providers {
    langbuilder = {
      source  = "langbuilder/langbuilder"
      version = "~> 1.0"
    }
  }
}

provider "langbuilder" {
  api_url   = "https://langbuilder.example.com/api/v1"
  api_token = var.langbuilder_api_token
}

variable "langbuilder_api_token" {
  description = "LangBuilder API authentication token"
  type        = string
  sensitive   = true
}

# Create a FlowEditor role
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

  permission {
    resource_type = "project"
    actions       = ["read"]
  }
}

# Create a FlowDeployer role that inherits from FlowEditor
resource "langbuilder_role" "flow_deployer" {
  name        = "FlowDeployer"
  description = "Can deploy flows to environments"

  permission {
    resource_type = "flow"
    actions       = ["read"]
  }

  permission {
    resource_type = "environment"
    actions       = ["deploy_environment"]
  }

  # Inherits permissions from FlowEditor
  depends_on = [langbuilder_role.flow_editor]
}

# Grant FlowEditor role to Alice in project PRJ-123
resource "langbuilder_grant" "alice_flow_editor" {
  principal   = "user:alice@example.com"
  role_id     = langbuilder_role.flow_editor.id
  description = "Alice can edit flows in PRJ-123"

  scope = {
    project = "PRJ-123"
  }
}

# Grant FlowEditor role to Data Science team in entire workspace
resource "langbuilder_grant" "datascience_flow_editor" {
  principal   = "group:DataScience"
  role_name   = "FlowEditor"
  description = "Data Science team can edit flows in WS-456"

  scope = {
    workspace = "WS-456"
  }
}

# Grant FlowDeployer role to deploy bot with expiration
resource "langbuilder_grant" "deploy_bot_staging" {
  principal   = "service_account:deploy-bot"
  role_id     = langbuilder_role.flow_deployer.id
  description = "Deploy bot can deploy to staging until end of 2025"

  scope = {
    environment = "staging"
  }

  expires_at = "2025-12-31T23:59:59Z"
}

# Read existing Admin role
data "langbuilder_role" "admin" {
  name = "Admin"
}

# Output admin role details
output "admin_role" {
  value = {
    id          = data.langbuilder_role.admin.id
    name        = data.langbuilder_role.admin.name
    permissions = length(data.langbuilder_role.admin.permissions)
  }
}

# Output created grants
output "grants_created" {
  value = {
    alice_grant      = langbuilder_grant.alice_flow_editor.id
    datascience_grant = langbuilder_grant.datascience_flow_editor.id
    deploy_bot_grant = langbuilder_grant.deploy_bot_staging.id
  }
}
