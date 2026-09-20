"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { 
  getPatientProfile, 
  updatePatientProfile, 
  reportMedicalChange, 
  PatientProfileResponse, 
  ProfileUpdatePayload 
} from "@/lib/api/profile";
import { 
  User, 
  Phone, 
  Mail, 
  MapPin, 
  Heart, 
  AlertTriangle, 
  Pill, 
  Scissors, 
  Calendar, 
  FileText, 
  Edit3, 
  MessageSquarePlus, 
  ArrowLeft, 
  ShieldCheck, 
  Loader2, 
  CheckCircle2, 
  X, 
  Clock,
  Sparkles,
  ChevronRight,
  Activity
} from "lucide-react";

export default function PatientProfilePage() {
  const router = useRouter();
  const { session } = useKiosk();

  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<PatientProfileResponse | null>(null);
  const [error, setError] = useState("");

  // Edit Demographics Modal State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [editPhone, setEditPhone] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editAddress, setEditAddress] = useState("");
  const [editEmergencyName, setEditEmergencyName] = useState("");
  const [editEmergencyPhone, setEditEmergencyPhone] = useState("");
  const [editSuccessMsg, setEditSuccessMsg] = useState("");

  // Report Change Modal State
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reportCategory, setReportCategory] = useState<"allergy" | "condition" | "medication" | "procedure" | "general">("allergy");
  const [reportDescription, setReportDescription] = useState("");
  const [reportLoading, setReportLoading] = useState(false);
  const [reportSuccessMsg, setReportSuccessMsg] = useState("");

  const loadProfile = async () => {
    if (!session?.sessionId) {
      router.replace("/");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await getPatientProfile(session.sessionId);
      setProfile(data);
      // Initialize edit fields
      setEditPhone(data.demographics.phone || "");
      setEditEmail(data.demographics.email || "");
      setEditAddress(data.demographics.address || "");
      setEditEmergencyName(data.demographics.emergency_contact?.name || "");
      setEditEmergencyPhone(data.demographics.emergency_contact?.phone || "");
    } catch (err: any) {
      setError(err?.message || "Failed to load patient profile.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, [session, router]);

  const handleUpdateDemographics = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.sessionId) return;

    setEditLoading(true);
    try {
      const payload: ProfileUpdatePayload = {
        phone: editPhone.trim(),
        email: editEmail.trim(),
        address: editAddress.trim(),
        emergency_contact: {
          name: editEmergencyName.trim(),
          phone: editEmergencyPhone.trim(),
          relation: profile?.demographics.emergency_contact?.relation || "Family",
        },
      };
      const res = await updatePatientProfile(session.sessionId, payload);
      setEditSuccessMsg(res.message);
      await loadProfile();
      setTimeout(() => {
        setIsEditModalOpen(false);
        setEditSuccessMsg("");
      }, 1200);
    } catch (err: any) {
      alert(err.message || "Failed to update profile details.");
    } finally {
      setEditLoading(false);
    }
  };

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

  const demo = profile?.demographics;
  const summary = profile?.profile_summary;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50/60 pb-16">
      <AppHeader 
        title="Patient Profile" 
        subtitle="Review and manage your personal health record"
        patientName={demo?.name}
        showNav={true}
      />

      <main className="flex-1 max-w-5xl mx-auto w-full p-4 sm:p-6 md:p-8 space-y-6">
        {/* Navigation Breadcrumb / Back Button */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => router.push("/session")}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900 text-sm font-semibold px-3 py-2 rounded-xl bg-white border border-slate-200 shadow-2xs hover:bg-slate-50 transition cursor-pointer"
          >
            <ArrowLeft size={16} />
            <span>Back to Home</span>
          </button>

          <button
            onClick={() => router.push("/history")}
            className="flex items-center gap-1.5 text-xs font-bold text-blue-700 bg-blue-50 hover:bg-blue-100 px-3.5 py-2 rounded-xl border border-blue-200 transition cursor-pointer"
          >
            <span>Full Medical History</span>
            <ChevronRight size={14} />
          </button>
        </div>

        {loading ? (
          <div className="bg-white rounded-3xl p-16 border border-slate-200 flex flex-col items-center justify-center space-y-4 shadow-xs">
            <Loader2 className="w-10 h-10 text-blue-600 animate-spin" />
            <p className="text-slate-500 font-semibold text-sm">Loading verified patient profile...</p>
          </div>
        ) : error ? (
          <div className="bg-rose-50 border border-rose-200 rounded-3xl p-8 text-center space-y-3">
            <AlertTriangle className="w-8 h-8 text-rose-600 mx-auto" />
            <h3 className="text-lg font-bold text-rose-900">Unable to load profile</h3>
            <p className="text-sm text-rose-700">{error}</p>
            <button
              onClick={loadProfile}
              className="px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-bold shadow-xs hover:bg-rose-700"
            >
              Try Again
            </button>
          </div>
        ) : demo ? (
          <>
            {/* Header Identity Card */}
            <div className="bg-white rounded-3xl p-6 md:p-8 border border-slate-200/90 shadow-xs relative overflow-hidden">
              <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-blue-500/10 via-teal-500/5 to-transparent rounded-full blur-3xl -z-0 pointer-events-none" />

              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
                <div className="flex items-start gap-4 sm:gap-5">
                  <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white flex items-center justify-center font-black text-2xl sm:text-3xl shadow-md shadow-blue-500/20 shrink-0">
                    {demo.name.charAt(0)}
                  </div>
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                        {demo.name}
                      </h2>
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800 uppercase tracking-wide">
                        Verified Patient
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs sm:text-sm text-slate-600">
                      {demo.gender && <span>{demo.gender}</span>}
                      {demo.age && <span>• {demo.age} years</span>}
                      {demo.blood_group && (
                        <span>
                          • Blood Group: <strong className="text-rose-600 font-bold">{demo.blood_group}</strong>
                        </span>
                      )}
                      {demo.dob && <span>• DOB: {demo.dob}</span>}
                    </div>

                    <div className="flex items-center gap-1.5 text-xs text-slate-400 pt-1">
                      <ShieldCheck size={14} className="text-emerald-600" />
                      <span>Single source of truth synced with Hospital PostgreSQL</span>
                    </div>
                  </div>
                </div>

                {/* Primary Action Buttons */}
                <div className="flex flex-wrap items-center gap-2.5 shrink-0">
                  <button
                    onClick={() => setIsEditModalOpen(true)}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs sm:text-sm font-bold shadow-xs hover:shadow transition cursor-pointer active:scale-95"
                  >
                    <Edit3 size={15} />
                    <span>Update Details</span>
                  </button>

                  <button
                    onClick={() => setIsReportModalOpen(true)}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200/80 text-xs sm:text-sm font-bold shadow-2xs transition cursor-pointer active:scale-95"
                  >
                    <MessageSquarePlus size={15} className="text-amber-600" />
                    <span>Report Medical Change</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Grid: Left Column (Demographics & Emergency) + Right Column (Clinical Highlights) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

              {/* Left Column: Personal & Contact Details */}
              <div className="space-y-6">

                {/* Contact Card */}
                <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-xs space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-blue-600" />
                      <h3 className="font-extrabold text-slate-900 text-sm">Contact Information</h3>
                    </div>
                    <button
                      onClick={() => setIsEditModalOpen(true)}
                      className="text-xs font-bold text-blue-600 hover:text-blue-800"
                    >
                      Edit
                    </button>
                  </div>

                  <div className="space-y-3.5 text-xs sm:text-sm">
                    <div className="flex items-start gap-3">
                      <Phone className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-[11px] text-slate-400 font-semibold uppercase">Mobile Number</p>
                        <p className="font-bold text-slate-800 font-mono">{demo.phone || "No phone recorded"}</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <Mail className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-[11px] text-slate-400 font-semibold uppercase">Email Address</p>
                        <p className="font-medium text-slate-800 break-all">{demo.email || "No email recorded"}</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <MapPin className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-[11px] text-slate-400 font-semibold uppercase">Residential Address</p>
                        <p className="font-medium text-slate-700 leading-relaxed">{demo.address || "No address recorded"}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Emergency Contact Card */}
                <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-xs space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <Heart className="w-4 h-4 text-rose-500" />
                      <h3 className="font-extrabold text-slate-900 text-sm">Emergency Contact</h3>
                    </div>
                    <span className="text-[10px] font-bold uppercase bg-rose-50 text-rose-700 px-2 py-0.5 rounded-full">
                      Important
                    </span>
                  </div>

                  {demo.emergency_contact?.name || demo.emergency_contact?.phone ? (
                    <div className="p-3.5 bg-rose-50/50 rounded-2xl border border-rose-100 space-y-1 text-xs sm:text-sm">
                      <p className="font-bold text-slate-900">{demo.emergency_contact.name}</p>
                      <p className="text-slate-600 flex items-center gap-1.5 font-mono">
                        <Phone size={13} className="text-rose-600" />
                        <span>{demo.emergency_contact.phone || "No phone"}</span>
                      </p>
                      {demo.emergency_contact.relation && (
                        <p className="text-[11px] text-slate-400">Relation: {demo.emergency_contact.relation}</p>
                      )}
                    </div>
                  ) : (
                    <div className="p-3 bg-slate-50 rounded-2xl text-xs text-slate-500 text-center">
                      No emergency contact recorded.
                      <button
                        onClick={() => setIsEditModalOpen(true)}
                        className="block mx-auto mt-1.5 font-bold text-blue-600 hover:underline"
                      >
                        + Add Emergency Contact
                      </button>
                    </div>
                  )}
                </div>

                {/* Preferences */}
                <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-xs space-y-2.5 text-xs">
                  <h4 className="font-bold text-slate-400 uppercase tracking-wider text-[11px]">Kiosk Preferences</h4>
                  <div className="flex justify-between py-1.5 border-b border-slate-100">
                    <span className="text-slate-500">Language:</span>
                    <span className="font-bold text-slate-800">{demo.preferred_language || "English"}</span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-slate-500">Intake Mode:</span>
                    <span className="font-bold text-slate-800">{demo.communication_mode || "Voice / Touch"}</span>
                  </div>
                </div>

              </div>

              {/* Right 2 Columns: Medical Profile Summary & Recent Visits */}
              <div className="lg:col-span-2 space-y-6">

                {/* Clinical Highlights Card */}
                <div className="bg-white rounded-3xl p-6 md:p-7 border border-slate-200/90 shadow-xs space-y-6">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <Activity className="w-5 h-5 text-blue-600" />
                      <h3 className="font-extrabold text-slate-900 text-base">Medical Profile Summary</h3>
                    </div>
                    <button
                      onClick={() => router.push("/history")}
                      className="text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1"
                    >
                      <span>View Full Breakdown</span>
                      <ChevronRight size={14} />
                    </button>
                  </div>

                  {/* 1. Chronic Conditions */}
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-700 uppercase tracking-wide flex items-center gap-1.5">
                        <Heart size={14} className="text-blue-600" />
                        Known Chronic Diagnoses
                      </span>
                      <span className="text-slate-400 text-[11px] font-mono">
                        {summary?.chronic_conditions?.length || 0} recorded
                      </span>
                    </div>

                    {summary?.chronic_conditions && summary.chronic_conditions.length > 0 ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {summary.chronic_conditions.map((cond, idx) => (
                          <div
                            key={idx}
                            className="p-3 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col justify-between"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <span className="font-bold text-slate-900 text-xs sm:text-sm leading-tight">
                                {cond.condition}
                              </span>
                              {cond.icd10 && (
                                <span className="text-[10px] font-mono font-bold bg-white text-slate-600 px-1.5 py-0.5 rounded border border-slate-200 shrink-0">
                                  {cond.icd10}
                                </span>
                              )}
                            </div>
                            {cond.since && (
                              <p className="text-[11px] text-slate-500 mt-1">Diagnosed: {cond.since}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400 italic bg-slate-50 p-3 rounded-xl">No chronic conditions recorded.</p>
                    )}
                  </div>

                  {/* 2. Allergies (CRITICAL HIGHLIGHT) */}
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-700 uppercase tracking-wide flex items-center gap-1.5">
                        <AlertTriangle size={14} className="text-amber-500" />
                        Allergies & Sensitivities
                      </span>
                      <span className="text-slate-400 text-[11px] font-mono">
                        {summary?.allergies?.length || 0} recorded
                      </span>
                    </div>

                    {summary?.allergies && summary.allergies.length > 0 ? (
                      <div className="space-y-2">
                        {summary.allergies.map((alg, idx) => {
                          const isSevere = alg.severity?.toLowerCase().includes("severe") || alg.severity?.toLowerCase().includes("life");
                          return (
                            <div
                              key={idx}
                              className={`p-3.5 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${
                                isSevere 
                                  ? "bg-rose-50/70 border-rose-200 text-rose-950" 
                                  : "bg-amber-50/60 border-amber-200 text-amber-950"
                              }`}
                            >
                              <div className="space-y-0.5">
                                <div className="flex items-center gap-2">
                                  <span className="font-extrabold text-sm">{alg.substance}</span>
                                  {isSevere && (
                                    <span className="text-[10px] font-bold bg-rose-600 text-white px-2 py-0.5 rounded-full uppercase tracking-wider">
                                      High Alert
                                    </span>
                                  )}
                                </div>
                                {alg.reaction && (
                                  <p className="text-xs opacity-80">Reaction: {alg.reaction}</p>
                                )}
                              </div>
                              <div className="text-left sm:text-right">
                                <span className="text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-white/70 border border-slate-200/50">
                                  {alg.severity || "Reported"}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400 italic bg-slate-50 p-3 rounded-xl">No allergies recorded.</p>
                    )}
                  </div>

                  {/* 3. Current Medications */}
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-700 uppercase tracking-wide flex items-center gap-1.5">
                        <Pill size={14} className="text-teal-600" />
                        Current Medications
                      </span>
                      <span className="text-slate-400 text-[11px] font-mono">
                        {summary?.current_medications?.length || 0} active
                      </span>
                    </div>

                    {summary?.current_medications && summary.current_medications.length > 0 ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {summary.current_medications.map((med, idx) => (
                          <div
                            key={idx}
                            className="p-3 rounded-2xl bg-teal-50/40 border border-teal-200/60 flex items-start gap-3"
                          >
                            <div className="w-8 h-8 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center shrink-0 mt-0.5">
                              <Pill size={16} />
                            </div>
                            <div className="min-w-0">
                              <p className="font-bold text-slate-900 text-xs sm:text-sm truncate">{med.name}</p>
                              <p className="text-xs text-slate-600 font-medium">
                                {med.dose} {med.frequency ? `• ${med.frequency}` : ""}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400 italic bg-slate-50 p-3 rounded-xl">No active medications recorded.</p>
                    )}
                  </div>

                  {/* 4. Surgeries */}
                  {summary?.surgeries && summary.surgeries.length > 0 && (
                    <div className="space-y-2">
                      <span className="font-bold text-slate-700 text-xs uppercase tracking-wide flex items-center gap-1.5">
                        <Scissors size={14} className="text-slate-500" />
                        Surgical History
                      </span>
                      <div className="space-y-2">
                        {summary.surgeries.map((surg, idx) => (
                          <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs flex justify-between items-center">
                            <div>
                              <p className="font-bold text-slate-900">{surg.procedure}</p>
                              {surg.indication && <p className="text-slate-500 text-[11px]">{surg.indication}</p>}
                            </div>
                            {surg.year && <span className="font-mono text-slate-400 font-bold">{surg.year}</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                </div>

                {/* Recent Hospital Activity */}
                <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-xs space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-indigo-600" />
                      <h3 className="font-extrabold text-slate-900 text-sm">Recent Hospital Activity</h3>
                    </div>
                    <span className="text-xs text-slate-400">
                      {profile.recent_activity?.length || 0} encounters
                    </span>
                  </div>

                  {profile.recent_activity && profile.recent_activity.length > 0 ? (
                    <div className="space-y-3">
                      {profile.recent_activity.slice(0, 3).map((act, idx) => (
                        <div
                          key={idx}
                          className="p-4 rounded-2xl bg-slate-50/70 border border-slate-200/80 space-y-2"
                        >
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-slate-800">
                              {act.chief_complaint ? `Visit: ${act.chief_complaint}` : "Outpatient Consultation"}
                            </span>
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800">
                              {act.status}
                            </span>
                          </div>

                          {act.date && (
                            <p className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                              <Clock size={12} /> {new Date(act.date).toLocaleDateString()}
                            </p>
                          )}

                          {act.doctor_note?.structured_sections && (
                            <div className="text-xs text-slate-600 bg-white p-2.5 rounded-xl border border-slate-100 line-clamp-2">
                              {act.doctor_note.structured_sections[0]?.content || "Doctor clinical summary recorded."}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic">No prior visits found in current hospital database.</p>
                  )}
                </div>

              </div>

            </div>
          </>
        ) : null}
      </main>

      {/* MODAL 1: Update Contact Details */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-lg w-full shadow-2xl border border-slate-200 space-y-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Edit3 className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-black text-slate-900">Update Contact Details</h3>
              </div>
              <button
                onClick={() => setIsEditModalOpen(false)}
                className="p-1 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 cursor-pointer"
              >
                <X size={20} />
              </button>
            </div>

            {editSuccessMsg && (
              <div className="p-3 bg-emerald-50 text-emerald-800 rounded-2xl text-xs font-bold flex items-center gap-2 border border-emerald-200">
                <CheckCircle2 size={16} />
                <span>{editSuccessMsg}</span>
              </div>
            )}

            <form onSubmit={handleUpdateDemographics} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-700 uppercase">Mobile Number</label>
                <input
                  type="text"
                  value={editPhone}
                  onChange={(e) => setEditPhone(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-slate-300 text-sm font-bold font-mono focus:border-blue-600 focus:outline-hidden"
                  placeholder="e.g. 9876543210"
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-700 uppercase">Email Address</label>
                <input
                  type="email"
                  value={editEmail}
                  onChange={(e) => setEditEmail(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-slate-300 text-sm focus:border-blue-600 focus:outline-hidden"
                  placeholder="name@example.com"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-700 uppercase">Residential Address</label>
                <textarea
                  rows={2}
                  value={editAddress}
                  onChange={(e) => setEditAddress(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:border-blue-600 focus:outline-hidden"
                  placeholder="House number, Street, City, Pincode"
                />
              </div>

              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-3">
                <h4 className="text-xs font-bold text-slate-800 uppercase">Emergency Contact</h4>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    value={editEmergencyName}
                    onChange={(e) => setEditEmergencyName(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs"
                    placeholder="Contact Name"
                  />
                  <input
                    type="text"
                    value={editEmergencyPhone}
                    onChange={(e) => setEditEmergencyPhone(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-mono"
                    placeholder="Emergency Phone"
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(false)}
                  className="flex-1 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold text-sm cursor-pointer"
                  disabled={editLoading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-sm shadow-md shadow-blue-600/20 cursor-pointer flex items-center justify-center gap-2"
                  disabled={editLoading}
                >
                  {editLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Report Medical Change */}
      {isReportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-lg w-full shadow-2xl border border-slate-200 space-y-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <MessageSquarePlus className="w-5 h-5 text-amber-600" />
                <h3 className="text-lg font-black text-slate-900">Report Medical Change</h3>
              </div>
              <button
                onClick={() => setIsReportModalOpen(false)}
                className="p-1 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 cursor-pointer"
              >
                <X size={20} />
              </button>
            </div>

            {/* Clinical Safety Disclaimer */}
            <div className="p-3.5 bg-blue-50 border border-blue-200 rounded-2xl text-xs text-blue-900 space-y-1">
              <div className="flex items-center gap-1.5 font-bold">
                <ShieldCheck size={14} className="text-blue-600" />
                <span>Patient Safety & Verification Guard</span>
              </div>
              <p className="opacity-90 leading-relaxed text-[11px]">
                To protect your clinical safety, doctor-verified medical history cannot be deleted directly. Your reported change will be flagged for your doctor to review and verify during your visit.
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
                  <label className="text-xs font-bold text-slate-700 uppercase">Category of Change</label>
                  <select
                    value={reportCategory}
                    onChange={(e: any) => setReportCategory(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-slate-300 text-sm font-semibold bg-white focus:border-blue-600 focus:outline-hidden"
                  >
                    <option value="allergy">New or Corrected Allergy</option>
                    <option value="medication">Change in Current Medication</option>
                    <option value="condition">New Medical Condition / Diagnosis</option>
                    <option value="procedure">Recent Surgery / Hospitalization</option>
                    <option value="general">Other Medical Discrepancy</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-700 uppercase">Describe the Change</label>
                  <textarea
                    rows={4}
                    value={reportDescription}
                    onChange={(e) => setReportDescription(e.target.value)}
                    className="w-full p-4 rounded-xl border border-slate-300 text-sm focus:border-blue-600 focus:outline-hidden placeholder:text-slate-400"
                    placeholder="e.g. I had an allergic reaction to Septran last week with a rash, or I stopped taking Metformin..."
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
                    {reportLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Submit for Doctor Review"}
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
