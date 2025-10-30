"""
Persona system management.

Manages loading and retrieving AI persona definitions and their system prompts.
Personas provide different conversation styles and approaches for prompt generation.
"""

import json
import logging
import os

from app.config import config

logger = logging.getLogger(__name__)


def load_personas():
    """
    Load persona definitions from personas.json.

    Returns:
        dict: Personas dictionary with persona_id as keys and persona metadata as values

    Raises:
        FileNotFoundError: If personas.json is missing
        json.JSONDecodeError: If personas.json contains invalid JSON

    Each persona includes:
        - name: Display name
        - description: User-facing description
        - icon: Emoji icon for UI
        - category: beginner/advanced/professional/specialized/creative/speed/adult
        - prompt_file: Filename of the persona's system prompt
        - features: List of key features
        - best_for: Use case description
        - supports_presets: Boolean
        - supports_quick_generate: Boolean
        - supports_streaming: Boolean
    """
    personas_file = config.PERSONAS_FILE

    try:
        with open(personas_file, 'r', encoding='utf-8') as f:
            personas = json.load(f)
            logger.info(f"Successfully loaded {len(personas)} personas from {personas_file}")
            return personas

    except FileNotFoundError:
        logger.error(f"Personas file not found: {personas_file}")
        logger.warning("Using empty fallback personas")
        return {}

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in personas file: {e}")
        logger.warning("Using empty fallback personas")
        return {}

    except Exception as e:
        logger.error(f"Unexpected error loading personas: {e}")
        logger.warning("Using empty fallback personas")
        return {}


def load_persona_prompt(persona_id: str):
    """
    Load the detailed system prompt for a specific persona from the personas/ directory.

    Args:
        persona_id: The persona identifier (e.g., 'creative_vision_guide')

    Returns:
        str: The full system prompt text for the persona, or empty string if not found

    The prompt file should be in the personas/ directory with filename matching
    the prompt_file value in personas.json.
    """
    personas = load_personas()

    if persona_id not in personas:
        logger.error(f"Persona ID not found: {persona_id}")
        return ""

    persona_info = personas[persona_id]
    prompt_file = persona_info.get('prompt_file')

    if not prompt_file:
        logger.error(f"No prompt_file specified for persona: {persona_id}")
        return ""

    prompt_path = os.path.join(config.PERSONAS_DIR, prompt_file)

    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
            logger.info(f"Successfully loaded prompt for persona '{persona_id}' from {prompt_path}")
            return prompt_content

    except FileNotFoundError:
        logger.error(f"Persona prompt file not found: {prompt_path}")
        return ""

    except Exception as e:
        logger.error(f"Error loading persona prompt from {prompt_path}: {e}")
        return ""
