# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **ComfyUI Prompt Generator** - a Flask web application that integrates with local Ollama to generate detailed prompts for ComfyUI image generation. It supports both Flux and SDXL models with dual operation modes (Quick Generate and Chat & Refine).

## Development Commands

### Setup and Installation
```bash
# Initial setup (Linux/Mac)
./setup.sh

# Initial setup (Windows)
setup.bat

# Manual setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Running the Application
```bash
# Start Ollama (required dependency)
ollama serve

# Run the Flask application
python prompt_generator.py
# Access at: http://localhost:5000
```

### Testing Ollama Connection
```bash
# Verify Ollama is running
curl http://localhost:11434

# List installed models
ollama list

# Install a model if needed
ollama pull qwen3:latest
```

## Architecture

### Core Application Structure
- **Backend**: `prompt_generator.py` - Flask application with 5 main routes
- **Frontend**: `index.html` - Single-page application (no templates/ directory)
- **Dependencies**: Only Flask 3.0.0 and requests 2.31.0

### Key Routes
- `GET /` - Serves the main application
- `GET /presets` - Returns available preset configurations
- `POST /generate` - One-shot prompt generation (Quick Generate mode)
- `POST /chat` - Conversational prompt refinement (Chat & Refine mode)
- `POST /reset` - Clears chat conversation history

### Preset System
The application includes 50+ curated presets across 4 categories:
- **Styles** (14 options): Cinematic, Anime, Photorealistic, etc.
- **Artists/Photographers** (17 options): Greg Rutkowski, Ansel Adams, etc.
- **Composition** (15 options): Portrait, Landscape, Rule of Thirds, etc.
- **Lighting** (15 options): Golden Hour, Neon, Volumetric, etc.

### Model-Specific Prompting
- **Flux Dev**: Natural language, conversational style prompts
- **SDXL (Juggernaut)**: Quality-tagged prompts with negative prompt generation

## Configuration

### Changing Ollama Model
Edit `prompt_generator.py` line 134:
```python
def call_ollama(messages, model="qwen3:latest"):
    # Change to your preferred model
```

### Changing Application Port
Edit `prompt_generator.py` line 323:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
# Change port=5000 to desired port
```

### Remote Ollama Instance
Edit `prompt_generator.py` line 15:
```python
OLLAMA_URL = "http://your-ollama-server:11434/api/generate"
```

## Development Guidelines

### Adding New Presets
Edit the `PRESETS` dictionary in `prompt_generator.py` (lines 18-96):
```python
PRESETS = {
    "styles": {
        "Your New Style": "style description, tags, keywords",
        # ...
    },
    # ... other categories
}
```

### Session Management
- Chat mode uses Flask server-side sessions
- Conversation history is automatically limited to 20 messages + system prompt
- Sessions reset when switching models

### Frontend Architecture
- Single HTML file with embedded CSS and JavaScript
- No external dependencies or frameworks
- Responsive design with mobile support
- Real-time preset selection and mode switching

## Common Development Tasks

### Adding New Routes
Follow the existing pattern in `prompt_generator.py`:
```python
@app.route('/new-endpoint', methods=['POST'])
def new_function():
    data = request.json
    # Handle request
    return jsonify({'result': 'response'})
```

### Modifying UI
All frontend code is in `index.html`:
- CSS: Lines 8-367
- HTML structure: Lines 370-459  
- JavaScript: Lines 461-671

### Debugging Connection Issues
1. Verify Ollama is running: `ollama serve`
2. Check Ollama API: `curl http://localhost:11434`
3. Verify model installation: `ollama list`
4. Check Flask console for backend errors
5. Check browser console (F12) for frontend errors

## Troubleshooting

### "Failed to connect to server"
- Ensure Ollama is running: `ollama serve`
- Verify correct Ollama URL in configuration
- Check firewall settings

### Empty or Poor Quality Prompts
- Try different Ollama models
- Provide more detailed input descriptions
- Use presets to guide AI output
- Switch to Chat mode for iterative refinement

### Port Conflicts
- Change port in `prompt_generator.py` line 323
- Common alternatives: 8080, 3000, 8000

## Privacy and Security

- All processing happens locally via Ollama
- No external API calls or data collection
- Session data stored server-side (not localStorage)
- No sensitive information should be logged or committed