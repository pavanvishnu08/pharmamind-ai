"""
PharmaMind AI - Biomedical Named Entity Recognition (NER) Service
Extracts 8 distinct biomedical entity categories with character offsets,
spelling variation normalization, and terminology system mapping (RxNorm, MeSH, MedDRA).
"""

from typing import Dict, Any, List, Optional, Tuple, Set
import re
import logging
from dataclasses import dataclass
from app.services.drug_normalization.normalizer import DrugNormalizer, compute_similarity_ratio

logger = logging.getLogger("pharmamind.services.entity_extraction")


@dataclass
class ExtractedEntity:
    """Standardized biomedical entity representation with character boundaries and ontological linkage."""
    text: str
    label: str  # DRUG, INGREDIENT, DISEASE, SYMPTOM, PROTEIN, PATHWAY, ADVERSE_EFFECT, DRUG_CLASS
    start_char: int
    end_char: int
    normalized_name: str
    normalized_id: str
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "label": self.label,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "normalized_name": self.normalized_name,
            "normalized_id": self.normalized_id,
            "confidence": self.confidence
        }


# Curated Ontological Gazetteers for High-Precision Biomedical Entity Extraction
BIOMEDICAL_GAZETTEER: Dict[str, List[Dict[str, Any]]] = {
    "DRUG": [
        {"terms": ["glucophage", "fortamet", "glumetza"], "name": "Glucophage", "id": "RxNorm:104443"},
        {"terms": ["coumadin", "jantoven"], "name": "Coumadin", "id": "RxNorm:202421"},
        {"terms": ["lipitor"], "name": "Lipitor", "id": "RxNorm:153165"},
        {"terms": ["zocor"], "name": "Zocor", "id": "RxNorm:104489"},
        {"terms": ["plavix"], "name": "Plavix", "id": "RxNorm:213169"},
        {"terms": ["prilosec", "losec"], "name": "Prilosec", "id": "RxNorm:151608"},
        {"terms": ["prinivil", "zestril"], "name": "Prinivil", "id": "RxNorm:152523"},
        {"terms": ["bayer aspirin", "bufferin", "ecotrin"], "name": "Bayer Aspirin", "id": "RxNorm:215568"}
    ],
    "INGREDIENT": [
        {"terms": ["metformin", "metformin hydrochloride", "metformin hcl"], "name": "Metformin", "id": "RxNorm:6809"},
        {"terms": ["warfarin", "warfarin sodium"], "name": "Warfarin", "id": "RxNorm:11289"},
        {"terms": ["aspirin", "acetylsalicylic acid"], "name": "Aspirin", "id": "RxNorm:1191"},
        {"terms": ["lisinopril", "lisinopril dihydrate"], "name": "Lisinopril", "id": "RxNorm:29046"},
        {"terms": ["simvastatin"], "name": "Simvastatin", "id": "RxNorm:36567"},
        {"terms": ["atorvastatin"], "name": "Atorvastatin", "id": "RxNorm:83367"},
        {"terms": ["clopidogrel"], "name": "Clopidogrel", "id": "RxNorm:32968"},
        {"terms": ["omeprazole"], "name": "Omeprazole", "id": "RxNorm:7646"},
        {"terms": ["ibuprofen"], "name": "Ibuprofen", "id": "RxNorm:5640"},
        {"terms": ["acetaminophen", "paracetamol"], "name": "Acetaminophen", "id": "RxNorm:161"}
    ],
    "DISEASE": [
        {"terms": ["type 2 diabetes mellitus", "type 2 diabetes", "t2d", "t2dm"], "name": "Type 2 Diabetes Mellitus", "id": "MeSH:D003924"},
        {"terms": ["hypertension", "high blood pressure"], "name": "Essential Hypertension", "id": "MeSH:D006973"},
        {"terms": ["deep vein thrombosis", "dvt"], "name": "Deep Vein Thrombosis", "id": "MeSH:D020246"},
        {"terms": ["pulmonary embolism", "pe"], "name": "Pulmonary Embolism", "id": "MeSH:D011655"},
        {"terms": ["atrial fibrillation", "afib", "a-fib"], "name": "Atrial Fibrillation", "id": "MeSH:D001281"},
        {"terms": ["hyperlipidemia", "hypercholesterolemia", "dyslipidemia"], "name": "Hyperlipidemia", "id": "MeSH:D006949"},
        {"terms": ["myocardial infarction", "heart attack"], "name": "Myocardial Infarction", "id": "MeSH:D009203"},
        {"terms": ["heart failure", "congestive heart failure", "chf"], "name": "Heart Failure", "id": "MeSH:D006333"},
        {"terms": ["stroke", "cerebrovascular accident", "cva", "ischemic stroke"], "name": "Cerebrovascular Accident", "id": "MeSH:D020521"}
    ],
    "SYMPTOM": [
        {"terms": ["chest pain", "angina"], "name": "Chest Pain", "id": "MeSH:D002637"},
        {"terms": ["dyspnea", "shortness of breath"], "name": "Dyspnea", "id": "MeSH:D004417"},
        {"terms": ["dry cough", "cough"], "name": "Cough", "id": "MeSH:D003371"},
        {"terms": ["dizziness", "lightheadedness", "vertigo"], "name": "Dizziness", "id": "MeSH:D004244"},
        {"terms": ["fatigue", "tiredness", "lethargy"], "name": "Fatigue", "id": "MeSH:D005221"},
        {"terms": ["edema", "peripheral edema", "swelling"], "name": "Edema", "id": "MeSH:D004487"},
        {"terms": ["myalgia", "muscle aches", "muscle pain"], "name": "Myalgia", "id": "MeSH:D063806"},
        {"terms": ["headache"], "name": "Headache", "id": "MeSH:D006261"},
        {"terms": ["epistaxis", "nosebleed"], "name": "Epistaxis", "id": "MeSH:D004844"},
        {"terms": ["tinnitus", "ringing in ears"], "name": "Tinnitus", "id": "MeSH:D014012"}
    ],
    "PROTEIN": [
        {"terms": ["vkorc1", "vitamin k epoxide reductase complex subunit 1", "vitamin k epoxide reductase"], "name": "VKORC1", "id": "HGNC:13647"},
        {"terms": ["cox-1", "ptgs1", "cyclooxygenase-1", "prostaglandin-endoperoxide synthase 1"], "name": "COX-1 (PTGS1)", "id": "HGNC:9604"},
        {"terms": ["cox-2", "ptgs2", "cyclooxygenase-2"], "name": "COX-2 (PTGS2)", "id": "HGNC:9605"},
        {"terms": ["hmg-coa reductase", "hmgcr", "3-hydroxy-3-methylglutaryl-coa reductase"], "name": "HMG-CoA Reductase (HMGCR)", "id": "HGNC:5006"},
        {"terms": ["angiotensin-converting enzyme", "ace"], "name": "Angiotensin-Converting Enzyme (ACE)", "id": "HGNC:2707"},
        {"terms": ["amp-activated protein kinase", "ampk"], "name": "AMP-Activated Protein Kinase (AMPK)", "id": "HGNC:9376"},
        {"terms": ["p2y12", "p2ry12", "purinergic receptor p2y12"], "name": "P2Y12 Receptor", "id": "HGNC:8541"},
        {"terms": ["cyp3a4", "cytochrome p450 3a4"], "name": "CYP3A4", "id": "HGNC:2637"},
        {"terms": ["cyp2c9", "cytochrome p450 2c9"], "name": "CYP2C9", "id": "HGNC:2623"}
    ],
    "PATHWAY": [
        {"terms": ["coagulation cascade", "blood coagulation cascade", "extrinsic pathway"], "name": "Coagulation Cascade", "id": "Reactome:R-HSA-140877"},
        {"terms": ["renin-angiotensin system", "raas", "renin-angiotensin-aldosterone system"], "name": "Renin-Angiotensin-Aldosterone System", "id": "Reactome:R-HSA-202237"},
        {"terms": ["gluconeogenesis", "hepatic gluconeogenesis"], "name": "Gluconeogenesis", "id": "Reactome:R-HSA-70263"},
        {"terms": ["cholesterol biosynthesis", "mevalonate pathway"], "name": "Cholesterol Biosynthesis", "id": "Reactome:R-HSA-191273"},
        {"terms": ["platelet activation", "platelet aggregation"], "name": "Platelet Activation and Aggregation", "id": "Reactome:R-HSA-76002"}
    ],
    "ADVERSE_EFFECT": [
        {"terms": ["major hemorrhage", "fatal bleeding", "major bleeding", "severe hemorrhage", "bleeding risk", "bleeding"], "name": "Major Hemorrhage", "id": "MedDRA:10025105"},
        {"terms": ["lactic acidosis", "metformin-associated lactic acidosis"], "name": "Lactic Acidosis", "id": "MedDRA:10023632"},
        {"terms": ["rhabdomyolysis"], "name": "Rhabdomyolysis", "id": "MedDRA:10039020"},
        {"terms": ["myopathy"], "name": "Myopathy", "id": "MedDRA:10028606"},
        {"terms": ["angioedema", "head and neck angioedema"], "name": "Angioedema", "id": "MedDRA:10002424"},
        {"terms": ["hyperkalemia", "elevated potassium"], "name": "Hyperkalemia", "id": "MedDRA:10020649"},
        {"terms": ["gastric ulcer", "peptic ulcer", "gi ulceration"], "name": "Gastric Ulcer", "id": "MedDRA:10017849"},
        {"terms": ["gastrointestinal hemorrhage", "gi bleeding", "gastrointestinal bleeding"], "name": "Gastrointestinal Hemorrhage", "id": "MedDRA:10017955"},
        {"terms": ["acute kidney injury", "renal impairment", "acute renal failure"], "name": "Acute Kidney Injury", "id": "MedDRA:10069339"}
    ],
    "DRUG_CLASS": [
        {"terms": ["biguanide", "biguanides", "biguanide antidiabetic agent"], "name": "Biguanides", "id": "ATC:A10BA"},
        {"terms": ["vitamin k antagonist", "coumarin anticoagulant", "vitamin k antagonists"], "name": "Vitamin K Antagonists", "id": "ATC:B01AA"},
        {"terms": ["hmg-coa reductase inhibitor", "statin", "statins"], "name": "HMG-CoA Reductase Inhibitors (Statins)", "id": "ATC:C10AA"},
        {"terms": ["ace inhibitor", "angiotensin-converting enzyme inhibitor", "ace inhibitors"], "name": "ACE Inhibitors", "id": "ATC:C09AA"},
        {"terms": ["nsaid", "nonsteroidal anti-inflammatory drug", "nsaids"], "name": "NSAIDs", "id": "ATC:M01A"},
        {"terms": ["antiplatelet", "antiplatelet agent", "platelet aggregation inhibitor"], "name": "Platelet Aggregation Inhibitors", "id": "ATC:B01AC"},
        {"terms": ["proton pump inhibitor", "ppi", "proton pump inhibitors"], "name": "Proton Pump Inhibitors", "id": "ATC:A02BC"}
    ]
}


class BiomedicalEntityExtractor:
    """
    Biomedical Named Entity Recognition and Ontological Normalization Pipeline.
    Supports exact span matching, regex boundary parsing, synonym mapping,
    and greedy non-overlapping span resolution across 8 categories.
    """

    def __init__(self, drug_normalizer: Optional[DrugNormalizer] = None):
        self.normalizer = drug_normalizer or DrugNormalizer()
        self._compiled_patterns: List[Tuple[re.Pattern, str, str, str, float]] = []
        self._build_compiled_patterns()

    def _build_compiled_patterns(self):
        """Compile regex patterns for high-speed deterministic extraction."""
        for label, entries in BIOMEDICAL_GAZETTEER.items():
            for item in entries:
                norm_name = item["name"]
                norm_id = item["id"]
                for term in item["terms"]:
                    # Create regex pattern with word boundaries
                    escaped = re.escape(term)
                    # Support hyphen / whitespace variations
                    pattern_str = rf"(?<!\w){escaped}(?!\w)"
                    pattern = re.compile(pattern_str, re.IGNORECASE)
                    confidence = 0.98 if len(term.split()) > 1 else 0.95
                    self._compiled_patterns.append((pattern, label, norm_name, norm_id, confidence))

        # Sort patterns by decreasing length of matched terms for greedy matching
        self._compiled_patterns.sort(key=lambda x: len(x[0].pattern), reverse=True)

    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """
        Extract non-overlapping biomedical entities from clinical or scientific text.
        Resolves conflicts by preferring longer spans and higher confidence.
        """
        if not text or not text.strip():
            return []

        raw_matches: List[ExtractedEntity] = []

        # 1. Gazetteer & Regex matching
        for pattern, label, norm_name, norm_id, confidence in self._compiled_patterns:
            for match in pattern.finditer(text):
                start, end = match.span()
                matched_text = text[start:end]
                raw_matches.append(
                    ExtractedEntity(
                        text=matched_text,
                        label=label,
                        start_char=start,
                        end_char=end,
                        normalized_name=norm_name,
                        normalized_id=norm_id,
                        confidence=confidence
                    )
                )

        # 2. Dynamic Normalizer Pass for Drugs / Ingredients
        # Scan words to catch drug names with salts or typos not directly in static gazetteer
        words = text.split()
        for word in words:
            clean_word = re.sub(r"[^\w-]", "", word)
            if len(clean_word) >= 4:
                norm_drug = self.normalizer.normalize(clean_word)
                if norm_drug.confidence_score >= 0.85 and norm_drug.rxcui:
                    # Find occurrences in text
                    pattern = re.compile(rf"(?<!\w){re.escape(clean_word)}(?!\w)", re.IGNORECASE)
                    for m in pattern.finditer(text):
                        start, end = m.span()
                        label = "DRUG" if norm_drug.original_brand else "INGREDIENT"
                        raw_matches.append(
                            ExtractedEntity(
                                text=text[start:end],
                                label=label,
                                start_char=start,
                                end_char=end,
                                normalized_name=norm_drug.display_name,
                                normalized_id=f"RxNorm:{norm_drug.rxcui}",
                                confidence=norm_drug.confidence_score
                            )
                        )

        # 3. Conflict Resolution: Greedy non-overlapping span filtering
        # Sort by start position, then by span length (descending), then confidence (descending)
        raw_matches.sort(key=lambda e: (e.start_char, -(e.end_char - e.start_char), -e.confidence))

        filtered_entities: List[ExtractedEntity] = []
        occupied_indices: Set[int] = set()

        for ent in raw_matches:
            span_indices = set(range(ent.start_char, ent.end_char))
            if not (span_indices & occupied_indices):
                filtered_entities.append(ent)
                occupied_indices.update(span_indices)

        # Re-sort filtered entities by start character offset
        filtered_entities.sort(key=lambda e: e.start_char)
        return filtered_entities

