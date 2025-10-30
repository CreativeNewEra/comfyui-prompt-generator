"""
Flask Blueprint Registration Module

This module provides the blueprint registration system for the ComfyUI Prompt Generator.
All route blueprints are registered here with the main Flask application.

Blueprints:
    - main: Main application page
    - presets: Preset system (legacy + hierarchical)
    - persona: Persona conversational system
    - generate: Quick generate (one-shot) endpoints
    - chat: Chat & refine conversational endpoints
    - history: Prompt history management
    - models: Ollama model management
    - admin: Administrative endpoints
"""

from flask import Flask


def register_blueprints(app: Flask):
    """
    Register all application blueprints with the Flask app.

    This function should be called during application initialization
    to mount all route handlers.

    Args:
        app: The Flask application instance
    """
    # Import blueprints locally to avoid circular imports
    from app.routes.main import bp as main_bp
    from app.routes.presets import bp as presets_bp
    from app.routes.persona import bp as persona_bp
    from app.routes.generate import bp as generate_bp
    from app.routes.chat import bp as chat_bp
    from app.routes.history import bp as history_bp
    from app.routes.models import bp as models_bp
    from app.routes.admin import bp as admin_bp

    # Register all blueprints
    # Note: url_prefix=None means routes use their decorators' paths directly
    app.register_blueprint(main_bp)
    app.register_blueprint(presets_bp)
    app.register_blueprint(persona_bp)
    app.register_blueprint(generate_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(models_bp)
    app.register_blueprint(admin_bp)

    app.logger.info("All blueprints registered successfully")
