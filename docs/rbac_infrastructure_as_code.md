# RBAC Infrastructure as Code

LangBuilder provides comprehensive Infrastructure-as-Code (IaC) support for managing Role-Based Access Control (RBAC) policies. This enables teams to version control, review, and deploy RBAC configurations using standard DevOps practices.

## Overview

The RBAC IaC system supports:

- **YAML/JSON Configuration**: Human-readable policy definitions
- **Terraform Integration**: Infrastructure provider for automated deployments
- **Export/Import**: Bidirectional configuration management
- **Template System**: Pre-built policy templates for common scenarios
- **Validation**: Schema validation and preview capabilities
- **GitOps Workflows**: Integration with CI/CD pipelines

## Configuration Format

### Basic Structure

```yaml
apiVersion: langflow.org/v1
kind: RBACPolicy
metadata:
  name: my-workspace-rbac
  workspace: production
  description: RBAC configuration for production workspace
  labels:
    environment: production
    team: ml-platform
spec:
  permissions:
    - name: flow:read
      description: Read flows and their configurations
      resourceType: flow
      action: read
    # ... more permissions

  roles:
    - name: data-scientist
      description: Data scientists can read and execute flows
      permissions:
        - flow:read
        - flow:execute
      priority: 100
    # ... more roles

  groups:
    - name: data-science-team
      description: Data science team members
      type: team
      members:
        - alice@company.com
        - bob@company.com
      autoAssignRoles:
        - data-scientist
    # ... more groups

  assignments:
    - user: lead@company.com
      roles:
        - ml-engineer
      scopeType: workspace
    # ... more assignments
```

## API Endpoints

### Export Configuration

#### Export Workspace Configuration
```http
GET /api/v1/rbac/iac/export/workspace/{workspace_id}?format=yaml&include_system=false
```

#### Export Global Configuration
```http
GET /api/v1/rbac/iac/export/global?format=yaml&include_system=true
```

**Parameters:**
- `format`: Export format (`yaml`, `json`, `terraform`)
- `include_system`: Include system-defined roles and permissions

### Import Configuration

#### Validate Configuration
```http
POST /api/v1/rbac/iac/validate
Content-Type: multipart/form-data

config: <YAML_OR_JSON_CONFIG>
format: yaml
```

#### Preview Import Changes
```http
POST /api/v1/rbac/iac/import/preview
Content-Type: multipart/form-data

config: <YAML_OR_JSON_CONFIG>
workspace_id: <WORKSPACE_UUID>
format: yaml
```

#### Apply Import
```http
POST /api/v1/rbac/iac/import/apply
Content-Type: multipart/form-data

config: <YAML_OR_JSON_CONFIG>
workspace_id: <WORKSPACE_UUID>
dry_run: false
format: yaml
```

#### Import from File
```http
POST /api/v1/rbac/iac/import/file
Content-Type: multipart/form-data

file: <CONFIG_FILE>
workspace_id: <WORKSPACE_UUID>
dry_run: false
```

### Templates

#### List Templates
```http
GET /api/v1/rbac/iac/templates
```

#### Generate Template
```http
POST /api/v1/rbac/iac/templates/generate
Content-Type: application/json

{
  "template_type": "basic",
  "workspace_name": "my-workspace",
  "include_examples": true
}
```

## Configuration Schema

### Metadata Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique configuration name |
| `workspace` | string | No | Target workspace |
| `project` | string | No | Target project |
| `environment` | string | No | Target environment |
| `description` | string | No | Configuration description |
| `labels` | object | No | Key-value labels |
| `annotations` | object | No | Additional metadata |

### Permission Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Permission name (e.g., "flow:read") |
| `description` | string | No | Permission description |
| `resourceType` | string | Yes | Resource type (flow, workspace, etc.) |
| `action` | string | Yes | Action (read, write, execute, etc.) |
| `scopeType` | string | No | Permission scope |
| `conditions` | object | No | Conditional logic |
| `metadata` | object | No | Additional metadata |
| `tags` | array | No | Permission tags |

### Role Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Role name |
| `description` | string | No | Role description |
| `type` | string | No | Role type (system, custom, etc.) |
| `permissions` | array | No | Permission names |
| `parentRole` | string | No | Parent role for inheritance |
| `priority` | integer | No | Role priority (1-1000) |
| `isSystem` | boolean | No | System role flag |
| `isDefault` | boolean | No | Default role flag |
| `scopeType` | string | No | Role scope |
| `metadata` | object | No | Additional metadata |
| `tags` | array | No | Role tags |

### Assignment Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user` | string | No* | User email/username |
| `group` | string | No* | Group name |
| `serviceAccount` | string | No* | Service account name |
| `roles` | array | Yes | Role names to assign |
| `scopeType` | string | Yes | Assignment scope |
| `scopeId` | string | No | Specific scope ID |
| `expiresAt` | string | No | Expiration timestamp |
| `conditions` | object | No | Assignment conditions |
| `metadata` | object | No | Additional metadata |

*Note: One of `user`, `group`, or `serviceAccount` must be specified.

### Group Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Group name |
| `description` | string | No | Group description |
| `type` | string | No | Group type (local, synced, etc.) |
| `members` | array | No | Member email addresses |
| `autoAssignRoles` | array | No | Auto-assigned roles |
| `membershipRules` | object | No | Dynamic membership rules |
| `maxMembers` | integer | No | Maximum members |
| `metadata` | object | No | Additional metadata |
| `tags` | array | No | Group tags |

## Templates

### Available Templates

1. **Basic Workspace**: Simple role-based access control
   - Roles: viewer, editor, admin
   - Use cases: Small teams, simple projects

2. **Advanced Workspace**: Comprehensive RBAC with project scoping
   - Roles: viewer, developer, maintainer, admin
   - Use cases: Medium teams, multi-project workspaces

3. **Enterprise Workspace**: Full-featured RBAC with compliance
   - Roles: guest, analyst, developer, lead, manager, admin
   - Use cases: Large enterprises, compliance requirements

4. **Service Account**: API access configuration
   - Roles: api-reader, api-writer, automation
   - Use cases: CI/CD integration, API access

### Generating Templates

Use the API or UI to generate templates:

```bash
curl -X POST "${LANGFLOW_API_URL}/api/v1/rbac/iac/templates/generate" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "template_type": "basic",
    "workspace_name": "production",
    "include_examples": true
  }'
```

## Terraform Integration

### Provider Configuration

```hcl
terraform {
  required_providers {
    langflow = {
      source  = "langflow/langflow"
      version = "~> 1.0"
    }
  }
}

provider "langflow" {
  api_url   = var.langflow_api_url
  api_token = var.langflow_api_token
}
```

### Resource Examples

#### Role Resource

```hcl
resource "langflow_role" "data_scientist" {
  name        = "data-scientist"
  description = "Data scientists can read and execute flows"
  workspace   = "production"
  permissions = [
    "flow:read",
    "flow:execute"
  ]
  priority = 100

  metadata = {
    team = "data-science"
  }
}
```

#### Role Assignment Resource

```hcl
resource "langflow_role_assignment" "alice_data_scientist" {
  user       = "alice@company.com"
  roles      = ["data-scientist"]
  scope_type = "workspace"
  workspace  = "production"
}
```

### Exporting to Terraform

Export existing configurations as Terraform HCL:

```bash
curl -X GET "${LANGFLOW_API_URL}/api/v1/rbac/iac/export/workspace/${WORKSPACE_ID}?format=terraform" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -o workspace-rbac.tf
```

## GitOps Workflows

### CI/CD Integration

#### GitHub Actions Example

```yaml
name: Deploy RBAC Configuration

on:
  push:
    paths:
      - 'rbac/**/*.yaml'
    branches:
      - main

jobs:
  deploy-rbac:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Validate RBAC Configuration
        run: |
          curl -X POST "${LANGFLOW_API_URL}/api/v1/rbac/iac/validate" \
            -H "Authorization: Bearer ${{ secrets.LANGFLOW_API_TOKEN }}" \
            -F "config=@rbac/production.yaml"

      - name: Preview Changes
        run: |
          curl -X POST "${LANGFLOW_API_URL}/api/v1/rbac/iac/import/preview" \
            -H "Authorization: Bearer ${{ secrets.LANGFLOW_API_TOKEN }}" \
            -F "config=@rbac/production.yaml" \
            -F "workspace_id=${{ vars.PRODUCTION_WORKSPACE_ID }}"

      - name: Apply Configuration
        run: |
          curl -X POST "${LANGFLOW_API_URL}/api/v1/rbac/iac/import/apply" \
            -H "Authorization: Bearer ${{ secrets.LANGFLOW_API_TOKEN }}" \
            -F "config=@rbac/production.yaml" \
            -F "workspace_id=${{ vars.PRODUCTION_WORKSPACE_ID }}"
```

#### GitLab CI Example

```yaml
stages:
  - validate
  - preview
  - deploy

validate-rbac:
  stage: validate
  script:
    - |
      curl -X POST "${LANGFLOW_API_URL}/api/v1/rbac/iac/validate" \
        -H "Authorization: Bearer ${LANGFLOW_API_TOKEN}" \
        -F "config=@rbac/production.yaml"
  only:
    changes:
      - rbac/**/*.yaml

preview-rbac:
  stage: preview
  script:
    - |
      curl -X POST "${LANGFLOW_API_URL}/api/v1/rbac/iac/import/preview" \
        -H "Authorization: Bearer ${LANGFLOW_API_TOKEN}" \
        -F "config=@rbac/production.yaml" \
        -F "workspace_id=${PRODUCTION_WORKSPACE_ID}"
  only:
    changes:
      - rbac/**/*.yaml

deploy-rbac:
  stage: deploy
  script:
    - |
      curl -X POST "${LANGFLOW_API_URL}/api/v1/rbac/iac/import/apply" \
        -H "Authorization: Bearer ${LANGFLOW_API_TOKEN}" \
        -F "config=@rbac/production.yaml" \
        -F "workspace_id=${PRODUCTION_WORKSPACE_ID}"
  only:
    refs:
      - main
    changes:
      - rbac/**/*.yaml
  when: manual
```

## Best Practices

### Configuration Management

1. **Version Control**: Store RBAC configurations in Git repositories
2. **Environment Separation**: Use separate configurations for dev/staging/production
3. **Code Reviews**: Require reviews for RBAC configuration changes
4. **Atomic Changes**: Group related changes in single commits
5. **Documentation**: Document role purposes and permission rationale

### Security Considerations

1. **Principle of Least Privilege**: Grant minimum necessary permissions
2. **Regular Audits**: Review configurations periodically
3. **Sensitive Data**: Avoid hardcoding sensitive information
4. **Access Control**: Restrict who can modify RBAC configurations
5. **Backup**: Regularly backup configurations

### Development Workflow

1. **Local Development**: Use templates to bootstrap new environments
2. **Testing**: Validate configurations before deployment
3. **Preview**: Always preview changes before applying
4. **Rollback**: Keep previous configurations for rollback capability
5. **Monitoring**: Monitor RBAC changes and access patterns

## Error Handling

### Common Validation Errors

- **Duplicate Names**: Role or permission names must be unique
- **Invalid References**: Assignments must reference existing roles
- **Schema Violations**: Configuration must match required schema
- **Permission Conflicts**: Conflicting permission definitions

### Import Errors

- **Missing Dependencies**: Referenced resources must exist or be created first
- **Workspace Not Found**: Target workspace must exist
- **Insufficient Permissions**: User must have admin rights to import
- **Format Errors**: Configuration must be valid YAML/JSON

### Resolution Strategies

1. **Validation First**: Always validate before importing
2. **Incremental Import**: Import in small batches to isolate issues
3. **Dry Run**: Use dry run mode to test without applying changes
4. **Rollback Plan**: Keep backup configurations for rollback
5. **Support**: Contact support for complex migration scenarios

## Monitoring and Compliance

### Audit Logging

All IaC operations are logged in the audit system:

- Configuration imports and exports
- Validation attempts
- Template generations
- API access patterns

### Compliance Reports

Generate compliance reports showing:

- Current role assignments
- Permission usage patterns
- Configuration change history
- Access pattern analysis

### Metrics and Alerting

Monitor key metrics:

- Configuration change frequency
- Import success/failure rates
- Validation error patterns
- Template usage statistics