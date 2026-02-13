"""
Voice API Endpoints
Handles voice transcription, synthesis, and settings
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.voice.whisper_stt import transcribe_audio, get_supported_formats
from app.voice.tts_service import (
    synthesize_speech,
    get_available_voices,
    VoiceProfile,
    TTSProvider,
)

router = APIRouter()


class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: float


class SynthesisRequest(BaseModel):
    text: str
    voice_profile: Optional[str] = "female_en"
    provider: Optional[str] = None


class VoiceSettingsRequest(BaseModel):
    default_voice: str
    provider: str
    auto_play: bool = True


@router.post("/voice/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    audio: UploadFile = File(...),
    language: Optional[str] = None,
):
    """
    Transcribe audio to text using Whisper
    
    - **audio**: Audio file (supports wav, mp3, m4a, ogg, webm, etc.)
    - **language**: Optional language hint (e.g., 'en', 'ms')
    """
    # Validate file extension
    supported = get_supported_formats()
    file_ext = audio.filename.split(".")[-1].lower() if audio.filename else ""
    
    if file_ext not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Supported: {', '.join(supported)}"
        )
    
    # Read audio data
    audio_data = await audio.read()
    
    if len(audio_data) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")
    
    # Transcribe
    try:
        result = await transcribe_audio(audio_data, audio.filename, language)
        return TranscriptionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/voice/synthesize")
async def synthesize(request: SynthesisRequest):
    """
    Synthesize speech from text
    
    - **text**: Text to convert to speech
    - **voice_profile**: Voice profile (male_en, female_en, male_ms, female_ms)
    - **provider**: TTS provider (browser, openai, elevenlabs, azure)
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        voice_profile = VoiceProfile(request.voice_profile)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid voice profile: {request.voice_profile}")
    
    provider = None
    if request.provider:
        try:
            provider = TTSProvider(request.provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {request.provider}")
    
    try:
        result = await synthesize_speech(request.text, voice_profile, provider)
        
        # For browser TTS, return metadata only
        if result["provider"] == "browser":
            return {
                "provider": "browser",
                "voice": result["voice"],
                "text": request.text,
            }
        
        # For backend TTS, return audio data
        from fastapi.responses import Response
        return Response(
            content=result["audio_data"],
            media_type=f"audio/{result['format']}",
            headers={
                "X-Voice-Provider": result["provider"],
                "X-Voice-Name": result["voice"],
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@router.get("/voice/voices")
async def list_voices():
    """
    Get list of available voice profiles
    
    Returns voice profiles with metadata
    """
    return get_available_voices()


# Voice settings storage (in-memory for now, should use DB in production)
_voice_settings = {
    "default_voice": "female_en",
    "provider": "browser",
    "auto_play": True,
}


@router.get("/voice/settings")
async def get_voice_settings():
    """Get current voice settings"""
    return _voice_settings


@router.post("/voice/settings")
async def update_voice_settings(settings: VoiceSettingsRequest):
    """
    Update voice settings
    
    - **default_voice**: Default voice profile
    - **provider**: TTS provider
    - **auto_play**: Auto-play TTS responses
    """
    # Validate voice profile
    try:
        VoiceProfile(settings.default_voice)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid voice profile: {settings.default_voice}")
    
    # Validate provider
    try:
        TTSProvider(settings.provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {settings.provider}")
    
    _voice_settings["default_voice"] = settings.default_voice
    _voice_settings["provider"] = settings.provider
    _voice_settings["auto_play"] = settings.auto_play
    
    return {"status": "updated", "settings": _voice_settings}
