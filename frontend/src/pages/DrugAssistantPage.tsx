import React, { useState } from 'react';
import { Sparkles, Send, ShieldCheck, AlertTriangle, ExternalLink, BookOpen, Clock, Activity, CheckCircle2 } from 'lucide-react';
import { ChatResponse, Citation } from '../types';
import { askAssistant } from '../services/api';
import { SafetyBanner } from '../components/SafetyBanner';

export const DrugAssistantPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [includeExperimental, setIncludeExperimental] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [responses, setResponses] = useState<{ query: string; response: ChatResponse }[]>([
    {
      query: 'What is the pharmacological mechanism of Metformin?',
      response: {
        conversation_id: 'conv-init-1',
        direct_explanation: 'Metformin is an FDA-approved Biguanide antidiabetic agent indicated as first-line pharmacotherapy for type 2 diabetes mellitus.',
        drug_information: {
          generic_name: 'Metformin',
          brand_name: 'Glucophage',
          rxnorm_cui: '6809',
          drug_class: 'Biguanide Antidiabetic Agent',
          mechanism_of_action: 'Decreases hepatic glucose production, decreases intestinal absorption of glucose, and improves insulin sensitivity via AMPK activation.',
        },
        evidence_summary: 'Pharmacological properties verified against FDA DailyMed structured labeling and NLM RxNorm terminology.',
        citations: [
          {
            source_title: 'FDA DailyMed Package Insert - Metformin',
            source_type: 'DailyMed',
            identifier: 'RxCUI:6809',
            url: 'https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=Metformin',
            evidence_status: 'Authoritative',
            retrieved_date: '2026-01-15',
          },
          {
            source_title: 'NLM RxNorm Standardized Terminology',
            source_type: 'RxNorm',
            identifier: 'CUI:6809',
            url: 'https://mor.nlm.nih.gov/RxNav/search?searchBy=RXCUI&searchTerm=6809',
            evidence_status: 'Authoritative',
            retrieved_date: '2026-01-15',
          },
        ],
        confidence_status: 'VERIFIED_AUTHORITATIVE',
        safety_disclaimer: 'Informational purpose only. Not clinical or prescribing advice. Consult a healthcare professional.',
        tokens_used: 164,
        latency_ms: 14.2,
      },
    },
  ]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const currentQuery = query.trim();
    setQuery('');
    setLoading(true);
    setError(null);

    try {
      const resp = await askAssistant(currentQuery, includeExperimental);
      setResponses((prev) => [...prev, { query: currentQuery, response: resp }]);
    } catch (err: any) {
      setError(err.message || 'Error processing consultation request');
    } finally {
      setLoading(false);
    }
  };

  const samplePrompts = [
    'Tell me about Warfarin indications',
    'How does Lisinopril work?',
    'What are documented interactions between Warfarin and Aspirin?',
    'Prescribe dosage for me (test guardrail)',
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-teal-400" />
          Evidence-Grounded AI Drug Assistant
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Biomedical RAG assistant anchoring every response to verified clinical sources with provenance tracking.
        </p>
      </div>

      <SafetyBanner />

      {/* Suggested Prompts */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[11px] font-mono text-slate-500 uppercase">Suggested Queries:</span>
        {samplePrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => setQuery(p)}
            className="text-xs px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 hover:border-teal-700/60 transition-colors"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Error / Guardrail Notice */}
      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/80 text-red-200 text-xs flex items-start gap-3 shadow-lg">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold text-sm text-red-300">Safety Guardrail Active</h4>
            <p className="mt-1 leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {/* Response Stream List */}
      <div className="space-y-6">
        {responses.map((item, idx) => {
          const resp = item.response;
          return (
            <div key={idx} className="space-y-4">
              {/* User Query Bubble */}
              <div className="flex justify-end">
                <div className="bg-gradient-to-r from-teal-900/60 to-blue-900/60 border border-teal-700/50 rounded-2xl px-5 py-3 text-xs sm:text-sm text-slate-100 max-w-2xl shadow-sm">
                  {item.query}
                </div>
              </div>

              {/* Assistant Grounded Response Card */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
                {/* Status Bar */}
                <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-slate-800 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1 font-mono text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      {resp.confidence_status}
                    </span>
                    <span className="font-mono text-[11px] text-slate-400">
                      Tokens: {resp.tokens_used} • Latency: {resp.latency_ms} ms
                    </span>
                  </div>
                  <span className="font-mono text-[11px] text-slate-500">
                    CID: {resp.conversation_id.slice(0, 12)}
                  </span>
                </div>

                {/* Direct Explanation */}
                <div className="space-y-1">
                  <h4 className="text-xs font-mono uppercase text-teal-400 font-semibold tracking-wider">
                    Direct Explanation
                  </h4>
                  <p className="text-sm text-slate-100 leading-relaxed font-light">
                    {resp.direct_explanation}
                  </p>
                </div>

                {/* Structured Drug Information */}
                {resp.drug_information && (
                  <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-2">
                    <h5 className="text-xs font-mono uppercase text-slate-400 font-semibold">
                      Extracted Pharmacological Entity
                    </h5>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-slate-500">Generic Name:</span>{' '}
                        <strong className="text-white">{resp.drug_information.generic_name}</strong>
                      </div>
                      <div>
                        <span className="text-slate-500">RxNorm CUI:</span>{' '}
                        <strong className="text-teal-300 font-mono">{resp.drug_information.rxnorm_cui || 'N/A'}</strong>
                      </div>
                      <div className="sm:col-span-2">
                        <span className="text-slate-500">Drug Class:</span>{' '}
                        <span className="text-slate-300">{resp.drug_information.drug_class}</span>
                      </div>
                      {resp.drug_information.mechanism_of_action && (
                        <div className="sm:col-span-2">
                          <span className="text-slate-500">Mechanism:</span>{' '}
                          <p className="text-slate-300 text-[11px] mt-1 bg-slate-900 p-2 rounded border border-slate-800">
                            {resp.drug_information.mechanism_of_action}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Evidence Summary */}
                <div className="space-y-1">
                  <h4 className="text-xs font-mono uppercase text-blue-400 font-semibold tracking-wider">
                    Evidence Synthesis
                  </h4>
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800/60">
                    {resp.evidence_summary}
                  </p>
                </div>

                {/* Citations List */}
                {resp.citations.length > 0 && (
                  <div className="space-y-2 pt-2">
                    <h4 className="text-xs font-mono uppercase text-slate-400 font-semibold tracking-wider flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-teal-400" />
                      Authoritative Source Citations ({resp.citations.length})
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {resp.citations.map((c, cIdx) => (
                        <a
                          key={cIdx}
                          href={c.url || '#'}
                          target="_blank"
                          rel="noreferrer"
                          className="p-3 rounded-lg bg-slate-950 border border-slate-800 hover:border-teal-700/60 flex items-start justify-between gap-2 group transition-all"
                        >
                          <div>
                            <p className="text-xs font-semibold text-slate-200 group-hover:text-teal-300 transition-colors">
                              {c.source_title}
                            </p>
                            <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400 mt-1">
                              <span className="text-teal-400">{c.source_type}</span>
                              <span>•</span>
                              <span>ID: {c.identifier}</span>
                            </div>
                          </div>
                          <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-teal-400 shrink-0 mt-0.5" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Safety Notice Footer */}
                <div className="pt-3 border-t border-slate-800 text-[11px] text-amber-300/80 flex items-center gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span>{resp.safety_disclaimer}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Input Box */}
      <form onSubmit={handleSubmit} className="sticky bottom-4 bg-slate-950/90 backdrop-blur-md p-2 rounded-2xl border border-slate-800 shadow-2xl space-y-2">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about medications, active ingredients, mechanisms, or interactions..."
            disabled={loading}
            className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-xs sm:text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 transition-colors disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-5 py-3 rounded-xl bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-500 hover:to-blue-500 text-white font-medium text-xs sm:text-sm flex items-center gap-2 shadow-lg shadow-teal-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
          >
            {loading ? (
              <span className="flex items-center gap-1.5">
                <span className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Evaluating...</span>
              </span>
            ) : (
              <>
                <span>Consult</span>
                <Send className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>

        <div className="flex items-center justify-between px-2 text-[11px] text-slate-500">
          <label className="flex items-center gap-2 cursor-pointer hover:text-slate-400">
            <input
              type="checkbox"
              checked={includeExperimental}
              onChange={(e) => setIncludeExperimental(e.target.checked)}
              className="rounded bg-slate-900 border-slate-700 text-teal-600 focus:ring-0"
            />
            <span>Include experimental Graph ML link predictions (clearly flagged)</span>
          </label>
          <span className="hidden sm:inline">Press Enter to send query</span>
        </div>
      </form>
    </div>
  );
};

