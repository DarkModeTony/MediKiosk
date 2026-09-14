# API Contracts

## 1. Authentication & Users
- `POST /api/v1/auth/login`
  - Req: `{ username, password }`
  - Res: `{ access_token, token_type, role, hospital_id }`

## 2. Patient & Kiosk
- `POST /api/v1/kiosk/session` (Start a session)
  - Res: `{ session_token, expires_at }`
- `POST /api/v1/patients/register`
  - Req: `{ demographic_data, consent }`
  - Res: `{ patient_id }`
- `GET /api/v1/patients/{id}`

## 3. Encounter & History
- `POST /api/v1/encounters`
  - Req: `{ patient_id }`
  - Res: `{ encounter_id }`
- `POST /api/v1/encounters/{id}/symptoms`
  - Req: `{ symptom_name, details }`
- `POST /api/v1/encounters/{id}/history`
  - Req: `{ history_data, ayush_data }`

## 4. Documents & OCR
- `POST /api/v1/documents/upload`
  - Req: `multipart/form-data (file)`
  - Res: `{ document_id }`
- `GET /api/v1/documents/{id}/status`

## 5. AI Summary & Verification
- `POST /api/v1/summaries/generate`
  - Req: `{ encounter_id }`
  - Res: `{ summary_id, draft_content, red_flags }`
- `POST /api/v1/summaries/{id}/verify`
  - Req: `{ doctor_id, final_content, status (accepted/rejected) }`

## 6. FHIR Export
- `GET /api/v1/fhir/Patient/{id}`
- `GET /api/v1/fhir/Encounter/{id}`
