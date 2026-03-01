% prolog/main.pl
% Authoritative inference engine:
% - deterministic forward chaining
% - exactly 25 production rules (R01–R25) represented as r01..r25
% - ordered trace of fired rules
% - refusal under uncertainty when critical inputs are missing
% - outputs JSON to stdout

:- module(main, [run/0, run_unmet_for_approve_json/0]).

:- use_module(json_writer).
:- use_module(rule_text).
:- use_module(constraints).

% Input facts will be provided by Python in a temp file:
% input(Key, Value).
:- dynamic input/2.

% Working memory derived facts:
:- dynamic wm/1.
% Track rule firing:
:- dynamic fired/1.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 1) Critical fields (for refusal-under-uncertainty)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

critical_field(uk_public_sector_applicability).
critical_field(decision_impact).
critical_field(consequence_severity).

critical_field(dpia_exists).
critical_field(human_oversight_plan).
critical_field(appeals_mechanism).
critical_field(explainability_provision).
critical_field(bias_fairness_assessment).
critical_field(security_controls).
critical_field(monitoring_incident_response).
critical_field(supplier_transparency).

% We keep "missing_critical" as strictly "absent entirely".
% (This preserves meaning in logs + constraint layer rule naming.)
missing_critical_fields(MissingKeys) :-
    findall(K, (critical_field(K), \+ input(K,_)), MissingKeys).

% Unclear critical evidence (present but explicitly marked as "unclear").
unclear_critical_fields(UnclearKeys) :-
    findall(K, (critical_field(K), input(K, unclear)), UnclearKeys).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 2) Deterministic forward chaining framework
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

reset_wm :-
    retractall(wm(_)),
    retractall(fired(_)).

already_fired(RuleId) :- fired(RuleId).

mark_fired(RuleId) :- assertz(fired(RuleId)).

add_wm(Fact) :-
    ( wm(Fact) -> true ; assertz(wm(Fact)) ).

no_primary_decision :-
    \+ wm(primary_decision(_)).

% Apply rules in fixed order repeatedly until fixpoint (no new rule fires).
forward_chain(TraceOut) :-
    forward_chain_loop,
    findall(R, fired(R), TraceOut).

forward_chain_loop :-
    ( apply_rules_once(FiredSomething),
      FiredSomething = true ->
        forward_chain_loop
    ; true).

apply_rules_once(FiredSomething) :-
    apply_rules_in_order([r01,r02,r03,r04,r05,r06,r07,r08,r09,r10,
                          r11,r12,r13,r14,r15,r16,r17,r18,r19,r20,
                          r21,r22,r23,r24,r25],
                         false,
                         FiredSomething).

apply_rules_in_order([], Acc, Acc).
apply_rules_in_order([R|Rs], Acc, FiredSomething) :-
    ( try_fire(R) ->
        apply_rules_in_order(Rs, true, FiredSomething)
    ;   apply_rules_in_order(Rs, Acc, FiredSomething)
    ).

try_fire(RuleId) :-
    \+ already_fired(RuleId),
    rule(RuleId, Condition, Actions),
    call(Condition),
    call(Actions),
    mark_fired(RuleId).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 3) Rule base (EXACTLY 25 rules)
% Each rule is deterministic: rule(Id, ConditionGoal, ActionGoal).
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% R01: Confirm UK public-sector applicability (yes).
rule(r01,
     ( input(uk_public_sector_applicability, yes) ),
     ( add_wm(jurisdiction_ok) )).

% R02: Jurisdiction unclear or not applicable: system lacks authority to decide.
rule(r02,
     ( input(uk_public_sector_applicability, unclear)
     ; input(uk_public_sector_applicability, no)
     ),
     ( add_wm(jurisdiction_unclear) )).

% R03: High severity.
rule(r03,
     ( input(consequence_severity, high) ),
     ( add_wm(high_severity) )).

% R04: Fully automated impact.
rule(r04,
     ( input(decision_impact, fully_automated) ),
     ( add_wm(fully_automated) )).

% R05 (merged): Data/system profile flags (personal/special/biometric/children).
% Consolidated to preserve the 25-rule governance boundary.
rule(r05,
     ( input(personal_data_usage, yes)
     ; input(special_category_data, yes)
     ; input(biometric_processing, yes)
     ; input(childrens_data, yes)
     ),
     ( ( input(personal_data_usage, yes)     -> add_wm(personal_data)     ; true ),
       ( input(special_category_data, yes)   -> add_wm(special_category)  ; true ),
       ( input(biometric_processing, yes)    -> add_wm(biometric)         ; true ),
       ( input(childrens_data, yes)          -> add_wm(children_data)     ; true ),
       % Optional aggregate marker for "heightened data sensitivity"
       ( ( input(special_category_data, yes)
         ; input(biometric_processing, yes)
         ; input(childrens_data, yes)
         ) -> add_wm(high_risk_data) ; true )
     )).

% R06: Primary refusal rule (missing critical OR unclear critical OR jurisdiction unclear).
rule(r06,
     ( no_primary_decision,
       ( (missing_critical_fields(M), M \= [])
       ; (unclear_critical_fields(U), U \= [])
       ; wm(jurisdiction_unclear)
       )
     ),
     ( add_wm(primary_decision(refuse_to_decide)) )).

% R07: Reject when fully automated + high severity (within jurisdiction).
rule(r07,
     ( no_primary_decision,
       wm(jurisdiction_ok),
       wm(fully_automated),
       wm(high_severity)
     ),
     ( add_wm(primary_decision(reject)) )).

% R08: Approve with safeguards when fully automated but not high severity.
rule(r08,
     ( no_primary_decision,
       wm(jurisdiction_ok),
       wm(fully_automated),
       \+ wm(high_severity)
     ),
     ( add_wm(primary_decision(approve_with_safeguards)) )).

% R09: DPIA exists.
rule(r09,
     ( input(dpia_exists, yes) ),
     ( add_wm(dpia_present) )).

% R10: DPIA missing.
rule(r10,
     ( input(dpia_exists, no) ),
     ( add_wm(dpia_missing) )).

% R11: Oversight exists.
rule(r11,
     ( input(human_oversight_plan, yes) ),
     ( add_wm(oversight_present) )).

% R12: Oversight missing.
rule(r12,
     ( input(human_oversight_plan, no) ),
     ( add_wm(oversight_missing) )).

% R13: Appeals exists.
rule(r13,
     ( input(appeals_mechanism, yes) ),
     ( add_wm(appeals_present) )).

% R14: Appeals missing.
rule(r14,
     ( input(appeals_mechanism, no) ),
     ( add_wm(appeals_missing) )).

% R15: Explainability exists.
rule(r15,
     ( input(explainability_provision, yes) ),
     ( add_wm(explain_present) )).

% R16: Explainability missing.
rule(r16,
     ( input(explainability_provision, no) ),
     ( add_wm(explain_missing) )).

% R17: Bias/fairness exists.
rule(r17,
     ( input(bias_fairness_assessment, yes) ),
     ( add_wm(bias_present) )).

% R18: Bias/fairness missing.
rule(r18,
     ( input(bias_fairness_assessment, no) ),
     ( add_wm(bias_missing) )).

% R19: Security exists.
rule(r19,
     ( input(security_controls, yes) ),
     ( add_wm(security_present) )).

% R20: Security missing.
rule(r20,
     ( input(security_controls, no) ),
     ( add_wm(security_missing) )).

% R21: Monitoring exists.
rule(r21,
     ( input(monitoring_incident_response, yes) ),
     ( add_wm(monitoring_present) )).

% R22: Monitoring missing.
rule(r22,
     ( input(monitoring_incident_response, no) ),
     ( add_wm(monitoring_missing) )).

% R23 (merged): Supplier transparency yes/no in one rule (frees r24).
rule(r23,
     ( input(supplier_transparency, yes)
     ; input(supplier_transparency, no)
     ),
     ( ( input(supplier_transparency, yes) -> add_wm(supplier_present)
       ; input(supplier_transparency, no)  -> add_wm(supplier_missing)
       )
     )).

% R24: Propose low-risk approval when minimum conditions satisfied.
rule(r24,
     ( no_primary_decision,
       wm(jurisdiction_ok),
       input(consequence_severity, low),
       input(decision_impact, advisory),
       wm(dpia_present),
       wm(oversight_present),
       wm(appeals_present),
       wm(explain_present),
       wm(bias_present),
       wm(security_present),
       wm(monitoring_present),
       wm(supplier_present)
     ),
     ( add_wm(primary_decision(approve)) )).

% R25: Default escalation (only when jurisdiction is OK and nothing else decided).
rule(r25,
     ( no_primary_decision,
       wm(jurisdiction_ok)
     ),
     ( add_wm(primary_decision(escalate)) )).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 4) Primary decision selection (minimal; rule-derived)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

primary_decision(Decision) :-
    ( wm(primary_decision(Decision)) -> true
    ; Decision = refuse_to_decide ).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 4b) Mandatory safeguards (machine-readable, non-decisional)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Safeguards are emitted only as an explanation artefact.
% They DO NOT change the primary decision; they increase actionability for oversight.

mandatory_safeguards(PrimaryDecision, Safeguards) :-
    ( PrimaryDecision == approve_with_safeguards ->
        % Deterministic list (kept stable for audit).
        Safeguards = [
            human_oversight_required,
            appeal_route_required,
            explainability_required,
            monitoring_required,
            incident_response_required,
            supplier_transparency_required
        ]
    ; Safeguards = []
    ).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 5) Build reasons list from fired rule IDs
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

reasons_for_fired_rules(FiredRuleIds, Reasons) :-
    findall(S, (member(R, FiredRuleIds), rule_text:rule_reason(R, S)), Reasons).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 6) Output JSON for Python
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

run :-
    reset_wm,
    missing_critical_fields(Missing),
    unclear_critical_fields(UnclearCritical),
    forward_chain(FiredRuleIds),
    primary_decision(PrimaryDecision),
    reasons_for_fired_rules(FiredRuleIds, PrimaryReasons),

    % UPDATED: pass BOTH missing + unclear into constraint layer (defence-in-depth)
    constraints:constraint_decision(
        PrimaryDecision,
        Missing,
        UnclearCritical,
        ConstraintDecision,
        ConstraintReasonIds
    ),
    findall(S, (member(CR, ConstraintReasonIds), rule_text:rule_reason(CR, S)), ConstraintReasons),

mandatory_safeguards(PrimaryDecision, Safeguards),

json_writer:json_write_obj([
     "primary_decision"=PrimaryDecision,
     "constraint_decision"=ConstraintDecision,
     "fired_rules"=arr(FiredRuleIds),
     "reasons"=arr(PrimaryReasons),
     "constraint_reasons"=arr(ConstraintReasons),
     "mandatory_safeguards"=arr(Safeguards),
     "missing_critical"=arr(Missing),
     "unclear_critical"=arr(UnclearCritical)
     ]),

    nl,
    halt.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 7) Backward-chaining support (counterfactual requirements)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

approve_requirements([
    jurisdiction_ok,
    severity_low,
    impact_advisory,
    dpia_present,
    oversight_present,
    appeals_present,
    explain_present,
    bias_present,
    security_present,
    monitoring_present,
    supplier_present
]).

req_met(jurisdiction_ok) :- wm(jurisdiction_ok).
req_met(severity_low) :- input(consequence_severity, low).
req_met(impact_advisory) :- input(decision_impact, advisory).
req_met(dpia_present) :- wm(dpia_present).
req_met(oversight_present) :- wm(oversight_present).
req_met(appeals_present) :- wm(appeals_present).
req_met(explain_present) :- wm(explain_present).
req_met(bias_present) :- wm(bias_present).
req_met(security_present) :- wm(security_present).
req_met(monitoring_present) :- wm(monitoring_present).
req_met(supplier_present) :- wm(supplier_present).

unmet_approve_requirements(Unmet) :-
    approve_requirements(Reqs),
    findall(R, (member(R, Reqs), \+ req_met(R)), Unmet).

run_unmet_for_approve_json :-
    reset_wm,
    forward_chain(_Fired),
    unmet_approve_requirements(Unmet),
    json_writer:json_write_obj([
        "unmet_for_approve"=arr(Unmet)
    ]),
    nl,
    halt.
