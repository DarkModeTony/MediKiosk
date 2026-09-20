"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { getTranslation } from "@/lib/i18n";
import { getPatientProfile, PatientProfileResponse } from "@/lib/api/profile";
import { 
  CheckCircle2, 
  User, 
  Stethoscope, 
  UploadCloud, 
  FileText, 
  ArrowRight,
  ShieldCheck,
  Clock,
  FileClock,
  HeartPulse,
  AlertTriangle,
  Pill,
  ChevronRight,
  Sparkles
} from "lucide-react";

export default function SessionReadyPage() {
  const router = useRouter();
  const { language, session } = useKiosk();
  const t = getTranslation(language);

  const [profileData, setProfileData] = useState<PatientProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session?.sessionId) {
      router.replace("/");
      return;
    }

    let isMounted = true;
    async function loadData() {
      try {
        const data = await getPatientProfile(session!.sessionId);
        if (isMounted) {
          setProfileData(data);
        }
      } catch (err) {
        console.warn("Could not fetch profile snapshot:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [session, router]);

  if (!session) return null;

  const demographics = profileData?.demographics;
  const patientName = demographics?.name || "Patient";
  const allergiesCount = profileData?.profile_summary?.allergies?.length || 0;
  const conditionsCount = profileData?.profile_summary?.chronic_conditions?.length || 0;
  const medsCount = profileData?.profile_summary?.current_medications?.length || 0;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50/50">
      <AppHeader patientName={patientName} showNav={true} />

      <main className="flex-1 flex flex-col items-center justify-start p-4 sm:p-6 md:p-10 max-w-5xl mx-auto w-full gap-6">

        {/* Patient Identity Header Banner */}
        <div className="bg-white p-6 md:p-8 rounded-3xl shadow-xs border border-slate-200/80 w-full flex flex-wrap items-center justify-between gap-4 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-blue-500/5 to-teal-500/5 rounded-full blur-2xl -z-0 pointer-events-none" />

          <div className="flex items-center gap-4 relative z-10">
            <div className="w-14 h-14 bg-gradient-to-br from-emerald-50 to-teal-50 text-emerald-600 rounded-2xl flex items-center justify-center border border-emerald-200/60 shadow-xs shrink-0">
              <CheckCircle2 size={32} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 uppercase tracking-wide">
                  Active Intake Session
                </span>
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <Clock size={12} /> Auto-lock protected
                </span>
              </div>
              <h2 className="text-2xl md:text-3xl font-black text-slate-900 mt-1 tracking-tight">
                {loading ? t.session.success : `Welcome, ${patientName}`}
              </h2>
              {demographics && (
                <p className="text-xs sm:text-sm text-slate-500 font-medium">
                  {demographics.gender || "Patient"} • {demographics.age ? `${demographics.age} yrs` : ""} • Blood Group: <span className="font-bold text-slate-700">{demographics.blood_group || "Not recorded"}</span>
                </p>
              )}
            </div>
          </div>

          {/* Quick Profile & History Shortcut Chips */}
          <div className="flex items-center gap-2 relative z-10">
            <button
              onClick={() => router.push("/profile")}
              className="flex items-center gap-2 px-4 py-2.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-2xl border border-blue-200/80 font-bold text-xs transition cursor-pointer shadow-xs active:scale-95"
            >
              <User size={16} />
              <span>View Profile</span>
            </button>
            <button
              onClick={() => router.push("/history")}
              className="flex items-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-2xl border border-slate-200 font-bold text-xs transition cursor-pointer shadow-xs active:scale-95"
            >
              <FileClock size={16} />
              <span>Medical History</span>
            </button>
          </div>
        </div>

        {/* Primary Row: Quick Health Summary Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full">
          <div 
            onClick={() => router.push("/history")}
            className="p-4 bg-white rounded-2xl border border-slate-200 shadow-2xs hover:border-blue-400 transition cursor-pointer group"
          >
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span className="text-[11px] font-bold uppercase tracking-wider">Conditions</span>
              <HeartPulse size={16} className="text-blue-600 group-hover:scale-110 transition-transform" />
            </div>
            <p className="text-2xl font-black text-slate-900">{conditionsCount}</p>
            <p className="text-[11px] text-slate-500 truncate">Known Chronic</p>
          </div>

          <div 
            onClick={() => router.push("/history")}
            className="p-4 bg-white rounded-2xl border border-slate-200 shadow-2xs hover:border-amber-400 transition cursor-pointer group"
          >
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span className="text-[11px] font-bold uppercase tracking-wider">Allergies</span>
              <AlertTriangle size={16} className="text-amber-500 group-hover:scale-110 transition-transform" />
            </div>
            <p className="text-2xl font-black text-slate-900">{allergiesCount}</p>
            <p className="text-[11px] text-slate-500 truncate">Recorded Safety</p>
          </div>

          <div 
            onClick={() => router.push("/history")}
            className="p-4 bg-white rounded-2xl border border-slate-200 shadow-2xs hover:border-teal-400 transition cursor-pointer group"
          >
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span className="text-[11px] font-bold uppercase tracking-wider">Medications</span>
              <Pill size={16} className="text-teal-600 group-hover:scale-110 transition-transform" />
            </div>
            <p className="text-2xl font-black text-slate-900">{medsCount}</p>
            <p className="text-[11px] text-slate-500 truncate">Current Active</p>
          </div>

          <div 
            onClick={() => router.push("/profile")}
            className="p-4 bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-2xl shadow-xs hover:opacity-95 transition cursor-pointer group flex flex-col justify-between"
          >
            <div className="flex items-center justify-between text-blue-200 mb-1">
              <span className="text-[11px] font-bold uppercase tracking-wider">My Profile</span>
              <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </div>
            <p className="text-base font-bold truncate">Contact & Emergency</p>
            <p className="text-[11px] text-blue-100">Review & Update →</p>
          </div>
        </div>

        {/* Section Heading */}
        <div className="w-full flex items-center justify-between pt-2">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-600" />
            <h3 className="text-lg font-extrabold text-slate-800">Visit Preparation Actions</h3>
          </div>
          <span className="text-xs text-slate-400">Complete before seeing doctor</span>
        </div>

        {/* 3 Intake Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">

          {/* Card 1: Clinical Symptom Intake */}
          <div 
            onClick={() => router.push("/clinical")}
            className="flex flex-col justify-between p-8 bg-white rounded-3xl border-2 border-blue-500/80 shadow-md shadow-blue-500/5 hover:border-blue-600 hover:shadow-lg transition-all cursor-pointer group active:scale-[0.99] relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-24 h-24 bg-blue-50 rounded-bl-full -z-0 opacity-50" />
            
            <div className="relative z-10 space-y-4">
              <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center border border-blue-100 group-hover:scale-105 transition-transform">
                <Stethoscope size={30} />
              </div>
              <div className="space-y-1">
                <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">Step 1 • Recommended</span>
                <h3 className="text-2xl font-black text-slate-900 group-hover:text-blue-600 transition-colors">
                  Symptom Intake
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed pt-1">
                  Describe what brings you to the hospital today. Use your voice in any language or touch the screen.
                </p>
              </div>
            </div>

            <div className="relative z-10 pt-6 mt-6 border-t border-slate-100 flex items-center justify-between text-blue-600 font-bold text-base">
              <span>Start Clinical Questions</span>
              <ArrowRight size={20} className="group-hover:translate-x-1.5 transition-transform" />
            </div>
          </div>

          {/* Card 2: Upload Documents */}
          <div 
            onClick={() => router.push("/documents")}
            className="flex flex-col justify-between p-8 bg-white rounded-3xl border-2 border-slate-200 hover:border-teal-500 hover:shadow-md transition-all cursor-pointer group active:scale-[0.99]"
          >
            <div className="space-y-4">
              <div className="w-14 h-14 bg-teal-50 text-teal-600 rounded-2xl flex items-center justify-center border border-teal-100 group-hover:scale-105 transition-transform">
                <UploadCloud size={30} />
              </div>
              <div className="space-y-1">
                <span className="text-xs font-bold text-teal-600 uppercase tracking-wider">Step 2 • Optional</span>
                <h3 className="text-2xl font-black text-slate-900 group-hover:text-teal-600 transition-colors">
                  Prescription / Reports
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed pt-1">
                  Scan or upload previous doctor prescriptions, discharge summaries, or blood lab reports for AI extraction.
                </p>
              </div>
            </div>

            <div className="pt-6 mt-6 border-t border-slate-100 flex items-center justify-between text-teal-700 font-bold text-base">
              <span>Upload Records</span>
              <ArrowRight size={20} className="group-hover:translate-x-1.5 transition-transform" />
            </div>
          </div>

          {/* Card 3: Review Visit Summary */}
          <div 
            onClick={() => router.push("/summary-preview")}
            className="flex flex-col justify-between p-8 bg-white rounded-3xl border-2 border-slate-200 hover:border-slate-400 hover:shadow-md transition-all cursor-pointer group active:scale-[0.99]"
          >
            <div className="space-y-4">
              <div className="w-14 h-14 bg-slate-100 text-slate-700 rounded-2xl flex items-center justify-center border border-slate-200 group-hover:scale-105 transition-transform">
                <FileText size={30} />
              </div>
              <div className="space-y-1">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Step 3 • Overview</span>
                <h3 className="text-2xl font-black text-slate-900 group-hover:text-slate-700 transition-colors">
                  Visit Summary
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed pt-1">
                  Preview the compiled clinical information before proceeding to wait for your OPD doctor.
                </p>
              </div>
            </div>

            <div className="pt-6 mt-6 border-t border-slate-100 flex items-center justify-between text-slate-700 font-bold text-base">
              <span>View Visit Summary</span>
              <ArrowRight size={20} className="group-hover:translate-x-1.5 transition-transform" />
            </div>
          </div>

        </div>

        {/* Security & Confidentiality Notice */}
        <div className="flex items-center justify-center gap-2 text-xs text-slate-500 pt-2">
          <ShieldCheck size={16} className="text-emerald-600" />
          <span>Your session is authenticated and protected. Patient data is encrypted and saved to the hospital queue.</span>
        </div>

      </main>
    </div>
  );
}
