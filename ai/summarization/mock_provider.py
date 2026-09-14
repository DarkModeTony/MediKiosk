import uuid
from datetime import datetime
from typing import List
from .interface import SummaryProvider
from .models import (
    ClinicalSummaryInput, ClinicalSummaryDraft, 
    ClinicalSummarySection, SummaryStatus
)

class MockSummaryProvider(SummaryProvider):
    def generate(self, input_data: ClinicalSummaryInput) -> ClinicalSummaryDraft:
        sections = []
        
        # Helper to avoid "inventing" empty sections
        def add_section(title: str, content: str):
            sections.append(ClinicalSummarySection(title=title, content=content))
            
        def safe_join(items: List[str], fallback: str = "Not documented") -> str:
            return ", ".join(items) if items else fallback

        # 1. Chief Complaint
        if input_data.chief_complaint:
            add_section("CHIEF COMPLAINT", input_data.chief_complaint)
        else:
            add_section("CHIEF COMPLAINT", "Not documented")

        # 2. Symptoms / HPI
        if input_data.symptoms or input_data.history_of_present_illness:
            hpi = input_data.history_of_present_illness or ""
            if input_data.symptoms:
                symps = "Reported symptoms: " + ", ".join(input_data.symptoms)
                hpi = f"{symps}\n{hpi}".strip()
            add_section("HISTORY OF PRESENT ILLNESS", hpi)
        else:
            add_section("HISTORY OF PRESENT ILLNESS", "Not documented")
            
        # 3. Medical History
        add_section("RELEVANT MEDICAL HISTORY", safe_join(input_data.past_medical_history))
        add_section("PAST SURGICAL HISTORY", safe_join(input_data.past_surgical_history))
        add_section("CURRENT MEDICATIONS", safe_join(input_data.medications))
        add_section("ALLERGIES", safe_join(input_data.allergies))
        add_section("FAMILY / PERSONAL HISTORY", safe_join(input_data.family_history + input_data.personal_history))
        add_section("REVIEW OF SYSTEMS", safe_join(input_data.review_of_systems))
        add_section("INVESTIGATIONS", safe_join(input_data.investigations))
        add_section("PROCEDURES", safe_join(input_data.procedures))

        # 4. Red Flags
        if input_data.red_flags:
            rf_texts = []
            for rf in input_data.red_flags:
                rf_texts.append(f"Priority: {rf.get('severity', 'UNKNOWN')}\nReason: {rf.get('rule_name', 'Rule fired')} detected by clinical rules.")
            add_section("RED FLAGS / PRIORITY", "\n\n".join(rf_texts))
        else:
            add_section("RED FLAGS / PRIORITY", "None identified")
            
        # 5. Documents
        add_section("PREVIOUS MEDICAL RECORDS", safe_join(input_data.previous_documents))

        # 6. Overall Summary
        # Simple dynamic deterministic summary based strictly on input length and presence
        summary_text = f"Patient presented with {len(input_data.symptoms)} symptoms. "
        if input_data.medications:
            summary_text += f"Currently on {len(input_data.medications)} medications. "
        if input_data.investigations:
            summary_text += f"Has {len(input_data.investigations)} previous lab results on file. "
        if input_data.red_flags:
            summary_text += "HIGH PRIORITY: Red flags were detected during intake and require immediate attention."
        
        add_section("CLINICAL SUMMARY", summary_text.strip())

        # No references generated here, the Aggregator is responsible for gathering source references
        # But if the provider wanted to cite them, it could. The architecture leaves references mostly 
        # to the aggregator to attach, or we return an empty list and aggregator fills it.
        
        return ClinicalSummaryDraft(
            id=str(uuid.uuid4()),
            encounter_id="draft", # to be overwritten by service
            version=1,
            generated_at=datetime.utcnow(),
            provider="MockSummaryProvider",
            status=SummaryStatus.AI_DRAFT,
            structured_sections=sections,
            source_references=[] # Provided by aggregator usually
        )
