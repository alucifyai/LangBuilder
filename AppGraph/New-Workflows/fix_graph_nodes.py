#!/usr/bin/env python3
"""
Script to fix orphaned and phantom nodes in the LangBuilder app graph.
"""

import json
import sys
from collections import defaultdict, Counter

def load_app_graph(filepath):
    """Load the app graph JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_all_nodes(app_graph):
    """Extract all node IDs from the app graph."""
    all_nodes = set()
    
    # Extract nodes from each subsystem
    for subsystem in app_graph.get('subsystems', []):
        app_graph_data = subsystem.get('app_graph', {})
        nodes_data = app_graph_data.get('nodes', {})
        
        # Add schema nodes
        for node in nodes_data.get('schema_nodes', []):
            all_nodes.add(node['id'])
        
        # Add interface nodes
        for node in nodes_data.get('interface_nodes', []):
            all_nodes.add(node['id'])
        
        # Add logic nodes
        for node in nodes_data.get('logic_nodes', []):
            all_nodes.add(node['id'])
        
        # Add test nodes
        for node in nodes_data.get('test_nodes', []):
            all_nodes.add(node['id'])
    
    return all_nodes

def extract_all_edges(app_graph):
    """Extract all edges from the app graph."""
    all_edges = []
    subsystem_edges = []
    
    # Extract edges from each subsystem
    for subsystem in app_graph.get('subsystems', []):
        app_graph_data = subsystem.get('app_graph', {})
        edges = app_graph_data.get('edges', [])
        
        for edge in edges:
            if 'source' in edge and 'target' in edge:
                all_edges.append({
                    'id': edge.get('id', 'unknown'),
                    'source': edge['source'],
                    'target': edge['target'],
                    'subsystem': subsystem['id']
                })
                subsystem_edges.append(edge)
    
    # Extract cross-subsystem edges
    cross_subsystem_edges = app_graph.get('edges', [])
    for edge in cross_subsystem_edges:
        if 'source' in edge and 'target' in edge:
            all_edges.append({
                'id': edge.get('id', 'unknown'),
                'source': edge['source'],
                'target': edge['target'],
                'subsystem': 'cross-subsystem'
            })
    
    return all_edges, subsystem_edges, cross_subsystem_edges

def find_orphaned_and_phantom_nodes(all_nodes, all_edges):
    """Find orphaned nodes (no connections) and phantom nodes (referenced but don't exist)."""
    
    # Nodes that appear in edges
    nodes_in_edges = set()
    for edge in all_edges:
        nodes_in_edges.add(edge['source'])
        nodes_in_edges.add(edge['target'])
    
    # Orphaned nodes: exist but not in any edge
    orphaned_nodes = all_nodes - nodes_in_edges
    
    # Phantom nodes: referenced in edges but don't exist as nodes
    phantom_nodes = nodes_in_edges - all_nodes
    
    return orphaned_nodes, phantom_nodes

def categorize_nodes_by_subsystem(app_graph):
    """Categorize nodes by subsystem."""
    nodes_by_subsystem = defaultdict(lambda: defaultdict(list))
    
    for subsystem in app_graph.get('subsystems', []):
        subsystem_id = subsystem['id']
        app_graph_data = subsystem.get('app_graph', {})
        nodes_data = app_graph_data.get('nodes', {})
        
        for node_type in ['schema_nodes', 'interface_nodes', 'logic_nodes', 'test_nodes']:
            for node in nodes_data.get(node_type, []):
                nodes_by_subsystem[subsystem_id][node_type].append(node)
    
    return nodes_by_subsystem

def analyze_orphaned_by_subsystem(orphaned_nodes, nodes_by_subsystem):
    """Analyze orphaned nodes by subsystem."""
    orphaned_by_subsystem = defaultdict(lambda: defaultdict(list))
    
    for subsystem_id, node_types in nodes_by_subsystem.items():
        for node_type, nodes in node_types.items():
            for node in nodes:
                if node['id'] in orphaned_nodes:
                    orphaned_by_subsystem[subsystem_id][node_type].append(node)
    
    return orphaned_by_subsystem

def print_analysis(orphaned_nodes, phantom_nodes, orphaned_by_subsystem):
    """Print analysis of orphaned and phantom nodes."""
    
    print(f"=== ORPHANED NODES ANALYSIS ===")
    print(f"Total orphaned nodes: {len(orphaned_nodes)}")
    print()
    
    total_orphaned_by_subsystem = 0
    for subsystem_id, node_types in orphaned_by_subsystem.items():
        subsystem_total = sum(len(nodes) for nodes in node_types.values())
        total_orphaned_by_subsystem += subsystem_total
        
        if subsystem_total > 0:
            print(f"{subsystem_id}: {subsystem_total} orphaned")
            for node_type, nodes in node_types.items():
                if nodes:
                    print(f"  - {node_type}: {len(nodes)}")
                    for node in nodes[:5]:  # Show first 5 examples
                        print(f"    * {node['id']}")
                    if len(nodes) > 5:
                        print(f"    ... and {len(nodes) - 5} more")
            print()
    
    print(f"=== PHANTOM NODES ANALYSIS ===")
    print(f"Total phantom nodes: {len(phantom_nodes)}")
    if phantom_nodes:
        print("Phantom nodes (referenced in edges but don't exist):")
        for phantom in sorted(phantom_nodes):
            print(f"  - {phantom}")
    print()

def main():
    if len(sys.argv) != 2:
        print("Usage: python fix_graph_nodes.py <graph_file.json>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    print(f"Loading app graph from: {filepath}")
    
    try:
        app_graph = load_app_graph(filepath)
        print("App graph loaded successfully!")
        
        # Extract all nodes and edges
        all_nodes = extract_all_nodes(app_graph)
        all_edges, subsystem_edges, cross_edges = extract_all_edges(app_graph)
        
        print(f"Total nodes: {len(all_nodes)}")
        print(f"Total edges: {len(all_edges)} (subsystem: {len(subsystem_edges)}, cross-subsystem: {len(cross_edges)})")
        
        # Find orphaned and phantom nodes
        orphaned_nodes, phantom_nodes = find_orphaned_and_phantom_nodes(all_nodes, all_edges)
        
        # Categorize nodes by subsystem
        nodes_by_subsystem = categorize_nodes_by_subsystem(app_graph)
        orphaned_by_subsystem = analyze_orphaned_by_subsystem(orphaned_nodes, nodes_by_subsystem)
        
        # Print analysis
        print_analysis(orphaned_nodes, phantom_nodes, orphaned_by_subsystem)
        
        return app_graph, all_nodes, all_edges, orphaned_nodes, phantom_nodes, orphaned_by_subsystem
        
    except Exception as e:
        print(f"Error loading app graph: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()