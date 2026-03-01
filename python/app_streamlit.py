# python/app_streamlit.py
from __future__ import annotations

import json
from datetime import datetime, timezone

import streamlit as st

from run_inference import (
    write_temp_facts_file,
    call_prolog,
    write_audit_log,
    PROJECT_ROOT,
    PROLOG_DIR,
)
from explain import call_prolog_unmet_for_approve, explanation_completeness_score

# -----------------------------
# 0) Page config
# -----------------------------
st.set_page_config(
    page_title="Governance Decision Support",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# 1) Professional styling + responsive fixes
# -----------------------------
st.markdown(
    """
<style>
/* ===========================
   Blue + White Professional (v4)
   Fixes:
   - Restore Streamlit header so sidebar toggle works
   - Remove heading/copy-link icon + stop layout shift
   - Remove "search input" look in selectbox closed state
   - Blue highlight behind header description text only
   =========================== */

:root{
  --bg: #FFFFFF;
  --sidebar-bg: #F5F7FB;
  --card-bg: #FFFFFF;

  --text: #0F172A;
  --muted: #475569;

  --primary: #2563EB;
  --primary-ink: #1D4ED8;
  --primary-soft: rgba(37, 99, 235, 0.14);
  --primary-soft-2: rgba(37, 99, 235, 0.10);

  --border: rgba(15, 23, 42, 0.10);
  --shadow: 0 10px 28px rgba(15, 23, 42, 0.07);
  --radius: 14px;
}

/* ===========================
   1) RESTORE STREAMLIT HEADER (sidebar toggle)
   =========================== */
header[data-testid="stHeader"]{
  display: block !important;
  visibility: visible !important;
  height: auto !important;
  background: var(--bg) !important;
  border-bottom: 1px solid rgba(15,23,42,0.06) !important;
}

/* Ensure toolbar is visible (contains sidebar toggle in some builds) */
div[data-testid="stToolbar"]{
  display: flex !important;
  visibility: visible !important;
}
[data-testid="stDecoration"]{
  display: block !important;
  visibility: visible !important;
}

/* ===========================
   2) BASE PAGE THEME
   =========================== */
html, body, .stApp, [data-testid="stAppViewContainer"]{
  background: var(--bg) !important;
  color: var(--text) !important;
}

.block-container{
  padding-top: 1.25rem;
  padding-bottom: 2.2rem;
  max-width: 1400px;
  margin: 0 auto;
}

h1, h2, h3, h4{
  color: var(--text) !important;
  letter-spacing: -0.01em;
}
h3{ margin-top: 0.2rem; }

a, a:visited{ color: var(--primary) !important; }

/* ===========================
   3) REMOVE HEADING ANCHOR / COPY ICON (and layout shift)
   =========================== */
/* The icon element */
a[data-testid="stMarkdownHeadingAnchor"]{
  display: none !important;
}
/* The container that sometimes reserves space */
div[data-testid="stHeadingWithActionElements"]{
  column-gap: 0 !important;
}
div[data-testid="stHeadingWithActionElements"] > div:last-child{
  display: none !important;
  width: 0 !important;
}

/* ===========================
   4) SIDEBAR THEME
   =========================== */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div{
  background: var(--sidebar-bg) !important;
}
section[data-testid="stSidebar"] .block-container{
  padding-top: 1.0rem;
  padding-bottom: 1.2rem;
}

/* Keep collapsed control visible if sidebar is closed */
div[data-testid="stSidebarCollapsedControl"]{
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 999999 !important;
}
div[data-testid="stSidebarCollapsedControl"] button{
  background: rgba(37, 99, 235, 0.12) !important;
  border: 1px solid rgba(37, 99, 235, 0.28) !important;
  border-radius: 10px !important;
}

/* ===========================
   5) CARDS / DIVIDERS
   =========================== */
.card{
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius);
  padding: 1.05rem 1.15rem;
  box-shadow: var(--shadow);
  overflow: visible;
}
.card, .card *{ color: var(--text) !important; }

.card div[style*="opacity"]{
  opacity: 1 !important;
  color: var(--muted) !important;
}

.hr{
  height: 1px;
  background: rgba(15, 23, 42, 0.10);
  margin: 0.9rem 0;
}

/* Header row */
.header-row{
  display:flex;
  justify-content: space-between;
  align-items:flex-start;
  gap: 1rem;
  flex-wrap: wrap;
}
.header-right{
  text-align:right;
  margin-left:auto;
  padding-top:0.55rem;
  padding-right:0.15rem;
}

/* Outcome card */
.outcome-row{
  display:flex;
  justify-content: space-between;
  align-items:center;
  gap:1rem;
  flex-wrap:wrap;
}
.outcome-left{ flex:1 1 auto; min-width:260px; }
.outcome-right{ flex:0 0 auto; text-align:right; }
.outcome-title{ font-size:1.18rem; font-weight:800; }
.outcome-sub{ margin-top:0.2rem; color: var(--muted) !important; }

/* ===========================
   6) BLUE HIGHLIGHT BEHIND HEADER DESCRIPTION ONLY
   NOTE: You should add class="header-desc" to your description div for perfect targeting.
   This also includes a safe fallback that targets your opacity description line.
   =========================== */
.header-desc{
  background: var(--primary-soft-2) !important;
  border: 1px solid rgba(37, 99, 235, 0.18) !important;
  border-radius: 12px !important;
  padding: 0.65rem 0.75rem !important;
}

/* Fallback: if you don't add .header-desc */
.header-card div[style*="opacity"]{
  background: var(--primary-soft-2) !important;
  border: 1px solid rgba(37, 99, 235, 0.18) !important;
  border-radius: 12px !important;
  padding: 0.65rem 0.75rem !important;
}

/* ===========================
   7) PILLS / BUTTONS / TABS / PROGRESS
   =========================== */
.pill{
  display:inline-block;
  padding: 0.30rem 0.74rem;
  border-radius: 999px;
  font-size: 0.88rem;
  line-height: 1.2;
  margin-right: 0.4rem;
  margin-bottom: 0.35rem;
  white-space: nowrap;
  background: var(--primary-soft) !important;
  border: 1px solid rgba(37, 99, 235, 0.35) !important;
  color: var(--primary-ink) !important;
  font-weight: 650;
}
.pill-ok   { background: rgba(22,163,74,0.12) !important; border-color: rgba(22,163,74,0.32) !important; color: #166534 !important; }
.pill-warn { background: rgba(245,158,11,0.12) !important; border-color: rgba(245,158,11,0.32) !important; color: #92400E !important; }
.pill-bad  { background: rgba(239,68,68,0.12) !important; border-color: rgba(239,68,68,0.32) !important; color: #991B1B !important; }

.stButton > button{
  background: var(--primary) !important;
  color:#FFF !important;
  border:1px solid var(--primary) !important;
  border-radius: 10px !important;
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.20);
  font-weight:700;
}
.stButton > button:hover{ filter: brightness(0.96); }

div[data-testid="stTabs"] [data-baseweb="tab-list"]{
  gap:0.25rem;
  flex-wrap:wrap;
}
div[data-testid="stTabs"] [data-baseweb="tab"]{
  padding:0.35rem 0.65rem;
  border-radius:10px;
}
div[data-testid="stTabs"] button[aria-selected="true"]{
  color: var(--primary) !important;
  font-weight:700;
}
div[data-testid="stTabs"] button[aria-selected="true"]::after{
  background-color: var(--primary) !important;
}

div[role="progressbar"] > div{
  background-color: var(--primary) !important;
}

/* ===========================
   8) INPUTS + SELECTBOX (remove “search” look)
   =========================== */
/* Text inputs */
input, textarea{
  background:#FFF !important;
  color: var(--text) !important;
  border: 1px solid rgba(15, 23, 42, 0.16) !important;
  border-radius: 10px !important;
  padding: 0.55rem 0.70rem !important;
}

/* Select outer */
[data-baseweb="select"] > div{
  background:#FFF !important;
  border: 1px solid rgba(15, 23, 42, 0.16) !important;
  border-radius: 12px !important;
  min-height: 44px !important;
  padding-left: 10px !important;
  padding-right: 10px !important;
}

/* Center align the selected value area */
[data-baseweb="select"] div[role="combobox"]{
  min-height: 44px !important;
  display:flex !important;
  align-items:center !important;
}

/* Hide the internal search input visually, but KEEP layout stable */
[data-baseweb="select"] input{
  opacity: 0 !important;
  height: 0 !important;
  min-height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  border: 0 !important;
}

/* Focus ring */
input:focus, textarea:focus,
[data-baseweb="select"] > div:focus-within{
  outline:none !important;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18) !important;
  border-color: rgba(37, 99, 235, 0.55) !important;
}

::placeholder{ color: rgba(71, 85, 105, 0.75) !important; }

/* Labels */
[data-testid="stWidgetLabel"] p{
  color: var(--text) !important;
  font-weight: 650 !important;
}

/* Your sidebar headings */
.sidebar-title{
  font-size:1.05rem;
  font-weight:750;
  margin:0.25rem 0;
  color: var(--text) !important;
}
.sidebar-section{
  font-size:0.92rem;
  font-weight:750;
  opacity:0.92;
  margin-top:0.35rem;
  color: var(--text) !important;
}

/* ===========================
   9) RESPONSIVE
   =========================== */
@media (max-width: 1100px){
  div[data-testid="column"]{
    width:100% !important;
    flex:1 1 100% !important;
  }
  .block-container{ padding-left:1rem; padding-right:1rem; }
}
@media (max-width: 900px){
  .outcome-right{
    width:100%;
    text-align:left;
    margin-left:0;
  }
}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# 2) Helper functions (UI only)
# -----------------------------
YES_NO_UNCLEAR = ["yes", "no", "unclear"]
IMPACT = ["advisory", "human_supported", "fully_automated"]
SEVERITY = ["low", "medium", "high"]

# Mirror the Python validation "critical" list (UI-only visibility; no inference).
CRITICAL_FIELDS = [
    "uk_public_sector_applicability",
    "decision_impact",
    "consequence_severity",
    "dpia_exists",
    "human_oversight_plan",
    "appeals_mechanism",
    "explainability_provision",
    "bias_fairness_assessment",
    "security_controls",
    "monitoring_incident_response",
    "supplier_transparency",
]


def render_html(html: str):
    """
    Render raw HTML safely in Streamlit markdown without it being interpreted as a code block.
    Streamlit/Markdown treats lines with 4+ leading spaces as code, so we strip left padding.
    """
    html = "\n".join(line.lstrip() for line in html.splitlines())
    st.markdown(html, unsafe_allow_html=True)

def _pretty(v: str) -> str:
    """Human-friendly display for dropdown values (keeps underlying atoms unchanged)."""
    return v.replace("_", " ").title()

def _pretty_label(value: str) -> str:
    """
    UI-only label formatting.
    Keeps Prolog atoms unchanged, but presents them professionally.
    Examples:
      approve_with_safeguards -> Approve with safeguards
      refuse_to_decide -> Refuse to decide
      human_supported -> Human supported
    """
    if value is None:
        return "—"
    return value.replace("_", " ").strip().capitalize()


def _pill(label: str, variant: str = "neutral") -> str:
    cls = {
        "ok": "pill pill-ok",
        "warn": "pill pill-warn",
        "bad": "pill pill-bad",
        "neutral": "pill pill-neutral",
    }.get(variant, "pill pill-neutral")

    safe_label = label.replace("\n", " ")
    return f'<span class="{cls}">{safe_label}</span>'


def _constraint_badge_html(constraint: str, variant: str) -> str:
    return _pill(f"Constraint: {_pretty_label(constraint)}", variant)


def _decision_variant(primary: str, constraint: str) -> tuple[str, str]:
    if constraint == "veto":
        return "bad", "Vetoed by governance constraints"
    if constraint == "refuse_to_decide":
        return "warn", "Refused due to insufficient/invalid authority"
    if primary == "reject":
        return "bad", "Rejected"
    if primary == "escalate":
        return "warn", "Escalation required"
    if primary == "approve_with_safeguards":
        return "warn", "Approval possible with mandatory safeguards"
    if primary == "approve":
        return "ok", "Approved (low risk, minimum governance met)"
    return "neutral", "Outcome produced"


def _collect_unknowns(facts: dict) -> list[str]:
    return sorted([k for k, v in facts.items() if v == "unclear"])


def _collect_unclear_critical(facts: dict) -> list[str]:
    return sorted([k for k in CRITICAL_FIELDS if facts.get(k) == "unclear"])


def _download_json_button(label: str, payload: dict, filename: str):
    st.download_button(
        label=label,
        data=json.dumps(payload, indent=2),
        file_name=filename,
        mime="application/json",
        use_container_width=True,
    )


# -----------------------------
# 3) Header
# -----------------------------
header_html = f"""
<div class="card header-card">
  <div class="header-row">
    <div style="flex: 1 1 520px;">
      <div style="font-size:1.55rem; font-weight:780;">
        Governance-Legitimate AI Deployment Decision Support
      </div>
      <div style="opacity:0.86; margin-top:0.25rem; line-height:1.35;">
        Deterministic rule-based expert system for assessing whether institutional authority can be legitimately exercised via AI-assisted decision-making.
        This interface performs <b>no inference</b>: it only collects facts, runs Prolog, and displays an audit-ready explanation.
      </div>
    </div>

    <div class="header-right" style="flex: 0 1 360px;">
      <div>
        {_pill("Audit-ready", "neutral")}
        {_pill("Deterministic", "neutral")}
        {_pill("Conservative", "neutral")}
      </div>
      <div style="opacity:0.75; margin-top:0.25rem; font-size:0.92rem; line-height:1.25;">
        Prolog Authoritative · Python Orchestration Only
      </div>
    </div>
  </div>
</div>
"""

render_html(header_html)

st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

# -----------------------------
# 4) Sidebar: Run metadata + Inputs
# -----------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">Run setup</div>', unsafe_allow_html=True)
    st.caption("Inputs are categorical. Use **unclear** when evidence is unavailable (structured uncertainty).")

    reviewer = st.text_input("Reviewer (Metadata Only)", placeholder="e.g., Governance Analyst")
    external_run_id = st.text_input("Run ID (Metadata Only)", placeholder="e.g., GOV-2026-01-25-001")

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Input Facts</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Deployment Context</div>', unsafe_allow_html=True)
    uk_public_sector_applicability = st.selectbox(
        "UK Public-Sector Applicability", YES_NO_UNCLEAR, index=0, format_func=_pretty
    )
    decision_impact = st.selectbox("Decision Impact", IMPACT, index=0, format_func=_pretty)
    consequence_severity = st.selectbox("Consequence Severity", SEVERITY, index=0, format_func=_pretty)

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Data & System Profile</div>', unsafe_allow_html=True)
    personal_data_usage = st.selectbox("Personal Data Usage", YES_NO_UNCLEAR, index=0, format_func=_pretty)
    special_category_data = st.selectbox("Special Category Data", YES_NO_UNCLEAR, index=1, format_func=_pretty)
    biometric_processing = st.selectbox("Biometric Processing", YES_NO_UNCLEAR, index=1, format_func=_pretty)
    childrens_data = st.selectbox("Children’s Data", YES_NO_UNCLEAR, index=1, format_func=_pretty)

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Governance & Assurance</div>', unsafe_allow_html=True)
    dpia_exists = st.selectbox("DPIA Exists", YES_NO_UNCLEAR, index=0, format_func=_pretty)
    human_oversight_plan = st.selectbox("Human Oversight Plan", YES_NO_UNCLEAR, index=0, format_func=_pretty)
    appeals_mechanism = st.selectbox("Appeals & Recourse Mechanisms", YES_NO_UNCLEAR, index=0, format_func=_pretty)
    explainability_provision = st.selectbox("Explainability Provision", YES_NO_UNCLEAR, index=0, format_func=_pretty)
    bias_fairness_assessment = st.selectbox("Bias & Fairness Assessment", YES_NO_UNCLEAR, index=0, format_func=_pretty)
    security_controls = st.selectbox("Security Controls", YES_NO_UNCLEAR, index=0, format_func=_pretty)
    monitoring_incident_response = st.selectbox("Monitoring & Incident Response", YES_NO_UNCLEAR, index=0, format_func=_pretty)
    supplier_transparency = st.selectbox("Supplier Transparency", YES_NO_UNCLEAR, index=0, format_func=_pretty)

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    facts = {
        "uk_public_sector_applicability": uk_public_sector_applicability,
        "decision_impact": decision_impact,
        "consequence_severity": consequence_severity,
        "personal_data_usage": personal_data_usage,
        "special_category_data": special_category_data,
        "biometric_processing": biometric_processing,
        "childrens_data": childrens_data,
        "dpia_exists": dpia_exists,
        "human_oversight_plan": human_oversight_plan,
        "appeals_mechanism": appeals_mechanism,
        "explainability_provision": explainability_provision,
        "bias_fairness_assessment": bias_fairness_assessment,
        "security_controls": security_controls,
        "monitoring_incident_response": monitoring_incident_response,
        "supplier_transparency": supplier_transparency,
    }

    unknown_fields = _collect_unknowns(facts)
    unclear_critical = _collect_unclear_critical(facts)

    st.markdown('<div class="sidebar-title">Evidence Completeness</div>', unsafe_allow_html=True)
    st.caption("UI-only uncertainty signals; inference is performed in Prolog only.")
    st.write(f"Unknown / Unclear Fields: **{len(unknown_fields)} / {len(facts)}**")
    st.write(f"Critical Fields Marked Unclear: **{len(unclear_critical)} / {len(CRITICAL_FIELDS)}**")

    run_btn = st.button("Run expert system", use_container_width=True)

# -----------------------------
# 5) Main layout
# -----------------------------
left, right = st.columns([1.15, 1.85], gap="large")

for k, v in {
    "last_result": None,
    "last_run_id": None,
    "last_inputs": None,
    "last_unmet": None,
    "last_score": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------------
# 6) Execute run (Prolog authoritative)
# -----------------------------
if run_btn:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    facts_path = write_temp_facts_file(facts, run_id)
    result = call_prolog(
        main_pl=PROLOG_DIR / "main.pl",
        constraints_pl=PROLOG_DIR / "constraints.pl",
        facts_pl=facts_path,
    )

    primary = result.get("primary_decision")
    constraint = result.get("constraint_decision")

    unmet = []
    if constraint != "refuse_to_decide" and primary != "refuse_to_decide":
        unmet = call_prolog_unmet_for_approve(
            project_root=PROJECT_ROOT,
            main_pl=PROLOG_DIR / "main.pl",
            constraints_pl=PROLOG_DIR / "constraints.pl",
            facts_pl=facts_path,
        )

    score = explanation_completeness_score(
        missing_critical=result.get("missing_critical", []),
        fired_rules=result.get("fired_rules", []),
        unmet_for_approve=unmet,
        refused=(constraint == "refuse_to_decide" or primary == "refuse_to_decide"),
    )

    result["unmet_for_approve"] = unmet
    result["explanation_completeness_score"] = score

    result["_validation"] = {
        "missing_critical": result.get("missing_critical", []),
        "unclear_critical": _collect_unclear_critical(facts),
    }

    metadata = {"reviewer": reviewer, "external_run_id": external_run_id}
    logged_inputs = dict(facts)
    logged_inputs["_meta"] = metadata

    write_audit_log(run_id, logged_inputs, result)

    st.session_state.last_result = result
    st.session_state.last_run_id = run_id
    st.session_state.last_inputs = logged_inputs
    st.session_state.last_unmet = unmet
    st.session_state.last_score = score

result = st.session_state.last_result
run_id = st.session_state.last_run_id
logged_inputs = st.session_state.last_inputs
unmet = st.session_state.last_unmet
score = st.session_state.last_score

# -----------------------------
# 7) Left panel
# -----------------------------
with left:
    st.markdown("### Governance outcome")

    if result is None:
        st.markdown(
            """
<div class="card header-card">
  <div style="font-size:1.05rem; font-weight:700;">Ready</div>
  <div style="opacity:0.86; margin-top:0.35rem; line-height:1.35;">
    Select input facts in the sidebar, then run the expert system.
    Outputs are conservative governance recommendations with traceable justification.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        primary = result.get("primary_decision")
        constraint = result.get("constraint_decision")
        variant, subtitle = _decision_variant(primary, constraint)

        primary_ui = _pretty_label(primary)

        st.markdown(
            f"""
    <div class="card">
    <div class="outcome-row">
        <div class="outcome-left">
        <div class="outcome-title">{primary_ui}</div>
        <div class="outcome-sub">{subtitle}</div>
        </div>
        <div class="outcome-right">
        {_constraint_badge_html(constraint, variant)}
        </div>
    </div>
    </div>
    """,
                unsafe_allow_html=True,
            )


        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown("### Run validity")

        missing_critical = result.get("missing_critical", [])
        unknowns = _collect_unknowns({k: v for k, v in logged_inputs.items() if k != "_meta"}) if logged_inputs else []
        unclear_crit_ui = _collect_unclear_critical({k: v for k, v in logged_inputs.items() if k != "_meta"}) if logged_inputs else []

        refused = (constraint == "refuse_to_decide") or (primary == "refuse_to_decide")

        st.markdown(
            """
<div class="card header-card">
  <div style="display:flex; gap:0.55rem; flex-wrap:wrap;">
    """
            + _pill("Inputs collected", "neutral")
            + _pill("Deterministic inference", "neutral")
            + _pill("JSON audit output", "neutral")
            + (_pill("Refusal = valid outcome", "neutral") if refused else "")
            + """
  </div>
  <div style="margin-top:0.65rem; opacity:0.92; line-height:1.45;">
    <div>Missing critical fields (Prolog): <b>{}</b></div>
    <div>Unclear fields (UI): <b>{}</b></div>
    <div>Critical fields marked unclear (UI): <b>{}</b></div>
  </div>
</div>
""".format(len(missing_critical), len(unknowns), len(unclear_crit_ui)),
            unsafe_allow_html=True,
        )

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown("### Explanation completeness")
        st.progress(min(max(score, 0), 100) / 100)
        st.caption(f"{score} / 100 (transparent heuristic; not a confidence score)")

# -----------------------------
# 8) Right panel: Tabs
# -----------------------------
with right:
    st.markdown("### Diagnostics & explanations")

    if result is None:
        st.markdown(
            """
<div class="card header-card">
  <div style="font-weight:700;">No run yet</div>
  <div style="opacity:0.86; margin-top:0.35rem; line-height:1.35;">
    Run the system to view: fired rules, reasons, counterfactual requirements, and audit export.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        tab_summary, tab_trace, tab_why_not, tab_audit = st.tabs(
            ["Summary", "Explanation trace", "Why-not (approval)", "Audit & export"]
        )

        primary = result.get("primary_decision")
        constraint = result.get("constraint_decision")

        with tab_summary:
            st.markdown("#### Key outputs")
            col_a, col_b = st.columns([1, 1], gap="large")
            with col_a:
                st.markdown(
                    f"""
<div class="card header-card">
  <div style="opacity:0.82;">Primary decision</div>
<div style="font-size:1.12rem; font-weight:800; margin-top:0.15rem;">{_pretty_label(primary)}</div>
</div>
""",
                    unsafe_allow_html=True,
                )
            with col_b:
                st.markdown(
                    f"""
<div class="card header-card">
  <div style="opacity:0.82;">Constraint layer</div>
<div style="font-size:1.12rem; font-weight:800; margin-top:0.15rem;">{_pretty_label(constraint)}</div>
</div>
""",
                    unsafe_allow_html=True,
                )

            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            st.markdown("#### Constraint reasons")
            cr = result.get("constraint_reasons", [])
            if cr:
                for line in cr:
                    st.write(f"- {line}")
            else:
                st.write("No constraint reasons returned.")

            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            st.markdown("#### Critical uncertainty (UI-only)")
            ui_unclear_crit = result.get("_validation", {}).get("unclear_critical", [])
            if ui_unclear_crit:
                st.warning("Some CRITICAL fields were marked 'unclear' (structured uncertainty):")
                for k in ui_unclear_crit:
                    st.write(f"- `{k}`")
            else:
                st.success("No critical fields marked 'unclear' (UI-only).")

            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            st.markdown("#### Mandatory safeguards (machine-readable)")
            saf = result.get("mandatory_safeguards", [])
            if saf:
                st.warning("Approval is only legitimate if these safeguards are implemented:")
                for s in saf:
                    st.write(f"- `{s}`")
            else:
                st.success("No mandatory safeguards returned for this outcome.")

            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            st.markdown("#### Missing critical (Prolog)")
            mc = result.get("missing_critical", [])
            if mc:
                st.warning("Critical evidence missing — refusal under uncertainty may occur (and is a valid governance outcome).")
                for m in mc:
                    st.write(f"- `{m}`")
            else:
                st.success("No critical fields missing (Prolog).")

        with tab_trace:
            st.markdown("#### Fired Rules (Ordered)")
            fired = result.get("fired_rules", [])
            if fired:
                for r in fired:
                    st.write(f"- `{r}`")
            else:
                st.write("No fired rules returned.")

            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            st.markdown("#### Reasons (Natural Language)")
            reasons = result.get("reasons", [])
            if reasons:
                for rr in reasons:
                    st.write(f"- {rr}")
            else:
                st.write("No reasons returned.")

        with tab_why_not:
            st.markdown("#### Counterfactual Requirements for Approval")
            st.caption(
                "This is a backward-chaining query: it lists conditions that would need to hold for `approve` to be justified in this case."
            )

            if constraint == "refuse_to_decide" or primary == "refuse_to_decide":
                st.info(
                    "The system refused to decide due to insufficient/invalid authority. "
                    "In this state, counterfactual approval conditions are intentionally withheld. "
                    "The correct next step is to provide missing evidence and/or clarify jurisdiction."
                )
            else:
                if unmet:
                    st.warning("Approval is not currently justified. Unmet requirements:")
                    for req in unmet:
                        st.write(f"- `{req}`")
                else:
                    st.success("All conditions for `approve` are currently satisfied.")

        with tab_audit:
            st.markdown("#### Audit Identifiers")
            st.write("**Internal run_id:**", run_id)
            meta = (logged_inputs or {}).get("_meta", {})
            st.write("**Reviewer (metadata):**", meta.get("reviewer") or "—")
            st.write("**External run id (metadata):**", meta.get("external_run_id") or "—")

            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            st.markdown("#### Export JSON")

            export_col1, export_col2 = st.columns([1, 1], gap="large")
            with export_col1:
                _download_json_button(
                    "Download inputs (JSON)",
                    payload=logged_inputs,
                    filename=f"{run_id}_inputs.json",
                )
            with export_col2:
                _download_json_button(
                    "Download result (JSON)",
                    payload=result,
                    filename=f"{run_id}_result.json",
                )

            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            st.markdown("#### Raw result preview")
            st.code(json.dumps(result, indent=2), language="json")
