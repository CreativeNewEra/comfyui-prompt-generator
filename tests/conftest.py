"""
Pytest configuration and fixtures for testing
"""

import pytest
import sys
import os

# Add parent directory to path so we can import app modules
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
from app import create_app
from app.presets import PRESETS


@pytest.fixture
def flask_app():
    """
    Create and configure a Flask app instance for testing
    """
    test_app = create_app()
    test_app.config['TESTING'] = True
    test_app.config['SECRET_KEY'] = 'test-secret-key'
    return test_app


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
def cleanup_conversation_store(flask_app):
    """Ensure conversation store is cleared between tests."""
    from app.database import init_db

    init_db()
    flask_app.conversation_store.clear_all()
    yield
    flask_app.conversation_store.clear_all()
