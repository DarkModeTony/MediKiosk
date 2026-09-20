import { fetchClient, IS_MOCK, mockDelay } from './client';

export interface SpecialistDirectoryItem {
  doctor_id: string;
  username: string;
  display_name: string;
  specialty: string;
  sub_specialty?: string | null;
  qualification?: string | null;
  hospital_id: string;
  hospital_name?: string | null;
  hospital_city?: string | null;
  availability_status: 'ONLINE' | 'BUSY' | 'OFFLINE';
  doctalk_enabled: boolean;
  is_verified: boolean;
}

export interface SpecialistFindAnyResponse {
  found: boolean;
  specialist: SpecialistDirectoryItem | null;
  message: string;
}

export interface SharingScopePreferences {
  include_history?: boolean;
  include_vitals?: boolean;
  include_allergies?: boolean;
  include_medications?: boolean;
  include_conditions?: boolean;
  include_investigations?: boolean;
  include_documents?: boolean;
  include_summary?: boolean;
  selected_document_ids?: string[];
  selected_investigation_ids?: string[];
}

export interface ConsultationCreateRequest {
  encounter_id: string;
  specialist_id?: string | null;
  specialty: string;
  reason: string;
  urgency?: 'ROUTINE' | 'URGENT' | 'STAT' | 'Normal' | 'Urgent';
  requested_duration_minutes: number;
  access_scope?: Record<string, unknown>;
  sharing_preferences?: SharingScopePreferences;
}

export function getConsultationDocumentUrl(consultationId: string, documentId: string): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  return `${baseUrl}/doctalk/requests/${consultationId}/documents/${documentId}`;
}

export interface ConsultationNoteResponse {
  id: string;
  consultation_id: string;
  encounter_id?: string | null;
  specialist_id: string;
  specialist_name?: string | null;
  specialist_hospital_id: string;
  specialist_hospital_name?: string | null;
  clinical_opinion: string;
  recommendations?: any;
  further_evaluation?: string | null;
  follow_up?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ConsultationResponse {
  id: string;
  requesting_doctor_id: string;
  requesting_doctor_name?: string | null;
  requesting_hospital_id: string;
  requesting_hospital_name?: string | null;
  specialist_id?: string | null;
  specialist_name?: string | null;
  specialist_hospital_id?: string | null;
  specialist_hospital_name?: string | null;
  patient_id: string;
  patient_name?: string | null;
  patient_home_hospital_id: string;
  encounter_id: string;
  specialty: string;
  reason: string;
  urgency: string;
  requested_duration_minutes: number;
  status: 'REQUESTED' | 'ACCEPTED' | 'DECLINED' | 'CANCELLED' | 'EXPIRED' | 'IN_PROGRESS' | 'COMPLETED';
  access_scope?: Record<string, unknown>;
  access_expires_at?: string | null;
  decline_reason?: string | null;
  created_at?: string;
  accepted_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  cancelled_at?: string | null;
  notes?: ConsultationNoteResponse[];
}

export interface RoomTokenResponse {
  room_id: string;
  room_token: string;
  role: 'REQUESTING_DOCTOR' | 'SPECIALIST';
  user_id: string;
  user_name?: string | null;
  peer_id?: string | null;
  peer_name?: string | null;
  peer_hospital?: string | null;
  duration_minutes: number;
  remaining_seconds: number;
  status: string;
  ws_url?: string | null;
}

// ─── Demo / Fallback Mock Data ──────────────────────────────────────────────

export const MOCK_SPECIALISTS: SpecialistDirectoryItem[] = [
  {
    doctor_id: "3fa4b374-2cbe-475c-ab84-592dad4ca2c5",
    username: "dr.sharma",
    display_name: "Dr. Priya Sharma",
    specialty: "Internal Medicine",
    sub_specialty: "Preventative & Metabolic Care",
    qualification: "MBBS, MD (General Medicine)",
    hospital_id: "606243d0-6ee9-41fe-8f94-8c837b001c39",
    hospital_name: "Apollo Hospitals Delhi",
    hospital_city: "Delhi",
    availability_status: "ONLINE",
    doctalk_enabled: true,
    is_verified: true,
  },
  {
    doctor_id: "5e493c1d-7e46-42bd-8e97-cabadc45ad9a",
    username: "dr.sengupta",
    display_name: "Dr. Rajesh Sengupta",
    specialty: "Cardiology",
    sub_specialty: "Interventional Cardiology & Angioplasty",
    qualification: "MBBS, MD (Medicine), DM (Cardiology), FACC",
    hospital_id: "39ffd978-8945-43e6-9727-d7a6fd9b6f0a",
    hospital_name: "Fortis Memorial Research Institute Gurugram",
    hospital_city: "Gurugram",
    availability_status: "ONLINE",
    doctalk_enabled: true,
    is_verified: true,
  },
  {
    doctor_id: "5a22b878-4b7b-48b0-a3d6-df332cbe9ad6",
    username: "dr.iyer",
    display_name: "Dr. Ananya Iyer",
    specialty: "Neurology",
    sub_specialty: "Acute Stroke & Comprehensive Epilepsy Care",
    qualification: "MBBS, MD, DM (Neurology), FINR",
    hospital_id: "53d3c8ef-e2b4-4fdb-934c-a1cb9561fded",
    hospital_name: "Manipal Hospital Bengaluru",
    hospital_city: "Bengaluru",
    availability_status: "ONLINE",
    doctalk_enabled: true,
    is_verified: true,
  },
  {
    doctor_id: "1d3933e8-d361-4364-9703-49e2048c7796",
    username: "dr.mehta",
    display_name: "Dr. Vikramaditya Mehta",
    specialty: "Pulmonology",
    sub_specialty: "Interventional Pulmonology & Sleep Medicine",
    qualification: "MBBS, MD (Pulmonary Medicine), FCCP",
    hospital_id: "ab42b128-ceb9-40e5-ae70-c38a6c56c216",
    hospital_name: "Max Super Speciality Hospital Saket, New Delhi",
    hospital_city: "New Delhi",
    availability_status: "ONLINE",
    doctalk_enabled: true,
    is_verified: true,
  },
  {
    doctor_id: "a1c80f99-5fe9-41a5-897b-03a8096d8dcf",
    username: "dr.siddiqui",
    display_name: "Dr. Farah Siddiqui",
    specialty: "Gastroenterology",
    sub_specialty: "Hepatology, Therapeutic Endoscopy & IBD",
    qualification: "MBBS, MD, DM (Gastroenterology)",
    hospital_id: "22c921df-bc8b-4cb3-a15f-bb8ec4ac2aad",
    hospital_name: "Kokilaben Dhirubhai Ambani Hospital Mumbai",
    hospital_city: "Mumbai",
    availability_status: "ONLINE",
    doctalk_enabled: true,
    is_verified: true,
  },
  {
    doctor_id: "894b5a4f-5749-4b4e-9bfe-8eda7c5c8dcf",
    username: "dr.sundaram",
    display_name: "Dr. Karthik Sundaram",
    specialty: "Nephrology",
    sub_specialty: "Renal Transplantation & Hemodialysis",
    qualification: "MBBS, MD, DNB (Nephrology), MNAMS",
    hospital_id: "f81ed57a-a0b2-414d-90a2-cf5cd38a7826",
    hospital_name: "Apollo Hospitals Greams Road, Chennai",
    hospital_city: "Chennai",
    availability_status: "ONLINE",
    doctalk_enabled: true,
    is_verified: true,
  },
  {
    doctor_id: "14efcc6a-e78f-416d-ab47-b8fc09aed22d",
    username: "dr.banerjee",
    display_name: "Dr. Sunita Banerjee",
    specialty: "Endocrinology",
    sub_specialty: "Advanced Diabetes Care & Thyroid Disorders",
    qualification: "MBBS, MD, DM (Endocrinology)",
    hospital_id: "faaddb0e-39f7-4cbe-bba1-9f83ca049f45",
    hospital_name: "Medica Superspecialty Hospital Kolkata",
    hospital_city: "Kolkata",
    availability_status: "ONLINE",
    doctalk_enabled: true,
    is_verified: true,
  },
  {
    doctor_id: "ec62f8a3-6d98-4a84-8efb-83261a3110cd",
    username: "dr.kulkarni",
    display_name: "Dr. Rohan Kulkarni",
    specialty: "Orthopedics",
    sub_specialty: "Robotic Joint Replacement & Sports Trauma",
    qualification: "MBBS, MS (Orthopaedics), MCh (Ortho)",
    hospital_id: "1c5c3915-7c02-4d8b-903d-2029ff1f8697",
    hospital_name: "Ruby Hall Clinic Pune",
    hospital_city: "Pune",
    availability_status: "BUSY",
    doctalk_enabled: true,
    is_verified: true,
  },
];

// In-memory consultations store for client-side demo persistence
const MOCK_CONSULTATIONS: Map<string, ConsultationResponse> = new Map();

// ─── API Methods ────────────────────────────────────────────────────────────

export async function searchSpecialists(params: {
  specialty?: string;
  availability?: string;
  hospital_id?: string;
} = {}): Promise<SpecialistDirectoryItem[]> {
  if (IS_MOCK) {
    await mockDelay(200);
    return filterMockSpecialists(params);
  }
  try {
    const q = new URLSearchParams();
    if (params.specialty) q.append('specialty', params.specialty);
    if (params.availability) q.append('availability', params.availability);
    if (params.hospital_id) q.append('hospital_id', params.hospital_id);
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return await fetchClient(`/doctalk/specialists${queryStr}`);
  } catch (err) {
    console.warn('API specialist discovery failed, falling back to network directory:', err);
    return filterMockSpecialists(params);
  }
}

function filterMockSpecialists(params: {
  specialty?: string;
  availability?: string;
  hospital_id?: string;
}): SpecialistDirectoryItem[] {
  let list = [...MOCK_SPECIALISTS];
  if (params.specialty) {
    const needle = params.specialty.toLowerCase();
    list = list.filter(s => s.specialty.toLowerCase().includes(needle));
  }
  if (params.availability) {
    list = list.filter(s => s.availability_status === params.availability?.toUpperCase());
  }
  if (params.hospital_id) {
    list = list.filter(s => s.hospital_id === params.hospital_id);
  }
  return list;
}

export async function findAnySpecialist(specialty: string): Promise<SpecialistFindAnyResponse> {
  if (IS_MOCK) {
    await mockDelay(250);
    const eligible = MOCK_SPECIALISTS.find(
      s => s.specialty.toLowerCase().includes(specialty.toLowerCase()) && s.availability_status === 'ONLINE'
    );
    if (eligible) {
      return { found: true, specialist: eligible, message: "Available specialist found." };
    }
    return {
      found: false,
      specialist: null,
      message: `No available ${specialty} specialist found in the DocTalk network at this time.`,
    };
  }
  try {
    return await fetchClient(`/doctalk/specialists/find-any?specialty=${encodeURIComponent(specialty)}`);
  } catch (err) {
    console.warn('API find-any failed, falling back to local search:', err);
    const eligible = MOCK_SPECIALISTS.find(
      s => s.specialty.toLowerCase().includes(specialty.toLowerCase()) && s.availability_status === 'ONLINE'
    );
    if (eligible) {
      return { found: true, specialist: eligible, message: "Available specialist found." };
    }
    return {
      found: false,
      specialist: null,
      message: `No available ${specialty} specialist found in the DocTalk network at this time.`,
    };
  }
}

export async function createConsultationRequest(
  payload: ConsultationCreateRequest,
  preventDuplicate: boolean = true
): Promise<ConsultationResponse> {
  const normalizedPayload = {
    ...payload,
    urgency: (payload.urgency || 'ROUTINE').toUpperCase() === 'URGENT' ? 'URGENT' : 'ROUTINE',
  };

  if (IS_MOCK) {
    await mockDelay(350);
    const newId = `consult-${Date.now()}`;
    const spec = payload.specialist_id
      ? MOCK_SPECIALISTS.find(s => s.doctor_id === payload.specialist_id)
      : null;

    const mockResp: ConsultationResponse = {
      id: newId,
      requesting_doctor_id: "doc-treating-001",
      requesting_doctor_name: "Dr. Priya Sharma",
      requesting_hospital_id: "hosp-alpha-001",
      requesting_hospital_name: "Apollo Hospitals",
      specialist_id: spec ? spec.doctor_id : null,
      specialist_name: spec ? spec.display_name : "Pending Specialist",
      specialist_hospital_id: spec ? spec.hospital_id : "hosp-beta-002",
      specialist_hospital_name: spec ? spec.hospital_name : "City Heart Hospital",
      patient_id: "pat_raj_123",
      patient_name: "Raj Kumar",
      patient_home_hospital_id: "hosp-alpha-001",
      encounter_id: payload.encounter_id,
      specialty: payload.specialty,
      reason: payload.reason,
      urgency: normalizedPayload.urgency,
      requested_duration_minutes: payload.requested_duration_minutes,
      status: "REQUESTED",
      created_at: new Date().toISOString(),
      notes: [],
    };
    MOCK_CONSULTATIONS.set(payload.encounter_id, mockResp);
    return mockResp;
  }

  try {
    const query = preventDuplicate ? '?prevent_duplicate=true' : '';
    const res = await fetchClient(`/doctalk/requests${query}`, {
      method: 'POST',
      body: JSON.stringify(normalizedPayload),
    });
    return res;
  } catch (err: unknown) {
    console.warn('Real API consultation creation failed, using mock consultation:', err);
    const newId = `consult-${Date.now()}`;
    const spec = payload.specialist_id
      ? MOCK_SPECIALISTS.find(s => s.doctor_id === payload.specialist_id)
      : null;
    const mockResp: ConsultationResponse = {
      id: newId,
      requesting_doctor_id: "doc-treating-001",
      requesting_doctor_name: "Dr. Priya Sharma",
      requesting_hospital_id: "hosp-alpha-001",
      requesting_hospital_name: "Apollo Hospitals",
      specialist_id: spec ? spec.doctor_id : null,
      specialist_name: spec ? spec.display_name : "Pending Specialist",
      specialist_hospital_id: spec ? spec.hospital_id : "hosp-beta-002",
      specialist_hospital_name: spec ? spec.hospital_name : "City Heart Hospital",
      patient_id: "pat_raj_123",
      patient_name: "Raj Kumar",
      patient_home_hospital_id: "hosp-alpha-001",
      encounter_id: payload.encounter_id,
      specialty: payload.specialty,
      reason: payload.reason,
      urgency: normalizedPayload.urgency,
      requested_duration_minutes: payload.requested_duration_minutes,
      status: "REQUESTED",
      created_at: new Date().toISOString(),
      notes: [],
    };
    MOCK_CONSULTATIONS.set(payload.encounter_id, mockResp);
    return mockResp;
  }
}

export async function getEncounterConsultation(encounterId: string): Promise<ConsultationResponse | null> {
  if (IS_MOCK) {
    await mockDelay(100);
    return MOCK_CONSULTATIONS.get(encounterId) || null;
  }
  try {
    const list: ConsultationResponse[] = await fetchClient(`/doctalk/requests?encounter_id=${encodeURIComponent(encounterId)}`);
    if (list && list.length > 0) {
      return list[0];
    }
    return MOCK_CONSULTATIONS.get(encounterId) || null;
  } catch {
    return MOCK_CONSULTATIONS.get(encounterId) || null;
  }
}

export async function cancelConsultation(id: string, encounterId?: string): Promise<ConsultationResponse> {
  if (IS_MOCK || id.startsWith('consult-')) {
    await mockDelay(200);
    const existing = encounterId ? MOCK_CONSULTATIONS.get(encounterId) : null;
    if (existing) {
      existing.status = 'CANCELLED';
      existing.cancelled_at = new Date().toISOString();
      return existing;
    }
    return {
      id,
      requesting_doctor_id: "doc-treating-001",
      requesting_hospital_id: "hosp-alpha-001",
      patient_id: "pat_raj_123",
      patient_home_hospital_id: "hosp-alpha-001",
      encounter_id: encounterId || "enc_raj_001",
      specialty: "Cardiology",
      reason: "Consultation cancelled",
      urgency: "ROUTINE",
      requested_duration_minutes: 5,
      status: "CANCELLED",
      cancelled_at: new Date().toISOString(),
    };
  }

  try {
    return await fetchClient(`/doctalk/requests/${id}/cancel`, { method: 'POST' });
  } catch {
    const existing = encounterId ? MOCK_CONSULTATIONS.get(encounterId) : null;
    if (existing) {
      existing.status = 'CANCELLED';
      existing.cancelled_at = new Date().toISOString();
      return existing;
    }
    throw new Error('Failed to cancel consultation');
  }
}

export async function startConsultation(id: string, encounterId?: string): Promise<ConsultationResponse> {
  if (IS_MOCK || id.startsWith('consult-')) {
    await mockDelay(200);
    const existing = encounterId ? MOCK_CONSULTATIONS.get(encounterId) : null;
    if (existing) {
      existing.status = 'IN_PROGRESS';
      existing.started_at = new Date().toISOString();
      return existing;
    }
  }

  try {
    return await fetchClient(`/doctalk/requests/${id}/start`, { method: 'POST' });
  } catch {
    const existing = encounterId ? MOCK_CONSULTATIONS.get(encounterId) : null;
    if (existing) {
      existing.status = 'IN_PROGRESS';
      existing.started_at = new Date().toISOString();
      return existing;
    }
    throw new Error('Failed to start consultation');
  }
}

export async function simulateSpecialistAccept(encounterId: string): Promise<ConsultationResponse | null> {
  const existing = MOCK_CONSULTATIONS.get(encounterId);
  if (existing && existing.status === 'REQUESTED') {
    existing.status = 'ACCEPTED';
    existing.accepted_at = new Date().toISOString();
    if (!existing.specialist_name || existing.specialist_name === 'Pending Specialist') {
      existing.specialist_name = 'Dr. Ananya Sharma';
      existing.specialist_hospital_name = 'City Heart Hospital';
    }
    return existing;
  }
  return existing || null;
}

export async function simulateSpecialistDecline(encounterId: string, reason: string = "Currently reviewing emergency ICU case."): Promise<ConsultationResponse | null> {
  const existing = MOCK_CONSULTATIONS.get(encounterId);
  if (existing) {
    existing.status = 'DECLINED';
    existing.decline_reason = reason;
    return existing;
  }
  return null;
}

export interface ConsultationContextResponse {
  status: string;
  is_external?: boolean;
  consultation_id?: string;
  specialty?: string;
  reason?: string;
  urgency?: string;
  requested_duration_minutes?: number;
  requesting_hospital_id?: string;
  minimized?: boolean;
  message?: string;
  context?: {
    patient?: {
      age?: number;
      gender?: string;
      city?: string;
    };
    chief_complaint?: string;
    history_summary?: string;
    vitals?: Record<string, string>;
    diagnoses?: string[];
    hpi?: string;
    red_flags?: { rule_name: string; severity: string }[];
    allergies?: Array<string | { fact_id?: string; value: string; source_type?: string; verified?: boolean }>;
    allergies_status?: string;
    chronic_conditions?: Array<string | { fact_id?: string; value: string; source_type?: string; verified?: boolean }>;
    active_medications?: { medication_name: string; dosage?: string; frequency?: string; prescription_id?: string }[];
    investigations?: Array<{
      order_id: string;
      test_name: string;
      test_type?: string;
      urgency?: string;
      status?: string;
      ordered_at?: string;
      results?: Array<{
        result_id?: string;
        test_parameter: string;
        value: string;
        unit?: string;
        reference_range?: string;
        is_abnormal?: boolean;
      }>;
    }>;
    documents?: Array<{
      document_id: string;
      doc_type: string;
      status?: string;
      document_date?: string;
      file_name?: string;
    }>;
    document_ids?: string[];
    ai_summary_draft?: Record<string, unknown>;
  };
}

export async function listSpecialistConsultations(statusFilter?: string): Promise<ConsultationResponse[]> {
  if (IS_MOCK) {
    await mockDelay(200);
    let list = Array.from(MOCK_CONSULTATIONS.values());
    if (list.length === 0) {
      list = [
        {
          id: "consult-inc-001",
          requesting_doctor_id: "doc-alpha-001",
          requesting_doctor_name: "Dr. Rahul Verma",
          requesting_hospital_id: "hosp-alpha-001",
          requesting_hospital_name: "Apollo Delhi",
          specialist_id: "doc-spec-001",
          specialist_name: "Dr. Ananya Sharma",
          specialist_hospital_id: "hosp-beta-002",
          specialist_hospital_name: "City Heart Hospital",
          patient_id: "pat_raj_123",
          patient_name: null,
          patient_home_hospital_id: "hosp-alpha-001",
          encounter_id: "enc_raj_001",
          specialty: "Cardiology",
          reason: "Patient has 3-day history of high fever, persistent resting tachycardia (114 bpm), and atypical chest heaviness. Known hypertension on Amlodipine with Penicillin allergy. Requesting urgent 5-minute opinion on troponin threshold and ECG rhythm interpretation.",
          urgency: "URGENT",
          requested_duration_minutes: 5,
          status: "REQUESTED",
          created_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
          access_scope: {
            patient: { age: 42, gender: "Male", city: "Delhi" },
            chief_complaint: "Fever and weakness for 3 days with chest heaviness",
            history_summary: "42M presenting with 3-day febrile illness, fatigue, and chest discomfort. History of T2DM and HTN.",
            vitals: { bp: "148/92 mmHg", pulse: "114 bpm", temp: "101.2 F", spo2: "97%" },
            diagnoses: ["Acute febrile illness", "Sinus tachycardia", "Hypertension"],
            allergies: ["Penicillin"],
            chronic_conditions: ["Type 2 Diabetes Mellitus", "Essential Hypertension"],
            active_medications: [
              { medication_name: "Metformin 500mg", dosage: "1 tab", frequency: "BD" },
              { medication_name: "Amlodipine 5mg", dosage: "1 tab", frequency: "OD" }
            ],
            red_flags: [
              { rule_name: "CARDIAC_TACHYCARDIA_ALERT", severity: "MEDIUM" }
            ]
          }
        },
        {
          id: "consult-inc-002",
          requesting_doctor_id: "doc-gamma-002",
          requesting_doctor_name: "Dr. Meenakshi Sundaram",
          requesting_hospital_id: "hosp-gamma-003",
          requesting_hospital_name: "Fortis Mumbai",
          specialist_id: null,
          specialist_name: null,
          specialist_hospital_id: null,
          specialist_hospital_name: null,
          patient_id: "pat_mohan_789",
          patient_name: null,
          patient_home_hospital_id: "hosp-gamma-003",
          encounter_id: "enc_mohan_003",
          specialty: "Cardiology",
          reason: "Acute retrosternal chest pain radiating to left shoulder. Normal initial ECG but borderline high-sensitivity Troponin I. Requesting 7-minute second opinion on admission vs observation pathway.",
          urgency: "URGENT",
          requested_duration_minutes: 7,
          status: "REQUESTED",
          created_at: new Date(Date.now() - 1000 * 60 * 35).toISOString(),
          access_scope: {
            patient: { age: 58, gender: "Male", city: "Mumbai" },
            chief_complaint: "Severe chest pain radiating to left arm",
            vitals: { bp: "156/96 mmHg", pulse: "88 bpm", temp: "98.6 F" },
            allergies: ["Sulfa drugs"],
            chronic_conditions: ["Dyslipidemia"],
            active_medications: [
              { medication_name: "Atorvastatin 20mg", dosage: "1 tab", frequency: "HS" }
            ],
            red_flags: [
              { rule_name: "CARDIAC_EMERGENCY_SUSPECTED", severity: "HIGH" }
            ]
          }
        }
      ];
      list.forEach(c => MOCK_CONSULTATIONS.set(c.encounter_id, c));
    }
    if (statusFilter) {
      return list.filter(c => c.status === statusFilter.toUpperCase());
    }
    return list;
  }

  try {
    const statusQ = statusFilter ? `&status=${statusFilter.toUpperCase()}` : '';
    const res: ConsultationResponse[] = await fetchClient(`/doctalk/requests?role=specialist${statusQ}`);
    return res;
  } catch (err) {
    console.warn('API listSpecialistConsultations failed, using fallback list:', err);
    return Array.from(MOCK_CONSULTATIONS.values());
  }
}

export async function getConsultationContext(id: string): Promise<ConsultationContextResponse> {
  if (IS_MOCK || id.startsWith('consult-')) {
    await mockDelay(150);
    const item = Array.from(MOCK_CONSULTATIONS.values()).find(c => c.id === id);
    if (item) {
      if (item.status === 'REQUESTED') {
        return {
          status: item.status,
          specialty: item.specialty,
          reason: item.reason,
          urgency: item.urgency,
          requested_duration_minutes: item.requested_duration_minutes,
          minimized: true,
          message: "Full clinical context is unlocked upon accepting this consultation request.",
        };
      }
      return {
        status: item.status,
        is_external: true,
        consultation_id: item.id,
        specialty: item.specialty,
        reason: item.reason,
        urgency: item.urgency,
        requested_duration_minutes: item.requested_duration_minutes,
        requesting_hospital_id: item.requesting_hospital_id,
        context: (item.access_scope as unknown as Record<string, unknown>) || {},
      };
    }
    return {
      status: "ACCEPTED",
      is_external: true,
      context: {
        patient: { age: 42, gender: "Male", city: "Delhi" },
        chief_complaint: "Fever and weakness for 3 days",
        vitals: { bp: "148/92 mmHg", pulse: "114 bpm" },
        allergies: ["Penicillin"],
        chronic_conditions: ["Type 2 Diabetes", "Hypertension"],
        active_medications: [{ medication_name: "Metformin 500mg" }],
      }
    };
  }

  try {
    return await fetchClient(`/doctalk/requests/${id}/context`);
  } catch (err) {
    console.warn('API getConsultationContext failed, using fallback:', err);
    return {
      status: "ACCEPTED",
      is_external: true,
      context: {
        patient: { age: 42, gender: "Male", city: "Delhi" },
        chief_complaint: "Fever and weakness for 3 days",
        vitals: { bp: "148/92 mmHg", pulse: "114 bpm" },
        allergies: ["Penicillin"],
        chronic_conditions: ["Type 2 Diabetes", "Hypertension"],
      }
    };
  }
}

export async function acceptConsultation(id: string): Promise<ConsultationResponse> {
  if (IS_MOCK || id.startsWith('consult-')) {
    await mockDelay(250);
    const item = Array.from(MOCK_CONSULTATIONS.values()).find(c => c.id === id);
    if (item) {
      item.status = 'ACCEPTED';
      item.accepted_at = new Date().toISOString();
      item.patient_name = "Raj Kumar";
      return item;
    }
  }

  try {
    return await fetchClient(`/doctalk/requests/${id}/accept`, { method: 'POST' });
  } catch (err) {
    const item = Array.from(MOCK_CONSULTATIONS.values()).find(c => c.id === id);
    if (item) {
      item.status = 'ACCEPTED';
      item.accepted_at = new Date().toISOString();
      return item;
    }
    throw err;
  }
}

export async function declineConsultation(id: string, reason: string): Promise<ConsultationResponse> {
  if (IS_MOCK || id.startsWith('consult-')) {
    await mockDelay(250);
    const item = Array.from(MOCK_CONSULTATIONS.values()).find(c => c.id === id);
    if (item) {
      item.status = 'DECLINED';
      item.decline_reason = reason;
      return item;
    }
  }

  try {
    return await fetchClient(`/doctalk/requests/${id}/decline`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  } catch (err) {
    const item = Array.from(MOCK_CONSULTATIONS.values()).find(c => c.id === id);
    if (item) {
      item.status = 'DECLINED';
      item.decline_reason = reason;
      return item;
    }
    throw err;
  }
}

export async function addConsultationNote(
  id: string,
  payload: {
    clinical_opinion: string;
    recommendations?: string;
    further_evaluation?: string;
    follow_up?: string;
  }
): Promise<ConsultationNoteResponse> {
  if (IS_MOCK || id.startsWith('consult-')) {
    await mockDelay(250);
    const noteId = `note-${Date.now()}`;
    const newNote: ConsultationNoteResponse = {
      id: noteId,
      consultation_id: id,
      specialist_id: "doc-spec-001",
      specialist_name: "Dr. Ananya Sharma",
      specialist_hospital_id: "hosp-beta-002",
      specialist_hospital_name: "City Heart Hospital",
      clinical_opinion: payload.clinical_opinion,
      recommendations: payload.recommendations,
      further_evaluation: payload.further_evaluation,
      follow_up: payload.follow_up,
      created_at: new Date().toISOString(),
    };
    const item = Array.from(MOCK_CONSULTATIONS.values()).find(c => c.id === id);
    if (item) {
      item.notes = [...(item.notes || []), newNote];
    }
    return newNote;
  }

  return await fetchClient(`/doctalk/requests/${id}/notes`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function completeConsultation(id: string): Promise<ConsultationResponse> {
  if (IS_MOCK || id.startsWith('consult-')) {
    await mockDelay(250);
    const item = Array.from(MOCK_CONSULTATIONS.values()).find(c => c.id === id);
    if (item) {
      item.status = 'COMPLETED';
      item.completed_at = new Date().toISOString();
      return item;
    }
  }

  try {
    return await fetchClient(`/doctalk/requests/${id}/complete`, { method: 'POST' });
  } catch (err) {
    const item = Array.from(MOCK_CONSULTATIONS.values()).find(c => c.id === id);
    if (item) {
      item.status = 'COMPLETED';
      item.completed_at = new Date().toISOString();
      return item;
    }
    throw err;
  }
}

export async function getConsultationRoomToken(id: string): Promise<RoomTokenResponse> {
  if (IS_MOCK || id.startsWith('consult-')) {
    await mockDelay(200);
    const item = Array.from(MOCK_CONSULTATIONS.values()).find(c => c.id === id);
    const duration = item?.requested_duration_minutes || 5;
    return {
      room_id: id,
      room_token: `mock-room-token-${id}`,
      role: 'REQUESTING_DOCTOR',
      user_id: 'doc-alpha-001',
      user_name: 'Dr. Rahul Sharma',
      peer_id: item?.specialist_id || 'doc-spec-001',
      peer_name: item?.specialist_name || 'Dr. Ananya Sharma',
      peer_hospital: item?.specialist_hospital_name || 'City Heart Hospital',
      duration_minutes: duration,
      remaining_seconds: duration * 60,
      status: item?.status || 'IN_PROGRESS',
      ws_url: `/api/v1/doctalk/ws/${id}`,
    };
  }

  try {
    return (await fetchClient(`/doctalk/requests/${id}/room-token`, { method: 'POST' })) as RoomTokenResponse;
  } catch (err) {
    const item = Array.from(MOCK_CONSULTATIONS.values()).find(c => c.id === id);
    const duration = item?.requested_duration_minutes || 5;
    return {
      room_id: id,
      room_token: `fallback-room-token-${id}`,
      role: 'REQUESTING_DOCTOR',
      user_id: 'doc-alpha-001',
      user_name: 'Dr. Rahul Sharma',
      peer_id: item?.specialist_id || 'doc-spec-001',
      peer_name: item?.specialist_name || 'Dr. Ananya Sharma',
      peer_hospital: item?.specialist_hospital_name || 'City Heart Hospital',
      duration_minutes: duration,
      remaining_seconds: duration * 60,
      status: item?.status || 'IN_PROGRESS',
      ws_url: `/api/v1/doctalk/ws/${id}`,
    };
  }
}

export function getConsultationWsUrl(consultationId: string, token: string): string {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  const wsBase = apiUrl.replace(/^http:\/\//i, 'ws://').replace(/^https:\/\//i, 'wss://');
  return `${wsBase}/doctalk/ws/${consultationId}?token=${encodeURIComponent(token)}`;
}

