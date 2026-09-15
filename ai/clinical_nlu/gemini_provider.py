import os
import json
import logging
from typing import Optional, Dict, Any, List
from google import genai
from google.genai import types

from .interface import NLUProvider
from .models import ExtractedFacts, CandidateFact, FactConfidence
from .mock_provider import MockNLUProvider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a specialized Clinical Natural Language Understanding (NLU) extraction component for MediPlatform.
Your role is to strictly extract candidate clinical facts from a patient's spoken or typed intake transcript.

NON-NEGOTIABLE SAFETY RULES:
1. NEVER DIAGNOSE: Do not infer or state a clinical diagnosis.
2. NEVER PRESCRIBE: Do not suggest or prescribe medications.
3. NEVER INVENT FACTS: Only extract symptoms, complaints, onset, severity, allergies, and conditions directly expressed in the transcript.
4. UNKNOWN IS NOT ABSENT: If a patient does not mention an allergy or condition, DO NOT claim they don't have it.
5. NEGATION: If a patient explicitly denies having a symptom/condition, set is_negation to true.
6. PROVENANCE: Every fact MUST include the exact source_text snippet from the transcript.

Return JSON in this format:
{
  "facts": [
    {
      "category": "chief_complaint" | "symptom" | "onset" | "severity" | "allergy" | "medication" | "chronic_condition",
      "fact_type": "reported_symptom" | "denied_symptom" | "reported_allergy" | "denied_allergy" | "reported_condition" | "denied_condition",
      "value": {"key": "value"},
      "source_text": "exact snippet",
      "confidence": "HIGH" | "MEDIUM" | "LOW",
      "confidence_score": 0.0 to 1.0,
      "is_negation": false
    }
  ]
}
"""

class GeminiNLUProvider(NLUProvider):
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is missing.")
        self.client = genai.Client(api_key=self.api_key)
        self.model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
        self.fallback = MockNLUProvider()

    def extract_candidate_facts(
        self,
        transcript: str,
        question_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExtractedFacts:
        if not transcript or not transcript.strip():
            return ExtractedFacts(transcript=transcript or "", facts=[])

        prompt = f"Question ID: {question_id or 'unknown'}\nTranscript: {transcript}\nContext: {json.dumps(context or {})}"

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
            )
            raw_text = response.text or "{}"
            data = json.loads(raw_text)
            raw_facts = data.get("facts", [])

            facts: List[CandidateFact] = []
            for rf in raw_facts:
                conf_str = rf.get("confidence", "HIGH").upper()
                conf_enum = FactConfidence.HIGH if conf_str == "HIGH" else (
                    FactConfidence.MEDIUM if conf_str == "MEDIUM" else FactConfidence.LOW
                )
                facts.append(
                    CandidateFact(
                        category=rf.get("category", "symptom"),
                        fact_type=rf.get("fact_type", "reported_symptom"),
                        value=rf.get("value", {}),
                        source_text=rf.get("source_text", transcript),
                        confidence=conf_enum,
                        confidence_score=float(rf.get("confidence_score", 0.9)),
                        is_negation=bool(rf.get("is_negation", False)),
                    )
                )

            return ExtractedFacts(
                transcript=transcript,
                question_id=question_id,
                facts=facts,
                metadata={"provider": "gemini", "model": self.model},
            )
        except Exception as e:
            logger.warning(f"Gemini NLU extraction failed, falling back to Mock provider: {e}")
            fallback_res = self.fallback.extract_candidate_facts(transcript, question_id, context)
            fallback_res.metadata["fallback_from_error"] = str(e)
            return fallback_res
