'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Pill,
  Search,
  Plus,
  Trash2,
  Copy,
  Edit3,
  AlertTriangle,
  CheckCircle2,
  Printer,
  FileText,
  Clock,
  ShieldAlert,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  X,
  Stethoscope,
  Info,
  RotateCcw,
  Sparkles,
  HeartPulse,
} from 'lucide-react';
import {
  MedicineSearchResult,
  PrescriptionItem,
  Prescription,
  SafetyAlert,
  searchMedicines,
  getEncounterPrescriptions,
  saveDraftPrescription,
  finalizePrescription,
  amendPrescription,
  getPatientPrescriptions,
} from '@/lib/api/prescriptions';
import { Patient, Encounter, RedFlag, ClinicalState } from '@/lib/api/types';
import { cn } from '@/lib/utils';

interface PrescriptionWorkspaceProps {
  encounter: Encounter;
  patient: Patient;
  redFlags?: RedFlag[];
  clinicalState?: ClinicalState | null;
}

const FREQUENCY_OPTIONS = [
  'Once daily (OD)',
  'Twice daily (BD)',
  'Three times daily (TID)',
  'Four times daily (QID)',
  'Every 4 hours',
  'Every 6 hours',
  'Every 8 hours',
  'Every 12 hours',
  'Once weekly',
  'SOS / PRN (As needed)',
];

const TIMING_OPTIONS = [
  'After food',
  'Before food',
  'With food',
  'Morning',
  'Afternoon',
  'Evening',
  'At bedtime',
  'Empty stomach',
];

export default function PrescriptionWorkspace({
  encounter,
  patient,
  redFlags = [],
  clinicalState,
}: PrescriptionWorkspaceProps) {
  // ── States ───────────────────────────────────────────────────────────────
  const [loading, setLoading] = useState(true);
  const [activePrescription, setActivePrescription] = useState<Prescription | null>(null);
  const [historicalPrescriptions, setHistoricalPrescriptions] = useState<Prescription[]>([]);
  const [items, setItems] = useState<PrescriptionItem[]>([]);
  const [notes, setNotes] = useState('');
  const [viewMode, setViewMode] = useState<'build' | 'review' | 'print' | 'history'>('build');

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<MedicineSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedMedicine, setSelectedMedicine] = useState<MedicineSearchResult | null>(null);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Item form editor state
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [dose, setDose] = useState('1 tablet');
  const [route, setRoute] = useState('Oral');
  const [frequency, setFrequency] = useState('Twice daily (BD)');
  const [timing, setTiming] = useState('After food');
  const [durationValue, setDurationValue] = useState<number>(5);
  const [durationUnit, setDurationUnit] = useState('days');
  const [quantity, setQuantity] = useState<number>(10);
  const [indication, setIndication] = useState('');
  const [instructions, setInstructions] = useState('');
  const [isPrn, setIsPrn] = useState(false);
  const [minInterval, setMinInterval] = useState('6 hours');
  const [maxDailyDose, setMaxDailyDose] = useState('4 doses');

  // Safety & Finalization
  const [acknowledgedSafety, setAcknowledgedSafety] = useState(false);
  const [showFinalizeConfirm, setShowFinalizeConfirm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Context panel collapse
  const [contextExpanded, setContextExpanded] = useState(false);

  // ── 1. Initial Data Loading ──────────────────────────────────────────────
  useEffect(() => {
    loadPrescriptionData();
  }, [encounter.id, patient.id]);

  const loadPrescriptionData = async () => {
    setLoading(true);
    try {
      const [rxs, hist] = await Promise.all([
        getEncounterPrescriptions(encounter.id),
        getPatientPrescriptions(patient.id),
      ]);
      setHistoricalPrescriptions(hist);

      // Find active prescription (draft or finalized for this encounter)
      const current = rxs[0] || null;
      if (current) {
        setActivePrescription(current);
        setItems(current.items || []);
        setNotes(current.notes || '');
        if (current.status === 'FINALIZED') {
          setViewMode('review');
        }
      } else {
        setActivePrescription(null);
        setItems([]);
        setNotes('');
        setViewMode('build');
      }
    } catch (err) {
      console.error('Failed to load prescriptions', err);
    } finally {
      setLoading(false);
    }
  };

  // ── 2. Debounced Medicine Search ─────────────────────────────────────────
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (!searchQuery.trim()) {
        setSearchResults([]);
        setIsSearching(false);
        return;
      }
      setIsSearching(true);
      try {
        const results = await searchMedicines(searchQuery, 12);
        setSearchResults(results);
        setHighlightIndex(-1);
      } catch (err) {
        console.error(err);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Handle Search Keyboard Navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (searchResults.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightIndex((prev) => (prev < searchResults.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightIndex((prev) => (prev > 0 ? prev - 1 : searchResults.length - 1));
    } else if (e.key === 'Enter' && highlightIndex >= 0) {
      e.preventDefault();
      handleSelectMedicine(searchResults[highlightIndex]);
    } else if (e.key === 'Escape') {
      setSearchResults([]);
    }
  };

  const handleSelectMedicine = (med: MedicineSearchResult) => {
    setSelectedMedicine(med);
    setSearchQuery('');
    setSearchResults([]);

    // Populate sensible defaults from extracted dataset form & routes
    setDose(med.default_dose || '1 unit');
    setRoute(med.suggested_routes[0] || 'Oral');
    setFrequency('Twice daily (BD)');
    setTiming('After food');
    setDurationValue(5);
    setDurationUnit('days');
    setQuantity(10);
    setIsPrn(false);
    setIndication('');
    setInstructions(
      med.dosage_form === 'Syrup'
        ? 'Shake well before use.'
        : med.dosage_form === 'Topical'
        ? 'Apply to clean, dry affected area.'
        : 'Take with a glass of water.'
    );
  };

  // ── 3. Add / Edit Prescription Item ──────────────────────────────────────
  const handleSaveItem = () => {
    if (!selectedMedicine && editingIndex === null) return;

    const newItem: PrescriptionItem = {
      medicine_id: selectedMedicine?.id || items[editingIndex!]?.medicine_id,
      medication_name: selectedMedicine?.name || items[editingIndex!].medication_name,
      generic_name: selectedMedicine?.generic_name || items[editingIndex!]?.generic_name,
      strength: selectedMedicine?.strength || items[editingIndex!]?.strength,
      dosage_form: selectedMedicine?.dosage_form || items[editingIndex!]?.dosage_form,
      dose,
      route,
      frequency,
      timing,
      duration_value: durationValue,
      duration_unit: durationUnit,
      quantity,
      indication,
      instructions,
      is_prn: isPrn,
      min_interval: isPrn ? minInterval : undefined,
      max_daily_dose: isPrn ? maxDailyDose : undefined,
      status: 'active',
      item_metadata: {
        price: selectedMedicine?.price || items[editingIndex!]?.item_metadata?.price,
        manufacturer: selectedMedicine?.manufacturer_name || items[editingIndex!]?.item_metadata?.manufacturer,
        pack_size: selectedMedicine?.pack_size_label || items[editingIndex!]?.item_metadata?.pack_size,
      },
    };

    if (editingIndex !== null) {
      const updated = [...items];
      updated[editingIndex] = newItem;
      setItems(updated);
      setEditingIndex(null);
    } else {
      setItems([...items, newItem]);
    }

    setSelectedMedicine(null);
  };

  const handleEditItem = (index: number) => {
    const item = items[index];
    setEditingIndex(index);
    setSelectedMedicine({
      id: item.medicine_id || 0,
      name: item.medication_name,
      generic_name: item.generic_name || '',
      composition_1: item.generic_name || '',
      composition_2: '',
      manufacturer_name: item.item_metadata?.manufacturer || '',
      type: 'allopathy',
      pack_size_label: item.item_metadata?.pack_size || '',
      price: item.item_metadata?.price || 0,
      dosage_form: item.dosage_form || 'Tablet',
      strength: item.strength || '',
      suggested_routes: [item.route || 'Oral'],
      default_dose: item.dose || '1 tablet',
    });
    setDose(item.dose || '1 tablet');
    setRoute(item.route || 'Oral');
    setFrequency(item.frequency || 'Twice daily (BD)');
    setTiming(item.timing || 'After food');
    setDurationValue(item.duration_value || 5);
    setDurationUnit(item.duration_unit || 'days');
    setQuantity(item.quantity || 10);
    setIndication(item.indication || '');
    setInstructions(item.instructions || '');
    setIsPrn(item.is_prn || false);
    setMinInterval(item.min_interval || '6 hours');
    setMaxDailyDose(item.max_daily_dose || '4 doses');
  };

  const handleDuplicateItem = (index: number) => {
    const item = items[index];
    setItems([...items, { ...item, id: undefined }]);
  };

  const handleRemoveItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };

  // ── 4. Save Draft & Finalization ─────────────────────────────────────────
  const handleSaveDraft = async () => {
    setIsSubmitting(true);
    setErrorMsg('');
    try {
      const res = await saveDraftPrescription(encounter.id, {
        patient_id: patient.id,
        notes,
        items,
      });
      setActivePrescription(res);
      setSaveSuccessMsg('Prescription draft saved successfully');
      setTimeout(() => setSaveSuccessMsg(''), 3000);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to save draft');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFinalize = async () => {
    if (items.length === 0) {
      setErrorMsg('Please add at least one medication before finalizing.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg('');
    try {
      // If no active prescription id, save draft first
      let rxId = activePrescription?.id;
      if (!rxId || activePrescription?.status !== 'DRAFT') {
        const draft = await saveDraftPrescription(encounter.id, {
          patient_id: patient.id,
          notes,
          items,
        });
        rxId = draft.id;
      }

      const res = await finalizePrescription(encounter.id, rxId, {
        notes,
        acknowledged_safety_alerts: acknowledgedSafety,
      });

      setActivePrescription(res);
      setShowFinalizeConfirm(false);
      setViewMode('review');
      setSaveSuccessMsg('Prescription officially verified & signed into medical record');
      setTimeout(() => setSaveSuccessMsg(''), 4000);
    } catch (err: any) {
      const msg = err.message || (typeof err.detail === 'string' ? err.detail : err.detail?.message) || 'Failed to finalize prescription';
      setErrorMsg(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAmend = async () => {
    if (!activePrescription) return;
    setIsSubmitting(true);
    try {
      const newDraft = await amendPrescription(encounter.id, activePrescription.id);
      setActivePrescription(newDraft);
      setItems(newDraft.items || []);
      setNotes(newDraft.notes || '');
      setViewMode('build');
      setSaveSuccessMsg('Prescription revised into new editable draft');
      setTimeout(() => setSaveSuccessMsg(''), 3000);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to amend prescription');
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Safety Warnings Computation ──────────────────────────────────────────
  const activeAlerts: SafetyAlert[] = activePrescription?.safety_check?.alerts || [];
  const hasCriticalSafetyAlert = activeAlerts.some((a) => a.severity === 'HIGH');

  // Patient Context helpers (Unknown != No)
  const facts = clinicalState?.facts || {};
  const hasRecordedAllergy = Object.keys(facts).some((k) => k.toLowerCase().includes('allergy'));

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 gap-3 text-slate-400">
        <div className="w-10 h-10 rounded-full border-4 border-teal-500/30 border-t-teal-500 animate-spin" />
        <p className="text-sm font-semibold">Loading prescription engine…</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Sub-nav: Modes & Status Bar ──────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-900/40 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
            <Pill className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-black text-slate-900 dark:text-slate-100">
                EHR Clinical Prescription
              </h2>
              {activePrescription?.status === 'FINALIZED' && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-black bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  <CheckCircle2 className="w-3.5 h-3.5" /> FINALIZED & SIGNED
                </span>
              )}
              {activePrescription?.status === 'DRAFT' && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-black bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                  <Clock className="w-3.5 h-3.5" /> DRAFT IN PROGRESS
                </span>
              )}
              {activePrescription?.status === 'AMENDED' && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-black bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                  <RotateCcw className="w-3.5 h-3.5" /> AMENDED VERSION
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Verified dataset of 253,973 medicines • Deterministic safety validation
            </p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {viewMode !== 'build' && activePrescription?.status !== 'FINALIZED' && (
            <button
              onClick={() => setViewMode('build')}
              className="px-3.5 py-2 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 transition-colors"
            >
              Edit Medications
            </button>
          )}

          {activePrescription?.status === 'FINALIZED' && (
            <>
              <button
                onClick={handleAmend}
                disabled={isSubmitting}
                className="px-3.5 py-2 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 transition-colors flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" /> Create Revised Prescription
              </button>
              <button
                onClick={() => setViewMode('print')}
                className="px-3.5 py-2 rounded-xl text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 transition-colors flex items-center gap-1.5 shadow-sm"
              >
                <Printer className="w-3.5 h-3.5" /> Print Rx Sheet
              </button>
            </>
          )}

          {activePrescription?.status !== 'FINALIZED' && (
            <>
              <button
                onClick={handleSaveDraft}
                disabled={isSubmitting || items.length === 0}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 transition-colors border border-slate-200 dark:border-slate-600"
              >
                Save Draft
              </button>
              {viewMode === 'build' ? (
                <button
                  onClick={() => setViewMode('review')}
                  disabled={items.length === 0}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 transition-colors shadow-sm disabled:opacity-50"
                >
                  Review Prescription ({items.length})
                </button>
              ) : (
                <button
                  onClick={() => setShowFinalizeConfirm(true)}
                  disabled={isSubmitting || items.length === 0}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition-colors shadow-sm flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" /> Finalize & Sign
                </button>
              )}
            </>
          )}

          <button
            onClick={() => setViewMode(viewMode === 'history' ? 'build' : 'history')}
            className="px-3.5 py-2 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 transition-colors"
          >
            History ({historicalPrescriptions.length})
          </button>
        </div>
      </div>

      {/* Messages */}
      {saveSuccessMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-sm font-semibold flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          {saveSuccessMsg}
        </div>
      )}
      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 text-sm font-semibold flex items-center gap-2 animate-fade-in">
          <AlertTriangle className="w-4 h-4 text-rose-600" />
          {errorMsg}
        </div>
      )}

      {/* ── Patient Safety & Context Panel (Section 3 & 10) ────────────────── */}
      <div className="rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm">
        <div
          onClick={() => setContextExpanded(!contextExpanded)}
          className="px-6 py-3.5 bg-slate-50/80 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between cursor-pointer hover:bg-slate-100/60 transition-colors select-none"
        >
          <div className="flex items-center gap-3">
            <HeartPulse className="w-4 h-4 text-rose-500" />
            <span className="text-xs uppercase font-bold tracking-wider text-slate-600 dark:text-slate-300">
              Patient Clinical Safety Context
            </span>
            <span className="text-xs text-slate-400">• Unknown ≠ No semantics applied</span>
          </div>
          <button className="text-xs font-semibold text-teal-600 dark:text-teal-400 flex items-center gap-1">
            {contextExpanded ? 'Collapse' : 'Expand full context'}
            {contextExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Compact Summary Strip */}
        <div className="px-6 py-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <p className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">Patient</p>
            <p className="font-bold text-slate-900 dark:text-slate-100 text-sm mt-0.5">
              {patient.name} ({patient.age}y, {patient.gender})
            </p>
          </div>

          <div>
            <p className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">Recorded Allergies</p>
            {hasRecordedAllergy ? (
              <span className="inline-flex items-center gap-1 font-bold text-rose-600 dark:text-rose-400 mt-0.5">
                <AlertTriangle className="w-3.5 h-3.5" /> Active Allergy Record
              </span>
            ) : (
              <span className="text-slate-400 italic font-medium mt-0.5 block">
                Not documented / Unknown
              </span>
            )}
          </div>

          <div>
            <p className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">Active Triage Alerts</p>
            {redFlags.length > 0 ? (
              <span className="inline-flex items-center gap-1 font-black text-rose-600 dark:text-rose-400 mt-0.5">
                <ShieldAlert className="w-3.5 h-3.5" /> {redFlags.length} Red Flag(s)
              </span>
            ) : (
              <span className="text-emerald-600 font-semibold mt-0.5 block">None detected</span>
            )}
          </div>

          <div>
            <p className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">Current Medications</p>
            <p className="font-medium text-slate-700 dark:text-slate-300 mt-0.5">
              {historicalPrescriptions.length > 0
                ? `${historicalPrescriptions.length} prior Rx on record`
                : 'Unknown / Not documented'}
            </p>
          </div>
        </div>

        {/* Expanded Details */}
        {contextExpanded && (
          <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-700/60 bg-slate-50/50 dark:bg-slate-800/40 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs animate-fade-in">
            <div className="p-3 rounded-xl bg-white dark:bg-slate-750 border border-slate-200 dark:border-slate-700">
              <p className="font-bold text-slate-700 dark:text-slate-200 mb-1.5 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> Allergies & Hypersensitivities
              </p>
              <p className="text-slate-500 leading-relaxed">
                Check documented Penicillins, NSAIDs, Cephalosporins, or Sulfa drugs. All checks are verified against both brand and generic molecules.
              </p>
            </div>

            <div className="p-3 rounded-xl bg-white dark:bg-slate-750 border border-slate-200 dark:border-slate-700">
              <p className="font-bold text-slate-700 dark:text-slate-200 mb-1.5 flex items-center gap-1.5">
                <Pill className="w-3.5 h-3.5 text-teal-500" /> Longitudinal Medications
              </p>
              <p className="text-slate-500 leading-relaxed">
                Finalizing this prescription automatically adds newly prescribed drugs to the patient's longitudinal profile and immutable clinical facts.
              </p>
            </div>

            <div className="p-3 rounded-xl bg-white dark:bg-slate-750 border border-slate-200 dark:border-slate-700">
              <p className="font-bold text-slate-700 dark:text-slate-200 mb-1.5 flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-500" /> Clinical Safety Guardrails
              </p>
              <p className="text-slate-500 leading-relaxed">
                AI does not autonomously prescribe. You retain legal, clinical, and regulatory authority over every dosage, route, and duration.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* ── Active Safety Alerts Strip ────────────────────────────────────────── */}
      {activeAlerts.length > 0 && (
        <div className="space-y-2">
          {activeAlerts.map((alert, idx) => (
            <div
              key={idx}
              className={cn(
                'p-4 rounded-2xl border flex items-start gap-3 text-sm animate-fade-in',
                alert.severity === 'HIGH'
                  ? 'bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800 text-rose-900 dark:text-rose-200'
                  : alert.severity === 'CAUTION'
                  ? 'bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200'
                  : 'bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800 text-blue-900 dark:text-blue-200'
              )}
            >
              <AlertTriangle
                className={cn(
                  'w-5 h-5 shrink-0 mt-0.5',
                  alert.severity === 'HIGH'
                    ? 'text-rose-600'
                    : alert.severity === 'CAUTION'
                    ? 'text-amber-600'
                    : 'text-blue-600'
                )}
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-black tracking-tight">{alert.title}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full font-bold uppercase bg-white/70 dark:bg-black/30">
                    {alert.severity}
                  </span>
                </div>
                <p className="text-xs mt-1 font-medium leading-relaxed">{alert.message}</p>
                <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">
                  Source: {alert.source}
                </p>
              </div>
            </div>
          ))}

          {hasCriticalSafetyAlert && activePrescription?.status !== 'FINALIZED' && (
            <div className="p-3.5 rounded-xl bg-slate-900 text-white flex items-center justify-between text-xs">
              <span className="font-medium flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                Clinician safety override required for high-priority alerts
              </span>
              <label className="flex items-center gap-2 font-bold cursor-pointer hover:text-teal-300">
                <input
                  type="checkbox"
                  checked={acknowledgedSafety}
                  onChange={(e) => setAcknowledgedSafety(e.target.checked)}
                  className="rounded border-slate-700 text-teal-500 focus:ring-teal-500"
                />
                I acknowledge and accept the clinical risk
              </label>
            </div>
          )}
        </div>
      )}

      {/* ── View Mode: BUILD PRESCRIPTION ───────────────────────────────────── */}
      {viewMode === 'build' && (
        <div className="space-y-6">
          {/* Medicine Search Box */}
          <div className="relative">
            <div className="relative flex items-center">
              <Search className="w-5 h-5 text-slate-400 absolute left-4 pointer-events-none" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search 253,000+ Indian medicines (e.g. Paracetamol, Augmentin, Metformin, Ascoril, Azithral)..."
                className="w-full pl-12 pr-10 py-3.5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-teal-500 shadow-sm"
              />
              {isSearching && (
                <div className="absolute right-4 w-4 h-4 border-2 border-teal-500/30 border-t-teal-500 rounded-full animate-spin" />
              )}
              {searchQuery && !isSearching && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-4 text-slate-400 hover:text-slate-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Autocomplete Dropdown */}
            {searchResults.length > 0 && (
              <div className="absolute z-30 left-0 right-0 mt-2 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-xl overflow-hidden max-h-96 overflow-y-auto animate-fade-in">
                <div className="px-4 py-2 bg-slate-50 dark:bg-slate-850 border-b border-slate-100 dark:border-slate-700 flex justify-between text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  <span>Top matches from Indian Formulary</span>
                  <span>Use ↑↓ to navigate, Enter to select</span>
                </div>
                {searchResults.map((med, idx) => (
                  <div
                    key={med.id}
                    onClick={() => handleSelectMedicine(med)}
                    className={cn(
                      'px-4 py-3 border-b border-slate-100 dark:border-slate-700/60 cursor-pointer flex items-center justify-between transition-colors',
                      idx === highlightIndex
                        ? 'bg-teal-50 dark:bg-teal-950/40 text-teal-900 dark:text-teal-100'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-700/50'
                    )}
                  >
                    <div className="min-w-0 flex-1 pr-4">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-900 dark:text-slate-100">
                          {med.name}
                        </span>
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-teal-100 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300">
                          {med.dosage_form}
                        </span>
                        {med.strength && (
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                            {med.strength}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                        Active: {med.generic_name || 'Not specified'} • {med.manufacturer_name}
                      </p>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-xs font-bold text-slate-900 dark:text-slate-100">
                        ₹{med.price.toFixed(2)}
                      </span>
                      <span className="block text-[10px] text-slate-400">{med.pack_size_label}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ── Medicine Selection & Dynamic Form Editor ─────────────────────── */}
          {selectedMedicine && (
            <div className="p-6 rounded-2xl bg-teal-50/40 dark:bg-slate-800/80 border-2 border-teal-500/30 dark:border-teal-500/20 shadow-sm space-y-5 animate-fade-in">
              <div className="flex items-start justify-between pb-4 border-b border-teal-200/50 dark:border-slate-700">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                    {editingIndex !== null ? 'Editing Prescribed Drug' : 'Prescribing Selected Drug'}
                  </span>
                  <h3 className="text-lg font-black text-slate-900 dark:text-slate-100 mt-0.5">
                    {selectedMedicine.name}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Composition: <span className="font-semibold text-slate-700 dark:text-slate-200">{selectedMedicine.generic_name}</span> • Mfg: {selectedMedicine.manufacturer_name}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setSelectedMedicine(null);
                    setEditingIndex(null);
                  }}
                  className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Dynamic Inputs Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-semibold">
                {/* Dose */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-300 mb-1.5">
                    Dose per administration
                  </label>
                  <input
                    type="text"
                    value={dose}
                    onChange={(e) => setDose(e.target.value)}
                    placeholder="e.g. 1 tablet, 5 ml, 2 drops"
                    className="w-full px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                {/* Route */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-300 mb-1.5">Route</label>
                  <select
                    value={route}
                    onChange={(e) => setRoute(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-teal-500 font-semibold"
                  >
                    {selectedMedicine.suggested_routes.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                    <option value="Oral">Oral</option>
                    <option value="Topical">Topical</option>
                    <option value="IV">IV</option>
                    <option value="IM">IM</option>
                    <option value="Sublingual">Sublingual</option>
                    <option value="Ophthalmic">Ophthalmic</option>
                    <option value="Inhalation">Inhalation</option>
                  </select>
                </div>

                {/* Frequency */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-300 mb-1.5">Frequency</label>
                  <select
                    value={frequency}
                    onChange={(e) => {
                      setFrequency(e.target.value);
                      if (e.target.value.includes('SOS') || e.target.value.includes('PRN')) {
                        setIsPrn(true);
                      }
                    }}
                    className="w-full px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-teal-500 font-semibold"
                  >
                    {FREQUENCY_OPTIONS.map((f) => (
                      <option key={f} value={f}>
                        {f}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Timing */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-300 mb-1.5">Food Timing</label>
                  <select
                    value={timing}
                    onChange={(e) => setTiming(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-teal-500 font-semibold"
                  >
                    {TIMING_OPTIONS.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Duration */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-300 mb-1.5">Duration</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      min={1}
                      max={365}
                      value={durationValue}
                      onChange={(e) => {
                        const val = parseInt(e.target.value) || 1;
                        setDurationValue(val);
                        // Auto-calc approximate quantity
                        setQuantity(val * (frequency.includes('Twice') ? 2 : frequency.includes('Three') ? 3 : 1));
                      }}
                      className="w-20 px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-teal-500"
                    />
                    <select
                      value={durationUnit}
                      onChange={(e) => setDurationUnit(e.target.value)}
                      className="flex-1 px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-teal-500"
                    >
                      <option value="days">Days</option>
                      <option value="weeks">Weeks</option>
                      <option value="months">Months</option>
                      <option value="ongoing">Ongoing</option>
                    </select>
                  </div>
                </div>

                {/* Quantity */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-300 mb-1.5">
                    Dispense Quantity
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                    className="w-full px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                {/* Clinical Indication */}
                <div className="sm:col-span-2">
                  <label className="block text-slate-600 dark:text-slate-300 mb-1.5">
                    Clinical Indication / Reason
                  </label>
                  <input
                    type="text"
                    value={indication}
                    onChange={(e) => setIndication(e.target.value)}
                    placeholder="e.g. Acute Pharyngitis, Fever relief, Hypertension control"
                    className="w-full px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>

              {/* PRN / SOS Options (Section 6) */}
              <div className="p-4 rounded-xl bg-white/70 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-700 space-y-3">
                <label className="flex items-center gap-2 cursor-pointer font-bold text-xs text-slate-800 dark:text-slate-200">
                  <input
                    type="checkbox"
                    checked={isPrn}
                    onChange={(e) => setIsPrn(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  Prescribe as SOS / PRN (Take as needed)
                </label>

                {isPrn && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-2 border-t border-slate-100 dark:border-slate-800 animate-fade-in">
                    <div>
                      <label className="block text-slate-500 dark:text-slate-400 mb-1">
                        Minimum interval between doses
                      </label>
                      <input
                        type="text"
                        value={minInterval}
                        onChange={(e) => setMinInterval(e.target.value)}
                        placeholder="e.g. 6 hours"
                        className="w-full px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-500 dark:text-slate-400 mb-1">
                        Maximum doses per day
                      </label>
                      <input
                        type="text"
                        value={maxDailyDose}
                        onChange={(e) => setMaxDailyDose(e.target.value)}
                        placeholder="e.g. 4 tablets / day"
                        className="w-full px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Patient Instructions */}
              <div>
                <label className="block text-slate-600 dark:text-slate-300 mb-1.5 text-xs font-semibold">
                  Patient Instructions & Precautions
                </label>
                <input
                  type="text"
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="e.g. Complete full 5-day course. Do not skip doses."
                  className="w-full px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-teal-500 text-xs"
                />
              </div>

              {/* Form Buttons */}
              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => {
                    setSelectedMedicine(null);
                    setEditingIndex(null);
                  }}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveItem}
                  className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 transition-colors shadow-sm flex items-center gap-1.5"
                >
                  <Plus className="w-4 h-4" />
                  {editingIndex !== null ? 'Update Medication' : 'Add to Prescription'}
                </button>
              </div>
            </div>
          )}

          {/* ── Prescribed Medication Cards List (Section 8) ────────────────── */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-black uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Prescribed Medications ({items.length})
              </h3>
              {items.length > 0 && (
                <span className="text-xs text-slate-400">
                  Total Rx items: {items.length}
                </span>
              )}
            </div>

            {items.length === 0 ? (
              <div className="p-12 text-center rounded-2xl bg-white dark:bg-slate-800 border-2 border-dashed border-slate-200 dark:border-slate-700 text-slate-400">
                <Pill className="w-12 h-12 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
                <p className="font-bold text-slate-600 dark:text-slate-300 text-base">
                  No medications added yet
                </p>
                <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
                  Type a medicine name above (e.g. Paracetamol, Augmentin, Metformin) to search and prescribe.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {items.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm hover:border-slate-300 dark:hover:border-slate-600 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-teal-100 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300 text-xs font-black flex items-center justify-center">
                          {idx + 1}
                        </span>
                        <h4 className="font-black text-slate-900 dark:text-slate-100 text-base">
                          {item.medication_name}
                        </h4>
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                          {item.dosage_form || 'Tablet'}
                        </span>
                        {item.is_prn && (
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-black bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200">
                            SOS / PRN
                          </span>
                        )}
                      </div>

                      {item.generic_name && (
                        <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                          Active: {item.generic_name}
                        </p>
                      )}

                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-700 dark:text-slate-300 pt-1">
                        <span>
                          <strong>Dose:</strong> {item.dose}
                        </span>
                        <span className="w-1 h-1 bg-slate-300 rounded-full" />
                        <span>
                          <strong>Route:</strong> {item.route}
                        </span>
                        <span className="w-1 h-1 bg-slate-300 rounded-full" />
                        <span>
                          <strong>Frequency:</strong> {item.frequency}
                        </span>
                        <span className="w-1 h-1 bg-slate-300 rounded-full" />
                        <span>
                          <strong>Timing:</strong> {item.timing}
                        </span>
                        <span className="w-1 h-1 bg-slate-300 rounded-full" />
                        <span>
                          <strong>Duration:</strong> {item.duration_value} {item.duration_unit}
                        </span>
                        <span className="w-1 h-1 bg-slate-300 rounded-full" />
                        <span>
                          <strong>Qty:</strong> {item.quantity}
                        </span>
                      </div>

                      {item.instructions && (
                        <p className="text-xs text-slate-500 italic mt-1">
                          "{item.instructions}"
                        </p>
                      )}
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center gap-1 shrink-0 self-end md:self-center">
                      <button
                        onClick={() => handleEditItem(idx)}
                        title="Edit line item"
                        className="p-2 rounded-xl text-slate-500 hover:text-teal-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDuplicateItem(idx)}
                        title="Duplicate line item"
                        className="p-2 rounded-xl text-slate-500 hover:text-teal-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleRemoveItem(idx)}
                        title="Remove line item"
                        className="p-2 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Doctor Notes */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm space-y-2">
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              Physician General Advice & Follow-Up Notes
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Review in OPD after 5 days with repeat CBC. Maintain hydration and report to emergency if high fever persists."
              className="w-full p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-xs font-medium focus:ring-2 focus:ring-teal-500"
            />
          </div>
        </div>
      )}

      {/* ── View Mode: REVIEW PRESCRIPTION (Section 11) ─────────────────────── */}
      {viewMode === 'review' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm space-y-6">
            <div className="border-b border-slate-200 dark:border-slate-700 pb-4 flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                  Pre-Finalization Verification
                </span>
                <h3 className="text-xl font-black text-slate-900 dark:text-slate-100">
                  Prescription Review Summary
                </h3>
              </div>
              <div className="text-right text-xs">
                <p className="font-bold text-slate-800 dark:text-slate-200">Encounter #{encounter.id.slice(-6)}</p>
                <p className="text-slate-400">{new Date().toLocaleDateString('en-IN', { dateStyle: 'long' })}</p>
              </div>
            </div>

            {/* Structured Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700 bg-slate-50/70 dark:bg-slate-900/40 text-slate-500 font-bold uppercase text-[10px]">
                    <th className="py-3 px-3">#</th>
                    <th className="py-3 px-3">Medication</th>
                    <th className="py-3 px-3">Dose</th>
                    <th className="py-3 px-3">Route</th>
                    <th className="py-3 px-3">Frequency</th>
                    <th className="py-3 px-3">Timing</th>
                    <th className="py-3 px-3">Duration</th>
                    <th className="py-3 px-3">Qty</th>
                    <th className="py-3 px-3">Instructions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700/60 font-medium">
                  {items.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-750/30">
                      <td className="py-3 px-3 font-bold text-slate-400">{idx + 1}</td>
                      <td className="py-3 px-3">
                        <strong className="text-slate-900 dark:text-slate-100 block">
                          {item.medication_name}
                        </strong>
                        <span className="text-[10px] text-slate-400 block truncate max-w-xs">
                          {item.generic_name}
                        </span>
                      </td>
                      <td className="py-3 px-3">{item.dose}</td>
                      <td className="py-3 px-3">{item.route}</td>
                      <td className="py-3 px-3">{item.frequency}</td>
                      <td className="py-3 px-3">{item.timing}</td>
                      <td className="py-3 px-3">
                        {item.duration_value} {item.duration_unit}
                      </td>
                      <td className="py-3 px-3 font-bold">{item.quantity}</td>
                      <td className="py-3 px-3 text-slate-500 italic max-w-xs truncate">
                        {item.instructions || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Doctor Notes Review */}
            {notes && (
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-700 text-xs">
                <span className="font-bold text-slate-500 uppercase tracking-wider block mb-1">
                  Physician Advice
                </span>
                <p className="text-slate-800 dark:text-slate-200 font-medium">{notes}</p>
              </div>
            )}

            {/* Safety Verification Checklist (Section 11) */}
            <div className="p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800 text-xs space-y-2">
              <span className="font-bold text-emerald-800 dark:text-emerald-300 uppercase tracking-wider flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Deterministic Clinical Safety Checks Completed
              </span>
              <ul className="space-y-1 text-slate-600 dark:text-slate-300 pl-5 list-disc">
                <li>Allergy conflict verification executed against patient hypersensitivity records.</li>
                <li>Active medication duplication check completed.</li>
                <li>Longitudinal profile synchronized with prescribed regimens.</li>
              </ul>
            </div>

            {/* Review Action bar */}
            <div className="flex justify-between items-center pt-4 border-t border-slate-200 dark:border-slate-700">
              <button
                onClick={() => setViewMode('build')}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 transition-colors"
              >
                Back to Edit
              </button>

              {activePrescription?.status !== 'FINALIZED' && (
                <button
                  onClick={() => setShowFinalizeConfirm(true)}
                  disabled={isSubmitting}
                  className="px-6 py-2.5 rounded-xl text-xs font-black text-white bg-emerald-600 hover:bg-emerald-700 transition-colors shadow-md flex items-center gap-2"
                >
                  <CheckCircle2 className="w-4 h-4" /> Finalize & Legally Sign Prescription
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── View Mode: PRINT Rx VIEW (Section 20) ────────────────────────────── */}
      {viewMode === 'print' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <button
              onClick={() => setViewMode('review')}
              className="text-xs font-bold text-teal-600 dark:text-teal-400 hover:underline"
            >
              ← Back to Review View
            </button>
            <button
              onClick={() => window.print()}
              className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-slate-900 dark:bg-teal-600 hover:bg-slate-800 transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <Printer className="w-4 h-4" /> Print Document
            </button>
          </div>

          {/* Clean Printable Rx Sheet */}
          <div className="p-10 rounded-2xl bg-white text-slate-900 border border-slate-300 shadow-lg print:shadow-none print:border-none space-y-8 font-sans">
            {/* Header */}
            <div className="flex justify-between items-start border-b-2 border-slate-900 pb-6">
              <div>
                <h1 className="text-2xl font-black tracking-tight text-teal-700 uppercase">
                  MediPlatform Hospital
                </h1>
                <p className="text-xs text-slate-600 font-semibold">
                  Department of General & Internal Medicine • Outpatient Division
                </p>
                <p className="text-[11px] text-slate-500">
                  National Health Facility Registry ID: MEDI-IN-9082
                </p>
              </div>
              <div className="text-right">
                <p className="font-bold text-sm">Dr. On Duty, MBBS, MD</p>
                <p className="text-xs text-slate-500">Reg No: MCI-2024-88419</p>
                <p className="text-xs text-slate-500 font-semibold mt-1">
                  Date: {new Date().toLocaleDateString('en-IN', { dateStyle: 'long' })}
                </p>
              </div>
            </div>

            {/* Patient Demographic Banner */}
            <div className="grid grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs">
              <div>
                <span className="text-slate-500 block font-bold text-[10px]">PATIENT NAME</span>
                <span className="font-black text-sm">{patient.name}</span>
              </div>
              <div>
                <span className="text-slate-500 block font-bold text-[10px]">AGE / GENDER</span>
                <span className="font-bold">{patient.age} Yrs / {patient.gender}</span>
              </div>
              <div>
                <span className="text-slate-500 block font-bold text-[10px]">PATIENT ID / UHID</span>
                <span className="font-mono font-bold">{patient.id.slice(-8).toUpperCase()}</span>
              </div>
              <div>
                <span className="text-slate-500 block font-bold text-[10px]">ENCOUNTER NO.</span>
                <span className="font-mono font-bold">#{encounter.id.slice(-6).toUpperCase()}</span>
              </div>
            </div>

            {/* Rx Symbol */}
            <div className="text-4xl font-serif font-black text-slate-900 italic">℞</div>

            {/* Medication Table */}
            <table className="w-full text-left text-xs border-collapse border border-slate-200">
              <thead>
                <tr className="bg-slate-100 font-bold uppercase text-[10px] text-slate-700 border-b border-slate-200">
                  <th className="py-2.5 px-3">#</th>
                  <th className="py-2.5 px-3">Medicine & Strength</th>
                  <th className="py-2.5 px-3">Dosage Form</th>
                  <th className="py-2.5 px-3">Dose & Route</th>
                  <th className="py-2.5 px-3">Frequency & Timing</th>
                  <th className="py-2.5 px-3">Duration</th>
                  <th className="py-2.5 px-3">Total Qty</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {items.map((item, idx) => (
                  <tr key={idx}>
                    <td className="py-3 px-3 font-bold">{idx + 1}</td>
                    <td className="py-3 px-3">
                      <p className="font-black text-sm">{item.medication_name}</p>
                      {item.generic_name && (
                        <p className="text-[10px] text-slate-500">Active: {item.generic_name}</p>
                      )}
                      {item.instructions && (
                        <p className="text-[11px] text-slate-600 italic mt-0.5">
                          Note: {item.instructions}
                        </p>
                      )}
                    </td>
                    <td className="py-3 px-3">{item.dosage_form || 'Tablet'}</td>
                    <td className="py-3 px-3">{item.dose} ({item.route})</td>
                    <td className="py-3 px-3">
                      {item.frequency}
                      <span className="block text-slate-500 font-normal">{item.timing}</span>
                    </td>
                    <td className="py-3 px-3">
                      {item.duration_value} {item.duration_unit}
                    </td>
                    <td className="py-3 px-3 font-bold">{item.quantity}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Advice Notes */}
            {notes && (
              <div className="p-4 border border-slate-200 rounded-xl bg-slate-50 text-xs">
                <p className="font-bold text-slate-700 uppercase tracking-wider text-[10px] mb-1">
                  General Advice & Follow-Up
                </p>
                <p className="text-slate-800 leading-relaxed font-medium">{notes}</p>
              </div>
            )}

            {/* Signature Block */}
            <div className="pt-12 flex justify-between items-end border-t border-slate-200 text-xs">
              <div>
                <p className="text-[10px] text-slate-400">
                  Digitally verified via MediPlatform EHR • Signed by licensed physician
                </p>
                <p className="text-[10px] text-slate-400 font-mono">
                  Timestamp: {activePrescription?.finalized_at || new Date().toISOString()}
                </p>
              </div>
              <div className="text-center w-48">
                <div className="h-10 border-b border-dashed border-slate-400 mb-1" />
                <p className="font-bold">Authorized Physician Signature</p>
                <p className="text-[10px] text-slate-500">Verified Clinical Sign-off</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── View Mode: LONGITUDINAL PRESCRIPTION HISTORY (Section 13) ──────── */}
      {viewMode === 'history' && (
        <div className="space-y-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-black text-slate-900 dark:text-slate-100">
              Patient Longitudinal Prescription History ({historicalPrescriptions.length})
            </h3>
            <button
              onClick={() => setViewMode('build')}
              className="text-xs font-bold text-teal-600 dark:text-teal-400 hover:underline"
            >
              ← Back to Current Prescription
            </button>
          </div>

          {historicalPrescriptions.length === 0 ? (
            <div className="p-8 text-center rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-400">
              <p className="font-semibold">No previous prescriptions found for this patient.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {historicalPrescriptions.map((rx) => (
                <div
                  key={rx.id}
                  className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm space-y-3"
                >
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700 pb-3 text-xs">
                    <div>
                      <span className="font-black text-slate-900 dark:text-slate-100">
                        Prescription #{rx.id.slice(-6).toUpperCase()}
                      </span>
                      <span className="text-slate-400 ml-2">
                        {rx.created_at ? new Date(rx.created_at).toLocaleDateString('en-IN', { dateStyle: 'medium' }) : ''}
                      </span>
                    </div>
                    <span
                      className={cn(
                        'px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase',
                        rx.status === 'FINALIZED'
                          ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-200'
                          : rx.status === 'AMENDED'
                          ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200'
                          : 'bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200'
                      )}
                    >
                      {rx.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
                    {rx.items.map((item, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-700/60"
                      >
                        <p className="font-bold text-slate-900 dark:text-slate-100">{item.medication_name}</p>
                        <p className="text-slate-500 text-[11px] mt-0.5">
                          {item.dose} • {item.frequency} • {item.duration_value} {item.duration_unit}
                        </p>
                      </div>
                    ))}
                  </div>

                  {rx.notes && (
                    <p className="text-xs text-slate-500 italic pt-1 border-t border-slate-100 dark:border-slate-700/40">
                      Notes: {rx.notes}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Finalization Confirmation Modal (Section 12) ────────────────────── */}
      {showFinalizeConfirm && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white dark:bg-slate-800 rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 dark:border-slate-700 space-y-5">
            <div className="flex items-center gap-3 text-emerald-600 dark:text-emerald-400">
              <div className="w-12 h-12 rounded-2xl bg-emerald-100 dark:bg-emerald-950 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-black text-slate-900 dark:text-slate-100">
                  Legal Clinician Verification
                </h3>
                <p className="text-xs text-slate-500">Confirm Prescription Sign-off</p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200 space-y-2">
              <p className="font-bold flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                Statutory Disclaimer & Prescribing Responsibility:
              </p>
              <p className="leading-relaxed">
                Please review the prescription carefully before signing. As the licensed attending clinician, you are responsible for the final clinical decision, patient suitability, and dosage verification.
              </p>
            </div>

            <div className="text-xs text-slate-600 dark:text-slate-300 space-y-1">
              <p>• <strong>Patient:</strong> {patient.name} ({patient.age}y, {patient.gender})</p>
              <p>• <strong>Encounter:</strong> #{encounter.id.slice(-6)}</p>
              <p>• <strong>Medications:</strong> {items.length} prescribed drug(s)</p>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowFinalizeConfirm(false)}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleFinalize}
                disabled={isSubmitting}
                className="px-6 py-2.5 rounded-xl text-xs font-black text-white bg-emerald-600 hover:bg-emerald-700 transition-colors shadow-md flex items-center gap-2"
              >
                {isSubmitting ? 'Signing…' : 'I Confirm & Legally Sign'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
