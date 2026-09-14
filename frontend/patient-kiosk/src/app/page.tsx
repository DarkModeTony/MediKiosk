"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { LanguageSelector } from "@/components/shared/LanguageSelector";
import { LargeTouchButton } from "@/components/shared/LargeTouchButton";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { getTranslation } from "@/lib/i18n";
import { HelpCircle } from "lucide-react";

export default function WelcomePage() {
  const router = useRouter();
  const { language } = useKiosk();
  const t = getTranslation(language);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader />
      
      <main className="flex-1 flex flex-col items-center justify-center p-8 max-w-5xl mx-auto w-full gap-16">
        
        {/* Hero Section */}
        <div className="text-center space-y-6">
          <div className="w-32 h-32 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-8">
            {/* Using a placeholder icon for brand */}
            <div className="w-16 h-16 bg-primary rounded-xl rotate-12" />
          </div>
          <h1 className="text-6xl font-extrabold text-brand-navy tracking-tight">
            {t.common.welcome}
          </h1>
          <p className="text-2xl text-muted-foreground font-medium">
            {t.welcome.subtitle}
          </p>
        </div>

        {/* Interaction Section */}
        <div className="flex flex-col items-center gap-10 w-full max-w-md">
          <LanguageSelector />
          
          <LargeTouchButton 
            onClick={() => router.push("/consent")}
            className="shadow-lg shadow-primary/20"
          >
            {t.common.start}
          </LargeTouchButton>
        </div>

      </main>

      {/* Footer / Help */}
      <footer className="p-8 flex justify-end">
        <button className="flex items-center gap-3 px-6 py-4 rounded-full bg-white border-2 border-border text-foreground hover:bg-slate-50 text-xl font-medium transition-colors touch-manipulation">
          <HelpCircle size={28} className="text-primary" />
          {t.common.help}
        </button>
      </footer>
    </div>
  );
}
