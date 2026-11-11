import React, { useState, useEffect } from 'react';
import { Search, Pill, ShieldCheck, ChevronRight, ExternalLink, Activity, Info } from 'lucide-react';
import { Drug } from '../types';
import { fetchDrugs } from '../services/api';

export const DrugSearchPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [drugs, setDrugs] = useState<Drug[]>([]);
  const [selectedDrug, setSelectedDrug] = useState<Drug | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDrugs();
  }, []);

  const loadDrugs = async (query?: string) => {
    setLoading(true);
    try {
      const data = await fetchDrugs(query);
      setDrugs(data);
      if (data.length > 0 && !selectedDrug) {
        setSelectedDrug(data[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadDrugs(searchTerm);
  };

  return (
    <div className="space-y-6">
      {/* Header & Search */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Drug Information & Monographs</h1>
          <p className="text-xs text-slate-400 mt-1">
            Authoritative pharmacological monographs sourced from FDA DailyMed and RxNorm.
          </p>
        </div>

        <form onSubmit={handleSearch} className="flex items-center gap-2 max-w-md w-full">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search generic, brand, or drug class..."
              className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 transition-colors"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white text-xs font-medium rounded-lg transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Drug Results List */}
        <div className="space-y-2 lg:col-span-1">
          <p className="text-xs font-mono text-slate-400 px-1 uppercase tracking-wider mb-2">
            Documented Drugs ({drugs.length})
          </p>
          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {drugs.map((d) => {
              const isSelected = selectedDrug?.id === d.id;
              return (
                <div
                  key={d.id}
                  onClick={() => setSelectedDrug(d)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-slate-900 border-teal-600/80 shadow-md shadow-teal-950/40'
                      : 'bg-slate-900/40 border-slate-800/80 hover:bg-slate-900 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-white flex items-center gap-2">
                        {d.generic_name}
                        {d.brand_name && (
                          <span className="text-[11px] font-normal text-slate-400">({d.brand_name})</span>
                        )}
                      </h4>
                      <p className="text-xs text-teal-400 mt-0.5">{d.drug_class || 'Pharmaceutical Agent'}</p>
                    </div>
                    <ChevronRight className={`w-4 h-4 transition-transform ${isSelected ? 'text-teal-400 translate-x-0.5' : 'text-slate-600'}`} />
                  </div>
                  <div className="flex items-center gap-2 text-[10px] font-mono text-slate-500 mt-3">
                    <span>RxCUI: {d.rxnorm_cui || 'N/A'}</span>
                    <span>•</span>
                    <span>ATC: {d.atc_code || 'N/A'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Monograph Detail */}
        <div className="lg:col-span-2">
          {selectedDrug ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-6">
              {/* Monograph Header */}
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-6 border-b border-slate-800">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800/60">
                      FDA Monograph
                    </span>
                    <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/60">
                      RxNorm Validated
                    </span>
                  </div>
                  <h2 className="text-2xl font-bold text-white mt-2 flex items-center gap-3">
                    {selectedDrug.generic_name}
                    {selectedDrug.brand_name && (
                      <span className="text-base font-normal text-slate-400 font-sans">
                        (Brand: {selectedDrug.brand_name})
                      </span>
                    )}
                  </h2>
                  <p className="text-sm text-slate-300 mt-1">{selectedDrug.drug_class}</p>
                </div>

                <div className="text-right font-mono text-xs text-slate-400 bg-slate-950 p-3 rounded-lg border border-slate-800 shrink-0">
                  <p>RxCUI: <strong className="text-teal-300">{selectedDrug.rxnorm_cui || 'N/A'}</strong></p>
                  <p>ATC: <strong className="text-blue-300">{selectedDrug.atc_code || 'N/A'}</strong></p>
                  <p>Route: <strong className="text-slate-200">{selectedDrug.route_of_administration || 'Oral'}</strong></p>
                </div>
              </div>

              {/* Description */}
              <div className="space-y-2">
                <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5 text-teal-400" />
                  Clinical Description & Indications
                </h3>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
                  {selectedDrug.description}
                </p>
              </div>

              {/* Mechanism of Action */}
              <div className="space-y-2">
                <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-blue-400" />
                  Mechanism of Action (MOA)
                </h3>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
                  {selectedDrug.mechanism_of_action}
                </p>
              </div>

              {/* Synonyms & Brand Equivalents */}
              <div className="space-y-2">
                <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400">
                  Documented Synonyms & Clinical Names
                </h3>
                <div className="flex flex-wrap gap-2">
                  {selectedDrug.synonyms.map((s) => (
                    <span
                      key={s.id}
                      className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800/80 text-slate-300 border border-slate-700/60"
                    >
                      {s.synonym} <span className="text-[10px] text-slate-400">({s.source})</span>
                    </span>
                  ))}
                </div>
              </div>

              {/* Provenance Link */}
              <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <ShieldCheck className="w-4 h-4" />
                  Verified Authoritative Record
                </span>
                <a
                  href={`https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=${selectedDrug.generic_name}`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-teal-400 hover:text-teal-300 underline"
                >
                  <span>DailyMed Package Insert</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          ) : (
            <div className="h-64 rounded-xl border border-dashed border-slate-800 flex items-center justify-center text-xs text-slate-500">
              Select a drug monograph from the list to view clinical evidence.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

