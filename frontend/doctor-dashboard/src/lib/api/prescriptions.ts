import { fetchClient } from './client';

export interface MedicineSearchResult {
  id: number;
  name: string;
  generic_name: string;
  composition_1: string;
  composition_2: string;
  manufacturer_name: string;
  type: string;
  pack_size_label: string;
  price: number;
  dosage_form: string;
  strength: string;
  suggested_routes: string[];
  default_dose: string;
}

export interface PrescriptionItem {
  id?: string;
  medicine_id?: number;
  medication_name: string;
  generic_name?: string;
  strength?: string;
  dosage_form?: string;
  dose?: string;
  dose_unit?: string;
  route?: string;
  frequency?: string;
  timing?: string;
  duration_value?: number;
  duration_unit?: string;
  quantity?: number;
  indication?: string;
  instructions?: string;
  is_prn?: boolean;
  min_interval?: string;
  max_daily_dose?: string;
  status?: string;
  item_metadata?: Record<string, any>;
  created_at?: string;
}

export interface SafetyAlert {
  type: 'ALLERGY_CONFLICT' | 'DUPLICATE_MEDICATION' | 'CONDITION_CONFLICT' | 'INFO';
  severity: 'INFO' | 'CAUTION' | 'HIGH';
  title: string;
  message: string;
  medication_name: string;
  source: string;
}

export interface SafetyCheckResult {
  alerts: SafetyAlert[];
  allergies_reviewed: boolean;
  current_meds_reviewed: boolean;
  patient_history_reviewed: boolean;
  passed_critical: boolean;
}

export interface Prescription {
  id: string;
  patient_id?: string;
  encounter_id: string;
  doctor_id?: string;
  status: 'DRAFT' | 'FINALIZED' | 'AMENDED' | 'CANCELLED';
  notes?: string;
  created_at?: string;
  updated_at?: string;
  finalized_at?: string;
  items: PrescriptionItem[];
  safety_check?: SafetyCheckResult;
}

export interface PrescriptionPayload {
  patient_id?: string;
  doctor_id?: string;
  notes?: string;
  items: PrescriptionItem[];
}

export async function searchMedicines(query: string, limit = 20): Promise<MedicineSearchResult[]> {
  if (!query || query.trim().length === 0) return [];
  const res = await fetchClient(
    `/medicines/search?q=${encodeURIComponent(query)}&limit=${limit}`
  );
  return res.medicines || [];
}

export async function getMedicine(medicineId: number): Promise<MedicineSearchResult> {
  return fetchClient(`/medicines/${medicineId}`);
}

// Demo encounter IDs that use mock data
const DEMO_ENCOUNTER_IDS = ['enc_raj_001', 'enc_anita_002', 'enc_mohan_003', 'enc_priya_004', 'enc_arjun_005', 'enc_neha_006'];
const DEMO_PATIENT_IDS = ['pat_raj_123', 'pat_anita_456', 'pat_mohan_789', 'pat_priya_012', 'pat_arjun_345', 'pat_neha_678'];

// In-memory draft store for demo prescriptions (persists through session)
const DEMO_PRESCRIPTIONS: Record<string, Prescription> = {};

export async function getEncounterPrescriptions(encounterId: string): Promise<Prescription[]> {
  if (DEMO_ENCOUNTER_IDS.includes(encounterId)) {
    // Return in-memory draft if exists, else empty
    return DEMO_PRESCRIPTIONS[encounterId] ? [DEMO_PRESCRIPTIONS[encounterId]] : [];
  }
  try {
    return await fetchClient(`/encounters/${encounterId}/prescriptions`);
  } catch {
    return [];
  }
}

export async function saveDraftPrescription(
  encounterId: string,
  payload: PrescriptionPayload
): Promise<Prescription> {
  if (DEMO_ENCOUNTER_IDS.includes(encounterId)) {
    const existing = DEMO_PRESCRIPTIONS[encounterId];
    const draft: Prescription = {
      id: existing?.id || `rx_demo_${encounterId}_${Date.now()}`,
      encounter_id: encounterId,
      status: 'DRAFT',
      notes: payload.notes || '',
      items: payload.items,
      created_at: existing?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    DEMO_PRESCRIPTIONS[encounterId] = draft;
    return draft;
  }
  return fetchClient(`/encounters/${encounterId}/prescriptions`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function finalizePrescription(
  encounterId: string,
  prescriptionId: string,
  payload: { doctor_id?: string; notes?: string; acknowledged_safety_alerts?: boolean }
): Promise<Prescription> {
  if (DEMO_ENCOUNTER_IDS.includes(encounterId)) {
    const existing = DEMO_PRESCRIPTIONS[encounterId];
    if (existing) {
      existing.status = 'FINALIZED';
      existing.finalized_at = new Date().toISOString();
      existing.notes = payload.notes || existing.notes;
      DEMO_PRESCRIPTIONS[encounterId] = existing;
      return existing;
    }
  }
  return fetchClient(
    `/encounters/${encounterId}/prescriptions/${prescriptionId}/finalize`,
    { method: 'POST', body: JSON.stringify(payload) }
  );
}

export async function amendPrescription(
  encounterId: string,
  prescriptionId: string
): Promise<Prescription> {
  if (DEMO_ENCOUNTER_IDS.includes(encounterId)) {
    const existing = DEMO_PRESCRIPTIONS[encounterId];
    if (existing) { existing.status = 'DRAFT'; DEMO_PRESCRIPTIONS[encounterId] = existing; return existing; }
  }
  return fetchClient(
    `/encounters/${encounterId}/prescriptions/${prescriptionId}/amend`,
    { method: 'POST' }
  );
}

export async function getPatientPrescriptions(patientId: string): Promise<Prescription[]> {
  if (DEMO_PATIENT_IDS.includes(patientId)) return [];
  try {
    return await fetchClient(`/patients/${patientId}/prescriptions`);
  } catch {
    return [];
  }
}
