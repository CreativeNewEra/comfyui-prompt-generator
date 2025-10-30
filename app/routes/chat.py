"""
Chat & Refine Routes

Handles conversational prompt refinement with conversation history.
Provides both streaming and non-streaming modes.

Routes:
    POST /chat - Non-streaming conversational mode
    POST /chat-stream - Streaming conversational mode (SSE)
    POST /reset - Reset conversation history
"""

from flask import Blueprint, jsonify, request, session, current_app
import json
import logging

bp = Blueprint('chat', __name__)
logger = logging.getLogger(__name__)


@bp.route('/chat', methods=['POST'])
def chat():
    """
    Generate prompts using conversational mode (Chat & Refine).

    Maintains conversation history in Flask session to allow iterative
    refinement. Users can have back-and-forth discussion to perfect prompts.
    Session automatically trims to last 20 messages to prevent bloat.

    Request JSON:
        {
            "message": "user message text",
            "model": "flux" or "sdxl",
            "style": "preset name or None",
            "artist": "preset name or None",
            "composition": "preset name or None",
            "lighting": "preset name or None"
        }

    Returns:
        JSON: Generated response and model type
        {
            "result": "AI response text",
            "model": "flux"
        }

    Status Codes:
        200: Success
        400: Missing/invalid message
        503: Ollama connection failed
        504: Ollama timeout
        404: Model not found
        502: Ollama API error

    Notes:
        - Conversation history persisted in server-side store keyed by session ID
        - Session cookie keeps only the conversation identifier
        - Changing model resets the stored conversation
        - History limited to 21 messages (system + 20 exchanges)
        - Each message saved to database with mode='chat'
    """
    logger.info("Received /chat request")

    # Validate request has JSON data
    data = request.get_json(silent=True)
    if not data:
        logger.warning("Chat request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    from app.config import config
    from app.presets import load_presets, PRESETS
    from app.utils import CHAT_SYSTEM_PROMPTS, build_hierarchical_prompt
    from app.ollama_client import call_ollama
    from app.database import save_to_history

    user_message = data.get('message', '').strip()
    model_type = data.get('model', 'flux')
    ollama_model = data.get('ollama_model', config.OLLAMA_MODEL)  # Ollama model to use

    # Get preset selections
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')
    selections = data.get('selections')

    hierarchical_message = None
    using_hierarchical = False
    if config.ENABLE_HIERARCHICAL_PRESETS and isinstance(selections, dict) and selections:
        logger.debug("Applying hierarchical selections to chat request")
        presets_data = load_presets()
        hierarchical_message = build_hierarchical_prompt(user_message, selections, presets_data)
        using_hierarchical = bool(hierarchical_message and hierarchical_message.strip())

    if not user_message:
        logger.warning("Chat request with empty message")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a message'
        }), 400

    conversation_id = session.get('conversation_id')
    conversation, stored_model = current_app.conversation_store.get_conversation(conversation_id)

    if stored_model and stored_model != model_type:
        logger.info("Model changed, starting new stored conversation")
        current_app.conversation_store.delete_session(conversation_id)
        conversation_id = None
        conversation = []
        stored_model = None

    if not conversation:
        system_prompt = CHAT_SYSTEM_PROMPTS.get(model_type, CHAT_SYSTEM_PROMPTS['flux'])
        conversation = [{
            "role": "system",
            "content": system_prompt
        }]
        conversation_id = current_app.conversation_store.create_session(model_type, conversation)
        session['conversation_id'] = conversation_id
    else:
        session['conversation_id'] = conversation_id

    logger.debug(f"Chat message preview: {user_message[:50]}...")

    # Initialize full_message with default value (used as fallback when no presets selected)
    full_message = user_message

    if using_hierarchical:
        full_message = hierarchical_message
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
            full_message = f"{user_message}\n\n[Selected presets: {preset_info}]"

    # Add user message
    conversation.append({
        "role": "user",
        "content": full_message
    })

    conversation = current_app.conversation_store.save_messages(conversation_id, conversation, model_type)

    conversation_snapshot = list(conversation)

    # Get response from Ollama
    result = call_ollama(conversation_snapshot, model=ollama_model)

    # Add assistant response to history
    conversation.append({
        "role": "assistant",
        "content": result
    })

    current_app.conversation_store.save_messages(conversation_id, conversation, model_type)
    logger.info("Successfully processed chat message")

    # Save to history
    presets_dict = {
        'style': style,
        'artist': artist,
        'composition': composition,
        'lighting': lighting
    }
    if using_hierarchical:
        presets_dict['hierarchical'] = selections
    save_to_history(user_message, result, model_type, presets_dict, 'chat')

    return jsonify({
        'result': result,
        'model': model_type
    })


@bp.route('/chat-stream', methods=['POST'])
def chat_stream():
    """Conversational mode with streaming - refine ideas back and forth"""
    logger.info("Received /chat-stream request")

    # Validate request has JSON data
    data = request.get_json(silent=True)
    if not data:
        logger.warning("Chat-stream request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    from app.config import config
    from app.presets import load_presets, PRESETS
    from app.utils import CHAT_SYSTEM_PROMPTS, build_hierarchical_prompt
    from app.ollama_client import call_ollama
    from app.database import save_to_history
    from app.errors import OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError, OllamaAPIError

    user_message = data.get('message', '').strip()
    model_type = data.get('model', 'flux')
    ollama_model = data.get('ollama_model', config.OLLAMA_MODEL)  # Ollama model to use

    # Get preset selections
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')
    selections = data.get('selections')

    hierarchical_message = None
    using_hierarchical = False
    if config.ENABLE_HIERARCHICAL_PRESETS and isinstance(selections, dict) and selections:
        logger.debug("Applying hierarchical selections to streaming chat request")
        presets_data = load_presets()
        hierarchical_message = build_hierarchical_prompt(user_message, selections, presets_data)
        using_hierarchical = bool(hierarchical_message and hierarchical_message.strip())

    if not user_message:
        logger.warning("Chat-stream request with empty message")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a message'
        }), 400

    conversation_id = session.get('conversation_id')
    conversation, stored_model = current_app.conversation_store.get_conversation(conversation_id)

    if stored_model and stored_model != model_type:
        logger.info("Model changed, starting new stored conversation")
        current_app.conversation_store.delete_session(conversation_id)
        conversation_id = None
        conversation = []
        stored_model = None

    if not conversation:
        system_prompt = CHAT_SYSTEM_PROMPTS.get(model_type, CHAT_SYSTEM_PROMPTS['flux'])
        conversation = [{
            "role": "system",
            "content": system_prompt
        }]
        conversation_id = current_app.conversation_store.create_session(model_type, conversation)

    session['conversation_id'] = conversation_id

    logger.debug(f"Chat message preview: {user_message[:50]}...")

    # Initialize full_message with default value (used as fallback when no presets selected)
    full_message = user_message

    if using_hierarchical:
        full_message = hierarchical_message
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
            full_message = f"{user_message}\n\n[Selected presets: {preset_info}]"

    conversation.append({
        "role": "user",
        "content": full_message
    })

    conversation = current_app.conversation_store.save_messages(conversation_id, conversation, model_type)

    conversation_snapshot = list(conversation)

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
        nonlocal conversation
        full_response = ""
        try:
            for token in call_ollama(conversation_snapshot, model=ollama_model, stream=True):
                full_response += token
                # Send token as SSE event
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Send completion event
            yield f"data: {json.dumps({'done': True})}\n\n"

            logger.info("Successfully processed streaming chat message")

        except (OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError, OllamaAPIError) as e:
            # Send error event
            yield f"data: {json.dumps({'error': str(e), 'type': type(e).__name__})}\n\n"
            logger.error(f"Error during streaming: {str(e)}")
        except Exception as e:
            # Send generic error event
            yield f"data: {json.dumps({'error': f'Unexpected error: {str(e)}', 'type': 'UnexpectedError'})}\n\n"
            logger.error(f"Unexpected error during streaming: {str(e)}", exc_info=True)
        finally:
            # Update session after streaming completes
            # Note: This happens after the response is sent, so we update via a background task
            if full_response:
                conversation.append({
                    "role": "assistant",
                    "content": full_response
                })

                conversation = current_app.conversation_store.save_messages(conversation_id, conversation, model_type)

                # Save to history after completion
                save_to_history(user_message, full_response, model_type, presets_dict, 'chat')

    return current_app.response_class(generate(), mimetype='text/event-stream')


@bp.route('/reset', methods=['POST'])
def reset():
    """
    Reset the conversation history in chat mode.

    Clears the session conversation and model type, effectively starting
    a fresh conversation. Useful when users want to start over or are
    stuck in an unproductive conversation thread.

    Returns:
        JSON: Confirmation of reset
        {
            "status": "reset"
        }

    Status Codes:
        200: Success (always)
    """
    logger.info("Resetting conversation history")

    conversation_id = session.pop('conversation_id', None)
    if conversation_id:
        current_app.conversation_store.delete_session(conversation_id)
    return jsonify({'status': 'reset'})
