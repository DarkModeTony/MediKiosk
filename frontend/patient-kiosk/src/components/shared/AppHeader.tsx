"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { Home, User, FileClock, LogOut } from "lucide-react";

interface AppHeaderProps {
  title?: string;
  subtitle?: string;
  rightContent?: React.ReactNode;
  showNav?: boolean;
  patientName?: string;
}

export function AppHeader({ title, subtitle, rightContent, showNav, patientName }: AppHeaderProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { session, resetSession } = useKiosk();

  const isSessionActive = Boolean(session?.sessionId);
  const shouldRenderNav = showNav ?? (isSessionActive && pathname !== "/" && pathname !== "/consent" && !pathname.startsWith("/registration"));

  return (
    <header className="sticky top-0 z-40 w-full bg-white/90 backdrop-blur-md border-b border-slate-200/80 shadow-xs">
      {/* Gradient accent bar */}
      <div className="h-0.5 w-full bg-gradient-to-r from-blue-600 via-teal-500 to-indigo-600" />

      {/* Header Body */}
      <div className="max-w-6xl mx-auto flex items-center justify-between px-4 sm:px-6 py-2.5 sm:py-3 gap-3">
        {/* Left: Brand + Title */}
        <div className="flex items-center gap-3 min-w-0">
          <Link href={isSessionActive ? "/session" : "/"} className="shrink-0 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-teal-500 flex items-center justify-center p-2 shadow-xs group-hover:scale-105 transition-transform">
              <Image
                src="/logo-white.png"
                alt="MediPlatform"
                width={26}
                height={26}
                className="w-full h-full object-contain"
              />
            </div>
          </Link>

          {title ? (
            <div className="min-w-0">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none">
                MediPlatform
              </p>
              <h1 className="text-base sm:text-lg font-extrabold text-slate-900 leading-tight truncate">
                {title}
              </h1>
              {subtitle && (
                <p className="text-[11px] text-slate-500 truncate hidden sm:block">{subtitle}</p>
              )}
            </div>
          ) : (
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none">
                MediPlatform
              </p>
              <h1 className="text-base sm:text-lg font-extrabold text-slate-900 leading-tight">
                Patient Kiosk
              </h1>
            </div>
          )}
        </div>

        {/* Center: Navigation Pills (when in active session) */}
        {shouldRenderNav && (
          <nav className="hidden md:flex items-center gap-1.5 bg-slate-100/90 p-1 rounded-2xl border border-slate-200">
            <Link
              href="/session"
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                pathname === "/session"
                  ? "bg-white text-blue-700 shadow-xs border border-slate-200/60"
                  : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
              }`}
            >
              <Home size={14} />
              <span>Home</span>
            </Link>

            <Link
              href="/profile"
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                pathname === "/profile"
                  ? "bg-white text-blue-700 shadow-xs border border-slate-200/60"
                  : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
              }`}
            >
              <User size={14} />
              <span>Profile</span>
            </Link>

            <Link
              href="/history"
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                pathname === "/history"
                  ? "bg-white text-blue-700 shadow-xs border border-slate-200/60"
                  : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
              }`}
            >
              <FileClock size={14} />
              <span>Medical History</span>
            </Link>
          </nav>
        )}

        {/* Right: Patient Name / Status + Actions */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {patientName && (
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-blue-50/70 border border-blue-200/60 rounded-xl">
              <span className="w-2 h-2 rounded-full bg-blue-600" />
              <span className="text-xs font-bold text-blue-900 truncate max-w-[140px]">{patientName}</span>
            </div>
          )}

          {/* Custom right content if provided */}
          {rightContent ? (
            rightContent
          ) : isSessionActive ? (
            <button
              onClick={resetSession}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-rose-50 text-slate-600 hover:text-rose-700 text-xs font-semibold border border-slate-200 transition-colors"
              title="Logout and reset session"
            >
              <LogOut size={14} />
              <span className="hidden sm:inline">Exit Kiosk</span>
            </button>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wide">Live</span>
            </div>
          )}
        </div>
      </div>

      {/* Mobile Sub-Navigation Bar for touch screens */}
      {shouldRenderNav && (
        <div className="md:hidden flex items-center justify-around border-t border-slate-200/60 bg-slate-50/90 px-2 py-1.5">
          <Link
            href="/session"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold ${
              pathname === "/session" ? "bg-white text-blue-700 shadow-xs border border-slate-200" : "text-slate-600"
            }`}
          >
            <Home size={14} />
            <span>Home</span>
          </Link>
          <Link
            href="/profile"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold ${
              pathname === "/profile" ? "bg-white text-blue-700 shadow-xs border border-slate-200" : "text-slate-600"
            }`}
          >
            <User size={14} />
            <span>Profile</span>
          </Link>
          <Link
            href="/history"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold ${
              pathname === "/history" ? "bg-white text-blue-700 shadow-xs border border-slate-200" : "text-slate-600"
            }`}
          >
            <FileClock size={14} />
            <span>History</span>
          </Link>
        </div>
      )}
    </header>
  );
}
