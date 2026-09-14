import os
from .interface import ExtractionProvider
from .mock_provider import MockExtractionProvider

def get_extraction_provider() -> ExtractionProvider:
    ai_mode = os.environ.get("EXTRACTION_MODE", os.environ.get("AI_MODE", "mock")).lower()
    
    if ai_mode == "mock":
        return MockExtractionProvider()
    elif ai_mode in ["real", "gemini"]:
        from .gemini_provider import GeminiExtractionProvider
        return GeminiExtractionProvider()
    else:
        raise ValueError(f"Unknown EXTRACTION_MODE configuration: {ai_mode}. Supported modes: mock, real, gemini.")
