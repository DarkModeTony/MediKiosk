"use client";

import React from "react";
import { AlertCircle, CheckCircle2 } from "lucide-react";

export function StatusMessage({ 
  message, 
  type = "error" 
}: { 
  message: string; 
  type?: "error" | "success" 
}) {
  if (!message) return null;

  return (
    <div className={`flex items-center gap-4 p-6 rounded-2xl border-2 ${
      type === "error" 
        ? "bg-destructive/10 border-destructive/20 text-destructive-foreground" 
        : "bg-emerald-500/10 border-emerald-500/20 text-emerald-700"
    }`}>
      {type === "error" ? (
        <AlertCircle size={32} className="text-destructive shrink-0" />
      ) : (
        <CheckCircle2 size={32} className="text-emerald-600 shrink-0" />
      )}
      <p className="text-xl font-medium">{message}</p>
    </div>
  );
}
