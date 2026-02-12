"""
Whisper Speech-to-Text Service
Handles audio transcription using OpenAI's Whisper model
"""
import os
import tempfile
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

_whisper_model = None


def get_whisper_model():
    """Lazy load Whisper model"""
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
            logger.info(f"Loading Whisper model: {model_size}")
            _whisper_model = whisper.load_model(model_size)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    return _whisper_model


async def transcribe_audio(
    audio_data: bytes,
    filename: str,
    language: Optional[str] = None
) -> dict:
    """
    Transcribe audio to text using Whisper
    
    Args:
        audio_data: Raw audio bytes
        filename: Original filename (for extension detection)
        language: Optional language code (e.g., 'en', 'ms')
    
    Returns:
        dict with 'text', 'language', and 'confidence'
    """
    suffix = Path(filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name
    
    try:
        model = get_whisper_model()
        
        options = {}
        if language:
            options["language"] = language
        
        result = model.transcribe(tmp_path, **options)
        
        return {
            "text": result["text"].strip(),
            "language": result.get("language", "unknown"),
            "confidence": _calculate_confidence(result),
        }
    
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise
    
    finally:
        try:
            os.unlink(tmp_path)
        except Exception as e:
            logger.warning(f"Failed to delete temp file {tmp_path}: {e}")


def _calculate_confidence(result: dict) -> float:
    """
    Calculate average confidence from Whisper segments
    
    Args:
        result: Whisper transcription result
    
    Returns:
        Average confidence score (0-1)
    """
    segments = result.get("segments", [])
    if not segments:
        return 0.0
    
    confidences = [1.0 - seg.get("no_speech_prob", 0.5) for seg in segments]
    return sum(confidences) / len(confidences)


def get_supported_formats() -> list[str]:
    """Return list of supported audio formats"""
    return [
        "wav", "mp3", "m4a", "ogg", "webm", 
        "flac", "aac", "wma", "opus"
    ]
