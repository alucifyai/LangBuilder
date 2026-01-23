#!/usr/bin/env python3
"""
Comprehensive PRD Reference Analysis and Impact Report Generator
This script consolidates ALL PRD reference details from appgraph.json
"""

import json
import re
from collections import defaultdict
from datetime import datetime

def analyze_appgraph_prd_references(appgraph_path):
    """Perform comprehensive PRD reference analysis with full detail extraction"""
    
    # Load the appgraph
    with open(appgraph_path, 'r') as f:
        appgraph = json.load(f)
    
    # Initialize comprehensive PRD structure
    prd_analysis = defaultdict(lambda: {
        'epic': None,
        'epic_title': None,
        'story': None,
        'story_title': None,
        'acceptance_criteria': [],
        'gherkin_scenarios': [],
        'validation_nodes': [],
        'implementation_nodes': [],
        'edges': [],
        'impact_summary': {
            'new_nodes': [],
            'modified_nodes': [],
            'intact_nodes': []
        }
    })
    
    # Pattern for extracting Epic/Story references
    pattern = re.compile(r'Epic\s+(\d+)\s+Story\s+(\d+\.\d+)')
    
    # Process all nodes
    for node in appgraph.get('nodes', []):
        node_id = node.get('id')
        node_type = node.get('type')
        impact_status = node.get('impact_analysis_status', 'unknown')
        
        # Process validation nodes
        if node_type == 'validation':
            epic = node.get('epic', '')
            story = node.get('story', '')
            
            # Extract epic and story numbers
            epic_match = re.search(r'Epic\s+(\d+)', epic)
            story_match = re.search(r'Story\s+(\d+\.\d+)', story)
            
            if epic_match and story_match:
                key = f"Epic {epic_match.group(1)} Story {story_match.group(1)}"
                
                # Store epic and story details
                if not prd_analysis[key]['epic']:
                    prd_analysis[key]['epic'] = f"Epic {epic_match.group(1)}"
                    prd_analysis[key]['epic_title'] = epic
                if not prd_analysis[key]['story']:
                    prd_analysis[key]['story'] = f"Story {story_match.group(1)}"
                    prd_analysis[key]['story_title'] = story
                
                # Store acceptance criteria
                ac = node.get('acceptance_criteria') or node.get('acceptance_criterion')
                if ac and ac not in prd_analysis[key]['acceptance_criteria']:
                    prd_analysis[key]['acceptance_criteria'].append(ac)
                
                # Store Gherkin scenario
                gherkin = node.get('gherkin', {})
                if gherkin:
                    scenario_detail = {
                        'node_id': node_id,
                        'name': node.get('name'),
                        'scenario': gherkin.get('scenario'),
                        'given': gherkin.get('given'),
                        'when': gherkin.get('when'),
                        'then': gherkin.get('then'),
                        'validates': node.get('validates', []),
                        'dependencies': node.get('dependencies', [])
                    }
                    prd_analysis[key]['gherkin_scenarios'].append(scenario_detail)
                
                # Add to validation nodes list
                prd_analysis[key]['validation_nodes'].append({
                    'id': node_id,
                    'name': node.get('name'),
                    'path': node.get('path'),
                    'status': impact_status
                })
        
        # Process nodes with prd_references field
        if 'prd_references' in node:
            for ref in node.get('prd_references', []):
                match = pattern.search(ref)
                if match:
                    key = f"Epic {match.group(1)} Story {match.group(2)}"
                    
                    # Add to implementation nodes
                    impl_node = {
                        'id': node_id,
                        'type': node_type,
                        'name': node.get('name', ''),
                        'description': node.get('description', ''),
                        'path': node.get('path', ''),
                        'status': impact_status
                    }
                    prd_analysis[key]['implementation_nodes'].append(impl_node)
                    
                    # Categorize by impact status
                    if impact_status == 'new':
                        prd_analysis[key]['impact_summary']['new_nodes'].append(node_id)
                    elif impact_status == 'modified':
                        prd_analysis[key]['impact_summary']['modified_nodes'].append(node_id)
                    elif impact_status == 'intact':
                        prd_analysis[key]['impact_summary']['intact_nodes'].append(node_id)
    
    # Process edges for PRD references
    for edge in appgraph.get('edges', []):
        if 'prd_references' in edge:
            for ref in edge.get('prd_references', []):
                match = pattern.search(ref)
                if match:
                    key = f"Epic {match.group(1)} Story {match.group(2)}"
                    prd_analysis[key]['edges'].append({
                        'id': edge.get('id'),
                        'source': edge.get('source'),
                        'target': edge.get('target'),
                        'type': edge.get('type'),
                        'status': edge.get('impact_analysis_status', 'unknown')
                    })
    
    return dict(prd_analysis), appgraph.get('metadata', {})

def generate_impact_report(prd_analysis, metadata, output_path):
    """Generate comprehensive impact analysis report"""
    
    report_lines = []
    
    # Header
    report_lines.append("# Comprehensive PRD Impact Analysis Report")
    report_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**AppGraph:** {metadata.get('name', 'Unknown')}")
    report_lines.append(f"**Version:** {metadata.get('version', 'Unknown')}")
    report_lines.append(f"**Enhancement:** {metadata.get('enhancement', 'Unknown')}")
    report_lines.append("")
    
    # Executive Summary
    report_lines.append("## Executive Summary")
    report_lines.append("")
    
    # Count statistics
    total_stories = len(prd_analysis)
    stories_with_tests = sum(1 for s in prd_analysis.values() if s['validation_nodes'])
    stories_with_impl = sum(1 for s in prd_analysis.values() if s['implementation_nodes'])
    stories_complete = sum(1 for s in prd_analysis.values() 
                          if s['validation_nodes'] and s['implementation_nodes'])
    
    report_lines.append(f"- **Total PRD Stories:** {total_stories}")
    report_lines.append(f"- **Stories with Implementation:** {stories_with_impl} ({stories_with_impl*100//total_stories if total_stories else 0}%)")
    report_lines.append(f"- **Stories with Tests:** {stories_with_tests} ({stories_with_tests*100//total_stories if total_stories else 0}%)")
    report_lines.append(f"- **Stories Complete (Impl + Tests):** {stories_complete} ({stories_complete*100//total_stories if total_stories else 0}%)")
    report_lines.append("")
    
    # Epic Overview
    report_lines.append("## Epic Overview")
    report_lines.append("")
    
    epics = defaultdict(list)
    for key, data in prd_analysis.items():
        epic = data.get('epic_title') or data.get('epic')
        if epic:
            epics[epic].append(key)
    
    for epic, stories in sorted(epics.items()):
        report_lines.append(f"### {epic}")
        report_lines.append(f"- **Stories:** {len(stories)}")
        impl_count = sum(1 for s in stories if prd_analysis[s]['implementation_nodes'])
        test_count = sum(1 for s in stories if prd_analysis[s]['validation_nodes'])
        report_lines.append(f"- **Implementation Coverage:** {impl_count}/{len(stories)}")
        report_lines.append(f"- **Test Coverage:** {test_count}/{len(stories)}")
        report_lines.append("")
    
    # Detailed Story Analysis
    report_lines.append("## Detailed Story Analysis")
    report_lines.append("")
    
    for key in sorted(prd_analysis.keys()):
        data = prd_analysis[key]
        
        report_lines.append(f"### {key}")
        if data['story_title']:
            report_lines.append(f"**{data['story_title']}**")
        report_lines.append("")
        
        # Acceptance Criteria
        if data['acceptance_criteria']:
            report_lines.append("**Acceptance Criteria:**")
            for ac in data['acceptance_criteria']:
                report_lines.append(f"- {ac}")
            report_lines.append("")
        
        # Implementation Status
        report_lines.append("**Implementation Status:**")
        if data['implementation_nodes']:
            report_lines.append(f"- Total Implementation Nodes: {len(data['implementation_nodes'])}")
            new_count = len(data['impact_summary']['new_nodes'])
            mod_count = len(data['impact_summary']['modified_nodes'])
            intact_count = len(data['impact_summary']['intact_nodes'])
            report_lines.append(f"  - New: {new_count}")
            report_lines.append(f"  - Modified: {mod_count}")
            report_lines.append(f"  - Intact: {intact_count}")
            
            # List key implementation nodes
            report_lines.append("- Key Components:")
            for node in data['implementation_nodes'][:5]:  # Show first 5
                status_icon = "🆕" if node['status'] == 'new' else "📝" if node['status'] == 'modified' else "✓"
                name = node['name'] or node['description'][:50] if node['description'] else node['id']
                report_lines.append(f"  - {status_icon} `{node['id']}` [{node['type']}]: {name}")
            if len(data['implementation_nodes']) > 5:
                report_lines.append(f"  - ... and {len(data['implementation_nodes'])-5} more")
        else:
            report_lines.append("- ⚠️ **No implementation nodes found**")
        report_lines.append("")
        
        # Validation Coverage
        report_lines.append("**Validation Coverage:**")
        if data['validation_nodes']:
            report_lines.append(f"- Validation Nodes: {len(data['validation_nodes'])}")
            report_lines.append(f"- Gherkin Scenarios: {len(data['gherkin_scenarios'])}")
            
            for scenario in data['gherkin_scenarios']:
                report_lines.append(f"  - **{scenario['scenario']}**")
                report_lines.append(f"    - Given: {scenario['given']}")
                report_lines.append(f"    - When: {scenario['when']}")
                if isinstance(scenario['then'], list):
                    report_lines.append(f"    - Then: {len(scenario['then'])} assertions")
                else:
                    report_lines.append(f"    - Then: {scenario['then']}")
                if scenario['validates']:
                    report_lines.append(f"    - Validates: {', '.join(scenario['validates'])}")
        else:
            report_lines.append("- ⚠️ **No validation tests found**")
        report_lines.append("")
        
        report_lines.append("---")
        report_lines.append("")
    
    # Risk Assessment
    report_lines.append("## Risk Assessment")
    report_lines.append("")
    
    # High risk: Stories with implementation but no tests
    high_risk = [k for k, v in prd_analysis.items() 
                 if v['implementation_nodes'] and not v['validation_nodes']]
    if high_risk:
        report_lines.append("### 🔴 High Risk - Implementation without Tests")
        for story in high_risk:
            report_lines.append(f"- {story}: {prd_analysis[story]['story_title']}")
        report_lines.append("")
    
    # Medium risk: Stories with tests but no implementation
    medium_risk = [k for k, v in prd_analysis.items() 
                   if v['validation_nodes'] and not v['implementation_nodes']]
    if medium_risk:
        report_lines.append("### 🟡 Medium Risk - Tests without Implementation")
        for story in medium_risk:
            report_lines.append(f"- {story}: {prd_analysis[story]['story_title']}")
        report_lines.append("")
    
    # Coverage Gaps
    report_lines.append("## Coverage Gaps and Recommendations")
    report_lines.append("")
    
    if stories_complete < total_stories:
        report_lines.append("### Priority Actions")
        report_lines.append("")
        
        if high_risk:
            report_lines.append("1. **Add Tests for Implemented Features:**")
            report_lines.append(f"   - {len(high_risk)} stories have implementation but lack validation tests")
            report_lines.append("")
        
        if medium_risk:
            report_lines.append("2. **Link Tests to Implementation:**")
            report_lines.append(f"   - {len(medium_risk)} stories have tests but no linked implementation")
            report_lines.append("   - This may indicate missing traceability rather than missing implementation")
            report_lines.append("")
    
    # Traceability Matrix
    report_lines.append("## Traceability Matrix Summary")
    report_lines.append("")
    report_lines.append("| Story | Epic | Implementation | Validation | Status |")
    report_lines.append("|-------|------|----------------|------------|--------|")
    
    for key in sorted(prd_analysis.keys()):
        data = prd_analysis[key]
        epic_num = data['epic'].split()[1] if data['epic'] else '-'
        story_num = data['story'].split()[1] if data['story'] else '-'
        impl_count = len(data['implementation_nodes'])
        val_count = len(data['validation_nodes'])
        status = "✅ Complete" if impl_count > 0 and val_count > 0 else "⚠️ Partial" if impl_count > 0 or val_count > 0 else "❌ Missing"
        report_lines.append(f"| {story_num} | {epic_num} | {impl_count} nodes | {val_count} tests | {status} |")
    
    report_lines.append("")
    
    # Write report
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    return output_path

if __name__ == "__main__":
    # Analyze the appgraph
    appgraph_path = "/Users/dongmingjiang/Alucify/LangBuilder/.alucify/appgraph.json"
    output_path = "/Users/dongmingjiang/Alucify/LangBuilder/.alucify/impact-analysis-report-comprehensive.md"
    
    print("Analyzing AppGraph PRD references...")
    prd_analysis, metadata = analyze_appgraph_prd_references(appgraph_path)
    
    print(f"Found {len(prd_analysis)} unique PRD story references")
    
    print("Generating comprehensive impact report...")
    report_path = generate_impact_report(prd_analysis, metadata, output_path)
    
    print(f"Report generated: {report_path}")
    
    # Print summary statistics
    total_impl = sum(len(v['implementation_nodes']) for v in prd_analysis.values())
    total_val = sum(len(v['validation_nodes']) for v in prd_analysis.values())
    total_complete = sum(1 for v in prd_analysis.values() 
                        if v['implementation_nodes'] and v['validation_nodes'])
    
    print(f"\nSummary:")
    print(f"- Total implementation nodes: {total_impl}")
    print(f"- Total validation nodes: {total_val}")
    print(f"- Stories with complete coverage: {total_complete}/{len(prd_analysis)}")