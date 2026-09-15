import { fetchClient, IS_MOCK, mockDelay } from './client';
import { MOCK_ENCOUNTERS } from './mockData';
import { Encounter } from './types';

export async function getEncounter(encounterId: string): Promise<Encounter> {
  // Always serve mock data for demo encounter IDs
  const demoEnc = MOCK_ENCOUNTERS.find(e => e.id === encounterId);
  if (IS_MOCK || demoEnc) {
    await mockDelay();
    if (!demoEnc) throw new Error('Encounter not found');
    return demoEnc;
  }
  try {
    return await fetchClient(`/encounters/${encounterId}`);
  } catch (err) {
    // If the encounter looks like a demo ID, serve mock
    const fallback = MOCK_ENCOUNTERS.find(e => e.id === encounterId);
    if (fallback) return fallback;
    throw err;
  }
}
