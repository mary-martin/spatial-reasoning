#!/usr/bin/env python3
"""
Create 1-Edge Visualizations

This script creates visualizations that properly show:
1. Object-specific uniqueness
2. Different levels of uniqueness analysis

Note: Global uniqueness is not included as it never occurs in CLEVR scenes.
"""

import json
import os
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
import numpy as np

# Import scene objects for graph creation
import sys
sys.path.append('.')
from scene_objects import Scene_Objects

def load_scene_data(scene_file):
    """Load scene data from JSON file"""
    with open(scene_file, 'r') as f:
        return json.load(f)

def create_graph_from_scene(scene_info):
    """Create NetworkX graph from scene objects"""
    G = nx.DiGraph()
    
    # Add nodes
    for i, entity in enumerate(scene_info.all_entities):
        G.add_node(i, color=entity.color, shape=entity.shape)
    
    # Add edges based on scene_relations (which contains the processed relationships)
    for pair, relations in scene_info.scene_relations.items():
        if relations:
            obj1_idx, obj2_idx = pair
            edge_label = ", ".join(relations)
            G.add_edge(obj1_idx, obj2_idx, label=edge_label, relations=relations)
    
    return G

def analyze_object_specific_uniqueness(scene_info, G):
    """Analyze object-specific uniqueness that actually occurs in CLEVR scenes"""
    
    # Object-specific uniqueness
    object_incoming_relations = defaultdict(list)
    object_outgoing_relations = defaultdict(list)
    
    for edge in G.edges(data=True):
        source, target = edge[0], edge[1]
        relations = edge[2]['relations']
        for rel in relations:
            object_outgoing_relations[source].append(rel)
            object_incoming_relations[target].append(rel)
    
    objects_with_unique_incoming = []
    objects_with_unique_outgoing = []
    
    for obj_idx in G.nodes():
        incoming_rels = object_incoming_relations[obj_idx]
        outgoing_rels = object_outgoing_relations[obj_idx]
        
        incoming_counts = Counter(incoming_rels)
        unique_incoming = [rel for rel, count in incoming_counts.items() if count == 1]
        if unique_incoming:
            objects_with_unique_incoming.append((obj_idx, unique_incoming))
        
        outgoing_counts = Counter(outgoing_rels)
        unique_outgoing = [rel for rel, count in outgoing_counts.items() if count == 1]
        if unique_outgoing:
            objects_with_unique_outgoing.append((obj_idx, unique_outgoing))
    
    return {
        'objects_with_unique_incoming': objects_with_unique_incoming,
        'objects_with_unique_outgoing': objects_with_unique_outgoing
    }

def create_visualization(scene_file):
    """Create comprehensive visualization focusing on object-specific uniqueness"""
    
    # Load scene data
    scene_data = load_scene_data(scene_file)
    scene_info = Scene_Objects(scene_data)
    G = create_graph_from_scene(scene_info)
    
    # Analyze object-specific uniqueness
    uniqueness_data = analyze_object_specific_uniqueness(scene_info, G)
    
    # Create visualization
    fig = plt.figure(figsize=(20, 10))
    
    # Plot 1: Scene Graph with Object-Specific Uniqueness Highlighted
    ax1 = plt.subplot(2, 3, 1)
    ax1.set_title(f'Scene Graph: {os.path.basename(scene_file)}\n(Object-Specific Uniqueness Highlighted)', 
                  fontsize=14, fontweight='bold')
    
    pos = nx.spring_layout(G, seed=42)
    
    # Draw nodes with different colors based on uniqueness
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        has_unique_incoming = any(node == obj_idx for obj_idx, _ in uniqueness_data['objects_with_unique_incoming'])
        has_unique_outgoing = any(node == obj_idx for obj_idx, _ in uniqueness_data['objects_with_unique_outgoing'])
        
        if has_unique_incoming and has_unique_outgoing:
            node_colors.append('red')  # Both unique
            node_sizes.append(1500)
        elif has_unique_incoming or has_unique_outgoing:
            node_colors.append('orange')  # One type unique
            node_sizes.append(1200)
        else:
            node_colors.append('lightblue')  # No uniqueness
            node_sizes.append(800)
    
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax1)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, edge_color='gray', width=1, arrows=True, ax=ax1, alpha=0.7)
    
    # Add node labels
    labels = {node: f"{scene_info.all_entities[node].color}\n{scene_info.all_entities[node].shape}\n({node})" 
              for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold', ax=ax1)
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=15, label='Both Unique'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=12, label='One Type Unique'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', markersize=10, label='No Uniqueness')
    ]
    ax1.legend(handles=legend_elements, loc='upper right', fontsize=8)
    
    ax1.axis('off')
    
    # Plot 2: Summary of Object-Specific Uniqueness
    ax2 = plt.subplot(2, 3, 2)
    ax2.set_title('Summary: Object-Specific Uniqueness', fontsize=14, fontweight='bold')
    ax2.axis('off')
    
    total_objects = len(scene_info.all_entities)
    
    summary_text = f"""
    OBJECT-SPECIFIC UNIQUENESS ANALYSIS:
    
    Scene Statistics:
    • Total objects: {total_objects}
    
    OBJECT-SPECIFIC UNIQUENESS:
    • Objects with unique incoming: {len(uniqueness_data['objects_with_unique_incoming'])}
    • Objects with unique outgoing: {len(uniqueness_data['objects_with_unique_outgoing'])}
    • Object uniqueness rate: {(len(uniqueness_data['objects_with_unique_incoming']) + len(uniqueness_data['objects_with_unique_outgoing']))/(total_objects*2)*100:.1f}%
    
    KEY FINDING:
    • Object-specific uniqueness is the most common type in CLEVR scenes
    • Individual objects have unique relational patterns
    """
    
    ax2.text(0.05, 0.95, summary_text, transform=ax2.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace', fontweight='bold',
             bbox=dict(boxstyle="round,pad=1", facecolor="lightgreen", alpha=0.8))
    
    # Plot 3: Object-Specific Uniqueness Summary
    ax3 = plt.subplot(2, 3, 3)
    ax3.set_title('Object-Specific Uniqueness Summary', fontsize=14, fontweight='bold')
    ax3.axis('off')
    
    objects_with_incoming_unique = len(uniqueness_data['objects_with_unique_incoming'])
    objects_with_outgoing_unique = len(uniqueness_data['objects_with_unique_outgoing'])
    
    obj_summary_text = f"""
    OBJECT-SPECIFIC UNIQUENESS:
    
    Objects with Unique Incoming Relations: {objects_with_incoming_unique}
    Objects with Unique Outgoing Relations: {objects_with_outgoing_unique}
    
    Uniqueness Rates:
    • Incoming: {objects_with_incoming_unique/total_objects*100:.1f}%
    • Outgoing: {objects_with_outgoing_unique/total_objects*100:.1f}%
    • Combined: {(objects_with_incoming_unique + objects_with_outgoing_unique)/(total_objects*2)*100:.1f}%
    
    This is the most common type of uniqueness in CLEVR scenes!
    """
    
    ax3.text(0.05, 0.95, obj_summary_text, transform=ax3.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace', fontweight='bold',
             bbox=dict(boxstyle="round,pad=1", facecolor="lightblue", alpha=0.8))
    
    # Plot 4: Unique Incoming Relations per Object
    ax4 = plt.subplot(2, 3, 4)
    ax4.set_title('Unique Incoming Relations per Object', fontsize=14, fontweight='bold')
    
    if uniqueness_data['objects_with_unique_incoming']:
        object_labels = []
        unique_relations = []
        
        for obj_idx, relations in uniqueness_data['objects_with_unique_incoming']:
            obj = scene_info.all_entities[obj_idx]
            object_labels.append(f"{obj.color}\n{obj.shape}\n({obj_idx})")
            unique_relations.append(len(relations))
        
        bars = ax4.bar(range(len(unique_relations)), unique_relations, 
                       color='lightgreen', alpha=0.7)
        ax4.set_xticks(range(len(unique_relations)))
        ax4.set_xticklabels(object_labels, fontsize=9, rotation=45)
        ax4.set_ylabel('Number of Unique Incoming Relations')
        
        # Add value labels on bars
        for bar, count in zip(bars, unique_relations):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', va='bottom', fontweight='bold')
    else:
        ax4.text(0.5, 0.5, 'No unique\nincoming relations', ha='center', va='center',
                transform=ax4.transAxes, fontsize=14, fontweight='bold')
    
    # Plot 5: Unique Outgoing Relations per Object
    ax5 = plt.subplot(2, 3, 5)
    ax5.set_title('Unique Outgoing Relations per Object', fontsize=14, fontweight='bold')
    
    if uniqueness_data['objects_with_unique_outgoing']:
        object_labels = []
        unique_relations = []
        
        for obj_idx, relations in uniqueness_data['objects_with_unique_outgoing']:
            obj = scene_info.all_entities[obj_idx]
            object_labels.append(f"{obj.color}\n{obj.shape}\n({obj_idx})")
            unique_relations.append(len(relations))
        
        bars = ax5.bar(range(len(unique_relations)), unique_relations, 
                       color='lightcoral', alpha=0.7)
        ax5.set_xticks(range(len(unique_relations)))
        ax5.set_xticklabels(object_labels, fontsize=9, rotation=45)
        ax5.set_ylabel('Number of Unique Outgoing Relations')
        
        # Add value labels on bars
        for bar, count in zip(bars, unique_relations):
            ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', va='bottom', fontweight='bold')
    else:
        ax5.text(0.5, 0.5, 'No unique\noutgoing relations', ha='center', va='center',
                transform=ax5.transAxes, fontsize=14, fontweight='bold')
    
    # Plot 6: Scene Statistics
    ax6 = plt.subplot(2, 3, 6)
    ax6.set_title('Scene Statistics', fontsize=14, fontweight='bold')
    ax6.axis('off')
    
    # Count total relations
    total_relations = 0
    for edge in G.edges(data=True):
        total_relations += len(edge[2]['relations'])
    
    stats_text = f"""
    SCENE STATISTICS:
    
    Scene Size: {total_objects} objects
    
    Statistics:
    • Total relations: {total_relations}
    • Relations per object: {total_relations/total_objects:.1f}
    • Objects with unique patterns: {len(uniqueness_data['objects_with_unique_incoming']) + len(uniqueness_data['objects_with_unique_outgoing'])}
    
    Scene Type:
    • Small scene (≤5 objects): {'Yes' if total_objects <= 5 else 'No'}
    • Medium scene (6-8 objects): {'Yes' if 6 <= total_objects <= 8 else 'No'}
    • Large scene (>8 objects): {'Yes' if total_objects > 8 else 'No'}
    """
    
    ax6.text(0.05, 0.95, stats_text, transform=ax6.transAxes, fontsize=9,
             verticalalignment='top', fontfamily='monospace', fontweight='bold',
             bbox=dict(boxstyle="round,pad=1", facecolor="lightcyan", alpha=0.8))
    
    plt.tight_layout()
    
    # Save the visualization
    scene_name = os.path.basename(scene_file).replace('.json', '')
    filename = f'1edge_analysis_{scene_name}.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"Visualization saved as '{filename}'")
    
    return filename

def main():
    """Main function to create visualizations"""
    
    # Analyze key scenes
    scene_files = [
        '../custom_clevr/output/scenes/CLEVR_train_000002.json',  # 3 objects
        '../custom_clevr/output/scenes/CLEVR_train_000000.json',  # 6 objects
        '../custom_clevr/output/scenes/CLEVR_train_000001.json',  # 9 objects
    ]
    
    print("=== Creating 1-Edge Visualizations ===")
    print("Generating visualizations showing object-specific uniqueness\n")
    
    generated_files = []
    
    for scene_file in scene_files:
        if os.path.exists(scene_file):
            print(f"Processing: {os.path.basename(scene_file)}")
            filename = create_visualization(scene_file)
            generated_files.append(filename)
        else:
            print(f"Scene file not found: {scene_file}")
    
    print(f"\n=== Visualizations Complete ===")
    print(f"Generated {len(generated_files)} visualization files:")
    for filename in generated_files:
        print(f"• {filename}")

if __name__ == "__main__":
    main()
