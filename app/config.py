"""
Application configuration management.

All configuration values are loaded from environment variables (.env file).
See .env.example for available options and descriptions.
"""

import os
import secrets
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class Config:
    """
    Configuration object for the Flask application.

    All values can be customized via environment variables in .env file.
    """

    # ============================================================================
    # Ollama Configuration
    # ============================================================================

    # Ollama API endpoint URL for prompt generation
    # Default: http://localhost:11434/api/generate
    # Can be customized to point to remote Ollama instances
    OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434/api/generate')

    # Default Ollama model to use for prompt generation
    # Common options: qwen3:latest, llama2, mistral, phi
    # Must be installed locally: ollama pull <model-name>
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:latest')

    # ============================================================================
    # Flask Configuration
    # ============================================================================

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

    # ============================================================================
    # Logging Configuration
    # ============================================================================

    # Logging level for application logs
    # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    # Default: INFO provides good balance of detail
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

    # ============================================================================
    # Feature Flags
    # ============================================================================

    # Feature flag for hierarchical preset system
    # Set to 'true' to enable new 5-level hierarchical presets
    # Set to 'false' to use legacy flat presets
    ENABLE_HIERARCHICAL_PRESETS = os.getenv('ENABLE_HIERARCHICAL_PRESETS', 'false').lower() in ('true', '1', 'yes')

    # Skip interactive Ollama connection check on startup
    # Set to 'false' for Docker/systemd deployments
    OLLAMA_STARTUP_CHECK = os.getenv('OLLAMA_STARTUP_CHECK', 'true').lower() in ('true', '1', 'yes')

    # ============================================================================
    # Security Configuration
    # ============================================================================

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
    # File Paths
    # ============================================================================

    # Database file path (relative to project root)
    DATABASE_PATH = 'prompt_history.db'

    # Preset files
    LEGACY_PRESETS_FILE = 'presets.json'
    HIERARCHICAL_PRESETS_FILE = 'hierarchical_presets.json'

    # Persona files
    PERSONAS_FILE = 'personas.json'
    PERSONAS_DIR = 'personas'

    # System prompts directory
    PROMPTS_DIR = 'prompts'

    @property
    def PRESETS_FILE(self):
        """Return the appropriate presets file based on feature flag."""
        return self.HIERARCHICAL_PRESETS_FILE if self.ENABLE_HIERARCHICAL_PRESETS else self.LEGACY_PRESETS_FILE

    @property
    def PROMPT_FILES(self):
        """Return paths to system prompt files."""
        return {
            'sdxl_oneshot': os.path.join(self.PROMPTS_DIR, 'sdxl_oneshot.txt'),
            'flux_oneshot': os.path.join(self.PROMPTS_DIR, 'flux_oneshot.txt'),
            'sdxl_chat': os.path.join(self.PROMPTS_DIR, 'sdxl_chat.txt'),
            'flux_chat': os.path.join(self.PROMPTS_DIR, 'flux_chat.txt')
        }


# Create a default config instance for easy importing
config = Config()
