# 🎨 ComfyUI Prompt Generator

A powerful, privacy-focused web application that uses local Ollama to generate detailed, optimized prompts for ComfyUI image generation. Supports both Flux and SDXL models with intelligent preset systems and conversational refinement.

[![CI](https://github.com/CreativeNewEra/comfyui-prompt-generator/workflows/CI/badge.svg)](https://github.com/CreativeNewEra/comfyui-prompt-generator/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-black.svg)](https://flake8.pycqa.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ⚡ Quick Start (5 Minutes!)

**Already have Ollama?** Get running in 4 commands:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama (in separate terminal)
ollama serve

# 3. Pull a model
ollama pull qwen3:latest

# 4. Run the app
python prompt_generator.py

# 5. Open http://localhost:5000 and start generating!
```

**First time? Try this:**
- Type: `"a cyberpunk warrior in neon city"`
- Click "Generate Prompt"
- Select some presets (Cyberpunk + Neon Lighting)
- Try "Chat & Refine" mode to iterate!

---

## 📍 Full Documentation

| Your Goal | Documentation |
|-----------|---------------|
| **New user? Complete setup** | [Installation Guide ↓](#-installation) |
| **Want to contribute?** | [Contribution guide →](CONTRIBUTING.md) |
| **Technical deep-dive?** | [Architecture docs →](ARCHITECTURE.md) |
| **Using Claude Code?** | [Development guide →](CLAUDE.md) |
| **API integration?** | [API Reference ↓](#-api-reference) |
| **Using NSFW/adult presets?** | [NSFW Presets Guide →](NSFW_PRESETS_GUIDE.md) |

---

## 🚀 Getting Started

### Quick Start Paths

**Path 1: Quick Setup with Make (Recommended) ⚡**
```bash
1. Make sure Ollama is installed: make setup-ollama
2. Install everything: make install
3. Configure: cp .env.example .env
4. Run the app: make run
5. Open: http://localhost:5000
```

**Path 2: Manual Setup 🛠️**
```bash
1. Make sure Ollama is installed and running
2. Run: ./setup.sh (Mac/Linux) or setup.bat (Windows)
3. Run: python prompt_generator.py
4. Open: http://localhost:5000
5. Test it out!
```

**Path 3: Upload to GitHub 🚀**
```bash
1. Read: GIT_SETUP.md (step-by-step instructions)
2. Create repository on GitHub
3. Run the git commands from GIT_SETUP.md
4. Share your project with the world!
```

**Path 4: Understand the Project First 📚**
```bash
1. Read this README (you're here!)
2. Read: ARCHITECTURE.md (technical architecture)
3. Read: PROJECT_STRUCTURE.md (file organization)
4. Then proceed to Path 1 or Path 2
```

### What You Have

Your complete project package includes:

| Category | Files | Purpose |
|----------|-------|---------|
| **Core App** | `prompt_generator.py`, `templates/index.html` | The actual application |
| **Setup** | `Makefile`, `setup.sh`, `setup.bat`, `requirements.txt` | Easy installation & development |
| **Docs** | `README.md`, `ARCHITECTURE.md`, `QUICKSTART.md` | Complete guides |
| **Testing** | `tests/`, `.github/workflows/ci.yml`, `.flake8` | Quality assurance |
| **Config** | `.env.example`, `.gitignore`, `LICENSE` | Configuration & legal |

✅ Complete, working Flask application
✅ Beautiful, responsive UI
✅ 70+ curated presets (including NSFW/adult content options)
✅ Dual-mode operation (Quick Generate + Chat)
✅ Comprehensive documentation
✅ MIT License
✅ You're 100% ready!

## ✨ Features

### 🚀 Dual Mode Operation
- **⚡ Quick Generate**: Instantly transform simple ideas into detailed prompts
- **💬 Chat & Refine**: Conversational mode to iteratively improve and refine your prompts
- **⚡ Streaming Responses**: Real-time token-by-token generation for immediate feedback

### 🎯 Model-Specific Optimization
- **Flux Dev**: Natural language prompts with detailed scene descriptions
- **SDXL (Juggernaut)**: Quality-tagged prompts with negative prompt generation

### 🎨 Hierarchical Preset System
Choose from **70+ professional artists and styles** across 7 main categories with intelligent cascading selection:

**Main Categories:**
- **📸 Photography**: Portrait, Landscape, Street, Fashion, Wildlife, Macro
- **🎨 Comic Book Art**: Marvel, DC, Manga, Indie styles
- **🎌 Anime/Manga**: Shonen, Shojo, Studio Ghibli, Seinen
- **🐉 Fantasy Art**: High Fantasy, Dark Fantasy, Fairy Tale
- **😱 Horror**: Gothic, Body Horror, Cosmic Horror, Folk Horror
- **🤖 Sci-Fi Art**: Cyberpunk, Space Opera, Hard Sci-Fi, Retro-Futurism
- **🔞 Adult/NSFW Photography**: Boudoir, Artistic Nude, Glamour, Pin-up, Sensual Portrait ([Guide](NSFW_PRESETS_GUIDE.md))

**Smart Features:**
- **Cascading Dropdowns**: Category → Type → Artist (progressive loading)
- **⚡ Preset Packs**: One-click professional setups (90s X-Men, Studio Ghibli, Blade Runner, Newton Bold Fashion, Vintage Pin-up, etc.)
- **🌟 Universal Options**: Mood, Time of Day, Lighting, Weather, Color Palettes, Camera Effects
- **🔥 Popular Indicators**: Highly-rated options marked for easy discovery
- **Feature Flag**: Toggle between hierarchical and legacy flat presets

**Examples:**
- Photography > Portrait > Annie Leibovitz + Golden Hour + Dramatic mood
- Fantasy > High Fantasy > Greg Rutkowski + Epic atmosphere + Stormy weather
- Sci-Fi > Cyberpunk > Syd Mead + Night + Neon lighting + Rainy

### 💾 Prompt History & Management
- **SQLite Database**: Automatically saves all generated prompts
- **Search & Filter**: Find past prompts by content or keywords
- **History Management**: Browse, reuse, and delete previous generations
- **Persistent Storage**: All your prompts saved locally for future reference

### 🔒 Privacy & Control
- **100% Local**: All processing happens on your machine via Ollama
- **No Censorship**: Uncensored models, complete creative freedom
- **No Data Collection**: Your prompts never leave your computer
- **Local Database**: History stored in local SQLite file only

### 🎯 User Experience
- 🌙 **Dark Mode Toggle**: Switch between light and dark themes
- Clean, modern interface with gradient design
- Real-time preset selection
- Copy-to-clipboard functionality
- Chat history in conversational mode
- Responsive design for all screen sizes
- Rotating log files (10MB max, keeps 5 backups)

## 💡 Quick Examples

See the tool in action with these real-world examples:

### Example 1: Simple One-Shot Generation

**Input:**
```
dragon perched on a mountain peak
```

**Output (Flux Dev):**
> A majestic dragon rests atop a windswept mountain peak, its scales shimmering with iridescent hues of deep emerald and sapphire. Massive leathery wings fold gracefully along its muscular body as it surveys the vast mountain range stretching to the horizon. The setting sun casts dramatic golden light across the scene, creating long shadows in the valleys below. Wispy clouds drift past at eye level, and ancient snow clings to the rocky summit. The dragon's eyes gleam with ancient wisdom, smoke curling from its nostrils into the thin mountain air. Ultra-detailed scales catch the light, each one perfectly rendered with depth and texture.

### Example 2: Chat & Refine Mode (Iterative Improvement)

**Initial message:**
```
a cyberpunk street market at night
```

> **Option 1 – Neon Bazaar Snapshot:** A bustling cyberpunk street market illuminated by layers of pink, teal, and amber neon signage. Vendors with holographic displays crowd the narrow alley while rain-slick pavement mirrors the lights. Dense crowds in reflective jackets weave between steam rising from food stalls, creating cinematic atmosphere.
> **Option 2 – Elevated Transit Walkway:** From an overhead walkway, the market stretches below in cascading tiers of stalls and glowing kanji billboards. Drones zip past, casting streaks of light across metallic awnings and intricate cables, giving the scene depth and motion.
> **Option 3 – Vendor Alley Close-Up:** Tight composition focusing on a single aisle of neon umbrellas and stacked crates of tech curiosities, with smoke illuminated by neon drifting across the frame for mood.
> _Negative prompt cues:_ blurry, low detail, washed-out colors, empty street, daylight.
> _Follow-up question:_ Should we emphasize a particular vendor or keep the view broad for now?

**Follow-up message:**
```
add more rain and make it more atmospheric, darker mood
```

> Absolutely—let's saturate the scene with rainfall and moodier contrast.
> **Option 1 – Downpour Drama:** Torrential rain sheets off neon billboards while characters huddle under transparent umbrellas, the puddled ground blooming with chromatic reflections and stray sparks from overhead cables.
> **Option 2 – Misty Neon Canyon:** Low-angle view through drifting fog as rain collects on suspended walkways, volumetric light slicing through mist to silhouette market-goers and glitching holograms.
> **Option 3 – Storm Shelter Niche:** Focus on a recessed stall with tarps snapping in the wind, steam from food carts blending with rain to create hazy atmosphere around the merchants.
> _Negative prompt refresh:_ washed-out colors, sunny daylight, crowdless, cartoonish proportions, flat lighting.
> _Next tweak:_ Want to lean into cooler blue tones or keep the vibrant neon mix while we add the rain?

**Final refinement:**
```
perfect, now add a street vendor in the foreground cooking noodles
```

> Love the idea of featuring the vendor up close—here are some takes:
> **Option 1 – Wok Master Spotlight:** Foreground vendor framed by sizzling wok flames under a transparent canopy, warm orange bounce lighting carving through the blue neon rain behind them while steam curls around their silhouette.
> **Option 2 – Steam-Lit Counter:** Medium shot of the vendor plating noodles on a rain-beaded counter, holographic menu panels flickering overhead and droplets streaking off the canopy edges.
> **Option 3 – Noodle Cart Panorama:** Wider view with the vendor's cart anchoring the foreground, rain trails captured with slight motion blur as the crowd streams past in the glowing marketplace.
> _Negative prompt reminders:_ de-saturated colors, empty foreground, flat composition, daylight, low detail.
> _Question:_ Should the vendor feel gritty and human, or enhanced with cybernetic upgrades?

### Example 3: Using Presets for Targeted Style

**Selected Presets:**
- **Style:** Cinematic
- **Artist/Photographer:** Greg Rutkowski
- **Composition:** Low Angle
- **Lighting:** Volumetric

**Input:**
```
a lone astronaut discovering an alien temple
```

**Output (SDXL/Juggernaut):**
> **Positive Prompt:**
> A lone astronaut stands before a massive alien temple, low angle shot emphasizing the towering ancient structure reaching into an alien sky. Volumetric light beams pierce through the temple's geometric openings, creating god rays that illuminate swirling dust particles and the astronaut's reflective suit. The scene is rendered in cinematic style reminiscent of Greg Rutkowski's epic compositions, with dramatic lighting and atmospheric depth. Intricate alien hieroglyphs cover the temple's weathered stone surface, bioluminescent elements pulse with mysterious energy. The astronaut's helmet reflects the otherworldly architecture, small human figure dwarfed by the monumental discovery. Rich color palette of deep teals, warm oranges, and purple atmospheric haze. Ultra-detailed textures, photorealistic rendering, 8k quality, masterpiece composition.
>
> **Negative Prompt:**
> blurry, low quality, distorted proportions, bad anatomy, cartoon, anime style, oversaturated, flat lighting, low detail, amateur, pixelated, compression artifacts, watermark, signature, text, multiple astronauts, modern buildings, Earth-like structures

---

These examples demonstrate how the tool transforms simple ideas into detailed, production-ready prompts for ComfyUI!

## 📸 Screenshots

Screenshots coming soon - see the app in action at http://localhost:5000 after installation!

## 🎬 Demo

See the app in action by running it locally at http://localhost:5000 - it only takes a few minutes to set up!

## 🏗️ Architecture

The application follows a simple client-server architecture with local AI processing:

```
┌─────────────────────────────────────────────────────────────────┐
│                          User Browser                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              HTML/CSS/JavaScript Frontend                 │  │
│  │  • Preset Selection   • Mode Switching                    │  │
│  │  • Real-time Updates  • Chat History                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP/JSON
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                       Flask Web Server                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Python Backend                         │  │
│  │  • Route Handlers    • Session Management                 │  │
│  │  • Preset System     • Error Handling                     │  │
│  │  • Request Validation                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────┘
                                │ REST API
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                         Ollama Server                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     Local AI Engine                       │  │
│  │  • Model Management  • Prompt Processing                  │  │
│  │  • GPU/CPU Inference • Response Generation                │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Large Language Model                         │
│           (qwen3, llama2, mistral, etc.)                        │
└─────────────────────────────────────────────────────────────────┘

Data Flow:
1. User enters prompt + selects presets in browser
2. Frontend sends JSON request to Flask backend
3. Flask processes request, builds context with presets
4. Flask sends formatted prompt to Ollama API
5. Ollama runs inference on selected LLM
6. LLM generates detailed prompt response
7. Ollama returns response to Flask
8. Flask formats and returns JSON to frontend
9. Frontend displays result with copy button
```

**Key Components:**
- **Frontend**: Single-page application (vanilla JavaScript)
- **Backend**: Flask 3.0.0 with RESTful API design
- **AI Engine**: Ollama for local LLM inference
- **Session Storage**: Server-side Flask sessions
- **Communication**: JSON over HTTP

## ⚡ Performance

### Generation Times
- **Quick Generate**: 5-30 seconds (depending on model and prompt complexity)
- **Chat Messages**: 3-20 seconds per message
- **First Request**: May take longer as model loads into memory

**Factors Affecting Speed:**
- Model size (larger models = slower but better quality)
- Hardware (GPU > CPU, more RAM = faster)
- Prompt length and complexity
- System load and available resources

### Memory Usage
- **Base Application**: ~50 MB (Flask + Python dependencies)
- **Ollama Server**: 200 MB - 1 GB (depending on configuration)
- **Model Memory**:
  - Small models (7B): 4-8 GB RAM
  - Medium models (13B): 8-16 GB RAM
  - Large models (70B+): 32+ GB RAM or GPU with 24+ GB VRAM

### Recommended Specifications
**Minimum:**
- CPU: Dual-core 2.0 GHz
- RAM: 8 GB
- Storage: 10 GB free space
- OS: Windows 10+, macOS 11+, Linux (Ubuntu 20.04+)

**Recommended:**
- CPU: Quad-core 3.0 GHz or better
- RAM: 16 GB
- GPU: NVIDIA GPU with 8+ GB VRAM (optional but significantly faster)
- Storage: 20 GB free space (for multiple models)
- OS: Windows 11, macOS 12+, Linux (Ubuntu 22.04+)

### Supported Platforms
- ✅ **Windows**: 10, 11 (x64)
- ✅ **macOS**: 11 Big Sur and later (Intel & Apple Silicon)
- ✅ **Linux**: Ubuntu 20.04+, Debian 11+, Fedora 37+, Arch Linux
- ✅ **Docker**: Can be containerized for deployment

### Optimization Tips
1. **Use GPU acceleration** if available (Ollama automatically detects NVIDIA GPUs)
2. **Choose smaller models** for faster responses (e.g., qwen3:latest instead of llama2:70b)
3. **Increase timeout** for large models by editing `call_ollama()` timeout parameter
4. **Close other applications** to free up system resources
5. **Use SSD storage** for faster model loading

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.10+**
   ```bash
   python --version
   ```

2. **Ollama** (with a model installed)
   - Download from [ollama.ai](https://ollama.ai)
   - Install a model:
     ```bash
     ollama pull qwen3:latest
     # or any other model you prefer
     ```

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/comfyui-prompt-generator.git
cd comfyui-prompt-generator
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Ollama

Make sure Ollama is running on your system:

```bash
ollama serve
```

Keep this terminal window open.

### 5. Run the Application

In a new terminal (with your virtual environment activated):

```bash
python prompt_generator.py
```

### 6. Open in Browser

Navigate to:
```
http://localhost:5000
```

## 🛠️ Development

### Using the Makefile

The project includes a comprehensive Makefile for common development tasks. To see all available commands:

```bash
make help
```

### Quick Start with Make

**Complete setup in one command:**
```bash
make install
```

This will:
- Create a virtual environment
- Install all dependencies (production + development)
- Prepare the project for development

**Start the application:**
```bash
make run
```

**Run tests:**
```bash
make test
```

**Lint the code:**
```bash
make lint
```

### Common Make Targets

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Full project setup (venv + dependencies) |
| `make install-prod` | Install only production dependencies |
| `make run` | Start the Flask application |
| `make test` | Run the test suite |
| `make test-cov` | Run tests with coverage report |
| `make lint` | Run flake8 linting |
| `make format` | Auto-format code with black and isort |
| `make format-check` | Verify formatting without making changes |
| `make clean` | Remove cache files and logs |
| `make clean-all` | Remove everything including venv |
| `make setup-ollama` | Show Ollama setup instructions |
| `make check-env` | Verify environment setup |
| `make validate` | Run linting + tests (CI simulation) |
| `make logs` | View recent application logs |
| `make info` | Display project information |

### Development Workflow

**First time setup:**
```bash
# 1. Clone the repository
git clone https://github.com/CreativeNewEra/comfyui-prompt-generator.git
cd comfyui-prompt-generator

# 2. Install dependencies
make install

# 3. Setup Ollama (follow displayed instructions)
make setup-ollama

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Run the application
make run
```

**Daily development:**
```bash
# Check environment is ready
make check-env

# Run the application
make run

# In another terminal: run tests
make test

# Lint your code before committing
make lint

# Format your code (optional but recommended)
make format
```

**Before committing:**
```bash
# Ensure formatting checks pass
make format-check

# Validate everything
make validate

# Clean up
make clean
```

### Code Formatting

We use [black](https://black.readthedocs.io/en/stable/) and [isort](https://pycqa.github.io/isort/) to keep the codebase consistent.

- `make format` runs isort followed by black to apply automatic fixes.
- `make format-check` runs both tools in check-only mode and fails if reformatting is required.

Both tools are installed when you run `make install` or `pip install -r requirements-dev.txt`. If you prefer to invoke them directly, use `black prompt_generator.py tests/` and `isort prompt_generator.py tests/` from your virtual environment.

### Manual Setup (Alternative)

If you prefer not to use Make, follow the installation steps in the [Installation](#-installation) section above.

## 📖 Usage

### Quick Generate Mode

1. Select your target model (Flux or SDXL)
2. Optionally choose presets from the dropdowns
3. Describe your image idea in the text area
4. Click "Generate Prompt"
5. Copy the generated prompt to use in ComfyUI

**Example Input:**
```
a warrior in a post-apocalyptic city
```

**Example Output (Flux):**
```
PROMPT: A battle-hardened warrior stands amid the ruins of a post-apocalyptic 
cityscape, weathered armor reflecting the amber glow of a dying sun. Crumbling 
skyscrapers loom in the background, their windows shattered, vegetation reclaiming 
the concrete jungle. The warrior's face is scarred but determined, holding a 
makeshift weapon. Dust particles float in volumetric light beams cutting through 
the haze, creating a cinematic atmosphere of desolation and resilience...
```

### Chat & Refine Mode

1. Switch to "Chat & Refine" mode
2. Start a conversation about your image concept
3. Iterate and refine based on AI suggestions
4. Use presets at any point to guide the direction
5. Click "New Conversation" to start fresh

**Example Conversation:**
```
You: I want a cozy coffee shop scene
AI: Offers several labeled prompt variations, highlights negative prompt ideas, and asks whether to focus on the barista or the seating area.
You: Make it more rainy and atmospheric
AI: Suggests new rainy variations, points out lighting tweaks to try, and checks if we should add characters.
You: Perfect! Now add a person reading by the window
AI: Proposes character-focused options and asks if you'd like to describe wardrobe or camera angle next.
```

### Using Presets

Presets are **optional** but powerful:
- Leave all on "None" for pure AI creativity
- Select one or more to guide the style
- Mix and match for unique combinations
- Experiment with different combinations

**Pro Tips:**
- Combine "Cyberpunk" style + "Neon Lighting" + "Low Angle" for dramatic sci-fi scenes
- Use "Photorealistic" + "Golden Hour" + "Rule of Thirds" for natural portraits
- Try "Surreal" + "Volumetric Lighting" for dreamlike artwork

## ⚙️ Configuration

### Using Environment Variables (Recommended)

The easiest way to configure the application is using a `.env` file:

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your preferred settings:**
   ```bash
   # Ollama Configuration
   OLLAMA_URL=http://localhost:11434/api/generate
   OLLAMA_MODEL=qwen3:latest

   # Flask Configuration
   FLASK_PORT=5000
   FLASK_DEBUG=true

   # Generate a secure secret key for production:
   # python -c "import secrets; print(secrets.token_hex(32))"
   FLASK_SECRET_KEY=your-secret-key-here

   # Logging Configuration
   LOG_LEVEL=INFO
   ```

3. **Available configuration options:**
   - `OLLAMA_URL`: URL for the Ollama API endpoint
   - `OLLAMA_MODEL`: Default model to use (e.g., `qwen3:latest`, `llama2`, `mistral`)
   - `FLASK_PORT`: Port for the web server (default: 5000)
   - `FLASK_DEBUG`: Debug mode - `true` for development, `false` for production
   - `FLASK_SECRET_KEY`: Secret key for session management (generate a random one for production)
   - `LOG_LEVEL`: Logging verbosity - `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` (default: INFO)
   - `ADMIN_API_KEY`: (Recommended for production) Required API key for `/admin/reload-prompts`. Provide via the `X-Admin-API-Key` header or `admin_api_key` query parameter.
   - `ADMIN_ALLOWED_IPS`: Optional comma-separated list of additional IPs permitted to access `/admin/reload-prompts` when no API key is configured.
   - `TRUST_PROXY_HEADERS`: Set to `true` if behind a trusted reverse proxy (nginx, Apache, etc.) that strips client-provided headers. Only enable if your proxy properly sanitizes X-Forwarded-For. Default: `false` (uses direct connection IP).

#### Admin Endpoint Security

The `/admin/reload-prompts` endpoint hot-reloads system prompt files without restarting the server. To prevent unauthorized use:

- **Set `ADMIN_API_KEY`** and include the same value in the `X-Admin-API-Key` header when calling the endpoint.
- If no API key is configured, only loopback addresses (e.g., `127.0.0.1`, `::1`) are permitted by default. Add trusted IPs to `ADMIN_ALLOWED_IPS` to extend access.
- Every denied attempt is logged with the source IP so you can monitor suspicious traffic.
- **Security Note**: By default, client IP detection uses `remote_addr` which cannot be spoofed. Only enable `TRUST_PROXY_HEADERS` if you're behind a reverse proxy that properly strips untrusted X-Forwarded-For headers.

### Manual Configuration (Alternative)

If you prefer not to use a `.env` file, you can edit `prompt_generator.py` directly:

**Change Ollama Model:**
```python
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:latest')
# Change the second argument to your preferred model
```

**Change Port:**
```python
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
# Change '5000' to your preferred port
```

**Remote Ollama Instance:**
```python
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434/api/generate')
# Change the second argument to your Ollama server URL
```

## 🎨 Customizing Presets

Add your own presets by editing `presets.json` in the project root:

```json
{
  "styles": {
    "Your Custom Style": "style description, tags, keywords"
  },
  "artists": {
    "Artist Name": "in the style of Artist Name"
  },
  "composition": {
    "Your Composition": "composition description"
  },
  "lighting": {
    "Your Lighting": "lighting description"
  }
}
```

**Hot-Reload Feature**: Changes to `presets.json` take effect immediately on the next request - no server restart needed! Just refresh your browser to see the new presets.

## 🔌 API Reference

The application provides the following REST API endpoints:

### Core Generation
- **`GET /`** - Serve the main web application
- **`GET /presets`** - Return available preset configurations
- **`GET /models`** - Return list of installed Ollama models
- **`POST /generate`** - One-shot prompt generation (Quick Generate mode)
- **`POST /chat`** - Conversational prompt refinement (Chat & Refine mode)
- **`POST /reset`** - Clear chat conversation history

### Streaming (Real-time)
- **`POST /generate-stream`** - One-shot generation with Server-Sent Events streaming
- **`POST /chat-stream`** - Conversational mode with real-time token streaming

### History Management
- **`GET /history`** - Retrieve prompt generation history (supports `?limit=N` and `?q=search`)
- **`DELETE /history/<id>`** - Delete a specific history item by ID

For detailed API documentation including request/response formats, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 🧪 Testing

The project includes a comprehensive test suite to ensure functionality and reliability.

### Running Tests

1. **Install test dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Run all tests:**
   ```bash
   pytest
   ```

3. **Run with verbose output:**
   ```bash
   pytest -v
   ```

4. **Run specific test file:**
   ```bash
   pytest tests/test_presets.py
   pytest tests/test_app.py
   ```

5. **Run with coverage report:**
   ```bash
   pytest --cov=prompt_generator --cov-report=html
   ```

### Test Structure

```
tests/
├── __init__.py           # Package initialization
├── conftest.py           # Pytest fixtures and configuration
├── test_presets.py       # Preset validation tests
└── test_app.py          # Flask route and functionality tests
```

### What's Tested

**Preset Tests (`test_presets.py`):**
- ✅ All preset categories exist (styles, artists, composition, lighting)
- ✅ Presets have valid structure (dictionaries with string values)
- ✅ "None" option exists in each category
- ✅ Preset values are non-empty for non-None options
- ✅ Total preset count meets expectations

**Application Tests (`test_app.py`):**
- ✅ Flask app initializes correctly
- ✅ GET / returns 200 and HTML content
- ✅ GET /presets returns valid JSON with all categories
- ✅ POST /generate with valid input works
- ✅ POST /generate with missing input returns 400
- ✅ POST /chat with valid message works
- ✅ POST /chat with missing message returns 400
- ✅ POST /reset works correctly
- ✅ 404 errors return JSON (not HTML)

### Writing New Tests

To add new tests, create a new test file in the `tests/` directory:

```python
# tests/test_new_feature.py
import pytest

def test_your_feature(client, presets):
    """Test description"""
    # Your test code here
    assert True
```

**Available Fixtures:**
- `flask_app` - The Flask application instance
- `client` - Flask test client for making requests
- `presets` - Access to PRESETS dictionary

### Continuous Integration

This project uses GitHub Actions for automated testing and code quality checks.

**What's Automated:**
- ✅ Tests run on Python 3.10, 3.11, 3.12, and 3.13
- ✅ Flake8 linting for code quality
- ✅ Automated on every push and pull request
- ✅ Status badge shows current build status

**CI Configuration:**
The workflow is defined in `.github/workflows/ci.yml` and runs:
1. **Syntax checking** - Catches Python syntax errors
2. **Linting** - Enforces code style with flake8
3. **Unit tests** - Runs the full test suite
4. **Import validation** - Ensures the app can initialize

**View CI Status:**
Check the [Actions tab](https://github.com/CreativeNewEra/comfyui-prompt-generator/actions) to see test results for all commits and pull requests.

### Code Quality

**Linting with flake8:**
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run flake8 linting
flake8 .

# Check specific file
flake8 prompt_generator.py
```

**Configuration:**
Flake8 settings are in `.flake8`:
- Max line length: 120 characters
- Excludes: virtual environments, build artifacts, logs
- Statistics and source code shown for violations

### Testing Best Practices

1. **Mock Ollama calls** - Tests use `monkeypatch` to avoid requiring Ollama
2. **Test edge cases** - Empty inputs, missing fields, invalid data
3. **Keep tests fast** - No actual AI model calls in unit tests
4. **Maintain coverage** - Aim for >80% code coverage
5. **CI validation** - All tests must pass before merging

## 🐛 Troubleshooting

### "Failed to connect to server. Make sure Ollama is running!"

**Solution:**
- Ensure Ollama is running: `ollama serve`
- Check if Ollama is on port 11434: `curl http://localhost:11434`
- Verify you have a model installed: `ollama list`

### "Error connecting to Ollama: Connection refused"

**Solution:**
- Start Ollama service
- Check firewall settings
- Verify OLLAMA_URL in the code matches your setup

### Slow Generation Times

**Solutions:**
- Use a smaller/faster model (e.g., `qwen3:latest` instead of larger models)
- Ensure Ollama has sufficient RAM allocated
- Consider using GPU acceleration if available

### Empty or Poor Quality Prompts

**Solutions:**
- Try a different Ollama model (some work better for creative tasks)
- Provide more detailed input descriptions
- Use presets to guide the AI
- Try Chat mode for iterative refinement

## 🗺️ Roadmap

Future enhancements planned:

- [ ] Model selector dropdown (auto-detect installed Ollama models)
- [ ] Prompt history with search and tags
- [ ] Save favorite preset combinations
- [ ] Batch generation (multiple variations)
- [ ] Direct ComfyUI API integration
- [ ] Image upload for prompt analysis
- [ ] Token counter and prompt analysis
- [ ] Export/import prompt collections
- [ ] Custom preset creator UI
- [ ] Prompt weighting system

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) - For making local LLMs accessible
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - The amazing image generation workflow tool
- [Flask](https://flask.palletsprojects.com/) - Lightweight web framework
- The open-source AI community

## 📧 Support

If you encounter issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Open an issue on GitHub
3. Join the discussion in Issues

## ⭐ Show Your Support

If you find this project useful, please consider:
- Starring the repository ⭐
- Sharing it with others
- Contributing improvements
- Reporting bugs or suggesting features

---

**Made with ❤️ for the ComfyUI and Ollama communities**

*Generate amazing prompts, locally and privately!*
