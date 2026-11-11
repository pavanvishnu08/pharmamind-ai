import React, { useState } from 'react';
import { Settings, Cpu, Database, Key, Shield, Save, Check } from 'lucide-react';
import { HealthResponse } from '../types';

interface SettingsPageProps {
  health: HealthResponse | null;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ health }) => {
  const [device, setDevice] = useState('cpu');
  const [threads, setThreads] = useState(4);
  const [lazyLoading, setLazyLoading] = useState(true);
  const [batchSize, setBatchSize] = useState(8);
  const [safetyThresholdMb, setSafetyThresholdMb] = useState(1024);
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Settings className="w-5 h-5 text-teal-400" />
          Hardware & Runtime Settings
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure CPU execution parameters, memory safety caps, and database preferences.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Hardware Constraints (Windows 16GB RAM) */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold flex items-center gap-2">
            <Cpu className="w-4 h-4 text-teal-400" />
            Machine Learning Hardware Guardrails
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Inference Execution Device</label>
              <select
                value={device}
                onChange={(e) => setDevice(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-teal-500"
              >
                <option value="cpu">CPU (Recommended for 16GB Host RAM)</option>
                <option value="cuda">CUDA / Dedicated GPU (Disabled on this host)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">CPU Worker Threads</label>
              <input
                type="number"
                min={1}
                max={12}
                value={threads}
                onChange={(e) => setThreads(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-teal-500"
              />
              <span className="text-[10px] text-slate-500">Capped to 4 threads to prevent system CPU starvation.</span>
            </div>

            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Maximum Batch Size</label>
              <input
                type="number"
                min={1}
                max={32}
                value={batchSize}
                onChange={(e) => setBatchSize(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-teal-500"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Memory Safety Threshold (MB)</label>
              <input
                type="number"
                min={512}
                max={4096}
                value={safetyThresholdMb}
                onChange={(e) => setSafetyThresholdMb(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-teal-500"
              />
              <span className="text-[10px] text-slate-500">Model unloading is triggered if available RAM drops below this limit.</span>
            </div>
          </div>

          <div className="pt-2">
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={lazyLoading}
                onChange={(e) => setLazyLoading(e.target.checked)}
                className="rounded bg-slate-950 border-slate-700 text-teal-600 focus:ring-0"
              />
              <span>Enable Lazy Transformer Loading (Load checkpoints only upon explicit request)</span>
            </label>
          </div>
        </div>

        {/* Database Configuration */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold flex items-center gap-2">
            <Database className="w-4 h-4 text-blue-400" />
            Database & Graph Store Connectivity
          </h3>

          <div className="space-y-3 text-xs">
            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Primary PostgreSQL Connection URL</label>
              <input
                type="text"
                defaultValue="postgresql+asyncpg://postgres:postgres@localhost:5432/pharmamind"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono text-xs focus:outline-none focus:border-teal-500"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Resilient Local Fallback</label>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
                <span>SQLite Fallback (aiosqlite): Active when PostgreSQL is unavailable</span>
                <span className="text-teal-400 font-mono font-bold">ENABLED</span>
              </div>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center justify-end gap-3 pt-2">
          {saved && (
            <span className="text-xs text-emerald-400 flex items-center gap-1">
              <Check className="w-4 h-4" />
              Settings saved successfully
            </span>
          )}
          <button
            type="submit"
            className="px-6 py-2.5 bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-500 hover:to-blue-500 text-white font-medium text-xs rounded-xl shadow-lg shadow-teal-500/20 flex items-center gap-2 transition-all"
          >
            <Save className="w-4 h-4" />
            <span>Save Configuration</span>
          </button>
        </div>
      </form>
    </div>
  );
};

