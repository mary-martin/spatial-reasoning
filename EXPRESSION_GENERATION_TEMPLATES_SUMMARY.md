# CLEVR-Ref+ Expression Generation Templates Summary

## Overview
This document provides a comprehensive overview of all expression generation templates and types available in the CLEVR-Ref+ dataset. The system supports 8 different template categories that generate various types of referring expressions.

## Template Categories

### 1. **Zero-Hop Templates** (`zero_hop.json`)
**Purpose**: Generate expressions that directly describe objects without spatial relationships.

**Structure**:
- **Template**: `<rORD_NUM> <VIS> <Z> <C> <M> <S>(s) <ORD_DIR>`
- **Example**: "the first one of the fully visible large red metal cube from left"

**Parameters**:
- `<Z>`: Size (small, large)
- `<C>`: Color (gray, red, blue, green, brown, purple, cyan, yellow)
- `<M>`: Material (rubber, metal)
- `<S>`: Shape (cube, sphere, cylinder)
- `<rORD_NUM>`: Ordinal number (the first one of the, the second one of the, etc.)
- `<ORD_DIR>`: Ordinal direction (from left, from right, from front)
- `<VIS>`: Visibility (fully visible, partially visible)

**Node Type**: `filter_count`

---

### 2. **One-Hop Templates** (`one_hop.json`)
**Purpose**: Generate expressions that describe objects in relation to another object through a single spatial relationship.

**Structure**:
- **Template**: `<rORD_NUM2> <VIS2> <Z2> <C2> <M2> <S2>(s) <ORD_DIR2> that are <R> <rORD_NUM> <VIS> <Z> <C> <M> <S>(s) <ORD_DIR>`
- **Example**: "the first one of the fully visible large red metal cube from left that are left the second one of the fully visible small blue rubber sphere from front"

**Parameters**:
- All parameters from zero-hop for both objects
- `<R>`: Relation (left, right, behind, front)

**Node Types**: `filter_unique` → `relate_filter_count`

---

### 3. **Two-Hop Templates** (`two_hop.json`)
**Purpose**: Generate expressions that describe objects through a chain of two spatial relationships.

**Structure**:
- **Template**: `<rORD_NUM3> <VIS3> <Z3> <C3> <M3> <S3>(s) <ORD_DIR3> that are <R2> the <ORD_NUM2> <VIS2> <Z2> <C2> <M2> <S2> <ORD_DIR2> that is <R> the <rORD_NUM> <VIS> <Z> <C> <M> <S>(s) <ORD_DIR>`
- **Example**: "the first one of the fully visible large red metal cube from left that are left the second one of the fully visible small blue rubber sphere from front that is behind the third one of the fully visible large green metal cylinder from right"

**Parameters**:
- All parameters from zero-hop for all three objects
- `<R>`, `<R2>`: Relations (left, right, behind, front)

**Node Types**: `filter_unique` → `relate_filter_unique` → `relate_filter_count`

---

### 4. **Three-Hop Templates** (`three_hop.json`)
**Purpose**: Generate expressions that describe objects through a chain of three spatial relationships.

**Structure**:
- **Template**: `<rORD_NUM4> <VIS4> <Z4> <C4> <M4> <S4>(s) <ORD_DIR4> that are <R3> the <ORD_NUM3> <VIS3> <Z3> <C3> <M3> <S3> <ORD_DIR3> that is <R2> the <ORD_NUM2> <VIS2> <Z2> <C2> <M2> <S2> <ORD_DIR2> that is <R> the <rORD_NUM> <VIS> <Z> <C> <M> <S>(s) <ORD_DIR>`

**Parameters**:
- All parameters from zero-hop for all four objects
- `<R>`, `<R2>`, `<R3>`: Relations (left, right, behind, front)

**Node Types**: `filter_unique` → `relate_filter_unique` → `relate_filter_unique` → `relate_filter_count`

---

### 5. **Single AND Templates** (`single_and.json`)
**Purpose**: Generate expressions that describe objects that satisfy multiple spatial relationships simultaneously.

**Structure**:
- **Template**: `<rORD_NUM3> <VIS3> <Z3> <C3> <M3> <S3>(s) <ORD_DIR3> that are [both] <R2> the <rORD_NUM2> <VIS2> <Z2> <C2> <M2> <S2>(s) <ORD_DIR2> and <R> the <rORD_NUM> <VIS> <Z> <C> <M> <S>(s) <ORD_DIR>`
- **Example**: "the first one of the fully visible large red metal cube from left that are [both] left the second one of the fully visible small blue rubber sphere from front and behind the third one of the fully visible large green metal cylinder from right"

**Parameters**:
- All parameters from zero-hop for all three objects
- `<R>`, `<R2>`: Relations (left, right, behind, front)

**Node Types**: `filter_unique` → `relate` → `filter_unique` → `relate` → `intersect` → `filter_count`

---

### 6. **Single OR Templates** (`single_or.json`)
**Purpose**: Generate expressions that describe objects that satisfy either of two different descriptions.

**Structure**:
- **Template**: "things that are [either] <rORD_NUM> <VIS> <Z> <C> <M> <S>(s) <ORD_DIR> or <rORD_NUM2> <VIS2> <Z2> <C2> <M2> <S2>(s) <ORD_DIR2>"
- **Example**: "things that are [either] the first one of the fully visible large red metal cube from left or the second one of the fully visible small blue rubber sphere from front"

**Parameters**:
- All parameters from zero-hop for both objects

**Node Types**: `filter` → `filter` → `union` → `count`

---

### 7. **Same Relate Templates** (`same_relate.json`)
**Purpose**: Generate expressions that describe objects sharing the same attributes as a reference object.

**Structure**:
- **Template**: "any other things that have the same <ATTRIBUTE> as the <rORD_NUM> <VIS> <Z> <C> <M> <S>(s) <ORD_DIR>"
- **Example**: "any other things that have the same color as the first one of the fully visible large red metal cube from left"

**Parameters**:
- All parameters from zero-hop for the reference object
- `<ATTRIBUTE>`: Size, Color, Material, or Shape

**Node Types**: `filter_unique` → `same_<attribute>` → `count`

**Supported Attributes**:
- `same_size`: Objects with the same size
- `same_color`: Objects with the same color
- `same_material`: Objects with the same material
- `same_shape`: Objects with the same shape

---

### 8. **Between Templates** (`between.json`) ⭐ **NEW**
**Purpose**: Generate expressions that describe objects positioned between two other objects.

**Structure**:
- **Template**: "The <C> <S> between the <C2> <S2> and the <C3> <S3>"
- **Example**: "The blue cube between the red sphere and the green cylinder"

**Parameters**:
- `<C>`, `<S>`: Color and Shape of the target object
- `<C2>`, `<S2>`: Color and Shape of the first reference object
- `<C3>`, `<S3>`: Color and Shape of the second reference object

**Node Type**: `filter_between_unique`

**Text Variations**:
- "The <C> <S> between the <C2> <S2> and the <C3> <S3>"
- "Find the <C> <S> that is between the <C2> <S2> and the <C3> <S3>"
- "Look at the <C> <S> between the <C2> <S2> and the <C3> <S3>"

---

## Data Types and Values

### **Object Properties**
| Type | Values |
|------|--------|
| **Color** | gray, red, blue, green, brown, purple, cyan, yellow |
| **Shape** | cube, sphere, cylinder |
| **Size** | small, large |
| **Material** | rubber, metal |
| **Visibility** | fully visible, partially visible |

### **Spatial Relations**
| Relation | Description |
|----------|-------------|
| **left** | Object is to the left of another object |
| **right** | Object is to the right of another object |
| **front** | Object is in front of another object |
| **behind** | Object is behind another object |

### **Ordinal Numbers**
- "the first one of the"
- "the second one of the"
- "the third one of the"
- "the fourth one of the"
- "the fifth one of the"
- "the sixth one of the"
- "the seventh one of the"
- "the eighth one of the"
- "the nineth one of the"

### **Ordinal Directions**
- "from left"
- "from right"
- "from front"

---

## Template Complexity Levels

### **Simple Templates**
- **Zero-Hop**: Direct object description
- **Same Relate**: Attribute-based similarity

### **Single Relationship Templates**
- **One-Hop**: One spatial relationship
- **Between**: Positioned between two objects

### **Complex Templates**
- **Two-Hop**: Chain of two relationships
- **Three-Hop**: Chain of three relationships
- **Single AND**: Multiple simultaneous relationships
- **Single OR**: Alternative descriptions

---

## Generation Pipeline

### **Template Processing Flow**
1. **Template Selection**: Choose appropriate template based on complexity
2. **Parameter Instantiation**: Fill in object properties and relationships
3. **Scene Validation**: Ensure the described objects exist in the scene
4. **Expression Generation**: Create natural language referring expressions
5. **Output**: Generate JSON with expressions and target object indices

### **Special Handling**
- **Between Expressions**: Generated separately and merged with main pipeline
- **Unique Objects**: Templates ensure single object identification
- **Count Expressions**: Return number of objects matching description
- **Existence Expressions**: Return boolean for object existence

---

## Usage Examples

### **Zero-Hop Example**
```
Input: Scene with multiple objects
Template: "the first one of the fully visible large red metal cube from left"
Output: Refers to the first large red metal cube from the left
```

### **One-Hop Example**
```
Input: Scene with spatial relationships
Template: "the small blue sphere that is left of the large red cube"
Output: Refers to the small blue sphere positioned to the left of the large red cube
```

### **Between Example**
```
Input: Scene with "between" metadata
Template: "The blue cube between the red sphere and the green cylinder"
Output: Refers to the blue cube positioned between the red sphere and green cylinder
```

---

## Integration Notes

### **Pipeline Integration**
- All templates are processed by `generate_refexp.py`
- Between expressions are generated by `generate_between_expressions.py`
- Results are merged by `merge_refex_outputs.py`
- Orchestrated by `generate_refex.sh`

### **Metadata Requirements**
- Scene JSON files must include spatial relationship metadata
- "Between" relationships must be pre-computed in scene data
- Camera parameters needed for accurate spatial calculations

### **Output Format**
```json
{
  "refexp": "The blue cube between the red sphere and the green cylinder",
  "target_idx": 2,
  "target_array_idx": 2,
  "between_pair": [0, 1]
}
```

This comprehensive template system enables the generation of diverse and complex referring expressions for CLEVR-Ref+ scenes, supporting both simple object descriptions and sophisticated spatial reasoning patterns.
