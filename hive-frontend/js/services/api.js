/**
 * API Service Module
 * Handles all API communications with error handling and automatic retries
 */

import { API_BASE } from '../config.js';

/**
 * Retry a fetch request with exponential backoff
 */
async function fetchWithRetry(url, options, maxRetries = 3) {
    let lastError;
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response;
        } catch (error) {
            lastError = error;
            if (error.name === 'AbortError') throw error;
            if (attempt < maxRetries) {
                const delay = Math.pow(2, attempt + 1) * 1000;
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
    throw lastError;
}

/**
 * Send a chat message to the backend (with retry)
 */
export async function sendChatMessage(userId, message) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    try {
        const response = await fetchWithRetry(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, message }),
            signal: controller.signal
        }, 3);

        clearTimeout(timeoutId);
        const data = await response.json();
        const responseMessage = data.response || data.answer;
        if (!responseMessage) {
            throw new Error('Invalid response format');
        }
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
 */
export async function resetSession(userId) {
    const response = await fetch(`${API_BASE}/session/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    });
    if (!response.ok) throw new Error('Failed to reset session');
    return await response.json();
}

/**
 * Get session status
 */
export async function getSessionStatus(userId) {
    const response = await fetch(`${API_BASE}/session/status?user_id=${userId}`);
    if (!response.ok) throw new Error('Failed to get session status');
    return await response.json();
}

/**
 * Get smart suggestions based on last question
 */
export async function getSuggestions(question, answer, programme) {
    try {
        const response = await fetch(`${API_BASE}/suggestions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, answer, programme })
        });
        if (!response.ok) return { suggestions: [] };
        return await response.json();
    } catch {
        return { suggestions: [] };
    }
}

/**
 * Get default suggestion chips
 */
export async function getDefaultSuggestions() {
    try {
        const response = await fetch(`${API_BASE}/suggestions/default`);
        if (!response.ok) return { suggestions: [] };
        return await response.json();
    } catch {
        return { suggestions: [] };
    }
}

/**
 * Export conversation
 */
export async function exportConversation(userId, format) {
    const response = await fetch(`${API_BASE}/conversation/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, format })
    });
    if (!response.ok) throw new Error('Export failed');
    return response;
}

/**
 * Submit feedback
 */
export async function submitFeedback(rating, comment, userId) {
    const response = await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating, comment, user_id: userId })
    });
    if (!response.ok) throw new Error('Feedback submission failed');
    return await response.json();
}

/**
 * Get calendar summary
 */
export async function getCalendarSummary() {
    try {
        const response = await fetch(`${API_BASE}/calendar/summary`);
        if (!response.ok) return null;
        return await response.json();
    } catch {
        return null;
    }
}

/**
 * Get upcoming calendar events
 */
export async function getCalendarUpcoming() {
    try {
        const response = await fetch(`${API_BASE}/calendar/upcoming`);
        if (!response.ok) return [];
        return await response.json();
    } catch {
        return [];
    }
}

/**
 * Compare two programmes
 */
export async function compareCourses(course1, course2) {
    try {
        const params = new URLSearchParams({ course1, course2 });
        const response = await fetch(`${API_BASE}/courses/compare?${params}`);
        if (!response.ok) return null;
        return await response.json();
    } catch {
        return null;
    }
}

/**
 * Get study groups
 */
export async function getStudyGroups(courseCode) {
    try {
        const url = courseCode
            ? `${API_BASE}/study-groups?course_code=${courseCode}`
            : `${API_BASE}/study-groups`;
        const response = await fetch(url);
        if (!response.ok) return [];
        return await response.json();
    } catch {
        return [];
    }
}
