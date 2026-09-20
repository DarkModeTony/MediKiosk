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
        Preserves backward compatibility for question_engine while extracting rich clinical dimensions.
        """
        res = self.provider.extract_candidate_facts(transcript, question_id)
        facts_dict: Dict[str, Any] = {
            "all_symptoms": [],
            "_candidate_facts": res.facts,
        }

        def _get_val_str(v: Any, default: str = "") -> str:
            if isinstance(v, dict):
                return str(v.get("complaint") or v.get("name") or v.get("symptom") or v.get("description") or v.get("value") or default)
            return str(v) if v is not None else default

        for fact in res.facts:
            cat = (fact.category or "").lower()
            val = fact.value if isinstance(fact.value, dict) else {"value": fact.value}

            if cat == "chief_complaint":
                facts_dict["chief_complaint"] = _get_val_str(val, transcript)
                if "all_symptoms" in val and isinstance(val["all_symptoms"], list):
                    facts_dict["all_symptoms"].extend(val["all_symptoms"])
            elif cat == "symptom":
                s_name = _get_val_str(val)
                if s_name and s_name not in facts_dict["all_symptoms"]:
                    facts_dict["all_symptoms"].append(s_name)
                if "chief_complaint" not in facts_dict and question_id == "chief_complaint_initial":
                    facts_dict["chief_complaint"] = s_name
            elif cat == "onset":
                facts_dict["onset"] = val.get("onset") or _get_val_str(val)
            elif cat == "severity":
                facts_dict["severity"] = val.get("severity") or _get_val_str(val)
            elif cat in ("character", "quality"):
                facts_dict["character"] = val.get("character") or _get_val_str(val)
            elif cat in ("location", "site"):
                facts_dict["location"] = val.get("location") or _get_val_str(val)
            elif cat == "radiation":
                facts_dict["radiation"] = val.get("radiation") or _get_val_str(val)
            elif cat == "associated":
                facts_dict["associated"] = _get_val_str(val)

        # Fallback: if question is chief complaint and still missing, populate from first symptom or transcript
        if question_id == "chief_complaint_initial" and not facts_dict.get("chief_complaint"):
            if facts_dict["all_symptoms"]:
                facts_dict["chief_complaint"] = facts_dict["all_symptoms"][0]
            elif transcript.strip():
                facts_dict["chief_complaint"] = transcript.strip()

        return facts_dict
