# python/validation.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List


CRITICAL_FIELDS = [
    "uk_public_sector_applicability",
    "decision_impact",
    "consequence_severity",
    "dpia_exists",
    "human_oversight_plan",
    "appeals_mechanism",
    "explainability_provision",
    "bias_fairness_assessment",
    "security_controls",
    "monitoring_incident_response",
    "supplier_transparency",
]


ALLOWED_VALUES = {
    "uk_public_sector_applicability": {"yes", "no", "unclear"},
    "decision_impact": {"advisory", "human_supported", "fully_automated"},
    "consequence_severity": {"low", "medium", "high"},
    "personal_data_usage": {"yes", "no", "unclear"},
    "special_category_data": {"yes", "no", "unclear"},
    "biometric_processing": {"yes", "no", "unclear"},
    "childrens_data": {"yes", "no", "unclear"},
    "dpia_exists": {"yes", "no", "unclear"},
    "human_oversight_plan": {"yes", "no", "unclear"},
    "appeals_mechanism": {"yes", "no", "unclear"},
    "explainability_provision": {"yes", "no", "unclear"},
    "bias_fairness_assessment": {"yes", "no", "unclear"},
    "security_controls": {"yes", "no", "unclear"},
    "monitoring_incident_response": {"yes", "no", "unclear"},
    "supplier_transparency": {"yes", "no", "unclear"},
}


@dataclass
class ValidationResult:
    ok: bool
    errors: List[str]
    missing_critical: List[str]
    unclear_critical: List[str]


def validate_fact_dict(facts: Dict[str, Any]) -> ValidationResult:
    errors: List[str] = []

    # Missing critical fields (key absent)
    missing_critical = [k for k in CRITICAL_FIELDS if k not in facts]

    # Critical fields present but explicitly unclear (structured uncertainty)
    unclear_critical: List[str] = []
    for k in CRITICAL_FIELDS:
        if k in facts and facts.get(k) == "unclear":
            unclear_critical.append(k)

    # Validate allowed values for any provided field we recognise
    for k, v in facts.items():
        if k in ALLOWED_VALUES:
            if v not in ALLOWED_VALUES[k]:
                errors.append(
                    f"Invalid value for {k}: {v!r}. Allowed: {sorted(ALLOWED_VALUES[k])}"
                )

    ok = (len(errors) == 0)
    return ValidationResult(
        ok=ok,
        errors=errors,
        missing_critical=missing_critical,
        unclear_critical=sorted(unclear_critical),
    )
