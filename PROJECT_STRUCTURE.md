# 📁 Project Structure

```
comfyui-prompt-generator/
│
├── 📄 prompt_generator.py          # Main Flask application
│   ├── Flask routes and API endpoints
│   ├── Ollama API integration
│   ├── Preset definitions (styles, artists, composition, lighting)
│   ├── System prompts for Flux and SDXL
│   └── Session management for chat mode
│
├── 📁 templates/
│   └── 📄 index.html               # Single-page frontend application
│       ├── Dual-mode UI (Quick Generate / Chat & Refine)
│       ├── Model selector (Flux / SDXL)
│       ├── Preset dropdown system
│       ├── Chat history display
│       └── Real-time interaction with backend
│
├── 📁 .github/
│   └── 📁 workflows/
│       └── 📄 lint.yml             # GitHub Actions for Python linting
│
├── 📄 requirements.txt             # Python dependencies
│   ├── Flask==3.0.0
│   └── requests==2.31.0
│
├── 📄 .gitignore                   # Git ignore patterns
│   ├── Python bytecode
│   ├── Virtual environments
│   ├── IDE files
│   └── OS-specific files
│
├── 📄 LICENSE                      # MIT License
│
├── 📄 README.md                    # Comprehensive documentation
│   ├── Features overview
│   ├── Installation guide
│   ├── Usage examples
│   ├── Configuration options
│   ├── Troubleshooting
│   └── Roadmap
│
├── 📄 QUICKSTART.md                # 5-minute setup guide
│   ├── Quick installation steps
│   ├── First use examples
│   └── Common issues
│
├── 📄 CONTRIBUTING.md              # Contribution guidelines
│   ├── How to contribute
│   ├── Code style guide
│   ├── PR process
│   └── Architecture overview
│
├── 📄 setup.sh                     # Linux/Mac setup script
│   ├── Environment setup
│   ├── Dependency installation
│   └── Quick start instructions
│
└── 📄 setup.bat                    # Windows setup script
    ├── Environment setup
    ├── Dependency installation
    └── Quick start instructions
```

## 🔑 Key Files Explained

### `prompt_generator.py`
The heart of the application. Contains:
- **Flask Routes**: `/`, `/presets`, `/generate`, `/chat`, `/reset`
- **Ollama Integration**: `call_ollama()` function handles API communication
- **Preset System**: Curated collections of styles, artists, compositions, and lighting
- **Model-Specific Prompts**: Optimized system prompts for Flux and SDXL

### `templates/index.html`
Complete frontend in a single file:
- **Responsive Design**: Works on all screen sizes
- **Interactive UI**: Real-time preset selection and mode switching
- **Chat Interface**: Full conversation history with message bubbles
- **Modern Styling**: Gradient backgrounds, smooth animations

### Configuration Files
- **requirements.txt**: Minimal dependencies (Flask + requests)
- **.gitignore**: Prevents committing unnecessary files
- **LICENSE**: MIT license for open-source distribution
- **GitHub Actions**: Automated code quality checks

### Documentation Files
- **README.md**: Full documentation (1000+ lines)
- **QUICKSTART.md**: Get started in 5 minutes
- **CONTRIBUTING.md**: Guide for contributors

## 🎨 Preset Categories

The application includes 50+ presets across 4 categories:

1. **Styles (14 options)**
   - Cinematic, Anime, Photorealistic, Oil Painting, Digital Art
   - Watercolor, Cyberpunk, Fantasy Art, Comic Book, Minimalist
   - Surreal, Vintage, 3D Render, Pencil Sketch

2. **Artists/Photographers (17 options)**
   - Digital Artists: Greg Rutkowski, Artgerm, Ross Tran, Loish
   - Traditional: Alphonse Mucha, H.R. Giger, Moebius
   - Photographers: Ansel Adams, Annie Leibovitz, Steve McCurry
   - Animation: Hayao Miyazaki, Makoto Shinkai

3. **Composition (15 options)**
   - Portrait, Landscape, Close-up, Wide Shot, Medium Shot
   - Extreme Close-up, Bird's Eye View, Low Angle, High Angle
   - Dutch Angle, Rule of Thirds, Symmetrical, Leading Lines
   - Frame within Frame, Golden Ratio

4. **Lighting (15 options)**
   - Natural: Golden Hour, Blue Hour, Natural Window Light
   - Studio: Professional Studio Lighting, Soft Diffused
   - Creative: Neon, Volumetric, Backlit, Dramatic Shadows
   - Atmospheric: Moonlight, Candlelight, Fire Light, Underwater

## 🔄 Application Flow

### Quick Generate Mode
1. User enters description + selects presets
2. Frontend sends POST to `/generate`
3. Backend builds prompt with presets
4. Ollama generates detailed prompt
5. Response displayed with copy button

### Chat & Refine Mode
1. User sends message + selects presets
2. Frontend sends POST to `/chat`
3. Backend maintains conversation history in session
4. Each exchange builds on previous context
5. Full chat history displayed
6. Can reset with `/reset` endpoint

## 🛠️ Customization Points

Easy places to extend the application:

1. **Add Presets**: Edit `PRESETS` dictionary
2. **Change Model**: Modify `call_ollama()` function
3. **Adjust System Prompts**: Edit `SYSTEM_PROMPTS` dictionary
4. **Modify UI**: Update `templates/index.html`
5. **Add Routes**: Create new Flask endpoints

## 📊 Technical Stack

- **Backend**: Python 3.8+ with Flask 3.0.0
- **Frontend**: Vanilla JavaScript (no frameworks)
- **Styling**: Pure CSS with modern features
- **AI Integration**: Ollama local API
- **Session Management**: Flask server-side sessions

## 🎯 Design Decisions

- **Single HTML file**: Simplifies deployment
- **No external CSS/JS**: Everything self-contained
- **Server-side sessions**: Better security than localStorage
- **Minimal dependencies**: Only Flask and requests
- **No database**: Stateless design for simplicity
- **Local-first**: Privacy and no API costs

---

**Total Files Created**: 11
**Lines of Code**: ~2000+
**Documentation**: ~4000+ words
**Ready to Deploy**: ✅
