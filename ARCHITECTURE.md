# Architecture Documentation

## Table of Contents
- [High-Level Architecture](#high-level-architecture)
- [Component Overview](#component-overview)
- [Request/Response Flow](#requestresponse-flow)
- [Data Models](#data-models)
- [Key Design Decisions](#key-design-decisions)
- [Extension Points](#extension-points)
- [Security Considerations](#security-considerations)
- [Performance Characteristics](#performance-characteristics)

---

## High-Level Architecture

The ComfyUI Prompt Generator follows a **three-tier architecture** with local AI processing:

```mermaid
graph TB
    subgraph "Client Layer"
        A[Web Browser]
        B[HTML/CSS/JS Frontend]
    end

    subgraph "Application Layer"
        C[Flask Web Server]
        D[Route Handlers]
        E[Session Manager]
        F[Preset Engine]
    end

    subgraph "AI Layer"
        G[Ollama Server]
        H[Language Model]
    end

    A --> B
    B -->|HTTP/JSON| C
    C --> D
    D --> E
    D --> F
    D -->|REST API| G
    G --> H
    H -->|Generated Text| G
    G -->|JSON Response| D
    D -->|JSON| B
    B --> A
```

### Architecture Principles

1. **Separation of Concerns**: Frontend, backend, and AI processing are decoupled
2. **Local-First**: All processing happens on the user's machine
3. **Stateless API**: Routes are stateless except for chat sessions
4. **Modular Design**: Components can be modified independently
5. **Privacy-Focused**: No external API calls or data collection

---

## Component Overview

### 1. Frontend (Single-Page Application)

**Location**: `templates/index.html`

**Technology Stack**:
- Vanilla JavaScript (ES6+)
- HTML5 with semantic markup
- CSS3 with custom properties (gradients, animations)

**Responsibilities**:
- Render user interface
- Handle user interactions
- Manage UI state (mode switching, preset selection)
- Communicate with backend via fetch API
- Display generated prompts with copy functionality
- Maintain chat history display

**Key Components**:

```
Frontend Architecture:
┌─────────────────────────────────────────────┐
│           User Interface Layer              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Input   │  │ Presets  │  │  Output  │  │
│  │  Form    │  │ Dropdowns│  │  Display │  │
│  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────┤
│         JavaScript Event Handlers           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Generate │  │   Chat   │  │  Reset   │  │
│  │  Click   │  │  Submit  │  │  Click   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────┤
│            API Communication                │
│         fetch() → Backend Routes            │
└─────────────────────────────────────────────┘
```

**State Management**:
- Local UI state (no Redux/Vuex needed)
- Chat history stored in DOM
- Current mode tracked via radio buttons
- Preset selections read from dropdown values

---

### 2. Backend (Flask Application)

**Location**: `prompt_generator.py`

**Technology Stack**:
- Flask 3.0.0 (lightweight WSGI framework)
- Python 3.10+
- Server-side sessions with signed cookies
- python-dotenv for configuration

**Core Routes**:

| Route | Method | Purpose | Authentication |
|-------|--------|---------|----------------|
| `/` | GET | Serve main HTML page | None |
| `/presets` | GET | Return preset configurations | None |
| `/generate` | POST | One-shot prompt generation | None |
| `/chat` | POST | Conversational refinement | Session-based |
| `/reset` | POST | Clear chat history | Session-based |

**Architecture Pattern**: RESTful API with Flask blueprints pattern (future enhancement)

```
Backend Architecture:
┌─────────────────────────────────────────────┐
│              Flask Application              │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │         Route Handlers              │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐        │   │
│  │  │  /   │ │/gene │ │/chat │        │   │
│  │  │      │ │-rate │ │      │        │   │
│  │  └──────┘ └──────┘ └──────┘        │   │
│  └─────────────────────────────────────┘   │
│                    ↓                        │
│  ┌─────────────────────────────────────┐   │
│  │      Business Logic Layer           │   │
│  │  ┌──────────┐  ┌──────────────┐    │   │
│  │  │ Preset   │  │  Message     │    │   │
│  │  │ Builder  │  │  Formatter   │    │   │
│  │  └──────────┘  └──────────────┘    │   │
│  └─────────────────────────────────────┘   │
│                    ↓                        │
│  ┌─────────────────────────────────────┐   │
│  │     Integration Layer               │   │
│  │  ┌──────────────────────────────┐   │   │
│  │  │   call_ollama() Function     │   │   │
│  │  │   - HTTP client              │   │   │
│  │  │   - Error handling           │   │   │
│  │  │   - Retry logic (future)     │   │   │
│  │  └──────────────────────────────┘   │   │
│  └─────────────────────────────────────┘   │
│                    ↓                        │
│            Ollama REST API                  │
└─────────────────────────────────────────────┘
```

**Key Modules**:

1. **Request Validation**
   - JSON payload validation
   - Input sanitization
   - Required field checking

2. **Session Management**
   - Server-side session storage
   - Conversation history tracking
   - Automatic history trimming (max 20 messages)

3. **Error Handling**
   - Custom exception classes
   - Global error handlers
   - Graceful degradation
   - Logging integration

4. **Configuration Management**
   - Environment variable support (.env)
   - Sensible defaults
   - Runtime configuration validation

---

### 3. AI Integration (Ollama)

**Communication Protocol**: HTTP REST API

**Endpoint**: `POST http://localhost:11434/api/generate`

**Request Format**:
```json
{
  "model": "qwen3:latest",
  "prompt": "System: [system prompt]\n\nUser: [user input]\nAssistant:",
  "stream": false
}
```

**Response Format**:
```json
{
  "model": "qwen3:latest",
  "created_at": "2023-08-04T19:22:45.499127Z",
  "response": "[Generated text here]",
  "done": true
}
```

**Integration Architecture**:

```
┌─────────────────────────────────────────────┐
│         Flask Application                   │
│                                             │
│  call_ollama(messages, model)               │
│         ↓                                   │
│  1. Format messages into prompt             │
│  2. Build request payload                   │
│  3. POST to Ollama API                      │
│  4. Handle timeout (120s)                   │
│  5. Parse JSON response                     │
│  6. Extract generated text                  │
│  7. Return to route handler                 │
└─────────────────────────────────────────────┘
                   ↓ HTTP
┌─────────────────────────────────────────────┐
│         Ollama Server (Local)               │
│                                             │
│  1. Receive prompt                          │
│  2. Load model into memory (if needed)      │
│  3. Tokenize input                          │
│  4. Run inference (GPU/CPU)                 │
│  5. Generate tokens sequentially            │
│  6. Decode to text                          │
│  7. Return JSON response                    │
└─────────────────────────────────────────────┘
```

**Error Handling**:
- `OllamaConnectionError`: Cannot reach Ollama server
- `OllamaTimeoutError`: Request exceeds 120-second timeout
- `OllamaModelNotFoundError`: Requested model not installed
- `OllamaAPIError`: Generic API errors

**Retry Strategy** (future enhancement):
- Exponential backoff for transient failures
- Circuit breaker pattern for sustained failures
- Fallback to alternative models

---

### 4. Preset System

**Purpose**: Provide curated style/composition/lighting guidance to the AI

**Architecture**:

```python
PRESETS = {
    "category": {
        "None": "",  # Always present
        "Preset Name": "preset, tags, keywords",
        # ... more presets
    }
}
```

**Categories**:
1. **styles**: Visual style (Cinematic, Anime, etc.)
2. **artists**: Artist/photographer styles
3. **composition**: Camera angles and framing
4. **lighting**: Lighting setup and mood

**Processing Flow**:

```
User Selection:
  Style: "Cyberpunk"
  Lighting: "Neon Lighting"
  Composition: "Low Angle"
  Artist: "None"
         ↓
Preset Builder:
  Filters out "None" selections
  Builds context strings
         ↓
Message Formatter:
  Combines with user input
  Creates structured prompt
         ↓
Final Prompt:
  "User's image idea: [input]

   Selected presets:
   Style: cyberpunk, neon lights, futuristic
   Lighting: neon lighting, vibrant colors, glowing
   Composition: low angle shot, looking up

   Please create a detailed prompt..."
```

**Design Pattern**: Strategy Pattern
- Presets act as strategies that modify AI behavior
- Each preset is independent and composable
- Easy to add/remove/modify presets

**Extensibility**:
- Add new categories by extending the PRESETS dict
- No code changes needed for new presets
- Frontend automatically renders new categories (future enhancement)

---

### 5. Session Management

**Purpose**: Maintain conversation history in Chat & Refine mode

**Technology**: Flask server-side sessions with signed cookies

**Session Data Structure**:
```python
session = {
    'conversation': [
        {'role': 'system', 'content': '[system prompt]'},
        {'role': 'user', 'content': '[user message 1]'},
        {'role': 'assistant', 'content': '[AI response 1]'},
        {'role': 'user', 'content': '[user message 2]'},
        # ... up to 20 messages + system prompt
    ],
    'model_type': 'flux'  # or 'sdxl'
}
```

**Session Lifecycle**:

```
1. User sends first chat message
   ↓
2. Backend checks session['conversation']
   - Not present → Initialize new session
   - Present → Continue existing session
   ↓
3. Add system prompt (if new)
   ↓
4. Append user message
   ↓
5. Call Ollama with full conversation
   ↓
6. Append assistant response
   ↓
7. Trim history if > 21 messages
   ↓
8. Save session (automatic)
   ↓
9. Return response to frontend
```

**Session Management Rules**:
- **New conversation**: First message or after reset
- **Model change**: Automatically resets conversation
- **History limit**: 20 messages + 1 system prompt (21 total)
- **Trimming**: Keeps system prompt + last 20 messages
- **Timeout**: Sessions expire after browser close (default Flask behavior)

**Session Storage**:
- **Development**: In-memory (lost on server restart)
- **Production**: Can be configured for Redis, database, or filesystem

---

## Request/Response Flow

### Quick Generate Mode

```
┌─────────┐                ┌───────┐                 ┌────────┐
│ Browser │                │ Flask │                 │ Ollama │
└────┬────┘                └───┬───┘                 └───┬────┘
     │                         │                         │
     │ 1. User enters prompt   │                         │
     │    & selects presets    │                         │
     │                         │                         │
     │ 2. POST /generate       │                         │
     │    {input, model,       │                         │
     │     presets}            │                         │
     ├────────────────────────>│                         │
     │                         │                         │
     │                         │ 3. Validate request     │
     │                         │                         │
     │                         │ 4. Build preset context │
     │                         │                         │
     │                         │ 5. Format prompt        │
     │                         │                         │
     │                         │ 6. POST /api/generate   │
     │                         ├────────────────────────>│
     │                         │                         │
     │                         │                         │ 7. Load model
     │                         │                         │
     │                         │                         │ 8. Generate
     │                         │                         │
     │                         │ 9. Return response      │
     │                         │<────────────────────────┤
     │                         │                         │
     │                         │ 10. Extract text        │
     │                         │                         │
     │ 11. JSON response       │                         │
     │     {result, model}     │                         │
     │<────────────────────────┤                         │
     │                         │                         │
     │ 12. Display prompt      │                         │
     │     + copy button       │                         │
     │                         │                         │
```

**Timing**:
- Steps 1-6: < 100ms
- Steps 7-8: 5-30 seconds (model-dependent)
- Steps 9-12: < 100ms
- **Total**: ~5-30 seconds

---

### Chat & Refine Mode

```
┌─────────┐                ┌───────┐                 ┌────────┐
│ Browser │                │ Flask │                 │ Ollama │
└────┬────┘                └───┬───┘                 └───┬────┘
     │                         │                         │
     │ 1. User sends message   │                         │
     │                         │                         │
     │ 2. POST /chat           │                         │
     │    {message, model,     │                         │
     │     presets}            │                         │
     ├────────────────────────>│                         │
     │                         │                         │
     │                         │ 3. Load session         │
     │                         │                         │
     │                         │ 4. Initialize if new    │
     │                         │    conversation         │
     │                         │                         │
     │                         │ 5. Append user message  │
     │                         │    to history           │
     │                         │                         │
     │                         │ 6. POST full history    │
     │                         ├────────────────────────>│
     │                         │                         │
     │                         │                         │ 7. Generate with
     │                         │                         │    context
     │                         │                         │
     │                         │ 8. Response             │
     │                         │<────────────────────────┤
     │                         │                         │
     │                         │ 9. Append to history    │
     │                         │                         │
     │                         │ 10. Trim if needed      │
     │                         │                         │
     │                         │ 11. Save session        │
     │                         │                         │
     │ 12. JSON response       │                         │
     │<────────────────────────┤                         │
     │                         │                         │
     │ 13. Append to chat UI   │                         │
     │                         │                         │
```

**Session Persistence**:
- Conversation persists across requests
- Resets on model change or explicit reset
- Trimmed to prevent memory bloat

---

### Error Flow

```
┌─────────┐                ┌───────┐                 ┌────────┐
│ Browser │                │ Flask │                 │ Ollama │
└────┬────┘                └───┬───┘                 └───┬────┘
     │                         │                         │
     │ POST /generate          │                         │
     ├────────────────────────>│                         │
     │                         │                         │
     │                         │ POST /api/generate      │
     │                         ├────────────────────────>│
     │                         │                         │
     │                         │          X Connection   │
     │                         │          Failed         │
     │                         │                         │
     │                         │ Catch ConnectionError   │
     │                         │                         │
     │                         │ Log error               │
     │                         │                         │
     │                         │ Raise                   │
     │                         │ OllamaConnectionError   │
     │                         │                         │
     │                         │ Error handler catches   │
     │                         │                         │
     │ 503 Service Unavailable │                         │
     │ {error, message, type}  │                         │
     │<────────────────────────┤                         │
     │                         │                         │
     │ Display error to user   │                         │
     │                         │                         │
```

**Error Responses**:
- `400`: Bad request (missing/invalid data)
- `404`: Route not found or model not found
- `500`: Internal server error
- `502`: Ollama API error
- `503`: Cannot connect to Ollama
- `504`: Ollama timeout

---

## Data Models

### Request Models

**Generate Request**:
```python
{
    "input": str,          # Required: User's prompt description
    "model": str,          # Required: "flux" or "sdxl"
    "style": str,          # Optional: Preset name or "None"
    "artist": str,         # Optional: Preset name or "None"
    "composition": str,    # Optional: Preset name or "None"
    "lighting": str        # Optional: Preset name or "None"
}
```

**Chat Request**:
```python
{
    "message": str,        # Required: User's message
    "model": str,          # Required: "flux" or "sdxl"
    "style": str,          # Optional: Preset name or "None"
    "artist": str,         # Optional: Preset name or "None"
    "composition": str,    # Optional: Preset name or "None"
    "lighting": str        # Optional: Preset name or "None"
}
```

### Response Models

**Success Response**:
```python
{
    "result": str,         # Generated prompt text
    "model": str           # Model used
}
```

**Error Response**:
```python
{
    "error": str,          # Error type
    "message": str,        # Human-readable message
    "status": int,         # HTTP status code
    "type": str            # Error category (optional)
}
```

### Internal Models

**Conversation Message**:
```python
{
    "role": str,           # "system", "user", or "assistant"
    "content": str         # Message content
}
```

**Ollama Request**:
```python
{
    "model": str,          # Model name (e.g., "qwen3:latest")
    "prompt": str,         # Formatted prompt
    "stream": bool         # Always false for now
}
```

---

## Key Design Decisions

### 1. **Single-Page Frontend**

**Decision**: Use vanilla JavaScript instead of React/Vue

**Rationale**:
- ✅ Simpler deployment (single HTML file)
- ✅ No build step required
- ✅ Faster initial load
- ✅ Easier for beginners to understand
- ✅ Minimal dependencies

**Trade-offs**:
- ❌ Less structured state management
- ❌ Manual DOM manipulation
- ❌ No component reusability

**Future**: Could migrate to a framework if complexity increases

---

### 2. **Server-Side Sessions**

**Decision**: Use Flask sessions instead of JWT or client-side storage

**Rationale**:
- ✅ Built into Flask (no extra dependencies)
- ✅ Automatically handles cookies
- ✅ Conversation history not exposed to client
- ✅ No token management complexity
- ✅ Secure by default (signed cookies)

**Trade-offs**:
- ❌ Not suitable for distributed deployments (without Redis)
- ❌ Sessions lost on server restart (development mode)

**Future**: Can add Redis session store for production

---

### 3. **Synchronous Ollama Calls**

**Decision**: Block during AI generation instead of async/polling

**Rationale**:
- ✅ Simpler implementation
- ✅ No WebSocket complexity
- ✅ No polling overhead
- ✅ Easier error handling
- ✅ User expects to wait for AI generation

**Trade-offs**:
- ❌ Ties up Flask worker during generation
- ❌ Cannot show progress indicators
- ❌ Long timeout (120s) required

**Future**: Could add streaming with Server-Sent Events (SSE)

---

### 4. **Preset System**

**Decision**: Hardcoded presets instead of database

**Rationale**:
- ✅ Fast access (no DB queries)
- ✅ Version controlled with code
- ✅ Easy to review and modify
- ✅ No database dependency
- ✅ Simple deployment

**Trade-offs**:
- ❌ Cannot add presets via UI
- ❌ Requires code changes to modify
- ❌ All users have same presets

**Future**: Could add user-defined preset persistence

---

### 5. **Model-Specific System Prompts**

**Decision**: Different prompts for Flux vs SDXL

**Rationale**:
- ✅ Optimized for each model's strengths
- ✅ Flux: Natural language, no quality tags
- ✅ SDXL: Structured with negative prompts
- ✅ Better output quality
- ✅ Educational for users

**Trade-offs**:
- ❌ Must maintain multiple prompts
- ❌ Harder to add new models

**Future**: Could create a prompt template system

---

### 6. **RESTful API Design**

**Decision**: JSON API instead of form submissions

**Rationale**:
- ✅ Clean separation of concerns
- ✅ Easy to test with curl/Postman
- ✅ Future mobile app support
- ✅ JavaScript-friendly
- ✅ Modern standard

**Trade-offs**:
- ❌ Requires JavaScript (no progressive enhancement)
- ❌ Not search engine friendly

**Future**: Could add a traditional form fallback

---

### 7. **No Authentication**

**Decision**: Application runs locally without auth

**Rationale**:
- ✅ Single-user application
- ✅ Runs on localhost
- ✅ Simpler setup
- ✅ No password management
- ✅ Privacy by design (local-only)

**Trade-offs**:
- ❌ Cannot deploy publicly without modification
- ❌ No user-specific data

**Future**: Would need auth for multi-user deployments

---

### 8. **Environment-Based Configuration**

**Decision**: Use .env files instead of config.py

**Rationale**:
- ✅ 12-factor app methodology
- ✅ Easy to change without code edits
- ✅ Different configs for dev/prod
- ✅ Secrets not in version control
- ✅ Standard practice

**Trade-offs**:
- ❌ Must create .env file
- ❌ Easy to forget to update .env.example

**Future**: Could add runtime config validation

---

## Extension Points

### 1. **Custom Model Support**

**Current**: Hardcoded model types (flux, sdxl)

**Extension**:
```python
# Add to SYSTEM_PROMPTS
SYSTEM_PROMPTS = {
    "flux": "...",
    "sdxl": "...",
    "your_model": "Your custom system prompt here"
}

# Frontend: Add to model selector
<option value="your_model">Your Model Name</option>
```

**Future Enhancement**: Auto-detect installed models via Ollama API

---

### 2. **Streaming Responses**

**Current**: Wait for complete response

**Extension Pattern**:
```python
@app.route('/generate-stream', methods=['POST'])
def generate_stream():
    def generate():
        # Yield chunks as they arrive
        for chunk in ollama_stream():
            yield f"data: {json.dumps(chunk)}\n\n"

    return Response(generate(), mimetype='text/event-stream')
```

**Frontend**:
```javascript
const eventSource = new EventSource('/generate-stream');
eventSource.onmessage = (event) => {
    // Append chunk to display
};
```

---

### 3. **Preset Management UI**

**Extension Point**: `prompt_generator.py:PRESETS`

**Future Implementation**:
```python
# New routes
@app.route('/presets', methods=['POST'])
def add_preset():
    # Save custom preset to database
    pass

@app.route('/presets/<id>', methods=['DELETE'])
def delete_preset():
    # Remove custom preset
    pass

# Database schema
CREATE TABLE user_presets (
    id INTEGER PRIMARY KEY,
    category TEXT,
    name TEXT,
    value TEXT,
    user_id INTEGER
);
```

---

### 4. **Prompt History**

**Extension Point**: Session storage

**Implementation**:
```python
# Add to session
session['history'] = [
    {
        'timestamp': datetime.now(),
        'prompt': 'user input',
        'result': 'generated prompt',
        'model': 'flux',
        'presets': {...}
    }
]

# New route
@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(session.get('history', []))
```

**Frontend**: Add history panel with search/filter

---

### 5. **Image Upload for Analysis**

**Extension Point**: New route + multipart form handling

**Implementation**:
```python
from werkzeug.utils import secure_filename
import base64

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    file = request.files['image']
    # Convert to base64
    image_data = base64.b64encode(file.read())
    # Send to multimodal LLM
    prompt = f"Describe this image in detail: {image_data}"
    # Return description
```

**Requirements**:
- Multimodal Ollama model (llava, bakllava)
- Image preprocessing
- Frontend file upload

---

### 6. **Batch Generation**

**Extension Point**: New route for bulk operations

**Implementation**:
```python
@app.route('/generate-batch', methods=['POST'])
def generate_batch():
    inputs = request.json['inputs']  # List of prompts
    results = []

    for input_text in inputs:
        result = generate_single(input_text)
        results.append(result)

    return jsonify({'results': results})
```

**Considerations**:
- Long request times (use async tasks)
- Progress tracking
- Error handling for partial failures

---

### 7. **Plugin System**

**Architecture**:
```python
# plugins/base.py
class PresetPlugin:
    def get_category_name(self):
        raise NotImplementedError

    def get_presets(self):
        raise NotImplementedError

# plugins/custom_styles.py
class CustomStylesPlugin(PresetPlugin):
    def get_category_name(self):
        return "custom_styles"

    def get_presets(self):
        return {
            "Style 1": "tags here",
            "Style 2": "more tags"
        }

# Load plugins
def load_plugins():
    for plugin_file in os.listdir('plugins'):
        if plugin_file.endswith('.py'):
            # Import and register plugin
            pass
```

---

### 8. **API Rate Limiting**

**Extension Point**: Flask middleware

**Implementation**:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/generate')
@limiter.limit("10 per minute")
def generate():
    # Rate limited to 10 requests per minute
    pass
```

---

### 9. **Caching Layer**

**Extension Point**: Decorator for routes

**Implementation**:
```python
from functools import lru_cache
import hashlib

def cache_prompt(func):
    cache = {}

    def wrapper(*args, **kwargs):
        # Create cache key from input
        key = hashlib.md5(
            json.dumps(request.json).encode()
        ).hexdigest()

        if key in cache:
            return cache[key]

        result = func(*args, **kwargs)
        cache[key] = result
        return result

    return wrapper

@app.route('/generate')
@cache_prompt
def generate():
    pass
```

---

### 10. **WebSocket Support**

**Extension Point**: Add Flask-SocketIO

**Implementation**:
```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app)

@socketio.on('generate')
def handle_generate(data):
    # Stream tokens as they're generated
    for token in ollama_stream(data['prompt']):
        emit('token', {'token': token})

    emit('complete', {'status': 'done'})

# Client
socket.on('token', (data) => {
    appendToken(data.token);
});
```

---

## Security Considerations

### 1. **Input Validation**

**Current Measures**:
- JSON schema validation
- Empty input rejection
- Type checking

**Recommendations**:
- Add input length limits
- Sanitize HTML in responses
- Validate preset selections against known values

---

### 2. **Session Security**

**Current Measures**:
- Signed cookies (prevents tampering)
- Server-side storage (history not exposed)
- Secret key from environment

**Recommendations**:
- Rotate secret key regularly
- Add session timeout
- Implement CSRF protection for state-changing operations

---

### 3. **Ollama Communication**

**Current Measures**:
- Localhost-only by default
- No user input in model name
- Timeout protection

**Recommendations**:
- Validate Ollama responses
- Add TLS if remote Ollama
- Implement request signing for remote deployments

---

### 4. **Dependency Security**

**Current Measures**:
- Pinned dependency versions
- Minimal dependency tree

**Recommendations**:
- Regular dependency updates
- Automated vulnerability scanning
- Use dependabot for GitHub repos

---

## Performance Characteristics

### Bottlenecks

1. **Ollama Inference** (5-30s)
   - Dominant factor in response time
   - Depends on model size and hardware
   - GPU vs CPU makes 10-100x difference

2. **First Request** (slower)
   - Model must be loaded into memory
   - Subsequent requests faster (warm cache)

3. **Network Latency** (negligible for localhost)
   - Local: <1ms
   - Remote Ollama: depends on network

### Optimization Strategies

1. **Model Selection**
   - Smaller models = faster responses
   - Trade-off: speed vs quality

2. **Hardware Acceleration**
   - GPU dramatically improves performance
   - Ollama auto-detects NVIDIA GPUs

3. **Session Trimming**
   - Prevents unbounded memory growth
   - Limits context window size

4. **Static Asset Caching**
   - Browser caches HTML/CSS/JS
   - Reduces repeat load times

### Scalability

**Current Architecture**:
- Single-threaded Flask dev server
- One request at a time
- Not suitable for >10 concurrent users

**Production Deployment**:
- Use Gunicorn/uWSGI with multiple workers
- Add reverse proxy (Nginx)
- Consider async task queue for AI generation
- Scale horizontally with load balancer

**Example Production Setup**:
```
Internet → Nginx → Gunicorn (4 workers) → Flask App
                                            ↓
                                     Ollama Server (GPU)
```

---

## Conclusion

This architecture balances **simplicity** with **extensibility**. The modular design allows for easy enhancements while keeping the core application straightforward and maintainable.

**Key Strengths**:
- ✅ Clear separation of concerns
- ✅ Privacy-focused (local-only)
- ✅ Easy to understand and modify
- ✅ Extensible at multiple points

**Areas for Future Enhancement**:
- Streaming responses
- User authentication for multi-user scenarios
- Advanced preset management
- Performance optimizations for scale

For specific implementation questions, refer to the inline code comments in `prompt_generator.py` and `templates/index.html`.
