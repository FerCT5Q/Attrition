"""Build V6 as a compact visual dictionary sourced from the reviewed V5 deck.

V6 changes presentation only. It keeps the aggregate V5 evidence and chart
payloads, but applies the visual grammar approved in Julia's slides 7, 11,
and 17: a short definition/population strip, blue distribution bars, direct
labels, and relative high/mid/low attrition pills.

No employee-level data is read or rendered. Dense category lists remain in
the HTML but only the leading rows are shown in presentation mode; V5 remains
the complete detailed reference.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import build_distribution_html_v5 as v5


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "distribution"
SOURCE = OUT / "attrition-43-variable-distributions-v5.html"
REFERENCE = ROOT / "docs" / "julia" / "attrition-variable-playbook-annual-v1.html"
TEMPLATE = Path(
    r"C:\Users\fcarranz\.codex\skills\html-slide-generator\templates\fullscreen\base-fullscreen.html"
)
TARGET = OUT / "attrition-43-variable-distributions-v6.html"
MANIFEST = OUT / "json" / "attrition-43-variable-distributions-v6-manifest.json"

EXPECTED_SLIDE_COUNT = 50
MAX_VISIBLE_ROWS = 14


@dataclass(frozen=True)
class ReferenceCopy:
    subtitle: str
    definition: str
    population: str
    source_html: str


TITLE_ALIASES = {
    "estimatedcommutedistanceandvoluntaryattrition": "commutedistance",
}


SUBTITLE_OVERRIDES = {
    "evidencefor44attritionmodelcandidates": (
        "A concise dictionary of 44 candidate variables, their distributions, and available attrition evidence"
    ),
    "agenda": "Five sections move from employee activity to workforce, survey, pay, and manager context",
    "appliedtoajob": "Most linked applicants applied to one internal requisition in a fiscal year",
    "appliedtoajobemployeesnapshottrailingsixmonths": (
        "Observed applications are separated from periods with incomplete source coverage"
    ),
    "transferwithinpastyear": "The same rolling 12-month transfer flag is shown at monthly and weekly frequencies",
    "location": "Country shows workforce concentration; attrition pills compare groups within the panel",
    "officesiteandcity": "Stored office site and the derived site-city view answer different location questions",
    "teamturnover": "Recent voluntary exits are shown relative to average team size",
    "unasalidainicialprecedemassalidas": (
        "Employees remaining after a team departure had higher attrition in this cohort; the result is descriptive"
    ),
    "sensibilidadequiposde6pluspersonas": (
        "The descriptive gap is larger in teams with at least six employees"
    ),
    "jobfamily": "August and September are separate snapshots around a reorganization, not a trend",
    "region": "Region, country split, and Labor Market are separate work-location views",
    "gender": "Protected categories remain anonymized for aggregate fairness review",
    "remotehybridinofficestatus": "The stored labels and the two-group exploratory view are not interchangeable",
    "engineeringvsnonengineering": "The stored flag and the organization-derived split are related, not equivalent",
    "rehire": "A source-definition break means the two historical periods should remain separate",
    "yearsofexperiencepriortoqualcomm": (
        "Completed years before Qualcomm are shown in privacy-safe bands"
    ),
    "annualvoluntaryattritionbypriorexperience": (
        "Attrition varies across experience bands; the comparison is descriptive, not causal"
    ),
    "commutedistance": "Distance is a postal-centroid proxy, not commute time or route distance",
    "rtohybridcommentinqvoice": "The chart counts topic mentions; it does not measure sentiment or agreement",
    "retentionconcernsinqvoicecomments": "Themes summarize improvement topics, not individual attrition risk",
    "nonrespondents": "A missing survey link can reflect eligibility or data coverage, not confirmed non-response",
    "intenttostayitems": "Coverage is visible; scale direction and workforce linkage still need validation",
    "careergoalsitem": "Response coverage is shown from 2024 onward; the 2023 item needs source mapping before attrition use",
    "averageofallqvoiceitems": "The comparable score covers complete respondents, not the full workforce",
    "qvoiceheartbeat": "Each item is compared with the respondent's own average, not an external benchmark",
    "standardizednormalizedwithinregion": "Scores show relative standing within each region and wave",
    "timeincurrentjobprofilevscurrentdetailedlevel": (
        "Two stored dates provide useful proxies, but neither is an approved career-tenure definition"
    ),
    "companytenure": "Original-hire tenure and latest-hire or rehire tenure measure different service periods",
    "timesincelastpromotion": "The latest recorded promotion is used; older history is incomplete",
    "promotionhistorybycurrentcompensationgrade": (
        "Counts reflect promotions observed in the current employment period"
    ),
    "howemployeesreachedtheircurrentcompensationgrade": (
        "Observable grade-entry history does not prove how an employee was originally hired"
    ),
    "level": "Three related fields provide different views of seniority",
    "levelgroupedbygradefamily": "Grade family adds context to Level; it is not an official career track",
    "reconstructedmanagerlayerstoceo": "Depth is the number of manager links to the approved CEO position",
    "compensationgrade": "Grades are aggregated, small groups are pooled, and no pay values are shown",
    "compratio": "Comp-ratio bands and the historical attrition pattern are descriptive",
    "withinteamcompensationrange": "Wide ranges are review signals, not pay-equity findings",
    "colocationwithmanager": "Matching assigned sites does not prove physical co-location",
    "residentialdistancefrommanager": "Distance uses postal centroids, not home addresses or travel routes",
    "officesiterelationshipwithmanager": "The comparison uses stored office-site fields only",
    "highriskmanager": "A ratio near 1 means observed exits were close to expected; it is not a manager rating",
    "highturnoverunderthisperson": "Recent team-exit counts provide context, not a manager evaluation",
    "aboveaverageteamturnover": "Most employees remain Unknown because the flag requires sufficient manager history",
    "managerleaving": "The flag records recent exposure to a manager's voluntary departure",
    "managerchange": "This is a dated event flag, not a cumulative career count",
    "numberofmanagerchanges": "Four views compare six- and twelve-month counts with two event definitions",
    "talentindex": "The latest recoverable value covers most employees; its effective date is not confirmed",
    "majorinflectionpoints": "Five change events are observable, but no approved rule defines a major change",
    "etfields": "ET1-ET11 behave like hierarchy references, not confirmed expert-track levels",
}


DEFINITION_OVERRIDES = {
    "appliedtoajob": "Unique internal requisitions observed for each linked applicant in a fiscal year.",
    "appliedtoajobemployeesnapshottrailingsixmonths": (
        "Unique internal requisitions observed in the six months before each workforce snapshot."
    ),
    "teamturnover": "Recent voluntary exits divided by average team size over the same six-month window.",
    "unasalidainicialprecedemassalidas": (
        "Six-month follow-up of employees who remained after one team departure, compared with a reference cohort."
    ),
    "sensibilidadequiposde6pluspersonas": (
        "The same post-departure comparison restricted to teams with at least six employees."
    ),
    "yearsofexperiencepriortoqualcomm": (
        "Completed years of work experience before Qualcomm, grouped into privacy-safe bands."
    ),
    "annualvoluntaryattritionbypriorexperience": (
        "Annual voluntary attrition by the last valid prior-experience band before exit."
    ),
    "commutedistance": "Estimated straight-line distance between residential and office postal centroids.",
    "rtohybridcommentinqvoice": "Counts of RTO, remote/WFH, and hybrid terms in selected QVoice comments.",
    "nonrespondents": "Whether each workforce record links to a QVoice response in the relevant survey wave.",
    "promotionhistorybycurrentcompensationgrade": (
        "Recorded promotion history summarized by current compensation grade."
    ),
    "howemployeesreachedtheircurrentcompensationgrade": (
        "Observable entry into the current grade, with or without a recorded promotion."
    ),
    "reconstructedmanagerlayerstoceo": "Reconstructed manager-link depth to the approved CEO root.",
    "withinteamcompensationrange": "Aggregate pay spread within comparable teams; exact compensation is excluded.",
    "highriskmanager": "Observed voluntary exits divided by expected exits for managers with sufficient history.",
    "highturnoverunderthisperson": "Recent voluntary-exit count under the employee's current manager.",
    "majorinflectionpoints": "Five dated employee-change events available as possible change indicators.",
}


POPULATION_OVERRIDES = {
    "appliedtoajob": "Linked internal applicants in the published fiscal years",
    "appliedtoajobemployeesnapshottrailingsixmonths": "Active regular employees with explicit coverage handling",
    "teamturnover": "Managers and teams meeting the aggregate publication rule",
    "unasalidainicialprecedemassalidas": "Employees remaining after the index event and comparison cohorts",
    "sensibilidadequiposde6pluspersonas": "Employees in teams with at least six members at the index date",
    "annualvoluntaryattritionbypriorexperience": "Employee-year exposure in complete fiscal years",
    "commutedistance": "Onsite active regular employee-snapshots with calculable distance",
    "rtohybridcommentinqvoice": "Selected QVoice comments; aggregate topic counts only",
    "retentionconcernsinqvoicecomments": "Selected QVoice comments; aggregate themes only",
    "nonrespondents": "Active workforce records and linked QVoice respondents",
    "intenttostayitems": "QVoice respondents in each published survey wave",
    "careergoalsitem": "QVoice respondents in published waves from 2024 onward",
    "averageofallqvoiceitems": "Respondents with all 33 comparable items",
    "qvoiceheartbeat": "QVoice respondents with comparable item responses",
    "standardizednormalizedwithinregion": "QVoice respondents within each region and survey wave",
    "promotionhistorybycurrentcompensationgrade": "Active regular employees with observable grade history",
    "withinteamcompensationrange": "Comparable teams meeting the aggregate publication rule",
    "highriskmanager": "Managers with enough history to estimate observed and expected exits",
}


FORCE_SIX_MONTH = {
    "location",
    "officesiteandcity",
    "unasalidainicialprecedemassalidas",
    "sensibilidadequiposde6pluspersonas",
    "jobfamily",
    "region",
    "gender",
    "remotehybridinofficestatus",
    "engineeringvsnonengineering",
    "rehire",
    "yearsofexperiencepriortoqualcomm",
    "commutedistance",
    "companytenure",
    "level",
    "compensationgrade",
    "compratio",
    "managerchange",
}


ANNUAL_ATTRITION = {"annualvoluntaryattritionbypriorexperience"}


V6_CSS = r"""
    /* V6: Julia-approved visual dictionary grammar, sourced from V5 data. */
    .slide-stage { padding:18px 20px 12px; gap:8px; }
    .slide-heading { padding:0 4px 10px; }
    .slide-title-text { font-size:clamp(24px,2.3vw,30px); letter-spacing:-.02em; }
    .slide-subtitle { margin-top:3px; font-size:14px; line-height:1.25; }
    .v6-playbook-card { gap:10px; padding:14px 16px 10px; box-shadow:0 12px 32px rgba(2,6,23,.09); }
    .v6-definition-strip { display:grid; grid-template-columns:1.45fr .8fr; gap:10px; flex:0 0 auto; }
    .v6-definition-strip > div { padding:13px 16px; border:1px solid var(--border-subtle); border-radius:12px; background:color-mix(in oklab,var(--bg-surface-2) 82%,transparent); }
    .v6-mini-label { display:block; margin-bottom:4px; color:var(--text-muted); font-size:11px; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }
    .v6-definition-strip strong { display:block; color:var(--text-main); font-size:17px; line-height:1.22; }
    .v6-chart-area { flex:1; min-height:0; overflow:hidden; }
    .v6-chart-area > * { min-height:0; }
    .v6-chart-area .two-pane,
    .v6-chart-area .prior-experience-annual-layout,
    .v6-chart-area .current-grade-entry-path-tenure-layout,
    .v6-chart-area .commute-attrition-layout { height:100%; min-height:0; display:block; }
    .v6-chart-area .two-chart { height:100%; min-height:0; display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; }
    #slide-12 .v6-chart-area .two-chart { grid-template-columns:repeat(3,minmax(0,1fr)); }
    #slide-12 .region-display-stack { display:contents; }
    .v6-chart-area .chart-card,
    .v6-chart-area .card { min-height:0; height:100%; padding:2px 0 0; gap:6px; border:0; border-radius:0; box-shadow:none; background:transparent; }
    .v6-panel-heading { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:10px; align-items:end; min-height:20px; color:var(--text-muted); font-size:11px; font-weight:800; letter-spacing:.05em; line-height:1.15; text-transform:uppercase; }
    .v6-panel-heading span:last-child { text-align:right; white-space:nowrap; }
    .v6-chart-area .card-title { border-bottom:0; padding:0; margin:0; font-size:11px; line-height:1.15; }
    .v6-chart-area .bar-list { flex:1; min-height:0; justify-content:flex-start; gap:5px; }
    .v6-chart-area .bar-row { position:relative; grid-template-columns:minmax(145px,250px) minmax(80px,1fr) 116px; gap:9px; min-height:28px; padding-right:108px; align-items:center; }
    .v6-chart-area .bar-label { min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--text-main); font-size:13px; font-weight:700; }
    .v6-chart-area .bar-track { height:13px; border-radius:var(--radius-pill); background:color-mix(in oklab,var(--accent) 10%,var(--bg-surface-3)); overflow:hidden; }
    .v6-chart-area .bar-fill { min-width:3px; height:100%; border-radius:var(--radius-pill); background:linear-gradient(90deg,var(--accent),var(--accent-2)); }
    .v6-chart-area .bar-value { color:var(--text-muted); font-size:12px; text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
    .v6-rate-pill,
    .v4-inline-attrition-rate { position:absolute; top:50%; right:0; min-width:92px; transform:translateY(-50%); padding:4px 9px; border-radius:var(--radius-pill); font-size:12px; font-weight:900; font-variant-numeric:tabular-nums; line-height:1.15; text-align:right; white-space:nowrap; }
    .attr-high { color:#c2410c; background:color-mix(in oklab,#f97316 14%,transparent); border:1px solid color-mix(in oklab,#f97316 30%,var(--border-subtle)); }
    .attr-mid { color:var(--accent); background:color-mix(in oklab,var(--accent) 10%,transparent); border:1px solid color-mix(in oklab,var(--accent) 24%,var(--border-subtle)); }
    .attr-low { color:#15803d; background:color-mix(in oklab,#22c55e 11%,transparent); border:1px solid color-mix(in oklab,#22c55e 28%,var(--border-subtle)); }
    .attr-unavailable { min-width:100px; color:var(--text-muted); background:color-mix(in oklab,var(--text-muted) 8%,transparent); border:1px solid var(--border-subtle); }
    body.theme-dark-royal .attr-high, body.theme-dark-carbon .attr-high { color:#fdba74; }
    body.theme-dark-royal .attr-low, body.theme-dark-carbon .attr-low { color:#86efac; }
    .v4-inline-attrition-summary { gap:7px; margin:2px 0 4px; color:var(--text-muted); font-size:11px; }
    .v4-inline-attrition-summary-label { color:var(--text-muted); }
    .v4-inline-attrition-summary-rate { padding:4px 9px; border-radius:var(--radius-pill); font-size:12px; font-weight:900; }
    .v6-hidden-row { display:none !important; }
    .v6-truncation-note { margin-top:auto; padding-top:4px; color:var(--text-muted); font-size:10px; line-height:1.2; }
    .v6-source-line { flex:0 0 auto; padding-top:7px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:11px; line-height:1.2; }
    .v6-source-line strong { color:var(--text-main); }
    .v6-chart-area .chart-footer { display:none !important; }
    .v6-chart-area .scope-note,
    .v6-chart-area .chart-note { font-size:11px; line-height:1.25; }
    .v6-chart-area .trend-bar,
    .v6-chart-area .team-outcome-bar,
    .v6-chart-area .retention-mini-bar,
    .v6-chart-area .qvoice-favorable-bar { background:linear-gradient(180deg,var(--accent-2),var(--accent)); }
    .v6-chart-area .trend-bar-wrap,
    .v6-chart-area .play-track { background:color-mix(in oklab,var(--accent) 10%,var(--bg-surface-3)); }
    #slide-5 .transfer-distribution-wrap { height:100%; }
    #slide-5 .transfer-chart-grid { display:grid; grid-template-rows:repeat(2,minmax(0,1fr)); flex:1 1 auto; min-height:0; }
    #slide-5 .transfer-chart-card { height:auto; min-height:0; padding:5px 0 0; }
    #slide-5 .transfer-chart { height:190px; min-height:190px; flex:0 0 190px; }
    #slide-19 .commute-attrition-card { padding:0; }
    #slide-19 .commute-attrition-chart { height:475px; min-height:475px; flex-basis:475px; }
    #slide-19 .commute-attrition-chart-note { font-size:11px; }
    #slide-33 .promotion-grade-matrix-card,
    #slide-36 .level-grade-family-chart,
    #slide-40 .within-team-compensation-stack { min-height:0; height:100%; }
    .v6-distribution-only .bar-row { grid-template-columns:minmax(145px,250px) minmax(80px,1fr) 116px; padding-right:0; }
    .v6-distribution-only .bar-value { grid-column:3; }
    .v6-intro-card { justify-content:center; gap:30px; padding:48px 66px; }
    .v6-hero-copy h1 { max-width:980px; margin:0 0 12px; color:var(--text-main); font-size:54px; line-height:1.02; letter-spacing:-.035em; }
    .v6-hero-copy p { max-width:1050px; margin:0; color:var(--text-muted); font-size:23px; line-height:1.3; }
    .v6-intro-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
    .v6-intro-grid > div { padding:15px 16px; border:1px solid var(--border-subtle); border-radius:12px; background:color-mix(in oklab,var(--bg-surface-2) 82%,transparent); }
    .v6-intro-grid strong { display:block; color:var(--text-main); font-size:17px; line-height:1.25; }
    .v6-agenda-card { padding:20px 24px; }
    .v6-agenda-card .agenda-vertical { display:flex; flex-direction:column; gap:10px; }
    .v6-agenda-card .agenda-item { display:flex; align-items:baseline; gap:12px; padding:13px 15px; }
    .v6-agenda-card .agenda-num { min-width:90px; font-size:12px; }
    .v6-agenda-card .agenda-item strong { min-width:310px; font-size:15px; }
    .v6-agenda-card .agenda-item span:last-child { font-size:14px; }
    .v6-reading-key { margin-top:4px; padding:10px 12px; border-radius:10px; background:color-mix(in oklab,var(--accent) 8%,transparent); border:1px solid color-mix(in oklab,var(--accent) 22%,var(--border-subtle)); color:var(--text-main); font-size:13px; }
    @media (max-width:900px) {
      .v6-definition-strip { grid-template-columns:1fr; }
      .v6-chart-area .two-chart, #slide-12 .v6-chart-area .two-chart { grid-template-columns:1fr; }
    }
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_text(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def extract_reference_copy(document: str) -> dict[str, ReferenceCopy]:
    _, stages, _ = v5.extract_stages(document)
    result: dict[str, ReferenceCopy] = {}
    for stage in stages:
        title = v5.stage_title(stage)
        subtitle_match = re.search(r'<p class="slide-subtitle">(.*?)</p>', stage, flags=re.S)
        strip_match = re.search(
            r'<div class="definition-strip"><div><span class="mini-label">Definition</span>'
            r'<strong>(.*?)</strong></div><div><span class="mini-label">Population</span>'
            r'<strong>(.*?)</strong></div></div>',
            stage,
            flags=re.S,
        )
        source_match = re.search(r'<div class="source-line">(.*?)</div>', stage, flags=re.S)
        if not strip_match:
            continue
        result[v5.normal(title)] = ReferenceCopy(
            subtitle=clean_text(subtitle_match.group(1)) if subtitle_match else "",
            definition=clean_text(strip_match.group(1)),
            population=clean_text(strip_match.group(2)),
            source_html=source_match.group(1).strip() if source_match else "<strong>Source:</strong> HRDA aggregate evidence.",
        )
    return result


def reference_key(title: str) -> str:
    key = v5.normal(title)
    return TITLE_ALIASES.get(key, key)


def measure_kind(stage: str, key: str) -> str:
    if key in ANNUAL_ATTRITION:
        return "annual"
    if key in FORCE_SIX_MONTH or "v4-inline-attrition-marker" in stage:
        return "six_month"
    if "v4-inline-attrition-unavailable-marker" in stage:
        return "unavailable"
    if key == "teamturnover":
        return "team_history"
    return "distribution"


def badge_markup(kind: str) -> str:
    if kind == "six_month":
        return '<span class="badge badge-info">6-month attrition</span>'
    if kind == "annual":
        return '<span class="badge badge-info">Annual attrition</span>'
    if kind == "unavailable":
        return '<span class="badge badge-neutral">Attrition not estimable</span>'
    if kind == "team_history":
        return '<span class="badge badge-info">6-month team history</span>'
    return '<span class="badge badge-neutral">Distribution</span>'


def source_markup(reference: ReferenceCopy | None, kind: str) -> str:
    if reference:
        base = re.split(r"\.\s*Annual attrition:", reference.source_html, maxsplit=1, flags=re.I)[0].strip()
    else:
        base = "<strong>Source:</strong> HRDA aggregate evidence"
    base = base.rstrip(". ")
    if kind == "six_month":
        suffix = "Six-month attrition is a voluntary exit after the snapshot; aggregate privacy-safe result."
    elif kind == "annual":
        suffix = "Annual attrition is a voluntary exit in the 12 months after the snapshot; aggregate privacy-safe result."
    elif kind == "unavailable":
        suffix = "No publishable time-aligned attrition estimate is available."
    elif kind == "team_history":
        suffix = "The rate describes recent team history and is not an individual prediction."
    else:
        suffix = "Aggregate privacy-safe result; no employee-level rows are shown."
    return f'{base}. {suffix}'


def title_slide() -> str:
    return '''<div class="slide-stage" id="slide-1">
      <div class="slide-heading"><div><h2 class="slide-title-text">Attrition Variable Playbook</h2><p class="slide-subtitle">A concise visual dictionary built from the reviewed V5 evidence</p></div><span class="badge badge-info">Presentation</span></div>
      <article class="card card-full v6-intro-card">
        <div class="v6-hero-copy"><h1>What each variable means<br/>and what the data shows</h1><p>Each slide keeps only the definition, population, distribution, and available attrition comparison needed to read the variable quickly.</p></div>
        <div class="v6-intro-grid">
          <div><span class="v6-mini-label">Population</span><strong>Active regular employees, excluding RF360 unless noted</strong></div>
          <div><span class="v6-mini-label">Outcome</span><strong>Six-month voluntary attrition where V5 has approved evidence</strong></div>
          <div><span class="v6-mini-label">Reading</span><strong>Blue bars show distribution; pills compare attrition within each panel</strong></div>
          <div><span class="v6-mini-label">Use</span><strong>Variable understanding and model-planning discussion</strong></div>
        </div>
      </article>
    </div>'''


def agenda_slide() -> str:
    items = (
        ("Slides 3-10", "Activity and mobility", "Applications, transfers, team exits, and post-exit cohorts."),
        ("Slides 11-19", "Workforce context", "Job family, geography, work arrangement, experience, and commute distance."),
        ("Slides 20-27", "QVoice", "Comment themes, participation, item coverage, and comparable scores."),
        ("Slides 28-38", "Career and compensation", "Tenure, promotions, levels, grade, and aggregate pay context."),
        ("Slides 39-50", "Manager and support signals", "Manager context, change events, talent index, and hierarchy fields."),
    )
    rows = "".join(
        f'<div class="agenda-item"><span class="agenda-num">{number}</span><strong>{title}</strong>'
        f'<span class="agenda-sep">-</span><span>{description}</span></div>'
        for number, title, description in items
    )
    return f'''<div class="slide-stage" id="slide-2">
      <div class="slide-heading"><div><h2 class="slide-title-text">How to use this playbook</h2><p class="slide-subtitle">Move by topic, then read each variable from definition to distribution to attrition</p></div></div>
      <article class="card card-full v6-agenda-card">
        <div class="agenda-vertical">{rows}</div>
        <div class="v6-reading-key">Blue = distribution. Orange = higher attrition within the panel. Green = lower. Blue = middle range. Gray = not estimable.</div>
      </article>
    </div>'''


def quantile(values: list[float], fraction: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def rate_class(value: float, values: list[float]) -> str:
    unique = sorted(set(values))
    if len(unique) <= 1 or max(unique) - min(unique) < 0.2:
        return "attr-mid"
    if len(unique) == 2:
        return "attr-low" if value == unique[0] else "attr-high"
    low = quantile(values, 1 / 3)
    high = quantile(values, 2 / 3)
    if value <= low:
        return "attr-low"
    if value >= high:
        return "attr-high"
    return "attr-mid"


RATE_SPAN = re.compile(
    r'<span class="(?P<class>[^"]*\bv4-inline-attrition-rate\b[^"]*)"(?P<attrs>[^>]*)>(?P<text>.*?)</span>',
    flags=re.S,
)


def classify_rate_spans(fragment: str) -> str:
    numeric_values: list[float] = []
    for match in RATE_SPAN.finditer(fragment):
        text = clean_text(match.group("text")).replace("−", "-")
        number = re.fullmatch(r"(-?\d+(?:\.\d+)?)%", text)
        if number:
            numeric_values.append(float(number.group(1)))

    def replacement(match: re.Match[str]) -> str:
        original_classes = match.group("class").split()
        text = clean_text(match.group("text")).replace("−", "-")
        number = re.fullmatch(r"(-?\d+(?:\.\d+)?)%", text)
        classes = [name for name in original_classes if name not in {"v4-inline-attrition-unavailable"}]
        classes.append("v6-rate-pill")
        if number:
            classes.append(rate_class(float(number.group(1)), numeric_values))
            visible = f"{float(number.group(1)):.1f}%"
        else:
            classes.append("attr-unavailable")
            visible = "Not estimable"
        unique_classes = " ".join(dict.fromkeys(classes))
        return f'<span class="{unique_classes}"{match.group("attrs")}>{visible}</span>'

    return RATE_SPAN.sub(replacement, fragment)


def normalize_bar_card(card: str, kind: str) -> tuple[str, int, int]:
    rows = v5.bar_rows(card)
    if not rows:
        return card, 0, 0

    shares: list[float] = []
    for _, _, row in rows:
        match = re.search(r'<div class="bar-value">\s*(-?\d+(?:\.\d+)?)%', row)
        if match:
            shares.append(float(match.group(1)))
    maximum = max(shares) if shares else 0.0

    rendered: list[str] = []
    position = 0
    hidden = 0
    for index, (start, end, row) in enumerate(rows):
        rendered.append(card[position:start])
        share_match = re.search(r'<div class="bar-value">\s*(-?\d+(?:\.\d+)?)%', row)
        if share_match:
            share = float(share_match.group(1))
            width = 100.0 * share / maximum if maximum > 0 else 0.0
            row = re.sub(
                r'(<div class="bar-fill" style="width:)(-?\d+(?:\.\d+)?)(%")',
                lambda match: f'{match.group(1)}{width:.1f}{match.group(3)}',
                row,
                count=1,
            )
            row = re.sub(
                r'(<div class="bar-value">\s*)-?\d+(?:\.\d+)?%',
                lambda match: f'{match.group(1)}{round(share):d}%',
                row,
                count=1,
            )
        if index >= MAX_VISIBLE_ROWS:
            row = row.replace('class="bar-row', 'class="bar-row v6-hidden-row', 1)
            hidden += 1
        rendered.append(row)
        position = end
    rendered.append(card[position:])
    card = "".join(rendered)
    card = classify_rate_spans(card)

    title_match = re.search(r'<div class="card-title">(.*?)</div>', card, flags=re.S)
    if title_match:
        title = title_match.group(1).strip()
        right = "Distribution"
        if kind == "six_month" and "v4-inline-attrition-rate" in card:
            right = "Distribution / 6-month attrition"
        elif kind == "annual" and "v4-inline-attrition-rate" in card:
            right = "Distribution / annual attrition"
        heading = f'<div class="v6-panel-heading"><span>{title}</span><span>{right}</span></div>'
        card = card[: title_match.start()] + heading + card[title_match.end() :]

    card = re.sub(r'<div class="chart-footer">.*?</div>', "", card, flags=re.S)
    if hidden:
        note = f'<div class="v6-truncation-note">Showing the first {MAX_VISIBLE_ROWS} of {len(rows)} categories; the complete detail remains in V5.</div>'
        close = card.rfind("</article>")
        card = card[:close] + note + card[close:]
    if "v4-inline-attrition-rate" not in card:
        card = card.replace('class="card chart-card', 'class="card chart-card v6-distribution-only', 1)
    return card, len(rows), hidden


def normalize_bar_cards(fragment: str, kind: str) -> tuple[str, int, int]:
    cards = v5.chart_cards(fragment)
    rendered: list[str] = []
    position = 0
    row_count = 0
    hidden_count = 0
    for start, end, card in cards:
        rendered.append(fragment[position:start])
        normalized, rows, hidden = normalize_bar_card(card, kind)
        rendered.append(normalized)
        position = end
        row_count += rows
        hidden_count += hidden
    rendered.append(fragment[position:])
    return "".join(rendered), row_count, hidden_count


def classify_summary_pills(fragment: str) -> str:
    pattern = re.compile(r'<span class="v4-inline-attrition-summary-rate">(?P<body>.*?)</span>', flags=re.S)
    matches = list(pattern.finditer(fragment))
    values: list[float] = []
    for match in matches:
        number = re.search(r'(-?\d+(?:\.\d+)?)%', clean_text(match.group("body")))
        if number:
            values.append(float(number.group(1)))

    def replacement(match: re.Match[str]) -> str:
        number = re.search(r'(-?\d+(?:\.\d+)?)%', clean_text(match.group("body")))
        klass = rate_class(float(number.group(1)), values) if number else "attr-unavailable"
        return f'<span class="v4-inline-attrition-summary-rate {klass}">{match.group("body")}</span>'

    return pattern.sub(replacement, fragment)


def replace_heading(stage: str, title: str, subtitle: str, kind: str) -> tuple[str, str]:
    heading_start = stage.find('<div class="slide-heading">')
    if heading_start < 0:
        raise ValueError(f"Missing heading in {v5.stage_id(stage)}")
    heading_end = v5.find_matching_div(stage, heading_start)
    heading = (
        '<div class="slide-heading"><div>'
        f'<h2 class="slide-title-text">{html.escape(title)}</h2>'
        f'<p class="slide-subtitle">{html.escape(subtitle)}</p>'
        f'</div>{badge_markup(kind)}</div>'
    )
    return stage[:heading_start] + heading + stage[heading_end:], heading


def rebuild_content_stage(
    stage: str,
    reference: ReferenceCopy | None,
) -> tuple[str, int, int]:
    identifier = v5.stage_id(stage)
    title = v5.stage_title(stage)
    key = reference_key(title)
    kind = measure_kind(stage, key)
    subtitle = SUBTITLE_OVERRIDES.get(key) or (reference.subtitle if reference else "Aggregate distribution from the reviewed V5 evidence")
    definition = DEFINITION_OVERRIDES.get(key) or (reference.definition if reference else subtitle)
    population = POPULATION_OVERRIDES.get(key) or (reference.population if reference else "Published aggregate population")

    stage, heading = replace_heading(stage, title, subtitle, kind)
    heading_start = stage.find(heading)
    heading_end = heading_start + len(heading)
    outer_end = stage.rfind("</div>")
    if outer_end < heading_end:
        raise ValueError(f"Could not isolate content in {identifier}")
    content = stage[heading_end:outer_end].strip()
    content = re.sub(r'<span class="v4-inline-attrition-(?:unavailable-)?marker".*?</span>', "", content, flags=re.S)
    content, rows, hidden = normalize_bar_cards(content, kind)
    content = classify_summary_pills(content)

    source = source_markup(reference, kind)
    if key == "careergoalsitem":
        source = (
            source.rstrip(". ")
            + ". The 2023 raw item is present but its plain-header format requires mapping before attrition processing;"
            " the published visual history starts in 2024."
        )
    rebuilt = (
        f'<div class="slide-stage" id="{identifier}" data-v6-playbook="true">'
        f'{heading}'
        '<article class="card card-full v6-playbook-card">'
        '<div class="v6-definition-strip">'
        f'<div><span class="v6-mini-label">Definition</span><strong>{html.escape(definition)}</strong></div>'
        f'<div><span class="v6-mini-label">Population</span><strong>{html.escape(population)}</strong></div>'
        '</div>'
        f'<div class="v6-chart-area">{content}</div>'
        f'<div class="v6-source-line">{source}</div>'
        '</article></div>'
    )
    return rebuilt, rows, hidden


def inject_css(document: str) -> str:
    style_end = document.find("</style>")
    if style_end < 0:
        raise ValueError("The source deck has no closing style tag.")
    return document[:style_end] + "\n" + V6_CSS + "\n" + document[style_end:]


def validate(document: str, source: str, rows_before: int, hidden_rows: int) -> None:
    _, source_stages, _ = v5.extract_stages(source)
    _, output_stages, _ = v5.extract_stages(document)
    if len(source_stages) != EXPECTED_SLIDE_COUNT or len(output_stages) != EXPECTED_SLIDE_COUNT:
        raise ValueError("V6 must preserve all 50 V5 slides.")
    if [v5.stage_id(stage) for stage in output_stages] != [v5.stage_id(stage) for stage in source_stages]:
        raise ValueError("V6 changed the V5 slide order or identifiers.")
    if v5.stage_title(output_stages[1]) != "How to use this playbook":
        raise ValueError("Slide 2 must remain the agenda.")
    nav_start = document.find('<div class="nav-ctrl" id="slide-nav">')
    theme_start = document.find('<div class="side-controls" id="theme-selector">', nav_start)
    nav_ids = re.findall(r'<button class="nav-pill(?: pill-active)?" data-slide="(\d+)"', document[nav_start:theme_start])
    if nav_ids != [str(index) for index in range(EXPECTED_SLIDE_COUNT)]:
        raise ValueError("V6 navigation must contain 50 consecutive slide indexes.")
    if document.count('data-theme="theme-') != 4:
        raise ValueError("V6 must preserve the four canonical themes.")
    required = (
        'document.querySelectorAll(\'#theme-selector [data-theme]\')',
        "localStorage.setItem('slide-studio-theme'",
        "localStorage.getItem('slide-studio-theme'",
        "querySelectorAll('.slide-stage')",
        "showSlide(0)",
        '<div class="nav-ctrl" id="slide-nav">',
        '<div class="side-controls" id="theme-selector">',
    )
    for token in required:
        if token not in document:
            raise ValueError(f"V6 is missing required template token: {token}")
    if ".app-header" in document or 'class="app-header"' in document:
        raise ValueError("V6 must not contain an app header.")
    if document.count('data-v6-playbook="true"') != EXPECTED_SLIDE_COUNT - 2:
        raise ValueError("Every content slide must use the V6 playbook layout.")
    rows_after = len(
        re.findall(r'<div\b[^>]*\bclass="[^"]*\bbar-row\b[^"]*"[^>]*>', document, flags=re.I)
    )
    if rows_after != rows_before:
        raise ValueError(f"V6 changed bar-row count: {rows_before} -> {rows_after}.")
    hidden_row_classes = len(
        re.findall(r'class="[^"]*\bv6-hidden-row\b[^"]*"', document)
    )
    if hidden_row_classes != hidden_rows:
        raise ValueError("V6 hidden-row audit does not reconcile.")
    if "Distribution / 6-month attrition" not in document:
        raise ValueError("V6 does not show the requested distribution/attrition column treatment.")
    if "Definition" not in document or "Population" not in document:
        raise ValueError("V6 is missing the visual dictionary fields.")
    if re.search(r'<div class="bar-value">\s*\d+\.\d+%', document):
        raise ValueError("V6 standard distribution labels must use whole percentages.")
    visible_scope = re.sub(r"(?is)<(?:script|style)\b.*?</(?:script|style)>", " ", document)
    visible_text = clean_text(visible_scope)
    if re.search(r"\b(?:Definici[oó]n|Poblaci[oó]n|Fuente|L[aá]mina|No estimable)\b", visible_text, flags=re.I):
        raise ValueError("V6 contains Spanish reader-facing text; the requested language is English.")


def build(overwrite: bool) -> None:
    required = (SOURCE, REFERENCE, TEMPLATE)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing V6 inputs: " + ", ".join(missing))
    if TARGET.exists() and not overwrite:
        raise FileExistsError(f"{TARGET} already exists; use --overwrite to regenerate V6.")

    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    temporary_target = TARGET.with_name(TARGET.name + ".tmp")
    shutil.copyfile(TEMPLATE, temporary_target)
    template_copy = temporary_target.read_text(encoding="utf-8")
    if '<div class="side-controls" id="theme-selector">' not in template_copy:
        raise ValueError("The copied fullscreen template is incomplete.")

    source_hash = sha256(SOURCE)
    reference_hash = sha256(REFERENCE)
    source = SOURCE.read_text(encoding="utf-8")
    reference = REFERENCE.read_text(encoding="utf-8")
    reference_copy = extract_reference_copy(reference)
    prefix, stages, suffix = v5.extract_stages(source)

    rebuilt_stages: list[str] = []
    total_rows = len(
        re.findall(r'<div\b[^>]*\bclass="[^"]*\bbar-row\b[^"]*"[^>]*>', source, flags=re.I)
    )
    processed_rows = 0
    hidden_rows = 0
    for stage in stages:
        identifier = v5.stage_id(stage)
        if identifier == "slide-1":
            rebuilt_stages.append(title_slide())
            continue
        if identifier == "slide-2":
            rebuilt_stages.append(agenda_slide())
            continue
        key = reference_key(v5.stage_title(stage))
        rebuilt, rows, hidden = rebuild_content_stage(stage, reference_copy.get(key))
        rebuilt_stages.append(rebuilt)
        processed_rows += rows
        hidden_rows += hidden

    if processed_rows != total_rows:
        raise ValueError(f"Only {processed_rows} of {total_rows} standard bar rows were processed.")

    document = prefix + "\n\n  " + "\n\n  ".join(rebuilt_stages) + "\n\n  " + suffix
    document = v5.rewrite_navigation(document, rebuilt_stages)
    document = inject_css(document)
    document, count = re.subn(
        r"<title>.*?</title>",
        "<title>Attrition Variable Playbook - V6</title>",
        document,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise ValueError("Could not update the V6 document title.")
    validate(document, source, total_rows, hidden_rows)
    temporary_target.write_text(document, encoding="utf-8")
    temporary_target.replace(TARGET)

    if sha256(SOURCE) != source_hash:
        raise ValueError("V5 changed while V6 was being generated.")

    manifest = {
        "version": 6,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "presentation",
        "objective": (
            "Restyle the reviewed V5 deck as a concise visual dictionary using the approved Julia layout examples, "
            "without recalculating or replacing the aggregate evidence."
        ),
        "source_deck": {
            "path": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": source_hash,
            "preserved": True,
        },
        "visual_reference": {
            "path": str(REFERENCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": reference_hash,
            "approved_examples": [7, 11, 17],
            "used_for": "layout and visual grammar only",
        },
        "base_template": str(TEMPLATE),
        "language": "English",
        "visual_rules": {
            "structure": "Short title and subtitle, definition/population strip, chart-first body, compact source line.",
            "distribution": "Blue bars; standard distribution labels rounded to whole percentages; counts remain integers.",
            "attrition": "Rates retain one decimal and use relative high/mid/low pills within each chart panel.",
            "dense_panels": (
                f"The first {MAX_VISIBLE_ROWS} rows are shown when a standard bar panel is denser; all source rows remain in the HTML and V5 remains the detailed reference."
            ),
            "complex_charts": "Original V5 chart types and payloads are retained inside the simplified card system.",
        },
        "privacy": {
            "classification": "presentation",
            "aggregate_only": True,
            "protected_categories": "remain anonymized where required",
            "prohibited": ["employee rows", "IDs", "names", "emails", "addresses", "free text", "exact compensation"],
        },
        "validation": {
            "slides": len(rebuilt_stages),
            "standard_bar_rows_preserved": total_rows,
            "rows_hidden_for_presentation_density": hidden_rows,
            "theme_count": 4,
            "definition_population_slides": EXPECTED_SLIDE_COUNT - 2,
            "outcome": "pass",
        },
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(TARGET)
    print(MANIFEST)
    print(f"slides={len(rebuilt_stages)}; bar_rows={total_rows}; hidden_rows={hidden_rows}; language=English")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the Julia-style V6 attrition variable playbook.")
    parser.add_argument("--overwrite", action="store_true", help="Allow regeneration of the V6 output files.")
    build(parser.parse_args().overwrite)
