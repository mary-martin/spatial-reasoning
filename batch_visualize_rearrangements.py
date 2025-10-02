#!/usr/bin/env python3
"""
Batch Visualize Scene Rearrangement Expressions

This script creates visualizations for multiple scene rearrangement expression pairs,
showing before and after scene graphs for each pair.
"""

import json
import os
import sys
import argparse
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import copy

# Add the relations directory to the path
sys.path.append('relations')
from scene_objects import Scene_Objects

# Add the refexp generation directory to the path
sys.path.append('custom_clevr/refexp_generation')
import refexp_engine as qeng

# Add the scene rearrangement directory to the path
sys.path.append('scene_rearrangement')
import rearrangement_engine as rearr_eng

def load_scene_data(scene_file):
    """Load scene data from JSON file"""
    with open(scene_file, 'r') as f:
        return json.load(f)

def load_rearrangement_data(rearrangement_file):
    """Load rearrangement expressions data from JSON file"""
    with open(rearrangement_file, 'r') as f:
        return json.load(f)

def create_scene_graph(scene_data):
    """Create a NetworkX graph from scene data"""
    G = nx.DiGraph()
    
    # Add nodes with object information
    for i, obj in enumerate(scene_data['objects']):
        G.add_node(i, 
                  color=obj['color'], 
                  shape=obj['shape'], 
                  size=obj['size'], 
                  material=obj['material'],
                  coords=obj['3d_coords'])
    
    # Add edges based on relationships
    if 'relationships' in scene_data:
        for relation_type, relation_lists in scene_data['relationships'].items():
            for obj_idx, related_objects in enumerate(relation_lists):
                if isinstance(related_objects, list):
                    for related_obj_idx in related_objects:
                        if isinstance(related_obj_idx, int):
                            G.add_edge(obj_idx, related_obj_idx, 
                                     label=relation_type, 
                                     relation=relation_type)
                        elif isinstance(related_obj_idx, list):
                            # Handle nested lists (like in 'between' relationships)
                            for nested_obj_idx in related_obj_idx:
                                if isinstance(nested_obj_idx, int):
                                    G.add_edge(obj_idx, nested_obj_idx, 
                                             label=relation_type, 
                                             relation=relation_type)
    
    return G

def apply_rearrangement_to_scene(scene_data, rearrangement_info):
    """Apply a rearrangement to a scene and return the modified scene"""
    modified_scene = copy.deepcopy(scene_data)
    
    target_object = rearrangement_info.get('target_object')
    reference_object = rearrangement_info.get('reference_object')
    target_relation = rearrangement_info.get('target_relation')
    
    if target_object is None or reference_object is None or target_relation is None:
        return modified_scene
    
    if 'relationships' not in modified_scene:
        modified_scene['relationships'] = {}
    
    if target_relation not in modified_scene['relationships']:
        modified_scene['relationships'][target_relation] = [[] for _ in range(len(modified_scene['objects']))]
    
    if target_object < len(modified_scene['relationships'][target_relation]):
        if reference_object not in modified_scene['relationships'][target_relation][target_object]:
            modified_scene['relationships'][target_relation][target_object].append(reference_object)
    
    # Add inverse relationship
    inverse_relation = get_inverse_relation(target_relation)
    if inverse_relation:
        if inverse_relation not in modified_scene['relationships']:
            modified_scene['relationships'][inverse_relation] = [[] for _ in range(len(modified_scene['objects']))]
        
        if reference_object < len(modified_scene['relationships'][inverse_relation]):
            if target_object not in modified_scene['relationships'][inverse_relation][reference_object]:
                modified_scene['relationships'][inverse_relation][reference_object].append(target_object)
    
    return modified_scene

def get_inverse_relation(relation):
    """Get the inverse of a spatial relation"""
    inverse_map = {
        'left': 'right',
        'right': 'left',
        'front': 'behind',
        'behind': 'front',
        'above': 'below',
        'below': 'above'
    }
    return inverse_map.get(relation)

def get_referent_from_refexp(refexp, scene_data, metadata):
    """Execute a referring expression to get the referent object(s)"""
    try:
        if 'program' in refexp and 'nodes' not in refexp:
            refexp_copy = refexp.copy()
            refexp_copy['nodes'] = refexp['program']
        else:
            refexp_copy = refexp
        
        result = qeng.answer_refexp(refexp_copy, metadata, scene_data, all_outputs=False)
        
        if result == '__INVALID__':
            return None
        elif isinstance(result, int):
            return [result]
        elif isinstance(result, list):
            return result
        else:
            return None
    except Exception as e:
        print(f"Error executing referring expression: {e}")
        return None

def create_batch_rearrangement_visualization(scene_data, rearrangement_pairs, max_pairs=4, 
                                           save_path=None, show_plot=True):
    """
    Create a batch visualization showing multiple rearrangement pairs
    
    Args:
        scene_data: Scene data dictionary
        rearrangement_pairs: List of rearrangement pairs
        max_pairs: Maximum number of pairs to visualize
        save_path: Path to save the plot (optional)
        show_plot: Whether to display the plot
    """
    
    # Get the specific scene
    if 'scenes' in scene_data:
        scene = scene_data['scenes'][0]
    else:
        scene = scene_data
    
    # Limit number of pairs
    pairs_to_show = rearrangement_pairs[:max_pairs]
    num_pairs = len(pairs_to_show)
    
    # Create subplots - 2 rows (original, modified) x num_pairs columns
    fig, axes = plt.subplots(2, num_pairs, figsize=(6*num_pairs, 12))
    if num_pairs == 1:
        axes = axes.reshape(2, 1)
    
    # Create metadata for expression execution
    metadata = {'types': {
        'Size': ['large', 'small'],
        'Color': ['blue', 'brown', 'cyan', 'gray', 'green', 'purple', 'red', 'yellow'],
        'Material': ['metal', 'rubber'],
        'Shape': ['cube', 'cylinder', 'sphere'],
        'Relation': ['left', 'right', 'front', 'behind', 'between', 'nearest', 'farthest']
    }}
    
    for i, pair in enumerate(pairs_to_show):
        # Extract expressions
        original_refexp = pair['original']
        rearrangement_refexp = pair['rearrangement']
        
        # Get rearrangement details
        target_object = rearrangement_refexp.get('target_object')
        reference_object = rearrangement_refexp.get('reference_object')
        target_relation = rearrangement_refexp.get('target_relation')
        
        # Get referents from original expression
        original_referents = get_referent_from_refexp(original_refexp, scene, metadata)
        
        # Apply rearrangement to create modified scene
        modified_scene = apply_rearrangement_to_scene(scene, rearrangement_refexp)
        
        # Create graphs
        original_graph = create_scene_graph(scene)
        modified_graph = create_scene_graph(modified_scene)
        
        # Plot original scene (top row)
        ax_original = axes[0, i]
        ax_original.set_title(f'Pair {i+1}: Original Scene', fontsize=12, fontweight='bold')
        _draw_scene_graph(original_graph, scene, original_referents, 
                         target_object, reference_object, ax_original, "Original")
        
        # Plot modified scene (bottom row)
        ax_modified = axes[1, i]
        ax_modified.set_title(f'Pair {i+1}: After Rearrangement', fontsize=12, fontweight='bold')
        _draw_scene_graph(modified_graph, modified_scene, original_referents, 
                         target_object, reference_object, ax_modified, "Modified")
        
        # Add expression text as subtitle
        expr_text = f'"{rearrangement_refexp["refexp"][:40]}..."'
        fig.text(0.5/num_pairs + i/num_pairs, 0.95, expr_text, 
                ha='center', va='top', fontsize=10, style='italic')
    
    # Add overall title
    fig.suptitle('Scene Rearrangement Visualizations', fontsize=16, fontweight='bold', y=0.98)
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=12, label='Target Object'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=12, label='Reference Object'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', markersize=10, label='Original Referent'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', markersize=8, label='Other Objects')
    ]
    fig.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.92), fontsize=10)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.88, right=0.85)
    
    # Save or show the plot
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Batch visualization saved to: {save_path}")
    
    if show_plot:
        plt.show()
    
    return fig

def _draw_scene_graph(G, scene_data, referents, target_object, reference_object, ax, title_prefix):
    """Helper function to draw a scene graph"""
    
    # Create layout
    pos = nx.spring_layout(G, seed=42, k=2, iterations=30)
    
    # Draw nodes with different colors based on their role
    node_colors = []
    node_sizes = []
    node_labels = {}
    
    for node in G.nodes():
        obj = scene_data['objects'][node]
        node_labels[node] = f"{obj['color']}\n{obj['shape']}\n({node})"
        
        # Determine node color based on role
        if node == target_object:
            node_colors.append('red')
            node_sizes.append(1000)
        elif node == reference_object:
            node_colors.append('orange')
            node_sizes.append(1000)
        elif referents and node in referents:
            node_colors.append('lightgreen')
            node_sizes.append(800)
        else:
            node_colors.append('lightblue')
            node_sizes.append(600)
    
    # Draw the graph
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color='gray', width=1, arrows=True, ax=ax, alpha=0.6)
    nx.draw_networkx_labels(G, pos, node_labels, font_size=6, font_weight='bold', ax=ax)
    
    # Draw edge labels (only for important edges to avoid clutter)
    edge_labels = {}
    for (u, v, data) in G.edges(data=True):
        if u == target_object or v == target_object or u == reference_object or v == reference_object:
            edge_labels[(u, v)] = data.get('label', '')
    
    if edge_labels:
        nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=5, font_color='darkgreen', ax=ax)
    
    ax.axis('off')

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Batch visualize scene rearrangement expressions')
    parser.add_argument('--scene_file', required=True,
                       help='Path to scene JSON file')
    parser.add_argument('--rearrangement_file', required=True,
                       help='Path to rearrangement expressions JSON file')
    parser.add_argument('--max_pairs', type=int, default=4,
                       help='Maximum number of pairs to visualize (default: 4)')
    parser.add_argument('--save_path', 
                       help='Path to save the visualization (optional)')
    parser.add_argument('--no_show', action='store_true',
                       help='Do not display the plot (useful when saving)')
    
    args = parser.parse_args()
    
    # Load data
    print(f"Loading scene data from: {args.scene_file}")
    scene_data = load_scene_data(args.scene_file)
    
    print(f"Loading rearrangement data from: {args.rearrangement_file}")
    rearrangement_data = load_rearrangement_data(args.rearrangement_file)
    
    # Get pairs
    pairs = rearrangement_data['expression_pairs']
    print(f"Found {len(pairs)} rearrangement pairs")
    
    # Create visualization
    print(f"Creating batch visualization for up to {args.max_pairs} pairs")
    fig = create_batch_rearrangement_visualization(
        scene_data, pairs, 
        max_pairs=args.max_pairs,
        save_path=args.save_path,
        show_plot=not args.no_show
    )
    
    if fig:
        print("Batch visualization complete!")
    else:
        print("Batch visualization failed!")

if __name__ == "__main__":
    main()

