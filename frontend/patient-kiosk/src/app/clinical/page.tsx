"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { AppHeader } from "@/components/shared/AppHeader";
import { LargeTouchButton } from "@/components/shared/LargeTouchButton";
import { StatusMessage } from "@/components/shared/StatusMessage";
import { startClinicalIntake } from "@/lib/api/clinical";

export default function ClinicalIntroPage() {
  const router = useRouter();
  const { session } = useKiosk();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!session) {
      router.replace("/");
    }
  }, [session, router]);

  const handleStart = async () => {
    if (!session) return;
    setLoading(true);
    try {
      if (process.env.NEXT_PUBLIC_AI_MODE === "mock") {
        console.log("MOCK MODE: Initializing clinical state");
      }
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
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader title="Medical History" />
      <main className="flex-1 flex flex-col items-center justify-center p-8 max-w-4xl mx-auto w-full">
        <div className="bg-white p-12 rounded-3xl shadow-sm border border-border w-full text-center space-y-8">
          <h2 className="text-4xl font-bold text-brand-navy">
            Let&apos;s understand your symptoms.
          </h2>
          <p className="text-2xl text-muted-foreground">
            I am going to ask you a few questions about how you are feeling. You can answer by speaking or touching the screen.
          </p>
          
          {error && <StatusMessage message={error} type="error" />}

          <div className="pt-8">
            <LargeTouchButton 
              onClick={handleStart} 
              disabled={loading}
              className="shadow-lg shadow-primary/20"
            >
              {loading ? "Starting..." : "Begin"}
            </LargeTouchButton>
          </div>
        </div>
      </main>
    </div>
  );
}
