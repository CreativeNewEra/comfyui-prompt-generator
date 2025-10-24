"""
Pytest configuration and fixtures for testing
"""

import pytest
import sys
import os

# Add parent directory to path so we can import prompt_generator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prompt_generator import app, PRESETS


@pytest.fixture
def flask_app():
    """
    Create and configure a Flask app instance for testing
    """
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    return app


@pytest.fixture
def client(flask_app):
    """
    Create a test client for the Flask app
    """
    return flask_app.test_client()


@pytest.fixture
def presets():
    """
    Provide access to PRESETS for testing
    """
    return PRESETS
