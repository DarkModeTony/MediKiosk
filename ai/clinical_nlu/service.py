from typing import Dict, Any

class ClinicalNLUService:
    def extract_facts(self, transcript: str, question_id: str) -> Dict[str, Any]:
        """
        Mock NLU layer. Extracts structured facts from transcript.
        DOES NOT diagnose.
        """
        t = transcript.lower()
        facts = {}
        
        # Chief complaint extraction mock
        if question_id == "chief_complaint_initial":
            if "chest" in t or "सीने" in t:
                facts["chief_complaint"] = "chest pain"
            elif "fever" in t or "बुखार" in t:
                facts["chief_complaint"] = "fever"
            elif "stomach" in t or "पेट" in t:
                facts["chief_complaint"] = "abdominal pain"
            else:
                facts["chief_complaint"] = transcript
        
        # Mock answers for other fields based on keywords
        if "today" in t or "आज" in t:
            facts["onset"] = "today"
        elif "yesterday" in t or "कल" in t:
            facts["onset"] = "yesterday"
            
        if "severe" in t or "तेज" in t:
            facts["severity"] = "severe"
            
        return facts
