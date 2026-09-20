'use client';

import React, { useState, useRef } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { Stethoscope, Shield, Sparkles, Zap, User, Lock, ArrowRight, Loader2, Building2, MapPin, CheckCircle2 } from 'lucide-react';

export interface NetworkDoctor {
  username: string;
  password: string;
  displayName: string;
  specialty: string;
  subSpecialty: string;
  hospital: string;
  city: string;
  initials: string;
  role: string;
}

export const NETWORK_DOCTORS: NetworkDoctor[] = [
  {
    username: 'dr.sharma',
    password: 'demo1234',
    displayName: 'Dr. Priya Sharma',
    specialty: 'Internal Medicine',
    subSpecialty: 'Preventative & Metabolic Care',
    hospital: 'Apollo Hospitals Delhi',
    city: 'Delhi',
    initials: 'PS',
    role: 'Senior Physician · Apollo Hospitals Delhi',
  },
  {
    username: 'dr.sengupta',
    password: 'demo1234',
    displayName: 'Dr. Rajesh Sengupta',
    specialty: 'Cardiology',
    subSpecialty: 'Interventional Cardiology & Angioplasty',
    hospital: 'Fortis Memorial Research Institute Gurugram',
    city: 'Gurugram',
    initials: 'RS',
    role: 'Director of Cardiology · Fortis Gurugram',
  },
  {
    username: 'dr.iyer',
    password: 'demo1234',
    displayName: 'Dr. Ananya Iyer',
    specialty: 'Neurology',
    subSpecialty: 'Acute Stroke & Comprehensive Epilepsy Care',
    hospital: 'Manipal Hospital Bengaluru',
    city: 'Bengaluru',
    initials: 'AI',
    role: 'Chief Neurologist · Manipal Bengaluru',
  },
  {
    username: 'dr.mehta',
    password: 'demo1234',
    displayName: 'Dr. Vikramaditya Mehta',
    specialty: 'Pulmonology',
    subSpecialty: 'Interventional Pulmonology & Sleep Medicine',
    hospital: 'Max Super Speciality Hospital Saket, New Delhi',
    city: 'New Delhi',
    initials: 'VM',
    role: 'Senior Consultant Pulmonologist · Max Saket',
  },
  {
    username: 'dr.siddiqui',
    password: 'demo1234',
    displayName: 'Dr. Farah Siddiqui',
    specialty: 'Gastroenterology',
    subSpecialty: 'Hepatology, Therapeutic Endoscopy & IBD',
    hospital: 'Kokilaben Dhirubhai Ambani Hospital Mumbai',
    city: 'Mumbai',
    initials: 'FS',
    role: 'Senior Gastroenterologist · Kokilaben Mumbai',
  },
  {
    username: 'dr.sundaram',
    password: 'demo1234',
    displayName: 'Dr. Karthik Sundaram',
    specialty: 'Nephrology',
    subSpecialty: 'Renal Transplantation & Hemodialysis',
    hospital: 'Apollo Hospitals Greams Road, Chennai',
    city: 'Chennai',
    initials: 'KS',
    role: 'Head of Nephrology · Apollo Chennai',
  },
  {
    username: 'dr.banerjee',
    password: 'demo1234',
    displayName: 'Dr. Sunita Banerjee',
    specialty: 'Endocrinology',
    subSpecialty: 'Advanced Diabetes Care & Thyroid Disorders',
    hospital: 'Medica Superspecialty Hospital Kolkata',
    city: 'Kolkata',
    initials: 'SB',
    role: 'Consultant Endocrinologist · Medica Kolkata',
  },
  {
    username: 'dr.kulkarni',
    password: 'demo1234',
    displayName: 'Dr. Rohan Kulkarni',
    specialty: 'Orthopedics',
    subSpecialty: 'Robotic Joint Replacement & Sports Trauma',
    hospital: 'Ruby Hall Clinic Pune',
    city: 'Pune',
    initials: 'RK',
    role: 'Orthopedic Surgeon · Ruby Hall Pune',
  },
];

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [selectedDoctor, setSelectedDoctor] = useState<NetworkDoctor>(NETWORK_DOCTORS[0]);
  const [demoFlash, setDemoFlash] = useState(false);
  const usernameRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  const saveDoctorToStorage = (doc: NetworkDoctor, token?: string, userId?: string, hospitalId?: string) => {
    try {
      if (token) {
        localStorage.setItem('token', token);
        localStorage.setItem('access_token', token);
      }
      localStorage.setItem(
        'currentUser',
        JSON.stringify({
          username: doc.username,
          displayName: doc.displayName,
          specialty: doc.specialty,
          subSpecialty: doc.subSpecialty,
          hospital: doc.hospital,
          city: doc.city,
          initials: doc.initials,
          user_id: userId,
          hospital_id: hospitalId,
        })
      );
    } catch (e) {
      console.warn('Could not save user to storage', e);
    }
  };

  const authenticateAndLogin = async (username: string, password: string, fallbackDoc: NetworkDoctor) => {
    setLoading(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    try {
      const res = await fetch(`${apiUrl}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (res.ok) {
        const data = await res.json();
        saveDoctorToStorage(fallbackDoc, data.access_token, data.user_id, data.hospital_id);
      } else {
        saveDoctorToStorage(fallbackDoc);
      }
    } catch (err) {
      console.warn('Real auth API unavailable, falling back to local session:', err);
      saveDoctorToStorage(fallbackDoc);
    }

    setTimeout(() => {
      router.push('/dashboard');
    }, 350);
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    const enteredUsername = usernameRef.current?.value || selectedDoctor.username;
    const enteredPassword = passwordRef.current?.value || selectedDoctor.password;
    const matched = NETWORK_DOCTORS.find((d) => d.username.toLowerCase() === enteredUsername.toLowerCase()) || selectedDoctor;
    authenticateAndLogin(enteredUsername, enteredPassword, matched);
  };

  const handleDoctorSelect = (doc: NetworkDoctor) => {
    setSelectedDoctor(doc);
    setDemoFlash(true);
    if (usernameRef.current) usernameRef.current.value = doc.username;
    if (passwordRef.current) passwordRef.current.value = doc.password;
    authenticateAndLogin(doc.username, doc.password, doc);
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
              <p className="text-teal-400 text-sm font-semibold">Multi-Hospital Physician Network</p>
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
              Review AI-prepared patient summaries, triage by priority, and collaborate across India&apos;s leading hospitals via DocTalk specialist consultations.
            </p>
          </div>

          {/* Feature bullets */}
          <div className="space-y-3">
            {[
              { icon: Stethoscope, text: 'Pre-consultation clinical intake summaries from AI' },
              { icon: Shield, text: 'Deterministic red-flag triage engine' },
              { icon: Sparkles, text: 'Cross-hospital DocTalk specialist network across 8 Indian cities' },
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

      {/* Right — Login Form & Multi-Doctor Switcher */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-8 bg-slate-50 overflow-y-auto">
        <div className="w-full max-w-md space-y-5 my-auto">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center p-1.5 shadow-sm">
              <Image src="/logo-white.png" alt="MediPlatform Logo" width={28} height={28} className="w-full h-full object-contain" />
            </div>
            <span className="text-xl font-black text-slate-900">MediPlatform</span>
          </div>

          <div>
            <h2 className="text-2xl sm:text-3xl font-black text-slate-900">Physician Sign in</h2>
            <p className="text-slate-500 text-xs sm:text-sm mt-1">Select a verified network doctor or enter credentials.</p>
          </div>

          {/* Quick Doctor Selection Grid (All 8 Doctors across India) */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Select Network Physician ({NETWORK_DOCTORS.length} Available)
              </span>
              <span className="text-[10px] text-teal-600 font-semibold">1-Click Sign In</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-56 overflow-y-auto pr-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-inner">
              {NETWORK_DOCTORS.map((doc) => {
                const isSelected = selectedDoctor.username === doc.username;
                return (
                  <button
                    key={doc.username}
                    type="button"
                    onClick={() => handleDoctorSelect(doc)}
                    disabled={loading}
                    className={`text-left p-2.5 rounded-xl border transition-all flex flex-col justify-between gap-1 group ${
                      isSelected
                        ? 'border-teal-500 bg-teal-50/80 ring-1 ring-teal-500 shadow-sm'
                        : 'border-slate-100 hover:border-teal-300 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1.5">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <div className="w-6 h-6 rounded-lg bg-teal-600 text-white font-black text-[10px] flex items-center justify-center shrink-0">
                          {doc.initials}
                        </div>
                        <span className="text-xs font-bold text-slate-900 truncate">{doc.displayName}</span>
                      </div>
                      {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />}
                    </div>
                    <div className="space-y-0.5 text-[10px]">
                      <span className="inline-block font-semibold text-teal-700 bg-teal-100/60 px-1.5 py-0.2 rounded">
                        {doc.specialty}
                      </span>
                      <p className="text-slate-500 truncate flex items-center gap-0.5">
                        <Building2 className="w-2.5 h-2.5 text-slate-400 shrink-0" />
                        <span className="truncate">{doc.hospital}</span>
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-slate-200" />
            <span className="text-xs text-slate-400 font-medium">or sign in with credentials</span>
            <div className="flex-1 h-px bg-slate-200" />
          </div>

          <form className="space-y-3.5" onSubmit={handleLogin}>
            <div className="space-y-1">
              <label htmlFor="username" className="block text-xs font-semibold text-slate-700">Username</label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  id="username" name="username" type="text" ref={usernameRef}
                  defaultValue={selectedDoctor.username} required
                  className={`w-full pl-10 pr-4 py-2.5 rounded-xl border-2 bg-white text-slate-900 text-sm font-medium focus:outline-none focus:ring-4 transition-all placeholder:text-slate-400 ${
                    demoFlash ? 'border-teal-400 ring-4 ring-teal-500/20 bg-teal-50' : 'border-slate-200 focus:border-teal-500 focus:ring-teal-500/10'
                  }`}
                />
              </div>
            </div>

            <div className="space-y-1">
              <label htmlFor="password" className="block text-xs font-semibold text-slate-700">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  id="password" name="password" type="password" ref={passwordRef}
                  defaultValue={selectedDoctor.password} required
                  className={`w-full pl-10 pr-4 py-2.5 rounded-xl border-2 bg-white text-slate-900 text-sm font-medium focus:outline-none focus:ring-4 transition-all placeholder:text-slate-400 ${
                    demoFlash ? 'border-teal-400 ring-4 ring-teal-500/20 bg-teal-50' : 'border-slate-200 focus:border-teal-500 focus:ring-teal-500/10'
                  }`}
                />
              </div>
            </div>

            <button
              type="submit" disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl text-sm font-bold text-white bg-slate-900 hover:bg-slate-800 shadow-lg shadow-slate-900/20 hover:shadow-xl transition-all duration-200 active:scale-[0.99] disabled:opacity-60"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
              Sign in as {selectedDoctor.displayName}
            </button>
          </form>

          <p className="text-center text-[11px] text-slate-400">
            MediPlatform v2.0 · All passwords default to <code className="font-mono font-bold text-slate-600">demo1234</code>
          </p>
        </div>
      </div>
    </div>
  );
}

