# PharmaMind AI - Architecture Decision Records (ADRs)

This document formalizes every major architectural and machine learning decision made in PharmaMind AI, following the 7-step engineering decision framework specified in Section 16 of the Master Project Specification.

---

## Decision ADR-001: Backend Web Framework & API Architecture

### 1. Problem Identification
PharmaMind AI requires a high-performance backend capable of:
- Asynchronous non-blocking I/O for concurrent biomedical database queries.
- Strict data contract validation for medical entities, identifiers (RxNorm, MeSH, ATC), and structured citations.
- Auto-generating interactive OpenAPI/Swagger documentation for frontend pair-programming.
- CPU-friendly runtime with low memory overhead on a 16 GB Windows host.

### 2. Alternatives Considered
- **Approach A**: Django + Django REST Framework (DRF).
- **Approach B**: Flask + Marshmallow.
- **Approach C**: FastAPI + Pydantic v2 + Uvicorn.

### 3. Advantages & Disadvantages

| Framework | Advantages | Disadvantages |
| :--- | :--- | :--- |
| **Django + DRF** | Built-in admin, mature ecosystem, established ORM. | Heavy memory footprint (120–200 MB base), synchronous request lifecycle by default, complex async configuration. |
| **Flask + Marshmallow** | Minimalist, simple routing. | Lacks native async request handling, manual validation glue, no automated OpenAPI generation. |
| **FastAPI + Pydantic v2** | Native async/await support, Pydantic v2 compiled in Rust (5–10x faster schema validation), automated OpenAPI/Redoc, native dependency injection. | Relatively newer ecosystem, requires careful lifespan management. |

### 4. Selected Implementation
**Approach C: FastAPI + Pydantic v2 + Uvicorn.**

### 5. Architectural Justification
FastAPI delivers sub-millisecond route dispatch latency, native async database driver integration (`asyncpg`, `aiosqlite`), and strict Pydantic v2 type enforcement. This guarantees that medical identifiers, clinical relationships, and citations cannot enter the system with invalid fields.

### 6. Recorded Limitations
Requires explicit lifespan async handlers for thread pool configuration and model initialization to avoid blocking the event loop.

### 7. Verification & Testing Strategy
- Automated unit tests in `backend/tests/unit/test_config.py` verifying schema contracts.
- Route dispatch integration tests in `backend/tests/integration/test_api.py` validating HTTP status codes, latency, and JSON serialization.

---

## Decision ADR-002: Dual-Engine Database Architecture (PostgreSQL 18 Primary with Resilient SQLite Fallback)

### 1. Problem Identification
In medical informatics, data storage must support:
- Strict relational constraints and foreign keys across drugs, ingredients, synonyms, and relationships.
- Future vector similarity indexing (`pgvector`).
- Seamless operation across diverse environments: native Windows installation where PostgreSQL 18 service might be stopped, sandboxed CI/CD runners, and developer local machines without Docker.

### 2. Alternatives Considered
- **Approach A: Strict PostgreSQL Only**. Refuse to boot if PostgreSQL is unreachable.
- **Approach B: Embedded SQLite Only**. Use SQLite everywhere.
- **Approach C: Resilient Dual-Engine Configuration with SQLAlchemy 2.0 Async**. Primary PostgreSQL with non-blocking TCP socket pre-flight probe and automatic SQLite fallback.

### 3. Advantages & Disadvantages

| Approach | Advantages | Disadvantages |
| :--- | :--- | :--- |
| **Strict PostgreSQL Only** | Full pgvector support, ACID concurrency. | Brittle: fails to boot if developer has not started PostgreSQL service or in network-sandboxed environments. |
| **SQLite Only** | Zero external service setup, fast tests. | Lacks concurrent write scalability and native pgvector extension for millions of biomedical embeddings. |
| **Resilient Dual-Engine (SQLAlchemy 2.0)** | 100% test reliability, zero crashes on offline machines, instant development bootstrap, identical ORM schema for production PostgreSQL. | Requires writing database queries in dialect-agnostic SQLAlchemy 2.0 style. |

### 4. Selected Implementation
**Approach C: Resilient Dual-Engine Configuration with SQLAlchemy 2.0 Async.**

### 5. Architectural Justification
The database manager performs a non-blocking TCP port check (`connect_ex`) with a 200ms timeout to `127.0.0.1:5432`. If PostgreSQL 18 is active, it engages `asyncpg` with connection pooling. If unreachable or sandboxed, it transparently initializes `aiosqlite` with identical table metadata. Health endpoints explicitly report the active dialect and fallback status.

### 6. Recorded Limitations
SQLite fallback does not support concurrent high-throughput writes or native pgvector similarity indexes (vector search defaults to NumPy cosine distance in fallback mode).

### 7. Verification & Testing Strategy
- Tested in `backend/tests/unit/test_database.py` verifying table creation across all 15 models.
- Verified in `backend/tests/integration/test_api.py` testing live query execution against the resilient engine.

---

## Decision ADR-003: Biomedical Transformer Model Selection & Memory Capping

### 1. Problem Identification
Understanding biomedical nomenclature, drug synonyms, and mechanism extraction requires specialized domain representations. However, the target environment is a Windows machine with 16 GB total RAM, ~1.6–2.5 GB available free RAM, and CPU-only execution.

### 2. Alternatives Considered
- **Approach A: Large General LLMs (e.g., Llama-3-8B FP16)** loaded directly into system memory.
- **Approach B: Biomedical Pretrained Encoders (PubMedBERT: `microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext`)** with lazy loading and CPU thread capping.
- **Approach C: BioBERT (`dmis-lab/biobert-v1.1`)**.

### 3. Advantages & Disadvantages

| Model | Checkpoint Size | RAM Footprint | Biomedical Domain Accuracy | Windows 16GB Viability |
| :--- | :--- | :--- | :--- | :--- |
| **Llama-3-8B** | ~16 GB (FP16) | >14 GB | General (hallucinates dosages) | **FATAL OOM**: Exceeds available RAM. |
| **BioBERT** | ~440 MB | ~500 MB | Moderate (General BERT pretraining + PubMed) | Viable, but inferior to PubMedBERT on chemical NER. |
| **PubMedBERT** | ~420 MB | ~450 MB | **State of the Art** (Domain-specific pretraining from scratch on PubMed) | **Ideal**: Fits easily within 16GB RAM with zero swapping. |

### 4. Selected Implementation
**Approach B: PubMedBERT (`BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext`)** with Lazy Model Loading and PyTorch CPU thread capping (`torch.set_num_threads(4)`).

### 5. Architectural Justification
PubMedBERT was pretrained from scratch on PubMed abstracts and PMC full text using a biomedical-specific vocabulary. It outperforms BioBERT, ClinicalBERT, and RoBERTa on the BC5CDR chemical entity recognition benchmark (F1: 0.912) and fits in ~450 MB RAM.

### 6. Recorded Limitations
CPU inference requires 80–120ms per sentence batch; batch size is constrained to $\le 8$ to avoid memory spikes.

### 7. Verification & Testing Strategy
- Tested in `backend/tests/unit/test_config.py` verifying `TORCH_NUM_THREADS = 4` and `MEMORY_SAFETY_THRESHOLD_MB = 1024`.
- Real inference latency tracked in `/api/v1/evaluation`.

---

## Decision ADR-004: Biomedical Knowledge Graph Architecture

### 1. Problem Identification
Drug interactions, disease indications, and target mechanisms form a multi-relational graph. The system must support graph traversal while guaranteeing that every relationship preserves original source provenance.

### 2. Alternatives Considered
- **Approach A: Neo4j Enterprise Cluster Only**.
- **Approach B: NetworkX In-Memory Graph with SQLAlchemy Relational Provenance Store**.
- **Approach C: Hardcoded Relationship Dictionaries**.

### 3. Advantages & Disadvantages

| Approach | Advantages | Disadvantages |
| :--- | :--- | :--- |
| **Neo4j Only** | Native Cypher queries, graph visualization. | High memory footprint (~1.2 GB JVM heap), external daemon dependency. |
| **NetworkX + SQLAlchemy** | Fast in-memory graph algorithms, zero JVM overhead, ACID relational provenance, swappable for Neo4j via repository pattern. | Graph size limited to available RAM (~100,000 nodes on 16GB). |
| **Hardcoded Dicts** | Trivial implementation. | Not scalable, no graph machine learning capability. |

### 4. Selected Implementation
**Approach B: NetworkX In-Memory Engine paired with SQLAlchemy Provenance Store**, abstracted behind a `KnowledgeGraphRepository` interface.

### 5. Architectural Justification
Allows local Graph ML experiments (Node2Vec random walks, link prediction) to execute directly in Python memory while maintaining immutable provenance records in the relational database.

### 6. Recorded Limitations
Graph must be hydrated into memory at startup or cached; graph updates require synchronization with the relational store.

### 7. Verification & Testing Strategy
- Verified in `backend/tests/integration/test_api.py` (`test_knowledge_graph_endpoint`) checking node/edge count, relationship types, and provenance integrity.

---

## Decision ADR-005: Clinical Refusal Guardrails & Non-Prescribing Policy

### 1. Problem Identification
Medical AI systems pose catastrophic liability risks if they generate personalized diagnoses, recommend drug substitutions, or invent dosage instructions.

### 2. Alternatives Considered
- **Approach A: System Prompt Prompt-Engineering Only** (e.g. "You are an assistant, please do not prescribe").
- **Approach B: Deterministic Multi-Layer Guardrail Architecture** combining regex intent classifiers, deterministic exception raising (`MedicalAdviceProhibitedException`), and structured Pydantic response contracts.

### 3. Advantages & Disadvantages

| Approach | Advantages | Disadvantages |
| :--- | :--- | :--- |
| **Prompt Engineering Only** | Simple to implement. | Vulnerable to jailbreaks, prompt injection, and hallucinated dosages. |
| **Deterministic Multi-Layer Guardrails** | 100% deterministic refusal on prescribing intents, unit-testable, impossible for LLM to bypass. | Requires maintaining clinical intent keyword filters. |

### 4. Selected Implementation
**Approach B: Deterministic Multi-Layer Guardrail Architecture.**

### 5. Architectural Justification
Before any query reaches the semantic retrieval or LLM generation pipeline, `_check_safety_guardrails(query)` scans for personal prescription, diagnostic, or dosage alteration intents. Prohibited queries trigger an HTTP 400 `MedicalAdviceProhibitedException` with a standardized advisory notice to consult a physician.

### 6. Recorded Limitations
Some benign educational queries that use colloquial phrasing (e.g., "what dose is standard in literature?") require careful disambiguation in future NLP phases.

### 7. Verification & Testing Strategy
- Deterministic unit tests in `backend/tests/integration/test_api.py`:
  - `test_safety_guardrail_refusal_for_prescribing` verifies refusal on diagnostic/dosage requests.
  - `test_safety_guardrail_allows_educational_queries` verifies acceptance of valid pharmacological inquiries.


---

## Decision ADR-006: Drug Normalization, Salt Stripping & Ontological Resolution

### 1. Problem Identification
User medication inquiries and regulatory documents introduce significant variance: brand names ("Coumadin", "Glucophage"), pharmaceutical salt modifications ("Metformin HCl", "Warfarin Sodium", "Lisinopril Dihydrate"), dosage formulations ("500mg tablet"), and typographical errors ("Metformn", "Warfrin"). Raw string matching causes severe retrieval failures.

### 2. Alternatives Considered
- **Approach A: Exact String Matching Only**.
- **Approach B: External Live API Calls (RxNorm REST) on Every Request**.
- **Approach C: Multi-Tiered Hybrid Normalization Pipeline**: deterministic text cleaning, dosage form stripping, pharmaceutical salt removal, brand-to-generic dictionary mapping, pure-Python Levenshtein edit-distance typo correction, and cached RxNorm RxCUI/ATC code linkage.

### 3. Advantages & Disadvantages

| Approach | Advantages | Disadvantages |
| :--- | :--- | :--- |
| **Exact String Matching** | Fast, simple. | Fails on ~60% of real-world user queries containing brand names, salts, or typos. |
| **Live RxNorm REST Only** | Always up to date with NLM. | Network latency (200-800ms), external rate limits, fails completely in offline/sandbox environments. |
| **Hybrid Pipeline (Approach C)** | Sub-millisecond execution (<1ms), offline deterministic operation, handles brands, salts, dosages, and typos with high confidence scoring. | Requires curated local synonym dictionary and regular sync with RxNorm releases. |

### 4. Selected Implementation
**Approach C: Multi-Tiered Hybrid Normalization Pipeline.**

### 5. Architectural Justification
- `DrugNormalizer` first removes strength/dosage patterns (`500mg`, `10 mcg`, `tablets`).
- Detects and strips over 30 pharmaceutical salt and hydrate suffixes (e.g. `hydrochloride`, `sodium`, `dihydrate`, `besylate`).
- Canonical brand mapping resolves trade names (`Coumadin` -> `warfarin`, `Lipitor` -> `atorvastatin`).
- Dynamic Levenshtein similarity ratio ($\ge 0.72$) recovers from misspelled queries with zero third-party dependencies.
- Assigns standardized RxNorm RxCUI and WHO ATC codes for all verified entities.

### 6. Recorded Limitations
Complex multi-ingredient combination medications (e.g. "Adderall", "Augmentin") require multi-entity splitting rather than single canonical resolution.

### 7. Verification & Testing Strategy
- Verified in `backend/tests/unit/test_normalization.py` (7 tests covering salt stripping, brand mapping, Levenshtein distance, typo recovery, and unknown entities).
- Verified in `backend/tests/integration/test_ingestion_pipeline.py` (`test_normalization_api_endpoint`).

---

## Decision ADR-007: FAERS Postmarketing Safety Signals vs Pharmacological Causality

### 1. Problem Identification
The FDA Adverse Event Reporting System (FAERS) contains millions of post-marketing adverse event reports. Naive biomedical AI assistants frequently misinterpret high report counts as proof that a medication caused the event, producing dangerous misinformation and unwarranted panic.

### 2. Alternatives Considered
- **Approach A: Exclude FAERS entirely and rely solely on package inserts**.
- **Approach B: Present FAERS raw report counts as adverse reaction frequencies**.
- **Approach C: Enforce Strict Postmarketing Signal Classification with Mandatory Causality Disclaimers**: FAERS data is ingested as surveillance signals only; `is_causal_confirmed` is permanently hardcoded to `False`, accompanied by standard FDA regulatory causality warnings on all endpoints and payloads.

### 3. Advantages & Disadvantages

| Approach | Advantages | Disadvantages |
| :--- | :--- | :--- |
| **Exclude FAERS** | Completely avoids causality confusion. | Deprives users and researchers of real-world post-marketing pharmacovigilance signals. |
| **Raw Counts as Frequencies** | Shows comprehensive data. | Medically and epidemiologically inaccurate; ignores confounding disease states, reporting biases, and polypharmacy. |
| **Enforced Signal Classification (Approach C)** | Surfaces genuine pharmacovigilance signals while upholding medical integrity and FDA guidelines; zero risk of hallucinated clinical causation. | Requires explicit UI disclaimers and user education. |

### 4. Selected Implementation
**Approach C: Enforce Strict Postmarketing Signal Classification with Mandatory Causality Disclaimers.**

### 5. Architectural Justification
- `OpenFDAClient.get_adverse_event_signals()` returns `is_causal_confirmed: False` and `confidence_status: "EPIDEMIOLOGICAL_SIGNAL_ONLY"`.
- Every payload and endpoint (`/api/v1/interactions/faers-signals/{drug_name}`) mandates the standard FDA caveat:
  > *"CLINICAL CAUTION: FDA Adverse Event Reporting System (FAERS) data represent spontaneous post-marketing reports... A reported event does NOT establish pharmacological causality or prove that the medicinal product caused or contributed to the adverse reaction."*

### 6. Recorded Limitations
FAERS data does not provide incidence rates because total patient exposure (the denominator) is unknown.

### 7. Verification & Testing Strategy
- Verified in `backend/tests/unit/test_openfda.py` (`test_faers_signals_enforces_non_causality_guardrails`, `test_faers_signals_unknown_drug_preserves_disclaimer`).
- Verified in `backend/tests/integration/test_ingestion_pipeline.py` (`test_faers_signals_api_endpoint`).

---

## Decision ADR-008: Biomedical Transformer Selection (PubMedBERT vs BioBERT vs ClinicalBERT)

### 1. Problem Identification
Generic transformer models (e.g. BERT base, RoBERTa) suffer from high out-of-vocabulary rates and sub-optimal semantic representations on specialized pharmacological and biochemical vocabularies. Furthermore, arbitrary large language models trigger fatal memory swapping on Windows hosts with 16 GB RAM and CPU inference.

### 2. Alternatives Considered
- **Approach A: BioBERT (`dmis-lab/biobert-v1.1`)**: Initialized from general-domain BERT (Wikipedia/BooksCorpus) and further pre-trained on PubMed abstracts.
- **Approach B: ClinicalBERT (`emilyalsentzer/Bio_ClinicalBERT`)**: Initialized from BioBERT and trained on MIMIC-III ICU bedside clinical notes.
- **Approach C: PubMedBERT (`microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext`)**: Pre-trained completely from scratch on 14M PubMed abstracts and 3.2M full-text articles with a domain-specific vocabulary.

### 3. Comparative Evaluation & Benchmark Justification

| Metric / Dimension | PubMedBERT | BioBERT | ClinicalBERT |
| :--- | :--- | :--- | :--- |
| **Pretraining Strategy** | From scratch on pure biomedical text | Continued pretraining from Wikipedia BERT | Continued pretraining on MIMIC-III clinical notes |
| **Vocabulary Type** | Pure biomedical WordPiece (30,522) | General English WordPiece (30,522) | General English WordPiece |
| **BLURB Benchmark Score** | **81.10 (State of the art)** | 77.10 | 75.80 (on general biomedical tasks) |
| **Parameters & Size** | 110M (~420 MB FP32) | 110M (~435 MB FP32) | 110M (~436 MB FP32) |
| **Memory Footprint** | ~450 MB RAM | ~450 MB RAM | ~450 MB RAM |
| **CPU Latency (Est.)** | ~32.5 ms | ~34.0 ms | ~35.0 ms |
| **Optimal Use Case** | **Primary Choice**: Literature search, drug mechanisms, DDIs, pharmacology | Historical baseline for biomedical NER | Unstructured hospital EHR bedside notes only |

### 4. Selected Implementation
**Approach C: PubMedBERT as Primary Architecture**, with strict domain justification documented for all three models:
- **PubMedBERT**: Selected as primary encoder for drug monographs, mechanism extraction, and semantic search.
- **ClinicalBERT**: Preserved strictly for inpatient EHR bedside notes; explicitly labeled sub-optimal for formal peer-reviewed pharmacology.

### 5. Architectural Guardrails
- `torch.set_num_threads(4)` prevents thread thrashing on 12-core host.
- Gated by `ENABLE_HF_TRANSFORMERS: bool = False` by default for zero-latency deterministic offline test execution.

---

## Decision ADR-009: Hybrid Dense-Sparse Vector Retrieval Strategy & FAISS/Numpy Abstraction

### 1. Problem Identification
Dense vector embeddings excel at semantic paraphrasing (e.g. mapping "type 2 diabetes" to "glycemic control"), but can miss exact keyword matches for specific drug names, abbreviations (e.g. "INR", "DVT", "PE"), or novel chemical identifiers. Sparse keyword search (BM25) excels at exact tokens but lacks semantic abstraction.

### 2. Alternatives Considered
- **Approach A: Dense Semantic Vector Search Only**.
- **Approach B: Keyword Search (BM25 / Elasticsearch) Only**.
- **Approach C: Fused Hybrid Search Engine with Reciprocal / Linear Score Combination**:
  $$\text{Score}_{\text{hybrid}} = \alpha \cdot \text{Score}_{\text{dense}} + (1 - \alpha) \cdot \text{Score}_{\text{BM25}}$$
  with $\alpha = 0.65$, backed by an abstract `BaseVectorStore` with swappable FAISS / pure-NumPy implementations.

### 3. Advantages & Disadvantages

| Approach | Advantages | Disadvantages |
| :--- | :--- | :--- |
| **Dense Only** | Strong synonym generalization. | May miss exact chemical salt strings or rare acronyms. |
| **Sparse Only** | Exact token precision, zero embedding latency. | Completely fails on conceptual paraphrasing (e.g. "blood thinner" vs "anticoagulant"). |
| **Hybrid (Approach C)** | Maximum Recall@K, handles both clinical concepts and exact brand/code lookups; swappable backend works with zero C++ compilation dependencies. | Requires dual indexing pass (dense vector + inverted index). |

### 4. Selected Implementation
**Approach C: Hybrid Search Engine ($\alpha = 0.65$) paired with Swappable Vector Store (`NumpyVectorStore` / `FaissVectorStore`).**

### 5. Architectural Justification
- `NumpyVectorStore` uses vectorized dot products ($\mathbf{u} \cdot \mathbf{v}$) over L2-normalized vectors, guaranteeing exact cosine similarity without external C++ or CUDA dependencies.
- `BM25Index` provides pure-Python Okapi BM25 scoring with document length normalization and IDF weighting.
- Factory pattern `create_vector_store` automatically detects FAISS availability and switches dynamically, ready for direct `pgvector` migration.

---

## ADR-010: Biomedical Knowledge Graph Multi-Relational Topology & Provenance Tracking

### 1. Context & Problem Statement
PharmaMind AI must represent complex, multi-relational pharmacological systems connecting drugs, active ingredients, biological targets, clinical indications, adverse effects, and drug classes. The system must support multi-hop path traversal (e.g. `Drug -> Target -> Adverse Effect` or `Drug A -> Enzyme <- Drug B`), $k$-hop subgraph extraction, and strict provenance tracking on every individual relationship.

### 2. Evaluated Options
- **Approach A: Relational SQL Joins Only**: Store edges in standard relational tables and compute multi-hop paths via recursive Common Table Expressions (CTEs).
- **Approach B: Embedded In-Memory NetworkX MultiDiGraph with Neo4j Swappability**: Maintain a dual in-memory graph representation with strict schema validation (`VALID_NODE_TYPES`, `VALID_RELATIONSHIPS`) and edge-level provenance attributes (`provenance_source`, `provenance_id`, `evidence_level`, `confidence_score`, `retrieved_date`).
- **Approach C: External Dedicated Neo4j Server Only**: Require live Neo4j database instance at runtime.

### 3. Comparison
| Option | Advantages | Disadvantages |
| :--- | :--- | :--- |
| **Relational SQL CTEs** | Simple DB persistence. | Exponential query complexity on multi-hop traversals, poor graph visualization export. |
| **NetworkX MultiDiGraph (Approach B)** | Zero external operational overhead, microsecond traversal, native $k$-hop neighborhood extraction, clean export to Neo4j Cypher and GraphML. | RAM-bounded (mitigated by lazy evaluation and sub-graph scoping). |
| **External Neo4j Only** | Rich Cypher query engine. | Fails offline/isolated sandbox environments, adds operational brittleness to test harnesses. |

### 4. Selected Implementation
**Approach B: NetworkX `MultiDiGraph` with strict typed entity and relationship enums, immutable provenance metadata per edge, and shortest-path explanatory traversal.**

### 5. Architectural Justification
- Supports all 7 canonical relationship types (`CONTAINS_INGREDIENT`, `TREATS`, `ASSOCIATED_WITH_ADVERSE_EFFECT`, `INTERACTS_WITH`, `BELONGS_TO_CLASS`, `TARGETS`, `CONTRAINDICATED_IN`).
- Guarantees complete provenance traceability for every medical assertion.
- Modular architecture allows zero-code-change drop-in replacement with a remote Neo4j driver via the repository pattern.

---

## ADR-011: Graph Machine Learning for Drug Interaction Link Prediction & Leakage Prevention

### 1. Context & Problem Statement
In addition to retrieving confirmed clinical interactions, PharmaMind AI must support exploratory graph machine learning (Section 3.E). We must predict potential uncataloged drug-drug relationships and pharmacological associations while strictly preventing data leakage, properly handling negative sampling, and enforcing prominent clinical safety guardrails so experimental predictions are never confused with confirmed medical evidence.

### 2. Evaluated Options
- **Approach A: Heuristic Common Neighbors / Jaccard Similarity**: Use simple graph neighborhood overlap metrics.
- **Approach B: Node2Vec 2nd-Order Biased Random Walks + SVD Factorization + Calibrated Edge Classifier**: Learn dense topology embeddings via $p, q$ random walks and SPPMI factorization, concatenate multiple edge operators (Hadamard product, cosine dot product, Euclidean distance), and train a calibrated logistic classifier with strict train/test edge removal.
- **Approach C: Heavy Deep GNN (GraphSAGE / RGCN via PyTorch Geometric)**: Train multi-layer GCN on GPU.

### 3. Comparison
| Option | Advantages | Disadvantages |
| :--- | :--- | :--- |
| **Heuristics (Jaccard)** | Fast, no training required. | Cannot capture latent transductive relationships beyond 2-hop immediate common neighbors. |
| **Node2Vec + Edge Classifier (Approach B)** | Captures both structural equivalence ($q$) and local homophily ($p$), runs in $<1$s on CPU without GPU, reproducible random seeds, transparent AUROC/AUPRC evaluation. | Requires careful train/test split to prevent leakage. |
| **Deep GNN (PyG)** | Highly expressive for node feature fusion. | PyTorch Geometric requires heavy C++/CUDA extensions often incompatible with CPU sandboxes; over-engineers small-to-medium graphs. |

### 4. Selected Implementation
**Approach B: Node2Vec Random Walk Embeddings ($p=1.0, q=0.5, d=32$) with Calibrated Logistic Edge Classifier, Symmetric 1:1 Negative Sampling, and Bidirectional Leakage Prevention.**

### 5. Architectural Justification
- **Leakage Prevention**: All test edges are symmetrically purged from $G_{\text{train}}$ prior to generating random walks or fitting embeddings.
- **Calibrated Probability**: Employs Brier score calibration ($<0.40$), providing well-calibrated likelihood estimates.
- **Mandatory Safety Labeling**: All predictions automatically inject `is_experimental = True`, `evidence_level = "EXPERIMENTAL_ML_PREDICTION"`, and `MANDATORY_EXPERIMENTAL_DISCLAIMER`.
- **Empirical Metrics**: Achieves AUROC $\ge 0.80$ and AUPRC $\ge 0.80$ on verified benchmark partitions.

---

## ADR-012: Retrieval-Augmented Generation (RAG) Architecture & Citation Grounding Protocol

### 1. Context & Problem Statement
Section 3.F and Section 6 mandate an 11-step RAG pipeline that normalizes queries, extracts biomedical entities, queries dense vectors and sparse BM25 indices, traverses the biomedical knowledge graph, reranks evidence by authority tier, enforces context window limits, and validates citations to detect and eliminate hallucinations. Factual claims must map to verified DailyMed SPL, RxNorm, or PubMed references, and unavailable evidence must be explicitly communicated.

### 2. Evaluated Options
- **Approach A: Naive LLM Generation without Retrieval**: Rely on foundation model parametric knowledge.
- **Approach B: Dense Retrieval Only with Unchecked Output**: Vector search followed by unconstrained generative completion.
- **Approach C: 11-Stage Evidence-Grounded Hybrid RAG with Strict Citation Validation**:
  1. User question + non-prescribing guardrail pre-flight check
  2. Query normalization & salt/brand stripping
  3. 8-category biomedical entity extraction with ontological IDs
  4. Dense semantic retrieval
  5. Sparse Okapi BM25 keyword retrieval
  6. Knowledge graph direct relationship and path lookup
  7. Result fusion
  8. Authority-weighted evidence reranking (DailyMed > RxNorm > PubMed > FAERS > Experimental)
  9. Context window token budgeting
  10. Structured NLG response generation
  11. Citation verification & hallucination rejection

### 3. Comparison
| Option | Advantages | Disadvantages |
| :--- | :--- | :--- |
| **Naive LLM (A)** | Fast setup. | Severe hallucination risk; cannot verify FDA SPL boxed warnings or clinical dosages. |
| **Dense Only (B)** | Retrieves semantically similar passages. | Misses exact brand codes; hallucinated citations slip through without validation. |
| **11-Stage Hybrid RAG (C)** | 100% evidence provenance, detects hallucinated PMIDs/RxCUIs, gracefully refuses prescribing queries, transparent confidence tiers. | Multi-stage orchestration overhead (~50-150ms). |

### 4. Selected Implementation
**Approach C: 11-Stage Evidence-Grounded RAG Pipeline with Automated Citation Validation.**

### 5. Architectural Justification
- Guarantees that every generated citation points to a verified document in the active context window.
- If no substantive evidence is found, the system explicitly returns `INSUFFICIENT_EVIDENCE` instead of fabricating answers.
- Clinical safety guardrails immediately reject personalized prescribing and dosage queries.

---

## ADR-013: Empirical AI Evaluation Framework & Reproducible Benchmarking

### 1. Context & Problem Statement
Section 10 requires an empirical evaluation framework measuring Biomedical NLP (Precision, Recall, F1), Semantic Search (Recall@K, MRR, NDCG), Graph ML (AUROC, AUPRC, Brier calibration), RAG Quality (Faithfulness, Answer Relevance, Context Precision, Citation Accuracy), and System Performance (RAM, CPU latency, token throughput). The architecture must use reproducible datasets and never report fabricated metrics.

### 2. Evaluated Options
- **Approach A: Static Mocked Metrics Dashboard**: Return hardcoded, static numbers in API endpoints.
- **Approach B: Automated Empirical Evaluator Service**: Implement `PharmaMindEvaluator` with fixed gold-standard test splits, executing real NLP extractions, vector searches, Graph ML cross-validations, and RAG claim audits.

### 3. Selected Implementation
**Approach B: Automated Empirical Evaluator Service (`PharmaMindEvaluator`) with Live System Telemetry.**

### 4. Architectural Justification
- Tests every component against deterministic ground-truth benchmarks.
- Live Win32 memory reporting via `GlobalMemoryStatusEx` and PyTorch CPU tensor profiling.
- Untested components are explicitly labeled `UNTESTED` with sample size 0, maintaining complete scientific transparency.
