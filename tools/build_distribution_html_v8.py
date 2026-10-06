"""Build V8 of the internal Attrition distribution deck from frozen V7.

V8 deliberately treats V7 as an immutable source.  It changes the reader
order, navigation, overview, and the comparable promotion-cohort visual without
rewriting V7's validated source transformations.
"""

from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import re
import shutil
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v7.html"
SOURCE_MANIFEST = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7-manifest.json"
COMPARABLE_PROMOTION_EVIDENCE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.time-since-last-promotion-comparable-cohorts-evidence-20260924.json"
)
COMPARABLE_PROMOTION_AUTHORIZATION = ROOT / "config" / "attrition_v7_internal_analysis_authorization_20260917.json"
IOS_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v8.ios-movement-reasons-trailing-12m-evidence-20260923.json"
AUTHORIZATION = ROOT / "config" / "attrition_v8_internal_analysis_authorization_20260923.json"
COLOR_POLICY = ROOT / "config" / "attrition_color_policy_v8.json"
COLOR_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v8.attrition-color-reference-evidence-20260924.json"
SIX_MONTH_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v3.six-month-attrition-evidence-20260914.json"
ANNUAL_HISTORY_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.nav28-39-direct-annual-attrition-evidence-20260917.json"
APPLICATION_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.application-trailing-12m-august-attrition-evidence-20260918.json"
JOB_FAMILY_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.job-family-august-trailing-12m-attrition-evidence-20260922.json"
REHIRE_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.rehire-comparison-august-trailing-12m-evidence-20260922.json"
CTO_ORG_EVIDENCE = ROOT / "output" / "distribution" / "json" / "engineering-cto-org-split-annual-attrition-evidence-20260917.json"
LAYERS_EVIDENCE = ROOT / "output" / "distribution" / "json" / "layers-from-ceo-annual-attrition-evidence-20260921.json"
QVOICE_HEARTBEAT_EVIDENCE = ROOT / "output" / "distribution" / "json" / "qvoice-2026-august-post-survey-ytd-heartbeat-relative-sign-attrition-evidence-20260923.json"
QVOICE_RESPONSE_GROUP_EVIDENCE = ROOT / "output" / "distribution" / "json" / "qvoice-favorable-unfavorable-question-attrition-evidence-20260923.json"
QVOICE_YTD_GROUP_EVIDENCE = ROOT / "output" / "distribution" / "json" / "qvoice-2026-ytd-attrition-evidence-20260917.json"
QVOICE_RETENTION_THEME_EVIDENCE = ROOT / "output" / "distribution" / "json" / "qvoice-retention-theme-august-trailing-12m-attrition-evidence-20260922.json"
TENURE_PANEL_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.time-at-detailed-level-time-in-role-august-trailing-12m-evidence-20260920.json"
PROMOTION_TRACK_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.promotion-track-trailing-12m-evidence-20260918.json"
PROMOTION_GRADE_TOP10_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.promotion-grade-top10-trailing-12m-evidence-20260918.json"
MANAGER_CONTEXT_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.nav38-plus-august-trailing-12m-evidence-20260921.json"
DIRECT_TEAM_SPAN_EVIDENCE = ROOT / "output" / "distribution" / "json" / "direct-team-span-annual-attrition-evidence-20260923.json"
COMMUTE_ALL_ELIGIBLE_EVIDENCE = ROOT / "output" / "distribution" / "json" / "commute-distance-all-eligible-six-month-attrition-evidence-20260917.json"
COMMUTE_ONSITE_EVIDENCE = ROOT / "output" / "distribution" / "json" / "commute-distance-onsite-six-month-attrition-evidence-20260917.json"
ACQUISITION_EVIDENCE_BUILDER = ROOT / "tools" / "build_acquisition_entry_evidence.py"
ACQUISITION_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v8.acquisition-entry-evidence-20260929.json"
OUTPUT_DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v8.html"
OUTPUT_MANIFEST = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v8-manifest.json"
BACKUP_DIRECTORY = OUTPUT_DECK.parent / "v8-backups"
BACKUP_REGISTRY = BACKUP_DIRECTORY / "backups.json"
HISTORICAL_VERSION_REGISTRY = BACKUP_DIRECTORY / "historical-v1-v7" / "history.json"


STAGE_RE = re.compile(
    r'(?P<stage><div\s+class="slide-stage"\s+id="(?P<id>[^"]+)"[^>]*>.*?)(?=\n\s*<div\s+class="slide-stage"|\n\s*<div\s+class="nav-ctrl")',
    re.S,
)


# V8 owns its presentation precision independently of V7.  The source deck
# remains immutable: V8 formats only reader-facing text, titles, accessibility
# labels, and dynamic chart content in its generated output.
V7_NUMERIC_DISPLAY_FORMATTER_MARKER = "<!-- V7 DISPLAY NUMBER FORMATTER -->"
V8_NUMERIC_DISPLAY_FORMATTER_MARKER = "<!-- V8 DISPLAY NUMBER FORMATTER -->"
V7_DYNAMIC_FORMATTER_BLOCK = re.compile(
    rf"\s*{re.escape(V7_NUMERIC_DISPLAY_FORMATTER_MARKER)}\s*<script\s+data-v7-display-number-formatter=\"true\">.*?</script>\s*",
    re.I | re.S,
)
DISPLAY_NUMBER_TOKEN = re.compile(
    r"(?<![\w,.-])(?P<number>-?(?:\d{1,3}(?:,\d{3})+|\d+)\.\d+)(?P<suffix>%?)(?![\w,.-])"
)
PROTECTED_HTML_BLOCK = re.compile(
    r"(<(?:script|style|code|pre|textarea)\b[^>]*>.*?</(?:script|style|code|pre|textarea)\s*>)",
    re.I | re.S,
)
RATE_PRECISION_BLOCK = re.compile(
    r'(<[a-z][\w:-]*\b[^>]*\bdata-v8-(?:rate|percent)-precision="one-decimal"[^>]*>.*?</[a-z][\w:-]*\s*>)',
    re.I | re.S,
)
READER_PROTECTED_BLOCK = re.compile(
    r'(<(?:script|style|code|pre|textarea)\b[^>]*>.*?</(?:script|style|code|pre|textarea)\s*>|'
    r'[a-z][\w:-]*\b[^>]*\bdata-v8-(?:rate|percent)-precision="one-decimal"[^>]*>.*?</[a-z][\w:-]*\s*>)',
    re.I | re.S,
)
HTML_TAG_TOKEN = re.compile(r"(<[^>]+>)")
DISPLAY_ATTRIBUTE_TOKEN = re.compile(
    r'(?P<prefix>\b(?:title|aria-label|aria-description|aria-valuetext|alt)=\")(?P<value>[^\"]*)(?P<suffix>\")',
    re.I,
)
RATE_PILL_TOKEN = re.compile(
    r'(?P<open><(?P<tag>span|strong|b)\b(?P<attrs>[^>]*\bclass="[^"]*(?:rate|attrition|pill)[^"]*"[^>]*)>)'
    r'(?P<value>\s*(?P<rate>-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)%\*?\s*)'
    r'(?P<close></(?P=tag)>)',
    re.I,
)
RATE_CLASS_TOKEN = re.compile(r"\battr-(?:low|mid|high|unavailable)\b|\bv8-reference-unavailable\b")
RATE_VALUE_TOKEN = re.compile(r"(?P<rate>-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)%")
PANEL_HEADING_TOKEN = re.compile(r'<div\s+class="v6-panel-heading"[^>]*>\s*<span>(?P<label>.*?)</span>', re.I | re.S)
BAR_LABEL_TOKEN = re.compile(r'<div\s+class="bar-label"[^>]*>(?P<label>.*?)</div>', re.I | re.S)
BASELINE_N_TOKEN = re.compile(r"\bn\s*=\s*(?P<count>\d{1,3}(?:,\d{3})*|\d+)", re.I)

# These panels already publish numeric rate labels but do not have a single
# deduplicated denominator that can serve as the primary comparable reference.
# The fallback is deliberately local: it ranks only rates within the specified
# chart panel and never makes a cross-slide or cross-panel assertion.
RELATIVE_RANK_FALLBACKS: dict[str, tuple[tuple[str, tuple[int, ...]], ...]] = {
    "slide-20": (
        ("Mar 2023 survey wave", (0, 1, 2)),
        ("Jan 2024 survey wave", (3, 4, 5)),
        ("Jan 2025 survey wave", (6, 7, 8)),
        ("2026 YTD survey wave", (9, 10, 11)),
    ),
    "slide-37-followup": (("Exact compensation-grade distribution", tuple(range(18))),),
    "slide-40": (
        ("Managers by number of groups to review", (0, 1, 2, 3, 4)),
        ("Share of comparable groups to review", (5, 6, 7, 8, 9, 10)),
    ),
    "slide-42": (("Assigned office-site relationship", (0, 1, 2)),),
}

# These are category boundaries, not measured results.  For example, turning
# "1–<1.1" into "1–<1" would create an invalid or misleading band.  Values
# whose fractional component is exactly zero are intentionally not protected:
# "50–<75.0%" can safely become "50–<75%".
NONZERO_FRACTIONAL_DECIMAL = r"\d+\.\d*[1-9]\d*"
SEMANTIC_CUTOFF_TOKEN = re.compile(
    rf"(?:"
    rf"(?:(?:&gt;|&lt;|&ge;|&le;|[<>≤≥])\s*)?\d+(?:\.\d+)?\s*(?:–|-)\s*(?:(?:&lt;|&le;|[<≤])\s*)?{NONZERO_FRACTIONAL_DECIMAL}(?:\s*(?:×|&times;|x))?"
    rf"|(?:(?:≥|&ge;)\s*){NONZERO_FRACTIONAL_DECIMAL}(?:\s*(?:×|&times;|x))?"
    rf")"
)
REQUIRED_SEMANTIC_CUTOFFS = (
    "1–&lt; 1.1",
    "1.1–&lt; 1.2",
    "≥ 1.2",
    "1–&lt;1.5×",
    "≥1.5×",
)


# The first two stages are reader orientation.  Every remaining stage appears
# exactly once in one of the two user-selected groups.
ORDERED_STAGES: tuple[tuple[str, str, str], ...] = (
    ("slide-1", "Start", "Employee characteristics and attrition"),
    ("slide-2", "Start", "Index"),
    ("slide-5", "Prioritized · workforce and mobility", "IOS movement events"),
    ("slide-12", "Prioritized · workforce and mobility", "Region"),
    ("slide-14", "Prioritized · workforce and mobility", "Work arrangement"),
    ("slide-15", "Prioritized · workforce and mobility", "Engineering vs. non-engineering"),
    ("slide-16", "Prioritized · workforce and mobility", "Rehire"),
    ("slide-acquisition", "Prioritized · workforce and mobility", "Acquisitions and attrition"),
    ("slide-17", "Prioritized · workforce and mobility", "Experience before Qualcomm"),
    ("slide-19", "Prioritized · workforce and mobility", "Estimated commute distance and voluntary attrition"),
    ("slide-21", "Prioritized · QVoice", "Retention concerns in QVoice comments"),
    ("slide-23", "Prioritized · QVoice", "Intent to Stay items"),
    ("slide-24", "Prioritized · QVoice", "Career goals item"),
    ("slide-25", "Prioritized · QVoice", "Average of comparable QVoice items"),
    ("slide-29", "Prioritized · career and organization", "Time at detailed level and time in role"),
    ("slide-31", "Prioritized · career and organization", "Company tenure"),
    ("slide-32", "Prioritized · career and organization", "Time since last promotion"),
    ("slide-34", "Prioritized · career and organization", "Promotion and attrition by pay track"),
    ("slide-37", "Prioritized · career and organization", "Manager layers to the CEO"),
    ("slide-37-span-followup", "Prioritized · career and organization", "Direct team size (span)"),
    ("slide-39", "Prioritized · career and organization", "Comp ratio"),
    ("slide-45", "Prioritized · manager signals", "Recent team exits under the current manager"),
    ("slide-47", "Prioritized · manager signals", "Manager leaving"),
    ("slide-3", "Other reviewed · applications and workplace", "Applied to a job"),
    ("slide-6", "Other reviewed · applications and workplace", "Location"),
    ("slide-7", "Other reviewed · applications and workplace", "Office site and city"),
    ("slide-9", "Other reviewed · applications and workplace", "Does one team departure precede more departures?"),
    ("slide-10", "Other reviewed · applications and workplace", "Sensitivity check: teams with 6+ employees"),
    ("slide-11", "Other reviewed · applications and workplace", "Job family"),
    ("slide-13", "Other reviewed · applications and workplace", "Gender"),
    ("slide-20", "Other reviewed · QVoice supporting context", "QVoice comments about remote, hybrid, and office work"),
    ("slide-26", "Other reviewed · QVoice supporting context", "QVoice heartbeat"),
    ("slide-35", "Other reviewed · career and compensation context", "Level"),
    ("slide-36", "Other reviewed · career and compensation context", "Level grouped by grade family"),
    ("slide-37-followup", "Other reviewed · career and compensation context", "0–2 layers: exact compensation grades"),
    ("slide-38", "Other reviewed · career and compensation context", "Compensation grade"),
    ("slide-40", "Other reviewed · career and compensation context", "Within-team compensation range"),
    ("slide-42", "Other reviewed · manager and support fields", "Assigned office-site proximity to manager"),
    ("slide-43", "Other reviewed · manager and support fields", "Office-site relationship with manager"),
    ("slide-44", "Other reviewed · manager and support fields", "Manager observed-to-expected exit ratio"),
    ("slide-46", "Other reviewed · manager and support fields", "Above-average team turnover"),
    ("slide-48", "Other reviewed · manager and support fields", "Manager change"),
    ("slide-49", "Other reviewed · manager and support fields", "Number of manager changes"),
    ("slide-50", "Other reviewed · manager and support fields", "Talent index"),
)

SECTION_ORDER: tuple[tuple[str, str], ...] = (
    ("Start", "Orientation"),
    ("Prioritized · workforce and mobility", "Selected workforce and mobility signals"),
    ("Prioritized · QVoice", "Selected QVoice signals"),
    ("Prioritized · career and organization", "Selected career, span, and organization signals"),
    ("Prioritized · manager signals", "Selected manager signals"),
    ("Other reviewed · applications and workplace", "Other application, team, and workplace variables"),
    ("Other reviewed · QVoice supporting context", "Other QVoice context"),
    ("Other reviewed · career and compensation context", "Other career and compensation context"),
    ("Other reviewed · manager and support fields", "Other manager and support fields"),
)

V8_OWNED_STAGE_IDS = frozenset({"slide-acquisition"})


V8_CSS = r'''

    /* V8 reader ordering and IOS visual. */
    #slide-1 .v8-overview { display:grid; grid-template-rows:auto 1fr auto; gap:12px; height:100%; }
    #slide-1 .v8-overview-lead { margin:0; color:var(--text-main); font-size:21px; font-weight:800; line-height:1.18; }
    #slide-1 .v8-overview-sub { margin:0; color:var(--text-muted); font-size:13px; line-height:1.38; max-width:940px; }
    #slide-1 .v8-overview-groups { display:grid; grid-template-columns:1fr 1fr; gap:14px; min-height:0; }
    #slide-1 .v8-overview-group { border:1px solid var(--border-subtle); border-radius:14px; padding:15px 17px; background:color-mix(in oklab,var(--bg-surface) 88%,transparent); }
    #slide-1 .v8-overview-group.priority { border-color:var(--border-strong); background:color-mix(in oklab,var(--accent) 6%,var(--bg-surface)); }
    #slide-1 .v8-overview-group h3 { margin:0 0 8px; color:var(--text-main); font-size:16px; }
    #slide-1 .v8-overview-group p { margin:0; color:var(--text-muted); font-size:12px; line-height:1.35; }
    #slide-1 .v8-topic-list { display:flex; flex-wrap:wrap; gap:6px; margin-top:12px; }
    #slide-1 .v8-topic { padding:4px 8px; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); color:var(--text-main); background:color-mix(in oklab,var(--bg-surface-2) 80%,transparent); font-size:10px; font-weight:700; line-height:1.1; }
    #slide-1 .v8-method-strip { display:grid; grid-template-columns:.9fr .95fr 1.35fr 1.45fr; gap:8px; }
    #slide-1 .v8-method { border-left:3px solid var(--accent); padding:7px 10px; background:color-mix(in oklab,var(--accent) 6%,transparent); color:var(--text-muted); font-size:11px; line-height:1.32; }
    #slide-1 .v8-method strong { display:block; margin-bottom:2px; color:var(--text-main); font-size:11px; }
    .v8-color-reference { color:var(--text-muted); font-size:inherit; font-weight:700; white-space:normal; }
    .v8-color-reference-standalone { margin:4px 0 0; padding-top:4px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:8.5px; line-height:1.2; }
    .v8-reference-unavailable { color:var(--text-muted) !important; background:color-mix(in oklab,var(--text-muted) 8%,transparent) !important; border:1px dashed color-mix(in oklab,var(--text-muted) 35%,var(--border-subtle)) !important; }
    #slide-2 .v8-agenda { display:flex; flex-direction:column; height:100%; gap:9px; }
    #slide-2 .v8-agenda-intro { margin:0 0 3px; color:var(--text-muted); font-size:13px; line-height:1.35; }
    #slide-2 .v8-agenda-row { display:grid; grid-template-columns:110px 250px 1fr; align-items:center; gap:14px; padding:11px 13px; border:1px solid var(--border-subtle); border-radius:11px; background:var(--bg-surface-2); }
    #slide-2 .v8-agenda-range { color:var(--accent); font-size:11px; font-weight:800; letter-spacing:.04em; text-transform:uppercase; }
    #slide-2 .v8-agenda-row strong { color:var(--text-main); font-size:14px; }
    #slide-2 .v8-agenda-row span:last-child { color:var(--text-muted); font-size:12px; line-height:1.25; }
    /* Other reviewed is deliberately neutral so it cannot read as prioritized. */
    #slide-2 .v8-agenda-row--other { border-color:color-mix(in oklab,var(--text-muted) 36%,var(--border-subtle)); border-left:5px solid color-mix(in oklab,var(--text-muted) 74%,var(--bg-surface)); background:color-mix(in oklab,var(--text-muted) 10%,var(--bg-surface)); }
    #slide-2 .v8-agenda-row--other .v8-agenda-range,
    #slide-2 .v8-agenda-row--other strong { color:var(--text-muted); }
    #slide-5 .v8-ios-card { padding:13px 15px 11px; gap:10px; }
    #slide-5 .v8-ios-definition { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
    #slide-5 .v8-ios-definition div { padding:7px 9px; border-left:3px solid var(--accent); border-radius:7px; background:color-mix(in oklab,var(--accent) 7%,transparent); color:var(--text-muted); font-size:10.5px; line-height:1.27; }
    #slide-5 .v8-ios-definition strong { color:var(--text-main); }
    #slide-5 .v8-ios-total { display:grid; grid-template-columns:1.1fr 1fr 1fr; gap:8px; }
    #slide-5 .v8-ios-total div { min-height:48px; padding:7px 10px; border:1px solid var(--border-subtle); border-radius:10px; background:color-mix(in oklab,var(--bg-surface-2) 78%,transparent); }
    #slide-5 .v8-ios-total strong { display:block; color:var(--text-main); font-size:18px; line-height:1; font-variant-numeric:tabular-nums; }
    #slide-5 .v8-ios-total span { display:block; margin-top:3px; color:var(--text-muted); font-size:9.5px; line-height:1.15; }
    #slide-5 .v8-ios-bars { display:flex; flex:1; flex-direction:column; justify-content:space-evenly; min-height:0; }
    #slide-5 .v8-ios-row { display:grid; grid-template-columns:228px minmax(0,1fr) 114px 162px; align-items:center; gap:9px; min-height:43px; border-bottom:1px solid var(--border-subtle); }
    #slide-5 .v8-ios-row:last-child { border-bottom:0; }
    #slide-5 .v8-ios-label { color:var(--text-main); font-size:12px; font-weight:800; line-height:1.14; }
    #slide-5 .v8-ios-track { height:12px; overflow:hidden; border:1px solid color-mix(in oklab,var(--text-muted) 20%,transparent); border-radius:var(--radius-pill); background:color-mix(in oklab,var(--text-muted) 10%,transparent); }
    #slide-5 .v8-ios-fill { height:100%; min-width:2px; border-radius:inherit; background:var(--accent); }
    #slide-5 .v8-ios-current { color:var(--text-muted); font-size:10px; font-variant-numeric:tabular-nums; line-height:1.17; }
    #slide-5 .v8-ios-current strong { display:block; color:var(--text-main); font-size:11px; }
    #slide-5 .v8-ios-rate { justify-self:end; min-width:145px; padding:5px 7px; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); color:var(--text-main); font-size:10.5px; font-weight:800; text-align:center; font-variant-numeric:tabular-nums; white-space:nowrap; }
    #slide-5 .v8-ios-rate.low { border-color:color-mix(in oklab,#16a34a 45%,transparent); color:#15803d; }
    #slide-5 .v8-ios-rate.high { border-color:color-mix(in oklab,#c2410c 45%,transparent); color:#c2410c; }
    #slide-5 .v8-ios-rate.exploratory { color:var(--text-muted); font-size:9.5px; }
    #slide-5 .v8-ios-note { margin:0; padding-top:7px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:10px; line-height:1.24; }
    #slide-5 .v8-ios-note strong { color:var(--text-main); }

    /* Promocion: encabezados y cifras en gris claro, centrados en su columna. */
    #slide-34 { --promotion-text: #8a909b; }
    body.theme-dark-royal #slide-34,
    body.theme-dark-carbon #slide-34 { --promotion-text: #b8bec8; }
    #slide-34 .track-story-header > div:nth-child(3),
    #slide-34 .track-story-rate-value { color:var(--promotion-text); text-align:center; }
    #slide-34 .track-story-row > .track-story-rate:nth-child(3) { justify-content:center; }

    /* Adquisiciones: jerarquía visual y copy en inglés por solicitud del usuario. */
    #slide-acquisition { --acquisition-muted:color-mix(in oklab,var(--text-main) 28%,var(--text-muted)); }
    #slide-acquisition .v8-acquisition-card { padding:16px 18px 12px; gap:10px; }
    #slide-acquisition .v8-acquisition-layout { display:grid; grid-template-columns:480px minmax(0,1fr); gap:16px; flex:1; min-height:0; }
    #slide-acquisition .v8-acquisition-summary { display:grid; grid-template-rows:1fr 1.2fr; gap:14px; min-height:0; }
    #slide-acquisition .v8-acquisition-panel { display:flex; flex-direction:column; min-height:0; padding:17px 18px; gap:12px; border:1px solid var(--border-subtle); border-radius:14px; background:var(--bg-surface-2); }
    #slide-acquisition .v8-acquisition-panel h3 { margin:0; color:var(--text-main); font-size:18px; font-weight:800; line-height:1.2; }
    #slide-acquisition .v8-acquisition-context { margin:5px 0 0; color:var(--acquisition-muted); font-size:12px; line-height:1.3; }
    #slide-acquisition .v8-acquisition-mix { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
    #slide-acquisition .v8-acquisition-mix-item { display:flex; flex-direction:column; gap:4px; }
    #slide-acquisition .v8-acquisition-mix-value { font-size:44px; line-height:1.08; letter-spacing:-.03em; font-weight:800; font-variant-numeric:tabular-nums; }
    #slide-acquisition .v8-acquisition-mix-item:first-child .v8-acquisition-mix-value { color:var(--accent); }
    #slide-acquisition .v8-acquisition-label { color:var(--text-main); font-size:14px; font-weight:700; line-height:1.2; }
    #slide-acquisition .v8-acquisition-mix-item small { color:var(--acquisition-muted); font-size:13px; }
    #slide-acquisition .v8-acquisition-composition { display:flex; height:28px; flex-shrink:0; overflow:hidden; border-radius:7px; background:color-mix(in oklab,var(--accent) 20%,var(--bg-surface)); }
    #slide-acquisition .v8-acquisition-composition-fill { height:100%; background:var(--accent); border-right:3px solid var(--bg-surface-2); }
    #slide-acquisition .v8-acquisition-rate-grid { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
    #slide-acquisition .v8-acquisition-rate-card { display:flex; flex-direction:column; align-items:flex-start; gap:8px; }
    #slide-acquisition .v8-acquisition-rate-card .v8-acquisition-label { min-height:34px; }
    /* Semantic colors come from the deck's .attr-* rules, not the layout class. */
    #slide-acquisition .v8-acquisition-rate { display:inline-flex; align-items:center; justify-content:center; min-width:104px; padding:5px 10px; border-radius:var(--radius-pill); font-size:14px; font-weight:800; font-variant-numeric:tabular-nums; line-height:1.15; text-align:center; white-space:nowrap; }
    #slide-acquisition .v8-acquisition-rate-card .v8-acquisition-rate { min-width:122px; padding:8px 14px; font-size:36px; letter-spacing:-.02em; }
    #slide-acquisition .v8-acquisition-baseline { color:var(--acquisition-muted); font-size:12px; font-variant-numeric:tabular-nums; }
    #slide-acquisition .v8-acquisition-takeaway { margin:0; padding:12px 0 0; border-top:1px solid var(--border-subtle); font-size:18px; font-weight:750; line-height:1.25; color:var(--text-main); }
    #slide-acquisition .v8-acquisition-takeaway small { display:block; margin-top:4px; font-size:12px; font-weight:400; color:var(--acquisition-muted); }
    #slide-acquisition .v8-acquisition-details { padding:17px 16px 12px; gap:9px; }
    #slide-acquisition .v8-acquisition-table { width:100%; border-collapse:collapse; table-layout:fixed; flex:1; font-size:14px; font-variant-numeric:tabular-nums; }
    #slide-acquisition .v8-acquisition-table thead th { padding:5px 6px 8px; color:var(--acquisition-muted); font-size:12px; font-weight:600; text-align:right; border-bottom:2px solid var(--border-subtle); }
    #slide-acquisition .v8-acquisition-table thead th:first-child { text-align:left; }
    #slide-acquisition .v8-acquisition-table thead th:last-child { text-align:center; }
    #slide-acquisition .v8-acquisition-table tbody th { padding:6px; text-align:left; font-size:13px; font-weight:650; line-height:1.2; }
    #slide-acquisition .v8-acquisition-table td { padding:6px; text-align:right; }
    #slide-acquisition .v8-acquisition-table tbody tr { height:38px; border-bottom:1px solid var(--border-subtle); }
    #slide-acquisition .v8-acquisition-table tbody tr:last-child { border-top:2px solid var(--border-strong); border-bottom:0; }
    #slide-acquisition .v8-acquisition-table td:last-child { text-align:center; }
    #slide-acquisition .v8-acquisition-share { color:var(--acquisition-muted); }
    #slide-acquisition .v8-acquisition-track { height:12px; overflow:hidden; border-radius:var(--radius-pill); background:color-mix(in oklab,var(--accent) 9%,var(--bg-surface)); }
    #slide-acquisition .v8-acquisition-fill { height:100%; min-width:2px; border-radius:inherit; background:var(--accent); }
    #slide-acquisition .v8-acquisition-table .v8-reference-unavailable { font-size:12px; color:var(--acquisition-muted) !important; }
    #slide-acquisition .v8-acquisition-legend { margin:0; color:var(--acquisition-muted); font-size:12px; line-height:1.35; }
    #slide-acquisition .v8-acquisition-notes { display:flex; flex-direction:column; gap:4px; padding-top:9px; border-top:1px solid var(--border-subtle); }
    #slide-acquisition .v8-acquisition-notes p { margin:0; color:var(--acquisition-muted); font-size:12px; line-height:1.25; }
    #slide-acquisition .v8-acquisition-notes strong { color:var(--text-main); }
    #slide-acquisition .v8-color-reference-standalone { margin:0; padding-top:0; border-top:0; color:var(--acquisition-muted); font-size:12px; font-weight:400; line-height:1.25; }
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive_current_v8() -> dict[str, Any] | None:
    """Archive an existing V8 deck before overwriting it, once per deck hash."""
    if not OUTPUT_DECK.exists():
        return None
    deck_sha256 = digest(OUTPUT_DECK)
    archive_id = f"v8-{deck_sha256[:12]}"
    deck_name = f"attrition-43-variable-distributions-{archive_id}.html"
    manifest_name = f"attrition-43-variable-distributions-{archive_id}-manifest.json"
    BACKUP_DIRECTORY.mkdir(parents=True, exist_ok=True)
    if BACKUP_REGISTRY.exists():
        registry = json.loads(BACKUP_REGISTRY.read_text(encoding="utf-8"))
    else:
        registry = {
            "schema_version": 1,
            "artifact": "Attrition distribution V8 backup registry",
            "search_instruction": "Search this registry by archive_id, deck_sha256, generated_at_utc, or original paths before opening an archived deck.",
            "backups": [],
        }
    backups = registry.get("backups")
    require(isinstance(backups, list), "V8 backup registry has an invalid backups collection.")
    existing = next((row for row in backups if row.get("deck_sha256") == deck_sha256), None)
    if existing is not None:
        return existing

    archived_deck = BACKUP_DIRECTORY / deck_name
    shutil.copy2(OUTPUT_DECK, archived_deck)
    archived_manifest: str | None = None
    if OUTPUT_MANIFEST.exists():
        manifest_path = BACKUP_DIRECTORY / manifest_name
        shutil.copy2(OUTPUT_MANIFEST, manifest_path)
        archived_manifest = manifest_path.name
    entry = {
        "archive_id": archive_id,
        "deck": archived_deck.name,
        "manifest": archived_manifest,
        "deck_sha256": deck_sha256,
        "archived_at_utc": datetime.now(timezone.utc).isoformat(),
        "original_deck": str(OUTPUT_DECK.relative_to(ROOT)).replace("\\", "/"),
        "original_manifest": str(OUTPUT_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
    }
    backups.append(entry)
    BACKUP_REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return entry


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def fmt_count(value: int) -> str:
    return f"{value:,}"


def display_decimal(value: Decimal, *, grouping: bool) -> str:
    """Apply V8's reader-facing precision policy without changing evidence."""
    if value == 0:
        return "0"

    magnitude = abs(value)
    if magnitude >= Decimal("1"):
        rounded = value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return f"{int(rounded):,}" if grouping else str(int(rounded))

    rounded = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if rounded == 0:
        return ">-0.1" if value < 0 else "<0.1"
    if abs(rounded) >= Decimal("1"):
        return f"{int(rounded):,}" if grouping else str(int(rounded))

    rendered = format(rounded, ".1f")
    if not grouping:
        return rendered
    integer_part, decimal_part = rendered.split(".", 1)
    return f"{int(integer_part):,}.{decimal_part}"


def format_display_token(raw_value: str) -> str:
    """Format one visible decimal token while retaining its grouping style."""
    try:
        value = Decimal(raw_value.replace(",", ""))
    except InvalidOperation:
        return raw_value
    return display_decimal(value, grouping="," in raw_value)


def protect_semantic_cutoffs(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Shield exact band boundaries while reader-facing rates are formatted."""
    protected: list[tuple[str, str]] = []

    def replace(match: re.Match[str]) -> str:
        placeholder = f"__V8_SEMANTIC_CUTOFF_{len(protected)}__"
        protected.append((placeholder, match.group(0)))
        return placeholder

    return SEMANTIC_CUTOFF_TOKEN.sub(replace, text), protected


def restore_semantic_cutoffs(text: str, protected: list[tuple[str, str]]) -> str:
    for placeholder, original in protected:
        text = text.replace(placeholder, original)
    return text


def normalize_display_number_text(text: str) -> str:
    """Normalize values shown to readers while retaining semantic band cuts."""
    masked, protected = protect_semantic_cutoffs(text)
    normalized = DISPLAY_NUMBER_TOKEN.sub(
        lambda match: format_display_token(match.group("number")) + match.group("suffix"),
        masked,
    )
    return restore_semantic_cutoffs(normalized, protected)


def normalize_visible_display_numbers(deck: str) -> str:
    """Normalize static text, tooltips, and accessibility copy only.

    Script/CSS payloads, style attributes, and calculation expressions stay
    unchanged so formatting cannot affect chart geometry or source evidence.
    """
    # Attrition rates retain one decimal place by policy.  Protect their full
    # element (including rate-specific accessibility copy) before applying the
    # deck-wide integer-first formatter to every other reader-facing number.
    segments = READER_PROTECTED_BLOCK.split(deck)
    for index in range(0, len(segments), 2):
        tokens = HTML_TAG_TOKEN.split(segments[index])
        for token_index, token in enumerate(tokens):
            if token.startswith("<"):
                tokens[token_index] = DISPLAY_ATTRIBUTE_TOKEN.sub(
                    lambda match: (
                        match.group("prefix")
                        + normalize_display_number_text(match.group("value"))
                        + match.group("suffix")
                    ),
                    token,
                )
            else:
                tokens[token_index] = normalize_display_number_text(token)
        segments[index] = "".join(tokens)
    return "".join(segments)


def remove_v7_dynamic_number_formatter(deck: str) -> str:
    """Prevent V7's one-decimal runtime formatter from pre-rounding V8 charts."""
    result, removed = V7_DYNAMIC_FORMATTER_BLOCK.subn("\n", deck, count=1)
    require(removed == 1, "V8 could not remove the inherited V7 dynamic number formatter.")
    require('data-v7-display-number-formatter="true"' not in result, "V8 retained the V7 dynamic number formatter.")
    return result


def inject_v8_dynamic_number_formatter(deck: str) -> str:
    """Apply V8's policy to labels and tooltips created after page load."""
    require(V8_NUMERIC_DISPLAY_FORMATTER_MARKER not in deck, "V8 number formatter was injected more than once.")
    body_match = re.search(r"<body\b[^>]*>", deck, re.I)
    require(body_match is not None, "V8 deck is missing its body element.")
    script = r'''
<!-- V8 DISPLAY NUMBER FORMATTER -->
  <script data-v8-display-number-formatter="true">
    (function () {
      var token = /(^|[^\w,.-])(-?(?:\d{1,3}(?:,\d{3})+|\d+)\.\d+)(%?)(?![\w,.-])/g;
      var semanticCutoff = /(?:(?:[<>≤≥]\s*)?\d+(?:\.\d+)?\s*(?:–|-)\s*(?:[<≤]\s*)?\d+\.\d*[1-9]\d*(?:\s*[×x])?|(?:≥\s*)\d+\.\d*[1-9]\d*(?:\s*[×x])?)/g;
      function roundHalfUp(value, digits) {
        var factor = Math.pow(10, digits);
        var magnitude = Math.abs(value) * factor;
        var roundedMagnitude = Math.floor(magnitude + 0.5 + Number.EPSILON);
        return (value < 0 ? -1 : 1) * roundedMagnitude / factor;
      }
      function formatRounded(value, grouping, fractionDigits) {
        return new Intl.NumberFormat('en-US', {
          useGrouping: grouping,
          minimumFractionDigits: fractionDigits,
          maximumFractionDigits: fractionDigits
        }).format(value);
      }
      function formatNumber(value, grouping) {
        if (value === 0) return '0';
        var magnitude = Math.abs(value);
        if (magnitude >= 1) return formatRounded(roundHalfUp(value, 0), grouping, 0);
        var rounded = roundHalfUp(value, 1);
        if (rounded === 0) return value < 0 ? '>-0.1' : '<0.1';
        if (Math.abs(rounded) >= 1) return formatRounded(roundHalfUp(rounded, 0), grouping, 0);
        return formatRounded(rounded, grouping, 1);
      }
      function protectCutoffs(value) {
        var protectedValues = [];
        var masked = String(value).replace(semanticCutoff, function (match) {
          var placeholder = '@@V8_SEMANTIC_CUTOFF_' + protectedValues.length + '@@';
          protectedValues.push([placeholder, match]);
          return placeholder;
        });
        return { masked: masked, protectedValues: protectedValues };
      }
      function restoreCutoffs(value, protectedValues) {
        protectedValues.forEach(function (entry) { value = value.split(entry[0]).join(entry[1]); });
        return value;
      }
      function normalizeText(value) {
        var protectedText = protectCutoffs(value);
        var normalized = protectedText.masked.replace(token, function (whole, prefix, rawNumber, suffix) {
          var numeric = Number(rawNumber.replace(/,/g, ''));
          if (!Number.isFinite(numeric)) return whole;
          return prefix + formatNumber(numeric, rawNumber.indexOf(',') >= 0) + suffix;
        });
        return restoreCutoffs(normalized, protectedText.protectedValues);
      }
      function skip(node) {
        var parent = node && node.parentElement;
        return parent && (/^(SCRIPT|STYLE|CODE|PRE|TEXTAREA)$/i.test(parent.tagName) || parent.closest('[data-v8-rate-precision="one-decimal"], [data-v8-percent-precision="one-decimal"]'));
      }
      function normalizeTextNode(node) {
        if (!node || skip(node)) return;
        var normalized = normalizeText(node.nodeValue);
        if (normalized !== node.nodeValue) node.nodeValue = normalized;
      }
      function normalizeElement(element) {
        if (!element || /^(SCRIPT|STYLE|CODE|PRE|TEXTAREA)$/i.test(element.tagName) || element.closest('[data-v8-rate-precision="one-decimal"], [data-v8-percent-precision="one-decimal"]')) return;
        ['title', 'aria-label', 'aria-description', 'aria-valuetext', 'alt'].forEach(function (attribute) {
          if (!element.hasAttribute(attribute)) return;
          var current = element.getAttribute(attribute);
          var normalized = normalizeText(current);
          if (normalized !== current) element.setAttribute(attribute, normalized);
        });
      }
      function normalizeSubtree(root) {
        if (!root) return;
        if (root.nodeType === Node.TEXT_NODE) {
          normalizeTextNode(root);
          return;
        }
        if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE) return;
        if (root.nodeType === Node.ELEMENT_NODE) normalizeElement(root);
        var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        var textNode;
        while ((textNode = walker.nextNode())) normalizeTextNode(textNode);
        if (root.querySelectorAll) root.querySelectorAll('[title], [aria-label], [aria-description], [aria-valuetext], [alt]').forEach(normalizeElement);
      }
      var observer = new MutationObserver(function (records) {
        records.forEach(function (record) {
          if (record.type === 'characterData') normalizeTextNode(record.target);
          if (record.type === 'attributes') normalizeElement(record.target);
          record.addedNodes.forEach(normalizeSubtree);
        });
      });
      observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
        characterData: true,
        attributes: true,
        attributeFilter: ['title', 'aria-label', 'aria-description', 'aria-valuetext', 'alt']
      });
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () { normalizeSubtree(document.body); });
      } else {
        normalizeSubtree(document.body);
      }
    })();
  </script>
'''
    return deck[:body_match.end()] + script + deck[body_match.end():]


def validate_display_number_policy(deck: str) -> None:
    """Fail the build if reader-visible V8 content exposes false precision."""
    examples = {
        "5.5": "6",
        "0.84": "0.8",
        "0.04": "<0.1",
        "0.0": "0",
        "0.95": "1",
        "-0.04": ">-0.1",
        "1,234.5": "1,235",
    }
    for raw, expected in examples.items():
        require(format_display_token(raw) == expected, f"V8 display formatter failed {raw}.")

    require(V8_NUMERIC_DISPLAY_FORMATTER_MARKER in deck, "V8 runtime number formatter is missing.")
    require('data-v8-display-number-formatter="true"' in deck, "V8 runtime number formatter marker is missing.")
    require('data-v7-display-number-formatter="true"' not in deck, "V8 retained the V7 runtime number formatter.")
    require("new MutationObserver" in deck, "V8 runtime number formatter does not cover dynamic chart labels.")
    require("roundHalfUp" in deck, "V8 runtime formatter does not use the approved rounding rule.")
    for cutoff in REQUIRED_SEMANTIC_CUTOFFS:
        require(cutoff in deck, f"V8 semantic cutoff was changed: {cutoff}.")

    violations: list[str] = []
    # One-decimal attrition rates and their accessibility copy are an explicit
    # exception to the general display-number policy.
    segments = READER_PROTECTED_BLOCK.split(deck)
    for index in range(0, len(segments), 2):
        for token in HTML_TAG_TOKEN.split(segments[index]):
            values = []
            if token.startswith("<"):
                values.extend(match.group("value") for match in DISPLAY_ATTRIBUTE_TOKEN.finditer(token))
            else:
                values.append(token)
            for value in values:
                masked, _ = protect_semantic_cutoffs(value)
                for match in DISPLAY_NUMBER_TOKEN.finditer(masked):
                    decimal_value = Decimal(match.group("number").replace(",", ""))
                    fractional = match.group("number").rsplit(".", 1)[1]
                    if len(fractional) != 1 or decimal_value == 0 or abs(decimal_value) >= 1:
                        violations.append(match.group(0))
    require(not violations, f"V8 visible number precision violations: {violations[:8]}")


def fmt_pct(value: float) -> str:
    """Display a reader-facing attrition rate without losing its decimal place."""
    decimal_value = Decimal(str(value))
    rounded = decimal_value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if decimal_value != 0 and rounded == 0:
        return "<0.1%" if decimal_value > 0 else ">-0.1%"
    return format(rounded, ".1f") + "%"


def load_color_policy() -> dict[str, Any]:
    policy = json.loads(COLOR_POLICY.read_text(encoding="utf-8"))
    calculation = policy.get("calculation", {})
    require(policy.get("deliverable_mode") == "internal_analysis", "V8 attrition-color policy has the wrong delivery mode.")
    require(Decimal(str(calculation.get("relative_materiality"))) == Decimal("0.2"), "V8 attrition-color policy must use the approved 20% materiality threshold.")
    require(
        Decimal(str(calculation.get("absolute_materiality_percentage_points"))) == Decimal("0.5"),
        "V8 attrition-color policy must use the approved 0.5 percentage-point threshold.",
    )
    sources = policy.get("reference_sources", {})
    require(sources, "V8 attrition-color policy is missing reference sources.")
    for source_id, source in sources.items():
        evidence_path = ROOT / str(source.get("evidence_path", ""))
        require(evidence_path.is_file(), f"V8 attrition-color source {source_id} is missing its evidence artifact.")
        exits = Decimal(str(source.get("voluntary_exits")))
        denominator = Decimal(str(source.get("baseline_employee_snapshots", source.get("baseline_employee_count"))))
        observed = (Decimal("100") * exits / denominator).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        declared = Decimal(str(source.get("rate_percent")))
        require(abs(observed - declared) <= Decimal("0.0001"), f"V8 attrition-color source {source_id} does not reconcile.")
    return policy


def attrition_color_class(rate: Decimal | None, reference_rate: Decimal | None, policy: dict[str, Any]) -> str:
    """Classify from evidence precision, never from the reader-visible rounded text."""
    unavailable = str(policy["states"]["not_comparable"])
    if rate is None or reference_rate is None:
        return unavailable
    relative = Decimal(str(policy["calculation"]["relative_materiality"]))
    absolute = Decimal(str(policy["calculation"]["absolute_materiality_percentage_points"]))
    if reference_rate == 0:
        if rate >= absolute:
            return str(policy["states"]["above_reference"])
        return str(policy["states"]["within_reference"])
    if rate <= reference_rate * (Decimal("1") - relative) and rate <= reference_rate - absolute:
        return str(policy["states"]["below_reference"])
    if rate >= reference_rate * (Decimal("1") + relative) and rate >= reference_rate + absolute:
        return str(policy["states"]["above_reference"])
    return str(policy["states"]["within_reference"])


def replace_rate_class(attributes: str, color_class: str) -> str:
    cleaned = RATE_CLASS_TOKEN.sub("", attributes)
    cleaned = re.sub(r"\s+", " ", cleaned).rstrip()
    class_match = re.search(r'(\bclass=")(?P<value>[^"]*)(")', cleaned)
    require(class_match is not None, "A V8 attrition-rate element is missing its CSS class.")
    classes = " ".join(token for token in class_match.group("value").split() if token)
    replacement = f'{class_match.group(1)}{classes} {color_class}{class_match.group(3)}'
    return cleaned[: class_match.start()] + replacement + cleaned[class_match.end() :]


def with_rate_marker(
    attributes: str,
    *,
    reference_id: str | None,
    color_method: str | None = None,
) -> str:
    attributes = re.sub(r'\sdata-v8-(?:rate-precision|color-reference|color-method)="[^"]*"', "", attributes)
    marker = ' data-v8-rate-precision="one-decimal"'
    if reference_id is not None:
        marker += f' data-v8-color-reference="{html.escape(reference_id, quote=True)}"'
    if color_method is not None:
        marker += f' data-v8-color-method="{html.escape(color_method, quote=True)}"'
    return attributes.rstrip() + marker


def parsed_rate(value: str) -> Decimal | None:
    match = RATE_VALUE_TOKEN.search(value)
    if match is None:
        return None
    return Decimal(match.group("rate").replace(",", ""))


def baseline_n_from_attributes(attributes: str) -> int | None:
    """Return the published baseline count when the rate pill declares one."""
    match = BASELINE_N_TOKEN.search(html.unescape(attributes))
    return None if match is None else int(match.group("count").replace(",", ""))


def within_panel_rank_class(rate: Decimal, peer_rates: list[Decimal], policy: dict[str, Any]) -> str:
    """Use a simple local scale: low green, high orange, otherwise blue."""
    require(peer_rates, "A within-panel rank needs at least one numeric rate.")
    lowest = min(peer_rates)
    highest = max(peer_rates)
    if lowest == highest:
        return str(policy["states"]["within_reference"])
    if rate == lowest:
        return str(policy["states"]["below_reference"])
    if rate == highest:
        return str(policy["states"]["above_reference"])
    return str(policy["states"]["within_reference"])


EVIDENCE_CACHE: dict[Path, dict[str, Any]] = {}


def load_aggregate_evidence(path: Path) -> dict[str, Any]:
    """Load an approved aggregate-only artifact once during a build."""
    if path not in EVIDENCE_CACHE:
        evidence = json.loads(path.read_text(encoding="utf-8"))
        require(evidence.get("outcome") == "pass", f"Color source {path.name} did not pass its validation.")
        EVIDENCE_CACHE[path] = evidence
    return EVIDENCE_CACHE[path]


def refresh_acquisition_entry_evidence() -> dict[str, Any]:
    """Regenerate the presentation-safe acquisition contract from validated V4 evidence."""
    require(ACQUISITION_EVIDENCE_BUILDER.is_file(), "No existe el constructor de evidencia de adquisición.")
    spec = importlib.util.spec_from_file_location("acquisition_entry_evidence_builder", ACQUISITION_EVIDENCE_BUILDER)
    require(spec is not None and spec.loader is not None, "No se pudo cargar el constructor de evidencia de adquisición.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    evidence = module.build(ACQUISITION_EVIDENCE)
    require(isinstance(evidence, dict), "El constructor de adquisición no devolvió evidencia JSON.")
    return evidence


def load_acquisition_entry_evidence() -> dict[str, Any]:
    """Verify the small, presentation-safe contract used by slide-acquisition."""
    require(ACQUISITION_EVIDENCE.is_file(), "Falta la evidencia agregada de adquisición.")
    evidence = json.loads(ACQUISITION_EVIDENCE.read_text(encoding="utf-8"))
    require(evidence.get("artifact_type") == "acquisition_entry_distribution_attrition_evidence", "La evidencia de adquisición tiene un tipo incorrecto.")
    require(evidence.get("artifact_classification") == "presentation", "La evidencia de adquisición debe ser apta para presentación.")
    require(evidence.get("deliverable_mode") == "presentation", "La evidencia de adquisición tiene un modo de entrega incorrecto.")
    require(evidence.get("outcome") == "pass", "La evidencia de adquisición no pasó sus validaciones.")
    require(evidence.get("validation", {}).get("aggregate_only") == "pass", "La evidencia de adquisición no confirma el contrato agregado.")
    require(evidence.get("privacy", {}).get("employee_rows_persisted") is False, "La evidencia de adquisición no puede contener filas de empleados.")
    require(evidence.get("privacy", {}).get("individual_identifiers_persisted") is False, "La evidencia de adquisición no puede contener identificadores individuales.")
    dates = evidence.get("dates", {})
    require(dates.get("current_snapshot") == "2026-08-23", "La fecha actual de adquisición no coincide.")
    require(dates.get("baseline_snapshot") == "2025-08-24", "La fecha basal de adquisición no coincide.")
    require(dates.get("outcome_window") == "(2025-08-24, 2026-08-23]", "La ventana de attrition de adquisición no coincide.")
    population = evidence.get("population", {})
    require(
        population.get("worker_type") == "Employee"
        and population.get("employee_type") == "Regular"
        and population.get("active_status") == 1
        and population.get("rf360_included") is True,
        "La población de adquisición no coincide con el contrato aprobado.",
    )
    totals = evidence.get("totals", {})
    require(
        totals == {
            "current_active_regular_employee_count": 50_043,
            "baseline_active_regular_employee_count": 45_002,
            "baseline_voluntary_exit_count": 2_484,
        },
        "Los totales de adquisición no reconcilian.",
    )
    segments = evidence.get("overall_distribution")
    require(isinstance(segments, list) and len(segments) == 2, "La evidencia de adquisición debe contener dos segmentos generales.")
    require(
        [row.get("label") for row in segments] == ["Con adquisición registrada", "Sin adquisición registrada"],
        "Las etiquetas generales de adquisición no coinciden.",
    )
    require(sum(int(row["current_employee_count"]) for row in segments) == totals["current_active_regular_employee_count"], "Los segmentos actuales de adquisición no reconcilian.")
    require(sum(int(row["baseline_employee_count"]) for row in segments) == totals["baseline_active_regular_employee_count"], "Los segmentos basales de adquisición no reconcilian.")
    require(sum(int(row["voluntary_exit_count"]) for row in segments) == totals["baseline_voluntary_exit_count"], "Las salidas de adquisición no reconcilian.")
    for row in segments:
        computed = percentage_from_counts(row["voluntary_exit_count"], row["baseline_employee_count"])
        require(
            abs(computed - Decimal(str(row["annual_attrition_rate_percent"]))) < Decimal("0.000000000001"),
            "Una tasa general de adquisición no reconcilia con sus conteos.",
        )
    top = evidence.get("top_acquisitions")
    require(isinstance(top, list) and len(top) == 11, "La evidencia debe contener Top 10 más Otras adquisiciones.")
    require(top[-1].get("label") == "Otras adquisiciones", "La fila Otras adquisiciones falta en la evidencia.")
    require(sum(int(row["current_employee_count"]) for row in top) == int(segments[0]["current_employee_count"]), "Top 10 más Otras no reconcilia con el segmento adquirido.")
    for row in top:
        attrition = row.get("annual_attrition", {})
        status = attrition.get("publication_status")
        if status == "publishable":
            require(int(attrition["baseline_employee_count"]) >= 30 and int(attrition["voluntary_exit_count"]) >= 30, "Una tasa de adquisición publicada no cumple la supresión.")
            computed = percentage_from_counts(attrition["voluntary_exit_count"], attrition["baseline_employee_count"])
            require(abs(computed - Decimal(str(attrition["annual_attrition_rate_percent"]))) < Decimal("0.000000000001"), "Una tasa de adquisición publicada no reconcilia.")
        elif status == "suppressed_voluntary_events_lt_30":
            require(attrition.get("annual_attrition_rate_percent") is None, "Una tasa suprimida de adquisición no debe persistir.")
            require("voluntary_exit_count" not in attrition, "La evidencia de presentación no puede persistir eventos pequeños.")
        elif status == "no_annual_comparable_cohort":
            require(attrition.get("annual_attrition_rate_percent") is None and int(attrition["baseline_employee_count"]) == 0, "Una cohorte no comparable de adquisición está mal marcada.")
        else:
            raise ValueError(f"Estado de adquisición no reconocido: {status}.")
    references = evidence.get("color_references", {})
    overall_reference = references.get("overall_distribution", {})
    acquired_reference = references.get("acquisition_panel", {})
    require(
        int(overall_reference.get("voluntary_exits", -1)) == 2_484
        and int(overall_reference.get("eligible_baseline_count", -1)) == 45_002,
        "La referencia general de adquisición no reconcilia.",
    )
    require(
        int(acquired_reference.get("voluntary_exits", -1)) == 193
        and int(acquired_reference.get("eligible_baseline_count", -1)) == 6_148,
        "La referencia del panel adquirido no reconcilia.",
    )
    history = evidence.get("historical_baseline_reconciliation", {})
    require(
        history.get("current_evidence_baseline_count") == 45_002
        and history.get("previous_deck_baseline_count") == 45_003
        and history.get("status") == "requires_data_owner_reconciliation",
        "La diferencia histórica de cohorte basal debe quedar documentada.",
    )
    provenance = evidence.get("source_provenance", {}).get("distribution_query", {})
    require(
        provenance.get("sql_sha256") == "4c0bef229458d3cce31edbb26e74a6863012eec853eba1a4a30cccacbb5b6af8"
        and provenance.get("result_sha256") == "3567cc86914e6ddb2947c08c92a5db0939382ac1dc7ebf91c70df6c249651930",
        "La procedencia de distribución de adquisición no coincide.",
    )
    encoded = json.dumps(evidence, ensure_ascii=False).lower()
    for prohibited in ('"employee_id"', '"employeeid"', '"manager_employee_id"', '"manager_name"', '"employee_name"'):
        require(prohibited not in encoded, "La evidencia de adquisición contiene un campo restringido.")
    return evidence


def percentage_from_counts(numerator: int | Decimal, denominator: int | Decimal) -> Decimal:
    numerator_decimal = Decimal(str(numerator))
    denominator_decimal = Decimal(str(denominator))
    require(denominator_decimal > 0, "A color-reference denominator must be positive.")
    require(numerator_decimal >= 0, "A color-reference numerator cannot be negative.")
    return Decimal("100") * numerator_decimal / denominator_decimal


def rate_from_row(row: dict[str, Any]) -> Decimal | None:
    """Recalculate a rate from an aggregate numerator and denominator."""
    pairs = (
        ("voluntary_exits", "employee_snapshot_count"),
        ("voluntary_exit_count", "baseline_employee_count"),
        ("voluntary_exit_count", "matched_employee_count"),
        ("annual_voluntary_exit_n", "baseline_cohort_n"),
        ("annual_voluntary_exits", "annual_baseline_employee_count"),
        ("voluntary_exits", "employee_count"),
    )
    for numerator_key, denominator_key in pairs:
        numerator = row.get(numerator_key)
        denominator = row.get(denominator_key)
        if numerator is not None and denominator is not None:
            return percentage_from_counts(numerator, denominator)
    return None


def fmt_pct_decimal(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if value != 0 and rounded == 0:
        return "<0.1%" if value > 0 else ">-0.1%"
    return format(rounded, ".1f") + "%"


def canonical_label(value: str) -> str:
    """Make aggregate category labels comparable to their HTML rendering."""
    text = re.sub(r"<[^>]+>", "", value)
    text = html.unescape(text)
    text = text.replace("â€“", "–").replace("Â", "").replace("â‰¤", "≤").replace("â‰¥", "≥")
    text = re.sub(r"(?<=\d)\.0(?=[^0-9]|$)", "", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def source_rate_label(stage: str, match: re.Match[str]) -> str | None:
    """Return the category label in the bar row that owns a rate pill."""
    row_start = stage.rfind('<div class="bar-row', 0, match.start())
    if row_start < 0:
        return None
    labels = list(BAR_LABEL_TOKEN.finditer(stage[row_start : match.start()]))
    if not labels:
        return None
    return canonical_label(labels[-1].group("label"))


def source_panel_heading(stage: str, match: re.Match[str]) -> str | None:
    headings = [heading for heading in PANEL_HEADING_TOKEN.finditer(stage) if heading.start() < match.start()]
    if not headings:
        return None
    return canonical_label(headings[-1].group("label"))


def aggregate_metric_lookup(path: Path, metric: str) -> dict[str, tuple[Decimal, str]]:
    evidence = load_aggregate_evidence(path)
    records: dict[str, tuple[Decimal, str]] = {}
    for row in evidence.get("rows", []):
        if str(row.get("metric")) != metric:
            continue
        rate = rate_from_row(row)
        if rate is None:
            continue
        label = canonical_label(str(row.get("category", "")))
        if metric == "level_grouped":
            label = re.sub(r"^\d+\s*-\s*", "", label)
        records[label] = (rate, str(row.get("publication_status", "publishable")))
    return records


def source_rate_matches_evidence(source_match: re.Match[str], rate: Decimal) -> bool:
    rendered = parsed_rate(source_match.group("value"))
    if rendered is None:
        return False
    return rendered == parsed_rate(fmt_pct_decimal(rate))


def raw_evidence_rates_for_stage(stage_id: str, stage: str) -> list[Decimal | None] | None:
    """Resolve pre-rounding rates only where an aggregate source proves them.

    A missing mapping intentionally returns ``None`` for that pill.  The caller
    then renders gray rather than assigning a semantic color from V7's visible,
    one-decimal text.
    """
    matches = source_rate_pills(stage)
    if not matches:
        return []

    heading_metric_rules: dict[str, tuple[Path, tuple[tuple[str, str], ...]]] = {
        "slide-6": (SIX_MONTH_EVIDENCE, (("country", "country"),)),
        "slide-7": (
            SIX_MONTH_EVIDENCE,
            (("office site city", "office_site_city"), ("office site", "office_site")),
        ),
        "slide-12": (
            SIX_MONTH_EVIDENCE,
            (("alternative display", "region_country_split"), ("labor market", "labor_market"), ("region distribution", "region")),
        ),
        "slide-13": (SIX_MONTH_EVIDENCE, (("stored gender", "gender"),)),
        "slide-17": (SIX_MONTH_EVIDENCE, (("prior", "prior_experience_years"),)),
        "slide-31": (
            ANNUAL_HISTORY_EVIDENCE,
            (("original hire", "original_hire_tenure"), ("latest hire", "latest_hire_tenure")),
        ),
        "slide-35": (
            ANNUAL_HISTORY_EVIDENCE,
            (("top 10 job levels", "job_level"), ("management level", "management_level"), ("level grouped", "level_grouped")),
        ),
        "slide-38": (ANNUAL_HISTORY_EVIDENCE, (("compensation grade", "compensation_grade"),)),
        "slide-39": (ANNUAL_HISTORY_EVIDENCE, (("compa_ratio", "comp_ratio_band"), ("compa ratio", "comp_ratio_band"))),
    }

    if stage_id == "slide-11":
        evidence = load_aggregate_evidence(JOB_FAMILY_EVIDENCE)
        lookup = {
            canonical_label(str(row["category_label"])): (
                percentage_from_counts(row["voluntary_exit_count"], row["baseline_employee_count"]),
                "publishable",
            )
            for row in evidence.get("rows", [])
        }
        return _rates_from_labels(stage, matches, lookup)

    if stage_id == "slide-14":
        rows = aggregate_metric_lookup(SIX_MONTH_EVIDENCE, "work_arrangement")
        evidence = load_aggregate_evidence(SIX_MONTH_EVIDENCE)
        all_rows = [row for row in evidence.get("rows", []) if row.get("metric") == "work_arrangement"]
        other_rows = [
            row
            for row in all_rows
            if canonical_label(str(row.get("category", "")))
            not in {canonical_label("Onsite"), canonical_label("Interim Modified – Short-Term Remote Work")}
        ]
        other_rate = percentage_from_counts(
            sum(int(row["voluntary_exits"]) for row in other_rows),
            sum(int(row["employee_snapshot_count"]) for row in other_rows),
        )
        expected = [
            rows.get(canonical_label("Onsite"), (None, ""))[0],
            rows.get(canonical_label("Interim Modified – Short-Term Remote Work"), (None, ""))[0],
            other_rate,
        ]
        return _rates_from_ordered_values(matches, expected)

    if stage_id == "slide-37":
        evidence = load_aggregate_evidence(LAYERS_EVIDENCE)
        lookup = {
            canonical_label(str(row["label"])): (
                percentage_from_counts(row["voluntary_exits"], row["employee_count"]),
                str(row.get("publication_status", "publishable")),
            )
            for row in evidence.get("distribution", [])
        }
        return _rates_from_labels(stage, matches, lookup)

    if stage_id == "slide-39":
        lookup = aggregate_metric_lookup(ANNUAL_HISTORY_EVIDENCE, "comp_ratio_band")
        band_order = ("≤ 0", "> 0–< 0.8", "0.8–< 0.9", "0.9–< 1", "1–< 1.1", "1.1–< 1.2", "≥ 1.2")
        values = [lookup.get(canonical_label(label), (None, ""))[0] for label in band_order]
        return _rates_from_ordered_values(matches, values + values)

    rule = heading_metric_rules.get(stage_id)
    if rule is None:
        return None
    path, heading_rules = rule
    lookups = {metric: aggregate_metric_lookup(path, metric) for _, metric in heading_rules}
    values: list[Decimal | None] = []
    for match in matches:
        heading = source_panel_heading(stage, match) or ""
        metric = next((candidate for text, candidate in heading_rules if text in heading), None)
        label = source_rate_label(stage, match)
        record = None if metric is None or label is None else lookups[metric].get(label)
        if record is None or record[1] != "publishable" or not source_rate_matches_evidence(match, record[0]):
            values.append(None)
        else:
            values.append(record[0])
    return values


def _rates_from_labels(
    stage: str,
    matches: list[re.Match[str]],
    lookup: dict[str, tuple[Decimal, str]],
) -> list[Decimal | None]:
    values: list[Decimal | None] = []
    for match in matches:
        label = source_rate_label(stage, match)
        record = None if label is None else lookup.get(label)
        if record is None or record[1] != "publishable" or not source_rate_matches_evidence(match, record[0]):
            values.append(None)
        else:
            values.append(record[0])
    return values


def _rates_from_ordered_values(matches: list[re.Match[str]], values: list[Decimal | None]) -> list[Decimal | None]:
    if len(matches) != len(values):
        return [None] * len(matches)
    return [rate if rate is not None and source_rate_matches_evidence(match, rate) else None for match, rate in zip(matches, values)]


def source_rate_pills(stage: str) -> list[re.Match[str]]:
    return list(RATE_PILL_TOKEN.finditer(stage))


def restore_rate_precision_and_apply_policy(
    deck: str,
    source: str,
    policy: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Restore V7 rate labels and apply V8 color semantics from raw evidence."""
    target_stages, _, _ = stage_map(deck)
    source_stages, _, _ = stage_map(source)
    source_references = policy["reference_sources"]
    stage_defaults = policy.get("stage_default_reference", {})
    mixed_stages = set(policy.get("mixed_or_derived_stages", []))
    outcome: dict[str, Any] = {"colored_pills": 0, "gray_pills": 0, "stages": {}}

    for stage_id, target_stage in target_stages.items():
        if stage_id not in source_stages:
            continue
        target_matches = source_rate_pills(target_stage)
        source_matches = source_rate_pills(source_stages[stage_id])
        if not target_matches:
            continue
        # V8-owned stages can intentionally have a different rate structure.
        if len(target_matches) != len(source_matches):
            continue
        reference_id = stage_defaults.get(stage_id)
        reference_rate = None if reference_id is None else Decimal(str(source_references[reference_id]["rate_percent"]))
        is_mixed = stage_id in mixed_stages
        raw_rates = raw_evidence_rates_for_stage(stage_id, source_stages[stage_id])
        has_validated_rate = bool(raw_rates) and any(rate is not None for rate in raw_rates)
        comparable = not is_mixed and reference_id is not None and has_validated_rate
        rendered: list[str] = []
        cursor = 0
        for rate_index, (target_match, source_match) in enumerate(zip(target_matches, source_matches)):
            rendered.append(target_stage[cursor : target_match.start()])
            source_attributes = source_match.group("attrs")
            source_value = source_match.group("value")
            rate = None if raw_rates is None else raw_rates[rate_index]
            is_exploratory = "internal-small-cohort" in source_attributes or "exploratory" in source_attributes
            color_class = attrition_color_class(
                rate if comparable and not is_exploratory else None,
                reference_rate if comparable and not is_exploratory else None,
                policy,
            )
            marker_reference = reference_id if comparable and rate is not None and not is_exploratory else None
            attributes = with_rate_marker(replace_rate_class(source_attributes, color_class), reference_id=marker_reference)
            rendered.append(f"<{source_match.group('tag')}{attributes}>{source_value}</{source_match.group('tag')}>")
            cursor = target_match.end()
            if color_class == policy["states"]["not_comparable"]:
                outcome["gray_pills"] += 1
            else:
                outcome["colored_pills"] += 1
        rendered.append(target_stage[cursor:])
        target_stages[stage_id] = "".join(rendered)
        references: list[dict[str, Any]] = []
        if comparable and reference_id is not None:
            reference = source_references[reference_id]
            references.append(
                {
                    "id": reference_id,
                    "label": None,
                    "rate_percent": str(reference_rate),
                    "voluntary_exits": int(reference["voluntary_exits"]),
                    "eligible_baseline_count": int(reference.get("baseline_employee_snapshots", reference.get("baseline_employee_count"))),
                    "evidence_path": str(reference["evidence_path"]),
                }
            )
        outcome["stages"][stage_id] = {
            "references": references,
            "pills": len(target_matches),
            "validated_rate_pills": 0 if raw_rates is None else sum(rate is not None for rate in raw_rates),
            "status": "comparable" if comparable else ("mixed_or_derived" if is_mixed else "reference_not_validated"),
        }

    first_start = min(match.start() for match in STAGE_RE.finditer(deck))
    last_match = list(STAGE_RE.finditer(deck))[-1]
    ordered = []
    for match in STAGE_RE.finditer(deck):
        stage_id = match.group("id")
        ordered.append(target_stages.get(stage_id, match.group("stage")))
    return deck[:first_start] + "\n\n".join(ordered) + deck[last_match.end() :], outcome


def rebuild_stages(deck: str, replacements: dict[str, str]) -> str:
    matches = list(STAGE_RE.finditer(deck))
    require(matches, "Cannot rebuild V8 stages without slide-stage elements.")
    return deck[: matches[0].start()] + "\n\n".join(
        replacements.get(match.group("id"), match.group("stage")) for match in matches
    ) + deck[matches[-1].end() :]


def reference_record(
    *,
    reference_id: str,
    label: str | None,
    voluntary_exits: int,
    eligible_baseline_count: int | Decimal,
    evidence_path: Path,
    denominator_definition: str = "Eligible baseline employees",
) -> dict[str, Any]:
    denominator = Decimal(str(eligible_baseline_count))
    rate = percentage_from_counts(voluntary_exits, denominator)
    stored_denominator: int | str
    if denominator == denominator.to_integral_value():
        stored_denominator = int(denominator)
    else:
        stored_denominator = str(denominator)
    return {
        "id": reference_id,
        "label": label,
        "rate_percent": str(rate),
        "voluntary_exits": int(voluntary_exits),
        "eligible_baseline_count": stored_denominator,
        "denominator_definition": denominator_definition,
        "evidence_path": str(evidence_path.relative_to(ROOT)).replace("\\", "/"),
        "evidence_sha256": digest(evidence_path),
    }


def policy_reference_record(policy: dict[str, Any], reference_id: str, *, label: str | None = None) -> dict[str, Any]:
    source = policy["reference_sources"][reference_id]
    return reference_record(
        reference_id=reference_id,
        label=label,
        voluntary_exits=int(source["voluntary_exits"]),
        eligible_baseline_count=int(source.get("baseline_employee_snapshots", source.get("baseline_employee_count"))),
        evidence_path=ROOT / str(source["evidence_path"]),
    )


def apply_special_stage_policy(
    deck: str,
    *,
    stage_id: str,
    rates: list[Decimal | None],
    references_by_pill: list[dict[str, Any] | None],
    policy: dict[str, Any],
    audit: dict[str, Any],
) -> str:
    """Override a stage whose panels have their own validated denominators."""
    stages, _, _ = stage_map(deck)
    stage = stages[stage_id]
    matches = source_rate_pills(stage)
    require(len(matches) == len(rates) == len(references_by_pill), f"{stage_id} color evidence does not match its visible rate pills.")
    output: list[str] = []
    cursor = 0
    unique_references: list[dict[str, Any]] = []
    validated_rates: list[Decimal | None] = []
    for match, rate, reference in zip(matches, rates, references_by_pill):
        output.append(stage[cursor : match.start()])
        is_exploratory = "internal-small-cohort" in match.group("attrs") or "exploratory" in match.group("attrs")
        evidence_rate = rate if rate is not None and source_rate_matches_evidence(match, rate) else None
        class_name = attrition_color_class(
            None if is_exploratory else evidence_rate,
            None if is_exploratory or reference is None else Decimal(str(reference["rate_percent"])),
            policy,
        )
        reference_id = None if evidence_rate is None or is_exploratory or reference is None else str(reference["id"])
        attrs = with_rate_marker(replace_rate_class(match.group("attrs"), class_name), reference_id=reference_id)
        output.append(f"<{match.group('tag')}{attrs}>{match.group('value')}</{match.group('tag')}>")
        cursor = match.end()
        validated_rates.append(evidence_rate)
        if reference is not None and not any(existing["id"] == reference["id"] for existing in unique_references):
            unique_references.append(reference)
    output.append(stage[cursor:])
    stages[stage_id] = "".join(output)
    audit["stages"][stage_id] = {
        "references": unique_references,
        "pills": len(matches),
        "validated_rate_pills": sum(rate is not None for rate in validated_rates),
        "status": "comparable",
    }
    return rebuild_stages(deck, stages)


def apply_within_panel_rank_fallbacks(deck: str, policy: dict[str, Any], audit: dict[str, Any]) -> str:
    """Color published numeric rates locally when no pooled reference exists.

    This is a reader-aid fallback, not an attrition benchmark.  It intentionally
    uses the current panel's displayed numeric rates and retains gray for a
    rate without a value, an explicitly exploratory rate, or a known baseline
    below 30 employees.
    """
    source = repair_rate_attribute_markup(SOURCE_DECK.read_text(encoding="utf-8"))
    source_stages, _, _ = stage_map(source)
    stages, _, _ = stage_map(deck)
    unavailable = str(policy["states"]["not_comparable"])
    method = "within-panel-rank"

    for stage_id, groups in RELATIVE_RANK_FALLBACKS.items():
        require(stage_id in source_stages and stage_id in stages, f"Missing V8 fallback-color stage {stage_id}.")
        source_stage = source_stages[stage_id]
        target_stage = stages[stage_id]
        source_matches = source_rate_pills(source_stage)
        target_matches = source_rate_pills(target_stage)
        require(
            len(source_matches) == len(target_matches),
            f"{stage_id} fallback-color pills do not reconcile to frozen V7.",
        )
        referenced_indexes = tuple(index for _, group in groups for index in group)
        require(
            sorted(referenced_indexes) == list(range(len(source_matches))),
            f"{stage_id} fallback-color groups must account for every visible rate pill exactly once.",
        )

        source_rates = [parsed_rate(match.group("value")) for match in source_matches]
        publishable: list[bool] = []
        published_counts: list[int | None] = []
        for match, rate in zip(source_matches, source_rates):
            attributes = match.group("attrs")
            count = baseline_n_from_attributes(attributes)
            published_counts.append(count)
            publishable.append(
                rate is not None
                and "internal-small-cohort" not in attributes
                and "exploratory" not in attributes
                and (count is None or count >= 30)
            )

        color_classes = [unavailable] * len(source_matches)
        group_audit: list[dict[str, Any]] = []
        for label, indexes in groups:
            rates = [source_rates[index] for index in indexes if publishable[index] and source_rates[index] is not None]
            numeric_rates = [rate for rate in rates if rate is not None]
            if numeric_rates:
                for index in indexes:
                    rate = source_rates[index]
                    if publishable[index] and rate is not None:
                        color_classes[index] = within_panel_rank_class(rate, numeric_rates, policy)
            group_audit.append(
                {
                    "label": label,
                    "visible_rate_pills": len(indexes),
                    "ranked_numeric_rate_pills": len(numeric_rates),
                    "minimum_published_rate_percent": None if not numeric_rates else str(min(numeric_rates)),
                    "maximum_published_rate_percent": None if not numeric_rates else str(max(numeric_rates)),
                }
            )

        rendered: list[str] = []
        cursor = 0
        for target_match, source_match, color_class in zip(target_matches, source_matches, color_classes):
            rendered.append(target_stage[cursor : target_match.start()])
            attributes = with_rate_marker(
                replace_rate_class(source_match.group("attrs"), color_class),
                reference_id=None,
                color_method=method if color_class != unavailable else None,
            )
            rendered.append(f"<{source_match.group('tag')}{attributes}>{source_match.group('value')}</{source_match.group('tag')}>")
            cursor = target_match.end()
        rendered.append(target_stage[cursor:])
        stages[stage_id] = "".join(rendered)

        ranked_pills = sum(color_class != unavailable for color_class in color_classes)
        audit["stages"][stage_id] = {
            "references": [],
            "pills": len(source_matches),
            "validated_rate_pills": ranked_pills,
            "published_numeric_rate_pills": sum(rate is not None for rate in source_rates),
            "status": "within_panel_rank",
            "color_method": "Within each chart panel: lowest published numeric rate = green; highest = orange; rates between = blue.",
            "color_method_id": method,
            "rank_groups": group_audit,
            "uncolored_rate_pills": len(source_matches) - ranked_pills,
            "uncolored_rule": "Gray when the published rate is not estimable, is exploratory, or declares a baseline cohort below 30 employees.",
        }

    return rebuild_stages(deck, stages)


def apply_special_color_policies(
    deck: str,
    policy: dict[str, Any],
    audit: dict[str, Any],
    acquisition: dict[str, Any],
) -> str:
    """Apply panel-level references where a slide contains multiple cohorts."""
    source = SOURCE_DECK.read_text(encoding="utf-8")
    source_stages, _, _ = stage_map(source)

    # Slide 3: each August applicant panel has a different applicant cohort.
    application = load_aggregate_evidence(APPLICATION_EVIDENCE)
    application_rows = [row for row in application["rows"] if int(row["cutoff_year"]) in {2025, 2026}]
    application_rows.sort(key=lambda row: (int(row["cutoff_year"]), int(row["bucket_order"])))
    application_refs: dict[int, dict[str, Any]] = {}
    for year in (2025, 2026):
        rows = [row for row in application_rows if int(row["cutoff_year"]) == year]
        application_refs[year] = reference_record(
            reference_id=f"applications-aug-{year}",
            label=f"Aug {year}",
            voluntary_exits=sum(int(row["voluntary_exit_count"]) for row in rows),
            eligible_baseline_count=int(rows[0]["total_distinct_applicants"]),
            evidence_path=APPLICATION_EVIDENCE,
        )
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-3",
        rates=[
            percentage_from_counts(row["voluntary_exit_count"], row["distinct_applicant_count"])
            if int(row["distinct_applicant_count"]) >= 30
            else None
            for row in application_rows
        ],
        references_by_pill=[application_refs[int(row["cutoff_year"])] for row in application_rows],
        policy=policy,
        audit=audit,
    )

    # Slide 15: its two panels use different windows and baseline cohorts.
    six_month = load_aggregate_evidence(SIX_MONTH_EVIDENCE)
    engineering = [row for row in six_month["rows"] if row.get("metric") == "engineering"]
    engineering.sort(key=lambda row: canonical_label(str(row["category"])))
    engineering_by_label = {canonical_label(str(row["category"])): row for row in engineering}
    cto = load_aggregate_evidence(CTO_ORG_EVIDENCE)
    cto_rows = list(cto["rows"])
    cto_ref = reference_record(
        reference_id="cto-org-annual",
        label="CTO / Corp Fxn & BU",
        voluntary_exits=int(cto["metrics"]["total_voluntary_exit_count"]),
        eligible_baseline_count=int(cto["metrics"]["eligible_employee_count"]),
        evidence_path=CTO_ORG_EVIDENCE,
    )
    six_ref = policy_reference_record(policy, "six_month_24_snapshot", label="Engineering split")
    engineering_rates = [
        percentage_from_counts(engineering_by_label[canonical_label(label)]["voluntary_exits"], engineering_by_label[canonical_label(label)]["employee_snapshot_count"])
        for label in ("Engineering", "Non_Engineering")
    ]
    cto_rates = [percentage_from_counts(row["voluntary_exits"], row["eligible_employee_count"]) for row in cto_rows]
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-15",
        rates=engineering_rates + cto_rates,
        references_by_pill=[six_ref, six_ref, cto_ref, cto_ref],
        policy=policy,
        audit=audit,
    )

    # Slide 16: Rehire and not-a-rehire share a fiscal-year panel reference.
    rehire = load_aggregate_evidence(REHIRE_EVIDENCE)
    rehire_rows = list(rehire["rows"])
    rehire_rates: list[Decimal | None] = []
    rehire_refs: list[dict[str, Any]] = []
    for fiscal_year in ("2024", "2025", "2026"):
        year_rows = [row for row in rehire_rows if str(row["fiscal_year"]) == fiscal_year]
        year_rows.sort(key=lambda row: 0 if row["rehire_group"] == "Rehire" else 1)
        reference = reference_record(
            reference_id=f"rehire-fy{fiscal_year}",
            label=f"FY{fiscal_year}",
            voluntary_exits=sum(int(row["voluntary_exit_count"]) for row in year_rows),
            eligible_baseline_count=sum(int(row["baseline_employee_count"]) for row in year_rows),
            evidence_path=REHIRE_EVIDENCE,
        )
        for row in year_rows:
            rehire_rates.append(percentage_from_counts(row["voluntary_exit_count"], row["baseline_employee_count"]))
            rehire_refs.append(reference)
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-16",
        rates=rehire_rates,
        references_by_pill=rehire_refs,
        policy=policy,
        audit=audit,
    )

    # The V8-only acquisition slide has two different, explicit references:
    # all eligible baseline employees for the two overall segments, and only
    # the acquired baseline segment for the Top 10 + Other panel.
    acquisition_overall_reference = policy_reference_record(
        policy, "acquisition_overall_annual", label="Overall workforce",
    )
    acquisition_panel_reference = policy_reference_record(
        policy, "acquisition_registered_annual", label="Acquisition recorded",
    )
    acquisition_references = acquisition["color_references"]
    require(
        int(acquisition_references["overall_distribution"]["voluntary_exits"]) == acquisition_overall_reference["voluntary_exits"]
        and int(acquisition_references["overall_distribution"]["eligible_baseline_count"]) == acquisition_overall_reference["eligible_baseline_count"],
        "La referencia general de color de adquisición no coincide con la política.",
    )
    require(
        int(acquisition_references["acquisition_panel"]["voluntary_exits"]) == acquisition_panel_reference["voluntary_exits"]
        and int(acquisition_references["acquisition_panel"]["eligible_baseline_count"]) == acquisition_panel_reference["eligible_baseline_count"],
        "La referencia del panel adquirido no coincide con la política.",
    )
    acquisition_segments = list(acquisition["overall_distribution"])
    acquisition_top_by_label = {str(row["label"]): row for row in acquisition["top_acquisitions"]}
    acquisition_published_top = [acquisition_top_by_label["RF360"], acquisition_top_by_label["Otras adquisiciones"]]
    acquisition_rates = [
        Decimal(str(row["annual_attrition_rate_percent"]))
        for row in acquisition_segments
    ] + [
        Decimal(str(row["annual_attrition"]["annual_attrition_rate_percent"]))
        for row in acquisition_published_top
    ]
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-acquisition",
        rates=acquisition_rates,
        references_by_pill=[acquisition_overall_reference, acquisition_overall_reference, acquisition_panel_reference, acquisition_panel_reference],
        policy=policy,
        audit=audit,
    )
    audit["stages"]["slide-acquisition"]["footer_text"] = (
        "Color references: overall workforce "
        f"{fmt_pct_decimal(Decimal(str(acquisition_overall_reference['rate_percent'])))} · "
        "recorded-acquisition cohort "
        f"{fmt_pct_decimal(Decimal(str(acquisition_panel_reference['rate_percent'])))}. "
        "Green: below reference · Blue: within range · Orange: above reference."
    )

    # Slide 19 shows the same four historical distance bands for All eligible
    # and Onsite snapshots.  Pool each population's four exhaustive calculable
    # bands; the separate current "No calculable" coverage bucket has no rate.
    commute_all = load_aggregate_evidence(COMMUTE_ALL_ELIGIBLE_EVIDENCE)
    commute_onsite = load_aggregate_evidence(COMMUTE_ONSITE_EVIDENCE)

    def commute_display_bands(evidence: dict[str, Any]) -> list[dict[str, Any]]:
        definitions = ((0, 10), (10, 20), (20, 30), (30, None))
        output: list[dict[str, Any]] = []
        for lower, upper in definitions:
            rows = [
                row for row in evidence["bands"]
                if Decimal(str(row["lower_km"])) >= lower
                and (upper is None or Decimal(str(row["lower_km"])) < upper)
            ]
            require(rows, "Commute evidence is missing a visible distance band.")
            output.append(
                {
                    "employee_snapshot_count": sum(int(row["employee_snapshot_count"]) for row in rows),
                    "voluntary_exits": sum(int(row["voluntary_exits"]) for row in rows),
                }
            )
        return output

    commute_all_bands = commute_display_bands(commute_all)
    commute_onsite_bands = commute_display_bands(commute_onsite)
    commute_all_ref = reference_record(
        reference_id="commute-all-eligible-six-month",
        label="All eligible",
        voluntary_exits=sum(int(row["voluntary_exits"]) for row in commute_all_bands),
        eligible_baseline_count=sum(int(row["employee_snapshot_count"]) for row in commute_all_bands),
        evidence_path=COMMUTE_ALL_ELIGIBLE_EVIDENCE,
        denominator_definition="Matched-distance employee snapshots across 24 six-month outcome windows",
    )
    commute_onsite_ref = reference_record(
        reference_id="commute-onsite-six-month",
        label="Onsite",
        voluntary_exits=sum(int(row["voluntary_exits"]) for row in commute_onsite_bands),
        eligible_baseline_count=sum(int(row["employee_snapshot_count"]) for row in commute_onsite_bands),
        evidence_path=COMMUTE_ONSITE_EVIDENCE,
        denominator_definition="Matched-distance Onsite employee snapshots across 24 six-month outcome windows",
    )
    commute_rates: list[Decimal | None] = []
    commute_refs: list[dict[str, Any]] = []
    for all_band, onsite_band in zip(commute_all_bands, commute_onsite_bands):
        commute_rates.extend(
            (
                percentage_from_counts(all_band["voluntary_exits"], all_band["employee_snapshot_count"]),
                percentage_from_counts(onsite_band["voluntary_exits"], onsite_band["employee_snapshot_count"]),
            )
        )
        commute_refs.extend((commute_all_ref, commute_onsite_ref))
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-19",
        rates=commute_rates,
        references_by_pill=commute_refs,
        policy=policy,
        audit=audit,
    )

    # Slide 21: its five displayed themes overlap.  The reference was
    # calculated separately over the deduplicated union of employees in any
    # displayed theme, rather than incorrectly summing row denominators.
    retention_themes = load_aggregate_evidence(QVOICE_RETENTION_THEME_EVIDENCE)
    theme_rows = list(retention_themes["rows"])
    theme_reference = retention_themes.get("reference_cohort", {})
    require(len(theme_rows) == 5, "QVoice theme evidence must contain the five displayed theme cohorts.")
    require(theme_reference.get("reference_id") == "qvoice-theme-union", "QVoice theme evidence is missing its deduplicated union reference.")
    require(
        retention_themes.get("validation", {}).get("reference_cohort_is_deduplicated_union") is True
        and int(retention_themes.get("validation", {}).get("reference_cohort_source_duplicate_employee_count", -1)) == 0,
        "QVoice theme reference cohort did not pass its deduplication audit.",
    )
    require(
        int(theme_reference["matched_employee_count"]) >= 30
        and int(theme_reference["voluntary_exit_count"]) >= 30
        and 0 <= int(theme_reference["voluntary_exit_count"]) <= int(theme_reference["matched_employee_count"]),
        "QVoice theme reference cohort is not publishable.",
    )
    theme_ref = reference_record(
        reference_id=str(theme_reference["reference_id"]),
        label="Any shown theme",
        voluntary_exits=int(theme_reference["voluntary_exit_count"]),
        eligible_baseline_count=int(theme_reference["matched_employee_count"]),
        evidence_path=QVOICE_RETENTION_THEME_EVIDENCE,
    )
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-21",
        rates=[
            percentage_from_counts(row["voluntary_exit_count"], row["matched_employee_count"])
            if row["publication_status"] == "publishable"
            else None
            for row in theme_rows
        ],
        references_by_pill=[theme_ref] * len(theme_rows),
        policy=policy,
        audit=audit,
    )

    # Slides 23 and 24: Favorable / No favorable are mutually exclusive
    # within each item and wave.  Each small panel therefore uses its own
    # pooled valid-response cohort, not the whole workforce or another item.
    response_groups = load_aggregate_evidence(QVOICE_RESPONSE_GROUP_EVIDENCE)

    def grouped_response_reference(
        groups: dict[str, Any], *, reference_id: str, label: str,
    ) -> dict[str, Any]:
        expected_labels = {"Favorable", "No favorable"}
        require(set(groups) == expected_labels, f"{reference_id} must contain only the two response groups.")
        exits = sum(int(groups[group]["voluntary_exit_count"]) for group in expected_labels)
        cohort = sum(int(groups[group]["matched_employee_count"]) for group in expected_labels)
        require(cohort >= 30 and exits >= 30 and 0 <= exits <= cohort, f"{reference_id} is not a publishable response reference.")
        return reference_record(
            reference_id=reference_id,
            label=label,
            voluntary_exits=exits,
            eligible_baseline_count=cohort,
            evidence_path=QVOICE_RESPONSE_GROUP_EVIDENCE,
        )

    intent_rates: list[Decimal | None] = []
    intent_refs: list[dict[str, Any]] = []
    for wave in response_groups["variables"]["intent_to_stay"]:
        year = int(wave["year"])
        panel_groups = [("driver", wave["groups"])] + [(str(key), value["groups"]) for key, value in wave["components"].items()]
        for panel_key, groups in panel_groups:
            reference = grouped_response_reference(
                groups,
                reference_id=f"qvoice-intent-{year}-{panel_key}",
                label=f"{year} {panel_key}",
            )
            for group in ("Favorable", "No favorable"):
                intent_rates.append(percentage_from_counts(groups[group]["voluntary_exit_count"], groups[group]["matched_employee_count"]))
                intent_refs.append(reference)
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-23",
        rates=intent_rates,
        references_by_pill=intent_refs,
        policy=policy,
        audit=audit,
    )
    audit["stages"]["slide-23"]["footer_text"] = (
        "Color reference(s): pooled valid-response cohort for each item and wave "
        "(2024: 4.8–5.0% · 2025: 4.6–4.8% · 2026 YTD: 3.7–3.8%)."
    )

    career_rates: list[Decimal | None] = []
    career_refs: list[dict[str, Any]] = []
    for wave in response_groups["variables"]["career_goals"]:
        year = int(wave["year"])
        reference = grouped_response_reference(
            wave["groups"], reference_id=f"qvoice-career-{year}", label=str(year),
        )
        # The driver and its single source item use the same two response
        # cohorts, so each reference deliberately appears twice in the slide.
        for groups in (wave["groups"], next(iter(wave["components"].values()))["groups"]):
            for group in ("Favorable", "No favorable"):
                career_rates.append(percentage_from_counts(groups[group]["voluntary_exit_count"], groups[group]["matched_employee_count"]))
                career_refs.append(reference)
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-24",
        rates=career_rates,
        references_by_pill=career_refs,
        policy=policy,
        audit=audit,
    )

    # Slide 25 score bands are mutually exclusive and exhaust the published
    # complete-comparable respondent cohort, so the six bands share one YTD
    # reference calculated from their aggregate numerator and denominator.
    qvoice_ytd = load_aggregate_evidence(QVOICE_YTD_GROUP_EVIDENCE)
    score_bands = qvoice_ytd["slides"]["25"]
    score_band_order = ("<50", "50–69", "70–79", "80–89", "90–99", "100")
    require(set(score_bands) == set(score_band_order), "Comparable QVoice score bands do not match the visible slide.")
    score_reference = reference_record(
        reference_id="qvoice-comparable-score-2026-ytd",
        label="2026 YTD score cohort",
        voluntary_exits=sum(int(score_bands[band]["voluntary_exit_count"]) for band in score_band_order),
        eligible_baseline_count=sum(int(score_bands[band]["matched_employee_count"]) for band in score_band_order),
        evidence_path=QVOICE_YTD_GROUP_EVIDENCE,
    )
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-25",
        rates=[percentage_from_counts(score_bands[band]["voluntary_exit_count"], score_bands[band]["matched_employee_count"]) for band in score_band_order],
        references_by_pill=[score_reference] * len(score_band_order),
        policy=policy,
        audit=audit,
    )

    # Slide 26: the three signs are mutually exclusive only within a question.
    heartbeat = load_aggregate_evidence(QVOICE_HEARTBEAT_EVIDENCE)
    heartbeat_rates: list[Decimal | None] = []
    heartbeat_refs: list[dict[str, Any]] = []
    for panel in heartbeat["slide"]["panels"]:
        for question in panel["questions"]:
            segments = list(question["segments"])
            reference = reference_record(
                reference_id=f"heartbeat-{question['question_id']}",
                label=str(question["question_id"]),
                voluntary_exits=sum(int(segment["voluntary_exit_count"]) for segment in segments),
                eligible_baseline_count=sum(int(segment["matched_employee_count"]) for segment in segments),
                evidence_path=QVOICE_HEARTBEAT_EVIDENCE,
            )
            for segment in segments:
                heartbeat_rates.append(percentage_from_counts(segment["voluntary_exit_count"], segment["matched_employee_count"]))
                heartbeat_refs.append(reference)
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-26",
        rates=heartbeat_rates,
        references_by_pill=heartbeat_refs,
        policy=policy,
        audit=audit,
    )

    # Slide 32: the two independent promotion panels have their own cohort rate.
    promotion = load_aggregate_evidence(COMPARABLE_PROMOTION_EVIDENCE)
    promotion_rates: list[Decimal | None] = []
    promotion_refs: list[dict[str, Any]] = []
    panel_specs = (
        ("recorded-promotion", "Recorded promotion", promotion["recorded_promotion_distribution"]),
        ("no-recorded-promotion-proxy", "No recorded promotion proxy", promotion["no_recorded_promotion_role_tenure_proxy_distribution"]),
    )
    for reference_id, label, rows in panel_specs:
        reference = reference_record(
            reference_id=reference_id,
            label=label,
            voluntary_exits=sum(int(row["voluntary_exits"]) for row in rows),
            eligible_baseline_count=sum(int(row["employee_count"]) for row in rows),
            evidence_path=COMPARABLE_PROMOTION_EVIDENCE,
        )
        for row in rows:
            rate = percentage_from_counts(row["voluntary_exits"], row["employee_count"])
            promotion_rates.append(rate if row["publication_status"] == "publishable" else None)
            promotion_refs.append(reference)
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-32",
        rates=promotion_rates,
        references_by_pill=promotion_refs,
        policy=policy,
        audit=audit,
    )

    # Slide 29 contains two independent, exhaustive August-2025 tenure
    # panels.  Each gets the pooled rate for its own six bands.
    tenure = load_aggregate_evidence(TENURE_PANEL_EVIDENCE)
    tenure_rates: list[Decimal | None] = []
    tenure_refs: list[dict[str, Any]] = []
    tenure_specs = (
        ("time_at_detailed_level", "Detailed level"),
        ("time_in_role", "Role tenure"),
    )
    tenure_order = ("<1 year", "1–<2 years", "2–<3 years", "3–<5 years", "5–<10 years", "10+ years")
    for metric, label in tenure_specs:
        rows_by_label = {str(row["category"]): row for row in tenure["annual_rows"] if str(row["metric"]) == metric}
        require(set(rows_by_label) == set(tenure_order), f"{metric} tenure evidence does not match the visible bands.")
        rows = [rows_by_label[band] for band in tenure_order]
        reference = reference_record(
            reference_id=f"tenure-{metric}",
            label=label,
            voluntary_exits=sum(int(row["voluntary_exits"]) for row in rows),
            eligible_baseline_count=sum(int(row["employee_snapshot_count"]) for row in rows),
            evidence_path=TENURE_PANEL_EVIDENCE,
        )
        for row in rows:
            tenure_rates.append(percentage_from_counts(row["voluntary_exits"], row["employee_snapshot_count"]))
            tenure_refs.append(reference)
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-29",
        rates=tenure_rates,
        references_by_pill=tenure_refs,
        policy=policy,
        audit=audit,
    )

    # Slide 34 has two non-overlapping panels.  Rates are based on each
    # panel's aggregated annual exit count over its summed average headcount.
    promotion_tracks = load_aggregate_evidence(PROMOTION_TRACK_EVIDENCE)
    promotion_grades = load_aggregate_evidence(PROMOTION_GRADE_TOP10_EVIDENCE)
    track_rows = list(promotion_tracks["display_rows"])
    grade_rows = list(promotion_grades["top_grade_rows"])
    require(len(track_rows) == 6 and len(grade_rows) == 10, "Promotion-track color evidence is incomplete.")
    track_reference = reference_record(
        reference_id="promotion-pay-tracks",
        label="Pay tracks",
        voluntary_exits=sum(int(row["voluntary_exit_count"]) for row in track_rows),
        eligible_baseline_count=sum(Decimal(str(row["average_monthly_headcount"])) for row in track_rows),
        evidence_path=PROMOTION_TRACK_EVIDENCE,
        denominator_definition="Sum of 12-month average monthly headcount across the displayed pay tracks",
    )
    grade_reference = reference_record(
        reference_id="promotion-top-10-grades",
        label="Top 10 grades",
        voluntary_exits=sum(int(row["voluntary_exit_count"]) for row in grade_rows),
        eligible_baseline_count=sum(Decimal(str(row["average_monthly_headcount"])) for row in grade_rows),
        evidence_path=PROMOTION_GRADE_TOP10_EVIDENCE,
        denominator_definition="Sum of 12-month average monthly headcount across the displayed top-ten grades",
    )
    promotion_rates = [
        percentage_from_counts(row["voluntary_exit_count"], Decimal(str(row["average_monthly_headcount"])))
        for row in track_rows + grade_rows
    ]
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-34",
        rates=promotion_rates,
        references_by_pill=[track_reference] * len(track_rows) + [grade_reference] * len(grade_rows),
        policy=policy,
        audit=audit,
    )

    # The direct-span follow-up is one mutually exclusive reconstructed
    # hierarchy cohort.  Its six bands reconcile to the eligible population.
    direct_span = load_aggregate_evidence(DIRECT_TEAM_SPAN_EVIDENCE)
    span_rows = list(direct_span["bands"])
    span_order = ("1–4", "5–9", "10–14", "15–19", "20–29", "30+")
    require([str(row["label"]) for row in span_rows] == list(span_order), "Direct-span evidence does not match the visible band order.")
    span_reference = reference_record(
        reference_id="direct-team-span",
        label="Direct-report cohort",
        voluntary_exits=sum(int(row["voluntary_exits"]) for row in span_rows),
        eligible_baseline_count=sum(int(row["employee_count"]) for row in span_rows),
        evidence_path=DIRECT_TEAM_SPAN_EVIDENCE,
    )
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-37-span-followup",
        rates=[percentage_from_counts(row["voluntary_exits"], row["employee_count"]) for row in span_rows],
        references_by_pill=[span_reference] * len(span_rows),
        policy=policy,
        audit=audit,
    )

    # Slides 43–49 have a fixed August-2025 baseline and aggregate counts in
    # their source evidence.  Their color references are pooled only within
    # the categories shown in the corresponding chart/panel.
    manager_context = load_aggregate_evidence(MANAGER_CONTEXT_EVIDENCE)
    manager_simple_rows = [
        row for row in manager_context["queries"]["simple_categories"]["rows"]
        if row.get("row_type") == "category"
    ]

    def manager_rows_for(metric: str, order: tuple[str, ...]) -> list[dict[str, Any]]:
        by_category = {str(row["category"]): row for row in manager_simple_rows if str(row.get("metric")) == metric}
        require(set(order) <= set(by_category), f"Manager-context evidence is missing a visible {metric} category.")
        return [by_category[category] for category in order]

    def manager_reference(rows: list[dict[str, Any]], *, reference_id: str, label: str) -> dict[str, Any]:
        return reference_record(
            reference_id=reference_id,
            label=label,
            voluntary_exits=sum(int(row["voluntary_exits"]) for row in rows),
            eligible_baseline_count=sum(int(row["employee_count"]) for row in rows),
            evidence_path=MANAGER_CONTEXT_EVIDENCE,
        )

    office_rows = manager_rows_for(
        "office_site_relationship", ("Same office_site", "Different office_site", "Not comparable / missing site"),
    )
    office_reference = manager_reference(office_rows, reference_id="office-site-relationship", label="Office-site cohort")
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-43",
        rates=[percentage_from_counts(row["voluntary_exits"], row["employee_count"]) for row in office_rows],
        references_by_pill=[office_reference] * len(office_rows),
        policy=policy,
        audit=audit,
    )

    observed_rows = [
        row for row in manager_context["queries"]["manager_observed_expected"]["rows"]
        if row.get("row_type") == "category"
    ]
    observed_order = ("<0.5×", "0.5–<1.0×", "1.0–<1.5×", "≥1.5×")
    observed_by_category = {str(row["category"]): row for row in observed_rows}
    require(set(observed_by_category) == set(observed_order), "Manager observed-to-expected evidence does not match the four visible bands.")
    observed_rows = [observed_by_category[category] for category in observed_order]
    observed_reference = manager_reference(observed_rows, reference_id="manager-observed-expected", label="Observable manager cohort")
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-44",
        rates=[percentage_from_counts(row["voluntary_exits"], row["employee_count"]) for row in observed_rows],
        references_by_pill=[observed_reference] * len(observed_rows),
        policy=policy,
        audit=audit,
    )

    recent_rows = manager_rows_for("recent_team_exits_under_manager", ("0", "1", "2+"))
    recent_reference = manager_reference(recent_rows, reference_id="recent-team-exits", label="Observed direct reports")
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-45",
        rates=[percentage_from_counts(row["voluntary_exits"], row["employee_count"]) for row in recent_rows],
        references_by_pill=[recent_reference] * len(recent_rows),
        policy=policy,
        audit=audit,
    )

    turnover_rows = [
        row for row in manager_context["queries"]["above_average_team_turnover"]["rows"]
        if row.get("row_type") == "category"
    ]
    turnover_order = ("0", "1", "Unknown")
    turnover_by_category = {str(row["category"]): row for row in turnover_rows}
    require(set(turnover_by_category) == set(turnover_order), "Above-average team-turnover evidence does not match the visible bands.")
    turnover_rows = [turnover_by_category[category] for category in turnover_order]
    turnover_reference = manager_reference(turnover_rows, reference_id="above-average-team-turnover", label="Team-context cohort")
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-46",
        rates=[percentage_from_counts(row["voluntary_exits"], row["employee_count"]) for row in turnover_rows],
        references_by_pill=[turnover_reference] * len(turnover_rows),
        policy=policy,
        audit=audit,
    )

    leaving_rows = manager_rows_for("manager_leaving_baseline_6m", ("Not exposed", "Exposed (1+)"))
    leaving_reference = manager_reference(leaving_rows, reference_id="manager-leaving-exposure", label="Exposure cohort")
    leaving_rates = [
        percentage_from_counts(row["voluntary_exits"], row["employee_count"])
        if str(row.get("publication_status")) == "publishable"
        else None
        for row in leaving_rows
    ]
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-47",
        rates=leaving_rates * 2,
        references_by_pill=[leaving_reference] * 4,
        policy=policy,
        audit=audit,
    )

    change_panel_specs = (
        ("All observed manager changes · trailing 6 months", "Observed 6 mo"),
        ("All observed manager changes · trailing 12 months", "Observed 12 mo"),
        ("Sensitivity: exclude same-date transfer/promotion · trailing 6 months", "Sensitivity 6 mo"),
        ("Sensitivity: exclude same-date transfer/promotion · trailing 12 months", "Sensitivity 12 mo"),
    )
    change_rates: list[Decimal | None] = []
    change_refs: list[dict[str, Any]] = []
    for metric, label in change_panel_specs:
        rows = manager_rows_for(metric, ("0", "1", "2", "3+"))
        reference = manager_reference(rows, reference_id=f"manager-changes-{canonical_label(metric)}", label=label)
        for row in rows:
            change_rates.append(percentage_from_counts(row["voluntary_exits"], row["employee_count"]))
            change_refs.append(reference)
    deck = apply_special_stage_policy(
        deck,
        stage_id="slide-49",
        rates=change_rates,
        references_by_pill=change_refs,
        policy=policy,
        audit=audit,
    )

    # The V8-only IOS chart has no inherited span-rate pills, but every reason
    # is measured against the validated all-IOS cohort in the same annual window.
    ios = load_aggregate_evidence(IOS_EVIDENCE)
    total = ios["rows"][0]
    audit["stages"]["slide-5"] = {
        "references": [
            reference_record(
                reference_id="ios-trailing-12m",
                label="All IOS movements",
                voluntary_exits=int(total["annual_voluntary_exit_n"]),
                eligible_baseline_count=int(total["baseline_cohort_n"]),
                evidence_path=IOS_EVIDENCE,
            )
        ],
        "pills": len(ios["rows"]) - 1,
        "validated_rate_pills": sum(row["publication_status"] != "internal_analysis_exception" for row in ios["rows"][1:]),
        "status": "comparable",
    }
    return apply_within_panel_rank_fallbacks(deck, policy, audit)


def summarize_color_classes(deck: str, policy: dict[str, Any]) -> dict[str, int]:
    classes = {name: str(value) for name, value in policy["states"].items()}
    values = {name: 0 for name in classes}
    for match in re.finditer(r'\bclass="(?P<classes>[^"]*)"', deck):
        assigned = set(match.group("classes").split())
        for state, class_name in classes.items():
            if class_name in assigned:
                values[state] += 1
    return values


def append_color_reference_footers(deck: str, policy: dict[str, Any], audit: dict[str, Any]) -> str:
    """Append, never replace, the source footer with the chart reference used."""
    stages, _, _ = stage_map(deck)
    for stage_id, record in audit["stages"].items():
        stage = stages[stage_id]
        references = list(record.get("references", []))
        custom_text = record.get("footer_text")
        if custom_text is not None:
            text = str(custom_text)
        elif references and record["status"] == "comparable":
            entries = []
            for reference in references:
                rate = fmt_pct_decimal(Decimal(str(reference["rate_percent"])))
                label = reference.get("label")
                entries.append(f"{label} {rate}" if label else rate)
            text = f'{html.escape(policy["display"]["footer_prefix"])} ' + " · ".join(entries)
            unmapped = int(record["pills"]) - int(record["validated_rate_pills"])
            if unmapped:
                text += f" · {unmapped} rate label{'s' if unmapped != 1 else ''} gray (not individually validated)"
        elif record["status"] == "within_panel_rank":
            text = (
                "Color scale: within each chart panel, lowest published attrition is green, "
                "highest is orange, and rates between are blue."
            )
            uncolored = int(record.get("uncolored_rate_pills", 0))
            if uncolored:
                text += f" · {uncolored} rate label{'s' if uncolored != 1 else ''} gray (not estimable or cohort below 30)."
        else:
            text = "Color reference: not validated for this chart; rate pills are gray."
        addition = f'<span class="v8-color-reference" data-v8-color-footer="{stage_id}" data-v8-rate-precision="one-decimal"> | {text}</span>'
        source_lines = list(re.finditer(r'(<div class="v6-source-line"[^>]*>.*?)(</div>)', stage, re.S))
        if source_lines:
            last = source_lines[-1]
            stage = stage[: last.start(2)] + addition + stage[last.start(2) :]
        else:
            stage = stage.replace("</article>", f'<p class="v8-color-reference v8-color-reference-standalone" data-v8-color-footer="{stage_id}" data-v8-rate-precision="one-decimal">{text}</p></article>', 1)
        stages[stage_id] = stage
    first_start = min(match.start() for match in STAGE_RE.finditer(deck))
    last_match = list(STAGE_RE.finditer(deck))[-1]
    return deck[:first_start] + "\n\n".join(stages.get(match.group("id"), match.group("stage")) for match in STAGE_RE.finditer(deck)) + deck[last_match.end() :]


def validate_color_policy_output(deck: str, policy: dict[str, Any], audit: dict[str, Any]) -> None:
    stages, _, _ = stage_map(deck)
    rate_pills = [pill for html_stage in stages.values() for pill in source_rate_pills(html_stage)]
    require(rate_pills, "V8 has no recognizable attrition-rate pills.")
    require(all('data-v8-rate-precision="one-decimal"' in pill.group("attrs") for pill in rate_pills), "Every V8 attrition-rate pill must preserve one decimal.")
    ios_stage_html = stages["slide-5"]
    ios_rate_elements = re.findall(r'<div class="v8-ios-rate[^>]*>', ios_stage_html)
    require(len(ios_rate_elements) == 6 and all('data-v8-rate-precision="one-decimal"' in element for element in ios_rate_elements), "V8 IOS reason rates are missing a one-decimal marker.")
    require('data-v8-color-footer=' in deck, "V8 color-reference footers are missing.")
    class_counts = summarize_color_classes(deck, policy)
    audit["class_counts"] = class_counts
    audit["colored_pills"] = class_counts["below_reference"] + class_counts["within_reference"] + class_counts["above_reference"]
    audit["gray_pills"] = class_counts["not_comparable"]
    require(audit["colored_pills"] > 0, "V8 attrition-color policy did not color any comparable pill.")
    require(audit["gray_pills"] > 0, "V8 attrition-color policy must fail closed for mixed or exploratory pills.")
    for state in ("below_reference", "within_reference", "above_reference", "not_comparable"):
        require(policy["states"][state] in deck, f"V8 attrition-color state {state} is not rendered.")


def color_evidence_artifact(policy: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    """Persist aggregate provenance for every visible color-reference decision."""
    policy_sources = []
    for source_id, source in policy["reference_sources"].items():
        evidence_path = ROOT / str(source["evidence_path"])
        policy_sources.append(
            {
                "id": source_id,
                "voluntary_exits": int(source["voluntary_exits"]),
                "eligible_baseline_count": int(source.get("baseline_employee_snapshots", source.get("baseline_employee_count"))),
                "rate_percent": str(Decimal(str(source["rate_percent"]))),
                "outcome_window": source["outcome_window"],
                "evidence_path": str(evidence_path.relative_to(ROOT)).replace("\\", "/"),
                "evidence_sha256": digest(evidence_path),
            }
        )
    return {
        "artifact_type": "attrition_color_reference_audit",
        "version": 3,
        "artifact_classification": "internal_analysis",
        "deliverable_mode": "internal_analysis",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Document the comparable-cohort references and within-panel rank fallback used to classify V8 rate pills without exposing employee-level records.",
        "policy": {
            "path": str(COLOR_POLICY.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(COLOR_POLICY),
            "policy_id": policy["policy_id"],
            "formula": policy["calculation"]["reference_formula"],
            "relative_materiality": policy["calculation"]["relative_materiality"],
            "absolute_materiality_percentage_points": policy["calculation"]["absolute_materiality_percentage_points"],
            "fallback_within_panel_rule": policy["calculation"]["fallback_within_panel_rule"],
            "fallback_color_scope": policy["calculation"]["fallback_color_scope"],
            "classification_precision": policy["calculation"]["rate_precision"],
            "display_decimal_places": policy["display"]["rate_decimal_places"],
        },
        "policy_reference_sources": policy_sources,
        "stage_color_audit": audit["stages"],
        "class_counts": audit["class_counts"],
        "validation": {
            "all_recognized_rate_pills_marked_one_decimal": "pass",
            "comparable_color_pills_use_aggregate_reference": "pass",
            "within_panel_rank_pills_use_published_numeric_rates_only": "pass",
            "unvalidated_or_exploratory_or_subthreshold_pills_fail_closed_to_gray": "pass",
            "no_employee_rows_or_identifiers_persisted": "pass",
        },
        "privacy": {
            "aggregate_only": True,
            "employee_rows_persisted": False,
            "employee_ids_persisted": False,
            "exact_compensation_values_persisted": False,
        },
        "outcome": "pass",
    }


def load_comparable_promotion_evidence() -> dict[str, Any]:
    """Verify the fixed-baseline cohort contract inherited unchanged from V7."""
    evidence = json.loads(COMPARABLE_PROMOTION_EVIDENCE.read_text(encoding="utf-8"))
    authorization = json.loads(COMPARABLE_PROMOTION_AUTHORIZATION.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "Comparable promotion-cohort evidence did not pass validation.")
    require(evidence.get("artifact_classification") == "internal_analysis", "Comparable promotion evidence must be internal aggregate analysis.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "Comparable promotion evidence has the wrong delivery mode.")
    require(authorization.get("status") == "approved", "Comparable promotion evidence lacks an approved authorization.")
    require(authorization.get("reporting_mode") == "internal_analysis", "Comparable promotion authorization has the wrong reporting mode.")
    require(authorization.get("small_cell_exception", {}).get("allow_subthreshold_aggregate_buckets") is True, "Comparable promotion authorization does not allow the approved small aggregate cell.")
    evidence_authorization = evidence.get("authorization", {})
    require(
        str(evidence_authorization.get("path", "")).replace("\\", "/") == str(COMPARABLE_PROMOTION_AUTHORIZATION.relative_to(ROOT)).replace("\\", "/"),
        "Comparable promotion evidence references an unexpected authorization.",
    )
    require(evidence_authorization.get("sha256") == digest(COMPARABLE_PROMOTION_AUTHORIZATION), "Comparable promotion authorization hash is invalid.")
    require(evidence_authorization.get("authorization_id") == authorization.get("authorization_id"), "Comparable promotion authorization identifier is invalid.")
    contract = evidence.get("outcome_contract", {})
    require(contract.get("baseline_snapshot_date") == "2025-08-24", "Promotion cohorts must use the fixed August 2025 baseline.")
    require(contract.get("outcome_window") == "(2025-08-24, 2026-08-23]", "Promotion cohorts must use the fixed annual outcome window.")
    require("is_rf360_yes_no" in str(contract.get("population")), "Comparable promotion cohort must explicitly apply the RF360 exclusion.")
    validation = evidence.get("validation", {})
    for key in (
        "baseline_reconciliation",
        "outcome_reconciliation",
        "snapshot_uniqueness",
        "valid_dates_and_nonnegative_time_in_role",
        "valid_promotion_events_and_no_future_leakage",
        "rf360_exclusion_applied",
    ):
        require(validation.get(key) == "pass", f"Comparable promotion evidence did not pass {key}.")
    expected_bands = {"0\u2013<1 year", "1\u2013<2 years", "2\u2013<3 years", "3\u2013<5 years", "5+ years"}
    for key in ("recorded_promotion_distribution", "no_recorded_promotion_role_tenure_proxy_distribution"):
        rows = evidence.get(key)
        require(isinstance(rows, list) and len(rows) == 5, f"Comparable promotion evidence is missing five {key} bands.")
        require({str(row.get("label")) for row in rows} == expected_bands, f"Comparable promotion evidence has unexpected {key} bands.")
        for row in rows:
            status = str(row.get("publication_status"))
            require(status in {"publishable", "internal_exploratory_small_cohort"}, "Promotion-band publication state is invalid.")
            require(row.get("annual_attrition_rate_percent") is not None, "Promotion band lacks its annual rate.")
            if status == "publishable":
                require(int(row.get("employee_count", 0)) >= 30, "A published promotion band has n<30.")
            else:
                require(int(row.get("employee_count", 30)) < 30, "An internal exploratory promotion band must be below n=30.")
                require(row.get("display_note"), "An internal exploratory promotion band lacks its display limitation.")
    totals = evidence.get("cohort_totals", {})
    require(
        int(totals.get("baseline_population", 0))
        == int(totals.get("recorded_promotion", 0))
        + int(totals.get("no_recorded_promotion_role_tenure_proxy", 0))
        + int(totals.get("declared_exclusions", 0)),
        "Comparable promotion cohort totals do not reconcile.",
    )
    encoded = json.dumps(evidence, ensure_ascii=False).lower()
    for prohibited in ('"employee_id"', '"manager_employee_id"', '"manager_name"', '"term_date"', '"promotion_date"'):
        require(prohibited not in encoded, f"Comparable promotion evidence must not persist {prohibited}.")
    return evidence


def rate_class(rate: float | None, status: str) -> str:
    if status == "internal_exploratory_small_cohort":
        return "exploratory"
    if rate is None:
        return ""
    if rate <= 4.0:
        return "low"
    if rate >= 7.0:
        return "high"
    return ""


def bar_row(row: dict[str, Any], max_count: int, *, compact: bool = False) -> str:
    count = int(row["employee_count"])
    label = html.escape(str(row["label"]))
    share = 100.0 * count / max_count if max_count else 0.0
    row_class = " compact" if compact else ""
    fill_class = ""
    if label.startswith("No promotion"):
        fill_class = " no-event"
    elif label.startswith("History predates"):
        fill_class = " history"
    status = str(row.get("publication_status", "publishable"))
    rate = row.get("annual_attrition_rate_percent")
    if status == "internal_exploratory_small_cohort":
        rate_text = f"Exploratory · n={fmt_count(int(row['annual_baseline_employee_count']))}"
    else:
        rate_text = f"{fmt_pct(float(rate))} · {fmt_count(int(row['annual_voluntary_exits']))} exits"
    return (
        f'<div class="v8-promotion-row{row_class}"><div class="v8-promotion-label">{label}</div>'
        f'<div class="v8-promotion-track"><div class="v8-promotion-fill{fill_class}" style="width:{share:.1f}%"></div></div>'
        f'<div class="v8-promotion-count">n={fmt_count(count)}</div>'
        f'<div class="v8-promotion-rate {rate_class(None if rate is None else float(rate), status)}">{rate_text}</div></div>'
    )


def intro_stage() -> str:
    prioritized = ("IOS movement", "Region", "Work arrangement", "Engineering", "Rehire", "Adquisiciones y attrition", "Experience", "Commute", "QVoice", "Career progression", "Layers, span & comp ratio", "Manager signals")
    other = ("Applications", "Location & office", "Team-turnover checks", "Job family & gender", "Supporting QVoice", "Level & compensation context", "Manager support fields")
    chips = lambda values: "".join(f'<span class="v8-topic">{html.escape(value)}</span>' for value in values)
    return f'''<div class="slide-stage" id="slide-1" data-v8-overview="true"><div class="slide-heading"><div><h2 class="slide-title-text">Employee characteristics and attrition</h2><p class="slide-subtitle">How the workforce is distributed and how voluntary attrition differs across reviewed characteristics</p></div><span class="badge badge-info">Internal exploratory analysis</span></div><article class="card card-full v8-overview"><div><p class="v8-overview-lead">Which workforce characteristics are worth following up?</p><p class="v8-overview-sub">This deck describes the distribution of reviewed characteristics and, where a comparable cohort is available, the voluntary attrition observed after that cohort. The grouping below reflects review priority, not proof of causality.</p></div><div class="v8-overview-groups"><section class="v8-overview-group priority"><h3>Prioritized variables</h3><p>Topics selected by the reviewers because their patterns merit further follow-up.</p><div class="v8-topic-list">{chips(prioritized)}</div></section><section class="v8-overview-group"><h3>Other reviewed variables</h3><p>Variables inspected in the same exercise that are retained as reference rather than current priorities.</p><div class="v8-topic-list">{chips(other)}</div></section></div><div class="v8-method-strip"><div class="v8-method"><strong>Workforce universe</strong>Active Regular employees at the snapshot named on each slide.</div><div class="v8-method"><strong>Voluntary attrition</strong>Employees who chose to leave; other termination types are excluded.</div><div class="v8-method"><strong>Comparable reference</strong>Voluntary exits ÷ eligible baseline employees for the same chart, not an average of category rates. Charts with the same population and outcome window share a reference.</div><div class="v8-method"><strong>Color meaning</strong>Green: at least 20% and 0.5 points below reference. Blue: within range. Orange: at least 20% and 0.5 points above. Gray: not estimable, exploratory, or not comparable.</div></div></article></div>'''


def format_slide_range(numbers: list[int]) -> str:
    require(numbers, "Un grupo de navegación no puede estar vacío.")
    return str(numbers[0]) if len(numbers) == 1 else f"{numbers[0]}&ndash;{numbers[-1]}"


def reader_sections() -> list[dict[str, Any]]:
    """Derive every visible section range from the single stage order."""
    ordered_sections = [title for title, _ in SECTION_ORDER]
    grouped: dict[str, list[int]] = {title: [] for title in ordered_sections}
    for number, (_, section, _) in enumerate(ORDERED_STAGES, start=1):
        require(section in grouped, f"El slide {number} usa un grupo no configurado: {section}.")
        grouped[section].append(number)
    require(all(grouped[title] for title in ordered_sections), "Todo grupo configurado debe contener al menos un slide.")
    return [
        {
            "title": title,
            "range": format_slide_range(grouped[title]),
            "description": description,
            "numbers": grouped[title],
        }
        for title, description in SECTION_ORDER
    ]


def agenda_stage() -> str:
    sections = reader_sections()
    prioritized_sections = [section for section in sections if section["title"].startswith("Prioritized")]
    other_sections = [section for section in sections if section["title"].startswith("Other reviewed")]
    prioritized_numbers = [number for section in prioritized_sections for number in section["numbers"]]
    other_numbers = [number for section in other_sections for number in section["numbers"]]
    section_copy = {
        "Prioritized · workforce and mobility": ("Fuerza laboral y movilidad", "IOS, región, modalidad de trabajo, ingeniería, rehire, adquisiciones, experiencia y traslado."),
        "Prioritized · QVoice": ("QVoice prioritario", "Comentarios de retención, intención de permanecer, metas de carrera e ítems comparables."),
        "Prioritized · career and organization": ("Carrera y organización", "Nivel, antigüedad, promociones, capas, tamaño de equipo y comp ratio."),
        "Prioritized · manager signals": ("Señales de manager", "Salidas recientes bajo el manager actual y salida del manager."),
    }
    rows = [
        (f"Slides {format_slide_range(prioritized_numbers)}", "Variables prioritarias", "Señales seleccionadas para seguimiento; no prueban causalidad.", "prioritized"),
        *[
            (f"Slides {section['range']}", *section_copy[section["title"]], "prioritized")
            for section in prioritized_sections
        ],
        (f"Slides {format_slide_range(other_numbers)}", "Otras variables revisadas", "Contexto de aplicaciones, lugar de trabajo, QVoice, carrera, compensación y manager.", "other"),
    ]
    rendered = "".join(
        f'<div class="v8-agenda-row{" v8-agenda-row--other" if tone == "other" else ""}"><span class="v8-agenda-range">{a}</span><strong>{b}</strong><span>{c}</span></div>'
        for a, b, c, tone in rows
    )
    return f'''<div class="slide-stage" id="slide-2" data-v8-agenda="true"><div class="slide-heading"><div><h2 class="slide-title-text">Índice</h2><p class="slide-subtitle">Dos grupos de revisión y sus temas relacionados</p></div><span class="badge badge-info">Análisis exploratorio interno</span></div><article class="card card-full v8-agenda"><p class="v8-agenda-intro">“Prioritaria” significa seleccionada para seguimiento; no significa que una variable cause attrition.</p>{rendered}</article></div>'''


def ios_stage(evidence: dict[str, Any], policy: dict[str, Any]) -> str:
    rows = list(evidence["rows"])
    total = rows[0]
    reasons = rows[1:]
    reference_rate = percentage_from_counts(total["annual_voluntary_exit_n"], total["baseline_cohort_n"])
    current_population = int(evidence["metrics"]["current_active_regular_employee_count"])
    maximum_share = max(float(row["current_workforce_share_percent"]) for row in reasons)
    bars: list[str] = []
    for row in reasons:
        share = float(row["current_workforce_share_percent"])
        status = str(row["publication_status"])
        rate = percentage_from_counts(row["annual_voluntary_exit_n"], row["baseline_cohort_n"])
        color_class = attrition_color_class(
            None if status == "internal_analysis_exception" else rate,
            None if status == "internal_analysis_exception" else reference_rate,
            policy,
        )
        if status == "internal_analysis_exception":
            rate_text = f"Exploratory · baseline n={fmt_count(int(row['baseline_cohort_n']))}"
        else:
            rate_text = f"{fmt_pct(rate)} · {fmt_count(int(row['annual_voluntary_exit_n']))} exits"
        bars.append(
            '<div class="v8-ios-row"><div class="v8-ios-label">'
            + html.escape(str(row["short_label"]))
            + '</div><div class="v8-ios-track"><div class="v8-ios-fill" style="width:'
            + f"{100 * share / maximum_share:.1f}%"
            + '"></div></div><div class="v8-ios-current"><strong>'
            + fmt_pct(share)
            + '</strong>n='
            + fmt_count(int(row["current_cohort_n"]))
            + '</div><div class="v8-ios-rate '
            + color_class
            + (' exploratory' if status == "internal_analysis_exception" else '')
            + '" data-v8-rate-precision="one-decimal"'
            + ('' if status == "internal_analysis_exception" else ' data-v8-color-reference="ios-trailing-12m"')
            + '>'
            + rate_text
            + "</div></div>"
        )
    return f'''<div class="slide-stage" id="slide-5" data-v8-ios-trailing-12m="true"><div class="slide-heading"><div><h2 class="slide-title-text">IOS movement events: trailing 12 months</h2><p class="slide-subtitle">Distribution among active Regular employees and annual voluntary attrition by recorded movement reason</p></div><span class="badge badge-info">Annual attrition (12 months)</span></div><article class="card card-full v8-ios-card"><div class="v8-ios-definition"><div><strong>Current distribution:</strong> IOS events recorded in the 12 months through 23 Aug 2026 for active Regular employees.</div><div><strong>Rate labels:</strong> the same 12-month feature at 24 Aug 2025, followed for strict voluntary exits through 23 Aug 2026.</div></div><div class="v8-ios-total"><div><strong>{fmt_pct(float(total['current_workforce_share_percent']))}</strong><span>of current active Regular workforce (n={fmt_count(current_population)}) had any eligible IOS movement</span></div><div><strong>n={fmt_count(int(total['current_cohort_n']))}</strong><span>current employees with any eligible IOS movement</span></div><div><strong>{fmt_pct(float(total['annual_voluntary_attrition_percent']))}</strong><span>annual voluntary attrition · {fmt_count(int(total['annual_voluntary_exit_n']))} exits from baseline n={fmt_count(int(total['baseline_cohort_n']))}</span></div></div><div class="v8-ios-bars">{''.join(bars)}</div><p class="v8-ios-note"><strong>Read carefully:</strong> each bar is a workforce share; rows show recorded reasons and can overlap, so they do not add to the all-IOS total. The downlevel row is exploratory because its annual baseline has fewer than 30 employees. This is descriptive, not causal.</p></article></div>'''


def acquisition_stage(evidence: dict[str, Any]) -> str:
    """Render English reader copy while retaining the frozen Spanish evidence."""
    overall = list(evidence["overall_distribution"])
    top = list(evidence["top_acquisitions"])
    totals = evidence["totals"]
    labels = {
        "Con adquisición registrada": "Acquisition recorded",
        "Sin adquisición registrada": "No acquisition recorded",
        "Otras adquisiciones": "Other acquisitions",
    }
    max_top_count = max(int(row["current_employee_count"]) for row in top)
    acquired_share = percentage_from_counts(overall[0]["current_employee_count"], totals["current_active_regular_employee_count"])
    rate_difference = (
        percentage_from_counts(overall[1]["voluntary_exit_count"], overall[1]["baseline_employee_count"])
        - percentage_from_counts(overall[0]["voluntary_exit_count"], overall[0]["baseline_employee_count"])
    )
    difference_label = format(abs(rate_difference).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP), "f").rstrip("0").rstrip(".")
    difference_direction = "lower" if rate_difference >= 0 else "higher"

    def share_markup(value: Decimal, css_class: str = "") -> str:
        # Distribution percentages are not attrition pills and must keep one
        # decimal through both the static and the runtime deck formatters.
        text = fmt_pct_decimal(value).replace(".0%", "%")
        return f'<span class="{css_class}" data-v8-percent-precision="one-decimal">{text}</span>'

    def numeric_rate(rate: Decimal, *, baseline: int, exits: int, context: str) -> str:
        text = fmt_pct_decimal(rate).replace(".0%", "%")
        description = f"Annual voluntary attrition for {context}: {text}; {fmt_count(exits)} voluntary exits / {fmt_count(baseline)} employees at the 24 Aug 2025 baseline, followed through 23 Aug 2026."
        escaped = html.escape(description, quote=True)
        return (
            '<span class="v8-acquisition-rate attr-mid" data-v8-rate-precision="one-decimal" '
            f'title="{escaped}" aria-label="{escaped}">{text}</span>'
        )

    mix_items: list[str] = []
    rate_cards: list[str] = []
    for row in overall:
        label = labels[str(row["label"])]
        current = int(row["current_employee_count"])
        baseline = int(row["baseline_employee_count"])
        exits = int(row["voluntary_exit_count"])
        share = percentage_from_counts(current, totals["current_active_regular_employee_count"])
        rate = percentage_from_counts(exits, baseline)
        mix_items.append(
            '<div class="v8-acquisition-mix-item">'
            + share_markup(share, "v8-acquisition-mix-value")
            + f'<span class="v8-acquisition-label">{label}</span>'
            + f'<small>{fmt_count(current)} employees</small></div>'
        )
        rate_cards.append(
            '<div class="v8-acquisition-rate-card">'
            + f'<span class="v8-acquisition-label">{label}</span>'
            + numeric_rate(rate, baseline=baseline, exits=exits, context=label)
            + f'<span class="v8-acquisition-baseline">Baseline: {fmt_count(baseline)} employees</span></div>'
        )

    top_rows: list[str] = []
    for row in top:
        label = labels.get(str(row["label"]), str(row["label"]))
        current = int(row["current_employee_count"])
        share = percentage_from_counts(current, overall[0]["current_employee_count"])
        attrition = row["annual_attrition"]
        status = str(attrition["publication_status"])
        if status == "publishable":
            rate_markup = numeric_rate(
                percentage_from_counts(attrition["voluntary_exit_count"], attrition["baseline_employee_count"]),
                baseline=int(attrition["baseline_employee_count"]),
                exits=int(attrition["voluntary_exit_count"]),
                context=label,
            )
        else:
            short_note, note = {
                "no_annual_comparable_cohort": (
                    "No cohort", "No comparable annual cohort: no employees in this acquisition segment at the 24 Aug 2025 baseline."
                ),
                "suppressed_voluntary_events_lt_30": (
                    "Suppressed", "Rate suppressed: fewer than 30 voluntary exits in the annual baseline cohort."
                ),
            }[status]
            escaped_note = html.escape(note, quote=True)
            rate_markup = (
                '<span class="v8-acquisition-rate v8-reference-unavailable" '
                f'title="{escaped_note}" aria-label="{escaped_note}">{short_note}</span>'
            )
        top_rows.append(
            f'<tr data-acquisition-label="{html.escape(label, quote=True)}"><th scope="row">{html.escape(label)}</th>'
            + '<td><div class="v8-acquisition-track" aria-hidden="true"><div class="v8-acquisition-fill" style="width:'
            + f"{Decimal('100') * current / max_top_count:.4f}%"
            + '"></div></div></td>'
            + f'<td class="v8-acquisition-count">{fmt_count(current)}</td>'
            + f'<td class="v8-acquisition-share">{share_markup(share)}</td>'
            + f'<td>{rate_markup}</td></tr>'
        )

    return f'''<div class="slide-stage" id="slide-acquisition" lang="en" data-v8-acquisition-entry="true">
      <div class="slide-heading"><div><h2 class="slide-title-text">Acquisitions and attrition</h2>
        <p class="slide-subtitle">Employees with an acquisition recorded show {difference_direction} observed annual voluntary attrition</p>
      </div><span class="badge badge-info">Annual attrition · 12 months</span></div>
      <article class="card card-full v8-acquisition-card">
        <div class="v8-acquisition-layout">
          <div class="v8-acquisition-summary">
            <section class="v8-acquisition-panel" aria-labelledby="acquisition-workforce-title">
              <header><h3 id="acquisition-workforce-title">Current workforce</h3>
                <p class="v8-acquisition-context">23 Aug 2026 · {fmt_count(int(totals['current_active_regular_employee_count']))} active Regular employees</p></header>
              <div class="v8-acquisition-mix">{''.join(mix_items)}</div>
              <div class="v8-acquisition-composition" aria-hidden="true"><div class="v8-acquisition-composition-fill" style="width:{acquired_share:.6f}%"></div></div>
            </section>
            <section class="v8-acquisition-panel" aria-labelledby="acquisition-attrition-title">
              <header><h3 id="acquisition-attrition-title">Annual voluntary attrition</h3>
                <p class="v8-acquisition-context">24 Aug 2025 cohort → 23 Aug 2026</p></header>
              <div class="v8-acquisition-rate-grid">{''.join(rate_cards)}</div>
              <p class="v8-acquisition-takeaway"><span data-v8-percent-precision="one-decimal">{difference_label} percentage points {difference_direction}</span>
                <small>Unadjusted comparison; does not establish causality.</small></p>
            </section>
          </div>
          <section class="v8-acquisition-panel v8-acquisition-details" aria-labelledby="acquisition-detail-title">
            <header><h3 id="acquisition-detail-title">Largest recorded acquisitions</h3>
              <p class="v8-acquisition-context">Top 10 + Other · shares of the {fmt_count(int(overall[0]['current_employee_count']))} employees with a record today</p></header>
            <table class="v8-acquisition-table" aria-label="Current acquisition headcount, share of recorded acquisitions, and annual voluntary attrition">
              <colgroup><col style="width:28%"><col style="width:28%"><col style="width:11%"><col style="width:11%"><col style="width:22%"></colgroup>
              <thead><tr><th scope="col">Acquisition</th><th scope="colgroup" colspan="2">Current employees</th><th scope="col">Share</th><th scope="col">Annual attrition</th></tr></thead>
              <tbody>{''.join(top_rows)}</tbody>
            </table>
            <p class="v8-acquisition-legend"><strong>No cohort:</strong> absent from the annual baseline.<br><strong>Suppressed:</strong> fewer than 30 voluntary exits.</p>
          </section>
        </div>
        <div class="v8-acquisition-notes">
          <p><strong>Annual rate:</strong> unique voluntary exits / starting cohort. Acquisition status fixed at 24 Aug 2025; exits through 23 Aug 2026. RF360 included.</p>
          <p>“No acquisition recorded” does not confirm hiring route. Baseline reconciliation pending: {fmt_count(int(totals['baseline_active_regular_employee_count']))} now vs {fmt_count(int(evidence['historical_baseline_reconciliation']['previous_deck_baseline_count']))} previously.</p>
        </div>
      </article>
    </div>'''


def promotion_stage(evidence: dict[str, Any]) -> str:
    distribution = list(evidence["display_distribution"])
    no_promo = evidence["no_promotion_recorded_current_episode"]
    levels = list(no_promo["level_grouped"])
    role_time = list(no_promo["time_in_role"])
    relations = {row["label"]: int(row["employee_count"]) for row in no_promo["role_start_vs_current_employment_episode"]}
    alignment = {row["label"]: int(row["employee_count"]) for row in no_promo["stored_time_in_role_vs_date_calculation"]}
    no_promo_count = int(no_promo["employee_count"])
    display_count = int(evidence["metrics"]["display_active_regular_employee_count"])
    baseline_count = int(evidence["metrics"]["baseline_active_regular_employee_count"])
    baseline_exits = int(evidence["metrics"]["baseline_voluntary_exits"])
    main_rows = "".join(bar_row(row, max(int(item["employee_count"]) for item in distribution)) for row in distribution)
    level_rows = "".join(bar_row(row, max(int(item["employee_count"]) for item in levels), compact=True) for row in levels)
    role_rows = "".join(bar_row(row, max(int(item["employee_count"]) for item in role_time), compact=True) for row in role_time)
    with_episode = relations.get("Role began with current employment episode", 0)
    after_episode = relations.get("Role began after current employment episode", 0)
    aligned = alignment.get("Within 3 months", 0)
    return f'''<div class="slide-stage" id="slide-32" data-v8-promotion-review="true"><div class="slide-heading"><div><h2 class="slide-title-text">Time since last promotion</h2><p class="slide-subtitle">Latest recorded promotion, plus current role context for employees without a recorded event</p></div><span class="badge badge-info">Annual attrition (12 months)</span></div><article class="card card-full v8-promotion-card"><div class="v8-promotion-definition"><span><strong>Current distribution:</strong> {fmt_count(display_count)} active Regular employees at 23 Aug 2026.</span><span><strong>Rate labels:</strong> same category for {fmt_count(baseline_count)} employees at 24 Aug 2025, followed through 23 Aug 2026 ({fmt_count(baseline_exits)} voluntary exits overall).</span></div><div class="v8-promotion-layout"><section class="v8-promotion-panel"><div class="v8-promotion-panel-title"><span>Latest recorded promotion in the current employment episode</span><span>Distribution / annual voluntary attrition</span></div><div class="v8-promotion-bars">{main_rows}</div></section><section class="v8-promotion-panel"><div class="v8-promotion-panel-title"><span>No promotion recorded in current episode</span><span>Current role and level context</span></div><div class="v8-no-promo-kpi"><div><strong>{fmt_count(no_promo_count)}</strong><span>{fmt_pct(100.0 * no_promo_count / display_count)} of current active Regular employees</span></div><div><strong>{fmt_count(with_episode)}</strong><span>role began with current employment episode</span></div><div><strong>{fmt_count(aligned)}</strong><span>stored role time within 3 months of date calculation</span></div></div><div class="v8-promotion-right-grid"><div><div class="v8-promotion-panel-title"><span>Current level grouped</span><span>n / annual attrition</span></div><div class="v8-promotion-bars">{level_rows}</div></div><div><div class="v8-promotion-panel-title"><span>Stored time in role</span><span>n / annual attrition</span></div><div class="v8-promotion-bars">{role_rows}</div></div></div></section></div><p class="v8-promotion-source"><strong>Read carefully:</strong> “No promotion recorded” is not “never promoted.” Recorded event history starts in Oct 2016. {fmt_count(after_episode)} of these employees began the current role after their current employment episode; role-start and stored time-in-role comparisons are current-snapshot context only. The 5+ year rate is explicitly exploratory because its annual baseline has n=7.</p></article></div>'''


def nav_html() -> str:
    section_items: dict[str, list[tuple[int, str]]] = {section: [] for section, _ in SECTION_ORDER}
    for index, (_, section, title) in enumerate(ORDERED_STAGES, start=1):
        section_items[section].append((index, title))
    details = []
    for section_index, section_record in enumerate(reader_sections(), start=1):
        section = str(section_record["title"])
        range_label = str(section_record["range"])
        buttons = "".join(
            f'<button class="nav-pill{" pill-active" if number == 1 else ""}" data-slide="{number - 1}">{number}. {html.escape(title)}</button>'
            for number, title in section_items[section]
        )
        details.append(
            f'<details class="nav-section" data-section="{section_index}{" open" if section_index == 1 else ""}">'
            f'<summary><span class="nav-section-title">{html.escape(section)}</span><span class="nav-section-range">{range_label}</span></summary>'
            f'<div class="nav-section-slides">{buttons}</div></details>'
        )
    return '<div class="nav-ctrl" id="slide-nav"><div class="nav-tab">Slides</div><div class="nav-panel"><div class="nav-label">Navigation</div>' + "".join(details) + "</div></div>"


def stage_map(deck: str) -> tuple[dict[str, str], int, int]:
    matches = list(STAGE_RE.finditer(deck))
    require(matches, "V7 source deck has no slide stages.")
    stages = {match.group("id"): match.group("stage") for match in matches}
    require(len(stages) == len(matches), "V7 source deck has duplicate stage IDs.")
    return stages, matches[0].start(), matches[-1].end()


def repair_rate_attribute_markup(deck: str) -> str:
    """Repair the inherited slide-42 rate tags only in the generated V8 copy.

    The frozen V7 file contains three rate pills whose ``title`` attribute
    reaches a newline before its missing closing quote.  One also contains a
    literal ``>``.  Browsers recover inconsistently, and the malformed third
    pill bypasses V8's one-decimal and color handling.  This repair preserves
    the visible source wording while making the HTML attributes valid.
    """
    pattern = re.compile(r'title="(?P<title>[^"]*?)\r?\naria-label="(?P<aria>[^"]*)"', re.S)

    def repair(match: re.Match[str]) -> str:
        title = match.group("title").replace(" >4 h offset", " &gt;4 h offset")
        aria = match.group("aria").replace(" >4 h offset", " &gt;4 h offset")
        return f'title="{title}" aria-label="{aria}"'

    return pattern.sub(repair, deck)


def replace_nav(deck: str, nav: str) -> str:
    start = deck.find('<div class="nav-ctrl" id="slide-nav">')
    end = deck.find('<div class="side-controls" id="theme-selector">', start)
    require(start >= 0 and end > start, "Could not locate the V7 navigation block.")
    return deck[:start] + nav + "\n\n  " + deck[end:]


def build() -> dict[str, Any]:
    source = repair_rate_attribute_markup(SOURCE_DECK.read_text(encoding="utf-8"))
    source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    refresh_acquisition_entry_evidence()
    acquisition = load_acquisition_entry_evidence()
    color_policy = load_color_policy()
    promotion = load_comparable_promotion_evidence()
    ios = json.loads(IOS_EVIDENCE.read_text(encoding="utf-8"))
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    require(ios.get("outcome") == "pass" and ios.get("artifact_classification") == "internal_analysis", "V8 IOS evidence is not approved aggregate internal analysis.")
    require(authorization.get("status") == "approved" and authorization.get("reporting_mode") == "internal_analysis", "V8 authorization is not approved.")
    stages, first_start, last_end = stage_map(source)
    expected_ids = {stage_id for stage_id, _, _ in ORDERED_STAGES}
    expected_source_ids = expected_ids - V8_OWNED_STAGE_IDS
    require(expected_source_ids <= set(stages), f"V7 source deck is missing V8 stages: {sorted(expected_source_ids - set(stages))!r}")
    require(not (V8_OWNED_STAGE_IDS & set(stages)), "V8-owned acquisition slide must not be added to frozen V7.")
    require("slide-27" in stages, "V7 QVoice standardized-within-region stage is missing.")
    source_cover = stages["slide-1"]
    # Keep the cover the reviewers selected in V7.  V8 changes its displayed
    # numbers only through the shared reader-facing precision policy below.
    stages["slide-2"] = agenda_stage()
    stages["slide-3"] = re.sub(r"\bUnknown\b", "Not recorded", stages["slide-3"], flags=re.I)
    stages["slide-5"] = ios_stage(ios, color_policy)
    stages["slide-acquisition"] = acquisition_stage(acquisition)
    ordered_stages = "\n\n".join(stages[stage_id] for stage_id, _, _ in ORDERED_STAGES)
    deck = source[:first_start] + ordered_stages + source[last_end:]
    deck = deck.replace("</style>", V8_CSS + "\n  </style>", 1)
    new_nav = nav_html()
    require(new_nav.count('class="nav-pill') == len(ORDERED_STAGES), "V8 navigation source does not match V8 stages.")
    deck = replace_nav(deck, new_nav)
    deck = deck.replace("<title>Employee Characteristics and Attrition</title>", "<title>Employee Characteristics and Attrition — V8</title>", 1)
    deck = remove_v7_dynamic_number_formatter(deck)
    deck = normalize_visible_display_numbers(deck)
    deck = inject_v8_dynamic_number_formatter(deck)
    validate_display_number_policy(deck)
    deck, color_audit = restore_rate_precision_and_apply_policy(deck, source, color_policy)
    deck = apply_special_color_policies(deck, color_policy, color_audit, acquisition)
    deck = append_color_reference_footers(deck, color_policy, color_audit)
    validate_color_policy_output(deck, color_policy, color_audit)
    generated_stages, _, _ = stage_map(deck)
    require(
        generated_stages["slide-1"] == normalize_visible_display_numbers(source_cover),
        "V8 must inherit the V7 cover without substituting an alternate overview layout.",
    )
    require(deck.count('class="slide-stage"') == len(ORDERED_STAGES), "V8 stage count is not contiguous after reordering.")
    require("QVoice scores standardized within region" not in deck, "Removed QVoice standardized-within-region stage is still visible.")
    promotion_stage = stages["slide-32"]
    require('data-v7-promotion-comparable-cohorts="true"' in promotion_stage, "V8 must inherit the comparable promotion-cohort slide from V7.")
    require("Time since latest recorded promotion" in promotion_stage, "V8 recorded-promotion panel is missing.")
    require("People with no recorded promotion" in promotion_stage, "V8 no-recorded-promotion panel is missing.")
    require(
        re.search(r"not.{0,12}never promoted", promotion_stage, flags=re.I | re.S) is not None,
        "V8 promotion slide must clearly distinguish missing recorded history from never promoted.",
    )
    require(promotion_stage.count("v7-promotion-comparable-row") == 10, "V8 promotion slide must retain five temporal bands per panel.")
    require("v8-promotion-review" not in promotion_stage, "V8 must not restore the superseded promotion-review visual.")
    for key in ("recorded_promotion_distribution", "no_recorded_promotion_role_tenure_proxy_distribution"):
        for row in promotion[key]:
            label = html.escape(str(row["label"]))
            require(label in promotion_stage, f"V8 promotion slide is missing the {label} band.")
            require(f"n={int(row['employee_count']):,}" in promotion_stage, f"V8 promotion slide is missing the {label} cohort count.")
    require("Not recorded" in stages["slide-3"], "V8 Applied to a job slide must replace Unknown.")
    require("YTD" not in stages["slide-5"], "V8 IOS slide must not retain a partial-year YTD label.")
    require("trailing 12 months" in stages["slide-5"], "V8 IOS slide must state its trailing-12-month definition.")
    acquisition_stage_html = generated_stages["slide-acquisition"]
    acquisition_pills = source_rate_pills(acquisition_stage_html)
    require(len(acquisition_pills) == 4, "El slide de adquisición debe mostrar cuatro tasas numéricas publicables.")
    require(all('data-v8-rate-precision="one-decimal"' in pill.group("attrs") for pill in acquisition_pills), "Las tasas de adquisición no conservan un decimal.")
    require(acquisition_stage_html.count("v8-reference-unavailable") == 9, "Las tasas no comparables o suprimidas de adquisición deben permanecer grises.")
    require("Rate suppressed: fewer than 30 voluntary exits" in acquisition_stage_html, "El slide de adquisición debe explicar la supresión.")
    require("No comparable annual cohort" in acquisition_stage_html, "El slide de adquisición debe explicar las cohortes no comparables.")
    require('lang="en"' in acquisition_stage_html, "El slide de adquisición debe usar el idioma solicitado por el usuario.")
    require("45,002" in acquisition_stage_html and "45,003" in acquisition_stage_html, "El slide de adquisición debe documentar la diferencia basal.")
    require(
        all(parsed_rate(pill.group("value")) != Decimal("0") for pill in acquisition_pills),
        "El slide de adquisición no debe convertir tasas no publicables en cero.",
    )
    color_evidence = color_evidence_artifact(color_policy, color_audit)
    archived_prior_v8 = archive_current_v8()
    OUTPUT_DECK.write_text(deck, encoding="utf-8")
    COLOR_EVIDENCE.write_text(json.dumps(color_evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "artifact_type": "internal_attrition_distribution_deck",
        "version": 8,
        "artifact_classification": "internal_analysis",
        "deliverable_mode": "internal_analysis",
        "source": {
            "deck": str(SOURCE_DECK.relative_to(ROOT)).replace("\\", "/"),
            "deck_sha256": digest(SOURCE_DECK),
            "manifest": str(SOURCE_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
            "manifest_sha256": digest(SOURCE_MANIFEST),
            "source_version": source_manifest.get("version", 7),
        },
        "output": {
            "deck": str(OUTPUT_DECK.relative_to(ROOT)).replace("\\", "/"),
            "deck_sha256": digest(OUTPUT_DECK),
            "visible_stage_count": len(ORDERED_STAGES),
            "navigation_count": len(ORDERED_STAGES),
        },
        "removed_visible_stage": {
            "source_stage_id": "slide-27",
            "title": "QVoice scores standardized within region",
            "reason": "Removed at reviewer request.",
        },
        "reader_groups": [
            {"title": section["title"], "range": section["range"], "description": section["description"]}
            for section in reader_sections()
        ],
        "ordered_stages": [
            {"slide_number": number, "source_stage_id": stage_id, "group": group, "title": title}
            for number, (stage_id, group, title) in enumerate(ORDERED_STAGES, start=1)
        ],
        "prioritization_rule": "Slides marked by the reviewers are grouped as Prioritized variables. The grouping expresses follow-up priority, not causal proof; all other reviewed variable slides are retained as Other reviewed variables.",
        "promotion_comparable_cohorts_evidence": {
            "path": str(COMPARABLE_PROMOTION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(COMPARABLE_PROMOTION_EVIDENCE),
            "baseline_snapshot": promotion["outcome_contract"]["baseline_snapshot_date"],
            "outcome_window": promotion["outcome_contract"]["outcome_window"],
            "cohort_totals": promotion["cohort_totals"],
            "declared_exclusions": promotion["declared_exclusions"],
            "small_cohort_display": promotion["validation"]["internal_exploratory_small_cohort_rows"],
            "evidence_authorization": promotion["authorization"],
            "rendering": "Slide-32 structure and evidence are inherited from validated V7; V8 applies only its documented reader-facing number precision policy.",
        },
        "ios_trailing_12m_evidence": {
            "path": str(IOS_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(IOS_EVIDENCE),
            "current_active_regular_employees": ios["metrics"]["current_active_regular_employee_count"],
            "baseline_active_regular_employees": ios["metrics"]["baseline_active_regular_employee_count"],
            "current_all_ios_movement_count": ios["metrics"]["current_all_ios_movement_count"],
        },
        "acquisition_entry_evidence": {
            "path": str(ACQUISITION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(ACQUISITION_EVIDENCE),
            "artifact_classification": acquisition["artifact_classification"],
            "outcome": acquisition["outcome"],
            "current_snapshot": acquisition["dates"]["current_snapshot"],
            "baseline_snapshot": acquisition["dates"]["baseline_snapshot"],
            "outcome_window": acquisition["dates"]["outcome_window"],
            "current_active_regular_employees": acquisition["totals"]["current_active_regular_employee_count"],
            "baseline_active_regular_employees": acquisition["totals"]["baseline_active_regular_employee_count"],
            "baseline_voluntary_exits": acquisition["totals"]["baseline_voluntary_exit_count"],
            "color_references": acquisition["color_references"],
            "source_provenance": acquisition["source_provenance"],
            "historical_baseline_reconciliation": acquisition["historical_baseline_reconciliation"],
            "rendering": "Slide-acquisition is regenerated from validated aggregate V4 evidence on every V8 build; V7 remains frozen and does not contain this stage.",
            "reader_language": "en",
            "layout": "Current workforce composition, annual comparison, and Top 10 + Other with a shared suppression legend.",
        },
        "authorization": {
            "path": str(AUTHORIZATION.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(AUTHORIZATION),
            "authorization_id": authorization["authorization_id"],
        },
        "privacy": {
            "aggregate_only": True,
            "employee_rows_persisted": False,
            "employee_ids_persisted": False,
            "exact_compensation_values_persisted": False,
        },
        "display_number_policy": {
            "version": "v8-integer-first-with-one-decimal-attrition-rates",
            "scope": "Reader-visible static text, tooltips, accessibility labels, and dynamically rendered chart text.",
            "rounding": "half_up",
            "absolute_value_at_least_one": "Display as a whole number.",
            "nonzero_absolute_value_below_one": "Display one decimal; use <0.1 (or >-0.1) when rounding would display zero.",
            "zero": "Display as 0.",
            "semantic_cutoffs": "Preserve nonzero decimal boundaries that define a category band.",
            "excluded": "Source evidence, calculations, scripts, CSS geometry, and style attributes retain their stored precision.",
        },
        "attrition_color_policy": {
            "path": str(COLOR_POLICY.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(COLOR_POLICY),
            "policy_id": color_policy["policy_id"],
            "classification_precision": color_policy["calculation"]["rate_precision"],
            "rate_display_decimal_places": color_policy["display"]["rate_decimal_places"],
            "class_counts": color_audit["class_counts"],
        },
        "attrition_color_reference_evidence": {
            "path": str(COLOR_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(COLOR_EVIDENCE),
            "artifact_classification": color_evidence["artifact_classification"],
            "outcome": color_evidence["outcome"],
        },
        "backup_policy": {
            "directory": str(BACKUP_DIRECTORY.relative_to(ROOT)).replace("\\", "/"),
            "registry": str(BACKUP_REGISTRY.relative_to(ROOT)).replace("\\", "/"),
            "archive_before_overwrite": True,
            "deduplicate_by_deck_sha256": True,
            "archived_prior_v8": archived_prior_v8,
        },
        "historical_version_archive": {
            "registry": str(HISTORICAL_VERSION_REGISTRY.relative_to(ROOT)).replace("\\", "/"),
            "scope": "V1-V7 deck HTML, manifests, and version-scoped aggregate evidence when available.",
            "search_instruction": "Use the historical registry to locate an archived version before comparing an earlier deck, slide, manifest, or aggregate evidence artifact.",
        },
        "outcome": "pass",
    }
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = build()
    print(OUTPUT_DECK)
    print(f"visible_stages={result['output']['visible_stage_count']}")
