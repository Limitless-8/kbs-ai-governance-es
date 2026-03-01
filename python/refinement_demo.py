from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from run_inference import write_temp_facts_file, call_prolog, PROLOG_DIR

BEFORE_LOG = Path("logs/20260126_215106_refuse_unclear_dpia.json")

def current_unclear_case() -> Dict[str, Any]:
    return {
        "uk_public_sector_applicability": "yes",
        "decision_impact": "advisory",
        "consequence_severity": "low",
        "personal_data_usage": "yes",
        "special_category_data": "no",
        "biometric_processing": "no",
        "childrens_data": "no",
        "dpia_exists": "unclear",
        "human_oversight_plan": "yes",
        "appeals_mechanism": "yes",
        "explainability_provision": "yes",
        "bias_fairness_assessment": "yes",
        "security_controls": "yes",
        "monitoring_incident_response": "yes",
        "supplier_transparency": "yes",
    }

def main() -> None:
    # 1) Load historical "before"
    before = json.loads(BEFORE_LOG.read_text(encoding="utf-8"))
    b_inp = before.get("inputs", {})
    b_res = before.get("result", {})

    # 2) Run current code on same inputs ("after")
    facts = current_unclear_case()
    fp = write_temp_facts_file(facts, "refinement_demo_unclear_dpia")
    after = call_prolog(
        main_pl=PROLOG_DIR / "main.pl",
        constraints_pl=PROLOG_DIR / "constraints.pl",
        facts_pl=fp,
    )

    print("=== REFINEMENT DEMO: identical inputs (unclear DPIA) ===\n")
    print("[BEFORE] log:", BEFORE_LOG.name)
    print(" primary/constraint:", b_res.get("primary_decision"), "/", b_res.get("constraint_decision"))
    print(" fired_rules:", b_res.get("fired_rules"))
    print()

    print("[AFTER] current system run")
    print(" primary/constraint:", after.get("primary_decision"), "/", after.get("constraint_decision"))
    print(" missing_critical:", after.get("missing_critical"))
    print(" unclear_critical:", after.get("unclear_critical"))
    print(" constraint_reasons:", after.get("constraint_reasons"))
    print(" fired_rules:", after.get("fired_rules"))
    print()

    print("PASS if AFTER is refuse_to_decide/refuse_to_decide and dpia_exists is in unclear_critical.")

if __name__ == "__main__":
    main()
