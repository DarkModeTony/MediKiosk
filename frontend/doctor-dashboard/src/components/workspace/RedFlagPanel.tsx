import React from 'react';
import { AlertTriangle, Info } from 'lucide-react';
import { RedFlag } from '@/lib/api/types';

interface RedFlagPanelProps {
  flags: RedFlag[];
}

export default function RedFlagPanel({ flags }: RedFlagPanelProps) {
  if (!flags || flags.length === 0) return null;

  return (
    <div className="bg-red-50 border-l-4 border-red-500 rounded-r-xl shadow-sm p-5 mb-6">
      <div className="flex items-start">
        <AlertTriangle className="h-6 w-6 text-red-600 mt-0.5 mr-3 shrink-0" />
        <div className="flex-1">
          <h3 className="text-lg font-bold text-red-800 tracking-tight">HIGH PRIORITY ALERTS</h3>
          
          <div className="mt-3 space-y-4">
            {flags.map((flag, idx) => (
              <div key={idx} className="bg-white/60 rounded-lg p-4 border border-red-100">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold text-red-900">{flag.rule_name.replace(/_/g, ' ')}</h4>
                    <div className="mt-2 text-sm text-red-800 flex items-center">
                       <Info className="w-4 h-4 mr-1 opacity-70" />
                       Source Evidence: 
                       <span className="font-medium ml-1">
                         {Object.values(flag.evidence || {}).join(' • ')}
                       </span>
                    </div>
                  </div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-600 text-white shadow-sm">
                    {flag.severity}
                  </span>
                </div>
              </div>
            ))}
          </div>
          
          <p className="text-xs text-red-600/80 mt-4 italic">
            Red flags are deterministically calculated by the backend clinical engine. Read-only.
          </p>
        </div>
      </div>
    </div>
  );
}
