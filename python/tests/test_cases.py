# python/tests/test_cases.py
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROLOG_DIR = PROJECT_ROOT / "prolog"

# Import the same helpers used by the orchestrator
import sys
sys.path.append(str(PROJECT_ROOT / "python"))

from run_inference import write_temp_facts_file, call_prolog  # noqa: E402


def run_case(case_name: str, facts: Dict[str, Any]) -> Dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + f"_{case_name}"
    facts_path = write_temp_facts_file(facts, run_id)
    return call_prolog(
        main_pl=PROLOG_DIR / "main.pl",
        constraints_pl=PROLOG_DIR / "constraints.pl",
        facts_pl=facts_path,
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


def test_low_risk_approval():
    facts = base_case()
    result = run_case("low_risk_approval", facts)
    assert result["primary_decision"] == "approve"
    assert result["constraint_decision"] == "confirm"
    assert result.get("mandatory_safeguards", []) == []


def test_refusal_due_to_insufficient_evidence_missing_field():
    facts = base_case()
    # Remove a critical field entirely (refusal under uncertainty)
    facts.pop("dpia_exists")
    result = run_case("refusal_missing_dpia", facts)
    assert result["primary_decision"] == "refuse_to_decide"
    assert result["constraint_decision"] == "refuse_to_decide"
    assert "dpia_exists" in result["missing_critical"]


def test_refusal_due_to_insufficient_evidence_unclear_field():
    facts = base_case()
    # Critical field present but explicitly unclear => refusal under uncertainty,
    # BUT tracked separately from "missing_critical" for audit semantics.
    facts["dpia_exists"] = "unclear"
    result = run_case("refusal_unclear_dpia", facts)
    assert result["primary_decision"] == "refuse_to_decide"
    assert result["constraint_decision"] == "refuse_to_decide"
    assert "dpia_exists" in result.get("unclear_critical", [])
    # and explicitly NOT "missing" (it is present, just unclear)
    assert "dpia_exists" not in result.get("missing_critical", [])


def test_rejection_high_severity_fully_automated():
    facts = base_case()
    facts["decision_impact"] = "fully_automated"
    facts["consequence_severity"] = "high"
    result = run_case("reject_fa_high", facts)
    assert result["primary_decision"] == "reject"
    assert result["constraint_decision"] == "veto"


def test_escalation_high_severity_human_supported():
    facts = base_case()
    facts["decision_impact"] = "human_supported"
    facts["consequence_severity"] = "high"
    result = run_case("escalate_high_hs", facts)
    assert result["primary_decision"] == "escalate"
    assert result["constraint_decision"] == "confirm"


def test_approval_with_safeguards_fully_automated_low():
    facts = base_case()
    facts["decision_impact"] = "fully_automated"
    facts["consequence_severity"] = "low"
    result = run_case("aws_fa_low", facts)
    assert result["primary_decision"] == "approve_with_safeguards"
    assert result["constraint_decision"] == "confirm"
    assert "mandatory_safeguards" in result
    assert len(result["mandatory_safeguards"]) > 0


def test_jurisdiction_no_should_refuse():
    facts = base_case()
    facts["uk_public_sector_applicability"] = "no"
    result = run_case("jurisdiction_no", facts)
    assert result["primary_decision"] == "refuse_to_decide"
    assert result["constraint_decision"] == "refuse_to_decide"
