# Phase 10: Complete System Audit

## 1. Patient Kiosk → Backend Flow
**Status: INCOMPLETE (MOCK DEPENDENT)**
- The frontend attempts to call `POST /api/v1/patients/register` and `POST /api/v1/kiosk/session` when `NEXT_PUBLIC_DATA_MODE=api` is set.
- **Gap:** These endpoints **do not exist** in the FastAPI backend (`backend/app/api/endpoints/patients.py` only has `GET /{patient_id}`, and `kiosk.py` only has `GET /`).
- **Result:** The frontend `fetchApi` fails and falls back to hardcoded mock data (`pat_raj_123` and `mock-session-raj-123`), bypassing actual PostgreSQL persistence for patient creation.

## 2. Clinical Intake Flow
**Status: PARTIALLY COMPLETE**
- The frontend correctly calls `POST /api/v1/clinical/start` and `POST /api/v1/clinical/answer`.
- **Gap:** It uses the mock session token `mock-session-raj-123`. The backend's `start_clinical_intake` checks `db.query(KioskSession).filter(KioskSession.session_token == session_token).first()`. 
- **Result:** Since the session was never actually created in PostgreSQL (due to the missing `POST /kiosk/session`), `start_clinical_intake` will throw `404 Session not found`. Real clinical intake cannot proceed without the session endpoint.

## 3. Document Flow
**Status: FUNCTIONAL**
- The Kiosk calls `POST /api/v1/documents/upload` which expects a `multipart/form-data` file and `session_token`.
- **Gap:** Again, it relies on a valid `session_token` existing in the database.

## 4. OCR Flow
**Status: FUNCTIONAL (PHASE 9B)**
- `POST /api/v1/documents/{document_id}/ocr` properly triggers GeminiOCRProvider.

## 5. Medical Extraction Flow
**Status: FUNCTIONAL (PHASE 9C)**
- `POST /api/v1/documents/{document_id}/entities` properly triggers GeminiExtractionProvider and evidence validation.

## 6. Summary Flow
**Status: FUNCTIONAL**
- `POST /api/v1/summaries/generate` is implemented and integrates with `ai/summarization/service.py`.

## 7. Doctor Dashboard Flow
**Status: INCOMPLETE**
- The doctor dashboard uses `getQueue()` in `queue.ts` which has NO real API implementation. It explicitly returns `[]` if `IS_MOCK=false`.
- **Gap:** Need a `GET /api/v1/encounters/active` or similar endpoint for the queue, and `queue.ts` needs to call it.
- **Gap:** `encounters.ts`, `patients.ts`, `documents.ts` in doctor-dashboard have fetchClient calls, but we need to ensure the backend actually returns all the data required for the Encounter Workspace (demographics, history, red flags, entities, summaries).

## 8. Supabase Persistence Flow
**Status: PARTIALLY COMPLETE**
- Alembic migrations and schemas are defined and robust.
- Database writing is functional for Documents, Entities, and Summaries.
- **Gap:** We cannot write KioskSessions, Patients, or initial Encounters because the endpoints are missing.

## 9. Existing Gaps
- **Missing APIs**: `POST /patients/register`, `POST /kiosk/session`, `GET /encounters/active` (or similar).
- **Hardcoded Mocks**: Frontend clients silently swallow API errors and return mock data, masking backend failures.

## 10. Broken/Incomplete Links
- `getQueue()` in `frontend/doctor-dashboard/src/lib/api/queue.ts`
- Missing `POST` routes in `backend/app/api/endpoints/patients.py` and `kiosk.py`.

## 11. Duplicate/Mock-Only Sections
- The UI handles mock fallback elegantly, but for a true E2E pipeline, we need to enforce `NEXT_PUBLIC_DATA_MODE=api` and *remove* or *bypass* the mock fallbacks during the E2E script.

## 12. Recommended Fixes
1. **Implement Missing Endpoints**: Add `POST /patients/register`, `POST /kiosk/session`, and `GET /encounters/active`.
2. **Update Frontend API Clients**: Ensure that when `NEXT_PUBLIC_DATA_MODE=api`, the clients do *not* catch `fetchApi` errors and return mock data. They should throw so the UI handles the real error.
3. **Canonical E2E Script**: Create `backend/smoke_test_full_e2e.py` to hit these exact endpoints linearly, asserting real database persistence at each step.
4. **Fix Provenance**: Ensure the Doctor Dashboard UI can display the `source_text`, `page_number`, and `confidence` retrieved from the backend `GET /api/v1/documents/{id}/entities`.
5. **Enforce Isolation**: Add explicit assertions in the E2E test that a new session token cannot access the previous encounter.
