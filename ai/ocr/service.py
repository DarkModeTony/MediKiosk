import os
from .interface import OCRProvider
from .mock_provider import MockOCRProvider

def get_ocr_provider() -> OCRProvider:
    ai_mode = os.environ.get("OCR_MODE", os.environ.get("AI_MODE", "mock")).lower()
    
    if ai_mode == "mock":
        return MockOCRProvider()
    elif ai_mode == "paddle":
        from .paddle_provider import PaddleOCRProvider
        return PaddleOCRProvider()
    elif ai_mode in ["real", "gemini"]:
        from .gemini_provider import GeminiOCRProvider
        return GeminiOCRProvider()
    else:
        raise ValueError(f"Unknown OCR_MODE configuration: {ai_mode}. Supported modes: mock, real, gemini, paddle.")
