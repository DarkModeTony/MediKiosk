import React from "react";
import { Badge } from "@/components/ui/badge";
import { Sparkles, User, CheckCircle2, ShieldAlert } from "lucide-react";

export type ProvenanceType = "AI_DRAFT" | "PATIENT_REPORTED" | "DOCTOR_VERIFIED" | "SYSTEM";

interface ProvenanceBadgeProps {
  type: ProvenanceType | string;
  className?: string;
  size?: "sm" | "md";
}

export function ProvenanceBadge({ type, className = "", size = "md" }: ProvenanceBadgeProps) {
  switch (type.toUpperCase()) {
    case "AI_DRAFT":
    case "AI_GENERATED":
    case "AI":
      return (
        <Badge variant="ai" className={`gap-1 font-semibold ${size === "sm" ? "text-[10px] py-0.5 px-2" : "text-xs py-1 px-2.5"} ${className}`}>
          <Sparkles className="w-3 h-3 text-indigo-600 animate-pulse" />
          <span>AI DRAFT</span>
        </Badge>
      );
    case "DOCTOR_VERIFIED":
    case "VERIFIED":
      return (
        <Badge variant="verified" className={`gap-1 font-bold ${size === "sm" ? "text-[10px] py-0.5 px-2" : "text-xs py-1 px-2.5"} ${className}`}>
          <CheckCircle2 className="w-3.5 h-3.5 text-teal-700" />
          <span>DOCTOR VERIFIED</span>
        </Badge>
      );
    case "PATIENT_REPORTED":
    case "KIOSK_INTAKE":
      return (
        <Badge variant="secondary" className={`gap-1 text-slate-700 ${size === "sm" ? "text-[10px] py-0.5 px-2" : "text-xs py-1 px-2.5"} ${className}`}>
          <User className="w-3 h-3 text-slate-500" />
          <span>PATIENT REPORTED</span>
        </Badge>
      );
    default:
      return (
        <Badge variant="outline" className={`text-slate-600 ${size === "sm" ? "text-[10px] py-0.5 px-2" : "text-xs py-1 px-2.5"} ${className}`}>
          {type}
        </Badge>
      );
  }
}
