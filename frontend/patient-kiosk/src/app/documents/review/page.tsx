"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { LargeTouchButton } from "@/components/shared/LargeTouchButton";
import { getDocumentEntities, confirmDocument, DocumentEntity } from "@/lib/api/documents";

function ReviewContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const documentId = searchParams.get("id");
  const [entities, setEntities] = useState<DocumentEntity[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!documentId) return;
    try {
      const data = await getDocumentEntities(documentId);
      setEntities(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    if (!documentId) {
      router.replace("/documents");
      return;
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadData();
  }, [documentId, router, loadData]);

  const handleConfirm = async () => {
    if (!documentId) return;
    // For MVP, we confirm everything as is
    // A full correction UI would build the payload here
    const payload = entities.map(e => ({
      entity_id: e.id,
      corrected_value: e.value,
      status: "PATIENT_CORRECTED"
    }));
    await confirmDocument(documentId, payload);
    router.push("/session"); // Done!
  };

  if (loading) return <div className="p-8 text-2xl">Loading review...</div>;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader title="Review Extraction" />
      <main className="flex-1 p-8 max-w-6xl mx-auto w-full gap-8 grid grid-cols-1 md:grid-cols-2">
        <div className="space-y-6">
          <h2 className="text-3xl font-bold text-brand-navy">Extracted Information</h2>
          <p className="text-lg text-muted-foreground">
            Please review the medical information we found. If anything is incorrect, you can adjust it below.
          </p>
          
          {entities.map(ent => (
            <div key={ent.id} className={`p-6 rounded-2xl border-2 ${
              ent.type === "LAB_RESULT" && ent.value?.abnormal_flag 
                ? "bg-red-50 border-red-200" 
                : "bg-white border-border"
            }`}>
              <div className="flex justify-between items-start mb-4">
                <span className="text-sm font-bold text-primary uppercase tracking-wider">{ent.type}</span>
                {ent.status === "AI_EXTRACTED" && (
                  <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded">AI EXTRACTED</span>
                )}
              </div>
              
              {ent.type === "MEDICATION" && (
                <div>
                  <h3 className="text-2xl font-bold text-brand-navy">{ent.value.name}</h3>
                  <p className="text-xl text-slate-600">{ent.value.strength} {ent.value.frequency}</p>
                </div>
              )}

              {ent.type === "DIAGNOSIS" && (
                <div>
                  <h3 className="text-2xl font-bold text-brand-navy">{ent.value.diagnosis}</h3>
                </div>
              )}

              {ent.type === "LAB_RESULT" && (
                <div>
                  <h3 className="text-2xl font-bold text-brand-navy flex items-center gap-2">
                    {ent.value.test_name}
                    {ent.value.abnormal_flag && (
                      <span className="text-xs bg-red-500 text-white px-2 py-1 rounded uppercase">Abnormal</span>
                    )}
                  </h3>
                  <p className="text-xl text-slate-600">
                    {ent.value.value} {ent.value.unit}
                    <span className="text-base text-muted-foreground block mt-1">
                      Ref: {ent.value.reference_low} - {ent.value.reference_high}
                    </span>
                  </p>
                </div>
              )}
              
              <div className="mt-4 p-4 bg-slate-50 rounded-xl text-sm font-mono text-muted-foreground">
                Source: {ent.source_text}
              </div>
            </div>
          ))}
        </div>
        
        <div className="bg-white p-12 rounded-3xl shadow-sm border border-border flex flex-col justify-center text-center space-y-8 h-fit sticky top-8">
          <h3 className="text-3xl font-bold text-brand-navy">Look correct?</h3>
          <p className="text-xl text-muted-foreground">
            This information will be added to your timeline for the doctor to review.
          </p>
          <LargeTouchButton onClick={handleConfirm} className="shadow-lg shadow-primary/20">
            Confirm & Continue
          </LargeTouchButton>
        </div>
      </main>
    </div>
  );
}

export default function DocumentReviewPage() {
  return (
    <React.Suspense fallback={<div className="p-8 text-2xl">Loading review...</div>}>
      <ReviewContent />
    </React.Suspense>
  );
}
