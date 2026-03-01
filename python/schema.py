# python/schema.py
from dataclasses import dataclass, asdict
from typing import Literal, Optional, Dict, Any


YesNoUnclear = Literal["yes", "no", "unclear"]
DecisionImpact = Literal["advisory", "human_supported", "fully_automated"]
Severity = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class DeploymentInput:
    # Minimal core fields for our current Prolog schema (we will expand later)
    uk_public_sector_applicability: YesNoUnclear
    decision_impact: DecisionImpact
    consequence_severity: Severity

    personal_data_usage: YesNoUnclear
    special_category_data: YesNoUnclear
    biometric_processing: YesNoUnclear
    childrens_data: YesNoUnclear

    dpia_exists: YesNoUnclear
    human_oversight_plan: YesNoUnclear
    appeals_mechanism: YesNoUnclear
    explainability_provision: YesNoUnclear
    bias_fairness_assessment: YesNoUnclear
    security_controls: YesNoUnclear
    monitoring_incident_response: YesNoUnclear
    supplier_transparency: YesNoUnclear

    def to_fact_dict(self) -> Dict[str, Any]:
        """
        Return a flat dict of facts that can be turned into Prolog input(Key,Value).
        """
        return asdict(self)


def example_case_low_risk_approve() -> DeploymentInput:
    return DeploymentInput(
        uk_public_sector_applicability="yes",
        decision_impact="advisory",
        consequence_severity="low",
        personal_data_usage="yes",
        special_category_data="no",
        biometric_processing="no",
        childrens_data="no",
        dpia_exists="yes",
        human_oversight_plan="yes",
        appeals_mechanism="yes",
        explainability_provision="yes",
        bias_fairness_assessment="yes",
        security_controls="yes",
        monitoring_incident_response="yes",
        supplier_transparency="yes",
    )
