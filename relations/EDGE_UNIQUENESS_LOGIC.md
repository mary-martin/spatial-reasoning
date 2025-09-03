# Edge Uniqueness Analysis Logic

## Overview

This document explains the detailed logic and algorithms used for analyzing uniqueness in CLEVR scene graphs. The analysis focuses on two main approaches: **1-edge uniqueness** and **2-edge uniqueness**, each with different definitions and computational methods.

## 1-Edge Uniqueness Analysis

### Definition
**1-edge uniqueness** identifies objects that have unique patterns of incoming or outgoing relations. An object has unique incoming relations if it receives a specific relation type only once from any other object. Similarly, an object has unique outgoing relations if it sends a specific relation type only once to any other object.

### Algorithm Logic

#### Step 1: Graph Construction
```python
def create_graph_from_scene(scene_info):
    G = nx.DiGraph()
    
    # Add nodes for each object
    for i, entity in enumerate(scene_info.all_entities):
        G.add_node(i, color=entity.color, shape=entity.shape)
    
    # Add edges based on scene_relations
    for pair, relations in scene_info.scene_relations.items():
        if relations:
            obj1_idx, obj2_idx = pair
            edge_label = ", ".join(relations)
            G.add_edge(obj1_idx, obj2_idx, label=edge_label, relations=relations)
    
    return G
```

#### Step 2: Relation Collection
```python
def analyze_object_specific_uniqueness(scene_info, G):
    # Initialize dictionaries to store relations per object
    object_incoming_relations = defaultdict(list)
    object_outgoing_relations = defaultdict(list)
    
    # Collect all relations for each object
    for edge in G.edges(data=True):
        source, target = edge[0], edge[1]
        relations = edge[2]['relations']
        
        for rel in relations:
            object_outgoing_relations[source].append(rel)  # Object sends this relation
            object_incoming_relations[target].append(rel)  # Object receives this relation
```

#### Step 3: Uniqueness Detection
```python
    objects_with_unique_incoming = []
    objects_with_unique_outgoing = []
    
    for obj_idx in G.nodes():
        incoming_rels = object_incoming_relations[obj_idx]
        outgoing_rels = object_outgoing_relations[obj_idx]
        
        # Count frequency of each relation type
        incoming_counts = Counter(incoming_rels)
        outgoing_counts = Counter(outgoing_rels)
        
        # Find relations that appear only once (unique)
        unique_incoming = [rel for rel, count in incoming_counts.items() if count == 1]
        unique_outgoing = [rel for rel, count in outgoing_counts.items() if count == 1]
        
        if unique_incoming:
            objects_with_unique_incoming.append((obj_idx, unique_incoming))
        if unique_outgoing:
            objects_with_unique_outgoing.append((obj_idx, unique_outgoing))
```

### Key Concepts

1. **Object-Specific**: Uniqueness is defined per individual object, not globally
2. **Incoming Relations**: Relations that an object receives from other objects
3. **Outgoing Relations**: Relations that an object sends to other objects
4. **Frequency-Based**: A relation is unique if it appears only once for that object

### Example
Consider a scene with 3 objects:
- Object 0 (blue cube) receives: ["left", "left", "front"]
- Object 1 (green sphere) receives: ["right", "behind"]
- Object 2 (red cylinder) receives: ["left", "right"]

**Analysis**:
- Object 0: "front" is unique (appears only once)
- Object 1: "right" and "behind" are both unique (each appears only once)
- Object 2: No unique incoming relations (both "left" and "right" appear once, but this is normal for 2 relations)

## 2-Edge Uniqueness Analysis

### Definition
**2-edge uniqueness** identifies unique combinations of two connected edges that end at a specific node. A 2-edge path is a sequence of two connected edges (e.g., A → B → C). A combination is considered unique if it appears only once for that specific ending node.

### Algorithm Logic

#### Step 1: Path Discovery
```python
def find_incoming_unique_2edge_paths(scene_info):
    G = nx.DiGraph()
    # ... graph construction ...
    
    # Find all 2-edge paths with individual label combinations ENDING at each node
    node_specific_combinations = defaultdict(lambda: defaultdict(list))
    
    for end_node in G.nodes():
        # Find all nodes that have edges TO this end_node
        for first_node in G.predecessors(end_node):
            # Get individual labels from first edge (first_node -> end_node)
            first_edge_relations = G[first_node][end_node]['relations']
            
            # Find all nodes that have edges TO the first_node
            for second_node in G.predecessors(first_node):
                if second_node != end_node:  # Avoid cycles
                    # Get individual labels from second edge (second_node -> first_node)
                    second_edge_relations = G[second_node][first_node]['relations']
                    
                    # Create ALL combinations of individual labels
                    for second_label, first_label in product(second_edge_relations, first_edge_relations):
                        edge_combination = (second_label, first_label)
                        path = (second_node, first_node, end_node)
                        
                        # Store the path with the specific label combination FOR THIS ENDING NODE
                        node_specific_combinations[end_node][edge_combination].append(path)
```

#### Step 2: Uniqueness Detection
```python
    # Find unique combinations PER ENDING NODE
    node_unique_combinations = defaultdict(list)
    node_non_unique_combinations = defaultdict(list)
    
    for end_node in node_specific_combinations:
        for combination, paths in node_specific_combinations[end_node].items():
            if len(paths) == 1:
                # This combination is unique for this ending node
                node_unique_combinations[end_node].append((combination, paths[0]))
            else:
                # This combination appears multiple times for this ending node
                node_non_unique_combinations[end_node].append((combination, paths))
```

### Key Concepts

1. **Incoming Paths**: Focus on paths that END at a specific node
2. **Individual Label Combinations**: Consider each individual relation label, not full edge labels
3. **Node-Specific**: Uniqueness is defined per ending node, not globally
4. **Path Structure**: A 2-edge path has the form: (second_node) --[second_label]--> (first_node) --[first_label]--> (end_node)

### Example
Consider a scene with 3 objects:
- Edge 0→1: ["left", "front"]
- Edge 1→2: ["right"]
- Edge 0→2: ["behind"]

**2-Edge Paths ending at Node 2**:
1. Path 0→1→2: 
   - Individual combinations: ("left", "right"), ("front", "right")
2. Path 0→2: (direct edge, not a 2-edge path)

**Analysis for Node 2**:
- Combination ("left", "right"): Appears once → UNIQUE
- Combination ("front", "right"): Appears once → UNIQUE

## Important Implementation Details

### Graph Representation
- **Directed Graph**: Uses NetworkX DiGraph to represent spatial relationships
- **Edge Labels**: Each edge can have multiple relation labels (e.g., ["left", "front"])
- **Node Attributes**: Store object properties (color, shape, index)

### Data Structures
```python
# For 1-edge analysis
object_incoming_relations = defaultdict(list)  # obj_idx -> [relation1, relation2, ...]
object_outgoing_relations = defaultdict(list)  # obj_idx -> [relation1, relation2, ...]

# For 2-edge analysis
node_specific_combinations = defaultdict(lambda: defaultdict(list))  # end_node -> combination -> [paths]
node_unique_combinations = defaultdict(list)  # end_node -> [(combination, path), ...]
```

### Key Differences Between 1-Edge and 2-Edge Analysis

| Aspect | 1-Edge Analysis | 2-Edge Analysis |
|--------|----------------|-----------------|
| **Scope** | Individual objects | Paths ending at objects |
| **Uniqueness Definition** | Per object's incoming/outgoing relations | Per ending node's incoming paths |
| **Pattern Type** | Direct relations | Multi-step paths |
| **Complexity** | O(E) where E = number of edges | O(V²×E) where V = vertices, E = edges |
| **Educational Value** | Pattern recognition | Multi-step reasoning |

### Computational Complexity

#### 1-Edge Analysis
- **Time Complexity**: O(E) where E is the number of edges
- **Space Complexity**: O(V + E) where V is the number of vertices
- **Main Operations**: 
  - Graph traversal: O(E)
  - Relation counting: O(E)
  - Uniqueness detection: O(V)

#### 2-Edge Analysis
- **Time Complexity**: O(V²×E) in worst case
- **Space Complexity**: O(V²×E) for storing all path combinations
- **Main Operations**:
  - Path discovery: O(V²×E)
  - Combination generation: O(V²×E)
  - Uniqueness detection: O(V²×E)

### Edge Cases and Considerations

1. **Cycles**: Avoid creating paths that form cycles (e.g., A→B→A)
2. **Multiple Relations per Edge**: Handle edges with multiple relation labels
3. **Empty Scenes**: Handle scenes with no objects or no relationships
4. **Self-Loops**: Consider whether self-loops should be included (typically excluded)

### Validation and Testing

#### 1-Edge Validation
```python
# Verify that unique relations actually appear only once
for obj_idx, unique_relations in objects_with_unique_incoming:
    for rel in unique_relations:
        count = object_incoming_relations[obj_idx].count(rel)
        assert count == 1, f"Relation {rel} appears {count} times for object {obj_idx}"
```

#### 2-Edge Validation
```python
# Verify that unique combinations appear only once per ending node
for end_node, combinations in node_unique_combinations.items():
    for combination, path in combinations:
        count = len(node_specific_combinations[end_node][combination])
        assert count == 1, f"Combination {combination} appears {count} times for node {end_node}"
```

## Results Interpretation

### 1-Edge Results
- **High uniqueness**: Indicates objects with distinctive spatial patterns
- **Low uniqueness**: Indicates objects with common spatial relationships
- **Educational value**: Enables pattern recognition and object identification

### 2-Edge Results
- **High uniqueness**: Indicates complex spatial signatures
- **Low uniqueness**: Indicates common multi-step patterns
- **Educational value**: Enables multi-step spatial reasoning

### Combined Analysis
- **Objects with both types**: Enable the most sophisticated spatial reasoning
- **Objects with only 1-edge**: Enable basic pattern recognition
- **Objects with only 2-edge**: Enable intermediate multi-step reasoning
- **Objects with neither**: Require other identification methods

## Conclusion

The edge uniqueness analysis provides two complementary approaches to understanding spatial relationships in CLEVR scenes:

1. **1-Edge Analysis**: Focuses on direct object-specific patterns, enabling pattern recognition and basic spatial reasoning.

2. **2-Edge Analysis**: Focuses on multi-step path patterns, enabling complex spatial reasoning and object identification through spatial signatures.

Both approaches reveal that CLEVR scenes contain rich spatial patterns that enable sophisticated reasoning tasks, with the combination of both methods providing the most comprehensive understanding of spatial relationships.
