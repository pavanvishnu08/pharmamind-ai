import React from 'react';
import { History, Clock, FileText, ChevronRight, Download, Trash2 } from 'lucide-react';
import { PageId } from '../types';

interface UserHistoryPageProps {
  onNavigate: (page: PageId) => void;
}

export const UserHistoryPage: React.FC<UserHistoryPageProps> = ({ onNavigate }) => {
  const historyItems = [
    {
      id: 'h1',
      type: 'AI_CONSULTATION',
      query: 'What is the pharmacological mechanism of Metformin?',
      timestamp: '2026-01-15 11:42 UTC',
      confidence: 'VERIFIED_AUTHORITATIVE',
      citationsCount: 2,
    },
    {
      id: 'h2',
      type: 'INTERACTION_CHECK',
      query: 'Warfarin + Aspirin Interaction Check',
      timestamp: '2026-01-15 10:15 UTC',
      confidence: 'HIGH_RISK_ALERT',
      citationsCount: 1,
    },
    {
      id: 'h3',
      type: 'MONOGRAPH_SEARCH',
      query: 'Simvastatin Monograph Inspection',
      timestamp: '2026-01-14 16:30 UTC',
      confidence: 'VERIFIED_AUTHORITATIVE',
      citationsCount: 3,
    },
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <History className="w-5 h-5 text-teal-400" />
            Consultation History & Evidence Audit
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Audit log of prior biomedical inquiries, interaction assessments, and verified citations.
          </p>
        </div>

        <button
          onClick={() => alert('Audit log exported as JSON format.')}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 font-medium transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export Audit Log</span>
        </button>
      </div>

      <div className="space-y-3">
        {historyItems.map((item) => (
          <div
            key={item.id}
            className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-teal-400">
                  {item.type}
                </span>
                <span className="text-xs font-mono text-slate-500">{item.timestamp}</span>
              </div>
              <h4 className="text-sm font-semibold text-white">{item.query}</h4>
              <p className="text-xs text-slate-400">
                Grounding: <span className="text-emerald-400">{item.confidence}</span> • {item.citationsCount} Citations Indexed
              </p>
            </div>

            <button
              onClick={() => onNavigate('assistant')}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1 self-end sm:self-auto"
            >
              <span>Review Monograph</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

