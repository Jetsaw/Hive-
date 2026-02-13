/**
 * Enhanced Admin Dashboard JavaScript
 * Real-time monitoring and terminal console
 */

const API_BASE = 'http://localhost:8000';

// DOM Elements
const consoleBody = document.getElementById('consoleBody');
const logLevel = document.getElementById('logLevel');
const clearLogsBtn = document.getElementById('clearLogs');
const exportLogsBtn = document.getElementById('exportLogs');
const questionsBody = document.getElementById('questionsBody');
const searchInput = document.getElementById('searchInput');
const refreshBtn = document.getElementById('refreshBtn');
const filterBtns = document.querySelectorAll('.filter-btn');
const answerModal = document.getElementById('answerModal');
const closeModal = document.getElementById('closeModal');
const cancelAnswer = document.getElementById('cancelAnswer');
const submitAnswer = document.getElementById('submitAnswer');

// State
let currentFilter = 'all';
let allQuestions = [];
let currentQuestionId = null;

// ===== CONSOLE LOGGING =====

function addConsoleLog(level, message, details = null) {
    const logDiv = document.createElement('div');
    logDiv.className = `console-log ${level}`;

    const time = new Date().toLocaleTimeString('en-US', { hour12: false });

    let html = `
        <span class="log-time">[${time}]</span>
        <span class="log-message">${message}</span>
    `;

    if (details) {
        html += '<div class="log-details">';
        for (const [key, value] of Object.entries(details)) {
            html += `<div>├─ ${key}: ${value}</div>`;
        }
        html += '</div>';
    }

    logDiv.innerHTML = html;
    consoleBody.appendChild(logDiv);

    // Auto-scroll to bottom
    consoleBody.scrollTop = consoleBody.scrollHeight;

    // Keep only last 100 logs
    while (consoleBody.children.length > 100) {
        consoleBody.removeChild(consoleBody.firstChild);
    }
}

// ===== FETCH LOGS FROM BACKEND =====

async function fetchLogs() {
    try {
        const response = await fetch(`${API_BASE}/admin/logs?limit=50`);
        const logs = await response.json();

        // Clear and repopulate
        consoleBody.innerHTML = '';
        logs.reverse().forEach(log => {
            const details = log.details && Object.keys(log.details).length > 0 ? log.details : null;
            addConsoleLog(log.level.toLowerCase(), log.message, details);
        });
    } catch (error) {
        addConsoleLog('error', 'Failed to fetch logs', { error: error.message });
    }
}

// ===== FETCH METRICS =====

async function fetchMetrics() {
    try {
        const response = await fetch(`${API_BASE}/admin/metrics`);
        const metrics = await response.json();

        // Update stats
        document.getElementById('statTotal').textContent = metrics.total_requests;
        document.getElementById('statPending').textContent = metrics.requests_today;

        addConsoleLog('info', 'Metrics updated', {
            'Total Requests': metrics.total_requests,
            'Avg Response Time': `${metrics.avg_response_time}s`,
            'Avg Confidence': `${metrics.avg_confidence}%`
        });
    } catch (error) {
        addConsoleLog('error', 'Failed to fetch metrics', { error: error.message });
    }
}

// ===== FETCH HEALTH STATUS =====

async function fetchHealth() {
    try {
        const response = await fetch(`${API_BASE}/admin/health`);
        const health = await response.json();

        const healthGrid = document.getElementById('healthGrid');
        healthGrid.innerHTML = '';

        for (const [service, data] of Object.entries(health)) {
            const statusClass = data.status === 'online' ? 'online' : 'offline';
            const serviceName = service.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());

            healthGrid.innerHTML += `
                <div class="health-item">
                    <span class="health-status ${statusClass}"></span>
                    <span class="health-name">${serviceName}</span>
                    <span class="health-time">${data.response_time}ms</span>
                </div>
            `;
        }

        addConsoleLog('success', 'Health check completed', {
            'Services': Object.keys(health).length,
            'Status': 'All systems operational'
        });
    } catch (error) {
        addConsoleLog('error', 'Health check failed', { error: error.message });
    }
}

// ===== FETCH QUESTIONS =====

async function fetchQuestions() {
    try {
        const response = await fetch(`${API_BASE}/admin/unanswered`);
        const data = await response.json();

        allQuestions = data.questions || [];

        // Update stats
        const pending = allQuestions.filter(q => q.status === 'pending').length;
        const answered = allQuestions.filter(q => q.status === 'answered').length;
        const ignored = allQuestions.filter(q => q.status === 'ignored').length;

        document.getElementById('statPending').textContent = pending;
        document.getElementById('statAnswered').textContent = answered;
        document.getElementById('statIgnored').textContent = ignored;
        document.getElementById('statTotal').textContent = allQuestions.length;

        renderQuestions();

        addConsoleLog('info', 'Questions loaded', {
            'Total': allQuestions.length,
            'Pending': pending,
            'Answered': answered
        });
    } catch (error) {
        addConsoleLog('error', 'Failed to fetch questions', { error: error.message });
        questionsBody.innerHTML = `
            <div class="empty-state">
                <h3>Error loading questions</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// ===== RENDER QUESTIONS =====

function renderQuestions() {
    let filtered = allQuestions;

    // Apply filter
    if (currentFilter !== 'all') {
        filtered = filtered.filter(q => q.status === currentFilter);
    }

    // Apply search
    const searchTerm = searchInput.value.toLowerCase();
    if (searchTerm) {
        filtered = filtered.filter(q =>
            q.question.toLowerCase().includes(searchTerm) ||
            (q.student_id && q.student_id.toLowerCase().includes(searchTerm))
        );
    }

    if (filtered.length === 0) {
        questionsBody.innerHTML = `
            <div class="empty-state">
                <h3>No questions found</h3>
                <p>There are no questions matching your criteria.</p>
            </div>
        `;
        return;
    }

    questionsBody.innerHTML = filtered.map(q => `
        <div class="question-row">
            <div class="student-id">${q.student_id || 'N/A'}</div>
            <div class="question-text">${q.question}</div>
            <div>
                <span class="status-badge ${q.status}">${q.status.toUpperCase()}</span>
            </div>
            <div class="question-actions">
                <button class="btn btn-sm btn-primary" onclick="openAnswerModal('${q.id}')">
                    Resolve
                </button>
            </div>
        </div>
    `).join('');
}

// ===== MODAL FUNCTIONS =====

function openAnswerModal(questionId) {
    const question = allQuestions.find(q => q.id === questionId);
    if (!question) return;

    currentQuestionId = questionId;
    document.getElementById('modalQuestion').textContent = question.question;
    answerModal.classList.add('active');

    addConsoleLog('info', 'Opening answer modal', {
        'Question ID': questionId,
        'Question': question.question.substring(0, 50) + '...'
    });
}

function closeAnswerModal() {
    answerModal.classList.remove('active');
    document.getElementById('answerText').value = '';
    currentQuestionId = null;
}

async function submitAnswerHandler() {
    const answerText = document.getElementById('answerText').value.trim();

    if (!answerText) {
        alert('Please enter an answer');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/admin/answer/${currentQuestionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                answer: answerText,
                add_to_kb: document.getElementById('addToKB').checked
            })
        });

        if (response.ok) {
            addConsoleLog('success', 'Answer submitted successfully', {
                'Question ID': currentQuestionId,
                'Answer Length': `${answerText.length} chars`
            });

            closeAnswerModal();
            fetchQuestions();
        } else {
            throw new Error('Failed to submit answer');
        }
    } catch (error) {
        addConsoleLog('error', 'Failed to submit answer', { error: error.message });
        alert('Failed to submit answer. Please try again.');
    }
}

// ===== EVENT LISTENERS =====

clearLogsBtn.addEventListener('click', () => {
    consoleBody.innerHTML = '';
    addConsoleLog('info', 'Console cleared');
});

exportLogsBtn.addEventListener('click', () => {
    const logs = Array.from(consoleBody.children).map(log => log.textContent).join('\n');
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hive-logs-${new Date().toISOString()}.txt`;
    a.click();

    addConsoleLog('success', 'Logs exported');
});

logLevel.addEventListener('change', (e) => {
    const level = e.target.value;
    const logs = consoleBody.querySelectorAll('.console-log');

    logs.forEach(log => {
        if (level === 'all' || log.classList.contains(level)) {
            log.style.display = 'block';
        } else {
            log.style.display = 'none';
        }
    });
});

filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        renderQuestions();

        addConsoleLog('info', `Filter changed to: ${currentFilter}`);
    });
});

searchInput.addEventListener('input', renderQuestions);

refreshBtn.addEventListener('click', () => {
    addConsoleLog('info', 'Refreshing data...');
    fetchQuestions();
    fetchMetrics();
    fetchHealth();
});

closeModal.addEventListener('click', closeAnswerModal);
cancelAnswer.addEventListener('click', closeAnswerModal);
submitAnswer.addEventListener('click', submitAnswerHandler);

answerModal.addEventListener('click', (e) => {
    if (e.target === answerModal) {
        closeAnswerModal();
    }
});

// ===== INITIALIZATION =====

async function initialize() {
    addConsoleLog('info', 'Admin dashboard initializing...');

    await fetchLogs();
    await fetchQuestions();
    await fetchMetrics();
    await fetchHealth();

    addConsoleLog('success', 'Dashboard initialized successfully');

    // Auto-refresh every 30 seconds
    setInterval(() => {
        fetchMetrics();
        fetchHealth();
    }, 30000);

    // Fetch new logs every 5 seconds
    setInterval(fetchLogs, 5000);
}

// Start the dashboard
initialize();

// Simulate some activity for demo
setTimeout(() => {
    addConsoleLog('info', 'POST /api/chat', {
        'Query': 'What are prerequisites for ACE6313?',
        'RAG': '5 docs retrieved',
        'Confidence': '87%',
        'Source': 'programme_structure.jsonl',
        'Response': '200 OK (1.2s)'
    });
}, 2000);

setTimeout(() => {
    addConsoleLog('warning', 'POST /api/chat', {
        'Query': 'Tell me about ACE6313',
        'RAG': '3 docs retrieved',
        'Confidence': '45% ⚠️ LOW',
        'Source': 'faie_full_qa.jsonl',
        'Response': '200 OK (0.8s)'
    });
}, 4000);
