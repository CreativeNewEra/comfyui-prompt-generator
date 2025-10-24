# 🎨 ComfyUI Prompt Generator

A powerful, privacy-focused web application that uses local Ollama to generate detailed, optimized prompts for ComfyUI image generation. Supports both Flux and SDXL models with intelligent preset systems and conversational refinement.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)

## ✨ Features

### 🚀 Dual Mode Operation
- **⚡ Quick Generate**: Instantly transform simple ideas into detailed prompts
- **💬 Chat & Refine**: Conversational mode to iteratively improve and refine your prompts

### 🎯 Model-Specific Optimization
- **Flux Dev**: Natural language prompts with detailed scene descriptions
- **SDXL (Juggernaut)**: Quality-tagged prompts with negative prompt generation

### 🎨 Intelligent Preset System
Choose from curated presets across four categories:
- **Styles**: Cinematic, Anime, Photorealistic, Oil Painting, Cyberpunk, and more
- **Artists/Photographers**: Greg Rutkowski, Ansel Adams, Studio Ghibli, and more
- **Composition**: Portrait, Landscape, Bird's Eye View, Golden Ratio, and more
- **Lighting**: Golden Hour, Volumetric, Studio Lighting, Neon, and more

### 🔒 Privacy & Control
- **100% Local**: All processing happens on your machine via Ollama
- **No Censorship**: Uncensored models, complete creative freedom
- **No Data Collection**: Your prompts never leave your computer

### 🎯 User Experience
- Clean, modern interface with gradient design
- Real-time preset selection
- Copy-to-clipboard functionality
- Chat history in conversational mode
- Responsive design for all screen sizes

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.8+**
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
AI: [Generates detailed prompt]
You: Make it more rainy and atmospheric
AI: [Refines with rain and mood details]
You: Perfect! Now add a person reading by the window
AI: [Adds character with natural integration]
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

### Changing the Ollama Model

Edit `prompt_generator.py`:

```python
def call_ollama(messages, model="qwen3:latest"):
    # Change to your preferred model
    # Examples: "llama2", "mistral", "codellama", etc.
```

### Changing the Port

Edit the last line of `prompt_generator.py`:

```python
app.run(debug=True, host='0.0.0.0', port=5000)
# Change port=5000 to your preferred port
```

### Remote Ollama Instance

If Ollama is running on a different machine:

```python
OLLAMA_URL = "http://your-ollama-server:11434/api/generate"
```

## 🎨 Customizing Presets

Add your own presets by editing the `PRESETS` dictionary in `prompt_generator.py`:

```python
PRESETS = {
    "styles": {
        "Your Custom Style": "your, custom, tags, here",
        # Add more...
    },
    # ... other categories
}
```

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
