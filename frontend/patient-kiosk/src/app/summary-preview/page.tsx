"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { generateSummary, getSummary, ClinicalSummary } from "@/lib/api/summaries";
import { Loader2, FileText, AlertTriangle, ShieldCheck } from "lucide-react";

export default function SummaryPreviewPage() {
  const router = useRouter();
  const { session } = useKiosk();
  const [summary, setSummary] = useState<ClinicalSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!session) {
      router.replace("/");
      return;
    }

    async function fetchOrGenerate() {
      try {
        if (!session || !session.encounterId) return;
        // Try getting existing
        try {
          const res = await getSummary(session.encounterId as string);
          setSummary(res.latest_version);
        } catch (e) {
          // generate if not exists
          await generateSummary(session.encounterId as string);
          const res2 = await getSummary(session.encounterId as string);
          setSummary(res2.latest_version);
        }
      } catch (err: unknown) {
        const e = err as Error;
        setError(e.message || "Failed to load summary");
      } finally {
        setLoading(false);
      }
    }
    
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchOrGenerate();
  }, [session, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="w-12 h-12 animate-spin text-primary" />
        <span className="ml-4 text-2xl text-slate-600">Generating AI Draft...</span>
      </div>
    );
  }

  if (error || !summary) {
    return <div className="p-8 text-red-500">Error: {error}</div>;
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-100">
      <AppHeader title="Physician Summary Preview (Dev Mode)" />
      
      <main className="flex-1 max-w-7xl mx-auto w-full p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Col - Summary */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-border">
            <div className="flex justify-between items-center mb-8 pb-4 border-b">
              <h2 className="text-3xl font-bold text-brand-navy flex items-center gap-3">
                <FileText className="text-primary" />
                Clinical Summary Draft
              </h2>
              <span className={`px-4 py-2 rounded-full text-sm font-bold tracking-widest ${summary.status === 'AI_DRAFT' ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'}`}>
                {summary.status}
              </span>
            </div>

            <div className="space-y-8">
              {summary.structured_sections.map((sec, i) => (
                <div key={i} className="space-y-2">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest">{sec.title}</h3>
                  <div className="text-lg text-slate-800 whitespace-pre-line leading-relaxed">
                    {sec.content || "Not documented"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col - Provenance & Red Flags */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-red-200 bg-red-50/30">
            <h3 className="text-xl font-bold text-brand-navy flex items-center gap-2 mb-4">
              <AlertTriangle className="text-red-500" />
              Red Flags
            </h3>
            {summary.structured_sections.find(s => s.title.includes("RED FLAGS"))?.content === "None identified" ? (
              <p className="text-slate-500 italic">No red flags detected.</p>
            ) : (
              <div className="text-red-700 font-medium whitespace-pre-line">
                {summary.structured_sections.find(s => s.title.includes("RED FLAGS"))?.content}
              </div>
            )}
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-border">
            <h3 className="text-xl font-bold text-brand-navy flex items-center gap-2 mb-4">
              <ShieldCheck className="text-emerald-500" />
              Source Provenance
            </h3>
            <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
              {summary.source_references && summary.source_references.length > 0 ? summary.source_references.map((ref, i) => (
                <div key={i} className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-xs font-bold text-primary block mb-1">{ref.source_type}</span>
                  <p className="text-sm text-slate-700 font-medium">{ref.fact}</p>
                  {ref.source_text && (
                    <p className="text-xs text-slate-400 mt-2 font-mono">Original: {ref.source_text}</p>
                  )}
                </div>
              )) : (
                <p className="text-slate-500 italic text-sm">No specific sources referenced.</p>
              )}
            </div>
          </div>
          
          <button onClick={() => router.push("/")} className="w-full py-4 rounded-xl font-bold bg-slate-200 text-slate-700 hover:bg-slate-300">
            Return to Home
          </button>
        </div>

      </main>
    </div>
  );
}
