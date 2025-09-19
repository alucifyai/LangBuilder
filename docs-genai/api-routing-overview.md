# API Routing Overview

Based on the comprehensive analysis, here's the complete mapping of all API routing paths and their corresponding source files:

## API Routing Structure Overview

**Base URL**: `/api`
- **V1 API**: `/api/v1/` (170 endpoints)
- **V2 API**: `/api/v2/` (15 endpoints)
- **Total**: 185 endpoints across 44 router files

## Key Router Files & Their Endpoints

### Core Authentication & User Management
- **`/api/v1/login.py`**: Authentication endpoints (`/login`, `/refresh`, `/logout`, `/auto_login`)
- **`/api/v1/users.py`**: User CRUD operations (`/users/`, `/users/whoami`, `/users/{user_id}`)
- **`/api/v1/api_key.py`**: API key management (`/api_key/`, `/api_key/store`)

### Flow Management & Execution
- **`/api/v1/flows.py`**: Flow CRUD, upload/download (`/flows/`, `/flows/batch/`, `/flows/upload/`)
- **`/api/v1/chat.py`**: Flow execution & building (`/build/{flow_id}/flow`, `/build/{flow_id}/vertices`)
- **`/api/v1/endpoints.py`**: Core endpoints (`/run/{flow_id}`, `/webhook/{flow_id}`, `/version`)

### RBAC System (Dual Routing)
The RBAC system uses **dual routing** - endpoints are available under both unified and individual prefixes:

#### Workspaces
- **`/api/v1/rbac/workspaces.py`**:
  - Unified: `/api/v1/rbac/workspaces/`
  - Individual: `/api/v1/workspaces/`
  - Endpoints: CRUD, user management, stats (9 endpoints)

#### Roles
- **`/api/v1/rbac/roles.py`**:
  - Unified: `/api/v1/rbac/roles/`
  - Individual: `/api/v1/roles/`
  - Endpoints: CRUD, permission management, system role initialization (10 endpoints)

#### Permissions
- **`/api/v1/rbac/permissions.py`**:
  - Unified: `/api/v1/rbac/permissions/`
  - Individual: `/api/v1/permissions/`
  - Endpoints: List, check permissions, system initialization (7 endpoints)

#### Projects (RBAC-enabled)
- **`/api/v1/rbac/projects.py`**: RBAC-aware project management
- **`/api/v1/projects.py`**: Legacy project endpoints

### Additional RBAC Components
- **`/api/v1/rbac/environments.py`**: Environment management
- **`/api/v1/rbac/audit.py`**: Audit logging
- **`/api/v1/rbac/role_assignments.py`**: Role assignment management
- **`/api/v1/rbac/service_accounts.py`**: Service account management
- **`/api/v1/rbac/user_groups.py`**: User group management

### File & Storage Management
- **`/api/v1/files.py`**: V1 file operations (flow-specific uploads)
- **`/api/v2/files.py`**: V2 file operations (user-global file management)
- **`/api/v1/store.py`**: Component store integration

### Monitoring & Variables
- **`/api/v1/monitor.py`**: Build monitoring, message tracking, transactions
- **`/api/v1/variable.py`**: Environment variable management

### MCP (Model Context Protocol)
- **`/api/v1/mcp.py`**: Base MCP endpoints
- **`/api/v1/mcp_projects.py`**: Project-specific MCP tools
- **`/api/v2/mcp.py`**: V2 MCP server management

### Legacy & Utilities
- **`/api/v1/folders.py`**: Legacy folder endpoints (redirect to projects)
- **`/api/v1/validate.py`**: Code/prompt validation
- **`/api/v1/voice_mode.py`**: Voice integration
- **`/api/v1/starter_projects.py`**: Starter project templates

## Router Architecture Summary

1. **Main Router**: `/api/router.py` - Orchestrates all sub-routers
2. **V1 Router**: `/api/v1/__init__.py` - Includes all V1 endpoints
3. **V2 Router**: `/api/v2/__init__.py` - Includes V2 endpoints
4. **RBAC Unified Router**: Provides all RBAC endpoints under `/rbac/` prefix
5. **Individual Routers**: Maintain backward compatibility for existing integrations

The system supports both modern unified RBAC routing and legacy individual endpoint routing for seamless migration.

## Detailed Endpoint Mapping

### API V1 Endpoints (170 endpoints total)

#### Authentication & User Management
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| POST | `/api/v1/login` | `login_to_get_access_token` | `src/backend/base/langflow/api/v1/login.py` |
| GET | `/api/v1/auto_login` | `auto_login` | `src/backend/base/langflow/api/v1/login.py` |
| POST | `/api/v1/refresh` | `refresh_token` | `src/backend/base/langflow/api/v1/login.py` |
| POST | `/api/v1/logout` | `logout` | `src/backend/base/langflow/api/v1/login.py` |
| POST | `/api/v1/users/` | `add_user` | `src/backend/base/langflow/api/v1/users.py` |
| GET | `/api/v1/users/whoami` | `read_current_user` | `src/backend/base/langflow/api/v1/users.py` |
| GET | `/api/v1/users/` | `read_all_users` | `src/backend/base/langflow/api/v1/users.py` |
| PATCH | `/api/v1/users/{user_id}` | `patch_user` | `src/backend/base/langflow/api/v1/users.py` |
| PATCH | `/api/v1/users/{user_id}/reset-password` | `reset_password` | `src/backend/base/langflow/api/v1/users.py` |
| DELETE | `/api/v1/users/{user_id}` | `delete_user` | `src/backend/base/langflow/api/v1/users.py` |

#### API Key Management
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| GET | `/api/v1/api_key/` | `get_api_keys_route` | `src/backend/base/langflow/api/v1/api_key.py` |
| POST | `/api/v1/api_key/` | `create_api_key_route` | `src/backend/base/langflow/api/v1/api_key.py` |
| DELETE | `/api/v1/api_key/{api_key_id}` | `delete_api_key_route` | `src/backend/base/langflow/api/v1/api_key.py` |
| POST | `/api/v1/api_key/store` | `save_store_api_key` | `src/backend/base/langflow/api/v1/api_key.py` |

#### Flow Management
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| POST | `/api/v1/flows/` | `create_flow` | `src/backend/base/langflow/api/v1/flows.py` |
| GET | `/api/v1/flows/` | `read_flows` | `src/backend/base/langflow/api/v1/flows.py` |
| GET | `/api/v1/flows/{flow_id}` | `read_flow` | `src/backend/base/langflow/api/v1/flows.py` |
| GET | `/api/v1/flows/public_flow/{flow_id}` | `read_public_flow` | `src/backend/base/langflow/api/v1/flows.py` |
| PATCH | `/api/v1/flows/{flow_id}` | `update_flow` | `src/backend/base/langflow/api/v1/flows.py` |
| DELETE | `/api/v1/flows/{flow_id}` | `delete_flow` | `src/backend/base/langflow/api/v1/flows.py` |
| POST | `/api/v1/flows/batch/` | `create_flows` | `src/backend/base/langflow/api/v1/flows.py` |
| POST | `/api/v1/flows/upload/` | `upload_file` | `src/backend/base/langflow/api/v1/flows.py` |
| DELETE | `/api/v1/flows/` | `delete_multiple_flows` | `src/backend/base/langflow/api/v1/flows.py` |
| POST | `/api/v1/flows/download/` | `download_multiple_file` | `src/backend/base/langflow/api/v1/flows.py` |
| GET | `/api/v1/flows/basic_examples/` | `read_basic_examples` | `src/backend/base/langflow/api/v1/flows.py` |

#### Flow Execution & Chat
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| POST | `/api/v1/build/{flow_id}/vertices` | `retrieve_vertices_order` | `src/backend/base/langflow/api/v1/chat.py` |
| POST | `/api/v1/build/{flow_id}/flow` | `build_flow` | `src/backend/base/langflow/api/v1/chat.py` |
| GET | `/api/v1/build/{job_id}/events` | `get_build_events` | `src/backend/base/langflow/api/v1/chat.py` |
| POST | `/api/v1/build/{job_id}/cancel` | `cancel_build` | `src/backend/base/langflow/api/v1/chat.py` |
| POST | `/api/v1/build/{flow_id}/vertices/{vertex_id}` | `build_vertex` | `src/backend/base/langflow/api/v1/chat.py` |
| POST | `/api/v1/build_public_tmp/{flow_id}/flow` | `build_public_tmp` | `src/backend/base/langflow/api/v1/chat.py` |

#### Project Management
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| POST | `/api/v1/projects/` | `create_project` | `src/backend/base/langflow/api/v1/projects.py` |
| GET | `/api/v1/projects/` | `list_projects` | `src/backend/base/langflow/api/v1/projects.py` |
| GET | `/api/v1/projects/{project_id}` | `read_project` | `src/backend/base/langflow/api/v1/projects.py` |
| PATCH | `/api/v1/projects/{project_id}` | `update_project` | `src/backend/base/langflow/api/v1/projects.py` |
| DELETE | `/api/v1/projects/{project_id}` | `delete_project` | `src/backend/base/langflow/api/v1/projects.py` |
| GET | `/api/v1/projects/download/{project_id}` | `download_file` | `src/backend/base/langflow/api/v1/projects.py` |
| POST | `/api/v1/projects/upload/` | `upload_file` | `src/backend/base/langflow/api/v1/projects.py` |

#### RBAC - Workspaces (prefix: `/api/v1/rbac/workspaces` and `/api/v1/workspaces`)
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| POST | `/api/v1/workspaces/` | `create_workspace` | `src/backend/base/langflow/api/v1/rbac/workspaces.py` |
| GET | `/api/v1/workspaces/` | `list_workspaces` | `src/backend/base/langflow/api/v1/rbac/workspaces.py` |
| GET | `/api/v1/workspaces/{workspace_id}` | `get_workspace` | `src/backend/base/langflow/api/v1/rbac/workspaces.py` |
| PUT | `/api/v1/workspaces/{workspace_id}` | `update_workspace` | `src/backend/base/langflow/api/v1/rbac/workspaces.py` |
| DELETE | `/api/v1/workspaces/{workspace_id}` | `delete_workspace` | `src/backend/base/langflow/api/v1/rbac/workspaces.py` |
| POST | `/api/v1/workspaces/{workspace_id}/invite` | `invite_user_to_workspace` | `src/backend/base/langflow/api/v1/rbac/workspaces.py` |
| GET | `/api/v1/workspaces/{workspace_id}/users` | `list_workspace_users` | `src/backend/base/langflow/api/v1/rbac/workspaces.py` |
| GET | `/api/v1/workspaces/{workspace_id}/projects` | `list_workspace_projects` | `src/backend/base/langflow/api/v1/rbac/workspaces.py` |
| GET | `/api/v1/workspaces/{workspace_id}/stats` | `get_workspace_statistics` | `src/backend/base/langflow/api/v1/rbac/workspaces.py` |

#### RBAC - Roles (prefix: `/api/v1/rbac/roles` and `/api/v1/roles`)
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| POST | `/api/v1/roles/` | `create_role` | `src/backend/base/langflow/api/v1/rbac/roles.py` |
| GET | `/api/v1/roles/` | `list_roles` | `src/backend/base/langflow/api/v1/rbac/roles.py` |
| GET | `/api/v1/roles/{role_id}` | `get_role` | `src/backend/base/langflow/api/v1/rbac/roles.py` |
| PUT | `/api/v1/roles/{role_id}` | `update_role` | `src/backend/base/langflow/api/v1/rbac/roles.py` |
| DELETE | `/api/v1/roles/{role_id}` | `delete_role` | `src/backend/base/langflow/api/v1/rbac/roles.py` |
| GET | `/api/v1/roles/{role_id}/permissions` | `list_role_permissions` | `src/backend/base/langflow/api/v1/rbac/roles.py` |
| POST | `/api/v1/roles/{role_id}/permissions` | `assign_permission_to_role` | `src/backend/base/langflow/api/v1/rbac/roles.py` |
| PUT | `/api/v1/roles/{role_id}/permissions` | `update_role_permissions` | `src/backend/base/langflow/api/v1/rbac/roles.py` |
| DELETE | `/api/v1/roles/{role_id}/permissions/{permission_id}` | `remove_permission_from_role` | `src/backend/base/langflow/api/v1/rbac/roles.py` |
| POST | `/api/v1/roles/initialize-system-roles` | `initialize_system_roles` | `src/backend/base/langflow/api/v1/rbac/roles.py` |

#### RBAC - Permissions (prefix: `/api/v1/rbac/permissions` and `/api/v1/permissions`)
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| GET | `/api/v1/permissions/` | `list_permissions` | `src/backend/base/langflow/api/v1/rbac/permissions.py` |
| GET | `/api/v1/permissions/{permission_id}` | `get_permission` | `src/backend/base/langflow/api/v1/rbac/permissions.py` |
| GET | `/api/v1/permissions/actions` | `list_actions` | `src/backend/base/langflow/api/v1/rbac/permissions.py` |
| GET | `/api/v1/permissions/resource-types` | `list_resource_types` | `src/backend/base/langflow/api/v1/rbac/permissions.py` |
| POST | `/api/v1/permissions/check-permission` | `check_permission` | `src/backend/base/langflow/api/v1/rbac/permissions.py` |
| POST | `/api/v1/permissions/batch-check-permission` | `batch_check_permissions` | `src/backend/base/langflow/api/v1/rbac/permissions.py` |
| POST | `/api/v1/permissions/initialize-system-permissions` | `initialize_system_permissions` | `src/backend/base/langflow/api/v1/rbac/permissions.py` |

#### File Management
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| POST | `/api/v1/files/upload/{flow_id}` | `upload_file` | `src/backend/base/langflow/api/v1/files.py` |
| GET | `/api/v1/files/download/{flow_id}/{file_name}` | `download_file` | `src/backend/base/langflow/api/v1/files.py` |
| GET | `/api/v1/files/images/{flow_id}/{file_name}` | `download_image` | `src/backend/base/langflow/api/v1/files.py` |
| GET | `/api/v1/files/profile_pictures/{folder_name}/{file_name}` | `download_profile_picture` | `src/backend/base/langflow/api/v1/files.py` |
| GET | `/api/v1/files/profile_pictures/list` | `list_profile_pictures` | `src/backend/base/langflow/api/v1/files.py` |
| GET | `/api/v1/files/list/{flow_id}` | `list_files` | `src/backend/base/langflow/api/v1/files.py` |
| DELETE | `/api/v1/files/delete/{flow_id}/{file_name}` | `delete_file` | `src/backend/base/langflow/api/v1/files.py` |

#### Monitoring
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| GET | `/api/v1/monitor/builds` | `get_vertex_builds` | `src/backend/base/langflow/api/v1/monitor.py` |
| DELETE | `/api/v1/monitor/builds` | `delete_vertex_builds` | `src/backend/base/langflow/api/v1/monitor.py` |
| GET | `/api/v1/monitor/messages/sessions` | `get_message_sessions` | `src/backend/base/langflow/api/v1/monitor.py` |
| GET | `/api/v1/monitor/messages` | `get_messages` | `src/backend/base/langflow/api/v1/monitor.py` |
| DELETE | `/api/v1/monitor/messages` | `delete_messages` | `src/backend/base/langflow/api/v1/monitor.py` |
| PUT | `/api/v1/monitor/messages/{message_id}` | `update_message` | `src/backend/base/langflow/api/v1/monitor.py` |
| DELETE | `/api/v1/monitor/messages/session/{session_id}` | `delete_messages_session` | `src/backend/base/langflow/api/v1/monitor.py` |
| GET | `/api/v1/monitor/transactions` | `get_transactions` | `src/backend/base/langflow/api/v1/monitor.py` |

#### Variables
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| POST | `/api/v1/variables/` | `create_variable` | `src/backend/base/langflow/api/v1/variable.py` |
| GET | `/api/v1/variables/` | `read_variables` | `src/backend/base/langflow/api/v1/variable.py` |
| PATCH | `/api/v1/variables/{variable_id}` | `update_variable` | `src/backend/base/langflow/api/v1/variable.py` |
| DELETE | `/api/v1/variables/{variable_id}` | `delete_variable` | `src/backend/base/langflow/api/v1/variable.py` |

#### Store & Components
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| GET | `/api/v1/store/check/` | `check_if_store_is_enabled` | `src/backend/base/langflow/api/v1/store.py` |
| GET | `/api/v1/store/check/api_key` | `check_if_store_has_api_key` | `src/backend/base/langflow/api/v1/store.py` |
| POST | `/api/v1/store/components/` | `share_component` | `src/backend/base/langflow/api/v1/store.py` |
| PATCH | `/api/v1/store/components/{component_id}` | `update_shared_component` | `src/backend/base/langflow/api/v1/store.py` |
| GET | `/api/v1/store/components/` | `get_components` | `src/backend/base/langflow/api/v1/store.py` |
| GET | `/api/v1/store/components/{component_id}` | `download_component` | `src/backend/base/langflow/api/v1/store.py` |
| GET | `/api/v1/store/tags` | `get_tags` | `src/backend/base/langflow/api/v1/store.py` |
| GET | `/api/v1/store/users/likes` | `get_list_of_components_liked_by_user` | `src/backend/base/langflow/api/v1/store.py` |
| POST | `/api/v1/store/users/likes/{component_id}` | `like_component` | `src/backend/base/langflow/api/v1/store.py` |

#### Validation
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| POST | `/api/v1/validate/code` | `post_validate_code` | `src/backend/base/langflow/api/v1/validate.py` |
| POST | `/api/v1/validate/prompt` | `post_validate_prompt` | `src/backend/base/langflow/api/v1/validate.py` |

#### Base Endpoints
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| GET | `/api/v1/all` | `get_all` | `src/backend/base/langflow/api/v1/endpoints.py` |
| POST | `/api/v1/run/{flow_id_or_name}` | `simplified_run_flow` | `src/backend/base/langflow/api/v1/endpoints.py` |
| POST | `/api/v1/webhook/{flow_id_or_name}` | `webhook_run_flow` | `src/backend/base/langflow/api/v1/endpoints.py` |
| GET | `/api/v1/task/{_task_id}` | `get_task_status` | `src/backend/base/langflow/api/v1/endpoints.py` |
| GET | `/api/v1/version` | `get_version` | `src/backend/base/langflow/api/v1/endpoints.py` |
| POST | `/api/v1/custom_component` | `custom_component` | `src/backend/base/langflow/api/v1/endpoints.py` |
| POST | `/api/v1/custom_component/update` | `custom_component_update` | `src/backend/base/langflow/api/v1/endpoints.py` |
| GET | `/api/v1/config` | `get_config` | `src/backend/base/langflow/api/v1/endpoints.py` |

#### Voice Mode
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| GET | `/api/v1/voice/elevenlabs/voice_ids` | `get_elevenlabs_voice_ids` | `src/backend/base/langflow/api/v1/voice_mode.py` |

#### MCP (Model Context Protocol)
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| GET | `/api/v1/mcp/sse` | `handle_sse` | `src/backend/base/langflow/api/v1/mcp.py` |
| POST | `/api/v1/mcp/` | `handle_messages` | `src/backend/base/langflow/api/v1/mcp.py` |

#### MCP Projects
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| GET | `/api/v1/mcp/project/{project_id}` | `list_project_tools` | `src/backend/base/langflow/api/v1/mcp_projects.py` |
| GET | `/api/v1/mcp/project/{project_id}/sse` | `handle_project_sse` | `src/backend/base/langflow/api/v1/mcp_projects.py` |
| POST | `/api/v1/mcp/project/{project_id}` | `handle_project_messages` | `src/backend/base/langflow/api/v1/mcp_projects.py` |
| POST | `/api/v1/mcp/project/{project_id}/` | `handle_project_messages_with_slash` | `src/backend/base/langflow/api/v1/mcp_projects.py` |
| PATCH | `/api/v1/mcp/project/{project_id}` | `update_project_mcp_settings` | `src/backend/base/langflow/api/v1/mcp_projects.py` |
| POST | `/api/v1/mcp/project/{project_id}/install` | `install_mcp_config` | `src/backend/base/langflow/api/v1/mcp_projects.py` |
| GET | `/api/v1/mcp/project/{project_id}/installed` | `check_installed_mcp_servers` | `src/backend/base/langflow/api/v1/mcp_projects.py` |

#### Starter Projects
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| GET | `/api/v1/starter-projects/` | `get_starter_projects` | `src/backend/base/langflow/api/v1/starter_projects.py` |

#### Folders (Legacy - redirects to projects)
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| POST | `/api/v1/folders/` | `create_folder_redirect` | `src/backend/base/langflow/api/v1/folders.py` |
| GET | `/api/v1/folders/` | `read_folders_redirect` | `src/backend/base/langflow/api/v1/folders.py` |
| GET | `/api/v1/folders/{folder_id}` | `read_folder_redirect` | `src/backend/base/langflow/api/v1/folders.py` |
| PATCH | `/api/v1/folders/{folder_id}` | `update_folder_redirect` | `src/backend/base/langflow/api/v1/folders.py` |
| DELETE | `/api/v1/folders/{folder_id}` | `delete_folder_redirect` | `src/backend/base/langflow/api/v1/folders.py` |
| GET | `/api/v1/folders/download/{folder_id}` | `download_file_redirect` | `src/backend/base/langflow/api/v1/folders.py` |
| POST | `/api/v1/folders/upload/` | `upload_file_redirect` | `src/backend/base/langflow/api/v1/folders.py` |

### API V2 Endpoints (15 endpoints total)

#### Files V2
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| POST | `/api/v2/files` | `upload_user_file` | `src/backend/base/langflow/api/v2/files.py` |
| POST | `/api/v2/files/` | `upload_user_file` | `src/backend/base/langflow/api/v2/files.py` |
| GET | `/api/v2/files` | `list_files` | `src/backend/base/langflow/api/v2/files.py` |
| GET | `/api/v2/files/` | `list_files` | `src/backend/base/langflow/api/v2/files.py` |
| DELETE | `/api/v2/files/batch/` | `delete_files_batch` | `src/backend/base/langflow/api/v2/files.py` |
| POST | `/api/v2/files/batch/` | `download_files_batch` | `src/backend/base/langflow/api/v2/files.py` |
| GET | `/api/v2/files/{file_id}` | `download_file` | `src/backend/base/langflow/api/v2/files.py` |
| PUT | `/api/v2/files/{file_id}` | `edit_file_name` | `src/backend/base/langflow/api/v2/files.py` |
| DELETE | `/api/v2/files/{file_id}` | `delete_file` | `src/backend/base/langflow/api/v2/files.py` |
| DELETE | `/api/v2/files` | `delete_all_files` | `src/backend/base/langflow/api/v2/files.py` |
| DELETE | `/api/v2/files/` | `delete_all_files` | `src/backend/base/langflow/api/v2/files.py` |

#### MCP V2
| Method | Path | Function | Source File |
|--------|------|----------|-------------|
| GET | `/api/v2/mcp/servers` | `get_servers` | `src/backend/base/langflow/api/v2/mcp.py` |
| GET | `/api/v2/mcp/servers/{server_name}` | `get_server_endpoint` | `src/backend/base/langflow/api/v2/mcp.py` |
| POST | `/api/v2/mcp/servers/{server_name}` | `add_server` | `src/backend/base/langflow/api/v2/mcp.py` |
| PATCH | `/api/v2/mcp/servers/{server_name}` | `update_server_endpoint` | `src/backend/base/langflow/api/v2/mcp.py` |
| DELETE | `/api/v2/mcp/servers/{server_name}` | `delete_server` | `src/backend/base/langflow/api/v2/mcp.py` |

## RBAC Dual Routing Details

The RBAC system implements dual routing for backward compatibility:

### Unified RBAC Routing (`/api/v1/rbac/`)
All RBAC endpoints are available under the unified prefix for consistent access:
- `/api/v1/rbac/workspaces/`
- `/api/v1/rbac/roles/`
- `/api/v1/rbac/permissions/`
- `/api/v1/rbac/projects/`
- `/api/v1/rbac/environments/`
- `/api/v1/rbac/audit/`
- `/api/v1/rbac/role-assignments/`
- `/api/v1/rbac/service-accounts/`
- `/api/v1/rbac/user-groups/`

### Individual Resource Routing
For backward compatibility, core RBAC resources are also available directly under `/api/v1/`:
- `/api/v1/workspaces/`
- `/api/v1/roles/`
- `/api/v1/permissions/`
- `/api/v1/projects/` (legacy, some overlap with RBAC projects)

This dual routing ensures existing integrations continue to work while providing a unified RBAC API structure for new implementations.