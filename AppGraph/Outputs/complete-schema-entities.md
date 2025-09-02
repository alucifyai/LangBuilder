# Complete LangBuilder Schema Entities

Based on deep code analysis of the LangBuilder database models, here are all the schema entities with their complete attributes.

**Last Updated:** Based on codebase analysis including MCP support, Voice Mode, and File V2 features.

## Core Entities

### 1. User
**Path:** `src/backend/base/langflow/services/database/models/user/model.py`
```graphql
type User {
  id: UUID! @primary
  username: String! @unique @indexed
  password: String!
  profile_image: String
  is_active: Boolean! @default(false)
  is_superuser: Boolean! @default(false)
  create_at: DateTime! @default(now)
  updated_at: DateTime! @default(now)
  last_login_at: DateTime
  store_api_key: String
  optins: JSON @default({
    github_starred: false,
    dialog_dismissed: false,
    discord_clicked: false
  })
  
  # Relationships
  api_keys: [ApiKey!]! @cascade(delete)
  flows: [Flow!]!
  variables: [Variable!]! @cascade(delete)
  folders: [Folder!]! @cascade(delete)
}
```

### 2. ApiKey
**Path:** `src/backend/base/langflow/services/database/models/api_key/model.py`
```graphql
type ApiKey {
  id: UUID! @primary
  name: String @indexed
  api_key: String! @unique @indexed
  created_at: DateTime! @default(now)
  last_used_at: DateTime
  total_uses: Int! @default(0)
  is_active: Boolean! @default(true)
  
  # Foreign Keys
  user_id: UUID! @indexed @foreign(user.id)
  user: User!
}
```

### 3. Flow
**Path:** `src/backend/base/langflow/services/database/models/flow/model.py`
```graphql
type Flow {
  id: UUID! @primary
  name: String! @indexed
  description: String @indexed
  data: JSON  # Contains nodes and edges structure
  icon: String  # Emoji or lucide icon
  icon_bg_color: String  # Hex color starting with #
  gradient: String
  is_component: Boolean @default(false)
  updated_at: DateTime @default(now)
  webhook: Boolean @default(false)
  endpoint_name: String @unique @indexed  # Alphanumeric with hyphens/underscores
  tags: [String!] @default([])
  locked: Boolean @default(false)
  mcp_enabled: Boolean @default(false)  # MCP server exposure
  action_name: String
  action_description: String
  access_type: AccessTypeEnum! @default(PRIVATE)  # PRIVATE or PUBLIC
  fs_path: String  # File system path
  
  # Foreign Keys
  user_id: UUID @indexed @foreign(user.id)
  user: User!
  folder_id: UUID @indexed @foreign(folder.id)
  folder: Folder
  
  # Unique Constraints
  @unique([user_id, name])
  @unique([user_id, endpoint_name])
}
```

### 4. Folder
**Path:** `src/backend/base/langflow/services/database/models/folder/model.py`
```graphql
type Folder {
  id: UUID! @primary
  name: String! @indexed
  description: String
  auth_settings: JSON  # Authentication settings for the folder/project
  
  # Foreign Keys
  parent_id: UUID @foreign(folder.id)
  parent: Folder
  user_id: UUID @foreign(user.id)
  user: User!
  
  # Relationships
  children: [Folder!]!
  flows: [Flow!]! @cascade(delete)
  
  # Unique Constraints
  @unique([user_id, name])
}
```

### 5. Variable
**Path:** `src/backend/base/langflow/services/database/models/variable/model.py`
```graphql
type Variable {
  id: UUID! @primary
  name: String!
  value: String! @encrypted  # Encrypted value
  type: String  # e.g., "CREDENTIAL"
  default_fields: [String!]
  created_at: DateTime @default(now)
  updated_at: DateTime
  
  # Foreign Keys
  user_id: UUID! @foreign(user.id)
  user: User!
}
```

### 6. Message
**Path:** `src/backend/base/langflow/services/database/models/message/model.py`
```graphql
type Message {
  id: UUID! @primary
  timestamp: DateTime! @default(now)
  sender: String!
  sender_name: String!
  session_id: String!
  text: String!
  files: [String!] @default([])
  error: Boolean! @default(false)
  edit: Boolean! @default(false)
  properties: JSON  # Properties object
  category: String! @default("message")
  content_blocks: [JSON!] @default([])
  
  # Foreign Keys
  flow_id: UUID @foreign(flow.id)
}
```

### 7. Transaction
**Path:** `src/backend/base/langflow/services/database/models/transactions/model.py`
```graphql
type Transaction {
  id: UUID! @primary
  timestamp: DateTime! @default(now)
  vertex_id: String!  # ID of the vertex/node in the flow
  target_id: String
  inputs: JSON  # Serialized with length limits
  outputs: JSON  # Serialized with length limits
  status: String!
  error: String
  
  # Foreign Keys
  flow_id: UUID! @foreign(flow.id)
}
```

### 8. VertexBuild
**Path:** `src/backend/base/langflow/services/database/models/vertex_builds/model.py`
```graphql
type VertexBuild {
  build_id: UUID! @primary
  id: String!  # Vertex/component ID
  timestamp: DateTime! @default(now)
  data: JSON  # Serialized with limits
  artifacts: JSON  # Serialized with limits
  params: String  # Serialized parameters
  valid: Boolean!
  
  # Foreign Keys
  flow_id: UUID! @foreign(flow.id)
}
```

### 9. File
**Path:** `src/backend/base/langflow/services/database/models/file/model.py`
**Note:** Part of File Management V2 system
```graphql
type File {
  id: UUID! @primary
  name: String! @unique
  path: String!
  size: Int!
  provider: String  # Storage provider (e.g., 'local', 's3')
  created_at: DateTime! @default(now)
  updated_at: DateTime! @default(now)
  
  # Foreign Keys
  user_id: UUID! @foreign(user.id)
  user: User!
}
```

## Additional Entities Not in Original App Graph

### 10. Component (Runtime Entity)
**Note:** Not a database entity but a core runtime concept
```graphql
type Component {
  display_name: String!
  description: String!
  icon: String
  category: ComponentCategory!
  inputs: [ComponentInput!]!
  outputs: [ComponentOutput!]!
  code: String!
  template: JSON
  documentation: String
  beta: Boolean!
  experimental: Boolean!
}

enum ComponentCategory {
  INPUT_OUTPUT
  TEXT_PROCESSING
  AGENTS
  CHAINS
  DATA
  EMBEDDINGS
  LLMS
  MEMORIES
  TOOLS
  RETRIEVERS
  LOGIC
  HELPERS
  CUSTOM
}
```

### 11. Vertex (Graph Runtime Entity)
**Note:** Runtime representation of a node in the flow graph
```graphql
type Vertex {
  id: String!
  display_name: String!
  description: String
  base_type: ComponentType!
  inputs: [VertexInput!]!
  outputs: [VertexOutput!]!
  params: JSON
  frozen: Boolean!
  is_input: Boolean!
  is_output: Boolean!
  is_state: Boolean!
  edges: [Edge!]!
}
```

### 12. Edge (Graph Runtime Entity)
**Note:** Runtime representation of connections between vertices
```graphql
type Edge {
  id: String!
  source: Vertex!
  target: Vertex!
  source_handle: String!
  target_handle: String!
  data: JSON
}
```

## Key Updates from Analysis

1. **File Entity Added**: Now includes the File Management V2 entity
2. **MCP Support Fields**: Flow entity includes `mcp_enabled`, `action_name`, `action_description`
3. **Access Control**: Flow has `access_type` enum (PRIVATE/PUBLIC)
4. **Project Settings**: Folder entity has `auth_settings` for project-level configuration
5. **Voice Mode Support**: Message entity supports rich content via `content_blocks`
6. **Runtime Entities**: Added Component, Vertex, and Edge as important runtime concepts

## Relationships Summary

- User → ApiKey (1:many, cascade delete)
- User → Flow (1:many)
- User → Variable (1:many, cascade delete)
- User → Folder (1:many, cascade delete)
- User → File (1:many)
- Folder → Flow (1:many, cascade delete)
- Folder → Folder (self-referential parent-child)
- Flow → Transaction (1:many)
- Flow → VertexBuild (1:many)
- Flow → Message (1:many)

## Service Layer Entities (Not in Database)

These services manage the runtime behavior and are implemented using the Service Factory pattern:

### Core Services
- **SessionService**: Manages user sessions and WebSocket connections
- **StateService**: Manages flow execution state (in-memory or persistent)
- **StorageService**: Handles file storage (local filesystem or S3)
- **TaskService**: Background task management and execution
- **SocketIOService**: WebSocket/SSE real-time communication
- **TelemetryService**: Usage tracking and analytics
- **VariableService**: Manages encrypted variables and secrets
- **CacheService**: Caching layer for performance optimization

### MCP-Specific Services
- **MCPServer**: Model Context Protocol server implementation
- **MCPProjectServer**: Per-project MCP server instances
- **MCPTransport**: SSE/WebSocket transport for MCP communication

### Voice Mode Services
- **VoiceHandler**: WebSocket handler for voice streaming
- **AudioProcessor**: VAD and audio resampling (24kHz to 16kHz)
- **RealtimeAPIClient**: OpenAI Realtime API integration
- **ElevenLabsClient**: Voice synthesis integration

## Notes on RBAC Schema (Future Implementation)

When RBAC is implemented, these additional entities would be needed:
- Role (with permissions array)
- Permission (resource, action pairs)
- RoleAssignment (links users/groups to roles with scope)
- Group (collection of users)
- ServiceAccount (for programmatic access)
- AuditLog (for compliance tracking)