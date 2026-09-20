import { fetchApi } from "./client";

export interface SummarySection {
  title: string;
  content: string;
}

export interface SourceReference {
  source_type: string;
  source_id: string;
  document_id?: string;
  page_number?: number;
  source_text?: string;
  fact: string;
  confidence?: number;
}

export interface ClinicalSummary {
  id: string;
  encounter_id: string;
  version: number;
  generated_at: string;
  provider: string;
  status: string;
  structured_sections: SummarySection[];
  source_references: SourceReference[];
}

export async function generateSummary(encounterId: string): Promise<{ status: string, summary_id: string }> {
  try {
    return await fetchApi(`/summaries/generate`, {
      method: "POST",
      body: JSON.stringify({ encounter_id: encounterId }),
    });
  } catch (e) {
    if (process.env.NEXT_PUBLIC_DATA_MODE !== "mock") throw e;
    console.warn("Backend unavailable, using mock summary generate");
    return { status: "GENERATED", summary_id: "sum_raj_999" };
  }
}

export async function getKioskSummary(sessionToken: string): Promise<{ summary_id: string, latest_version: ClinicalSummary, status: string, encounter_id: string, patient_id: string }> {
  return await fetchApi(`/kiosk/summary`, {
    headers: {
      "X-Session-Token": sessionToken,
    },
  });
}

export async function generateKioskSummary(sessionToken: string): Promise<{ status: string, summary_id: string, encounter_id: string }> {
  return await fetchApi(`/kiosk/summary/generate`, {
    method: "POST",
    headers: {
      "X-Session-Token": sessionToken,
    },
  });
}

export async function getSummary(encounterId?: string, sessionToken?: string): Promise<{ summary_id: string, latest_version: ClinicalSummary, status: string }> {
  if (sessionToken) {
    try {
      return await getKioskSummary(sessionToken);
    } catch (e) {
      if (!encounterId) throw e;
      console.warn("Kiosk session summary fetch failed, falling back to encounter ID:", e);
    }
  }

  if (!encounterId) {
    throw new Error("No encounter ID or session token provided");
  }

  try {
    return await fetchApi(`/summaries/encounters/${encounterId}/summary`);
  } catch (e) {
    // Only use mock fallback if explicitly in mock mode AND request is for demo encounter
    if (process.env.NEXT_PUBLIC_DATA_MODE === "mock" && encounterId === "enc_raj_001") {
      console.warn("Using demo summary fallback for mock encounter:", encounterId);
      return {
        summary_id: "sum_raj_999",
        status: "AI_DRAFT",
        latest_version: {
          id: "sum_raj_999",
          encounter_id: encounterId,
          version: 1,
          generated_at: new Date().toISOString(),
          provider: "Gemini AI (MediPlatform)",
          status: "AI_DRAFT",
          structured_sections: [
            { title: "CHIEF COMPLAINT", content: "Fever (101.2°F) and generalised weakness for 3 days." },
            { title: "HISTORY OF PRESENT ILLNESS", content: "Mr Raj Kumar, 42M, office employee from Delhi. 3-day history of low-grade fever (101.2°F), generalised weakness, headache, and reduced appetite. Known T2DM and Hypertension — consider secondary infection given diabetic background." },
            { title: "RELEVANT MEDICAL HISTORY", content: "• Type 2 Diabetes Mellitus — April 2020, active. HbA1c 7.4% (Feb 2026).\n• Hypertension — July 2022, active. BP today 148/92 mmHg.\n• Surgical: Appendectomy (2015, for acute appendicitis)." },
            { title: "FAMILY HISTORY", content: "Father: Hypertension. Mother: Type 2 Diabetes." },
            { title: "SOCIAL HISTORY", content: "Non-smoker. Occasional alcohol. Office employee. Preferred language: Hindi." },
            { title: "ALLERGIES", content: "⚠ Penicillin → Skin rash (Moderate severity). Confirmed at kiosk intake. Avoid all penicillin-class antibiotics." },
            { title: "CURRENT MEDICATIONS", content: "1. Metformin 500 mg — Twice daily (active)\n2. Amlodipine 5 mg — Once daily (active)" },
            { title: "VITALS", content: "Temperature: 101.2°F | BP: 148/92 mmHg | HR: 96 bpm | SpO₂: 98%" },
            { title: "ACTIVE RED FLAGS", content: "MEDIUM — ELEVATED_BP_KNOWN_HYPERTENSIVE: BP 148/92 mmHg in known hypertensive on Amlodipine 5 mg OD. Review antihypertensive dose." },
            { title: "SUGGESTED WORKUP", content: "• CBC + differential\n• Blood culture (if systemic infection suspected)\n• FBG + HbA1c (glycaemic review)\n• Urine routine & microscopy\n• LFT/RFT baseline (Metformin monitoring)" }
          ],
          source_references: []
        }
      };
    }
    throw e;
  }
}
