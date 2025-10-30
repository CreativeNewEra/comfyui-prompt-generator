"""
Database operations for prompt history and conversation storage.

Manages SQLite database for:
- Prompt generation history
- Conversation session storage and trimming
"""

import sqlite3
import json
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.config import config

logger = logging.getLogger(__name__)


def init_db():
    """
    Initialize the SQLite database and create tables if they don't exist.

    Creates the prompt_history table with the following schema:
    - id: Auto-incrementing primary key
    - timestamp: ISO format UTC timestamp of generation
    - user_input: Original user description/request
    - generated_output: AI-generated prompt result
    - model: Model type used (flux/sdxl)
    - presets: JSON string of preset selections
    - mode: Generation mode (oneshot/chat)

    This function is idempotent - safe to call multiple times.
    Creates database file if it doesn't exist.
    """
    logger.info("Initializing prompt history database")
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompt_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_input TEXT NOT NULL,
            generated_output TEXT NOT NULL,
            model TEXT NOT NULL,
            presets TEXT,
            mode TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_store (
            session_id TEXT PRIMARY KEY,
            model_type TEXT NOT NULL,
            conversation TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_conversation_updated
        ON conversation_store (updated_at)
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


class ConversationStore:
    """
    Persist chat transcripts on the server side.

    Manages conversation sessions with automatic trimming to prevent
    token limit issues and memory bloat.
    """

    def __init__(self, db_path: str, max_messages: int = 21, max_age_hours: int = 24):
        """
        Initialize conversation store.

        Args:
            db_path: Path to SQLite database file
            max_messages: Maximum messages to keep (includes system prompt)
            max_age_hours: Auto-cleanup conversations older than this
        """
        self.db_path = db_path
        self.max_messages = max_messages
        self.max_age_hours = max_age_hours
        self._ensure_table()

    def _connect(self):
        """Create database connection."""
        return sqlite3.connect(self.db_path)

    def _ensure_table(self):
        """Ensure conversation_store table exists."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_store (
                    session_id TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    conversation TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_conversation_updated
                ON conversation_store (updated_at)
            ''')
            conn.commit()

    def _trim_messages(self, messages):
        """
        Trim conversation to max_messages while preserving user-assistant pairs.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Trimmed list of messages
        """
        if not messages or len(messages) <= self.max_messages:
            return list(messages)

        # Extract system prompt if present
        system_msg = None
        conv_messages = messages
        if messages[0].get('role') == 'system':
            system_msg = messages[0]
            conv_messages = messages[1:]

        # Calculate how many conversation messages we can keep
        max_conv_messages = self.max_messages - (1 if system_msg else 0)

        # If we need to trim, ensure we preserve complete user-assistant pairs
        if len(conv_messages) > max_conv_messages:
            keep_count = max_conv_messages

            # Check what role we'd be starting with after the trim
            start_index = len(conv_messages) - keep_count
            # If we're starting with an 'assistant' message, that means we're breaking a pair
            if start_index < len(conv_messages) and conv_messages[start_index].get('role') == 'assistant':
                # Move forward to the next user message to preserve the pair
                keep_count -= 1

            conv_messages = conv_messages[-keep_count:] if keep_count > 0 else []
            # Ensure the last message is always an assistant response
            if conv_messages and conv_messages[-1].get('role') == 'user':
                conv_messages = conv_messages[:-1]

        # Reconstruct the message list
        result = []
        if system_msg:
            result.append(system_msg)
        result.extend(conv_messages)
        return result

    def _cleanup(self, conn):
        """Delete old conversations past max_age_hours."""
        if not self.max_age_hours:
            return

        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.max_age_hours)
        conn.execute(
            'DELETE FROM conversation_store WHERE updated_at < ?',
            (cutoff.isoformat(),)
        )

    def create_session(self, model_type: str, initial_messages=None) -> str:
        """
        Create a new conversation session.

        Args:
            model_type: Model identifier (e.g., 'flux', 'sdxl')
            initial_messages: Optional list of initial messages

        Returns:
            session_id: Unique session identifier
        """
        session_id = secrets.token_urlsafe(16)
        messages = initial_messages or []
        self.save_messages(session_id, messages, model_type)
        return session_id

    def get_conversation(self, session_id: Optional[str]):
        """
        Retrieve conversation messages for a session.

        Args:
            session_id: Session identifier

        Returns:
            Tuple of (messages, model_type) or ([], None) if not found
        """
        if not session_id:
            return [], None

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT conversation, model_type FROM conversation_store WHERE session_id = ?',
                (session_id,)
            )
            row = cursor.fetchone()

        if not row:
            return [], None

        try:
            conversation = json.loads(row[0])
        except json.JSONDecodeError:
            conversation = []

        return conversation, row[1]

    def save_messages(self, session_id: str, messages, model_type: str):
        """
        Save conversation messages for a session (with trimming).

        Args:
            session_id: Session identifier
            messages: List of message dicts
            model_type: Model identifier

        Returns:
            Trimmed messages that were saved
        """
        trimmed = self._trim_messages(messages)
        serialized = json.dumps(trimmed)
        timestamp = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            conn.execute('''
                INSERT INTO conversation_store (session_id, model_type, conversation, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    model_type=excluded.model_type,
                    conversation=excluded.conversation,
                    updated_at=excluded.updated_at
            ''', (session_id, model_type, serialized, timestamp))
            self._cleanup(conn)
            conn.commit()

        return trimmed

    def delete_session(self, session_id: Optional[str]):
        """
        Delete a conversation session.

        Args:
            session_id: Session identifier
        """
        if not session_id:
            return

        with self._connect() as conn:
            conn.execute('DELETE FROM conversation_store WHERE session_id = ?', (session_id,))
            conn.commit()

    def clear_all(self):
        """Delete all conversation sessions."""
        with self._connect() as conn:
            conn.execute('DELETE FROM conversation_store')
            conn.commit()


def save_to_history(user_input, output, model, presets, mode):
    """
    Save a generated prompt to the history database.

    Args:
        user_input: The user's input text
        output: The generated prompt output
        model: The model type (flux or sdxl)
        presets: Dictionary of preset selections
        mode: The generation mode (oneshot or chat)

    Returns:
        int: The ID of the inserted record, or None if failed
    """
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()

        timestamp = datetime.now(timezone.utc).isoformat()
        presets_json = json.dumps(presets)

        cursor.execute('''
            INSERT INTO prompt_history (timestamp, user_input, generated_output, model, presets, mode)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, user_input, output, model, presets_json, mode))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.debug(f"Saved prompt to history with ID: {record_id}")
        return record_id
    except Exception as e:
        logger.error(f"Failed to save to history: {str(e)}")
        return None


def get_history(limit=50, search_query=None):
    """
    Retrieve prompt history from the database.

    Args:
        limit: Maximum number of records to return (default: 50)
        search_query: Optional search string to filter results

    Returns:
        list: List of history records as dictionaries
    """
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        if search_query:
            # Search in user_input and generated_output
            cursor.execute('''
                SELECT id, timestamp, user_input, generated_output, model, presets, mode
                FROM prompt_history
                WHERE user_input LIKE ? OR generated_output LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (f'%{search_query}%', f'%{search_query}%', limit))
        else:
            cursor.execute('''
                SELECT id, timestamp, user_input, generated_output, model, presets, mode
                FROM prompt_history
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        # Convert rows to dictionaries
        history = []
        for row in rows:
            history.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'user_input': row['user_input'],
                'generated_output': row['generated_output'],
                'model': row['model'],
                'presets': json.loads(row['presets']) if row['presets'] else {},
                'mode': row['mode']
            })

        logger.debug(f"Retrieved {len(history)} history records")
        return history
    except Exception as e:
        logger.error(f"Failed to retrieve history: {str(e)}")
        return []


def delete_history_item(item_id):
    """
    Delete a specific history item from the database.

    Args:
        item_id: The ID of the history item to delete

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM prompt_history WHERE id = ?', (item_id,))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if deleted:
            logger.info(f"Deleted history item with ID: {item_id}")
        else:
            logger.warning(f"No history item found with ID: {item_id}")

        return deleted
    except Exception as e:
        logger.error(f"Failed to delete history item: {str(e)}")
        return False
