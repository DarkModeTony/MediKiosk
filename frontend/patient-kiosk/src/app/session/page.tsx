"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { getTranslation } from "@/lib/i18n";
import { 
  CheckCircle2, 
  User, 
  Stethoscope, 
  UploadCloud, 
  FileText, 
  ArrowRight,
  LogOut,
  ShieldCheck,
  Clock
} from "lucide-react";

export default function SessionReadyPage() {
  const router = useRouter();
  const { language, session, resetSession } = useKiosk();
  const t = getTranslation(language);

  useEffect(() => {
    if (!session) {
      router.replace("/");
    }
  }, [session, router]);

  if (!session) return null;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader rightContent={
        <button 
          onClick={resetSession}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 hover:bg-red-50 text-slate-600 hover:text-red-700 text-xs md:text-sm font-semibold border border-slate-200 transition-colors"
        >
          <LogOut size={16} />
          <span>Exit Kiosk</span>
        </button>
      } />

      <main className="flex-1 flex flex-col items-center justify-center p-6 md:p-10 max-w-5xl mx-auto w-full gap-8">

        {/* Patient Identity Header Banner */}
        <div className="bg-white p-6 md:p-8 rounded-3xl shadow-sm border border-slate-200 w-full flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center border border-emerald-100 shrink-0">
              <CheckCircle2 size={32} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 uppercase tracking-wide">
                  Active Intake Session
                </span>
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <Clock size={12} /> 5 min idle auto-reset
                </span>
              </div>
              <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 mt-1">
                {t.session.success}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-3 px-5 py-3 bg-slate-50 rounded-2xl border border-slate-200">
            <User size={24} className="text-slate-500" />
            <div className="text-left">
              <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Patient Identifier</p>
              <p className="text-lg font-mono font-bold text-slate-800">
                {session.patientId?.substring(0, 12).toUpperCase() || "UNKNOWN"}
              </p>
            </div>
          </div>
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
          <ShieldCheck size={16} className="text-slate-400" />
          <span>Your session is automatically saved to the hospital queue. Take your time.</span>
        </div>

      </main>
    </div>
  );
}
