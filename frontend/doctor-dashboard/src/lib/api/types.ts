export interface Patient {
  id: string;
  name: string;
  age: number;
  gender: string;
  created_at: string;
}

export interface Encounter {
  id: string;
  patient_id: string;
  status: string;
  priority: 'HIGH' | 'MEDIUM' | 'NORMAL';
  chief_complaint: string;
  created_at: string;
  updated_at: string;
}

export interface QueueItem extends Patient, Encounter {
  arrival: string;
}

export interface FactState {
  state: 'COLLECTED' | 'NOT_ASKED' | 'UNKNOWN';
  value: string | null;
}

export interface ClinicalState {
  status: 'IN_PROGRESS' | 'COMPLETED';
  encounter_id: string;
  facts: Record<string, FactState>;
}

export interface RedFlag {
  rule_name: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  evidence: Record<string, string>;
  status: 'ACTIVE' | 'RESOLVED';
}

export interface SummarySection {
  title: string;
  content: string;
  section_type: string;
}

export interface SummaryVersion {
  structured_sections: SummarySection[];
}

export interface ClinicalSummary {
  summary_id: string;
  status: 'AI_DRAFT' | 'DOCTOR_EDITED' | 'DOCTOR_VERIFIED';
  latest_version: SummaryVersion;
  original_draft: SummaryVersion;
}

export interface Medication {
  name: string;
  dose: string;
  frequency: string;
}

export interface LabResult {
  test: string;
  result: string;
  unit: string;
  reference: string;
  status: string;
}

export interface DocumentEntity {
  type: string;
  value: Medication | LabResult | Record<string, unknown>;
  status: 'AI_EXTRACTED' | 'PATIENT_CORRECTED';
  source_text: string;
}

export interface TimelineEvent {
  date: string;
  date_known: boolean;
  type: 'DOCUMENT' | 'ENCOUNTER';
  document_id: string;
  document_type: string;
  entities: DocumentEntity[];
}

export interface PatientTimeline {
  patient_id: string;
  events: TimelineEvent[];
}

export interface SourceReference {
  document_id: string;
  text: string;
  page: number;
}
