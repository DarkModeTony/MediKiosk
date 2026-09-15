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

## 5. Repository Structure

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

## 6. Database Schema

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

## 7. Full API Reference

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

## 8. Local Development Setup

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

## 9. Testing & Validation

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

## 10. Security & Hospital Isolation

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

## 11. Implementation Status

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

## 12. Safety, Governance & Ethics

1. **Human-in-the-Loop**: All AI outputs require explicit physician review and verification before entering the legal record.
2. **Server-Authoritative Safety**: Red flags are always computed by deterministic server-side rules. AI never generates or modifies triage severity.
3. **Unknown != Negative**: Denying a fact with unknown status always triggers a HIGH conflict flag for doctor review.
4. **Evidence Provenance**: Every extracted clinical entity includes `source_text` and `confidence_score`. Hallucinated claims are stripped by the validator before the doctor sees them.
5. **Data Privacy**: This repository uses de-identified synthetic test fixtures. Production deployments must comply with applicable regulations (India ABDM/DISHA, HIPAA, etc.).
6. **Medicine Authority**: The 253k Indian medicines dataset is the sole authoritative source. Safety checks are deterministic - no AI involvement.

---

## 13. Authors & License

Maintained by the **MediPlatform Engineering Team**.  
Licensed under the [MIT License](LICENSE).
