#!/usr/bin/env python3
"""
Demo Script for Scene Rearrangement Visualization

This script demonstrates how to use the scene rearrangement visualization tools
to visualize before and after scene graphs for rearrangement expressions.
"""

import subprocess
import os
import sys

def run_command(cmd, description):
    """Run a command and print the result"""
    print(f"\n{'='*60}")
    print(f"DEMO: {description}")
    print(f"{'='*60}")
    print(f"Command: {cmd}")
    print()
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout:
                print("Output:", result.stdout)
        else:
            print("❌ FAILED")
            if result.stderr:
                print("Error:", result.stderr)
    except Exception as e:
        print(f"❌ ERROR: {e}")

def main():
    """Main demo function"""
    print("SCENE REARRANGEMENT VISUALIZATION DEMO")
    print("=" * 60)
    print("This demo shows how to visualize scene rearrangement expressions")
    print("with before and after scene graphs.")
    print()
    
    # Check if required files exist
    scene_file = "custom_clevr/output/clevr_ref+_scenes.json"
    rearrangement_file = "custom_clevr/output/clevr_ref+_rearrangements.json"
    
    if not os.path.exists(scene_file):
        print(f"❌ Scene file not found: {scene_file}")
        return
    
    if not os.path.exists(rearrangement_file):
        print(f"❌ Rearrangement file not found: {rearrangement_file}")
        return
    
    print("✅ Required files found")
    print(f"   Scene file: {scene_file}")
    print(f"   Rearrangement file: {rearrangement_file}")
    
    # Create output directory
    output_dir = "figures/scene_rearrangement_visualizations"
    os.makedirs(output_dir, exist_ok=True)
    print(f"✅ Output directory: {output_dir}")
    
    # Demo 1: Single rearrangement pair visualization
    cmd1 = f"""python visualize_scene_rearrangement.py \\
    --scene_file {scene_file} \\
    --rearrangement_file {rearrangement_file} \\
    --pair_idx 0 \\
    --save_path {output_dir}/single_rearrangement_pair_0.png \\
    --no_show"""
    
    run_command(cmd1, "Single Rearrangement Pair Visualization (Pair 0)")
    
    # Demo 2: Different rearrangement pair
    cmd2 = f"""python visualize_scene_rearrangement.py \\
    --scene_file {scene_file} \\
    --rearrangement_file {rearrangement_file} \\
    --pair_idx 1 \\
    --save_path {output_dir}/single_rearrangement_pair_1.png \\
    --no_show"""
    
    run_command(cmd2, "Single Rearrangement Pair Visualization (Pair 1)")
    
    # Demo 3: Batch visualization of multiple pairs
    cmd3 = f"""python batch_visualize_rearrangements.py \\
    --scene_file {scene_file} \\
    --rearrangement_file {rearrangement_file} \\
    --max_pairs 3 \\
    --save_path {output_dir}/batch_rearrangement_visualization.png \\
    --no_show"""
    
    run_command(cmd3, "Batch Rearrangement Visualization (3 pairs)")
    
    # Demo 4: Show all available pairs
    cmd4 = f"""python -c "
import json
with open('{rearrangement_file}', 'r') as f:
    data = json.load(f)

print('AVAILABLE REARRANGEMENT PAIRS:')
print(f'Total pairs: {{len(data[\"expression_pairs\"])}}')
print()

for i, pair in enumerate(data['expression_pairs']):
    original = pair['original']['refexp']
    rearrangement = pair['rearrangement']['refexp']
    target_obj = pair['rearrangement'].get('target_object', 'N/A')
    ref_obj = pair['rearrangement'].get('reference_object', 'N/A')
    relation = pair['rearrangement'].get('target_relation', 'N/A')
    
    print(f'Pair {{i}}:')
    print(f'  Original: \"{{original[:60]}}...\"')
    print(f'  Rearrangement: \"{{rearrangement}}\"')
    print(f'  Target Object: {{target_obj}}, Reference Object: {{ref_obj}}, Relation: {{relation}}')
    print()
" """
    
    run_command(cmd4, "List All Available Rearrangement Pairs")
    
    # Demo 5: Show what files were created
    cmd5 = f"ls -la {output_dir}/"
    run_command(cmd5, "Generated Visualization Files")
    
    print("\n" + "="*60)
    print("DEMO COMPLETE!")
    print("="*60)
    print("The scene rearrangement visualization tools have been demonstrated.")
    print("You can now:")
    print("1. View the generated PNG files in the figures directory")
    print("2. Use the tools with your own rearrangement data")
    print("3. Modify the visualization parameters as needed")
    print()
    print("Key features demonstrated:")
    print("✅ Single pair visualization with before/after scene graphs")
    print("✅ Batch visualization of multiple pairs")
    print("✅ Highlighting of target and reference objects")
    print("✅ Relationship change tracking")
    print("✅ Expression information display")

if __name__ == "__main__":
    main()
