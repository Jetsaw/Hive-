
const API_BASE = "/api";

const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");
const plusBtn = document.getElementById("plusBtn");
const micBtn = document.getElementById("micBtn");

const userIdKey = "hive_user_id";
const userId = localStorage.getItem(userIdKey) || crypto.randomUUID();
localStorage.setItem(userIdKey, userId);

let voiceMode = false;
let recognition = null;

function addMessage(role, text, sources = []) {
    const bubble = document.createElement("div");
    bubble.className = "msg " + (role === "user" ? "user" : "bot");
    bubble.textContent = text;
    chatEl.appendChild(bubble);
    chatEl.scrollTop = chatEl.scrollHeight;
}

async function sendMessage() {
    const msg = inputEl.value.trim();
    if (!msg) return;

    inputEl.value = "";
    addMessage("user", msg);

    try {
        const res = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, message: msg })
        });

        if (!res.ok) {
            const t = await res.text();
            addMessage("assistant", `Server error (${res.status}): ${t}`);
            return;
        }

        const data = await res.json();
        addMessage("assistant", data.answer || "No response", data.sources || []);

        if (voiceMode && "speechSynthesis" in window) {
            const u = new SpeechSynthesisUtterance(data.answer || "");
            speechSynthesis.cancel();
            speechSynthesis.speak(u);
        }
    } catch (e) {
        addMessage("assistant", "Failed to reach backend. Is Docker running and nginx started?");
    }
}

sendBtn.addEventListener("click", sendMessage);
inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

plusBtn.addEventListener("click", () => {
    alert("Upload is coming soon ");
});

micBtn.addEventListener("click", () => {
    voiceMode = !voiceMode;
    micBtn.classList.toggle("mic-on", voiceMode);

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
        alert("SpeechRecognition not supported in this browser (try Chrome/Edge).");
        return;
    }

    if (voiceMode) {
        recognition = new SR();
        recognition.lang = "en-MY";
        recognition.interimResults = true;

        recognition.onresult = (event) => {
            let transcript = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            inputEl.value = transcript.trim();
        };

        recognition.onend = () => {
            if (voiceMode) recognition.start();
        };

        recognition.start();
    } else {
        if (recognition) recognition.stop();
        recognition = null;
    }
});
