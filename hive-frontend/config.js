// Configuration constants for HIVE frontend
export const API_BASE = (window.location.hostname === "localhost" && window.location.port === "8080")
    ? "http://localhost:8000/api"
    : "/api";

export const USER_ID_KEY = "hive_user_id";
export const VOICE_SETTINGS_KEY = "hive_voice_settings";
