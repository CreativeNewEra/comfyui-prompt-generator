"""
Pytest configuration and fixtures for testing
"""

import pytest
import sys
import os
import tempfile

# Add parent directory to path so we can import prompt_generator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope='session', autouse=True)
def setup_test_database(tmp_path_factory):
    """
    Configure a test-specific database path for all tests.
    This prevents tests from modifying the production database.
    """
    test_db_dir = tmp_path_factory.mktemp("test_db")
    test_db_path = str(test_db_dir / "test_prompt_history.db")
    os.environ['DB_PATH'] = test_db_path
    yield test_db_path
    # Cleanup happens automatically with tmp_path_factory


# Import after setting DB_PATH to ensure test database is used
from prompt_generator import app, PRESETS, conversation_store


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


@pytest.fixture(autouse=True)
def cleanup_conversation_store():
    """Ensure conversation store is cleared between tests."""
    import prompt_generator

    prompt_generator.init_db()
    conversation_store.clear_all()
    yield
    conversation_store.clear_all()
