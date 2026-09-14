"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { LargeTouchButton } from "@/components/shared/LargeTouchButton";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { getTranslation } from "@/lib/i18n";
import { Input } from "@/components/ui/input";
import { StatusMessage } from "@/components/shared/StatusMessage";
import { searchPatient } from "@/lib/api/patients";
import { createKioskSession } from "@/lib/api/kiosk";

export default function ExistingPatientPage() {
  const router = useRouter();
  const { language, setSession } = useKiosk();
  const t = getTranslation(language);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    if (!query || query.length < 3) {
      setError(t.registration.not_found);
      return;
    }

    setLoading(true);
    try {
      // 1. Search Patient
      const patientData = await searchPatient(query);

      // 2. Create Session
      const sessionData = await createKioskSession({
        patient_id: patientData.patient_id,
        language: language,
      });

      // 3. Save to Context & Redirect
      setSession({
        sessionId: sessionData.session_token,
        patientId: patientData.patient_id,
        expiresAt: sessionData.expires_at,
      });

      router.push("/session");
    } catch (err: unknown) {
      const _e = err as Error;
      setError(t.registration.not_found);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader title={t.registration.existing} />
      
      <main className="flex-1 flex flex-col items-center justify-center p-8 max-w-4xl mx-auto w-full">
        
        <form onSubmit={handleSearch} className="bg-white p-12 rounded-3xl shadow-sm border border-border w-full space-y-12 text-center">
          
          <h3 className="text-3xl font-semibold text-brand-navy">
            {t.registration.search_prompt}
          </h3>
          
          {error && <StatusMessage message={error} type="error" />}

          <Input 
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="text-4xl p-10 rounded-3xl text-center font-bold tracking-widest placeholder:font-normal placeholder:tracking-normal" 
            placeholder="e.g. 9876543210"
          />

          <div className="flex gap-6 pt-4">
            <LargeTouchButton 
              type="button"
              variant="outline" 
              onClick={() => router.back()}
              className="flex-1"
              disabled={loading}
            >
              {t.common.back}
            </LargeTouchButton>
            <LargeTouchButton 
              type="submit"
              variant="primary" 
              className="flex-[2] shadow-lg shadow-primary/20"
              disabled={loading}
            >
              {loading ? t.common.loading : t.common.continue}
            </LargeTouchButton>
          </div>

        </form>
      </main>
    </div>
  );
}
