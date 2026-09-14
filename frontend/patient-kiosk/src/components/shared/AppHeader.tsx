import React from "react";
import { Activity } from "lucide-react";

export function AppHeader({ 
  title, 
  subtitle,
  rightContent 
}: { 
  title?: string;
  subtitle?: string;
  rightContent?: React.ReactNode;
}) {
  return (
    <header className="flex items-center justify-between py-6 px-8 bg-white border-b border-border shadow-sm">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-brand-primary/10 flex items-center justify-center text-primary">
          <Activity size={28} className="text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-brand-navy">
            {title || "MediPlatform"}
          </h1>
          {subtitle && (
            <p className="text-muted-foreground font-medium">{subtitle}</p>
          )}
        </div>
      </div>
      
      {rightContent && (
        <div className="flex items-center gap-4">
          {rightContent}
        </div>
      )}
    </header>
  );
}
