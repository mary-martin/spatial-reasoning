import json
import os
from scene_objects import Scene_Objects
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from functools import reduce


class SpatialPredictor(object):
    """
    The SpatialPredictor class performs spatial relation grounding using scene information from CLEVR.
    It handles the grounding of multiple mentions from an input expression using a single SpatialPredictor object.
    """

    def __init__(self, scene_info):
        """
        Initializes the SpatialPredictor object.

        Parameters:
        - scene_info: An instance of the Scene_Objects class containing scene information.
        """
        self.scene_info = scene_info
        # all entity objects from the scene
        self.entities = scene_info.all_entities
        # offsets between all paired objects in the scene
        self.offsets = scene_info.obj_offsets
        # locations of all objects in the scene
        self.obj_locations = scene_info.all_locations
        # relations that are opposing
        self.inverse_relations = {
            "right": "left",
            "front": "behind",
            "left": "right",
            "behind": "front",
        }
        # constraints to do initial spatial constraint grounding
        self.relation_constraints = {
            "left": [1, 1],
            "right": [1, -1],
            "front": [0, -1],
            "behind": [0, 1],
        }

    # Function to perform initial grounding of object mentions in the scene
    def initial_grounding(self, mentions):
        # mentioned objects from the expression
        obj_mentions = mentions["objects"]
        # dictionary to store lists of associated grounding objects
        grounded = defaultdict(list)
        # store ungrounded relations in a list
        ungrounded = []
        # candidate graph created to store candidate groundings
        self.candidate_graph = nx.DiGraph()

        # Iterate through all object mentions
        # if an object mention has an associated color or label (shape)
        # find any object in the scene that has a matching descriptor
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
        # return any objects that have been grounded
        return grounded

    def relate(self, mentions):
        """
        Relates objects in the scene based on spatial relations mentioned in the input expression.

        Parameters:
        - mentions: A dictionary containing mentions from the input expression.

        Returns:
        - candidate_graph: A directed graph representing the candidate spatial relations.
        """
        self.grounded = self.initial_grounding(mentions)
        true_groundings = self.grounded.keys()
        # we use objects from the initial grounding to guide spatial relation grounding
        # we make the assumptions that these groundings are true, or not candidates
        self.true_nodes = reduce(
            set.union, (set(lst) for lst in self.grounded.values())
        )
        # print(self.true_nodes)
        # get the spatial relations from the stored expression information
        relations = mentions["relations"]
        # initialize the dictionary of proposed candidates with true groundings
        self.candidates = self.grounded

        # Repeat grounding process until all relations are grounded
        while relations:
            # init array of relations that cannot be grounded during the current iteration
            ug_relations = []
            # loop through list of current relations that must be grounded
            for relation in relations:
                # o1 and o2 refer to the start and goal node in a directed relation (from the expression)
                o1 = relation["o1"]
                o2 = relation["o2"]
                # get the relation label from the mention ('left', 'right', 'front', 'behind', 'between')
                relation_label = relation["label"]
                # store whether each object already has associated entities from the scene
                o1_exists = o1 in self.candidates.keys()
                o2_exists = o2 in self.candidates.keys()

                # if a relation contains 3 mentioned objects,
                # it can be decomposed into pairwise relations
                if "o3" in relation.keys():
                    if not self.decompose(relation):
                        ug_relations.append(relation)
                # if o1 already has associated candidates
                # or o2 is in the list of true grounded nodes (does not need to search for candidates)
                # swap o1 and o2 so that o2 is the goal object to be grounded
                elif not o1_exists or o2 in true_groundings:
                    # if the start object (o1) is not grounded
                    # and the goal object is grounded, swap o1 and o2
                    if o2_exists:
                        o1, o2 = o2, o1
                        # invert the relation type if o1 and o1 have been swapped
                        relation_label = self.inverse_relations[relation_label]
                        # find candidates that match the given relation
                        self.match_candidates(o1, o2, relation_label)
                    else:
                        # If both objects are ungrounded, add to the list
                        # of ungrounded objects to be grounded in a future iteration
                        ug_relations.append(relation)
                else:
                    # covers the case that o1 exists in the candidate graph
                    self.match_candidates(o1, o2, relation_label)
            # after each iteration, ungrounded relations are assigned as the new list of relations
            relations = ug_relations
            # print(self.grounded)
            # prunes any infeasible edges and finds the best node based on the input expression
            self.prune_tree()

        return self.candidate_graph

    def match_candidates(self, o1, o2, relation_label):
        """
        Matches candidates for spatial relations between two objects.

        Parameters:
        - o1: Object 1 identifier.
        - o2: Object 2 identifier.
        - relation_label: Spatial relation label.

        Updates the candidates dictionary.
        """
        # o1 has existing candidates in the grapth
        # get associated candidate objects
        o1_entities = self.candidates[o1]
        for obj in o1_entities:
            # for each o1 candidate,
            # find a set of o2 candidates that match the given relation
            candidate_obj, matched = self.evaluate_pairs(obj, relation_label)
            # if any objects have een found that fit the specified relation,
            # add them to the list of candidates for o2
            if matched:
                self.candidates[o2] = list(
                    reduce(set.union, map(set, [self.candidates[o2], candidate_obj]))
                )

    def clear_graph(self):
        self.candidate_graph.clear()

    def show_candidate_graph(self):
        """
        Displays the candidate graph using NetworkX and Matplotlib.
        Nodes associated with the best object are colored in lightgreen.

        Edge weights are displayed.

        Requires the Graphviz layout engine.

        Note: This function assumes the existence of 'best_node', 'candidate_graph', and 'ranked_predictions' attributes.
        """
        colors = []
        for obj in self.candidate_graph.nodes():
            if obj != self.best_node:
                colors.append("lightblue")
            else:
                colors.append("lightgreen")

        pos = nx.nx_agraph.graphviz_layout(
            self.candidate_graph, prog="dot", args="-Grankdir=TB"
        )
        edge_weights = {
            (node1, node2): round(attributes.get("weight", ""), 4)
            for node1, node2, attributes in self.candidate_graph.edges(data=True)
        }
        nx.draw(
            self.candidate_graph,
            pos,
            node_color=colors,
            with_labels=True,
            font_weight="bold",
        )
        nx.draw_networkx_edge_labels(
            self.candidate_graph, pos, edge_labels=edge_weights
        )
        node_in_degrees = self.candidate_graph.in_degree()
        plt.show()

    # Function to evaluate pairs of objects based on a spatial relation
    def evaluate_pairs(self, object1, relation_label, base_score=0):
        """
        Evaluates pairs of objects based on a spatial relation.

        Parameters:
        - object1: The index of the object for which pairs are being evaluated.
        - relation_label: Spatial relation label.
        - base_score: Base score for the relation.

        Returns:
        - matched_objs: List of matched objects.
        - matched: Boolean indicating whether at least one candidate object has been found.
        """
        scene_obj_idx = object1
        # get the directional constraint based on the relation label
        relation_direction = self.relation_constraints[relation_label]
        # get all of the stored offsets between the object and all other scene objects
        obj_specific_pairs = self.offsets.get_obj_offsets(scene_obj_idx)
        matched_objs = []
        scores = []
        matched = False

        # iterate through all offset pairs (potential edges)
        for paired_obj, offset in obj_specific_pairs.items():
            dim = relation_direction[0]
            sign = relation_direction[1]
            direction = offset["direction"]
            # check that the pair (edge) adheres to the relation constraint
            # and that the paired object is not one of the 'true' nodes
            if direction[dim] == sign and paired_obj not in self.true_nodes:
                # if constraints are satisfied, add the scene object to the candidate graph
                if paired_obj not in self.candidate_graph.nodes():
                    self.candidate_graph.add_node(paired_obj)
                xyz_offsets = abs(np.array(offset["xyz_offsets"]))
                # score the relation based on vector (xyz) distance
                score = self.score_relations(xyz_offsets, dim)
                # add to list of scores
                scores.append(score)
                matched_objs.append(paired_obj)
                if not matched:
                    matched = True
        # normalize all object scores
        _, norm_scores = self.calculate_norm(scores)
        for match, final_score in zip(matched_objs, norm_scores):
            # add an edge to the candidate graph for each matched object
            self.candidate_graph.add_edge(scene_obj_idx, match, weight=final_score)

        # return set of matched objects and whether a match has been found
        return matched_objs, matched

    def score_relations(self, xyz_offsets, dim=None, params=(0.3, 1)):
        """
        Scores spatial relations based on distance (magnitude) and vector composition.

        Parameters:
        - xyz_offsets: List of XYZ offsets.
        - dim: Dimension for dimension-specific relations.
        - params: Tuple of scaling parameters for distance and vector components.

        Returns:
        - score: Score for the spatial relation.
        """
        dist_scaling, vec_scaling = params
        xy_offsets = [xyz_offsets[0], xyz_offsets[1]]
        # direction_distance = xyz_offsets[dim]
        magnitude, vec_norm = self.calculate_norm(xy_offsets)
        if dim:
            norm_offset = vec_norm[dim]
        else:
            # covers the case that the relation is not dimension specific (between)
            norm_offset = 0
        score = -1 * dist_scaling * magnitude + vec_scaling * norm_offset

        return score

    def prune_tree(self):
        """
        Prunes the candidate graph based on the in-degree of nodes.
        Selects the best object (leaf node) based on the highest in-degree.

        Note: This function assumes the existence of 'candidate_graph', 'true_nodes', 'best_node', and 'ranked_predictions' attributes.
        """
        G = self.candidate_graph
        predicted_nodes = {}
        # the direction of the candidate graph always flows towards the predicted targets
        # so we get the leaf nodes of the graph
        leaf_nodes = [node for node in G.nodes() if len(nx.descendants(G, node)) == 0]
        node_in_degrees = dict(self.candidate_graph.in_degree())

        # Find the maximum in-degree and the corresponding node
        max_in_degree_node = max(node_in_degrees, key=node_in_degrees.get)
        max_in_degree = node_in_degrees[max_in_degree_node]

        # remove nodes that do not have the max number of incoming edges
        for leaf_node in leaf_nodes:
            if node_in_degrees[leaf_node] == max_in_degree:
                incoming_edges = G.in_edges(leaf_node, data=True)
                edge_sum = sum(
                    obj_weight["weight"] for _, _, obj_weight in incoming_edges
                )
                # store the incoming edge sum as the score for the proedicted object
                predicted_nodes[leaf_node] = edge_sum
            else:
                self.candidate_graph.remove_node(leaf_node)

        # sort the predictions based on score (high to low)
        self.ranked_predictions = sorted(
            predicted_nodes.items(), key=lambda x: x[1], reverse=True
        )
        # select object with the highest score as the best object
        # also store all of the candidates that still fulfill the relation(s)
        self.best_object = self.ranked_predictions[0]
        self.best_node = self.best_object[0]
        print("Qualifying objects:", self.ranked_predictions)
        print("Best object:", self.best_object)

    def decompose(self, relation, weight=-1):
        """
        Decomposes a relation into pairwise relations.

        Parameters:
        - relation: The relation to decompose.
        - weight: Weight parameter for scoring.

        Returns:
        - decomposable: Boolean indicating whether decomposition is possible.
        """
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
