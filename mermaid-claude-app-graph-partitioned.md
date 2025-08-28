%% Partitioned (base)
```mermaid
graph LR
    subgraph ss001["User Management & Authentication"]
        ns0001["User
(schema)
Central user entity managing authentication and authorization"]
        ns0002["ApiKey
(schema)
API authentication tokens for programmatic access"]
        ns0003["Variable
(schema)
Secure storage for environment variables and secrets"]
        ni0001["LoginPage
(interface)
User authentication interface"]
        ni0002["UserSettingsPage
(interface)
User profile and configuration management"]
        ni0003["ApiKeysManagement
(interface)
API key creation and management interface"]
        nl0001["AuthenticationService
(logic)
Handles user login, logout, and session management"]
        nl0002["ApiKeyManagement
(logic)
Creates, validates, and manages API keys"]
        nt0001["UserAuthentication
(test)
User can successfully log in and access protected resources"]
        ns0001 -->|owns| ns0002
        ns0001 -->|has| ns0003
        ni0001 --> nl0001
        ni0003 --> ns0002
        ni0002 --> nl0001
        ni0003 --> nl0002
        nl0001 --> ns0001
        nl0002 --> ns0002
        nt0001 --> ni0001
        nt0001 --> nl0001
        nt0001 --> ns0001
    end
    subgraph ss002["Flow Management & Execution"]
        ns0004["Flow
(schema)
AI workflow configuration with visual node graph"]
        ns0005["Folder
(schema)
Hierarchical organization for flows"]
        ns0006["Transaction
(schema)
Execution audit trail for flow runs"]
        ni0004["FlowEditor
(interface)
Visual node-based flow builder interface"]
        ni0005["FlowDashboard
(interface)
Flow collection management interface"]
        nl0003["FlowExecutionEngine
(logic)
Processes flow graphs and executes components"]
        nl0004["ComponentRegistry
(logic)
Manages component discovery, loading, and instantiation"]
        nt0002["FlowExecution
(test)
Flow executes successfully with proper data flow"]
        ns0005 -->|contains| ns0004
        ns0004 -->|generates| ns0006
        ni0004 --> ns0004
        ni0004 --> nl0003
        ni0005 --> ns0004
        ni0005 --> ns0005
        nl0003 --> ns0004
        nl0003 --> ns0006
        nl0004 --> ns0004
        nt0002 --> ni0004
        nt0002 --> nl0003
        nt0002 --> ns0004
        nt0002 --> ns0006
    end
    subgraph ss003["Chat & Messaging Interface"]
        ns0007["Message
(schema)
Chat message with metadata and attachments"]
        ns0008["File
(schema)
Uploaded file metadata and storage"]
        ni0006["PlaygroundInterface
(interface)
Interactive chat testing environment"]
        nl0005["ChatService
(logic)
Manages chat sessions and message streaming"]
        nt0003["ChatInteraction
(test)
User can send messages and receive responses"]
        ni0006 --> ns0007
        ni0006 --> nl0005
        ni0006 --> ns0008
        nl0005 --> ns0007
        nl0005 --> ns0008
        nt0003 --> ni0006
        nt0003 --> nl0005
        nt0003 --> ns0007
    end
    subgraph ss004["Component Library & Integrations"]
        ns0009["Component
(schema)
Reusable workflow component definition"]
        ns0010["VertexBuild
(schema)
Component build and validation artifacts"]
        ni0007["ComponentLibrary
(interface)
Component browsing and management interface"]
        nl0006["ComponentExecutor
(logic)
Executes individual components with their logic"]
        nt0004["ComponentExecution
(test)
Components execute correctly with valid inputs"]
        ns0009 -->|creates| ns0010
        ni0007 --> ns0009
        ni0007 --> ns0010
        nl0006 --> ns0009
        nl0006 --> ns0010
        nt0004 --> ni0007
        nt0004 --> nl0006
        nt0004 --> ns0009
        nt0004 --> ns0010
    end
    ns0001 -. |user owns flows| .-> ns0004
    ns0001 -. |user owns folders| .-> ns0005
    ns0002 -. |API key access| .-> nl0003
    ni0006 -. |chat triggers flow| .-> nl0003
    nl0003 -. |executes components| .-> nl0006
    nl0004 -. |loads components| .-> ns0009
    nl0003 -. |execution creates messages| .-> ns0007
    ns0001 -. |user owns files| .-> ns0008
    nl0005 -. |chat uses execution| .-> nl0003
    ns0007 -. |message references flow| .-> ns0004
    ```
