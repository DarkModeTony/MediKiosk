"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { generateSummary, getSummary, ClinicalSummary } from "@/lib/api/summaries";
import {
  Loader2,
  FileText,
  AlertTriangle,
  ShieldCheck,
  Home,
  ChevronDown,
  ChevronUp,
  Sparkles,
  CheckCircle2,
} from "lucide-react";

export default function SummaryPreviewPage() {
  const router = useRouter();
  const { session } = useKiosk();
  const [summary, setSummary] = useState<ClinicalSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  useEffect(() => {
    if (!session) { router.replace("/"); return; }

    async function fetchOrGenerate() {
      try {
        // Use actual encounter ID from session, or fall back to demo encounter
        const encId = session?.encounterId || "7c245014-b38e-42e6-a421-dbfb1f2a6398";
        try {
          const res = await getSummary(encId);
          setSummary(res.latest_version);
        } catch {
          await generateSummary(encId);
          const res2 = await getSummary(encId);
          setSummary(res2.latest_version);
        }
      } catch (err: unknown) {
        const e = err as Error;
        setError(e.message || "Failed to load summary");
      } finally {
        setLoading(false);
      }
    }
    fetchOrGenerate();
  }, [session, router]);

  const toggleSection = (i: number) =>
    setExpanded((e) => ({ ...e, [i]: !e[i] }));

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 gap-6">
        <div className="relative">
          <div className="w-20 h-20 rounded-full border-4 border-blue-500/30 border-t-blue-400 animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <Sparkles className="w-8 h-8 text-blue-400 animate-pulse" />
          </div>
        </div>
        <div className="text-center">
          <p className="text-blue-200 font-bold text-xl">Generating AI Clinical Summary…</p>
          <p className="text-blue-400/60 text-sm mt-2">Powered by Gemini AI</p>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center p-12">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <p className="text-xl font-bold text-slate-700">Could not load summary</p>
          <p className="text-slate-500 mt-2">{error}</p>
          <button onClick={() => router.push("/")} className="mt-6 px-6 py-3 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800 transition">
            Return Home
          </button>
        </div>
      </div>
    );
  }

  const redFlagSection = summary.structured_sections?.find((s) =>
    s.title?.toLowerCase().includes("red flag")
  );
  const hasRedFlags = redFlagSection?.content && redFlagSection.content !== "None identified";

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50/20 to-white relative overflow-hidden">
      <div className="pointer-events-none absolute -top-40 right-0 w-[500px] h-[500px] rounded-full bg-blue-400/10 blur-3xl" />
      <AppHeader title="Visit Summary Preview" subtitle="AI-Generated Draft" />

      <main className="relative flex-1 max-w-6xl mx-auto w-full p-6 md:p-8 grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in">

        {/* Summary Sections */}
        <div className="lg:col-span-2 space-y-4">
          {/* Status banner */}
          <div className={`flex items-center gap-3 px-5 py-3.5 rounded-2xl border font-semibold text-sm ${
            summary.status === 'AI_DRAFT'
              ? 'bg-amber-50 border-amber-200 text-amber-800'
              : 'bg-emerald-50 border-emerald-200 text-emerald-800'
          }`}>
            <Sparkles className="w-4 h-4 shrink-0" />
            <span>
              This is an <strong>AI-Generated Draft Summary</strong>. Your doctor will review and verify all information before your consultation.
            </span>
            <span className={`ml-auto px-2.5 py-0.5 rounded-full text-xs font-bold border ${
              summary.status === 'AI_DRAFT' ? 'bg-amber-100 text-amber-800 border-amber-200' : 'bg-emerald-100 text-emerald-800 border-emerald-200'
            }`}>
              {summary.status}
            </span>
          </div>

          {/* Sections as accordions */}
          <div className="space-y-3">
            {summary.structured_sections?.map((sec, i) => (
              <div key={i} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <button
                  onClick={() => toggleSection(i)}
                  className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center">
                      <FileText className="w-4 h-4 text-blue-600" />
                    </div>
                    <h3 className="font-bold text-slate-900 text-sm uppercase tracking-wider">{sec.title}</h3>
                  </div>
                  {expanded[i] ? (
                    <ChevronUp className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  )}
                </button>
                {expanded[i] && (
                  <div className="px-6 pb-5 border-t border-slate-100">
                    <p className="text-slate-700 whitespace-pre-line leading-relaxed text-base mt-4">
                      {sec.content || "Not documented"}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Right panel */}
        <div className="space-y-4">
          {/* Red Flags */}
          {hasRedFlags ? (
            <div className="p-5 rounded-2xl bg-red-50 border border-red-200 shadow-sm">
              <h3 className="font-bold text-red-800 flex items-center gap-2 mb-3 text-sm">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                RED FLAGS DETECTED
              </h3>
              <p className="text-red-700 font-medium text-sm whitespace-pre-line leading-relaxed">
                {redFlagSection?.content}
              </p>
            </div>
          ) : (
            <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 shadow-sm">
              <h3 className="font-bold text-emerald-800 flex items-center gap-2 text-sm">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                No Red Flags Detected
              </h3>
              <p className="text-emerald-600 text-xs mt-1">No critical symptoms reported during intake.</p>
            </div>
          )}

          {/* Provenance */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
            <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-3 text-sm">
              <ShieldCheck className="w-4 h-4 text-teal-600" />
              Source Provenance
            </h3>
            <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
              {summary.source_references && summary.source_references.length > 0 ? (
                summary.source_references.map((ref, i) => (
                  <div key={i} className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider block mb-1">{ref.source_type}</span>
                    <p className="text-sm text-slate-800 font-medium leading-snug">{ref.fact}</p>
                    {ref.source_text && (
                      <p className="text-xs text-slate-400 mt-1.5 font-mono bg-slate-100 rounded px-2 py-1">
                        {ref.source_text}
                      </p>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-slate-400 italic text-sm">No specific sources referenced.</p>
              )}
            </div>
          </div>

          {/* Return Home */}
          <button
            onClick={() => router.push("/")}
            className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-200 transition-all"
          >
            <Home className="w-4 h-4" />
            Return to Home
          </button>
        </div>

      </main>
    </div>
  );
}
