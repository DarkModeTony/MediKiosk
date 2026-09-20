import { fetchApi } from "./client";

export interface PatientDemographics {
  name: string;
  age?: number;
  gender?: string;
  dob?: string;
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  blood_group?: string;
  emergency_contact?: {
    name?: string;
    phone?: string;
    relation?: string;
  };
  preferred_language?: string;
  communication_mode?: string;
}

export interface ChronicCondition {
  condition: string;
  icd10?: string;
  since?: string;
  status?: string;
}

export interface AllergyItem {
  substance: string;
  reaction?: string;
  severity?: string;
  confirmed?: boolean;
}

export interface MedicationItem {
  name: string;
  dose?: string;
  frequency?: string;
  status?: string;
}

export interface SurgeryItem {
  procedure: string;
  year?: number | string;
  indication?: string;
  status?: string;
}

export interface HospitalizationItem {
  reason: string;
  year?: number | string;
}

export interface RecentActivityItem {
  encounter_id: string;
  date?: string;
  status: string;
  chief_complaint?: string;
  doctor_note?: any;
}

export interface PrescriptionSummaryItem {
  name: string;
  dose?: string;
  frequency?: string;
  instructions?: string;
  status?: string;
}

export interface PrescriptionSummary {
  id: string;
  status: string;
  notes?: string;
  created_at?: string;
  finalized_at?: string;
  items: PrescriptionSummaryItem[];
}

export interface PatientProfileResponse {
  patient_id: string;
  demographics: PatientDemographics;
  profile_summary: {
    chronic_conditions: ChronicCondition[];
    allergies: AllergyItem[];
    current_medications: MedicationItem[];
    surgeries: SurgeryItem[];
    hospitalizations: HospitalizationItem[];
    vitals_last: Record<string, any>;
  };
  recent_activity: RecentActivityItem[];
  prescriptions: PrescriptionSummary[];
  documents_count: number;
}

export interface ProfileUpdatePayload {
  phone?: string;
  email?: string;
  address?: string;
  emergency_contact?: {
    name?: string;
    phone?: string;
    relation?: string;
  };
  preferred_language?: string;
  communication_mode?: string;
}

export interface MedicalChangeReportPayload {
  category: "allergy" | "condition" | "medication" | "procedure" | "general";
  description: string;
  details?: Record<string, any>;
}

export interface PendingReportItem {
  id: string;
  category: string;
  description: string;
  reported_at?: string;
  status: string;
}

export interface MedicalHistoryResponse {
  patient_id: string;
  patient_name: string;
  medical_history: {
    chronic_conditions?: ChronicCondition[];
    surgeries?: SurgeryItem[];
    hospitalizations?: HospitalizationItem[];
  };
  allergies: {
    known?: AllergyItem[];
  };
  current_medications: MedicationItem[];
  family_history?: Record<string, any>;
  social_history?: Record<string, any>;
  vitals_last?: Record<string, any>;
  prescriptions?: Array<{
    id: string;
    status: string;
    notes?: string;
    created_at?: string;
    items: Array<{
      medication_name: string;
      dose?: string;
      frequency?: string;
      instructions?: string;
    }>;
  }>;
  pending_reports: PendingReportItem[];
}

export async function getPatientProfile(sessionToken: string): Promise<PatientProfileResponse> {
  return await fetchApi<PatientProfileResponse>("/kiosk/profile", {
    method: "GET",
    headers: {
      "X-Session-Token": sessionToken,
    },
  });
}

export async function updatePatientProfile(
  sessionToken: string,
  payload: ProfileUpdatePayload
): Promise<{ status: string; message: string; demographics: PatientDemographics }> {
  return await fetchApi<{ status: string; message: string; demographics: PatientDemographics }>(
    "/kiosk/profile",
    {
      method: "PUT",
      headers: {
        "X-Session-Token": sessionToken,
      },
      body: JSON.stringify(payload),
    }
  );
}

export async function reportMedicalChange(
  sessionToken: string,
  payload: MedicalChangeReportPayload
): Promise<{ status: string; fact_id: string; message: string }> {
  return await fetchApi<{ status: string; fact_id: string; message: string }>(
    "/kiosk/profile/report-change",
    {
      method: "POST",
      headers: {
        "X-Session-Token": sessionToken,
      },
      body: JSON.stringify(payload),
    }
  );
}

export async function getPatientMedicalHistory(sessionToken: string): Promise<MedicalHistoryResponse> {
  return await fetchApi<MedicalHistoryResponse>("/kiosk/medical-history", {
    method: "GET",
    headers: {
      "X-Session-Token": sessionToken,
    },
  });
}
