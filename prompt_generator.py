#!/usr/bin/env python3
"""
Prompt Generator Web App
Talks to local Ollama to generate detailed prompts for ComfyUI
"""

from flask import Flask, render_template, request, jsonify, session
import requests
import json
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

OLLAMA_URL = "http://localhost:11434/api/generate"

# Preset options for prompt enhancement
PRESETS = {
    "styles": {
        "None": "",
        "Cinematic": "cinematic, dramatic, movie still, film grain",
        "Anime": "anime style, manga, cel shaded, vibrant colors",
        "Photorealistic": "photorealistic, highly detailed, 8k uhd, dslr, high quality",
        "Oil Painting": "oil painting, brushstrokes, traditional art, painterly",
        "Digital Art": "digital art, concept art, detailed, artstation trending",
        "Watercolor": "watercolor painting, soft colors, artistic, flowing",
        "Cyberpunk": "cyberpunk, neon lights, futuristic, dystopian, tech noir",
        "Fantasy Art": "fantasy art, magical, epic, detailed, ethereal",
        "Comic Book": "comic book style, bold lines, halftone dots, pop art",
        "Minimalist": "minimalist, clean, simple, modern, elegant",
        "Surreal": "surreal, dreamlike, abstract, unusual, imaginative",
        "Vintage": "vintage, retro, nostalgic, aged, classic",
        "3D Render": "3d render, octane render, unreal engine, ray tracing",
        "Pencil Sketch": "pencil sketch, graphite, hand drawn, detailed shading"
    },
    
    "artists": {
        "None": "",
        "Greg Rutkowski": "in the style of Greg Rutkowski",
        "Artgerm": "in the style of Artgerm",
        "Alphonse Mucha": "in the style of Alphonse Mucha, art nouveau",
        "H.R. Giger": "in the style of H.R. Giger, biomechanical",
        "Hayao Miyazaki": "Studio Ghibli style, Hayao Miyazaki",
        "Ross Tran": "in the style of Ross Tran",
        "Loish": "in the style of Loish",
        "Makoto Shinkai": "in the style of Makoto Shinkai",
        "James Gurney": "in the style of James Gurney",
        "Ansel Adams": "Ansel Adams photography style",
        "Annie Leibovitz": "Annie Leibovitz portrait photography style",
        "Steve McCurry": "Steve McCurry documentary photography style",
        "Peter Lindbergh": "Peter Lindbergh fashion photography style",
        "Sebastião Salgado": "Sebastião Salgado black and white photography",
        "Irving Penn": "Irving Penn studio photography style",
        "Moebius": "in the style of Moebius, detailed linework",
        "Simon Stålenhag": "in the style of Simon Stålenhag",
        "Zdzisław Beksiński": "in the style of Zdzisław Beksiński, dystopian"
    },
    
    "composition": {
        "None": "",
        "Portrait": "portrait composition, centered subject",
        "Landscape": "landscape composition, wide view",
        "Close-up": "close-up shot, detailed, intimate",
        "Wide Shot": "wide shot, establishing shot, full scene",
        "Medium Shot": "medium shot, waist up, balanced framing",
        "Extreme Close-up": "extreme close-up, macro detail",
        "Bird's Eye View": "bird's eye view, top-down perspective, aerial view",
        "Low Angle": "low angle shot, looking up, dramatic perspective",
        "High Angle": "high angle shot, looking down",
        "Dutch Angle": "dutch angle, tilted, dynamic composition",
        "Rule of Thirds": "rule of thirds composition, balanced",
        "Symmetrical": "symmetrical composition, centered, balanced",
        "Leading Lines": "leading lines composition, depth, perspective",
        "Frame within Frame": "frame within frame composition",
        "Golden Ratio": "golden ratio composition, fibonacci spiral"
    },
    
    "lighting": {
        "None": "",
        "Golden Hour": "golden hour lighting, warm, soft sunlight",
        "Blue Hour": "blue hour lighting, cool tones, twilight",
        "Studio Lighting": "professional studio lighting, three point lighting",
        "Dramatic Shadows": "dramatic shadows, high contrast, chiaroscuro",
        "Soft Diffused": "soft diffused lighting, even, flattering",
        "Neon Lighting": "neon lighting, vibrant colors, glowing",
        "Candlelight": "candlelight, warm glow, intimate atmosphere",
        "Backlit": "backlit, rim lighting, silhouette, halo effect",
        "Natural Window Light": "natural window light, soft, directional",
        "Harsh Sunlight": "harsh sunlight, strong shadows, high contrast",
        "Overcast": "overcast lighting, soft shadows, even illumination",
        "Volumetric Lighting": "volumetric lighting, god rays, atmospheric",
        "Moonlight": "moonlight, cool tones, mysterious atmosphere",
        "Fire Light": "firelight, warm orange glow, flickering",
        "Underwater Light": "underwater lighting, caustics, diffused"
    }
}

# System prompts for different models
SYSTEM_PROMPTS = {
    "sdxl": """You are an expert prompt engineer for Stable Diffusion XL (SDXL). When users describe an image idea, you expand it into a detailed, effective prompt.

The user may provide preset selections for style, artist/photographer, composition, and lighting. When these are provided, incorporate them naturally into the prompt.

SDXL works best with:
- Natural language descriptions with rich details
- Quality tags like: masterpiece, best quality, highly detailed, sharp focus, 8k
- Specific details about: subject, composition, lighting, camera angle, art style, mood, colors
- Negative prompts to avoid unwanted elements

Format your response as:
PROMPT: [detailed positive prompt incorporating any presets]
NEGATIVE: [negative prompt with things to avoid]

Be creative, specific, and detailed. Weave the preset selections naturally into the description.""",

    "flux": """You are an expert prompt engineer for Flux models. When users describe an image idea, you expand it into a detailed, effective prompt.

The user may provide preset selections for style, artist/photographer, composition, and lighting. When these are provided, incorporate them naturally and seamlessly into the prompt description.

Flux models work best with:
- Natural language, conversational style prompts
- Very detailed scene descriptions
- Specific lighting and atmospheric details
- Camera angles and composition details
- Art style and mood descriptions
- No need for quality tags or negative prompts (Flux ignores them)

Format your response as:
PROMPT: [single detailed natural language prompt incorporating any presets naturally]

Be extremely descriptive and creative. Write like you're describing a photograph or painting in detail. Integrate the preset selections seamlessly into the narrative."""
}

def call_ollama(messages, model="qwen3:latest"):
    """Call Ollama API with messages"""
    try:
        # Build the prompt from messages
        system_msg = ""
        conversation = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] == "user":
                conversation += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                conversation += f"Assistant: {msg['content']}\n"
        
        # Format the full prompt
        if system_msg:
            full_prompt = f"{system_msg}\n\n{conversation}Assistant:"
        else:
            full_prompt = f"{conversation}Assistant:"
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        return result['response']
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Ollama: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/presets', methods=['GET'])
def get_presets():
    """Get available presets"""
    return jsonify(PRESETS)

@app.route('/generate', methods=['POST'])
def generate():
    """Generate a prompt (one-shot mode)"""
    data = request.json
    user_input = data.get('input', '').strip()
    model_type = data.get('model', 'flux')
    
    # Get preset selections
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')
    
    if not user_input:
        return jsonify({'error': 'Please provide a description'}), 400
    
    # Build context with presets
    preset_context = []
    if style != 'None':
        preset_context.append(f"Style: {PRESETS['styles'][style]}")
    if artist != 'None':
        preset_context.append(f"Artist/Style: {PRESETS['artists'][artist]}")
    if composition != 'None':
        preset_context.append(f"Composition: {PRESETS['composition'][composition]}")
    if lighting != 'None':
        preset_context.append(f"Lighting: {PRESETS['lighting'][lighting]}")
    
    # Build the full user message
    if preset_context:
        preset_info = "\n".join(preset_context)
        full_input = f"User's image idea: {user_input}\n\nSelected presets:\n{preset_info}\n\nPlease create a detailed prompt incorporating these elements."
    else:
        full_input = user_input
    
    # Get appropriate system prompt
    system_prompt = SYSTEM_PROMPTS.get(model_type, SYSTEM_PROMPTS['flux'])
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_input}
    ]
    
    result = call_ollama(messages)
    
    return jsonify({
        'result': result,
        'model': model_type
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Conversational mode - refine ideas back and forth"""
    data = request.json
    user_message = data.get('message', '').strip()
    model_type = data.get('model', 'flux')
    
    # Get preset selections
    style = data.get('style', 'None')
    artist = data.get('artist', 'None')
    composition = data.get('composition', 'None')
    lighting = data.get('lighting', 'None')
    
    if not user_message:
        return jsonify({'error': 'Please provide a message'}), 400
    
    # Get or initialize conversation history
    if 'conversation' not in session:
        session['conversation'] = []
        session['model_type'] = model_type
    
    # If model changed, reset conversation
    if session.get('model_type') != model_type:
        session['conversation'] = []
        session['model_type'] = model_type
    
    # Add system prompt if starting new conversation
    if not session['conversation']:
        system_prompt = SYSTEM_PROMPTS.get(model_type, SYSTEM_PROMPTS['flux'])
        session['conversation'].append({
            "role": "system", 
            "content": system_prompt
        })
    
    # Build context with presets
    preset_context = []
    if style != 'None':
        preset_context.append(f"Style: {PRESETS['styles'][style]}")
    if artist != 'None':
        preset_context.append(f"Artist/Style: {PRESETS['artists'][artist]}")
    if composition != 'None':
        preset_context.append(f"Composition: {PRESETS['composition'][composition]}")
    if lighting != 'None':
        preset_context.append(f"Lighting: {PRESETS['lighting'][lighting]}")
    
    # Build the full user message
    if preset_context:
        preset_info = "\n".join(preset_context)
        full_message = f"{user_message}\n\n[Selected presets: {preset_info}]"
    else:
        full_message = user_message
    
    # Add user message
    session['conversation'].append({
        "role": "user",
        "content": full_message
    })
    
    # Get response from Ollama
    result = call_ollama(session['conversation'])
    
    # Add assistant response to history
    session['conversation'].append({
        "role": "assistant",
        "content": result
    })
    
    # Keep conversation manageable (last 10 messages + system)
    if len(session['conversation']) > 21:  # system + 20 messages
        session['conversation'] = [session['conversation'][0]] + session['conversation'][-20:]
    
    session.modified = True
    
    return jsonify({
        'result': result,
        'model': model_type
    })

@app.route('/reset', methods=['POST'])
def reset():
    """Reset conversation history"""
    session.pop('conversation', None)
    session.pop('model_type', None)
    return jsonify({'status': 'reset'})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎨 Prompt Generator Starting...")
    print("="*60)
    print("\nOpen your browser to: http://localhost:5000")
    print("\nMake sure Ollama is running!")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
