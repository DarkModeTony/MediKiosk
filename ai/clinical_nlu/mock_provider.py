import re
from typing import Optional, Dict, Any, List
from .interface import NLUProvider
from .models import ExtractedFacts, CandidateFact, FactConfidence

class MockNLUProvider(NLUProvider):
    """
    Deterministic rule- and keyword-based Clinical NLU provider.
    Used for local testing, offline demo, and unit tests.
    """

    def extract_candidate_facts(
        self,
        transcript: str,
        question_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExtractedFacts:
        t = transcript.lower().strip()
        facts: List[CandidateFact] = []

        # 1. Chief Complaint & Symptoms
        symptom_map = {
            "chest pain": ["chest", "सीने", "छाती"],
            "fever": ["fever", "बुखार", "ताप"],
            "abdominal pain": ["stomach", "abdominal", "पेट"],
            "headache": ["headache", "सर दर्द", "सिर दर्द"],
            "cough": ["cough", "खांसी"],
            "shortness of breath": ["breath", "सांस", "dyspnea"],
            "vomiting": ["vomit", "उल्टी"],
        }

        detected_symptom = None
        for symptom_name, keywords in symptom_map.items():
            for kw in keywords:
                if kw in t:
                    detected_symptom = symptom_name
                    facts.append(
                        CandidateFact(
                            category="symptom",
                            fact_type="reported_symptom",
                            value={"name": symptom_name},
                            source_text=kw,
                            confidence=FactConfidence.HIGH,
                            confidence_score=0.95,
                            is_negation=False,
                        )
                    )
                    break
            if detected_symptom and question_id == "chief_complaint_initial":
                facts.append(
                    CandidateFact(
                        category="chief_complaint",
                        fact_type="chief_complaint",
                        value={"complaint": detected_symptom},
                        source_text=transcript,
                        confidence=FactConfidence.HIGH,
                        confidence_score=0.95,
                    )
                )
                break

        if question_id == "chief_complaint_initial" and not detected_symptom and transcript:
            facts.append(
                CandidateFact(
                    category="chief_complaint",
                    fact_type="chief_complaint",
                    value={"complaint": transcript},
                    source_text=transcript,
                    confidence=FactConfidence.MEDIUM,
                    confidence_score=0.75,
                )
            )

        # 2. Onset
        onset_val = None
        if "today" in t or "आज" in t:
            onset_val = "today"
        elif "yesterday" in t or "कल" in t:
            onset_val = "yesterday"
        elif "days" in t or "दिन" in t:
            match = re.search(r"(\d+)\s*(days?|दिन)", t)
            onset_val = f"{match.group(1)} days ago" if match else "recent"

        if onset_val:
            facts.append(
                CandidateFact(
                    category="onset",
                    fact_type="onset_time",
                    value={"onset": onset_val},
                    source_text=onset_val,
                    confidence=FactConfidence.HIGH,
                    confidence_score=0.9,
                )
            )

        # 3. Severity
        if any(w in t for w in ["severe", "तेज", "very high", "unbearable", "bahut"]):
            facts.append(
                CandidateFact(
                    category="severity",
                    fact_type="symptom_severity",
                    value={"severity": "severe"},
                    source_text="severe",
                    confidence=FactConfidence.HIGH,
                    confidence_score=0.9,
                )
            )
        elif any(w in t for w in ["mild", "हल्का", "slight"]):
            facts.append(
                CandidateFact(
                    category="severity",
                    fact_type="symptom_severity",
                    value={"severity": "mild"},
                    source_text="mild",
                    confidence=FactConfidence.HIGH,
                    confidence_score=0.9,
                )
            )

        # 4. Allergy statements (reported or denied)
        if "allergic to" in t or "allergy to" in t or "एलर्जी" in t:
            for allergen in ["penicillin", "aspirin", "sulfa", "paracetamol", "peanuts"]:
                if allergen in t:
                    facts.append(
                        CandidateFact(
                            category="allergy",
                            fact_type="reported_allergy",
                            value={"allergen": allergen.capitalize(), "reaction": "unspecified"},
                            source_text=f"allergic to {allergen}",
                            confidence=FactConfidence.HIGH,
                            confidence_score=0.9,
                        )
                    )

        # 5. Chronic conditions (reported or denied)
        for condition, pattern in [("Type 2 Diabetes", "diabetes"), ("Hypertension", "bp"), ("Asthma", "asthma")]:
            if pattern in t:
                is_neg = any(neg in t for neg in ["no ", "don't have", "not have", "नहीं"])
                facts.append(
                    CandidateFact(
                        category="chronic_condition",
                        fact_type="denied_condition" if is_neg else "reported_condition",
                        value={"condition": condition, "status": "denied" if is_neg else "active"},
                        source_text=transcript,
                        confidence=FactConfidence.HIGH,
                        confidence_score=0.9,
                        is_negation=is_neg,
                    )
                )

        return ExtractedFacts(
            transcript=transcript,
            question_id=question_id,
            facts=facts,
            metadata={"provider": "mock", "raw_length": len(transcript)},
        )
