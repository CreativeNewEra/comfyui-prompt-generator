"""Pytest configuration and fixtures for testing the Flask app in both preset modes."""

import importlib
import os
import sys

import pytest

# Ensure we can import the application module from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def _load_app(monkeypatch, hierarchical_enabled):
    """Import prompt_generator with the desired feature flag state."""
    env_value = 'true' if hierarchical_enabled else 'false'
    monkeypatch.setenv('ENABLE_HIERARCHICAL_PRESETS', env_value)

    if 'prompt_generator' in sys.modules:
        del sys.modules['prompt_generator']

    module = importlib.import_module('prompt_generator')
    module.app.config['TESTING'] = True
    module.app.config['SECRET_KEY'] = 'test-secret-key'
    return module


@pytest.fixture(params=[False, True])
def app_module(request, monkeypatch):
    """Provide the prompt_generator module with legacy and hierarchical presets."""
    module = _load_app(monkeypatch, request.param)
    yield module
    if 'prompt_generator' in sys.modules:
        del sys.modules['prompt_generator']


@pytest.fixture
def flask_app(app_module):
    """Create and configure a Flask app instance for testing."""
    return app_module.app


@pytest.fixture
def client(flask_app):
    """Create a test client for the Flask app."""
    return flask_app.test_client()


@pytest.fixture
def presets(app_module):
    """Expose the active preset data for the current test mode."""
    return app_module.PRESETS


@pytest.fixture
def hierarchical_enabled(app_module):
    """Return whether hierarchical presets are active for this test run."""
    return app_module.ENABLE_HIERARCHICAL_PRESETS
