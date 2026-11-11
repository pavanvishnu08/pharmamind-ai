import React from 'react';
import {
  LayoutDashboard,
  Pill,
  MessageSquareCode,
  GitFork,
  Network,
  BookOpenText,
  BarChart3,
  History,
  Settings,
  ShieldCheck,
  Home
} from 'lucide-react';
import { PageId } from '../types';

interface SidebarProps {
  currentPage: PageId;
  onNavigate: (page: PageId) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPage, onNavigate }) => {
  const navItems: { id: PageId; label: string; icon: React.ReactNode; category?: string; badge?: string }[] = [
    { id: 'landing', label: 'Home & Overview', icon: <Home className="w-4 h-4" /> },
    { id: 'dashboard', label: 'Main Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'drug-search', label: 'Drug Monographs', icon: <Pill className="w-4 h-4" />, badge: 'FDA/RxNorm' },
    { id: 'assistant', label: 'AI Drug Assistant', icon: <MessageSquareCode className="w-4 h-4" />, badge: 'RAG' },
    { id: 'interactions', label: 'Interaction Explorer', icon: <GitFork className="w-4 h-4" />, badge: 'DDI' },
    { id: 'graph', label: 'Knowledge Graph', icon: <Network className="w-4 h-4" />, badge: 'Graph ML' },
    { id: 'literature', label: 'Research Literature', icon: <BookOpenText className="w-4 h-4" />, badge: 'PubMed' },
    { id: 'evaluation', label: 'AI Model Benchmarks', icon: <BarChart3 className="w-4 h-4" />, badge: 'Metrics' },
    { id: 'history', label: 'Consultation History', icon: <History className="w-4 h-4" /> },
    { id: 'settings', label: 'Settings & Hardware', icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800/80 flex flex-col shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="p-4 space-y-1">
        <p className="px-3 text-[10px] font-mono uppercase tracking-wider text-slate-500 mb-2">
          Biomedical Modules
        </p>
        {navItems.map((item) => {
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-teal-950/80 to-blue-950/40 text-teal-300 border border-teal-800/60 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className={isActive ? 'text-teal-400' : 'text-slate-400'}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                    isActive
                      ? 'bg-teal-900 text-teal-200 border border-teal-700/60'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="mt-auto p-4 border-t border-slate-800/80">
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3 text-xs">
          <div className="flex items-center gap-2 text-teal-400 font-semibold mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>Integrity Tier 1</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-snug">
            All pharmacological claims anchored to verified provenance IDs.
          </p>
        </div>
      </div>
    </aside>
  );
};

