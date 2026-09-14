"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { Language } from "@/lib/i18n";
import { useRouter } from "next/navigation";

interface KioskSession {
  sessionId: string;
  patientId?: string;
  encounterId?: string;
  expiresAt: string;
}

interface KioskContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  hasConsent: boolean;
  setHasConsent: (consent: boolean) => void;
  session: KioskSession | null;
  setSession: (session: KioskSession | null) => void;
  resetSession: () => void;
}

const KioskContext = createContext<KioskContextType | undefined>(undefined);

const INACTIVITY_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

export function KioskSessionProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>("en");
  const [hasConsent, setHasConsent] = useState(false);
  const [session, setSession] = useState<KioskSession | null>(null);
  const router = useRouter();

  // Reset all state (except language, optionally)
  const resetSession = useCallback(() => {
    setHasConsent(false);
    setSession(null);
    router.push("/");
  }, [router]);

  // Inactivity timeout
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    const resetTimer = () => {
      clearTimeout(timeoutId);
      // Only reset if they are in the flow (e.g., have consent or session)
      if (hasConsent || session) {
        timeoutId = setTimeout(() => {
          resetSession();
        }, INACTIVITY_TIMEOUT_MS);
      }
    };

    // Events to track activity
    const events = ["mousedown", "mousemove", "keydown", "scroll", "touchstart"];
    
    resetTimer(); // init
    events.forEach((e) => window.addEventListener(e, resetTimer));

    return () => {
      clearTimeout(timeoutId);
      events.forEach((e) => window.removeEventListener(e, resetTimer));
    };
  }, [hasConsent, session, resetSession]);

  return (
    <KioskContext.Provider
      value={{
        language,
        setLanguage,
        hasConsent,
        setHasConsent,
        session,
        setSession,
        resetSession,
      }}
    >
      {children}
    </KioskContext.Provider>
  );
}

export function useKiosk() {
  const context = useContext(KioskContext);
  if (context === undefined) {
    throw new Error("useKiosk must be used within a KioskSessionProvider");
  }
  return context;
}
