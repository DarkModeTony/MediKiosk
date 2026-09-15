import { fetchClient, IS_MOCK, mockDelay } from './client';
import { MOCK_SUMMARIES } from './mockData';
import { ClinicalSummary, SummaryVersion } from './types';

export async function getSummary(encounterId: string): Promise<ClinicalSummary> {
  if (IS_MOCK || MOCK_SUMMARIES[encounterId]) {
    await mockDelay();
    return MOCK_SUMMARIES[encounterId] || { 
      summary_id: '', status: 'AI_DRAFT', 
      latest_version: { structured_sections: [] },
      original_draft: { structured_sections: [] }
    };
  }
  try {
    return await fetchClient(`/summaries/encounters/${encounterId}/summary`);
  } catch {
    return MOCK_SUMMARIES[encounterId] || { 
      summary_id: '', status: 'AI_DRAFT', 
      latest_version: { structured_sections: [] },
      original_draft: { structured_sections: [] }
    };
  }
}

export async function editSummary(summaryId: string, content: SummaryVersion): Promise<{status: string}> {
  if (IS_MOCK) {
    await mockDelay();
    // find in mock and update state locally (for demo purposes, we can just return success)
    // Actually modifying MOCK_SUMMARIES to verify state persistence
    for (const key in MOCK_SUMMARIES) {
      if (MOCK_SUMMARIES[key].summary_id === summaryId) {
         MOCK_SUMMARIES[key].latest_version = content;
         MOCK_SUMMARIES[key].status = 'DOCTOR_EDITED';
      }
    }
    return { status: 'success' };
  }
  return fetchClient(`/summaries/${summaryId}/edit`, {
    method: 'POST',
    body: JSON.stringify({ content })
  });
}

export async function verifySummary(summaryId: string): Promise<{status: string}> {
  if (IS_MOCK) {
    await mockDelay();
    for (const key in MOCK_SUMMARIES) {
      if (MOCK_SUMMARIES[key].summary_id === summaryId) {
         MOCK_SUMMARIES[key].status = 'DOCTOR_VERIFIED';
      }
    }
    return { status: 'success' };
  }
  return fetchClient(`/summaries/${summaryId}/verify`, { method: 'POST' });
}

export async function rejectSummary(summaryId: string): Promise<{status: string}> {
  if (IS_MOCK) {
    await mockDelay();
    return { status: 'success' };
  }
  return fetchClient(`/summaries/${summaryId}/reject`, { method: 'POST' });
}
