import React, { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp, ShieldAlert, Info, Lock } from 'lucide-react';
import { RedFlag } from '@/lib/api/types';

interface RedFlagPanelProps {
  flags: RedFlag[];
}

const SEVERITY_CONFIG = {
  HIGH: {
    bg: 'from-red-700 to-red-600',
    badgeBg: 'bg-red-900/60 border-red-500/60 text-red-200',
    cardBg: 'bg-red-900/30 border-red-500/40',
    icon: ShieldAlert,
    pulse: true,
  },
  MEDIUM: {
    bg: 'from-amber-600 to-amber-500',
    badgeBg: 'bg-amber-900/60 border-amber-500/60 text-amber-200',
    cardBg: 'bg-amber-900/20 border-amber-500/40',
    icon: AlertTriangle,
    pulse: false,
  },
};

export default function RedFlagPanel({ flags }: RedFlagPanelProps) {
  const [expanded, setExpanded] = useState(true);

  if (!flags || flags.length === 0) return null;

  const hasHigh = flags.some((f) => f.severity === 'HIGH');
  const cfg = hasHigh ? SEVERITY_CONFIG.HIGH : SEVERITY_CONFIG.MEDIUM;

  return (
    <div className={`rounded-2xl overflow-hidden shadow-lg animate-fade-in`}>
      {/* Header bar */}
      <button
        onClick={() => setExpanded((e) => !e)}
        className={`w-full flex items-center justify-between px-6 py-4 bg-gradient-to-r ${cfg.bg} text-white`}
      >
        <div className="flex items-center gap-3">
          {cfg.pulse && (
            <div className="relative">
              <div className="absolute inset-0 w-8 h-8 rounded-full bg-white/20 animate-ping" />
              <div className="relative w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                <cfg.icon className="w-5 h-5 text-white" />
              </div>
            </div>
          )}
          {!cfg.pulse && <cfg.icon className="w-6 h-6 text-white" />}
          <div className="text-left">
            <p className="font-black text-base tracking-tight">
              {hasHigh ? 'CRITICAL CLINICAL ALERTS' : 'CLINICAL ALERTS'}
            </p>
            <p className="text-xs text-white/70 mt-0.5">
              {flags.length} flag{flags.length !== 1 ? 's' : ''} detected · Doctor review required
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-white/20 border border-white/30">
            {flags.length} Alert{flags.length !== 1 ? 's' : ''}
          </span>
          {expanded ? <ChevronUp className="w-5 h-5 text-white/70" /> : <ChevronDown className="w-5 h-5 text-white/70" />}
        </div>
      </button>

      {/* Flags list */}
      {expanded && (
        <div className="bg-slate-900 border-x border-b border-slate-700 p-4 space-y-3">
          {flags.map((flag, idx) => {
            const severityCfg = SEVERITY_CONFIG[flag.severity as keyof typeof SEVERITY_CONFIG] || SEVERITY_CONFIG.MEDIUM;
            return (
              <div
                key={idx}
                className={`flex items-start gap-4 p-4 rounded-xl border ${severityCfg.cardBg}`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${severityCfg.badgeBg} border`}>
                  <severityCfg.icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="font-bold text-slate-100 text-sm">
                      {flag.rule_name.replace(/_/g, ' ')}
                    </h4>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${severityCfg.badgeBg}`}>
                      {flag.severity}
                    </span>
                  </div>
                  {flag.evidence && Object.keys(flag.evidence).length > 0 && (
                    <div className="flex items-start gap-1.5 mt-1.5">
                      <Info className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                      <p className="text-xs text-slate-400 leading-relaxed">
                        Evidence: {Object.values(flag.evidence).join(' · ')}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Authoritative notice */}
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700">
            <Lock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <p className="text-[10px] text-slate-500 italic">
              Red flags are deterministically calculated by the backend clinical engine. Read-only.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
