/**
 * LocalStorage Service Module
 * Manages browser storage for user data and settings
 */

import { USER_ID_KEY, VOICE_SETTINGS_KEY } from '../config.js';

/**
 * Get or create user ID
 * @returns {string} User ID
 */
export function getUserId() {
    let userId = localStorage.getItem(USER_ID_KEY);
    if (!userId) {
        userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem(USER_ID_KEY, userId);
    }
    return userId;
}

/**
 * Get voice settings from localStorage
 * @returns {Object} Voice settings
 */
export function getVoiceSettings() {
    const stored = localStorage.getItem(VOICE_SETTINGS_KEY);
    if (stored) {
        try {
            return JSON.parse(stored);
        } catch (e) {
            console.error('Failed to parse voice settings:', e);
        }
    }

    // Default settings
    return {
        default_voice: 'female_en',
        provider: 'browser',
        auto_play: true
    };
}

/**
 * Save voice settings to localStorage
 * @param {Object} settings - Voice settings
 */
export function setVoiceSettings(settings) {
    localStorage.setItem(VOICE_SETTINGS_KEY, JSON.stringify(settings));
}

/**
 * Get theme preference
 * @returns {string} Theme ('light' or 'dark')
 */
export function getTheme() {
    return localStorage.getItem('hive_theme') || 'dark';
}

/**
 * Save theme preference
 * @param {string} theme - Theme name
 */
export function setTheme(theme) {
    localStorage.setItem('hive_theme', theme);
}
