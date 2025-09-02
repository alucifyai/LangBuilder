```mermaid
%% LangBuilder Partitioned AppGraph v2.0.0-RBAC-Partitioned
graph LR
    subgraph rbac_security_subsystem["RBAC & Security Subsystem"]
        schema_role["Role\n(entity)"]
        schema_permission["Permission\n(entity)"]
        schema_role_assignment["RoleAssignment\n(entity)"]
        schema_workspace["Workspace\n(entity)"]
        schema_audit_log["AuditLog\n(entity)"]
        interface_rbac_dashboard["RBAC Management Dashboard\n(screen)"]
        interface_role_editor["Role Editor Interface\n(component)"]
        interface_audit_viewer["Audit Log Viewer\n(component)"]
        logic_rbac_authorization["RBAC Authorization Engine\n(service)"]
        logic_role_management["Role Management Service\n(service)"]
        logic_audit_logging["Audit Logging Service\n(service)"]
        test_rbac_role_creation["Role Creation and Management\n(acceptance_test)"]
        test_rbac_permission_enforcement["Permission Enforcement Across Resources\n(acceptance_test)"]
    style schema_role fill:#FF6B6B,stroke:#333,stroke-width:1px,color:#000
    style schema_permission fill:#FF6B6B,stroke:#333,stroke-width:1px,color:#000
    style schema_role_assignment fill:#FF6B6B,stroke:#333,stroke-width:1px,color:#000
    style schema_workspace fill:#FF6B6B,stroke:#333,stroke-width:1px,color:#000
    style schema_audit_log fill:#FF6B6B,stroke:#333,stroke-width:1px,color:#000
    style interface_rbac_dashboard fill:#4ECDC4,stroke:#333,stroke-width:1px,color:#000
    style interface_role_editor fill:#4ECDC4,stroke:#333,stroke-width:1px,color:#000
    style interface_audit_viewer fill:#4ECDC4,stroke:#333,stroke-width:1px,color:#000
    style logic_rbac_authorization fill:#45B7D1,stroke:#333,stroke-width:1px,color:#000
    style logic_role_management fill:#45B7D1,stroke:#333,stroke-width:1px,color:#000
    style logic_audit_logging fill:#45B7D1,stroke:#333,stroke-width:1px,color:#000
    style test_rbac_role_creation fill:#B8860B,stroke:#333,stroke-width:1px,color:#000
    style test_rbac_permission_enforcement fill:#B8860B,stroke:#333,stroke-width:1px,color:#000
        schema_role -->|has_permissions| schema_permission
        schema_role_assignment -->|assigned_role| schema_role
        schema_workspace -->|scopes_role_assignments| schema_role_assignment
        interface_rbac_dashboard -->|includes| interface_role_editor
        logic_rbac_authorization -->|queries| logic_role_management
        logic_role_management -->|logs_actions| logic_audit_logging
        logic_audit_logging -->|creates_entries| schema_audit_log
        test_rbac_role_creation -->|tests| logic_role_management
        test_rbac_permission_enforcement -->|tests| logic_rbac_authorization
        schema_role -->|has_permissions| schema_permission
        schema_role_assignment -->|assigned_role| schema_role
        schema_workspace -->|scopes_role_assignments| schema_role_assignment
        interface_rbac_dashboard -->|includes| interface_role_editor
        logic_rbac_authorization -->|queries| logic_role_management
        logic_role_management -->|logs_actions| logic_audit_logging
        logic_audit_logging -->|creates_entries| schema_audit_log
        test_rbac_role_creation -->|tests| logic_role_management
        test_rbac_permission_enforcement -->|tests| logic_rbac_authorization
        schema_role -->|has_permissions| schema_permission
        schema_role_assignment -->|assigned_role| schema_role
        schema_workspace -->|scopes_role_assignments| schema_role_assignment
        interface_rbac_dashboard -->|includes| interface_role_editor
        logic_rbac_authorization -->|queries| logic_role_management
        logic_role_management -->|logs_actions| logic_audit_logging
        logic_audit_logging -->|creates_entries| schema_audit_log
        test_rbac_role_creation -->|tests| logic_role_management
        test_rbac_permission_enforcement -->|tests| logic_rbac_authorization
    end
    subgraph auth_subsystem["Authentication & Authorization Subsystem"]
        schema_user["User\n(entity)"]
        schema_apikey["ApiKey\n(entity)"]
        schema_credential["Credential\n(entity)"]
        ui_login_page["LoginPage\n(page)"]
        ui_auth_store["AuthStore\n(store)"]
        ui_api_keys_store["ApiKeysStore\n(store)"]
        logic_auth_flow["AuthenticationFlow\n(statechart)"]
        logic_user_service["UserService\n(service)"]
        logic_session_manager["SessionManager\n(service)"]
        logic_rate_limiter["RateLimiter\n(service)"]
        test_user_authentication["UserAuthenticationTest\n(acceptance)"]
        test_user_isolation["UserIsolationTest\n(security)"]
        test_api_key_management["ApiKeyManagementTest\n(acceptance)"]
    style schema_user fill:#96CEB4,stroke:#333,stroke-width:1px,color:#000
    style schema_apikey fill:#96CEB4,stroke:#333,stroke-width:1px,color:#000
    style schema_credential fill:#96CEB4,stroke:#333,stroke-width:1px,color:#000
    style ui_login_page fill:#96CEB4,stroke:#333,stroke-width:1px,color:#000
    style logic_auth_flow fill:#96CEB4,stroke:#333,stroke-width:1px,color:#000
        schema_user -->|owns| schema_apikey
        schema_user -->|owns| schema_credential
        ui_login_page -->|initiates| logic_auth_flow
        ui_auth_store -->|calls| logic_user_service
        test_user_authentication -->|tests| logic_auth_flow
        test_user_isolation -->|verifies| logic_user_service
        test_api_key_management -->|tests| ui_api_keys_store
        logic_user_service -->|manages| schema_user
        ui_api_keys_store -->|stores| schema_apikey
        schema_user -->|owns| schema_apikey
        schema_user -->|owns| schema_credential
        ui_login_page -->|initiates| logic_auth_flow
        ui_auth_store -->|calls| logic_user_service
        test_user_authentication -->|tests| logic_auth_flow
        test_user_isolation -->|verifies| logic_user_service
        test_api_key_management -->|tests| ui_api_keys_store
        logic_user_service -->|manages| schema_user
        ui_api_keys_store -->|stores| schema_apikey
        schema_user -->|owns| schema_apikey
        schema_user -->|owns| schema_credential
        ui_login_page -->|initiates| logic_auth_flow
        ui_auth_store -->|calls| logic_user_service
        test_user_authentication -->|tests| logic_auth_flow
        test_user_isolation -->|verifies| logic_user_service
        test_api_key_management -->|tests| ui_api_keys_store
        logic_user_service -->|manages| schema_user
        ui_api_keys_store -->|stores| schema_apikey
    end
    subgraph flow_management_subsystem["Flow Management Subsystem"]
        schema_flow["Flow\n(entity)"]
        schema_folder["Folder\n(entity)"]
        schema_flowrun["FlowRun\n(entity)"]
        schema_variable["Variable\n(entity)"]
        schema_store["Store\n(entity)"]
        schema_global_variable["GlobalVariable\n(entity)"]
        ui_flow_page["FlowPage\n(page)"]
        ui_home_page["HomePage\n(page)"]
        ui_settings_page["SettingsPage\n(page)"]
        ui_flow_store["FlowStore\n(store)"]
        ui_folder_store["FolderStore\n(store)"]
        ui_flow_grid["FlowGrid\n(component)"]
        ui_flow_card["FlowCard\n(component)"]
        ui_node_toolbar["NodeToolbar\n(component)"]
        ui_edit_node_modal["EditNodeModal\n(modal)"]
        ui_share_modal["ShareModal\n(modal)"]
        ui_header_component["HeaderComponent\n(component)"]
        ui_shortcut_store["ShortcutStore\n(store)"]
        ui_location_store["LocationStore\n(store)"]
        ui_dark_mode_store["DarkModeStore\n(store)"]
        logic_flow_service["FlowService\n(service)"]
        logic_validation_engine["ValidationEngine\n(engine)"]
        logic_export_service["ExportService\n(service)"]
        logic_cleanup_service["CleanupService\n(service)"]
        test_flow_creation["FlowCreationTest\n(acceptance)"]
        test_flow_sharing["FlowSharingTest\n(acceptance)"]
        test_data_persistence["DataPersistenceTest\n(integration)"]
        schema_folder -->|contains| schema_flow
        schema_flow -->|has| schema_flowrun
        schema_folder -->|parent_child| schema_folder
        ui_flow_page -->|includes| ui_node_toolbar
        ui_home_page -->|includes| ui_flow_grid
        ui_flow_grid -->|renders| ui_flow_card
        ui_flow_store -->|calls| logic_flow_service
        logic_export_service -->|serializes| schema_flow
        test_flow_creation -->|tests| logic_flow_service
        test_flow_sharing -->|tests| ui_share_modal
        test_data_persistence -->|tests| logic_cleanup_service
        logic_flow_service -->|persists| schema_flow
        ui_home_page -->|shows| schema_flow
        ui_settings_page -->|configures| schema_apikey
        ui_flow_page -->|includes| ui_sidebar_component
        ui_home_page -->|includes| ui_header_component
        ui_folder_store -->|organizes| schema_folder
        ui_edit_node_modal -->|configures| schema_vertex
        ui_settings_page -->|configures| schema_global_variable
        logic_cleanup_service -->|cleans| logic_session_manager
        ui_settings_page -->|utilizes| ui_api_keys_store
        ui_settings_page -->|utilizes| ui_shortcut_store
        ui_settings_page -->|utilizes| ui_dark_mode_store
        schema_folder -->|contains| schema_flow
        schema_flow -->|has| schema_flowrun
        schema_folder -->|parent_child| schema_folder
        ui_flow_page -->|includes| ui_node_toolbar
        ui_home_page -->|includes| ui_flow_grid
        ui_flow_grid -->|renders| ui_flow_card
        ui_flow_store -->|calls| logic_flow_service
        logic_export_service -->|serializes| schema_flow
        test_flow_creation -->|tests| logic_flow_service
        test_flow_sharing -->|tests| ui_share_modal
        test_data_persistence -->|tests| logic_cleanup_service
        logic_flow_service -->|persists| schema_flow
        ui_home_page -->|shows| schema_flow
        ui_settings_page -->|configures| schema_apikey
        ui_flow_page -->|includes| ui_sidebar_component
        ui_home_page -->|includes| ui_header_component
        ui_folder_store -->|organizes| schema_folder
        ui_edit_node_modal -->|configures| schema_vertex
        ui_settings_page -->|configures| schema_global_variable
        logic_cleanup_service -->|cleans| logic_session_manager
        ui_settings_page -->|utilizes| ui_api_keys_store
        ui_settings_page -->|utilizes| ui_shortcut_store
        ui_settings_page -->|utilizes| ui_dark_mode_store
        schema_folder -->|contains| schema_flow
        schema_flow -->|has| schema_flowrun
        schema_folder -->|parent_child| schema_folder
        ui_flow_page -->|includes| ui_node_toolbar
        ui_home_page -->|includes| ui_flow_grid
        ui_flow_grid -->|renders| ui_flow_card
        ui_flow_store -->|calls| logic_flow_service
        logic_export_service -->|serializes| schema_flow
        test_flow_creation -->|tests| logic_flow_service
        test_flow_sharing -->|tests| ui_share_modal
        test_data_persistence -->|tests| logic_cleanup_service
        logic_flow_service -->|persists| schema_flow
        ui_home_page -->|shows| schema_flow
        ui_settings_page -->|configures| schema_apikey
        ui_flow_page -->|includes| ui_sidebar_component
        ui_home_page -->|includes| ui_header_component
        ui_folder_store -->|organizes| schema_folder
        ui_edit_node_modal -->|configures| schema_vertex
        ui_settings_page -->|configures| schema_global_variable
        logic_cleanup_service -->|cleans| logic_session_manager
        ui_settings_page -->|utilizes| ui_api_keys_store
        ui_settings_page -->|utilizes| ui_shortcut_store
        ui_settings_page -->|utilizes| ui_dark_mode_store
    end
    subgraph execution_engine_subsystem["Graph Execution Engine Subsystem"]
        schema_vertex["Vertex\n(entity)"]
        schema_edge["Edge\n(entity)"]
        schema_component["Component\n(entity)"]
        schema_transaction["Transaction\n(entity)"]
        ui_sidebar_component["SidebarComponent\n(component)"]
        ui_types_store["TypesStore\n(store)"]
        logic_flow_execution["FlowExecutionEngine\n(statechart)"]
        logic_graph_engine["GraphExecutionEngine\n(engine)"]
        logic_component_loader["ComponentLoader\n(service)"]
        logic_cache_manager["CacheManager\n(service)"]
        test_flow_execution["FlowExecutionTest\n(acceptance)"]
        test_component_loading["ComponentLoadingTest\n(unit)"]
        test_graph_cycles["GraphCycleTest\n(unit)"]
        test_performance["PerformanceTest\n(performance)"]
        schema_vertex -->|connects| schema_edge
        logic_component_loader -->|loads| schema_component
        logic_graph_engine -->|executes| schema_vertex
        logic_flow_execution -->|caches| logic_cache_manager
        test_flow_execution -->|tests| logic_flow_execution
        test_component_loading -->|tests| logic_component_loader
        test_graph_cycles -->|tests| logic_graph_engine
        test_performance -->|measures| logic_graph_engine
        schema_transaction -->|tracks| schema_flowrun
        ui_flow_store -->|references| ui_types_store
        schema_vertex -->|connects| schema_edge
        logic_component_loader -->|loads| schema_component
        logic_graph_engine -->|executes| schema_vertex
        logic_flow_execution -->|caches| logic_cache_manager
        test_flow_execution -->|tests| logic_flow_execution
        test_component_loading -->|tests| logic_component_loader
        test_graph_cycles -->|tests| logic_graph_engine
        test_performance -->|measures| logic_graph_engine
        schema_transaction -->|tracks| schema_flowrun
        ui_flow_store -->|references| ui_types_store
        schema_vertex -->|connects| schema_edge
        logic_component_loader -->|loads| schema_component
        logic_graph_engine -->|executes| schema_vertex
        logic_flow_execution -->|caches| logic_cache_manager
        test_flow_execution -->|tests| logic_flow_execution
        test_component_loading -->|tests| logic_component_loader
        test_graph_cycles -->|tests| logic_graph_engine
        test_performance -->|measures| logic_graph_engine
        schema_transaction -->|tracks| schema_flowrun
        ui_flow_store -->|references| ui_types_store
    end
    subgraph communication_subsystem["Real-time Communication Subsystem"]
        schema_message["Message\n(entity)"]
        ui_playground_page["PlaygroundPage\n(page)"]
        ui_chat_interface["ChatInterface\n(component)"]
        ui_message_store["MessageStore\n(store)"]
        ui_global_store["GlobalStore\n(store)"]
        logic_websocket_handler["WebSocketHandler\n(statechart)"]
        logic_sse_handler["ServerSentEventsHandler\n(statechart)"]
        logic_notification_service["NotificationService\n(service)"]
        logic_event_manager["EventManager\n(service)"]
        test_websocket_connection["WebSocketConnectionTest\n(integration)"]
        test_error_handling["ErrorHandlingTest\n(unit)"]
        ui_playground_page -->|includes| ui_chat_interface
        logic_websocket_handler -->|updates| ui_message_store
        logic_sse_handler -->|delivers| logic_notification_service
        ui_global_store -->|displays| logic_notification_service
        test_websocket_connection -->|tests| logic_websocket_handler
        test_error_handling -->|tests| logic_event_manager
        ui_playground_page -->|shows| schema_message
        schema_flow -->|generates| schema_message
        logic_auth_flow -->|navigates| ui_location_store
        ui_playground_page -->|includes| ui_chat_interface
        logic_websocket_handler -->|updates| ui_message_store
        logic_sse_handler -->|delivers| logic_notification_service
        ui_global_store -->|displays| logic_notification_service
        test_websocket_connection -->|tests| logic_websocket_handler
        test_error_handling -->|tests| logic_event_manager
        ui_playground_page -->|shows| schema_message
        schema_flow -->|generates| schema_message
        logic_auth_flow -->|navigates| ui_location_store
        ui_playground_page -->|includes| ui_chat_interface
        logic_websocket_handler -->|updates| ui_message_store
        logic_sse_handler -->|delivers| logic_notification_service
        ui_global_store -->|displays| logic_notification_service
        test_websocket_connection -->|tests| logic_websocket_handler
        test_error_handling -->|tests| logic_event_manager
        ui_playground_page -->|shows| schema_message
        schema_flow -->|generates| schema_message
        logic_auth_flow -->|navigates| ui_location_store
    end
    subgraph marketplace_subsystem["Template & Store Subsystem"]
        schema_template["Template\n(entity)"]
        ui_store_page["StorePage\n(page)"]
        ui_api_modal["ApiModal\n(modal)"]
        logic_template_service["TemplateService\n(service)"]
        logic_api_handler["ApiRequestHandler\n(process)"]
        logic_file_upload["FileUploadProcess\n(process)"]
        logic_telemetry_service["TelemetryService\n(service)"]
        test_template_instantiation["TemplateInstantiationTest\n(acceptance)"]
        test_api_integration["ApiIntegrationTest\n(integration)"]
        test_file_upload["FileUploadTest\n(integration)"]
        logic_template_service -->|provides| schema_template
        ui_store_page -->|shows| schema_template
        ui_api_modal -->|exports| schema_flow
        logic_telemetry_service -->|monitors| logic_event_manager
        test_template_instantiation -->|verifies| logic_template_service
        test_api_integration -->|tests| logic_api_handler
        test_file_upload -->|tests| logic_file_upload
        logic_api_handler -->|validates| logic_validation_engine
        logic_rate_limiter -->|limits| logic_api_handler
        logic_file_upload -->|stores| schema_store
        logic_template_service -->|provides| schema_template
        ui_store_page -->|shows| schema_template
        ui_api_modal -->|exports| schema_flow
        logic_telemetry_service -->|monitors| logic_event_manager
        test_template_instantiation -->|verifies| logic_template_service
        test_api_integration -->|tests| logic_api_handler
        test_file_upload -->|tests| logic_file_upload
        logic_api_handler -->|validates| logic_validation_engine
        logic_rate_limiter -->|limits| logic_api_handler
        logic_file_upload -->|stores| schema_store
        logic_template_service -->|provides| schema_template
        ui_store_page -->|shows| schema_template
        ui_api_modal -->|exports| schema_flow
        logic_telemetry_service -->|monitors| logic_event_manager
        test_template_instantiation -->|verifies| logic_template_service
        test_api_integration -->|tests| logic_api_handler
        test_file_upload -->|tests| logic_file_upload
        logic_api_handler -->|validates| logic_validation_engine
        logic_rate_limiter -->|limits| logic_api_handler
        logic_file_upload -->|stores| schema_store
        validate_file -->|isValid| upload_to_storage
        upload_to_storage -->|uploadSuccessful| process_file
        process_file --> update_database
    end
    logic_auth_flow -. |loads_user_permissions| .-> logic_rbac_authorization
    schema_workspace -. |manages_workspace_membership| .-> schema_user
    logic_flow_service -. |validates_flow_permissions| .-> logic_rbac_authorization
    logic_flow_execution -. |validates_execution_permissions| .-> logic_rbac_authorization
    logic_api_handler -. |validates_api_permissions| .-> logic_rbac_authorization
    logic_template_service -. |validates_template_permissions| .-> logic_rbac_authorization
    logic_audit_logging -. |comprehensive_audit_trail| .-> all_subsystems
    schema_user -. |owns| .-> schema_flow
    schema_user -. |owns| .-> schema_folder
    schema_user -. |owns| .-> schema_variable
    schema_user -. |owns| .-> schema_store
    ui_flow_page -. |starts| .-> logic_flow_execution
    logic_websocket_handler -. |updates| .-> ui_message_store
    linkStyle 0 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 1 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 2 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 3 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 4 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 5 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 6 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 7 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 8 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 9 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 10 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 11 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 12 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 13 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 14 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 15 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 16 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 17 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 18 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 19 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 20 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 21 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 22 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 23 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 24 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 25 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 26 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 213 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 214 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 215 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 216 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 217 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 218 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
    linkStyle 219 stroke:#FFE66D,stroke-width:2px,color:#FFE66D
```
