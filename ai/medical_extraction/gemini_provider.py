import os
import re
import json
from typing import Optional
from google import genai
from google.genai import types

from .interface import ExtractionProvider
from .models import ExtractedEntities, ConfidenceLevel

def conservative_normalize(text: str) -> str:
    """Conservatively normalize text for evidence comparison."""
    if not text:
        return ""
    # Lowercase
    t = text.lower()
    # Replace line breaks and tabs with spaces
    t = re.sub(r'[\r\n\t]', ' ', t)
    # Remove surrounding punctuation safely (keep internal punctuation like 10/09/2026)
    # Just collapse whitespace
    t = re.sub(r'\s+', ' ', t).strip()
    return t

class GeminiExtractionProvider(ExtractionProvider):
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is missing.")
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-3.6-flash"

    def extract(self, text: str, page_number: int) -> ExtractedEntities:
        if not text or not text.strip():
            return ExtractedEntities()

        system_prompt = """
You are a medical document information extraction system.

Extract ONLY medical information explicitly present in the supplied OCR text.

Do not infer.
Do not guess.
Do not diagnose.
Do not complete missing information.
Do not invent medication doses.
Do not invent medication frequencies.
Do not invent laboratory values.
Do not invent reference ranges.
Do not invent diagnoses.
Do not invent procedures.
Do not invent surgeries.
Do not invent allergies.
Do not invent dates.

If information is not explicitly present, leave the corresponding field null.
Extraction is transcription/structuring, not medical interpretation.

Map allergies, procedures, and surgeries into the `other` list.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[{"role": "user", "parts": [{"text": text}]}],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.0,
                    response_mime_type="application/json",
                    response_schema=ExtractedEntities
                )
            )
            
            if not response.text:
                raise ValueError("Gemini returned empty response")
                
            try:
                parsed_json = json.loads(response.text)
                entities = ExtractedEntities.model_validate(parsed_json)
            except Exception as e:
                raise ValueError(f"Failed to parse or validate schema: {e}")
                
            # Deterministic evidence validation
            return self._validate_evidence(text, entities, page_number)
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            raise RuntimeError(f"Gemini API failure during extraction: {e}")

    def _validate_evidence(self, ocr_text: str, entities: ExtractedEntities, page_number: int) -> ExtractedEntities:
        normalized_ocr = conservative_normalize(ocr_text)
        validated = ExtractedEntities()
        
        def check_evidence(field_value: Optional[str], source_text: str) -> bool:
            if not field_value:
                return True # Missing is fine
            norm_val = conservative_normalize(field_value)
            norm_src = conservative_normalize(source_text)
            # Both field and source text must be present in OCR
            if norm_val not in normalized_ocr or norm_src not in normalized_ocr:
                return False
            # Ensure field value is present within the source text as well
            if norm_val not in norm_src:
                return False
            return True

        for med in entities.medications:
            # Must have source text, and source text must exist in OCR
            if not med.source_text or conservative_normalize(med.source_text) not in normalized_ocr:
                continue
            
            if not check_evidence(med.name, med.source_text): continue
            if not check_evidence(med.strength, med.source_text): continue
            if not check_evidence(med.frequency, med.source_text): continue
            if not check_evidence(med.route, med.source_text): continue
            
            med.page_number = page_number
            med.confidence_level = ConfidenceLevel.HIGH # Standardize since we do strict deterministic validation
            validated.medications.append(med)
            
        for lab in entities.lab_results:
            if not lab.source_text or conservative_normalize(lab.source_text) not in normalized_ocr:
                continue
                
            if not check_evidence(lab.test_name, lab.source_text): continue
            if not check_evidence(lab.value, lab.source_text): continue
            if not check_evidence(lab.unit, lab.source_text): continue
            if not check_evidence(lab.reference_low, lab.source_text): continue
            if not check_evidence(lab.reference_high, lab.source_text): continue
            
            lab.page_number = page_number
            lab.confidence_level = ConfidenceLevel.HIGH
            # Wipe abnormal flag to let downstream handle it, unless explicitly extracted safely?
            # Actually, requirements say: "Preserve existing downstream abnormal-lab logic."
            lab.abnormal_flag = None
            validated.lab_results.append(lab)
            
        for diag in entities.diagnoses:
            if not diag.source_text or conservative_normalize(diag.source_text) not in normalized_ocr:
                continue
                
            if not check_evidence(diag.diagnosis, diag.source_text): continue
            
            diag.page_number = page_number
            diag.confidence_level = ConfidenceLevel.HIGH
            validated.diagnoses.append(diag)
            
        for pat in entities.patient_info:
            if not pat.source_text or conservative_normalize(pat.source_text) not in normalized_ocr:
                continue
                
            if not check_evidence(pat.value, pat.source_text): continue
            pat.page_number = page_number
            pat.confidence_level = ConfidenceLevel.HIGH
            validated.patient_info.append(pat)
            
        for other in entities.other:
            if not other.source_text or conservative_normalize(other.source_text) not in normalized_ocr:
                continue
                
            if not check_evidence(other.value, other.source_text): continue
            other.page_number = page_number
            other.confidence_level = ConfidenceLevel.HIGH
            validated.other.append(other)
            
        if entities.document_date:
            norm_date = conservative_normalize(entities.document_date)
            if norm_date in normalized_ocr:
                validated.document_date = entities.document_date

        return validated
