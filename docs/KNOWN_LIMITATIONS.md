# PharmaMind AI - Known Limitations & Engineering Boundaries

This document provides transparent disclosure of known technical and clinical limitations in PharmaMind AI.

---

## 1. Hardware & Compute Constraints

1. **CPU Inference Latency**: Running PubMedBERT and Sentence Transformers on an Intel 12-core CPU without a dedicated GPU yields an inference latency of 60–120ms per sentence. While acceptable for interactive consultations, batch document indexing requires batch scheduling.
2. **Host RAM Availability**: On a 16 GB machine running Windows 11 with typical background software, available free RAM fluctuates between 1.6 GB and 3.0 GB. Running multiple simultaneous transformer models (e.g. PubMedBERT + BioBERT simultaneously) risks triggering OS pagefile swapping. Lazy loading and thread limits mitigate this constraint.

---

## 2. Biomedical Data Coverage Boundaries

1. **Commercial Datasets Not Included**: DrugBank commercial datasets and proprietary hospital formularies are intentionally excluded to respect intellectual property terms. PharmaMind AI relies strictly on public-domain open-access sources (FDA DailyMed, RxNorm, openFDA, PubMed).
2. **Pediatric and Geriatric Dosage Exclusions**: The platform does not calculate or suggest adjusted dosages for renal impairment, hepatic insufficiency, pediatrics, or pregnancy.
3. **FAERS Signal Spontaneity**: Signals from FAERS reflect post-marketing reporting volume, not verified incidence or controlled incidence rates. A higher report count does not imply higher pharmacological causality.

---

## 3. Machine Learning & Graph Limitations

1. **Closed-World vs Open-World Link Prediction**: Graph ML link prediction assumes an open-world setting where unobserved edges may either be true non-interactions or undiscovered interactions. Predictions cannot replace in vitro CYP450 binding assays or Phase IV clinical monitoring.
2. **Language Coverage**: Monograph entity extraction is currently optimized for English-language medical labeling. International brand name synonyms in non-English languages are partially indexed via RxNorm foreign trade names but not fully mapped.

