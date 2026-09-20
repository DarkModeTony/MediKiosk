import React, { useState } from 'react';
import { FileText, Eye, Check, Edit3 } from 'lucide-react';
import { TimelineEvent, DocumentEntity } from '@/lib/api/types';

interface DocumentViewerProps {
  timelineEvents: TimelineEvent[];
}

export default function DocumentViewer({ timelineEvents }: DocumentViewerProps) {
  const docs = timelineEvents.filter(e => e.type === 'DOCUMENT');
  const [selectedDoc, setSelectedDoc] = useState<TimelineEvent | null>(null);
  
  if (docs.length === 0) {
    return <div className="p-6 text-slate-500 bg-slate-50 rounded-xl border border-slate-200">No medical documents uploaded for this patient.</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-full">
      <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
        <h3 className="font-bold text-slate-800 text-lg">Medical Documents & Source Provenance</h3>
      </div>
      
      <div className="flex flex-1 h-[400px]">
        {/* Document List */}
        <div className="w-1/3 border-r border-slate-200 bg-slate-50/50 overflow-y-auto">
          {docs.map((doc, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedDoc(doc)}
              className={`w-full text-left p-4 border-b border-slate-200 transition-colors ${
                selectedDoc?.document_id === doc.document_id ? 'bg-blue-50 border-l-4 border-l-blue-600' : 'hover:bg-slate-100 border-l-4 border-l-transparent'
              }`}
            >
              <div className="flex items-center space-x-3 mb-1">
                <FileText className={`w-5 h-5 ${selectedDoc?.document_id === doc.document_id ? 'text-blue-600' : 'text-slate-400'}`} />
                <span className="font-semibold text-slate-800 text-sm truncate">{doc.document_type}</span>
              </div>
              <p className="text-xs text-slate-500 ml-8">
                {new Date(doc.date).toLocaleDateString()}
              </p>
            </button>
          ))}
        </div>
        
        {/* Document Detail */}
        <div className="w-2/3 p-6 overflow-y-auto bg-slate-50">
          {selectedDoc ? (
            <div className="space-y-6">
              <div className="flex justify-between items-center bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                <div>
                   <h4 className="font-bold text-slate-900">{selectedDoc.document_type}</h4>
                   <p className="text-sm text-slate-500">{new Date(selectedDoc.date).toLocaleDateString()}</p>
                </div>
                <button className="flex items-center px-3 py-1.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50">
                  <Eye className="w-4 h-4 mr-2" /> View Original Image
                </button>
              </div>
              
              <div>
                <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Extracted Entities</h5>
                {Boolean(selectedDoc.entities && selectedDoc.entities.length > 0) ? (
                  <div className="space-y-3">
                    {selectedDoc.entities!.map((entity: DocumentEntity, i: number) => {
                      const val = entity.value as Record<string, string>;
                      return (
                      <div key={i} className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                        <div className="flex justify-between items-start mb-2">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800 uppercase tracking-wide">
                            {entity.type.replace('_', ' ')}
                          </span>
                          {entity.status === 'AI_EXTRACTED' ? (
                            <span className="inline-flex items-center text-xs font-medium text-slate-500">
                              <Check className="w-3 h-3 mr-1" /> Extracted
                            </span>
                          ) : (
                            <span className="inline-flex items-center text-xs font-medium text-teal-600">
                              <Edit3 className="w-3 h-3 mr-1" /> Corrected
                            </span>
                          )}
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-slate-500 mb-1">Structured Value</p>
                            <div className="font-medium text-slate-900 text-sm">
                              {entity.type === 'MEDICATION' ? (
                                <>{val.name} {val.dose} {val.frequency}</>
                              ) : entity.type === 'LAB_RESULT' ? (
                                <>{val.test}: <span className={val.status === 'Abnormal' ? 'text-red-600 font-bold' : ''}>{val.result} {val.unit}</span></>
                              ) : (
                                JSON.stringify(val)
                              )}
                            </div>
                          </div>
                          <div className="pl-4 border-l border-slate-200">
                            <p className="text-sm text-slate-500 mb-1">Raw Source Text</p>
                            <div className="font-mono text-xs text-slate-700 bg-slate-50 p-2 rounded">
                              {entity.source_text || "Source details not available"}
                            </div>
                          </div>
                        </div>
                        
                      </div>
                    )})}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 italic">No clinical entities extracted from this document.</p>
                )}
              </div>
            </div>
          ) : (
             <div className="h-full flex items-center justify-center text-slate-400">
               Select a document to view extraction details and source provenance.
             </div>
          )}
        </div>
      </div>
    </div>
  );
}
