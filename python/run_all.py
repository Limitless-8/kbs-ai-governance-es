from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = PROJECT_ROOT / "python"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
LOGS_DIR = PROJECT_ROOT / "logs"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def run_cmd(cmd: list[str], *, cwd: Path) -> Tuple[int, str, str]:
    """
    Run a command and return (returncode, stdout, stderr).
    """
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        shell=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def determinism_check() -> Dict[str, Any]:
    """
    Determinism proof:
      same inputs, same Prolog call, outputs identical JSON.

    Notes:
    - We call Prolog directly via the Python helper call_prolog (no logging).
    - This avoids timestamps/run_id differences.
    """
    # Make python/ importable when running from project root
    sys.path.append(str(PYTHON_DIR))

    from run_inference import write_temp_facts_file, call_prolog, PROLOG_DIR  # noqa: E402

    facts = {
        "uk_public_sector_applicability": "yes",
        "decision_impact": "fully_automated",
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

    # Fixed run_id so the temp facts file name is stable (doesn't affect Prolog output).
    run_id = "DETERMINISM_CHECK_FIXED"
    facts_path = write_temp_facts_file(facts, run_id)

    res1 = call_prolog(
        main_pl=PROLOG_DIR / "main.pl",
        constraints_pl=PROLOG_DIR / "constraints.pl",
        facts_pl=facts_path,
    )
    res2 = call_prolog(
        main_pl=PROLOG_DIR / "main.pl",
        constraints_pl=PROLOG_DIR / "constraints.pl",
        facts_pl=facts_path,
    )

    ok = (res1 == res2)
    return {
        "ok": ok,
        "result_1": res1,
        "result_2": res2,
    }


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    summary_path = ARTIFACTS_DIR / f"run_all_summary_{stamp}.json"

    steps = []
    overall_ok = True

    # 1) pytest
    rc, out, err = run_cmd(["pytest", "-q"], cwd=PROJECT_ROOT)
    steps.append(
        {
            "step": "pytest",
            "ok": rc == 0,
            "returncode": rc,
            "stdout": out.strip(),
            "stderr": err.strip(),
        }
    )
    overall_ok = overall_ok and (rc == 0)

    # 2) suite + rule coverage (expects you have python/run_suite.py)
    suite_script = PYTHON_DIR / "run_suite.py"
    if suite_script.exists():
        rc, out, err = run_cmd([sys.executable, str(suite_script)], cwd=PROJECT_ROOT)
        steps.append(
            {
                "step": "suite_and_rule_coverage",
                "ok": rc == 0,
                "returncode": rc,
                "stdout": out.strip(),
                "stderr": err.strip(),
            }
        )
        overall_ok = overall_ok and (rc == 0)
    else:
        steps.append(
            {
                "step": "suite_and_rule_coverage",
                "ok": False,
                "returncode": None,
                "stdout": "",
                "stderr": "Missing python/run_suite.py (create/rename your suite script to python/run_suite.py).",
            }
        )
        overall_ok = False

    # 3) EDA over logs (prints distributions)
    eda_script = PYTHON_DIR / "eda_logs.py"
    if eda_script.exists():
        rc, out, err = run_cmd([sys.executable, str(eda_script)], cwd=PROJECT_ROOT)
        steps.append(
            {
                "step": "eda_logs",
                "ok": rc == 0,
                "returncode": rc,
                "stdout": out.strip(),
                "stderr": err.strip(),
            }
        )
        overall_ok = overall_ok and (rc == 0)
    else:
        steps.append(
            {
                "step": "eda_logs",
                "ok": False,
                "returncode": None,
                "stdout": "",
                "stderr": "Missing python/eda_logs.py",
            }
        )
        overall_ok = False

    # 4) determinism check
    try:
        det = determinism_check()
        steps.append({"step": "determinism_check", **det})
        overall_ok = overall_ok and bool(det["ok"])
    except Exception as e:
        steps.append(
            {
                "step": "determinism_check",
                "ok": False,
                "error": str(e),
            }
        )
        overall_ok = False

    # Write machine-readable summary
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overall_ok": overall_ok,
        "logs_present": LOGS_DIR.exists(),
        "log_count": len(list(LOGS_DIR.glob("*.json"))) if LOGS_DIR.exists() else 0,
        "steps": steps,
    }
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Console report (examiner-friendly)
    print("\n=== RUN-ALL SUMMARY ===")
    print("overall_ok:", overall_ok)
    print("summary_json:", summary_path)
    print("-----------------------")
    for s in steps:
        print(f"- {s['step']}: {'PASS' if s.get('ok') else 'FAIL'}")

    if not overall_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
