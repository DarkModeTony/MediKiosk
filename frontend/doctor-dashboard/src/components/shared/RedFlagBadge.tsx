import React from "react";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, AlertCircle, ShieldAlert, Info } from "lucide-react";

interface RedFlagBadgeProps {
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | string;
  ruleName?: string;
  className?: string;
}

export function RedFlagBadge({ severity, ruleName, className = "" }: RedFlagBadgeProps) {
  const norm = (severity || "").toUpperCase();

  let variant: "critical" | "destructive" | "warning" | "secondary" = "warning";
  let icon = <AlertTriangle className="w-3.5 h-3.5 mr-1" />;

  if (norm === "CRITICAL") {
    variant = "critical";
    icon = <ShieldAlert className="w-3.5 h-3.5 mr-1" />;
  } else if (norm === "HIGH") {
    variant = "destructive";
    icon = <AlertCircle className="w-3.5 h-3.5 mr-1" />;
  } else if (norm === "MEDIUM" || norm === "MODERATE") {
    variant = "warning";
    icon = <AlertTriangle className="w-3.5 h-3.5 mr-1" />;
  } else {
    variant = "secondary";
    icon = <Info className="w-3.5 h-3.5 mr-1 text-slate-500" />;
  }

  return (
    <Badge variant={variant} className={`inline-flex items-center tracking-wide font-bold uppercase ${className}`}>
      {icon}
      <span>{severity}</span>
      {ruleName && <span className="ml-1 opacity-90 font-normal lowercase tracking-normal">({ruleName})</span>}
    </Badge>
  );
}
