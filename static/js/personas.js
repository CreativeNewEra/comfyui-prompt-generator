/**
 * Persona System Module
 * Manages conversational AI personas for prompt generation
 * (Placeholder for future persona system implementation)
 */

// Global persona state
let currentPersona = null;
let personaList = [];

/**
 * Load available personas from the API
 */
async function loadPersonas() {
    try {
        const response = await fetch('/api/personas');
        const data = await response.json();
        personaList = data.personas || [];
        console.log(`Loaded ${personaList.length} personas`);
        return personaList;
    } catch (error) {
        console.error('Failed to load personas:', error);
        return [];
    }
}

/**
 * Get details for a specific persona
 * @param {string} personaId - The persona ID
 */
async function getPersonaDetails(personaId) {
    try {
        const response = await fetch(`/api/personas/${personaId}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Failed to load persona details:', error);
        return null;
    }
}

/**
 * Set the active persona
 * @param {string} personaId - The persona ID to activate
 */
function setActivePersona(personaId) {
    currentPersona = personaId;
    console.log(`Active persona: ${personaId}`);
    // Update UI to reflect active persona
    updatePersonaUI(personaId);
}

/**
 * Update UI elements to reflect active persona
 * @param {string} personaId - The active persona ID
 */
function updatePersonaUI(personaId) {
    // Remove active class from all persona buttons
    document.querySelectorAll('.persona-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Add active class to selected persona button
    const activeBtn = document.querySelector(`[data-persona="${personaId}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }

    // Update any persona-specific UI elements
    const personaIndicator = document.getElementById('personaIndicator');
    if (personaIndicator) {
        const persona = personaList.find(p => p.id === personaId);
        if (persona) {
            personaIndicator.textContent = `${persona.icon} ${persona.name}`;
            personaIndicator.style.display = 'block';
        }
    }
}

/**
 * Clear the active persona
 */
function clearActivePersona() {
    currentPersona = null;
    document.querySelectorAll('.persona-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const personaIndicator = document.getElementById('personaIndicator');
    if (personaIndicator) {
        personaIndicator.style.display = 'none';
    }
}

/**
 * Chat with a persona (non-streaming)
 * @param {string} personaId - The persona ID
 * @param {string} message - The user's message
 * @param {Object} additionalData - Additional data (model, presets, etc.)
 */
async function chatWithPersona(personaId, message, additionalData = {}) {
    try {
        const response = await fetch('/persona-chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                persona_id: personaId,
                message: message,
                ...additionalData
            })
        });

        const data = await response.json();
        return { response, data };
    } catch (error) {
        console.error('Failed to chat with persona:', error);
        throw error;
    }
}

/**
 * Chat with a persona (streaming)
 * @param {string} personaId - The persona ID
 * @param {string} message - The user's message
 * @param {Object} additionalData - Additional data (model, presets, etc.)
 * @param {Function} onToken - Callback for each token
 * @param {Function} onComplete - Callback when complete
 * @param {Function} onError - Callback for errors
 */
async function chatWithPersonaStreaming(personaId, message, additionalData, onToken, onComplete, onError) {
    const payload = {
        persona_id: personaId,
        message: message,
        ...additionalData
    };

    await generateWithStreaming('/persona-chat-stream', payload, onToken, onComplete, onError);
}

/**
 * Reset persona conversation
 * @param {string} personaId - The persona ID
 */
async function resetPersonaConversation(personaId) {
    try {
        await fetch('/persona-reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ persona_id: personaId })
        });
        console.log(`Reset conversation for persona: ${personaId}`);
    } catch (error) {
        console.error('Failed to reset persona conversation:', error);
    }
}

/**
 * Get the currently active persona ID
 * @returns {string|null} Current persona ID or null
 */
function getCurrentPersona() {
    return currentPersona;
}

/**
 * Check if a persona supports presets
 * @param {string} personaId - The persona ID
 * @returns {boolean} True if persona supports presets
 */
function personaSupportsPresets(personaId) {
    const persona = personaList.find(p => p.id === personaId);
    if (!persona) return false;

    // Personas that support presets
    const presetSupportingPersonas = [
        'technical_engineer',
        'art_director',
        'photography_expert',
        'nsfw_specialist'
    ];

    return presetSupportingPersonas.includes(personaId);
}

/**
 * Render persona selector UI
 * @param {string} containerId - ID of the container element
 */
function renderPersonaSelector(containerId) {
    const container = document.getElementById(containerId);
    if (!container || personaList.length === 0) return;

    container.innerHTML = personaList.map(persona => `
        <button class="persona-btn" data-persona="${persona.id}" onclick="setActivePersona('${persona.id}')">
            <span class="persona-icon">${persona.icon}</span>
            <span class="persona-name">${persona.name}</span>
            <span class="persona-description">${persona.description}</span>
        </button>
    `).join('');
}
