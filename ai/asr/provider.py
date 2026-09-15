import os
import time
import io
from typing import Optional

SARVAM_API_URL = "https://api.sarvam.ai/speech-to-text"

class ASRProvider:
    def transcribe(self, audio_data: bytes, language_code: Optional[str] = None, content_type: Optional[str] = None) -> dict:
        raise NotImplementedError()

class MockASRProvider(ASRProvider):
    def transcribe(self, audio_data: bytes, language_code: Optional[str] = None, content_type: Optional[str] = None) -> dict:
        time.sleep(0.5)
        return {
            "transcript": "Mock transcribed text",
            "detected_language": "en-IN"
        }

class SarvamASRProvider(ASRProvider):
    """
    Sarvam AI Saaras v3 speech-to-text provider.
    Supports 22 Indian languages + English with code-mixing.
    https://api.sarvam.ai/speech-to-text
    """
    def __init__(self):
        self.api_key = os.environ.get("SARVAM_API_KEY")
        if not self.api_key:
            raise RuntimeError("SARVAM_API_KEY is not set in environment variables.")

    def transcribe(self, audio_data: bytes, language_code: Optional[str] = None, content_type: Optional[str] = None) -> dict:
        try:
            import httpx
        except ImportError:
            raise RuntimeError("httpx is required for SarvamASRProvider. Run: pip install httpx")

        headers = {
            "api-subscription-key": self.api_key,
        }

        mime = (content_type or "audio/webm").split(";")[0].strip()
        ext = "webm"
        if "wav" in mime:
            ext = "wav"
        elif "mp4" in mime or "m4a" in mime:
            ext = "mp4"
        elif "ogg" in mime or "opus" in mime:
            ext = "ogg"
        elif "mp3" in mime or "mpeg" in mime:
            ext = "mp3"

        files = {
            "file": (f"recording.{ext}", io.BytesIO(audio_data), mime),
        }
        data = {
            "model": "saaras:v3",
            "with_timestamps": "false",
            "with_diarization": "false",
        }
        if language_code:
            data["language_code"] = language_code

        response = httpx.post(
            SARVAM_API_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()

        return {
            "transcript": result.get("transcript", ""),
            "detected_language": result.get("language_code", "unknown"),
            "raw": result
        }


def get_asr_provider() -> ASRProvider:
    """Factory: returns Sarvam provider when ASR_MODE=sarvam, else Mock."""
    asr_mode = os.environ.get("ASR_MODE", "mock").lower()
    if asr_mode == "sarvam":
        return SarvamASRProvider()
    return MockASRProvider()
