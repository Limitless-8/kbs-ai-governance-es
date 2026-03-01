# python/eda_logs.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOGS_DIR = PROJECT_ROOT / "logs"


def load_logs() -> List[Dict[str, Any]]:
    if not LOGS_DIR.exists():
        return []
    records: List[Dict[str, Any]] = []
    for p in sorted(LOGS_DIR.glob("*.json")):
        try:
            records.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"Skipping unreadable log {p.name}: {e}")
    return records


def _safe_list(x: Any) -> List[Any]:
    if isinstance(x, list):
        return x
    return []


def main() -> None:
    logs = load_logs()
    if not logs:
        print("No logs found in ./logs. Run python/run_inference.py a few times first.")
        return

    # Flatten into a dataframe
    rows = []
    for rec in logs:
        result = rec.get("result", {}) or {}
        validation = result.get("_validation", {}) or {}

        rows.append(
            {
                "run_id": rec.get("run_id"),
                "timestamp_utc": rec.get("timestamp_utc"),
                "primary_decision": result.get("primary_decision"),
                "constraint_decision": result.get("constraint_decision"),
                "fired_rules": _safe_list(result.get("fired_rules")),
                "missing_critical": _safe_list(result.get("missing_critical")),
                "validation_missing_critical": _safe_list(validation.get("missing_critical")),
                "validation_unclear_critical": _safe_list(validation.get("unclear_critical")),
            }
        )

    df = pd.DataFrame(rows)

    print("\n=== Basic counts ===")
    print("Total runs:", len(df))

    print("\n=== Outcome distribution: primary_decision ===")
    print(df["primary_decision"].value_counts(dropna=False).to_string())

    print("\n=== Outcome distribution: constraint_decision ===")
    print(df["constraint_decision"].value_counts(dropna=False).to_string())

    # Rule activation frequency
    all_rules = df.explode("fired_rules")["fired_rules"].dropna()
    rule_counts = all_rules.value_counts()

    print("\n=== Top fired rules ===")
    print(rule_counts.head(15).to_string())

    # Refusal drivers (now includes both missing + unclear critical evidence)
    refusal_df = df[df["constraint_decision"] == "refuse_to_decide"].copy()
    print("\n=== Refusal drivers (constraint=refuse_to_decide) ===")
    if len(refusal_df) > 0:
        miss = refusal_df.explode("missing_critical")["missing_critical"].dropna()
        v_miss = refusal_df.explode("validation_missing_critical")["validation_missing_critical"].dropna()
        v_unclear = refusal_df.explode("validation_unclear_critical")["validation_unclear_critical"].dropna()

        if len(miss) > 0:
            print("\n- Prolog missing_critical:")
            print(miss.value_counts().to_string())
        else:
            print("\n- Prolog missing_critical: (none)")

        if len(v_miss) > 0:
            print("\n- Validation missing_critical:")
            print(v_miss.value_counts().to_string())
        else:
            print("\n- Validation missing_critical: (none)")

        if len(v_unclear) > 0:
            print("\n- Validation unclear_critical:")
            print(v_unclear.value_counts().to_string())
        else:
            print("\n- Validation unclear_critical: (none)")
    else:
        print("No refusal_to_decide cases in logs yet.")

    # Escalation drivers
    esc_df = df[df["primary_decision"] == "escalate"].copy()
    print("\n=== Escalation drivers (primary_decision=escalate) ===")
    if len(esc_df) > 0:
        esc_rules = esc_df.explode("fired_rules")["fired_rules"].dropna()
        print(esc_rules.value_counts().head(15).to_string())
    else:
        print("No escalate cases in logs yet.")

    print("\n=== Done ===")

if __name__ == "__main__":
    main()
