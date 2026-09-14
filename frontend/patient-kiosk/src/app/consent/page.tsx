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
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader title={t.consent.title} rightContent={<AudioPromptButton />} />
      
      <main className="flex-1 flex flex-col items-center justify-center p-8 max-w-4xl mx-auto w-full">
        
        <div className="bg-white p-12 rounded-3xl shadow-sm border border-border w-full space-y-12">
          
          <div className="space-y-6 text-center">
            <h2 className="text-4xl font-bold text-brand-navy">
              {t.consent.title}
            </h2>
            <p className="text-2xl leading-relaxed text-muted-foreground">
              {t.consent.description}
            </p>
          </div>

          {error && <StatusMessage message={t.consent.error_not_checked} type="error" />}

          <div 
            className="flex items-center gap-6 p-8 rounded-2xl bg-muted/50 cursor-pointer touch-manipulation hover:bg-muted"
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
              className="w-10 h-10 rounded-lg border-2" 
            />
            <label 
              htmlFor="consent" 
              className="text-2xl font-medium cursor-pointer flex-1"
            >
              {t.consent.checkbox}
            </label>
          </div>

          <div className="flex gap-6 pt-4">
            <LargeTouchButton 
              variant="outline" 
              onClick={() => router.back()}
              className="flex-1"
            >
              {t.common.back}
            </LargeTouchButton>
            <LargeTouchButton 
              variant="primary" 
              onClick={handleContinue}
              className="flex-[2] shadow-lg shadow-primary/20"
            >
              {t.common.continue}
            </LargeTouchButton>
          </div>

        </div>
      </main>
    </div>
  );
}
