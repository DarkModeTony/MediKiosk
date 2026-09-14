'use client';

import React, { useEffect, useState, use } from 'react';
import DoctorLayout from '@/components/layout/DoctorLayout';
import RedFlagPanel from '@/components/workspace/RedFlagPanel';
import SummaryPanel from '@/components/workspace/SummaryPanel';
import DocumentViewer from '@/components/workspace/DocumentViewer';
import ClinicalTimeline from '@/components/workspace/ClinicalTimeline';

import { getEncounter } from '@/lib/api/encounters';
import { getPatient } from '@/lib/api/patients';
import { getClinicalState, getRedFlags } from '@/lib/api/clinical';
import { getSummary } from '@/lib/api/summaries';
import { getTimeline } from '@/lib/api/documents';
import { Clock, UserCircle2, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { Encounter, Patient, RedFlag, ClinicalSummary, ClinicalState, PatientTimeline } from '@/lib/api/types';

export default function EncounterWorkspace({ params }: { params: Promise<{ encounterId: string }> }) {
  const resolvedParams = use(params);
  
  const [loading, setLoading] = useState(true);
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
        
        const [pat, rf, sum, cstate, tl] = await Promise.all([
          getPatient(enc.patient_id),
          getRedFlags(enc.id),
          getSummary(enc.id),
          getClinicalState(enc.id),
          getTimeline(enc.patient_id)
        ]);
        
        setPatient(pat);
        setRedFlags(rf);
        setSummary(sum);
        setClinicalState(cstate);
        setTimeline(tl);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [resolvedParams.encounterId]);

  if (loading) {
    return <DoctorLayout><div className="flex justify-center p-12"><Clock className="animate-spin text-slate-400 h-8 w-8" /></div></DoctorLayout>;
  }

  if (!encounter || !patient) {
    return <DoctorLayout><div className="p-12 text-center text-slate-500">Encounter workspace could not be loaded.</div></DoctorLayout>;
  }

  return (
    <DoctorLayout>
      <div className="max-w-[1600px] mx-auto space-y-6">
        
        {/* Patient Header */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-wrap items-center justify-between">
          <div className="flex items-center space-x-4">
             <UserCircle2 className="w-12 h-12 text-slate-300" />
             <div>
               <h2 className="text-xl font-bold text-slate-900">{patient.name}</h2>
               <div className="text-sm text-slate-500 mt-0.5 flex items-center space-x-3">
                 <span>{patient.age}M</span>
                 <span className="w-1 h-1 bg-slate-300 rounded-full" />
                 <span>ID: {patient.id.split('_')[1]}</span>
                 <span className="w-1 h-1 bg-slate-300 rounded-full" />
                 <span>Encounter #{encounter.id.split('_')[2] || '123'}</span>
               </div>
             </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right mr-4">
              <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Chief Complaint</p>
              <p className="text-sm font-medium text-slate-900">{encounter.chief_complaint || clinicalState?.facts?.CHIEF_COMPLAINT?.value || 'Not documented'}</p>
            </div>
            {encounter.priority === 'HIGH' && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-red-100 text-red-800">
                <AlertCircle className="w-4 h-4 mr-1.5" /> HIGH PRIORITY
              </span>
            )}
            <Link href={`/patients/${patient.id}`} className="px-4 py-2 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors">
              Patient Profile
            </Link>
          </div>
        </div>

        {/* Red Flags Panel */}
        <RedFlagPanel flags={redFlags} />

        {/* Main Split: AI Summary (Left) & Clinical History + Docs (Right) */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 h-[700px]">
          {/* AI Clinical Summary (Editable) */}
          <SummaryPanel summaryId={summary?.summary_id || encounter.id} summaryData={summary!} onUpdate={() => {
            // Very simple reload strategy for MVP
            window.location.reload();
          }} />
          
          {/* Context Panels */}
          <div className="flex flex-col space-y-6 h-full overflow-hidden">
            {/* Structured History */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex-1 flex flex-col min-h-[300px]">
              <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 shrink-0">
                <h3 className="font-bold text-slate-800 text-lg">Structured Clinical History</h3>
              </div>
              <div className="p-6 overflow-y-auto flex-1">
                <div className="grid grid-cols-2 gap-x-8 gap-y-6">
                  {Object.entries(clinicalState?.facts || {}).map(([key, fact]) => (
                    <div key={key}>
                       <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">{key.replace(/_/g, ' ')}</p>
                       <p className="text-sm font-medium text-slate-800">
                         {fact.state === 'COLLECTED' ? fact.value : fact.state === 'UNKNOWN' ? <span className="text-slate-400 italic">Not documented</span> : <span className="text-slate-400 italic">{fact.state}</span>}
                       </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Document / Provenance Viewer */}
            <div className="flex-1 min-h-[350px]">
               <DocumentViewer timelineEvents={timeline?.events || []} />
            </div>
          </div>
        </div>

        {/* Timeline Bottom */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mt-6">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
            <h3 className="font-bold text-slate-800 text-lg">Clinical Timeline</h3>
          </div>
          <div className="p-6">
             <ClinicalTimeline events={timeline?.events || []} />
          </div>
        </div>

      </div>
    </DoctorLayout>
  );
}
