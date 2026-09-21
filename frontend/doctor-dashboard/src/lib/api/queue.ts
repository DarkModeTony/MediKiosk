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

export const MOCK_QUEUE: QueueItem[] = MOCK_ENCOUNTERS.map(enc => {
  const patient = MOCK_PATIENTS.find(p => p.id === enc.patient_id);
  return {
    ...patient,
    ...enc,
    arrival: enc.created_at,
  } as QueueItem;
});

const CACHE_KEY = 'medikiosk_doctor_queue_cache';

export function getCachedQueue(): QueueItem[] {
  if (typeof window !== 'undefined') {
    try {
      const stored = localStorage.getItem(CACHE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {}
  }
  return MOCK_QUEUE;
}

export async function getQueue(): Promise<QueueItem[]> {
  if (IS_MOCK) {
    // Instant return for dummy data
    return MOCK_QUEUE;
  }
  
  // Real API with instant fallback
  try {
    const apiQueue: QueueItem[] = await fetchClient(`/encounters/active`);
    if (apiQueue && apiQueue.length > 0) {
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem(CACHE_KEY, JSON.stringify(apiQueue));
        } catch {}
      }
      return apiQueue;
    }
    return MOCK_QUEUE;
  } catch {
    // Backend down or network delay — return cached or dummy data immediately
    return getCachedQueue();
  }
}
