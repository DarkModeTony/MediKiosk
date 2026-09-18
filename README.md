# MediPlatform (MediKiosk)

> **AI-Assisted Clinical Intake & Medical Record Preparation for High-Volume Indian Hospitals**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 14+](https://img.shields.io/badge/Next.js-14%2B-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC.svg)](https://tailwindcss.com/)
[![shadcn/ui](https://img.shields.io/badge/shadcn%2Fui-base--nova-000000.svg)](https://ui.shadcn.com/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E.svg)](https://supabase.com)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4.svg)](https://ai.google.dev/)
[![Sarvam AI](https://img.shields.io/badge/Voice-Sarvam%20ASR-FF6F00.svg)](https://www.sarvam.ai/)
[![Tests](https://img.shields.io/badge/tests-151%20passing-brightgreen.svg)](#9-testing--validation)

---

## 1. Problem & Solution

High-volume OPDs across India see **80-120+ patients per shift**, leaving doctors as little as **2-3 minutes per consultation**. The core problems:

- **Documentation overload**: >50% of consultation time is spent on transcription instead of diagnosis.
- **Paper fragmentation**: Crumpled prescriptions, unsorted lab slips, illegible handwriting.
- **Language barriers**: Patients struggle to communicate history, especially in regional languages.
- **No digital triage**: Critical patients queue alongside minor ailments.
- **Fragmented clinical intelligence:** Doctors lack a unified view that connects patient history, symptoms, reports, and prescriptions into actionable clinical context.

**MediPlatform** turns the waiting room into a clinical preparation engine:

1. **Smartphone-less Kiosk** - touch-first UI for patients in the waiting area.
2. **Indic Voice Input** - Sarvam AI (saaras:v3) transcribes patient speech in 22 Indian languages.
3. **Document Digitization** - Gemini Vision OCR extracts medications, dosages, and diagnoses from uploaded prescriptions and lab reports.
4. **Deterministic Safety Tripwires** - Server-side rules fire red flags (e.g., chest pain + diaphoresis) and elevate queue priority instantly.
5. **Doctor-in-the-Loop Dashboard** - The doctor reviews a pre-assembled, evidence-backed clinical summary and verifies with a single click.

> **Clinical Safety Principle**: The doctor is always the final clinical decision-maker. No AI output enters the legal medical record without explicit physician verification.

---

## 2. System Architecture

```mermaid
flowchart TD
    subgraph PatientExperience["Patient Experience (Waiting Room)"]
        PK["Patient Kiosk (Next.js 14)<br/>Touch-first UI + Voice + Document Upload"]
    end

    subgraph ExternalAI["Multimodal AI Services"]
        SARVAM["Sarvam AI saaras:v3<br/>Indic Speech-to-Text (22 Languages)"]
        GEMINI_OCR["Gemini Vision OCR<br/>Prescription + Lab Report Digitization"]
        GEMINI_EXT["Gemini Medical Extraction<br/>Entities + Confidence + Provenance"]
        GEMINI_NLU["Gemini Clinical NLU<br/>Allergy / Condition / Medication Facts"]
        GEMINI_SUM["Gemini Summarizer<br/>Draft + Anti-Hallucination Validator"]
    end

    subgraph BackendCore["FastAPI Backend"]
        AUTH["JWT Auth + Hospital Isolation"]
        PIPELINE["Conversation-Facts Pipeline<br/>NLU -> Validate -> Reconcile -> patient_facts"]
        RED_FLAG["Deterministic Red-Flag Engine<br/>Server-Authoritative, Never AI"]
        LONGITUDINAL["Longitudinal Profile (21 Domains)<br/>patient_facts + JSONB snapshot"]
    end

    subgraph DatabaseLayer["Persistence"]
        POSTGRES[("Supabase PostgreSQL")]
        SQLITE[("SQLite medicines.db<br/>253k Indian Medicines FTS5")]
    end

    subgraph DoctorExperience["Doctor Consultation Room"]
        DD["Doctor Dashboard (Next.js 14)<br/>Queue / Assessment / Investigations / Prescriptions"]
    end

    PK --> API["FastAPI REST"]
    API --> SARVAM --> PIPELINE --> GEMINI_NLU
    PIPELINE --> LONGITUDINAL
    API --> GEMINI_OCR --> GEMINI_EXT
    API --> AUTH --> RED_FLAG
    API --> GEMINI_SUM
    API <--> POSTGRES
    API --> SQLITE
    POSTGRES --> DD
    DD --> API
```

---

## 3. AI Subsystem Architecture

Every AI subsystem uses a **factory pattern** with real and mock providers. Set modes via environment variables — all mock for offline dev, all real for production.

| Subsystem | Real Provider | Mock | Env Var |
|---|---|---|---|
| ASR (Voice) | `SarvamASRProvider` (saaras:v3) | `MockASRProvider` | `ASR_MODE=sarvam` |
| OCR | `GeminiOCRProvider` / `PaddleOCRProvider` | `MockOCRProvider` | `OCR_MODE=gemini\|paddle` |
| Medical Extraction | `GeminiExtractionProvider` | `MockExtractionProvider` | `EXTRACTION_MODE=gemini` |
| Clinical NLU | `GeminiNLUProvider` | `MockNLUProvider` | `NLU_MODE=gemini` |
| Summarization | `GeminiSummaryProvider` / `OpenAISummaryProvider` | `MockSummaryProvider` | `AI_MODE=real` + `LLM_PROVIDER=gemini` |
| Red-Flag Detection | Deterministic rules only | N/A | Always deterministic |
| Fact Reconciliation | Deterministic engine only | N/A | Always deterministic |

### Non-Negotiable Safety Rules

- **Red flags are always deterministic** - never AI-generated, never suppressed.
- **NLU never diagnoses** - extracts only factual entities stated by the patient.
- **Unknown != Negative** - denying an unknown allergy/condition triggers HIGH conflict for doctor review.
- **Anti-hallucination validator** - strips any clinical entity from AI summaries that cannot be traced to source data.
- **Doctor verification mandatory** - AI drafts never auto-enter the legal medical record.

---

## 4. Clinical Workflows

### 4.1 Patient Intake (Kiosk -> Backend)

```
Patient walks up to kiosk
  -> Consent
  -> Registration (new UHID / returning patient lookup)
  -> Clinical conversation (voice + touch)
       Each answer: POST /api/v1/clinical/answer
         -> Sarvam ASR transcription (if voice input)
         -> Gemini NLU: ExtractedFacts (category, fact_type, value, confidence)
         -> Fact reconciliation: conflict detection + Unknown != Negative guard
         -> Insert to patient_facts (immutable, append-only, provenance-tracked)
         -> Sync to patient_longitudinal_profiles (21-domain JSONB snapshot)
         -> Deterministic red-flag evaluation (boost queue priority if triggered)
         -> Returns next adaptive question
  -> Document upload (prescriptions, lab reports, discharge summaries)
       -> Gemini Vision OCR -> raw text
       -> Gemini Extraction -> document_entities (confidence_score + source_text)
  -> Summary preview
  -> Encounter status -> WAITING_FOR_DOCTOR
```

### 4.2 Doctor Encounter Workspace

```
Doctor logs in -> JWT token issued
Queue page: encounters sorted by red flag severity
Open encounter:
  Tab 1 - Summary: AI-generated draft (editable) + verify button
  Tab 2 - History:  Q&A transcript + red flags
  Tab 3 - Documents: OCR results + entity evidence
  Tab 4 - Timeline: Registration, uploads, red flags, milestones
  Tab 5 - Prescription:
    -> Medicine autocomplete (253k medicines, sub-ms SQLite FTS5)
    -> POST /api/v1/prescriptions/{id}/safety-check
         -> Allergy cross-check (incl. cross-reactions, e.g. penicillin->amoxicillin)
         -> Duplicate medication detection
         -> Unknown allergy status warning
    -> POST /api/v1/prescriptions/{id}/finalize
         -> Medications sync to patient_facts + longitudinal_profile

Clinical Assessment (Tab or modal):
  -> HPI, vitals, physical exam findings
  -> Confirmed allergies + confirmed medications
  -> Provisional / confirmed diagnoses + clinical plan
  -> POST /api/v1/encounters/{id}/assessment/verify
       -> Diagnoses + allergies auto-sync to patient_facts (immutable audit)

Investigation Orders:
  -> Place order (lab, imaging, ECG, other)
  -> POST /api/v1/investigations/{id}/results  (record findings + abnormal flags)
  -> POST /api/v1/investigations/{id}/review   (physician acknowledgement)
```

### 4.3 Authentication & Hospital Isolation

```
POST /api/v1/auth/login  -> JWT (24h expiry)
All protected routes:
  Authorization: Bearer <token>
  -> get_current_user() validates JWT, loads doctor + hospital_id
  -> verify_encounter_access() checks hospital scope
  -> Cross-hospital access -> safe HTTP 404 (no information leakage)
```

---

## 5. Patient ↔ Doctor: Complete Data Flow

This section traces exactly how a single patient visit flows from the waiting-room kiosk to the doctor's screen, and how every clinical action feeds back into the patient's permanent longitudinal record.

---

### 5.1 End-to-End Journey (Narrative)

#### Phase 1 — Patient Arrives at Kiosk (Waiting Room)

```
Patient sits at touch screen kiosk (no smartphone needed)
  │
  ├─ [Step 1] Consent
  │     POST /api/v1/kiosk/session  →  session_token (UUID, 60 min TTL)
  │     KioskSession row created in PostgreSQL
  │
  ├─ [Step 2] Registration
  │     New patient  →  POST /api/v1/patients/register
  │                        → Patient row (UUID patient_id, demographic_data JSONB)
  │                        → Encounter row created (status: IN_PROGRESS)
  │     Returning    →  Phone/UHID lookup → existing patient_id resolved
  │
  ├─ [Step 3] Clinical Intake Conversation
  │     Adaptive Q&A engine generates next question based on pathway + answers so far
  │     For each patient answer:
  │       POST /api/v1/clinical/answer  { session_token, answer_text, is_voice }
  │         │
  │         ├─ [Voice] → POST /api/v1/voice/transcribe
  │         │              Multipart audio → Sarvam AI saaras:v3
  │         │              Returns: { transcript, detected_language }
  │         │
  │         ├─ [NLU]  → GeminiNLUProvider (or MockNLUProvider)
  │         │              Input: answer text
  │         │              Output: ExtractedFacts[]
  │         │                { category, fact_type, value, confidence, source_text }
  │         │
  │         ├─ [Validate] → confidence threshold check + category filtering
  │         │
  │         ├─ [Reconcile] → ReconciliationEngine (deterministic)
  │         │                  Detects contradictions (e.g. "no allergies" then "penicillin rash")
  │         │                  Unknown ≠ Negative: if status=unknown, flags HIGH conflict
  │         │
  │         ├─ [Persist] → patient_facts row (immutable, append-only)
  │         │                { patient_id, category, fact_type, value,
  │         │                  source_type=CONVERSATION, confidence,
  │         │                  valid_from, source_text, verified=false }
  │         │
  │         ├─ [Sync]    → patient_longitudinal_profiles JSONB updated
  │         │                (e.g. allergies[], chronic_conditions[], medications[])
  │         │
  │         ├─ [Red Flag] → RedFlagEngine (deterministic, never AI)
  │         │                 Evaluates patient_facts against rule set
  │         │                 e.g. CARDIAC_EMERGENCY_SUSPECTED, HIGH_GRADE_FEVER
  │         │                 If triggered: red_flags row inserted (severity HIGH/MEDIUM)
  │         │                              Encounter.priority elevated in queue
  │         │
  │         └─ Returns: next adaptive question (or COMPLETE)
  │
  ├─ [Step 4] Document Upload (optional)
  │     POST /api/v1/documents/upload  (multipart: file + encounter_id)
  │       → Document row + file stored in backend/uploads/
  │       → OCR pipeline:
  │           GeminiOCRProvider → raw text extraction per page
  │           document_ocr row  { raw_text, engine_used, confidence }
  │       → Extraction pipeline:
  │           GeminiExtractionProvider → structured entities
  │           document_entities rows  { entity_type, value, confidence_score, source_text }
  │           (medications, diagnoses, vitals extracted with provenance)
  │
  ├─ [Step 5] Summary Generation
  │     POST /api/v1/summaries/generate  { encounter_id }
  │       → Aggregator collects: patient_facts + document_entities + red_flags
  │       → GeminiSummaryProvider generates 10-section draft
  │       → AntiHallucinationValidator strips any entity not traceable to source data
  │       → clinical_summaries row created  { draft_content JSONB, status: AI_DRAFT }
  │
  └─ [Step 6] Encounter Status → WAITING_FOR_DOCTOR
        Encounter.status updated → patient appears in doctor queue sorted by severity
```

---

#### Phase 2 — Doctor Opens Encounter (Consultation Room)

```
Doctor logs in
  POST /api/v1/auth/login  →  JWT (24h)
  All subsequent requests: Authorization: Bearer <token>

Queue Page  GET /api/v1/encounters/active
  → Hospital-scoped query (hospital_id from JWT)
  → Encounters sorted: HIGH red flags → MEDIUM → NORMAL → WAITING time
  → Each queue card shows: patient name, chief complaint, wait time, red flag badge

Doctor clicks patient → Encounter Workspace
  GET /api/v1/encounters/{encounter_id}
  GET /api/v1/summaries/encounters/{encounter_id}/summary
  GET /api/v1/clinical/state?encounter_id=...
  (all validated via verify_encounter_access → hospital scope check)

  ┌── Tab 1: AI Summary ──────────────────────────────────────────────────────┐
  │  Displays: structured_sections (COMPLAINT, HPI, HISTORY, ALLERGIES,       │
  │            MEDICATIONS, VITALS, RED FLAGS, SUGGESTED WORKUP)               │
  │  Doctor can: Edit sections inline → POST /api/v1/summaries/{id}/edit      │
  │              Verify → POST /api/v1/summaries/{id}/verify                  │
  │                → summary_verifications row created (final_content, doc_id) │
  │                → Encounter.status → COMPLETED                              │
  └───────────────────────────────────────────────────────────────────────────┘

  ┌── Tab 2: Clinical History ─────────────────────────────────────────────────┐
  │  Displays: all patient_facts for this encounter                             │
  │            full Q&A transcript from clinical_histories                      │
  │            red_flags panel (rule_name, evidence, severity)                  │
  └────────────────────────────────────────────────────────────────────────────┘

  ┌── Tab 3: Prescription (Rx) ────────────────────────────────────────────────┐
  │  Medicine search (live as-you-type):                                        │
  │    GET /api/v1/medicines/search?q=amox&limit=20                             │
  │    → SQLite FTS5 query across 253k Indian medicines (<1ms)                  │
  │                                                                             │
  │  Add item → configure dose / frequency / duration / route / timing         │
  │  Save draft:  POST /api/v1/encounters/{id}/prescriptions                   │
  │    → prescriptions row (status: DRAFT) + prescription_items rows           │
  │                                                                             │
  │  Safety Check: POST /api/v1/prescriptions/{id}/safety-check                │
  │    → Allergy cross-check vs patient_longitudinal_profiles.allergies[]      │
  │        Includes cross-reaction logic (penicillin → amoxicillin flagged)    │
  │    → Duplicate check vs current_medications[]                               │
  │    → Unknown allergy status warning                                         │
  │    → Returns: SafetyAlert[] with severity INFO / CAUTION / HIGH            │
  │                                                                             │
  │  Finalize: POST /api/v1/prescriptions/{id}/finalize                        │
  │    → prescription.status → FINALIZED                                        │
  │    → Each medication written to patient_facts                               │
  │        { source_type: PRESCRIPTION, confidence: 1.0, verified: true }      │
  │    → patient_longitudinal_profiles.current_medications[] updated            │
  └────────────────────────────────────────────────────────────────────────────┘

  ┌── Tab 4: Documents ────────────────────────────────────────────────────────┐
  │  Lists all uploaded documents for encounter                                 │
  │  Shows OCR text + extracted entities per document with confidence badge     │
  └────────────────────────────────────────────────────────────────────────────┘

  ┌── Tab 5: Timeline ─────────────────────────────────────────────────────────┐
  │  Chronological events: diagnoses, prescriptions, labs, surgeries,           │
  │                        current encounter, uploaded documents                 │
  │  Each event: date, type, entities, AI_EXTRACTED / DOCTOR_VERIFIED badge     │
  └────────────────────────────────────────────────────────────────────────────┘

  ┌── Clinical Assessment ─────────────────────────────────────────────────────┐
  │  POST /api/v1/encounters/{id}/assessment                                    │
  │    → Records: HPI, vitals, physical exam, confirmed allergies,              │
  │               confirmed medications, provisional/confirmed diagnoses, plan  │
  │  POST /api/v1/encounters/{id}/assessment/verify  (sign-off)                 │
  │    → Confirmed diagnoses → patient_facts (verified=true, source: ASSESSMENT)│
  │    → Confirmed allergies → patient_facts + longitudinal_profile.allergies[] │
  │    → audit_logs row created                                                  │
  └────────────────────────────────────────────────────────────────────────────┘

  ┌── Investigation Orders ─────────────────────────────────────────────────────┐
  │  POST /api/v1/encounters/{id}/investigations                                │
  │    → investigation_orders row (status: ORDERED)                             │
  │  POST /api/v1/investigations/{id}/results                                   │
  │    → Results recorded, abnormal_flags set (status: COMPLETED)               │
  │  POST /api/v1/investigations/{id}/review                                    │
  │    → Physician acknowledgement (status: REVIEWED)                           │
  └────────────────────────────────────────────────────────────────────────────┘
```

---

### 5.2 Sequence Diagram

```mermaid
sequenceDiagram
    actor Patient
    participant Kiosk as Patient Kiosk<br/>(Next.js :3000)
    participant API as FastAPI Backend<br/>(:8000)
    participant Sarvam as Sarvam AI<br/>(ASR)
    participant Gemini as Gemini AI<br/>(NLU / OCR / Summary)
    participant DB as PostgreSQL<br/>(Supabase)
    actor Doctor
    participant Dashboard as Doctor Dashboard<br/>(Next.js :3001)

    Note over Patient,DB: ── PHASE 1: Patient Intake ──

    Patient->>Kiosk: Tap "Begin"
    Kiosk->>API: POST /kiosk/session
    API->>DB: INSERT kiosk_sessions
    API-->>Kiosk: { session_token, encounter_id }

    Patient->>Kiosk: Register (phone / UHID)
    Kiosk->>API: POST /patients/register
    API->>DB: INSERT patients + encounters
    API-->>Kiosk: { patient_id, encounter_id }

    loop For each clinical question
        Kiosk->>Patient: Display question
        Patient->>Kiosk: Answer (voice or touch)
        opt Voice input
            Kiosk->>API: POST /voice/transcribe (audio)
            API->>Sarvam: audio blob
            Sarvam-->>API: { transcript, language }
        end
        Kiosk->>API: POST /clinical/answer { answer_text }
        API->>Gemini: NLU extraction
        Gemini-->>API: ExtractedFacts[]
        API->>API: Reconciliation Engine (deterministic)
        API->>DB: INSERT patient_facts
        API->>DB: UPDATE patient_longitudinal_profiles
        API->>API: Red-Flag Engine (deterministic)
        opt Red flag triggered
            API->>DB: INSERT red_flags
            API->>DB: UPDATE encounters.priority
        end
        API-->>Kiosk: next question
    end

    opt Document upload
        Patient->>Kiosk: Upload prescription / lab report
        Kiosk->>API: POST /documents/upload
        API->>Gemini: OCR → raw text
        API->>Gemini: Extraction → entities
        API->>DB: INSERT document_ocr + document_entities
    end

    Kiosk->>API: POST /summaries/generate
    API->>Gemini: Generate draft summary
    API->>API: Anti-hallucination validator
    API->>DB: INSERT clinical_summaries (AI_DRAFT)
    API->>DB: UPDATE encounters.status = WAITING_FOR_DOCTOR
    Kiosk-->>Patient: Show summary preview

    Note over Doctor,DB: ── PHASE 2: Doctor Consultation ──

    Doctor->>Dashboard: Login
    Dashboard->>API: POST /auth/login
    API-->>Dashboard: JWT token

    Doctor->>Dashboard: View Queue
    Dashboard->>API: GET /encounters/active
    API->>DB: Query encounters (hospital-scoped, sorted by red flag severity)
    API-->>Dashboard: QueueItem[] (Raj Kumar at top — MEDIUM flag)

    Doctor->>Dashboard: Open patient encounter
    Dashboard->>API: GET /encounters/{id} + /summary + /clinical/state
    API->>DB: Fetch encounter + summary + patient_facts
    API-->>Dashboard: Full encounter workspace data

    Doctor->>Dashboard: Review AI Summary → Verify
    Dashboard->>API: POST /summaries/{id}/verify
    API->>DB: INSERT summary_verifications (final_content, doctor_id, verified_at)

    Doctor->>Dashboard: Search medicine "Paracetamol"
    Dashboard->>API: GET /medicines/search?q=Paracetamol
    API->>API: SQLite FTS5 query (253k medicines, <1ms)
    API-->>Dashboard: MedicineSearchResult[]

    Doctor->>Dashboard: Add medicine → Save Draft
    Dashboard->>API: POST /encounters/{id}/prescriptions
    API->>DB: INSERT prescriptions + prescription_items

    Doctor->>Dashboard: Safety Check
    Dashboard->>API: POST /prescriptions/{id}/safety-check
    API->>DB: Read patient_longitudinal_profiles (allergies, current_meds)
    API->>API: Allergy cross-check + Duplicate detection (deterministic)
    API-->>Dashboard: SafetyAlert[] (e.g. ALLERGY: Penicillin → Amoxicillin)

    Doctor->>Dashboard: Finalize Prescription
    Dashboard->>API: POST /prescriptions/{id}/finalize
    API->>DB: UPDATE prescriptions.status = FINALIZED
    API->>DB: INSERT patient_facts (medication, source: PRESCRIPTION, verified: true)
    API->>DB: UPDATE patient_longitudinal_profiles.current_medications[]

    Doctor->>Dashboard: Sign off Assessment
    Dashboard->>API: POST /encounters/{id}/assessment/verify
    API->>DB: INSERT patient_facts (diagnoses + allergies, verified: true)
    API->>DB: INSERT audit_logs
```

---

### 5.3 Data Layer: What Lives Where

| Data | Table(s) | Written By | Read By |
|---|---|---|---|
| Patient identity | `patients` | Kiosk registration | Dashboard, Kiosk |
| Active encounter | `encounters` | Clinical start | Queue, all workspace tabs |
| Raw Q&A conversation | `clinical_histories` | `/clinical/answer` | History tab |
| Individual clinical facts | `patient_facts` | NLU pipeline, assessment verify, prescription finalize | History tab, safety check |
| 21-domain profile snapshot | `patient_longitudinal_profiles` | Same as above | Safety check, longitudinal profile page |
| Red flags | `red_flags` | Red-flag engine (deterministic) | Queue priority, Summary tab |
| Document files | `backend/uploads/` | `/documents/upload` | Documents tab |
| OCR raw text | `document_ocr` | Gemini / PaddleOCR | Documents tab |
| Extracted entities | `document_entities` | GeminiExtractionProvider | Timeline, Summary |
| AI summary draft | `clinical_summaries` | GeminiSummaryProvider | Summary tab |
| Doctor-verified summary | `summary_verifications` | `/summaries/{id}/verify` | Legal record |
| Prescription draft/final | `prescriptions` + `prescription_items` | `/encounters/{id}/prescriptions` | Prescription tab, patient history |
| Clinical assessment | `clinical_assessments` | `/encounters/{id}/assessment` | Assessment tab |
| Investigation orders | `investigation_orders` | `/encounters/{id}/investigations` | Investigations tab |
| Audit trail | `audit_logs` | Assessment verify, investigations | Compliance |

---

### 5.4 Real Example: Raj Kumar (Demo Patient)

Below is a concrete trace of every step for the built-in demo patient **Raj Kumar (42M, Delhi, T2DM + HTN)**:

| Step | Action | Data Written |
|---|---|---|
| Kiosk session | `POST /kiosk/session` | `kiosk_sessions` row, `encounter_id` returned |
| Registration | Phone `9000000001` looked up | Resolves to `patient_id = b54f64df-...` |
| Intake Q1 | Chief complaint: "Fever and weakness" | `patient_facts`: CHIEF_COMPLAINT = "Fever and general weakness" |
| Intake Q2 | PMH: "Diabetes 2020, Hypertension 2022" | `patient_facts`: 2× CHRONIC_CONDITION rows |
| Intake Q3 | Allergy: "Penicillin → skin rash" | `patient_facts`: ALLERGY row; `longitudinal_profile.allergies[]` updated |
| Intake Q4 | Meds: "Metformin 500mg BD, Amlodipine 5mg OD" | `patient_facts`: 2× MEDICATION rows |
| Intake Q5 | BP answer triggers rule | `red_flags`: ELEVATED_BP_KNOWN_HYPERTENSIVE, MEDIUM severity; queue priority raised |
| Summary | Gemini generates 10-section draft | `clinical_summaries` row; validator strips unconfirmed claims |
| **Doctor queue** | Dashboard shows Raj at top of queue | MEDIUM badge, "Fever and weakness for 3 days" |
| **Open encounter** | Doctor opens workspace | Loads summary, history, red flags, timeline — all from DB |
| **Prescribe** | Doctor searches "Azithromycin" | SQLite FTS5 returns 500mg tablet matches in <1ms |
| **Safety check** | Amoxicillin chosen instead | ALLERGY alert fires (penicillin cross-reaction) |
| **Finalize Rx** | Doctor signs off prescription | `prescription_items` written; `patient_facts` MEDICATION row added with `verified=true` |
| **Assessment** | Doctor confirms diagnoses | `clinical_assessments` + `patient_facts` DIAGNOSIS rows, `audit_logs` entry |

---

## 6. Repository Structure

```
MediKiosk/
|-- A_Z_medicines_dataset_of_India.csv       # 253k Indian medicines (SQLite-indexed at startup)
|-- AGENTS.md                                # Agent knowledge base and source of truth
|-- ai/
|   |-- asr/                                 # SarvamASRProvider + MockASRProvider
|   |-- clinical_nlu/                        # GeminiNLUProvider + MockNLUProvider + interface
|   |-- medical_extraction/                  # GeminiExtractionProvider + Mock + interface
|   |-- ocr/                                 # GeminiOCRProvider + PaddleOCRProvider + Mock
|   |-- question_engine/                     # Adaptive clinical Q&A pathway state machine
|   |-- reconciliation/                      # Deterministic fact conflict detection engine
|   |-- red_flags/                           # Deterministic emergency triage rules
|   `-- summarization/                       # Gemini/OpenAI/Mock + anti-hallucination validator
|-- backend/
|   |-- alembic/versions/                    # 4 migration files
|   |-- app/
|   |   |-- api/
|   |   |   |-- deps.py                      # get_current_user, verify_encounter_access
|   |   |   `-- endpoints/
|   |   |       |-- auth.py                  # JWT login + /me
|   |   |       |-- assessments.py           # Doctor clinical assessment + sign-off
|   |   |       |-- clinical.py              # Intake Q&A + NLU pipeline
|   |   |       |-- documents.py             # Upload + OCR + entity extraction
|   |   |       |-- encounters.py            # Queue + encounter management
|   |   |       |-- investigations.py        # Lab/imaging order lifecycle
|   |   |       |-- kiosk.py                 # Kiosk session tokens
|   |   |       |-- longitudinal.py          # 21-domain profile + patient_facts
|   |   |       |-- patients.py              # Registration + lookup
|   |   |       |-- prescriptions.py         # Prescription + safety checks
|   |   |       |-- summaries.py             # AI summary generation + verification
|   |   |       `-- voice.py                 # Sarvam ASR endpoint
|   |   |-- core/security.py                 # JWT encode/decode helpers
|   |   |-- models/models.py                 # All SQLAlchemy models (20+ tables)
|   |   |-- schemas/
|   |   |   |-- assessment.py
|   |   |   |-- investigation.py
|   |   |   |-- longitudinal_profile.py      # 21-domain JSONB schema
|   |   |   `-- prescription.py
|   |   `-- services/
|   |       |-- conversation_fact_pipeline.py # NLU -> validate -> reconcile -> patient_facts
|   |       |-- medicine_search.py            # SQLite FTS5 medicine search (sub-ms)
|   |       `-- storage.py
|   |-- tests/                               # 12 test files, 151 tests total
|   |-- requirements.txt
|   |-- conftest.py
|   `-- .env.example
`-- frontend/
    |-- patient-kiosk/                       # Port 3000, Next.js 14, TypeScript, Tailwind
    |   `-- src/app/
    |       |-- consent/
    |       |-- registration/
    |       |-- clinical/conversation/        # Voice + touch Q&A with live ASR transcript
    |       |-- documents/                    # Drag-and-drop upload
    |       `-- summary-preview/
    `-- doctor-dashboard/                    # Port 3001, Next.js 14, TypeScript, Tailwind, shadcn/ui
        `-- src/app/
            |-- login/
            |-- dashboard/
            |-- queue/
            |-- encounters/[encounterId]/    # 5-tab encounter workspace
            `-- patients/[patientId]/        # Longitudinal profile + prescription history
```

---

## 7. Database Schema

All models in `backend/app/models/models.py`. Managed via SQLAlchemy + Alembic on Supabase PostgreSQL.

| Table | Purpose |
|---|---|
| `hospitals` | Multi-tenant root entity |
| `users` | Doctors and staff, linked to a hospital |
| `patients` | Patient identity; `demographic_data` JSONB |
| `encounters` | One per visit; statuses: IN_PROGRESS, WAITING_FOR_DOCTOR, COMPLETED |
| `kiosk_sessions` | Ephemeral session tokens |
| `clinical_histories` | Raw Q&A conversation payload (JSONB) |
| `documents` | Uploaded files (stored in backend/uploads/) |
| `document_ocr` | Raw OCR text with engine_used and confidence |
| `document_entities` | Structured entities with confidence_score and source_text |
| `clinical_summaries` | AI draft summary (draft_content JSONB) |
| `summary_verifications` | Doctor-verified final record (final_content JSONB, verified_at) |
| `red_flags` | Deterministic safety events (rule_name, severity HIGH/MEDIUM) |
| `clinical_assessments` | Doctor formal assessment (HPI, vitals, diagnoses, plan) |
| `investigation_orders` | Lab/imaging orders (ORDERED -> COMPLETED -> REVIEWED) |
| `prescriptions` | Doctor prescriptions (DRAFT -> FINALIZED -> AMENDED -> CANCELLED) |
| `prescription_items` | Individual medication line items |
| `patient_longitudinal_profiles` | 21-domain JSONB snapshot, updated per encounter |
| `patient_facts` | Immutable append-only provenance store (source_type, confidence, valid_from) |
| `audit_logs` | Full action audit trail |
| `fhir_resources` | FHIR resource storage (table exists; serialization TBD) |

### Dual Longitudinal Store Architecture

| Store | Type | Purpose |
|---|---|---|
| `patient_facts` | Immutable, append-only | Audit-safe provenance; one row = one clinical fact |
| `patient_longitudinal_profiles` | Mutable JSONB snapshot | Fast read access across 21 clinical domains |

Both are updated atomically on every write (NLU extraction, prescription finalization, assessment sign-off).

---

## 8. Full API Reference

Base prefix: `/api/v1`. All protected routes require `Authorization: Bearer <token>`.

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | Doctor login; returns JWT |
| GET | `/api/v1/auth/me` | Current authenticated user |

### Patients & Longitudinal Profile
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/patients/register` | Register patient or resolve by UHID |
| GET | `/api/v1/patients/{id}` | Patient demographics |
| GET | `/api/v1/patients/{id}/longitudinal-profile` | 21-domain health profile |
| PUT | `/api/v1/patients/{id}/longitudinal-profile` | Full profile replace |
| PATCH | `/api/v1/patients/{id}/longitudinal-profile` | Partial profile update |
| POST | `/api/v1/patients/{id}/facts` | Append provenance-tracked fact |
| GET | `/api/v1/patients/{id}/facts` | List all facts with provenance |
| GET | `/api/v1/patients/{id}/prescriptions` | Full prescription history |
| GET | `/api/v1/patients/{id}/investigations` | Investigation history |

### Encounters
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/encounters/active` | Hospital-scoped triage-sorted queue |
| GET | `/api/v1/encounters/{id}` | Full encounter with summary, red flags, documents |

### Kiosk & Clinical Intake
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/kiosk/session` | Create kiosk session token |
| POST | `/api/v1/clinical/start` | Start intake session |
| GET | `/api/v1/clinical/state` | Current intake state |
| POST | `/api/v1/clinical/answer` | Submit answer -> NLU -> patient_facts -> next question |
| GET | `/api/v1/clinical/question/{pathway}/{id}` | Get specific question |

### Voice (ASR)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/voice/transcribe` | Multipart audio -> Sarvam AI -> transcript |

### Documents
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/documents/upload` | Upload -> OCR -> entity extraction |
| GET | `/api/v1/documents/{id}` | Document details + extracted entities |

### AI Summaries
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/summaries/generate` | Generate AI draft summary |
| GET | `/api/v1/summaries/encounters/{id}/summary` | Get encounter summary |
| POST | `/api/v1/summaries/{id}/edit` | Doctor edits draft |
| POST | `/api/v1/summaries/{id}/verify` | Doctor verification sign-off |
| POST | `/api/v1/summaries/{id}/reject` | Reject and regenerate |

### Clinical Assessment
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/encounters/{id}/assessment` | Create or update assessment |
| GET | `/api/v1/encounters/{id}/assessment` | Retrieve assessment |
| POST | `/api/v1/encounters/{id}/assessment/verify` | Sign-off; syncs diagnoses/allergies to patient_facts |

### Investigations
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/encounters/{id}/investigations` | Place investigation order |
| GET | `/api/v1/encounters/{id}/investigations` | List all orders for encounter |
| POST | `/api/v1/investigations/{id}/results` | Record diagnostic results + abnormal flags |
| POST | `/api/v1/investigations/{id}/review` | Physician review + acknowledgement |
| POST | `/api/v1/investigations/{id}/cancel` | Cancel order |

### Prescriptions
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/medicines/search?q=...` | Autocomplete across 253k medicines |
| GET | `/api/v1/medicines/{id}` | Single medicine details |
| GET | `/api/v1/encounters/{id}/prescriptions` | List encounter prescriptions |
| POST | `/api/v1/encounters/{id}/prescriptions` | Create or update draft |
| POST | `/api/v1/prescriptions/{id}/safety-check` | Allergy + duplicate deterministic check |
| POST | `/api/v1/prescriptions/{id}/finalize` | Sign-off; syncs medications to patient_facts |
| POST | `/api/v1/prescriptions/{id}/amend` | Amend finalized prescription |

---

## 9. Local Development Setup

### Prerequisites
- Python 3.10+ (developed on 3.14.7)
- Node.js 18+ (LTS)
- PostgreSQL via Supabase or local instance
- API Keys: [Google Gemini](https://aistudio.google.com/) and [Sarvam AI](https://www.sarvam.ai/)

### Step 1: Clone
```bash
git clone https://github.com/DarkModeTony/MediKiosk.git
cd MediKiosk
```

### Step 2: Backend
```bash
cd backend
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

#### Configure `backend/.env`:
```env
# Database
DATABASE_URL=postgresql://postgres.your-ref:your-password@aws-0-region.pooler.supabase.com:5432/postgres

# AI Keys
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash
SARVAM_API_KEY=your_sarvam_api_key

# Provider Modes ('real' or 'mock' - use mock for offline development, no quota needed)
AI_MODE=real
OCR_MODE=gemini
EXTRACTION_MODE=gemini
NLU_MODE=gemini
LLM_PROVIDER=gemini
ASR_MODE=sarvam

# Auth
SECRET_KEY=your-random-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

> **Tip**: Set all `*_MODE` vars to `mock` for fully offline local development - no API keys required.

#### Run Migrations:
```bash
alembic upgrade head
```

#### Start Backend:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

### Step 3: Patient Kiosk (Port 3000)
```bash
cd frontend/patient-kiosk
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```
Access: http://localhost:3000

### Step 4: Doctor Dashboard (Port 3001)
```bash
cd frontend/doctor-dashboard
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev -- -p 3001
```
Access: http://localhost:3001

---

## 10. Testing & Validation

151 tests covering auth isolation, NLU providers, conversation pipelines, prescriptions, assessments, and investigations.

```bash
cd backend
.venv\Scripts\Activate.ps1   # or source .venv/bin/activate

# Run all 151 tests
python -m pytest tests/ -v

# Targeted suites
python -m pytest tests/test_auth_isolation.py -v           # Hospital tenant isolation
python -m pytest tests/test_nlu_providers.py -v            # Gemini NLU + Mock NLU
python -m pytest tests/test_conversation_fact_pipeline.py -v  # NLU -> patient_facts
python -m pytest tests/test_prescriptions.py -v            # Prescription + safety checks
python -m pytest tests/test_clinical_assessment.py -v      # Assessment workflow
python -m pytest tests/test_investigations.py -v           # Investigation lifecycle
```

Expected: **151 passed**

---

## 11. Security & Hospital Isolation

Every API endpoint enforces hospital-level tenant isolation:

- `get_current_user()` - validates JWT, loads doctor + `hospital_id`.
- `verify_encounter_access()` - ensures the requested encounter belongs to the doctor's hospital; returns HTTP 404 (not 403) on cross-tenant access to prevent information leakage.
- All patient, document, longitudinal profile, prescription, assessment, and investigation queries are hospital-scoped.

```python
# All encounter endpoints use this pattern
@router.get("/{encounter_id}")
async def get_encounter(
    encounter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    encounter = verify_encounter_access(db, encounter_id, current_user.hospital_id)
    # ...
```

---

## 12. Implementation Status

### Fully Implemented
- FastAPI backend with CORS, routing, health endpoint
- JWT authentication + hospital-level tenant isolation across all APIs
- Patient registration and kiosk session management
- Clinical intake Q&A with adaptive question engine
- **Sarvam ASR** - `POST /api/v1/voice/transcribe`, saaras:v3
- **Gemini NLU** - structured clinical fact extraction with confidence + provenance
- **Conversation -> patient_facts pipeline** - NLU -> validate -> reconcile -> immutable facts
- **Fact Reconciliation Engine** - deterministic conflict detection, Unknown != Negative guard
- **Deterministic Red-Flag Engine** - CARDIAC_EMERGENCY, THUNDERCLAP_HEADACHE, HIGH_GRADE_FEVER
- **Gemini Vision OCR** + PaddleOCR + Mock fallback
- Medical entity extraction with confidence scores and source_text provenance
- **Anti-hallucination validator** - strips unsupported claims before doctor review
- Clinical summarization (Gemini + OpenAI + Mock)
- **Summary verification workflow** - doctor edit -> verify -> immutable SummaryVerification
- **21-domain Longitudinal Patient Profile** - JSONB snapshot + patient_facts store
- **Doctor Clinical Assessment** - HPI, vitals, physical exam, diagnoses; auto-syncs to patient_facts
- **Investigation Workflow** - ORDERED -> COMPLETED -> REVIEWED -> CANCELLED + abnormal flags
- **Prescription Workflow** - 253k Indian medicines (SQLite FTS5) + allergy/duplicate safety checks
- Doctor Dashboard - login, queue, 5-tab encounter workspace, prescriptions
- Patient Kiosk - consent, registration, voice Q&A, document upload, summary preview
- **151 automated tests** across all subsystems

### Partially Implemented
- FHIR resource table exists; serialization/ABDM integration not yet done
- Consent UI exists; API-layer enforcement pending
- Audit logging covers prescriptions/assessments/investigations; full read coverage pending

### Planned
- FHIR R4 bundle export for ABDM compliance
- TTS to read kiosk questions aloud
- Thermal printer prescription slip generation
- Production security hardening (KMS, WAF, per-hospital API key rotation)

---

## 13. Safety, Governance & Ethics

1. **Human-in-the-Loop**: All AI outputs require explicit physician review and verification before entering the legal record.
2. **Server-Authoritative Safety**: Red flags are always computed by deterministic server-side rules. AI never generates or modifies triage severity.
3. **Unknown != Negative**: Denying a fact with unknown status always triggers a HIGH conflict flag for doctor review.
4. **Evidence Provenance**: Every extracted clinical entity includes `source_text` and `confidence_score`. Hallucinated claims are stripped by the validator before the doctor sees them.
5. **Data Privacy**: This repository uses de-identified synthetic test fixtures. Production deployments must comply with applicable regulations (India ABDM/DISHA, HIPAA, etc.).
6. **Medicine Authority**: The 253k Indian medicines dataset is the sole authoritative source. Safety checks are deterministic - no AI involvement.

---

## 14. Authors & License

Maintained by the **MediPlatform Engineering Team**.  
Licensed under the [MIT License](LICENSE).
