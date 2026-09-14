import { fetchClient, IS_MOCK, mockDelay } from './client';
import { MOCK_ENCOUNTERS, MOCK_PATIENTS } from './mockData';
import { QueueItem } from './types';

export async function getQueue(): Promise<QueueItem[]> {
  if (IS_MOCK) {
    await mockDelay();
    
    // Combine patients and encounters to form a queue
    return MOCK_ENCOUNTERS.map(enc => {
      const patient = MOCK_PATIENTS.find(p => p.id === enc.patient_id);
      return {
        ...enc,
        ...patient,
        arrival: enc.created_at
      } as QueueItem;
    });
  }
  
  // Real API fallback
  return fetchClient(`/encounters/active`);
}
