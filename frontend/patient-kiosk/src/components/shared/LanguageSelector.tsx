"use client";

import React from "react";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { Language } from "@/lib/i18n";

export function LanguageSelector() {
  const { language, setLanguage } = useKiosk();

  const languages: { code: Language; label: string }[] = [
    { code: "en", label: "English" },
    { code: "hi", label: "हिन्दी" },
  ];

  return (
    <div className="flex bg-muted p-1 rounded-2xl w-max">
      {languages.map((lang) => {
        const isActive = language === lang.code;
        return (
          <button
            key={lang.code}
            onClick={() => setLanguage(lang.code)}
            className={`px-8 py-4 rounded-xl text-xl font-semibold transition-all duration-200 touch-manipulation ${
              isActive 
                ? "bg-white text-brand-primary shadow-sm ring-1 ring-black/5" 
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {lang.label}
          </button>
        );
      })}
    </div>
  );
}
