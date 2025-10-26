# NSFW Presets Guide

This document describes the adult/NSFW presets added to the ComfyUI Prompt Generator.

## 📋 Overview

NSFW presets have been added to both the simple (`presets.json`) and hierarchical (`hierarchical_presets.json`) preset systems. These presets enable tasteful, artistic generation of mature content including boudoir photography, artistic nudes, glamour photography, and pin-up styles.

---

## 🎨 Simple Preset System (presets.json)

### Added to "Styles" Category:
- **Boudoir** - Intimate, sensual, elegant, romantic lighting
- **Pin-up** - Retro glamour, classic curves, vintage aesthetic
- **Artistic Nude** - Fine art photography, tasteful, elegant, classical figure study
- **Glamour** - Sophisticated, alluring, high fashion beauty
- **Sensual Portrait** - Intimate atmosphere, romantic mood, soft focus

### Added to "Artists" Category:
- **Helmut Newton** - Bold contrast, provocative, high fashion edge
- **Ellen von Unwerth** - Playful sensuality, vintage glamour, feminine empowerment
- **Rankin** - Bold fashion, intimate portraits, contemporary edge
- **David LaChapelle** - Surreal glamour, vibrant colors, pop art aesthetic
- **Patrick Demarchelier** - Elegant beauty, soft sophistication, timeless glamour
- **Luis Royo** - Fantasy art style, sensual fantasy figures, dramatic poses

### Added to "Composition" Category:
- **Reclining Pose** - Relaxed, horizontal composition, elegant curves
- **Over Shoulder** - Intimate perspective, suggestive framing
- **Back View** - Elegant spine and curves, artistic silhouette
- **Figure Study** - Classical composition, artistic form, balanced pose
- **Intimate Close** - Sensual detail, personal space

### Added to "Lighting" Category:
- **Silk Lighting** - Soft wrapping light, flattering glow, sensual mood
- **Low Key Dramatic** - Dramatic shadows, moody atmosphere, selective illumination
- **Boudoir Soft** - Warm and intimate, flattering shadows, romantic ambiance
- **Rim Light Silhouette** - Glowing edges, sensual silhouette, dramatic outline
- **Warm Amber Glow** - Sunset tones, intimate warmth, golden skin tones

---

## 🏗️ Hierarchical Preset System (hierarchical_presets.json)

A complete new category **"Adult/NSFW Photography"** (🔞) has been added with the following structure:

### Level 1: Main Category
**adult_photography** - Mature content featuring artistic figure, boudoir, and sensual photography

### Level 2: Types (5 subcategories)

#### 1. **Boudoir Photography** 💋
Intimate, romantic, bedroom-style portraiture

**Level 3 Artists:**
- **Helmut Newton**
  - Bold, provocative, high-contrast fashion nude
  - Signature: Dramatic lighting, powerful poses, edgy elegance
  - Level 4 Options: Lighting (harsh dramatic, studio strobe), Film type (B&W high contrast, color vibrant), Composition (power pose, architectural, confrontational)
  - Level 5 Options: Mood (powerful, provocative, elegant_dangerous), Environment (studio_minimal, urban_architecture, luxury_interior)

- **Ellen von Unwerth**
  - Playful, joyful, feminine sensuality with vintage glamour
  - Signature: Fun, energetic, empowering femininity
  - Level 4 Options: Lighting (soft natural, golden hour, vintage soft), Mood (playful_fun, romantic_dreamy, vintage_pin_up)
  - Level 5 Options: Pose style (laughing_candid, playful_movement), Wardrobe (lingerie_vintage, silk_robe)

#### 2. **Artistic Nude/Figure Study** 🎨
Classical fine art nude photography, tasteful and artistic

**Level 3 Artists:**
- **Classical Style**
  - Traditional fine art nude in the style of great masters
  - Level 4 Options: Lighting (chiaroscuro, soft diffused, rembrandt, natural window), Composition (figure_study, silhouette, detail_fragment), Film style (B&W grain, warm tones, high key, low key)
  - Level 5 Options: Pose type (reclining_classical, standing_sculptural, seated_contemplative), Mood (serene_peaceful, dramatic_intense), Environment (studio_minimal, natural_outdoor, draped_fabric)

#### 3. **Glamour Photography** ✨
High-fashion beauty and allure, sophisticated sensuality

**Level 3 Artists:**
- **Rankin**
  - Contemporary glamour, bold fashion-forward, intimate portraits
  - Level 4 Options: Lighting (beauty_dish, ring_light, hard_editorial), Color palette (vibrant_bold, monochrome, natural_skin)
  - Level 5 Options: Expression (intense_gaze, soft_sensual, confident_powerful), Styling (high_fashion_minimal, glamour_lingerie, wet_look)

#### 4. **Pin-up Style** 💄
Vintage-inspired retro glamour, playful and nostalgic

**Level 3 Artists:**
- **Retro Glamour Style**
  - 1940s-1960s pin-up aesthetic, classic curves and poses
  - Level 4 Options: Era style (1940s victory, 1950s classic, 1960s mod, rockabilly), Color grading (vintage_faded, vibrant_saturated, sepia_warm), Props (classic_pin_up, automotive, nautical, domestic)
  - Level 5 Options: Pose style (classic_over_shoulder, legs_up_playful, sitting_coy), Wardrobe (vintage_lingerie, retro_swimsuit, polka_dot_bikini), Makeup & hair (victory_rolls, pin_curls, red_lips_classic)

#### 5. **Sensual Portrait** 🌹
Intimate, emotional, romantic portraiture

**Level 3 Artists:**
- **Contemporary Intimate Style**
  - Modern sensual portraiture with emotional depth
  - Level 4 Options: Lighting (natural_soft, candlelight, golden_hour, low_key_mood), Depth of field (shallow_dreamy, medium_balanced)
  - Level 5 Options: Mood (romantic_tender, passionate_intense, dreamy_soft), Subject (single_person, couple_intimate), Environment (bedroom_intimate, natural_outdoor, bath_water, sheets_fabric)

---

## 🎁 Preset Packs (Quick-Start Combinations)

Four new preset packs have been added for one-click NSFW setups:

### 1. **Newton Bold Fashion** 🔞
- Category: Boudoir → Helmut Newton
- Style: Bold, dramatic B&W high-contrast
- Perfect for: Powerful, provocative fashion nude photography

### 2. **Vintage Pin-up Classic** 💄
- Category: Pin-up → Retro Glamour
- Style: 1950s classic with vibrant colors
- Perfect for: Classic pin-up nostalgia with playful poses

### 3. **Artistic Figure Study** 🎨
- Category: Artistic Nude → Classical Style
- Style: Chiaroscuro lighting, B&W grain, reclining pose
- Perfect for: Fine art gallery-quality figure studies

### 4. **Playful Boudoir** 💋
- Category: Boudoir → Ellen von Unwerth
- Style: Playful, fun, vintage soft lighting
- Perfect for: Joyful, empowering feminine boudoir shots

---

## 🚀 How to Use

### Simple System (presets.json)
1. Simply select from the dropdown menus when generating prompts
2. Combine styles, artists, compositions, and lighting as needed
3. Example: Style="Boudoir" + Artist="Helmut Newton" + Lighting="Low Key Dramatic"

### Hierarchical System (hierarchical_presets.json)
1. Enable hierarchical presets in `.env`: `ENABLE_HIERARCHICAL_PRESETS=true`
2. Select **Adult/NSFW Photography** as your main category
3. Choose a subcategory (Boudoir, Artistic Nude, Glamour, Pin-up, or Sensual Portrait)
4. Select an artist/style
5. Configure technical details (Level 4)
6. Set scene specifics (Level 5)

**OR** use a preset pack for instant configuration!

---

## 📝 Example Combinations

### Flux Prompt Example (Natural Language):
```
User selects: Boudoir > Ellen von Unwerth + Vintage Soft + Playful Movement

AI generates:
"A playful boudoir portrait captured in the joyful, empowering style of Ellen von Unwerth,
bathed in vintage soft lighting reminiscent of classic Hollywood glamour. The subject is
caught in playful movement, laughing candidly with genuine joy, wearing delicate vintage
lingerie that flows with her motion. The warm, flattering light wraps around her form,
creating a romantic ambiance. Shot with a shallow depth of field, the background softly
blurs while keeping her radiant smile and dancing eyes in perfect focus. The overall mood
is one of feminine power and uninhibited joy, celebrating sensuality through authentic
happiness rather than posed perfection."
```

### SDXL Prompt Example (Tags):
```
User selects: Artistic Nude > Classical Style + Chiaroscuro + Figure Study

AI generates:
"masterpiece, best quality, highres, fine art nude photography, classical figure study,
(chiaroscuro lighting:1.3), dramatic light and shadow, Renaissance style, reclining pose,
elegant curves, sculptural form, artistic composition, (black and white:1.2), film grain,
timeless aesthetic, serene peaceful mood, draped fabric backdrop, gallery quality,
museum worthy, tasteful artistic nude, professional fine art photography"

Negative: "explicit, pornographic, crude, vulgar, low quality, distorted anatomy,
oversaturated, amateur, snapshot, phone camera"
```

---

## ⚠️ Important Notes

1. **Tasteful & Artistic**: These presets are designed for artistic, tasteful adult content generation. They focus on photography styles, lighting, composition, and artistic merit.

2. **Professional Standards**: All artist references are based on real, respected photographers and their documented styles.

3. **Flexibility**: Mix and match elements from different subcategories to create unique styles.

4. **Model Compatibility**:
   - **Flux**: Excels at natural language descriptions with nuanced mood and atmosphere
   - **SDXL**: Benefits from structured tags with quality modifiers and negative prompts

5. **Respect & Ethics**: Use these tools responsibly and ethically. Always respect consent, privacy, and legal guidelines in your jurisdiction.

---

## 🎯 Quick Reference

| Want to create... | Use this subcategory | Top artist choice |
|-------------------|---------------------|-------------------|
| Bold, dramatic fashion nude | Boudoir | Helmut Newton |
| Playful, empowering feminine | Boudoir | Ellen von Unwerth |
| Classical fine art nude | Artistic Nude | Classical Style |
| Modern glamour editorial | Glamour | Rankin |
| Retro vintage pin-up | Pin-up | Retro Glamour |
| Intimate couples/romantic | Sensual Portrait | Contemporary Intimate |

---

## 📚 Further Customization

You can further customize by editing the JSON files:

- Add new artists to `level3_artists`
- Add new technical options to `level4_technical`
- Add new scene specifics to `level5_specifics`
- Create additional preset packs combining your favorite settings

Refer to the existing structure as templates for your additions.

---

**Version**: 1.0
**Date**: October 2025
**Compatibility**: ComfyUI Prompt Generator v2.0+
