# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documentation consolidation and accuracy improvements
- Comprehensive API reference in README
- Database schema documentation in ARCHITECTURE
- Streaming responses documentation
- Dark mode feature now documented

### Changed
- Merged QUICKSTART.md into README (Quick Start section)
- Merged PROJECT_STRUCTURE.md into ARCHITECTURE (Project Structure section)
- Merged GIT_SETUP.md into CONTRIBUTING (Publishing to GitHub section)
- Updated all line count references (prompt_generator.py now ~1,760 lines)
- Updated preset count to accurate 61 presets
- Fixed outdated route documentation (added 4 new endpoints)

### Documentation
- Added missing features: Prompt History Database, Streaming Responses, Dark Mode Toggle
- Updated environment variables (added LOG_LEVEL)
- Fixed Architecture documentation with new routes: /generate-stream, /chat-stream, /history, /history/<id>
- Added Database Layer section with SQLite schema
- Added Streaming Responses (SSE) section
- Improved cross-references between docs

### Removed
- QUICKSTART.md (merged into README)
- PROJECT_STRUCTURE.md (merged into ARCHITECTURE)
- GIT_SETUP.md (merged into CONTRIBUTING)

### Planned
- Model selector dropdown (auto-detect Ollama models)
- Save favorite preset combinations
- Batch generation (multiple variations)
- Direct ComfyUI API integration
- Image upload for prompt analysis
- Token counter and prompt analysis
- Custom preset creator UI
- Condense EXAMPLES.md for better readability

## [1.0.0] - 2025-01-XX

### Added
- Initial release of ComfyUI Prompt Generator
- Dual-mode operation (Quick Generate / Chat & Refine)
- Support for Flux Dev and SDXL (Juggernaut) models
- Intelligent preset system with 50+ options:
  - 14 art styles (Cinematic, Anime, Photorealistic, etc.)
  - 17 artist/photographer styles
  - 15 composition presets
  - 15 lighting presets
- Ollama integration for local AI processing
- Real-time prompt generation
- Conversational refinement mode with history
- Copy-to-clipboard functionality
- Responsive web interface
- Session management for chat mode
- Model-specific system prompts
- Comprehensive documentation
- Setup scripts for Windows, Mac, and Linux
- MIT license

### Features
- 🔒 100% local processing - no data sent to external servers
- 💬 Interactive chat mode for iterative prompt refinement
- ⚡ Quick generate mode for instant results
- 🎨 Mix-and-match preset combinations
- 📋 One-click copy to clipboard
- 🎯 Model-optimized prompts (Flux uses natural language, SDXL uses quality tags)
- 🔄 Conversation history in chat mode
- ⚙️ Easy customization of presets

### Technical Details
- Built with Flask 3.0.0
- Python 3.8+ compatible
- Minimal dependencies (Flask + requests)
- No database required
- Server-side session management
- RESTful API design

---

## Version History Format

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security improvements
```

---

[Unreleased]: https://github.com/YOUR_USERNAME/comfyui-prompt-generator/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/YOUR_USERNAME/comfyui-prompt-generator/releases/tag/v1.0.0
