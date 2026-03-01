# python/explain.py
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List


def call_prolog_unmet_for_approve(
    project_root: Path,
    main_pl: Path,
    constraints_pl: Path,
    facts_pl: Path,
) -> List[str]:
    """
    Backward-chaining query:
      "What conditions would justify approval in this case?"

    Note: governance hygiene is enforced by callers (run_inference / Streamlit):
    they should NOT call this when the system is in a refusal state.
    """
    cmd = [
        "swipl",
        "-q",
        "-s", str(main_pl),
        "-s", str(constraints_pl),
        "-s", str(facts_pl),
        "-g", "main:run_unmet_for_approve_json",
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, cwd=str(project_root))
    if completed.returncode != 0:
        raise RuntimeError(
            "Prolog unmet-for-approve call failed.\n"
            f"Return code: {completed.returncode}\n"
            f"STDERR:\n{completed.stderr}\n"
            f"STDOUT:\n{completed.stdout}\n"
        )
    payload = json.loads(completed.stdout.strip())
    return payload.get("unmet_for_approve", [])


def explanation_completeness_score(
    missing_critical: List[str],
    fired_rules: List[str],
    unmet_for_approve: List[str],
    *,
    refused: bool = False,
) -> int:
    """
    Deterministic, simple score out of 100.

    Important: this is NOT a confidence score. It's an "explanation artefact completeness"
    heuristic for audit/oversight.

    Base scoring:
      - Start 100
      - Each missing critical field: -10
      - If no rules fired: -20
      - Each unmet approve requirement: -3

    Governance adjustment:
      - If the system refused (a valid governance outcome), do NOT penalise for unmet_for_approve,
        because callers should not compute that list in refusal states.
    """
    score = 100
    score -= 10 * len(missing_critical)

    if len(fired_rules) == 0:
        score -= 20

    if not refused:
        score -= 3 * len(unmet_for_approve)

    if score < 0:
        score = 0
    return score
