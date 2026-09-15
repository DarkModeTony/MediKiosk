'use client';

import React from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { Stethoscope, Shield, Sparkles } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen flex">
      {/* Left — Brand Panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-slate-900 via-slate-800 to-teal-950 flex-col items-center justify-center p-16 relative overflow-hidden">
        {/* Decorative circles */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] rounded-full bg-teal-500/5 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full bg-blue-500/5 blur-3xl pointer-events-none" />

        <div className="relative space-y-10 max-w-md">
          {/* Logo */}
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center p-2.5 shadow-2xl shadow-teal-600/30">
              <Image
                src="/logo-white.png"
                alt="MediPlatform Logo"
                width={40}
                height={40}
                className="w-full h-full object-contain"
              />
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
        </div>
      </div>

      {/* Right — Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-slate-50">
        <div className="w-full max-w-md space-y-8">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center p-1.5 shadow-sm">
              <Image
                src="/logo-white.png"
                alt="MediPlatform Logo"
                width={28}
                height={28}
                className="w-full h-full object-contain"
              />
            </div>
            <span className="text-xl font-black text-slate-900">MediPlatform</span>
          </div>

          <div>
            <h2 className="text-3xl font-black text-slate-900">Sign in</h2>
            <p className="text-slate-500 mt-2">Access your physician workspace.</p>
          </div>

          {/* Demo badge */}
          <div className="flex items-center gap-2 px-4 py-3 bg-blue-50 border border-blue-200 rounded-xl text-sm">
            <Sparkles className="w-4 h-4 text-blue-600 shrink-0" />
            <p className="text-blue-800">
              <strong>Demo Mode —</strong> credentials are pre-filled. Click Sign In to continue.
            </p>
          </div>

          <form className="space-y-5" onSubmit={handleLogin}>
            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-sm font-semibold text-slate-700">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                defaultValue="dr.sharma@mediplatform.local"
                required
                className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 bg-white text-slate-900 text-sm font-medium focus:outline-none focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 transition-all placeholder:text-slate-400"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="password" className="block text-sm font-semibold text-slate-700">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                defaultValue="demo1234"
                required
                className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 bg-white text-slate-900 text-sm font-medium focus:outline-none focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 transition-all placeholder:text-slate-400"
              />
            </div>

            <button
              type="submit"
              className="w-full py-3.5 px-6 rounded-xl text-base font-bold text-white bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-500 hover:to-teal-400 shadow-lg shadow-teal-600/25 hover:shadow-xl hover:shadow-teal-600/30 transition-all duration-200 active:scale-[0.99]"
            >
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
