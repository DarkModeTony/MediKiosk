import { fetchClient, IS_MOCK, mockDelay } from './client';
import { MOCK_CLINICAL_STATE, MOCK_RED_FLAGS } from './mockData';
import { ClinicalState, RedFlag } from './types';

export async function getClinicalState(encounterId: string): Promise<ClinicalState> {
  if (IS_MOCK) {
    await mockDelay();
    if (!MOCK_CLINICAL_STATE[encounterId]) {
       throw new Error('Clinical state not found');
    }
    return MOCK_CLINICAL_STATE[encounterId];
  }
  return fetchClient(`/clinical/state?encounter_id=${encounterId}`);
}

export async function getRedFlags(encounterId: string): Promise<RedFlag[]> {
  if (IS_MOCK) {
    await mockDelay();
    return MOCK_RED_FLAGS[encounterId] || [];
  }
  // For non-mock fallback we return empty array for now
  return []; 
}
