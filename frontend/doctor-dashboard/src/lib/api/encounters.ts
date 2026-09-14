import { fetchClient, IS_MOCK, mockDelay } from './client';
import { MOCK_ENCOUNTERS } from './mockData';
import { Encounter } from './types';

export async function getEncounter(encounterId: string): Promise<Encounter> {
  if (IS_MOCK) {
    await mockDelay();
    const encounter = MOCK_ENCOUNTERS.find(e => e.id === encounterId);
    if (!encounter) throw new Error('Encounter not found');
    return encounter;
  }
  return fetchClient(`/encounters/${encounterId}`);
}
