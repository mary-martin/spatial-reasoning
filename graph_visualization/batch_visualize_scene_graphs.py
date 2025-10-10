#!/usr/bin/env python3
"""
Batch Scene Graph Visualization with Referent Highlighting

This script creates visualizations for multiple referring expressions
from a scene, showing how different expressions refer to different objects.
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

def load_refexp_data(refexp_file):
    """Load referring expressions data from JSON file"""
    with open(refexp_file, 'r') as f:
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

def create_batch_visualization(scene_data, refexp_data, scene_idx=0, max_refexps=6, 
                              save_path=None, show_plot=True):
    """
    Create a batch visualization showing multiple referring expressions for a scene
    
    Args:
        scene_data: Scene data dictionary
        refexp_data: Referring expressions data dictionary
        scene_idx: Index of scene to visualize
        max_refexps: Maximum number of referring expressions to show
        save_path: Path to save the plot (optional)
        show_plot: Whether to display the plot
    """
    
    # Get the specific scene
    if 'scenes' in scene_data:
        scene = scene_data['scenes'][scene_idx]
    else:
        scene = scene_data
    
    # Get referring expressions for this scene
    if 'refexps' in refexp_data:
        scene_refexps = [r for r in refexp_data['refexps'] 
                        if r.get('image_index', 0) == scene_idx][:max_refexps]
    else:
        scene_refexps = [refexp_data][:max_refexps]
    
    if not scene_refexps:
        print(f"No referring expressions found for scene {scene_idx}")
        return None
    
    # Create the scene graph
    G = create_scene_graph(scene)
    
    # Metadata for executing referring expressions
    metadata = {'types': {
        'Size': ['large', 'small'],
        'Color': ['blue', 'brown', 'cyan', 'gray', 'green', 'purple', 'red', 'yellow'],
        'Material': ['metal', 'rubber'],
        'Shape': ['cube', 'cylinder', 'sphere'],
        'Relation': ['left', 'right', 'front', 'behind', 'between', 'nearest', 'farthest']
    }}
    
    # Calculate grid layout
    n_refexps = len(scene_refexps)
    cols = min(3, n_refexps)
    rows = (n_refexps + cols - 1) // cols
    
    # Create the visualization
    fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
    if n_refexps == 1:
        axes = [axes]
    elif rows == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    fig.suptitle(f'Scene Graph Visualizations with Different Referents\n'
                 f'Scene: {scene.get("image_filename", "Unknown")} ({len(scene["objects"])} objects)', 
                 fontsize=14, fontweight='bold')
    
    # Create layout once for consistency
    pos = nx.spring_layout(G, seed=42, k=3, iterations=50)
    
    for i, refexp in enumerate(scene_refexps):
        ax = axes[i]
        
        # Get the referent object(s)
        referent_objects = get_referent_from_refexp(refexp, scene, metadata)
        
        # Set title
        title = f'Refexp {i+1}: "{refexp["refexp"][:50]}{"..." if len(refexp["refexp"]) > 50 else ""}"'
        ax.set_title(title, fontsize=10, fontweight='bold')
        
        # Draw nodes with different colors based on whether they are referents
        node_colors = []
        node_sizes = []
        node_labels = {}
        
        for node in G.nodes():
            obj = scene['objects'][node]
            node_labels[node] = f"{obj['color'][:3]}\n{obj['shape'][:3]}\n({node})"
            
            if referent_objects and node in referent_objects:
                node_colors.append('red')  # Referent objects in red
                node_sizes.append(1200)
            else:
                node_colors.append('lightblue')  # Non-referent objects in light blue
                node_sizes.append(600)
        
        # Draw the graph
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color='gray', width=1, arrows=True, ax=ax, alpha=0.6)
        nx.draw_networkx_labels(G, pos, node_labels, font_size=7, font_weight='bold', ax=ax)
        
        # Draw edge labels (only for first subplot to avoid clutter)
        if i == 0:
            edge_labels = nx.get_edge_attributes(G, 'label')
            nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=6, font_color='darkgreen', ax=ax)
        
        # Add referent information
        if referent_objects:
            ax.text(0.02, 0.98, f'Referent: {referent_objects}', 
                   transform=ax.transAxes, fontsize=8, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
                   verticalalignment='top')
        else:
            ax.text(0.02, 0.98, 'Referent: None', 
                   transform=ax.transAxes, fontsize=8, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7),
                   verticalalignment='top')
        
        ax.axis('off')
    
    # Hide unused subplots
    for i in range(n_refexps, len(axes)):
        axes[i].axis('off')
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=12, label='Referent Object'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', markersize=10, label='Other Objects')
    ]
    fig.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.05), ncol=2)
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)
    
    # Save or show the plot
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Batch visualization saved to: {save_path}")
    
    if show_plot:
        plt.show()
    
    return fig

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Create batch visualizations of scene graphs with different referents')
    parser.add_argument('--scene_file', required=True,
                       help='Path to scene JSON file')
    parser.add_argument('--refexp_file', required=True,
                       help='Path to referring expressions JSON file')
    parser.add_argument('--scene_idx', type=int, default=0,
                       help='Index of scene to visualize (default: 0)')
    parser.add_argument('--max_refexps', type=int, default=6,
                       help='Maximum number of referring expressions to show (default: 6)')
    parser.add_argument('--save_path', 
                       help='Path to save the visualization (optional)')
    parser.add_argument('--no_show', action='store_true',
                       help='Do not display the plot (useful when saving)')
    
    args = parser.parse_args()
    
    # Load data
    print(f"Loading scene data from: {args.scene_file}")
    scene_data = load_scene_data(args.scene_file)
    
    print(f"Loading referring expressions from: {args.refexp_file}")
    refexp_data = load_refexp_data(args.refexp_file)
    
    # Create batch visualization
    print(f"Creating batch visualization for scene {args.scene_idx} with up to {args.max_refexps} referring expressions")
    fig = create_batch_visualization(
        scene_data, refexp_data, 
        scene_idx=args.scene_idx, 
        max_refexps=args.max_refexps,
        save_path=args.save_path,
        show_plot=not args.no_show
    )
    
    if fig:
        print("Batch visualization complete!")
    else:
        print("No referring expressions found for the specified scene.")

if __name__ == "__main__":
    main()
