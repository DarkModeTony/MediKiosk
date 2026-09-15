'use client';

import React, { useEffect, useState, use } from 'react';
import DoctorLayout from '@/components/layout/DoctorLayout';
import { getPatient } from '@/lib/api/patients';
import { getPatientPrescriptions, Prescription } from '@/lib/api/prescriptions';
import { Patient } from '@/lib/api/types';
import { Clock, User, Pill, CheckCircle2, ChevronRight } from 'lucide-react';
import Link from 'next/link';

export default function PatientProfilePage({ params }: { params: Promise<{ patientId: string }> }) {
  const resolvedParams = use(params);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getPatient(resolvedParams.patientId),
      getPatientPrescriptions(resolvedParams.patientId).catch(() => []),
    ])
      .then(([pat, rxs]) => {
        setPatient(pat);
        setPrescriptions(rxs);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [resolvedParams.patientId]);

  if (loading) {
    return (
      <DoctorLayout>
        <div className="flex justify-center p-12">
          <Clock className="animate-spin text-slate-400" />
        </div>
      </DoctorLayout>
    );
  }

  if (!patient) {
    return (
      <DoctorLayout>
        <div className="p-12 text-center text-slate-500">Patient not found</div>
      </DoctorLayout>
    );
  }

  return (
    <DoctorLayout>
      <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-8">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-6">
              <div className="w-20 h-20 bg-teal-100 dark:bg-teal-900/40 rounded-2xl flex items-center justify-center text-teal-600 dark:text-teal-300 font-black text-2xl">
                {patient.name.charAt(0)}
              </div>
              <div>
                <h1 className="text-3xl font-black text-slate-900 dark:text-slate-100">{patient.name}</h1>
                <p className="text-base text-slate-500 dark:text-slate-400 mt-1">
                  {patient.age} years • {patient.gender}
                </p>
                <div className="flex space-x-3 mt-3">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200">
                    ID: {patient.id.slice(-8).toUpperCase()}
                  </span>
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300">
                    ABHA Registered
                  </span>
                </div>
              </div>
            </div>

            <Link
              href="/queue"
              className="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-sm font-semibold rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            >
              Back to Queue
            </Link>
          </div>
        </div>

        {/* Longitudinal Prescriptions */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50/70 dark:bg-slate-850 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Pill className="w-4 h-4 text-teal-600 dark:text-teal-400" />
              <h3 className="font-bold text-slate-900 dark:text-slate-100">
                Longitudinal Medication & Prescription History ({prescriptions.length})
              </h3>
            </div>
          </div>
          <div className="p-6">
            {prescriptions.length === 0 ? (
              <p className="text-sm text-slate-400">No prescriptions recorded yet.</p>
            ) : (
              <div className="space-y-4">
                {prescriptions.map((rx) => (
                  <div
                    key={rx.id}
                    className="p-5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/40 space-y-3"
                  >
                    <div className="flex items-center justify-between text-xs border-b border-slate-200/60 dark:border-slate-700/60 pb-2.5">
                      <div className="flex items-center gap-2">
                        <span className="font-black text-slate-900 dark:text-slate-100">
                          Prescription #{rx.id.slice(-6).toUpperCase()}
                        </span>
                        <span className="text-slate-400">
                          • {rx.created_at ? new Date(rx.created_at).toLocaleDateString('en-IN', { dateStyle: 'medium' }) : ''}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            rx.status === 'FINALIZED'
                              ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700'
                              : 'bg-amber-100 dark:bg-amber-900/40 text-amber-700'
                          }`}
                        >
                          {rx.status}
                        </span>
                        <Link
                          href={`/encounters/${rx.encounter_id}`}
                          className="text-teal-600 dark:text-teal-400 hover:underline font-semibold flex items-center gap-0.5"
                        >
                          View Encounter <ChevronRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
                      {rx.items.map((item, i) => (
                        <div
                          key={i}
                          className="p-3 rounded-lg bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700"
                        >
                          <p className="font-bold text-slate-900 dark:text-slate-100">{item.medication_name}</p>
                          <p className="text-slate-500 text-[11px] mt-0.5">
                            {item.dose} • {item.frequency} • {item.duration_value} {item.duration_unit}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50/70 dark:bg-slate-850">
              <h3 className="font-bold text-slate-900 dark:text-slate-100">Allergies</h3>
            </div>
            <div className="p-6 text-sm text-slate-400 italic">
              Check active encounter for verified hypersensitivity profile (Unknown ≠ No).
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50/70 dark:bg-slate-850">
              <h3 className="font-bold text-slate-900 dark:text-slate-100">Encounter History</h3>
            </div>
            <div className="p-6 text-sm">
              <Link
                href="/queue"
                className="text-teal-600 dark:text-teal-400 hover:underline font-semibold flex items-center gap-1"
              >
                View Patient in Active Queue <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </DoctorLayout>
  );
}
