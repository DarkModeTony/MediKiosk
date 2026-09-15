import {
  Patient, Encounter, ClinicalState, RedFlag, PatientTimeline, ClinicalSummary
} from './types';

// ─── Demo Patient Data ────────────────────────────────────────────────────────
// Raj Kumar (42, M, Delhi) — primary showcase patient.
// Pre-loaded with Type 2 DM + HTN, Penicillin allergy, Metformin + Amlodipine,
// current encounter: Fever & weakness x3 days, BP elevated, family history.

export const MOCK_PATIENTS: Patient[] = [
  { id: "pat_raj_123",   name: "Raj Kumar",    age: 42, gender: "Male",   created_at: "2026-09-15T08:10:00Z" },
  { id: "pat_anita_456", name: "Anita Sharma", age: 45, gender: "Female", created_at: "2026-09-15T08:30:00Z" },
  { id: "pat_mohan_789", name: "Mohan Singh",  age: 34, gender: "Male",   created_at: "2026-09-15T08:45:00Z" },
  { id: "pat_priya_012", name: "Priya Verma",  age: 29, gender: "Female", created_at: "2026-09-15T09:00:00Z" },
  { id: "pat_arjun_345", name: "Arjun Patel",  age: 52, gender: "Male",   created_at: "2026-09-15T09:15:00Z" },
  { id: "pat_neha_678",  name: "Neha Gupta",   age: 24, gender: "Female", created_at: "2026-09-15T09:30:00Z" },
];

export const MOCK_ENCOUNTERS: Encounter[] = [
  {
    id: "enc_raj_001",
    patient_id: "pat_raj_123",
    status: "WAITING",
    priority: "MEDIUM",
    chief_complaint: "Fever and weakness for 3 days",
    created_at: "2026-09-15T08:15:00Z",
    updated_at: "2026-09-15T08:20:00Z",
  },
  {
    id: "enc_anita_002",
    patient_id: "pat_anita_456",
    status: "IN_CONSULTATION",
    priority: "NORMAL",
    chief_complaint: "Persistent cough",
    created_at: "2026-09-15T08:35:00Z",
    updated_at: "2026-09-15T08:35:00Z",
  },
  {
    id: "enc_mohan_003",
    patient_id: "pat_mohan_789",
    status: "WAITING",
    priority: "HIGH",
    chief_complaint: "Severe chest pain radiating to left arm",
    created_at: "2026-09-15T08:50:00Z",
    updated_at: "2026-09-15T08:52:00Z",
  },
  {
    id: "enc_priya_004",
    patient_id: "pat_priya_012",
    status: "WAITING",
    priority: "NORMAL",
    chief_complaint: "Abdominal pain and nausea",
    created_at: "2026-09-15T09:05:00Z",
    updated_at: "2026-09-15T09:05:00Z",
  },
  {
    id: "enc_arjun_005",
    patient_id: "pat_arjun_345",
    status: "COMPLETED",
    priority: "NORMAL",
    chief_complaint: "Follow-up for hypertension",
    created_at: "2026-09-15T09:20:00Z",
    updated_at: "2026-09-15T10:00:00Z",
  },
  {
    id: "enc_neha_006",
    patient_id: "pat_neha_678",
    status: "WAITING",
    priority: "NORMAL",
    chief_complaint: "Headache and dizziness",
    created_at: "2026-09-15T09:35:00Z",
    updated_at: "2026-09-15T09:35:00Z",
  },
];

// ─── Raj Kumar: Clinical State ─────────────────────────────────────────────────
export const MOCK_CLINICAL_STATE: Record<string, ClinicalState> = {
  "enc_raj_001": {
    status: "COMPLETED",
    encounter_id: "enc_raj_001",
    facts: {
      CHIEF_COMPLAINT:       { state: "COLLECTED", value: "Fever and general weakness" },
      ONSET:                 { state: "COLLECTED", value: "3 days ago" },
      ASSOCIATED_SYMPTOMS:   { state: "COLLECTED", value: "Headache, reduced appetite" },
      SEVERITY:              { state: "COLLECTED", value: "Moderate" },
      PAST_MEDICAL_HISTORY:  { state: "COLLECTED", value: "Type 2 Diabetes Mellitus (since 2020), Hypertension (since 2022)" },
      SURGICAL_HISTORY:      { state: "COLLECTED", value: "Appendectomy (2015)" },
      ALLERGIES:             { state: "COLLECTED", value: "Penicillin — Skin rash (moderate)" },
      CURRENT_MEDICATIONS:   { state: "COLLECTED", value: "Metformin 500 mg BD, Amlodipine 5 mg OD" },
      FAMILY_HISTORY:        { state: "COLLECTED", value: "Father: Hypertension; Mother: Type 2 Diabetes" },
      SOCIAL_HISTORY:        { state: "COLLECTED", value: "Non-smoker, occasional alcohol, office employee" },
      PREFERRED_LANGUAGE:    { state: "COLLECTED", value: "Hindi" },
    },
  } satisfies ClinicalState,
};

// ─── Raj Kumar: Red Flags ──────────────────────────────────────────────────────
export const MOCK_RED_FLAGS: Record<string, RedFlag[]> = {
  // Raj Kumar: elevated BP (148/92) in known hypertensive diabetic — MEDIUM flag
  "enc_raj_001": [
    {
      rule_name: "ELEVATED_BP_KNOWN_HYPERTENSIVE",
      severity: "MEDIUM",
      evidence: {
        BLOOD_PRESSURE: "148/92 mmHg",
        PAST_MEDICAL_HISTORY: "Hypertension since 2022",
        CURRENT_MEDICATION: "Amlodipine 5 mg OD",
      },
      status: "ACTIVE",
    } satisfies RedFlag,
  ],
  // Mohan Singh: HIGH — classic cardiac presentation
  "enc_mohan_003": [
    {
      rule_name: "CARDIAC_EMERGENCY_SUSPECTED",
      severity: "HIGH",
      evidence: {
        CHIEF_COMPLAINT: "Severe chest pain radiating to left arm",
        ONSET: "Sudden, 30 minutes ago",
      },
      status: "ACTIVE",
    } satisfies RedFlag,
  ],
};

// ─── Raj Kumar: Medical Timeline ──────────────────────────────────────────────
export const MOCK_TIMELINES: Record<string, PatientTimeline> = {
  "pat_raj_123": {
    patient_id: "pat_raj_123",
    events: [
      {
        date: "2020-04-10T10:00:00Z",
        date_known: true,
        type: "DOCUMENT",
        document_id: "doc_raj_dm_01",
        document_type: "Diagnosis Record",
        entities: [
          {
            type: "DIAGNOSIS",
            value: { condition: "Type 2 Diabetes Mellitus", icd10: "E11", status: "Active" },
            status: "AI_EXTRACTED",
            source_text: "Diagnosed with T2DM — HbA1c 8.2%",
          },
        ],
      },
      {
        date: "2020-04-10T10:00:00Z",
        date_known: true,
        type: "DOCUMENT",
        document_id: "doc_raj_metformin_01",
        document_type: "Prescription",
        entities: [
          {
            type: "MEDICATION",
            value: { name: "Metformin", dose: "500 mg", frequency: "Twice daily" },
            status: "AI_EXTRACTED",
            source_text: "Tab Metformin 500 mg BD",
          },
        ],
      },
      {
        date: "2022-07-05T09:30:00Z",
        date_known: true,
        type: "DOCUMENT",
        document_id: "doc_raj_htn_01",
        document_type: "Prescription",
        entities: [
          {
            type: "DIAGNOSIS",
            value: { condition: "Hypertension", icd10: "I10", status: "Active" },
            status: "AI_EXTRACTED",
            source_text: "BP 154/96 — started on Amlodipine",
          },
          {
            type: "MEDICATION",
            value: { name: "Amlodipine", dose: "5 mg", frequency: "Once daily" },
            status: "AI_EXTRACTED",
            source_text: "Tab Amlodipine 5 mg OD",
          },
        ],
      },
      {
        date: "2015-03-18T08:00:00Z",
        date_known: true,
        type: "DOCUMENT",
        document_id: "doc_raj_surgery_01",
        document_type: "Discharge Summary",
        entities: [
          {
            type: "PROCEDURE",
            value: { procedure: "Appendectomy", year: 2015, indication: "Acute appendicitis" },
            status: "AI_EXTRACTED",
            source_text: "Laparoscopic appendectomy performed on 18/03/2015",
          },
        ],
      },
      {
        date: "2026-02-10T11:00:00Z",
        date_known: true,
        type: "DOCUMENT",
        document_id: "doc_raj_lab_01",
        document_type: "Laboratory Report",
        entities: [
          {
            type: "LAB_RESULT",
            value: { test: "HbA1c", result: "7.4", unit: "%", reference: "<7.0 (Target)", status: "Above Target" },
            status: "AI_EXTRACTED",
            source_text: "HbA1c: 7.4% (Target < 7.0)",
          },
          {
            type: "LAB_RESULT",
            value: { test: "Fasting Blood Glucose", result: "142", unit: "mg/dL", reference: "70-100", status: "High" },
            status: "AI_EXTRACTED",
            source_text: "FBS: 142 mg/dL",
          },
        ],
      },
      {
        date: "2026-09-15T08:15:00Z",
        date_known: true,
        type: "ENCOUNTER",
        document_id: "enc_raj_001",
        document_type: "Current Encounter",
        entities: [],
      },
    ],
  } satisfies PatientTimeline,
};

// ─── Raj Kumar: AI-Generated Clinical Summary ──────────────────────────────────
export const MOCK_SUMMARIES: Record<string, ClinicalSummary> = {
  "enc_raj_001": {
    summary_id: "sum_raj_999",
    status: "AI_DRAFT",
    latest_version: {
      structured_sections: [
        {
          title: "CHIEF COMPLAINT",
          content: "Fever (101.2°F) and generalised weakness for 3 days.",
          section_type: "COMPLAINT",
        },
        {
          title: "HISTORY OF PRESENT ILLNESS",
          content:
            "Mr Raj Kumar, a 42-year-old male office employee from Delhi, presents with a 3-day history of low-grade fever (documented 101.2°F), generalised weakness, headache, and reduced appetite. No preceding upper respiratory symptoms or travel history obtained during kiosk intake. Duration and progression are consistent with a viral or bacterial systemic illness, though his poorly controlled diabetes (HbA1c 7.4% in Feb 2026) warrants consideration of secondary infection.",
          section_type: "HPI",
        },
        {
          title: "RELEVANT MEDICAL HISTORY",
          content:
            "• Type 2 Diabetes Mellitus — diagnosed April 2020, active. HbA1c 7.4% (Feb 2026).\n• Hypertension — diagnosed July 2022, active. BP today 148/92 mmHg (elevated above target).\n• Surgical history: Laparoscopic appendectomy (March 2015, acute appendicitis). No other hospitalisations reported.",
          section_type: "HISTORY",
        },
        {
          title: "FAMILY HISTORY",
          content: "Father: Hypertension. Mother: Type 2 Diabetes Mellitus.",
          section_type: "FAMILY",
        },
        {
          title: "SOCIAL HISTORY",
          content: "Non-smoker. Occasional alcohol use. Office employee. Preferred communication language: Hindi.",
          section_type: "SOCIAL",
        },
        {
          title: "ALLERGIES",
          content: "⚠ Penicillin → Skin rash (Moderate severity). Confirmed by patient at kiosk intake.",
          section_type: "ALLERGIES",
        },
        {
          title: "CURRENT MEDICATIONS",
          content:
            "1. Metformin 500 mg — Twice daily (active)\n2. Amlodipine 5 mg — Once daily (active)",
          section_type: "MEDICATIONS",
        },
        {
          title: "VITALS",
          content:
            "Temperature: 101.2°F  |  BP: 148/92 mmHg  |  HR: 96 bpm  |  SpO₂: 98%",
          section_type: "VITALS",
        },
        {
          title: "ACTIVE RED FLAGS",
          content:
            "MEDIUM — ELEVATED_BP_KNOWN_HYPERTENSIVE: BP 148/92 mmHg in a known hypertensive patient currently on Amlodipine 5 mg OD. Consider dose optimisation or antihypertensive review.",
          section_type: "ALERTS",
        },
        {
          title: "SUGGESTED WORKUP (AI Draft — Doctor Verification Required)",
          content:
            "• CBC with differential (fever workup)\n• Blood Culture (if systemic infection suspected)\n• Fasting Blood Glucose + HbA1c (glycaemic review)\n• Urine routine and microscopy\n• LFT / RFT baseline (given Metformin use)",
          section_type: "PLAN",
        },
      ],
    },
    original_draft: {
      structured_sections: [
        {
          title: "CHIEF COMPLAINT",
          content: "Fever (101.2°F) and generalised weakness for 3 days.",
          section_type: "COMPLAINT",
        },
        {
          title: "HISTORY OF PRESENT ILLNESS",
          content:
            "Mr Raj Kumar, a 42-year-old male office employee from Delhi, presents with a 3-day history of low-grade fever (documented 101.2°F), generalised weakness, headache, and reduced appetite. No preceding upper respiratory symptoms or travel history obtained during kiosk intake. Duration and progression are consistent with a viral or bacterial systemic illness, though his poorly controlled diabetes (HbA1c 7.4% in Feb 2026) warrants consideration of secondary infection.",
          section_type: "HPI",
        },
        {
          title: "RELEVANT MEDICAL HISTORY",
          content:
            "• Type 2 Diabetes Mellitus — diagnosed April 2020, active. HbA1c 7.4% (Feb 2026).\n• Hypertension — diagnosed July 2022, active. BP today 148/92 mmHg (elevated above target).\n• Surgical history: Laparoscopic appendectomy (March 2015, acute appendicitis). No other hospitalisations reported.",
          section_type: "HISTORY",
        },
        {
          title: "FAMILY HISTORY",
          content: "Father: Hypertension. Mother: Type 2 Diabetes Mellitus.",
          section_type: "FAMILY",
        },
        {
          title: "SOCIAL HISTORY",
          content: "Non-smoker. Occasional alcohol use. Office employee. Preferred communication language: Hindi.",
          section_type: "SOCIAL",
        },
        {
          title: "ALLERGIES",
          content: "⚠ Penicillin → Skin rash (Moderate severity). Confirmed by patient at kiosk intake.",
          section_type: "ALLERGIES",
        },
        {
          title: "CURRENT MEDICATIONS",
          content:
            "1. Metformin 500 mg — Twice daily (active)\n2. Amlodipine 5 mg — Once daily (active)",
          section_type: "MEDICATIONS",
        },
        {
          title: "VITALS",
          content:
            "Temperature: 101.2°F  |  BP: 148/92 mmHg  |  HR: 96 bpm  |  SpO₂: 98%",
          section_type: "VITALS",
        },
        {
          title: "ACTIVE RED FLAGS",
          content:
            "MEDIUM — ELEVATED_BP_KNOWN_HYPERTENSIVE: BP 148/92 mmHg in a known hypertensive patient currently on Amlodipine 5 mg OD. Consider dose optimisation or antihypertensive review.",
          section_type: "ALERTS",
        },
        {
          title: "SUGGESTED WORKUP (AI Draft — Doctor Verification Required)",
          content:
            "• CBC with differential (fever workup)\n• Blood Culture (if systemic infection suspected)\n• Fasting Blood Glucose + HbA1c (glycaemic review)\n• Urine routine and microscopy\n• LFT / RFT baseline (given Metformin use)",
          section_type: "PLAN",
        },
      ],
    },
  } satisfies ClinicalSummary,
};
