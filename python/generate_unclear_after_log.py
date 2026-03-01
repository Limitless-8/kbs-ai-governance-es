from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any

from run_inference import (
    write_temp_facts_file,
    call_prolog,
    write_audit_log,
    PROLOG_DIR,
)

def facts_unclear_dpia() -> Dict[str, Any]:
    return {
        "uk_public_sector_applicability": "yes",
        "decision_impact": "advisory",
        "consequence_severity": "low",
        "personal_data_usage": "yes",
        "special_category_data": "no",
        "biometric_processing": "no",
        "childrens_data": "no",
        "dpia_exists": "unclear",  # <-- critical structured uncertainty
        "human_oversight_plan": "yes",
        "appeals_mechanism": "yes",
        "explainability_provision": "yes",
        "bias_fairness_assessment": "yes",
        "security_controls": "yes",
        "monitoring_incident_response": "yes",
        "supplier_transparency": "yes",
    }

def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_AFTER_unclear_dpia"
    facts = facts_unclear_dpia()
    facts_path = write_temp_facts_file(facts, run_id)

    result = call_prolog(
        main_pl=PROLOG_DIR / "main.pl",
        constraints_pl=PROLOG_DIR / "constraints.pl",
        facts_pl=facts_path,
    )

    log_path = write_audit_log(run_id, facts, result)

    print("WROTE:", log_path)
    print("primary/constraint:", result.get("primary_decision"), "/", result.get("constraint_decision"))
    print("missing_critical:", result.get("missing_critical"))
    print("unclear_critical:", result.get("unclear_critical"))
    print("constraint_reasons:", result.get("constraint_reasons"))
    print("fired_rules:", result.get("fired_rules"))

if __name__ == "__main__":
    main()
