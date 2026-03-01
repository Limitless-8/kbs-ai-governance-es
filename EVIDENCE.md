# Evidence Index — Governance-Legitimate AI Deployment Expert System

This file provides a single verification path for all key coursework claims:
determinism, refusal under uncertainty, forward chaining, backward chaining, testing, coverage, refinement evidence, and audit logging.

---

## 1) Environment + dependencies
- Create venv and install:
  - `python -m venv .venv`
  - `.venv\Scripts\activate`
  - `pip install -r requirements.txt`

Prerequisite:
- SWI-Prolog installed and `swipl` available on PATH.

---

## 2) Run the system (authoritative Prolog inference)
Command:
- `python python\run_inference.py`

Expected:
- JSON printed
- log written to `logs/<run_id>.json`
- contains: `primary_decision`, `constraint_decision`, `fired_rules`, `reasons`, `missing_critical`, `unclear_critical`

---

## 3) Automated tests (pytest)
Command:
- `pytest -q`

Expected:
- all tests pass

File:
- `python/tests/test_cases.py`

---

## 4) Rule coverage + scenario suite artefacts
Command:
- `python python\run_suite.py`  *(or your suite script name)*

Expected outputs:
- `artifacts/suite_<timestamp>.csv`
- `artifacts/rule_coverage_<timestamp>.csv`
- coverage should show 25/25 rules fired at least once

Example artefacts (latest run):
- `artifacts/suite_20260126_233040.csv`
- `artifacts/rule_coverage_20260126_233040.csv`

---

## 5) Refinement evidence (failure-driven refinement)
Claim:
- A case with `dpia_exists=unclear` was previously handled over-permissively as `escalate/confirm`.
- After refinement, it correctly produces `refuse_to_decide/refuse_to_decide`, with `unclear_critical=['dpia_exists']`.

Before log:
- `logs/20260126_215106_refuse_unclear_dpia.json`

After log:
- `logs/20260201_025206_AFTER_unclear_dpia.json`

Reproduce the comparison in one command:
- `python python\refinement_demo.py`

Expected:
- BEFORE: `escalate / confirm`
- AFTER: `refuse_to_decide / refuse_to_decide`, with `unclear_critical` containing `dpia_exists`

---

## 6) Backward chaining demonstration (“why-not approval”)
Command:
- Use Streamlit UI tab: **Why-not (approval)**, or run the goal via Python helper.

Expected:
- `unmet_for_approve` list produced for non-refusal cases.

---

## 7) Audit log EDA (no ML)
Command:
- `python python\eda_logs.py`

Expected:
- outcome distributions
- top fired rules
- refusal drivers
- escalation drivers

## 8) Reproducibility & End-to-End Verification (One Command)

Command:
  python python\run_all.py

Observed output (PowerShell):
  === RUN-ALL SUMMARY ===
  overall_ok: True
  summary_json: artifacts\run_all_summary_20260201_030951.json
  -----------------------
  - pytest: PASS
  - suite_and_rule_coverage: PASS
  - eda_logs: PASS
  - determinism_check: PASS

