#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt Generator Web App
Talks to local Ollama to generate detailed prompts for ComfyUI

Configuration:
    You can customize the application by creating a .env file in the root directory.
    Copy .env.example to .env and modify the values:
    - OLLAMA_URL: URL for the Ollama API endpoint
    - OLLAMA_MODEL: Default model to use (e.g., qwen3:latest, llama2, mistral)
    - FLASK_PORT: Port for the web server (default: 5000)
    - FLASK_DEBUG: Debug mode (true/false)
    - FLASK_SECRET_KEY: Secret key for session management (generate a random one for production)
"""

from flask import Flask, render_template, request, jsonify, session
import requests
import json
import secrets
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from requests.exceptions import ConnectionError, Timeout, RequestException
import sqlite3
from datetime import datetime

# Load environment variables from .env file if it exists
load_dotenv()

# Configuration with environment variable fallbacks
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434/api/generate')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:latest')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() in ('true', '1', 'yes')
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# Configure logging
def setup_logging():
    """Configure logging with both console and file handlers"""
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Convert string log level to logging constant
    numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)

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

# Initialize logging
logger = setup_logging()

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


# Database Configuration
DB_PATH = 'prompt_history.db'


def init_db():
    """Initialize the database and create the history table if it doesn't exist"""
    logger.info("Initializing prompt history database")
    conn = sqlite3.connect(DB_PATH)
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

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


def save_to_history(user_input, output, model, presets, mode):
    """
    Save a generated prompt to the history database

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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        timestamp = datetime.utcnow().isoformat()
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
    Retrieve prompt history from the database

    Args:
        limit: Maximum number of records to return (default: 50)
        search_query: Optional search string to filter results

    Returns:
        list: List of history records as dictionaries
    """
    try:
        conn = sqlite3.connect(DB_PATH)
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
    Delete a specific history item from the database

    Args:
        item_id: The ID of the history item to delete

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
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


# Custom Exception Classes
class OllamaConnectionError(Exception):
    """Raised when unable to connect to Ollama"""
    pass


class OllamaTimeoutError(Exception):
    """Raised when Ollama request times out"""
    pass


class OllamaModelNotFoundError(Exception):
    """Raised when the requested model is not found"""
    pass


class OllamaAPIError(Exception):
    """Raised when Ollama returns an error response"""
    pass


# Preset options for prompt enhancement
PRESETS = {
    "styles": {
        "None": "",
        "Cinematic": "cinematic, dramatic, movie still, film grain",
        "Anime": "anime style, manga, cel shaded, vibrant colors",
        "Photorealistic": "photorealistic, highly detailed, 8k uhd, dslr, high quality",
        "Oil Painting": "oil painting, brushstrokes, traditional art, painterly",
        "Digital Art": "digital art, concept art, detailed, artstation trending",
        "Watercolor": "watercolor painting, soft colors, artistic, flowing",
        "Cyberpunk": "cyberpunk, neon lights, futuristic, dystopian, tech noir",
        "Fantasy Art": "fantasy art, magical, epic, detailed, ethereal",
        "Comic Book": "comic book style, bold lines, halftone dots, pop art",
        "Minimalist": "minimalist, clean, simple, modern, elegant",
        "Surreal": "surreal, dreamlike, abstract, unusual, imaginative",
        "Vintage": "vintage, retro, nostalgic, aged, classic",
        "3D Render": "3d render, octane render, unreal engine, ray tracing",
        "Pencil Sketch": "pencil sketch, graphite, hand drawn, detailed shading"
    },
    
    "artists": {
        "None": "",
        "Greg Rutkowski": "in the style of Greg Rutkowski",
        "Artgerm": "in the style of Artgerm",
        "Alphonse Mucha": "in the style of Alphonse Mucha, art nouveau",
        "H.R. Giger": "in the style of H.R. Giger, biomechanical",
        "Hayao Miyazaki": "Studio Ghibli style, Hayao Miyazaki",
        "Ross Tran": "in the style of Ross Tran",
        "Loish": "in the style of Loish",
        "Makoto Shinkai": "in the style of Makoto Shinkai",
        "James Gurney": "in the style of James Gurney",
        "Ansel Adams": "Ansel Adams photography style",
        "Annie Leibovitz": "Annie Leibovitz portrait photography style",
        "Steve McCurry": "Steve McCurry documentary photography style",
        "Peter Lindbergh": "Peter Lindbergh fashion photography style",
        "Sebastião Salgado": "Sebastião Salgado black and white photography",
        "Irving Penn": "Irving Penn studio photography style",
        "Moebius": "in the style of Moebius, detailed linework",
        "Simon Stålenhag": "in the style of Simon Stålenhag",
        "Zdzisław Beksiński": "in the style of Zdzisław Beksiński, dystopian"
    },
    
    "composition": {
        "None": "",
        "Portrait": "portrait composition, centered subject",
        "Landscape": "landscape composition, wide view",
        "Close-up": "close-up shot, detailed, intimate",
        "Wide Shot": "wide shot, establishing shot, full scene",
        "Medium Shot": "medium shot, waist up, balanced framing",
        "Extreme Close-up": "extreme close-up, macro detail",
        "Bird's Eye View": "bird's eye view, top-down perspective, aerial view",
        "Low Angle": "low angle shot, looking up, dramatic perspective",
        "High Angle": "high angle shot, looking down",
        "Dutch Angle": "dutch angle, tilted, dynamic composition",
        "Rule of Thirds": "rule of thirds composition, balanced",
        "Symmetrical": "symmetrical composition, centered, balanced",
        "Leading Lines": "leading lines composition, depth, perspective",
        "Frame within Frame": "frame within frame composition",
        "Golden Ratio": "golden ratio composition, fibonacci spiral"
    },
    
    "lighting": {
        "None": "",
        "Golden Hour": "golden hour lighting, warm, soft sunlight",
        "Blue Hour": "blue hour lighting, cool tones, twilight",
        "Studio Lighting": "professional studio lighting, three point lighting",
        "Dramatic Shadows": "dramatic shadows, high contrast, chiaroscuro",
        "Soft Diffused": "soft diffused lighting, even, flattering",
        "Neon Lighting": "neon lighting, vibrant colors, glowing",
        "Candlelight": "candlelight, warm glow, intimate atmosphere",
        "Backlit": "backlit, rim lighting, silhouette, halo effect",
        "Natural Window Light": "natural window light, soft, directional",
        "Harsh Sunlight": "harsh sunlight, strong shadows, high contrast",
        "Overcast": "overcast lighting, soft shadows, even illumination",
        "Volumetric Lighting": "volumetric lighting, god rays, atmospheric",
        "Moonlight": "moonlight, cool tones, mysterious atmosphere",
        "Fire Light": "firelight, warm orange glow, flickering",
        "Underwater Light": "underwater lighting, caustics, diffused"
    }
}

# System prompts for different models
SYSTEM_PROMPTS = {
    "sdxl": """You are an expert prompt engineer for Stable Diffusion XL (SDXL). When users describe an image idea, you expand it into a detailed, effective prompt.

The user may provide preset selections for style, artist/photographer, composition, and lighting. When these are provided, incorporate them naturally into the prompt.

SDXL works best with:
- Natural language descriptions with rich details
- Quality tags like: masterpiece, best quality, highly detailed, sharp focus, 8k
- Specific details about: subject, composition, lighting, camera angle, art style, mood, colors
- Negative prompts to avoid unwanted elements

Format your response as:
PROMPT: [detailed positive prompt incorporating any presets]
NEGATIVE: [negative prompt with things to avoid]

Be creative, specific, and detailed. Weave the preset selections naturally into the description.""",

    "flux": """You are an expert prompt engineer for Flux models. When users describe an image idea, you expand it into a detailed, effective prompt.

The user may provide preset selections for style, artist/photographer, composition, and lighting. When these are provided, incorporate them naturally and seamlessly into the prompt description.

Flux models work best with:
- Natural language, conversational style prompts
- Very detailed scene descriptions
- Specific lighting and atmospheric details
- Camera angles and composition details
- Art style and mood descriptions
- No need for quality tags or negative prompts (Flux ignores them)

Format your response as:
PROMPT: [single detailed natural language prompt incorporating any presets naturally]

Be extremely descriptive and creative. Write like you're describing a photograph or painting in detail. Integrate the preset selections seamlessly into the narrative."""
}

def call_ollama(messages, model=None, stream=False):
    """
    Call Ollama API with messages

    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Model name (optional, defaults to OLLAMA_MODEL)
        stream: If True, returns a generator that yields tokens; if False, returns complete response

    Returns:
        str: The complete response from Ollama (if stream=False)
        generator: A generator that yields tokens (if stream=True)

    Raises:
        OllamaConnectionError: If cannot connect to Ollama server
        OllamaTimeoutError: If the request times out
        OllamaModelNotFoundError: If the requested model is not found
        OllamaAPIError: If Ollama returns an error response
    """
    if model is None:
        model = OLLAMA_MODEL

    logger.debug(f"Attempting to call Ollama API with model: {model}, stream: {stream}")

    # Build the prompt from messages
    system_msg = ""
    conversation = ""

    for msg in messages:
        if msg["role"] == "system":
            system_msg = msg["content"]
        elif msg["role"] == "user":
            conversation += f"User: {msg['content']}\n"
        elif msg["role"] == "assistant":
            conversation += f"Assistant: {msg['content']}\n"

    # Format the full prompt
    if system_msg:
        full_prompt = f"{system_msg}\n\n{conversation}Assistant:"
    else:
        full_prompt = f"{conversation}Assistant:"

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": stream
    }

    if stream:
        # Return generator for streaming mode
        return _stream_ollama_response(payload, model)
    else:
        # Non-streaming mode (existing behavior)
        return _call_ollama_sync(payload, model)


def _stream_ollama_response(payload, model):
    """
    Generator function that streams tokens from Ollama

    Args:
        payload: The request payload
        model: Model name for error messages

    Yields:
        str: Individual tokens as they arrive
    """
    try:
        logger.debug(f"Sending streaming request to Ollama at {OLLAMA_URL}")
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120)

        # Check for specific error status codes
        if response.status_code == 404:
            error_detail = response.json().get('error', '') if response.headers.get('content-type', '').startswith('application/json') else ''
            if 'model' in error_detail.lower() or 'not found' in error_detail.lower():
                logger.error(f"Ollama model not found: {model}")
                raise OllamaModelNotFoundError(
                    f"Model '{model}' is not installed.\n\n"
                    f"To fix this, run:\n"
                    f"  ollama pull {model}\n\n"
                    f"To see available models, visit: https://ollama.com/library\n"
                    f"To list installed models, run: ollama list"
                )
            logger.error(f"Ollama API endpoint not found: {error_detail}")
            raise OllamaAPIError(
                f"Ollama API endpoint not found.\n\n"
                f"To fix this:\n"
                f"1. Verify Ollama is running: curl http://localhost:11434\n"
                f"2. Check OLLAMA_URL in .env (current: {OLLAMA_URL})\n"
                f"3. Update Ollama to latest version: curl -fsSL https://ollama.com/install.sh | sh\n\n"
                f"Error details: {error_detail}"
            )

        # Raise for other HTTP errors
        response.raise_for_status()

        # Stream the response line by line
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)

                    # Check for errors in the chunk
                    if 'error' in chunk:
                        logger.error(f"Ollama API returned error: {chunk['error']}")
                        raise OllamaAPIError(f"Ollama API error: {chunk['error']}")

                    # Yield the token if present
                    if 'response' in chunk:
                        yield chunk['response']

                    # Check if done
                    if chunk.get('done', False):
                        logger.debug("Streaming completed successfully")
                        break

                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse streaming chunk: {line}")
                    continue

    except Timeout:
        logger.error(f"Ollama request timed out after 120 seconds for model: {model}")
        raise OllamaTimeoutError(
            f"Request timed out after 120 seconds.\n\n"
            f"To fix this:\n"
            f"1. Try a smaller/faster model: ollama pull qwen2.5:0.5b\n"
            f"2. Check Ollama status: ollama ps\n"
            f"3. Ensure your system has enough RAM (8GB+ recommended)\n"
            f"4. Try restarting Ollama: pkill ollama && ollama serve\n\n"
            f"Current model '{model}' may be too large for your system."
        )
    except ConnectionError:
        logger.error(f"Failed to connect to Ollama at {OLLAMA_URL}")
        raise OllamaConnectionError(
            f"Cannot connect to Ollama at {OLLAMA_URL}\n\n"
            f"To fix this:\n"
            f"1. Start Ollama: ollama serve\n"
            f"2. Verify it's running: curl {OLLAMA_URL.rsplit('/api', 1)[0]}\n"
            f"3. Check your OLLAMA_URL setting in .env\n\n"
            f"For installation help: https://ollama.com/download"
        )
    except (OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError, OllamaAPIError):
        # Re-raise our custom exceptions (already logged)
        raise
    except RequestException as e:
        logger.error(f"Request exception when calling Ollama: {str(e)}")
        raise OllamaAPIError(
            f"Network error communicating with Ollama: {str(e)}\n\n"
            f"To fix this:\n"
            f"1. Check network connectivity to {OLLAMA_URL}\n"
            f"2. Verify Ollama is running: curl http://localhost:11434\n"
            f"3. Check firewall settings if using remote Ollama"
        )
    except Exception as e:
        logger.error(f"Unexpected error when streaming from Ollama: {str(e)}", exc_info=True)
        raise OllamaAPIError(
            f"Unexpected error: {str(e)}\n\n"
            f"To troubleshoot:\n"
            f"1. Check application logs: tail -f logs/app.log\n"
            f"2. Verify Ollama is working: ollama run {model} \"test\"\n"
            f"3. Report issue with logs at: https://github.com/CreativeNewEra/comfyui-prompt-generator/issues"
        )


def _call_ollama_sync(payload, model):
    """
    Synchronous call to Ollama (non-streaming)

    Args:
        payload: The request payload
        model: Model name for error messages

    Returns:
        str: The complete response from Ollama
    """
    try:
        logger.debug(f"Sending request to Ollama at {OLLAMA_URL}")
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)

        # Check for specific error status codes
        if response.status_code == 404:
            error_detail = response.json().get('error', '') if response.headers.get('content-type', '').startswith('application/json') else ''
            if 'model' in error_detail.lower() or 'not found' in error_detail.lower():
                logger.error(f"Ollama model not found: {model}")
                raise OllamaModelNotFoundError(
                    f"Model '{model}' is not installed.\n\n"
                    f"To fix this, run:\n"
                    f"  ollama pull {model}\n\n"
                    f"To see available models, visit: https://ollama.com/library\n"
                    f"To list installed models, run: ollama list"
                )
            logger.error(f"Ollama API endpoint not found: {error_detail}")
            raise OllamaAPIError(
                f"Ollama API endpoint not found.\n\n"
                f"To fix this:\n"
                f"1. Verify Ollama is running: curl http://localhost:11434\n"
                f"2. Check OLLAMA_URL in .env (current: {OLLAMA_URL})\n"
                f"3. Update Ollama to latest version: curl -fsSL https://ollama.com/install.sh | sh\n\n"
                f"Error details: {error_detail}"
            )

        # Raise for other HTTP errors
        response.raise_for_status()

        # Parse response
        result = response.json()

        # Check if response contains an error field
        if 'error' in result:
            logger.error(f"Ollama API returned error: {result['error']}")
            raise OllamaAPIError(
                f"Ollama API error: {result['error']}\n\n"
                f"To troubleshoot:\n"
                f"1. Check Ollama logs: journalctl -u ollama -f (Linux) or Console.app (Mac)\n"
                f"2. Verify model is working: ollama run {model} \"test\"\n"
                f"3. Check available resources: ollama ps\n"
                f"4. Try restarting Ollama service"
            )

        # Return the generated response
        if 'response' in result:
            logger.debug("Successfully received response from Ollama")
            return result['response']
        else:
            logger.error("Unexpected response format from Ollama API")
            raise OllamaAPIError(
                f"Unexpected response format from Ollama.\n\n"
                f"To fix this:\n"
                f"1. Update Ollama: curl -fsSL https://ollama.com/install.sh | sh\n"
                f"2. Verify API is working: curl {OLLAMA_URL.rsplit('/api', 1)[0]}/api/tags\n"
                f"3. Check logs: tail -f logs/app.log\n\n"
                f"The Ollama API may have changed or be misconfigured."
            )

    except Timeout:
        logger.error(f"Ollama request timed out after 120 seconds for model: {model}")
        raise OllamaTimeoutError(
            f"Request timed out after 120 seconds.\n\n"
            f"To fix this:\n"
            f"1. Try a smaller/faster model: ollama pull qwen2.5:0.5b\n"
            f"2. Check Ollama status: ollama ps\n"
            f"3. Ensure your system has enough RAM (8GB+ recommended)\n"
            f"4. Try restarting Ollama: pkill ollama && ollama serve\n\n"
            f"Current model '{model}' may be too large for your system."
        )
    except ConnectionError:
        logger.error(f"Failed to connect to Ollama at {OLLAMA_URL}")
        raise OllamaConnectionError(
            f"Cannot connect to Ollama at {OLLAMA_URL}\n\n"
            f"To fix this:\n"
            f"1. Start Ollama: ollama serve\n"
            f"2. Verify it's running: curl {OLLAMA_URL.rsplit('/api', 1)[0]}\n"
            f"3. Check your OLLAMA_URL setting in .env\n\n"
            f"For installation help: https://ollama.com/download"
        )
    except (OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError, OllamaAPIError):
        # Re-raise our custom exceptions (already logged)
        raise
    except RequestException as e:
        logger.error(f"Request exception when calling Ollama: {str(e)}")
        raise OllamaAPIError(
            f"Network error communicating with Ollama: {str(e)}\n\n"
            f"To fix this:\n"
            f"1. Check network connectivity to {OLLAMA_URL}\n"
            f"2. Verify Ollama is running: curl http://localhost:11434\n"
            f"3. Check firewall settings if using remote Ollama"
        )
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON response from Ollama API")
        raise OllamaAPIError(
            f"Invalid response from Ollama (not valid JSON).\n\n"
            f"To fix this:\n"
            f"1. Update Ollama: curl -fsSL https://ollama.com/install.sh | sh\n"
            f"2. Restart Ollama service\n"
            f"3. Verify API endpoint: curl {OLLAMA_URL.rsplit('/api', 1)[0]}/api/version\n\n"
            f"This usually indicates an Ollama version mismatch or corruption."
        )
    except KeyError as e:
        logger.error(f"Missing expected field in Ollama response: {str(e)}")
        raise OllamaAPIError(
            f"Incomplete response from Ollama (missing field: {str(e)}).\n\n"
            f"To fix this:\n"
            f"1. Update Ollama to latest version\n"
            f"2. Try a different model: ollama pull qwen2.5:latest\n"
            f"3. Check Ollama status: ollama ps"
        )
    except Exception as e:
        logger.error(f"Unexpected error when calling Ollama: {str(e)}", exc_info=True)
        raise OllamaAPIError(
            f"Unexpected error: {str(e)}\n\n"
            f"To troubleshoot:\n"
            f"1. Check application logs: tail -f logs/app.log\n"
            f"2. Verify Ollama is working: ollama run {model} \"test\"\n"
            f"3. Report issue with logs at: https://github.com/CreativeNewEra/comfyui-prompt-generator/issues"
        )

# Error Handlers
@app.errorhandler(400)
def bad_request_error(error):
    """Handle 400 errors"""
    logger.warning(f"Bad request: {str(error)}")
    return jsonify({
        'error': 'Bad request',
        'message': 'The request could not be understood or was missing required parameters',
        'status': 400
    }), 400


@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    logger.warning(f"Not found: {request.path}")
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found on this server',
        'status': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'message': 'An internal server error occurred. Please try again later.',
        'status': 500
    }), 500


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Handle any unexpected errors"""
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    return jsonify({
        'error': 'Unexpected error',
        'message': 'An unexpected error occurred. Please try again.',
        'status': 500
    }), 500


@app.errorhandler(OllamaConnectionError)
def handle_connection_error(error):
    """Handle Ollama connection errors"""
    logger.error(f"Ollama connection error: {str(error)}")
    return jsonify({
        'error': 'Connection Error',
        'message': str(error),
        'status': 503,
        'type': 'connection_error'
    }), 503


@app.errorhandler(OllamaTimeoutError)
def handle_timeout_error(error):
    """Handle Ollama timeout errors"""
    logger.error(f"Ollama timeout error: {str(error)}")
    return jsonify({
        'error': 'Timeout Error',
        'message': str(error),
        'status': 504,
        'type': 'timeout_error'
    }), 504


@app.errorhandler(OllamaModelNotFoundError)
def handle_model_not_found_error(error):
    """Handle Ollama model not found errors"""
    logger.error(f"Ollama model not found: {str(error)}")
    return jsonify({
        'error': 'Model Not Found',
        'message': str(error),
        'status': 404,
        'type': 'model_not_found'
    }), 404


@app.errorhandler(OllamaAPIError)
def handle_api_error(error):
    """Handle Ollama API errors"""
    logger.error(f"Ollama API error: {str(error)}")
    return jsonify({
        'error': 'API Error',
        'message': str(error),
        'status': 502,
        'type': 'api_error'
    }), 502


# Routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/presets', methods=['GET'])
def get_presets():
    """Get available presets"""
    return jsonify(PRESETS)

@app.route('/generate', methods=['POST'])
def generate():
    """Generate a prompt (one-shot mode)"""
    logger.info("Received /generate request")

    # Validate request has JSON data
    if not request.json:
        logger.warning("Generate request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    data = request.json
    user_input = data.get('input', '').strip()
    model_type = data.get('model', 'flux')

    # Get preset selections
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')

    if not user_input:
        logger.warning("Generate request with empty input")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a description'
        }), 400

    logger.info(f"Generating prompt for model: {model_type}")
    logger.debug(f"User input preview: {user_input[:50]}...")

    # Build context with presets
    preset_context = []
    if style != 'None':
        preset_context.append(f"Style: {PRESETS['styles'][style]}")
    if artist != 'None':
        preset_context.append(f"Artist/Style: {PRESETS['artists'][artist]}")
    if composition != 'None':
        preset_context.append(f"Composition: {PRESETS['composition'][composition]}")
    if lighting != 'None':
        preset_context.append(f"Lighting: {PRESETS['lighting'][lighting]}")

    # Build the full user message
    if preset_context:
        preset_info = "\n".join(preset_context)
        full_input = f"User's image idea: {user_input}\n\nSelected presets:\n{preset_info}\n\nPlease create a detailed prompt incorporating these elements."
    else:
        full_input = user_input

    # Get appropriate system prompt
    system_prompt = SYSTEM_PROMPTS.get(model_type, SYSTEM_PROMPTS['flux'])

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_input}
    ]

    result = call_ollama(messages)
    logger.info("Successfully generated prompt")

    # Save to history
    presets_dict = {
        'style': style,
        'artist': artist,
        'composition': composition,
        'lighting': lighting
    }
    save_to_history(user_input, result, model_type, presets_dict, 'oneshot')

    return jsonify({
        'result': result,
        'model': model_type
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Conversational mode - refine ideas back and forth"""
    logger.info("Received /chat request")

    # Validate request has JSON data
    if not request.json:
        logger.warning("Chat request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    data = request.json
    user_message = data.get('message', '').strip()
    model_type = data.get('model', 'flux')

    # Get preset selections
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')

    if not user_message:
        logger.warning("Chat request with empty message")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a message'
        }), 400

    # Get or initialize conversation history
    if 'conversation' not in session:
        logger.info("Starting new chat conversation")
        session['conversation'] = []
        session['model_type'] = model_type

    # If model changed, reset conversation
    if session.get('model_type') != model_type:
        logger.info(f"Model changed to {model_type}, resetting conversation")
        session['conversation'] = []
        session['model_type'] = model_type

    # Add system prompt if starting new conversation
    if not session['conversation']:
        system_prompt = SYSTEM_PROMPTS.get(model_type, SYSTEM_PROMPTS['flux'])
        session['conversation'].append({
            "role": "system",
            "content": system_prompt
        })

    logger.debug(f"Chat message preview: {user_message[:50]}...")

    # Build context with presets
    preset_context = []
    if style != 'None':
        preset_context.append(f"Style: {PRESETS['styles'][style]}")
    if artist != 'None':
        preset_context.append(f"Artist/Style: {PRESETS['artists'][artist]}")
    if composition != 'None':
        preset_context.append(f"Composition: {PRESETS['composition'][composition]}")
    if lighting != 'None':
        preset_context.append(f"Lighting: {PRESETS['lighting'][lighting]}")

    # Build the full user message
    if preset_context:
        preset_info = "\n".join(preset_context)
        full_message = f"{user_message}\n\n[Selected presets: {preset_info}]"
    else:
        full_message = user_message

    # Add user message
    session['conversation'].append({
        "role": "user",
        "content": full_message
    })

    # Get response from Ollama
    result = call_ollama(session['conversation'])

    # Add assistant response to history
    session['conversation'].append({
        "role": "assistant",
        "content": result
    })

    # Keep conversation manageable (last 10 messages + system)
    if len(session['conversation']) > 21:  # system + 20 messages
        logger.debug("Trimming conversation history to maintain manageable size")
        session['conversation'] = [session['conversation'][0]] + session['conversation'][-20:]

    session.modified = True
    logger.info("Successfully processed chat message")

    # Save to history
    presets_dict = {
        'style': style,
        'artist': artist,
        'composition': composition,
        'lighting': lighting
    }
    save_to_history(user_message, result, model_type, presets_dict, 'chat')

    return jsonify({
        'result': result,
        'model': model_type
    })

@app.route('/generate-stream', methods=['POST'])
def generate_stream():
    """Generate a prompt with streaming (one-shot mode)"""
    logger.info("Received /generate-stream request")

    # Validate request has JSON data
    if not request.json:
        logger.warning("Generate-stream request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    data = request.json
    user_input = data.get('input', '').strip()
    model_type = data.get('model', 'flux')

    # Get preset selections
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')

    if not user_input:
        logger.warning("Generate-stream request with empty input")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a description'
        }), 400

    logger.info(f"Generating streaming prompt for model: {model_type}")
    logger.debug(f"User input preview: {user_input[:50]}...")

    # Build context with presets
    preset_context = []
    if style != 'None':
        preset_context.append(f"Style: {PRESETS['styles'][style]}")
    if artist != 'None':
        preset_context.append(f"Artist/Style: {PRESETS['artists'][artist]}")
    if composition != 'None':
        preset_context.append(f"Composition: {PRESETS['composition'][composition]}")
    if lighting != 'None':
        preset_context.append(f"Lighting: {PRESETS['lighting'][lighting]}")

    # Build the full user message
    if preset_context:
        preset_info = "\n".join(preset_context)
        full_input = f"User's image idea: {user_input}\n\nSelected presets:\n{preset_info}\n\nPlease create a detailed prompt incorporating these elements."
    else:
        full_input = user_input

    # Get appropriate system prompt
    system_prompt = SYSTEM_PROMPTS.get(model_type, SYSTEM_PROMPTS['flux'])

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_input}
    ]

    def generate():
        """Generator function for SSE streaming"""
        try:
            full_response = ""
            for token in call_ollama(messages, stream=True):
                full_response += token
                # Send token as SSE event
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Send completion event
            yield f"data: {json.dumps({'done': True})}\n\n"

            # Save to history after completion
            presets_dict = {
                'style': style,
                'artist': artist,
                'composition': composition,
                'lighting': lighting
            }
            save_to_history(user_input, full_response, model_type, presets_dict, 'oneshot')
            logger.info("Successfully generated streaming prompt")

        except (OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError, OllamaAPIError) as e:
            # Send error event
            yield f"data: {json.dumps({'error': str(e), 'type': type(e).__name__})}\n\n"
            logger.error(f"Error during streaming: {str(e)}")
        except Exception as e:
            # Send generic error event
            yield f"data: {json.dumps({'error': f'Unexpected error: {str(e)}', 'type': 'UnexpectedError'})}\n\n"
            logger.error(f"Unexpected error during streaming: {str(e)}", exc_info=True)

    return app.response_class(generate(), mimetype='text/event-stream')


@app.route('/chat-stream', methods=['POST'])
def chat_stream():
    """Conversational mode with streaming - refine ideas back and forth"""
    logger.info("Received /chat-stream request")

    # Validate request has JSON data
    if not request.json:
        logger.warning("Chat-stream request missing JSON data")
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    data = request.json
    user_message = data.get('message', '').strip()
    model_type = data.get('model', 'flux')

    # Get preset selections
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')

    if not user_message:
        logger.warning("Chat-stream request with empty message")
        return jsonify({
            'error': 'Invalid input',
            'message': 'Please provide a message'
        }), 400

    # Get or initialize conversation history
    if 'conversation' not in session:
        logger.info("Starting new chat conversation")
        session['conversation'] = []
        session['model_type'] = model_type

    # If model changed, reset conversation
    if session.get('model_type') != model_type:
        logger.info(f"Model changed to {model_type}, resetting conversation")
        session['conversation'] = []
        session['model_type'] = model_type

    # Add system prompt if starting new conversation
    if not session['conversation']:
        system_prompt = SYSTEM_PROMPTS.get(model_type, SYSTEM_PROMPTS['flux'])
        session['conversation'].append({
            "role": "system",
            "content": system_prompt
        })

    logger.debug(f"Chat message preview: {user_message[:50]}...")

    # Build context with presets
    preset_context = []
    if style != 'None':
        preset_context.append(f"Style: {PRESETS['styles'][style]}")
    if artist != 'None':
        preset_context.append(f"Artist/Style: {PRESETS['artists'][artist]}")
    if composition != 'None':
        preset_context.append(f"Composition: {PRESETS['composition'][composition]}")
    if lighting != 'None':
        preset_context.append(f"Lighting: {PRESETS['lighting'][lighting]}")

    # Build the full user message
    if preset_context:
        preset_info = "\n".join(preset_context)
        full_message = f"{user_message}\n\n[Selected presets: {preset_info}]"
    else:
        full_message = user_message

    # Add user message
    session['conversation'].append({
        "role": "user",
        "content": full_message
    })

    # Make a copy of the conversation for the request
    conversation_snapshot = list(session['conversation'])

    # Store session data that we'll need after streaming
    session_conversation = session['conversation']

    def generate():
        """Generator function for SSE streaming"""
        full_response = ""
        try:
            for token in call_ollama(conversation_snapshot, stream=True):
                full_response += token
                # Send token as SSE event
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Send completion event
            yield f"data: {json.dumps({'done': True})}\n\n"

            logger.info("Successfully processed streaming chat message")

        except (OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError, OllamaAPIError) as e:
            # Send error event
            yield f"data: {json.dumps({'error': str(e), 'type': type(e).__name__})}\n\n"
            logger.error(f"Error during streaming: {str(e)}")
        except Exception as e:
            # Send generic error event
            yield f"data: {json.dumps({'error': f'Unexpected error: {str(e)}', 'type': 'UnexpectedError'})}\n\n"
            logger.error(f"Unexpected error during streaming: {str(e)}", exc_info=True)
        finally:
            # Update session after streaming completes
            # Note: This happens after the response is sent, so we update via a background task
            if full_response:
                # Add assistant response to session history
                session_conversation.append({
                    "role": "assistant",
                    "content": full_response
                })

                # Keep conversation manageable (last 10 messages + system)
                if len(session_conversation) > 21:  # system + 20 messages
                    logger.debug("Trimming conversation history to maintain manageable size")
                    # Trim but keep the reference valid
                    trimmed = [session_conversation[0]] + session_conversation[-20:]
                    session_conversation.clear()
                    session_conversation.extend(trimmed)

                # Save to history after completion
                presets_dict = {
                    'style': style,
                    'artist': artist,
                    'composition': composition,
                    'lighting': lighting
                }
                save_to_history(user_message, full_response, model_type, presets_dict, 'chat')

    return app.response_class(generate(), mimetype='text/event-stream')


@app.route('/reset', methods=['POST'])
def reset():
    """Reset conversation history"""
    logger.info("Resetting conversation history")
    session.pop('conversation', None)
    session.pop('model_type', None)
    return jsonify({'status': 'reset'})


@app.route('/history', methods=['GET'])
def get_prompt_history():
    """Get prompt history (last 50 records by default)"""
    logger.info("Received /history request")

    limit = request.args.get('limit', 50, type=int)
    search_query = request.args.get('q', None)

    # Validate limit
    if limit < 1 or limit > 200:
        return jsonify({
            'error': 'Invalid limit',
            'message': 'Limit must be between 1 and 200'
        }), 400

    history = get_history(limit=limit, search_query=search_query)

    logger.info(f"Retrieved {len(history)} history records")
    return jsonify({
        'history': history,
        'count': len(history)
    })


@app.route('/history/<int:history_id>', methods=['DELETE'])
def delete_prompt_history(history_id):
    """Delete a specific history item"""
    logger.info(f"Received request to delete history item {history_id}")

    success = delete_history_item(history_id)

    if success:
        return jsonify({
            'status': 'deleted',
            'id': history_id
        })
    else:
        return jsonify({
            'error': 'Not found',
            'message': f'History item with ID {history_id} not found'
        }), 404

if __name__ == '__main__':
    # Initialize database
    init_db()

    print("\n" + "="*60)
    print("=== Prompt Generator Starting ===")
    print("="*60)
    print(f"\nOpen your browser to: http://localhost:{FLASK_PORT}")
    print(f"Using Ollama model: {OLLAMA_MODEL}")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"Log level: {LOG_LEVEL}")
    print("\n" + "-"*60)
    print("IMPORTANT: Make sure Ollama is running!")
    print("  Start Ollama: ollama serve")
    print("  Check status: curl http://localhost:11434")
    print("  Install model: ollama pull " + OLLAMA_MODEL)
    print("-"*60)
    print("\nPress Ctrl+C to stop\n")

    logger.info("="*60)
    logger.info("Starting Prompt Generator Application")
    logger.info("="*60)
    logger.info(f"Flask port: {FLASK_PORT}")
    logger.info(f"Flask debug mode: {FLASK_DEBUG}")
    logger.info(f"Ollama URL: {OLLAMA_URL}")
    logger.info(f"Ollama model: {OLLAMA_MODEL}")
    logger.info(f"Log level: {LOG_LEVEL}")
    logger.info("Application ready to accept requests")

    app.run(debug=FLASK_DEBUG, host='0.0.0.0', port=FLASK_PORT)
