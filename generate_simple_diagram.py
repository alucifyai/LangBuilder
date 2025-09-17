#!/usr/bin/env python3
"""
Simple LangBuilder Database ER Diagram Generator
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np


def create_simple_er():
    """Create a simplified ER diagram."""
    
    fig, ax = plt.subplots(1, 1, figsize=(20, 14))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Color scheme
    colors = {
        'user': '#E3F2FD',      # Light Blue
        'rbac': '#F3E5F5',      # Light Purple
        'tenant': '#E8F5E8',    # Light Green
        'flow': '#FFF3E0',      # Light Orange
        'audit': '#FFEBEE',     # Light Red
        'api': '#F1F8E9'        # Light Lime
    }
    
    # Core entities with simplified positioning
    entities = [
        # User Management
        ('User', 15, 80, 'user', ['id (PK)', 'username', 'is_active']),
        
        # Multi-tenant Hierarchy
        ('Workspace', 40, 80, 'tenant', ['id (PK)', 'name', 'owner_id (FK)']),
        ('Project', 65, 80, 'tenant', ['id (PK)', 'name', 'workspace_id (FK)']),
        ('Environment', 40, 60, 'tenant', ['id (PK)', 'name', 'project_id (FK)']),
        
        # Flow System
        ('Flow', 65, 60, 'flow', ['id (PK)', 'name', 'data']),
        ('Folder', 15, 60, 'flow', ['id (PK)', 'name', 'parent_id (FK)']),
        
        # RBAC Core
        ('Role', 15, 40, 'rbac', ['id (PK)', 'name', 'workspace_id (FK)']),
        ('Permission', 40, 40, 'rbac', ['id (PK)', 'code', 'action']),
        ('RoleAssignment', 65, 40, 'rbac', ['id (PK)', 'role_id (FK)', 'user_id (FK)']),
        
        # Groups & Service Accounts
        ('UserGroup', 15, 20, 'rbac', ['id (PK)', 'name', 'workspace_id (FK)']),
        ('ServiceAccount', 40, 20, 'api', ['id (PK)', 'name', 'workspace_id (FK)']),
        ('ApiKey', 65, 20, 'api', ['id (PK)', 'api_key', 'user_id (FK)']),
        
        # Audit & Security
        ('AuditLog', 40, 5, 'audit', ['id (PK)', 'event_type', 'timestamp']),
        ('SSOConfiguration', 65, 5, 'api', ['id (PK)', 'provider_type', 'workspace_id (FK)']),
    ]
    
    # Draw entities
    for name, x, y, color_key, fields in entities:
        # Entity box
        box = FancyBboxPatch(
            (x-8, y-6), 16, 12,
            boxstyle="round,pad=0.5",
            facecolor=colors[color_key],
            edgecolor='#333333',
            linewidth=1.5
        )
        ax.add_patch(box)
        
        # Entity name
        ax.text(x, y+4, name, fontsize=10, fontweight='bold', 
                ha='center', va='center')
        
        # Fields
        for i, field in enumerate(fields):
            ax.text(x, y+1-i*2, field, fontsize=8, ha='center', va='center',
                   fontfamily='monospace')
    
    # Key relationships (arrows)
    relationships = [
        (15, 80, 40, 80),  # User -> Workspace
        (40, 80, 65, 80),  # Workspace -> Project
        (65, 80, 40, 60),  # Project -> Environment
        (40, 60, 65, 60),  # Environment -> Flow
        (15, 80, 65, 40),  # User -> RoleAssignment
        (40, 80, 15, 40),  # Workspace -> Role
    ]
    
    for x1, y1, x2, y2 in relationships:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', lw=1, color='#666666'))
    
    # Title
    ax.text(50, 95, 'LangBuilder Database Entity-Relationship Diagram', 
            fontsize=16, fontweight='bold', ha='center')
    
    # Legend
    legend_items = [
        ('User Management', colors['user']),
        ('Multi-tenant', colors['tenant']),
        ('RBAC System', colors['rbac']),
        ('Flow System', colors['flow']),
        ('Audit & Security', colors['audit']),
        ('API & Integration', colors['api'])
    ]
    
    for i, (label, color) in enumerate(legend_items):
        y_pos = 92 - i * 3
        legend_box = FancyBboxPatch(
            (82, y_pos-1), 15, 2,
            boxstyle="round,pad=0.2",
            facecolor=color,
            edgecolor='#333333',
            linewidth=1
        )
        ax.add_patch(legend_box)
        ax.text(89.5, y_pos, label, fontsize=9, ha='center', va='center')
    
    plt.tight_layout()
    return fig


if __name__ == "__main__":
    try:
        print("Generating ER diagram...")
        fig = create_simple_er()
        
        # Save diagrams
        plt.savefig('LangBuilder_ER_Diagram.png', dpi=300, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        plt.savefig('LangBuilder_ER_Diagram.pdf', bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        
        print("✅ ER Diagram generated successfully!")
        print("📄 Files created:")
        print("   - LangBuilder_ER_Diagram.png")
        print("   - LangBuilder_ER_Diagram.pdf")
        
        plt.close(fig)
        
    except Exception as e:
        print(f"❌ Error generating diagram: {e}")
        import traceback
        traceback.print_exc()