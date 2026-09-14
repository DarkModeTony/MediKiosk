import os
import uuid
import json
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional

from google import genai
from google.genai import types

from .interface import SummaryProvider
from .models import (
    ClinicalSummaryInput, ClinicalSummaryDraft, 
    ClinicalSummarySection, SummaryStatus, SourceReference, SourceType
)
from .validator import AntiHallucinationValidator

class GeminiSummaryProvider(SummaryProvider):
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is missing.")
        self.client = genai.Client(api_key=self.api_key)
        self.model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

    def generate(self, input_data: ClinicalSummaryInput) -> ClinicalSummaryDraft:
        input_payload = input_data.model_dump(exclude_none=True)
        
        system_prompt = """
You are a highly constrained medical summarization assistant.
Your task is to generate a clinical summary draft using ONLY the facts explicitly provided in the JSON input.

STRICT SAFETY RULES:
- You are generating a clinical summary, NOT a diagnosis.
- Use only facts explicitly present in the supplied structured input.
- Never infer or invent diagnoses, symptoms, medications, doses, allergies, vitals, labs, investigations, procedures, or dates.
- Never infer a medical condition merely because symptoms suggest it.
- Missing information must be represented as "Not documented".
- Preserve uncertainty when the input itself is uncertain.
- Do not create new clinical entities.
- Do not create new source references.
- Do not modify red-flag severity.
- If the input is empty or lacks information for a section, write "Not documented".
- Your output must match the requested JSON schema.
"""

        # We can pass the target schema directly using the existing ClinicalSummaryDraft schema 
        # But we need a subset model to avoid generating metadata like version/id that we manage.
        # So we'll use a local Pydantic model for Gemini's structured output.
        class LLMSourceReference(BaseModel):
            source_type: str = Field(description="Type of source (e.g. CLINICAL_INTERVIEW, MEDICAL_DOCUMENT)")
            source_id: str = Field(description="ID of the source")
            fact: str = Field(description="The exact clinical fact extracted from the input")

        class LLMSummarySection(BaseModel):
            title: str = Field(description="Title of the section (e.g., 'HISTORY OF PRESENT ILLNESS')")
            content: str = Field(description="Content of the section, relying ONLY on input facts.")

        class LLMSummaryOutput(BaseModel):
            structured_sections: List[LLMSummarySection]
            source_references: List[LLMSourceReference]

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[{"role": "user", "parts": [{"text": json.dumps(input_payload)}]}],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.0,
                    response_mime_type="application/json",
                    response_schema=LLMSummaryOutput
                )
            )
            
            if not response.text:
                raise RuntimeError("LLM failed to generate structured output. Empty response.")
                
            try:
                parsed_json = json.loads(response.text)
                parsed = LLMSummaryOutput.model_validate(parsed_json)
            except (json.JSONDecodeError, ValidationError) as e:
                raise RuntimeError(f"LLM returned invalid schema: {str(e)}")
            
            # Map adapter schema to actual ClinicalSummaryDraft
            sections = [
                ClinicalSummarySection(title=sec.title, content=sec.content)
                for sec in parsed.structured_sections
            ]
            
            refs = [
                SourceReference(
                    source_type=SourceType(ref.source_type) if ref.source_type in [e.value for e in SourceType] else SourceType.CLINICAL_INTERVIEW,
                    source_id=ref.source_id,
                    fact=ref.fact,
                    document_id=None,
                    page_number=None,
                    source_text=None,
                    confidence=None
                )
                for ref in parsed.source_references
            ]
                
            draft = ClinicalSummaryDraft(
                id=str(uuid.uuid4()),
                encounter_id="draft", # Service overrides this
                version=1,
                generated_at=datetime.utcnow(),
                provider="GeminiSummaryProvider",
                status=SummaryStatus.AI_DRAFT,
                structured_sections=sections,
                source_references=refs
            )
            
            # Run the anti-hallucination & source-reference validator
            AntiHallucinationValidator.validate(input_data, draft)
            
            return draft

        except ValueError as e:
            # Anti-hallucination failure / Source-reference failure
            raise RuntimeError(str(e))
        except Exception as e:
            if isinstance(e, RuntimeError) and ("invalid schema" in str(e) or "missing" in str(e) or "Anti-hallucination" in str(e)):
                raise e
            # API failure / connection failure / timeout
            raise RuntimeError(f"Failed to generate LLM summary: {str(e)}")
