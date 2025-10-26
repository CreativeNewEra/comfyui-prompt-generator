# Hierarchical Preset API Documentation

## Overview

The hierarchical preset system provides 7 new API endpoints for navigating through 5 levels of preset selections. These routes enable progressive loading of preset data for an optimal user experience.

**Base URL:** `http://localhost:5000`

**Feature Flag:** These routes require `ENABLE_HIERARCHICAL_PRESETS=true` in `.env`

---

## API Routes

### 1. Get Categories (Level 1)

**Endpoint:** `GET /api/categories`

**Description:** Returns all main style categories (Photography, Fantasy, Sci-Fi, etc.)

**Authentication:** None required

**Request Parameters:** None

**Response:**
```json
{
  "version": "1.0",
  "categories": [
    {
      "id": "photography",
      "name": "Photography",
      "icon": "📸",
      "description": "Realistic camera-based imagery",
      "popularity": "high",
      "best_for": ["portraits", "landscapes", "realistic scenes"]
    },
    {
      "id": "fantasy",
      "name": "Fantasy Art",
      "icon": "🐉",
      "description": "Epic magical worlds, creatures, heroes",
      "popularity": "high",
      "best_for": ["dragons", "wizards", "epic battles", "magical"]
    }
    // ... more categories
  ]
}
```

**Error Responses:**
- `400` - Hierarchical presets not enabled
- `500` - Server error loading presets

**Example:**
```bash
curl http://localhost:5000/api/categories
```

---

### 2. Get Types (Level 2)

**Endpoint:** `GET /api/categories/<category_id>/types`

**Description:** Returns sub-types for a specific category

**Path Parameters:**
- `category_id` (string) - Category identifier (e.g., "photography", "fantasy")

**Response:**
```json
{
  "category_id": "photography",
  "category_name": "Photography",
  "types": [
    {
      "id": "portrait",
      "name": "Portrait Photography",
      "description": "People-focused, faces & emotion",
      "icon": "👤",
      "popularity": "high"
    },
    {
      "id": "landscape",
      "name": "Landscape Photography",
      "description": "Nature & scenery, grand vistas",
      "icon": "🏞",
      "popularity": "high"
    }
    // ... more types
  ]
}
```

**Error Responses:**
- `400` - Hierarchical presets not enabled
- `404` - Category not found
- `500` - Server error

**Examples:**
```bash
# Get photography types
curl http://localhost:5000/api/categories/photography/types

# Get fantasy types
curl http://localhost:5000/api/categories/fantasy/types

# Get sci-fi types
curl http://localhost:5000/api/categories/scifi/types
```

---

### 3. Get Artists (Level 3)

**Endpoint:** `GET /api/categories/<category_id>/types/<type_id>/artists`

**Description:** Returns artists/styles for a specific type

**Path Parameters:**
- `category_id` (string) - Category identifier
- `type_id` (string) - Type identifier

**Response:**
```json
{
  "category_id": "photography",
  "type_id": "portrait",
  "type_name": "Portrait Photography",
  "artists": [
    {
      "id": "annie_leibovitz",
      "name": "Annie Leibovitz",
      "description": "Celebrity portraits, dramatic concepts, theatrical",
      "signature": "Bold, theatrical, narrative-driven",
      "best_for": ["editorial", "iconic portraits", "conceptual"],
      "popularity": "high",
      "has_technical": true,
      "has_specifics": true
    },
    {
      "id": "richard_avedon",
      "name": "Richard Avedon",
      "description": "White backdrop minimalist portraits, powerful, raw emotion",
      "signature": "Simple, powerful, stark white backgrounds",
      "best_for": ["character studies", "dramatic simplicity"],
      "popularity": "medium",
      "has_technical": false,
      "has_specifics": false
    }
    // ... more artists
  ]
}
```

**Error Responses:**
- `400` - Hierarchical presets not enabled
- `404` - Category or type not found
- `500` - Server error

**Examples:**
```bash
# Get portrait photographers
curl http://localhost:5000/api/categories/photography/types/portrait/artists

# Get high fantasy artists
curl http://localhost:5000/api/categories/fantasy/types/high_fantasy/artists

# Get cyberpunk artists
curl http://localhost:5000/api/categories/scifi/types/cyberpunk/artists
```

---

### 4. Get Technical Options (Level 4)

**Endpoint:** `GET /api/artists/<category_id>/<type_id>/<artist_id>/technical`

**Description:** Returns technical/style options specific to an artist

**Path Parameters:**
- `category_id` (string) - Category identifier
- `type_id` (string) - Type identifier
- `artist_id` (string) - Artist identifier

**Response:**
```json
{
  "category_id": "photography",
  "type_id": "portrait",
  "artist_id": "annie_leibovitz",
  "artist_name": "Annie Leibovitz",
  "technical_options": {
    "camera_lens": {
      "name": "Camera & Lens",
      "options": [
        {
          "id": "medium_format",
          "name": "Medium format (Hasselblad)",
          "description": "Her signature camera",
          "recommended": true
        },
        {
          "id": "35mm_full_frame",
          "name": "35mm full frame",
          "description": "Standard professional"
        }
        // ... more options
      ]
    },
    "lighting": {
      "name": "Lighting Setup",
      "options": [
        {
          "id": "theatrical",
          "name": "Conceptual/theatrical",
          "description": "Her specialty - narrative lighting",
          "recommended": true
        }
        // ... more options
      ]
    }
    // ... more technical categories
  }
}
```

**Error Responses:**
- `400` - Hierarchical presets not enabled
- `404` - Artist not found
- `500` - Server error

**Examples:**
```bash
# Get Annie Leibovitz technical options
curl http://localhost:5000/api/artists/photography/portrait/annie_leibovitz/technical

# Get Greg Rutkowski technical options
curl http://localhost:5000/api/artists/fantasy/high_fantasy/greg_rutkowski/technical

# Get H.R. Giger technical options
curl http://localhost:5000/api/artists/horror/body_horror/hr_giger/technical
```

---

### 5. Get Scene Specifics (Level 5)

**Endpoint:** `GET /api/artists/<category_id>/<type_id>/<artist_id>/specifics`

**Description:** Returns scene-specific options for an artist

**Path Parameters:**
- `category_id` (string) - Category identifier
- `type_id` (string) - Type identifier
- `artist_id` (string) - Artist identifier

**Response:**
```json
{
  "category_id": "photography",
  "type_id": "portrait",
  "artist_id": "annie_leibovitz",
  "artist_name": "Annie Leibovitz",
  "scene_specifics": {
    "subject_type": {
      "name": "Subject Type",
      "options": [
        {
          "id": "single_person",
          "name": "Single person",
          "sub_options": {
            "age": ["child", "teen", "young_adult", "middle_aged", "senior"],
            "type": ["celebrity", "athlete", "artist", "professional", "casual"]
          }
        }
        // ... more options
      ]
    },
    "pose_expression": {
      "name": "Pose & Expression",
      "options": [
        "direct_gaze_confident",
        "looking_away_contemplative",
        "conceptual_theatrical"
      ],
      "recommended": "conceptual_theatrical"
    }
    // ... more scene options
  }
}
```

**Error Responses:**
- `400` - Hierarchical presets not enabled
- `404` - Artist not found
- `500` - Server error

**Examples:**
```bash
# Get Annie Leibovitz scene specifics
curl http://localhost:5000/api/artists/photography/portrait/annie_leibovitz/specifics

# Get Jim Lee scene specifics
curl http://localhost:5000/api/artists/comic_book/marvel_style/jim_lee/specifics
```

---

### 6. Get Preset Packs

**Endpoint:** `GET /api/preset-packs`

**Description:** Returns pre-configured preset combinations for quick start

**Response:**
```json
{
  "packs": [
    {
      "name": "90s X-Men Comic",
      "icon": "🦸",
      "selections": {
        "level1": "comic_book",
        "level2": "marvel_style",
        "level3": "jim_lee",
        "level4": {
          "inking": "heavy_crosshatch",
          "coloring": "modern_gradient",
          "detail": "maximum"
        },
        "level5": {
          "scene_type": "character",
          "action": "dynamic_action",
          "composition": "low_angle"
        }
      }
    },
    {
      "name": "Studio Ghibli Magic",
      "icon": "🎌",
      "selections": {
        "level1": "anime",
        "level2": "slice_of_life",
        "level3": "studio_ghibli",
        "level4": {
          "technique": "painted_backgrounds",
          "color": "soft_pastel"
        },
        "level5": {
          "mood": "whimsical",
          "atmosphere": "peaceful"
        }
      }
    }
    // ... more packs
  ]
}
```

**Error Responses:**
- `400` - Hierarchical presets not enabled
- `500` - Server error

**Example:**
```bash
curl http://localhost:5000/api/preset-packs
```

---

### 7. Get Universal Options

**Endpoint:** `GET /api/universal-options`

**Description:** Returns universal options available across all categories

**Response:**
```json
{
  "universal_options": {
    "mood": {
      "core": [
        {
          "id": "dramatic",
          "name": "Dramatic",
          "description": "Intense, powerful, striking"
        },
        {
          "id": "peaceful",
          "name": "Peaceful",
          "description": "Serene, calm, tranquil"
        }
        // ... more moods
      ],
      "by_category": {
        "fantasy": ["epic", "heroic", "magical", "whimsical"],
        "horror": ["terrifying", "unsettling", "eerie", "grotesque"]
      }
    },
    "lighting": {
      "core": [
        {
          "id": "golden_hour",
          "name": "Golden Hour",
          "description": "Warm sunset/sunrise light, flattering",
          "popularity": "high"
        }
        // ... more lighting options
      ]
    },
    "time_of_day": {
      "options": [
        {
          "id": "dawn",
          "name": "Dawn",
          "description": "Early morning, soft light, hopeful"
        }
        // ... more times
      ]
    },
    "weather_atmosphere": { /* ... */ },
    "color_palettes": { /* ... */ },
    "camera_effects": { /* ... */ },
    "composition": { /* ... */ }
  }
}
```

**Error Responses:**
- `400` - Hierarchical presets not enabled
- `500` - Server error

**Example:**
```bash
curl http://localhost:5000/api/universal-options
```

---

## Complete User Flow Example

Here's how a frontend would use these routes to build a complete preset selection:

### Step 1: Get Categories
```bash
curl http://localhost:5000/api/categories
# User selects: "photography"
```

### Step 2: Get Types for Photography
```bash
curl http://localhost:5000/api/categories/photography/types
# User selects: "portrait"
```

### Step 3: Get Artists for Portrait Photography
```bash
curl http://localhost:5000/api/categories/photography/types/portrait/artists
# User selects: "annie_leibovitz"
```

### Step 4: Get Technical Options
```bash
curl http://localhost:5000/api/artists/photography/portrait/annie_leibovitz/technical
# User selects: medium_format, theatrical lighting, f/2.8
```

### Step 5: Get Scene Specifics
```bash
curl http://localhost:5000/api/artists/photography/portrait/annie_leibovitz/specifics
# User selects: conceptual_theatrical pose, costume wardrobe, conceptual set
```

### Step 6: Get Universal Options (Optional)
```bash
curl http://localhost:5000/api/universal-options
# User selects: mood: dramatic, time: golden_hour, colors: warm_tones
```

### Step 7: Generate Prompt
```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "A woman posing",
    "model": "flux",
    "selections": {
      "level1": "photography",
      "level2": "portrait",
      "level3": "annie_leibovitz",
      "level4": {
        "camera_lens": "medium_format",
        "lighting": "theatrical",
        "aperture": "f2_8"
      },
      "level5": {
        "pose_expression": "conceptual_theatrical",
        "wardrobe": "costume_conceptual",
        "environment": "conceptual_set"
      },
      "universal": {
        "mood": ["dramatic", "elegant"],
        "time_of_day": "golden_hour",
        "color_palette": "warm_tones"
      }
    }
  }'
```

---

## Error Handling

All routes return consistent error responses:

### Feature Not Enabled
```json
{
  "error": "Hierarchical presets not enabled",
  "message": "Set ENABLE_HIERARCHICAL_PRESETS=true in .env"
}
```
**Status:** `400 Bad Request`

### Resource Not Found
```json
{
  "error": "Category not found",
  "message": "No category with id 'invalid_category'"
}
```
**Status:** `404 Not Found`

### Server Error
```json
{
  "error": "Failed to load categories",
  "message": "Error details..."
}
```
**Status:** `500 Internal Server Error`

---

## Testing

### Manual Testing

Use `curl` or your browser to test routes:

```bash
# Test categories
curl http://localhost:5000/api/categories | jq

# Test with error handling
curl http://localhost:5000/api/categories/invalid/types

# Test full chain
curl http://localhost:5000/api/categories && \
curl http://localhost:5000/api/categories/photography/types && \
curl http://localhost:5000/api/categories/photography/types/portrait/artists
```

### Automated Testing

Run the provided test script:

```bash
# Make sure app is running with hierarchical presets enabled
python prompt_generator.py

# In another terminal
python test_api_routes.py
```

The test script will:
- Test all 7 API routes
- Verify JSON responses
- Test error handling
- Check multiple categories
- Provide detailed results

---

## Performance Notes

### Caching
- Routes call `load_presets()` on each request (hot-reload capability)
- For production, consider caching the presets in memory
- File is ~104KB, loads quickly from disk

### Response Times
- Categories: ~10-20ms
- Types: ~10-20ms
- Artists: ~10-20ms
- Technical: ~10-20ms
- Specifics: ~10-20ms
- Preset Packs: ~10-20ms
- Universal: ~10-20ms

All routes are fast since they just slice the JSON data.

### Optimization Tips
For high-traffic scenarios:
1. Cache `load_presets()` result in app memory
2. Use Redis for distributed caching
3. Add ETags for browser caching
4. Compress responses with gzip

---

## Next Steps

After testing these API routes:

1. **Build Frontend Wizard** - Create UI components that call these routes
2. **Add Search** - Implement artist/category search
3. **Add Validation** - Validate selection combinations
4. **Add Analytics** - Track popular selections
5. **Add Caching** - Optimize for production

---

## Support

For issues or questions:

1. Check `logs/app.log` for errors
2. Verify `ENABLE_HIERARCHICAL_PRESETS=true` in `.env`
3. Confirm `hierarchical_presets.json` exists
4. Run `python test_api_routes.py` to diagnose issues
5. Review this documentation

---

## Changelog

### Version 1.0 (Phase 2A)
- Initial release of hierarchical preset API
- 7 new routes for 5-level navigation
- Preset packs support
- Universal options support
- Comprehensive error handling
- Full documentation
- Automated test suite
