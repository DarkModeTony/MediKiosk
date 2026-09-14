"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { LargeTouchButton } from "@/components/shared/LargeTouchButton";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { getTranslation } from "@/lib/i18n";
import { UserPlus, UserSearch } from "lucide-react";

export default function RegistrationPage() {
  const router = useRouter();
  const { language } = useKiosk();
  const t = getTranslation(language);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader title={t.registration.findRecord} />
      
      <main className="flex-1 flex flex-col items-center justify-center p-8 max-w-5xl mx-auto w-full gap-16">
        
        <h2 className="text-5xl font-bold text-brand-navy text-center">
          {t.registration.findRecord}
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full">
          
          <button 
            onClick={() => router.push("/registration/existing")}
            className="flex flex-col items-center gap-8 bg-white p-12 rounded-3xl shadow-sm border-2 border-transparent hover:border-primary/50 transition-all active:scale-95 touch-manipulation group"
          >
            <div className="w-24 h-24 bg-primary/10 rounded-2xl flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
              <UserSearch size={48} />
            </div>
            <span className="text-3xl font-semibold text-brand-navy">
              {t.registration.existing}
            </span>
          </button>

          <button 
            onClick={() => router.push("/registration/new")}
            className="flex flex-col items-center gap-8 bg-white p-12 rounded-3xl shadow-sm border-2 border-transparent hover:border-secondary transition-all active:scale-95 touch-manipulation group"
          >
            <div className="w-24 h-24 bg-secondary/20 rounded-2xl flex items-center justify-center text-brand-navy group-hover:scale-110 transition-transform">
              <UserPlus size={48} />
            </div>
            <span className="text-3xl font-semibold text-brand-navy">
              {t.registration.new}
            </span>
          </button>

        </div>

        <div className="w-full max-w-md pt-8">
          <LargeTouchButton variant="outline" onClick={() => router.back()}>
            {t.common.back}
          </LargeTouchButton>
        </div>

      </main>
    </div>
  );
}
