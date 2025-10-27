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
The application includes 80+ curated presets stored in `presets.json`:
- **styles**: 19 options (Cinematic, Anime, Photorealistic, Boudoir, Pin-up, Artistic Nude, etc.)
- **artists**: 24 options (Greg Rutkowski, Ansel Adams, Helmut Newton, Ellen von Unwerth, etc.)
- **composition**: 21 options (Portrait, Landscape, Rule of Thirds, Reclining Pose, Figure Study, etc.)
- **lighting**: 20 options (Golden Hour, Neon, Volumetric, Boudoir Soft, Silk Lighting, etc.)

**Note**: Includes NSFW/adult content presets (boudoir, artistic nude, glamour, pin-up styles)

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
- **70+ Professional Artists** across 7 main categories (Photography, Comic Art, Anime, Fantasy, Horror, Sci-Fi, Adult/NSFW)
- **Progressive Loading**: 3 cascading dropdowns (Category → Type → Artist)
- **Preset Packs**: 9 quick-start professional combinations (one-click setup)
- **Universal Options**: Mood, time, lighting, weather, colors, camera effects (works across all categories)
- **Feature Flag Toggle**: Switch between systems without code changes
- **NSFW Content**: Full Adult/NSFW Photography category with Boudoir, Artistic Nude, Glamour, Pin-up, and Sensual Portrait subcategories

**Note**: The hierarchical system includes mature content. See [NSFW_PRESETS_GUIDE.md](NSFW_PRESETS_GUIDE.md) for details.

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

**Backend Functions** (`prompt_generator.py`):
```python
# Lines ~984-1072
def load_personas():
    """Load persona definitions from personas.json"""
    # Returns: {persona_id: {name, description, icon, category, ...}}

def load_persona_prompt(persona_id: str):
    """Load detailed system prompt from personas/ directory"""
    # Returns: Full system prompt string
```

**API Routes** (lines 2004-2534):
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
- Automatic reset when switching personas

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
data: {"token": " A"}
data: {"token": " perfect"}
data: {"token": " subject"}
data: {"token": "."}
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

**Implementation Status:**
- ✅ Phase 1: Core infrastructure (personas.json, system prompts)
- ✅ Phase 2: Backend integration (API routes, session management, Ollama integration)
- ⏳ Phase 3: Frontend UI (persona selector, active indicator, chat integration)

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
├── prompt_generator.py      # Main Flask application (~2,500+ lines)
├── presets.json            # Preset configurations (hot-reloadable)
├── personas.json           # Persona metadata (7 personas)
├── personas/               # Persona system prompts
│   ├── creative_vision_guide.txt   # 5.8KB - Beginner-friendly
│   ├── technical_engineer.txt      # 6.3KB - Advanced technical
│   ├── art_director.txt            # 7.2KB - Commercial focus
│   ├── photography_expert.txt      # 8.1KB - Camera specs
│   ├── fantasy_storyteller.txt     # 9.4KB - Narrative building
│   ├── quick_sketch.txt            # 9.0KB - Rapid iteration
│   └── nsfw_specialist.txt         # 9.9KB - Artistic adult content
├── templates/
│   └── index.html          # Single-page frontend
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── test_app.py         # Route and functionality tests
│   └── test_presets.py     # Preset validation tests
├── test_persona_api.py     # Persona API test suite
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies (pytest, flake8)
├── .env.example            # Environment configuration template
├── .flake8                 # Linting configuration
├── Makefile                # Development commands
├── README.md               # User-facing documentation
├── ARCHITECTURE.md         # Detailed technical architecture
├── PERSONAS.md             # Persona user guide
├── PERSONAS_DEVELOPER.md   # Persona developer guide
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
