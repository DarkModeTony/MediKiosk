import os
import time

class ASRProvider:
    def transcribe(self, audio_data: bytes) -> str:
        raise NotImplementedError()

class MockASRProvider(ASRProvider):
    def transcribe(self, audio_data: bytes) -> str:
        # Simulate network delay
        time.sleep(1)
        # In mock mode, we expect the frontend to just send the text string disguised as audio,
        # or we just return a static string. Actually, the frontend will likely send a direct transcript via the API
        # if NEXT_PUBLIC_AI_MODE=mock, bypassing this backend ASR entirely for simplicity, 
        # or it will send a special keyword.
        return "Mock transcribed text"

class IndicConformerProvider(ASRProvider):
    def transcribe(self, audio_data: bytes) -> str:
        # Real integration would go here.
        raise NotImplementedError("IndicConformer model not loaded")

def get_asr_provider() -> ASRProvider:
    ai_mode = os.environ.get("AI_MODE", "mock")
    if ai_mode == "mock":
        return MockASRProvider()
    else:
        return IndicConformerProvider()
