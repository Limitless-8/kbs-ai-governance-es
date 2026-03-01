# python/generate_logs.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any

from run_inference import (
    write_temp_facts_file,
    call_prolog,
    write_audit_log,
    PROLOG_DIR,
)


def base_case() -> Dict[str, Any]:
    return {
        "uk_public_sector_applicability": "yes",
        "decision_impact": "advisory",
        "consequence_severity": "low",
        "personal_data_usage": "yes",
        "special_category_data": "no",
        "biometric_processing": "no",
        "childrens_data": "no",
        "dpia_exists": "yes",
        "human_oversight_plan": "yes",
        "appeals_mechanism": "yes",
        "explainability_provision": "yes",
        "bias_fairness_assessment": "yes",
        "security_controls": "yes",
        "monitoring_incident_response": "yes",
        "supplier_transparency": "yes",
    }


def run_and_log(tag: str, facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate one run, write an audit log, and return the result dict.
    """
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + f"_{tag}"
    facts_path = write_temp_facts_file(facts, run_id)

    result = call_prolog(
        main_pl=PROLOG_DIR / "main.pl",
        constraints_pl=PROLOG_DIR / "constraints.pl",
        facts_pl=facts_path,
    )

    write_audit_log(run_id, facts, result)
    return result


def _assert_outcome(tag: str, result: Dict[str, Any], primary: str, constraint: str) -> None:
    got_p = result.get("primary_decision")
    got_c = result.get("constraint_decision")
    if got_p != primary or got_c != constraint:
        raise RuntimeError(
            f"[{tag}] unexpected outcome.\n"
            f"Expected: primary={primary}, constraint={constraint}\n"
            f"Got:      primary={got_p}, constraint={got_c}\n"
            f"Fired:    {result.get('fired_rules')}\n"
            f"Missing:  {result.get('missing_critical')}\n"
        )


def main() -> None:
    # 1) approve (low-risk + minimum governance met)
    res = run_and_log("approve", base_case())
    _assert_outcome("approve", res, primary="approve", constraint="confirm")

    # 2) approve_with_safeguards (fully automated, low severity)
    f = base_case()
    f["decision_impact"] = "fully_automated"
    f["consequence_severity"] = "low"
    res = run_and_log("approve_with_safeguards", f)
    _assert_outcome("approve_with_safeguards", res, primary="approve_with_safeguards", constraint="confirm")

    # 3) escalate (high severity, but not fully automated => default escalation)
    f = base_case()
    f["decision_impact"] = "human_supported"
    f["consequence_severity"] = "high"
    res = run_and_log("escalate", f)
    _assert_outcome("escalate", res, primary="escalate", constraint="confirm")

    # 4) reject + veto (fully automated + high severity)
    f = base_case()
    f["decision_impact"] = "fully_automated"
    f["consequence_severity"] = "high"
    res = run_and_log("reject_veto", f)
    _assert_outcome("reject_veto", res, primary="reject", constraint="veto")

    # 5) refuse_to_decide (missing critical evidence: dpia_exists omitted)
    f = base_case()
    f.pop("dpia_exists")
    res = run_and_log("refuse_missing_dpia", f)
    _assert_outcome("refuse_missing_dpia", res, primary="refuse_to_decide", constraint="refuse_to_decide")

    # 6) refuse_to_decide (jurisdiction not applicable / outside authority)
    f = base_case()
    f["uk_public_sector_applicability"] = "no"
    res = run_and_log("refuse_jurisdiction_no", f)
    _assert_outcome("refuse_jurisdiction_no", res, primary="refuse_to_decide", constraint="refuse_to_decide")

    # 7) refuse_to_decide (structured uncertainty: critical field present but UNCLEAR)
    # This proves "unclear" behaves as refusal-under-uncertainty for critical evidence.
    f = base_case()
    f["dpia_exists"] = "unclear"
    res = run_and_log("refuse_unclear_dpia", f)
    _assert_outcome("refuse_unclear_dpia", res, primary="refuse_to_decide", constraint="refuse_to_decide")

    # 8) refuse_to_decide (structured uncertainty: jurisdiction UNCLEAR)
    f = base_case()
    f["uk_public_sector_applicability"] = "unclear"
    res = run_and_log("refuse_jurisdiction_unclear", f)
    _assert_outcome("refuse_jurisdiction_unclear", res, primary="refuse_to_decide", constraint="refuse_to_decide")

    print("Generated logs for 8 scenarios (validated outcomes).")


if __name__ == "__main__":
    main()
