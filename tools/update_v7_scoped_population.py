"""Apply the approved Critical Tech / non-RF360 scope to the reviewed V7 deck.

The updater modifies V7 in place only.  It never rebuilds the deck from V6:
direct workforce panels use frozen scoped evidence; panels without a fresh,
approved scoped source are replaced by a transparent suppression state rather
than retaining Qualcomm-wide data under a new population label.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from build_distribution_html_v5 import category_key, find_matching_tag
from build_distribution_html_v7 import build_slide as build_ios_slide


ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v7.html"
CURRENT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.scoped-latest-distribution-evidence-20260917.json"
ANNUAL = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.annual-attrition-evidence-20260917.json"
IOS = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.ios-movement-reasons-ytd-evidence-20260917.json"

POPULATION = "Active Critical Tech employees, excluding Other Eng and RF360"
SCOPE_SOURCE = (
    "Current distribution: HRDA post_hire_monthly_worker_dtls, latest active monthly snapshot; "
    "Critical Tech job-family match, Other Eng and RF360 excluded."
)
COMP_RATIO_SOURCE = (
    "Current distribution: HRDA post_hire_monthly_worker_dtls, latest active monthly snapshot; "
    "scoped annual attrition: 12-month Voluntary follow-up from HRDA termination history. "
    "Critical Tech job-family match, Other Eng and RF360 excluded."
)

# Direct current-distribution panels that are supported by the frozen scoped
# snapshot evidence.  The key is a V7 slide and the nested key is its chart
# card position within that slide.
DIRECT_PANELS: dict[int, dict[int, str]] = {
    6: {0: "country"},
    7: {0: "office_site", 1: "office_site_city"},
    11: {0: "job_family"},
    12: {0: "region", 1: "region_country_split", 2: "labor_market"},
    13: {0: "gender"},
    14: {0: "work_arrangement", 1: "work_arrangement_binary"},
    15: {0: "engineering"},
    16: {0: "rehire"},
    17: {0: "prior_experience_years"},
    31: {1: "company_tenure"},
    35: {0: "level_grouped", 1: "management_level", 2: "job_level"},
    38: {0: "compensation_grade"},
    39: {0: "comp_ratio_band"},
    48: {0: "manager_change"},
}

# These panels have a fresh scoped source, but their companion panel in the
# original deck depends on an unrefreshed historical/derived calculation.
PARTIAL_PANEL_SUPPRESSIONS = {
    (11, 1): "The prior reorganization comparison was not recalculated under the Critical Tech population.",
    (15, 1): "The organizational split was not reconciled to the approved Critical Tech population.",
    (31, 0): "The original-hire tenure proxy was not recalculated under the approved population.",
}

# A current or historical calculation remains only when a scoped query has
# been regenerated and its semantics are suitable for this deck.  Every other
# data panel is deliberately suppressed here, preventing an old company-wide
# statistic from inheriting the new Critical Tech label.
FULL_SLIDE_SUPPRESSIONS: dict[int, str] = {
    3: "The applicant-level source was not rejoined to the approved Critical Tech employee scope.",
    4: "The application-history distribution was not rejoined to the approved Critical Tech employee scope.",
    20: "The QVoice comment source was not rejoined to the approved Critical Tech employee scope.",
    21: "The QVoice comment source was not rejoined to the approved Critical Tech employee scope.",
    22: "The QVoice participation source was not rejoined to the approved Critical Tech employee scope.",
    23: "The QVoice response source was not rejoined to the approved Critical Tech employee scope.",
    24: "The QVoice response source was not rejoined to the approved Critical Tech employee scope.",
    25: "The respondent-only QVoice score was not rejoined to the approved Critical Tech employee scope.",
    26: "The QVoice heartbeat source was not rejoined to the approved Critical Tech employee scope.",
    27: "The regional QVoice standardization was not recalculated under the approved Critical Tech employee scope.",
    29: "The job-profile and detailed-level tenure proxies were not recalculated under the approved population.",
    32: "The promotion-history calculation was not recalculated under the approved population.",
    33: "The promotion-by-grade calculation was not recalculated under the approved population.",
    34: "The grade-entry history calculation was not recalculated under the approved population.",
    36: "The grade-family mapping was not recalculated under the approved population.",
    37: "The manager-chain reconstruction was not recalculated under the approved population.",
    40: "The comparable-team compensation calculation was not recalculated under the approved population.",
    41: "The employee-manager location comparison was not recalculated under the approved population.",
    42: "The employee-manager residential-distance calculation was not recalculated under the approved population.",
    43: "The employee-manager office-site comparison was not recalculated under the approved population.",
    44: "The manager observed-to-expected exit calculation was not recalculated under the approved population.",
    45: "The current-manager team-exit calculation was not recalculated under the approved population.",
    46: "The above-average team-turnover flag was not recalculated under the approved population.",
    47: "The manager-leaving exposure calculation was not recalculated under the approved population.",
    49: "The manager-change count windows were not recalculated under the approved population.",
    50: "The Talent Index source was not rejoined to the approved Critical Tech employee scope.",
    51: "The proxy-event calculation was not recalculated under the approved population.",
    52: "The ET-field hierarchy counts were not recalculated under the approved population.",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def chart_cards(stage: str) -> list[tuple[int, int, str]]:
    """Return chart cards even when they are nested inside the outer slide card."""
    cards = []
    pattern = re.compile(r'<article\b(?=[^>]*\bclass="[^"]*\bchart-card\b[^"]*")[^>]*>', re.I)
    for match in pattern.finditer(stage):
        end = find_matching_tag(stage, "article", match.start())
        cards.append((match.start(), end, stage[match.start():end]))
    return cards


def stage_from_document(document: str, number: int) -> str:
    marker = f'<div class="slide-stage" id="slide-{number}"'
    start = document.index(marker)
    next_stage = re.search(r'<div class="slide-stage" id="slide-\d+"', document[start + len(marker):])
    end = start + len(marker) + next_stage.start() if next_stage else document.index('<div class="nav-ctrl"', start)
    return document[start:end]


def replace_stage(document: str, number: int, replacement: str) -> str:
    old = stage_from_document(document, number)
    return document.replace(old, replacement, 1)


def replace_chart_card(stage: str, index: int, replacement: str) -> str:
    cards = chart_cards(stage)
    if index >= len(cards):
        raise ValueError(f"Slide has no chart card {index}.")
    start, end, _ = cards[index]
    return stage[:start] + replacement + stage[end:]


def card_opening(card: str) -> str:
    return card[: card.index(">") + 1]


def current_index(payload: dict) -> dict[str, list[dict]]:
    indexed: dict[str, list[dict]] = {}
    for raw in payload["rows"]:
        row = dict(raw)
        indexed.setdefault(str(row["metric"]), []).append(row)
    return {
        metric: sorted(rows, key=lambda item: (-int(item["employee_count"]), str(item["category"])))
        for metric, rows in indexed.items()
    }


def annual_index(payload: dict) -> dict[str, dict[str, float]]:
    indexed: dict[str, dict[str, float]] = {}
    for row in payload["rows"]:
        indexed.setdefault(str(row["metric"]), {})[
            category_key(str(row["metric"]), row["category"])
        ] = float(row["attrition_rate_percent"])
    return indexed


def annual_key(metric: str, category: str) -> str:
    # The current-snapshot evidence uses reader-friendly year labels while the
    # annual query uses ``<1`` and integer values.  This is a lossless label
    # normalization, not a change in the underlying grouping.
    if metric == "prior_experience_years":
        match = re.fullmatch(r"(\d+) years?", category)
        if match:
            return "lt1" if match.group(1) == "0" else match.group(1)
    return category_key(metric, category)


def rate_class(rate: float | None, available: list[float]) -> str:
    if rate is None:
        return "attr-unavailable"
    if rate == max(available):
        return "attr-high"
    if rate == min(available):
        return "attr-low"
    return "attr-mid"


def annual_pill(rate: float | None, klass: str) -> str:
    if rate is None:
        return (
            '<span class="v4-inline-attrition-rate v6-rate-pill attr-unavailable" '
            'title="No publishable exact-match annual rate; the label does not mean zero." '
            'aria-label="Annual voluntary attrition rate not publishable">Not estimable</span>'
        )
    shown = f"{rate:.1f}%"
    return (
        f'<span class="v4-inline-attrition-rate v6-rate-pill {klass}" '
        f'title="Annual voluntary attrition: {shown}" '
        f'aria-label="Annual voluntary attrition: {shown}">{shown}</span>'
    )


def current_distribution_card(card: str, metric: str, rows: list[dict], rates: dict[str, dict[str, float]], snapshot_date: str, denominator: int) -> str:
    if not rows:
        raise ValueError(f"No scoped current rows are available for {metric}.")
    displayed = rows[:10]
    matches = [rates.get(metric, {}).get(annual_key(metric, str(row["category"]))) for row in displayed]
    available = [rate for rate in matches if rate is not None]
    max_share = max(float(row["workforce_share_percent"]) for row in displayed)
    title = {
        "country": "Country · current snapshot",
        "office_site": "Office site · current snapshot",
        "office_site_city": "Office site and city · current snapshot",
        "job_family": "Job family · current snapshot",
        "region": "Region · current snapshot",
        "region_country_split": "Country split / region · current snapshot",
        "labor_market": "Labor market · current snapshot",
        "gender": "Stored anonymized codes · current snapshot",
        "work_arrangement": "Stored work arrangement · current snapshot",
        "work_arrangement_binary": "Onsite versus other stored values · current snapshot",
        "engineering": "Stored engineering flag · current snapshot",
        "rehire": "Rehire flag · current snapshot",
        "prior_experience_years": "Experience before Qualcomm · current snapshot",
        "company_tenure": "Service since latest hire / rehire · current snapshot",
        "level_grouped": "Level group · current snapshot",
        "management_level": "Management level · current snapshot",
        "job_level": "Detailed job level · current snapshot",
        "compensation_grade": "Compensation grade · current snapshot",
        "comp_ratio_band": "Compa-ratio band · current snapshot",
        "manager_change": "Manager-change flag · current snapshot",
    }[metric]
    rendered_rows = []
    for row, rate in zip(displayed, matches):
        label = html.escape(str(row["category"]))
        share = float(row["workforce_share_percent"])
        count = int(row["employee_count"])
        width = max(2.0, 100 * share / max_share)
        rendered_rows.append(
            '<div class="bar-row v4-inline-attrition-row"><div class="bar-label" title="'
            + label
            + '">'
            + label
            + '</div><div class="bar-track"><div class="bar-fill" style="width:'
            + f"{width:.1f}%"
            + '"></div></div><div class="bar-value">'
            + f"{share:.1f}%<span>&nbsp;·&nbsp;n={count:,}</span></div>"
            + annual_pill(rate, rate_class(rate, available))
            + "</div>"
        )
    hidden_note = "" if len(rows) <= len(displayed) else f" Top {len(displayed)} publishable categories shown."
    content = (
        '<div class="v6-panel-heading"><span>' + title + '</span><span>Distribution / Annual attrition</span></div>'
        '<div class="bar-list">' + "".join(rendered_rows) + "</div>"
        f'<div class="chart-footer">{snapshot_date} snapshot · scoped workforce n={denominator:,}.{hidden_note}</div>'
    )
    return card_opening(card) + content + "</article>"


def suppressed_card(card: str, title: str, reason: str) -> str:
    content = (
        '<div class="v6-panel-heading"><span>' + html.escape(title) + '</span><span>Scope refresh</span></div>'
        '<div class="empty-panel v7-scope-suppression"><strong>Not published for the scoped population</strong>'
        '<span>' + html.escape(reason) + '</span></div>'
        '<div class="chart-footer">The prior company-wide values were removed rather than relabeled.</div>'
    )
    return card_opening(card) + content + "</article>"


def full_slide_suppression(stage: str, reason: str) -> str:
    chart_area = re.search(r'<div class="v6-chart-area(?: [^"]*)?">', stage)
    source = re.search(r'<div class="v6-source-line">.*?</div>', stage, flags=re.S)
    if not chart_area or not source:
        raise ValueError("The slide does not contain the expected V6 visual/source structure.")
    start = chart_area.start()
    end = source.start()
    replacement = (
        '<div class="v6-chart-area"><article class="card chart-card v7-scope-suppression-card">'
        '<div class="v6-panel-heading"><span>Scope refresh status</span><span>Not published</span></div>'
        '<div class="empty-panel v7-scope-suppression"><strong>Not published for the scoped population</strong>'
        '<span>' + html.escape(reason) + '</span></div>'
        '<p class="v7-scope-suppression-note">The former company-wide visual was removed. Recalculate and validate the source-to-worker join before publishing it for Critical Tech.</p>'
        '</article></div>'
    )
    stage = stage[:start] + replacement + stage[end:]
    stage = re.sub(
        r'<span class="badge [^"]+">.*?</span>',
        '<span class="badge badge-neutral">Not published</span>',
        stage,
        count=1,
        flags=re.S,
    )
    stage = re.sub(
        r'(<span class="v6-mini-label">Population</span><strong>).*?(</strong>)',
        r'\1' + POPULATION + r'\2',
        stage,
        count=1,
        flags=re.S,
    )
    return stage


def update_population_strip(stage: str) -> str:
    return re.sub(
        r'(<span class="v6-mini-label">Population</span><strong>).*?(</strong>)',
        r'\1' + POPULATION + r'\2',
        stage,
        count=1,
        flags=re.S,
    )


def replace_source_line(stage: str, text: str = SCOPE_SOURCE) -> str:
    return re.sub(
        r'<div class="v6-source-line">.*?</div>',
        '<div class="v6-source-line"><strong>Source:</strong> ' + html.escape(text) + '</div>',
        stage,
        count=1,
        flags=re.S,
    )


def annual_prior_experience_card(card: str, annual_rows: list[dict]) -> str:
    rows = sorted(annual_rows, key=lambda row: (-int(row["employee_snapshot_count"]), str(row["category"])))[:12]
    rates = [float(row["attrition_rate_percent"]) for row in rows]
    maximum = max(rates)
    body = []
    for row in rows:
        label = html.escape(str(row["category"]))
        rate = float(row["attrition_rate_percent"])
        n = int(row["employee_snapshot_count"])
        width = max(2.0, 100 * rate / maximum)
        body.append(
            '<div class="bar-row v4-inline-attrition-row"><div class="bar-label" title="'
            + label + '">' + label + '</div><div class="bar-track"><div class="bar-fill" style="width:'
            + f'{width:.1f}%"></div></div><div class="bar-value">n={n:,}</div>'
            + annual_pill(rate, rate_class(rate, rates)) + "</div>"
        )
    content = (
        '<div class="v6-panel-heading"><span>Annual voluntary attrition by prior experience</span><span>Annual attrition</span></div>'
        '<div class="bar-list">' + "".join(body) + '</div>'
        '<div class="chart-footer">Bars scale to the annual voluntary attrition rate; n is employee-snapshot exposure. Top 12 publishable bands shown.</div>'
    )
    return card_opening(card) + content + "</article>"


def append_css(document: str) -> str:
    marker = "    /* 13. CONTENT-SPECIFIC STYLES â€” add below this line"
    if "v7-scope-suppression-card" in document:
        return document
    if marker not in document:
        fallback = re.search(r"^\s*/\* 13\. CONTENT-SPECIFIC STYLES.*$", document, flags=re.M)
        if not fallback:
            raise ValueError("The V7 content-style marker is missing.")
        marker = fallback.group(0)
    css = r'''

    /* V7 Critical Tech population refresh */
    .v7-scope-suppression-card { justify-content:center; padding:22px 28px; }
    .v7-scope-suppression { margin:auto; max-width:820px; min-height:200px; display:flex; flex-direction:column; justify-content:center; gap:10px; text-align:center; border:1px dashed color-mix(in oklab, var(--accent) 38%, var(--border-subtle)); border-radius:14px; padding:24px 32px; background:color-mix(in oklab, var(--accent-soft) 34%, transparent); }
    .v7-scope-suppression strong { font-size:20px; color:var(--text-main); }
    .v7-scope-suppression span { font-size:14px; line-height:1.4; color:var(--text-muted); }
    .v7-scope-suppression-note { max-width:820px; margin:0 auto; color:var(--text-muted); font-size:12px; line-height:1.35; text-align:center; }
'''
    return document.replace(marker, marker + css, 1)


def normalize_stage_gaps(document: str) -> str:
    """Keep inter-slide whitespace stable when a stage is replaced in place."""
    return re.sub(
        r'(?<=</div>)\s*(?=<div class="slide-stage" id="slide-\d+")',
        "\n\n  ",
        document,
    )


def validate(document: str, snapshot_date: str, population_count: int) -> None:
    stages = re.findall(r'<div class="slide-stage" id="slide-\d+"', document)
    nav = re.findall(r'<button class="nav-pill[^>]* data-slide="\d+"', document)
    if len(stages) != 50 or len(nav) != 50:
        raise ValueError("V7 must retain 50 stages and 50 navigation items.")
    if "Active regular employees, excluding RF360" in document:
        raise ValueError("A stale active-regular population label remains in V7.")
    if "14.7% of the active regular workforce" in document:
        raise ValueError("The old global IOS headline remains in V7.")
    if f"{snapshot_date} snapshot · scoped workforce n={population_count:,}." not in document:
        raise ValueError("The scoped current-distribution snapshot was not rendered.")
    if document.count("v7-scope-suppression") < len(FULL_SLIDE_SUPPRESSIONS):
        raise ValueError("At least one unscoped source-specific slide was not suppressed.")


def main() -> None:
    for path in (DECK, CURRENT, ANNUAL, IOS):
        if not path.exists():
            raise FileNotFoundError(path)
    document = append_css(DECK.read_text(encoding="utf-8"))
    current = load(CURRENT)
    annual = load(ANNUAL)
    ios = load(IOS)
    by_metric = current_index(current)
    annual_rates = annual_index(annual)
    snapshot_date = str(current["snapshot_date"])
    denominator = int(current["scoped_employee_count"])

    # Deck-level population statement and the scoped IOS visual are both
    # rendered from the evidence files, not string-edited old values.
    document = document.replace(
        "Active regular employees, excluding RF360 unless noted",
        POPULATION,
    )
    document = replace_stage(document, 5, build_ios_slide(ios))

    for slide_number, mapping in DIRECT_PANELS.items():
        stage = update_population_strip(stage_from_document(document, slide_number))
        for card_index, metric in mapping.items():
            existing = chart_cards(stage)[card_index][2]
            stage = replace_chart_card(
                stage,
                card_index,
                current_distribution_card(existing, metric, by_metric[metric], annual_rates, snapshot_date, denominator),
            )
        source = COMP_RATIO_SOURCE if slide_number == 39 else SCOPE_SOURCE
        document = replace_stage(document, slide_number, replace_source_line(stage, source))

    for (slide_number, card_index), reason in PARTIAL_PANEL_SUPPRESSIONS.items():
        stage = stage_from_document(document, slide_number)
        existing = chart_cards(stage)[card_index][2]
        stage = replace_chart_card(stage, card_index, suppressed_card(existing, "Scope refresh status", reason))
        document = replace_stage(document, slide_number, replace_source_line(stage))

    # Slide 18 is a scoped annual-outcome visual, not a current snapshot
    # distribution.  Its original Plotly container was blank, so use the same
    # approved horizontal-bar grammar as the rest of the playbook.
    stage = update_population_strip(stage_from_document(document, 18))
    existing = chart_cards(stage)[0][2]
    stage = replace_chart_card(
        stage,
        0,
        annual_prior_experience_card(existing, [row for row in annual["rows"] if row["metric"] == "prior_experience_years"]),
    )
    document = replace_stage(document, 18, replace_source_line(stage, "Annual scoped attrition evidence from HRDA post_hire_monthly_worker_dtls and termination history; Critical Tech job-family match, Other Eng and RF360 excluded."))

    # The annual commute query was rebuilt under scope but did not pass its
    # all-band publication rule.  Keep its explicit suppression and correct
    # the population statement rather than use the old global rates.
    stage = update_population_strip(stage_from_document(document, 19))
    document = replace_stage(document, 19, replace_source_line(stage, "Scoped annual commute-distance evidence; Critical Tech job-family match, Other Eng and RF360 excluded. The annual distance rate is not published."))

    stage = stage_from_document(document, 8)
    stage = re.sub(
        r'(<span class="v6-mini-label">Population</span><strong>).*?(</strong>)',
        r'\1Scoped Critical Tech manager-led teams meeting the aggregate publication rule\2',
        stage,
        count=1,
        flags=re.S,
    )
    document = replace_stage(document, 8, replace_source_line(stage, "Scoped annual team-turnover evidence from HRDA; Critical Tech job-family match, Other Eng and RF360 excluded."))

    for slide_number in (9, 10):
        stage = stage_from_document(document, slide_number)
        stage = re.sub(
            r'<p class="slide-subtitle">.*?</p>',
            '<p class="slide-subtitle">The annual post-departure rate is not published because the scoped cohort does not satisfy the follow-up rule</p>',
            stage,
            count=1,
            flags=re.S,
        )
        stage = re.sub(
            r'(<span class="v6-mini-label">Definition</span><strong>).*?(</strong>)',
            r'\1Descriptive annual attrition after a team departure; suppressed when the cohort rule fails.\2',
            stage,
            count=1,
            flags=re.S,
        )
        stage = re.sub(
            r'<span class="badge [^"]+">.*?</span>',
            '<span class="badge badge-neutral">Not published</span>',
            stage,
            count=1,
            flags=re.S,
        )
        document = replace_stage(
            document,
            slide_number,
            replace_source_line(stage, "Scoped annual post-departure evidence; Critical Tech job-family match, Other Eng and RF360 excluded. The rate is not published because the annual cohort rule did not pass."),
        )

    for slide_number, reason in FULL_SLIDE_SUPPRESSIONS.items():
        stage = full_slide_suppression(stage_from_document(document, slide_number), reason)
        document = replace_stage(document, slide_number, replace_source_line(stage, "Scope refresh: prior source-specific values removed pending a validated Critical Tech / non-RF360 recalculation."))

    # IOS source and copy were produced before the scope was approved; use the
    # frozen scoped evidence as the render source and state the scope plainly.
    ios_stage = stage_from_document(document, 5)
    ios_total = next(
        row for row in ios["rows"]
        if int(row["calendar_year"]) == 2026 and row["group_key"] == "total"
    )
    ios_stage = re.sub(
        r"IOS movements represent [0-9.]+% of the (?:active regular|scoped Critical Tech) workforce in 2026 YTD",
        f"IOS movements represent {float(ios_total['workforce_share_percent']):.1f}% of the scoped Critical Tech workforce in 2026 YTD",
        ios_stage,
        count=1,
    )
    ios_stage = ios_stage.replace("active regular workforce", "scoped Critical Tech workforce")
    ios_stage = ios_stage.replace("Active regular employees; latest active monthly snapshot within 45 days before the event.", "Active Critical Tech employees, excluding Other Eng and RF360; latest active monthly snapshot within 45 days before the event.")
    ios_stage = ios_stage.replace("average active regular workforce", "average scoped Critical Tech workforce")
    document = replace_stage(document, 5, replace_source_line(ios_stage, "HRDA workers_ios_transfers, post_hire_monthly_worker_dtls, and all_terminations; Critical Tech job-family match, Other Eng and RF360 excluded. Cells below n=30 are suppressed."))

    # Catch wording that appears in a retained definition strip but is not a
    # data source in its own right.  This is a text-only consistency pass;
    # numerical panels were already recalculated or suppressed above.
    document = document.replace("Active regular employees, excluding RF360", POPULATION)
    document = document.replace(
        "Stored work country for active regular employees.",
        "Stored work country for the scoped Critical Tech workforce.",
    )

    document = normalize_stage_gaps(document)
    validate(document, snapshot_date, denominator)
    DECK.write_text(document, encoding="utf-8")
    print(json.dumps({"deck": str(DECK), "snapshot_date": snapshot_date, "scoped_employee_count": denominator, "direct_slides": sorted(DIRECT_PANELS), "suppressed_slides": sorted(FULL_SLIDE_SUPPRESSIONS)}, indent=2))


if __name__ == "__main__":
    main()
