% prolog/constraints.pl
% Governance constraint layer (subordinate authority).
% <= 8 deterministic rules. Output is one of:
%   confirm | veto | refuse_to_decide
%
% This layer NEVER generates a primary decision.
% It only governs whether issuing the primary decision is legitimate.

:- module(constraints, [constraint_decision/5]).

% constraint_decision(
%   +PrimaryDecision,
%   +MissingCritical,
%   +UnclearCritical,
%   -ConstraintDecision,
%   -ConstraintReasons
% )

constraint_decision(Primary, MissingCritical, UnclearCritical, Decision, Reasons) :-
    % Apply rules in strict order; first match wins (deterministic).
    ( c01_missing_or_unclear_reason(MissingCritical, UnclearCritical, R) ->
        Decision = refuse_to_decide,
        Reasons = [R]
    ; c02_jurisdiction_unclear ->
        Decision = refuse_to_decide,
        Reasons = [c02_jurisdiction_unclear]
    ; c03_veto_overconfident_approval(Primary) ->
        Decision = veto,
        Reasons = [c03_veto_approval_without_minimum_docs]
    ; c04_veto_fully_automated_high_severity(Primary) ->
        Decision = veto,
        Reasons = [c04_veto_fully_automated_high_severity]
    ; c05_refuse_if_primary_is_refuse(Primary) ->
        Decision = refuse_to_decide,
        Reasons = [c05_primary_refused]
    ; c06_confirm_default ->
        Decision = confirm,
        Reasons = [c06_confirm]
    ).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Constraint rules
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% C01: Missing OR unclear critical evidence => refuse
% Return a reason id that matches the actual driver for audit semantics.
c01_missing_or_unclear_reason(Missing, Unclear, ReasonId) :-
    ( Missing \= [] ->
        ReasonId = c01_missing_critical_evidence
    ; Unclear \= [] ->
        ReasonId = c01_unclear_critical_evidence
    ).

% C02: Jurisdiction unclear => refuse to decide
c02_jurisdiction_unclear :-
    main:wm(jurisdiction_unclear).

% C03: If primary says approve but any required governance docs are missing => veto
% (docs missing are represented in working memory as *_missing)
c03_veto_overconfident_approval(approve) :-
    ( main:wm(dpia_missing)
    ; main:wm(oversight_missing)
    ; main:wm(appeals_missing)
    ; main:wm(explain_missing)
    ; main:wm(bias_missing)
    ; main:wm(security_missing)
    ; main:wm(monitoring_missing)
    ; main:wm(supplier_missing)
    ), !.
c03_veto_overconfident_approval(_) :- fail.

% C04: Fully automated + high severity cannot be authorised here => veto
c04_veto_fully_automated_high_severity(Primary) :-
    Primary \= refuse_to_decide,
    main:wm(fully_automated),
    main:wm(high_severity).

% C05: If primary already refused, constraint also refuses
c05_refuse_if_primary_is_refuse(refuse_to_decide).

% C06: Default confirm
c06_confirm_default.
