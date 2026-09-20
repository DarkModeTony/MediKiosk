import { fetchClient, IS_MOCK, mockDelay } from './client';
import { MOCK_ENCOUNTERS } from './mockData';
import { Encounter } from './types';

export async function getEncounter(encounterId: string): Promise<Encounter> {
  if (IS_MOCK) {
    await mockDelay();
    const demoEnc = MOCK_ENCOUNTERS.find(e => e.id === encounterId);
    if (!demoEnc) throw new Error('Encounter not found');
    return demoEnc;
  }
  try {
    return await fetchClient(`/encounters/${encounterId}`);
  } catch (err) {
    // If backend fails or not found, fallback to demo
    const fallback = MOCK_ENCOUNTERS.find(e => e.id === encounterId);
    if (fallback) return fallback;
    throw err;
  }
}
