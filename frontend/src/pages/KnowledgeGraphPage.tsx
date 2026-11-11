import React, { useState, useEffect } from 'react';
import { Network, Filter, ShieldCheck, Database, Layers, Info } from 'lucide-react';
import { KnowledgeGraphResponse, GraphNode, GraphEdge } from '../types';
import { fetchKnowledgeGraph } from '../services/api';

export const KnowledgeGraphPage: React.FC = () => {
  const [graphData, setGraphData] = useState<KnowledgeGraphResponse | null>(null);
  const [selectedNodeType, setSelectedNodeType] = useState<string>('ALL');
  const [selectedRelType, setSelectedRelType] = useState<string>('ALL');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadGraph();
  }, [selectedNodeType, selectedRelType]);

  const loadGraph = async () => {
    setLoading(true);
    try {
      const nodeFilter = selectedNodeType === 'ALL' ? undefined : selectedNodeType;
      const relFilter = selectedRelType === 'ALL' ? undefined : selectedRelType;
      const data = await fetchKnowledgeGraph(nodeFilter, relFilter);
      setGraphData(data);
      if (data.nodes.length > 0 && !selectedNode) {
        setSelectedNode(data.nodes[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const nodeColorMap: Record<string, string> = {
    DRUG: 'bg-teal-500/20 text-teal-300 border-teal-500/50',
    TARGET: 'bg-blue-500/20 text-blue-300 border-blue-500/50',
    DISEASE: 'bg-purple-500/20 text-purple-300 border-purple-500/50',
    ADVERSE_EFFECT: 'bg-amber-500/20 text-amber-300 border-amber-500/50',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Network className="w-5 h-5 text-teal-400" />
            Biomedical Knowledge Graph Explorer
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Explore multi-relational entities with verified pharmacological provenance and link confidence.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={selectedNodeType}
            onChange={(e) => setSelectedNodeType(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-teal-500"
          >
            <option value="ALL">All Entity Types</option>
            <option value="DRUG">Drugs</option>
            <option value="TARGET">Biological Targets</option>
            <option value="DISEASE">Diseases / Indications</option>
            <option value="ADVERSE_EFFECT">Adverse Effects</option>
          </select>

          <select
            value={selectedRelType}
            onChange={(e) => setSelectedRelType(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-teal-500"
          >
            <option value="ALL">All Relationships</option>
            <option value="TREATS">TREATS</option>
            <option value="TARGETS">TARGETS</option>
            <option value="INTERACTS_WITH">INTERACTS_WITH</option>
            <option value="ASSOCIATED_WITH_ADVERSE_EFFECT">ASSOCIATED_WITH_ADVERSE_EFFECT</option>
          </select>
        </div>
      </div>

      {/* Main Graph Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Visual Graph Topology Canvas */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6 min-h-[500px] flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 pb-4 border-b border-slate-800">
            <div className="flex items-center gap-2 font-mono">
              <Database className="w-4 h-4 text-teal-400" />
              <span>Engine: {graphData?.graph_engine || 'Local NetworkX'}</span>
            </div>
            <div className="flex items-center gap-4 font-mono">
              <span>Nodes: <strong className="text-white">{graphData?.total_nodes || 0}</strong></span>
              <span>Edges: <strong className="text-white">{graphData?.total_edges || 0}</strong></span>
            </div>
          </div>

          {/* Interactive Topology Graph Visualizer */}
          <div className="relative flex-1 rounded-xl bg-slate-950 p-6 flex flex-wrap items-center justify-center gap-4 overflow-hidden border border-slate-800/80">
            <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] opacity-40 pointer-events-none" />
            
            {graphData?.nodes.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              const colorClass = nodeColorMap[node.node_type] || 'bg-slate-800 text-slate-300 border-slate-700';
              return (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`relative z-10 px-4 py-2.5 rounded-xl border text-xs font-semibold cursor-pointer transition-all ${colorClass} ${
                    isSelected ? 'ring-2 ring-teal-400 scale-110 shadow-lg shadow-teal-950' : 'hover:scale-105'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
                    <span>{node.label}</span>
                  </div>
                  <span className="text-[9px] font-mono opacity-70 block mt-0.5">{node.node_type}</span>
                </div>
              );
            })}
          </div>

          {/* Graph Legend */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-4 border-t border-slate-800 text-xs">
            <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono">
              <span className="flex items-center gap-1.5 text-teal-300">
                <span className="w-2.5 h-2.5 rounded bg-teal-500/40 border border-teal-500" /> Drug
              </span>
              <span className="flex items-center gap-1.5 text-blue-300">
                <span className="w-2.5 h-2.5 rounded bg-blue-500/40 border border-blue-500" /> Target / Enzyme
              </span>
              <span className="flex items-center gap-1.5 text-purple-300">
                <span className="w-2.5 h-2.5 rounded bg-purple-500/40 border border-purple-500" /> Disease
              </span>
              <span className="flex items-center gap-1.5 text-amber-300">
                <span className="w-2.5 h-2.5 rounded bg-amber-500/40 border border-amber-500" /> Adverse Effect
              </span>
            </div>
          </div>
        </div>

        {/* Selected Entity Inspector & Active Edges */}
        <div className="space-y-4">
          {selectedNode ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
              <div className="flex items-start justify-between pb-3 border-b border-slate-800">
                <div>
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-teal-400">
                    {selectedNode.node_type}
                  </span>
                  <h3 className="text-lg font-bold text-white mt-1.5">{selectedNode.label}</h3>
                </div>
                <span className="text-xs font-mono text-slate-500">ID: {selectedNode.id}</span>
              </div>

              {/* Node Properties */}
              <div className="space-y-2">
                <h4 className="text-xs font-mono uppercase text-slate-400 font-semibold">Properties</h4>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1 text-xs font-mono">
                  {Object.entries(selectedNode.properties).map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-slate-500">{k}:</span>
                      <span className="text-slate-200">{String(v)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Connected Relationships for this node */}
              <div className="space-y-2">
                <h4 className="text-xs font-mono uppercase text-slate-400 font-semibold">Connected Relationships</h4>
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {graphData?.edges
                    .filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((edge) => (
                      <div
                        key={edge.id}
                        className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1.5"
                      >
                        <div className="flex items-center justify-between font-mono text-[11px]">
                          <span className="text-teal-400 font-bold">{edge.relationship_type}</span>
                          <span className="text-slate-400">{(edge.confidence_score * 100).toFixed(0)}% Conf</span>
                        </div>
                        <p className="text-slate-300">
                          {edge.source} <span className="text-slate-500">→</span> {edge.target}
                        </p>
                        <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1">
                          <span>Src: {edge.provenance_source}</span>
                          <span>{edge.retrieved_date}</span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-500">
              Click any node in the topology canvas to inspect properties and relationships.
            </div>
          )}

          {/* Provenance Distribution Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3">
            <h4 className="text-xs font-mono uppercase text-slate-400 font-semibold flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-teal-400" />
              Source Provenance Distribution
            </h4>
            <div className="space-y-2 text-xs">
              {Object.entries(graphData?.provenance_summary || {}).map(([src, count]) => (
                <div key={src} className="flex items-center justify-between">
                  <span className="text-slate-300">{src}</span>
                  <span className="font-mono text-teal-400 font-bold bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                    {count} relations
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

