"""
Preset System Routes

Handles both legacy flat presets and hierarchical preset system.
Routes are feature-flagged via ENABLE_HIERARCHICAL_PRESETS config.

Routes:
    GET /presets - Legacy flat presets (hot-reloadable)
    GET /api/categories - Level 1: Main categories
    GET /api/categories/<id>/types - Level 2: Types within category
    GET /api/categories/<cat>/<type>/artists - Level 3: Artists
    GET /api/artists/<cat>/<type>/<artist>/technical - Level 4: Technical options
    GET /api/artists/<cat>/<type>/<artist>/specifics - Level 5: Scene specifics
    GET /api/preset-packs - Quick-start preset packs
    GET /api/universal-options - Universal cross-cutting options
"""

from flask import Blueprint, jsonify, current_app
import logging

bp = Blueprint('presets', __name__)
logger = logging.getLogger(__name__)


@bp.route('/presets', methods=['GET'])
def get_presets():
    """
    Return available preset options as JSON.

    Provides the PRESETS dictionary to the frontend for populating
    dropdown menus. Includes all categories: styles, artists,
    composition, and lighting.

    NOTE: This endpoint reloads presets.json from disk on each request,
    allowing hot-reload without server restart. This makes it easy to
    edit presets and see changes immediately by refreshing the browser.

    Returns:
        JSON: PRESETS dictionary with all preset categories and options

    Example Response:
        {
            "styles": {"None": "", "Cinematic": "cinematic, dramatic, ...", ...},
            "artists": {"None": "", "Greg Rutkowski": "in the style of...", ...},
            ...
        }
    """
    logger.debug("Reloading presets from disk for hot-reload")

    # Import load_presets from shared modules
    from app.presets import load_presets

    # Reload presets from file on each request to enable hot-reload
    presets = load_presets()
    return jsonify(presets)


# ============================================================================
# Hierarchical Preset API Routes
# ============================================================================
# The following routes support the new hierarchical (5-level) progressive
# preset system. They are only active when ENABLE_HIERARCHICAL_PRESETS=true.
# Each route returns a subset of the hierarchical_presets.json data.


@bp.route('/api/categories', methods=['GET'])
def get_categories():
    """
    Get all main categories (Level 1 of hierarchical presets).

    Returns list of top-level categories like Photography, Fantasy, Sci-Fi, etc.
    Each category includes metadata like icon, description, and popularity.

    Only active when ENABLE_HIERARCHICAL_PRESETS=true.

    Returns:
        JSON: List of category objects with id, name, icon, description, etc.

    Example Response:
        {
            "version": "1.0",
            "categories": [
                {
                    "id": "photography",
                    "name": "Photography",
                    "icon": "📸",
                    "description": "Realistic camera-based imagery",
                    "popularity": "high",
                    "best_for": ["portraits", "landscapes", "realistic scenes"]
                },
                ...
            ]
        }
    """
    from app.config import config
    from app.presets import load_presets

    if not config.ENABLE_HIERARCHICAL_PRESETS:
        return jsonify({
            'error': 'Hierarchical presets not enabled',
            'message': 'Set ENABLE_HIERARCHICAL_PRESETS=true in .env'
        }), 400

    try:
        presets = load_presets()
        categories = []

        for cat_id, cat_data in presets.get('categories', {}).items():
            categories.append({
                'id': cat_id,
                'name': cat_data.get('name', cat_id),
                'icon': cat_data.get('icon', ''),
                'description': cat_data.get('description', ''),
                'popularity': cat_data.get('popularity', 'medium'),
                'best_for': cat_data.get('best_for', [])
            })

        # Sort by popularity (high first)
        categories.sort(key=lambda x: 0 if x['popularity'] == 'high' else 1)

        logger.info(f"Returned {len(categories)} categories")

        return jsonify({
            'version': presets.get('version', '1.0'),
            'categories': categories
        })

    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return jsonify({
            'error': 'Failed to load categories',
            'message': str(e)
        }), 500


@bp.route('/api/categories/<category_id>/types', methods=['GET'])
def get_category_types(category_id):
    """
    Get sub-types for a category (Level 2 of hierarchical presets).

    Args:
        category_id: ID of the category (e.g., 'photography', 'fantasy')

    Returns:
        JSON: List of type objects for this category

    Example:
        GET /api/categories/photography/types
        Returns: Portrait, Landscape, Street, Fashion, etc.
    """
    from app.config import config
    from app.presets import load_presets

    if not config.ENABLE_HIERARCHICAL_PRESETS:
        return jsonify({
            'error': 'Hierarchical presets not enabled'
        }), 400

    try:
        presets = load_presets()
        category = presets.get('categories', {}).get(category_id)

        if not category:
            logger.warning(f"Category not found: {category_id}")
            return jsonify({
                'error': 'Category not found',
                'message': f"No category with id '{category_id}'"
            }), 404

        types = []
        for type_id, type_data in category.get('level2_types', {}).items():
            types.append({
                'id': type_id,
                'name': type_data.get('name', type_id),
                'description': type_data.get('description', ''),
                'icon': type_data.get('icon', ''),
                'popularity': type_data.get('popularity', 'medium')
            })

        # Sort by popularity
        types.sort(key=lambda x: 0 if x['popularity'] == 'high' else 1)

        logger.info(f"Returned {len(types)} types for category '{category_id}'")

        return jsonify({
            'category_id': category_id,
            'category_name': category.get('name', category_id),
            'types': types
        })

    except Exception as e:
        logger.error(f"Error getting types for {category_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to load types',
            'message': str(e)
        }), 500


@bp.route('/api/categories/<category_id>/types/<type_id>/artists', methods=['GET'])
def get_artists(category_id, type_id):
    """
    Get artists/styles for a type (Level 3 of hierarchical presets).

    Args:
        category_id: ID of the category (e.g., 'photography')
        type_id: ID of the type (e.g., 'portrait')

    Returns:
        JSON: List of artist objects for this type

    Example:
        GET /api/categories/photography/types/portrait/artists
        Returns: Annie Leibovitz, Richard Avedon, Steve McCurry, etc.
    """
    from app.config import config
    from app.presets import load_presets

    if not config.ENABLE_HIERARCHICAL_PRESETS:
        return jsonify({'error': 'Hierarchical presets not enabled'}), 400

    try:
        presets = load_presets()
        category = presets.get('categories', {}).get(category_id)

        if not category:
            return jsonify({
                'error': 'Category not found',
                'message': f"No category '{category_id}'"
            }), 404

        type_data = category.get('level2_types', {}).get(type_id)
        if not type_data:
            return jsonify({
                'error': 'Type not found',
                'message': f"No type '{type_id}' in category '{category_id}'"
            }), 404

        artists = []
        for artist_id, artist_data in type_data.get('level3_artists', {}).items():
            artists.append({
                'id': artist_id,
                'name': artist_data.get('name', artist_id),
                'description': artist_data.get('description', ''),
                'signature': artist_data.get('signature', ''),
                'best_for': artist_data.get('best_for', []),
                'popularity': artist_data.get('popularity', 'medium'),
                'has_technical': bool(artist_data.get('level4_technical')),
                'has_specifics': bool(artist_data.get('level5_specifics'))
            })

        # Sort by popularity
        artists.sort(key=lambda x: 0 if x['popularity'] == 'high' else 1)

        logger.info(f"Returned {len(artists)} artists for {category_id}/{type_id}")

        return jsonify({
            'category_id': category_id,
            'type_id': type_id,
            'type_name': type_data.get('name', type_id),
            'artists': artists
        })

    except Exception as e:
        logger.error(f"Error getting artists: {str(e)}")
        return jsonify({
            'error': 'Failed to load artists',
            'message': str(e)
        }), 500


@bp.route('/api/artists/<category_id>/<type_id>/<artist_id>/technical', methods=['GET'])
def get_artist_technical(category_id, type_id, artist_id):
    """
    Get technical options for an artist (Level 4 of hierarchical presets).

    Args:
        category_id: ID of the category
        type_id: ID of the type
        artist_id: ID of the artist

    Returns:
        JSON: Technical options for this artist (camera, lighting, etc.)

    Example:
        GET /api/artists/photography/portrait/annie_leibovitz/technical
        Returns: camera_lens, film_digital, aperture, lighting options
    """
    from app.config import config
    from app.presets import load_presets

    if not config.ENABLE_HIERARCHICAL_PRESETS:
        return jsonify({'error': 'Hierarchical presets not enabled'}), 400

    try:
        presets = load_presets()

        # Navigate to artist data
        artist_data = (presets.get('categories', {})
                      .get(category_id, {})
                      .get('level2_types', {})
                      .get(type_id, {})
                      .get('level3_artists', {})
                      .get(artist_id))

        if not artist_data:
            return jsonify({
                'error': 'Artist not found',
                'message': f"No artist '{artist_id}' in {category_id}/{type_id}"
            }), 404

        technical = artist_data.get('level4_technical', {})

        logger.info(f"Returned technical options for {artist_id}")

        return jsonify({
            'category_id': category_id,
            'type_id': type_id,
            'artist_id': artist_id,
            'artist_name': artist_data.get('name', artist_id),
            'technical_options': technical
        })

    except Exception as e:
        logger.error(f"Error getting technical options: {str(e)}")
        return jsonify({
            'error': 'Failed to load technical options',
            'message': str(e)
        }), 500


@bp.route('/api/artists/<category_id>/<type_id>/<artist_id>/specifics', methods=['GET'])
def get_artist_specifics(category_id, type_id, artist_id):
    """
    Get scene specifics for an artist (Level 5 of hierarchical presets).

    Args:
        category_id: ID of the category
        type_id: ID of the type
        artist_id: ID of the artist

    Returns:
        JSON: Scene-specific options for this artist

    Example:
        GET /api/artists/photography/portrait/annie_leibovitz/specifics
        Returns: subject_type, pose_expression, wardrobe, environment, framing
    """
    from app.config import config
    from app.presets import load_presets

    if not config.ENABLE_HIERARCHICAL_PRESETS:
        return jsonify({'error': 'Hierarchical presets not enabled'}), 400

    try:
        presets = load_presets()

        # Navigate to artist data
        artist_data = (presets.get('categories', {})
                      .get(category_id, {})
                      .get('level2_types', {})
                      .get(type_id, {})
                      .get('level3_artists', {})
                      .get(artist_id))

        if not artist_data:
            return jsonify({
                'error': 'Artist not found',
                'message': f"No artist '{artist_id}' in {category_id}/{type_id}"
            }), 404

        specifics = artist_data.get('level5_specifics', {})

        logger.info(f"Returned scene specifics for {artist_id}")

        return jsonify({
            'category_id': category_id,
            'type_id': type_id,
            'artist_id': artist_id,
            'artist_name': artist_data.get('name', artist_id),
            'scene_specifics': specifics
        })

    except Exception as e:
        logger.error(f"Error getting specifics: {str(e)}")
        return jsonify({
            'error': 'Failed to load specifics',
            'message': str(e)
        }), 500


@bp.route('/api/preset-packs', methods=['GET'])
def get_preset_packs():
    """
    Get all preset packs for quick start.

    Preset packs are pre-configured combinations of selections across all 5 levels.
    Users can click a pack to instantly apply all selections and jump to generation.

    Returns:
        JSON: List of preset pack objects

    Example Response:
        {
            "packs": [
                {
                    "name": "90s X-Men Comic",
                    "icon": "🦸",
                    "selections": {
                        "level1": "comic_book",
                        "level2": "marvel_style",
                        "level3": "jim_lee",
                        ...
                    }
                },
                ...
            ]
        }
    """
    from app.config import config
    from app.presets import load_presets

    if not config.ENABLE_HIERARCHICAL_PRESETS:
        return jsonify({'error': 'Hierarchical presets not enabled'}), 400

    try:
        presets = load_presets()
        packs = presets.get('preset_packs', {}).get('packs', [])

        logger.info(f"Returned {len(packs)} preset packs")

        return jsonify({
            'packs': packs
        })

    except Exception as e:
        logger.error(f"Error getting preset packs: {str(e)}")
        return jsonify({
            'error': 'Failed to load preset packs',
            'message': str(e)
        }), 500


@bp.route('/api/universal-options', methods=['GET'])
def get_universal_options():
    """
    Get universal options (mood, lighting, time, weather, colors, camera effects).

    Universal options are available across all categories and can be applied
    in addition to the 5-level hierarchical selections.

    Returns:
        JSON: All universal option categories

    Example Response:
        {
            "universal_options": {
                "mood": {
                    "core": [...],
                    "by_category": {...}
                },
                "lighting": {...},
                "time_of_day": {...},
                "weather_atmosphere": {...},
                "color_palettes": {...},
                "camera_effects": {...},
                "composition": {...}
            }
        }
    """
    from app.config import config
    from app.presets import load_presets

    if not config.ENABLE_HIERARCHICAL_PRESETS:
        return jsonify({'error': 'Hierarchical presets not enabled'}), 400

    try:
        presets = load_presets()
        universal = presets.get('universal_options', {})

        logger.info(f"Returned universal options ({len(universal)} categories)")

        return jsonify({
            'universal_options': universal
        })

    except Exception as e:
        logger.error(f"Error getting universal options: {str(e)}")
        return jsonify({
            'error': 'Failed to load universal options',
            'message': str(e)
        }), 500
