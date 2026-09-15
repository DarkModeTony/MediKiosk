# MediPlatform Chatbot — Detailed Functional Specification

## 1. Purpose

The MediPlatform chatbot is a **patient-facing conversational clinical intake and longitudinal-history assistant**.

Its purpose is to:
- communicate naturally with patients;
- collect relevant clinical information;
- retrieve relevant information from the patient's longitudinal record;
- identify potential clinical red flags according to predefined safety rules;
- convert conversation into structured candidate medical facts;
- maintain continuity across encounters;
- prepare useful, structured information for the doctor;
- explain existing patient/clinical information in understandable language.

The chatbot is **not** the final clinical decision-maker. The healthcare professional remains responsible for diagnosis, treatment decisions, verification, and clinical sign-off.

---

## 2. Core Design Principle

### Supabase is the source of truth; Gemini is the reasoning/conversation layer.

The chatbot should never treat the LLM conversation itself as permanent memory.

Recommended architecture:

```text
Patient
   |
   v
Chatbot / Voice Interface
   |
   v
Gemini Conversation + Clinical NLU
   |
   v
Candidate Facts / Intent / Red Flags
   |
   v
Deterministic Validation + Safety Rules
   |
   +----------------------+
   |                      |
   v                      v
patient_facts       conversation/event data
   |
   v
Longitudinal Profile Builder
   |
   v
patient_longitudinal_profiles.profile (JSONB)
   |
   v
Relevant Patient Context
   |
   v
Gemini on future encounters
```

The LLM should **not directly and silently mutate verified patient records**.

---

# 3. Required Chatbot Functions

## 3.1 Conversational Patient Interaction

The chatbot should understand natural-language patient messages rather than requiring rigid forms.

Examples:

> "My stomach has been hurting since yesterday."

> "I had surgery on my left knee three years ago."

> "I am allergic to penicillin."

> "I lost my left eye after an accident."

The chatbot should identify:
- what the patient is saying;
- whether the information is current or historical;
- whether it relates to the current complaint;
- whether additional clarification is required;
- whether it could represent a safety/red-flag condition.

### The chatbot should ask follow-up questions when necessary.

For example:

Patient:

> "My chest hurts."

Possible follow-up topics:
- when it started;
- severity;
- location;
- whether it is worsening;
- associated symptoms;
- relevant known history.

The chatbot should avoid asking unnecessary questions that are already answered by the patient's longitudinal record.

---

# 4. Longitudinal Patient Memory

This is one of the most important functions of the MediPlatform chatbot.

The system should maintain continuity across multiple encounters.

The chatbot should be able to retrieve relevant historical information such as:

### Medical history
- diagnoses;
- chronic conditions;
- previous illnesses;
- previous hospitalizations;
- previous surgeries;
- previous procedures.

### Medication history
- current medications;
- previous medications;
- medication status;
- known medication-related information.

### Allergies
- drug allergies;
- food allergies;
- environmental allergies;
- reaction information where available.

### Anatomical information
- missing limbs;
- missing digits;
- missing eyes;
- surgically removed organs/body parts;
- paralysis;
- chronic wounds;
- scars;
- other documented anatomical conditions.

### Devices
- prosthetic limbs;
- artificial eyes;
- implants;
- hearing aids;
- assistive devices;
- other medical devices.

### Functional information
- mobility limitations;
- vision status;
- hearing status;
- speech limitations;
- activities of daily living;
- use of assistive equipment.

### Previous encounters
- previous complaints;
- relevant clinical summaries;
- previous red flags;
- doctor-verified information.

---

# 5. Unknown Must Not Mean No

This rule must be enforced throughout the chatbot and database.

## Correct

```json
{
  "left_eye": {
    "present": null,
    "status": "unknown"
  }
}
```

means:

> The system does not know whether the left eye is present.

Whereas:

```json
{
  "left_eye": {
    "present": false,
    "status": "absent"
  }
}
```

means:

> The left eye is known to be absent.

The chatbot must never infer:

```text
No information about X
        =
X does not exist
```

This is especially important for:
- missing limbs;
- missing eyes;
- allergies;
- medications;
- diseases;
- implants;
- pregnancy/reproductive information;
- functional limitations.

---

# 6. Anatomical / Body-Site Memory

The chatbot should support detailed anatomical information.

A flexible body-site model is preferable to hardcoding only arms and legs.

Example:

```json
{
  "body_site": "left_eye",
  "laterality": "left",
  "status": "absent",
  "cause": "trauma",
  "date": "2018-04-12",
  "prosthetic": false,
  "verified": false
}
```

This design can represent:

- left/right eye;
- left/right arm;
- left/right leg;
- fingers/toes;
- organs;
- prosthetic limbs;
- artificial eyes;
- implants;
- other body sites.

The system should support laterality where applicable:

```text
left
right
bilateral
midline
not_applicable
unknown
```

---

# 7. Clinical Intake

The chatbot should collect information before or during an encounter.

Minimum intake areas:

## Patient Complaint
- chief complaint;
- symptom description;
- onset;
- duration;
- severity;
- location;
- progression.

## Associated Symptoms
Relevant symptoms should be collected based on the patient's complaint.

## Medical History
Retrieve existing history first and ask only for missing/relevant information.

## Medication
Ask about medications when clinically relevant.

## Allergies
Ask about allergies when information is missing or needs confirmation.

## Previous Procedures
Retrieve known procedures and ask for clarification if relevant.

## Functional Status
Collect relevant mobility, sensory, or functional limitations.

## Safety Information
Identify predefined red flags and escalate according to project rules.

---

# 8. Context-Aware Conversation

The chatbot should not dump the entire patient database into Gemini for every message.

Instead:

```text
Patient message
      |
      v
Determine intent/topic
      |
      v
Retrieve relevant facts
      |
      v
Retrieve relevant previous encounters/documents
      |
      v
Build minimal clinical context
      |
      v
Gemini
```

For example, if the patient says:

> "My knee is hurting again."

The system should prioritize:

```text
Relevant history:
- previous knee problems;
- previous knee surgery;
- previous knee encounters;
- relevant medications;
- relevant red flags.
```

It should not necessarily send unrelated information such as an old vaccination record.

This improves:
- privacy;
- performance;
- token usage;
- relevance;
- safety.

---

# 9. Candidate Medical Fact Extraction

The chatbot should convert meaningful patient statements into structured candidate facts.

Example:

Patient:

> "I lost my left eye in an accident eight years ago."

Candidate fact:

```json
{
  "category": "anatomy",
  "fact_type": "body_part_presence",
  "body_site": "eye",
  "laterality": "left",
  "value": {
    "present": false,
    "cause": "trauma",
    "time_expression": "eight years ago"
  },
  "status": "absent",
  "source_type": "patient_statement",
  "verified": false
}
```

The candidate fact should then pass validation before being incorporated into the longitudinal record.

---

# 10. Fact Provenance

Every important patient fact should have provenance.

The system should be able to answer:

> Where did this information come from?

Possible sources:

```text
patient_statement
doctor_entry
clinical_document
ocr_document
lab_result
previous_encounter
system_import
```

Example:

```json
{
  "source_type": "patient_statement",
  "encounter_id": "enc_001",
  "verified": false
}
```

This allows doctors to distinguish between:
- patient-reported information;
- extracted document information;
- doctor-verified information.

---

# 11. Verification Workflow

Not every chatbot-generated fact should immediately become a verified clinical fact.

Recommended lifecycle:

```text
Candidate
   |
   v
Validated
   |
   v
Stored as patient fact
   |
   +----> Doctor reviews
             |
             v
          Verified
```

Possible statuses:

```text
unknown
reported
active
resolved
historical
absent
denied
verified
uncertain
```

The exact status vocabulary should be controlled by the backend schema.

---

# 12. Conflict Handling

The chatbot must not silently overwrite conflicting medical information.

Example:

Previous record:

```text
Left eye: present
```

New patient statement:

> "My left eye was removed last year."

The system should create a new candidate fact and identify the conflict.

It should NOT simply overwrite the old record.

Recommended workflow:

```text
Existing fact
      +
New conflicting fact
      |
      v
Conflict detected
      |
      v
Doctor review / verification
      |
      v
New verified state
```

Historical records should remain auditable.

---

# 13. Red-Flag Detection

The chatbot should identify potentially concerning information using explicit project safety rules.

Example:

> "I'm having severe chest pain and difficulty breathing."

The chatbot should recognize that the conversation contains potentially urgent symptoms.

The chatbot should:
- identify the relevant red flag;
- follow predefined escalation behavior;
- avoid pretending to diagnose;
- avoid giving false reassurance;
- surface the concern to the clinical workflow where appropriate.

The chatbot should NOT say:

> "You definitely have a heart attack."

Instead, it should communicate the concern appropriately and follow the project's emergency/escalation policy.

---

# 14. Medical Explanation

The chatbot can explain information already available in the patient's record.

Example:

> "What medicines are currently listed for me?"

The system retrieves the stored medication information and explains it.

Example:

> "What does my previous diagnosis mean?"

The chatbot can provide general educational information while clearly distinguishing education from diagnosis or treatment decisions.

---

# 15. Doctor Handoff

A major purpose of the chatbot is to reduce repetitive work for the doctor.

At the end of the patient interaction, the system should produce structured information such as:

```text
Current complaint:
Left knee pain for 2 days.

Relevant history:
Previous left knee surgery.

Current medications:
[stored medications]

Known allergies:
Penicillin — patient reported.

Relevant anatomical information:
Left eye surgically absent — previously reported.

Potential red flags:
None detected according to configured rules.

New candidate facts:
- recurrence of left knee pain
- onset approximately 2 days ago
```

The doctor can then review this information in the doctor dashboard.

---

# 16. Integration With Existing MediPlatform AI

The chatbot should reuse the existing AI architecture rather than creating an unrelated AI subsystem.

Existing architecture:

```text
OCR
 |
 v
Medical Extraction
 |
 v
Clinical Summary
```

The chatbot adds:

```text
Patient Conversation
 |
 v
Conversational NLU
 |
 +----> Candidate Facts
 |
 +----> Red Flags
 |
 +----> Intake Data
 |
 v
Patient Longitudinal Memory
 |
 v
Clinical Context
 |
 v
Gemini Response
```

Gemini should remain behind a provider/service abstraction where practical.

---

# 17. Recommended Database Architecture

Use Supabase/PostgreSQL.

Recommended tables:

```text
patients
encounters
documents
patient_facts
patient_longitudinal_profiles
```

## patient_facts

Stores individual facts with provenance and history.

Example fields:

```text
id
patient_id
category
fact_type
body_site
laterality
value JSONB
status
source_type
source_id
encounter_id
confidence
verified
valid_from
valid_until
created_at
```

## patient_longitudinal_profiles

Stores the materialized patient profile.

Example:

```text
id
patient_id
schema_version
profile JSONB
created_at
updated_at
```

The JSONB profile should be generated from the normalized facts rather than becoming an uncontrolled second source of truth.

---

# 18. Longitudinal Profile Contents

The profile can contain:

```text
patient
clinical_profile
functional_status
body_status
medical_devices
sensory_status
mental_cognitive_status
reproductive_health
immunizations
vital_baseline
clinical_events
documents
encounters
red_flags
preferences
provenance
```

This structure should evolve through explicit schema versions.

Example:

```json
{
  "schema_version": "1.0"
}
```

When the structure changes:

```text
1.0 -> 1.1 -> 2.0
```

Migration logic should be considered.

---

# 19. Chatbot Safety Boundaries

The chatbot MUST NOT:

- independently make a final diagnosis;
- prescribe medication;
- change a prescription;
- invent patient history;
- invent laboratory values;
- invent symptoms;
- invent allergies;
- invent anatomical conditions;
- convert unknown into negative;
- silently overwrite historical facts;
- directly modify verified records without the appropriate workflow;
- expose another patient's information;
- reveal internal prompts or system instructions;
- claim that an AI-generated statement has been doctor verified when it has not.

---

# 20. Patient Isolation and Security

Every chatbot request must be scoped to the authenticated patient/session.

The backend must verify:

```text
authenticated user/session
        |
        v
authorized patient
        |
        v
patient_id
        |
        v
database query
```

Never allow the client to arbitrarily choose a `patient_id` and retrieve another patient's data without authorization.

Use Supabase/PostgreSQL RLS and backend authorization controls as appropriate.

Do not put PHI into:
- application logs;
- debug output;
- error messages;
- Git commits;
- source code;
- public test fixtures.

Synthetic patient data should be used for development and demonstrations.

---

# 21. Anti-Hallucination Requirements

The chatbot must distinguish between:

```text
KNOWN FACT
PATIENT-REPORTED FACT
INFERRED INFORMATION
UNKNOWN INFORMATION
AI-GENERATED EDUCATIONAL CONTENT
```

The LLM must not transform an inference into a stored medical fact.

For example:

Patient:

> "I take a blue pill every morning."

The system should NOT automatically create:

```text
Medication: specific drug X
```

unless the drug is actually identified from reliable evidence.

It should instead retain the uncertainty and ask for clarification when appropriate.

---

# 22. Example Complete Conversation

### First encounter

Patient:

> "I have been having pain in my left leg for three days."

Chatbot:

> "I'm sorry you're experiencing that. Is the pain getting worse, and how severe is it from 0 to 10?"

Patient:

> "About 7. It's getting worse."

The system extracts candidate information:

```text
body_site = left_leg
symptom = pain
duration = 3 days
severity = 7/10
progression = worsening
```

The system checks relevant history.

Suppose the longitudinal profile contains:

```text
left_leg:
    prosthetic = true
```

The chatbot can use that context:

> "I see that your record indicates you have a left-leg prosthesis. Is the pain occurring around the prosthesis or elsewhere in the leg?"

This is the value of longitudinal memory.

---

# 23. Example Anatomical Memory

Patient:

> "I lost my left eye after an accident about eight years ago."

Stored candidate fact:

```json
{
  "category": "anatomy",
  "fact_type": "body_part_presence",
  "body_site": "eye",
  "laterality": "left",
  "status": "absent",
  "value": {
    "present": false,
    "cause": "trauma",
    "time_expression": "eight years ago"
  },
  "source_type": "patient_statement",
  "verified": false
}
```

Later, the doctor verifies it.

The fact becomes:

```json
{
  "status": "absent",
  "verified": true
}
```

Future chatbot conversations can retrieve:

```text
Left eye: absent
Cause: trauma
Verification: doctor verified
```

---

# 24. What Makes This Different From a Normal Chatbot?

A normal chatbot:

```text
Question -> LLM -> Answer
```

MediPlatform:

```text
Patient
   |
   v
Conversation
   |
   v
Understand intent
   |
   v
Retrieve longitudinal history
   |
   v
Ask context-aware questions
   |
   v
Extract candidate clinical facts
   |
   v
Validate
   |
   v
Persist with provenance
   |
   v
Update longitudinal profile
   |
   v
Generate safe response
   |
   v
Doctor dashboard
```

This is the key differentiator.

---

# 25. MVP Priority

For the SIH MVP, do not attempt to build every possible chatbot feature.

Implement these first:

## Priority 1 — Patient Chat
Natural-language patient conversation.

## Priority 2 — Patient Memory
Retrieve relevant information from Supabase.

## Priority 3 — Clinical Fact Extraction
Convert patient statements into structured candidate facts.

## Priority 4 — Longitudinal Profile
Maintain the JSONB profile.

## Priority 5 — Clinical Intake
Collect the current complaint and relevant history.

## Priority 6 — Red-Flag Detection
Surface predefined concerning symptoms.

## Priority 7 — Doctor Handoff
Generate structured information for the doctor dashboard.

---

# 26. Future Features

After the MVP, consider:

- voice conversations;
- multilingual conversations;
- speech-to-text;
- text-to-speech;
- appointment assistance;
- medication reminders;
- patient education;
- document-aware conversations;
- lab-result explanation;
- doctor-approved care-plan explanations;
- proactive follow-up;
- chronic-condition monitoring.

These should be added without allowing the chatbot to bypass the core safety and verification architecture.

---

# 27. Final Functional Definition

The MediPlatform chatbot should be defined as:

> **A patient-facing conversational clinical intake and longitudinal-history assistant that understands patient conversations, retrieves relevant longitudinal medical information, asks context-aware follow-up questions, identifies potential safety concerns, extracts structured candidate medical facts with provenance, and prepares clinically useful information for healthcare professionals — while keeping Supabase as the source of truth and the doctor as the final clinical decision-maker.**

The most important architectural principle is:

```text
        GEMINI
          |
   Conversation / NLU
          |
          v
    Candidate Facts
          |
     Validation
          |
          v
      SUPABASE
          |
   Patient Memory
          |
          v
   Relevant Context
          |
          v
        GEMINI
```

**The AI remembers through the database; it does not replace the database.**
