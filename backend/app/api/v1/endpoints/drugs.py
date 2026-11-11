"""
PharmaMind AI - Drug Information Endpoints
Includes search, normalization, biomedical entity extraction, and multi-source ingestion.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.database.session import get_db
from app.models.drug import Drug, Ingredient, DrugIngredient, DrugSynonym
from app.schemas.drug import (
    DrugResponse,
    DrugCreate,
    DrugNormalizationRequest,
    DrugNormalizationResponse,
    EntityExtractionRequest,
    EntityExtractionResponse,
    ExtractedEntityResponse,
    DrugIngestionRequest,
    DrugIngestionResponse
)
from app.services.drug_normalization.normalizer import DrugNormalizer
from app.services.entity_extraction.extractor import BiomedicalEntityExtractor
from app.services.data_ingestion.pipeline import DataIngestionPipeline

router = APIRouter()

# Singletons for services
_normalizer = DrugNormalizer()
_extractor = BiomedicalEntityExtractor(drug_normalizer=_normalizer)
_ingestion_pipeline = DataIngestionPipeline(normalizer=_normalizer)

# Initial Verified Authoritative Dataset for Bootstrap
INITIAL_BOOTSTRAP_DRUGS = [
    {
        "generic_name": "Metformin",
        "brand_name": "Glucophage",
        "rxnorm_cui": "6809",
        "atc_code": "A10BA02",
        "drug_class": "Biguanide Antidiabetic Agent",
        "description": "First-line oral anti-hyperglycemic agent used to improve glucose tolerance in patients with type 2 diabetes mellitus.",
        "mechanism_of_action": "Decreases hepatic glucose production, decreases intestinal absorption of glucose, and improves insulin sensitivity by increasing peripheral glucose uptake and utilization via AMP-activated protein kinase (AMPK) activation.",
        "route_of_administration": "Oral",
        "synonyms": [
            {"synonym": "Glucophage", "source": "DailyMed", "language": "en"},
            {"synonym": "Fortamet", "source": "RxNorm", "language": "en"},
            {"synonym": "Metformin Hydrochloride", "source": "USP", "language": "en"}
        ]
    },
    {
        "generic_name": "Warfarin",
        "brand_name": "Coumadin",
        "rxnorm_cui": "11289",
        "atc_code": "B01AA03",
        "drug_class": "Vitamin K Antagonist Anticoagulant",
        "description": "Oral anticoagulant medication indicated for the prophylaxis and treatment of venous thrombosis and pulmonary embolism.",
        "mechanism_of_action": "Competitively inhibits the vitamin K epoxide reductase complex subunit 1 (VKORC1), depleting functional vitamin K reserves and reducing synthesis of active clotting factors II, VII, IX, and X.",
        "route_of_administration": "Oral",
        "synonyms": [
            {"synonym": "Coumadin", "source": "DailyMed", "language": "en"},
            {"synonym": "Jantoven", "source": "RxNorm", "language": "en"},
            {"synonym": "Warfarin Sodium", "source": "USP", "language": "en"}
        ]
    },
    {
        "generic_name": "Aspirin",
        "brand_name": "Bayer Aspirin",
        "rxnorm_cui": "1191",
        "atc_code": "B01AC06",
        "drug_class": "Nonsteroidal Anti-inflammatory Drug (NSAID) / Antiplatelet",
        "description": "Analgesic, antipyretic, anti-inflammatory, and platelet aggregation inhibitor.",
        "mechanism_of_action": "Irreversibly inactivates cyclooxygenase-1 (COX-1) and cyclooxygenase-2 (COX-2) via acetylation of a specific serine residue, suppressing prostaglandin and thromboxane A2 synthesis.",
        "route_of_administration": "Oral",
        "synonyms": [
            {"synonym": "Acetylsalicylic Acid", "source": "IUPAC", "language": "en"},
            {"synonym": "ASA", "source": "Medical Acronym", "language": "en"},
            {"synonym": "Ecotrin", "source": "DailyMed", "language": "en"}
        ]
    },
    {
        "generic_name": "Lisinopril",
        "brand_name": "Prinivil",
        "rxnorm_cui": "29046",
        "atc_code": "C09AA03",
        "drug_class": "Angiotensin-Converting Enzyme (ACE) Inhibitor",
        "description": "Oral antihypertensive agent used for treatment of hypertension, heart failure, and post-myocardial infarction.",
        "mechanism_of_action": "Competitively inhibits ACE, blocking conversion of angiotensin I to the potent vasoconstrictor angiotensin II, thereby reducing systemic vascular resistance and aldosterone secretion.",
        "route_of_administration": "Oral",
        "synonyms": [
            {"synonym": "Zestril", "source": "DailyMed", "language": "en"},
            {"synonym": "Qbrelis", "source": "RxNorm", "language": "en"}
        ]
    },
    {
        "generic_name": "Simvastatin",
        "brand_name": "Zocor",
        "rxnorm_cui": "36567",
        "atc_code": "C10AA01",
        "drug_class": "HMG-CoA Reductase Inhibitor (Statin)",
        "description": "Lipid-lowering agent indicated to reduce risk of cardiovascular events and hyperlipidemia.",
        "mechanism_of_action": "Competitively inhibits 3-hydroxy-3-methylglutaryl-coenzyme A (HMG-CoA) reductase, the rate-limiting enzyme in cholesterol biosynthesis, upregulating hepatic LDL receptors.",
        "route_of_administration": "Oral",
        "synonyms": [
            {"synonym": "Zocor", "source": "DailyMed", "language": "en"},
            {"synonym": "Flolipid", "source": "RxNorm", "language": "en"}
        ]
    }
]


async def seed_bootstrap_drugs_if_empty(db: AsyncSession):
    """Seed initial verified records if the database is currently empty."""
    res = await db.execute(select(func.count(Drug.id)))
    count = res.scalar_one_or_none() or 0
    if count == 0:
        for item in INITIAL_BOOTSTRAP_DRUGS:
            drug = Drug(
                generic_name=item["generic_name"],
                brand_name=item["brand_name"],
                rxnorm_cui=item["rxnorm_cui"],
                atc_code=item["atc_code"],
                drug_class=item["drug_class"],
                description=item["description"],
                mechanism_of_action=item["mechanism_of_action"],
                route_of_administration=item["route_of_administration"],
                is_fda_approved=True
            )
            db.add(drug)
            await db.flush()
            for s in item.get("synonyms", []):
                syn = DrugSynonym(
                    drug_id=drug.id,
                    synonym=s["synonym"],
                    source=s["source"],
                    language=s["language"]
                )
                db.add(syn)
        await db.commit()


@router.get("", response_model=List[DrugResponse])
async def list_drugs(
    q: Optional[str] = Query(None, description="Search query across generic name, brand name, or synonym"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List and search documented drugs with pagination.
    """
    await seed_bootstrap_drugs_if_empty(db)

    query = select(Drug)
    if q:
        search_term = f"%{q.strip().lower()}%"
        query = query.outerjoin(Drug.synonyms).where(
            or_(
                func.lower(Drug.generic_name).like(search_term),
                func.lower(Drug.brand_name).like(search_term),
                func.lower(DrugSynonym.synonym).like(search_term),
                func.lower(Drug.drug_class).like(search_term)
            )
        ).distinct()

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    drugs = result.scalars().all()
    return drugs


# Phase 2 Endpoints: Normalization, NER, Ingestion

@router.post("/normalize", response_model=DrugNormalizationResponse)
async def normalize_drug(payload: DrugNormalizationRequest):
    """
    Normalize a drug name by stripping pharmaceutical salts, resolving brand names
    to generic counterparts, correcting typos, and assigning RxNorm/ATC identifiers.
    """
    norm = _normalizer.normalize(payload.query)
    return DrugNormalizationResponse(
        input_text=norm.input_text,
        canonical_name=norm.canonical_name,
        display_name=norm.display_name,
        rxcui=norm.rxcui,
        atc_code=norm.atc_code,
        drug_class=norm.drug_class,
        match_type=norm.match_type,
        confidence_score=norm.confidence_score,
        salt_removed=norm.salt_removed,
        original_brand=norm.original_brand
    )


@router.post("/extract-entities", response_model=EntityExtractionResponse)
async def extract_biomedical_entities(payload: EntityExtractionRequest):
    """
    Extract biomedical entities across 8 categories (drugs, ingredients, diseases,
    symptoms, proteins/targets, pathways, adverse effects, drug classes) with character offsets.
    """
    entities = _extractor.extract_entities(payload.text)
    response_entities = [
        ExtractedEntityResponse(
            text=e.text,
            label=e.label,
            start_char=e.start_char,
            end_char=e.end_char,
            normalized_name=e.normalized_name,
            normalized_id=e.normalized_id,
            confidence=e.confidence
        )
        for e in entities
    ]
    return EntityExtractionResponse(
        text=payload.text,
        entity_count=len(response_entities),
        entities=response_entities
    )


@router.post("/ingest", response_model=DrugIngestionResponse)
async def ingest_drug(payload: DrugIngestionRequest):
    """
    Execute full multi-source ingestion pipeline for a given drug or monograph:
    RxNorm, DailyMed SPL, openFDA labeling & FAERS signals, and PubMed literature.
    """
    res = await _ingestion_pipeline.ingest_drug_monograph(payload.drug_name)
    return DrugIngestionResponse(
        drug_id=res.drug_id,
        generic_name=res.generic_name,
        brand_names=res.brand_names,
        rxcui=res.rxcui,
        atc_code=res.atc_code,
        drug_class=res.drug_class,
        monograph_sections=res.monograph_sections,
        faers_signals=res.faers_signals,
        literature_citations=res.literature_citations,
        quality_report=res.quality_report.to_dict(),
        provenance_records=res.provenance_records
    )


@router.get("/{drug_id}", response_model=DrugResponse)
async def get_drug(drug_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve single drug record by UUID or generic name.
    """
    await seed_bootstrap_drugs_if_empty(db)

    query = select(Drug).where(
        or_(
            Drug.id == drug_id,
            func.lower(Drug.generic_name) == drug_id.strip().lower()
        )
    )
    result = await db.execute(query)
    drug = result.scalars().first()
    if not drug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug '{drug_id}' not found in authoritative records."
        )
    return drug
