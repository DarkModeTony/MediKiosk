import { fetchClient, IS_MOCK, mockDelay } from './client';
import { MOCK_TIMELINES } from './mockData';
import { PatientTimeline } from './types';

export async function getTimeline(patientId: string): Promise<PatientTimeline> {
  if (IS_MOCK || MOCK_TIMELINES[patientId]) {
    await mockDelay();
    return MOCK_TIMELINES[patientId] || { patient_id: patientId, events: [] };
  }
  try {
    return await fetchClient(`/documents/patients/${patientId}/timeline`);
  } catch {
    return MOCK_TIMELINES[patientId] || { patient_id: patientId, events: [] };
  }
}
