"""
PharmaMind AI - FDA DailyMed Structured Product Labeling (SPL) Client
Extracts regulatory indications, contraindications, boxed warnings, and MOA.
"""

from typing import Dict, Any, List, Optional
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger("pharmamind.integrations.dailymed")

# Curated FDA DailyMed Monograph Cache for Sandbox & Deterministic Testing
DAILYMED_OFFLINE_CACHE: Dict[str, Dict[str, Any]] = {
    "metformin": {
        "setid": "7b79a781-6453-4dc9-8472-metformin001",
        "title": "METFORMIN HYDROCHLORIDE tablet, film coated",
        "generic_name": "Metformin Hydrochloride",
        "brand_name": "Glucophage",
        "sections": {
            "boxed_warning": "WARNING: LACTIC ACIDOSIS. Postmarketing cases of metformin-associated lactic acidosis have resulted in death, hypothermia, hypotension, and resistant bradyarrhythmias. The onset is often subtle, accompanied only by nonspecific symptoms such as malaise, myalgias, respiratory distress, somnolence, and abdominal pain.",
            "indications_and_usage": "Metformin Hydrochloride Tablets, USP are indicated as an adjunct to diet and exercise to improve glycemic control in adults and pediatric patients 10 years of age and older with type 2 diabetes mellitus.",
            "contraindications": "Severe renal impairment (eGFR below 30 mL/min/1.73 m2). Known hypersensitivity to metformin hydrochloride. Acute or chronic metabolic acidosis, including diabetic ketoacidosis.",
            "mechanism_of_action": "Metformin is an antihyperglycemic agent which improves glucose tolerance in patients with type 2 diabetes, lowering both basal and postprandial plasma glucose. Its pharmacologic mechanisms of action differ from other classes of oral antihyperglycemic agents. Metformin decreases hepatic glucose production, decreases intestinal absorption of glucose, and improves insulin sensitivity by increasing peripheral glucose uptake and utilization.",
            "drug_interactions": "Carbonic anhydrase inhibitors may increase the risk of lactic acidosis. Drugs that reduce metformin clearance (such as ranolazine, vandetanib, dolutegravir, and cimetidine) may increase the accumulation of metformin. Alcohol potentiates the effect of metformin on lactate metabolism."
        },
        "license": "Public Domain (US FDA)",
        "effective_time": "2025-06-01"
    },
    "warfarin": {
        "setid": "coumadin-7b79a781-6453-4dc9-8472-warfarin001",
        "title": "COUMADIN (warfarin sodium) tablet",
        "generic_name": "Warfarin Sodium",
        "brand_name": "Coumadin",
        "sections": {
            "boxed_warning": "WARNING: BLEEDING RISK. Warfarin sodium can cause major or fatal bleeding. Perform regular monitoring of INR in all treated patients. Drugs, dietary changes, and other factors affect INR levels achieved with warfarin therapy.",
            "indications_and_usage": "Prophylaxis and treatment of venous thrombosis and its extension, pulmonary embolism; prophylaxis and treatment of thromboembolic complications associated with atrial fibrillation and/or cardiac valve replacement; reduction in the risk of death, recurrent myocardial infarction, and thromboembolic events such as stroke or systemic embolization after myocardial infarction.",
            "contraindications": "Pregnancy (except in women with mechanical heart valves). Hemorrhagic tendencies or blood dyscrasias. Recent or contemplated surgery of the central nervous system or eye, or traumatic surgery resulting in large open surfaces. Bleeding tendencies associated with active ulceration or overt bleeding of gastrointestinal, genitourinary, or respiratory tracts.",
            "mechanism_of_action": "Warfarin competitively inhibits the vitamin K epoxide reductase complex 1 (VKORC1), an essential enzyme for activating the vitamin K epoxide cycle. This depletes functional vitamin K reserves and limits gamma-carboxylation of coagulation factors II, VII, IX, and X, as well as anticoagulant proteins C and S.",
            "drug_interactions": "Aspirin, other NSAIDs, and antiplatelet agents significantly heighten major hemorrhage risk. Concomitant CYP2C9 inhibitors (e.g., amiodarone, fluconazole) or CYP3A4 inhibitors (e.g., simvastatin) increase warfarin anticoagulant effects and elevate INR."
        },
        "license": "Public Domain (US FDA)",
        "effective_time": "2025-04-15"
    },
    "aspirin": {
        "setid": "aspirin-7b79a781-6453-4dc9-8472-aspirin001",
        "title": "ASPIRIN tablet",
        "generic_name": "Aspirin",
        "brand_name": "Bayer Aspirin",
        "sections": {
            "boxed_warning": None,
            "indications_and_usage": "Vascular indications: reduction of combined risk of death and nonfatal stroke in patients who have had ischemic stroke or transient ischemic attacks. Temporary relief of headache, muscular pain, toothache, and inflammation.",
            "contraindications": "Known allergy to NSAIDs, patients with asthma, rhinitis, and nasal polyps. Active peptic ulcer disease.",
            "mechanism_of_action": "Aspirin acetylates and irreversibly inactivates cyclooxygenase-1 (PTGS1/COX-1) and cyclooxygenase-2 (PTGS2/COX-2), thereby suppressing the formation of prostaglandin H2 and downstream thromboxane A2 in platelets.",
            "drug_interactions": "Anticoagulants such as warfarin: concomitant therapy significantly increases the risk of bleeding. ACE inhibitors: high-dose aspirin may attenuate hypotensive and renal vasodilatory effects."
        },
        "license": "Public Domain (US FDA)",
        "effective_time": "2025-02-10"
    }
}


class DailyMedClient:
    """
    Client for retrieving Structured Product Labeling (SPL) monographs from FDA DailyMed.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 6.0):
        self.base_url = (base_url or settings.DAILYMED_BASE_URL).rstrip("/")
        self.timeout = timeout

    async def get_spl_by_drug_name(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve SPL monograph by generic drug name."""
        clean_name = drug_name.strip().lower()

        # Check offline cache
        for key, val in DAILYMED_OFFLINE_CACHE.items():
            if clean_name in key or key in clean_name:
                return val

        url = f"{self.base_url}/spls.json"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url, params={"drug_name": drug_name, "pagesize": 1})
                if res.status_code == 200:
                    data = res.json()
                    spl_data = data.get("data", [])
                    if spl_data:
                        setid = spl_data[0].get("setid")
                        title = spl_data[0].get("title")
                        return {
                            "setid": setid,
                            "title": title,
                            "generic_name": drug_name,
                            "sections": {},
                            "license": "Public Domain (US FDA)",
                            "source": "DailyMed Live API"
                        }
        except Exception as e:
            logger.debug(f"DailyMed online lookup failed for '{drug_name}': {e}. Using offline cache.")

        return None

    async def get_sections_by_setid(self, setid: str) -> Dict[str, Any]:
        """Fetch clinical sections for a specific DailyMed SPL SetID."""
        for _, val in DAILYMED_OFFLINE_CACHE.items():
            if val["setid"] == setid:
                return val["sections"]

        return {}

