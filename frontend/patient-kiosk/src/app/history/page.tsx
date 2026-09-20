"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { 
  getPatientMedicalHistory, 
  reportMedicalChange, 
  MedicalHistoryResponse, 
  PendingReportItem 
} from "@/lib/api/profile";
import { 
  HeartPulse, 
  AlertTriangle, 
  Pill, 
  Scissors, 
  Users, 
  Coffee, 
  FileText, 
  Clock, 
  ShieldCheck, 
  Loader2, 
  ArrowLeft, 
  MessageSquarePlus, 
  CheckCircle2, 
  X,
  AlertCircle,
  ChevronRight
} from "lucide-react";

export default function MedicalHistoryPage() {
  const router = useRouter();
  const { session } = useKiosk();

  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<MedicalHistoryResponse | null>(null);
  const [error, setError] = useState("");

  // Report Change Modal
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reportCategory, setReportCategory] = useState<"allergy" | "condition" | "medication" | "procedure" | "general">("condition");
  const [reportDescription, setReportDescription] = useState("");
  const [reportLoading, setReportLoading] = useState(false);
  const [reportSuccessMsg, setReportSuccessMsg] = useState("");

  const loadHistory = async () => {
    if (!session?.sessionId) {
      router.replace("/");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await getPatientMedicalHistory(session.sessionId);
      setHistory(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load medical history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [session, router]);

  const handleReportChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.sessionId || !reportDescription.trim()) return;

    setReportLoading(true);
    try {
      const res = await reportMedicalChange(session.sessionId, {
        category: reportCategory,
        description: reportDescription.trim(),
      });
      setReportSuccessMsg(res.message);
      setReportDescription("");
      await loadHistory();
      setTimeout(() => {
        setIsReportModalOpen(false);
        setReportSuccessMsg("");
      }, 2000);
    } catch (err: any) {
      alert(err.message || "Failed to submit report.");
    } finally {
      setReportLoading(false);
    }
  };

  if (!session) return null;

  const conditions = history?.medical_history?.chronic_conditions || [];
  const allergies = history?.allergies?.known || [];
  const medications = history?.current_medications || [];
  const surgeries = history?.medical_history?.surgeries || [];
  const hospitalizations = history?.medical_history?.hospitalizations || [];
  const familyHistory = history?.family_history || {};
  const socialHistory = history?.social_history || {};
  const prescriptions = history?.prescriptions || [];
  const pendingReports = history?.pending_reports || [];

  return (
    <div className="min-h-screen flex flex-col bg-slate-50/60 pb-20">
      <AppHeader 
        title="Complete Medical History" 
        subtitle="Longitudinal clinical record and verified diagnoses"
        patientName={history?.patient_name}
        showNav={true}
      />

      <main className="flex-1 max-w-5xl mx-auto w-full p-4 sm:p-6 md:p-8 space-y-6">

        {/* Top Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <button
            onClick={() => router.push("/profile")}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900 text-sm font-semibold px-3 py-2 rounded-xl bg-white border border-slate-200 shadow-2xs hover:bg-slate-50 transition cursor-pointer"
          >
            <ArrowLeft size={16} />
            <span>Back to Profile</span>
          </button>

          <button
            onClick={() => setIsReportModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200/80 rounded-xl text-xs sm:text-sm font-bold shadow-2xs transition cursor-pointer"
          >
            <MessageSquarePlus size={15} className="text-amber-600" />
            <span>Report a Discrepancy</span>
          </button>
        </div>

        {loading ? (
          <div className="bg-white rounded-3xl p-16 border border-slate-200 flex flex-col items-center justify-center space-y-4 shadow-xs">
            <Loader2 className="w-10 h-10 text-blue-600 animate-spin" />
            <p className="text-slate-500 font-semibold text-sm">Loading longitudinal clinical history...</p>
          </div>
        ) : error ? (
          <div className="bg-rose-50 border border-rose-200 rounded-3xl p-8 text-center space-y-3">
            <AlertCircle className="w-8 h-8 text-rose-600 mx-auto" />
            <h3 className="text-lg font-bold text-rose-900">Unable to load medical history</h3>
            <p className="text-sm text-rose-700">{error}</p>
            <button
              onClick={loadHistory}
              className="px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-bold shadow-xs hover:bg-rose-700"
            >
              Try Again
            </button>
          </div>
        ) : (
          <div className="space-y-6">

            {/* Pending Doctor Review Banner (if any) */}
            {pendingReports.length > 0 && (
              <div className="p-5 bg-amber-50/80 border border-amber-200 rounded-3xl shadow-xs space-y-3">
                <div className="flex items-center gap-2 text-amber-900 font-extrabold text-sm">
                  <Clock className="w-4 h-4 text-amber-600" />
                  <span>Pending Doctor Review ({pendingReports.length})</span>
                </div>
                <p className="text-xs text-amber-800 opacity-90">
                  You submitted the following discrepancies. They are recorded in the safety audit store and will be reviewed by your physician.
                </p>
                <div className="space-y-2">
                  {pendingReports.map((report) => (
                    <div
                      key={report.id}
                      className="p-3 bg-white/90 rounded-2xl border border-amber-200 text-xs flex items-center justify-between"
                    >
                      <div>
                        <span className="font-bold text-slate-800 uppercase text-[10px] tracking-wider px-2 py-0.5 rounded-full bg-amber-100 text-amber-900 mr-2">
                          {report.category}
                        </span>
                        <span className="text-slate-700 font-medium">{report.description}</span>
                      </div>
                      <span className="text-[10px] text-amber-700 font-bold bg-amber-50 px-2 py-1 rounded-md border border-amber-200 shrink-0">
                        Pending Verification
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* SECTION 1: Chronic Conditions */}
            <div className="bg-white rounded-3xl p-6 sm:p-7 border border-slate-200/90 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <HeartPulse className="w-5 h-5 text-blue-600" />
                  <h3 className="font-extrabold text-slate-900 text-base">Diagnoses & Chronic Conditions</h3>
                </div>
                <span className="text-xs font-mono text-slate-400 font-bold">
                  {conditions.length} recorded
                </span>
              </div>

              {conditions.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {conditions.map((cond, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-2xl bg-slate-50/70 border border-slate-200 flex flex-col justify-between gap-2"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className="font-extrabold text-slate-900 text-sm">
                          {cond.condition}
                        </span>
                        {cond.icd10 && (
                          <span className="text-[10px] font-mono font-bold bg-white text-slate-700 px-2 py-0.5 rounded border border-slate-200 shrink-0">
                            {cond.icd10}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center justify-between text-xs text-slate-500 pt-1 border-t border-slate-100">
                        <span>Since: <strong>{cond.since || "Unknown"}</strong></span>
                        <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold uppercase border border-emerald-200">
                          {cond.status || "Active"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-2xl bg-slate-50 text-xs text-slate-500 italic">
                  No information recorded.
                </div>
              )}
            </div>

            {/* SECTION 2: Allergies & Drug Sensitivities */}
            <div className="bg-white rounded-3xl p-6 sm:p-7 border border-slate-200/90 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-500" />
                  <h3 className="font-extrabold text-slate-900 text-base">Allergies & Adverse Drug Reactions</h3>
                </div>
                <span className="text-xs font-mono text-slate-400 font-bold">
                  {allergies.length} recorded
                </span>
              </div>

              {allergies.length > 0 ? (
                <div className="space-y-3">
                  {allergies.map((alg, idx) => {
                    const isSevere = alg.severity?.toLowerCase().includes("severe") || alg.severity?.toLowerCase().includes("life");
                    return (
                      <div
                        key={idx}
                        className={`p-4 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                          isSevere 
                            ? "bg-rose-50/70 border-rose-200" 
                            : "bg-amber-50/60 border-amber-200"
                        }`}
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-black text-base text-slate-900">{alg.substance}</span>
                            {isSevere && (
                              <span className="text-[10px] font-bold bg-rose-600 text-white px-2 py-0.5 rounded-full uppercase tracking-wider">
                                Severe Risk
                              </span>
                            )}
                          </div>
                          {alg.reaction && (
                            <p className="text-xs text-slate-700">
                              Reaction: <strong className="font-semibold">{alg.reaction}</strong>
                            </p>
                          )}
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-lg bg-white/80 border border-slate-200">
                            {alg.severity || "Recorded"}
                          </span>
                          {alg.confirmed && (
                            <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-lg">
                              <CheckCircle2 size={12} /> Confirmed
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="p-4 rounded-2xl bg-slate-50 text-xs text-slate-500 italic">
                  No information recorded (Unknown ≠ Negative).
                </div>
              )}
            </div>

            {/* SECTION 3: Current Medications */}
            <div className="bg-white rounded-3xl p-6 sm:p-7 border border-slate-200/90 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <Pill className="w-5 h-5 text-teal-600" />
                  <h3 className="font-extrabold text-slate-900 text-base">Current Active Medications</h3>
                </div>
                <span className="text-xs font-mono text-slate-400 font-bold">
                  {medications.length} active
                </span>
              </div>

              {medications.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {medications.map((med, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-2xl bg-teal-50/30 border border-teal-200/60 flex items-start gap-3.5"
                    >
                      <div className="w-9 h-9 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center shrink-0 mt-0.5">
                        <Pill size={18} />
                      </div>
                      <div className="min-w-0 space-y-0.5">
                        <p className="font-black text-slate-900 text-sm">{med.name}</p>
                        <p className="text-xs font-bold text-teal-900">{med.dose}</p>
                        {med.frequency && (
                          <p className="text-[11px] text-slate-500">Frequency: {med.frequency}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-2xl bg-slate-50 text-xs text-slate-500 italic">
                  No information recorded.
                </div>
              )}
            </div>

            {/* SECTION 4: Surgeries & Hospitalizations */}
            <div className="bg-white rounded-3xl p-6 sm:p-7 border border-slate-200/90 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <Scissors className="w-5 h-5 text-slate-700" />
                  <h3 className="font-extrabold text-slate-900 text-base">Surgeries & Past Hospitalizations</h3>
                </div>
              </div>

              {surgeries.length > 0 || hospitalizations.length > 0 ? (
                <div className="space-y-3">
                  {surgeries.map((surg, idx) => (
                    <div key={`s-${idx}`} className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 flex justify-between items-center text-xs">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900 text-sm">{surg.procedure}</span>
                          <span className="text-[10px] font-bold uppercase bg-slate-200/60 text-slate-700 px-1.5 py-0.5 rounded">
                            Surgery
                          </span>
                        </div>
                        {surg.indication && <p className="text-slate-500 mt-0.5">{surg.indication}</p>}
                      </div>
                      {surg.year && <span className="font-mono text-slate-500 font-bold">{surg.year}</span>}
                    </div>
                  ))}

                  {hospitalizations.map((hosp, idx) => (
                    <div key={`h-${idx}`} className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 flex justify-between items-center text-xs">
                      <div>
                        <span className="font-bold text-slate-900 text-sm">{hosp.reason}</span>
                        <span className="text-[10px] font-bold uppercase bg-slate-200/60 text-slate-700 px-1.5 py-0.5 rounded ml-2">
                          Hospitalization
                        </span>
                      </div>
                      {hosp.year && <span className="font-mono text-slate-500 font-bold">{hosp.year}</span>}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-2xl bg-slate-50 text-xs text-slate-500 italic">
                  No information recorded.
                </div>
              )}
            </div>

            {/* SECTION 5: Family & Social History */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

              {/* Family History */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-xs space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                  <Users className="w-4 h-4 text-purple-600" />
                  <h4 className="font-extrabold text-slate-900 text-sm">Family Medical History</h4>
                </div>

                {Object.keys(familyHistory).length > 0 ? (
                  <div className="space-y-2 text-xs">
                    {Object.entries(familyHistory).map(([relation, condition], idx) => (
                      <div key={idx} className="flex justify-between py-1 border-b border-slate-50">
                        <span className="text-slate-500 capitalize">{relation.replace("_", " ")}:</span>
                        <span className="font-bold text-slate-800">{String(condition)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No information recorded.</p>
                )}
              </div>

              {/* Social / Lifestyle History */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-xs space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                  <Coffee className="w-4 h-4 text-amber-600" />
                  <h4 className="font-extrabold text-slate-900 text-sm">Lifestyle & Social Background</h4>
                </div>

                {Object.keys(socialHistory).length > 0 ? (
                  <div className="space-y-2 text-xs">
                    {Object.entries(socialHistory).map(([key, val], idx) => (
                      <div key={idx} className="flex justify-between py-1 border-b border-slate-50">
                        <span className="text-slate-500 capitalize">{key.replace("_", " ")}:</span>
                        <span className="font-bold text-slate-800">{String(val)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No information recorded.</p>
                )}
              </div>

            </div>

            {/* SECTION 6: Past Prescriptions */}
            <div className="bg-white rounded-3xl p-6 sm:p-7 border border-slate-200/90 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-indigo-600" />
                  <h3 className="font-extrabold text-slate-900 text-base">Prescriptions on Record</h3>
                </div>
                <span className="text-xs font-mono text-slate-400 font-bold">
                  {prescriptions.length} issued
                </span>
              </div>

              {prescriptions.length > 0 ? (
                <div className="space-y-3">
                  {prescriptions.map((rx) => (
                    <div key={rx.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-slate-800">
                          {rx.notes || "Prescription Order"}
                        </span>
                        <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 text-[10px] font-bold">
                          {rx.status}
                        </span>
                      </div>
                      {rx.created_at && (
                        <p className="text-[11px] text-slate-400">
                          Issued: {new Date(rx.created_at).toLocaleDateString()}
                        </p>
                      )}
                      <div className="pt-2 border-t border-slate-200/60 space-y-1">
                        {rx.items.map((it, idx) => (
                          <div key={idx} className="text-xs flex items-center justify-between text-slate-700">
                            <span className="font-semibold">• {it.medication_name} ({it.dose})</span>
                            <span className="text-slate-500 font-mono text-[11px]">{it.frequency}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-2xl bg-slate-50 text-xs text-slate-500 italic">
                  No information recorded.
                </div>
              )}
            </div>

          </div>
        )}

      </main>

      {/* MODAL: Report Discrepancy */}
      {isReportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-lg w-full shadow-2xl border border-slate-200 space-y-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <MessageSquarePlus className="w-5 h-5 text-amber-600" />
                <h3 className="text-lg font-black text-slate-900">Report Clinical Discrepancy</h3>
              </div>
              <button
                onClick={() => setIsReportModalOpen(false)}
                className="p-1 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 cursor-pointer"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-3.5 bg-blue-50 border border-blue-200 rounded-2xl text-xs text-blue-900 space-y-1">
              <div className="flex items-center gap-1.5 font-bold">
                <ShieldCheck size={14} className="text-blue-600" />
                <span>Deterministic Verification Guard</span>
              </div>
              <p className="opacity-90 leading-relaxed text-[11px]">
                Your report will be recorded with immutable provenance and highlighted for your doctor to verify during your visit.
              </p>
            </div>

            {reportSuccessMsg ? (
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-xs text-emerald-800 space-y-1 font-bold">
                <p className="flex items-center gap-2 text-sm">
                  <CheckCircle2 size={18} />
                  <span>Report Submitted!</span>
                </p>
                <p className="font-normal opacity-90 text-[11px]">{reportSuccessMsg}</p>
              </div>
            ) : (
              <form onSubmit={handleReportChange} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-700 uppercase">Category</label>
                  <select
                    value={reportCategory}
                    onChange={(e: any) => setReportCategory(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-slate-300 text-sm font-semibold bg-white focus:border-blue-600 focus:outline-hidden"
                  >
                    <option value="condition">Medical Condition / Diagnosis</option>
                    <option value="allergy">Allergy / Drug Reaction</option>
                    <option value="medication">Current Medication</option>
                    <option value="procedure">Surgery or Procedure</option>
                    <option value="general">Other Information</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-700 uppercase">Description</label>
                  <textarea
                    rows={4}
                    value={reportDescription}
                    onChange={(e) => setReportDescription(e.target.value)}
                    className="w-full p-4 rounded-xl border border-slate-300 text-sm focus:border-blue-600 focus:outline-hidden placeholder:text-slate-400"
                    placeholder="Provide details about the change or discrepancy..."
                    required
                  />
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsReportModalOpen(false)}
                    className="flex-1 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold text-sm cursor-pointer"
                    disabled={reportLoading}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 py-3 bg-amber-600 hover:bg-amber-700 text-white rounded-xl font-bold text-sm shadow-md shadow-amber-600/20 cursor-pointer flex items-center justify-center gap-2"
                    disabled={reportLoading || !reportDescription.trim()}
                  >
                    {reportLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Submit Report"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
