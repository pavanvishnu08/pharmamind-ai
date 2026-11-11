import React from 'react';
import { Pill, Activity, Shield, Database, Cpu, Search, Sparkles } from 'lucide-react';
import { HealthResponse, PageId } from '../types';

interface NavbarProps {
  currentPage: PageId;
  onNavigate: (page: PageId) => void;
  health: HealthResponse | null;
}

export const Navbar: React.FC<NavbarProps> = ({ currentPage, onNavigate, health }) => {
  return (
    <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => onNavigate('landing')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-blue-600 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <Pill className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                PharmaMind <span className="text-teal-400 font-mono text-xs uppercase px-1.5 py-0.5 rounded bg-teal-950/80 border border-teal-800/80">AI</span>
              </span>
              <p className="text-[10px] text-slate-400 font-mono hidden sm:block">Biomedical Intelligence Platform</p>
            </div>
          </div>

          {/* Quick System Telemetry */}
          <div className="hidden lg:flex items-center gap-4 text-xs font-mono text-slate-400 bg-slate-900/60 px-3.5 py-1.5 rounded-full border border-slate-800">
            <div className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-blue-400" />
              <span>DB:</span>
              <span className="text-slate-200">{health?.database.dialect || 'PostgreSQL 18'}</span>
              {health?.database.is_fallback && (
                <span className="text-[10px] px-1 rounded bg-amber-900/50 text-amber-300 border border-amber-800">fallback</span>
              )}
            </div>
            <div className="w-px h-3 bg-slate-800" />
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-teal-400" />
              <span>Free RAM:</span>
              <span className="text-slate-200">{health?.memory.available_gb ? `${health.memory.available_gb} GB` : '2.1 GB'}</span>
            </div>
            <div className="w-px h-3 bg-slate-800" />
            <div className="flex items-center gap-1.5">
              <div className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-teal-400 animate-pulse' : 'bg-amber-400'}`} />
              <span className="text-slate-300 uppercase">{health?.status || 'Active'}</span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate('drug-search')}
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 text-xs text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 rounded-lg transition-colors"
            >
              <Search className="w-3.5 h-3.5 text-slate-400" />
              <span>Search Medicines</span>
            </button>
            <button
              onClick={() => onNavigate('assistant')}
              className="flex items-center gap-2 px-3.5 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-500 hover:to-blue-500 rounded-lg shadow-sm shadow-teal-500/20 transition-all"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>AI Assistant</span>
            </button>
            <button
              onClick={() => onNavigate('auth')}
              className="text-xs text-slate-300 hover:text-white px-3 py-1.5 rounded-lg border border-slate-800 hover:bg-slate-900 transition-colors"
            >
              Sign In
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

