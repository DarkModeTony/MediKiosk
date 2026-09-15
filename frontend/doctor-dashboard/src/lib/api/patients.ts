import { fetchClient, IS_MOCK, mockDelay } from './client';
import { MOCK_PATIENTS } from './mockData';
import { Patient } from './types';

export async function getPatient(patientId: string): Promise<Patient> {
  // Always serve mock data for demo patient IDs
  const demoPatient = MOCK_PATIENTS.find(p => p.id === patientId);
  if (IS_MOCK || demoPatient) {
    await mockDelay();
    if (!demoPatient) throw new Error('Patient not found');
    return demoPatient;
  }
  try {
    return await fetchClient(`/patients/${patientId}`);
  } catch (err) {
    const fallback = MOCK_PATIENTS.find(p => p.id === patientId);
    if (fallback) return fallback;
    throw err;
  }
}
