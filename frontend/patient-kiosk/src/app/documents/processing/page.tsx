"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { getDocumentDetails } from "@/lib/api/documents";
import { Loader2 } from "lucide-react";

function ProcessingContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const documentId = searchParams.get("id");
  const [status, setStatus] = useState("PROCESSING");

  useEffect(() => {
    if (!documentId) {
      router.replace("/documents");
      return;
    }

    const interval = setInterval(async () => {
      try {
        const details = await getDocumentDetails(documentId);
        setStatus(details.status);
        if (details.status === "COMPLETED") {
          clearInterval(interval);
          router.push(`/documents/review?id=${documentId}`);
        } else if (details.status === "FAILED") {
          clearInterval(interval);
        }
      } catch (e) {
        console.error(e);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [documentId, router]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader title="Processing Document" />
      <main className="flex-1 flex items-center justify-center p-8">
        <div className="bg-white p-16 rounded-3xl shadow-sm border border-border w-full max-w-2xl text-center space-y-8">
          <Loader2 className="w-24 h-24 animate-spin text-primary mx-auto" />
          <h2 className="text-4xl font-bold text-brand-navy">Reading Document</h2>
          <p className="text-2xl text-muted-foreground">
            {status === "FAILED" 
              ? "Failed to process document. Please try again."
              : "Our AI is extracting medical information from your upload..."}
          </p>
          {status === "FAILED" && (
            <button 
              onClick={() => router.push("/documents")}
              className="mt-8 py-4 px-8 rounded-xl bg-primary text-white text-xl font-bold"
            >
              Go Back
            </button>
          )}
        </div>
      </main>
    </div>
  );
}

export default function DocumentProcessingPage() {
  return (
    <Suspense fallback={<div className="p-8 text-2xl">Loading...</div>}>
      <ProcessingContent />
    </Suspense>
  );
}
