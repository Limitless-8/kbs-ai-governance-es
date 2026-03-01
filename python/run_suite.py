from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List

from run_inference import write_temp_facts_file, call_prolog, PROLOG_DIR, PROJECT_ROOT

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Preferred column order (more readable than alphabetical)
FACT_ORDER = [
    "uk_public_sector_applicability",
    "decision_impact",
    "consequence_severity",
    "personal_data_usage",
    "special_category_data",
    "biometric_processing",
    "childrens_data",
    "dpia_exists",
    "human_oversight_plan",
    "appeals_mechanism",
    "explainability_provision",
    "bias_fairness_assessment",
    "security_controls",
    "monitoring_incident_response",
    "supplier_transparency",
]


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


@dataclass(frozen=True)
class Scenario:
    name: str
    facts: Dict[str, Any]
    expect_primary: str
    expect_constraint: str


def build_scenarios() -> List[Scenario]:
    scenarios: List[Scenario] = []

    # --- Baseline coverage ---
    scenarios.append(Scenario("approve", dict(base_case()), "approve", "confirm"))

    f = base_case()
    f["decision_impact"] = "fully_automated"
    f["consequence_severity"] = "low"
    scenarios.append(Scenario("approve_with_safeguards", dict(f), "approve_with_safeguards", "confirm"))

    f = base_case()
    f["decision_impact"] = "human_supported"
    f["consequence_severity"] = "high"
    scenarios.append(Scenario("escalate", dict(f), "escalate", "confirm"))

    f = base_case()
    f["decision_impact"] = "fully_automated"
    f["consequence_severity"] = "high"
    scenarios.append(Scenario("reject_veto", dict(f), "reject", "veto"))

    f = base_case()
    f.pop("dpia_exists")
    scenarios.append(Scenario("refuse_missing_dpia", dict(f), "refuse_to_decide", "refuse_to_decide"))

    f = base_case()
    f["dpia_exists"] = "unclear"
    scenarios.append(Scenario("refuse_unclear_dpia", dict(f), "refuse_to_decide", "refuse_to_decide"))

    f = base_case()
    f["uk_public_sector_applicability"] = "no"
    scenarios.append(Scenario("refuse_jurisdiction_no", dict(f), "refuse_to_decide", "refuse_to_decide"))

    f = base_case()
    f["uk_public_sector_applicability"] = "unclear"
    scenarios.append(Scenario("refuse_jurisdiction_unclear", dict(f), "refuse_to_decide", "refuse_to_decide"))

    # --- Rule coverage: force *_missing rules ---
    # Expected: jurisdiction OK but minimum approval conditions fail => default escalation (r25), constraint confirm.

    f = base_case()
    f["dpia_exists"] = "no"  # r10
    scenarios.append(Scenario("escalate_dpia_no", dict(f), "escalate", "confirm"))

    f = base_case()
    f["human_oversight_plan"] = "no"  # r12
    scenarios.append(Scenario("escalate_oversight_no", dict(f), "escalate", "confirm"))

    f = base_case()
    f["appeals_mechanism"] = "no"  # r14
    scenarios.append(Scenario("escalate_appeals_no", dict(f), "escalate", "confirm"))

    f = base_case()
    f["explainability_provision"] = "no"  # r16
    scenarios.append(Scenario("escalate_explainability_no", dict(f), "escalate", "confirm"))

    f = base_case()
    f["bias_fairness_assessment"] = "no"  # r18
    scenarios.append(Scenario("escalate_bias_no", dict(f), "escalate", "confirm"))

    f = base_case()
    f["security_controls"] = "no"  # r20
    scenarios.append(Scenario("escalate_security_no", dict(f), "escalate", "confirm"))

    f = base_case()
    f["monitoring_incident_response"] = "no"  # r22
    scenarios.append(Scenario("escalate_monitoring_no", dict(f), "escalate", "confirm"))

    # Supplier transparency explicitly "no" (blocks r24 approval)
    f = base_case()
    f["supplier_transparency"] = "no"  # r23 supplier_missing
    scenarios.append(Scenario("escalate_supplier_no", dict(f), "escalate", "confirm"))

    return scenarios


def run_one(run_id: str, facts: Dict[str, Any]) -> Dict[str, Any]:
    facts_path = write_temp_facts_file(facts, run_id)
    return call_prolog(
        main_pl=PROLOG_DIR / "main.pl",
        constraints_pl=PROLOG_DIR / "constraints.pl",
        facts_pl=facts_path,
    )


def parse_rule_ids(fired_rules_cell: str) -> List[str]:
    if not fired_rules_cell:
        return []
    return [x.strip() for x in fired_rules_cell.split(",") if x.strip()]


def compute_rule_coverage(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    coverage["r01"] = {"count": 3, "scenarios": ["approve", ...]}
    """
    coverage: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        scenario = row.get("scenario", "")
        fired = parse_rule_ids(row.get("fired_rules", ""))
        for rid in fired:
            if rid not in coverage:
                coverage[rid] = {"count": 0, "scenarios": []}
            coverage[rid]["count"] += 1
            if scenario and scenario not in coverage[rid]["scenarios"]:
                coverage[rid]["scenarios"].append(scenario)
    for rid in coverage:
        coverage[rid]["scenarios"] = sorted(coverage[rid]["scenarios"])
    return coverage


def all_rule_ids() -> List[str]:
    return [f"r{str(i).zfill(2)}" for i in range(1, 26)]


def main() -> None:
    require_full_coverage = True  # <-- NEW: fail if any r01..r25 never fires

    scenarios = build_scenarios()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_csv = ARTIFACTS_DIR / f"suite_{stamp}.csv"

    all_keys = {k for s in scenarios for k in s.facts.keys()}
    input_keys = [k for k in FACT_ORDER if k in all_keys] + sorted(all_keys - set(FACT_ORDER))

    fieldnames = (
        ["run_id", "scenario"]
        + input_keys
        + [
            "primary_decision",
            "constraint_decision",
            "missing_critical",
            "unclear_critical",
            "fired_rules",
            "reasons",
            "constraint_reasons",
        ]
    )

    failures: List[str] = []
    all_rows: List[Dict[str, Any]] = []

    with out_csv.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()

        for s in scenarios:
            run_id = f"{stamp}_{s.name}"
            result = run_one(run_id, s.facts)

            got_p = result.get("primary_decision")
            got_c = result.get("constraint_decision")
            if got_p != s.expect_primary or got_c != s.expect_constraint:
                failures.append(
                    f"{s.name}: expected ({s.expect_primary},{s.expect_constraint}) got ({got_p},{got_c})"
                )

            row: Dict[str, Any] = {"run_id": run_id, "scenario": s.name}
            for k in input_keys:
                row[k] = s.facts.get(k, "")

            row["primary_decision"] = got_p
            row["constraint_decision"] = got_c
            row["missing_critical"] = ",".join(result.get("missing_critical", []))
            row["unclear_critical"] = ",".join(result.get("unclear_critical", []))
            row["fired_rules"] = ",".join(result.get("fired_rules", []))
            row["reasons"] = " | ".join(result.get("reasons", []))
            row["constraint_reasons"] = " | ".join(result.get("constraint_reasons", []))

            writer.writerow(row)
            all_rows.append(row)

    print(f"Wrote CSV: {out_csv}")

    # ----------------------------
    # Write rule coverage CSV
    # ----------------------------
    coverage_csv = ARTIFACTS_DIR / f"rule_coverage_{stamp}.csv"
    coverage = compute_rule_coverage(all_rows)

    uncovered = []
    with coverage_csv.open("w", newline="", encoding="utf-8") as fp:
        fieldnames_cov = ["rule_id", "covered", "hit_count", "scenarios"]
        w_cov = csv.DictWriter(fp, fieldnames=fieldnames_cov)
        w_cov.writeheader()

        for rid in all_rule_ids():
            info = coverage.get(rid, {"count": 0, "scenarios": []})
            is_covered = info["count"] > 0
            if not is_covered:
                uncovered.append(rid)

            w_cov.writerow(
                {
                    "rule_id": rid,
                    "covered": "yes" if is_covered else "no",
                    "hit_count": info["count"],
                    "scenarios": " | ".join(info["scenarios"]),
                }
            )

    print(f"Wrote rule coverage CSV: {coverage_csv}")

    if failures:
        print("\nFAILURES:")
        for msg in failures:
            print(" -", msg)
        raise SystemExit(1)

    if require_full_coverage and uncovered:
        print("\nRULE COVERAGE INCOMPLETE:")
        print("Uncovered rules:", ", ".join(uncovered))
        raise SystemExit(2)

    print("All scenarios matched expected outcomes.")
    print(f"Covered {len(all_rule_ids()) - len(uncovered)} / {len(all_rule_ids())} rules.")


if __name__ == "__main__":
    main()
