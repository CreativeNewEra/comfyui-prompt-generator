"""
Quick Generate Routes

Handles one-shot prompt generation with optional presets.
Provides both streaming and non-streaming modes.

Routes:
    POST /generate - Non-streaming one-shot generation
    POST /generate-stream - Streaming one-shot generation (SSE)
"""

from flask import Blueprint, jsonify, request, current_app
import json
import logging

bp = Blueprint('generate', __name__)
logger = logging.getLogger(__name__)


@bp.route('/generate', methods=['POST'])
def generate():
    """
    Generate a prompt using one-shot mode (Quick Generate).

    Accepts user input and optional preset selections, then calls Ollama
    to generate a detailed prompt formatted for the selected model type.
    Saves result to history database.

    Request JSON:
        {
            "input": "user description text",
            "model": "flux" or "sdxl",
            "style": "preset name or None",
            "artist": "preset name or None",
            "composition": "preset name or None",
            "lighting": "preset name or None"
        }

    Returns:
        JSON: Generated prompt and model type
        {
            "result": "generated prompt text",
            "model": "flux"
        }

    Status Codes:
        200: Success
        400: Missing/invalid input
        503: Ollama connection failed
        504: Ollama timeout
        404: Model not found
        502: Ollama API error
    """
    logger.info("Received /generate request")

    # Validate request contains JSON data
    data = request.get_json(silent=True)
    if not data:
        logger.warning("Generate request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    from app.config import config
    from app.presets import load_presets, PRESETS
    from app.utils import SYSTEM_PROMPTS, build_hierarchical_prompt
    from app.ollama_client import call_ollama
    from app.database import save_to_history

    # Extract request parameters
    user_input = data.get('input', '').strip()
    model_type = data.get('model', 'flux')  # Default to Flux if not specified
    ollama_model = data.get('ollama_model', config.OLLAMA_MODEL)  # Ollama model to use

    # Extract preset selections (all default to 'None' if not provided)
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')
    selections = data.get('selections')

    hierarchical_prompt = None
    using_hierarchical = False
    if config.ENABLE_HIERARCHICAL_PRESETS and isinstance(selections, dict) and selections:
        logger.debug("Applying hierarchical selections to oneshot generation request")
        presets_data = load_presets()
        hierarchical_prompt = build_hierarchical_prompt(user_input, selections, presets_data)
        using_hierarchical = bool(hierarchical_prompt and hierarchical_prompt.strip())

    # Validate user provided some input
    if not user_input:
        logger.warning("Generate request with empty input")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a description'
        }), 400

    logger.info(f"Generating prompt for model: {model_type}")
    logger.debug(f"User input preview: {user_input[:50]}...")

    # Initialize full_input with default value (used as fallback when no presets selected)
    full_input = user_input

    if using_hierarchical:
        full_input = hierarchical_prompt
    else:
        # Build preset context by looking up selected preset values
        # Only include presets that aren't "None" or empty
        preset_context = []
        if style and style != 'None' and style in PRESETS['styles']:
            preset_context.append(f"Style: {PRESETS['styles'][style]}")
        if artist and artist != 'None' and artist in PRESETS['artists']:
            preset_context.append(f"Artist/Style: {PRESETS['artists'][artist]}")
        if composition and composition != 'None' and composition in PRESETS['composition']:
            preset_context.append(f"Composition: {PRESETS['composition'][composition]}")
        if lighting and lighting != 'None' and lighting in PRESETS['lighting']:
            preset_context.append(f"Lighting: {PRESETS['lighting'][lighting]}")

        # Build the full user message with presets incorporated
        if preset_context:
            # If presets are selected, format them clearly for the AI
            preset_info = "\n".join(preset_context)
            full_input = f"User's image idea: {user_input}\n\nSelected presets:\n{preset_info}\n\nPlease create a detailed prompt incorporating these elements."

    # Get the appropriate system prompt for this model type
    # Falls back to Flux prompt if model type is unknown
    system_prompt = SYSTEM_PROMPTS.get(model_type, SYSTEM_PROMPTS['flux'])

    # Construct message array for Ollama
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_input}
    ]

    # Call Ollama API (may raise custom exceptions caught by error handlers)
    result = call_ollama(messages, model=ollama_model)
    logger.info(f"Successfully generated prompt using model: {ollama_model}")

    # Save the generation to history database for later retrieval
    presets_dict = {
        'style': style,
        'artist': artist,
        'composition': composition,
        'lighting': lighting
    }
    if using_hierarchical:
        presets_dict['hierarchical'] = selections
    save_to_history(user_input, result, model_type, presets_dict, 'oneshot')

    return jsonify({
        'result': result,
        'model': model_type
    })


@bp.route('/generate-stream', methods=['POST'])
def generate_stream():
    """Generate a prompt with streaming (one-shot mode)"""
    logger.info("Received /generate-stream request")

    # Validate request has JSON data
    data = request.get_json(silent=True)
    if not data:
        logger.warning("Generate-stream request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    from app.config import config
    from app.presets import load_presets, PRESETS
    from app.utils import SYSTEM_PROMPTS, build_hierarchical_prompt
    from app.ollama_client import call_ollama
    from app.database import save_to_history
    from app.errors import OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError, OllamaAPIError

    user_input = data.get('input', '').strip()
    model_type = data.get('model', 'flux')
    ollama_model = data.get('ollama_model', config.OLLAMA_MODEL)  # Ollama model to use

    # Get preset selections
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')
    selections = data.get('selections')

    hierarchical_prompt = None
    using_hierarchical = False
    if config.ENABLE_HIERARCHICAL_PRESETS and isinstance(selections, dict) and selections:
        logger.debug("Applying hierarchical selections to streaming oneshot request")
        presets_data = load_presets()
        hierarchical_prompt = build_hierarchical_prompt(user_input, selections, presets_data)
        using_hierarchical = bool(hierarchical_prompt and hierarchical_prompt.strip())

    if not user_input:
        logger.warning("Generate-stream request with empty input")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a description'
        }), 400

    logger.info(f"Generating streaming prompt for model: {model_type}, ollama_model: {ollama_model}")
    logger.debug(f"User input preview: {user_input[:50]}...")

    # Initialize full_input with default value (used as fallback when no presets selected)
    full_input = user_input

    if using_hierarchical:
        full_input = hierarchical_prompt
    else:
        # Build context with presets
        preset_context = []
        if style and style != 'None' and style in PRESETS['styles']:
            preset_context.append(f"Style: {PRESETS['styles'][style]}")
        if artist and artist != 'None' and artist in PRESETS['artists']:
            preset_context.append(f"Artist/Style: {PRESETS['artists'][artist]}")
        if composition and composition != 'None' and composition in PRESETS['composition']:
            preset_context.append(f"Composition: {PRESETS['composition'][composition]}")
        if lighting and lighting != 'None' and lighting in PRESETS['lighting']:
            preset_context.append(f"Lighting: {PRESETS['lighting'][lighting]}")

        # Build the full user message
        if preset_context:
            preset_info = "\n".join(preset_context)
            full_input = f"User's image idea: {user_input}\n\nSelected presets:\n{preset_info}\n\nPlease create a detailed prompt incorporating these elements."

    # Get appropriate system prompt
    system_prompt = SYSTEM_PROMPTS.get(model_type, SYSTEM_PROMPTS['flux'])

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_input}
    ]

    presets_dict = {
        'style': style,
        'artist': artist,
        'composition': composition,
        'lighting': lighting
    }
    if using_hierarchical:
        presets_dict['hierarchical'] = selections

    def generate():
        """Generator function for SSE streaming"""
        try:
            full_response = ""
            for token in call_ollama(messages, model=ollama_model, stream=True):
                full_response += token
                # Send token as SSE event
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Send completion event
            yield f"data: {json.dumps({'done': True})}\n\n"

            # Save to history after completion
            save_to_history(user_input, full_response, model_type, presets_dict, 'oneshot')
            logger.info("Successfully generated streaming prompt")

        except (OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError, OllamaAPIError) as e:
            # Send error event
            yield f"data: {json.dumps({'error': str(e), 'type': type(e).__name__})}\n\n"
            logger.error(f"Error during streaming: {str(e)}")
        except Exception as e:
            # Send generic error event
            yield f"data: {json.dumps({'error': f'Unexpected error: {str(e)}', 'type': 'UnexpectedError'})}\n\n"
            logger.error(f"Unexpected error during streaming: {str(e)}", exc_info=True)

    return current_app.response_class(generate(), mimetype='text/event-stream')
