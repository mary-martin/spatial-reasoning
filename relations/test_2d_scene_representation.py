#!/usr/bin/env python3

import json
import os
import sys
import matplotlib.pyplot as plt
import networkx as nx

# Import the scene objects module
from scene_objects import Scene_Objects

def test_2d_scene_representation():
    """Test the 2D graphical scene representation with spatial relationships"""
    
    print("=== Testing 2D Scene Representation ===\n")
    
    # Load scene data
    data_dir = "/home/mary/Code/spatial-reasoning/custom_clevr/output/scenes/"
    scene_file = "CLEVR_train_000000.json"
    
    with open(os.path.join(data_dir, scene_file)) as data:
        scene_data = json.load(data)
    
    print(f"Loaded scene: {scene_file}")
    print(f"Number of objects: {len(scene_data['objects'])}")
    
    # Create scene objects
    scene_info = Scene_Objects(scene_data)
    
    # Test 1: Check object relationships
    print("\n--- Object Relationships ---")
    for i, entity in enumerate(scene_info.all_entities):
        print(f"Object {entity.idx} ({entity.color} {entity.shape}):")
        print(f"  Position: {entity.coords}")
        print(f"  Front: {entity.front}")
        print(f"  Behind: {entity.behind}")
        print(f"  Left: {entity.left}")
        print(f"  Right: {entity.right}")
        print()
    
    # Test 2: Check combined relations
    print("--- Combined Relations ---")
    for pair, relations in scene_info.scene_relations.items():
        if relations:  # Only show pairs with relations
            obj1_idx, obj2_idx = pair
            obj1 = scene_info.all_entities[obj1_idx]
            obj2 = scene_info.all_entities[obj2_idx]
            print(f"Object {obj1_idx} ({obj1.color} {obj1.shape}) -> Object {obj2_idx} ({obj2.color} {obj2.shape}): {relations}")
    
    # Test 3: Check position dictionary for 2D plotting
    print("\n--- 2D Position Dictionary ---")
    for obj_idx, pos in scene_info.position_dict.items():
        entity = scene_info.all_entities[int(obj_idx)]
        print(f"Object {obj_idx}: {entity.color} {entity.shape} at position {pos}")
    
    # Test 4: Verify relationship consistency
    print("\n--- Relationship Consistency Check ---")
    for i, entity in enumerate(scene_info.all_entities):
        # Check that if A is left of B, then B is right of A
        for left_obj in entity.left:
            if i in scene_info.all_entities[left_obj].right:
                print(f"✓ Object {i} left of {left_obj} ✓ Object {left_obj} right of {i}")
            else:
                print(f"✗ Inconsistency: Object {i} left of {left_obj} but Object {left_obj} NOT right of {i}")
        
        # Check that if A is front of B, then B is behind A
        for front_obj in entity.front:
            if i in scene_info.all_entities[front_obj].behind:
                print(f"✓ Object {i} front of {front_obj} ✓ Object {front_obj} behind {i}")
            else:
                print(f"✗ Inconsistency: Object {i} front of {front_obj} but Object {front_obj} NOT behind {i}")
    
    # Test 5: Test 2D graph creation (without displaying)
    print("\n--- 2D Graph Creation Test ---")
    try:
        # Test show_2d_graph without plotting
        scene_info.show_2d_graph(plot=False)
        print("✓ 2D graph creation successful")
        
        # Test show_combined_graph without plotting
        scene_info.show_combined_graph(plot=False)
        print("✓ Combined graph creation successful")
        
    except Exception as e:
        print(f"✗ Error creating 2D graphs: {e}")
    
    # Test 6: Check object offsets
    print("\n--- Object Offset Calculations ---")
    if len(scene_info.all_locations) >= 2:
        offset = scene_info.obj_offsets.offset_data[(0, 1)]
        print(f"Offset between objects 0 and 1:")
        print(f"  Theta degrees: {offset['theta_degrees']:.2f}")
        print(f"  Cos theta: {offset['cos_theta']:.4f}")
        print(f"  XYZ offsets: {[f'{x:.3f}' for x in offset['xyz_offsets']]}")
    
    print("\n=== 2D Scene Representation Test Complete ===")
    
    return scene_info

def create_visualization_demo(scene_info):
    """Create a demonstration of the 2D visualization"""
    
    print("\n=== Creating 2D Visualization Demo ===")
    
    # Create a simple 2D plot showing object positions
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot 1: Object positions in 2D space
    ax1.set_title('Object Positions in 2D Space')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    
    # Plot camera position
    ax1.scatter(scene_info.camera_pos[0], scene_info.camera_pos[1], 
               c='red', marker='o', s=100, label='Camera', zorder=5)
    
    # Plot object positions
    colors = ['blue', 'green', 'red', 'orange', 'purple', 'brown']
    for i, (pos, entity) in enumerate(zip(scene_info.all_locations, scene_info.all_entities)):
        color = colors[i % len(colors)]
        ax1.scatter(pos[0], pos[1], c=color, marker='s', s=80, 
                   label=f"{entity.color} {entity.shape} ({entity.idx})")
        ax1.annotate(f"{entity.idx}", (pos[0], pos[1]), xytext=(5, 5), 
                    textcoords='offset points', fontsize=10, fontweight='bold')
    
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Relationship graph
    ax2.set_title('Spatial Relationships Graph')
    
    # Create a simple relationship visualization
    G = nx.DiGraph()
    
    # Add nodes
    for i in range(len(scene_info.all_entities)):
        G.add_node(i)
    
    # Add edges for relationships
    for pair, relations in scene_info.scene_relations.items():
        if relations:
            obj1_idx, obj2_idx = pair
            if obj2_idx > obj1_idx:  # Only show one direction to avoid clutter
                G.add_edge(obj1_idx, obj2_idx, label=", ".join(relations))
    
    # Use circular layout
    pos = nx.circular_layout(G)
    nx.draw(G, pos, ax=ax2, with_labels=True, node_size=500, 
            node_color='skyblue', font_size=12, font_weight='bold')
    
    # Add edge labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, 
                                font_color='red', font_size=8)
    
    plt.tight_layout()
    plt.savefig('2d_scene_representation_demo.png', dpi=150, bbox_inches='tight')
    print("✓ 2D visualization demo saved as '2d_scene_representation_demo.png'")
    
    # Don't show the plot interactively to avoid blocking
    # plt.show()

if __name__ == "__main__":
    # Run the test
    scene_info = test_2d_scene_representation()
    
    # Create visualization demo
    create_visualization_demo(scene_info)
    
    print("\n=== All Tests Completed Successfully ===")


