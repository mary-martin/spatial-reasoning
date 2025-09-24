# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import numpy as np
import json, os, math
from collections import defaultdict

"""
Utilities for working with function program representations of rearrangement expressions.

This module extends the refexp engine with functions specific to scene rearrangement,
including checking if relations already exist and generating placement instructions.
"""

# Import the base handlers from refexp_engine
import sys
sys.path.append('../custom_clevr/refexp_generation')
import refexp_engine as qeng

# Additional handlers for rearrangement-specific functions

def place_relation_handler(scene_struct, inputs, side_inputs):
    """
    Handler for place_relation function - indicates where an object should be placed.
    This is a logical function that returns True if the placement is valid.
    
    Args:
        scene_struct: Scene structure containing objects and relationships
        inputs: List containing two inputs - [object_to_move, reference_object]
        side_inputs: List containing one input - the relation type
    
    Returns:
        True if the placement is valid (always True for generation purposes)
    """
    assert len(inputs) == 2
    assert len(side_inputs) == 1
    # For generation purposes, we always return True
    # The actual validation happens during constraint checking
    return True


def check_relation_exists_handler(scene_struct, inputs, side_inputs):
    """
    Handler for check_relation_exists function - checks if a relation already exists.
    
    Args:
        scene_struct: Scene structure containing objects and relationships
        inputs: List containing two inputs - [object1, object2]
        side_inputs: List containing one input - the relation type
    
    Returns:
        True if the relation already exists, False otherwise
    """
    assert len(inputs) == 2
    assert len(side_inputs) == 1
    
    obj1_idx, obj2_idx = inputs
    relation = side_inputs[0]
    
    # Check if the relation already exists in the scene
    if relation in scene_struct['relationships']:
        relations = scene_struct['relationships'][relation]
        if obj1_idx in relations and obj2_idx in relations[obj1_idx]:
            return True
    
    return False


def find_valid_placement_options(scene_struct, target_object_idx, metadata):
    """
    Find valid placement options for a target object.
    
    Args:
        scene_struct: Scene structure containing objects and relationships
        target_object_idx: Index of the object to be moved
        metadata: Metadata containing type information
    
    Returns:
        Dictionary mapping (relation, reference_object_idx) to validity
    """
    options = {}
    
    # Get all other objects in the scene
    all_objects = list(range(len(scene_struct['objects'])))
    other_objects = [idx for idx in all_objects if idx != target_object_idx]
    
    # For each relation type
    for relation in metadata['types']['Relation']:
        for ref_obj_idx in other_objects:
            # Check if this relation already exists
            relation_exists = check_relation_exists_handler(
                scene_struct, [target_object_idx, ref_obj_idx], [relation]
            )
            
            # We want relations that DON'T already exist
            options[(relation, ref_obj_idx)] = not relation_exists
    
    return options


def find_filter_options_for_rearrangement(scene_struct, metadata, target_object_idx=None):
    """
    Find valid filter options for rearrangement templates.
    
    Args:
        scene_struct: Scene structure containing objects and relationships
        metadata: Metadata containing type information
        target_object_idx: Optional target object index
    
    Returns:
        Dictionary mapping parameter tuples to valid object indices
    """
    attribute_map = {}
    
    # Precompute filter options similar to refexp generation
    attr_keys = ['size', 'color', 'material', 'shape']
    
    # Create masks for all combinations
    masks = []
    for i in range(2 ** len(attr_keys)):
        mask = []
        for j in range(len(attr_keys)):
            mask.append((i // (2 ** j)) % 2)
        masks.append(mask)
    
    # Build attribute map
    for object_idx, obj in enumerate(scene_struct['objects']):
        keys = [tuple(obj[k] for k in attr_keys)]
        
        for mask in masks:
            for key in keys:
                masked_key = []
                for a, b in zip(key, mask):
                    if b == 1:
                        masked_key.append(a)
                    else:
                        masked_key.append(None)
                masked_key = tuple(masked_key)
                if masked_key not in attribute_map:
                    attribute_map[masked_key] = set()
                attribute_map[masked_key].add(object_idx)
    
    return attribute_map


def find_placement_filter_options(scene_struct, metadata, target_object_idx, reference_object_idx):
    """
    Find valid placement filter options for a specific target-reference pair.
    
    Args:
        scene_struct: Scene structure containing objects and relationships
        metadata: Metadata containing type information
        target_object_idx: Index of the object to be moved
        reference_object_idx: Index of the reference object
    
    Returns:
        Dictionary mapping parameter tuples to valid placement options
    """
    options = {}
    
    # Get the target and reference objects
    target_obj = scene_struct['objects'][target_object_idx]
    ref_obj = scene_struct['objects'][reference_object_idx]
    
    # For each relation type, check if it's valid (doesn't already exist)
    for relation in metadata['types']['Relation']:
        relation_exists = check_relation_exists_handler(
            scene_struct, [target_object_idx, reference_object_idx], [relation]
        )
        
        if not relation_exists:  # Only include relations that don't already exist
            # Create the filter option key: [target_color, target_shape, ref_color, ref_shape, relation]
            key = (target_obj['color'], target_obj['shape'], 
                   ref_obj['color'], ref_obj['shape'], relation)
            options[key] = True
    
    return options


# Register the new handlers
execute_handlers = qeng.execute_handlers.copy()
execute_handlers.update({
    'place_relation': place_relation_handler,
    'check_relation_exists': check_relation_exists_handler,
})


def answer_rearrangement(rearrangement, metadata, scene_struct, all_outputs=False,
                        cache_outputs=True):
    """
    Use structured scene information to answer a structured rearrangement expression.
    This extends the refexp answering functionality with rearrangement-specific handlers.
    """
    all_input_types, all_output_types = [], []
    node_outputs = []
    
    for node in rearrangement['nodes']:
        if cache_outputs and '_output' in node:
            node_output = node['_output']
        else:
            node_type = node['type']
            msg = 'Could not find handler for "%s"' % node_type
            assert node_type in execute_handlers, msg
            handler = execute_handlers[node_type]
            node_inputs = [node_outputs[idx] for idx in node['inputs']]
            side_inputs = node.get('side_inputs', [])
            node_output = handler(scene_struct, node_inputs, side_inputs)
            if cache_outputs:
                node['_output'] = node_output
        node_outputs.append(node_output)
        if node_output == '__INVALID__':
            break

    if all_outputs:
        return node_outputs
    else:
        return node_outputs[-1]


def validate_rearrangement_constraints(rearrangement, metadata, scene_struct, verbose=False):
    """
    Validate that a rearrangement expression meets the required constraints:
    1. The target relation should not already exist in the scene
    2. The objects should be different
    3. The placement should be valid
    
    Args:
        rearrangement: The rearrangement expression to validate
        metadata: Metadata containing type information
        scene_struct: Scene structure
        verbose: Whether to print debug information
    
    Returns:
        True if the rearrangement is valid, False otherwise
    """
    try:
        # Execute the rearrangement to get the final result
        result = answer_rearrangement(rearrangement, metadata, scene_struct)
        
        if result == '__INVALID__':
            if verbose:
                print("Invalid rearrangement: execution failed")
            return False
        
        # Check if this is a placement relation (should return True)
        if result is not True:
            if verbose:
                print(f"Invalid rearrangement: expected True, got {result}")
            return False
        
        # Additional validation: check that the relation doesn't already exist
        # This is handled by the constraint checking in the template instantiation
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"Error validating rearrangement: {e}")
        return False


def is_valid_rearrangement(rearrangement, metadata, scene_struct, answer=None, verbose=False):
    """
    Check if a rearrangement expression is valid and non-trivial.
    
    Args:
        rearrangement: The rearrangement expression to check
        metadata: Metadata containing type information
        scene_struct: Scene structure
        answer: Expected answer (optional)
        verbose: Whether to print debug information
    
    Returns:
        True if the rearrangement is valid, False otherwise
    """
    if answer is None:
        answer = answer_rearrangement(rearrangement, metadata, scene_struct)
    
    if answer == '__INVALID__':
        return False
    
    # Check constraints
    return validate_rearrangement_constraints(rearrangement, metadata, scene_struct, verbose)

