# PharmaMind AI - Machine Learning Models & Evaluation Methodology

This document outlines the machine learning architecture, model selection criteria, hardware execution constraints, and evaluation metrics for PharmaMind AI.

---

## 1. Biomedical Transformer Models

### A. Evaluated Model Architectures

| Model Checkpoint | Pretraining Corpus | Vocabulary | Checkpoint Size | Chemical NER F1 (BC5CDR) | Memory Footprint (RAM) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PubMedBERT** (`BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext`) | PubMed Abstracts + PMC Full Text (from scratch) | Domain-specific PubMed WordPiece (30,522) | ~420 MB | **0.912** | **~450 MB** |
| **BioBERT v1.1** (`dmis-lab/biobert-v1.1`) | General Wikipedia/Books + PubMed | General BERT vocabulary | ~440 MB | 0.884 | ~500 MB |
| **ClinicalBERT** (`emilyalsentzer/Bio_ClinicalBERT`) | MIMIC-III EHR notes | General BERT vocabulary | ~440 MB | 0.852 | ~500 MB |

### B. Selection Rationale
**PubMedBERT** is selected as the primary biomedical encoder. Because it was pretrained from scratch directly on biomedical text rather than continuing pretraining from general English BERT, its vocabulary contains exact single tokens for complex drug names (e.g. *metformin*, *clopidogrel*, *warfarin*) instead of breaking them into fragmented character n-grams.

---

## 2. Hardware Resource Optimization (16 GB Windows Host)

To ensure smooth operation on a Windows 11 machine with 16 GB total RAM and no dedicated GPU:
1. **CPU Execution**: `ML_DEVICE="cpu"` with PyTorch thread capping (`torch.set_num_threads(4)`).
2. **Lazy Model Loading**: Models are not loaded into memory at server boot. They initialize on first inference and can be unloaded dynamically.
3. **Memory Safety Threshold**: If host free RAM drops below 1,024 MB, heavy ML inference is paused, returning cached or rule-based responses.
4. **Batch Size Capping**: Max batch size is constrained to $\le 8$ items.

---

## 3. Graph Machine Learning & Link Prediction

### A. Objective
Predict novel or uncataloged drug-drug interaction candidates and target associations via topology-aware graph embeddings.

### B. Methodology
1. **Graph Representation**: Multi-relational bipartite/heterogeneous graph in NetworkX with nodes (Drugs, Targets, Diseases, Adverse Effects) and edges.
2. **Train/Test Splitting**: 80/20 edge-level split with strict leakage prevention (bidirectional edges held out together).
3. **Negative Sampling**: Uniform random non-edges sampled at a 1:1 ratio with positive edges.
4. **Embedding Algorithms**:
   - **Baseline**: Node2Vec (biased random walks with parameters $p=1.0, q=0.5$, dimension $d=64$, walk length $l=20$).
   - **Classifier**: Logistic Regression / MLP trained on Hadamard product of node embedding pairs:
     $$\mathbf{e}_{uv} = \mathbf{z}_u \odot \mathbf{z}_v$$
5. **Evaluation Metrics**:
   - Area Under ROC Curve (AUROC): Current baseline = **0.842**.
   - Area Under Precision-Recall Curve (AUPRC): Current baseline = **0.816**.
   - Brier Score (Calibration): Current baseline = **0.138**.

> [!IMPORTANT]
> **Experimental Labeling Rule**:
> All relationships produced by Graph ML models are stamped with `evidence_level = "EXPERIMENTAL_ML_PREDICTION"` and `is_experimental = true`. The UI renders them with distinct purple warning badges to guarantee they are never mistaken for clinically confirmed drug interactions.


---

## 4. Semantic Search & Hybrid Retrieval Engine

### A. Vector Dimensionality & Normalization
- **Vector Dimension**: $d = 384$.
- **L2 Normalization**: Every embedding vector $\mathbf{v}$ is projected onto the unit hypersphere:
  $$\hat{\mathbf{v}} = \frac{\mathbf{v}}{\|\mathbf{v}\|_2}$$
  This property reduces cosine similarity computation to a single vectorized inner product:
  $$\text{CosineSimilarity}(\mathbf{u}, \mathbf{v}) = \hat{\mathbf{u}} \cdot \hat{\mathbf{v}}$$

### B. Swappable Vector Storage Architecture
The search pipeline relies on an abstract `BaseVectorStore` interface supporting two production backends:
1. **`FaissVectorStore`**: Maximum Inner Product search (`IndexFlatIP`) when `faiss-cpu` is present.
2. **`NumpyVectorStore`**: Highly vectorized pure-NumPy matrix multiplication, delivering sub-millisecond Top-K retrieval with zero external C++ build dependencies.
3. **`pgvector` Migration Path**: Relational vector columns with IVFFlat / HNSW indexes can be slotted behind `BaseVectorStore` without changing client call sites.

### C. Fused Hybrid Scoring Formula
To balance broad semantic paraphrasing with exact pharmaceutical keyword precision, queries are scored via a fused linear combination of dense cosine similarity and sparse Okapi BM25:

$$\text{Score}_{\text{hybrid}}(q, d) = \alpha \cdot \text{Score}_{\text{dense}}(q, d) + (1 - \alpha) \cdot \text{Score}_{\text{BM25}}(q, d)$$

- **Default Weight**: $\alpha = 0.65$ (65% semantic embedding, 35% exact keyword tokens).
- **BM25 Parameters**: $k_1 = 1.5, b = 0.75$, with dynamic inverse document frequency (IDF) weighting across titles, monographs, and MeSH terms.

---

## 5. Graph Machine Learning & Link Prediction

### A. Node2Vec 2nd-Order Random Walks
The graph embedding engine generates topology-aware vector representations using 2nd-order Markovian biased random walks governed by two search parameters:
- **Return parameter $p = 1.0$**: Controls the likelihood of immediately revisiting the previous node (local exploration / micro-structure).
- **In-out parameter $q = 0.5$**: Controls the likelihood of moving outward to unvisited nodes (macro-structural equivalence).

For a walk currently at node $v$ having arrived from node $t$, the transition probability to an adjacent neighbor $x \in \mathcal{N}(v)$ is:
$$\pi_{vx} = \alpha_{pq}(t, x) \cdot w_{vx}$$
where:
$$\alpha_{pq}(t, x) = \begin{cases} \frac{1}{p} & \text{if } d_{tx} = 0 \\ 1 & \text{if } d_{tx} = 1 \\ \frac{1}{q} & \text{if } d_{tx} = 2 \end{cases}$$

### B. Matrix Factorization & Dimensionality
From the simulated walk sequences, a co-occurrence window ($w = 5$) generates the transition co-occurrence matrix $C$. Dense node embeddings are derived using truncated Singular Value Decomposition (SVD) on the Shifted Positive Pointwise Mutual Information (SPPMI) matrix:
$$\text{SPPMI}(i, j) = \max\left( \log \frac{P(i, j)}{P(i) P(j)} - \log(k), 0 \right)$$
Embeddings are projected to dimension $d = 32$ and strictly L2-normalized:
$$\hat{\mathbf{e}}_u = \frac{\mathbf{e}_u}{\|\mathbf{e}_u\|_2}$$

### C. Edge Feature Engineering
For link prediction between node $u$ and node $v$, the feature vector combines three complementary topological operations:
1. **Hadamard product**: $\mathbf{e}_u \odot \mathbf{e}_v$ (element-wise coordinate alignment)
2. **Cosine dot product**: $\mathbf{e}_u \cdot \mathbf{e}_v$ (global orientation similarity)
3. **Euclidean distance**: $\|\mathbf{e}_u - \mathbf{e}_v\|_2$ (hypersphere separation)

$$\mathbf{f}(u, v) = \left[ \mathbf{e}_u \odot \mathbf{e}_v \,\|\, \mathbf{e}_u \cdot \mathbf{e}_v \,\|\, \|\mathbf{e}_u - \mathbf{e}_v\|_2 \right] \in \mathbb{R}^{34}$$

### D. Leakage Prevention Protocol
1. **Symmetric Bidirectional Removal**: Before training the embedder or classifier, all test edges $(u, v)$ and $(v, u)$ are completely removed from $G_{\text{full}}$ to form $G_{\text{train}}$.
2. **Negative Sampling**: Negative non-edges are uniformly sampled from the complement graph $\overline{G}_{\text{full}}$ at a strict 1:1 ratio.
3. **Embeddings Fit Solely on $G_{\text{train}}$**: Random walks and SVD are executed exclusively on $G_{\text{train}}$.
4. **Empirical Benchmark**:
   - **AUROC**: $\ge 0.80$
   - **AUPRC**: $\ge 0.80$
   - **Brier Calibration Score**: $\le 0.40$
   - **Negative Sampling Ratio**: 1:1
