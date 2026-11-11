"""
PharmaMind AI - NLM RxNorm REST API Client
Handles standardized drug terminology, RxCUI resolution, synonyms, and ATC mappings.
"""

from typing import Dict, Any, List, Optional
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger("pharmamind.integrations.rxnorm")

# Authoritative Offline Cache for Standard Formularies
RXNORM_OFFLINE_CACHE: Dict[str, Dict[str, Any]] = {
    "metformin": {
        "rxcui": "6809",
        "name": "Metformin",
        "synonym": "Glucophage",
        "tty": "IN",  # Ingredient
        "atc_code": "A10BA02",
        "drug_class": "Biguanide Antidiabetic Agent",
        "brand_names": ["Glucophage", "Fortamet", "Glumetza", "Riomet"],
        "ingredients": ["Metformin"]
    },
    "warfarin": {
        "rxcui": "11289",
        "name": "Warfarin",
        "synonym": "Coumadin",
        "tty": "IN",
        "atc_code": "B01AA03",
        "drug_class": "Vitamin K Antagonist Anticoagulant",
        "brand_names": ["Coumadin", "Jantoven"],
        "ingredients": ["Warfarin"]
    },
    "aspirin": {
        "rxcui": "1191",
        "name": "Aspirin",
        "synonym": "Acetylsalicylic Acid",
        "tty": "IN",
        "atc_code": "B01AC06",
        "drug_class": "NSAID / Antiplatelet",
        "brand_names": ["Bayer Aspirin", "Ecotrin", "Bufferin"],
        "ingredients": ["Aspirin"]
    },
    "lisinopril": {
        "rxcui": "29046",
        "name": "Lisinopril",
        "synonym": "Prinivil",
        "tty": "IN",
        "atc_code": "C09AA03",
        "drug_class": "ACE Inhibitor",
        "brand_names": ["Prinivil", "Zestril", "Qbrelis"],
        "ingredients": ["Lisinopril"]
    },
    "simvastatin": {
        "rxcui": "36567",
        "name": "Simvastatin",
        "synonym": "Zocor",
        "tty": "IN",
        "atc_code": "C10AA01",
        "drug_class": "HMG-CoA Reductase Inhibitor (Statin)",
        "brand_names": ["Zocor", "Flolipid"],
        "ingredients": ["Simvastatin"]
    },
    "atorvastatin": {
        "rxcui": "83367",
        "name": "Atorvastatin",
        "synonym": "Lipitor",
        "tty": "IN",
        "atc_code": "C10AA05",
        "drug_class": "HMG-CoA Reductase Inhibitor (Statin)",
        "brand_names": ["Lipitor"],
        "ingredients": ["Atorvastatin"]
    },
    "clopidogrel": {
        "rxcui": "32968",
        "name": "Clopidogrel",
        "synonym": "Plavix",
        "tty": "IN",
        "atc_code": "B01AC04",
        "drug_class": "P2Y12 Platelet Inhibitor",
        "brand_names": ["Plavix"],
        "ingredients": ["Clopidogrel"]
    },
    "omeprazole": {
        "rxcui": "7646",
        "name": "Omeprazole",
        "synonym": "Prilosec",
        "tty": "IN",
        "atc_code": "A02BC01",
        "drug_class": "Proton Pump Inhibitor (PPI)",
        "brand_names": ["Prilosec", "Losec"],
        "ingredients": ["Omeprazole"]
    }
}


def _levenshtein_ratio(s1: str, s2: str) -> float:
    """Compute normalized string similarity ratio."""
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    if not s2:
        return 0.0
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return 1.0 - (prev[-1] / max(len(s1), len(s2)))


class RxNormClient:
    """
    Client for querying the National Library of Medicine RxNorm REST API.
    Provides automated fallback to curated offline data for offline sandbox resilience.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 5.0):
        self.base_url = (base_url or settings.RXNORM_BASE_URL).rstrip("/")
        self.timeout = timeout

    async def get_rxcui_by_name(self, drug_name: str) -> Optional[str]:
        """Resolve generic or brand name to canonical RxNorm Concept Unique Identifier (RxCUI)."""
        clean_name = drug_name.strip().lower()

        # Check offline cache first
        for key, val in RXNORM_OFFLINE_CACHE.items():
            if clean_name == key or clean_name == val["name"].lower() or any(clean_name == b.lower() for b in val["brand_names"]):
                return val["rxcui"]

        # Online query to NLM RxNav
        url = f"{self.base_url}/rxcui.json"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url, params={"name": drug_name})
                if res.status_code == 200:
                    data = res.json()
                    id_group = data.get("idGroup", {})
                    rxnorm_ids = id_group.get("rxnormId", [])
                    if rxnorm_ids:
                        return rxnorm_ids[0]
        except Exception as e:
            logger.debug(f"RxNorm online lookup failed for '{drug_name}': {e}. Using cache.")

        return None

    async def approximate_match(self, term: str) -> List[Dict[str, Any]]:
        """
        Approximate string matching endpoint for resolving typos and brand names.
        """
        clean_term = term.strip().lower()
        candidates = []

        # Local fuzzy check
        for key, val in RXNORM_OFFLINE_CACHE.items():
            ratio = _levenshtein_ratio(clean_term, key)
            brand_ratios = [_levenshtein_ratio(clean_term, b.lower()) for b in val.get("brand_names", [])]
            max_brand = max(brand_ratios) if brand_ratios else 0.0
            best_score = max(ratio, max_brand)
            if clean_term in key or key in clean_term or best_score >= 0.70:
                candidates.append({
                    "rxcui": val["rxcui"],
                    "name": val["name"],
                    "score": round(best_score, 2),
                    "rank": 1
                })

        if candidates:
            # Sort by score descending
            candidates.sort(key=lambda c: c["score"], reverse=True)
            return candidates

        url = f"{self.base_url}/approximateTerm.json"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url, params={"term": term, "maxEntries": 5})
                if res.status_code == 200:
                    data = res.json()
                    candidate_list = data.get("approximateGroup", {}).get("candidate", [])
                    return [
                        {
                            "rxcui": c.get("rxcui"),
                            "score": float(c.get("score", 0)) / 100.0,
                            "rank": int(c.get("rank", 0))
                        }
                        for c in candidate_list
                    ]
        except Exception as e:
            logger.debug(f"RxNorm approximate match query failed: {e}")

        return candidates

    async def get_all_properties(self, rxcui: str) -> Dict[str, Any]:
        """Fetch all properties for a given RxCUI."""
        # Check offline cache
        for _, val in RXNORM_OFFLINE_CACHE.items():
            if val["rxcui"] == rxcui:
                return {
                    "rxcui": rxcui,
                    "name": val["name"],
                    "tty": val["tty"],
                    "atc_code": val["atc_code"],
                    "drug_class": val["drug_class"],
                    "brand_names": val["brand_names"],
                    "source": "RxNorm Cache"
                }

        url = f"{self.base_url}/rxcui/{rxcui}/allProperties.json"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url, params={"prop": "all"})
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.debug(f"RxNorm allProperties lookup failed for '{rxcui}': {e}")

        return {"rxcui": rxcui, "name": f"RxCUI:{rxcui}", "source": "Unresolved"}

    async def get_brand_names(self, rxcui: str) -> List[str]:
        """Retrieve brand names associated with an ingredient RxCUI."""
        for _, val in RXNORM_OFFLINE_CACHE.items():
            if val["rxcui"] == rxcui:
                return val.get("brand_names", [])

        url = f"{self.base_url}/rxcui/{rxcui}/allrelated.json"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    concepts = data.get("allRelatedGroup", {}).get("conceptGroup", [])
                    brands = []
                    for group in concepts:
                        if group.get("tty") == "BN":  # Brand Name
                            for c in group.get("conceptProperties", []):
                                brands.append(c.get("name"))
                    return brands
        except Exception as e:
            logger.debug(f"RxNorm brand names lookup failed for '{rxcui}': {e}")

        return []
