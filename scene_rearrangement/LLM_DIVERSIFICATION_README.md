# LLM Rearrangement Expression Diversification Pipeline

This system adds LLM-based expression diversification to the scene rearrangement generation pipeline. It creates natural, conversational variations of rearrangement instructions while maintaining the same meaning, target object, and placement instruction.

## Overview

The LLM diversification pipeline takes structured rearrangement expressions (like "Place the red cube to the left of the blue sphere") and generates multiple natural variations (like "Move the red cube so it's left of the blue sphere", "Put the red cube on the left side of the blue sphere", etc.) using large language models.

## Key Differences from Refexp LLM Diversification

While based on the same architectural principles as the referring expression LLM diversification, the rearrangement version has key adaptations:

| Aspect | Refexp Diversification | Rearrangement Diversification |
|--------|----------------------|------------------------------|
| **Input** | Identifying expressions | Action/placement instructions |
| **Focus** | Object identification | Object placement with spatial relations |
| **Action Verbs** | N/A | Place, move, put, position, set, relocate |
| **Structure** | Single expression | Paired expressions (original refexp + rearrangement) |
| **Preservation** | Object attributes + relations | Object attributes + relations + action intent |

## Technical Architecture

### Core Components

#### 1. **`llm_diversify_rearrangements.py`** - Main Diversification Engine

**Purpose**: Core LLM diversification implementation adapted for action-oriented rearrangement instructions.

**Key Classes**:
- `DiversificationConfig`: Configuration dataclass for LLM settings
- `LLMRearrangementDiversifier`: Main diversification engine

**Key Methods**:
- `_initialize_client()`: Initialize OpenAI/Anthropic clients
- `_create_diversification_prompt()`: Generate context-aware prompts for rearrangement instructions
- `_call_openai()`: OpenAI API integration with model-specific parameter handling
- `_call_anthropic()`: Anthropic API integration
- `diversify_rearrangement()`: Diversify single rearrangement expression
- `diversify_batch()`: Process multiple expression pairs with rate limiting
- `_get_scene_context()`: Extract scene context for better prompts

**Unique Features**:
- Preserves paired structure (original refexp + rearrangement)
- Context includes both identifying expression and placement instruction
- Prompt emphasizes action verbs and instruction intent
- Maintains target object, reference object, and spatial relation

#### 2. **`integrate_llm_diversification.py`** - Pipeline Integration

**Purpose**: Generate enhanced pipeline scripts and manage configuration for rearrangement expressions.

**Key Functions**:
- `load_pipeline_config()`: Load and merge configuration files
- `create_diversified_pipeline_script()`: Create `run_rearrangement_with_llm.sh`
- `create_config_template()`: Generate configuration templates
- `validate_config()`: Verify configuration completeness

**Features**:
- Configuration management specific to rearrangement pairs
- Pipeline script generation with proper file paths
- Multi-provider setup
- Error handling and validation

#### 3. **`test_llm_diversification_rearrangements.py`** - Test Suite

**Purpose**: Comprehensive testing framework for LLM diversification of rearrangement expressions.

**Key Functions**:
- `create_test_scene_data()`: Generate test scene data
- `create_test_rearrangement_pairs()`: Create diverse test rearrangement pairs
- `run_test_diversification()`: Main test runner
- `save_test_data()`: Save test data to files

**Test Coverage**:
- API connectivity and authentication
- Rearrangement expression diversification quality
- Paired structure preservation
- Error handling and edge cases
- Configuration validation
- Output format verification

### Configuration Files

#### **`rearrangement_llm_config.json`** - Main Configuration

**Structure**:
```json
{
  "llm_diversification": {
    "enabled": true,
    "providers": {
      "openai": {
        "enabled": true,
        "api_key": "your-openai-api-key-here",
        "models": ["gpt-3.5-turbo"]
      },
      "anthropic": {
        "enabled": false,
        "api_key": "your-anthropic-api-key-here",
        "models": ["claude-3-opus-20240229"]
      }
    },
    "settings": {
      "max_variations": 2,
      "temperature": 0.8,
      "max_pairs_per_run": 50,
      "delay_between_requests": 1.0
    }
  }
}
```

**Configuration Options**:
- `enabled`: Master switch for LLM diversification
- `providers`: LLM provider configurations
- `settings`: Diversification parameters
- `max_variations`: Number of variations per rearrangement (default: 2)
- `temperature`: Creativity level (0.0-1.0, default: 0.8)
- `max_pairs_per_run`: Processing limit for expression pairs (default: 50)
- `delay_between_requests`: Rate limiting delay in seconds (default: 1.0)

### Pipeline Scripts

#### **`run_rearrangement_with_llm.sh`** - Enhanced Pipeline

**Purpose**: Complete rearrangement generation pipeline with integrated LLM diversification.

**Pipeline Steps**:
1. **Base Rearrangement Generation**: Generate paired expressions (original refexp + rearrangement)
2. **LLM Diversification**: Apply LLM diversification to rearrangement instructions (if enabled)
3. **Finalization**: Organize outputs and display statistics

**Technical Implementation**:
- **Input Sources**: 
  - Scene data: `../custom_clevr/output/clevr_ref+_scenes.json`
  - Referring expressions: `../custom_clevr/output/clevr_ref+_base_refexps.json`
- **Configuration**: Reads from `rearrangement_llm_config.json` for LLM settings
- **Processing Limit**: Configurable via `max_pairs` parameter
- **Output Structure**: Maintains paired structure with diversified rearrangements

**Integration Points**:
- Reads from `rearrangement_llm_config.json`
- Uses `llm_diversify_rearrangements.py` for diversification
- Processes expression pairs from rearrangement generation
- Saves results to structured output files in `../custom_clevr/output/` directory

### Output Format Specifications

#### **Primary Output Files**

**1. `clevr_ref+_rearrangements.json`** - Base Rearrangement Pairs
- **Purpose**: Contains all original rearrangement expression pairs
- **Content**: 
  - Original referring expressions
  - Rearrangement instructions
  - Linking metadata (pair_id, scene_id)
- **Structure**: Standard paired format with `info` and `expression_pairs` sections
- **Generated**: Always created by the pipeline

**2. `clevr_ref+_rearrangements_diversified_<provider>_<model>.json`** - Diversified Pairs
- **Purpose**: Rearrangement pairs with LLM-diversified instructions
- **Content**:
  - Original referring expressions (unchanged)
  - Diversified rearrangement instructions
  - Variation metadata
  - Diversification method tracking
- **Structure**: Enhanced paired format with diversification metadata
- **Generated**: Only when LLM diversification is enabled

#### **File Structure Details**

**Base Rearrangement Pairs** (`clevr_ref+_rearrangements.json`):
```json
{
  "info": {
    "license": "Creative Commons Attribution (CC-BY 4.0)",
    "date": "10/08/2025",
    "version": "1.0",
    "description": "Scene rearrangement expressions paired with original referring expressions",
    "num_successful_pairs": 100
  },
  "expression_pairs": [
    {
      "original": {
        "refexp": "The red cube",
        "program": [...],
        "answer": 1,
        "image_filename": "CLEVR_train_000000.png",
        "image_index": 0
      },
      "rearrangement": {
        "refexp": "Place the red cube to the left of the blue sphere",
        "program": [...],
        "target_object": 1,
        "reference_object": 2,
        "target_relation": "left",
        "template_used": "place_simple.json"
      },
      "pair_id": "pair_000001",
      "scene_id": "CLEVR_train_000000"
    }
  ]
}
```

**Diversified Rearrangement Pairs** (`clevr_ref+_rearrangements_diversified_*.json`):
```json
{
  "info": {
    "license": "Creative Commons Attribution (CC-BY 4.0)",
    "date": "10/08/2025",
    "version": "1.0",
    "description": "Scene rearrangement expressions paired with original referring expressions",
    "num_successful_pairs": 100,
    "diversification": {
      "llm_provider": "openai",
      "model_name": "gpt-3.5-turbo",
      "max_variations": 2,
      "temperature": 0.8,
      "diversification_date": "2025-10-08 14:30:00"
    }
  },
  "expression_pairs": [
    {
      "original": {
        "refexp": "The red cube",
        "program": [...],
        "answer": 1,
        "image_filename": "CLEVR_train_000000.png",
        "image_index": 0
      },
      "rearrangement": {
        "refexp": "Move the red cube so it's left of the blue sphere",
        "program": [...],
        "target_object": 1,
        "reference_object": 2,
        "target_relation": "left",
        "template_used": "place_simple.json",
        "original_rearrangement_refexp": "Place the red cube to the left of the blue sphere",
        "variation_id": 1,
        "diversification_method": "openai_gpt-3.5-turbo"
      },
      "pair_id": "pair_000001",
      "scene_id": "CLEVR_train_000000",
      "diversified": true
    }
  ]
}
```

## Prompt Engineering for Rearrangement Instructions

The diversification prompt is specifically designed for action-oriented instructions:

### Prompt Structure

```
You are an expert at creating natural, conversational variations of spatial 
rearrangement instructions for visual scenes.

SCENE CONTEXT: {scene_summary}

ORIGINAL IDENTIFYING EXPRESSION: "{original_refexp}"
REARRANGEMENT INSTRUCTION: "{rearrangement_expression}"

TASK: Create {max_variations} natural, conversational variations of the 
REARRANGEMENT INSTRUCTION that:
1. Refer to the EXACT SAME object to move (the target object)
2. Refer to the EXACT SAME reference object (spatial anchor)
3. Maintain the same spatial relationship and placement instruction
4. Use different sentence structures and word choices
5. Sound natural and conversational like human instructions
6. Are grammatically correct

REQUIREMENTS:
- Keep all spatial relations accurate (left, right, front, behind, between)
- Preserve object attributes (color, shape, material)
- Use different action verbs (place, move, put, position, set, relocate)
- Vary sentence structures (imperative, instructive, directive)
- Maintain the instruction's intent (moving/placing the object)
- Make expressions sound like natural human instructions
```

### Key Prompt Features

1. **Dual Context**: Provides both the original identifying expression and the rearrangement instruction
2. **Action Emphasis**: Explicitly encourages different action verbs
3. **Spatial Accuracy**: Emphasizes preserving spatial relationships
4. **Instruction Intent**: Focuses on maintaining the action/placement goal
5. **Conversational Tone**: Encourages natural, human-like instructions

## Quick Start Guide

### 1. Setup and Configuration

```bash
# Navigate to scene_rearrangement directory
cd scene_rearrangement

# Install required packages (if not already installed)
pip install openai anthropic

# Configure API keys in rearrangement_llm_config.json
# Set enabled: true and add your API keys
```

### 2. Test the System

```bash
# Run simple test with 3 expression pairs
python test_llm_diversification_rearrangements.py --api_key YOUR_API_KEY

# Or use existing test data
python test_llm_diversification_rearrangements.py \
    --api_key YOUR_API_KEY \
    --use-existing-data
```

### 3. Run Full Pipeline

First, generate the enhanced pipeline script:

```bash
# Generate the pipeline script with your configuration
python integrate_llm_diversification.py \
    --config rearrangement_llm_config.json \
    --output-script run_rearrangement_with_llm.sh
```

Then run the pipeline:

```bash
# Run complete pipeline with LLM diversification
./run_rearrangement_with_llm.sh
```

**Pipeline Output**:
- **Always Generated**: `../custom_clevr/output/clevr_ref+_rearrangements.json` (base pairs)
- **If LLM Enabled**: `../custom_clevr/output/clevr_ref+_rearrangements_diversified_*.json` (diversified)

## Usage Examples

### Basic Diversification

```python
from llm_diversify_rearrangements import (
    DiversificationConfig, LLMRearrangementDiversifier
)

# Create configuration
config = DiversificationConfig(
    llm_provider='openai',
    model_name='gpt-3.5-turbo',
    api_key='your-api-key',
    max_variations=2,
    temperature=0.8
)

# Initialize diversifier
diversifier = LLMRearrangementDiversifier(config)

# Diversify rearrangement expression
variations = diversifier.diversify_rearrangement(
    rearrangement_expression="Place the red cube to the left of the blue sphere",
    original_refexp="The red cube",
    scene_context=scene_data
)

# Results:
# - "Move the red cube so it's left of the blue sphere"
# - "Put the red cube on the left side of the blue sphere"
```

### Batch Processing

```python
# Process multiple expression pairs
diversified_pairs = diversifier.diversify_batch(
    expression_pairs, 
    scene_data
)

# Each pair now has diversified rearrangement instructions
for pair in diversified_pairs:
    print(f"Original: {pair['rearrangement']['original_rearrangement_refexp']}")
    print(f"Diversified: {pair['rearrangement']['refexp']}")
    print(f"Variation ID: {pair['rearrangement']['variation_id']}")
```

## Command-Line Usage

### Diversify Existing Rearrangement Pairs

```bash
python llm_diversify_rearrangements.py \
    --rearrangements_file ../custom_clevr/output/clevr_ref+_rearrangements.json \
    --scenes_file ../custom_clevr/output/clevr_ref+_scenes.json \
    --output_file ../custom_clevr/output/clevr_ref+_rearrangements_diversified.json \
    --llm_provider openai \
    --model_name gpt-3.5-turbo \
    --api_key YOUR_API_KEY \
    --max_variations 2 \
    --temperature 0.8 \
    --max_pairs 50 \
    --delay 1.0
```

### Generate Enhanced Pipeline Script

```bash
# Create configuration template
python integrate_llm_diversification.py --create-config

# Generate pipeline script from configuration
python integrate_llm_diversification.py \
    --config rearrangement_llm_config.json \
    --output-script run_rearrangement_with_llm.sh

# Validate configuration only
python integrate_llm_diversification.py \
    --config rearrangement_llm_config.json \
    --validate-only
```

## Performance Metrics

### Typical Performance (50 expression pairs, 2 variations each):
- **Processing Time**: ~2-3 minutes
- **API Calls**: 50 requests
- **Rate Limiting**: Default 1.0 second delays
- **Success Rate**: ~95-100% (with proper API configuration)
- **Total Outputs**: 100 diversified pairs (2 variations × 50 original pairs)

### Expected Quality:
- **Meaning Preservation**: High (maintains object identity and spatial relations)
- **Linguistic Diversity**: Varied action verbs and sentence structures
- **Naturalness**: Conversational, instruction-like tone
- **Spatial Accuracy**: Preserved spatial relationships

## Example Diversifications

### Example 1: Simple Placement

**Original Identifying Expression**: "The red cube"
**Original Rearrangement**: "Place the red cube to the left of the blue sphere"

**Diversified Variations**:
1. "Move the red cube so it's left of the blue sphere"
2. "Put the red cube on the left side of the blue sphere"

### Example 2: Material-Based Instruction

**Original Identifying Expression**: "The metal cylinder"
**Original Rearrangement**: "Move the metal cylinder behind the green cube"

**Diversified Variations**:
1. "Place the metal cylinder behind the green cube"
2. "Position the cylinder at the back of the green cube"

### Example 3: Complex Spatial Relation

**Original Identifying Expression**: "The large yellow sphere"
**Original Rearrangement**: "Put the yellow sphere to the right of the small blue cube"

**Diversified Variations**:
1. "Move the yellow sphere so it's on the right of the blue cube"
2. "Position the large yellow sphere right of the small blue cube"

## Troubleshooting

### Common Issues

**1. API Key Errors**
```bash
# Error: Invalid API key
# Solution: Check your API key in rearrangement_llm_config.json
```

**2. File Not Found**
```bash
# Error: Cannot find scenes or rearrangements file
# Solution: Make sure you've run the base rearrangement generation first
./run_rearrangement_generation.sh
```

**3. Rate Limiting**
```bash
# Error: Rate limit exceeded
# Solution: Increase delay_between_requests in config
# Set "delay_between_requests": 2.0 or higher
```

### Debug Mode

```bash
# Enable verbose logging for troubleshooting
python llm_diversify_rearrangements.py \
    --rearrangements_file test_data/test_rearrangement_pairs.json \
    --scenes_file test_data/test_scenes.json \
    --output_file test_output.json \
    --llm_provider openai \
    --model_name gpt-3.5-turbo \
    --api_key YOUR_API_KEY \
    --max_pairs 5 \
    --delay 0.5
```

## Comparison with Refexp LLM Diversification

| Feature | Refexp Diversification | Rearrangement Diversification |
|---------|------------------------|------------------------------|
| **Input Type** | Single expressions | Paired expressions |
| **Output Preservation** | Object identification | Object + placement instruction |
| **Action Verbs** | None | place, move, put, position, etc. |
| **Spatial Relations** | Preserved | Preserved + emphasized |
| **Instruction Intent** | N/A | Maintained (moving/placing) |
| **Context** | Scene objects | Scene + original refexp + rearrangement |
| **Use Case** | Object identification | Spatial manipulation tasks |

## Extension Points

The rearrangement LLM diversification system can be extended:

### 1. Additional Action Verbs

Expand the prompt to include more action verbs:
- "relocate", "shift", "transfer", "arrange", "situate"

### 2. Enhanced Evaluation

Create evaluation metrics specific to rearrangement instructions:
- Action verb diversity
- Instruction clarity
- Spatial relation accuracy
- Target object preservation
- Reference object preservation

### 3. Multi-Step Instructions

Extend to handle complex, multi-step rearrangements:
- "Move A to the left of B, then place C behind A"

### 4. Conditional Instructions

Add conditional placement instructions:
- "If there's space, place the red cube to the left of the blue sphere"

## Contributing

To extend the LLM diversification system for rearrangements:

1. **Add New Providers**: Extend `LLMRearrangementDiversifier` class
2. **Improve Prompts**: Modify `_create_diversification_prompt()` for better instruction variations
3. **Add Tests**: Extend test suite with new rearrangement scenarios
4. **Create Evaluation**: Build evaluation metrics for instruction quality
5. **Update Documentation**: Keep this README current with changes

## Related Documentation

- **Scene Rearrangement README**: `scene_rearrangement/README.md`
- **Scene Rearrangement Pipeline**: `custom_clevr/docs/SCENE_REARRANGEMENT_PIPELINE.md`
- **Refexp LLM Diversification**: `custom_clevr/docs/LLM_DIVERSIFICATION_README.md`
- **Implementation Summary**: `scene_rearrangement/IMPLEMENTATION_SUMMARY.md`


