#!/usr/bin/env python3
"""
Visualize Scene Rearrangement Expressions

This script visualizes scene graphs before and after rearrangement expressions are applied.
It shows the original scene graph, the modified scene graph, and highlights the objects
involved in the rearrangement.
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
    """
    Apply a rearrangement to a scene and return the modified scene.
    
    Args:
        scene_data: Original scene data
        rearrangement_info: Dictionary containing rearrangement details
    
    Returns:
        Modified scene data with updated relationships
    """
    # Create a deep copy of the scene
    modified_scene = copy.deepcopy(scene_data)
    
    # Extract rearrangement details
    target_object = rearrangement_info.get('target_object')
    reference_object = rearrangement_info.get('reference_object')
    target_relation = rearrangement_info.get('target_relation')
    
    if target_object is None or reference_object is None or target_relation is None:
        return modified_scene
    
    # Ensure relationships exist
    if 'relationships' not in modified_scene:
        modified_scene['relationships'] = {}
    
    # Initialize the target relation if it doesn't exist
    if target_relation not in modified_scene['relationships']:
        modified_scene['relationships'][target_relation] = [[] for _ in range(len(modified_scene['objects']))]
    
    # Add the new relationship
    # target_object is now in target_relation with reference_object
    if target_object < len(modified_scene['relationships'][target_relation]):
        if reference_object not in modified_scene['relationships'][target_relation][target_object]:
            modified_scene['relationships'][target_relation][target_object].append(reference_object)
    
    # Also add the inverse relationship
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
        # Convert program structure to nodes structure if needed
        if 'program' in refexp and 'nodes' not in refexp:
            refexp_copy = refexp.copy()
            refexp_copy['nodes'] = refexp['program']
        else:
            refexp_copy = refexp
        
        # Execute the referring expression program
        result = qeng.answer_refexp(refexp_copy, metadata, scene_data, all_outputs=False)
        
        # Handle different result types
        if result == '__INVALID__':
            return None
        elif isinstance(result, int):
            return [result]  # Single object
        elif isinstance(result, list):
            return result    # Multiple objects
        else:
            return None
    except Exception as e:
        print(f"Error executing referring expression: {e}")
        return None

def visualize_scene_rearrangement(scene_data, rearrangement_pair, pair_idx=0, 
                                save_path=None, show_plot=True):
    """
    Visualize scene graph before and after rearrangement
    
    Args:
        scene_data: Scene data dictionary
        rearrangement_pair: Dictionary containing original and rearrangement expressions
        pair_idx: Index of the pair (for display)
        save_path: Path to save the plot (optional)
        show_plot: Whether to display the plot
    """
    
    # Get the specific scene
    if 'scenes' in scene_data:
        scene = scene_data['scenes'][0]  # Assuming we're working with the first scene
    else:
        scene = scene_data
    
    # Extract expressions
    original_refexp = rearrangement_pair['original']
    rearrangement_refexp = rearrangement_pair['rearrangement']
    
    # Get rearrangement details
    target_object = rearrangement_refexp.get('target_object')
    reference_object = rearrangement_refexp.get('reference_object')
    target_relation = rearrangement_refexp.get('target_relation')
    
    # Create metadata for expression execution
    metadata = {'types': {
        'Size': ['large', 'small'],
        'Color': ['blue', 'brown', 'cyan', 'gray', 'green', 'purple', 'red', 'yellow'],
        'Material': ['metal', 'rubber'],
        'Shape': ['cube', 'cylinder', 'sphere'],
        'Relation': ['left', 'right', 'front', 'behind', 'between', 'nearest', 'farthest']
    }}
    
    # Get referents from original expression
    original_referents = get_referent_from_refexp(original_refexp, scene, metadata)
    
    # Apply rearrangement to create modified scene
    modified_scene = apply_rearrangement_to_scene(scene, rearrangement_refexp)
    
    # Create graphs
    original_graph = create_scene_graph(scene)
    modified_graph = create_scene_graph(modified_scene)
    
    # Create the visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # Plot 1: Original Scene Graph
    ax1.set_title('Original Scene Graph', fontsize=14, fontweight='bold')
    _draw_scene_graph(original_graph, scene, original_referents, 
                     target_object, reference_object, ax1, "Original")
    
    # Plot 2: Modified Scene Graph
    ax2.set_title('Modified Scene Graph (After Rearrangement)', fontsize=14, fontweight='bold')
    _draw_scene_graph(modified_graph, modified_scene, original_referents, 
                     target_object, reference_object, ax2, "Modified")
    
    # Plot 3: Expression Information
    ax3.set_title('Expression Information', fontsize=14, fontweight='bold')
    ax3.axis('off')
    
    info_text = f"REARRANGEMENT PAIR #{pair_idx + 1}\n\n"
    info_text += f"ORIGINAL EXPRESSION:\n{original_refexp['refexp']}\n\n"
    info_text += f"REARRANGEMENT EXPRESSION:\n{rearrangement_refexp['refexp']}\n\n"
    
    if original_referents:
        info_text += f"ORIGINAL REFERENTS: {original_referents}\n\n"
    else:
        info_text += "ORIGINAL REFERENTS: Could not determine\n\n"
    
    info_text += f"REARRANGEMENT DETAILS:\n"
    info_text += f"  Target Object: {target_object}\n"
    info_text += f"  Reference Object: {reference_object}\n"
    info_text += f"  Target Relation: {target_relation}\n\n"
    
    info_text += "OBJECTS IN SCENE:\n"
    for i, obj in enumerate(scene['objects']):
        status = ""
        if i == target_object:
            status = " ← TARGET OBJECT"
        elif i == reference_object:
            status = " ← REFERENCE OBJECT"
        elif original_referents and i in original_referents:
            status = " ← ORIGINAL REFERENT"
        
        info_text += f"Object {i}: {obj['color']} {obj['shape']} ({obj['size']}, {obj['material']}){status}\n"
    
    ax3.text(0.05, 0.95, info_text, transform=ax3.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=1", facecolor="lightyellow", alpha=0.8))
    
    # Plot 4: Relationship Changes
    ax4.set_title('Relationship Changes', fontsize=14, fontweight='bold')
    ax4.axis('off')
    
    changes_text = "RELATIONSHIP CHANGES:\n\n"
    
    # Show original relationships for target object
    if target_object is not None:
        changes_text += f"TARGET OBJECT {target_object} RELATIONSHIPS:\n"
        changes_text += "Original:\n"
        for rel_type, rel_lists in scene.get('relationships', {}).items():
            if target_object < len(rel_lists) and rel_lists[target_object]:
                changes_text += f"  {rel_type}: {rel_lists[target_object]}\n"
        
        changes_text += "\nAfter Rearrangement:\n"
        for rel_type, rel_lists in modified_scene.get('relationships', {}).items():
            if target_object < len(rel_lists) and rel_lists[target_object]:
                changes_text += f"  {rel_type}: {rel_lists[target_object]}\n"
        
        # Highlight the new relationship
        if target_relation and target_object < len(modified_scene.get('relationships', {}).get(target_relation, [])):
            new_rels = modified_scene['relationships'][target_relation][target_object]
            if reference_object in new_rels:
                changes_text += f"\n*** NEW RELATIONSHIP: Object {target_object} is now {target_relation} of Object {reference_object}\n"
    
    ax4.text(0.05, 0.95, changes_text, transform=ax4.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=1", facecolor="lightcyan", alpha=0.8))
    
    plt.tight_layout()
    
    # Save or show the plot
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Visualization saved to: {save_path}")
    
    if show_plot:
        plt.show()
    
    return fig

def _draw_scene_graph(G, scene_data, referents, target_object, reference_object, ax, title_prefix):
    """Helper function to draw a scene graph"""
    
    # Create layout
    pos = nx.spring_layout(G, seed=42, k=3, iterations=50)
    
    # Draw nodes with different colors based on their role
    node_colors = []
    node_sizes = []
    node_labels = {}
    
    for node in G.nodes():
        obj = scene_data['objects'][node]
        node_labels[node] = f"{obj['color']}\n{obj['shape']}\n({node})"
        
        # Determine node color based on role
        if node == target_object:
            node_colors.append('red')  # Target object in red
            node_sizes.append(1500)
        elif node == reference_object:
            node_colors.append('orange')  # Reference object in orange
            node_sizes.append(1500)
        elif referents and node in referents:
            node_colors.append('lightgreen')  # Original referents in light green
            node_sizes.append(1200)
        else:
            node_colors.append('lightblue')  # Other objects in light blue
            node_sizes.append(800)
    
    # Draw the graph
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color='gray', width=1.5, arrows=True, ax=ax, alpha=0.7)
    nx.draw_networkx_labels(G, pos, node_labels, font_size=8, font_weight='bold', ax=ax)
    
    # Draw edge labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8, font_color='darkgreen', ax=ax)
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=15, label='Target Object'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=15, label='Reference Object'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', markersize=12, label='Original Referent'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', markersize=10, label='Other Objects')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=8)
    ax.axis('off')

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Visualize scene rearrangement expressions')
    parser.add_argument('--scene_file', required=True,
                       help='Path to scene JSON file')
    parser.add_argument('--rearrangement_file', required=True,
                       help='Path to rearrangement expressions JSON file')
    parser.add_argument('--pair_idx', type=int, default=0,
                       help='Index of rearrangement pair to visualize (default: 0)')
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
    
    # Get the specific pair
    if args.pair_idx >= len(rearrangement_data['expression_pairs']):
        print(f"Pair index {args.pair_idx} out of range. Available: {len(rearrangement_data['expression_pairs'])}")
        return
    
    pair = rearrangement_data['expression_pairs'][args.pair_idx]
    
    # Create visualization
    print(f"Creating visualization for rearrangement pair {args.pair_idx}")
    fig = visualize_scene_rearrangement(
        scene_data, pair, 
        pair_idx=args.pair_idx,
        save_path=args.save_path,
        show_plot=not args.no_show
    )
    
    if fig:
        print("Visualization complete!")
    else:
        print("Visualization failed!")

if __name__ == "__main__":
    main()
