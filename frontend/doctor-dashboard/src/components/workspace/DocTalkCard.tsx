'use client';

import React, { useState, useEffect } from 'react';
import {
  Stethoscope,
  Clock,
  Building2,
  Globe2,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Loader2,
  Play,
  RotateCcw,
  FileText,
  UserCheck,
  ChevronRight,
  Video,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import {
  ConsultationResponse,
  getEncounterConsultation,
  cancelConsultation,
  startConsultation,
  simulateSpecialistAccept,
  simulateSpecialistDecline,
} from '@/lib/api/doctalk';
import DocTalkRequestDialog from './DocTalkRequestDialog';
import DocTalkRoomModal from './DocTalkRoomModal';
import { cn } from '@/lib/utils';

interface DocTalkCardProps {
  encounterId: string;
  patientName?: string;
  treatingHospitalName?: string;
  suggestedSpecialty?: string;
}

export default function DocTalkCard({
  encounterId,
  patientName,
  treatingHospitalName = 'Apollo Hospitals',
  suggestedSpecialty = 'Cardiology',
}: DocTalkCardProps) {
  const [consultation, setConsultation] = useState<ConsultationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [dialogOpen, setDialogOpen] = useState<boolean>(false);
  const [cancelling, setCancelling] = useState<boolean>(false);
  const [starting, setStarting] = useState<boolean>(false);
  const [notesOpen, setNotesOpen] = useState<boolean>(false);
  const [roomOpen, setRoomOpen] = useState<boolean>(false);

  // Poll or fetch consultation for this encounter
  const refreshConsultation = async () => {
    try {
      const data = await getEncounterConsultation(encounterId);
      setConsultation(data);
    } catch (err) {
      console.warn('Could not fetch consultation for encounter:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    refreshConsultation();

    // Polling while active to check for acceptance
    const interval = setInterval(() => {
      if (consultation && ['REQUESTED', 'ACCEPTED'].includes(consultation.status)) {
        refreshConsultation();
      }
    }, 4000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [encounterId, consultation?.status]);

  const handleCancel = async () => {
    if (!consultation) return;
    setCancelling(true);
    try {
      const updated = await cancelConsultation(consultation.id, encounterId);
      setConsultation(updated);
    } catch (err) {
      console.error('Cancel failed:', err);
    } finally {
      setCancelling(false);
    }
  };

  const handleStart = async () => {
    if (!consultation) return;
    setStarting(true);
    try {
      const updated = await startConsultation(consultation.id);
      setConsultation(updated);
      setRoomOpen(true);
    } catch (err) {
      console.error('Start failed, launching room directly:', err);
      setRoomOpen(true);
    } finally {
      setStarting(false);
    }
  };

  // Demo simulator helpers
  const handleSimulateAccept = async () => {
    const res = await simulateSpecialistAccept(encounterId);
    if (res) setConsultation({ ...res });
  };

  const handleSimulateDecline = async () => {
    const res = await simulateSpecialistDecline(
      encounterId,
      'Dr. Ananya is currently attending to an acute cardiac catheterization case.'
    );
    if (res) setConsultation({ ...res });
  };

  const hasActiveConsultation = Boolean(
    consultation && ['REQUESTED', 'ACCEPTED', 'IN_PROGRESS'].includes(consultation.status)
  );

  return (
    <>
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden transition-all">
        {/* Top brand indicator */}
        <div className="h-1 w-full bg-gradient-to-r from-teal-500 via-cyan-500 to-blue-600" />

        <div className="p-5">
          {/* Header row: Entry Point */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start sm:items-center gap-3.5">
              <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-teal-500 to-teal-700 text-white flex items-center justify-center font-bold text-xl shadow-md shadow-teal-600/20 shrink-0">
                <Stethoscope className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 className="text-base font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-1.5">
                    DocTalk
                    <span className="text-teal-600 dark:text-teal-400 font-bold">· Ask a Specialist</span>
                  </h2>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-teal-50 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                    Cross-Hospital Second Opinion
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Need another doctor&apos;s input on this case? Request a 3, 5, or 7 minute consultation with a specialist.
                </p>
              </div>
            </div>

            {/* Main Action or Status Trigger */}
            <div className="flex items-center gap-2 self-end sm:self-center">
              {!hasActiveConsultation ? (
                <button
                  type="button"
                  onClick={() => setDialogOpen(true)}
                  className="px-4 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-black shadow-md shadow-teal-600/20 hover:shadow-teal-600/30 transition-all flex items-center gap-2 cursor-pointer focus:outline-none focus:ring-2 focus:ring-teal-500"
                >
                  <UserCheck className="w-4 h-4" />
                  <span>Ask a Specialist</span>
                </button>
              ) : (
                <span className="text-xs font-bold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-700/60 px-3 py-1.5 rounded-xl">
                  Consultation In Progress
                </span>
              )}
            </div>
          </div>

          {/* Dynamic State Section */}
          {loading ? (
            <div className="mt-4 py-3 flex items-center justify-center gap-2 text-xs text-slate-400">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-teal-500" />
              <span>Checking DocTalk network status...</span>
            </div>
          ) : consultation ? (
            <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700/80">
              {/* STATE 1: REQUESTED (Waiting for specialist) */}
              {consultation.status === 'REQUESTED' && (
                <div className="rounded-xl bg-gradient-to-r from-teal-50/80 via-white to-cyan-50/50 dark:from-slate-800 dark:via-slate-800/80 dark:to-slate-800/60 border border-teal-200 dark:border-teal-800/70 p-4 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full bg-teal-500 animate-ping" />
                      <span className="text-xs font-bold text-teal-800 dark:text-teal-200 uppercase tracking-wider">
                        Consultation request sent
                      </span>
                      <span className="text-xs text-slate-400">·</span>
                      <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                        Waiting for specialist...
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Demo shortcuts */}
                      <button
                        type="button"
                        onClick={handleSimulateAccept}
                        className="text-[11px] font-semibold text-teal-700 dark:text-teal-300 hover:underline bg-teal-100 dark:bg-teal-900/60 px-2 py-0.5 rounded-md"
                        title="Simulate specialist accepting in demo mode"
                      >
                        ⚡ Simulate Accept
                      </button>
                      <button
                        type="button"
                        onClick={handleSimulateDecline}
                        className="text-[11px] font-semibold text-amber-700 dark:text-amber-300 hover:underline bg-amber-100 dark:bg-amber-900/60 px-2 py-0.5 rounded-md"
                        title="Simulate specialist declining in demo mode"
                      >
                        ⚡ Simulate Decline
                      </button>

                      <button
                        type="button"
                        onClick={handleCancel}
                        disabled={cancelling}
                        className="px-3 py-1.5 rounded-lg border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 text-xs font-bold transition-colors disabled:opacity-50"
                      >
                        {cancelling ? 'Cancelling...' : 'Cancel Request'}
                      </button>
                    </div>
                  </div>

                  {/* Consultation details summary */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-1">
                    <div>
                      <p className="text-[10px] font-bold uppercase text-slate-400">Target Specialist</p>
                      <p className="font-semibold text-slate-800 dark:text-slate-200">
                        {consultation.specialist_name || 'Any Available Specialist'}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase text-slate-400">Specialist Facility</p>
                      <p className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1">
                        <Building2 className="w-3 h-3 text-slate-400" />
                        {consultation.specialist_hospital_name || 'Network Hospital'}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase text-slate-400">Specialty</p>
                      <p className="font-semibold text-slate-800 dark:text-slate-200">
                        {consultation.specialty}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase text-slate-400">Duration & Urgency</p>
                      <p className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1">
                        <Clock className="w-3 h-3 text-teal-600" />
                        {consultation.requested_duration_minutes}m · {consultation.urgency}
                      </p>
                    </div>
                  </div>

                  {consultation.reason && (
                    <div className="text-xs bg-white/80 dark:bg-slate-900/80 p-2.5 rounded-lg border border-slate-200/60 dark:border-slate-700/60">
                      <span className="font-bold text-slate-500 dark:text-slate-400">Reason: </span>
                      <span className="text-slate-700 dark:text-slate-300">{consultation.reason}</span>
                    </div>
                  )}
                </div>
              )}

              {/* STATE 2: ACCEPTED (Dr. X accepted your request) */}
              {consultation.status === 'ACCEPTED' && (
                <div className="rounded-xl bg-gradient-to-r from-emerald-50/90 via-white to-teal-50/50 dark:from-emerald-950/40 dark:via-slate-800 dark:to-teal-950/30 border border-emerald-300 dark:border-emerald-700 p-4 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-emerald-500 text-white flex items-center justify-center shadow-md shadow-emerald-500/20 shrink-0">
                        <CheckCircle2 className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="text-sm font-black text-emerald-900 dark:text-emerald-100">
                          {consultation.specialist_name || 'Specialist'} accepted your request.
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5 mt-0.5">
                          <span>{consultation.specialty}</span>
                          <span className="w-1 h-1 bg-slate-300 rounded-full" />
                          <span className="font-medium text-slate-700 dark:text-slate-300 flex items-center gap-1">
                            <Building2 className="w-3 h-3 text-slate-400" />
                            {consultation.specialist_hospital_name || 'Partner Hospital'}
                          </span>
                          <span className="w-1 h-1 bg-slate-300 rounded-full" />
                          <span className="text-emerald-700 dark:text-emerald-300 font-bold">
                            {consultation.requested_duration_minutes} min window open
                          </span>
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleStart}
                        disabled={starting}
                        className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-black shadow-md shadow-emerald-600/30 transition-all flex items-center gap-2 cursor-pointer"
                      >
                        {starting ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Connecting...</span>
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4 fill-current" />
                            <span>Start Consultation</span>
                          </>
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={handleCancel}
                        disabled={cancelling}
                        className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 text-xs font-semibold"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* STATE 3: IN_PROGRESS */}
              {consultation.status === 'IN_PROGRESS' && (
                <div className="rounded-xl bg-cyan-50 dark:bg-cyan-950/40 border border-cyan-300 dark:border-cyan-800 p-4 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-cyan-600 text-white flex items-center justify-center shrink-0">
                        <Stethoscope className="w-5 h-5 animate-pulse" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-black text-cyan-950 dark:text-cyan-100">
                            Consultation in progress with {consultation.specialist_name || 'Specialist'}
                          </span>
                          <span className="text-[10px] font-bold uppercase bg-cyan-200 dark:bg-cyan-900 text-cyan-800 dark:text-cyan-200 px-2 py-0.5 rounded-full">
                            Active {consultation.requested_duration_minutes}m Session
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          {consultation.specialty} · {consultation.specialist_hospital_name}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setRoomOpen(true)}
                        className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-700 text-white text-xs font-bold shadow-md shadow-cyan-600/30 transition-all flex items-center gap-1.5 cursor-pointer"
                      >
                        <Video className="w-4 h-4" />
                        <span>Join Consultation Room</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setNotesOpen(!notesOpen)}
                        className="px-3 py-2 rounded-xl bg-white dark:bg-slate-800 border border-cyan-300 dark:border-cyan-700 text-cyan-800 dark:text-cyan-200 text-xs font-bold hover:bg-cyan-50 transition-colors flex items-center gap-1.5"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>Specialist Notes</span>
                      </button>
                    </div>
                  </div>

                  {notesOpen && (
                    <div className="p-3 bg-white dark:bg-slate-900 rounded-xl border border-cyan-200 dark:border-cyan-800/60 text-xs text-slate-700 dark:text-slate-300 space-y-1.5">
                      <p className="font-bold text-slate-900 dark:text-slate-100">Specialist Clinical Opinion</p>
                      <p className="italic text-slate-500">
                        Session active. Specialist notes and recommendations will populate automatically upon submission.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* STATE 4: DECLINED / CANCELLED / EXPIRED */}
              {['DECLINED', 'CANCELLED', 'EXPIRED'].includes(consultation.status) && (
                <div className="rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 p-4 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center shrink-0">
                        {consultation.status === 'DECLINED' ? (
                          <XCircle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                        ) : (
                          <AlertCircle className="w-5 h-5 text-slate-500" />
                        )}
                      </div>
                      <div>
                        <p className="text-xs font-bold text-slate-800 dark:text-slate-200">
                          {consultation.status === 'DECLINED'
                            ? 'Specialist was unable to take this consultation request.'
                            : consultation.status === 'EXPIRED'
                            ? 'Consultation request expired without response.'
                            : 'Consultation request was cancelled.'}
                        </p>
                        {consultation.decline_reason && (
                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                            Reason: {consultation.decline_reason}
                          </p>
                        )}
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => setDialogOpen(true)}
                      className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-sm transition-all flex items-center gap-1.5 self-start sm:self-auto"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Find Another Specialist</span>
                    </button>
                  </div>
                </div>
              )}

              {/* STATE 5: COMPLETED & SPECIALIST OPINION */}
              {consultation.status === 'COMPLETED' && (
                <div className="space-y-4">
                  {/* Status Banner */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center shrink-0">
                        <CheckCircle2 className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="text-xs font-black text-teal-900 dark:text-teal-100">
                          Consultation Completed
                        </p>
                        <p className="text-[11px] text-teal-700 dark:text-teal-300">
                          {consultation.specialist_name || 'Specialist'} · {consultation.specialty} · {consultation.specialist_hospital_name || 'Network Hospital'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={refreshConsultation}
                        className="px-2.5 py-1.5 rounded-lg border border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-300 hover:bg-teal-100 dark:hover:bg-teal-900/50 text-xs font-semibold flex items-center gap-1 cursor-pointer"
                        title="Refresh specialist notes"
                      >
                        <RotateCcw className="w-3 h-3" />
                        <span>Refresh</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setDialogOpen(true)}
                        className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-xs transition-colors cursor-pointer"
                      >
                        Request Another Opinion
                      </button>
                    </div>
                  </div>

                  {/* 🩺 Specialist Consultation Card */}
                  {consultation.notes && consultation.notes.length > 0 ? (
                    consultation.notes.map((note, nIdx) => {
                      const noteTimeStr = note.created_at
                        ? new Date(note.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                        : '';
                      return (
                        <div
                          key={nIdx}
                          className="rounded-2xl bg-white dark:bg-slate-900 border-2 border-teal-200/90 dark:border-teal-800/80 shadow-sm overflow-hidden"
                        >
                          {/* Section Header */}
                          <div className="px-5 py-3.5 bg-gradient-to-r from-teal-50 via-cyan-50/50 to-white dark:from-slate-800 dark:via-slate-800/80 dark:to-slate-800/60 border-b border-teal-100 dark:border-slate-700 flex flex-wrap items-center justify-between gap-3">
                            <div className="flex items-center gap-2">
                              <span className="text-lg">🩺</span>
                              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 tracking-tight">
                                Specialist Consultation
                              </h3>
                              <span className="text-[10px] font-bold uppercase tracking-wider bg-teal-600 text-white px-2 py-0.5 rounded-md">
                                Verified Specialist Input
                              </span>
                            </div>

                            {noteTimeStr && (
                              <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 font-mono">
                                <Clock className="w-3.5 h-3.5 text-slate-400" />
                                <span className="font-bold">Time:</span>
                                <span>{noteTimeStr}</span>
                              </div>
                            )}
                          </div>

                          {/* Attribution Grid */}
                          <div className="p-5 space-y-4">
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 pb-4 border-b border-slate-100 dark:border-slate-800 text-xs">
                              <div className="space-y-0.5">
                                <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Specialist:</p>
                                <p className="text-sm font-black text-slate-900 dark:text-slate-100">
                                  {note.specialist_name || consultation.specialist_name || 'Dr. Specialist'}
                                </p>
                              </div>
                              <div className="space-y-0.5">
                                <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Hospital:</p>
                                <p className="text-sm font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1">
                                  <Building2 className="w-3.5 h-3.5 text-slate-400" />
                                  {note.specialist_hospital_name || consultation.specialist_hospital_name || 'Network Hospital'}
                                </p>
                              </div>
                              <div className="space-y-0.5">
                                <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Specialty:</p>
                                <p className="text-sm font-bold text-teal-700 dark:text-teal-300">
                                  {consultation.specialty}
                                </p>
                              </div>
                            </div>

                            {/* Opinion */}
                            <div className="space-y-1.5">
                              <p className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                                <FileText className="w-3.5 h-3.5 text-teal-600" />
                                Opinion:
                              </p>
                              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200/80 dark:border-slate-700 text-xs leading-relaxed text-slate-800 dark:text-slate-100">
                                {note.clinical_opinion}
                              </div>
                            </div>

                            {/* Recommendations */}
                            {note.recommendations && (
                              <div className="space-y-1.5">
                                <p className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                                  Recommendations:
                                </p>
                                <div className="p-3.5 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/60 text-xs leading-relaxed text-slate-800 dark:text-slate-100">
                                  {Array.isArray(note.recommendations) ? (
                                    <ul className="list-disc list-inside space-y-1.5">
                                      {note.recommendations.map((rec: any, idx: number) => (
                                        <li key={idx}>
                                          {typeof rec === 'string'
                                            ? rec
                                            : rec.recommendation || rec.text || JSON.stringify(rec)}
                                        </li>
                                      ))}
                                    </ul>
                                  ) : typeof note.recommendations === 'string' ? (
                                    <p className="whitespace-pre-line">{note.recommendations}</p>
                                  ) : (
                                    <pre className="font-mono text-[11px] whitespace-pre-wrap">
                                      {JSON.stringify(note.recommendations, null, 2)}
                                    </pre>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Further Evaluation */}
                            {note.further_evaluation && (
                              <div className="space-y-1">
                                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                                  Further Evaluation:
                                </p>
                                <p className="text-xs text-slate-700 dark:text-slate-300 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700">
                                  {note.further_evaluation}
                                </p>
                              </div>
                            )}

                            {/* Follow-up */}
                            {note.follow_up && (
                              <div className="space-y-1">
                                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                                  Follow-Up:
                                </p>
                                <p className="text-xs text-slate-700 dark:text-slate-300 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700">
                                  {note.follow_up}
                                </p>
                              </div>
                            )}

                            {/* Safety Policy Badge */}
                            <div className="flex items-start gap-2.5 p-3 rounded-xl bg-teal-50/60 dark:bg-teal-950/30 border border-teal-200/80 dark:border-teal-800/60 text-xs text-teal-900 dark:text-teal-200">
                              <ShieldCheck className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                              <p className="text-[11px] leading-relaxed">
                                <strong>Treating Physician Review:</strong> This specialist opinion is advisory for clinical decision-making. DocTalk does not overwrite your existing patient facts, diagnoses, prescriptions, investigation orders, or AI clinical summary.
                              </p>
                            </div>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs text-slate-600 dark:text-slate-400 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-slate-400" />
                        <span>Consultation session completed. Specialist is documenting clinical opinion and recommendations.</span>
                      </div>
                      <button
                        type="button"
                        onClick={refreshConsultation}
                        className="text-xs text-teal-600 hover:underline font-semibold cursor-pointer"
                      >
                        Check for notes
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>

      {/* Request Dialog Modal */}
      <DocTalkRequestDialog
        isOpen={dialogOpen}
        onClose={() => setDialogOpen(false)}
        encounterId={encounterId}
        patientName={patientName}
        treatingHospitalName={treatingHospitalName}
        initialSpecialty={suggestedSpecialty}
        hasActiveConsultation={hasActiveConsultation}
        onRequestCreated={(created) => {
          setConsultation(created);
        }}
      />

      {/* Real-time Consultation Room Modal */}
      {consultation && (
        <DocTalkRoomModal
          isOpen={roomOpen}
          onClose={() => setRoomOpen(false)}
          consultationId={consultation.id}
          consultationTitle={consultation.reason}
          patientName={patientName}
          contextScope={consultation.access_scope}
          initialRole="REQUESTING_DOCTOR"
          onConsultationEnded={() => {
            setRoomOpen(false);
            refreshConsultation();
          }}
        />
      )}
    </>
  );
}
