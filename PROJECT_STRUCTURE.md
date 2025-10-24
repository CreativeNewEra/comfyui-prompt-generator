# 📁 Project Structure

## 🌳 File Tree

```
comfyui-prompt-generator/
│
├── 📁 .github/
│   └── 📁 workflows/
│       └── 📄 lint.yml                    # GitHub Actions CI/CD
│
├── 📁 templates/
│   └── 📄 index.html                      # Frontend application (450 lines)
│
├── 📄 .gitignore                          # Git ignore patterns
├── 📄 CHANGELOG.md                        # Version history
├── 📄 CLAUDE.md                           # Claude Code instructions
├── 📄 CONTRIBUTING.md                     # Contribution guide (200+ lines)
├── 📄 GIT_SETUP.md                        # GitHub upload instructions
├── 📄 LICENSE                             # MIT License
├── 📄 PROJECT_STRUCTURE.md                # This architecture documentation
├── 📄 QUICKSTART.md                       # 5-minute setup guide
├── 📄 README.md                           # Main documentation (500+ lines)
├── 📄 prompt_generator.py                 # Flask backend (340 lines)
├── 📄 requirements.txt                    # Python dependencies
├── 📄 setup.bat                           # Windows setup script
└── 📄 setup.sh                            # Linux/Mac setup script

Total: 14 files across 3 directories
```

## 📊 File Breakdown by Type

### Application Code (2 files)
```
prompt_generator.py     340 lines   Python/Flask backend
templates/index.html    450 lines   HTML/CSS/JavaScript frontend
─────────────────────────────────
Total Code:             790 lines
```

### Documentation (7 files)
```
README.md               500+ lines  Main documentation
CONTRIBUTING.md         200+ lines  Contributor guide
PROJECT_STRUCTURE.md    200+ lines  Architecture docs (this file)
GIT_SETUP.md           250+ lines  Upload instructions
QUICKSTART.md          100+ lines  Quick start guide
CLAUDE.md              150+ lines  Claude Code guide
CHANGELOG.md           100+ lines  Version history
LICENSE                 21 lines   MIT License
─────────────────────────────────
Total Documentation:    1,600+ lines (~5,500 words)
```

### Configuration (4 files)
```
requirements.txt        2 lines     Python packages
.gitignore             40 lines     Git patterns
setup.sh               30 lines     Unix setup
setup.bat              35 lines     Windows setup
```

### CI/CD (1 file)
```
.github/workflows/lint.yml  25 lines  GitHub Actions
```

## 📦 Total Project Size

- **Files**: 14
- **Directories**: 3
- **Code**: ~790 lines
- **Documentation**: ~1,600 lines
- **Configuration**: ~110 lines
- **Total Lines**: ~2,500 lines

## 🎯 What Each File Does

| File | Purpose | Priority |
|------|---------|----------|
| `prompt_generator.py` | Core application logic | 🔴 Critical |
| `templates/index.html` | User interface | 🔴 Critical |
| `requirements.txt` | Dependencies | 🔴 Critical |
| `README.md` | Main documentation | 🟡 Important |
| `QUICKSTART.md` | Quick setup | 🟡 Important |
| `LICENSE` | Legal terms | 🟡 Important |
| `.gitignore` | Clean commits | 🟡 Important |
| `GIT_SETUP.md` | Upload guide | 🟢 Helpful |
| `CONTRIBUTING.md` | Contributor guide | 🟢 Helpful |
| `setup.sh` | Unix automation | 🟢 Helpful |
| `setup.bat` | Windows automation | 🟢 Helpful |
| `CLAUDE.md` | Claude Code guide | 🔵 Reference |
| `PROJECT_STRUCTURE.md` | Architecture (this file) | 🔵 Reference |
| `CHANGELOG.md` | Version tracking | 🔵 Reference |
| `.github/workflows/lint.yml` | Code quality | 🔵 Reference |

## 🔑 Key Components Explained

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
- **README.md**: Full documentation with Getting Started guide
- **QUICKSTART.md**: Get started in 5 minutes
- **CONTRIBUTING.md**: Guide for contributors
- **GIT_SETUP.md**: Step-by-step GitHub upload instructions
- **CLAUDE.md**: Instructions for Claude Code development

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

1. **Add Presets**: Edit `PRESETS` dictionary in `prompt_generator.py`
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

## 💾 Disk Space

Estimated sizes:
```
Code:           ~50 KB
Documentation:  ~200 KB
Total:          ~250 KB (minimal!)
```

With virtual environment:
```
venv/:          ~50 MB (Python packages)
Total:          ~50.25 MB
```

## 🚀 File Creation Order (if rebuilding)

1. **Core Files First**
   ```
   prompt_generator.py
   templates/index.html
   requirements.txt
   ```

2. **Essential Config**
   ```
   .gitignore
   LICENSE
   ```

3. **Main Documentation**
   ```
   README.md
   QUICKSTART.md
   ```

4. **Helper Scripts**
   ```
   setup.sh
   setup.bat
   ```

5. **Extended Documentation**
   ```
   CONTRIBUTING.md
   GIT_SETUP.md
   PROJECT_STRUCTURE.md
   CHANGELOG.md
   CLAUDE.md
   ```

6. **CI/CD**
   ```
   .github/workflows/lint.yml
   ```

## 🎨 Color-Coded Priority

- 🔴 **Critical**: Can't run without these
- 🟡 **Important**: Should include for professionalism
- 🟢 **Helpful**: Makes life easier
- 🔵 **Reference**: Nice to have, informative

---

**Everything is organized, documented, and ready to go!** ✨
