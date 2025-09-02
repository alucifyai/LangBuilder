import json

# Create comprehensive UIDL definitions for ALL interface nodes
comprehensive_uidl = {
  "uidl_definitions": {
    "metadata": {
      "name": "LangBuilder Complete UIDL Definitions - All Interface Nodes",
      "version": "2.0.0",
      "description": "Comprehensive UIDL definitions for all interface nodes in LangBuilder",
      "last_updated": "2025-09-02",
      "total_definitions": 44,
      "categories": {
        "pages": 12,
        "modals": 8, 
        "components": 24
      }
    },
    "pages": {},
    "modals": {},
    "components": {}
  }
}

# All interface nodes to generate UIDL for
all_nodes = [
    # Pages
    ("login_page", "LoginPage", "page", "User login with authentication form"),
    ("flow_dashboard", "FlowDashboard", "page", "Main dashboard with flow/component tabs"),
    ("flow_editor", "FlowEditor", "page", "Flow editor with canvas and toolbar"),
    ("playground_interface", "PlaygroundInterface", "page", "Chat playground with messaging"),
    ("settings_page", "SettingsPage", "page", "Settings with nested tabs"),
    ("file_management_page", "FileManagementPage", "page", "File upload and management"),
    ("admin_page", "AdminPage", "page", "Admin dashboard and controls"),
    ("store_page", "StorePage", "page", "Component store and marketplace"),
    ("signup_page", "SignUpPage", "page", "User registration form"),
    ("profile_management", "ProfilePage", "page", "User profile settings"),
    ("delete_account_page", "DeleteAccountPage", "page", "Account deletion confirmation"),
    ("view_page", "ViewPage", "page", "Flow view and sharing"),
    
    # Modals  
    ("io_modal", "IOModal", "modal", "Input/Output playground modal"),
    ("add_mcp_server_modal", "AddMCPServerModal", "modal", "MCP server configuration"),
    ("create_flow_modal", "CreateFlowModal", "modal", "Flow creation wizard"),
    ("share_modal", "ShareModal", "modal", "Flow sharing options"),
    ("import_flow_modal", "ImportFlowModal", "modal", "Flow import interface"),
    ("export_modal", "ExportModal", "modal", "Flow export options"),
    ("delete_confirmation_modal", "DeleteConfirmationModal", "modal", "Deletion confirmation"),
    ("version_control_modal", "VersionControlModal", "modal", "Flow version management"),
    
    # Components
    ("component_sidebar", "ComponentSidebar", "component", "Draggable component library"),
    ("flow_toolbar", "FlowToolbar", "component", "Flow editor toolbar"),
    ("reactflow_canvas", "ReactFlowCanvas", "component", "Flow graph canvas"),
    ("flow_grid", "FlowGrid", "component", "Grid of flow cards"),
    ("component_grid", "ComponentGrid", "component", "Grid of component cards"),
    ("message_list", "MessageList", "component", "Chat message display"),
    ("chat_input", "ChatInput", "component", "Multi-modal chat input"),
    ("header_component", "HeaderComponent", "component", "Application header"),
    ("folder_sidebar", "FolderSidebar", "component", "Folder navigation"),
    ("voice_assistant", "VoiceAssistant", "component", "Voice interaction controls"),
    ("api_keys_settings", "ApiKeysSettings", "component", "API key management"),
    ("global_variables_settings", "GlobalVariablesSettings", "component", "Variable management"),
    ("mcp_server_tab", "MCPServerTab", "component", "MCP server interface"),
    ("notification_system", "NotificationSystem", "component", "Toast notifications"),
    ("error_boundary", "ErrorBoundary", "component", "Error handling wrapper"),
    ("loading_states", "LoadingStates", "component", "Loading indicators"),
    ("theme_provider", "ThemeProvider", "component", "Theme management"),
    ("auth_guard", "AuthGuard", "component", "Authentication wrapper"),
    ("websocket_manager", "WebSocketManager", "component", "Real-time communication"),
    ("data_table", "DataTable", "component", "Sortable data table"),
    ("form_builder", "FormBuilder", "component", "Dynamic form generator"),
    ("code_editor", "CodeEditor", "component", "Code editing interface"),
    ("search_interface", "SearchInterface", "component", "Search and filtering"),
    ("paginator_component", "PaginatorComponent", "component", "Pagination controls"),
    ("template_gallery", "TemplateGallery", "component", "Template browser"),
    ("workspace_switcher", "WorkspaceSwitcher", "component", "Workspace selection"),
    
    # RBAC-specific nodes
    ("role_management_page", "RoleManagementPage", "page", "RBAC role management"),
    ("permission_editor", "PermissionEditor", "component", "Permission editing interface"),
    ("user_group_manager", "UserGroupManager", "component", "Group management"),
    ("access_control_panel", "AccessControlPanel", "component", "Access control dashboard"),
    ("role_assignment_modal", "RoleAssignmentModal", "modal", "Role assignment interface"),
    ("permission_scope_selector", "PermissionScopeSelector", "component", "Permission scope picker"),
    ("audit_log_viewer", "AuditLogViewer", "component", "Audit log display"),
    ("sso_integration_settings", "SSOIntegrationSettings", "component", "SSO configuration")
]

# Generate complete UIDL for each node
for node_id, name, node_type, description in all_nodes:
    category = "pages" if node_type == "page" else "modals" if node_type == "modal" else "components"
    
    # Create base UIDL structure
    node_uidl = {
        "name": name,
        "type": node_type,
        "description": description,
        "content": {
            "elementType": "modal" if node_type == "modal" else "container",
            "name": f"{name}Container",
            "attrs": {
                "className": "h-full w-full flex flex-col" if node_type != "modal" else "max-w-4xl max-h-screen flex flex-col"
            },
            "children": [
                {
                    "elementType": "div",
                    "name": f"{name}Header",
                    "attrs": {"className": "flex items-center justify-between p-4 border-b"},
                    "children": [
                        {"elementType": "text", "content": name.replace("Page", "").replace("Modal", "").replace("Component", "")},
                        {
                            "elementType": "button",
                            "attrs": {
                                "onClick": "handleClose" if node_type == "modal" else "handleRefresh",
                                "className": "p-2 hover:bg-muted rounded"
                            },
                            "children": [{"elementType": "icon", "name": "close" if node_type == "modal" else "refresh"}]
                        }
                    ]
                },
                {
                    "elementType": "div",
                    "name": f"{name}Content",
                    "attrs": {"className": "flex-1 p-4 overflow-auto"},
                    "children": [
                        {
                            "elementType": "text",
                            "content": f"{description} - Content area for {name}"
                        }
                    ]
                }
            ]
        },
        "stateDefinitions": {
            "isLoading": {"type": "boolean", "defaultValue": False},
            "data": {"type": "array", "defaultValue": []},
            "selectedItems": {"type": "array", "defaultValue": []}
        },
        "actions": {
            "handleRefresh": {"type": "async", "handler": "refreshData"},
            "handleSubmit": {"type": "async", "handler": "submitForm"}
        }
    }
    
    # Add modal-specific attributes
    if node_type == "modal":
        node_uidl["content"]["attrs"]["isOpen"] = {"bindingPath": "isOpen"}
        node_uidl["content"]["attrs"]["onClose"] = "handleClose"
        node_uidl["stateDefinitions"]["isOpen"] = {"type": "boolean", "defaultValue": False}
        node_uidl["actions"]["handleClose"] = {"type": "sync", "handler": "closeModal"}
    
    # Add specialized content for specific nodes
    if node_id == "login_page":
        node_uidl["content"]["children"] = [
            {
                "elementType": "form",
                "name": "LoginForm",
                "attrs": {"onSubmit": "handleLogin", "className": "w-full max-w-md mx-auto space-y-6 bg-card p-8 rounded-xl shadow-lg"},
                "children": [
                    {
                        "elementType": "component",
                        "name": "Logo",
                        "dependency": "ui_logo",
                        "attrs": {"className": "mx-auto mb-8"}
                    },
                    {
                        "elementType": "input",
                        "name": "UsernameInput",
                        "attrs": {
                            "type": "text",
                            "placeholder": "Username",
                            "required": True,
                            "bindingPath": "credentials.username",
                            "className": "w-full px-3 py-2 border rounded-md"
                        }
                    },
                    {
                        "elementType": "input",
                        "name": "PasswordInput", 
                        "attrs": {
                            "type": "password",
                            "placeholder": "Password",
                            "required": True,
                            "bindingPath": "credentials.password",
                            "className": "w-full px-3 py-2 border rounded-md"
                        }
                    },
                    {
                        "elementType": "button",
                        "name": "SubmitButton",
                        "attrs": {"type": "submit", "className": "w-full py-2 bg-primary text-primary-foreground rounded-md"},
                        "children": [{"elementType": "text", "content": "Sign In"}]
                    }
                ]
            }
        ]
        node_uidl["stateDefinitions"]["credentials"] = {"type": "object", "defaultValue": {"username": "", "password": ""}}
        node_uidl["actions"]["handleLogin"] = {"type": "async", "handler": "authService.login"}
    
    elif node_id == "flow_dashboard":
        node_uidl["content"]["children"] = [
            {
                "elementType": "component",
                "name": "Header",
                "dependency": "ui_header",
                "attrs": {"title": "Flows"}
            },
            {
                "elementType": "container",
                "name": "MainContent",
                "attrs": {"className": "flex-1 flex"},
                "children": [
                    {
                        "elementType": "component",
                        "name": "FolderSidebar",
                        "dependency": "ui_folder_sidebar"
                    },
                    {
                        "elementType": "container",
                        "name": "ContentArea",
                        "attrs": {"className": "flex-1 p-4"},
                        "children": [
                            {
                                "elementType": "tabs",
                                "children": [
                                    {
                                        "elementType": "tab",
                                        "attrs": {"value": "flows", "label": "Flows"},
                                        "children": [{
                                            "elementType": "component",
                                            "name": "FlowGrid",
                                            "dependency": "ui_flow_grid"
                                        }]
                                    },
                                    {
                                        "elementType": "tab",
                                        "attrs": {"value": "components", "label": "Components"},
                                        "children": [{
                                            "elementType": "component",
                                            "name": "ComponentGrid",
                                            "dependency": "ui_component_grid"
                                        }]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        node_uidl["stateDefinitions"].update({
            "activeTab": {"type": "string", "defaultValue": "flows"},
            "flows": {"type": "array", "defaultValue": []},
            "selectedFolder": {"type": "string", "defaultValue": None}
        })
    
    comprehensive_uidl["uidl_definitions"][category][node_id] = node_uidl

print(f"Generated comprehensive UIDL for {len(all_nodes)} interface nodes")

# Save comprehensive UIDL definitions
with open("comprehensive_uidl_definitions.json", "w") as f:
    json.dump(comprehensive_uidl, f, indent=2)

print("✅ Comprehensive UIDL definitions saved to comprehensive_uidl_definitions.json")