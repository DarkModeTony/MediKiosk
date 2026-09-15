from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from .models import ExtractedFacts

class NLUProvider(ABC):
    """
    Interface for Clinical Natural Language Understanding.
    Extracts structured candidate clinical facts from patient statements.
    
    NON-NEGOTIABLE SAFETY INVARIANTS:
    - Never diagnose.
    - Never prescribe medication.
    - Never convert unknown allergy or condition to negative.
    - Never invent symptoms not present in the transcript.
    - Must attach source text provenance for every candidate fact.
    """

    @abstractmethod
    def extract_candidate_facts(
        self,
        transcript: str,
        question_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExtractedFacts:
        pass
