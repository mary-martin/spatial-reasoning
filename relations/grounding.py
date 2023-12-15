import json
import os
from scene_objects import Scene_Objects
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np


class SpatialPredictor(object):
    def __init__(self, scene_info):
        self.scene_info = scene_info
        self.entities = scene_info.all_entities
        self.offsets = scene_info.obj_offsets
        self.obj_locations = scene_info.all_locations
        self.inverse_relations = {
            "right": "left",
            "front": "behind",
            "left": "right",
            "behind": "front",
        }
        self.relation_constraints = {
            "left": [1, 1],
            "right": [1, -1],
            "front": [0, -1],
            "behind": [0, 1],
        }

    # Function to perform initial grounding of object mentions in the scene
    def initial_grounding(self, mentions):
        """
        Perform initial grounding of object mentions in the scene.

        Parameters:
        - mentions (dict): Dictionary containing mentions in the scene.
        - entities (list): List of entities in the scene.

        Returns:
        - tuple: A tuple containing dictionaries of grounded and ungrounded objects.
        """
        obj_mentions = mentions["objects"]
        grounded = defaultdict(list)
        ungrounded = []
        self.candidate_graph = nx.DiGraph()

        for i, obj in enumerate(obj_mentions):
            found = False
            for entity in self.entities:
                features = [entity.shape, entity.color]
                mention_label = obj["label"]
                color = ""
                if "color" in obj.keys():
                    color = obj["color"]

                # Check if the object mention matches entity features
                if mention_label != "object" and color:
                    if mention_label in features and color in features:
                        grounded[i + 1].append(entity)
                        self.candidate_graph.add_node(entity.idx)
                        found = True
                elif mention_label in features:
                    grounded[i + 1].append(entity)
                    self.candidate_graph.add_node(entity.idx)
                    found = True
                elif color in features:
                    grounded[i + 1].append(entity)
                    self.candidate_graph.add_node(entity.idx)
                    found = True

            if not found:
                ungrounded.append(i + 1)

        return dict(grounded)

    def relate(self, mentions):
        """
        Establish spatial relations between objects in the scene.

        Parameters:
        - mentions (dict): Dictionary containing relations in the scene.
        - grounded (dict): Dictionary containing grounded objects.
        - scene_info (SceneInfo): Information about the scene.

        Returns:
        - dict: Dictionary containing qualifying pairs of objects based on spatial relations.
        """
        self.grounded = self.initial_grounding(mentions)
        relations = mentions["relations"]
        self.candidates = defaultdict(list)
        ug_relations = []
        #
        # Loop through relations and find candidates for o2 (goal object) in each relation mention
        for relation in relations:
            o1 = relation["o1"]
            o2 = relation["o2"]
            relation_label = relation["label"]

            if "o3" in relation.keys():
                if not self.decompose(relation):
                    ug_relations.append(relation)
            elif o1 not in self.grounded.keys():
                # if the start object (o1) is not grounded
                # and the goal object is grounded, swap o1 and o2
                if o2 in self.grounded.keys():
                    o1, o2 = o2, o1
                    # o1 has one or more entities associated with it (from the scene)
                    o1_entities = self.grounded[o1]
                    # loop through the entities associated with o1
                    for obj in o1_entities:
                        inverse_label = self.inverse_relations[relation_label]
                        candidate_obj = self.evaluate_pairs(obj.idx, inverse_label)
                        self.candidates[o2].append(candidate_obj)
                else:
                    # If both objects are ungrounded
                    ug_relations.append(relation)
            else:
                # this is the standard case where o1 is grounded
                o1_entities = self.grounded[o1]
                for obj in o1_entities:
                    candidate_obj = self.evaluate_pairs(obj.idx, relation_label)
                    self.candidates[o2].append(candidate_obj)

        # Handle ungrounded relations
        while ug_relations:
            new_ug_relations = []

            for relation in ug_relations:
                o1 = relation["o1"]
                o2 = relation["o2"]
                relation_label = relation["label"]

                if "o3" in relation.keys():
                    if not self.decompose(relation):
                        new_ug_relations.append(relation)
                print(self.candidates)
                if o1 not in self.candidates.keys():
                    if o2 in self.candidates.keys():
                        # One of the objects is grounded now, add candidates
                        o1, o2 = o2, o1
                        # o1_entities = grounded[o1]
                        # print(candidates[o1])
                        for candidate_set in self.candidates[o1]:
                            for obj in candidate_set.keys():
                                score = candidate_set[obj]["score"]
                                inverse_label = self.inverse_relations[relation_label]
                                self.candidates[o2].append(
                                    self.evaluate_pairs(obj, inverse_label)
                                )
                    else:
                        # Both objects are still ungrounded, keep in the list for the next iteration
                        new_ug_relations.append(relation)
                else:
                    o1_entities = self.candidates[o1]
                    for candidate_set in o1_entities:
                        for obj in candidate_set.keys():
                            score = candidate_set[obj]["score"]
                            self.candidates[o2].append(
                                self.evaluate_pairs(obj, relation_label)
                            )

            ug_relations = new_ug_relations

        return ug_relations, self.candidate_graph

    def clear_graph(self):
        self.candidate_graph.clear()

    def show_candidate_graph(self):
        pos = nx.nx_agraph.graphviz_layout(
            self.candidate_graph, prog="dot", args="-Grankdir=TB"
        )
        print(self.candidate_graph.edges(data=True))
        edge_weights = {
            (node1, node2): round(attributes.get("weight", ""), 4) for node1, node2, attributes in self.candidate_graph.edges(data=True)
        }
        nx.draw(self.candidate_graph, pos, with_labels=True, font_weight="bold")
        nx.draw_networkx_edge_labels(self.candidate_graph, pos, edge_labels=edge_weights)
        plt.show()

    # Function to evaluate pairs of objects based on a spatial relation
    def evaluate_pairs(self, object1, relation_label, base_score=0):
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
        relation_direction = self.relation_constraints[relation_label]
        # print(relation_direction)
        obj_specific_pairs = self.offsets.get_obj_offsets(scene_obj_idx)
        matched_objs = {}

        for paired_obj, offset in obj_specific_pairs.items():
            dim = relation_direction[0]
            sign = relation_direction[1]
            direction = offset["direction"]
            if direction[dim] == sign:
                if paired_obj not in self.candidate_graph.nodes():
                    self.candidate_graph.add_node(paired_obj)
                score = self.score_relations(offset, dim)
                self.candidate_graph.add_edge(scene_obj_idx, paired_obj, weight=score)
                # offset['score'] = score
                matched_objs[paired_obj] = {"score": score, "parent": scene_obj_idx}

        return matched_objs

    # Function to score spatial relations based on distance and ratio
    def score_relations(self, offset, dim, dist_scaling=-1, ratio_scaling=-1):
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

        xyz_offsets = offset["xyz_offsets"]
        direction_distance = abs(xyz_offsets[dim])
        total_distance = np.linalg.norm(np.array(xyz_offsets))
        other_dir = xyz_offsets[compared_direction]
        ratio_offset = direction_distance / abs(other_dir)

        score = (
            dist_scaling * total_distance
            + ratio_scaling * ratio_offset
            + dist_scaling * direction_distance
        )

        return score

    def decompose(self, relation, weight=-1):
        decomposable = False
        o1 = relation["o1"]
        o2 = relation["o2"]
        o3 = relation["o3"]
        r1 = {"o1": o2, "o2": o1, "label": "opposing"}
        r2 = {"o1": o3, "o1": o1, "label": "opposing"}
        op_relations = [r1, r2]

        if o2 and o3 in self.grounded.keys():
            decomposable = True
            o2_idx = self.grounded[o2][0].idx
            o3_idx = self.grounded[o3][0].idx
            o2_offsets = self.offsets.get_obj_offsets(o2_idx)
            o3_offsets = self.offsets.get_obj_offsets(o3_idx)
            for candidate in o2_offsets.keys():
                if candidate in o3_offsets.keys():
                    offset1 = o2_offsets[candidate]
                    offset2 = o3_offsets[candidate]
                    vector1 = offset1["direction"]
                    vector2 = offset2["direction"]
                    target_loc = np.array(self.obj_locations[candidate])
                    o2_loc = np.array(self.obj_locations[o2])
                    o3_loc = np.array(self.obj_locations[o3])
                    score = self.cos_angle(vector1, vector2)
                    if score <= 0.0:
                        score = weight * self.euclidean_distance(
                            target_loc, o2_loc, o3_loc
                        )
                        print(score)
                        if candidate not in self.candidate_graph.nodes():
                            self.candidate_graph.add_node(candidate)
                        self.candidate_graph.add_edge(o2_idx, candidate, weight=score/2)
                        self.candidate_graph.add_edge(o3_idx, candidate, weight=score/2)

        return decomposable

    def cos_angle(self, vector_A, vector_B):
        # Calculate the dot product
        dot_product = np.dot(vector_A, vector_B)

        # Calculate the magnitudes
        magnitude_A = np.linalg.norm(vector_A)
        magnitude_B = np.linalg.norm(vector_B)

        # Calculate the cosine of the angle
        cosine_angle = dot_product / (magnitude_A * magnitude_B)

        return cosine_angle

    def euclidean_distance(self, p3, p1, p2):
        midpoint = (p1 + p2) / 2
        mid_distance = np.linalg.norm(p3 - midpoint)

        return mid_distance
