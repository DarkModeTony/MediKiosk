// TypeScript definitions for Patient Medical History Longitudinal Profile Schema (v1.0)

export interface PatientDemographics {
  patient_id?: string;
  name?: string;
  date_of_birth?: string;
  age?: number;
  gender?: string;
  blood_group?: string;
}

export interface Allergy {
  allergen: string;
  reaction?: string;
  severity?: "mild" | "moderate" | "severe" | string;
  status?: "active" | "resolved" | "unknown" | string;
  verified?: boolean;
}

export interface ChronicCondition {
  condition: string;
  status?: "active" | "resolved" | string;
  diagnosed_date?: string;
  severity?: string;
  verified?: boolean;
}

export interface PreviousCondition {
  condition: string;
  status?: string;
  year?: number | string;
  verified?: boolean;
}

export interface Surgery {
  procedure: string;
  body_site?: string;
  date?: string;
  reason?: string;
  outcome?: string;
  verified?: boolean;
}

export interface Hospitalization {
  reason: string;
  date?: string;
  duration_days?: number;
  outcome?: string;
}

export interface MedicalHistory {
  allergies: Allergy[];
  chronic_conditions: ChronicCondition[];
  previous_conditions: PreviousCondition[];
  surgeries: Surgery[];
  hospitalizations: Hospitalization[];
}

export interface CurrentMedication {
  name: string;
  dose?: string;
  frequency?: string;
  route?: string;
  reason?: string;
  start_date?: string;
  status?: string;
}

export interface PreviousMedication {
  name: string;
  dose?: string;
  frequency?: string;
  reason?: string;
  status?: string;
}

export interface Medications {
  current: CurrentMedication[];
  previous: PreviousMedication[];
}

export interface EyeDetail {
  present?: boolean | null;
  status: "present" | "absent" | "unknown" | string;
  cause?: string;
  date?: string;
  prosthetic?: boolean;
  vision?: string;
  verified?: boolean;
}

export interface LimbDetail {
  present?: boolean | null;
  status: "present" | "absent" | "unknown" | string;
  prosthetic?: boolean;
  verified?: boolean;
}

export interface AnatomicalStatus {
  eyes: {
    left: EyeDetail;
    right: EyeDetail;
  };
  arms: {
    left: LimbDetail;
    right: LimbDetail;
  };
  legs: {
    left: LimbDetail;
    right: LimbDetail;
  };
  hands: {
    left: LimbDetail;
    right: LimbDetail;
  };
  feet: {
    left: LimbDetail;
    right: LimbDetail;
  };
  other: Record<string, unknown>[];
}

export interface MedicalDevice {
  type?: string;
  name?: string | null;
  body_site?: string | null;
  status?: string;
  since?: string | null;
}

export interface SensoryStatus {
  vision: {
    left_eye?: { status?: string; visual_ability?: string };
    right_eye?: { status?: string; visual_ability?: string };
  };
  hearing: {
    left_ear?: { status?: string };
    right_ear?: { status?: string };
  };
  speech: {
    status?: string;
  };
}

export interface FunctionalStatus {
  mobility: {
    walking?: string;
    walking_aid?: string | null;
    wheelchair?: boolean;
  };
  daily_activities: {
    eating?: string;
    bathing?: string;
    dressing?: string;
    toileting?: string;
  };
}

export interface FamilyHistoryItem {
  condition: string;
  relationship: string;
  status?: string;
}

export interface SocialHistory {
  smoking: {
    status: string;
    verified?: boolean;
  };
  alcohol: {
    status: string;
    verified?: boolean;
  };
  occupation?: string;
  living_situation?: string;
}

export interface ImmunizationItem {
  vaccine: string;
  doses?: number;
  last_dose_date?: string;
}

export interface VitalRecord {
  date?: string;
  height_cm?: number;
  weight_kg?: number;
  blood_pressure?: string;
  heart_rate?: number;
  temperature_c?: number;
  oxygen_saturation?: number;
}

export interface MentalCognitiveStatus {
  cognitive_status?: string;
  known_conditions?: string[];
  communication_needs?: string[];
}

export interface ReproductiveHealth {
  status?: string;
  pregnancy_status?: string;
}

export interface PreviousEncounterRecord {
  encounter_id?: string;
  date?: string;
  chief_complaint?: string;
  summary?: string;
  diagnosis?: string;
  outcome?: string;
}

export interface DocumentRecord {
  document_id?: string;
  type?: string;
  date?: string;
  summary?: string;
}

export interface PatientPreferences {
  preferred_language?: string;
  communication_mode?: string;
  accessibility_needs?: string[];
}

export interface StatementMemory {
  statement: string;
  date?: string;
  source?: string;
  verified?: boolean;
}

export interface ChatbotMemory {
  important_patient_statements: StatementMemory[];
  recent_concerns: Record<string, unknown>[];
  pending_questions: Record<string, unknown>[];
}

export interface Provenance {
  last_updated?: string;
  last_updated_by?: string;
  profile_version?: number;
}

export interface LongitudinalProfile {
  schema_version: "1.0" | string;
  patient: PatientDemographics;
  medical_history: MedicalHistory;
  medications: Medications;
  anatomical_status: AnatomicalStatus;
  medical_devices: MedicalDevice[];
  sensory_status: SensoryStatus;
  functional_status: FunctionalStatus;
  family_history: FamilyHistoryItem[];
  social_history: SocialHistory;
  immunizations: ImmunizationItem[];
  vital_history: VitalRecord[];
  mental_cognitive_status: MentalCognitiveStatus;
  reproductive_health: ReproductiveHealth;
  current_symptoms: unknown[];
  red_flags: unknown[];
  previous_encounters: PreviousEncounterRecord[];
  documents: DocumentRecord[];
  patient_preferences: PatientPreferences;
  chatbot_memory: ChatbotMemory;
  provenance: Provenance;
}
