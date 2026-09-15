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
import { UserSearch, Delete, Sparkles, Loader2, Phone } from "lucide-react";

export default function ExistingPatientPage() {
  const router = useRouter();
  const { language, setSession } = useKiosk();
  const t = getTranslation(language);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");

  const handleSearch = async (e?: React.FormEvent, directQuery?: string) => {
    if (e) e.preventDefault();
    setError("");

    const term = directQuery || query;
    if (!term || term.trim().length < 2) {
      setError("Please enter your registered mobile number or Patient ID.");
      return;
    }

    setLoading(true);
    try {
      // 1. Search Patient via API
      const patientData = await searchPatient(term.trim());

      // 2. Create Session
      const sessionData = await createKioskSession({
        patient_id: patientData.patient_id,
        language: language,
      });

      // 3. Save to Context & Redirect
      setSession({
        sessionId: sessionData.session_token,
        patientId: patientData.patient_id || sessionData.patient_id,
        encounterId: sessionData.encounter_id ?? undefined,
        expiresAt: sessionData.expires_at,
      });

      router.push("/session");
    } catch (_err: unknown) {
      setError(t.registration.not_found);
      setLoading(false);
    }
  };

  const handleKeypadPress = (val: string) => {
    setQuery((prev) => prev + val);
    setError("");
  };

  const handleBackspace = () => {
    setQuery((prev) => prev.slice(0, -1));
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader title={t.registration.existing} />

      <main className="flex-1 flex flex-col items-center justify-center p-6 md:p-10 max-w-2xl mx-auto w-full">

        <div className="bg-white p-8 md:p-10 rounded-3xl shadow-sm border border-slate-200 w-full space-y-6 text-center">

          <div className="space-y-2">
            <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-2 border border-blue-100">
              <UserSearch className="w-6 h-6" />
            </div>
            <h3 className="text-2xl md:text-3xl font-extrabold text-slate-900">
              {t.registration.search_prompt}
            </h3>
            <p className="text-sm text-slate-500">
              Enter your 10-digit mobile number or Patient ID.
            </p>
          </div>

          {error && <StatusMessage message={error} type="error" />}

          {/* Large Input Display */}
          <div className="relative">
            <Input 
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="text-3xl md:text-4xl p-6 md:p-8 rounded-2xl text-center font-mono font-bold tracking-widest border-2 border-slate-300 focus:border-blue-600" 
              placeholder="e.g. 9876543210"
            />
          </div>

          {/* Quick Demo Test Chip */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-1 text-xs text-slate-500">
            <span>Demo Quick-Fill:</span>
            <button
              type="button"
              onClick={() => {
                setQuery("patient_001");
                handleSearch(undefined, "patient_001");
              }}
              className="px-3 py-1 bg-slate-100 hover:bg-slate-200 rounded-full font-mono text-slate-700 font-bold border border-slate-200 flex items-center gap-1.5 transition cursor-pointer"
            >
              <Sparkles className="w-3 h-3 text-amber-600" />
              patient_001 (Raj Kumar)
            </button>
            <button
              type="button"
              onClick={() => {
                setQuery("9000000001");
                handleSearch(undefined, "9000000001");
              }}
              className="px-3 py-1 bg-blue-50 hover:bg-blue-100 text-blue-800 rounded-full font-mono font-bold border border-blue-200 flex items-center gap-1.5 transition cursor-pointer"
            >
              <Phone className="w-3 h-3 text-blue-600" />
              9000000001 (Mobile)
            </button>
          </div>

          {/* On-screen Numeric Keypad for Touch Kiosks */}
          <div className="grid grid-cols-3 gap-2.5 max-w-xs mx-auto pt-2">
            {["1", "2", "3", "4", "5", "6", "7", "8", "9"].map((num) => (
              <button
                key={num}
                type="button"
                onClick={() => handleKeypadPress(num)}
                className="h-14 rounded-2xl bg-slate-50 border border-slate-200 hover:bg-slate-100 text-2xl font-bold text-slate-800 transition active:scale-95 touch-manipulation"
              >
                {num}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setQuery("")}
              className="h-14 rounded-2xl bg-slate-50 border border-slate-200 hover:bg-slate-100 text-xs font-bold text-slate-500 uppercase tracking-wider transition active:scale-95"
            >
              Clear
            </button>
            <button
              type="button"
              onClick={() => handleKeypadPress("0")}
              className="h-14 rounded-2xl bg-slate-50 border border-slate-200 hover:bg-slate-100 text-2xl font-bold text-slate-800 transition active:scale-95"
            >
              0
            </button>
            <button
              type="button"
              onClick={handleBackspace}
              className="h-14 rounded-2xl bg-slate-50 border border-slate-200 hover:bg-slate-100 flex items-center justify-center text-slate-700 transition active:scale-95"
              aria-label="Backspace"
            >
              <Delete size={24} />
            </button>
          </div>

          {/* Navigation Controls */}
          <div className="flex gap-4 pt-4 border-t border-slate-100">
            <LargeTouchButton 
              type="button"
              variant="outline" 
              onClick={() => router.back()}
              className="flex-1 py-4 text-base"
              disabled={loading}
            >
              {t.common.back}
            </LargeTouchButton>
            <LargeTouchButton 
              type="button"
              variant="primary" 
              onClick={(e) => handleSearch(e)}
              className="flex-[2] py-4 text-lg font-bold shadow-lg shadow-blue-600/20"
              disabled={loading || !query.trim()}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Searching...</span>
                </span>
              ) : (
                <span>{t.common.continue} →</span>
              )}
            </LargeTouchButton>
          </div>

        </div>
      </main>
    </div>
  );
}
