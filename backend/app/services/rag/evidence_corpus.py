"""
PharmaMind AI - Curated Biomedical Evidence Corpus
Indexes verified DailyMed SPL monographs, RxNorm data, PubMed research, and Boxed Warnings
into the Hybrid Retrieval Engine (Dense Embeddings + BM25 Index).
"""

from typing import List, Dict, Any, Optional
import logging
from app.services.semantic_search.hybrid_search import HybridSearchEngine

logger = logging.getLogger("pharmamind.services.rag.evidence")

# Curated benchmark evidence corpus from authoritative sources
BENCHMARK_EVIDENCE_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "doc_id": "DAILYMED-WARFARIN-001",
        "title": "FDA DailyMed: Warfarin Sodium Tablets - Indications, Dosage, and Boxed Warning",
        "content": (
            "Warfarin sodium is an oral anticoagulant acting as a competitive inhibitor of the vitamin K epoxide "
            "reductase complex 1 (VKORC1). By inhibiting VKORC1, warfarin depletes functional vitamin K reserves, "
            "blocking gamma-carboxylation of coagulation factors II (prothrombin), VII, IX, and X, as well as "
            "endogenous anticoagulant proteins C and S. Indicated for prophylaxis and treatment of venous thromboembolism, "
            "pulmonary embolism, and thromboembolic complications associated with atrial fibrillation or cardiac valve replacement. "
            "BOXED WARNING: Warfarin can cause major or fatal bleeding. Regular monitoring of the International Normalized "
            "Ratio (INR) is required. Numerous drug, dietary, and genetic interactions affect anticoagulant response."
        ),
        "source_type": "DailyMed",
        "source_id": "RxCUI:11289",
        "authority_tier": 1.0,
        "evidence_status": "Authoritative",
        "metadata": {
            "drug_name": "Warfarin",
            "rxnorm_cui": "11289",
            "atc_code": "B01AA03",
            "boxed_warning": True,
            "target": "VKORC1"
        }
    },
    {
        "doc_id": "DAILYMED-METFORMIN-002",
        "title": "FDA DailyMed: Metformin Hydrochloride - Mechanism of Action and Clinical Pharmacology",
        "content": (
            "Metformin hydrochloride is an antihyperglycemic biguanide that improves glucose tolerance in patients "
            "with type 2 diabetes mellitus. It acts primarily by reducing hepatic gluconeogenesis through activation "
            "of AMP-activated protein kinase (AMPK) and inhibition of mitochondrial complex I. Secondary mechanisms include "
            "decreasing intestinal absorption of glucose and improving peripheral insulin sensitivity by increasing "
            "peripheral glucose uptake and utilization. Unlike sulfonylureas, metformin does not stimulate insulin secretion "
            "and does not cause hypoglycemia when used as monotherapy. "
            "BOXED WARNING: Lactic acidosis is a rare but severe metabolic complication that can occur due to metformin "
            "accumulation, particularly in patients with severe renal impairment (eGFR < 30 mL/min/1.73 m2)."
        ),
        "source_type": "DailyMed",
        "source_id": "RxCUI:6809",
        "authority_tier": 1.0,
        "evidence_status": "Authoritative",
        "metadata": {
            "drug_name": "Metformin",
            "rxnorm_cui": "6809",
            "atc_code": "A10BA02",
            "boxed_warning": True,
            "target": "AMPK"
        }
    },
    {
        "doc_id": "DAILYMED-LISINOPRIL-003",
        "title": "FDA DailyMed: Lisinopril Tablets - ACE Inhibitor Mechanism and Renal Hemodynamics",
        "content": (
            "Lisinopril is an oral synthetic peptide derivative, an angiotensin-converting enzyme (ACE) inhibitor. "
            "It inhibits ACE in human subjects and animals, preventing the conversion of angiotensin I to the potent "
            "vasoconstrictor angiotensin II. Decreased angiotensin II leads to decreased vasopressor activity and reduced "
            "aldosterone secretion, producing systemic vasodilation and decreased peripheral vascular resistance. "
            "Indicated for the treatment of hypertension, adjunctive therapy in systolic heart failure, and improving "
            "survival in hemodynamically stable patients within 24 hours of acute myocardial infarction. "
            "BOXED WARNING: Fetal toxicity - drugs that act directly on the renin-angiotensin system can cause injury "
            "and death to the developing fetus when administered during pregnancy."
        ),
        "source_type": "DailyMed",
        "source_id": "RxCUI:29046",
        "authority_tier": 1.0,
        "evidence_status": "Authoritative",
        "metadata": {
            "drug_name": "Lisinopril",
            "rxnorm_cui": "29046",
            "atc_code": "C09AA03",
            "boxed_warning": True,
            "target": "ACE"
        }
    },
    {
        "doc_id": "DAILYMED-ASPIRIN-004",
        "title": "FDA DailyMed: Aspirin (Acetylsalicylic Acid) - Antiplatelet and Anti-inflammatory Pharmacology",
        "content": (
            "Aspirin (acetylsalicylic acid) acts via irreversible acetylation and inactivation of cyclooxygenase-1 (COX-1) "
            "and cyclooxygenase-2 (COX-2). In platelets, inhibition of COX-1 permanently blocks the synthesis of "
            "thromboxane A2 (TXA2), a potent inducer of platelet aggregation and vasoconstriction, for the entire lifespan "
            "of the platelet (7-10 days). In peripheral tissues, inhibition of COX-2 reduces synthesis of pro-inflammatory "
            "prostaglandins (PGE2, PGF2a), mediating analgesic, antipyretic, and anti-inflammatory effects. Indicated for secondary "
            "prevention of cardiovascular events, acute coronary syndrome, and transient ischemic attacks. "
            "Adverse effects include dyspepsia, gastric mucosal erosion, gastrointestinal ulceration, and bleeding."
        ),
        "source_type": "DailyMed",
        "source_id": "RxCUI:1191",
        "authority_tier": 1.0,
        "evidence_status": "Authoritative",
        "metadata": {
            "drug_name": "Aspirin",
            "rxnorm_cui": "1191",
            "atc_code": "B01AC06",
            "boxed_warning": False,
            "target": "COX1/COX2"
        }
    },
    {
        "doc_id": "DAILYMED-SIMVASTATIN-005",
        "title": "FDA DailyMed: Simvastatin Tablets - HMG-CoA Reductase Inhibitor & CYP3A4 Metabolism",
        "content": (
            "Simvastatin is an inactive lactone prodrug that is hydrolyzed in vivo to its active beta-hydroxy acid form, "
            "which competitively inhibits 3-hydroxy-3-methylglutaryl-coenzyme A (HMG-CoA) reductase. HMG-CoA reductase "
            "catalyzes the conversion of HMG-CoA to mevalonate, an early and rate-limiting step in the biosynthesis of "
            "cholesterol. Inhibition upregulates high-affinity LDL receptors on hepatocytes, increasing catabolism of "
            "circulating LDL cholesterol. Simvastatin is extensively metabolized by cytochrome P450 3A4 (CYP3A4). "
            "Concomitant use with strong CYP3A4 inhibitors (clarithromycin, erythromycin, ketoconazole) significantly "
            "elevates simvastatin plasma concentrations, markedly increasing the risk of myopathy and rhabdomyolysis."
        ),
        "source_type": "DailyMed",
        "source_id": "RxCUI:36567",
        "authority_tier": 1.0,
        "evidence_status": "Authoritative",
        "metadata": {
            "drug_name": "Simvastatin",
            "rxnorm_cui": "36567",
            "atc_code": "C10AA01",
            "boxed_warning": False,
            "target": "HMGCR"
        }
    },
    {
        "doc_id": "DAILYMED-CLOPIDOGREL-006",
        "title": "FDA DailyMed: Clopidogrel Bisulfate - P2Y12 Antiplatelet Prodrug & CYP2C19 Bioactivation",
        "content": (
            "Clopidogrel is an oral thienopyridine prodrug that requires hepatic biotransformation to an active thiol "
            "metabolite primarily by CYP2C19, with contributions from CYP3A4, CYP2B6, and CYP1A2. The active metabolite "
            "irreversibly and selectively binds to the platelet P2Y12 ADP receptor, inhibiting ADP-mediated activation of the "
            "glycoprotein GPIIb/IIIa complex and preventing platelet cross-linking and aggregation. Indicated for acute coronary "
            "syndromes and stroke prevention. "
            "BOXED WARNING: Diminished antiplatelet effect in CYP2C19 poor metabolizers. Tests are available to identify "
            "CYP2C19 genotype. Consider alternative antiplatelet agents (e.g., prasugrel, ticagrelor) in poor metabolizers."
        ),
        "source_type": "DailyMed",
        "source_id": "RxCUI:32968",
        "authority_tier": 1.0,
        "evidence_status": "Authoritative",
        "metadata": {
            "drug_name": "Clopidogrel",
            "rxnorm_cui": "32968",
            "atc_code": "B01AC04",
            "boxed_warning": True,
            "target": "P2Y12"
        }
    },
    {
        "doc_id": "DDI-WARFARIN-ASPIRIN-007",
        "title": "Clinical DDI Monograph: Warfarin Sodium and Aspirin Pharmacodynamic Co-administration",
        "content": (
            "Co-administration of warfarin sodium and aspirin produces a potent synergistic pharmacodynamic interaction. "
            "Warfarin depletes clotting factors II, VII, IX, and X, impairing secondary hemostasis. Aspirin irreversibly "
            "inhibits platelet COX-1 and thromboxane A2 production, impairing primary hemostatic plug formation. "
            "Furthermore, aspirin can produce direct mucosal damage in the gastrointestinal tract. Clinical studies indicate "
            "a 3- to 5-fold increase in major gastrointestinal hemorrhage and intracranial bleeding risk when these agents "
            "are combined without gastroprotective therapy. Dual therapy should only be prescribed with strict clinical "
            "justification (e.g. mechanical heart valves with acute coronary disease) under frequent INR surveillance."
        ),
        "source_type": "DailyMed",
        "source_id": "SPL-Coumadin-DDI",
        "authority_tier": 1.0,
        "evidence_status": "Authoritative",
        "metadata": {
            "drug_1": "Warfarin",
            "drug_2": "Aspirin",
            "interaction_type": "Pharmacodynamic Synergism",
            "severity": "Major",
            "clinical_consequence": "Severe Hemorrhage Risk"
        }
    },
    {
        "doc_id": "DDI-WARFARIN-SIMVASTATIN-008",
        "title": "Clinical DDI Monograph: Warfarin Sodium and Simvastatin Metabolic Competition",
        "content": (
            "Simvastatin and warfarin exhibit pharmacokinetic and pharmacodynamic interactions. Both drugs undergo hepatic "
            "metabolism involving cytochrome P450 enzymes. While warfarin S-enantiomer is primarily cleared by CYP2C9 and "
            "R-enantiomer by CYP3A4 and CYP1A2, simvastatin is a substrate and weak competitive inhibitor of CYP3A4. "
            "Concomitant initiation or dose elevation of simvastatin can competitively inhibit R-warfarin clearance and alter "
            "protein binding, producing clinically significant elevations in prothrombin time (PT) and International "
            "Normalized Ratio (INR). Patients established on warfarin require baseline INR measurement prior to simvastatin "
            "initiation and close INR monitoring during statin titration."
        ),
        "source_type": "DailyMed",
        "source_id": "SPL-Zocor-DDI",
        "authority_tier": 1.0,
        "evidence_status": "Authoritative",
        "metadata": {
            "drug_1": "Warfarin",
            "drug_2": "Simvastatin",
            "interaction_type": "Pharmacokinetic Competitive CYP3A4",
            "severity": "Moderate",
            "clinical_consequence": "Elevated INR and Bleeding Risk"
        }
    },
    {
        "doc_id": "PUBMED-PMC-METFORMIN-009",
        "title": "NCBI PubMed: Cellular and Molecular Mechanisms of Metformin Action in Human Physiology",
        "content": (
            "In this comprehensive molecular review (PMID: 28416495, DOI: 10.1016/j.cmet.2017.04.018), researchers elucidate "
            "how metformin suppresses hepatic gluconeogenesis through both AMPK-dependent and AMPK-independent pathways. "
            "Metformin transiently inhibits mitochondrial respiratory chain Complex I, decreasing intracellular ATP/AMP ratios. "
            "This activates AMP-activated protein kinase (AMPK), leading to phosphorylation and cytoplasmic sequestration of "
            "transcription factor CRTC2, downregulating gluconeogenic genes PEPCK and G6Pase. Concurrently, elevated AMP inhibits "
            "fructose-1,6-bisphosphatase (FBPase), acutely halting gluconeogenesis independent of gene transcription."
        ),
        "source_type": "PubMed",
        "source_id": "PMID:28416495",
        "authority_tier": 0.85,
        "evidence_status": "Literature Supported",
        "metadata": {
            "pmid": "28416495",
            "doi": "10.1016/j.cmet.2017.04.018",
            "journal": "Cell Metabolism",
            "drug_name": "Metformin"
        }
    },
    {
        "doc_id": "PUBMED-PMC-WARFARIN-010",
        "title": "NCBI PubMed: Pharmacogenomics of Warfarin - CYP2C9 and VKORC1 Polymorphisms",
        "content": (
            "Clinical Pharmacogenetics Implementation Consortium (CPIC) guideline (PMID: 28198005, DOI: 10.1002/cpt.668) "
            "evaluates the impact of CYP2C9 (*2, *3 alleles) and VKORC1 (-1639G>A) variants on warfarin maintenance dosing. "
            "Patients carrying variant alleles require significantly lower warfarin doses to achieve therapeutic target INR (2.0-3.0) "
            "and experience a 2- to 3-fold higher incidence of supratherapeutic INR during treatment initiation. Pharmacogenetic "
            "dosing algorithms combining CYP2C9 and VKORC1 genotypes with clinical covariates explain >50% of dose variability."
        ),
        "source_type": "PubMed",
        "source_id": "PMID:28198005",
        "authority_tier": 0.85,
        "evidence_status": "Literature Supported",
        "metadata": {
            "pmid": "28198005",
            "doi": "10.1002/cpt.668",
            "journal": "Clinical Pharmacology & Therapeutics",
            "drug_name": "Warfarin"
        }
    }
]


def create_and_populate_evidence_corpus(engine: Optional[HybridSearchEngine] = None) -> HybridSearchEngine:
    """
    Instantiate and populate the HybridSearchEngine with curated biomedical evidence items.
    """
    if engine is None:
        engine = HybridSearchEngine(dense_weight=0.65)

    docs = []
    for item in BENCHMARK_EVIDENCE_DOCUMENTS:
        doc = {
            "id": item["doc_id"],
            "title": item["title"],
            "content": item["content"],
            "source_type": item["source_type"],
            "source_id": item["source_id"],
            "authority_tier": item["authority_tier"],
            "evidence_status": item["evidence_status"],
            "metadata": {
                "source_type": item["source_type"],
                "source_id": item["source_id"],
                "authority_tier": item["authority_tier"],
                "evidence_status": item["evidence_status"],
                **item.get("metadata", {})
            }
        }
        docs.append(doc)

    engine.index_documents(docs, text_field="content")
    logger.info("Populated biomedical evidence corpus with %d authoritative documents.", len(docs))
    return engine
