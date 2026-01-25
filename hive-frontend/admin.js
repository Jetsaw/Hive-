/**
 * HIVE Admin - Unanswered Questions Management
 * JavaScript for admin interface
 */

import { API_BASE } from './config.js';

let currentFilter = 'all';
let currentQuestionId = null;
let allQuestions = [];

document.addEventListener('DOMContentLoaded', () => {
    loadQuestions();
});

// Load questions from API
async function loadQuestions() {
    try {
        const response = await fetch(`${API_BASE}/admin/unanswered?limit=200`);
        if (!response.ok) throw new Error('Failed to load questions');

        const data = await response.json();
        allQuestions = data.questions;

        // Update stats
        updateStats(data.stats);

        // Display questions
        displayQuestions(allQuestions);
    } catch (error) {
        console.error('Error loading questions:', error);
        document.getElementById('questionsList').innerHTML = `
            <div class="empty-state">
                ❌ Failed to load questions. Please check the server connection.
            </div>
        `;
    }
}

// Update statistics display
function updateStats(stats) {
    document.getElementById('statPending').textContent = stats.pending || 0;
    document.getElementById('statAnswered').textContent = stats.answered || 0;
    document.getElementById('statIgnored').textContent = stats.ignored || 0;
    document.getElementById('statTotal').textContent = stats.total || 0;
}

// Filter questions by status
function filterQuestions(status) {
    currentFilter = status;

    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.status === status) {
            btn.classList.add('active');
        }
    });

    // Filter and display
    const filtered = status === 'all'
        ? allQuestions
        : allQuestions.filter(q => q.status === status);

    displayQuestions(filtered);
}

// Display questions in the list
function displayQuestions(questions) {
    const container = document.getElementById('questionsList');

    if (questions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>No questions found</h3>
                <p>There are no ${currentFilter === 'all' ? '' : currentFilter} questions at the moment.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = questions.map(q => createQuestionCard(q)).join('');
}

// Create HTML for a question card
function createQuestionCard(question) {
    const timestamp = new Date(question.timestamp).toLocaleString();
    const confidenceClass = question.confidence_score < 0.4 ? 'confidence-low' : 'confidence-medium';
    const confidencePercent = Math.round(question.confidence_score * 100);

    const statusBadge = question.status === 'pending'
        ? '<span class="meta-badge" style="background: #FFF4E6; color: #F57C00;">⏳ Pending</span>'
        : question.status === 'answered'
            ? '<span class="meta-badge" style="background: #E8F5E9; color: #388E3C;">✅ Answered</span>'
            : '<span class="meta-badge" style="background: #F5F5F5; color: #757575;">🚫 Ignored</span>';

    const actions = question.status === 'pending'
        ? `
            <button class="action-btn btn-answer" onclick="openAnswerModal(${question.id})">
                ✏️ Add Answer
            </button>
            <button class="action-btn btn-ignore" onclick="ignoreQuestion(${question.id})">
                🚫 Ignore
            </button>
        `
        : question.status === 'answered'
            ? `
            <div style="padding: var(--space-sm); background: var(--gray-soft); border-radius: 8px;">
                <strong>Admin Answer:</strong> ${question.admin_answer || 'N/A'}
                ${question.admin_notes ? `<br><em>Notes: ${question.admin_notes}</em>` : ''}
            </div>
        `
            : `
            <div style="padding: var(--space-sm); background: var(--gray-soft); border-radius: 8px; font-style: italic;">
                ${question.admin_notes || 'Marked as ignored'}
            </div>
        `;

    return `
        <div class="question-card">
            <div class="question-header">
                <span class="question-id">#${question.id}</span>
                <span class="question-time">${timestamp}</span>
            </div>
            <div class="question-text">${escapeHtml(question.question)}</div>
            <div class="question-meta">
                ${statusBadge}
                <span class="meta-badge ${confidenceClass}">
                    📊 Confidence: ${confidencePercent}%
                </span>
                <span class="meta-badge">
                    📚 RAG Results: ${question.rag_results_count}
                </span>
            </div>
            <div class="question-reason">
                💡 ${question.uncertainty_reason || 'Low confidence score'}
            </div>
            <details style="margin-top: var(--space-sm);">
                <summary style="cursor: pointer; font-weight: 600; color: var(--sage-knowledge);">
                    View Bot's Attempted Answer
                </summary>
                <div style="margin-top: var(--space-sm); padding: var(--space-sm); background: var(--gray-soft); border-radius: 8px;">
                    ${escapeHtml(question.attempted_answer || 'N/A')}
                </div>
            </details>
            <div class="question-actions">
                ${actions}
            </div>
        </div>
    `;
}

// Open answer modal
function openAnswerModal(questionId) {
    const question = allQuestions.find(q => q.id === questionId);
    if (!question) return;

    currentQuestionId = questionId;
    document.getElementById('modalQuestion').textContent = question.question;
    document.getElementById('answerText').value = '';
    document.getElementById('adminNotes').value = '';
    document.getElementById('addToKB').checked = false;

    document.getElementById('answerModal').classList.add('active');
}

// Close modal
function closeModal() {
    document.getElementById('answerModal').classList.remove('active');
    currentQuestionId = null;
}

// Submit answer
async function submitAnswer() {
    if (!currentQuestionId) return;

    const answer = document.getElementById('answerText').value.trim();
    const notes = document.getElementById('adminNotes').value.trim();
    const addToKB = document.getElementById('addToKB').checked;

    if (!answer) {
        alert('Please enter an answer');
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE}/admin/unanswered/${currentQuestionId}/answer`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answer, notes, add_to_kb: addToKB })
            }
        );

        if (!response.ok) throw new Error('Failed to submit answer');

        const result = await response.json();

        // Close modal
        closeModal();

        // Reload questions
        await loadQuestions();

        // Show success message
        alert('✅ Answer submitted successfully!');
    } catch (error) {
        console.error('Error submitting answer:', error);
        alert('❌ Failed to submit answer. Please try again.');
    }
}

// Ignore question
async function ignoreQuestion(questionId) {
    const reason = prompt('Reason for ignoring (optional):');
    if (reason === null) return; // User cancelled

    try {
        const response = await fetch(
            `${API_BASE}/admin/unanswered/${questionId}/ignore`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: reason || 'No reason provided' })
            }
        );

        if (!response.ok) throw new Error('Failed to ignore question');

        // Reload questions
        await loadQuestions();

        alert('✅ Question marked as ignored');
    } catch (error) {
        console.error('Error ignoring question:', error);
        alert('❌ Failed to ignore question. Please try again.');
    }
}

// Utility: Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal when clicking outside
document.getElementById('answerModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'answerModal') {
        closeModal();
    }
});
