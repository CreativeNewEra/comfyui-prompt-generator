# Persona System Developer Guide

This guide explains how to create, modify, and maintain personas in the ComfyUI Prompt Generator.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Adding a New Persona](#adding-a-new-persona)
3. [File Structure](#file-structure)
4. [Persona Configuration](#persona-configuration)
5. [Writing System Prompts](#writing-system-prompts)
6. [API Reference](#api-reference)
7. [Testing](#testing)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Components

The persona system consists of four main components:

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Phase 3)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Persona Grid │  │ Chat  │  │ Active Badge │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  API Routes (Flask Backend)                  │
│  GET  /api/personas              List all personas          │
│  GET  /api/personas/<id>         Get persona + prompt       │
│  POST /persona-chat              Non-streaming chat         │
│  POST /persona-chat-stream       Streaming chat (SSE)       │
│  POST /persona-reset             Reset conversation         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Backend Functions                          │
│  load_personas()                 Load personas.json         │
│  load_persona_prompt(id)         Load system prompt         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Storage                              │
│  personas.json                   Persona metadata           │
│  personas/*.txt                  System prompts             │
│  conversation_store              Session management         │
│  prompt_history.db               History tracking           │
└─────────────────────────────────────────────────────────────┘
```

### Flow

1. **Frontend** displays persona grid (Phase 3)
2. **User** selects persona → `GET /api/personas/<id>`
3. **Backend** loads persona metadata and system prompt
4. **User** sends message → `POST /persona-chat-stream`
5. **Backend** injects persona system prompt into conversation
6. **Ollama** generates response with persona personality
7. **Backend** streams response to frontend via SSE
8. **Conversation** saved to session store and history

---

## Adding a New Persona

### Step 1: Create System Prompt File

Create a new file in `personas/` directory:

```bash
touch personas/my_new_persona.txt
```

Write the persona's system prompt (see [Writing System Prompts](#writing-system-prompts) below).

### Step 2: Add Persona to personas.json

Edit `personas.json` and add your persona:

```json
{
  "my_new_persona": {
    "name": "My New Persona",
    "description": "Short description of what this persona does (1-2 sentences)",
    "icon": "🎯",
    "category": "specialized",
    "prompt_file": "my_new_persona.txt",
    "features": [
      "Key feature 1",
      "Key feature 2",
      "Key feature 3"
    ],
    "best_for": "Use case description (who should use this)",
    "supports_presets": true,
    "supports_quick_generate": false,
    "supports_streaming": true
  }
}
```

### Step 3: Test the Persona

```bash
# Start the Flask server
python3 prompt_generator.py

# Test persona loading
curl http://localhost:5000/api/personas/my_new_persona | python3 -m json.tool

# Test persona chat (requires Ollama)
curl -X POST http://localhost:5000/persona-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "persona_id": "my_new_persona"}'
```

### Step 4: Document the Persona

Add your persona to `PERSONAS.md` with:
- Description
- Best for
- Example conversation
- Example output

---

## File Structure

```
comfyui-prompt-generator/
├── personas.json                    # Persona metadata
├── personas/                        # System prompts directory
│   ├── creative_vision_guide.txt
│   ├── technical_engineer.txt
│   ├── art_director.txt
│   ├── photography_expert.txt
│   ├── fantasy_storyteller.txt
│   ├── quick_sketch.txt
│   ├── nsfw_specialist.txt
│   └── my_new_persona.txt          # ← Your new persona
├── prompt_generator.py              # Flask app with persona routes
├── test_persona_api.py              # Test suite
├── PERSONAS.md                      # User documentation
└── PERSONAS_DEVELOPER.md            # This file
```

---

## Persona Configuration

### personas.json Schema

```json
{
  "persona_id": {
    "name": "string",               // Display name (3-30 chars)
    "description": "string",        // User-facing description (50-200 chars)
    "icon": "emoji",                // Single emoji for UI
    "category": "string",           // See categories below
    "prompt_file": "string",        // Filename in personas/ directory
    "features": ["array"],          // 2-5 key features
    "best_for": "string",           // Use case (30-100 chars)
    "supports_presets": boolean,    // Can use style/artist presets?
    "supports_quick_generate": boolean,  // Works with one-shot generation?
    "supports_streaming": boolean   // Supports SSE streaming?
  }
}
```

### Categories

- `beginner` - For new users (simple, guided)
- `advanced` - For power users (technical, complex)
- `professional` - For commercial work (client-focused)
- `specialized` - For specific use cases (photography, etc.)
- `creative` - For narrative/artistic approaches
- `speed` - For rapid iteration
- `adult` - For mature content (NSFW)

### Persona ID Naming Conventions

- Lowercase with underscores: `my_persona_name`
- Descriptive and concise: `fantasy_storyteller` not `fs`
- Avoid special characters or numbers

### Icons

Use a single emoji that represents the persona:
- 🎨 Creative/artistic
- ⚙️ Technical/mechanical
- 🎬 Commercial/media
- 📷 Photography
- 🧙 Fantasy/magical
- ⚡ Speed/energy
- 💋 Sensual/romantic

---

## Writing System Prompts

### Template Structure

```
You are a "[Persona Name]," a [personality adjectives].
Your goal is to [primary objective].
You understand [domain knowledge].
Your method is to [approach].
Your final output is [expected result].

═══════════════════════════════════════════════════════════════════
YOUR CONVERSATIONAL APPROACH
═══════════════════════════════════════════════════════════════════

1.  **[PRINCIPLE 1]:** Description of first principle
2.  **[PRINCIPLE 2]:** Description of second principle
3.  **[PRINCIPLE 3]:** Description of third principle

**Question Examples:**
* "Example question 1?"
* "Example question 2?"

═══════════════════════════════════════════════════════════════════
EXAMPLE CONVERSATION (Your target behavior)
═══════════════════════════════════════════════════════════════════

**User:** "User input example"

**You:** "Your response example"

[Continue example conversation to demonstrate persona behavior]

═══════════════════════════════════════════════════════════════════
HANDLING SPECIAL SITUATIONS
═══════════════════════════════════════════════════════════════════

**If [Situation 1]:**
**You:** "How to respond"

**If [Situation 2]:**
**You:** "How to respond"

═══════════════════════════════════════════════════════════════════
TECHNICAL REFERENCE (Optional)
═══════════════════════════════════════════════════════════════════

[Domain-specific reference material, terminology, frameworks]
```

### Writing Guidelines

**DO:**
- ✅ Be specific about persona personality and approach
- ✅ Provide concrete example conversations
- ✅ Include edge case handling
- ✅ Use clear, structured formatting
- ✅ Specify expected output format
- ✅ Give domain-specific context

**DON'T:**
- ❌ Make prompts too vague or generic
- ❌ Forget to provide example conversations
- ❌ Leave edge cases unhandled
- ❌ Use inconsistent formatting
- ❌ Assume the AI knows domain knowledge

### Tone & Style Guidelines

| Persona Type | Tone | Vocabulary | Sentence Structure |
|--------------|------|------------|-------------------|
| Beginner-Friendly | Warm, encouraging | Simple, accessible | Short, clear |
| Technical | Professional, precise | Technical terms | Structured, detailed |
| Creative | Imaginative, expressive | Evocative, vivid | Flowing, narrative |
| Speed-Focused | Energetic, direct | Concise, punchy | Brief, imperative |

### Testing Your Prompt

1. **Test with Ollama locally:**
   ```bash
   curl -X POST http://localhost:11434/api/generate \
     -d '{"model": "qwen3:latest",
          "prompt": "Your system prompt here\n\nUser: Test message",
          "stream": false}'
   ```

2. **Test edge cases:**
   - Vague user input ("something cool")
   - Very specific user input (technical details)
   - User says "I don't know"
   - User asks persona to choose

3. **Test tone consistency:**
   - Is the persona's personality consistent?
   - Does it match the category (beginner/advanced)?
   - Is the output format what you expected?

---

## API Reference

### GET /api/personas

List all available personas with metadata.

**Response:**
```json
{
  "persona_id": {
    "name": "Persona Name",
    "description": "Description",
    "icon": "🎨",
    "category": "beginner",
    "features": ["Feature 1", "Feature 2"],
    "best_for": "Use case",
    "supports_presets": true,
    "supports_quick_generate": false,
    "supports_streaming": true
  }
}
```

**Status Codes:**
- `200` - Success
- `500` - Server error loading personas

---

### GET /api/personas/&lt;persona_id&gt;

Get specific persona with full system prompt.

**Response:**
```json
{
  "id": "creative_vision_guide",
  "name": "Creative Vision Guide",
  "description": "...",
  "icon": "🎨",
  "category": "beginner",
  "features": [...],
  "best_for": "...",
  "supports_presets": false,
  "supports_quick_generate": false,
  "supports_streaming": true,
  "system_prompt": "You are a Creative Vision Guide..."
}
```

**Status Codes:**
- `200` - Success
- `404` - Persona not found
- `500` - Server error

---

### POST /persona-chat

Generate response using persona (non-streaming).

**Request:**
```json
{
  "message": "User message text",
  "persona_id": "creative_vision_guide",
  "model": "flux",                    // Optional: for presets
  "ollama_model": "qwen3:latest",     // Optional: Ollama model
  "style": "Cinematic",               // Optional: if persona supports presets
  "artist": "Greg Rutkowski",         // Optional
  "composition": "Portrait",          // Optional
  "lighting": "Golden Hour"           // Optional
}
```

**Response:**
```json
{
  "result": "AI response text",
  "persona": "creative_vision_guide"
}
```

**Status Codes:**
- `200` - Success
- `400` - Missing message or persona_id
- `404` - Persona not found
- `503` - Ollama connection failed
- `504` - Ollama timeout
- `502` - Ollama API error

---

### POST /persona-chat-stream

Generate response using persona with streaming (SSE).

**Request:** Same as `/persona-chat`

**Response:** Server-Sent Events stream
```
data: {"token": "Hello"}
data: {"token": " there"}
data: {"token": "!"}
data: {"done": true}
```

**Error Events:**
```
data: {"error": "Error message", "type": "ErrorType"}
```

**Status Codes:**
- `200` - Streaming started
- `400` - Missing message or persona_id
- `404` - Persona not found

---

### POST /persona-reset

Reset persona conversation history.

**Request:** Empty JSON `{}`

**Response:**
```json
{
  "message": "Persona conversation reset"
}
```

**Status Codes:**
- `200` - Success

---

## Testing

### Automated Testing

Run the test suite:

```bash
# Run all persona API tests
python3 test_persona_api.py

# Or use pytest (if configured)
pytest tests/test_persona_*.py
```

### Manual Testing Checklist

**For Each New Persona:**

- [ ] Persona loads without errors
- [ ] System prompt file exists and is readable
- [ ] GET /api/personas returns persona
- [ ] GET /api/personas/&lt;id&gt; returns full data
- [ ] POST /persona-chat works with basic message
- [ ] POST /persona-chat-stream streams correctly
- [ ] Persona personality is consistent
- [ ] Edge cases handled (vague input, "I don't know")
- [ ] Preset support works (if applicable)
- [ ] Conversation history saves correctly

### Testing with Ollama

```bash
# Start Flask server
python3 prompt_generator.py

# Test streaming conversation
curl -N -X POST http://localhost:5000/persona-chat-stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to create an image of a dragon",
    "persona_id": "creative_vision_guide"
  }'

# Test preset support (if applicable)
curl -X POST http://localhost:5000/persona-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Cyberpunk street scene",
    "persona_id": "technical_engineer",
    "style": "Cinematic",
    "lighting": "Neon"
  }'
```

### Testing Without Ollama

If Ollama is not available, you can still test:

- ✅ Persona loading (GET endpoints)
- ✅ Validation (POST with missing fields)
- ✅ Error handling (invalid persona_id)
- ❌ Actual conversation (requires Ollama)

---

## Best Practices

### System Prompt Design

1. **Be Specific About Behavior**
   - ✅ "Ask one or two questions at a time"
   - ❌ "Be helpful"

2. **Provide Examples**
   - Include 2-3 full conversation examples
   - Show edge case handling
   - Demonstrate expected output format

3. **Define Boundaries**
   - What the persona does
   - What the persona doesn't do
   - How to handle "I don't know"

4. **Use Structure**
   - Clear sections with headers
   - Numbered principles
   - Formatted examples

5. **Test Iteratively**
   - Start simple, add complexity
   - Test with real Ollama models
   - Refine based on actual behavior

### Persona Design

1. **Solve a Specific Problem**
   - Don't create personas that overlap
   - Each should serve a distinct use case
   - Clear target audience

2. **Balance Complexity**
   - Too simple = not useful
   - Too complex = confusing
   - Find the sweet spot for target users

3. **Consider Workflow**
   - How many exchanges before useful output?
   - Does it support iteration?
   - Can users switch mid-task?

4. **Maintain Consistency**
   - Tone should match throughout
   - Terminology should be consistent
   - Output format should be predictable

### Code Style

1. **Follow Existing Patterns**
   - Use same JSON structure
   - Follow naming conventions
   - Match error handling style

2. **Document Everything**
   - Add persona to PERSONAS.md
   - Include docstrings
   - Write clear commit messages

3. **Test Thoroughly**
   - Run automated tests
   - Manual testing with Ollama
   - Edge case validation

---

## Troubleshooting

### Persona Not Loading

**Problem:** GET /api/personas/my_persona returns 404

**Solutions:**
1. Check persona_id matches exactly (case-sensitive)
2. Verify entry exists in personas.json
3. Validate JSON syntax: `python3 -m json.tool personas.json`
4. Check Flask logs for errors

### System Prompt Not Found

**Problem:** GET /api/personas/my_persona has empty system_prompt

**Solutions:**
1. Check prompt_file path in personas.json
2. Verify file exists: `ls personas/my_persona.txt`
3. Check file permissions: `chmod 644 personas/my_persona.txt`
4. Check for typos in filename

### Persona Behaves Inconsistently

**Problem:** Ollama doesn't follow persona instructions

**Solutions:**
1. Make system prompt more explicit
2. Add more example conversations
3. Test with different Ollama models (some follow instructions better)
4. Increase prompt specificity
5. Add negative examples ("Don't do X")

### Presets Not Working

**Problem:** Presets not being applied to persona

**Solutions:**
1. Check `supports_presets: true` in personas.json
2. Verify preset values being sent in request
3. Check logs for preset application
4. Test with legacy presets first (simpler)

### Streaming Issues

**Problem:** POST /persona-chat-stream not streaming

**Solutions:**
1. Check `supports_streaming: true`
2. Verify SSE headers in response
3. Test with curl -N flag
4. Check Ollama streaming support
5. Review Flask logs for generator errors

### Session Not Persisting

**Problem:** Conversation resets unexpectedly

**Solutions:**
1. Check Flask secret key is set
2. Verify session cookies are being sent
3. Check conversation_store database
4. Test /persona-reset isn't being called
5. Verify persona_id stays consistent

---

## Advanced Topics

### Creating Persona Variants

You can create variants of existing personas:

```json
{
  "technical_engineer_beginner": {
    "name": "Technical Engineer (Beginner)",
    "description": "Simplified version with explanations",
    "prompt_file": "technical_engineer_beginner.txt",
    "category": "advanced",
    ...
  }
}
```

### Dynamic Persona Loading

For advanced use cases, you can create personas that:
- Load additional context from files
- Adjust behavior based on user history
- Combine multiple persona traits

### Multi-Language Support

To add multi-language persona support:
1. Create language-specific prompt files: `creative_vision_guide_es.txt`
2. Add language field to personas.json
3. Modify `load_persona_prompt()` to check user language preference
4. Update frontend to show language selector

### Persona Analytics

Track persona usage:
```python
# In persona-chat route, add:
persona_analytics.increment(persona_id)
persona_analytics.track_success(persona_id, user_satisfaction)
```

---

## Contributing

### Submitting New Personas

1. Create persona files (JSON entry + prompt file)
2. Test thoroughly with Ollama
3. Document in PERSONAS.md
4. Submit PR with:
   - Persona files
   - Documentation updates
   - Test results
   - Example conversations

### Code Review Checklist

- [ ] JSON syntax valid
- [ ] Prompt file properly formatted
- [ ] All required fields present
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Example conversations provided
- [ ] Tested with Ollama

---

## Resources

- **Flask Documentation:** https://flask.palletsprojects.com/
- **Ollama API Reference:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **Server-Sent Events:** https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
- **Prompt Engineering Guide:** https://www.promptingguide.ai/

---

## Version History

**v1.0.0** (2025-01-26)
- Initial persona system implementation
- 7 built-in personas
- API routes complete
- Session management
- Streaming support

---

## Support

For bugs, feature requests, or questions:
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Tag with `persona-system` label
- Include persona_id, error logs, and expected behavior

**Version:** 1.0.0
**Last Updated:** 2025-01-26
