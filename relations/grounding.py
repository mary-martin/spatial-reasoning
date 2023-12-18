import json
import os
from scene_objects import Scene_Objects
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from functools import reduce


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
                        grounded[i + 1].append(entity.idx)
                        self.candidate_graph.add_node(entity.idx)
                        found = True
                elif mention_label in features:
                    grounded[i + 1].append(entity.idx)
                    self.candidate_graph.add_node(entity.idx)
                    found = True
                elif color in features:
                    grounded[i + 1].append(entity.idx)
                    self.candidate_graph.add_node(entity.idx)
                    found = True

            if not found:
                ungrounded.append(i + 1)

        return grounded

    def relate(self, mentions):
        self.grounded = self.initial_grounding(mentions)
        true_groundings = self.grounded.keys()
        self.true_nodes = reduce(
            set.union, (set(lst) for lst in self.grounded.values())
        )
        # print(self.true_nodes)
        relations = mentions["relations"]
        self.candidates = self.grounded

        # Loop through relations and find candidates for o2 (goal object) in each relation mention
        while relations:
            ug_relations = []
            for relation in relations:
                o1 = relation["o1"]
                o2 = relation["o2"]
                relation_label = relation["label"]
                o1_exists = o1 in self.candidates.keys()
                o2_exists = o2 in self.candidates.keys()

                if "o3" in relation.keys():
                    if not self.decompose(relation):
                        ug_relations.append(relation)
                elif not o1_exists or o2 in true_groundings:
                    # if the start object (o1) is not grounded
                    # and the goal object is grounded, swap o1 and o2
                    if o2_exists:
                        o1, o2 = o2, o1
                        relation_label = self.inverse_relations[relation_label]
                        self.match_candidates(o1, o2, relation_label)
                    else:
                        # If both objects are ungrounded
                        ug_relations.append(relation)
                else:
                    self.match_candidates(o1, o2, relation_label)

            relations = ug_relations
            # print(self.grounded)
            self.prune_tree()

        return self.candidate_graph

    def match_candidates(self, o1, o2, relation_label):
        o1_entities = self.candidates[o1]
        for obj in o1_entities:
            candidate_obj, matched = self.evaluate_pairs(obj, relation_label)
            if matched:
                self.candidates[o2] = list(
                    reduce(set.union, map(set, [self.candidates[o2], candidate_obj]))
                )

    def clear_graph(self):
        self.candidate_graph.clear()

    def show_candidate_graph(self):
        
        colors = []
        for obj in self.candidate_graph.nodes():
            if obj != self.best_node:
                colors.append('lightblue')
            else:
                colors.append('lightgreen')
                
        pos = nx.nx_agraph.graphviz_layout(
            self.candidate_graph, prog="dot", args="-Grankdir=TB"
        )
        edge_weights = {
            (node1, node2): round(attributes.get("weight", ""), 4)
            for node1, node2, attributes in self.candidate_graph.edges(data=True)
        }
        nx.draw(self.candidate_graph, pos, node_color=colors, with_labels=True, font_weight="bold")
        nx.draw_networkx_edge_labels(
            self.candidate_graph, pos, edge_labels=edge_weights
        )
        node_in_degrees = self.candidate_graph.in_degree()
        plt.show()

    # Function to evaluate pairs of objects based on a spatial relation
    def evaluate_pairs(self, object1, relation_label, base_score=0):
        scene_obj_idx = object1
        relation_direction = self.relation_constraints[relation_label]
        obj_specific_pairs = self.offsets.get_obj_offsets(scene_obj_idx)
        matched_objs = []
        scores = []
        matched = False

        for paired_obj, offset in obj_specific_pairs.items():
            dim = relation_direction[0]
            sign = relation_direction[1]
            direction = offset["direction"]
            if direction[dim] == sign and paired_obj not in self.true_nodes:
                if paired_obj not in self.candidate_graph.nodes():
                    self.candidate_graph.add_node(paired_obj)
                xyz_offsets = abs(np.array(offset["xyz_offsets"]))
                score = self.score_relations(xyz_offsets, dim)
                scores.append(score)
                matched_objs.append(paired_obj)
                if not matched:
                    matched = True

        magnitude, norm_scores = self.calculate_norm(scores)
        for match, final_score in zip(matched_objs, norm_scores):
            self.candidate_graph.add_edge(scene_obj_idx, match, weight=final_score)

        return matched_objs, matched

    # Function to score spatial relations based on distance and ratio
    def score_relations(
        self, xyz_offsets, dim=None, dist_scaling=-0.3, ratio_scaling=1
    ):
        xy_offsets = [xyz_offsets[0], xyz_offsets[1]]
        # direction_distance = xyz_offsets[dim]
        magnitude, vec_norm = self.calculate_norm(xy_offsets)
        if dim:
            norm_offset = vec_norm[dim]
        else:
            norm_offset = 0
        score = dist_scaling * magnitude + ratio_scaling * norm_offset

        return score

    def prune_tree(self):
        G = self.candidate_graph
        predicted_nodes = {}
        leaf_nodes = [node for node in G.nodes() if len(nx.descendants(G, node)) == 0]
        
        # Convert InDegreeView to dictionary
        node_in_degrees = dict(self.candidate_graph.in_degree())

        # Find the maximum in-degree and the corresponding node
        max_in_degree_node = max(node_in_degrees, key=node_in_degrees.get)
        max_in_degree = node_in_degrees[max_in_degree_node]

        for leaf_node in leaf_nodes:
            if node_in_degrees[leaf_node] == max_in_degree:
                incoming_edges = G.in_edges(leaf_node, data=True)
                edge_sum = sum(obj_weight['weight'] for _, _, obj_weight in incoming_edges)
                predicted_nodes[leaf_node] = edge_sum
            else:
                self.candidate_graph.remove_node(leaf_node)

        self.ranked_predictions = sorted(predicted_nodes.items(), key=lambda x: x[1], reverse=True)
        self.best_object = self.ranked_predictions[0]
        self.best_node = self.best_object[0]
        print("Qualifying objects:", self.ranked_predictions)
        print("Best object:", self.best_object)
                

    def decompose(self, relation, weight=-1):
        decomposable = False
        o1, o2, o3 = relation["o1"], relation["o2"], relation["o3"]
        r1 = {"o1": o2, "o2": o1, "label": "opposing"}
        r2 = {"o1": o3, "o1": o1, "label": "opposing"}
        op_relations = [r1, r2]

        if all(obj in self.candidates for obj in [o2, o3]):
            decomposable = True
            o2_idx, o3_idx = self.candidates[o2][0], self.candidates[o3][0]
            o2_offsets, o3_offsets = self.offsets.get_obj_offsets(
                o2_idx
            ), self.offsets.get_obj_offsets(o3_idx)
            for candidate in set(o2_offsets) & set(o3_offsets):
                offset1, offset2 = o2_offsets[candidate], o3_offsets[candidate]
                vector1, vector2 = offset1["direction"], offset2["direction"]
                target_loc, o2_loc, o3_loc = (
                    np.array(self.obj_locations[candidate]),
                    np.array(self.obj_locations[o2]),
                    np.array(self.obj_locations[o3]),
                )

                angle_eval = self.cos_angle(vector1, vector2)
                if angle_eval <= 0.0:
                    distance_to_midpoint = self.euclidean_distance(
                        target_loc, o2_loc, o3_loc
                    )
                    score = self.score_relations(distance_to_midpoint)

                    if candidate not in self.candidate_graph.nodes():
                        self.candidate_graph.add_node(candidate)
                        self.candidates[o1].append(candidate)
                    self.candidate_graph.add_edge(o2_idx, candidate, weight=score / 2)
                    self.candidate_graph.add_edge(o3_idx, candidate, weight=score / 2)

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
        mid_distance = p3 - midpoint

        return mid_distance

    def calculate_norm(self, vector):
        # Calculate the L2 norm (magnitude) of the vector
        magnitude = np.linalg.norm(vector)
        # Normalize the vector
        normalized_vector = vector / magnitude

        return magnitude, normalized_vector
