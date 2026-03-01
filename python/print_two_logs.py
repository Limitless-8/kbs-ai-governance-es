import json
from pathlib import Path

files = [
    Path("logs/20260126_215106_refuse_unclear_dpia.json"),
    Path("logs/20260126_215401_refuse_unclear_dpia.json"),
]

for p in files:
    rec = json.loads(p.read_text(encoding="utf-8"))
    inp = rec.get("inputs", {})
    res = rec.get("result", {})

    print("\n---", p.name, "---")
    print("primary/constraint:", res.get("primary_decision"), "/", res.get("constraint_decision"))
    print("missing_critical:", res.get("missing_critical"))
    print("unclear_critical:", res.get("unclear_critical"))
    print("fired_rules:", res.get("fired_rules"))
    print("inputs:", inp)
