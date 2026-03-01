# python/run_inference.py
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from explain import call_prolog_unmet_for_approve, explanation_completeness_score
from schema import example_case_low_risk_approve
from validation import validate_fact_dict


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROLOG_DIR = PROJECT_ROOT / "prolog"
TMP_DIR = PROJECT_ROOT / "tmp"
LOGS_DIR = PROJECT_ROOT / "logs"


def _prolog_escape_atom(s: str) -> str:
    """
    For our controlled atoms (yes/no/unclear etc.) we can safely emit as bare atoms.
    If you later add free text, you'll need quoted strings with escaping.
    """
    import re
    if not re.fullmatch(r"[a-z0-9_]+", s):
        raise ValueError(f"Unsafe atom for Prolog: {s!r}")
    return s


def write_temp_facts_file(facts: Dict[str, Any], run_id: str) -> Path:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    facts_path = TMP_DIR / f"{run_id}_facts.pl"

    lines: List[str] = []
    lines.append(f"% Auto-generated facts for run_id={run_id}")
    lines.append(":- dynamic main:input/2.")
    lines.append("")

    for k, v in facts.items():
        if v is None:
            continue
        key_atom = _prolog_escape_atom(k)
        val_atom = _prolog_escape_atom(str(v))
        lines.append(f"main:input({key_atom}, {val_atom}).")

    facts_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return facts_path


def call_prolog(main_pl: Path, constraints_pl: Path, facts_pl: Path) -> Dict[str, Any]:
    """
    Calls SWI-Prolog deterministically and expects one JSON object on stdout.
    """
    cmd = [
        "swipl",
        "-q",
        "-s", str(main_pl),
        "-s", str(constraints_pl),
        "-s", str(facts_pl),
        "-g", "main:run",
    ]

    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )

    if completed.returncode != 0:
        raise RuntimeError(
            "Prolog call failed.\n"
            f"Return code: {completed.returncode}\n"
            f"STDERR:\n{completed.stderr}\n"
            f"STDOUT:\n{completed.stdout}\n"
        )

    out = completed.stdout.strip()
    return json.loads(out)


def write_audit_log(run_id: str, facts: Dict[str, Any], result: Dict[str, Any]) -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f"{run_id}.json"

    payload = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": facts,
        "result": result,
    }

    log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return log_path


def _compute_extras(facts_path: Path, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute non-inferential explanation extras.

    Governance hygiene:
    - Do NOT run counterfactual approval requirements when the system refuses.
    """
    primary = result.get("primary_decision")
    constraint = result.get("constraint_decision")
    missing_critical = result.get("missing_critical", [])

    unmet: List[str] = []
    refused = (constraint == "refuse_to_decide") or (primary == "refuse_to_decide")

    if not refused:
        unmet = call_prolog_unmet_for_approve(
            project_root=PROJECT_ROOT,
            main_pl=PROLOG_DIR / "main.pl",
            constraints_pl=PROLOG_DIR / "constraints.pl",
            facts_pl=facts_path,
        )

    score = explanation_completeness_score(
        missing_critical=missing_critical,
        fired_rules=result.get("fired_rules", []),
        unmet_for_approve=unmet,
        refused=refused,
    )

    return {
        "unmet_for_approve": unmet,
        "explanation_completeness_score": score,
    }


def main() -> None:
    # 1) build an example case
    inp = example_case_low_risk_approve()
    facts = inp.to_fact_dict()

    # 2) validate (Python has no inference authority; only validation/reporting)
    vr = validate_fact_dict(facts)
    if not vr.ok:
        print("VALIDATION FAILED:")
        for e in vr.errors:
            print(" -", e)

        # High-value governance visibility (not inference):
        if vr.missing_critical:
            print("\nMissing critical fields:")
            for k in vr.missing_critical:
                print(" -", k)

        if vr.unclear_critical:
            print("\nCritical fields marked 'unclear' (structured uncertainty):")
            for k in vr.unclear_critical:
                print(" -", k)

        raise SystemExit(1)

    # 3) generate temp facts file
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    facts_path = write_temp_facts_file(facts, run_id)

    # 4) call Prolog (authoritative inference)
    result = call_prolog(
        main_pl=PROLOG_DIR / "main.pl",
        constraints_pl=PROLOG_DIR / "constraints.pl",
        facts_pl=facts_path,
    )

    # 5) attach explanation extras (still non-inferential)
    result.update(_compute_extras(facts_path=facts_path, result=result))

    # 6) OPTIONAL: attach validation visibility to the audit result (metadata-only)
    # This does not influence Prolog and helps audit readers understand uncertainty.
    result["_validation"] = {
        "missing_critical": vr.missing_critical,
        "unclear_critical": vr.unclear_critical,
    }

    # 7) write audit log
    log_path = write_audit_log(run_id, facts, result)

    print("RUN OK")
    print("Result:", json.dumps(result, indent=2))
    print("Log written to:", log_path)


if __name__ == "__main__":
    main()
