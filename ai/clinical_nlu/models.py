from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

class FactConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class CandidateFact(BaseModel):
    category: str # "chief_complaint", "symptom", "onset", "severity", "allergy", "medication", "chronic_condition", "lifestyle"
    fact_type: str # e.g. "reported_symptom", "denied_condition", "reported_allergy"
    value: Dict[str, Any] # structured representation, e.g. {"name": "fever", "duration": "3 days"}
    source_text: str # Exact text snippet or transcript provenance
    confidence: FactConfidence = FactConfidence.HIGH
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    is_negation: bool = False # True if patient denied having something

class ExtractedFacts(BaseModel):
    transcript: str
    question_id: Optional[str] = None
    facts: List[CandidateFact] = []
    metadata: Dict[str, Any] = {}
