# Refinement Dossier (Failure → Rulebase Refinement → Improved Legitimacy)

This file documents a concrete refinement cycle where the expert system produced an undesirable governance outcome, and was then refined to better satisfy the non-negotiable design objective: **refusal under uncertainty** and **bounded authority**.

## Summary

- **Problem:** A proposal with a critical governance field marked `unclear` (structured uncertainty) previously resulted in a non-refusal outcome (`escalate/confirm`), which is over-permissive for a legitimacy-first system.
- **Refinement intent:** Treat **unclear critical evidence** as insufficient authority to issue a decision.
- **Outcome:** Same inputs now produce **refusal** (`refuse_to_decide/refuse_to_decide`), aligned with conservative legitimacy.

---

## Evidence: before vs after (same inputs)

### Inputs (identical in both runs)

Critical structured uncertainty:
- `dpia_exists = unclear`

Full input set (identical):
- uk_public_sector_applicability=yes
- decision_impact=advisory
- consequence_severity=low
- personal_data_usage=yes
- special_category_data=no
- biometric_processing=no
- childrens_data=no
- dpia_exists=unclear
- human_oversight_plan=yes
- appeals_mechanism=yes
- explainability_provision=yes
- bias_fairness_assessment=yes
- security_controls=yes
- monitoring_incident_response=yes
- supplier_transparency=yes

---

## BEFORE (undesirable)

**Log file:** `logs/20260126_215106_refuse_unclear_dpia.json`  
**Primary/constraint:** `escalate / confirm`  
**Missing critical:** `[]`  
**Unclear critical:** *(not recorded in this older run)*  
**Fired rules (ordered):**
- r01, r05, r11, r13, r15, r17, r19, r21, r23, r25

**Interpretation:**
- The system defaulted to escalation (`r25`) rather than refusing, even though a **critical governance artefact (DPIA)** was explicitly **unclear**.
- This is over-permissive for a legitimacy-first system: escalation still constitutes an issued governance outcome.

---

## AFTER (refinement aligned with legitimacy)

**Log file:** `logs/20260201_025206_AFTER_unclear_dpia.json`  
**Primary/constraint:** `refuse_to_decide / refuse_to_decide`  
**Missing critical:** `[]`  
**Unclear critical:** `['dpia_exists']`  
**Constraint reason:** `Constraint: unclear critical evidence => refuse to decide.`  
**Fired rules (ordered):**
- r01, r05, r06, r11, r13, r15, r17, r19, r21, r23

**Interpretation:**
- Refusal is now triggered (`r06`), correctly treating **unclear critical evidence** as insufficient authority.
- The audit trail now cleanly distinguishes:
  - absent keys → `missing_critical`
  - present-but-unclear → `unclear_critical`

---

## Why this refinement improves legitimacy

This refinement better enforces the project’s design objective:

- **Refusal under uncertainty:** a critical artefact marked `unclear` no longer permits escalation as if authority were intact.
- **Bounded authority:** the system withholds decision issuance when governance justification cannot be demonstrated.
- **Auditability:** the change is visible in both outcome and trace (shift from `r25` escalation to `r06` refusal).

---

## Notes (audit semantics)

In the AFTER run, the system records `dpia_exists` under `missing_critical` even though the input value is `unclear`.
If desired, this can be tightened so that:
- absent keys → `missing_critical`
- present-but-unclear → `unclear_critical`

This would improve audit semantics, but does not change the core refinement claim: **structured uncertainty now results in refusal rather than escalation.**
