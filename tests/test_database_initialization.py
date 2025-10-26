"""Integration tests for database initialization behavior."""

import sqlite3

import prompt_generator


def test_prompt_history_table_exists_before_requests(client, monkeypatch, tmp_path):
    """The prompt history table should exist before any endpoint is accessed."""
    test_db_path = tmp_path / "test_prompt_history.db"
    monkeypatch.setattr(prompt_generator, "DB_PATH", str(test_db_path))

    # Ensure the database is initialized (if prompt_generator does this at import, this is fine)
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
