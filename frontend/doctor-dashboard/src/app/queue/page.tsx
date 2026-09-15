'use client';

import React, { useEffect, useState } from 'react';
import DoctorLayout from '@/components/layout/DoctorLayout';
import { getQueue } from '@/lib/api/queue';
import { QueueItem } from '@/lib/api/types';
import {
  Clock,
  AlertCircle,
  CheckCircle2,
  Users,
  Filter,
  RefreshCw,
  ArrowRight,
  UserCircle2,
} from 'lucide-react';
import Link from 'next/link';

type FilterOption = 'ALL' | 'HIGH' | 'MEDIUM' | 'NORMAL' | 'WAITING' | 'IN_CONSULTATION' | 'COMPLETED';

const PRIORITY_CONFIG = {
  HIGH: { label: 'HIGH', bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400', border: 'border-red-200', icon: AlertCircle, dot: 'bg-red-500' },
  MEDIUM: { label: 'MED', bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-400', border: 'border-amber-200', icon: Clock, dot: 'bg-amber-400' },
  NORMAL: { label: 'NORMAL', bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-400', border: 'border-blue-200', icon: Users, dot: 'bg-blue-400' },
} as const;

const STATUS_CONFIG = {
  WAITING: { label: 'Waiting', dot: 'bg-amber-400', text: 'text-amber-600 dark:text-amber-400' },
  IN_CONSULTATION: { label: 'In Consultation', dot: 'bg-teal-500', text: 'text-teal-600 dark:text-teal-400' },
  COMPLETED: { label: 'Completed', dot: 'bg-slate-300', text: 'text-slate-400' },
} as const;

export default function QueuePage() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterOption>('ALL');

  const loadQueue = () => {
    setLoading(true);
    getQueue().then((data) => {
      setQueue(data);
      setLoading(false);
    });
  };

  useEffect(() => { loadQueue(); }, []);

  const filtered = queue.filter((p) => {
    if (filter === 'ALL') return true;
    if (filter === 'HIGH' || filter === 'MEDIUM' || filter === 'NORMAL') return p.priority === filter;
    return p.status === filter;
  });

  const filterBtns: { key: FilterOption; label: string }[] = [
    { key: 'ALL', label: 'All' },
    { key: 'HIGH', label: '🔴 High' },
    { key: 'MEDIUM', label: '🟡 Medium' },
    { key: 'WAITING', label: 'Waiting' },
    { key: 'IN_CONSULTATION', label: 'In Consultation' },
    { key: 'COMPLETED', label: 'Completed' },
  ];

  return (
    <DoctorLayout>
      <div className="max-w-7xl mx-auto space-y-6 animate-fade-in">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100">Patient Queue</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
              {queue.length} total · {queue.filter(q => q.status === 'WAITING').length} waiting
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

        {/* Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-4 h-4 text-slate-400" />
          {filterBtns.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all border ${
                filter === key
                  ? 'bg-teal-600 text-white border-teal-600 shadow-sm'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Patient Cards */}
        {loading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 animate-pulse">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-slate-200 dark:bg-slate-700" />
                  <div className="space-y-2 flex-1">
                    <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded-full w-32" />
                    <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded-full w-48" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-16 text-center">
            <CheckCircle2 className="w-12 h-12 text-teal-400 mx-auto mb-4" />
            <p className="text-slate-500 dark:text-slate-400 font-semibold text-lg">No patients match this filter.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map((patient) => {
              const pCfg = PRIORITY_CONFIG[patient.priority as keyof typeof PRIORITY_CONFIG] || PRIORITY_CONFIG.NORMAL;
              const sCfg = STATUS_CONFIG[patient.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.WAITING;

              return (
                <div
                  key={patient.id}
                  className={`group bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 hover:shadow-md transition-all duration-200 overflow-hidden ${
                    patient.priority === 'HIGH' ? 'priority-high' : patient.priority === 'MEDIUM' ? 'priority-medium' : 'priority-normal'
                  }`}
                >
                  <div className="p-5 flex items-center gap-5">
                    {/* Avatar */}
                    <div className={`w-12 h-12 rounded-2xl ${pCfg.bg} border ${pCfg.border} flex items-center justify-center font-black text-lg shrink-0 ${pCfg.text}`}>
                      {patient.name.charAt(0)}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-bold text-slate-900 dark:text-slate-100 text-base">{patient.name}</h3>
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${pCfg.bg} ${pCfg.text} ${pCfg.border}`}>
                          <pCfg.icon className="w-3 h-3" />
                          {pCfg.label}
                        </span>
                      </div>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5 truncate">
                        {patient.age}y · {patient.gender} · {patient.chief_complaint}
                      </p>
                    </div>

                    {/* Status + Time */}
                    <div className="hidden md:flex flex-col items-end gap-1 shrink-0">
                      <div className={`flex items-center gap-1.5 text-xs font-semibold ${sCfg.text}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${sCfg.dot}`} />
                        {sCfg.label}
                      </div>
                      <p className="text-xs text-slate-400">
                        {new Date(patient.arrival).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>

                    {/* CTA */}
                    <Link
                      href={`/encounters/${patient.id}`}
                      className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 dark:bg-slate-700 text-white text-sm font-bold hover:bg-slate-800 dark:hover:bg-slate-600 shadow-sm transition-all group-hover:shadow-md shrink-0"
                    >
                      <UserCircle2 className="w-4 h-4" />
                      <span className="hidden sm:inline">Open</span>
                      <ArrowRight className="w-3.5 h-3.5 opacity-70" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </DoctorLayout>
  );
}
