/**
 * API Service Module
 * Handles all API communications with error handling and retries
 */

import { API_BASE } from '../config.js';

/**
 * Send a chat message to the backend
 * @param {string} userId - User ID
 * @param {string} message - Message text
 * @returns {Promise<Object>} API response
 */
export async function sendChatMessage(userId, message) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, message }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Validate response - accept both 'response' (new) and 'answer' (legacy) fields
        const responseMessage = data.response || data.answer;
        if (!responseMessage) {
            throw new Error('Invalid response format');
        }

        // Normalize to 'answer' field for backwards compatibility
        return { ...data, answer: responseMessage };

    } catch (error) {
        clearTimeout(timeoutId);

        if (error.name === 'AbortError') {
            throw new Error('Request timed out. Please try again.');
        } else if (error.message.includes('Failed to fetch')) {
            throw new Error('Network error. Please check your connection.');
        } else {
            throw error;
        }
    }
}

/**
 * Reset user session
 * @param {string} userId - User ID
 * @returns {Promise<Object>} API response
 */
export async function resetSession(userId) {
    const response = await fetch(`${API_BASE}/session/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    });

    if (!response.ok) {
        throw new Error('Failed to reset session');
    }

    return await response.json();
}

/**
 * Get session status
 * @param {string} userId - User ID
 * @returns {Promise<Object>} Session status
 */
export async function getSessionStatus(userId) {
    const response = await fetch(`${API_BASE}/session/status?user_id=${userId}`);

    if (!response.ok) {
        throw new Error('Failed to get session status');
    }

    return await response.json();
}
