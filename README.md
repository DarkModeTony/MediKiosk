# MediPlatform (MediKiosk)

> **Enterprise AI-Assisted Clinical Intake, Longitudinal Health Record & Specialist Consultation Platform for High-Volume Indian Hospitals**

[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 14+](https://img.shields.io/badge/Next.js-14%2B-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC.svg)](https://tailwindcss.com/)
[![shadcn/ui](https://img.shields.io/badge/shadcn%2Fui-base--nova-000000.svg)](https://ui.shadcn.com/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E.svg)](https://supabase.com)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4.svg)](https://ai.google.dev/)
[![Sarvam AI](https://img.shields.io/badge/Voice-Sarvam%20ASR-FF6F00.svg)](https://www.sarvam.ai/)
[![Tests](https://img.shields.io/badge/tests-295%20passing-brightgreen.svg)](#10-testing--validation)

---

## 1. Executive Summary & Clinical Vision

Government and high-volume private Outpatient Departments (OPDs) across India routinely manage **80 to 150+ patients per physician shift**, leaving doctors with as little as **2 to 3 minutes per consultation**. Over half of that brief encounter is spent transcribing handwritten paper records, eliciting fundamental symptom chronologies, and translating regional vernacular into medical English.

**MediPlatform** transforms the waiting room into an active, intelligent clinical intake and triage station:

1. **Smartphone-Less Patient Kiosk**: Touch-friendly, high-contrast UI tailored for non-tech-savvy patients.
2. **Indic Voice Recognition**: Powered by Sarvam AI (`saaras:v3`) supporting 22 Indian languages and conversational code-mixed Hinglish.
3. **Multi-Symptom Adaptive Intake Engine**: Dynamic dimension tracking (onset, character, severity, radiation, aggravating/relieving factors) with multi-symptom awareness.
4. **Document Digitization & Medical Extraction**: Gemini Vision OCR transforms physical paper slips and lab reports into structured clinical entities with provenance tracking.
5. **Strict Patient Data Isolation**: Zero-leakage session architecture protecting new patients from cross-contamination, adhering to *Unknown ≠ Negative*.
6. **21-Domain Longitudinal Health Profile**: Immutable audit store (`patient_facts`) paired with high-performance JSONB snapshots for instant historical review.
7. **Deterministic Safety Tripwires**: Server-authoritative Red-Flag Rules and Prescription Drug Safety Engines that execute without probabilistic AI hallucination risks.
8. **DocTalk Specialist Tele-Consultation Network**: Peer-to-peer real-time consultation network connecting general OPD doctors to hospital specialists with pre-acceptance privacy gating.
9. **Physician Verification Workspace**: 5-tab Doctor Dashboard where the doctor reviews, edits, and verifies AI-drafted summaries before sign-off.

> **Foundational Safety Law**: *The doctor is always the ultimate clinical decision-maker. No AI output or hallucinated claim ever enters the legal medical record without explicit physician review and verification.*

---

## 2. High-Level System Architecture

```mermaid
flowchart TB
    subgraph Kiosk["Patient Kiosk (Port 3000)"]
        UI["Touch UI & Mobile Keypad"]
        MIC["Audio Capture (MediaRecorder)"]
        DOCS["Camera / Slip Drag-and-Drop"]
        PORTAL["Patient Portal (/profile, /history)"]
    end

    subgraph AI_Layer["Multimodal AI Pipelines"]
        ASR["Sarvam AI (saaras:v3)<br/>22 Indian Languages + Hinglish"]
        OCR["Gemini Vision OCR<br/>Prescription / Lab Digitize"]
        NLU["Gemini Clinical NLU<br/>Structured Clinical Entities"]
        SUM["Gemini Clinical Summarizer<br/>10-Section Clinical Draft"]
        VAL["Anti-Hallucination Validator<br/>Provenance & Grounding Gate"]
    end

    subgraph Backend["FastAPI Backend Orchestrator (Port 8000)"]
        AUTH["JWT & Hospital Multi-Tenant Isolation"]
        ROUTER["Adaptive Symptom Pathway Router"]
        RED_FLAG["Deterministic Red-Flag Engine<br/>Server-Authoritative Rules"]
        RECON["Fact Reconciliation Engine<br/>Unknown != Negative Guard"]
        DOCTALK["DocTalk Consultation Engine<br/>Discovery, Pre-Acceptance Privacy, Notes"]
        RX_ENGINE["Prescription Safety Engine<br/>Allergy Cross-Reactivity & Duplicates"]
    end

    subgraph Storage["Data & Persistence Layer"]
        PG[("Supabase PostgreSQL<br/>Audit Logs, Encounters, Profiles, patient_facts")]
        SQLITE[("SQLite medicines.db<br/>253,000+ Indian Medicines FTS5")]
    end

    subgraph Dashboard["Doctor Dashboard (Port 3001)"]
        QUEUE["Priority Queue<br/>Red-Flag Sorted"]
        WORKSPACE["5-Tab Workspace<br/>Summary, History, Rx, Labs, Assessment"]
        TALK_UI["DocTalk Specialist Hub<br/>Live Consultation Room & Timeline"]
    end

    MIC -->|WebM Audio| ASR -->|Transcript| ROUTER
    UI -->|Responses| ROUTER --> NLU
    DOCS -->|Images/PDFs| OCR --> NLU
    NLU --> VAL --> RECON --> PG
    ROUTER --> RED_FLAG --> PG
    PG --> SUM --> VAL --> PG

    AUTH --> PG
    DOCTALK <--> PG
    RX_ENGINE <--> SQLITE
    RX_ENGINE <--> PG

    PG --> QUEUE
    PG --> WORKSPACE
    DOCTALK <--> TALK_UI
```

---

## 3. Core Feature Deep-Dives

### 3.1 DocTalk — Hospital Doctor-to-Specialist Live Consultation

DocTalk connects attending OPD physicians with on-call hospital specialists (Cardiologists, Neurologists, Nephrologists, Pulmonologists, etc.) across the hospital or health system.

#### Key Capabilities:
- **Real-Time Specialist Discovery**: Filters by specialty, hospital affiliation, and live availability (`AVAILABLE`, `IN_CONSULTATION`, `OFFLINE`).
- **Deterministic Auto-Match**: `find-any` fallback matches available, eligible specialists based on lowest active caseload.
- **Pre-Acceptance Privacy Guard**: Prior to a specialist accepting a request, patient PII (name, phone, address) is masked. The specialist only reviews clinical urgency, chief complaint, age/gender, and requesting physician notes.
- **Mutual Clinical Notes & Timeline**: Structured recommendations and mutual notes persist directly to the patient's encounter timeline and audit logs.

```mermaid
sequenceDiagram
    autonumber
    actor OPD as OPD Doctor
    participant Core as Backend DocTalk API
    participant DB as Supabase PostgreSQL
    actor Spec as On-Call Specialist

    OPD->>Core: POST /doctalk/requests (Encounter ID, Specialty, Urgency, Clinical Question)
    Core->>DB: Insert DocTalkConsultation (status: REQUESTED)
    Core->>Spec: Real-Time In-App Notification

    Note over Spec,Core: Pre-Acceptance Privacy Active: PII Masked
    Spec->>Core: GET /doctalk/requests/{id}/context
    Core-->>Spec: Anonymized Clinical Context (Age, Gender, Symptoms, Question)

    alt Specialist Accepts
        Spec->>Core: POST /doctalk/requests/{id}/accept
        Core->>DB: Update status -> ACCEPTED (Full Encounter Context Unlocked)
        Spec->>Core: POST /doctalk/requests/{id}/start -> status: IN_PROGRESS
        
        par Collaborative Consultation
            OPD->>Core: POST /doctalk/requests/{id}/notes (Requesting Query / Observation)
            Spec->>Core: POST /doctalk/requests/{id}/notes (Specialist Opinion / Recommendation)
        end

        Spec->>Core: POST /doctalk/requests/{id}/complete (Final Opinion)
        Core->>DB: Status -> COMPLETED, Write to Encounter Timeline & Audit Log
    else Specialist Declines
        Spec->>Core: POST /doctalk/requests/{id}/decline (Reason)
        Core->>DB: Status -> DECLINED, OPD Doctor Notified for Re-Routing
    else Expiry Timeout
        Core->>DB: Auto-Sweep Marks Request as EXPIRED if unanswered
    end
```

#### DocTalk State Machine:
```mermaid
stateDiagram-v2
    [*] --> REQUESTED: OPD Doctor initiates
    REQUESTED --> ACCEPTED: Specialist accepts
    REQUESTED --> DECLINED: Specialist declines
    REQUESTED --> EXPIRED: 15-min timeout
    REQUESTED --> CANCELLED: OPD Doctor withdraws

    ACCEPTED --> IN_PROGRESS: Consultation begins
    IN_PROGRESS --> COMPLETED: Specialist submits opinion
    IN_PROGRESS --> CANCELLED: Terminated early

    COMPLETED --> [*]
    DECLINED --> [*]
    EXPIRED --> [*]
    CANCELLED --> [*]
```

---

### 3.2 Patient Longitudinal Profile & Comprehensive History Portal

Patients have access to their complete digital health footprint, ensuring continuity of care across hospital departments.

```mermaid
graph LR
    subgraph ProfileDomains["21-Domain Longitudinal Health Record"]
        D1["Personal Demographics"]
        D2["Active Chronic Conditions"]
        D3["Allergies & Drug Sensitivities"]
        D4["Current Medications"]
        D5["Past Surgical History"]
        D6["Hospitalizations & Discharges"]
        D7["Family Medical History"]
        D8["Social & Lifestyle Factors"]
        D9["Active Prescriptions"]
        D10["Laboratory Investigations"]
        D11["Diagnostic Imaging"]
        D12["Audit Provenance (patient_facts)"]
    end

    subgraph KioskViews["Patient Kiosk Views"]
        V1["/profile - Profile Snapshot & Contact Updates"]
        V2["/history - Categorized Longitudinal Clinical Record"]
        V3["Discrepancy Reporting Modal"]
    end

    ProfileDomains --> V1
    ProfileDomains --> V2
    V3 -->|New Unverified Claim| PENDING["patient_facts (verified=false)"]
    PENDING -->|Physician Review| V2
```

- **7-Patient Diverse Cohort Demo**: Out-of-the-box pre-configured clinical personas:
  1. *Raj Kumar (42M)*: Type 2 Diabetes, Hypertension, Appendectomy, Penicillin Allergy.
  2. *Anita Desai (38F)*: Rheumatoid Arthritis, Methotrexate, Sulfonamide Allergy.
  3. *Mohan Lal Verma (67M)*: COPD, Ischemic Heart Disease, Aspirin/NSAID Sensitivity.
  4. *Priya Sundaram (29F)*: Hypothyroidism, PCOS, Metformin.
  5. *Dr. Vikram Patel (54M)*: Chronic Kidney Disease (Stage 3b), ACE-Inhibitor Hyperkalemia.
  6. *Sunita Sharma (48F)*: Cholelithiasis, GERD, Ciprofloxacin Allergy.
  7. *Amitabh Roy (61M)*: Post-CABG, Dyslipidemia, Atorvastatin Myopathy.

- **Patient Discrepancy Reporting**: Allows patients to report changes or mistakes in their record. Writes directly to `patient_facts` marked as `verified=false` with provenance tracking for the doctor to review during consultation.

---

### 3.3 Patient Data Isolation & Context Safety

To prevent medical errors, newly registered patients must never inherit or see another patient's medical history.

```mermaid
flowchart TD
    subgraph NewPatientPath["Genuinely New Patient Registration"]
        REG["POST /patients/register"]
        NEW_ENC["Create Fresh Encounter<br/>status: IN_PROGRESS"]
        EMPTY_PROF["Create Empty Longitudinal Profile<br/>conditions: [], allergies: []"]
        SESS_NEW["POST /kiosk/session<br/>Bound to new patient_id & encounter_id"]
        SUMM_NEW["GET /kiosk/summary (X-Session-Token)"]
        DISP_NEW["Display Clean Slate<br/>Allergies: Not documented<br/>History: No previous history<br/>Unknown != Negative"]
        
        REG --> NEW_ENC --> EMPTY_PROF --> SESS_NEW --> SUMM_NEW --> DISP_NEW
    end

    subgraph ExistingPatientPath["Returning Cohort Patient Login"]
        SEARCH["POST /patients/search or Phone Lookup"]
        RES_EXT["Resolve Existing patient_id"]
        SESS_EXT["POST /kiosk/session<br/>Bound to verified patient UUID"]
        PROF_EXT["GET /kiosk/profile & /history"]
        DISP_EXT["Display Full Clinical Record<br/>Active conditions, allergies, medications"]
        
        SEARCH --> RES_EXT --> SESS_EXT --> PROF_EXT --> DISP_EXT
    end

    subgraph SecurityShield["Isolation & Fallback Shields"]
        TOKEN["Session-Token Bound Endpoints<br/>GET /api/v1/kiosk/summary"]
        QUOTA["Deterministic Quota Fallback<br/>Gemini 429 -> MockSummaryProvider"]
        NO_LEAK["Zero-Leakage Guarantee<br/>No hardcoded demo UUID fallbacks"]
    end

    NewPatientPath -.-> SecurityShield
    ExistingPatientPath -.-> SecurityShield
```

- **Clean State Guarantees**: A new patient profile starts with empty arrays.
- **Unknown ≠ Negative Principle**: Absences of records are explicitly labeled *"No information recorded"* or *"Not documented"* rather than assuming negative (e.g., absence of allergy record does not equal "No allergies").
- **API Rate-Limit Graceful Fallback**: If Gemini Vision or Summarization hits 429 Quota Exhaustion or network timeouts, the backend automatically transitions to `MockSummaryProvider` to generate a 100% factual summary grounded strictly in the patient's submitted data, preventing 500 errors or fallback data leaks.

---

### 3.4 Multi-Symptom Adaptive Clinical Intake Engine

The intake engine runs an adaptive question loop based on clinical evidence pathways:

```mermaid
flowchart TD
    START(["Patient Answers Chief Complaint"])
    ROUTER{"Multilingual Symptom Router<br/>(English, Hindi, Hinglish)"}

    START --> ROUTER

    ROUTER -->|"Chest Pain"| CP["Chest Pain Pathway"]
    ROUTER -->|"Fever"| FV["Fever Pathway"]
    ROUTER -->|"Headache"| HA["Headache Pathway"]
    ROUTER -->|"Abdominal Pain"| AP["Abdominal Pain Pathway"]
    ROUTER -->|"Cough / SOB"| CG["Cough & Respiratory Pathway"]
    ROUTER -->|"Vomiting"| VM["Vomiting Pathway"]
    ROUTER -->|"Dizziness"| DZ["Dizziness Pathway"]
    ROUTER -->|"Other"| GN["General Adaptive Pathway"]

    subgraph DimensionEngine["Dimension Priority Loop"]
        D_ONSET["1. Onset & Chronology"]
        D_CHAR["2. Character & Nature"]
        D_SEV["3. Severity Scale (1-10)"]
        D_LOC["4. Location & Radiation"]
        D_ASSOC["5. Associated Symptoms"]
        D_RELIEF["6. Aggravating / Relieving Factors"]
    end

    CP --> DimensionEngine
    FV --> DimensionEngine
    HA --> DimensionEngine
    AP --> DimensionEngine
    CG --> DimensionEngine
    VM --> DimensionEngine
    DZ --> DimensionEngine
    GN --> DimensionEngine

    DimensionEngine --> RED{"Check Deterministic Red Flags"}
    RED -->|Emergency Fired| PRIO["Elevate Queue Priority to HIGH<br/>Alert Triage"]
    RED -->|Normal| CONT["Next Question or Complete"]
```

---

## 4. Prescription & Medicine Search Engine

- **Authoritative Dataset**: 253,000+ commercial Indian drug formulations (`A_Z_medicines_dataset_of_India.csv`).
- **High-Speed FTS5 Search**: Indexed in SQLite (`medicines.db`) with sub-millisecond prefix search by brand, salt/generic composition, and manufacturer.
- **Safety Tripwires**:
  - **Allergy Cross-Reactivity**: Compares prescribed molecules against recorded allergies in `patient_longitudinal_profiles` (e.g. penicillin → amoxicillin cross-reaction).
  - **Duplicate Medication Alert**: Flags therapeutic duplicates against active medications.
  - **Unknown Allergy Status Warning**: Reminds the physician if allergy status was not explicitly confirmed.
- **Workflow Lifecycle**: `DRAFT` ➔ `SAFETY_CHECKED` ➔ `FINALIZED` (immutable lock) ➔ `AMENDED`.

---

## 5. Technology Stack

| Layer | Technologies | Description |
|---|---|---|
| **Backend Core** | FastAPI, Python 3.13, Uvicorn, AnyIO | Async REST API orchestration and security gating |
| **Database & ORM** | Supabase PostgreSQL, SQLAlchemy, Alembic | Relational models, JSONB profiles, immutable audit facts |
| **Medicines Engine** | SQLite (FTS5 full-text search) | 253,000+ Indian medicines indexed for sub-millisecond search |
| **Voice / ASR** | Sarvam AI (`saaras:v3`) | Indic Speech-to-Text supporting 22 languages and Hinglish |
| **Multimodal OCR** | Google Gemini Vision (`gemini-3.6-flash`), PaddleOCR | High-accuracy extraction from crumpled or handwritten slips |
| **Clinical NLU / LLM** | Google Gemini, OpenAI GPT-4o, Custom Validators | Structured entity extraction with anti-hallucination validation |
| **Patient Kiosk** | Next.js 14, React, Tailwind CSS, Lucide Icons | Touch-first, responsive interface for OPD waiting rooms |
| **Doctor Dashboard** | Next.js 14, React, Tailwind CSS, shadcn/ui | Clinical queue, 5-tab workspace, DocTalk collaboration room |
| **Testing** | Pytest, FastAPI TestClient, Vitest | 295+ comprehensive tests across all backend subsystems |

---

## 6. REST API Reference

### 6.1 DocTalk Specialist Network (`/api/v1/doctalk`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/specialists` | Discover specialists filtered by specialty, hospital, and availability |
| `GET` | `/specialists/find-any` | Deterministic auto-match for earliest available specialist |
| `POST` | `/requests` | Create a new specialist consultation request |
| `GET` | `/requests/my-requests` | List outbound consultation requests for the requesting doctor |
| `GET` | `/requests/my-consultations` | List incoming consultation requests for the specialist |
| `GET` | `/requests/{id}` | Retrieve request details |
| `GET` | `/requests/{id}/context` | Pre-acceptance gated clinical context (PII masked prior to accept) |
| `POST` | `/requests/{id}/accept` | Specialist accepts request and unlocks full encounter |
| `POST` | `/requests/{id}/decline` | Specialist declines request with reason |
| `POST` | `/requests/{id}/start` | Transition status to `IN_PROGRESS` |
| `POST` | `/requests/{id}/complete` | Submit final specialist opinion and complete consultation |
| `GET/POST`| `/requests/{id}/notes` | Live consultation mutual notes and structured discussion |

### 6.2 Patient Kiosk & Profiles (`/api/v1/kiosk`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/session` | Create or resume a kiosk session token |
| `GET` | `/profile` | Comprehensive patient profile with longitudinal data |
| `PATCH` | `/profile/demographics` | Safe patient self-service contact and demographic update |
| `POST` | `/profile/report-change` | Log discrepancy / unverified medical history change for doctor review |
| `GET` | `/summary` | Session-authenticated AI clinical summary (strictly isolated) |
| `POST` | `/summary/generate` | Trigger on-demand AI summary draft for authenticated kiosk session |

### 6.3 Clinical Intake & Voice (`/api/v1`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/clinical/start` | Initialize clinical intake conversation for session |
| `GET` | `/clinical/state` | Current conversation state, active pathway, collected facts |
| `POST` | `/clinical/answer` | Submit answer (voice transcript or text), extract facts, evaluate red flags |
| `POST` | `/voice/transcribe` | Sarvam AI ASR multipart audio transcription |
| `POST` | `/documents/upload` | Upload physical slip/lab report for OCR and entity extraction |

### 6.4 Prescriptions & Encounters (`/api/v1`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/medicines/search` | Fast autocomplete across 253k Indian medicines |
| `GET` | `/medicines/{id}` | Detailed medicine composition, salt, and manufacturer |
| `POST` | `/encounters/{id}/prescriptions`| Create or update draft prescription |
| `POST` | `/prescriptions/{id}/safety-check` | Execute deterministic allergy and duplicate checks |
| `POST` | `/prescriptions/{id}/finalize` | Sign-off and finalize prescription; sync to longitudinal record |
| `GET` | `/encounters/active` | Hospital-scoped active queue sorted by red-flag severity |

---

## 7. Database Schema & Models

```mermaid
erDiagram
    HOSPITALS ||--o{ USERS : employs
    HOSPITALS ||--o{ PATIENTS : registers
    PATIENTS ||--o{ ENCOUNTERS : attends
    ENCOUNTERS ||--o{ KIOSK_SESSIONS : activates
    ENCOUNTERS ||--o{ CLINICAL_HISTORIES : collects
    ENCOUNTERS ||--o{ RED_FLAGS : triggers
    ENCOUNTERS ||--o{ DOCUMENTS : contains
    ENCOUNTERS ||--o{ CLINICAL_SUMMARIES : produces
    ENCOUNTERS ||--o{ PRESCRIPTIONS : prescribes
    ENCOUNTERS ||--o{ DOCTALK_CONSULTATIONS : initiates

    PATIENTS ||--o| PATIENT_LONGITUDINAL_PROFILES : snapshots
    PATIENTS ||--o{ PATIENT_FACTS : records

    DOCTALK_CONSULTATIONS ||--o{ DOCTALK_NOTES : contains
    PRESCRIPTIONS ||--o{ PRESCRIPTION_ITEMS : details
```

---

## 8. Directory Structure

```text
MediKiosk/
├── A_Z_medicines_dataset_of_India.csv       # 253k Indian medicines dataset
├── README.md                                # This document
├── AGENTS.md                                # Architecture knowledge base & agent rules
├── ai/                                      # Multimodal AI & Deterministic Engines
│   ├── asr/                                 # Sarvam ASR provider + Mock
│   ├── clinical_nlu/                        # Clinical NLU extraction providers
│   ├── medical_extraction/                  # OCR entity extraction models & logic
│   ├── ocr/                                 # Gemini Vision & PaddleOCR providers
│   ├── question_engine/                     # Adaptive clinical symptom pathways
│   ├── reconciliation/                      # Deterministic Fact Reconciliation
│   ├── red_flags/                           # Deterministic Red-Flag Rule Engine
│   └── summarization/                       # Clinical summary providers & validator
├── backend/                                 # FastAPI Application
│   ├── alembic/                             # Database migrations
│   ├── app/
│   │   ├── api/endpoints/                   # clinical, doctalk, encounters, kiosk, etc.
│   │   ├── models/models.py                 # SQLAlchemy database schema
│   │   ├── schemas/                         # Pydantic request & response models
│   │   └── services/                        # Medicine search, DocTalk session manager, etc.
│   └── tests/                               # 295 automated Pytest suites
└── frontend/
    ├── patient-kiosk/                       # Next.js 14 touch-first kiosk application (Port 3000)
    │   └── src/app/
    │       ├── clinical/                    # Conversational intake with voice
    │       ├── history/                     # Comprehensive medical history portal
    │       ├── profile/                     # Patient profile & discrepancy reporting
    │       └── summary-preview/             # Isolated AI summary preview
    └── doctor-dashboard/                    # Next.js 14 physician dashboard (Port 3001)
        └── src/app/
            ├── queue/                       # Priority triage queue
            ├── encounters/[id]/             # 5-tab physician workspace
            └── doctalk/                     # DocTalk specialist tele-consultation hub
```

---

## 9. Quickstart & Local Setup

### 9.1 Prerequisites
- **Python 3.13+**
- **Node.js 18+ & npm**
- **Supabase PostgreSQL** account or local PostgreSQL instance

### 9.2 Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, GEMINI_API_KEY, and SARVAM_API_KEY

# Run database migrations & seed reference data
alembic upgrade head
python seed_doctors.py
python seed_patients.py

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 9.3 Patient Kiosk Setup (Port 3000)
```bash
cd frontend/patient-kiosk
npm install
npm run dev
# Kiosk accessible at http://localhost:3000
```

### 9.4 Doctor Dashboard Setup (Port 3001)
```bash
cd frontend/doctor-dashboard
npm install
npx next dev --port 3001
# Dashboard accessible at http://localhost:3001
```

---

## 10. Testing & Validation

The codebase includes **295 automated tests** covering all clinical safety paths, cross-hospital isolation boundaries, DocTalk workflows, and patient data protection rules.

```bash
cd backend

# Run the complete test suite
pytest -v

# Run specific isolation and safety suites
pytest tests/test_patient_data_isolation.py -v
pytest tests/test_patient_profile.py -v
pytest tests/test_doctalk.py tests/test_doctalk_security.py -v
pytest tests/test_prescriptions.py -v
pytest tests/test_red_flags.py -v
```

### Frontend Static Type Checking:
```bash
cd frontend/patient-kiosk && npx tsc --noEmit
cd frontend/doctor-dashboard && npx tsc --noEmit
```

---

## 11. Safety, Governance & Clinical Ethics

1. **Human-in-the-Loop Imperative**: AI generates preliminary documentation drafts only; a licensed physician must review, edit, and sign off on every clinical summary and prescription.
2. **Deterministic Safety Primacy**: Red-flag emergency detection and drug-drug/allergy safety checks are 100% deterministic rules. AI is never permitted to override or suppress triage severity.
3. **Unknown ≠ Negative**: Absence of clinical data is never treated as a negative finding. The system explicitly reminds physicians when allergies or past histories are unrecorded.
4. **Verifiable Provenance**: Every extracted clinical claim maintains a reference to source text, timestamp, and confidence score. The Anti-Hallucination Validator automatically strips unsupported statements.
5. **Hospital-Level Tenant Isolation**: All endpoints enforce strict hospital boundary access checks. Cross-tenant queries fail with HTTP 404 to eliminate information leakage.

---

## 12. Authors & License

Maintained by the **MediPlatform Engineering Team**.  
Licensed under the [MIT License](LICENSE).
