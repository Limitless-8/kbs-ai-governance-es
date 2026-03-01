# Governance‑Legitimate AI Deployment Expert System  
**UK Public Sector**

---

A deterministic, audit‑first **rule‑based expert system** that evaluates whether a **specific proposed deployment** of an AI system can be **legitimately authorised** in a UK public‑sector decision‑making context.

This system is **normative rather than predictive**: it does **not** optimise outcomes or assess social benefit.  
Instead, it decides only when **sufficient governance justification** exists.

> **Refusal to decide is a successful outcome** where legitimacy cannot be demonstrated.

---

## 0. Quick Verification (Marker Path)

### Install dependencies

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Run the end‑to‑end verification

```powershell
python python\run_all.py
```

If it prints:

```
overall_ok: True
```

and all checks are **PASS**, the system is reproduced end‑to‑end.

For the full evidence map and expected outputs, see **EVIDENCE.md**.

---

## Table of Contents

0. [Quick Verification (Marker Path)](#0-quick-verification-marker-path)
1. [Design Objective (Non‑Negotiable)](#1-design-objective-non-negotiable)  
2. [What This System Produces](#2-what-this-system-produces)  
3. [Architecture (Hybrid, Disciplined)](#3-architecture-hybrid-disciplined)  
4. [Inputs (Structured Frames + Validation)](#4-inputs-structured-frames--validation)  
5. [Knowledge Representation (25 Production Rules)](#5-knowledge-representation-25-production-rules)  
6. [Inference (Forward + Backward Chaining)](#6-inference-forward--backward-chaining)  
7. [Constraint Layer (Subordinate Governance Authority)](#7-constraint-layer-subordinate-governance-authority)  
8. [Explanation Facility (Audit‑First)](#8-explanation-facility-audit-first)  
9. [Testing, Coverage, and Refinement Evidence](#9-testing-coverage-and-refinement-evidence)  
10. [Governance Oversight Console (Streamlit)](#10-governance-oversight-console-streamlit)  
11. [Audit Logs + EDA (No ML)](#11-audit-logs--eda-no-ml)  
12. [Reproducibility: How to Run Everything](#12-reproducibility-how-to-run-everything)  
13. [Folder Structure](#13-folder-structure)  
14. [Known Limits + Future Improvement](#14-known-limits--future-improvement)  
15. [Licence / Notes](#15-licence--notes)  
16. [One-Command Verification (Recommended)](#16-one-command-verification-recommended)

---

## 1. Design Objective (Non‑Negotiable)

This project develops a small, deterministic expert system that evaluates whether a **specific proposed deployment** of an AI system may be legitimately authorised within **UK public‑sector decision‑making contexts**.

### Governing principles

Correctness is **subordinate to legitimacy**. The system prioritises:

- **Traceability** — every conclusion is reconstructable from facts and fired rules  
- **Auditability** — reasoning is inspectable post‑hoc  
- **Refusal under uncertainty** — absence of justification results in non‑decision  
- **Bounded authority** — the system may withhold, but never compel deployment  

> Refusal to decide is treated as a *successful outcome* where legitimacy cannot be demonstrated.

This is a deliberately conservative system designed to be **correctly cautious**, not ambitiously incomplete.

---

## 2. What This System Produces

### 2.1 Primary decision outputs (finite and mutually exclusive)

The inference engine produces **exactly one** of:

- `approve`  
- `approve_with_safeguards`  
- `escalate`  
- `reject`  
- `refuse_to_decide` *(insufficient or invalid evidence)*  

### 2.2 Constraint‑layer outputs (subordinate authority)

A separate governance constraint layer returns one of:

- `confirm`  
- `veto`  
- `refuse_to_decide` *(with reason)*  

**Important:**  
The constraint layer **cannot generate primary decisions**.  
It can only authorise, invalidate, or withhold authority over decisions produced by the primary engine.

### 2.3 Formal legitimacy condition

A decision is considered legitimate **iff**:

```
Legitimate(Decision) ⇔
EvidenceSufficient ∧
JurisdictionValid ∧
AuthorityBounded
```

---

## 3. Architecture (Hybrid, Disciplined)

The system uses a **hybrid architecture** with strict epistemic separation.

### 3.1 Prolog — Authoritative inference engine

Prolog is used **exclusively** for:

- Knowledge representation  
- Deterministic inference  
- Decision generation  
- Refusal logic  
- Governance constraint evaluation  

> All authoritative reasoning originates in **Prolog**.

### 3.2 Python — Orchestration layer (non‑inferential)

Python is used **solely** for:

- Structured input collection (UI)  
- Frame‑based validation  
- Translating inputs into Prolog facts  
- Explanation formatting extras *(non‑inferential)*  
- Audit logging  
- Automated test execution  
- EDA of system behaviour  

Python has **no epistemic authority**:

- Encodes no domain rules  
- Cannot influence inference  
- Cannot alter decisions  

---

## 4. Inputs (Structured Frames + Validation)

Inputs are **categorical** and validated **before inference**.

### 4.1 Core governance schema

**Deployment context**

- `uk_public_sector_applicability`: yes | no | unclear  
- `decision_impact`: advisory | human_supported | fully_automated  
- `consequence_severity`: low | medium | high  

**Data / system profile**

- `personal_data_usage`: yes | no | unclear  
- `special_category_data`: yes | no | unclear  
- `biometric_processing`: yes | no | unclear  
- `childrens_data`: yes | no | unclear  

**Evidence & assurance**

- `dpia_exists`  
- `human_oversight_plan`  
- `appeals_mechanism`  
- `explainability_provision`  
- `bias_fairness_assessment`  
- `security_controls`  
- `monitoring_incident_response`  
- `supplier_transparency`  

### 4.2 Structured uncertainty (“known unknowns”)

- Missing critical fields → `missing_critical`  
- Fields explicitly set to `unclear` → `unclear_critical`  

> Silence is **not neutral**: absence is treated as structured uncertainty.

---

## 5. Knowledge Representation (25 Production Rules)

The rule base is intentionally constrained:

- **Exactly 25** deterministic production rules (`r01–r25`)  
- All rules are named and audit‑mapped via `rule_text.pl`  
- Rule count is a **governance boundary**, not a technical limitation  
- Deliberate underfitting to avoid false authority and automation bias  

**Rule implementation**:

- `prolog/main.pl` — forward chaining + primary decision rules  
- `prolog/rule_text.pl` — stable human‑readable rule reasons  

---

## 6. Inference (Forward + Backward Chaining)

### 6.1 Forward chaining (primary)

- Rules fire in a fixed order until a fixpoint  
- Produces a **single primary decision**  
- Outputs an ordered fired‑rule trace  
- Refusal is a **terminal state**, not an error  

### 6.2 Backward chaining (demonstrated)

A dedicated Prolog goal answers:

> *“What conditions would justify approval in this case?”*

Called from Python:

```
main:run_unmet_for_approve_json
```

Produces `unmet_for_approve` for oversight use (only when not in refusal).

---

## 7. Constraint Layer (Subordinate Governance Authority)

Implemented in:

```
prolog/constraints.pl
```

Enforces authority containment:

- Refuses if critical evidence is missing or unclear  
- Refuses if jurisdiction is unclear  
- Vetoes over‑confident approvals  
- Vetoes high‑severity fully automated deployments  

> The constraint layer **cannot propose decisions** — only confirm, veto, or refuse.

---

## 8. Explanation Facility (Audit‑First)

Every run produces audit‑ready artefacts:

- `fired_rules` (ordered)  
- Natural‑language rule reasons  
- `missing_critical` / `unclear_critical`  
- Constraint decision + reasons  

**Optional explanation extras**:

- `unmet_for_approve`  
- `explanation_completeness_score` *(artefact completeness, not confidence)*  

All outputs are emitted as a **single Prolog‑generated JSON object**, parsed and logged by Python.

---

## 9. Testing, Coverage, and Refinement Evidence

### 9.1 Automated tests

Location:

```
python/tests/test_cases.py
```

Verified behaviours:

- Low‑risk approval  
- Approval with safeguards  
- Escalation  
- Rejection + constraint veto  
- Refusal under missing critical evidence  
- Refusal under unclear critical evidence  
- Jurisdiction out‑of‑scope refusal  

Run:

```
pytest -q
```

### 9.2 Scenario suite + rule coverage

Generated artefacts:

- `artifacts/suite_<timestamp>.csv`  
- `artifacts/rule_coverage_<timestamp>.csv`  

Used as **non‑ML evaluation evidence**:

- Outcome distribution  
- Rule activation frequency  
- Full rule coverage (25/25)  

### 9.3 Failure-driven refinement (documented)

Identified issue:

- **Before:** `dpia_exists=unclear` → `escalate / confirm`  
- **After:** same inputs → `refuse_to_decide / refuse_to_decide`  

**Evidence (audit logs):**

Before: `logs/20260126_215106_refuse_unclear_dpia.json`  
After:  `logs/20260201_025206_AFTER_unclear_dpia.json`

Reproduce the comparison:

```powershell
python python\refinement_demo.py

Demonstrates:
...

- Refusal under uncertainty  
- Conservative governance legitimacy  
- No post‑hoc rationalisation  

Optional analysis tool:

```powershell
python/find_refinement_pairs.py

```

---

## 10. Governance Oversight Console (Streamlit)

Run:

```
streamlit run python/app_streamlit.py

```

Capabilities:

- Structured categorical input  
- Primary + constraint decision display  
- Explanation trace  
- “Why‑not approval” counterfactuals  
- JSON import/export  
- Audit completeness scoring  

> The UI encodes **no rules** and has **no influence** over inference.

---

## 11. Audit Logs + EDA (No ML)

Audit logs are written to:

```
logs/*.json
```

Each log contains:

- `run_id`, timestamp  
- Inputs  
- Full Prolog output  
- Validation metadata  

### 11.1 Behavioural EDA

```
python python\eda_logs.py
```

Outputs:

- Outcome distributions  
- Top fired rules  
- Refusal drivers  
- Escalation drivers  

> No accuracy metrics. No optimisation. No learning.

---

## 12. Reproducibility: How to Run Everything

### Prerequisites

- Python 3.10+  
- SWI‑Prolog (`swipl` on PATH)

### Key commands

```powershell
python python\run_inference.py
streamlit run python\app_streamlit.py
pytest -q
python python\run_suite.py
python python\generate_logs.py
python python\eda_logs.py

```

## 13. Folder Structure

```text
.
├─ prolog/
│  ├─ main.pl
│  ├─ constraints.pl
│  ├─ rule_text.pl
│  └─ json_writer.pl
├─ python/
│  ├─ run_inference.py
│  ├─ run_all.py
│  ├─ run_suite.py
│  ├─ app_streamlit.py
│  ├─ explain.py
│  ├─ schema.py
│  ├─ validation.py
│  ├─ generate_logs.py
│  ├─ eda_logs.py
│  ├─ refinement_demo.py
│  ├─ find_refinement_pairs.py
│  └─ tests/
│     └─ test_cases.py
├─ logs/
├─ tmp/
├─ artifacts/
├─ EVIDENCE.md
└─ README.md

```

---

## 14. Known Limits + Future Improvement

### Known limits

- Rule systems are brittle  
- Governance policy evolves  
- Thresholds embed normative assumptions  
- Ambiguous cases escalate or refuse  
- Not a full legal compliance engine  

### One future improvement (non‑ML)

- Machine‑readable safeguard lists for `approve_with_safeguards`  
- Preserve bounded authority  
- Improve auditability  
- **No learning. No optimisation.**

---

## 15. Licence / Notes

This project is an **academic demonstration** of governance‑legitimate symbolic AI engineering.

**Final statement:**

> This expert system is not designed to decide more,  
> but to decide **only when justified**.

---

## 16. One‑Command Verification (Recommended)

```powershell
python python\run_all.py
```

---
