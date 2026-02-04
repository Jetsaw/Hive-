/**
 * Theme Utility Module
 * Manages light/dark theme switching
 */

import { getTheme, setTheme } from '../services/storage.js';

/**
 * Load theme from storage and apply
 */
export function loadTheme() {
    const theme = getTheme();
    document.body.setAttribute('data-theme', theme);
    updateThemeIcon(theme);
}

/**
 * Toggle between light and dark theme
 */
export function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.body.setAttribute('data-theme', newTheme);
    setTheme(newTheme);
    updateThemeIcon(newTheme);
}

/**
 * Update theme toggle button icon
 * @param {string} theme - Current theme
 */
function updateThemeIcon(theme) {
    // Icons are managed via CSS (sun-icon/moon-icon classes)
    // No additional logic needed
}
