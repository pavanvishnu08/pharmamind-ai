import React from 'react';
import { AlertTriangle, ShieldCheck, Info } from 'lucide-react';

interface SafetyBannerProps {
  compact?: boolean;
}

export const SafetyBanner: React.FC<SafetyBannerProps> = ({ compact = false }) => {
  if (compact) {
    return (
      <div className="bg-amber-950/40 border border-amber-800/60 rounded-lg px-4 py-2 flex items-center gap-2 text-xs text-amber-200">
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
        <span>
          <strong>Educational & Informational Platform:</strong> Not for diagnosis, individual prescribing, or dosage calculations. Always consult a qualified physician or pharmacist.
        </span>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-slate-900 via-navy-950 to-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg mb-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-400 shrink-0">
            <ShieldCheck className="w-5 h-5 text-teal-400" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Biomedical Evidence & Clinical Provenance Protocol
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-teal-900/60 text-teal-300 border border-teal-700/50">
                Authoritative Grounding
              </span>
            </h4>
            <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
              PharmaMind AI synthesizes evidence from FDA DailyMed, NLM RxNorm, and PubMed literature.
              Every factual assertion is mapped to source citations. Experimental ML link predictions are strictly labeled and never represented as confirmed clinical drug interactions.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 self-end md:self-auto shrink-0">
          <span className="text-xs font-mono text-slate-400 flex items-center gap-1.5 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            Educational Use Only
          </span>
        </div>
      </div>
    </div>
  );
};

