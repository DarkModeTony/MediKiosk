"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/AppHeader";
import { LargeTouchButton } from "@/components/shared/LargeTouchButton";
import { useKiosk } from "@/components/providers/KioskSessionProvider";
import { getTranslation } from "@/lib/i18n";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { StatusMessage } from "@/components/shared/StatusMessage";
import { registerPatient } from "@/lib/api/patients";
import { createKioskSession } from "@/lib/api/kiosk";
import {
  User,
  Calendar,
  Phone,
  HeartPulse,
  ArrowRight,
  ChevronLeft,
} from "lucide-react";

export default function NewPatientPage() {
  const router = useRouter();
  const { language, setSession } = useKiosk();
  const t = getTranslation(language);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    name: "",
    age: "",
    gender: "",
    mobile: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!formData.name.trim() || !formData.age.trim() || !formData.gender) {
      setError("Please fill in your name, age, and select your gender to proceed.");
      return;
    }

    setLoading(true);
    try {
      const patientData = await registerPatient({
        name: formData.name.trim(),
        date_of_birth: formData.age.trim(),
        gender: formData.gender,
        language: language,
        mobile_number: formData.mobile.trim(),
      });

      const sessionData = await createKioskSession({
        patient_id: patientData.patient_id,
        language: language,
      });

      setSession({
        sessionId: sessionData.session_token,
        patientId: patientData.patient_id,
        expiresAt: sessionData.expires_at,
      });

      router.push("/session");
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || t.errors.network);
      setLoading(false);
    }
  };

  const genders = ["Male", "Female", "Other"];

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-teal-50/20 to-white relative overflow-hidden">
      <div className="pointer-events-none absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full bg-teal-400/10 blur-3xl" />

      <AppHeader title={t.registration.new} />

      <main className="relative flex-1 flex flex-col items-center justify-center p-6 md:p-12 max-w-3xl mx-auto w-full">
        <form onSubmit={handleSubmit} className="w-full animate-fade-in">
          <div className="bg-white/90 backdrop-blur-sm p-8 md:p-12 rounded-3xl shadow-sm border border-slate-200 space-y-8">

            {/* Header */}
            <div className="space-y-2 text-center pb-4 border-b border-slate-100">
              <div className="w-14 h-14 bg-gradient-to-br from-teal-500 to-teal-600 rounded-2xl flex items-center justify-center mx-auto shadow-lg shadow-teal-600/25">
                <HeartPulse className="w-7 h-7 text-white" />
              </div>
              <h1 className="text-2xl md:text-3xl font-black text-slate-900">
                Patient Registration
              </h1>
              <p className="text-sm md:text-base text-slate-500">
                Please provide your basic details for the doctor&apos;s records.
              </p>
            </div>

            {error && <StatusMessage message={error} type="error" />}

            <div className="space-y-7">
              {/* Full Name */}
              <div className="space-y-2">
                <Label htmlFor="name" className="text-base md:text-lg font-bold text-slate-800 flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg bg-blue-100 flex items-center justify-center">
                    <User className="w-3.5 h-3.5 text-blue-600" />
                  </div>
                  {t.registration.name} <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="text-lg md:text-xl h-14 px-5 rounded-2xl border-2 border-slate-200 focus:border-blue-500 focus-visible:ring-0 focus-visible:ring-offset-0 bg-slate-50/50 transition-colors"
                  placeholder="e.g. Ramesh Kumar"
                  required
                />
              </div>

              {/* Age */}
              <div className="space-y-2">
                <Label htmlFor="age" className="text-base md:text-lg font-bold text-slate-800 flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg bg-blue-100 flex items-center justify-center">
                    <Calendar className="w-3.5 h-3.5 text-blue-600" />
                  </div>
                  {t.registration.age} (Years) <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="age"
                  type="number"
                  min="1"
                  max="120"
                  value={formData.age}
                  onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                  className="text-lg md:text-xl h-14 px-5 rounded-2xl border-2 border-slate-200 focus:border-blue-500 focus-visible:ring-0 focus-visible:ring-offset-0 bg-slate-50/50 transition-colors"
                  placeholder="e.g. 42"
                  required
                />
              </div>

              {/* Gender */}
              <div className="space-y-3">
                <Label className="text-base md:text-lg font-bold text-slate-800">
                  {t.registration.gender} <span className="text-red-500">*</span>
                </Label>
                <div className="grid grid-cols-3 gap-3">
                  {genders.map((g) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => setFormData({ ...formData, gender: g })}
                      className={`py-4 rounded-2xl text-base md:text-lg font-bold border-2 transition-all duration-200 active:scale-[0.98] ${
                        formData.gender === g
                          ? "border-blue-600 bg-blue-50 text-blue-700 shadow-sm shadow-blue-100"
                          : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50"
                      }`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>

              {/* Mobile */}
              <div className="space-y-2">
                <Label htmlFor="mobile" className="text-base md:text-lg font-bold text-slate-800 flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg bg-blue-100 flex items-center justify-center">
                    <Phone className="w-3.5 h-3.5 text-blue-600" />
                  </div>
                  {t.registration.mobile}{" "}
                  <span className="text-xs text-slate-400 font-normal">(Optional)</span>
                </Label>
                <Input
                  id="mobile"
                  type="tel"
                  value={formData.mobile}
                  onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                  className="text-lg md:text-xl h-14 px-5 rounded-2xl border-2 border-slate-200 focus:border-blue-500 focus-visible:ring-0 focus-visible:ring-offset-0 bg-slate-50/50 transition-colors"
                  placeholder="e.g. 9876543210"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4 pt-4 border-t border-slate-100">
              <LargeTouchButton
                type="button"
                variant="outline"
                onClick={() => router.back()}
                className="flex-1 py-5 text-base gap-2"
                disabled={loading}
              >
                <ChevronLeft className="w-4 h-4" />
                {t.common.back}
              </LargeTouchButton>
              <LargeTouchButton
                type="submit"
                variant="primary"
                className="flex-[2] py-5 text-xl font-extrabold gap-3"
                loading={loading}
              >
                {t.common.continue}
                <ArrowRight className="w-5 h-5" />
              </LargeTouchButton>
            </div>
          </div>
        </form>
      </main>
    </div>
  );
}
