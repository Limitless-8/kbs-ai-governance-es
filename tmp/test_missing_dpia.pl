% tmp/test_missing_dpia.pl
:- dynamic main:input/2.

main:input(uk_public_sector_applicability, yes).
main:input(decision_impact, advisory).
main:input(consequence_severity, low).

% omit dpia_exists entirely => critical missing
main:input(human_oversight_plan, yes).
main:input(appeals_mechanism, yes).
main:input(explainability_provision, yes).
main:input(bias_fairness_assessment, yes).
main:input(security_controls, yes).
main:input(monitoring_incident_response, yes).
main:input(supplier_transparency, yes).
