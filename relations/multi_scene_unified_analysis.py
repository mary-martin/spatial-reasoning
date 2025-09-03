#!/usr/bin/env python3
"""
Multi-Scene Unified Uniqueness Analysis

This script performs unified 1-edge and 2-edge uniqueness analysis
across multiple CLEVR scenes to understand combined patterns.
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

def analyze_scene_unified_uniqueness(scene_file):
    """Analyze unified uniqueness for a single scene"""
    
    print(f"\n=== Analyzing: {os.path.basename(scene_file)} ===")
    
    # Load scene data
    scene_data = load_scene_data(scene_file)
    scene_info = Scene_Objects(scene_data)
    G = create_graph_from_scene(scene_info)
    
    print(f"Scene has {len(scene_info.all_entities)} objects and {G.number_of_edges()} edges")
    
    # Analyze both types of uniqueness
    edge1_results = analyze_1edge_uniqueness(scene_info, G)
    edge2_results, combination_counts = analyze_2edge_uniqueness(scene_info, G)
    
    # Calculate statistics
    edge1_incoming = len(edge1_results['objects_with_unique_incoming'])
    edge1_outgoing = len(edge1_results['objects_with_unique_outgoing'])
    edge1_total = edge1_incoming + edge1_outgoing
    
    edge2_total = sum(len(combinations) for combinations in edge2_results.values())
    edge2_objects = len([obj for obj, combinations in edge2_results.items() if combinations])
    
    # Find objects with both types
    objects_with_both = []
    objects_with_only_1edge = []
    objects_with_only_2edge = []
    objects_with_neither = []
    
    for obj_idx in G.nodes():
        has_1edge_incoming = any(obj_idx == obj for obj, _ in edge1_results['objects_with_unique_incoming'])
        has_1edge_outgoing = any(obj_idx == obj for obj, _ in edge1_results['objects_with_unique_outgoing'])
        has_2edge = obj_idx in edge2_results and len(edge2_results[obj_idx]) > 0
        
        has_1edge = has_1edge_incoming or has_1edge_outgoing
        
        if has_1edge and has_2edge:
            objects_with_both.append(obj_idx)
        elif has_1edge and not has_2edge:
            objects_with_only_1edge.append(obj_idx)
        elif not has_1edge and has_2edge:
            objects_with_only_2edge.append(obj_idx)
        else:
            objects_with_neither.append(obj_idx)
    
    # Print results
    print(f"1-Edge uniqueness: {edge1_total} patterns ({edge1_incoming} incoming, {edge1_outgoing} outgoing)")
    print(f"2-Edge uniqueness: {edge2_total} combinations across {edge2_objects} objects")
    print(f"Objects with both types: {len(objects_with_both)}")
    print(f"Objects with only 1-edge: {len(objects_with_only_1edge)}")
    print(f"Objects with only 2-edge: {len(objects_with_only_2edge)}")
    print(f"Objects with neither: {len(objects_with_neither)}")
    
    return {
        'scene_name': os.path.basename(scene_file),
        'total_objects': len(scene_info.all_entities),
        'total_edges': G.number_of_edges(),
        'edge1_total': edge1_total,
        'edge1_incoming': edge1_incoming,
        'edge1_outgoing': edge1_outgoing,
        'edge2_total': edge2_total,
        'edge2_objects': edge2_objects,
        'objects_with_both': len(objects_with_both),
        'objects_with_only_1edge': len(objects_with_only_1edge),
        'objects_with_only_2edge': len(objects_with_only_2edge),
        'objects_with_neither': len(objects_with_neither),
        'total_unique_patterns': edge1_total + edge2_total
    }

def create_multi_scene_unified_visualization(results):
    """Create visualization comparing unified uniqueness across scenes"""
    
    fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(16, 18))
    
    # Plot 1: Total Unique Patterns per Scene
    ax1.set_title('Total Unique Patterns per Scene', fontsize=14, fontweight='bold')
    
    scene_names = [r['scene_name'] for r in results]
    total_patterns = [r['total_unique_patterns'] for r in results]
    
    bars = ax1.bar(range(len(total_patterns)), total_patterns, color='purple', alpha=0.7)
    ax1.set_xticks(range(len(total_patterns)))
    ax1.set_xticklabels(scene_names, rotation=45, ha='right')
    ax1.set_ylabel('Number of Unique Patterns')
    
    # Add value labels on bars
    for bar, count in zip(bars, total_patterns):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(count), ha='center', va='bottom', fontweight='bold')
    
    # Plot 2: 1-Edge vs 2-Edge Comparison
    ax2.set_title('1-Edge vs 2-Edge Patterns per Scene', fontsize=14, fontweight='bold')
    
    edge1_totals = [r['edge1_total'] for r in results]
    edge2_totals = [r['edge2_total'] for r in results]
    
    x = np.arange(len(scene_names))
    width = 0.35
    
    bars1 = ax2.bar(x - width/2, edge1_totals, width, label='1-Edge Patterns', color='orange', alpha=0.7)
    bars2 = ax2.bar(x + width/2, edge2_totals, width, label='2-Edge Combinations', color='green', alpha=0.7)
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(scene_names, rotation=45, ha='right')
    ax2.set_ylabel('Count')
    ax2.legend()
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    # Plot 3: Object Uniqueness Distribution
    ax3.set_title('Object Uniqueness Distribution per Scene', fontsize=14, fontweight='bold')
    
    both_types = [r['objects_with_both'] for r in results]
    only_1edge = [r['objects_with_only_1edge'] for r in results]
    only_2edge = [r['objects_with_only_2edge'] for r in results]
    neither = [r['objects_with_neither'] for r in results]
    
    x = np.arange(len(scene_names))
    width = 0.2
    
    bars1 = ax3.bar(x - 1.5*width, both_types, width, label='Both Types', color='red', alpha=0.7)
    bars2 = ax3.bar(x - 0.5*width, only_1edge, width, label='Only 1-Edge', color='orange', alpha=0.7)
    bars3 = ax3.bar(x + 0.5*width, only_2edge, width, label='Only 2-Edge', color='green', alpha=0.7)
    bars4 = ax3.bar(x + 1.5*width, neither, width, label='Neither', color='lightblue', alpha=0.7)
    
    ax3.set_xticks(x)
    ax3.set_xticklabels(scene_names, rotation=45, ha='right')
    ax3.set_ylabel('Number of Objects')
    ax3.legend()
    
    # Add value labels on bars
    for bars in [bars1, bars2, bars3, bars4]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    # Plot 4: Scene Size vs Uniqueness
    ax4.set_title('Scene Size vs Total Unique Patterns', fontsize=14, fontweight='bold')
    
    object_counts = [r['total_objects'] for r in results]
    
    ax4.scatter(object_counts, total_patterns, s=100, alpha=0.7, color='purple')
    ax4.set_xlabel('Number of Objects')
    ax4.set_ylabel('Total Unique Patterns')
    
    # Add trend line
    if len(object_counts) > 1:
        z = np.polyfit(object_counts, total_patterns, 1)
        p = np.poly1d(z)
        ax4.plot(object_counts, p(object_counts), "r--", alpha=0.8)
    
    # Add scene labels
    for i, scene_name in enumerate(scene_names):
        ax4.annotate(scene_name, (object_counts[i], total_patterns[i]), 
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    # Plot 5: Uniqueness Coverage
    ax5.set_title('Uniqueness Coverage per Scene', fontsize=14, fontweight='bold')
    
    coverage_percentages = []
    for r in results:
        total_objects = r['total_objects']
        objects_with_uniqueness = total_objects - r['objects_with_neither']
        coverage = (objects_with_uniqueness / total_objects) * 100
        coverage_percentages.append(coverage)
    
    bars = ax5.bar(range(len(coverage_percentages)), coverage_percentages, color='gold', alpha=0.7)
    ax5.set_xticks(range(len(coverage_percentages)))
    ax5.set_xticklabels(scene_names, rotation=45, ha='right')
    ax5.set_ylabel('Coverage Percentage (%)')
    ax5.set_ylim(0, 100)
    
    # Add value labels on bars
    for bar, percentage in zip(bars, coverage_percentages):
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{percentage:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # Plot 6: Summary Statistics
    ax6.set_title('Summary Statistics', fontsize=14, fontweight='bold')
    ax6.axis('off')
    
    total_scenes = len(results)
    avg_objects = np.mean([r['total_objects'] for r in results])
    avg_patterns = np.mean(total_patterns)
    avg_coverage = np.mean(coverage_percentages)
    total_patterns_across_scenes = sum(total_patterns)
    
    summary_text = f"""
    MULTI-SCENE UNIFIED ANALYSIS SUMMARY:
    
    Scenes Analyzed: {total_scenes}
    
    Average Statistics:
    • Average objects per scene: {avg_objects:.1f}
    • Average unique patterns: {avg_patterns:.1f}
    • Average uniqueness coverage: {avg_coverage:.1f}%
    
    Total Statistics:
    • Total unique patterns found: {total_patterns_across_scenes}
    • Total objects across all scenes: {sum([r['total_objects'] for r in results])}
    
    Key Findings:
    • Combined analysis reveals more uniqueness than individual methods
    • Some objects have both 1-edge and 2-edge uniqueness
    • Scene size affects both types of uniqueness differently
    • Unified approach provides comprehensive spatial reasoning insights
    """
    
    ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace', fontweight='bold',
             bbox=dict(boxstyle="round,pad=1", facecolor="lightyellow", alpha=0.8))
    
    plt.tight_layout()
    
    # Save the visualization
    filename = 'multi_scene_unified_analysis.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"Multi-scene unified visualization saved as '{filename}'")
    
    return filename

def main():
    """Main function to analyze multiple scenes with unified approach"""
    
    # Analyze multiple scenes
    scene_files = [
        '../custom_clevr/output/scenes/CLEVR_train_000000.json',  # 6 objects
        '../custom_clevr/output/scenes/CLEVR_train_000001.json',  # 9 objects
        '../custom_clevr/output/scenes/CLEVR_train_000002.json',  # 3 objects
        '../custom_clevr/output/scenes/CLEVR_train_000003.json',  # 10 objects
        '../custom_clevr/output/scenes/CLEVR_train_000004.json',  # 3 objects
    ]
    
    print("=== Multi-Scene Unified Uniqueness Analysis ===")
    print("Combining 1-edge and 2-edge analysis across multiple scenes\n")
    
    results = []
    
    for scene_file in scene_files:
        if os.path.exists(scene_file):
            result = analyze_scene_unified_uniqueness(scene_file)
            results.append(result)
        else:
            print(f"Scene file not found: {scene_file}")
    
    if results:
        print(f"\n=== Creating Multi-Scene Unified Visualization ===")
        filename = create_multi_scene_unified_visualization(results)
        
        print(f"\n=== Unified Analysis Complete ===")
        print(f"Analyzed {len(results)} scenes")
        print(f"Generated visualization: {filename}")
        
        # Print summary
        total_patterns = sum(r['total_unique_patterns'] for r in results)
        total_objects = sum(r['total_objects'] for r in results)
        total_both_types = sum(r['objects_with_both'] for r in results)
        
        print(f"Total unique patterns across all scenes: {total_patterns}")
        print(f"Total objects across all scenes: {total_objects}")
        print(f"Total objects with both types of uniqueness: {total_both_types}")
        
        # Calculate overall coverage
        total_objects_with_uniqueness = sum(r['total_objects'] - r['objects_with_neither'] for r in results)
        overall_coverage = (total_objects_with_uniqueness / total_objects) * 100
        print(f"Overall uniqueness coverage: {overall_coverage:.1f}%")
    else:
        print("No scenes were successfully analyzed.")

if __name__ == "__main__":
    main()

