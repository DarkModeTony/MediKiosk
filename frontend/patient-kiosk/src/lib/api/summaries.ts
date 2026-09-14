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

export async function getSummary(encounterId: string): Promise<{ summary_id: string, latest_version: ClinicalSummary, status: string }> {
  try {
    return await fetchApi(`/summaries/encounters/${encounterId}/summary`);
  } catch (e) {
    if (process.env.NEXT_PUBLIC_DATA_MODE !== "mock") throw e;
    console.warn("Backend unavailable, using mock summary get");
    return {
      summary_id: "sum_raj_999",
      status: "AI_DRAFT",
      latest_version: {
        id: "sum_raj_999",
        encounter_id: "enc_raj_001",
        version: 1,
        generated_at: new Date().toISOString(),
        provider: "MediPlatform AI",
        status: "AI_DRAFT",
        structured_sections: [
          { title: "CHIEF COMPLAINT", content: "Chest pain" },
          { title: "RED FLAGS", content: "HIGH: CHEST_PAIN_SUDDEN_ONSET" }
        ],
        source_references: []
      }
    };
  }
}
