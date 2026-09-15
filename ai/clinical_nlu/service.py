import os
import logging
from typing import Dict, Any, Optional

from .interface import NLUProvider
from .mock_provider import MockNLUProvider
from .gemini_provider import GeminiNLUProvider
from .models import ExtractedFacts

logger = logging.getLogger(__name__)

def get_nlu_provider() -> NLUProvider:
    """
    Factory function for Clinical NLU provider.
    Defaults to MockNLUProvider unless NLU_MODE is 'gemini' or 'real' and API key is present.
    """
    mode = os.environ.get("NLU_MODE", "mock").lower()
    if mode in ["gemini", "real"]:
        try:
            return GeminiNLUProvider()
        except Exception as e:
            logger.warning(f"Could not instantiate GeminiNLUProvider ({e}), falling back to mock.")
            return MockNLUProvider()
    return MockNLUProvider()

class ClinicalNLUService:
    """
    Backward-compatible adapter that wraps an NLUProvider.
    Ensures existing question_engine code calling `extract_facts(transcript, question_id)`
    continues to work without any modification.
    """
    def __init__(self, provider: Optional[NLUProvider] = None):
        self.provider = provider or get_nlu_provider()

    def extract_candidate_facts(self, transcript: str, question_id: str = "general", context: Optional[Dict] = None) -> ExtractedFacts:
        return self.provider.extract_candidate_facts(transcript, question_id, context)

    def extract_facts(self, transcript: str, question_id: str) -> Dict[str, Any]:
        """
        Legacy dictionary-based extraction method.
        Preserves backward compatibility for question_engine.
        """
        res = self.provider.extract_candidate_facts(transcript, question_id)
        facts_dict: Dict[str, Any] = {}

        for fact in res.facts:
            if fact.category == "chief_complaint":
                facts_dict["chief_complaint"] = fact.value.get("complaint", transcript)
            elif fact.category == "onset":
                facts_dict["onset"] = fact.value.get("onset")
            elif fact.category == "severity":
                facts_dict["severity"] = fact.value.get("severity")
            elif fact.category == "symptom" and "chief_complaint" not in facts_dict and question_id == "chief_complaint_initial":
                facts_dict["chief_complaint"] = fact.value.get("name")

        return facts_dict
