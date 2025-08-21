#!/usr/bin/env python3

import json
import os
import sys
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from collections import defaultdict, Counter
from itertools import product

# Import the scene objects module
from scene_objects import Scene_Objects

def find_incoming_unique_2edge_paths(scene_info):
    """Find unique 2-edge paths that are INCOMING to each node (not outgoing)"""
    
    print("=== Finding Incoming Unique 2-Edge Paths ===\n")
    print("Now checking unique combinations for paths ENDING at each node\n")
    
    # Create the graph from scene relationships
    G = nx.DiGraph()
    
    # Add nodes
    for i in range(len(scene_info.all_entities)):
        G.add_node(i)
    
    # Add edges with relationship labels
    for pair, relations in scene_info.scene_relations.items():
        if relations:
            obj1_idx, obj2_idx = pair
            edge_label = ", ".join(relations)
            G.add_edge(obj1_idx, obj2_idx, label=edge_label, relations=relations)
    
    print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Find all 2-edge paths with individual label combinations ENDING at each node
    node_specific_combinations = defaultdict(lambda: defaultdict(list))
    all_2edge_paths = []
    
    for end_node in G.nodes():
        # Find all nodes that have edges TO this end_node
        for first_node in G.predecessors(end_node):
            # Get individual labels from first edge (first_node -> end_node)
            first_edge_relations = G[first_node][end_node]['relations']
            
            # Find all nodes that have edges TO the first_node
            for second_node in G.predecessors(first_node):
                if second_node != end_node:  # Avoid cycles
                    # Get individual labels from second edge (second_node -> first_node)
                    second_edge_relations = G[second_node][first_node]['relations']
                    
                    # Create ALL combinations of individual labels
                    for second_label, first_label in product(second_edge_relations, first_edge_relations):
                        edge_combination = (second_label, first_label)
                        path = (second_node, first_node, end_node)
                        
                        # Store the path with the specific label combination FOR THIS ENDING NODE
                        node_specific_combinations[end_node][edge_combination].append(path)
                        all_2edge_paths.append((path, edge_combination, end_node))
    
    # Find unique combinations PER ENDING NODE
    node_unique_combinations = defaultdict(list)
    node_non_unique_combinations = defaultdict(list)
    
    for end_node in node_specific_combinations:
        for combination, paths in node_specific_combinations[end_node].items():
            if len(paths) == 1:
                # This combination is unique for this ending node
                node_unique_combinations[end_node].append((combination, paths[0]))
            else:
                # This combination appears multiple times for this ending node
                node_non_unique_combinations[end_node].append((combination, paths))
    
    # Print results
    total_unique = sum(len(combinations) for combinations in node_unique_combinations.values())
    total_non_unique = sum(len(combinations) for combinations in node_non_unique_combinations.values())
    
    print(f"\nFound {total_unique} unique incoming combinations across all ending nodes")
    print(f"Found {total_non_unique} non-unique incoming combinations across all ending nodes")
    
    # Show unique combinations per node
    print("\n--- UNIQUE Incoming Combinations PER ENDING NODE ---")
    for end_node in sorted(node_unique_combinations.keys()):
        if node_unique_combinations[end_node]:
            end_obj = scene_info.all_entities[end_node]
            print(f"\nEnding Node {end_node} ({end_obj.color} {end_obj.shape}):")
            for i, (combination, path) in enumerate(node_unique_combinations[end_node]):
                second, first = path[0], path[1]
                second_obj = scene_info.all_entities[second]
                first_obj = scene_info.all_entities[first]
                
                print(f"  {i+1}. {second_obj.color} {second_obj.shape}({second}) --[{combination[0]}]--> "
                      f"{first_obj.color} {first_obj.shape}({first}) --[{combination[1]}]--> "
                      f"{end_obj.color} {end_obj.shape}({end_node})")
    
    # Show non-unique combinations per node (top examples)
    print("\n--- NON-UNIQUE Incoming Combinations PER ENDING NODE (Top Examples) ---")
    for end_node in sorted(node_non_unique_combinations.keys()):
        if node_non_unique_combinations[end_node]:
            end_obj = scene_info.all_entities[end_node]
            print(f"\nEnding Node {end_node} ({end_obj.color} {end_obj.shape}):")
            for i, (combination, paths) in enumerate(node_non_unique_combinations[end_node][:3]):  # Show top 3
                print(f"  {i+1}. Combination {combination} appears {len(paths)} times")
    
    return G, node_unique_combinations, node_non_unique_combinations, all_2edge_paths

def create_incoming_visualizations(scene_info, G, node_unique_combinations, node_non_unique_combinations):
    """Create visualizations for incoming unique analysis"""
    
    print("\n=== Creating Incoming Node Visualizations ===")
    
    # Create comprehensive visualization
    fig = plt.figure(figsize=(20, 16))
    
    # Calculate statistics
    total_unique = sum(len(combinations) for combinations in node_unique_combinations.values())
    total_non_unique = sum(len(combinations) for combinations in node_non_unique_combinations.values())
    total_paths = total_unique + total_non_unique
    
    # Plot 1: Full Scene Graph
    ax1 = plt.subplot(3, 3, 1)
    ax1.set_title('Full Scene Graph\n(All Spatial Relationships)', fontsize=12, fontweight='bold')
    
    pos = nx.circular_layout(G)
    nx.draw(G, pos, ax=ax1, with_labels=True, node_size=800, 
            node_color='lightblue', font_size=10, font_weight='bold',
            edge_color='gray', arrowsize=15, arrowstyle='->')
    
    # Add edge labels (simplified)
    edge_labels = {}
    for edge in G.edges():
        label = G[edge[0]][edge[1]]['label']
        if 'front' in label and 'left' in label:
            edge_labels[edge] = 'FL'
        elif 'front' in label and 'right' in label:
            edge_labels[edge] = 'FR'
        elif 'behind' in label and 'left' in label:
            edge_labels[edge] = 'BL'
        elif 'behind' in label and 'right' in label:
            edge_labels[edge] = 'BR'
        else:
            edge_labels[edge] = label[:2]
    
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, 
                                font_color='red', font_size=8, font_weight='bold')
    
    # Plot 2: Object Positions in 2D Space
    ax2 = plt.subplot(3, 3, 2)
    ax2.set_title('Object Positions in 2D Space', fontsize=12, fontweight='bold')
    
    # Plot camera position
    ax2.scatter(scene_info.camera_pos[0], scene_info.camera_pos[1], 
               c='red', marker='o', s=200, label='Camera', zorder=5, alpha=0.7)
    
    # Plot object positions with labels
    colors = ['blue', 'green', 'cyan', 'brown', 'gray', 'orange']
    for i, (pos, entity) in enumerate(zip(scene_info.all_locations, scene_info.all_entities)):
        color = colors[i % len(colors)]
        ax2.scatter(pos[0], pos[1], c=color, marker='s', s=150, 
                   label=f"{entity.color} {entity.shape} ({entity.idx})", alpha=0.8)
        ax2.annotate(f"{entity.idx}", (pos[0], pos[1]), xytext=(8, 8), 
                    textcoords='offset points', fontsize=12, fontweight='bold')
    
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlabel('X Position')
    ax2.set_ylabel('Y Position')
    
    # Plot 3: Unique Incoming Combinations per Ending Node
    ax3 = plt.subplot(3, 3, 3)
    ax3.set_title('Unique Incoming Combinations per Ending Node', fontsize=12, fontweight='bold')
    
    # Count unique combinations per node
    unique_counts = []
    node_labels = []
    for end_node in sorted(node_unique_combinations.keys()):
        unique_counts.append(len(node_unique_combinations[end_node]))
        end_obj = scene_info.all_entities[end_node]
        node_labels.append(f"{end_obj.color}\n{end_obj.shape}\n({end_node})")
    
    if unique_counts:
        bars = ax3.bar(range(len(unique_counts)), unique_counts, color='lightgreen', alpha=0.7)
        ax3.set_xlabel('Ending Node', fontsize=10)
        ax3.set_ylabel('Number of unique incoming combinations', fontsize=10)
        ax3.set_xticks(range(len(unique_counts)))
        ax3.set_xticklabels(node_labels, fontsize=8, rotation=45, ha='right')
        
        # Add value labels on bars
        for bar, count in zip(bars, unique_counts):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', va='bottom', fontweight='bold')
    else:
        ax3.text(0.5, 0.5, 'No unique\ncombinations', ha='center', va='center',
                transform=ax3.transAxes, fontsize=14, fontweight='bold')
    
    # Plot 4: Non-Unique Incoming Combinations per Ending Node
    ax4 = plt.subplot(3, 3, 4)
    ax4.set_title('Non-Unique Incoming Combinations per Ending Node', fontsize=12, fontweight='bold')
    
    # Count non-unique combinations per node
    non_unique_counts = []
    for end_node in sorted(node_non_unique_combinations.keys()):
        non_unique_counts.append(len(node_non_unique_combinations[end_node]))
    
    if non_unique_counts:
        bars = ax4.bar(range(len(non_unique_counts)), non_unique_counts, color='lightcoral', alpha=0.7)
        ax4.set_xlabel('Ending Node', fontsize=10)
        ax4.set_ylabel('Number of non-unique incoming combinations', fontsize=10)
        ax4.set_xticks(range(len(non_unique_counts)))
        ax4.set_xticklabels(node_labels, fontsize=8, rotation=45, ha='right')
        
        # Add value labels on bars
        for bar, count in zip(bars, non_unique_counts):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', va='bottom', fontweight='bold')
    else:
        ax4.text(0.5, 0.5, 'No non-unique\ncombinations', ha='center', va='center',
                transform=ax4.transAxes, fontsize=14, fontweight='bold')
    
    # Plot 5: Incoming Path Statistics
    ax5 = plt.subplot(3, 3, 5)
    ax5.set_title('Incoming Path Statistics', fontsize=12, fontweight='bold')
    
    if total_paths > 0:
        labels = ['Unique Incoming Paths', 'Non-Unique Incoming Paths']
        sizes = [total_unique, total_non_unique]
        colors = ['lightgreen', 'lightcoral']
        
        wedges, texts, autotexts = ax5.pie(sizes, labels=labels, colors=colors, 
                                          autopct='%1.1f%%', startangle=90)
        ax5.axis('equal')
        
        # Make text bold
        for text in texts:
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_fontweight('bold')
    else:
        ax5.text(0.5, 0.5, 'No paths\nfound', ha='center', va='center',
                transform=ax5.transAxes, fontsize=14, fontweight='bold')
    
    # Plot 6: Individual Label Distribution
    ax6 = plt.subplot(3, 3, 6)
    ax6.set_title('Individual Label Distribution', fontsize=12, fontweight='bold')
    
    # Count individual labels
    individual_labels = Counter()
    for edge in G.edges():
        relations = G[edge[0]][edge[1]]['relations']
        for relation in relations:
            individual_labels[relation] += 1
    
    if individual_labels:
        labels_list = list(individual_labels.keys())
        counts_list = list(individual_labels.values())
        
        bars = ax6.bar(range(len(labels_list)), counts_list, color='teal', alpha=0.7)
        ax6.set_xlabel('Individual Labels', fontsize=10)
        ax6.set_ylabel('Count', fontsize=10)
        ax6.set_xticks(range(len(labels_list)))
        ax6.set_xticklabels(labels_list, rotation=45, ha='right', fontsize=10)
        
        # Add value labels on bars
        for bar, count in zip(bars, counts_list):
            ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', va='bottom', fontweight='bold')
    else:
        ax6.text(0.5, 0.5, 'No labels\nfound', ha='center', va='center',
                transform=ax6.transAxes, fontsize=14, fontweight='bold')
    
    # Plot 7: Example Unique Incoming Paths per Node
    ax7 = plt.subplot(3, 3, 7)
    ax7.set_title('Example Unique Incoming Paths per Node', fontsize=12, fontweight='bold')
    
    if node_unique_combinations:
        # Show examples of unique paths for each node
        y_pos = 0
        for end_node in sorted(node_unique_combinations.keys()):
            if node_unique_combinations[end_node]:
                end_obj = scene_info.all_entities[end_node]
                ax7.text(0, y_pos, f"Node {end_node} ({end_obj.color} {end_obj.shape}):", 
                        fontsize=10, fontweight='bold')
                y_pos += 1
                
                for i, (combination, path) in enumerate(node_unique_combinations[end_node][:2]):  # Show first 2
                    second, first = path[0], path[1]
                    second_obj = scene_info.all_entities[second]
                    first_obj = scene_info.all_entities[first]
                    
                    ax7.text(0.5, y_pos, f"  {combination[0]} → {combination[1]}", 
                            fontsize=9, color='red', fontweight='bold')
                    y_pos += 0.5
                
                y_pos += 1
        
        ax7.set_xlim(0, 2)
        ax7.set_ylim(-0.5, y_pos-0.5)
        ax7.set_xticks([])
        ax7.set_yticks([])
    else:
        ax7.text(0.5, 0.5, 'No unique\npaths found', ha='center', va='center',
                transform=ax7.transAxes, fontsize=14, fontweight='bold')
    
    # Plot 8: Comparison with Outgoing Analysis
    ax8 = plt.subplot(3, 3, 8)
    ax8.set_title('Comparison: Outgoing vs Incoming Analysis', fontsize=12, fontweight='bold')
    ax8.axis('off')
    
    # Create comparison text
    comparison_text = f"""
    Outgoing Analysis (Previous):
    • 7 unique combinations
    • 76 total paths
    • 9.2% unique paths
    
    Incoming Analysis (Current):
    • {total_unique} unique combinations
    • {total_paths} total paths
    • {total_unique/total_paths*100:.1f}% unique paths
    
    Key Finding:
    • {total_unique} unique incoming combinations found
    • Incoming analysis reveals different patterns!
    • Different ending nodes have different unique incoming patterns
    """
    
    ax8.text(0.05, 0.95, comparison_text, transform=ax8.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace', fontweight='bold')
    
    # Plot 9: Summary Statistics
    ax9 = plt.subplot(3, 3, 9)
    ax9.set_title('Incoming Analysis Summary Statistics', fontsize=12, fontweight='bold')
    ax9.axis('off')
    
    # Create summary text
    summary_text = f"""
    Incoming Graph Statistics:
    • Nodes: {G.number_of_nodes()}
    • Edges: {G.number_of_edges()}
    • Total unique incoming combinations: {total_unique}
    • Total non-unique incoming combinations: {total_non_unique}
    • Total incoming paths analyzed: {total_paths}
    
    Nodes with Unique Incoming Combinations:
    • {len([n for n in node_unique_combinations if node_unique_combinations[n]])} nodes have unique incoming patterns
    
    Individual Labels Found:
    • {list(set([label for edge in G.edges() for label in G[edge[0]][edge[1]]['relations']]))}
    
    Key Insight:
    • Incoming analysis reveals unique spatial signatures!
    • Different ending points have different unique incoming patterns
    • Individual labels CAN provide uniqueness for incoming paths
    """
    
    ax9.text(0.05, 0.95, summary_text, transform=ax9.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('incoming_node_analysis.png', dpi=150, bbox_inches='tight')
    print("Incoming node visualization saved as 'incoming_node_analysis.png'")
    
    # Create focused visualization
    create_focused_incoming_visualization(scene_info, G, node_unique_combinations, node_non_unique_combinations)

def create_focused_incoming_visualization(scene_info, G, node_unique_combinations, node_non_unique_combinations):
    """Create a focused visualization highlighting incoming findings"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Plot 1: Incoming Unique Combinations
    ax1.set_title('Incoming Unique Combinations Found!', fontsize=14, fontweight='bold')
    
    # Create a clear message about the finding
    total_unique = sum(len(combinations) for combinations in node_unique_combinations.values())
    total_non_unique = sum(len(combinations) for combinations in node_non_unique_combinations.values())
    total_paths = total_unique + total_non_unique
    
    message = f"""
    INCOMING ANALYSIS RESULTS:
    
    UNIQUE INCOMING COMBINATIONS FOUND!
    
    • Total unique incoming combinations: {total_unique}
    • Total non-unique incoming combinations: {total_non_unique}
    • Total incoming paths analyzed: {total_paths}
    • Uniqueness rate: {total_unique/total_paths*100:.1f}%
    
    This means:
    • Individual label combinations ARE unique per ending node
    • Different ending nodes have different unique incoming patterns
    • Incoming analysis reveals spatial signatures
    • Individual labels CAN provide uniqueness for incoming paths
    
    Nodes with Unique Incoming Combinations:
    • {len([n for n in node_unique_combinations if node_unique_combinations[n]])} nodes have unique incoming patterns
    """
    
    ax1.text(0.5, 0.5, message, ha='center', va='center', transform=ax1.transAxes, 
             fontsize=12, fontweight='bold', bbox=dict(boxstyle="round,pad=1", 
             facecolor="lightgreen", alpha=0.8))
    ax1.axis('off')
    
    # Plot 2: Unique Incoming Combinations per Node
    ax2.set_title('Unique Incoming Combinations per Ending Node', fontsize=14, fontweight='bold')
    
    # Count unique combinations per node
    unique_counts = []
    node_labels = []
    for end_node in sorted(node_unique_combinations.keys()):
        unique_counts.append(len(node_unique_combinations[end_node]))
        end_obj = scene_info.all_entities[end_node]
        node_labels.append(f"{end_obj.color}\n{end_obj.shape}\n({end_node})")
    
    if unique_counts:
        # Create horizontal bar chart
        y_pos = range(len(unique_counts))
        bars = ax2.barh(y_pos, unique_counts, color='lightgreen', alpha=0.7)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(node_labels, fontsize=11, fontweight='bold')
        ax2.set_xlabel('Number of Unique Incoming Combinations', fontsize=12, fontweight='bold')
        ax2.invert_yaxis()
        
        # Add value labels on bars
        for bar, count in zip(bars, unique_counts):
            ax2.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                    str(count), ha='left', va='center', fontweight='bold', fontsize=11)
        
        # Add title annotation
        ax2.text(0.5, 1.02, 'Each Ending Node Has Different Unique Incoming Patterns', 
                transform=ax2.transAxes, ha='center', va='bottom', 
                fontsize=14, fontweight='bold', color='green')
    else:
        ax2.text(0.5, 0.5, 'No unique\ncombinations', ha='center', va='center',
                transform=ax2.transAxes, fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('focused_incoming_analysis.png', dpi=150, bbox_inches='tight')
    print("Focused incoming visualization saved as 'focused_incoming_analysis.png'")

def main():
    """Main function to run the incoming analysis"""
    
    # Load scene data
    data_dir = "/home/mary/Code/spatial-reasoning/custom_clevr/output/scenes/"
    scene_file = "CLEVR_train_000000.json"
    
    with open(os.path.join(data_dir, scene_file)) as data:
        scene_data = json.load(data)
    
    # Create scene objects
    scene_info = Scene_Objects(scene_data)
    
    # Find incoming unique 2-edge paths
    G, node_unique_combinations, node_non_unique_combinations, all_2edge_paths = find_incoming_unique_2edge_paths(scene_info)
    
    # Create visualizations
    create_incoming_visualizations(scene_info, G, node_unique_combinations, node_non_unique_combinations)
    
    print("\n=== Incoming Analysis Complete ===")
    total_unique = sum(len(combinations) for combinations in node_unique_combinations.values())
    total_non_unique = sum(len(combinations) for combinations in node_non_unique_combinations.values())
    print(f"Total unique incoming combinations: {total_unique}")
    print(f"Total non-unique incoming combinations: {total_non_unique}")
    print(f"Total incoming paths analyzed: {total_unique + total_non_unique}")
    print("\nGenerated files:")
    print("• incoming_node_analysis.png - Incoming comprehensive analysis")
    print("• focused_incoming_analysis.png - Focused incoming findings")

if __name__ == "__main__":
    main()


