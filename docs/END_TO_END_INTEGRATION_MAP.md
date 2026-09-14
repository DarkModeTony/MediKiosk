# End-to-End Integration Map

This document defines the deterministic ID and data mapping required to simulate the complete Phase 4 ➔ Phase 7 MediPlatform clinical workflow in Mock Mode (while PostgreSQL is offline).

## 1. Frontend Applications
- **Patient Kiosk** (Next.js): `frontend/patient-kiosk`
- **Doctor Dashboard** (Next.js): `frontend/doctor-dashboard`

## 2. Shared Canonical Identities

To create the illusion of a single connected flow without a real database, both frontends use the following hardcoded canonical identities.

### Raj Kumar (Primary Demo Flow)
- **Patient ID**: `pat_raj_123`
- **Session Token**: `mock-session-raj-123`
- **Encounter ID**: `enc_raj_001`
- **Summary ID**: `sum_raj_999`
- **Document IDs**: `doc_raj_01` (Prescription), `doc_raj_02` (Lab Report)

### Data Flow Mapping
1. **Kiosk Registration** 
   - Route: `/api/v1/patients/register` 
   - Mock Returns: `pat_raj_123`
2. **Kiosk Session Creation**
   - Route: `/api/v1/kiosk/session`
   - Mock Returns: `mock-session-raj-123`
3. **Clinical Intake (Start/Answer)**
   - Route: `/api/v1/clinical/start` & `/api/v1/clinical/answer`
   - Mock Returns: ClinicalState bound to `enc_raj_001` with pre-defined facts (Chest pain, etc.) and Red Flag (`CHEST_PAIN_SUDDEN_ONSET`).
4. **Document Upload**
   - Route: `/api/v1/documents/upload`
   - Mock Returns: Document Entities for `doc_raj_01` or `doc_raj_02`.
5. **Doctor Dashboard Queue**
   - Route: `/api/v1/queue`
   - Mock List contains: `pat_raj_123` linked to `enc_raj_001` with `HIGH` priority.
6. **Doctor Dashboard Workspace**
   - Red Flags pulled directly from `enc_raj_001`.
   - Summary ID `sum_raj_999` generated and mapped to `enc_raj_001`.

## 3. Authoritative Rules
- The **Red Flag** is inherently tied to the backend Encounter/Clinical State. The frontend UI does not compute flags.
- **Summary Versioning** (`AI_DRAFT` ➔ `DOCTOR_EDITED` ➔ `DOCTOR_VERIFIED`) modifies the state of `sum_raj_999` without destroying the `original_draft`.
- Navigating between Raj Kumar and any other mock patient safely segregates states due to explicit ID lookups (`MOCK_ENCOUNTERS[patient_id]`).
