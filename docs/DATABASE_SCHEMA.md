# Database Schema

## Tables Overview

1.  **hospitals**: (id, name, created_at, updated_at). PK: id (UUID).
2.  **users**: (id, hospital_id, role, username, password_hash, ...). PK: id (UUID), FK: hospital_id.
3.  **patients**: (id, hospital_id, demographic_data(JSONB), created_at). PK: id (UUID), FK: hospital_id.
4.  **encounters**: (id, patient_id, status, start_time, end_time). PK: id (UUID), FK: patient_id.
5.  **clinical_histories**: (id, encounter_id, ayush_data(JSONB), history_data(JSONB)). PK: id, FK: encounter_id.
6.  **symptoms**: (id, encounter_id, symptom_name, details(JSONB)). PK: id, FK: encounter_id.
7.  **observations**: (id, encounter_id, category, value(JSONB)). PK: id, FK: encounter_id.
8.  **documents**: (id, encounter_id, file_path, doc_type, status). PK: id, FK: encounter_id.
9.  **document_ocr**: (id, document_id, raw_text, engine_used). PK: id, FK: document_id.
10. **document_entities**: (id, document_id, entity_type, value, confidence). PK: id, FK: document_id.
11. **medications**: (id, patient_id, name, dosage, status). PK: id, FK: patient_id.
12. **clinical_summaries**: (id, encounter_id, draft_content(JSONB), model_info, created_at). PK: id, FK: encounter_id.
13. **summary_verifications**: (id, summary_id, doctor_id, final_content(JSONB), status, verified_at). PK: id, FK: summary_id, FK: doctor_id.
14. **red_flags**: (id, encounter_id, rule_name, input_evidence(JSONB), severity, status). PK: id, FK: encounter_id.
15. **prescriptions**: (id, encounter_id, doctor_id, created_at). PK: id, FK: encounter_id, FK: doctor_id.
16. **prescription_items**: (id, prescription_id, medication_name, instructions). PK: id, FK: prescription_id.
17. **consents**: (id, patient_id, type, granted_at). PK: id, FK: patient_id.
18. **audit_logs**: (id, user_id, action, target_resource, details(JSONB), timestamp). PK: id, FK: user_id.
19. **kiosk_sessions**: (id, session_token, data(JSONB), expires_at). PK: id.
20. **fhir_resources**: (id, resource_type, internal_id, fhir_data(JSONB)). PK: id.

## Key Design Principles
- **UUIDs** are used as Primary Keys across all tables for scalability and security.
- **JSONB** is utilized selectively for flexible data schemas: AYUSH fields, clinical outputs, FHIR representation, and kiosk transient data.
- **Strict Foreign Keys** ensure data integrity linking everything to Hospitals, Patients, and Encounters.
