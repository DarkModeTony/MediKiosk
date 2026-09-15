'use client';

import React, { useState, useRef } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { Stethoscope, Shield, Sparkles, Zap, User, Lock, ArrowRight, Loader2 } from 'lucide-react';

const DEMO_CREDENTIALS = {
  username: 'dr.sharma',
  password: 'demo1234',
  displayName: 'Dr. Priya Sharma',
  role: 'Senior Physician · Apollo Hospitals',
};

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [demoFlash, setDemoFlash] = useState(false);
  const usernameRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => router.push('/dashboard'), 800);
  };

  const handleDemoLogin = () => {
    setDemoFlash(true);
    if (usernameRef.current) usernameRef.current.value = DEMO_CREDENTIALS.username;
    if (passwordRef.current) passwordRef.current.value = DEMO_CREDENTIALS.password;
    setTimeout(() => {
      setDemoFlash(false);
      setLoading(true);
      setTimeout(() => router.push('/dashboard'), 700);
    }, 500);
  };

  return (
    <div className="min-h-screen flex">
      {/* Left — Brand Panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-slate-900 via-slate-800 to-teal-950 flex-col items-center justify-center p-16 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] rounded-full bg-teal-500/5 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full bg-blue-500/5 blur-3xl pointer-events-none" />

        <div className="relative space-y-10 max-w-md">
          {/* Logo */}
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center p-2.5 shadow-2xl shadow-teal-600/30">
              <Image src="/logo-white.png" alt="MediPlatform Logo" width={40} height={40} className="w-full h-full object-contain" />
            </div>
            <div>
              <h1 className="text-2xl font-black text-white tracking-tight">MediPlatform</h1>
              <p className="text-teal-400 text-sm font-semibold">Physician Workspace</p>
            </div>
          </div>

          {/* Headline */}
          <div className="space-y-4">
            <h2 className="text-4xl font-black text-white leading-tight">
              AI-powered clinical summaries,{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-cyan-300">
                verified by you.
              </span>
            </h2>
            <p className="text-slate-400 text-lg leading-relaxed">
              Review AI-prepared patient summaries, triage by priority, and verify clinical records — all before the consultation begins.
            </p>
          </div>

          {/* Feature bullets */}
          <div className="space-y-3">
            {[
              { icon: Stethoscope, text: 'Pre-consultation clinical summaries from AI' },
              { icon: Shield, text: 'Deterministic red-flag triage engine' },
              { icon: Sparkles, text: 'Gemini AI extraction from uploaded documents' },
            ].map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-teal-900/60 border border-teal-700/50 flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4 text-teal-400" />
                </div>
                <p className="text-slate-300 text-sm font-medium">{text}</p>
              </div>
            ))}
          </div>

          {/* Demo patient snapshot card */}
          <div className="p-4 rounded-2xl bg-teal-900/30 border border-teal-700/40 backdrop-blur-sm">
            <p className="text-teal-300 text-xs font-semibold uppercase tracking-wider mb-3">Demo Patient Preloaded</p>
            <div className="space-y-1.5 text-sm">
              {[
                { label: 'Patient',    value: 'Raj Kumar, 42M · Delhi', cls: 'text-white font-semibold' },
                { label: 'Complaint',  value: 'Fever & weakness · 3 days', cls: 'text-white font-semibold' },
                { label: 'History',    value: 'T2DM · Hypertension', cls: 'text-white font-semibold' },
                { label: 'Allergy',    value: '⚠ Penicillin', cls: 'text-amber-300 font-semibold' },
                { label: 'Vitals',     value: 'Temp 101.2°F · BP 148/92', cls: 'text-white font-semibold' },
                { label: 'Meds',       value: 'Metformin · Amlodipine', cls: 'text-white font-semibold' },
              ].map(({ label, value, cls }) => (
                <div key={label} className="flex justify-between">
                  <span className="text-slate-400">{label}</span>
                  <span className={cls}>{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right — Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-slate-50">
        <div className="w-full max-w-md space-y-6">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center p-1.5 shadow-sm">
              <Image src="/logo-white.png" alt="MediPlatform Logo" width={28} height={28} className="w-full h-full object-contain" />
            </div>
            <span className="text-xl font-black text-slate-900">MediPlatform</span>
          </div>

          <div>
            <h2 className="text-3xl font-black text-slate-900">Sign in</h2>
            <p className="text-slate-500 mt-2">Access your physician workspace.</p>
          </div>

          {/* One-click Demo Login button */}
          <button
            id="demo-login-btn"
            type="button"
            onClick={handleDemoLogin}
            disabled={loading}
            className="w-full flex items-center justify-between gap-3 px-5 py-4 rounded-2xl bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-500 hover:to-teal-400 text-white shadow-xl shadow-teal-600/30 hover:shadow-2xl hover:shadow-teal-600/40 transition-all duration-200 group disabled:opacity-70"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center font-black text-base shrink-0">
                PS
              </div>
              <div className="text-left">
                <p className="font-bold text-sm">{DEMO_CREDENTIALS.displayName}</p>
                <p className="text-teal-100/80 text-xs">{DEMO_CREDENTIALS.role}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-xs font-bold bg-white/20 px-2.5 py-1 rounded-lg">DEMO</span>
              {loading
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <Zap className="w-4 h-4 group-hover:scale-110 transition-transform" />
              }
            </div>
          </button>

          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-slate-200" />
            <span className="text-xs text-slate-400 font-medium">or sign in manually</span>
            <div className="flex-1 h-px bg-slate-200" />
          </div>

          <form className="space-y-4" onSubmit={handleLogin}>
            <div className="space-y-1.5">
              <label htmlFor="username" className="block text-sm font-semibold text-slate-700">Username</label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  id="username" name="username" type="text" ref={usernameRef}
                  defaultValue={DEMO_CREDENTIALS.username} required
                  className={`w-full pl-10 pr-4 py-3 rounded-xl border-2 bg-white text-slate-900 text-sm font-medium focus:outline-none focus:ring-4 transition-all placeholder:text-slate-400 ${
                    demoFlash ? 'border-teal-400 ring-4 ring-teal-500/20 bg-teal-50' : 'border-slate-200 focus:border-teal-500 focus:ring-teal-500/10'
                  }`}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="password" className="block text-sm font-semibold text-slate-700">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  id="password" name="password" type="password" ref={passwordRef}
                  defaultValue={DEMO_CREDENTIALS.password} required
                  className={`w-full pl-10 pr-4 py-3 rounded-xl border-2 bg-white text-slate-900 text-sm font-medium focus:outline-none focus:ring-4 transition-all placeholder:text-slate-400 ${
                    demoFlash ? 'border-teal-400 ring-4 ring-teal-500/20 bg-teal-50' : 'border-slate-200 focus:border-teal-500 focus:ring-teal-500/10'
                  }`}
                />
              </div>
            </div>

            <button
              type="submit" disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl text-base font-bold text-white bg-slate-900 hover:bg-slate-800 shadow-lg shadow-slate-900/20 hover:shadow-xl transition-all duration-200 active:scale-[0.99] disabled:opacity-60"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <ArrowRight className="w-5 h-5" />}
              Sign in to Workspace
            </button>
          </form>

          <p className="text-center text-xs text-slate-400">
            MediPlatform v2.0 · Protected by clinical PHI security protocols
          </p>
        </div>
      </div>
    </div>
  );
}
