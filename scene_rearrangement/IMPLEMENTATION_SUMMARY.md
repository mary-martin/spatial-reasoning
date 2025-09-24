# Scene Rearrangement Expression Generation - Implementation Summary

## Overview

I have successfully implemented a scene rearrangement expression generation system that creates paired expressions for spatial reasoning tasks. The system takes existing referring expressions and generates corresponding "rearrangement" expressions that specify where to place the referenced objects.

## Key Features Implemented

### 1. **Paired Expression Generation**
- **Original Expression**: Identifies an object (e.g., "The red cube")
- **Rearrangement Expression**: Specifies new position (e.g., "Place the red cube to the left of the green sphere")
- **Linking System**: Each pair is linked with unique IDs and metadata

### 2. **Non-existing Relations Constraint**
- Ensures the target relation doesn't already exist in the scene
- Uses `check_relation_exists_handler` to validate placement options
- Only generates rearrangements for valid, non-existing spatial relations

### 3. **Template-based Generation**
- Uses the same template system as refexp generation
- Three template types implemented:
  - `place_simple.json`: Basic color/shape placement
  - `place_with_material.json`: Includes material properties
  - `place_relation_check.json`: Includes relation existence checking

### 4. **Comprehensive Linking System**
- Each expression pair has a unique `pair_id`
- Links original and rearrangement expressions with metadata
- Tracks generation information (template used, target objects, relations)

## File Structure

```
scene_rearrangement/
├── README.md                           # Main documentation
├── IMPLEMENTATION_SUMMARY.md          # This summary
├── metadata.json                      # Function and type definitions
├── synonyms.json                      # Synonym mappings
├── rearrangement_engine.py            # Core rearrangement logic
├── generate_rearrangement_expressions.py  # Main generation script
├── test_rearrangement_system.py       # Test suite
├── run_rearrangement_generation.sh    # Execution script
└── rearrangement_templates/           # Template definitions
    ├── place_simple.json
    ├── place_with_material.json
    └── place_relation_check.json
```

## Technical Implementation

### Core Components

1. **Rearrangement Engine** (`rearrangement_engine.py`)
   - Extends refexp engine with rearrangement-specific handlers
   - `place_relation_handler`: Validates placement instructions
   - `check_relation_exists_handler`: Checks if relations already exist
   - `find_valid_placement_options`: Finds valid placement relations

2. **Template System**
   - Follows same structure as refexp templates
   - Parameters: `<C>`, `<S>`, `<M>`, `<R>` for Color, Shape, Material, Relation
   - Constraints ensure different objects and non-existing relations

3. **Generation Pipeline**
   - Loads existing referring expressions
   - Extracts target objects from expressions
   - Finds valid placement relations
   - Instantiates templates with specific parameters
   - Validates and links expressions

### Key Functions

- `extract_object_from_refexp()`: Extracts target object from referring expressions
- `find_valid_placement_relations()`: Finds valid placement options
- `instantiate_rearrangement_template()`: Instantiates templates with parameters
- `generate_rearrangement_for_refexp()`: Main generation function

## Output Format

The system generates JSON output with the following structure:

```json
{
  "info": {
    "description": "Scene rearrangement expressions paired with original referring expressions",
    "num_original_refexps": 5,
    "num_successful_pairs": 5,
    "templates_used": ["place_simple.json", "place_with_material.json"]
  },
  "expression_pairs": [
    {
      "original": {
        "refexp": "The red cube",
        "program": [...],
        "image_filename": "CLEVR_train_000000.png"
      },
      "rearrangement": {
        "refexp": "Place the red cube to the left of the green sphere",
        "program": [...],
        "target_object": 1,
        "reference_object": 2,
        "target_relation": "left"
      },
      "pair_id": "pair_000001",
      "scene_id": "CLEVR_train_000000",
      "generation_info": {
        "template_used": "place_simple.json",
        "target_object": 1,
        "reference_object": 2,
        "target_relation": "left"
      }
    }
  ]
}
```

## Testing Results

The system has been tested and verified to work correctly:

- ✅ All required files exist and load properly
- ✅ Template structure is valid
- ✅ Rearrangement engine functions correctly
- ✅ Successfully generates paired expressions
- ✅ Validates non-existing relations constraint
- ✅ Links original and rearrangement expressions

## Usage

### Basic Usage
```bash
cd scene_rearrangement
python generate_rearrangement_expressions.py \
    --input_refexps_file ../custom_clevr/output/clevr_ref+_base_refexps.json \
    --input_scenes_file ../custom_clevr/output/clevr_ref+_scenes.json \
    --output_rearrangement_file ../custom_clevr/output/clevr_ref+_rearrangements.json \
    --num_refexps 100
```

### Using the Shell Script
```bash
cd scene_rearrangement
./run_rearrangement_generation.sh
```

### Testing
```bash
cd scene_rearrangement
python test_rearrangement_system.py
```

## Key Achievements

1. **Successfully implemented** a complete scene rearrangement expression generation system
2. **Maintained compatibility** with the existing refexp generation framework
3. **Ensured constraint satisfaction** by only generating non-existing relations
4. **Created comprehensive linking** between original and rearrangement expressions
5. **Provided template-based generation** following the same patterns as refexp generation
6. **Delivered working system** with test suite and documentation

## Future Enhancements

Potential improvements for the system:

1. **Additional Template Types**: More complex spatial relations, multi-object placements
2. **Constraint Validation**: More sophisticated constraint checking
3. **Performance Optimization**: Batch processing, parallel generation
4. **Evaluation Metrics**: Success rate analysis, quality metrics
5. **Integration**: Direct integration with the main refexp generation pipeline

The system is now ready for use and can generate paired expressions for spatial reasoning tasks as requested.

