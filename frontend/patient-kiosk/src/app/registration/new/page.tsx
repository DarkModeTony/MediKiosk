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
    
    if (!formData.name || !formData.age || !formData.gender) {
      setError(t.common.error);
      return;
    }

    setLoading(true);
    try {
      // 1. Register Patient
      const patientData = await registerPatient({
        name: formData.name,
        date_of_birth: formData.age,
        gender: formData.gender,
        language: language,
        mobile_number: formData.mobile,
      });

      // 2. Create Session
      const sessionData = await createKioskSession({
        patient_id: patientData.patient_id,
        language: language,
      });

      // 3. Save to Context & Redirect
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

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader title={t.registration.new} />
      
      <main className="flex-1 flex flex-col items-center justify-center p-8 max-w-4xl mx-auto w-full">
        
        <form onSubmit={handleSubmit} className="bg-white p-12 rounded-3xl shadow-sm border border-border w-full space-y-8">
          
          {error && <StatusMessage message={error} type="error" />}

          <div className="space-y-6">
            <div className="space-y-3">
              <Label htmlFor="name" className="text-2xl text-brand-navy">{t.registration.name}</Label>
              <Input 
                id="name" 
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="text-2xl p-8 rounded-2xl" 
                placeholder="John Doe"
              />
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-3">
                <Label htmlFor="age" className="text-2xl text-brand-navy">{t.registration.age}</Label>
                <Input 
                  id="age" 
                  value={formData.age}
                  onChange={(e) => setFormData({...formData, age: e.target.value})}
                  className="text-2xl p-8 rounded-2xl"
                  placeholder="e.g. 45"
                />
              </div>

              <div className="space-y-3">
                <Label htmlFor="gender" className="text-2xl text-brand-navy">{t.registration.gender}</Label>
                <div className="flex gap-4">
                  {["Male", "Female"].map((g) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => setFormData({...formData, gender: g})}
                      className={`flex-1 py-5 rounded-2xl text-xl font-medium border-2 transition-all ${
                        formData.gender === g 
                          ? "border-primary bg-primary/10 text-primary" 
                          : "border-border bg-white text-muted-foreground hover:bg-slate-50"
                      }`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <Label htmlFor="mobile" className="text-2xl text-brand-navy">{t.registration.mobile}</Label>
              <Input 
                id="mobile"
                type="tel" 
                value={formData.mobile}
                onChange={(e) => setFormData({...formData, mobile: e.target.value})}
                className="text-2xl p-8 rounded-2xl" 
                placeholder="Optional"
              />
            </div>
          </div>

          <div className="flex gap-6 pt-8 mt-8 border-t border-border">
            <LargeTouchButton 
              type="button"
              variant="outline" 
              onClick={() => router.back()}
              className="flex-1"
              disabled={loading}
            >
              {t.common.back}
            </LargeTouchButton>
            <LargeTouchButton 
              type="submit"
              variant="primary" 
              className="flex-[2] shadow-lg shadow-primary/20"
              disabled={loading}
            >
              {loading ? t.common.loading : t.common.continue}
            </LargeTouchButton>
          </div>

        </form>
      </main>
    </div>
  );
}
