# Personas - AI Conversation Styles for Prompt Generation

## What Are Personas?

Personas are different AI conversation styles designed to help you create image prompts in different ways. Instead of using dropdown menus with 80+ presets, you can have a natural conversation with an AI personality that guides you through creating your image idea.

Think of personas as different creative partners, each with their own approach:

- **Beginners** get patient, step-by-step guidance
- **Power users** get technical control with weights and syntax
- **Professionals** get commercial-focused creative direction
- **Storytellers** get narrative-rich world-building

---

## Available Personas

### 🎨 Creative Vision Guide
**Best for:** Beginners, vague ideas, creative exploration

**What it does:**
Patiently builds your image idea step-by-step through simple questions. Perfect if you feel overwhelmed by too many choices or just have a vague idea like "something with a dragon."

**Approach:**
- Asks one or two questions at a time
- Summarizes the scene as you build it together
- Never presents multiple options (builds, doesn't list)
- Warm and encouraging tone

**Example Conversation:**
```
You: "I want to make a picture of a cat."
Persona: "A cat! A perfect subject. To get us started, where is this cat?
          Are we imagining them cozy indoors, or outside exploring?"

You: "Indoors."
Persona: "Great, a cozy indoor scene. What's the cat doing? Are they
          peacefully sleeping, or maybe staring intently out a window?"
```

**Output:** Final scene description (not a technical prompt)

---

### ⚙️ Technical Prompt Engineer
**Best for:** Power users, specific technical requirements, fine-tuned control

**What it does:**
Gives you advanced technical control with prompt weights, emphasis syntax, and quality tags. For users who want precise control over generation parameters.

**Approach:**
- Asks about negative prompts, quality tags, CFG scale
- Uses technical syntax: `(concept:1.2)` for 20% boost
- Explains why certain weights are recommended
- Provides comprehensive negative prompts

**Example Output:**
```
POSITIVE PROMPT:
(masterpiece:1.3), (best quality:1.2), ((cyberpunk female character:1.3)),
standing in neon-lit street, detailed face, perfect anatomy,
(futuristic clothing:1.1), dramatic lighting, 8k, HDR

NEGATIVE PROMPT:
(low quality:1.2), (blurry:1.3), (extra limbs:1.4), (bad anatomy:1.3),
mutation, deformed, disfigured
```

**Supports Presets:** Yes
**Supports Quick Generate:** Yes

---

### 🎬 Art Director
**Best for:** Designers, marketers, professional projects, client work

**What it does:**
Thinks about images in terms of use case, target audience, and commercial viability. Creates professional creative briefs before generating prompts.

**Approach:**
- Asks about use case (social media, website, print, portfolio)
- Considers target audience and brand consistency
- Provides creative brief + optimized prompt
- Tailors output for specific platforms (Instagram, LinkedIn, print)

**Example Output:**
```
CREATIVE BRIEF
Project: Instagram announcement for new coffee shop location
Objective: Drive immediate foot traffic by showcasing work-friendly atmosphere
Target Audience: Young professionals (25-35), remote workers

VISUAL STRATEGY:
- Show laptop-friendly setup (hint at WiFi/remote work)
- Balance industrial (exposed brick) with warmth (Edison bulbs)
- Instagram-optimized composition (1:1 or 4:5)
- Natural window light + warm artificial lighting

OPTIMIZED PROMPT:
Professional photograph of modern industrial coffee shop interior...
```

**Supports Presets:** Yes
**Supports Quick Generate:** No (needs strategic discussion first)

---

### 📷 Photography Expert
**Best for:** Photorealistic renders, photography enthusiasts, technical accuracy

**What it does:**
Uses real camera terminology (focal length, aperture, ISO, lens type) to create photorealistic prompts. Perfect for photography enthusiasts.

**Approach:**
- Asks about camera body, lens choice, and settings
- Discusses lighting setups (Rembrandt, butterfly, split lighting)
- Provides technical camera specifications
- Explains how each setting affects the image

**Example Output:**
```
CAMERA SPECIFICATIONS:
Camera: Full-frame DSLR (Canon 5D Mark IV)
Lens: 85mm f/1.4
Aperture: f/1.8 (balance between bokeh and sharpness)
ISO: 200 (clean image in golden hour light)
Shutter speed: 1/250s

PHOTOGRAPHIC PROMPT:
Professional portrait photograph of a woman, golden hour natural lighting,
shot on Canon 5D Mark IV with 85mm f/1.4 lens at f/1.8 aperture,
shallow depth of field, creamy bokeh background...
```

**Supports Presets:** Yes
**Supports Quick Generate:** Yes

---

### 🧙 Fantasy Storyteller
**Best for:** Character art, book covers, RPG content, fantasy/sci-fi

**What it does:**
Creates narrative-rich images with character backstory, world context, and lore. Every image tells a story.

**Approach:**
- Asks about character motivation, personality, backstory
- Builds world context and establishes stakes
- Adds narrative-rich details that hint at larger stories
- Provides both narrative description and visual prompt

**Example Output:**
```
NARRATIVE DESCRIPTION:
An elderly wizard, weathered by grief and obsession, hunches over an ancient
tome in a long-abandoned library. His eyes, wild with desperate hope, scan
glowing necromantic runes that pulse with forbidden power. The shadows move
unnaturally—no longer mere absence of light, but entities drawn to the dark
magic being awakened.

THE STAKES:
He seeks to resurrect the one person he couldn't save, but in doing so, may
unleash something far worse than death.

VISUAL PROMPT:
Cinematic fantasy illustration of an elderly wizard with wild gray hair,
hunched over ancient tome in abandoned library, glowing necromantic runes
casting eerie green light on desperate face, spectral energy coiling around
fingers, unnatural shadows moving on walls...
```

**Supports Presets:** No (narrative-focused, not technical)
**Supports Quick Generate:** No (needs story context)

---

### ⚡ Quick Sketch Assistant
**Best for:** Rapid prototyping, A/B testing, brainstorming, speed experiments

**What it does:**
Maximum 2-3 quick questions, then generates immediately. Speed over perfection. Uses "yes, and..." improv style.

**Approach:**
- Asks MAX 2-3 rapid-fire questions
- Makes smart assumptions to fill in blanks
- No long explanations or discussions
- Immediate generation (under 30 seconds)

**Example Conversation:**
```
You: "Dragon"
Persona: "Dragon! Realistic or fantasy-stylized? And epic battle scene or majestic portrait?"

You: "Fantasy, majestic"
Persona: "Got it! Generating:

Majestic fantasy dragon, perched on mountain peak, wings spread wide,
scales shimmering with iridescent colors, golden sunset lighting...

Quick iterations: Want it darker/moodier? More colorful? In flight instead?"
```

**Supports Presets:** Optional (can be added but not required)
**Supports Quick Generate:** Yes

---

### 💋 NSFW/Boudoir Specialist
**Best for:** Adult content creators, artistic nude photography, boudoir sessions

**What it does:**
Professional approach to tasteful adult content with artistic focus. Emphasizes lighting, posing, and mood like high-end boudoir photographers.

**Approach:**
- Artistic merit first (lighting, composition, emotion)
- Professional tone (like fashion/boudoir photographer)
- Focuses on empowerment, not objectification
- Emphasizes taste: shadows, silhouettes, implied rather than explicit

**Example Output:**
```
CREATIVE DIRECTION
Mood: Soft, romantic, intimate
Style: Natural light boudoir, editorial elegance

LIGHTING SETUP:
- Primary: Large bedroom window with sheer white curtains
- Time: Late morning (soft, flattering)
- Direction: 45° side angle (sculptural, feminine)

PHOTOGRAPHIC PROMPT:
Professional boudoir photography, woman in silk lingerie with flowing robe
draped off shoulder, soft natural morning light through sheer curtains,
dreamy romantic atmosphere, elegant posing, tasteful and elegant,
fine art boudoir photography...
```

**Supports Presets:** Yes (uses NSFW presets from hierarchical system)
**Supports Quick Generate:** Yes

---

## How to Choose a Persona

### I'm new to AI image generation
→ **🎨 Creative Vision Guide** - Patient step-by-step guidance

### I know exactly what I want, technically
→ **⚙️ Technical Prompt Engineer** - Precise control with weights

### I'm creating for a client or professional project
→ **🎬 Art Director** - Strategic creative direction

### I want photorealistic images
→ **📷 Photography Expert** - Real camera specifications

### I'm creating fantasy/sci-fi character art
→ **🧙 Fantasy Storyteller** - Narrative-rich world-building

### I need to test ideas quickly
→ **⚡ Quick Sketch Assistant** - Rapid iteration

### I'm creating tasteful adult content
→ **💋 NSFW/Boudoir Specialist** - Professional artistic approach

---

## Using Personas (Once Frontend is Built)

**Step 1: Choose Your Persona**
Select from the persona grid based on your needs and experience level.

**Step 2: Start Conversation**
Send your initial idea or let the persona guide you with questions.

**Step 3: Refine Together**
Have a back-and-forth conversation to perfect your image concept.

**Step 4: Generate**
Use the final prompt in ComfyUI for image generation.

**Step 5: Switch if Needed**
Not working? Switch to a different persona approach.

---

## Persona Features Comparison

| Feature | Creative Vision | Technical | Art Director | Photography | Fantasy | Quick Sketch | NSFW |
|---------|----------------|-----------|--------------|-------------|---------|--------------|------|
| Beginner-Friendly | ✅ | ❌ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ |
| Guided Questions | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| Technical Control | ❌ | ✅ | ⚠️ | ✅ | ❌ | ❌ | ⚠️ |
| Preset Support | ❌ | ✅ | ✅ | ✅ | ❌ | ⚠️ | ✅ |
| Speed | Slow | Medium | Slow | Medium | Slow | Fast | Medium |
| Conversational Style | Warm | Professional | Confident | Technical | Imaginative | Energetic | Respectful |
| Output Type | Scene Description | Technical Prompt | Brief + Prompt | Camera Specs + Prompt | Narrative + Prompt | Quick Prompt | Setup + Prompt |

---

## Tips for Best Results

### General Tips
- **Be specific when you can** - "A cyberpunk city at night" vs. "something cool"
- **Let personas guide you** - They're designed to ask the right questions
- **Iterate freely** - Switch personas if one approach isn't working
- **Save good conversations** - History is tracked for reference

### Persona-Specific Tips

**Creative Vision Guide:**
- Start with even vague ideas ("something magical")
- Answer questions simply and honestly
- Don't worry about technical terminology

**Technical Engineer:**
- Mention if you have specific weight requirements
- Ask about negative prompts if quality issues occur
- Specify your target CFG scale if you know it

**Art Director:**
- Clearly state your use case (Instagram, print, website)
- Mention target audience demographics
- Be open about brand guidelines or constraints

**Photography Expert:**
- Mention preferred camera brand if you have one
- Specify desired depth of field (shallow/deep)
- Ask about specific lighting setups by name

**Fantasy Storyteller:**
- Provide character backstory if you have one
- Mention the "moment" being captured
- Share world-building context

**Quick Sketch:**
- Keep answers short and fast
- Use rapid iterations ("darker", "more colorful")
- Don't overthink - just iterate

**NSFW Specialist:**
- Clearly state artistic intent
- Mention comfort level with sensuality
- Ask for specific lighting moods

---

## Technical Details

### API Endpoints
- `GET /api/personas` - List all available personas
- `GET /api/personas/<id>` - Get specific persona details
- `POST /persona-chat` - Non-streaming conversation
- `POST /persona-chat-stream` - Streaming conversation (recommended)
- `POST /persona-reset` - Reset conversation history

### Session Management
- Conversations are saved per-persona
- Switching personas resets the conversation
- History limited to 20 exchanges (same as regular chat)

### Compatibility
- Works with both Flux and SDXL models
- Supports legacy presets (for compatible personas)
- Supports hierarchical presets (for compatible personas)
- All conversations saved to history database

---

## Frequently Asked Questions

**Q: Can I switch personas mid-conversation?**
A: Yes! Switching personas will reset the conversation and start fresh with the new personality.

**Q: Do personas work without presets?**
A: Yes! Creative Vision Guide and Fantasy Storyteller work purely conversationally without needing presets.

**Q: Which persona is best for beginners?**
A: Creative Vision Guide is specifically designed for beginners and those overwhelmed by choices.

**Q: Can I use presets with personas?**
A: Some personas support presets (Technical Engineer, Art Director, Photography Expert, NSFW Specialist), others don't need them.

**Q: Are conversations saved?**
A: Yes, all conversations are saved to the history database with persona metadata.

**Q: Can I create my own persona?**
A: Yes! See PERSONAS_DEVELOPER.md for instructions on creating custom personas.

**Q: Does streaming work with all personas?**
A: Yes, all personas support real-time streaming for a more interactive experience.

**Q: Is the NSFW Specialist safe for work?**
A: The persona itself is professional, but the content it helps create is adult-oriented. Use discretion.

---

## What's Next?

**Current Status:** Backend complete (Phase 1 & 2)
**Coming Soon:** Frontend UI (Phase 3)

Once the frontend is built, you'll be able to:
- Choose personas from a visual card grid
- See active persona indicator during chat
- Switch personas with one click
- View scene summaries for guided personas

---

## Feedback & Contributing

Have ideas for new personas? Found a bug? Want to improve existing personas?

- Report issues: [GitHub Issues](https://github.com/anthropics/claude-code/issues)
- Suggest personas: Open an issue with "Persona Suggestion:" prefix
- Contribute: See PERSONAS_DEVELOPER.md for development guide

---

## Credits

Persona system designed and implemented for ComfyUI Prompt Generator.
Original idea inspired by conversational AI assistants with specialized personalities.

**Version:** 1.0.0
**Last Updated:** 2025-01-26
