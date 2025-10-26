"""Integration tests for database initialization behavior."""

import sqlite3

import prompt_generator


def test_prompt_history_table_exists_before_requests(client):
    """The prompt history table should exist before any endpoint is accessed."""
    connection = sqlite3.connect(prompt_generator.DB_PATH)
    try:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='prompt_history'"
        )
        assert cursor.fetchone() is not None, "prompt_history table should be created at import time"
    finally:
        connection.close()

    response = client.get('/')
    assert response.status_code == 200
