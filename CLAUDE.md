# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **ComfyUI Prompt Generator** - a Flask web application that integrates with local Ollama to generate detailed prompts for ComfyUI image generation. It supports both Flux and SDXL models with dual operation modes (Quick Generate and Chat & Refine).

## Development Commands

### Quick Start with Make (Recommended)
```bash
# Complete setup
make install

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start the application
make run

# Run tests
make test

# Run linting
make lint

# View all available commands
make help
```

### Manual Setup (Alternative)
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# For development (includes pytest, flake8)
pip install -r requirements-dev.txt

# Run the application
python prompt_generator.py
```

### Testing
```bash
# Run all tests
make test
# or: pytest

# Run tests with coverage
make test-cov
# or: pytest --cov=prompt_generator --cov-report=html

# Run specific test file
pytest tests/test_app.py
pytest tests/test_presets.py
```

### Linting
```bash
# Run flake8
make lint
# or: flake8 prompt_generator.py tests/

# Configuration in .flake8 (max line length: 120)
```

### Ollama Setup
```bash
# Show Ollama setup instructions
make setup-ollama

# Verify Ollama is running
curl http://localhost:11434

# List installed models
ollama list

# Install a model
ollama pull qwen3:latest
```

## Architecture

### Core Application Structure
- **Backend**: `prompt_generator.py` - Flask application (~2,098 lines)
- **Frontend**: `templates/index.html` - Single-page application with embedded CSS/JS and dark mode
- **Database**: SQLite (`prompt_history.db`) - Auto-created for prompt history
- **Presets**: `presets.json` - Curated preset configurations (hot-reloadable)
- **Dependencies**: Flask 3.0.0, requests 2.31.0, python-dotenv 1.0.0, sqlite3 (built-in)
- **Tests**: `tests/` directory with pytest fixtures in `conftest.py`

### Key Routes
- `GET /` - Serves the main application (`templates/index.html`)
- `GET /presets` - Returns available preset configurations (JSON, hot-reloads from presets.json)
- `GET /models` - Returns list of installed Ollama models
- `POST /generate` - One-shot prompt generation (Quick Generate mode)
- `POST /generate-stream` - Streaming one-shot generation with Server-Sent Events
- `POST /chat` - Conversational prompt refinement (Chat & Refine mode)
- `POST /chat-stream` - Streaming conversational mode with real-time tokens
- `POST /reset` - Clears chat conversation history
- `GET /history` - Retrieve prompt generation history (supports search)
- `DELETE /history/<id>` - Delete a specific history item

### Error Handling
The application uses custom exception classes with specific HTTP error handlers:
- `OllamaConnectionError` → 503 Service Unavailable
- `OllamaTimeoutError` → 504 Gateway Timeout
- `OllamaModelNotFoundError` → 404 Not Found
- `OllamaAPIError` → 502 Bad Gateway

All routes return JSON error responses with `error`, `message`, `status`, and `type` fields.

### Session Management
- Chat mode uses Flask server-side sessions (signed cookies)
- Conversation history automatically limited to 20 messages + system prompt
- Sessions reset when switching models or calling `/reset`
- Trimming happens in `/chat` and `/chat-stream` routes when conversation exceeds 21 messages

### Preset System

The application supports **two preset systems** (toggled via feature flag):

#### **Legacy Preset System** (Default for backward compatibility)
The application includes 61 curated presets stored in `presets.json`:
- **styles**: 14 options (Cinematic, Anime, Photorealistic, etc.)
- **artists**: 18 options (Greg Rutkowski, Ansel Adams, Studio Ghibli, etc.)
- **composition**: 15 options (Portrait, Landscape, Rule of Thirds, etc.)
- **lighting**: 15 options (Golden Hour, Neon, Volumetric, etc.)

Presets are loaded from the JSON file at startup by the `load_presets()` function (line 629).
The `/presets` endpoint reloads the file on each request, enabling hot-reload without server restart.
Each preset is optional - all default to "None" with empty string value.

**Hot-Reload Feature**: Edit `presets.json` and refresh the browser to see changes immediately - no server restart needed!

#### **Hierarchical Preset System** (New in v2.0)

**Enabling the System**:
Set `ENABLE_HIERARCHICAL_PRESETS=true` in `.env` file and restart the application.

**File Structure**:
- **Legacy**: `presets.json` (flat 4-category structure)
- **Hierarchical**: `hierarchical_presets.json` (5-level nested structure)

**Key Features**:
- **50+ Professional Artists** across 6 main categories (Photography, Comic Art, Anime, Fantasy, Horror, Sci-Fi)
- **Progressive Loading**: 3 cascading dropdowns (Category → Type → Artist)
- **Preset Packs**: 5 quick-start professional combinations (one-click setup)
- **Universal Options**: Mood, time, lighting, weather, colors, camera effects (works across all categories)
- **Feature Flag Toggle**: Switch between systems without code changes

**New API Routes** (lines 1671-2087):
```python
GET /api/categories                                          # Level 1: Main categories
GET /api/categories/<id>/types                               # Level 2: Types within category
GET /api/categories/<cat_id>/types/<type_id>/artists         # Level 3: Artists
GET /api/preset-packs                                        # Quick-start combinations
GET /api/universal-options                                   # Cross-cutting options
```

**Backend Implementation**:
```python
# Feature flag (line 76)
ENABLE_HIERARCHICAL_PRESETS = os.getenv('ENABLE_HIERARCHICAL_PRESETS', 'false').lower() in ('true', '1', 'yes')

# Dual file paths (lines 631-635)
LEGACY_PRESETS_FILE = 'presets.json'
HIERARCHICAL_PRESETS_FILE = 'hierarchical_presets.json'
PRESETS_FILE = HIERARCHICAL_PRESETS_FILE if ENABLE_HIERARCHICAL_PRESETS else LEGACY_PRESETS_FILE

# Dynamic loading (line 648+)
def load_presets():
    """Loads appropriate preset file based on feature flag"""
    preset_type = "hierarchical" if ENABLE_HIERARCHICAL_PRESETS else "legacy"
    # Validates structure and logs loaded counts

# Enhanced prompt building (lines 894-1052)
def build_hierarchical_prompt(user_input, selections, presets_data):
    """
    Builds enhanced prompt from hierarchical selections
    Args:
        user_input (str): User's image idea
        selections (dict): {level1, level2, level3, universal}
        presets_data (dict): Full hierarchical presets JSON
    Returns:
        str: Enhanced prompt with artist descriptions and atmospheric settings
    """
```

**Frontend Implementation** (`templates/index.html`):
```javascript
// State management (lines 1665-1669)
let hierarchicalEnabled = false;
let currentCategoryId = '';
let currentTypeId = '';
let currentArtistId = '';

// Progressive loading (lines 1671-1800)
async function loadCategories() { /* Fetch and populate categories */ }
async function loadTypes(categoryId) { /* Fetch types for category */ }
async function loadArtists(categoryId, typeId) { /* Fetch artists */ }

// Preset packs (lines 1954-2022)
async function loadPresetPacks() { /* Display quick-start buttons */ }
async function applyPresetPack(pack) { /* Auto-fill dropdowns */ }

// Universal options (lines 1864-1952)
async function loadUniversalOptions() { /* Populate mood, time, lighting, etc. */ }

// Payload generation (lines 2463-2518)
if (hierarchicalEnabled) {
    basePayload.selections = {
        level1: currentCategoryId,
        level2: currentTypeId,
        level3: currentArtistId,
        universal: { /* mood, time, lighting, weather, colors, camera */ }
    };
}
```

**Migration Scripts**:
- `migrate_presets.py` - Safely install hierarchical system with backup
- `rollback_presets.py` - Revert to legacy system in one command

**Testing**:
- `test_api_routes.py` - Validates all 7 hierarchical API routes
- Run: `python test_api_routes.py` (requires `ENABLE_HIERARCHICAL_PRESETS=true`)

### Database System
The application uses SQLite to persist prompt generation history:
- **Database File**: `prompt_history.db` (auto-created in project root)
- **Schema**: See `init_db()` function (line 382)
- **Table**: `prompt_history` with fields: id, timestamp, user_input, generated_output, model, presets, mode
- **Functions**: `save_to_history()`, `get_history()`, `delete_history_item()`
- Automatically saves all generations (oneshot and chat modes)
- Supports search queries across user input and output

### Model-Specific Prompting
Two distinct system prompts in `SYSTEM_PROMPTS` dictionary (line 703):
- **Flux**: Natural language, conversational style, no quality tags needed
- **SDXL**: Quality-tagged prompts with separate negative prompt generation

Additional chat-specific prompts in `CHAT_SYSTEM_PROMPTS` for conversational mode.

### Streaming Support
The application supports real-time streaming responses via Server-Sent Events (SSE):
- **Endpoints**: `/generate-stream` and `/chat-stream`
- **Implementation**: See `_stream_ollama_response()` function (line 849)
- **Flow**: Tokens stream to frontend as they're generated by Ollama
- **Response Format**: Newline-delimited JSON (NDJSON) with `{"token": "..."}` events
- **Completion**: Final event includes `{"done": true}`
- **Error Handling**: Errors sent as SSE events: `{"error": "...", "type": "..."}`
- Uses generator functions to yield tokens incrementally
- Provides responsive, real-time feedback to users

### Ollama Connection & Auto-Discovery
The application includes intelligent Ollama connection handling:
- **Auto-Discovery**: Scans local /24 network for Ollama servers if localhost fails
- **Interactive Prompts**: In terminal mode, prompts for manual IP entry if connection fails
- **Connection Validation**: Checks `/api/version` endpoint to verify it's actually Ollama
- **Helper Functions**:
  - `get_ollama_base_url()` - Extracts base URL from full endpoint
  - `build_generate_url()` - Constructs proper /api/generate endpoint
  - `check_ollama_connection()` - Validates Ollama is reachable
  - `auto_discover_ollama_server()` - Parallel network scan for Ollama (line 230)
  - `ensure_ollama_connection()` - Interactive connection setup (line 295)
- **Bypass Option**: Set `OLLAMA_STARTUP_CHECK=false` for non-interactive deployments (Docker, systemd)

## Configuration

### Environment Variables (.env)
Configuration is managed via `.env` file (copy from `.env.example`):

```bash
# Ollama Configuration
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen3:latest

# Flask Configuration
FLASK_PORT=5000
FLASK_DEBUG=true  # false for production
FLASK_SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Startup Behavior (optional)
OLLAMA_STARTUP_CHECK=true  # Set to 'false' to skip interactive Ollama connection check (for Docker/systemd)
```

All configuration values have fallback defaults if .env is not present.

### Changing Configuration
Prefer editing `.env` over modifying code. Key locations if manual editing is needed:
- Ollama URL: Line 47
- Ollama model: Line 52
- Flask port: Line 56
- Flask debug: Line 61
- Secret key: Line 66
- Log level: Line 71

## Logging System

The application includes comprehensive logging:
- **Location**: `logs/app.log` (created automatically)
- **Rotation**: 10MB max file size, keeps 5 backups
- **Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Setup**: `setup_logging()` function (line 77)

View logs:
```bash
make logs          # View last 50 lines
make logs-follow   # Follow logs in real-time
```

## Development Guidelines

### Adding New Presets
Edit `presets.json` in the project root directory:
```json
{
  "styles": {
    "Your New Style": "style description, tags, keywords"
  }
}
```

Changes take effect immediately on next request - no server restart needed!
The `/presets` endpoint reloads the JSON file on each request (hot-reload).
Presets are automatically available via `/presets` endpoint and frontend dropdowns.

Note: The file is loaded by `load_presets()` function in `prompt_generator.py` (line 629).

### Adding New Routes
Follow the RESTful pattern:
```python
@app.route('/new-endpoint', methods=['POST'])
def new_function():
    logger.info("Received /new-endpoint request")

    # Validate JSON
    if not request.json:
        return jsonify({'error': 'Invalid request', 'message': 'Request must contain JSON data'}), 400

    data = request.json
    # Handle request

    logger.info("Successfully processed request")
    return jsonify({'result': 'response'})
```

Error handling is automatic via registered error handlers.

### Adding New Model Types
1. Add system prompt to `SYSTEM_PROMPTS` dictionary (line 703)
2. Add chat prompt to `CHAT_SYSTEM_PROMPTS` dictionary (line 741)
3. Update frontend model selector in `templates/index.html`
4. No other code changes needed - the system is model-agnostic

### Adding Streaming Support to New Routes
Follow the SSE pattern used in `/generate-stream` (line 1706):
```python
@app.route('/new-stream', methods=['POST'])
def new_stream():
    def generate():
        try:
            full_response = ""
            for token in call_ollama(messages, model=model, stream=True):
                full_response += token
                # Send token as SSE event
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Send completion event
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'error': str(e), 'type': type(e).__name__})}\n\n"

    return app.response_class(generate(), mimetype='text/event-stream')
```

Key Points:
- Use `call_ollama(..., stream=True)` to get token generator
- Yield SSE-formatted events: `data: {JSON}\n\n`
- Always send a `{"done": true}` completion event
- Handle errors gracefully with error events

### Modifying UI
All frontend code is in `templates/index.html` (single file):
- Structure: HTML with semantic markup
- Styling: Embedded CSS with custom properties
- Logic: Vanilla JavaScript (ES6+)
- No build step or external dependencies

### Testing Best Practices
- Tests use `monkeypatch` to mock Ollama calls (see `tests/test_app.py`)
- Fixtures available: `flask_app`, `client`, `presets` (defined in `conftest.py`)
- All tests must pass before CI succeeds (GitHub Actions)
- Coverage report generated with `make test-cov`

### Working with Database
The SQLite database is auto-managed, but if you need to inspect it:
```bash
# Open database in sqlite3
sqlite3 prompt_history.db

# View schema
.schema prompt_history

# Query recent prompts
SELECT * FROM prompt_history ORDER BY timestamp DESC LIMIT 10;

# Search prompts
SELECT * FROM prompt_history WHERE user_input LIKE '%cyberpunk%';

# Exit
.quit
```

## Troubleshooting

### "Failed to connect to server"
1. Verify Ollama is running: `ollama serve`
2. Check Ollama API: `curl http://localhost:11434`
3. Verify model installation: `ollama list`
4. Check OLLAMA_URL in `.env` or code (line 47)
5. Review logs: `make logs`
6. Try auto-discovery: Application will prompt for network scan on startup if connection fails

### Empty or Poor Quality Prompts
- Try different Ollama models (`OLLAMA_MODEL` in `.env`)
- Provide more detailed input descriptions
- Use presets to guide AI output
- Switch to Chat mode for iterative refinement
- Check logs for errors

### Port Conflicts
- Change `FLASK_PORT` in `.env` file
- Common alternatives: 8080, 3000, 8000
- Verify port availability: `lsof -i :5000` (Linux/Mac)

### Tests Failing
- Ensure virtual environment is activated
- Install dev dependencies: `pip install -r requirements-dev.txt`
- Check pytest output for specific failures
- Verify imports work: `python -c "from prompt_generator import app"`

### Linting Errors
- Configuration in `.flake8` file
- Max line length: 120 characters
- Excludes: venv, logs, build artifacts
- Auto-fix some issues: Consider using `black` or `autopep8`

### Streaming Not Working
- Check browser console for JavaScript errors
- Verify browser supports EventSource API (all modern browsers do)
- Check network tab for SSE connection status
- Ensure Ollama model supports streaming (most do)
- Review logs for errors during streaming

### Non-Interactive Environments (Docker, systemd)
If running in a non-interactive environment and getting startup errors:
```bash
# In .env file, add:
OLLAMA_STARTUP_CHECK=false
```
This skips the interactive Ollama connection prompt and allows the app to start without terminal input.

## File Structure

```
.
├── prompt_generator.py      # Main Flask application (~2,098 lines)
├── presets.json            # Preset configurations (hot-reloadable)
├── templates/
│   └── index.html          # Single-page frontend
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── test_app.py         # Route and functionality tests
│   └── test_presets.py     # Preset validation tests
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies (pytest, flake8)
├── .env.example            # Environment configuration template
├── .flake8                 # Linting configuration
├── Makefile                # Development commands
├── README.md               # User-facing documentation
├── ARCHITECTURE.md         # Detailed technical architecture
└── logs/                   # Application logs (auto-created)
    └── app.log
```

## Privacy and Security

- All processing happens locally via Ollama
- No external API calls or data collection
- Session data stored server-side (signed cookies)
- Secret key from environment variable (generate unique for production)
- No authentication (designed for single-user local use)
- Input validation on all routes
- Comprehensive error handling prevents information leakage

## Advanced Topics

### Model Selection Feature
The `/models` endpoint (line 1353) allows dynamic model selection:
- Queries Ollama's `/api/tags` endpoint
- Returns list of installed models
- Frontend can display model selector dropdown
- Each user can choose their preferred model without editing config

### Network Discovery
The auto-discovery feature (line 230) enables finding Ollama on local networks:
- Scans /24 subnet in parallel (uses ThreadPoolExecutor)
- Timeout of 0.75s per host
- Max 20 concurrent connections
- Cancels remaining tasks when server found
- Falls back to manual IP entry if scan fails
- Useful for multi-machine setups (Ollama on different computer)

### Conversation Trimming Logic
Chat sessions automatically manage memory:
- System prompt always preserved (index 0)
- User/assistant exchanges limited to 20 messages (10 exchanges)
- Trimming happens in both `/chat` (line 1683) and `/chat-stream` (line 1916)
- Prevents token limit issues with Ollama
- Maintains conversation context while controlling resource usage

### Database Best Practices
When working with the history database:
- All timestamps stored in UTC (ISO 8601 format)
- Presets stored as JSON strings for flexibility
- Use parameterized queries to prevent SQL injection
- Connection opened/closed per request (not pooled)
- Safe for concurrent access (SQLite handles locking)
