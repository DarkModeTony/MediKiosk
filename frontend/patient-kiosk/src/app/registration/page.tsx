"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { LargeTouchButton } from "@/components/shared/LargeTouchButton";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { getTranslation } from "@/lib/i18n";
import { UserPlus, UserSearch, ArrowRight, Sparkles, ChevronLeft } from "lucide-react";

export default function RegistrationPage() {
  const router = useRouter();
  const { language } = useKiosk();
  const t = getTranslation(language);

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50/20 to-white relative overflow-hidden">
      <div className="pointer-events-none absolute -bottom-40 -right-40 w-[500px] h-[500px] rounded-full bg-blue-400/10 blur-3xl" />

      <AppHeader title={t.registration.findRecord} />

      <main className="relative flex-1 flex flex-col items-center justify-center p-6 md:p-12 max-w-5xl mx-auto w-full gap-10">

        {/* Heading */}
        <div className="text-center space-y-3 animate-fade-in">
          <h1 className="text-3xl md:text-5xl font-black text-slate-900 tracking-tight">
            {t.registration.findRecord}
          </h1>
          <p className="text-lg md:text-xl text-slate-500 max-w-xl mx-auto">
            Choose whether you have visited this hospital before or are a first-time patient.
          </p>
        </div>

        {/* Two large touch cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8 w-full animate-slide-up">

          {/* Existing Patient */}
          <button
            onClick={() => router.push("/registration/existing")}
            className="group relative flex flex-col items-start text-left p-8 md:p-10 bg-white rounded-3xl border-2 border-slate-200 hover:border-blue-500 shadow-sm hover:shadow-xl hover:shadow-blue-500/10 transition-all duration-300 active:scale-[0.99] touch-manipulation overflow-hidden"
          >
            {/* Hover gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-3xl" />

            <div className="relative w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-blue-600/25 group-hover:scale-105 transition-transform duration-300">
              <UserSearch size={32} className="text-white" />
            </div>

            <div className="relative space-y-2 flex-1">
              <h2 className="text-2xl md:text-3xl font-bold text-slate-900 group-hover:text-blue-700 transition-colors duration-200">
                {t.registration.existing}
              </h2>
              <p className="text-slate-500 text-sm md:text-base leading-relaxed">
                Enter your registered mobile number, Hospital Patient ID, or scan your hospital barcode.
              </p>
            </div>

            <div className="relative mt-8 flex items-center gap-2 text-blue-600 font-bold text-base group-hover:translate-x-1.5 transition-transform duration-200">
              <span>Find My Record</span>
              <ArrowRight size={20} />
            </div>
          </button>

          {/* New Patient */}
          <button
            onClick={() => router.push("/registration/new")}
            className="group relative flex flex-col items-start text-left p-8 md:p-10 bg-white rounded-3xl border-2 border-slate-200 hover:border-teal-500 shadow-sm hover:shadow-xl hover:shadow-teal-500/10 transition-all duration-300 active:scale-[0.99] touch-manipulation overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-teal-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-3xl" />

            <div className="relative w-16 h-16 bg-gradient-to-br from-teal-500 to-teal-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-teal-600/25 group-hover:scale-105 transition-transform duration-300">
              <UserPlus size={32} className="text-white" />
            </div>

            <div className="relative space-y-2 flex-1">
              <div className="flex items-center gap-3 flex-wrap">
                <h2 className="text-2xl md:text-3xl font-bold text-slate-900 group-hover:text-teal-700 transition-colors duration-200">
                  {t.registration.new}
                </h2>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-teal-100 text-teal-800">
                  <Sparkles size={11} />
                  Quick · 2 min
                </span>
              </div>
              <p className="text-slate-500 text-sm md:text-base leading-relaxed">
                First time here? Register your basic details to begin your OPD clinical intake.
              </p>
            </div>

            <div className="relative mt-8 flex items-center gap-2 text-teal-600 font-bold text-base group-hover:translate-x-1.5 transition-transform duration-200">
              <span>Register as New Patient</span>
              <ArrowRight size={20} />
            </div>
          </button>
        </div>

        {/* Back button */}
        <div className="w-full max-w-xs animate-fade-in">
          <LargeTouchButton variant="outline" onClick={() => router.back()} className="py-4 text-base gap-2">
            <ChevronLeft className="w-4 h-4" />
            {t.common.back}
          </LargeTouchButton>
        </div>
      </main>
    </div>
  );
}
