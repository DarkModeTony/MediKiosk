'use client';

import React, { useState, useEffect } from 'react';
import DoctorLayout from '@/components/layout/DoctorLayout';
import {
  Stethoscope,
  Building2,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Loader2,
  Play,
  FileText,
  UserCheck,
  RefreshCw,
  Globe2,
  AlertOctagon,
  ArrowRight,
} from 'lucide-react';
import {
  ConsultationResponse,
  listSpecialistConsultations,
  acceptConsultation,
  declineConsultation,
} from '@/lib/api/doctalk';
import SpecialistWorkspaceModal from '@/components/workspace/SpecialistWorkspaceModal';
import { cn } from '@/lib/utils';

export default function DocTalkSpecialistHub() {
  const [activeTab, setActiveTab] = useState<'incoming' | 'consultations'>('incoming');
  const [consultations, setConsultations] = useState<ConsultationResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Decline dialog state
  const [declineTarget, setDeclineTarget] = useState<ConsultationResponse | null>(null);
  const [declineReason, setDeclineReason] = useState<string>('');
  const [declining, setDeclining] = useState<boolean>(false);

  // Active workspace modal state
  const [activeWorkspaceConsultation, setActiveWorkspaceConsultation] = useState<ConsultationResponse | null>(null);

  // Action feedback message
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchConsultations = async (showLoadingSpinner: boolean = true) => {
    if (showLoadingSpinner) setLoading(true);
    else setRefreshing(true);
    try {
      const data = await listSpecialistConsultations();
      setConsultations(data);
    } catch (err) {
      console.error('Failed to load specialist consultations:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchConsultations();
    const interval = setInterval(() => {
      fetchConsultations(false);
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  const handleAccept = async (c: ConsultationResponse) => {
    try {
      const updated = await acceptConsultation(c.id);
      setConsultations((prev) =>
        prev.map((item) => (item.id === c.id ? { ...item, status: 'ACCEPTED', accepted_at: updated.accepted_at } : item))
      );
      setToastMessage({
        type: 'success',
        text: `Consultation request from ${c.requesting_doctor_name || 'Dr. Rahul'} accepted. You may now inspect clinical context and start session.`,
      });
      // Promptly open specialist workspace
      setActiveWorkspaceConsultation(updated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to accept consultation';
      setToastMessage({ type: 'error', text: msg });
    }
  };

  const handleConfirmDecline = async () => {
    if (!declineTarget) return;
    setDeclining(true);
    try {
      const reasonToUse = declineReason.trim() || 'Specialist currently engaged in urgent patient care.';
      const updated = await declineConsultation(declineTarget.id, reasonToUse);
      setConsultations((prev) =>
        prev.map((item) => (item.id === declineTarget.id ? { ...item, status: 'DECLINED', decline_reason: reasonToUse } : item))
      );
      setDeclineTarget(null);
      setDeclineReason('');
      setToastMessage({
        type: 'success',
        text: 'Consultation request declined.',
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to decline consultation';
      setToastMessage({ type: 'error', text: msg });
    } finally {
      setDeclining(false);
    }
  };

  const incomingRequests = consultations.filter((c) => c.status === 'REQUESTED');
  const myConsultations = consultations.filter((c) => ['ACCEPTED', 'IN_PROGRESS', 'COMPLETED'].includes(c.status));

  return (
    <DoctorLayout>
      <div className="max-w-[1400px] mx-auto space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-500 to-teal-700 text-white flex items-center justify-center font-bold text-2xl shadow-md shadow-teal-600/20 shrink-0">
              <Stethoscope className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-xl font-black text-slate-900 dark:text-slate-100 tracking-tight">
                  DocTalk Requests
                </h1>
                <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-teal-100 dark:bg-teal-900/50 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                  Specialist Consultation Network
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Review and accept incoming 3–7 minute second opinion requests from treating doctors across partner hospitals.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 self-end sm:self-center">
            <button
              type="button"
              onClick={() => fetchConsultations(false)}
              disabled={refreshing}
              className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 text-xs font-semibold flex items-center gap-1.5 transition-colors"
              title="Refresh requests"
            >
              <RefreshCw className={cn('w-4 h-4', refreshing ? 'animate-spin text-teal-600' : '')} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Feedback Alert */}
        {toastMessage && (
          <div
            className={cn(
              'p-3.5 rounded-xl text-xs font-semibold flex items-center justify-between border animate-fade-in',
              toastMessage.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-200 dark:border-emerald-800'
                : 'bg-red-50 text-red-800 border-red-200 dark:bg-red-950/40 dark:text-red-200 dark:border-red-800'
            )}
          >
            <div className="flex items-center gap-2">
              {toastMessage.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
              )}
              <span>{toastMessage.text}</span>
            </div>
            <button
              type="button"
              onClick={() => setToastMessage(null)}
              className="text-slate-400 hover:text-slate-700 ml-4"
            >
              ✕
            </button>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800">
          <button
            type="button"
            onClick={() => setActiveTab('incoming')}
            className={cn(
              'px-5 py-3 text-sm font-bold border-b-2 transition-all flex items-center gap-2',
              activeTab === 'incoming'
                ? 'border-teal-500 text-teal-600 dark:text-teal-400 bg-white dark:bg-slate-800 rounded-t-xl'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            )}
          >
            <span>Incoming Requests</span>
            {incomingRequests.length > 0 && (
              <span className="w-5 h-5 rounded-full bg-teal-600 text-white text-[10px] font-black flex items-center justify-center">
                {incomingRequests.length}
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('consultations')}
            className={cn(
              'px-5 py-3 text-sm font-bold border-b-2 transition-all flex items-center gap-2',
              activeTab === 'consultations'
                ? 'border-teal-500 text-teal-600 dark:text-teal-400 bg-white dark:bg-slate-800 rounded-t-xl'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            )}
          >
            <span>My Consultations</span>
            {myConsultations.length > 0 && (
              <span className="w-5 h-5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 text-[10px] font-black flex items-center justify-center">
                {myConsultations.length}
              </span>
            )}
          </button>
        </div>

        {/* Tab 1: Incoming Requests */}
        {activeTab === 'incoming' && (
          <div className="space-y-4">
            {loading ? (
              <div className="py-20 text-center text-slate-400 flex flex-col items-center justify-center gap-3 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700">
                <Loader2 className="w-8 h-8 animate-spin text-teal-500" />
                <p className="text-sm font-semibold text-slate-600 dark:text-slate-300">
                  Checking cross-hospital incoming requests...
                </p>
              </div>
            ) : incomingRequests.length === 0 ? (
              <div className="py-20 text-center text-slate-400 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 space-y-3">
                <Stethoscope className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-600" />
                <p className="text-base font-bold text-slate-700 dark:text-slate-200">
                  No pending consultation requests
                </p>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  When treating physicians across partner facilities request a consultation in your specialty, requests will appear here in real time.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {incomingRequests.map((req) => (
                  <div
                    key={req.id}
                    className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-5 space-y-4 hover:border-teal-300 dark:hover:border-teal-700 transition-all"
                  >
                    {/* Top Row: Doctor, Hospital, Urgency, Duration */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-700/80 pb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-teal-50 dark:bg-teal-950/50 border border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-300 flex items-center justify-center font-bold text-sm shrink-0">
                          {req.requesting_doctor_name ? req.requesting_doctor_name.charAt(3) || 'D' : 'D'}
                        </div>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                              {req.requesting_doctor_name || 'Treating Physician'}
                            </h3>
                            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-cyan-700 dark:text-cyan-300 bg-cyan-50 dark:bg-cyan-950/40 px-2 py-0.5 rounded-full border border-cyan-200 dark:border-cyan-800">
                              <Globe2 className="w-2.5 h-2.5" />
                              {req.requesting_hospital_name || 'Hospital Alpha'}
                            </span>
                            <span className="text-[10px] font-semibold text-slate-400" suppressHydrationWarning>
                              Requested {req.created_at ? new Date(req.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recently'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                            Domain: <strong className="text-slate-700 dark:text-slate-300">{req.specialty}</strong>
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            'text-[10px] font-black uppercase px-2.5 py-1 rounded-lg',
                            req.urgency === 'URGENT'
                              ? 'bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-300'
                              : 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
                          )}
                        >
                          {req.urgency}
                        </span>
                        <span className="inline-flex items-center gap-1 text-[10px] font-black uppercase px-2.5 py-1 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950/50 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                          <Clock className="w-3 h-3" />
                          {req.requested_duration_minutes}m Window
                        </span>
                      </div>
                    </div>

                    {/* Reason for consultation */}
                    <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-750 border border-slate-200/80 dark:border-slate-700 space-y-1">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        Treating Doctor&apos;s Consultation Question
                      </p>
                      <p className="text-xs text-slate-800 dark:text-slate-200 font-medium leading-relaxed">
                        {req.reason}
                      </p>
                    </div>

                    {/* Minimized Pre-Acceptance Privacy Preview */}
                    <div className="flex items-center justify-between text-xs text-slate-500 bg-slate-50/50 dark:bg-slate-850 px-3.5 py-2 rounded-xl border border-slate-200/60 dark:border-slate-700/60">
                      <div className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                        <span className="font-semibold text-slate-700 dark:text-slate-300">
                          Pre-acceptance Privacy Guard Active
                        </span>
                        <span className="text-[11px] text-slate-400">
                          (Full clinical facts unlocked upon acceptance)
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400">
                        Facility: {req.requesting_hospital_name || 'Hospital Alpha'}
                      </span>
                    </div>

                    {/* Action buttons: Accept / Decline */}
                    <div className="flex items-center justify-end gap-3 pt-1">
                      <button
                        type="button"
                        onClick={() => setDeclineTarget(req)}
                        className="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950/30 text-xs font-bold transition-colors"
                      >
                        Decline
                      </button>

                      <button
                        type="button"
                        onClick={() => handleAccept(req)}
                        className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-black shadow-md shadow-teal-600/20 transition-all flex items-center gap-1.5 cursor-pointer"
                      >
                        <UserCheck className="w-4 h-4" />
                        <span>Accept Consultation ({req.requested_duration_minutes}m)</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: My Consultations */}
        {activeTab === 'consultations' && (
          <div className="space-y-4">
            {myConsultations.length === 0 ? (
              <div className="py-20 text-center text-slate-400 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 space-y-3">
                <FileText className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-600" />
                <p className="text-base font-bold text-slate-700 dark:text-slate-200">
                  No active or completed consultations yet
                </p>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  Accepted consultations will be tracked here with full clinical context and opinion recording.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {myConsultations.map((c) => (
                  <div
                    key={c.id}
                    className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-5 space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span
                            className={cn(
                              'text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full',
                              c.status === 'ACCEPTED'
                                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200'
                                : c.status === 'IN_PROGRESS'
                                ? 'bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-200'
                                : 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
                            )}
                          >
                            {c.status}
                          </span>
                          <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                            {c.specialty} Consultation
                          </span>
                          <span className="text-xs text-slate-400">·</span>
                          <span className="text-xs text-slate-500">
                            Dr. {c.requesting_doctor_name || 'Treating Doctor'} ({c.requesting_hospital_name || 'Partner Facility'})
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 line-clamp-1">
                          {c.reason}
                        </p>
                      </div>

                      <div className="flex items-center gap-2 self-end sm:self-center">
                        <button
                          type="button"
                          onClick={() => setActiveWorkspaceConsultation(c)}
                          className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-sm transition-all flex items-center gap-1.5"
                        >
                          <span>Open Specialist Workspace</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Decline Reason Modal */}
        {declineTarget && (
          <div
            role="dialog"
            aria-modal="true"
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in"
          >
            <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Decline Consultation Request
                </h3>
                <button
                  type="button"
                  onClick={() => setDeclineTarget(null)}
                  className="text-slate-400 hover:text-slate-700"
                >
                  ✕
                </button>
              </div>

              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Please specify a reason for declining. This will be shared with the treating physician so they can route the request to another specialist.
              </p>

              <textarea
                rows={3}
                placeholder="e.g. Currently scrubbed in operating theater / ICU rounds..."
                value={declineReason}
                onChange={(e) => setDeclineReason(e.target.value)}
                className="w-full text-xs px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />

              <div className="flex items-center justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setDeclineTarget(null)}
                  disabled={declining}
                  className="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-600 dark:text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmDecline}
                  disabled={declining}
                  className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition-all disabled:opacity-50"
                >
                  {declining ? 'Declining...' : 'Confirm Decline'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Specialist Workspace Modal */}
        {activeWorkspaceConsultation && (
          <SpecialistWorkspaceModal
            isOpen={Boolean(activeWorkspaceConsultation)}
            onClose={() => setActiveWorkspaceConsultation(null)}
            consultation={activeWorkspaceConsultation}
            onConsultationUpdated={(updated) => {
              setConsultations((prev) =>
                prev.map((c) => (c.id === updated.id ? { ...c, ...updated } : c))
              );
              setActiveWorkspaceConsultation((curr) => (curr && curr.id === updated.id ? { ...curr, ...updated } : curr));
            }}
          />
        )}
      </div>
    </DoctorLayout>
  );
}
