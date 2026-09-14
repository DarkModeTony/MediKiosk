"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { AppHeader } from "@/components/shared/AppHeader";
import { LargeTouchButton } from "@/components/shared/LargeTouchButton";
import { getClinicalState, ClinicalState } from "@/lib/api/clinical";
import { CheckCircle2 } from "lucide-react";

export default function ClinicalReviewPage() {
  const router = useRouter();
  const { session, resetSession } = useKiosk();
  const [state, setState] = useState<ClinicalState | null>(null);

  useEffect(() => {
    if (!session) {
      router.replace("/");
      return;
    }
    const load = async () => {
      try {
        const s = await getClinicalState(session.sessionId);
        setState(s);
      } catch (e) {
        console.error(e);
      }
    };
    load();
  }, [session, router]);

  if (!state) return <div className="p-8 text-2xl">Loading...</div>;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader title="Intake Complete" />
      <main className="flex-1 flex flex-col items-center justify-center p-8 max-w-4xl mx-auto w-full gap-12">
        <div className="bg-white p-16 rounded-3xl shadow-sm border border-border w-full text-center space-y-8">
          <div className="w-32 h-32 bg-emerald-500/10 rounded-full flex items-center justify-center text-emerald-500 mx-auto mb-4 animate-in zoom-in duration-500">
            <CheckCircle2 size={64} />
          </div>
          <h2 className="text-4xl font-bold text-brand-navy">
            Thank you!
          </h2>
          <p className="text-2xl text-muted-foreground">
            Your clinical history has been successfully recorded and is now available for the doctor to review.
          </p>
          
          <div className="text-left bg-slate-50 p-8 rounded-2xl border border-border mt-8 space-y-2">
            <h3 className="text-xl font-bold text-brand-navy mb-4">Summary of Recorded Facts (Internal):</h3>
            {Object.entries(state.facts).map(([key, fact]) => (
              <div key={key} className="text-lg text-muted-foreground flex justify-between">
                <span className="font-medium text-brand-navy capitalize">{key.replace(/_/g, " ")}:</span>
                <span>{String(fact.value)}</span>
              </div>
            ))}
          </div>

          <div className="pt-8">
            <LargeTouchButton 
              onClick={resetSession} 
              variant="primary"
              className="shadow-lg shadow-primary/20"
            >
              Finish & Exit
            </LargeTouchButton>
          </div>
        </div>
      </main>
    </div>
  );
}
