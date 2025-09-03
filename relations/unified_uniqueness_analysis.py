#!/usr/bin/env python3
"""
Unified Uniqueness Analysis

This script combines 1-edge and 2-edge uniqueness analysis methods
to provide a comprehensive view of uniqueness in CLEVR scenes.
"""

import json
import os
import sys
import networkx as nx
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import numpy as np

# Import scene objects for graph creation
sys.path.append('.')
from scene_objects import Scene_Objects

def invert_relation(relation):
    """Invert a spatial relation for incoming path analysis"""
    relation_inversions = {
        'left': 'right',
        'right': 'left', 
        'front': 'behind',
        'behind': 'front',
        'nearest': 'nearest',  # These don't have inverses
        'farthest': 'farthest'
    }
    return relation_inversions.get(relation, relation)

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

def analyze_1edge_uniqueness(scene_info, G):
    """Analyze 1-edge uniqueness (object-specific patterns)"""
    
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

def analyze_2edge_uniqueness(scene_info, G):
    """Analyze 2-edge uniqueness (incoming path patterns with inverted relations)"""
    
    node_unique_combinations = defaultdict(list)
    all_combinations = []
    
    # For each ending node, find all incoming 2-edge paths
    for end_node in G.nodes():
        # Find all nodes that have edges to the ending node
        for pred in G.predecessors(end_node):
            # Find all nodes that have edges to the predecessor
            for pred_pred in G.predecessors(pred):
                if pred_pred != end_node:  # Avoid self-loops
                    # Get the edge labels and INVERT them for incoming analysis
                    edge1_relations = [invert_relation(rel) for rel in G[pred_pred][pred]['relations']]
                    edge2_relations = [invert_relation(rel) for rel in G[pred][end_node]['relations']]
                    
                    # Create all combinations of individual relations
                    for rel1 in edge1_relations:
                        for rel2 in edge2_relations:
                            combination = (rel1, rel2)
                            path = (pred_pred, pred)
                            all_combinations.append(combination)
    
    # Count global frequencies
    combination_counts = Counter(all_combinations)
    
    # Find unique combinations per ending node
    for end_node in G.nodes():
        node_combinations = []
        
        for pred in G.predecessors(end_node):
            for pred_pred in G.predecessors(pred):
                if pred_pred != end_node:
                    # INVERT relations for incoming analysis
                    edge1_relations = [invert_relation(rel) for rel in G[pred_pred][pred]['relations']]
                    edge2_relations = [invert_relation(rel) for rel in G[pred][end_node]['relations']]
                    
                    for rel1 in edge1_relations:
                        for rel2 in edge2_relations:
                            combination = (rel1, rel2)
                            path = (pred_pred, pred)
                            node_combinations.append((combination, path))
        
        # Count combinations for this specific node
        node_combination_counts = Counter([combo for combo, _ in node_combinations])
        
        # Find unique combinations for this node
        for combination, path in node_combinations:
            if node_combination_counts[combination] == 1:
                node_unique_combinations[end_node].append((combination, path))
    
    return node_unique_combinations, combination_counts

def analyze_combined_uniqueness(scene_info, G):
    """Analyze combined 1-edge and 2-edge uniqueness"""
    
    # Get individual analyses
    edge1_results = analyze_1edge_uniqueness(scene_info, G)
    edge2_results, combination_counts = analyze_2edge_uniqueness(scene_info, G)
    
    # Find objects with both types of uniqueness
    objects_with_both_types = []
    objects_with_only_1edge = []
    objects_with_only_2edge = []
    objects_with_neither = []
    
    for obj_idx in G.nodes():
        has_1edge_incoming = any(obj_idx == obj for obj, _ in edge1_results['objects_with_unique_incoming'])
        has_1edge_outgoing = any(obj_idx == obj for obj, _ in edge1_results['objects_with_unique_outgoing'])
        has_2edge = obj_idx in edge2_results and len(edge2_results[obj_idx]) > 0
        
        has_1edge = has_1edge_incoming or has_1edge_outgoing
        
        if has_1edge and has_2edge:
            objects_with_both_types.append(obj_idx)
        elif has_1edge and not has_2edge:
            objects_with_only_1edge.append(obj_idx)
        elif not has_1edge and has_2edge:
            objects_with_only_2edge.append(obj_idx)
        else:
            objects_with_neither.append(obj_idx)
    
    return {
        'edge1_results': edge1_results,
        'edge2_results': edge2_results,
        'combination_counts': combination_counts,
        'objects_with_both_types': objects_with_both_types,
        'objects_with_only_1edge': objects_with_only_1edge,
        'objects_with_only_2edge': objects_with_only_2edge,
        'objects_with_neither': objects_with_neither
    }

def create_unified_visualization(scene_file):
    """Create comprehensive visualization combining 1-edge and 2-edge analysis"""
    
    # Load scene data
    scene_data = load_scene_data(scene_file)
    scene_info = Scene_Objects(scene_data)
    G = create_graph_from_scene(scene_info)
    
    # Analyze combined uniqueness
    combined_results = analyze_combined_uniqueness(scene_info, G)
    
    # Create visualization
    fig = plt.figure(figsize=(20, 12))
    
    # Plot 1: Scene Graph with Combined Uniqueness Highlighted
    ax1 = plt.subplot(3, 4, 1)
    ax1.set_title(f'Scene Graph: {os.path.basename(scene_file)}\n(Combined Uniqueness Highlighted)', 
                  fontsize=14, fontweight='bold')
    
    pos = nx.spring_layout(G, seed=42)
    
    # Draw nodes with different colors based on uniqueness type
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        if node in combined_results['objects_with_both_types']:
            node_colors.append('red')  # Both types
            node_sizes.append(1500)
        elif node in combined_results['objects_with_only_1edge']:
            node_colors.append('orange')  # Only 1-edge
            node_sizes.append(1200)
        elif node in combined_results['objects_with_only_2edge']:
            node_colors.append('green')  # Only 2-edge
            node_sizes.append(1200)
        else:
            node_colors.append('lightblue')  # No uniqueness
            node_sizes.append(800)
    
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax1)
    nx.draw_networkx_edges(G, pos, edge_color='gray', width=1, arrows=True, ax=ax1, alpha=0.7)
    
    # Add node labels
    labels = {node: f"{scene_info.all_entities[node].color}\n{scene_info.all_entities[node].shape}\n({node})" 
              for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold', ax=ax1)
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=15, label='Both Types'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=12, label='Only 1-Edge'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=12, label='Only 2-Edge'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', markersize=10, label='No Uniqueness')
    ]
    ax1.legend(handles=legend_elements, loc='upper right', fontsize=8)
    
    ax1.axis('off')
    
    # Plot 2: Combined Uniqueness Summary
    ax2 = plt.subplot(3, 4, 2)
    ax2.set_title('Combined Uniqueness Summary', fontsize=14, fontweight='bold')
    ax2.axis('off')
    
    total_objects = len(scene_info.all_entities)
    edge1_incoming = len(combined_results['edge1_results']['objects_with_unique_incoming'])
    edge1_outgoing = len(combined_results['edge1_results']['objects_with_unique_outgoing'])
    edge2_total = sum(len(combinations) for combinations in combined_results['edge2_results'].values())
    
    summary_text = f"""
    COMBINED UNIQUENESS ANALYSIS:
    
    Scene Statistics:
    • Total objects: {total_objects}
    
    1-EDGE UNIQUENESS:
    • Objects with unique incoming: {edge1_incoming}
    • Objects with unique outgoing: {edge1_outgoing}
    • Total 1-edge patterns: {edge1_incoming + edge1_outgoing}
    
    2-EDGE UNIQUENESS:
    • Total unique 2-edge combinations: {edge2_total}
    • Objects with 2-edge uniqueness: {len([obj for obj, combinations in combined_results['edge2_results'].items() if combinations])}
    
    COMBINED PATTERNS:
    • Objects with both types: {len(combined_results['objects_with_both_types'])}
    • Objects with only 1-edge: {len(combined_results['objects_with_only_1edge'])}
    • Objects with only 2-edge: {len(combined_results['objects_with_only_2edge'])}
    • Objects with neither: {len(combined_results['objects_with_neither'])}
    """
    
    ax2.text(0.05, 0.95, summary_text, transform=ax2.transAxes, fontsize=9,
             verticalalignment='top', fontfamily='monospace', fontweight='bold',
             bbox=dict(boxstyle="round,pad=1", facecolor="lightgreen", alpha=0.8))
    
    # Plot 3: Uniqueness Type Distribution
    ax3 = plt.subplot(3, 4, 3)
    ax3.set_title('Uniqueness Type Distribution', fontsize=14, fontweight='bold')
    
    uniqueness_types = ['Both Types', 'Only 1-Edge', 'Only 2-Edge', 'Neither']
    uniqueness_counts = [
        len(combined_results['objects_with_both_types']),
        len(combined_results['objects_with_only_1edge']),
        len(combined_results['objects_with_only_2edge']),
        len(combined_results['objects_with_neither'])
    ]
    
    colors = ['red', 'orange', 'green', 'lightblue']
    bars = ax3.bar(uniqueness_types, uniqueness_counts, color=colors, alpha=0.7)
    ax3.set_ylabel('Number of Objects')
    
    # Add value labels on bars
    for bar, count in zip(bars, uniqueness_counts):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(count), ha='center', va='bottom', fontweight='bold')
    
    # Plot 4: 1-Edge vs 2-Edge Comparison
    ax4 = plt.subplot(3, 4, 4)
    ax4.set_title('1-Edge vs 2-Edge Comparison', fontsize=14, fontweight='bold')
    
    edge1_total = edge1_incoming + edge1_outgoing
    edge2_total = edge2_total  # Already calculated above
    
    comparison_types = ['1-Edge Patterns', '2-Edge Combinations']
    comparison_counts = [edge1_total, edge2_total]
    
    colors = ['orange', 'green']
    bars = ax4.bar(comparison_types, comparison_counts, color=colors, alpha=0.7)
    ax4.set_ylabel('Count')
    
    # Add value labels on bars
    for bar, count in zip(bars, comparison_counts):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(count), ha='center', va='bottom', fontweight='bold')
    
    # Plot 5: 1-Edge Incoming Relations per Object
    ax5 = plt.subplot(3, 4, 5)
    ax5.set_title('1-Edge: Unique Incoming Relations per Object', fontsize=14, fontweight='bold')
    
    if combined_results['edge1_results']['objects_with_unique_incoming']:
        object_labels = []
        unique_relations = []
        
        for obj_idx, relations in combined_results['edge1_results']['objects_with_unique_incoming']:
            obj = scene_info.all_entities[obj_idx]
            object_labels.append(f"{obj.color}\n{obj.shape}\n({obj_idx})")
            unique_relations.append(len(relations))
        
        bars = ax5.bar(range(len(unique_relations)), unique_relations, 
                       color='lightgreen', alpha=0.7)
        ax5.set_xticks(range(len(unique_relations)))
        ax5.set_xticklabels(object_labels, fontsize=9, rotation=45)
        ax5.set_ylabel('Number of Unique Incoming Relations')
        
        # Add value labels on bars
        for bar, count in zip(bars, unique_relations):
            ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', va='bottom', fontweight='bold')
    else:
        ax5.text(0.5, 0.5, 'No unique\nincoming relations', ha='center', va='center',
                transform=ax5.transAxes, fontsize=14, fontweight='bold')
    
    # Plot 6: 1-Edge Outgoing Relations per Object
    ax6 = plt.subplot(3, 4, 6)
    ax6.set_title('1-Edge: Unique Outgoing Relations per Object', fontsize=14, fontweight='bold')
    
    if combined_results['edge1_results']['objects_with_unique_outgoing']:
        object_labels = []
        unique_relations = []
        
        for obj_idx, relations in combined_results['edge1_results']['objects_with_unique_outgoing']:
            obj = scene_info.all_entities[obj_idx]
            object_labels.append(f"{obj.color}\n{obj.shape}\n({obj_idx})")
            unique_relations.append(len(relations))
        
        bars = ax6.bar(range(len(unique_relations)), unique_relations, 
                       color='lightcoral', alpha=0.7)
        ax6.set_xticks(range(len(unique_relations)))
        ax6.set_xticklabels(object_labels, fontsize=9, rotation=45)
        ax6.set_ylabel('Number of Unique Outgoing Relations')
        
        # Add value labels on bars
        for bar, count in zip(bars, unique_relations):
            ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', va='bottom', fontweight='bold')
    else:
        ax6.text(0.5, 0.5, 'No unique\noutgoing relations', ha='center', va='center',
                transform=ax6.transAxes, fontsize=14, fontweight='bold')
    
    # Plot 7: 2-Edge Unique Combinations per Object
    ax7 = plt.subplot(3, 4, 7)
    ax7.set_title('2-Edge: Unique Combinations per Object', fontsize=14, fontweight='bold')
    
    objects_with_2edge = [(obj, len(combinations)) for obj, combinations in combined_results['edge2_results'].items() if combinations]
    
    if objects_with_2edge:
        object_labels = []
        unique_combinations = []
        
        for obj_idx, count in objects_with_2edge:
            obj = scene_info.all_entities[obj_idx]
            object_labels.append(f"{obj.color}\n{obj.shape}\n({obj_idx})")
            unique_combinations.append(count)
        
        bars = ax7.bar(range(len(unique_combinations)), unique_combinations, 
                       color='lightblue', alpha=0.7)
        ax7.set_xticks(range(len(unique_combinations)))
        ax7.set_xticklabels(object_labels, fontsize=9, rotation=45)
        ax7.set_ylabel('Number of Unique 2-Edge Combinations')
        
        # Add value labels on bars
        for bar, count in zip(bars, unique_combinations):
            ax7.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', va='bottom', fontweight='bold')
    else:
        ax7.text(0.5, 0.5, 'No unique\n2-edge combinations', ha='center', va='center',
                transform=ax7.transAxes, fontsize=14, fontweight='bold')
    
    # Plot 8: Scene Statistics
    ax8 = plt.subplot(3, 4, 8)
    ax8.set_title('Scene Statistics', fontsize=14, fontweight='bold')
    ax8.axis('off')
    
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
    • Total 1-edge patterns: {edge1_incoming + edge1_outgoing}
    • Total 2-edge combinations: {edge2_total}
    
    Uniqueness Coverage:
    • Objects with any uniqueness: {total_objects - len(combined_results['objects_with_neither'])}
    • Objects with no uniqueness: {len(combined_results['objects_with_neither'])}
    • Uniqueness coverage: {(total_objects - len(combined_results['objects_with_neither']))/total_objects*100:.1f}%
    """
    
    ax8.text(0.05, 0.95, stats_text, transform=ax8.transAxes, fontsize=9,
             verticalalignment='top', fontfamily='monospace', fontweight='bold',
             bbox=dict(boxstyle="round,pad=1", facecolor="lightcyan", alpha=0.8))
    
    # Plot 9: Example Unique Patterns
    ax9 = plt.subplot(3, 4, 9)
    ax9.set_title('Example Unique Patterns', fontsize=14, fontweight='bold')
    ax9.axis('off')
    
    y_pos = 0.95
    ax9.text(0.02, y_pos, "EXAMPLE UNIQUE PATTERNS:", fontsize=12, fontweight='bold', transform=ax9.transAxes)
    y_pos -= 0.05
    
    # Show 1-edge examples
    if combined_results['edge1_results']['objects_with_unique_incoming']:
        obj_idx, relations = combined_results['edge1_results']['objects_with_unique_incoming'][0]
        obj = scene_info.all_entities[obj_idx]
        ax9.text(0.05, y_pos, f"1-Edge: {obj.color} {obj.shape} receives only {relations}", 
                fontsize=9, color='orange', transform=ax9.transAxes)
        y_pos -= 0.04
    
    # Show 2-edge examples
    for obj_idx, combinations in combined_results['edge2_results'].items():
        if combinations:
            obj = scene_info.all_entities[obj_idx]
            combination, path = combinations[0]
            ax9.text(0.05, y_pos, f"2-Edge: {obj.color} {obj.shape} has unique {combination[0]}→{combination[1]} path", 
                    fontsize=9, color='green', transform=ax9.transAxes)
            y_pos -= 0.04
            break
    
    plt.tight_layout()
    
    # Save the visualization
    scene_name = os.path.basename(scene_file).replace('.json', '')
    filename = f'unified_uniqueness_analysis_{scene_name}.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"Unified visualization saved as '{filename}'")
    
    return filename

def main():
    """Main function to create unified analysis"""
    
    # Analyze key scenes
    scene_files = [
        '../custom_clevr/output/scenes/CLEVR_train_000000.json',  # 6 objects
        '../custom_clevr/output/scenes/CLEVR_train_000001.json',  # 9 objects
        '../custom_clevr/output/scenes/CLEVR_train_000002.json',  # 3 objects
    ]
    
    print("=== Unified Uniqueness Analysis ===")
    print("Combining 1-edge and 2-edge uniqueness analysis methods\n")
    
    generated_files = []
    
    for scene_file in scene_files:
        if os.path.exists(scene_file):
            print(f"Processing: {os.path.basename(scene_file)}")
            filename = create_unified_visualization(scene_file)
            generated_files.append(filename)
        else:
            print(f"Scene file not found: {scene_file}")
    
    print(f"\n=== Unified Analysis Complete ===")
    print(f"Generated {len(generated_files)} visualization files:")
    for filename in generated_files:
        print(f"• {filename}")

if __name__ == "__main__":
    main()
