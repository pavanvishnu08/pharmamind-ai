export interface DrugSynonym {
  id: string;
  synonym: string;
  source: string;
  language: string;
}

export interface DrugIngredient {
  id: string;
  name: string;
  unii?: string;
  pubchem_cid?: string;
  chemical_formula?: string;
  molecular_weight?: number;
  strength?: string;
}

export interface Drug {
  id: string;
  generic_name: string;
  brand_name?: string;
  rxnorm_cui?: string;
  atc_code?: string;
  drug_class?: string;
  description?: string;
  mechanism_of_action?: string;
  route_of_administration?: string;
  is_fda_approved: boolean;
  synonyms: DrugSynonym[];
  ingredients: DrugIngredient[];
}

export interface InteractionEvidenceItem {
  source_drug: string;
  target_drug: string;
  relationship_type: string;
  clinical_effect: string;
  evidence_level: 'VERIFIED_AUTHORITATIVE' | 'SCIENTIFIC_LITERATURE' | 'EXPERIMENTAL_ML_PREDICTION' | 'UNCERTAIN_SIGNAL';
  provenance_source: string;
  provenance_id?: string;
  confidence_score: number;
  retrieved_date: string;
  is_experimental: boolean;
  warning_notice: string;
}

export interface InteractionCheckResponse {
  queried_drugs: string[];
  normalized_drugs: string[];
  total_interactions_found: number;
  interactions: InteractionEvidenceItem[];
  clinical_safety_notice: string;
  uncertainty_statement?: string;
}

export interface GraphNode {
  id: string;
  label: string;
  node_type: 'DRUG' | 'INGREDIENT' | 'DISEASE' | 'ADVERSE_EFFECT' | 'TARGET' | 'CLASS';
  properties: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
  evidence_level: string;
  provenance_source: string;
  confidence_score: number;
  retrieved_date: string;
  is_experimental: boolean;
}

export interface KnowledgeGraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
  graph_engine: string;
  provenance_summary: Record<string, number>;
}

export interface PublicationItem {
  pmid: string;
  title: string;
  abstract: string;
  journal: string;
  publication_year: number;
  authors: string;
  doi?: string;
  mesh_terms: string[];
  evidence_type: string;
}

export interface Citation {
  source_title: string;
  source_type: string;
  identifier: string;
  url?: string;
  evidence_status: string;
  retrieved_date: string;
}

export interface ChatResponse {
  conversation_id: string;
  direct_explanation: string;
  drug_information?: Record<string, any>;
  evidence_summary: string;
  citations: Citation[];
  confidence_status: string;
  safety_disclaimer: string;
  tokens_used: number;
  latency_ms: number;
}

export interface MetricItem {
  task: string;
  metric_name: string;
  value: number;
  target_threshold?: number;
  dataset: string;
  sample_size: number;
  is_tested: boolean;
  benchmark_status: 'PASS' | 'WARN' | 'UNTESTED';
  notes?: string;
}

export interface SystemPerformanceMetrics {
  api_latency_ms: number;
  model_inference_latency_ms: number;
  ram_usage_mb: number;
  free_ram_mb: number;
  token_throughput_per_sec: number;
  failure_rate_pct: number;
}

export interface EvaluationDashboardResponse {
  system_metrics: SystemPerformanceMetrics;
  nlp_metrics: MetricItem[];
  retrieval_metrics: MetricItem[];
  graph_ml_metrics: MetricItem[];
  rag_metrics: MetricItem[];
  total_experiments: number;
  evaluated_at: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  application: string;
  version: string;
  environment: string;
  timestamp: string;
  database: {
    connected: boolean;
    dialect: string;
    is_fallback: boolean;
    url_target: string;
    latency_ms?: number;
  };
  memory: {
    total_gb: number;
    available_gb: number;
    used_gb: number;
    memory_load_pct: number;
    is_safe_for_ml: boolean;
    safety_threshold_mb: number;
  };
  machine_learning: {
    device: string;
    torch_version: string;
    num_threads: number;
    lazy_loading_enabled: boolean;
    max_batch_size: number;
  };
  provenance_integrity: boolean;
}

export type PageId =
  | 'landing'
  | 'auth'
  | 'dashboard'
  | 'drug-search'
  | 'assistant'
  | 'interactions'
  | 'graph'
  | 'literature'
  | 'evaluation'
  | 'history'
  | 'settings';

// Phase 2 Types: Normalization, NER, Ingestion & FAERS Signals

export interface NormalizedDrugResult {
  input_text: string;
  canonical_name: string;
  display_name: string;
  rxcui?: string;
  atc_code?: string;
  drug_class?: string;
  match_type: 'EXACT' | 'BRAND_MAPPING' | 'SALT_STRIPPED' | 'FUZZY_CORRECTION' | 'UNKNOWN';
  confidence_score: number;
  salt_removed?: string;
  original_brand?: string;
}

export interface ExtractedBiomedicalEntity {
  text: string;
  label: 'DRUG' | 'INGREDIENT' | 'DISEASE' | 'SYMPTOM' | 'PROTEIN' | 'PATHWAY' | 'ADVERSE_EFFECT' | 'DRUG_CLASS';
  start_char: number;
  end_char: number;
  normalized_name: string;
  normalized_id: string;
  confidence: number;
}

export interface FAERSReactionSignal {
  term: string;
  count: number;
}

export interface FAERSSignalData {
  drug_name: string;
  is_causal_confirmed: boolean;
  signal_type: string;
  signal_count: number;
  top_adverse_reactions: FAERSReactionSignal[];
  disclaimer: string;
  provenance_source: string;
  provenance_id: string;
  confidence_status: string;
}

export interface DrugIngestionResult {
  drug_id: string;
  generic_name: string;
  brand_names: string[];
  rxcui: string;
  atc_code?: string;
  drug_class?: string;
  monograph_sections: Record<string, any>;
  faers_signals: FAERSSignalData;
  literature_citations: any[];
  quality_report: {
    is_valid: boolean;
    quality_score: number;
    missing_fields: string[];
    validation_errors: string[];
    deduplication_status: string;
    provenance_retained: boolean;
  };
  provenance_records: any[];
}
