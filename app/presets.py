"""
Preset system management.

Supports two preset systems:
- Legacy flat presets (4 categories: styles, artists, composition, lighting)
- Hierarchical presets (5-level nested structure with categories, types, artists)

Toggle between systems using ENABLE_HIERARCHICAL_PRESETS config flag.
"""

import json
import logging
import os

from app.config import config

logger = logging.getLogger(__name__)


# Load presets at module import time
# This allows routes to import PRESETS directly without calling load_presets()
PRESETS = None


def load_presets():
    """
    Load presets from either hierarchical_presets.json or legacy presets.json.

    The function supports both:
    - Legacy flat presets (styles, artists, composition, lighting)
    - New hierarchical presets (categories, preset_packs, universal_options)

    Which file is loaded depends on the ENABLE_HIERARCHICAL_PRESETS feature flag.

    Returns:
        dict: Presets dictionary in appropriate format based on preset type

    Raises:
        FileNotFoundError: If presets file is missing
        json.JSONDecodeError: If presets file contains invalid JSON

    The function includes fallback presets in case the file is missing or invalid.
    This ensures the application can still run even if the presets file is corrupted.
    """
    preset_type = "hierarchical" if config.ENABLE_HIERARCHICAL_PRESETS else "legacy"
    presets_file = config.PRESETS_FILE

    try:
        with open(presets_file, 'r', encoding='utf-8') as f:
            presets = json.load(f)
            logger.info(f"Successfully loaded {preset_type} presets from {presets_file}")

            # Validate structure based on type
            if config.ENABLE_HIERARCHICAL_PRESETS:
                if 'categories' in presets and 'preset_packs' in presets:
                    num_categories = len(presets.get('categories', {}))
                    num_packs = len(presets.get('preset_packs', {}).get('packs', []))
                    logger.info(f"Loaded {num_categories} categories and {num_packs} preset packs")
                else:
                    logger.warning("Hierarchical presets file missing expected structure")

            return presets

    except FileNotFoundError:
        logger.error(f"Presets file not found: {presets_file}")
        logger.warning(f"Using minimal fallback {preset_type} presets")

        # Return appropriate fallback based on type
        if config.ENABLE_HIERARCHICAL_PRESETS:
            return {
                "version": "1.0",
                "categories": {},
                "preset_packs": {"packs": []},
                "universal_options": {},
                "quality_tags": {"flux": {}, "sdxl": {}}
            }
        else:
            return {
                "styles": {"None": ""},
                "artists": {"None": ""},
                "composition": {"None": ""},
                "lighting": {"None": ""}
            }

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in presets file: {e}")
        logger.warning(f"Using minimal fallback {preset_type} presets")

        if config.ENABLE_HIERARCHICAL_PRESETS:
            return {
                "version": "1.0",
                "categories": {},
                "preset_packs": {"packs": []},
                "universal_options": {},
                "quality_tags": {"flux": {}, "sdxl": {}}
            }
        else:
            return {
                "styles": {"None": ""},
                "artists": {"None": ""},
                "composition": {"None": ""},
                "lighting": {"None": ""}
            }

    except Exception as e:
        logger.error(f"Unexpected error loading presets: {e}")
        logger.warning(f"Using minimal fallback {preset_type} presets")

        if config.ENABLE_HIERARCHICAL_PRESETS:
            return {
                "version": "1.0",
                "categories": {},
                "preset_packs": {"packs": []},
                "universal_options": {},
                "quality_tags": {"flux": {}, "sdxl": {}}
            }
        else:
            return {
                "styles": {"None": ""},
                "artists": {"None": ""},
                "composition": {"None": ""},
                "lighting": {"None": ""}
            }


# Load presets at module import time
PRESETS = load_presets()
