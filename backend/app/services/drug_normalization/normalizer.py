"""
PharmaMind AI - Biomedical Drug Normalization Service
Performs pharmaceutical salt stripping, brand-to-generic mapping,
typo correction (Levenshtein distance), and RxNorm RxCUI/ATC code resolution.
"""

from typing import Dict, Any, List, Optional, Tuple
import re
import logging
from dataclasses import dataclass
from app.integrations.data_sources.rxnorm_client import RxNormClient, RXNORM_OFFLINE_CACHE

logger = logging.getLogger("pharmamind.services.drug_normalization")

# Common pharmaceutical salt formulations and hydration states
PHARMACEUTICAL_SALTS: List[str] = [
    "hydrochloride", "hcl", "sodium", "potassium", "calcium",
    "succinate", "tartrate", "maleate", "mesylate", "besylate",
    "sulfate", "sulphate", "phosphate", "acetate", "citrate",
    "fumarate", "gluconate", "nitrate", "bromide", "iodide",
    "dihydrate", "trihydrate", "monohydrate", "hydrate",
    "dipotassium", "disodium", "valerate", "propionate", "benzoate",
    "palmitate", "decanoate", "lactate", "furoate", "enanthate"
]

# Curated Brand-to-Generic Mappings
BRAND_TO_GENERIC: Dict[str, str] = {
    # Antidiabetic
    "glucophage": "metformin",
    "fortamet": "metformin",
    "glumetza": "metformin",
    "riomet": "metformin",
    # Anticoagulants & Antiplatelets
    "coumadin": "warfarin",
    "jantoven": "warfarin",
    "plavix": "clopidogrel",
    "effient": "prasugrel",
    "brilinta": "ticagrelor",
    "eliquis": "apixaban",
    "xarelto": "rivaroxaban",
    "pradaxa": "dabigatran",
    # Statins
    "lipitor": "atorvastatin",
    "zocor": "simvastatin",
    "crestor": "rosuvastatin",
    "pravachol": "pravastatin",
    "mevacor": "lovastatin",
    # Antihypertensives & ACE/ARBs
    "prinivil": "lisinopril",
    "zestril": "lisinopril",
    "qbrelis": "lisinopril",
    "cozaar": "losartan",
    "diovan": "valsartan",
    "norvasc": "amlodipine",
    "lopressor": "metoprolol",
    "toprol-xl": "metoprolol",
    "coreg": "carvedilol",
    # Analgesics & NSAIDs
    "bayer": "aspirin",
    "bayer aspirin": "aspirin",
    "ecotrin": "aspirin",
    "bufferin": "aspirin",
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
    "aleve": "naproxen",
    "tylenol": "acetaminophen",
    "celebrex": "celecoxib",
    # Gastrointestinal
    "prilosec": "omeprazole",
    "losec": "omeprazole",
    "nexium": "esomeprazole",
    "prevacid": "lansoprazole",
    "pepcid": "famotidine",
    # Diuretics & CNS
    "lasix": "furosemide",
    "prozac": "fluoxetine",
    "zoloft": "sertraline",
    "xanax": "alprazolam",
    "valium": "diazepam"
}

# Known Canonical Generic Drug Registry
CANONICAL_DRUGS: Dict[str, Dict[str, Any]] = {
    "metformin": {
        "rxcui": "6809",
        "atc_code": "A10BA02",
        "class": "Biguanide Antidiabetic Agent",
        "display_name": "Metformin"
    },
    "warfarin": {
        "rxcui": "11289",
        "atc_code": "B01AA03",
        "class": "Vitamin K Antagonist Anticoagulant",
        "display_name": "Warfarin"
    },
    "aspirin": {
        "rxcui": "1191",
        "atc_code": "B01AC06",
        "class": "NSAID / Antiplatelet",
        "display_name": "Aspirin"
    },
    "lisinopril": {
        "rxcui": "29046",
        "atc_code": "C09AA03",
        "class": "ACE Inhibitor",
        "display_name": "Lisinopril"
    },
    "simvastatin": {
        "rxcui": "36567",
        "atc_code": "C10AA01",
        "class": "HMG-CoA Reductase Inhibitor (Statin)",
        "display_name": "Simvastatin"
    },
    "atorvastatin": {
        "rxcui": "83367",
        "atc_code": "C10AA05",
        "class": "HMG-CoA Reductase Inhibitor (Statin)",
        "display_name": "Atorvastatin"
    },
    "clopidogrel": {
        "rxcui": "32968",
        "atc_code": "B01AC04",
        "class": "P2Y12 Platelet Inhibitor",
        "display_name": "Clopidogrel"
    },
    "omeprazole": {
        "rxcui": "7646",
        "atc_code": "A02BC01",
        "class": "Proton Pump Inhibitor (PPI)",
        "display_name": "Omeprazole"
    },
    "ibuprofen": {
        "rxcui": "5640",
        "atc_code": "M01AE01",
        "class": "Nonsteroidal Anti-inflammatory Drug (NSAID)",
        "display_name": "Ibuprofen"
    },
    "acetaminophen": {
        "rxcui": "161",
        "atc_code": "N02BE01",
        "class": "Anilide Analgesic / Antipyretic",
        "display_name": "Acetaminophen"
    },
    "amlodipine": {
        "rxcui": "17767",
        "atc_code": "C08CA01",
        "class": "Dihydropyridine Calcium Channel Blocker",
        "display_name": "Amlodipine"
    },
    "losartan": {
        "rxcui": "5224",
        "atc_code": "C09CA01",
        "class": "Angiotensin II Receptor Blocker (ARB)",
        "display_name": "Losartan"
    }
}


def compute_levenshtein_distance(s1: str, s2: str) -> int:
    """
    Compute Levenshtein edit distance between two strings with O(min(N, M)) space.
    """
    if len(s1) < len(s2):
        return compute_levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def compute_similarity_ratio(s1: str, s2: str) -> float:
    """Compute normalized similarity ratio in range [0.0, 1.0]."""
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    dist = compute_levenshtein_distance(s1, s2)
    return 1.0 - (dist / max_len)


@dataclass
class NormalizedDrug:
    """Structured representation of a normalized pharmaceutical entity."""
    input_text: str
    canonical_name: str
    display_name: str
    rxcui: Optional[str]
    atc_code: Optional[str]
    drug_class: Optional[str]
    match_type: str  # EXACT, BRAND_MAPPING, SALT_STRIPPED, FUZZY_CORRECTION, UNKNOWN
    confidence_score: float
    salt_removed: Optional[str] = None
    original_brand: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_text": self.input_text,
            "canonical_name": self.canonical_name,
            "display_name": self.display_name,
            "rxcui": self.rxcui,
            "atc_code": self.atc_code,
            "drug_class": self.drug_class,
            "match_type": self.match_type,
            "confidence_score": self.confidence_score,
            "salt_removed": self.salt_removed,
            "original_brand": self.original_brand
        }


class DrugNormalizer:
    """
    Production Drug Normalization Engine.
    Handles text cleaning, salt stripping, brand name resolution,
    spelling variation correction, and RxNorm/ATC linkage.
    """

    def __init__(self, rxnorm_client: Optional[RxNormClient] = None, fuzzy_threshold: float = 0.72):
        self.rxnorm_client = rxnorm_client or RxNormClient()
        self.fuzzy_threshold = fuzzy_threshold

    def clean_text(self, text: str) -> str:
        """Strip punctuation, excessive whitespace, dosage/strength patterns, and lower-case text."""
        # Strip strength patterns: e.g. 500mg, 10 mg, 0.5mcg, 5ml, 1000mg
        cleaned = re.sub(r"\b\d+(\.\d+)?\s*(mg|mcg|ug|g|ml|l|%|iu|meq)\b", "", text, flags=re.IGNORECASE)
        # Strip common dosage forms
        cleaned = re.sub(r"\b(tablet|tablets|capsule|capsules|tab|cap|solution|syrup|oral|injection|cream|ointment)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"[^\w\s-]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
        return cleaned

    def strip_salts(self, text: str) -> Tuple[str, Optional[str]]:
        """
        Detect and strip pharmaceutical salt formulations or hydrates.
        Returns: (base_name, salt_found)
        """
        words = text.split()
        if len(words) <= 1:
            return text, None

        salt_detected = []
        base_words = []

        for word in words:
            clean_word = word.lower().strip("-")
            if clean_word in PHARMACEUTICAL_SALTS:
                salt_detected.append(word)
            else:
                base_words.append(word)

        if salt_detected and base_words:
            return " ".join(base_words), " ".join(salt_detected)

        return text, None

    def normalize(self, query: str) -> NormalizedDrug:
        """
        Main synchronous normalization pipeline for drug strings.
        Steps:
        1. Text cleaning
        2. Exact match check
        3. Brand-to-generic dictionary lookup
        4. Pharmaceutical salt removal
        5. Fuzzy approximate matching / typo correction
        6. RxNorm offline cache linkage
        """
        cleaned = self.clean_text(query)
        if not cleaned:
            return NormalizedDrug(
                input_text=query,
                canonical_name="",
                display_name="",
                rxcui=None,
                atc_code=None,
                drug_class=None,
                match_type="UNKNOWN",
                confidence_score=0.0
            )

        # 1. Exact canonical check
        if cleaned in CANONICAL_DRUGS:
            info = CANONICAL_DRUGS[cleaned]
            return NormalizedDrug(
                input_text=query,
                canonical_name=cleaned,
                display_name=info["display_name"],
                rxcui=info["rxcui"],
                atc_code=info["atc_code"],
                drug_class=info["class"],
                match_type="EXACT",
                confidence_score=1.0
            )

        # 2. Brand-to-Generic resolution
        if cleaned in BRAND_TO_GENERIC:
            canonical = BRAND_TO_GENERIC[cleaned]
            info = CANONICAL_DRUGS.get(canonical, {})
            return NormalizedDrug(
                input_text=query,
                canonical_name=canonical,
                display_name=info.get("display_name", canonical.capitalize()),
                rxcui=info.get("rxcui"),
                atc_code=info.get("atc_code"),
                drug_class=info.get("class"),
                match_type="BRAND_MAPPING",
                confidence_score=0.98,
                original_brand=query.strip()
            )

        # 3. Pharmaceutical salt stripping
        base_name, salt = self.strip_salts(cleaned)
        if salt and base_name in CANONICAL_DRUGS:
            info = CANONICAL_DRUGS[base_name]
            return NormalizedDrug(
                input_text=query,
                canonical_name=base_name,
                display_name=info["display_name"],
                rxcui=info["rxcui"],
                atc_code=info["atc_code"],
                drug_class=info["class"],
                match_type="SALT_STRIPPED",
                confidence_score=0.95,
                salt_removed=salt
            )

        # Check if base after salt stripping is a brand name
        if salt and base_name in BRAND_TO_GENERIC:
            canonical = BRAND_TO_GENERIC[base_name]
            info = CANONICAL_DRUGS.get(canonical, {})
            return NormalizedDrug(
                input_text=query,
                canonical_name=canonical,
                display_name=info.get("display_name", canonical.capitalize()),
                rxcui=info.get("rxcui"),
                atc_code=info.get("atc_code"),
                drug_class=info.get("class"),
                match_type="SALT_STRIPPED",
                confidence_score=0.94,
                salt_removed=salt,
                original_brand=base_name.capitalize()
            )

        # 4. Fuzzy approximate matching / Typo correction against canonical drugs
        target_name = base_name if base_name else cleaned
        best_match = None
        best_ratio = 0.0

        for candidate in CANONICAL_DRUGS.keys():
            ratio = compute_similarity_ratio(target_name, candidate)
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = candidate

        # Also check against brands for typo correction (e.g. "Coumadne" -> "coumadin" -> "warfarin")
        best_brand_match = None
        best_brand_ratio = 0.0
        for brand_candidate, gen_target in BRAND_TO_GENERIC.items():
            ratio = compute_similarity_ratio(target_name, brand_candidate)
            if ratio > best_brand_ratio:
                best_brand_ratio = ratio
                best_brand_match = (brand_candidate, gen_target)

        # Evaluate best candidate between direct generic and brand
        if best_brand_ratio > best_ratio and best_brand_ratio >= self.fuzzy_threshold:
            brand_name, gen_name = best_brand_match
            info = CANONICAL_DRUGS.get(gen_name, {})
            return NormalizedDrug(
                input_text=query,
                canonical_name=gen_name,
                display_name=info.get("display_name", gen_name.capitalize()),
                rxcui=info.get("rxcui"),
                atc_code=info.get("atc_code"),
                drug_class=info.get("class"),
                match_type="FUZZY_CORRECTION",
                confidence_score=round(best_brand_ratio * 0.95, 3),
                original_brand=brand_name.capitalize()
            )
        elif best_match and best_ratio >= self.fuzzy_threshold:
            info = CANONICAL_DRUGS[best_match]
            return NormalizedDrug(
                input_text=query,
                canonical_name=best_match,
                display_name=info["display_name"],
                rxcui=info["rxcui"],
                atc_code=info["atc_code"],
                drug_class=info["class"],
                match_type="FUZZY_CORRECTION",
                confidence_score=round(best_ratio * 0.95, 3),
                salt_removed=salt
            )

        # 5. Fallback: Unknown entity
        return NormalizedDrug(
            input_text=query,
            canonical_name=target_name,
            display_name=target_name.capitalize(),
            rxcui=None,
            atc_code=None,
            drug_class=None,
            match_type="UNKNOWN",
            confidence_score=0.3
        )
