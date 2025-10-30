"""
History Management Routes

Handles prompt generation history retrieval and deletion.

Routes:
    GET /history - Retrieve prompt history with optional search
    DELETE /history/<id> - Delete specific history item
"""

from flask import Blueprint, jsonify, request
import logging

bp = Blueprint('history', __name__)
logger = logging.getLogger(__name__)


@bp.route('/history', methods=['GET'])
def get_prompt_history():
    """
    Retrieve prompt generation history from database.

    Returns up to 200 most recent prompt generations, optionally filtered
    by search query. Searches both user input and generated output fields.

    Query Parameters:
        limit (int, optional): Number of records to return (1-200, default: 50)
        q (str, optional): Search query to filter results

    Returns:
        JSON: List of history records with metadata
        {
            "history": [
                {
                    "id": 123,
                    "timestamp": "2024-01-15T10:30:00",
                    "user_input": "original description",
                    "generated_output": "generated prompt",
                    "model": "flux",
                    "presets": {"style": "Cinematic", ...},
                    "mode": "oneshot"
                },
                ...
            ],
            "count": 10
        }

    Status Codes:
        200: Success
        400: Invalid limit parameter

    Example:
        GET /history?limit=10&q=cyberpunk
    """
    logger.info("Received /history request")

    from app.database import get_history

    limit = request.args.get('limit', 50, type=int)
    search_query = request.args.get('q', None)

    # Validate limit
    if limit < 1 or limit > 200:
        return jsonify({
            'error': 'Invalid limit',
            'message': 'Limit must be between 1 and 200'
        }), 400

    history = get_history(limit=limit, search_query=search_query)

    logger.info(f"Retrieved {len(history)} history records")
    return jsonify({
        'history': history,
        'count': len(history)
    })


@bp.route('/history/<int:history_id>', methods=['DELETE'])
def delete_prompt_history(history_id):
    """
    Delete a specific prompt history record.

    Permanently removes a history item from the database by ID.
    Useful for cleaning up unwanted or test generations.

    URL Parameters:
        history_id (int): Database ID of the history record to delete

    Returns:
        JSON: Confirmation of deletion
        {
            "status": "deleted",
            "id": 123
        }

    Status Codes:
        200: Successfully deleted
        404: History item not found

    Example:
        DELETE /history/123
    """
    logger.info(f"Received request to delete history item {history_id}")

    from app.database import delete_history_item

    success = delete_history_item(history_id)

    if success:
        return jsonify({
            'status': 'deleted',
            'id': history_id
        })
    else:
        return jsonify({
            'error': 'Not found',
            'message': f'History item with ID {history_id} not found'
        }), 404
