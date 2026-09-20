'use client';

import React, { useState, useEffect, useId } from 'react';
import {
  Stethoscope,
  X,
  Sparkles,
  Search,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Building2,
  Globe2,
  Loader2,
  UserCheck,
  ShieldCheck,
} from 'lucide-react';
import {
  SpecialistDirectoryItem,
  searchSpecialists,
  findAnySpecialist,
  createConsultationRequest,
  ConsultationResponse,
} from '@/lib/api/doctalk';
import { cn } from '@/lib/utils';

export const MEDICAL_SPECIALTIES = [
  'Cardiology',
  'Neurology',
  'Pulmonology',
  'Nephrology',
  'Gastroenterology',
  'Dermatology',
  'Orthopedics',
  'General Surgery',
  'Internal Medicine',
  'Pediatrics',
  'Endocrinology',
  'Psychiatry',
  'Oncology',
  'ENT',
];

interface DocTalkRequestDialogProps {
  isOpen: boolean;
  onClose: () => void;
  encounterId: string;
  patientName?: string;
  treatingHospitalName?: string;
  initialSpecialty?: string;
  hasActiveConsultation?: boolean;
  onRequestCreated: (consultation: ConsultationResponse) => void;
}

export default function DocTalkRequestDialog({
  isOpen,
  onClose,
  encounterId,
  patientName,
  treatingHospitalName = 'Apollo Hospitals',
  initialSpecialty = 'Cardiology',
  hasActiveConsultation = false,
  onRequestCreated,
}: DocTalkRequestDialogProps) {
  const dialogId = useId();
  const specialtySelectId = useId();
  const reasonInputId = useId();

  // Form states
  const [specialty, setSpecialty] = useState<string>(initialSpecialty);
  const [customSpecialty, setCustomSpecialty] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [urgency, setUrgency] = useState<'Normal' | 'Urgent'>('Normal');
  const [duration, setDuration] = useState<3 | 5 | 7>(5);
  
  // Selection mode: 'specific' (browse directory) by default so doctor explicitly selects recipient
  const [selectionMode, setSelectionMode] = useState<'any' | 'specific'>('specific');
  const [selectedSpecialist, setSelectedSpecialist] = useState<SpecialistDirectoryItem | null>(null);

  // Specialist browsing
  const [specialists, setSpecialists] = useState<SpecialistDirectoryItem[]>([]);
  const [loadingSpecialists, setLoadingSpecialists] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Submission state
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Explicit sharing preferences states
  const [includeHistory, setIncludeHistory] = useState<boolean>(true);
  const [includeVitals, setIncludeVitals] = useState<boolean>(true);
  const [includeAllergies, setIncludeAllergies] = useState<boolean>(true);
  const [includeMedications, setIncludeMedications] = useState<boolean>(true);
  const [includeConditions, setIncludeConditions] = useState<boolean>(true);
  const [includeInvestigations, setIncludeInvestigations] = useState<boolean>(true);
  const [includeDocuments, setIncludeDocuments] = useState<boolean>(true);
  const [includeSummary, setIncludeSummary] = useState<boolean>(true);
  const [showSharingDetails, setShowSharingDetails] = useState<boolean>(false);

  const activeSpecialty = customSpecialty.trim() || specialty;

  // Load specialists when specialty changes or dialog opens
  useEffect(() => {
    if (!isOpen) return;
    let isMounted = true;
    setLoadingSpecialists(true);
    setErrorMessage(null);

    searchSpecialists({ specialty: activeSpecialty })
      .then((data) => {
        if (isMounted) {
          setSpecialists(data);
          // If a selected specialist is not in the new list, pick the first one
          if (!selectedSpecialist || !data.some((d) => d.doctor_id === selectedSpecialist.doctor_id)) {
            setSelectedSpecialist(data.length > 0 ? data[0] : null);
          }
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error('Failed to load specialists:', err);
        }
      })
      .finally(() => {
        if (isMounted) setLoadingSpecialists(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, activeSpecialty]);

  // Handle keyboard ESC to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (hasActiveConsultation) {
      setErrorMessage('An active consultation request is already open for this encounter.');
      return;
    }

    if (!reason.trim()) {
      setErrorMessage('Please provide a brief reason for the consultation.');
      return;
    }

    if (!activeSpecialty) {
      setErrorMessage('Please select or specify a specialty.');
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);

    try {
      let specialistIdToUse = selectedSpecialist?.doctor_id || null;

      // If user chose "Find Any Available Specialist", use findAnySpecialist to resolve specialist if needed
      if (selectionMode === 'any') {
        const findAnyRes = await findAnySpecialist(activeSpecialty);
        if (findAnyRes.found && findAnyRes.specialist) {
          specialistIdToUse = findAnyRes.specialist.doctor_id;
        }
      }

      const created = await createConsultationRequest(
        {
          encounter_id: encounterId,
          specialty: activeSpecialty,
          reason: reason.trim(),
          urgency: urgency === 'Urgent' ? 'URGENT' : 'ROUTINE',
          requested_duration_minutes: duration,
          specialist_id: specialistIdToUse,
          sharing_preferences: {
            include_history: includeHistory,
            include_vitals: includeVitals,
            include_allergies: includeAllergies,
            include_medications: includeMedications,
            include_conditions: includeConditions,
            include_investigations: includeInvestigations,
            include_documents: includeDocuments,
            include_summary: includeSummary,
          },
        },
        true
      );

      onRequestCreated(created);
      onClose();
    } catch (err: unknown) {
      console.error('Failed to create DocTalk request:', err);
      const msg = err instanceof Error ? err.message : 'Unable to send consultation request. Please try again.';
      setErrorMessage(msg);
    } finally {
      setSubmitting(false);
    }
  };

  // Filtered specialists based on search query in the modal
  const filteredSpecialists = specialists.filter((s) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      s.display_name.toLowerCase().includes(q) ||
      (s.hospital_name && s.hospital_name.toLowerCase().includes(q)) ||
      (s.sub_specialty && s.sub_specialty.toLowerCase().includes(q))
    );
  });

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={`${dialogId}-title`}
      aria-describedby={`${dialogId}-description`}
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto animate-fade-in"
    >
      <div
        className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden my-auto max-h-[92vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4.5 border-b border-slate-200 dark:border-slate-800 bg-gradient-to-r from-teal-50/80 via-white to-cyan-50/50 dark:from-slate-800/80 dark:via-slate-900 dark:to-slate-800/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-md shadow-teal-600/20">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id={`${dialogId}-title`} className="text-lg font-black text-slate-900 dark:text-slate-100 tracking-tight">
                  DocTalk: Ask a Specialist
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-teal-100 dark:bg-teal-900/50 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                  Cross-Hospital Network
                </span>
              </div>
              <p id={`${dialogId}-description`} className="text-xs text-slate-500 dark:text-slate-400">
                Need another doctor&apos;s input on this case? Request a focused 3–7 minute second opinion.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Duplicate warning banner */}
        {hasActiveConsultation && (
          <div className="bg-amber-50 dark:bg-amber-950/40 border-b border-amber-200 dark:border-amber-800/60 px-6 py-3 flex items-center gap-2 text-amber-800 dark:text-amber-200 text-xs font-semibold">
            <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
            <span>
              An active DocTalk consultation is already open for this encounter. Complete or cancel the active consultation before creating another request.
            </span>
          </div>
        )}

        {/* Error message */}
        {errorMessage && (
          <div className="bg-red-50 dark:bg-red-950/40 border-b border-red-200 dark:border-red-800/60 px-6 py-3 flex items-center gap-2 text-red-800 dark:text-red-200 text-xs font-semibold">
            <AlertTriangle className="w-4 h-4 shrink-0 text-red-600" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Scrollable Form Content */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* Patient Context Tag */}
          {patientName && (
            <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl px-3.5 py-2 border border-slate-200 dark:border-slate-700/60 flex items-center justify-between text-xs text-slate-600 dark:text-slate-400">
              <span>
                Case: <strong className="text-slate-800 dark:text-slate-200">{patientName}</strong>
              </span>
              <span>
                Treating Facility: <strong className="text-slate-800 dark:text-slate-200">{treatingHospitalName}</strong>
              </span>
            </div>
          )}

          {/* 1. Specialty Selection */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label htmlFor={specialtySelectId} className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Specialty <span className="text-red-500">*</span>
              </label>
              <span className="text-[11px] text-slate-400">Select consultation domain</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 max-h-36 overflow-y-auto p-1 border border-slate-200 dark:border-slate-700 rounded-xl bg-slate-50/50 dark:bg-slate-800/30">
              {MEDICAL_SPECIALTIES.map((spec) => {
                const isSelected = specialty === spec && !customSpecialty;
                return (
                  <button
                    key={spec}
                    type="button"
                    onClick={() => {
                      setSpecialty(spec);
                      setCustomSpecialty('');
                      setSelectedSpecialist(null);
                    }}
                    className={cn(
                      'text-left px-3 py-2 rounded-lg text-xs font-semibold transition-all flex items-center justify-between border',
                      isSelected
                        ? 'bg-teal-600 text-white border-teal-600 shadow-sm'
                        : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-teal-400 dark:hover:border-teal-600'
                    )}
                  >
                    <span>{spec}</span>
                    {isSelected && <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />}
                  </button>
                );
              })}
            </div>
            {/* Custom specialty alternative */}
            <div className="pt-1">
              <input
                id={specialtySelectId}
                type="text"
                placeholder="Or type custom specialty (e.g. Pediatric Cardiology)..."
                value={customSpecialty}
                onChange={(e) => {
                  setCustomSpecialty(e.target.value);
                  setSelectedSpecialist(null);
                }}
                className="w-full text-xs px-3 py-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all"
              />
            </div>
          </div>

          {/* 2. Reason for Consultation */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label htmlFor={reasonInputId} className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Reason for Consultation <span className="text-red-500">*</span>
              </label>
              <span className="text-[11px] text-slate-400">{reason.length}/500 chars</span>
            </div>
            <textarea
              id={reasonInputId}
              rows={3}
              maxLength={500}
              placeholder="e.g. 42M with persistent fever and elevated BP. Need advice on adjusting antihypertensives given borderline creatinine and penicillin allergy..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full text-xs px-3.5 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all resize-none"
            />
          </div>

          {/* 3. Urgency & Duration Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Urgency */}
            <div className="space-y-2">
              <span className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Urgency
              </span>
              <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Urgency level">
                <button
                  type="button"
                  role="radio"
                  aria-checked={urgency === 'Normal'}
                  onClick={() => setUrgency('Normal')}
                  className={cn(
                    'px-3 py-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition-all',
                    urgency === 'Normal'
                      ? 'bg-teal-50 dark:bg-teal-950/40 border-teal-500 text-teal-700 dark:text-teal-300 shadow-sm ring-1 ring-teal-500'
                      : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300'
                  )}
                >
                  <span className="w-2 h-2 rounded-full bg-teal-500" />
                  <span>Normal</span>
                </button>
                <button
                  type="button"
                  role="radio"
                  aria-checked={urgency === 'Urgent'}
                  onClick={() => setUrgency('Urgent')}
                  className={cn(
                    'px-3 py-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition-all',
                    urgency === 'Urgent'
                      ? 'bg-amber-50 dark:bg-amber-950/40 border-amber-500 text-amber-700 dark:text-amber-300 shadow-sm ring-1 ring-amber-500'
                      : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300'
                  )}
                >
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                  <span>Urgent</span>
                </button>
              </div>
            </div>

            {/* Duration (Strictly 3, 5, 7 mins) */}
            <div className="space-y-2">
              <span className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Duration (Gated)
              </span>
              <div className="grid grid-cols-3 gap-1.5" role="radiogroup" aria-label="Consultation duration">
                {([3, 5, 7] as const).map((mins) => {
                  const isSelected = duration === mins;
                  return (
                    <button
                      key={mins}
                      type="button"
                      role="radio"
                      aria-checked={isSelected}
                      onClick={() => setDuration(mins)}
                      className={cn(
                        'px-2 py-2.5 rounded-xl border text-xs font-bold flex flex-col items-center justify-center transition-all',
                        isSelected
                          ? 'bg-teal-600 text-white border-teal-600 shadow-sm ring-1 ring-teal-500'
                          : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-teal-400'
                      )}
                    >
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>{mins}m</span>
                      </div>
                      <span className={cn('text-[9px] font-normal mt-0.5', isSelected ? 'text-teal-100' : 'text-slate-400')}>
                        {mins === 3 ? 'Rapid' : mins === 5 ? 'Standard' : 'Extended'}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* 4. Specialist Selection Mode */}
          <div className="space-y-3 pt-1 border-t border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between">
              <span className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Specialist Routing
              </span>
              <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-0.5 rounded-lg text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => {
                    setSelectionMode('any');
                    setSelectedSpecialist(null);
                  }}
                  className={cn(
                    'px-2.5 py-1 rounded-md transition-all',
                    selectionMode === 'any'
                      ? 'bg-white dark:bg-slate-700 text-teal-700 dark:text-teal-300 shadow-xs'
                      : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                  )}
                >
                  ⚡ Find Any Online
                </button>
                <button
                  type="button"
                  onClick={() => setSelectionMode('specific')}
                  className={cn(
                    'px-2.5 py-1 rounded-md transition-all',
                    selectionMode === 'specific'
                      ? 'bg-white dark:bg-slate-700 text-teal-700 dark:text-teal-300 shadow-xs'
                      : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                  )}
                >
                  🔍 Select Specific
                </button>
              </div>
            </div>

            {/* Mode A: Fast Find Any explanation */}
            {selectionMode === 'any' ? (
              <div className="p-3.5 rounded-xl bg-gradient-to-r from-teal-50 to-cyan-50 dark:from-teal-950/30 dark:to-cyan-950/20 border border-teal-200 dark:border-teal-800/60 flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                <div className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                  <p className="font-semibold text-slate-800 dark:text-slate-100">
                    Deterministic 1-Click Specialist Routing
                  </p>
                  <p className="mt-0.5 text-slate-500 dark:text-slate-400">
                    DocTalk will instantly match your request with the first available verified 🟢 ONLINE specialist in{' '}
                    <strong>{activeSpecialty}</strong> across the cross-hospital network (zero AI ranking or ratings).
                  </p>
                </div>
              </div>
            ) : (
              /* Mode B: Browse Specialist Directory */
              <div className="space-y-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search doctor or hospital..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full text-xs pl-8 pr-3 py-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div className="max-h-48 overflow-y-auto space-y-2 p-1">
                  {loadingSpecialists ? (
                    <div className="py-6 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-teal-500" />
                      <span>Checking specialist availability across network...</span>
                    </div>
                  ) : filteredSpecialists.length === 0 ? (
                    <div className="py-6 text-center text-slate-400 text-xs bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-700">
                      No verified specialists found for {activeSpecialty}. You can use &ldquo;Find Any Online&rdquo; to match automatically when a doctor logs in.
                    </div>
                  ) : (
                    filteredSpecialists.map((doc) => {
                      const isSelected = selectedSpecialist?.doctor_id === doc.doctor_id;
                      const isOnline = doc.availability_status === 'ONLINE';
                      const isBusy = doc.availability_status === 'BUSY';
                      const isOtherHospital = doc.hospital_name && doc.hospital_name !== treatingHospitalName;

                      return (
                        <div
                          key={doc.doctor_id}
                          onClick={() => setSelectedSpecialist(doc)}
                          className={cn(
                            'p-3 rounded-xl border text-xs cursor-pointer transition-all flex items-center justify-between gap-3',
                            isSelected
                              ? 'bg-teal-50 dark:bg-teal-950/40 border-teal-500 ring-1 ring-teal-500'
                              : 'bg-white dark:bg-slate-800/80 border-slate-200 dark:border-slate-700 hover:border-teal-300 dark:hover:border-teal-700'
                          )}
                        >
                          <div className="space-y-1 min-w-0 flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-bold text-slate-900 dark:text-slate-100">{doc.display_name}</span>
                              {doc.qualification && (
                                <span className="text-[10px] text-slate-400 font-medium">({doc.qualification})</span>
                              )}
                              {/* Availability Pill */}
                              <span
                                className={cn(
                                  'inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full',
                                  isOnline
                                    ? 'bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300'
                                    : isBusy
                                    ? 'bg-amber-100 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300'
                                    : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                                )}
                              >
                                <span
                                  className={cn(
                                    'w-1.5 h-1.5 rounded-full',
                                    isOnline ? 'bg-emerald-500' : isBusy ? 'bg-amber-500' : 'bg-slate-400'
                                  )}
                                />
                                {isOnline ? 'Available' : isBusy ? 'Busy' : 'Offline'}
                              </span>
                            </div>

                            <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-[11px] flex-wrap">
                              <span>{doc.specialty}</span>
                              {doc.sub_specialty && (
                                <>
                                  <span className="w-1 h-1 bg-slate-300 rounded-full" />
                                  <span>{doc.sub_specialty}</span>
                                </>
                              )}
                              <span className="w-1 h-1 bg-slate-300 rounded-full" />
                              <span className="flex items-center gap-1 text-slate-600 dark:text-slate-300 font-medium">
                                <Building2 className="w-3 h-3 text-slate-400" />
                                {doc.hospital_name || 'Network Hospital'}
                              </span>
                            </div>

                            {/* External hospital notice */}
                            {isOtherHospital && (
                              <div className="pt-0.5">
                                <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-cyan-700 dark:text-cyan-300 bg-cyan-50 dark:bg-cyan-950/40 px-1.5 py-0.5 rounded border border-cyan-200 dark:border-cyan-800">
                                  <Globe2 className="w-2.5 h-2.5" />
                                  External Hospital Specialist
                                </span>
                              </div>
                            )}
                          </div>

                          <div className="shrink-0">
                            {isSelected ? (
                              <span className="flex items-center gap-1 text-xs font-bold text-teal-600 dark:text-teal-400">
                                <CheckCircle2 className="w-4 h-4" />
                                Selected
                              </span>
                            ) : (
                              <button
                                type="button"
                                className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-slate-700 hover:bg-teal-50 hover:text-teal-700 dark:hover:bg-teal-900/30 dark:hover:text-teal-300 transition-colors"
                              >
                                Select
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            )}
          </div>

          {/* 5. Explicit Context Sharing (Privacy & Security Boundary) */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 p-3 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                <span className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                  Shared Consultation Context
                </span>
              </div>
              <button
                type="button"
                onClick={() => setShowSharingDetails(!showSharingDetails)}
                className="text-[11px] font-semibold text-teal-600 dark:text-teal-400 hover:underline"
              >
                {showSharingDetails ? 'Hide Options' : 'Customize Sharing'}
              </button>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Cross-hospital isolation active: Specialist receives a strictly scoped, source-traceable snapshot with patient demographics minimized.
            </p>

            {showSharingDetails && (
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200 dark:border-slate-800 text-xs">
                <label className="flex items-center gap-2 text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeHistory}
                    onChange={(e) => setIncludeHistory(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>Clinical History & Symptoms</span>
                </label>
                <label className="flex items-center gap-2 text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeVitals}
                    onChange={(e) => setIncludeVitals(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>Vitals & Exam Findings</span>
                </label>
                <label className="flex items-center gap-2 text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeAllergies}
                    onChange={(e) => setIncludeAllergies(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>Confirmed Allergies</span>
                </label>
                <label className="flex items-center gap-2 text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeMedications}
                    onChange={(e) => setIncludeMedications(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>Active Medications</span>
                </label>
                <label className="flex items-center gap-2 text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeConditions}
                    onChange={(e) => setIncludeConditions(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>Chronic Conditions</span>
                </label>
                <label className="flex items-center gap-2 text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeInvestigations}
                    onChange={(e) => setIncludeInvestigations(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>Recent Investigations</span>
                </label>
                <label className="flex items-center gap-2 text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeDocuments}
                    onChange={(e) => setIncludeDocuments(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>Uploaded Documents</span>
                </label>
                <label className="flex items-center gap-2 text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeSummary}
                    onChange={(e) => setIncludeSummary(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>Clinical Summary Draft</span>
                </label>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-bold hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={submitting || hasActiveConsultation || !reason.trim() || !activeSpecialty}
              className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-black shadow-md shadow-teal-600/20 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Submitting Request...</span>
                </>
              ) : (
                <>
                  <UserCheck className="w-4 h-4" />
                  <span>Request Consultation ({duration} min)</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
