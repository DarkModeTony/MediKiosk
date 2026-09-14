import { fetchApi } from "./client";

export interface Option {
  id: string;
  label: string;
}

export interface Question {
  id: string;
  text: string;
  category: string;
  input_type: string;
  clinical_field: string;
  options: Option[] | null;
  required: boolean;
}

export interface Fact {
  field: string;
  value: unknown;
  state: string;
}

export interface RedFlag {
  id: string;
  rule_name: string;
  evidence: unknown;
  severity: string;
}

export interface ClinicalState {
  encounter_id: string;
  status: string;
  current_pathway: string | null;
  current_question_id: string | null;
  facts: Record<string, Fact>;
  new_red_flags: RedFlag[];
  completed: boolean;
}

export interface AnswerPayload {
  question_id: string;
  raw_transcript?: string;
  selected_option_id?: string;
}

export async function startClinicalIntake(sessionToken: string): Promise<ClinicalState> {
  try {
    return await fetchApi<ClinicalState>(`/clinical/start?session_token=${sessionToken}`, {
      method: "POST"
    });
  } catch (e) {
    if (process.env.NEXT_PUBLIC_DATA_MODE !== "mock") throw e;
    console.warn("Backend unavailable, using mock clinical start");
    return {
      encounter_id: "enc_raj_001",
      status: "IN_PROGRESS",
      current_pathway: "HPI",
      current_question_id: "chief_complaint_initial",
      facts: {},
      new_red_flags: [],
      completed: false
    };
  }
}

export async function getClinicalState(sessionToken: string): Promise<ClinicalState> {
  try {
    return await fetchApi<ClinicalState>(`/clinical/state?session_token=${sessionToken}`);
  } catch (e) {
    if (process.env.NEXT_PUBLIC_DATA_MODE !== "mock") throw e;
    console.warn("Backend unavailable, using mock clinical state");
    return {
      encounter_id: "enc_raj_001",
      status: "COMPLETED",
      current_pathway: null,
      current_question_id: null,
      facts: {
        CHIEF_COMPLAINT: { field: "CHIEF_COMPLAINT", value: "Chest pain", state: "COLLECTED" },
        ONSET: { field: "ONSET", value: "Today morning", state: "COLLECTED" },
        PAST_MEDICAL_HISTORY: { field: "PAST_MEDICAL_HISTORY", value: "Hypertension", state: "COLLECTED" }
      },
      new_red_flags: [
        { id: "rf_1", rule_name: "CHEST_PAIN_SUDDEN_ONSET", severity: "HIGH", evidence: {"CHIEF_COMPLAINT": "Chest pain", "ONSET": "Today morning"} }
      ],
      completed: true
    };
  }
}

export async function submitClinicalAnswer(sessionToken: string, payload: AnswerPayload): Promise<ClinicalState> {
  try {
    return await fetchApi<ClinicalState>(`/clinical/answer?session_token=${sessionToken}`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  } catch (e) {
    if (process.env.NEXT_PUBLIC_DATA_MODE !== "mock") throw e;
    console.warn("Backend unavailable, using mock clinical answer");
    // Immediately complete for demo speed
    return {
      encounter_id: "enc_raj_001",
      status: "COMPLETED",
      current_pathway: null,
      current_question_id: null,
      facts: {
        CHIEF_COMPLAINT: { field: "CHIEF_COMPLAINT", value: payload.raw_transcript || "Chest pain", state: "COLLECTED" }
      },
      new_red_flags: [
        { id: "rf_1", rule_name: "CHEST_PAIN_SUDDEN_ONSET", severity: "HIGH", evidence: {"CHIEF_COMPLAINT": "Chest pain", "ONSET": "Today morning"} }
      ],
      completed: true
    };
  }
}

export async function getQuestionDetails(pathway: string, questionId: string): Promise<Question> {
  try {
    return await fetchApi<Question>(`/clinical/question/${pathway}/${questionId}`);
  } catch (e) {
    if (process.env.NEXT_PUBLIC_DATA_MODE !== "mock") throw e;
    console.warn("Backend unavailable, using mock question details");
    return {
      id: "chief_complaint_initial",
      text: "What brings you here today?",
      category: "HPI",
      input_type: "VOICE_ONLY",
      clinical_field: "chief_complaint",
      options: null,
      required: true
    };
  }
}
