/**
 * Chat Area Component
 * Manages chat message rendering, scrolling, and suggestion chips
 */

let messageIdCounter = 0;

/**
 * Add a message to the chat
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
 * Add suggestion chips below the last assistant message
 */
export function addSuggestionChips(suggestions, onClick) {
    const chatMessages = document.getElementById('chatMessages');

    // Remove any existing chips
    const existing = document.querySelector('.suggestion-chips');
    if (existing) existing.remove();

    const chipsHTML = `
        <div class="suggestion-chips">
            ${suggestions.map(s => `<button class="suggestion-chip">${escapeHtml(s)}</button>`).join('')}
        </div>
    `;

    chatMessages.insertAdjacentHTML('beforeend', chipsHTML);

    // Attach click handlers
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const text = chip.textContent.trim();
            // Remove chips after clicking
            const container = document.querySelector('.suggestion-chips');
            if (container) container.remove();
            if (onClick) onClick(text);
        });
    });

    scrollToBottom();
}

/**
 * Remove a message by ID
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
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}
