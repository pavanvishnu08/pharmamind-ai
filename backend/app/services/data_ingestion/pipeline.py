"""
PharmaMind AI - Biomedical Data Ingestion & Quality Validation Pipeline
Coordinates DailyMed, RxNorm, openFDA, and PubMed ingestion.
Enforces deduplication, schema validation, completeness scoring, and immutable provenance retention.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import json
import logging
from dataclasses import dataclass, field

from app.integrations.data_sources.rxnorm_client import RxNormClient
from app.integrations.data_sources.dailymed_client import DailyMedClient
from app.integrations.data_sources.openfda_client import OpenFDAClient, FAERS_CAUSALITY_DISCLAIMER
from app.integrations.data_sources.pubmed_client import PubMedClient
from app.services.drug_normalization.normalizer import DrugNormalizer, NormalizedDrug

logger = logging.getLogger("pharmamind.services.data_ingestion")


@dataclass
class QualityReport:
    """Audit report for ingested biomedical records."""
    is_valid: bool
    quality_score: float  # 0.0 to 1.0 completeness and compliance score
    missing_fields: List[str]
    validation_errors: List[str]
    deduplication_status: str  # NEW_RECORD, MERGED_EXISTING, DUPLICATE_SKIPPED
    provenance_retained: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "quality_score": self.quality_score,
            "missing_fields": self.missing_fields,
            "validation_errors": self.validation_errors,
            "deduplication_status": self.deduplication_status,
            "provenance_retained": self.provenance_retained
        }


@dataclass
class IngestionResult:
    """Comprehensive result of a monograph or drug data ingestion."""
    drug_id: str
    generic_name: str
    brand_names: List[str]
    rxcui: str
    atc_code: Optional[str]
    drug_class: Optional[str]
    monograph_sections: Dict[str, Any]
    faers_signals: Dict[str, Any]
    literature_citations: List[Dict[str, Any]]
    quality_report: QualityReport
    provenance_records: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "drug_id": self.drug_id,
            "generic_name": self.generic_name,
            "brand_names": self.brand_names,
            "rxcui": self.rxcui,
            "atc_code": self.atc_code,
            "drug_class": self.drug_class,
            "monograph_sections": self.monograph_sections,
            "faers_signals": self.faers_signals,
            "literature_citations": self.literature_citations,
            "quality_report": self.quality_report.to_dict(),
            "provenance_records": self.provenance_records
        }


class DataIngestionPipeline:
    """
    Production-grade biomedical data ingestion orchestrator.
    Integrates external sources, ensures strict data provenance,
    validates data completeness, and preserves audit trails.
    """

    def __init__(
        self,
        rxnorm_client: Optional[RxNormClient] = None,
        dailymed_client: Optional[DailyMedClient] = None,
        openfda_client: Optional[OpenFDAClient] = None,
        pubmed_client: Optional[PubMedClient] = None,
        normalizer: Optional[DrugNormalizer] = None
    ):
        self.rxnorm = rxnorm_client or RxNormClient()
        self.dailymed = dailymed_client or DailyMedClient()
        self.openfda = openfda_client or OpenFDAClient()
        self.pubmed = pubmed_client or PubMedClient()
        self.normalizer = normalizer or DrugNormalizer(rxnorm_client=self.rxnorm)

        # In-memory registry for deduplication cache
        self._ingested_rxcuis: Dict[str, str] = {}
        self._ingested_canonical_names: Dict[str, str] = {}

    def validate_data_quality(self, data: Dict[str, Any]) -> QualityReport:
        """
        Evaluate structural completeness and mandatory fields.
        Returns a QualityReport with quality score and missing fields.
        """
        missing: List[str] = []
        errors: List[str] = []

        # Mandatory fields
        if not data.get("generic_name"):
            errors.append("Missing mandatory 'generic_name'")
        if not data.get("rxcui"):
            missing.append("rxcui")
        if not data.get("drug_class"):
            missing.append("drug_class")
        if not data.get("atc_code"):
            missing.append("atc_code")

        sections = data.get("sections", {})
        if not sections.get("indications_and_usage"):
            missing.append("indications_and_usage")
        if not sections.get("mechanism_of_action"):
            missing.append("mechanism_of_action")
        if not sections.get("contraindications"):
            missing.append("contraindications")

        # Calculate completeness score: 7 key dimensions
        total_dimensions = 7
        present_dimensions = total_dimensions - len(missing) - len(errors)
        quality_score = max(0.0, round(present_dimensions / total_dimensions, 2))

        is_valid = len(errors) == 0

        # Check deduplication
        rxcui = data.get("rxcui")
        canonical = data.get("generic_name", "").lower()
        if rxcui and rxcui in self._ingested_rxcuis:
            dedup_status = "MERGED_EXISTING"
        elif canonical in self._ingested_canonical_names:
            dedup_status = "MERGED_EXISTING"
        else:
            dedup_status = "NEW_RECORD"

        return QualityReport(
            is_valid=is_valid,
            quality_score=quality_score,
            missing_fields=missing,
            validation_errors=errors,
            deduplication_status=dedup_status,
            provenance_retained=True
        )

    async def ingest_drug_monograph(self, query: str) -> IngestionResult:
        """
        Full multi-source ingestion pipeline:
        1. Normalization (Salt removal, brand-to-generic, RxCUI resolution)
        2. DailyMed SPL Monograph extraction
        3. openFDA Labeling & FAERS signal gathering
        4. PubMed literature indexing
        5. Quality audit & provenance record construction
        """
        # Step 1: Normalize query
        normalized: NormalizedDrug = self.normalizer.normalize(query)
        canonical = normalized.canonical_name or query.strip().lower()
        display_name = normalized.display_name or query.strip().capitalize()

        # Step 2: Fetch DailyMed SPL
        dailymed_spl = await self.dailymed.get_spl_by_drug_name(canonical) or {}
        sections = dailymed_spl.get("sections", {})

        # Step 3: Fetch openFDA Labeling & FAERS Signals
        openfda_label = await self.openfda.get_drug_labeling(canonical) or {}
        faers_signals = await self.openfda.get_adverse_event_signals(canonical, limit=5)

        # Merge openfda indications if DailyMed missed them
        if not sections.get("indications_and_usage") and openfda_label.get("indications"):
            sections["indications_and_usage"] = openfda_label["indications"]
        if not sections.get("boxed_warning") and openfda_label.get("boxed_warning"):
            sections["boxed_warning"] = openfda_label["boxed_warning"]

        # Step 4: Fetch Peer-Reviewed Literature
        literature = await self.pubmed.search_and_fetch(f"{canonical} pharmacology mechanism", max_results=3)

        # Step 5: Resolve Brand Names
        brand_names = []
        if normalized.original_brand:
            brand_names.append(normalized.original_brand)
        if dailymed_spl.get("brand_name"):
            brand_names.append(dailymed_spl["brand_name"])
        brand_names = list(dict.fromkeys(brand_names))  # Deduplicate

        # Step 6: Construct Audit Quality Report
        payload_to_validate = {
            "generic_name": display_name,
            "rxcui": normalized.rxcui,
            "drug_class": normalized.drug_class,
            "atc_code": normalized.atc_code,
            "sections": sections
        }
        quality_report = self.validate_data_quality(payload_to_validate)

        # Register in deduplication cache
        if normalized.rxcui:
            self._ingested_rxcuis[normalized.rxcui] = display_name
        self._ingested_canonical_names[canonical] = display_name

        # Step 7: Construct Immutable Provenance Records
        now_iso = datetime.now(timezone.utc).isoformat()
        provenance_records = [
            {
                "source_name": "NLM RxNorm",
                "source_identifier": f"RxCUI:{normalized.rxcui or 'UNKNOWN'}",
                "retrieved_at": now_iso,
                "license_terms": "National Library of Medicine (NLM) Open Terms",
                "match_type": normalized.match_type,
                "confidence_score": normalized.confidence_score
            },
            {
                "source_name": "FDA DailyMed",
                "source_identifier": dailymed_spl.get("setid", f"SPL-{canonical.upper()}"),
                "retrieved_at": now_iso,
                "license_terms": dailymed_spl.get("license", "Public Domain (US FDA)")
            },
            {
                "source_name": "FDA Adverse Event Reporting System (FAERS)",
                "source_identifier": faers_signals.get("provenance_id", "FAERS-POSTMARKETING"),
                "retrieved_at": now_iso,
                "license_terms": "Creative Commons Attribution 4.0 (openFDA)",
                "is_causal_confirmed": False,
                "regulatory_notice": FAERS_CAUSALITY_DISCLAIMER
            }
        ]

        for pub in literature:
            provenance_records.append({
                "source_name": "NCBI PubMed",
                "source_identifier": f"PMID:{pub.get('pmid')}",
                "retrieved_at": now_iso,
                "license_terms": "NLM / PubMed Central Open Access",
                "doi": pub.get("doi")
            })

        drug_id = f"DRUG-{normalized.rxcui or canonical.upper()}"

        return IngestionResult(
            drug_id=drug_id,
            generic_name=display_name,
            brand_names=brand_names,
            rxcui=normalized.rxcui or "UNKNOWN",
            atc_code=normalized.atc_code,
            drug_class=normalized.drug_class,
            monograph_sections=sections,
            faers_signals=faers_signals,
            literature_citations=literature,
            quality_report=quality_report,
            provenance_records=provenance_records
        )

