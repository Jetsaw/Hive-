/**
 * HIVE Main Application Entry Point
 * Orchestrates all components and modules
 */

import { API_BASE, USER_ID_KEY, VOICE_SETTINGS_KEY } from './config.js';
import { loadTheme, toggleTheme } from './utils/theme.js';
import { sendChatMessage, getSuggestions, exportConversation, submitFeedback, getCalendarSummary, getCalendarUpcoming, compareCourses } from './services/api.js';
import { startVoiceRecording, stopVoiceRecording, speakText, initVoiceSettings } from './services/voice.js';
import { getUserId, getVoiceSettings } from './services/storage.js';
import { addMessage, addTypingIndicator, removeMessage, scrollToBottom, addSuggestionChips } from './components/ChatArea.js';
import { initSidebar } from './components/Sidebar.js';
import { t, initI18n, toggleLanguage, getLanguage } from './i18n.js';

// App State
let isRecording = false;
let wasLastInputVoice = false;
let lastQuestion = '';

// DOM Elements
let messageInput;
let sendBtn;
let voiceBtn;
let themeToggleBtn;
let newChatBtn;
let charCounter;
let welcomeScreen;
let statusBadge;

/**
 * Initialize the application
 */
function init() {
    // Get DOM elements
    messageInput = document.getElementById('messageInput');
    sendBtn = document.getElementById('sendBtn');
    voiceBtn = document.getElementById('voiceBtn');
    themeToggleBtn = document.getElementById('themeToggle');
    newChatBtn = document.getElementById('newChatBtn');
    charCounter = document.getElementById('charCounter');
    welcomeScreen = document.getElementById('welcomeScreen');
    statusBadge = document.getElementById('statusBadge');

    // Initialize theme
    loadTheme();

    // Initialize sidebar
    initSidebar();

    // Initialize voice settings
    initVoiceSettings();

    // Initialize i18n
    initI18n();

    // Attach event listeners
    setupEventListeners();

    // Auto-resize textarea
    messageInput.addEventListener('input', () => {
        autoResize();
        updateCharCounter();
    });

    // Setup quick question cards
    setupQuickQuestions();

    // Register service worker for PWA
    registerServiceWorker();

    // Restore chat history from localStorage
    restoreChatHistory();

    // Initial focus
    messageInput.focus();

    console.log('HIVE v3.0 initialized successfully');
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    sendBtn.addEventListener('click', handleSendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    voiceBtn.addEventListener('click', handleVoiceToggle);
    themeToggleBtn.addEventListener('click', () => toggleTheme());
    newChatBtn.addEventListener('click', handleNewChat);

    // Language toggle
    const langBtn = document.getElementById('langToggle');
    if (langBtn) {
        langBtn.addEventListener('click', () => {
            const newLang = toggleLanguage();
            langBtn.textContent = newLang.toUpperCase();
        });
        langBtn.textContent = getLanguage().toUpperCase();
    }

    // Export buttons
    document.getElementById('exportBtn')?.addEventListener('click', () => showModal('exportModal'));
    document.querySelectorAll('[data-export]').forEach(btn => {
        btn.addEventListener('click', () => handleExport(btn.dataset.export));
    });

    // Feedback button
    document.getElementById('feedbackBtn')?.addEventListener('click', () => showModal('feedbackModal'));
    document.getElementById('submitFeedbackBtn')?.addEventListener('click', handleFeedback);

    // Calendar button
    document.getElementById('calendarBtn')?.addEventListener('click', handleShowCalendar);

    // Comparison button
    document.getElementById('compareBtn')?.addEventListener('click', handleShowComparison);

    // Modal close
    document.querySelectorAll('.modal-close, .modal-overlay').forEach(el => {
        el.addEventListener('click', (e) => {
            if (e.target === el) {
                el.closest('.modal-overlay')?.classList.add('hidden');
            }
        });
    });

    // Feedback stars
    document.querySelectorAll('.star-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const rating = parseInt(btn.dataset.rating);
            document.querySelectorAll('.star-btn').forEach((s, i) => {
                s.classList.toggle('active', i < rating);
            });
            document.getElementById('feedbackRating').value = rating;
        });
    });

    // Online status
    window.addEventListener('online', () => updateOnlineStatus(true));
    window.addEventListener('offline', () => updateOnlineStatus(false));
}

/**
 * Handle sending a message
 */
async function handleSendMessage(text) {
    const messageText = typeof text === 'string' ? text : messageInput.value.trim();
    if (!messageText) return;

    // Hide welcome screen if visible
    if (welcomeScreen && !welcomeScreen.classList.contains('hidden')) {
        welcomeScreen.classList.add('hidden');
    }

    // Remove existing suggestion chips
    const existingChips = document.querySelector('.suggestion-chips');
    if (existingChips) existingChips.remove();

    addMessage('user', messageText);
    lastQuestion = messageText;

    // Save to local chat history
    saveChatMessage('user', messageText);

    messageInput.value = '';
    autoResize();
    updateCharCounter();
    scrollToBottom();

    const typingId = addTypingIndicator();

    try {
        const response = await sendChatMessage(getUserId(), messageText);
        removeMessage(typingId);
        addMessage('assistant', response.answer);
        saveChatMessage('assistant', response.answer);

        // Fetch and show suggestion chips
        const suggestions = await getSuggestions(messageText, response.answer);
        if (suggestions.suggestions && suggestions.suggestions.length > 0) {
            addSuggestionChips(suggestions.suggestions, (chipText) => {
                handleSendMessage(chipText);
            });
        }

        // Speak if voice input was used
        const voiceSettings = getVoiceSettings();
        if (wasLastInputVoice && voiceSettings.auto_play) {
            speakText(response.answer);
        }
        wasLastInputVoice = false;

    } catch (error) {
        removeMessage(typingId);
        addMessage('assistant', t('error_message'));
        console.error('Chat error:', error);
    }

    scrollToBottom();
}

/**
 * Setup quick question cards on welcome screen
 */
function setupQuickQuestions() {
    const quickQuestions = document.querySelectorAll('.quick-question');
    quickQuestions.forEach(card => {
        card.addEventListener('click', () => {
            const question = card.dataset.question || card.textContent.trim();
            handleSendMessage(question);
        });
    });
}

/**
 * Handle voice recording toggle
 */
async function handleVoiceToggle() {
    if (isRecording) {
        isRecording = false;
        voiceBtn.classList.remove('recording');
        try {
            const transcript = await stopVoiceRecording();
            if (transcript) {
                messageInput.value = transcript;
                wasLastInputVoice = true;
                autoResize();
                updateCharCounter();
                handleSendMessage();
            }
        } catch (error) {
            console.error('Voice recording error:', error);
        }
    } else {
        isRecording = true;
        voiceBtn.classList.add('recording');
        try {
            await startVoiceRecording();
        } catch (error) {
            console.error('Voice recording start error:', error);
            isRecording = false;
            voiceBtn.classList.remove('recording');
        }
    }
}

/**
 * Handle new chat/reset session
 */
async function handleNewChat() {
    if (!confirm(t('new_chat_confirm'))) return;

    try {
        const userId = getUserId();
        const response = await fetch(`${API_BASE}/session/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });

        if (response.ok) {
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = '';

            const welcomeHTML = `
                <div class="welcome-screen" id="welcomeScreen">
                    <div class="welcome-logo" role="img" aria-label="Hive Logo">
                        <img src="./assets/logo.png" alt="HIVE Logo">
                    </div>
                    <h1 class="welcome-text" data-i18n="welcome_title">${t('welcome_title')}</h1>
                    <p class="welcome-subtitle" data-i18n="welcome_subtitle">${t('welcome_subtitle')}</p>
                    <div class="quick-questions-grid">
                        <button class="quick-question" data-question="${t('quick_q1')}">${t('quick_q1')}</button>
                        <button class="quick-question" data-question="${t('quick_q2')}">${t('quick_q2')}</button>
                        <button class="quick-question" data-question="${t('quick_q3')}">${t('quick_q3')}</button>
                        <button class="quick-question" data-question="${t('quick_q4')}">${t('quick_q4')}</button>
                    </div>
                </div>
            `;
            chatMessages.innerHTML = welcomeHTML;
            welcomeScreen = document.getElementById('welcomeScreen');

            setupQuickQuestions();
            clearChatHistory();

            messageInput.value = '';
            autoResize();
            updateCharCounter();
            messageInput.focus();
        }
    } catch (error) {
        console.error('Reset session error:', error);
    }
}

/**
 * Export conversation handler
 */
async function handleExport(format) {
    try {
        const response = await exportConversation(getUserId(), format);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `hive_chat.${format}`;
        a.click();
        URL.revokeObjectURL(url);
        hideModal('exportModal');
        showToast(t('export_success'));
    } catch (error) {
        showToast('Export failed. Please try again.', 'error');
    }
}

/**
 * Feedback submission handler
 */
async function handleFeedback() {
    const rating = parseInt(document.getElementById('feedbackRating')?.value || '0');
    const comment = document.getElementById('feedbackComment')?.value || '';

    if (rating < 1 || rating > 5) {
        showToast('Please select a rating', 'error');
        return;
    }

    try {
        await submitFeedback(rating, comment, getUserId());
        hideModal('feedbackModal');
        showToast(t('feedback_thanks'));
        // Reset form
        document.querySelectorAll('.star-btn').forEach(s => s.classList.remove('active'));
        if (document.getElementById('feedbackComment')) {
            document.getElementById('feedbackComment').value = '';
        }
        if (document.getElementById('feedbackRating')) {
            document.getElementById('feedbackRating').value = '0';
        }
    } catch (error) {
        showToast('Feedback submission failed', 'error');
    }
}

/**
 * Show calendar panel
 */
async function handleShowCalendar() {
    const modal = document.getElementById('calendarModal');
    if (!modal) return;
    showModal('calendarModal');

    const content = document.getElementById('calendarContent');
    if (!content) return;
    content.innerHTML = '<p style="text-align:center;">Loading...</p>';

    const [summary, upcoming] = await Promise.all([
        getCalendarSummary(),
        getCalendarUpcoming()
    ]);

    if (!summary) {
        content.innerHTML = '<p>Unable to load calendar data.</p>';
        return;
    }

    let html = `
        <div class="calendar-summary">
            <h3>${summary.trimester}</h3>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width:${summary.progress_percent}%"></div>
            </div>
            <p>${summary.days_remaining} ${t('days_remaining')} (${summary.progress_percent}% complete)</p>
            <p>Exams: ${summary.exam_start} to ${summary.exam_end}</p>
        </div>
        <h4>${t('upcoming_events')}</h4>
        <div class="event-list">
    `;

    if (upcoming && upcoming.length > 0) {
        upcoming.forEach(event => {
            const typeClass = event.type === 'deadline' ? 'event-deadline' :
                              event.type === 'exam' ? 'event-exam' : 'event-holiday';
            html += `
                <div class="event-item ${typeClass}">
                    <span class="event-name">${event.name}</span>
                    <span class="event-date">${event.date}</span>
                    <span class="event-days">${event.days_until}d</span>
                </div>
            `;
        });
    } else {
        html += '<p>No upcoming events.</p>';
    }

    html += '</div>';
    content.innerHTML = html;
}

/**
 * Show course comparison
 */
async function handleShowComparison() {
    const modal = document.getElementById('comparisonModal');
    if (!modal) return;
    showModal('comparisonModal');

    const content = document.getElementById('comparisonContent');
    if (!content) return;
    content.innerHTML = '<p style="text-align:center;">Loading...</p>';

    const data = await compareCourses('Applied Artificial Intelligence', 'Intelligent Robotics');

    if (!data || data.error) {
        content.innerHTML = '<p>Unable to load comparison data.</p>';
        return;
    }

    const p1 = data.programme_1;
    const p2 = data.programme_2;

    let html = `
        <div class="comparison-grid">
            <div class="comparison-card">
                <h3>${p1.name}</h3>
                <p class="comparison-code">${p1.code}</p>
                <h4>Focus Areas</h4>
                <ul>${p1.focus_areas.map(f => `<li>${f}</li>`).join('')}</ul>
                <h4>Unique Subjects</h4>
                <ul>${p1.unique_subjects.map(s => `<li>${s}</li>`).join('')}</ul>
                <h4>Career Paths</h4>
                <ul>${p1.career_paths.map(c => `<li>${c}</li>`).join('')}</ul>
            </div>
            <div class="comparison-card">
                <h3>${p2.name}</h3>
                <p class="comparison-code">${p2.code}</p>
                <h4>Focus Areas</h4>
                <ul>${p2.focus_areas.map(f => `<li>${f}</li>`).join('')}</ul>
                <h4>Unique Subjects</h4>
                <ul>${p2.unique_subjects.map(s => `<li>${s}</li>`).join('')}</ul>
                <h4>Career Paths</h4>
                <ul>${p2.career_paths.map(c => `<li>${c}</li>`).join('')}</ul>
            </div>
        </div>
        <div class="comparison-shared">
            <h4>${t('similarities')} (${data.shared_count} shared subjects)</h4>
            <div class="shared-chips">
                ${data.shared_subjects.map(s => `<span class="chip">${s}</span>`).join('')}
            </div>
            <p class="comparison-rec">${data.recommendation}</p>
        </div>
    `;

    content.innerHTML = html;
}

/**
 * Show modal
 */
function showModal(id) {
    document.getElementById(id)?.classList.remove('hidden');
}

/**
 * Hide modal
 */
function hideModal(id) {
    document.getElementById(id)?.classList.add('hidden');
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Auto-resize textarea
 */
function autoResize() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
}

/**
 * Update character counter
 */
function updateCharCounter() {
    const length = messageInput.value.length;
    charCounter.textContent = `${length}/1000`;
    charCounter.classList.remove('limit-near', 'limit-reached');
    if (length > 900) charCounter.classList.add('limit-near');
    if (length >= 1000) charCounter.classList.add('limit-reached');
}

/**
 * Update online/offline status
 */
function updateOnlineStatus(isOnline) {
    if (statusBadge) {
        statusBadge.textContent = isOnline ? t('online') : t('offline');
        statusBadge.classList.toggle('offline', !isOnline);
    }
}

/**
 * Chat history persistence (localStorage)
 */
function saveChatMessage(role, content) {
    try {
        const key = `hive_chat_${getUserId()}`;
        const history = JSON.parse(localStorage.getItem(key) || '[]');
        history.push({ role, content, timestamp: Date.now() });
        // Keep last 100 messages
        if (history.length > 100) history.splice(0, history.length - 100);
        localStorage.setItem(key, JSON.stringify(history));
    } catch { /* Storage full or unavailable */ }
}

function restoreChatHistory() {
    try {
        const key = `hive_chat_${getUserId()}`;
        const history = JSON.parse(localStorage.getItem(key) || '[]');
        if (history.length > 0 && welcomeScreen) {
            welcomeScreen.classList.add('hidden');
            history.forEach(msg => addMessage(msg.role, msg.content));
            scrollToBottom();
        }
    } catch { /* Ignore restore errors */ }
}

function clearChatHistory() {
    try {
        const key = `hive_chat_${getUserId()}`;
        localStorage.removeItem(key);
    } catch { /* Ignore */ }
}

/**
 * Register PWA service worker
 */
function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('./sw.js').catch(() => {
            // Service worker registration failed - PWA won't work offline
        });
    }
}

// Make handleSendMessage available for suggestion chips
window._hiveSendMessage = handleSendMessage;

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', init);

// Export for debugging
window.HIVE = {
    version: '3.0.0',
    reset: handleNewChat,
};
