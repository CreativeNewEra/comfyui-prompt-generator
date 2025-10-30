"""
Model Management Routes

Handles Ollama model queries and configuration.

Routes:
    GET /models - List available Ollama models
"""

from flask import Blueprint, jsonify
import requests
from requests.exceptions import ConnectionError, RequestException
import logging

bp = Blueprint('models', __name__)
logger = logging.getLogger(__name__)


@bp.route('/models', methods=['GET'])
def get_models():
    """
    Return available Ollama models installed on the system.

    Queries the Ollama API /api/tags endpoint to retrieve a list of
    all locally installed models. This allows users to select which
    model they want to use for prompt generation.

    Returns:
        JSON: List of model names and default model
        {
            "models": ["qwen3:latest", "llama2", "mistral", ...],
            "default": "qwen3:latest"
        }

    Status Codes:
        200: Success
        503: Cannot connect to Ollama
        502: Ollama API error

    Example Response:
        {
            "models": ["qwen3:latest", "llama2:latest", "mistral:latest"],
            "default": "qwen3:latest"
        }
    """
    logger.info("Received /models request")

    from app.config import config
    from app.errors import OllamaConnectionError, OllamaTimeoutError, OllamaAPIError

    try:
        # Get base URL for Ollama (remove /api/generate path)
        ollama_base_url = config.OLLAMA_URL.rsplit('/api', 1)[0]
        tags_url = f"{ollama_base_url}/api/tags"

        logger.debug(f"Fetching models from {tags_url}")
        response = requests.get(tags_url, timeout=10)
        response.raise_for_status()

        result = response.json()

        # Extract model names from the response
        # Ollama returns: {"models": [{"name": "model:tag", ...}, ...]}
        models = []
        if 'models' in result:
            models = [model['name'] for model in result['models']]

        logger.info(f"Found {len(models)} installed Ollama models")

        return jsonify({
            'models': models,
            'default': config.OLLAMA_MODEL
        })

    except ConnectionError:
        logger.error(f"Failed to connect to Ollama at {tags_url}")
        raise OllamaConnectionError(
            f"Cannot connect to Ollama to fetch models.\n\n"
            f"To fix this:\n"
            f"1. Start Ollama: ollama serve\n"
            f"2. Verify it's running: curl http://localhost:11434\n"
            f"3. Check your OLLAMA_URL setting in .env"
        )
    except requests.exceptions.Timeout:
        logger.error("Timeout fetching models from Ollama")
        raise OllamaTimeoutError(
            f"Timeout fetching models from Ollama.\n\n"
            f"To fix this:\n"
            f"1. Check Ollama status: ollama ps\n"
            f"2. Try restarting Ollama: pkill ollama && ollama serve"
        )
    except RequestException as e:
        logger.error(f"Request exception when fetching models: {str(e)}")
        raise OllamaAPIError(
            f"Error fetching models from Ollama: {str(e)}\n\n"
            f"To fix this:\n"
            f"1. Verify Ollama is running: curl http://localhost:11434\n"
            f"2. Check network connectivity"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching models: {str(e)}", exc_info=True)
        raise OllamaAPIError(
            f"Unexpected error fetching models: {str(e)}\n\n"
            f"Check application logs: tail -f logs/app.log"
        )
