import {
  Patient, Encounter, ClinicalState, RedFlag, PatientTimeline, ClinicalSummary
} from './types';

export const MOCK_PATIENTS: Patient[] = [
  { id: "pat_raj_123", name: "Raj Kumar", age: 68, gender: "Male", created_at: "2026-09-12T09:00:00Z" },
  { id: "pat_anita_456", name: "Anita Sharma", age: 45, gender: "Female", created_at: "2026-09-12T09:30:00Z" },
  { id: "pat_mohan_789", name: "Mohan Singh", age: 34, gender: "Male", created_at: "2026-09-12T09:45:00Z" },
  { id: "pat_priya_012", name: "Priya Verma", age: 29, gender: "Female", created_at: "2026-09-12T10:00:00Z" },
  { id: "pat_arjun_345", name: "Arjun Patel", age: 52, gender: "Male", created_at: "2026-09-12T10:15:00Z" },
  { id: "pat_neha_678", name: "Neha Gupta", age: 24, gender: "Female", created_at: "2026-09-12T10:30:00Z" }
];

export const MOCK_ENCOUNTERS: Encounter[] = [
  { id: "enc_raj_001", patient_id: "pat_raj_123", status: "WAITING", priority: "HIGH", chief_complaint: "Chest pain", created_at: "2026-09-12T09:05:00Z", updated_at: "2026-09-12T09:10:00Z" },
  { id: "enc_anita_002", patient_id: "pat_anita_456", status: "IN_CONSULTATION", priority: "NORMAL", chief_complaint: "Fever", created_at: "2026-09-12T09:35:00Z", updated_at: "2026-09-12T09:35:00Z" },
  { id: "enc_mohan_003", patient_id: "pat_mohan_789", status: "WAITING", priority: "NORMAL", chief_complaint: "Headache", created_at: "2026-09-12T09:50:00Z", updated_at: "2026-09-12T09:50:00Z" },
  { id: "enc_priya_004", patient_id: "pat_priya_012", status: "WAITING", priority: "HIGH", chief_complaint: "Abdominal Pain", created_at: "2026-09-12T10:05:00Z", updated_at: "2026-09-12T10:05:00Z" },
  { id: "enc_arjun_005", patient_id: "pat_arjun_345", status: "COMPLETED", priority: "NORMAL", chief_complaint: "Cough", created_at: "2026-09-12T10:20:00Z", updated_at: "2026-09-12T11:00:00Z" },
  { id: "enc_neha_006", patient_id: "pat_neha_678", status: "WAITING", priority: "NORMAL", chief_complaint: "Vomiting", created_at: "2026-09-12T10:35:00Z", updated_at: "2026-09-12T10:35:00Z" }
];

export const MOCK_CLINICAL_STATE: Record<string, ClinicalState> = {
  "enc_raj_001": {
    status: "COMPLETED",
    encounter_id: "enc_raj_001",
    facts: {
      CHIEF_COMPLAINT: { state: "COLLECTED", value: "Chest pain" },
      ONSET: { state: "COLLECTED", value: "Today morning" },
      PAST_MEDICAL_HISTORY: { state: "COLLECTED", value: "Hypertension" },
      ALLERGIES: { state: "NOT_ASKED", value: null },
      FAMILY_HISTORY: { state: "UNKNOWN", value: "Not documented" }
    }
  } satisfies ClinicalState
};

export const MOCK_RED_FLAGS: Record<string, RedFlag[]> = {
  "enc_raj_001": [
    { rule_name: "CHEST_PAIN_SUDDEN_ONSET", severity: "HIGH", evidence: {"CHIEF_COMPLAINT": "Chest pain", "ONSET": "Today morning"}, status: "ACTIVE" } satisfies RedFlag
  ]
};

export const MOCK_TIMELINES: Record<string, PatientTimeline> = {
  "pat_raj_123": {
    patient_id: "pat_raj_123",
    events: [
      { date: "2025-06-15T10:00:00Z", date_known: true, type: "DOCUMENT", document_id: "doc_raj_01", document_type: "Prescription", entities: [{ type: "MEDICATION", value: { name: "Amlodipine", dose: "5 mg", frequency: "once daily" }, status: "AI_EXTRACTED", source_text: "Tab Amlodipine 5mg OD" }] },
      { date: "2026-01-20T08:30:00Z", date_known: true, type: "DOCUMENT", document_id: "doc_raj_02", document_type: "Laboratory Report", entities: [{ type: "LAB_RESULT", value: { test: "Hemoglobin", result: "10.2", unit: "g/dL", reference: "12-16", status: "Abnormal" }, status: "AI_EXTRACTED", source_text: "Hb: 10.2 g/dL (Ref: 12-16)" }] },
      { date: "2026-09-12T09:05:00Z", date_known: true, type: "ENCOUNTER", document_id: "enc_raj_001", document_type: "Current Encounter", entities: [] }
    ]
  } satisfies PatientTimeline
};

export const MOCK_SUMMARIES: Record<string, ClinicalSummary> = {
  "enc_raj_001": {
    summary_id: "sum_raj_999",
    status: "AI_DRAFT",
    latest_version: {
      structured_sections: [
        { title: "CHIEF COMPLAINT", content: "Chest pain", section_type: "COMPLAINT" },
        { title: "HISTORY OF PRESENT ILLNESS", content: "Patient reports sudden onset chest pain beginning today morning.", section_type: "HPI" },
        { title: "RELEVANT MEDICAL HISTORY", content: "Hypertension", section_type: "HISTORY" },
        { title: "CURRENT MEDICATIONS", content: "Amlodipine 5 mg once daily", section_type: "MEDICATIONS" },
        { title: "INVESTIGATIONS", content: "Hemoglobin 10.2 g/dL (Abnormal)", section_type: "LABS" },
        { title: "RED FLAGS", content: "HIGH: CHEST_PAIN_SUDDEN_ONSET", section_type: "ALERTS" }
      ]
    },
    original_draft: {
      structured_sections: [
        { title: "CHIEF COMPLAINT", content: "Chest pain", section_type: "COMPLAINT" },
        { title: "HISTORY OF PRESENT ILLNESS", content: "Patient reports sudden onset chest pain beginning today morning.", section_type: "HPI" },
        { title: "RELEVANT MEDICAL HISTORY", content: "Hypertension", section_type: "HISTORY" },
        { title: "CURRENT MEDICATIONS", content: "Amlodipine 5 mg once daily", section_type: "MEDICATIONS" },
        { title: "INVESTIGATIONS", content: "Hemoglobin 10.2 g/dL (Abnormal)", section_type: "LABS" },
        { title: "RED FLAGS", content: "HIGH: CHEST_PAIN_SUDDEN_ONSET", section_type: "ALERTS" }
      ]
    }
  } satisfies ClinicalSummary
};
