"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { LanguageSelector } from "@/components/shared/LanguageSelector";
import { LargeTouchButton } from "@/components/shared/LargeTouchButton";
import { BrandEmblem } from "@/components/shared/BrandEmblem";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { getTranslation } from "@/lib/i18n";
import {
  ShieldCheck,
  UserCheck,
  Stethoscope,
  AlertOctagon,
  HelpCircle,
  ArrowRight,
  Clock,
  FileText,
} from "lucide-react";

export default function WelcomePage() {
  const router = useRouter();
  const { language } = useKiosk();
  const t = getTranslation(language);

  const steps = [
    {
      num: "01",
      icon: UserCheck,
      title: "Check-In",
      desc: "Provide your name or existing Patient ID.",
      color: "from-blue-500 to-blue-600",
      ring: "ring-blue-100",
    },
    {
      num: "02",
      icon: Stethoscope,
      title: "Share Symptoms",
      desc: "Speak in your language or use the touchscreen.",
      color: "from-teal-500 to-teal-600",
      ring: "ring-teal-100",
    },
    {
      num: "03",
      icon: FileText,
      title: "Meet Doctor",
      desc: "Your doctor receives a prepared clinical summary.",
      color: "from-emerald-500 to-emerald-600",
      ring: "ring-emerald-100",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50/30 to-teal-50/20 relative overflow-hidden">
      {/* Background decorative blobs */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-[600px] h-[600px] rounded-full bg-blue-400/10 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-[500px] h-[500px] rounded-full bg-teal-400/10 blur-3xl" />
      </div>

      <AppHeader />

      <main className="relative flex-1 flex flex-col items-center justify-center p-6 md:p-12 max-w-5xl mx-auto w-full gap-10">

        {/* Hero Section */}
        <div className="text-center space-y-6 flex flex-col items-center animate-fade-in">
          {/* Floating brand emblem */}
          <div className="animate-float">
            <BrandEmblem size="xl" />
          </div>

          <div className="space-y-3 max-w-2xl">
            <h1 className="text-5xl md:text-7xl font-black tracking-tight leading-[1.05]">
              <span className="text-slate-900">Welcome to</span>
              <br />
              <span className="text-gradient">MediPlatform</span>
            </h1>
            <p className="text-xl md:text-2xl text-slate-500 font-normal leading-relaxed">
              {t.welcome.subtitle}
            </p>
          </div>

          {/* Trust badges */}
          <div className="flex flex-wrap justify-center gap-3 pt-1">
            {[
              { icon: ShieldCheck, text: "Private & Secure", bg: "bg-blue-50/80 border-blue-200/70 text-blue-800" },
              { icon: Stethoscope, text: "Doctor Reviewed", bg: "bg-teal-50/80 border-teal-200/70 text-teal-800" },
              { icon: Clock, text: "Under 5 Minutes", bg: "bg-slate-100 border-slate-200 text-slate-700" },
              { icon: UserCheck, text: "Voice Enabled", bg: "bg-emerald-50/80 border-emerald-200/70 text-emerald-800" },
            ].map(({ icon: Icon, text, bg }) => (
              <div
                key={text}
                className={`inline-flex items-center gap-2 px-3.5 py-1.5 border rounded-full text-xs md:text-sm font-semibold ${bg}`}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span>{text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 3-Step Visual Guide */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-3xl animate-slide-up">
          {steps.map((step) => (
            <div
              key={step.num}
              className="group relative p-5 bg-white/80 backdrop-blur-sm rounded-2xl border border-white shadow-sm hover:shadow-md transition-all duration-300 flex items-start gap-4 overflow-hidden"
            >
              {/* Subtle gradient background */}
              <div className={`absolute inset-0 bg-gradient-to-br ${step.color} opacity-0 group-hover:opacity-[0.03] transition-opacity duration-300`} />

              <div
                className={`relative w-11 h-11 rounded-xl bg-gradient-to-br ${step.color} flex items-center justify-center shrink-0 shadow-sm ring-4 ${step.ring}`}
              >
                <step.icon className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  Step {step.num}
                </span>
                <h3 className="font-bold text-slate-900 text-base">{step.title}</h3>
                <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Language + CTA */}
        <div className="flex flex-col items-center gap-5 w-full max-w-md animate-slide-up">
          <div className="w-full glass p-5 rounded-2xl shadow-sm">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 text-center">
              Select Your Preferred Language
            </p>
            <LanguageSelector />
          </div>

          <LargeTouchButton
            onClick={() => router.push("/consent")}
            className="text-xl font-extrabold py-6 gap-3"
          >
            {t.common.start}
            <ArrowRight className="w-5 h-5" />
          </LargeTouchButton>
        </div>

        {/* Emergency Banner */}
        <div className="w-full max-w-3xl p-4 bg-amber-50 border border-amber-300/60 rounded-2xl flex items-start gap-3 text-amber-900 text-xs md:text-sm shadow-sm animate-fade-in">
          <AlertOctagon className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <p>
            <strong>Immediate Medical Emergency?</strong> If you are experiencing severe chest
            pain, sudden breathlessness, or heavy bleeding, please notify hospital staff
            immediately.
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative py-4 px-8 border-t border-slate-200/60 bg-white/60 backdrop-blur-sm flex items-center justify-between text-xs text-slate-400">
        <span>MediPlatform Healthcare Kiosk • v2.0</span>
        <div className="flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-slate-300" />
          <span>Need help? Press screen or ask attendant</span>
        </div>
      </footer>
    </div>
  );
}
