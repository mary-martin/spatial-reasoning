#!/usr/bin/env python3
"""
Test script for LLM diversification of rearrangement expressions

This script provides a simple way to test the LLM diversification functionality
with a small sample of rearrangement expressions.
"""

import json
import os
import sys
from typing import Dict, Any, List

def create_test_scene_data() -> Dict[str, Any]:
    """Create minimal test scene data"""
    return {
        "info": {
            "date": "2025-01-01",
            "version": "1.0",
            "split": "test"
        },
        "scenes": [
            {
                "image_filename": "CLEVR_train_000000.png",
                "image_index": 0,
                "objects": [
                    {
                        "color": "red",
                        "shape": "cube",
                        "material": "metal",
                        "size": "small"
                    },
                    {
                        "color": "blue",
                        "shape": "sphere",
                        "material": "rubber",
                        "size": "large"
                    },
                    {
                        "color": "green",
                        "shape": "cylinder",
                        "material": "metal",
                        "size": "small"
                    }
                ]
            },
            {
                "image_filename": "CLEVR_train_000001.png",
                "image_index": 1,
                "objects": [
                    {
                        "color": "yellow",
                        "shape": "cube",
                        "material": "rubber",
                        "size": "large"
                    },
                    {
                        "color": "purple",
                        "shape": "sphere",
                        "material": "metal",
                        "size": "small"
                    }
                ]
            }
        ]
    }

def create_test_rearrangement_pairs() -> List[Dict[str, Any]]:
    """Create test rearrangement expression pairs"""
    return [
        {
            "original": {
                "refexp": "The red cube",
                "program": [],
                "answer": 0,
                "image_filename": "CLEVR_train_000000.png",
                "image_index": 0
            },
            "rearrangement": {
                "refexp": "Place the red cube to the left of the blue sphere",
                "program": [],
                "target_object": 0,
                "reference_object": 1,
                "target_relation": "left",
                "template_used": "place_simple.json"
            },
            "pair_id": "pair_000000",
            "scene_id": "CLEVR_train_000000"
        },
        {
            "original": {
                "refexp": "The metal cylinder",
                "program": [],
                "answer": 2,
                "image_filename": "CLEVR_train_000000.png",
                "image_index": 0
            },
            "rearrangement": {
                "refexp": "Move the green cylinder behind the red cube",
                "program": [],
                "target_object": 2,
                "reference_object": 0,
                "target_relation": "behind",
                "template_used": "place_with_material.json"
            },
            "pair_id": "pair_000001",
            "scene_id": "CLEVR_train_000000"
        },
        {
            "original": {
                "refexp": "The large yellow cube",
                "program": [],
                "answer": 0,
                "image_filename": "CLEVR_train_000001.png",
                "image_index": 1
            },
            "rearrangement": {
                "refexp": "Put the yellow cube to the right of the purple sphere",
                "program": [],
                "target_object": 0,
                "reference_object": 1,
                "target_relation": "right",
                "template_used": "place_simple.json"
            },
            "pair_id": "pair_000002",
            "scene_id": "CLEVR_train_000001"
        }
    ]

def save_test_data(output_dir: str = "test_data"):
    """Save test data to files"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save scene data
    scene_data = create_test_scene_data()
    scene_file = os.path.join(output_dir, "test_scenes.json")
    with open(scene_file, 'w') as f:
        json.dump(scene_data, f, indent=2)
    print(f"Created test scene data: {scene_file}")
    
    # Save rearrangement pairs
    pairs_data = {
        "info": {
            "license": "Test data",
            "date": "2025-01-01",
            "version": "1.0",
            "num_successful_pairs": 3
        },
        "expression_pairs": create_test_rearrangement_pairs()
    }
    pairs_file = os.path.join(output_dir, "test_rearrangement_pairs.json")
    with open(pairs_file, 'w') as f:
        json.dump(pairs_data, f, indent=2)
    print(f"Created test rearrangement pairs: {pairs_file}")
    
    return scene_file, pairs_file

def run_test_diversification(scene_file: str, pairs_file: str, 
                             llm_provider: str, model_name: str, api_key: str):
    """Run LLM diversification on test data"""
    from llm_diversify_rearrangements import (
        DiversificationConfig, LLMRearrangementDiversifier,
        load_expression_pairs_data, load_scene_data, save_diversified_data
    )
    
    print("\n=== Running LLM Diversification Test ===")
    
    # Create configuration
    config = DiversificationConfig(
        llm_provider=llm_provider,
        model_name=model_name,
        api_key=api_key,
        max_variations=2,
        temperature=0.8,
        delay_between_requests=0.5
    )
    
    # Load test data
    print(f"Loading rearrangement pairs from {pairs_file}")
    expression_pairs = load_expression_pairs_data(pairs_file)
    print(f"Loaded {len(expression_pairs)} expression pairs")
    
    print(f"Loading scenes from {scene_file}")
    scene_data = load_scene_data(scene_file)
    print(f"Loaded {len(scene_data.get('scenes', []))} scenes")
    
    # Initialize diversifier
    diversifier = LLMRearrangementDiversifier(config)
    
    # Process expressions
    print(f"\nStarting diversification...")
    diversified_data = diversifier.diversify_batch(expression_pairs, scene_data)
    
    print(f"\nDiversification complete!")
    print(f"Generated {len(diversified_data)} diversified expression pairs")
    
    # Save results
    output_file = "test_data/test_diversified_rearrangements.json"
    original_info = {"test": True, "date": "2025-01-01"}
    save_diversified_data(diversified_data, output_file, original_info, config)
    
    # Display sample results
    print("\n=== Sample Results ===")
    for i, pair in enumerate(diversified_data[:4]):  # Show first 4
        print(f"\nPair {i+1}:")
        print(f"  Original refexp: {pair['original']['refexp']}")
        print(f"  Original rearrangement: {pair['rearrangement'].get('original_rearrangement_refexp', 'N/A')}")
        print(f"  Diversified rearrangement: {pair['rearrangement']['refexp']}")
        print(f"  Variation ID: {pair['rearrangement'].get('variation_id', 'N/A')}")
    
    return diversified_data

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test LLM diversification for rearrangement expressions')
    parser.add_argument('--llm_provider', default='openai', choices=['openai', 'anthropic'],
                       help='LLM provider to use (default: openai)')
    parser.add_argument('--model_name', default='gpt-3.5-turbo',
                       help='Model name (default: gpt-3.5-turbo)')
    parser.add_argument('--api_key', required=True,
                       help='API key for the LLM provider')
    parser.add_argument('--use-existing-data', action='store_true',
                       help='Use existing test data instead of creating new')
    
    args = parser.parse_args()
    
    # Create or load test data
    if args.use_existing_data and os.path.exists("test_data/test_scenes.json"):
        print("Using existing test data...")
        scene_file = "test_data/test_scenes.json"
        pairs_file = "test_data/test_rearrangement_pairs.json"
    else:
        print("Creating new test data...")
        scene_file, pairs_file = save_test_data()
    
    # Run diversification test
    try:
        diversified_data = run_test_diversification(
            scene_file, pairs_file, 
            args.llm_provider, args.model_name, args.api_key
        )
        print("\n✅ Test completed successfully!")
        print(f"Results saved to: test_data/test_diversified_rearrangements.json")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()


