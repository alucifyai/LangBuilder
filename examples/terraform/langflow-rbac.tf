# Terraform configuration for LangBuilder RBAC management
# This example demonstrates how to manage RBAC policies using Terraform

terraform {
  required_version = ">= 1.0"
  required_providers {
    langflow = {
      source  = "langflow/langflow"
      version = "~> 1.0"
    }
  }
}

# Provider configuration
provider "langflow" {
  api_url   = var.langflow_api_url
  api_token = var.langflow_api_token
}

# Variables
variable "langflow_api_url" {
  description = "LangBuilder API URL"
  type        = string
}

variable "langflow_api_token" {
  description = "LangBuilder API token"
  type        = string
  sensitive   = true
}

variable "workspace_name" {
  description = "Target workspace name"
  type        = string
  default     = "production"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

# Data sources
data "langflow_workspace" "main" {
  name = var.workspace_name
}

# Basic permissions
resource "langflow_permission" "flow_read" {
  name         = "flow:read"
  description  = "Read flows and their configurations"
  resource_type = "flow"
  action       = "read"
  workspace    = data.langflow_workspace.main.id

  metadata = {
    category    = "basic"
    compliance  = "required"
    sensitivity = "low"
  }

  tags = ["basic", "read-only"]
}

resource "langflow_permission" "flow_write" {
  name         = "flow:write"
  description  = "Create and modify flows"
  resource_type = "flow"
  action       = "write"
  workspace    = data.langflow_workspace.main.id

  conditions = {
    requires_approval = true
    approval_threshold = 1
  }

  metadata = {
    category    = "basic"
    compliance  = "required"
    sensitivity = "medium"
  }

  tags = ["basic", "write"]
}

resource "langflow_permission" "flow_execute" {
  name         = "flow:execute"
  description  = "Execute flows"
  resource_type = "flow"
  action       = "execute"
  workspace    = data.langflow_workspace.main.id

  conditions = {
    audit_required = true
    resource_limits = {
      max_cpu    = "1000m"
      max_memory = "2Gi"
    }
  }

  metadata = {
    category    = "basic"
    compliance  = "required"
    sensitivity = "medium"
  }

  tags = ["basic", "execute"]
}

resource "langflow_permission" "flow_deploy" {
  name         = "flow:deploy"
  description  = "Deploy flows to production"
  resource_type = "flow"
  action       = "deploy"
  workspace    = data.langflow_workspace.main.id

  conditions = {
    requires_approval = true
    approval_threshold = 2
    break_glass_eligible = false
  }

  metadata = {
    category    = "advanced"
    compliance  = "critical"
    sensitivity = "high"
  }

  tags = ["advanced", "deploy", "production"]
}

resource "langflow_permission" "workspace_admin" {
  name         = "workspace:admin"
  description  = "Administer workspace settings"
  resource_type = "workspace"
  action       = "admin"
  workspace    = data.langflow_workspace.main.id

  conditions = {
    requires_approval = true
    approval_threshold = 3
    break_glass_eligible = true
  }

  metadata = {
    category    = "admin"
    compliance  = "critical"
    sensitivity = "critical"
  }

  tags = ["admin", "critical"]
}

# Roles
resource "langflow_role" "viewer" {
  name        = "viewer"
  description = "Can view flows and workspace information"
  type        = "custom"
  workspace   = data.langflow_workspace.main.id
  priority    = 100

  permissions = [
    langflow_permission.flow_read.name
  ]

  metadata = {
    level      = "entry"
    department = "all"
  }

  tags = ["read-only", "basic"]
}

resource "langflow_role" "developer" {
  name        = "developer"
  description = "Can develop and test flows"
  type        = "custom"
  workspace   = data.langflow_workspace.main.id
  priority    = 200

  permissions = [
    langflow_permission.flow_read.name,
    langflow_permission.flow_write.name,
    langflow_permission.flow_execute.name
  ]

  metadata = {
    level      = "intermediate"
    department = "engineering"
  }

  tags = ["development", "standard"]

  depends_on = [
    langflow_permission.flow_read,
    langflow_permission.flow_write,
    langflow_permission.flow_execute
  ]
}

resource "langflow_role" "deployer" {
  name        = "deployer"
  description = "Can deploy flows in addition to development"
  type        = "custom"
  workspace   = data.langflow_workspace.main.id
  priority    = 250

  permissions = [
    langflow_permission.flow_read.name,
    langflow_permission.flow_write.name,
    langflow_permission.flow_execute.name,
    langflow_permission.flow_deploy.name
  ]

  metadata = {
    level      = "advanced"
    department = "engineering"
  }

  tags = ["deployment", "advanced"]

  depends_on = [
    langflow_permission.flow_read,
    langflow_permission.flow_write,
    langflow_permission.flow_execute,
    langflow_permission.flow_deploy
  ]
}

resource "langflow_role" "admin" {
  name        = "admin"
  description = "Full workspace administration"
  type        = "custom"
  workspace   = data.langflow_workspace.main.id
  priority    = 300

  permissions = [
    langflow_permission.flow_read.name,
    langflow_permission.flow_write.name,
    langflow_permission.flow_execute.name,
    langflow_permission.flow_deploy.name,
    langflow_permission.workspace_admin.name
  ]

  metadata = {
    level      = "admin"
    department = "all"
  }

  tags = ["administration", "full-access"]

  depends_on = [
    langflow_permission.flow_read,
    langflow_permission.flow_write,
    langflow_permission.flow_execute,
    langflow_permission.flow_deploy,
    langflow_permission.workspace_admin
  ]
}

# User groups
resource "langflow_user_group" "engineering_team" {
  name        = "engineering-team"
  description = "Engineering team members"
  type        = "team"
  workspace   = data.langflow_workspace.main.id

  members = [
    "alice@company.com",
    "bob@company.com",
    "charlie@company.com"
  ]

  auto_assign_roles = [
    langflow_role.developer.name
  ]

  metadata = {
    department = "engineering"
    focus      = "development"
  }

  tags = ["engineering", "development"]

  depends_on = [langflow_role.developer]
}

resource "langflow_user_group" "devops_team" {
  name        = "devops-team"
  description = "DevOps and platform team"
  type        = "team"
  workspace   = data.langflow_workspace.main.id

  members = [
    "david@company.com",
    "eva@company.com"
  ]

  auto_assign_roles = [
    langflow_role.deployer.name
  ]

  metadata = {
    department = "platform"
    focus      = "deployment"
  }

  tags = ["devops", "platform", "deployment"]

  depends_on = [langflow_role.deployer]
}

# Individual role assignments
resource "langflow_role_assignment" "admin_assignment" {
  user       = "admin@company.com"
  roles      = [langflow_role.admin.name]
  scope_type = "workspace"
  workspace  = data.langflow_workspace.main.id

  metadata = {
    reason      = "workspace-administrator"
    assigned_by = "infrastructure-team"
  }

  depends_on = [langflow_role.admin]
}

resource "langflow_role_assignment" "lead_assignment" {
  user       = "lead@company.com"
  roles      = [langflow_role.deployer.name]
  scope_type = "workspace"
  workspace  = data.langflow_workspace.main.id

  metadata = {
    reason      = "team-lead"
    assigned_by = "infrastructure-team"
  }

  depends_on = [langflow_role.deployer]
}

# Group-based role assignments
resource "langflow_role_assignment" "engineering_team_assignment" {
  group      = langflow_user_group.engineering_team.name
  roles      = [langflow_role.developer.name]
  scope_type = "workspace"
  workspace  = data.langflow_workspace.main.id

  metadata = {
    reason      = "team-membership"
    assigned_by = "infrastructure-team"
  }

  depends_on = [
    langflow_role.developer,
    langflow_user_group.engineering_team
  ]
}

resource "langflow_role_assignment" "devops_team_assignment" {
  group      = langflow_user_group.devops_team.name
  roles      = [langflow_role.deployer.name]
  scope_type = "workspace"
  workspace  = data.langflow_workspace.main.id

  metadata = {
    reason      = "deployment-access"
    assigned_by = "infrastructure-team"
  }

  depends_on = [
    langflow_role.deployer,
    langflow_user_group.devops_team
  ]
}

# Temporary contractor access
resource "langflow_role_assignment" "contractor_assignment" {
  user       = "contractor@external.com"
  roles      = [langflow_role.viewer.name]
  scope_type = "workspace"
  workspace  = data.langflow_workspace.main.id
  expires_at = "2024-12-31T23:59:59Z"

  conditions = {
    ip_restrictions = ["203.0.113.0/24"]
    vpn_required   = true
  }

  metadata = {
    reason      = "temporary-contractor"
    vendor      = "ExternalConsultants Inc"
    contract_id = "EXT-2024-001"
    assigned_by = "infrastructure-team"
  }

  depends_on = [langflow_role.viewer]
}

# Service account for CI/CD
resource "langflow_service_account" "cicd_account" {
  name        = "cicd-deployment"
  description = "Service account for CI/CD pipeline deployments"
  workspace   = data.langflow_workspace.main.id

  roles = [
    langflow_role.deployer.name
  ]

  scope_type = "workspace"

  metadata = {
    purpose    = "automation"
    system     = "github-actions"
    maintained_by = "platform-team"
  }

  tags = ["automation", "cicd", "deployment"]

  depends_on = [langflow_role.deployer]
}

# API key for service account
resource "langflow_api_key" "cicd_key" {
  name               = "cicd-deployment-key"
  description        = "API key for CI/CD deployment service account"
  service_account_id = langflow_service_account.cicd_account.id
  expires_at         = "2025-12-31T23:59:59Z"

  scopes = [
    "flow:deploy",
    "flow:read",
    "project:read"
  ]

  metadata = {
    rotation_schedule = "quarterly"
    last_rotated     = "2024-01-01T00:00:00Z"
    environment      = var.environment
  }

  tags = ["automation", "deployment", "temporary"]

  depends_on = [langflow_service_account.cicd_account]
}

# Outputs
output "workspace_id" {
  description = "The workspace ID"
  value       = data.langflow_workspace.main.id
}

output "admin_role_id" {
  description = "The admin role ID"
  value       = langflow_role.admin.id
}

output "developer_role_id" {
  description = "The developer role ID"
  value       = langflow_role.developer.id
}

output "cicd_service_account_id" {
  description = "The CI/CD service account ID"
  value       = langflow_service_account.cicd_account.id
}

output "cicd_api_key_id" {
  description = "The CI/CD API key ID"
  value       = langflow_api_key.cicd_key.id
  sensitive   = true
}

# Local values for reuse
locals {
  common_tags = {
    environment    = var.environment
    workspace     = var.workspace_name
    managed_by    = "terraform"
    configuration = "rbac-policies"
  }

  basic_permissions = [
    langflow_permission.flow_read.name,
    langflow_permission.flow_write.name,
    langflow_permission.flow_execute.name
  ]

  admin_permissions = concat(local.basic_permissions, [
    langflow_permission.flow_deploy.name,
    langflow_permission.workspace_admin.name
  ])
}

# Example of using locals for consistency
resource "langflow_role" "power_user" {
  name        = "power-user"
  description = "Power users with extended flow access"
  type        = "custom"
  workspace   = data.langflow_workspace.main.id
  priority    = 225

  permissions = local.basic_permissions

  metadata = merge(local.common_tags, {
    level      = "advanced"
    department = "mixed"
  })

  tags = ["power-user", "extended"]

  depends_on = [
    langflow_permission.flow_read,
    langflow_permission.flow_write,
    langflow_permission.flow_execute
  ]
}