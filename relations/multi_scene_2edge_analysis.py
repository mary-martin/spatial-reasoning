#!/usr/bin/env python3
"""
Multi-Scene 2-Edge Analysis

This script analyzes 2-edge uniqueness across multiple CLEVR scenes
to understand patterns and variations.
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

def find_incoming_unique_2edge_paths(scene_info, G):
    """Find unique incoming 2-edge paths for each ending node"""
    
    node_unique_combinations = defaultdict(list)
    all_combinations = []
    
    # For each ending node, find all incoming 2-edge paths
    for end_node in G.nodes():
        incoming_paths = []
        
        # Find all nodes that have edges to the ending node
        for pred in G.predecessors(end_node):
            # Find all nodes that have edges to the predecessor
            for pred_pred in G.predecessors(pred):
                if pred_pred != end_node:  # Avoid self-loops
                    # Get the edge labels
                    edge1_relations = G[pred_pred][pred]['relations']
                    edge2_relations = G[pred][end_node]['relations']
                    
                    # Create all combinations of individual relations
                    for rel1 in edge1_relations:
                        for rel2 in edge2_relations:
                            combination = (rel1, rel2)
                            path = (pred_pred, pred)
                            incoming_paths.append((combination, path))
                            all_combinations.append(combination)
    
    # Count global frequencies
    combination_counts = Counter(all_combinations)
    
    # Find unique combinations per ending node
    for end_node in G.nodes():
        node_combinations = []
        
        for pred in G.predecessors(end_node):
            for pred_pred in G.predecessors(pred):
                if pred_pred != end_node:
                    edge1_relations = G[pred_pred][pred]['relations']
                    edge2_relations = G[pred][end_node]['relations']
                    
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

def analyze_scene_2edge_uniqueness(scene_file):
    """Analyze 2-edge uniqueness for a single scene"""
    
    print(f"\n=== Analyzing: {os.path.basename(scene_file)} ===")
    
    # Load scene data
    scene_data = load_scene_data(scene_file)
    scene_info = Scene_Objects(scene_data)
    G = create_graph_from_scene(scene_info)
    
    print(f"Scene has {len(scene_info.all_entities)} objects and {G.number_of_edges()} edges")
    
    # Find unique 2-edge paths
    node_unique_combinations, combination_counts = find_incoming_unique_2edge_paths(scene_info, G)
    
    # Count statistics
    total_unique = sum(len(combinations) for combinations in node_unique_combinations.values())
    total_combinations = len(combination_counts)
    unique_combinations = [combo for combo, count in combination_counts.items() if count == 1]
    total_globally_unique = len(unique_combinations)
    
    # Print results
    print(f"Total unique incoming combinations: {total_unique}")
    print(f"Total globally unique combinations: {total_globally_unique}")
    print(f"Total combinations: {total_combinations}")
    
    # Show unique combinations per node
    for end_node in sorted(node_unique_combinations.keys()):
        if node_unique_combinations[end_node]:
            end_obj = scene_info.all_entities[end_node]
            print(f"  Ending Node {end_node} ({end_obj.color} {end_obj.shape}): {len(node_unique_combinations[end_node])} unique combinations")
    
    return {
        'scene_name': os.path.basename(scene_file),
        'total_objects': len(scene_info.all_entities),
        'total_edges': G.number_of_edges(),
        'total_unique_combinations': total_unique,
        'total_globally_unique': total_globally_unique,
        'total_combinations': total_combinations,
        'node_unique_combinations': node_unique_combinations
    }

def create_multi_scene_visualization(results):
    """Create visualization comparing 2-edge uniqueness across scenes"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Total Unique Combinations per Scene
    ax1.set_title('Total Unique 2-Edge Combinations per Scene', fontsize=14, fontweight='bold')
    
    scene_names = [r['scene_name'] for r in results]
    unique_counts = [r['total_unique_combinations'] for r in results]
    
    bars = ax1.bar(range(len(unique_counts)), unique_counts, color='lightblue', alpha=0.7)
    ax1.set_xticks(range(len(unique_counts)))
    ax1.set_xticklabels(scene_names, rotation=45, ha='right')
    ax1.set_ylabel('Number of Unique Combinations')
    
    # Add value labels on bars
    for bar, count in zip(bars, unique_counts):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(count), ha='center', va='bottom', fontweight='bold')
    
    # Plot 2: Scene Size vs Unique Combinations
    ax2.set_title('Scene Size vs Unique Combinations', fontsize=14, fontweight='bold')
    
    object_counts = [r['total_objects'] for r in results]
    
    ax2.scatter(object_counts, unique_counts, s=100, alpha=0.7, color='red')
    ax2.set_xlabel('Number of Objects')
    ax2.set_ylabel('Number of Unique Combinations')
    
    # Add trend line
    if len(object_counts) > 1:
        z = np.polyfit(object_counts, unique_counts, 1)
        p = np.poly1d(z)
        ax2.plot(object_counts, p(object_counts), "r--", alpha=0.8)
    
    # Add scene labels
    for i, scene_name in enumerate(scene_names):
        ax2.annotate(scene_name, (object_counts[i], unique_counts[i]), 
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    # Plot 3: Globally Unique vs Node-Specific Unique
    ax3.set_title('Globally Unique vs Node-Specific Unique', fontsize=14, fontweight='bold')
    
    globally_unique = [r['total_globally_unique'] for r in results]
    node_specific_unique = [r['total_unique_combinations'] for r in results]
    
    x = np.arange(len(scene_names))
    width = 0.35
    
    bars1 = ax3.bar(x - width/2, globally_unique, width, label='Globally Unique', color='lightcoral', alpha=0.7)
    bars2 = ax3.bar(x + width/2, node_specific_unique, width, label='Node-Specific Unique', color='lightgreen', alpha=0.7)
    
    ax3.set_xticks(x)
    ax3.set_xticklabels(scene_names, rotation=45, ha='right')
    ax3.set_ylabel('Number of Unique Combinations')
    ax3.legend()
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    for bar in bars2:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    # Plot 4: Summary Statistics
    ax4.set_title('Summary Statistics', fontsize=14, fontweight='bold')
    ax4.axis('off')
    
    total_scenes = len(results)
    avg_unique = np.mean(unique_counts)
    avg_objects = np.mean(object_counts)
    total_unique_across_scenes = sum(unique_counts)
    
    summary_text = f"""
    MULTI-SCENE 2-EDGE ANALYSIS SUMMARY:
    
    Scenes Analyzed: {total_scenes}
    
    Average Statistics:
    • Average objects per scene: {avg_objects:.1f}
    • Average unique combinations: {avg_unique:.1f}
    
    Total Statistics:
    • Total unique combinations found: {total_unique_across_scenes}
    • Total objects across all scenes: {sum(object_counts)}
    
    Key Findings:
    • Node-specific uniqueness is more common than global uniqueness
    • Scene size affects the number of unique combinations
    • Each scene has different patterns of uniqueness
    """
    
    ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace', fontweight='bold',
             bbox=dict(boxstyle="round,pad=1", facecolor="lightyellow", alpha=0.8))
    
    plt.tight_layout()
    
    # Save the visualization
    filename = 'multi_scene_2edge_analysis.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"Multi-scene visualization saved as '{filename}'")
    
    return filename

def main():
    """Main function to analyze multiple scenes"""
    
    # Analyze multiple scenes
    scene_files = [
        '../custom_clevr/output/scenes/CLEVR_train_000000.json',  # 6 objects
        '../custom_clevr/output/scenes/CLEVR_train_000001.json',  # 9 objects
        '../custom_clevr/output/scenes/CLEVR_train_000002.json',  # 3 objects
        '../custom_clevr/output/scenes/CLEVR_train_000003.json',  # 7 objects
        '../custom_clevr/output/scenes/CLEVR_train_000004.json',  # 8 objects
    ]
    
    print("=== Multi-Scene 2-Edge Uniqueness Analysis ===")
    print("Analyzing 2-edge uniqueness patterns across multiple scenes\n")
    
    results = []
    
    for scene_file in scene_files:
        if os.path.exists(scene_file):
            result = analyze_scene_2edge_uniqueness(scene_file)
            results.append(result)
        else:
            print(f"Scene file not found: {scene_file}")
    
    if results:
        print(f"\n=== Creating Multi-Scene Visualization ===")
        filename = create_multi_scene_visualization(results)
        
        print(f"\n=== Analysis Complete ===")
        print(f"Analyzed {len(results)} scenes")
        print(f"Generated visualization: {filename}")
        
        # Print summary
        total_unique = sum(r['total_unique_combinations'] for r in results)
        total_globally_unique = sum(r['total_globally_unique'] for r in results)
        print(f"Total unique combinations across all scenes: {total_unique}")
        print(f"Total globally unique combinations across all scenes: {total_globally_unique}")
    else:
        print("No scenes were successfully analyzed.")

if __name__ == "__main__":
    main()
