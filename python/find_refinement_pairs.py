from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict

LOGS_DIR = Path("logs")  # adjust if needed

def canonical_inputs(d: dict) -> str:
    # stable string key for identical input dictionaries
    return json.dumps(d, sort_keys=True, separators=(",", ":"))

def main():
    files = sorted(LOGS_DIR.glob("*.json"))
    print("Logs found:", len(files))

    groups = defaultdict(list)

    for fp in files:
        rec = json.loads(fp.read_text(encoding="utf-8"))
        inputs = rec.get("inputs", {}) or {}
        result = rec.get("result", {}) or {}

        key = canonical_inputs(inputs)
        groups[key].append({
            "file": fp.name,
            "ts": rec.get("timestamp_utc"),
            "primary": result.get("primary_decision"),
            "constraint": result.get("constraint_decision"),
            "fired": tuple(result.get("fired_rules", []) or []),
            "reasons": tuple(result.get("reasons", []) or []),
            "extras": tuple(sorted((k for k in result.keys() if k not in {
                "primary_decision","constraint_decision","fired_rules","reasons",
                "constraint_reasons","missing_critical","unclear_critical"
            }))),
        })

    decision_changes = []
    trace_changes = []

    for key, runs in groups.items():
        if len(runs) < 2:
            continue
        runs_sorted = sorted(runs, key=lambda r: (r["ts"] or "", r["file"]))
        prim_set = {(r["primary"], r["constraint"]) for r in runs_sorted}
        if len(prim_set) > 1:
            decision_changes.append(runs_sorted)

        # same decision but different fired rules / reasons / new output fields
        if len(prim_set) == 1:
            fired_set = {r["fired"] for r in runs_sorted}
            reasons_set = {r["reasons"] for r in runs_sorted}
            extras_set = {r["extras"] for r in runs_sorted}
            if len(fired_set) > 1 or len(reasons_set) > 1 or len(extras_set) > 1:
                trace_changes.append(runs_sorted)

    print("\n=== Candidates: SAME INPUTS, DIFFERENT DECISIONS ===")
    for runs in decision_changes[:10]:
        print("\n---")
        for r in runs:
            print(r["ts"], r["file"], "->", (r["primary"], r["constraint"]))

    print("\n=== Candidates: SAME INPUTS, SAME DECISION, BUT TRACE/OUTPUT CHANGED ===")
    for runs in trace_changes[:10]:
        print("\n---")
        for r in runs:
            print(r["ts"], r["file"], "->", (r["primary"], r["constraint"]),
                  "| fired_len:", len(r["fired"]), "| reasons_len:", len(r["reasons"]),
                  "| extras:", r["extras"])

    print("\nDone.")
    print("Decision-change groups:", len(decision_changes))
    print("Trace-change groups:", len(trace_changes))

if __name__ == "__main__":
    main()
