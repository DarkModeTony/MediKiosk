'use client';

import React, { useEffect, useState, use } from 'react';
import DoctorLayout from '@/components/layout/DoctorLayout';
import { getPatient } from '@/lib/api/patients';
import { Patient } from '@/lib/api/types';
import { Clock, User } from 'lucide-react';
import Link from 'next/link';

export default function PatientProfilePage({ params }: { params: Promise<{ patientId: string }> }) {
  const resolvedParams = use(params);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPatient(resolvedParams.patientId)
      .then(setPatient)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [resolvedParams.patientId]);

  if (loading) {
    return <DoctorLayout><div className="flex justify-center p-12"><Clock className="animate-spin text-slate-400" /></div></DoctorLayout>;
  }

  if (!patient) {
    return <DoctorLayout><div className="p-12 text-center text-slate-500">Patient not found</div></DoctorLayout>;
  }

  return (
    <DoctorLayout>
      <div className="max-w-5xl mx-auto space-y-8">
        
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-6">
              <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center text-slate-400">
                <User className="w-10 h-10" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900">{patient.name}</h1>
                <p className="text-lg text-slate-500 mt-1">{patient.age} years • {patient.gender}</p>
                <div className="flex space-x-4 mt-4">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
                    Patient ID: {patient.id.split('_')[1]}
                  </span>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    ABHA Linked
                  </span>
                </div>
              </div>
            </div>
            
            <Link 
              href="/queue"
              className="px-4 py-2 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors"
            >
              Back to Queue
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
              <h3 className="font-semibold text-slate-800">Allergies</h3>
            </div>
            <div className="p-6 text-slate-500">
              Not documented
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
              <h3 className="font-semibold text-slate-800">Encounter History</h3>
            </div>
            <div className="p-6">
               <Link href={`/encounters/enc_${patient.id.split('_')[1]}_001`} className="text-teal-600 hover:underline font-medium">
                 View Current Encounter
               </Link>
            </div>
          </div>
        </div>
      </div>
    </DoctorLayout>
  );
}
