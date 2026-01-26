import { API_BASE, USER_ID_KEY, VOICE_SETTINGS_KEY } from './config.js';

// Voice settings state
let voiceSettings = {
    default_voice: "female_en",
    provider: "browser",
    auto_play: true
};
let wasLastInputVoice = false;

// DOM Elements
const chatMessages = document.getElementById("chatMessages");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const voiceBtn = document.getElementById("voiceBtn");
const attachBtn = document.getElementById("attachBtn");
const settingsBtn = document.getElementById("settingsBtn");
const settingsModal = document.getElementById("settingsModal");
const closeSettings = document.getElementById("closeSettings");
const voiceProfile = document.getElementById("voiceProfile");
const autoPlayVoice = document.getElementById("autoPlayVoice");
const themeToggle = document.getElementById("themeToggle");
const newSessionBtn = document.getElementById("newSessionBtn");

const userId = localStorage.getItem(USER_ID_KEY) || crypto.randomUUID();
localStorage.setItem(USER_ID_KEY, userId);

// Voice state
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let recognition = null;

// Initialize
document.addEventListener("DOMContentLoaded", init);

// Theme Management
function loadTheme() {
    const savedTheme = localStorage.getItem("hive_theme") || "light";
    document.body.setAttribute("data-theme", savedTheme);
    // Also set dark-mode class for CSS compatibility
    document.body.classList.toggle("dark-mode", savedTheme === "dark");
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.body.getAttribute("data-theme") || "light";
    const newTheme = currentTheme === "light" ? "dark" : "light";
    document.body.setAttribute("data-theme", newTheme);
    // Also toggle dark-mode class for CSS compatibility
    document.body.classList.toggle("dark-mode", newTheme === "dark");
    localStorage.setItem("hive_theme", newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const themeBtn = document.getElementById("themeToggle");
    if (themeBtn) {
        // Icon rotation is handled by CSS based on data-theme attribute
        // No need to change icon content since we're using CSS transform
    }
}

function init() {
    // Load theme preference
    loadTheme();

    // Auto-resize textarea
    messageInput.addEventListener("input", autoResize);

    // Send message handlers
    sendBtn.addEventListener("click", sendMessage);
    messageInput.addEventListener("keydown", handleKeyPress);

    // Voice button
    voiceBtn.addEventListener("click", toggleVoiceRecording);

    // Settings modal
    settingsBtn.addEventListener("click", () => {
        settingsModal.classList.add("active");
    });

    closeSettings.addEventListener("click", () => {
        settingsModal.classList.remove("active");
    });

    settingsModal.addEventListener("click", (e) => {
        if (e.target === settingsModal) {
            settingsModal.classList.remove("active");
        }
    });
    // Voice settings
    voiceProfile.addEventListener("change", updateVoiceSettings);
    autoPlayVoice.addEventListener("change", updateVoiceSettings);

    // Theme toggle
    themeToggle.addEventListener("click", toggleTheme);

    // New session
    if (newSessionBtn) {
        newSessionBtn.addEventListener("click", resetSession);
    }

    // Quick actions
    document.querySelectorAll(".quick-action-card").forEach(btn => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            messageInput.value = query;
            sendMessage();
        });
    });

    // Attach button (placeholder)
    attachBtn.addEventListener("click", () => {
        alert("File upload coming soon!");
    });

    // Close modal with Escape key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && settingsModal.classList.contains("active")) {
            settingsModal.classList.remove("active");
        }
    });

    // Load voice settings
    loadVoiceSettings();
}

function autoResize() {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    messageInput.value = "";
    autoResize();
    addMessage("user", message);

    // Add loading state to send button
    sendBtn.disabled = true;
    sendBtn.classList.add('loading');

    const loadingId = addThinkingMessage();

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, message }),
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        removeMessage(loadingId);
        addMessage("assistant", data.answer || "No response");

        if (wasLastInputVoice && voiceSettings.auto_play && voiceSettings.provider === "browser") {
            speakText(data.answer);
        }

        wasLastInputVoice = false;

    } catch (error) {
        removeMessage(loadingId);
        addMessage("assistant", "Sorry, I'm having trouble connecting. Please try again.");
        console.error("Chat error:", error);
        wasLastInputVoice = false;
    } finally {
        // Remove loading state
        sendBtn.disabled = false;
        sendBtn.classList.remove('loading');
    }
}

function addMessage(role, text) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = role === "user" ? "U" : "H";

    const card = document.createElement("div");
    card.className = "card";

    const cardContent = document.createElement("div");
    cardContent.className = "card-content";
    cardContent.style.padding = "1rem";
    cardContent.textContent = text;

    card.appendChild(cardContent);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(card);

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    return messageDiv;
}

function addThinkingMessage() {
    const thinkingDiv = document.createElement("div");
    thinkingDiv.className = "message assistant thinking";
    thinkingDiv.id = `thinking-${Date.now()}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = "H";

    const card = document.createElement("div");
    card.className = "card";

    const cardContent = document.createElement("div");
    cardContent.className = "card-content";
    cardContent.style.padding = "1rem";
    cardContent.textContent = "Thinking...";

    card.appendChild(cardContent);
    thinkingDiv.appendChild(avatar);
    thinkingDiv.appendChild(card);

    chatMessages.appendChild(thinkingDiv);
    scrollToBottom();

    return thinkingDiv.id;
}

function removeMessage(id) {
    const element = document.getElementById(id);
    if (element) element.remove();
}

function scrollToBottom() {
    chatMessages.parentElement.scrollTop = chatMessages.parentElement.scrollHeight;
}

// Voice Recording
async function toggleVoiceRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
            await transcribeAudio(audioBlob);

            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;

        // Update UI - add recording class to button
        voiceBtn.classList.add("recording");

    } catch (error) {
        console.error("Microphone access error:", error);
        alert("Could not access microphone. Please check permissions.");
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;

        // Update UI - remove recording class
        voiceBtn.classList.remove("recording");
    }
}

async function transcribeAudio(audioBlob) {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");

    try {
        const response = await fetch(`${API_BASE}/voice/transcribe`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Transcription failed: ${response.status}`);
        }

        const data = await response.json();

        // Set transcribed text in input
        messageInput.value = data.text;
        autoResize();
        messageInput.focus();

        // Mark that this input came from voice
        wasLastInputVoice = true;

        // Auto-send the message
        sendMessage();

    } catch (error) {
        console.error("Transcription error:", error);
        alert("Voice transcription failed. Please try again.");
    }
}

// Text-to-Speech
function speakText(text) {
    if ("speechSynthesis" in window && voiceSettings.auto_play) {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();

        // Remove emojis from text before speaking
        const cleanText = removeEmojis(text);

        const utterance = new SpeechSynthesisUtterance(cleanText);

        // Get available voices
        const voices = window.speechSynthesis.getVoices();
        const profile = voiceSettings.default_voice;

        // Better voice selection
        let selectedVoice = null;

        if (profile === "female_en") {
            selectedVoice = voices.find(v => v.lang.startsWith("en") && v.name.toLowerCase().includes("female")) ||
                voices.find(v => v.lang.startsWith("en") && v.name.toLowerCase().includes("zira")) ||
                voices.find(v => v.lang.startsWith("en"));
        } else if (profile === "male_en") {
            selectedVoice = voices.find(v => v.lang.startsWith("en") && v.name.toLowerCase().includes("male")) ||
                voices.find(v => v.lang.startsWith("en") && v.name.toLowerCase().includes("david")) ||
                voices.find(v => v.lang.startsWith("en"));
        }

        if (selectedVoice) {
            utterance.voice = selectedVoice;
        }

        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        window.speechSynthesis.speak(utterance);
    }
}

// Remove emojis from text
function removeEmojis(text) {
    // Remove all emojis using regex
    return text.replace(/[\u{1F600}-\u{1F64F}]/gu, '') // Emoticons
        .replace(/[\u{1F300}-\u{1F5FF}]/gu, '') // Misc Symbols and Pictographs
        .replace(/[\u{1F680}-\u{1F6FF}]/gu, '') // Transport and Map
        .replace(/[\u{1F1E0}-\u{1F1FF}]/gu, '') // Flags
        .replace(/[\u{2600}-\u{26FF}]/gu, '') // Misc symbols
        .replace(/[\u{2700}-\u{27BF}]/gu, '') // Dingbats
        .replace(/[\u{1F900}-\u{1F9FF}]/gu, '') // Supplemental Symbols and Pictographs
        .replace(/[\u{1FA00}-\u{1FA6F}]/gu, '') // Chess Symbols
        .replace(/[\u{1FA70}-\u{1FAFF}]/gu, '') // Symbols and Pictographs Extended-A
        .replace(/[\u{FE00}-\u{FE0F}]/gu, '') // Variation Selectors
        .replace(/[\u{200D}]/gu, '') // Zero Width Joiner
        .trim();
}

// Voice Settings - Using localStorage for persistence
function loadVoiceSettings() {
    // Load from localStorage
    const saved = localStorage.getItem("hive_voice_settings");
    if (saved) {
        try {
            voiceSettings = JSON.parse(saved);
        } catch (e) {
            console.error("Failed to parse voice settings:", e);
        }
    }

    // Update UI
    if (voiceProfile) voiceProfile.value = voiceSettings.default_voice;
    if (autoPlayVoice) autoPlayVoice.checked = voiceSettings.auto_play;

    console.log("Voice settings loaded:", voiceSettings);
}

function updateVoiceSettings() {
    voiceSettings = {
        default_voice: voiceProfile.value,
        provider: "browser",
        auto_play: autoPlayVoice.checked,
    };

    // Save to localStorage
    localStorage.setItem("hive_voice_settings", JSON.stringify(voiceSettings));
    console.log("Voice settings saved:", voiceSettings);
}

// Load voices when available
if ("speechSynthesis" in window) {
    // Voices may not be loaded immediately
    window.speechSynthesis.onvoiceschanged = () => {
        console.log("Voices loaded:", window.speechSynthesis.getVoices().length);
    };
}

// ===== MEMORY STATUS FUNCTIONS =====
async function updateMemoryStatus() {
    try {
        const response = await fetch(`${API_BASE}/session/memory?user_id=${userId}`);
        if (response.ok) {
            const memory = await response.json();
            displayMemoryStatus(memory);
        }
    } catch (error) {
        console.error("Failed to fetch memory status:", error);
    }
}

function displayMemoryStatus(memory) {
    const headerStatus = document.getElementById("headerMemoryStatus");
    const memoryText = document.getElementById("memoryText");

    if (headerStatus && memoryText && memory.pairs_count > 0) {
        headerStatus.style.display = "inline-flex";
        memoryText.textContent = `${memory.pairs_count} ${memory.pairs_count === 1 ? 'pair' : 'pairs'}`;

        // Add summary indicator if available
        if (memory.summary_available) {
            headerStatus.classList.add("has-summary");
            memoryText.textContent += ` + summary`;
        } else {
            headerStatus.classList.remove("has-summary");
        }
    } else if (headerStatus) {
        headerStatus.style.display = "none";
    }
}

// ===== NEW SESSION FUNCTION =====
async function resetSession() {
    if (!confirm("Start a new session? This will clear the conversation memory.")) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/session/reset?user_id=${userId}`, {
            method: "POST"
        });

        if (response.ok) {
            // Clear chat messages except welcome card
            const welcome = document.querySelector(".welcome-card");
            chatMessages.innerHTML = "";
            if (welcome) {
                chatMessages.appendChild(welcome);
            }

            // Update memory status
            updateMemoryStatus();

            console.log("Session reset successfully");
        }
    } catch (error) {
        console.error("Failed to reset session:", error);
        alert("Failed to reset session. Please try again.");
    }
}

// Update memory status after assistant messages
document.addEventListener("DOMContentLoaded", () => {
    // Override addMessage to update memory status after assistant responses
    const originalAddMessage = addMessage;
    window.addMessage = function (role, text) {
        const result = originalAddMessage(role, text);
        if (role === "assistant") {
            // Update memory status after assistant response
            setTimeout(updateMemoryStatus, 500);
        }
        return result;
    };
});

