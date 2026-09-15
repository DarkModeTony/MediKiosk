"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { AppHeader } from "@/components/shared/AppHeader";
import { LargeTouchButton } from "@/components/shared/LargeTouchButton";
import { StatusMessage } from "@/components/shared/StatusMessage";
import { startClinicalIntake } from "@/lib/api/clinical";
import { Mic, Touchpad, Stethoscope, Sparkles, ChevronLeft, ArrowRight } from "lucide-react";

export default function ClinicalIntroPage() {
  const router = useRouter();
  const { session } = useKiosk();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!session) router.replace("/");
  }, [session, router]);

  const handleStart = async () => {
    if (!session) return;
    setLoading(true);
    try {
      await startClinicalIntake(session.sessionId);
      router.push("/clinical/conversation");
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || "Failed to start clinical intake. Please try again.");
      setLoading(false);
    }
  };

  if (!session) return null;

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50/20 to-white relative overflow-hidden">
      <div className="pointer-events-none absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full bg-blue-400/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -left-40 w-[400px] h-[400px] rounded-full bg-teal-400/10 blur-3xl" />

      <AppHeader title="Clinical Intake" subtitle="Symptom Interview" />

      <main className="relative flex-1 flex flex-col items-center justify-center p-6 md:p-10 max-w-4xl mx-auto w-full">
        <div className="w-full animate-fade-in">
          <div className="bg-white/90 backdrop-blur-sm p-8 md:p-14 rounded-3xl shadow-sm border border-slate-200 text-center space-y-8">

            {/* Icon Hero */}
            <div className="relative inline-flex">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-3xl flex items-center justify-center mx-auto shadow-2xl shadow-blue-600/30">
                <Stethoscope size={40} className="text-white" />
              </div>
              <span className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-emerald-500 border-2 border-white flex items-center justify-center">
                <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
              </span>
            </div>

            <div className="space-y-4 max-w-2xl mx-auto">
              <h1 className="text-3xl md:text-5xl font-black text-slate-900 tracking-tight">
                Let&apos;s understand your symptoms.
              </h1>
              <p className="text-lg md:text-xl text-slate-500 font-normal leading-relaxed">
                Our clinical assistant will ask you a few simple questions. Answer naturally by
                speaking in your language or tapping the screen.
              </p>
            </div>

            {error && <StatusMessage message={error} type="error" />}

            {/* Two ways cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto text-left">
              {[
                {
                  icon: Mic,
                  title: "Speak Your Answer",
                  desc: "Tap the microphone and speak naturally in Hindi, English, or any Indian regional language.",
                  color: "text-blue-600",
                  bg: "bg-blue-50",
                  border: "border-blue-100",
                },
                {
                  icon: Touchpad,
                  title: "Touch Options",
                  desc: "Prefer touching? Clear option buttons appear on screen for each question.",
                  color: "text-teal-600",
                  bg: "bg-teal-50",
                  border: "border-teal-100",
                },
              ].map(({ icon: Icon, title, desc, color, bg, border }) => (
                <div key={title} className={`p-5 rounded-2xl ${bg} border ${border} flex items-start gap-4`}>
                  <div className={`w-12 h-12 rounded-xl bg-white flex items-center justify-center shrink-0 shadow-sm border ${border}`}>
                    <Icon size={24} className={color} />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-base">{title}</h4>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">{desc}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* AI badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-50 border border-indigo-100 rounded-full text-xs font-semibold text-indigo-800">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              <span>AI organizes your answers. Your doctor reviews and confirms everything.</span>
            </div>

            {/* Actions */}
            <div className="flex gap-4 pt-2 max-w-xl mx-auto w-full">
              <LargeTouchButton
                variant="outline"
                onClick={() => router.push("/session")}
                className="flex-1 py-5 text-base gap-2"
                disabled={loading}
              >
                <ChevronLeft size={18} />
                Back
              </LargeTouchButton>
              <LargeTouchButton
                onClick={handleStart}
                loading={loading}
                className="flex-[2] py-5 text-xl font-extrabold gap-3"
              >
                Begin Interview
                <ArrowRight size={20} />
              </LargeTouchButton>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
