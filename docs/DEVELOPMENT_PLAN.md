# Development Plan

## Phase 1: Architecture & Documentation (Current)
- Document the system architecture, boundaries, schemas, and API contracts.
- Map reference repositories to system modules.

## Phase 2: Database & Backend Foundation
- Initialize monorepo.
- Configure PostgreSQL via docker-compose.
- Set up FastAPI with basic health checks.
- Configure SQLAlchemy and Alembic.
- Create all 20 database tables and initial migrations.
- Establish `ai/` and `fhir/` directory structures.

## Phase 3: Patient Kiosk Foundation
- Setup Next.js application (`frontend/patient-kiosk`).
- Implement basic layout, Tailwind CSS, shadcn/ui.
- Implement patient registration and consent UI.

## Phase 4: Clinical Conversation Workflow
- Setup Adaptive Question Engine (`ai/question_engine`).
- Define clinical pathways for Fever, Chest Pain, etc.
- Integrate NLP mapping for patient responses.

## Phase 5: ASR Integration
- Implement `ai/asr` module.
- Integrate IndicConformer for Hindi/English voice input.
- Connect kiosk microphone to backend ASR service.

## Phase 6: OCR & Medical Extraction
- Implement `ai/ocr` using PaddleOCR.
- Setup async document processing pipeline.
- Implement medical entity extraction.

## Phase 7: AI Summarization
- Implement `ai/summarization`.
- Combine structured facts and extracted entities into Draft Summaries.

## Phase 8: Red Flags
- Implement `ai/red_flags` rule engine based on deterministic rules.
- Integrate real-time checking during patient intake.

## Phase 9: Doctor Dashboard
- Setup Next.js application (`frontend/doctor-dashboard`).
- Implement patient queues, timelines, and document viewers.

## Phase 10: Doctor Verification & Prescriptions
- Implement UI and APIs for doctors to edit/verify AI summaries.
- Implement prescription creation flow.

## Phase 11: FHIR Integration
- Map internal PostgreSQL schema to FHIR resources using `fhir.resources`.
- Expose FHIR endpoints.

## Phase 12: Security, Audit, and Consent
- Finalize JWT RBAC.
- Ensure audit logs cover all required actions.
- Implement session cleanup.

## Phase 13: Full End-to-End Integration
- Connect all modules for the final MVP workflow.
- Testing and synthetic data generation (Synthea).
