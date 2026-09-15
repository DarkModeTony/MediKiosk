import { fetchApi } from "./client";

export interface DocumentEntity {
  id: string;
  type: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  value: any;
  confidence: number;
  status: string;
  source_text: string;
}

export interface DocumentDetails {
  id: string;
  doc_type: string;
  status: string;
  document_date?: string;
}

export async function uploadDocument(file: File, docType: string, sessionToken: string) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("doc_type", docType);
  formData.append("session_token", sessionToken);

  const apiBase = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/api\/v1\/?$/, "");
  try {
    const res = await fetch(`${apiBase}/api/v1/documents/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error("Failed to upload document");
    return await res.json();
  } catch (e) {
    if (process.env.NEXT_PUBLIC_DATA_MODE !== "mock") throw e;
    console.warn("Backend unavailable, using mock document upload");
    return { document_id: "doc_raj_01", status: "PENDING_OCR" };
  }
}

export async function triggerOCR(documentId: string) {
  try {
    return await fetchApi(`/documents/${documentId}/ocr`, { method: "POST" });
  } catch (e) {
    if (process.env.NEXT_PUBLIC_DATA_MODE !== "mock") throw e;
    console.warn("Backend unavailable, using mock OCR");
    return { status: "PROCESSING" };
  }
}

export async function getDocumentEntities(documentId: string): Promise<DocumentEntity[]> {
  try {
    return await fetchApi<DocumentEntity[]>(`/documents/${documentId}/entities`);
  } catch (e) {
    if (process.env.NEXT_PUBLIC_DATA_MODE !== "mock") throw e;
    console.warn("Backend unavailable, using mock entities");
    return [
      {
        id: "ent_1",
        type: "MEDICATION",
        value: { name: "Amlodipine", dose: "5 mg", frequency: "once daily" },
        confidence: 0.98,
        status: "AI_EXTRACTED",
        source_text: "Tab Amlodipine 5mg OD"
      }
    ];
  }
}

export async function getDocumentDetails(documentId: string): Promise<DocumentDetails> {
  try {
    return await fetchApi<DocumentDetails>(`/documents/${documentId}`);
  } catch (e) {
    if (process.env.NEXT_PUBLIC_DATA_MODE !== "mock") throw e;
    console.warn("Backend unavailable, using mock details");
    return {
      id: "doc_raj_01",
      doc_type: "Prescription",
      status: "COMPLETED",
      document_date: "2025-06-15T10:00:00Z"
    };
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function confirmDocument(documentId: string, entities: any[]) {
  try {
    return await fetchApi(`/documents/${documentId}/confirm`, {
      method: "POST",
      body: JSON.stringify({ entities }),
    });
  } catch (e) {
    if (process.env.NEXT_PUBLIC_DATA_MODE !== "mock") throw e;
    console.warn("Backend unavailable, using mock confirm");
    return { status: "CONFIRMED" };
  }
}
