/**
 * HIVE Main Application Entry Point
 * Orchestrates all components and modules
 */

import { API_BASE, USER_ID_KEY, VOICE_SETTINGS_KEY } from './config.js';
import { loadTheme, toggleTheme } from './utils/theme.js';
import { sendChatMessage } from './services/api.js';
import { startVoiceRecording, stopVoiceRecording, speakText, initVoiceSettings } from './services/voice.js';
import { getUserId, getVoiceSettings } from './services/storage.js';
import { addMessage, addTypingIndicator, removeMessage, scrollToBottom } from './components/ChatArea.js';
import { initSidebar } from './components/Sidebar.js';

// App State
let isRecording = false;
let wasLastInputVoice = false;

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

    // Attach event listeners
    setupEventListeners();

    // Auto-resize textarea
    messageInput.addEventListener('input', () => {
        autoResize();
        updateCharCounter();
    });

    // Initial focus
    messageInput.focus();

    console.log('HIVE initialized successfully');
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Send message
    sendBtn.addEventListener('click', handleSendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Voice recording
    voiceBtn.addEventListener('click', handleVoiceToggle);

    // Theme toggle
    themeToggleBtn.addEventListener('click', () => {
        toggleTheme();
    });

    // New chat
    newChatBtn.addEventListener('click', handleNewChat);

    // Check online status
    window.addEventListener('online', () => updateOnlineStatus(true));
    window.addEventListener('offline', () => updateOnlineStatus(false));
}

/**
 * Handle sending a message
 */
async function handleSendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    // Hide welcome screen if visible
    if (welcomeScreen && !welcomeScreen.classList.contains('hidden')) {
        welcomeScreen.classList.add('hidden');
    }

    // Add user message
    addMessage('user', text);

    // Clear input
    messageInput.value = '';
    autoResize();
    updateCharCounter();
    scrollToBottom();

    // Show typing indicator
    const typingId = addTypingIndicator();

    try {
        // Send to API
        const response = await sendChatMessage(getUserId(), text);

        // Remove typing indicator
        removeMessage(typingId);

        // Add assistant message
        addMessage('assistant', response.answer);

        // Speak if voice input was used
        const voiceSettings = getVoiceSettings();
        if (wasLastInputVoice && voiceSettings.auto_play) {
            speakText(response.answer);
        }

        // Reset voice flag
        wasLastInputVoice = false;

    } catch (error) {
        removeMessage(typingId);
        addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        console.error('Chat error:', error);
    }

    scrollToBottom();
}

/**
 * Handle voice recording toggle
 */
async function handleVoiceToggle() {
    if (isRecording) {
        // Stop recording
        isRecording = false;
        voiceBtn.classList.remove('recording');
        
        try {
            const transcript = await stopVoiceRecording();
            if (transcript) {
                messageInput.value = transcript;
                wasLastInputVoice = true;
                autoResize();
                updateCharCounter();
                // Auto-send after transcription
                handleSendMessage();
            }
        } catch (error) {
            console.error('Voice recording error:', error);
        }
    } else {
        // Start recording
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
    if (!confirm('Start a new conversation? This will clear the current chat.')) {
        return;
    }

    try {
        const userId = getUserId();
        const response = await fetch(`${API_BASE}/session/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });

        if (response.ok) {
            // Clear chat messages
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = '';

            // Show welcome screen
            const welcomeHTML = `
                <div class="welcome-screen" id="welcomeScreen">
                    <div class="welcome-logo" role="img" aria-label="Hive Logo">
                        <img src="./assets/logo.png" alt="HIVE Logo">
                    </div>
                    <h1 class="welcome-text">Hi, I'm HIVE</h1>
                    <p class="welcome-subtitle">MMU Academic Adviser</p>
                </div>
            `;
            chatMessages.innerHTML = welcomeHTML;
            welcomeScreen = document.getElementById('welcomeScreen');

            // Clear input
            messageInput.value = '';
            autoResize();
            updateCharCounter();
            messageInput.focus();
        }
    } catch (error) {
        console.error('Reset session error:', error);
        alert('Failed to reset session. Please try again.');
    }
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

    // Update styling based on character count
    charCounter.classList.remove('limit-near', 'limit-reached');
    if (length > 900) {
        charCounter.classList.add('limit-near');
    }
    if (length >= 1000) {
        charCounter.classList.add('limit-reached');
    }
}

/**
 * Update online/offline status
 */
function updateOnlineStatus(isOnline) {
    if (statusBadge) {
        if (isOnline) {
            statusBadge.textContent = 'Online';
            statusBadge.classList.remove('offline');
        } else {
            statusBadge.textContent = 'Offline';
            statusBadge.classList.add('offline');
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', init);

// Export for debugging
window.HIVE = {
    version: '2.0.0',
    reset: handleNewChat,
};
