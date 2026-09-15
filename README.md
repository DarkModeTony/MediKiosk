# MediPlatform (MediKiosk)
> **Autonomous AI-Powered Clinical Intake & Medical Record Preparation Platform for High-Volume Healthcare**

[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 14+](https://img.shields.io/badge/Next.js-14%2B-black.svg)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC.svg)](https://tailwindcss.com/)
[![shadcn/ui](https://img.shields.io/badge/shadcn%2Fui-base--nova-000000.svg)](https://ui.shadcn.com/)
[![Supabase Postgres](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E.svg)](https://supabase.com)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4.svg)](https://ai.google.dev/)
[![Sarvam AI](https://img.shields.io/badge/Voice-Sarvam%20AI%20ASR-FF6F00.svg)](https://www.sarvam.ai/)

---

## 1. Executive Summary & Clinical Context

High-volume Outpatient Departments (OPDs) across high-density healthcare ecosystems (such as tertiary public and private hospitals in India) operate under extreme pressure. Doctors often see **80 to 120+ patients per shift**, leaving as little as **2 to 3 minutes per consultation**. 

### The Problem
* **Documentation Burden**: Clinicians spend more than 50% of consultation time manually transcribing patient complaints, deciphering crumpled handwritten paper prescriptions, and documenting vitals.
* **Paper-Based Fragmentation**: Patients carry bags of past physical prescriptions, lab slips, and discharge summaries that doctors do not have the time to read or digitize during a 3-minute visit.
* **Language & Literacy Barriers**: Rural and semi-urban patients struggle to convey their longitudinal history, leading to missed symptoms or overlooked drug interactions.
* **No Digital Triage**: High-risk patients (e.g., unstable angina, acute respiratory distress) wait in the exact same physical queue as patients with minor ailments.

### The MediPlatform Solution
**MediPlatform** turns the waiting room into a high-throughput clinical preparation engine:
1. **Smartphone-Less Patient Kiosk**: Patients walk up to a large touch-screen kiosk, authenticate via phone or hospital ID, and undergo an adaptive, voice-enabled intake in regional languages.
2. **Sarvam AI Indic Voice ASR**: Patients can speak naturally into the kiosk microphone; speech is transcribed in real-time with Indian accent and regional language awareness.
3. **Multimodal Document Digitization**: Patients upload photos of previous prescriptions and lab reports; Google Gemini extracts raw text (OCR) and converts it into structured clinical entities (medications, dosages, diagnoses, vitals).
4. **Deterministic Safety Tripwires**: Server-authoritative clinical rules flag critical red flags immediately (e.g., severe chest pain radiating to the jaw) and boost patient queue priority.
5. **Doctor-in-the-Loop Clinical Dashboard**: When the patient enters the consultation room, the doctor has a structured, pre-assembled clinical summary with evidence provenance. The doctor reviews, modifies, and verifies the record with one click.

---

## 2. System Architecture

```mermaid
flowchart TD
    subgraph PatientExperience["Patient Experience (Waiting Room)"]
        PK["Patient Kiosk (Next.js 14)<br/>• Touch-first UI<br/>• Web Audio Recording<br/>• Document Camera / Upload"]
    end

    subgraph ExternalAI["Multimodal AI Services"]
        SARVAM["Sarvam AI (Saaras v3)<br/>• Indic Speech-to-Text<br/>• Real-time Transcription"]
        GEMINI_OCR["Google Gemini Vision (OCR)<br/>• Prescription Digitization<br/>• Lab Report Transcoding"]
        GEMINI_EXT["Google Gemini Extraction<br/>• Structured Medical Entities<br/>• Provenance & Confidence"]
        GEMINI_SUM["Google Gemini Summarizer<br/>• Clinical Draft Generation<br/>• Anti-Hallucination Validator"]
    end

    subgraph BackendCore["FastAPI Backend Orchestrator"]
        API["FastAPI REST API (Python 3.14)"]
        RED_FLAG["Deterministic Red-Flag Engine<br/>• Server-Authoritative Safety Rules"]
        PATHWAYS["Clinical Pathway Engine<br/>• Dynamic Branching Questions"]
        LONGITUDINAL["Longitudinal Profile Service<br/>• 21 Health Domains & Facts"]
    end

    subgraph DatabaseLayer["Persistence Layer"]
        POSTGRES[("Supabase PostgreSQL<br/>• SQLAlchemy ORM<br/>• Alembic Migrations")]
    end

    subgraph DoctorExperience["Doctor Consultation Room"]
        DD["Doctor Dashboard (Next.js 14)<br/>• Priority Triage Queue<br/>• Split-Pane Encounter Workspace<br/>• Verified Clinical Record Sign-off"]
    end

    PK -->|"Audio Streams"| API
    API -->|"Multipart Audio"| SARVAM
    SARVAM -->|"Transcribed Text"| API
    API -->|"Branching Questions"| PK

    PK -->|"Document Uploads"| API
    API -->|"Vision OCR"| GEMINI_OCR
    GEMINI_OCR -->|"Raw Text"| API
    API -->|"Structured Extraction"| GEMINI_EXT
    GEMINI_EXT -->|"Entities & Vitals"| API

    API -->|"Deterministic Rules"| RED_FLAG
    API -->|"Aggregate History + Entities"| GEMINI_SUM
    GEMINI_SUM -->|"Draft Summary"| API
    API <-->|"Persistence & State"| POSTGRES

    POSTGRES -->|"Triage Sorted Queue"| DD
    DD -->|"Review & Final Verification"| API
```

---

## 3. Core Modules & Capabilities

### 🩺 1. Patient Kiosk (`frontend/patient-kiosk`)
- **Modern Base-Nova UI**: High-contrast, accessibility-first design with smooth micro-animations, glassmorphism, and large touch targets designed for kiosks.
- **Bi-modal Intake (Voice + Touch)**:
  - Powered by **Sarvam AI (Saaras v3)**: Native browser `MediaRecorder` audio capture streamed to the backend for high-accuracy Indian-language speech-to-text.
  - Live transcript review and correction before submission.
- **Adaptive Clinical Tree**: Traverses dynamic decision trees based on primary symptoms (chest pain, respiratory distress, fever, etc.).
- **Document Uploader**: Intuitive drag-and-drop / camera snapshot uploader with document categorization (prescriptions, lab tests, discharge summaries).
- **Patient Summary Preview**: Interactive review accordion showing captured concerns and OCR-extracted medications with Gemini status indicators.

### 👨‍⚕️ 2. Doctor Dashboard (`frontend/doctor-dashboard`)
- **Triage Queue with Priority Elevation**: Encounters are automatically prioritized based on server-evaluated red flags (HIGH severity = pulsing emergency indicator).
- **Encounter Workspace**:
  - **Clinical Summary Panel**: In-place editable draft summary synthesized by Gemini.
  - **Evidence Provenance**: Click on any extracted medication or symptom to see the exact bounding box / source text snippet from the patient's uploaded document.
  - **Interactive Verification**: One-click verification stamping doctor credentials, timestamp, and audit trail.
- **Clinical Timeline**: Visual timeline tracking patient registration, document uploads, red-flag triggers, and verification milestones.
- **Dark Mode Support**: One-click toggle between light mode and eye-comfort dark mode for dimly lit clinical environments.

### 🧠 3. AI & Safety Architecture (`ai/`)
- **Dual-Provider Architecture (Factory Pattern)**:
  - Every AI subsystem (`OCR`, `Medical Extraction`, `Summarization`, `ASR`) implements a strict provider interface with both **Gemini/Sarvam** and **Mock** implementations.
  - Guarantees seamless offline/local development even if external API limits or internet connections are disrupted.
- **Anti-Hallucination Evidence Validator (`ai/summarization/validator.py`)**:
  - Cross-references all medications, dosages, and diagnoses in the AI summary against raw document entities and patient Q&A.
  - Unsubstantiated claims are stripped or flagged before reaching the doctor.
- **Deterministic Red-Flag Engine (`ai/red_flags/engine.py`)**:
  - **Strict Rule**: AI never determines medical triage severity. Red flags are evaluated deterministically by server-side rules (e.g., chest pain duration, radiating pain, diaphoresis).

### 🧬 4. Longitudinal Patient Health Profile Schema (v1.0)
- Defined in `backend/app/schemas/longitudinal_profile.py` with SQLAlchemy persistence (`PatientLongitudinalProfile` and `PatientFact`).
- Covers **21 Clinical Domains**:
  - Medical History & Chronic Conditions
  - Surgical History & Anatomical Status (implements *"unknown != no"* medical semantics)
  - Medical Devices & Implants (pacemakers, stents)
  - Sensory & Functional Limitations
  - Social & Occupational History
  - Reproductive History & Vitals
  - Cognitive & Mental Health State
  - Provenance-Tracked Fact Store (`patient_facts`)

---

## 4. Repository Structure

```text
MediKiosk/
├── ai/                                  # Modular AI abstractions & business logic
│   ├── asr/                             # Voice processing (Sarvam AI Saaras v3 + Mock)
│   ├── clinical_nlu/                    # Clinical intent & entity parsing
│   ├── medical_extraction/              # Prescription entity extraction (Gemini + Mock)
│   ├── ocr/                             # Image & prescription OCR (Gemini Vision + Mock)
│   ├── question_engine/                 # Dynamic clinical pathway state machines
│   ├── red_flags/                       # Deterministic emergency triage rules
│   └── summarization/                   # Clinical draft summarization & validation
├── backend/                             # FastAPI Core REST Orchestrator
│   ├── alembic/                         # Database schema migrations
│   │   └── versions/                    # Versioned migration files
│   ├── app/
│   │   ├── api/endpoints/               # REST Route Handlers
│   │   │   ├── clinical.py              # Intake Q&A & pathway progression
│   │   │   ├── documents.py             # File upload, OCR, entity extraction
│   │   │   ├── encounters.py            # Queue management & encounter status
│   │   │   ├── longitudinal.py          # 21-domain longitudinal profile & facts
│   │   │   ├── patients.py              # Patient registration & demographic lookup
│   │   │   └── voice.py                 # Sarvam AI speech-to-text endpoint
│   │   ├── models/                      # SQLAlchemy Database Models
│   │   │   └── models.py                # Patients, Encounters, RedFlags, Summaries, etc.
│   │   ├── schemas/                     # Pydantic Request/Response Models
│   │   │   └── longitudinal_profile.py  # Comprehensive medical profile schema
│   │   ├── services/                    # Storage, database session management
│   │   ├── database.py                  # Database engine & sessionmaker
│   │   └── main.py                      # Application factory & middleware configuration
│   ├── tests/                           # Pytest integration & unit test suite
│   │   ├── test_longitudinal_profile.py # Longitudinal profile & fact tests
│   │   ├── test_voice.py                # Sarvam & Mock ASR tests
│   │   └── ...
│   ├── requirements.txt                 # Python dependencies
│   └── .env.example                     # Environment template
├── frontend/                            # Next.js 14 Applications
│   ├── patient-kiosk/                   # Touch-friendly Patient Kiosk (Port 3000)
│   │   ├── src/app/
│   │   │   ├── clinical/                # Voice/touch clinical conversation
│   │   │   ├── consent/                 # Patient privacy consent
│   │   │   ├── documents/               # Document scanning & upload
│   │   │   ├── registration/            # New / Returning patient intake
│   │   │   ├── session/                 # Kiosk session launcher
│   │   │   └── summary-preview/         # Pre-consultation summary check
│   │   ├── src/components/shared/       # BrandEmblem, LargeTouchButton, Header
│   │   └── src/lib/api/                 # Backend REST client wrappers
│   └── doctor-dashboard/                # Clinical Review Dashboard (Port 3001)
│       ├── src/app/
│       │   ├── dashboard/               # High-level OPD overview & metrics
│       │   ├── encounters/[id]/         # Split-screen clinical encounter workspace
│       │   ├── login/                   # Doctor authentication
│       │   └── queue/                   # Priority-sorted triage waiting list
│       ├── src/components/layout/       # Collapsible sidebar & dark mode controller
│       └── src/components/workspace/    # RedFlagPanel, SummaryPanel, DocumentViewer
├── docs/                                # Architecture specs & functional design docs
├── AGENTS.md                            # Primary AI agent instructions & session logs
└── README.md                            # System documentation (this file)
```

---

## 5. Database Schema (PostgreSQL)

The persistence layer is managed via **SQLAlchemy** on **Supabase PostgreSQL**:

| Table | Purpose | Key Columns |
|---|---|---|
| `patients` | Root patient identity | `id`, `uhid`, `demographic_data` (JSONB), `created_at` |
| `encounters` | Individual clinical visit | `id`, `patient_id`, `status` (`IN_PROGRESS`, `WAITING`, `COMPLETED`), `priority` |
| `kiosk_sessions` | Ephemeral kiosk auth token | `id`, `session_token`, `encounter_id`, `is_active` |
| `clinical_histories` | Raw intake Q&A transcript | `id`, `encounter_id`, `qa_payload` (JSONB) |
| `red_flags` | Deterministic safety alerts | `id`, `encounter_id`, `rule_name`, `severity` (`HIGH`, `MEDIUM`), `metadata` |
| `documents` | Uploaded prescription/lab files | `id`, `encounter_id`, `file_name`, `storage_path`, `file_type` |
| `document_ocr` | Raw transcribed text | `id`, `document_id`, `raw_text`, `ocr_provider` |
| `document_entities` | Structured medical facts | `id`, `document_id`, `entity_type`, `entity_value`, `confidence_score` |
| `clinical_summaries` | Gemini AI draft summary | `id`, `encounter_id`, `draft_content` (JSONB), `version` |
| `summary_verifications`| Verified clinical sign-off | `id`, `summary_id`, `doctor_id`, `final_content` (JSONB), `verified_at` |
| `patient_longitudinal_profiles` | 21-domain lifetime profile | `id`, `patient_id`, `profile_data` (JSONB), `version` |
| `patient_facts` | Provenance-tracked medical facts | `id`, `patient_id`, `fact_domain`, `fact_key`, `fact_value`, `source_type` |

---

## 6. Getting Started & Local Setup

### Prerequisites
* **Python**: `3.10+` (Developed and validated on `Python 3.14.7`)
* **Node.js**: `18.0.0+` (LTS recommended)
* **PostgreSQL / Supabase**: An active Postgres instance or Supabase project
* **API Keys**:
  * [Google Gemini API Key](https://aistudio.google.com/)
  * [Sarvam AI API Key](https://www.sarvam.ai/) (for Indic speech-to-text)

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/DarkModeTony/MediKiosk.git
cd MediKiosk
```

---

### Step 2: Backend Setup & Database Migrations
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

#### Configure `backend/.env`:
```env
DATABASE_URL=postgresql://postgres.your-ref:your-password@aws-0-region.pooler.supabase.com:5432/postgres
GEMINI_API_KEY=your_gemini_api_key_here
SARVAM_API_KEY=your_sarvam_api_key_here

# Provider Modes: 'real' (HTTP calls) or 'mock' (local zero-quota testing)
AI_MODE=real
OCR_MODE=gemini
LLM_PROVIDER=gemini
ASR_MODE=sarvam
```

#### Run Database Migrations:
```bash
alembic upgrade head
```

#### Start the Backend Server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The FastAPI documentation will be available at:
* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Step 3: Patient Kiosk Frontend Setup
Open a new terminal window:
```bash
cd frontend/patient-kiosk

# Install dependencies
npm install

# Create environment configuration
# Ensure .env.local contains:
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_DATA_MODE=api

# Start Patient Kiosk dev server
npm run dev
```
Access the Patient Kiosk at [http://localhost:3000](http://localhost:3000).

---

### Step 4: Doctor Dashboard Frontend Setup
Open another terminal window:
```bash
cd frontend/doctor-dashboard

# Install dependencies
npm install

# Create environment configuration
# Ensure .env.local contains:
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_DATA_MODE=api

# Start Doctor Dashboard dev server (port 3001)
npm run dev -- -p 3001
```
Access the Doctor Dashboard at [http://localhost:3001](http://localhost:3001).

---

## 7. Key API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/patients/register` | Registers a new patient or resolves existing UHID |
| `POST` | `/api/v1/clinical/progress` | Submits answers and receives next pathway question |
| `POST` | `/api/v1/voice/transcribe` | Streams multipart audio to Sarvam AI ASR for transcription |
| `POST` | `/api/v1/documents/upload` | Uploads document, triggers Gemini OCR & medical entity extraction |
| `GET` | `/api/v1/encounters/active` | Retrieves triage-sorted patient queue for doctor dashboard |
| `GET` | `/api/v1/encounters/{id}` | Detailed encounter view with summary, OCR documents, & red flags |
| `POST` | `/api/v1/encounters/{id}/verify` | Clinician sign-off saving immutable `summary_verifications` |
| `GET` | `/api/v1/patients/{id}/longitudinal-profile` | Fetches 21-domain patient medical history profile |
| `POST` | `/api/v1/patients/{id}/facts` | Appends provenance-tracked clinical fact to patient history |

---

## 8. Testing & Validation

MediPlatform includes extensive automated test suites covering API contracts, database operations, longitudinal profiles, and voice transcription:

```bash
# Activate backend virtual environment
cd backend
source .venv/bin/activate # or .venv\Scripts\activate on Windows

# Run complete pytest test suite
python -m pytest tests/ -v

# Run voice ASR test suite
python -m pytest tests/test_voice.py -v

# Run longitudinal profile schema test suite
python -m pytest tests/test_longitudinal_profile.py -v

# Run End-to-End pipeline smoke test (requires valid GEMINI_API_KEY)
python smoke_test_full_e2e.py
```

---

## 9. Safety, Governance & Ethical Disclaimers

1. **Human-in-the-Loop Authority**: The AI subsystems (Gemini, Sarvam) act **strictly as assistive intake scribes**. No AI output is accepted into the patient's legal medical record without explicit review, potential modification, and formal cryptographic verification by a licensed medical practitioner.
2. **Server-Authoritative Red Flags**: Clinical triage elevation is performed by deterministic rule-based code, not generative models.
3. **Evidence Validation**: All clinical entities extracted by LLMs must cite source document provenance (bounding coordinates or source string offsets). Unverified hallucinations are rejected.
4. **Data Privacy & PHI**: This repository contains strictly synthetic, de-identified clinical test fixtures. When deploying to clinical settings, ensure compliance with applicable national healthcare privacy regulations (e.g., India's ABDM / DISHA, HIPAA).

---

## 10. Roadmap & Upcoming Milestones

- [x] Multilingual Touch-Screen Patient Kiosk UI
- [x] Gemini Vision OCR & Prescription Entity Extraction
- [x] Sarvam AI Indic Voice Speech-to-Text (`saaras:v3`)
- [x] 21-Domain Longitudinal Health Profile Schema
- [x] Doctor Queue & Summary Verification Workspace
- [x] Base-Nova shadcn design system overhaul
- [ ] Ayushman Bharat Digital Mission (ABDM) M1/M2/M3 compliance
- [ ] Standard FHIR R4 Bundle export (`fhir/`)
- [ ] Direct thermal printer prescription slip generation for patients

---

## 11. Authors & License

Maintained by the **MediPlatform Engineering Team**.  
Licensed under the [MIT License](LICENSE).
