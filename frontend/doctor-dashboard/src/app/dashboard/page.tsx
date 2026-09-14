'use client';

import React, { useEffect, useState } from 'react';
import DoctorLayout from '@/components/layout/DoctorLayout';
import { getQueue } from '@/lib/api/queue';
import { QueueItem } from '@/lib/api/types';
import { Users, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getQueue().then(data => {
      setQueue(data);
      setLoading(false);
    });
  }, []);

  const waiting = queue.filter(q => q.status === 'WAITING').length;
  const inConsultation = queue.filter(q => q.status === 'IN_CONSULTATION').length;
  const completed = queue.filter(q => q.status === 'COMPLETED').length;
  const highPriority = queue.filter(q => q.priority === 'HIGH' && q.status !== 'COMPLETED').length;

  return (
    <DoctorLayout>
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">Good morning, Dr. Sharma</h2>
          <p className="text-slate-500 mt-1">Here is your overview for today.</p>
        </div>

        {loading ? (
          <div className="flex justify-center p-12"><Clock className="animate-spin text-slate-400" /></div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col items-center">
                <div className="bg-blue-50 text-blue-600 p-3 rounded-full mb-4">
                  <Users className="w-6 h-6" />
                </div>
                <div className="text-3xl font-bold text-slate-800">{waiting}</div>
                <div className="text-sm font-medium text-slate-500 mt-1 uppercase tracking-wider">Waiting</div>
              </div>
              
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col items-center">
                <div className="bg-amber-50 text-amber-600 p-3 rounded-full mb-4">
                  <Clock className="w-6 h-6" />
                </div>
                <div className="text-3xl font-bold text-slate-800">{inConsultation}</div>
                <div className="text-sm font-medium text-slate-500 mt-1 uppercase tracking-wider">In Consultation</div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-red-200 p-6 flex flex-col items-center border-t-4 border-t-red-500">
                <div className="bg-red-50 text-red-600 p-3 rounded-full mb-4">
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <div className="text-3xl font-bold text-slate-800">{highPriority}</div>
                <div className="text-sm font-medium text-slate-500 mt-1 uppercase tracking-wider">High Priority</div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col items-center">
                <div className="bg-teal-50 text-teal-600 p-3 rounded-full mb-4">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div className="text-3xl font-bold text-slate-800">{completed}</div>
                <div className="text-sm font-medium text-slate-500 mt-1 uppercase tracking-wider">Completed</div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center">
                <h3 className="font-semibold text-slate-800">High Priority Patients</h3>
                <Link href="/queue" className="text-sm text-teal-600 hover:text-teal-700 font-medium">View All Queue</Link>
              </div>
              <div className="divide-y divide-slate-100">
                {queue.filter(q => q.priority === 'HIGH' && q.status !== 'COMPLETED').map(patient => (
                  <div key={patient.id} className="p-6 flex items-center justify-between hover:bg-slate-50 transition-colors">
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 rounded-full bg-red-100 text-red-600 flex items-center justify-center font-bold">
                        {patient.name.charAt(0)}
                      </div>
                      <div>
                        <h4 className="font-semibold text-slate-900">{patient.name}</h4>
                        <p className="text-sm text-slate-500">{patient.age}M • {patient.chief_complaint}</p>
                      </div>
                    </div>
                    <Link 
                      href={`/encounters/${patient.id}`} 
                      className="px-4 py-2 bg-slate-900 text-white text-sm font-medium rounded-lg hover:bg-slate-800 transition-colors"
                    >
                      Open Encounter
                    </Link>
                  </div>
                ))}
                {queue.filter(q => q.priority === 'HIGH' && q.status !== 'COMPLETED').length === 0 && (
                  <div className="p-6 text-center text-slate-500">No high priority patients waiting.</div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </DoctorLayout>
  );
}
