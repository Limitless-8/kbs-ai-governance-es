from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set

from run_inference import write_temp_facts_file, call_prolog, PROLOG_DIR, PROJECT_ROOT
from explain import call_prolog_unmet_for_approve


# ----------------------------
# 1) Search problem definition
# ----------------------------
# We define a state as a set of facts (a dict), and we can apply operators that
# "add or correct" one governance-related fact at a time to move closer to approval.
#
# We DO NOT infer in Python. We ask Prolog what is currently unmet for approval.
# That means Prolog remains authoritative; search is just a demonstration tool.


# Map from approve requirement atoms (returned by Prolog) to the fact assignment
# that would satisfy that requirement in our current schema.
REQUIREMENT_TO_FACT: Dict[str, Tuple[str, str]] = {
    # structural requirements:
    "jurisdiction_ok": ("uk_public_sector_applicability", "yes"),
    "severity_low": ("consequence_severity", "low"),
    "impact_advisory": ("decision_impact", "advisory"),
    # governance docs requirements:
    "dpia_present": ("dpia_exists", "yes"),
    "oversight_present": ("human_oversight_plan", "yes"),
    "appeals_present": ("appeals_mechanism", "yes"),
    "explain_present": ("explainability_provision", "yes"),
    "bias_present": ("bias_fairness_assessment", "yes"),
    "security_present": ("security_controls", "yes"),
    "monitoring_present": ("monitoring_incident_response", "yes"),
    "supplier_present": ("supplier_transparency", "yes"),
}


def base_case() -> Dict[str, Any]:
    # Same baseline schema you use elsewhere
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


def demo_start_case() -> Dict[str, Any]:
    """
    A deliberately "not-approvable" starting case to make search meaningful.
    It remains within jurisdiction but breaks multiple approval requirements.
    """
    f = base_case()
    # Break several approval requirements:
    f["decision_impact"] = "human_supported"          # should be advisory for approve in your current Prolog
    f["consequence_severity"] = "medium"              # should be low
    f["dpia_exists"] = "no"                           # should be yes
    f["human_oversight_plan"] = "no"                  # should be yes
    f["supplier_transparency"] = "no"                 # should be yes
    return f


def canonical_facts_key(facts: Dict[str, Any]) -> str:
    # stable key for visited-set (ignore ordering)
    return json.dumps(facts, sort_keys=True, separators=(",", ":"))


def unmet_for_approve(facts: Dict[str, Any]) -> List[str]:
    """
    Ask Prolog: what approval requirements are unmet under these facts?
    This uses your existing backward-chaining goal.
    """
    # temp facts file
    facts_path = write_temp_facts_file(facts, run_id="search_demo")
    unmet = call_prolog_unmet_for_approve(
        project_root=PROJECT_ROOT,
        main_pl=PROLOG_DIR / "main.pl",
        constraints_pl=PROLOG_DIR / "constraints.pl",
        facts_pl=facts_path,
    )
    return unmet


def heuristic(unmet: List[str]) -> int:
    # Greedy/A* heuristic: number of unmet requirements (lower is better)
    return len(unmet)


@dataclass(frozen=True)
class Node:
    facts: Dict[str, Any]
    path: Tuple[str, ...]  # human-readable operator descriptions


def neighbors(facts: Dict[str, Any]) -> List[Tuple[Dict[str, Any], str]]:
    """
    Generate next states by satisfying ONE currently-unmet requirement at a time.
    Operator = set a specific fact to a specific value.
    """
    unmet = unmet_for_approve(facts)
    next_states: List[Tuple[Dict[str, Any], str]] = []

    for req in unmet:
        if req not in REQUIREMENT_TO_FACT:
            # ignore unknown requirements (keeps the demo robust)
            continue

        k, v = REQUIREMENT_TO_FACT[req]
        if facts.get(k) == v:
            continue

        new_facts = dict(facts)
        new_facts[k] = v
        op_desc = f"set {k}={v} (to satisfy {req})"
        next_states.append((new_facts, op_desc))

    return next_states


# ----------------------------
# 2) BFS (uninformed search)
# ----------------------------
def bfs(start_facts: Dict[str, Any], max_expansions: int = 200) -> Tuple[Optional[Node], int]:
    start_unmet = unmet_for_approve(start_facts)
    if len(start_unmet) == 0:
        return Node(start_facts, ()), 0

    q = deque([Node(start_facts, ())])
    visited: Set[str] = {canonical_facts_key(start_facts)}
    expansions = 0

    while q and expansions < max_expansions:
        node = q.popleft()
        expansions += 1

        if len(unmet_for_approve(node.facts)) == 0:
            return node, expansions

        for nf, op in neighbors(node.facts):
            key = canonical_facts_key(nf)
            if key in visited:
                continue
            visited.add(key)
            q.append(Node(nf, node.path + (op,)))

    return None, expansions


# ----------------------------
# 3) Greedy best-first search
# ----------------------------
def greedy_best_first(start_facts: Dict[str, Any], max_expansions: int = 200) -> Tuple[Optional[Node], int]:
    # simple priority queue using list (small search space)
    frontier: List[Tuple[int, Node]] = []
    start_node = Node(start_facts, ())
    frontier.append((heuristic(unmet_for_approve(start_facts)), start_node))

    visited: Set[str] = {canonical_facts_key(start_facts)}
    expansions = 0

    while frontier and expansions < max_expansions:
        frontier.sort(key=lambda x: x[0])  # lowest heuristic first
        _, node = frontier.pop(0)
        expansions += 1

        if len(unmet_for_approve(node.facts)) == 0:
            return node, expansions

        for nf, op in neighbors(node.facts):
            key = canonical_facts_key(nf)
            if key in visited:
                continue
            visited.add(key)
            h = heuristic(unmet_for_approve(nf))
            frontier.append((h, Node(nf, node.path + (op,))))

    return None, expansions


def show_result(name: str, node: Optional[Node], expansions: int) -> None:
    print(f"\n=== {name} ===")
    print(f"Nodes expanded: {expansions}")
    if node is None:
        print("No solution found within expansion limit.")
        return
    print(f"Steps in path: {len(node.path)}")
    for i, step in enumerate(node.path, 1):
        print(f"  {i}. {step}")

    # Show final decision (to demonstrate we really reached approve conditions)
    facts_path = write_temp_facts_file(node.facts, run_id="search_demo_final")
    final_result = call_prolog(
        main_pl=PROLOG_DIR / "main.pl",
        constraints_pl=PROLOG_DIR / "constraints.pl",
        facts_pl=facts_path,
    )
    print("Final primary_decision:", final_result.get("primary_decision"))
    print("Final constraint_decision:", final_result.get("constraint_decision"))


def main() -> None:
    start = demo_start_case()

    print("Start case unmet requirements:", unmet_for_approve(start))

    node_bfs, exp_bfs = bfs(start, max_expansions=250)
    show_result("BFS (uninformed, shortest path)", node_bfs, exp_bfs)

    node_greedy, exp_greedy = greedy_best_first(start, max_expansions=250)
    show_result("Greedy best-first (informed, heuristic=#unmet)", node_greedy, exp_greedy)


if __name__ == "__main__":
    main()
