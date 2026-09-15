"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { LargeTouchButton } from "@/components/shared/LargeTouchButton";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { getTranslation } from "@/lib/i18n";
import { Checkbox } from "@/components/ui/checkbox";
import { AudioPromptButton } from "@/components/shared/AudioPromptButton";
import { StatusMessage } from "@/components/shared/StatusMessage";
import { ShieldCheck, Lock, Stethoscope, FileText, CheckCircle, ArrowRight } from "lucide-react";

const privacyPoints = [
  {
    icon: Lock,
    title: "Strictly Confidential",
    desc: "Your medical history and voice transcripts are encrypted and stored safely on our servers.",
    color: "text-blue-600",
    bg: "bg-blue-50",
    border: "border-blue-100",
  },
  {
    icon: Stethoscope,
    title: "Doctor Authoritative",
    desc: "Our AI assistant only organizes your notes. Your doctor reviews and verifies everything.",
    color: "text-teal-600",
    bg: "bg-teal-50",
    border: "border-teal-100",
  },
  {
    icon: FileText,
    title: "Zero Paperwork",
    desc: "Spend less time repeating symptoms, and more time discussing your treatment with your doctor.",
    color: "text-emerald-600",
    bg: "bg-emerald-50",
    border: "border-emerald-100",
  },
];

export default function ConsentPage() {
  const router = useRouter();
  const { language, setHasConsent } = useKiosk();
  const t = getTranslation(language);
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState(false);

  const handleContinue = () => {
    if (!agreed) {
      setError(true);
      return;
    }
    setHasConsent(true);
    router.push("/registration");
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50/20 to-white relative overflow-hidden">
      {/* Decorative blob */}
      <div className="pointer-events-none absolute top-0 right-0 w-[400px] h-[400px] rounded-full bg-teal-400/10 blur-3xl" />

      <AppHeader title={t.consent.title} rightContent={<AudioPromptButton />} />

      <main className="relative flex-1 flex flex-col items-center justify-center p-6 md:p-12 max-w-4xl mx-auto w-full">
        <div className="w-full space-y-8 animate-fade-in">

          {/* Heading */}
          <div className="space-y-3 text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-teal-500 rounded-3xl flex items-center justify-center mx-auto shadow-lg shadow-blue-600/25">
              <ShieldCheck className="w-9 h-9 text-white" />
            </div>
            <h1 className="text-3xl md:text-5xl font-black text-slate-900 tracking-tight">
              {t.consent.title}
            </h1>
            <p className="text-lg md:text-xl text-slate-500 max-w-2xl mx-auto leading-relaxed">
              {t.consent.description}
            </p>
          </div>

          {/* Privacy Points */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {privacyPoints.map(({ icon: Icon, title, desc, color, bg, border }) => (
              <div
                key={title}
                className={`p-5 rounded-2xl ${bg} border ${border} flex flex-col gap-3 hover:shadow-sm transition-shadow`}
              >
                <div className={`w-10 h-10 rounded-xl bg-white flex items-center justify-center shadow-sm border ${border}`}>
                  <Icon className={`w-5 h-5 ${color}`} />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">{title}</h3>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>

          {error && <StatusMessage message={t.consent.error_not_checked} type="error" />}

          {/* Consent Checkbox */}
          <div
            className={`flex items-start gap-5 p-6 rounded-2xl border-2 transition-all cursor-pointer select-none ${
              agreed
                ? "bg-blue-50/60 border-blue-500 shadow-sm shadow-blue-100"
                : "bg-white border-slate-200 hover:border-slate-300 shadow-sm"
            }`}
            onClick={() => {
              setAgreed(!agreed);
              setError(false);
            }}
          >
            <Checkbox
              id="consent"
              checked={agreed}
              onCheckedChange={(c) => {
                setAgreed(c as boolean);
                setError(false);
              }}
              className="w-8 h-8 rounded-xl border-2 border-slate-300 data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600 mt-0.5 shrink-0"
            />
            <div className="flex-1">
              <label htmlFor="consent" className="text-base md:text-lg font-semibold text-slate-800 cursor-pointer leading-relaxed block">
                {t.consent.checkbox}
              </label>
              <p className="text-xs text-slate-400 mt-1">Tap anywhere on this box to confirm your consent.</p>
            </div>
            {agreed && (
              <CheckCircle className="w-6 h-6 text-blue-500 shrink-0 animate-fade-in" />
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-4">
            <LargeTouchButton
              variant="outline"
              onClick={() => router.back()}
              className="flex-1 py-5 text-base"
            >
              {t.common.back}
            </LargeTouchButton>
            <LargeTouchButton
              variant="primary"
              onClick={handleContinue}
              className="flex-[2] py-5 text-xl font-extrabold gap-3"
            >
              {t.common.continue}
              <ArrowRight className="w-5 h-5" />
            </LargeTouchButton>
          </div>
        </div>
      </main>
    </div>
  );
}
