/**
 * Chat Area Component
 * Manages chat message rendering and scrolling
 */

let messageIdCounter = 0;

/**
 * Add a message to the chat
 * @param {string} role - 'user' or 'assistant'
 * @param {string} text - Message text
 * @returns {string} Message ID
 */
export function addMessage(role, text) {
    const chatMessages = document.getElementById('chatMessages');
    const messageId = `msg-${++messageIdCounter}`;

    const timestamp = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });

    const messageHTML = `
        <div class="message-container ${role}-message" id="${messageId}">
            <div class="message">
                ${escapeHtml(text)}
                <span class="message-time">${timestamp}</span>
            </div>
        </div>
    `;

    chatMessages.insertAdjacentHTML('beforeend', messageHTML);
    scrollToBottom();

    return messageId;
}

/**
 * Add typing indicator
 * @returns {string} Indicator ID
 */
export function addTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const indicatorId = `typing-${++messageIdCounter}`;

    const indicatorHTML = `
        <div class="message-container assistant-message" id="${indicatorId}">
            <div class="message">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        </div>
    `;

    chatMessages.insertAdjacentHTML('beforeend', indicatorHTML);
    scrollToBottom();

    return indicatorId;
}

/**
 * Remove a message by ID
 * @param {string} messageId - Message ID
 */
export function removeMessage(messageId) {
    const element = document.getElementById(messageId);
    if (element) {
        element.remove();
    }
}

/**
 * Scroll chat to bottom
 */
export function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}
