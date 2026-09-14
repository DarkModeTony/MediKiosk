import re
from typing import Set
from .models import ClinicalSummaryInput, ClinicalSummaryDraft

class AntiHallucinationValidator:
    """
    Validates a generated ClinicalSummaryDraft against its ClinicalSummaryInput 
    to ensure no hallucinated clinical entities (diagnoses, meds, etc.) are present.
    """
    
    @staticmethod
    def _normalize_text(text: str) -> Set[str]:
        if not text:
            return set()
        # Lowercase, remove punctuation, split into tokens including numbers
        words = re.findall(r'\b[a-z0-9]+\b', text.lower())
        
        # Stopwords to ignore
        stop_words = {
            "and", "or", "the", "a", "an", "is", "are", "was", "were", "to", "of", "in", 
            "for", "with", "on", "at", "by", "patient", "has", "had", "been", "not", 
            "documented", "none", "identified", "reported", "denied", "stated", "showed",
            "no", "yes", "he", "she", "it", "they", "his", "her", "their", "from", "as",
            "an", "but", "if", "we", "you", "this", "that", "these", "those"
        }
        return set(w for w in words if w not in stop_words)

    @classmethod
    def validate(cls, input_data: ClinicalSummaryInput, draft: ClinicalSummaryDraft) -> bool:
        # 1. Gather all allowed tokens from the input
        allowed_tokens = set()
        
        def add_tokens(text_source):
            if isinstance(text_source, str):
                allowed_tokens.update(cls._normalize_text(text_source))
            elif isinstance(text_source, list):
                for item in text_source:
                    if isinstance(item, str):
                        allowed_tokens.update(cls._normalize_text(item))
                    elif isinstance(item, dict):
                        for v in item.values():
                            if isinstance(v, str):
                                allowed_tokens.update(cls._normalize_text(v))
                                
        if input_data.patient_context:
            add_tokens([str(v) for v in input_data.patient_context.values()])
        if input_data.encounter_context:
            add_tokens([str(v) for v in input_data.encounter_context.values()])
            
        add_tokens(input_data.chief_complaint)
        add_tokens(input_data.history_of_present_illness)
        add_tokens(input_data.symptoms)
        add_tokens(input_data.past_medical_history)
        add_tokens(input_data.past_surgical_history)
        add_tokens(input_data.medications)
        add_tokens(input_data.allergies)
        add_tokens(input_data.family_history)
        add_tokens(input_data.personal_history)
        add_tokens(input_data.review_of_systems)
        add_tokens(input_data.ayush_history)
        add_tokens(input_data.investigations)
        add_tokens(input_data.procedures)
        add_tokens(input_data.red_flags)
        add_tokens(input_data.previous_documents)

        # Standard section titles and formatting terms
        allowed_tokens.update(cls._normalize_text(
            "chief complaint history present illness relevant medical past surgical "
            "current medications allergies family personal review systems investigations "
            "procedures red flags priority previous records clinical summary provider "
            "status priority reason detected by rules ayush"
        ))
        
        # Supported paraphrasing / clinical connector terms
        paraphrases = {
            "presents", "complains", "complaints", "reports", "denies", "states", "shows", "indicates", 
            "normal", "abnormal", "elevated", "decreased", "stable", "severe", "mild", 
            "moderate", "daily", "weekly", "monthly", "years", "days", "months", "old",
            "male", "female", "symptoms", "results", "file", "intake", "immediate", "attention",
            "currently", "taking", "takes", "diagnosed", "treated", "mg", "ml", "mcg", "dose", "tablet",
            "name", "time", "demographics", "gender", "details", "encounter", "start", "date", "unknown", "information",
            "condition", "conditions", "history", "presenting", "illnesses", "severity", "onset", "duration",
            "absent", "nil", "null", "none", "notes", "type", "finding", "findings", "clinical", "status",
            "rule", "rules", "ruled", "out", "document", "documents", "context", "patient", "encounters", "record", "records",
            "identification", "data", "assessment", "plan", "provided", "summary", "other", "about", "which", "there"
        }
        allowed_tokens.update(paraphrases)
        
        # 2. Validate generated sections for unsupported entities
        for section in draft.structured_sections:
            section_tokens = cls._normalize_text(section.title + " " + section.content)
            # Find unsupported tokens
            unsupported = section_tokens - allowed_tokens
            
            # If there are highly specific words/numbers not in the input (len > 4 to catch actual terms), reject
            unsupported_long = [w for w in unsupported if len(w) > 4 or w.isdigit() or any(c.isdigit() for c in w)]
            if unsupported_long:
                raise ValueError(f"Anti-hallucination validation failed. Unsupported clinical entities detected: {unsupported_long}")

        # 3. Validate source references
        input_texts = set()
        for src_list in [input_data.symptoms, input_data.past_medical_history, input_data.past_surgical_history, input_data.medications, input_data.allergies, input_data.investigations, input_data.procedures]:
            for item in src_list:
                input_texts.add(item.lower().strip())
        if input_data.chief_complaint:
            input_texts.add(input_data.chief_complaint.lower().strip())
        if input_data.history_of_present_illness:
            input_texts.add(input_data.history_of_present_illness.lower().strip())
            
        for ref in draft.source_references:
            if not ref.fact:
                continue
                
            # Exact or normalized match
            ref_norm = ref.fact.lower().strip()
            
            found = False
            for it in input_texts:
                # Substring check for references is acceptable if we normalize, but token overlap is better
                if ref_norm in it or it in ref_norm:
                    found = True
                    break
            
            if not found:
                # Try token overlap for paraphrase support
                ref_tokens = cls._normalize_text(ref.fact)
                if ref_tokens and ref_tokens.issubset(allowed_tokens):
                    found = True
                    
            if not found:
                raise ValueError(f"Source reference validation failed: Fact '{ref.fact}' not found in input.")

        return True
