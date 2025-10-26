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
from datetime import datetime, timezone, timedelta
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

# Feature flag for hierarchical preset system
# Set to 'true' to enable new 5-level hierarchical presets
# Set to 'false' to use legacy flat presets
ENABLE_HIERARCHICAL_PRESETS = os.getenv('ENABLE_HIERARCHICAL_PRESETS', 'false').lower() in ('true', '1', 'yes')

# Administrative API key required for sensitive operations (e.g. reloading prompts)
# If unset, access to the admin endpoint is limited to loopback/localhost clients
ADMIN_API_KEY = os.getenv('ADMIN_API_KEY')

# Optional comma separated list of additional IPs allowed to access admin endpoints
# Example: ADMIN_ALLOWED_IPS="192.168.1.10,10.0.0.5"
ADMIN_ALLOWED_IPS = {
    ip.strip()
    for ip in os.getenv('ADMIN_ALLOWED_IPS', '').split(',')
    if ip.strip()
}

# Trust X-Forwarded-For header for IP detection (only enable if behind a trusted proxy)
# WARNING: Only set to 'true' if your app is behind a reverse proxy (nginx, etc.)
# that properly strips untrusted X-Forwarded-For headers from clients
TRUST_PROXY_HEADERS = os.getenv('TRUST_PROXY_HEADERS', 'false').lower() in ('true', '1', 'yes')

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
# Admin Security Helpers
# ============================================================================

def get_client_ip(req) -> str:
    """
    Return the best-effort client IP for the current request.

    Security note: Only trusts X-Forwarded-For if TRUST_PROXY_HEADERS is enabled.
    By default, uses req.remote_addr which cannot be spoofed by clients.
    """
    if not req:
        return ''

    # Only trust X-Forwarded-For if explicitly enabled (i.e., behind a trusted proxy)
    if TRUST_PROXY_HEADERS:
        forwarded_for = req.headers.get('X-Forwarded-For', '') if hasattr(req, 'headers') else ''
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

    # Default to remote_addr which is set by the WSGI server and cannot be spoofed
    return getattr(req, 'remote_addr', '') or ''


def is_loopback_ip(ip: str) -> bool:
    """Return True if the provided IP address is a loopback/localhost address."""
    if not ip:
        return False

    try:
        return ipaddress.ip_address(ip).is_loopback
    except ValueError:
        return False


def authorize_admin_request(req):
    """Evaluate whether the incoming request may access admin-only endpoints."""
    client_ip = get_client_ip(req)
    forwarded_for = req.headers.get('X-Forwarded-For', '') if hasattr(req, 'headers') else ''

    if ADMIN_API_KEY:
        args = getattr(req, 'args', {})
        provided_key = (req.headers.get('X-Admin-API-Key') if hasattr(req, 'headers') else None) or args.get('admin_api_key')
        if provided_key and secrets.compare_digest(str(provided_key), str(ADMIN_API_KEY)):
            return True, client_ip, forwarded_for, 'valid API key'
        return False, client_ip, forwarded_for, 'missing or invalid API key'

    if client_ip and (is_loopback_ip(client_ip) or client_ip in ADMIN_ALLOWED_IPS):
        return True, client_ip, forwarded_for, 'allowed client IP'

    if not client_ip:
        return False, client_ip, forwarded_for, 'unable to determine client IP'

    return False, client_ip, forwarded_for, 'client IP not permitted'


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
# Can be overridden via DB_PATH environment variable (useful for testing)
DB_PATH = os.getenv('DB_PATH', 'prompt_history.db')


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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_store (
            session_id TEXT PRIMARY KEY,
            model_type TEXT NOT NULL,
            conversation TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_conversation_updated
        ON conversation_store (updated_at)
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


class ConversationStore:
    """Persist chat transcripts on the server side."""

    def __init__(self, db_path: str, max_messages: int = 21, max_age_hours: int = 24):
        self.db_path = db_path
        self.max_messages = max_messages
        self.max_age_hours = max_age_hours
        self._ensure_table()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_table(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_store (
                    session_id TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    conversation TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_conversation_updated
                ON conversation_store (updated_at)
            ''')
            conn.commit()

    def _trim_messages(self, messages):
        if not messages or len(messages) <= self.max_messages:
            return list(messages)

        # Extract system prompt if present
        system_msg = None
        conv_messages = messages
        if messages[0].get('role') == 'system':
            system_msg = messages[0]
            conv_messages = messages[1:]

        # Calculate how many conversation messages we can keep
        max_conv_messages = self.max_messages - (1 if system_msg else 0)

        # If we need to trim, ensure we preserve complete user-assistant pairs
        if len(conv_messages) > max_conv_messages:
            # Count back from the end, ensuring we keep complete pairs
            # Each pair is user + assistant, so pairs are at indices (0,1), (2,3), (4,5), etc.
            # If the last message is 'user', we need to be careful not to orphan it

            # Start from the end and count backwards in pairs
            keep_count = max_conv_messages

            # If we would end on an assistant message (even index from end), that's good
            # If we would end on a user message (odd index from end), reduce by 1 to keep the pair
            if keep_count < len(conv_messages):
                # Check what role we'd be starting with after the trim
                start_index = len(conv_messages) - keep_count
                # If we're starting with an 'assistant' message, that means we're breaking a pair
                if start_index < len(conv_messages) and conv_messages[start_index].get('role') == 'assistant':
                    # Move forward to the next user message to preserve the pair
                    keep_count -= 1

            conv_messages = conv_messages[-keep_count:] if keep_count > 0 else []

        # Reconstruct the message list
        result = []
        if system_msg:
            result.append(system_msg)
        result.extend(conv_messages)
        return result

    def _cleanup(self, conn):
        if not self.max_age_hours:
            return

        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.max_age_hours)
        conn.execute(
            'DELETE FROM conversation_store WHERE updated_at < ?',
            (cutoff.isoformat(),)
        )

    def create_session(self, model_type: str, initial_messages=None) -> str:
        session_id = secrets.token_urlsafe(16)
        messages = initial_messages or []
        self.save_messages(session_id, messages, model_type)
        return session_id

    def get_conversation(self, session_id: Optional[str]):
        if not session_id:
            return [], None

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT conversation, model_type FROM conversation_store WHERE session_id = ?',
                (session_id,)
            )
            row = cursor.fetchone()

        if not row:
            return [], None

        try:
            conversation = json.loads(row[0])
        except json.JSONDecodeError:
            conversation = []

        return conversation, row[1]

    def save_messages(self, session_id: str, messages, model_type: str):
        trimmed = self._trim_messages(messages)
        serialized = json.dumps(trimmed)
        timestamp = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            conn.execute('''
                INSERT INTO conversation_store (session_id, model_type, conversation, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    model_type=excluded.model_type,
                    conversation=excluded.conversation,
                    updated_at=excluded.updated_at
            ''', (session_id, model_type, serialized, timestamp))
            self._cleanup(conn)
            conn.commit()

        return trimmed

    def delete_session(self, session_id: Optional[str]):
        if not session_id:
            return

        with self._connect() as conn:
            conn.execute('DELETE FROM conversation_store WHERE session_id = ?', (session_id,))
            conn.commit()

    def clear_all(self):
        with self._connect() as conn:
            conn.execute('DELETE FROM conversation_store')
            conn.commit()


conversation_store = ConversationStore(DB_PATH)


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

        timestamp = datetime.now(timezone.utc).isoformat()
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
# NOTE: Presets have been moved to presets.json for easier editing.
# The JSON file is loaded at startup and can be reloaded without restarting
# the server (see /presets endpoint).
#
# All presets default to "None" (empty string), making them optional.
# Users can mix and match presets across categories for creative control.
# The AI model weaves these elements naturally into the final prompt.

# Path to the presets configuration files
# Use absolute path based on script location to ensure it works
# regardless of where the script is run from
LEGACY_PRESETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'presets.json')
HIERARCHICAL_PRESETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hierarchical_presets.json')

# Select which presets file to use based on feature flag
PRESETS_FILE = HIERARCHICAL_PRESETS_FILE if ENABLE_HIERARCHICAL_PRESETS else LEGACY_PRESETS_FILE

# Paths to the system prompt files
# These allow prompts to be edited without modifying the Python code
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prompts')
PROMPT_FILES = {
    'sdxl_oneshot': os.path.join(PROMPTS_DIR, 'sdxl_oneshot.txt'),
    'flux_oneshot': os.path.join(PROMPTS_DIR, 'flux_oneshot.txt'),
    'sdxl_chat': os.path.join(PROMPTS_DIR, 'sdxl_chat.txt'),
    'flux_chat': os.path.join(PROMPTS_DIR, 'flux_chat.txt')
}


def load_presets():
    """
    Load presets from either hierarchical_presets.json or legacy presets.json.

    The function supports both:
    - Legacy flat presets (styles, artists, composition, lighting)
    - New hierarchical presets (categories, preset_packs, universal_options)

    Which file is loaded depends on the ENABLE_HIERARCHICAL_PRESETS feature flag.

    Returns:
        dict: Presets dictionary in appropriate format based on preset type

    Raises:
        FileNotFoundError: If presets file is missing
        json.JSONDecodeError: If presets file contains invalid JSON

    The function includes fallback presets in case the file is missing or invalid.
    This ensures the application can still run even if the presets file is corrupted.
    """
    preset_type = "hierarchical" if ENABLE_HIERARCHICAL_PRESETS else "legacy"

    try:
        with open(PRESETS_FILE, 'r', encoding='utf-8') as f:
            presets = json.load(f)
            logger.info(f"Successfully loaded {preset_type} presets from {PRESETS_FILE}")

            # Validate structure based on type
            if ENABLE_HIERARCHICAL_PRESETS:
                if 'categories' in presets and 'preset_packs' in presets:
                    num_categories = len(presets.get('categories', {}))
                    num_packs = len(presets.get('preset_packs', {}).get('packs', []))
                    logger.info(f"Loaded {num_categories} categories and {num_packs} preset packs")
                else:
                    logger.warning("Hierarchical presets file missing expected structure")

            return presets

    except FileNotFoundError:
        logger.error(f"Presets file not found: {PRESETS_FILE}")
        logger.warning(f"Using minimal fallback {preset_type} presets")

        # Return appropriate fallback based on type
        if ENABLE_HIERARCHICAL_PRESETS:
            return {
                "version": "1.0",
                "categories": {},
                "preset_packs": {"packs": []},
                "universal_options": {},
                "quality_tags": {"flux": {}, "sdxl": {}}
            }
        else:
            return {
                "styles": {"None": ""},
                "artists": {"None": ""},
                "composition": {"None": ""},
                "lighting": {"None": ""}
            }

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in presets file: {e}")
        logger.warning(f"Using minimal fallback {preset_type} presets")

        if ENABLE_HIERARCHICAL_PRESETS:
            return {
                "version": "1.0",
                "categories": {},
                "preset_packs": {"packs": []},
                "universal_options": {},
                "quality_tags": {"flux": {}, "sdxl": {}}
            }
        else:
            return {
                "styles": {"None": ""},
                "artists": {"None": ""},
                "composition": {"None": ""},
                "lighting": {"None": ""}
            }

    except Exception as e:
        logger.error(f"Unexpected error loading presets: {e}")
        logger.warning(f"Using minimal fallback {preset_type} presets")

        if ENABLE_HIERARCHICAL_PRESETS:
            return {
                "version": "1.0",
                "categories": {},
                "preset_packs": {"packs": []},
                "universal_options": {},
                "quality_tags": {"flux": {}, "sdxl": {}}
            }
        else:
            return {
                "styles": {"None": ""},
                "artists": {"None": ""},
                "composition": {"None": ""},
                "lighting": {"None": ""}
            }


def load_prompts():
    """
    Load system prompts from text files in the prompts/ directory.

    Returns:
        tuple: (SYSTEM_PROMPTS dict, CHAT_SYSTEM_PROMPTS dict)

    This function attempts to load prompts from external text files, enabling
    prompt editing without code changes. If files are missing or unreadable,
    it falls back to hardcoded default prompts to ensure the app remains functional.

    The function logs all operations for debugging and provides helpful error
    messages if files are missing.
    """
    # Hardcoded fallback prompts (original defaults)
    fallback_system_prompts = {
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

    fallback_chat_prompts = {
        "sdxl": """You are a collaborative prompt engineering partner helping the user craft prompts for Stable Diffusion XL (SDXL). Use a conversational tone and work iteratively.

For each user message:
- Briefly acknowledge the request and how it fits the ongoing concept.
- Brainstorm 2-3 improved prompt variations labeled as Option 1, Option 2, etc. Write them as rich natural language descriptions that naturally include any provided presets.
- Provide a short list of negative prompt considerations that SDXL users might add, highlighting differences between the options when helpful.
- Ask at least one follow-up question or suggest the next tweak to keep the collaboration moving forward.

Do not reply with a single "PROMPT:" line. Keep responses friendly, structured, and easy to skim in chat format.""",

        "flux": """You are a creative brainstorming partner for Flux image models. Respond conversationally and iterate with the user.

For each reply:
- Offer 2-3 distinct creative directions or prompt variations, each clearly labeled (e.g., Option 1, Option 2) and written in vivid natural language.
- Call out noteworthy stylistic, compositional, or lighting ideas for each option, integrating any presets the user selected.
- Ask at least one clarifying or exploratory question to encourage further refinement, or suggest what the user might try next.

Avoid emitting a single "PROMPT:" response. Keep the tone collaborative and idea-focused."""
    }

    system_prompts = {}
    chat_prompts = {}

    # Try to load SDXL oneshot prompt
    try:
        with open(PROMPT_FILES['sdxl_oneshot'], 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                system_prompts['sdxl'] = content
                logger.info("Loaded SDXL oneshot prompt from prompts/sdxl_oneshot.txt")
            else:
                logger.warning("prompts/sdxl_oneshot.txt is empty, using fallback")
                system_prompts['sdxl'] = fallback_system_prompts['sdxl']
    except FileNotFoundError:
        logger.warning("prompts/sdxl_oneshot.txt not found, using fallback")
        system_prompts['sdxl'] = fallback_system_prompts['sdxl']
    except Exception as e:
        logger.error(f"Error loading prompts/sdxl_oneshot.txt: {e}, using fallback")
        system_prompts['sdxl'] = fallback_system_prompts['sdxl']

    # Try to load Flux oneshot prompt
    try:
        with open(PROMPT_FILES['flux_oneshot'], 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                system_prompts['flux'] = content
                logger.info("Loaded Flux oneshot prompt from prompts/flux_oneshot.txt")
            else:
                logger.warning("prompts/flux_oneshot.txt is empty, using fallback")
                system_prompts['flux'] = fallback_system_prompts['flux']
    except FileNotFoundError:
        logger.warning("prompts/flux_oneshot.txt not found, using fallback")
        system_prompts['flux'] = fallback_system_prompts['flux']
    except Exception as e:
        logger.error(f"Error loading prompts/flux_oneshot.txt: {e}, using fallback")
        system_prompts['flux'] = fallback_system_prompts['flux']

    # Try to load SDXL chat prompt
    try:
        with open(PROMPT_FILES['sdxl_chat'], 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                chat_prompts['sdxl'] = content
                logger.info("Loaded SDXL chat prompt from prompts/sdxl_chat.txt")
            else:
                logger.warning("prompts/sdxl_chat.txt is empty, using fallback")
                chat_prompts['sdxl'] = fallback_chat_prompts['sdxl']
    except FileNotFoundError:
        logger.warning("prompts/sdxl_chat.txt not found, using fallback")
        chat_prompts['sdxl'] = fallback_chat_prompts['sdxl']
    except Exception as e:
        logger.error(f"Error loading prompts/sdxl_chat.txt: {e}, using fallback")
        chat_prompts['sdxl'] = fallback_chat_prompts['sdxl']

    # Try to load Flux chat prompt
    try:
        with open(PROMPT_FILES['flux_chat'], 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                chat_prompts['flux'] = content
                logger.info("Loaded Flux chat prompt from prompts/flux_chat.txt")
            else:
                logger.warning("prompts/flux_chat.txt is empty, using fallback")
                chat_prompts['flux'] = fallback_chat_prompts['flux']
    except FileNotFoundError:
        logger.warning("prompts/flux_chat.txt not found, using fallback")
        chat_prompts['flux'] = fallback_chat_prompts['flux']
    except Exception as e:
        logger.error(f"Error loading prompts/flux_chat.txt: {e}, using fallback")
        chat_prompts['flux'] = fallback_chat_prompts['flux']

    logger.info("System prompts loaded successfully")
    return system_prompts, chat_prompts


def build_hierarchical_prompt(user_input, selections, presets_data):
    """
    Build enhanced prompt from hierarchical preset selections.

    This function takes user selections from the hierarchical preset wizard
    and constructs a detailed, enhanced prompt that can be sent to the LLM.

    Args:
        user_input (str): User's basic image idea
        selections (dict): Dictionary with selections at each level:
            - level1 (str): Category ID (e.g., 'photography', 'fantasy')
            - level2 (str): Type ID (e.g., 'portrait', 'high_fantasy')
            - level3 (str): Artist ID (e.g., 'annie_leibovitz')
            - level4 (dict): Technical options {option_key: value_id}
            - level5 (dict): Scene specifics {key: value}
            - universal (dict): Universal options (mood, lighting, etc.)
        presets_data (dict): Full hierarchical presets JSON data

    Returns:
        str: Enhanced prompt with all selections formatted as text

    Example:
        >>> selections = {
        ...     'level1': 'photography',
        ...     'level2': 'portrait',
        ...     'level3': 'annie_leibovitz',
        ...     'level4': {'lighting': 'theatrical'},
        ...     'universal': {'mood': ['dramatic', 'elegant']}
        ... }
        >>> enhanced = build_hierarchical_prompt("A woman posing", selections, presets)
        >>> print(enhanced)
        A woman posing

        Style: Photography > Portrait > Annie Leibovitz
        ...
    """
    if not selections:
        logger.debug("No hierarchical selections provided, returning user input as-is")
        return user_input

    try:
        prompt_parts = [user_input, ""]

        # Get category data (Level 1)
        category_id = selections.get('level1')
        if not category_id:
            logger.debug("No level1 category selected")
            return user_input

        category = presets_data.get('categories', {}).get(category_id)
        if not category:
            logger.warning(f"Category '{category_id}' not found in presets")
            return user_input

        # Level 2: Type
        type_id = selections.get('level2')
        type_data = category.get('level2_types', {}).get(type_id) if type_id else None

        if type_data:
            prompt_parts.append(f"Style: {category['name']} > {type_data['name']}")

        # Level 3: Artist/Style
        artist_id = selections.get('level3')
        artist_data = type_data.get('level3_artists', {}).get(artist_id) if type_data and artist_id else None

        if artist_data:
            prompt_parts.append(f"Artist Style: {artist_data['name']}")

            if artist_data.get('description'):
                prompt_parts.append(f"Description: {artist_data['description']}")

            if artist_data.get('signature'):
                prompt_parts.append(f"Signature: {artist_data['signature']}")

            prompt_parts.append("")

        # Level 4: Technical details
        level4_selections = selections.get('level4', {})
        if level4_selections and artist_data:
            technical_opts = artist_data.get('level4_technical', {})
            if technical_opts:
                prompt_parts.append("Technical Details:")
                for tech_key, tech_value in level4_selections.items():
                    tech_category = technical_opts.get(tech_key)
                    if tech_category:
                        options = tech_category.get('options', [])
                        # Handle both list of dicts and list of strings
                        if options and isinstance(options[0], dict):
                            option = next((opt for opt in options if opt.get('id') == tech_value), None)
                            if option:
                                desc = f" ({option.get('description')})" if option.get('description') else ""
                                prompt_parts.append(f"- {tech_category['name']}: {option['name']}{desc}")
                        else:
                            # Simple string list
                            prompt_parts.append(f"- {tech_category['name']}: {tech_value.replace('_', ' ')}")
                prompt_parts.append("")

        # Level 5: Scene specifics
        level5_selections = selections.get('level5', {})
        if level5_selections:
            prompt_parts.append("Scene Details:")
            for key, value in level5_selections.items():
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, list):
                    prompt_parts.append(f"- {formatted_key}: {', '.join(value)}")
                elif isinstance(value, dict):
                    # Handle nested selections
                    for sub_key, sub_value in value.items():
                        formatted_sub_key = sub_key.replace('_', ' ').title()
                        prompt_parts.append(f"- {formatted_key} - {formatted_sub_key}: {sub_value}")
                else:
                    formatted_value = str(value).replace('_', ' ')
                    prompt_parts.append(f"- {formatted_key}: {formatted_value}")
            prompt_parts.append("")

        # Universal options
        universal = selections.get('universal', {})
        if universal:
            universal_added = False

            if universal.get('mood'):
                moods = universal['mood'] if isinstance(universal['mood'], list) else [universal['mood']]
                prompt_parts.append(f"Mood: {', '.join(moods)}")
                universal_added = True

            if universal.get('time_of_day'):
                prompt_parts.append(f"Time: {universal['time_of_day'].replace('_', ' ')}")
                universal_added = True

            if universal.get('lighting'):
                prompt_parts.append(f"Lighting: {universal['lighting'].replace('_', ' ')}")
                universal_added = True

            if universal.get('color_palette'):
                prompt_parts.append(f"Colors: {universal['color_palette'].replace('_', ' ')}")
                universal_added = True

            if universal.get('weather_atmosphere'):
                prompt_parts.append(f"Weather: {universal['weather_atmosphere'].replace('_', ' ')}")
                universal_added = True

            if universal.get('camera_effects'):
                effects = universal['camera_effects'] if isinstance(universal['camera_effects'], list) else [universal['camera_effects']]
                prompt_parts.append(f"Camera Effects: {', '.join(effects)}")
                universal_added = True

            if universal_added:
                prompt_parts.append("")

        enhanced_prompt = "\n".join(prompt_parts).strip()
        logger.info(f"Built hierarchical prompt ({len(enhanced_prompt)} chars) from {len(selections)} level selections")

        return enhanced_prompt

    except Exception as e:
        logger.error(f"Error building hierarchical prompt: {e}")
        logger.debug(f"Selections: {selections}")
        # Return original user input on error
        return user_input


# Load presets from JSON file at startup
# This variable is used throughout the application for preset lookups
PRESETS = load_presets()

# ============================================================================
# Model-Specific System Prompts
# ============================================================================
# Different AI image generation models have different prompting requirements.
# These system prompts instruct the Ollama LLM on how to format output
# appropriately for each model type.
#
# System prompts are now loaded from text files in the prompts/ directory:
#   - prompts/sdxl_oneshot.txt - SDXL quick generate mode
#   - prompts/flux_oneshot.txt - Flux quick generate mode
#   - prompts/sdxl_chat.txt - SDXL conversational mode
#   - prompts/flux_chat.txt - Flux conversational mode
#
# This allows prompt editing without modifying code. If files are missing,
# the application falls back to hardcoded defaults in load_prompts().
#
# When adding new models, add corresponding text files to prompts/ directory.

# Load system prompts from text files (with fallback to hardcoded defaults)
SYSTEM_PROMPTS, CHAT_SYSTEM_PROMPTS = load_prompts()

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


@app.errorhandler(405)
def method_not_allowed_error(error):
    """Handle HTTP 405 Method Not Allowed errors."""
    logger.warning("Method not allowed: %s %s", request.method, request.path)
    return jsonify({
        'error': 'Method not allowed',
        'message': 'The requested URL does not support this HTTP method.',
        'status': 405
    }), 405


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
    # Reload presets from file on each request to enable hot-reload
    presets = load_presets()
    return jsonify(presets)


# ============================================================================
# Hierarchical Preset API Routes (Phase 2)
# ============================================================================
# These routes provide level-by-level navigation through the hierarchical
# preset system. They are only active when ENABLE_HIERARCHICAL_PRESETS=true.
# Each route returns a subset of the hierarchical_presets.json data.


@app.route('/api/categories', methods=['GET'])
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
    if not ENABLE_HIERARCHICAL_PRESETS:
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


@app.route('/api/categories/<category_id>/types', methods=['GET'])
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
    if not ENABLE_HIERARCHICAL_PRESETS:
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


@app.route('/api/categories/<category_id>/types/<type_id>/artists', methods=['GET'])
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
    if not ENABLE_HIERARCHICAL_PRESETS:
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


@app.route('/api/artists/<category_id>/<type_id>/<artist_id>/technical', methods=['GET'])
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
    if not ENABLE_HIERARCHICAL_PRESETS:
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


@app.route('/api/artists/<category_id>/<type_id>/<artist_id>/specifics', methods=['GET'])
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
    if not ENABLE_HIERARCHICAL_PRESETS:
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


@app.route('/api/preset-packs', methods=['GET'])
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
    if not ENABLE_HIERARCHICAL_PRESETS:
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


@app.route('/api/universal-options', methods=['GET'])
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
    if not ENABLE_HIERARCHICAL_PRESETS:
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


# End of hierarchical preset API routes
# ============================================================================


@app.route('/admin/reload-prompts', methods=['POST'])
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
    global SYSTEM_PROMPTS, CHAT_SYSTEM_PROMPTS

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
        # Reload prompts from files
        new_system_prompts, new_chat_prompts = load_prompts()

        # Update global variables
        SYSTEM_PROMPTS = new_system_prompts
        CHAT_SYSTEM_PROMPTS = new_chat_prompts

        reloaded_prompts = list(SYSTEM_PROMPTS.keys()) + [f"{k}_chat" for k in CHAT_SYSTEM_PROMPTS.keys()]

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
    data = request.get_json(silent=True)
    if not data:
        logger.warning("Generate request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    # Extract request parameters
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

    conversation_id = session.get('conversation_id')
    conversation, stored_model = conversation_store.get_conversation(conversation_id)

    if stored_model and stored_model != model_type:
        logger.info("Model changed, starting new stored conversation")
        conversation_store.delete_session(conversation_id)
        conversation_id = None
        conversation = []
        stored_model = None

    if not conversation:
        system_prompt = CHAT_SYSTEM_PROMPTS.get(model_type, CHAT_SYSTEM_PROMPTS['flux'])
        conversation = [{
            "role": "system",
            "content": system_prompt
        }]
        conversation_id = conversation_store.create_session(model_type, conversation)
        session['conversation_id'] = conversation_id
    else:
        session['conversation_id'] = conversation_id

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
    conversation.append({
        "role": "user",
        "content": full_message
    })

    conversation = conversation_store.save_messages(conversation_id, conversation, model_type)

    conversation_snapshot = list(conversation)

    # Get response from Ollama
    result = call_ollama(conversation_snapshot, model=ollama_model)

    # Add assistant response to history
    conversation.append({
        "role": "assistant",
        "content": result
    })

    conversation_store.save_messages(conversation_id, conversation, model_type)
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
    data = request.get_json(silent=True)
    if not data:
        logger.warning("Generate-stream request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

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
    data = request.get_json(silent=True)
    if not data:
        logger.warning("Chat-stream request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

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

    conversation_id = session.get('conversation_id')
    conversation, stored_model = conversation_store.get_conversation(conversation_id)

    if stored_model and stored_model != model_type:
        logger.info("Model changed, starting new stored conversation")
        conversation_store.delete_session(conversation_id)
        conversation_id = None
        conversation = []
        stored_model = None

    if not conversation:
        system_prompt = CHAT_SYSTEM_PROMPTS.get(model_type, CHAT_SYSTEM_PROMPTS['flux'])
        conversation = [{
            "role": "system",
            "content": system_prompt
        }]
        conversation_id = conversation_store.create_session(model_type, conversation)

    session['conversation_id'] = conversation_id

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

    conversation.append({
        "role": "user",
        "content": full_message
    })

    conversation = conversation_store.save_messages(conversation_id, conversation, model_type)

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

                conversation = conversation_store.save_messages(conversation_id, conversation, model_type)

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
    conversation_id = session.pop('conversation_id', None)
    if conversation_id:
        conversation_store.delete_session(conversation_id)
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
