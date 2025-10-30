"""
ComfyUI Prompt Generator - Flask Application Factory

This module provides the application factory pattern for creating Flask instances.
All configuration, logging, database initialization, blueprint registration, and
error handlers are set up here.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request

from app.config import config
from app.database import init_db, ConversationStore
from app.errors import (
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaModelNotFoundError,
    OllamaAPIError
)


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
    numeric_level = getattr(logging, config.LOG_LEVEL, logging.INFO)

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


# Module-level logger
logger = setup_logging()


def create_app():
    """
    Application factory function that creates and configures the Flask application.

    This function:
    1. Creates the Flask application instance
    2. Configures the app from app.config
    3. Initializes the database (creates tables if needed)
    4. Initializes the conversation store
    5. Registers all blueprints (routes)
    6. Registers all error handlers
    7. Optionally checks Ollama connection (if OLLAMA_STARTUP_CHECK is enabled)

    Returns:
        Flask: Configured Flask application instance

    Environment Variables:
        All configuration is loaded from .env file via app.config.Config
        See .env.example for available options

    Notes:
        - This factory pattern allows for easier testing and multiple app instances
        - Database and conversation store are initialized on app creation
        - Ollama connection check can be disabled for Docker/systemd deployments
    """
    logger.info("Creating Flask application")

    # Create Flask app instance
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    # Configure Flask from config object
    app.secret_key = config.FLASK_SECRET_KEY
    app.debug = config.FLASK_DEBUG

    # Store config object in app for route access
    app.config['APP_CONFIG'] = config

    logger.info(f"Flask configured - Debug: {config.FLASK_DEBUG}, Port: {config.FLASK_PORT}")

    # Initialize database
    logger.info("Initializing database")
    init_db()

    # Initialize conversation store and attach to app
    logger.info("Initializing conversation store")
    app.conversation_store = ConversationStore(
        db_path=config.DATABASE_PATH,
        max_messages=21,  # System prompt + 20 user/assistant messages
        max_age_hours=24
    )

    # Register all blueprints
    logger.info("Registering blueprints")
    from app.routes import register_blueprints
    register_blueprints(app)

    # Register error handlers
    logger.info("Registering error handlers")
    register_error_handlers(app)

    # Optional: Check Ollama connection on startup
    if config.OLLAMA_STARTUP_CHECK:
        logger.info("Checking Ollama connection (set OLLAMA_STARTUP_CHECK=false to skip)")
        from app.ollama_client import ensure_ollama_connection
        ensure_ollama_connection()
    else:
        logger.info("Skipping Ollama startup check (OLLAMA_STARTUP_CHECK=false)")

    logger.info("Flask application created successfully")
    return app


def register_error_handlers(app: Flask):
    """
    Register all error handlers with the Flask application.

    Handles:
    - HTTP errors: 400, 404, 405, 500
    - Generic exceptions: Exception
    - Custom Ollama errors: OllamaConnectionError, OllamaTimeoutError,
                           OllamaModelNotFoundError, OllamaAPIError

    Args:
        app: Flask application instance
    """

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
