%% LangBuilder v1.5 (base)
```mermaid
graph LR
    ns0001["User
(schema)
Central user entity managing authentication and authorization"]
    ns0002["ApiKey
(schema)
API authentication tokens for programmatic access"]
    ns0003["Variable
(schema)
Secure storage for environment variables and secrets"]
    ns0004["Flow
(schema)
AI workflow configuration with visual node graph"]
    ns0005["Folder
(schema)
Hierarchical organization for flows"]
    ns0006["Transaction
(schema)
Execution audit trail for flow runs"]
    ns0007["Message
(schema)
Chat message with metadata and attachments"]
    ns0008["File
(schema)
Uploaded file metadata and storage"]
    ns0009["Component
(schema)
Reusable workflow component definition"]
    ns0010["VertexBuild
(schema)
Component build and validation artifacts"]
    ni0001["LoginPage
(interface)
User authentication interface"]
    ni0002["UserSettingsPage
(interface)
User profile and configuration management"]
    ni0003["ApiKeysManagement
(interface)
API key creation and management interface"]
    ni0004["FlowEditor
(interface)
Visual node-based flow builder interface"]
    ni0005["FlowDashboard
(interface)
Flow collection management interface"]
    ni0006["PlaygroundInterface
(interface)
Interactive chat testing environment"]
    ni0007["ComponentLibrary
(interface)
Component browsing and management interface"]
    nl0001["AuthenticationService
(logic)
Handles user login, logout, and session management"]
    nl0002["ApiKeyManagement
(logic)
Creates, validates, and manages API keys"]
    nl0003["FlowExecutionEngine
(logic)
Processes flow graphs and executes components"]
    nl0004["ComponentRegistry
(logic)
Manages component discovery, loading, and instantiation"]
    nl0005["ChatService
(logic)
Manages chat sessions and message streaming"]
    nl0006["ComponentExecutor
(logic)
Executes individual components with their logic"]
    nt0001["UserAuthentication
(test)
User can successfully log in and access protected resources"]
    nt0002["FlowExecution
(test)
Flow executes successfully with proper data flow"]
    nt0003["ChatInteraction
(test)
User can send messages and receive responses"]
    nt0004["ComponentExecution
(test)
Components execute correctly with valid inputs"]
    ns0001 -->|owns| ns0002
    ns0001 -->|has| ns0003
    ns0001 -->|creates| ns0004
    ns0001 -->|owns| ns0005
    ns0001 -->|uploads| ns0008
    ns0005 -->|contains| ns0004
    ns0004 -->|generates| ns0006
    ns0004 -->|creates| ns0010
    ns0009 -->|produces| ns0010
    ni0001 --> nl0001
    ni0002 --> nl0001
    ni0003 --> ns0002
    ni0003 --> nl0002
    ni0004 --> ns0004
    ni0004 --> nl0003
    ni0005 --> ns0004
    ni0005 --> ns0005
    ni0006 --> ns0007
    ni0006 --> ns0008
    ni0006 --> nl0005
    ni0007 --> ns0009
    nl0003 --> nl0004
    nl0004 --> nl0006
    nl0005 --> nl0003
    nl0002 --> ns0002
    nl0003 --> ns0006
    nl0001 --> ns0001
    nl0003 --> ns0004
    nl0004 --> ns0009
    nl0005 --> ns0007
    ni0001 -->|redirects| ni0005
    ni0004 -->|opens| ni0006
    nt0001 -->|tests| ni0001
    nt0001 -->|tests| nl0001
    nt0001 -->|tests| ns0001
    nt0002 -->|tests| nl0003
    nt0002 -->|tests| ni0004
    nt0002 -->|tests| ns0004
    nt0003 -->|tests| nl0005
    nt0003 -->|tests| ni0006
    nt0003 -->|tests| ns0007
    nt0004 -->|tests| nl0006
    nt0004 -->|tests| ni0007
    nt0004 -->|tests| ns0009
    ```
