import sys
import os
import uuid
from datetime import datetime

# Ensure import paths work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ai.summarization.validator import AntiHallucinationValidator
from ai.summarization.models import ClinicalSummaryInput, ClinicalSummaryDraft, ClinicalSummarySection, SourceReference, SummaryStatus, SourceType

# Base valid input
input_data = ClinicalSummaryInput(
    chief_complaint="Patient presents with mild fever and cough.",
    history_of_present_illness="Symptoms started 2 days ago.",
    symptoms=["fever", "cough"],
    past_medical_history=["hypertension"],
    past_surgical_history=["appendectomy"],
    medications=["lisinopril 10mg"],
    allergies=["penicillin"],
    family_history=["none"],
    personal_history=["none"],
    review_of_systems=["normal"],
    investigations=["CBC normal"],
    procedures=["none"],
    ayush_history=["none"],
    red_flags=[{"alert": "fever"}],
    previous_documents=["old records reviewed"]
)

def build_draft(content: str, refs: list = None) -> ClinicalSummaryDraft:
    return ClinicalSummaryDraft(
        id=str(uuid.uuid4()),
        encounter_id="123",
        provider="Audit",
        status=SummaryStatus.AI_DRAFT,
        generated_at=datetime.utcnow(),
        structured_sections=[
            ClinicalSummarySection(title="Clinical Summary", content=content)
        ],
        source_references=refs or [],
        version=1
    )

def expect_reject(test_name: str, draft: ClinicalSummaryDraft):
    try:
        AntiHallucinationValidator.validate(input_data, draft)
        print(f"FAIL (False Negative) - {test_name}: Validator incorrectly ACCEPTED.")
        return False
    except ValueError as e:
        print(f"PASS - {test_name}: Correctly REJECTED. ({str(e)})")
        return True

def expect_accept(test_name: str, draft: ClinicalSummaryDraft):
    try:
        AntiHallucinationValidator.validate(input_data, draft)
        print(f"PASS - {test_name}: Correctly ACCEPTED.")
        return True
    except ValueError as e:
        print(f"FAIL (False Positive) - {test_name}: Validator incorrectly REJECTED. ({str(e)})")
        return False

print("--- ADVERSARIAL AUDIT START ---")

passed = 0
total = 0

# 1. Invented diagnosis
total += 1
passed += 1 if expect_reject("1. Invented diagnosis", build_draft("Patient has diabetes.")) else 0

# 2. Invented medication
total += 1
passed += 1 if expect_reject("2. Invented medication", build_draft("Patient is taking ibuprofen.")) else 0

# 3. Invented medication dose
total += 1
passed += 1 if expect_reject("3. Invented medication dose", build_draft("Patient is taking lisinopril 20mg.")) else 0

# 4. Invented lab value
total += 1
passed += 1 if expect_reject("4. Invented lab value", build_draft("CBC showed hemoglobin 8.5.")) else 0

# 5. Invented laboratory test
total += 1
passed += 1 if expect_reject("5. Invented laboratory test", build_draft("MRI of brain was normal.")) else 0

# 6. Invented procedure
total += 1
passed += 1 if expect_reject("6. Invented procedure", build_draft("Patient underwent endoscopy.")) else 0

# 7. Invented surgery
total += 1
passed += 1 if expect_reject("7. Invented surgery", build_draft("Past surgical history of cholecystectomy.")) else 0

# 8. Invented allergy
total += 1
passed += 1 if expect_reject("8. Invented allergy", build_draft("Patient is allergic to sulfa.")) else 0

# 9. Invented symptom
total += 1
passed += 1 if expect_reject("9. Invented symptom", build_draft("Patient complains of severe chest pain.")) else 0

# 10. Invented vital sign
total += 1
passed += 1 if expect_reject("10. Invented vital sign", build_draft("Blood pressure is 180/100.")) else 0

# 11. Invented date
total += 1
passed += 1 if expect_reject("11. Invented date", build_draft("Symptoms started on 2023-05-15.")) else 0

# 12. Invented source reference
total += 1
draft = build_draft("Patient has fever.", [SourceReference(source_type=SourceType.OTHER, source_id="1", fact="Patient had chest pain")])
passed += 1 if expect_reject("12. Invented source reference", draft) else 0

# 13. Valid clinical paraphrase
total += 1
passed += 1 if expect_accept("13. Valid clinical paraphrase", build_draft("Patient presents with a mild fever and cough. Takes lisinopril 10mg.")) else 0

# 14. Common structural words
total += 1
passed += 1 if expect_accept("14. Common structural words", build_draft("Chief complaint and relevant medical history evaluated.")) else 0

# 15. "severity", "onset", "documents", "demographics", "complaints", "AYUSH"
total += 1
passed += 1 if expect_accept("15. Allowed safe words", build_draft("AYUSH demographics: Onset and severity of complaints based on documents.")) else 0

# 16. Rejected OCR entity (something not in input)
total += 1
passed += 1 if expect_reject("16. Rejected OCR entity", build_draft("Optical character recognition showed tachycardia.")) else 0

# 17. Unsupported clinical entity hidden inside a natural-language sentence
total += 1
passed += 1 if expect_reject("17. Hidden entity", build_draft("The patient was feeling fine until they suddenly developed asthma yesterday.")) else 0

# 18. Unsupported medication with a plausible dose
total += 1
passed += 1 if expect_reject("18. Plausible dose wrong med", build_draft("Patient was prescribed amoxicillin 500mg.")) else 0

# 19. Unsupported diagnosis expressed using a synonym
total += 1
passed += 1 if expect_reject("19. Unsupported diagnosis synonym", build_draft("Patient suffered a myocardial infarction.")) else 0

# 20. Unsupported lab expressed using a synonym
total += 1
passed += 1 if expect_reject("20. Unsupported lab synonym", build_draft("Erythrocyte sedimentation rate was high.")) else 0

print(f"--- SUMMARY: {passed}/{total} PASSED ---")
