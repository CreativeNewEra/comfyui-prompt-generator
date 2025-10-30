/**
 * UI Helper Functions Module
 * Manages all UI interactions, theme, notifications, and visual feedback
 */

// Theme Management

/**
 * Get the system's preferred color scheme
 * @returns {string} 'dark' or 'light'
 */
function getSystemTheme() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

/**
 * Get the stored theme preference from localStorage
 * @returns {string|null} Stored theme or null
 */
function getStoredTheme() {
    return localStorage.getItem('theme');
}

/**
 * Set and persist the theme
 * @param {string} theme - 'dark' or 'light'
 */
function setTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateThemeIcon(theme);
}

/**
 * Update the theme toggle icon
 * @param {string} theme - Current theme
 */
function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('themeIcon');
    themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

/**
 * Toggle between light and dark themes
 */
function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

/**
 * Initialize theme on page load
 */
function initializeTheme() {
    const storedTheme = getStoredTheme();
    const theme = storedTheme || getSystemTheme();
    setTheme(theme);
}

/**
 * Listen for system theme changes
 */
function setupThemeListener() {
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!getStoredTheme()) {
                setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
}

// Loading and Error States

/**
 * Show loading indicator
 */
function showLoading() {
    document.getElementById('loading').classList.add('visible');
    document.getElementById('generateBtn').disabled = true;
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    document.getElementById('loading').classList.remove('visible');
    document.getElementById('generateBtn').disabled = false;
}

/**
 * Show streaming indicator
 */
function showStreamingIndicator() {
    document.getElementById('streamingIndicator').classList.add('visible');
    document.getElementById('loading').classList.remove('visible');
}

/**
 * Hide streaming indicator
 */
function hideStreamingIndicator() {
    document.getElementById('streamingIndicator').classList.remove('visible');
}

/**
 * Show stop button and hide generate button
 */
function showStopButton() {
    document.getElementById('stopBtn').classList.add('visible');
    document.getElementById('generateBtn').style.display = 'none';
}

/**
 * Hide stop button and show generate button
 */
function hideStopButton() {
    document.getElementById('stopBtn').classList.remove('visible');
    document.getElementById('generateBtn').style.display = 'block';
}

/**
 * Show error message
 * @param {string} message - Error message to display
 */
function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.classList.add('visible');
}

/**
 * Hide error message
 */
function hideError() {
    document.getElementById('error').classList.remove('visible');
}

// Output Display

/**
 * Show output text
 * @param {string} text - Text to display
 */
function showOutput(text) {
    document.getElementById('output').textContent = text;
    document.getElementById('outputArea').classList.add('visible');
}

/**
 * Add a message to the chat history
 * @param {string} role - 'user' or 'assistant'
 * @param {string} content - Message content
 */
function addChatMessage(role, content) {
    const chatHistory = document.getElementById('chatHistory');
    chatHistory.classList.add('visible');

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    const roleDiv = document.createElement('div');
    roleDiv.className = 'role';
    roleDiv.textContent = role === 'user' ? '👤 You' : '🤖 Assistant';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';
    contentDiv.textContent = content;

    messageDiv.appendChild(roleDiv);
    messageDiv.appendChild(contentDiv);

    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    if (role === 'assistant') {
        showOutput(content);
    }
}

// Copy to Clipboard

/**
 * Copy output to clipboard with visual feedback
 */
async function copyOutputToClipboard() {
    const output = document.getElementById('output').textContent;
    try {
        await navigator.clipboard.writeText(output);
        const btn = document.getElementById('copyBtn');
        btn.textContent = '✓ Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = 'Copy';
            btn.classList.remove('copied');
        }, 2000);
    } catch (error) {
        console.error('Failed to copy:', error);
        alert('Failed to copy to clipboard');
    }
}

// Modal/History Overlay

/**
 * Toggle history modal visibility
 */
function toggleHistory() {
    const overlay = document.getElementById('historyOverlay');
    const isVisible = overlay.classList.contains('visible');

    if (isVisible) {
        overlay.classList.remove('visible');
    } else {
        overlay.classList.add('visible');
        // Trigger history load (handled in main.js)
        if (window.loadHistory) {
            window.loadHistory();
        }
    }
}

// Utility Functions

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Escape single quotes for HTML attributes
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeAttribute(str) {
    return str.replace(/'/g, "\\'");
}

/**
 * Add animation class to element temporarily
 * @param {HTMLElement} element - Element to animate
 * @param {string} className - Animation class name
 * @param {number} duration - Duration in milliseconds
 */
function addTemporaryAnimation(element, className, duration = 600) {
    element.classList.add(className);
    setTimeout(() => element.classList.remove(className), duration);
}
