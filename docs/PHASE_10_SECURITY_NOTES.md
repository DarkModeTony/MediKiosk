# Phase 10 Security Notes

This document separates current MVP safeguards from required production security measures.

## 1. CURRENT MVP SAFEGUARDS

### A. CORS Configuration
The backend currently enforces restrictive Cross-Origin Resource Sharing (CORS) policies. Only predefined frontend origins (such as `http://localhost:3000` and `http://localhost:3001`) are permitted to make API requests, limiting the surface area for Cross-Site Request Forgery (CSRF).

### B. Patient and Encounter Isolation (API Layer)
The endpoints use UUIDs and properly scope queries by `patient_id` or `encounter_id`. The Phase 10 smoke test explicitly verified that a newly registered patient (Session B) cannot retrieve the active clinical state of an unrelated patient (Session A). This verifies isolation at the data association level for MVP.

### C. Safe Document Processing
Uploaded documents are processed synchronously and stored via Supabase, avoiding arbitrary file execution risks on the backend host.

### D. Hardened Prompt Pipelines
The Gemini OCR and Medical Extraction pipelines are constrained by strict system prompts (from Phase 9A) designed to extract facts only and never provide autonomous diagnoses, treatment plans, or unverified hallucinations. Validations exist to catch unsupported diagnostic entity injection.

### E. Frontend API Fallbacks Disabled
All frontend clients in `patient-kiosk` and `doctor-dashboard` have been hardened to strictly throw errors when in `NEXT_PUBLIC_DATA_MODE="api"`. Mock data cannot accidentally slip into the UI during a failed API call, which prevents showing fabricated or incorrect medical information to a real patient.

---

## 2. PRODUCTION REQUIREMENTS

The following mechanisms MUST be implemented before MediPlatform handles real Protected Health Information (PHI):

### A. Authentication & Authorization
Currently, there is no real Identity and Access Management (IAM). 
- **Doctor Dashboard**: Must implement secure login (e.g., OAuth 2.0 / OIDC) and enforce JWT validation on all `/encounters` and `/patients` endpoints.
- **Patient Kiosk**: Must implement short-lived, cryptographically secure OTPs for patient login or Aadhar-based e-KYC.

### B. Secrets Management
- **API Keys**: Ensure `GEMINI_API_KEY` and Supabase credentials are not committed to source control and are loaded from a secure KMS (Key Management Service) in production.
- **Audit Logs**: Validate that sensitive tokens and keys are never printed to `stdout` or logs.

### C. Transport Security (TLS/SSL)
All traffic must be strictly over HTTPS. Red flags and medical histories must never traverse the network in plain text.

### D. Data Encryption at Rest
While Supabase encrypts data at rest automatically on its managed volumes, field-level encryption for highly sensitive fields (like full names, Aadhar IDs) using Application-Layer Encryption is strongly recommended to comply with HIPAA/ABDM.

### E. Audit Logging
Implement an immutable audit trail for:
1. Every successful and failed access attempt to a patient record.
2. Every Doctor verification, edit, or rejection of an AI Summary.
3. Every document upload and extraction event.

### F. Rate Limiting and WAF
Deploy a Web Application Firewall (WAF) and enforce API rate limiting (HTTP 429) to prevent DoS attacks against the LLM extraction endpoints, which are computationally expensive.

### G. Session Expiration
Kiosk sessions are currently generated with a 60-minute expiration timestamp, but a background cron or middleware must actively purge or invalidate expired tokens.
