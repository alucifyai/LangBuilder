#!/usr/bin/env python3
"""
Script to update the partitioned graph file with distributed edges
"""

import json

# Load the distributed edges
with open('/Users/dongmingjiang/GB/LangBuilder/edge_distributions.json', 'r') as f:
    distributions = json.load(f)

# Load the partitioned graph
with open('/Users/dongmingjiang/GB/LangBuilder/langbuilder_app_graph_partitioned.json', 'r') as f:
    partitioned_graph = json.load(f)

# Map subsystem keys to their order in the partitioned file
subsystem_mapping = {
    0: "user_management_auth",
    1: "flow_development", 
    2: "execution_runtime",
    3: "file_asset_management",
    4: "integration_services",
    5: "system_infrastructure"
}

# Update each subsystem with its distributed edges
for i, (subsystem_index, subsystem_key) in enumerate(subsystem_mapping.items()):
    if subsystem_key in distributions:
        edges = distributions[subsystem_key]["edges"]
        partitioned_graph["partitioned_app_graph"]["subsystems"][subsystem_index]["subsystem_appgraph"]["edges"] = edges
        print(f"Updated {subsystem_key} with {len(edges)} edges")

# Save the updated partitioned graph
with open('/Users/dongmingjiang/GB/LangBuilder/langbuilder_app_graph_partitioned.json', 'w') as f:
    json.dump(partitioned_graph, f, indent=2)

print(f"\nPartitioned graph file updated successfully!")

# Verify edge counts
total_distributed = sum(len(distributions[key]["edges"]) for key in distributions.keys())
print(f"Total edges distributed: {total_distributed}")