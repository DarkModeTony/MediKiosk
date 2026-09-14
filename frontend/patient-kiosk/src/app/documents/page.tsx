"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { AppHeader } from "@/components/shared/AppHeader";
import { StatusMessage } from "@/components/shared/StatusMessage";
import { uploadDocument, triggerOCR } from "@/lib/api/documents";
import { UploadCloud, FileText } from "lucide-react";

export default function DocumentUploadPage() {
  const router = useRouter();
  const { session } = useKiosk();
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState("PRESCRIPTION");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!session) {
    if (typeof window !== "undefined") router.replace("/");
    return null;
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const res = await uploadDocument(file, docType, session.sessionId);
      const documentId = res.document_id;
      // Kick off processing
      triggerOCR(documentId).catch(console.error);
      router.push(`/documents/processing?id=${documentId}`);
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || "Failed to upload file");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader title="Previous Medical Records" />
      <main className="flex-1 flex flex-col items-center justify-center p-8 max-w-4xl mx-auto w-full gap-8">
        <div className="bg-white p-12 rounded-3xl shadow-sm border border-border w-full space-y-8">
          <div className="text-center">
            <h2 className="text-4xl font-bold text-brand-navy">Upload a Document</h2>
            <p className="text-xl text-muted-foreground mt-4">
              Do you have a previous prescription or laboratory report?
            </p>
          </div>
          
          {error && <StatusMessage message={error} type="error" />}

          <div className="flex flex-col items-center gap-6 p-8 border-4 border-dashed border-primary/20 rounded-2xl bg-primary/5">
            <input
              type="file"
              id="file-upload"
              accept=".jpg,.jpeg,.png,.pdf"
              className="hidden"
              onChange={handleFileChange}
            />
            <label 
              htmlFor="file-upload"
              className="flex flex-col items-center gap-4 cursor-pointer"
            >
              <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center text-primary shadow-sm border border-border">
                {file ? <FileText size={48} /> : <UploadCloud size={48} />}
              </div>
              <span className="text-2xl font-medium text-brand-navy">
                {file ? file.name : "Tap to browse files"}
              </span>
              <span className="text-lg text-muted-foreground">
                Supports JPG, PNG, PDF (Max 10MB)
              </span>
            </label>
          </div>

          <div className="space-y-4">
            <label className="text-xl font-bold text-brand-navy">Document Type</label>
            <div className="grid grid-cols-2 gap-4">
              {["PRESCRIPTION", "LAB_REPORT", "DISCHARGE_SUMMARY", "OTHER"].map(type => (
                <button
                  key={type}
                  onClick={() => setDocType(type)}
                  className={`p-6 border-2 rounded-2xl text-xl font-semibold transition-all ${
                    docType === type 
                      ? "border-primary bg-primary/5 text-primary" 
                      : "border-border bg-white text-muted-foreground hover:border-primary/50"
                  }`}
                >
                  {type.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>

          <div className="pt-8 flex gap-4">
            <button 
              onClick={() => router.push("/session")} 
              className="flex-1 py-6 px-8 rounded-2xl text-2xl font-bold bg-slate-200 text-slate-700 hover:bg-slate-300 transition-colors"
            >
              Skip
            </button>
            <button 
              onClick={handleUpload}
              disabled={!file || loading}
              className="flex-1 py-6 px-8 rounded-2xl text-2xl font-bold bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {loading ? "Uploading..." : "Upload & Continue"}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
