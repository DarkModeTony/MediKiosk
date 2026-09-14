import os
from .interface import SummaryProvider
from .mock_provider import MockSummaryProvider
from .openai_provider import OpenAISummaryProvider
from .gemini_provider import GeminiSummaryProvider

def get_summary_provider() -> SummaryProvider:
    ai_mode = os.environ.get("AI_MODE", "mock").lower()
    
    if ai_mode == "real":
        llm_provider = os.environ.get("LLM_PROVIDER", "").lower()
        if llm_provider == "openai":
            return OpenAISummaryProvider()
        elif llm_provider == "gemini":
            return GeminiSummaryProvider()
        else:
            raise ValueError(f"AI_MODE is real but LLM_PROVIDER is missing or unsupported: '{llm_provider}'")
    else:
        return MockSummaryProvider()
