#!/bin/bash

# Script to run scene rearrangement expression generation
# This script generates rearrangement expressions from existing referring expressions

echo "Scene Rearrangement Expression Generation"
echo "========================================"

# Set default parameters
INPUT_REFEXPS="../custom_clevr/output/clevr_ref+_base_refexps.json"
INPUT_SCENES="../custom_clevr/output/clevr_ref+_scenes.json"
OUTPUT_FILE="../custom_clevr/output/clevr_ref+_rearrangements.json"
NUM_REFEXPS=100  # Process first 100 referring expressions for testing
VERBOSE="--verbose"

# Check if input files exist
if [ ! -f "$INPUT_REFEXPS" ]; then
    echo "ERROR: Input referring expressions file not found: $INPUT_REFEXPS"
    echo "Please make sure the refexp generation has been run first."
    exit 1
fi

if [ ! -f "$INPUT_SCENES" ]; then
    echo "ERROR: Input scenes file not found: $INPUT_SCENES"
    echo "Please make sure the scene data is available."
    exit 1
fi

echo "Input referring expressions: $INPUT_REFEXPS"
echo "Input scenes: $INPUT_SCENES"
echo "Output file: $OUTPUT_FILE"
echo "Number of referring expressions to process: $NUM_REFEXPS"
echo ""

# Run the generation
echo "Starting rearrangement expression generation..."
python generate_rearrangement_expressions.py \
    --input_refexps_file "$INPUT_REFEXPS" \
    --input_scenes_file "$INPUT_SCENES" \
    --output_rearrangement_file "$OUTPUT_FILE" \
    --num_refexps "$NUM_REFEXPS" \
    --rearrangements_per_refexp 1 \
    --max_attempts 50 \
    $VERBOSE

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Rearrangement expression generation completed successfully!"
    echo "Output saved to: $OUTPUT_FILE"
    
    # Show some statistics
    if [ -f "$OUTPUT_FILE" ]; then
        echo ""
        echo "Output file statistics:"
        python -c "
import json
with open('$OUTPUT_FILE', 'r') as f:
    data = json.load(f)
    print(f'  - Total expression pairs: {len(data[\"expression_pairs\"])}')
    print(f'  - Original referring expressions processed: {data[\"info\"][\"num_original_refexps\"]}')
    print(f'  - Successful pairs generated: {data[\"info\"][\"num_successful_pairs\"]}')
    if data['expression_pairs']:
        print(f'  - Success rate: {data[\"info\"][\"num_successful_pairs\"] / data[\"info\"][\"num_original_refexps\"] * 100:.1f}%')
"
    fi
else
    echo ""
    echo "✗ Rearrangement expression generation failed!"
    exit 1
fi

