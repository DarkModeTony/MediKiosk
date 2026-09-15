import { fetchClient, IS_MOCK, mockDelay } from './client';
import { MOCK_CLINICAL_STATE, MOCK_RED_FLAGS } from './mockData';
import { ClinicalState, RedFlag } from './types';

export async function getClinicalState(encounterId: string): Promise<ClinicalState> {
  if (IS_MOCK || MOCK_CLINICAL_STATE[encounterId]) {
    await mockDelay();
    if (!MOCK_CLINICAL_STATE[encounterId]) throw new Error('Clinical state not found');
    return MOCK_CLINICAL_STATE[encounterId];
  }
  try {
    return await fetchClient(`/clinical/state?encounter_id=${encounterId}`);
  } catch {
    return MOCK_CLINICAL_STATE[encounterId] || { status: 'COMPLETED', encounter_id: encounterId, facts: {} };
  }
}

export async function getRedFlags(encounterId: string): Promise<RedFlag[]> {
  if (IS_MOCK || MOCK_RED_FLAGS[encounterId]) {
    await mockDelay();
    return MOCK_RED_FLAGS[encounterId] || [];
  }
  try {
    return await fetchClient(`/encounters/${encounterId}/red-flags`) || [];
  } catch {
    return MOCK_RED_FLAGS[encounterId] || [];
  }
}
