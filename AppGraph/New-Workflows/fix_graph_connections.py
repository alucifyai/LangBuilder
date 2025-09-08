#!/usr/bin/env python3
"""
Script to fix orphaned and phantom nodes in the LangBuilder app graph.
"""

import json
import sys
from collections import defaultdict

def load_app_graph(filepath):
    """Load the app graph JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_app_graph(app_graph, filepath):
    """Save the fixed app graph."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(app_graph, f, indent=2, ensure_ascii=False)

def get_next_edge_id(app_graph):
    """Get the next available edge ID."""
    max_id = 0
    
    # Check subsystem edges
    for subsystem in app_graph.get('subsystems', []):
        edges = subsystem.get('app_graph', {}).get('edges', [])
        for edge in edges:
            if 'id' in edge and edge['id'].startswith('edge_'):
                try:
                    num = int(edge['id'].split('_')[1])
                    max_id = max(max_id, num)
                except:
                    pass
    
    # Check cross-subsystem edges
    for edge in app_graph.get('edges', []):
        if 'id' in edge and edge['id'].startswith('edge_'):
            try:
                num = int(edge['id'].split('_')[1])
                max_id = max(max_id, num)
            except:
                pass
        elif 'id' in edge and edge['id'].startswith('rbac_edge_'):
            try:
                num = int(edge['id'].split('_')[2])
                max_id = max(max_id, num)
            except:
                pass
    
    return max_id + 1

def find_subsystem_by_node(app_graph, node_id):
    """Find which subsystem contains a given node."""
    for subsystem in app_graph.get('subsystems', []):
        nodes_data = subsystem.get('app_graph', {}).get('nodes', {})
        
        for node_type in ['schema_nodes', 'interface_nodes', 'logic_nodes', 'test_nodes']:
            for node in nodes_data.get(node_type, []):
                if node['id'] == node_id:
                    return subsystem['id']
    return None

def add_edge_to_subsystem(app_graph, subsystem_id, edge):
    """Add an edge to a specific subsystem."""
    for subsystem in app_graph.get('subsystems', []):
        if subsystem['id'] == subsystem_id:
            edges = subsystem.get('app_graph', {}).get('edges', [])
            edges.append(edge)
            break

def add_cross_subsystem_edge(app_graph, edge):
    """Add a cross-subsystem edge."""
    if 'edges' not in app_graph:
        app_graph['edges'] = []
    app_graph['edges'].append(edge)

def create_phantom_nodes(app_graph, phantom_nodes):
    """Create missing phantom nodes based on their context."""
    
    phantom_definitions = {
        # RBAC System Components
        'admin_role_validator': {
            'type': 'logic',
            'subsystem': 'security_administration',
            'name': 'Admin Role Validator',
            'description': 'Validates administrator role assignments and permissions',
            'statechart_enabled': True
        },
        'api_security_enforcer': {
            'type': 'logic',
            'subsystem': 'security_administration',
            'name': 'API Security Enforcer',
            'description': 'Enforces security policies on API endpoints',
            'statechart_enabled': True
        },
        'background_job_authorizer': {
            'type': 'logic',
            'subsystem': 'security_administration',
            'name': 'Background Job Authorizer',
            'description': 'Authorizes background job execution based on user permissions',
            'statechart_enabled': True
        },
        'compliance_dashboard': {
            'type': 'interface',
            'subsystem': 'security_administration',
            'name': 'Compliance Dashboard',
            'description': 'Dashboard for viewing compliance and audit reports'
        },
        'component_modification_auditor': {
            'type': 'logic',
            'subsystem': 'security_administration',
            'name': 'Component Modification Auditor',
            'description': 'Audits all component modification operations',
            'statechart_enabled': True
        },
        'flow_execution_audit_logger': {
            'type': 'logic',
            'subsystem': 'security_administration',
            'name': 'Flow Execution Audit Logger',
            'description': 'Logs all flow execution activities for audit purposes',
            'statechart_enabled': True
        },
        'rbac_system_initializer': {
            'type': 'logic',
            'subsystem': 'security_administration',
            'name': 'RBAC System Initializer',
            'description': 'Initializes the RBAC system on application startup',
            'statechart_enabled': True
        },
        'real_time_permission_enforcer': {
            'type': 'logic',
            'subsystem': 'security_administration',
            'name': 'Real-time Permission Enforcer',
            'description': 'Enforces permissions in real-time during user interactions',
            'statechart_enabled': True
        },
        'user_permission_context': {
            'type': 'logic',
            'subsystem': 'security_administration',
            'name': 'User Permission Context',
            'description': 'Manages user permission context throughout the session',
            'statechart_enabled': True
        },
        'workspace_access_validator': {
            'type': 'logic',
            'subsystem': 'security_administration',
            'name': 'Workspace Access Validator',
            'description': 'Validates user access to workspace resources',
            'statechart_enabled': True
        },
        'marketplace_access_controller': {
            'type': 'logic',
            'subsystem': 'flow_authoring_execution',
            'name': 'Marketplace Access Controller',
            'description': 'Controls access to marketplace components and flows',
            'statechart_enabled': True
        },
        # Missing RBAC protected flows
        'export_component_rbac_protected': {
            'type': 'logic',
            'subsystem': 'security_administration',
            'name': 'Export Component (RBAC Protected)',
            'description': 'RBAC-protected component export flow with permission validation',
            'statechart_enabled': True
        },
        'import_component_rbac_protected': {
            'type': 'logic',
            'subsystem': 'security_administration',
            'name': 'Import Component (RBAC Protected)',
            'description': 'RBAC-protected component import flow with permission validation',
            'statechart_enabled': True
        },
        # Integration and Platform Components
        'sso_integration_service': {
            'type': 'logic',
            'subsystem': 'integration_communication',
            'name': 'SSO Integration Service',
            'description': 'Service for Single Sign-On integration and management',
            'statechart_enabled': True
        },
        'main_app': {
            'type': 'logic',
            'subsystem': 'platform_infrastructure',
            'name': 'Main Application',
            'description': 'Main application bootstrap and lifecycle management',
            'statechart_enabled': True
        },
        # Test Nodes
        'frontend_state_tests': {
            'type': 'test',
            'subsystem': 'user_experience_interaction',
            'name': 'Frontend State Tests',
            'description': 'Tests for frontend state management and consistency'
        },
        'mcp_integration_system_tests': {
            'type': 'test',
            'subsystem': 'integration_communication',
            'name': 'MCP Integration System Tests',
            'description': 'System tests for MCP server integration'
        },
        'store_integration_tests': {
            'type': 'test',
            'subsystem': 'flow_authoring_execution',
            'name': 'Store Integration Tests',
            'description': 'Integration tests for component store functionality'
        },
        'websocket_tests': {
            'type': 'test',
            'subsystem': 'integration_communication',
            'name': 'WebSocket Tests',
            'description': 'Tests for WebSocket communication functionality'
        }
    }
    
    for phantom_id in phantom_nodes:
        if phantom_id in phantom_definitions:
            definition = phantom_definitions[phantom_id]
            
            # Find the target subsystem
            for subsystem in app_graph.get('subsystems', []):
                if subsystem['id'] == definition['subsystem']:
                    nodes_data = subsystem.get('app_graph', {}).get('nodes', {})
                    
                    # Determine node type collection
                    if definition['type'] == 'schema':
                        node_collection = 'schema_nodes'
                    elif definition['type'] == 'interface':
                        node_collection = 'interface_nodes'
                    elif definition['type'] == 'logic':
                        node_collection = 'logic_nodes'
                    elif definition['type'] == 'test':
                        node_collection = 'test_nodes'
                    
                    # Create node
                    new_node = {
                        'id': phantom_id,
                        'type': definition['type'],
                        'name': definition['name'],
                        'description': definition['description']
                    }
                    
                    # Add statechart if it's a logic node
                    if definition['type'] == 'logic' and definition.get('statechart_enabled', False):
                        new_node['statechart'] = {
                            'id': phantom_id.replace('_', '').lower() + 'Statechart',
                            'initial': 'idle',
                            'states': {
                                'idle': {
                                    'on': {
                                        'EXECUTE': 'processing'
                                    }
                                },
                                'processing': {
                                    'on': {
                                        'SUCCESS': 'completed',
                                        'ERROR': 'error'
                                    }
                                },
                                'completed': {
                                    'on': {
                                        'RESET': 'idle'
                                    }
                                },
                                'error': {
                                    'on': {
                                        'RETRY': 'processing',
                                        'RESET': 'idle'
                                    }
                                }
                            }
                        }
                    
                    # Add to appropriate collection
                    if node_collection not in nodes_data:
                        nodes_data[node_collection] = []
                    nodes_data[node_collection].append(new_node)
                    
                    print(f"Created phantom node: {phantom_id} in {definition['subsystem']}")
                    break

def fix_orphaned_rbac_nodes(app_graph, edge_id_counter):
    """Fix orphaned RBAC nodes by connecting them to appropriate components."""
    
    # Common RBAC connections
    rbac_connections = [
        ('rbac_enforcement_engine', 'validates_permission'),
        ('audit_logger', 'logs_operation'),
        ('permission_resolver', 'resolves_permission'),
        ('role_hierarchy_manager', 'checks_hierarchy')
    ]
    
    # Resource mappings for RBAC protected flows
    resource_mappings = {
        'create_flow_rbac_protected': ('flow_entity', 'flow_dashboard'),
        'read_flow_rbac_protected': ('flow_entity', 'flow_dashboard'),
        'update_flow_rbac_protected': ('flow_entity', 'flow_editor'),
        'delete_flow_rbac_protected': ('flow_entity', 'flow_dashboard'),
        'execute_flow_rbac_protected': ('flow_entity', 'flow_execution_engine'),
        'share_flow_rbac_protected': ('flow_entity', 'flow_dashboard'),
        'export_flow_rbac_protected': ('flow_entity', 'flow_dashboard'),
        'import_flow_rbac_protected': ('flow_entity', 'flow_dashboard'),
        'duplicate_flow_rbac_protected': ('flow_entity', 'flow_dashboard'),
        'create_component_rbac_protected': ('component_entity', 'component_sidebar'),
        'update_component_rbac_protected': ('component_entity', 'component_sidebar'),
        'delete_component_rbac_protected': ('component_entity', 'component_sidebar'),
        'install_component_rbac_protected': ('component_entity', 'store_page'),
        'publish_component_rbac_protected': ('component_entity', 'store_page'),
        'export_component_rbac_protected': ('component_entity', 'component_sidebar'),
        'import_component_rbac_protected': ('component_entity', 'component_sidebar'),
        'create_user_rbac_protected': ('user_entity', 'user_management_interface'),
        'update_user_rbac_protected': ('user_entity', 'user_management_interface'),
        'delete_user_rbac_protected': ('user_entity', 'user_management_interface'),
        'assign_user_role_rbac_protected': ('user_entity', 'user_management_interface'),
        'revoke_user_role_rbac_protected': ('user_entity', 'user_management_interface'),
        'view_user_permissions_rbac_protected': ('user_entity', 'user_management_interface'),
        'create_workspace_rbac_protected': ('workspace_entity', 'workspace_management_interface'),
        'update_workspace_rbac_protected': ('workspace_entity', 'workspace_management_interface'),
        'delete_workspace_rbac_protected': ('workspace_entity', 'workspace_management_interface'),
        'join_workspace_rbac_protected': ('workspace_entity', 'workspace_management_interface'),
        'leave_workspace_rbac_protected': ('workspace_entity', 'workspace_management_interface'),
        'invite_to_workspace_rbac_protected': ('workspace_entity', 'workspace_management_interface'),
        'manage_workspace_permissions_rbac_protected': ('workspace_entity', 'workspace_management_interface'),
    }
    
    # Find security_administration subsystem
    security_subsystem = None
    for subsystem in app_graph.get('subsystems', []):
        if subsystem['id'] == 'security_administration':
            security_subsystem = subsystem
            break
    
    if not security_subsystem:
        print("Error: Could not find security_administration subsystem")
        return edge_id_counter
    
    # Get orphaned RBAC nodes
    logic_nodes = security_subsystem.get('app_graph', {}).get('nodes', {}).get('logic_nodes', [])
    orphaned_rbac_nodes = [node for node in logic_nodes if node['id'].endswith('_rbac_protected')]
    
    print(f"Fixing {len(orphaned_rbac_nodes)} orphaned RBAC nodes...")
    
    for rbac_node in orphaned_rbac_nodes:
        rbac_id = rbac_node['id']
        print(f"  Processing: {rbac_id}")
        
        # Connect to RBAC infrastructure
        for target_node, relationship in rbac_connections:
            edge = {
                'id': f'rbac_edge_{edge_id_counter}',
                'type': 'logic_dependency',
                'source': rbac_id,
                'target': target_node,
                'relationship': 'depends_on',
                'label': relationship.replace('_', ' ').title(),
                'details': f'{rbac_id} {relationship.replace("_", " ")} via {target_node}',
                'source_subsystem': 'security_administration',
                'target_subsystem': 'security_administration'
            }
            
            add_edge_to_subsystem(app_graph, 'security_administration', edge)
            edge_id_counter += 1
        
        # Connect to resource and interface if mapping exists
        if rbac_id in resource_mappings:
            resource_entity, interface_node = resource_mappings[rbac_id]
            
            # Connect to resource entity
            resource_subsystem = find_subsystem_by_node(app_graph, resource_entity)
            if resource_subsystem:
                edge = {
                    'id': f'rbac_edge_{edge_id_counter}',
                    'type': 'data_operation',
                    'source': rbac_id,
                    'target': resource_entity,
                    'relationship': 'manages',
                    'label': 'Manages Resource',
                    'details': f'{rbac_id} manages {resource_entity} with RBAC validation',
                    'source_subsystem': 'security_administration',
                    'target_subsystem': resource_subsystem
                }
                
                if resource_subsystem == 'security_administration':
                    add_edge_to_subsystem(app_graph, 'security_administration', edge)
                else:
                    add_cross_subsystem_edge(app_graph, edge)
                edge_id_counter += 1
            
            # Connect to interface
            interface_subsystem = find_subsystem_by_node(app_graph, interface_node)
            if interface_subsystem:
                edge = {
                    'id': f'rbac_edge_{edge_id_counter}',
                    'type': 'interface_service',
                    'source': rbac_id,
                    'target': interface_node,
                    'relationship': 'serves',
                    'label': 'Serves Interface',
                    'details': f'{rbac_id} serves {interface_node} with RBAC protection',
                    'source_subsystem': 'security_administration',
                    'target_subsystem': interface_subsystem
                }
                
                if interface_subsystem == 'security_administration':
                    add_edge_to_subsystem(app_graph, 'security_administration', edge)
                else:
                    add_cross_subsystem_edge(app_graph, edge)
                edge_id_counter += 1
    
    print(f"Added connections for {len(orphaned_rbac_nodes)} RBAC nodes")
    return edge_id_counter

def fix_orphaned_platform_nodes(app_graph, edge_id_counter):
    """Fix orphaned platform infrastructure nodes."""
    
    platform_connections = {
        'testing_quality_assurance': [
            ('error_handling_tests', 'manages'),
            ('performance_benchmark_tests', 'manages'),
            ('regression_test_suite', 'manages'),
            ('deployment_orchestration', 'validates')
        ],
        'deployment_orchestration': [
            ('main_app', 'deploys'),
            ('testing_quality_assurance', 'depends_on')
        ]
    }
    
    # Find platform_infrastructure subsystem
    platform_subsystem = None
    for subsystem in app_graph.get('subsystems', []):
        if subsystem['id'] == 'platform_infrastructure':
            platform_subsystem = subsystem
            break
    
    if not platform_subsystem:
        print("Error: Could not find platform_infrastructure subsystem")
        return edge_id_counter
    
    for node_id, connections in platform_connections.items():
        for target_node, relationship in connections:
            target_subsystem = find_subsystem_by_node(app_graph, target_node)
            if target_subsystem:
                edge = {
                    'id': f'edge_{edge_id_counter}',
                    'type': 'logic_dependency',
                    'source': node_id,
                    'target': target_node,
                    'relationship': 'depends_on' if relationship == 'depends_on' else 'manages',
                    'label': relationship.replace('_', ' ').title(),
                    'details': f'{node_id} {relationship.replace("_", " ")} {target_node}',
                    'source_subsystem': 'platform_infrastructure',
                    'target_subsystem': target_subsystem
                }
                
                if target_subsystem == 'platform_infrastructure':
                    add_edge_to_subsystem(app_graph, 'platform_infrastructure', edge)
                else:
                    add_cross_subsystem_edge(app_graph, edge)
                edge_id_counter += 1
    
    return edge_id_counter

def fix_orphaned_test_nodes(app_graph, edge_id_counter):
    """Fix orphaned test nodes by connecting them to what they test."""
    
    test_connections = {
        'error_handling_tests': ('error_boundary', 'tests'),
        'security_access_control_tests': ('rbac_enforcement_engine', 'tests'),
        'performance_benchmark_tests': ('flow_execution_engine', 'benchmarks'),
        'api_integration_tests': ('sso_integration_service', 'tests'),
        'regression_test_suite': ('main_app', 'validates')
    }
    
    for test_id, (target_node, relationship) in test_connections.items():
        target_subsystem = find_subsystem_by_node(app_graph, target_node)
        if target_subsystem:
            edge = {
                'id': f'edge_{edge_id_counter}',
                'type': 'test_relationship',
                'source': test_id,
                'target': target_node,
                'relationship': 'tests',
                'label': relationship.replace('_', ' ').title(),
                'details': f'{test_id} {relationship.replace("_", " ")} {target_node}',
                'source_subsystem': 'user_experience_interaction',
                'target_subsystem': target_subsystem
            }
            
            if target_subsystem == 'user_experience_interaction':
                add_edge_to_subsystem(app_graph, 'user_experience_interaction', edge)
            else:
                add_cross_subsystem_edge(app_graph, edge)
            edge_id_counter += 1
    
    return edge_id_counter

def main():
    if len(sys.argv) != 2:
        print("Usage: python fix_graph_connections.py <graph_file.json>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    output_path = filepath.replace('.json', '_fixed.json')
    
    print(f"Loading app graph from: {filepath}")
    
    try:
        app_graph = load_app_graph(filepath)
        print("App graph loaded successfully!")
        
        # Get starting edge ID counter
        edge_id_counter = get_next_edge_id(app_graph)
        print(f"Starting edge ID counter at: {edge_id_counter}")
        
        # Get phantom nodes (you would need to run the analysis script first)
        phantom_nodes = [
            'admin_role_validator', 'api_security_enforcer', 'background_job_authorizer',
            'compliance_dashboard', 'component_modification_auditor', 'export_component_rbac_protected',
            'flow_execution_audit_logger', 'frontend_state_tests', 'import_component_rbac_protected',
            'main_app', 'marketplace_access_controller', 'mcp_integration_system_tests',
            'rbac_system_initializer', 'real_time_permission_enforcer', 'sso_integration_service',
            'store_integration_tests', 'user_permission_context', 'websocket_tests',
            'workspace_access_validator'
        ]
        
        # Create phantom nodes
        print("Creating phantom nodes...")
        create_phantom_nodes(app_graph, phantom_nodes)
        
        # Fix orphaned RBAC nodes
        print("Fixing orphaned RBAC nodes...")
        edge_id_counter = fix_orphaned_rbac_nodes(app_graph, edge_id_counter)
        
        # Fix orphaned platform nodes
        print("Fixing orphaned platform nodes...")
        edge_id_counter = fix_orphaned_platform_nodes(app_graph, edge_id_counter)
        
        # Fix orphaned test nodes
        print("Fixing orphaned test nodes...")
        edge_id_counter = fix_orphaned_test_nodes(app_graph, edge_id_counter)
        
        # Save the fixed graph
        print(f"Saving fixed graph to: {output_path}")
        save_app_graph(app_graph, output_path)
        
        print("Graph fixing completed successfully!")
        
    except Exception as e:
        print(f"Error fixing app graph: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()