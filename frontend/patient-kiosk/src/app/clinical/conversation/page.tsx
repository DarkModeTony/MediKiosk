"use client";

import React, { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { AppHeader } from "@/components/shared/AppHeader";
import { StatusMessage } from "@/components/shared/StatusMessage";
import {
  getClinicalState,
  submitClinicalAnswer,
  getQuestionDetails,
  ClinicalState,
  Question,
} from "@/lib/api/clinical";
import { transcribeVoice } from "@/lib/api/voice";
import {
  Mic,
  MicOff,
  AlertTriangle,
  Loader2,
  Sparkles,
  Languages,
  Check,
  RotateCcw,
  Send,
  Stethoscope,
  ShieldAlert,
  ChevronRight,
} from "lucide-react";

// ── Waveform animation component ─────────────────────────────────────────────
function VoiceWaveform({ active }: { active: boolean }) {
  if (!active) return null;
  return (
    <div className="flex items-center gap-[3px] h-10">
      {[1, 2, 3, 4, 5, 6, 7].map((i) => (
        <div
          key={i}
          className="waveform-bar w-1.5 rounded-full bg-white/80"
          style={{
            height: `${20 + Math.sin(i) * 18}px`,
            animationDelay: `${(i - 1) * 0.1}s`,
          }}
        />
      ))}
    </div>
  );
}

export default function ClinicalConversationPage() {
  const router = useRouter();
  const { session } = useKiosk();

  const [state, setState] = useState<ClinicalState | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [questionKey, setQuestionKey] = useState(0);

  // Voice states
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [detectedLang, setDetectedLang] = useState("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const loadState = useCallback(async () => {
    if (!session) return;
    try {
      const s = await getClinicalState(session.sessionId);
      setState(s);

      if (s.completed) {
        router.push("/clinical/review");
        return;
      }

      if (s.current_question_id === "chief_complaint_initial") {
        setQuestion({
          id: "chief_complaint_initial",
          text: "What brings you here today?",
          category: "HPI",
          input_type: "VOICE_ONLY",
          clinical_field: "chief_complaint",
          options: null,
          required: true,
        });
      } else if (s.current_pathway && s.current_question_id) {
        const q = await getQuestionDetails(s.current_pathway, s.current_question_id);
        setQuestion(q);
      }
      setQuestionKey((k) => k + 1);
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || "Failed to load interview state.");
    } finally {
      setLoading(false);
    }
  }, [session, router]);

  useEffect(() => {
    if (!session) {
      router.replace("/session");
      return;
    }
    loadState();
  }, [session, router, loadState]);

  // ── Recording ──────────────────────────────────────────────────────────────

  const startRecording = async () => {
    setError("");
    setTranscript("");
    setDetectedLang("");
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "";

      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const audioBlob = new Blob(chunksRef.current, { type: mimeType || "audio/webm" });

        if (!chunksRef.current.length || audioBlob.size < 200) {
          setIsTranscribing(false);
          setError("No audio captured. Tap the mic, speak clearly, then tap again to stop.");
          return;
        }
        await sendToSarvam(audioBlob);
      };

      recorder.start(250);
      setIsRecording(true);
    } catch {
      setError("Microphone access denied. Please allow microphone permissions and try again.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      try { mediaRecorderRef.current.requestData(); } catch (_e) { /* ignore */ }
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    setIsTranscribing(true);
  };

  const sendToSarvam = async (audioBlob: Blob) => {
    try {
      const result = await transcribeVoice(audioBlob);
      if (!result.transcript?.trim()) {
        setError("Could not clearly hear speech. Please speak closer to your microphone.");
      } else {
        setTranscript(result.transcript);
        setDetectedLang(result.detected_language);
        setError("");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Voice transcription failed.";
      setError(msg);
    } finally {
      setIsTranscribing(false);
    }
  };

  const handleMicToggle = () => {
    if (isRecording) stopRecording();
    else startRecording();
  };

  // ── Submission ─────────────────────────────────────────────────────────────

  const handleVoiceSubmit = async () => {
    if (!session || !question || !transcript.trim()) return;
    setLoading(true);
    const answer = transcript.trim();
    setTranscript("");
    setDetectedLang("");
    try {
      await submitClinicalAnswer(session.sessionId, {
        question_id: question.id,
        raw_transcript: answer,
      });
      await loadState();
    } catch {
      setError("Failed to submit answer. Please try again.");
      setLoading(false);
    }
  };

  const handleOptionSelect = async (optionId: string) => {
    if (!session || !question) return;
    setLoading(true);
    try {
      await submitClinicalAnswer(session.sessionId, {
        question_id: question.id,
        selected_option_id: optionId,
      });
      await loadState();
    } catch {
      setError("Failed to submit option.");
      setLoading(false);
    }
  };

  // ── Loading State ──────────────────────────────────────────────────────────

  if (!session || loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-900 to-blue-950 gap-6">
        <div className="relative">
          <div className="w-20 h-20 rounded-full border-4 border-blue-500/30 border-t-blue-400 animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <Stethoscope className="w-8 h-8 text-blue-400" />
          </div>
        </div>
        <p className="text-blue-200 font-semibold text-lg">Connecting to Clinical Assistant…</p>
      </div>
    );
  }

  const hasRedFlags = state?.new_red_flags && state.new_red_flags.length > 0;

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900">

      {/* Subtle background pattern */}
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full bg-blue-600/5 blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] rounded-full bg-teal-600/5 blur-3xl" />
      </div>

      {/* Header */}
      <div className="relative z-10 sticky top-0">
        <div className="h-0.5 w-full bg-gradient-to-r from-blue-500 via-teal-400 to-blue-500" />
        <div className="bg-slate-900/90 backdrop-blur-md border-b border-white/10">
          <div className="max-w-4xl mx-auto flex items-center justify-between px-5 py-3.5">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-teal-500 flex items-center justify-center shadow-sm">
                <Stethoscope className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-[11px] font-bold text-blue-400 uppercase tracking-widest">MediPlatform</p>
                <h1 className="text-base font-bold text-white">Clinical Assistant</h1>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-teal-900/50 border border-teal-700/50">
                <Sparkles className="w-3 h-3 text-teal-400" />
                <span className="text-[10px] font-bold text-teal-300 uppercase tracking-wide">Sarvam AI</span>
              </div>
              <button
                onClick={() => router.push("/session")}
                className="text-xs font-semibold text-slate-400 hover:text-white px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800/50 hover:bg-slate-700 transition-all"
              >
                Pause Intake
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Red Flag Banner */}
      {hasRedFlags && (
        <div className="relative z-10 bg-gradient-to-r from-red-700 to-red-600 text-white px-6 py-4 flex items-center shadow-lg animate-fade-in">
          <div className="flex items-center gap-3 max-w-4xl mx-auto w-full">
            <div className="w-10 h-10 rounded-full bg-red-900/50 flex items-center justify-center shrink-0">
              <ShieldAlert size={22} className="text-red-100" />
            </div>
            <div>
              <p className="font-black text-base">PRIORITY CLINICAL ALERT DETECTED</p>
              <p className="text-xs text-red-200 mt-0.5">
                Your reported symptoms have been flagged for immediate triage evaluation by the OPD doctor.
              </p>
            </div>
          </div>
        </div>
      )}

      <main className="relative z-10 flex-1 flex flex-col items-center justify-center p-4 md:p-8 max-w-4xl mx-auto w-full gap-6">

        {error && <StatusMessage message={error} type="error" />}

        {question && (
          <div key={questionKey} className="w-full space-y-5 animate-slide-up">

            {/* Question Category Badge */}
            <div className="flex items-center justify-between px-1">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-900/60 border border-blue-700/60 text-blue-300 rounded-full text-xs font-bold uppercase tracking-wider">
                <Stethoscope size={12} />
                {question.category || "General Intake"}
              </div>
              {detectedLang && (
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-900/50 border border-teal-700/50 text-teal-300 rounded-full text-xs font-semibold">
                  <Languages size={12} />
                  Detected: <strong>{detectedLang.toUpperCase()}</strong>
                </div>
              )}
            </div>

            {/* Question Card */}
            <div className="relative p-8 md:p-12 bg-white/5 backdrop-blur-sm rounded-3xl border border-white/10 text-center overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 to-teal-600/5" />
              <h2 className="relative text-3xl md:text-5xl font-extrabold text-white tracking-tight leading-tight">
                &ldquo;{question.text}&rdquo;
              </h2>
            </div>

            {/* Voice Input Card */}
            <div className="p-8 bg-white/5 backdrop-blur-sm rounded-3xl border border-white/10 flex flex-col items-center gap-6">

              {/* Mic Button with rings */}
              <div className="relative flex items-center justify-center">
                {isRecording && (
                  <>
                    <div className="absolute w-44 h-44 rounded-full bg-red-500/10 animate-ping" />
                    <div className="absolute w-36 h-36 rounded-full bg-red-500/15 animate-pulse" />
                  </>
                )}
                <button
                  onClick={handleMicToggle}
                  disabled={isTranscribing}
                  className={`relative w-28 h-28 md:w-32 md:h-32 rounded-full flex flex-col items-center justify-center transition-all duration-300 shadow-2xl active:scale-95 disabled:opacity-50 select-none ${
                    isRecording
                      ? "bg-gradient-to-br from-red-500 to-red-600 shadow-red-600/40 ring-8 ring-red-500/20 scale-105"
                      : isTranscribing
                      ? "bg-gradient-to-br from-amber-500 to-amber-600 shadow-amber-600/30 ring-8 ring-amber-500/20"
                      : "bg-gradient-to-br from-blue-500 to-blue-600 shadow-blue-600/30 ring-8 ring-blue-500/10 hover:scale-105 hover:shadow-blue-600/50"
                  }`}
                  aria-label={isRecording ? "Stop recording" : "Start recording"}
                >
                  {isTranscribing ? (
                    <Loader2 size={44} className="animate-spin text-white" />
                  ) : isRecording ? (
                    <>
                      <MicOff size={36} className="text-white" />
                      <VoiceWaveform active={isRecording} />
                    </>
                  ) : (
                    <Mic size={44} className="text-white" />
                  )}
                </button>
              </div>

              {/* Status Text */}
              <div className="text-center space-y-1.5">
                <p className="text-xl md:text-2xl font-bold text-white">
                  {isTranscribing
                    ? "Transcribing with Sarvam AI…"
                    : isRecording
                    ? "Listening… Tap again to stop"
                    : "Tap Microphone to Speak"}
                </p>
                <p className="text-sm text-blue-300/70">
                  Speak in Hindi, English, or any Indian regional language
                </p>
              </div>

              {/* Transcript Box */}
              {transcript && (
                <div className="w-full max-w-xl space-y-3 animate-slide-up">
                  <div className="p-5 bg-white/10 border border-white/20 rounded-2xl backdrop-blur-sm">
                    <label className="text-xs font-bold uppercase tracking-wider text-blue-300 block mb-2">
                      Your Spoken Answer · Tap to edit
                    </label>
                    <textarea
                      value={transcript}
                      onChange={(e) => setTranscript(e.target.value)}
                      rows={3}
                      className="w-full bg-transparent text-lg md:text-xl font-medium text-white outline-none resize-none placeholder:text-white/30"
                    />
                  </div>

                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => { setTranscript(""); setDetectedLang(""); }}
                      className="flex-1 py-3.5 px-4 rounded-xl border border-white/20 text-white/70 font-semibold hover:bg-white/10 transition flex items-center justify-center gap-2 text-base"
                    >
                      <RotateCcw size={15} />
                      Re-record
                    </button>
                    <button
                      type="button"
                      onClick={handleVoiceSubmit}
                      disabled={!transcript.trim()}
                      className="flex-[2] py-3.5 px-6 rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 text-white font-bold transition flex items-center justify-center gap-2 text-base shadow-lg shadow-blue-600/25 disabled:opacity-50"
                    >
                      <Check size={18} />
                      Confirm & Submit
                    </button>
                  </div>
                </div>
              )}

              {/* Text fallback */}
              {!transcript && !isRecording && !isTranscribing && (
                <div className="w-full max-w-xl pt-4 border-t border-white/10">
                  <p className="text-center text-xs text-white/40 mb-3 font-medium">
                    Prefer to type? Use the box below:
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={transcript}
                      onChange={(e) => setTranscript(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter" && transcript.trim()) handleVoiceSubmit(); }}
                      className="flex-1 p-4 border border-white/20 rounded-xl text-base outline-none focus:border-blue-400 bg-white/10 text-white placeholder:text-white/30 transition backdrop-blur-sm"
                      placeholder="Type your symptoms here…"
                    />
                    {transcript.trim() && (
                      <button
                        onClick={handleVoiceSubmit}
                        className="bg-blue-500 text-white px-5 py-3.5 rounded-xl text-sm font-bold flex items-center gap-1.5 shadow-sm hover:bg-blue-400 transition"
                      >
                        <Send size={16} />
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Quick-Touch Options */}
            {question.options && question.options.length > 0 && (
              <div className="space-y-3">
                <p className="text-xs font-bold text-white/40 uppercase tracking-wider text-center">
                  Or tap one of the options below:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {question.options.map((opt) => (
                    <button
                      key={opt.id}
                      onClick={() => handleOptionSelect(opt.id)}
                      className="p-5 bg-white/5 border border-white/15 hover:border-blue-400/60 hover:bg-blue-600/10 rounded-2xl text-lg font-bold text-white/90 hover:text-white transition-all text-left flex items-center justify-between group active:scale-[0.99] backdrop-blur-sm"
                    >
                      <span>{opt.label}</span>
                      <ChevronRight size={20} className="text-white/30 group-hover:text-blue-400 transition-colors" />
                    </button>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}

        {/* Error */}
        {!question && !loading && (
          <div className="text-center text-white/60 py-12">
            <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-amber-400" />
            <p className="text-xl font-semibold">Unable to load the next question.</p>
          </div>
        )}
      </main>
    </div>
  );
}
