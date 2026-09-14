# Architecture Documentation

## 1. System Overview
MediPlatform is a modular monolith designed for high-volume clinical environments. It separates patient data ingestion, AI-driven extraction/summarization, and doctor verification.

## 2. Component Architecture
- **Frontend (Next.js)**: Split into two apps: `patient-kiosk` and `doctor-dashboard`.
- **Backend (FastAPI)**: Modular monolith handling APIs, database interactions, and orchestrating AI components.
- **AI Modules**: Abstracted behind interfaces to allow swapping models.
- **Database (PostgreSQL)**: Primary storage with JSONB fields for flexible data (FHIR, AYUSH).

## 3. Workflow Architectures

### Patient Kiosk Flow
1. Patient selects language and gives consent.
2. Provides history via Voice/Touch.
3. System translates voice (ASR via IndicConformer) into text.
4. Adaptive Question Engine dynamically queries patient.
5. Patient uploads documents.
6. OCR & Extraction run asynchronously.

### Doctor Workflow
1. Doctor logs into dashboard.
2. Reviews extracted clinical history, timeline, and AI summary.
3. Edits and verifies the AI summary.
4. Generates a prescription.
5. Verification finalizes the clinical record.

### Document Processing Flow (Pipeline)
`File -> OCR (PaddleOCR) -> Raw Text -> Medical Entity Extraction -> Validation -> Structured Entities (Timeline)`

### AI Processing Flow
- **Question Engine**: Follows clinical pathways deterministically, uses LLM for NLP mapping.
- **Red Flags**: Deterministic rule engine.
- **Summarization**: Takes structured facts + extracted entities -> Draft Summary -> Doctor Review.

### FHIR Architecture
`Internal DB -> FHIR Mapper (fhir.resources) -> FHIR Resource -> Export/ABDM`

## 4. Security Boundaries
- Strict RBAC using JWT.
- Hospital-level data isolation.
- Consent tracking and temporary kiosk-session deletion.
- No authoritative AI diagnosis (Human-in-the-loop required).
