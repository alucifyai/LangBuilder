#!/usr/bin/env python3
"""
Script to distribute the 120 comprehensive edges across the 6 subsystems
based on the source and target nodes.
"""

import json

# Load the comprehensive edges
with open('/Users/dongmingjiang/GB/LangBuilder/comprehensive_edges.json', 'r') as f:
    edges = json.load(f)

# Define subsystem node mappings (based on the analysis)
subsystems = {
    "user_management_auth": {
        "nodes": {
            "user_entity", "api_key_entity", "flow_entity", "login_page", 
            "authentication_system", "security_access_control", "auth_guard",
            "authentication_authorization_tests", "security_access_control_tests",
            "database_integration_tests", "credential_entity", "global_variable_entity"
        },
        "edges": []
    },
    "flow_development": {
        "nodes": {
            "flow_entity", "folder_entity", "component_entity", "flow_dashboard", 
            "flow_editor", "component_sidebar", "reactflow_canvas", "flow_grid",
            "folder_sidebar", "component_grid", "flow_toolbar", "template_gallery",
            "search_interface", "workspace_switcher", "flow_management_tests",
            "component_integration_tests", "frontend_ui_tests"
        },
        "edges": []
    },
    "execution_runtime": {
        "nodes": {
            "vertex_entity", "edge_entity", "transaction_entity", "vertex_build_entity",
            "flow_execution_engine", "job_queue_system", "graph_state_management",
            "validation_engine", "graph_execution_tests", "job_queue_tests", 
            "validation_engine_tests", "performance_benchmark_tests"
        },
        "edges": []
    },
    "file_asset_management": {
        "nodes": {
            "file_entity", "message_entity", "file_management_page", "file_management_system",
            "voice_assistant", "voice_mode_system", "playground_interface", "message_list",
            "chat_input", "io_modal", "data_table", "file_management_tests",
            "voice_mode_tests", "real_time_communication_tests"
        },
        "edges": []
    },
    "integration_services": {
        "nodes": {
            "store_entity", "store_page", "store_integration_system", "mcp_integration_system",
            "mcp_server_tab", "add_mcp_server_modal", "api_integration_tests", 
            "mcp_integration_tests", "form_builder", "paginator_component"
        },
        "edges": []
    },
    "system_infrastructure": {
        "nodes": {
            "variable_entity", "settings_page", "admin_page", "header_component",
            "notification_system", "error_boundary", "theme_provider", "loading_states",
            "websocket_manager", "websocket_sse_communication", "real_time_event_system",
            "frontend_state_management", "application_lifecycle", "component_management",
            "caching_system", "configuration_management", "error_handling_system",
            "session_management_system", "telemetry_analytics_system", 
            "logging_monitoring_system", "dependency_injection_system",
            "deployment_orchestration", "testing_quality_assurance",
            "api_keys_settings", "global_variables_settings", "caching_system_tests",
            "error_handling_tests", "deployment_validation_tests", "e2e_workflow_tests",
            "regression_test_suite"
        },
        "edges": []
    }
}

# Distribute edges based on source and target nodes
for edge in edges:
    source = edge["source"]
    target = edge["target"]
    edge_assigned = False
    
    # Try to assign to subsystem where both source and target exist
    for subsystem_key, subsystem_data in subsystems.items():
        if source in subsystem_data["nodes"] and target in subsystem_data["nodes"]:
            subsystem_data["edges"].append(edge)
            edge_assigned = True
            break
    
    # If not assigned, assign to subsystem with source node
    if not edge_assigned:
        for subsystem_key, subsystem_data in subsystems.items():
            if source in subsystem_data["nodes"]:
                subsystem_data["edges"].append(edge)
                edge_assigned = True
                break
    
    # If still not assigned, assign to subsystem with target node
    if not edge_assigned:
        for subsystem_key, subsystem_data in subsystems.items():
            if target in subsystem_data["nodes"]:
                subsystem_data["edges"].append(edge)
                edge_assigned = True
                break
    
    # If still not assigned, add to system infrastructure as fallback
    if not edge_assigned:
        subsystems["system_infrastructure"]["edges"].append(edge)

# Print distribution summary
print("Edge Distribution Summary:")
print("=" * 50)
total_edges = 0
for subsystem_key, subsystem_data in subsystems.items():
    edge_count = len(subsystem_data["edges"])
    total_edges += edge_count
    print(f"{subsystem_key}: {edge_count} edges")

print(f"\nTotal distributed edges: {total_edges}")
print(f"Original edge count: {len(edges)}")

# Save the distributions (convert sets to lists for JSON serialization)
output_subsystems = {}
for key, data in subsystems.items():
    output_subsystems[key] = {
        "nodes": list(data["nodes"]),
        "edges": data["edges"]
    }

with open('/Users/dongmingjiang/GB/LangBuilder/edge_distributions.json', 'w') as f:
    json.dump(output_subsystems, f, indent=2)

print("\nEdge distributions saved to edge_distributions.json")