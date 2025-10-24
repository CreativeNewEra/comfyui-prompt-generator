# 🚀 Quick Start Guide

## Get Up and Running in 5 Minutes!

### Step 1: Install Ollama (if you haven't already)

**Download Ollama:**
- Visit [ollama.ai](https://ollama.ai)
- Download for your OS (Windows/Mac/Linux)
- Install and start Ollama

**Pull a Model:**
```bash
ollama pull qwen3:latest
```

### Step 2: Setup the Project

**Option A: Automatic Setup (Recommended)**

On Linux/Mac:
```bash
chmod +x setup.sh
./setup.sh
```

On Windows:
```bash
setup.bat
```

**Option B: Manual Setup**

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Start Ollama

In a terminal window:
```bash
ollama serve
```

Keep this running!

### Step 4: Run the App

In a new terminal (with venv activated):
```bash
python prompt_generator.py
```

### Step 5: Open in Browser

Navigate to:
```
http://localhost:5000
```

## 🎯 First Use

1. **Try Quick Generate Mode:**
   - Type: "a cyberpunk warrior in neon city"
   - Click "Generate Prompt"
   - Copy the result!

2. **Experiment with Presets:**
   - Select "Cyberpunk" style
   - Choose "Low Angle" composition
   - Pick "Neon Lighting"
   - Try the same prompt again!

3. **Try Chat Mode:**
   - Switch to "Chat & Refine"
   - Start with: "I want a cozy scene"
   - Refine: "make it rainy"
   - Keep iterating!

## 🐛 Troubleshooting

**Can't connect to Ollama?**
- Make sure Ollama is running: `ollama serve`
- Check: `curl http://localhost:11434`

**No models installed?**
```bash
ollama list          # Check what you have
ollama pull qwen3:latest  # Install a model
```

**Port 5000 in use?**
Edit `prompt_generator.py`, change the last line:
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Use different port
```

## 📚 What's Next?

- Read the full [README.md](README.md)
- Check out [CONTRIBUTING.md](CONTRIBUTING.md) to add features
- Customize presets in `prompt_generator.py`
- Join the community and share your creations!

---

**Need Help?** Open an issue on GitHub!
