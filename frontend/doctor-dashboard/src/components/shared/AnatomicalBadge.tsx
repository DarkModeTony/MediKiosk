import React from "react";
import { Badge } from "@/components/ui/badge";
import { Check, X, HelpCircle, AlertCircle, Wrench } from "lucide-react";

interface AnatomicalBadgeProps {
  status: "PRESENT" | "ABSENT" | "UNKNOWN" | "IMPAIRED" | "PROSTHETIC" | string;
  label?: string;
  className?: string;
}

export function AnatomicalBadge({ status, label, className = "" }: AnatomicalBadgeProps) {
  const norm = (status || "").toUpperCase();

  switch (norm) {
    case "PRESENT":
    case "INTACT":
      return (
        <Badge variant="success" className={`gap-1 font-semibold ${className}`}>
          <Check className="w-3 h-3 text-emerald-700" />
          <span>{label ? `${label}: Present` : "Present"}</span>
        </Badge>
      );
    case "ABSENT":
    case "AMPUTATED":
    case "REMOVED":
      return (
        <Badge variant="destructive" className={`gap-1 font-semibold ${className}`}>
          <X className="w-3 h-3 text-red-700" />
          <span>{label ? `${label}: Absent` : "Absent"}</span>
        </Badge>
      );
    case "IMPAIRED":
    case "PARTIAL":
      return (
        <Badge variant="warning" className={`gap-1 font-semibold ${className}`}>
          <AlertCircle className="w-3 h-3 text-amber-700" />
          <span>{label ? `${label}: Impaired` : "Impaired"}</span>
        </Badge>
      );
    case "PROSTHETIC":
    case "IMPLANT":
    case "ARTIFICIAL":
      return (
        <Badge variant="ai" className={`gap-1 font-semibold ${className}`}>
          <Wrench className="w-3 h-3 text-indigo-700" />
          <span>{label ? `${label}: Prosthetic / Device` : "Prosthetic"}</span>
        </Badge>
      );
    case "UNKNOWN":
    default:
      return (
        <Badge variant="unknown" className={`gap-1 font-medium bg-slate-100 text-slate-600 border border-slate-300 ${className}`}>
          <HelpCircle className="w-3 h-3 text-slate-400" />
          <span>{label ? `${label}: Unknown (Not Examined)` : "Unknown"}</span>
        </Badge>
      );
  }
}
