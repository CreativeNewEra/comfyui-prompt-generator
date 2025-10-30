/**
 * Main Application Module
 * Initializes the application and handles core functionality
 */

// Global application state
let currentMode = 'oneshot';
let currentModel = 'flux';
let isStreaming = false;
let currentEventSource = null;
let streamingEnabled = false;

// History state
let historyData = [];
let searchTimeout = null;

// Initialize theme as early as possible
initializeTheme();
setupThemeListener();

/**
 * Initialize the application on DOM load
 */
window.addEventListener('DOMContentLoaded', async () => {
    console.log('Initializing ComfyUI Prompt Generator...');

    // Try to load hierarchical presets first
    try {
        await loadCategories();
        setupHierarchicalListeners();
        await loadUniversalOptions();
        await loadPresetPacks();
        console.log('Hierarchical presets loaded successfully');
    } catch (error) {
        console.log('Hierarchical presets not available, loading legacy presets');
    }

    // Load legacy presets as fallback
    try {
        const presetsData = await fetchPresets();
        presets = presetsData;

        if (presets.styles && presets.artists) {
            document.getElementById('legacyPresets').style.display = 'grid';
            document.querySelector('.presets-grid').style.display = 'none';

            populateSelect('styleSelect', presets.styles);
            populateSelect('artistSelect', presets.artists);
            populateSelect('compositionSelect', presets.composition);
            populateSelect('lightingSelect', presets.lighting);
        }

        initializeDefaultFavorites(presets);
        loadFavoritesFromStorage();
    } catch (error) {
        console.error('Failed to load presets:', error);
    }

    // Load Ollama models
    try {
        const modelsData = await fetchModels();
        const ollamaModelSelect = document.getElementById('ollamaModelSelect');

        ollamaModelSelect.innerHTML = '';

        if (modelsData.models && modelsData.models.length > 0) {
            modelsData.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                if (model === modelsData.default) {
                    option.selected = true;
                }
                ollamaModelSelect.appendChild(option);
            });
        } else {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No models found';
            ollamaModelSelect.appendChild(option);
        }
    } catch (error) {
        console.error('Failed to load Ollama models:', error);
        const ollamaModelSelect = document.getElementById('ollamaModelSelect');
        ollamaModelSelect.innerHTML = '<option value="">Error loading models</option>';
    }

    // Load personas
    try {
        const personasData = await fetch('/api/personas').then(r => r.json());
        const personaSelect = document.getElementById('personaSelect');

        // Keep the "None" option
        personaSelect.innerHTML = '<option value="">None (Standard)</option>';

        // Add each persona as an option
        for (const [id, persona] of Object.entries(personasData)) {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = `${persona.icon} ${persona.name} - ${persona.description.substring(0, 50)}...`;
            personaSelect.appendChild(option);
        }

        console.log(`Loaded ${Object.keys(personasData).length} personas`);
    } catch (error) {
        console.error('Failed to load personas:', error);
    }

    console.log('Application initialized successfully');
});

/**
 * Additional initialization after DOM content loaded
 */
document.addEventListener('DOMContentLoaded', () => {
    // Theme toggle button
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);

    // Save Favorite button
    document.getElementById('saveFavoriteBtn').addEventListener('click', () => {
        const name = prompt('Enter a name for this favorite:');
        if (name && name.trim() !== '') {
            saveFavorite(name.trim());
        }
    });

    // Initialize Quick Presets functionality
    initializeQuickPresets();

    // Mode switching
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMode = btn.dataset.mode;

            const resetBtn = document.getElementById('resetBtn');
            const chatHistory = document.getElementById('chatHistory');
            const inputLabel = document.getElementById('inputLabel');

            if (currentMode === 'chat') {
                resetBtn.style.display = 'block';
                inputLabel.textContent = 'Your message:';
            } else {
                resetBtn.style.display = 'none';
                chatHistory.classList.remove('visible');
                inputLabel.textContent = 'Describe what you want to generate:';
            }

            hideError();
            document.getElementById('userInput').value = '';
        });
    });

    // Model switching
    document.querySelectorAll('.model-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.model-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentModel = btn.dataset.model;
            hideError();
        });
    });

    // Streaming toggle
    document.getElementById('streamingToggle').addEventListener('change', (e) => {
        streamingEnabled = e.target.checked;
    });

    // Stop button
    document.getElementById('stopBtn').addEventListener('click', () => {
        stopStreaming();
    });

    // Generate button
    document.getElementById('generateBtn').addEventListener('click', handleGenerate);

    // Reset conversation
    document.getElementById('resetBtn').addEventListener('click', handleReset);

    // Copy button
    document.getElementById('copyBtn').addEventListener('click', copyOutputToClipboard);

    // Enter to submit (Ctrl+Enter for newline)
    document.getElementById('userInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.ctrlKey && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('generateBtn').click();
        }
    });

    // History button
    document.getElementById('historyBtn').addEventListener('click', toggleHistory);
    document.getElementById('historyCloseBtn').addEventListener('click', toggleHistory);

    // Close history when clicking overlay background
    document.getElementById('historyOverlay').addEventListener('click', (e) => {
        if (e.target.id === 'historyOverlay') {
            toggleHistory();
        }
    });

    // History search with debounce
    document.getElementById('historySearchInput').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();

        searchTimeout = setTimeout(() => {
            loadHistory(query || null);
        }, 300);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        if (e.key === 'h' || e.key === 'H') {
            e.preventDefault();
            toggleHistory();
        }

        if (e.key === 'Escape') {
            const overlay = document.getElementById('historyOverlay');
            if (overlay.classList.contains('visible')) {
                toggleHistory();
            }
        }
    });
});

/**
 * Handle generate button click
 */
async function handleGenerate() {
    const input = document.getElementById('userInput').value.trim();

    if (!input) {
        showError('Please enter a description or message!');
        return;
    }

    const ollamaModel = document.getElementById('ollamaModelSelect').value;
    const selectedPersona = document.getElementById('personaSelect').value;
    hideError();

    let basePayload = {
        model: currentModel,
        ollama_model: ollamaModel
    };

    // Add persona if selected
    if (selectedPersona) {
        basePayload.persona_id = selectedPersona;
    }

    // Add hierarchical selections if enabled
    const hierarchicalState = getHierarchicalState();
    if (hierarchicalState.enabled && (hierarchicalState.categoryId || hierarchicalState.typeId || hierarchicalState.artistId)) {
        basePayload.selections = {
            level1: hierarchicalState.categoryId,
            level2: hierarchicalState.typeId,
            level3: hierarchicalState.artistId
        };

        // Add universal options if any are selected
        const universalOptions = {};

        // Mood (multi-select)
        const moodSelect = document.getElementById('moodSelect');
        const selectedMoods = Array.from(moodSelect.selectedOptions).map(opt => opt.value).filter(v => v);
        if (selectedMoods.length > 0) {
            universalOptions.mood = selectedMoods;
        }

        // Time of day
        const timeOfDay = document.getElementById('timeOfDaySelect').value;
        if (timeOfDay) {
            universalOptions.time_of_day = timeOfDay;
        }

        // Lighting
        const lighting = document.getElementById('universalLightingSelect').value;
        if (lighting) {
            universalOptions.lighting = lighting;
        }

        // Weather
        const weather = document.getElementById('weatherSelect').value;
        if (weather) {
            universalOptions.weather_atmosphere = weather;
        }

        // Color palette
        const colorPalette = document.getElementById('colorPaletteSelect').value;
        if (colorPalette) {
            universalOptions.color_palette = colorPalette;
        }

        // Camera effects (multi-select)
        const cameraSelect = document.getElementById('cameraEffectsSelect');
        const selectedEffects = Array.from(cameraSelect.selectedOptions).map(opt => opt.value).filter(v => v);
        if (selectedEffects.length > 0) {
            universalOptions.camera_effects = selectedEffects;
        }

        if (Object.keys(universalOptions).length > 0) {
            basePayload.selections.universal = universalOptions;
            console.log('Adding universal options:', universalOptions);
        }

        console.log('Sending hierarchical selections:', basePayload.selections);
    } else {
        // Use legacy presets
        const style = document.getElementById('styleSelect').value;
        const artist = document.getElementById('artistSelect').value;
        const composition = document.getElementById('compositionSelect').value;
        const lighting = document.getElementById('lightingSelect').value;

        basePayload.style = style;
        basePayload.artist = artist;
        basePayload.composition = composition;
        basePayload.lighting = lighting;
    }

    const payload = currentMode === 'oneshot'
        ? { input: input, ...basePayload }
        : { message: input, ...basePayload };

    // Determine endpoint based on persona selection
    let streamingEndpoint, nonStreamingEndpoint;

    if (selectedPersona) {
        // Use persona endpoints if persona is selected
        streamingEndpoint = '/persona-chat-stream';
        nonStreamingEndpoint = '/persona-chat';
    } else {
        // Use standard endpoints
        streamingEndpoint = currentMode === 'oneshot' ? '/generate-stream' : '/chat-stream';
        nonStreamingEndpoint = currentMode === 'oneshot' ? '/generate' : '/chat';
    }

    // Check if streaming is enabled
    if (streamingEnabled) {
        await handleStreamingGeneration(streamingEndpoint, payload);
        return;
    }

    // Non-streaming mode
    await handleNonStreamingGeneration(payload, nonStreamingEndpoint);
}

/**
 * Handle streaming generation
 * @param {string} endpoint - API endpoint
 * @param {Object} payload - Request payload
 */
async function handleStreamingGeneration(endpoint, payload) {
    isStreaming = true;
    showStreamingIndicator();
    showStopButton();
    document.getElementById('userInput').disabled = true;
    hideError();

    let fullResponse = '';
    const outputDiv = document.getElementById('output');
    const outputArea = document.getElementById('outputArea');
    outputArea.classList.add('visible');
    outputDiv.classList.add('streaming');
    outputDiv.textContent = '';

    if (currentMode === 'chat') {
        const userInput = payload.message || payload.input;
        addChatMessage('user', userInput);
    }

    const onToken = (token, full) => {
        fullResponse = full;
        outputDiv.textContent = full;
        outputDiv.scrollTop = outputDiv.scrollHeight;
    };

    const onComplete = (full) => {
        isStreaming = false;
        outputDiv.classList.remove('streaming');

        if (currentMode === 'chat') {
            addChatMessage('assistant', full);
            document.getElementById('userInput').value = '';
        }
        stopStreaming();
    };

    const onError = async (error) => {
        const errorMsg = error.message || 'Streaming failed. Falling back to normal mode.';
        showError(errorMsg);
        outputDiv.classList.remove('streaming');

        if (!fullResponse.trim()) {
            try {
                showError('Streaming failed. Trying non-streaming mode...');
                await handleNonStreamingGeneration(payload);
            } catch (fallbackError) {
                showError('Failed to connect to server. Make sure Ollama is running!');
            }
        }
        stopStreaming();
    };

    await generateWithStreaming(endpoint, payload, onToken, onComplete, onError);
}

/**
 * Handle non-streaming generation
 * @param {Object} payload - Request payload
 */
async function handleNonStreamingGeneration(payload, endpoint) {
    showLoading();

    try {
        // Make the API call to the specified endpoint
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            // Check if using persona or chat mode
            if (currentMode === 'chat' || payload.persona_id) {
                addChatMessage('user', payload.message || payload.input);
                addChatMessage('assistant', data.result);
                document.getElementById('userInput').value = '';
            } else {
                showOutput(data.result);
            }
        } else {
            showError(data.error || data.message || 'Something went wrong!');
        }
    } catch (error) {
        console.error('Generation error:', error);
        showError('Failed to connect to server. Make sure Ollama is running!');
    } finally {
        hideLoading();
    }
}

/**
 * Handle reset button click
 */
async function handleReset() {
    if (confirm('Start a new conversation?')) {
        await resetConversation();
        document.getElementById('chatHistory').innerHTML = '';
        document.getElementById('chatHistory').classList.remove('visible');
        document.getElementById('userInput').value = '';
        document.getElementById('outputArea').classList.remove('visible');
        hideError();
    }
}

/**
 * Stop streaming
 */
function stopStreaming() {
    if (currentEventSource) {
        currentEventSource.close();
        currentEventSource = null;
    }
    isStreaming = false;
    hideStreamingIndicator();
    hideStopButton();
    hideLoading();
    document.getElementById('generateBtn').disabled = false;
    document.getElementById('userInput').disabled = false;
}

// History Management

/**
 * Load history from server
 * @param {string|null} searchQuery - Optional search query
 */
async function loadHistory(searchQuery = null) {
    try {
        const data = await fetchHistory(searchQuery);
        historyData = data.history || [];
        renderHistory();
    } catch (error) {
        console.error('Failed to load history:', error);
        document.getElementById('historyContent').innerHTML = `
            <div class="history-empty">
                <h3>Error loading history</h3>
                <p>Please try again later</p>
            </div>
        `;
    }
}

// Make loadHistory available globally for toggleHistory
window.loadHistory = loadHistory;

/**
 * Render history items
 */
function renderHistory() {
    const content = document.getElementById('historyContent');

    if (historyData.length === 0) {
        content.innerHTML = `
            <div class="history-empty">
                <h3>No history yet</h3>
                <p>Generated prompts will appear here</p>
            </div>
        `;
        return;
    }

    content.innerHTML = historyData.map(item => {
        const timestamp = new Date(item.timestamp).toLocaleString();
        const presetList = Object.entries(item.presets || {})
            .filter(([key, value]) => value && value !== 'None')
            .map(([key, value]) => value)
            .join(', ');

        return `
            <div class="history-item" data-id="${item.id}">
                <div class="history-item-header">
                    <div class="history-item-meta">
                        <span class="history-badge ${item.model}">${item.model.toUpperCase()}</span>
                        <span class="history-badge ${item.mode}">${item.mode === 'oneshot' ? '⚡ Quick' : '💬 Chat'}</span>
                        <span class="history-timestamp">${timestamp}</span>
                    </div>
                    <div class="history-item-actions">
                        <button class="history-btn history-btn-copy" onclick="copyHistoryItem('${item.id}')">
                            Copy
                        </button>
                        <button class="history-btn history-btn-delete" onclick="deleteHistoryItemUI('${item.id}')">
                            Delete
                        </button>
                    </div>
                </div>
                <div class="history-item-input">
                    <strong>Input:</strong>
                    ${escapeHtml(item.user_input)}
                </div>
                ${presetList ? `<div style="font-size: 0.85em; color: #666; margin-bottom: 10px;">Presets: ${escapeHtml(presetList)}</div>` : ''}
                <div class="history-item-output">
                    <strong>Generated Prompt:</strong>
                    ${escapeHtml(item.generated_output)}
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Copy a history item to clipboard
 * @param {string|number} id - History item ID
 */
async function copyHistoryItem(id) {
    const item = historyData.find(h => h.id == id);
    if (!item) return;

    try {
        await navigator.clipboard.writeText(item.generated_output);

        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        btn.style.background = '#20c997';

        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 2000);
    } catch (error) {
        console.error('Failed to copy:', error);
        alert('Failed to copy to clipboard');
    }
}

/**
 * Delete a history item
 * @param {string|number} id - History item ID
 */
async function deleteHistoryItemUI(id) {
    if (!confirm('Delete this history item?')) return;

    try {
        const response = await deleteHistoryItem(id);

        if (response.ok) {
            historyData = historyData.filter(h => h.id != id);
            renderHistory();
        } else {
            alert('Failed to delete history item');
        }
    } catch (error) {
        console.error('Failed to delete:', error);
        alert('Failed to delete history item');
    }
}

// Make functions available globally for onclick handlers
window.copyHistoryItem = copyHistoryItem;
window.deleteHistoryItemUI = deleteHistoryItemUI;
window.loadFavorite = loadFavorite;
window.handleDeleteFavorite = handleDeleteFavorite;
window.handleRenameFavorite = handleRenameFavorite;
