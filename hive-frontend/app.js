import { API_BASE, USER_ID_KEY, VOICE_SETTINGS_KEY } from './config.js';

// DOM Elements
const chatMessages = document.getElementById("chatMessages");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const voiceBtn = document.getElementById("voiceBtn");
const attachBtn = document.getElementById("attachBtn");
const settingsBtn = document.getElementById("settingsBtn");
const voiceIndicator = document.getElementById("voiceIndicator");
const settingsModal = document.getElementById("settingsModal");
const closeSettings = document.getElementById("closeSettings");
const voiceProfile = document.getElementById("voiceProfile");
const autoPlayVoice = document.getElementById("autoPlayVoice");

const userId = localStorage.getItem(USER_ID_KEY) || crypto.randomUUID();
localStorage.setItem(USER_ID_KEY, userId);

let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let wasLastInputVoice = false;
let voiceSettings = {
    default_voice: "female_en",
    provider: "browser",
    auto_play: true,
};

init();

function init() {
    // Auto-resize textarea
    messageInput.addEventListener("input", autoResize);

    // Send message handlers
    sendBtn.addEventListener("click", sendMessage);
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Voice button
    voiceBtn.addEventListener("click", toggleVoiceRecording);

    // Settings
    settingsBtn.addEventListener("click", () => settingsModal.style.display = "flex");
    closeSettings.addEventListener("click", () => settingsModal.style.display = "none");
    settingsModal.addEventListener("click", (e) => {
        if (e.target === settingsModal) settingsModal.style.display = "none";
    });

    // Voice settings
    voiceProfile.addEventListener("change", updateVoiceSettings);
    autoPlayVoice.addEventListener("change", updateVoiceSettings);

    // Quick actions
    document.querySelectorAll(".quick-action-btn").forEach(btn => {
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
    }
}

function addMessage(role, text) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? "You" : "🤖";

    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = text;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    return messageDiv;
}

function addThinkingMessage() {
    const thinkingDiv = document.createElement("div");
    thinkingDiv.className = "message assistant";
    thinkingDiv.id = `thinking-${Date.now()}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = "🤖";

    const content = document.createElement("div");
    content.className = "message-content";
    content.style.fontStyle = "italic";
    content.style.color = "#666";

    const thinking = document.createElement("div");
    thinking.className = "message-loading";
    thinking.innerHTML = "<span></span><span></span><span></span>";

    const thinkingText = document.createElement("span");
    thinkingText.textContent = " Thinking...";
    thinkingText.style.marginLeft = "10px";

    content.appendChild(thinking);
    content.appendChild(thinkingText);
    thinkingDiv.appendChild(avatar);
    thinkingDiv.appendChild(content);

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

        // Update UI
        voiceBtn.classList.add("recording");
        voiceIndicator.style.display = "flex";

    } catch (error) {
        console.error("Microphone access error:", error);
        alert("Could not access microphone. Please check permissions.");
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }

    isRecording = false;
    voiceBtn.classList.remove("recording");
    voiceIndicator.style.display = "none";
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
    if ("speechSynthesis" in window) {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);

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
        } else if (profile === "female_ms") {
            selectedVoice = voices.find(v => v.lang.startsWith("ms")) ||
                voices.find(v => v.lang.startsWith("id"));
        } else if (profile === "male_ms") {
            selectedVoice = voices.find(v => v.lang.startsWith("ms")) ||
                voices.find(v => v.lang.startsWith("id"));
        }

        if (selectedVoice) {
            utterance.voice = selectedVoice;
        }

        utterance.rate = 0.9;
        utterance.pitch = 1.0;

        window.speechSynthesis.speak(utterance);
    }
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

// Initialize new handlers
document.addEventListener("DOMContentLoaded", () => {
    const newSessionBtn = document.getElementById("newSessionBtn");
    if (newSessionBtn) {
        newSessionBtn.addEventListener("click", resetSession);
    }

    // Update memory status after each response
    const originalAddMessage = addMessage;
    window.addMessage = function (role, text) {
        originalAddMessage(role, text);
        if (role === "assistant") {
            // Update memory status after assistant response
            setTimeout(updateMemoryStatus, 500);
        }
    };
});

