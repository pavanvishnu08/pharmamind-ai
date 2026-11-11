# PharmaMind AI - Clinical Safety Protocols & Non-Prescribing Policy

PharmaMind AI is strictly designed for **educational, pharmacological, and biomedical research purposes**. It is not a clinical decision support system (CDSS) for patient-specific prescribing, diagnostic decisions, or acute medical treatment.

---

## 1. Non-Prescribing Policy & Guardrails

### A. Strict Clinical Prohibitions
Under no circumstances will PharmaMind AI:
- Generate personalized dosage instructions (e.g. "take 500mg twice daily").
- Advise a patient to start, stop, discontinue, or substitute an active prescription medication.
- Provide personalized diagnoses based on patient symptoms.
- Generate pediatric or obstetric drug dosing schedules.

### B. Automated Refusal Engine
All incoming queries are passed through `_check_safety_guardrails(query)` in `app/api/v1/endpoints/assistant.py`.
If prohibited intent keywords or regex patterns are detected (e.g. `dosage for me`, `prescribe`, `diagnose me`, `stop taking my medication`), the system immediately raises `MedicalAdviceProhibitedException` (HTTP 400) returning a standardized refusal:

```json
{
  "detail": "PharmaMind AI cannot provide personalized clinical decisions, diagnoses, or dosage recommendations regarding '...'. Please consult a licensed medical doctor or clinical pharmacist."
}
```

This behavior is deterministically verified in automated tests (`test_safety_guardrail_refusal_for_prescribing`).

---

## 2. Citation Validation Protocol

To combat language model hallucinations:
1. Every factual assertion must link to a valid source citation in `citations`.
2. Citations must include:
   - `source_title`
   - `source_type` (DailyMed, RxNorm, PubMed)
   - `identifier` (RxCUI, PMID, SetID)
   - `url` (valid external HTTP link)
   - `retrieved_date`
3. If an assertion cannot be grounded in retrieved context, the system explicitly reports **INSUFFICIENT_EVIDENCE** rather than hallucinating details.

