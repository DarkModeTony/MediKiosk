import React from 'react';
import { FileText, User } from 'lucide-react';
import { TimelineEvent, DocumentEntity } from '@/lib/api/types';

interface ClinicalTimelineProps {
  events: TimelineEvent[];
}

export default function ClinicalTimeline({ events }: ClinicalTimelineProps) {
  if (!events || events.length === 0) {
    return <div className="text-slate-500 italic">Timeline events not documented.</div>;
  }

  return (
    <div className="relative border-l-2 border-slate-200 ml-3 py-4 space-y-8">
      {events.map((event, idx) => (
        <div key={idx} className="relative pl-8">
          {/* Timeline Dot */}
          <div className={`absolute -left-[9px] top-1 w-4 h-4 rounded-full border-2 border-white shadow-sm ${
            event.type === 'ENCOUNTER' ? 'bg-teal-500' : 'bg-blue-400'
          }`} />
          
          <div className="flex items-start justify-between">
            <div>
              <span className="inline-flex items-center text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                {event.date_known ? new Date(event.date).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' }) : "Date not documented"}
              </span>
              <h4 className="text-base font-semibold text-slate-900 flex items-center">
                {event.type === 'ENCOUNTER' ? <User className="w-4 h-4 mr-2 text-teal-600" /> : <FileText className="w-4 h-4 mr-2 text-blue-600" />}
                {event.document_type || event.type}
              </h4>
              
              {event.entities?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {event.entities.map((ent: DocumentEntity, eIdx: number) => {
                     const val = ent.value as Record<string, string>;
                     return (
                     <span key={eIdx} className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                       {val.name || val.test || ent.type}
                     </span>
                     );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
