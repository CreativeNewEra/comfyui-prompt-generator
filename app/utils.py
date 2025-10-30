"""
Utility functions for prompt generation and system prompt management.

This module contains helper functions for:
- Loading system prompts from files
- Building hierarchical prompts from preset selections
- Managing prompt dictionaries
"""

import logging
import os
from typing import Dict, Tuple

from app.config import config

# Setup logger
logger = logging.getLogger(__name__)


def load_prompts() -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Load system prompts from text files in the prompts/ directory.

    Returns:
        tuple: (SYSTEM_PROMPTS dict, CHAT_SYSTEM_PROMPTS dict)

    This function attempts to load prompts from external text files, enabling
    prompt editing without code changes. If files are missing or unreadable,
    it falls back to hardcoded default prompts to ensure the app remains functional.

    The function logs all operations for debugging and provides helpful error
    messages if files are missing.
    """
    # Hardcoded fallback prompts (original defaults)
    fallback_system_prompts = {
        "sdxl": """You are an expert prompt engineer for Stable Diffusion XL (SDXL). When users describe an image idea, you expand it into a detailed, effective prompt.

The user may provide preset selections for style, artist/photographer, composition, and lighting. When these are provided, incorporate them naturally into the prompt.

SDXL works best with:
- Natural language descriptions with rich details
- Quality tags like: masterpiece, best quality, highly detailed, sharp focus, 8k
- Specific details about: subject, composition, lighting, camera angle, art style, mood, colors
- Negative prompts to avoid unwanted elements

Format your response as:
PROMPT: [detailed positive prompt incorporating any presets]
NEGATIVE: [negative prompt with things to avoid]

Be creative, specific, and detailed. Weave the preset selections naturally into the description.""",

        "flux": """You are an expert prompt engineer for Flux models. When users describe an image idea, you expand it into a detailed, effective prompt.

The user may provide preset selections for style, artist/photographer, composition, and lighting. When these are provided, incorporate them naturally and seamlessly into the prompt description.

Flux models work best with:
- Natural language, conversational style prompts
- Very detailed scene descriptions
- Specific lighting and atmospheric details
- Camera angles and composition details
- Art style and mood descriptions
- No need for quality tags or negative prompts (Flux ignores them)

Format your response as:
PROMPT: [single detailed natural language prompt incorporating any presets naturally]

Be extremely descriptive and creative. Write like you're describing a photograph or painting in detail. Integrate the preset selections seamlessly into the narrative."""
    }

    fallback_chat_prompts = {
        "sdxl": """You are a collaborative prompt engineering partner helping the user craft prompts for Stable Diffusion XL (SDXL). Use a conversational tone and work iteratively.

For each user message:
- Briefly acknowledge the request and how it fits the ongoing concept.
- Brainstorm 2-3 improved prompt variations labeled as Option 1, Option 2, etc. Write them as rich natural language descriptions that naturally include any provided presets.
- Provide a short list of negative prompt considerations that SDXL users might add, highlighting differences between the options when helpful.
- Ask at least one follow-up question or suggest the next tweak to keep the collaboration moving forward.

Do not reply with a single "PROMPT:" line. Keep responses friendly, structured, and easy to skim in chat format.""",

        "flux": """You are a creative brainstorming partner for Flux image models. Respond conversationally and iterate with the user.

For each reply:
- Offer 2-3 distinct creative directions or prompt variations, each clearly labeled (e.g., Option 1, Option 2) and written in vivid natural language.
- Call out noteworthy stylistic, compositional, or lighting ideas for each option, integrating any presets the user selected.
- Ask at least one clarifying or exploratory question to encourage further refinement, or suggest what the user might try next.

Avoid emitting a single "PROMPT:" response. Keep the tone collaborative and idea-focused."""
    }

    system_prompts = {}
    chat_prompts = {}

    # Get prompt files from config
    prompt_files = config.PROMPT_FILES

    # Try to load SDXL oneshot prompt
    try:
        with open(prompt_files['sdxl_oneshot'], 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                system_prompts['sdxl'] = content
                logger.info("Loaded SDXL oneshot prompt from prompts/sdxl_oneshot.txt")
            else:
                logger.warning("prompts/sdxl_oneshot.txt is empty, using fallback")
                system_prompts['sdxl'] = fallback_system_prompts['sdxl']
    except FileNotFoundError:
        logger.warning("prompts/sdxl_oneshot.txt not found, using fallback")
        system_prompts['sdxl'] = fallback_system_prompts['sdxl']
    except Exception as e:
        logger.error(f"Error loading prompts/sdxl_oneshot.txt: {e}, using fallback")
        system_prompts['sdxl'] = fallback_system_prompts['sdxl']

    # Try to load Flux oneshot prompt
    try:
        with open(prompt_files['flux_oneshot'], 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                system_prompts['flux'] = content
                logger.info("Loaded Flux oneshot prompt from prompts/flux_oneshot.txt")
            else:
                logger.warning("prompts/flux_oneshot.txt is empty, using fallback")
                system_prompts['flux'] = fallback_system_prompts['flux']
    except FileNotFoundError:
        logger.warning("prompts/flux_oneshot.txt not found, using fallback")
        system_prompts['flux'] = fallback_system_prompts['flux']
    except Exception as e:
        logger.error(f"Error loading prompts/flux_oneshot.txt: {e}, using fallback")
        system_prompts['flux'] = fallback_system_prompts['flux']

    # Try to load SDXL chat prompt
    try:
        with open(prompt_files['sdxl_chat'], 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                chat_prompts['sdxl'] = content
                logger.info("Loaded SDXL chat prompt from prompts/sdxl_chat.txt")
            else:
                logger.warning("prompts/sdxl_chat.txt is empty, using fallback")
                chat_prompts['sdxl'] = fallback_chat_prompts['sdxl']
    except FileNotFoundError:
        logger.warning("prompts/sdxl_chat.txt not found, using fallback")
        chat_prompts['sdxl'] = fallback_chat_prompts['sdxl']
    except Exception as e:
        logger.error(f"Error loading prompts/sdxl_chat.txt: {e}, using fallback")
        chat_prompts['sdxl'] = fallback_chat_prompts['sdxl']

    # Try to load Flux chat prompt
    try:
        with open(prompt_files['flux_chat'], 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                chat_prompts['flux'] = content
                logger.info("Loaded Flux chat prompt from prompts/flux_chat.txt")
            else:
                logger.warning("prompts/flux_chat.txt is empty, using fallback")
                chat_prompts['flux'] = fallback_chat_prompts['flux']
    except FileNotFoundError:
        logger.warning("prompts/flux_chat.txt not found, using fallback")
        chat_prompts['flux'] = fallback_chat_prompts['flux']
    except Exception as e:
        logger.error(f"Error loading prompts/flux_chat.txt: {e}, using fallback")
        chat_prompts['flux'] = fallback_chat_prompts['flux']

    logger.info("System prompts loaded successfully")
    return system_prompts, chat_prompts


def build_hierarchical_prompt(user_input: str, selections: Dict, presets_data: Dict) -> str:
    """
    Build enhanced prompt from hierarchical preset selections.

    This function takes user selections from the hierarchical preset wizard
    and constructs a detailed, enhanced prompt that can be sent to the LLM.

    Args:
        user_input (str): User's basic image idea
        selections (dict): Dictionary with selections at each level:
            - level1 (str): Category ID (e.g., 'photography', 'fantasy')
            - level2 (str): Type ID (e.g., 'portrait', 'high_fantasy')
            - level3 (str): Artist ID (e.g., 'annie_leibovitz')
            - level4 (dict): Technical options {option_key: value_id}
            - level5 (dict): Scene specifics {key: value}
            - universal (dict): Universal options (mood, lighting, etc.)
        presets_data (dict): Full hierarchical presets JSON data

    Returns:
        str: Enhanced prompt with all selections formatted as text

    Example:
        >>> selections = {
        ...     'level1': 'photography',
        ...     'level2': 'portrait',
        ...     'level3': 'annie_leibovitz',
        ...     'level4': {'lighting': 'theatrical'},
        ...     'universal': {'mood': ['dramatic', 'elegant']}
        ... }
        >>> enhanced = build_hierarchical_prompt("A woman posing", selections, presets)
        >>> print(enhanced)
        A woman posing

        Style: Photography > Portrait > Annie Leibovitz
        ...
    """
    if not selections:
        logger.debug("No hierarchical selections provided, returning user input as-is")
        return user_input

    try:
        prompt_parts = [user_input, ""]

        # Get category data (Level 1)
        category_id = selections.get('level1')
        if not category_id:
            logger.debug("No level1 category selected")
            return user_input

        category = presets_data.get('categories', {}).get(category_id)
        if not category:
            logger.warning(f"Category '{category_id}' not found in presets")
            return user_input

        # Level 2: Type
        type_id = selections.get('level2')
        type_data = category.get('level2_types', {}).get(type_id) if type_id else None

        if type_data:
            prompt_parts.append(f"Style: {category['name']} > {type_data['name']}")

        # Level 3: Artist/Style
        artist_id = selections.get('level3')
        artist_data = type_data.get('level3_artists', {}).get(artist_id) if type_data and artist_id else None

        if artist_data:
            prompt_parts.append(f"Artist Style: {artist_data['name']}")

            if artist_data.get('description'):
                prompt_parts.append(f"Description: {artist_data['description']}")

            if artist_data.get('signature'):
                prompt_parts.append(f"Signature: {artist_data['signature']}")

            prompt_parts.append("")

        # Level 4: Technical details
        level4_selections = selections.get('level4', {})
        if level4_selections and artist_data:
            technical_opts = artist_data.get('level4_technical', {})
            if technical_opts:
                prompt_parts.append("Technical Details:")
                for tech_key, tech_value in level4_selections.items():
                    tech_category = technical_opts.get(tech_key)
                    if tech_category:
                        options = tech_category.get('options', [])
                        # Handle both list of dicts and list of strings
                        if options and isinstance(options[0], dict):
                            option = next((opt for opt in options if opt.get('id') == tech_value), None)
                            if option:
                                desc = f" ({option.get('description')})" if option.get('description') else ""
                                prompt_parts.append(f"- {tech_category['name']}: {option['name']}{desc}")
                        else:
                            # Simple string list
                            prompt_parts.append(f"- {tech_category['name']}: {tech_value.replace('_', ' ')}")
                prompt_parts.append("")

        # Level 5: Scene specifics
        level5_selections = selections.get('level5', {})
        if level5_selections:
            prompt_parts.append("Scene Details:")
            for key, value in level5_selections.items():
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, list):
                    prompt_parts.append(f"- {formatted_key}: {', '.join(value)}")
                elif isinstance(value, dict):
                    # Handle nested selections
                    for sub_key, sub_value in value.items():
                        formatted_sub_key = sub_key.replace('_', ' ').title()
                        prompt_parts.append(f"- {formatted_key} - {formatted_sub_key}: {sub_value}")
                else:
                    formatted_value = str(value).replace('_', ' ')
                    prompt_parts.append(f"- {formatted_key}: {formatted_value}")
            prompt_parts.append("")

        # Universal options
        universal = selections.get('universal', {})
        if universal:
            universal_added = False

            if universal.get('mood'):
                moods = universal['mood'] if isinstance(universal['mood'], list) else [universal['mood']]
                prompt_parts.append(f"Mood: {', '.join(moods)}")
                universal_added = True

            if universal.get('time_of_day'):
                prompt_parts.append(f"Time: {universal['time_of_day'].replace('_', ' ')}")
                universal_added = True

            if universal.get('lighting'):
                prompt_parts.append(f"Lighting: {universal['lighting'].replace('_', ' ')}")
                universal_added = True

            if universal.get('color_palette'):
                prompt_parts.append(f"Colors: {universal['color_palette'].replace('_', ' ')}")
                universal_added = True

            if universal.get('weather_atmosphere'):
                prompt_parts.append(f"Weather: {universal['weather_atmosphere'].replace('_', ' ')}")
                universal_added = True

            if universal.get('camera_effects'):
                effects = universal['camera_effects'] if isinstance(universal['camera_effects'], list) else [universal['camera_effects']]
                prompt_parts.append(f"Camera Effects: {', '.join(effects)}")
                universal_added = True

            if universal_added:
                prompt_parts.append("")

        enhanced_prompt = "\n".join(prompt_parts).strip()
        logger.info(f"Built hierarchical prompt ({len(enhanced_prompt)} chars) from {len(selections)} level selections")

        return enhanced_prompt

    except Exception as e:
        logger.error(f"Error building hierarchical prompt: {e}")
        logger.debug(f"Selections: {selections}")
        # Return original user input on error
        return user_input


# Load system prompts at module import time
# These can be reloaded dynamically via the /admin/reload-prompts endpoint
SYSTEM_PROMPTS, CHAT_SYSTEM_PROMPTS = load_prompts()


def get_system_prompt(model_type: str, chat_mode: bool = False) -> str:
    """
    Get the appropriate system prompt for the given model type and mode.

    Args:
        model_type (str): Model type ('flux', 'sdxl', etc.)
        chat_mode (bool): Whether to get chat mode prompt (True) or oneshot mode (False)

    Returns:
        str: System prompt content
    """
    if chat_mode:
        return CHAT_SYSTEM_PROMPTS.get(model_type, CHAT_SYSTEM_PROMPTS.get('flux', ''))
    else:
        return SYSTEM_PROMPTS.get(model_type, SYSTEM_PROMPTS.get('flux', ''))


def reload_system_prompts() -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Reload system prompts from disk.

    This function is called by the admin reload endpoint to refresh prompts
    without restarting the application.

    Returns:
        tuple: (SYSTEM_PROMPTS dict, CHAT_SYSTEM_PROMPTS dict)
    """
    global SYSTEM_PROMPTS, CHAT_SYSTEM_PROMPTS
    SYSTEM_PROMPTS, CHAT_SYSTEM_PROMPTS = load_prompts()
    return SYSTEM_PROMPTS, CHAT_SYSTEM_PROMPTS
