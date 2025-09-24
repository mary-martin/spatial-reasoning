#!/usr/bin/env python3
"""
Test script for the scene rearrangement system.
This script tests the system with a small subset of data to ensure it works correctly.
"""

import json
import os
import sys
import argparse

# Add the refexp generation directory to the path
sys.path.append('../custom_clevr/refexp_generation')

def test_basic_functionality():
    """Test basic functionality of the rearrangement system."""
    print("Testing basic functionality...")
    
    # Test 1: Check if all required files exist
    required_files = [
        'metadata.json',
        'synonyms.json',
        'rearrangement_engine.py',
        'generate_rearrangement_expressions.py'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"ERROR: Required file {file} not found")
            return False
        else:
            print(f"✓ {file} exists")
    
    # Test 2: Check if template directory exists and has templates
    template_dir = 'rearrangement_templates'
    if not os.path.exists(template_dir):
        print(f"ERROR: Template directory {template_dir} not found")
        return False
    
    template_files = [f for f in os.listdir(template_dir) if f.endswith('.json')]
    if not template_files:
        print(f"ERROR: No template files found in {template_dir}")
        return False
    
    print(f"✓ Found {len(template_files)} template files: {template_files}")
    
    # Test 3: Test metadata loading
    try:
        with open('metadata.json', 'r') as f:
            metadata = json.load(f)
        print("✓ Metadata loaded successfully")
        print(f"  - Dataset: {metadata['dataset']}")
        print(f"  - Functions: {len(metadata['functions'])}")
        print(f"  - Types: {len(metadata['types'])}")
    except Exception as e:
        print(f"ERROR: Failed to load metadata: {e}")
        return False
    
    # Test 4: Test synonyms loading
    try:
        with open('synonyms.json', 'r') as f:
            synonyms = json.load(f)
        print("✓ Synonyms loaded successfully")
        print(f"  - Synonym groups: {len(synonyms)}")
    except Exception as e:
        print(f"ERROR: Failed to load synonyms: {e}")
        return False
    
    # Test 5: Test template loading
    try:
        templates = []
        for template_file in template_files:
            with open(os.path.join(template_dir, template_file), 'r') as f:
                template_data = json.load(f)
                for template in template_data:
                    template['name'] = template_file
                    templates.append(template)
        print(f"✓ Loaded {len(templates)} templates successfully")
        
        # Check template structure
        for i, template in enumerate(templates):
            required_keys = ['text', 'nodes', 'params']
            for key in required_keys:
                if key not in template:
                    print(f"ERROR: Template {i} missing required key '{key}'")
                    return False
        print("✓ All templates have required structure")
        
    except Exception as e:
        print(f"ERROR: Failed to load templates: {e}")
        return False
    
    return True


def test_rearrangement_engine():
    """Test the rearrangement engine functionality."""
    print("\nTesting rearrangement engine...")
    
    try:
        import rearrangement_engine as reng
        print("✓ Rearrangement engine imported successfully")
        
        # Test basic handlers
        test_scene = {
            'objects': [
                {'color': 'red', 'shape': 'cube', 'material': 'rubber', 'size': 'large'},
                {'color': 'blue', 'shape': 'sphere', 'material': 'metal', 'size': 'small'}
            ],
            'relationships': {
                'left': {0: [1], 1: []},
                'right': {0: [], 1: [0]},
                'behind': {0: [], 1: []},
                'front': {0: [], 1: []}
            }
        }
        
        # Test place_relation_handler
        result = reng.place_relation_handler(test_scene, [0, 1], ['left'])
        if result is True:
            print("✓ place_relation_handler works correctly")
        else:
            print(f"ERROR: place_relation_handler returned {result}, expected True")
            return False
        
        # Test check_relation_exists_handler
        result = reng.check_relation_exists_handler(test_scene, [0, 1], ['left'])
        if result is True:
            print("✓ check_relation_exists_handler correctly identifies existing relation")
        else:
            print(f"ERROR: check_relation_exists_handler returned {result}, expected True")
            return False
        
        result = reng.check_relation_exists_handler(test_scene, [0, 1], ['behind'])
        if result is False:
            print("✓ check_relation_exists_handler correctly identifies non-existing relation")
        else:
            print(f"ERROR: check_relation_exists_handler returned {result}, expected False")
            return False
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to test rearrangement engine: {e}")
        return False


def test_with_sample_data():
    """Test the system with sample data if available."""
    print("\nTesting with sample data...")
    
    # Check if sample data files exist
    refexps_file = '../custom_clevr/output/clevr_ref+_base_refexps.json'
    scenes_file = '../custom_clevr/output/clevr_ref+_scenes.json'
    
    if not os.path.exists(refexps_file):
        print(f"Sample refexps file not found: {refexps_file}")
        print("Skipping sample data test")
        return True
    
    if not os.path.exists(scenes_file):
        print(f"Sample scenes file not found: {scenes_file}")
        print("Skipping sample data test")
        return True
    
    try:
        # Load sample data
        with open(refexps_file, 'r') as f:
            refexps_data = json.load(f)
        print(f"✓ Loaded {len(refexps_data['refexps'])} referring expressions")
        
        with open(scenes_file, 'r') as f:
            scenes_data = json.load(f)
        print(f"✓ Loaded {len(scenes_data['scenes'])} scenes")
        
        # Test with a small subset
        test_refexps = refexps_data['refexps'][:5]  # First 5 expressions
        print(f"Testing with {len(test_refexps)} referring expressions...")
        
        # This would require running the full generation pipeline
        # For now, just verify the data structure is correct
        for i, refexp in enumerate(test_refexps):
            required_keys = ['refexp', 'program', 'image_filename']
            for key in required_keys:
                if key not in refexp:
                    print(f"ERROR: Refexp {i} missing required key '{key}'")
                    return False
        
        print("✓ Sample data structure is correct")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to test with sample data: {e}")
        return False


def main():
    """Run all tests."""
    print("Scene Rearrangement System Test Suite")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test 1: Basic functionality
    if not test_basic_functionality():
        all_tests_passed = False
    
    # Test 2: Rearrangement engine
    if not test_rearrangement_engine():
        all_tests_passed = False
    
    # Test 3: Sample data
    if not test_with_sample_data():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("✓ All tests passed! The scene rearrangement system is ready to use.")
        print("\nTo generate rearrangement expressions, run:")
        print("python generate_rearrangement_expressions.py --help")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()

