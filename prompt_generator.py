#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI Prompt Generator - Entry Point

A Flask web application that integrates with local Ollama to generate
detailed prompts for ComfyUI image generation.

Features:
- Quick Generate mode (one-shot prompt generation)
- Chat & Refine mode (conversational refinement)
- Persona System (7 specialized AI personalities)
- Preset System (80+ curated presets or hierarchical categories)
- Streaming support (real-time token generation)
- History tracking (SQLite database)

Usage:
    python prompt_generator.py

Configuration:
    Create a .env file in the project root (see .env.example)

    Key settings:
    - OLLAMA_URL: Ollama API endpoint
    - OLLAMA_MODEL: Default model (e.g., qwen3:latest)
    - FLASK_PORT: Web server port (default: 5000)
    - FLASK_DEBUG: Debug mode (true/false)
    - FLASK_SECRET_KEY: Session secret key
    - ENABLE_HIERARCHICAL_PRESETS: Enable hierarchical preset system (true/false)

For more information:
    See README.md and CLAUDE.md for detailed documentation
"""

from app import create_app
from app.config import config

# Create Flask application using factory pattern
app = create_app()

if __name__ == '__main__':
    """
    Run the Flask development server.

    For production deployments, use a WSGI server like Gunicorn:
        gunicorn -w 4 -b 0.0.0.0:5000 prompt_generator:app
    """
    print("\n" + "="*70)
    print("🎨 ComfyUI Prompt Generator")
    print("="*70)
    print(f"Server starting on http://localhost:{config.FLASK_PORT}")
    print(f"Debug mode: {config.FLASK_DEBUG}")
    print(f"Default model: {config.OLLAMA_MODEL}")
    print(f"Preset system: {'Hierarchical' if config.ENABLE_HIERARCHICAL_PRESETS else 'Legacy'}")
    print("="*70 + "\n")

    app.run(
        host='0.0.0.0',
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
