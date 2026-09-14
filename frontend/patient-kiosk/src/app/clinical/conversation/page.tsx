"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { AppHeader } from "@/components/shared/AppHeader";
import { StatusMessage } from "@/components/shared/StatusMessage";
import { getClinicalState, submitClinicalAnswer, getQuestionDetails, ClinicalState, Question } from "@/lib/api/clinical";
import { Mic, MicOff, AlertTriangle } from "lucide-react";

export default function ClinicalConversationPage() {
  const router = useRouter();
  const { session } = useKiosk();
  
  const [state, setState] = useState<ClinicalState | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // Voice simulation states
  const [isListening, setIsListening] = useState(false);
  const [mockTranscript, setMockTranscript] = useState("");

  const loadState = useCallback(async () => {
    if (!session) return;
    try {
      const s = await getClinicalState(session.sessionId);
      setState(s);
      
      if (s.completed) {
        router.push("/clinical/review");
        return;
      }
      
      if (s.current_pathway && s.current_question_id) {
        const q = await getQuestionDetails(s.current_pathway, s.current_question_id);
        setQuestion(q);
      } else if (s.current_question_id === "chief_complaint_initial") {
        setQuestion({
          id: "chief_complaint_initial",
          text: "What brings you here today?",
          category: "HPI",
          input_type: "VOICE_ONLY",
          clinical_field: "chief_complaint",
          options: null,
          required: true
        });
      }
    } catch (_e: unknown) {
      setError("Failed to load interview state.");
    } finally {
      setLoading(false);
    }
  }, [session, router]);

  useEffect(() => {
    if (!session) {
      router.replace("/session");
      return;
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadState();
  }, [session, router, loadState]);

  const handleOptionSelect = async (optionId: string) => {
    if (!session || !question) return;
    setLoading(true);
    try {
      await submitClinicalAnswer(session.sessionId, {
        question_id: question.id,
        selected_option_id: optionId
      });
      await loadState();
    } catch (_e: unknown) {
      setError("Failed to submit answer.");
      setLoading(false);
    }
  };

  const handleVoiceSubmit = async () => {
    if (!session || !question || !mockTranscript) return;
    setIsListening(false);
    setLoading(true);
    try {
      await submitClinicalAnswer(session.sessionId, {
        question_id: question.id,
        raw_transcript: mockTranscript
      });
      setMockTranscript("");
      await loadState();
    } catch (_e: unknown) {
      setError("Failed to submit voice answer.");
      setLoading(false);
    }
  };

  if (!session || loading) return <div className="p-8 text-2xl">Loading...</div>;

  const hasRedFlags = state?.new_red_flags && state.new_red_flags.length > 0;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader title="Medical History" subtitle={question?.category} />
      
      {hasRedFlags && (
        <div className="bg-destructive text-destructive-foreground p-6 flex items-center gap-4 animate-in slide-in-from-top">
          <AlertTriangle size={32} />
          <div>
            <h3 className="text-2xl font-bold">PRIORITY ALERT</h3>
            <p className="text-xl">Some of your symptoms may require immediate medical attention.</p>
          </div>
        </div>
      )}

      <main className="flex-1 flex flex-col items-center justify-center p-8 max-w-4xl mx-auto w-full gap-8">
        
        {error && <StatusMessage message={error} type="error" />}

        {question && (
          <div className="w-full space-y-12">
            <h2 className="text-5xl font-bold text-brand-navy text-center leading-tight">
              &quot;{question.text}&quot;
            </h2>

            {/* Voice Input Section */}
            <div className="flex flex-col items-center bg-white p-8 rounded-3xl border-2 border-border shadow-sm gap-6">
              <button 
                onClick={() => setIsListening(!isListening)}
                className={`w-32 h-32 rounded-full flex items-center justify-center transition-all ${
                  isListening ? "bg-red-500 text-white animate-pulse" : "bg-primary/10 text-primary hover:bg-primary/20"
                }`}
              >
                {isListening ? <MicOff size={48} /> : <Mic size={48} />}
              </button>
              
              <span className="text-2xl font-medium text-muted-foreground">
                {isListening ? "Listening..." : "Tap to Speak"}
              </span>

              {process.env.NEXT_PUBLIC_AI_MODE === "mock" && isListening && (
                <div className="flex gap-4 w-full mt-4 items-center">
                  <input 
                    type="text" 
                    value={mockTranscript}
                    onChange={(e) => setMockTranscript(e.target.value)}
                    className="flex-1 p-4 border rounded-xl text-xl"
                    placeholder="[MOCK] Type voice transcript..."
                  />
                  <button onClick={handleVoiceSubmit} className="bg-primary text-white px-6 py-4 rounded-xl text-xl">
                    Submit
                  </button>
                </div>
              )}
            </div>

            {/* Touch Options */}
            {question.options && question.options.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {question.options.map(opt => (
                  <button
                    key={opt.id}
                    onClick={() => handleOptionSelect(opt.id)}
                    className="p-6 bg-white border-2 border-border rounded-2xl text-2xl font-semibold text-brand-navy hover:border-primary/50 hover:bg-slate-50 transition-all text-left"
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
