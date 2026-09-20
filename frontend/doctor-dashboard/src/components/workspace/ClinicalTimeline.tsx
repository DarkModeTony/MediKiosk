'use client';

import React, { useState } from 'react';
import {
  FileText,
  User,
  Stethoscope,
  CheckCircle2,
  Play,
  Building2,
  Clock,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import { TimelineEvent, DocumentEntity } from '@/lib/api/types';
import { cn } from '@/lib/utils';

interface ClinicalTimelineProps {
  events: TimelineEvent[];
}

export default function ClinicalTimeline({ events }: ClinicalTimelineProps) {
  const [expandedOpinions, setExpandedOpinions] = useState<Record<number, boolean>>({});

  if (!events || events.length === 0) {
    return (
      <div className="py-12 text-center text-slate-400 dark:text-slate-500 italic">
        <Clock className="w-10 h-10 mx-auto mb-2 text-slate-300 dark:text-slate-600" />
        <p className="font-medium">Timeline events not documented yet.</p>
      </div>
    );
  }

  const toggleOpinion = (idx: number) => {
    setExpandedOpinions((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const formatTime = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return 'Date not documented';
    }
  };

  const getEventMeta = (event: TimelineEvent) => {
    switch (event.type) {
      case 'DOCTALK_REQUESTED':
        return {
          icon: <Stethoscope className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />,
          dotBg: 'bg-cyan-500 ring-4 ring-cyan-100 dark:ring-cyan-950',
          title: event.title || '🩺 DocTalk requested',
          badgeColor: 'bg-cyan-50 dark:bg-cyan-900/40 text-cyan-700 dark:text-cyan-300 border-cyan-200 dark:border-cyan-800',
        };
      case 'DOCTALK_ACCEPTED':
        return {
          icon: <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />,
          dotBg: 'bg-emerald-500 ring-4 ring-emerald-100 dark:ring-emerald-950',
          title: event.title || '✓ Specialist accepted',
          badgeColor: 'bg-emerald-50 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800',
        };
      case 'DOCTALK_STARTED':
        return {
          icon: <Play className="w-4 h-4 fill-current text-green-600 dark:text-green-400" />,
          dotBg: 'bg-green-500 ring-4 ring-green-100 dark:ring-green-950',
          title: event.title || '🟢 Consultation started',
          badgeColor: 'bg-green-50 dark:bg-green-900/40 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800',
        };
      case 'DOCTALK_COMPLETED':
        return {
          icon: <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400" />,
          dotBg: 'bg-teal-500 ring-4 ring-teal-100 dark:ring-teal-950',
          title: event.title || '✓ Consultation completed',
          badgeColor: 'bg-teal-50 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300 border-teal-200 dark:border-teal-800',
        };
      case 'DOCTALK_OPINION':
        return {
          icon: <FileText className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />,
          dotBg: 'bg-indigo-600 ring-4 ring-indigo-100 dark:ring-indigo-950',
          title: event.title || '📄 Specialist opinion added',
          badgeColor: 'bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800',
        };
      case 'ENCOUNTER':
        return {
          icon: <User className="w-4 h-4 text-teal-600 dark:text-teal-400" />,
          dotBg: 'bg-teal-500 ring-4 ring-teal-100 dark:ring-teal-950',
          title: event.document_type || 'Encounter',
          badgeColor: 'bg-teal-50 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300 border-teal-200 dark:border-teal-800',
        };
      default:
        return {
          icon: <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />,
          dotBg: 'bg-blue-500 ring-4 ring-blue-100 dark:ring-blue-950',
          title: event.document_type || 'Clinical Document',
          badgeColor: 'bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800',
        };
    }
  };

  return (
    <div className="relative border-l-2 border-slate-200 dark:border-slate-700 ml-4 py-3 space-y-8">
      {events.map((event, idx) => {
        const meta = getEventMeta(event);
        const isDocTalk = event.type.startsWith('DOCTALK_');
        const isOpinion = event.type === 'DOCTALK_OPINION';
        const isExpanded = expandedOpinions[idx] ?? true; // default opinions expanded

        return (
          <div key={idx} className="relative pl-7 group">
            {/* Timeline Node Dot */}
            <div
              className={cn(
                'absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-2 border-white dark:border-slate-800 shadow-sm transition-transform duration-200 group-hover:scale-125',
                meta.dotBg
              )}
            />

            <div className="space-y-2">
              {/* Header: Timestamp and Title */}
              <div className="flex flex-wrap items-center gap-2">
                {event.date && (
                  <span className="inline-flex items-center gap-1 text-xs font-mono font-bold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md">
                    <Clock className="w-3 h-3 text-slate-400" />
                    {formatTime(event.date)}
                    <span className="text-slate-300 dark:text-slate-600">·</span>
                    <span className="text-[11px] font-sans font-medium text-slate-400">
                      {formatDate(event.date)}
                    </span>
                  </span>
                )}

                <span
                  className={cn(
                    'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold border shadow-xs',
                    meta.badgeColor
                  )}
                >
                  {meta.icon}
                  {meta.title}
                </span>

                {event.specialty && (
                  <span className="text-[11px] font-bold text-teal-700 dark:text-teal-300 bg-teal-50 dark:bg-teal-950/40 px-2 py-0.5 rounded-md border border-teal-200 dark:border-teal-800">
                    {event.specialty}
                  </span>
                )}
              </div>

              {/* Event Body */}
              {isDocTalk ? (
                <div className="mt-2 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 p-4 space-y-3">
                  {/* Doctor & Hospital Attribution */}
                  {(event.specialist_name || event.specialist_hospital) && (
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600 dark:text-slate-300">
                      {event.specialist_name && (
                        <div className="flex items-center gap-1.5 font-semibold text-slate-900 dark:text-slate-100">
                          <User className="w-3.5 h-3.5 text-teal-600" />
                          <span>Specialist: {event.specialist_name}</span>
                        </div>
                      )}
                      {event.specialist_hospital && (
                        <div className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
                          <Building2 className="w-3.5 h-3.5 text-slate-400" />
                          <span>{event.specialist_hospital}</span>
                        </div>
                      )}
                      {event.urgency && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-amber-100 dark:bg-amber-900/50 text-amber-800 dark:text-amber-200">
                          {event.urgency}
                        </span>
                      )}
                      {event.duration_minutes && (
                        <span className="text-[11px] text-slate-500">
                          {event.duration_minutes} min consultation
                        </span>
                      )}
                    </div>
                  )}

                  {/* Consultation Request Reason */}
                  {event.reason && (
                    <div className="text-xs text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-slate-200 dark:border-slate-700/80">
                      <span className="font-bold text-slate-500 dark:text-slate-400">Reason: </span>
                      <span>{event.reason}</span>
                    </div>
                  )}

                  {/* Full Specialist Opinion Section */}
                  {isOpinion && (
                    <div className="space-y-3 pt-1">
                      <button
                        type="button"
                        onClick={() => toggleOpinion(idx)}
                        className="w-full flex items-center justify-between text-xs font-bold text-indigo-700 dark:text-indigo-300 hover:text-indigo-900 dark:hover:text-indigo-100 transition-colors"
                      >
                        <span className="flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5" />
                          Specialist Assessment & Advice Details
                        </span>
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </button>

                      {isExpanded && (
                        <div className="space-y-3.5 border-t border-slate-200 dark:border-slate-700 pt-3">
                          {/* Clinical Opinion */}
                          {event.clinical_opinion && (
                            <div>
                              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                                Clinical Opinion
                              </p>
                              <p className="text-xs leading-relaxed text-slate-800 dark:text-slate-200 bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
                                {event.clinical_opinion}
                              </p>
                            </div>
                          )}

                          {/* Recommendations */}
                          {event.recommendations && (
                            <div>
                              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                                Recommendations
                              </p>
                              <div className="text-xs bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/60 rounded-lg p-3 text-slate-800 dark:text-slate-200">
                                {Array.isArray(event.recommendations) ? (
                                  <ul className="list-disc list-inside space-y-1">
                                    {event.recommendations.map((rec: any, rIdx: number) => (
                                      <li key={rIdx} className="leading-relaxed">
                                        {typeof rec === 'string'
                                          ? rec
                                          : rec.text || rec.recommendation || JSON.stringify(rec)}
                                      </li>
                                    ))}
                                  </ul>
                                ) : typeof event.recommendations === 'string' ? (
                                  <p className="leading-relaxed whitespace-pre-line">
                                    {event.recommendations}
                                  </p>
                                ) : (
                                  <pre className="text-[11px] font-mono whitespace-pre-wrap">
                                    {JSON.stringify(event.recommendations, null, 2)}
                                  </pre>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Further Evaluation */}
                          {event.further_evaluation && (
                            <div>
                              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                                Further Evaluation
                              </p>
                              <p className="text-xs text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-slate-200 dark:border-slate-700">
                                {event.further_evaluation}
                              </p>
                            </div>
                          )}

                          {/* Follow-up */}
                          {event.follow_up && (
                            <div>
                              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                                Follow-Up Advice
                              </p>
                              <p className="text-xs text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-slate-200 dark:border-slate-700">
                                {event.follow_up}
                              </p>
                            </div>
                          )}

                          {/* Safety Policy Notice */}
                          <div className="flex items-start gap-2 p-2.5 rounded-lg bg-slate-100 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-[11px] text-slate-500 dark:text-slate-400">
                            <ShieldCheck className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                            <span>
                              <strong>Clinical Protection:</strong> Specialist recommendations are advisory.
                              DocTalk never automatically overwrites patient facts, diagnoses, prescriptions,
                              or clinical summaries. Treating doctor retains sole decision authority.
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                /* Standard Document / Encounter Entry */
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5 mt-1">
                    {meta.title}
                  </h4>

                  {event.entities && event.entities.length > 0 && (
                    <div className="mt-2.5 flex flex-wrap gap-2">
                      {event.entities.map((ent: DocumentEntity, eIdx: number) => {
                        const val = ent.value as Record<string, string>;
                        return (
                          <span
                            key={eIdx}
                            className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-600"
                          >
                            {val.name || val.test || val.condition || val.procedure || ent.type}
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
