/**
 * Sidebar Component
 * Manages sidebar navigation, mobile menu, and page views
 */

import { t, getLanguage, toggleLanguage } from '../i18n.js';

/**
 * Initialize sidebar functionality
 */
export function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.querySelectorAll('.nav-link');

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 1024) {
            if (!sidebar.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        }
    });

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const page = link.getAttribute('data-page');
            if (!link.getAttribute('target')) {
                e.preventDefault();
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
                if (window.innerWidth <= 1024) {
                    sidebar.classList.remove('active');
                }
                handlePageNavigation(page);
            }
        });
    });

    const programmeSelect = document.getElementById('programmeSelect');
    if (programmeSelect) {
        programmeSelect.addEventListener('change', (e) => {
            const programme = e.target.value;
            console.log('Programme selected:', programme);
        });
    }
}

/**
 * Handle page navigation between views
 */
function handlePageNavigation(page) {
    const chatArea = document.querySelector('.chat-area');
    const inputArea = document.querySelector('.input-area');

    switch (page) {
        case 'chat':
            chatArea.style.display = '';
            inputArea.style.display = '';
            break;
        case 'history':
            showHistoryView(chatArea, inputArea);
            break;
        case 'settings':
            showSettingsView(chatArea, inputArea);
            break;
    }
}

/**
 * Show chat history view
 */
function showHistoryView(chatArea, inputArea) {
    inputArea.style.display = 'none';

    const chatMessages = document.getElementById('chatMessages');
    const userId = localStorage.getItem('hive_user_id') || '';
    const key = `hive_chat_${userId}`;
    let history = [];
    try { history = JSON.parse(localStorage.getItem(key) || '[]'); } catch {}

    let html = `
        <div style="padding: 2rem; max-width: 800px; margin: 0 auto;">
            <h2 style="margin-bottom: 1rem; color: hsl(var(--color-text));">${t('history')}</h2>
    `;

    if (history.length === 0) {
        html += '<p style="color: hsl(var(--color-text-muted));">No conversation history yet.</p>';
    } else {
        html += '<div style="display: flex; flex-direction: column; gap: 0.75rem;">';
        history.forEach(msg => {
            const role = msg.role === 'user' ? 'You' : 'HIVE';
            const time = msg.timestamp ? new Date(msg.timestamp).toLocaleString() : '';
            const bgColor = msg.role === 'user'
                ? 'hsl(var(--color-primary) / 0.1)'
                : 'hsl(var(--color-surface))';
            html += `
                <div style="background: ${bgColor}; padding: 0.75rem 1rem; border-radius: 0.75rem; border: 1px solid hsl(var(--color-border));">
                    <strong style="color: hsl(var(--color-primary));">${role}</strong>
                    <span style="font-size: 0.75rem; color: hsl(var(--color-text-muted)); margin-left: 0.5rem;">${time}</span>
                    <p style="margin: 0.25rem 0 0; color: hsl(var(--color-text));">${msg.content}</p>
                </div>
            `;
        });
        html += '</div>';
    }

    html += '</div>';
    chatMessages.innerHTML = html;
}

/**
 * Show settings view
 */
function showSettingsView(chatArea, inputArea) {
    inputArea.style.display = 'none';

    const chatMessages = document.getElementById('chatMessages');
    const currentLang = getLanguage();

    chatMessages.innerHTML = `
        <div style="padding: 2rem; max-width: 600px; margin: 0 auto;">
            <h2 style="margin-bottom: 1.5rem; color: hsl(var(--color-text));">${t('settings')}</h2>

            <div style="background: hsl(var(--color-surface)); border: 1px solid hsl(var(--color-border)); border-radius: 0.75rem; padding: 1.25rem; margin-bottom: 1rem;">
                <h4 style="margin-bottom: 0.75rem; color: hsl(var(--color-text));">Language / Bahasa</h4>
                <div style="display: flex; gap: 0.5rem;">
                    <button id="setLangEN" class="settings-lang-btn ${currentLang === 'en' ? 'active' : ''}"
                        style="padding: 0.5rem 1.5rem; border-radius: 0.5rem; border: 2px solid hsl(var(--color-border)); background: ${currentLang === 'en' ? 'hsl(var(--color-primary))' : 'transparent'}; color: ${currentLang === 'en' ? 'white' : 'hsl(var(--color-text))'}; cursor: pointer;">
                        English
                    </button>
                    <button id="setLangMS" class="settings-lang-btn ${currentLang === 'ms' ? 'active' : ''}"
                        style="padding: 0.5rem 1.5rem; border-radius: 0.5rem; border: 2px solid hsl(var(--color-border)); background: ${currentLang === 'ms' ? 'hsl(var(--color-primary))' : 'transparent'}; color: ${currentLang === 'ms' ? 'white' : 'hsl(var(--color-text))'}; cursor: pointer;">
                        Bahasa Melayu
                    </button>
                </div>
            </div>

            <div style="background: hsl(var(--color-surface)); border: 1px solid hsl(var(--color-border)); border-radius: 0.75rem; padding: 1.25rem; margin-bottom: 1rem;">
                <h4 style="margin-bottom: 0.5rem; color: hsl(var(--color-text));">About</h4>
                <p style="color: hsl(var(--color-text-muted)); margin: 0;">HIVE v3.0 - MMU Academic Adviser</p>
                <p style="color: hsl(var(--color-text-muted)); margin: 0.25rem 0 0;">Built for Faculty of Engineering & Technology</p>
            </div>
        </div>
    `;

    document.getElementById('setLangEN')?.addEventListener('click', () => {
        const { setLanguage } = require('../i18n.js');
        // Use dynamic import workaround
        localStorage.setItem('hive_language', 'en');
        location.reload();
    });
    document.getElementById('setLangMS')?.addEventListener('click', () => {
        localStorage.setItem('hive_language', 'ms');
        location.reload();
    });
}
