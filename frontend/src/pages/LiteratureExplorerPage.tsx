import React, { useState, useEffect } from 'react';
import { BookOpenText, Search, ExternalLink, Calendar, Users, Bookmark } from 'lucide-react';
import { PublicationItem } from '../types';
import { fetchLiterature } from '../services/api';

export const LiteratureExplorerPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [publications, setPublications] = useState<PublicationItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadLiterature();
  }, []);

  const loadLiterature = async (q?: string) => {
    setLoading(true);
    try {
      const data = await fetchLiterature(q);
      setPublications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadLiterature(searchTerm);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <BookOpenText className="w-5 h-5 text-teal-400" />
            Research Literature Explorer
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Peer-reviewed scientific literature indexed from PubMed and PubMed Central Open Access.
          </p>
        </div>

        <form onSubmit={handleSearch} className="flex items-center gap-2 max-w-md w-full">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by drug, biological target, or MeSH term..."
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

      {/* Publications Stream */}
      <div className="space-y-4">
        {publications.map((pub) => (
          <div
            key={pub.pmid}
            className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-3 hover:border-slate-700 transition-all shadow-md"
          >
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
              <h3 className="text-base font-bold text-white leading-snug">
                {pub.title}
              </h3>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800">
                  PMID: {pub.pmid}
                </span>
                <a
                  href={`https://pubmed.ncbi.nlm.nih.gov/${pub.pmid}/`}
                  target="_blank"
                  rel="noreferrer"
                  className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400">
              <span className="text-teal-400 font-semibold">{pub.journal}</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                {pub.publication_year}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Users className="w-3.5 h-3.5 text-slate-500" />
                {pub.authors}
              </span>
            </div>

            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
              {pub.abstract}
            </p>

            <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800 text-xs">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-[10px] font-mono text-slate-500 uppercase mr-1">MeSH Terms:</span>
                {pub.mesh_terms.map((term, tIdx) => (
                  <span
                    key={tIdx}
                    className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/60"
                  >
                    {term}
                  </span>
                ))}
              </div>
              {pub.doi && (
                <span className="text-[10px] font-mono text-slate-500">DOI: {pub.doi}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

