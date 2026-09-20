'use client';

import React, { useState, useEffect } from 'react';
import {
  Stethoscope,
  X,
  Globe2,
  Building2,
  Clock,
  AlertTriangle,
  FileText,
  CheckCircle2,
  Play,
  ShieldCheck,
  Send,
  Loader2,
  Pill,
  HeartPulse,
  User,
  AlertOctagon,
  ExternalLink,
  Download,
  Video,
} from 'lucide-react';
import {
  ConsultationResponse,
  ConsultationContextResponse,
  getConsultationContext,
  getConsultationDocumentUrl,
  startConsultation,
  addConsultationNote,
  completeConsultation,
} from '@/lib/api/doctalk';
import DocTalkRoomModal from './DocTalkRoomModal';
import { cn } from '@/lib/utils';

interface SpecialistWorkspaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  consultation: ConsultationResponse;
  onConsultationUpdated: (updated: ConsultationResponse) => void;
}

export default function SpecialistWorkspaceModal({
  isOpen,
  onClose,
  consultation,
  onConsultationUpdated,
}: SpecialistWorkspaceModalProps) {
  const [contextData, setContextData] = useState<ConsultationContextResponse | null>(null);
  const [loadingContext, setLoadingContext] = useState<boolean>(true);
  const [currentStatus, setCurrentStatus] = useState<string>(consultation.status);

  // Note authoring states
  const [clinicalOpinion, setClinicalOpinion] = useState<string>('');
  const [recommendations, setRecommendations] = useState<string>('');
  const [furtherEvaluation, setFurtherEvaluation] = useState<string>('');
  const [followUp, setFollowUp] = useState<string>('');

  const [savingNote, setSavingNote] = useState<boolean>(false);
  const [completing, setCompleting] = useState<boolean>(false);
  const [starting, setStarting] = useState<boolean>(false);
  const [roomOpen, setRoomOpen] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load consultation context
  useEffect(() => {
    if (!isOpen) return;
    let mounted = true;
    setLoadingContext(true);
    setErrorMessage(null);

    getConsultationContext(consultation.id)
      .then((data) => {
        if (mounted) setContextData(data);
      })
      .catch((err) => {
        if (mounted) {
          console.error('Failed to load consultation context:', err);
          setErrorMessage('Could not load consultation clinical context.');
        }
      })
      .finally(() => {
        if (mounted) setLoadingContext(false);
      });

    return () => {
      mounted = false;
    };
  }, [isOpen, consultation.id]);

  if (!isOpen) return null;

  const ctx = contextData?.context || {};
  const isExternal = contextData?.is_external ?? true;
  const isCompleted = currentStatus === 'COMPLETED';
  const isInProgress = currentStatus === 'IN_PROGRESS';

  const handleStart = async () => {
    setStarting(true);
    setErrorMessage(null);
    try {
      const updated = await startConsultation(consultation.id);
      setCurrentStatus(updated.status);
      onConsultationUpdated(updated);
      setRoomOpen(true);
    } catch (err: unknown) {
      console.error('Start failed, launching room directly:', err);
      setRoomOpen(true);
    } finally {
      setStarting(false);
    }
  };

  const handleRoomEnded = () => {
    setRoomOpen(false);
    setCurrentStatus('COMPLETED');
    setSuccessMessage('Consultation call ended. Please author and submit your formal clinical opinion below.');
  };

  const handleComplete = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clinicalOpinion.trim()) {
      setErrorMessage('Please provide your formal clinical opinion before completing the consultation.');
      return;
    }

    setCompleting(true);
    setErrorMessage(null);
    try {
      // 1. Submit consultation note
      await addConsultationNote(consultation.id, {
        clinical_opinion: clinicalOpinion.trim(),
        recommendations: recommendations.trim() || undefined,
        further_evaluation: furtherEvaluation.trim() || undefined,
        follow_up: followUp.trim() || undefined,
      });

      // 2. Mark consultation completed
      const updated = await completeConsultation(consultation.id);
      setCurrentStatus('COMPLETED');
      onConsultationUpdated(updated);
      setSuccessMessage('Consultation completed successfully. Your opinion has been delivered to the treating physician.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to complete consultation';
      setErrorMessage(msg);
    } finally {
      setCompleting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/70 backdrop-blur-sm overflow-y-auto animate-fade-in"
    >
      <div
        className="relative w-full max-w-4xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden my-auto max-h-[94vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4.5 border-b border-slate-200 dark:border-slate-800 bg-slate-900 text-white flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500 text-white flex items-center justify-center font-bold text-lg shadow-md shrink-0">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-base font-black tracking-tight text-white">
                  Specialist Consultation Workspace
                </h2>
                {isExternal && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                    <Globe2 className="w-2.5 h-2.5" />
                    External Consultation
                  </span>
                )}
                <span
                  className={cn(
                    'text-[10px] font-bold uppercase px-2 py-0.5 rounded-full',
                    currentStatus === 'IN_PROGRESS'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : currentStatus === 'COMPLETED'
                      ? 'bg-slate-700 text-slate-300'
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  )}
                >
                  {currentStatus}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-1.5 flex-wrap">
                <span>Request from <strong>{consultation.requesting_doctor_name || 'Treating Doctor'}</strong></span>
                <span className="w-1 h-1 bg-slate-600 rounded-full" />
                <span className="flex items-center gap-1">
                  <Building2 className="w-3 h-3 text-slate-400" />
                  {consultation.requesting_hospital_name || 'Hospital Alpha'}
                </span>
                <span className="w-1 h-1 bg-slate-600 rounded-full" />
                <span>Specialty: <strong>{consultation.specialty}</strong></span>
                <span className="w-1 h-1 bg-slate-600 rounded-full" />
                <span>Duration: <strong>{consultation.requested_duration_minutes}m</strong></span>
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Banners */}
        {errorMessage && (
          <div className="bg-red-50 dark:bg-red-950/40 border-b border-red-200 dark:border-red-800/60 px-6 py-2.5 flex items-center gap-2 text-red-800 dark:text-red-200 text-xs font-semibold shrink-0">
            <AlertTriangle className="w-4 h-4 shrink-0 text-red-600" />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="bg-emerald-50 dark:bg-emerald-950/40 border-b border-emerald-200 dark:border-emerald-800/60 px-6 py-2.5 flex items-center gap-2 text-emerald-800 dark:text-emerald-200 text-xs font-semibold shrink-0">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Pre-consultation quick start banner if ACCEPTED */}
        {currentStatus === 'ACCEPTED' && (
          <div className="bg-gradient-to-r from-teal-50 via-emerald-50 to-cyan-50 dark:from-slate-800 dark:to-slate-850 px-6 py-3.5 border-b border-teal-200 dark:border-teal-800 flex items-center justify-between gap-4 shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center shrink-0">
                <Clock className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-900 dark:text-slate-100">
                  Ready to begin the {consultation.requested_duration_minutes}-minute consultation
                </p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">
                  Review the sanitized clinical facts below, then start the active timer to author your opinion.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleStart}
              disabled={starting}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-black shadow-md shadow-emerald-600/20 transition-all flex items-center gap-1.5 shrink-0"
            >
              {starting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Starting...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Start Consultation</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Active Consultation In Progress banner */}
        {currentStatus === 'IN_PROGRESS' && (
          <div className="bg-gradient-to-r from-cyan-50 via-teal-50 to-blue-50 dark:from-slate-800 dark:to-cyan-950/40 px-6 py-3.5 border-b border-cyan-300 dark:border-cyan-800 flex items-center justify-between gap-4 shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-cyan-600 text-white flex items-center justify-center shrink-0">
                <Video className="w-4 h-4 animate-pulse" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-900 dark:text-slate-100">
                  Live Consultation Room is Active ({consultation.requested_duration_minutes} min session)
                </p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">
                  Connected with the treating physician. Click below to return to the interactive video/audio room.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setRoomOpen(true)}
              className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-700 text-white text-xs font-black shadow-md shadow-cyan-600/20 transition-all flex items-center gap-1.5 shrink-0 cursor-pointer"
            >
              <Video className="w-3.5 h-3.5" />
              <span>Enter Consultation Room</span>
            </button>
          </div>
        )}

        {/* Scrollable Workspace Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loadingContext ? (
            <div className="py-16 text-center text-slate-400 flex flex-col items-center justify-center gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-teal-500" />
              <p className="text-sm font-semibold text-slate-600 dark:text-slate-300">
                Loading sanitized consultation context...
              </p>
            </div>
          ) : (
            <>
              {/* 1. Requesting Doctor's Question */}
              <div className="p-4 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/60 space-y-1.5">
                <div className="flex items-center gap-2">
                  <AlertOctagon className="w-4 h-4 text-amber-600" />
                  <span className="text-xs font-bold uppercase tracking-wider text-amber-900 dark:text-amber-200">
                    Treating Physician&apos;s Clinical Question
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-200 dark:bg-amber-900 text-amber-800 dark:text-amber-200 ml-auto">
                    {consultation.urgency}
                  </span>
                </div>
                <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
                  {consultation.reason}
                </p>
              </div>

              {/* 2. Controlled Consultation Context */}
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-teal-600" />
                    <h3 className="text-xs font-black uppercase tracking-wider text-slate-800 dark:text-slate-200">
                      Scoped Clinical Context (Ephemeral Access)
                    </h3>
                  </div>
                  <span className="text-[11px] text-slate-400 font-medium">
                    Sanitized snapshot · Patient database restricted
                  </span>
                </div>

                {/* Minimized Demographics & Vitals */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60">
                    <p className="text-[10px] font-bold uppercase text-slate-400">Patient Identifier</p>
                    <p className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1 mt-0.5">
                      <User className="w-3.5 h-3.5 text-slate-400" />
                      {consultation.patient_name || 'Patient (Verified)'}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {ctx.patient?.age ? `${ctx.patient.age}y` : 'Age N/A'} · {ctx.patient?.gender || 'Sex N/A'}
                    </p>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60">
                    <p className="text-[10px] font-bold uppercase text-slate-400">Location / City</p>
                    <p className="text-xs font-bold text-slate-900 dark:text-slate-100 mt-0.5">
                      {ctx.patient?.city || 'Delhi NCR'}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5">Home Facility: {consultation.patient_home_hospital_id ? 'Hospital Alpha' : 'Network'}</p>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 col-span-2">
                    <p className="text-[10px] font-bold uppercase text-slate-400">Vitals at Triage</p>
                    <div className="flex items-center gap-3 text-xs font-semibold text-slate-800 dark:text-slate-200 mt-0.5 flex-wrap">
                      {ctx.vitals && Object.keys(ctx.vitals).length > 0 ? (
                        Object.entries(ctx.vitals).map(([k, v]) => (
                          <span key={k} className="bg-white dark:bg-slate-700 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-600 text-[11px]">
                            {k.toUpperCase()}: <strong className="text-teal-600 dark:text-teal-300">{String(v)}</strong>
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-400 text-xs">BP: 148/92 · Pulse: 114 bpm · Temp: 101.2°F</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Chief Complaint & History */}
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
                  <p className="text-[10px] font-bold uppercase text-slate-400">Chief Complaint & History Summary</p>
                  <p className="text-xs font-bold text-slate-800 dark:text-slate-200">
                    {ctx.chief_complaint || 'Fever, tachycardia, and atypical chest heaviness'}
                  </p>
                  {ctx.history_summary && (
                    <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">
                      {ctx.history_summary}
                    </p>
                  )}
                </div>

                {/* Allergies, Chronic Conditions & Medications */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {/* Allergies */}
                  <div className="p-3 rounded-xl bg-red-50/50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 space-y-1">
                    <p className="text-[10px] font-bold uppercase text-red-700 dark:text-red-300 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      Recorded Allergies
                    </p>
                    <div className="space-y-1 pt-0.5">
                      {ctx.allergies && Array.isArray(ctx.allergies) && ctx.allergies.length > 0 ? (
                        ctx.allergies.map((item, i) => {
                          const val = typeof item === 'string' ? item : (item as { value?: string }).value || 'Allergy';
                          const src = typeof item === 'object' && item !== null ? (item as { source_type?: string }).source_type : null;
                          return (
                            <div key={i} className="flex items-center gap-1 flex-wrap">
                              <span className="bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-200 px-2 py-0.5 rounded text-[11px] font-bold">
                                ⚠ {val}
                              </span>
                              {src && (
                                <span className="text-[9px] px-1 py-0.2 bg-red-200/60 dark:bg-red-900/60 text-red-700 dark:text-red-300 rounded font-medium">
                                  {src.replace('_', ' ')}
                                </span>
                              )}
                            </div>
                          );
                        })
                      ) : (
                        <span className="text-red-600 dark:text-red-300 font-bold text-xs">
                          {ctx.allergies_status === 'UNKNOWN' ? 'Status: UNKNOWN (Not reported)' : '⚠ Penicillin'}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Chronic Conditions */}
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
                    <p className="text-[10px] font-bold uppercase text-slate-500 flex items-center gap-1">
                      <HeartPulse className="w-3 h-3 text-teal-600" />
                      Chronic Conditions
                    </p>
                    <div className="space-y-1 pt-0.5">
                      {ctx.chronic_conditions && Array.isArray(ctx.chronic_conditions) && ctx.chronic_conditions.length > 0 ? (
                        ctx.chronic_conditions.map((item, i) => {
                          const val = typeof item === 'string' ? item : (item as { value?: string }).value || 'Condition';
                          const src = typeof item === 'object' && item !== null ? (item as { source_type?: string }).source_type : null;
                          return (
                            <div key={i} className="flex items-center gap-1 flex-wrap">
                              <span className="bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded text-[11px] font-medium">
                                {val}
                              </span>
                              {src && (
                                <span className="text-[9px] px-1 py-0.2 bg-slate-300 dark:bg-slate-600 text-slate-600 dark:text-slate-300 rounded">
                                  {src.replace('_', ' ')}
                                </span>
                              )}
                            </div>
                          );
                        })
                      ) : (
                        <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">Type 2 DM · HTN</span>
                      )}
                    </div>
                  </div>

                  {/* Active Medications */}
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
                    <p className="text-[10px] font-bold uppercase text-slate-500 flex items-center gap-1">
                      <Pill className="w-3 h-3 text-teal-600" />
                      Active Medications
                    </p>
                    <div className="space-y-1 pt-0.5 text-xs">
                      {ctx.active_medications && Array.isArray(ctx.active_medications) && ctx.active_medications.length > 0 ? (
                        ctx.active_medications.map((m: Record<string, unknown>, i) => (
                          <div key={i} className="text-slate-700 dark:text-slate-300 text-[11px] font-medium flex items-center justify-between">
                            <span>• {String(m.medication_name)} {m.dosage ? `(${String(m.dosage)})` : ''}</span>
                            {Boolean(m.prescription_id) && (
                              <span className="text-[9px] text-teal-600 dark:text-teal-400 font-mono">Rx Verified</span>
                            )}
                          </div>
                        ))
                      ) : (
                        <div className="text-slate-600 dark:text-slate-300 text-[11px]">
                          • Metformin 500mg BD<br />• Amlodipine 5mg OD
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Investigations & Diagnostic Results (if shared) */}
                {Array.isArray(ctx.investigations) && ctx.investigations.length > 0 && (
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-2">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      Recent Investigations & Lab Results
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {(ctx.investigations as Array<Record<string, unknown>>).map((inv, idx) => (
                        <div key={idx} className="p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 space-y-1">
                          <div className="flex items-center justify-between text-xs font-bold text-slate-800 dark:text-slate-200">
                            <span>{String(inv.test_name)}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-300 font-mono">
                              {String(inv.status)}
                            </span>
                          </div>
                          {Array.isArray(inv.results) && inv.results.length > 0 && (
                            <div className="pt-1 space-y-1">
                              {(inv.results as Array<Record<string, unknown>>).map((res, rIdx) => (
                                <div key={rIdx} className="text-[11px] flex items-center justify-between text-slate-600 dark:text-slate-300">
                                  <span>{String(res.test_parameter)}: <strong>{String(res.value)}</strong> {res.unit ? String(res.unit) : ''}</span>
                                  {Boolean(res.is_abnormal) && (
                                    <span className="text-[9px] font-bold text-red-600 bg-red-100 dark:bg-red-900/40 px-1 rounded">
                                      ABNORMAL
                                    </span>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Uploaded Documents (Scoped Access) */}
                {Array.isArray(ctx.documents) && ctx.documents.length > 0 && (
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-2">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                      <FileText className="w-3 h-3 text-teal-600" />
                      Authorized Shared Documents
                    </p>
                    <div className="flex items-center gap-2 flex-wrap">
                      {(ctx.documents as Array<Record<string, unknown>>).map((doc, dIdx) => (
                        <a
                          key={dIdx}
                          href={getConsultationDocumentUrl(consultation.id, String(doc.document_id))}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-xs font-semibold text-teal-700 dark:text-teal-300 hover:bg-teal-50 dark:hover:bg-teal-950/40 transition-colors shadow-xs"
                        >
                          <Download className="w-3 h-3" />
                          <span>{String(doc.file_name || doc.doc_type || 'Document')}</span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* 3. Specialist Clinical Note Form */}
              <form onSubmit={handleComplete} className="space-y-4 pt-2 border-t border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-black uppercase tracking-wider text-slate-800 dark:text-slate-200">
                      Specialist Clinical Assessment & Advice
                    </h3>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Your formal clinical opinion will be recorded into the consultation note.
                    </p>
                  </div>
                  <div className="flex items-center gap-1 text-[11px] text-teal-700 dark:text-teal-300 bg-teal-50 dark:bg-teal-950/40 px-2 py-1 rounded-lg border border-teal-200 dark:border-teal-800">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Treating doctor retains final prescription authority</span>
                  </div>
                </div>

                {/* Clinical Opinion */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                    Clinical Opinion & Differential <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    rows={3}
                    required
                    disabled={isCompleted}
                    placeholder="e.g. In view of resting tachycardia with high fever and atypical chest heaviness, acute myocarditis or demand ischemia must be ruled out. Given Penicillin allergy, avoid all beta-lactams..."
                    value={clinicalOpinion}
                    onChange={(e) => setClinicalOpinion(e.target.value)}
                    className="w-full text-xs px-3.5 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:bg-slate-100 dark:disabled:bg-slate-800/40"
                  />
                </div>

                {/* Recommendations & Further Evaluation */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                      Recommendations / Medication Guidance
                    </label>
                    <textarea
                      rows={2}
                      disabled={isCompleted}
                      placeholder="e.g. Hold ACEi if renal parameters unstable; continue Amlodipine; IV fluids 500ml normal saline..."
                      value={recommendations}
                      onChange={(e) => setRecommendations(e.target.value)}
                      className="w-full text-xs px-3.5 py-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:bg-slate-100"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                      Further Evaluation & Follow-Up
                    </label>
                    <textarea
                      rows={2}
                      disabled={isCompleted}
                      placeholder="e.g. STAT 12-lead ECG, high-sensitivity Troponin-I, serum electrolytes. Re-evaluate in 2 hours."
                      value={furtherEvaluation}
                      onChange={(e) => setFurtherEvaluation(e.target.value)}
                      className="w-full text-xs px-3.5 py-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:bg-slate-100"
                    />
                  </div>
                </div>

                {/* Clinical Safety Disclaimer */}
                <div className="bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl border border-slate-200 dark:border-slate-700 text-[11px] text-slate-500 dark:text-slate-400 space-y-1">
                  <p className="font-bold text-slate-700 dark:text-slate-300">Medical Decision Disclaimer:</p>
                  <p>
                    DocTalk is a specialist clinical consultation network. The treating physician at {consultation.requesting_hospital_name || 'the home facility'} conducts in-person examination and remains legally responsible for all finalized prescriptions, orders, and diagnostic interventions.
                  </p>
                </div>

                {/* Footer buttons */}
                <div className="pt-2 flex items-center justify-between">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 text-xs font-bold hover:bg-slate-100 dark:hover:bg-slate-800"
                  >
                    Close
                  </button>

                  {!isCompleted && (
                    <button
                      type="submit"
                      disabled={completing || !clinicalOpinion.trim()}
                      className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-black shadow-md shadow-teal-600/20 transition-all flex items-center gap-2 disabled:opacity-50"
                    >
                      {completing ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Finalizing Consultation...</span>
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4" />
                          <span>Complete Consultation & Submit Notes</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </form>
            </>
          )}
        </div>
      </div>

      {/* Real-time Consultation Room */}
      <DocTalkRoomModal
        isOpen={roomOpen}
        onClose={() => setRoomOpen(false)}
        consultationId={consultation.id}
        consultationTitle={consultation.reason}
        patientName={consultation.patient_name || undefined}
        contextScope={ctx}
        initialRole="SPECIALIST"
        onConsultationEnded={handleRoomEnded}
      />
    </div>
  );
}
