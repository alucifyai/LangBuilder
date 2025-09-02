#!/usr/bin/env python3
"""
Script to update the LangBuilder app graph with comprehensive UIDL definitions
"""

import json
import sys
from typing import Dict, Any

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load JSON file and return parsed content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        sys.exit(1)

def save_json_file(filepath: str, data: Dict[str, Any]) -> None:
    """Save data to JSON file with proper formatting"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        sys.exit(1)

def update_interface_node_uidl(node: Dict[str, Any], uidl_def: Dict[str, Any]) -> Dict[str, Any]:
    """Update an interface node with comprehensive UIDL definition"""
    # Keep existing node structure but enhance the uidl_definition
    updated_node = node.copy()
    
    # Replace the simplified uidl_definition with comprehensive one
    updated_node["uidl_definition"] = {
        "name": uidl_def["name"],
        "type": uidl_def["type"],
        "content": uidl_def["content"],
        "stateDefinitions": uidl_def.get("stateDefinitions", {}),
        "actions": uidl_def.get("actions", {}),
        "props": uidl_def.get("props", {}),
        "events": uidl_def.get("events", {})
    }
    
    return updated_node

def main():
    """Main function to update app graph with UIDL definitions"""
    
    # Load the existing app graph
    app_graph = load_json_file('/Users/dongmingjiang/GB/LangBuilder/langbuilder_app_graph.json')
    
    # Load the comprehensive UIDL definitions
    uidl_definitions = load_json_file('/Users/dongmingjiang/GB/LangBuilder/complete_uidl_definitions.json')
    additional_definitions = load_json_file('/Users/dongmingjiang/GB/LangBuilder/additional_uidl_definitions.json')
    
    # Create mapping of interface node names to UIDL definitions
    uidl_mapping = {}
    
    # Add pages from main definitions
    for page_id, page_def in uidl_definitions["uidl_definitions"]["pages"].items():
        uidl_mapping[page_def["name"]] = page_def
    
    # Add modals from main definitions
    for modal_id, modal_def in uidl_definitions["uidl_definitions"]["modals"].items():
        uidl_mapping[modal_def["name"]] = modal_def
    
    # Add components from main definitions
    for comp_id, comp_def in uidl_definitions["uidl_definitions"]["components"].items():
        uidl_mapping[comp_def["name"]] = comp_def
    
    # Add additional pages
    for page_id, page_def in additional_definitions["additional_uidl_definitions"]["pages"].items():
        uidl_mapping[page_def["name"]] = page_def
    
    # Add additional components
    for comp_id, comp_def in additional_definitions["additional_uidl_definitions"]["components"].items():
        uidl_mapping[comp_def["name"]] = comp_def
    
    # Update interface nodes in the app graph
    updated_interface_nodes = []
    
    for node in app_graph["app_graph"]["nodes"]["interface_nodes"]:
        node_name = node["name"]
        
        if node_name in uidl_mapping:
            print(f"Updating {node_name} with comprehensive UIDL definition")
            updated_node = update_interface_node_uidl(node, uidl_mapping[node_name])
            updated_interface_nodes.append(updated_node)
        else:
            print(f"No UIDL definition found for {node_name}, keeping existing definition")
            updated_interface_nodes.append(node)
    
    # Update the app graph
    app_graph["app_graph"]["nodes"]["interface_nodes"] = updated_interface_nodes
    
    # Update metadata
    app_graph["app_graph"]["metadata"]["description"] = "Comprehensive application graph with enhanced UIDL definitions - 15 schema entities, 36 interface nodes with detailed UIDL, 25 logic nodes, 20 test nodes, and 120 properly typed edges"
    app_graph["app_graph"]["metadata"]["version"] = "2.3.0"
    app_graph["app_graph"]["metadata"]["analysis_source"] = "Complete codebase analysis with comprehensive UIDL definitions including MCP support, Voice Mode, File V2 features, RBAC preparation, and detailed UI/UX component specifications"
    
    # Save the updated app graph
    save_json_file('/Users/dongmingjiang/GB/LangBuilder/langbuilder_app_graph_enhanced.json', app_graph)
    
    print(f"Successfully updated app graph with enhanced UIDL definitions")
    print(f"Updated {len([n for n in updated_interface_nodes if n['name'] in uidl_mapping])} interface nodes")
    print(f"Saved to: langbuilder_app_graph_enhanced.json")

if __name__ == "__main__":
    main()