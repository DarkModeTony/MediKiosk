# MediPlatform — Agent Knowledge Base & Project Blueprint

> [!IMPORTANT]
> **SYSTEM INSTRUCTION FOR AGENTS:**
> This document is the primary source of truth for any AI agent or developer working on MediPlatform.
> It documents the architecture, constraints, and implementation status as they **actually exist in the repository today**.
> Do not invent features that are not verified. Do not treat planned features as implemented.
> Before making changes, re-read the relevant sections here and verify assumptions against the actual code.

---

## 1. Project Overview

- **Name**: MediPlatform (repository: MediKiosk)
- **Goal**: An AI-assisted clinical intake and medical record preparation platform for high-volume Indian hospitals.
- **Problem**: Doctors in busy OPDs spend excessive time documenting patient histories, reducing diagnostic time.
- **Solution**: A smartphone-less Patient Kiosk collects structured history before the doctor visit. The backend uses multiple AI providers (Gemini for OCR/extraction/summarization, Sarvam for ASR) and deterministic rule engines (red-flag detection). The doctor reviews, edits, and verifies an AI-drafted clinical summary. The doctor is always the final clinical decision-maker.

---

## 2. Technology Stack

### A. Backend Core
- **FastAPI (Python 3.14.7)**: Central orchestrator. Exposes RESTful endpoints consumed by both frontends.
- **SQLAlchemy & Alembic**: ORM and migration tooling. All models are in `backend/app/models/models.py`. Migrations are in `backend/alembic/versions/`.
- **AnyIO / Starlette**: Used inherently by FastAPI for async concurrency.

### B. Database Layer
- **Supabase (PostgreSQL)**: Primary persistence layer.
- **How it's used**: We connect directly to PostgreSQL via SQLAlchemy using a `DATABASE_URL` connection string. We do **NOT** use the Supabase client SDK for data operations.
- **SQLite (medicines.db)**: A secondary local SQLite database stores the 253k Indian medicines dataset for sub-millisecond prescription search. Managed by `backend/app/services/medicine_search.py`. It is NOT used for patient or clinical data.

### C. Frontend Layer (Next.js 14+)
- **Two separate applications**:
  1. `frontend/patient-kiosk` — Touch-friendly UI for patients in the waiting room. Runs on port 3000.
  2. `frontend/doctor-dashboard` — Data-rich UI for doctors to review queues and verify clinical summaries. Runs on port 3001.
- **TypeScript & Tailwind CSS**: Strict typing and utility-first styling.
- **shadcn/ui (base-nova style)**: Installed and used in `doctor-dashboard`. Components include: button, badge, card, input, label, separator, dialog, table, tabs, progress, select, textarea.
- **Font**: `next/font/google` with Inter used in both frontends.
- **API communication**: Both frontends use `fetch` wrappers in `src/lib/api/`. They read `NEXT_PUBLIC_API_URL` to route calls to the FastAPI backend.

### D. AI Layer — Multi-Provider Architecture

> [!IMPORTANT]
> **Do not assume that Sarvam AI replaces Gemini.** Sarvam is used only for voice/ASR. Gemini remains the provider for OCR, medical extraction, and summarization. Both are active and independently configurable.

The AI layer is organized into independent subsystems, each with its own provider interface:

| Subsystem | Interface | Mock Provider | Real Providers | `.env` key |
|---|---|---|---|---|
| **ASR (Voice)** | `ASRProvider` | `MockASRProvider` | `SarvamASRProvider` | `ASR_MODE` |
| **OCR** | `OCRProvider` | `MockOCRProvider` | `GeminiOCRProvider`, `PaddleOCRProvider` | `OCR_MODE` |
| **Medical Extraction** | `ExtractionProvider` | `MockExtractionProvider` | `GeminiExtractionProvider` | `EXTRACTION_MODE` |
| **Summarization** | `SummaryProvider` | `MockSummaryProvider` | `GeminiSummaryProvider`, `OpenAISummaryProvider` | `AI_MODE` + `LLM_PROVIDER` |
| **Clinical NLU** | *(inline, no interface)* | `ClinicalNLUService` (keyword-based mock) | *(not yet a real provider)* | N/A |
| **Red-Flag Detection** | *(deterministic, no AI)* | `RedFlagEngine` | N/A — always deterministic | N/A |

Each subsystem follows a factory pattern (e.g., `get_asr_provider()`, `get_ocr_provider()`) that reads `.env` variables to select the provider at runtime.

**CRITICAL**: Mock providers are mandatory for local development when API quotas are exhausted or internet is unavailable. Never remove mock providers.

---

## 3. AI Subsystem Detail

### ASR — Voice Transcription (Sarvam AI)
- **Provider**: `SarvamASRProvider` in `ai/asr/provider.py`
- **Model**: `saaras:v3` via `https://api.sarvam.ai/speech-to-text`
- **Activation**: `ASR_MODE=sarvam` in `.env`
- **Supported audio formats**: WAV, WebM, OGG, MP4, MP3 (browser `MediaRecorder` default is `audio/webm`)
- **Languages**: 22 Indian languages + Indian English with code-mixing (Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Odia, Punjabi, English-IN)
- **REST endpoint**: `POST /api/v1/voice/transcribe` (multipart form: `audio` file + optional `language_code`)
- **Returns**: `{ transcript, detected_language, status }`
- **What it does NOT do**: Sarvam ASR is a **transcription-only** service. It converts patient speech to text. There is **no TTS (text-to-speech)**, no bidirectional voice conversation loop, and no Sarvam-powered chatbot. The conversational clinical intake is conducted via on-screen UI prompts and text/touch answers, with voice-to-text as an input method.

### OCR (Gemini / PaddleOCR / Mock)
- **Gemini provider**: `ai/ocr/gemini_provider.py` — passes images to Gemini Vision to extract raw text from uploaded documents.
- **PaddleOCR provider**: `ai/ocr/paddle_provider.py` — local offline OCR alternative (does not require Gemini API key).
- **Mock provider**: `ai/ocr/mock_provider.py` — returns hardcoded text for development.
- **Activation**: `OCR_MODE=gemini` (or `real`), `OCR_MODE=paddle`, or `OCR_MODE=mock` (default).

### Medical Extraction (Gemini / Mock)
- **Gemini provider**: `ai/medical_extraction/gemini_provider.py` — given OCR raw text, prompts Gemini with a strict JSON schema to identify medications, vitals, diagnoses; assigns `confidence_score` and `source_text` provenance.
- **Mock provider**: `ai/medical_extraction/mock_provider.py`
- **Activation**: `EXTRACTION_MODE=gemini` (or `real`) or `EXTRACTION_MODE=mock` (default).

### Summarization (Gemini / OpenAI / Mock)
- **Gemini provider**: `ai/summarization/gemini_provider.py`
- **OpenAI provider**: `ai/summarization/openai_provider.py`
- **Mock provider**: `ai/summarization/mock_provider.py`
- **Activation**: `AI_MODE=real` + `LLM_PROVIDER=gemini` or `LLM_PROVIDER=openai`. Default: mock.
- **Validator**: `ai/summarization/validator.py` contains `AntiHallucinationValidator`. It strips any clinical entity (diagnosis, medication) from the AI-generated summary draft that cannot be traced back to the source data. This validation is non-negotiable and must not be bypassed.

### Clinical NLU (Partially Implemented – Mock + Real Provider)
- Interface defined in `ai/clinical_nlu/interface.py` (`NLUProvider` abstract class).
- Real provider `GeminiNLUProvider` implemented in `ai/clinical_nlu/gemini_provider.py` for structured extraction using Gemini.
- Mock provider `MockNLUProvider` remains for offline development (`ai/clinical_nlu/mock_provider.py`).
- Factory in `ai/clinical_nlu/service.py` selects provider based on `NLU_MODE` environment variable.
- Still does **not** perform diagnosis or prescribe medication; it only extracts factual clinical entities.

### Red-Flag Engine (Deterministic — No AI)
- Located at `ai/red_flags/engine.py`.
- Purely rule-based. Evaluates clinical facts against hardcoded rules (CARDIAC_EMERGENCY_SUSPECTED, THUNDERCLAP_HEADACHE, HIGH_GRADE_FEVER).
- **Red-flag detection is always deterministic. AI must never generate, modify, or suppress red flags.**

### Conversation → Patient Facts Pipeline
- Implemented in `backend/app/services/conversation_fact_pipeline.py`.
- Orchestrates ASR transcripts → NLU extraction → validation → deterministic conflict detection → insertion into `patient_facts`.
- Uses `ai/reconciliation/engine.py` for fact conflict handling.
- Status: *Partially Implemented – pipeline exists, integration with clinical endpoint pending.*

### Fact Reconciliation Engine
- Implemented in `ai/reconciliation/engine.py`.
- Deterministic engine that detects contradictory facts, preserves historical facts, and flags conflicts for doctor review.
- Status: *Implemented (deterministic, no AI).*
---

## 4. Database Schema

Defined in `backend/app/models/models.py`. Migrations: `backend/alembic/versions/`.

### Core Tables

| Table | Purpose |
|---|---|
| `hospitals` | Multi-tenant hospital root entity |
| `users` | Doctors and staff, linked to a hospital |
| `patients` | Patient identity. `demographic_data` is a JSONB column |
| `encounters` | One per visit. Statuses: `IN_PROGRESS`, `WAITING_FOR_DOCTOR`, `COMPLETED` |
| `kiosk_sessions` | Links transient kiosk session (`session_token` UUID) to an active encounter |
| `clinical_histories` | Raw Q&A conversation data from kiosk intake (JSONB) |
| `symptoms` | Individual symptom records captured during intake |
| `observations` | Structured clinical observation records |
| `documents` | Uploaded files (image/PDF) — stored locally in `backend/uploads/` |
| `document_ocr` | Raw OCR text per document page, includes `engine_used` and `confidence` |
| `document_entities` | Structured medical entities extracted from OCR text (medication, dosage, diagnosis), with `confidence_score` and `source_text` provenance |
| `medications` | Legacy/simple medication records per patient |
| `clinical_summaries` | AI-generated draft summary for an encounter (`draft_content` JSONB) |
| `summary_verifications` | Doctor edits and verifications of a summary draft (`final_content` JSONB, `status`) |
| `red_flags` | Deterministic safety events per encounter: `rule_name`, `severity` (HIGH/MEDIUM), `status` |
| `prescriptions` | Doctor prescriptions per encounter (DRAFT → FINALIZED → AMENDED → CANCELLED) |
| `prescription_items` | Individual medication line items within a prescription |
| `consents` | Patient consent records |
| `audit_logs` | Action audit trail per user |
| `fhir_resources` | FHIR resource storage (table exists; full ABDM integration is not yet implemented) |
| `patient_longitudinal_profiles` | Per-patient structured health profile snapshot (JSONB, schema v1.0) |
| `patient_facts` | Provenance-tracked individual clinical facts per patient |

### Longitudinal Patient Data Architecture

`patient_longitudinal_profiles` stores a JSONB snapshot of the patient's structured medical profile (21 domains including medical history, anatomical status, devices, sensory, functional, social, vitals, cognitive, reproductive, provenance, chatbot memory). Accessed via `GET/PUT/PATCH /api/v1/patients/{patient_id}/longitudinal-profile`.

`patient_facts` is a normalized, immutable provenance store. Each row represents one clinical fact (e.g., an allergy, chronic condition, medication) with fields: `category`, `fact_type`, `body_site`, `laterality`, `value`, `source_type`, `source_id`, `confidence`, `verified`, `valid_from`, `valid_until`. Accessed via `POST/GET /api/v1/patients/{patient_id}/facts`.

**Architectural Principle**:
- Supabase/PostgreSQL is the single source of truth.
- `patient_facts` = immutable provenance store (append-only, audit-safe).
- `patient_longitudinal_profiles` = mutable structured snapshot for fast read access.
- When writing new facts, use `copy.deepcopy` and `sqlalchemy.orm.attributes.flag_modified` to ensure SQLAlchemy detects in-place JSONB mutations.

---

## 5. Prescription Workflow

### Medicine Dataset
- Source: `A_Z_medicines_dataset_of_India.csv` (253k+ records, root of repository).
- Ingested into a local SQLite database at `backend/data/medicines.db` at startup by `backend/app/services/medicine_search.py`.
- Search is indexed (FTS5 + prefix index) for sub-millisecond performance.
- **The medicines dataset is the sole authoritative source for prescription medicine data. Do not invent medicine information.**

### Prescription API Endpoints
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/medicines/search?q=...` | Autocomplete search across 253k medicines |
| GET | `/api/v1/medicines/{id}` | Retrieve single medicine details |
| GET | `/api/v1/encounters/{id}/prescriptions` | List prescriptions for an encounter |
| POST | `/api/v1/encounters/{id}/prescriptions` | Create or update a draft prescription |
| POST | `/api/v1/prescriptions/{id}/safety-check` | Run deterministic safety checks |
| POST | `/api/v1/prescriptions/{id}/finalize` | Finalize a prescription (doctor sign-off) |
| POST | `/api/v1/prescriptions/{id}/amend` | Amend a finalized prescription |
| GET | `/api/v1/patients/{id}/prescriptions` | Retrieve prescription history for a patient |

### Deterministic Safety Checks
Safety alerts are **always computed by backend logic**, never by AI. Three alert categories:
1. **ALLERGY** — Cross-checks prescribed medicines against patient's recorded allergies in `patient_longitudinal_profiles`. Includes cross-reaction logic (e.g., penicillin → amoxicillin).
2. **DUPLICATE** — Detects if the same or similar medicine is already in the active medication list.
3. **UNKNOWN_ALLERGY_STATUS** — Warns when allergy status is unknown (unknown ≠ no allergy).

After finalization, medications are written to `patient_facts` (provenance) and `patient_longitudinal_profiles` (current_medications snapshot) via longitudinal sync.

---

## 6. REST API Surface

All routes are registered in `backend/app/main.py`. Base prefix: `/api/v1`.

| Router prefix | Tag | Key routes |
|---|---|---|
| `/api/v1/patients` | Patients | `POST /register`, `GET /{id}` |
| `/api/v1/patients` | Longitudinal Profile | `GET/PUT/PATCH /{id}/longitudinal-profile`, `POST/GET /{id}/facts` |
| `/api/v1/kiosk` | Kiosk | Session management |
| `/api/v1/clinical` | Clinical | `POST /start`, `GET /state`, `POST /answer`, `GET /question/{pathway}/{id}` |
| `/api/v1/documents` | Documents | `POST /upload`, `GET /{id}` |
| `/api/v1/summaries` | Summaries | `POST /generate`, `GET /encounters/{id}/summary`, `POST /{id}/edit`, `POST /{id}/verify`, `POST /{id}/reject` |
| `/api/v1/encounters` | Encounters | `GET /active`, `GET /{id}` |
| `/api/v1/voice` | Voice / ASR | `POST /transcribe` |
| `/api/v1` | Prescriptions | Medicine search + prescription CRUD (see Section 5) |
| `/api/v1/doctalk` | DocTalk | `GET /specialists`, `GET /specialists/find-any`, `POST /requests`, `GET /requests/my-requests`, `GET /requests/my-consultations`, `GET /requests/{id}`, `GET /requests/{id}/context`, `POST /requests/{id}/accept`, `POST /requests/{id}/decline`, `POST /requests/{id}/cancel`, `POST /requests/{id}/start`, `POST /requests/{id}/complete`, `GET/POST /requests/{id}/notes` |
| `/health` | Health | `GET /health` |

CORS is configured to allow `http://localhost:3000` and `http://localhost:3001`.

---

## 7. Frontend Routes

### Patient Kiosk (`frontend/patient-kiosk`, port 3000)
| Route | Description |
|---|---|
| `/` | Welcome / landing page |
| `/consent` | Patient consent page |
| `/registration` | Registration type selection |
| `/registration/new` | New patient registration form |
| `/registration/existing` | Existing patient login with quick demo chips for all 7 cohort patients |
| `/session` | Session dashboard with profile snapshot and intake workflow cards |
| `/profile` | Patient profile with demographics, contact edit modal, clinical summary, and discrepancy reporting |
| `/history` | Complete categorized medical history (conditions, allergies, meds, surgeries, prescriptions) |
| `/documents` | Document upload (drag-and-drop) |
| `/clinical` | Clinical intake intro |
| `/clinical/conversation` | Conversational clinical Q&A with voice input |
| `/summary-preview` | Patient-facing summary preview |

### Doctor Dashboard (`frontend/doctor-dashboard`, port 3001)
| Route | Description |
|---|---|
| `/` | Redirect to `/dashboard` |
| `/login` | Split-screen login page |
| `/dashboard` | Animated stat cards overview |
| `/queue` | Priority-sorted encounter queue |
| `/encounters/[encounterId]` | Encounter workspace (tabs: Summary / History / Documents / Timeline / Prescription) |
| `/patients/[patientId]` | Patient profile with longitudinal data and prescription history |
| `/doctalk` | Dedicated DocTalk specialist hub (incoming requests, pre-acceptance privacy, consultation workspace) |

---

## 8. File Structure

```text
MediKiosk/
├── A_Z_medicines_dataset_of_India.csv       # 253k Indian medicines dataset (do not commit modifications)
├── AGENTS.md                                # This file — primary agent knowledge base
├── README.md                                # Project-level overview
├── MediPlatform_Chatbot_Functional_Specification.md
├── adversarial_audit.py                     # Adversarial testing script
├── ai/                                      # All AI logic
│   ├── asr/                                 # ASR: MockASRProvider + SarvamASRProvider
│   ├── clinical_nlu/                        # Clinical NLU: keyword-based mock ClinicalNLUService
│   ├── medical_extraction/                  # Extraction: interface, mock, gemini, models
│   ├── ocr/                                 # OCR: interface, mock, gemini, paddle
│   ├── question_engine/                     # Adaptive clinical Q&A pathways
│   ├── red_flags/                           # Deterministic red-flag rule engine
│   └── summarization/                       # Summary: interface, mock, gemini, openai, aggregator, validator
├── backend/
│   ├── alembic/                             # Migrations (run: alembic upgrade head)
│   │   └── versions/
│   │       ├── 4f6c80f861c0_create_models.py
│   │       ├── 8a056f6d9ce7_initial_schema.py
│   │       ├── b7e91a2c3d4e_add_longitudinal_profiles_and_facts.py
│   │       └── c3f81e7d9a2b_add_prescription_workflow_fields.py
│   ├── app/
│   │   ├── api/endpoints/                   # clinical, documents, encounters, kiosk, longitudinal,
│   │   │                                    # patients, prescriptions, summaries, voice
│   │   ├── models/models.py                 # All SQLAlchemy models
│   │   ├── schemas/
│   │   │   ├── longitudinal_profile.py      # Pydantic models for 21-domain profile
│   │   │   └── prescription.py              # Pydantic models for prescription workflow
│   │   └── services/
│   │       ├── medicine_search.py           # SQLite-backed medicine search service
│   │       └── storage.py                   # Local file storage for uploaded documents
│   ├── data/                                # Runtime: medicines.db (auto-generated, gitignored)
│   ├── uploads/                             # Runtime: uploaded patient documents (gitignored)
│   ├── tests/                               # pytest test suite (12 test files)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── doctor-dashboard/                    # Next.js 14+, TypeScript, Tailwind, shadcn/ui
│   └── patient-kiosk/                       # Next.js 14+, TypeScript, Tailwind
└── docs/                                    # Architecture and API documentation
```

---

## 9. Current Implementation Status

### ✅ Implemented (verified in repository)

- **FastAPI backend** with full CORS, routing, and health check
- **Supabase PostgreSQL** as primary database via SQLAlchemy
- **Patient registration** (`POST /api/v1/patients/register`)
- **Kiosk session management** (UUID session tokens)
- **Clinical intake Q&A** via adaptive question engine (`ai/question_engine/`) — dynamic dimension tracking (onset, character, severity, location, radiation, associated), priority sorting, automatic skipping of answered dimensions in free-text speech, multi-symptom awareness, robust multilingual symptom routing (English & Hindi/Hinglish), and intelligent general intake routing (eliminating hardcoded fever fallback)
- **Deterministic red-flag detection** (`ai/red_flags/engine.py`) — backend-authoritative, no AI involvement (supports `CARDIAC_EMERGENCY_SUSPECTED`, `THUNDERCLAP_HEADACHE`, `HIGH_GRADE_FEVER`)
- **Document upload** with local file storage (`backend/uploads/`)
- **OCR pipeline** — Gemini Vision provider + PaddleOCR provider + Mock provider
- **Medical extraction pipeline** — Gemini provider + Mock provider; extracts medications, diagnoses, vitals with provenance and confidence scores
- **Anti-hallucination validator** (`ai/summarization/validator.py`) — strips unsupported clinical claims from AI drafts
- **Clinical summarization** — Gemini provider + OpenAI provider + Mock provider
- **Summary verification workflow** — doctor edits and verifies AI draft; verification stored as `SummaryVerification`
- **Longitudinal patient profile** — JSONB snapshot (`patient_longitudinal_profiles`) + provenance fact store (`patient_facts`)
- **Longitudinal profile REST API** — GET/PUT/PATCH profile, POST/GET facts
- **Sarvam ASR** — `POST /api/v1/voice/transcribe`, transcription only, `saaras:v3`
- **Voice input in patient kiosk** — browser `MediaRecorder` → audio blob → Sarvam endpoint → transcript → clinical pathway
- **Prescription workflow** — medicine search, draft save, deterministic safety check, finalize, amend, longitudinal sync
- **Medicine search** — 253k Indian medicines indexed in SQLite, sub-millisecond search
- **Doctor Dashboard** — login, dashboard, encounter queue (priority-sorted by red-flag severity), encounter workspace, patient profile
- **Patient Kiosk** — welcome, consent, registration, document upload, clinical conversation, summary preview
- **shadcn/ui** installed on doctor-dashboard (base-nova style)
- **Multi-hospital schema** — `hospitals` and `users` tables exist
- **Clinical NLU** — Mock provider (keyword-based) + Gemini provider (real AI extraction). Factory `get_nlu_provider()` selects via `NLU_MODE` env var. Both providers output `ExtractedFacts` with provenance. NLU never diagnoses, prescribes, or converts unknown to negative.
- **Conversation → patient_facts pipeline** (`backend/app/services/conversation_fact_pipeline.py`) — wired into `POST /api/v1/clinical/answer`. On each voice/text answer: NLU extraction → validation (confidence threshold, category filtering) → conflict detection → immutable `patient_facts` insertion → longitudinal profile sync. Pipeline errors are logged but never crash the intake flow.
- **Fact reconciliation engine** (`ai/reconciliation/engine.py`) — deterministic conflict detection for allergies, chronic conditions, and medications. Includes Unknown ≠ Negative guard: denying a category with `unknown` status always flags a HIGH conflict for doctor review.
- **Authentication & Hospital-Level Tenant Isolation** — JWT authentication (`/api/v1/auth/login`, `/api/v1/auth/me`), `get_current_user` dependency, hospital-scoped active queue, and strict cross-hospital boundary enforcement across patients, encounters, documents, longitudinal profiles, prescriptions, assessments, and investigations (returns safe 404s).
- **Doctor Clinical Assessment Workflow** (`/api/v1/encounters/{id}/assessment`) — full physician clinical assessment capturing HPI, vitals/physical exam, confirmed allergies, confirmed medications, provisional/confirmed diagnoses, and clinical plan; doctor verification and sign-off automatically synchronizes confirmed diagnoses and allergies into `patient_facts` and `patient_longitudinal_profiles` with immutable audit logging.
- **Investigation Workflow Lifecycle** (`/api/v1/encounters/{id}/investigations`, `/api/v1/investigations/{id}`) — order placement (`ORDERED`), diagnostic results recording with abnormal flags (`COMPLETED`), physician review & acknowledgement (`REVIEWED`), cancellation (`CANCELLED`), encounter/patient-level history, and audit logging.
- **DocTalk Backend Foundation & Cross-Hospital Lifecycle** (`/api/v1/doctalk/requests`) — cross-hospital consultation requests (`DocTalkConsultation`, `DocTalkConsultationNote`), deterministic 3/5/7-minute duration gating, consultation state machine (`REQUESTED` -> `ACCEPTED` -> `IN_PROGRESS` -> `COMPLETED`, `DECLINED`, `CANCELLED`), ephemeral scoped context access boundary, formal note authoring, and audit log integration.
- **DocTalk Cross-Hospital Specialist Discovery** (`/api/v1/doctalk/specialists`, `/api/v1/doctalk/specialists/find-any`) — cross-hospital specialist directory with multi-tier eligibility gating (`is_verified`, `doctalk_enabled`, specialty present, registered hospital), availability filtering (`ONLINE`, `BUSY`, `OFFLINE`), deterministic first-available online matching, strict hospital isolation boundary preservation (safe 404s for cross-hospital records outside DocTalk context), and zero exposure of private contact details.
- **DocTalk Treating Doctor UI** (`frontend/doctor-dashboard/src/components/workspace/DocTalkCard.tsx`, `DocTalkRequestDialog.tsx`) — encounter workspace integration with entry point banner, accessible request modal with specialty picker, gated 3/5/7-minute duration selector, urgency toggle, deterministic "Find Any Online" and cross-hospital specialist directory browser with external hospital indicator, active request state display (`REQUESTED`, `ACCEPTED`, `IN_PROGRESS`, `DECLINED`, `COMPLETED`), duplicate active request prevention, and interactive lifecycle controls.
- **DocTalk Specialist-Side Workflow** (`frontend/doctor-dashboard/src/app/doctalk/page.tsx`, `SpecialistWorkspaceModal.tsx`, `GET /api/v1/doctalk/requests/{id}/context`, `POST /accept`, `POST /decline`, `POST /start`, `POST /notes`, `POST /complete`) — dedicated DocTalk specialist hub with Incoming Requests queue and My Consultations archive; pre-acceptance privacy gating (patient identity suppressed to `None`/masked before acceptance; minimal clinical scope returned); explicit `[Accept]` and `[Decline]` (with structured decline reason); post-acceptance scoped consultation workspace with prominent external hospital badge (`🌐 External Consultation`), synthesized clinical facts (demographics, vitals, chief complaint, allergies, chronic conditions, active meds, red flags, AI summary draft); specialist consultative note authoring (clinical opinion, recommendations, further evaluation, follow-up); deterministic safety guarantee (specialist advises, treating doctor retains ultimate clinical authority; AI never prescribes/diagnoses); and strict tenant boundary enforcement (specialist cannot access other hospital's direct patient/encounter records; safe 404s).
- **DocTalk Secure Consultation Context & Privacy Boundary** (`backend/app/services/doctalk_context_service.py`, `GET /api/v1/doctalk/requests/{id}/context`, `GET /api/v1/doctalk/requests/{id}/documents/{document_id}`) — privacy and tenant boundary between full patient records and external DocTalk specialists. Features: (1) Explicit sharing preferences (treating doctor toggles history, vitals, allergies, meds, conditions, investigations, documents, summary); (2) Demographic minimization (age, gender, city only; zero PII like name, phone, aadhaar); (3) Source traceability for all clinical facts (provenance tracking with `source_type`, `source_id`, `verified` flag); (4) Deterministic clinical safety (UNKNOWN never converted to negative; zero AI-generated diagnoses or prescriptions); (5) Temporary access lifecycle enforcement (specialist active access is automatically revoked with `403 Forbidden` upon cancellation, decline, completion, or `access_expires_at` timeout, while audit history is permanently retained); (6) Scoped document streaming endpoint (`/requests/{id}/documents/{document_id}`) verifying caller authority, active consultation status, and explicit access scope inclusion; (7) Complete isolation assurance: external specialists cannot access Hospital A patients (`/patients/{id}`), encounters (`/encounters/{id}`), direct documents (`/documents/{id}`), or unrelated hospital files (returns safe 404s).
- **DocTalk Secure Real-Time Doctor-to-Doctor Consultation** (`backend/app/services/doctalk_session_manager.py`, `POST /api/v1/doctalk/requests/{id}/room-token`, `WS /api/v1/doctalk/ws/{consultation_id}`, `POST /requests/{id}/start`, `POST /requests/{id}/complete`, `DocTalkRoomModal.tsx`) — secure 3/5/7-minute peer-to-peer real-time consultation connecting treating physician and assigned specialist. Features: (1) Authenticated room security (non-predictable consultation UUIDs, signed short-lived room tokens, strictly 2 authorized doctors per room); (2) Zero media storage / recording (P2P WebRTC encrypted media streams attached to ephemeral HTML5 video elements, zero audio/video server recording for privacy); (3) Server-authoritative countdown timer (ticks server-side with 10s ping sync, visual amber warning under 60s and pulsing red under 15s, auto-completion on expiry); (4) Micro-controls (microphone mute/unmute, camera on/off, split-view clinical context drawer, companion clinical notes & chat, and explicit End Consultation action); (5) Resilience and graceful degradation (camera/mic permission denied banner with automatic fallback to companion audio/text mode, reconnecting state on network drop, peer-left alerts); (6) Seamless post-consultation workflow transition (immediate redirect for specialist to author formal opinion and recommendations, instant update for treating doctor to review opinion).
- **DocTalk Specialist Opinion & Encounter Timeline Integration** (`backend/app/models/models.py`, `backend/alembic/versions/e6f7a8b9c0d1_add_encounter_id_to_doctalk_notes.py`, `backend/app/api/endpoints/doctalk.py`, `backend/app/api/endpoints/documents.py`, `backend/app/api/endpoints/encounters.py`, `frontend/doctor-dashboard/src/components/workspace/DocTalkCard.tsx`, `frontend/doctor-dashboard/src/components/workspace/ClinicalTimeline.tsx`) — integration of cross-hospital specialist consultation into the encounter timeline. Features: (1) Specialist formal opinion persistence capturing clinical opinion, recommendations, further evaluation, follow-up, consultation ID, encounter ID, specialist and specialist hospital attribution, and timestamps; (2) Treating doctor view (`DocTalkCard.tsx`) in encounter workspace (`/encounters/[encounterId]`) displaying `🩺 Specialist Consultation` card with specialist name, hospital, specialty, consultation time, clinical opinion, recommendations, further evaluation, follow-up, and clinical safety attribution banner; (3) Encounter timeline milestones displaying the 5 consultation milestones in exact chronological order: `09:42 🩺 DocTalk requested`, `09:44 ✓ Specialist accepted`, `09:45 🟢 Consultation started`, `09:51 ✓ Consultation completed`, and `09:52 📄 Specialist opinion added`; (4) Strict clinical data safety: DocTalk specialist opinions are advisory and NEVER overwrite or mutate patient facts, diagnoses, prescriptions, investigation orders, or AI clinical summaries (treating doctor retains sole clinical decision-making authority); (5) Comprehensive audit trail capturing requester, requesting hospital, specialist, specialist hospital, patient, encounter, timestamps, and action types; (6) Verified by 5 automated tests (`tests/test_specialist_opinion_timeline.py`) asserting persistence, timeline milestones, audit trail, and zero clinical data overwrite.
- **Patient Profile & Complete Medical History Section** (`frontend/patient-kiosk/src/app/profile/page.tsx`, `frontend/patient-kiosk/src/app/history/page.tsx`, `backend/app/api/endpoints/kiosk.py`, `backend/seed_patients.py`) — complete patient personal health management and clinical background portal in the Patient Kiosk. Features: (1) Session-authenticated security dependency (`get_kiosk_session_and_patient`) verifying `X-Session-Token` or Bearer authorization header, deriving patient identity strictly from the active kiosk session (patients cannot access or tamper with arbitrary patient IDs); (2) Profile dashboard (`/profile`) presenting personal demographics (name, gender, age, DOB, blood group, address, mobile, email, emergency contact), clinical summary (chronic diagnoses, allergies, current medications, surgeries), recent hospital encounters, and active prescriptions; (3) Safe contact update modal (`PUT /api/v1/kiosk/profile`) allowing patients to update contact/address/emergency info while protecting verified medical facts; (4) Clinical discrepancy reporting modal (`POST /api/v1/kiosk/profile/report-change`) creating unverified, audit-safe facts (`pending_doctor_review`) so doctors review patient-reported changes without unverified facts overwriting doctor verified records; (5) Categorized Complete Medical History page (`/history`) organizing diagnoses, active medications, allergies with severity ratings, surgeries/hospitalizations, family history, lifestyle background, and past prescriptions; (6) Unknown ≠ Negative clinical integrity guarantee (gracefully displaying "No information recorded" rather than false negatives); (7) Expanded 7-patient diverse Indian demo cohort (`backend/seed_patients.py`) covering Raj Kumar (T2DM, HTN), Anita Desai (RA, Sulfa allergy), Mohan Lal Verma (COPD, CAD, Aspirin allergy), Priya Swaminathan (Hypothyroidism, Asthma, Peanut allergy), Arjun Patel (CKD 3a, Contrast allergy), Sunita Roy (Hep B, GERD, Cipro allergy), and Harpreet Singh (T2DM, Gout, Allopurinol allergy), with 1-click quick-fill selection chips on `/registration/existing`.

### ⚠️ Partially Implemented

- **FHIR resource storage** — `fhir_resources` table exists; no FHIR serialization/deserialization logic is implemented; no ABDM integration.
- **Consent management** — `consents` table and kiosk consent UI page exist; no consent enforcement logic at the API layer.
- **Audit logging** — `audit_logs` table exists; wired into prescriptions, assessments, and investigations; full coverage across all minor reads is pending.

### 🔮 Planned / Future (not yet implemented)

- **Full bidirectional voice conversation loop** — Sarvam ASR converts speech to text; TTS (text-to-speech) to read questions aloud is not implemented.
- **FHIR/ABDM compliance** — Converting verified summaries into standard FHIR bundles for Ayushman Bharat Digital Mission interoperability.
- **Production security hardening** — KMS encryption at rest, WAF, production IAM policies, per-hospital API key management.

---

## 10. Clinical Safety Rules (Non-Negotiable)

> [!CAUTION]
> These rules must NEVER be weakened, bypassed, or removed by any agent or developer.

1. **Red-flag detection is always deterministic**. AI must never generate, modify, suppress, or classify red flags. Red-flag logic lives exclusively in `ai/red_flags/engine.py`.
2. **AI must not diagnose patients**. AI may summarize reported symptoms; it must not name a diagnosis as certain.
3. **AI must not prescribe medication**. Only the doctor may finalize a prescription. AI may suggest based on dataset data only if explicitly requested, but the doctor is the sole authority.
4. **AI must not invent patient history**. The anti-hallucination validator (`ai/summarization/validator.py`) enforces this for summaries. Do not weaken it.
5. **Unknown ≠ No**. If the patient has not stated they have no allergy, the system must treat allergy status as unknown, not absent. This is enforced in safety checks and must be preserved.
6. **Verified medical information must not be silently overwritten**. Conflicting patient statements must be explicitly flagged.
7. **Clinical summaries require doctor verification**. An AI draft is never the final clinical record. The doctor must explicitly verify or reject it.
8. **Patient data must not leak across patients or hospitals**.
9. **The doctor is the final clinical decision-maker in all workflows**.

---

## 11. Do Not Misrepresent the Architecture

> [!WARNING]
> The following misrepresentations are common errors to avoid:

- **Do not** describe Sarvam ASR as a full conversational voice assistant. It is transcription-only.
- **Do not** describe Gemini as removed from the project. Gemini OCR, extraction, summarization, and NLU providers exist and remain active alongside Sarvam ASR.
- **Do not** describe FHIR/ABDM compliance as implemented. The table exists; no real FHIR logic exists.
- **Do not** describe hospital-level access control as unverified. It is enforced across all patient/clinical endpoints via `verify_encounter_access`, `verify_patient_access`, and `verify_document_access`, backed by automated tests.
- **Do not** describe `ClinicalNLUService` as a diagnosis engine. It extracts factual entities only; it never diagnoses, prescribes, or converts unknown to negative.
- **Do not** claim features are implemented based solely on README text. Verify against the code.
- **Do not** describe doctor verification as automatic. It requires explicit doctor action.
- **Do not** claim AI-generated information is clinically verified unless a `SummaryVerification` record with `DOCTOR_VERIFIED` status exists.

---

## 12. Hard Constraints for Agents

> [!IMPORTANT]
> These constraints apply to all agents and developers working on this repository.

1. **Python version**: Do NOT downgrade from Python 3.14.7. Do NOT attempt to install Python 3.10 or any older version.
2. **No Docker**: Do NOT containerize the backend with Docker. Do NOT redesign the monolith into microservices.
3. **No real patient data**: Never commit real patient records, PHI, or medical documents.
4. **No credentials**: Never commit `.env` files, API keys, or secrets. `backend/uploads/` and `backend/data/` are gitignored.
5. **Provider interfaces are mandatory**: Always maintain `OCRProvider`, `ExtractionProvider`, `SummaryProvider`, `ASRProvider` interfaces. Both Mock and Real providers must remain intact.
6. **Mock providers are mandatory**: Required for local development when API quotas are exhausted or internet is down.
7. **Do not weaken the validator**: The `AntiHallucinationValidator` must not be bypassed or softened.
8. **Red-flag logic stays deterministic**: Do not replace or supplement `RedFlagEngine` with AI-generated alerts.
9. **Test after backend changes**: Always run `python -m pytest backend/ -v` before considering backend changes complete.
10. **Update AGENTS.md**: After completing a significant implementation task, update the "Recent Changes" section and revise any affected sections of this file.

---

## 13. Environment Variables Reference

| Variable | Description | Values |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string to Supabase PostgreSQL | `postgresql://...` |
| `OCR_MODE` | OCR provider selection | `mock` (default), `gemini` / `real`, `paddle` |
| `NLU_MODE` | Clinical NLU provider selection | `mock` (default), `gemini` |
| `NLU_MODE` | Clinical NLU provider selection | `mock` (default), `gemini` |
| `EXTRACTION_MODE` | Medical extraction provider selection | `mock` (default), `gemini` / `real` |
| `AI_MODE` | Summarization mode | `mock` (default), `real` |
| `LLM_PROVIDER` | LLM for summarization (when `AI_MODE=real`) | `gemini`, `openai` |
| `ASR_MODE` | ASR provider selection | `mock` (default), `sarvam` |
| `SARVAM_API_KEY` | API key for Sarvam AI speech-to-text | — |
| `GEMINI_API_KEY` | API key for Google Gemini (OCR, extraction, summarization) | — |
| `OPENAI_API_KEY` | API key for OpenAI (summarization only) | — |
| `NEXT_PUBLIC_API_URL` | FastAPI base URL (both frontends) | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL (frontend) | — |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key (frontend) | — |

---

## 14. Common Tasks

### Run backend tests
```powershell
cd backend
.venv\Scripts\activate
python -m pytest backend/ -v
```

### Run a specific test file
```powershell
python -m pytest backend/tests/test_prescriptions.py -v
```

### Run frontends
```powershell
# Terminal 1 — Patient Kiosk
cd frontend/patient-kiosk && npm run dev

# Terminal 2 — Doctor Dashboard
cd frontend/doctor-dashboard && npm run dev
```

### Apply database migrations
```powershell
cd backend
.venv\Scripts\activate
alembic upgrade head
```

### Switch providers via `.env` (no code change required)
```dotenv
# Use Sarvam for voice, Gemini for OCR+extraction+summary
ASR_MODE=sarvam
SARVAM_API_KEY=your_key_here
OCR_MODE=gemini
EXTRACTION_MODE=gemini
AI_MODE=real
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here

# Full mock mode (no external API calls)
ASR_MODE=mock
OCR_MODE=mock
EXTRACTION_MODE=mock
AI_MODE=mock
```

### Free Tier API quota exhausted (Gemini 429 RESOURCE_EXHAUSTED)
Switch to mock mode in `.env`:
```dotenv
AI_MODE=mock
OCR_MODE=mock
EXTRACTION_MODE=mock
```
Quotas reset at midnight Pacific Time. Do not modify provider code to work around quota limits.

---

## 15. Recent Changes

*Reverse-chronological log of significant changes:*

- **2026-09-20** — Implemented DocTalk Phase 9: Specialist Opinion & Encounter Timeline Integration. Added `encounter_id` to `doctalk_consultation_notes` model + Alembic migration `e6f7a8b9c0d1`. Integrated 5 chronologically ordered milestones into the timeline (`DOCTALK_REQUESTED`, `DOCTALK_ACCEPTED`, `DOCTALK_STARTED`, `DOCTALK_COMPLETED`, `DOCTALK_OPINION`). Implemented dedicated treating doctor view (`DocTalkCard.tsx`) showing specialist, hospital, specialty, time, opinion, recommendations, further evaluation, follow-up, and clinical safety attribution banner. Enforced strict data immutability guarantee: DocTalk specialist opinions are advisory and NEVER overwrite existing patient facts, diagnoses, prescriptions, investigation orders, or AI clinical summaries. Enriched comprehensive audit logs across all consultation transitions. Full test suite passing in `tests/test_specialist_opinion_timeline.py` (5/5 tests).
- **2026-09-20** — Implemented DocTalk Phase 8: Secure Real-Time Doctor-to-Doctor Consultation. Built native WebSocket signaling layer (`DocTalkConnectionManager`), signed short-lived room tokens, 3/5/7-minute server-authoritative countdown timer with auto-completion on expiry, P2P WebRTC zero-media-recording controls (camera, mic, companion chat & split-view clinical context drawer), hardware denial fallback to audio/text mode, and direct post-consultation workflow transition. Full test suite passing in `tests/test_realtime_consultation.py` (12/12 tests).
- **2026-09-15** — Full audit and rewrite of `AGENTS.md` to match verified current repository state. Corrected Sarvam AI description (transcription-only, not a voice chatbot). Corrected Gemini description (still active for OCR, extraction, summarization). Added prescription workflow documentation. Added implementation status table (implemented/partial/planned). Resolved all stale/contradictory statements.
- **2026-09-15** — Implemented full Doctor Prescription Workflow: 253k medicines indexed in SQLite (`medicine_search.py`), `prescriptions` + `prescription_items` schema + Alembic migration `c3f81e7d9a2b`, full REST API (`prescriptions.py`), deterministic safety checks (allergy/duplicate/unknown-status), longitudinal sync on finalization. Frontend: `PrescriptionWorkspace.tsx`, `prescriptions.ts` API client, Prescription tab in encounter workspace.
- **2026-09-15** — Completed full UI/UX redesign of both frontends (shadcn base-nova, Inter font, dark mode, animated components). Doctor Dashboard: sidebar, stat cards, queue, encounter workspace with tabs, red-flag panel. Patient Kiosk: animated hero, glassmorphic trust badges, floating-label inputs, drag-and-drop documents, voice conversation UI.
- **2026-09-15** — Integrated Sarvam AI Saaras v3 ASR: `SarvamASRProvider` in `ai/asr/provider.py`, `POST /api/v1/voice/transcribe` endpoint, browser `MediaRecorder` → Sarvam pipeline in clinical conversation page, language detection badge, live transcript editing. Test suite `test_voice.py` added.
- **2026-09-15** — Implemented Patient Medical History Longitudinal Profile (v1.0): `PatientLongitudinalProfile` + `PatientFact` SQLAlchemy models, Alembic migration `b7e91a2c3d4e`, 21-domain Pydantic schema in `longitudinal_profile.py`, REST API in `longitudinal.py`, test suite `test_longitudinal_profile.py`.
- **2026-09-15** — Added Real Clinical NLU provider (Gemini) and factory with `NLU_MODE`.
- **2026-09-15** — Implemented Conversation → Patient Facts pipeline and deterministic Fact Reconciliation Engine.
- **Earlier sessions** — Initial project setup, Supabase configuration, FastAPI CORS middleware, patient registration verified against Supabase PostgreSQL, all three servers running (FastAPI :8000, Kiosk :3000, Dashboard :3001).


