# 🚀 Git Setup & Upload Instructions

## Step-by-Step Guide to Upload to GitHub

### 1️⃣ Create GitHub Repository

1. Go to [GitHub](https://github.com)
2. Click the **+** button → **New repository**
3. Fill in:
   - **Repository name**: `comfyui-prompt-generator`
   - **Description**: "AI-powered prompt generator for ComfyUI using local Ollama - private, uncensored, and feature-rich"
   - **Visibility**: Choose Public or Private
   - **✅ Do NOT** initialize with README (we already have one)
4. Click **Create repository**

### 2️⃣ Navigate to Your Project Folder

```bash
cd /path/to/comfyui-prompt-generator
```

### 3️⃣ Initialize Git Repository

```bash
# Initialize git
git init

# Add all files
git add .

# Make your first commit
git commit -m "Initial commit: ComfyUI Prompt Generator v1.0

- Flask web application with dual-mode interface
- Quick Generate and Chat & Refine modes
- Support for Flux and SDXL models
- 50+ curated presets (styles, artists, composition, lighting)
- Ollama integration for local AI processing
- Complete documentation and setup scripts
- MIT licensed"
```

### 4️⃣ Connect to GitHub

Replace `YOUR_USERNAME` with your GitHub username:

```bash
# Set main as default branch
git branch -M main

# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/comfyui-prompt-generator.git

# Push to GitHub
git push -u origin main
```

## 🔐 Alternative: Using SSH

If you prefer SSH (recommended for frequent use):

```bash
# Add remote with SSH
git remote add origin git@github.com:YOUR_USERNAME/comfyui-prompt-generator.git

# Push to GitHub
git push -u origin main
```

## 📋 Quick Copy-Paste Version

```bash
# Navigate to project
cd comfyui-prompt-generator

# Initialize and commit
git init
git add .
git commit -m "Initial commit: ComfyUI Prompt Generator v1.0"

# Connect and push (CHANGE YOUR_USERNAME!)
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/comfyui-prompt-generator.git
git push -u origin main
```

## 🎯 Post-Upload Checklist

After uploading, enhance your repository:

### 1. Add Topics (GitHub Tags)
Go to your repo → About section → ⚙️ Settings → Add topics:
```
comfyui, prompt-generator, ollama, ai, stable-diffusion, 
flux, sdxl, image-generation, flask, python, local-ai
```

### 2. Create First Release
1. Go to **Releases** → **Create a new release**
2. Tag: `v1.0.0`
3. Title: `ComfyUI Prompt Generator v1.0.0`
4. Description:
```markdown
## 🎨 First Release!

Initial release of ComfyUI Prompt Generator - a powerful, privacy-focused 
prompt engineering tool.

### ✨ Features
- 🚀 Dual-mode operation (Quick Generate / Chat & Refine)
- 🎯 Model-specific optimization (Flux Dev / SDXL)
- 🎨 50+ curated presets
- 🔒 100% local processing with Ollama
- 💬 Conversational refinement mode
- 📋 One-click copy to clipboard

### 📦 Installation
See [README.md](README.md) for detailed setup instructions.

### 🙏 Acknowledgments
Thanks to the Ollama and ComfyUI communities!
```

### 3. Add a Website (Optional)
If you have GitHub Pages enabled:
1. Go to Settings → Pages
2. Source: Deploy from branch → main → /root
3. Your README will become a website!

### 4. Enable Discussions (Optional)
Settings → Features → ✅ Discussions
- Great for community Q&A

### 5. Add Repository Description
In the About section:
```
AI-powered prompt generator for ComfyUI using local Ollama. 
Generate detailed, optimized prompts with 50+ presets. 
Private, uncensored, and easy to use. 🎨
```

## 🔄 Future Updates

When you make changes:

```bash
# Check status
git status

# Add changes
git add .

# Commit with descriptive message
git commit -m "Add feature: <description>"

# Push to GitHub
git push
```

## 🌿 Creating Branches

For new features:

```bash
# Create and switch to new branch
git checkout -b feature/preset-saver

# Make changes, commit
git add .
git commit -m "Add preset saving functionality"

# Push branch
git push -u origin feature/preset-saver

# Then create Pull Request on GitHub
```

## 📝 Good Commit Message Examples

```bash
# Feature additions
git commit -m "Add batch generation feature"
git commit -m "Implement prompt history with search"

# Bug fixes
git commit -m "Fix: Resolve Ollama connection timeout"
git commit -m "Fix: Chat history not clearing on reset"

# Documentation
git commit -m "Docs: Add troubleshooting section"
git commit -m "Docs: Update installation guide for Windows"

# Refactoring
git commit -m "Refactor: Improve preset system architecture"
git commit -m "Refactor: Optimize Ollama API calls"
```

## 🎉 You're Done!

Your repository is now live! Share it:
- Twitter/X with hashtags: #ComfyUI #Ollama #AIArt
- Reddit: r/StableDiffusion, r/comfyui
- Discord: ComfyUI and Ollama communities
- LinkedIn: Show off your project!

## 🆘 Troubleshooting

**Authentication Failed?**
```bash
# GitHub removed password auth - use Personal Access Token
# Go to: Settings → Developer settings → Personal access tokens → Generate new token
# Use token as password when prompted
```

**Large Files Warning?**
```bash
# Add to .gitignore, then:
git rm --cached <file>
git commit -m "Remove large file"
git push
```

**Merge Conflicts?**
```bash
# Pull latest changes first
git pull origin main

# Resolve conflicts in files
# Then commit and push
git add .
git commit -m "Resolve merge conflicts"
git push
```

---

**Ready to share your awesome project with the world!** 🚀
