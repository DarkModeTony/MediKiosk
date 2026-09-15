import { fetchApi } from "./client";

export interface PatientRegistration {
  name: string;
  date_of_birth?: string;
  gender: string;
  language: string;
  mobile_number?: string;
}

export interface PatientResponse {
  patient_id: string;
}

export async function registerPatient(data: PatientRegistration): Promise<PatientResponse> {
  try {
    return await fetchApi<PatientResponse>("/patients/register", {
      method: "POST",
      body: JSON.stringify({ demographic_data: data, consent: true }),
    });
  } catch (e) {
    if (process.env.NEXT_PUBLIC_DATA_MODE !== "mock") throw e;
    console.warn("Backend unavailable, using mock patient registration");
    return {
      patient_id: "pat_raj_123", // Canonical Demo ID
    };
  }
}

export async function searchPatient(query: string): Promise<PatientResponse> {
  try {
    return await fetchApi<PatientResponse>(`/patients/search?q=${encodeURIComponent(query)}`);
  } catch (e) {
    const isDemoQuery = ["patient_001", "pat_raj_123", "9000000001", "raj"].includes(query.trim().toLowerCase());
    if (isDemoQuery || process.env.NEXT_PUBLIC_DATA_MODE === "mock") {
      console.warn("Using fallback demo patient search for:", query);
      return { patient_id: "b54f64df-1582-4762-86ef-dbc1c70c2916" };
    }
    throw e;
  }
}
