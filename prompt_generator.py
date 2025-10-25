#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt Generator Web App
Talks to local Ollama to generate detailed prompts for ComfyUI

Configuration:
    You can customize the application by creating a .env file in the root directory.
    Copy .env.example to .env and modify the values:
    - OLLAMA_URL: URL for the Ollama API endpoint
    - OLLAMA_MODEL: Default model to use (e.g., qwen3:latest, llama2, mistral)
    - FLASK_PORT: Port for the web server (default: 5000)
    - FLASK_DEBUG: Debug mode (true/false)
    - FLASK_SECRET_KEY: Secret key for session management (generate a random one for production)
"""

from flask import Flask, render_template, request, jsonify, session
import requests
import json
import secrets
import os
import sys
import socket
import ipaddress
import logging
from typing import Optional
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from requests.exceptions import ConnectionError, Timeout, RequestException
import sqlite3
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables from .env file if it exists
# This allows users to customize configuration without modifying code
load_dotenv()

# ============================================================================
# Application Configuration
# ============================================================================
# All configuration values can be set via environment variables in .env file.
# See .env.example for available options and descriptions.

# Ollama API endpoint URL for prompt generation
# Default: http://localhost:11434/api/generate
# Can be customized to point to remote Ollama instances
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434/api/generate')

# Default Ollama model to use for prompt generation
# Common options: qwen3:latest, llama2, mistral, phi
# Must be installed locally: ollama pull <model-name>
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:latest')

# Flask web server port
# Default: 5000. Change if port is already in use
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))

# Flask debug mode - enables detailed error pages and auto-reload
# Set to 'false' in production for security
# Accepts: true/false, 1/0, yes/no (case insensitive)
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() in ('true', '1', 'yes')

# Flask secret key for session management and cookie signing
# Generated randomly if not provided. Set a stable value in production
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))

# Logging level for application logs
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
# Default: INFO provides good balance of detail
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging():
    """
    Configure application logging with file rotation and console output.

    Sets up two handlers:
    1. File handler: Rotates logs at 10MB, keeps 5 backups in logs/app.log
    2. Console handler: Outputs to stderr for real-time monitoring

    Both handlers use the same format and log level (from LOG_LEVEL config).
    Werkzeug (Flask dev server) logging is reduced to WARNING to minimize noise.

    Returns:
        logging.Logger: Configured logger instance for this module

    Notes:
        - Log files are created in ./logs/ directory (auto-created if missing)
        - Format: timestamp - module - level - message
        - Rotation prevents unbounded disk usage
    """
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Convert string log level to logging constant
    numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Setup file handler with rotation (10MB max, keep 5 backups)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Reduce noise from werkzeug (Flask's dev server)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    return logging.getLogger(__name__)

# Initialize logging system
logger = setup_logging()


# ============================================================================
# Ollama Connection Helpers
# ============================================================================

def get_ollama_base_url(url: str) -> str:
    """Return the base URL for the Ollama server without the /api suffix.

    Handles URLs with path prefixes correctly by working from right to left.
    Examples:
        'http://localhost:11434/api/generate' -> 'http://localhost:11434'
        'https://example.com/api/ollama/api/generate' -> 'https://example.com/api/ollama'
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
    """Ensure the provided base URL targets the /api/generate endpoint."""
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
    """Determine the local IP address used for outbound connections."""
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
        timeout: Connection timeout per host in seconds
        max_workers: Maximum number of parallel connection attempts
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
    """Helper function to update both global OLLAMA_URL and environment variable.

    Centralizes URL updates to follow DRY principle and maintain consistency.
    """
    global OLLAMA_URL
    OLLAMA_URL = new_url
    os.environ['OLLAMA_URL'] = new_url


def ensure_ollama_connection() -> Optional[str]:
    """Confirm Ollama is reachable or prompt the user for updated settings.

    Returns:
        The validated Ollama URL if connection is successful, None otherwise.

    For non-interactive environments (Docker, systemd), set OLLAMA_STARTUP_CHECK=false
    in your environment to skip this check and allow the application to start.
    """
    global OLLAMA_URL

    base_url = get_ollama_base_url(OLLAMA_URL)
    if check_ollama_connection(base_url):
        return OLLAMA_URL

    logger.warning(
        "Failed to connect to Ollama at %s. You can set OLLAMA_URL in your .env file.",
        OLLAMA_URL,
    )

    # Allow bypassing startup check for non-interactive deployments
    if os.getenv('OLLAMA_STARTUP_CHECK', 'true').lower() == 'false':
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
                return OLLAMA_URL
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


# Initialize Flask application
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY  # Required for session management

# ============================================================================
# Database Configuration
# ============================================================================
# SQLite database for storing prompt generation history
# Allows users to browse, search, and reuse previous prompts
DB_PATH = 'prompt_history.db'


def init_db():
    """
    Initialize the SQLite database and create tables if they don't exist.

    Creates the prompt_history table with the following schema:
    - id: Auto-incrementing primary key
    - timestamp: ISO format UTC timestamp of generation
    - user_input: Original user description/request
    - generated_output: AI-generated prompt result
    - model: Model type used (flux/sdxl)
    - presets: JSON string of preset selections
    - mode: Generation mode (oneshot/chat)

    This function is idempotent - safe to call multiple times.
    Creates database file if it doesn't exist.
    """
    logger.info("Initializing prompt history database")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompt_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_input TEXT NOT NULL,
            generated_output TEXT NOT NULL,
            model TEXT NOT NULL,
            presets TEXT,
            mode TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


def save_to_history(user_input, output, model, presets, mode):
    """
    Save a generated prompt to the history database

    Args:
        user_input: The user's input text
        output: The generated prompt output
        model: The model type (flux or sdxl)
        presets: Dictionary of preset selections
        mode: The generation mode (oneshot or chat)

    Returns:
        int: The ID of the inserted record, or None if failed
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        timestamp = datetime.now(datetime.UTC).isoformat()
        presets_json = json.dumps(presets)

        cursor.execute('''
            INSERT INTO prompt_history (timestamp, user_input, generated_output, model, presets, mode)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, user_input, output, model, presets_json, mode))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.debug(f"Saved prompt to history with ID: {record_id}")
        return record_id
    except Exception as e:
        logger.error(f"Failed to save to history: {str(e)}")
        return None


def get_history(limit=50, search_query=None):
    """
    Retrieve prompt history from the database

    Args:
        limit: Maximum number of records to return (default: 50)
        search_query: Optional search string to filter results

    Returns:
        list: List of history records as dictionaries
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        if search_query:
            # Search in user_input and generated_output
            cursor.execute('''
                SELECT id, timestamp, user_input, generated_output, model, presets, mode
                FROM prompt_history
                WHERE user_input LIKE ? OR generated_output LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (f'%{search_query}%', f'%{search_query}%', limit))
        else:
            cursor.execute('''
                SELECT id, timestamp, user_input, generated_output, model, presets, mode
                FROM prompt_history
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        # Convert rows to dictionaries
        history = []
        for row in rows:
            history.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'user_input': row['user_input'],
                'generated_output': row['generated_output'],
                'model': row['model'],
                'presets': json.loads(row['presets']) if row['presets'] else {},
                'mode': row['mode']
            })

        logger.debug(f"Retrieved {len(history)} history records")
        return history
    except Exception as e:
        logger.error(f"Failed to retrieve history: {str(e)}")
        return []


def delete_history_item(item_id):
    """
    Delete a specific history item from the database

    Args:
        item_id: The ID of the history item to delete

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM prompt_history WHERE id = ?', (item_id,))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if deleted:
            logger.info(f"Deleted history item with ID: {item_id}")
        else:
            logger.warning(f"No history item found with ID: {item_id}")

        return deleted
    except Exception as e:
        logger.error(f"Failed to delete history item: {str(e)}")
        return False


# ============================================================================
# Custom Exception Classes
# ============================================================================
# These exceptions provide granular error handling for Ollama API interactions.
# Each exception type maps to a specific HTTP error handler with appropriate
# status codes and user-friendly error messages.


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


# ============================================================================
# Preset System
# ============================================================================
# Curated preset options that users can combine to enhance their prompts.
# Each category provides dropdown options in the UI. When selected (not "None"),
# the preset text is incorporated into the AI prompt generation context.
#
# Structure:
#   PRESETS = {
#       "category_name": {
#           "Display Name": "prompt text/tags to inject",
#           ...
#       },
#       ...
#   }
#
# All presets default to "None" (empty string), making them optional.
# Users can mix and match presets across categories for creative control.
# The AI model weaves these elements naturally into the final prompt.

PRESETS = {
    # Visual styles and artistic approaches
    # Defines the overall aesthetic and rendering style
    "styles": {
        "None": "",
        "Cinematic": "cinematic, dramatic, movie still, film grain",
        "Anime": "anime style, manga, cel shaded, vibrant colors",
        "Photorealistic": "photorealistic, highly detailed, 8k uhd, dslr, high quality",
        "Oil Painting": "oil painting, brushstrokes, traditional art, painterly",
        "Digital Art": "digital art, concept art, detailed, artstation trending",
        "Watercolor": "watercolor painting, soft colors, artistic, flowing",
        "Cyberpunk": "cyberpunk, neon lights, futuristic, dystopian, tech noir",
        "Fantasy Art": "fantasy art, magical, epic, detailed, ethereal",
        "Comic Book": "comic book style, bold lines, halftone dots, pop art",
        "Minimalist": "minimalist, clean, simple, modern, elegant",
        "Surreal": "surreal, dreamlike, abstract, unusual, imaginative",
        "Vintage": "vintage, retro, nostalgic, aged, classic",
        "3D Render": "3d render, octane render, unreal engine, ray tracing",
        "Pencil Sketch": "pencil sketch, graphite, hand drawn, detailed shading"
    },

    # Artist and photographer styles
    # Emulates the distinctive style of famous artists and photographers
    # Helps achieve specific visual signatures and techniques
    "artists": {
        "None": "",
        "Greg Rutkowski": "in the style of Greg Rutkowski",
        "Artgerm": "in the style of Artgerm",
        "Alphonse Mucha": "in the style of Alphonse Mucha, art nouveau",
        "H.R. Giger": "in the style of H.R. Giger, biomechanical",
        "Hayao Miyazaki": "Studio Ghibli style, Hayao Miyazaki",
        "Ross Tran": "in the style of Ross Tran",
        "Loish": "in the style of Loish",
        "Makoto Shinkai": "in the style of Makoto Shinkai",
        "James Gurney": "in the style of James Gurney",
        "Ansel Adams": "Ansel Adams photography style",
        "Annie Leibovitz": "Annie Leibovitz portrait photography style",
        "Steve McCurry": "Steve McCurry documentary photography style",
        "Peter Lindbergh": "Peter Lindbergh fashion photography style",
        "Sebastião Salgado": "Sebastião Salgado black and white photography",
        "Irving Penn": "Irving Penn studio photography style",
        "Moebius": "in the style of Moebius, detailed linework",
        "Simon Stålenhag": "in the style of Simon Stålenhag",
        "Zdzisław Beksiński": "in the style of Zdzisław Beksiński, dystopian"
    },

    # Camera angles and framing composition
    # Controls how the subject is positioned and framed in the image
    # Affects perspective, viewer engagement, and visual hierarchy
    "composition": {
        "None": "",
        "Portrait": "portrait composition, centered subject",
        "Landscape": "landscape composition, wide view",
        "Close-up": "close-up shot, detailed, intimate",
        "Wide Shot": "wide shot, establishing shot, full scene",
        "Medium Shot": "medium shot, waist up, balanced framing",
        "Extreme Close-up": "extreme close-up, macro detail",
        "Bird's Eye View": "bird's eye view, top-down perspective, aerial view",
        "Low Angle": "low angle shot, looking up, dramatic perspective",
        "High Angle": "high angle shot, looking down",
        "Dutch Angle": "dutch angle, tilted, dynamic composition",
        "Rule of Thirds": "rule of thirds composition, balanced",
        "Symmetrical": "symmetrical composition, centered, balanced",
        "Leading Lines": "leading lines composition, depth, perspective",
        "Frame within Frame": "frame within frame composition",
        "Golden Ratio": "golden ratio composition, fibonacci spiral"
    },

    # Lighting conditions and techniques
    # Defines the mood, atmosphere, and time of day
    # Critical for achieving professional, cinematic, or artistic looks
    "lighting": {
        "None": "",
        "Golden Hour": "golden hour lighting, warm, soft sunlight",
        "Blue Hour": "blue hour lighting, cool tones, twilight",
        "Studio Lighting": "professional studio lighting, three point lighting",
        "Dramatic Shadows": "dramatic shadows, high contrast, chiaroscuro",
        "Soft Diffused": "soft diffused lighting, even, flattering",
        "Neon Lighting": "neon lighting, vibrant colors, glowing",
        "Candlelight": "candlelight, warm glow, intimate atmosphere",
        "Backlit": "backlit, rim lighting, silhouette, halo effect",
        "Natural Window Light": "natural window light, soft, directional",
        "Harsh Sunlight": "harsh sunlight, strong shadows, high contrast",
        "Overcast": "overcast lighting, soft shadows, even illumination",
        "Volumetric Lighting": "volumetric lighting, god rays, atmospheric",
        "Moonlight": "moonlight, cool tones, mysterious atmosphere",
        "Fire Light": "firelight, warm orange glow, flickering",
        "Underwater Light": "underwater lighting, caustics, diffused"
    }
}

# ============================================================================
# Model-Specific System Prompts
# ============================================================================
# Different AI image generation models have different prompting requirements.
# These system prompts instruct the Ollama LLM on how to format output
# appropriately for each model type.
#
# SDXL (Stable Diffusion XL):
#   - Requires quality tags and structured format
#   - Needs separate negative prompt for things to avoid
#   - Uses comma-separated tag style prompts
#
# Flux:
#   - Prefers natural language descriptions
#   - No need for quality tags or negative prompts
#   - Works best with conversational, detailed narratives
#
# When adding new models, define their optimal prompting strategy here.

SYSTEM_PROMPTS = {
    "sdxl": """You are an expert prompt engineer for Stable Diffusion XL (SDXL). When users describe an image idea, you expand it into a detailed, effective prompt.

The user may provide preset selections for style, artist/photographer, composition, and lighting. When these are provided, incorporate them naturally into the prompt.

SDXL works best with:
- Natural language descriptions with rich details
- Quality tags like: masterpiece, best quality, highly detailed, sharp focus, 8k
- Specific details about: subject, composition, lighting, camera angle, art style, mood, colors
- Negative prompts to avoid unwanted elements

Format your response as:
PROMPT: [detailed positive prompt incorporating any presets]
NEGATIVE: [negative prompt with things to avoid]

Be creative, specific, and detailed. Weave the preset selections naturally into the description.""",

    "flux": """You are an expert prompt engineer for Flux models. When users describe an image idea, you expand it into a detailed, effective prompt.

The user may provide preset selections for style, artist/photographer, composition, and lighting. When these are provided, incorporate them naturally and seamlessly into the prompt description.

Flux models work best with:
- Natural language, conversational style prompts
- Very detailed scene descriptions
- Specific lighting and atmospheric details
- Camera angles and composition details
- Art style and mood descriptions
- No need for quality tags or negative prompts (Flux ignores them)

Format your response as:
PROMPT: [single detailed natural language prompt incorporating any presets naturally]

Be extremely descriptive and creative. Write like you're describing a photograph or painting in detail. Integrate the preset selections seamlessly into the narrative."""
}

# ============================================================================
# Ollama API Integration
# ============================================================================

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
                              Defaults to OLLAMA_MODEL from config.
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
        model = OLLAMA_MODEL

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
        logger.debug(f"Sending streaming request to Ollama at {OLLAMA_URL}")
        # stream=True enables line-by-line reading, timeout prevents hanging
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120)

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
                f"2. Check OLLAMA_URL in .env (current: {OLLAMA_URL})\n"
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
        logger.error(f"Failed to connect to Ollama at {OLLAMA_URL}")
        raise OllamaConnectionError(
            f"Cannot connect to Ollama at {OLLAMA_URL}\n\n"
            f"To fix this:\n"
            f"1. Start Ollama: ollama serve\n"
            f"2. Verify it's running: curl {OLLAMA_URL.rsplit('/api', 1)[0]}\n"
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
            f"1. Check network connectivity to {OLLAMA_URL}\n"
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
    Synchronous call to Ollama (non-streaming)

    Args:
        payload: The request payload
        model: Model name for error messages

    Returns:
        str: The complete response from Ollama
    """
    try:
        logger.debug(f"Sending request to Ollama at {OLLAMA_URL}")
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)

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
                f"2. Check OLLAMA_URL in .env (current: {OLLAMA_URL})\n"
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
                f"2. Verify API is working: curl {OLLAMA_URL.rsplit('/api', 1)[0]}/api/tags\n"
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
        logger.error(f"Failed to connect to Ollama at {OLLAMA_URL}")
        raise OllamaConnectionError(
            f"Cannot connect to Ollama at {OLLAMA_URL}\n\n"
            f"To fix this:\n"
            f"1. Start Ollama: ollama serve\n"
            f"2. Verify it's running: curl {OLLAMA_URL.rsplit('/api', 1)[0]}\n"
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
            f"1. Check network connectivity to {OLLAMA_URL}\n"
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
            f"3. Verify API endpoint: curl {OLLAMA_URL.rsplit('/api', 1)[0]}/api/version\n\n"
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

# ============================================================================
# Flask Error Handlers
# ============================================================================
# These handlers catch exceptions and return consistent JSON error responses.
# All error responses include: error, message, status, and optionally type.
# Custom Ollama exceptions (defined above) have dedicated handlers.

@app.errorhandler(400)
def bad_request_error(error):
    """
    Handle HTTP 400 Bad Request errors.

    Triggered by malformed requests, missing parameters, or validation failures.

    Args:
        error: The error object from Flask

    Returns:
        tuple: (JSON response dict, HTTP status code 400)
    """
    logger.warning(f"Bad request: {str(error)}")
    return jsonify({
        'error': 'Bad request',
        'message': 'The request could not be understood or was missing required parameters',
        'status': 400
    }), 400


@app.errorhandler(404)
def not_found_error(error):
    """
    Handle HTTP 404 Not Found errors.

    Triggered when a route doesn't exist or a resource (like history item) isn't found.

    Args:
        error: The error object from Flask

    Returns:
        tuple: (JSON response dict, HTTP status code 404)
    """
    logger.warning(f"Not found: {request.path}")
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found on this server',
        'status': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle HTTP 500 Internal Server Error.

    Triggered by uncaught exceptions in route handlers or application logic.

    Args:
        error: The error object from Flask

    Returns:
        tuple: (JSON response dict, HTTP status code 500)
    """
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'message': 'An internal server error occurred. Please try again later.',
        'status': 500
    }), 500


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """
    Handle any unexpected/uncaught exceptions.

    Catch-all handler for exceptions not covered by specific handlers.
    Logs full traceback for debugging.

    Args:
        error: The exception object

    Returns:
        tuple: (JSON response dict, HTTP status code 500)
    """
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    return jsonify({
        'error': 'Unexpected error',
        'message': 'An unexpected error occurred. Please try again.',
        'status': 500
    }), 500


@app.errorhandler(OllamaConnectionError)
def handle_connection_error(error):
    """
    Handle Ollama connection errors (custom exception).

    Returns 503 Service Unavailable when Ollama server is unreachable.
    Error message includes troubleshooting steps.

    Args:
        error (OllamaConnectionError): The connection error exception

    Returns:
        tuple: (JSON response dict with troubleshooting, HTTP status code 503)
    """
    logger.error(f"Ollama connection error: {str(error)}")
    return jsonify({
        'error': 'Connection Error',
        'message': str(error),
        'status': 503,
        'type': 'connection_error'
    }), 503


@app.errorhandler(OllamaTimeoutError)
def handle_timeout_error(error):
    """
    Handle Ollama timeout errors (custom exception).

    Returns 504 Gateway Timeout when request exceeds 120 second limit.
    Usually indicates model is too large for available system resources.

    Args:
        error (OllamaTimeoutError): The timeout error exception

    Returns:
        tuple: (JSON response dict with troubleshooting, HTTP status code 504)
    """
    logger.error(f"Ollama timeout error: {str(error)}")
    return jsonify({
        'error': 'Timeout Error',
        'message': str(error),
        'status': 504,
        'type': 'timeout_error'
    }), 504


@app.errorhandler(OllamaModelNotFoundError)
def handle_model_not_found_error(error):
    """
    Handle Ollama model not found errors (custom exception).

    Returns 404 Not Found when requested model isn't installed locally.
    Error message includes 'ollama pull' command to install the model.

    Args:
        error (OllamaModelNotFoundError): The model not found exception

    Returns:
        tuple: (JSON response dict with installation instructions, HTTP status code 404)
    """
    logger.error(f"Ollama model not found: {str(error)}")
    return jsonify({
        'error': 'Model Not Found',
        'message': str(error),
        'status': 404,
        'type': 'model_not_found'
    }), 404


@app.errorhandler(OllamaAPIError)
def handle_api_error(error):
    """
    Handle Ollama API errors (custom exception).

    Returns 502 Bad Gateway for API-level errors, malformed responses,
    or unexpected Ollama behavior.

    Args:
        error (OllamaAPIError): The API error exception

    Returns:
        tuple: (JSON response dict with troubleshooting, HTTP status code 502)
    """
    logger.error(f"Ollama API error: {str(error)}")
    return jsonify({
        'error': 'API Error',
        'message': str(error),
        'status': 502,
        'type': 'api_error'
    }), 502


# ============================================================================
# Application Routes
# ============================================================================

@app.route('/')
def index():
    """
    Serve the main application page.

    Returns the single-page application HTML which includes embedded
    CSS and JavaScript for the full user interface.

    Returns:
        str: Rendered HTML template (templates/index.html)
    """
    return render_template('index.html')


@app.route('/presets', methods=['GET'])
def get_presets():
    """
    Return available preset options as JSON.

    Provides the PRESETS dictionary to the frontend for populating
    dropdown menus. Includes all categories: styles, artists,
    composition, and lighting.

    Returns:
        JSON: PRESETS dictionary with all preset categories and options

    Example Response:
        {
            "styles": {"None": "", "Cinematic": "cinematic, dramatic, ...", ...},
            "artists": {"None": "", "Greg Rutkowski": "in the style of...", ...},
            ...
        }
    """
    return jsonify(PRESETS)


@app.route('/models', methods=['GET'])
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

    try:
        # Get base URL for Ollama (remove /api/generate path)
        ollama_base_url = OLLAMA_URL.rsplit('/api', 1)[0]
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
            'default': OLLAMA_MODEL
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


@app.route('/generate', methods=['POST'])
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
    if not request.json:
        logger.warning("Generate request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    # Extract request parameters
    data = request.json
    user_input = data.get('input', '').strip()
    model_type = data.get('model', 'flux')  # Default to Flux if not specified
    ollama_model = data.get('ollama_model', OLLAMA_MODEL)  # Ollama model to use

    # Extract preset selections (all default to 'None' if not provided)
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')

    # Validate user provided some input
    if not user_input:
        logger.warning("Generate request with empty input")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a description'
        }), 400

    logger.info(f"Generating prompt for model: {model_type}")
    logger.debug(f"User input preview: {user_input[:50]}...")

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
    else:
        # No presets selected, use input as-is
        full_input = user_input

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
    save_to_history(user_input, result, model_type, presets_dict, 'oneshot')

    return jsonify({
        'result': result,
        'model': model_type
    })

@app.route('/chat', methods=['POST'])
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
        - Conversation history stored in session['conversation']
        - Changing model resets conversation
        - History limited to 21 messages (system + 20 exchanges)
        - Each message saved to database with mode='chat'
    """
    logger.info("Received /chat request")

    # Validate request has JSON data
    if not request.json:
        logger.warning("Chat request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    data = request.json
    user_message = data.get('message', '').strip()
    model_type = data.get('model', 'flux')
    ollama_model = data.get('ollama_model', OLLAMA_MODEL)  # Ollama model to use

    # Get preset selections
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')

    if not user_message:
        logger.warning("Chat request with empty message")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a message'
        }), 400

    # Get or initialize conversation history from Flask session
    # Session is stored as signed cookie, persists across requests
    if 'conversation' not in session:
        logger.info("Starting new chat conversation")
        session['conversation'] = []
        session['model_type'] = model_type

    # If model type changed, reset conversation
    # Different models need different prompting strategies
    if session.get('model_type') != model_type:
        logger.info(f"Model changed to {model_type}, resetting conversation")
        session['conversation'] = []
        session['model_type'] = model_type

    # Add system prompt if starting new conversation
    # System prompt instructs the AI on how to format responses
    if not session['conversation']:
        system_prompt = SYSTEM_PROMPTS.get(model_type, SYSTEM_PROMPTS['flux'])
        session['conversation'].append({
            "role": "system",
            "content": system_prompt
        })

    logger.debug(f"Chat message preview: {user_message[:50]}...")

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
    else:
        full_message = user_message

    # Add user message
    session['conversation'].append({
        "role": "user",
        "content": full_message
    })

    # Get response from Ollama
    result = call_ollama(session['conversation'], model=ollama_model)

    # Add assistant response to history
    session['conversation'].append({
        "role": "assistant",
        "content": result
    })

    # Keep conversation manageable to prevent session bloat and token limits
    # Retain system message (index 0) + last 20 messages (10 exchanges)
    if len(session['conversation']) > 21:  # system + 20 messages
        logger.debug("Trimming conversation history to maintain manageable size")
        # Keep first message (system) and last 20 messages
        session['conversation'] = [session['conversation'][0]] + session['conversation'][-20:]

    # Mark session as modified to ensure Flask saves changes
    session.modified = True
    logger.info("Successfully processed chat message")

    # Save to history
    presets_dict = {
        'style': style,
        'artist': artist,
        'composition': composition,
        'lighting': lighting
    }
    save_to_history(user_message, result, model_type, presets_dict, 'chat')

    return jsonify({
        'result': result,
        'model': model_type
    })

@app.route('/generate-stream', methods=['POST'])
def generate_stream():
    """Generate a prompt with streaming (one-shot mode)"""
    logger.info("Received /generate-stream request")

    # Validate request has JSON data
    if not request.json:
        logger.warning("Generate-stream request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    data = request.json
    user_input = data.get('input', '').strip()
    model_type = data.get('model', 'flux')
    ollama_model = data.get('ollama_model', OLLAMA_MODEL)  # Ollama model to use

    # Get preset selections
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')

    if not user_input:
        logger.warning("Generate-stream request with empty input")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a description'
        }), 400

    logger.info(f"Generating streaming prompt for model: {model_type}, ollama_model: {ollama_model}")
    logger.debug(f"User input preview: {user_input[:50]}...")

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
    else:
        full_input = user_input

    # Get appropriate system prompt
    system_prompt = SYSTEM_PROMPTS.get(model_type, SYSTEM_PROMPTS['flux'])

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_input}
    ]

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
            presets_dict = {
                'style': style,
                'artist': artist,
                'composition': composition,
                'lighting': lighting
            }
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

    return app.response_class(generate(), mimetype='text/event-stream')


@app.route('/chat-stream', methods=['POST'])
def chat_stream():
    """Conversational mode with streaming - refine ideas back and forth"""
    logger.info("Received /chat-stream request")

    # Validate request has JSON data
    if not request.json:
        logger.warning("Chat-stream request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    data = request.json
    user_message = data.get('message', '').strip()
    model_type = data.get('model', 'flux')
    ollama_model = data.get('ollama_model', OLLAMA_MODEL)  # Ollama model to use

    # Get preset selections
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')

    if not user_message:
        logger.warning("Chat-stream request with empty message")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a message'
        }), 400

    # Get or initialize conversation history
    if 'conversation' not in session:
        logger.info("Starting new chat conversation")
        session['conversation'] = []
        session['model_type'] = model_type

    # If model changed, reset conversation
    if session.get('model_type') != model_type:
        logger.info(f"Model changed to {model_type}, resetting conversation")
        session['conversation'] = []
        session['model_type'] = model_type

    # Add system prompt if starting new conversation
    if not session['conversation']:
        system_prompt = SYSTEM_PROMPTS.get(model_type, SYSTEM_PROMPTS['flux'])
        session['conversation'].append({
            "role": "system",
            "content": system_prompt
        })

    logger.debug(f"Chat message preview: {user_message[:50]}...")

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
    else:
        full_message = user_message

    # Add user message
    session['conversation'].append({
        "role": "user",
        "content": full_message
    })

    # Make a copy of the conversation for the request
    conversation_snapshot = list(session['conversation'])

    # Store session data that we'll need after streaming
    session_conversation = session['conversation']

    def generate():
        """Generator function for SSE streaming"""
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
                # Add assistant response to session history
                session_conversation.append({
                    "role": "assistant",
                    "content": full_response
                })

                # Keep conversation manageable (last 10 messages + system)
                if len(session_conversation) > 21:  # system + 20 messages
                    logger.debug("Trimming conversation history to maintain manageable size")
                    # Trim but keep the reference valid
                    trimmed = [session_conversation[0]] + session_conversation[-20:]
                    session_conversation.clear()
                    session_conversation.extend(trimmed)

                # Save to history after completion
                presets_dict = {
                    'style': style,
                    'artist': artist,
                    'composition': composition,
                    'lighting': lighting
                }
                save_to_history(user_message, full_response, model_type, presets_dict, 'chat')

    return app.response_class(generate(), mimetype='text/event-stream')


@app.route('/reset', methods=['POST'])
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
    session.pop('conversation', None)
    session.pop('model_type', None)
    return jsonify({'status': 'reset'})


@app.route('/history', methods=['GET'])
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


@app.route('/history/<int:history_id>', methods=['DELETE'])
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

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    # Initialize the SQLite database (creates tables if they don't exist)
    init_db()

    # Ensure we can reach Ollama or gather updated connection details
    ensure_ollama_connection()

    # Display startup banner to console with configuration details
    print("\n" + "="*60)
    print("=== Prompt Generator Starting ===")
    print("="*60)
    print(f"\nOpen your browser to: http://localhost:{FLASK_PORT}")
    print(f"Using Ollama model: {OLLAMA_MODEL}")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"Log level: {LOG_LEVEL}")
    print("\n" + "-"*60)
    print("IMPORTANT: Make sure Ollama is running!")
    print("  Start Ollama: ollama serve")
    print("  Check status: curl http://localhost:11434")
    print("  Install model: ollama pull " + OLLAMA_MODEL)
    print("-"*60)
    print("\nPress Ctrl+C to stop\n")

    # Log startup information for debugging
    logger.info("="*60)
    logger.info("Starting Prompt Generator Application")
    logger.info("="*60)
    logger.info(f"Flask port: {FLASK_PORT}")
    logger.info(f"Flask debug mode: {FLASK_DEBUG}")
    logger.info(f"Ollama URL: {OLLAMA_URL}")
    logger.info(f"Ollama model: {OLLAMA_MODEL}")
    logger.info(f"Log level: {LOG_LEVEL}")
    logger.info("Application ready to accept requests")

    # Start Flask development server
    # host='0.0.0.0' allows access from other devices on network
    # DO NOT use debug=True in production (security risk)
    app.run(debug=FLASK_DEBUG, host='0.0.0.0', port=FLASK_PORT)
