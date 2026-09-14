import os
import uuid
import json
from datetime import datetime
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional

from .interface import SummaryProvider
from .models import (
    ClinicalSummaryInput, ClinicalSummaryDraft, 
    ClinicalSummarySection, SummaryStatus, SourceReference, SourceType
)
from .validator import AntiHallucinationValidator

# Adapter schema for LLM structured output
class LLMSourceReference(BaseModel):
    source_type: SourceType = Field(description="Type of source (e.g. CLINICAL_INTERVIEW, MEDICAL_DOCUMENT, OCR)")
    source_id: str = Field(description="ID of the source")
    fact: str = Field(description="The exact clinical fact extracted from the input")

class LLMSummarySection(BaseModel):
    title: str = Field(description="Title of the section (e.g., 'HISTORY OF PRESENT ILLNESS')")
    content: str = Field(description="Content of the section, relying ONLY on input facts.")

class LLMSummaryOutput(BaseModel):
    structured_sections: List[LLMSummarySection]
    source_references: List[LLMSourceReference]

class OpenAISummaryProvider(SummaryProvider):
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is missing.")
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-2024-08-06") # Using a model that supports structured outputs

    def generate(self, input_data: ClinicalSummaryInput) -> ClinicalSummaryDraft:
        # Serialize only structured clinical facts into the LLM request
        # Explicitly avoiding sending any backend state or objects
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
- Your output must match the provided JSON schema.
"""

        try:
            # Using OpenAI Beta Parse for guaranteed structured output schema enforcement
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(input_payload)}
                ],
                response_format=LLMSummaryOutput,
                temperature=0.0
            )
            
            parsed = response.choices[0].message.parsed
            if not parsed:
                # If parsing somehow failed (e.g., refusal)
                raise RuntimeError(f"LLM failed to generate structured output. Refusal: {response.choices[0].message.refusal}")
            
            # Map adapter schema to actual ClinicalSummaryDraft
            sections = [
                ClinicalSummarySection(title=sec.title, content=sec.content)
                for sec in parsed.structured_sections
            ]
            
            refs = [
                SourceReference(
                    source_type=ref.source_type,
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
                provider="OpenAISummaryProvider",
                status=SummaryStatus.AI_DRAFT,
                structured_sections=sections,
                source_references=refs
            )
            
            # Run the anti-hallucination & source-reference validator
            # If invalid, it raises ValueError, and the original invalid output is not saved
            AntiHallucinationValidator.validate(input_data, draft)
            
            return draft

        except ValidationError as e:
            # Schema validation failure
            raise RuntimeError(f"LLM returned invalid schema: {str(e)}")
        except ValueError as e:
            # Anti-hallucination failure / Source-reference failure
            raise RuntimeError(str(e))
        except Exception as e:
            # API failure / connection failure / timeout
            raise RuntimeError(f"Failed to generate LLM summary: {str(e)}")
