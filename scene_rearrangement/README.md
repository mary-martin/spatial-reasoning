# Scene Rearrangement Expression Generation

This directory contains the scene rearrangement expression generation system that creates paired expressions for spatial reasoning tasks.

## Overview

The scene rearrangement system takes existing referring expressions and generates corresponding "rearrangement" expressions that specify where to place the referenced object. Each pair consists of:

1. **Original Expression**: "The red cube" (identifies an object)
2. **Rearrangement Expression**: "Place the red cube to the left of the green sphere" (specifies new position)

## Key Features

- **Paired Generation**: Each rearrangement expression is linked to its original referring expression
- **Non-existing Relations**: Ensures the target relation doesn't already exist in the scene
- **Template-based**: Uses the same template system as refexp generation
- **Linking System**: Maintains connections between original and rearrangement expressions

## Files

- `generate_rearrangement_expressions.py`: Main generation script
- `rearrangement_engine.py`: Core logic for generating rearrangement expressions
- `rearrangement_templates/`: Template definitions for rearrangement expressions
- `metadata.json`: Metadata for rearrangement functions
- `synonyms.json`: Synonym definitions (shared with refexp generation)

## Usage

```bash
python generate_rearrangement_expressions.py \
    --input_refexps_file ../custom_clevr/output/clevr_ref+_base_refexps.json \
    --input_scenes_file ../custom_clevr/output/clevr_ref+_scenes.json \
    --output_rearrangement_file ../custom_clevr/output/clevr_ref+_rearrangements.json
```

## Template Structure

Rearrangement templates follow the same structure as referring expression templates but focus on placement instructions:

```json
{
  "text": [
    "Place the <C> <S> to the <R> of the <C2> <S2>",
    "Move the <C> <S> to the <R> of the <C2> <S2>"
  ],
  "nodes": [...],
  "params": [...],
  "constraints": [...]
}
```

## Output Format

The output includes both original and rearrangement expressions with linking information:

```json
{
  "info": {...},
  "expression_pairs": [
    {
      "original": {
        "refexp": "The red cube",
        "program": [...],
        "answer": 1
      },
      "rearrangement": {
        "refexp": "Place the red cube to the left of the green sphere",
        "program": [...],
        "target_relation": "left",
        "target_object": 2
      },
      "pair_id": "pair_001",
      "scene_id": "CLEVR_train_000000"
    }
  ]
}
```

