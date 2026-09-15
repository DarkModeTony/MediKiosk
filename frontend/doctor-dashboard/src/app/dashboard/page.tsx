'use client';

import React, { useEffect, useState } from 'react';
import DoctorLayout from '@/components/layout/DoctorLayout';
import { getQueue } from '@/lib/api/queue';
import { QueueItem } from '@/lib/api/types';
import {
  Users,
  AlertTriangle,
  CheckCircle2,
  Clock,
  TrendingUp,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import Link from 'next/link';

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  gradient,
  accent,
}: {
  label: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  gradient: string;
  accent: string;
}) {
  return (
    <div className={`relative bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 overflow-hidden hover:shadow-md transition-shadow duration-300`}>
      {/* Gradient accent top bar */}
      <div className={`absolute top-0 left-0 right-0 h-1 ${gradient}`} />

      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">{label}</p>
          <p className={`text-4xl font-black mt-2 ${color} animate-fade-in`}>{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-2xl ${accent} flex items-center justify-center`}>
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
      </div>

      <div className="mt-4 flex items-center gap-1.5">
        <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
        <span className="text-xs text-slate-400">Updated just now</span>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const loadQueue = () => {
    setLoading(true);
    getQueue().then((data) => {
      setQueue(data);
      setLoading(false);
      setLastUpdated(new Date());
    });
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const waiting = queue.filter((q) => q.status === 'WAITING').length;
  const inConsultation = queue.filter((q) => q.status === 'IN_CONSULTATION').length;
  const completed = queue.filter((q) => q.status === 'COMPLETED').length;
  const highPriority = queue.filter((q) => q.priority === 'HIGH' && q.status !== 'COMPLETED').length;

  const highPriorityPatients = queue.filter(
    (q) => q.priority === 'HIGH' && q.status !== 'COMPLETED'
  );

  return (
    <DoctorLayout>
      <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">

        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100">Good morning, Dr. Sharma</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1 text-sm">
              Last updated: {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </p>
          </div>
          <button
            onClick={loadQueue}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 shadow-sm transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Stat cards */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 h-32 animate-pulse">
                <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded-full w-20 mb-3" />
                <div className="h-10 bg-slate-200 dark:bg-slate-700 rounded-full w-16" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
            <StatCard label="Waiting" value={waiting} icon={Users} color="text-blue-600" gradient="bg-gradient-to-r from-blue-500 to-blue-600" accent="bg-blue-50 dark:bg-blue-900/30" />
            <StatCard label="In Consultation" value={inConsultation} icon={Clock} color="text-amber-600" gradient="bg-gradient-to-r from-amber-400 to-amber-500" accent="bg-amber-50 dark:bg-amber-900/30" />
            <StatCard label="High Priority" value={highPriority} icon={AlertTriangle} color="text-red-600" gradient="bg-gradient-to-r from-red-500 to-red-600" accent="bg-red-50 dark:bg-red-900/30" />
            <StatCard label="Completed" value={completed} icon={CheckCircle2} color="text-teal-600" gradient="bg-gradient-to-r from-teal-500 to-teal-600" accent="bg-teal-50 dark:bg-teal-900/30" />
          </div>
        )}

        {/* High priority patient list */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-2 h-2 rounded-full bg-red-500" />
              <h2 className="font-bold text-slate-800 dark:text-slate-100 text-base">High Priority Patients</h2>
            </div>
            <Link
              href="/queue"
              className="flex items-center gap-1.5 text-sm text-teal-600 hover:text-teal-700 font-semibold transition-colors"
            >
              View All Queue
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="divide-y divide-slate-50 dark:divide-slate-700">
            {highPriorityPatients.length === 0 ? (
              <div className="px-6 py-10 text-center">
                <CheckCircle2 className="w-10 h-10 text-teal-400 mx-auto mb-3" />
                <p className="text-slate-500 dark:text-slate-400 font-medium">No high priority patients waiting.</p>
                <p className="text-sm text-slate-400 mt-1">All clear for now.</p>
              </div>
            ) : (
              highPriorityPatients.map((patient) => (
                <div
                  key={patient.id}
                  className="px-6 py-4 flex items-center justify-between hover:bg-red-50/50 dark:hover:bg-red-900/10 transition-colors priority-high pl-7"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-red-400 to-red-600 text-white flex items-center justify-center font-black text-sm shadow-sm">
                      {patient.name.charAt(0)}
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900 dark:text-slate-100">{patient.name}</h3>
                      <p className="text-sm text-slate-500 dark:text-slate-400">
                        {patient.age}y • {patient.chief_complaint}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-700 border border-red-200">
                      <AlertTriangle className="w-3 h-3" />
                      HIGH
                    </span>
                    <Link
                      href={`/encounters/${patient.id}`}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 dark:bg-slate-700 text-white text-sm font-bold hover:bg-slate-800 dark:hover:bg-slate-600 shadow-sm transition-all"
                    >
                      Open Encounter
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </DoctorLayout>
  );
}
