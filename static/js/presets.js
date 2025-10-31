/**
 * Preset System Module
 * Handles both legacy and hierarchical preset systems
 */

// Global preset state
let presets = {};
let favorites = [];
let hierarchicalEnabled = false;
let currentCategoryId = '';
let currentTypeId = '';
let currentArtistId = '';
let currentPresetPack = null;

// Legacy Presets

/**
 * Populate a select element with preset options
 * @param {string} selectId - ID of the select element
 * @param {Object} options - Preset options
 */
function populateSelect(selectId, options) {
    const select = document.getElementById(selectId);
    Object.keys(options).forEach(key => {
        if (key !== 'None') {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = key;
            select.appendChild(option);
        }
    });
}

/**
 * Get current preset selections
 * @returns {Object} Current preset values
 */
function getCurrentPresets() {
    return {
        style: document.getElementById('styleSelect').value,
        artist: document.getElementById('artistSelect').value,
        composition: document.getElementById('compositionSelect').value,
        lighting: document.getElementById('lightingSelect').value
    };
}

// Favorites Management

/**
 * Initialize default favorites if none exist
 * @param {Object} availablePresets - Available presets to validate against
 */
function initializeDefaultFavorites(availablePresets) {
    const categoryMap = {
        style: 'styles',
        artist: 'artists',
        composition: 'composition',
        lighting: 'lighting'
    };

    const isValidSelection = (category, value) => {
        if (!value || value === 'None') return true;
        const presetCategory = categoryMap[category];
        return (
            availablePresets &&
            availablePresets[presetCategory] &&
            Object.prototype.hasOwnProperty.call(availablePresets[presetCategory], value)
        );
    };

    const stored = localStorage.getItem('favoritePresets');

    if (stored) {
        try {
            const existingFavorites = JSON.parse(stored);
            const validExisting = existingFavorites.filter(favorite => {
                return Object.entries(favorite.presets).every(([category, value]) =>
                    isValidSelection(category, value)
                );
            });

            if (validExisting.length !== existingFavorites.length) {
                localStorage.setItem('favoritePresets', JSON.stringify(validExisting));
                favorites = validExisting;
            }
            return;
        } catch (error) {
            console.error('Error validating existing favorites:', error);
        }
    }

    const defaultFavoritesConfig = [
        {
            name: 'Synthwave Cityscape',
            presets: {
                style: 'Synthwave',
                artist: 'Beeple',
                composition: 'Panorama',
                lighting: 'Neon Lighting'
            }
        },
        {
            name: 'Impressionist Dawn',
            presets: {
                style: 'Impressionist',
                artist: 'Claude Monet',
                composition: 'Rule of Thirds',
                lighting: 'Soft Diffused'
            }
        },
        {
            name: 'Ghibli Adventure',
            presets: {
                style: 'Anime',
                artist: 'Hayao Miyazaki',
                composition: 'Wide Shot',
                lighting: 'Volumetric Lighting'
            }
        },
        {
            name: 'Studio Portrait Glow',
            presets: {
                style: 'Photorealistic',
                artist: 'Annie Leibovitz',
                composition: 'Portrait',
                lighting: 'Studio Lighting'
            }
        }
    ];

    const validDefaults = defaultFavoritesConfig.filter(favorite => {
        return Object.entries(favorite.presets).every(([category, value]) =>
            isValidSelection(category, value)
        );
    });

    favorites = validDefaults;
    localStorage.setItem('favoritePresets', JSON.stringify(validDefaults));
}

/**
 * Load favorites from localStorage
 */
function loadFavoritesFromStorage() {
    try {
        const stored = localStorage.getItem('favoritePresets');
        favorites = stored ? JSON.parse(stored) : [];
    } catch (error) {
        console.error('Failed to load favorites:', error);
        favorites = [];
    }
    renderFavorites();
}

/**
 * Save current presets as a favorite
 * @param {string} name - Name for the favorite
 */
function saveFavorite(name) {
    const currentPresets = getCurrentPresets();

    const hasPresets = Object.values(currentPresets).some(v => v && v !== 'None');
    if (!hasPresets) {
        alert('Please select at least one preset before saving!');
        return;
    }

    if (favorites.some(f => f.name === name)) {
        alert('A favorite with this name already exists!');
        return;
    }

    const favorite = {
        name: name,
        presets: currentPresets
    };

    favorites.push(favorite);
    localStorage.setItem('favoritePresets', JSON.stringify(favorites));
    renderFavorites();
}

/**
 * Load a favorite preset configuration
 * @param {string} name - Name of the favorite to load
 */
function loadFavorite(name) {
    const favorite = favorites.find(f => f.name === name);
    if (!favorite) return;

    const selects = ['styleSelect', 'artistSelect', 'compositionSelect', 'lightingSelect'];
    const presetKeys = ['style', 'artist', 'composition', 'lighting'];

    selects.forEach((selectId, index) => {
        const select = document.getElementById(selectId);
        const value = favorite.presets[presetKeys[index]] || 'None';
        select.value = value;

        select.classList.add('animating');
        setTimeout(() => select.classList.remove('animating'), 600);

        syncQuickPresetButtons(presetKeys[index], value);
    });
}

/**
 * Delete a favorite
 * @param {string} name - Name of the favorite to delete
 */
function deleteFavorite(name) {
    favorites = favorites.filter(f => f.name !== name);
    localStorage.setItem('favoritePresets', JSON.stringify(favorites));
    renderFavorites();
}

/**
 * Rename a favorite
 * @param {string} oldName - Current name
 * @param {string} newName - New name
 */
function renameFavorite(oldName, newName) {
    if (!newName || newName.trim() === '') return;

    const favorite = favorites.find(f => f.name === oldName);
    if (!favorite) return;

    if (favorites.some(f => f.name === newName && f.name !== oldName)) {
        alert('A favorite with this name already exists!');
        return;
    }

    favorite.name = newName;
    localStorage.setItem('favoritePresets', JSON.stringify(favorites));
    renderFavorites();
}

/**
 * Render favorites chips in the UI
 */
function renderFavorites() {
    const container = document.getElementById('favoritesChips');

    if (favorites.length === 0) {
        container.innerHTML = '<span class="favorites-empty">No favorites yet. Select presets and click "Save Current" to create one!</span>';
        return;
    }

    container.innerHTML = favorites.map(fav => `
        <div class="favorite-chip" onclick="loadFavorite('${escapeAttribute(fav.name)}')">
            <span class="favorite-chip-name">${escapeHtml(fav.name)}</span>
            <div class="favorite-chip-actions">
                <button class="favorite-chip-btn rename" onclick="event.stopPropagation(); handleRenameFavorite('${escapeAttribute(fav.name)}')" title="Rename">✏️</button>
                <button class="favorite-chip-btn delete" onclick="event.stopPropagation(); handleDeleteFavorite('${escapeAttribute(fav.name)}')" title="Delete">×</button>
            </div>
        </div>
    `).join('');
}

/**
 * Handle delete favorite button click
 * @param {string} name - Name of favorite to delete
 */
function handleDeleteFavorite(name) {
    if (confirm(`Delete favorite "${name}"?`)) {
        deleteFavorite(name);
    }
}

/**
 * Handle rename favorite button click
 * @param {string} oldName - Current name of favorite
 */
function handleRenameFavorite(oldName) {
    const newName = prompt(`Rename favorite:`, oldName);
    if (newName && newName.trim() !== '') {
        renameFavorite(oldName, newName.trim());
    }
}

// Quick Presets

/**
 * Initialize quick preset buttons
 */
function initializeQuickPresets() {
    const quickPresetButtons = document.querySelectorAll('.quick-preset-btn');
    const categoryToSelectMap = {
        'style': 'styleSelect',
        'artist': 'artistSelect',
        'composition': 'compositionSelect',
        'lighting': 'lightingSelect'
    };

    quickPresetButtons.forEach(button => {
        button.addEventListener('click', () => {
            const category = button.dataset.category;
            const value = button.dataset.value;
            const selectId = categoryToSelectMap[category];
            const select = document.getElementById(selectId);

            const isActive = button.classList.contains('active');

            const categoryButtons = document.querySelectorAll(`.quick-preset-btn[data-category="${category}"]`);
            categoryButtons.forEach(btn => btn.classList.remove('active'));

            if (isActive) {
                select.value = 'None';
            } else {
                select.value = value;
                button.classList.add('active');
            }

            select.classList.add('animating');
            setTimeout(() => select.classList.remove('animating'), 600);
        });
    });

    Object.entries(categoryToSelectMap).forEach(([category, selectId]) => {
        const select = document.getElementById(selectId);
        select.addEventListener('change', () => {
            syncQuickPresetButtons(category, select.value);
        });
    });
}

/**
 * Sync quick preset button states with dropdown values
 * @param {string} category - Preset category
 * @param {string} value - Selected value
 */
function syncQuickPresetButtons(category, value) {
    const categoryButtons = document.querySelectorAll(`.quick-preset-btn[data-category="${category}"]`);

    categoryButtons.forEach(button => {
        if (button.dataset.value === value && value !== 'None') {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
}

// Hierarchical Presets

/**
 * Load hierarchical categories
 */
async function loadCategories() {
    try {
        const data = await fetchCategories();

        const categorySelect = document.getElementById('categorySelect');
        categorySelect.innerHTML = '<option value="">None</option>';

        data.categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.id;
            option.textContent = `${cat.icon} ${cat.name}`;
            categorySelect.appendChild(option);
        });

        hierarchicalEnabled = true;
    } catch (error) {
        console.error('Hierarchical presets not available, using legacy:', error);
        hierarchicalEnabled = false;
    }
}

/**
 * Load types for selected category
 * @param {string} categoryId - Category ID
 */
async function loadTypes(categoryId) {
    const typeSelect = document.getElementById('typeSelect');
    const artistSelect = document.getElementById('artistStyleSelect');

    if (!categoryId) {
        typeSelect.innerHTML = '<option value="">Select category first</option>';
        typeSelect.disabled = true;
        artistSelect.innerHTML = '<option value="">Select type first</option>';
        artistSelect.disabled = true;
        return;
    }

    try {
        const data = await fetchTypes(categoryId);

        typeSelect.innerHTML = '<option value="">None</option>';
        data.types.forEach(type => {
            const option = document.createElement('option');
            option.value = type.id;
            option.textContent = `${type.icon} ${type.name}`;
            typeSelect.appendChild(option);
        });

        typeSelect.disabled = false;
        artistSelect.innerHTML = '<option value="">Select type first</option>';
        artistSelect.disabled = true;
    } catch (error) {
        console.error('Failed to load types:', error);
        typeSelect.innerHTML = '<option value="">Error loading types</option>';
    }
}

/**
 * Load artists for selected type
 * @param {string} categoryId - Category ID
 * @param {string} typeId - Type ID
 */
async function loadArtists(categoryId, typeId) {
    const artistSelect = document.getElementById('artistStyleSelect');

    if (!typeId) {
        artistSelect.innerHTML = '<option value="">Select type first</option>';
        artistSelect.disabled = true;
        return;
    }

    try {
        const data = await fetchArtists(categoryId, typeId);

        artistSelect.innerHTML = '<option value="">None</option>';
        data.artists.forEach(artist => {
            const option = document.createElement('option');
            option.value = artist.id;
            option.textContent = artist.name;
            if (artist.popularity === 'high') {
                option.textContent += ' 🔥';
            }
            artistSelect.appendChild(option);
        });

        artistSelect.disabled = false;
    } catch (error) {
        console.error('Failed to load artists:', error);
        artistSelect.innerHTML = '<option value="">Error loading artists</option>';
    }
}

/**
 * Load universal options
 */
async function loadUniversalOptions() {
    try {
        const data = await fetchUniversalOptions();
        const universal = data?.universal_options || {};

        // Mood
        const moodSelect = document.getElementById('moodSelect');
        moodSelect.innerHTML = '';
        const moodOptions = Array.isArray(universal.mood?.core)
            ? universal.mood.core
            : [];
        moodOptions.forEach(mood => {
            const option = document.createElement('option');
            option.value = mood.id || mood.name || mood;
            option.textContent = mood.name || mood;
            moodSelect.appendChild(option);
        });

        // Time of Day
        const timeSelect = document.getElementById('timeOfDaySelect');
        timeSelect.innerHTML = '<option value="">None</option>';
        const timeOptions = Array.isArray(universal.time_of_day?.options)
            ? universal.time_of_day.options
            : [];
        timeOptions.forEach(time => {
            const option = document.createElement('option');
            option.value = time.id || time.name || time;
            option.textContent = time.name || time;
            timeSelect.appendChild(option);
        });

        // Lighting
        const lightingSelect = document.getElementById('universalLightingSelect');
        lightingSelect.innerHTML = '<option value="">None</option>';
        const lightingOptions = Array.isArray(universal.lighting?.core)
            ? universal.lighting.core
            : [];
        lightingOptions.forEach(light => {
            const option = document.createElement('option');
            option.value = light.id || light.name || light;
            option.textContent = light.name || light;
            if (light.popularity === 'high') {
                option.textContent += ' 🔥';
            }
            lightingSelect.appendChild(option);
        });

        // Weather/Atmosphere
        const weatherSelect = document.getElementById('weatherSelect');
        weatherSelect.innerHTML = '<option value="">None</option>';
        const weatherOptions = Array.isArray(universal.weather_atmosphere?.options)
            ? universal.weather_atmosphere.options
            : [];
        weatherOptions.forEach(weather => {
            const option = document.createElement('option');
            option.value = weather.id || weather.name || weather;
            option.textContent = weather.name || weather;
            weatherSelect.appendChild(option);
        });

        // Color Palettes
        const colorSelect = document.getElementById('colorPaletteSelect');
        colorSelect.innerHTML = '<option value="">None</option>';
        const colorPaletteOptions = Array.isArray(universal.color_palettes?.universal)
            ? universal.color_palettes.universal
            : Array.isArray(universal.color_palettes?.options)
                ? universal.color_palettes.options
                : [];
        colorPaletteOptions.forEach(color => {
            const option = document.createElement('option');
            option.value = color.id || color.name || color;
            option.textContent = color.name || color;
            colorSelect.appendChild(option);
        });

        // Camera Effects
        const cameraSelect = document.getElementById('cameraEffectsSelect');
        cameraSelect.innerHTML = '';
        const cameraOptions = Array.isArray(universal.camera_effects?.options)
            ? universal.camera_effects.options
            : [];
        if (cameraOptions.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'None';
            cameraSelect.appendChild(option);
        } else {
            cameraOptions.forEach(effect => {
                const option = document.createElement('option');
                option.value = effect.id || effect.name || effect;
                option.textContent = effect.name || effect;
                cameraSelect.appendChild(option);
            });
        }

        document.getElementById('universalOptionsSection').style.display = 'block';
        console.log('Universal options loaded successfully');
    } catch (error) {
        console.error('Failed to load universal options:', error);
    }
}

/**
 * Load preset packs
 */
async function loadPresetPacks() {
    try {
        const data = await fetchPresetPacks();
        const packs = Array.isArray(data?.packs) ? data.packs : [];

        const container = document.getElementById('presetPacksContainer');
        container.innerHTML = '';

        if (packs.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'preset-pack-empty';
            emptyState.textContent = data?.error
                ? 'Preset packs are unavailable. Enable hierarchical presets to view them.'
                : 'No preset packs available yet.';
            container.appendChild(emptyState);
        } else {
            packs.forEach(pack => {
                const btn = document.createElement('button');
                btn.className = 'preset-pack-btn';
                const iconDiv = document.createElement('div');
                iconDiv.className = 'preset-pack-icon';
                iconDiv.textContent = pack.icon;
                const nameDiv = document.createElement('div');
                nameDiv.className = 'preset-pack-name';
                nameDiv.textContent = pack.name;
                btn.appendChild(iconDiv);
                btn.appendChild(nameDiv);
                btn.onclick = () => applyPresetPack(pack);
                container.appendChild(btn);
            });
        }

        document.getElementById('presetPacksSection').style.display = 'block';
        console.log(`Loaded ${packs.length} preset packs`);
    } catch (error) {
        console.error('Failed to load preset packs:', error);
    }
}

/**
 * Apply a preset pack
 * @param {Object} pack - Preset pack configuration
 */
async function applyPresetPack(pack) {
    currentPresetPack = pack;

    document.querySelectorAll('.preset-pack-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    event.target.closest('.preset-pack-btn').classList.add('active');

    const sel = pack.selections;

    if (sel.level1) {
        document.getElementById('categorySelect').value = sel.level1;
        currentCategoryId = sel.level1;
        await loadTypes(sel.level1);
    }

    if (sel.level2) {
        await new Promise(resolve => setTimeout(resolve, 100));
        document.getElementById('typeSelect').value = sel.level2;
        currentTypeId = sel.level2;
        await loadArtists(sel.level1, sel.level2);
    }

    if (sel.level3) {
        await new Promise(resolve => setTimeout(resolve, 100));
        document.getElementById('artistStyleSelect').value = sel.level3;
        currentArtistId = sel.level3;
    }

    console.log(`Applied preset pack: ${pack.name}`);
}

/**
 * Set up cascading dropdown listeners for hierarchical presets
 */
function setupHierarchicalListeners() {
    const categorySelect = document.getElementById('categorySelect');
    const typeSelect = document.getElementById('typeSelect');

    categorySelect.addEventListener('change', async (e) => {
        currentCategoryId = e.target.value;
        currentTypeId = '';
        currentArtistId = '';
        await loadTypes(currentCategoryId);
    });

    typeSelect.addEventListener('change', async (e) => {
        currentTypeId = e.target.value;
        currentArtistId = '';
        await loadArtists(currentCategoryId, currentTypeId);
    });

    document.getElementById('artistStyleSelect').addEventListener('change', (e) => {
        currentArtistId = e.target.value;
    });
}

/**
 * Get hierarchical preset state
 * @returns {Object} Current hierarchical preset state
 */
function getHierarchicalState() {
    return {
        enabled: hierarchicalEnabled,
        categoryId: currentCategoryId,
        typeId: currentTypeId,
        artistId: currentArtistId
    };
}
