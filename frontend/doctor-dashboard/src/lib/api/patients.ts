import { fetchClient, IS_MOCK, mockDelay } from './client';
import { MOCK_PATIENTS } from './mockData';
import { Patient } from './types';

export async function getPatient(patientId: string): Promise<Patient> {
  if (IS_MOCK) {
    await mockDelay();
    const patient = MOCK_PATIENTS.find(p => p.id === patientId);
    if (!patient) throw new Error('Patient not found');
    return patient;
  }
  return fetchClient(`/patients/${patientId}`);
}
