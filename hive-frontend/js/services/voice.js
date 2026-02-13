/**
 * Voice Service Module
 * Handles speech-to-text and text-to-speech functionality
 */

import { API_BASE } from '../config.js';
import { getVoiceSettings, setVoiceSettings } from './storage.js';

let mediaRecorder = null;
let audioChunks = [];

/**
 * Initialize voice settings
 */
export function initVoiceSettings() {
    // Load voices when available
    if ('speechSynthesis' in window) {
        window.speechSynthesis.onvoiceschanged = () => {
            console.log('Voices loaded:', window.speechSynthesis.getVoices().length);
        };
    }
}

/**
 * Start voice recording
 * @returns {Promise<void>}
 */
export async function startVoiceRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // Clear previous chunks
        audioChunks = [];

        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.start();
        console.log('Recording started');

    } catch (error) {
        console.error('Failed to start recording:', error);
        throw new Error('Microphone access denied. Please allow microphone access.');
    }
}

/**
 * Stop voice recording and transcribe
 * @returns {Promise<string>} Transcribed text
 */
export function stopVoiceRecording() {
    return new Promise((resolve, reject) => {
        if (!mediaRecorder) {
            reject(new Error('No active recording'));
            return;
        }

        mediaRecorder.onstop = async () => {
            try {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

                // Stop all tracks
                mediaRecorder.stream.getTracks().forEach(track => track.stop());

                // Transcribe
                const transcript = await transcribeAudio(audioBlob);

                // Clear chunks
                audioChunks = [];
                mediaRecorder = null;

                resolve(transcript);
            } catch (error) {
                reject(error);
            }
        };

        mediaRecorder.stop();
    });
}

/**
 * Transcribe audio using backend API
 * @param {Blob} audioBlob - Audio blob
 * @returns {Promise<string>} Transcribed text
 */
async function transcribeAudio(audioBlob) {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');

    try {
        const response = await fetch(`${API_BASE}/voice/transcribe`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Transcription failed');
        }

        const data = await response.json();
        return data.text || '';

    } catch (error) {
        console.error('Transcription error:', error);
        throw new Error('Failed to transcribe audio. Please try again.');
    }
}

/**
 * Speak text using browser TTS
 * @param {string} text - Text to speak
 */
export function speakText(text) {
    if (!('speechSynthesis' in window)) {
        console.warn('Text-to-speech not supported');
        return;
    }

    // Stop any ongoing speech
    window.speechSynthesis.cancel();

    // Remove emojis and special characters
    const cleanText = removeEmojis(text);

    const utterance = new SpeechSynthesisUtterance(cleanText);
    const settings = getVoiceSettings();

    // Get available voices
    const voices = window.speechSynthesis.getVoices();

    // Try to find a good English voice
    const preferredVoice = voices.find(voice =>
        voice.lang.startsWith('en') && voice.name.toLowerCase().includes('female')
    ) || voices.find(voice => voice.lang.startsWith('en'));

    if (preferredVoice) {
        utterance.voice = preferredVoice;
    }

    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    window.speechSynthesis.speak(utterance);
}

/**
 * Remove emojis from text
 * @param {string} text - Text with emojis
 * @returns {string} Clean text
 */
function removeEmojis(text) {
    return text.replace(/[\u{1F600}-\u{1F64F}]/gu, '') // Emoticons
        .replace(/[\u{1F300}-\u{1F5FF}]/gu, '') // Misc Symbols and Pictographs
        .replace(/[\u{1F680}-\u{1F6FF}]/gu, '') // Transport and Map
        .replace(/[\u{1F1E0}-\u{1F1FF}]/gu, '') // Flags
        .replace(/[\u{2600}-\u{26FF}]/gu, '')   // Misc symbols
        .replace(/[\u{2700}-\u{27BF}]/gu, '')   // Dingbats
        .trim();
}
