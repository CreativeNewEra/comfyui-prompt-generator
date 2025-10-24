# 📝 Prompt Examples Guide

This guide demonstrates how to use the ComfyUI Prompt Generator effectively with real-world examples. Learn what good prompts look like and how different presets affect the output.

## Table of Contents

- [Quick Generate Examples](#quick-generate-examples)
  - [Flux Model Examples](#flux-model-examples)
  - [SDXL Model Examples](#sdxl-model-examples)
- [Preset Combinations](#preset-combinations)
- [Chat & Refine Examples](#chat--refine-examples)
- [Art Style Tips](#art-style-tips)
- [Best Practices](#best-practices)

---

## Quick Generate Examples

### Flux Model Examples

Flux models work best with **natural language descriptions** and don't need quality tags or negative prompts.

#### Example 1: Simple Portrait Enhancement

**Model:** Flux Dev
**Presets:** None
**Input:**
```
a woman with red hair
```

**Output:**
```
PROMPT: A woman with vibrant red hair cascading in loose waves over her shoulders,
her porcelain skin illuminated by soft natural light. Her striking green eyes gaze
thoughtfully into the distance, framed by delicate features and a subtle, enigmatic
smile. The rich copper tones of her hair catch highlights, creating depth and movement
throughout the frame.
```

**Why it works:** Even a simple input gets expanded with lighting details, specific color descriptions, and emotional tone.

---

#### Example 2: Fantasy Scene with Presets

**Model:** Flux Dev
**Presets:**
- Style: Fantasy Art
- Lighting: Volumetric Lighting
- Composition: Low Angle

**Input:**
```
a wizard casting a spell in ancient ruins
```

**Output:**
```
PROMPT: A powerful wizard stands amid crumbling ancient stone ruins, robes billowing
dramatically as arcane energy spirals from his outstretched hands. Shot from a low angle
looking upward, emphasizing his commanding presence against a twilight sky. Volumetric
rays of mystical light pierce through broken archways, illuminating floating runes and
dust particles in the air. The scene is steeped in fantasy art aesthetics with ethereal
blues and purples mixing with warm amber glows from magical energy. Intricate carvings
on weathered pillars frame the composition, while swirling mist adds atmospheric depth
to this epic magical moment.
```

**Why it works:** The presets guide the AI to incorporate specific visual elements (low angle for drama, volumetric lighting for atmosphere) while maintaining natural language flow.

---

#### Example 3: Cyberpunk Character

**Model:** Flux Dev
**Presets:**
- Style: Cyberpunk
- Artist: Simon Stålenhag
- Lighting: Neon Lighting
- Composition: Medium Shot

**Input:**
```
street vendor in a futuristic night market
```

**Output:**
```
PROMPT: A weathered street vendor operates a cluttered noodle cart in a rain-slicked
futuristic night market, captured in a medium shot that shows them from the waist up
amid their makeshift stall. Vibrant neon signs in multiple languages cast electric blues,
hot pinks, and acid greens across wet surfaces, reflecting off puddles and chrome fixtures.
The scene evokes Simon Stålenhag's distinctive blend of the mundane and technological,
with holographic menu displays flickering beside traditional cooking equipment. Steam
rises from bubbling pots, diffusing through the neon glow while cables and pipes snake
overhead through the dystopian urban sprawl. The vendor's augmented reality visor flickers
with transaction data as they serve customers in this gritty cyberpunk setting.
```

**Why it works:** Multiple presets combine to create a cohesive vision - cyberpunk aesthetic + specific artist style + neon lighting + proper framing all work together naturally.

---

#### Example 4: Nature Photography

**Model:** Flux Dev
**Presets:**
- Artist: Ansel Adams
- Composition: Landscape
- Lighting: Golden Hour

**Input:**
```
mountain lake reflection
```

**Output:**
```
PROMPT: A pristine mountain lake captures a perfect mirror reflection of snow-capped
peaks in the style of Ansel Adams' iconic landscape photography. Golden hour sunlight
bathes the scene in warm amber tones, highlighting textured rock formations in the
foreground while casting long shadows across the valley. The landscape composition
emphasizes the sweeping grandeur of nature, with the lake serving as the calm centerpiece
dividing earth and sky. Sharp detail throughout the frame reveals every ripple on the
water's surface, every pine tree on distant slopes, and every cloud formation in the
dramatic sky. The photograph balances light and shadow with masterful precision, creating
depth through careful tonal gradation from the bright peaks to darker foreground elements.
```

**Why it works:** Combining a photography-specific artist (Ansel Adams) with appropriate composition and lighting creates authentic photographic language and technical details.

---

### SDXL Model Examples

SDXL (Stable Diffusion XL) works best with **quality tags** and benefits from **negative prompts** to avoid unwanted elements.

#### Example 5: Character Portrait for SDXL

**Model:** SDXL (Juggernaut)
**Presets:**
- Style: Photorealistic
- Composition: Portrait
- Lighting: Studio Lighting

**Input:**
```
elderly man with beard
```

**Output:**
```
PROMPT: elderly man with distinguished white beard, portrait composition, photorealistic,
highly detailed skin texture, professional studio lighting with three point setup, sharp
focus on eyes, weathered facial features, expressive wrinkles, 8k uhd, dslr quality,
masterpiece, best quality, centered subject, detailed hair strands, life experience in
eyes, dramatic but flattering illumination

NEGATIVE: blurry, low quality, poorly drawn, deformed, disfigured, bad anatomy, ugly,
extra limbs, poorly lit, overexposed, underexposed, amateur, low resolution, jpeg artifacts,
watermark, signature
```

**Why it works:** SDXL prompt includes specific quality tags (8k uhd, masterpiece) and technical photography terms. The negative prompt prevents common SDXL issues.

---

#### Example 6: Sci-Fi Environment for SDXL

**Model:** SDXL (Juggernaut)
**Presets:**
- Style: 3D Render
- Composition: Wide Shot
- Lighting: Volumetric Lighting

**Input:**
```
spaceship interior corridor
```

**Output:**
```
PROMPT: futuristic spaceship interior corridor, wide shot establishing view, 3d render,
octane render, unreal engine, ray tracing, volumetric lighting with god rays, detailed
metal panels and technical details, glowing control panels, atmospheric fog, pristine
white and blue color scheme, highly detailed, sharp focus, 8k quality, masterpiece,
best quality, photorealistic materials, advanced technology, clean modern design,
dramatic perspective

NEGATIVE: blurry, low quality, poorly rendered, grainy, artifacts, low poly, simple,
cartoon, anime, deformed geometry, bad proportions, cluttered, messy, dark, underexposed,
flat lighting
```

**Why it works:** Technical render terms (octane, unreal engine, ray tracing) signal to SDXL you want high-quality CGI aesthetic. Negative prompt avoids stylistic conflicts.

---

#### Example 7: Artistic Portrait with Style Mix

**Model:** SDXL (Juggernaut)
**Presets:**
- Style: Oil Painting
- Artist: Alphonse Mucha
- Composition: Portrait
- Lighting: Soft Diffused

**Input:**
```
woman with flowing dress
```

**Output:**
```
PROMPT: beautiful woman in flowing Art Nouveau dress, in the style of Alphonse Mucha,
art nouveau aesthetic, portrait composition, oil painting style with visible brushstrokes,
traditional art, painterly technique, soft diffused lighting creating gentle shadows,
ornate decorative elements, floral motifs, elegant flowing lines, pastel color palette,
masterpiece, best quality, highly detailed fabric textures, romantic atmosphere,
ethereal beauty, centered subject, flattering illumination

NEGATIVE: photorealistic, modern, digital art, 3d render, blurry, low quality, poorly
drawn, bad anatomy, deformed, simple, cartoon, harsh lighting, dark, oversaturated,
watermark, signature
```

**Why it works:** Combines specific artist style with appropriate medium (oil painting) and compatible lighting. Negative prompt excludes conflicting styles like photorealism.

---

#### Example 8: Action Scene

**Model:** SDXL (Juggernaut)
**Presets:**
- Style: Cinematic
- Composition: Dutch Angle
- Lighting: Dramatic Shadows

**Input:**
```
ninja jumping between buildings
```

**Output:**
```
PROMPT: dynamic ninja leaping between rooftop buildings at night, dutch angle tilted
composition creating tension, cinematic film still, dramatic shadows with high contrast
chiaroscuro lighting, motion blur on limbs suggesting speed, detailed black tactical
outfit, moonlight rim lighting, urban environment, masterpiece, best quality, highly
detailed, sharp focus on face, movie-quality action scene, 8k uhd, film grain texture,
atmospheric fog, depth of field

NEGATIVE: blurry, static pose, boring composition, low quality, poorly drawn anatomy,
deformed limbs, bad proportions, flat lighting, overexposed, cartoon, amateur, simple
background, watermark
```

**Why it works:** Cinematic style + dutch angle + dramatic lighting creates intense action movie aesthetic. Motion blur and compositional tilt add dynamism.

---

## Preset Combinations

Here are proven preset combinations for specific artistic goals:

### Combination 1: Epic Fantasy Landscape

**Best for:** Grand, atmospheric environment art

- **Style:** Fantasy Art
- **Composition:** Landscape or Wide Shot
- **Lighting:** Volumetric Lighting or Golden Hour
- **Artist:** Greg Rutkowski or James Gurney

**Example output focus:** Sweeping vistas, magical lighting, detailed environments

---

### Combination 2: Moody Portrait Photography

**Best for:** Emotional character portraits

- **Style:** Photorealistic
- **Composition:** Portrait or Close-up
- **Lighting:** Natural Window Light or Dramatic Shadows
- **Artist:** Annie Leibovitz or Peter Lindbergh

**Example output focus:** Realistic skin texture, emotional depth, professional photography look

---

### Combination 3: Retro Synthwave Aesthetic

**Best for:** 80s-inspired neon artwork

- **Style:** Cyberpunk or Digital Art
- **Composition:** Symmetrical or Rule of Thirds
- **Lighting:** Neon Lighting or Blue Hour
- **Artist:** Simon Stålenhag

**Example output focus:** Vibrant colors, retro-futuristic elements, nostalgic atmosphere

---

### Combination 4: Classical Fine Art

**Best for:** Traditional painting style

- **Style:** Oil Painting or Watercolor
- **Composition:** Golden Ratio or Frame within Frame
- **Lighting:** Soft Diffused or Natural Window Light
- **Artist:** Alphonse Mucha or traditional artists

**Example output focus:** Traditional medium characteristics, classical composition, timeless quality

---

### Combination 5: Hyperrealistic Studio Shot

**Best for:** Product or fashion photography

- **Style:** Photorealistic or 3D Render
- **Composition:** Medium Shot or Close-up
- **Lighting:** Studio Lighting
- **Artist:** Irving Penn or Annie Leibovitz

**Example output focus:** Perfect lighting control, commercial quality, sharp detail

---

### Combination 6: Dreamlike Surrealism

**Best for:** Abstract, imaginative scenes

- **Style:** Surreal
- **Composition:** Dutch Angle or Extreme Close-up
- **Lighting:** Volumetric Lighting or Moonlight
- **Artist:** Zdzisław Beksiński or H.R. Giger

**Example output focus:** Unusual perspectives, otherworldly atmosphere, imaginative elements

---

## Chat & Refine Examples

Chat mode allows iterative refinement. Here's how conversations typically flow:

### Conversation Example 1: Building a Scene

**Model:** Flux Dev
**Mode:** Chat & Refine

```
👤 User: I want a cozy coffee shop

🤖 Assistant: PROMPT: A warm, inviting coffee shop interior with soft amber lighting
from vintage Edison bulbs hanging overhead. Rustic wooden tables and mismatched chairs
create an eclectic charm, while potted plants add touches of green throughout the space.
A gleaming espresso machine sits on a weathered brick counter, steam rising from freshly
brewed coffee. Shelves lined with books and ceramic mugs fill the walls, and large
windows reveal a quiet street outside. The atmosphere is cozy and intimate, perfect
for reading or quiet conversation.

👤 User: Make it rainy outside and add more atmosphere

🤖 Assistant: PROMPT: A warm, inviting coffee shop interior while rain streams down
the large windows, creating a cozy refuge from the weather outside. Soft amber lighting
from vintage Edison bulbs casts a golden glow that reflects off the rain-streaked glass.
Water droplets race down the windowpanes, slightly blurring the view of the wet,
lamp-lit street beyond. Inside, rustic wooden tables and mismatched chairs create
eclectic charm, while potted plants add life to the space. The gleaming espresso machine
hisses and steams at the weathered brick counter, adding to the atmospheric ambiance.
Shelves lined with well-worn books and ceramic mugs create a lived-in feel. The sound
of rain on the roof and the aroma of fresh coffee create a deeply peaceful, hygge
atmosphere perfect for spending a rainy afternoon.

👤 User: Perfect! Add a person reading by the window

🤖 Assistant: PROMPT: A warm, inviting coffee shop interior while rain streams down
the large windows, with a solitary figure seated at a small table beside the glass,
absorbed in a book. The reader is illuminated by a combination of soft amber light
from vintage Edison bulbs overhead and the cool grey daylight filtering through the
rain-streaked windows, creating a beautiful contrast on their face and the pages before
them. A steaming cup of coffee sits beside their book on the worn wooden table. Rain
droplets race down the windowpanes, slightly blurring the view of the wet, lamp-lit
street beyond while the person remains contentedly dry inside this cozy refuge. The
gleaming espresso machine hisses softly at the weathered brick counter in the background.
Potted plants and shelves of well-worn books create a lived-in, literary atmosphere.
The scene captures that perfect rainy day moment of peaceful solitude, warmth, and the
simple pleasure of reading in a coffee shop while the world goes by outside.
```

**Why it works:** Each message builds on the previous, adding layers of detail while maintaining consistency. The AI remembers earlier elements and integrates new requests seamlessly.

---

### Conversation Example 2: Style Exploration

**Model:** SDXL (Juggernaut)
**Mode:** Chat & Refine
**Presets:** Experimenting with different combinations

```
👤 User: A dragon on a mountaintop

🤖 Assistant: PROMPT: majestic dragon perched on rocky mountain peak, wings spread wide,
detailed scales, fantasy art, dramatic cloudy sky, highly detailed, sharp focus,
masterpiece, best quality, epic scene, 8k quality

NEGATIVE: blurry, low quality, cartoon, simple, poorly drawn, bad anatomy, deformed

👤 User: Make it more like a cinematic movie scene

[User changes preset: Style → Cinematic]

🤖 Assistant: PROMPT: massive dragon perched on windswept mountain peak, cinematic
film still, dramatic composition, movie quality, wings partially spread revealing
intricate wing membrane details, cinematic lighting with volumetric fog, detailed
realistic scales catching dramatic light, film grain texture, anamorphic lens aesthetic,
epic scale, highly detailed, masterpiece, best quality, sharp focus, 8k uhd, moody
atmosphere, storm clouds gathering

NEGATIVE: blurry, low quality, cartoon, anime, simple, poorly drawn, bad anatomy,
deformed, flat lighting, overexposed, amateur, low resolution

👤 User: What if we made it look like a Sebastião Salgado photograph? Black and white, documentary style

[User changes presets: Style → Photorealistic, Artist → Sebastião Salgado]

🤖 Assistant: PROMPT: powerful dragon resting on remote mountain summit, Sebastião
Salgado black and white photography style, documentary photography aesthetic, dramatic
monochrome with rich tonal range, deep blacks and luminous highlights, film photography
grain structure, stark contrast emphasizing the dragon's weathered scales and ancient
presence, documentary realism treating the mythical creature as if real, environmental
context showing the harsh mountain terrain, overcast natural lighting, medium format
film quality, timeless archival quality, masterpiece, highly detailed, sharp focus

NEGATIVE: color, digital art, 3d render, painting, cartoon, anime, blurry, low quality,
poorly drawn, bad anatomy, modern, oversaturated, bright colors, fantasy art style
```

**Why it works:** Chat mode lets you experiment with wildly different interpretations of the same concept, quickly testing various artistic directions.

---

### Conversation Example 3: Problem Solving

**Model:** Flux Dev
**Mode:** Chat & Refine

```
👤 User: A busy marketplace scene

🤖 Assistant: PROMPT: A vibrant marketplace bustling with activity, colorful vendor
stalls lined with fresh produce and handcrafted goods, crowds of shoppers weaving
between displays, merchants calling out their wares, bright fabrics hanging overhead
creating canopy shade, warm natural daylight filtering through, rich atmosphere of
commerce and community...

👤 User: Too crowded and chaotic, I want it more peaceful

🤖 Assistant: PROMPT: A serene early morning marketplace before the crowds arrive,
just a few vendors setting up their colorful stalls with fresh produce and handcrafted
goods. Soft golden hour sunlight filters between buildings, casting long gentle shadows
across the cobblestone ground. A single early shopper browses quietly while a merchant
arranges flowers in neat rows. Bright fabrics hang peacefully overhead, barely swaying
in the calm morning air. The atmosphere is tranquil and contemplative, capturing the
quiet beauty of the marketplace at dawn before the day's hustle begins...

👤 User: That's better, but can you emphasize the lighting more?

🤖 Assistant: PROMPT: A serene early morning marketplace bathed in spectacular golden
hour sunlight, warm amber rays piercing between buildings and creating dramatic beams
of light through the morning mist. Just a few vendors set up their colorful stalls,
their produce and handcrafted goods glowing in the magical dawn light. Soft illumination
catches suspended dust particles in the air, creating an ethereal atmosphere. Long
gentle shadows stretch across ancient cobblestones, adding depth and dimension. A single
early shopper is silhouetted against a shaft of sunlight while a merchant arranges
flowers that seem to luminous in the warm glow. Bright fabrics overhead filter the
light into colorful patterns below. The entire scene is defined by the quality of light
- peaceful, golden, and transformative, turning an ordinary marketplace into something
transcendent...
```

**Why it works:** Chat mode lets you course-correct when the first attempt doesn't match your vision, refining specific aspects while keeping what works.

---

## Art Style Tips

### For Photography Styles

**Do:**
- Specify camera details (focal length, aperture) for SDXL
- Mention film types for specific looks (Kodak Portra, Ilford HP5)
- Use photography-specific artists (Ansel Adams, Annie Leibovitz)
- Include lighting setups (three-point, Rembrandt, split lighting)

**Example:**
```
Input: "portrait of musician"
Better: "portrait of jazz musician, 85mm lens, shallow depth of field,
Rembrandt lighting, Annie Leibovitz style"
```

---

### For Painted Styles

**Do:**
- Specify the painting medium (oil, watercolor, acrylic)
- Mention brush techniques (impasto, glazing, alla prima)
- Reference specific art movements (Impressionism, Art Nouveau)
- Include traditional art descriptors (canvas texture, brushstrokes)

**Example:**
```
Input: "landscape painting"
Better: "impressionist landscape, oil on canvas, visible brushstrokes,
plein air painting style, vibrant color palette"
```

---

### For Digital/3D Art

**Do:**
- Specify render engines (Octane, Unreal Engine, Blender Cycles)
- Mention rendering techniques (ray tracing, global illumination)
- Include quality markers (4K, 8K, highly detailed)
- Reference digital art platforms (ArtStation trending)

**Example:**
```
Input: "robot character"
Better: "sci-fi robot character design, Unreal Engine 5, ray traced reflections,
8k render, trending on ArtStation, detailed mechanical parts"
```

---

### For Anime/Manga

**Do:**
- Specify anime style period (90s anime, modern anime)
- Mention studio styles (Studio Ghibli, Makoto Shinkai)
- Include characteristic techniques (cel shaded, key visual)
- Reference specific aesthetic elements (vibrant colors, dramatic eyes)

**Example:**
```
Input: "anime character"
Better: "anime character in Makoto Shinkai style, detailed background,
vibrant colors, soft lighting, key visual, modern anime aesthetic"
```

---

### For Cinematic Looks

**Do:**
- Reference film stocks or color grades (Fujifilm, teal and orange)
- Mention aspect ratios (anamorphic, 2.35:1)
- Include cinematography terms (bokeh, lens flare, film grain)
- Specify mood/genre (film noir, sci-fi thriller)

**Example:**
```
Input: "city street at night"
Better: "noir city street at night, cinematic composition, anamorphic lens,
film grain, teal and orange color grade, high contrast, 2.35:1 aspect ratio"
```

---

## Best Practices

### 1. Start Simple, Then Add Detail

**Basic approach:**
1. Start with core concept: "dragon in forest"
2. Add key element: "ancient dragon sleeping in misty forest"
3. Layer in details: "ancient dragon sleeping in misty primordial forest, morning light"

Use Quick Generate for single shots, Chat mode for iterative building.

---

### 2. Use Presets Strategically

**Preset strategy:**
- **No presets:** Maximum AI creativity, unpredictable results
- **One preset:** Gentle guidance (just style OR lighting)
- **Two presets:** Balanced direction (style + lighting)
- **Three+ presets:** Strong artistic control (style + artist + composition + lighting)

**Example progression:**
```
None: "cat in window"
→ Unexpected, varied results

One (Lighting): "cat in window" + Golden Hour
→ Warm, naturally lit scenes

Two (Style + Lighting): "cat in window" + Photorealistic + Natural Window Light
→ Realistic photography aesthetic

Three (Style + Artist + Lighting): "cat in window" + Photorealistic +
Annie Leibovitz + Natural Window Light
→ Professional portrait photography style
```

---

### 3. Model Selection Guide

**Choose Flux when:**
- You want natural, flowing descriptions
- Creating artistic or creative concepts
- You prefer conversational prompts
- Working on complex scenes with lots of details

**Choose SDXL when:**
- You need precise technical control
- Working with established Stable Diffusion workflows
- You want to specify what to avoid (negative prompts)
- Creating specific quality-tagged outputs

---

### 4. Troubleshooting Prompts

**Problem:** Results are too generic

**Solutions:**
- Add more specific details to input
- Use Chat mode to refine iteratively
- Select more presets for guidance
- Include emotional or atmospheric descriptors

---

**Problem:** Results don't match your vision

**Solutions:**
- Switch to Chat mode and describe what's wrong
- Try different preset combinations
- Switch models (Flux ↔ SDXL)
- Be more specific about the desired style

---

**Problem:** Output is repetitive across generations

**Solutions:**
- Vary your input descriptions
- Try different preset combinations
- Use Chat mode to explore variations
- Ask for "different interpretation" or "alternative version"

---

### 5. Advanced Techniques

#### Technique 1: Layered Descriptions

Build prompts in layers of specificity:

```
Layer 1 (Subject): warrior
Layer 2 (Context): warrior in ancient temple
Layer 3 (Details): battle-worn warrior in crumbling ancient temple
Layer 4 (Atmosphere): battle-worn warrior in crumbling ancient temple,
shafts of divine light
```

#### Technique 2: Emotional Direction

Include mood/emotion words to guide atmosphere:

```
Basic: "abandoned building"
With emotion: "melancholic abandoned building, nostalgic atmosphere"
```

#### Technique 3: Reference Combination

Mix multiple artistic references:

```
"in the style of Ansel Adams photography meets Blade Runner aesthetic"
"combining Studio Ghibli's warmth with cyberpunk elements"
```

#### Technique 4: Temporal Specificity

Specify time for better context:

```
"medieval castle" → "medieval castle at dawn"
"city street" → "city street during blue hour"
"forest" → "autumn forest in late afternoon"
```

---

## Quick Reference

### When to Use What

| Goal | Mode | Model | Key Presets |
|------|------|-------|-------------|
| Fast single prompt | Quick Generate | Flux | 0-2 presets |
| Precise control | Quick Generate | SDXL | 2-4 presets |
| Exploration | Chat & Refine | Flux | Vary during chat |
| Iteration | Chat & Refine | Either | Add/change per message |
| Photography | Quick Generate | SDXL | Artist + Lighting |
| Artistic | Quick Generate | Flux | Style + Artist |
| Technical/3D | Quick Generate | SDXL | Style: 3D Render |
| Natural scenes | Either | Flux | Lighting presets |

---

### Common Preset Pairings

**Great combinations:**
- Photorealistic + Studio Lighting
- Cinematic + Dramatic Shadows
- Cyberpunk + Neon Lighting
- Fantasy Art + Volumetric Lighting
- Oil Painting + Soft Diffused
- 3D Render + any lighting
- Anime + any Makoto Shinkai/Studio Ghibli artist

**Avoid combining:**
- Oil Painting + Photorealistic (conflicting styles)
- Pencil Sketch + 3D Render (medium conflict)
- Minimalist + Fantasy Art (aesthetic conflict)

---

## Conclusion

The key to great prompts is experimentation and iteration. Use these examples as starting points, but don't be afraid to:

- Mix unexpected preset combinations
- Try both Quick Generate and Chat modes
- Switch between Flux and SDXL
- Refine prompts through conversation
- Save your best results and learn what works

**Remember:** The AI is a creative partner. Start with your vision, use presets as guidance, and iterate until you achieve exactly what you want.

Happy prompting! 🎨
