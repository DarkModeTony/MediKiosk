'use client';

import React, { useEffect, useState, use } from 'react';
import DoctorLayout from '@/components/layout/DoctorLayout';
import RedFlagPanel from '@/components/workspace/RedFlagPanel';
import SummaryPanel from '@/components/workspace/SummaryPanel';
import DocumentViewer from '@/components/workspace/DocumentViewer';
import ClinicalTimeline from '@/components/workspace/ClinicalTimeline';
import PrescriptionWorkspace from '@/components/workspace/PrescriptionWorkspace';

import { getEncounter } from '@/lib/api/encounters';
import { getPatient } from '@/lib/api/patients';
import { getClinicalState, getRedFlags } from '@/lib/api/clinical';
import { getSummary } from '@/lib/api/summaries';
import { getTimeline } from '@/lib/api/documents';
import {
  UserCircle2,
  AlertCircle,
  Clock,
  ChevronLeft,
  FileText,
  Activity,
  List,
  Image as ImageIcon,
  Pill,
} from 'lucide-react';
import Link from 'next/link';
import { Encounter, Patient, RedFlag, ClinicalSummary, ClinicalState, PatientTimeline } from '@/lib/api/types';
import { cn } from '@/lib/utils';

type Tab = 'summary' | 'history' | 'prescription' | 'documents' | 'timeline';

const TABS: { key: Tab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { key: 'summary', label: 'AI Summary', icon: FileText },
  { key: 'history', label: 'Clinical History', icon: List },
  { key: 'prescription', label: 'Prescription (Rx)', icon: Pill },
  { key: 'documents', label: 'Documents', icon: ImageIcon },
  { key: 'timeline', label: 'Timeline', icon: Activity },
];

export default function EncounterWorkspace({ params }: { params: Promise<{ encounterId: string }> }) {
  const resolvedParams = use(params);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('summary');
  const [encounter, setEncounter] = useState<Encounter | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [redFlags, setRedFlags] = useState<RedFlag[]>([]);
  const [summary, setSummary] = useState<ClinicalSummary | null>(null);
  const [clinicalState, setClinicalState] = useState<ClinicalState | null>(null);
  const [timeline, setTimeline] = useState<PatientTimeline | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const enc = await getEncounter(resolvedParams.encounterId);
        setEncounter(enc);
        const [patR, rfR, sumR, cstateR, tlR] = await Promise.allSettled([
          getPatient(enc.patient_id),
          getRedFlags(enc.id),
          getSummary(enc.id),
          getClinicalState(enc.id),
          getTimeline(enc.patient_id),
        ]);
        if (patR.status === 'fulfilled') setPatient(patR.value);
        if (rfR.status === 'fulfilled') setRedFlags(rfR.value);
        if (sumR.status === 'fulfilled') setSummary(sumR.value);
        if (cstateR.status === 'fulfilled') setClinicalState(cstateR.value);
        if (tlR.status === 'fulfilled') setTimeline(tlR.value);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [resolvedParams.encounterId]);

  if (loading) {
    return (
      <DoctorLayout>
        <div className="flex flex-col items-center justify-center h-80 gap-4">
          <div className="w-12 h-12 rounded-full border-4 border-teal-500/30 border-t-teal-500 animate-spin" />
          <p className="text-slate-500 font-medium">Loading encounter workspace…</p>
        </div>
      </DoctorLayout>
    );
  }

  if (!encounter || !patient) {
    return (
      <DoctorLayout>
        <div className="p-12 text-center text-slate-500">
          <UserCircle2 className="w-16 h-16 mx-auto mb-4 text-slate-300" />
          <p className="text-xl font-bold text-slate-600">Encounter workspace could not be loaded.</p>
        </div>
      </DoctorLayout>
    );
  }

  const facts = clinicalState?.facts || {};

  return (
    <DoctorLayout>
      <div className="max-w-[1600px] mx-auto space-y-5 animate-fade-in">

        {/* Back link */}
        <Link href="/queue" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 font-semibold transition-colors">
          <ChevronLeft className="w-4 h-4" />
          Back to Queue
        </Link>

        {/* Patient Header Card */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
          {/* Top accent bar based on priority */}
          <div className={`h-1 w-full ${encounter.priority === 'HIGH' ? 'bg-gradient-to-r from-red-500 to-red-600' : 'bg-gradient-to-r from-teal-500 to-teal-600'}`} />

          <div className="px-6 py-5 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center font-black text-2xl shadow-sm ${
                encounter.priority === 'HIGH'
                  ? 'bg-red-100 dark:bg-red-900/30 text-red-600'
                  : 'bg-teal-100 dark:bg-teal-900/30 text-teal-600'
              }`}>
                {patient.name.charAt(0)}
              </div>
              <div>
                <h1 className="text-xl font-black text-slate-900 dark:text-slate-100">{patient.name}</h1>
                <div className="flex items-center gap-2 mt-1 text-sm text-slate-500 dark:text-slate-400">
                  <span>{patient.age}y</span>
                  <span className="w-1 h-1 bg-slate-300 rounded-full" />
                  <span>ID: {patient.id.split('_').slice(-1)[0]}</span>
                  <span className="w-1 h-1 bg-slate-300 rounded-full" />
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    Encounter #{encounter.id.split('_').slice(-1)[0] || '001'}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Chief complaint */}
              <div className="hidden md:block px-4 py-2 rounded-xl bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600">
                <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Chief Complaint</p>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                  {encounter.chief_complaint || clinicalState?.facts?.CHIEF_COMPLAINT?.value || 'Not documented'}
                </p>
              </div>

              {encounter.priority === 'HIGH' && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-black bg-red-600 text-white shadow-sm">
                  <AlertCircle className="w-3.5 h-3.5" />
                  HIGH PRIORITY
                </span>
              )}

              <Link
                href={`/patients/${patient.id}`}
                className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-sm font-semibold hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors border border-slate-200 dark:border-slate-600"
              >
                Patient Profile
              </Link>
            </div>
          </div>
        </div>

        {/* Red Flags */}
        {redFlags.length > 0 && <RedFlagPanel flags={redFlags} />}

        {/* Tabbed Workspace */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
          {/* Tab bar */}
          <div className="flex border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/80">
            {TABS.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={cn(
                  'flex items-center gap-2 px-5 py-3.5 text-sm font-semibold border-b-2 transition-all duration-150',
                  activeTab === key
                    ? 'border-teal-500 text-teal-600 dark:text-teal-400 bg-white dark:bg-slate-700'
                    : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-white/50 dark:hover:bg-slate-700/50'
                )}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="p-6">
            {activeTab === 'summary' && (
              <SummaryPanel
                summaryId={summary?.summary_id || encounter.id}
                summaryData={summary!}
                onUpdate={() => window.location.reload()}
              />
            )}

            {activeTab === 'history' && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-5">
                {Object.entries(facts).length === 0 ? (
                  <div className="col-span-3 py-12 text-center text-slate-400">
                    <List className="w-10 h-10 mx-auto mb-3 text-slate-300" />
                    <p className="font-medium">No structured history collected yet.</p>
                  </div>
                ) : Object.entries(facts).map(([key, fact]) => (
                  <div key={key} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-700/50 border border-slate-100 dark:border-slate-600">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                      {key.replace(/_/g, ' ')}
                    </p>
                    <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                      {fact.state === 'COLLECTED'
                        ? fact.value
                        : <span className="text-slate-400 italic font-normal">{fact.state === 'UNKNOWN' ? 'Not documented' : fact.state}</span>}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'prescription' && (
              <PrescriptionWorkspace
                encounter={encounter}
                patient={patient}
                redFlags={redFlags}
                clinicalState={clinicalState}
              />
            )}

            {activeTab === 'documents' && (
              <DocumentViewer timelineEvents={timeline?.events || []} />
            )}

            {activeTab === 'timeline' && (
              <ClinicalTimeline events={timeline?.events || []} />
            )}
          </div>
        </div>
      </div>
    </DoctorLayout>
  );
}
