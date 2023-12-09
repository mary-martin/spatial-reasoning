import json
import os
from scene_objects import Scene_Objects
from collections import defaultdict
import math

# Define inverse relations for later use
inverse_relations = {'right': 'left', 'front': 'behind', 'left': 'right', 'behind': 'front'}

# Define relation directions to represent the spatial relationships
relation_directions = {'left': [1, 1], 'right': [1, -1], 'front': [0, -1], 'behind': [0, 1]}

# Function to perform initial grounding of object mentions in the scene
def initial_grounding(mentions, entities):
    """
    Perform initial grounding of object mentions in the scene.

    Parameters:
    - mentions (dict): Dictionary containing mentions in the scene.
    - entities (list): List of entities in the scene.

    Returns:
    - tuple: A tuple containing dictionaries of grounded and ungrounded objects.
    """
    obj_mentions = mentions['objects']
    grounded = defaultdict(list)
    ungrounded = []

    for i, obj in enumerate(obj_mentions):
        found = False
        for entity in entities:
            features = [entity.shape, entity.color]
            mention_label = obj['label']
            color = ''
            if 'color' in obj.keys():
                color = obj['color']
            
            # Check if the object mention matches entity features
            if mention_label != 'object' and color:
                if mention_label in features and color in features:
                    grounded[i + 1].append(entity)
                    found = True
            elif mention_label in features:
                grounded[i + 1].append(entity)
                found = True
            elif color in obj.keys():
                if obj['color'] in features:
                    grounded[i + 1].append(entity)
                    found = True
        if not found:
            ungrounded.append(i + 1)

    return dict(grounded), ungrounded

# DONE
# Function to establish spatial relations between objects in the scene
# loop through relations and find candidates for o2 (goal object) in each relation
# also return relations that do not have an o1 or o2 in grounded
# TODO
# then add index of o2 from relation that has been grounded
# store the candidates and their scores for the object mention associated with o2
# if the grounded object mention is in an ungrounded relation, 
# loop through ungrounded relations and check if the newly grounded relation is in an ungrounded relation
# if so, find 'child' candidates for each candidate object and 
# add the base score for each candidate to the child candidate score
# return the list of child candidates for each parent candidate
# iterate until no ungrounded relations remain
# record the 'path' of candidates and the cumulative path score 
# the path is a list of consecutive objects from the scene (their indices) and represents a possible
# set of objects that correspond to the relation mentions

def relate(mentions, grounded, scene_info):
    """
    Establish spatial relations between objects in the scene.

    Parameters:
    - mentions (dict): Dictionary containing relations in the scene.
    - grounded (dict): Dictionary containing grounded objects.
    - scene_info (SceneInfo): Information about the scene.

    Returns:
    - dict: Dictionary containing qualifying pairs of objects based on spatial relations.
    """
    relations = mentions['relations']
    candidates = defaultdict(list)
    ug_relations = []
    # graph = defaultdict(list)  # Graph to store linked relations
    # 
    # Loop through relations and find candidates for o2 (goal object) in each relation mention
    for relation in relations:
        o1 = relation['o1']
        o2 = relation['o2']
        relation_label = relation['label']

        if o1 not in grounded.keys():
            # if the start object (o1) is not grounded 
            # and the goal object is grounded, swap o1 and o2
            if o2 in grounded.keys():
                o1, o2 = o2, o1
                # o1 has one or more entities associated with it (from the scene)
                o1_entities = grounded[o1]
                # loop through the entities associated with o1
                for obj in o1_entities:
                    inverse_label = inverse_relations[relation_label]
                    candidate_obj = evaluate_pairs(obj.idx, inverse_label, scene_info)
                    candidates[o2].append(candidate_obj)
            else:
                # If both objects are ungrounded
                ug_relations.append(relation)
        else:
            # this is the standard case where o1 is grounded
            o1_entities = grounded[o1]
            for obj in o1_entities:
                candidate_obj = evaluate_pairs(obj.idx, relation_label, scene_info)
                candidates[o2].append(candidate_obj)

    # Handle ungrounded relations
    while ug_relations:
        new_ug_relations = []

        for relation in ug_relations:
            o1 = relation['o1']
            o2 = relation['o2']
            relation_label = relation['label']

            print(candidates)
            if o1 not in candidates.keys():
                if o2 in candidates.keys():
                # One of the objects is grounded now, add candidates
                    o1, o2 = o2, o1
                    # o1_entities = grounded[o1]
                    # print(candidates[o1])
                    for candidate_set in candidates[o1]:
                        for obj in candidate_set.keys():
                            score = candidate_set[obj]['score']
                            inverse_label = inverse_relations[relation_label]
                            candidates[o2].append(evaluate_pairs(obj, inverse_label, scene_info, score))
                            # graph[o1].append(relation)
                else:
                    # Both objects are still ungrounded, keep in the list for the next iteration
                    new_ug_relations.append(relation)
            else:
                o1_entities = candidates[o1]
                for candidate_set in o1_entities:
                    for obj in candidate_set.keys():
                        score = candidate_set[obj]['score']
                        candidates[o2].append(evaluate_pairs(obj, relation_label, scene_info, score))

        ug_relations = new_ug_relations

    return dict(candidates), ug_relations
    

# Function to evaluate pairs of objects based on a spatial relation
def evaluate_pairs(object1, relation_label, scene_info, base_score=0):
    """
    Evaluate pairs of objects based on a spatial relation.

    Parameters:
    - object1 (Entity): The first object in the relation.
    - relation_label (str): The spatial relation label.
    - scene_info (SceneInfo): Information about the scene.

    Returns:
    - dict: Dictionary of matched objects and their offsets.
    """
    scene_obj_idx = object1
    relation_direction = relation_directions[relation_label]
    # print(relation_direction)
    offsets = scene_info.obj_offsets
    obj_specific_pairs = offsets.get_obj_offsets(scene_obj_idx)
    matched_objs = {}

    for paired_obj, offset in obj_specific_pairs.items():
        dim = relation_direction[0]
        sign = relation_direction[1]
        direction = offset['direction']
        if direction[dim] == sign:
            score = score_relations(offset, dim) + base_score
            # offset['score'] = score
            matched_objs[paired_obj] = {'score':score, 'parent': scene_obj_idx}

    return matched_objs


# Function to score spatial relations based on distance and ratio
def score_relations(offset, dim, dist_scaling=-1, ratio_scaling=-1):
    """
    Score spatial relations based on distance and ratio.

    Parameters:
    - offset (dict): Offset information between two objects.
    - dim (int): Dimension along which the relation is evaluated.
    - dist_scaling (float): Scaling factor for distance in the score calculation.
    - ratio_scaling (float): Scaling factor for ratio in the score calculation.

    Returns:
    - float: Score of the spatial relation.
    """
    compared_direction = 0

    if dim == compared_direction:
        compared_direction = 1

    xyz_offsets = offset['xyz_offsets']
    direction_distance = abs(xyz_offsets[dim])
    other_dir = xyz_offsets[compared_direction]
    ratio_offset = direction_distance / abs(other_dir)

    score = dist_scaling * direction_distance + ratio_scaling * ratio_offset

    return score
