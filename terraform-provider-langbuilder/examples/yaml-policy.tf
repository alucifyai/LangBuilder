# Example: Apply RBAC policy from YAML file
#
# This demonstrates using the langbuilder_policy_apply resource
# to apply an entire RBAC policy from a YAML file.
#
# PRD Story 3.6 @AC1 - Apply bindings via IaC

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

# Apply RBAC policy from YAML file
resource "langbuilder_policy_apply" "rbac_policy" {
  yaml_file = file("${path.module}/rbac-policy.yaml")

  # Prune grants not in policy (GitOps mode)
  prune = true
}

# Output apply results
output "policy_apply_results" {
  value = {
    roles_created   = langbuilder_policy_apply.rbac_policy.roles_created
    roles_updated   = langbuilder_policy_apply.rbac_policy.roles_updated
    grants_created  = langbuilder_policy_apply.rbac_policy.grants_created
    grants_updated  = langbuilder_policy_apply.rbac_policy.grants_updated
    grants_removed  = langbuilder_policy_apply.rbac_policy.grants_removed
    last_applied    = langbuilder_policy_apply.rbac_policy.last_applied
  }
}
