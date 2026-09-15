import { fetchClient, IS_MOCK, mockDelay } from './client';
import { MOCK_ENCOUNTERS, MOCK_PATIENTS } from './mockData';
import { QueueItem } from './types';

// Demo Raj Kumar entry always shown at top of queue
const DEMO_RAJ_QUEUE_ITEM: QueueItem = {
  id: "enc_raj_001",
  patient_id: "pat_raj_123",
  name: "Raj Kumar",
  age: 42,
  gender: "Male",
  status: "WAITING",
  priority: "MEDIUM",
  chief_complaint: "Fever and weakness for 3 days",
  arrival: "2026-09-15T08:15:00Z",
  created_at: "2026-09-15T08:15:00Z",
  updated_at: "2026-09-15T08:20:00Z",
  red_flag_count: 1,
  red_flag_severity: "MEDIUM",
};

export async function getQueue(): Promise<QueueItem[]> {
  if (IS_MOCK) {
    await mockDelay();
    return MOCK_ENCOUNTERS.map(enc => {
      const patient = MOCK_PATIENTS.find(p => p.id === enc.patient_id);
      return { ...enc, ...patient, arrival: enc.created_at } as QueueItem;
    });
  }
  
  // Real API — always prepend demo patient
  try {
    const apiQueue: QueueItem[] = await fetchClient(`/encounters/active`);
    // Remove any duplicate of Raj if already present, then prepend
    const withoutRaj = apiQueue.filter(q => q.patient_id !== 'pat_raj_123' && q.id !== 'enc_raj_001');
    return [DEMO_RAJ_QUEUE_ITEM, ...withoutRaj];
  } catch {
    // Backend down — show demo only
    return [DEMO_RAJ_QUEUE_ITEM];
  }
}
