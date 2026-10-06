"""Apply frozen annual attrition evidence to the reviewed V7 HTML deck only."""

from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

from build_distribution_html_v5 import category_key, chart_cards, extract_stages, find_matching_tag, normal, visible_label


ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v7.html"
EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.annual-attrition-evidence-20260917.json"
COMP_TREND = ROOT / "output" / "distribution" / "json" / "comp-ratio-annual-attrition-trend-evidence-20260917.json"
POST_EXIT = ROOT / "output" / "distribution" / "json" / "team-post-exit-annual-attrition-evidence-20260917.json"
TEAM_TURNOVER = ROOT / "output" / "distribution" / "json" / "team-turnover-annual-evidence-20260917.json"
COMMUTE = ROOT / "output" / "distribution" / "json" / "commute-distance-onsite-annual-attrition-evidence-20260917.json"

PANEL_METRICS = {
    6: {0: "country"},
    7: {0: "office_site", 1: "office_site_city"},
    11: {0: "job_family", 1: "job_family"},
    12: {0: "region", 1: "region_country_split", 2: "labor_market"},
    13: {0: "gender"},
    14: {0: "work_arrangement", 1: "work_arrangement_binary"},
    15: {0: "engineering"},
    17: {0: "prior_experience_years"},
    31: {1: "company_tenure"},
    35: {0: "level_grouped", 1: "management_level", 2: "job_level"},
    38: {0: "compensation_grade"},
    39: {0: "comp_ratio_band"},
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rate_index(payload: dict) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for row in payload["rows"]:
        metric = str(row["metric"])
        result.setdefault(metric, {})[category_key(metric, row["category"])] = float(row["attrition_rate_percent"])
    return result


def card_rows(card: str) -> list[tuple[int, int, str]]:
    result = []
    cursor = 0
    pattern = re.compile(r'<div\b[^>]*\bclass="[^"]*\bbar-row\b[^"]*"[^>]*>', re.I)
    while match := pattern.search(card, cursor):
        end = find_matching_tag(card, "div", match.start())
        result.append((match.start(), end, card[match.start():end]))
        cursor = end
    return result


def rate_class(rate: float, all_rates: list[float]) -> str:
    if rate == max(all_rates):
        return "attr-high"
    if rate == min(all_rates):
        return "attr-low"
    return "attr-mid"


def annual_span(rate: float | None, klass: str | None = None) -> str:
    if rate is None:
        return ('<span class="v4-inline-attrition-rate v6-rate-pill attr-unavailable" '
                'title="No publishable exact-match annual rate; the label does not mean zero." '
                'aria-label="Annual voluntary attrition rate not publishable">Not estimable</span>')
    shown = f"{rate:.1f}%"
    return (f'<span class="v4-inline-attrition-rate v6-rate-pill {klass}" '
            f'title="Annual voluntary attrition: {shown}" '
            f'aria-label="Annual voluntary attrition: {shown}">{shown}</span>')


def update_row(row: str, rate: float | None, klass: str | None) -> str:
    pattern = re.compile(r'<span class="v4-inline-attrition-rate\b[^"]*"[^>]*>.*?</span>', re.I | re.S)
    updated, count = pattern.subn(annual_span(rate, klass), row, count=1)
    if count != 1:
        raise ValueError("Expected exactly one existing inline attrition span.")
    return updated


def update_card(card: str, metric: str, evidence: dict[str, dict[str, float]]) -> str:
    rows = card_rows(card)
    resolved = [(start, end, row, evidence.get(metric, {}).get(category_key(metric, visible_label(row)))) for start, end, row in rows]
    observed = [rate for _, _, _, rate in resolved if rate is not None]
    if not observed:
        # A scoped refresh may intentionally replace an unsupported companion
        # chart with a suppression panel.  Do not revive it with stale values.
        return card
    parts, cursor = [], 0
    for start, end, row, rate in resolved:
        parts.append(card[cursor:start])
        parts.append(update_row(row, rate, rate_class(rate, observed) if rate is not None else None))
        cursor = end
    parts.append(card[cursor:])
    return "".join(parts)


def replace_chart_cards(stage: str, mapping: dict[int, str], evidence: dict[str, dict[str, float]]) -> str:
    cards = []
    pattern = re.compile(r'<article\b(?=[^>]*\bclass="[^"]*\bchart-card\b[^"]*")[^>]*>', re.I)
    for match in pattern.finditer(stage):
        cards.append((match.start(), find_matching_tag(stage, "article", match.start()), stage[match.start():find_matching_tag(stage, "article", match.start())]))
    pieces, cursor = [], 0
    for index, (start, end, card) in enumerate(cards):
        pieces.append(stage[cursor:start])
        pieces.append(update_card(card, mapping[index], evidence) if index in mapping else card)
        cursor = end
    pieces.append(stage[cursor:])
    return "".join(pieces)


def update_summary(stage: str, metric: str, categories: tuple[str, str], evidence: dict[str, dict[str, float]]) -> str:
    rates = {category: evidence[metric][category_key(metric, category)] for category in categories}

    def repl(match: re.Match[str]) -> str:
        category = html.unescape(re.sub(r"<[^>]+>", "", match.group("category"))).strip()
        rate = rates.get(category)
        if rate is None:
            raise ValueError(f"Missing annual summary category {category!r}.")
        return (f'<span class="v4-inline-attrition-summary-rate" title="Annual voluntary attrition · {html.escape(category)}: {rate:.1f}%">'
                f'<span class="v4-inline-attrition-summary-category">{match.group("category")}</span> {rate:.1f}%</span>')

    pattern = re.compile(r'<span class="v4-inline-attrition-summary-rate"[^>]*><span class="v4-inline-attrition-summary-category">(?P<category>.*?)</span>.*?</span>', re.S)
    stage, count = pattern.subn(repl, stage)
    # A later scoped-population refresh may replace the historical trend card
    # with a current horizontal distribution.  In that valid state there is
    # no summary-chip container left to update.
    if count == 0:
        return stage
    if count != 2:
        raise ValueError(f"Expected two summary rate chips for {metric}, got {count}.")
    return stage


def annualize_stage_text(stage: str) -> str:
    stage = stage.replace("6-month attrition", "Annual attrition")
    stage = stage.replace("6-month voluntary attrition", "Annual voluntary attrition")
    stage = stage.replace("Six-month voluntary attrition", "Annual voluntary attrition")
    stage = stage.replace("Distribution / 6-month attrition", "Distribution / annual attrition")
    stage = stage.replace("Six-month attrition is a voluntary exit after the snapshot", "Annual attrition is a voluntary exit in the 12 months after the snapshot")
    return stage


def replace_stage(document: str, number: int, replacement: str) -> str:
    start_pattern = f'<div class="slide-stage" id="slide-{number}"'
    start = document.index(start_pattern)
    next_match = re.search(r'<div class="slide-stage" id="slide-\d+"', document[start + len(start_pattern):])
    end = start + len(start_pattern) + next_match.start() if next_match else document.index('<div class="nav-ctrl"', start)
    return document[:start] + replacement + document[end:]


def stage_from_document(document: str, number: int) -> str:
    start = document.index(f'<div class="slide-stage" id="slide-{number}"')
    next_match = re.search(r'<div class="slide-stage" id="slide-\d+"', document[start + 1:])
    end = start + 1 + next_match.start() if next_match else document.index('<div class="nav-ctrl"', start)
    return document[start:end]


def ensure_comp_ratio_summary_styles(document: str) -> str:
    """Keep one scoped one-series summary treatment without changing the deck shell."""
    tuning = """    /* comp-ratio-scoped-layout-tuning: reserve room for the published annual summary */
    .comp-ratio-main { grid-template-rows:minmax(0,.72fr) minmax(0,1.28fr); }
    .comp-ratio-history-chart { height:182px; flex:0 0 182px; }
""".rstrip()
    # Earlier iterations inserted this override more than once.  Normalize the
    # deck before adding it so reruns are byte-stable.
    document = document.replace(tuning, "")
    has_summary_note_style = ".comp-ratio-summary-note" in document
    anchor = (
        "    .comp-ratio-scoped-summary .comp-ratio-summary-note { align-self:center; color:var(--text-muted); font-size:10px; line-height:1.22; }"
        if has_summary_note_style
        else "    .comp-ratio-summary-difference strong { display:block; color:var(--accent); font-size:13px; font-variant-numeric:tabular-nums; }"
    )
    summary_style = "" if has_summary_note_style else """
    .comp-ratio-pooled-summary.comp-ratio-scoped-summary { grid-template-columns:minmax(0,0.82fr) minmax(0,1.5fr); }
    .comp-ratio-scoped-summary .comp-ratio-summary-note { align-self:center; color:var(--text-muted); font-size:10px; line-height:1.22; }
"""
    addition = summary_style + "\n" + tuning
    if anchor not in document:
        raise ValueError("Could not find the comp-ratio summary style anchor.")
    document = document.replace(anchor, anchor + addition, 1)
    footer_anchor = "    .comp-ratio-history-card .chart-footer { padding-top:5px; font-size:10px; line-height:1.22; }"
    pattern = re.escape(tuning) + r"\s*" + re.escape(footer_anchor)
    document, count = re.subn(pattern, tuning + "\n\n" + footer_anchor, document, count=1)
    if count != 1:
        raise ValueError("Could not normalize the comp-ratio summary style spacing.")
    return document


def update_comp_history(document: str, payload: dict) -> str:
    rows = []
    for row in payload["rows"]:
        rows.append({
            "snapshot_date": row["snapshot_date"], "group_label": row["group_label"],
            "employee_snapshots": row["employee_snapshot_count"], "voluntary_exit_snapshots": row["voluntary_exits"],
            "voluntary_rate_percent": row["attrition_rate_percent"],
        })
    replacement = "var compRatioHistoryRows = " + json.dumps(rows, separators=(",", ":")) + ";"
    document, count = re.subn(r"var compRatioHistoryRows = \[.*?\];", replacement, document, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Could not replace comp-ratio annual history rows.")
    displayed_groups = [str(item["group_label"]) for item in payload["groups"]]
    document, count = re.subn(
        r"var compRatioHistoryGroups = \[.*?\];",
        "var compRatioHistoryGroups = " + json.dumps(displayed_groups, separators=(",", ":")) + ";",
        document,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise ValueError("Could not replace comp-ratio displayed groups.")
    chart_layout = re.compile(
        r"(function renderCompRatioHistoryChart\(\) \{.*?Plotly\.react\(chart, traces, \{\s*)(?:width:\s*chart\.clientWidth \|\| 1360,\s*)?height:\s*\d+,",
        flags=re.S,
    )
    document, count = chart_layout.subn(
        r"\1width: chart.clientWidth || 1360,\n          height: 182,",
        document,
        count=1,
    )
    if count != 1:
        raise ValueError("Could not set the comp-ratio chart dimensions.")
    navigation_hook = """      renderCompRatioHistoryChart();
      var compRatioHistoryRedraw;
      document.addEventListener('keydown', function () {
        window.clearTimeout(compRatioHistoryRedraw);
        compRatioHistoryRedraw = window.setTimeout(function () {
          var compSlide = document.getElementById('slide-39');
          if (compSlide && compSlide.style.display !== 'none') renderCompRatioHistoryChart();
        }, 0);
      });
      new MutationObserver"""
    navigation_anchor = "      renderCompRatioHistoryChart();\n      new MutationObserver"
    if "var compRatioHistoryRedraw;" not in document:
        if navigation_anchor not in document:
            raise ValueError("Could not add the comp-ratio visible-slide redraw hook.")
        document = document.replace(navigation_anchor, navigation_hook, 1)

    groups = payload["groups"]
    if len(groups) != 1 or str(groups[0]["group_label"]) != ">=0.8":
        raise ValueError("The scoped comp-ratio trend must contain only the publishable >=0.8 series.")
    group = groups[0]
    summary = (
        '<div class="comp-ratio-pooled-summary comp-ratio-scoped-summary">'
        '<div class="comp-ratio-summary-item"><div class="comp-ratio-summary-label">'
        '<i class="comp-ratio-summary-dot high"></i>&gt;=0.8</div>'
        f'<strong>{float(group["attrition_rate_percent"]):.1f}%</strong>'
        f'<small>pooled annual &middot; n={int(group["employee_snapshot_count"]):,} &middot; '
        f'{int(group["voluntary_exits"]):,} Voluntary exits</small></div>'
        '<div class="comp-ratio-summary-note">The &lt;0.8 annual series is not published because it has no publishable annual points under the scoped population.</div>'
        '</div>'
    )
    stage = stage_from_document(document, 39)
    summary_match = re.search(r'<div class="comp-ratio-pooled-summary[^\"]*">', stage)
    if not summary_match:
        raise ValueError("Could not find the comp-ratio pooled summary.")
    summary_end = find_matching_tag(stage, "div", summary_match.start())
    # Put the annual result above the chart rather than below it.  Plotly owns
    # the chart's lower legend and tick labels, so a below-chart summary would
    # overlap them in the fixed-height presentation canvas.
    stage = stage[:summary_match.start()] + stage[summary_end:]
    title = '<div class="card-title">Annual voluntary attrition after each snapshot</div>'
    title_index = stage.find(title)
    if title_index < 0:
        raise ValueError("Could not find the comp-ratio history title.")
    title_end = title_index + len(title)
    stage = stage[:title_end] + summary + stage[title_end:]

    history_start = stage.find('<article class="card chart-card comp-ratio-history-card">')
    footer_match = re.search(r'<div class="chart-footer">.*?</div>', stage[history_start:], flags=re.S)
    if history_start < 0 or not footer_match:
        raise ValueError("Could not find the comp-ratio history footer.")
    footer_start = history_start + footer_match.start()
    footer_end = history_start + footer_match.end()
    footer = (
        '<div class="chart-footer">24 complete monthly snapshots from 2023-09-24 through 2025-08-24. '
        'Each point uses strict <strong>term_type = \'VOLUNTARY\'</strong> exits in the 12 months after the snapshot; '
        'pooled n counts employee-snapshot exposures. Descriptive association only, not individual prediction.</div>'
    )
    stage = stage[:footer_start] + footer + stage[footer_end:]
    stage, count = re.subn(
        r'<div class="v6-source-line">.*?</div>',
        '<div class="v6-source-line"><strong>Source:</strong> Current distribution: HRDA post_hire_monthly_worker_dtls, latest active monthly snapshot; scoped annual attrition: 12-month Voluntary follow-up from HRDA termination history. Critical Tech job-family match, Other Eng and RF360 excluded.</div>',
        stage,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise ValueError("Could not replace the comp-ratio source line.")
    document = replace_stage(document, 39, stage)
    for old, new in (
        ("Six-month voluntary attrition by comp-ratio group", "Annual voluntary attrition by comp-ratio group"),
        ("six-month voluntary attrition", "annual voluntary attrition"),
        ("Six-month voluntary attrition", "Annual voluntary attrition"),
        ("Voluntary rate:", "Annual voluntary attrition:"),
    ):
        document = document.replace(old, new)
    return document


def update_team_turnover(stage: str, payload: dict) -> str:
    scenarios = {str(row["scenario"]): row for row in payload["rows"] if row.get("row_type") == "scenario_summary"}
    order = ("All manager-led teams", "Teams with >5 direct reports")
    cards = []
    for match in re.finditer(r'<article\b(?=[^>]*\bclass="[^"]*\bteam-turnover-card\b[^"]*")[^>]*>', stage, flags=re.I):
        cards.append((match.start(), find_matching_tag(stage, "article", match.start()), stage[match.start():find_matching_tag(stage, "article", match.start())]))
    replacements = []
    for card, scenario in zip(cards[:2], order):
        start, end, fragment = card
        row = scenarios[scenario]
        teams = int(row["manager_teams"])
        with_exit = int(row["teams_with_at_least_one_voluntary_exit"])
        without_exit = int(row["teams_without_voluntary_exit"])
        positive_pct = 100 * with_exit / teams
        zero_pct = 100 * without_exit / teams
        updated = fragment
        updated = re.sub(r'<div class="team-rate"><strong>.*?</strong><span>.*?</span></div>', f'<div class="team-rate"><strong>{float(row["annual_turnover_percent"]):.1f}%</strong><span>annual voluntary<br/>turnover</span></div>', updated, count=1, flags=re.S)
        updated = re.sub(r'(<div class="team-kpis">.*?<strong>)[\d,]+(</strong><span>manager teams</span>.*?<strong>)[\d,]+(</strong><span>reports at cutoff</span>.*?<strong>)[\d,]+(</strong><span>voluntary exits</span>)', rf'\g<1>{teams:,}\g<2>{int(row["direct_reports_at_cutoff"]):,}\g<3>{int(row["voluntary_exit_events"]):,}\g<4>', updated, count=1, flags=re.S)
        updated = updated.replace("Teams by six-month exit occurrence", "Teams by annual exit occurrence")
        updated = re.sub(
            r'aria-label="[^"]*"><div class="team-outcome-zero" style="width:[^"]+"></div><div class="team-outcome-positive" style="width:[^"]+">',
            f'aria-label="{scenario}: {zero_pct:.1f}% of teams with no voluntary exit and {positive_pct:.1f}% with at least one voluntary exit"><div class="team-outcome-zero" style="width:{zero_pct:.2f}%"></div><div class="team-outcome-positive" style="width:{positive_pct:.2f}%">',
            updated, count=1,
        )
        updated = re.sub(r'<div class="team-outcome-legend"><span>0 exits <strong>.*?</strong></span><span>≥1 exit <strong>.*?</strong></span></div>', f'<div class="team-outcome-legend"><span>0 exits <strong>{zero_pct:.1f}% · {without_exit:,}</strong></span><span>≥1 exit <strong>{positive_pct:.1f}% · {with_exit:,}</strong></span></div>', updated, count=1)
        updated = re.sub(r'<div class="chart-footer"><strong>.*?</strong> voluntary exits per 100 direct-report employee-months.</div>', f'<div class="chart-footer"><strong>{float(row["voluntary_exits_per_100_employee_months"]):.1f}</strong> voluntary exits per 100 direct-report employee-months.</div>', updated, count=1)
        replacements.append((start, end, updated))
    parts, cursor = [], 0
    for start, end, replacement in replacements:
        parts.extend((stage[cursor:start], replacement)); cursor = end
    parts.append(stage[cursor:])
    return annualize_stage_text("".join(parts).replace("6-month team history", "Annual team history").replace("same six-month window", "same 12-month window").replace("six-month equivalent", "annual"))


def update_post_exit(stage: str, scope: str, payload: dict) -> str:
    if payload.get("outcome") != "pass":
        match = re.search(r'<article class="card chart-card team-post-exit-card">', stage)
        if not match:
            raise ValueError("The post-exit slide has no expected chart card to suppress.")
        start = match.start()
        end = find_matching_tag(stage, "article", start)
        replacement = (
            '<article class="card chart-card team-post-exit-card"><div class="card-title">Annual post-departure attrition</div>'
            '<div class="empty-panel v7-scope-suppression"><strong>Annual rate not published</strong>'
            '<span>The scoped Critical Tech population does not meet the minimum cohort at every annual follow-up point.</span></div>'
            '<div class="chart-footer">The former company-wide curve was removed rather than relabeled.</div></article>'
        )
        return stage[:start] + replacement + stage[end:]
    exposed = payload["curves"][f"{scope}::exposed"]
    reference = payload["curves"][f"{scope}::reference_standardized"]
    evidence = {"exposed": exposed, "reference": reference}
    exposed_rate = exposed[-1]["cumulative_incidence_percent"]
    reference_rate = reference[-1]["cumulative_incidence_percent"]
    delta = exposed_rate - reference_rate
    stage, count = re.subn(r"var teamPostExitPayload = \{.*?\};", "var teamPostExitPayload = " + json.dumps(evidence, separators=(",", ":")) + ";", stage, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Could not replace a post-exit annual payload.")
    stage = re.sub(r'<div class="team-post-exit-kpis">.*?</div>\s*<div class="chart-footer">', f'<div class="team-post-exit-kpis"><div class="team-post-exit-kpi"><strong>{exposed_rate:.1f}%</strong><span>team after one initial departure</span></div><div class="team-post-exit-kpi"><strong>{reference_rate:.1f}%</strong><span>similar-size teams with no recent departure</span></div><div class="team-post-exit-kpi"><strong>{delta:+.1f} pp</strong><span>descriptive difference at one year</span></div></div><div class="chart-footer">', stage, count=1, flags=re.S)
    stage = stage.replace("six-month cumulative voluntary attrition", "annual cumulative voluntary attrition")
    stage = stage.replace("descriptive difference at six months", "descriptive difference at one year")
    stage = stage.replace("tickvals: [0, 1, 2, 3, 4, 5, 6], ticktext: ['Start', '1', '2', '3', '4', '5', '6']", "tickvals: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], ticktext: ['Start', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']")
    return stage


def update_commute(stage: str, payload: dict) -> str:
    if payload.get("outcome") != "pass":
        match = re.search(r'<article class="card chart-card commute-attrition-card">', stage)
        if not match:
            raise ValueError("The commute slide has no chart card to suppress.")
        start = match.start()
        end = find_matching_tag(stage, "article", start)
        replacement = ('<article class="card chart-card commute-attrition-card"><div class="card-title">Annual voluntary attrition by estimated distance</div>'
                       '<div class="empty-panel"><strong>Annual rate not published</strong><span>The 12-month distance profile did not meet the minimum cohort and voluntary-event rule in every required band.</span></div>'
                       '<p class="commute-attrition-chart-note"><strong>What changed:</strong> the former six-month chart was removed rather than relabeled. No annual distance rate is substituted or imputed.</p></article>')
        stage = stage[:start] + replacement + stage[end:]
        return annualize_stage_text(stage).replace("Six-month attrition", "Annual attrition")
    rows = [{"band": band["category"], "lower_km": band["lower_km"], "average_monthly_onsite_population": band["average_monthly_onsite_employee_snapshots"], "voluntary_exits": band["voluntary_exits"], "attrition_rate_percent": band["attrition_rate_percent"]} for band in payload["bands"]]
    baseline = payload["baseline"]["attrition_rate_percent"]
    stage, count = re.subn(r"var rows = \[.*?\];\s*var baseline = [0-9.]+;(?=\s*var chart = document.getElementById\('commute-attrition-chart'\))", "var rows = " + json.dumps(rows, separators=(",", ":")) + f";\n      var baseline = {baseline};", stage, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Could not replace the commute annual data.")
    stage = stage.replace("Six-month voluntary attrition", "Annual voluntary attrition").replace("six-month voluntary attrition", "annual voluntary attrition")
    stage = re.sub(r"dotted line is the [0-9.]+% rate", f"dotted line is the {baseline:.1f}% annual rate", stage)
    return annualize_stage_text(stage)


def main() -> None:
    if not all(path.exists() for path in (EVIDENCE, COMP_TREND, POST_EXIT, TEAM_TURNOVER, COMMUTE)):
        missing = [str(path) for path in (EVIDENCE, COMP_TREND, POST_EXIT, TEAM_TURNOVER, COMMUTE) if not path.exists()]
        raise FileNotFoundError("Missing annual frozen evidence: " + ", ".join(missing))
    document = ensure_comp_ratio_summary_styles(DECK.read_text(encoding="utf-8"))
    rates = rate_index(load(EVIDENCE))
    for slide, mapping in PANEL_METRICS.items():
        stage = annualize_stage_text(stage_from_document(document, slide))
        document = replace_stage(document, slide, replace_chart_cards(stage, mapping, rates))
    for slide, metric, categories in ((16, "rehire", ("Not rehire (0)", "Rehire (1)")), (48, "manager_change", ("No manager change (0)", "Manager change (1)"))):
        stage = annualize_stage_text(stage_from_document(document, slide))
        document = replace_stage(document, slide, update_summary(stage, metric, categories, rates))
    document = replace_stage(document, 8, update_team_turnover(stage_from_document(document, 8), load(TEAM_TURNOVER)))
    document = replace_stage(document, 9, update_post_exit(stage_from_document(document, 9), "all_teams", load(POST_EXIT)))
    document = replace_stage(document, 10, update_post_exit(stage_from_document(document, 10), "teams_6_plus", load(POST_EXIT)))
    document = replace_stage(document, 19, update_commute(stage_from_document(document, 19), load(COMMUTE)))
    document = update_comp_history(document, load(COMP_TREND))
    # The suppressed commute chart no longer renders, but keep its dormant
    # axis wording consistent with the annual deck if it is inspected.
    document = document.replace("title: { text: 'Six-month attrition'", "title: { text: 'Annual attrition'")
    document = document.replace("Six-month voluntary attrition where V5 has approved evidence", "Annual voluntary attrition where V7 has approved evidence")
    document = document.replace("Outcome</span><strong>Six-month", "Outcome</span><strong>Annual")
    DECK.write_text(document, encoding="utf-8")
    print(json.dumps({"deck": str(DECK), "sha256": hashlib.sha256(DECK.read_bytes()).hexdigest(), "annual_panels": sum(len(items) for items in PANEL_METRICS.values())}, indent=2))


if __name__ == "__main__":
    main()
