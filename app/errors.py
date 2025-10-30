"""
Custom exception classes for Ollama API interactions.

These exceptions map to specific HTTP status codes for proper error handling.
"""


class OllamaConnectionError(Exception):
    """
    Raised when unable to establish connection to Ollama server.

    This typically indicates:
    - Ollama is not running
    - Wrong URL configured
    - Network/firewall issues

    HTTP Status: 503 Service Unavailable
    """
    pass


class OllamaTimeoutError(Exception):
    """
    Raised when Ollama request exceeds timeout threshold (120 seconds).

    This typically indicates:
    - Model is too large for available RAM
    - System resources exhausted
    - Ollama is hung/unresponsive

    HTTP Status: 504 Gateway Timeout
    """
    pass


class OllamaModelNotFoundError(Exception):
    """
    Raised when the requested model is not installed locally.

    This typically indicates:
    - Model not pulled via 'ollama pull <model>'
    - Typo in model name
    - Model was deleted

    HTTP Status: 404 Not Found
    """
    pass


class OllamaAPIError(Exception):
    """
    Raised when Ollama returns an error response or unexpected format.

    This is a catch-all for:
    - Invalid API responses
    - Ollama version mismatches
    - API endpoint errors
    - Unexpected errors

    HTTP Status: 502 Bad Gateway
    """
    pass
