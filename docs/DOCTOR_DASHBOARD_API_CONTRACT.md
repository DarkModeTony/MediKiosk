# DOCTOR DASHBOARD API CONTRACT

This document specifies the exact FastAPI backend endpoints the Phase 7 Doctor Dashboard will consume, to strictly enforce the "AI Assists. Doctor Decides." philosophy without duplicating clinical reasoning in the frontend.

## 1. Patients & Encounters
*These minimal endpoints were added in Phase 7 to support header metadata.*

### GET `/api/v1/patients/{patient_id}`
- **Method**: GET
- **Params**: `patient_id` (str)
- **Response**:
  ```json
  {
    "id": "uuid",
    "name": "string",
    "age": 68,
    "gender": "string",
    "created_at": "datetime"
  }
  ```
- **Errors**: 404 Patient not found.

### GET `/api/v1/encounters/{encounter_id}`
- **Method**: GET
- **Params**: `encounter_id` (str)
- **Response**:
  ```json
  {
    "id": "uuid",
    "patient_id": "uuid",
    "status": "string",
    "priority": "HIGH|MEDIUM|NORMAL",
    "chief_complaint": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
  ```
- **Errors**: 404 Encounter not found.

## 2. Clinical History (Phase 4)

### GET `/api/v1/clinical/state`
- **Method**: GET
- **Params**: `session_token` (str) OR `encounter_id` (str, modified to allow encounter_id directly for Doctor Dashboard).
- **Response**: `ClinicalState`
  ```json
  {
    "status": "IN_PROGRESS|COMPLETED",
    "encounter_id": "uuid",
    "facts": {
        "CHEST_PAIN": {"state": "COLLECTED", "value": "true"},
        "ONSET": {"state": "COLLECTED", "value": "Today morning"}
    }
  }
  ```

## 3. Documents & Extraction (Phase 5)

### GET `/api/v1/documents/patients/{patient_id}/timeline`
- **Method**: GET
- **Params**: `patient_id` (str)
- **Response**:
  ```json
  {
    "patient_id": "uuid",
    "events": [
      {
        "date": "2025-01-01T00:00:00",
        "date_known": true,
        "type": "DOCUMENT",
        "document_id": "uuid",
        "document_type": "string",
        "entities": [{"type": "MEDICATION", "value": {"name": "Amlodipine"}, "status": "AI_EXTRACTED"}]
      }
    ]
  }
  ```

### GET `/api/v1/documents/{document_id}`
- **Method**: GET
- **Params**: `document_id` (str)
- **Response**: Document metadata (type, status, date).

### GET `/api/v1/documents/{document_id}/entities`
- **Method**: GET
- **Params**: `document_id` (str)
- **Response**: Array of extracted entities with `source_text`, `confidence`, and `status`.

### POST `/api/v1/documents/{document_id}/confirm`
- **Method**: POST
- **Params**: `document_id` (str)
- **Body**: 
  ```json
  {
    "entities": [
      {"entity_id": "uuid", "corrected_value": {}, "status": "PATIENT_CORRECTED"}
    ]
  }
  ```

## 4. AI Clinical Summary (Phase 6)

### GET `/api/v1/summaries/encounters/{encounter_id}/summary`
- **Method**: GET
- **Params**: `encounter_id` (str)
- **Response**:
  ```json
  {
    "summary_id": "uuid",
    "latest_version": {"structured_sections": []},
    "status": "AI_DRAFT|DOCTOR_EDITED|DOCTOR_VERIFIED",
    "original_draft": {}
  }
  ```

### POST `/api/v1/summaries/{summary_id}/edit`
- **Method**: POST
- **Params**: `summary_id` (str)
- **Body**: `{"content": {}}`
- **Response**: `{"status": "success"}`

### POST `/api/v1/summaries/{summary_id}/verify`
- **Method**: POST
- **Params**: `summary_id` (str)
- **Response**: `{"status": "success"}`

### POST `/api/v1/summaries/{summary_id}/reject`
- **Method**: POST
- **Params**: `summary_id` (str)
- **Response**: `{"status": "success"}`
