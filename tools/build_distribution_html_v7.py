"""Build the V7 attrition distribution deck for authorized internal analysis.

V7 replaces the prior rolling-transfer visual on slide 5 and carries the
explicit internal-analysis exception through the complete deck: all available
aggregate categories, counts and percentages remain visible, including
sub-threshold buckets. Employee-level rows and identifiers are never added.
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable

try:
    from .refresh_promotion_track_trailing_12m_slide import (
        CSS as PROMOTION_TRACK_CSS,
        build_stage as build_promotion_track_stage,
        strip_scoped_css as strip_promotion_track_css,
    )
except ImportError:
    from refresh_promotion_track_trailing_12m_slide import (
        CSS as PROMOTION_TRACK_CSS,
        build_stage as build_promotion_track_stage,
        strip_scoped_css as strip_promotion_track_css,
    )

try:
    from .update_qvoice_slide_18_request_concern import (
        build_stage as build_qvoice_request_concern_stage,
        displayed_composition_shares as displayed_qvoice_composition_shares,
        load_evidence as load_qvoice_request_concern_evidence,
    )
except ImportError:
    from update_qvoice_slide_18_request_concern import (
        build_stage as build_qvoice_request_concern_stage,
        displayed_composition_shares as displayed_qvoice_composition_shares,
        load_evidence as load_qvoice_request_concern_evidence,
    )


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v6.html"
OUTPUT_DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v7.html"
V4_COMMUTE_REFERENCE_DECK = next(
    candidate
    for candidate in (
        ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v4 0.html",
        OUTPUT_DECK,
        ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v4.html",
    )
    if candidate.exists()
)
EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.ios-movement-reasons-ytd-evidence-20260917.json"
)
PROMOTION_TRACK_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.promotion-track-trailing-12m-evidence-20260918.json"
)
PROMOTION_GRADE_TOP10_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.promotion-grade-top10-trailing-12m-evidence-20260918.json"
)
APPLICATION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.application-employee-snapshot-trailing-6m-internal-evidence-20260917.json"
)
APPLICATION_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.application-trailing-12m-august-attrition-evidence-20260918.json"
)
GENDER_LABEL_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.gender-label-evidence-20260917.json"
)
SIX_MONTH_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v3.six-month-attrition-evidence-20260914.json"
)
REHIRE_ANNUAL_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.rehire-annual-attrition-evidence-20260917.json"
)
REHIRE_FY2026_OBSERVED_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.rehire-fy2026-observed-attrition-evidence-20260920.json"
)
REHIRE_AUGUST_TRAILING_12M_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.rehire-august-trailing-12m-evidence-20260921.json"
)
REHIRE_COMPARISON_AUGUST_TRAILING_12M_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.rehire-comparison-august-trailing-12m-evidence-20260922.json"
)
JOB_FAMILY_AUGUST_SNAPSHOT_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.job-family-august-snapshot-evidence-20260921.json"
)
JOB_FAMILY_AUGUST_TRAILING_12M_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.job-family-august-trailing-12m-attrition-evidence-20260922.json"
)
REHIRE_VISIBLE_FISCAL_YEARS = ("2024", "2025", "2026")
COMMUTE_ONSITE_SIX_MONTH_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "commute-distance-onsite-six-month-attrition-evidence-20260917.json"
)
COMMUTE_ALL_ELIGIBLE_SIX_MONTH_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "commute-distance-all-eligible-six-month-attrition-evidence-20260917.json"
)
COMMUTE_AUGUST_SNAPSHOT_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "commute-distance-global-evidence-20260921-august.json"
)
CTO_ORG_DISPLAY_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "engineering-cto-org-split-display-evidence-20260911.json"
)
CTO_ORG_ANNUAL_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "engineering-cto-org-split-annual-attrition-evidence-20260917.json"
)
QVOICE_WAVE_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "qvoice-wave-annual-attrition-evidence-20260918.json"
)
QVOICE_YTD_GROUP_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "qvoice-2026-ytd-attrition-evidence-20260917.json"
)
QVOICE_FAVORABLE_UNFAVORABLE_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "qvoice-favorable-unfavorable-question-attrition-evidence-20260923.json"
)
QVOICE_OPEN_TEXT_REQUEST_CONCERN_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "qvoice-open-text-request-concern-evidence-20260922.json"
)
QVOICE_HEARTBEAT_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "qvoice-2026-august-post-survey-ytd-heartbeat-relative-sign-attrition-evidence-20260923.json"
)
QVOICE_RETENTION_THEME_AUGUST_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "qvoice-retention-theme-august-trailing-12m-attrition-evidence-20260922.json"
)
NAV28_39_DIRECT_ANNUAL_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.nav28-39-direct-annual-attrition-evidence-20260917.json"
)
TIME_IN_JOB_PROFILE_TIME_IN_ROLE_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.time-at-detailed-level-time-in-role-august-trailing-12m-evidence-20260920.json"
)
NAV28_39_PROMOTION_ANNUAL_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.nav28-39-promotion-annual-attrition-evidence-20260917.json"
)
TIME_SINCE_LAST_PROMOTION_COMPARABLE_COHORTS_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.time-since-last-promotion-comparable-cohorts-evidence-20260924.json"
)
WITHIN_TEAM_ANNUAL_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.nav38-within-team-annual-attrition-evidence-20260917.json"
)
COLOCATION_ANNUAL_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.nav39-colocation-trailing-12m-evidence-20260921.json"
)
COLOCATION_DISPLAY_YEARS = ("2023", "2024", "2025", "2026")
MANAGER_TIMEZONE_ANNUAL_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.manager-timezone-annual-attrition-evidence-20260918.json"
)
MANAGER_TIMEZONE_2026_YTD_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.manager-timezone-2026-ytd-attrition-evidence-20260918.json"
)
MANAGER_TIMEZONE_AUGUST_TRAILING_12M_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.manager-timezone-august-trailing-12m-evidence-20260921.json"
)
NAV38_PLUS_AUGUST_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.nav38-plus-august-trailing-12m-evidence-20260921.json"
)
LAYERS_FROM_CEO_ANNUAL_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "layers-from-ceo-annual-attrition-evidence-20260921.json"
)
LAYERS_FROM_CEO_0_2_COMPENSATION_GRADE_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "layers-from-ceo-0-2-exact-compensation-grade-evidence-20260922.json"
)
DIRECT_TEAM_SPAN_ANNUAL_ATTRITION_EVIDENCE_FILE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "direct-team-span-annual-attrition-evidence-20260923.json"
)
AUTHORIZATION_FILE = ROOT / "config" / "attrition_v7_internal_analysis_authorization_20260917.json"
MANIFEST_FILE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7-manifest.json"
TEMPLATE = Path(
    r"C:\Users\fcarranz\.codex\skills\html-slide-generator\templates\fullscreen\base-fullscreen.html"
)

YEARS = (2024, 2025, 2026)
GROUP_KEYS = (
    "total",
    "reorg_manager_change",
    "lateral_ios",
    "country_move",
    "promo_ios",
    "immigration_parking",
    "downlevel_ios",
)

NUMERIC_DISPLAY_FORMATTER_MARKER = "<!-- V7 DISPLAY NUMBER FORMATTER -->"
DISPLAY_NUMBER_TOKEN = re.compile(
    r"(?<![\w,.-])(?P<number>-?(?:\d{1,3}(?:,\d{3})+|\d+)\.\d+)(?P<suffix>%?)(?![\w,.-])"
)
PROTECTED_HTML_BLOCK = re.compile(r"(<(?:script|style)\b[^>]*>.*?</(?:script|style)\s*>)", re.I | re.S)
HTML_TAG_TOKEN = re.compile(r"(<[^>]+>)")
DISPLAY_ATTRIBUTE_TOKEN = re.compile(r'(?P<prefix>\b(?:title|aria-label)=")(?P<value>[^"]*)(?P<suffix>")', re.I)

# Only these stages carry a validated annual measure.  Six-month, YTD, and
# partial-year QVoice panels deliberately remain outside this list.
ANNUAL_ATTRITION_STAGE_IDS = (
    15,
    16,
    29,
    31,
    32,
    35,
    36,
    37,
    38,
    39,
    40,
    43,
    44,
    45,
    46,
    47,
    48,
    49,
    50,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def format_display_number(raw_value: str) -> str:
    """Render a visible numeric token without false precision.

    Source evidence retains its stored precision.  This formatter is only for
    values shown to readers in HTML labels, accessible labels, and tooltips.
    """
    try:
        value = Decimal(raw_value.replace(",", ""))
    except InvalidOperation:
        return raw_value

    rounded = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if rounded == rounded.to_integral_value():
        rendered_integer = str(int(rounded))
        return f"{int(rounded):,}" if "," in raw_value else rendered_integer

    rendered = format(rounded, ".1f")
    if "," not in raw_value:
        return rendered
    integer_part, decimal_part = rendered.split(".", 1)
    return f"{int(integer_part):,}.{decimal_part}"


def format_display_percent(raw_value: str) -> str:
    """Render a visible percentage with exactly one decimal place."""
    try:
        value = Decimal(raw_value.replace(",", ""))
    except InvalidOperation:
        return raw_value

    rounded = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    rendered = format(rounded, ".1f")
    if "," not in raw_value:
        return rendered
    integer_part, decimal_part = rendered.split(".", 1)
    return f"{int(integer_part):,}.{decimal_part}"


def normalize_display_number_text(text: str) -> str:
    return DISPLAY_NUMBER_TOKEN.sub(
        lambda match: (
            format_display_percent(match.group("number"))
            if match.group("suffix") == "%"
            else format_display_number(match.group("number"))
        )
        + match.group("suffix"),
        text,
    )


def normalize_visible_display_numbers(deck: str) -> str:
    """Normalize only reader-visible HTML text plus tooltip/accessibility copy.

    Script, CSS, data payloads, style attributes, and calculation expressions
    are intentionally preserved so presentation rounding never changes a
    calculation, chart geometry, or data contract.
    """
    segments = PROTECTED_HTML_BLOCK.split(deck)
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


def inject_dynamic_number_formatter(deck: str) -> str:
    """Apply the same display policy to values Plotly creates at runtime."""
    require(NUMERIC_DISPLAY_FORMATTER_MARKER not in deck, "V7 number formatter was injected more than once.")
    body_match = re.search(r"<body\b[^>]*>", deck, re.I)
    require(body_match is not None, "V7 deck is missing its body element.")
    script = f'''\n{NUMERIC_DISPLAY_FORMATTER_MARKER}
  <script data-v7-display-number-formatter="true">
    (function () {{
      var token = /(^|[^\\w,.-])(-?(?:\\d{{1,3}}(?:,\\d{{3}})+|\\d+)\\.\\d+)(%?)(?![\\w,.-])/g;
      function normalizeText(value) {{
        return String(value).replace(token, function (whole, prefix, rawNumber, suffix) {{
          var numeric = Number(rawNumber.replace(/,/g, ''));
          if (!Number.isFinite(numeric)) return whole;
          return prefix + new Intl.NumberFormat('en-US', {{
            useGrouping: rawNumber.indexOf(',') >= 0,
            minimumFractionDigits: suffix === '%' ? 1 : 0,
            maximumFractionDigits: 1
          }}).format(numeric) + suffix;
        }});
      }}
      function skip(node) {{
        var parent = node && node.parentElement;
        return parent && /^(SCRIPT|STYLE|CODE|PRE|TEXTAREA)$/i.test(parent.tagName);
      }}
      function normalizeTextNode(node) {{
        if (!node || skip(node)) return;
        var normalized = normalizeText(node.nodeValue);
        if (normalized !== node.nodeValue) node.nodeValue = normalized;
      }}
      function normalizeElement(element) {{
        if (!element || /^(SCRIPT|STYLE|CODE|PRE|TEXTAREA)$/i.test(element.tagName)) return;
        ['title', 'aria-label'].forEach(function (attribute) {{
          if (!element.hasAttribute(attribute)) return;
          var current = element.getAttribute(attribute);
          var normalized = normalizeText(current);
          if (normalized !== current) element.setAttribute(attribute, normalized);
        }});
      }}
      function normalizeSubtree(root) {{
        if (!root) return;
        if (root.nodeType === Node.TEXT_NODE) {{
          normalizeTextNode(root);
          return;
        }}
        if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE) return;
        if (root.nodeType === Node.ELEMENT_NODE) normalizeElement(root);
        var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        var textNode;
        while ((textNode = walker.nextNode())) normalizeTextNode(textNode);
        if (root.querySelectorAll) root.querySelectorAll('[title], [aria-label]').forEach(normalizeElement);
      }}
      var observer = new MutationObserver(function (records) {{
        records.forEach(function (record) {{
          if (record.type === 'characterData') normalizeTextNode(record.target);
          if (record.type === 'attributes') normalizeElement(record.target);
          record.addedNodes.forEach(normalizeSubtree);
        }});
      }});
      observer.observe(document.documentElement, {{
        childList: true,
        subtree: true,
        characterData: true,
        attributes: true,
        attributeFilter: ['title', 'aria-label']
      }});
      if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', function () {{ normalizeSubtree(document.body); }});
      }} else {{
        normalizeSubtree(document.body);
      }}
    }})();
  </script>\n'''
    return deck[:body_match.end()] + script + deck[body_match.end():]


def clarify_annual_attrition_windows(deck: str) -> str:
    """Make every validated annual label explicitly state its 12-month window."""
    overview = stage_fragment(deck, 1)
    old_overview = "Six-month voluntary attrition where V5 has approved evidence"
    new_overview = "Window stated on each slide: six months, 12 months, or YTD; measures are not interchangeable"
    if old_overview in overview:
        deck = replace_stage_fragment(deck, 1, overview.replace(old_overview, new_overview, 1))
    else:
        require(
            'data-v7-intro-population-context="true"' in overview
            and "12 months ending 23 Aug 2026" in overview,
            "V7 overview must disclose its validated 12-month population context.",
        )

    annual_pattern = re.compile(
        r"\bannual (?:team |voluntary )?attrition\b(?!\s*\(12 months\))",
        re.I,
    )
    for slide_number in ANNUAL_ATTRITION_STAGE_IDS:
        stage = stage_fragment(deck, slide_number)
        clarified = annual_pattern.sub(lambda match: match.group(0) + " (12 months)", stage)
        require(
            clarified != stage or "12 months" in stage,
            f"V7 slide {slide_number} lacks an annual attrition phrase to clarify.",
        )
        deck = replace_stage_fragment(deck, slide_number, clarified)
    return deck


def validate_display_number_policy(deck: str) -> None:
    """Validate reader-visible static content after presentation formatting."""
    examples = {
        "628.0": "628",
        "3.64": "3.6",
        "3.65": "3.7",
        "1,234.0": "1,234",
        "1,234.56": "1,234.6",
    }
    for raw, expected in examples.items():
        require(format_display_number(raw) == expected, f"V7 number formatter failed {raw}.")

    require(NUMERIC_DISPLAY_FORMATTER_MARKER in deck, "V7 runtime number formatter is missing.")
    require('maximumFractionDigits: 1' in deck, "V7 runtime number formatter does not cap decimals at one.")
    require('new MutationObserver' in deck, "V7 runtime number formatter does not cover dynamic chart labels.")

    violations: list[str] = []
    segments = PROTECTED_HTML_BLOCK.split(deck)
    for index in range(0, len(segments), 2):
        for token in HTML_TAG_TOKEN.split(segments[index]):
            values = []
            if token.startswith("<"):
                values.extend(match.group("value") for match in DISPLAY_ATTRIBUTE_TOKEN.finditer(token))
            else:
                values.append(token)
            for value in values:
                for match in DISPLAY_NUMBER_TOKEN.finditer(value):
                    rendered = match.group("number")
                    fractional = rendered.rsplit(".", 1)[1]
                    decimal_value = Decimal(rendered.replace(",", ""))
                    if len(fractional) != 1 or (
                        decimal_value == decimal_value.to_integral_value()
                        and match.group("suffix") != "%"
                    ):
                        violations.append(match.group(0))
    require(not violations, f"V7 visible number precision violations: {violations[:8]}")


def validate_attrition_window_language(deck: str) -> None:
    overview = stage_fragment(deck, 1)
    require(
        "Each slide states its own time period." in overview,
        "V7 overview must disclose that attrition windows differ by validated evidence.",
    )
    annual_pattern = re.compile(r"\bannual (?:team |voluntary )?attrition\b(?!\s*\(12 months\))", re.I)
    for slide_number in ANNUAL_ATTRITION_STAGE_IDS:
        unmatched = annual_pattern.findall(stage_fragment(deck, slide_number))
        require(not unmatched, f"V7 slide {slide_number} has annual attrition without its 12-month window: {unmatched[:3]}")

    require("6-month attrition" in stage_fragment(deck, 14), "V7 six-month work-arrangement window changed unexpectedly.")
    manager_proximity = stage_fragment(deck, 42)
    require(
        "Annual voluntary attrition (12 months)" in manager_proximity
        and "24 Aug 2025 baseline cohort followed through 23 Aug 2026" in manager_proximity,
        "V7 manager-timezone slide must disclose its August-to-August annual window.",
    )
    require("YTD attrition" not in manager_proximity and "not annualized" not in manager_proximity, "V7 manager-timezone slide retains obsolete YTD wording.")
    qvoice_open_text = stage_fragment(deck, 20)
    require(
        "2023-2025: 12 months after survey" in qvoice_open_text
        and "2026: YTD through Aug 2026; not annualized" in qvoice_open_text,
        "V7 QVoice open-text slide must retain its historical 12-month and 2026 YTD distinction.",
    )


def commute_attrition_chart_script(deck: str) -> str:
    """Extract the obsolete V6 Plotly script formerly used on slide 19."""
    marker = "var chart = document.getElementById('commute-attrition-chart');"
    marker_at = deck.find(marker)
    require(marker_at >= 0, "Commute-distance Plotly chart script is missing.")
    script_start = deck.rfind("<script", 0, marker_at)
    script_end = deck.find("</script>", marker_at)
    require(script_start >= 0 and script_end >= 0, "Commute-distance Plotly script is malformed.")
    return deck[script_start : script_end + len("</script>")]


def remove_v6_commute_attrition_script(deck: str) -> str:
    """Remove the one-kilometre attrition-line script superseded by the V4 bars."""
    script = commute_attrition_chart_script(deck)
    require(
        "renderCommuteAttritionChart" in script,
        "The obsolete commute-distance script does not have its expected renderer.",
    )
    updated = deck.replace(script, "", 1)
    require(updated != deck, "Could not remove the obsolete commute-distance script.")
    return updated


def remove_v6_commute_attrition_styles(deck: str) -> str:
    """Remove stale V6 CSS selectors for the superseded line-chart layout."""
    updated, removed_rules = re.subn(
        r'^\s*#slide-19 \.commute-attrition[^\{]*\{[^}]*\}\s*\n',
        '',
        deck,
        flags=re.M,
    )
    require(removed_rules >= 5, "Could not remove the obsolete V6 commute-distance styles.")
    old_layout_selector = "    .commute-attrition-layout,\n"
    require(old_layout_selector in updated, "The obsolete V6 commute layout selector is missing.")
    return updated.replace(old_layout_selector, "", 1)


def load_v4_commute_reference() -> tuple[str, Path, str]:
    """Load the frozen V4 commute card, with a V7 fallback when it was archived away."""
    if V4_COMMUTE_REFERENCE_DECK.exists() and V4_COMMUTE_REFERENCE_DECK != OUTPUT_DECK:
        candidate = V4_COMMUTE_REFERENCE_DECK.read_text(encoding="utf-8")
        try:
            article_with_class(candidate, "commute-distance-comparison-card")
        except ValueError:
            # Some V4 exports retained the styling but not the chart card.
            # Fall through to the normalized, already-rendered V7 card.
            pass
        else:
            return candidate, V4_COMMUTE_REFERENCE_DECK, "frozen_v4_reference"

    require(OUTPUT_DECK.exists(), f"Missing V4 commute-chart reference and no current V7 fallback: {V4_COMMUTE_REFERENCE_DECK}")
    fallback_card = article_with_class(
        OUTPUT_DECK.read_text(encoding="utf-8"), "commute-distance-comparison-card"
    )
    cleaned, pill_count = re.subn(
        r'<span class="(?:commute-all-eligible-attrition|commute-onsite-attrition)\b[^"]*".*?</span>',
        "",
        fallback_card,
        flags=re.S,
    )
    require(pill_count == 10, "The current V7 commute fallback must contain ten removable attrition pills.")
    cleaned = cleaned.replace(" commute-attrition-line", "")
    attrition_footer = (
        "<strong>Attrition labels:</strong> Historical six-month voluntary attrition is shown for All eligible and Onsite bands; "
        "each uses its own employee-snapshot denominator, and No calculable is not estimable. "
    )
    require(attrition_footer in cleaned, "The current V7 commute fallback lacks its known attrition footer.")
    cleaned = cleaned.replace(attrition_footer, "", 1)
    require(
        "commute-all-eligible-attrition" not in cleaned
        and "commute-onsite-attrition" not in cleaned
        and "commute-attrition-line" not in cleaned,
        "The normalized V7 commute fallback retains V7 attrition enrichment.",
    )
    return cleaned, OUTPUT_DECK, "normalized_current_v7_card_fallback"


def load_commute_onsite_six_month_attrition_evidence() -> dict[str, Any]:
    """Load the frozen, published Onsite distance attrition evidence."""
    evidence = json.loads(COMMUTE_ONSITE_SIX_MONTH_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "Commute Onsite six-month evidence did not pass validation.")
    contract = evidence.get("outcome_contract", {})
    require(
        contract.get("population") == "Employee, Regular, active_status=1 y work_arrangement=ONSITE en cada snapshot",
        "Commute attrition evidence must be limited to Onsite employee-snapshots.",
    )
    require(
        contract.get("snapshot_window") == "24 snapshots mensuales, 2024-03-24 a 2026-02-22",
        "Commute attrition evidence has an unexpected historical window.",
    )
    require(
        contract.get("target") == "term_type='VOLUNTARY' con term_date en (snapshot_date, snapshot_date + 6 meses]",
        "Commute attrition evidence has an unexpected outcome definition.",
    )
    bands = evidence.get("bands")
    require(isinstance(bands, list) and len(bands) == 31, "Commute attrition evidence must contain 30 one-kilometre bands plus 30+ km.")
    require(
        all(int(row["employee_snapshot_count"]) >= 30 and int(row["voluntary_exits"]) >= 30 for row in bands),
        "Every published Onsite distance band must meet the exposure and voluntary-event threshold.",
    )
    return evidence


def load_cto_org_display_evidence() -> dict[str, Any]:
    """Load the current aggregate distribution for slide 15's lower panel."""
    evidence = json.loads(CTO_ORG_DISPLAY_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "CTO organizational display evidence did not pass validation.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "CTO display evidence must be internal_analysis.")
    rows = evidence.get("category_distribution")
    require(isinstance(rows, list) and len(rows) == 2, "CTO display evidence must contain exactly two categories.")
    by_category = {str(row["category"]): row for row in rows}
    require(set(by_category) == {"CTO", "Corp Fxn & BU"}, "CTO display categories are unexpected.")
    metrics = evidence.get("metrics", {})
    require(
        metrics.get("category_reconciliation_difference") == 0
        and metrics.get("categories_below_minimum_count") == 0,
        "CTO display evidence does not reconcile or has a small category.",
    )
    require(all(int(row["employee_count"]) >= 30 for row in rows), "CTO display category is below the cohort minimum.")
    return evidence


def load_cto_org_annual_attrition_evidence() -> dict[str, Any]:
    """Load the validated historical cohort outcome for the CTO split."""
    evidence = json.loads(CTO_ORG_ANNUAL_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "CTO annual attrition evidence did not pass validation.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "CTO annual evidence must be internal_analysis.")
    require(evidence.get("validation", {}).get("outcome") == "pass", "CTO annual evidence validation is not passing.")
    rows = evidence.get("rows")
    require(isinstance(rows, list) and len(rows) == 2, "CTO annual evidence must contain exactly two categories.")
    by_category = {str(row["category"]): row for row in rows}
    require(set(by_category) == {"CTO", "Corp Fxn & BU"}, "CTO annual categories are unexpected.")
    for row in rows:
        eligible = int(row["eligible_employee_count"])
        exits = int(row["voluntary_exits"])
        rate = float(row["annual_attrition_rate_percent"])
        require(eligible >= 30 and 0 <= exits <= eligible, "CTO annual cohort is invalid.")
        require(abs(rate - (100 * exits / eligible)) < 0.0001, "CTO annual rate does not reconcile to exits and cohort.")
    metrics = evidence.get("metrics", {})
    required_zero_metrics = (
        "category_reconciliation_difference",
        "categories_below_minimum_count",
        "duplicate_source_employee_count",
        "manager_conflict_employee_count",
        "et_leader_conflict_employee_count",
        "branch_a_cycle_count",
        "branch_a_depth_limit_count",
        "branch_a_duplicate_member_count",
        "branch_overlap_count",
    )
    require(all(metrics.get(metric) == 0 for metric in required_zero_metrics), "CTO annual evidence failed a required reconciliation.")
    require(metrics.get("branch_a_root_present") == 1 and metrics.get("branch_b_active_present") == 1, "CTO annual mapping anchor is unavailable.")
    return evidence


def load_commute_all_eligible_six_month_attrition_evidence() -> dict[str, Any]:
    """Load the frozen All eligible distance attrition evidence."""
    evidence = json.loads(COMMUTE_ALL_ELIGIBLE_SIX_MONTH_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "Commute All eligible six-month evidence did not pass validation.")
    contract = evidence.get("outcome_contract", {})
    require(
        contract.get("population") == "Employee, Regular y active_status=1 en cada snapshot, sin filtro de work_arrangement",
        "Commute attrition evidence must use the All eligible employee-snapshot population.",
    )
    require(
        contract.get("snapshot_window") == "24 snapshots mensuales, 2024-03-24 a 2026-02-22",
        "Commute All eligible evidence has an unexpected historical window.",
    )
    require(
        contract.get("target") == "term_type='VOLUNTARY' con term_date en (snapshot_date, snapshot_date + 6 meses]",
        "Commute All eligible evidence has an unexpected outcome definition.",
    )
    bands = evidence.get("bands")
    require(isinstance(bands, list) and len(bands) == 31, "Commute All eligible evidence must contain 30 one-kilometre bands plus 30+ km.")
    require(
        all(int(row["employee_snapshot_count"]) >= 30 and int(row["voluntary_exits"]) >= 30 for row in bands),
        "Every published All eligible distance band must meet the exposure and voluntary-event threshold.",
    )
    return evidence


def load_commute_august_snapshot_evidence() -> dict[str, Any]:
    """Load current All/Onsite distance distributions at the August close."""
    evidence = json.loads(COMMUTE_AUGUST_SNAPSHOT_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("artifact") == "internal_analysis", "Commute August evidence must be internal_analysis.")
    require(evidence.get("snapshot_date") == "2026-08-23", "Commute distribution must use the August fiscal close.")
    require(evidence.get("grain") == "Distinct employee snapshot", "Commute August grain is unexpected.")
    metrics = evidence.get("metrics", {})
    onsite = metrics.get("onsite", {})
    distribution = evidence.get("distribution")
    onsite_distribution = evidence.get("onsite_distribution")
    require(metrics.get("outcome") == "pass" and onsite.get("outcome") == "pass", "Commute August evidence did not pass validation.")
    require(isinstance(distribution, list) and isinstance(onsite_distribution, list), "Commute August distributions are missing.")
    require(
        sum(int(row["employee_count"]) for row in distribution) == int(metrics["matched_distance_employees"]),
        "All-employee commute distance distribution does not reconcile.",
    )
    require(
        sum(int(row["employee_count"]) for row in onsite_distribution) == int(onsite["matched_distance_employees"]),
        "Onsite commute distance distribution does not reconcile.",
    )
    require(
        int(metrics["matched_distance_employees"]) + int(metrics["unavailable_employee_count"]) == int(metrics["eligible_employees"]),
        "All-employee commute coverage does not reconcile.",
    )
    require(
        int(onsite["matched_distance_employees"]) + int(onsite["unavailable_employee_count"]) == int(onsite["eligible_employees"]),
        "Onsite commute coverage does not reconcile.",
    )
    return evidence


def commute_attrition_by_display_band(
    evidence: dict[str, Any],
    population_name: str,
) -> dict[str, dict[str, float | int | None]]:
    """Aggregate frozen 1-km rates to V4's four calculable distance bands.

    The V4 card's ``No calculable`` group is a current-distribution coverage
    bucket. It has no valid distance exposure in the six-month evidence, so it
    remains explicitly not estimable rather than receiving an inferred rate.
    """
    definitions = (
        ("0-<10 km", 0, 10),
        ("10-<20 km", 10, 20),
        ("20-<30 km", 20, 30),
        ("30+ km", 30, None),
    )
    source_bands = evidence["bands"]
    results: dict[str, dict[str, float | int | None]] = {}
    for label, lower, upper in definitions:
        rows = [
            row
            for row in source_bands
            if float(row["lower_km"]) >= lower and (upper is None or float(row["lower_km"]) < upper)
        ]
        require(rows, f"Commute attrition evidence is missing source bands for {label}.")
        exposures = sum(int(row["employee_snapshot_count"]) for row in rows)
        exits = sum(int(row["voluntary_exits"]) for row in rows)
        require(exposures >= 30 and exits >= 30, f"Commute {population_name} attrition band {label} fails the publication threshold.")
        results[label] = {
            "employee_snapshot_count": exposures,
            "voluntary_exits": exits,
            "attrition_rate_percent": 100 * exits / exposures,
        }
    require(
        sum(int(row["employee_snapshot_count"]) for row in results.values())
        == int(evidence["coverage"]["matched_distance_employee_snapshot_count"]),
        f"The V4 display-band aggregation must reconcile to matched-distance {population_name} exposure.",
    )
    require(
        sum(int(row["voluntary_exits"]) for row in results.values())
        == int(evidence["coverage"]["matched_distance_voluntary_exits"]),
        f"The V4 display-band aggregation must reconcile to matched-distance {population_name} voluntary exits.",
    )
    results["No calculable"] = {
        "employee_snapshot_count": None,
        "voluntary_exits": None,
        "attrition_rate_percent": None,
    }
    return results


def commute_onsite_attrition_by_display_band(evidence: dict[str, Any]) -> dict[str, dict[str, float | int | None]]:
    return commute_attrition_by_display_band(evidence, "Onsite")


def commute_all_eligible_attrition_by_display_band(evidence: dict[str, Any]) -> dict[str, dict[str, float | int | None]]:
    return commute_attrition_by_display_band(evidence, "All eligible")


def commute_comparison_row_with_label(card: str, required_label: str) -> str:
    """Return one complete V4 commute comparison row by its rendered band label."""
    row_pattern = re.compile(r'<div\b[^>]*\bclass="[^"]*\bcommute-comparison-row\b[^"]*"[^>]*>', re.I)
    label_pattern = re.compile(
        r'<div\b[^>]*\bclass="[^"]*\bcommute-comparison-label\b[^"]*"[^>]*>(?P<label>.*?)</div>',
        re.I | re.S,
    )
    for match in row_pattern.finditer(card):
        row = card[match.start() : matching_tag_end(card, "div", match.start())]
        label_match = label_pattern.search(row)
        if not label_match:
            continue
        label = html.unescape(re.sub(r"<[^>]+>", "", label_match.group("label"))).strip()
        if label == required_label:
            return row
    raise ValueError(f"Could not find the V4 commute comparison row {required_label!r}.")


def commute_comparison_line_with_series(row: str, required_series: str) -> str:
    """Return one complete V4 series line by its rendered All/Onsite label."""
    line_pattern = re.compile(r'<div\b[^>]*\bclass="[^"]*\bcommute-comparison-line\b[^"]*"[^>]*>', re.I)
    series_pattern = re.compile(
        r'<span\b[^>]*\bclass="[^"]*\bcommute-series-name\b[^"]*"[^>]*>(?P<name>.*?)</span>',
        re.I | re.S,
    )
    for match in line_pattern.finditer(row):
        line = row[match.start() : matching_tag_end(row, "div", match.start())]
        series_match = series_pattern.search(line)
        if not series_match:
            continue
        series = html.unescape(re.sub(r"<[^>]+>", "", series_match.group("name"))).strip()
        if series == required_series:
            return line
    raise ValueError(f"Could not find the V4 commute comparison series {required_series!r}.")


def add_commute_attrition_pills(
    comparison_card: str,
    all_eligible_attrition_by_band: dict[str, dict[str, float | int | None]],
    onsite_attrition_by_band: dict[str, dict[str, float | int | None]],
) -> str:
    """Add Location-style six-month attrition pills to both validated series."""
    updated = comparison_card

    def add_series(
        card: str,
        series_name: str,
        population_name: str,
        pill_class_name: str,
        attrition_by_band: dict[str, dict[str, float | int | None]],
    ) -> str:
        publishable_rates = [
            float(row["attrition_rate_percent"])
            for row in attrition_by_band.values()
            if row["attrition_rate_percent"] is not None
        ]
        require(len(publishable_rates) == 4, f"Expected four calculable {population_name} commute attrition bands.")
        result = card
        for label in ("0-<10 km", "10-<20 km", "20-<30 km", "30+ km", "No calculable"):
            row = commute_comparison_row_with_label(result, label)
            series_line = commute_comparison_line_with_series(row, series_name)
            attrition = attrition_by_band[label]["attrition_rate_percent"]
            if attrition is None:
                pill = (
                    f'<span class="{pill_class_name} v6-rate-pill attr-unavailable is-unavailable" '
                    'title="Six-month voluntary attrition is not estimable because estimated commute distance is not calculable for this group." '
                    'aria-label="Six-month voluntary attrition not estimable">Not estimable</span>'
                )
            else:
                rate = float(attrition)
                pill = (
                    f'<span class="{pill_class_name} v6-rate-pill '
                    + attrition_pill_class(rate, publishable_rates)
                    + f'" title="Six-month voluntary attrition after an {population_name} employee-snapshot: {rate:.1f}%"'
                    + f' aria-label="Six-month voluntary attrition: {rate:.1f}%">{rate:.1f}%</span>'
                )
            marked_line = series_line.replace(
                'class="commute-comparison-line"',
                'class="commute-comparison-line commute-attrition-line"',
                1,
            )
            require(marked_line != series_line, f"Could not mark the {population_name} line for {label}.")
            marked_line = marked_line[:-len("</div>")] + pill + "</div>"
            updated_row = row.replace(series_line, marked_line, 1)
            result = result.replace(row, updated_row, 1)
        return result

    updated = add_series(updated, "All", "All eligible", "commute-all-eligible-attrition", all_eligible_attrition_by_band)
    updated = add_series(updated, "Onsite", "Onsite", "commute-onsite-attrition", onsite_attrition_by_band)
    footer = (
        "The underlying evidence keeps 1-km detail; these bands make the all-vs-Onsite comparison readable. "
        "Percentages use each segment's own denominator. Distance is Haversine km, not route distance or travel time."
    )
    enriched_footer = (
        "<strong>Attrition labels:</strong> Historical six-month voluntary attrition is shown for All eligible and Onsite bands; "
        "each uses its own employee-snapshot denominator, and No calculable is not estimable. "
        + footer
    )
    require(footer in updated, "The V4 commute distance footer is missing.")
    return updated.replace(footer, enriched_footer, 1)


def build_v4_commute_distance_slide(
    v4_reference: str,
    commute_all_eligible_attrition_evidence: dict[str, Any],
    commute_onsite_attrition_evidence: dict[str, Any],
) -> str:
    """Build slide 19 around V4's horizontal bars and validated attrition pills."""
    comparison_card = article_with_class(v4_reference, "commute-distance-comparison-card")
    if "commute-all-eligible-attrition" not in comparison_card:
        comparison_card = add_commute_attrition_pills(
            comparison_card,
            commute_all_eligible_attrition_by_display_band(commute_all_eligible_attrition_evidence),
            commute_onsite_attrition_by_display_band(commute_onsite_attrition_evidence),
        )
    return (
        '\n  <div class="slide-stage" id="slide-19" data-v6-playbook="true"><div class="slide-heading"><div>'
        '<h2 class="slide-title-text">Commute distance</h2>'
        '<p class="slide-subtitle">Approximate geographic proxy · postal centroid to Qualcomm office coordinate · all eligible vs Onsite</p>'
        '</div><span class="badge badge-info">Distribution + 6-month attrition</span></div>'
        '<article class="card card-full v6-playbook-card">'
        '<div class="v6-definition-strip"><div><span class="v6-mini-label">Definition</span>'
        '<strong>Estimated straight-line distance between residential and office postal centroids.</strong>'
        '</div><div><span class="v6-mini-label">Population</span>'
        '<strong>All eligible and Onsite active regular employee-snapshots · snapshot 2026-09-27</strong>'
        '</div></div><div class="v6-chart-area"><div class="commute-distance-comparison-layout">'
        + comparison_card
        + '</div></div><div class="v6-source-line"><strong>Source:</strong> HRDA workforce snapshots + Qualcomm office model + postal-centroid reference. Distribution is the latest snapshot; All eligible and Onsite attrition are voluntary exits in the six months after 24 historical monthly snapshots. Distance is an approximate geographic proxy, not route distance or travel time.</div>'
        '</article></div>'
    )


def replace_commute_distance_slide(
    deck: str,
    v4_reference: str,
    commute_all_eligible_attrition_evidence: dict[str, Any],
    commute_onsite_attrition_evidence: dict[str, Any],
) -> str:
    """Replace V6's line chart with V4's bars and two validated attrition series."""
    pattern = r'\s*<div class="slide-stage" id="slide-19".*?(?=\n\s*<div class="slide-stage" id="slide-20")'
    replacement = build_v4_commute_distance_slide(
        v4_reference,
        commute_all_eligible_attrition_evidence,
        commute_onsite_attrition_evidence,
    )
    replacement, subtitle_replacements = re.subn(
        r'(<h2 class="slide-title-text">Commute distance</h2>)<p class="slide-subtitle">.*?</p>',
        r'\1<p class="slide-subtitle">Latest distribution; historical six-month attrition labels for validated All eligible and Onsite distance bands</p>',
        replacement,
        count=1,
        flags=re.S,
    )
    require(subtitle_replacements == 1, "Could not apply the commute-distance attrition subtitle.")
    updated, replacements = re.subn(pattern, replacement, deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate exactly one V6 slide 19 block.")
    return updated


def validate_v4_commute_distance_restoration(
    deck: str,
    v4_reference: str,
    commute_all_eligible_attrition_evidence: dict[str, Any],
    commute_onsite_attrition_evidence: dict[str, Any],
) -> None:
    """Verify the V4 distribution plus validated All eligible and Onsite rates."""
    reference_card = article_with_class(v4_reference, "commute-distance-comparison-card")
    restored_card = article_with_class(deck, "commute-distance-comparison-card")
    require(restored_card.count('class="commute-comparison-row"') == 5, "Slide 19 must contain five distance-band rows.")
    require(restored_card.count("commute-comparison-line") == 10, "Slide 19 must contain two bars per distance band.")
    for expected in (
        "0-&lt;10 km", "10-&lt;20 km", "20-&lt;30 km", "30+ km", "No calculable",
        "28.5% · 14,293", "30% · 13,626", "20.7% · 10,414", "21.7% · 9,875",
        "6.9% · 3,481", "7.1% · 3,213", "27% · 13,572", "28.2% · 12,822",
        "16.8% · 8,447", "13% · 5,897",
    ):
        require(expected in restored_card, f"Slide 19 is missing the V4 comparison value {expected!r}.")
    for fill_width in re.findall(r'class="bar-fill[^\"]*" style="width:([^\"]+)"', reference_card):
        require(
            f'style="width:{fill_width}"' in restored_card,
            f"Slide 19 is missing the V4 distribution-bar width {fill_width!r}.",
        )
    series = (
        ("All eligible", "commute-all-eligible-attrition", commute_all_eligible_attrition_by_display_band(commute_all_eligible_attrition_evidence)),
        ("Onsite", "commute-onsite-attrition", commute_onsite_attrition_by_display_band(commute_onsite_attrition_evidence)),
    )
    for series_name, pill_prefix, attrition_by_band in series:
        publishable_rates = [
            float(row["attrition_rate_percent"])
            for row in attrition_by_band.values()
            if row["attrition_rate_percent"] is not None
        ]
        require(restored_card.count(f"{pill_prefix} v6-rate-pill") == 5, f"Slide 19 must show one {series_name} attrition pill per distance band.")
        for label, row in attrition_by_band.items():
            attrition = row["attrition_rate_percent"]
            if attrition is None:
                require(
                    f'{pill_prefix} v6-rate-pill attr-unavailable is-unavailable' in restored_card,
                    "Slide 19 must mark No calculable attrition as not estimable.",
                )
            else:
                rate = float(attrition)
                expected_class = attrition_pill_class(rate, publishable_rates)
                require(
                    f'{pill_prefix} v6-rate-pill {expected_class}' in restored_card
                    and f'>{rate:.1f}%</span>' in restored_card,
                    f"Slide 19 is missing the validated {label} {series_name} attrition pill.",
                )
    require("Historical six-month voluntary attrition is shown for All eligible and Onsite bands" in restored_card, "Slide 19 must explain both attrition lenses.")
    require(
        "commute-attrition-chart" not in deck and "renderCommuteAttritionChart" not in deck,
        "Slide 19 must not retain the superseded one-kilometre attrition line chart or its script.",
    )


def validate_commute_august_snapshot(
    deck: str,
    snapshot_evidence: dict[str, Any],
    all_eligible_attrition_evidence: dict[str, Any],
    onsite_attrition_evidence: dict[str, Any],
) -> None:
    """Verify current distribution counts and retained historical labels separately."""
    stage = stage_fragment(deck, 19)
    require('data-v7-commute-august-snapshot="true"' in stage, "V7 Commute August replacement is missing.")
    require("2026-09" not in stage and "September" not in stage, "V7 Commute slide still references a September snapshot.")
    require("snapshot 23 Aug 2026" in stage, "V7 Commute slide must identify the August snapshot.")
    require(stage.count('class="commute-comparison-row"') == 5, "V7 Commute slide must contain five distance rows.")
    require(stage.count("commute-comparison-line") == 10, "V7 Commute slide must contain All and Onsite for every row.")
    metrics = snapshot_evidence["metrics"]
    onsite_metrics = metrics["onsite"]
    all_counts = commute_snapshot_display_bands(snapshot_evidence["distribution"], int(metrics["unavailable_employee_count"]))
    onsite_counts = commute_snapshot_display_bands(snapshot_evidence["onsite_distribution"], int(onsite_metrics["unavailable_employee_count"]))
    for label, count in all_counts.items():
        require(html.escape(label) in stage and f"{count:,}" in stage, f"V7 Commute slide is missing All August count for {label}.")
    for count in onsite_counts.values():
        require(f"{count:,}" in stage, "V7 Commute slide is missing an Onsite August count.")
    require(f"All eligible ({int(metrics['eligible_employees']):,})" in stage, "V7 Commute slide is missing the All August denominator.")
    require(f"Onsite ({int(onsite_metrics['eligible_employees']):,})" in stage, "V7 Commute slide is missing the Onsite August denominator.")
    for prefix, evidence, population in (
        ("commute-all-eligible-attrition", all_eligible_attrition_evidence, "All eligible"),
        ("commute-onsite-attrition", onsite_attrition_evidence, "Onsite"),
    ):
        rates_by_band = commute_attrition_by_display_band(evidence, population)
        rates = [float(row["attrition_rate_percent"]) for row in rates_by_band.values() if row["attrition_rate_percent"] is not None]
        require(stage.count(prefix) == 5, f"V7 Commute slide must retain five historical {population} labels.")
        for row in rates_by_band.values():
            rate = row["attrition_rate_percent"]
            if rate is None:
                require(f"{prefix} v6-rate-pill attr-unavailable is-unavailable" in stage, "V7 Commute must mark No calculable historical attrition as N/E.")
            else:
                numeric_rate = float(rate)
                expected_class = attrition_pill_class(numeric_rate, rates)
                require(
                    f"{prefix} v6-rate-pill {expected_class}" in stage and f">{numeric_rate:.1f}%</span>" in stage,
                    f"V7 Commute is missing a historical {population} attrition label.",
                )
    require("historical six-month voluntary attrition" in stage, "V7 Commute must distinguish its historical rate labels from the August distribution.")
    require("commute-attrition-chart" not in deck and "renderCommuteAttritionChart" not in deck, "V7 Commute retains the superseded line chart.")


def load_evidence() -> dict[str, Any]:
    evidence = json.loads(EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("reporting_mode") == "internal_analysis", "V7 evidence must use internal_analysis.")
    require(evidence.get("deliverable_classification") == "internal_analysis", "V7 evidence classification is incorrect.")
    rows = evidence.get("rows")
    require(isinstance(rows, list) and len(rows) == 21, "Expected 21 frozen IOS group-year rows.")
    require(evidence.get("validation", {}).get("outcome") == "pass", "Frozen evidence did not pass validation.")
    pairs = {(row["calendar_year"], row["group_key"]) for row in rows}
    expected_pairs = {(year, group_key) for year in YEARS for group_key in GROUP_KEYS}
    require(pairs == expected_pairs, "Frozen evidence does not contain the expected three-year IOS matrix.")
    require(all(row["observed_monthly_snapshots"] == 8 for row in rows), "Each year must use eight monthly snapshots.")
    require(all(row["cohort_n"] is not None for row in rows), "Internal IOS evidence must retain every cohort count.")
    require(all(row["workforce_share_percent"] is not None for row in rows), "Internal IOS evidence must retain every workforce percentage.")
    require(
        all(
            row["post_event_voluntary_attrition_percent"] is not None
            or int(row["cohort_n"]) == 0
            for row in rows
        ),
        "Internal IOS evidence may omit attrition only when the cohort denominator is zero.",
    )
    require(
        all(row["publication_status"] in {"publish", "internal_analysis_exception"} for row in rows),
        "Unexpected IOS publication status.",
    )
    return evidence


def load_application_evidence() -> dict[str, Any]:
    evidence = json.loads(APPLICATION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("reporting_mode") == "internal_analysis", "Application evidence must use internal_analysis.")
    require(evidence.get("artifact_classification") == "internal_analysis", "Application evidence classification is incorrect.")
    latest = evidence.get("latest_distribution")
    trend = evidence.get("trend")
    require(isinstance(latest, list) and len(latest) == 4, "Internal application evidence must have four latest buckets.")
    require(isinstance(trend, list) and len(trend) == 12, "Internal application evidence must have twelve trend points.")
    require({row["application_bucket"] for row in latest} == set(("0", "1", "2+", "Unknown")), "Latest application buckets are incomplete.")
    require(
        all(
            all(item["buckets"][bucket]["percent_of_eligible_snapshots"] is not None for bucket in ("0", "1", "2+", "Unknown"))
            for item in trend
        ),
        "Internal application trend must retain every bucket percentage.",
    )
    return evidence


def load_application_attrition_evidence() -> dict[str, Any]:
    evidence = json.loads(APPLICATION_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("reporting_mode") == "internal_analysis", "Application attrition evidence must use internal_analysis.")
    require(evidence.get("artifact_classification") == "internal_analysis", "Application attrition classification is incorrect.")
    require(evidence.get("outcome") == "pass" and evidence.get("validation", {}).get("outcome") == "pass", "Application attrition evidence did not pass validation.")
    require(evidence.get("artifact") == "application_intensity_trailing_12m_august_attrition", "Application attrition evidence has the wrong definition.")
    require(evidence.get("semantic_type") == "derived_feature", "Application attrition must be documented as a derived feature.")
    require(evidence.get("visible_slide_cutoffs") == [2025, 2026], "Slide 3 must use the two latest August cutoffs.")
    require(evidence.get("evidence_only_cutoffs") == [2022, 2023, 2024], "Historical August cutoffs must remain evidence only.")
    authorization = evidence.get("authorization", {})
    require(
        authorization.get("scope", {}).get("trailing_12m_august_application_attrition", {}).get("subthreshold_aggregate_buckets_authorized"),
        "Rolling-August small-cell authorization is missing.",
    )
    rows = evidence.get("rows")
    require(isinstance(rows, list) and len(rows) == 20, "Application attrition evidence must contain twenty August-cutoff/bucket rows.")
    expected = {(year, bucket) for year in (2022, 2023, 2024, 2025, 2026) for bucket in ("1", "2", "3", "4+")}
    require({(int(row["cutoff_year"]), str(row["application_bucket"])) for row in rows} == expected, "Application attrition matrix is incomplete.")
    main_query = evidence.get("provenance", {}).get("main_query", {})
    query_path = ROOT / str(main_query.get("path", ""))
    require(query_path.exists() and digest(query_path) == main_query.get("sha256"), "Rolling-August attrition SQL provenance is invalid.")
    canonical_rows = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    require(
        hashlib.sha256(canonical_rows.encode("utf-8")).hexdigest() == main_query.get("result_sha256"),
        "Rolling-August attrition result hash does not match its aggregate rows.",
    )
    for row in rows:
        denominator = int(row["distinct_applicant_count"])
        exits = int(row["voluntary_exit_count"])
        rate = row["trailing_12m_voluntary_attrition_percent"]
        require(denominator > 0 and 0 <= exits <= denominator, "Rolling-August numerator or denominator is invalid.")
        require(rate is not None and abs(float(rate) - round(100 * exits / denominator, 2)) < 0.000001, "Rolling-August rate does not reconcile.")
    return evidence


def load_gender_label_evidence() -> dict[str, Any]:
    evidence = json.loads(GENDER_LABEL_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("artifact_classification") == "internal_analysis", "Gender label evidence must be internal_analysis.")
    require(evidence.get("reporting_mode") == "internal_analysis", "Gender label evidence reporting mode is incorrect.")
    require(evidence.get("semantic_type") == "direct_field", "Gender labels must be validated as a direct field.")
    require(evidence.get("outcome") == "pass", "Gender label evidence did not pass.")
    query = evidence.get("query", {})
    query_path = ROOT / str(query.get("path", ""))
    require(query_path.exists(), "Gender label audit SQL is missing.")
    require(digest(query_path) == query.get("sha256"), "Gender label audit SQL hash does not match its evidence.")
    rows = evidence.get("rows")
    require(isinstance(rows, list) and len(rows) >= 2, "Gender label evidence must retain its aggregate domain.")
    canonical_rows = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    require(
        hashlib.sha256(canonical_rows.encode("utf-8")).hexdigest() == query.get("result_sha256"),
        "Gender label evidence result hash does not match its aggregate rows.",
    )
    labels = {str(row["gender"]): row for row in rows}
    for label in ("F", "M"):
        require(label in labels, f"Validated stored gender label is missing: {label}")
        require(int(labels[label]["employee_count"]) >= 30, f"Validated gender label is below n=30: {label}")
        require(int(labels[label]["snapshot_count"]) == 6, f"Validated gender label does not cover six snapshots: {label}")
    require(evidence.get("display_mapping") == {"Category A": "F", "Category B": "M"}, "Gender display mapping is unexpected.")
    return evidence


def load_work_arrangement_group_evidence() -> dict[str, float]:
    """Derive the three displayed attrition rates from published aggregates.

    The third group is not an average of rounded labels.  It is the exact
    residual of the validated non-onsite aggregate after removing the
    Short-Term Remote Work row, using employee-snapshots and exits.
    """
    evidence = json.loads(SIX_MONTH_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("deliverable_mode") == "internal_analysis", "Six-month work-arrangement evidence must be internal_analysis.")
    require(evidence.get("outcome") == "pass", "Six-month work-arrangement evidence did not pass.")

    rows = {
        str(row["category"]): row
        for row in evidence.get("rows", [])
        if row.get("metric") in {"work_arrangement", "work_arrangement_binary"}
    }
    onsite = rows.get("Onsite")
    short_term_remote = rows.get("Interim Modified – Short-Term Remote Work")
    other_non_onsite = rows.get("Other stored values (0)")
    require(onsite is not None, "Six-month evidence is missing the Onsite work-arrangement row.")
    require(short_term_remote is not None, "Six-month evidence is missing the Short-Term Remote Work row.")
    require(other_non_onsite is not None, "Six-month evidence is missing the non-onsite aggregate row.")

    other_snapshots = int(other_non_onsite["employee_snapshot_count"]) - int(short_term_remote["employee_snapshot_count"])
    other_exits = int(other_non_onsite["voluntary_exits"]) - int(short_term_remote["voluntary_exits"])
    require(other_snapshots > 0 and other_exits >= 0, "The derived remaining non-onsite group is invalid.")

    return {
        "onsite_rate": float(onsite["attrition_rate_percent"]),
        "short_term_remote_rate": float(short_term_remote["attrition_rate_percent"]),
        "other_offsite_rate": 100 * other_exits / other_snapshots,
        "other_offsite_snapshots": float(other_snapshots),
        "other_offsite_exits": float(other_exits),
    }


def load_rehire_annual_attrition_evidence() -> dict[str, Any]:
    evidence = json.loads(REHIRE_ANNUAL_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("artifact_classification") == "internal_analysis", "Rehire annual evidence must be internal_analysis.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "Rehire annual evidence reporting mode is incorrect.")
    require(evidence.get("outcome") == "pass", "Rehire annual evidence did not pass.")
    rows = evidence.get("rows")
    expected_years = ("2020", "2021", "2023", "2024", "2025", "2026")
    require(isinstance(rows, list) and tuple(str(row.get("fiscal_year")) for row in rows) == expected_years, "Rehire annual evidence must contain the six audited fiscal years in order.")
    return evidence


def load_rehire_august_trailing_12m_evidence() -> dict[str, Any]:
    """Load the three comparable August-to-August Rehire cohorts."""
    evidence = json.loads(REHIRE_AUGUST_TRAILING_12M_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("artifact_classification") == "internal_analysis", "August Rehire evidence must be internal_analysis.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "August Rehire reporting mode is incorrect.")
    require(evidence.get("outcome") == "pass", "August Rehire evidence did not pass.")
    rows = evidence.get("rows")
    require(
        isinstance(rows, list) and tuple(str(row.get("fiscal_year")) for row in rows) == REHIRE_VISIBLE_FISCAL_YEARS,
        "August Rehire evidence must contain FY2024-FY2026 in order.",
    )
    for row in rows:
        cohort = int(row["baseline_rehire_employee_count"])
        distinct = int(row["distinct_employee_count"])
        exits = int(row["voluntary_exit_count"])
        rate = float(row["trailing_12m_voluntary_attrition_rate_percent"])
        require(cohort >= 30 and distinct == cohort and 0 <= exits <= cohort, "An August Rehire cohort is invalid.")
        require(abs(rate - 100 * exits / cohort) < 0.00011, "An August Rehire T12 rate does not reconcile.")
        require(str(row["publication_status"]) == "publishable_trailing_12m", "An August Rehire rate is not publishable.")
    return evidence


def load_rehire_comparison_august_trailing_12m_evidence() -> dict[str, Any]:
    """Load the three historical August Rehire versus non-Rehire comparisons."""
    evidence = json.loads(REHIRE_COMPARISON_AUGUST_TRAILING_12M_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("artifact_classification") == "presentation", "Rehire complement evidence must be presentation-classified.")
    require(evidence.get("deliverable_mode") == "presentation", "Rehire complement reporting mode is incorrect.")
    require(evidence.get("outcome") == "pass", "Rehire complement evidence did not pass.")
    rows = evidence.get("rows")
    require(
        isinstance(rows, list)
        and len(rows) == 6
        and tuple(str(row.get("fiscal_year")) for row in rows[::2]) == REHIRE_VISIBLE_FISCAL_YEARS
        and all(
            tuple(str(row.get("rehire_group")) for row in rows[index : index + 2])
            == ("Rehire", "Not a rehire")
            for index in range(0, len(rows), 2)
        ),
        "Rehire comparison evidence must contain Rehire and Not a rehire for FY2024-FY2026 in order.",
    )
    baseline_totals: dict[str, int] = {}
    for row in rows:
        cohort = int(row["baseline_employee_count"])
        distinct = int(row["distinct_employee_count"])
        exits = int(row["voluntary_exit_count"])
        rate = float(row["trailing_12m_voluntary_attrition_rate_percent"])
        duplicate_count = int(row["duplicate_employee_snapshot_count"])
        require(cohort >= 30 and distinct == cohort and duplicate_count == 0 and 0 <= exits <= cohort, "A Rehire complement cohort is invalid.")
        require(abs(rate - 100 * exits / cohort) < 0.00011, "A Rehire complement T12 rate does not reconcile.")
        year = str(row["fiscal_year"])
        baseline_totals[year] = baseline_totals.get(year, 0) + cohort
    require(baseline_totals == {"2024": 42666, "2025": 42167, "2026": 45003}, "Historical Rehire cohorts do not reconcile by fiscal year.")
    require(str(evidence["definition"]["outcome"]) == "Strict VOLUNTARY termination in (baseline_snapshot_date, outcome_cutoff_date]", "The historical Rehire comparison window is incorrect.")
    return evidence


def load_job_family_august_snapshot_evidence() -> dict[str, Any]:
    """Load the single fiscal-August Job family distribution."""
    evidence = json.loads(JOB_FAMILY_AUGUST_SNAPSHOT_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("artifact_classification") == "internal_analysis", "Job family August evidence must be internal_analysis.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "Job family August reporting mode is incorrect.")
    require(evidence.get("outcome") == "pass", "Job family August evidence did not pass.")
    snapshot = evidence.get("snapshot", {})
    require(snapshot.get("snapshot_date") == "2026-08-23", "Job family must use the 2026 fiscal-August closing snapshot.")
    active = int(snapshot["active_regular_employee_count"])
    observable = int(snapshot["observable_employee_count"])
    top_total = int(snapshot["top_20_employee_count"])
    other = int(snapshot["other_job_families_employee_count"])
    rows = evidence.get("top_20")
    require(active == observable and top_total + other == observable, "Job family August distribution does not reconcile.")
    require(isinstance(rows, list) and len(rows) == 20, "Job family August evidence must contain 20 ranked categories.")
    require(all(int(row["employee_count"]) >= 30 for row in rows) and other >= 30, "A Job family August display category is below n=30.")
    return evidence


def load_job_family_august_trailing_12m_attrition_evidence() -> dict[str, Any]:
    """Load the August Job family distribution plus historical 12-month rates."""
    evidence = json.loads(JOB_FAMILY_AUGUST_TRAILING_12M_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("artifact_classification") == "presentation", "Job family trailing-12-month evidence must be presentation-classified.")
    require(evidence.get("deliverable_mode") == "presentation", "Job family trailing-12-month reporting mode is incorrect.")
    require(evidence.get("outcome") == "pass", "Job family trailing-12-month evidence did not pass.")
    window = evidence.get("window", {})
    require(window.get("current_snapshot_date") == "2026-08-23", "Job family attrition must use the August 2026 display snapshot.")
    require(window.get("baseline_snapshot_date") == "2025-08-24", "Job family attrition must use the August 2025 baseline snapshot.")
    require(window.get("outcome_cutoff_date") == "2026-08-23", "Job family attrition must end at the August 2026 cutoff.")
    rows = evidence.get("rows")
    require(isinstance(rows, list) and len(rows) == 21, "Job family trailing-12-month evidence must contain 21 display categories.")
    require([int(row["display_order"]) for row in rows] == list(range(1, 22)), "Job family display categories must be ordered 1 through 21.")
    require(len({str(row["category_label"]) for row in rows}) == 21, "Job family display categories must be unique.")
    summary = evidence.get("summary", {})
    require(int(summary["current_duplicate_source_rows"]) == 0 and int(summary["baseline_duplicate_source_rows"]) == 0, "Job family snapshots contain duplicate employee rows.")
    require(int(summary["baseline_extra_job_family_mappings"]) == 0, "Job family baseline contains contradictory employee-to-family mappings.")
    require(int(summary["display_category_count"]) == 21, "Job family summary category count is incorrect.")
    require(
        sum(int(row["current_employee_count"]) for row in rows) == int(summary["current_observable_employees"]),
        "Job family current distribution does not reconcile.",
    )
    require(
        sum(int(row["baseline_employee_count"]) for row in rows) == int(summary["baseline_observable_employees"]),
        "Job family baseline categories do not reconcile.",
    )
    rates = []
    for row in rows:
        baseline = int(row["baseline_employee_count"])
        exits = int(row["voluntary_exit_count"])
        rate = float(row["trailing_12m_voluntary_attrition_rate_percent"])
        require(baseline >= 30 and 0 <= exits <= baseline, "A Job family attrition cohort is invalid.")
        require(abs(rate - (100.0 * exits / baseline)) < 0.00011, "A Job family trailing-12-month rate does not reconcile.")
        rates.append(rate)
    require(min(rates) >= 0 and max(rates) <= 100, "A Job family attrition rate is outside the valid range.")
    return evidence


def load_rehire_fy2026_observed_attrition_evidence() -> dict[str, Any]:
    """Load the realized FY2026 rate, which is distinct from forward follow-up."""
    evidence = json.loads(REHIRE_FY2026_OBSERVED_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("artifact_classification") == "internal_analysis", "FY2026 Rehire observed evidence must be internal_analysis.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "FY2026 Rehire observed evidence reporting mode is incorrect.")
    require(evidence.get("outcome") == "pass", "FY2026 Rehire observed evidence did not pass.")
    row = evidence.get("row")
    require(isinstance(row, dict), "FY2026 Rehire observed evidence must contain one aggregate row.")
    require(str(row.get("publication_status")) == "publishable_observed_period_rate", "FY2026 Rehire observed rate is not publishable.")
    require(int(row.get("observed_snapshot_count") or 0) >= 12, "FY2026 Rehire observed rate requires 12 monthly snapshots.")
    require(int(row.get("employee_snapshot_count") or 0) >= 30, "FY2026 Rehire observed rate is below the employee-snapshot threshold.")
    require(int(row.get("distinct_employee_count") or 0) >= 30, "FY2026 Rehire observed rate is below the distinct-employee threshold.")
    headcount = float(row.get("average_monthly_rehire_headcount") or 0)
    rate = float(row.get("observed_voluntary_attrition_rate_percent") or -1)
    exits = int(row.get("voluntary_exit_count") or 0)
    require(headcount > 0 and rate >= 0, "FY2026 Rehire observed rate lacks a valid denominator or rate.")
    require(abs(rate - 100 * exits / headcount) < 0.0001, "FY2026 Rehire observed rate does not reconcile.")
    return evidence


def load_qvoice_wave_attrition_evidence() -> dict[str, Any]:
    """Load annual QVoice-wave labels for the slide-20 table only."""
    evidence = json.loads(QVOICE_WAVE_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("artifact") == "internal_analysis", "QVoice wave evidence must be internal_analysis.")
    require(evidence.get("outcome") == "pass" and evidence.get("validation", {}).get("outcome") == "pass", "QVoice wave evidence did not pass validation.")
    require(evidence.get("minimum_shared_cohort") == 30, "QVoice wave evidence must retain the n=30 rule.")
    rows = evidence.get("waves")
    expected_waves = ("Mar-2023", "Jan-2024", "Jan-2025", "Jan-2026")
    require(isinstance(rows, list) and tuple(str(row.get("wave")) for row in rows) == expected_waves, "QVoice wave labels are incomplete or out of order.")
    for index, row in enumerate(rows):
        matched = int(row["matched_employee_count"])
        exits = int(row["voluntary_exit_count"])
        rate = float(row["voluntary_attrition_rate_percent"])
        require(matched >= 30 and 0 <= exits <= matched, "A QVoice wave attrition cohort is not publishable.")
        require(abs(rate - 100 * exits / matched) < 0.00011, "A QVoice wave attrition rate does not reconcile.")
        outcome_type = str(row["outcome_type"])
        expected_type = "ytd" if index == 3 else "annual_12m"
        expected_label = f"YTD attrition · {rate:.1f}%" if outcome_type == "ytd" else f"Annual attrition · {rate:.1f}%"
        require(outcome_type == expected_type and str(row["label"]) == expected_label, "A QVoice wave label has an invalid annual/YTD contract.")
    require(str(rows[-1]["baseline_snapshot"]) == "2025-12-28" and str(rows[-1]["outcome_start"]) == "2026-01-07", "QVoice 2026 YTD boundary is unexpected.")
    require(evidence.get("validation", {}).get("all_historical_waves_have_complete_12_month_followup") is True, "Historical QVoice waves require complete follow-up.")
    encoded = json.dumps(evidence, ensure_ascii=False)
    for prohibited in ('"employee_id"', '"emp_id"', '"raw_comment"', '"comment_text"'):
        require(prohibited not in encoded, f"QVoice wave evidence must not persist {prohibited}.")
    return evidence


def load_qvoice_ytd_group_attrition_evidence() -> dict[str, Any]:
    """Load the aggregate 2026-YTD QVoice group attrition evidence."""
    evidence = json.loads(QVOICE_YTD_GROUP_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("artifact") == "internal_analysis", "QVoice YTD evidence must be internal_analysis.")
    require(evidence.get("outcome") == "pass" and evidence.get("validation", {}).get("outcome") == "pass", "QVoice YTD evidence did not pass validation.")
    require(evidence.get("minimum_shared_cohort") == 30, "QVoice YTD evidence must retain the n=30 rule.")
    contract = evidence.get("outcome_contract", {})
    require(contract.get("baseline_snapshot") == "2025-12-28", "QVoice YTD baseline snapshot is unexpected.")
    require(contract.get("survey_launch_date") == "2026-01-07", "QVoice YTD survey launch is unexpected.")
    require(contract.get("outcome_window") == "(2026-01-07, 2026-09-27]", "QVoice YTD outcome window is unexpected.")
    require(contract.get("label") == "Voluntary attrition YTD 2026; not annualized", "QVoice YTD rate must remain non-annualized.")
    slides = evidence.get("slides")
    require(isinstance(slides, dict) and set(slides) == {str(slide) for slide in range(20, 28)}, "QVoice YTD evidence must cover slides 20–27.")
    expected_groups = {
        "20": {"Remote / WFH", "Hybrid", "RTO / office attendance"},
        "21": set(evidence.get("validation", {}).get("retention_display_order", [])),
        "22": {"Responded", "QVoice row / no answer", "No QVoice row"},
        "24": {"0", "1"},
        "26": {"Heartbeat eligible"},
    }
    for slide, expected in expected_groups.items():
        rows = slides.get(slide)
        require(isinstance(rows, dict) and set(rows) == expected, f"QVoice slide {slide} attrition groups are incomplete.")
    require(isinstance(slides["25"], dict) and len(slides["25"]) == 6, "QVoice score-band attrition groups are incomplete.")
    require(isinstance(slides["27"], dict) and len(slides["27"]) == 5, "QVoice standardized-score attrition groups are incomplete.")
    intent = slides.get("23")
    require(isinstance(intent, dict) and set(intent) == {"intent_see_myself", "intent_rarely_look"}, "QVoice intent groups are incomplete.")
    require(all(isinstance(values, dict) and set(values) == {"0", "1"} for values in intent.values()), "QVoice intent values must retain stored 0 and 1.")
    for slide_rows in slides.values():
        groups = slide_rows.values() if isinstance(slide_rows, dict) else []
        for row in groups:
            if isinstance(row, dict) and "matched_employee_count" not in row:
                groups = row.values()
                for nested in groups:
                    denominator = int(nested["matched_employee_count"])
                    exits = int(nested["voluntary_exit_count"])
                    rate = float(nested["ytd_voluntary_attrition_rate_percent"])
                    require(denominator >= 30 and 0 <= exits <= denominator, "A QVoice YTD group is not publishable.")
                    require(abs(rate - 100 * exits / denominator) < 0.00011, "A QVoice YTD rate does not reconcile to exits and cohort.")
            else:
                denominator = int(row["matched_employee_count"])
                exits = int(row["voluntary_exit_count"])
                rate = float(row["ytd_voluntary_attrition_rate_percent"])
                require(denominator >= 30 and 0 <= exits <= denominator, "A QVoice YTD group is not publishable.")
                require(abs(rate - 100 * exits / denominator) < 0.00011, "A QVoice YTD rate does not reconcile to exits and cohort.")
    encoded = json.dumps(evidence, ensure_ascii=False)
    for prohibited in ('"employee_id"', '"emp_id"', '"raw_comment"', '"comment_text"'):
        require(prohibited not in encoded, f"QVoice YTD evidence must not persist {prohibited}.")
    return evidence


def load_qvoice_favorable_unfavorable_attrition_evidence() -> dict[str, Any]:
    """Load aggregate driver and component QVoice response-group evidence for slides 19–20."""
    evidence = json.loads(QVOICE_FAVORABLE_UNFAVORABLE_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("artifact") == "presentation", "QVoice response-group evidence must be presentation classified.")
    require(evidence.get("outcome") == "pass" and evidence.get("validation", {}).get("outcome") == "pass", "QVoice response-group evidence did not pass validation.")
    require(evidence.get("minimum_shared_cohort") == 30, "QVoice response-group evidence must retain the n=30 rule.")
    validation = evidence["validation"]
    for key in (
        "header_mapping_exactly_once_per_wave",
        "all_source_participant_keys_unique",
        "all_display_groups_mutually_exclusive",
        "linked_response_shares_sum_to_100_percent",
        "component_groups_mutually_exclusive",
        "component_response_shares_sum_to_100_percent",
        "historical_waves_have_complete_12_month_followup",
        "jan_2026_is_ytd_not_annualized",
    ):
        require(validation.get(key) is True, f"QVoice response-group validation failed: {key}.")
    variables = evidence.get("variables")
    require(isinstance(variables, dict) and set(variables) == {"intent_to_stay", "career_goals"}, "QVoice response-group metrics are incomplete.")
    for metric, rows in variables.items():
        require(isinstance(rows, list) and [int(row.get("year")) for row in rows] == [2024, 2025, 2026], f"QVoice {metric} years are incomplete.")
        for row in rows:
            expected_type = "ytd" if int(row["year"]) == 2026 else "annual_12m"
            require(str(row["outcome_type"]) == expected_type, f"QVoice {metric} has an invalid outcome type.")
            if expected_type == "ytd":
                require(str(row["outcome_end"]) == "2026-09-27", "QVoice 2026 must retain the YTD cutoff.")
            groups = row.get("groups")
            require(isinstance(groups, dict) and set(groups) == {"Favorable", "No favorable"}, f"QVoice {metric} groups are incomplete.")
            share_total = 0.0
            for group in groups.values():
                matched = int(group["matched_employee_count"])
                exits = int(group["voluntary_exit_count"])
                rate = float(group["voluntary_attrition_rate_percent"])
                share = float(group["linked_response_share_percent"])
                require(matched >= 30 and 0 <= exits <= matched, f"QVoice {metric} group is not publishable.")
                require(abs(rate - 100 * exits / matched) < 0.00011, f"QVoice {metric} rate does not reconcile.")
                share_total += share
            require(abs(share_total - 100) < 0.0002, f"QVoice {metric} shares do not sum to 100%.")
            components = row.get("components")
            require(isinstance(components, dict) and components, f"QVoice {metric} components are missing.")
            for component_key, component in components.items():
                component_groups = component.get("groups")
                require(isinstance(component_groups, dict) and set(component_groups) == {"Favorable", "No favorable"}, f"QVoice {metric} component {component_key} groups are incomplete.")
                component_share_total = 0.0
                for group in component_groups.values():
                    matched = int(group["matched_employee_count"])
                    exits = int(group["voluntary_exit_count"])
                    rate = float(group["voluntary_attrition_rate_percent"])
                    share = float(group["linked_response_share_percent"])
                    require(matched >= 30 and 0 <= exits <= matched, f"QVoice {metric} component {component_key} group is not publishable.")
                    require(abs(rate - 100 * exits / matched) < 0.00011, f"QVoice {metric} component {component_key} rate does not reconcile.")
                    component_share_total += share
                require(abs(component_share_total - 100) < 0.0002, f"QVoice {metric} component {component_key} shares do not sum to 100%.")
    encoded = json.dumps(evidence, ensure_ascii=False)
    for prohibited in ('"employee_id"', '"emp_id"', '"participant_key"', '"raw_comment"', '"comment_text"'):
        require(prohibited not in encoded, f"QVoice response-group evidence must not persist {prohibited}.")
    return evidence


def load_qvoice_heartbeat_attrition_evidence() -> dict[str, Any]:
    """Load post-survey YTD attrition for the 18 displayed heartbeat sign bars."""
    evidence = json.loads(QVOICE_HEARTBEAT_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("artifact") == "presentation", "QVoice heartbeat evidence must be presentation classified.")
    require(evidence.get("outcome") == "pass" and evidence.get("validation", {}).get("outcome") == "pass", "QVoice heartbeat evidence did not pass validation.")
    require(evidence.get("minimum_shared_cohort") == 30, "QVoice heartbeat evidence must retain the n=30 rule.")
    contract = evidence.get("outcome_contract", {})
    require(contract.get("window") == "(2026-01-07, 2026-08-23]", "QVoice heartbeat evidence has an unexpected post-survey window.")
    require(contract.get("baseline_snapshot") == "2025-12-28", "QVoice heartbeat baseline snapshot is unexpected.")
    require(contract.get("survey_launch_date") == "2026-01-07", "QVoice heartbeat launch date is unexpected.")
    require(contract.get("august_cutoff_date") == "2026-08-23", "QVoice heartbeat cutoff date is unexpected.")
    require("not annualized" in str(contract.get("label", "")).lower(), "QVoice heartbeat evidence must disclose that YTD is not annualized.")
    slide = evidence.get("slide", {})
    require(
        slide.get("number") == 24
        and slide.get("technical_stage") == 26
        and slide.get("group") == "Heartbeat top-three relative-sign questions",
        "QVoice heartbeat evidence is not scoped to slide 24.",
    )
    panels = slide.get("panels")
    require(isinstance(panels, list) and len(panels) == 2, "QVoice heartbeat evidence must contain two rankings.")
    require([int(panel.get("ranking_sign")) for panel in panels] == [1, -1], "QVoice heartbeat rankings must be +1 then -1.")
    segments: list[dict[str, Any]] = []
    for panel in panels:
        questions = panel.get("questions")
        require(isinstance(questions, list) and len(questions) == 3, "Each heartbeat ranking must contain three questions.")
        for question in questions:
            question_segments = question.get("segments")
            require(isinstance(question_segments, list) and [int(segment.get("sign")) for segment in question_segments] == [1, 0, -1], "Each heartbeat question must contain the +1, 0, and -1 groups.")
            valid = int(question["valid_response_count"])
            require(sum(int(segment["matched_response_count"]) for segment in question_segments) == valid, "Heartbeat signs do not reconcile to the valid-response denominator.")
            require(abs(sum(float(segment["share_of_valid_responses_percent"]) for segment in question_segments) - 100.0) < 0.0002, "Heartbeat shares do not sum to 100%.")
            for segment in question_segments:
                matched = int(segment["matched_employee_count"])
                exits = int(segment["voluntary_exit_count"])
                rate = float(segment["ytd_voluntary_attrition_rate_percent"])
                require(matched >= 30 and 0 <= exits <= matched, "A QVoice heartbeat segment is not publishable.")
                require(abs(rate - 100 * exits / matched) < 0.00011, "A QVoice heartbeat YTD rate does not reconcile.")
                segments.append(segment)
    require(len(segments) == 18, "QVoice heartbeat evidence must contain eighteen displayed sign segments.")
    validation = evidence.get("validation", {})
    for key in (
        "all_question_sign_shares_reconcile_to_100_percent",
        "all_rates_reconcile_to_exits_and_matched_cohort",
    ):
        require(validation.get(key) is True, f"QVoice heartbeat validation failed: {key}.")
    encoded = json.dumps(evidence, ensure_ascii=False)
    for prohibited in ('"employee_id"', '"emp_id"', '"raw_comment"', '"comment_text"'):
        require(prohibited not in encoded, f"QVoice heartbeat evidence must not persist {prohibited}.")
    return evidence


def load_qvoice_retention_theme_august_attrition_evidence() -> dict[str, Any]:
    """Load the five Jan-2026 QVoice theme cohorts with August trailing-12m attrition."""
    evidence = json.loads(QVOICE_RETENTION_THEME_AUGUST_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("artifact") == "presentation", "QVoice retention-theme evidence must be presentation classified.")
    require(evidence.get("outcome") == "pass" and evidence.get("validation", {}).get("outcome") == "pass", "QVoice retention-theme evidence did not pass validation.")
    require(evidence.get("minimum_shared_cohort") == 30, "QVoice retention-theme evidence must retain the n=30 rule.")
    contract = evidence.get("outcome_contract", {})
    require(contract.get("window") == "(2025-08-24, 2026-08-23]", "QVoice retention-theme evidence has an unexpected August window.")
    require(contract.get("baseline_snapshot") == "2025-08-24" and contract.get("august_cutoff_date") == "2026-08-23", "QVoice retention-theme baseline or cutoff is unexpected.")
    rows = evidence.get("rows")
    require(isinstance(rows, list) and len(rows) == 5, "QVoice retention-theme evidence must contain five displayed themes.")
    expected = [
        "Tools, processes and bureaucracy",
        "Work arrangement/RTO/commute",
        "Manager, leadership and respect",
        "Workload, staffing and work-life",
        "Rewards",
    ]
    require([str(row.get("theme")) for row in rows] == expected, "QVoice retention-theme evidence is incomplete or out of order.")
    rates: list[float] = []
    for row in rows:
        distribution_count = int(row["distribution_count"])
        source_count = int(row["source_employee_count"])
        matched = int(row["matched_employee_count"])
        exits = int(row["voluntary_exit_count"])
        rate = float(row["trailing_12m_voluntary_attrition_rate_percent"])
        require(distribution_count == source_count and matched >= 30 and 0 <= exits <= matched, "A QVoice retention-theme cohort is invalid.")
        require(abs(rate - 100 * exits / matched) < 0.00011, "A QVoice retention-theme rate does not reconcile to exits and cohort.")
        rates.append(rate)
    require(len(set(rates)) > 1, "QVoice retention-theme rates must support relative color coding.")
    encoded = json.dumps(evidence, ensure_ascii=False)
    for prohibited in ('"employee_id"', '"emp_id"', '"raw_comment"', '"comment_text"'):
        require(prohibited not in encoded, f"QVoice retention-theme evidence must not persist {prohibited}.")
    return evidence


def load_annual_attrition_evidence(
    path: Path,
    expected_metrics: set[str],
    description: str,
) -> dict[str, Any]:
    """Load one aggregate-only annual evidence file used by slides 29–41.

    Every rate in these files is calculated on a historical employee-snapshot
    cohort, with strict voluntary exits in the following twelve months.  This
    guard keeps a later visual-only rebuild from silently reverting to an
    inherited six-month pill or publishing a sub-threshold aggregate.
    """
    evidence = json.loads(path.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", f"{description} annual evidence did not pass validation.")
    require(evidence.get("deliverable_mode") == "internal_analysis", f"{description} annual evidence must be internal_analysis.")
    contract = evidence.get("outcome_contract", {})
    require(contract.get("grain") == "employee_snapshot", f"{description} annual evidence has an unexpected grain.")
    require(
        contract.get("target") == "term_type='VOLUNTARY' con term_date en (snapshot_date, snapshot_date + 12 months]",
        f"{description} annual evidence must use a 12-month voluntary-exit outcome.",
    )
    require(
        int(contract.get("minimum_employee_snapshot_exposure", 0)) == 30
        and int(contract.get("minimum_voluntary_exits", 0)) == 30,
        f"{description} annual evidence must preserve the n=30 publication rule.",
    )
    rows = evidence.get("rows")
    require(isinstance(rows, list) and rows, f"{description} annual evidence has no rows.")
    metrics = {str(row.get("metric")) for row in rows}
    require(metrics == expected_metrics, f"{description} annual evidence metrics are incomplete or unexpected.")
    for row in rows:
        status = str(row.get("publication_status"))
        exposure = int(row["employee_snapshot_count"])
        exits = int(row["voluntary_exits"])
        rate = float(row["annual_attrition_rate_percent"])
        require(exposure >= 0 and 0 <= exits <= exposure, f"{description} annual evidence has an invalid cohort.")
        require(abs(rate - 100 * exits / exposure) < 0.00011 if exposure else rate == 0, f"{description} annual rate does not reconcile.")
        if status == "publishable":
            require(exposure >= 30 and exits >= 30, f"{description} publishes an under-threshold annual cohort.")
        else:
            require(status.startswith("not_estimable"), f"{description} annual evidence has an unknown publication status.")
    encoded = json.dumps(rows, ensure_ascii=False)
    for prohibited in ('"employee_id"', '"manager_id"', '"pay_value"', '"salary"'):
        require(prohibited not in encoded, f"{description} annual evidence must not contain {prohibited}.")
    return evidence


def load_nav28_39_direct_annual_attrition_evidence() -> dict[str, Any]:
    return load_annual_attrition_evidence(
        NAV28_39_DIRECT_ANNUAL_ATTRITION_EVIDENCE_FILE,
        {
            "comp_ratio_band",
            "compensation_grade",
            "detailed_level_tenure",
            "job_level",
            "latest_hire_tenure",
            "level_grade_family",
            "level_grouped",
            "management_level",
            "original_hire_tenure",
            "stored_manager_layer_proxy",
        },
        "Direct-field slides 28–39",
    )


def load_time_in_job_profile_time_in_role_evidence() -> dict[str, Any]:
    """Load the August cohort evidence for the revised tenure slide."""
    evidence = json.loads(TIME_IN_JOB_PROFILE_TIME_IN_ROLE_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "Time-in-role slide evidence did not pass safe-display validation.")
    require(evidence.get("deliverable_mode") == "presentation", "Time-in-role slide evidence must be presentation-safe.")
    require(
        evidence.get("annual_attrition_status") == "publishable_time_at_detailed_level_and_time_in_role",
        "Detailed-level evidence must publish both valid August cohort rates.",
    )
    display_rows = evidence.get("display_rows")
    require(isinstance(display_rows, dict) and set(display_rows) == {"time_at_detailed_level", "time_in_role"}, "Tenure display metrics are incomplete.")
    expected_bands = {"<1 year", "1–<2 years", "2–<3 years", "3–<5 years", "5–<10 years", "10+ years"}
    display_dates = set()
    for metric, rows in display_rows.items():
        require(isinstance(rows, list) and len(rows) == 6, f"{metric} needs six visible tenure bands.")
        require({str(row.get("category")) for row in rows} == expected_bands, f"{metric} has unexpected tenure bands.")
        require(all(int(row.get("employee_count", 0)) >= 30 for row in rows), f"{metric} includes a sub-threshold display band.")
        display_dates.update(str(row.get("snapshot_date")) for row in rows)
    require(len(display_dates) == 1, "Both tenure distributions must use the same current snapshot.")
    require(display_dates == {"2025-08-24"}, "Both tenure distributions must use the August 2025 baseline snapshot.")
    annual_rows = evidence.get("annual_rows")
    require(isinstance(annual_rows, list) and len(annual_rows) == 12, "Tenure evidence needs six annual rows per measure.")
    require({str(row.get("metric")) for row in annual_rows} == {"time_at_detailed_level", "time_in_role"}, "Annual evidence must contain both tenure measures.")
    for metric in ("time_at_detailed_level", "time_in_role"):
        metric_rows = [row for row in annual_rows if str(row.get("metric")) == metric]
        require(len(metric_rows) == 6, f"Annual evidence needs six bands for {metric}.")
        require({str(row.get("category")) for row in metric_rows} == expected_bands, f"Annual {metric} evidence has unexpected tenure bands.")
        require(all(str(row.get("publication_status")) == "publishable" for row in metric_rows), f"Every {metric} annual band must be publishable.")
        require({str(row.get("baseline_snapshot_date")) for row in metric_rows} == {"2025-08-24"}, f"Annual {metric} evidence must use the August 2025 baseline.")
        require({str(row.get("outcome_cutoff_date")) for row in metric_rows} == {"2026-08-23"}, f"Annual {metric} evidence must use the August 2026 cutoff.")
    coverage = evidence.get("coverage")
    require(isinstance(coverage, dict), "Time-in-role evidence is missing coverage validation.")
    for metric in ("time_at_detailed_level", "time_in_role"):
        require(coverage.get(metric, {}).get("annual_attrition_displayable") is True, f"{metric} must publish the valid August cohort rate.")
        require(int(coverage.get(metric, {}).get("baseline_valid_employee_count", 0)) == 41757, f"{metric} baseline coverage is inconsistent.")
    encoded = json.dumps(evidence, ensure_ascii=False)
    for prohibited in ('"employee_id"', '"name"', '"email"', '"salary"', '"pay_value"'):
        require(prohibited not in encoded, f"Time-in-role evidence must not contain {prohibited}.")
    return evidence


def load_nav28_39_promotion_annual_attrition_evidence() -> dict[str, Any]:
    return load_annual_attrition_evidence(
        NAV28_39_PROMOTION_ANNUAL_ATTRITION_EVIDENCE_FILE,
        {"current_grade_entry_path", "promotion_history_by_grade", "time_since_promotion"},
        "Promotion-history slides 28–39",
    )


def load_time_since_last_promotion_comparable_cohorts_evidence() -> dict[str, Any]:
    """Load the authorized internal, fixed-baseline evidence for slide 26."""
    evidence = json.loads(TIME_SINCE_LAST_PROMOTION_COMPARABLE_COHORTS_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "Comparable promotion-cohort evidence did not pass validation.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "Comparable promotion-cohort evidence must be approved internal analysis.")
    authorization_evidence = evidence.get("authorization", {})
    authorization = json.loads(AUTHORIZATION_FILE.read_text(encoding="utf-8"))
    require(authorization.get("status") == "approved", "Comparable promotion evidence lacks an approved V7 authorization.")
    require(authorization.get("reporting_mode") == "internal_analysis", "Comparable promotion authorization has the wrong reporting mode.")
    require(authorization.get("small_cell_exception", {}).get("allow_subthreshold_aggregate_buckets") is True, "Comparable promotion authorization does not allow small aggregate cells.")
    require(
        str(authorization_evidence.get("path", "")).replace("\\", "/") == str(AUTHORIZATION_FILE.relative_to(ROOT)).replace("\\", "/"),
        "Comparable promotion evidence references an unexpected authorization.",
    )
    require(authorization_evidence.get("sha256") == digest(AUTHORIZATION_FILE), "Comparable promotion authorization hash is invalid.")
    require(authorization_evidence.get("authorization_id") == authorization.get("authorization_id"), "Comparable promotion authorization identifier is invalid.")
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
    small_rows = validation.get("internal_exploratory_small_cohort_rows")
    require(isinstance(small_rows, list), "Comparable promotion evidence lacks its small-cohort display declaration.")
    expected_bands = {"0–<1 year", "1–<2 years", "2–<3 years", "3–<5 years", "5+ years"}
    for key in ("recorded_promotion_distribution", "no_recorded_promotion_role_tenure_proxy_distribution"):
        rows = evidence.get(key)
        require(isinstance(rows, list) and len(rows) == 5, f"Comparable promotion evidence is missing five {key} bands.")
        require({str(row.get("label")) for row in rows} == expected_bands, f"Comparable promotion evidence has unexpected {key} bands.")
        for row in rows:
            status = str(row.get("publication_status"))
            require(status in {"publishable", "internal_exploratory_small_cohort"}, "Promotion-band publication state is invalid.")
            if status == "publishable":
                require(int(row.get("employee_count", 0)) >= 30, "A published promotion band has n<30.")
                require(row.get("annual_attrition_rate_percent") is not None, "A published promotion band lacks its annual rate.")
            else:
                require(int(row.get("employee_count", 30)) < 30, "An internal exploratory promotion band must be below n=30.")
                require(row.get("annual_attrition_rate_percent") is not None, "An internal exploratory promotion band lacks its descriptive annual rate.")
                require(row.get("display_note"), "An internal exploratory promotion band lacks its display limitation.")
    require(
        any(row.get("publication_status") == "internal_exploratory_small_cohort" for rows in (evidence["recorded_promotion_distribution"], evidence["no_recorded_promotion_role_tenure_proxy_distribution"]) for row in rows),
        "Comparable promotion evidence must explicitly retain its authorized small cohort.",
    )
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


def load_within_team_annual_attrition_evidence() -> dict[str, Any]:
    return load_annual_attrition_evidence(
        WITHIN_TEAM_ANNUAL_ATTRITION_EVIDENCE_FILE,
        {"within_team_no_comparable", "within_team_review_count", "within_team_review_share"},
        "Within-team compensation slide",
    )


def load_colocation_annual_attrition_evidence() -> dict[str, Any]:
    """Load the fiscal-year-end trailing-window evidence for co-location."""
    evidence = json.loads(COLOCATION_ANNUAL_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "Co-location trailing evidence did not pass validation.")
    require(evidence.get("deliverable_mode") == "presentation", "Co-location trailing evidence must be presentation-safe.")
    contract = evidence.get("outcome_contract", {})
    require(contract.get("grain") == "baseline employee snapshot", "Co-location trailing evidence has an unexpected grain.")
    require(
        contract.get("target") == "term_type='VOLUNTARY' with term_date in (baseline_snapshot_date, outcome_cutoff_date]",
        "Co-location trailing evidence has an unexpected outcome contract.",
    )
    expected_years = {str(year) for year in range(2021, 2027)}
    rates = evidence.get("rates", {})
    require(set(rates) == {"same_office_site", "same_office_site_and_city"}, "Co-location trailing metrics are incomplete.")
    for metric, rows in rates.items():
        require(isinstance(rows, list) and {str(row.get("fiscal_year")) for row in rows} == expected_years, f"Co-location trailing {metric} years are incomplete.")
        require(len(rows) == len(expected_years), f"Co-location trailing {metric} has duplicate fiscal years.")
        for row in rows:
            exposure = int(row["employee_count"])
            exits = int(row["voluntary_exits"])
            rate = float(row["annual_attrition_rate_percent"])
            days = int(row["window_days"])
            require(exposure >= 30 and 0 <= exits <= exposure, f"Co-location trailing {metric} has an invalid cohort.")
            require(364 <= days <= 371, f"Co-location trailing {metric} has an invalid fiscal window.")
            require(abs(rate - 100 * exits / exposure) < 0.00011, f"Co-location trailing {metric} rate does not reconcile.")
            require(str(row["publication_status"]) == "publishable", f"Co-location trailing {metric} must be publishable.")
    diagnostics = evidence.get("diagnostics", [])
    require(isinstance(diagnostics, list) and {str(row.get("fiscal_year")) for row in diagnostics} == expected_years, "Co-location trailing diagnostics are incomplete.")
    for row in diagnostics:
        require(int(row["duplicate_employee_snapshot_count"]) == 0, "Co-location trailing evidence has duplicate employee snapshots.")
        require(int(row["conflicting_employee_snapshot_count"]) == 0, "Co-location trailing evidence has conflicting baseline mappings.")
        require(str(row["outcome"]).startswith("complete_trailing_window"), "Co-location trailing outcome window is incomplete.")
    acceptance = evidence.get("acceptance_rule", {})
    require(acceptance.get("outcome") == "pass" and acceptance.get("all_windows_complete") is True, "Co-location trailing acceptance rule did not pass.")
    encoded = json.dumps(evidence, ensure_ascii=False)
    for prohibited in ('"employee_id"', '"manager_id"', '"name"', '"email"', '"salary"'):
        require(prohibited not in encoded, f"Co-location trailing evidence must not contain {prohibited}.")
    return evidence


def load_manager_timezone_annual_attrition_evidence() -> dict[str, Any]:
    """Load the aggregate-only evidence behind the replacement stage 42 visual."""
    evidence = json.loads(MANAGER_TIMEZONE_ANNUAL_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "Manager time-zone evidence did not pass validation.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "Manager time-zone evidence must be internal_analysis.")
    contract = evidence.get("outcome_contract", {})
    require(contract.get("grain") == "employee_snapshot", "Manager time-zone evidence has an unexpected grain.")
    require(
        contract.get("target") == "term_type='VOLUNTARY' con term_date en (snapshot_date, snapshot_date + 12 months]",
        "Manager time-zone evidence must use the strict twelve-month voluntary outcome.",
    )
    require(
        contract.get("time_zone_rule") == "same stored office_site first; otherwise IANA UTC-offset difference at 12:00 UTC on snapshot date is <=4 hours or >4 hours",
        "Manager time-zone evidence has an unexpected category rule.",
    )
    categories = (
        "same_office_site",
        "different_site_up_to_4_hours",
        "different_site_more_than_4_hours",
    )
    latest = evidence.get("latest_distribution", {})
    require(set(latest) == set(categories) | {"unmapped_time_zone_proxy"}, "Latest manager time-zone distribution is incomplete.")
    diagnostics = evidence.get("diagnostics", {})
    categorized = int(diagnostics["latest_categorized_employee_manager_pair_count"])
    unmapped = int(diagnostics["latest_unmapped_employee_manager_pair_count"])
    eligible = int(diagnostics["latest_eligible_employee_manager_pair_count"])
    require(categorized + unmapped == eligible and categorized > 0, "Latest manager time-zone coverage does not reconcile.")
    require(
        sum(int(latest[category]["employee_snapshot_count"]) for category in categories) == categorized,
        "Latest manager time-zone display categories do not reconcile.",
    )
    rows = evidence.get("rows")
    require(isinstance(rows, list) and rows, "Manager time-zone evidence has no annual rows.")
    by_year = {str(year): set() for year in range(2020, 2026)}
    for row in rows:
        require(str(row.get("metric")) == "time_zone_proximity", "Unexpected manager time-zone metric.")
        year = str(row["fiscal_year"])
        by_year.setdefault(year, set()).add(str(row["category"]))
        exposure = int(row["employee_snapshot_count"])
        exits = int(row["voluntary_exits"])
        rate = float(row["annual_attrition_rate_percent"])
        require(exposure > 0 and 0 <= exits <= exposure, "Manager time-zone annual cohort is invalid.")
        require(abs(rate - 100 * exits / exposure) < 0.00011, "Manager time-zone annual rate does not reconcile.")
    for year in map(str, range(2020, 2025)):
        require(by_year.get(year) == set(categories), f"FY{year} manager time-zone categories are incomplete.")
    encoded = json.dumps(evidence, ensure_ascii=False)
    for prohibited in ('"employee_id"', '"manager_id"', '"home_address"', '"postal_code"'):
        require(prohibited not in encoded, f"Manager time-zone evidence must not persist {prohibited}.")
    return evidence


def load_manager_timezone_2026_ytd_attrition_evidence() -> dict[str, Any]:
    """Load the three compact 2026 YTD labels for stage 42.

    The display is intentionally YTD rather than annual: the 2026 outcome
    window is incomplete and must never be described or styled as a full-year
    attrition result.
    """
    evidence = json.loads(MANAGER_TIMEZONE_2026_YTD_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "Manager time-zone 2026 YTD evidence did not pass validation.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "Manager time-zone 2026 YTD evidence must be internal_analysis.")
    contract = evidence.get("outcome_contract", {})
    require(contract.get("grain") == "employee_baseline_snapshot", "Manager time-zone 2026 YTD evidence has an unexpected grain.")
    require(
        contract.get("label") == "2026 YTD voluntary attrition; not annualized",
        "Manager time-zone labels must explicitly remain 2026 YTD and not annualized.",
    )
    require(
        contract.get("time_zone_rule") == "same stored office_site first; otherwise IANA UTC-offset difference at 12:00 UTC on baseline date is <=4 hours or >4 hours",
        "Manager time-zone 2026 YTD evidence has an unexpected category rule.",
    )
    categories = {
        "same_office_site",
        "different_site_up_to_4_hours",
        "different_site_more_than_4_hours",
    }
    rows = evidence.get("rows")
    require(isinstance(rows, list) and len(rows) == len(categories), "Manager time-zone 2026 YTD evidence must have exactly three category rows.")
    require({str(row.get("category")) for row in rows} == categories, "Manager time-zone 2026 YTD categories are incomplete.")
    diagnostics = evidence.get("diagnostics", {})
    categorized = int(diagnostics["categorized_employee_manager_pair_count"])
    unmapped = int(diagnostics["unmapped_employee_manager_pair_count"])
    eligible = int(diagnostics["eligible_employee_manager_pair_count"])
    require(categorized + unmapped == eligible and categorized > 0, "Manager time-zone 2026 YTD coverage does not reconcile.")
    require(sum(int(row["employee_count"]) for row in rows) == categorized, "Manager time-zone 2026 YTD categories do not reconcile to coverage.")
    for row in rows:
        employees = int(row["employee_count"])
        exits = int(row["voluntary_exits"])
        rate = float(row["ytd_voluntary_attrition_rate_percent"])
        require(employees > 0 and 0 <= exits <= employees, "Manager time-zone 2026 YTD cohort is invalid.")
        require(abs(rate - 100 * exits / employees) < 0.00011, "Manager time-zone 2026 YTD rate does not reconcile.")
    encoded = json.dumps(evidence, ensure_ascii=False)
    for prohibited in ('"employee_id"', '"manager_id"', '"home_address"', '"postal_code"'):
        require(prohibited not in encoded, f"Manager time-zone 2026 YTD evidence must not persist {prohibited}.")
    return evidence


def load_manager_timezone_august_trailing_12m_evidence() -> dict[str, Any]:
    """Load August-to-August manager-site proximity distribution and rates."""
    evidence = json.loads(MANAGER_TIMEZONE_AUGUST_TRAILING_12M_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("deliverable_mode") == "internal_analysis", "Manager proximity August evidence must be internal_analysis.")
    require(evidence.get("outcome") == "pass", "Manager proximity August evidence did not pass.")
    contract = evidence.get("outcome_contract", {})
    require(
        contract.get("baseline_snapshot") == "2025-08-24" and contract.get("outcome_cutoff_date") == "2026-08-23",
        "Manager proximity must use the August 2025-to-2026 window.",
    )
    categories = {
        "same_office_site",
        "different_site_up_to_4_hours",
        "different_site_more_than_4_hours",
    }
    annual = evidence.get("annual_attrition", {})
    current = evidence.get("latest_distribution", {})
    require(set(annual) == categories and set(current) == categories | {"unmapped_time_zone_proxy"}, "Manager proximity categories are incomplete.")
    diagnostics = evidence.get("diagnostics", {})
    require(
        int(diagnostics["baseline_duplicate_employee_source_count"]) == 0
        and int(diagnostics["current_duplicate_employee_source_count"]) == 0,
        "Manager proximity source snapshots have duplicate rows.",
    )
    for category in categories:
        row = annual[category]
        cohort = int(row["employee_count"])
        exits = int(row["voluntary_exit_count"])
        rate = float(row["attrition_rate_percent"])
        require(cohort >= 30 and 0 <= exits <= cohort, "A manager proximity baseline category is invalid.")
        require(abs(rate - 100 * exits / cohort) < 0.00011, "A manager proximity T12 rate does not reconcile.")
    return evidence


def load_nav38_plus_august_attrition_evidence() -> dict[str, Any]:
    """Load the fixed-August aggregate evidence for visible slides 38 onward."""
    evidence = json.loads(NAV38_PLUS_AUGUST_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "Slides 38+ annual evidence did not pass validation.")
    require(evidence.get("deliverable_mode") == "presentation", "Slides 38+ evidence must be presentation-safe.")
    require(evidence.get("baseline_snapshot_date") == "2025-08-24", "Slides 38+ evidence has an unexpected baseline.")
    require(evidence.get("outcome_cutoff_date") == "2026-08-23", "Slides 38+ evidence has an unexpected outcome cutoff.")
    require(evidence.get("outcome_window") == "(2025-08-24, 2026-08-23]", "Slides 38+ evidence has an unexpected outcome window.")
    queries = evidence.get("queries", {})
    require(set(queries) == {"simple_categories", "manager_observed_expected", "above_average_team_turnover"}, "Slides 38+ evidence is incomplete.")
    for name, payload in queries.items():
        query_path = ROOT / str(payload["query_path"])
        require(query_path.exists(), f"Slides 38+ query is missing: {name}.")
        require(digest(query_path) == payload["query_sha256"], f"Slides 38+ SQL provenance is invalid: {name}.")
        require("employee_id" not in json.dumps(payload["rows"], ensure_ascii=False).lower(), f"Slides 38+ evidence exposes employee IDs: {name}.")
        require("manager_id" not in json.dumps(payload["rows"], ensure_ascii=False).lower(), f"Slides 38+ evidence exposes manager IDs: {name}.")
        for row in payload["rows"]:
            if row.get("row_type") != "category":
                continue
            count = int(row["employee_count"])
            exits = int(row["voluntary_exits"])
            rate = float(row["annual_attrition_rate_percent"])
            require(count >= 0 and 0 <= exits <= count, f"Slides 38+ category has an invalid aggregate: {name}.")
            require(abs(rate - 100 * exits / count) < 0.001 if count else rate == 0, f"Slides 38+ rate does not reconcile: {name}.")
            status = str(row.get("publication_status", "publishable" if count >= 30 else "not_estimable_below_30_baseline_employees"))
            row["publication_status"] = status
            if status == "publishable":
                require(count >= 30, f"Slides 38+ published a sub-threshold category: {name}.")
    require(isinstance(evidence.get("metric_map"), dict), "Slides 38+ metric map is missing.")
    return evidence


def load_layers_from_ceo_annual_attrition_evidence() -> dict[str, Any]:
    """Load the fixed-baseline reconstructed layer cohorts for slide 32."""
    evidence = json.loads(LAYERS_FROM_CEO_ANNUAL_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "Manager-layer annual evidence did not pass validation.")
    require(evidence.get("deliverable_mode") == "presentation", "Manager-layer evidence must be presentation-safe.")
    require(evidence.get("baseline_snapshot_date") == "2025-08-24", "Manager-layer evidence has an unexpected baseline.")
    require(evidence.get("outcome_cutoff_date") == "2026-08-23", "Manager-layer evidence has an unexpected cutoff.")
    require(evidence.get("outcome_window") == "(2025-08-24, 2026-08-23]", "Manager-layer evidence has an unexpected window.")
    query_path = ROOT / str(evidence.get("provenance", {}).get("audit_sql", ""))
    require(query_path.exists(), "Manager-layer annual SQL provenance is missing.")
    require(digest(query_path) == evidence["provenance"]["audit_sql_sha256"], "Manager-layer annual SQL provenance is invalid.")
    distribution = evidence.get("distribution")
    require(isinstance(distribution, list) and distribution, "Manager-layer annual evidence has no distribution.")
    labels = set()
    for row in distribution:
        label = str(row["label"])
        count = int(row["employee_count"])
        exits = int(row["voluntary_exits"])
        rate = float(row["annual_attrition_rate_percent"])
        require(label not in labels, "Manager-layer annual evidence contains duplicate labels.")
        labels.add(label)
        require(count >= 30 and 0 <= exits <= count, "Manager-layer annual evidence has an invalid cohort.")
        require(abs(rate - 100 * exits / count) < 0.00011, "Manager-layer annual rate does not reconcile.")
        require(str(row["publication_status"]) == "publishable", "Manager-layer annual evidence has an unpublished visible band.")
    metrics = evidence.get("metrics", {})
    require(sum(int(row["employee_count"]) for row in distribution) == int(metrics["display_eligible_count"]), "Manager-layer distribution does not reconcile.")
    require(int(metrics["display_approved_root_match_count"]) == int(metrics["display_eligible_count"]), "Manager-layer baseline root coverage failed.")
    require(int(metrics["root_reference_pass"]) == 1 and float(metrics["convergence_rate_percent"]) == 100.0, "Manager-layer root validation failed.")
    encoded = json.dumps(evidence, ensure_ascii=False).lower()
    for prohibited in ('"employee_id"', '"manager_employee_id"', '"root_employee_id"', '"email"'):
        require(prohibited not in encoded, f"Manager-layer evidence exposes restricted field: {prohibited}.")
    return evidence


def load_layers_from_ceo_0_2_compensation_grade_evidence() -> dict[str, Any]:
    """Load the authorized internal exact-grade follow-up for the 0–2 layer cohort."""
    evidence = json.loads(LAYERS_FROM_CEO_0_2_COMPENSATION_GRADE_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "0–2 layer compensation-grade evidence did not pass validation.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "0–2 layer compensation-grade evidence must be an authorized internal analysis.")
    require(evidence.get("artifact_classification") == "internal_analysis", "0–2 layer compensation-grade evidence has an invalid classification.")
    require(evidence.get("baseline_snapshot_date") == "2025-08-24", "0–2 layer compensation-grade evidence has an unexpected baseline.")
    require(evidence.get("outcome_cutoff_date") == "2026-08-23", "0–2 layer compensation-grade evidence has an unexpected cutoff.")
    require(evidence.get("outcome_window") == "(2025-08-24, 2026-08-23]", "0–2 layer compensation-grade evidence has an unexpected window.")
    authorization_evidence = evidence.get("authorization", {})
    authorization_path = str(authorization_evidence.get("path", "")).replace("\\", "/")
    expected_authorization_path = str(AUTHORIZATION_FILE.relative_to(ROOT)).replace("\\", "/")
    require(authorization_path == expected_authorization_path, "0–2 layer compensation-grade evidence references an unexpected authorization.")
    require(digest(AUTHORIZATION_FILE) == authorization_evidence.get("sha256"), "0–2 layer compensation-grade authorization hash is invalid.")
    authorization = json.loads(AUTHORIZATION_FILE.read_text(encoding="utf-8"))
    require(authorization.get("status") == "approved", "0–2 layer compensation-grade authorization is not approved.")
    require(authorization.get("reporting_mode") == "internal_analysis", "0–2 layer compensation-grade authorization has the wrong reporting mode.")
    require(authorization_evidence.get("authorization_id") == authorization.get("authorization_id"), "0–2 layer compensation-grade authorization identifier is invalid.")
    require(authorization_evidence.get("authorized_audience") == authorization.get("authorized_audience"), "0–2 layer compensation-grade audience is invalid.")
    require(bool(authorization_evidence.get("small_cell_exception_applied")), "0–2 layer compensation-grade evidence must record the small-cell exception.")
    require(bool(authorization.get("small_cell_exception", {}).get("allow_subthreshold_aggregate_buckets")), "0–2 layer compensation-grade authorization does not permit small aggregate buckets.")
    query_path = ROOT / str(evidence.get("provenance", {}).get("audit_sql", ""))
    require(query_path.exists(), "0–2 layer compensation-grade SQL provenance is missing.")
    require(
        digest(query_path) == evidence["provenance"]["audit_sql_sha256"],
        "0–2 layer compensation-grade SQL provenance is invalid.",
    )
    cohort = evidence.get("cohort", {})
    require(int(cohort.get("employee_count", 0)) == 185, "0–2 layer compensation-grade evidence has an unexpected cohort size.")
    require(int(cohort.get("voluntary_exits", -1)) == 19, "0–2 layer compensation-grade evidence has an unexpected exit count.")
    cohort_rate = float(cohort.get("annual_attrition_rate_percent", -1))
    require(abs(cohort_rate - 100 * 19 / 185) < 0.00011, "0–2 layer compensation-grade cohort rate does not reconcile.")
    rows = evidence.get("rows")
    expected_labels = {
        "M30", "M40", "M50", "M60", "R80", "S50", "S60", "S80", "T80",
        "V10", "V30", "V40", "V70", "V80", "X30", "X40", "X45", "X85",
    }
    require(isinstance(rows, list) and len(rows) == len(expected_labels), "0–2 layer compensation-grade evidence must contain every exact stored grade.")
    labels: set[str] = set()
    total_count = 0
    total_exits = 0
    total_share = 0.0
    for row in rows:
        label = str(row.get("label", ""))
        count = int(row.get("employee_count", 0))
        exits = int(row.get("voluntary_exits", -1))
        share = float(row.get("cohort_share_percent", -1))
        rate = float(row.get("annual_attrition_rate_percent", -1))
        require(label not in labels, "0–2 layer compensation-grade evidence contains duplicate labels.")
        labels.add(label)
        require(count > 0 and 0 <= exits <= count, "0–2 layer compensation-grade evidence has an invalid visible aggregate.")
        require(abs(rate - 100 * exits / count) < 0.00011, "0–2 layer compensation-grade rate does not reconcile.")
        require(abs(share - 100 * count / 185) < 0.00011, "0–2 layer compensation-grade share does not reconcile.")
        require(str(row.get("publication_status")) == "internal_analysis_authorized", "0–2 layer compensation-grade evidence has an unauthorized visible group.")
        total_count += count
        total_exits += exits
        total_share += share
    require(labels == expected_labels, "0–2 layer compensation-grade evidence has an unexpected exact-grade set.")
    require(total_count == 185 and total_exits == 19, "0–2 layer compensation-grade rows do not reconcile to the cohort.")
    require(abs(total_share - 100.0) < 0.00011, "0–2 layer compensation-grade shares do not sum to 100%.")
    validation = evidence.get("validation", {})
    require(validation.get("outcome") == "pass", "0–2 layer compensation-grade validation is not passing.")
    validation_metrics = validation.get("metrics", {})
    require(int(validation_metrics.get("displayed_grade_count", 0)) == len(rows), "0–2 layer compensation-grade count of exact grades is invalid.")
    require(int(validation_metrics.get("subthreshold_grade_count", 0)) == sum(int(row["employee_count"]) < 30 for row in rows), "0–2 layer compensation-grade small-cell count is invalid.")
    privacy_checks = evidence.get("privacy_checks", {})
    require(bool(privacy_checks.get("all_rows_aggregate_only")), "0–2 layer compensation-grade evidence must remain aggregate-only.")
    require(not privacy_checks.get("employee_identifiers_persisted"), "0–2 layer compensation-grade evidence persists employee identifiers.")
    require(not privacy_checks.get("manager_identifiers_persisted"), "0–2 layer compensation-grade evidence persists manager identifiers.")
    require(not privacy_checks.get("exact_compensation_values_persisted"), "0–2 layer compensation-grade evidence persists exact compensation values.")
    encoded = json.dumps(evidence, ensure_ascii=False).lower()
    for prohibited in ('"employee_id"', '"manager_employee_id"', '"root_employee_id"', '"annual_base_pay"', '"base_pay_rate"', '"email"'):
        require(prohibited not in encoded, f"0–2 layer compensation-grade evidence exposes restricted field: {prohibited}.")
    return evidence


def load_direct_team_span_annual_attrition_evidence() -> dict[str, Any]:
    """Load the authorized aggregate direct-team-span follow-up evidence."""
    evidence = json.loads(DIRECT_TEAM_SPAN_ANNUAL_ATTRITION_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "Direct-team-span evidence did not pass validation.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "Direct-team-span evidence must be internal analysis.")
    require(evidence.get("artifact_classification") == "internal_analysis", "Direct-team-span evidence has an invalid classification.")
    require(evidence.get("semantic_type") == "hierarchy", "Direct-team-span evidence must be a reconstructed hierarchy.")
    require(evidence.get("baseline_snapshot_date") == "2025-08-24", "Direct-team-span evidence has an unexpected baseline.")
    require(evidence.get("outcome_cutoff_date") == "2026-08-23", "Direct-team-span evidence has an unexpected cutoff.")
    require(evidence.get("outcome_window") == "(2025-08-24, 2026-08-23]", "Direct-team-span evidence has an unexpected window.")
    authorization_evidence = evidence.get("authorization", {})
    require(
        str(authorization_evidence.get("path", "")).replace("\\", "/")
        == str(AUTHORIZATION_FILE.relative_to(ROOT)).replace("\\", "/"),
        "Direct-team-span evidence references an unexpected authorization.",
    )
    require(digest(AUTHORIZATION_FILE) == authorization_evidence.get("sha256"), "Direct-team-span authorization hash is invalid.")
    authorization = json.loads(AUTHORIZATION_FILE.read_text(encoding="utf-8"))
    require(authorization.get("status") == "approved", "Direct-team-span authorization is not approved.")
    require(authorization.get("reporting_mode") == "internal_analysis", "Direct-team-span authorization has the wrong reporting mode.")
    require(authorization_evidence.get("authorization_id") == authorization.get("authorization_id"), "Direct-team-span authorization identifier is invalid.")
    require(authorization_evidence.get("authorized_audience") == authorization.get("authorized_audience"), "Direct-team-span audience is invalid.")
    require(bool(authorization_evidence.get("small_cell_exception_applied")), "Direct-team-span evidence must record the small-cell exception.")
    query_path = ROOT / str(evidence.get("provenance", {}).get("audit_sql", ""))
    require(query_path.exists(), "Direct-team-span SQL provenance is missing.")
    require(digest(query_path) == evidence["provenance"]["audit_sql_sha256"], "Direct-team-span SQL provenance is invalid.")
    coverage = evidence.get("coverage", {})
    require(int(coverage.get("baseline_employee_count", 0)) == 45_003, "Direct-team-span baseline count is invalid.")
    require(int(coverage.get("eligible_employee_count", 0)) == 44_737, "Direct-team-span eligible count is invalid.")
    require(int(coverage.get("unresolvable_manager_exclusion_count", -1)) == 266, "Direct-team-span coverage exclusion is invalid.")
    require(
        abs(float(coverage.get("eligible_percent", 0)) - 100 * 44_737 / 45_003) < 0.00011,
        "Direct-team-span coverage percent does not reconcile.",
    )
    bands = evidence.get("bands")
    expected_labels = ["1–4", "5–9", "10–14", "15–19", "20–29", "30+"]
    require(isinstance(bands, list) and [str(row.get("label")) for row in bands] == expected_labels, "Direct-team-span bands are incomplete or out of order.")
    total_employees = 0
    total_teams = 0
    total_exits = 0
    for row in bands:
        count = int(row.get("employee_count", 0))
        teams = int(row.get("team_count", 0))
        exits = int(row.get("voluntary_exits", -1))
        rate = float(row.get("annual_attrition_rate_percent", -1))
        require(count >= 30 and teams > 0 and 0 <= exits <= count, "Direct-team-span band has an invalid aggregate.")
        require(abs(rate - 100 * exits / count) < 0.00011, "Direct-team-span annual rate does not reconcile.")
        require(str(row.get("publication_status")) == "internal_analysis_authorized", "Direct-team-span band lacks authorization.")
        total_employees += count
        total_teams += teams
        total_exits += exits
    validation_metrics = evidence.get("validation", {}).get("metrics", {})
    require(total_employees == 44_737, "Direct-team-span bands do not reconcile to eligible employees.")
    require(total_teams == int(validation_metrics.get("eligible_team_count", 0)) == 9_665, "Direct-team-span bands do not reconcile to teams.")
    require(total_exits == int(validation_metrics.get("baseline_voluntary_exits", 0)) == 2_480, "Direct-team-span bands do not reconcile to voluntary exits.")
    exact = evidence.get("exact_span_comparison", {})
    five = exact.get("five_direct_reports", {})
    twenty = exact.get("twenty_direct_reports", {})
    require((int(five.get("direct_report_count", 0)), int(five.get("employee_count", 0)), int(five.get("team_count", 0))) == (5, 7_160, 1_432), "Exact span 5 comparison is invalid.")
    require((int(twenty.get("direct_report_count", 0)), int(twenty.get("employee_count", 0)), int(twenty.get("team_count", 0))) == (20, 80, 4), "Exact span 20 comparison is invalid.")
    require(abs(float(five.get("annual_attrition_rate_percent", 0)) - 100 * int(five.get("voluntary_exits", 0)) / int(five.get("employee_count", 1))) < 0.00011, "Exact span 5 annual rate does not reconcile.")
    require(abs(float(twenty.get("annual_attrition_rate_percent", 0)) - 100 * int(twenty.get("voluntary_exits", 0)) / int(twenty.get("employee_count", 1))) < 0.00011, "Exact span 20 annual rate does not reconcile.")
    require(bool(twenty.get("exploratory")), "Exact span 20 must remain exploratory because it has four teams.")
    privacy = evidence.get("privacy_checks", {})
    require(bool(privacy.get("all_rows_aggregate_only")), "Direct-team-span evidence must remain aggregate-only.")
    require(not privacy.get("identity_fields_persisted"), "Direct-team-span evidence persists identity fields.")
    require(not privacy.get("employee_rows_persisted") and not privacy.get("manager_rows_persisted"), "Direct-team-span evidence persists row-level data.")
    encoded = json.dumps(evidence, ensure_ascii=False).lower()
    for prohibited in ('"employee_id"', '"manager_employee_id"', '"manager_name"', '"employee_name"', '"email"'):
        require(prohibited not in encoded, f"Direct-team-span evidence exposes restricted field: {prohibited}.")
    return evidence


def index_rows(evidence: dict[str, Any]) -> dict[tuple[int, str], dict[str, Any]]:
    return {(row["calendar_year"], row["group_key"]): row for row in evidence["rows"]}


def rate_class(group_key: str, year: int, rows_by_key: dict[tuple[int, str], dict[str, Any]]) -> str:
    """Return a relative attrition pill class, preserving Total as neutral."""
    if group_key == "total":
        return "ios-rate-total"
    available = [
        rows_by_key[(year, key)]["post_event_voluntary_attrition_percent"]
        for key in GROUP_KEYS
        if key != "total" and rows_by_key[(year, key)]["post_event_voluntary_attrition_percent"] is not None
    ]
    value = rows_by_key[(year, group_key)]["post_event_voluntary_attrition_percent"]
    if value is None:
        return "ios-rate-suppressed"
    if value == min(available):
        return "ios-rate-low"
    if value == max(available):
        return "ios-rate-high"
    return "ios-rate-mid"


def table_cell(group_key: str, year: int, rows_by_key: dict[tuple[int, str], dict[str, Any]]) -> str:
    row = rows_by_key[(year, group_key)]
    cohort_n = f'{int(row["cohort_n"]):,}'
    attrition = row["post_event_voluntary_attrition_percent"]
    rate = "Not estimable" if attrition is None else f"{float(attrition):.1f}% attrition"
    return (
        '<td><div class="ios-ytd-n">n=' + cohort_n + '</div>'
        + '<span class="ios-rate-pill ' + rate_class(group_key, year, rows_by_key) + '">'
        + rate
        + "</span></td>"
    )


def build_table(evidence: dict[str, Any]) -> str:
    rows_by_key = index_rows(evidence)
    current_total = rows_by_key[(2026, "total")]
    current_share = float(current_total["workforce_share_percent"])
    labels = {key: rows_by_key[(2024, key)]["short_label"] for key in GROUP_KEYS}
    cutoff_labels = {}
    for year in YEARS:
        cutoff = date.fromisoformat(evidence["cutoffs"][str(year)]["cutoff_date"])
        cutoff_labels[year] = f"{cutoff.day} {cutoff.strftime('%b')}"
    body = []
    for key in GROUP_KEYS:
        extra = ' class="ios-ytd-total-row"' if key == "total" else ""
        cells = "".join(table_cell(key, year, rows_by_key) for year in YEARS)
        body.append(
            f'<tr{extra}><th scope="row">{html.escape(labels[key])}</th>{cells}</tr>'
        )
    headers = "".join(
        f'<th>{year}<span>through {html.escape(cutoff_labels[year])}</span></th>' for year in YEARS
    )
    return (
        '<section class="ios-ytd-table-wrap" aria-label="Cohort size and observed voluntary attrition by IOS movement reason">'
        '<div class="ios-ytd-table-heading"><strong>Cohort n and observed voluntary attrition</strong>'
        '<span>after first IOS event, through each August cutoff</span></div>'
        '<table class="ios-ytd-table"><thead><tr><th>IOS movement reason</th>'
        + headers
        + '</tr></thead><tbody>'
        + "".join(body)
        + "</tbody></table></section>"
    )


def build_slide(evidence: dict[str, Any]) -> str:
    rows_by_key = index_rows(evidence)
    maximum_share = max(
        float(row["workforce_share_percent"])
        for row in evidence["rows"]
        if row["workforce_share_percent"] is not None and row["group_key"] != "total"
    )
    current_total = rows_by_key[(2026, "total")]
    current_share = float(current_total["workforce_share_percent"])
    panels = build_year_panel(
        2026,
        rows_by_key,
        evidence["cutoffs"]["2026"]["cutoff_date"],
        maximum_share,
    )
    rendered = """  <div class=\"slide-stage\" id=\"slide-5\" data-v6-playbook=\"true\" data-v7-ios-movement=\"true\">
    <div class=\"slide-heading\"><div><h2 class=\"slide-title-text\">IOS movements represent 14.7% of the active regular workforce in 2026 YTD</h2><p class=\"slide-subtitle\">Through 23 Aug 2026 · Workforce share, cohort n, and observed voluntary attrition by IOS movement reason</p></div><span class=\"badge badge-info\">2026 YTD</span></div>
    <article class=\"card card-full v6-playbook-card ios-ytd-card\">
      <div class=\"v6-definition-strip ios-ytd-definition\"><div><span class=\"v6-mini-label\">Definition</span><strong>First eligible IOS event per employee, reason, and calendar year.</strong></div><div><span class=\"v6-mini-label\">Population</span><strong>Active regular employees; latest active monthly snapshot within 45 days before the event.</strong></div></div>
      <div class=\"v6-chart-area ios-ytd-horizontal-area\"><div class=\"ios-ytd-horizontal-grid\">""" + panels + """</div>
        <p class=\"ios-ytd-method\"><strong>Read this as:</strong> each bar is the share of the average active regular workforce, scaled to the largest reason shown; n and observed voluntary attrition are shown at right. Reason rows may overlap and do not sum to Total.</p>
      </div>
      <div class=\"v6-source-line\"><strong>Source:</strong> HRDA workers_ios_transfers, post_hire_monthly_worker_dtls, and all_terminations. Internal aggregate analysis under the named V7 authorization; all available cells are shown.</div>
    </article>
  </div>"""
    return rendered.replace("14.7%", f"{current_share:.1f}%", 1)


def build_year_panel(
    year: int,
    rows_by_key: dict[tuple[int, str], dict[str, Any]],
    cutoff_date: str,
    maximum_share: float,
) -> str:
    cutoff = date.fromisoformat(cutoff_date)
    header = (
        '<article class="card chart-card ios-ytd-year-panel"><div class="v6-panel-heading">'
        f"<span>{year} YTD</span><span>through {cutoff.day} {cutoff.strftime('%b')}</span></div>"
        '<div class="bar-list ios-ytd-bar-list">'
    )
    rows = []
    for group_key in GROUP_KEYS:
        if group_key == "total":
            continue
        row = rows_by_key[(year, group_key)]
        label = html.escape(row["short_label"])
        share = float(row["workforce_share_percent"])
        attrition = row["post_event_voluntary_attrition_percent"]
        width = max(3.0, 100.0 * share / maximum_share)
        if attrition is None:
            pill_class = "attr-unavailable"
            attrition_text = "Not estimable"
        elif group_key == "total":
            pill_class = "attr-mid"
            attrition_text = f"{float(attrition):.1f}%"
        else:
            available = [
                rows_by_key[(year, key)]["post_event_voluntary_attrition_percent"]
                for key in GROUP_KEYS
                if key != "total"
                and rows_by_key[(year, key)]["post_event_voluntary_attrition_percent"] is not None
            ]
            pill_class = "attr-low" if attrition == min(available) else "attr-high" if attrition == max(available) else "attr-mid"
            attrition_text = f"{float(attrition):.1f}%"
        title = (
            "Observed voluntary attrition: not estimable because cohort n=0"
            if attrition is None
            else "Observed voluntary attrition: " + f"{float(attrition):.1f}%"
        )
        rows.append(
            '<div class="bar-row v4-inline-attrition-row ios-ytd-bar-row"><div class="bar-label" title="'
            + label
            + '">'
            + label
            + '</div><div class="bar-track"><div class="bar-fill" style="width:'
            + f"{width:.1f}%"
            + '"></div></div><div class="bar-value">'
            + f"{share:.1f}%<span>n={int(row['cohort_n']):,}</span>"
            + '</div><span class="v4-inline-attrition-rate v6-rate-pill '
            + pill_class
            + '" title="'
            + title
            + '" aria-label="Observed voluntary attrition: '
            + ("not estimable because cohort n=0" if attrition is None else f"{float(attrition):.1f}%")
            + '">'
            + attrition_text
            + "</span></div>"
        )
    return header + "".join(rows) + "</div></article>"


def css_block() -> str:
    return r'''

    /* V7 internal_analysis — annual IOS movement reasons and complete aggregate visibility */
    body[data-deliverable-mode="internal_analysis"] .v6-chart-area .bar-list { overflow-y:auto; padding-right:4px; }
    body[data-deliverable-mode="internal_analysis"] .v6-chart-area .bar-row { flex:0 0 auto; }
    body[data-deliverable-mode="internal_analysis"] .v6-truncation-note { display:none !important; }

    /* V7 stage 42 — assigned office-site/time-zone proximity replaces the
       former residential-distance visual. */
    #slide-42 .manager-timezone-proximity-card { min-height:0; padding:12px 14px 10px; gap:8px; }
    #slide-42 .manager-timezone-chart-area { min-height:0; }
    #slide-42 .manager-timezone-distribution-card { position:relative; min-height:0; padding:18px 22px; gap:10px; }
    #slide-42 .manager-timezone-distribution-card .bar-list { flex:1; justify-content:space-evenly; gap:16px; padding:10px 0 42px; overflow:visible; }
    #slide-42 .manager-timezone-bar-row { grid-template-columns:minmax(230px,320px) minmax(0,1fr) 118px; min-height:58px; gap:12px; padding-right:104px; }
    #slide-42 .manager-timezone-bar-row .bar-label { font-size:14px; line-height:1.15; }
    #slide-42 .manager-timezone-bar-row .bar-track { height:18px; }
    #slide-42 .manager-timezone-bar-row .bar-value { font-size:13px; white-space:nowrap; }
    #slide-42 .manager-timezone-annual-pill.v6-rate-pill { min-width:76px; padding:4px 8px; font-size:12px; text-align:right; }
    #slide-42 .manager-timezone-distribution-card .chart-footer { position:absolute; right:22px; bottom:14px; left:22px; display:block !important; margin:0; padding-top:9px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:11px; line-height:1.25; }
    #slide-42 .manager-timezone-distribution-card .chart-footer strong { color:var(--text-main); }

    /* V7 slide 32 — two fixed-baseline promotion cohorts. */
    #slide-32 .v7-promotion-comparable-card { min-height:0; padding:12px 15px 10px; gap:9px; }
    #slide-32 .v7-promotion-comparable-definition { display:flex; justify-content:space-between; gap:16px; padding:7px 10px; border-radius:9px; background:color-mix(in oklab,var(--accent) 7%,transparent); color:var(--text-muted); font-size:10px; line-height:1.25; }
    #slide-32 .v7-promotion-comparable-definition strong { color:var(--text-main); }
    #slide-32 .v7-promotion-comparable-layout { display:grid; grid-template-columns:1fr 1fr; gap:12px; min-height:0; flex:1; }
    #slide-32 .v7-promotion-comparable-panel { display:flex; flex-direction:column; min-width:0; min-height:0; padding:10px; border:1px solid var(--border-subtle); border-radius:12px; background:color-mix(in oklab,var(--bg-surface-2) 58%,transparent); }
    #slide-32 .v7-promotion-comparable-heading { display:flex; align-items:flex-start; justify-content:space-between; gap:8px; min-height:30px; padding-bottom:6px; border-bottom:1px solid var(--border-subtle); color:var(--text-main); font-size:11px; font-weight:800; line-height:1.15; }
    #slide-32 .v7-promotion-comparable-heading small { color:var(--text-muted); font-size:9px; font-weight:700; line-height:1.15; text-align:right; white-space:nowrap; }
    #slide-32 .v7-promotion-comparable-bars { display:flex; flex:1; flex-direction:column; justify-content:space-evenly; min-height:0; gap:2px; padding-top:4px; }
    #slide-32 .v7-promotion-comparable-row { display:grid; grid-template-columns:116px minmax(0,1fr) 86px 60px; align-items:center; column-gap:7px; min-height:29px; padding:2px 0; border-bottom:1px solid color-mix(in oklab,var(--border-subtle) 75%,transparent); }
    #slide-32 .v7-promotion-comparable-row:last-child { border-bottom:0; }
    #slide-32 .v7-promotion-comparable-row.is-suppressed { grid-template-columns:116px minmax(0,1fr); }
    #slide-32 .v7-promotion-comparable-label { color:var(--text-main); font-size:10px; font-weight:800; line-height:1.12; }
    #slide-32 .v7-promotion-comparable-track { height:9px; overflow:hidden; border:1px solid color-mix(in oklab,var(--text-muted) 20%,transparent); border-radius:var(--radius-pill); background:color-mix(in oklab,var(--text-muted) 10%,transparent); }
    #slide-32 .v7-promotion-comparable-fill { height:100%; min-width:2px; border-radius:inherit; background:var(--accent); }
    #slide-32 .v7-promotion-comparable-value { color:var(--text-muted); font-size:9px; font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }
    #slide-32 .v7-promotion-annual.v7-annual-attrition { position:static; transform:none; justify-self:end; min-width:56px; padding:3px 5px; font-size:9px; line-height:1; text-align:center; white-space:nowrap; }
    #slide-32 .v7-promotion-comparable-row.is-exploratory { opacity:.82; }
    #slide-32 .v7-promotion-annual.internal-small-cohort { border-color:color-mix(in oklab,var(--text-muted) 52%,transparent); background:color-mix(in oklab,var(--text-muted) 11%,transparent); color:var(--text-muted); }
    #slide-32 .v7-promotion-suppressed { color:var(--text-muted); font-size:9px; font-style:italic; line-height:1.15; }
    #slide-32 .v7-promotion-comparable-note { margin:0; padding-top:6px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:9px; line-height:1.2; }
    #slide-32 .v7-promotion-comparable-note strong { color:var(--text-main); }
    #slide-42 .v6-source-line { font-size:9px; line-height:1.16; }
    #slide-5 .ios-ytd-card { padding:12px 14px 10px; gap:8px; }
    #slide-5 .ios-ytd-definition { min-height:48px; }
    #slide-5 .ios-ytd-horizontal-area { display:grid; grid-template-rows:minmax(0,1fr) auto; gap:7px; min-height:0; flex:1; }
    #slide-5 .ios-ytd-horizontal-grid { display:grid; grid-template-columns:1fr; gap:10px; min-height:0; }
    #slide-5 .ios-ytd-year-panel { min-height:0; height:auto; padding:8px; gap:6px; border:1px solid var(--border-subtle); border-radius:12px; background:color-mix(in oklab,var(--bg-surface-2) 58%,transparent); box-shadow:none; }
    #slide-5 .ios-ytd-year-panel .v6-panel-heading { min-height:22px; font-size:10px; }
    #slide-5 .ios-ytd-year-panel .bar-list { min-height:0; flex:1; justify-content:space-evenly; gap:5px; }
    #slide-5 .ios-ytd-year-panel .ios-ytd-bar-row { grid-template-columns:minmax(180px,300px) minmax(100px,1fr) 112px; gap:9px; min-height:42px; padding-right:108px; }
    #slide-5 .ios-ytd-year-panel .bar-label { font-size:13px; line-height:1.1; text-align:right; white-space:nowrap; }
    #slide-5 .ios-ytd-year-panel .bar-track { height:15px; }
    #slide-5 .ios-ytd-year-panel .bar-value { font-size:12px; line-height:1.1; white-space:nowrap; }
    #slide-5 .ios-ytd-year-panel .bar-value span { display:inline; margin:0; color:var(--text-muted); font-size:12px; font-weight:700; }
    #slide-5 .ios-ytd-year-panel .bar-value span::before { content:' · '; }
    #slide-5 .ios-ytd-year-panel .v4-inline-attrition-rate { min-width:92px; padding:4px 9px; font-size:12px; text-align:right; }
    #slide-5 .ios-ytd-suppressed-row { grid-template-columns:minmax(180px,300px) minmax(0,1fr) !important; padding-right:0 !important; }
    #slide-5 .ios-ytd-suppressed { color:var(--text-muted); font-size:12px; font-style:italic; line-height:1.15; }
    #slide-5 .ios-ytd-method { margin:0; padding-top:6px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:11px; line-height:1.25; }
    #slide-5 .ios-ytd-method strong { color:var(--text-main); }
    @media (max-width:900px) { #slide-5 .ios-ytd-horizontal-grid { grid-template-columns:1fr; } }

    /* V7 slide 3 — recent application intensity in the Location grammar. */
    #slide-3 .application-visual-story { padding:14px 16px 10px; gap:10px; }
    .application-focus-years { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; min-height:0; flex:1; }
    .application-focus-card { min-width:0; padding:16px 18px 14px; border:1px solid var(--border-subtle); border-radius:14px; background:color-mix(in oklab,var(--bg-surface-2) 58%,transparent); display:flex; flex-direction:column; gap:12px; }
    .application-focus-card.is-current { border-color:var(--border-strong); background:color-mix(in oklab,var(--accent) 5%,var(--bg-surface)); box-shadow:inset 0 4px 0 var(--accent); }
    .application-focus-header { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; padding-bottom:9px; border-bottom:1px solid var(--border-subtle); }
    .application-focus-year { display:flex; flex-direction:column; gap:3px; }
    .application-focus-year strong { color:var(--text-main); font-size:22px; line-height:1; }
    .application-focus-year span { color:var(--text-muted); font-size:12px; font-variant-numeric:tabular-nums; }
    .application-period-pill { padding:4px 9px; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface); color:var(--text-muted); font-size:11px; font-weight:800; white-space:nowrap; }
    .application-repeat-hero { min-height:82px; display:flex; align-items:center; justify-content:space-between; gap:12px; padding:10px 13px; border-radius:12px; background:color-mix(in oklab,var(--accent) 10%,var(--bg-surface)); }
    .application-repeat-stat { display:flex; align-items:baseline; flex-wrap:wrap; gap:3px 9px; min-width:0; }
    .application-repeat-stat strong { color:var(--accent); font-size:42px; font-weight:900; line-height:.92; letter-spacing:-.035em; font-variant-numeric:tabular-nums; }
    .application-repeat-stat span { color:var(--text-main); font-size:13px; font-weight:800; line-height:1.15; }
    .application-repeat-stat small { width:100%; color:var(--text-muted); font-size:11px; font-weight:700; font-variant-numeric:tabular-nums; }
    .application-change-pill { flex:0 0 auto; padding:5px 9px; border-radius:var(--radius-pill); background:var(--accent); color:var(--text-invert); font-size:11px; font-weight:900; white-space:nowrap; }
    .application-focus-list { display:flex; flex-direction:column; justify-content:space-evenly; gap:0; min-height:0; flex:1; }
    .application-focus-row { display:grid; grid-template-columns:82px minmax(0,1fr) 86px 96px; align-items:center; gap:8px; min-height:65px; padding:7px 0; border-bottom:1px solid var(--border-subtle); }
    .application-focus-row:last-child { border-bottom:0; }
    .application-focus-label { display:flex; align-items:center; gap:7px; color:var(--text-main); font-size:14px; font-weight:800; white-space:nowrap; }
    .application-focus-key { width:10px; height:10px; flex:0 0 10px; border-radius:3px; background:#94A3B8; }
    .application-focus-key.is-repeat { background:var(--accent); }
    .application-focus-track { height:20px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    .application-focus-fill { height:100%; border-radius:inherit; background:#94A3B8; }
    .application-focus-fill.is-repeat { background:var(--accent); }
    .application-focus-value { display:flex; flex-direction:column; align-items:flex-end; gap:2px; min-width:0; font-variant-numeric:tabular-nums; }
    .application-focus-value strong { color:var(--text-main); font-size:15px; line-height:1; white-space:nowrap; }
    .application-focus-value span { color:var(--text-muted); font-size:11px; font-weight:700; line-height:1; white-space:nowrap; }
    #slide-3 .application-focus-attrition { position:static; transform:none; display:inline-flex; align-items:center; justify-content:center; justify-self:end; width:96px; min-width:96px; max-width:96px; padding:4px 6px; font-size:10px; line-height:1; text-align:center; white-space:nowrap; }
    .application-followup-band { display:flex; align-items:center; justify-content:center; gap:9px; padding:7px 11px; border:1px solid var(--border-subtle); border-radius:10px; background:var(--bg-surface-2); color:var(--text-muted); font-size:11px; line-height:1.2; text-align:center; }
    .application-followup-band strong { color:var(--text-main); }
    .application-visual-source { margin-top:auto; padding-top:6px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:10px; line-height:1.2; }
    .application-visual-source strong { color:var(--text-main); }
    @media (max-width:900px) { .application-focus-years { grid-template-columns:1fr; } }

    /* V7 slide 4 — application coverage simplified in the Location grammar. */
    #slide-4 .application-coverage-story { padding:14px 16px 10px; gap:10px; }
    #slide-4 .application-coverage-meta { display:flex; align-items:center; justify-content:space-between; gap:12px; color:var(--text-muted); font-size:11px; line-height:1.2; }
    #slide-4 .application-coverage-meta strong { color:var(--text-main); }
    .application-coverage-hero { padding:11px 13px; border:1px solid var(--border-subtle); border-radius:12px; background:var(--bg-surface-2); }
    .application-coverage-hero-head { display:flex; justify-content:space-between; gap:12px; margin-bottom:7px; color:var(--text-main); font-size:12px; font-weight:800; }
    .application-coverage-rail { display:flex; width:100%; height:46px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:12px; background:var(--bg-surface-3); }
    .application-coverage-segment { display:flex; align-items:center; justify-content:center; height:100%; color:#fff; font-size:14px; font-weight:900; line-height:1; text-shadow:0 1px 2px rgba(0,0,0,.34); white-space:nowrap; }
    .application-coverage-covered { background:var(--accent); }
    .application-coverage-unknown { background:#94A3B8; }
    .application-coverage-counts { display:grid; grid-template-columns:9.7596fr 90.2404fr; margin-top:5px; color:var(--text-muted); font-size:10px; font-variant-numeric:tabular-nums; }
    .application-coverage-counts span:first-child { text-align:left; }
    .application-coverage-counts span:last-child { text-align:right; }
    .application-coverage-lower { display:grid; grid-template-columns:minmax(0,1.08fr) minmax(0,.92fr); gap:10px; min-height:0; flex:1; }
    .application-covered-card,
    .application-history-card { min-height:0; padding:12px 14px; gap:8px; }
    .application-covered-list { display:flex; flex-direction:column; justify-content:space-evenly; gap:12px; min-height:0; flex:1; }
    .application-covered-row { display:grid; grid-template-columns:132px minmax(0,1fr) 118px; align-items:center; gap:9px; min-height:42px; }
    .application-covered-label { color:var(--text-main); font-size:13px; font-weight:800; line-height:1.05; }
    .application-covered-label span { display:block; margin-top:3px; color:var(--text-muted); font-size:10px; font-weight:600; }
    .application-covered-track { height:17px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    .application-covered-fill { height:100%; min-width:2px; border-radius:inherit; }
    .application-covered-value { color:var(--text-main); text-align:right; font-size:12px; font-weight:800; font-variant-numeric:tabular-nums; white-space:nowrap; }
    .application-covered-value span { display:block; margin-top:2px; color:var(--text-muted); font-size:10px; font-weight:600; }
    .application-history-summary { display:flex; justify-content:space-between; gap:10px; color:var(--text-muted); font-size:10px; line-height:1.2; }
    .application-history-summary strong { display:block; color:var(--text-main); font-size:13px; font-variant-numeric:tabular-nums; }
    .application-history-bars { display:flex; align-items:flex-end; justify-content:space-between; gap:7px; min-height:0; flex:1; padding:4px 2px 0; }
    .application-history-month { display:flex; flex:1 1 0; min-width:0; height:100%; flex-direction:column; align-items:center; justify-content:flex-end; gap:4px; }
    .application-history-rail { display:flex; width:100%; max-width:28px; height:148px; flex-direction:column; justify-content:flex-end; overflow:hidden; border:1px solid var(--border-subtle); border-radius:6px 6px 3px 3px; background:var(--bg-surface-3); }
    .application-history-unknown { width:100%; background:#94A3B8; }
    .application-history-covered { width:100%; background:var(--accent); }
    .application-history-month > span { color:var(--text-muted); font-size:10px; line-height:1; white-space:nowrap; }
    .application-coverage-note { padding:6px 9px; border-left:3px solid #B45309; border-radius:8px; background:color-mix(in oklab,#B45309 8%,var(--bg-surface)); color:var(--text-muted); font-size:10px; line-height:1.2; }
    .application-coverage-note strong { color:var(--text-main); }
    @media (max-width:900px) { .application-coverage-lower { grid-template-columns:1fr; } }

    /* V7 slide 3 consolidation — coverage context plus observed attrition. */
    #slide-3 .application-visual-story { padding:12px 16px 9px; gap:8px; }
    #slide-3 .application-coverage-context { padding:9px 12px 7px; border:1px solid var(--border-subtle); border-radius:11px; background:var(--bg-surface-2); }
    #slide-3 .application-coverage-context-head { display:flex; align-items:baseline; justify-content:space-between; gap:12px; margin-bottom:6px; }
    #slide-3 .application-coverage-context-head strong { color:var(--text-main); font-size:12px; }
    #slide-3 .application-coverage-context-head span { color:var(--text-muted); font-size:10px; font-weight:700; text-align:right; }
    #slide-3 .application-coverage-rail { height:34px; border-radius:9px; }
    #slide-3 .application-coverage-segment { font-size:12px; }
    #slide-3 .application-coverage-counts { margin-top:4px; font-size:10px; }
    #slide-3 .application-coverage-caveat { margin-top:4px; color:var(--text-muted); font-size:10px; line-height:1.15; text-align:center; }
    #slide-3 .application-focus-card { padding:13px 18px 11px; gap:8px; }
    #slide-3 .application-focus-header { padding-bottom:7px; }
    #slide-3 .application-repeat-hero { min-height:70px; padding:8px 13px; }
    #slide-3 .application-repeat-stat strong { font-size:38px; }
    #slide-3 .application-focus-keyline { display:grid; grid-template-columns:82px minmax(0,1fr) 86px 108px; align-items:end; gap:8px; min-height:14px; color:var(--text-muted); font-size:9px; font-weight:800; letter-spacing:.02em; text-transform:uppercase; }
    #slide-3 .application-focus-keyline span:first-child { grid-column:2 / 4; text-align:right; }
    #slide-3 .application-focus-keyline span:last-child { grid-column:4; text-align:center; }
    #slide-3 .application-focus-row { grid-template-columns:82px minmax(0,1fr) 86px 108px; min-height:58px; padding:5px 0; }
    #slide-3 .application-focus-track { height:18px; }
    #slide-3 .application-focus-attrition { width:108px; min-width:108px; max-width:108px; }
    #slide-3 .application-focus-attrition.is-small-base { background:var(--bg-surface-3); border-color:var(--border-subtle); color:var(--text-muted); }
    #slide-3 .application-followup-band { padding:6px 10px; font-size:10px; line-height:1.15; }
    #slide-3 .application-visual-source { padding-top:5px; font-size:9px; line-height:1.15; }

    /* V7 slide 14 — one readable three-group work-arrangement chart. */
    #slide-14 .v6-chart-area { min-height:0; }
    #slide-14 .work-arrangement-three-group-card { min-height:0; padding:20px 26px; gap:12px; }
    #slide-14 .work-arrangement-three-group-card .bar-list { flex:1; justify-content:center; gap:28px; padding:12px 0; }
    #slide-14 .work-arrangement-three-group-card .bar-row { grid-template-columns:minmax(260px,360px) minmax(0,1fr) 124px; gap:12px; min-height:58px; padding-right:68px; }
    #slide-14 .work-arrangement-three-group-card .bar-label { font-size:14px; line-height:1.15; }
    #slide-14 .work-arrangement-three-group-card .bar-track { height:18px; }
    #slide-14 .work-arrangement-three-group-card .bar-value { font-size:13px; white-space:nowrap; }
    #slide-14 .work-arrangement-three-group-card .v4-inline-attrition-rate { min-width:58px; font-size:13px; }
    #slide-14 .work-arrangement-three-group-card .chart-footer { margin:0; padding-top:9px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:11px; line-height:1.25; }

    /* V7 slide 15 — current organization distribution plus a visible, time-safe annual cohort result. */
    #slide-15 .engineering-cto-display-card { gap:4px; }
    #slide-15 .engineering-cto-display-card .bar-list { flex:0 0 auto; }
    #slide-15 .engineering-cto-display-card .chart-footer { display:block !important; margin:0; padding-top:5px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:9px; line-height:1.18; }

    /* V7 slide 16 — latest Rehire versus non-Rehire cohort comparison. */
    #slide-16 .rehire-comparison-card { min-height:0; padding:16px 22px 12px; gap:10px; }
    #slide-16 .rehire-comparison-card .bar-list { flex:1; justify-content:center; gap:22px; padding:10px 0; }
    #slide-16 .rehire-comparison-card .bar-row { grid-template-columns:minmax(180px,250px) minmax(0,1fr) 230px; gap:12px; min-height:54px; padding-right:0; }
    #slide-16 .rehire-comparison-card .bar-label { font-size:14px; line-height:1.15; }
    #slide-16 .rehire-comparison-card .bar-track { height:18px; }
    #slide-16 .rehire-comparison-card .bar-value { display:flex; align-items:center; justify-content:flex-end; gap:8px; font-size:13px; white-space:nowrap; }
    #slide-16 .rehire-comparison-card .rehire-comparison-attrition { position:static; transform:none; display:inline-flex; min-width:52px; padding:3px 6px; font-size:11px; line-height:1.1; text-align:center; }
    #slide-16 .rehire-comparison-keyline { display:grid; grid-template-columns:minmax(180px,250px) minmax(0,1fr) 230px; gap:12px; color:var(--text-muted); font-size:10px; font-weight:700; letter-spacing:.03em; text-transform:uppercase; }
    #slide-16 .rehire-comparison-keyline span:last-child { text-align:right; }
    #slide-16 .rehire-followup-note { margin:0; padding:7px 9px; border-left:3px solid #B45309; border-radius:7px; background:color-mix(in oklab,#B45309 8%,var(--bg-surface)); color:var(--text-main); font-size:10px; line-height:1.25; }
    #slide-16 .rehire-followup-note strong { color:var(--text-main); }

    /* V7 slide 16 - retain three historical fiscal-August cohorts. */
    #slide-16 .rehire-history-layout { display:grid; grid-template-rows:minmax(0,1fr) auto; gap:8px; height:100%; min-height:0; }
    #slide-16 .rehire-history-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; min-height:0; height:100%; }
    #slide-16 .rehire-year-card { min-width:0; min-height:0; padding:10px 12px 9px; gap:7px; }
    #slide-16 .rehire-year-card .v6-panel-heading { font-size:10px; }
    #slide-16 .rehire-year-card .rehire-comparison-keyline { grid-template-columns:minmax(86px,102px) minmax(0,1fr) minmax(94px,120px); gap:7px; font-size:8px; }
    #slide-16 .rehire-year-card .bar-list { flex:1; justify-content:flex-start; gap:16px; padding:10px 0 0; }
    #slide-16 .rehire-year-card .bar-row { grid-template-columns:minmax(86px,102px) minmax(0,1fr) minmax(94px,120px); gap:7px; min-height:56px; padding-right:0; }
    #slide-16 .rehire-year-card .bar-label { font-size:11px; line-height:1.1; }
    #slide-16 .rehire-year-card .bar-track { height:14px; }
    #slide-16 .rehire-year-card .bar-value { display:flex; align-items:center; justify-content:flex-end; gap:5px; font-size:10px; }
    #slide-16 .rehire-year-card .rehire-comparison-attrition { position:static; transform:none; display:inline-flex; min-width:42px; padding:3px 5px; font-size:10px; line-height:1.1; text-align:center; }
    #slide-16 .rehire-history-note { margin:0; padding:7px 9px; border-left:3px solid #B45309; border-radius:7px; background:color-mix(in oklab,#B45309 8%,var(--bg-surface)); color:var(--text-main); font-size:10px; line-height:1.25; }
    @media (max-width:900px) { #slide-16 .rehire-history-grid { grid-template-columns:1fr; overflow-y:auto; } }

    /* V7 slide 11 â€” one fiscal-August Job family distribution. */
    #slide-11 .job-family-august-story { padding:12px 14px 10px; gap:8px; }
    #slide-11 .job-family-august-card { min-height:0; padding:12px 18px 10px; gap:6px; }
    #slide-11 .job-family-august-card .bar-list { min-height:0; flex:1; gap:1px; overflow:visible; }
    #slide-11 .job-family-august-bar-row { grid-template-columns:minmax(250px,330px) minmax(0,1fr) 124px 76px; min-height:19px; gap:9px; padding-right:0; }
    #slide-11 .job-family-august-bar-row .bar-label,
    #slide-11 .job-family-august-bar-row .bar-value { font-size:9.5px; line-height:1; }
    #slide-11 .job-family-august-bar-row .bar-track { height:9px; }
    #slide-11 .job-family-august-attrition { position:static; transform:none; display:inline-flex; min-width:0; width:100%; box-sizing:border-box; justify-content:center; padding:2px 4px; font-size:9.5px; line-height:1; text-align:center; }
    #slide-11 .job-family-august-card .chart-footer { display:block !important; margin:0; padding-top:4px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:9.5px; line-height:1.1; }

    /* V7 slides 20-27: original QVoice distributions at full width. Attrition
       is represented only by four direct labels in slide 20's wave table. */
    #slide-20 .two-pane,
    #slide-21 .two-pane,
    #slide-25 .two-pane,
    #slide-26 .two-pane,
    #slide-27 .two-pane { display:grid; grid-template-columns:minmax(0,1.6fr) minmax(318px,.84fr); gap:12px; }
    #slide-23 .two-pane,
    #slide-24 .two-pane { display:grid; grid-template-columns:minmax(0,1.36fr) minmax(344px,.94fr); gap:12px; }
    #slide-20 .qvoice-comment-card,
    #slide-21 .qvoice-retention-card,
    #slide-25 .qvoice-comparable-card,
    #slide-26 .qvoice-heartbeat-card,
    #slide-27 .qvoice-normalized-region-card { min-width:0; }
    #slide-20 .two-pane,
    #slide-21 .two-pane,
    #slide-23 .two-pane,
    #slide-24 .two-pane,
    #slide-25 .two-pane,
    #slide-26 .two-pane,
    #slide-27 .two-pane { display:block !important; }
    #slide-20 .qvoice-comment-card,
    #slide-21 .qvoice-retention-card,
    #slide-25 .qvoice-comparable-card,
    #slide-26 .qvoice-heartbeat-card,
    #slide-27 .qvoice-normalized-region-card { width:100% !important; }
    #slide-20 .qvoice-comment-table td:first-child { display:flex !important; align-items:center; gap:6px; }
    #slide-20 .qvoice-wave-attrition.v6-rate-pill { position:static !important; transform:none !important; display:inline-block !important; min-width:0 !important; padding:2px 5px !important; font-size:8.5px !important; line-height:1.1 !important; text-align:left !important; }
    #slide-20 .qvoice-comment-table,
    #slide-20 .qvoice-diagnostic-table { font-size:9px; }
    #slide-20 .qvoice-comment-note,
    #slide-20 .qvoice-diagnostic-note,
    #slide-21 .retention-footnote,
    #slide-25 .chart-footer,
    #slide-26 .chart-footer,
    #slide-27 .chart-footer { font-size:9px; line-height:1.18; }
    #slide-21 .retention-theme-label { font-size:10px; }
    #slide-26 .qvoice-heartbeat-item span { font-size:9px; }
    #slide-26 .qvoice-heartbeat-value { min-width:90px; }
    /* QVoice layout refresh: the reference slide's horizontal-bar hierarchy is
       applied to the rate panel without changing a displayed value or cohort. */
    #slide-20 .two-pane,
    #slide-21 .two-pane,
    #slide-23 .two-pane,
    #slide-24 .two-pane,
    #slide-25 .two-pane,
    #slide-27 .two-pane { grid-template-columns:minmax(0,1.52fr) minmax(400px,.92fr); gap:14px; }
    .qvoice-ytd-attrition-card { min-width:0; min-height:0; height:100%; padding:12px 14px 10px; gap:8px; border-color:var(--border-strong); background:color-mix(in oklab,var(--bg-surface-2) 78%,transparent); }
    .qvoice-ytd-attrition-card .v6-panel-heading { min-height:auto; margin:0; padding-bottom:6px; font-size:10px; line-height:1.15; }
    .qvoice-ytd-window { margin:0; padding:6px 7px; border-left:3px solid var(--accent); border-radius:6px; background:color-mix(in oklab,var(--accent) 8%,transparent); color:var(--text-main); font-size:9.5px; line-height:1.28; }
    .qvoice-ytd-rate-list { display:flex; flex:1; flex-direction:column; min-height:0; }
    .qvoice-ytd-rate-row { display:grid; flex:1 1 0; grid-template-columns:minmax(0,1fr) auto; grid-template-areas:"label pill" "track track" "cohort cohort"; column-gap:8px; row-gap:4px; align-content:center; padding:8px 0; border-bottom:1px solid var(--border-subtle); }
    .qvoice-ytd-rate-row:last-child { border-bottom:0; }
    .qvoice-ytd-rate-label { grid-area:label; min-width:0; color:var(--text-main); font-size:10.5px; font-weight:700; line-height:1.15; }
    .qvoice-ytd-rate-row .v6-rate-pill { grid-area:pill; position:static; transform:none; min-width:52px; padding:3px 6px; font-size:11px; line-height:1; text-align:center; font-variant-numeric:tabular-nums; }
    .qvoice-ytd-rate-track { grid-area:track; height:8px; overflow:hidden; border:1px solid color-mix(in oklab,var(--text-muted) 18%,transparent); border-radius:var(--radius-pill); background:color-mix(in oklab,var(--text-muted) 10%,transparent); }
    .qvoice-ytd-rate-fill { height:100%; min-width:10%; border-radius:inherit; }
    .qvoice-ytd-rate-fill.attr-low { background:#15803d; }
    .qvoice-ytd-rate-fill.attr-mid { background:var(--accent-2); }
    .qvoice-ytd-rate-fill.attr-high { background:#c2410c; }
    .qvoice-ytd-cohort { grid-area:cohort; color:var(--text-muted); font-size:9px; font-variant-numeric:tabular-nums; line-height:1.1; }
    .qvoice-ytd-color-key { margin:0; padding-top:6px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:8.5px; line-height:1.15; }
    .qvoice-ytd-color-key i { display:inline-block; width:7px; height:7px; margin:0 2px 0 4px; border-radius:50%; vertical-align:middle; }
    .qvoice-ytd-color-key i.attr-low { background:#15803d; }
    .qvoice-ytd-color-key i.attr-mid { background:var(--accent-2); }
    .qvoice-ytd-color-key i.attr-high { background:#c2410c; }
    #slide-26 .two-pane { display:grid; grid-template-columns:1fr; grid-template-rows:minmax(0,1fr) 94px; gap:8px; }
    #slide-26 .qvoice-ytd-attrition-card { display:flex; flex-direction:row; align-items:center; height:auto; padding:8px 12px; gap:12px; }
    #slide-26 .qvoice-ytd-attrition-card .v6-panel-heading { flex:0 0 205px; border-bottom:0; padding:0; }
    #slide-26 .qvoice-ytd-window { flex:0 0 260px; }
    #slide-26 .qvoice-ytd-rate-list { flex:1; display:block; }
    #slide-26 .qvoice-ytd-rate-row { height:100%; padding:0; }
    #slide-26 .qvoice-ytd-color-key { flex:0 0 170px; padding:0; border-top:0; }
    #slide-23 .qvoice-ytd-rate-label { font-size:10px; }
    #slide-27 .qvoice-ytd-rate-label { font-size:9.5px; }

    /* V7 slide 20 — replace the two numeric tables with visual comparisons.
       The topic chart is retained; the right panel uses a shared, zero-based
       scale so values can be compared directly across every survey wave. */
    #slide-20 .two-pane { display:grid !important; grid-template-columns:minmax(0,1.15fr) minmax(340px,.85fr); gap:14px; }
    #slide-20 .qvoice-comment-card { width:auto !important; min-height:0; }
    #slide-20 .qvoice-comment-chart { height:300px; flex:0 0 300px; }
    #slide-20 .qvoice-wave-name { color:var(--text-main); font-size:9px; font-weight:800; line-height:1.1; white-space:nowrap; }
    #slide-20 .qvoice-office-context-card { width:auto !important; min-height:0; padding:12px 14px; gap:7px; }
    #slide-20 .qvoice-office-context-card .v6-panel-heading { margin:0; padding-bottom:5px; }
    #slide-20 .qvoice-office-context-intro,
    #slide-20 .qvoice-office-context-note { margin:0; color:var(--text-muted); font-size:9px; line-height:1.22; }
    #slide-20 .qvoice-context-list { display:flex; flex:1; flex-direction:column; justify-content:space-around; min-height:0; }
    #slide-20 .qvoice-context-row { display:grid; grid-template-columns:160px minmax(0,1fr); column-gap:7px; row-gap:4px; align-items:center; padding:7px 0; border-bottom:1px solid var(--border-subtle); }
    #slide-20 .qvoice-context-row:last-child { border-bottom:0; }
    #slide-20 .qvoice-context-wave { grid-row:span 2; display:flex; flex-wrap:wrap; align-items:center; align-content:center; gap:4px 5px; min-width:0; color:var(--text-main); font-size:10px; font-weight:800; line-height:1.1; }
    #slide-20 .qvoice-context-metric { display:grid; grid-template-columns:110px minmax(0,1fr) 40px; gap:5px; align-items:center; }
    #slide-20 .qvoice-context-label { color:var(--text-muted); font-size:8.5px; line-height:1.05; white-space:nowrap; }
    #slide-20 .qvoice-context-track { height:10px; overflow:hidden; border-radius:var(--radius-pill); background:color-mix(in oklab,var(--accent) 10%,var(--bg-surface-3)); }
    #slide-20 .qvoice-context-fill { min-width:3px; height:100%; border-radius:inherit; }
    #slide-20 .qvoice-context-fill.is-improvement { background:linear-gradient(90deg,var(--accent),var(--accent-2)); }
    #slide-20 .qvoice-context-fill.is-friction { background:linear-gradient(90deg,#B08A00,#D4A900); }
    #slide-20 .qvoice-context-value { color:var(--text-main); font-size:9px; font-weight:800; font-variant-numeric:tabular-nums; text-align:right; }

    /* V7 slide 19 — V4 distance-band distribution retained as a full-width comparison. */
    #slide-19 .commute-distance-comparison-layout { display:block; height:100%; min-height:0; }
    #slide-19 .commute-distance-comparison-card { height:100%; min-height:0; padding:18px 22px; gap:10px; }
    #slide-19 .commute-distance-comparison-card .commute-comparison-list { justify-content:space-evenly; gap:8px; }
    #slide-19 .commute-distance-comparison-card .commute-comparison-row { grid-template-columns:104px minmax(0,1fr); gap:14px; padding:6px 0; }
    #slide-19 .commute-distance-comparison-card .commute-comparison-label { font-size:12px; }
    #slide-19 .commute-distance-comparison-card .commute-comparison-series { gap:16px; }
    #slide-19 .commute-distance-comparison-card .commute-series-name { font-size:11px; }
    #slide-19 .commute-distance-comparison-card .commute-series-value { font-size:11px; }
    #slide-19 .commute-distance-comparison-card .commute-comparison-line { grid-template-rows:auto 13px; gap:4px 7px; }
    #slide-19 .commute-distance-comparison-card .commute-comparison-line .bar-track { height:13px; }
    #slide-19 .commute-distance-comparison-card .commute-attrition-line { grid-template-columns:minmax(0,1fr) auto auto; gap:4px 7px; }
    #slide-19 .commute-distance-comparison-card .commute-all-eligible-attrition,
    #slide-19 .commute-distance-comparison-card .commute-onsite-attrition { position:static; grid-column:3; grid-row:1; min-width:54px; padding:2px 6px; transform:none; font-size:10px; line-height:1.1; text-align:right; justify-self:end; }
    #slide-19 .commute-distance-comparison-card .commute-all-eligible-attrition.attr-unavailable,
    #slide-19 .commute-distance-comparison-card .commute-onsite-attrition.attr-unavailable { min-width:88px; }
    #slide-19 .commute-distance-comparison-card .chart-footer { display:block !important; margin:0; padding-top:8px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:11px; line-height:1.25; }

    /* V7 multi-chart layouts — Julia-style dividers in the inter-panel gaps. */
    .v6-chart-area .two-chart,
    .manager-change-comparison-grid { position:relative; }
    .v6-chart-area .two-chart::before,
    .manager-change-comparison-grid::before {
      content:"";
      position:absolute;
      z-index:0;
      top:0;
      bottom:0;
      left:50%;
      width:1px;
      background:var(--border-subtle);
      pointer-events:none;
    }
    #slide-12 .v6-chart-area .two-chart::before { left:calc(33.333% - 3px); }
    #slide-12 .v6-chart-area .two-chart::after {
      content:"";
      position:absolute;
      z-index:0;
      top:0;
      bottom:0;
      left:calc(66.667% + 3px);
      width:1px;
      background:var(--border-subtle);
      pointer-events:none;
    }
    @media (max-width:900px) {
      .v6-chart-area .two-chart::before,
      #slide-12 .v6-chart-area .two-chart::after { display:none; }
    }

    /* V7 nav slides 28–39 — annual voluntary attrition in the Location visual grammar. */
    #slide-29 .v4-inline-attrition-row,
    #slide-31 .v4-inline-attrition-row,
    #slide-32 .v4-inline-attrition-row,
    #slide-35 .v4-inline-attrition-row,
    #slide-37 .v4-inline-attrition-row,
    #slide-38 .v4-inline-attrition-row,
    #slide-39 .v4-inline-attrition-row,
    #slide-40 .v4-inline-attrition-row { padding-right:96px; }
    #slide-29 .v7-annual-attrition,
    #slide-31 .v7-annual-attrition,
    #slide-32 .v7-annual-attrition,
    #slide-35 .v7-annual-attrition,
    #slide-37 .v7-annual-attrition,
    #slide-38 .v7-annual-attrition,
    #slide-39 .v7-annual-attrition,
    #slide-40 .v7-annual-attrition { min-width:86px; padding:3px 6px; font-size:10px; text-align:center; }
    #slide-29 .role-level-tenure-card .bar-list,
    #slide-31 .company-tenure-card .bar-list,
    #slide-32 .promotion-distribution-card .bar-list { gap:5px; }
    #slide-29 .bar-row,
    #slide-31 .bar-row,
    #slide-32 .bar-row { min-height:28px; }
    #slide-35 .level-main-card .bar-list,
    #slide-35 .level-support-card .bar-list,
    #slide-38 .compensation-grade-card .bar-list { overflow-y:auto; padding-right:4px; }
    /* Keep the three Level views inside the fixed slide stage.  The job-level
       card has more visible categories than the management card, so it gets
       the larger share and retains its own vertical scroll if needed. */
    #slide-35 .v6-chart-area .two-pane { display:grid; grid-template-columns:minmax(0,1fr); grid-template-rows:minmax(0,1fr); }
    #slide-35 .level-constructs { height:auto; max-height:100%; grid-template-rows:minmax(0,1fr); overflow:hidden; }
    #slide-35 .level-main-card,
    #slide-35 .level-support-card,
    #slide-35 .level-job-detail-card { min-height:0; height:auto; }
    #slide-35 .level-support-stack { min-height:0; height:auto; }
    #slide-35 .level-support-stack { grid-template-rows:minmax(0,.65fr) minmax(0,1.35fr); }
    #slide-35 .level-job-detail-card .bar-list { overflow-y:auto; padding-right:4px; }
    #slide-35 .level-support-card .bar-row,
    #slide-35 .level-job-detail-card .bar-row { min-height:24px; }
    #slide-35 .level-main-card .bar-row,
    #slide-38 .compensation-grade-card .bar-row { min-height:30px; }
    #slide-37 .layers-from-ceo-distribution-card .bar-list { gap:5px; }
    #slide-37 .layers-from-ceo-distribution-card .bar-row { min-height:30px; }

    /* V7 follow-up after manager layers: authorized exact-grade internal exploration. */
    #slide-37-followup { grid-template-rows:auto minmax(0,1fr); gap:8px; }
    #slide-37-followup .layers-grade-followup-card { min-height:0; padding:12px 18px 10px; gap:8px; }
    #slide-37-followup .layers-grade-followup-intro { display:grid; grid-template-columns:minmax(0,1.35fr) minmax(330px,.65fr); gap:16px; align-items:center; padding:9px 12px; border:1px solid var(--border-subtle); border-radius:12px; background:color-mix(in oklab,var(--accent) 5%,var(--bg-surface)); }
    #slide-37-followup .layers-grade-followup-intro > div { display:flex; flex-direction:column; gap:3px; min-width:0; }
    #slide-37-followup .layers-grade-followup-eyebrow { color:var(--text-muted); font-size:10px; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }
    #slide-37-followup .layers-grade-followup-intro strong { color:var(--text-main); font-size:16px; line-height:1.2; font-variant-numeric:tabular-nums; }
    #slide-37-followup .layers-grade-followup-intro p { margin:0; color:var(--text-muted); font-size:12px; line-height:1.3; }
    #slide-37-followup .layers-grade-followup-chart { display:flex; flex:1; flex-direction:column; min-height:0; gap:4px; padding:1px 3px 0; }
    #slide-37-followup .layers-grade-followup-keyline,
    #slide-37-followup .layers-grade-followup-bar-row { display:grid; grid-template-columns:minmax(80px,106px) minmax(0,1fr) 92px 82px 76px 106px; column-gap:8px; align-items:center; }
    #slide-37-followup .layers-grade-followup-keyline { padding:0 0 4px; border-bottom:1px solid var(--border-subtle); color:var(--text-muted); font-size:10px; font-weight:800; letter-spacing:.04em; line-height:1; text-transform:uppercase; }
    #slide-37-followup .layers-grade-followup-keyline span:nth-child(n+3) { text-align:right; }
    #slide-37-followup .layers-grade-followup-keyline span:last-child { text-align:center; }
    #slide-37-followup .layers-grade-followup-bar-list { display:flex; flex:1; flex-direction:column; justify-content:space-evenly; min-height:0; gap:1px; overflow:visible; }
    #slide-37-followup .layers-grade-followup-cell { min-height:25px; padding:3px 0; border-bottom:1px solid var(--border-subtle); }
    #slide-37-followup .layers-grade-followup-cell:last-child { border-bottom:0; }
    #slide-37-followup .layers-grade-followup-cell.is-comparable { background:linear-gradient(90deg,color-mix(in oklab,var(--accent) 6%,transparent),transparent 58%); }
    #slide-37-followup .layers-grade-followup-label { color:var(--text-main); font-size:11px; font-weight:800; line-height:1; letter-spacing:.02em; }
    #slide-37-followup .layers-grade-followup-cell.is-comparable .layers-grade-followup-label { color:var(--accent); }
    #slide-37-followup .layers-grade-followup-track { height:9px; overflow:hidden; border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    #slide-37-followup .layers-grade-followup-track span { display:block; min-width:3px; height:100%; border-radius:inherit; background:linear-gradient(90deg,var(--accent-2),var(--accent)); }
    #slide-37-followup .layers-grade-followup-cell.is-exploratory .layers-grade-followup-track span { background:color-mix(in oklab,var(--text-muted) 55%,var(--accent-soft)); }
    #slide-37-followup .layers-grade-followup-distribution,
    #slide-37-followup .layers-grade-followup-exits { color:var(--text-muted); font-size:10px; line-height:1; text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
    #slide-37-followup .layers-grade-followup-distribution { color:var(--text-main); font-weight:700; }
    #slide-37-followup .layers-grade-followup-attrition.v6-rate-pill { position:static; transform:none; display:inline-flex; width:100%; min-width:0; box-sizing:border-box; align-items:center; justify-content:center; padding:3px 4px; font-size:10px; line-height:1; text-align:center; }
    #slide-37-followup .layers-grade-followup-exploratory,
    #slide-37-followup .layers-grade-followup-comparable { display:inline-flex; align-items:center; justify-content:center; min-width:0; padding:3px 4px; border-radius:var(--radius-pill); font-size:10px; font-weight:800; line-height:1; text-align:center; white-space:nowrap; }
    #slide-37-followup .layers-grade-followup-exploratory { border:1px dashed color-mix(in oklab,var(--text-muted) 42%,transparent); color:var(--text-muted); }
    #slide-37-followup .layers-grade-followup-comparable { border:1px solid color-mix(in oklab,var(--accent) 28%,transparent); background:color-mix(in oklab,var(--accent) 8%,transparent); color:var(--accent); }
    #slide-37-followup .layers-grade-followup-takeaway { padding:7px 10px; border-left:4px solid var(--accent); border-radius:8px; background:color-mix(in oklab,var(--accent) 7%,var(--bg-surface)); color:var(--text-main); font-size:12px; line-height:1.25; }
    #slide-37-followup .layers-grade-followup-caveat { color:var(--text-muted); font-size:10px; line-height:1.2; }
    #slide-37-followup .layers-grade-followup-source { padding-top:6px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:10px; line-height:1.15; }
    #slide-37-followup .layers-grade-followup-source strong { color:var(--text-main); }
    @media (max-width:900px) {
      #slide-37-followup .layers-grade-followup-intro { grid-template-columns:1fr; }
      #slide-37-followup .layers-grade-followup-keyline,
      #slide-37-followup .layers-grade-followup-bar-row { grid-template-columns:70px minmax(0,1fr) 78px 68px 64px 88px; column-gap:5px; }
    }

    /* V7 follow-up after exact grades: reconstructed direct-team span. */
    #slide-37-span-followup { grid-template-rows:auto minmax(0,1fr); gap:8px; }
    #slide-37-span-followup .direct-team-span-card { min-height:0; padding:12px 18px 10px; gap:8px; }
    #slide-37-span-followup .direct-team-span-intro { display:grid; grid-template-columns:minmax(0,1.3fr) minmax(320px,.7fr); gap:16px; align-items:center; padding:9px 12px; border:1px solid var(--border-subtle); border-radius:12px; background:color-mix(in oklab,var(--accent) 5%,var(--bg-surface)); }
    #slide-37-span-followup .direct-team-span-intro > div { display:flex; flex-direction:column; gap:3px; min-width:0; }
    #slide-37-span-followup .direct-team-span-eyebrow { color:var(--text-muted); font-size:10px; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }
    #slide-37-span-followup .direct-team-span-intro strong { color:var(--text-main); font-size:16px; line-height:1.2; font-variant-numeric:tabular-nums; }
    #slide-37-span-followup .direct-team-span-intro p { margin:0; color:var(--text-muted); font-size:12px; line-height:1.3; }
    #slide-37-span-followup .direct-team-span-chart { display:flex; flex:1; flex-direction:column; min-height:0; gap:5px; padding:2px 4px 0; }
    #slide-37-span-followup .direct-team-span-keyline,
    #slide-37-span-followup .direct-team-span-bar-row { display:grid; grid-template-columns:minmax(120px,150px) minmax(0,1fr) 118px 164px 88px; column-gap:10px; align-items:center; }
    #slide-37-span-followup .direct-team-span-keyline { padding:0 0 4px; border-bottom:1px solid var(--border-subtle); color:var(--text-muted); font-size:10px; font-weight:800; letter-spacing:.05em; line-height:1; text-transform:uppercase; }
    #slide-37-span-followup .direct-team-span-keyline span:nth-child(n+3) { text-align:right; }
    #slide-37-span-followup .direct-team-span-bar-list { display:flex; flex:1; flex-direction:column; justify-content:space-evenly; min-height:0; gap:4px; overflow:visible; }
    #slide-37-span-followup .direct-team-span-bar-row { min-height:43px; padding:4px 0; border-bottom:1px solid var(--border-subtle); }
    #slide-37-span-followup .direct-team-span-bar-row:last-child { border-bottom:0; }
    #slide-37-span-followup .direct-team-span-bar-row.is-largest { background:linear-gradient(90deg,color-mix(in oklab,var(--accent) 6%,transparent),transparent 58%); }
    #slide-37-span-followup .direct-team-span-label { color:var(--text-main); font-size:15px; font-weight:800; line-height:1; }
    #slide-37-span-followup .direct-team-span-bar-row.is-largest .direct-team-span-label { color:var(--accent); }
    #slide-37-span-followup .direct-team-span-track { height:15px; overflow:hidden; border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    #slide-37-span-followup .direct-team-span-track span { display:block; min-width:3px; height:100%; border-radius:inherit; background:linear-gradient(90deg,var(--accent-2),var(--accent)); }
    #slide-37-span-followup .direct-team-span-distribution,
    #slide-37-span-followup .direct-team-span-detail { color:var(--text-muted); font-size:11px; line-height:1.1; text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
    #slide-37-span-followup .direct-team-span-distribution { color:var(--text-main); font-weight:700; }
    #slide-37-span-followup .direct-team-span-attrition.v6-rate-pill { position:static; transform:none; display:inline-flex; width:100%; min-width:0; box-sizing:border-box; align-items:center; justify-content:center; padding:4px 5px; font-size:11px; line-height:1; text-align:center; }
    #slide-37-span-followup .direct-team-span-exact { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }
    #slide-37-span-followup .direct-team-span-exact-card { display:flex; align-items:center; justify-content:space-between; gap:12px; min-width:0; padding:7px 10px; border:1px solid var(--border-subtle); border-radius:9px; background:color-mix(in oklab,var(--bg-surface) 96%,transparent); }
    #slide-37-span-followup .direct-team-span-exact-card.is-exploratory { border-style:dashed; border-color:color-mix(in oklab,var(--text-muted) 55%,var(--border-subtle)); }
    #slide-37-span-followup .direct-team-span-exact-card strong { display:block; color:var(--text-main); font-size:12px; line-height:1.15; }
    #slide-37-span-followup .direct-team-span-exact-card span { display:block; color:var(--text-muted); font-size:10px; line-height:1.15; font-variant-numeric:tabular-nums; }
    #slide-37-span-followup .direct-team-span-exact-rate { color:var(--text-main); font-size:15px; font-weight:800; white-space:nowrap; font-variant-numeric:tabular-nums; }
    #slide-37-span-followup .direct-team-span-caveat { padding:7px 10px; border-left:4px solid var(--accent); border-radius:8px; background:color-mix(in oklab,var(--accent) 7%,var(--bg-surface)); color:var(--text-main); font-size:11px; line-height:1.25; }
    #slide-37-span-followup .direct-team-span-source { padding-top:6px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:10px; line-height:1.15; }
    #slide-37-span-followup .direct-team-span-source strong { color:var(--text-main); }
    @media (max-width:900px) {
      #slide-37-span-followup .direct-team-span-intro { grid-template-columns:1fr; }
      #slide-37-span-followup .direct-team-span-keyline,
      #slide-37-span-followup .direct-team-span-bar-row { grid-template-columns:minmax(90px,120px) minmax(0,1fr) 92px 126px 72px; column-gap:7px; }
      #slide-37-span-followup .direct-team-span-detail { white-space:normal; }
    }

    #slide-33 .promotion-grade-matrix td { padding:4px 3px; vertical-align:middle; white-space:normal; }
    #slide-33 .v7-matrix-annual-pill { position:static; display:inline-flex; align-items:center; gap:2px; min-width:0; margin:2px 0 0; padding:2px 4px; font-size:10px; line-height:1; text-align:center; }
    #slide-33 .v7-annual-pill-prefix { color:inherit; font-size:9px; font-weight:900; letter-spacing:.03em; }
    #slide-33 .promotion-grade-matrix tbody tr { height:39px; }

    #slide-34 .entry-path-list { gap:8px; }
    #slide-34 .entry-path-row { grid-template-rows:auto auto; align-items:center; }
    #slide-34 .entry-path-annual-rates { grid-column:2 / -1; display:flex; flex-wrap:wrap; gap:3px; min-width:0; margin-top:-3px; }
    #slide-34 .v7-entry-path-annual-pill { position:static; display:inline-flex; align-items:center; gap:2px; min-width:0; padding:2px 4px; font-size:10px; line-height:1; text-align:center; }
    #slide-34 .v7-entry-path-annual-pill .v7-annual-pill-prefix { color:inherit; font-size:9px; font-weight:900; }

    #slide-36 .level-grade-family-chart { gap:7px; overflow-y:auto; padding-right:3px; }
    #slide-36 .level-grade-family-row { grid-template-rows:auto auto; min-height:44px; }
    #slide-36 .level-grade-family-track { grid-column:2; grid-row:1; }
    #slide-36 .level-grade-family-total { grid-column:3; grid-row:1; }
    #slide-36 .level-grade-family-annual-rates { grid-column:2 / -1; grid-row:2; display:flex; flex-wrap:wrap; gap:3px; min-width:0; }
    #slide-36 .level-grade-family-legend { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:4px 16px; font-size:10.5px; }
    #slide-36 .level-grade-family-legend-item { min-width:0; }
    #slide-36 .v7-level-family-annual-pill { position:static; display:inline-flex; align-items:center; gap:2px; min-width:0; padding:2px 4px; font-size:10px; line-height:1; text-align:center; }
    #slide-36 .v7-level-family-annual-pill .v7-annual-pill-prefix { color:inherit; font-size:9px; font-weight:900; }

    #slide-39 .v7-comp-ratio-annual-card { padding:13px 15px; gap:7px; }
    #slide-39 .v7-comp-ratio-annual-definition { margin:0; color:var(--text-muted); font-size:10px; line-height:1.22; }
    #slide-39 .v7-comp-ratio-annual-list { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:5px 10px; flex:1; align-content:center; }
    #slide-39 .v7-comp-ratio-annual-row { display:flex; align-items:center; justify-content:space-between; gap:5px; min-width:0; padding:4px 0; border-bottom:1px solid var(--border-subtle); color:var(--text-main); font-size:10px; font-weight:700; }
    #slide-39 .v7-comp-ratio-annual-row > span:first-child { min-width:0; white-space:nowrap; }
    #slide-39 .v7-comp-ratio-annual-pill { position:static; flex:0 0 auto; min-width:0; padding:3px 5px; font-size:10px; line-height:1; text-align:center; }
    #slide-39 .v7-comp-ratio-annual-card .chart-footer { margin:0; padding-top:6px; font-size:10px; line-height:1.22; }

    #slide-40 .within-team-compensation-stack .bar-list { overflow-y:auto; padding-right:4px; }
    #slide-40 .within-team-compensation-stack .bar-row { min-height:29px; }
    #slide-40 .within-team-state-card { grid-template-columns:auto 1fr; }
    #slide-40 .v7-within-team-state-pill { position:static; display:inline-block; min-width:0; margin-right:7px; padding:3px 6px; font-size:10px; line-height:1; text-align:center; vertical-align:middle; }
    #slide-40 .within-team-state-value { display:flex; align-items:center; flex-wrap:wrap; gap:4px; }

    /* V7 visible slides 37-44 / technical stages 43-50 — baseline August 2025 cohort attrition labels. */
    #slide-43 .v6-distribution-only .bar-row,
    #slide-44 .v6-distribution-only .bar-row,
    #slide-45 .v6-distribution-only .bar-row,
    #slide-46 .v6-distribution-only .bar-row,
    #slide-47 .v6-distribution-only .bar-row { padding-right:96px; }
    #slide-43 .v7-annual-attrition,
    #slide-44 .v7-annual-attrition,
    #slide-45 .v7-annual-attrition,
    #slide-46 .v7-annual-attrition,
    #slide-47 .v7-annual-attrition { min-width:86px; padding:3px 6px; font-size:10px; text-align:center; }
    #slide-47 .v7-annual-attrition.internal-small-cohort { border-style:dashed; }
    #slide-43 .bar-list,
    #slide-44 .bar-list,
    #slide-45 .bar-list,
    #slide-46 .bar-list,
    #slide-47 .bar-list { gap:10px; }
    #slide-47 .two-chart { gap:18px; }
    #slide-48 .v7-manager-change-annual-summary { display:flex; flex-wrap:wrap; align-items:center; gap:7px; margin:2px 0 4px; }
    #slide-48 .v7-manager-change-summary-pill { position:static; display:inline-block; min-width:0; padding:4px 8px; font-size:11px; text-align:center; transform:none; }
    #slide-49 .manager-change-comparison-card .bar-row { padding-right:92px; }
    #slide-49 .manager-change-comparison-card .v7-annual-attrition { min-width:82px; padding:3px 5px; font-size:9px; text-align:center; }
    #slide-49 .manager-change-comparison-grid { gap:10px; }
    #slide-50 .talent-index-distribution-card .bar-row { padding-right:96px; min-height:25px; }
    @media (max-width:900px) {
      #slide-39 .v7-comp-ratio-annual-list { grid-template-columns:1fr; }
      #slide-36 .level-grade-family-annual-rates { display:none; }
    }

    /* V7 QVoice navigation slides 18-25: compact relative-color attrition
       labels attached to the same displayed distribution cohorts. */
    .qvoice-inline-attrition-panel { flex:0 0 auto; min-width:0; margin-top:9px; padding:8px 10px 7px; border:1px solid var(--border-strong); border-radius:11px; background:color-mix(in oklab,var(--bg-surface-2) 72%,transparent); }
    .qvoice-inline-attrition-head { display:flex; align-items:baseline; justify-content:space-between; gap:10px; padding-bottom:5px; border-bottom:1px solid var(--border-subtle); }
    .qvoice-inline-attrition-head strong { min-width:0; color:var(--text-main); font-size:10px; line-height:1.15; }
    .qvoice-inline-attrition-head span { flex:0 0 auto; color:var(--text-muted); font-size:9px; line-height:1.15; white-space:nowrap; }
    .qvoice-inline-attrition-list { display:flex; flex-direction:column; gap:2px; margin-top:4px; }
    .qvoice-inline-attrition-row { display:grid; grid-template-columns:minmax(0,1fr) auto 100px; align-items:center; gap:7px; min-height:19px; padding:2px 0; border-bottom:1px solid color-mix(in oklab,var(--border-subtle) 70%,transparent); }
    .qvoice-inline-attrition-row:last-child { border-bottom:0; }
    .qvoice-inline-attrition-label { min-width:0; overflow:hidden; color:var(--text-main); font-size:9.5px; line-height:1.1; text-overflow:ellipsis; white-space:nowrap; }
    .qvoice-inline-attrition-cohort { color:var(--text-muted); font-size:8.5px; line-height:1.1; font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }
    .qvoice-inline-attrition-pill { position:static !important; display:inline-flex; align-items:center; justify-content:center; min-width:48px; padding:3px 5px; transform:none !important; font-size:9.5px; line-height:1; text-align:center; font-variant-numeric:tabular-nums; }
    .qvoice-inline-attrition-key { display:flex; align-items:center; flex-wrap:wrap; gap:3px 9px; margin-top:4px; color:var(--text-muted); font-size:8px; line-height:1.1; }
    .qvoice-inline-attrition-key span { display:inline-flex; align-items:center; gap:3px; white-space:nowrap; }
    .qvoice-inline-attrition-key i { display:inline-block; width:7px; height:7px; border-radius:50%; }
    .qvoice-inline-attrition-key i.attr-low { background:#15803d; }
    .qvoice-inline-attrition-key i.attr-mid { background:var(--accent-2); }
    .qvoice-inline-attrition-key i.attr-high { background:#c2410c; }
    .qvoice18-attrition-pill { position:static !important; display:inline-flex !important; align-items:center; justify-content:center; min-width:48px; margin-left:3px; padding:2px 5px !important; transform:none !important; font-size:8.5px !important; line-height:1 !important; text-align:center !important; font-variant-numeric:tabular-nums; }
    #slide-20 .qvoice18-group-stats .qvoice18-attrition-pill.attr-low { color:#15803d !important; }
    #slide-20 .qvoice18-group-stats .qvoice18-attrition-pill.attr-mid { color:var(--accent) !important; }
    #slide-20 .qvoice18-group-stats .qvoice18-attrition-pill.attr-high { color:#c2410c !important; }
    #slide-20 .qvoice18-group-stats { gap:4px; }
    #slide-21 .retention-theme-row { grid-template-columns:minmax(180px,1.15fr) minmax(180px,2fr) minmax(170px,1.2fr); }
    #slide-21 .retention-theme-value { display:flex; align-items:center; justify-content:flex-end; gap:4px; min-width:0; font-size:10px; }
    #slide-21 .qvoice-inline-attrition-pill { flex:0 0 48px; }
    #slide-23 .qvoice-inline-attrition-row,
    #slide-24 .qvoice-inline-attrition-row { grid-template-columns:minmax(0,1fr) auto 96px; }
    #slide-25 .qvoice-inline-attrition-row,
    #slide-27 .qvoice-inline-attrition-row { grid-template-columns:minmax(0,1fr) auto 102px; }
    #slide-23 .qvoice-inline-attrition-panel,
    #slide-24 .qvoice-inline-attrition-panel,
    #slide-25 .qvoice-inline-attrition-panel,
    #slide-27 .qvoice-inline-attrition-panel { margin-top:7px; }
    #slide-23 .qvoice-inline-attrition-panel,
    #slide-25 .qvoice-inline-attrition-panel,
    #slide-27 .qvoice-inline-attrition-panel { padding-top:7px; padding-bottom:6px; }
    #slide-23 .qvoice-inline-attrition-row,
    #slide-25 .qvoice-inline-attrition-row,
    #slide-27 .qvoice-inline-attrition-row { min-height:18px; }
    #slide-23 .qvoice-inline-attrition-head strong,
    #slide-25 .qvoice-inline-attrition-head strong,
    #slide-27 .qvoice-inline-attrition-head strong { font-size:9.5px; }

    /* V7 navigation slide 19 / technical stage 21 - approved QVoice theme layout. */
    #slide-21 { grid-template-rows:auto 1fr; gap:8px; }
    #slide-21 .qv19-card { min-height:0; padding:16px 18px 12px; gap:10px; }
    #slide-21 .qv19-intro { display:grid; grid-template-columns:1.35fr 1fr; gap:12px; padding:10px 12px; border:1px solid var(--border-subtle); border-radius:12px; background:color-mix(in oklab,var(--bg-surface-2) 76%,transparent); }
    #slide-21 .qv19-intro-block { display:flex; flex-direction:column; gap:3px; min-width:0; }
    #slide-21 .qv19-eyebrow { color:var(--text-muted); font-size:10px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
    #slide-21 .qv19-intro strong { color:var(--text-main); font-size:13px; line-height:1.2; }
    #slide-21 .qv19-panel-head { display:flex; align-items:baseline; justify-content:space-between; gap:12px; border-bottom:2px solid var(--accent); padding:0 0 6px; }
    #slide-21 .qv19-panel-head strong { color:var(--text-main); font-size:13px; }
    #slide-21 .qv19-panel-head span { color:var(--text-muted); font-size:10px; white-space:nowrap; }
    #slide-21 .qv19-column-head,
    #slide-21 .qv19-row,
    #slide-21 .qv19-unpublishable { display:grid; grid-template-columns:250px minmax(0,1fr) 176px; gap:12px; align-items:center; }
    #slide-21 .qv19-column-head { padding:2px 0 4px; color:var(--text-muted); font-size:9px; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }
    #slide-21 .qv19-column-head span:last-child { text-align:right; }
    #slide-21 .qv19-list { display:grid; gap:8px; }
    #slide-21 .qv19-row { min-height:42px; }
    #slide-21 .qv19-label { color:var(--text-main); font-size:12px; font-weight:700; line-height:1.15; }
    #slide-21 .qv19-track { height:17px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    #slide-21 .qv19-fill { height:100%; min-width:4px; border-radius:inherit; background:linear-gradient(90deg,var(--accent-2),var(--accent)); }
    #slide-21 .qv19-distribution { color:var(--text-main); font-size:11px; font-weight:800; font-variant-numeric:tabular-nums; white-space:nowrap; }
    #slide-21 .qv19-attrition-cell { display:flex; align-items:center; justify-content:flex-end; gap:7px; min-width:0; }
    #slide-21 .qv19-attrition-pill { display:inline-flex; align-items:center; justify-content:center; min-width:52px; padding:4px 9px; border-radius:var(--radius-pill); border:1px solid color-mix(in oklab,var(--accent) 28%,transparent); background:color-mix(in oklab,var(--accent) 12%,transparent); color:var(--accent); font-size:11px; font-weight:900; font-variant-numeric:tabular-nums; white-space:nowrap; }
    #slide-21 .qv19-attrition-pill.attr-low { border-color:color-mix(in oklab,#22c55e 35%,transparent); background:color-mix(in oklab,#22c55e 13%,transparent); color:#15803d; }
    #slide-21 .qv19-attrition-pill.attr-high { border-color:color-mix(in oklab,#f97316 35%,transparent); background:color-mix(in oklab,#f97316 13%,transparent); color:#c2410c; }
    #slide-21 .qv19-unpublishable { margin-top:2px; padding:9px 10px; border:1px solid color-mix(in oklab,var(--accent) 28%,var(--border-subtle)); border-radius:10px; background:color-mix(in oklab,var(--accent) 7%,transparent); }
    #slide-21 .qv19-unpublishable strong { color:var(--text-main); font-size:11px; }
    #slide-21 .qv19-unpublishable span { color:var(--text-muted); font-size:9px; }
    #slide-21 .qv19-unpublishable b { color:var(--accent); font-size:11px; text-align:right; }
    #slide-21 .qv19-footer { display:flex; justify-content:space-between; gap:12px; padding-top:6px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:9.5px; line-height:1.2; }
    #slide-21 .qv19-footer strong { color:var(--text-main); }

    /* V7 QVoice slides 21–22 — three complete response/attrition cohorts.
       This replaces coverage bars and stored 0/1 panels with the approved
       Favorable / No favorable layout. */
    #slide-23 .qvoice-fu-card,
    #slide-24 .qvoice-fu-card { min-height:0; padding:15px 18px 12px; gap:10px; }
    #slide-23 .qvoice-fu-card-head,
    #slide-24 .qvoice-fu-card-head { flex:0 0 auto; padding-bottom:8px; border-bottom:1px solid var(--border-subtle); }
    #slide-23 .qvoice-fu-eyebrow,
    #slide-24 .qvoice-fu-eyebrow { margin:0 0 4px; color:var(--text-main); font-size:14px; font-weight:800; line-height:1.18; }
    #slide-23 .qvoice-fu-definition,
    #slide-24 .qvoice-fu-definition,
    #slide-23 .qvoice-fu-meta,
    #slide-24 .qvoice-fu-meta { margin:2px 0 0; color:var(--text-muted); font-size:10px; line-height:1.2; }
    #slide-23 .qvoice-fu-definition strong,
    #slide-24 .qvoice-fu-definition strong { color:var(--text-main); }
    #slide-23 .qvoice-fu-wave-grid,
    #slide-24 .qvoice-fu-wave-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); flex:1 1 auto; min-height:0; gap:12px; }
    #slide-23 .qvoice-fu-wave-card,
    #slide-24 .qvoice-fu-wave-card { display:flex; flex-direction:column; min-width:0; padding:12px 13px 10px; border:1px solid var(--border-subtle); border-radius:12px; background:color-mix(in oklab,var(--bg-surface-2) 72%,transparent); gap:7px; }
    #slide-23 .qvoice-fu-wave-head,
    #slide-24 .qvoice-fu-wave-head { display:flex; align-items:baseline; justify-content:space-between; gap:8px; padding-bottom:7px; border-bottom:1px solid var(--border-subtle); }
    #slide-23 .qvoice-fu-wave-head strong,
    #slide-24 .qvoice-fu-wave-head strong { color:var(--text-main); font-size:18px; line-height:1; }
    #slide-23 .qvoice-fu-wave-head span,
    #slide-24 .qvoice-fu-wave-head span { color:var(--text-muted); font-size:9px; font-weight:700; letter-spacing:.05em; text-transform:uppercase; }
    #slide-23 .qvoice-fu-response,
    #slide-24 .qvoice-fu-response { display:flex; flex:1 1 0; min-height:0; flex-direction:column; gap:4px; padding:6px 0; }
    #slide-23 .qvoice-fu-response + .qvoice-fu-response,
    #slide-24 .qvoice-fu-response + .qvoice-fu-response { border-top:1px solid color-mix(in oklab,var(--border-subtle) 76%,transparent); }
    #slide-23 .qvoice-fu-response-top,
    #slide-24 .qvoice-fu-response-top { display:flex; align-items:center; justify-content:space-between; gap:8px; color:var(--text-main); font-size:11px; line-height:1.1; }
    #slide-23 .qvoice-fu-response-top strong,
    #slide-24 .qvoice-fu-response-top strong { font-size:15px; font-variant-numeric:tabular-nums; }
    #slide-23 .qvoice-fu-response-label,
    #slide-24 .qvoice-fu-response-label { display:inline-flex; align-items:center; min-width:0; gap:5px; font-weight:750; }
    #slide-23 .qvoice-fu-dot,
    #slide-24 .qvoice-fu-dot { display:inline-block; flex:0 0 auto; width:8px; height:8px; border-radius:50%; }
    #slide-23 .qvoice-fu-dot-favorable,
    #slide-24 .qvoice-fu-dot-favorable { background:var(--accent); }
    #slide-23 .qvoice-fu-dot-no-favorable,
    #slide-24 .qvoice-fu-dot-no-favorable { background:#D97706; }
    #slide-23 .qvoice-fu-track,
    #slide-24 .qvoice-fu-track { height:14px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:999px; background:var(--bg-surface-3); }
    #slide-23 .qvoice-fu-fill,
    #slide-24 .qvoice-fu-fill { display:block; min-width:2px; height:100%; border-radius:inherit; }
    #slide-23 .qvoice-fu-fill-favorable,
    #slide-24 .qvoice-fu-fill-favorable { background:linear-gradient(90deg,var(--accent),var(--accent-2)); }
    #slide-23 .qvoice-fu-fill-no-favorable,
    #slide-24 .qvoice-fu-fill-no-favorable { background:linear-gradient(90deg,#D97706,#F59E0B); }
    #slide-23 .qvoice-fu-attrition,
    #slide-24 .qvoice-fu-attrition { display:grid; grid-template-columns:minmax(0,1fr) auto; align-items:center; gap:4px 7px; margin-top:auto; }
    #slide-23 .qvoice-fu-period,
    #slide-24 .qvoice-fu-period { min-width:0; color:var(--text-muted); font-size:8.5px; line-height:1.1; }
    #slide-23 .qvoice-fu-attrition-pill,
    #slide-24 .qvoice-fu-attrition-pill { position:static !important; transform:none !important; display:inline-flex; align-items:center; justify-content:center; min-width:49px; padding:3px 5px; font-size:10px; line-height:1; font-variant-numeric:tabular-nums; }
    #slide-23 .qvoice-fu-cohort,
    #slide-24 .qvoice-fu-cohort { grid-column:1 / -1; color:var(--text-muted); font-size:8.5px; line-height:1; font-variant-numeric:tabular-nums; }
    #slide-23 .qvoice-fu-footer,
    #slide-24 .qvoice-fu-footer { display:grid; grid-template-columns:1.35fr 1.2fr .8fr; flex:0 0 auto; gap:8px 14px; margin:0; padding-top:8px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:8.5px; line-height:1.2; }
    #slide-23 .qvoice-fu-footer strong,
    #slide-24 .qvoice-fu-footer strong { color:var(--text-main); }
    /* V7 QVoice driver decomposition: one driver block plus one block per
       source question, each with its own two-category distribution and rate. */
    #slide-23 .qvoice-fu-segments,
    #slide-24 .qvoice-fu-segments { display:flex; flex-direction:column; min-height:0; gap:5px; overflow:hidden; }
    #slide-23 .qvoice-fu-segment,
    #slide-24 .qvoice-fu-segment { padding:5px 0 4px; border-bottom:1px solid color-mix(in oklab,var(--border-subtle) 78%,transparent); }
    #slide-23 .qvoice-fu-segment:last-child,
    #slide-24 .qvoice-fu-segment:last-child { border-bottom:0; }
    #slide-23 .qvoice-fu-driver,
    #slide-24 .qvoice-fu-driver { padding:6px 7px 5px; border:1px solid var(--border-strong); border-radius:8px; background:color-mix(in oklab,var(--accent-soft) 38%,transparent); }
    #slide-23 .qvoice-fu-segment-head,
    #slide-24 .qvoice-fu-segment-head { display:flex; align-items:baseline; justify-content:space-between; gap:5px; margin-bottom:2px; }
    #slide-23 .qvoice-fu-segment-head strong,
    #slide-24 .qvoice-fu-segment-head strong { min-width:0; color:var(--text-main); font-size:9px; line-height:1.1; font-weight:800; }
    #slide-23 .qvoice-fu-driver .qvoice-fu-segment-head strong,
    #slide-24 .qvoice-fu-driver .qvoice-fu-segment-head strong { font-size:10px; }
    #slide-23 .qvoice-fu-segment-head span,
    #slide-24 .qvoice-fu-segment-head span { flex:0 0 auto; color:var(--text-muted); font-size:7px; font-weight:700; text-transform:uppercase; letter-spacing:.03em; }
    #slide-23 .qvoice-fu-response,
    #slide-24 .qvoice-fu-response { flex:0 0 auto; min-height:0; gap:2px; padding:3px 0 2px; }
    #slide-23 .qvoice-fu-response + .qvoice-fu-response,
    #slide-24 .qvoice-fu-response + .qvoice-fu-response { border-top:1px solid color-mix(in oklab,var(--border-subtle) 62%,transparent); }
    #slide-23 .qvoice-fu-response-top,
    #slide-24 .qvoice-fu-response-top { font-size:9px; }
    #slide-23 .qvoice-fu-response-top strong,
    #slide-24 .qvoice-fu-response-top strong { font-size:12px; }
    #slide-23 .qvoice-fu-track,
    #slide-24 .qvoice-fu-track { height:9px; }
    #slide-23 .qvoice-fu-response-foot,
    #slide-24 .qvoice-fu-response-foot { display:flex; align-items:center; justify-content:space-between; gap:5px; min-height:14px; }
    #slide-23 .qvoice-fu-response-foot .qvoice-fu-cohort,
    #slide-24 .qvoice-fu-response-foot .qvoice-fu-cohort { color:var(--text-muted); font-size:7px; }
    #slide-23 .qvoice-fu-attrition-pill,
    #slide-24 .qvoice-fu-attrition-pill { min-width:39px; padding:2px 4px; font-size:8.5px; }
    #slide-23 .qvoice-fu-components-label,
    #slide-24 .qvoice-fu-components-label { padding:2px 0 0; color:var(--text-muted); font-size:7px; font-weight:800; letter-spacing:.05em; text-transform:uppercase; }
    #slide-23 .qvoice-fu-component,
    #slide-24 .qvoice-fu-component { padding-top:3px; }
    #slide-23 .qvoice-fu-wave-card,
    #slide-24 .qvoice-fu-wave-card { gap:4px; }
    #slide-23 .qvoice-fu-wave-head,
    #slide-24 .qvoice-fu-wave-head { padding-bottom:5px; }
    @media (max-width:900px) {
      .qvoice-inline-attrition-row { grid-template-columns:minmax(0,1fr) auto; }
      .qvoice-inline-attrition-cohort { grid-column:1 / -1; text-align:left; }
    }
'''


def script_block(evidence: dict[str, Any]) -> str:
    evidence_json = json.dumps(evidence["rows"], ensure_ascii=False, separators=(",", ":"))
    return f'''

  <!-- V7 IOS MOVEMENT REASON SCRIPT -->
  <script>
    (function () {{
      var iosMovementRows = {evidence_json};
      var groupOrder = {json.dumps(list(GROUP_KEYS))};
      var years = {json.dumps(list(YEARS))};
      var slide = document.getElementById('slide-5');
      var chart = document.getElementById('ios-movement-reason-ytd-chart');

      function visible() {{
        return Boolean(slide) && window.getComputedStyle(slide).display !== 'none';
      }}

      function mix(surface, accent, weight) {{
        var hex = function (value) {{
          var text = String(value || '').trim().replace(/^#/, '');
          if (text.length === 3) text = text.split('').map(function (part) {{ return part + part; }}).join('');
          if (!/^[0-9a-f]{{6}}$/i.test(text)) return null;
          return [parseInt(text.slice(0, 2), 16), parseInt(text.slice(2, 4), 16), parseInt(text.slice(4, 6), 16)];
        }};
        var base = hex(surface), highlight = hex(accent);
        if (!base || !highlight) return accent;
        return 'rgb(' + base.map(function (value, index) {{ return Math.round(value + (highlight[index] - value) * weight); }}).join(',') + ')';
      }}

      function themeColors() {{
        var styles = getComputedStyle(document.body);
        return {{
          surface: styles.getPropertyValue('--bg-surface').trim() || '#ffffff',
          text: styles.getPropertyValue('--text-main').trim() || '#0f172a',
          muted: styles.getPropertyValue('--text-muted').trim() || '#5b6478',
          accent: styles.getPropertyValue('--accent').trim() || '#2457ff',
          accent2: styles.getPropertyValue('--accent-2').trim() || '#3b82f6',
          border: styles.getPropertyValue('--border-subtle').trim() || 'rgba(15,23,42,0.08)',
          font: 'Aptos, "Segoe UI", system-ui, -apple-system, sans-serif'
        }};
      }}

      function renderIOSMovementChart() {{
        if (!chart || !visible()) return;
        if (!window.Plotly) {{
          chart.innerHTML = '<p class="chart-note">The interactive chart could not load. The cohort and attrition table below remains available.</p>';
          return;
        }}
        var byKey = new Map(iosMovementRows.map(function (row) {{ return [row.calendar_year + '|' + row.group_key, row]; }}));
        var colors = themeColors();
        var palette = [mix(colors.surface, colors.accent, 0.58), colors.accent2, colors.accent];
        var labels = groupOrder.map(function (groupKey) {{
          var row = byKey.get('2024|' + groupKey);
          return row.short_label.replace(' / ', '<br>');
        }});
        var traces = years.map(function (year, index) {{
          var yearRows = groupOrder.map(function (groupKey) {{ return byKey.get(year + '|' + groupKey); }});
          return {{
            type: 'bar',
            name: String(year),
            x: labels,
            y: yearRows.map(function (row) {{ return row.workforce_share_percent; }}),
            customdata: yearRows.map(function (row) {{ return [row.cohort_n, row.post_event_voluntary_attrition_percent, row.cutoff_date, row.group_label, row.publication_status]; }}),
            text: yearRows.map(function (row) {{ return row.workforce_share_percent === null ? '' : row.workforce_share_percent.toFixed(1) + '%'; }}),
            texttemplate: '%{{text}}',
            textposition: 'auto',
            insidetextanchor: 'middle',
            insidetextfont: {{ family: colors.font, size: 10, color: '#ffffff' }},
            outsidetextfont: {{ family: colors.font, size: 10, color: colors.text }},
            marker: {{ color: palette[index], line: {{ color: colors.surface, width: 1 }} }},
            hovertemplate: '<b>%{{customdata[3]}}</b><br>' + year + ' through %{{customdata[2]}}<br>Workforce share: <b>%{{y:.1f}}%</b><br>Cohort: n=%{{customdata[0]:,}}<br>Observed voluntary attrition: %{{customdata[1]:.1f}}%<extra></extra>'
          }};
        }});
        Plotly.react(chart, traces, {{
          height: 205,
          barmode: 'group',
          bargap: 0.22,
          bargroupgap: 0.08,
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          font: {{ family: colors.font, color: colors.text }},
          margin: {{ t: 30, r: 8, b: 54, l: 48 }},
          legend: {{ orientation: 'h', x: 0, y: 1.18, font: {{ family: colors.font, size: 11, color: colors.text }} }},
          xaxis: {{ tickfont: {{ family: colors.font, size: 10, color: colors.muted }}, fixedrange: true, showgrid: false, tickangle: 0 }},
          yaxis: {{ title: {{ text: 'Share of average active regular workforce', font: {{ family: colors.font, size: 10, color: colors.muted }} }}, range: [0, 18], tickvals: [0, 5, 10, 15], ticksuffix: '%', tickfont: {{ family: colors.font, size: 10, color: colors.muted }}, gridcolor: colors.border, zeroline: true, zerolinecolor: colors.border, fixedrange: true }},
          hoverlabel: {{ font: {{ family: colors.font }} }}
        }}, {{ responsive: false, displayModeBar: false }});
      }}

      renderIOSMovementChart();
      var scheduleRender = function () {{ window.requestAnimationFrame(renderIOSMovementChart); }};
      new MutationObserver(function (records) {{
        if (records.some(function (record) {{ return record.attributeName === 'class'; }})) scheduleRender();
      }}).observe(document.body, {{ attributes: true, attributeFilter: ['class'] }});
      if (slide) new MutationObserver(scheduleRender).observe(slide, {{ attributes: true, attributeFilter: ['style'] }});
      window.addEventListener('resize', scheduleRender);
    }})();
  </script>
'''


def replace_slide(deck: str, slide: str) -> str:
    pattern = r'\s*<div class="slide-stage" id="slide-5".*?(?=\n\s*<div class="slide-stage" id="slide-6")'
    updated, replacements = re.subn(pattern, "\n" + slide, deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate exactly one V6 slide 5 block.")
    return updated


def remove_old_transfer_script(deck: str) -> str:
    pattern = r'\s*<script>\s*\(function \(\) \{\s*var transferRows =.*?</script>'
    updated, replacements = re.subn(pattern, "\n", deck, count=1, flags=re.S)
    require(replacements == 1, "Could not remove the obsolete V6 transfer-chart script.")
    return updated


def flatten_application_trend(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    flattened = []
    for item in evidence["trend"]:
        flattened.append(
            {
                "snapshot_date": item["snapshot_date"],
                "fiscal_year": item["fiscal_year"],
                "eligible_employee_snapshots": item["eligible_employee_snapshots"],
                "coverage_percent": item["coverage_percent"],
                "unknown_percent": item["unknown_percent"],
                "zero_percent": item["buckets"]["0"]["percent_of_eligible_snapshots"],
                "one_percent": item["buckets"]["1"]["percent_of_eligible_snapshots"],
                "two_plus_percent": item["buckets"]["2+"]["percent_of_eligible_snapshots"],
                "publication_status": "internal_analysis_exception",
            }
        )
    return flattened


def build_application_snapshot_slide(evidence: dict[str, Any]) -> str:
    colors = {"0": "var(--accent)", "1": "#0F766E", "2+": "#B45309"}
    descriptions = {"0": "No unique requisition", "1": "One unique requisition", "2+": "Two or more unique requisitions"}
    by_bucket = {row["application_bucket"]: row for row in evidence["latest_distribution"]}
    eligible = int(by_bucket["0"]["eligible_employee_snapshots"])
    unknown_count = int(by_bucket["Unknown"]["employee_snapshots"])
    unknown_pct = float(by_bucket["Unknown"]["percent_of_eligible_snapshots"])
    coverage_pct = float(by_bucket["0"]["coverage_percent"])
    covered_count = eligible - unknown_count

    covered_rows = []
    for bucket_name in ("0", "1", "2+"):
        row = by_bucket[bucket_name]
        pct = float(row["percent_of_eligible_snapshots"])
        count = int(row["employee_snapshots"])
        width = min(100.0, pct * 10.0)
        covered_rows.append(
            '<div class="application-covered-row">'
            f'<div class="application-covered-label">{html.escape(bucket_name)}<span>{html.escape(descriptions[bucket_name])}</span></div>'
            f'<div class="application-covered-track" title="{pct:.2f}% of all eligible employees; n={count:,}">'
            f'<div class="application-covered-fill" style="width:{width:.4f}%;background:{colors[bucket_name]}"></div></div>'
            f'<div class="application-covered-value">{pct:.2f}%<span>n={count:,}</span></div></div>'
        )

    trend_rows = evidence["trend"]
    month_bars = []
    for item in trend_rows:
        snapshot = date.fromisoformat(item["snapshot_date"])
        coverage = float(item["coverage_percent"])
        unknown = float(item["unknown_percent"])
        total = int(item["eligible_employee_snapshots"])
        label = snapshot.strftime("%b")
        tooltip = (
            f'{snapshot.isoformat()}: {coverage:.2f}% covered, {unknown:.2f}% Unknown; '
            f'n={total:,} eligible employee-snapshots'
        )
        month_bars.append(
            f'<div class="application-history-month" title="{html.escape(tooltip)}" aria-label="{html.escape(tooltip)}">'
            '<div class="application-history-rail">'
            f'<div class="application-history-unknown" style="height:{unknown:.4f}%"></div>'
            f'<div class="application-history-covered" style="height:{coverage:.4f}%"></div>'
            f'</div><span>{label}</span></div>'
        )

    first = trend_rows[0]
    last = trend_rows[-1]
    unknown_values = [float(item["unknown_percent"]) for item in trend_rows]
    return (
        '  <div class="slide-stage" id="slide-4" data-v6-playbook="true" data-v7-application-coverage="true">'
        '<div class="slide-heading"><div><h2 class="slide-title-text">Applied to a job — trailing six months</h2>'
        '<p class="slide-subtitle">Application coverage is incomplete, so employees without reliable coverage remain Unknown</p>'
        '</div><span class="badge badge-neutral">Distribution</span></div>'
        '<article class="card card-full application-coverage-story">'
        '<div class="application-coverage-meta">'
        '<span><strong>Definition:</strong> applications observed in the trailing six months; unreliable coverage remains Unknown.</span>'
        '<span><strong>Population:</strong> active regular employees, excluding RF360</span></div>'
        '<section class="application-coverage-hero">'
        f'<div class="application-coverage-hero-head"><span>Latest snapshot · {html.escape(evidence["latest_snapshot"])}</span><span>{eligible:,} eligible employee-snapshots</span></div>'
        '<div class="application-coverage-rail" aria-label="Latest application-feed coverage">'
        f'<div class="application-coverage-segment application-coverage-covered" style="width:{coverage_pct:.4f}%">{coverage_pct:.2f}% covered</div>'
        f'<div class="application-coverage-segment application-coverage-unknown" style="width:{unknown_pct:.4f}%">{unknown_pct:.2f}% Unknown</div></div>'
        f'<div class="application-coverage-counts" style="grid-template-columns:{coverage_pct:.4f}fr {unknown_pct:.4f}fr"><span>n={covered_count:,}</span><span>n={unknown_count:,}</span></div>'
        '</section><div class="application-coverage-lower">'
        '<article class="card chart-card application-covered-card"><div class="v6-panel-heading">'
        f'<span>What the covered {coverage_pct:.2f}% contains</span><span>Scale: 0–10% of all eligible</span></div>'
        '<div class="application-covered-list">' + "".join(covered_rows) + '</div></article>'
        '<article class="card chart-card application-history-card"><div class="v6-panel-heading">'
        '<span>Coverage stayed limited</span><span>12 complete snapshots</span></div>'
        '<div class="application-history-summary">'
        f'<span><strong>{float(first["unknown_percent"]):.2f}%</strong>Unknown · Sep 2025</span>'
        f'<span><strong>{min(unknown_values):.2f}%–{max(unknown_values):.2f}%</strong>12-month Unknown range</span>'
        f'<span><strong>{float(last["unknown_percent"]):.2f}%</strong>Unknown · Aug 2026</span></div>'
        '<div class="application-history-bars">' + "".join(month_bars) + '</div></article></div>'
        '<div class="application-coverage-note"><strong>Internal analysis:</strong> all aggregate buckets remain available, including the sub-30 2+ bucket under the named V7 authorization. No employee-level rows are shown.</div>'
        '<div class="application-visual-source"><strong>Source:</strong> HRDA · hrda.job_applications_vw + hrda.post_hire_monthly_worker_dtls.</div>'
        '</article></div>'
    )


def update_application_snapshot_content(deck: str, evidence: dict[str, Any]) -> str:
    pattern = r'\s*<div class="slide-stage" id="slide-4".*?(?=\n\s*<div class="slide-stage" id="slide-5")'
    updated, replacements = re.subn(pattern, "\n" + build_application_snapshot_slide(evidence), deck, count=1, flags=re.S)
    require(replacements == 1, "Could not replace the V7 application snapshot slide.")
    payload = json.dumps(flatten_application_trend(evidence), ensure_ascii=False, separators=(",", ":"))
    updated, replacements = re.subn(r'var applicationSnapshotTrend = \[.*?\];', f'var applicationSnapshotTrend = {payload};', updated, count=1, flags=re.S)
    require(replacements == 1, "Could not update the V7 application snapshot trend data.")
    return updated


def application_attrition_class(row: dict[str, Any], year_rows: list[dict[str, Any]]) -> str:
    rate = row["attrition_rate_percent"]
    if rate is None:
        return "attr-unavailable"
    rates = [
        float(item["attrition_rate_percent"])
        for item in year_rows
        if item["attrition_rate_percent"] is not None
    ]
    if not rates or len(set(rates)) == 1:
        return "attr-mid"
    if float(rate) == min(rates):
        return "attr-low"
    if float(rate) == max(rates):
        return "attr-high"
    return "attr-mid"


def application_attrition_cell(row: dict[str, Any], year_rows: list[dict[str, Any]]) -> str:
    distribution = f'{float(row["distribution_percent"]):.2f}% · n={int(row["distinct_applicants"]):,}'
    rate = row["attrition_rate_percent"]
    attrition_class = application_attrition_class(row, year_rows)
    if rate is None:
        reason = "12m follow-up incomplete" if row["followup_status"] != "complete_12m_followup" else "zero denominator"
        attrition = f'<span class="application-attrition-value {attrition_class}">Not estimable</span><small>{reason}</small>'
    else:
        attrition = (
            f'<span class="application-attrition-value {attrition_class}">{float(rate):.2f}% voluntary attrition</span>'
            f'<small>eligible n={int(row["attrition_eligible_applicants"]):,} · exits={int(row["voluntary_exits"]):,}</small>'
        )
    return (
        '<td><strong class="application-distribution-value">'
        + distribution
        + '</strong><div class="application-attrition-detail">'
        + attrition
        + '</div></td>'
    )


def build_application_attrition_slide(evidence: dict[str, Any]) -> str:
    rows_by_key = {(int(row["fiscal_year"]), str(row["application_bucket"])): row for row in evidence["rows"]}
    bucket_labels = {"1": "1 job", "2": "2 jobs", "3": "3 jobs", "4+": "4+ jobs"}
    recent_year_cards = []
    repeat_shares: dict[int, float] = {}
    for year in (2025, 2026):
        year_rows = [rows_by_key[(year, bucket)] for bucket in ("1", "2", "3", "4+")]
        label = "FY2026 YTD" if year == 2026 else "FY2025"
        period = "through 10 Sep" if year == 2026 else "full year"
        total_applicants = int(year_rows[0]["annual_distinct_applicants"])
        repeat_share = sum(float(row["distribution_percent"]) for row in year_rows if str(row["application_bucket"]) != "1")
        repeat_count = sum(int(row["distinct_applicants"]) for row in year_rows if str(row["application_bucket"]) != "1")
        repeat_shares[year] = repeat_share
        visual_rows = []
        for row in year_rows:
            bucket = str(row["application_bucket"])
            pct = float(row["distribution_percent"])
            count = int(row["distinct_applicants"])
            repeat_class = " is-repeat" if bucket != "1" else ""
            tooltip = (
                f"{label} · {bucket_labels[bucket]} · {pct:.2f}% of applicants · "
                f"n={count:,} · attrition Not estimable because 12-month follow-up is incomplete"
            )
            attrition_tooltip = (
                f"{label} · {bucket_labels[bucket]} · 12-month voluntary attrition is Not estimable "
                "because follow-up is incomplete"
            )
            visual_rows.append(
                '<div class="application-focus-row">'
                f'<div class="application-focus-label"><i class="application-focus-key{repeat_class}"></i>{bucket_labels[bucket]}</div>'
                f'<div class="application-focus-track" title="{html.escape(tooltip)}" aria-label="{html.escape(tooltip)}">'
                f'<div class="application-focus-fill{repeat_class}" style="width:{pct:.4f}%"></div></div>'
                f'<div class="application-focus-value"><strong>{pct:.2f}%</strong><span>n={count:,}</span></div>'
                f'<span class="application-focus-attrition v6-rate-pill attr-unavailable is-unavailable" title="{html.escape(attrition_tooltip)}" aria-label="{html.escape(attrition_tooltip)}">Not estimable</span></div>'
            )
        change_pill = ""
        if year == 2026:
            change_pill = (
                f'<span class="application-change-pill">+{repeat_share - repeat_shares[2025]:.2f} pp vs FY2025</span>'
            )
        recent_year_cards.append(
            f'<article class="application-focus-card{" is-current" if year == 2026 else ""}">'
            '<div class="application-focus-header">'
            f'<div class="application-focus-year"><strong>{label}</strong><span>n={total_applicants:,} applicants</span></div>'
            f'<span class="application-period-pill">{period}</span></div>'
            '<div class="application-repeat-hero"><div class="application-repeat-stat">'
            f'<strong>{repeat_share:.2f}%</strong><span>applied to 2+ jobs</span><small>n={repeat_count:,} applicants</small></div>'
            f'{change_pill}</div>'
            '<div class="application-focus-list">' + "".join(visual_rows) + '</div></article>'
        )

    chart_rows = []
    for year in (2022, 2023, 2024, 2025, 2026):
        items = []
        for bucket in ("1", "2", "3", "4+"):
            row = rows_by_key[(year, bucket)]
            items.append(
                {
                    "label": bucket,
                    "count": int(row["distinct_applicants"]),
                    "percent": float(row["distribution_percent"]),
                    "attrition_rate_percent": row["attrition_rate_percent"],
                }
            )
        chart_rows.append({"fiscal_year": "FY2026 YTD" if year == 2026 else f"FY{year}", "buckets": items})
    return (
        '  <div class="slide-stage" id="slide-3" data-v6-playbook="true" data-v7-application-attrition="true">'
        '<div class="slide-heading"><div><h2 class="slide-title-text">Applicants applying to 2+ jobs more than doubled in FY2026 YTD</h2>'
        '<p class="slide-subtitle">FY2025 full year vs FY2026 through 10 Sep · share of linked applicants by unique internal requisitions</p>'
        '</div><span class="badge badge-info">Distribution + 12-month attrition</span></div>'
        '<article class="card card-full application-visual-story">'
        '<div class="application-focus-years">' + "".join(recent_year_cards) + '</div>'
        '<div class="application-followup-band"><strong>Attrition labels:</strong>'
        '<span>12-month voluntary attrition is Not estimable for all eight rows because both periods still have incomplete follow-up.</span></div>'
        '<div class="application-visual-source"><strong>Source:</strong> HRDA · application records and workforce snapshots · cutoff 10 Sep 2026 · internal aggregate analysis.</div>'
        '</article></div>'
    ), chart_rows


def trailing_august_attrition_class(row: dict[str, Any], year_rows: list[dict[str, Any]]) -> str:
    rate = float(row["trailing_12m_voluntary_attrition_percent"])
    rates = [float(item["trailing_12m_voluntary_attrition_percent"]) for item in year_rows]
    if len(set(rates)) == 1:
        return "attr-mid"
    if rate == min(rates):
        return "attr-low"
    if rate == max(rates):
        return "attr-high"
    return "attr-mid"


def application_coverage_context(evidence: dict[str, Any]) -> tuple[str, float]:
    """Render the one coverage measure retained after the standalone slide is removed."""
    by_bucket = {str(row["application_bucket"]): row for row in evidence["latest_distribution"]}
    covered = by_bucket["0"]
    unknown = by_bucket["Unknown"]
    coverage_pct = float(covered["coverage_percent"])
    unknown_pct = float(unknown["unknown_percent"])
    eligible = int(covered["eligible_employee_snapshots"])
    covered_count = int(covered["observed_employee_snapshots"])
    unknown_count = int(unknown["employee_snapshots"])
    snapshot = str(evidence["latest_snapshot"])
    require(abs(coverage_pct + unknown_pct - 100.0) < 0.001, "Application coverage must reconcile to Unknown.")
    require(covered_count + unknown_count == eligible, "Application coverage counts must reconcile to eligible snapshots.")
    markup = (
        '<section class="application-coverage-context" aria-label="Application-feed coverage context">'
        '<div class="application-coverage-context-head"><strong>Application-feed coverage</strong>'
        f'<span>{html.escape(snapshot)} · {eligible:,} active regular employee-snapshots</span></div>'
        '<div class="application-coverage-rail" aria-label="Applications observed for a limited share of active regular employee-snapshots">'
        f'<div class="application-coverage-segment application-coverage-covered" style="width:{coverage_pct:.4f}%">{coverage_pct:.2f}% covered</div>'
        f'<div class="application-coverage-segment application-coverage-unknown" style="width:{unknown_pct:.4f}%">{unknown_pct:.2f}% Unknown</div></div>'
        f'<div class="application-coverage-counts" style="grid-template-columns:{coverage_pct:.4f}fr {unknown_pct:.4f}fr"><span>n={covered_count:,}</span><span>n={unknown_count:,}</span></div>'
        '<div class="application-coverage-caveat">Coverage is data availability, not the percentage of employees seeking a role.</div>'
        '</section>'
    )
    return markup, coverage_pct


def build_application_trailing_august_attrition_slide(
    evidence: dict[str, Any],
    application_evidence: dict[str, Any] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    rows_by_key = {(int(row["cutoff_year"]), str(row["application_bucket"])): row for row in evidence["rows"]}
    bucket_labels = {"1": "1 job", "2": "2 jobs", "3": "3 jobs", "4+": "4+ jobs"}
    coverage_context = ""
    coverage_headline = ""
    if application_evidence is not None:
        coverage_context, coverage_pct = application_coverage_context(application_evidence)
        coverage_headline = f'; application coverage is {coverage_pct:.2f}%'

    recent_year_cards = []
    repeat_shares: dict[int, float] = {}
    for year in (2025, 2026):
        year_rows = [rows_by_key[(year, bucket)] for bucket in ("1", "2", "3", "4+")]
        cutoff_date = date.fromisoformat(str(year_rows[0]["august_cutoff_date"]))
        total_applicants = int(year_rows[0]["total_distinct_applicants"])
        repeat_count = sum(int(row["distinct_applicant_count"]) for row in year_rows if str(row["application_bucket"]) != "1")
        repeat_share = 100 * repeat_count / total_applicants
        repeat_shares[year] = repeat_share
        label = f"Aug {year}"
        period = f"trailing 12m ending {cutoff_date.strftime('%d %b %Y')}"
        visual_rows = []
        for row in year_rows:
            bucket = str(row["application_bucket"])
            count = int(row["distinct_applicant_count"])
            pct = 100 * count / total_applicants
            exits = int(row["voluntary_exit_count"])
            rate = float(row["trailing_12m_voluntary_attrition_percent"])
            attrition_class = trailing_august_attrition_class(row, year_rows)
            repeat_class = " is-repeat" if bucket != "1" else ""
            small_base_class = " is-small-base" if count < 30 else ""
            small_base_marker = "*" if count < 30 else ""
            tooltip = (
                f"{label} - {bucket_labels[bucket]} - {pct:.2f}% of applicants - "
                f"n={count:,} - {rate:.2f}% observed voluntary attrition - {exits:,} exits"
            )
            visual_rows.append(
                '<div class="application-focus-row">'
                f'<div class="application-focus-label"><i class="application-focus-key{repeat_class}"></i>{bucket_labels[bucket]}</div>'
                f'<div class="application-focus-track" title="{html.escape(tooltip)}" aria-label="{html.escape(tooltip)}">'
                f'<div class="application-focus-fill{repeat_class}" style="width:{pct:.4f}%"></div></div>'
                f'<div class="application-focus-value"><strong>{pct:.2f}%</strong><span>n={count:,}</span></div>'
                f'<span class="application-focus-attrition v6-rate-pill {attrition_class}{small_base_class}" title="{html.escape(tooltip)}" aria-label="{html.escape(tooltip)}">{rate:.2f}%{small_base_marker}</span></div>'
            )
        change_pill = ""
        if year == 2026:
            change_pill = f'<span class="application-change-pill">+{repeat_share - repeat_shares[2025]:.2f} pp vs Aug 2025</span>'
        recent_year_cards.append(
            f'<article class="application-focus-card{" is-current" if year == 2026 else ""}">'
            '<div class="application-focus-header">'
            f'<div class="application-focus-year"><strong>{label}</strong><span>n={total_applicants:,} applicants</span></div>'
            f'<span class="application-period-pill">{period}</span></div>'
            '<div class="application-repeat-hero"><div class="application-repeat-stat">'
            f'<strong>{repeat_share:.2f}%</strong><span>applied to 2+ jobs</span><small>n={repeat_count:,} applicants</small></div>'
            f'{change_pill}</div>'
            '<div class="application-focus-keyline"><span>Share of applicants</span><span>Observed T12 attrition</span></div>'
            '<div class="application-focus-list">' + "".join(visual_rows) + '</div></article>'
        )

    chart_rows = []
    for year in (2022, 2023, 2024, 2025, 2026):
        items = []
        for bucket in ("1", "2", "3", "4+"):
            row = rows_by_key[(year, bucket)]
            count = int(row["distinct_applicant_count"])
            total = int(row["total_distinct_applicants"])
            items.append(
                {
                    "label": bucket,
                    "count": count,
                    "percent": round(100 * count / total, 2),
                    "attrition_rate_percent": float(row["trailing_12m_voluntary_attrition_percent"]),
                }
            )
        chart_rows.append({"fiscal_year": f"Aug {year}", "buckets": items})

    slide = (
        '  <div class="slide-stage" id="slide-3" data-v6-playbook="true" data-v7-application-attrition="true">'
        '<div class="slide-heading"><div><h2 class="slide-title-text">Repeat applications more than doubled'
        + coverage_headline
        + '</h2><p class="slide-subtitle">Trailing 12-month application windows ending at August cutoffs - share of linked applicants by unique internal requisitions</p>'
        + '</div><span class="badge badge-info">Distribution + observed attrition</span></div>'
        + '<article class="card card-full application-visual-story">'
        + coverage_context
        + '<div class="application-focus-years">'
        + "".join(recent_year_cards)
        + '</div><div class="application-followup-band"><strong>Attrition labels:</strong>'
        + '<span>observed voluntary attrition in the same trailing 12-month window; not prospective follow-up. * n&lt;30: descriptive only.</span></div>'
        + '<div class="application-visual-source"><strong>Source:</strong> HRDA - linked application records and workforce terminations - latest cutoff 23 Aug 2026 - internal aggregate analysis.</div>'
        + '</article></div>'
    )
    return slide, chart_rows


def update_application_intensity_content(
    deck: str,
    evidence: dict[str, Any],
    application_evidence: dict[str, Any],
) -> str:
    slide, chart_rows = build_application_trailing_august_attrition_slide(evidence, application_evidence)
    pattern = r'\s*<div class="slide-stage" id="slide-3".*?(?=\n\s*<div class="slide-stage" id="slide-4")'
    updated, replacements = re.subn(pattern, "\n" + slide, deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the V7 application-intensity slide.")
    payload = json.dumps(chart_rows, ensure_ascii=False, separators=(",", ":"))
    updated, replacements = re.subn(r'var chartData = \[.*?\];', f'var chartData = {payload};', updated, count=1, flags=re.S)
    require(replacements == 1, "Could not update the annual application chart data.")
    return updated


def update_team_attrition_wording(deck: str) -> str:
    pattern = r'(<div class="slide-stage" id="slide-8".*?)(?=\n\s*<div class="slide-stage" id="slide-9")'

    def replace_stage(match: re.Match[str]) -> str:
        stage = match.group(1)
        stage, replacements = re.subn(r'(<h2 class="slide-title-text">)Team turnover(</h2>)', r'\1Team attrition\2', stage, count=1)
        require(replacements == 1, "Could not rename the Team turnover slide title.")
        stage, replacements = re.subn(r'six-month equivalent<br/>voluntary turnover', 'six-month equivalent<br/>voluntary attrition', stage, count=2)
        require(replacements == 2, "Could not rename the Team turnover rate labels.")
        return stage

    updated, replacements = re.subn(pattern, replace_stage, deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the V7 team-turnover slide.")
    updated, replacements = re.subn(
        r'(<button class="nav-pill" data-slide="7">8\.) Team turnover(</button>)',
        r'\1 Team attrition\2',
        updated,
        count=1,
    )
    require(replacements == 1, "Could not rename the Team turnover navigation item.")
    return updated


def restore_internal_gender_labels(deck: str, evidence: dict[str, Any]) -> str:
    """Restore validated stored gender labels for the authorized internal deck."""
    mapping = evidence["display_mapping"]
    pattern = r'(<div class="slide-stage" id="slide-13".*?)(?=\n\s*<div class="slide-stage" id="slide-14")'

    def replace_stage(match: re.Match[str]) -> str:
        stage = match.group(1)
        replacements = (
            (
                "Protected categories remain anonymized for aggregate fairness review",
                "Stored gender values are visible for aggregate internal fairness review",
            ),
            ("Stored anonymized codes", "Stored gender values"),
            (
                f'title="Category A">Category A</div>',
                f'title="{html.escape(mapping["Category A"])}">{html.escape(mapping["Category A"])}</div>',
            ),
            (
                f'title="Category B">Category B</div>',
                f'title="{html.escape(mapping["Category B"])}">{html.escape(mapping["Category B"])}</div>',
            ),
        )
        for source, target in replacements:
            require(stage.count(source) == 1, f"Gender slide must contain exactly one occurrence of {source!r}.")
            stage = stage.replace(source, target, 1)
        return stage

    updated, replacements = re.subn(pattern, replace_stage, deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the V7 Gender slide.")
    return updated


def matching_tag_end(fragment: str, tag: str, start: int) -> int:
    """Return the end offset of a balanced HTML tag in a known slide fragment."""
    token = re.compile(rf"</?{re.escape(tag)}\b[^>]*>", re.I)
    depth = 0
    for match in token.finditer(fragment, start):
        if match.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                return match.end()
        else:
            depth += 1
    raise ValueError(f"Unbalanced <{tag}> tag while rebuilding work arrangement.")


def article_with_class(fragment: str, required_class: str) -> str:
    """Return one complete article that has the requested exact CSS class."""
    for match in re.finditer(r"<article\b(?P<attributes>[^>]*)>", fragment, re.I):
        class_match = re.search(r'\bclass="(?P<classes>[^"]*)"', match.group("attributes"), re.I)
        classes = class_match.group("classes").split() if class_match else []
        if required_class in classes:
            return fragment[match.start() : matching_tag_end(fragment, "article", match.start())]
    raise ValueError(f"Could not find the work-arrangement card {required_class!r}.")


def bar_row_with_label(card: str, required_label: str) -> str:
    """Return one complete horizontal bar row using its stored visible label."""
    row_pattern = re.compile(r'<div\b[^>]*\bclass="[^"]*\bbar-row\b[^"]*"[^>]*>', re.I)
    label_pattern = re.compile(
        r'<div\b[^>]*\bclass="[^"]*\bbar-label\b[^"]*"[^>]*>(?P<label>.*?)</div>',
        re.I | re.S,
    )
    for match in row_pattern.finditer(card):
        row = card[match.start() : matching_tag_end(card, "div", match.start())]
        label_match = label_pattern.search(row)
        if not label_match:
            continue
        label = html.unescape(re.sub(r"<[^>]+>", "", label_match.group("label"))).strip()
        if label == required_label:
            return row
    raise ValueError(f"Could not find the work-arrangement row {required_label!r}.")


def displayed_distribution(row: str) -> tuple[int, float]:
    """Read the current distribution count and share from an inherited V6 row."""
    value_match = re.search(
        r'<div\b[^>]*\bclass="[^"]*\bbar-value\b[^"]*"[^>]*>(?P<value>[^<]+)',
        row,
        re.I,
    )
    if not value_match:
        raise ValueError("A work-arrangement row is missing its distribution value.")
    rendered = html.unescape(value_match.group("value")).strip()
    parsed = re.search(r"(?P<share>\d+(?:\.\d+)?)%\D+(?P<count>[\d,]+)", rendered)
    if not parsed:
        raise ValueError(f"Could not parse the work-arrangement distribution value {rendered!r}.")
    return int(parsed.group("count").replace(",", "")), float(parsed.group("share"))


def attrition_pill_class(rate: float, all_rates: list[float]) -> str:
    if rate == min(all_rates):
        return "attr-low"
    if rate == max(all_rates):
        return "attr-high"
    return "attr-mid"


def annual_rate_class(rate: float, all_rates: list[float]) -> str:
    """Keep a single published rate blue instead of simultaneously low/high."""
    return "attr-mid" if len(set(all_rates)) <= 1 else attrition_pill_class(rate, all_rates)


def compensation_grade_rate_class(rate: float, all_rates: list[float]) -> str:
    """Use low/middle/high relative bands so the long grade list is readable."""
    if len(set(all_rates)) <= 1:
        return "attr-mid"
    ordered = sorted(all_rates)
    low_threshold = ordered[len(ordered) // 3]
    high_threshold = ordered[(2 * len(ordered)) // 3]
    if rate <= low_threshold:
        return "attr-low"
    if rate >= high_threshold:
        return "attr-high"
    return "attr-mid"


def stage_fragment(deck: str, slide_number: int) -> str:
    pattern = rf'(<div class="slide-stage" id="slide-{slide_number}".*?)(?=\n\s*<div class="slide-stage"|\n\s*<script|\Z)'
    match = re.search(pattern, deck, flags=re.S)
    require(match is not None, f"Could not locate V7 slide {slide_number}.")
    return match.group(1)


def replace_stage_fragment(deck: str, slide_number: int, replacement: str) -> str:
    original = stage_fragment(deck, slide_number)
    require(deck.count(original) == 1, f"V7 slide {slide_number} is not uniquely replaceable.")
    return deck.replace(original, replacement, 1)


def replace_intro_slide_with_population_context(
    deck: str,
    layers_from_ceo_annual_attrition_evidence: dict[str, Any],
) -> str:
    """Make the cover self-explanatory for a non-technical audience."""
    metrics = layers_from_ceo_annual_attrition_evidence["metrics"]
    population = int(metrics["display_eligible_count"])
    voluntary_exits = int(metrics["baseline_voluntary_exits"])
    attrition_rate = 100 * voluntary_exits / population
    require(
        int(metrics["published_employee_count"]) == population,
        "Cover-population count must reconcile to the published manager-layer cohort.",
    )
    require(
        str(layers_from_ceo_annual_attrition_evidence["baseline_snapshot_date"]) == "2025-08-24"
        and str(layers_from_ceo_annual_attrition_evidence["outcome_cutoff_date"]) == "2026-08-23",
        "Cover attrition context must use the validated August trailing-12-month window.",
    )

    stage = f'''  <div class="slide-stage" id="slide-1" data-v7-intro-population-context="true">
      <div class="slide-heading"><div><h2 class="slide-title-text">Employee characteristics and attrition</h2><p class="slide-subtitle">How characteristics are distributed and how voluntary attrition differs across them</p></div><span class="badge badge-info">Internal analysis</span></div>
      <article class="card card-full v6-intro-card">
        <div class="v6-hero-copy"><h1>What may be related<br/>to voluntary attrition?</h1><p>We reviewed employee characteristics that may help explain or be related to voluntary attrition. Each slide shows how employees are distributed across categories and, where available, the voluntary attrition rate for each category. Most distributions show employees active in August 2026. Each slide states its own time period. These comparisons show patterns; they do not prove cause.</p></div>
        <div class="v6-intro-grid">
          <div><span class="v6-mini-label">Our workforce</span><strong>Employees with Regular status who were active at the date used for each slide.</strong></div>
          <div><span class="v6-mini-label">Voluntary attrition</span><strong>The percentage who chose to leave the company. Other types of departure are not included.</strong></div>
          <div><span class="v6-mini-label">2026 annual context</span><strong>{attrition_rate:.1f}% &middot; {voluntary_exits:,} employees chose to leave in the 12 months ending 23 Aug 2026.</strong></div>
          <div><span class="v6-mini-label">Why 2025 appears</span><strong>We start with {population:,} Regular employees active on 24 Aug 2025 and follow them to 23 Aug 2026.</strong></div>
        </div>
      </article>
    </div>'''
    return replace_stage_fragment(deck, 1, stage)


QVOICE_INTENT_DISPLAY_YEARS = ("2024", "2025", "2026")


def limit_qvoice_intent_display_to_recent_years(deck: str) -> str:
    """Keep only the requested 2024-2026 coverage bars on navigation slide 20.

    This is a presentation-window choice only. It does not alter the source
    workbook, the component mapping, or the underlying QVoice aggregates.
    """
    stage = stage_fragment(deck, 23)
    chart_start = stage.find('<div class="trend-chart"')
    require(chart_start >= 0, "Intent-to-Stay slide is missing its coverage chart.")
    chart_end = matching_tag_end(stage, "div", chart_start)
    chart = stage[chart_start:chart_end]
    wrappers: list[tuple[str, str]] = []
    for match in re.finditer(r'<div class="trend-bar-wrap">', chart):
        wrapper = chart[match.start() : matching_tag_end(chart, "div", match.start())]
        year_match = re.search(r'<div class="trend-label"><span>(\d{4})</span>', wrapper)
        require(year_match is not None, "Intent-to-Stay coverage bar is missing its year label.")
        wrappers.append((year_match.group(1), wrapper))
    require(wrappers, "Intent-to-Stay coverage chart has no bars.")
    selected = [wrapper for year, wrapper in wrappers if year in QVOICE_INTENT_DISPLAY_YEARS]
    selected_years = [year for year, _ in wrappers if year in QVOICE_INTENT_DISPLAY_YEARS]
    require(selected_years == list(QVOICE_INTENT_DISPLAY_YEARS), "Intent-to-Stay chart is missing a requested recent year.")

    opening_end = chart.find(">") + 1
    closing_start = chart.rfind("</div>")
    require(opening_end > 0 and closing_start > opening_end, "Intent-to-Stay coverage chart is malformed.")
    require(re.search(r"--bars:\d+", chart[:opening_end]) is not None, "Intent-to-Stay coverage chart is missing its bar-count style.")
    opening = re.sub(r"--bars:\d+", f"--bars:{len(selected)}", chart[:opening_end], count=1)
    filtered_chart = opening + "".join(selected) + chart[closing_start:]
    filtered_stage = stage[:chart_start] + filtered_chart + stage[chart_end:]
    for year in QVOICE_INTENT_DISPLAY_YEARS:
        require(f"<span>{year}</span>" in filtered_stage, f"Intent-to-Stay slide lost {year}.")
    for year, _ in wrappers:
        if year not in QVOICE_INTENT_DISPLAY_YEARS:
            require(f"<span>{year}</span>" not in filtered_chart, f"Intent-to-Stay slide still shows {year}.")
    return replace_stage_fragment(deck, 23, filtered_stage)


def load_promotion_track_evidence() -> dict[str, Any]:
    evidence = json.loads(PROMOTION_TRACK_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "Promotion-track evidence did not pass validation.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "Promotion-track evidence must be internal_analysis.")
    require(len(evidence.get("display_rows", [])) == 6, "Promotion-track evidence must contain six display tracks.")
    return evidence


def load_promotion_grade_top10_evidence() -> dict[str, Any]:
    evidence = json.loads(PROMOTION_GRADE_TOP10_EVIDENCE_FILE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "Top-10 compensation-grade evidence did not pass validation.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "Top-10 compensation-grade evidence must be internal_analysis.")
    require(len(evidence.get("top_grade_rows", [])) == 10, "Top-10 compensation-grade evidence must contain ten grades.")
    return evidence


def replace_promotion_track_slide(
    deck: str,
    evidence: dict[str, Any],
    top_grade_evidence: dict[str, Any],
) -> str:
    """Make the pay-track story part of every full V7 build."""
    updated = replace_stage_fragment(deck, 34, build_promotion_track_stage(evidence, top_grade_evidence))
    nav_pattern = re.compile(r'(<button class="nav-pill(?: pill-active)?" data-slide="28">).*?(</button>)', re.S)
    require(len(nav_pattern.findall(updated)) == 1, "The slide 29 navigation item is missing.")
    updated = nav_pattern.sub(r"\g<1>29. Promotion and attrition by pay track\g<2>", updated, count=1)
    updated = strip_promotion_track_css(updated)
    require("</style>" in updated, "The deck has no main style block for the promotion-track CSS.")
    return updated.replace("</style>", PROMOTION_TRACK_CSS + "\n</style>", 1)


def article_with_class_and_text(fragment: str, required_class: str, required_text: str) -> str:
    """Return one card selected by stable class and an existing visible heading."""
    for match in re.finditer(r"<article\b(?P<attributes>[^>]*)>", fragment, re.I):
        class_match = re.search(r'\bclass="(?P<classes>[^"]*)"', match.group("attributes"), re.I)
        classes = class_match.group("classes").split() if class_match else []
        if required_class not in classes:
            continue
        article = fragment[match.start() : matching_tag_end(fragment, "article", match.start())]
        if required_text in article:
            return article
    raise ValueError(f"Could not find card {required_class!r} containing {required_text!r}.")


def annual_rows_by_category(evidence: dict[str, Any], metric: str) -> dict[str, dict[str, Any]]:
    rows = [row for row in evidence["rows"] if str(row["metric"]) == metric]
    require(rows, f"Annual evidence is missing metric {metric!r}.")
    result = {str(row["category"]): row for row in rows}
    require(len(result) == len(rows), f"Annual evidence has duplicate categories for metric {metric!r}.")
    return result


def display_rows_by_category(evidence: dict[str, Any], metric: str) -> dict[str, dict[str, Any]]:
    rows = evidence["display_rows"].get(metric)
    require(isinstance(rows, list) and rows, f"Display evidence is missing metric {metric!r}.")
    result = {str(row["category"]): row for row in rows}
    require(len(result) == len(rows), f"Display evidence has duplicate categories for metric {metric!r}.")
    return result


def aggregate_annual_rows(rows: list[dict[str, Any]], category: str) -> dict[str, Any]:
    """Pool raw annual cohorts before calculating an Other-category rate."""
    require(rows, f"Cannot aggregate empty annual category {category!r}.")
    exposure = sum(int(row["employee_snapshot_count"]) for row in rows)
    exits = sum(int(row["voluntary_exits"]) for row in rows)
    return {
        "category": category,
        "employee_snapshot_count": exposure,
        "voluntary_exits": exits,
        "annual_attrition_rate_percent": 100 * exits / exposure if exposure else 0.0,
        "publication_status": "publishable" if exposure >= 30 and exits >= 30 else "not_estimable_below_aggregate_threshold",
    }


def annual_rate(row: dict[str, Any] | None) -> float | None:
    if row is None or str(row.get("publication_status")) != "publishable":
        return None
    return float(row["annual_attrition_rate_percent"])


def internal_annual_rate(row: dict[str, Any] | None) -> float | None:
    """Return an aggregate rate for explicitly authorized internal review.

    This does not change the evidence publication status or the shared-output
    n>=30 rule.  It only lets the named internal-analysis artifact display the
    already-reconciled aggregate rate for a subthreshold cohort.
    """
    if row is None:
        return None
    rate = row.get("annual_attrition_rate_percent")
    denominator = row.get("employee_count", row.get("baseline_employee_count", 0))
    if rate is None or int(denominator or 0) <= 0:
        return None
    return float(rate)


def annual_attrition_pill(
    label: str,
    row: dict[str, Any] | None,
    all_rates: list[float],
    *,
    unavailable_reason: str | None = None,
    unavailable_text: str = "Not estimable",
    extra_class: str = "",
    allow_internal_subthreshold: bool = False,
    rate_class_fn: Callable[[float, list[float]], str] = annual_rate_class,
) -> str:
    """Render one Location-style annual rate, or the explicit gray state."""
    rate = annual_rate(row)
    internal_small_cohort = False
    if rate is None and allow_internal_subthreshold:
        rate = internal_annual_rate(row)
        internal_small_cohort = rate is not None
    escaped_label = html.escape(label)
    if rate is None:
        reason = unavailable_reason or "the historical cohort does not meet the aggregate publication rule"
        return (
            '<span class="v7-annual-attrition v6-rate-pill attr-unavailable is-unavailable '
            + extra_class
            + '" title="Annual voluntary attrition is not estimable for '
            + escaped_label
            + ': '
            + html.escape(reason)
            + '" aria-label="Annual voluntary attrition for '
            + escaped_label
            + ': '
            + html.escape(unavailable_text)
            + '">'
            + html.escape(unavailable_text)
            + "</span>"
        )
    pill_class = rate_class_fn(rate, all_rates)
    small_cohort_class = " internal-small-cohort" if internal_small_cohort else ""
    if internal_small_cohort:
        denominator = int(row.get("employee_count", row.get("baseline_employee_count", 0)))
        exits = int(row.get("voluntary_exits", row.get("voluntary_exit_count", 0)))
        title = (
            f"Descriptive internal-analysis annual voluntary attrition for {label}: {rate:.1f}%; "
            f"baseline cohort n={denominator:,}; voluntary exits={exits:,}; below the shared-output n=30 threshold."
        )
    else:
        title = f"Annual voluntary attrition for {label}: {rate:.1f}%"
    display_rate = f"{rate:.1f}%*" if internal_small_cohort else f"{rate:.1f}%"
    return (
        '<span class="v7-annual-attrition v6-rate-pill '
        + pill_class
        + small_cohort_class
        + (' ' + extra_class if extra_class else '')
        + '" title="'
        + html.escape(title)
        + '" aria-label="'
        + html.escape(title)
        + '">'
        + display_rate
        + "</span>"
    )


def nav38_metric_rows(evidence: dict[str, Any], metric: str) -> dict[str, dict[str, Any]]:
    """Return normalized category rows from the three post-slide-38 queries."""
    if metric == "manager_observed_expected":
        rows = evidence["queries"]["manager_observed_expected"]["rows"]
    elif metric == "above_average_team_turnover":
        rows = evidence["queries"]["above_average_team_turnover"]["rows"]
    else:
        rows = [
            row
            for row in evidence["queries"]["simple_categories"]["rows"]
            if str(row.get("metric")) == metric
        ]
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("row_type") != "category":
            continue
        category = str(row["category"])
        result[category] = row
    if not result and metric not in {"manager_observed_expected", "above_average_team_turnover"}:
        # Legacy HTML and the saved SQL can carry different UTF-8/Latin-1
        # renderings of the middle-dot separator. Match the semantic metric
        # while keeping the original evidence text untouched.
        normalized_metric = re.sub(r"[^a-z0-9]+", "", metric.lower())
        for row in evidence["queries"]["simple_categories"]["rows"]:
            candidate = str(row.get("metric", ""))
            if row.get("row_type") == "category" and re.sub(r"[^a-z0-9]+", "", candidate.lower()) == normalized_metric:
                result[str(row["category"])] = row
    require(result, f"Slides 38+ evidence has no category rows for {metric!r}.")
    return result


def mojibake_variant(value: str) -> str:
    """Match legacy HTML labels that were UTF-8 decoded as Latin-1."""
    try:
        return value.encode("utf-8").decode("latin-1")
    except UnicodeError:
        return value


def nav38_card_mapping(card: str, rows_by_category: dict[str, dict[str, Any]], aliases: dict[str, str] | None = None) -> dict[str, dict[str, Any] | None]:
    """Map visible legacy labels to fresh evidence, including old mojibake."""
    aliases = aliases or {}
    mapping: dict[str, dict[str, Any] | None] = {}
    candidates = dict(rows_by_category)
    candidates.update({mojibake_variant(key): value for key, value in rows_by_category.items()})
    for visible_label in card_bar_labels(card):
        source_label = aliases.get(visible_label, visible_label)
        mapping[visible_label] = candidates.get(source_label)
        if mapping[visible_label] is None:
            mapping[visible_label] = candidates.get(mojibake_variant(source_label))
    return mapping


def remove_inherited_attrition_pills(fragment: str) -> str:
    """Drop any stale six-month or prior annual pill before inserting one rate."""
    return re.sub(
        r'<span\b[^>]*\bclass="[^"]*\b(?:v4-inline-attrition-rate|v7-annual-attrition)\b[^"]*"[^>]*>.*?</span>',
        "",
        fragment,
        flags=re.I | re.S,
    )


def add_annual_pill_to_bar_row(row: str, pill: str) -> str:
    """Append one annual pill without modifying the bar, distribution, or label."""
    updated = remove_inherited_attrition_pills(row)
    opening_match = re.match(r"<div\b[^>]*>", updated, re.I)
    require(opening_match is not None, "A bar row is missing its opening element.")
    opening = opening_match.group(0)
    class_match = re.search(r'\bclass="([^"]*)"', opening, re.I)
    require(class_match is not None and "bar-row" in class_match.group(1).split(), "A rate row must retain bar-row.")
    if "v4-inline-attrition-row" not in class_match.group(1).split():
        classes = class_match.group(1) + " v4-inline-attrition-row"
        opening = opening[: class_match.start(1)] + classes + opening[class_match.end(1) :]
        updated = opening + updated[opening_match.end() :]
    value_match = re.search(
        r'(<div\b[^>]*\bclass="[^"]*\bbar-value\b[^"]*"[^>]*>)(.*?)(</div>)',
        updated,
        flags=re.I | re.S,
    )
    require(value_match is not None, "A bar row is missing its distribution value.")
    replacement = value_match.group(1) + value_match.group(2).rstrip() + pill + value_match.group(3)
    return updated[: value_match.start()] + replacement + updated[value_match.end() :]


def update_bar_card_with_annual_attrition(
    card: str,
    label_to_row: dict[str, dict[str, Any] | None],
    *,
    unavailable_reasons: dict[str, str] | None = None,
    allow_internal_subthreshold: bool = False,
    rate_class_fn: Callable[[float, list[float]], str] = annual_rate_class,
) -> str:
    """Replace every row's inherited pill with validated annual attrition."""
    available_rates = []
    for row in label_to_row.values():
        rate = annual_rate(row)
        if rate is None and allow_internal_subthreshold:
            rate = internal_annual_rate(row)
        if rate is not None:
            available_rates.append(rate)
    require(available_rates, "An annual attrition card needs at least one published rate.")
    updated = card
    for label, evidence_row in label_to_row.items():
        original_row = bar_row_with_label(updated, label)
        pill = annual_attrition_pill(
            label,
            evidence_row,
            available_rates,
            unavailable_reason=(unavailable_reasons or {}).get(label),
            allow_internal_subthreshold=allow_internal_subthreshold,
            rate_class_fn=rate_class_fn,
        )
        replacement = add_annual_pill_to_bar_row(original_row, pill)
        updated = updated.replace(original_row, replacement, 1)
    updated = updated.replace("Distribution / 6-month attrition", "Distribution / annual attrition")
    updated = updated.replace("</span><span>Distribution</span>", "</span><span>Distribution / annual attrition</span>")
    return updated


def update_bar_card_with_unavailable_annual_attrition(
    card: str,
    reason: str,
    *,
    unavailable_text: str = "Not estimable",
    panel_subtitle: str = "Distribution / annual attrition",
) -> str:
    """Use an explicit gray annual state where no time-safe rate exists."""
    updated = card
    labels = []
    for match in re.finditer(r'<div\b[^>]*\bclass="[^"]*\bbar-label\b[^"]*"[^>]*>(?P<label>.*?)</div>', card, re.I | re.S):
        labels.append(html.unescape(re.sub(r"<[^>]+>", "", match.group("label"))).strip())
    require(labels, "The unavailable annual card has no bar rows.")
    for label in labels:
        original_row = bar_row_with_label(updated, label)
        replacement = add_annual_pill_to_bar_row(
            original_row,
            annual_attrition_pill(
                label,
                None,
                [],
                unavailable_reason=reason,
                unavailable_text=unavailable_text,
            ),
        )
        updated = updated.replace(original_row, replacement, 1)
    updated = updated.replace("</span><span>Distribution</span>", "</span><span>" + html.escape(panel_subtitle) + "</span>")
    return updated


def update_bar_card_distribution_and_annual_attrition(
    card: str,
    display_rows: dict[str, dict[str, Any]],
    annual_rows: dict[str, dict[str, Any]],
    *,
    heading: str,
    panel_subtitle: str = "Distribution / annual attrition",
) -> str:
    """Replace current counts and add a time-aligned annual rate to each row."""
    total = sum(int(row["employee_count"]) for row in display_rows.values())
    maximum = max(int(row["employee_count"]) for row in display_rows.values())
    require(total > 0 and maximum > 0, "A current tenure distribution is empty.")
    require(set(annual_rows) == set(display_rows), "Annual and display tenure bands do not reconcile.")
    available_rates = [annual_rate(row) for row in annual_rows.values() if annual_rate(row) is not None]
    require(available_rates, "An annual attrition card needs at least one published rate.")
    updated = card
    header_match = re.search(r'(<div class="v6-panel-heading"><span>).*?(</span><span>)', updated, flags=re.S)
    require(header_match is not None, "A tenure distribution card is missing its panel heading.")
    updated = updated[: header_match.start()] + header_match.group(1) + html.escape(heading) + header_match.group(2) + updated[header_match.end() :]
    for label in card_bar_labels(updated):
        require(label in display_rows, f"Display evidence is missing visible category {label!r}.")
        require(label in annual_rows, f"Annual evidence is missing visible category {label!r}.")
        count = int(display_rows[label]["employee_count"])
        original_row = bar_row_with_label(updated, label)
        stripped_row = remove_inherited_attrition_pills(original_row)
        fill_match = re.search(r'(<div class="bar-fill" style="width:)[^\"]*(")', stripped_row)
        require(fill_match is not None, "A tenure bar row is missing its bar fill.")
        filled_row = stripped_row[: fill_match.start()] + fill_match.group(1) + f"{100 * count / maximum:.1f}%" + fill_match.group(2) + stripped_row[fill_match.end() :]
        value_match = re.search(
            r'(<div\b[^>]*\bclass="[^"]*\bbar-value\b[^"]*"[^>]*>)(.*?)(</div>)',
            filled_row,
            flags=re.I | re.S,
        )
        require(value_match is not None, "A tenure bar row is missing its value.")
        base_row = filled_row[: value_match.start()] + value_match.group(1) + f"{round(100 * count / total)}% · {count:,}" + value_match.group(3) + filled_row[value_match.end() :]
        pill = annual_attrition_pill(label, annual_rows[label], [float(rate) for rate in available_rates])
        replacement = add_annual_pill_to_bar_row(base_row, pill)
        updated = updated.replace(original_row, replacement, 1)
    updated = updated.replace("</span><span>Distribution</span>", "</span><span>" + html.escape(panel_subtitle) + "</span>")
    return updated


def update_bar_card_distribution_and_unavailable_annual_attrition(
    card: str,
    rows_by_category: dict[str, dict[str, Any]],
    *,
    heading: str,
    unavailable_reason: str,
    unavailable_text: str,
    panel_subtitle: str = "Distribution / annual attrition",
) -> str:
    """Replace inherited counts with the validated current distribution."""
    total = sum(int(row["employee_count"]) for row in rows_by_category.values())
    maximum = max(int(row["employee_count"]) for row in rows_by_category.values())
    require(total > 0 and maximum > 0, "A current tenure distribution is empty.")
    updated = card
    header_match = re.search(r'(<div class="v6-panel-heading"><span>).*?(</span><span>)', updated, flags=re.S)
    require(header_match is not None, "A tenure distribution card is missing its panel heading.")
    updated = updated[: header_match.start()] + header_match.group(1) + html.escape(heading) + header_match.group(2) + updated[header_match.end() :]
    for label in card_bar_labels(updated):
        require(label in rows_by_category, f"Display evidence is missing visible category {label!r}.")
        evidence_row = rows_by_category[label]
        count = int(evidence_row["employee_count"])
        share = round(100 * count / total)
        original_row = bar_row_with_label(updated, label)
        stripped_row = remove_inherited_attrition_pills(original_row)
        fill_match = re.search(r'(<div class="bar-fill" style="width:)[^"]*(")', stripped_row)
        require(fill_match is not None, "A tenure bar row is missing its bar fill.")
        filled_row = stripped_row[: fill_match.start()] + fill_match.group(1) + f"{100 * count / maximum:.1f}%" + fill_match.group(2) + stripped_row[fill_match.end() :]
        value_match = re.search(
            r'(<div\b[^>]*\bclass="[^"]*\bbar-value\b[^"]*"[^>]*>)(.*?)(</div>)',
            filled_row,
            flags=re.I | re.S,
        )
        require(value_match is not None, "A tenure bar row is missing its value.")
        base_row = filled_row[: value_match.start()] + value_match.group(1) + f"{share}% · {count:,}" + value_match.group(3) + filled_row[value_match.end() :]
        pill = annual_attrition_pill(
            label,
            None,
            [],
            unavailable_reason=unavailable_reason,
            unavailable_text=unavailable_text,
        )
        replacement = add_annual_pill_to_bar_row(base_row, pill)
        updated = updated.replace(original_row, replacement, 1)
    updated = updated.replace("</span><span>Distribution</span>", "</span><span>" + html.escape(panel_subtitle) + "</span>")
    return updated


def set_stage_annual_badge(stage: str, text: str = "Annual attrition") -> str:
    heading_start = stage.find('<div class="slide-heading">')
    require(heading_start >= 0, "A slide is missing its heading.")
    heading_end = matching_tag_end(stage, "div", heading_start)
    heading = stage[heading_start:heading_end]
    updated_heading, replacements = re.subn(
        r'<span class="badge badge-(?:info|neutral)">.*?</span>',
        '<span class="badge badge-info">' + html.escape(text) + "</span>",
        heading,
        count=1,
        flags=re.S,
    )
    require(replacements == 1, "A slide heading is missing its badge.")
    return stage[:heading_start] + updated_heading + stage[heading_end:]


def card_bar_labels(card: str) -> list[str]:
    labels = []
    for match in re.finditer(r'<div\b[^>]*\bclass="[^"]*\bbar-label\b[^"]*"[^>]*>(?P<label>.*?)</div>', card, re.I | re.S):
        labels.append(html.unescape(re.sub(r"<[^>]+>", "", match.group("label"))).strip())
    require(labels, "A bar card has no labels.")
    return labels


def direct_bar_mapping(card: str, rows_by_category: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for label in card_bar_labels(card):
        require(label in rows_by_category, f"Annual evidence is missing visible category {label!r}.")
        mapping[label] = rows_by_category[label]
    return mapping


def replace_stage_source_with_annual_definition(stage: str, extra: str = "") -> str:
    source_match = re.search(r'<div class="v6-source-line">.*?</div>', stage, re.S)
    require(source_match is not None, "A slide is missing its source line.")
    replacement = (
        '<div class="v6-source-line"><strong>Source:</strong> HRDA - hrda.post_hire_monthly_worker_dtls. '
        'Annual attrition is a strict voluntary exit in the 12 months after the historical snapshot; '
        'aggregate internal-analysis result. '
        + html.escape(extra)
        + "</div>"
    )
    return stage[:source_match.start()] + replacement + stage[source_match.end():]


def replace_stage_source_with_trailing_12m_definition(stage: str, extra: str = "") -> str:
    """Replace a source line for fiscal-year-end, trailing attrition windows."""
    source_match = re.search(r'<div class="v6-source-line">.*?</div>', stage, re.S)
    require(source_match is not None, "A slide is missing its source line.")
    replacement = (
        '<div class="v6-source-line"><strong>Source:</strong> HRDA - hrda.post_hire_monthly_worker_dtls. '
        'Trailing 12-month attrition uses a prior fiscal-year-end employee cohort and voluntary exits through '
        'the displayed fiscal-year end; aggregate presentation-safe result. '
        + html.escape(extra)
        + "</div>"
    )
    return stage[:source_match.start()] + replacement + stage[source_match.end():]


def replace_time_in_job_profile_time_in_role(deck: str, evidence: dict[str, Any]) -> str:
    """Slide 29: compare detailed-level tenure and stored time-in-role bands."""
    stage = stage_fragment(deck, 29)
    job_profile_card = article_with_class_and_text(stage, "role-level-tenure-card", "Time in current job profile")
    detailed_level_card = article_with_class_and_text(stage, "role-level-tenure-card", "Time at current detailed level")
    annual_rows_by_metric = {
        metric: {
            str(row["category"]): row
            for row in evidence["annual_rows"]
            if str(row["metric"]) == metric
        }
        for metric in ("time_at_detailed_level", "time_in_role")
    }
    detailed_level_updated = update_bar_card_distribution_and_annual_attrition(
        job_profile_card,
        display_rows_by_category(evidence, "time_at_detailed_level"),
        annual_rows_by_metric["time_at_detailed_level"],
        heading="Time at detailed level",
        panel_subtitle="Distribution / trailing 12m attrition",
    )
    time_in_role_updated = update_bar_card_distribution_and_annual_attrition(
        detailed_level_card,
        display_rows_by_category(evidence, "time_in_role"),
        annual_rows_by_metric["time_in_role"],
        heading="Time in role",
        panel_subtitle="Distribution / trailing 12m attrition",
    )
    stage = stage.replace(job_profile_card, detailed_level_updated, 1).replace(detailed_level_card, time_in_role_updated, 1)
    stage = set_stage_annual_badge(stage, "August trailing 12m")
    stage = stage.replace("Time in job profile vs. detailed level", "Time at detailed level and time in role", 1)
    stage = stage.replace(
        "Two stored dates provide useful approximations, but neither is an approved career-tenure definition",
        "The detailed-level clock uses levelentrydate adjusted for rehire; Time in role uses the stored numeric field",
        2,
    )
    stage = stage.replace(
        "The detailed-level clock uses levelentrydate adjusted for rehire; Time in role uses the stored numeric field",
        "Baseline distribution is August 2025; the same cohort is followed for voluntary exits through August 2026",
        2,
    )
    source_match = re.search(r'<div class="v6-source-line">.*?</div>', stage, re.S)
    require(source_match is not None, "The revised tenure slide is missing its source line.")
    source_line = (
        '<div class="v6-source-line"><strong>Source:</strong> HRDA - hrda.post_hire_monthly_worker_dtls. '
        'Baseline distribution: active regular employees at the 2025-08-24 monthly snapshot. '
        'Both annual rates: strict voluntary exits from that same cohort in (2025-08-24, 2026-08-23]. '
        'Time at detailed level uses GREATEST(levelentrydate, max_hire_rehire_date) with job_level_primary_position populated; Time in role uses the stored numeric field.</div>'
    )
    stage = stage[:source_match.start()] + source_line + stage[source_match.end() :]
    updated_deck = replace_stage_fragment(deck, 29, stage)
    updated_deck = re.sub(
        r'(\d+\. )Time in job profile vs\. detailed level',
        r'\1Time at detailed level and time in role',
        updated_deck,
        count=1,
    )
    return updated_deck


def replace_company_tenure_with_annual_attrition(deck: str, direct_evidence: dict[str, Any]) -> str:
    stage = stage_fragment(deck, 31)
    original_rows = annual_rows_by_category(direct_evidence, "original_hire_tenure")
    latest_rows = annual_rows_by_category(direct_evidence, "latest_hire_tenure")
    original_card = article_with_class_and_text(stage, "company-tenure-card", "Service since original hire")
    latest_card = article_with_class_and_text(stage, "company-tenure-card", "Service since latest hire")
    stage = stage.replace(
        original_card,
        update_bar_card_with_annual_attrition(original_card, direct_bar_mapping(original_card, original_rows)),
        1,
    ).replace(
        latest_card,
        update_bar_card_with_annual_attrition(latest_card, direct_bar_mapping(latest_card, latest_rows)),
        1,
    )
    stage = set_stage_annual_badge(stage)
    stage = replace_stage_source_with_annual_definition(stage, "Each service-period panel uses its own displayed tenure band as the historical cohort category.")
    return replace_stage_fragment(deck, 31, stage)


def replace_promotion_time_with_annual_attrition(deck: str, promotion_evidence: dict[str, Any]) -> str:
    stage = stage_fragment(deck, 32)
    rows = annual_rows_by_category(promotion_evidence, "time_since_promotion")
    time_card = article_with_class_and_text(stage, "promotion-time-card", "Calendar-anniversary")
    state_card = article_with_class_and_text(stage, "promotion-state-card", "Non-temporal observed-history states")
    stage = stage.replace(
        time_card,
        update_bar_card_with_annual_attrition(time_card, direct_bar_mapping(time_card, rows)),
        1,
    ).replace(
        state_card,
        update_bar_card_with_annual_attrition(state_card, direct_bar_mapping(state_card, rows)),
        1,
    )
    stage = set_stage_annual_badge(stage)
    stage = stage.replace(
        "The latest recorded promotion is used; older history is incomplete",
        "The latest recorded promotion is used; annual attrition remains explicit where historical promotion evidence is usable",
        1,
    )
    stage = replace_stage_source_with_annual_definition(stage, "History predating observed promotion events is a distinct state, not a zero-promotion assumption.")
    return replace_stage_fragment(deck, 32, stage)


def comparable_promotion_rows(rows: list[dict[str, Any]]) -> str:
    published = [row for row in rows if row.get("publication_status") == "publishable"]
    maximum = max((int(row["employee_count"]) for row in rows), default=1)
    rates = [float(row["annual_attrition_rate_percent"]) for row in published]
    rendered: list[str] = []
    for row in rows:
        label = html.escape(str(row["label"]))
        count = int(row["employee_count"])
        share = float(row["distribution_percent"])
        rate = float(row["annual_attrition_rate_percent"])
        is_small = row.get("publication_status") == "internal_exploratory_small_cohort"
        rate_class = "internal-small-cohort" if is_small else annual_rate_class(rate, rates)
        rate_text = f"{rate:.1f}%*" if is_small else f"{rate:.1f}%"
        rate_title = (
            f"Internal exploratory aggregate: {int(row['voluntary_exits']):,} voluntary exits from n={count:,}; n<30 is descriptive, not a stable rate estimate."
            if is_small
            else f"Annual voluntary attrition: {int(row['voluntary_exits']):,} voluntary exits from n={count:,}."
        )
        width = 100.0 * count / maximum
        rendered.append(
            '<div class="v7-promotion-comparable-row' + (" is-exploratory" if is_small else "") + '">'
            f'<div class="v7-promotion-comparable-label">{label}</div>'
            '<div class="v7-promotion-comparable-track">'
            f'<div class="v7-promotion-comparable-fill" style="width:{width:.4f}%"></div></div>'
            f'<div class="v7-promotion-comparable-value">{share:.1f}% · n={count:,}</div>'
            f'<span class="v7-promotion-annual v7-annual-attrition v6-rate-pill {rate_class}" title="{html.escape(rate_title)}" aria-label="{html.escape(rate_title)}">{rate_text}</span>'
            '</div>'
        )
    return "".join(rendered)


def replace_time_since_last_promotion_with_comparable_cohorts(deck: str, evidence: dict[str, Any]) -> str:
    """Replace slide 26 with the two independently normalized temporal panels."""
    recorded = list(evidence["recorded_promotion_distribution"])
    proxy = list(evidence["no_recorded_promotion_role_tenure_proxy_distribution"])
    totals = evidence["cohort_totals"]
    exclusions = {str(row["category"]): int(row["employee_count"]) for row in evidence["declared_exclusions"]}
    recorded_total = int(totals["recorded_promotion"])
    proxy_total = int(totals["no_recorded_promotion_role_tenure_proxy"])
    history_excluded = exclusions.get("excluded_history_before_observable", 0)
    mismatch_excluded = exclusions.get("excluded_role_tenure_not_aligned", 0)
    stage = f'''<div class="slide-stage" id="slide-32" data-v7-promotion-comparable-cohorts="true">
  <div class="slide-heading"><div><h2 class="slide-title-text">Time since last promotion</h2><p class="slide-subtitle">Two independent baseline cohorts; the lower panel is a strict employment-episode proxy, not “never promoted”</p></div><span class="badge badge-info">Annual voluntary attrition (12 months)</span></div>
  <article class="card card-full v7-promotion-comparable-card">
    <div class="v7-promotion-comparable-definition"><span><strong>Feature snapshot:</strong> 24 Aug 2025 · active Regular employees, excluding RF360.</span><span><strong>Trailing 12-month voluntary attrition:</strong> strict exits in (2025-08-24, 2026-08-23].</span></div>
    <div class="v7-promotion-comparable-layout">
      <section class="v7-promotion-comparable-panel"><div class="v7-promotion-comparable-heading"><span>Time since latest recorded promotion</span><small>n={recorded_total:,} · distribution / annual attrition</small></div><div class="v7-promotion-comparable-bars">{comparable_promotion_rows(recorded)}</div></section>
      <section class="v7-promotion-comparable-panel"><div class="v7-promotion-comparable-heading"><span>People with no recorded promotion</span><small>n={proxy_total:,} · distribution / annual attrition</small></div><div class="v7-promotion-comparable-bars">{comparable_promotion_rows(proxy)}</div></section>
    </div>
    <p class="v7-promotion-comparable-note"><strong>Read carefully:</strong> panel percentages use their own cohort denominator. The proxy requires no valid recorded promotion since hire/rehire, an episode inside observable history, and stored role tenure matching calendar episode tenure (rounded to one decimal). Cohorts are independent: {history_excluded:,} no-event cases with earlier unobservable history and {mismatch_excluded:,} with a role/episode mismatch are excluded from the proxy. The recorded-promotion 5+ row (n=7) is shown under the internal-analysis exception as descriptive only; its rate is not a stable estimate. This is distinct from the proxy's 5+ no-recorded-promotion cohort.</p>
  </article>
</div>'''
    require(stage.count("v7-promotion-comparable-row") == 10, "Comparable promotion slide must contain five bands in each panel.")
    require("never promoted" in stage.lower(), "Comparable promotion slide must state the semantic limitation.")
    return replace_stage_fragment(deck, 32, stage)


PROMOTION_HISTORY_STATES = (
    "zero_recorded_promotions",
    "one_recorded_promotion",
    "two_or_more_recorded_promotions",
    "partial_promotion_history",
)
ENTRY_PATH_STATES = (
    "promotion_confirmed_into_current_grade",
    "observed_entry_without_registered_promotion",
    "current_grade_entry_not_observable",
)


def table_row_label(row: str) -> str:
    match = re.search(r'<th\b[^>]*\bscope="row"[^>]*>(?P<label>.*?)</th>', row, re.I | re.S)
    require(match is not None, "An annual promotion matrix row is missing its row label.")
    return html.unescape(re.sub(r"<[^>]+>", "", match.group("label"))).strip()


def table_rows(table: str) -> list[str]:
    rows = []
    for match in re.finditer(r"<tr\b[^>]*>", table, re.I):
        row = table[match.start() : matching_tag_end(table, "tr", match.start())]
        if 'scope="row"' in row:
            rows.append(row)
    require(rows, "An annual promotion matrix has no data rows.")
    return rows


def annual_cell_pill(prefix: str, label: str, row: dict[str, Any] | None, all_rates: list[float], css_class: str) -> str:
    pill = annual_attrition_pill(label, row, all_rates, extra_class=css_class)
    rate = annual_rate(row)
    display = "Not estimable" if rate is None else f"{rate:.1f}%"
    return pill.replace(
        ">" + display + "</span>",
        "><span class=\"v7-annual-pill-prefix\">" + html.escape(prefix) + "</span>" + display + "</span>",
        1,
    )


def promotion_history_matrix_card(
    card: str,
    rows_by_category: dict[str, dict[str, Any]],
    visible_grades: set[str],
) -> str:
    """Add one compact annual attrition pill to each displayed matrix cell."""
    table_match = re.search(r'<table\b[^>]*\bclass="[^"]*\bpromotion-grade-matrix\b[^"]*"[^>]*>', card, re.I)
    require(table_match is not None, "Promotion-history card is missing its matrix.")
    table_end = matching_tag_end(card, "table", table_match.start())
    table = card[table_match.start():table_end]
    source_rows = table_rows(table)
    matrix: dict[tuple[str, str], dict[str, Any] | None] = {}
    for source_row in source_rows:
        grade = table_row_label(source_row)
        for state in PROMOTION_HISTORY_STATES:
            if grade == "Other grades":
                raw_rows = [
                    item
                    for category, item in rows_by_category.items()
                    if category.split("|", 1)[0] not in visible_grades and category.endswith("|" + state)
                ]
                matrix[(grade, state)] = aggregate_annual_rows(raw_rows, f"Other grades|{state}") if raw_rows else None
            else:
                matrix[(grade, state)] = rows_by_category.get(grade + "|" + state)
    rates = [rate for item in matrix.values() if (rate := annual_rate(item)) is not None]
    require(rates, "Promotion-history matrix has no publishable annual cells.")
    updated_table = table
    for source_row in source_rows:
        grade = table_row_label(source_row)
        current_row = next(row for row in table_rows(updated_table) if table_row_label(row) == grade)
        cells = list(re.finditer(r'<td\b(?P<attrs>[^>]*)>(?P<content>.*?)</td>', current_row, re.I | re.S))
        data_cells = [cell for cell in cells if "promotion-grade-total" not in cell.group("attrs")]
        require(len(data_cells) == len(PROMOTION_HISTORY_STATES), f"Promotion-history row {grade!r} has an unexpected cell count.")
        rebuilt = current_row
        for cell, state in reversed(list(zip(data_cells, PROMOTION_HISTORY_STATES))):
            item = matrix[(grade, state)]
            pill = annual_cell_pill("A", grade + " / " + state, item, rates, "v7-matrix-annual-pill")
            replacement = (
                '<td' + cell.group("attrs") + ">" + cell.group("content") + pill + "</td>"
            )
            rebuilt = rebuilt[:cell.start()] + replacement + rebuilt[cell.end():]
        updated_table = updated_table.replace(current_row, rebuilt, 1)
    updated = card[:table_match.start()] + updated_table + card[table_end:]
    return updated


def replace_promotion_history_with_annual_attrition(deck: str, promotion_evidence: dict[str, Any]) -> str:
    stage = stage_fragment(deck, 33)
    rows_by_category = annual_rows_by_category(promotion_evidence, "promotion_history_by_grade")
    matrix_cards = [
        article_with_class_and_text(stage, "promotion-grade-matrix-card", "M20 through R40"),
        article_with_class_and_text(stage, "promotion-grade-matrix-card", "R50 through Other grades"),
    ]
    visible_grades = {
        table_row_label(row)
        for card in matrix_cards
        for table_match in re.finditer(r'<table\b[^>]*\bpromotion-grade-matrix\b[^>]*>', card, re.I)
        for row in table_rows(card[table_match.start():matching_tag_end(card, "table", table_match.start())])
        if table_row_label(row) != "Other grades"
    }
    for card in matrix_cards:
        stage = stage.replace(card, promotion_history_matrix_card(card, rows_by_category, visible_grades), 1)
    stage = set_stage_annual_badge(stage)
    stage = stage.replace(
        "Counts reflect promotions observed in the current employment period",
        "Distribution retains observed promotion history; compact annual attrition pills appear in every visible cell",
        1,
    )
    stage = replace_stage_source_with_annual_definition(stage, "Matrix cells under the threshold remain explicitly Not estimable; Other grades are pooled from raw annual cohorts before the rate is calculated.")
    return replace_stage_fragment(deck, 33, stage)


def entry_path_card_rows(card: str) -> list[str]:
    rows = []
    for match in re.finditer(r'<div\b[^>]*\bclass="[^"]*\bentry-path-row\b[^"]*"[^>]*>', card, re.I):
        rows.append(card[match.start() : matching_tag_end(card, "div", match.start())])
    require(rows, "The current-grade entry card has no rows.")
    return rows


def entry_path_grade(row: str) -> str:
    match = re.search(r'<div\b[^>]*\bclass="[^"]*\bentry-path-grade\b[^"]*"[^>]*>(?P<label>.*?)</div>', row, re.I | re.S)
    require(match is not None, "The current-grade entry row is missing its grade.")
    return html.unescape(re.sub(r"<[^>]+>", "", match.group("label"))).strip()


def replace_entry_path_with_annual_attrition(deck: str, promotion_evidence: dict[str, Any]) -> str:
    stage = stage_fragment(deck, 34)
    rows_by_category = annual_rows_by_category(promotion_evidence, "current_grade_entry_path")
    cards = [
        article_with_class_and_text(stage, "entry-path-card", "M20 through R30"),
        article_with_class_and_text(stage, "entry-path-card", "R40 through Other grades"),
    ]
    visible_grades = {entry_path_grade(row) for card in cards for row in entry_path_card_rows(card) if entry_path_grade(row) != "Other grades"}
    metric_rows: dict[tuple[str, str], dict[str, Any] | None] = {}
    for card in cards:
        for row in entry_path_card_rows(card):
            grade = entry_path_grade(row)
            for state in ENTRY_PATH_STATES:
                if grade == "Other grades":
                    raw_rows = [
                        item
                        for category, item in rows_by_category.items()
                        if category.split("|", 1)[0] not in visible_grades and category.endswith("|" + state)
                    ]
                    metric_rows[(grade, state)] = aggregate_annual_rows(raw_rows, f"Other grades|{state}") if raw_rows else None
                else:
                    metric_rows[(grade, state)] = rows_by_category.get(grade + "|" + state)
    rates = [rate for item in metric_rows.values() if (rate := annual_rate(item)) is not None]
    require(rates, "Current-grade entry paths have no publishable annual rates.")
    labels = ("P", "N", "U")
    for card in cards:
        updated_card = card
        for original_row in entry_path_card_rows(card):
            grade = entry_path_grade(original_row)
            pills = "".join(
                annual_cell_pill(prefix, grade + " / " + state, metric_rows[(grade, state)], rates, "v7-entry-path-annual-pill")
                for prefix, state in zip(labels, ENTRY_PATH_STATES)
            )
            markup = '<div class="entry-path-annual-rates" aria-label="Annual voluntary attrition by entry path">' + pills + "</div>"
            replacement = original_row[:-len("</div>")] + markup + "</div>"
            updated_card = updated_card.replace(original_row, replacement, 1)
        stage = stage.replace(card, updated_card, 1)
    stage = set_stage_annual_badge(stage)
    stage = stage.replace(
        "Observable grade-entry history does not prove how an employee was originally hired",
        "Observable grade-entry history retains its distribution; P, N, and U annual attrition pills follow every visible row",
        1,
    )
    stage = replace_stage_source_with_annual_definition(stage, "P = confirmed promotion, N = observed entry without registered promotion, and U = entry not observable; Other grades are cohort-pooled before calculation.")
    return replace_stage_fragment(deck, 34, stage)


LEVEL_GROUPED_EVIDENCE_LABELS = {
    "VP & Above": "1 - VP & Above",
    "Sr Dir": "2 - Sr Dir",
    "Princ/Directors": "3 - Princ/Directors",
    "Mgrs Corp": "4 - Mgrs Corp",
    "Sr Staff & /Mgr": "5 - Sr Staff & /Mgr",
    "Staff & /Mgr": "6 - Staff & /Mgr",
    "Senior & Lead": "7 - Senior & Lead",
    "Assoc & Int/Eng": "8 - Assoc & Int/Eng",
    "Support": "9 - Support",
}


def mapped_level_group_card(card: str, rows_by_category: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for label in card_bar_labels(card):
        category = LEVEL_GROUPED_EVIDENCE_LABELS.get(label)
        require(category is not None and category in rows_by_category, f"Level-grouped annual evidence is missing {label!r}.")
        mapping[label] = rows_by_category[category]
    return mapping


def replace_level_with_annual_attrition(deck: str, direct_evidence: dict[str, Any]) -> str:
    stage = stage_fragment(deck, 35)
    grouped_rows = annual_rows_by_category(direct_evidence, "level_grouped")
    management_rows = annual_rows_by_category(direct_evidence, "management_level")
    job_rows = annual_rows_by_category(direct_evidence, "job_level")
    grouped_card = article_with_class_and_text(stage, "level-main-card", "Level grouped")
    management_card = article_with_class_and_text(stage, "level-support-card", "Management level")
    job_card = article_with_class_and_text(stage, "level-job-detail-card", "Top 10 job levels + Other")
    visible_job_levels = set(card_bar_labels(job_card)) - {"Other levels"}
    job_mapping = {
        label: (
            aggregate_annual_rows(
                [item for category, item in job_rows.items() if category not in visible_job_levels],
                "Other levels",
            )
            if label == "Other levels"
            else job_rows.get(label)
        )
        for label in card_bar_labels(job_card)
    }
    require(all(item is not None for item in job_mapping.values()), "Level slide is missing a displayed job-level annual cohort.")
    stage = stage.replace(
        grouped_card,
        update_bar_card_with_annual_attrition(grouped_card, mapped_level_group_card(grouped_card, grouped_rows)),
        1,
    ).replace(
        management_card,
        update_bar_card_with_annual_attrition(management_card, direct_bar_mapping(management_card, management_rows)),
        1,
    ).replace(
        job_card,
        update_bar_card_with_annual_attrition(job_card, job_mapping),
        1,
    )
    stage = set_stage_annual_badge(stage)
    stage = stage.replace(
        "Three related fields provide different views of seniority",
        "Three related seniority views retain their distributions and add annual voluntary attrition by displayed group",
        1,
    )
    stage = replace_stage_source_with_annual_definition(stage, "Other levels is aggregated from its historical employee-snapshot and voluntary-exit totals before the annual rate is calculated.")
    return replace_stage_fragment(deck, 35, stage)


def level_grade_family_row_label(row: str) -> str:
    match = re.search(r'<div\b[^>]*\bclass="[^"]*\blevel-grade-family-label\b[^"]*"[^>]*>(?P<label>.*?)</div>', row, re.I | re.S)
    require(match is not None, "A level-grade-family row is missing its grouped-level label.")
    return html.unescape(re.sub(r"<[^>]+>", "", match.group("label"))).strip()


def level_grade_family_rows(card: str) -> list[str]:
    rows = []
    for match in re.finditer(r'<div\b[^>]*\bclass="[^"]*\blevel-grade-family-row\b[^"]*"[^>]*>', card, re.I):
        rows.append(card[match.start() : matching_tag_end(card, "div", match.start())])
    require(rows, "The level-grade-family chart has no rows.")
    return rows


def level_grade_family_segments(row: str) -> list[tuple[str, str]]:
    segments = []
    for match in re.finditer(r'<span\b[^>]*\bclass="[^"]*\blevel-grade-family-segment(?!-)[^"]*"[^>]*>', row, re.I):
        opening = match.group(0)
        title_match = re.search(r'\btitle="([^"]*)"', opening, re.I)
        require(title_match is not None, "A level-grade-family segment has no title.")
        family = html.unescape(title_match.group(1)).split(":", 1)[0].strip()
        segments.append((family, row[match.start() : matching_tag_end(row, "span", match.start())]))
    require(segments, "A level-grade-family row has no segments.")
    return segments


def replace_level_grade_family_with_annual_attrition(deck: str, direct_evidence: dict[str, Any]) -> str:
    stage = stage_fragment(deck, 36)
    evidence_rows = annual_rows_by_category(direct_evidence, "level_grade_family")
    card = article_with_class_and_text(stage, "level-grade-family-card", "Level grouped")
    row_metrics: dict[tuple[str, str], dict[str, Any] | None] = {}
    for row in level_grade_family_rows(card):
        visible_label = level_grade_family_row_label(row)
        group_label = LEVEL_GROUPED_EVIDENCE_LABELS.get(visible_label)
        require(group_label is not None, f"Level-family annual evidence cannot map {visible_label!r}.")
        for family, _ in level_grade_family_segments(row):
            row_metrics[(visible_label, family)] = evidence_rows.get(group_label + "|" + family)
    rates = [rate for metric in row_metrics.values() if (rate := annual_rate(metric)) is not None]
    require(rates, "Level-grade-family visual has no publishable annual rates.")
    updated_card = card
    for source_row in level_grade_family_rows(card):
        label = level_grade_family_row_label(source_row)
        pills = "".join(
            annual_cell_pill(family, label + " / " + family, row_metrics[(label, family)], rates, "v7-level-family-annual-pill")
            for family, _ in level_grade_family_segments(source_row)
        )
        track_match = re.search(r'<div\b[^>]*\bclass="[^"]*\blevel-grade-family-track\b[^"]*"[^>]*>', source_row, re.I)
        require(track_match is not None, "A level-grade-family row has no track.")
        track_end = matching_tag_end(source_row, "div", track_match.start())
        markup = '<div class="level-grade-family-annual-rates" aria-label="Annual voluntary attrition by grade family">' + pills + "</div>"
        replacement = source_row[:track_end] + markup + source_row[track_end:]
        updated_card = updated_card.replace(source_row, replacement, 1)
    stage = stage.replace(card, updated_card, 1)
    stage = set_stage_annual_badge(stage)
    stage = stage.replace(
        "Grade family adds context to Level; it is not an official career track",
        "Grade family adds context to Level; annual voluntary attrition is shown below every visible level-by-family segment",
        1,
    )
    stage = replace_stage_source_with_annual_definition(stage, "Every rate is assigned to the displayed historical level-by-grade-family employee-snapshot cohort.")
    return replace_stage_fragment(deck, 36, stage)


def replace_manager_layers_with_annual_attrition(deck: str, evidence: dict[str, Any]) -> str:
    """Render baseline reconstructed layer cohorts with their annual rates."""
    stage = stage_fragment(deck, 37)
    card = article_with_class_and_text(stage, "layers-from-ceo-distribution-card", "manager-chain depth")
    evidence_rows = {str(row["label"]): row for row in evidence["distribution"]}
    visible_rows = nav38_card_mapping(card, evidence_rows)
    require(all(row is not None for row in visible_rows.values()), "Manager-layer annual evidence is missing a visible depth band.")
    card = update_bar_card_distribution_and_annual_attrition(
        card,
        visible_rows,
        visible_rows,
        heading="Active regular employees by reconstructed manager-chain depth",
        panel_subtitle="Distribution / annual attrition",
    )
    original_card = article_with_class_and_text(stage, "layers-from-ceo-distribution-card", "manager-chain depth")
    stage = stage.replace(original_card, card, 1)
    stage = set_stage_annual_badge(stage, "August trailing 12m")
    stage = stage.replace(
        "The chart counts manager links between each employee and the approved CEO root",
        "Each baseline employee is assigned to a reconstructed manager-chain depth; the same cohort is followed for strict voluntary exits",
        2,
    )
    stage = replace_stage_source_with_annual_definition(
        stage,
        "Baseline category membership is reconstructed at 2025-08-24 to the unique no-manager CEO-title root; rates use strict VOLUNTARY exits in (2025-08-24, 2026-08-23].",
    )
    stage = stage.replace("aggregate internal-analysis result.", "aggregate presentation-safe result.", 1)
    return replace_stage_fragment(deck, 37, stage)


def build_layers_from_ceo_0_2_compensation_grade_slide(evidence: dict[str, Any]) -> str:
    """Render the authorized internal follow-up with every exact stored grade."""
    ordered_rows = sorted(evidence["rows"], key=lambda row: str(row["label"]))
    cohort = evidence["cohort"]
    comparable_rows = [row for row in ordered_rows if int(row["employee_count"]) >= 30]
    comparable_count = sum(int(row["employee_count"]) for row in comparable_rows)
    comparable_labels = ", ".join(str(row["label"]) for row in comparable_rows)
    largest_share = max(float(row["cohort_share_percent"]) for row in ordered_rows)
    rates = [float(row["annual_attrition_rate_percent"]) for row in ordered_rows]
    rendered_cells = []
    for row in ordered_rows:
        label = str(row["label"])
        count = int(row["employee_count"])
        exits = int(row["voluntary_exits"])
        share = float(row["cohort_share_percent"])
        rate = float(row["annual_attrition_rate_percent"])
        exploratory = count < 30
        cell_class = "is-exploratory" if exploratory else "is-comparable"
        status_tag = (
            '<span class="layers-grade-followup-exploratory">Exploratory n&lt;30</span>'
            if exploratory
            else '<span class="layers-grade-followup-comparable">n&ge;30</span>'
        )
        pill_class = attrition_pill_class(rate, rates)
        tooltip = (
            f"Exact compensation grade {label}: n={count:,}; {share:.1f}% of the cohort; "
            f"{exits:,} voluntary exits; {rate:.1f}% 12-month attrition."
        )
        escaped_tooltip = html.escape(tooltip, quote=True)
        rendered_cells.append(
            '<section class="layers-grade-followup-cell layers-grade-followup-bar-row '
            + cell_class
            + '" data-grade="'
            + html.escape(label, quote=True)
            + '" aria-label="'
            + escaped_tooltip
            + '"><div class="layers-grade-followup-label">'
            + html.escape(label)
            + '</div><div class="layers-grade-followup-track" aria-hidden="true"><span style="width:'
            + f"{100 * share / largest_share:.1f}%"
            + '"></span></div><div class="layers-grade-followup-distribution">'
            + f"n={count:,} &middot; {share:.1f}%"
            + '</div><div class="layers-grade-followup-exits">'
            + f"{exits:,} exits"
            + '</div><span class="layers-grade-followup-attrition v6-rate-pill '
            + pill_class
            + '" title="'
            + escaped_tooltip
            + '" aria-label="'
            + escaped_tooltip
            + '">'
            + f"{rate:.1f}%"
            + '</span>'
            + status_tag
            + "</section>"
        )
    return (
        '\n  <div class="slide-stage" id="slide-37-followup" data-v7-layers-grade-followup="true">'
        '<div class="slide-heading"><div><h2 class="slide-title-text">0&ndash;2 manager layers: exact compensation-grade distribution</h2>'
        '<p class="slide-subtitle">Baseline cohort 24 Aug 2025 &middot; strict voluntary exits through 23 Aug 2026</p>'
        '</div><span class="badge badge-info">Internal exploratory analysis</span></div>'
        '<article class="card card-full v6-playbook-card layers-grade-followup-card">'
        '<div class="layers-grade-followup-intro"><div><span class="layers-grade-followup-eyebrow">0&ndash;2 reconstructed manager layers &middot; exact stored grade codes</span><strong>'
        + f"18 exact grades &middot; n={int(cohort['employee_count']):,} &middot; {int(cohort['voluntary_exits']):,} voluntary exits &middot; {float(cohort['annual_attrition_rate_percent']):.1f}% 12-month attrition"
        + '</strong></div><p>Authorized only for the internal exploratory review with Julia. Every stored grade remains visible; no pay values are displayed.</p></div>'
        '<div class="layers-grade-followup-chart"><div class="layers-grade-followup-keyline" aria-hidden="true">'
        '<span>Exact grade</span><span>Employee distribution</span><span>n / share</span><span>Voluntary exits</span><span>Annual attrition</span><span>Review status</span>'
        '</div><div class="layers-grade-followup-bar-list">'
        + "".join(rendered_cells)
        + '</div></div><div class="layers-grade-followup-takeaway"><strong>Read-out:</strong> '
        + html.escape(comparable_labels)
        + f" are the only grades with n &ge; 30 ({comparable_count:,} of {int(cohort['employee_count']):,} employees). The remaining cells are retained to inspect the full mix, not to rank small-cohort rates."
        + '</div><div class="layers-grade-followup-caveat">All cells tagged <strong>Exploratory n&lt;30</strong> are descriptive only. Composition and attrition are associations, not evidence that grade causes attrition.</div>'
        '<div class="layers-grade-followup-source"><strong>Source:</strong> Same-snapshot reconstructed manager chains and exact stored <code>compensation_grade</code> codes at 24 Aug 2025; strict VOLUNTARY exits in (2025-08-24, 2026-08-23]. No employee, manager, or exact compensation/pay values are shown.</div>'
        '</article></div>'
    )


def insert_layers_from_ceo_0_2_compensation_grade_followup(deck: str, evidence: dict[str, Any]) -> str:
    """Insert the approved follow-up after technical stage 37 and keep reader navigation contiguous."""
    require('id="slide-37-followup"' not in deck, "0–2 layer compensation-grade follow-up already exists.")
    stage_37 = stage_fragment(deck, 37)
    followup = build_layers_from_ceo_0_2_compensation_grade_slide(evidence)
    updated = deck.replace(stage_37, stage_37 + "\n" + followup, 1)

    nav_button_pattern = (
        r'(?P<prefix><button class="nav-pill(?: [^"]*)?" data-slide=")'
        r'(?P<index>\d+)(?P<middle>">)(?P<label>\d+)'
        r'(?P<suffix>\. [^<]+</button>)'
    )

    def shift_nav_button(match: re.Match[str]) -> str:
        index = int(match.group("index"))
        label = int(match.group("label"))
        require(label == index + 1, "Navigation labels must match indexes before inserting the 0–2 follow-up.")
        if index <= 30:
            return match.group(0)
        return (
            f'{match.group("prefix")}{index + 1}{match.group("middle")}'
            f'{label + 1}{match.group("suffix")}'
        )

    updated, nav_buttons = re.subn(nav_button_pattern, shift_nav_button, updated)
    require(nav_buttons == 43, "V7 must have 43 navigation items before the 0–2 follow-up is inserted.")
    anchor = '<button class="nav-pill" data-slide="30">31. Manager layers to the CEO</button>'
    followup_nav = '<button class="nav-pill" data-slide="31">32. 0&ndash;2 layers: exact compensation grades</button>'
    require(updated.count(anchor) == 1, "Manager layers navigation anchor is missing.")
    updated = updated.replace(anchor, anchor + "\n      " + followup_nav, 1)

    # Normalize every range to an HTML entity. This avoids corrupting the
    # en dash when the source deck moves between Windows code pages.
    range_pattern = (
        r'(?P<prefix><span class="nav-section-range">)(?P<start>\d+)'
        r'(?P<separator>[^0-9]+)(?P<end>\d+)(?P<suffix></span>)'
    )

    def normalize_range_separator(match: re.Match[str]) -> str:
        return f'{match.group("prefix")}{match.group("start")}&ndash;{match.group("end")}{match.group("suffix")}'

    updated, normalized_ranges = re.subn(range_pattern, normalize_range_separator, updated)
    require(normalized_ranges == 6, "Could not normalize all navigation range separators before follow-up insertion.")
    expected_ranges = [
        '<span class="nav-section-range">1&ndash;2</span>',
        '<span class="nav-section-range">3&ndash;4</span>',
        '<span class="nav-section-range">5&ndash;17</span>',
        '<span class="nav-section-range">18&ndash;24</span>',
        '<span class="nav-section-range">25&ndash;34</span>',
        '<span class="nav-section-range">35&ndash;43</span>',
    ]
    for item in expected_ranges:
        require(updated.count(item) == 1, f"Expected navigation range is missing before follow-up insertion: {item}")
    updated = updated.replace('<span class="nav-section-range">25&ndash;34</span>', '<span class="nav-section-range">25&ndash;35</span>', 1)
    updated = updated.replace('<span class="nav-section-range">35&ndash;43</span>', '<span class="nav-section-range">36&ndash;44</span>', 1)
    require(updated.count("Slides 25-34") == 1 and updated.count("Slides 35-43") == 1, "Agenda ranges are missing before follow-up insertion.")
    updated = updated.replace("Slides 25-34", "Slides 25-35", 1)
    updated = updated.replace("Slides 35-43", "Slides 36-44", 1)
    return updated


def build_direct_team_span_followup_slide(evidence: dict[str, Any]) -> str:
    """Render the authorized direct-team-span distribution and annual attrition."""
    coverage = evidence["coverage"]
    bands = evidence["bands"]
    largest_share = max(float(row["employee_share_percent"]) for row in bands)
    rates = [float(row["annual_attrition_rate_percent"]) for row in bands]
    rendered_bands = []
    for row in bands:
        label = str(row["label"])
        count = int(row["employee_count"])
        teams = int(row["team_count"])
        exits = int(row["voluntary_exits"])
        share = float(row["employee_share_percent"])
        rate = float(row["annual_attrition_rate_percent"])
        is_largest = math.isclose(share, largest_share, abs_tol=0.000001)
        pill_class = attrition_pill_class(rate, rates)
        tooltip = (
            f"{label} direct reports: n={count:,}; {teams:,} teams; "
            f"{exits:,} voluntary exits; {rate:.1f}% annual attrition."
        )
        escaped_tooltip = html.escape(tooltip, quote=True)
        rendered_bands.append(
            '<section class="direct-team-span-band direct-team-span-bar-row'
            + (" is-largest" if is_largest else "")
            + '" data-span-band="'
            + html.escape(label, quote=True)
            + '" aria-label="'
            + escaped_tooltip
            + '"><div class="direct-team-span-label">'
            + html.escape(label)
            + '</div><div class="direct-team-span-track" aria-hidden="true"><span style="width:'
            + f"{100 * share / largest_share:.1f}%"
            + '"></span></div><div class="direct-team-span-distribution">'
            + f"n={count:,} &middot; {share:.1f}%"
            + '</div><div class="direct-team-span-detail">'
            + f"{teams:,} teams &middot; {exits:,} exits"
            + '</div><span class="direct-team-span-attrition v6-rate-pill '
            + pill_class
            + '" title="'
            + escaped_tooltip
            + '" aria-label="'
            + escaped_tooltip
            + '">'
            + f"{rate:.1f}%"
            + "</span></section>"
        )
    five = evidence["exact_span_comparison"]["five_direct_reports"]
    twenty = evidence["exact_span_comparison"]["twenty_direct_reports"]

    def exact_card(row: dict[str, Any], caption: str, exploratory: bool) -> str:
        class_suffix = " is-exploratory" if exploratory else ""
        exploratory_note = " &middot; exploratory (4 teams)" if exploratory else ""
        return (
            '<section class="direct-team-span-exact-card'
            + class_suffix
            + '" data-exact-span="'
            + str(int(row["direct_report_count"]))
            + '"><div><strong>'
            + caption
            + '</strong><span>n='
            + f"{int(row['employee_count']):,} &middot; {int(row['team_count']):,} teams &middot; {int(row['voluntary_exits']):,} exits"
            + exploratory_note
            + '</span></div><div class="direct-team-span-exact-rate">'
            + f"{float(row['annual_attrition_rate_percent']):.1f}%"
            + "</div></section>"
        )

    return (
        '\n  <div class="slide-stage" id="slide-37-span-followup" data-v7-direct-team-span-followup="true">'
        '<div class="slide-heading"><div><h2 class="slide-title-text">Direct team size (span): distribution and annual attrition</h2>'
        '<p class="slide-subtitle">Baseline cohort 24 Aug 2025 &middot; strict voluntary exits through 23 Aug 2026</p>'
        '</div><span class="badge badge-info">Internal exploratory analysis</span></div>'
        '<article class="card card-full v6-playbook-card direct-team-span-card">'
        '<div class="direct-team-span-intro"><div><span class="direct-team-span-eyebrow">Same-snapshot reconstructed direct reports per manager</span><strong>'
        + f"{int(coverage['eligible_employee_count']):,} of {int(coverage['baseline_employee_count']):,} active regular employees are eligible ({float(coverage['eligible_percent']):.1f}% coverage)"
        + '</strong></div><p>'
        + f"{int(coverage['unresolvable_manager_exclusion_count']):,} employees have no resolvable active regular manager at the snapshot and are reported as coverage exclusions, not as a span band."
        + '</p></div><div class="direct-team-span-chart"><div class="direct-team-span-keyline" aria-hidden="true">'
        '<span>Direct reports</span><span>Employee distribution</span><span>n / share</span><span>Teams / voluntary exits</span><span>Annual attrition</span>'
        '</div><div class="direct-team-span-bar-list">'
        + "".join(rendered_bands)
        + '</div></div><div class="direct-team-span-exact">'
        + exact_card(five, "Exact size: 5 direct reports", False)
        + exact_card(twenty, "Exact size: 20 direct reports", True)
        + '</div><div class="direct-team-span-caveat"><strong>Read-out:</strong> The bands describe observed workforce distribution and annual attrition; they do not establish that team size causes attrition. The exact size of 20 is exploratory because it comes from only four teams.</div>'
        '<div class="direct-team-span-source"><strong>Source:</strong> Direct-report counts reconstructed from same-snapshot reporting relationships at 24 Aug 2025; strict VOLUNTARY exits in (2025-08-24, 2026-08-23]. Stored report-count fields are not used as the primary definition. No employee, manager, or individual records are shown.</div>'
        '</article></div>'
    )


def insert_direct_team_span_followup(deck: str, evidence: dict[str, Any]) -> str:
    """Insert the direct-team-span slide after the exact-grade follow-up."""
    require('id="slide-37-span-followup"' not in deck, "Direct-team-span follow-up already exists.")
    followup = re.search(
        r'<div class="slide-stage" id="slide-37-followup".*?(?=\n\s*<div class="slide-stage" id="slide-38")',
        deck,
        flags=re.S,
    )
    require(followup is not None, "The exact-grade follow-up must be present before inserting direct-team span.")
    span_slide = build_direct_team_span_followup_slide(evidence)
    updated = deck[:followup.end()] + "\n" + span_slide + deck[followup.end():]

    nav_button_pattern = (
        r'(?P<prefix><button class="nav-pill(?: [^"]*)?" data-slide=")'
        r'(?P<index>\d+)(?P<middle>">)(?P<label>\d+)'
        r'(?P<suffix>\. [^<]+</button>)'
    )

    def shift_nav_button(match: re.Match[str]) -> str:
        index = int(match.group("index"))
        label = int(match.group("label"))
        require(label == index + 1, "Navigation labels must match indexes before inserting direct-team span.")
        if index <= 31:
            return match.group(0)
        return (
            f'{match.group("prefix")}{index + 1}{match.group("middle")}'
            f'{label + 1}{match.group("suffix")}'
        )

    updated, nav_buttons = re.subn(nav_button_pattern, shift_nav_button, updated)
    require(nav_buttons == 44, "V7 must have 44 navigation items before inserting direct-team span.")
    anchor = '<button class="nav-pill" data-slide="31">32. 0&ndash;2 layers: exact compensation grades</button>'
    span_nav = '<button class="nav-pill" data-slide="32">33. Direct team size (span)</button>'
    require(updated.count(anchor) == 1, "Exact-grade follow-up navigation anchor is missing.")
    updated = updated.replace(anchor, anchor + "\n      " + span_nav, 1)

    range_pattern = (
        r'(?P<prefix><span class="nav-section-range">)(?P<start>\d+)'
        r'(?P<separator>[^0-9]+)(?P<end>\d+)(?P<suffix></span>)'
    )

    def normalize_range_separator(match: re.Match[str]) -> str:
        return f'{match.group("prefix")}{match.group("start")}&ndash;{match.group("end")}{match.group("suffix")}'

    updated, normalized_ranges = re.subn(range_pattern, normalize_range_separator, updated)
    require(normalized_ranges == 6, "Could not normalize all navigation ranges before direct-team-span insertion.")
    expected_ranges = [
        '<span class="nav-section-range">1&ndash;2</span>',
        '<span class="nav-section-range">3&ndash;4</span>',
        '<span class="nav-section-range">5&ndash;17</span>',
        '<span class="nav-section-range">18&ndash;24</span>',
        '<span class="nav-section-range">25&ndash;35</span>',
        '<span class="nav-section-range">36&ndash;44</span>',
    ]
    for item in expected_ranges:
        require(updated.count(item) == 1, f"Expected navigation range is missing before direct-team-span insertion: {item}")
    updated = updated.replace('<span class="nav-section-range">25&ndash;35</span>', '<span class="nav-section-range">25&ndash;36</span>', 1)
    updated = updated.replace('<span class="nav-section-range">36&ndash;44</span>', '<span class="nav-section-range">37&ndash;45</span>', 1)
    require(updated.count("Slides 25-35") == 1 and updated.count("Slides 36-44") == 1, "Agenda ranges are missing before direct-team-span insertion.")
    updated = updated.replace("Slides 25-35", "Slides 25-36", 1)
    updated = updated.replace("Slides 36-44", "Slides 37-45", 1)
    return updated


def replace_compensation_grade_with_annual_attrition(deck: str, direct_evidence: dict[str, Any]) -> str:
    stage = stage_fragment(deck, 38)
    evidence_rows = annual_rows_by_category(direct_evidence, "compensation_grade")
    card = article_with_class_and_text(stage, "compensation-grade-card", "All publicable compensation grades")
    visible_grades = set(card_bar_labels(card)) - {"Other grades"}
    mapping: dict[str, dict[str, Any] | None] = {}
    for label in card_bar_labels(card):
        mapping[label] = (
            aggregate_annual_rows(
                [item for category, item in evidence_rows.items() if category not in visible_grades],
                "Other grades",
            )
            if label == "Other grades"
            else evidence_rows.get(label)
        )
    require(all(item is not None for item in mapping.values()), "Compensation-grade slide is missing a visible annual cohort.")
    stage = stage.replace(
        card,
        update_bar_card_with_annual_attrition(
            card,
            mapping,
            rate_class_fn=compensation_grade_rate_class,
        ),
        1,
    )
    stage = set_stage_annual_badge(stage)
    stage = replace_stage_source_with_annual_definition(stage, "Other grades is reconstructed from summed historical exposures and exits before its annual rate is calculated.")
    return replace_stage_fragment(deck, 38, stage)


def replace_comp_ratio_with_annual_attrition(deck: str, direct_evidence: dict[str, Any]) -> str:
    """Keep the distribution and replace the incompatible six-month trend with annual bands."""
    stage = stage_fragment(deck, 39)
    evidence_rows = annual_rows_by_category(direct_evidence, "comp_ratio_band")
    distribution_card = article_with_class_and_text(stage, "comp-ratio-distribution-card", "Distribution by compa_ratio bands")
    mapping = direct_bar_mapping(distribution_card, evidence_rows)
    updated_distribution = update_bar_card_with_annual_attrition(distribution_card, mapping)
    rates = [rate for item in mapping.values() if (rate := annual_rate(item)) is not None]
    require(len(rates) == 7, "Comp-ratio annual evidence must cover all seven visible bands.")
    annual_lines = "".join(
        '<div class="v7-comp-ratio-annual-row"><span>'
        + html.escape(label)
        + "</span>"
        + annual_attrition_pill(label, row, rates, extra_class="v7-comp-ratio-annual-pill")
        + "</div>"
        for label, row in mapping.items()
    )
    annual_card = (
        '<article class="card chart-card comp-ratio-history-card v7-comp-ratio-annual-card">'
        '<div class="card-title">Annual voluntary attrition by compa_ratio band</div>'
        '<p class="v7-comp-ratio-annual-definition">Each rate uses the employees in its historical band as the denominator and strict voluntary exits in the following 12 months.</p>'
        '<div class="v7-comp-ratio-annual-list">'
        + annual_lines
        + '</div><div class="chart-footer">This panel replaces the inherited six-month trend because its historical scope is not the annual cohort shown beside it. Green = lowest rate, red = highest, blue = intermediate.</div>'
        '</article>'
    )
    history_card = article_with_class_and_text(stage, "comp-ratio-history-card", "Six-month voluntary attrition")
    stage = stage.replace(distribution_card, updated_distribution, 1).replace(history_card, annual_card, 1)
    stage = set_stage_annual_badge(stage)
    stage = stage.replace(
        "Comp-ratio bands and the historical attrition pattern are descriptive",
        "Comp-ratio bands and the annual historical attrition pattern are descriptive",
        1,
    )
    stage = replace_stage_source_with_annual_definition(stage, "The right panel intentionally shows the same seven annual bands rather than relabeling the inherited six-month trend.")
    return replace_stage_fragment(deck, 39, stage)


def remove_comp_ratio_six_month_history_script(deck: str) -> str:
    marker = "var compRatioHistoryRows ="
    marker_at = deck.find(marker)
    require(marker_at >= 0, "The obsolete comp-ratio six-month history script is missing.")
    script_start = deck.rfind("<script", 0, marker_at)
    script_end = deck.find("</script>", marker_at)
    require(script_start >= 0 and script_end >= 0, "The obsolete comp-ratio history script is malformed.")
    return deck[:script_start] + deck[script_end + len("</script>") :]


def replace_within_team_compensation_with_annual_attrition(deck: str, evidence: dict[str, Any]) -> str:
    stage = stage_fragment(deck, 40)
    count_rows = annual_rows_by_category(evidence, "within_team_review_count")
    share_rows = annual_rows_by_category(evidence, "within_team_review_share")
    state_rows = annual_rows_by_category(evidence, "within_team_no_comparable")
    count_card = article_with_class_and_text(stage, "within-team-count-card", "Managers by number of groups")
    share_card = article_with_class_and_text(stage, "within-team-rate-card", "Share of each manager")
    state_card = article_with_class_and_text(stage, "within-team-state-card", "Managers with no comparable groups")
    count_updated = update_bar_card_with_annual_attrition(count_card, direct_bar_mapping(count_card, count_rows))
    share_updated = update_bar_card_with_annual_attrition(share_card, direct_bar_mapping(share_card, share_rows))
    count_updated = count_updated.replace("Distribution / annual attrition", "Distribution / annual team attrition")
    share_updated = share_updated.replace("Distribution / annual attrition", "Distribution / annual team attrition")
    state_metric = state_rows["No comparable groups"]
    state_pill = annual_attrition_pill(
        "Managers with no comparable groups",
        state_metric,
        [float(state_metric["annual_attrition_rate_percent"])],
        extra_class="v7-within-team-state-pill",
    )
    state_updated = state_card.replace(
        '<div class="within-team-state-value">',
        '<div class="within-team-state-value">' + state_pill,
        1,
    )
    require(state_updated != state_card, "Could not add annual team attrition to the no-comparable-groups state.")
    stage = stage.replace(count_card, count_updated, 1).replace(share_card, share_updated, 1).replace(state_card, state_updated, 1)
    stage = set_stage_annual_badge(stage, "Annual team attrition")
    stage = stage.replace(
        "Wide ranges are review signals, not pay-equity findings",
        "Wide ranges are review signals, not pay-equity findings; labels show annual attrition among direct reports, not managers",
        1,
    )
    stage = replace_stage_source_with_annual_definition(stage, "For this slide the denominator is active regular direct reports assigned to managers in each displayed review-state category; pills therefore report annual team attrition.")
    return replace_stage_fragment(deck, 40, stage)


def retain_colocation_trend_years(card: str) -> str:
    """Keep the requested concise FY2023-FY2026 window in one trend card."""
    wrap_pattern = re.compile(r'<div\b[^>]*\bclass="[^"]*\btrend-bar-wrap\b[^"]*"[^>]*>', re.I)
    found_years: list[str] = []
    updated = card
    for match in reversed(list(wrap_pattern.finditer(card))):
        wrapper_end = matching_tag_end(card, "div", match.start())
        wrapper = card[match.start() : wrapper_end]
        year_match = re.search(r'<div class="trend-label">\s*<span>(?P<year>\d{4})</span>', wrapper, re.S)
        require(year_match is not None, "A co-location bar is missing its fiscal year.")
        year = year_match.group("year")
        found_years.append(year)
        if year not in COLOCATION_DISPLAY_YEARS:
            updated = updated[: match.start()] + updated[wrapper_end:]
    full_years = {str(year) for year in range(2020, 2027)}
    require(
        set(found_years) in (full_years, set(COLOCATION_DISPLAY_YEARS)),
        "Co-location chart has an unexpected fiscal-year inventory.",
    )
    updated, replacements = re.subn(
        r'(<div class="trend-chart"\s+style="--bars:)\d+("\s*>)',
        rf'\g<1>{len(COLOCATION_DISPLAY_YEARS)}\g<2>',
        updated,
        count=1,
    )
    require(replacements == 1, "Could not update the co-location visible bar count.")
    return updated


def co_location_card_with_annual_attrition(
    card: str,
    rows_by_year: dict[str, dict[str, Any]],
    unavailable_reason: str,
) -> str:
    display_years = COLOCATION_DISPLAY_YEARS
    card = retain_colocation_trend_years(card)
    publishable_rates = [annual_rate(rows_by_year[year]) for year in display_years]
    publishable_rates = [rate for rate in publishable_rates if rate is not None]
    require(len(publishable_rates) == len(display_years), "Co-location trailing windows must publish every displayed year.")
    updated = card
    for match in list(re.finditer(r'<div\b[^>]*\bclass="[^"]*\btrend-bar-wrap\b[^"]*"[^>]*>', card, re.I)):
        wrapper = card[match.start() : matching_tag_end(card, "div", match.start())]
        year_match = re.search(r'<div class="trend-label">\s*<span>(?P<year>\d{4})</span>', wrapper, re.S)
        require(year_match is not None, "A co-location bar is missing its fiscal year.")
        year = year_match.group("year")
        require(year in display_years, "Co-location chart has an unexpected fiscal year.")
        evidence_row = rows_by_year.get(year)
        rate = annual_rate(evidence_row)
        if rate is None:
            pill = (
                '<span class="v7-annual-attrition v6-rate-pill attr-unavailable is-unavailable v7-colocation-annual-pill" '
                'title="Trailing 12-month voluntary attrition ending FY'
                + html.escape(year)
                + ': '
                + html.escape(unavailable_reason)
                + '" aria-label="Trailing 12-month voluntary attrition ending FY'
                + html.escape(year)
                + ': Not estimable">Not estimable</span>'
            )
        else:
            pill = (
                '<span class="v7-annual-attrition v6-rate-pill '
                + annual_rate_class(rate, publishable_rates)
                + ' v7-colocation-annual-pill" title="Trailing 12-month voluntary attrition ending FY'
                + html.escape(year)
                + ': '
                + f"{rate:.1f}%"
                + '" aria-label="Trailing 12-month voluntary attrition ending FY'
                + html.escape(year)
                + ': '
                + f"{rate:.1f}%"
                + '">'
                + f"{rate:.1f}%"
                + "</span>"
            )
        label_match = re.search(r'(<div class="trend-label">.*?)(</div>)', wrapper, re.S)
        require(label_match is not None, "A co-location bar is missing its label wrapper.")
        # The targeted refresh is intentionally idempotent: replace a prior
        # co-location pill rather than appending a second rate to the year label.
        label_contents = re.sub(
            r'<span\b[^>]*\b(?:v7-colocation-annual-pill|v7-annual-attrition)\b[^>]*>.*?</span>',
            "",
            label_match.group(1),
            flags=re.I | re.S,
        )
        replacement = (
            wrapper[:label_match.start()]
            + label_contents
            + pill
            + label_match.group(2)
            + wrapper[label_match.end():]
        )
        updated = updated.replace(wrapper, replacement, 1)
    return updated


def replace_colocation_with_annual_attrition(deck: str, evidence: dict[str, Any]) -> str:
    stage = stage_fragment(deck, 41)
    office_rows = {str(row["fiscal_year"]): row for row in evidence["rates"]["same_office_site"]}
    office_city_rows = {str(row["fiscal_year"]): row for row in evidence["rates"]["same_office_site_and_city"]}
    office_card = article_with_class_and_text(stage, "chart-card", "Same stored office_site as manager")
    office_city_card = article_with_class_and_text(stage, "chart-card", "Same stored office_site and city as manager")
    unavailable_reason = "the fiscal year is outside the FY2023-FY2026 display window"
    office_updated = co_location_card_with_annual_attrition(office_card, office_rows, unavailable_reason)
    office_city_updated = co_location_card_with_annual_attrition(office_city_card, office_city_rows, unavailable_reason)
    office_updated = office_updated.replace(
        "Both stored office_site values are nonblank; percent uses comparable employee-manager snapshots.",
        "Both stored office_site values are nonblank; percent uses comparable employee-manager snapshots. Annual attrition appears below FY2020–FY2024; FY2025–FY2026 are gray because complete 12-month follow-up is unavailable.",
        1,
    )
    office_city_updated = office_city_updated.replace(
        "Different cities are not the same location. This is still a stored-field proxy, not physical presence.",
        "Different cities are not the same location. This is still a stored-field proxy, not physical presence. Annual attrition appears below FY2020–FY2024; FY2025–FY2026 are gray because complete 12-month follow-up is unavailable.",
        1,
    )
    office_updated = re.sub(
        r"(Both stored office_site values are nonblank; percent uses comparable employee-manager snapshots\.).*?(?=</(?:p|div)>)",
        r"\1 Showing FY2023-FY2026 only; each pill is trailing 12-month voluntary attrition from the prior fiscal-year-end cohort.",
        office_updated,
        count=1,
        flags=re.S,
    )
    office_city_updated = re.sub(
        r"(Different cities are not the same location\. This is still a stored-field proxy, not physical presence\.).*?(?=</(?:p|div)>)",
        r"\1 Showing FY2023-FY2026 only; each pill is trailing 12-month voluntary attrition from the prior fiscal-year-end cohort.",
        office_city_updated,
        count=1,
        flags=re.S,
    )
    stage = stage.replace(office_card, office_updated, 1).replace(office_city_card, office_city_updated, 1)
    stage = set_stage_annual_badge(stage, "Trailing 12m attrition")
    stage, subtitle_replacements = re.subn(
        r'(<h2 class="slide-title-text">Co-location with manager</h2><p class="slide-subtitle">).*?(</p>)',
        r'\1Matching assigned sites do not prove physical co-location; FY2023-FY2026 trailing 12-month voluntary attrition uses the prior fiscal-year-end cohort.\2',
        stage,
        count=1,
        flags=re.S,
    )
    require(subtitle_replacements == 1, "Could not update the concise co-location subtitle.")
    stage = replace_stage_source_with_trailing_12m_definition(stage, "Each FY2023-FY2026 pill is voluntary attrition from the prior fiscal-year-end cohort through that FY's final available snapshot. FY2020-FY2022 are intentionally omitted from this concise current view.")
    return replace_stage_fragment(deck, 41, stage)


def build_manager_timezone_proximity_slide(
    distribution_evidence: dict[str, Any],
    ytd_attrition_evidence: dict[str, Any],
) -> str:
    """Render three distribution bars with one compact 2026 YTD label each."""
    category_order = (
        ("same_office_site", "Same assigned office site"),
        ("different_site_up_to_4_hours", "Different site · ≤4 h offset"),
        ("different_site_more_than_4_hours", "Different site · >4 h offset"),
    )
    latest = distribution_evidence["latest_distribution"]
    diagnostics = distribution_evidence["diagnostics"]
    categorized = int(diagnostics["latest_categorized_employee_manager_pair_count"])
    eligible = int(diagnostics["latest_eligible_employee_manager_pair_count"])
    unmapped = int(diagnostics["latest_unmapped_employee_manager_pair_count"])
    ytd_by_category = {str(row["category"]): row for row in ytd_attrition_evidence["rows"]}
    # Display policy for this aggregate, internal-analysis view: a rate is
    # visible when its employee cohort meets the shared n>=30 threshold.  The
    # prior extra threshold of 30 voluntary exits hid a valid 633-person
    # cohort; the event count remains transparent in the hover label instead.
    displayable_rates = [
        float(row["ytd_voluntary_attrition_rate_percent"])
        for row in ytd_by_category.values()
        if int(row["employee_count"]) >= 30
    ]
    require(displayable_rates, "Manager time-zone slide needs at least one displayable 2026 YTD rate.")

    def ytd_pill(category: str, label: str) -> str:
        row = ytd_by_category[category]
        cohort_size = int(row["employee_count"])
        voluntary_exits = int(row["voluntary_exits"])
        if cohort_size < 30:
            return (
                '<span class="v4-inline-attrition-rate v6-rate-pill manager-timezone-ytd-pill attr-unavailable is-unavailable" '
                'title="2026 YTD voluntary attrition is not estimable because this aggregate segment has fewer than 30 baseline employees" '
                'aria-label="2026 YTD voluntary attrition for '
                + html.escape(label)
                + ': Not estimable">N/E</span>'
            )
        rate = float(row["ytd_voluntary_attrition_rate_percent"])
        rate_class = annual_rate_class(rate, displayable_rates)
        return (
            '<span class="v4-inline-attrition-rate v6-rate-pill manager-timezone-ytd-pill '
            + rate_class
            + '" title="2026 YTD voluntary attrition for '
            + html.escape(label)
            + ': '
            + f"{rate:.1f}% (observed through {html.escape(str(ytd_attrition_evidence['outcome_contract']['outcome_end_date']))}; not annualized)"
            + f" · baseline cohort n={cohort_size:,}; voluntary exits={voluntary_exits:,}"
            + '" aria-label="2026 YTD voluntary attrition for '
            + html.escape(label)
            + ': '
            + f"{rate:.1f}%; not annualized"
            + '">'
            + f"{rate:.1f}%"
            + "</span>"
        )

    maximum = max(int(latest[key]["employee_snapshot_count"]) for key, _ in category_order)
    distribution_rows = []
    for key, label in category_order:
        count = int(latest[key]["employee_snapshot_count"])
        share = 100 * count / categorized
        width = 100 * count / maximum
        distribution_rows.append(
            '<div class="bar-row v4-inline-attrition-row manager-timezone-bar-row"><div class="bar-label">'
            + html.escape(label)
            + '</div><div class="bar-track"><div class="bar-fill" style="width:'
            + f"{width:.1f}%"
            + '"></div></div><div class="bar-value">'
            + f"{share:.1f}% &middot; {count:,}"
            + ytd_pill(key, label)
            + "</div></div>"
        )
    categorized_share = 100 * categorized / eligible
    ytd_contract = ytd_attrition_evidence["outcome_contract"]
    return (
        '\n  <div class="slide-stage" id="slide-42" data-v6-playbook="true" data-v7-manager-timezone-proximity="true"><div class="slide-heading"><div>'
        '<h2 class="slide-title-text">Assigned office-site proximity to manager</h2>'
        '<p class="slide-subtitle">Same assigned site vs. different site by IANA time-zone offset · not residential distance</p>'
        '</div><span class="badge badge-info">Distribution + 2026 YTD attrition</span></div>'
        '<article class="card card-full v6-playbook-card manager-timezone-proximity-card">'
        '<div class="v6-definition-strip"><div><span class="v6-mini-label">Definition</span>'
        '<strong>Stored office_site match first; otherwise assigned-office time-zone difference of ≤4 h or &gt;4 h.</strong>'
        '</div><div><span class="v6-mini-label">Attrition label</span>'
        '<strong>2026 YTD voluntary attrition from '
        + html.escape(str(ytd_contract["baseline_snapshot"]))
        + ' through '
        + html.escape(str(ytd_contract["outcome_end_date"]))
        + '; observed and not annualized.</strong>'
        '</div></div><div class="v6-chart-area manager-timezone-chart-area">'
        '<article class="card chart-card manager-timezone-distribution-card"><div class="v6-panel-heading"><span>Latest assigned-site distribution</span><span>2026 YTD attrition · not annualized</span></div>'
        '<div class="bar-list">'
        + "".join(distribution_rows)
        + '</div><p class="chart-footer"><strong>'
        + f"{categorized:,} of {eligible:,} pairs ({categorized_share:.1f}%)"
        + '</strong> reconcile to the three categories. The remaining '
        + f"{unmapped:,} pairs are retained as mapping coverage, not assigned to a time-zone band."
        + '</p></article></div><div class="v6-source-line"><strong>Source:</strong> HRDA workforce snapshots + Qualcomm office catalog; IANA zone inferred from office coordinates. This is an assigned-office proxy only: it does not measure home location, physical presence, commute distance, travel time, or collaboration.</div></article></div>'
    )


def replace_residential_distance_with_manager_timezone_proximity(
    deck: str,
    distribution_evidence: dict[str, Any],
    ytd_attrition_evidence: dict[str, Any],
) -> str:
    return replace_stage_fragment(
        deck,
        42,
        build_manager_timezone_proximity_slide(distribution_evidence, ytd_attrition_evidence),
    )


def replace_nav28_39_with_annual_attrition(
    deck: str,
    direct_evidence: dict[str, Any],
    time_in_job_profile_time_in_role_evidence: dict[str, Any],
    promotion_evidence: dict[str, Any],
    within_team_evidence: dict[str, Any],
    colocation_evidence: dict[str, Any],
    layers_evidence: dict[str, Any],
) -> str:
    """Apply annual, Location-style labels to nav slides 28–39 (stage 29–41)."""
    updated = replace_time_in_job_profile_time_in_role(deck, time_in_job_profile_time_in_role_evidence)
    updated = replace_company_tenure_with_annual_attrition(updated, direct_evidence)
    updated = replace_promotion_time_with_annual_attrition(updated, promotion_evidence)
    updated = replace_promotion_history_with_annual_attrition(updated, promotion_evidence)
    updated = replace_entry_path_with_annual_attrition(updated, promotion_evidence)
    updated = replace_level_with_annual_attrition(updated, direct_evidence)
    updated = replace_level_grade_family_with_annual_attrition(updated, direct_evidence)
    updated = replace_manager_layers_with_annual_attrition(updated, layers_evidence)
    updated = replace_compensation_grade_with_annual_attrition(updated, direct_evidence)
    updated = replace_comp_ratio_with_annual_attrition(updated, direct_evidence)
    updated = replace_within_team_compensation_with_annual_attrition(updated, within_team_evidence)
    updated = replace_colocation_with_annual_attrition(updated, colocation_evidence)
    return remove_comp_ratio_six_month_history_script(updated)


def nav38_source_line(extra: str) -> str:
    return (
        '<div class="v6-source-line"><strong>Source:</strong> HRDA - '
        'hrda.post_hire_monthly_worker_dtls and hrda.all_terminations. '
        'Attrition baseline cohort: active regular employees at the 2025-08-24 snapshot. '
        'Annual voluntary attrition: strict VOLUNTARY exits from that same category cohort in '
        '(2025-08-24, 2026-08-23]. ' + html.escape(extra) + '</div>'
    )


def replace_nav38_plus_with_august_attrition(
    deck: str,
    evidence: dict[str, Any],
    *,
    allow_internal_subthreshold: bool = False,
) -> str:
    """Add fixed-August prospective attrition labels to the retained manager stages."""
    # Visible slide 36 / technical stage 43: office-site relationship.
    stage = stage_fragment(deck, 43)
    office_card = article_with_class(stage, "office-site-relationship-card")
    office_rows = nav38_metric_rows(evidence, "office_site_relationship")
    office_updated = update_bar_card_with_annual_attrition(
        office_card,
        nav38_card_mapping(office_card, office_rows),
    )
    stage = stage.replace(office_card, office_updated, 1)
    stage = set_stage_annual_badge(stage, "August trailing 12m")
    stage = stage.replace(
        "The comparison uses stored office-site fields only",
        "Stored office-site category at baseline; annual attrition follows the same employees for 12 months",
        1,
    )
    source_match = re.search(r'<div class="v6-source-line">.*?</div>', stage, re.S)
    require(source_match is not None, "Slide 43 is missing its source line.")
    stage = stage[:source_match.start()] + nav38_source_line("Office-site categories are assigned from the baseline employee-manager snapshot.") + stage[source_match.end():]
    deck = replace_stage_fragment(deck, 43, stage)

    # Visible slide 37 / technical stage 44: manager ratio bands.
    stage = stage_fragment(deck, 44)
    ratio_card = article_with_class(stage, "manager-score-distribution-card")
    ratio_rows = nav38_metric_rows(evidence, "manager_observed_expected")
    ratio_updated = update_bar_card_with_annual_attrition(
        ratio_card,
        nav38_card_mapping(ratio_card, ratio_rows),
    )
    stage = stage.replace(ratio_card, ratio_updated, 1)
    stage = set_stage_annual_badge(stage, "August trailing 12m")
    source_match = re.search(r'<div class="v6-source-line">.*?</div>', stage, re.S)
    require(source_match is not None, "Slide 44 is missing its source line.")
    stage = stage[:source_match.start()] + nav38_source_line("The visible manager counts are manager-level context; the rate denominator is the baseline direct-report cohort assigned to each band.") + stage[source_match.end():]
    deck = replace_stage_fragment(deck, 44, stage)

    # Visible slide 38 / technical stage 45: recent team exits.
    stage = stage_fragment(deck, 45)
    team_exit_card = article_with_class(stage, "manager-turnover-distribution-card")
    team_exit_rows = nav38_metric_rows(evidence, "recent_team_exits_under_manager")
    team_exit_updated = update_bar_card_with_annual_attrition(
        team_exit_card,
        nav38_card_mapping(team_exit_card, team_exit_rows),
    )
    stage = stage.replace(team_exit_card, team_exit_updated, 1)
    stage = set_stage_annual_badge(stage, "August trailing 12m")
    source_match = re.search(r'<div class="v6-source-line">.*?</div>', stage, re.S)
    require(source_match is not None, "Slide 45 is missing its source line.")
    stage = stage[:source_match.start()] + nav38_source_line("The rate is voluntary attrition among baseline employees grouped by recent team-exit context; it is not manager attrition.") + stage[source_match.end():]
    deck = replace_stage_fragment(deck, 45, stage)

    # Visible slide 39 / technical stage 46: above-average team-turnover signal.
    stage = stage_fragment(deck, 46)
    above_card = article_with_class(stage, "manager-turnover-distribution-card")
    above_rows = nav38_metric_rows(evidence, "above_average_team_turnover")
    above_updated = update_bar_card_with_annual_attrition(
        above_card,
        nav38_card_mapping(above_card, above_rows),
    )
    stage = stage.replace(above_card, above_updated, 1)
    stage = set_stage_annual_badge(stage, "August trailing 12m")
    source_match = re.search(r'<div class="v6-source-line">.*?</div>', stage, re.S)
    require(source_match is not None, "Slide 46 is missing its source line.")
    stage = stage[:source_match.start()] + nav38_source_line("Unknown remains a real category: insufficient manager history is not interpreted as signal 0.") + stage[source_match.end():]
    deck = replace_stage_fragment(deck, 46, stage)

    # Visible slide 40 / technical stage 47: manager leaving. The named
    # internal-analysis artifact may show the reconciled subthreshold rate;
    # shared-output publication status remains unchanged in the evidence.
    stage = stage_fragment(deck, 47)
    leaving_rows = nav38_metric_rows(evidence, "manager_leaving_baseline_6m")
    leaving_cards = []
    for match in re.finditer(r'<article\b(?P<attributes>[^>]*)>', stage, re.I):
        attrs = match.group("attributes")
        classes = re.search(r'\bclass="(?P<classes>[^"]*)"', attrs, re.I)
        if classes and "manager-leaving-card" in classes.group("classes").split():
            leaving_cards.append(stage[match.start():matching_tag_end(stage, "article", match.start())])
    require(len(leaving_cards) == 2, "Slide 47 must contain two manager-leaving cards.")
    primary_card = leaving_cards[0]
    sensitivity_card = leaving_cards[1]
    primary_updated = update_bar_card_with_annual_attrition(
        primary_card,
        nav38_card_mapping(primary_card, leaving_rows),
        unavailable_reasons={"Exposed (1+)": "the August 2025 exposed baseline cohort has fewer than 30 employees"},
        allow_internal_subthreshold=allow_internal_subthreshold,
    )
    sensitivity_updated = update_bar_card_with_annual_attrition(
        sensitivity_card,
        nav38_card_mapping(
            sensitivity_card,
            leaving_rows,
            {"No manager exits": "Not exposed", "1+ manager exit": "Exposed (1+)"},
        ),
        unavailable_reasons={"1+ manager exit": "the August 2025 exposed baseline cohort has fewer than 30 employees"},
        allow_internal_subthreshold=allow_internal_subthreshold,
    )
    stage = stage.replace(primary_card, primary_updated, 1).replace(sensitivity_card, sensitivity_updated, 1)
    stage = set_stage_annual_badge(stage, "August trailing 12m")
    manager_leaving_subtitle = (
        "The current distribution is descriptive; internal rates below n=30 are shown for descriptive review only"
        if allow_internal_subthreshold
        else "The current distribution is descriptive; a 12-month rate is shown only where its historical baseline cohort is estimable"
    )
    stage = stage.replace(
        "The flag records recent exposure to a manager's voluntary departure",
        manager_leaving_subtitle,
        1,
    )
    stage = stage.replace(
        "The flag records recent exposure to a manager&#x27;s voluntary departure",
        manager_leaving_subtitle,
        1,
    )
    source_match = re.search(r'<div class="v6-source-line">.*?</div>', stage, re.S)
    require(source_match is not None, "Slide 47 is missing its source line.")
    stage = stage[:source_match.start()] + nav38_source_line(
        "The exposed baseline bucket has n=4 and 1 voluntary exit; its 25.0% rate is shown only as a descriptive internal-analysis value under the named small-cell authorization, not as a stable estimate."
        if allow_internal_subthreshold
        else "The exposed baseline bucket is below n=30 and is intentionally shown as Not estimable; no rate is fabricated."
    ) + stage[source_match.end():]
    deck = replace_stage_fragment(deck, 47, stage)

    # Visible slide 41 / technical stage 48: replace inherited six-month pills
    # with two fixed-August annual rates while preserving the prevalence trend.
    stage = stage_fragment(deck, 48)
    manager_change_rows = nav38_metric_rows(evidence, "manager_change")
    manager_change_order = ("No manager change (0)", "Manager change (1)")
    manager_change_rates = [float(manager_change_rows[label]["annual_attrition_rate_percent"]) for label in manager_change_order]
    summary_parts = [
        '<span class="v4-inline-attrition-summary-label">August trailing 12m voluntary attrition:</span>'
    ]
    for label in manager_change_order:
        row = manager_change_rows[label]
        rate = float(row["annual_attrition_rate_percent"])
        cls = annual_rate_class(rate, manager_change_rates)
        summary_parts.append(
            '<span class="v7-annual-attrition v6-rate-pill v7-manager-change-summary-pill '
            + cls
            + '" title="Annual voluntary attrition for '
            + html.escape(label)
            + ': '
            + f"{rate:.1f}%"
            + '" aria-label="Annual voluntary attrition for '
            + html.escape(label)
            + ': '
            + f"{rate:.1f}%"
            + '">' + html.escape(label) + ' ' + f"{rate:.1f}%" + '</span>'
        )
    summary = '<div class="v4-inline-attrition-summary v7-manager-change-annual-summary" aria-label="August trailing 12-month voluntary attrition rates by manager-change flag">' + "".join(summary_parts) + '</div>'
    summary_match = re.search(r'<div class="v4-inline-attrition-summary".*?</div>', stage, re.S)
    require(summary_match is not None, "Slide 48 is missing its inherited attrition summary.")
    stage = stage[:summary_match.start()] + summary + stage[summary_match.end():]
    stage = set_stage_annual_badge(stage, "August trailing 12m")
    source_match = re.search(r'<div class="v6-source-line">.*?</div>', stage, re.S)
    require(source_match is not None, "Slide 48 is missing its source line.")
    stage = stage[:source_match.start()] + nav38_source_line("The displayed prevalence trend is historical context; the two pills use the fixed August 2025 baseline cohort and are prospective through August 2026.") + stage[source_match.end():]
    deck = replace_stage_fragment(deck, 48, stage)

    # Visible slide 42 / technical stage 49: four manager-change distributions.
    stage = stage_fragment(deck, 49)
    number_cards = []
    for match in re.finditer(r'<article\b(?P<attributes>[^>]*)>', stage, re.I):
        attrs = match.group("attributes")
        classes = re.search(r'\bclass="(?P<classes>[^"]*)"', attrs, re.I)
        if classes and "manager-change-distribution-card" in classes.group("classes").split():
            number_cards.append(stage[match.start():matching_tag_end(stage, "article", match.start())])
    require(len(number_cards) == 4, "Slide 49 must contain four manager-change distribution cards.")
    for card in number_cards:
        heading_match = re.search(r'<div class="v6-panel-heading"><span>(.*?)</span>', card, re.S)
        require(heading_match is not None, "A manager-change card is missing its metric heading.")
        metric = html.unescape(re.sub(r"<[^>]+>", "", heading_match.group(1))).strip()
        rows = nav38_metric_rows(evidence, metric)
        updated_card = update_bar_card_with_annual_attrition(
            card,
            nav38_card_mapping(card, rows),
        )
        stage = stage.replace(card, updated_card, 1)
    stage = set_stage_annual_badge(stage, "August trailing 12m")
    source_match = re.search(r'<div class="v6-source-line">.*?</div>', stage, re.S)
    require(source_match is not None, "Slide 49 is missing its source line.")
    stage = stage[:source_match.start()] + nav38_source_line("Each panel keeps its event-count definition; the annual label follows the corresponding category cohort rather than the current distribution month.") + stage[source_match.end():]
    deck = replace_stage_fragment(deck, 49, stage)

    # Visible slide 43 / technical stage 50: no time-safe prospective rate for
    # the latest recoverable talent-index cycle.
    stage = stage_fragment(deck, 50)
    talent_card = article_with_class(stage, "talent-index-distribution-card")
    talent_updated = update_bar_card_with_unavailable_annual_attrition(
        talent_card,
        "the latest recoverable talent-index cycle has no confirmed effective date at the August 2025 baseline",
        panel_subtitle="Distribution / annual attrition",
    )
    stage = stage.replace(talent_card, talent_updated, 1)
    stage = set_stage_annual_badge(stage, "Annual attrition: not estimable")
    source_match = re.search(r'<div class="v6-source-line">.*?</div>', stage, re.S)
    require(source_match is not None, "Slide 50 is missing its source line.")
    stage = stage[:source_match.start()] + nav38_source_line("Talent Index remains Not estimable: the stored cycle date is not confirmed as a knowledge-safe baseline feature, so a prospective rate could leak future information.") + stage[source_match.end():]
    deck = replace_stage_fragment(deck, 50, stage)

    # Visible slide 46 / technical stage 51: publish a transparent proxy card,
    # explicitly separated from the undefined target feature.
    stage = stage_fragment(deck, 51)
    proxy_rows = nav38_metric_rows(evidence, "major_inflection_proxy")
    proxy_order = ("No proxy movement", "1+ proxy movement")
    proxy_total = sum(int(proxy_rows[label]["employee_count"]) for label in proxy_order)
    proxy_max = max(int(proxy_rows[label]["employee_count"]) for label in proxy_order)
    proxy_rates = [float(proxy_rows[label]["annual_attrition_rate_percent"]) for label in proxy_order]
    proxy_bar_rows = []
    for label in proxy_order:
        row = proxy_rows[label]
        count = int(row["employee_count"])
        rate = float(row["annual_attrition_rate_percent"])
        pill_class = annual_rate_class(rate, proxy_rates)
        pill = (
            '<span class="v7-annual-attrition v6-rate-pill '
            + pill_class
            + '" title="Annual voluntary attrition for '
            + html.escape(label)
            + ': '
            + f"{rate:.1f}%"
            + '" aria-label="Annual voluntary attrition for '
            + html.escape(label)
            + ': '
            + f"{rate:.1f}%"
            + '">' + f"{rate:.1f}%" + '</span>'
        )
        proxy_bar_rows.append(
            '<div class="bar-row v4-inline-attrition-row"><div class="bar-label" title="'
            + html.escape(label)
            + '">'
            + html.escape(label)
            + '</div><div class="bar-track"><div class="bar-fill" style="width:'
            + f"{100 * count / proxy_max:.1f}%"
            + '"></div></div><div class="bar-value">'
            + f"{100 * count / proxy_total:.1f}% · {count:,}"
            + '</div>'
            + pill
            + '</div>'
        )
    proxy_card = (
        '<article class="card chart-card v6-distribution-only major-inflection-proxy-card">'
        '<div class="v6-panel-heading"><span>Baseline proxy movement distribution</span><span>Distribution / annual attrition</span></div>'
        '<div class="bar-list">' + "".join(proxy_bar_rows) + '</div>'
        '<p class="major-inflection-proxy-note"><strong>Proxy boundary:</strong> 1+ recorded movement is shown only as a transparent sensitivity proxy; it is not an approved definition of a major inflection point.</p>'
        '</article>'
    )
    state_match = re.search(r'<article\b[^>]*\bclass="card"[^>]*>\s*<div class="state-visual"', stage, re.I)
    require(state_match is not None, "Slide 51 is missing its not-estimable state card.")
    state_card = stage[state_match.start():matching_tag_end(stage, "article", state_match.start())]
    stage = stage.replace(state_card, proxy_card, 1)
    stage = set_stage_annual_badge(stage, "August trailing 12m proxy")
    stage = stage.replace(
        "Five change events are observable, but no approved rule defines a major change",
        "A transparent movement proxy is shown; no approved rule defines a major inflection",
        1,
    )
    source_match = re.search(r'<div class="v6-source-line">.*?</div>', stage, re.S)
    require(source_match is not None, "Slide 51 is missing its source line.")
    stage = stage[:source_match.start()] + nav38_source_line("The proxy uses manager_change, is_transferred, location_change, job_family_change, and cost_center_change; it is not the target major-inflection feature.") + stage[source_match.end():]
    deck = replace_stage_fragment(deck, 51, stage)

    # Visible slide 47 / technical stage 52: each ET field is a separate,
    # potentially overlapping baseline population.
    stage = stage_fragment(deck, 52)
    et_card = article_with_class(stage, "v6-distribution-only")
    et_rows = nav38_metric_rows(evidence, "et_field_presence")
    et_updated = update_bar_card_with_annual_attrition(
        et_card,
        nav38_card_mapping(et_card, et_rows),
    )
    note = '<p class="et-field-attrition-note"><strong>Read the labels as:</strong> annual voluntary attrition among baseline employees with each ET field populated. Fields are not mutually exclusive; these are not attrition rates for ET hierarchy levels.</p>'
    et_updated = et_updated.replace('</article>', note + '</article>', 1)
    stage = stage.replace(et_card, et_updated, 1)
    stage = set_stage_annual_badge(stage, "August trailing 12m")
    source_match = re.search(r'<div class="v6-source-line">.*?</div>', stage, re.S)
    require(source_match is not None, "Slide 52 is missing its source line.")
    stage = stage[:source_match.start()] + nav38_source_line("ET-field populations overlap; each annual label uses the field-populated baseline denominator independently.") + stage[source_match.end():]
    deck = replace_stage_fragment(deck, 52, stage)
    return deck


def qvoice_ytd_rate_row(label: str, metric: dict[str, Any], rates: list[float]) -> str:
    """Render a Location-style aggregate YTD rate, never an employee-level result."""
    denominator = int(metric["matched_employee_count"])
    exits = int(metric["voluntary_exit_count"])
    rate = float(metric["ytd_voluntary_attrition_rate_percent"])
    color_class = "attr-mid" if len(rates) == 1 else attrition_pill_class(rate, rates)
    maximum_rate = max(rates)
    require(maximum_rate > 0, "A QVoice rate rail requires a positive panel maximum.")
    relative_width = max(10.0, (rate / maximum_rate) * 100.0)
    return (
        '<div class="qvoice-ytd-rate-row"><div class="qvoice-ytd-rate-label" title="'
        + html.escape(label)
        + '">'
        + html.escape(label)
        + '</div><span class="v6-rate-pill '
        + color_class
        + '" title="2026 YTD voluntary attrition: '
        + f"{rate:.1f}%"
        + '" aria-label="2026 YTD voluntary attrition for '
        + html.escape(label)
        + ': '
        + f"{rate:.1f}%"
        + '">'
        + f"{rate:.1f}%"
        + '</span><div class="qvoice-ytd-rate-track" title="Relative to the highest attrition rate within this panel"><div class="qvoice-ytd-rate-fill '
        + color_class
        + '" style="width:'
        + f"{relative_width:.1f}%"
        + '"></div></div><span class="qvoice-ytd-cohort">n='
        + f"{denominator:,} / {exits:,} exits"
        + "</span></div>"
    )


def qvoice_ytd_attrition_card(title: str, groups: list[tuple[str, dict[str, Any]]], window: str) -> str:
    rates = [float(metric["ytd_voluntary_attrition_rate_percent"]) for _, metric in groups]
    require(rates, "A QVoice attrition panel requires at least one rate.")
    return (
        '<article class="card chart-card qvoice-ytd-attrition-card qvoice-ytd-groups-'
        + str(len(groups))
        + '" data-qvoice-ytd-layout="rate-rails">'
        '<div class="v6-panel-heading"><span>'
        + html.escape(title)
        + '</span><span>2026 YTD</span></div>'
        '<p class="qvoice-ytd-window"><strong>Voluntary attrition</strong> · '
        + html.escape(window)
        + ' · not annualized</p><div class="qvoice-ytd-rate-list">'
        + "".join(qvoice_ytd_rate_row(label, metric, rates) for label, metric in groups)
        + '</div><p class="qvoice-ytd-color-key"><i class="attr-low"></i>lowest · <i class="attr-mid"></i>middle · <i class="attr-high"></i>highest · rail length is relative</p>'
        '</article>'
    )


def ordered_score_bands(rows: dict[str, dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    """Keep the visual score progression stable even when the source set order changes."""
    def key(label: str) -> tuple[int, str]:
        if label.startswith("<"):
            return (0, label)
        if label.startswith("100"):
            return (100, label)
        match = re.search(r"\d+", label)
        return (int(match.group(0)) if match else 99, label)

    return [(label, rows[label]) for label in sorted(rows, key=key)]


def ordered_z_score_bands(rows: dict[str, dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    """Order the standardized-score bands low to high without altering stored labels."""
    normalized_minus = lambda label: label.replace("−", "-").replace("âˆ’", "-")

    def key(label: str) -> tuple[float, str]:
        text = normalized_minus(label)
        if text.startswith("<"):
            return (-2.0, label)
        if "1.0" in text and "to" not in text:
            return (2.0, label)
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        return (float(match.group(0)) if match else 99.0, label)

    return [(label, rows[label]) for label in sorted(rows, key=key)]


def replace_qvoice_ytd_attrition_content(deck: str, evidence: dict[str, Any]) -> str:
    """Add one compact 2026-YTD attrition panel to each QVoice slide 20–27.

    The original distribution remains visible.  Rows use only pre-aggregated
    group membership and the fixed pre-wave cohort; no raw response/comment
    content or employee identifiers reaches the deck.
    """
    slides = evidence["slides"]
    window = evidence["outcome_contract"]["outcome_window"]
    panels: dict[int, tuple[str, list[tuple[str, dict[str, Any]]]]] = {
        20: ("Comment-topic cohorts", list(slides["20"].items())),
        21: ("Improvement-theme cohorts", list(slides["21"].items())),
        22: ("Participation-proxy cohorts", list(slides["22"].items())),
        23: (
            "Stored Intent-to-Stay values",
            [
                ("See myself at Qualcomm · stored 0", slides["23"]["intent_see_myself"]["0"]),
                ("See myself at Qualcomm · stored 1", slides["23"]["intent_see_myself"]["1"]),
                ("Rarely look for a new job · stored 0", slides["23"]["intent_rarely_look"]["0"]),
                ("Rarely look for a new job · stored 1", slides["23"]["intent_rarely_look"]["1"]),
            ],
        ),
        24: ("Career-goals stored values", [("Stored value 0", slides["24"]["0"]), ("Stored value 1", slides["24"]["1"])]),
        25: ("Comparable-score bands", ordered_score_bands(slides["25"])),
        26: ("Heartbeat-eligible cohort", [("Heartbeat eligible", slides["26"]["Heartbeat eligible"])]),
        27: ("Within-region standardized-score bands", ordered_z_score_bands(slides["27"])),
    }
    subtitles = {
        20: "Jan-2026 comment-topic cohorts retain their distribution and add voluntary attrition YTD; topic mentions do not prove sentiment or causality",
        21: "Jan-2026 improvement-theme cohorts retain their distribution and add voluntary attrition YTD; themes are not individual attrition risk",
        22: "Participation-proxy groups retain their distribution and add voluntary attrition YTD; no QVoice row is not confirmed non-response",
        23: "Jan-2026 stored 0/1 response groups retain coverage and show voluntary attrition YTD without inferring scale direction beyond the stored value",
        24: "Jan-2026 stored 0/1 Career Goals groups show voluntary attrition YTD; 2023 still needs header mapping before it can enter this calculation",
        25: "The score covers respondents who answered all 33 common items; 2026 bands now show voluntary attrition YTD",
        26: "The heartbeat display uses item-specific denominators; the YTD rate therefore applies to the single heartbeat-eligible cohort, not to each item",
        27: "Scores retain their within-region interpretation; the Jan-2026 standardized-score bands now show voluntary attrition YTD",
    }

    updated = deck
    for slide_number, (title, groups) in panels.items():
        next_stage_pattern = r'(?=\n\s*<div class="slide-stage"|\n\s*<script|\Z)'
        pattern = rf'(<div class="slide-stage" id="slide-{slide_number}".*?){next_stage_pattern}'

        def replace_stage(match: re.Match[str], *, number: int = slide_number, panel_title: str = title, panel_groups: list[tuple[str, dict[str, Any]]] = groups) -> str:
            stage = match.group(1)
            pane_start = stage.find('<div class="two-pane">')
            require(pane_start >= 0, f"QVoice slide {number} is missing its distribution pane.")
            pane_end = matching_tag_end(stage, "div", pane_start)
            require("qvoice-ytd-attrition-card" not in stage, f"QVoice slide {number} already contains a YTD attrition panel.")
            panel = qvoice_ytd_attrition_card(panel_title, panel_groups, window)
            stage = stage[: pane_end - len("</div>")] + panel + stage[pane_end - len("</div>") :]
            stage, replacements = re.subn(
                r'<span class="badge badge-(?:neutral|info)">(?:Distribution|Attrition not estimable)</span>',
                '<span class="badge badge-info">2026 YTD attrition</span>',
                stage,
                count=1,
            )
            require(replacements == 1, f"QVoice slide {number} is missing its V6 badge.")
            old_subtitle = re.search(r'<p class="slide-subtitle">.*?</p>', stage, flags=re.S)
            require(old_subtitle is not None, f"QVoice slide {number} is missing its subtitle.")
            stage = stage[: old_subtitle.start()] + '<p class="slide-subtitle">' + subtitles[number] + '</p>' + stage[old_subtitle.end() :]
            stage = stage.replace(
                "No publishable time-aligned attrition estimate is available.",
                "A time-aligned 2026 YTD voluntary-attrition cohort is shown above.",
            )
            source_match = re.search(r'(<div class="v6-source-line">.*?)(</div>)', stage, flags=re.S)
            require(source_match is not None, f"QVoice slide {number} is missing its source line.")
            source_addition = ' 2026 YTD voluntary attrition: pre-wave active Regular cohort (28 Dec 2025), strict VOLUNTARY exits in ' + window + '; not annualized.'
            stage = stage[: source_match.start()] + source_match.group(1) + source_addition + source_match.group(2) + stage[source_match.end() :]
            stage = stage.replace(f'<div class="slide-stage" id="slide-{number}"', f'<div class="slide-stage" id="slide-{number}" data-v7-qvoice-ytd-attrition="true"', 1)
            return stage

        updated, replacements = re.subn(pattern, replace_stage, updated, count=1, flags=re.S)
        require(replacements == 1, f"Could not locate QVoice slide {slide_number}.")
    return updated


def qvoice_wave_attrition_label(row: dict[str, Any], all_rates: list[float]) -> str:
    """Render one compact, wave-level label without counts, exits, or a rail."""
    rate = float(row["voluntary_attrition_rate_percent"])
    label = str(row["label"])
    pill_class = attrition_pill_class(rate, all_rates)
    period = "annual" if row["outcome_type"] == "annual_12m" else "YTD"
    return (
        '<span class="qvoice-wave-attrition v6-rate-pill '
        + pill_class
        + '" title="'
        + html.escape(f"{period} voluntary attrition: {rate:.1f}%")
        + '" aria-label="'
        + html.escape(f"{period} voluntary attrition for {row['wave']}: {rate:.1f}%")
        + '">'
        + html.escape(label)
        + '</span>'
    )


def replace_qvoice_wave_attrition_labels(deck: str, evidence: dict[str, Any]) -> str:
    """Place four historical/QTD labels beside their matching QVoice table waves."""
    rows = list(evidence["waves"])
    rates = [float(row["voluntary_attrition_rate_percent"]) for row in rows]
    require(len(rows) == 4 and len(rates) == 4, "QVoice table labels require four wave rates.")
    stage = stage_fragment(deck, 20)
    require("qvoice-ytd-attrition-card" not in stage and "qvoice-ytd-rate-track" not in stage, "QVoice slide 20 must not contain a right-side attrition rail.")
    require(stage.count('<table class="qvoice-comment-table">') == 1, "QVoice slide 20 comment table is missing.")
    for row in rows:
        wave = str(row["wave"])
        label = qvoice_wave_attrition_label(row, rates)
        pattern = rf'<tr><td>{re.escape(wave)}</td>(.*?)</tr>'
        replacement = '<tr><td><span class="qvoice-wave-name">' + html.escape(wave) + '</span>' + label + '</td>' + r'\1</tr>'
        stage, replacements = re.subn(pattern, replacement, stage, count=1, flags=re.S)
        require(replacements == 1, f"QVoice table is missing the {wave} row.")
    source_match = re.search(r'(<div class="v6-source-line">.*?)(</div>)', stage, flags=re.S)
    require(source_match is not None, "QVoice slide 20 source line is missing.")
    source_addition = " Attrition labels: annual voluntary attrition after each historical wave-month start; Jan-2026 is voluntary attrition YTD from 07 Jan through 27 Sep 2026."
    stage = stage[: source_match.start()] + source_match.group(1) + source_addition + source_match.group(2) + stage[source_match.end() :]
    stage = stage.replace(
        '<div class="slide-stage" id="slide-20"',
        '<div class="slide-stage" id="slide-20" data-v7-qvoice-wave-attrition="direct-labels"',
        1,
    )
    return replace_stage_fragment(deck, 20, stage)


def qvoice_inline_attrition_pill(label: str, metric: dict[str, Any], rates: list[float]) -> str:
    """Render one compact, color-coded QVoice YTD attrition pill."""
    rate = float(metric["ytd_voluntary_attrition_rate_percent"])
    pill_class = "attr-mid" if len(set(rates)) <= 1 else attrition_pill_class(rate, rates)
    return (
        '<span class="qvoice-inline-attrition-pill v6-rate-pill '
        + pill_class
        + '" title="2026 YTD voluntary attrition for '
        + html.escape(label, quote=True)
        + ': '
        + f"{rate:.1f}%"
        + '" aria-label="2026 YTD voluntary attrition for '
        + html.escape(label, quote=True)
        + ': '
        + f"{rate:.1f}%"
        + '">'
        + f"{rate:.1f}%"
        + "</span>"
    )


def qvoice_inline_attrition_row(label: str, metric: dict[str, Any], rates: list[float]) -> str:
    denominator = int(metric["matched_employee_count"])
    exits = int(metric["voluntary_exit_count"])
    return (
        '<div class="qvoice-inline-attrition-row"><span class="qvoice-inline-attrition-label">'
        + html.escape(label)
        + '</span>'
        + qvoice_inline_attrition_pill(label, metric, rates)
        + '<span class="qvoice-inline-attrition-cohort">n='
        + f"{denominator:,} / {exits:,} exits"
        + "</span></div>"
    )


def qvoice_inline_attrition_panel(title: str, groups: list[tuple[str, dict[str, Any]]]) -> str:
    rates = [float(metric["ytd_voluntary_attrition_rate_percent"]) for _, metric in groups]
    return (
        '<section class="qvoice-inline-attrition-panel" data-qvoice-inline-attrition="2026-ytd">'
        '<div class="qvoice-inline-attrition-head"><strong>'
        + html.escape(title)
        + '</strong><span>2026 YTD · not annualized</span></div>'
        '<div class="qvoice-inline-attrition-list">'
        + "".join(qvoice_inline_attrition_row(label, metric, rates) for label, metric in groups)
        + '</div><div class="qvoice-inline-attrition-key"><span><i class="attr-low"></i>lower</span><span><i class="attr-mid"></i>middle</span><span><i class="attr-high"></i>higher</span><span>Color is relative within this slide.</span></div>'
        '</section>'
    )


def append_qvoice_inline_attrition_panel(stage: str, card_class: str, panel: str) -> str:
    card = article_with_class(stage, card_class)
    require('data-qvoice-inline-attrition="2026-ytd"' not in card, f"QVoice {card_class} already contains an inline attrition panel.")
    insertion = card.rfind("</article>")
    require(insertion >= 0, f"QVoice {card_class} has no closing article tag.")
    updated_card = card[:insertion] + panel + card[insertion:]
    return stage.replace(card, updated_card, 1)


def replace_qvoice_open_text_attrition_pills(deck: str, evidence: dict[str, Any]) -> str:
    """Color the eight existing open-text attrition labels on navigation slide 18."""
    stage = stage_fragment(deck, 20)
    if 'data-v7-qvoice-open-text-no-comment-attrition="true"' in stage:
        return deck
    require('data-v7-qvoice-open-text-attrition-pills="true"' not in stage, "QVoice slide 18 already contains colored attrition pills.")
    expected_rates = [
        float(group["voluntary_attrition_rate_percent"])
        for wave in evidence["waves"]
        for group in wave["groups"]
    ]
    all_rates = list(expected_rates)
    matches = list(re.finditer(r'<span>Attrition (?P<rate>[0-9]+(?:\.[0-9]+)?)%</span>', stage))
    require(len(matches) == len(expected_rates) == 8, "QVoice slide 18 must expose eight attrition labels before coloring them.")
    position = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal position
        rate = float(match.group("rate"))
        expected = expected_rates[position]
        require(abs(rate - round(expected, 1)) < 0.00011, "QVoice slide 18 attrition labels do not reconcile to the evidence order.")
        label = f"QVoice open-text group {position + 1}"
        pill_class = attrition_pill_class(expected, all_rates) if len(set(all_rates)) > 1 else "attr-mid"
        position += 1
        return (
            '<span class="qvoice18-attrition-pill v6-rate-pill '
            + pill_class
            + '" title="Voluntary attrition for '
            + label
            + ': '
            + f"{rate:.1f}%"
            + '" aria-label="Voluntary attrition for '
            + label
            + ': '
            + f"{rate:.1f}%"
            + '">'
            + f"{rate:.1f}%"
            + "</span>"
        )

    stage, replacements = re.subn(
        r'<span>Attrition (?P<rate>[0-9]+(?:\.[0-9]+)?)%</span>',
        replace,
        stage,
        count=8,
    )
    require(replacements == 8 and position == 8, "QVoice slide 18 colored attrition pills were incomplete.")
    stage = stage.replace(
        '<div class="slide-stage" id="slide-20"',
        '<div class="slide-stage" id="slide-20" data-v7-qvoice-open-text-attrition-pills="true"',
        1,
    )
    return replace_stage_fragment(deck, 20, stage)


def build_qvoice_retention_theme_stage(evidence: dict[str, Any]) -> str:
    """Build navigation slide 19 with the approved Region-style theme layout."""
    rows = list(evidence["rows"])
    denominator = int(evidence["distribution_denominator"])
    rates = [float(row["trailing_12m_voluntary_attrition_rate_percent"]) for row in rows]
    maximum_distribution = max(float(row["distribution_percent"]) for row in rows)
    window = str(evidence["outcome_contract"]["window"])
    rendered_rows: list[str] = []
    for row in rows:
        label = str(row["theme"])
        distribution_pct = float(row["distribution_percent"])
        distribution_count = int(row["distribution_count"])
        matched = int(row["matched_employee_count"])
        exits = int(row["voluntary_exit_count"])
        rate = float(row["trailing_12m_voluntary_attrition_rate_percent"])
        relative_width = max(4.0, 100.0 * distribution_pct / maximum_distribution)
        pill_class = attrition_pill_class(rate, rates)
        tooltip = (
            f"{label}: {distribution_pct:.1f}% of Jan-2026 improvement commenters; "
            f"trailing 12-month voluntary attrition {rate:.1f}%; n={matched:,}; exits={exits:,}"
        )
        rendered_rows.append(
            '<div class="qv19-row">'
            f'<div class="qv19-label">{html.escape(label)}</div>'
            f'<div class="qv19-track" title="{html.escape(tooltip, quote=True)}" aria-label="{html.escape(tooltip, quote=True)}">'
            f'<div class="qv19-fill" style="width:{relative_width:.4f}%"></div></div>'
            f'<div class="qv19-attrition-cell"><span class="qv19-distribution">{distribution_pct:.1f}% · n={distribution_count:,}</span>'
            f'<span class="qv19-attrition-pill {pill_class}" title="{html.escape(tooltip, quote=True)}" aria-label="{html.escape(tooltip, quote=True)}">{rate:.1f}%</span></div>'
            '</div>'
        )
    return (
        '<div class="slide-stage" id="slide-21" data-v6-playbook="true" data-v7-qvoice-retention-theme-attrition="august-trailing-12m">'
        '<div class="slide-heading"><div><h2 class="slide-title-text">QVoice comments by theme</h2>'
        '<p class="slide-subtitle">Jan-2026 improvement themes · distribution and trailing 12-month voluntary attrition through August 2026</p>'
        '</div><span class="badge badge-info">Distribution + 12-month attrition</span></div>'
        '<article class="card card-full qv19-card">'
        '<div class="qv19-intro">'
        '<div class="qv19-intro-block"><span class="qv19-eyebrow">Population</span>'
        '<strong>Employees with at least one selected improvement comment</strong></div>'
        '<div class="qv19-intro-block"><span class="qv19-eyebrow">Reading the chart</span>'
        '<strong>Bar = share of commenters · pill = trailing 12-month attrition</strong></div></div>'
        '<div class="qv19-panel-head"><strong>What employees commented about</strong>'
        f'<span>Jan-2026 · n = {denominator:,} commenters</span></div>'
        '<div class="qv19-column-head" aria-hidden="true"><span>Comment theme</span><span>Distribution</span><span>12-month attrition</span></div>'
        '<div class="qv19-list">'
        + "".join(rendered_rows)
        + '</div><div class="qv19-unpublishable">'
        '<strong>Explicit intent to leave</strong>'
        '<span>Shown separately; the category is too small to publish an attrition estimate.</span>'
        '<b>Not publishable (n&lt;30)</b></div>'
        '<div class="qv19-footer">'
        '<span><strong>Important:</strong> Themes can overlap; distribution bars do not sum to 100%.</span>'
        f'<span><strong>Attrition:</strong> voluntary exits in {html.escape(window)} among the matched August-2025 cohort.</span>'
        '</div></article></div>'
    )


def replace_qvoice_retention_theme_stage(deck: str, evidence: dict[str, Any]) -> str:
    """Make the approved draft layout permanent in the main builder output."""
    replacement = build_qvoice_retention_theme_stage(evidence)
    require('data-v7-qvoice-retention-theme-attrition="august-trailing-12m"' in replacement, "QVoice retention-theme marker is missing.")
    require(replacement.count('class="qv19-row"') == 5, "QVoice retention-theme visual must show five theme rows.")
    require(replacement.count('qv19-attrition-pill') == 5, "QVoice retention-theme visual must show five attrition pills.")
    return replace_stage_fragment(deck, 21, replacement)


def replace_qvoice_ytd_inline_attrition_labels(deck: str, evidence: dict[str, Any]) -> str:
    """Add colored 2026-YTD attrition labels to the remaining QVoice distributions."""
    slides = evidence["slides"]
    window = evidence["outcome_contract"]["outcome_window"]

    stage = stage_fragment(deck, 21)
    require('data-v7-qvoice-inline-attrition="true"' not in stage, "QVoice slide 19 already contains inline attrition labels.")
    retention_order = list(evidence["validation"]["retention_display_order"])
    retention_groups = [(label, slides["21"][label]) for label in retention_order]
    retention_rates = [float(metric["ytd_voluntary_attrition_rate_percent"]) for _, metric in retention_groups]
    for label, metric in retention_groups:
        pattern = re.compile(
            r'(<div class="retention-theme-label">'
            + re.escape(html.escape(label))
            + r'</div>.*?<div class="retention-theme-value">)(.*?)(</div>)',
            flags=re.S,
        )
        replacement = r'\1' + r'\2' + qvoice_inline_attrition_pill(label, metric, retention_rates) + r'\3'
        stage, replacements = pattern.subn(replacement, stage, count=1)
        require(replacements == 1, f"QVoice slide 19 is missing the {label!r} theme row.")
    stage = stage.replace(
        '<div class="slide-stage" id="slide-21"',
        '<div class="slide-stage" id="slide-21" data-v7-qvoice-inline-attrition="true"',
        1,
    )
    stage = re.sub(
        r'<span class="badge badge-(?:neutral|info)">Distribution</span>',
        '<span class="badge badge-info">2026 YTD attrition</span>',
        stage,
        count=1,
    )
    stage = stage.replace(
        '<span class="badge badge-info">2026 YTD attrition</span>',
        '<span class="badge badge-info">2026 YTD attrition (not annualized)</span>',
        1,
    )
    deck = replace_stage_fragment(deck, 21, stage)

    intent_groups = [
        ("See myself at Qualcomm · stored 0", slides["23"]["intent_see_myself"]["0"]),
        ("See myself at Qualcomm · stored 1", slides["23"]["intent_see_myself"]["1"]),
        ("Rarely look for a new job · stored 0", slides["23"]["intent_rarely_look"]["0"]),
        ("Rarely look for a new job · stored 1", slides["23"]["intent_rarely_look"]["1"]),
    ]
    career_groups = [(f"Stored value {label}", slides["24"][label]) for label in ("0", "1")]
    score_groups = ordered_score_bands(slides["25"])
    standardized_groups = ordered_z_score_bands(slides["27"])
    panel_specs = (
        (23, "chart-card", "2026 YTD attrition by stored Intent-to-Stay response", intent_groups),
        (24, "chart-card", "2026 YTD attrition by stored Career Goals response", career_groups),
        (25, "qvoice-comparable-card", "2026 YTD attrition by comparable-score band", score_groups),
        (27, "qvoice-normalized-region-card", "2026 YTD attrition by standardized-score band", standardized_groups),
    )
    for stage_number, card_class, title, groups in panel_specs:
        stage = stage_fragment(deck, stage_number)
        require('data-v7-qvoice-inline-attrition="true"' not in stage, f"QVoice slide {stage_number} already contains inline attrition labels.")
        stage = append_qvoice_inline_attrition_panel(stage, card_class, qvoice_inline_attrition_panel(title, groups))
        stage = stage.replace(
            f'<div class="slide-stage" id="slide-{stage_number}"',
            f'<div class="slide-stage" id="slide-{stage_number}" data-v7-qvoice-inline-attrition="true"',
            1,
        )
        stage = re.sub(
            r'<span class="badge badge-(?:neutral|info)">(?:Distribution|Attrition not estimable)</span>',
            '<span class="badge badge-info">2026 YTD attrition</span>',
            stage,
            count=1,
        )
        stage = stage.replace(
            "No publishable time-aligned attrition estimate is available.",
            "2026 YTD voluntary attrition is shown for the displayed groups; not annualized.",
            1,
        )
        source_marker = '<div class="v6-source-line">'
        require(source_marker in stage, f"QVoice slide {stage_number} is missing its source line.")
        stage = stage.replace(source_marker, source_marker + f"2026 YTD voluntary attrition window: {html.escape(window)}; not annualized. ", 1)
        deck = replace_stage_fragment(deck, stage_number, stage)
    return deck


def clarify_qvoice_comparable_score_bands(deck: str) -> str:
    """Make the comparable-score bands self-explanatory in navigation slide 23."""
    stage = stage_fragment(deck, 25)
    require('qvoice-comparable-card' in stage, "QVoice comparable-score card is missing.")
    band_labels = {
        "<50": "<50% favorable",
        "50–69": "50–69% favorable",
        "70–79": "70–79% favorable",
        "80–89": "80–89% favorable",
        "90–99": "90–99% favorable",
        "100": "100% favorable",
    }
    for old, new in band_labels.items():
        old_escaped = html.escape(old, quote=True)
        new_escaped = html.escape(new, quote=True)
        stage = stage.replace(f'title="{old_escaped}:', f'title="{new_escaped}:')
        stage = stage.replace(f'for {old_escaped}:', f'for {new_escaped}:')
        stage = stage.replace(f'>{old_escaped}</span>', f'>{new_escaped}</span>')
    stage = stage.replace(
        'Each bar sums to 100.0% of respondents included in the wave.',
        "Each bar sums to 100.0% of respondents included in the wave. Individual score = % of the 33 comparable items answered favorably.",
        1,
    )
    stage = stage.replace(
        'Denominator by wave: respondents with <strong>33/33 valid comparable items</strong>. Bands reconcile exactly to each n; no perception is inferred for the entire workforce.',
        'Denominator by wave: respondents with <strong>33/33 valid comparable items</strong>. Individual score = 100 * favorable items / 33. Bands reconcile exactly to each n; no perception is inferred for the entire workforce.',
        1,
    )
    require(html.escape('<50% favorable') in stage and html.escape('100% favorable') in stage, "QVoice comparable-score bands were not clarified.")
    require('Individual score = 100 * favorable items / 33.' in stage, "QVoice comparable-score formula note is missing.")
    return replace_stage_fragment(deck, 25, stage)


def qvoice_trailing_12m_rate_row(label: str, metric: dict[str, Any]) -> str:
    rate = float(metric["trailing_12m_voluntary_attrition_rate_percent"])
    denominator = int(metric["matched_employee_count"])
    exits = int(metric["voluntary_exit_count"])
    return (
        '<div class="qvoice-ytd-rate-row">'
        '<div class="qvoice-ytd-rate-label">'
        + html.escape(label)
        + '</div><span class="v6-rate-pill attr-mid" title="Trailing 12-month voluntary attrition: '
        + f"{rate:.1f}%"
        + '" aria-label="Trailing 12-month voluntary attrition: '
        + f"{rate:.1f}%"
        + '">'
        + f"{rate:.1f}%"
        + '</span><div class="qvoice-ytd-rate-track" title="Trailing 12-month voluntary attrition rate"><div class="qvoice-ytd-rate-fill attr-mid" style="width:100.0%"></div></div><span class="qvoice-ytd-cohort">n='
        + f"{denominator:,} / {exits:,} exits"
        + "</span></div>"
    )


def qvoice_trailing_12m_attrition_card(title: str, metric: dict[str, Any], window: str) -> str:
    return (
        '<article class="card chart-card qvoice-ytd-attrition-card qvoice-ytd-groups-1" data-qvoice-attrition-layout="rate-rails">'
        '<div class="v6-panel-heading"><span>'
        + html.escape(title)
        + '</span><span>August 2026 cutoff</span></div>'
        '<p class="qvoice-ytd-window"><strong>Voluntary attrition</strong> · '
        + html.escape(window)
        + ' Â· trailing 12 months</p><div class="qvoice-ytd-rate-list">'
        + qvoice_trailing_12m_rate_row("Heartbeat eligible", metric)
        + '</div><p class="qvoice-ytd-color-key">Rate is calculated as voluntary exits divided by the matched heartbeat-eligible cohort.</p>'
        '</article>'
    )


def replace_qvoice_heartbeat_relative_sign_ytd_attrition(deck: str, evidence: dict[str, Any]) -> str:
    """Replace the legacy top-five heartbeat bars with the approved top-three sign view."""
    panels = list(evidence["slide"]["panels"])
    all_segments = [segment for panel in panels for question in panel["questions"] for segment in question["segments"]]
    rates = [float(segment["ytd_voluntary_attrition_rate_percent"]) for segment in all_segments]
    require(len(panels) == 2 and len(all_segments) == 18, "Heartbeat visual requires two panels and eighteen sign rows.")

    sign_css = {1: "above", 0: "equal", -1: "below"}

    def render_segment(question_id: str, segment: dict[str, Any]) -> str:
        sign = int(segment["sign"])
        share = float(segment["share_of_valid_responses_percent"])
        rate = float(segment["ytd_voluntary_attrition_rate_percent"])
        matched = int(segment["matched_employee_count"])
        exits = int(segment["voluntary_exit_count"])
        label = f"{segment['sign_symbol']} · {segment['sign_label']}"
        tooltip = (
            f"{question_id} {label}: {share:.1f}% of valid responses; post-survey voluntary attrition YTD "
            f"{rate:.1f}%; n={matched:,}; exits={exits:,}."
        )
        return (
            '<div class="qvoice-heartbeat-sign-row" title="'
            + html.escape(tooltip, quote=True)
            + '" aria-label="'
            + html.escape(tooltip, quote=True)
            + '"><span class="qvoice-heartbeat-sign-label '
            + sign_css[sign]
            + '">' + html.escape(label)
            + '</span><div class="qvoice-heartbeat-track"><div class="qvoice-heartbeat-fill '
            + sign_css[sign]
            + '" style="width:' + f"{share:.1f}%"
            + '"></div></div><strong class="qvoice-heartbeat-share">'
            + f"{share:.1f}%"
            + '</strong><span class="qvoice-heartbeat-attrition v6-rate-pill '
            + attrition_pill_class(rate, rates)
            + '">' + f"{rate:.1f}%"
            + '</span></div>'
        )

    def render_question(question: dict[str, Any]) -> str:
        question_id = str(question["question_id"])
        question_label = str(question["question_label"])
        sign_rows = "".join(render_segment(question_id, segment) for segment in question["segments"])
        return (
            '<article class="qvoice-heartbeat-question"><div class="qvoice-heartbeat-question-heading">'
            '<div><strong>' + html.escape(question_id) + '</strong><span title="'
            + html.escape(question_label, quote=True) + '">' + html.escape(question_label)
            + '</span></div><span class="qvoice-heartbeat-rank">#'
            + str(int(question["rank"]))
            + '</span></div><div class="qvoice-heartbeat-sign-list">'
            + sign_rows + '</div></article>'
        )

    panel_html: list[str] = []
    for panel in panels:
        ranking_symbol = str(panel["ranking_symbol"])
        ranking_label = str(panel["ranking_label"])
        panel_html.append(
            '<section class="qvoice-heartbeat-panel"><div class="qvoice-heartbeat-panel-heading"><div><h3>Top 3 · '
            + html.escape(ranking_symbol + " " + ranking_label)
            + '</h3><p>Ranked by this relative-response share.</p></div><span>Share&nbsp;&nbsp; Attrition YTD</span></div>'
            + '<div class="qvoice-heartbeat-question-list">'
            + "".join(render_question(question) for question in panel["questions"])
            + '</div></section>'
        )

    heartbeat_css = '''<style id="qvoice-heartbeat-relative-sign-style">
    #slide-26 .v6-playbook-card { gap:8px; }
    #slide-26 .v6-definition-strip { padding:7px 12px; }
    #slide-26 .v6-chart-area { min-height:0; display:flex; flex:1; }
    #slide-26 .qvoice-heartbeat-card { width:100%; min-height:0; padding:10px 13px; gap:7px; }
    #slide-26 .qvoice-heartbeat-card .card-title { margin:0; padding-bottom:4px; }
    #slide-26 .qvoice-heartbeat-intro { margin:0; font-size:10px; line-height:1.25; color:var(--text-muted); }
    #slide-26 .qvoice-heartbeat-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; min-height:0; flex:1; }
    #slide-26 .qvoice-heartbeat-panel { min-width:0; min-height:0; display:flex; flex-direction:column; gap:6px; padding:8px; border:1px solid var(--border-subtle); border-radius:9px; background:color-mix(in oklab, var(--bg-surface) 82%, transparent); }
    #slide-26 .qvoice-heartbeat-panel-heading { display:flex; justify-content:space-between; align-items:flex-start; gap:8px; padding:0 2px 5px; border-bottom:1px solid var(--border-subtle); }
    #slide-26 .qvoice-heartbeat-panel-heading h3 { margin:0; font-size:11px; line-height:1.2; color:var(--text-main); }
    #slide-26 .qvoice-heartbeat-panel-heading p { margin:2px 0 0; font-size:8.5px; line-height:1.15; color:var(--text-muted); }
    #slide-26 .qvoice-heartbeat-panel-heading > span { flex:0 0 auto; padding-top:2px; font-size:8px; font-weight:700; letter-spacing:.02em; color:var(--text-muted); white-space:nowrap; }
    #slide-26 .qvoice-heartbeat-question-list { display:flex; flex:1; flex-direction:column; gap:6px; min-height:0; }
    #slide-26 .qvoice-heartbeat-question { flex:1 1 0; display:flex; flex-direction:column; justify-content:center; padding:8px 7px; border:1px solid var(--border-subtle); border-radius:7px; background:color-mix(in oklab, var(--bg-body) 48%, var(--bg-surface)); }
    #slide-26 .qvoice-heartbeat-question-heading { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:5px; }
    #slide-26 .qvoice-heartbeat-question-heading > div { min-width:0; display:flex; align-items:baseline; gap:5px; }
    #slide-26 .qvoice-heartbeat-question-heading strong { font-size:11px; color:var(--accent); }
    #slide-26 .qvoice-heartbeat-question-heading span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:9.5px; font-weight:700; color:var(--text-main); }
    #slide-26 .qvoice-heartbeat-question-heading .qvoice-heartbeat-rank { flex:0 0 auto; color:var(--text-muted); font-size:8px; font-weight:700; }
    #slide-26 .qvoice-heartbeat-sign-list { display:flex; flex-direction:column; gap:5px; }
    #slide-26 .qvoice-heartbeat-sign-row { display:grid; grid-template-columns:132px minmax(0,1fr) 37px 43px; align-items:center; gap:5px; min-width:0; }
    #slide-26 .qvoice-heartbeat-sign-label { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:9px; line-height:1; color:var(--text-muted); }
    #slide-26 .qvoice-heartbeat-sign-label.above { color:var(--accent); font-weight:700; }
    #slide-26 .qvoice-heartbeat-sign-label.below { color:color-mix(in oklab, #b45309 84%, var(--text-main)); font-weight:700; }
    #slide-26 .qvoice-heartbeat-track { height:10px; overflow:hidden; border-radius:999px; background:color-mix(in oklab, var(--text-muted) 14%, transparent); }
    #slide-26 .qvoice-heartbeat-fill { min-width:2px; height:100%; border-radius:inherit; }
    #slide-26 .qvoice-heartbeat-fill.above { background:var(--accent); }
    #slide-26 .qvoice-heartbeat-fill.equal { background:color-mix(in oklab, var(--text-muted) 72%, transparent); }
    #slide-26 .qvoice-heartbeat-fill.below { background:color-mix(in oklab, #f59e0b 88%, var(--text-main)); }
    #slide-26 .qvoice-heartbeat-share { text-align:right; font-size:9px; font-variant-numeric:tabular-nums; color:var(--text-main); }
    #slide-26 .qvoice-heartbeat-attrition { position:static !important; right:auto !important; top:auto !important; transform:none !important; display:inline-flex !important; align-items:center; justify-content:center; min-width:43px; padding:3px 4px; border-radius:999px; font-size:9px; line-height:1; font-weight:800; text-align:center; font-variant-numeric:tabular-nums; }
    /* Same low / middle / high attrition pill treatment as Job family (slide 10). */
    #slide-26 .qvoice-heartbeat-attrition.attr-low { color:#15803d; background:color-mix(in oklab, #22c55e 14%, transparent); border:1px solid color-mix(in oklab, #22c55e 30%, var(--border-subtle)); }
    #slide-26 .qvoice-heartbeat-attrition.attr-mid { color:var(--accent); background:color-mix(in oklab, var(--accent) 10%, transparent); border:1px solid color-mix(in oklab, var(--accent) 24%, var(--border-subtle)); }
    #slide-26 .qvoice-heartbeat-attrition.attr-high { color:#c2410c; background:color-mix(in oklab, #f97316 14%, transparent); border:1px solid color-mix(in oklab, #f97316 30%, var(--border-subtle)); }
    #slide-26 .qvoice-heartbeat-footer { margin:0; padding-top:5px; border-top:1px solid var(--border-subtle); font-size:8.5px; line-height:1.2; color:var(--text-muted); }
    #slide-26 .v6-source-line { font-size:8px; line-height:1.2; }
    </style>'''
    stage = (
        '<div class="slide-stage" id="slide-26" data-v6-playbook="true" '
        'data-v7-qvoice-heartbeat-attrition="post-survey-ytd-through-august" '
        'data-v7-qvoice-heartbeat-relative-signs="true">'
        + heartbeat_css
        + '<div class="slide-heading"><div><h2 class="slide-title-text">QVoice heartbeat</h2>'
        '<p class="slide-subtitle">Each item is compared with the respondent\'s own mean; attrition is post-survey voluntary exits through fiscal August 2026</p>'
        '</div><span class="badge badge-info">Post-survey attrition YTD</span></div>'
        '<article class="card card-full v6-playbook-card"><div class="v6-definition-strip"><div><span class="v6-mini-label">Relative signal</span>'
        '<strong>+1 above, 0 equal to, and -1 below each respondent\'s own mean.</strong></div><div><span class="v6-mini-label">Outcome</span>'
        '<strong>Voluntary exits after 07 Jan through 23 Aug 2026; YTD, not annualized.</strong></div></div>'
        '<div class="v6-chart-area"><article class="card chart-card qvoice-heartbeat-card"><div class="card-title">Top relative-response signals and segment attrition</div>'
        '<p class="qvoice-heartbeat-intro">For every ranked question, the three mutually exclusive response signs sum to 100.0% of valid responses. Pills show the matching segment\'s attrition.</p>'
        '<div class="qvoice-heartbeat-grid">' + "".join(panel_html) + '</div>'
        '<p class="qvoice-heartbeat-footer"><strong>Read as a within-question comparison:</strong> people may appear under more than one question; rates are descriptive, post-survey YTD, and not annualized. Hover a row for n and exits.</p>'
        '</article></div><div class="v6-source-line"><strong>Source:</strong> Jan-2026 QVoice raw responses linked to the active Regular workforce at 28 Dec 2025; strict voluntary exits through the fiscal-August close.</div>'
        '</article></div>'
    )
    return replace_stage_fragment(deck, 26, stage)


def qvoice_context_metric(label: str, value: int, maximum: int, fill_class: str) -> str:
    """Render a direct-labeled horizontal bar on a shared, zero-based scale."""
    require(maximum > 0 and 0 <= value <= maximum, "QVoice context bars require values within a positive shared scale.")
    width = max(3.0, (value / maximum) * 100.0)
    return (
        '<div class="qvoice-context-metric"><span class="qvoice-context-label">'
        + html.escape(label)
        + '</span><div class="qvoice-context-track" title="'
        + html.escape(f"{label}: {value:,} cases; shared scale 0–{maximum:,}")
        + '"><div class="qvoice-context-fill '
        + fill_class
        + '" style="width:'
        + f"{width:.1f}%"
        + '"></div></div><span class="qvoice-context-value">'
        + f"{value:,}"
        + "</span></div>"
    )


def replace_qvoice_comment_tables_with_bar_charts(deck: str) -> str:
    """Use visual bar comparisons for the two numeric tables on QVoice slide 20."""
    stage = stage_fragment(deck, 20)
    comment_card = article_with_class(stage, "qvoice-comment-card")
    comment_table = re.search(r'<table class="qvoice-comment-table">.*?</table>', comment_card, flags=re.S)
    diagnostic_table = re.search(r'<table class="qvoice-diagnostic-table">.*?</table>', comment_card, flags=re.S)
    chart = re.search(r'<div id="qvoice-comment-chart"[^>]*></div>', comment_card, flags=re.S)
    title = re.search(r'<div class="card-title">.*?</div>', comment_card, flags=re.S)
    note = re.search(r'<p class="qvoice-comment-note">.*?</p>', comment_card, flags=re.S)
    diagnostic_note = re.search(r'<p class="qvoice-diagnostic-note">.*?</p>', comment_card, flags=re.S)
    require(comment_table is not None and diagnostic_table is not None, "QVoice slide 20 requires both source tables before chart conversion.")
    require(chart is not None and title is not None and note is not None and diagnostic_note is not None, "QVoice slide 20 source content is incomplete.")

    wave_rows = list(
        re.finditer(
            r'<tr><td><span class="qvoice-wave-name">(?P<wave>[^<]+)</span>(?P<attrition><span class="qvoice-wave-attrition[^>]*>.*?</span>)</td><td><strong>[\d,]+</strong></td><td><strong>[\d,]+</strong></td><td><strong>[\d,]+</strong></td></tr>',
            comment_table.group(0),
            flags=re.S,
        )
    )
    require(len(wave_rows) == 4, "QVoice topic table must provide one labeled attrition row per survey wave.")
    attrition_by_wave = {
        html.unescape(row.group("wave")).strip(): row.group("attrition")
        for row in wave_rows
    }

    context_rows = list(
        re.finditer(
            r'<tr><td>(?P<wave>[^<]+)</td><td><strong>(?P<improvement>[\d,]+)</strong></td><td><strong>(?P<friction>[\d,]+)</strong></td></tr>',
            diagnostic_table.group(0),
            flags=re.S,
        )
    )
    require(len(context_rows) == 4, "QVoice office-context table must provide four survey-wave rows.")
    parsed_context_rows = [
        (
            html.unescape(row.group("wave")).strip(),
            int(row.group("improvement").replace(",", "")),
            int(row.group("friction").replace(",", "")),
        )
        for row in context_rows
    ]
    require(
        set(attrition_by_wave) == {wave for wave, _, _ in parsed_context_rows},
        "QVoice attrition labels must map one-to-one to the office-context waves.",
    )
    maximum_context_cases = max(value for _, improvement, friction in parsed_context_rows for value in (improvement, friction))
    require(maximum_context_cases == 1373, "QVoice office-context bars must retain the maximum published count.")
    context_bars = "".join(
        '<div class="qvoice-context-row"><div class="qvoice-context-wave">'
        + '<span class="qvoice-wave-name">'
        + html.escape(wave)
        + "</span>"
        + attrition_by_wave[wave]
        + "</div>"
        + qvoice_context_metric("What to improve", improvement, maximum_context_cases, "is-improvement")
        + qvoice_context_metric("Office attendance", friction, maximum_context_cases, "is-friction")
        + "</div>"
        for wave, improvement, friction in parsed_context_rows
    )
    context_card = (
        '<article class="card chart-card qvoice-office-context-card"><div class="v6-panel-heading"><span>Related office comments by survey</span><span>Comments</span></div>'
        '<p class="qvoice-office-context-intro">Each bar is a comment count. Every bar uses the same 0–'
        + f"{maximum_context_cases:,}"
        + " scale.</p><div class=\"qvoice-context-list\">"
        + context_bars
        + "</div>"
        + '<p class="qvoice-office-context-note">Office attendance is counted only when it appears in a comment. It can be positive, negative, or neutral.</p>'
        + "</article>"
    )
    card_open_end = comment_card.find(">") + 1
    require(card_open_end > 0, "QVoice topic card opening tag is malformed.")
    rebuilt_comment_card = (
        comment_card[:card_open_end]
        + '<div class="card-title">Comments mentioning each topic, by survey</div>'
        + chart.group(0).replace('aria-label="QVoice topic mentions by survey wave"', 'aria-label="Comments by topic and survey"', 1)
        + '<p class="qvoice-comment-note">A person can mention more than one topic. Counts are not percentages.</p>'
        + "</article>"
    )
    pane_start = stage.find('<div class="two-pane">')
    require(pane_start >= 0, "QVoice slide 20 is missing its chart pane.")
    pane_end = matching_tag_end(stage, "div", pane_start)
    pane = stage[pane_start:pane_end]
    require(pane.count(comment_card) == 1, "QVoice topic card must be uniquely replaceable.")
    rebuilt_pane = pane.replace(comment_card, rebuilt_comment_card + context_card, 1)
    stage = stage[:pane_start] + rebuilt_pane + stage[pane_end:]
    updated = replace_stage_fragment(deck, 20, stage)
    updated, replacements = re.subn(
        r'(function renderQVoiceCommentChart\(\) \{.*?chart\.innerHTML = \'<p class="chart-note">)The interactive chart could not load\. The aggregate table below contains the complete published counts\.(</p>\';)',
        r'\1The interactive chart could not load. Reload this slide to view the aggregate visual.\2',
        updated,
        count=1,
        flags=re.S,
    )
    require(replacements == 1, "QVoice topic-chart fallback still refers to a removed table.")
    return updated


def qvoice_favorable_unfavorable_response_row(
    label: str,
    row: dict[str, Any],
    rates: list[float],
    outcome_type: str,
) -> str:
    """Render one compact response bar and its cohort-matched attrition outcome."""
    share = float(row["linked_response_share_percent"])
    rate = float(row["voluntary_attrition_rate_percent"])
    cohort = int(row["matched_employee_count"])
    exits = int(row["voluntary_exit_count"])
    color_class = attrition_pill_class(rate, rates)
    dot_class = "qvoice-fu-dot-favorable" if label == "Favorable" else "qvoice-fu-dot-no-favorable"
    fill_class = "qvoice-fu-fill-favorable" if label == "Favorable" else "qvoice-fu-fill-no-favorable"
    period = "Annual voluntary attrition · 12 months" if outcome_type == "annual_12m" else "Voluntary attrition YTD · not annualized"
    return (
        '<div class="qvoice-fu-response">'
        '<div class="qvoice-fu-response-top"><span class="qvoice-fu-response-label"><i class="qvoice-fu-dot '
        + dot_class
        + '"></i>'
        + html.escape(label)
        + '</span><strong>'
        + f"{share:.1f}%"
        + "</strong></div>"
        '<div class="qvoice-fu-track"><span class="qvoice-fu-fill '
        + fill_class
        + '" style="width:'
        + f"{share:.4f}%"
        + '"></span></div>'
        '<div class="qvoice-fu-response-foot"><span class="qvoice-fu-cohort">n='
        + f"{cohort:,} · {exits:,} exits"
        + '</span><span class="qvoice-fu-attrition-pill v6-rate-pill '
        + color_class
        + '" title="'
        + html.escape(f"{period}: {rate:.1f}%", quote=True)
        + '" aria-label="'
        + html.escape(f"{label}; {period}: {rate:.1f}%", quote=True)
        + '">'
        + f"{rate:.1f}%"
        + "</span></div></div>"
    )


def qvoice_favorable_unfavorable_section(
    title: str,
    groups: dict[str, Any],
    outcome_type: str,
    section_class: str = "",
    question: str | None = None,
) -> str:
    """Render a driver or component block with its two response bars."""
    rates = [float(groups[label]["voluntary_attrition_rate_percent"]) for label in ("Favorable", "No favorable")]
    question_attr = f' title="{html.escape(question, quote=True)}"' if question else ""
    response_rows = "".join(
        qvoice_favorable_unfavorable_response_row(label, groups[label], rates, outcome_type)
        for label in ("Favorable", "No favorable")
    )
    extra_class = f" {section_class}" if section_class else ""
    return (
        '<section class="qvoice-fu-segment'
        + extra_class
        + '"><div class="qvoice-fu-segment-head"><strong'
        + question_attr
        + '>'
        + html.escape(title)
        + '</strong><span>Favorable / No favorable</span></div>'
        + response_rows
        + "</section>"
    )


def build_qvoice_favorable_unfavorable_stage(metric: str, evidence: dict[str, Any]) -> str:
    """Build the three-card QVoice driver-plus-question response layout."""
    specifications = {
        "intent_to_stay": {
            "stage": 23,
            "title": "Intent to Stay items",
            "subtitle": "Driver and question-level response mix with cohort-matched voluntary attrition",
            "definition": "Both Intent-to-Stay questions are valid; Favorable means both are favorable.",
            "message": "Driver first, followed by the two component questions",
            "caveat": "The driver uses complete valid answers to Q4 and Q12. Each question block uses that question's valid responses; partial driver responses are excluded from the driver block.",
        },
        "career_goals": {
            "stage": 24,
            "title": "Career goals item",
            "subtitle": "Driver and question-level response mix with cohort-matched voluntary attrition",
            "definition": "Stored binary Career Goals response: 1 = Favorable; 0 = No favorable.",
            "message": "Driver first, followed by its single source question",
            "caveat": "Career Goals is one source question, so the driver and question-level blocks intentionally use the same response definition. Wording differs in 2024 versus 2025–2026.",
        },
    }
    spec = specifications[metric]
    rows = evidence["variables"][metric]
    cards: list[str] = []
    for wave in rows:
        component_sections = "".join(
            qvoice_favorable_unfavorable_section(
                str(component["short_label"]),
                component["groups"],
                str(wave["outcome_type"]),
                "qvoice-fu-component",
                str(component.get("question", "")),
            )
            for component in wave["components"].values()
        )
        cards.append(
            '<section class="qvoice-fu-wave-card"><div class="qvoice-fu-wave-head"><strong>'
            + str(wave["year"])
            + '</strong><span>'
            + ("Annual attrition · 12 months" if wave["outcome_type"] == "annual_12m" else "YTD attrition · not annualized")
            + '</span></div><div class="qvoice-fu-segments">'
            + qvoice_favorable_unfavorable_section(
                "Driver · " + ("Intent to Stay" if metric == "intent_to_stay" else "Career goals"),
                wave["groups"],
                str(wave["outcome_type"]),
                "qvoice-fu-driver",
            )
            + '<div class="qvoice-fu-components-label">Component questions</div>'
            + component_sections
            + '</div>'
            + "</section>"
        )
    return (
        '<div class="slide-stage" id="slide-'
        + str(spec["stage"])
        + '" data-v6-playbook="true" data-v7-qvoice-favorable-unfavorable="'
        + metric
        + '"><div class="slide-heading"><div><h2 class="slide-title-text">'
        + spec["title"]
        + "</h2><p class=\"slide-subtitle\">"
        + spec["subtitle"]
        + '</p></div><span class="badge badge-info">2024–2026</span></div>'
        '<article class="card card-full qvoice-fu-card"><div class="qvoice-fu-card-head"><div><p class="qvoice-fu-eyebrow">'
        + spec["message"]
        + '</p><p class="qvoice-fu-definition"><strong>Definition:</strong> '
        + spec["definition"]
        + '</p><p class="qvoice-fu-meta">Population: linked QVoice respondents in the active Regular pre-wave cohort</p></div></div>'
        '<div class="qvoice-fu-wave-grid">'
        + "".join(cards)
        + '</div><div class="qvoice-fu-footer"><span>'
        + spec["caveat"]
        + '</span><span><strong>2024–2025:</strong> strict voluntary exits in the following 12 months. <strong>2026:</strong> YTD through 27 Sep 2026; not annualized.</span><span>Source: QVoice raw workbooks + time-safe workforce join.</span></div></article></div>'
    )


def replace_qvoice_favorable_unfavorable_stages(deck: str, evidence: dict[str, Any]) -> str:
    """Replace the former coverage-plus-stored-value visual on navigation slides 21–22."""
    for metric in ("intent_to_stay", "career_goals"):
        deck = replace_stage_fragment(deck, 23 if metric == "intent_to_stay" else 24, build_qvoice_favorable_unfavorable_stage(metric, evidence))
    return deck


def simplify_qvoice_slide_18_language(deck: str) -> str:
    """Use plain-language labels for the QVoice remote/hybrid/office slide."""
    stage = stage_fragment(deck, 20)

    def replace_once(source: str, target: str, description: str) -> None:
        nonlocal stage
        if stage.count(target) == 1:
            return
        require(stage.count(source) == 1, f"QVoice slide 18 is missing {description}.")
        stage = stage.replace(source, target, 1)

    replace_once(
        '<h2 class="slide-title-text">RTO and hybrid comments in QVoice</h2>',
        '<h2 class="slide-title-text">QVoice comments about remote, hybrid, and office work</h2>',
        "the original title",
    )
    replace_once(
        '<p class="slide-subtitle">The chart counts topic mentions; it does not measure sentiment, complaints, or policy agreement</p>',
        '<p class="slide-subtitle">How often employees mentioned each topic — not whether they liked or disliked it</p>',
        "the original subtitle",
    )
    replace_once(
        '<span class="v6-mini-label">Definition</span><strong>The chart counts topic mentions; it does not measure sentiment, complaints, or policy agreement</strong>',
        '<span class="v6-mini-label">What this shows</span><strong>Comments that mention these topics. It does not show whether a comment was positive or negative.</strong>',
        "the original definition",
    )
    replace_once(
        '<div class="card-title">Absolute respondent-wave cases by topic mention</div>',
        '<div class="card-title">Comments mentioning each topic, by survey</div>',
        "the original chart title",
    )
    replace_once(
        'aria-label="QVoice topic mentions by survey wave"',
        'aria-label="Comments by topic and survey"',
        "the original chart label",
    )
    stage, replacements = re.subn(
        r'<p class="qvoice-comment-note">.*?</p>',
        '<p class="qvoice-comment-note">A person can mention more than one topic. Counts are not percentages.</p>',
        stage,
        count=1,
        flags=re.S,
    )
    require(replacements == 1, "QVoice slide 18 is missing the chart note.")
    replace_once(
        '<span>Office context by survey wave</span><span>Cases</span>',
        '<span>Related office comments by survey</span><span>Comments</span>',
        "the original right-panel heading",
    )
    stage, replacements = re.subn(
        r'<p class="qvoice-office-context-intro">.*?</p>',
        '<p class="qvoice-office-context-intro">Each bar is a comment count. Every bar uses the same scale.</p>',
        stage,
        count=1,
        flags=re.S,
    )
    require(replacements == 1, "QVoice slide 18 is missing the right-panel introduction.")
    if "What to improve" not in stage:
        require(stage.count("Improvement prompts") >= 4, "QVoice slide 18 is missing improvement-comment labels.")
        stage = stage.replace("Improvement prompts", "What to improve")
    if "Office attendance" not in stage:
        require(stage.count("Requirement / friction") >= 4, "QVoice slide 18 is missing office-attendance labels.")
        stage = stage.replace("Requirement / friction", "Office attendance")
    stage, replacements = re.subn(
        r'<p class="qvoice-office-context-note">.*?</p>',
        '<p class="qvoice-office-context-note">Office attendance is counted only when it appears in a comment. It can be positive, negative, or neutral.</p>',
        stage,
        count=1,
        flags=re.S,
    )
    require(replacements == 1, "QVoice slide 18 is missing the office-attendance note.")
    updated = replace_stage_fragment(deck, 20, stage)

    rows_match = re.search(r'var qvoiceCommentRows = (\[.*?\]);', updated, flags=re.S)
    require(rows_match is not None, "QVoice comment-chart data is missing.")
    original_rows = json.loads(rows_match.group(1))
    require(len(original_rows) == 4, "QVoice comment-chart data must retain four survey waves.")
    renamed_rows = []
    for row in original_rows:
        require(
            set(row) == {"wave", "Remote / WFH", "Hybrid", "RTO / office attendance"},
            "QVoice comment-chart data has an unexpected topic schema.",
        )
        renamed_rows.append(
            {
                "wave": row["wave"],
                "Remote work": row["Remote / WFH"],
                "Hybrid work": row["Hybrid"],
                "Office attendance": row["RTO / office attendance"],
            }
        )
    updated, replacements = re.subn(
        r'var qvoiceCommentRows = \[.*?\];',
        'var qvoiceCommentRows = ' + json.dumps(renamed_rows, ensure_ascii=False) + ';',
        updated,
        count=1,
        flags=re.S,
    )
    require(replacements == 1, "Could not simplify the QVoice comment-chart labels.")
    updated, replacements = re.subn(
        r'var qvoiceCommentThemes = \[.*?\];',
        'var qvoiceCommentThemes = ["Remote work", "Hybrid work", "Office attendance"];',
        updated,
        count=1,
        flags=re.S,
    )
    require(replacements == 1, "Could not simplify the QVoice chart legend.")
    updated, replacements = re.subn(
        r'(<button class="nav-pill" data-slide="\d+">)(?P<number>\d+)\. RTO and hybrid comments in QVoice(</button>)',
        r'\g<1>\g<number>. QVoice comments about remote, hybrid, and office work\g<3>',
        updated,
        count=1,
    )
    require(replacements == 1, "Could not simplify the QVoice navigation label.")
    return updated


def replace_qvoice_request_concern_slide(deck: str, evidence: dict[str, Any]) -> str:
    """Make the request/concern composition part of every full V7 build.

    Navigation slide 18 is technical stage ``slide-20``.  The renderer uses
    the aggregate-only evidence artifact and replaces the temporary topic-bar
    composition with the approved three-group stacked-bar layout.
    """
    replacement = build_qvoice_request_concern_stage(evidence)
    require(
        'data-qvoice-open-text-request-concern="20260922"' in replacement,
        "The QVoice request/concern renderer is missing its evidence marker.",
    )
    require(
        'data-v7-qvoice-open-text-no-comment-attrition="true"' in replacement,
        "The QVoice request/concern renderer is missing the no-comment attrition marker.",
    )
    require('data-v7-qvoice-open-text-three-group-composition="true"' in replacement, "The QVoice three-group composition marker is missing.")
    require(replacement.count('class="qvoice18-composition-bar"') == 4, "The QVoice visual must render one three-group bar per wave.")
    require("Participation mix and subsequent attrition" in replacement, "The QVoice composition panel is missing.")
    require("qvoice18-rail-card" not in replacement, "The obsolete QVoice coverage rails remain.")
    require(replacement.count('qvoice18-attrition-pill v6-rate-pill') == 12, "The QVoice composition panel must render three pills per survey wave.")
    updated = replace_stage_fragment(deck, 20, replacement)
    require(
        "QVoice comments about remote, hybrid, and office work" in updated,
        "The QVoice navigation label is missing after the slide replacement.",
    )
    return updated


def refresh_qvoice_slide_18_language_only() -> None:
    """Apply plain-language copy to the current deck without rebuilding other slides."""
    require(OUTPUT_DECK.exists(), f"Missing current V7 deck: {OUTPUT_DECK}")
    require(MANIFEST_FILE.exists(), f"Missing current V7 manifest: {MANIFEST_FILE}")
    source_hash = digest(OUTPUT_DECK)
    before = OUTPUT_DECK.read_text(encoding="utf-8")
    after = simplify_qvoice_slide_18_language(before)
    before_stages = application_stage_map(before)
    after_stages = application_stage_map(after)
    require(before_stages.keys() == after_stages.keys(), "Plain-language refresh changed the slide inventory.")
    last_stage = max(after_stages)
    for slide_number in after_stages:
        if slide_number not in (20, last_stage):
            require(before_stages[slide_number] == after_stages[slide_number], f"Plain-language refresh changed slide {slide_number}.")
    slide_20 = after_stages[20]
    for required in (
        "QVoice comments about remote, hybrid, and office work",
        "How often employees mentioned each topic",
        "Comments mentioning each topic, by survey",
        "Related office comments by survey",
        "What to improve",
        "Office attendance",
        "It can be positive, negative, or neutral.",
    ):
        require(required in slide_20, f"QVoice slide 18 is missing plain-language copy: {required}")
    for removed in ("Improvement prompts", "Requirement / friction", "Office context by survey wave"):
        require(removed not in slide_20, f"QVoice slide 18 retains technical copy: {removed}")
    require('var qvoiceCommentThemes = ["Remote work", "Hybrid work", "Office attendance"];' in after, "QVoice chart legend was not simplified.")
    require(digest(OUTPUT_DECK) == source_hash, "The deck changed concurrently; plain-language refresh was not written.")

    temporary_deck = OUTPUT_DECK.with_suffix(".qvoice-plain-language.tmp")
    temporary_deck.write_text(after, encoding="utf-8")
    temporary_deck.replace(OUTPUT_DECK)
    written_deck_hash = digest(OUTPUT_DECK)

    manifest_hash = digest(MANIFEST_FILE)
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    manifest["updated_slide_18_language"] = {
        "navigation_slide": 18,
        "stage_id": "slide-20",
        "title": "QVoice comments about remote, hybrid, and office work",
        "language_rule": "Use everyday terms; the context counts are not complaint or sentiment labels.",
    }
    validation = manifest.setdefault("validation", {})
    validation["qvoice_slide_18_plain_language_refresh_outcome"] = "pass"
    manifest["output_deck"] = {
        "path": str(OUTPUT_DECK.relative_to(ROOT)).replace("\\", "/"),
        "sha256": written_deck_hash,
    }
    require(digest(OUTPUT_DECK) == written_deck_hash, "The deck changed again before the plain-language manifest was written.")
    require(digest(MANIFEST_FILE) == manifest_hash, "The manifest changed concurrently; plain-language manifest was not written.")
    temporary_manifest = MANIFEST_FILE.with_suffix(".qvoice-plain-language.tmp")
    temporary_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_manifest.replace(MANIFEST_FILE)
    print(OUTPUT_DECK)
    print(MANIFEST_FILE)


def refresh_qvoice_intent_display_window_only() -> None:
    """Apply the approved 2024-2026 display window without rebuilding V7."""
    require(OUTPUT_DECK.exists(), f"Missing current V7 deck: {OUTPUT_DECK}")
    require(MANIFEST_FILE.exists(), f"Missing current V7 manifest: {MANIFEST_FILE}")
    source_hash = digest(OUTPUT_DECK)
    before = OUTPUT_DECK.read_text(encoding="utf-8")
    after = limit_qvoice_intent_display_to_recent_years(before)
    before_stages = application_stage_map(before)
    after_stages = application_stage_map(after)
    require(before_stages.keys() == after_stages.keys(), "Intent-to-Stay refresh changed the slide inventory.")
    for slide_number in after_stages:
        if slide_number != 23:
            require(before_stages[slide_number] == after_stages[slide_number], f"Intent-to-Stay refresh changed slide {slide_number}.")
    slide_23 = after_stages[23]
    require('style="--bars:3"' in slide_23, "Intent-to-Stay chart must render three bars.")
    for year in QVOICE_INTENT_DISPLAY_YEARS:
        require(f"<span>{year}</span>" in slide_23, f"Intent-to-Stay chart is missing {year}.")
    for historical_year in ("2019", "2020", "2023"):
        require(f"<span>{historical_year}</span>" not in slide_23, f"Intent-to-Stay chart still shows {historical_year}.")
    require(digest(OUTPUT_DECK) == source_hash, "The deck changed concurrently; Intent-to-Stay was not written.")

    temporary_deck = OUTPUT_DECK.with_suffix(".qvoice-intent-window.tmp")
    temporary_deck.write_text(after, encoding="utf-8")
    temporary_deck.replace(OUTPUT_DECK)
    written_deck_hash = digest(OUTPUT_DECK)

    manifest_hash = digest(MANIFEST_FILE)
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    manifest["updated_slide_20_display_window"] = {
        "navigation_slide": 20,
        "stage_id": "slide-23",
        "title": "Intent to Stay items",
        "displayed_years": list(QVOICE_INTENT_DISPLAY_YEARS),
        "rule": "Presentation-only window; earlier QVoice waves and the 2023 mapping finding remain documented but are not displayed.",
    }
    validation = manifest.setdefault("validation", {})
    validation["qvoice_intent_displayed_years"] = list(QVOICE_INTENT_DISPLAY_YEARS)
    validation["qvoice_intent_display_window_refresh_outcome"] = "pass"
    manifest["output_deck"] = {
        "path": str(OUTPUT_DECK.relative_to(ROOT)).replace("\\", "/"),
        "sha256": written_deck_hash,
    }
    require(digest(OUTPUT_DECK) == written_deck_hash, "The deck changed again before the Intent-to-Stay manifest was written.")
    require(digest(MANIFEST_FILE) == manifest_hash, "The manifest changed concurrently; Intent-to-Stay manifest was not written.")
    temporary_manifest = MANIFEST_FILE.with_suffix(".qvoice-intent-window.tmp")
    temporary_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_manifest.replace(MANIFEST_FILE)
    print(OUTPUT_DECK)
    print(MANIFEST_FILE)


def refresh_colocation_trailing_12m_slide_only() -> None:
    """Refresh navigation slide 36 from the frozen fiscal-year-end trailing evidence."""
    require(OUTPUT_DECK.exists(), f"Missing current V7 deck: {OUTPUT_DECK}")
    require(MANIFEST_FILE.exists(), f"Missing current V7 manifest: {MANIFEST_FILE}")
    require(COLOCATION_ANNUAL_ATTRITION_EVIDENCE_FILE.exists(), f"Missing co-location trailing evidence: {COLOCATION_ANNUAL_ATTRITION_EVIDENCE_FILE}")
    evidence = load_colocation_annual_attrition_evidence()
    source_hash = digest(OUTPUT_DECK)
    before = OUTPUT_DECK.read_text(encoding="utf-8")
    after = replace_colocation_with_annual_attrition(before, evidence)
    before_stages = application_stage_map(before)
    after_stages = application_stage_map(after)
    require(before_stages.keys() == after_stages.keys(), "Co-location refresh changed the slide inventory.")
    for slide_number in after_stages:
        if slide_number != 41:
            require(before_stages[slide_number] == after_stages[slide_number], f"Co-location refresh changed slide {slide_number}.")
    slide_41 = after_stages[41]
    require("Trailing 12m attrition" in slide_41, "Co-location slide is missing the trailing-window badge.")
    require("FY2023-FY2026" in slide_41, "Co-location slide is missing its concise display window.")
    require(slide_41.count('<div class="trend-bar-wrap">') == 2 * len(COLOCATION_DISPLAY_YEARS), "Co-location slide must retain four fiscal years in both charts.")
    for omitted_year in ("2020", "2021", "2022"):
        require(f"<span>{omitted_year}</span>" not in slide_41, f"Co-location slide must not retain FY{omitted_year}.")
    for metric in ("same_office_site", "same_office_site_and_city"):
        rows = {str(row["fiscal_year"]): row for row in evidence["rates"][metric]}
        for year in COLOCATION_DISPLAY_YEARS:
            rate = float(rows[year]["annual_attrition_rate_percent"])
            require(f">{rate:.1f}%</span>" in slide_41, f"Co-location slide is missing FY{year} trailing rate.")
    require(digest(OUTPUT_DECK) == source_hash, "The deck changed concurrently; co-location was not written.")

    temporary_deck = OUTPUT_DECK.with_suffix(".colocation-trailing-12m.tmp")
    temporary_deck.write_text(after, encoding="utf-8")
    temporary_deck.replace(OUTPUT_DECK)
    written_deck_hash = digest(OUTPUT_DECK)

    manifest_hash = digest(MANIFEST_FILE)
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    manifest["updated_slide_36_colocation_trailing_12m"] = {
        "navigation_slide": 36,
        "stage_id": "slide-41",
        "title": "Co-location with manager",
        "displayed_trailing_years": list(COLOCATION_DISPLAY_YEARS),
        "omitted_years_for_concise_view": ["2020", "2021", "2022"],
        "baseline_rule": evidence["outcome_contract"]["window_rule"],
        "query_path": evidence["execution"]["query_path"],
        "query_sha256": evidence["execution"]["query_sha256"],
    }
    validation = manifest.setdefault("validation", {})
    validation["colocation_trailing_12m_displayed_years"] = list(COLOCATION_DISPLAY_YEARS)
    validation["colocation_trailing_12m_refresh_outcome"] = "pass"
    manifest["output_deck"] = {
        "path": str(OUTPUT_DECK.relative_to(ROOT)).replace("\\", "/"),
        "sha256": written_deck_hash,
    }
    require(digest(OUTPUT_DECK) == written_deck_hash, "The deck changed again before the co-location manifest was written.")
    require(digest(MANIFEST_FILE) == manifest_hash, "The manifest changed concurrently; co-location manifest was not written.")
    temporary_manifest = MANIFEST_FILE.with_suffix(".colocation-trailing-12m.tmp")
    temporary_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_manifest.replace(MANIFEST_FILE)
    print(OUTPUT_DECK)
    print(MANIFEST_FILE)


def refresh_manager_timezone_ytd_slide_only() -> None:
    """Refresh navigation slide 36 without rebuilding unrelated deck content."""
    require(OUTPUT_DECK.exists(), f"Missing current V7 deck: {OUTPUT_DECK}")
    require(MANIFEST_FILE.exists(), f"Missing current V7 manifest: {MANIFEST_FILE}")
    require(MANAGER_TIMEZONE_ANNUAL_ATTRITION_EVIDENCE_FILE.exists(), "Missing manager time-zone distribution evidence.")
    require(MANAGER_TIMEZONE_2026_YTD_ATTRITION_EVIDENCE_FILE.exists(), "Missing manager time-zone 2026 YTD evidence.")
    distribution_evidence = load_manager_timezone_annual_attrition_evidence()
    ytd_evidence = load_manager_timezone_2026_ytd_attrition_evidence()
    source_hash = digest(OUTPUT_DECK)
    before = OUTPUT_DECK.read_text(encoding="utf-8")
    after = replace_residential_distance_with_manager_timezone_proximity(
        before,
        distribution_evidence,
        ytd_evidence,
    )
    before_stages = application_stage_map(before)
    after_stages = application_stage_map(after)
    require(before_stages.keys() == after_stages.keys(), "Manager time-zone refresh changed the slide inventory.")
    for slide_number in after_stages:
        if slide_number != 42:
            require(before_stages[slide_number] == after_stages[slide_number], f"Manager time-zone refresh changed slide {slide_number}.")
    slide_42 = after_stages[42]
    require(slide_42.count("manager-timezone-ytd-pill") == 3, "Slide 36 must retain three 2026 YTD attrition labels.")
    require("N/E</span>" not in slide_42, "Slide 36 should show every rate for cohorts at or above n=30.")
    for row in ytd_evidence["rows"]:
        rate = float(row["ytd_voluntary_attrition_rate_percent"])
        cohort_size = int(row["employee_count"])
        exits = int(row["voluntary_exits"])
        require(f">{rate:.1f}%</span>" in slide_42, f"Slide 36 is missing a 2026 YTD rate for {row['category']}.")
        require(
            f"baseline cohort n={cohort_size:,}; voluntary exits={exits:,}" in slide_42,
            f"Slide 36 is missing cohort context for {row['category']}.",
        )
    require(digest(OUTPUT_DECK) == source_hash, "The deck changed concurrently; manager time-zone was not written.")

    temporary_deck = OUTPUT_DECK.with_suffix(".manager-timezone-ytd.tmp")
    temporary_deck.write_text(after, encoding="utf-8")
    temporary_deck.replace(OUTPUT_DECK)
    written_deck_hash = digest(OUTPUT_DECK)

    manifest_hash = digest(MANIFEST_FILE)
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    manifest["updated_slide_36_manager_timezone_ytd_display"] = {
        "navigation_slide": 36,
        "stage_id": "slide-42",
        "title": "Assigned office-site proximity to manager",
        "display_rule": "Show 2026 YTD voluntary attrition for each aggregate baseline cohort at or above 30 employees; do not suppress a valid aggregate rate solely because voluntary exits are below 30.",
        "low_event_count_handling": "The tooltip retains the aggregate baseline cohort and voluntary-exit counts.",
        "query_path": ytd_evidence["query"],
        "query_sha256": ytd_evidence["query_sha256"],
    }
    validation = manifest.setdefault("validation", {})
    validation["manager_timezone_ytd_display_cohort_threshold"] = 30
    validation["manager_timezone_ytd_low_event_rate_visible"] = True
    validation["manager_timezone_ytd_refresh_outcome"] = "pass"
    manifest["output_deck"] = {
        "path": str(OUTPUT_DECK.relative_to(ROOT)).replace("\\", "/"),
        "sha256": written_deck_hash,
    }
    require(digest(OUTPUT_DECK) == written_deck_hash, "The deck changed again before the manager time-zone manifest was written.")
    require(digest(MANIFEST_FILE) == manifest_hash, "The manifest changed concurrently; manager time-zone manifest was not written.")
    temporary_manifest = MANIFEST_FILE.with_suffix(".manager-timezone-ytd.tmp")
    temporary_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_manifest.replace(MANIFEST_FILE)
    print(OUTPUT_DECK)
    print(MANIFEST_FILE)


def work_arrangement_row(label: str, title: str, employee_count: int, share_percent: float, width_percent: float, rate: float, pill_class: str) -> str:
    rendered_rate = f"{rate:.1f}%"
    return (
        '<div class="bar-row v4-inline-attrition-row"><div class="bar-label" title="'
        + html.escape(title)
        + '">'
        + html.escape(label)
        + '</div><div class="bar-track"><div class="bar-fill" style="width:'
        + f"{width_percent:.1f}%"
        + '"></div></div><div class="bar-value">'
        + f"{share_percent:.0f}% &middot; {employee_count:,}"
        + '<span class="v4-inline-attrition-rate v6-rate-pill '
        + pill_class
        + '" title="Six-month voluntary attrition: '
        + rendered_rate
        + '" aria-label="Six-month voluntary attrition: '
        + rendered_rate
        + '">'
        + rendered_rate
        + "</span></div></div>"
    )


def replace_work_arrangement_content(deck: str, rate_evidence: dict[str, float]) -> tuple[str, dict[str, float]]:
    """Collapse slide 14 into three transparent, attrition-labelled groups."""
    pattern = r'(<div class="slide-stage" id="slide-14".*?)(?=\n\s*<div class="slide-stage" id="slide-15")'

    def replace_stage(match: re.Match[str]) -> str:
        stage = match.group(1)
        stored_card = article_with_class(stage, "work-arrangement-card")
        binary_card = article_with_class(stage, "work-arrangement-binary-card")
        onsite_count, _ = displayed_distribution(bar_row_with_label(stored_card, "Onsite"))
        short_term_count, _ = displayed_distribution(
            bar_row_with_label(stored_card, "Interim Modified – Short-Term Remote Work")
        )
        binary_other_count, _ = displayed_distribution(bar_row_with_label(binary_card, "Other stored values (0)"))
        other_offsite_count = binary_other_count - short_term_count
        total_count = onsite_count + binary_other_count
        require(other_offsite_count > 0 and total_count > onsite_count, "Slide 14 three-group distribution is invalid.")

        rates = [
            rate_evidence["onsite_rate"],
            rate_evidence["short_term_remote_rate"],
            rate_evidence["other_offsite_rate"],
        ]
        rows = (
            work_arrangement_row(
                "Onsite",
                "Onsite",
                onsite_count,
                100 * onsite_count / total_count,
                100.0,
                rates[0],
                attrition_pill_class(rates[0], rates),
            ),
            work_arrangement_row(
                "Short-Term Remote Work",
                "Interim Modified – Short-Term Remote Work",
                short_term_count,
                100 * short_term_count / total_count,
                100 * short_term_count / onsite_count,
                rates[1],
                attrition_pill_class(rates[1], rates),
            ),
            work_arrangement_row(
                "Other offsite arrangements",
                "All remaining stored non-onsite values",
                other_offsite_count,
                100 * other_offsite_count / total_count,
                100 * other_offsite_count / onsite_count,
                rates[2],
                attrition_pill_class(rates[2], rates),
            ),
        )
        replacement_body = (
            '<div class="v6-definition-strip"><div><span class="v6-mini-label">Definition</span>'
            '<strong>Stored work arrangement grouped as Onsite, Short-Term Remote Work, and all other non-onsite values.</strong>'
            '</div><div><span class="v6-mini-label">Attrition lens</span>'
            '<strong>Six-month voluntary attrition is shown for every displayed group.</strong></div></div>'
            '<div class="v6-chart-area"><article class="card chart-card work-arrangement-three-group-card">'
            '<div class="v6-panel-heading"><span>Work arrangement · three grouped categories</span>'
            '<span>Distribution / 6-month attrition</span></div><div class="bar-list">'
            + "".join(rows)
            + '</div><p class="chart-footer">Other offsite arrangements combine every remaining stored non-onsite value; the rate is calculated from its aggregate exits and employee-snapshots.</p>'
            '</article></div>'
        )
        body_pattern = r'(<article class="card card-full v6-playbook-card">).*?(<div class="v6-source-line">.*?</div></article>)'
        stage, replacements = re.subn(
            body_pattern,
            lambda body: body.group(1) + replacement_body + body.group(2),
            stage,
            count=1,
            flags=re.S,
        )
        require(replacements == 1, "Could not replace the V7 Work arrangement slide body.")
        old_subtitle = "The source contains several work-arrangement labels; the two-group view is exploratory"
        new_subtitle = "Three grouped work arrangements; every row includes six-month voluntary attrition"
        require(stage.count(old_subtitle) == 1, "Slide 14 subtitle did not match the V6 source.")
        return stage.replace(old_subtitle, new_subtitle, 1)

    updated, replacements = re.subn(pattern, replace_stage, deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the V7 Work arrangement slide.")
    return updated, dict(rate_evidence)


def cto_org_attrition_row(
    label: str,
    display_count: int,
    display_share: float,
    width_percent: float,
    annual_rate: float,
    rate_class: str,
) -> str:
    """Render one current distribution row with a time-safe annual outcome pill."""
    rendered_rate = f"{annual_rate:.1f}%"
    return (
        '<div class="bar-row v4-inline-attrition-row"><div class="bar-label" title="'
        + html.escape(label)
        + '">'
        + html.escape(label)
        + '</div><div class="bar-track"><div class="bar-fill" style="width:'
        + f"{width_percent:.1f}%"
        + '"></div></div><div class="bar-value">'
        + f"{display_share:.0f}% &middot; {display_count:,}"
        + '<span class="v4-inline-attrition-rate v6-rate-pill '
        + rate_class
        + '" title="Annual voluntary attrition from the 2025-07-27 cohort: '
        + rendered_rate
        + '" aria-label="Annual voluntary attrition from the 2025-07-27 cohort: '
        + rendered_rate
        + '">'
        + rendered_rate
        + "</span></div></div>"
    )


def replace_cto_org_split_with_annual_attrition(
    deck: str,
    display_evidence: dict[str, Any],
    annual_evidence: dict[str, Any],
) -> str:
    """Add annual cohort attrition to slide 15's documented organizational split.

    The current distribution and annual attrition intentionally use different
    time labels: counts/shares are the current display snapshot, while rates
    use a historical baseline so exited employees stay in the denominator.
    """
    pattern = r'(<div class="slide-stage" id="slide-15".*?)(?=\n\s*<div class="slide-stage" id="slide-16")'

    def replace_stage(match: re.Match[str]) -> str:
        stage = match.group(1)
        display_rows = {str(row["category"]): row for row in display_evidence["category_distribution"]}
        annual_rows = {str(row["category"]): row for row in annual_evidence["rows"]}
        order = ("CTO", "Corp Fxn & BU")
        display_counts = [int(display_rows[label]["employee_count"]) for label in order]
        annual_rates = [float(annual_rows[label]["annual_attrition_rate_percent"]) for label in order]
        maximum_display_count = max(display_counts)
        rows = "".join(
            cto_org_attrition_row(
                label,
                int(display_rows[label]["employee_count"]),
                float(display_rows[label]["percentage"]),
                100 * int(display_rows[label]["employee_count"]) / maximum_display_count,
                float(annual_rows[label]["annual_attrition_rate_percent"]),
                attrition_pill_class(float(annual_rows[label]["annual_attrition_rate_percent"]), annual_rates),
            )
            for label in order
        )
        baseline = annual_evidence["baseline_snapshot"]
        outcome_end = annual_evidence["outcome_window"]["end_inclusive"]
        current_snapshot = display_evidence["snapshot_date"]
        annual_card = (
            '<article class="card chart-card engineering-cto-display-card" data-v7-cto-org-annual-attrition="true">'
            '<div class="v6-panel-heading"><span>Documented organizational split: CTO vs. Corp Fxn &amp; BU</span>'
            '<span>Distribution / annual attrition</span></div><div class="bar-list">'
            + rows
            + '</div><p class="chart-footer">Current distribution: '
            + html.escape(current_snapshot)
            + '. Annual voluntary attrition: '
            + html.escape(baseline)
            + ' cohort through '
            + html.escape(outcome_end)
            + '; CTO n='
            + f"{int(annual_rows['CTO']['eligible_employee_count']):,}"
            + ' / '
            + f"{int(annual_rows['CTO']['voluntary_exits']):,} exits; Corp Fxn &amp; BU n="
            + f"{int(annual_rows['Corp Fxn & BU']['eligible_employee_count']):,}"
            + ' / '
            + f"{int(annual_rows['Corp Fxn & BU']['voluntary_exits']):,} exits."
            + '</p></article>'
        )
        old_card = article_with_class(stage, "engineering-cto-display-card")
        stage = stage.replace(old_card, annual_card, 1)
        replacements = (
            (
                "The stored flag and the organization-derived split are related, not equivalent",
                "The stored flag and the organization-derived split are related, not equivalent; both show attrition",
            ),
            (
                "Active regular employees, excluding RF360",
                "Upper panel excludes RF360; lower organizational split uses all active regular employees",
            ),
            (
                "Six-month attrition is a voluntary exit after the snapshot; aggregate privacy-safe result.",
                "Upper panel: six-month voluntary attrition after its snapshot. Lower panel: annual voluntary attrition after the documented 2025-07-27 organizational cohort; aggregate internal-analysis result.",
            ),
            (
                '<span class="badge badge-info">6-month attrition</span>',
                '<span class="badge badge-info">Attrition comparison</span>',
            ),
        )
        for old, new in replacements:
            require(stage.count(old) == 1, f"Slide 15 must contain exactly one occurrence of {old!r}.")
            stage = stage.replace(old, new, 1)
        return stage

    updated, replacements = re.subn(pattern, replace_stage, deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the V7 CTO organizational split slide.")
    return updated


def build_job_family_august_snapshot_slide(
    snapshot_evidence: dict[str, Any],
    attrition_evidence: dict[str, Any],
) -> str:
    """Render the August Job family distribution with trailing-12-month pills."""
    snapshot = snapshot_evidence["snapshot"]
    categories = list(attrition_evidence["rows"])
    denominator = int(snapshot["observable_employee_count"])
    maximum = max(int(row["current_employee_count"]) for row in categories)
    rates = [float(row["trailing_12m_voluntary_attrition_rate_percent"]) for row in categories]
    rows = []
    for row in categories:
        label = str(row["category_label"])
        count = int(row["current_employee_count"])
        share = 100 * count / denominator
        width = 100 * count / maximum
        rate = row.get("trailing_12m_voluntary_attrition_rate_percent")
        baseline = int(row["baseline_employee_count"])
        exits = int(row["voluntary_exit_count"])
        if rate is None:
            pill_class = "attr-unavailable"
            pill_text = "Not estimable"
            tooltip = f"Attrition not estimable; August 2025 baseline cohort n={baseline:,}."
            unavailable = " is-unavailable"
        else:
            rate = float(rate)
            pill_class = attrition_pill_class(rate, rates)
            pill_text = f"{rate:.1f}%"
            tooltip = (
                f"Trailing 12-month voluntary attrition: {rate:.1f}%; "
                f"August 2025 baseline cohort n={baseline:,}; voluntary exits through 23 Aug 2026={exits:,}."
            )
            unavailable = ""
        escaped_label = html.escape(label, quote=True)
        escaped_tooltip = html.escape(tooltip, quote=True)
        rows.append(
            '<div class="bar-row job-family-august-bar-row"><div class="bar-label" title="'
            + escaped_label
            + '">'
            + html.escape(label)
            + '</div><div class="bar-track"><div class="bar-fill" style="width:'
            + f"{width:.4f}%"
            + '"></div></div><div class="bar-value">'
            + f"{share:.1f}% &middot; {count:,}"
            + '</div><span class="job-family-august-attrition v4-inline-attrition-rate v6-rate-pill '
            + pill_class
            + unavailable
            + '" title="'
            + escaped_tooltip
            + '" aria-label="'
            + escaped_tooltip
            + '">'
            + pill_text
            + "</span></div>"
        )
    return (
        '\n  <div class="slide-stage" id="slide-11" data-v6-playbook="true" data-v7-job-family-august-snapshot="true" data-v7-job-family-august-trailing-12m="true"><div class="slide-heading"><div>'
        '<h2 class="slide-title-text">Job family</h2>'
        '<p class="slide-subtitle">One fiscal-August snapshot with trailing 12-month attrition by historical Job family cohort</p>'
        '</div><span class="badge badge-info">August 2026 distribution / 12-month attrition</span></div>'
        '<article class="card card-full v6-playbook-card job-family-august-story"><div class="v6-definition-strip"><div><span class="v6-mini-label">Definition</span>'
        '<strong>Stored HRDA job family at the active-workforce snapshot.</strong></div><div><span class="v6-mini-label">Population</span>'
        '<strong>Current distribution: active regular employees with a populated job family; attrition: the August 2025 baseline cohort.</strong></div></div><div class="v6-chart-area">'
        '<article class="card chart-card job-family-august-card"><div class="v6-panel-heading"><span>Snapshot 2026-08-23 &middot; top 20 + Other</span>'
        + f'<span>{denominator:,} active regular employees &middot; Distribution / trailing 12m attrition</span></div><div class="bar-list">'
        + "".join(rows)
        + '</div><p class="chart-footer">Bars show the August 2026 workforce distribution; colored pills show strict voluntary attrition for the August 2025 cohort through 23 Aug 2026. Color is relative within this slide.</p>'
        '</article></div><div class="v6-source-line"><strong>Source:</strong> HRDA monthly workforce snapshots. Distribution uses 23 Aug 2026; attrition uses the active Regular cohort at 24 Aug 2025 and strict VOLUNTARY exits in (24 Aug 2025, 23 Aug 2026].</div></article></div>'
    )


def replace_job_family_with_august_snapshot(
    deck: str,
    snapshot_evidence: dict[str, Any],
    attrition_evidence: dict[str, Any],
) -> str:
    return replace_stage_fragment(deck, 11, build_job_family_august_snapshot_slide(snapshot_evidence, attrition_evidence))


def rehire_august_trailing_12m_label(row: dict[str, Any], rates: list[float]) -> str:
    """Render a comparable August-to-August attrition pill below one prevalence bar."""
    rate = float(row["trailing_12m_voluntary_attrition_rate_percent"])
    cohort = int(row["baseline_rehire_employee_count"])
    exits = int(row["voluntary_exit_count"])
    baseline = str(row["baseline_snapshot_date"])
    cutoff = str(row["outcome_cutoff_date"])
    return (
        '<span class="rehire-annual-attrition v6-rate-pill '
        + attrition_pill_class(rate, rates)
        + '" title="Annual voluntary attrition (12 months): active Rehire (1) cohort at '
        + html.escape(baseline)
        + ' followed through '
        + html.escape(cutoff)
        + f'; n={cohort:,}; voluntary exits={exits:,}" aria-label="Annual voluntary attrition (12 months) for FY{html.escape(str(row["fiscal_year"]))}: {rate:.1f}%">'
        + f"<strong>{rate:.1f}%</strong></span>"
    )


def retain_rehire_trend_years_for_august_view(stage: str) -> str:
    """Keep FY2024-FY2026 bars from the legacy prevalence visual."""
    visible_years = set(REHIRE_VISIBLE_FISCAL_YEARS)
    wrap_pattern = re.compile(r'<div\b[^>]*\bclass="[^"]*\btrend-bar-wrap\b[^"]*"[^>]*>', re.I)
    wrappers = list(wrap_pattern.finditer(stage))
    require(len(wrappers) >= len(visible_years), "Rehire source trend lacks the requested fiscal years.")
    found_years: set[str] = set()
    for match in reversed(wrappers):
        wrapper_end = matching_tag_end(stage, "div", match.start())
        wrapper = stage[match.start() : wrapper_end]
        year_match = re.search(r'<div class="trend-label">\s*<span>(\d{4})</span>', wrapper, flags=re.S)
        require(year_match is not None, "A Rehire source bar is missing its fiscal-year label.")
        year = year_match.group(1)
        found_years.add(year)
        if year not in visible_years:
            stage = stage[: match.start()] + stage[wrapper_end:]
    require(visible_years <= found_years, "Rehire source trend omits a requested fiscal year.")
    stage, replacements = re.subn(
        r'(<div class="trend-chart"\s+style="--bars:)\d+(")',
        rf'\g<1>{len(REHIRE_VISIBLE_FISCAL_YEARS)}\g<2>',
        stage,
        count=1,
    )
    require(replacements == 1, "Could not update the visible Rehire bar count.")
    return stage


def replace_rehire_with_august_trailing_12m_labels(deck: str, evidence: dict[str, Any]) -> str:
    """Show the latest Rehire cohort and its non-Rehire complement side by side."""
    pattern = r'(<div class="slide-stage" id="slide-16".*?)(?=\n\s*<div class="slide-stage" id="slide-17")'

    def replace_stage(match: re.Match[str]) -> str:
        stage = match.group(1)
        rows = list(evidence["rows"])
        rates = [float(row["trailing_12m_voluntary_attrition_rate_percent"]) for row in rows]
        total_count = sum(int(row["baseline_employee_count"]) for row in rows)
        max_count = max(int(row["baseline_employee_count"]) for row in rows)
        comparison_rows = []
        for row in rows:
            group = str(row["rehire_group"])
            count = int(row["baseline_employee_count"])
            exits = int(row["voluntary_exit_count"])
            rate = float(row["trailing_12m_voluntary_attrition_rate_percent"])
            share = 100.0 * count / total_count
            width = max(6.0, 100.0 * count / max_count)
            pill_class = annual_rate_class(rate, rates)
            title = (
                f"Annual voluntary attrition (12 months) for {group}: {rate:.1f}%; "
                f"24 Aug 2025 baseline n={count:,}; voluntary exits through 23 Aug 2026={exits:,}"
            )
            escaped_group = html.escape(group)
            escaped_title = html.escape(title, quote=True)
            comparison_rows.append(
                '<div class="bar-row v4-inline-attrition-row rehire-comparison-row">'
                f'<div class="bar-label" title="{escaped_group}">{escaped_group}</div>'
                f'<div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%"></div></div>'
                f'<div class="bar-value">{share:.1f}% · {count:,}'
                f'<span class="v4-inline-attrition-rate v6-rate-pill rehire-comparison-attrition {pill_class}" '
                f'title="{escaped_title}" aria-label="{escaped_title}">{rate:.1f}%</span></div></div>'
            )

        comparison_card = (
            '<article class="card chart-card rehire-comparison-card">'
            '<div class="v6-panel-heading"><span>Latest fiscal-August baseline · 24 Aug 2025</span>'
            '<span>Distribution / trailing 12m attrition</span></div>'
            '<div class="rehire-comparison-keyline"><span></span><span>Share of baseline cohort</span><span>Attrition</span></div>'
            '<div class="bar-list">' + "".join(comparison_rows) + '</div>'
            '<p class="rehire-followup-note"><strong>How to read it:</strong> bar length shows the baseline distribution; '
            'the colored pill shows strict voluntary attrition in the 12 months after the 24 Aug 2025 snapshot, through 23 Aug 2026.</p>'
            '</article>'
        )
        stage, replacements = re.subn(
            r'<article class="card chart-card">.*?</article>',
            comparison_card,
            stage,
            count=1,
            flags=re.S,
        )
        require(replacements == 1, "Could not replace the Rehire trend chart with the two-group comparison.")

        stage, replacements = re.subn(
            r'(<p class="slide-subtitle">).*?(</p>)',
            r'\1Latest fiscal-August Rehire status compared with the complementary non-Rehire group; both labels use the same 12-month cohort\2',
            stage,
            count=1,
            flags=re.S,
        )
        require(replacements == 1, "Could not update the Rehire subtitle.")
        stage, replacements = re.subn(
            r'(<span class="v6-mini-label">Definition</span><strong>).*?(</strong>)',
            r'\1Stored Rehire flag; the latest August cohort is split into Rehire and Not a rehire.\2',
            stage,
            count=1,
            flags=re.S,
        )
        require(replacements == 1, "Could not update the Rehire definition.")
        stage, replacements = re.subn(
            r'(<span class="badge badge-info">).*?(</span>)',
            r'\1Annual attrition (12 months)\2',
            stage,
            count=1,
        )
        require(replacements == 1, "Could not update the Rehire attrition badge.")
        source_line = (
            '<div class="v6-source-line"><strong>Source:</strong> HRDA - hrda.post_hire_monthly_worker_dtls and hrda.all_terminations. '
            'Baseline cohort: active Regular employees at the 24 Aug 2025 fiscal-August snapshot, split by stored is_rehire flag. '
            'Annual voluntary attrition (12 months): strict VOLUNTARY exits from the same cohort in (2025-08-24, 2026-08-23]. '
            'Aggregate privacy-safe result.</div>'
        )
        stage, replacements = re.subn(r'<div class="v6-source-line">.*?</div>', source_line, stage, count=1, flags=re.S)
        require(replacements == 1, "Could not update the Rehire source line.")
        stage = stage.replace(' data-v7-rehire-august-trailing-12m="true"', '')
        stage, replacements = re.subn(
            r'(<div class="slide-stage" id="slide-16")',
            r'\1 data-v7-rehire-complement-august-trailing-12m="true"',
            stage,
            count=1,
        )
        require(replacements == 1, "Could not mark the Rehire comparison slide.")
        return stage

    updated, replacements = re.subn(pattern, replace_stage, deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the V7 Rehire slide.")
    return updated


def replace_rehire_with_historical_august_trailing_12m_labels(deck: str, evidence: dict[str, Any]) -> str:
    """Show FY2024-FY2026 Rehire comparisons with one 12-month panel per year."""
    pattern = r'(<div class="slide-stage" id="slide-16".*?)(?=\n\s*<div class="slide-stage" id="slide-17")'

    def replace_stage(match: re.Match[str]) -> str:
        stage = match.group(1)
        rows_by_year: dict[str, list[dict[str, Any]]] = {}
        for row in evidence["rows"]:
            rows_by_year.setdefault(str(row["fiscal_year"]), []).append(row)

        all_panels: list[str] = []
        for fiscal_year in REHIRE_VISIBLE_FISCAL_YEARS:
            year_rows = rows_by_year[fiscal_year]
            require(
                tuple(str(row["rehire_group"]) for row in year_rows) == ("Rehire", "Not a rehire"),
                f"Historical Rehire rows are incomplete for FY{fiscal_year}.",
            )
            year_rates = [float(row["trailing_12m_voluntary_attrition_rate_percent"]) for row in year_rows]
            total_count = sum(int(row["baseline_employee_count"]) for row in year_rows)
            max_count = max(int(row["baseline_employee_count"]) for row in year_rows)
            baseline = str(year_rows[0]["baseline_snapshot_date"])
            cutoff = str(year_rows[0]["outcome_cutoff_date"])
            comparison_rows: list[str] = []
            for row in year_rows:
                group = str(row["rehire_group"])
                count = int(row["baseline_employee_count"])
                exits = int(row["voluntary_exit_count"])
                rate = float(row["trailing_12m_voluntary_attrition_rate_percent"])
                share = 100.0 * count / total_count
                width = max(6.0, 100.0 * count / max_count)
                pill_class = annual_rate_class(rate, year_rates)
                escaped_group = html.escape(group)
                escaped_baseline = html.escape(baseline)
                escaped_cutoff = html.escape(cutoff)
                title = (
                    f"FY{fiscal_year} {group}: {rate:.1f}% voluntary attrition; "
                    f"baseline {baseline}, n={count:,}; exits through {cutoff}={exits:,}"
                )
                escaped_title = html.escape(title, quote=True)
                comparison_rows.append(
                    '<div class="bar-row v4-inline-attrition-row rehire-comparison-row">'
                    f'<div class="bar-label" title="{escaped_group}">{escaped_group}</div>'
                    f'<div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%"></div></div>'
                    f'<div class="bar-value">{share:.1f}% &middot; {count:,}'
                    f'<span class="v4-inline-attrition-rate v6-rate-pill rehire-comparison-attrition {pill_class}" '
                    f'title="{escaped_title}" aria-label="{escaped_title}">{rate:.1f}%</span></div></div>'
                )
            all_panels.append(
                '<article class="card chart-card rehire-year-card">'
                f'<div class="v6-panel-heading"><span>FY{fiscal_year} cohort</span><span>Baseline {escaped_baseline}</span></div>'
                '<div class="rehire-comparison-keyline"><span></span><span>Share / count</span><span>Attrition</span></div>'
                '<div class="bar-list">' + "".join(comparison_rows) + '</div>'
                f'<div class="chart-footer">Followed through {escaped_cutoff}</div>'
                '</article>'
            )

        history_content = (
            '<div class="rehire-history-layout">'
            '<div class="rehire-history-grid">' + "".join(all_panels) + '</div>'
            '<p class="rehire-history-note"><strong>How to read it:</strong> each panel starts with its own fiscal-August active Regular baseline. '
            'Bar length shows the Rehire split; the colored pill shows strict voluntary attrition in the following 12 months.</p>'
            '</div>'
        )
        stage, replacements = re.subn(
            r'<article class="card chart-card">.*?</article>',
            history_content,
            stage,
            count=1,
            flags=re.S,
        )
        require(replacements == 1, "Could not replace the Rehire chart with the historical comparison panels.")

        stage, replacements = re.subn(
            r'(<p class="slide-subtitle">).*?(</p>)',
            r'\1Three fiscal-August cohorts (FY2024-FY2026) compare Rehire with the complementary Not a rehire group; each panel uses its own following 12-month cohort\2',
            stage,
            count=1,
            flags=re.S,
        )
        require(replacements == 1, "Could not update the historical Rehire subtitle.")
        stage, replacements = re.subn(
            r'(<span class="v6-mini-label">Definition</span><strong>).*?(</strong>)',
            r'\1Stored Rehire flag; each fiscal-August cohort is split into Rehire and Not a rehire.\2',
            stage,
            count=1,
            flags=re.S,
        )
        require(replacements == 1, "Could not update the historical Rehire definition.")
        stage, replacements = re.subn(
            r'(<span class="badge badge-info">).*?(</span>)',
            r'\g<1>12-month attrition by cohort\g<2>',
            stage,
            count=1,
        )
        require(replacements == 1, "Could not update the historical Rehire attrition badge.")
        source_line = (
            '<div class="v6-source-line"><strong>Source:</strong> HRDA - hrda.post_hire_monthly_worker_dtls and hrda.all_terminations. '
            'Baseline cohorts: active Regular employees at the fiscal-August closing snapshots for FY2024, FY2025, and FY2026, '
            'split by stored is_rehire flag. Strict VOLUNTARY exits are measured in the following 12 months for each baseline. '
            'Aggregate privacy-safe result.</div>'
        )
        stage, replacements = re.subn(r'<div class="v6-source-line">.*?</div>', source_line, stage, count=1, flags=re.S)
        require(replacements == 1, "Could not update the historical Rehire source line.")
        stage = stage.replace(' data-v7-rehire-august-trailing-12m="true"', '')
        stage, replacements = re.subn(
            r'(<div class="slide-stage" id="slide-16")',
            r'\1 data-v7-rehire-comparison-august-trailing-12m="true"',
            stage,
            count=1,
        )
        require(replacements == 1, "Could not mark the historical Rehire comparison slide.")
        return stage

    updated, replacements = re.subn(pattern, replace_stage, deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the V7 Rehire slide for historical replacement.")
    return updated


def commute_snapshot_display_bands(
    distribution: list[dict[str, Any]],
    unavailable_count: int,
) -> dict[str, int]:
    """Aggregate privacy-coalesced source bands to the five visible bands."""
    definitions: tuple[tuple[str, int, int | None], ...] = (
        ("0-<10 km", 0, 10),
        ("10-<20 km", 10, 20),
        ("20-<30 km", 20, 30),
        ("30+ km", 30, None),
    )
    result: dict[str, int] = {}
    assigned = 0
    for label, lower, upper in definitions:
        rows = [
            row for row in distribution
            if int(row["lower_km"]) >= lower and (upper is None or int(row["upper_km"]) <= upper)
        ]
        require(rows, f"Commute August distribution is missing source rows for {label}.")
        value = sum(int(row["employee_count"]) for row in rows)
        result[label] = value
        assigned += value
    require(assigned == sum(int(row["employee_count"]) for row in distribution), "Commute display bands do not reconcile to the matched population.")
    result["No calculable"] = int(unavailable_count)
    return result


def commute_historical_attrition_pill(
    rate: float | None,
    rates: list[float],
    pill_class_name: str,
    population_label: str,
) -> str:
    if rate is None:
        return (
            f'<span class="{pill_class_name} v6-rate-pill attr-unavailable is-unavailable" '
            'title="Historical six-month voluntary attrition is not estimable because estimated commute distance is not calculable for this group." '
            'aria-label="Historical six-month voluntary attrition: not estimable">N/E</span>'
        )
    return (
        f'<span class="{pill_class_name} v6-rate-pill {attrition_pill_class(rate, rates)}" '
        f'title="Historical six-month voluntary attrition after an {html.escape(population_label)} employee-snapshot: {rate:.1f}%" '
        f'aria-label="Historical six-month voluntary attrition for {html.escape(population_label)}: {rate:.1f}%">{rate:.1f}%</span>'
    )


def build_commute_august_snapshot_slide(
    snapshot_evidence: dict[str, Any],
    all_eligible_attrition_evidence: dict[str, Any],
    onsite_attrition_evidence: dict[str, Any],
) -> str:
    """Render current August distributions while retaining valid historical rate labels."""
    metrics = snapshot_evidence["metrics"]
    onsite_metrics = metrics["onsite"]
    all_counts = commute_snapshot_display_bands(snapshot_evidence["distribution"], int(metrics["unavailable_employee_count"]))
    onsite_counts = commute_snapshot_display_bands(snapshot_evidence["onsite_distribution"], int(onsite_metrics["unavailable_employee_count"]))
    all_total = int(metrics["eligible_employees"])
    onsite_total = int(onsite_metrics["eligible_employees"])
    all_attrition = commute_all_eligible_attrition_by_display_band(all_eligible_attrition_evidence)
    onsite_attrition = commute_onsite_attrition_by_display_band(onsite_attrition_evidence)
    all_rates = [float(row["attrition_rate_percent"]) for row in all_attrition.values() if row["attrition_rate_percent"] is not None]
    onsite_rates = [float(row["attrition_rate_percent"]) for row in onsite_attrition.values() if row["attrition_rate_percent"] is not None]

    def line(series: str, count: int, denominator: int, rates_by_band: dict[str, dict[str, float | int | None]], label: str, pill_class: str) -> str:
        share = 100 * count / denominator
        rate = rates_by_band[label]["attrition_rate_percent"]
        rates = all_rates if series == "All" else onsite_rates
        return (
            '<div class="commute-comparison-line commute-attrition-line"><span class="commute-series-name">'
            + series
            + '</span><div class="bar-track"><div class="bar-fill commute-series-'
            + ("all" if series == "All" else "onsite")
            + '" style="width:'
            + f"{share:.4f}%"
            + '"></div></div><span class="commute-series-value">'
            + f"{share:.1f}% &middot; {count:,}"
            + "</span>"
            + commute_historical_attrition_pill(
                None if rate is None else float(rate), rates, pill_class, "All eligible" if series == "All" else "Onsite"
            )
            + "</div>"
        )

    rows = []
    for label in ("0-<10 km", "10-<20 km", "20-<30 km", "30+ km", "No calculable"):
        rows.append(
            '<div class="commute-comparison-row"><div class="commute-comparison-label">'
            + html.escape(label)
            + '</div><div class="commute-comparison-series">'
            + line("All", all_counts[label], all_total, all_attrition, label, "commute-all-eligible-attrition")
            + line("Onsite", onsite_counts[label], onsite_total, onsite_attrition, label, "commute-onsite-attrition")
            + "</div></div>"
        )
    return (
        '\n  <div class="slide-stage" id="slide-19" data-v6-playbook="true" data-v7-commute-august-snapshot="true"><div class="slide-heading"><div>'
        '<h2 class="slide-title-text">Commute distance</h2><p class="slide-subtitle">Fiscal-August distribution; historical six-month attrition labels remain separate</p>'
        '</div><span class="badge badge-info">August 2026 snapshot</span></div><article class="card card-full v6-playbook-card"><div class="v6-definition-strip"><div><span class="v6-mini-label">Definition</span>'
        '<strong>Estimated straight-line distance between residential and office postal centroids.</strong></div><div><span class="v6-mini-label">Population</span>'
        '<strong>All active regular employees and the Onsite subset at 23 Aug 2026.</strong></div></div><div class="v6-chart-area"><div class="commute-distance-comparison-layout">'
        '<article class="card chart-card commute-distance-card commute-distance-comparison-card"><div class="card-title">Distance bands: all eligible vs Onsite</div>'
        + f'<div class="commute-comparison-legend"><span><i class="commute-legend-swatch commute-series-all"></i>All eligible ({all_total:,})</span><span><i class="commute-legend-swatch commute-series-onsite"></i>Onsite ({onsite_total:,})</span><span><i class="commute-legend-swatch commute-series-missing"></i>No calculable</span></div>'
        + '<div class="commute-comparison-list">'
        + "".join(rows)
        + '</div><p class="chart-footer"><strong>Distribution:</strong> snapshot 23 Aug 2026. <strong>Attrition labels:</strong> historical six-month voluntary attrition for All eligible and Onsite bands; each uses its own employee-snapshot denominator. No calculable has no valid distance exposure, so its attrition is not estimable.</p>'
        '</article></div></div><div class="v6-source-line"><strong>Source:</strong> HRDA fiscal-August workforce snapshot, Qualcomm office catalog, and GeoNames postal centroids. Distance is a geographic approximation, not route distance, travel time, or actual commute.</div></article></div>'
    )


def replace_commute_distance_with_august_snapshot(
    deck: str,
    snapshot_evidence: dict[str, Any],
    all_eligible_attrition_evidence: dict[str, Any],
    onsite_attrition_evidence: dict[str, Any],
) -> str:
    return replace_stage_fragment(
        deck,
        19,
        build_commute_august_snapshot_slide(snapshot_evidence, all_eligible_attrition_evidence, onsite_attrition_evidence),
    )


def build_manager_timezone_august_trailing_12m_slide(evidence: dict[str, Any]) -> str:
    """Render current August distribution and its August-to-August T12 labels."""
    category_order = (
        ("same_office_site", "Same assigned office site"),
        ("different_site_up_to_4_hours", "Different site &middot; &le;4 h offset"),
        ("different_site_more_than_4_hours", "Different site &middot; &gt;4 h offset"),
    )
    latest = evidence["latest_distribution"]
    annual = evidence["annual_attrition"]
    diagnostics = evidence["diagnostics"]
    current_pairs = int(diagnostics["current_pair_count"])
    current_unmapped = int(latest["unmapped_time_zone_proxy"]["employee_count"])
    current_categorized = sum(int(latest[key]["employee_count"]) for key, _ in category_order)
    require(current_categorized + current_unmapped == current_pairs, "Manager proximity current coverage does not reconcile.")
    maximum = max(int(latest[key]["employee_count"]) for key, _ in category_order)
    rates = [float(annual[key]["attrition_rate_percent"]) for key, _ in category_order]
    rows = []
    for key, label in category_order:
        current_count = int(latest[key]["employee_count"])
        share = 100 * current_count / current_pairs
        rate_row = annual[key]
        cohort = int(rate_row["employee_count"])
        exits = int(rate_row["voluntary_exit_count"])
        rate = float(rate_row["attrition_rate_percent"])
        pill = (
            '<span class="v4-inline-attrition-rate v6-rate-pill manager-timezone-annual-pill '
            + annual_rate_class(rate, rates)
            + '" title="Annual voluntary attrition (12 months) for '
            + html.unescape(label)
            + ': '
            + f"{rate:.1f}% &middot; baseline 24 Aug 2025 n={cohort:,}; voluntary exits through 23 Aug 2026={exits:,}" "\n"
            + 'aria-label="Annual voluntary attrition (12 months) for '
            + html.unescape(label)
            + f': {rate:.1f}%">{rate:.1f}%</span>'
        )
        rows.append(
            '<div class="bar-row v4-inline-attrition-row manager-timezone-bar-row"><div class="bar-label">'
            + label
            + '</div><div class="bar-track"><div class="bar-fill" style="width:'
            + f"{100 * current_count / maximum:.4f}%"
            + '"></div></div><div class="bar-value">'
            + f"{share:.1f}% &middot; {current_count:,}"
            + pill
            + "</div></div>"
        )
    return (
        '\n  <div class="slide-stage" id="slide-42" data-v6-playbook="true" data-v7-manager-timezone-proximity="true" data-v7-manager-timezone-august-trailing-12m="true"><div class="slide-heading"><div>'
        '<h2 class="slide-title-text">Assigned office-site proximity to manager</h2><p class="slide-subtitle">Same assigned site vs. different site by IANA time-zone offset &middot; not residential distance</p>'
        '</div><span class="badge badge-info">Distribution + annual attrition (12 months)</span></div><article class="card card-full v6-playbook-card manager-timezone-proximity-card">'
        '<div class="v6-definition-strip"><div><span class="v6-mini-label">Definition</span><strong>Stored office_site match first; otherwise assigned-office time-zone difference of &le;4 h or &gt;4 h.</strong></div>'
        '<div><span class="v6-mini-label">Attrition label</span><strong>Annual voluntary attrition (12 months): 24 Aug 2025 baseline cohort followed through 23 Aug 2026.</strong></div></div>'
        '<div class="v6-chart-area manager-timezone-chart-area"><article class="card chart-card manager-timezone-distribution-card"><div class="v6-panel-heading"><span>Assigned-site distribution at 23 Aug 2026</span><span>Annual voluntary attrition (12 months)</span></div>'
        '<div class="bar-list">'
        + "".join(rows)
        + f'</div><p class="chart-footer"><strong>{current_categorized:,} of {current_pairs:,} employee-manager pairs ({100 * current_categorized / current_pairs:.1f}%)</strong> reconcile to the three categories. The remaining {current_unmapped:,} pairs are retained as mapping coverage, not assigned to a time-zone band.</p>'
        '</article></div><div class="v6-source-line"><strong>Source:</strong> HRDA workforce snapshots + Qualcomm office catalog; IANA zone inferred from office coordinates. This is an assigned-office proxy only: it does not measure home location, physical presence, commute distance, travel time, or collaboration.</div></article></div>'
    )


def replace_residential_distance_with_manager_timezone_august_trailing_12m(
    deck: str,
    evidence: dict[str, Any],
) -> str:
    updated = replace_stage_fragment(deck, 42, build_manager_timezone_august_trailing_12m_slide(evidence))
    nav_pattern = r'(<button class="nav-pill(?: [^"]*)?" data-slide="\d+">\d+\.) Residential distance from manager(</button>)'
    updated, replacements = re.subn(
        nav_pattern,
        r'\1 Assigned office-site proximity to manager\2',
        updated,
        count=1,
    )
    require(replacements == 1, "Could not update the manager-proximity navigation label.")
    return updated


def rehire_annual_label(row: dict[str, Any], rate_class: str) -> str:
    """Render a year-specific, publication-safe attrition label."""
    status = str(row["publication_status"])
    year = str(row["fiscal_year"])
    if status in {"publishable", "publishable_mature_partial_year"}:
        rate = float(row["attrition_rate_percent"])
        partial = status == "publishable_mature_partial_year"
        qualifier = "*" if partial else ""
        return (
            '<span class="rehire-annual-attrition v6-rate-pill '
            + rate_class
            + (" is-partial" if partial else "")
            + '" title="12-month voluntary attrition after active Rehire (1) snapshot exposures in FY'
            + html.escape(year)
            + '" aria-label="12-month voluntary attrition in FY'
            + html.escape(year)
            + ': '
            + f"{rate:.1f}%"
            + '">'
            + '<strong>'
            + f"{rate:.1f}%"
            + "</strong>"
            + qualifier
            + "</span>"
        )
    if status == "not_comparable_source_era":
        text = "Not comparable"
        title = "The pre-2022 source era is not comparable to the current rehire definition."
    elif status == "not_estimable_incomplete_followup":
        text = "Not estimable"
        title = "A complete 12-month follow-up is not yet observable for this fiscal year."
    else:
        raise ValueError(f"Unexpected rehire annual publication status: {status!r}")
    return (
        '<span class="rehire-annual-attrition v6-rate-pill attr-unavailable is-unavailable" title="'
        + html.escape(title)
        + '">'
        + text
        + "</span>"
    )


def rehire_fy2026_observed_label(evidence: dict[str, Any]) -> str:
    """Render a realized FY2026 rate without implying prospective follow-up."""
    row = evidence["row"]
    rate = float(row["observed_voluntary_attrition_rate_percent"])
    exits = int(row["voluntary_exit_count"])
    headcount = float(row["average_monthly_rehire_headcount"])
    months = int(row["observed_snapshot_count"])
    first_date = html.escape(str(row["first_snapshot_date"]))
    last_date = html.escape(str(row["last_snapshot_date"]))
    return (
        '<span class="rehire-annual-attrition rehire-observed-period-attrition v6-rate-pill attr-mid is-observed" '
        'title="Observed FY2026 voluntary attrition: '
        + f"{exits:,} exits / {headcount:,.0f} average monthly active Rehire headcount; "
        + f"{months} monthly snapshots from {first_date} through {last_date}. "
        + 'This is a realized fiscal-year rate, not the prospective 12-month metric used for FY2024 and FY2025." '
        + 'aria-label="Observed FY2026 voluntary attrition: '
        + f"{rate:.1f}%; realized fiscal-year rate, not prospective\">"
        + '<strong>'
        + f"{rate:.1f}%"
        + '</strong></span>'
    )


def add_rehire_label_to_trend_year(stage: str, year: str, label: str) -> str:
    """Append one annual-attrition label under the matching trend-chart year."""
    wrap_pattern = re.compile(r'<div\b[^>]*\bclass="[^"]*\btrend-bar-wrap\b[^"]*"[^>]*>', re.I)
    for match in wrap_pattern.finditer(stage):
        wrapper_end = matching_tag_end(stage, "div", match.start())
        wrapper = stage[match.start() : wrapper_end]
        if f"<span>{year}</span>" not in wrapper:
            continue
        trend_label = re.search(r'(<div class="trend-label">.*?)(</div>)', wrapper, flags=re.S)
        require(trend_label is not None, f"Slide 16 trend label is missing for FY{year}.")
        updated_wrapper = (
            wrapper[: trend_label.start()]
            + trend_label.group(1)
            + label
            + trend_label.group(2)
            + wrapper[trend_label.end() :]
        )
        return stage[: match.start()] + updated_wrapper + stage[wrapper_end:]
    raise ValueError(f"Slide 16 is missing its trend bar for FY{year}.")


def retain_rehire_trend_years(stage: str, evidence: dict[str, Any]) -> str:
    """Keep only the requested fiscal years in the Rehire prevalence chart."""
    evidence_years = tuple(str(row["fiscal_year"]) for row in evidence["rows"])
    visible_years = set(REHIRE_VISIBLE_FISCAL_YEARS)
    require(visible_years <= set(evidence_years), "The requested Rehire display years are absent from the evidence.")

    wrap_pattern = re.compile(r'<div\b[^>]*\bclass="[^"]*\btrend-bar-wrap\b[^"]*"[^>]*>', re.I)
    wrappers = list(wrap_pattern.finditer(stage))
    require(len(wrappers) == len(evidence_years), "Slide 16 must contain one Rehire trend bar per audited fiscal year before filtering.")
    found_years: list[str] = []
    for match in reversed(wrappers):
        wrapper_end = matching_tag_end(stage, "div", match.start())
        wrapper = stage[match.start() : wrapper_end]
        year_match = re.search(r'<div class="trend-label">\s*<span>(\d{4})</span>', wrapper, flags=re.S)
        require(year_match is not None, "A Rehire trend bar is missing its fiscal-year label.")
        year = year_match.group(1)
        found_years.append(year)
        if year not in visible_years:
            stage = stage[: match.start()] + stage[wrapper_end:]
    require(set(found_years) == set(evidence_years), "Rehire trend-bar years do not reconcile to the evidence.")

    stage, replacements = re.subn(
        r'(<div class="trend-chart"\s+style="--bars:)\d+(")',
        rf'\g<1>{len(REHIRE_VISIBLE_FISCAL_YEARS)}\g<2>',
        stage,
        count=1,
    )
    require(replacements == 1, "Could not update the visible Rehire bar count.")
    return stage


def replace_rehire_with_annual_attrition_labels(
    deck: str,
    evidence: dict[str, Any],
    fy2026_observed_evidence: dict[str, Any],
) -> str:
    """Replace pooled top pills with fiscal-year attrition below each bar."""
    pattern = r'(<div class="slide-stage" id="slide-16".*?)(?=\n\s*<div class="slide-stage" id="slide-17")'

    def replace_stage(match: re.Match[str]) -> str:
        stage = match.group(1)
        summary = re.search(r'<div\b[^>]*\bclass="[^"]*\bv4-inline-attrition-summary\b[^"]*"[^>]*>', stage, flags=re.I)
        require(summary is not None, "Slide 16 pooled attrition pills are missing.")
        summary_end = matching_tag_end(stage, "div", summary.start())
        stage = stage[: summary.start()] + stage[summary_end:]
        stage = retain_rehire_trend_years(stage, evidence)
        displayed_rows = [
            row for row in evidence["rows"] if str(row["fiscal_year"]) in REHIRE_VISIBLE_FISCAL_YEARS
        ]
        require(
            tuple(str(row["fiscal_year"]) for row in displayed_rows) == REHIRE_VISIBLE_FISCAL_YEARS,
            "Rehire display years must be FY2024 through FY2026 in order.",
        )
        publishable_rates = [
            float(row["attrition_rate_percent"])
            for row in displayed_rows
            if str(row["publication_status"]).startswith("publishable")
        ]
        require(publishable_rates, "Rehire evidence has no publishable annual attrition rates.")
        for row in displayed_rows:
            year = str(row["fiscal_year"])
            if year == "2026":
                stage = add_rehire_label_to_trend_year(stage, year, rehire_fy2026_observed_label(fy2026_observed_evidence))
                continue
            rate_class = (
                attrition_pill_class(float(row["attrition_rate_percent"]), publishable_rates)
                if str(row["publication_status"]).startswith("publishable")
                else "attr-unavailable"
            )
            stage = add_rehire_label_to_trend_year(stage, year, rehire_annual_label(row, rate_class))

        stage, replacements = re.subn(
            r'(<div class="slide-stage" id="slide-16")',
            r'\1 data-v7-rehire-annual-attrition="true"',
            stage,
            count=1,
        )
        require(replacements == 1, "Could not mark the V7 annual Rehire slide.")
        replacements = (
            (
                "A source-definition break means the two historical periods should remain separate",
                "Annual Rehire prevalence; FY2024-FY2025 prospective 12-month attrition; FY2026 observed fiscal-year rate (not prospective)",
            ),
            (
                "Stored rehire flag; historical definition changes need to remain visible.",
                "Stored rehire flag; FY2024-FY2025 show prospective attrition and FY2026 a realized fiscal-year rate.",
            ),
            (
                "Annual flag prevalence",
                "Annual Rehire prevalence; FY2024-FY2025 12-month attrition and FY2026 observed fiscal-year attrition",
            ),
            (
                "The series changes source era from 2022-10-23.",
                "FY2024-FY2025 are prospective 12-month voluntary-exit rates (FY2025* uses mature snapshots only). FY2026 is a realized fiscal-year rate: voluntary exits / average monthly active Rehire headcount; it is not directly comparable to the prospective rates.",
            ),
            (
                "Six-month attrition is a voluntary exit after the snapshot; aggregate privacy-safe result.",
                "FY2024-FY2025 attrition is a voluntary exit after the snapshot; FY2026 is an observed fiscal-year rate; aggregate privacy-safe result.",
            ),
        )
        for old, new in replacements:
            require(stage.count(old) == 1, f"Slide 16 must contain exactly one instance of {old!r}.")
            stage = stage.replace(old, new, 1)
        title = '<div class="card-title">Annual Rehire prevalence; FY2024-FY2025 12-month attrition and FY2026 observed fiscal-year attrition</div>'
        followup_note = (
            '<p class="rehire-followup-note"><strong>FY2025*</strong> uses only snapshots with a complete '
            '12-month follow-up (through 24 Aug 2025); it is not based on all FY2025 snapshots. '
            '<strong>FY2026</strong> is realized voluntary attrition in the 12 observed fiscal-year snapshots, '
            'not a prospective 12-month rate.</p>'
        )
        require(stage.count(title) == 1, "Could not locate the Rehire chart title for its follow-up note.")
        stage = stage.replace(title, title + followup_note, 1)
        stage, replacements = re.subn(
            r'(<span class="badge badge-info">)6-month attrition(</span>)',
            r'\1Annual attrition\2',
            stage,
            count=1,
        )
        require(replacements == 1, "Could not update the Rehire attrition badge.")
        return stage

    updated, replacements = re.subn(pattern, replace_stage, deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the V7 Rehire slide.")
    return updated


def validate_rehire_fy2024plus_slide(
    deck: str,
    evidence: dict[str, Any],
    fy2026_observed_evidence: dict[str, Any],
) -> None:
    """Validate the targeted Rehire refresh without rewriting unrelated slides."""
    rehire_html = stage_fragment(deck, 16)
    require('data-v7-rehire-annual-attrition="true"' in rehire_html, "Annual Rehire treatment is missing.")
    require('v4-inline-attrition-summary' not in rehire_html, "Rehire still has pooled attrition pills above the bars.")
    require(rehire_html.count('<div class="trend-bar-wrap">') == len(REHIRE_VISIBLE_FISCAL_YEARS), "Rehire must retain only three fiscal-year bars.")
    require(rehire_html.count('class="rehire-annual-attrition') == len(REHIRE_VISIBLE_FISCAL_YEARS), "Rehire must show one attrition status below every displayed bar.")
    require('FY2024-FY2025 prospective 12-month attrition; FY2026 observed fiscal-year rate (not prospective)' in rehire_html, "Rehire subtitle does not distinguish its two attrition measures.")
    require('style="--bars:3"' in rehire_html, "Rehire chart must reserve space for only three displayed years.")
    evidence_years = {str(row["fiscal_year"]) for row in evidence["rows"]}
    for year in REHIRE_VISIBLE_FISCAL_YEARS:
        require(f'<span>{year}</span>' in rehire_html, f"Rehire is missing displayed FY{year}.")
    for year in evidence_years - set(REHIRE_VISIBLE_FISCAL_YEARS):
        require(f'<span>{year}</span>' not in rehire_html, f"Rehire must not retain FY{year}.")
    require(
        'class="rehire-followup-note"' in rehire_html
        and 'it is not based on all FY2025 snapshots.' in rehire_html
        and 'not a prospective 12-month rate.' in rehire_html,
        "Rehire must visibly explain the FY2025 partial follow-up and the FY2026 observed metric.",
    )
    require('FY2024-FY2025 attrition is a voluntary exit after the snapshot; FY2026 is an observed fiscal-year rate' in rehire_html, "Rehire source note must distinguish the two measures.")

    displayed_rows = [
        row for row in evidence["rows"] if str(row["fiscal_year"]) in REHIRE_VISIBLE_FISCAL_YEARS
    ]
    publishable_rows = [
        row for row in displayed_rows if str(row["publication_status"]).startswith("publishable")
    ]
    publishable_rates = [float(row["attrition_rate_percent"]) for row in publishable_rows]
    for row in displayed_rows:
        status = str(row["publication_status"])
        year = str(row["fiscal_year"])
        if year == "2026":
            observed_row = fy2026_observed_evidence["row"]
            observed_rate = float(observed_row["observed_voluntary_attrition_rate_percent"])
            require(
                f'>{observed_rate:.1f}%</strong></span>' in rehire_html,
                "Rehire is missing the FY2026 observed fiscal-year rate.",
            )
            require(
                'class="rehire-annual-attrition rehire-observed-period-attrition v6-rate-pill attr-mid is-observed"' in rehire_html,
                "Rehire FY2026 observed rate is missing its distinct non-prospective marker.",
            )
            continue
        if status.startswith("publishable"):
            require(f'>{float(row["attrition_rate_percent"]):.1f}%</strong>' in rehire_html, f"Rehire is missing FY{year} annual rate.")
            expected_class = attrition_pill_class(float(row["attrition_rate_percent"]), publishable_rates)
            require(
                f'class="rehire-annual-attrition v6-rate-pill {expected_class}' in rehire_html,
                f"Rehire FY{year} lacks its expected {expected_class} attrition pill.",
            )
        else:
            raise ValueError(f"Unexpected displayed Rehire annual status: {status!r}")


def refresh_rehire_slide_only() -> None:
    """Regenerate only Rehire from the source stage when a full build is unavailable."""
    require(OUTPUT_DECK.exists(), f"Missing current V7 deck: {OUTPUT_DECK}")
    require(MANIFEST_FILE.exists(), f"Missing current V7 manifest: {MANIFEST_FILE}")
    require(SOURCE_DECK.exists(), f"Missing V6 source deck: {SOURCE_DECK}")
    require(REHIRE_ANNUAL_ATTRITION_EVIDENCE_FILE.exists(), f"Missing Rehire evidence: {REHIRE_ANNUAL_ATTRITION_EVIDENCE_FILE}")
    require(REHIRE_FY2026_OBSERVED_ATTRITION_EVIDENCE_FILE.exists(), f"Missing FY2026 observed Rehire evidence: {REHIRE_FY2026_OBSERVED_ATTRITION_EVIDENCE_FILE}")
    evidence = load_rehire_annual_attrition_evidence()
    fy2026_observed_evidence = load_rehire_fy2026_observed_attrition_evidence()

    deck_hash = digest(OUTPUT_DECK)
    before = OUTPUT_DECK.read_text(encoding="utf-8")
    source_deck = SOURCE_DECK.read_text(encoding="utf-8")
    source_rehire_stage = stage_fragment(source_deck, 16)
    after = replace_stage_fragment(before, 16, source_rehire_stage)
    after = replace_rehire_with_annual_attrition_labels(after, evidence, fy2026_observed_evidence)
    validate_rehire_fy2024plus_slide(after, evidence, fy2026_observed_evidence)
    require(digest(OUTPUT_DECK) == deck_hash, "The deck changed concurrently; the Rehire refresh was not written.")

    temporary_deck = OUTPUT_DECK.with_suffix(".rehire-fy2024plus.tmp")
    temporary_deck.write_text(after, encoding="utf-8")
    temporary_deck.replace(OUTPUT_DECK)
    written_deck_hash = digest(OUTPUT_DECK)

    manifest_hash = digest(MANIFEST_FILE)
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    updated_slide = manifest.setdefault("updated_slide_16", {})
    updated_slide.update(
        {
            "slide_number": 16,
            "title": "Rehire",
            "visual": "Annual Rehire prevalence bars for FY2024 onward, with prospective 12-month voluntary attrition for FY2024-FY2025 and a separately labeled realized FY2026 fiscal-year rate.",
            "displayed_fiscal_years": list(REHIRE_VISIBLE_FISCAL_YEARS),
        }
    )
    evidence_entry = manifest.setdefault("rehire_annual_attrition_evidence", {})
    evidence_entry.update(
        {
            "path": str(REHIRE_ANNUAL_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(REHIRE_ANNUAL_ATTRITION_EVIDENCE_FILE),
            "query": evidence["query"],
            "query_sha256": evidence["query_sha256"],
            "fiscal_years": [str(row["fiscal_year"]) for row in evidence["rows"]],
            "displayed_fiscal_years": list(REHIRE_VISIBLE_FISCAL_YEARS),
            "publication_statuses": [str(row["publication_status"]) for row in evidence["rows"]],
        }
    )
    observed_evidence_entry = manifest.setdefault("rehire_fy2026_observed_attrition_evidence", {})
    observed_evidence_entry.update(
        {
            "path": str(REHIRE_FY2026_OBSERVED_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(REHIRE_FY2026_OBSERVED_ATTRITION_EVIDENCE_FILE),
            "query": fy2026_observed_evidence["query"],
            "query_sha256": fy2026_observed_evidence["query_sha256"],
            "definition": "FY2026 realized voluntary exits / average monthly active Rehire headcount; not prospective.",
            "row": fy2026_observed_evidence["row"],
        }
    )
    validation = manifest.setdefault("validation", {})
    validation.update(
        {
            "rehire_annual_attrition_statuses_visible": len(REHIRE_VISIBLE_FISCAL_YEARS),
            "rehire_displayed_fiscal_years": list(REHIRE_VISIBLE_FISCAL_YEARS),
            "rehire_pooled_six_month_pills_removed": True,
            "rehire_fy2026_observed_rate_visible": True,
            "rehire_fy2024plus_refresh_outcome": "pass",
        }
    )
    manifest["output_deck"] = {
        "path": str(OUTPUT_DECK.relative_to(ROOT)).replace("\\", "/"),
        "sha256": written_deck_hash,
    }
    require(digest(OUTPUT_DECK) == written_deck_hash, "The deck changed before its Rehire manifest could be written.")
    require(digest(MANIFEST_FILE) == manifest_hash, "The manifest changed concurrently; the Rehire refresh was not written.")
    temporary_manifest = MANIFEST_FILE.with_suffix(".rehire-fy2024plus.tmp")
    temporary_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_manifest.replace(MANIFEST_FILE)
    print(OUTPUT_DECK)
    print(MANIFEST_FILE)


def add_team_post_exit_value_labels(deck: str) -> str:
    """Make the six monthly cumulative-attrition values visible in slides 9–10.

    V7 inherits these two charts from V6.  Apply the visual treatment at the
    final-render boundary so a V7 rebuild cannot discard the values as a
    hand-edited HTML change.
    """
    trace_signature = "function trace(rows, name, color, dash) {"
    labeled_trace_signature = "function trace(rows, name, color, dash, textPosition) {"
    trace_mode = "            mode: 'lines+markers',"
    labeled_trace_mode = "            mode: 'lines+markers+text',"
    marker_line = "            marker: { color: color, size: 7 },"
    labeled_marker_lines = """            marker: { color: color, size: 7 },
            text: points.map(function (row) { return row.follow_month === 0 ? '' : row.cumulative_incidence_percent.toFixed(1) + '%'; }),
            textposition: textPosition,
            textfont: { family: 'Aptos, Segoe UI, system-ui, sans-serif', size: 12, color: color },
            cliponaxis: false,"""
    exposed_call = "            trace(exposed, 'Team after one initial departure', colors.accent, 'solid'),"
    labeled_exposed_call = "            trace(exposed, 'Team after one initial departure', colors.accent, 'solid', 'top center'),"
    reference_call = "            trace(reference, 'Similar-size teams with no recent departure', colors.accent2, 'dash')"
    labeled_reference_call = "            trace(reference, 'Similar-size teams with no recent departure', colors.accent2, 'dash', 'bottom center')"
    compact_margin = "            margin: { t: 30, r: 14, b: 45, l: 62 },"
    labeled_margin = "            margin: { t: 30, r: 34, b: 45, l: 62 },"

    def replace_once(stage: str, old: str, new: str, description: str, slide_number: int) -> str:
        require(stage.count(old) == 1, f"Slide {slide_number} must contain exactly one {description}.")
        return stage.replace(old, new, 1)

    def replace_stage(match: re.Match[str], slide_number: int) -> str:
        stage = match.group(1)
        stage = replace_once(stage, trace_signature, labeled_trace_signature, "team-post-exit trace function", slide_number)
        stage = replace_once(stage, trace_mode, labeled_trace_mode, "team-post-exit trace mode", slide_number)
        stage = replace_once(stage, marker_line, labeled_marker_lines, "team-post-exit marker definition", slide_number)
        stage = replace_once(stage, exposed_call, labeled_exposed_call, "exposed-series trace call", slide_number)
        stage = replace_once(stage, reference_call, labeled_reference_call, "reference-series trace call", slide_number)
        stage = replace_once(stage, compact_margin, labeled_margin, "team-post-exit chart margin", slide_number)
        return stage

    updated = deck
    for slide_number in (9, 10):
        pattern = rf'(<div class="slide-stage" id="slide-{slide_number}".*?)(?=\n\s*<div class="slide-stage" id="slide-{slide_number + 1}")'
        updated, replacements = re.subn(
            pattern,
            lambda match, number=slide_number: replace_stage(match, number),
            updated,
            count=1,
            flags=re.S,
        )
        require(replacements == 1, f"Could not label V7 team-post-exit slide {slide_number}.")
    return updated


def enable_internal_aggregate_visibility(deck: str) -> str:
    updated = re.sub(r'\s+v6-hidden-row(?=\s|")', '', deck)
    updated = re.sub(r'\s*<div class="v6-truncation-note">.*?</div>', '', updated, flags=re.S)
    updated = updated.replace('<span class="badge badge-info">Presentation</span>', '<span class="badge badge-info">Internal analysis</span>', 1)
    updated = updated.replace('<body class="theme-light-classic">', '<body class="theme-light-classic" data-deliverable-mode="internal_analysis">', 1)
    return updated


def remove_obsolete_prior_experience_slide(deck: str) -> str:
    """Remove the blank prior-experience slide and close the displayed nav gap.

    Stage IDs are deliberately retained for all following slides: the V7
    transformations use those stable technical IDs.  The template navigates by
    DOM order, so only nav indexes and visible labels need to be contiguous.
    """
    stage_pattern = r'\s*<div class="slide-stage" id="slide-18".*?(?=\n\s*<div class="slide-stage" id="slide-19")'
    updated, replacements = re.subn(stage_pattern, '\n', deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate exactly one obsolete V7 prior-experience slide.")

    styles_pattern = (
        r'\n\s*\.prior-experience-annual-layout\s*\{.*?'
        r'\.prior-experience-annual-side \.provenance-status\s*\{[^}]*\}\n'
    )
    updated, replacements = re.subn(styles_pattern, '\n', updated, count=1, flags=re.S)
    require(replacements == 1, "Could not remove the obsolete prior-experience chart styles.")
    for selector in (
        r'\n\s*\.prior-experience-annual-layout,',
        r'\n\s*\.v6-chart-area \.prior-experience-annual-layout,',
    ):
        updated, replacements = re.subn(selector, '', updated, count=1)
        require(replacements == 1, "Could not remove an obsolete prior-experience responsive selector.")

    nav_pattern = (
        r'\s*<button class="nav-pill" data-slide="17">'
        r'18\. Annual voluntary attrition by prior experience</button>'
    )
    updated, replacements = re.subn(nav_pattern, '', updated, count=1)
    require(replacements == 1, "Could not remove the obsolete prior-experience navigation item.")

    nav_button_pattern = (
        r'(?P<prefix><button class="nav-pill(?: [^"]*)?" data-slide=")'
        r'(?P<index>\d+)(?P<middle>">)(?P<label>\d+)'
        r'(?P<suffix>\. [^<]+</button>)'
    )

    def renumber_nav_button(match: re.Match[str]) -> str:
        index = int(match.group("index"))
        label = int(match.group("label"))
        require(label == index + 1, "V7 navigation labels must match their 0-based indexes before slide removal.")
        if index < 18:
            return match.group(0)
        return (
            f'{match.group("prefix")}{index - 1}{match.group("middle")}'
            f'{label - 1}{match.group("suffix")}'
        )

    updated, nav_buttons = re.subn(nav_button_pattern, renumber_nav_button, updated)
    require(nav_buttons == 49, "V7 must retain 49 navigation buttons after removing slide 18.")
    for old, new in (
        ('<span class="nav-section-range">6–19</span>', '<span class="nav-section-range">6–18</span>'),
        ('<span class="nav-section-range">20–27</span>', '<span class="nav-section-range">19–26</span>'),
        ('<span class="nav-section-range">28–39</span>', '<span class="nav-section-range">27–38</span>'),
        ('<span class="nav-section-range">40–50</span>', '<span class="nav-section-range">39–49</span>'),
    ):
        require(updated.count(old) == 1, f"Could not locate navigation range {old}.")
        updated = updated.replace(old, new, 1)

    for obsolete in (
        'id="slide-18"',
        'prior-experience-annual',
        'Annual voluntary attrition by prior experience',
    ):
        require(obsolete not in updated, f"Obsolete prior-experience content remains: {obsolete}")
    return updated


def remove_application_coverage_slide(deck: str) -> str:
    """Remove the standalone coverage slide after retaining its headline measure on slide 3.

    Technical stage IDs remain stable so the many later V7 transformations and
    validators continue to address their original content.  The template moves
    through slides by DOM order, therefore navigation indexes and visible
    labels—not later technical IDs—are renumbered.
    """
    stage_pattern = r'\s*<div class="slide-stage" id="slide-4".*?(?=\n\s*<div class="slide-stage" id="slide-5")'
    updated, replacements = re.subn(stage_pattern, '\n', deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate exactly one standalone application-coverage slide.")

    nav_pattern = r'\s*<button class="nav-pill" data-slide="3">4\. Applied to a job .*?</button>'
    updated, replacements = re.subn(nav_pattern, '', updated, count=1, flags=re.S)
    require(replacements == 1, "Could not remove the standalone application-coverage navigation item.")

    nav_button_pattern = (
        r'(?P<prefix><button class="nav-pill(?: [^"]*)?" data-slide=")'
        r'(?P<index>\d+)(?P<middle>">)(?P<label>\d+)'
        r'(?P<suffix>\. [^<]+</button>)'
    )

    def renumber_nav_button(match: re.Match[str]) -> str:
        index = int(match.group("index"))
        label = int(match.group("label"))
        require(label == index + 1, "Navigation labels must match 0-based indexes before slide 4 removal.")
        if index < 4:
            return match.group(0)
        return (
            f'{match.group("prefix")}{index - 1}{match.group("middle")}'
            f'{label - 1}{match.group("suffix")}'
        )

    updated, nav_buttons = re.subn(nav_button_pattern, renumber_nav_button, updated)
    require(nav_buttons == 48, "V7 must retain 48 navigation buttons after removing slide 4.")

    section_range_map = {
        (1, 2): (1, 2),
        (3, 5): (3, 4),
        (6, 18): (5, 17),
        (19, 26): (18, 25),
        (27, 38): (26, 37),
        (39, 49): (38, 48),
    }

    def update_section_range(match: re.Match[str]) -> str:
        current = (int(match.group("start")), int(match.group("end")))
        require(current in section_range_map, f"Unexpected navigation section range: {current}.")
        start, end = section_range_map[current]
        return f'{match.group("prefix")}{start}{match.group("separator")}{end}{match.group("suffix")}'

    range_pattern = (
        r'(?P<prefix><span class="nav-section-range">)(?P<start>\d+)'
        r'(?P<separator>[^0-9]+)(?P<end>\d+)(?P<suffix></span>)'
    )
    updated, ranges = re.subn(range_pattern, update_section_range, updated)
    require(ranges == 6, "Could not update all navigation section ranges after slide 4 removal.")

    agenda_range_map = {
        (3, 10): (3, 9),
        (11, 19): (10, 17),
        (20, 27): (18, 25),
        (28, 38): (26, 36),
        (39, 50): (37, 48),
    }

    def update_agenda_range(match: re.Match[str]) -> str:
        current = (int(match.group("start")), int(match.group("end")))
        require(current in agenda_range_map, f"Unexpected agenda range: {current}.")
        start, end = agenda_range_map[current]
        return f'{match.group("prefix")}{start}{match.group("separator")}{end}{match.group("suffix")}'

    agenda_pattern = (
        r'(?P<prefix><span class="agenda-num">Slides )(?P<start>\d+)'
        r'(?P<separator>[^0-9]+)(?P<end>\d+)(?P<suffix></span>)'
    )
    updated, agenda_ranges = re.subn(agenda_pattern, update_agenda_range, updated)
    require(agenda_ranges == 5, "Could not update all agenda ranges after slide 4 removal.")

    for obsolete in (
        'id="slide-4"',
        'data-v7-application-coverage="true"',
    ):
        require(obsolete not in updated, f"Standalone application-coverage content remains: {obsolete}")
    return updated


def remove_redundant_promotion_history_slide(deck: str) -> str:
    """Remove the superseded grade-level promotion matrix after pay-track refresh."""
    stage_pattern = r'\s*<div class="slide-stage" id="slide-33".*?(?=\n\s*<div class="slide-stage" id="slide-34")'
    updated, replacements = re.subn(stage_pattern, '\n', deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the redundant promotion-history stage.")

    nav_pattern = (
        r'\s*<button class="nav-pill" data-slide="28">'
        r'29\. Promotion history by current compensation grade</button>'
    )
    updated, replacements = re.subn(nav_pattern, '', updated, count=1)
    require(replacements == 1, "Could not remove the redundant promotion-history navigation item.")

    nav_button_pattern = (
        r'(?P<prefix><button class="nav-pill(?: [^"]*)?" data-slide=")'
        r'(?P<index>\d+)(?P<middle>">)(?P<label>\d+)'
        r'(?P<suffix>\. [^<]+</button>)'
    )

    def renumber_nav_button(match: re.Match[str]) -> str:
        index = int(match.group("index"))
        label = int(match.group("label"))
        require(label == index + 1, "Navigation labels must match indexes before promotion-history removal.")
        if index < 28:
            return match.group(0)
        return (
            f'{match.group("prefix")}{index - 1}{match.group("middle")}'
            f'{label - 1}{match.group("suffix")}'
        )

    updated, nav_buttons = re.subn(nav_button_pattern, renumber_nav_button, updated)
    require(nav_buttons == 47, "The deck must have 47 navigation buttons after promotion-history removal.")

    range_map = {
        (1, 2): (1, 2),
        (3, 4): (3, 4),
        (5, 17): (5, 17),
        (18, 25): (18, 25),
        (26, 37): (26, 36),
        (38, 48): (37, 47),
    }
    range_pattern = (
        r'(?P<prefix><span class="nav-section-range">)(?P<start>\d+)'
        r'(?P<separator>[^0-9]+)(?P<end>\d+)(?P<suffix></span>)'
    )

    def update_range(match: re.Match[str]) -> str:
        current = (int(match.group("start")), int(match.group("end")))
        require(current in range_map, f"Unexpected navigation range before promotion-history removal: {current}.")
        start, end = range_map[current]
        return f'{match.group("prefix")}{start}{match.group("separator")}{end}{match.group("suffix")}'

    updated, ranges = re.subn(range_pattern, update_range, updated)
    require(ranges == 6, "Could not update navigation ranges after promotion-history removal.")
    require(updated.count("Slides 37-48") == 1, "The manager agenda range is missing before promotion-history removal.")
    updated = updated.replace("Slides 37-48", "Slides 37-47", 1)

    require('id="slide-33"' not in updated, "The redundant promotion-history stage remains.")
    require("29. Promotion history by current compensation grade" not in updated, "The redundant promotion-history label remains.")
    return updated


def remove_redundant_colocation_slide(deck: str) -> str:
    """Remove the co-location visual because the following proxy is equivalent for this deck."""
    stage_pattern = r'\s*<div class="slide-stage" id="slide-41".*?(?=\n\s*<div class="slide-stage" id="slide-42")'
    updated, replacements = re.subn(stage_pattern, '\n', deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the redundant co-location stage.")

    nav_pattern = (
        r'\s*<button class="nav-pill" data-slide="35">'
        r'36\. Co-location with manager</button>'
    )
    updated, replacements = re.subn(nav_pattern, '', updated, count=1)
    require(replacements == 1, "Could not remove the redundant co-location navigation item.")

    nav_button_pattern = (
        r'(?P<prefix><button class="nav-pill(?: [^"]*)?" data-slide=")'
        r'(?P<index>\d+)(?P<middle>">)(?P<label>\d+)'
        r'(?P<suffix>\. [^<]+</button>)'
    )

    def renumber_nav_button(match: re.Match[str]) -> str:
        index = int(match.group("index"))
        label = int(match.group("label"))
        require(label == index + 1, "Navigation labels must match indexes before co-location removal.")
        if index < 35:
            return match.group(0)
        return (
            f'{match.group("prefix")}{index - 1}{match.group("middle")}'
            f'{label - 1}{match.group("suffix")}'
        )

    updated, nav_buttons = re.subn(nav_button_pattern, renumber_nav_button, updated)
    require(nav_buttons == 46, "V7 must retain 46 navigation buttons after co-location removal.")

    range_map = {
        (1, 2): (1, 2),
        (3, 4): (3, 4),
        (5, 17): (5, 17),
        (18, 25): (18, 25),
        (26, 36): (26, 35),
        (37, 47): (36, 46),
    }
    range_pattern = (
        r'(?P<prefix><span class="nav-section-range">)(?P<start>\d+)'
        r'(?P<separator>[^0-9]+)(?P<end>\d+)(?P<suffix></span>)'
    )

    def update_range(match: re.Match[str]) -> str:
        current = (int(match.group("start")), int(match.group("end")))
        require(current in range_map, f"Unexpected navigation range before co-location removal: {current}.")
        start, end = range_map[current]
        return f'{match.group("prefix")}{start}{match.group("separator")}{end}{match.group("suffix")}'

    updated, ranges = re.subn(range_pattern, update_range, updated)
    require(ranges == 6, "Could not update navigation ranges after co-location removal.")

    require(updated.count("Slides 37-47") == 1, "The manager agenda range is missing before co-location removal.")
    updated = updated.replace("Slides 37-47", "Slides 36-46", 1)
    require(updated.count("Slides 26-36") == 1, "The career agenda range is missing before co-location removal.")
    updated = updated.replace("Slides 26-36", "Slides 26-35", 1)

    require('id="slide-41"' not in updated, "The redundant co-location stage remains.")
    require("Co-location with manager" not in updated, "The redundant co-location label remains.")
    return updated


def remove_redundant_manager_support_tail_slides(deck: str) -> str:
    """Remove the final exploratory slides at requester direction."""
    stage_pattern = r'\s*<div class="slide-stage" id="slide-51".*?(?=\n\s*<div class="slide-stage" id="slide-52")'
    updated, replacements = re.subn(stage_pattern, '\n', deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the Major inflection points stage.")

    stage_pattern = r'\s*<div class="slide-stage" id="slide-52".*?(?=\n\s*<div class="nav-ctrl" id="slide-nav")'
    updated, replacements = re.subn(stage_pattern, '\n', updated, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the ET fields stage.")

    nav_pattern = (
        r'\s*<button class="nav-pill" data-slide="44">'
        r'45\. Major inflection points</button>\s*'
        r'<button class="nav-pill" data-slide="45">'
        r'46\. ET fields</button>'
    )
    updated, replacements = re.subn(nav_pattern, '', updated, count=1)
    require(replacements == 1, "Could not remove the final exploratory navigation items.")

    require(updated.count('<span class="nav-section-range">36–46</span>') == 1, "The final manager-support navigation range is missing.")
    updated = updated.replace('<span class="nav-section-range">36–46</span>', '<span class="nav-section-range">36–44</span>', 1)
    require(updated.count("Slides 36-46") == 1, "The final manager-support agenda range is missing.")
    updated = updated.replace("Slides 36-46", "Slides 36-44", 1)

    for obsolete in (
        'id="slide-51"',
        'id="slide-52"',
        "Major inflection points",
        "45. Major inflection points",
        "ET fields",
        "46. ET fields",
    ):
        require(obsolete not in updated, f"Removed tail-slide content remains: {obsolete}")
    return updated


def remove_qvoice_participation_coverage_slide(deck: str) -> str:
    """Remove the participation-coverage visual and keep navigation contiguous.

    Technical stage IDs deliberately remain stable for the retained slides:
    later transformations address those IDs, while the HTML navigator moves by
    DOM order and therefore needs only its displayed indexes and labels updated.
    """
    stage_pattern = r'\s*<div class="slide-stage" id="slide-22".*?(?=\n\s*<div class="slide-stage" id="slide-23")'
    updated, replacements = re.subn(stage_pattern, '\n', deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the QVoice participation-coverage stage.")

    nav_pattern = (
        r'\s*<button class="nav-pill" data-slide="19">'
        r'20\. QVoice participation coverage</button>'
    )
    updated, replacements = re.subn(nav_pattern, '', updated, count=1)
    require(replacements == 1, "Could not remove the QVoice participation-coverage navigation item.")

    nav_button_pattern = (
        r'(?P<prefix><button class="nav-pill(?: [^"]*)?" data-slide=")'
        r'(?P<index>\d+)(?P<middle>">)(?P<label>\d+)'
        r'(?P<suffix>\. [^<]+</button>)'
    )

    def renumber_nav_button(match: re.Match[str]) -> str:
        index = int(match.group("index"))
        label = int(match.group("label"))
        require(label == index + 1, "Navigation labels must match indexes before participation-slide removal.")
        if index < 20:
            return match.group(0)
        return (
            f'{match.group("prefix")}{index - 1}{match.group("middle")}'
            f'{label - 1}{match.group("suffix")}'
        )

    updated, nav_buttons = re.subn(nav_button_pattern, renumber_nav_button, updated)
    require(nav_buttons == 43, "V7 must retain 43 navigation buttons after participation-slide removal.")

    range_map = {
        (1, 2): (1, 2),
        (3, 4): (3, 4),
        (5, 17): (5, 17),
        (18, 25): (18, 24),
        (26, 35): (25, 34),
        (36, 44): (35, 43),
    }
    range_pattern = (
        r'(?P<prefix><span class="nav-section-range">)(?P<start>\d+)'
        r'(?P<separator>[^0-9]+)(?P<end>\d+)(?P<suffix></span>)'
    )

    def update_range(match: re.Match[str]) -> str:
        current = (int(match.group("start")), int(match.group("end")))
        require(current in range_map, f"Unexpected navigation range before participation-slide removal: {current}.")
        start, end = range_map[current]
        return f'{match.group("prefix")}{start}{match.group("separator")}{end}{match.group("suffix")}'

    updated, ranges = re.subn(range_pattern, update_range, updated)
    require(ranges == 6, "Could not update navigation ranges after participation-slide removal.")

    for old, new in (
        ("Slides 18-25", "Slides 18-24"),
        ("Slides 26-35", "Slides 25-34"),
        ("Slides 36-44", "Slides 35-43"),
    ):
        require(updated.count(old) == 1, f"Could not locate agenda range {old}.")
        updated = updated.replace(old, new, 1)

    for obsolete in (
        'id="slide-22"',
        'data-v7-qvoice-participation-layout=',
        "QVoice participation coverage",
    ):
        require(obsolete not in updated, f"Removed QVoice participation content remains: {obsolete}")
    return updated


def remove_team_attrition_slide(deck: str) -> str:
    """Remove the requester-retired team-attrition slide and close navigation.

    The technical stage IDs of the retained slides stay unchanged because the
    builder addresses them directly.  Browser navigation uses DOM order, so
    only the visible button indices, labels, section ranges, and agenda ranges
    are renumbered.
    """
    stage_pattern = r'\s*<div class="slide-stage" id="slide-8".*?(?=\n\s*<div class="slide-stage" id="slide-9")'
    updated, replacements = re.subn(stage_pattern, '\n', deck, count=1, flags=re.S)
    require(replacements == 1, "Could not locate the Team attrition stage requested for removal.")

    nav_pattern = r'\s*<button class="nav-pill" data-slide="6">7\. Team attrition</button>'
    updated, replacements = re.subn(nav_pattern, '', updated, count=1)
    require(replacements == 1, "Could not remove the Team attrition navigation item.")

    nav_button_pattern = (
        r'(?P<prefix><button class="nav-pill(?: [^"]*)?" data-slide=")'
        r'(?P<index>\d+)(?P<middle>">)(?P<label>\d+)'
        r'(?P<suffix>\. [^<]+</button>)'
    )

    def renumber_nav_button(match: re.Match[str]) -> str:
        index = int(match.group("index"))
        label = int(match.group("label"))
        require(label == index + 1, "Navigation labels must match indexes before Team attrition removal.")
        if index < 7:
            return match.group(0)
        return (
            f'{match.group("prefix")}{index - 1}{match.group("middle")}'
            f'{label - 1}{match.group("suffix")}'
        )

    updated, nav_buttons = re.subn(nav_button_pattern, renumber_nav_button, updated)
    require(nav_buttons == 44, "V7 must retain 44 navigation buttons after Team attrition removal.")

    range_map = {
        (1, 2): (1, 2),
        (3, 4): (3, 4),
        (5, 17): (5, 16),
        (18, 24): (17, 23),
        (25, 36): (24, 35),
        (37, 45): (36, 44),
    }
    range_pattern = (
        r'(?P<prefix><span class="nav-section-range">)(?P<start>\d+)'
        r'(?P<separator>[^0-9]+)(?P<end>\d+)(?P<suffix></span>)'
    )

    def update_range(match: re.Match[str]) -> str:
        current = (int(match.group("start")), int(match.group("end")))
        require(current in range_map, f"Unexpected navigation range before Team attrition removal: {current}.")
        start, end = range_map[current]
        return f'{match.group("prefix")}{start}{match.group("separator")}{end}{match.group("suffix")}'

    updated, ranges = re.subn(range_pattern, update_range, updated)
    require(ranges == 6, "Could not update all navigation ranges after Team attrition removal.")

    agenda_map = {
        (3, 9): (3, 8),
        (10, 17): (9, 16),
        (18, 24): (17, 23),
        (25, 36): (24, 35),
        (37, 45): (36, 44),
    }
    agenda_pattern = (
        r'(?P<prefix><span class="agenda-num">Slides )(?P<start>\d+)'
        r'(?P<separator>[^0-9]+)(?P<end>\d+)(?P<suffix></span>)'
    )

    def update_agenda_range(match: re.Match[str]) -> str:
        current = (int(match.group("start")), int(match.group("end")))
        require(current in agenda_map, f"Unexpected agenda range before Team attrition removal: {current}.")
        start, end = agenda_map[current]
        return f'{match.group("prefix")}{start}{match.group("separator")}{end}{match.group("suffix")}'

    updated, agenda_ranges = re.subn(agenda_pattern, update_agenda_range, updated)
    require(agenda_ranges == 5, "Could not update all agenda ranges after Team attrition removal.")

    for obsolete in (
        'id="slide-8"',
        '>Team attrition</h2>',
        '7. Team attrition</button>',
    ):
        require(obsolete not in updated, f"Removed Team attrition content remains: {obsolete}")
    return updated


def validate_output(
    deck: str,
    evidence: dict[str, Any],
    application_evidence: dict[str, Any],
    application_attrition_evidence: dict[str, Any],
    gender_label_evidence: dict[str, Any],
    work_arrangement_group_evidence: dict[str, float],
    job_family_august_snapshot_evidence: dict[str, Any],
    job_family_august_trailing_12m_attrition_evidence: dict[str, Any],
    rehire_comparison_august_trailing_12m_evidence: dict[str, Any],
    cto_org_display_evidence: dict[str, Any],
    cto_org_annual_attrition_evidence: dict[str, Any],
    qvoice_ytd_attrition_evidence: dict[str, Any],
    qvoice_ytd_group_attrition_evidence: dict[str, Any],
    qvoice_favorable_unfavorable_attrition_evidence: dict[str, Any],
    qvoice_open_text_request_concern_evidence: dict[str, Any],
    qvoice_heartbeat_attrition_evidence: dict[str, Any],
    qvoice_retention_theme_august_attrition_evidence: dict[str, Any],
    nav28_39_direct_annual_attrition_evidence: dict[str, Any],
    time_in_job_profile_time_in_role_evidence: dict[str, Any],
    nav28_39_promotion_annual_attrition_evidence: dict[str, Any],
    time_since_last_promotion_comparable_cohorts_evidence: dict[str, Any],
    within_team_annual_attrition_evidence: dict[str, Any],
    colocation_annual_attrition_evidence: dict[str, Any],
    manager_timezone_august_trailing_12m_evidence: dict[str, Any],
    nav38_plus_august_attrition_evidence: dict[str, Any],
    layers_from_ceo_annual_attrition_evidence: dict[str, Any],
    layers_from_ceo_0_2_compensation_grade_evidence: dict[str, Any],
    direct_team_span_annual_attrition_evidence: dict[str, Any],
) -> None:
    require(len(re.findall(r'<div class="slide-stage"', deck)) == 44, "V7 must retain 44 slides after removing Team attrition.")
    nav_ids = re.findall(r'<button class="nav-pill[^>]* data-slide="(\d+)"', deck)
    require(nav_ids == [str(index) for index in range(44)], "V7 navigation must retain one 0-based item per slide.")
    stage_ids = re.findall(r'<div class="slide-stage" id="([^"]+)"', deck)
    require(len(stage_ids) == len(set(stage_ids)) == 44, "Slide IDs must remain unique.")
    require(
        all(obsolete not in deck for obsolete in (
            'id="slide-18"',
            'id="slide-22"',
            'id="slide-33"',
            'id="slide-41"',
            'id="slide-8"',
            'prior-experience-annual',
            'Annual voluntary attrition by prior experience',
            '29. Promotion history by current compensation grade',
            'Co-location with manager',
            '>Team attrition</h2>',
            '7. Team attrition</button>',
            'id="slide-51"',
            'id="slide-52"',
            'Major inflection points',
            'ET fields',
            'QVoice participation coverage',
        )),
        "An obsolete removed slide or its chart container remains.",
    )
    nav_ranges = re.findall(r'<span class="nav-section-range">(\d+)[^0-9]+(\d+)</span>', deck)
    require(
        [(int(start), int(end)) for start, end in nav_ranges]
        == [(1, 2), (3, 4), (5, 16), (17, 23), (24, 35), (36, 44)],
        "V7 navigation ranges must reconcile after Team attrition is removed.",
    )
    require(
        re.findall(r'<span class="nav-section-range">([^<]+)</span>', deck)
        == ["1&ndash;2", "3&ndash;4", "5&ndash;16", "17&ndash;23", "24&ndash;35", "36&ndash;44"],
        "V7 navigation range separators must render as a valid en dash rather than mojibake.",
    )
    require(
        'data-slide="35">36. Assigned office-site proximity to manager</button>' in deck,
        "V7 navigation must relabel the retained manager-proximity slide after Team attrition removal.",
    )
    require(
        'data-slide="30">31. 0&ndash;2 layers: exact compensation grades</button>' in deck,
        "V7 navigation must label the exact-grade manager-layers follow-up.",
    )
    require(
        'data-slide="31">32. Direct team size (span)</button>' in deck,
        "V7 navigation must label the direct-team-span follow-up.",
    )
    intro_html = stage_fragment(deck, 1)
    intro_metrics = layers_from_ceo_annual_attrition_evidence["metrics"]
    intro_population = int(intro_metrics["display_eligible_count"])
    intro_exits = int(intro_metrics["baseline_voluntary_exits"])
    intro_rate = 100 * intro_exits / intro_population
    require('data-v7-intro-population-context="true"' in intro_html, "V7 cover population-context marker is missing.")
    require('Employee characteristics and attrition' in intro_html, "V7 cover title is missing its plain-language update.")
    require('How characteristics are distributed and how voluntary attrition differs across them' in intro_html, "V7 cover subtitle is missing.")
    require('Employees with Regular status who were active at the date used for each slide.' in intro_html, "V7 cover workforce definition is missing.")
    require('The percentage who chose to leave the company. Other types of departure are not included.' in intro_html, "V7 cover voluntary-attrition definition is missing.")
    require(
        f'{intro_rate:.1f}% &middot; {intro_exits:,} employees chose to leave in the 12 months ending 23 Aug 2026.' in intro_html,
        "V7 cover annual voluntary-attrition context is missing.",
    )
    require(f'We start with {intro_population:,} Regular employees active on 24 Aug 2025 and follow them to 23 Aug 2026.' in intro_html, "V7 cover annual-rate method is missing.")
    require('Each slide shows how employees are distributed across categories and, where available, the voluntary attrition rate for each category.' in intro_html, "V7 cover distribution-and-attrition purpose is missing.")
    require('Most distributions show employees active in August 2026.' in intro_html and 'Each slide states its own time period.' in intro_html, "V7 cover 2026 distribution context is missing.")
    for obsolete_intro_text in ('reviewed V5 evidence', 'What each variable means', 'model-planning discussion', 'next 12 months'):
        require(obsolete_intro_text not in intro_html, f"V7 cover retains obsolete technical wording: {obsolete_intro_text}")
    require('data-slide="0">1. Employee characteristics and attrition</button>' in deck, "V7 cover navigation title is missing.")
    followup_stage = re.search(
        r'<div class="slide-stage" id="slide-37-followup".*?(?=\n\s*<div class="slide-stage" id="slide-38")',
        deck,
        flags=re.S,
    )
    require(followup_stage is not None, "V7 0–2 manager-layers compensation-grade follow-up is missing.")
    followup_html = followup_stage.group(0)
    require('data-v7-layers-grade-followup="true"' in followup_html, "V7 follow-up marker is missing.")
    require('0&ndash;2 manager layers: exact compensation-grade distribution' in followup_html, "V7 exact-grade follow-up title is missing.")
    require('strict voluntary exits through 23 Aug 2026' in followup_html, "V7 follow-up must disclose its outcome cutoff.")
    require('grade causes attrition' in followup_html, "V7 follow-up must preserve its non-causal caveat.")
    require('Internal exploratory analysis' in followup_html, "V7 exact-grade follow-up must be marked as internal analysis.")
    require('No employee, manager, or exact compensation/pay values are shown.' in followup_html, "V7 follow-up must disclose its privacy boundary.")
    require('V grade family' not in followup_html and 'All other grade families' not in followup_html, "V7 exact-grade follow-up still contains grouped grade families.")
    followup_rows = {str(row["label"]): row for row in layers_from_ceo_0_2_compensation_grade_evidence["rows"]}
    require(followup_html.count('class="layers-grade-followup-cell ') == len(followup_rows), "V7 follow-up must render every exact compensation grade.")
    require('class="layers-grade-followup-chart"' in followup_html and 'class="layers-grade-followup-keyline"' in followup_html, "V7 exact-grade follow-up must use the horizontal distribution-bar layout.")
    require('layers-grade-followup-grid' not in followup_html, "V7 exact-grade follow-up must not retain the obsolete grade-card grid.")
    require(followup_html.count('layers-grade-followup-track') == len(followup_rows), "V7 exact-grade follow-up must render one distribution track per grade.")
    require(followup_html.count('layers-grade-followup-attrition v6-rate-pill') == len(followup_rows), "V7 exact-grade follow-up must render one annual-attrition label per grade.")
    subthreshold_rows = 0
    followup_rates = [float(row["annual_attrition_rate_percent"]) for row in followup_rows.values()]
    for label, row in followup_rows.items():
        count = int(row["employee_count"])
        if count < 30:
            subthreshold_rows += 1
        require(f'data-grade="{label}"' in followup_html, f"V7 follow-up is missing exact grade {label}.")
        require(
            f"n={count:,} &middot; {float(row['cohort_share_percent']):.1f}%" in followup_html,
            f"V7 follow-up is missing the exact-grade distribution for {label}.",
        )
        require(
            f'layers-grade-followup-attrition v6-rate-pill {attrition_pill_class(float(row["annual_attrition_rate_percent"]), followup_rates)}'
            in followup_html and f">{float(row['annual_attrition_rate_percent']):.1f}%</span>" in followup_html,
            f"V7 follow-up is missing the annual attrition label for {label}.",
        )
        require(
            f"{int(row['voluntary_exits']):,} exits" in followup_html,
            f"V7 follow-up is missing the exit count for {label}.",
        )
    require(followup_html.count('class="layers-grade-followup-exploratory"') == subthreshold_rows, "V7 follow-up must visibly mark every small exact-grade cohort as exploratory.")
    for prohibited in ('annual_base_pay', 'base_pay_rate', 'employee_id', 'manager_employee_id', 'root_employee_id'):
        require(prohibited not in followup_html.lower(), f"V7 exact-grade follow-up exposes restricted field: {prohibited}.")
    span_stage = re.search(
        r'<div class="slide-stage" id="slide-37-span-followup".*?(?=\n\s*<div class="slide-stage" id="slide-38")',
        deck,
        flags=re.S,
    )
    require(span_stage is not None, "V7 direct-team-span follow-up is missing.")
    span_html = span_stage.group(0)
    require('data-v7-direct-team-span-followup="true"' in span_html, "V7 direct-team-span marker is missing.")
    require('Direct team size (span): distribution and annual attrition' in span_html, "V7 direct-team-span title is missing.")
    require('Internal exploratory analysis' in span_html, "V7 direct-team-span slide must be marked as internal analysis.")
    require('strict voluntary exits through 23 Aug 2026' in span_html, "V7 direct-team-span slide must disclose its outcome cutoff.")
    require('team size causes attrition' in span_html, "V7 direct-team-span slide must preserve its non-causal caveat.")
    require(len(re.findall(r'<section class="direct-team-span-band(?:\s|\")', span_html)) == 6, "V7 direct-team-span slide must render exactly six bands.")
    require('class="direct-team-span-chart"' in span_html and 'class="direct-team-span-keyline"' in span_html, "V7 direct-team-span slide must use the horizontal distribution-bar layout.")
    require('direct-team-span-grid' not in span_html, "V7 direct-team-span slide must not retain the obsolete six-card grid.")
    require(span_html.count('direct-team-span-track') == 6, "V7 direct-team-span slide must render one distribution track per band.")
    require(span_html.count('direct-team-span-attrition v6-rate-pill') == 6, "V7 direct-team-span slide must render one annual-attrition label per band.")
    require('44,737 of 45,003' in span_html and '266 employees have no resolvable active regular manager' in span_html, "V7 direct-team-span coverage disclosure is incomplete.")
    span_bands = direct_team_span_annual_attrition_evidence["bands"]
    span_rates = [float(row["annual_attrition_rate_percent"]) for row in span_bands]
    for row in span_bands:
        label = str(row["label"])
        require(f'data-span-band="{label}"' in span_html, f"V7 direct-team-span slide is missing band {label}.")
        require(
            f"n={int(row['employee_count']):,} &middot; {float(row['employee_share_percent']):.1f}%" in span_html
            and f"{int(row['team_count']):,} teams &middot; {int(row['voluntary_exits']):,} exits" in span_html,
            f"V7 direct-team-span slide is missing the distribution for {label}.",
        )
        require(
            f'direct-team-span-attrition v6-rate-pill {attrition_pill_class(float(row["annual_attrition_rate_percent"]), span_rates)}'
            in span_html and f">{float(row['annual_attrition_rate_percent']):.1f}%</span>" in span_html,
            f"V7 direct-team-span slide is missing attrition metrics for {label}.",
        )
    five = direct_team_span_annual_attrition_evidence["exact_span_comparison"]["five_direct_reports"]
    twenty = direct_team_span_annual_attrition_evidence["exact_span_comparison"]["twenty_direct_reports"]
    require('data-exact-span="5"' in span_html and 'n=7,160 &middot; 1,432 teams' in span_html, "V7 direct-team-span slide is missing the exact size 5 callout.")
    require('data-exact-span="20"' in span_html and 'n=80 &middot; 4 teams' in span_html, "V7 direct-team-span slide is missing the exact size 20 callout.")
    require(f"{float(five['annual_attrition_rate_percent']):.1f}%" in span_html and f"{float(twenty['annual_attrition_rate_percent']):.1f}%" in span_html, "V7 direct-team-span exact-rate callouts are missing.")
    require('exploratory (4 teams)' in span_html, "V7 direct-team-span exact size 20 must be visibly exploratory.")
    for prohibited in ('employee_id', 'manager_employee_id', 'manager_name', 'employee_name', 'email'):
        require(prohibited not in span_html.lower(), f"V7 direct-team-span follow-up exposes restricted field: {prohibited}.")
    require(all(f'data-theme="{theme}"' in deck for theme in (
        "theme-light-classic", "theme-light-soft", "theme-dark-royal", "theme-dark-carbon"
    )), "The four canonical themes are required.")
    require('class="ios-ytd-horizontal-grid"' in deck, "V7 horizontal IOS movement layout is missing.")
    require(deck.count('<article class="card chart-card ios-ytd-year-panel">') == 1, "V7 must contain exactly one 2026 horizontal panel.")
    require('id="transfer-monthly-chart"' not in deck and 'id="transfer-weekly-chart"' not in deck, "Obsolete transfer chart containers remain.")
    require('var transferRows' not in deck, "Obsolete transfer chart data remains in V7.")
    require('Transfer within the past year' not in deck, "V7 still exposes the old rolling-transfer slide language.")
    current_total = next(row for row in evidence["rows"] if row["calendar_year"] == 2026 and row["group_key"] == "total")
    require(
        f'IOS movements represent {float(current_total["workforce_share_percent"]):.1f}% of the active regular workforce in 2026 YTD' in deck,
        "V7 2026 headline is missing.",
    )
    require(deck.count('ios-ytd-bar-row') == 7, "The six 2026 IOS reason bars were not rendered.")
    for row in evidence["rows"]:
        if row["group_key"] != "total":
            require(row["short_label"] in deck, f"Missing IOS reason label: {row['short_label']}")
    require("All IOS movements" not in stage_fragment(deck, 5), "The redundant IOS total bar remains.")
    require('<!-- V7 IOS MOVEMENT REASON SCRIPT -->' not in deck, "The previous V7 Plotly script should not remain after the horizontal-bar redesign.")
    require('showSlide(0)' in deck and 'slide-studio-theme' in deck, "Template navigation/theme behavior is missing.")
    require('data-deliverable-mode="internal_analysis"' in deck, "V7 must be marked as internal_analysis.")
    require(
        not re.search(r'class="[^"]*\bv6-hidden-row\b', deck)
        and not re.search(r'<div class="v6-truncation-note"', deck),
        "Internal V7 still hides aggregate rows.",
    )
    require('Not shown (n &lt; 30)' not in deck and 'suppressed_below_n30' not in deck, "Internal V7 still suppresses a sub-30 aggregate bucket.")
    require('Internal analysis' in deck, "V7 internal-analysis label is missing.")
    require(application_evidence["latest_snapshot"] in deck, "V7 latest application snapshot is missing.")
    require('two_plus_percent":null' not in deck and 'two_plus_percent": null' not in deck, "V7 still contains a null application percentage.")
    require('data-v7-application-attrition="true"' in deck, "V7 slide 3 attrition enhancement is missing.")
    require(application_attrition_evidence["validation"]["outcome"] == "pass", "Application attrition evidence validation is missing.")
    application_stage = stage_fragment(deck, 3)
    validate_application_trailing_august_slide_3_content(application_stage, application_attrition_evidence)
    gender_stage = re.search(r'<div class="slide-stage" id="slide-13".*?(?=\n\s*<div class="slide-stage" id="slide-14")', deck, flags=re.S)
    require(gender_stage is not None, "V7 Gender slide is missing.")
    gender_html = gender_stage.group(0)
    for placeholder, label in gender_label_evidence["display_mapping"].items():
        require(f'title="{label}">{label}</div>' in gender_html, f"V7 Gender slide is missing stored label {label}.")
        require(placeholder not in gender_html, f"V7 Gender slide still exposes placeholder {placeholder}.")
    require("Stored gender values are visible for aggregate internal fairness review" in gender_html, "V7 Gender slide must identify its internal label disclosure.")
    require("Stored anonymized codes" not in gender_html and "anonymized" not in gender_html.lower(), "V7 Gender slide still describes its labels as anonymized.")
    work_arrangement_stage = re.search(r'<div class="slide-stage" id="slide-14".*?(?=\n\s*<div class="slide-stage" id="slide-15")', deck, flags=re.S)
    require(work_arrangement_stage is not None, "V7 Work arrangement slide is missing.")
    work_arrangement_html = work_arrangement_stage.group(0)
    require(work_arrangement_html.count('work-arrangement-three-group-card') == 1, "V7 slide 14 must contain one three-group chart.")
    require('work-arrangement-stack' not in work_arrangement_html and 'work-arrangement-binary-card' not in work_arrangement_html, "V7 slide 14 still contains a second work-arrangement chart.")
    require(work_arrangement_html.count('v4-inline-attrition-rate') == 3, "V7 slide 14 must expose attrition for all three groups.")
    for label in ("Onsite", "Short-Term Remote Work", "Other offsite arrangements"):
        require(f'>{label}</div>' in work_arrangement_html, f"V7 slide 14 is missing the {label!r} group.")
    for rate in (
        work_arrangement_group_evidence["onsite_rate"],
        work_arrangement_group_evidence["short_term_remote_rate"],
        work_arrangement_group_evidence["other_offsite_rate"],
    ):
        require(f'>{rate:.1f}%</span>' in work_arrangement_html, f"V7 slide 14 is missing a validated attrition rate of {rate:.1f}%.")
    require('Other offsite arrangements combine every remaining stored non-onsite value' in work_arrangement_html, "V7 slide 14 must disclose the residual grouping.")
    cto_stage = re.search(r'<div class="slide-stage" id="slide-15".*?(?=\n\s*<div class="slide-stage" id="slide-16")', deck, flags=re.S)
    require(cto_stage is not None, "V7 CTO organizational split slide is missing.")
    cto_html = cto_stage.group(0)
    require('data-v7-cto-org-annual-attrition="true"' in cto_html, "V7 slide 15 annual CTO attrition treatment is missing.")
    require('Distribution / annual attrition' in cto_html, "V7 slide 15 must identify its annual attrition panel.")
    require('Current distribution:' in cto_html and 'Annual voluntary attrition (12 months):' in cto_html, "V7 slide 15 must disclose the two time windows.")
    require('Upper panel excludes RF360; lower organizational split uses all active regular employees' in cto_html, "V7 slide 15 must disclose the lower-panel population.")
    require(
        'Upper panel: six-month voluntary attrition after its snapshot. Lower panel: annual voluntary attrition' in cto_html,
        "V7 slide 15 source line must distinguish the two attrition windows.",
    )
    current_by_category = {str(row["category"]): row for row in cto_org_display_evidence["category_distribution"]}
    annual_by_category = {str(row["category"]): row for row in cto_org_annual_attrition_evidence["rows"]}
    annual_rates = [float(row["annual_attrition_rate_percent"]) for row in annual_by_category.values()]
    for category in ("CTO", "Corp Fxn & BU"):
        current = current_by_category[category]
        annual = annual_by_category[category]
        require(f'{int(current["employee_count"]):,}' in cto_html, f"V7 slide 15 is missing the current {category} distribution count.")
        rendered_rate = f'{float(annual["annual_attrition_rate_percent"]):.1f}%'
        require(f'>{rendered_rate}</span>' in cto_html, f"V7 slide 15 is missing the {category} annual attrition rate.")
        expected_class = attrition_pill_class(float(annual["annual_attrition_rate_percent"]), annual_rates)
        require(
            f'v4-inline-attrition-rate v6-rate-pill {expected_class}' in cto_html,
            f"V7 slide 15 {category} rate lacks the expected {expected_class} color class.",
        )
        require(
            f"n={int(annual['eligible_employee_count']):,} / {int(annual['voluntary_exits']):,} exits" in cto_html,
            f"V7 slide 15 is missing the {category} annual cohort detail.",
        )
    job_family_stage = stage_fragment(deck, 11)
    job_snapshot = job_family_august_snapshot_evidence["snapshot"]
    job_attrition_rows = job_family_august_trailing_12m_attrition_evidence["rows"]
    require('data-v7-job-family-august-snapshot="true"' in job_family_stage, "V7 Job family August replacement is missing.")
    require('data-v7-job-family-august-trailing-12m="true"' in job_family_stage, "V7 Job family trailing-12-month attrition treatment is missing.")
    require("2026-09" not in job_family_stage and "Snapshot 2026-09" not in job_family_stage, "V7 Job family still references the September reorganization snapshot.")
    require(job_family_stage.count("job-family-august-bar-row") == 21, "V7 Job family must show Top 20 plus Other.")
    require(job_family_stage.count("job-family-august-attrition v4-inline-attrition-rate v6-rate-pill") == 21, "V7 Job family must show one attrition pill per display category.")
    require("Distribution / trailing 12m attrition" in job_family_stage, "V7 Job family must identify the attrition measure.")
    require("strict VOLUNTARY exits" in job_family_stage, "V7 Job family source note must identify strict voluntary exits.")
    require(f"{int(job_snapshot['observable_employee_count']):,} active regular employees" in job_family_stage, "V7 Job family is missing the August denominator.")
    for row in job_family_august_snapshot_evidence["top_20"]:
        require(str(row["label"]) in job_family_stage and f"{int(row['employee_count']):,}" in job_family_stage, "V7 Job family misses an August category.")
    require(f"{int(job_snapshot['other_job_families_employee_count']):,}" in job_family_stage, "V7 Job family is missing August Other.")
    require(
        [str(row["category_label"]) for row in job_attrition_rows]
        == [str(row["label"]) for row in job_family_august_snapshot_evidence["top_20"]] + ["Other job families"],
        "V7 Job family attrition rows do not match the current display categories.",
    )
    attrition_rates = [float(row["trailing_12m_voluntary_attrition_rate_percent"]) for row in job_attrition_rows]
    for row in job_attrition_rows:
        rate = float(row["trailing_12m_voluntary_attrition_rate_percent"])
        expected_class = attrition_pill_class(rate, attrition_rates)
        require(
            f"job-family-august-attrition v4-inline-attrition-rate v6-rate-pill {expected_class}" in job_family_stage
            and f">{rate:.1f}%</span>" in job_family_stage,
            f"V7 Job family {row['category_label']} is missing the expected attrition pill.",
        )

    rehire_stage = re.search(r'<div class="slide-stage" id="slide-16".*?(?=\n\s*<div class="slide-stage" id="slide-17")', deck, flags=re.S)
    require(rehire_stage is not None, "V7 Rehire slide is missing.")
    rehire_html = rehire_stage.group(0)
    require('data-v7-rehire-comparison-august-trailing-12m="true"' in rehire_html, "V7 Rehire historical comparison treatment is missing.")
    require('rehire-history-grid' in rehire_html, "V7 Rehire slide must use the historical comparison grid.")
    require(rehire_html.count('rehire-year-card') == 3, "V7 Rehire slide must show exactly three historical year panels.")
    require(rehire_html.count('rehire-comparison-row') == 6, "V7 Rehire slide must show two baseline groups per year.")
    require('FY2024 cohort' in rehire_html and 'FY2025 cohort' in rehire_html and 'FY2026 cohort' in rehire_html, "V7 Rehire slide must identify FY2024-FY2026.")
    require('following 12-month cohort' in rehire_html, "V7 Rehire subtitle does not identify the historical 12-month cohorts.")
    require('Strict VOLUNTARY exits are measured in the following 12 months for each baseline.' in rehire_html, "V7 Rehire source note must state the historical 12-month outcome rule.")
    displayed_rehire_rows = list(rehire_comparison_august_trailing_12m_evidence["rows"])
    for index in range(0, len(displayed_rehire_rows), 2):
        year_rows = displayed_rehire_rows[index : index + 2]
        year_rates = [float(row["trailing_12m_voluntary_attrition_rate_percent"]) for row in year_rows]
        for row in year_rows:
            rate = float(row["trailing_12m_voluntary_attrition_rate_percent"])
            expected_pill_class = annual_rate_class(rate, year_rates)
            require(f'>{rate:.1f}%</span>' in rehire_html, f"V7 Rehire slide is missing the {row['rehire_group']} annual rate.")
            require(
                f'rehire-comparison-attrition {expected_pill_class}' in rehire_html,
            f"V7 Rehire {row['rehire_group']} lacks its expected {expected_pill_class} attrition pill.",
        )
    require('id="slide-8"' not in deck, "V7 Team attrition stage must be absent.")
    require('>Team attrition</h2>' not in deck, "V7 Team attrition title must be absent.")
    require('7. Team attrition</button>' not in deck, "V7 Team attrition navigation item must be absent.")
    for slide_number in (9, 10):
        stage = re.search(
            rf'<div class="slide-stage" id="slide-{slide_number}".*?(?=\n\s*<div class="slide-stage" id="slide-{slide_number + 1}")',
            deck,
            flags=re.S,
        )
        require(stage is not None, f"V7 slide {slide_number} is missing.")
        stage_html = stage.group(0)
        require("mode: 'lines+markers+text'" in stage_html, f"V7 slide {slide_number} is missing visible attrition labels.")
        require("row.follow_month === 0 ? '' : row.cumulative_incidence_percent.toFixed(1) + '%'" in stage_html, f"V7 slide {slide_number} is missing its attrition label formatter.")
        require("'top center'" in stage_html and "'bottom center'" in stage_html, f"V7 slide {slide_number} is missing separated label positions.")
    require('V7 multi-chart layouts — Julia-style dividers in the inter-panel gaps.' in deck, "V7 multi-chart divider styles are missing.")
    require('.manager-change-comparison-grid::before' in deck, "V7 manager-comparison divider is missing.")
    require('#slide-12 .v6-chart-area .two-chart::after' in deck, "V7 Region second divider is missing.")
    content_styles_marker = deck.find("/* 13. CONTENT-SPECIFIC STYLES")
    content_styles_close = deck.find("*/", content_styles_marker)
    v7_styles_start = deck.find("/* V7 internal_analysis")
    require(
        content_styles_marker >= 0 and content_styles_close >= 0 and v7_styles_start > content_styles_close,
        "V7 custom CSS must be inserted after, not inside, the template's content-style comment.",
    )
    # Slide 3 deliberately shows only the two latest August trailing windows.
    # Earlier August cutoffs remain traceable in aggregate evidence, not in the
    # current-period visual; this is observed trailing attrition, not follow-up.
    validate_application_trailing_august_slide_3_content(stage_fragment(deck, 3), application_attrition_evidence)

    qvoice_stage = stage_fragment(deck, 20)
    require(
        'data-qvoice-open-text-request-concern="20260922"' in qvoice_stage,
        "V7 QVoice slide 20 is missing its permanent request/concern marker.",
    )
    require(
        'data-v7-qvoice-open-text-three-group-composition="true"' in qvoice_stage
        and qvoice_stage.count('class="qvoice18-composition-bar"') == 4,
        "V7 QVoice slide 20 must show four three-group composition bars.",
    )
    require(
        len(re.findall(r'<div class="qvoice18-rate-card ', qvoice_stage)) == 12,
        "V7 QVoice slide 20 must show three composition and attrition cards per wave.",
    )
    require(
        'data-v7-qvoice-open-text-attrition-pills="true"' in qvoice_stage
        and 'data-v7-qvoice-open-text-no-comment-attrition="true"' in qvoice_stage
        and qvoice_stage.count('qvoice18-attrition-pill v6-rate-pill') == 12,
        "V7 QVoice slide 18 must show twelve color-coded attrition pills.",
    )
    require(
        len(re.findall(r'<div class="qvoice18-topic-row">', qvoice_stage))
        == len(qvoice_open_text_request_concern_evidence["latest_survey_subthemes"]),
        "V7 QVoice slide 20 must show every publishable latest-wave subtheme.",
    )
    require("Participation mix and subsequent attrition" in qvoice_stage, "The QVoice composition heading is missing.")
    require("all QVoice participants with a usable key" in qvoice_stage, "The QVoice composition denominator is missing.")
    require("qvoice18-rail-card" not in qvoice_stage, "The obsolete QVoice coverage rails remain in slide 20.")
    require("qvoice-comment-chart" not in qvoice_stage, "The obsolete QVoice topic chart remains in slide 20.")
    display_waves = {
        "Mar-2023": "Mar 2023",
        "Jan-2024": "Jan 2024",
        "Jan-2025": "Jan 2025",
        "Jan-2026": "2025 QVoice (fielded Jan 2026)",
    }
    for wave in qvoice_open_text_request_concern_evidence["waves"]:
        require(display_waves[str(wave["wave"])] in qvoice_stage, f"QVoice wave {wave['wave']} is missing.")
        require(f"QVoice participants n={int(wave['survey_participant_count']):,}" in qvoice_stage, f"QVoice wave {wave['wave']} is missing its composition denominator.")
        composition_by_group = {str(group["group"]): group for group in wave["composition"]["groups"]}
        attrition_by_group = {str(group["group"]): group for group in wave["groups"]}
        attrition_by_group["no_open_text_comment"] = wave["no_comment"]
        display_shares = displayed_qvoice_composition_shares(wave)
        require(abs(sum(display_shares.values()) - 100.0) < 0.0001, f"QVoice wave {wave['wave']} display shares do not sum to 100.0%.")
        for group_name in (
            "requested_remote_hybrid_or_raised_onsite_policy_concern",
            "all_other_open_text_commenters",
            "no_open_text_comment",
        ):
            composition = composition_by_group[group_name]
            require(
                f"{display_shares[group_name]:.1f}%" in qvoice_stage,
                f"QVoice wave {wave['wave']} is missing a published three-group composition share.",
            )
            require(
                f"n={int(composition['participant_count']):,}" in qvoice_stage,
                f"QVoice wave {wave['wave']} is missing a published cohort count.",
            )
            rate = float(attrition_by_group[group_name]["voluntary_attrition_rate_percent"])
            expected_class = attrition_pill_class(
                rate,
                [
                    float(item["voluntary_attrition_rate_percent"])
                    for item_wave in qvoice_open_text_request_concern_evidence["waves"]
                    for item in item_wave["groups"]
                ]
                + [
                    float(item_wave["no_comment"]["voluntary_attrition_rate_percent"])
                    for item_wave in qvoice_open_text_request_concern_evidence["waves"]
                ],
            )
            require(f">{rate:.1f}%</span>" in qvoice_stage, f"QVoice wave {wave['wave']} is missing a group attrition rate.")
            require(
                f"qvoice18-attrition-pill v6-rate-pill {expected_class}" in qvoice_stage,
                f"QVoice wave {wave['wave']} three-group attrition pill lacks its expected {expected_class} color.",
            )
    heartbeat_stage = stage_fragment(deck, 26)
    heartbeat_panels = qvoice_heartbeat_attrition_evidence["slide"]["panels"]
    heartbeat_questions = [question for panel in heartbeat_panels for question in panel["questions"]]
    heartbeat_segments = [segment for question in heartbeat_questions for segment in question["segments"]]
    heartbeat_segment_rates = [float(segment["ytd_voluntary_attrition_rate_percent"]) for segment in heartbeat_segments]
    require('data-v7-qvoice-heartbeat-attrition="post-survey-ytd-through-august"' in heartbeat_stage, "V7 QVoice slide 26 is missing its post-survey YTD marker.")
    require('data-v7-qvoice-heartbeat-relative-signs="true"' in heartbeat_stage, "V7 QVoice slide 24 is missing the relative-sign marker.")
    require(heartbeat_stage.count('<article class="qvoice-heartbeat-question">') == 6, "V7 QVoice slide 24 must show six compact question cards.")
    require(heartbeat_stage.count('<div class="qvoice-heartbeat-sign-row"') == 18, "V7 QVoice slide 24 must show eighteen relative-sign bars.")
    require(heartbeat_stage.count("qvoice-heartbeat-attrition v6-rate-pill") == 18, "V7 QVoice slide 24 must show one YTD attrition pill per sign bar.")
    require("Post-survey attrition YTD" in heartbeat_stage and "not annualized" in heartbeat_stage, "V7 QVoice slide 26 must identify the non-annualized post-survey window.")
    require("favorable" not in heartbeat_stage.lower(), "V7 QVoice slide 26 must not show absolute favorable context.")
    require("qvoice-ytd-attrition-card" not in heartbeat_stage and "Attrition not estimable" not in heartbeat_stage, "V7 QVoice slide 26 retains obsolete heartbeat attrition content.")
    require("100.0% of valid responses" in heartbeat_stage, "V7 QVoice slide 26 must state the within-question 100% denominator.")
    for question in heartbeat_questions:
        question_id = str(question["question_id"])
        require(question_id in heartbeat_stage, f"V7 QVoice slide 24 is missing {question_id}.")
        for segment in question["segments"]:
            share = float(segment["share_of_valid_responses_percent"])
            rate = float(segment["ytd_voluntary_attrition_rate_percent"])
            matched = int(segment["matched_employee_count"])
            exits = int(segment["voluntary_exit_count"])
            expected_class = attrition_pill_class(rate, heartbeat_segment_rates)
            require(f">{share:.1f}%</strong>" in heartbeat_stage, f"V7 QVoice slide 24 is missing a heartbeat sign share.")
            require(f">{rate:.1f}%</span>" in heartbeat_stage, f"V7 QVoice slide 24 is missing a heartbeat YTD attrition rate.")
            require(
                f'qvoice-heartbeat-attrition v6-rate-pill {expected_class}' in heartbeat_stage,
                f"V7 QVoice slide 24 a YTD rate lacks its expected {expected_class} color.",
            )
            require(f"n={matched:,}; exits={exits:,}" in heartbeat_stage, "V7 QVoice slide 24 is missing hidden cohort detail for a sign bar.")
    def validate_inline_qvoice_panel(
        slide_number: int,
        groups: list[tuple[str, dict[str, Any]]],
        require_panel: bool = True,
        require_detail: bool = True,
    ) -> None:
        stage_html = stage_fragment(deck, slide_number)
        require(
            'data-v7-qvoice-inline-attrition="true"' in stage_html,
            f"V7 QVoice slide {slide_number} is missing its inline YTD attrition marker.",
        )
        if require_panel:
            require(stage_html.count('qvoice-inline-attrition-panel') == 1, f"V7 QVoice slide {slide_number} must show one inline attrition panel.")
        require(stage_html.count('qvoice-inline-attrition-pill') == len(groups), f"V7 QVoice slide {slide_number} must show one pill per group.")
        require("2026 YTD" in stage_html and "not annualized" in stage_html, f"V7 QVoice slide {slide_number} must disclose its YTD window.")
        rates = [float(metric["ytd_voluntary_attrition_rate_percent"]) for _, metric in groups]
        for label, metric in groups:
            rate = float(metric["ytd_voluntary_attrition_rate_percent"])
            expected_class = "attr-mid" if len(rates) == 1 else attrition_pill_class(rate, rates)
            require(html.escape(label) in stage_html, f"V7 QVoice slide {slide_number} is missing the {label!r} group label.")
            require(f">{rate:.1f}%</span>" in stage_html, f"V7 QVoice slide {slide_number} is missing the {label!r} rate.")
            require(
                f'qvoice-inline-attrition-pill v6-rate-pill {expected_class}' in stage_html,
                f"V7 QVoice slide {slide_number} {label!r} rate lacks its expected {expected_class} color.",
            )
            if require_detail:
                require(
                    f"n={int(metric['matched_employee_count']):,} / {int(metric['voluntary_exit_count']):,} exits" in stage_html,
                    f"V7 QVoice slide {slide_number} is missing its cohort/exits detail for {label!r}.",
                )
        require("No publishable time-aligned attrition estimate is available." not in stage_html, f"V7 QVoice slide {slide_number} still says attrition is unavailable.")

    ytd_slides = qvoice_ytd_group_attrition_evidence["slides"]
    retention_groups = [
        (label, ytd_slides["21"][label])
        for label in qvoice_ytd_group_attrition_evidence["validation"]["retention_display_order"]
    ]
    validate_inline_qvoice_panel(25, ordered_score_bands(ytd_slides["25"]))
    validate_inline_qvoice_panel(27, ordered_z_score_bands(ytd_slides["27"]))
    comparable_score_stage = stage_fragment(deck, 25)
    for label in ("<50% favorable", "50–69% favorable", "70–79% favorable", "80–89% favorable", "90–99% favorable", "100% favorable"):
        require(label in html.unescape(comparable_score_stage), f"V7 QVoice slide 23 is missing the clarified {label!r} score-band label.")
    require("Individual score = 100 * favorable items / 33." in comparable_score_stage, "V7 QVoice slide 23 is missing the individual-score definition.")

    retention_theme_stage = stage_fragment(deck, 21)
    require(
        'data-v7-qvoice-retention-theme-attrition="august-trailing-12m"' in retention_theme_stage,
        "V7 navigation slide 19 is missing the permanent QVoice theme layout marker.",
    )
    require(
        retention_theme_stage.count('class="qv19-row"') == len(qvoice_retention_theme_august_attrition_evidence["rows"]) == 5,
        "V7 navigation slide 19 must show the five publishable QVoice themes.",
    )
    require(
        retention_theme_stage.count("qv19-attrition-pill") == 5
        and "Explicit intent to leave" in retention_theme_stage
        and "Not publishable (n&lt;30)" in retention_theme_stage,
        "V7 navigation slide 19 must keep the separate suppressed intent-to-leave note.",
    )
    retention_rates = [
        float(row["trailing_12m_voluntary_attrition_rate_percent"])
        for row in qvoice_retention_theme_august_attrition_evidence["rows"]
    ]
    require("(2025-08-24, 2026-08-23]" in retention_theme_stage, "V7 navigation slide 19 must identify the August trailing-12-month window.")
    require("Themes can overlap" in retention_theme_stage, "V7 navigation slide 19 must disclose theme overlap.")
    for row in qvoice_retention_theme_august_attrition_evidence["rows"]:
        label = str(row["theme"])
        rate = float(row["trailing_12m_voluntary_attrition_rate_percent"])
        expected_class = attrition_pill_class(rate, retention_rates)
        require(html.escape(label) in retention_theme_stage, f"V7 navigation slide 19 is missing the {label!r} theme.")
        require(f">{rate:.1f}%</span>" in retention_theme_stage, f"V7 navigation slide 19 is missing the {label!r} attrition rate.")
        require(
            f"qv19-attrition-pill {expected_class}" in retention_theme_stage,
            f"V7 navigation slide 19 {label!r} rate lacks its expected {expected_class} color.",
        )

    for metric, slide_number in (("intent_to_stay", 23), ("career_goals", 24)):
        stage_html = stage_fragment(deck, slide_number)
        expected_marker = f'data-v7-qvoice-favorable-unfavorable="{metric}"'
        require(expected_marker in stage_html, f"V7 QVoice slide {slide_number} is missing its Favorable / No favorable marker.")
        require(stage_html.count('class="qvoice-fu-wave-card"') == 3, f"V7 QVoice slide {slide_number} must show three survey years.")
        expected_response_rows = 18 if metric == "intent_to_stay" else 12
        require(stage_html.count('class="qvoice-fu-response"') == expected_response_rows, f"V7 QVoice slide {slide_number} must show the driver and all component response rows for every year.")
        require('qvoice-inline-attrition-panel' not in stage_html and 'qvoice-inline-attrition-pill' not in stage_html, f"V7 QVoice slide {slide_number} retains the obsolete YTD stored-value panel.")
        require('Observable response coverage' not in stage_html and 'stored Intent-to-Stay response' not in stage_html and 'stored Career Goals response' not in stage_html, f"V7 QVoice slide {slide_number} retains obsolete coverage/stored-value language.")
        for wave in qvoice_favorable_unfavorable_attrition_evidence["variables"][metric]:
            year = int(wave["year"])
            require(f">{year}</strong>" in stage_html, f"V7 QVoice slide {slide_number} is missing {year}.")
            groups = wave["groups"]
            rates = [float(groups[label]["voluntary_attrition_rate_percent"]) for label in ("Favorable", "No favorable")]
            for label in ("Favorable", "No favorable"):
                group = groups[label]
                share = float(group["linked_response_share_percent"])
                rate = float(group["voluntary_attrition_rate_percent"])
                cohort = int(group["matched_employee_count"])
                exits = int(group["voluntary_exit_count"])
                expected_class = attrition_pill_class(rate, rates)
                require(f"width:{share:.4f}%" in stage_html, f"V7 QVoice slide {slide_number} is missing the {year} {label} share.")
                require(f">{share:.1f}%</strong>" in stage_html, f"V7 QVoice slide {slide_number} is missing the {year} {label} label.")
                require(f">{rate:.1f}%</span>" in stage_html, f"V7 QVoice slide {slide_number} is missing the {year} {label} attrition rate.")
                require(f"n={cohort:,} · {exits:,} exits" in stage_html, f"V7 QVoice slide {slide_number} is missing the {year} {label} cohort/exits detail.")
                require(f"qvoice-fu-attrition-pill v6-rate-pill {expected_class}" in stage_html, f"V7 QVoice slide {slide_number} {year} {label} rate lacks its year-relative color.")
            if year in (2024, 2025):
                require("Annual attrition · 12 months" in stage_html, f"V7 QVoice slide {slide_number} must identify annual attrition.")
            else:
                require("YTD attrition · not annualized" in stage_html and "27 Sep 2026" in stage_html, f"V7 QVoice slide {slide_number} must identify the non-annualized 2026 YTD outcome.")
            for component_key, component in wave["components"].items():
                require(html.escape(str(component["short_label"])) in stage_html, f"V7 QVoice slide {slide_number} is missing component {component_key}.")
                component_groups = component["groups"]
                component_rates = [float(component_groups[label]["voluntary_attrition_rate_percent"]) for label in ("Favorable", "No favorable")]
                for label in ("Favorable", "No favorable"):
                    group = component_groups[label]
                    share = float(group["linked_response_share_percent"])
                    rate = float(group["voluntary_attrition_rate_percent"])
                    cohort = int(group["matched_employee_count"])
                    exits = int(group["voluntary_exit_count"])
                    expected_class = attrition_pill_class(rate, component_rates)
                    require(f"width:{share:.4f}%" in stage_html, f"V7 QVoice slide {slide_number} is missing the {year} {component_key} {label} share.")
                    require(f">{rate:.1f}%</span>" in stage_html, f"V7 QVoice slide {slide_number} is missing the {year} {component_key} {label} attrition rate.")
                    require(f"n={cohort:,} · {exits:,} exits" in stage_html, f"V7 QVoice slide {slide_number} is missing the {year} {component_key} {label} cohort/exits detail.")
                    require(f"qvoice-fu-attrition-pill v6-rate-pill {expected_class}" in stage_html, f"V7 QVoice slide {slide_number} {year} {component_key} {label} rate lacks its component-relative color.")

    # Navigation slides 28–39: every published label must now be annual.
    annual_stage_counts = {
        29: 12,  # two current distributions; annual rates are unavailable for both
        31: 12,
        32: 10,
        35: 25,
        36: 20,
        37: 10,
        38: 37,
        39: 14,
        40: 11,
    }
    for slide_number, expected_pills in annual_stage_counts.items():
        stage_html = stage_fragment(deck, slide_number)
        require(
            stage_html.count("v7-annual-attrition") == expected_pills,
            f"V7 slide {slide_number} has an unexpected number of annual attrition labels.",
        )
        require(
            not re.search(r"six-month attrition|six-month voluntary attrition", stage_html, flags=re.I),
            f"V7 slide {slide_number} still labels a rate as six-month attrition.",
        )
        if slide_number == 29:
            require(
                "(2025-08-24, 2026-08-23]" in stage_html,
                "V7 slide 29 must visibly describe its August trailing-12-month outcome window.",
            )
        else:
            require(
                "12 months after the historical snapshot" in stage_html
                or "12 months after the snapshot" in stage_html
                or "Trailing 12-month voluntary attrition" in stage_html,
                f"V7 slide {slide_number} must visibly describe its annual outcome window.",
            )

    promotion_track_stage = stage_fragment(deck, 34)
    require("track-story-card" in promotion_track_stage, "V7 slide 30 must use the pay-track story.")
    require(promotion_track_stage.count('class="track-story-row"') == 16, "V7 slide 30 must show six grouped tracks and ten exact grades.")
    require(promotion_track_stage.count("track-story-panel-top10") == 1, "V7 slide 30 must include the Top 10 compensation-grade panel.")
    require(promotion_track_stage.count('class="track-letter is-grade"') == 10, "V7 slide 30 must show ten exact compensation-grade labels.")
    require("promotion-grade-matrix" not in promotion_track_stage, "V7 slide 30 still contains the old promotion matrix.")
    require("trailing 12 months" in promotion_track_stage, "V7 slide 30 must disclose its trailing-12-month window.")

    job_profile_stage = stage_fragment(deck, 29)
    require("Time at detailed level and time in role" in job_profile_stage, "V7 slide 29 must show the two validated tenure measures.")
    require("field proxy" not in job_profile_stage, "V7 slide 29 still exposes removed technical terminology.")
    require(job_profile_stage.count("attr-unavailable") == 0, "V7 slide 29 must not leave either validated tenure rate unavailable.")
    require(job_profile_stage.count("aria-label=\"Annual voluntary attrition (12 months) for") == 12, "V7 slide 29 must show six annual rates for each tenure measure.")
    require(job_profile_stage.count("trailing 12m attrition") == 2, "V7 slide 29 must identify the trailing-12-month rate on both cards.")
    require("(2025-08-24, 2026-08-23]" in job_profile_stage, "V7 slide 29 must show the August trailing-12-month window.")
    require("levelentrydate" in job_profile_stage and "max_hire_rehire_date" in job_profile_stage, "V7 slide 29 must disclose the detailed-level date rule.")
    for metric in ("time_at_detailed_level", "time_in_role"):
        for row in time_in_job_profile_time_in_role_evidence["display_rows"][metric]:
            require(f"{int(row['employee_count']):,}" in job_profile_stage, f"V7 slide 29 is missing the {metric} current distribution count.")
    for row in time_in_job_profile_time_in_role_evidence["annual_rows"]:
        require(f"{float(row['annual_attrition_rate_percent']):.1f}%" in job_profile_stage, f"V7 slide 29 is missing the Time-in-role annual rate for {row['category']}.")
    layers_stage = stage_fragment(deck, 37)
    layer_pills = re.findall(r'<span class="v7-annual-attrition v6-rate-pill ([^"]*)"', layers_stage)
    require(len(layer_pills) == 10 and all("attr-unavailable" not in classes for classes in layer_pills), "V7 slide 37 must show ten validated annual attrition labels.")
    require("Baseline category membership is reconstructed" in layers_stage, "V7 slide 37 must explain its baseline cohort definition.")
    comp_ratio_stage = stage_fragment(deck, 39)
    require("comp-ratio-voluntary-attrition-chart" not in comp_ratio_stage, "V7 slide 39 must not retain the six-month trend chart.")
    require("same seven annual bands" in comp_ratio_stage, "V7 slide 39 must identify the annual band replacement.")
    within_team_stage = stage_fragment(deck, 40)
    require("annual team attrition" in within_team_stage.lower(), "V7 slide 40 must name the direct-report outcome as annual team attrition.")

    # Published direct-field rates remain traceable to the evidence in their matching visual.
    direct_metric_stages = {
        "original_hire_tenure": 31,
        "latest_hire_tenure": 31,
        "comp_ratio_band": 39,
    }
    for metric, slide_number in direct_metric_stages.items():
        stage_html = stage_fragment(deck, slide_number)
        for row in annual_rows_by_category(nav28_39_direct_annual_attrition_evidence, metric).values():
            rate = annual_rate(row)
            if rate is not None:
                require(f">{rate:.1f}%</span>" in stage_html, f"V7 slide {slide_number} is missing annual {metric} evidence.")
    promotion_stage = stage_fragment(deck, 32)
    require('data-v7-promotion-comparable-cohorts="true"' in promotion_stage, "V7 slide 32 must use comparable promotion cohorts.")
    require("People with no recorded promotion" in promotion_stage, "V7 slide 32 must use the plain-language no-recorded-promotion label.")
    require("never promoted" in promotion_stage.lower(), "V7 slide 32 must state that the proxy is not never promoted.")
    require("excluding RF360" in promotion_stage, "V7 slide 32 must disclose the applied RF360 exclusion.")
    require("(2025-08-24, 2026-08-23]" in promotion_stage, "V7 slide 32 must disclose its fixed annual outcome window.")
    require(promotion_stage.count("v7-promotion-comparable-row") == 10, "V7 slide 32 must retain five temporal bands per panel.")
    for key in ("recorded_promotion_distribution", "no_recorded_promotion_role_tenure_proxy_distribution"):
        for row in time_since_last_promotion_comparable_cohorts_evidence[key]:
            label = str(row["label"])
            require(html.escape(label) in promotion_stage, f"V7 slide 32 is missing the {label} promotion band.")
            if row["publication_status"] == "publishable":
                require(f"n={int(row['employee_count']):,}" in promotion_stage, f"V7 slide 32 is missing the {label} cohort count.")
                require(f">{float(row['annual_attrition_rate_percent']):.1f}%</span>" in promotion_stage, f"V7 slide 32 is missing the {label} annual rate.")
            else:
                require(f"n={int(row['employee_count']):,}" in promotion_stage, f"V7 slide 32 is missing the {label} internal exploratory cohort count.")
                require(f">{float(row['annual_attrition_rate_percent']):.1f}%*</span>" in promotion_stage, f"V7 slide 32 is missing the {label} internal exploratory rate marker.")
                require("internal-small-cohort" in promotion_stage, "V7 slide 32 must flag the authorized small cohort as exploratory.")
    for metric in ("within_team_review_count", "within_team_review_share", "within_team_no_comparable"):
        stage_html = stage_fragment(deck, 40)
        for row in annual_rows_by_category(within_team_annual_attrition_evidence, metric).values():
            rate = annual_rate(row)
            if rate is not None and str(row["category"]) != "8+ groups to review":
                require(f">{rate:.1f}%</span>" in stage_html, "V7 slide 40 is missing annual team-attrition evidence.")
    timezone_stage = stage_fragment(deck, 42)
    require('data-v7-manager-timezone-proximity="true"' in timezone_stage, "V7 stage 42 must use the manager time-zone proxy.")
    require('data-v7-manager-timezone-august-trailing-12m="true"' in timezone_stage, "V7 stage 42 must use the August trailing-12-month cohort.")
    require("Residential distance from manager" not in timezone_stage, "V7 stage 42 retains the replaced residential-distance framing.")
    require(timezone_stage.count("manager-timezone-bar-row") == 3, "V7 stage 42 must show exactly the three requested proximity categories.")
    latest = manager_timezone_august_trailing_12m_evidence["latest_distribution"]
    for category in ("same_office_site", "different_site_up_to_4_hours", "different_site_more_than_4_hours"):
        require(f"{int(latest[category]['employee_count']):,}" in timezone_stage, f"V7 stage 42 is missing the current {category} count.")
    diagnostics = manager_timezone_august_trailing_12m_evidence["diagnostics"]
    require(f"{int(diagnostics['current_pair_count']):,}" in timezone_stage, "V7 stage 42 is missing its current-pair coverage value.")
    require(f"{int(latest['unmapped_time_zone_proxy']['employee_count']):,}" in timezone_stage, "V7 stage 42 is missing its current unmapped coverage value.")
    annual_rows = manager_timezone_august_trailing_12m_evidence["annual_attrition"]
    annual_rates = [float(row["attrition_rate_percent"]) for row in annual_rows.values()]
    for category in ("same_office_site", "different_site_up_to_4_hours", "different_site_more_than_4_hours"):
        row = annual_rows[category]
        rate = float(row["attrition_rate_percent"])
        expected_class = annual_rate_class(rate, annual_rates)
        require(
            f'manager-timezone-annual-pill {expected_class}' in timezone_stage and f">{rate:.1f}%</span>" in timezone_stage,
            "V7 stage 42 is missing a validated August trailing-12-month label.",
        )
    require(timezone_stage.count("manager-timezone-annual-pill") == 3, "V7 stage 42 must show exactly one annual label per category.")
    require("Annual voluntary attrition (12 months)" in timezone_stage and "24 Aug 2025 baseline cohort followed through 23 Aug 2026" in timezone_stage, "V7 stage 42 must disclose the August-to-August outcome window.")
    require("2026 YTD attrition" not in timezone_stage and "not annualized" not in timezone_stage, "V7 stage 42 retains obsolete YTD language.")
    for prohibited_header in ("FY2020", "FY2021", "FY2022", "FY2023", "FY2024", "manager-timezone-rate-grid"):
        require(prohibited_header not in timezone_stage, "V7 stage 42 must not retain the historical annual matrix.")

    # Visible slides 38-44 / technical stages 43-50: attrition is calculated
    # from the same baseline category population used by each label.
    nav38_expected_pills = {43: 3, 44: 4, 45: 3, 46: 3, 47: 4, 48: 2, 49: 16, 50: 10}
    for slide_number, expected_pills in nav38_expected_pills.items():
        stage_html = stage_fragment(deck, slide_number)
        require(
            stage_html.count("v7-annual-attrition") == expected_pills,
            f"V7 slide {slide_number} has an unexpected number of slides-38-plus annual attrition labels.",
        )
    for slide_number in (43, 44, 45, 46, 47, 48, 49):
        stage_html = stage_fragment(deck, slide_number)
        require("2025-08-24" in stage_html and "2026-08-23" in stage_html, f"V7 slide {slide_number} must disclose the August outcome window.")
        require("six-month attrition" not in stage_html.lower() and "six-month voluntary attrition" not in stage_html.lower(), f"V7 slide {slide_number} retains a six-month attrition label.")
    require(stage_fragment(deck, 50).count("attr-unavailable") == 10, "V7 slide 50 must show ten gray Not estimable labels.")
    require("Annual attrition (12 months): not estimable" in stage_fragment(deck, 50), "V7 slide 50 must identify the unavailable annual outcome.")
    nav38_metric_stage_map = {
        "office_site_relationship": 43,
        "manager_observed_expected": 44,
        "recent_team_exits_under_manager": 45,
        "above_average_team_turnover": 46,
        "manager_leaving_baseline_6m": 47,
        "manager_change": 48,
    }
    for metric, slide_number in nav38_metric_stage_map.items():
        stage_html = stage_fragment(deck, slide_number)
        rows = nav38_metric_rows(nav38_plus_august_attrition_evidence, metric)
        for row in rows.values():
            if str(row.get("publication_status", "publishable")) == "publishable":
                rendered_rate = f"{float(row['annual_attrition_rate_percent']):.1f}%"
                rate_marker = f">{rendered_rate}</span>" if slide_number != 48 else f" {rendered_rate}</span>"
                require(rate_marker in stage_html, f"V7 slide {slide_number} is missing a validated annual rate for {metric}.")
    for metric in (
        "All observed manager changes Â· trailing 6 months",
        "All observed manager changes Â· trailing 12 months",
        "Sensitivity: exclude same-date transfer/promotion Â· trailing 6 months",
        "Sensitivity: exclude same-date transfer/promotion Â· trailing 12 months",
    ):
        stage_html = stage_fragment(deck, 49)
        for row in nav38_metric_rows(nav38_plus_august_attrition_evidence, metric).values():
            require(f">{float(row['annual_attrition_rate_percent']):.1f}%</span>" in stage_html, f"V7 slide 49 is missing a validated annual rate for {metric}.")
    manager_leaving_stage = stage_fragment(deck, 47)
    require(
        manager_leaving_stage.count("internal-small-cohort") == 2
        and manager_leaving_stage.count(">25.0%*</span>") == 2
        and "n=4 and 1 voluntary exit" in manager_leaving_stage,
        "V7 slide 47 must show the authorized descriptive subthreshold manager-leaving rate.",
    )
    for query_name, payload in nav38_plus_august_attrition_evidence["queries"].items():
        encoded = json.dumps(payload["rows"], ensure_ascii=False).lower()
        require("employee_id" not in encoded and "manager_id" not in encoded, f"Slides 38+ evidence exposes an identifier in {query_name}.")
    for prohibited in ("employee_id", "manager_id", "pay_value", "salary"):
        require(prohibited not in deck.lower(), f"V7 output must not expose {prohibited}.")


def application_visual_css() -> str:
    match = re.search(
        r'/\* V7 slide 3 — recent application intensity in the Location grammar\. \*/.*?(?=\n\s*/\* V7 slide 14)',
        css_block(),
        flags=re.S,
    )
    require(match is not None, "Could not isolate the V7 application visual CSS.")
    return match.group(0).rstrip()


def replace_application_visual_css(deck: str) -> str:
    pattern = r'\s*/\* V7 (?:slide 3|slides 3–4).*?(?=\n\s*/\* V7 slide 14)'
    updated, replacements = re.subn(pattern, "\n\n    " + application_visual_css(), deck, count=1, flags=re.S)
    require(replacements == 1, "Could not replace only the slide 3–4 visual CSS block.")
    return updated


def application_slide_3_css() -> str:
    match = re.search(
        r'/\* V7 slide 3 — recent application intensity in the Location grammar\. \*/.*?(?=\n\s*/\* V7 slide 4)',
        css_block(),
        flags=re.S,
    )
    require(match is not None, "Could not isolate the V7 slide 3 visual CSS.")
    return match.group(0).rstrip()


def replace_application_slide_3_css(deck: str) -> str:
    replacement = "\n\n    " + application_slide_3_css()
    if "/* V7 slide 3 — recent application intensity" in deck:
        pattern = r'\s*/\* V7 slide 3 — recent application intensity.*?(?=\n\s*/\* V7 slide 4)'
        updated, replacements = re.subn(pattern, replacement, deck, count=1, flags=re.S)
    else:
        pattern = r'\s*/\* V7 slides 3.*?Location grammar\. \*/.*?(?=\n\s*#slide-4 \.application-coverage-meta)'
        slide_4_prefix = (
            "\n\n    /* V7 slide 4 — application coverage simplified in the Location grammar. */\n"
            "    #slide-4 .application-coverage-story { padding:14px 16px 10px; gap:10px; }"
        )
        updated, replacements = re.subn(pattern, replacement + slide_4_prefix, deck, count=1, flags=re.S)
    require(replacements == 1, "Could not replace only the slide 3 visual CSS block.")
    return updated


def application_stage_map(deck: str) -> dict[int, str]:
    stages: dict[int, str] = {}
    for match in re.finditer(r'<div class="slide-stage" id="slide-(\d+)"', deck):
        slide_number = int(match.group(1))
        require(slide_number not in stages, f"Duplicate technical slide id: {slide_number}.")
        stages[slide_number] = stage_fragment(deck, slide_number)
    return stages


def validate_application_trailing_august_slide_3_content(slide_3: str, application_attrition_evidence: dict[str, Any]) -> None:
    require('application-visual-story' in slide_3, "Slide 3 rolling-August visual story is missing.")
    require('<table' not in slide_3, "Slide 3 must not contain a visible table.")
    require(slide_3.count('application-focus-card') == 2, "Slide 3 must show the two visible August cutoffs.")
    require(slide_3.count('application-focus-row') == 8, "Slide 3 must show four application buckets for each visible cutoff.")
    require(slide_3.count('application-repeat-stat') == 2, "Slide 3 must show one 2+ jobs summary per visible cutoff.")
    require(slide_3.count('application-focus-attrition v6-rate-pill') == 8, "Slide 3 must show one direct attrition label beside every bar.")
    require('Not estimable' not in slide_3, "Rolling observed attrition must not retain prospective-follow-up placeholders.")
    require('Distribution + observed attrition' in slide_3, "Slide 3 must identify observed attrition.")
    require('not prospective follow-up' in slide_3, "Slide 3 must distinguish its trailing window from prospective follow-up.")
    require('Aug 2025' in slide_3 and 'Aug 2026' in slide_3, "Slide 3 is missing a visible August cutoff label.")
    for historical_year in (2022, 2023, 2024):
        require(f'Aug {historical_year}' not in slide_3, "Slide 3 must keep distant August cutoffs in evidence only.")

    rows_by_key = {
        (int(row['cutoff_year']), str(row['application_bucket'])): row
        for row in application_attrition_evidence['rows']
    }
    repeat_shares: dict[int, float] = {}
    for year in (2025, 2026):
        year_rows = [rows_by_key[(year, bucket)] for bucket in ('1', '2', '3', '4+')]
        total = int(year_rows[0]['total_distinct_applicants'])
        repeat_count = sum(int(row['distinct_applicant_count']) for row in year_rows if str(row['application_bucket']) != '1')
        repeat_shares[year] = 100 * repeat_count / total
        for row in year_rows:
            pct = 100 * int(row['distinct_applicant_count']) / total
            rate = float(row['trailing_12m_voluntary_attrition_percent'])
            expected_class = trailing_august_attrition_class(row, year_rows)
            small_base_marker = "*" if int(row['distinct_applicant_count']) < 30 else ""
            require(f'{pct:.2f}%' in slide_3, "Slide 3 lost a rolling-window distribution percentage.")
            require(f'n={int(row["distinct_applicant_count"]):,}' in slide_3, "Slide 3 lost a rolling-window cohort count.")
            require(f'>{rate:.2f}%{small_base_marker}</span>' in slide_3, "Slide 3 lost a direct observed-attrition label.")
            require(
                f'application-focus-attrition v6-rate-pill {expected_class}' in slide_3,
                "Slide 3 attrition labels must use the Location high/low color grammar.",
            )
    require(f'+{repeat_shares[2026] - repeat_shares[2025]:.2f} pp vs Aug 2025' in slide_3, "Slide 3 lost the August repeat-application comparison.")


def validate_application_consolidated_slide_3_content(
    slide_3: str,
    application_attrition_evidence: dict[str, Any],
    application_evidence: dict[str, Any],
) -> None:
    """Validate the coherent, single-slide application story after slide 4 removal."""
    validate_application_trailing_august_slide_3_content(slide_3, application_attrition_evidence)
    require('application-coverage-context' in slide_3, "Slide 3 must retain the application-feed coverage context.")
    require('Coverage is data availability, not the percentage of employees seeking a role.' in slide_3, "Slide 3 must distinguish coverage from employee application prevalence.")
    by_bucket = {str(row["application_bucket"]): row for row in application_evidence["latest_distribution"]}
    covered = by_bucket["0"]
    unknown = by_bucket["Unknown"]
    coverage_pct = float(covered["coverage_percent"])
    unknown_pct = float(unknown["unknown_percent"])
    eligible = int(covered["eligible_employee_snapshots"])
    covered_count = int(covered["observed_employee_snapshots"])
    unknown_count = int(unknown["employee_snapshots"])
    require(application_evidence["latest_snapshot"] in slide_3, "Slide 3 lost the application-coverage snapshot date.")
    require(f'{coverage_pct:.2f}% covered' in slide_3, "Slide 3 lost the observed application-feed percentage.")
    require(f'{unknown_pct:.2f}% Unknown' in slide_3, "Slide 3 lost the unknown application-feed percentage.")
    for count in (eligible, covered_count, unknown_count):
        require(f'n={count:,}' in slide_3 or f'{count:,} active regular employee-snapshots' in slide_3, "Slide 3 lost an application-coverage count.")
    require(slide_3.count('application-focus-attrition v6-rate-pill') == 8, "Slide 3 must retain eight direct attrition pills.")
    require(slide_3.count('is-small-base') == 4, "Slide 3 must flag all four sub-30 attrition categories.")


def validate_application_slide_3_content(slide_3: str, application_attrition_evidence: dict[str, Any]) -> None:
    require('application-visual-story' in slide_3, "Slide 3 visual story is missing.")
    require('<table' not in slide_3, "Slide 3 still contains a visible table.")
    require(slide_3.count('application-focus-card') == 2, "Slide 3 must focus on FY2025 and FY2026 YTD.")
    require(slide_3.count('application-focus-row') == 8, "Slide 3 must show four application buckets for each recent year.")
    require(slide_3.count('application-repeat-stat') == 2, "Slide 3 must show one 2+ jobs summary per recent year.")
    require(
        slide_3.count('class="application-focus-attrition v6-rate-pill attr-unavailable is-unavailable"') == 8,
        "Slide 3 must show one attrition-status pill beside every application bar.",
    )
    require(slide_3.count('>Not estimable</span>') == 8, "Slide 3 lost a bucket-level incomplete-follow-up status.")
    require('Distribution + 12-month attrition' in slide_3, "Slide 3 must identify its distribution and attrition encodings.")
    require('+9.20 pp' in slide_3, "Slide 3 lost the FY2025-to-FY2026 YTD change.")
    for historical_year in (2022, 2023, 2024):
        require(f'FY{historical_year}' not in slide_3, "Slide 3 must omit distant historical years from the visual.")
    for row in application_attrition_evidence["rows"]:
        if int(row["fiscal_year"]) not in (2025, 2026):
            continue
        distribution = f'{float(row["distribution_percent"]):.2f}%'
        count = f'n={int(row["distinct_applicants"]):,}'
        require(distribution in slide_3 and count in slide_3, "Slide 3 lost a recent-year distribution value.")


def validate_application_visual_refresh(
    before: str,
    after: str,
    application_evidence: dict[str, Any],
    application_attrition_evidence: dict[str, Any],
) -> None:
    before_stages = application_stage_map(before)
    after_stages = application_stage_map(after)
    require(before_stages.keys() == after_stages.keys(), "The targeted refresh changed the slide inventory.")
    for slide_number in before_stages:
        if slide_number not in (3, 4):
            require(before_stages[slide_number] == after_stages[slide_number], f"Targeted refresh changed slide {slide_number}.")

    slide_3 = after_stages[3]
    slide_4 = after_stages[4]
    validate_application_trailing_august_slide_3_content(slide_3, application_attrition_evidence)

    require('application-coverage-story' in slide_4, "Slide 4 coverage story is missing.")
    require('<table' not in slide_4, "Slide 4 contains a table.")
    require('application-employee-snapshot-trend-chart' not in slide_4, "Slide 4 still contains the dense Plotly trend chart.")
    require(slide_4.count('application-covered-row') == 3, "Slide 4 must show the three covered application buckets.")
    require(slide_4.count('application-history-month') == 12, "Slide 4 must show all twelve complete snapshots.")
    require(application_evidence["latest_snapshot"] in slide_4, "Slide 4 lost the latest snapshot date.")
    for row in application_evidence["latest_distribution"]:
        pct = f'{float(row["percent_of_eligible_snapshots"]):.2f}%'
        count = f'n={int(row["employee_snapshots"]):,}'
        require(pct in slide_4 and count in slide_4, "Slide 4 lost a latest-distribution value.")

    require(after.count('<div class="slide-stage"') == before.count('<div class="slide-stage"'), "Slide count changed during targeted refresh.")
    require(after.count('class="nav-pill') == before.count('class="nav-pill'), "Navigation count changed during targeted refresh.")
    require('data-deliverable-mode="internal_analysis"' in after, "Internal-analysis classification is missing.")
    for prohibited in ("employee_id", "manager_id", "pay_value", "salary"):
        require(prohibited not in after.lower(), f"Targeted refresh must not expose {prohibited}.")


def validate_application_slide_3_refresh(
    before: str,
    after: str,
    application_attrition_evidence: dict[str, Any],
) -> None:
    before_stages = application_stage_map(before)
    after_stages = application_stage_map(after)
    require(before_stages.keys() == after_stages.keys(), "The slide 3 refresh changed the slide inventory.")
    for slide_number in before_stages:
        if slide_number != 3:
            require(before_stages[slide_number] == after_stages[slide_number], f"Slide 3 refresh changed slide {slide_number}.")
    validate_application_trailing_august_slide_3_content(after_stages[3], application_attrition_evidence)
    require(after.count('<div class="slide-stage"') == before.count('<div class="slide-stage"'), "Slide count changed during slide 3 refresh.")
    require(after.count('class="nav-pill') == before.count('class="nav-pill'), "Navigation count changed during slide 3 refresh.")
    require('data-deliverable-mode="internal_analysis"' in after, "Internal-analysis classification is missing.")
    for prohibited in ("employee_id", "manager_id", "pay_value", "salary"):
        require(prohibited not in after.lower(), f"Slide 3 refresh must not expose {prohibited}.")


def application_slide_3_manifest_entry() -> dict[str, Any]:
    return {
        "slide_number": 3,
        "title": "Applicants applying to 2+ jobs more than doubled in FY2026 YTD",
        "visual": (
            "Two Location-style horizontal-bar panels show only FY2025 and FY2026 YTD, with four "
            "direct-labeled distribution rows per year, a 2+ jobs summary, and a visible 12-month "
            "attrition-status pill beside every bar. FY2022–FY2024 remain in the evidence file but are "
            "intentionally omitted from the slide."
        ),
        "not_estimable_rule": (
            "FY2025 and FY2026 YTD remain Not estimable because the 12-month follow-up is incomplete; "
            "no zero imputation."
        ),
        "recent_year_change": {
            "fy2025_two_plus_percent": 7.68,
            "fy2026_ytd_two_plus_percent": 16.88,
            "change_percentage_points": 9.20,
        },
    }


def update_application_slide_3_validation(validation: dict[str, Any]) -> None:
    for obsolete_key in (
        "application_attrition_not_estimable_cells_visible",
        "application_slide_3_complete_year_panels",
        "application_slide_3_complete_year_rows",
    ):
        validation.pop(obsolete_key, None)
    validation.update(
        {
            "application_attrition_cells_visible": 8,
            "application_attrition_rates_visible": 0,
            "application_attrition_not_estimable_buckets_retained": 8,
            "application_attrition_not_estimable_status_pills_visible": 8,
            "application_attrition_not_estimable_year_labels_visible": 2,
            "application_slide_3_tables_visible": 0,
            "application_slide_3_recent_year_panels": 2,
            "application_slide_3_recent_year_rows": 8,
            "application_slide_3_historical_years_visible": 0,
            "application_slide_3_distribution_only_years": 2,
            "application_slide_3_change_percentage_points": 9.20,
        }
    )


def application_trailing_august_slide_3_manifest_entry() -> dict[str, Any]:
    return {
        "slide_number": 3,
        "title": "Repeat applications more than doubled; application coverage is 9.76%",
        "visual": (
            "A compact coverage rail shows that application data is observed for 9.76% of active regular "
            "employee-snapshots, separate from the two August 2025 and August 2026 trailing-12-month "
            "application panels. Every application bucket has its distribution, cohort n, and a direct "
            "observed voluntary-attrition label. August 2022-2024 remain aggregate evidence only."
        ),
        "observed_attrition_rule": (
            "Strict voluntary terminations after the first qualifying application and on or before the "
            "same August cutoff, divided by distinct linked applicants in that rolling window. This is "
            "observed trailing attrition, not prospective follow-up."
        ),
        "recent_cutoff_change": {
            "august_2025_two_plus_percent": 7.93,
            "august_2026_two_plus_percent": 16.75,
            "change_percentage_points": 8.82,
        },
        "coverage_context": {
            "snapshot_date": "2026-08-23",
            "eligible_employee_snapshots": 50043,
            "observed_application_coverage_percent": 9.7596,
            "unknown_percent": 90.2404,
        },
    }


def update_application_trailing_august_slide_3_validation(validation: dict[str, Any]) -> None:
    for obsolete_key in (
        "application_attrition_not_estimable_cells_visible",
        "application_attrition_not_estimable_buckets_retained",
        "application_attrition_not_estimable_status_pills_visible",
        "application_attrition_not_estimable_year_labels_visible",
        "application_slide_3_complete_year_panels",
        "application_slide_3_complete_year_rows",
        "application_slide_3_distribution_only_years",
    ):
        validation.pop(obsolete_key, None)
    validation.update(
        {
            "application_attrition_cells_visible": 8,
            "application_attrition_rates_visible": 8,
            "application_attrition_observed_trailing_12m_pills_visible": 8,
            "application_attrition_colored_pills_visible": 8,
            "application_slide_3_tables_visible": 0,
            "application_slide_3_recent_august_panels": 2,
            "application_slide_3_recent_august_rows": 8,
            "application_slide_3_historical_years_visible": 0,
            "application_slide_3_change_percentage_points": 8.82,
            "application_slide_3_subthreshold_attrition_pills_flagged": 4,
            "application_coverage_context_visible": 1,
            "application_coverage_percent_visible": 9.7596,
            "application_slide_4_removed": True,
        }
    )


def validate_application_slide_consolidation(
    before: str,
    after: str,
    application_attrition_evidence: dict[str, Any],
    application_evidence: dict[str, Any],
) -> None:
    before_stages = application_stage_map(before)
    after_stages = application_stage_map(after)
    require(4 in before_stages and 4 not in after_stages, "The standalone application-coverage stage was not removed.")
    require(after_stages.keys() == before_stages.keys() - {4}, "Slide consolidation changed an unexpected stage.")
    last_stage = max(after_stages)
    for slide_number in after_stages:
        # Stage 2 owns the navigation markup. The trailing script is parsed as
        # part of the final stage, so its updated chart payload is expected.
        if slide_number not in (2, 3, last_stage):
            require(before_stages[slide_number] == after_stages[slide_number], f"Slide consolidation changed slide {slide_number}.")

    validate_application_consolidated_slide_3_content(
        after_stages[3], application_attrition_evidence, application_evidence
    )
    require(len(after_stages) == 48, "The deck must contain 48 slide stages after slide 4 removal.")
    nav_ids = re.findall(r'<button class="nav-pill[^>]* data-slide="(\d+)"', after)
    require(nav_ids == [str(index) for index in range(48)], "Navigation must retain 48 contiguous items after slide 4 removal.")
    nav_ranges = re.findall(r'<span class="nav-section-range">(\d+)[^0-9]+(\d+)</span>', after)
    require(
        [(int(start), int(end)) for start, end in nav_ranges]
        == [(1, 2), (3, 4), (5, 17), (18, 25), (26, 37), (38, 48)],
        "Navigation ranges must reconcile after slide 4 removal.",
    )
    for required_range in ('Slides 3-9', 'Slides 10-17', 'Slides 18-25', 'Slides 26-36', 'Slides 37-48'):
        require(required_range in after, f"Agenda range {required_range} is missing.")
    for forbidden in ('id="slide-4"', 'data-v7-application-coverage="true"'):
        require(forbidden not in after, f"Removed slide 4 content remains: {forbidden}")
    require('data-deliverable-mode="internal_analysis"' in after, "Internal-analysis classification is missing.")
    for prohibited in ("employee_id", "manager_id", "pay_value", "salary"):
        require(prohibited not in after.lower(), f"Slide consolidation must not expose {prohibited}.")


def consolidate_application_slides() -> None:
    """Move coverage context to slide 3 and remove the standalone slide 4."""
    require(OUTPUT_DECK.exists(), f"Missing current V7 deck: {OUTPUT_DECK}")
    require(MANIFEST_FILE.exists(), f"Missing current V7 manifest: {MANIFEST_FILE}")
    application_evidence = load_application_evidence()
    application_attrition_evidence = load_application_attrition_evidence()

    source_hash = digest(OUTPUT_DECK)
    before = OUTPUT_DECK.read_text(encoding="utf-8")
    slide_3, chart_rows = build_application_trailing_august_attrition_slide(
        application_attrition_evidence, application_evidence
    )
    after = replace_stage_fragment(before, 3, slide_3)
    after, replacements = re.subn(
        r'var chartData = \[.*?\];',
        f'var chartData = {json.dumps(chart_rows, ensure_ascii=False, separators=(",", ":"))};',
        after,
        count=1,
        flags=re.S,
    )
    require(replacements == 1, "Could not update the application chart data during consolidation.")
    after = remove_application_coverage_slide(after)
    after = replace_application_visual_css(after)
    validate_application_slide_consolidation(before, after, application_attrition_evidence, application_evidence)
    require(digest(OUTPUT_DECK) == source_hash, "The deck changed concurrently; application consolidation was not written.")

    temporary_deck = OUTPUT_DECK.with_suffix(".application-consolidated.tmp")
    temporary_deck.write_text(after, encoding="utf-8")
    temporary_deck.replace(OUTPUT_DECK)
    written_deck_hash = digest(OUTPUT_DECK)

    manifest_hash = digest(MANIFEST_FILE)
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    manifest["updated_slide_3"] = application_trailing_august_slide_3_manifest_entry()
    manifest.pop("updated_slide_4", None)
    validation = manifest.setdefault("validation", {})
    update_application_trailing_august_slide_3_validation(validation)
    for obsolete_key in (
        "application_slide_4_tables_visible",
        "application_slide_4_covered_bucket_rows",
        "application_slide_4_monthly_bars",
    ):
        validation.pop(obsolete_key, None)
    validation.update(
        {
            "slides": 47,
            "navigation_items": 47,
            "application_slide_consolidation_outcome": "pass",
        }
    )
    manifest["output_deck"] = {
        "path": str(OUTPUT_DECK.relative_to(ROOT)).replace("\\", "/"),
        "sha256": written_deck_hash,
    }
    require(digest(OUTPUT_DECK) == written_deck_hash, "The deck changed again before the consolidation manifest was written.")
    require(digest(MANIFEST_FILE) == manifest_hash, "The manifest changed concurrently; consolidation manifest was not written.")
    temporary_manifest = MANIFEST_FILE.with_suffix(".application-consolidated.tmp")
    temporary_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_manifest.replace(MANIFEST_FILE)
    print(OUTPUT_DECK)
    print(MANIFEST_FILE)


def refresh_application_visuals_only() -> None:
    require(OUTPUT_DECK.exists(), f"Missing current V7 deck: {OUTPUT_DECK}")
    require(MANIFEST_FILE.exists(), f"Missing current V7 manifest: {MANIFEST_FILE}")
    application_evidence = load_application_evidence()
    application_attrition_evidence = load_application_attrition_evidence()

    source_hash = digest(OUTPUT_DECK)
    before = OUTPUT_DECK.read_text(encoding="utf-8")
    slide_3, _ = build_application_trailing_august_attrition_slide(application_attrition_evidence)
    after = replace_stage_fragment(before, 3, slide_3)
    after = replace_stage_fragment(after, 4, build_application_snapshot_slide(application_evidence))
    after = replace_application_visual_css(after)
    validate_application_visual_refresh(before, after, application_evidence, application_attrition_evidence)
    require(digest(OUTPUT_DECK) == source_hash, "The deck changed concurrently; targeted refresh was not written.")

    temporary_deck = OUTPUT_DECK.with_suffix(".application-visuals.tmp")
    temporary_deck.write_text(after, encoding="utf-8")
    temporary_deck.replace(OUTPUT_DECK)

    manifest_hash = digest(MANIFEST_FILE)
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    manifest["updated_slide_3"] = application_trailing_august_slide_3_manifest_entry()
    manifest["updated_slide_4"] = {
        "slide_number": 4,
        "title": "Applied to a job — trailing six months",
        "visual": "One coverage-first stacked bar, three simple covered-bucket bars, and twelve compact monthly coverage bars; no visible table.",
        "latest_snapshot": application_evidence["latest_snapshot"],
        "reporting_mode": "internal_analysis",
    }
    validation = manifest.setdefault("validation", {})
    update_application_trailing_august_slide_3_validation(validation)
    validation.update(
        {
            "application_slide_4_tables_visible": 0,
            "application_slide_4_covered_bucket_rows": 3,
            "application_slide_4_monthly_bars": 12,
            "application_visual_refresh_outcome": "pass",
        }
    )
    manifest["output_deck"] = {
        "path": str(OUTPUT_DECK.relative_to(ROOT)).replace("\\", "/"),
        "sha256": digest(OUTPUT_DECK),
    }
    require(digest(MANIFEST_FILE) == manifest_hash, "The manifest changed concurrently; targeted manifest refresh was not written.")
    temporary_manifest = MANIFEST_FILE.with_suffix(".application-visuals.tmp")
    temporary_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_manifest.replace(MANIFEST_FILE)
    print(OUTPUT_DECK)
    print(MANIFEST_FILE)


def refresh_application_slide_3_only() -> None:
    require(OUTPUT_DECK.exists(), f"Missing current V7 deck: {OUTPUT_DECK}")
    require(MANIFEST_FILE.exists(), f"Missing current V7 manifest: {MANIFEST_FILE}")
    application_attrition_evidence = load_application_attrition_evidence()

    source_hash = digest(OUTPUT_DECK)
    before = OUTPUT_DECK.read_text(encoding="utf-8")
    slide_3, _ = build_application_trailing_august_attrition_slide(application_attrition_evidence)
    after = replace_stage_fragment(before, 3, slide_3)
    after = replace_application_slide_3_css(after)
    validate_application_slide_3_refresh(before, after, application_attrition_evidence)
    require(digest(OUTPUT_DECK) == source_hash, "The deck changed concurrently; slide 3 was not written.")

    temporary_deck = OUTPUT_DECK.with_suffix(".application-slide-3.tmp")
    temporary_deck.write_text(after, encoding="utf-8")
    temporary_deck.replace(OUTPUT_DECK)
    written_deck_hash = digest(OUTPUT_DECK)

    manifest_hash = digest(MANIFEST_FILE)
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    manifest["updated_slide_3"] = application_trailing_august_slide_3_manifest_entry()
    validation = manifest.setdefault("validation", {})
    update_application_trailing_august_slide_3_validation(validation)
    validation["application_slide_3_refresh_outcome"] = "pass"
    manifest["output_deck"] = {
        "path": str(OUTPUT_DECK.relative_to(ROOT)).replace("\\", "/"),
        "sha256": written_deck_hash,
    }
    require(digest(OUTPUT_DECK) == written_deck_hash, "The deck changed again before the slide 3 manifest was written.")
    require(digest(MANIFEST_FILE) == manifest_hash, "The manifest changed concurrently; slide 3 manifest was not written.")
    temporary_manifest = MANIFEST_FILE.with_suffix(".application-slide-3.tmp")
    temporary_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_manifest.replace(MANIFEST_FILE)
    print(OUTPUT_DECK)
    print(MANIFEST_FILE)


def main() -> None:
    require(SOURCE_DECK.exists(), f"Missing source deck: {SOURCE_DECK}")
    require(EVIDENCE_FILE.exists(), f"Missing frozen evidence: {EVIDENCE_FILE}")
    require(PROMOTION_TRACK_EVIDENCE_FILE.exists(), f"Missing promotion-track evidence: {PROMOTION_TRACK_EVIDENCE_FILE}")
    require(PROMOTION_GRADE_TOP10_EVIDENCE_FILE.exists(), f"Missing Top-10 compensation-grade evidence: {PROMOTION_GRADE_TOP10_EVIDENCE_FILE}")
    require(APPLICATION_EVIDENCE_FILE.exists(), f"Missing internal application evidence: {APPLICATION_EVIDENCE_FILE}")
    require(APPLICATION_ATTRITION_EVIDENCE_FILE.exists(), f"Missing application attrition evidence: {APPLICATION_ATTRITION_EVIDENCE_FILE}")
    require(GENDER_LABEL_EVIDENCE_FILE.exists(), f"Missing internal gender-label evidence: {GENDER_LABEL_EVIDENCE_FILE}")
    require(SIX_MONTH_ATTRITION_EVIDENCE_FILE.exists(), f"Missing six-month work-arrangement evidence: {SIX_MONTH_ATTRITION_EVIDENCE_FILE}")
    require(REHIRE_COMPARISON_AUGUST_TRAILING_12M_EVIDENCE_FILE.exists(), f"Missing historical Rehire comparison trailing-12-month evidence: {REHIRE_COMPARISON_AUGUST_TRAILING_12M_EVIDENCE_FILE}")
    require(JOB_FAMILY_AUGUST_SNAPSHOT_EVIDENCE_FILE.exists(), f"Missing August Job family snapshot evidence: {JOB_FAMILY_AUGUST_SNAPSHOT_EVIDENCE_FILE}")
    require(JOB_FAMILY_AUGUST_TRAILING_12M_ATTRITION_EVIDENCE_FILE.exists(), f"Missing August Job family trailing-12-month attrition evidence: {JOB_FAMILY_AUGUST_TRAILING_12M_ATTRITION_EVIDENCE_FILE}")
    require(COMMUTE_ONSITE_SIX_MONTH_ATTRITION_EVIDENCE_FILE.exists(), f"Missing Onsite commute attrition evidence: {COMMUTE_ONSITE_SIX_MONTH_ATTRITION_EVIDENCE_FILE}")
    require(COMMUTE_ALL_ELIGIBLE_SIX_MONTH_ATTRITION_EVIDENCE_FILE.exists(), f"Missing All eligible commute attrition evidence: {COMMUTE_ALL_ELIGIBLE_SIX_MONTH_ATTRITION_EVIDENCE_FILE}")
    require(COMMUTE_AUGUST_SNAPSHOT_EVIDENCE_FILE.exists(), f"Missing August Commute snapshot evidence: {COMMUTE_AUGUST_SNAPSHOT_EVIDENCE_FILE}")
    require(CTO_ORG_DISPLAY_EVIDENCE_FILE.exists(), f"Missing CTO organizational display evidence: {CTO_ORG_DISPLAY_EVIDENCE_FILE}")
    require(CTO_ORG_ANNUAL_ATTRITION_EVIDENCE_FILE.exists(), f"Missing CTO annual attrition evidence: {CTO_ORG_ANNUAL_ATTRITION_EVIDENCE_FILE}")
    require(QVOICE_WAVE_ATTRITION_EVIDENCE_FILE.exists(), f"Missing QVoice 2026 YTD attrition evidence: {QVOICE_WAVE_ATTRITION_EVIDENCE_FILE}")
    require(QVOICE_YTD_GROUP_ATTRITION_EVIDENCE_FILE.exists(), f"Missing QVoice group YTD attrition evidence: {QVOICE_YTD_GROUP_ATTRITION_EVIDENCE_FILE}")
    require(QVOICE_FAVORABLE_UNFAVORABLE_ATTRITION_EVIDENCE_FILE.exists(), f"Missing QVoice Favorable / No favorable evidence: {QVOICE_FAVORABLE_UNFAVORABLE_ATTRITION_EVIDENCE_FILE}")
    require(QVOICE_OPEN_TEXT_REQUEST_CONCERN_EVIDENCE_FILE.exists(), f"Missing QVoice open-text request/concern evidence: {QVOICE_OPEN_TEXT_REQUEST_CONCERN_EVIDENCE_FILE}")
    require(QVOICE_HEARTBEAT_ATTRITION_EVIDENCE_FILE.exists(), f"Missing QVoice heartbeat post-survey YTD evidence: {QVOICE_HEARTBEAT_ATTRITION_EVIDENCE_FILE}")
    require(QVOICE_RETENTION_THEME_AUGUST_ATTRITION_EVIDENCE_FILE.exists(), f"Missing QVoice retention-theme August trailing-12-month evidence: {QVOICE_RETENTION_THEME_AUGUST_ATTRITION_EVIDENCE_FILE}")
    require(NAV28_39_DIRECT_ANNUAL_ATTRITION_EVIDENCE_FILE.exists(), f"Missing direct-field annual evidence: {NAV28_39_DIRECT_ANNUAL_ATTRITION_EVIDENCE_FILE}")
    require(TIME_IN_JOB_PROFILE_TIME_IN_ROLE_EVIDENCE_FILE.exists(), f"Missing Time in job profile / Time in role evidence: {TIME_IN_JOB_PROFILE_TIME_IN_ROLE_EVIDENCE_FILE}")
    require(NAV28_39_PROMOTION_ANNUAL_ATTRITION_EVIDENCE_FILE.exists(), f"Missing promotion-history annual evidence: {NAV28_39_PROMOTION_ANNUAL_ATTRITION_EVIDENCE_FILE}")
    require(TIME_SINCE_LAST_PROMOTION_COMPARABLE_COHORTS_EVIDENCE_FILE.exists(), f"Missing comparable promotion-cohort evidence: {TIME_SINCE_LAST_PROMOTION_COMPARABLE_COHORTS_EVIDENCE_FILE}")
    require(WITHIN_TEAM_ANNUAL_ATTRITION_EVIDENCE_FILE.exists(), f"Missing within-team annual evidence: {WITHIN_TEAM_ANNUAL_ATTRITION_EVIDENCE_FILE}")
    require(COLOCATION_ANNUAL_ATTRITION_EVIDENCE_FILE.exists(), f"Missing co-location annual evidence: {COLOCATION_ANNUAL_ATTRITION_EVIDENCE_FILE}")
    require(MANAGER_TIMEZONE_AUGUST_TRAILING_12M_EVIDENCE_FILE.exists(), f"Missing manager time-zone August trailing-12-month evidence: {MANAGER_TIMEZONE_AUGUST_TRAILING_12M_EVIDENCE_FILE}")
    require(NAV38_PLUS_AUGUST_ATTRITION_EVIDENCE_FILE.exists(), f"Missing slides 38+ August trailing-12-month evidence: {NAV38_PLUS_AUGUST_ATTRITION_EVIDENCE_FILE}")
    require(LAYERS_FROM_CEO_ANNUAL_ATTRITION_EVIDENCE_FILE.exists(), f"Missing manager-layer annual evidence: {LAYERS_FROM_CEO_ANNUAL_ATTRITION_EVIDENCE_FILE}")
    require(DIRECT_TEAM_SPAN_ANNUAL_ATTRITION_EVIDENCE_FILE.exists(), f"Missing direct-team-span annual evidence: {DIRECT_TEAM_SPAN_ANNUAL_ATTRITION_EVIDENCE_FILE}")
    require(LAYERS_FROM_CEO_0_2_COMPENSATION_GRADE_EVIDENCE_FILE.exists(), f"Missing 0–2 manager-layer compensation-grade evidence: {LAYERS_FROM_CEO_0_2_COMPENSATION_GRADE_EVIDENCE_FILE}")
    require(AUTHORIZATION_FILE.exists(), f"Missing V7 authorization: {AUTHORIZATION_FILE}")
    require(TEMPLATE.exists(), f"Missing required HTML base template: {TEMPLATE}")
    template = TEMPLATE.read_text(encoding="utf-8")
    require('slide-studio-theme' in template and 'class="slide-stage"' in template, "Unexpected base template.")

    evidence = load_evidence()
    promotion_track_evidence = load_promotion_track_evidence()
    promotion_grade_top10_evidence = load_promotion_grade_top10_evidence()
    application_evidence = load_application_evidence()
    application_attrition_evidence = load_application_attrition_evidence()
    gender_label_evidence = load_gender_label_evidence()
    work_arrangement_group_evidence = load_work_arrangement_group_evidence()
    rehire_comparison_august_trailing_12m_evidence = load_rehire_comparison_august_trailing_12m_evidence()
    job_family_august_snapshot_evidence = load_job_family_august_snapshot_evidence()
    job_family_august_trailing_12m_attrition_evidence = load_job_family_august_trailing_12m_attrition_evidence()
    commute_onsite_attrition_evidence = load_commute_onsite_six_month_attrition_evidence()
    commute_all_eligible_attrition_evidence = load_commute_all_eligible_six_month_attrition_evidence()
    commute_august_snapshot_evidence = load_commute_august_snapshot_evidence()
    cto_org_display_evidence = load_cto_org_display_evidence()
    cto_org_annual_attrition_evidence = load_cto_org_annual_attrition_evidence()
    qvoice_ytd_attrition_evidence = load_qvoice_wave_attrition_evidence()
    qvoice_ytd_group_attrition_evidence = load_qvoice_ytd_group_attrition_evidence()
    qvoice_favorable_unfavorable_attrition_evidence = load_qvoice_favorable_unfavorable_attrition_evidence()
    qvoice_open_text_request_concern_evidence = load_qvoice_request_concern_evidence()
    qvoice_heartbeat_attrition_evidence = load_qvoice_heartbeat_attrition_evidence()
    qvoice_retention_theme_august_attrition_evidence = load_qvoice_retention_theme_august_attrition_evidence()
    nav28_39_direct_annual_attrition_evidence = load_nav28_39_direct_annual_attrition_evidence()
    time_in_job_profile_time_in_role_evidence = load_time_in_job_profile_time_in_role_evidence()
    nav28_39_promotion_annual_attrition_evidence = load_nav28_39_promotion_annual_attrition_evidence()
    time_since_last_promotion_comparable_cohorts_evidence = load_time_since_last_promotion_comparable_cohorts_evidence()
    within_team_annual_attrition_evidence = load_within_team_annual_attrition_evidence()
    colocation_annual_attrition_evidence = load_colocation_annual_attrition_evidence()
    manager_timezone_august_trailing_12m_evidence = load_manager_timezone_august_trailing_12m_evidence()
    nav38_plus_august_attrition_evidence = load_nav38_plus_august_attrition_evidence()
    layers_from_ceo_annual_attrition_evidence = load_layers_from_ceo_annual_attrition_evidence()
    layers_from_ceo_0_2_compensation_grade_evidence = load_layers_from_ceo_0_2_compensation_grade_evidence()
    direct_team_span_annual_attrition_evidence = load_direct_team_span_annual_attrition_evidence()
    authorization = json.loads(AUTHORIZATION_FILE.read_text(encoding="utf-8"))
    deck = SOURCE_DECK.read_text(encoding="utf-8")
    deck = replace_slide(deck, build_slide(evidence))
    deck = remove_old_transfer_script(deck)
    deck = update_application_intensity_content(deck, application_attrition_evidence, application_evidence)
    deck = update_application_snapshot_content(deck, application_evidence)
    deck = update_team_attrition_wording(deck)
    deck = restore_internal_gender_labels(deck, gender_label_evidence)
    deck, work_arrangement_group_evidence = replace_work_arrangement_content(deck, work_arrangement_group_evidence)
    deck = replace_cto_org_split_with_annual_attrition(deck, cto_org_display_evidence, cto_org_annual_attrition_evidence)
    deck = replace_job_family_with_august_snapshot(
        deck,
        job_family_august_snapshot_evidence,
        job_family_august_trailing_12m_attrition_evidence,
    )
    deck = replace_rehire_with_historical_august_trailing_12m_labels(deck, rehire_comparison_august_trailing_12m_evidence)
    deck = add_team_post_exit_value_labels(deck)
    deck = enable_internal_aggregate_visibility(deck)
    deck = replace_nav28_39_with_annual_attrition(
        deck,
        nav28_39_direct_annual_attrition_evidence,
        time_in_job_profile_time_in_role_evidence,
        nav28_39_promotion_annual_attrition_evidence,
        within_team_annual_attrition_evidence,
        colocation_annual_attrition_evidence,
        layers_from_ceo_annual_attrition_evidence,
    )
    deck = replace_time_since_last_promotion_with_comparable_cohorts(
        deck,
        time_since_last_promotion_comparable_cohorts_evidence,
    )
    allow_internal_subthreshold = (
        authorization.get("reporting_mode") == "internal_analysis"
        and authorization.get("small_cell_exception", {}).get("allow_subthreshold_aggregate_buckets") is True
    )
    deck = replace_nav38_plus_with_august_attrition(
        deck,
        nav38_plus_august_attrition_evidence,
        allow_internal_subthreshold=allow_internal_subthreshold,
    )
    deck = replace_qvoice_wave_attrition_labels(deck, qvoice_ytd_attrition_evidence)
    deck = replace_qvoice_heartbeat_relative_sign_ytd_attrition(deck, qvoice_heartbeat_attrition_evidence)
    deck = replace_qvoice_comment_tables_with_bar_charts(deck)
    deck = simplify_qvoice_slide_18_language(deck)
    deck = replace_qvoice_request_concern_slide(deck, qvoice_open_text_request_concern_evidence)
    deck = limit_qvoice_intent_display_to_recent_years(deck)
    deck = replace_qvoice_open_text_attrition_pills(deck, qvoice_open_text_request_concern_evidence)
    deck = replace_qvoice_ytd_inline_attrition_labels(deck, qvoice_ytd_group_attrition_evidence)
    deck = clarify_qvoice_comparable_score_bands(deck)
    deck = replace_qvoice_retention_theme_stage(deck, qvoice_retention_theme_august_attrition_evidence)
    deck = replace_qvoice_favorable_unfavorable_stages(deck, qvoice_favorable_unfavorable_attrition_evidence)
    deck = replace_residential_distance_with_manager_timezone_august_trailing_12m(
        deck,
        manager_timezone_august_trailing_12m_evidence,
    )
    deck = replace_commute_distance_with_august_snapshot(
        deck,
        commute_august_snapshot_evidence,
        commute_all_eligible_attrition_evidence,
        commute_onsite_attrition_evidence,
    )
    deck = remove_v6_commute_attrition_script(deck)
    deck = remove_v6_commute_attrition_styles(deck)
    deck = remove_obsolete_prior_experience_slide(deck)
    deck = remove_application_coverage_slide(deck)
    deck = remove_redundant_promotion_history_slide(deck)
    deck = remove_redundant_colocation_slide(deck)
    deck = remove_redundant_manager_support_tail_slides(deck)
    deck = remove_qvoice_participation_coverage_slide(deck)
    deck = insert_layers_from_ceo_0_2_compensation_grade_followup(deck, layers_from_ceo_0_2_compensation_grade_evidence)
    deck = insert_direct_team_span_followup(deck, direct_team_span_annual_attrition_evidence)
    deck = remove_team_attrition_slide(deck)
    deck = replace_intro_slide_with_population_context(deck, layers_from_ceo_annual_attrition_evidence)
    deck = deck.replace("19. Retention concerns in QVoice comments", "19. QVoice comments by theme", 1)
    deck = deck.replace('1. Attrition Variable Playbook', '1. Employee characteristics and attrition', 1)
    deck = deck.replace('<title>Attrition Variable Playbook - V6</title>', '<title>Employee Characteristics and Attrition</title>', 1)
    deck = deck.replace('4. Transfer within the past year', '4. IOS movement events', 1)
    deck = replace_promotion_track_slide(deck, promotion_track_evidence, promotion_grade_top10_evidence)
    marker = (
        '    /* 13. CONTENT-SPECIFIC STYLES — add below this line\n'
        '       ================================================================== */'
    )
    require(marker in deck, "V6 content-style marker is missing.")
    # Insert after the marker's closing delimiter. Replacing only the first
    # line would leave the injected CSS inside this comment and disable it.
    deck = deck.replace(marker, marker + css_block(), 1)
    require('</body>' in deck, "V6 closing body tag is missing.")
    deck = clarify_annual_attrition_windows(deck)

    validate_output(
        deck,
        evidence,
        application_evidence,
        application_attrition_evidence,
        gender_label_evidence,
        work_arrangement_group_evidence,
        job_family_august_snapshot_evidence,
        job_family_august_trailing_12m_attrition_evidence,
        rehire_comparison_august_trailing_12m_evidence,
        cto_org_display_evidence,
        cto_org_annual_attrition_evidence,
        qvoice_ytd_attrition_evidence,
        qvoice_ytd_group_attrition_evidence,
        qvoice_favorable_unfavorable_attrition_evidence,
        qvoice_open_text_request_concern_evidence,
        qvoice_heartbeat_attrition_evidence,
        qvoice_retention_theme_august_attrition_evidence,
        nav28_39_direct_annual_attrition_evidence,
        time_in_job_profile_time_in_role_evidence,
        nav28_39_promotion_annual_attrition_evidence,
        time_since_last_promotion_comparable_cohorts_evidence,
        within_team_annual_attrition_evidence,
        colocation_annual_attrition_evidence,
        manager_timezone_august_trailing_12m_evidence,
        nav38_plus_august_attrition_evidence,
        layers_from_ceo_annual_attrition_evidence,
        layers_from_ceo_0_2_compensation_grade_evidence,
        direct_team_span_annual_attrition_evidence,
    )
    validate_commute_august_snapshot(
        deck,
        commute_august_snapshot_evidence,
        commute_all_eligible_attrition_evidence,
        commute_onsite_attrition_evidence,
    )
    deck = normalize_visible_display_numbers(deck)
    deck = inject_dynamic_number_formatter(deck)
    validate_display_number_policy(deck)
    validate_attrition_window_language(deck)
    OUTPUT_DECK.write_text(deck, encoding="utf-8")

    manifest = {
        "version": 7,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "artifact_classification": "internal_analysis",
        "authorization": {
            "path": str(AUTHORIZATION_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(AUTHORIZATION_FILE),
            "authorization_id": authorization["authorization_id"],
            "audience": authorization["authorized_audience"],
            "small_cell_exception": authorization["small_cell_exception"],
        },
        "language": "English",
        "display_number_policy": {
            "integer_values": "Display without decimal places.",
            "non_integer_values": "Display with at most one decimal place, rounded half-up.",
            "scope": "Visible labels, axes, KPIs, tables, tooltips, and accessibility labels; underlying evidence and calculations retain their original precision.",
            "dynamic_chart_labels": "Normalized at runtime after Plotly renders.",
        },
        "attrition_window_language": {
            "annual_measure": "Every validated annual attrition label explicitly states its 12-month window.",
            "evidence_driven_exceptions": "Six-month, YTD, partial-year, and not-estimable panels retain their specific window or availability language rather than being relabeled as annual.",
        },
        "objective": "Use fiscal-August evidence for the affected V7 visuals: a single Job family snapshot, comparable Rehire August-to-August 12-month attrition, current Commute distributions, and manager-proximity annual attrition. Retain the validated QVoice, workforce, and annual-category visuals elsewhere in the deck.",
        "source_deck": {
            "path": str(SOURCE_DECK.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(SOURCE_DECK),
            "slides_preserved": 48,
        },
        "removed_slide_18": {
            "former_navigation_slide": 18,
            "former_stage_id": "slide-18",
            "title": "Annual voluntary attrition by prior experience",
            "chart_status": "The HTML contained only an empty chart container and related CSS; no chart-rendering script, plotted series, or data payload referenced that container.",
            "reason": "Obsolete visual; removed at requester direction.",
            "navigation_after_removal": "The deck uses contiguous navigation while later technical stage IDs are retained to avoid changing validated builder selectors.",
        },
        "removed_slide_20": {
            "former_navigation_slide": 20,
            "former_stage_id": "slide-22",
            "title": "QVoice participation coverage",
            "reason": "Removed at requester direction; the participation-coverage visual is no longer part of the deck or its builder.",
            "navigation_after_removal": "Intent to Stay items becomes navigation slide 20; later technical stage IDs remain stable for validated builder selectors.",
        },
        "removed_slide_36": {
            "former_navigation_slide": 36,
            "former_stage_id": "slide-41",
            "title": "Co-location with manager",
        "reason": "Redundant with the following assigned office-site proximity proxy; the next slide provides the current distribution and annual attrition view.",
        "navigation_after_removal": "Assigned office-site proximity to manager becomes navigation slide 35; technical stage IDs remain stable for the validated builder selectors.",
    },
    "removed_slide_45": {
        "former_navigation_slide": 45,
        "former_stage_id": "slide-51",
        "title": "Major inflection points",
        "reason": "Removed at requester direction; the exploratory movement proxy is not retained in the presentation.",
            "navigation_after_removal": "The deck ends with Talent index at navigation slide 43.",
    },
    "removed_slide_46": {
        "former_navigation_slide": 46,
        "former_stage_id": "slide-52",
        "title": "ET fields",
        "reason": "Removed at requester direction; the exploratory ET-field coverage visual is not retained in the presentation.",
            "navigation_after_removal": "The deck ends with Talent index at navigation slide 43.",
    },
        "updated_slide": {
            "slide_number": 5,
            "title": "IOS movements represent 11.4% of the active regular workforce in 2026 YTD",
            "visual": "One 2026 YTD horizontal-bar panel showing six IOS movement reasons, workforce share, cohort n, and observed voluntary-attrition pills; the redundant overall bar is removed.",
            "prior_rolling_transfer_visual_removed": True,
        },
        "updated_slide_1": {
            "navigation_slide_number": 1,
            "stage_id": "slide-1",
            "title": "Employee characteristics and attrition",
            "visual": "Plain-language cover explaining that the deck reviews employee characteristics, shows their distributions, and compares voluntary attrition across categories where available.",
            "population": layers_from_ceo_annual_attrition_evidence["population"],
            "baseline_snapshot_date": layers_from_ceo_annual_attrition_evidence["baseline_snapshot_date"],
            "outcome_window": layers_from_ceo_annual_attrition_evidence["outcome_window"],
            "distribution_context": "Most distribution charts show employees active at the August 2026 close; exceptions declare their own snapshot or historical period.",
            "baseline_employee_count": layers_from_ceo_annual_attrition_evidence["metrics"]["display_eligible_count"],
            "voluntary_exit_count": layers_from_ceo_annual_attrition_evidence["metrics"]["baseline_voluntary_exits"],
            "annual_voluntary_attrition_rate_percent": round(
                100
                * layers_from_ceo_annual_attrition_evidence["metrics"]["baseline_voluntary_exits"]
                / layers_from_ceo_annual_attrition_evidence["metrics"]["display_eligible_count"],
                4,
            ),
            "evidence": {
                "path": str(LAYERS_FROM_CEO_ANNUAL_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(LAYERS_FROM_CEO_ANNUAL_ATTRITION_EVIDENCE_FILE),
                "audit_sql": layers_from_ceo_annual_attrition_evidence["provenance"]["audit_sql"],
                "audit_sql_sha256": layers_from_ceo_annual_attrition_evidence["provenance"]["audit_sql_sha256"],
            },
        },
        "updated_slide_29": {
            "navigation_slide_number": 27,
            "stage_id": "slide-34",
            "title": "Promotion and attrition by pay track",
            "replaces": "Promotion history by current compensation grade",
            "visual": "Two comparable panels: six pay-track rows grouped by letter and ten exact compensation-grade rows ranked by current employee count; every row shows current workforce distribution, promotion rate, and trailing-12-month voluntary attrition.",
            "window": promotion_track_evidence["window"],
            "track_rule": "Compensation grades are grouped by their first letter; M10, M20 and M30 appear as M.",
            "top10_grade_rule": promotion_grade_top10_evidence["definition"],
            "top10_grade_rows": 10,
            "top10_grade_evidence": {
                "path": str(PROMOTION_GRADE_TOP10_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(PROMOTION_GRADE_TOP10_EVIDENCE_FILE),
                "query_provenance": promotion_grade_top10_evidence["query_provenance"],
            },
            "outcome": "pass",
        },
        "updated_slide_3": application_trailing_august_slide_3_manifest_entry(),
        "removed_slide_4": {
            "former_navigation_slide": 4,
            "former_stage_id": "slide-4",
            "title": "Applied to a job - trailing six months",
            "reason": "The coverage context was consolidated into slide 3; the detailed coverage distribution and monthly history remain in its aggregate evidence artifact.",
        },
        "removed_slide_7": {
            "former_navigation_slide": 7,
            "former_stage_id": "slide-8",
            "title": "Team attrition",
            "reason": "Removed at requester direction.",
            "navigation_after_removal": "The deck uses contiguous navigation from 1 through 44; later technical stage IDs remain stable for validated builder selectors.",
        },
        "updated_slide_14": {
            "slide_number": 14,
            "title": "Work arrangement",
            "visual": "One horizontal distribution chart for Onsite, Short-Term Remote Work, and all remaining non-onsite values, with six-month voluntary attrition visible in every row.",
            "other_offsite_grouping": "Other stored non-onsite aggregate less Interim Modified – Short-Term Remote Work; calculated from validated employee-snapshot denominators and voluntary-exit numerators, not rounded-rate arithmetic.",
            "other_offsite_rate_percent": round(work_arrangement_group_evidence["other_offsite_rate"], 4),
        },
        "updated_slide_15": {
            "slide_number": 15,
            "title": "Engineering vs. non-engineering",
            "visual": "The documented CTO versus Corp Fxn & BU lower distribution keeps its current snapshot counts and adds a rate pill for twelve-month voluntary attrition from a historical organizational cohort.",
            "current_distribution_snapshot": cto_org_display_evidence["snapshot_date"],
            "annual_attrition_baseline_snapshot": cto_org_annual_attrition_evidence["baseline_snapshot"],
            "annual_attrition_outcome_end": cto_org_annual_attrition_evidence["outcome_window"]["end_inclusive"],
            "time_safety": "Membership is assigned at the historical baseline before exits; the current roster is not used to retroactively classify exited employees.",
            "attrition_pill_encoding": {
                "lowest_rate": "green",
                "highest_rate": "red",
                "intermediate_rate": "blue",
            },
        },
        "updated_slide_16": {
            "slide_number": 16,
            "title": "Rehire",
            "visual": "Three fiscal-August panels (FY2024-FY2026) compare Rehire with the complementary Not a rehire cohort; each bar shows baseline share, cohort count, and strict voluntary attrition over the following 12 months.",
            "historical_fiscal_years": list(REHIRE_VISIBLE_FISCAL_YEARS),
            "baseline_snapshots": sorted({str(row["baseline_snapshot_date"]) for row in rehire_comparison_august_trailing_12m_evidence["rows"]}),
            "outcome_cutoffs": sorted({str(row["outcome_cutoff_date"]) for row in rehire_comparison_august_trailing_12m_evidence["rows"]}),
            "displayed_groups_per_year": ["Rehire", "Not a rehire"],
            "displayed_rows": len(rehire_comparison_august_trailing_12m_evidence["rows"]),
            "attrition_pill_encoding": {
                "lower_rate_within_year": "green",
                "higher_rate_within_year": "red",
            },
            "common_measure": "Strict VOLUNTARY exits / each mutually exclusive active Regular baseline group at each fiscal-August snapshot; each panel uses the complete following 12-month window.",
            "evidence_path": str(REHIRE_COMPARISON_AUGUST_TRAILING_12M_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
        },
        "updated_slide_11": {
            "navigation_slide_number": 9,
            "stage_id": "slide-11",
            "title": "Job family",
            "visual": "One Top-20-plus-Other distribution from the fiscal-August 2026 snapshot with one trailing-12-month voluntary-attrition pill per category; the prior September reorganization comparison is removed.",
            "snapshot_date": job_family_august_snapshot_evidence["snapshot"]["snapshot_date"],
            "attrition_baseline_snapshot": job_family_august_trailing_12m_attrition_evidence["window"]["baseline_snapshot_date"],
            "attrition_outcome_cutoff": job_family_august_trailing_12m_attrition_evidence["window"]["outcome_cutoff_date"],
            "distribution_only": False,
            "trailing_12m_attrition_labels": len(job_family_august_trailing_12m_attrition_evidence["rows"]),
            "attrition_pill_encoding": {
                "lowest_rate": "green",
                "highest_rate": "orange",
                "intermediate_rate": "blue",
            },
        },
        "updated_slide_19": {
            "navigation_slide_number": 17,
            "stage_id": "slide-19",
            "title": "Commute distance",
            "visual": "Five August 2026 distance bands for All eligible and Onsite populations; historical six-month attrition pills remain visibly labeled as a separate measure; no attrition line chart.",
            "snapshot_date": commute_august_snapshot_evidence["snapshot_date"],
            "distribution_evidence": {
                "path": str(COMMUTE_AUGUST_SNAPSHOT_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(COMMUTE_AUGUST_SNAPSHOT_EVIDENCE_FILE),
                "all_eligible_count": commute_august_snapshot_evidence["metrics"]["eligible_employees"],
                "onsite_count": commute_august_snapshot_evidence["metrics"]["onsite"]["eligible_employees"],
            },
            "all_eligible_six_month_attrition_evidence": {
                "path": str(COMMUTE_ALL_ELIGIBLE_SIX_MONTH_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(COMMUTE_ALL_ELIGIBLE_SIX_MONTH_ATTRITION_EVIDENCE_FILE),
                "outcome_contract": commute_all_eligible_attrition_evidence["outcome_contract"],
                "display_band_aggregation": commute_all_eligible_attrition_by_display_band(commute_all_eligible_attrition_evidence),
                "color_encoding": {
                    "lowest_calculable_rate": "green",
                    "highest_calculable_rate": "red",
                    "intermediate_calculable_rate": "blue",
                    "no_calculable_distance": "gray_not_estimable",
                },
            },
            "onsite_six_month_attrition_evidence": {
                "path": str(COMMUTE_ONSITE_SIX_MONTH_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(COMMUTE_ONSITE_SIX_MONTH_ATTRITION_EVIDENCE_FILE),
                "outcome_contract": commute_onsite_attrition_evidence["outcome_contract"],
                "display_band_aggregation": commute_onsite_attrition_by_display_band(commute_onsite_attrition_evidence),
                "color_encoding": {
                    "lowest_calculable_rate": "green",
                    "highest_calculable_rate": "red",
                    "intermediate_calculable_rate": "blue",
                    "no_calculable_distance": "gray_not_estimable",
                },
            },
        },
        "updated_slide_42": {
            "navigation_slide_number": 36,
            "stage_id": "slide-42",
            "title": "Assigned office-site proximity to manager",
            "replaces": "Residential distance from manager",
            "visual": "One full-width distribution chart at the August 2026 close with three assigned-site categories. Each bar has one compact annual voluntary-attrition (12-month) label from the August 2025 baseline cohort; no historical matrix or additional attrition chart is rendered.",
            "population": "Active regular employee-manager pairs with a unique stored office_site at the employee snapshot.",
            "coverage_rule": "Pairs without a reconciled office-catalog time-zone proxy remain a declared aggregate mapping-coverage count and are never assigned to a display category.",
            "proxy_boundary": "No home location, physical presence, commute distance, travel time, or collaboration measure is used.",
            "attrition_window": manager_timezone_august_trailing_12m_evidence["outcome_contract"],
            "attrition_pill_encoding": {
                "lowest_publishable_rate": "green",
                "highest_publishable_rate": "red",
                "intermediate_publishable_rate": "blue",
            },
        },
        "inserted_slide_32": {
            "navigation_slide_number": 31,
            "stage_id": "slide-37-followup",
            "title": "0–2 manager layers: exact compensation-grade distribution",
            "placement": "Immediately after Manager layers to the CEO and before Compensation grade.",
            "visual": "Eighteen horizontal bars on a common maximum-share scale show all exact stored compensation_grade codes with baseline n, cohort share, strict-voluntary exits, and 12-month attrition. Every n<30 row is visibly tagged exploratory.",
            "interpretation": "The distribution is an authorized internal exploratory view for the requester and Julia. Small-cohort rates are descriptive and no grade is asserted to cause attrition.",
            "evidence": {
                "path": str(LAYERS_FROM_CEO_0_2_COMPENSATION_GRADE_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(LAYERS_FROM_CEO_0_2_COMPENSATION_GRADE_EVIDENCE_FILE),
                "audit_sql": layers_from_ceo_0_2_compensation_grade_evidence["provenance"]["audit_sql"],
                "audit_sql_sha256": layers_from_ceo_0_2_compensation_grade_evidence["provenance"]["audit_sql_sha256"],
                "execution_date": layers_from_ceo_0_2_compensation_grade_evidence["provenance"]["execution_date"],
                "cohort": layers_from_ceo_0_2_compensation_grade_evidence["cohort"],
                "rows": layers_from_ceo_0_2_compensation_grade_evidence["rows"],
                "deliverable_mode": layers_from_ceo_0_2_compensation_grade_evidence["deliverable_mode"],
                "authorization": layers_from_ceo_0_2_compensation_grade_evidence["authorization"],
                "exact_category_rule": layers_from_ceo_0_2_compensation_grade_evidence["exact_category_rule"],
            },
        },
        "inserted_slide_33": {
            "navigation_slide_number": 32,
            "stage_id": "slide-37-span-followup",
            "title": "Direct team size (span): distribution and annual attrition",
            "placement": "Immediately after the exact compensation-grade follow-up and before Compensation grade.",
            "visual": "Six horizontal bars on a common maximum-share scale show reconstructed direct-team-size distribution, employee count, number of teams, strict-voluntary exits, and annual attrition. Exact sizes 5 and 20 appear as compact comparison cards; size 20 is visibly exploratory because it represents four teams.",
            "interpretation": "Authorized internal exploratory distribution and attrition association only. Team span is reconstructed from same-snapshot reporting relationships; it does not establish that team size causes attrition.",
            "evidence": {
                "path": str(DIRECT_TEAM_SPAN_ANNUAL_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(DIRECT_TEAM_SPAN_ANNUAL_ATTRITION_EVIDENCE_FILE),
                "audit_sql": direct_team_span_annual_attrition_evidence["provenance"]["audit_sql"],
                "audit_sql_sha256": direct_team_span_annual_attrition_evidence["provenance"]["audit_sql_sha256"],
                "aggregate_result_sha256": direct_team_span_annual_attrition_evidence["provenance"]["aggregate_result_sha256"],
                "execution_date": direct_team_span_annual_attrition_evidence["provenance"]["execution_date"],
                "coverage": direct_team_span_annual_attrition_evidence["coverage"],
                "bands": direct_team_span_annual_attrition_evidence["bands"],
                "exact_span_comparison": direct_team_span_annual_attrition_evidence["exact_span_comparison"],
                "deliverable_mode": direct_team_span_annual_attrition_evidence["deliverable_mode"],
                "authorization": direct_team_span_annual_attrition_evidence["authorization"],
            },
        },
        "updated_slides_27_39": {
            "navigation_slide_numbers_after_removal": list(range(24, 36)),
            "navigation_to_stage": {
                "24": "slide-29: Time at detailed level and time in role",
                "25": "slide-31: Company tenure",
                "26": "slide-32: Time since last promotion",
                "27": "slide-34: Promotion and attrition by pay track",
                "28": "slide-35: Level",
                "29": "slide-36: Level grouped by grade family",
                "30": "slide-37: Manager layers to the CEO",
                "31": "slide-37-followup: 0–2 layers: exact compensation grades",
                "32": "slide-37-span-followup: Direct team size (span)",
                "33": "slide-38: Compensation grade",
                "34": "slide-39: Comp ratio",
                "35": "slide-40: Within-team compensation range",
            },
            "annual_definition": "Category membership is assigned at the historical employee snapshot; annual attrition is strict VOLUNTARY termination in (snapshot_date, snapshot_date + 12 months].",
            "publication_rule": "At least 30 baseline employees per displayed category; manager-layer rates are calculated from the same cohort even when the event numerator is below 30, and only sub-30 employee cohorts are rendered gray.",
            "color_encoding": {
                "lowest_publishable_rate": "green",
                "highest_publishable_rate": "red",
                "intermediate_publishable_rate": "blue",
                "unavailable_or_incomplete": "gray_not_estimable",
            },
            "compensation_grade_color_encoding": {
                "low": "green: lower third of publishable compensation-grade rates",
                "middle": "blue: middle third of publishable compensation-grade rates",
                "high": "orange: upper third of publishable compensation-grade rates",
            },
            "exceptions": {
                "detailed_level_tenure": "Published from levelentrydate adjusted by max_hire_rehire_date; time_in_job_profile_start_date is not substituted.",
                "manager_layers_to_ceo": "Published from a baseline reconstructed manager-chain depth to the unique no-manager CEO-title root; strict voluntary attrition follows the same baseline depth cohort.",
                "within_team_compensation": "Pills report annual team attrition among historical direct reports assigned to managers in the displayed review state, not manager attrition.",
            },
            "direct_field_evidence": {
                "path": str(NAV28_39_DIRECT_ANNUAL_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(NAV28_39_DIRECT_ANNUAL_ATTRITION_EVIDENCE_FILE),
                "metrics": sorted({str(row["metric"]) for row in nav28_39_direct_annual_attrition_evidence["rows"]}),
            },
            "tenure_evidence": {
                "path": str(TIME_IN_JOB_PROFILE_TIME_IN_ROLE_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(TIME_IN_JOB_PROFILE_TIME_IN_ROLE_EVIDENCE_FILE),
                "metrics": sorted({str(row["metric"]) for row in time_in_job_profile_time_in_role_evidence["annual_rows"]}),
                "outcome_window": time_in_job_profile_time_in_role_evidence["display_contract"]["outcome_window"],
            },
            "promotion_evidence": {
                "path": str(TIME_SINCE_LAST_PROMOTION_COMPARABLE_COHORTS_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(TIME_SINCE_LAST_PROMOTION_COMPARABLE_COHORTS_EVIDENCE_FILE),
                "deliverable_mode": time_since_last_promotion_comparable_cohorts_evidence["deliverable_mode"],
                "baseline_snapshot": time_since_last_promotion_comparable_cohorts_evidence["outcome_contract"]["baseline_snapshot_date"],
                "outcome_window": time_since_last_promotion_comparable_cohorts_evidence["outcome_contract"]["outcome_window"],
                "cohort_totals": time_since_last_promotion_comparable_cohorts_evidence["cohort_totals"],
                "declared_exclusions": time_since_last_promotion_comparable_cohorts_evidence["declared_exclusions"],
                "publication_rule": "n >= 30 by default; the approved V7 internal-analysis exception retains a smaller aggregate band with count and descriptive rate, visibly marked as not a stable estimate.",
                "small_cohort_display": time_since_last_promotion_comparable_cohorts_evidence["validation"]["internal_exploratory_small_cohort_rows"],
                "authorization": time_since_last_promotion_comparable_cohorts_evidence["authorization"],
            },
            "manager_layers_evidence": {
                "path": str(LAYERS_FROM_CEO_ANNUAL_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(LAYERS_FROM_CEO_ANNUAL_ATTRITION_EVIDENCE_FILE),
                "audit_sql": layers_from_ceo_annual_attrition_evidence["provenance"]["audit_sql"],
                "audit_sql_sha256": layers_from_ceo_annual_attrition_evidence["provenance"]["audit_sql_sha256"],
                "baseline_snapshot_date": layers_from_ceo_annual_attrition_evidence["baseline_snapshot_date"],
                "outcome_window": layers_from_ceo_annual_attrition_evidence["outcome_window"],
                "baseline_employee_count": layers_from_ceo_annual_attrition_evidence["metrics"]["display_eligible_count"],
                "baseline_voluntary_exits": layers_from_ceo_annual_attrition_evidence["metrics"]["baseline_voluntary_exits"],
                "published_bands": len(layers_from_ceo_annual_attrition_evidence["distribution"]),
            },
            "manager_layers_0_2_compensation_grade_followup_evidence": {
                "path": str(LAYERS_FROM_CEO_0_2_COMPENSATION_GRADE_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(LAYERS_FROM_CEO_0_2_COMPENSATION_GRADE_EVIDENCE_FILE),
                "audit_sql": layers_from_ceo_0_2_compensation_grade_evidence["provenance"]["audit_sql"],
                "audit_sql_sha256": layers_from_ceo_0_2_compensation_grade_evidence["provenance"]["audit_sql_sha256"],
                "baseline_snapshot_date": layers_from_ceo_0_2_compensation_grade_evidence["baseline_snapshot_date"],
                "outcome_window": layers_from_ceo_0_2_compensation_grade_evidence["outcome_window"],
                "cohort": layers_from_ceo_0_2_compensation_grade_evidence["cohort"],
                "display_rows": layers_from_ceo_0_2_compensation_grade_evidence["rows"],
                "deliverable_mode": layers_from_ceo_0_2_compensation_grade_evidence["deliverable_mode"],
                "authorization": layers_from_ceo_0_2_compensation_grade_evidence["authorization"],
                "exact_category_rule": layers_from_ceo_0_2_compensation_grade_evidence["exact_category_rule"],
                "interpretation": "Authorized internal exploratory exact-grade composition and attrition association only; small-cohort rates are descriptive and compensation grade is not asserted to cause attrition.",
            },
            "direct_team_span_followup_evidence": {
                "path": str(DIRECT_TEAM_SPAN_ANNUAL_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(DIRECT_TEAM_SPAN_ANNUAL_ATTRITION_EVIDENCE_FILE),
                "audit_sql": direct_team_span_annual_attrition_evidence["provenance"]["audit_sql"],
                "audit_sql_sha256": direct_team_span_annual_attrition_evidence["provenance"]["audit_sql_sha256"],
                "baseline_snapshot_date": direct_team_span_annual_attrition_evidence["baseline_snapshot_date"],
                "outcome_window": direct_team_span_annual_attrition_evidence["outcome_window"],
                "coverage": direct_team_span_annual_attrition_evidence["coverage"],
                "bands": direct_team_span_annual_attrition_evidence["bands"],
                "exact_span_comparison": direct_team_span_annual_attrition_evidence["exact_span_comparison"],
                "deliverable_mode": direct_team_span_annual_attrition_evidence["deliverable_mode"],
                "authorization": direct_team_span_annual_attrition_evidence["authorization"],
                "interpretation": "Authorized internal exploratory distribution and attrition association only; the exact size 20 comparison is descriptive because it has four teams.",
            },
            "within_team_evidence": {
                "path": str(WITHIN_TEAM_ANNUAL_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(WITHIN_TEAM_ANNUAL_ATTRITION_EVIDENCE_FILE),
            },
            "colocation_evidence": {
                "path": str(COLOCATION_ANNUAL_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(COLOCATION_ANNUAL_ATTRITION_EVIDENCE_FILE),
                "outcome_contract": colocation_annual_attrition_evidence["outcome_contract"],
                "displayed_trailing_years": list(COLOCATION_DISPLAY_YEARS),
                "omitted_years_for_concise_view": ["2020", "2021", "2022"],
            },
        },
        "updated_slides_38_plus": {
            "navigation_slide_numbers": list(range(37, 45)),
            "stage_ids": list(range(43, 51)),
            "visual": "Slides 37-44 retain their distributions and add annual voluntary-attrition labels calculated from the same August 2025 baseline category population.",
            "baseline_snapshot": nav38_plus_august_attrition_evidence["baseline_snapshot_date"],
            "outcome_window": nav38_plus_august_attrition_evidence["outcome_window"],
            "population": nav38_plus_august_attrition_evidence["population"],
            "definition": nav38_plus_august_attrition_evidence["definition"],
            "publication_rule": nav38_plus_august_attrition_evidence["publication_rule"],
            "metric_map": {
                metric: stage_id
                for metric, stage_id in nav38_plus_august_attrition_evidence["metric_map"].items()
                if metric not in {"major_inflection_proxy", "et_field_presence"}
            },
            "evidence": {
                "path": str(NAV38_PLUS_AUGUST_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(NAV38_PLUS_AUGUST_ATTRITION_EVIDENCE_FILE),
                "queries": {
                    name: {
                        "path": payload["query_path"],
                        "sha256": payload["query_sha256"],
                        "result_sha256": payload["result_sha256"],
                    }
                    for name, payload in nav38_plus_august_attrition_evidence["queries"].items()
                },
            },
            "denominator_caveat": "Manager-ratio, recent-team-exit, and above-average-team-turnover labels describe annual attrition of baseline direct reports assigned to each displayed category; they are not manager attrition rates.",
            "exceptions": {
                "manager_leaving_exposed": nav38_plus_august_attrition_evidence["unavailable_features"]["manager_leaving_exposed"],
                "talent_index": nav38_plus_august_attrition_evidence["unavailable_features"]["talent_index"],
            },
            "internal_analysis_small_cell_visibility": {
                "enabled": allow_internal_subthreshold,
                "audience": authorization["authorized_audience"],
                "manager_leaving_exposed": {
                    "baseline_employee_count": 4,
                    "voluntary_exits": 1,
                    "annual_attrition_rate_percent": 25.0,
                    "display_asterisk": True,
                    "publication_status_remains": "not_estimable_below_30_baseline_employees",
                    "interpretation": "Descriptive internal-analysis value only; not a stable estimate.",
                },
            },
            "outcome": nav38_plus_august_attrition_evidence["outcome"],
        },
        "updated_qvoice_slides": {
            "stage_ids": [20, 21, 23, 24, 25, 26, 27],
            "navigation_slide_numbers_after_removal": list(range(17, 24)),
            "visual": "Slide 17 permanently uses three mutually exclusive open-text groups per QVoice wave: remote/hybrid/onsite comment, other written comment, and no written comment. Each stacked bar sums to 100% of QVoice participants with a usable key, and each group has its own voluntary-attrition pill. Non-exclusive latest-wave subthemes remain on the right. Slides 18-23 retain their source distributions and their validated QVoice-specific treatments.",
            "layout_refresh": {
                "reference": "Permanent integration of the prior request/concern visual into the full V7 builder.",
                "data_change": True,
                "preserved": "The aggregate-only QVoice open-text evidence and its cohort-specific attrition calculations are rendered directly by the main build flow.",
            },
            "slide_20_request_concern_evidence": {
                "path": str(QVOICE_OPEN_TEXT_REQUEST_CONCERN_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(QVOICE_OPEN_TEXT_REQUEST_CONCERN_EVIDENCE_FILE),
                "outcome": qvoice_open_text_request_concern_evidence["outcome"],
                "outcome_contract": qvoice_open_text_request_concern_evidence["outcome_contract"],
                "waves": [str(row["wave"]) for row in qvoice_open_text_request_concern_evidence["waves"]],
                "three_group_composition_bars": len(qvoice_open_text_request_concern_evidence["waves"]),
                "three_group_attrition_cards": sum(len(row["composition"]["groups"]) for row in qvoice_open_text_request_concern_evidence["waves"]),
                "display_precision": "Counts are integers. Visible composition and attrition percentages use one decimal; largest-remainder allocation ensures each displayed composition bar sums to 100.0%.",
                "latest_survey_subthemes": len(qvoice_open_text_request_concern_evidence["latest_survey_subthemes"]),
            },
            "color_encoding": {
                "request_or_concern_share": "blue",
                "all_other_commenters_share": "gray",
                "no_comment_share": "light blue",
                "group_attrition": "direct percentage labels; no causal interpretation",
            },
            "privacy": "Aggregate-only internal analysis. No employee identifiers, employee rows, raw comments, or individual QVoice responses are rendered.",
        },
        "evidence": {
            "path": str(EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(EVIDENCE_FILE),
            "query": evidence["query"],
            "reporting_mode": evidence["reporting_mode"],
            "rows": len(evidence["rows"]),
            "cutoffs": evidence["cutoffs"],
            "minimum_shared_cohort": evidence["privacy"]["minimum_shared_cohort"],
            "suppression": "None for aggregate cells under the named internal_analysis authorization",
            "subthreshold_aggregate_buckets_visible": True,
        },
        "application_snapshot_evidence": {
            "path": str(APPLICATION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(APPLICATION_EVIDENCE_FILE),
            "reporting_mode": application_evidence["reporting_mode"],
            "latest_snapshot": application_evidence["latest_snapshot"],
            "trend_points": len(application_evidence["trend"]),
            "buckets_per_point": 4,
        },
        "application_attrition_evidence": {
            "path": str(APPLICATION_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(APPLICATION_ATTRITION_EVIDENCE_FILE),
            "reporting_mode": application_attrition_evidence["reporting_mode"],
            "artifact": application_attrition_evidence["artifact"],
            "main_query": application_attrition_evidence["provenance"]["main_query"],
            "rows": len(application_attrition_evidence["rows"]),
            "visible_slide_cutoffs": application_attrition_evidence["visible_slide_cutoffs"],
            "evidence_only_cutoffs": application_attrition_evidence["evidence_only_cutoffs"],
            "subthreshold_aggregate_buckets": application_attrition_evidence["validation"]["metrics"]["subthreshold_aggregate_buckets"],
        },
        "work_arrangement_attrition_evidence": {
            "path": str(SIX_MONTH_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(SIX_MONTH_ATTRITION_EVIDENCE_FILE),
            "deliverable_mode": "internal_analysis",
            "other_offsite_employee_snapshots": int(work_arrangement_group_evidence["other_offsite_snapshots"]),
            "other_offsite_voluntary_exits": int(work_arrangement_group_evidence["other_offsite_exits"]),
            "other_offsite_attrition_rate_percent": round(work_arrangement_group_evidence["other_offsite_rate"], 4),
        },
        "job_family_august_snapshot_evidence": {
            "path": str(JOB_FAMILY_AUGUST_SNAPSHOT_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(JOB_FAMILY_AUGUST_SNAPSHOT_EVIDENCE_FILE),
            "query": job_family_august_snapshot_evidence["query"],
            "query_sha256": job_family_august_snapshot_evidence["query_sha256"],
            "snapshot": job_family_august_snapshot_evidence["snapshot"],
        },
        "job_family_august_trailing_12m_attrition_evidence": {
            "path": str(JOB_FAMILY_AUGUST_TRAILING_12M_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(JOB_FAMILY_AUGUST_TRAILING_12M_ATTRITION_EVIDENCE_FILE),
            "query": job_family_august_trailing_12m_attrition_evidence["query"],
            "query_sha256": job_family_august_trailing_12m_attrition_evidence["query_sha256"],
            "window": job_family_august_trailing_12m_attrition_evidence["window"],
            "summary": job_family_august_trailing_12m_attrition_evidence["summary"],
            "rows": job_family_august_trailing_12m_attrition_evidence["rows"],
            "outcome": job_family_august_trailing_12m_attrition_evidence["outcome"],
        },
        "rehire_comparison_august_trailing_12m_evidence": {
            "path": str(REHIRE_COMPARISON_AUGUST_TRAILING_12M_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(REHIRE_COMPARISON_AUGUST_TRAILING_12M_EVIDENCE_FILE),
            "query": rehire_comparison_august_trailing_12m_evidence["query"],
            "query_sha256": rehire_comparison_august_trailing_12m_evidence["query_sha256"],
            "fiscal_years": list(REHIRE_VISIBLE_FISCAL_YEARS),
            "rows": rehire_comparison_august_trailing_12m_evidence["rows"],
            "outcome": rehire_comparison_august_trailing_12m_evidence["outcome"],
        },
        "cto_org_annual_attrition_evidence": {
            "display_distribution_path": str(CTO_ORG_DISPLAY_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "display_distribution_sha256": digest(CTO_ORG_DISPLAY_EVIDENCE_FILE),
            "path": str(CTO_ORG_ANNUAL_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(CTO_ORG_ANNUAL_ATTRITION_EVIDENCE_FILE),
            "query": cto_org_annual_attrition_evidence["provenance"]["query_path"],
            "query_sha256": cto_org_annual_attrition_evidence["provenance"]["sql_sha256"],
            "baseline_snapshot": cto_org_annual_attrition_evidence["baseline_snapshot"],
            "outcome_window": cto_org_annual_attrition_evidence["outcome_window"],
            "rows": cto_org_annual_attrition_evidence["rows"],
            "outcome": cto_org_annual_attrition_evidence["outcome"],
        },
        "manager_timezone_august_trailing_12m_evidence": {
            "path": str(MANAGER_TIMEZONE_AUGUST_TRAILING_12M_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(MANAGER_TIMEZONE_AUGUST_TRAILING_12M_EVIDENCE_FILE),
            "query": manager_timezone_august_trailing_12m_evidence["query"],
            "query_sha256": manager_timezone_august_trailing_12m_evidence["query_sha256"],
            "outcome_contract": manager_timezone_august_trailing_12m_evidence["outcome_contract"],
            "coverage": manager_timezone_august_trailing_12m_evidence["diagnostics"],
            "outcome": manager_timezone_august_trailing_12m_evidence["outcome"],
        },
        "gender_label_disclosure": {
            "path": str(GENDER_LABEL_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(GENDER_LABEL_EVIDENCE_FILE),
            "query": gender_label_evidence["query"],
            "display_mapping": gender_label_evidence["display_mapping"],
            "aggregate_rows": len(gender_label_evidence["rows"]),
            "outcome": gender_label_evidence["outcome"],
        },
        "qvoice_wave_attrition_evidence": {
            "path": str(QVOICE_WAVE_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(QVOICE_WAVE_ATTRITION_EVIDENCE_FILE),
            "window_audit": qvoice_ytd_attrition_evidence["provenance"]["window_audit"],
            "jan_2026_ytd_evidence": qvoice_ytd_attrition_evidence["provenance"]["jan_2026_ytd_evidence"],
            "outcome_contract": qvoice_ytd_attrition_evidence["outcome_contract"],
            "outcome": qvoice_ytd_attrition_evidence["outcome"],
        },
        "qvoice_ytd_group_attrition_evidence": {
            "path": str(QVOICE_YTD_GROUP_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(QVOICE_YTD_GROUP_ATTRITION_EVIDENCE_FILE),
            "outcome": qvoice_ytd_group_attrition_evidence["outcome"],
            "validation_outcome": qvoice_ytd_group_attrition_evidence["validation"]["outcome"],
            "minimum_shared_cohort": qvoice_ytd_group_attrition_evidence["minimum_shared_cohort"],
            "outcome_contract": qvoice_ytd_group_attrition_evidence["outcome_contract"],
            "stages": [20, 25, 27],
            "inline_attrition_panels_visible": 2,
            "inline_attrition_pills_visible": 11,
            "open_text_attrition_pills_visible": 8,
            "region_attrition_pills_visible": 12,
        },
        "qvoice_favorable_unfavorable_attrition_evidence": {
            "path": str(QVOICE_FAVORABLE_UNFAVORABLE_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(QVOICE_FAVORABLE_UNFAVORABLE_ATTRITION_EVIDENCE_FILE),
            "artifact": qvoice_favorable_unfavorable_attrition_evidence["artifact"],
            "outcome": qvoice_favorable_unfavorable_attrition_evidence["outcome"],
            "minimum_shared_cohort": qvoice_favorable_unfavorable_attrition_evidence["minimum_shared_cohort"],
            "outcome_contract": qvoice_favorable_unfavorable_attrition_evidence["outcome_contract"],
            "visual": {
                "navigation_slides": [19, 20],
                "stage_ids": [23, 24],
                "years": [2024, 2025, 2026],
                "driver_bars_per_year": 2,
                "component_bars_per_year": {"intent_to_stay": 4, "career_goals": 2},
                "response_bars_visible": 30,
                "attrition_labels_visible": 30,
                "component_blocks_per_slide": {"intent_to_stay": 2, "career_goals": 1},
                "career_goals_has_one_source_question": True,
                "yearly_share_denominator": "Matched linked QVoice response cohort for each driver or component block; each pair sums to 100%.",
            },
        },
        "qvoice_heartbeat_attrition_evidence": {
            "path": str(QVOICE_HEARTBEAT_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(QVOICE_HEARTBEAT_ATTRITION_EVIDENCE_FILE),
            "window_audit": qvoice_heartbeat_attrition_evidence["provenance"]["window_audit"],
            "outcome_contract": qvoice_heartbeat_attrition_evidence["outcome_contract"],
            "ranking_panels": len(qvoice_heartbeat_attrition_evidence["slide"]["panels"]),
            "displayed_questions": sum(len(panel["questions"]) for panel in qvoice_heartbeat_attrition_evidence["slide"]["panels"]),
            "displayed_segments": sum(
                len(question["segments"])
                for panel in qvoice_heartbeat_attrition_evidence["slide"]["panels"]
                for question in panel["questions"]
            ),
            "outcome": qvoice_heartbeat_attrition_evidence["outcome"],
        },
        "qvoice_retention_theme_august_attrition_evidence": {
            "path": str(QVOICE_RETENTION_THEME_AUGUST_ATTRITION_EVIDENCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(QVOICE_RETENTION_THEME_AUGUST_ATTRITION_EVIDENCE_FILE),
            "window_audit": qvoice_retention_theme_august_attrition_evidence["provenance"]["window_audit"],
            "outcome_contract": qvoice_retention_theme_august_attrition_evidence["outcome_contract"],
            "rows": qvoice_retention_theme_august_attrition_evidence["rows"],
            "outcome": qvoice_retention_theme_august_attrition_evidence["outcome"],
        },
        "definition": {
            "cohort": "First eligible IOS event per employee, reason, and calendar year; Total deduplicates employees across reasons.",
            "eligibility": "Active regular employee at the latest monthly snapshot no more than 45 days before the event.",
            "attrition": "Strict Voluntary termination after the first event through the same-year August cutoff; observed YTD, not a 12-month follow-up.",
            "overlap": "Reason rows may overlap and do not sum to Total.",
        },
        "validation": {
            "slides": 44,
            "navigation_items": 44,
            "obsolete_prior_experience_slide_removed": True,
            "qvoice_participation_coverage_slide_removed": True,
            "redundant_colocation_slide_removed": True,
            "team_attrition_slide_removed": True,
            "major_inflection_slide_removed": True,
            "et_fields_slide_removed": True,
            "themes": 4,
            "frozen_group_year_rows": 21,
            "rendered_group_year_rows": 6,
            "ios_total_bar_removed": True,
            "ios_reason_bars_visible": 6,
            "obsolete_transfer_containers_removed": True,
            "hidden_aggregate_rows_removed": True,
            "truncation_notes_removed": True,
            "application_trend_buckets_visible": 48,
            "application_attrition_cells_visible": 8,
            "application_attrition_rates_visible": 8,
            "application_attrition_observed_trailing_12m_pills_visible": 8,
            "application_attrition_colored_pills_visible": 8,
            "application_slide_3_tables_visible": 0,
            "application_slide_3_recent_august_panels": 2,
            "application_slide_3_recent_august_rows": 8,
            "application_slide_3_historical_years_visible": 0,
            "application_slide_3_change_percentage_points": 8.82,
            "application_slide_3_subthreshold_attrition_pills_flagged": 4,
            "application_coverage_context_visible": 1,
            "application_coverage_percent_visible": 9.7596,
            "application_slide_4_removed": True,
            "work_arrangement_chart_cards": 1,
            "work_arrangement_groups_with_attrition": 3,
            "cto_org_groups_with_annual_attrition": 2,
            "cto_org_attrition_time_windows_visible": True,
            "rehire_comparison_year_panels_visible": 3,
            "rehire_comparison_groups_visible": 6,
            "rehire_comparison_attrition_labels_visible": 6,
            "rehire_comparison_fiscal_years": list(REHIRE_VISIBLE_FISCAL_YEARS),
            "rehire_comparison_baseline_snapshots": sorted({str(row["baseline_snapshot_date"]) for row in rehire_comparison_august_trailing_12m_evidence["rows"]}),
            "rehire_comparison_outcome_cutoffs": sorted({str(row["outcome_cutoff_date"]) for row in rehire_comparison_august_trailing_12m_evidence["rows"]}),
            "job_family_august_snapshot_categories": 21,
            "job_family_august_trailing_12m_attrition_labels": len(job_family_august_trailing_12m_attrition_evidence["rows"]),
            "job_family_august_trailing_12m_attrition_window": job_family_august_trailing_12m_attrition_evidence["window"]["outcome_interval"],
            "commute_august_snapshot_distance_rows": 5,
            "validated_protected_category_labels_visible": True,
            "qvoice_open_text_three_group_composition_bars_visible": len(qvoice_open_text_request_concern_evidence["waves"]),
            "qvoice_open_text_three_group_attrition_cards_visible": sum(len(row["composition"]["groups"]) for row in qvoice_open_text_request_concern_evidence["waves"]),
            "qvoice_open_text_latest_subthemes_visible": len(qvoice_open_text_request_concern_evidence["latest_survey_subthemes"]),
            "qvoice_open_text_attrition_pills_visible": sum(len(row["groups"]) + 1 for row in qvoice_open_text_request_concern_evidence["waves"]),
            "qvoice_inline_attrition_panels_visible": 2,
            "qvoice_inline_attrition_pills_visible": 11,
            "qvoice_comparable_score_band_labels_explicit": True,
            "qvoice_comparable_score_formula_note_visible": True,
            "qvoice_retention_theme_rows_visible": len(qvoice_retention_theme_august_attrition_evidence["rows"]),
            "qvoice_retention_theme_attrition_window": qvoice_retention_theme_august_attrition_evidence["outcome_contract"]["window"],
            "qvoice_favorable_unfavorable_response_bars_visible": 30,
            "qvoice_favorable_unfavorable_attrition_labels_visible": 30,
            "qvoice_heartbeat_relative_sign_bars_visible": sum(
                len(question["segments"])
                for panel in qvoice_heartbeat_attrition_evidence["slide"]["panels"]
                for question in panel["questions"]
            ),
            "qvoice_heartbeat_attrition_pills_visible": sum(
                len(question["segments"])
                for panel in qvoice_heartbeat_attrition_evidence["slide"]["panels"]
                for question in panel["questions"]
            ),
            "qvoice_heartbeat_reference_attrition_visible": 0,
            "qvoice_heartbeat_attrition_window": qvoice_heartbeat_attrition_evidence["outcome_contract"]["window"],
            "qvoice_legacy_right_attrition_panels_removed": 8,
            "qvoice_rate_rails_visible": 0,
            "qvoice_intent_displayed_years": list(QVOICE_INTENT_DISPLAY_YEARS),
            "career_and_compensation_annual_attrition_slides": 14,
            "nav28_39_annual_attrition_pills": 266,
            "nav28_39_no_six_month_labels": True,
            "manager_timezone_distribution_categories": 3,
            "manager_timezone_august_trailing_12m_attrition_labels": 3,
            "manager_timezone_historical_matrix_removed": True,
            "manager_timezone_unmapped_pairs_declared": True,
            "slides_38_plus_annual_attrition_labels": 45,
            "slides_38_plus_stage_ids": list(range(43, 51)),
            "slides_38_plus_manager_leaving_exposed_not_estimable": True,
            "slides_38_plus_manager_leaving_exposed_internal_descriptive_rate_visible": True,
            "slides_38_plus_manager_leaving_exposed_rate_asterisked": True,
            "slides_38_plus_talent_index_not_estimable": True,
            "ceo_layers_annual_attrition_unavailable": False,
            "ceo_layers_annual_attrition_labels_visible": len(layers_from_ceo_annual_attrition_evidence["distribution"]),
            "ceo_layers_0_2_compensation_grade_followup_rows_visible": len(layers_from_ceo_0_2_compensation_grade_evidence["rows"]),
            "ceo_layers_0_2_compensation_grade_followup_cohort": layers_from_ceo_0_2_compensation_grade_evidence["cohort"],
            "ceo_layers_0_2_exact_grade_cells_visible": len(layers_from_ceo_0_2_compensation_grade_evidence["rows"]),
            "ceo_layers_0_2_exploratory_n_lt_30_cells_visible": sum(
                int(row["employee_count"]) < 30
                for row in layers_from_ceo_0_2_compensation_grade_evidence["rows"]
            ),
            "direct_team_span_bands_visible": len(direct_team_span_annual_attrition_evidence["bands"]),
            "direct_team_span_eligible_employee_count": direct_team_span_annual_attrition_evidence["coverage"]["eligible_employee_count"],
            "direct_team_span_coverage_exclusion_count": direct_team_span_annual_attrition_evidence["coverage"]["unresolvable_manager_exclusion_count"],
            "direct_team_span_baseline_voluntary_exits": direct_team_span_annual_attrition_evidence["validation"]["metrics"]["baseline_voluntary_exits"],
            "direct_team_span_exact_five": direct_team_span_annual_attrition_evidence["exact_span_comparison"]["five_direct_reports"],
            "direct_team_span_exact_twenty": direct_team_span_annual_attrition_evidence["exact_span_comparison"]["twenty_direct_reports"],
            "subthreshold_aggregate_buckets_visible": True,
            "aggregate_only": True,
            "outcome": "pass",
        },
        "output_deck": {
            "path": str(OUTPUT_DECK.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(OUTPUT_DECK),
        },
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT_DECK)
    print(MANIFEST_FILE)


if __name__ == "__main__":
    if "--qvoice-slide-18-plain-language" in sys.argv:
        refresh_qvoice_slide_18_language_only()
    elif "--qvoice-intent-display-window-only" in sys.argv:
        refresh_qvoice_intent_display_window_only()
    elif "--manager-timezone-ytd-only" in sys.argv:
        refresh_manager_timezone_ytd_slide_only()
    elif "--colocation-trailing-12m-only" in sys.argv:
        refresh_colocation_trailing_12m_slide_only()
    elif "--rehire-fy2024plus-only" in sys.argv:
        refresh_rehire_slide_only()
    elif "--application-consolidate-slides" in sys.argv:
        consolidate_application_slides()
    elif "--application-slide-3-only" in sys.argv:
        refresh_application_slide_3_only()
    elif "--application-visuals-only" in sys.argv:
        refresh_application_visuals_only()
    else:
        main()
