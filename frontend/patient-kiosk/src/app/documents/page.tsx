"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { AppHeader } from "@/components/shared/AppHeader";
import { StatusMessage } from "@/components/shared/StatusMessage";
import { LargeTouchButton } from "@/components/shared/LargeTouchButton";
import { uploadDocument, triggerOCR } from "@/lib/api/documents";
import {
  UploadCloud,
  FileText,
  Image,
  FlaskConical,
  FileHeart,
  ArrowRight,
  ChevronLeft,
  Check,
} from "lucide-react";

const DOC_TYPES = [
  { id: "PRESCRIPTION", label: "Prescription", icon: FileText, color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-200", activeBorder: "border-blue-600 bg-blue-50", desc: "Doctor-written medicine list" },
  { id: "LAB_REPORT", label: "Lab Report", icon: FlaskConical, color: "text-teal-600", bg: "bg-teal-50", border: "border-teal-200", activeBorder: "border-teal-600 bg-teal-50", desc: "Blood tests, urine, pathology" },
  { id: "DISCHARGE_SUMMARY", label: "Discharge Summary", icon: FileHeart, color: "text-purple-600", bg: "bg-purple-50", border: "border-purple-200", activeBorder: "border-purple-600 bg-purple-50", desc: "Hospital stay record" },
  { id: "OTHER", label: "Other Document", icon: Image, color: "text-slate-600", bg: "bg-slate-50", border: "border-slate-200", activeBorder: "border-slate-600 bg-slate-50", desc: "X-ray, scan, or other" },
];

export default function DocumentUploadPage() {
  const router = useRouter();
  const { session } = useKiosk();
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState("PRESCRIPTION");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);

  if (!session) {
    if (typeof window !== "undefined") router.replace("/");
    return null;
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) setFile(e.target.files[0]);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const res = await uploadDocument(file, docType, session.sessionId);
      triggerOCR(res.document_id).catch(console.error);
      router.push(`/documents/processing?id=${res.document_id}`);
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || "Failed to upload file");
      setLoading(false);
    }
  };

  const selectedType = DOC_TYPES.find((t) => t.id === docType)!;

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50/20 to-white relative overflow-hidden">
      <div className="pointer-events-none absolute -top-40 -right-40 w-[400px] h-[400px] rounded-full bg-teal-400/10 blur-3xl" />

      <AppHeader title="Previous Medical Records" />

      <main className="relative flex-1 flex flex-col items-center justify-center p-6 md:p-10 max-w-4xl mx-auto w-full">
        <div className="w-full bg-white/90 backdrop-blur-sm p-8 md:p-12 rounded-3xl shadow-sm border border-slate-200 space-y-8 animate-fade-in">

          {/* Heading */}
          <div className="text-center space-y-2">
            <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-teal-500 rounded-2xl flex items-center justify-center mx-auto shadow-lg shadow-blue-500/25">
              <UploadCloud className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-3xl md:text-4xl font-black text-slate-900">Upload a Document</h1>
            <p className="text-lg text-slate-500">
              Do you have a previous prescription or laboratory report? Tap to upload.
            </p>
          </div>

          {error && <StatusMessage message={error} type="error" />}

          {/* Drop Zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`relative flex flex-col items-center gap-5 p-10 border-2 border-dashed rounded-2xl transition-all duration-300 ${
              dragOver
                ? "border-blue-500 bg-blue-50/80 scale-[1.01]"
                : file
                ? "border-emerald-400 bg-emerald-50/50"
                : "border-slate-300 bg-slate-50/50 hover:border-blue-400 hover:bg-blue-50/30"
            }`}
          >
            <input
              type="file"
              id="file-upload"
              accept=".jpg,.jpeg,.png,.pdf"
              className="hidden"
              onChange={handleFileChange}
            />

            <label htmlFor="file-upload" className="flex flex-col items-center gap-4 cursor-pointer w-full">
              <div className={`w-24 h-24 rounded-2xl flex items-center justify-center shadow-sm transition-all ${
                file ? "bg-emerald-100 text-emerald-600" : "bg-white text-blue-600 border border-slate-200"
              }`}>
                {file ? <Check size={48} strokeWidth={2.5} /> : <UploadCloud size={48} />}
              </div>

              {file ? (
                <div className="text-center space-y-1">
                  <p className="text-xl font-bold text-emerald-700">{file.name}</p>
                  <p className="text-sm text-slate-400">{(file.size / 1024).toFixed(0)} KB • Tap to change</p>
                </div>
              ) : (
                <div className="text-center space-y-1">
                  <p className="text-2xl font-bold text-slate-700">Tap to browse or drag here</p>
                  <p className="text-base text-slate-400">Supports JPG, PNG, PDF · Max 10 MB</p>
                </div>
              )}
            </label>
          </div>

          {/* Document Type */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-slate-800">Document Type</h2>
            <div className="grid grid-cols-2 gap-3">
              {DOC_TYPES.map(({ id, label, icon: Icon, color, border, activeBorder, desc }) => (
                <button
                  key={id}
                  onClick={() => setDocType(id)}
                  className={`flex items-center gap-4 p-5 border-2 rounded-2xl text-left transition-all duration-200 active:scale-[0.99] ${
                    docType === id ? activeBorder : `${border} bg-white hover:border-slate-300`
                  }`}
                >
                  <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${docType === id ? "bg-white shadow-sm" : "bg-slate-100"}`}>
                    <Icon className={`w-6 h-6 ${color}`} />
                  </div>
                  <div>
                    <p className={`font-bold text-base ${docType === id ? "text-slate-900" : "text-slate-600"}`}>{label}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{desc}</p>
                  </div>
                  {docType === id && (
                    <div className="ml-auto">
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center ${color.replace("text-", "bg-").replace("600", "100")}`}>
                        <Check className={`w-3 h-3 ${color}`} />
                      </div>
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4 pt-4 border-t border-slate-100">
            <LargeTouchButton
              variant="outline"
              onClick={() => router.push("/session")}
              className="flex-1 py-5 text-base gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              Skip
            </LargeTouchButton>
            <LargeTouchButton
              variant="primary"
              onClick={handleUpload}
              disabled={!file}
              loading={loading}
              className="flex-[2] py-5 text-xl font-extrabold gap-3"
            >
              Upload {selectedType.label}
              <ArrowRight className="w-5 h-5" />
            </LargeTouchButton>
          </div>
        </div>
      </main>
    </div>
  );
}
