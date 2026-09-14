import React, { useState } from 'react';
import { CheckCircle2, Edit2, AlertCircle, Sparkles, Clock } from 'lucide-react';
import { editSummary, verifySummary } from '@/lib/api/summaries';
import { ClinicalSummary, SummarySection } from '@/lib/api/types';

interface SummaryPanelProps {
  summaryId: string;
  summaryData: ClinicalSummary;
  onUpdate: () => void;
}

export default function SummaryPanel({ summaryId, summaryData, onUpdate }: SummaryPanelProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState<string>("");
  const [verifying, setVerifying] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  if (!summaryData || !summaryData.latest_version) {
    return <div className="p-4 text-slate-500">Summary not generated yet.</div>;
  }

  const sections = summaryData.latest_version.structured_sections || [];
  const status = summaryData.status || 'AI_DRAFT';

  const handleEdit = () => {
    // Flatten for simple editing in MVP
    const text = sections.map((s: SummarySection) => `[${s.title}]\n${s.content}`).join('\n\n');
    setEditedContent(text);
    setIsEditing(true);
  };

  const handleSaveEdit = async () => {
    try {
      // Very crude parse back to sections for MVP
      const newSections = editedContent.split('\n\n').map(block => {
        const lines = block.split('\n');
        const title = lines[0].replace(/\[|\]/g, '');
        return { title, content: lines.slice(1).join('\n'), section_type: 'UNKNOWN' };
      });
      
      await editSummary(summaryId, { structured_sections: newSections });
      setIsEditing(false);
      onUpdate();
    } catch (e) {
      console.error(e);
    }
  };

  const handleVerify = async () => {
    try {
      setVerifying(true);
      await verifySummary(summaryId);
      setShowConfirm(false);
      onUpdate();
    } catch (e) {
      console.error(e);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-full">
      <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center shrink-0">
        <div className="flex items-center space-x-3">
          <h3 className="font-bold text-slate-800 text-lg">AI Clinical Summary</h3>
          {status === 'AI_DRAFT' && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
              <Sparkles className="w-3 h-3 mr-1" /> AI GENERATED
            </span>
          )}
          {status === 'DOCTOR_EDITED' && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
              <Edit2 className="w-3 h-3 mr-1" /> DOCTOR EDITED
            </span>
          )}
          {status === 'DOCTOR_VERIFIED' && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-teal-100 text-teal-800 border border-teal-200">
              <CheckCircle2 className="w-3 h-3 mr-1" /> DOCTOR VERIFIED
            </span>
          )}
        </div>
        
        <div className="flex space-x-2">
           {status !== 'DOCTOR_VERIFIED' && !isEditing && (
             <button onClick={handleEdit} className="px-3 py-1.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors">
               Edit
             </button>
           )}
           {status !== 'DOCTOR_VERIFIED' && !isEditing && (
             <button onClick={() => setShowConfirm(true)} className="px-3 py-1.5 text-sm font-medium text-white bg-teal-600 rounded-md hover:bg-teal-700 transition-colors shadow-sm">
               Verify Summary
             </button>
           )}
        </div>
      </div>

      <div className="p-6 overflow-y-auto flex-1">
        {status === 'AI_DRAFT' && !isEditing && (
          <div className="mb-6 bg-blue-50/50 rounded-lg p-4 flex items-start text-sm text-blue-800 border border-blue-100">
            <AlertCircle className="w-5 h-5 text-blue-500 mt-0.5 mr-3 shrink-0" />
            <p><strong>Requires Verification:</strong> This is an AI-generated draft. Review the information carefully against the source documents and clinical history before verifying. AI assists, Doctor decides.</p>
          </div>
        )}

        {isEditing ? (
          <div className="space-y-4 h-full flex flex-col">
            <textarea
              className="w-full flex-1 p-4 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500 resize-none font-mono text-sm"
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
            />
            <div className="flex justify-end space-x-3 pt-2">
              <button onClick={() => setIsEditing(false)} className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-md">Cancel</button>
              <button onClick={handleSaveEdit} className="px-4 py-2 text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-md shadow-sm">Save Changes</button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {sections.map((section: SummarySection, i: number) => (
              <div key={i}>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">{section.title}</h4>
                <div className="text-slate-800 leading-relaxed font-medium">
                   {section.content || <span className="text-slate-400 font-normal italic">Not documented</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {showConfirm && (
        <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-slate-900 mb-2">Verify Clinical Summary?</h3>
            <p className="text-slate-600 mb-6 text-sm leading-relaxed">
              You are verifying an AI-generated clinical summary. Please review the information before confirming. This will lock the summary version.
            </p>
            <div className="flex justify-end space-x-3">
              <button onClick={() => setShowConfirm(false)} className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-lg">Cancel</button>
              <button onClick={handleVerify} disabled={verifying} className="px-4 py-2 text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 rounded-lg shadow-sm flex items-center">
                {verifying ? <Clock className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle2 className="w-4 h-4 mr-2" />}
                Confirm Verification
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
