#!/usr/bin/env python3
"""
LLM-based Rearrangement Expression Diversification Pipeline

This script takes generated rearrangement expressions and uses LLMs to create more diverse,
natural, conversational variations while maintaining the same meaning and placement instruction.

Requirements:
- Keep the same meaning, target object, and placement instruction
- Use natural, conversational language
- Vary sentence structure and word choice
- Maintain spatial accuracy
- Generate 3-5 variations per expression

Supported LLMs:
- GPT-4, GPT-5 (OpenAI)
- Claude (Anthropic)
"""

import json
import argparse
import os
import time
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DiversificationConfig:
    """Configuration for LLM diversification"""
    llm_provider: str  # 'openai', 'anthropic'
    model_name: str    # 'gpt-4', 'gpt-5', 'claude-3-opus', etc.
    api_key: str
    max_variations: int = 4
    temperature: float = 0.8
    max_tokens: int = 150
    batch_size: int = 10
    delay_between_requests: float = 1.0

class LLMRearrangementDiversifier:
    """Main class for diversifying rearrangement expressions using LLMs"""
    
    def __init__(self, config: DiversificationConfig):
        self.config = config
        self.client = self._initialize_client()
        
    def _initialize_client(self):
        """Initialize the appropriate LLM client based on provider"""
        if self.config.llm_provider == 'openai':
            try:
                from openai import OpenAI
                return OpenAI(api_key=self.config.api_key)
            except ImportError:
                raise ImportError("Please install openai: pip install openai")
                
        elif self.config.llm_provider == 'anthropic':
            try:
                import anthropic
                return anthropic.Anthropic(api_key=self.config.api_key)
            except ImportError:
                raise ImportError("Please install anthropic: pip install anthropic")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.llm_provider}")
    
    def _create_diversification_prompt(self, rearrangement_expression: str, 
                                      original_refexp: str, scene_context: Dict[str, Any]) -> str:
        """Create a prompt for diversifying the rearrangement expression"""
        
        # Extract scene information for context
        objects = scene_context.get('objects', [])
        object_descriptions = []
        for obj in objects:
            desc = f"{obj.get('color', 'unknown')} {obj.get('shape', 'object')}"
            if 'material' in obj:
                desc = f"{obj.get('material', '')} {desc}"
            object_descriptions.append(desc)
        
        scene_summary = f"Scene contains: {', '.join(object_descriptions[:5])}"
        if len(object_descriptions) > 5:
            scene_summary += f" and {len(object_descriptions) - 5} other objects"
        
        prompt = f"""You are an expert at creating natural, conversational variations of spatial rearrangement instructions for visual scenes.

SCENE CONTEXT: {scene_summary}

ORIGINAL IDENTIFYING EXPRESSION: "{original_refexp}"
REARRANGEMENT INSTRUCTION: "{rearrangement_expression}"

TASK: Create {self.config.max_variations} natural, conversational variations of the REARRANGEMENT INSTRUCTION that:
1. Refer to the EXACT SAME object to move (the target object)
2. Refer to the EXACT SAME reference object (spatial anchor)
3. Maintain the same spatial relationship and placement instruction
4. Use different sentence structures and word choices
5. Sound natural and conversational like human instructions
6. Are grammatically correct

REQUIREMENTS:
- Keep all spatial relations accurate (left, right, front, behind, between, nearest, farthest)
- Preserve object attributes (color, shape, material) but vary how you describe them
- Use different action verbs (place, move, put, position, set, relocate)
- Vary sentence structures (imperative, instructive, directive)
- Maintain the instruction's intent (moving/placing the object)
- Make expressions sound like natural human instructions

OUTPUT FORMAT: Return only the variations, one per line, without numbering or explanations.

EXAMPLES:
Original: "Place the red cube to the left of the blue sphere"
Variations:
- "Move the red cube so it's left of the blue sphere"
- "Put the red cube on the left side of the blue sphere"
- "Position the red cube to the left of the blue sphere"
- "Set the red cube left of the blue sphere"

Original: "Move the metal cylinder behind the green cube"
Variations:
- "Place the metal cylinder behind the green cube"
- "Put the metal cylinder in back of the green cube"
- "Position the cylinder behind the green cube"
- "Set the metal cylinder at the back of the green cube"

Now create variations for the given rearrangement instruction:"""
        
        return prompt
    
    def _call_openai(self, prompt: str) -> List[str]:
        """Call OpenAI API for diversification"""
        try:
            # Use max_completion_tokens for newer models like o4-mini
            if self.config.model_name.startswith('o4-'):
                response = self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": "You are an expert at creating natural language variations of spatial instructions while preserving meaning."},
                        {"role": "user", "content": prompt}
                    ],
                    max_completion_tokens=self.config.max_tokens
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": "You are an expert at creating natural language variations of spatial instructions while preserving meaning."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
            
            content = response.choices[0].message.content.strip()
            variations = [line.strip() for line in content.split('\n') if line.strip()]
            return variations[:self.config.max_variations]
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return []
    
    def _call_anthropic(self, prompt: str) -> List[str]:
        """Call Anthropic API for diversification"""
        try:
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            variations = [line.strip() for line in content.split('\n') if line.strip()]
            return variations[:self.config.max_variations]
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return []
    
    def diversify_rearrangement(self, rearrangement_expression: str, 
                               original_refexp: str, scene_context: Dict[str, Any]) -> List[str]:
        """Diversify a single rearrangement expression using LLM"""
        prompt = self._create_diversification_prompt(
            rearrangement_expression, original_refexp, scene_context
        )
        
        if self.config.llm_provider == 'openai':
            variations = self._call_openai(prompt)
        elif self.config.llm_provider == 'anthropic':
            variations = self._call_anthropic(prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.config.llm_provider}")
        
        # Filter out variations that are too similar to original or too short
        filtered_variations = []
        for var in variations:
            if (len(var) > 10 and 
                var.lower() != rearrangement_expression.lower() and
                not var.startswith('Original:') and
                not var.startswith('Variation')):
                filtered_variations.append(var)
        
        return filtered_variations[:self.config.max_variations]
    
    def diversify_batch(self, expression_pairs: List[Dict[str, Any]], 
                       scene_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Diversify a batch of rearrangement expression pairs"""
        diversified_data = []
        
        for i, pair_data in enumerate(expression_pairs):
            logger.info(f"Processing expression pair {i+1}/{len(expression_pairs)}")
            
            rearrangement = pair_data.get('rearrangement', {})
            original = pair_data.get('original', {})
            
            rearrangement_expression = rearrangement.get('refexp', '')
            original_refexp = original.get('refexp', '')
            
            if not rearrangement_expression or not original_refexp:
                continue
            
            # Get scene context for this expression
            scene_id = pair_data.get('scene_id', '')
            scene_context = self._get_scene_context(scene_data, scene_id)
            
            # Generate variations
            variations = self.diversify_rearrangement(
                rearrangement_expression, original_refexp, scene_context
            )
            
            # Create diversified entries
            for j, variation in enumerate(variations):
                diversified_pair = pair_data.copy()
                
                # Update the rearrangement part with the variation
                diversified_rearrangement = rearrangement.copy()
                diversified_rearrangement['refexp'] = variation
                diversified_rearrangement['original_rearrangement_refexp'] = rearrangement_expression
                diversified_rearrangement['variation_id'] = j + 1
                diversified_rearrangement['diversification_method'] = f"{self.config.llm_provider}_{self.config.model_name}"
                
                diversified_pair['rearrangement'] = diversified_rearrangement
                diversified_pair['diversified'] = True
                
                diversified_data.append(diversified_pair)
            
            # Add delay between requests to respect rate limits
            if i < len(expression_pairs) - 1:
                time.sleep(self.config.delay_between_requests)
        
        return diversified_data
    
    def _get_scene_context(self, scene_data: Dict[str, Any], scene_id: str) -> Dict[str, Any]:
        """Extract scene context for a specific scene"""
        scenes = scene_data.get('scenes', [])
        
        # Try matching by scene_id (e.g., "CLEVR_train_000000")
        for scene in scenes:
            image_filename = scene.get('image_filename', '')
            if scene_id in image_filename or image_filename.replace('.png', '') == scene_id:
                return scene
        
        return {}

def load_expression_pairs_data(filepath: str) -> List[Dict[str, Any]]:
    """Load expression pairs data from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data.get('expression_pairs', [])

def load_scene_data(filepath: str) -> Dict[str, Any]:
    """Load scene data from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def save_diversified_data(data: List[Dict[str, Any]], output_filepath: str, 
                         original_info: Dict[str, Any], llm_config: DiversificationConfig):
    """Save diversified rearrangement expressions to JSON file"""
    output_data = {
        "info": {
            **original_info,
            "diversification": {
                "llm_provider": llm_config.llm_provider,
                "model_name": llm_config.model_name,
                "max_variations": llm_config.max_variations,
                "temperature": llm_config.temperature,
                "diversification_date": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        },
        "expression_pairs": data
    }
    
    with open(output_filepath, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved {len(data)} diversified expression pairs to {output_filepath}")

def main():
    parser = argparse.ArgumentParser(description='Diversify rearrangement expressions using LLMs')
    parser.add_argument('--rearrangements_file', required=True, 
                       help='Path to JSON file containing rearrangement expression pairs')
    parser.add_argument('--scenes_file', required=True,
                       help='Path to JSON file containing scene data')
    parser.add_argument('--output_file', required=True,
                       help='Path to output JSON file for diversified rearrangements')
    parser.add_argument('--llm_provider', choices=['openai', 'anthropic'], required=True,
                       help='LLM provider to use')
    parser.add_argument('--model_name', required=True,
                       help='Model name (e.g., gpt-4, gpt-5, claude-3-opus)')
    parser.add_argument('--api_key', required=True,
                       help='API key for the LLM provider')
    parser.add_argument('--max_variations', type=int, default=4,
                       help='Maximum number of variations per expression (default: 4)')
    parser.add_argument('--temperature', type=float, default=0.8,
                       help='Temperature for LLM generation (default: 0.8)')
    parser.add_argument('--max_pairs', type=int, default=None,
                       help='Maximum number of expression pairs to process (for testing)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between API requests in seconds (default: 1.0)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = DiversificationConfig(
        llm_provider=args.llm_provider,
        model_name=args.model_name,
        api_key=args.api_key,
        max_variations=args.max_variations,
        temperature=args.temperature,
        delay_between_requests=args.delay
    )
    
    # Load data
    logger.info(f"Loading rearrangement expression pairs from {args.rearrangements_file}")
    expression_pairs = load_expression_pairs_data(args.rearrangements_file)
    
    logger.info(f"Loading scenes from {args.scenes_file}")
    scene_data = load_scene_data(args.scenes_file)
    
    # Limit pairs for testing if specified
    if args.max_pairs:
        expression_pairs = expression_pairs[:args.max_pairs]
        logger.info(f"Limited to {len(expression_pairs)} expression pairs for testing")
    
    # Initialize diversifier
    diversifier = LLMRearrangementDiversifier(config)
    
    # Process expression pairs
    logger.info(f"Starting diversification of {len(expression_pairs)} expression pairs")
    start_time = time.time()
    
    diversified_data = diversifier.diversify_batch(expression_pairs, scene_data)
    
    end_time = time.time()
    logger.info(f"Diversification completed in {end_time - start_time:.2f} seconds")
    logger.info(f"Generated {len(diversified_data)} total variations")
    
    # Load original info from rearrangements file
    with open(args.rearrangements_file, 'r') as f:
        original_data = json.load(f)
        original_info = original_data.get('info', {})
    
    # Save results
    save_diversified_data(diversified_data, args.output_file, original_info, config)
    
    logger.info("Diversification pipeline completed successfully!")

if __name__ == '__main__':
    main()


