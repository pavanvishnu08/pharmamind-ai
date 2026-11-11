import React from 'react';
import { Pill, GitFork, Network, BookOpen, ShieldCheck, Cpu, ArrowRight, Sparkles, CheckCircle2 } from 'lucide-react';
import { PageId } from '../types';

interface LandingPageProps {
  onNavigate: (page: PageId) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  return (
    <div className="space-y-12 py-4">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950 border border-slate-800 p-8 md:p-12 shadow-2xl">
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-20 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-3xl space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-950/80 border border-teal-800/80 text-teal-300 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Production Biomedical NLP & Knowledge Graph Platform</span>
          </div>

          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Evidence-Grounded Drug Intelligence for Healthcare Research
          </h1>

          <p className="text-base md:text-lg text-slate-300 leading-relaxed font-light">
            PharmaMind AI bridges transformer language models, biomedical knowledge graphs, and semantic retrieval to provide verifiable pharmaceutical insights with strict clinical provenance.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-4">
            <button
              onClick={() => onNavigate('assistant')}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-blue-600 hover:from-teal-400 hover:to-blue-500 text-white font-medium text-sm flex items-center gap-2 shadow-lg shadow-teal-500/25 transition-all"
            >
              <span>Consult AI Drug Assistant</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate('interactions')}
              className="px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-medium text-sm flex items-center gap-2 transition-all"
            >
              <GitFork className="w-4 h-4 text-teal-400" />
              <span>Explore Drug Interactions</span>
            </button>
            <button
              onClick={() => onNavigate('evaluation')}
              className="px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-medium text-sm flex items-center gap-2 transition-all"
            >
              <Cpu className="w-4 h-4 text-blue-400" />
              <span>Inspect AI Benchmarks</span>
            </button>
          </div>
        </div>
      </section>

      {/* Core Architectural Pillars */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div
          onClick={() => onNavigate('drug-search')}
          className="p-6 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-teal-700/60 transition-all cursor-pointer group"
        >
          <div className="w-12 h-12 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400 mb-4 group-hover:scale-105 transition-transform">
            <Pill className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white mb-2 group-hover:text-teal-300 transition-colors">
            Authoritative Drug Monographs
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Direct integration with FDA DailyMed structured labeling and NLM RxNorm standardized clinical drug identifiers.
          </p>
        </div>

        <div
          onClick={() => onNavigate('interactions')}
          className="p-6 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-blue-700/60 transition-all cursor-pointer group"
        >
          <div className="w-12 h-12 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4 group-hover:scale-105 transition-transform">
            <GitFork className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white mb-2 group-hover:text-blue-300 transition-colors">
            Drug-Drug Interaction Intelligence
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Multi-drug clinical risk assessment showing pharmacodynamics, CYP450 metabolism competitions, and explicit uncertainty statements.
          </p>
        </div>

        <div
          onClick={() => onNavigate('graph')}
          className="p-6 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-cyan-700/60 transition-all cursor-pointer group"
        >
          <div className="w-12 h-12 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4 group-hover:scale-105 transition-transform">
            <Network className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white mb-2 group-hover:text-cyan-300 transition-colors">
            Biomedical Knowledge Graph & ML
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Multi-relational graph connecting drugs, biological targets, indications, and adverse effects with Node2Vec link prediction evaluation.
          </p>
        </div>
      </section>

      {/* Provenance & Four-Tier Evidence Grounding */}
      <section className="bg-slate-900/40 border border-slate-800 rounded-xl p-8">
        <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-teal-400" />
          Four-Tier Evidence Classification Hierarchy
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-4 rounded-lg bg-slate-950 border border-teal-800/40">
            <span className="font-mono text-[10px] text-teal-400 font-bold uppercase tracking-wider block mb-1">
              Tier 1: Authoritative
            </span>
            <p className="font-medium text-slate-200 mb-1">FDA DailyMed & RxNorm</p>
            <p className="text-slate-400 text-[11px]">Legally binding, regulatory package inserts and standardized nomenclature.</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-950 border border-blue-800/40">
            <span className="font-mono text-[10px] text-blue-400 font-bold uppercase tracking-wider block mb-1">
              Tier 2: Scientific Literature
            </span>
            <p className="font-medium text-slate-200 mb-1">PubMed & PMC Open Access</p>
            <p className="text-slate-400 text-[11px]">Peer-reviewed observational studies and clinical trials with PMID provenance.</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-950 border border-purple-800/40">
            <span className="font-mono text-[10px] text-purple-400 font-bold uppercase tracking-wider block mb-1">
              Tier 3: Experimental ML
            </span>
            <p className="font-medium text-slate-200 mb-1">Graph ML Link Predictions</p>
            <p className="text-slate-400 text-[11px]">Strictly labeled experimental hypotheses; never presented as clinical facts.</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-950 border border-amber-800/40">
            <span className="font-mono text-[10px] text-amber-400 font-bold uppercase tracking-wider block mb-1">
              Tier 4: Signals & Uncertainties
            </span>
            <p className="font-medium text-slate-200 mb-1">FAERS Post-Marketing Signals</p>
            <p className="text-slate-400 text-[11px]">Spontaneous reporting signals explicitly not establishing causality.</p>
          </div>
        </div>
      </section>
    </div>
  );
};

