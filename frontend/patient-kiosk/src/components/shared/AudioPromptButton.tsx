"use client";

import React from "react";
import { Volume2 } from "lucide-react";

export function AudioPromptButton({ onClick }: { onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 px-6 py-4 rounded-2xl bg-brand-primary/10 text-brand-primary hover:bg-brand-primary/20 transition-colors touch-manipulation"
      aria-label="Play audio help"
    >
      <Volume2 size={28} />
      <span className="text-xl font-medium">Listen</span>
    </button>
  );
}
