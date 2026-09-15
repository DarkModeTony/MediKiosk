import React from "react";

interface BrandEmblemProps {
  size?: "sm" | "md" | "lg";
  className?: string;
  showText?: boolean;
}

export function BrandEmblem({ size = "md", className = "", showText = true }: BrandEmblemProps) {
  const sizeMap = {
    sm: { icon: "w-7 h-7", text: "text-base", sub: "text-[10px]" },
    md: { icon: "w-9 h-9", text: "text-lg", sub: "text-xs" },
    lg: { icon: "w-12 h-12", text: "text-2xl", sub: "text-sm" },
  };

  const { icon, text, sub } = sizeMap[size];

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <div className={`${icon} rounded-xl bg-gradient-to-br from-blue-600 via-teal-600 to-emerald-600 p-0.5 shadow-sm flex items-center justify-center shrink-0`}>
        <div className="w-full h-full bg-white rounded-[10px] flex items-center justify-center p-1.5">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-full h-full text-blue-600"
          >
            <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="currentColor" strokeWidth="2.5" />
            <path d="M7 12h2.5l1.5-3 2 6 1.5-3H17" stroke="#0d9488" strokeWidth="2.5" />
          </svg>
        </div>
      </div>
      {showText && (
        <div className="flex flex-col">
          <span className={`${text} font-extrabold text-slate-900 tracking-tight leading-none`}>
            Medi<span className="text-blue-600">Platform</span>
          </span>
          <span className={`${sub} text-slate-500 font-medium tracking-wider mt-0.5 uppercase`}>
            Clinician Station
          </span>
        </div>
      )}
    </div>
  );
}
