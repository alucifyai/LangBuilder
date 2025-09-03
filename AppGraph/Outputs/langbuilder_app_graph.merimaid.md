```mermaid
%% LangBuilder Complete Application Graph v2.2.0
graph LR
    user_entity["User\n(schema)\nUser entity with authentication, profile management, and system access control"]
    api_key_entity["ApiKey\n(schema)\nAPI authentication credentials for external system access and integration"]
    flow_entity["Flow\n(schema)\nAI workflow definition with components, execution logic, and MCP integration support"]
    folder_entity["Folder\n(schema)\nHierarchical folder organization system for flows and project management"]
    variable_entity["Variable\n(schema)\nEncrypted variable storage for credentials and sensitive configuration data"]
    message_entity["Message\n(schema)\nChat message storage with support for rich content, files, and voice mode integration"]
    transaction_entity["Transaction\n(schema)\nFlow execution transaction logging with input/output tracking and performance monitoring"]
    vertex_build_entity["VertexBuild\n(schema)\nComponent build artifacts and execution state tracking for flow vertices"]
    file_entity["File\n(schema)\nFile management system V2 with storage provider support and user association"]
    component_entity["Component\n(schema)\nRuntime component definition with template, documentation, and lifecycle management"]
    vertex_entity["Vertex\n(schema)\nGraph runtime representation of flow nodes with state management and edge connections"]
    edge_entity["Edge\n(schema)\nGraph runtime representation of connections between vertices with data flow management"]
    credential_entity["Credential\n(schema)\nSecure credential management for API keys, tokens, and authentication data"]
    store_entity["Store\n(schema)\nComponent marketplace integration with sharing, discovery, and rating capabilities"]
    global_variable_entity["GlobalVariable\n(schema)\nSystem-wide configuration variables and environment settings management"]
    login_page["LoginPage\n(interface)\nUser authentication interface with credential validation and auto-login support"]
    flow_dashboard["FlowDashboard\n(interface)\nMain application dashboard with flow management, search, and folder navigation"]
    flow_editor["FlowEditor\n(interface)\nVisual flow builder with drag-and-drop components, real-time collaboration, and execution monitoring"]
    playground_interface["PlaygroundInterface\n(interface)\nInteractive chat interface for testing flows with voice mode, file attachments, and session management"]
    component_sidebar["ComponentSidebar\n(interface)\nCollapsible sidebar with component library, search, and drag-to-canvas functionality"]
    flow_toolbar["FlowToolbar\n(interface)\nAction toolbar with save, build, run, share, and settings controls"]
    reactflow_canvas["ReactFlowCanvas\n(interface)\nMain canvas area for visual flow building with node manipulation and connection handling"]
    io_modal["IOModal\n(interface)\nPlayground modal for flow testing with input fields, output display, and chat interface"]
    message_list["MessageList\n(interface)\nScrollable message container with rich content rendering, streaming support, and voice integration"]
    chat_input["ChatInput\n(interface)\nMulti-modal input interface with text, file attachments, voice recording, and send controls"]
    voice_assistant["VoiceAssistant\n(interface)\nVoice interaction component with real-time audio processing, VAD, and provider selection"]
    folder_sidebar["FolderSidebar\n(interface)\nHierarchical folder navigation with create, rename, delete, and drag-drop organization"]
    flow_grid["FlowGrid\n(interface)\nResponsive grid display of flows with cards, thumbnails, actions, and bulk operations"]
    component_grid["ComponentGrid\n(interface)\nComponent marketplace display with search, filtering, ratings, and installation"]
    mcp_server_tab["MCPServerTab\n(interface)\nMCP server management interface with server configuration, tool discovery, and execution monitoring"]
    add_mcp_server_modal["AddMCPServerModal\n(interface)\nModal dialog for adding new MCP servers with configuration validation and connection testing"]
    settings_page["SettingsPage\n(interface)\nUser settings management with tabs for general, API keys, global variables, and MCP servers"]
    api_keys_settings["ApiKeysSettings\n(interface)\nAPI key management interface with creation, deletion, usage tracking, and security controls"]
    global_variables_settings["GlobalVariablesSettings\n(interface)\nGlobal variable management with encryption, scoping, and environment-specific configurations"]
    file_management_page["FileManagementPage\n(interface)\nFile management interface with upload, download, search, and organization capabilities"]
    admin_page["AdminPage\n(interface)\nSystem administration interface with user management, system monitoring, and configuration"]
    store_page["StorePage\n(interface)\nComponent marketplace with browsing, search, ratings, and community-driven content discovery"]
    header_component["HeaderComponent\n(interface)\nApplication header with navigation, user profile, notifications, and theme controls"]
    notification_system["NotificationSystem\n(interface)\nReal-time notification display with toasts, badges, and persistent notification center"]
    error_boundary["ErrorBoundary\n(interface)\nApplication-wide error handling with user-friendly error displays and recovery options"]
    loading_states["LoadingStates\n(interface)\nComprehensive loading state management with skeletons, spinners, and progress indicators"]
    theme_provider["ThemeProvider\n(interface)\nApplication theme management with light/dark modes, custom themes, and responsive design tokens"]
    auth_guard["AuthGuard\n(interface)\nRoute protection and authentication state management with automatic redirects and session handling"]
    websocket_manager["WebSocketManager\n(interface)\nReal-time communication management with connection pooling, reconnection logic, and event routing"]
    data_table["DataTable\n(interface)\nAdvanced data table with sorting, filtering, pagination, and export capabilities"]
    form_builder["FormBuilder\n(interface)\nDynamic form generation with validation, conditional fields, and custom input types"]
    code_editor["CodeEditor\n(interface)\nIntegrated code editor with syntax highlighting, auto-completion, and debugging support"]
    search_interface["SearchInterface\n(interface)\nGlobal search functionality with autocomplete, filters, and result categorization"]
    paginator_component["PaginatorComponent\n(interface)\nAdvanced pagination component with page size selection, navigation, and total count display"]
    template_gallery["TemplateGallery\n(interface)\nTemplate selection interface with categories, previews, and quick start functionality"]
    workspace_switcher["WorkspaceSwitcher\n(interface)\nMulti-workspace management with workspace selection, creation, and switching capabilities"]
    application_lifecycle["Application Lifecycle Management\n(logic)\nCore application startup, initialization, and shutdown orchestration with service management"]
    flow_execution_engine["Flow Execution Engine\n(logic)\nGraph-based flow execution with dependency resolution, parallel processing, and state management"]
    job_queue_system["Asynchronous Job Queue System\n(logic)\nBackground job processing with event streaming, cancellation support, and resource management"]
    authentication_system["Authentication and Authorization System\n(logic)\nJWT-based authentication with API key support, session management, and user isolation"]
    real_time_event_system["Real-time Event Management System\n(logic)\nEvent-driven architecture with WebSocket/SSE support, queue management, and delivery guarantees"]
    component_management["Component Lifecycle Management\n(logic)\nDynamic component loading, caching, validation, and execution with hot-reloading support"]
    graph_state_management["Graph State Management\n(logic)\nVertex state tracking, dependency resolution, and execution coordination with cycle detection"]
    validation_engine["Multi-layer Validation Engine\n(logic)\nComprehensive input validation with schema validation, business rules, and data integrity checks"]
    caching_system["Multi-level Caching System\n(logic)\nHierarchical caching with TTL management, cache invalidation, and performance optimization"]
    error_handling_system["Comprehensive Error Handling System\n(logic)\nMulti-level error handling with recovery strategies, logging, and user feedback"]
    security_access_control["Security and Access Control System\n(logic)\nComprehensive security with RBAC, data isolation, input sanitization, and audit logging"]
    websocket_sse_communication["WebSocket and SSE Communication System\n(logic)\nReal-time bidirectional communication with connection management, heartbeats, and failover"]
    frontend_state_management["Frontend State Management System\n(logic)\nZustand-based state management with cross-store communication, persistence, and synchronization"]
    mcp_integration_system["Model Context Protocol Integration System\n(logic)\nMCP server management, tool discovery, and execution coordination with per-project isolation"]
    voice_mode_system["Voice Mode Processing System\n(logic)\nReal-time voice processing with VAD, audio resampling, and multi-provider support"]
    file_management_system["File Management System V2\n(logic)\nAdvanced file handling with storage providers, metadata management, and security controls"]
    store_integration_system["Component Store Integration System\n(logic)\nMarketplace functionality with component sharing, discovery, ratings, and installation"]
    telemetry_analytics_system["Telemetry and Analytics System\n(logic)\nUsage tracking, performance monitoring, and analytics collection with privacy controls"]
    session_management_system["Session Management System\n(logic)\nMulti-session support with state persistence, cleanup, and real-time synchronization"]
    api_versioning_system["API Versioning and Compatibility System\n(logic)\nAPI version management with backward compatibility, deprecation handling, and migration support"]
    dependency_injection_system["Service Dependency Injection System\n(logic)\nService factory pattern with dependency resolution, lifecycle management, and health monitoring"]
    configuration_management["Configuration Management System\n(logic)\nEnvironment-based configuration with hot-reloading, validation, and security controls"]
    logging_monitoring_system["Comprehensive Logging and Monitoring System\n(logic)\nStructured logging with distributed tracing, metrics collection, and alerting capabilities"]
    testing_quality_assurance["Testing and Quality Assurance System\n(logic)\nComprehensive testing framework with unit, integration, E2E, and performance testing capabilities"]
    deployment_orchestration["Deployment Orchestration System\n(logic)\nMulti-environment deployment with Docker containerization, health checks, and rollback capabilities"]
    flow_management_tests["Flow Management Test Suite\n(test)\nComprehensive testing of flow CRUD operations, validation, and user isolation"]
    authentication_authorization_tests["Authentication and Authorization Test Suite\n(test)\nJWT authentication, API key validation, session management, and security boundary testing"]
    graph_execution_tests["Graph Execution Engine Test Suite\n(test)\nGraph building, vertex execution, dependency resolution, and cycle detection testing"]
    component_integration_tests["Component Integration Test Suite\n(test)\nDynamic component loading, template validation, execution, and lifecycle management"]
    real_time_communication_tests["Real-time Communication Test Suite\n(test)\nWebSocket/SSE functionality, event streaming, and connection management testing"]
    job_queue_tests["Asynchronous Job Queue Test Suite\n(test)\nBackground job processing, event streaming, cancellation, and resource cleanup testing"]
    validation_engine_tests["Multi-layer Validation Engine Test Suite\n(test)\nSchema validation, business rule enforcement, and data integrity checking"]
    caching_system_tests["Multi-level Caching System Test Suite\n(test)\nCache hit/miss behavior, TTL management, invalidation strategies, and performance optimization"]
    error_handling_tests["Comprehensive Error Handling Test Suite\n(test)\nError classification, recovery strategies, user feedback, and system stability testing"]
    security_access_control_tests["Security and Access Control Test Suite\n(test)\nRBAC enforcement, data isolation, input sanitization, and security boundary testing"]
    mcp_integration_tests["MCP Integration Test Suite\n(test)\nMCP server management, tool discovery, execution coordination, and security validation"]
    voice_mode_tests["Voice Mode Processing Test Suite\n(test)\nAudio processing, VAD detection, provider integration, and real-time communication testing"]
    file_management_tests["File Management System Test Suite\n(test)\nFile upload, storage provider integration, metadata management, and security validation"]
    frontend_ui_tests["Frontend UI Component Test Suite\n(test)\nReact component behavior, state management, user interactions, and responsive design testing"]
    e2e_workflow_tests["End-to-End Workflow Test Suite\n(test)\nComplete user journey testing from login to flow execution with real-world scenarios"]
    performance_benchmark_tests["Performance and Load Testing Suite\n(test)\nSystem performance under load, resource utilization, and scalability validation"]
    api_integration_tests["API Integration Test Suite\n(test)\nREST API functionality, request/response validation, error handling, and versioning support"]
    database_integration_tests["Database Integration Test Suite\n(test)\nDatabase operations, transaction management, data integrity, and migration testing"]
    deployment_validation_tests["Deployment and Infrastructure Test Suite\n(test)\nContainer deployment, service discovery, health checks, and production readiness validation"]
    regression_test_suite["Regression Test Suite\n(test)\nAutomated regression testing to prevent feature breakage and ensure backward compatibility"]
    user_entity -->|owns| api_key_entity
    user_entity -->|creates| flow_entity
    user_entity -->|organizes| folder_entity
    user_entity -->|manages| variable_entity
    user_entity -->|uploads| file_entity
    folder_entity -->|contains| flow_entity
    flow_entity -->|generates| transaction_entity
    flow_entity -->|builds| vertex_build_entity
    flow_entity -->|processes| message_entity
    vertex_entity -->|connects| edge_entity
    login_page -->|redirects| flow_dashboard
    flow_dashboard -->|opens| flow_editor
    flow_dashboard -->|launches| playground_interface
    flow_dashboard -->|settings| settings_page
    flow_editor -->|tests| playground_interface
    settings_page -->|manages| file_management_page
    flow_dashboard -->|browses| store_page
    flow_editor -->|imports| store_page
    flow_dashboard -->|displays| flow_entity
    flow_editor -->|saves| flow_entity
    flow_editor -->|loads| component_entity
    playground_interface -->|creates| message_entity
    component_sidebar -->|lists| component_entity
    reactflow_canvas -->|renders| vertex_entity
    application_lifecycle -->|requires| authentication_system
    flow_execution_engine -->|loads| component_management
    flow_execution_engine -->|tracks| graph_state_management
    job_queue_system -->|executes| flow_execution_engine
    authentication_system -->|enforces| security_access_control
    authentication_system -->|validates| user_entity
    real_time_event_system -->|transmits| websocket_sse_communication
    component_management -->|caches| caching_system
    graph_state_management -->|tracks| vertex_build_entity
    validation_engine -->|reports| error_handling_system
    caching_system -->|configures| configuration_management
    error_handling_system -->|logs| transaction_entity
    security_access_control -->|authorizes| user_entity
    websocket_sse_communication -->|transmits| message_entity
    frontend_state_management -->|syncs| flow_entity
    mcp_integration_system -->|extends| component_management
    voice_mode_system -->|streams| real_time_event_system
    file_management_system -->|secures| security_access_control
    store_integration_system -->|authenticates| authentication_system
    session_management_system -->|stores| caching_system
    flow_management_tests -->|tests| flow_entity
    authentication_authorization_tests -->|tests| user_entity
    graph_execution_tests -->|tests| vertex_entity
    component_integration_tests -->|tests| component_entity
    real_time_communication_tests -->|tests| message_entity
    job_queue_tests -->|tests| transaction_entity
    validation_engine_tests -->|tests| flow_entity
    caching_system_tests -->|tests| component_entity
    error_handling_tests -->|tests| transaction_entity
    security_access_control_tests -->|tests| user_entity
    mcp_integration_tests -->|tests| flow_entity
    voice_mode_tests -->|tests| message_entity
    file_management_tests -->|tests| file_entity
    frontend_ui_tests -->|tests| login_page
    e2e_workflow_tests -->|tests| flow_dashboard
    performance_benchmark_tests -->|tests| flow_execution_engine
    api_integration_tests -->|tests| flow_entity
    database_integration_tests -->|tests| user_entity
    deployment_validation_tests -->|tests| application_lifecycle
    regression_test_suite -->|tests| flow_entity
    folder_entity -->|parent_of| folder_entity
    user_entity -->|credentials| credential_entity
    user_entity -->|contributes| store_entity
    credential_entity -->|relates| variable_entity
    store_entity -->|contains| component_entity
    global_variable_entity -->|scoped_to| user_entity
    playground_interface -->|embeds| io_modal
    voice_assistant -->|enhances| chat_input
    folder_sidebar -->|filters| flow_grid
    component_sidebar -->|displays| component_grid
    mcp_server_tab -->|opens| add_mcp_server_modal
    settings_page -->|includes| api_keys_settings
    settings_page -->|includes| global_variables_settings
    header_component -->|displays| notification_system
    error_boundary -->|controls| loading_states
    theme_provider -->|themes| header_component
    auth_guard -->|protects| login_page
    websocket_manager -->|provides| real_time_event_system
    file_management_page -->|displays| data_table
    add_mcp_server_modal -->|uses| form_builder
    flow_dashboard -->|includes| search_interface
    flow_entity -->|contains| component_entity
    transaction_entity -->|tracks| vertex_entity
    message_entity -->|belongs_to| user_entity
    vertex_build_entity -->|references| component_entity
    file_entity -->|used_by| flow_entity
    api_key_entity -->|authorizes| transaction_entity
    variable_entity -->|used_in| flow_entity
    credential_entity -->|manages| api_key_entity
    store_entity -->|shares| flow_entity
    store_page -->|imports| flow_editor
    playground_interface -->|edits| flow_editor
    file_management_page -->|uses| flow_editor
    settings_page -->|admin| admin_page
    flow_dashboard -->|templates| template_gallery
    template_gallery -->|creates| flow_editor
    flow_editor -->|displays| reactflow_canvas
    flow_editor -->|includes| component_sidebar
    flow_editor -->|includes| flow_toolbar
    playground_interface -->|displays| message_list
    flow_dashboard -->|includes| workspace_switcher
    settings_page -->|includes| mcp_server_tab
    store_page -->|includes| paginator_component
    telemetry_analytics_system -->|aggregates| logging_monitoring_system
    dependency_injection_system -->|configures| configuration_management
    deployment_orchestration -->|validates| validation_engine
    settings_page -->|configures| api_key_entity
    settings_page -->|configures| variable_entity
    file_management_page -->|uploads| file_entity
    store_page -->|browses| store_entity
    login_page -->|authenticates| user_entity
    flow_execution_engine -->|records| transaction_entity
    job_queue_system -->|executes| vertex_build_entity
    voice_assistant -->|transcribes| message_entity
    mcp_integration_system -->|exposes| flow_entity
    admin_page -->|administers| user_entity
    user_entity -->|owns| api_key_entity
    user_entity -->|creates| flow_entity
    user_entity -->|organizes| folder_entity
    user_entity -->|manages| variable_entity
    user_entity -->|uploads| file_entity
    folder_entity -->|contains| flow_entity
    flow_entity -->|generates| transaction_entity
    flow_entity -->|builds| vertex_build_entity
    flow_entity -->|processes| message_entity
    vertex_entity -->|connects| edge_entity
    login_page -->|redirects| flow_dashboard
    flow_dashboard -->|opens| flow_editor
    flow_dashboard -->|launches| playground_interface
    flow_dashboard -->|settings| settings_page
    flow_editor -->|tests| playground_interface
    settings_page -->|manages| file_management_page
    flow_dashboard -->|browses| store_page
    flow_editor -->|imports| store_page
    flow_dashboard -->|displays| flow_entity
    flow_editor -->|saves| flow_entity
    flow_editor -->|loads| component_entity
    playground_interface -->|creates| message_entity
    component_sidebar -->|lists| component_entity
    reactflow_canvas -->|renders| vertex_entity
    application_lifecycle -->|requires| authentication_system
    flow_execution_engine -->|loads| component_management
    flow_execution_engine -->|tracks| graph_state_management
    job_queue_system -->|executes| flow_execution_engine
    authentication_system -->|enforces| security_access_control
    authentication_system -->|validates| user_entity
    real_time_event_system -->|transmits| websocket_sse_communication
    component_management -->|caches| caching_system
    graph_state_management -->|tracks| vertex_build_entity
    validation_engine -->|reports| error_handling_system
    caching_system -->|configures| configuration_management
    error_handling_system -->|logs| transaction_entity
    security_access_control -->|authorizes| user_entity
    websocket_sse_communication -->|transmits| message_entity
    frontend_state_management -->|syncs| flow_entity
    mcp_integration_system -->|extends| component_management
    voice_mode_system -->|streams| real_time_event_system
    file_management_system -->|secures| security_access_control
    store_integration_system -->|authenticates| authentication_system
    session_management_system -->|stores| caching_system
    flow_management_tests -->|tests| flow_entity
    authentication_authorization_tests -->|tests| user_entity
    graph_execution_tests -->|tests| vertex_entity
    component_integration_tests -->|tests| component_entity
    real_time_communication_tests -->|tests| message_entity
    job_queue_tests -->|tests| transaction_entity
    validation_engine_tests -->|tests| flow_entity
    caching_system_tests -->|tests| component_entity
    error_handling_tests -->|tests| transaction_entity
    security_access_control_tests -->|tests| user_entity
    mcp_integration_tests -->|tests| flow_entity
    voice_mode_tests -->|tests| message_entity
    file_management_tests -->|tests| file_entity
    frontend_ui_tests -->|tests| login_page
    e2e_workflow_tests -->|tests| flow_dashboard
    performance_benchmark_tests -->|tests| flow_execution_engine
    api_integration_tests -->|tests| flow_entity
    database_integration_tests -->|tests| user_entity
    deployment_validation_tests -->|tests| application_lifecycle
    regression_test_suite -->|tests| flow_entity
    folder_entity -->|parent_of| folder_entity
    user_entity -->|credentials| credential_entity
    user_entity -->|contributes| store_entity
    credential_entity -->|relates| variable_entity
    store_entity -->|contains| component_entity
    global_variable_entity -->|scoped_to| user_entity
    playground_interface -->|embeds| io_modal
    voice_assistant -->|enhances| chat_input
    folder_sidebar -->|filters| flow_grid
    component_sidebar -->|displays| component_grid
    mcp_server_tab -->|opens| add_mcp_server_modal
    settings_page -->|includes| api_keys_settings
    settings_page -->|includes| global_variables_settings
    header_component -->|displays| notification_system
    error_boundary -->|controls| loading_states
    theme_provider -->|themes| header_component
    auth_guard -->|protects| login_page
    websocket_manager -->|provides| real_time_event_system
    file_management_page -->|displays| data_table
    add_mcp_server_modal -->|uses| form_builder
    flow_dashboard -->|includes| search_interface
    flow_entity -->|contains| component_entity
    transaction_entity -->|tracks| vertex_entity
    message_entity -->|belongs_to| user_entity
    vertex_build_entity -->|references| component_entity
    file_entity -->|used_by| flow_entity
    api_key_entity -->|authorizes| transaction_entity
    variable_entity -->|used_in| flow_entity
    credential_entity -->|manages| api_key_entity
    store_entity -->|shares| flow_entity
    store_page -->|imports| flow_editor
    playground_interface -->|edits| flow_editor
    file_management_page -->|uses| flow_editor
    settings_page -->|admin| admin_page
    flow_dashboard -->|templates| template_gallery
    template_gallery -->|creates| flow_editor
    flow_editor -->|displays| reactflow_canvas
    flow_editor -->|includes| component_sidebar
    flow_editor -->|includes| flow_toolbar
    playground_interface -->|displays| message_list
    flow_dashboard -->|includes| workspace_switcher
    settings_page -->|includes| mcp_server_tab
    store_page -->|includes| paginator_component
    telemetry_analytics_system -->|aggregates| logging_monitoring_system
    dependency_injection_system -->|configures| configuration_management
    deployment_orchestration -->|validates| validation_engine
    settings_page -->|configures| api_key_entity
    settings_page -->|configures| variable_entity
    file_management_page -->|uploads| file_entity
    store_page -->|browses| store_entity
    login_page -->|authenticates| user_entity
    flow_execution_engine -->|records| transaction_entity
    job_queue_system -->|executes| vertex_build_entity
    voice_assistant -->|transcribes| message_entity
    mcp_integration_system -->|exposes| flow_entity
    admin_page -->|administers| user_entity
```
