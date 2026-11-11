import React, { useState } from 'react';
import { GitFork, Plus, X, AlertTriangle, ShieldCheck, Info, CheckCircle2 } from 'lucide-react';
import { InteractionCheckResponse } from '../types';
import { checkInteractions } from '../services/api';
import { SafetyBanner } from '../components/SafetyBanner';

export const InteractionExplorerPage: React.FC = () => {
  const [selectedDrugs, setSelectedDrugs] = useState<string[]>(['Warfarin', 'Aspirin']);
  const [newDrugInput, setNewDrugInput] = useState('');
  const [results, setResults] = useState<InteractionCheckResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddDrug = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = newDrugInput.trim();
    if (clean && !selectedDrugs.some((d) => d.toLowerCase() === clean.toLowerCase())) {
      setSelectedDrugs([...selectedDrugs, clean]);
      setNewDrugInput('');
    }
  };

  const handleRemoveDrug = (name: string) => {
    if (selectedDrugs.length > 2) {
      setSelectedDrugs(selectedDrugs.filter((d) => d !== name));
    }
  };

  const handleCheck = async () => {
    if (selectedDrugs.length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const data = await checkInteractions(selectedDrugs);
      setResults(data);
    } catch (err: any) {
      setError(err.message || 'Error checking interactions');
    } finally {
      setLoading(false);
    }
  };

  const quickPresets = [
    ['Warfarin', 'Aspirin'],
    ['Simvastatin', 'Warfarin'],
    ['Lisinopril', 'Aspirin'],
    ['Metformin', 'Simvastatin'],
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <GitFork className="w-5 h-5 text-teal-400" />
          Drug-Drug Interaction (DDI) Explorer
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Evaluate documented medication interactions across active regimens with clinical severity alerts.
        </p>
      </div>

      <SafetyBanner compact />

      {/* Regimen Builder Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h3 className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold">
          Active Medication Regimen
        </h3>

        {/* Selected Drugs Tags */}
        <div className="flex flex-wrap items-center gap-2">
          {selectedDrugs.map((drug) => (
            <span
              key={drug}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-teal-950/80 border border-teal-800/80 text-teal-300 text-xs font-medium"
            >
              <span>{drug}</span>
              {selectedDrugs.length > 2 && (
                <button
                  type="button"
                  onClick={() => handleRemoveDrug(drug)}
                  className="hover:text-red-400 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </span>
          ))}
        </div>

        {/* Add Input & Check Action */}
        <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
          <form onSubmit={handleAddDrug} className="flex items-center gap-2 flex-1 w-full">
            <input
              type="text"
              value={newDrugInput}
              onChange={(e) => setNewDrugInput(e.target.value)}
              placeholder="Add another drug (e.g. Simvastatin, Lisinopril, Metformin)..."
              className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 transition-colors"
            />
            <button
              type="submit"
              className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg flex items-center gap-1.5 transition-colors shrink-0"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add</span>
            </button>
          </form>

          <button
            onClick={handleCheck}
            disabled={loading || selectedDrugs.length < 2}
            className="w-full sm:w-auto px-6 py-2 bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-500 hover:to-blue-500 text-white font-medium text-xs rounded-lg shadow-md shadow-teal-500/20 transition-all disabled:opacity-50 shrink-0"
          >
            {loading ? 'Analyzing Interactions...' : 'Evaluate Regimen Interactions'}
          </button>
        </div>

        {/* Presets */}
        <div className="flex flex-wrap items-center gap-2 pt-2 text-[11px] text-slate-500 font-mono">
          <span>Quick Benchmark Pairs:</span>
          {quickPresets.map((preset, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedDrugs(preset)}
              className="px-2 py-0.5 rounded bg-slate-950 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 transition-colors"
            >
              {preset.join(' + ')}
            </button>
          ))}
        </div>
      </div>

      {/* Results View */}
      {results && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span>Evaluation Findings</span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                {results.total_interactions_found} Interaction{results.total_interactions_found === 1 ? '' : 's'} Identified
              </span>
            </h3>
            <span className="text-[11px] font-mono text-slate-400">
              Regimen: {results.normalized_drugs.join(' • ')}
            </span>
          </div>

          {results.interactions.length > 0 ? (
            <div className="space-y-3">
              {results.interactions.map((item, idx) => (
                <div
                  key={idx}
                  className="bg-slate-900/80 border border-amber-900/40 rounded-xl p-5 shadow-lg space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">
                        {item.source_drug} <span className="text-slate-500">↔</span> {item.target_drug}
                      </span>
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                        {item.evidence_level}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-teal-400">
                      Confidence: {(item.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div className="space-y-1">
                    <h5 className="text-xs font-mono uppercase text-slate-400 font-semibold">
                      Clinical Effect & Pharmacodynamics
                    </h5>
                    <p className="text-xs sm:text-sm text-slate-200 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                      {item.clinical_effect}
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-800/40 text-xs text-amber-200 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <span><strong>Clinical Warning:</strong> {item.warning_notice}</span>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800/60">
                    <span>Source: <strong className="text-slate-300">{item.provenance_source}</strong></span>
                    <span>Retrieved: {item.retrieved_date.slice(0, 10)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-800 text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-teal-400 mx-auto" />
              <h4 className="text-sm font-semibold text-white">No Documented Interaction Found</h4>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                No high-confidence physiological interaction was matched between the selected agents in authoritative FDA DailyMed monographs.
              </p>
            </div>
          )}

          {/* Uncertainty Notice */}
          {results.uncertainty_statement && (
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400 space-y-1">
              <div className="flex items-center gap-1.5 text-slate-300 font-semibold">
                <Info className="w-4 h-4 text-cyan-400" />
                <span>Explicit Evidence Boundary & Uncertainty</span>
              </div>
              <p>{results.uncertainty_statement}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

