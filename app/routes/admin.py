"""
Admin Routes

Handles administrative endpoints requiring special authorization.

Routes:
    POST /admin/reload-prompts - Reload system prompts from files

Security:
    Access requires either:
    - Valid ADMIN_API_KEY via X-Admin-API-Key header or admin_api_key query param
    - Request from loopback/localhost IP
    - Request from whitelisted IP (ADMIN_ALLOWED_IPS)
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)


@bp.route('/admin/reload-prompts', methods=['POST'])
def reload_prompts():
    """
    Reload system prompts from text files without restarting the server.

    This endpoint allows administrators to reload all system prompts
    (SDXL oneshot, Flux oneshot, SDXL chat, Flux chat) from their
    respective text files in the prompts/ directory. This enables
    rapid iteration on prompt engineering without server downtime.

    Security Note:
        Access requires either a valid ADMIN_API_KEY provided via the
        X-Admin-API-Key header (or admin_api_key query param) or that the
        request originates from a loopback/localhost IP address. Additional
        IPs can be whitelisted through the ADMIN_ALLOWED_IPS environment
        variable.

    Returns:
        JSON: Success message with list of reloaded prompts

    Example Response:
        {
            "success": true,
            "message": "System prompts reloaded successfully",
            "reloaded": ["sdxl_oneshot", "flux_oneshot", "sdxl_chat", "flux_chat"]
        }

    Example curl:
        curl -X POST http://localhost:5000/admin/reload-prompts
    """
    from app.auth import authorize_admin_request
    from app.utils import reload_system_prompts

    authorized, client_ip, forwarded_for, reason = authorize_admin_request(request)
    if not authorized:
        logger.warning(
            "Denied /admin/reload-prompts request from %s (forwarded_for=%s, reason=%s)",
            client_ip or 'unknown',
            forwarded_for or 'none',
            reason,
        )
        return jsonify({
            'success': False,
            'error': 'forbidden',
            'message': 'Unauthorized access to admin endpoint'
        }), 403

    logger.warning(
        "Authorized system prompts reload request via /admin/reload-prompts endpoint from %s",
        client_ip or 'unknown'
    )

    try:
        # Reload prompts from files and update global variables
        new_system_prompts, new_chat_prompts = reload_system_prompts()

        reloaded_prompts = list(new_system_prompts.keys()) + [f"{k}_chat" for k in new_chat_prompts.keys()]

        logger.info(f"System prompts reloaded successfully: {reloaded_prompts}")

        return jsonify({
            'success': True,
            'message': 'System prompts reloaded successfully',
            'reloaded': reloaded_prompts,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })

    except Exception as e:
        logger.error(f"Failed to reload system prompts: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to reload prompts',
            'message': str(e)
        }), 500
