"""
Ollama API client for prompt generation.

This module provides all functionality for communicating with the Ollama API,
including connection management, auto-discovery, and streaming support.
"""

import os
import sys
import json
import logging
import socket
import ipaddress
import requests
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import ConnectionError, Timeout, RequestException

from app.config import config
from app.errors import (
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaModelNotFoundError,
    OllamaAPIError
)

# Initialize logger for this module
logger = logging.getLogger(__name__)


def get_ollama_base_url(url: str) -> str:
    """Return the base URL for the Ollama server without the /api suffix.

    Handles URLs with path prefixes correctly by working from right to left.
    Examples:
        'http://localhost:11434/api/generate' -> 'http://localhost:11434'
        'https://example.com/api/ollama/api/generate' -> 'https://example.com/api/ollama'

    Args:
        url: The full Ollama URL (may include /api/generate or /api path)

    Returns:
        str: Base URL without /api suffix, or empty string if url is empty
    """
    if not url:
        return ''

    stripped = url.rstrip('/')

    # Work from right to left to handle prefixed paths correctly
    if stripped.endswith('/api/generate'):
        return stripped[:-len('/api/generate')]
    if stripped.endswith('/api'):
        return stripped[:-len('/api')]

    return stripped


def build_generate_url(base_url: str) -> str:
    """Ensure the provided base URL targets the /api/generate endpoint.

    Args:
        base_url: Base URL or partial URL for Ollama server

    Returns:
        str: Full URL with /api/generate endpoint, or empty string if base_url is empty
    """
    if not base_url:
        return ''

    url = base_url.strip()
    if not url.startswith('http://') and not url.startswith('https://'):
        url = f'http://{url}'

    url = url.rstrip('/')

    if url.endswith('/api/generate'):
        return url
    if url.endswith('/api'):
        return f'{url}/generate'
    if url.endswith('/api/'):
        return f'{url}generate'

    return f'{url}/api/generate'


def check_ollama_connection(base_url: str, timeout: float = 2.0) -> bool:
    """Attempt to contact the Ollama server and confirm it is reachable.

    Validates the response contains Ollama-specific fields to ensure we're
    actually connecting to an Ollama server, not just any HTTP endpoint.

    Args:
        base_url: Base URL of the Ollama server (without /api suffix)
        timeout: Connection timeout in seconds (default: 2.0)

    Returns:
        bool: True if Ollama server is reachable and valid, False otherwise
    """
    if not base_url:
        return False

    test_url = f'{base_url.rstrip("/")}/api/version'
    try:
        response = requests.get(test_url, timeout=timeout)
        response.raise_for_status()

        # Validate this is actually an Ollama server by checking response structure
        try:
            data = response.json()
            # Ollama's /api/version endpoint returns {"version": "..."}
            if not isinstance(data, dict) or 'version' not in data:
                logger.debug(f"Response from {base_url} doesn't match Ollama API structure")
                return False
        except (json.JSONDecodeError, ValueError):
            logger.debug(f"Response from {base_url} is not valid JSON")
            return False

        logger.debug(f"Successfully connected to Ollama at {base_url}")
        return True
    except RequestException as exc:
        logger.debug(f"Ollama connection test failed for {base_url}: {exc}")
        return False


def get_local_ip() -> Optional[str]:
    """Determine the local IP address used for outbound connections.

    Returns:
        str: Local IP address, or None if unable to determine
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # The address is irrelevant; we just need to trigger socket assignment
            sock.connect(('8.8.8.8', 80))
            return sock.getsockname()[0]
    except OSError as exc:
        logger.debug(f"Unable to determine local IP address: {exc}")
        return None


def auto_discover_ollama_server(timeout: float = 0.75, max_workers: int = 20) -> Optional[str]:
    """Scan the local /24 network for an Ollama instance on port 11434.

    Uses parallel scanning to check multiple hosts simultaneously, reducing
    total scan time from ~3 minutes to under 10 seconds for a /24 network.

    Args:
        timeout: Connection timeout per host in seconds (default: 0.75)
        max_workers: Maximum number of parallel connection attempts (default: 20)

    Returns:
        str: Full Ollama URL (with /api/generate) if found, None otherwise
    """
    local_ip = get_local_ip()
    if not local_ip:
        logger.warning("Unable to detect local network configuration for discovery")
        return None

    try:
        network = ipaddress.ip_network(f'{local_ip}/24', strict=False)
    except ValueError as exc:
        logger.debug(f"Invalid network definition for discovery: {exc}")
        return None

    logger.info(f"Scanning {network} for Ollama servers on port 11434 (parallel mode)")

    # Build list of candidate IPs to scan (exclude local IP)
    all_hosts = [str(host) for host in network.hosts()]
    candidates = [ip for ip in all_hosts if ip != local_ip]

    def check_host(host_ip: str) -> Optional[str]:
        """Check a single host for Ollama service."""
        candidate_base = f'http://{host_ip}:11434'
        if check_ollama_connection(candidate_base, timeout=timeout):
            return build_generate_url(candidate_base)
        return None

    # Scan hosts in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_host = {executor.submit(check_host, ip): ip for ip in candidates}

        # Return the first successful result
        for future in as_completed(future_to_host):
            result = future.result()
            if result:
                host_ip = future_to_host[future]
                logger.info(f"Discovered Ollama server at http://{host_ip}:11434")
                # Cancel remaining pending tasks since we found a server
                for f in future_to_host:
                    if not f.done():
                        f.cancel()
                return result

    logger.info("Ollama auto-discovery scan completed without finding a server")
    return None


def _update_ollama_url(new_url: str) -> None:
    """Helper function to update both config.OLLAMA_URL and environment variable.

    Centralizes URL updates to follow DRY principle and maintain consistency.

    Args:
        new_url: The new Ollama URL to set
    """
    config.OLLAMA_URL = new_url
    os.environ['OLLAMA_URL'] = new_url


def ensure_ollama_connection() -> Optional[str]:
    """Confirm Ollama is reachable or prompt the user for updated settings.

    This function performs an interactive connection check on startup. It can
    be disabled by setting OLLAMA_STARTUP_CHECK=false in the .env file for
    non-interactive environments (Docker, systemd).

    Returns:
        str: The validated Ollama URL if connection is successful, None otherwise

    Notes:
        For non-interactive environments (Docker, systemd), set OLLAMA_STARTUP_CHECK=false
        in your environment to skip this check and allow the application to start.
    """
    base_url = get_ollama_base_url(config.OLLAMA_URL)
    if check_ollama_connection(base_url):
        return config.OLLAMA_URL

    logger.warning(
        "Failed to connect to Ollama at %s. You can set OLLAMA_URL in your .env file.",
        config.OLLAMA_URL,
    )

    # Allow bypassing startup check for non-interactive deployments
    if not config.OLLAMA_STARTUP_CHECK:
        logger.info(
            "OLLAMA_STARTUP_CHECK is disabled; continuing startup without Ollama connection."
        )
        return None

    if not sys.stdin.isatty():
        logger.error(
            "Unable to connect to Ollama and standard input is not interactive. "
            "Set OLLAMA_URL correctly in .env or set OLLAMA_STARTUP_CHECK=false to skip this check."
        )
        return None

    print("\nUnable to reach Ollama at the configured URL.")
    print("You can update the address here, or press Enter to keep the current setting.")

    while True:
        user_choice = input(
            "Enter a new Ollama host/IP (e.g. 192.168.1.50:11434), "
            "type 'scan' to search your network, or press Enter to retry: "
        ).strip()

        if user_choice.lower() == 'scan':
            discovered_url = auto_discover_ollama_server()
            if discovered_url:
                _update_ollama_url(discovered_url)
                print(f"Discovered Ollama server at {get_ollama_base_url(discovered_url)}")
                return discovered_url
            print("No Ollama server found during network scan. You can try again or enter an IP manually.")
            continue

        if not user_choice:
            # Retry the currently configured URL once more
            if check_ollama_connection(base_url):
                return config.OLLAMA_URL
            print(
                f"Still unable to reach Ollama at {base_url}. "
                "Provide a new address or type 'scan' to search."
            )
            continue

        new_url = build_generate_url(user_choice)
        new_base = get_ollama_base_url(new_url)
        if check_ollama_connection(new_base):
            _update_ollama_url(new_url)
            print(f"Ollama connection updated to {new_base}")
            return new_url

        print(
            f"Could not connect to Ollama at {new_base}. "
            "Please verify the address or try again."
        )


def call_ollama(messages, model=None, stream=False):
    """
    Call Ollama API to generate text based on conversation messages.

    This is the main interface for communicating with Ollama. It handles
    message formatting, API calls, and error handling. Supports both
    streaming (token-by-token) and synchronous (complete response) modes.

    Args:
        messages (list): List of message dictionaries with 'role' and 'content' keys.
                        Valid roles: 'system', 'user', 'assistant'
                        Example: [
                            {"role": "system", "content": "You are helpful"},
                            {"role": "user", "content": "Generate a prompt"}
                        ]
        model (str, optional): Ollama model name (e.g., 'qwen3:latest', 'llama2').
                              Defaults to config.OLLAMA_MODEL if not specified.
        stream (bool, optional): If True, returns a generator yielding tokens.
                                If False, returns complete response string.
                                Default: False

    Returns:
        str: The complete response from Ollama (if stream=False)
        generator: A generator that yields tokens as they arrive (if stream=True)

    Raises:
        OllamaConnectionError: Cannot connect to Ollama server (check if running)
        OllamaTimeoutError: Request exceeded 120 second timeout (model too large?)
        OllamaModelNotFoundError: Model not installed (need 'ollama pull')
        OllamaAPIError: API returned error or unexpected format

    Notes:
        - Timeout is fixed at 120 seconds
        - Messages are formatted into a single prompt string for Ollama
        - System message is placed at the start, followed by conversation
        - All custom exceptions include troubleshooting guidance
    """
    # Use configured default model if none specified
    if model is None:
        model = config.OLLAMA_MODEL

    logger.debug(f"Attempting to call Ollama API with model: {model}, stream: {stream}")

    # Build the prompt from messages
    # Ollama's /api/generate endpoint expects a single prompt string,
    # so we convert the message list into a formatted conversation
    system_msg = ""
    conversation = ""

    for msg in messages:
        if msg["role"] == "system":
            # Extract system message (instructions for the AI)
            system_msg = msg["content"]
        elif msg["role"] == "user":
            # Format user messages with "User:" prefix
            conversation += f"User: {msg['content']}\n"
        elif msg["role"] == "assistant":
            # Format assistant messages (conversation history)
            conversation += f"Assistant: {msg['content']}\n"

    # Assemble the full prompt
    # System message goes first, then conversation, ending with "Assistant:" to prompt response
    if system_msg:
        full_prompt = f"{system_msg}\n\n{conversation}Assistant:"
    else:
        full_prompt = f"{conversation}Assistant:"

    # Prepare API request payload
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": stream  # Enable/disable streaming mode
    }

    # Route to appropriate handler based on streaming mode
    if stream:
        # Return generator for streaming mode (tokens arrive one by one)
        return _stream_ollama_response(payload, model)
    else:
        # Return complete response for synchronous mode
        return _call_ollama_sync(payload, model)


def _stream_ollama_response(payload, model):
    """
    Generator function that streams tokens from Ollama in real-time.

    This function makes a streaming HTTP request to Ollama and yields tokens
    as they arrive. Used for the /generate-stream and /chat-stream endpoints
    to provide responsive, real-time feedback to users.

    Args:
        payload (dict): Request payload containing 'model', 'prompt', and 'stream'
        model (str): Model name for inclusion in error messages

    Yields:
        str: Individual tokens (text fragments) as they arrive from Ollama

    Raises:
        OllamaConnectionError: Cannot connect to Ollama server
        OllamaTimeoutError: Request exceeded 120 second timeout
        OllamaModelNotFoundError: Model not installed locally
        OllamaAPIError: API returned error or malformed response

    Notes:
        - Processes response line-by-line as JSON chunks
        - Each chunk contains a 'response' field (token) and 'done' flag
        - Continues until 'done': true is received
        - Skips malformed JSON lines with warning instead of failing
    """
    try:
        logger.debug(f"Sending streaming request to Ollama at {config.OLLAMA_URL}")
        # stream=True enables line-by-line reading, timeout prevents hanging
        response = requests.post(config.OLLAMA_URL, json=payload, stream=True, timeout=120)

        # Check for HTTP 404 - could be model not found OR endpoint not found
        if response.status_code == 404:
            error_detail = response.json().get('error', '') if response.headers.get('content-type', '').startswith('application/json') else ''
            if 'model' in error_detail.lower() or 'not found' in error_detail.lower():
                logger.error(f"Ollama model not found: {model}")
                raise OllamaModelNotFoundError(
                    f"Model '{model}' is not installed.\n\n"
                    f"To fix this, run:\n"
                    f"  ollama pull {model}\n\n"
                    f"To see available models, visit: https://ollama.com/library\n"
                    f"To list installed models, run: ollama list"
                )
            logger.error(f"Ollama API endpoint not found: {error_detail}")
            raise OllamaAPIError(
                f"Ollama API endpoint not found.\n\n"
                f"To fix this:\n"
                f"1. Verify Ollama is running: curl http://localhost:11434\n"
                f"2. Check OLLAMA_URL in .env (current: {config.OLLAMA_URL})\n"
                f"3. Update Ollama to latest version: curl -fsSL https://ollama.com/install.sh | sh\n\n"
                f"Error details: {error_detail}"
            )

        # Raise for other HTTP errors (non-404)
        response.raise_for_status()

        # Stream the response line by line
        # Ollama returns newline-delimited JSON (NDJSON) format
        for line in response.iter_lines():
            if line:  # Skip empty lines
                try:
                    # Each line is a JSON object with response token and metadata
                    chunk = json.loads(line)

                    # Check for error field in chunk (API-level errors)
                    if 'error' in chunk:
                        logger.error(f"Ollama API returned error: {chunk['error']}")
                        raise OllamaAPIError(f"Ollama API error: {chunk['error']}")

                    # Yield the token if present (incremental text generation)
                    if 'response' in chunk:
                        yield chunk['response']

                    # Check if generation is complete
                    # Final chunk has 'done': true and includes metadata (timing, etc.)
                    if chunk.get('done', False):
                        logger.debug("Streaming completed successfully")
                        break

                except json.JSONDecodeError:
                    # Don't fail on malformed lines, just log and continue
                    # This provides resilience against network issues
                    logger.warning(f"Failed to parse streaming chunk: {line}")
                    continue

    except Timeout:
        logger.error(f"Ollama request timed out after 120 seconds for model: {model}")
        raise OllamaTimeoutError(
            f"Request timed out after 120 seconds.\n\n"
            f"To fix this:\n"
            f"1. Try a smaller/faster model: ollama pull qwen2.5:0.5b\n"
            f"2. Check Ollama status: ollama ps\n"
            f"3. Ensure your system has enough RAM (8GB+ recommended)\n"
            f"4. Try restarting Ollama: pkill ollama && ollama serve\n\n"
            f"Current model '{model}' may be too large for your system."
        )
    except ConnectionError:
        logger.error(f"Failed to connect to Ollama at {config.OLLAMA_URL}")
        raise OllamaConnectionError(
            f"Cannot connect to Ollama at {config.OLLAMA_URL}\n\n"
            f"To fix this:\n"
            f"1. Start Ollama: ollama serve\n"
            f"2. Verify it's running: curl {config.OLLAMA_URL.rsplit('/api', 1)[0]}\n"
            f"3. Check your OLLAMA_URL setting in .env\n\n"
            f"For installation help: https://ollama.com/download"
        )
    except (OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError, OllamaAPIError):
        # Re-raise our custom exceptions (already logged)
        raise
    except RequestException as e:
        logger.error(f"Request exception when calling Ollama: {str(e)}")
        raise OllamaAPIError(
            f"Network error communicating with Ollama: {str(e)}\n\n"
            f"To fix this:\n"
            f"1. Check network connectivity to {config.OLLAMA_URL}\n"
            f"2. Verify Ollama is running: curl http://localhost:11434\n"
            f"3. Check firewall settings if using remote Ollama"
        )
    except Exception as e:
        logger.error(f"Unexpected error when streaming from Ollama: {str(e)}", exc_info=True)
        raise OllamaAPIError(
            f"Unexpected error: {str(e)}\n\n"
            f"To troubleshoot:\n"
            f"1. Check application logs: tail -f logs/app.log\n"
            f"2. Verify Ollama is working: ollama run {model} \"test\"\n"
            f"3. Report issue with logs at: https://github.com/CreativeNewEra/comfyui-prompt-generator/issues"
        )


def _call_ollama_sync(payload, model):
    """
    Synchronous call to Ollama (non-streaming).

    Makes a complete HTTP POST request to Ollama and waits for the full response
    before returning. Used for the /generate and /chat endpoints.

    Args:
        payload (dict): The request payload containing 'model', 'prompt', and 'stream'
        model (str): Model name for error messages

    Returns:
        str: The complete response from Ollama

    Raises:
        OllamaConnectionError: Cannot connect to Ollama server
        OllamaTimeoutError: Request exceeded 120 second timeout
        OllamaModelNotFoundError: Model not installed locally
        OllamaAPIError: API returned error or unexpected format
    """
    try:
        logger.debug(f"Sending request to Ollama at {config.OLLAMA_URL}")
        response = requests.post(config.OLLAMA_URL, json=payload, timeout=120)

        # Check for specific error status codes
        if response.status_code == 404:
            error_detail = response.json().get('error', '') if response.headers.get('content-type', '').startswith('application/json') else ''
            if 'model' in error_detail.lower() or 'not found' in error_detail.lower():
                logger.error(f"Ollama model not found: {model}")
                raise OllamaModelNotFoundError(
                    f"Model '{model}' is not installed.\n\n"
                    f"To fix this, run:\n"
                    f"  ollama pull {model}\n\n"
                    f"To see available models, visit: https://ollama.com/library\n"
                    f"To list installed models, run: ollama list"
                )
            logger.error(f"Ollama API endpoint not found: {error_detail}")
            raise OllamaAPIError(
                f"Ollama API endpoint not found.\n\n"
                f"To fix this:\n"
                f"1. Verify Ollama is running: curl http://localhost:11434\n"
                f"2. Check OLLAMA_URL in .env (current: {config.OLLAMA_URL})\n"
                f"3. Update Ollama to latest version: curl -fsSL https://ollama.com/install.sh | sh\n\n"
                f"Error details: {error_detail}"
            )

        # Raise for other HTTP errors
        response.raise_for_status()

        # Parse response
        result = response.json()

        # Check if response contains an error field
        if 'error' in result:
            logger.error(f"Ollama API returned error: {result['error']}")
            raise OllamaAPIError(
                f"Ollama API error: {result['error']}\n\n"
                f"To troubleshoot:\n"
                f"1. Check Ollama logs: journalctl -u ollama -f (Linux) or Console.app (Mac)\n"
                f"2. Verify model is working: ollama run {model} \"test\"\n"
                f"3. Check available resources: ollama ps\n"
                f"4. Try restarting Ollama service"
            )

        # Return the generated response
        if 'response' in result:
            logger.debug("Successfully received response from Ollama")
            return result['response']
        else:
            logger.error("Unexpected response format from Ollama API")
            raise OllamaAPIError(
                f"Unexpected response format from Ollama.\n\n"
                f"To fix this:\n"
                f"1. Update Ollama: curl -fsSL https://ollama.com/install.sh | sh\n"
                f"2. Verify API is working: curl {config.OLLAMA_URL.rsplit('/api', 1)[0]}/api/tags\n"
                f"3. Check logs: tail -f logs/app.log\n\n"
                f"The Ollama API may have changed or be misconfigured."
            )

    except Timeout:
        logger.error(f"Ollama request timed out after 120 seconds for model: {model}")
        raise OllamaTimeoutError(
            f"Request timed out after 120 seconds.\n\n"
            f"To fix this:\n"
            f"1. Try a smaller/faster model: ollama pull qwen2.5:0.5b\n"
            f"2. Check Ollama status: ollama ps\n"
            f"3. Ensure your system has enough RAM (8GB+ recommended)\n"
            f"4. Try restarting Ollama: pkill ollama && ollama serve\n\n"
            f"Current model '{model}' may be too large for your system."
        )
    except ConnectionError:
        logger.error(f"Failed to connect to Ollama at {config.OLLAMA_URL}")
        raise OllamaConnectionError(
            f"Cannot connect to Ollama at {config.OLLAMA_URL}\n\n"
            f"To fix this:\n"
            f"1. Start Ollama: ollama serve\n"
            f"2. Verify it's running: curl {config.OLLAMA_URL.rsplit('/api', 1)[0]}\n"
            f"3. Check your OLLAMA_URL setting in .env\n\n"
            f"For installation help: https://ollama.com/download"
        )
    except (OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError, OllamaAPIError):
        # Re-raise our custom exceptions (already logged)
        raise
    except RequestException as e:
        logger.error(f"Request exception when calling Ollama: {str(e)}")
        raise OllamaAPIError(
            f"Network error communicating with Ollama: {str(e)}\n\n"
            f"To fix this:\n"
            f"1. Check network connectivity to {config.OLLAMA_URL}\n"
            f"2. Verify Ollama is running: curl http://localhost:11434\n"
            f"3. Check firewall settings if using remote Ollama"
        )
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON response from Ollama API")
        raise OllamaAPIError(
            f"Invalid response from Ollama (not valid JSON).\n\n"
            f"To fix this:\n"
            f"1. Update Ollama: curl -fsSL https://ollama.com/install.sh | sh\n"
            f"2. Restart Ollama service\n"
            f"3. Verify API endpoint: curl {config.OLLAMA_URL.rsplit('/api', 1)[0]}/api/version\n\n"
            f"This usually indicates an Ollama version mismatch or corruption."
        )
    except KeyError as e:
        logger.error(f"Missing expected field in Ollama response: {str(e)}")
        raise OllamaAPIError(
            f"Incomplete response from Ollama (missing field: {str(e)}).\n\n"
            f"To fix this:\n"
            f"1. Update Ollama to latest version\n"
            f"2. Try a different model: ollama pull qwen2.5:latest\n"
            f"3. Check Ollama status: ollama ps"
        )
    except Exception as e:
        logger.error(f"Unexpected error when calling Ollama: {str(e)}", exc_info=True)
        raise OllamaAPIError(
            f"Unexpected error: {str(e)}\n\n"
            f"To troubleshoot:\n"
            f"1. Check application logs: tail -f logs/app.log\n"
            f"2. Verify Ollama is working: ollama run {model} \"test\"\n"
            f"3. Report issue with logs at: https://github.com/CreativeNewEra/comfyui-prompt-generator/issues"
        )
