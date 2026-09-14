"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { LargeTouchButton } from "@/components/shared/LargeTouchButton";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { getTranslation } from "@/lib/i18n";
import { CheckCircle2, User } from "lucide-react";

export default function SessionReadyPage() {
  const router = useRouter();
  const { language, session, resetSession } = useKiosk();
  const t = getTranslation(language);

  // Protection: If no session, go home
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
          className="px-6 py-3 rounded-xl bg-destructive/10 text-destructive font-semibold hover:bg-destructive/20 transition-colors"
        >
          Cancel Session
        </button>
      } />
      
      <main className="flex-1 flex flex-col items-center justify-center p-8 max-w-4xl mx-auto w-full">
        
        <div className="bg-white p-16 rounded-3xl shadow-sm border border-border w-full space-y-12 text-center flex flex-col items-center">
          
          <div className="w-32 h-32 bg-emerald-500/10 rounded-full flex items-center justify-center text-emerald-500 mb-4 animate-in zoom-in duration-500">
            <CheckCircle2 size={64} />
          </div>

          <div className="space-y-4">
            <h2 className="text-5xl font-bold text-brand-navy">
              {t.session.success}
            </h2>
            <p className="text-2xl text-muted-foreground">
              {t.session.subtitle}
            </p>
          </div>

          <div className="flex items-center gap-4 px-8 py-6 bg-slate-50 rounded-2xl border border-border w-full justify-center">
            <User size={32} className="text-brand-navy" />
            <span className="text-2xl font-semibold text-brand-navy font-mono tracking-wider">
              ID: {session.patientId?.substring(0, 8).toUpperCase() || "UNKNOWN"}
            </span>
          </div>

          <div className="w-full max-w-md pt-8">
            <LargeTouchButton 
              onClick={() => {
                router.push("/clinical");
              }}
              className="shadow-lg shadow-primary/20"
            >
              Start Clinical Intake
            </LargeTouchButton>
          </div>

        </div>
      </main>
    </div>
  );
}
