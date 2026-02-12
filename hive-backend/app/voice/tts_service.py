"""
Text-to-Speech Service
Supports multiple TTS providers with voice profile management
"""
import os
import logging
from typing import Optional, Literal
from enum import Enum

logger = logging.getLogger(__name__)


class VoiceProfile(str, Enum):
    """Available voice profiles"""
    MALE_EN = "male_en"
    FEMALE_EN = "female_en"
    MALE_MS = "male_ms"
    FEMALE_MS = "female_ms"


class TTSProvider(str, Enum):
    """Supported TTS providers"""
    BROWSER = "browser"  # Browser native (no backend processing)
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"
    AZURE = "azure"


VOICE_MAPPINGS = {
    TTSProvider.OPENAI: {
        VoiceProfile.MALE_EN: "onyx",
        VoiceProfile.FEMALE_EN: "nova",
        VoiceProfile.MALE_MS: "onyx",
        VoiceProfile.FEMALE_MS: "nova",
    },
    TTSProvider.ELEVENLABS: {
        VoiceProfile.MALE_EN: "adam",
        VoiceProfile.FEMALE_EN: "rachel",
        VoiceProfile.MALE_MS: "adam",
        VoiceProfile.FEMALE_MS: "rachel",
    },
    TTSProvider.AZURE: {
        VoiceProfile.MALE_EN: "en-US-GuyNeural",
        VoiceProfile.FEMALE_EN: "en-US-JennyNeural",
        VoiceProfile.MALE_MS: "ms-MY-OsmanNeural",
        VoiceProfile.FEMALE_MS: "ms-MY-YasminNeural",
    },
}


async def synthesize_speech(
    text: str,
    voice_profile: VoiceProfile = VoiceProfile.FEMALE_EN,
    provider: Optional[TTSProvider] = None,
) -> dict:
    """
    Synthesize speech from text
    
    Args:
        text: Text to convert to speech
        voice_profile: Voice profile to use
        provider: TTS provider (defaults to env VOICE_PROVIDER)
    
    Returns:
        dict with 'audio_data' (bytes), 'format', and 'provider'
    """
    if provider is None:
        provider_str = os.getenv("VOICE_PROVIDER", "browser")
        provider = TTSProvider(provider_str)
    
    if provider == TTSProvider.BROWSER:
        return {
            "audio_data": None,
            "format": "browser",
            "provider": "browser",
            "voice": voice_profile.value,
        }
    
    if provider == TTSProvider.OPENAI:
        return await _synthesize_openai(text, voice_profile)
    elif provider == TTSProvider.ELEVENLABS:
        return await _synthesize_elevenlabs(text, voice_profile)
    elif provider == TTSProvider.AZURE:
        return await _synthesize_azure(text, voice_profile)
    else:
        raise ValueError(f"Unsupported TTS provider: {provider}")


async def _synthesize_openai(text: str, voice_profile: VoiceProfile) -> dict:
    """Synthesize using OpenAI TTS"""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        voice = VOICE_MAPPINGS[TTSProvider.OPENAI][voice_profile]
        
        response = await client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
        )
        
        audio_data = response.content
        
        return {
            "audio_data": audio_data,
            "format": "mp3",
            "provider": "openai",
            "voice": voice,
        }
    
    except Exception as e:
        logger.error(f"OpenAI TTS failed: {e}")
        raise


async def _synthesize_elevenlabs(text: str, voice_profile: VoiceProfile) -> dict:
    """Synthesize using ElevenLabs"""
    try:
        import httpx
        
        api_key = os.getenv("ELEVENLABS_API_KEY")
        voice = VOICE_MAPPINGS[TTSProvider.ELEVENLABS][voice_profile]
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
        headers = {"xi-api-key": api_key}
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            audio_data = response.content
        
        return {
            "audio_data": audio_data,
            "format": "mp3",
            "provider": "elevenlabs",
            "voice": voice,
        }
    
    except Exception as e:
        logger.error(f"ElevenLabs TTS failed: {e}")
        raise


async def _synthesize_azure(text: str, voice_profile: VoiceProfile) -> dict:
    """Synthesize using Azure Cognitive Services"""
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        service_region = os.getenv("AZURE_SPEECH_REGION", "eastus")
        
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=service_region
        )
        
        voice = VOICE_MAPPINGS[TTSProvider.AZURE][voice_profile]
        speech_config.speech_synthesis_voice_name = voice
        
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        result = synthesizer.speak_text_async(text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return {
                "audio_data": result.audio_data,
                "format": "wav",
                "provider": "azure",
                "voice": voice,
            }
        else:
            raise Exception(f"Azure TTS failed: {result.reason}")
    
    except Exception as e:
        logger.error(f"Azure TTS failed: {e}")
        raise


def get_available_voices() -> dict:
    """Get list of available voice profiles"""
    return {
        "voices": [
            {
                "id": VoiceProfile.MALE_EN.value,
                "name": "Male (English)",
                "language": "en",
                "gender": "male",
            },
            {
                "id": VoiceProfile.FEMALE_EN.value,
                "name": "Female (English)",
                "language": "en",
                "gender": "female",
            },
            {
                "id": VoiceProfile.MALE_MS.value,
                "name": "Male (Malay)",
                "language": "ms",
                "gender": "male",
            },
            {
                "id": VoiceProfile.FEMALE_MS.value,
                "name": "Female (Malay)",
                "language": "ms",
                "gender": "female",
            },
        ],
        "default": VoiceProfile.FEMALE_EN.value,
    }
