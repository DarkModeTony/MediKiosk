import { fetchClient, IS_MOCK, mockDelay } from './client';
import { MOCK_TIMELINES } from './mockData';
import { PatientTimeline } from './types';

export async function getTimeline(patientId: string, encounterId?: string): Promise<PatientTimeline> {
  if (IS_MOCK) {
    await mockDelay();
    return MOCK_TIMELINES[patientId] || { patient_id: patientId, events: [] };
  }
  try {
    const query = encounterId ? `?encounter_id=${encodeURIComponent(encounterId)}` : '';
    return await fetchClient(`/documents/patients/${patientId}/timeline${query}`);
  } catch {
    return MOCK_TIMELINES[patientId] || { patient_id: patientId, events: [] };
  }
}
