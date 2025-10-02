#!/usr/bin/env python3
"""
Visualize Scene Graph with Comprehensive Expressions

This script visualizes scene graphs using the comprehensive expressions file
that contains both original and LLM-diversified expressions.
"""

import json
import os
import sys
import argparse
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# Add the relations directory to the path
sys.path.append('relations')
from scene_objects import Scene_Objects

# Add the refexp generation directory to the path
sys.path.append('custom_clevr/refexp_generation')
import refexp_engine as qeng

def load_scene_data(scene_file):
    """Load scene data from JSON file"""
    with open(scene_file, 'r') as f:
        return json.load(f)

def load_comprehensive_expressions(comprehensive_file):
    """Load comprehensive expressions data from JSON file"""
    with open(comprehensive_file, 'r') as f:
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

def visualize_comprehensive_expressions(scene_data, comprehensive_data, scene_idx=0, 
                                       expr_type='original', expr_idx=0, 
                                       save_path=None, show_plot=True):
    """
    Visualize scene graph with comprehensive expressions
    
    Args:
        scene_data: Scene data dictionary
        comprehensive_data: Comprehensive expressions data dictionary
        scene_idx: Index of scene to visualize
        expr_type: 'original' or 'diversified'
        expr_idx: Index of expression to use
        save_path: Path to save the plot (optional)
        show_plot: Whether to display the plot
    """
    
    # Get the specific scene
    if 'scenes' in scene_data:
        scene = scene_data['scenes'][scene_idx]
    else:
        scene = scene_data
    
    # Get the specific expression
    if expr_type == 'original':
        expressions = comprehensive_data['original_expressions']
    else:
        expressions = comprehensive_data['diversified_expressions']
    
    if expr_idx >= len(expressions):
        print(f"Expression index {expr_idx} out of range. Available: {len(expressions)}")
        return None
    
    refexp = expressions[expr_idx]
    
    # Create the scene graph
    G = create_scene_graph(scene)
    
    # Get the referent object(s)
    metadata = {'types': {
        'Size': ['large', 'small'],
        'Color': ['blue', 'brown', 'cyan', 'gray', 'green', 'purple', 'red', 'yellow'],
        'Material': ['metal', 'rubber'],
        'Shape': ['cube', 'cylinder', 'sphere'],
        'Relation': ['left', 'right', 'front', 'behind', 'between', 'nearest', 'farthest']
    }}
    
    referent_objects = get_referent_from_refexp(refexp, scene, metadata)
    
    # Create the visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Plot 1: Scene Graph with Referent Highlighted
    title = f'Scene Graph with Referent Highlighted\n'
    title += f'Expression Type: {expr_type.title()}\n'
    title += f'Expression: "{refexp["refexp"]}"'
    ax1.set_title(title, fontsize=12, fontweight='bold')
    
    # Create layout
    pos = nx.spring_layout(G, seed=42, k=3, iterations=50)
    
    # Draw nodes with different colors based on whether they are referents
    node_colors = []
    node_sizes = []
    node_labels = {}
    
    for node in G.nodes():
        obj = scene['objects'][node]
        node_labels[node] = f"{obj['color']}\n{obj['shape']}\n({node})"
        
        if referent_objects and node in referent_objects:
            node_colors.append('red')  # Referent objects in red
            node_sizes.append(1500)
        else:
            node_colors.append('lightblue')  # Non-referent objects in light blue
            node_sizes.append(800)
    
    # Draw the graph
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax1)
    nx.draw_networkx_edges(G, pos, edge_color='gray', width=1.5, arrows=True, ax=ax1, alpha=0.7)
    nx.draw_networkx_labels(G, pos, node_labels, font_size=8, font_weight='bold', ax=ax1)
    
    # Draw edge labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8, font_color='darkgreen', ax=ax1)
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=15, label='Referent Object'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', markersize=12, label='Other Objects')
    ]
    ax1.legend(handles=legend_elements, loc='upper right', fontsize=10)
    ax1.axis('off')
    
    # Plot 2: Expression Information
    ax2.set_title('Expression Information', fontsize=12, fontweight='bold')
    ax2.axis('off')
    
    # Create expression information text
    info_text = f"EXPRESSION TYPE: {expr_type.upper()}\n\n"
    info_text += f"EXPRESSION: {refexp['refexp']}\n\n"
    
    if referent_objects:
        info_text += f"REFERENT OBJECT(S): {referent_objects}\n\n"
    else:
        info_text += "REFERENT: Could not determine referent\n\n"
    
    info_text += "OBJECTS IN SCENE:\n"
    for i, obj in enumerate(scene['objects']):
        status = "← REFERENT" if referent_objects and i in referent_objects else ""
        info_text += f"Object {i}: {obj['color']} {obj['shape']} ({obj['size']}, {obj['material']}) {status}\n"
    
    info_text += f"\nSCENE: {scene.get('image_filename', 'Unknown')}\n"
    info_text += f"TOTAL EXPRESSIONS: {len(comprehensive_data['original_expressions'])} original, {len(comprehensive_data['diversified_expressions'])} diversified\n"
    
    ax2.text(0.05, 0.95, info_text, transform=ax2.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=1", facecolor="lightyellow", alpha=0.8))
    
    plt.tight_layout()
    
    # Save or show the plot
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Visualization saved to: {save_path}")
    
    if show_plot:
        plt.show()
    
    return fig

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Visualize scene graphs with comprehensive expressions')
    parser.add_argument('--scene_file', required=True,
                       help='Path to scene JSON file')
    parser.add_argument('--comprehensive_file', required=True,
                       help='Path to comprehensive expressions JSON file')
    parser.add_argument('--scene_idx', type=int, default=0,
                       help='Index of scene to visualize (default: 0)')
    parser.add_argument('--expr_type', choices=['original', 'diversified'], default='original',
                       help='Type of expression to visualize (default: original)')
    parser.add_argument('--expr_idx', type=int, default=0,
                       help='Index of expression to use (default: 0)')
    parser.add_argument('--save_path', 
                       help='Path to save the visualization (optional)')
    parser.add_argument('--no_show', action='store_true',
                       help='Do not display the plot (useful when saving)')
    
    args = parser.parse_args()
    
    # Load data
    print(f"Loading scene data from: {args.scene_file}")
    scene_data = load_scene_data(args.scene_file)
    
    print(f"Loading comprehensive expressions from: {args.comprehensive_file}")
    comprehensive_data = load_comprehensive_expressions(args.comprehensive_file)
    
    # Create visualization
    print(f"Creating visualization for scene {args.scene_idx}, {args.expr_type} expression {args.expr_idx}")
    fig = visualize_comprehensive_expressions(
        scene_data, comprehensive_data, 
        scene_idx=args.scene_idx, 
        expr_type=args.expr_type,
        expr_idx=args.expr_idx,
        save_path=args.save_path,
        show_plot=not args.no_show
    )
    
    if fig:
        print("Visualization complete!")
    else:
        print("Visualization failed!")

if __name__ == "__main__":
    main()

