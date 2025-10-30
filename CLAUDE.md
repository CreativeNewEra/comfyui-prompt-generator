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
# or: pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_app.py
pytest tests/test_presets.py
```

### Linting
```bash
# Run flake8
make lint
# or: flake8 app/ prompt_generator.py tests/

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

The application uses a **modular blueprint-based architecture** for maintainability and scalability:

#### **Backend Structure**
- **Entry Point**: `prompt_generator.py` (61 lines) - Uses app factory pattern
- **App Package**: `app/` directory with modular components:
  - `__init__.py` (350 lines) - Flask app factory with blueprint registration
  - `config.py` (133 lines) - Centralized configuration management
  - `errors.py` (62 lines) - Custom exception classes
  - `database.py` (392 lines) - SQLite database operations
  - `ollama_client.py` (642 lines) - Ollama API client with connection handling
  - `presets.py` (127 lines) - Preset loading and management
  - `personas.py` (104 lines) - Persona system functions
  - `auth.py` (100 lines) - Authentication and authorization utilities
  - `utils.py` (364 lines) - Prompt building and helper functions
  - **Routes (Blueprints)**: `app/routes/` directory (9 files, ~2,153 lines total)
    - `__init__.py` (52 lines) - Blueprint registration
    - `main.py` (23 lines) - Main page route
    - `generate.py` (271 lines) - Quick Generate endpoints (2 routes)
    - `chat.py` (363 lines) - Chat & Refine endpoints (3 routes)
    - `persona.py` (571 lines) - Persona system endpoints (5 routes)
    - `presets.py` (491 lines) - Preset API endpoints (8 routes)
    - `history.py` (118 lines) - History management (2 routes)
    - `models.py` (105 lines) - Model management (1 route)
    - `admin.py` (97 lines) - Admin endpoints (1 route)

#### **Frontend Structure**
- **HTML**: `templates/index.html` (294 lines) - Clean semantic markup
- **CSS**: `static/css/style.css` (1,217 lines) - All styles extracted from HTML
- **JavaScript**: `static/js/` directory (5 modular files, ~1,851 lines total):
  - `api.js` (195 lines) - API client functions for backend communication
  - `ui.js` (255 lines) - UI helper functions and DOM manipulation
  - `presets.js` (631 lines) - Preset system logic and event handlers
  - `personas.js` (200 lines) - Persona system UI logic
  - `main.js` (570 lines) - Main application initialization and coordination

#### **Core Dependencies**
- Flask 3.0.0 - Web framework
- requests 2.31.0 - HTTP client for Ollama
- python-dotenv 1.0.0 - Environment configuration
- sqlite3 (built-in) - Database
- pytest, flake8 (dev dependencies) - Testing and linting

#### **Data Files**
- **Database**: `prompt_history.db` (SQLite, auto-created)
- **Presets**: `presets.json` (80+ curated presets, hot-reloadable)
- **Hierarchical Presets**: `hierarchical_presets.json` (v2.0, feature-flagged)
- **Personas**: `personas.json` + `personas/*.txt` (7 AI personalities)

### Key Routes

All routes are organized into blueprints in `app/routes/`:

#### Main Routes (`app/routes/main.py`)
- `GET /` - Serves the main application

#### Generate Routes (`app/routes/generate.py`)
- `POST /generate` - One-shot prompt generation (Quick Generate mode)
- `POST /generate-stream` - Streaming one-shot generation with SSE

#### Chat Routes (`app/routes/chat.py`)
- `POST /chat` - Conversational prompt refinement
- `POST /chat-stream` - Streaming conversational mode
- `POST /reset` - Clears chat conversation history

#### Persona Routes (`app/routes/persona.py`)
- `GET /api/personas` - List all available personas
- `GET /api/personas/<id>` - Get specific persona details
- `POST /persona-chat` - Persona conversational mode
- `POST /persona-chat-stream` - Streaming persona chat
- `POST /persona-reset` - Reset persona conversation

#### Preset Routes (`app/routes/presets.py`)
- `GET /presets` - Get legacy preset configurations
- `GET /api/categories` - Get hierarchical categories (Level 1)
- `GET /api/categories/<id>/types` - Get types within category (Level 2)
- `GET /api/categories/<cat_id>/types/<type_id>/artists` - Get artists (Level 3)
- `GET /api/preset-packs` - Get quick-start preset combinations
- `GET /api/universal-options` - Get universal preset options
- Additional hierarchical preset endpoints

#### History Routes (`app/routes/history.py`)
- `GET /history` - Retrieve prompt generation history (supports search)
- `DELETE /history/<id>` - Delete a specific history item

#### Model Routes (`app/routes/models.py`)
- `GET /models` - Returns list of installed Ollama models

#### Admin Routes (`app/routes/admin.py`)
- `GET /admin/health` - Health check endpoint

### Error Handling

Custom exception classes are defined in `app/errors.py`:
- `OllamaConnectionError` → 503 Service Unavailable
- `OllamaTimeoutError` → 504 Gateway Timeout
- `OllamaModelNotFoundError` → 404 Not Found
- `OllamaAPIError` → 502 Bad Gateway

Error handlers are registered in `app/__init__.py` via the `register_error_handlers()` function.
All routes return JSON error responses with `error`, `message`, `status`, and `type` fields.

### Session Management

Session management is handled in the route blueprints with Flask sessions:
- Chat mode uses Flask server-side sessions (signed cookies)
- Conversation history automatically limited to 20 messages + system prompt
- Sessions reset when switching models or calling `/reset`
- Trimming logic implemented in `app/routes/chat.py` when conversation exceeds 21 messages
- Separate session tracking for persona conversations (`persona_conversation_id`)

### Preset System

The application supports **two preset systems** (toggled via feature flag in `app/config.py`):

#### **Legacy Preset System** (Default for backward compatibility)
The application includes 80+ curated presets stored in `presets.json`:
- **styles**: 19 options (Cinematic, Anime, Photorealistic, Boudoir, Pin-up, Artistic Nude, etc.)
- **artists**: 24 options (Greg Rutkowski, Ansel Adams, Helmut Newton, Ellen von Unwerth, etc.)
- **composition**: 21 options (Portrait, Landscape, Rule of Thirds, Reclining Pose, Figure Study, etc.)
- **lighting**: 20 options (Golden Hour, Neon, Volumetric, Boudoir Soft, Silk Lighting, etc.)

**Note**: Includes NSFW/adult content presets (boudoir, artistic nude, glamour, pin-up styles)

Presets are loaded by the `load_presets()` function in `app/presets.py`.
The `/presets` endpoint (in `app/routes/presets.py`) reloads the file on each request, enabling hot-reload without server restart.
Each preset is optional - all default to "None" with empty string value.

**Hot-Reload Feature**: Edit `presets.json` and refresh the browser to see changes immediately - no server restart needed!

#### **Hierarchical Preset System** (New in v2.0)

**Enabling the System**:
Set `ENABLE_HIERARCHICAL_PRESETS=true` in `.env` file and restart the application.

**File Structure**:
- **Legacy**: `presets.json` (flat 4-category structure)
- **Hierarchical**: `hierarchical_presets.json` (5-level nested structure)

**Key Features**:
- **70+ Professional Artists** across 7 main categories (Photography, Comic Art, Anime, Fantasy, Horror, Sci-Fi, Adult/NSFW)
- **Progressive Loading**: 3 cascading dropdowns (Category → Type → Artist)
- **Preset Packs**: 9 quick-start professional combinations (one-click setup)
- **Universal Options**: Mood, time, lighting, weather, colors, camera effects (works across all categories)
- **Feature Flag Toggle**: Switch between systems without code changes
- **NSFW Content**: Full Adult/NSFW Photography category with Boudoir, Artistic Nude, Glamour, Pin-up, and Sensual Portrait subcategories

**Note**: The hierarchical system includes mature content. See [NSFW_PRESETS_GUIDE.md](NSFW_PRESETS_GUIDE.md) for details.

**API Routes** (implemented in `app/routes/presets.py`):
```python
GET /api/categories                                          # Level 1: Main categories
GET /api/categories/<id>/types                               # Level 2: Types within category
GET /api/categories/<cat_id>/types/<type_id>/artists         # Level 3: Artists
GET /api/preset-packs                                        # Quick-start combinations
GET /api/universal-options                                   # Cross-cutting options
```

**Backend Implementation**:
```python
# Feature flag in app/config.py
ENABLE_HIERARCHICAL_PRESETS = os.getenv('ENABLE_HIERARCHICAL_PRESETS', 'false').lower() in ('true', '1', 'yes')

# Preset loading in app/presets.py
def load_presets():
    """Loads appropriate preset file based on feature flag"""
    preset_type = "hierarchical" if ENABLE_HIERARCHICAL_PRESETS else "legacy"
    # Validates structure and logs loaded counts

# Enhanced prompt building in app/utils.py
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

**Frontend Implementation** (in `static/js/presets.js`):
```javascript
// State management
let hierarchicalEnabled = false;
let currentCategoryId = '';
let currentTypeId = '';
let currentArtistId = '';

// Progressive loading functions
async function loadCategories() { /* Fetch and populate categories */ }
async function loadTypes(categoryId) { /* Fetch types for category */ }
async function loadArtists(categoryId, typeId) { /* Fetch artists */ }

// Preset packs
async function loadPresetPacks() { /* Display quick-start buttons */ }
async function applyPresetPack(pack) { /* Auto-fill dropdowns */ }

// Universal options
async function loadUniversalOptions() { /* Populate mood, time, lighting, etc. */ }
```

**Migration Scripts**:
- `migrate_presets.py` - Safely install hierarchical system with backup
- `rollback_presets.py` - Revert to legacy system in one command

**Testing**:
- `test_api_routes.py` - Validates all hierarchical API routes
- Run: `python test_api_routes.py` (requires `ENABLE_HIERARCHICAL_PRESETS=true`)

### Persona System

The application includes a **conversational AI persona system** that provides different conversation styles and approaches for prompt generation. Instead of using preset dropdowns, users can have natural conversations with specialized AI personalities.

**Overview:**
The persona system addresses choice paralysis from 80+ presets by providing guided conversational experiences. Each persona has its own personality, approach, and system prompt that shapes how it interacts with users.

**Available Personas:**
- 🎨 **Creative Vision Guide** - Patient step-by-step scene building for beginners
- ⚙️ **Technical Prompt Engineer** - Advanced control with weights and emphasis syntax
- 🎬 **Art Director** - Commercial/professional creative briefs
- 📷 **Photography Expert** - Camera-centric with real lens/lighting terminology
- 🧙 **Fantasy Storyteller** - Narrative-rich world-building
- ⚡ **Quick Sketch Assistant** - Rapid 2-3 question generation
- 💋 **NSFW/Boudoir Specialist** - Tasteful artistic adult content

**File Structure:**
```
personas.json                  # Persona metadata (7 personas)
personas/                      # System prompt files
├── creative_vision_guide.txt  # 5.8KB - Beginner-friendly guided approach
├── technical_engineer.txt     # 6.3KB - Advanced technical control
├── art_director.txt           # 7.2KB - Commercial creative direction
├── photography_expert.txt     # 8.1KB - Camera specifications
├── fantasy_storyteller.txt    # 9.4KB - Narrative world-building
├── quick_sketch.txt           # 9.0KB - Rapid iteration
└── nsfw_specialist.txt        # 9.9KB - Artistic adult content
```

**Backend Functions** (in `app/personas.py`):
```python
def load_personas():
    """Load persona definitions from personas.json"""
    # Returns: {persona_id: {name, description, icon, category, ...}}

def load_persona_prompt(persona_id: str):
    """Load detailed system prompt from personas/ directory"""
    # Returns: Full system prompt string
```

**API Routes** (implemented in `app/routes/persona.py`):
```python
GET  /api/personas              # List all personas with metadata
GET  /api/personas/<id>         # Get specific persona + system prompt
POST /persona-chat              # Non-streaming conversational mode
POST /persona-chat-stream       # Streaming mode with SSE (recommended)
POST /persona-reset             # Reset persona conversation history
```

**Session Management:**
- `session['persona_conversation_id']` - Tracks persona conversation
- `session['active_persona']` - Tracks current persona ID
- Separate from regular chat sessions (`conversation_id`)
- Automatic reset when switching personas (handled in `app/routes/persona.py`)

**Key Features:**
1. **Persona-Specific System Prompts**: Each persona loads its own detailed system prompt that defines personality, approach, and behavior
2. **Preset Compatibility**: Some personas support presets (Technical Engineer, Art Director, Photography Expert, NSFW Specialist)
3. **No-Preset Mode**: Guided personas (Creative Vision Guide, Fantasy Storyteller) work purely conversationally
4. **Streaming Support**: All personas support real-time token-by-token streaming via SSE
5. **History Tracking**: Conversations saved to database with `mode='persona-chat'` and persona metadata
6. **Hot-Reloadable**: Personas can be added/modified without code changes

**Request Payload Example:**
```json
{
  "message": "I want to create an image of a cat",
  "persona_id": "creative_vision_guide",
  "model": "flux",                    // Optional: for presets if supported
  "ollama_model": "qwen3:latest",     // Optional: override default
  "style": "Cinematic",               // Optional: if persona supports presets
  "artist": "Greg Rutkowski",         // Optional
  "composition": "Portrait",          // Optional
  "lighting": "Golden Hour"           // Optional
}
```

**Response (Streaming SSE):**
```
data: {"token": "A"}
data: {"token": " cat"}
data: {"token": "!"}
data: {"done": true}
```

**Adding New Personas:**
1. Create system prompt file: `personas/my_new_persona.txt`
2. Add entry to `personas.json` with metadata
3. Test with `/api/personas/<id>` endpoint
4. Document in `PERSONAS.md`
5. See `PERSONAS_DEVELOPER.md` for detailed guide

**Documentation:**
- `PERSONAS.md` - User-facing documentation (which persona to choose, how to use)
- `PERSONAS_DEVELOPER.md` - Developer guide (how to add new personas, API reference)
- `test_persona_api.py` - Comprehensive test suite

**Testing:**
```bash
# Test persona loading
curl http://localhost:5000/api/personas | python3 -m json.tool

# Test specific persona
curl http://localhost:5000/api/personas/creative_vision_guide | python3 -m json.tool

# Test conversation (requires Ollama)
curl -X POST http://localhost:5000/persona-chat-stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "persona_id": "quick_sketch"}'

# Run test suite
python3 test_persona_api.py
```

**Design Philosophy:**
- **Solves Choice Paralysis**: Conversational approach vs. 80+ dropdown presets
- **Multiple Skill Levels**: Beginner-friendly to advanced technical control
- **Specialized Workflows**: Photography, fantasy, commercial, NSFW
- **Maintains Existing Features**: Works alongside Quick Generate & presets
- **Hot-Swappable**: Switch personas mid-project
- **Extensible**: Easy to add new personas via JSON + text files

### Database System

The application uses SQLite to persist prompt generation history:
- **Database File**: `prompt_history.db` (auto-created in project root)
- **Schema**: See `init_db()` function in `app/database.py`
- **Table**: `prompt_history` with fields: id, timestamp, user_input, generated_output, model, presets, mode
- **Functions**: Defined in `app/database.py`:
  - `save_to_history()` - Save generation to database
  - `get_history()` - Retrieve history with optional search
  - `delete_history_item()` - Delete specific history entry
- Automatically saves all generations (oneshot, chat, and persona modes)
- Supports search queries across user input and output

### Model-Specific Prompting

System prompts are defined in `app/utils.py`:
- **SYSTEM_PROMPTS** dictionary with model-specific instructions:
  - **Flux**: Natural language, conversational style, no quality tags needed
  - **SDXL**: Quality-tagged prompts with separate negative prompt generation
- **CHAT_SYSTEM_PROMPTS** dictionary for conversational mode prompts
- Prompt building functions (`build_prompt()`, `build_hierarchical_prompt()`) in `app/utils.py`

### Streaming Support

The application supports real-time streaming responses via Server-Sent Events (SSE):
- **Endpoints**: Implemented in `app/routes/generate.py`, `app/routes/chat.py`, and `app/routes/persona.py`
- **Implementation**: Streaming handled by `call_ollama()` function in `app/ollama_client.py`
- **Flow**: Tokens stream to frontend as they're generated by Ollama
- **Response Format**: Newline-delimited JSON (NDJSON) with `{"token": "..."}` events
- **Completion**: Final event includes `{"done": true}`
- **Error Handling**: Errors sent as SSE events: `{"error": "...", "type": "..."}`
- Uses generator functions to yield tokens incrementally
- Provides responsive, real-time feedback to users

### Ollama Connection & Auto-Discovery

The application includes intelligent Ollama connection handling (in `app/ollama_client.py`):
- **Auto-Discovery**: Scans local /24 network for Ollama servers if localhost fails
- **Interactive Prompts**: In terminal mode, prompts for manual IP entry if connection fails
- **Connection Validation**: Checks `/api/version` endpoint to verify it's actually Ollama
- **Helper Functions** (in `app/ollama_client.py`):
  - `get_ollama_base_url()` - Extracts base URL from full endpoint
  - `build_generate_url()` - Constructs proper /api/generate endpoint
  - `check_ollama_connection()` - Validates Ollama is reachable
  - `auto_discover_ollama_server()` - Parallel network scan for Ollama
  - `ensure_ollama_connection()` - Interactive connection setup
- **Bypass Option**: Set `OLLAMA_STARTUP_CHECK=false` in `.env` for non-interactive deployments (Docker, systemd)

## Configuration

### Environment Variables (.env)

Configuration is managed via `.env` file (copy from `.env.example`) and loaded in `app/config.py`:

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

# Feature Flags
ENABLE_HIERARCHICAL_PRESETS=false  # Set to 'true' to enable hierarchical preset system

# Startup Behavior (optional)
OLLAMA_STARTUP_CHECK=true  # Set to 'false' to skip interactive Ollama connection check (for Docker/systemd)
```

All configuration values are centralized in `app/config.py` with fallback defaults if .env is not present.

### Changing Configuration

Configuration values are loaded from `.env` and managed in `app/config.py`. The Config class provides:
- Environment variable loading with fallbacks
- Type conversion and validation
- Centralized access to all settings

To modify configuration:
1. Edit `.env` file (recommended)
2. Or modify defaults in `app/config.py`
3. Restart application for changes to take effect

## Logging System

The application includes comprehensive logging configured in `app/config.py`:
- **Location**: `logs/app.log` (created automatically)
- **Rotation**: 10MB max file size, keeps 5 backups
- **Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Setup**: `setup_logging()` function in `app/config.py`
- **Level**: Configurable via `LOG_LEVEL` in `.env`

View logs:
```bash
make logs          # View last 50 lines
make logs-follow   # Follow logs in real-time
```

## Development Guidelines

### Project Structure and Import Patterns

The application uses a modular blueprint-based architecture. When working with the codebase:

**Import Patterns:**
```python
# Import from app modules
from app.config import Config
from app.database import save_to_history, get_history
from app.ollama_client import call_ollama, check_ollama_connection
from app.errors import OllamaConnectionError, OllamaTimeoutError
from app.presets import load_presets
from app.personas import load_personas, load_persona_prompt
from app.utils import build_prompt, build_hierarchical_prompt

# Import Flask extensions
from flask import Blueprint, request, jsonify, session, render_template
```

### Adding New Routes

Create a new blueprint in `app/routes/`:

1. **Create the blueprint file** (e.g., `app/routes/my_feature.py`):
```python
from flask import Blueprint, request, jsonify
from app.config import Config
from app.database import save_to_history
import logging

# Create blueprint
bp = Blueprint('my_feature', __name__)
logger = logging.getLogger(__name__)

@bp.route('/my-endpoint', methods=['POST'])
def my_endpoint():
    """Description of what this endpoint does"""
    logger.info("Received /my-endpoint request")

    # Validate JSON
    if not request.json:
        return jsonify({
            'error': 'Invalid request',
            'message': 'Request must contain JSON data'
        }), 400

    data = request.json
    # Handle request logic

    logger.info("Successfully processed request")
    return jsonify({'result': 'response'})
```

2. **Register the blueprint** in `app/routes/__init__.py`:
```python
from app.routes.my_feature import bp as my_feature_bp

def register_blueprints(app):
    # ... existing blueprints ...
    app.register_blueprint(my_feature_bp)
```

Error handling is automatic via error handlers registered in `app/__init__.py`.

### Adding New Modules

To add a new module to the `app/` directory:

1. **Create the module file** (e.g., `app/my_module.py`):
```python
"""
Description of what this module does.
"""
import logging
from app.config import Config

logger = logging.getLogger(__name__)

def my_function():
    """Function documentation"""
    config = Config()
    # Implementation
    pass
```

2. **Import in relevant files**:
```python
from app.my_module import my_function
```

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
The `/presets` endpoint (in `app/routes/presets.py`) reloads the JSON file on each request (hot-reload).
Presets are automatically available via `/presets` endpoint and frontend dropdowns.

### Adding New Model Types

1. Add system prompt to `SYSTEM_PROMPTS` dictionary in `app/utils.py`
2. Add chat prompt to `CHAT_SYSTEM_PROMPTS` dictionary in `app/utils.py`
3. Update frontend model selector in `templates/index.html`
4. Update model selection logic in `static/js/main.js`
5. No other code changes needed - the system is model-agnostic

### Adding Streaming Support to New Routes

Follow the SSE pattern used in `app/routes/generate.py`:

```python
from flask import Blueprint, request, current_app
from app.ollama_client import call_ollama
import json

bp = Blueprint('my_stream', __name__)

@bp.route('/my-stream', methods=['POST'])
def my_stream():
    """Streaming endpoint with SSE"""
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

    return current_app.response_class(generate(), mimetype='text/event-stream')
```

Key Points:
- Use `call_ollama(..., stream=True)` to get token generator
- Yield SSE-formatted events: `data: {JSON}\n\n`
- Always send a `{"done": true}` completion event
- Handle errors gracefully with error events

### Modifying Frontend

The frontend is now fully modular:

**HTML Structure** (`templates/index.html`):
- Clean semantic markup (294 lines)
- Links to external CSS and JS files
- No embedded styles or scripts

**CSS Styles** (`static/css/style.css`):
- All application styles (1,217 lines)
- CSS custom properties for theming
- Dark mode support

**JavaScript Modules** (`static/js/`):
- `api.js` - API client functions (fetch wrappers, error handling)
- `ui.js` - UI helpers (show/hide elements, notifications, etc.)
- `presets.js` - Preset system logic and event handlers
- `personas.js` - Persona system UI and interactions
- `main.js` - Application initialization and coordination

**Making Changes:**
1. **HTML**: Edit `templates/index.html` for structure changes
2. **Styles**: Edit `static/css/style.css` for visual changes
3. **JavaScript**: Edit appropriate file in `static/js/` for functionality changes
4. No build step required - changes are immediately reflected

### Testing Best Practices

- Tests use `monkeypatch` to mock Ollama calls (see `tests/test_app.py`)
- Fixtures available: `flask_app`, `client`, `presets` (defined in `tests/conftest.py`)
- All tests must pass before CI succeeds (GitHub Actions)
- Coverage report generated with `make test-cov`
- Test imports should use: `from app.module import function`

**Running Tests:**
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_app.py

# Run with coverage
pytest --cov=app --cov-report=html
```

### Working with Database

The SQLite database is auto-managed by functions in `app/database.py`, but if you need to inspect it:

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
4. Check `OLLAMA_URL` in `.env` file
5. Review logs: `make logs`
6. Try auto-discovery: Application will prompt for network scan on startup if connection fails
7. Check connection logic in `app/ollama_client.py`

### Empty or Poor Quality Prompts
- Try different Ollama models (`OLLAMA_MODEL` in `.env`)
- Provide more detailed input descriptions
- Use presets to guide AI output
- Switch to Chat mode for iterative refinement
- Try different personas for alternative approaches
- Check logs for errors

### Port Conflicts
- Change `FLASK_PORT` in `.env` file
- Common alternatives: 8080, 3000, 8000
- Verify port availability: `lsof -i :5000` (Linux/Mac)

### Tests Failing
- Ensure virtual environment is activated
- Install dev dependencies: `pip install -r requirements-dev.txt`
- Check pytest output for specific failures
- Verify imports work: `python -c "from app import create_app; app = create_app()"`
- Check if app structure changed (blueprints, modules)

### Linting Errors
- Configuration in `.flake8` file
- Max line length: 120 characters
- Excludes: venv, logs, build artifacts
- Check all app modules: `flake8 app/ prompt_generator.py tests/`
- Auto-fix some issues: Consider using `black` or `autopep8`

### Streaming Not Working
- Check browser console for JavaScript errors
- Verify browser supports EventSource API (all modern browsers do)
- Check network tab for SSE connection status
- Ensure Ollama model supports streaming (most do)
- Review streaming implementation in `app/routes/` blueprints
- Check `call_ollama()` function in `app/ollama_client.py`
- Review logs for errors during streaming

### Import Errors After Refactoring
If you see `ImportError` or `ModuleNotFoundError`:
- Verify the app package structure is intact
- Check that `app/__init__.py` exists and creates the Flask app
- Ensure blueprints are registered in `app/routes/__init__.py`
- Verify imports use correct paths: `from app.module import function`
- Check that `prompt_generator.py` calls `create_app()` correctly

### Non-Interactive Environments (Docker, systemd)
If running in a non-interactive environment and getting startup errors:
```bash
# In .env file, add:
OLLAMA_STARTUP_CHECK=false
```
This skips the interactive Ollama connection prompt (configured in `app/config.py`).

## File Structure

```
.
├── prompt_generator.py         # Application entry point (61 lines)
├── app/                        # Main application package
│   ├── __init__.py             # Flask app factory (350 lines)
│   ├── config.py               # Configuration management (133 lines)
│   ├── errors.py               # Custom exceptions (62 lines)
│   ├── database.py             # Database operations (392 lines)
│   ├── ollama_client.py        # Ollama API client (642 lines)
│   ├── presets.py              # Preset loading (127 lines)
│   ├── personas.py             # Persona functions (104 lines)
│   ├── auth.py                 # Auth utilities (100 lines)
│   ├── utils.py                # Helper functions (364 lines)
│   └── routes/                 # Blueprint-based routes
│       ├── __init__.py         # Blueprint registration (52 lines)
│       ├── main.py             # Main page (23 lines)
│       ├── generate.py         # Quick Generate (271 lines)
│       ├── chat.py             # Chat & Refine (363 lines)
│       ├── persona.py          # Persona system (571 lines)
│       ├── presets.py          # Preset API (491 lines)
│       ├── history.py          # History management (118 lines)
│       ├── models.py           # Model management (105 lines)
│       └── admin.py            # Admin endpoints (97 lines)
├── templates/
│   └── index.html              # Main frontend template (294 lines)
├── static/
│   ├── css/
│   │   └── style.css           # All application styles (1,217 lines)
│   └── js/
│       ├── api.js              # API client (195 lines)
│       ├── ui.js               # UI helpers (255 lines)
│       ├── presets.js          # Preset logic (631 lines)
│       ├── personas.js         # Persona UI (200 lines)
│       └── main.js             # Main app logic (570 lines)
├── presets.json                # Legacy preset configurations
├── hierarchical_presets.json   # Hierarchical preset system (v2.0)
├── personas.json               # Persona metadata (7 personas)
├── personas/                   # Persona system prompts
│   ├── creative_vision_guide.txt   # 5.8KB - Beginner-friendly
│   ├── technical_engineer.txt      # 6.3KB - Advanced technical
│   ├── art_director.txt            # 7.2KB - Commercial focus
│   ├── photography_expert.txt      # 8.1KB - Camera specs
│   ├── fantasy_storyteller.txt     # 9.4KB - Narrative building
│   ├── quick_sketch.txt            # 9.0KB - Rapid iteration
│   └── nsfw_specialist.txt         # 9.9KB - Artistic adult content
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_app.py             # Route and functionality tests
│   └── test_presets.py         # Preset validation tests
├── test_persona_api.py         # Persona API test suite
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── .env.example                # Environment configuration template
├── .flake8                     # Linting configuration
├── Makefile                    # Development commands
├── README.md                   # User-facing documentation
├── ARCHITECTURE.md             # Detailed technical architecture
├── CLAUDE.md                   # This file - Claude Code guidance
├── PERSONAS.md                 # Persona user guide
├── PERSONAS_DEVELOPER.md       # Persona developer guide
└── logs/                       # Application logs (auto-created)
    └── app.log
```

## Privacy and Security

- All processing happens locally via Ollama
- No external API calls or data collection
- Session data stored server-side (signed cookies)
- Secret key from environment variable (generate unique for production)
- No authentication (designed for single-user local use)
- Input validation on all routes (handled in blueprints)
- Comprehensive error handling prevents information leakage (via `app/errors.py`)

## Advanced Topics

### Model Selection Feature

The `/models` endpoint (in `app/routes/models.py`) allows dynamic model selection:
- Queries Ollama's `/api/tags` endpoint
- Returns list of installed models
- Frontend can display model selector dropdown
- Each user can choose their preferred model without editing config
- Uses `get_ollama_models()` function from `app/ollama_client.py`

### Network Discovery

The auto-discovery feature (in `app/ollama_client.py`) enables finding Ollama on local networks:
- `auto_discover_ollama_server()` function scans /24 subnet in parallel
- Uses ThreadPoolExecutor for concurrent connections
- Timeout of 0.75s per host
- Max 20 concurrent connections
- Cancels remaining tasks when server found
- Falls back to manual IP entry if scan fails
- Useful for multi-machine setups (Ollama on different computer)

### Conversation Trimming Logic

Chat sessions automatically manage memory (implemented in `app/routes/chat.py`):
- System prompt always preserved (index 0)
- User/assistant exchanges limited to 20 messages (10 exchanges)
- Trimming happens in both `/chat` and `/chat-stream` routes
- Prevents token limit issues with Ollama
- Maintains conversation context while controlling resource usage
- Logic can be found in the chat route handlers

### Database Best Practices

When working with the history database (see `app/database.py`):
- All timestamps stored in UTC (ISO 8601 format)
- Presets stored as JSON strings for flexibility
- Use parameterized queries to prevent SQL injection (already implemented)
- Connection opened/closed per request (not pooled)
- Safe for concurrent access (SQLite handles locking)
- Database operations isolated in dedicated module

### Blueprint Architecture

The application uses Flask blueprints for modular route organization:
- **Separation of Concerns**: Each feature has its own blueprint
- **Independent Testing**: Blueprints can be tested in isolation
- **Easy Maintenance**: Related routes grouped together
- **Scalability**: New features added as new blueprints
- **Registration**: All blueprints registered in `app/routes/__init__.py`
- **Import Pattern**: Blueprints import from `app.*` modules

Benefits of this architecture:
- Clear code organization and navigation
- Easier debugging and testing
- Better collaboration (developers work on separate blueprints)
- Simplified feature addition and removal
