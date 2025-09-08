#!/usr/bin/env python3

import json
from datetime import datetime

def get_next_edge_id(edges):
    """Get the next available edge ID"""
    max_id = 0
    for edge in edges:
        edge_id = edge.get('id', '')
        if edge_id.startswith('edge_'):
            try:
                num = int(edge_id.replace('edge_', ''))
                max_id = max(max_id, num)
            except ValueError:
                pass
    return f"edge_{max_id + 1}"

def create_edge(source, target, edge_type, relationship, label, details, edge_id=None):
    """Create a new edge with consistent format"""
    return {
        "id": edge_id,
        "type": edge_type,
        "source": source,
        "target": target,
        "relationship": relationship,
        "label": label,
        "details": details,
        "orphan_fix": True,
        "created_at": datetime.now().isoformat()
    }

def fix_orphaned_nodes():
    with open('/Users/dongmingjiang/GB/LangBuilder/AppGraph/New-Workflows/langbuilder_app_graph_enhanced_v4_with_85_rbac_flows.json', 'r') as f:
        data = json.load(f)
    
    total_edges_added = 0
    
    # Define edge patterns for different node types
    edge_patterns = {
        # Flow Authoring & Execution Subsystem
        'voice_assistant': [
            ('chat_input', 'interface_composition', 'integrates_with', 'Voice input integration', 'Provides voice input capabilities to chat interface'),
            ('flow_execution_engine', 'interface_composition', 'controls', 'Flow control', 'Controls flow execution through voice commands')
        ],
        'flow_grid': [
            ('flow_entity', 'interface_composition', 'displays', 'Flow display', 'Displays flow entities in grid format'),
            ('flow_management', 'interface_composition', 'manages', 'Flow management', 'Manages flow operations through grid interface')
        ],
        'header_component': [
            ('auth_guard', 'interface_composition', 'integrates_with', 'Auth integration', 'Integrates with authentication system'),
            ('workspace_switcher', 'interface_composition', 'contains', 'Navigation', 'Contains workspace switching functionality')
        ],
        'marketplace_access_controller': [
            ('rbac_enforcement_engine', 'logic_dependency', 'validates_with', 'Permission validation', 'Validates marketplace access permissions'),
            ('component_management', 'logic_dependency', 'controls', 'Access control', 'Controls access to marketplace components')
        ],
        'frontend_ui_tests': [
            ('flow_grid', 'test_validation', 'tests', 'UI testing', 'Tests flow grid component functionality'),
            ('header_component', 'test_validation', 'tests', 'UI testing', 'Tests header component functionality')
        ],
        
        # User Experience & Interaction Subsystem
        'login_page': [
            ('auth_guard', 'interface_navigation', 'navigates_to', 'Authentication flow', 'Navigates to authentication guard'),
            ('user_entity', 'data_operation', 'authenticates', 'User authentication', 'Authenticates user credentials')
        ],
        'chat_input': [
            ('flow_execution_engine', 'interface_composition', 'triggers', 'Flow execution', 'Triggers flow execution from chat input'),
            ('websocket_sse_communication', 'interface_composition', 'communicates_via', 'Real-time communication', 'Communicates through WebSocket/SSE')
        ],
        'folder_sidebar': [
            ('flow_entity', 'interface_composition', 'organizes', 'Flow organization', 'Organizes flows in folder structure'),
            ('workspace_entity', 'interface_composition', 'displays', 'Workspace display', 'Displays workspace folder structure')
        ],
        'file_management_page': [
            ('flow_entity', 'data_operation', 'manages', 'File management', 'Manages flow files and assets'),
            ('folder_sidebar', 'interface_composition', 'uses', 'Navigation', 'Uses folder sidebar for navigation')
        ],
        'admin_page': [
            ('role_management_ui', 'interface_navigation', 'navigates_to', 'Role management', 'Navigates to role management interface'),
            ('rbac_enforcement_engine', 'interface_composition', 'uses', 'Authorization', 'Uses RBAC for admin access control')
        ],
        'form_builder': [
            ('component_management', 'interface_composition', 'builds_forms_for', 'Form generation', 'Builds forms for component configuration'),
            ('validation_engine', 'interface_composition', 'validates_with', 'Input validation', 'Validates form inputs using validation engine')
        ],
        'search_interface': [
            ('flow_entity', 'data_operation', 'searches', 'Flow search', 'Searches through flow entities'),
            ('component_management', 'data_operation', 'searches', 'Component search', 'Searches through available components')
        ],
        'template_gallery': [
            ('flow_entity', 'interface_composition', 'displays', 'Template display', 'Displays flow templates'),
            ('marketplace_access_controller', 'interface_composition', 'uses', 'Access control', 'Uses marketplace access control')
        ],
        
        # Integration & Communication Subsystem  
        'websocket_sse_communication': [
            ('chat_input', 'logic_dependency', 'serves', 'Real-time communication', 'Serves real-time communication for chat'),
            ('flow_execution_engine', 'logic_dependency', 'streams_to', 'Execution streaming', 'Streams execution updates')
        ],
        
        # Platform Infrastructure Subsystem
        'global_variable_entity': [
            ('global_variables_settings', 'schema_relationship', 'managed_by', 'Settings management', 'Managed through global variables settings interface'),
            ('credential_entity', 'schema_relationship', 'relates_to', 'Credential relationship', 'Related to credential management')
        ],
        'notification_system': [
            ('error_handling_system', 'interface_composition', 'displays_from', 'Error notifications', 'Displays notifications from error handling'),
            ('job_queue_system', 'interface_composition', 'displays_from', 'Job notifications', 'Displays job status notifications')
        ],
        'loading_states': [
            ('flow_execution_engine', 'interface_composition', 'displays_for', 'Execution loading', 'Displays loading states for flow execution'),
            ('component_management', 'interface_composition', 'displays_for', 'Component loading', 'Displays loading states for component operations')
        ],
        'theme_provider': [
            ('header_component', 'interface_composition', 'styles', 'Theme styling', 'Provides theme styling for header'),
            ('flow_grid', 'interface_composition', 'styles', 'Theme styling', 'Provides theme styling for flow grid')
        ],
        'data_table': [
            ('flow_entity', 'interface_composition', 'displays', 'Data display', 'Displays flow data in tabular format'),
            ('audit_log_entity', 'interface_composition', 'displays', 'Audit display', 'Displays audit logs in tabular format')
        ],
        'workspace_switcher': [
            ('workspace_entity', 'interface_composition', 'switches_between', 'Workspace switching', 'Switches between different workspaces'),
            ('header_component', 'interface_composition', 'integrated_in', 'Navigation integration', 'Integrated in header component')
        ],
        'job_queue_system': [
            ('flow_execution_engine', 'logic_dependency', 'queues_for', 'Job queuing', 'Queues jobs for flow execution'),
            ('notification_system', 'logic_dependency', 'notifies_through', 'Job notifications', 'Sends notifications through notification system')
        ],
        'error_handling_system': [
            ('flow_execution_engine', 'logic_dependency', 'handles_errors_for', 'Error handling', 'Handles errors from flow execution'),
            ('notification_system', 'logic_dependency', 'reports_to', 'Error reporting', 'Reports errors to notification system')
        ],
        'frontend_state_management': [
            ('flow_grid', 'logic_dependency', 'manages_state_for', 'State management', 'Manages UI state for flow grid'),
            ('chat_input', 'logic_dependency', 'manages_state_for', 'State management', 'Manages UI state for chat input')
        ],
        'mcp_integration_system': [
            ('component_management', 'logic_dependency', 'integrates_with', 'MCP integration', 'Integrates MCP components'),
            ('flow_execution_engine', 'logic_dependency', 'provides_context_to', 'Context provision', 'Provides model context to flow execution')
        ]
    }
    
    # Test node patterns - connect tests to what they test
    test_patterns = {
        'authentication_authorization_tests': [('auth_guard', 'test_validation', 'tests', 'Auth testing', 'Tests authentication and authorization functionality')],
        'real_time_communication_tests': [('websocket_sse_communication', 'test_validation', 'tests', 'Communication testing', 'Tests real-time communication functionality')],
        'job_queue_tests': [('job_queue_system', 'test_validation', 'tests', 'Queue testing', 'Tests job queue system functionality')],
        'validation_engine_tests': [('validation_engine', 'test_validation', 'tests', 'Validation testing', 'Tests validation engine functionality')],
        'caching_system_tests': [('component_management', 'test_validation', 'tests', 'Cache testing', 'Tests caching system functionality')],
        'error_handling_tests': [('error_handling_system', 'test_validation', 'tests', 'Error testing', 'Tests error handling system functionality')],
        'security_access_control_tests': [('rbac_enforcement_engine', 'test_validation', 'tests', 'Security testing', 'Tests security and access control functionality')],
        'voice_mode_tests': [('voice_assistant', 'test_validation', 'tests', 'Voice testing', 'Tests voice mode processing functionality')],
        'performance_benchmark_tests': [('flow_execution_engine', 'test_validation', 'tests', 'Performance testing', 'Tests system performance and benchmarks')],
        'api_integration_tests': [('validation_engine', 'test_validation', 'tests', 'API testing', 'Tests API integration functionality')],
        'regression_test_suite': [('flow_execution_engine', 'test_validation', 'tests', 'Regression testing', 'Tests for regression in core functionality')],
        'mcp_integration_tests': [('mcp_integration_system', 'test_validation', 'tests', 'MCP testing', 'Tests MCP integration functionality')]
    }
    
    # Combine all patterns
    all_patterns = {**edge_patterns, **test_patterns}
    
    # Process each subsystem
    for subsystem in data['subsystems']:
        subsystem_id = subsystem['id']
        edges = subsystem['app_graph']['edges']
        
        # Find orphaned nodes in this subsystem
        all_nodes = {}
        nodes = subsystem['app_graph']['nodes']
        for node_type in ['schema_nodes', 'interface_nodes', 'logic_nodes', 'test_nodes']:
            if node_type in nodes:
                for node in nodes[node_type]:
                    all_nodes[node['id']] = node_type
        
        # Extract all edge source and target IDs
        edge_node_ids = set()
        for edge in edges:
            if 'source' in edge:
                edge_node_ids.add(edge['source'])
            if 'target' in edge:
                edge_node_ids.add(edge['target'])
            if 'source_node_id' in edge:
                edge_node_ids.add(edge['source_node_id'])
            if 'target_node_id' in edge:
                edge_node_ids.add(edge['target_node_id'])
        
        # Find orphaned nodes
        orphaned_nodes = [node_id for node_id in all_nodes.keys() if node_id not in edge_node_ids]
        
        if orphaned_nodes:
            print(f"\nProcessing {len(orphaned_nodes)} orphaned nodes in {subsystem_id}:")
        
        # Add edges for orphaned nodes
        for orphaned_node in orphaned_nodes:
            if orphaned_node in all_patterns:
                patterns = all_patterns[orphaned_node]
                for target, edge_type, relationship, label, details in patterns:
                    # Check if target exists in this subsystem or is a common node
                    if target in all_nodes or target in ['user_entity', 'workspace_entity', 'flow_entity']:
                        edge_id = get_next_edge_id(edges)
                        new_edge = create_edge(orphaned_node, target, edge_type, relationship, label, details, edge_id)
                        edges.append(new_edge)
                        total_edges_added += 1
                        print(f"  Added edge: {orphaned_node} -> {target} ({relationship})")
            else:
                print(f"  Warning: No pattern defined for {orphaned_node}")
    
    # Update metadata
    for subsystem in data['subsystems']:
        if 'orphan_fix_applied' not in subsystem['app_graph']['metadata']:
            subsystem['app_graph']['metadata']['orphan_fix_applied'] = True
            subsystem['app_graph']['metadata']['orphan_fix_timestamp'] = datetime.now().isoformat()
    
    # Save the updated file
    with open('/Users/dongmingjiang/GB/LangBuilder/AppGraph/New-Workflows/langbuilder_app_graph_enhanced_v4_with_85_rbac_flows.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nTotal edges added: {total_edges_added}")
    print("File updated successfully!")

if __name__ == "__main__":
    fix_orphaned_nodes()