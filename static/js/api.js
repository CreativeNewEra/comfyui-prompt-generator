/**
 * API Client Module
 * Handles all communication with the backend Flask server
 */

/**
 * Fetch presets from the server
 * @returns {Promise<Object>} Presets data
 */
async function fetchPresets() {
    const response = await fetch('/presets');
    return await response.json();
}

/**
 * Fetch available Ollama models
 * @returns {Promise<Object>} Models data with models array and default model
 */
async function fetchModels() {
    const response = await fetch('/models');
    return await response.json();
}

/**
 * Fetch hierarchical categories
 * @returns {Promise<Object>} Categories data
 */
async function fetchCategories() {
    const response = await fetch('/api/categories');
    return await response.json();
}

/**
 * Fetch types for a given category
 * @param {string} categoryId - The category ID
 * @returns {Promise<Object>} Types data
 */
async function fetchTypes(categoryId) {
    const response = await fetch(`/api/categories/${categoryId}/types`);
    return await response.json();
}

/**
 * Fetch artists for a given category and type
 * @param {string} categoryId - The category ID
 * @param {string} typeId - The type ID
 * @returns {Promise<Object>} Artists data
 */
async function fetchArtists(categoryId, typeId) {
    const response = await fetch(`/api/categories/${categoryId}/types/${typeId}/artists`);
    return await response.json();
}

/**
 * Fetch universal options
 * @returns {Promise<Object>} Universal options data
 */
async function fetchUniversalOptions() {
    const response = await fetch('/api/universal-options');
    return await response.json();
}

/**
 * Fetch preset packs
 * @returns {Promise<Object>} Preset packs data
 */
async function fetchPresetPacks() {
    const response = await fetch('/api/preset-packs');
    return await response.json();
}

/**
 * Generate prompt (non-streaming)
 * @param {Object} payload - Request payload
 * @returns {Promise<Object>} Response data
 */
async function generatePrompt(payload) {
    const response = await fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    return { response, data: await response.json() };
}

/**
 * Chat with AI (non-streaming)
 * @param {Object} payload - Request payload
 * @returns {Promise<Object>} Response data
 */
async function chatWithAI(payload) {
    const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    return { response, data: await response.json() };
}

/**
 * Generate prompt with streaming
 * @param {string} endpoint - API endpoint
 * @param {Object} payload - Request payload
 * @param {Function} onToken - Callback for each token received
 * @param {Function} onComplete - Callback when streaming completes
 * @param {Function} onError - Callback for errors
 * @returns {Promise<void>}
 */
async function generateWithStreaming(endpoint, payload, onToken, onComplete, onError) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || errorData.message || `HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.trim() || !line.startsWith('data: ')) continue;

                try {
                    const data = JSON.parse(line.slice(6));

                    if (data.error) {
                        throw new Error(data.error);
                    }

                    if (data.token) {
                        fullResponse += data.token;
                        onToken(data.token, fullResponse);
                    }

                    if (data.done) {
                        onComplete(fullResponse);
                        return;
                    }
                } catch (e) {
                    console.error('Failed to parse SSE data:', e, 'Line:', line);
                }
            }
        }
    } catch (error) {
        console.error('Streaming error:', error);
        onError(error);
    }
}

/**
 * Reset conversation
 * @returns {Promise<void>}
 */
async function resetConversation() {
    // Check if a persona is selected
    const personaSelect = document.getElementById('personaSelect');
    const selectedPersona = personaSelect ? personaSelect.value : '';

    // Use persona reset endpoint if persona is selected
    const endpoint = selectedPersona ? '/persona-reset' : '/reset';

    await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(selectedPersona ? { persona_id: selectedPersona } : {})
    });
}

/**
 * Fetch history with optional search query
 * @param {string|null} searchQuery - Optional search query
 * @returns {Promise<Object>} History data
 */
async function fetchHistory(searchQuery = null) {
    const url = searchQuery
        ? `/history?q=${encodeURIComponent(searchQuery)}`
        : '/history';
    const response = await fetch(url);
    return await response.json();
}

/**
 * Delete a history item
 * @param {string|number} id - History item ID
 * @returns {Promise<Response>} Fetch response
 */
async function deleteHistoryItem(id) {
    return await fetch(`/history/${id}`, {
        method: 'DELETE'
    });
}
