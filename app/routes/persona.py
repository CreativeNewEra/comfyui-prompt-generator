"""
Persona System Routes

Handles conversational AI persona-based prompt generation.
Personas provide different conversation styles and approaches.

Routes:
    GET /api/personas - List all available personas
    GET /api/personas/<id> - Get specific persona details
    POST /persona-chat - Non-streaming persona conversation
    POST /persona-chat-stream - Streaming persona conversation (SSE)
    POST /persona-reset - Reset persona conversation history
"""

from flask import Blueprint, jsonify, request, session, current_app
import json
import logging

bp = Blueprint('persona', __name__)
logger = logging.getLogger(__name__)


@bp.route('/api/personas', methods=['GET'])
def get_personas():
    """
    Get all available personas with their metadata.

    Returns a list of all personas including their display name, description,
    icon, category, features, and capabilities. This is used by the frontend
    to display the persona selector UI.

    Returns:
        JSON: Dictionary of persona objects keyed by persona_id

    Example Response:
        {
            "creative_vision_guide": {
                "name": "Creative Vision Guide",
                "description": "Patient, step-by-step scene building...",
                "icon": "🎨",
                "category": "beginner",
                "features": ["guided_questions", "scene_summary", ...],
                "best_for": "Vague ideas, creative exploration, beginners",
                "supports_presets": false,
                "supports_quick_generate": false,
                "supports_streaming": true
            },
            ...
        }
    """
    try:
        from app.personas import load_personas

        personas = load_personas()
        logger.debug(f"Returned {len(personas)} personas")
        return jsonify(personas)

    except Exception as e:
        logger.error(f"Error loading personas: {e}")
        return jsonify({
            'error': 'Failed to load personas',
            'message': str(e)
        }), 500


@bp.route('/api/personas/<persona_id>', methods=['GET'])
def get_persona_details(persona_id):
    """
    Get detailed information for a specific persona including its system prompt.

    Args:
        persona_id: The persona identifier (e.g., 'creative_vision_guide')

    Returns:
        JSON: Complete persona object including metadata and system prompt

    Example Response:
        {
            "id": "creative_vision_guide",
            "name": "Creative Vision Guide",
            "description": "Patient, step-by-step scene building...",
            "icon": "🎨",
            "category": "beginner",
            "features": ["guided_questions", "scene_summary", ...],
            "best_for": "Vague ideas, creative exploration, beginners",
            "supports_presets": false,
            "supports_quick_generate": false,
            "supports_streaming": true,
            "system_prompt": "You are a Creative Vision Guide..."
        }
    """
    try:
        from app.personas import load_personas, load_persona_prompt

        personas = load_personas()

        if persona_id not in personas:
            return jsonify({
                'error': 'Persona not found',
                'message': f'No persona with id: {persona_id}'
            }), 404

        persona_info = personas[persona_id]
        system_prompt = load_persona_prompt(persona_id)

        # Combine metadata with system prompt
        response = {
            'id': persona_id,
            **persona_info,
            'system_prompt': system_prompt
        }

        logger.debug(f"Returned details for persona: {persona_id}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error loading persona {persona_id}: {e}")
        return jsonify({
            'error': 'Failed to load persona details',
            'message': str(e)
        }), 500


@bp.route('/persona-chat', methods=['POST'])
def persona_chat():
    """
    Generate responses using persona-based conversational mode (non-streaming).

    Personas provide different conversational styles and approaches:
    - Creative Vision Guide: Patient step-by-step scene building
    - Technical Engineer: Advanced prompt engineering with weights
    - Art Director: Commercial/professional creative direction
    - Photography Expert: Camera-centric photorealistic prompts
    - Fantasy Storyteller: Narrative-rich world-building
    - Quick Sketch: Rapid 2-3 question generation
    - NSFW Specialist: Tasteful artistic adult content

    Request JSON:
        {
            "message": "user message text",
            "persona_id": "creative_vision_guide",
            "model": "flux" or "sdxl" (optional, used for presets if persona supports them),
            "ollama_model": "qwen3:latest" (optional),
            "style": "preset name or None" (optional, only if persona supports presets),
            "artist": "preset name or None" (optional),
            "composition": "preset name or None" (optional),
            "lighting": "preset name or None" (optional)
        }

    Returns:
        JSON: Generated response with persona metadata
        {
            "result": "AI response text",
            "persona": "creative_vision_guide"
        }

    Status Codes:
        200: Success
        400: Missing/invalid message or persona
        404: Persona not found
        503: Ollama connection failed
        504: Ollama timeout
        502: Ollama API error

    Notes:
        - Conversation history persisted in server-side store with persona_id
        - Changing persona resets the conversation
        - Each persona has its own system prompt loaded from personas/ directory
        - Personas that don't support presets ignore preset parameters
    """
    logger.info("Received /persona-chat request")

    # Validate request has JSON data
    data = request.get_json(silent=True)
    if not data:
        logger.warning("Persona-chat request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    from app.config import config
    from app.personas import load_personas, load_persona_prompt
    from app.presets import load_presets, PRESETS
    from app.utils import build_hierarchical_prompt
    from app.ollama_client import call_ollama
    from app.database import save_to_history

    user_message = data.get('message', '').strip()
    persona_id = data.get('persona_id', '').strip()
    model_type = data.get('model', 'flux')  # For preset compatibility
    ollama_model = data.get('ollama_model', config.OLLAMA_MODEL)

    if not user_message:
        logger.warning("Persona-chat request with empty message")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a message'
        }), 400

    if not persona_id:
        logger.warning("Persona-chat request missing persona_id")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Please specify a persona_id'
        }), 400

    # Load and validate persona
    personas = load_personas()
    if persona_id not in personas:
        logger.warning(f"Invalid persona_id: {persona_id}")
        return jsonify({
            'error': 'Persona not found',
            'message': f'No persona with id: {persona_id}'
        }), 404

    persona_info = personas[persona_id]
    persona_system_prompt = load_persona_prompt(persona_id)

    if not persona_system_prompt:
        logger.error(f"Failed to load system prompt for persona: {persona_id}")
        return jsonify({
            'error': 'Persona configuration error',
            'message': f'Could not load prompt for persona: {persona_id}'
        }), 500

    # Get or create conversation with persona
    conversation_id = session.get('persona_conversation_id')
    stored_persona = session.get('active_persona')

    conversation, stored_model = current_app.conversation_store.get_conversation(conversation_id)

    # Reset conversation if persona changed
    if stored_persona and stored_persona != persona_id:
        logger.info(f"Persona changed from {stored_persona} to {persona_id}, starting new conversation")
        current_app.conversation_store.delete_session(conversation_id)
        conversation_id = None
        conversation = []
        stored_persona = None

    # Initialize conversation with persona system prompt
    if not conversation:
        conversation = [{
            "role": "system",
            "content": persona_system_prompt
        }]
        conversation_id = current_app.conversation_store.create_session(persona_id, conversation)
        session['persona_conversation_id'] = conversation_id
        session['active_persona'] = persona_id
    else:
        session['persona_conversation_id'] = conversation_id
        session['active_persona'] = persona_id

    logger.debug(f"Persona: {persona_id}, Message preview: {user_message[:50]}...")

    # Handle presets if persona supports them
    full_message = user_message
    if persona_info.get('supports_presets', False):
        style = data.get('style', 'None')
        artist = data.get('artist', 'None')
        composition = data.get('composition', 'None')
        lighting = data.get('lighting', 'None')
        selections = data.get('selections')

        hierarchical_message = None
        using_hierarchical = False
        if config.ENABLE_HIERARCHICAL_PRESETS and isinstance(selections, dict) and selections:
            logger.debug("Applying hierarchical selections to persona chat")
            presets_data = load_presets()
            hierarchical_message = build_hierarchical_prompt(user_message, selections, presets_data)
            using_hierarchical = bool(hierarchical_message and hierarchical_message.strip())

        if using_hierarchical:
            full_message = hierarchical_message
        else:
            # Build context with legacy presets
            preset_context = []
            if style and style != 'None' and style in PRESETS['styles']:
                preset_context.append(f"Style: {PRESETS['styles'][style]}")
            if artist and artist != 'None' and artist in PRESETS['artists']:
                preset_context.append(f"Artist/Style: {PRESETS['artists'][artist]}")
            if composition and composition != 'None' and composition in PRESETS['composition']:
                preset_context.append(f"Composition: {PRESETS['composition'][composition]}")
            if lighting and lighting != 'None' and lighting in PRESETS['lighting']:
                preset_context.append(f"Lighting: {PRESETS['lighting'][lighting]}")

            if preset_context:
                preset_info = "\n".join(preset_context)
                full_message = f"{user_message}\n\n[Selected presets: {preset_info}]"

    # Add user message
    conversation.append({
        "role": "user",
        "content": full_message
    })

    conversation = current_app.conversation_store.save_messages(conversation_id, conversation, persona_id)
    conversation_snapshot = list(conversation)

    # Get response from Ollama
    result = call_ollama(conversation_snapshot, model=ollama_model)

    # Add assistant response to history
    conversation.append({
        "role": "assistant",
        "content": result
    })

    current_app.conversation_store.save_messages(conversation_id, conversation, persona_id)
    logger.info(f"Successfully processed persona chat message for: {persona_id}")

    # Save to history with persona metadata
    presets_dict = {'persona': persona_id}
    if persona_info.get('supports_presets', False):
        presets_dict.update({
            'style': data.get('style', 'None'),
            'artist': data.get('artist', 'None'),
            'composition': data.get('composition', 'None'),
            'lighting': data.get('lighting', 'None')
        })
    save_to_history(user_message, result, model_type, presets_dict, 'persona-chat')

    return jsonify({
        'result': result,
        'persona': persona_id
    })


@bp.route('/persona-chat-stream', methods=['POST'])
def persona_chat_stream():
    """
    Generate responses using persona-based conversational mode with streaming (SSE).

    This is the streaming version of /persona-chat, providing real-time token-by-token
    responses for a more interactive experience. Recommended for production use.

    Request JSON: Same as /persona-chat
        {
            "message": "user message text",
            "persona_id": "creative_vision_guide",
            "model": "flux" or "sdxl" (optional),
            "ollama_model": "qwen3:latest" (optional),
            "style/artist/composition/lighting": (optional, if persona supports presets)
        }

    Returns:
        Server-Sent Events (text/event-stream):
        - Token events: {"token": "word"}
        - Completion event: {"done": true}
        - Error events: {"error": "message", "type": "ErrorType"}

    Status Codes:
        200: Streaming started successfully
        400: Missing/invalid message or persona
        404: Persona not found
        (Errors sent as SSE events during streaming)

    Notes:
        - Uses Server-Sent Events for real-time streaming
        - Conversation history updated after streaming completes
        - Same session management as /persona-chat
    """
    logger.info("Received /persona-chat-stream request")

    # Validate request has JSON data
    data = request.get_json(silent=True)
    if not data:
        logger.warning("Persona-chat-stream request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    from app.config import config
    from app.personas import load_personas, load_persona_prompt
    from app.presets import load_presets, PRESETS
    from app.utils import build_hierarchical_prompt
    from app.ollama_client import call_ollama
    from app.database import save_to_history
    from app.errors import OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError, OllamaAPIError

    user_message = data.get('message', '').strip()
    persona_id = data.get('persona_id', '').strip()
    model_type = data.get('model', 'flux')
    ollama_model = data.get('ollama_model', config.OLLAMA_MODEL)

    if not user_message:
        logger.warning("Persona-chat-stream request with empty message")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a message'
        }), 400

    if not persona_id:
        logger.warning("Persona-chat-stream request missing persona_id")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Please specify a persona_id'
        }), 400

    # Load and validate persona
    personas = load_personas()
    if persona_id not in personas:
        logger.warning(f"Invalid persona_id: {persona_id}")
        return jsonify({
            'error': 'Persona not found',
            'message': f'No persona with id: {persona_id}'
        }), 404

    persona_info = personas[persona_id]
    persona_system_prompt = load_persona_prompt(persona_id)

    if not persona_system_prompt:
        logger.error(f"Failed to load system prompt for persona: {persona_id}")
        return jsonify({
            'error': 'Persona configuration error',
            'message': f'Could not load prompt for persona: {persona_id}'
        }), 500

    # Get or create conversation with persona
    conversation_id = session.get('persona_conversation_id')
    stored_persona = session.get('active_persona')

    conversation, stored_model = current_app.conversation_store.get_conversation(conversation_id)

    # Reset conversation if persona changed
    if stored_persona and stored_persona != persona_id:
        logger.info(f"Persona changed from {stored_persona} to {persona_id}, starting new conversation")
        current_app.conversation_store.delete_session(conversation_id)
        conversation_id = None
        conversation = []
        stored_persona = None

    # Initialize conversation with persona system prompt
    if not conversation:
        conversation = [{
            "role": "system",
            "content": persona_system_prompt
        }]
        conversation_id = current_app.conversation_store.create_session(persona_id, conversation)

    session['persona_conversation_id'] = conversation_id
    session['active_persona'] = persona_id

    logger.debug(f"Persona: {persona_id}, Message preview: {user_message[:50]}...")

    # Handle presets if persona supports them
    full_message = user_message
    presets_dict = {'persona': persona_id}

    if persona_info.get('supports_presets', False):
        style = data.get('style', 'None')
        artist = data.get('artist', 'None')
        composition = data.get('composition', 'None')
        lighting = data.get('lighting', 'None')
        selections = data.get('selections')

        hierarchical_message = None
        using_hierarchical = False
        if config.ENABLE_HIERARCHICAL_PRESETS and isinstance(selections, dict) and selections:
            logger.debug("Applying hierarchical selections to streaming persona chat")
            presets_data = load_presets()
            hierarchical_message = build_hierarchical_prompt(user_message, selections, presets_data)
            using_hierarchical = bool(hierarchical_message and hierarchical_message.strip())

        if using_hierarchical:
            full_message = hierarchical_message
            presets_dict['hierarchical'] = selections
        else:
            # Build context with legacy presets
            preset_context = []
            if style and style != 'None' and style in PRESETS['styles']:
                preset_context.append(f"Style: {PRESETS['styles'][style]}")
            if artist and artist != 'None' and artist in PRESETS['artists']:
                preset_context.append(f"Artist/Style: {PRESETS['artists'][artist]}")
            if composition and composition != 'None' and composition in PRESETS['composition']:
                preset_context.append(f"Composition: {PRESETS['composition'][composition]}")
            if lighting and lighting != 'None' and lighting in PRESETS['lighting']:
                preset_context.append(f"Lighting: {PRESETS['lighting'][lighting]}")

            if preset_context:
                preset_info = "\n".join(preset_context)
                full_message = f"{user_message}\n\n[Selected presets: {preset_info}]"

            presets_dict.update({
                'style': style,
                'artist': artist,
                'composition': composition,
                'lighting': lighting
            })

    # Add user message
    conversation.append({
        "role": "user",
        "content": full_message
    })

    conversation = current_app.conversation_store.save_messages(conversation_id, conversation, persona_id)
    conversation_snapshot = list(conversation)

    def generate():
        """Generator function for SSE streaming"""
        nonlocal conversation
        full_response = ""
        try:
            for token in call_ollama(conversation_snapshot, model=ollama_model, stream=True):
                full_response += token
                # Send token as SSE event
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Send completion event
            yield f"data: {json.dumps({'done': True})}\n\n"

            logger.info(f"Successfully processed streaming persona chat for: {persona_id}")

        except (OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError, OllamaAPIError) as e:
            # Send error event
            yield f"data: {json.dumps({'error': str(e), 'type': type(e).__name__})}\n\n"
            logger.error(f"Error during persona streaming: {str(e)}")
        except Exception as e:
            # Send generic error event
            yield f"data: {json.dumps({'error': f'Unexpected error: {str(e)}', 'type': 'UnexpectedError'})}\n\n"
            logger.error(f"Unexpected error during persona streaming: {str(e)}", exc_info=True)
        finally:
            # Update session after streaming completes
            if full_response:
                conversation.append({
                    "role": "assistant",
                    "content": full_response
                })

                current_app.conversation_store.save_messages(conversation_id, conversation, persona_id)

                # Save to history after completion
                save_to_history(user_message, full_response, model_type, presets_dict, 'persona-chat')

    return current_app.response_class(generate(), mimetype='text/event-stream')


@bp.route('/persona-reset', methods=['POST'])
def persona_reset():
    """
    Reset the persona conversation history.

    Clears the persona session conversation, effectively starting a fresh
    conversation with the current or next persona. Similar to /reset but
    specifically for persona mode.

    Returns:
        JSON: Success confirmation
        {
            "message": "Persona conversation reset"
        }

    Status Codes:
        200: Success
    """
    logger.info("Received /persona-reset request")

    conversation_id = session.get('persona_conversation_id')
    if conversation_id:
        current_app.conversation_store.delete_session(conversation_id)

    session.pop('persona_conversation_id', None)
    session.pop('active_persona', None)

    logger.info("Persona conversation reset successfully")

    return jsonify({
        'message': 'Persona conversation reset'
    })
