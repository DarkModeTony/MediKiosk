import io
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
from ai.asr.provider import get_asr_provider

router = APIRouter()

SUPPORTED_AUDIO_TYPES = {"audio/wav", "audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg", "audio/mp3"}

@router.post("/transcribe")
async def transcribe_voice(
    audio: UploadFile = File(...),
    language_code: Optional[str] = Form(None)
):
    """
    Transcribe patient voice input using Sarvam AI saaras:v3.
    Accepts audio file (WAV, WebM, OGG, MP4) from the browser microphone.
    Returns transcript and detected language.
    
    Supported languages: Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati,
    Kannada, Malayalam, Odia, Punjabi, English (Indian).
    """
    # Check file content type (browser MediaRecorder usually sends audio/webm)
    ct = audio.content_type or ""
    if ct and ct.lower() not in SUPPORTED_AUDIO_TYPES:
        # Accept anyway — browsers sometimes send audio/webm;codecs=opus
        if not ct.lower().startswith("audio/"):
            raise HTTPException(status_code=422, detail=f"Unsupported audio type: {ct}. Expected audio/*")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="Empty audio file received.")

    try:
        provider = get_asr_provider()
        result = provider.transcribe(audio_bytes, language_code=language_code, content_type=ct)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    return {
        "transcript": result.get("transcript", ""),
        "detected_language": result.get("detected_language", "unknown"),
        "status": "ok"
    }
