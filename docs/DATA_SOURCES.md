# PharmaMind AI - Biomedical Data Sources & Provenance Guidelines

PharmaMind AI integrates only legitimate, documented, open-access biomedical data sources. This document details each data source, its licensing terms, retrieval protocols, and strict causality disclaimers.

---

## 1. Primary Data Sources

### A. FDA DailyMed
- **Source**: National Library of Medicine (NLM) / US Food and Drug Administration (FDA).
- **Endpoint**: `https://dailymed.nlm.nih.gov/dailymed/services/v2`
- **Data Retained**: Structured Product Labeling (SPL), approved indications, contraindications, boxed warnings, mechanism of action, and drug-drug interactions.
- **License**: Public Domain (US Government work).
- **Identifiers**: SetID (GUID), National Drug Code (NDC).
- **Evidence Classification**: **Tier 1: Authoritative Verified**.

### B. NLM RxNorm
- **Source**: National Library of Medicine (NLM).
- **Endpoint**: `https://rxnav.nlm.nih.gov/REST`
- **Data Retained**: Standardized drug nomenclature, active ingredients, brand names, clinical drug components, and anatomical therapeutic chemical (ATC) mappings.
- **License**: UMLS Metathesaurus license (Free for research/public health use).
- **Identifiers**: RxNorm Concept Unique Identifier (RxCUI).
- **Role**: Primary drug normalization and synonym resolution engine.

### C. PubMed & PubMed Central (PMC) Open Access
- **Source**: National Center for Biotechnology Information (NCBI).
- **Endpoint**: NCBI E-utilities (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`)
- **Data Retained**: Peer-reviewed abstracts, titles, publication dates, journal citations, and MeSH terms.
- **License**: Open Access (CC-BY / Public Domain for PMC Open Access subset).
- **Identifiers**: PubMed ID (PMID), PubMed Central ID (PMCID), Digital Object Identifier (DOI).
- **Evidence Classification**: **Tier 2: Peer-Reviewed Scientific Literature**.

### D. openFDA Drug Labeling & FAERS
- **Source**: US Food and Drug Administration.
- **Endpoint**: `https://api.fda.gov/drug/`
- **Data Retained**: Adverse event reports, 510(k) clearances, NDC directory.
- **License**: Open Data Commons Attribution License (Public Domain).
- **Critical Caveat Regarding FAERS Data**:
  > [!CAUTION]
  > **FAERS Reports Are Signals, NOT Proof of Causality.**
  > FAERS data consists of spontaneous adverse event reports submitted by healthcare providers and consumers. The submission of a report does not constitute an admission that healthcare personnel, user facility, or the medication caused or contributed to the event. PharmaMind AI explicitly flags all FAERS signals as **Tier 4: Uncertain Signal** and never presents them as clinically confirmed drug interactions.

---

## 2. Provenance Storage & Data Hygiene

Every stored biomedical assertion in `drug_relationships` and `source_records` must retain:
1. `provenance_source`: Name of the authoritative agency or repository (e.g. `FDA DailyMed`, `PubMed`, `RxNorm`).
2. `provenance_id`: Unique persistent identifier (e.g. `RxCUI:6809`, `PMID:11502884`, `SetID:7b79a781`).
3. `confidence_score`: Float value between 0.0 and 1.0 reflecting validation status.
4. `evidence_level`: One of `VERIFIED_AUTHORITATIVE`, `SCIENTIFIC_LITERATURE`, `EXPERIMENTAL_ML_PREDICTION`, or `UNCERTAIN_SIGNAL`.
5. `retrieved_date`: UTC ISO-8601 timestamp recording when the record was ingested.


---

## 3. Data Ingestion Pipeline & Quality Validation Rules

### A. Data Quality Completeness Dimensions
The `DataIngestionPipeline` audits every monograph across 7 core quality dimensions:
1. `generic_name`: Non-empty canonical title.
2. `rxcui`: Valid NLM RxNorm Concept Unique Identifier.
3. `drug_class`: Pharmacological or therapeutic class designation.
4. `atc_code`: WHO Anatomical Therapeutic Chemical code.
5. `indications_and_usage`: FDA-approved clinical indications.
6. `mechanism_of_action`: Molecular and biological mechanism description.
7. `contraindications`: Documented clinical contraindications.

Records lacking non-essential fields receive a proportional `quality_score` ($\ge 0.0$ to $1.0$) and a transparent `missing_fields` list.

### B. Deduplication Protocol
- Primary Key: `rxcui` (RxNorm Concept Unique Identifier).
- Secondary Key: Canonical generic name (lowercase alphanumeric).
- Existing records are marked as `MERGED_EXISTING` and updated rather than duplicated.

### C. Ingestion Output Schema (`IngestionResult`)

```json
{
  "drug_id": "DRUG-6809",
  "generic_name": "Metformin",
  "brand_names": ["Glucophage", "Fortamet", "Glumetza"],
  "rxcui": "6809",
  "atc_code": "A10BA02",
  "drug_class": "Biguanide Antidiabetic Agent",
  "monograph_sections": {
    "boxed_warning": "WARNING: LACTIC ACIDOSIS...",
    "indications_and_usage": "Metformin Hydrochloride Tablets are indicated...",
    "contraindications": "Severe renal impairment (eGFR below 30 mL/min/1.73 m2)...",
    "mechanism_of_action": "Decreases hepatic glucose production...",
    "drug_interactions": "Carbonic anhydrase inhibitors may increase risk..."
  },
  "faers_signals": {
    "drug_name": "Metformin",
    "is_causal_confirmed": false,
    "signal_type": "Spontaneous Adverse Event Postmarketing Signal",
    "signal_count": 58000,
    "top_adverse_reactions": [
      {"term": "DIARRHOEA", "count": 15420},
      {"term": "NAUSEA", "count": 11200},
      {"term": "LACTIC ACIDOSIS", "count": 8940}
    ],
    "disclaimer": "CLINICAL CAUTION: FDA Adverse Event Reporting System (FAERS) data represent spontaneous post-marketing reports... A reported event does NOT establish pharmacological causality...",
    "confidence_status": "EPIDEMIOLOGICAL_SIGNAL_ONLY"
  },
  "literature_citations": [
    {
      "pmid": "12558500",
      "title": "Metformin and AMP-activated protein kinase...",
      "journal": "Journal of Clinical Investigation",
      "year": 2001,
      "doi": "10.1172/JCI13505"
    }
  ],
  "quality_report": {
    "is_valid": true,
    "quality_score": 1.0,
    "missing_fields": [],
    "validation_errors": [],
    "deduplication_status": "NEW_RECORD",
    "provenance_retained": true
  },
  "provenance_records": [
    {"source_name": "NLM RxNorm", "source_identifier": "RxCUI:6809"},
    {"source_name": "FDA DailyMed", "source_identifier": "SPL-7b79a781"},
    {"source_name": "FDA Adverse Event Reporting System (FAERS)", "source_identifier": "FAERS-POSTMARKETING", "is_causal_confirmed": false}
  ]
}
```
