import React from "react";
import Link from "next/link";
import Image from "next/image";

interface AppHeaderProps {
  title?: string;
  subtitle?: string;
  rightContent?: React.ReactNode;
}

export function AppHeader({ title, subtitle, rightContent }: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-40 w-full">
      {/* Gradient bar */}
      <div className="h-0.5 w-full bg-gradient-to-r from-blue-600 via-teal-500 to-blue-400" />

      {/* Glass header body */}
      <div className="glass border-b border-white/60 shadow-sm shadow-slate-200/50">
        <div className="max-w-5xl mx-auto flex items-center justify-between px-5 py-3.5">
          {/* Left: Brand + Page Title */}
          <div className="flex items-center gap-3 min-w-0">
            <Link href="/" className="shrink-0">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-teal-500 flex items-center justify-center p-1.5 shadow-sm">
                <Image
                  src="/logo-white.png"
                  alt="MediPlatform"
                  width={24}
                  height={24}
                  className="w-full h-full object-contain"
                />
              </div>
            </Link>

            {title ? (
              <div className="min-w-0">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest leading-none">
                  MediPlatform
                </p>
                <h1 className="text-base font-bold text-slate-900 leading-tight truncate">
                  {title}
                </h1>
                {subtitle && (
                  <p className="text-[11px] text-slate-500 truncate">{subtitle}</p>
                )}
              </div>
            ) : (
              <div>
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest leading-none">
                  MediPlatform
                </p>
                <h1 className="text-base font-bold text-slate-900 leading-tight">
                  Patient Kiosk
                </h1>
              </div>
            )}
          </div>

          {/* Right: Status + Actions */}
          <div className="flex items-center gap-3 shrink-0">
            {/* Live indicator */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wide">Live</span>
            </div>

            {rightContent}
          </div>
        </div>
      </div>
    </header>
  );
}
