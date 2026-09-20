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
            "chest pain": ["chest pain", "chest", "सीने में दर्द", "सीने", "छाती", "heart pain", "chhati", "chest discomfort"],
            "headache": ["headache", "head pain", "head hurts", "sar dard", "sir dard", "sar me dard", "sir me dard", "migraine", "matha", "माथा", "सिर दर्द", "सर दर्द", "सिर में दर्द", "सर में दर्द"],
            "abdominal pain": ["stomach pain", "stomach ache", "stomach hurts", "abdominal pain", "stomach", "abdominal", "pet dard", "pet me dard", "पेट में दर्द", "पेट दर्द", "पेट", "belly pain", "tummy ache"],
            "fever": ["fever", "high fever", "बुखार", "ताप", "temperature", "bukhar", "tez bukhar", "तेज बुखार"],
            "cough": ["cough", "खांसी", "khansi", "balgham", "phlegm", "coughing"],
            "shortness of breath": ["shortness of breath", "breath", "सांस", "dyspnea", "saans", "difficulty breathing", "सांस लेने में तकलीफ"],
            "vomiting": ["vomit", "vomiting", "उल्टी", "nausea", "जी मिचलाना", "ulti", "throwing up", "puking"],
            "dizziness": ["dizzy", "dizziness", "chakkar", "चक्कर", "lightheaded", "faint", "सिर चकराना"],
            "weakness": ["weakness", "kamzori", "कमजोरी", "fatigue", "tiredness", "exhaustion", "weak"],
            "body ache": ["body ache", "badan dard", "बदन दर्द", "body pain"],
        }

        detected_symptoms = []
        for symptom_name, keywords in symptom_map.items():
            for kw in keywords:
                if kw in t:
                    detected_symptoms.append(symptom_name)
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

        if detected_symptoms and question_id == "chief_complaint_initial":
            primary = detected_symptoms[0]
            facts.append(
                CandidateFact(
                    category="chief_complaint",
                    fact_type="chief_complaint",
                    value={"complaint": primary, "all_symptoms": detected_symptoms},
                    source_text=transcript,
                    confidence=FactConfidence.HIGH,
                    confidence_score=0.95,
                )
            )
        elif question_id == "chief_complaint_initial" and not detected_symptoms and transcript:
            facts.append(
                CandidateFact(
                    category="chief_complaint",
                    fact_type="chief_complaint",
                    value={"complaint": transcript, "all_symptoms": []},
                    source_text=transcript,
                    confidence=FactConfidence.MEDIUM,
                    confidence_score=0.75,
                )
            )

        # 2. Onset
        onset_val = None
        if any(w in t for w in ["sudden", "thunderclap", "suddenly", "अचानक"]):
            onset_val = "sudden"
        elif "today" in t or "आज" in t:
            onset_val = "today"
        elif "yesterday" in t or "कल" in t:
            onset_val = "yesterday"
        elif "morning" in t or "सुबह" in t:
            onset_val = "morning"
        elif "hour" in t or "घंटे" in t:
            onset_val = "hours"
        elif "days" in t or "दिन" in t:
            match = re.search(r"(\d+|one|two|three|four|five|six|seven|ten|एक|दो|तीन|चार)\s*(days?|दिन)", t)
            onset_val = f"{match.group(1)} days ago" if match else "few days ago"

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
