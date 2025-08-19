# Node-Specific 2-Edge Paths Analysis: Incoming Approach

## Overview

This document summarizes the **incoming analysis** of unique 2-edge paths that considers **individual label combinations per ending node**, rather than starting node. This approach reveals that **unique spatial signatures exist** when analyzing paths that END at specific nodes.

## Key Analysis

### **Previous Analysis (Outgoing)**
- Checked uniqueness for paths STARTING from each node
- Found **7 unique combinations** out of 76 total paths
- Analyzed outgoing relationships from each node

### **Current Analysis (Incoming)**
- Checks uniqueness for paths ENDING at each node
- Found **7 unique combinations** out of 76 total paths
- Analyzes incoming relationships to each node

## Results Summary

### **Graph Structure**
- **6 nodes** (objects) with **30 edges** (spatial relationships)
- **4 individual labels**: `front`, `behind`, `left`, `right`
- **76 total individual label paths** analyzed per ending node

### **Key Finding: Unique Incoming Combinations Found!**
- **7 unique incoming combinations** found across all ending nodes
- **69 non-unique incoming combinations** (appear multiple times per ending node)
- **9.2% uniqueness rate** (7 out of 76 combinations are unique)

### **Unique Incoming Combinations Per Ending Node**

| Ending Node | Object | Unique Combinations | Examples |
|-------------|--------|-------------------|----------|
| **0** | blue cube | **1** | `('left', 'left')` → brown sphere → cyan cube → blue cube |
| **1** | green cylinder | **1** | `('front', 'front')` → blue cube → brown sphere → green cylinder |
| **2** | cyan cube | **2** | `('behind', 'behind')` → gray cube → brown cylinder → cyan cube<br>`('front', 'left')` → blue cube → brown sphere → cyan cube |
| **3** | brown cylinder | **1** | `('right', 'behind')` → green cylinder → gray cube → brown cylinder |
| **4** | gray cube | **1** | `('right', 'right')` → green cylinder → brown cylinder → gray cube |
| **5** | brown sphere | **1** | `('left', 'front')` → cyan cube → blue cube → brown sphere |

## Analysis Breakdown

### **Individual Label Distribution**
- **`front`**: Appears in many relationships
- **`behind`**: Appears in many relationships  
- **`left`**: Appears in many relationships
- **`right`**: Appears in many relationships

### **Pattern Recognition**
1. **Ending-Node-Specific Uniqueness**: Each ending node has different unique patterns
2. **Direction Consistency**: Some unique patterns involve same direction twice (e.g., `('left', 'left')`, `('right', 'right')`)
3. **Direction Changes**: Other unique patterns involve direction changes (e.g., `('front', 'left')`, `('right', 'behind')`)
4. **Spatial Signatures**: Each ending node has distinctive incoming spatial relationship patterns

## Comparison: Outgoing vs Incoming

| Metric | Outgoing Analysis | Incoming Analysis | Change |
|--------|------------------|------------------|---------|
| **Total Paths** | 76 | 76 | 0% |
| **Unique Combinations** | 7 | 7 | 0% |
| **Non-Unique Combinations** | 69 | 69 | 0% |
| **Uniqueness Rate** | 9.2% | 9.2% | 0% |

**Key Insight**: Both outgoing and incoming analyses find the same number of unique combinations, but they represent different spatial patterns!

## Implications

### **Spatial Reasoning**
- **Unique incoming spatial signatures exist** when considered per ending node
- **Different ending objects have different unique incoming patterns**
- **Incoming analysis reveals distinctive spatial configurations**
- **Individual labels CAN provide uniqueness** for incoming paths

### **Graph Analysis**
- **Incoming connectivity** reveals unique patterns
- **Spatial signatures** exist at the ending node level
- **Predictable patterns** with ending-node-specific variations
- **Context-dependent uniqueness** in incoming spatial relationships

### **Machine Learning**
- **Feature engineering**: Ending-node-specific patterns provide distinctive features
- **Pattern recognition**: Incoming spatial configurations are learnable
- **Context awareness**: Ending point matters for spatial uniqueness
- **Spatial signatures**: Individual labels can be distinctive per ending node

## Technical Implementation

### **Algorithm Changes**
```python
# Previous: Check uniqueness for paths STARTING from each node
for start_node in G.nodes():
    for neighbor in G.neighbors(start_node):
        # ... outgoing analysis ...

# Current: Check uniqueness for paths ENDING at each node
for end_node in G.nodes():
    for first_node in G.predecessors(end_node):
        for second_node in G.predecessors(first_node):
            # ... incoming analysis ...
```

### **Key Functions**
- `G.predecessors(node)`: Find nodes that have edges TO the given node
- `defaultdict(lambda: defaultdict(list))`: Nested structure for ending-node-specific combinations
- `itertools.product()`: Generates all individual label combinations
- `Counter()`: Counts occurrences per ending node
- `defaultdict(list)`: Groups unique combinations by ending node

## Visualization Features

### **`node_specific_2edge_analysis.png`** (Comprehensive)
A comprehensive 3x3 subplot visualization showing:

1. **Full Scene Graph** - All spatial relationships with arrows
2. **Object Positions** - 2D spatial layout with camera
3. **Unique Incoming Combinations per Ending Node** - Bar chart showing unique counts per ending node
4. **Non-Unique Incoming Combinations per Ending Node** - Bar chart showing non-unique counts per ending node
5. **Incoming Path Statistics** - Pie chart of unique vs non-unique incoming paths
6. **Individual Label Distribution** - Frequency of each label
7. **Example Unique Incoming Paths per Node** - Sample unique combinations for each ending node
8. **Comparison** - Outgoing vs incoming analysis
9. **Summary Statistics** - Complete incoming analysis stats

### **`focused_node_specific_analysis.png`** (Focused)
A focused 1x2 subplot visualization highlighting:

1. **Key Finding** - "UNIQUE INCOMING COMBINATIONS FOUND!" with detailed explanation
2. **Unique Incoming Combinations per Ending Node** - Horizontal bar chart showing unique counts per ending node

## Key Insights

### **1. Ending-Node-Specific Uniqueness Exists**
- **7 unique incoming combinations** found across all ending nodes
- **Each ending node has different unique incoming patterns**
- **Individual labels CAN provide uniqueness** for incoming paths

### **2. Context Matters**
- **Ending point determines uniqueness**
- **Same combination can be unique for one ending node, common for another**
- **Incoming spatial signatures are context-dependent**

### **3. Spatial Pattern Diversity**
- **Different ending objects have different unique incoming spatial configurations**
- **Some patterns involve direction consistency** (e.g., `('left', 'left')`, `('right', 'right')`)
- **Others involve direction changes** (e.g., `('front', 'left')`, `('right', 'behind')`)

### **4. Practical Applications**
- **Object identification**: Use ending-node-specific unique incoming patterns
- **Spatial reasoning**: Consider ending point context
- **Graph analysis**: Focus on incoming connectivity patterns
- **Machine learning**: Extract ending-node-specific spatial features

## Conclusion

The incoming analysis reveals that:

1. **Unique incoming spatial signatures DO exist** when analyzed per ending node
2. **Individual labels CAN provide uniqueness** for incoming paths
3. **Different ending objects have different unique incoming spatial patterns**
4. **Context (ending node) is crucial** for incoming spatial uniqueness
5. **9.2% of incoming combinations are unique** when considered per ending node

This incoming approach provides valuable insights for:
- **Spatial reasoning systems**
- **Object identification algorithms**
- **Graph-based spatial analysis**
- **Machine learning feature engineering**

The key lesson is that **incoming spatial uniqueness is context-dependent** and requires considering the **ending point** when analyzing spatial relationship patterns.

## Comparison with Outgoing Analysis

Both outgoing and incoming analyses find the same number of unique combinations (7), but they represent fundamentally different spatial patterns:

- **Outgoing**: "What unique paths start from each object?"
- **Incoming**: "What unique paths end at each object?"

This dual perspective provides a complete picture of spatial uniqueness in the scene graph.
