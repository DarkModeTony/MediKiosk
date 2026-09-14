from typing import Dict, Any, List
from datetime import datetime
import uuid

class RedFlag:
    def __init__(self, rule_name: str, evidence: dict, severity: str):
        self.id = str(uuid.uuid4())
        self.rule_name = rule_name
        self.evidence = evidence
        self.severity = severity
        self.timestamp = datetime.utcnow()
        self.status = "ACTIVE"

class RedFlagEngine:
    def evaluate(self, facts: Dict[str, Any]) -> List[RedFlag]:
        """
        Deterministic rule evaluation for red flags.
        Facts here is a dict mapping field to Fact objects.
        """
        flags = []
        
        # Helper to get fact value safely
        def get_val(field: str):
            fact = facts.get(field)
            if fact and fact.state == "COLLECTED":
                return str(fact.value).lower()
            return None

        # Rule 1: Chest Pain + Shortness of breath
        if get_val("chief_complaint") == "chest pain" or get_val("chief_complaint_initial") == "chest pain":
            if get_val("shortness_of_breath") in ["yes_severe", "yes_mild", "yes"]:
                flags.append(RedFlag(
                    rule_name="CARDIAC_EMERGENCY_SUSPECTED",
                    evidence={"chief_complaint": "chest pain", "shortness_of_breath": "yes"},
                    severity="HIGH"
                ))

        # Rule 2: Sudden onset severe headache (Thunderclap)
        if get_val("chief_complaint") == "headache" and get_val("onset") == "sudden":
             flags.append(RedFlag(
                 rule_name="THUNDERCLAP_HEADACHE",
                 evidence={"complaint": "headache", "onset": "sudden"},
                 severity="HIGH"
             ))

        # Rule 3: Very high fever
        if get_val("severity") == "very_high":
            flags.append(RedFlag(
                 rule_name="HIGH_GRADE_FEVER",
                 evidence={"fever_severity": "very_high"},
                 severity="MEDIUM"
             ))

        return flags
