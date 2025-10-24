# Contributing to ComfyUI Prompt Generator

First off, thank you for considering contributing to ComfyUI Prompt Generator! It's people like you that make this tool better for everyone.

## 🎯 Ways to Contribute

### 1. 🐛 Report Bugs
Found a bug? Please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, Ollama version)
- Screenshots if applicable

### 2. 💡 Suggest Features
Have an idea? Open an issue with:
- Clear description of the feature
- Why it would be useful
- How it might work
- Examples if applicable

### 3. 📝 Improve Documentation
Help make the docs better:
- Fix typos or unclear instructions
- Add examples
- Improve README
- Create tutorials

### 4. 💻 Submit Code
Want to add features or fix bugs:
- Fork the repository
- Create a feature branch
- Make your changes
- Submit a pull request

## 🚀 Development Setup

1. Fork and clone the repository
```bash
git clone https://github.com/yourusername/comfyui-prompt-generator.git
cd comfyui-prompt-generator
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create a feature branch
```bash
git checkout -b feature/your-feature-name
```

## 📋 Code Style Guidelines

### Python Code
- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small
- Comment complex logic

Example:
```python
def generate_prompt(user_input, presets):
    """
    Generate a detailed prompt from user input and presets.
    
    Args:
        user_input (str): The user's image description
        presets (dict): Selected preset options
        
    Returns:
        str: Generated detailed prompt
    """
    # Implementation here
    pass
```

### HTML/CSS/JavaScript
- Use semantic HTML5 elements
- Keep CSS organized and commented
- Use meaningful class names
- Comment complex JavaScript logic
- Ensure responsive design

## 🧪 Testing

Before submitting a PR:

1. Test your changes thoroughly
2. Test on different browsers if UI changes
3. Ensure no console errors
4. Test with different Ollama models
5. Verify both Quick Generate and Chat modes work

## 📤 Pull Request Process

1. **Update Documentation**: If you add features, update README.md

2. **Write Clear Commit Messages**:
   ```
   Add feature: Brief description
   
   More detailed explanation of what changed and why.
   Fixes #issue_number
   ```

3. **Create Pull Request**:
   - Clear title describing the change
   - Description of what changed and why
   - Reference any related issues
   - Include screenshots for UI changes

4. **Address Review Feedback**: Be responsive to comments and suggestions

## 🎨 Adding New Presets

To add new presets, edit the `PRESETS` dictionary in `prompt_generator.py`:

```python
PRESETS = {
    "styles": {
        "Your New Style": "style description, tags, keywords",
        # ...
    },
    "artists": {
        "Artist Name": "in the style of Artist Name, characteristics",
        # ...
    },
    # ... other categories
}
```

Guidelines for presets:
- Keep descriptions concise but descriptive
- Test with both Flux and SDXL
- Ensure they integrate well with existing presets
- Add to the appropriate category

## 🔧 Architecture Overview

```
comfyui-prompt-generator/
├── prompt_generator.py    # Flask backend
├── templates/
│   └── index.html         # Frontend UI
├── requirements.txt       # Python dependencies
└── README.md             # Documentation
```

### Key Components

**Backend (prompt_generator.py)**:
- Flask routes for API endpoints
- Ollama API integration
- Session management for chat mode
- Preset system

**Frontend (index.html)**:
- Single-page application
- Mode switching (Quick/Chat)
- Model selection
- Preset dropdowns
- Real-time updates

## 🐛 Debugging Tips

1. **Backend Issues**: Check Flask console for errors
2. **Frontend Issues**: Check browser console (F12)
3. **Ollama Connection**: Verify with `curl http://localhost:11434`
4. **Session Issues**: Clear browser cookies

## ❓ Questions?

Feel free to:
- Open an issue for discussion
- Ask in existing issues
- Check closed issues for similar questions

## 📜 Code of Conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on what's best for the community
- Show empathy towards others

## 🎉 Recognition

Contributors will be recognized in the README and release notes!

---

Thank you for contributing! 🙏
