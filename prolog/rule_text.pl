% prolog/rule_text.pl
% Human-readable short reasons for each rule id.
% Keep these stable for audit logs.

:- module(rule_text, [rule_reason/2]).

rule_reason(r01, "UK public-sector applicability confirmed.").
rule_reason(r02, "Jurisdiction unclear or outside scope: system lacks authority to decide.").

rule_reason(r03, "High consequence severity triggers stronger governance needs.").
rule_reason(r04, "Fully automated decision-making increases legitimacy risk.").

% r05 merged data/system profile flags
rule_reason(r05, "Data/system profile indicates one or more of: personal data, special category data, biometric processing, or children's data; heightened governance attention required.").

% r06 now covers: missing critical OR unclear critical OR jurisdiction unclear
rule_reason(r06, "Refusal triggered: missing or unclear critical evidence, or jurisdiction unclear (refusal under uncertainty).").

rule_reason(r07, "Reject triggered: fully automated decision-making with high consequence severity.").
rule_reason(r08, "Safeguards required: fully automated decision-making (non-high severity) cannot be approved without additional controls.").

rule_reason(r09, "DPIA exists and is completed.").
rule_reason(r10, "DPIA missing or not completed.").

rule_reason(r11, "Human oversight plan exists.").
rule_reason(r12, "Human oversight plan missing.").

rule_reason(r13, "Appeals and recourse mechanisms exist.").
rule_reason(r14, "Appeals and recourse missing.").

rule_reason(r15, "Explainability provision exists.").
rule_reason(r16, "Explainability provision missing.").

rule_reason(r17, "Bias/fairness assessment exists.").
rule_reason(r18, "Bias/fairness assessment missing.").

rule_reason(r19, "Security controls documented.").
rule_reason(r20, "Security controls missing.").

rule_reason(r21, "Monitoring & incident response exists.").
rule_reason(r22, "Monitoring & incident response missing.").

% r23 merged supplier yes/no handling
rule_reason(r23, "Supplier transparency status recorded (present or missing).").

% approval moved to r24
rule_reason(r24, "All minimum governance conditions met for low-risk approval.").

% default escalation
rule_reason(r25, "Default escalation: jurisdiction confirmed but approval/rejection conditions not met; senior review required.").

% Constraint-layer reason text (for audit display)
rule_reason(c01_missing_critical_evidence, "Constraint: missing critical evidence => refuse to decide.").
rule_reason(c01_unclear_critical_evidence, "Constraint: unclear critical evidence => refuse to decide.").
rule_reason(c02_jurisdiction_unclear, "Constraint: jurisdiction unclear => refuse to decide.").
rule_reason(c03_veto_approval_without_minimum_docs, "Constraint: vetoed approval because minimum governance documentation is missing.").
rule_reason(c04_veto_fully_automated_high_severity, "Constraint: vetoed because fully automated + high severity is not legitimate for deployment decision.").
rule_reason(c05_primary_refused, "Constraint: primary decision refused; constraint also refuses.").
rule_reason(c06_confirm, "Constraint: decision issuance confirmed.").
