"""Create the V3 attrition-distribution deck without modifying V2.

V3 deliberately keeps the validated V2 distribution cards and adds only the
analogous historical voluntary-attrition view where the source, semantic
definition and time-safe join permit it.  It uses frozen aggregate evidence
only; no employee rows, IDs, exact pay values or free text are rendered.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "distribution"
EVIDENCE_DIR = OUT / "json"
V2 = OUT / "attrition-43-variable-distributions-v2.html"
V2_MANIFEST = EVIDENCE_DIR / "attrition-43-variable-distributions-v2-manifest.json"
TEMPLATE = Path(r"C:\Users\fcarranz\.codex\skills\html-slide-generator\templates\fullscreen\base-fullscreen.html")
EVIDENCE = EVIDENCE_DIR / "attrition-43-variable-distributions-v3.six-month-attrition-evidence-20260914.json"
QUEUE = ROOT / "config" / "attrition_distribution_v3_queue.yaml"
TARGET = OUT / "attrition-43-variable-distributions-v3.html"
MANIFEST = EVIDENCE_DIR / "attrition-43-variable-distributions-v3-manifest.json"

MINIMUM_COHORT = 30
MATURE_FIRST_SNAPSHOT = "2024-03-24"
MATURE_LAST_SNAPSHOT = "2026-02-22"


@dataclass
class Slide:
    label: str
    html_text: str
    section: str
    kind: str


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def normal(value: object) -> str:
    text = html.unescape(str(value)).replace("Â", "")
    text = text.replace("–", "-").replace("—", "-").replace("−", "-").replace("·", " ")
    text = re.sub(r"^\s*\d+\s*-\s*", "", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9+<>=%]+", "", text.lower())


def number(value: Any) -> float:
    return float(value)


def integer(value: Any) -> int:
    return int(value)


def find_matching_div(text: str, open_start: int) -> int:
    """Return the first character after the div that starts at open_start."""
    token_pattern = re.compile(r"</?div\b[^>]*>", re.IGNORECASE)
    depth = 0
    for token in token_pattern.finditer(text, open_start):
        value = token.group(0)
        if value.lower().startswith("</"):
            depth -= 1
            if depth == 0:
                return token.end()
        elif not value.rstrip().endswith("/>"):
            depth += 1
    raise ValueError("No se encontró el cierre del contenedor div.")


def find_matching_tag(text: str, tag: str, open_start: int) -> int:
    """Return the character after the matching tag opened at open_start."""
    token_pattern = re.compile(rf"</?{re.escape(tag)}\b[^>]*>", re.IGNORECASE)
    depth = 0
    for token in token_pattern.finditer(text, open_start):
        value = token.group(0)
        if value.lower().startswith("</"):
            depth -= 1
            if depth == 0:
                return token.end()
        elif not value.rstrip().endswith("/>"):
            depth += 1
    raise ValueError(f"Matching closing tag not found: {tag}")


def stage_title(stage: str) -> str:
    match = re.search(r'<h2 class="slide-title-text">(.*?)</h2>', stage, flags=re.S)
    if not match:
        raise ValueError("Una lámina no tiene título visible.")
    return html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()


def extract_stages(document: str) -> tuple[str, list[str], str]:
    first_stage = document.find('<div class="slide-stage"')
    nav_start = document.find('<div class="nav-ctrl" id="slide-nav">')
    if first_stage < 0 or nav_start < 0:
        raise ValueError("El deck V2 no contiene el contrato esperado de stages y navegación.")
    matches = list(re.finditer(r'<div class="slide-stage" id="slide-\d+"(?:\s[^>]*)?>', document))
    if not matches:
        raise ValueError("El deck V2 no contiene stages numerados.")
    stages: list[str] = []
    for position, match in enumerate(matches):
        end = matches[position + 1].start() if position + 1 < len(matches) else nav_start
        stages.append(document[match.start():end])
    return document[:first_stage], stages, document[nav_start:]


def visible_bar_labels(stage: str) -> list[str]:
    labels = [
        html.unescape(re.sub(r"<[^>]+>", "", value)).strip()
        for value in re.findall(
            r'<div class="bar-label"(?:\s+[^>]*)?>(.*?)</div>',
            stage,
            flags=re.S,
        )
    ]
    return [label for label in labels if label]


def category_normal(value: object) -> str:
    """Normalize only known missing-value display aliases."""
    key = normal(value)
    aliases = {
        "sinofficesite": "noofficesite",
        "sinofficesitecitypair": "noofficesitecitypair",
        "sinmodalidad": "noworkarrangement",
    }
    return aliases.get(key, key)


def article_classes(article: str) -> list[str]:
    opening = re.match(r"<article\b(?P<attrs>[^>]*)>", article, flags=re.I)
    if not opening:
        raise ValueError("Could not read an article opening tag.")
    class_match = re.search(r'\bclass="([^"]*)"', opening.group("attrs"), flags=re.I)
    return class_match.group(1).split() if class_match else []


def article_card_title(article: str) -> str:
    match = re.search(r'<div class="card-title"(?:\s[^>]*)?>(.*?)</div>', article, flags=re.I | re.S)
    if not match:
        return "Tasa por segmento"
    return html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()


def chart_cards(stage: str) -> list[tuple[int, int, str, list[str]]]:
    """Return source chart-card fragments in the visible source order."""
    cards: list[tuple[int, int, str, list[str]]] = []
    pattern = re.compile(r"<article\b[^>]*>", re.I)
    position = 0
    while match := pattern.search(stage, position):
        end = find_matching_tag(stage, "article", match.start())
        fragment = stage[match.start():end]
        classes = article_classes(fragment)
        if "chart-card" in classes:
            cards.append((match.start(), end, fragment, classes))
        position = end
    return cards


def replace_stage_heading(stage: str, title: str, subtitle: str) -> str:
    stage, title_count = re.subn(
        r'<h2 class="slide-title-text">.*?</h2>',
        f'<h2 class="slide-title-text">{esc(title)}</h2>',
        stage,
        count=1,
        flags=re.S,
    )
    if title_count != 1:
        raise ValueError("Could not replace the attrition companion title.")
    stage, subtitle_count = re.subn(
        r'<p class="slide-subtitle">.*?</p>',
        f'<p class="slide-subtitle">{esc(subtitle)}</p>',
        stage,
        count=1,
        flags=re.S,
    )
    if subtitle_count != 1:
        raise ValueError("Could not replace the attrition companion subtitle.")
    return stage


def refresh_context_for_attrition(stage: str) -> str:
    """Keep the source context in place but label its companion metric."""
    pattern = re.compile(r"<article\b[^>]*>", re.I)
    position = 0
    while match := pattern.search(stage, position):
        end = find_matching_tag(stage, "article", match.start())
        fragment = stage[match.start():end]
        if "side-copy" not in article_classes(fragment):
            position = end
            continue
        fragment, badge_count = re.subn(
            r'<span class="badge([^\"]*)">.*?</span>',
            '<span class="badge\\1 v3-attrition-badge">Attrition \u00b7 6 meses</span>',
            fragment,
            count=1,
            flags=re.S,
        )
        note = (
            '<p class="v3-context-note">Las barras naranjas conservan la segmentación visible; '
            'la medida es la tasa <strong>Voluntary</strong> durante los seis meses posteriores a cada snapshot.</p>'
        )
        if badge_count:
            fragment = re.sub(r'(<span class="badge[^>]*>.*?</span>)', r'\1' + note, fragment, count=1, flags=re.S)
        else:
            fragment = re.sub(r'(</div>)', note + r'\1', fragment, count=1)
        return stage[:match.start()] + fragment + stage[end:]
    raise ValueError(f"Missing source context card for {stage_title(stage)!r}.")


def add_markers(stage: str, distribution: str | None, attrition: str | None, note: str = "") -> str:
    start = stage.find('<div class="slide-heading">')
    if start < 0:
        return stage
    end = find_matching_div(stage, start)
    insertion = []
    if distribution:
        insertion.append(f'<span class="v3-marker v3-marker-distribution">{esc(distribution)}</span>')
    if attrition:
        insertion.append(
            f'<span class="v3-marker v3-marker-attrition" title="{esc(note)}">{esc(attrition)}</span>'
        )
    if not insertion:
        return stage
    markup = '<div class="v3-heading-markers">' + "".join(insertion) + "</div>"
    close_start = end - len("</div>")
    return stage[:close_start] + markup + stage[close_start:]


def add_paired_attrition(stage: str, card: str) -> str:
    marker = '<div class="two-pane">'
    pane_start = stage.find(marker)
    if pane_start < 0:
        raise ValueError(f"La lámina {stage_title(stage)!r} no tiene un layout two-pane para el pareado.")
    pane_open_end = pane_start + len(marker)
    pane_end = find_matching_div(stage, pane_start)
    pane_close_start = pane_end - len("</div>")
    inner = stage[pane_open_end:pane_close_start]
    side_start = inner.rfind('<article class="card side-copy')
    if side_start < 0:
        raise ValueError(f"La lámina {stage_title(stage)!r} no tiene la tarjeta contextual esperada.")
    paired_inner = inner[:side_start] + card + inner[side_start:]
    return (
        stage[:pane_start]
        + '<div class="two-pane v3-paired">'
        + paired_inner
        + stage[pane_close_start:]
    )


def restore_gender_internal_labels(stage: str) -> str:
    """V2's presentation-mode refresh anonymized gender labels.

    V3 is explicitly classified as internal_analysis and its evidence query
    enforces the cohort gate, so it may restore the stored F/M labels solely
    for this internal aggregate artifact.  The field remains non-operational.
    """
    replacements = (
        ('title="Category A">Category A</div>', 'title="F">F</div>'),
        ('title="Category B">Category B</div>', 'title="M">M</div>'),
        ('Restricted presentation', 'Internal analysis'),
        ('Stored anonymized codes', 'Stored gender values'),
        ('anonymized codes', 'stored values'),
        ('Semantic labels are suppressed in this presentation.', 'Etiquetas almacenadas visibles sólo en este análisis interno agregado; nunca para targeting.'),
    )
    for source, target in replacements:
        stage = stage.replace(source, target)
    return stage


def sanitize_restricted_work_arrangement(stage: str) -> str:
    """Do not carry medical/caregiving/leave labels into V3 reader-facing HTML."""
    return re.sub(
        r'[^<>{}]{0,80}(?:Medical Accommodation|Caregiving|Return from LOA)[^<>{}]{0,80}',
        'Restricted arrangement categories',
        stage,
        flags=re.IGNORECASE,
    )


def source_section(title: str) -> str:
    key = normal(title)
    if any(token in key for token in ("appliedtoajob", "transfer", "location", "officesite", "teamturnover")):
        return "Movilidad y ubicación"
    if any(
        token in key
        for token in (
            "jobfamily",
            "region",
            "gender",
            "workarrangement",
            "engineering",
            "rehire",
            "priorexperience",
            "commutedistance",
        )
    ):
        return "Estructura de la población"
    if any(
        token in key
        for token in (
            "qvoice",
            "rto",
            "nonrespond",
            "intenttostay",
            "careergoals",
            "averageqvoice",
            "standardized",
            "externalpull",
        )
    ):
        return "QVoice y fuentes externas"
    if any(
        token in key
        for token in (
            "timeinrole",
            "companytenure",
            "promotion",
            "gradeentry",
            "level",
            "compensation",
            "compratio",
        )
    ):
        return "Carrera y compensación"
    return "Manager y señales avanzadas"


def evidence_by_metric(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for row in payload["rows"]:
        result.setdefault(str(row["metric"]), []).append(dict(row))
    return result


def aggregate_rows(label: str, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    exposure = sum(integer(row["employee_snapshot_count"]) for row in rows)
    exits = sum(integer(row["voluntary_exits"]) for row in rows)
    if exposure < MINIMUM_COHORT or exits < MINIMUM_COHORT:
        return None
    baseline = number(rows[0]["baseline_rate_percent"])
    rate = 100.0 * exits / exposure
    return {
        "category": label,
        "employee_snapshot_count": exposure,
        "voluntary_exits": exits,
        "attrition_rate_percent": rate,
        "baseline_rate_percent": baseline,
        "lift_vs_baseline": rate / baseline if baseline else 0.0,
    }


def select_display_rows(
    metric: str,
    metric_rows: list[dict[str, Any]],
    source_stage: str,
    maximum_rows: int,
    fallback_other_label: str = "Otras categorías",
) -> list[dict[str, Any]]:
    """Keep the V2 display order when its labels can be reconciled safely.

    V2's current distribution provides the visible category order.  Historical
    categories not displayed in V2 are pooled into the matching Other bucket,
    never shown as a new unreviewed category.
    """
    labels = visible_bar_labels(source_stage)
    by_normal = {category_normal(row["category"]): row for row in metric_rows}
    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    other_label: str | None = None

    for label in labels:
        normalized = category_normal(label)
        if "other" in normalized or "otros" in normalized:
            other_label = label
            continue
        direct = by_normal.get(normalized)
        if direct and category_normal(direct["category"]) not in used:
            selected.append(direct)
            used.add(category_normal(direct["category"]))

    # A V2 chart can use label variants such as "No office site" or a stripped
    # numeric level prefix.  A conservative prefix comparison keeps exact
    # source values first and avoids assigning a mismatched category.
    if not selected:
        for label in labels:
            normalized = category_normal(label)
            if "other" in normalized or "otros" in normalized:
                other_label = label
                continue
            matches = [
                row
                for row in metric_rows
                if category_normal(row["category"]) == normalized
                or category_normal(row["category"]).startswith(normalized)
                or normalized.startswith(category_normal(row["category"]))
            ]
            if len(matches) == 1 and category_normal(matches[0]["category"]) not in used:
                selected.append(matches[0])
                used.add(category_normal(matches[0]["category"]))

    if selected:
        remaining = [row for row in metric_rows if category_normal(row["category"]) not in used]
        if other_label:
            other = aggregate_rows(other_label, remaining)
            if other:
                selected.append(other)
        return selected[:maximum_rows]

    ordered = sorted(metric_rows, key=lambda row: integer(row["employee_snapshot_count"]), reverse=True)
    if len(ordered) <= maximum_rows:
        return ordered
    selected = ordered[:maximum_rows]
    other = aggregate_rows(fallback_other_label, ordered[maximum_rows:])
    if other:
        selected.append(other)
    return selected


def attrition_card(
    title: str,
    metric: str,
    source_stage: str,
    grouped: dict[str, list[dict[str, Any]]],
    maximum_rows: int,
    extra_class: str = "",
) -> str:
    rows = select_display_rows(metric, grouped.get(metric, []), source_stage, maximum_rows)
    if not rows:
        return no_estimate_card(title, "No hubo categorías publicables con la regla de privacidad de V3.", extra_class)

    maximum_rate = max(number(row["attrition_rate_percent"]) for row in rows) or 1.0
    baseline = number(rows[0]["baseline_rate_percent"])
    rendered_rows = []
    for row in rows:
        rate = number(row["attrition_rate_percent"])
        lift = number(row["lift_vs_baseline"])
        width = max(2.0, 100.0 * rate / maximum_rate)
        rendered_rows.append(
            '<div class="v3-rate-row">'
            f'<div class="v3-rate-label" title="{esc(row["category"])}">{esc(row["category"])}</div>'
            f'<div class="v3-rate-track"><div class="v3-rate-fill" style="width:{width:.2f}%"></div></div>'
            f'<div class="v3-rate-value">{rate:.2f}% <small>{lift:.2f}×</small></div>'
            "</div>"
        )
    return f"""<article class="card chart-card v3-attrition-card {esc(extra_class)}">
      <div class="card-title"><span class="v3-card-marker">ATTRITION · 6 MESES</span> {esc(title)}</div>
      <div class="v3-rate-list">{''.join(rendered_rows)}</div>
      <div class="v3-attrition-footer">Cada barra es la tasa Voluntary posterior al snapshot. Historia: 24 cortes maduros ({MATURE_FIRST_SNAPSHOT} a {MATURE_LAST_SNAPSHOT}); baseline de la misma población: <strong>{baseline:.2f}%</strong>. <strong>Lift</strong> = tasa del segmento ÷ baseline; 1.00× = igual al baseline.</div>
    </article>"""


def inherit_source_bar_style(card: str) -> str:
    """Give a V3 rate replacement the same V2 bar geometry as its source card."""
    replacements = (
        ('v3-attrition-card ', 'v3-attrition-card v3-source-style '),
        ('v3-no-estimate-card ', 'v3-no-estimate-card v3-source-style '),
        ('class="v3-rate-list"', 'class="bar-list v3-rate-list"'),
        ('class="v3-rate-row"', 'class="bar-row v3-rate-row"'),
        ('class="v3-rate-label"', 'class="bar-label v3-rate-label"'),
        ('class="v3-rate-track"', 'class="bar-track v3-rate-track"'),
        ('class="v3-rate-fill"', 'class="bar-fill v3-rate-fill"'),
        ('class="v3-rate-value"', 'class="bar-value v3-rate-value"'),
        ('class="v3-attrition-footer"', 'class="chart-footer v3-attrition-footer"'),
    )
    for original, replacement in replacements:
        card = card.replace(original, replacement)
    return card


def no_estimate_card(title: str, reason: str, extra_class: str = "") -> str:
    return f"""<article class="card chart-card v3-no-estimate-card {esc(extra_class)}">
      <div class="card-title"><span class="v3-card-marker v3-card-marker-muted">ATTRITION · 6 MESES</span> {esc(title)}</div>
      <div class="v3-no-estimate-value">No estimable</div>
      <p>{esc(reason)}</p>
      <div class="v3-attrition-footer">Se conserva la distribución/evidencia de V2, pero V3 no convierte una fuente incompleta, un proxy o una definición pendiente en una tasa de attrition.</div>
    </article>"""




def attrition_panel_title(source_card: str) -> str:
    """Reuse the source-panel name while removing its distribution wording."""
    title = article_card_title(source_card)
    title = re.sub(r"\bdistribution of\s+", "", title, flags=re.I)
    title = re.sub(r"\bdistribution\b", "", title, flags=re.I)
    title = re.sub(r"\s{2,}", " ", title).strip(" -·")
    return f"Tasa Voluntary · {title}" if title else "Tasa Voluntary"


def clone_attrition_layout(
    stage: str,
    panels: list[dict[str, Any]],
    grouped: dict[str, list[dict[str, Any]]],
) -> str:
    """Clone a V2 source layout and replace only its chart cards with rate cards."""
    source_cards = chart_cards(stage)
    if len(source_cards) != len(panels):
        raise ValueError(
            f"La lámina {stage_title(stage)!r} tiene {len(source_cards)} paneles de gráfico; "
            f"la configuración V3 espera {len(panels)}."
        )

    rendered: list[str] = []
    position = 0
    for (start, end, source_card, classes), panel in zip(source_cards, panels):
        preserved_classes = [name for name in classes if name not in {"card", "chart-card"}]
        extra_class = " ".join(
            part
            for part in [*preserved_classes, str(panel.get("extra_class", ""))]
            if part
        )
        title = str(panel.get("title") or attrition_panel_title(source_card))
        metric = panel.get("metric")
        if metric:
            replacement = attrition_card(
                title,
                str(metric),
                source_card,
                grouped,
                int(panel["maximum_rows"]),
                extra_class,
            )
        else:
            replacement = no_estimate_card(
                title,
                str(panel["reason"]),
                extra_class,
            )
        rendered.append(stage[position:start])
        rendered.append(inherit_source_bar_style(replacement))
        position = end
    rendered.append(stage[position:])
    companion = "".join(rendered)
    source_title = stage_title(stage)
    companion = replace_stage_heading(
        companion,
        f"Attrition voluntario · {source_title}",
        "Tasa Voluntary durante los seis meses posteriores a cada snapshot · misma estructura y segmentación que la distribución.",
    )
    companion = refresh_context_for_attrition(companion)
    companion = add_markers(
        companion,
        None,
        "ATTRITION · 6 MESES",
        "Misma estructura visual y mismo orden de segmentos que la distribución de origen.",
    )
    return companion.replace('class="slide-stage"', 'class="slide-stage" data-v3-layout="source-clone"', 1)


V3_CSS = r"""
    /* V3: distribution vs. six-month attrition comparison */
    .v3-heading-markers { display:flex; align-items:center; justify-content:flex-end; gap:7px; flex-wrap:wrap; margin-left:12px; }
    .v3-marker { display:inline-flex; align-items:center; min-height:24px; padding:3px 9px; border-radius:var(--radius-pill); font-size:10px; font-weight:800; letter-spacing:.07em; white-space:nowrap; }
    .v3-marker-distribution { color:var(--accent); background:color-mix(in oklab,var(--accent) 12%,transparent); border:1px solid color-mix(in oklab,var(--accent) 28%,var(--border-subtle)); }
    .v3-marker-attrition { color:#c2410c; background:color-mix(in oklab,#f97316 14%,transparent); border:1px solid color-mix(in oklab,#f97316 34%,var(--border-subtle)); }
    body.theme-dark-royal .v3-marker-attrition, body.theme-dark-carbon .v3-marker-attrition { color:#fdba74; }
    .v3-card-marker { color:#c2410c; } body.theme-dark-royal .v3-card-marker, body.theme-dark-carbon .v3-card-marker { color:#fdba74; }
    .v3-card-marker-muted { color:var(--text-muted); }
    .v3-attrition-badge { color:#c2410c !important; background:color-mix(in oklab,#f97316 14%,transparent) !important; border-color:color-mix(in oklab,#f97316 34%,var(--border-subtle)) !important; }
    body.theme-dark-royal .v3-attrition-badge, body.theme-dark-carbon .v3-attrition-badge { color:#fdba74 !important; }
    .v3-context-note { margin:0; color:var(--text-muted); font-size:10px; line-height:1.25; }
    .two-pane.v3-paired { grid-template-columns:minmax(0,1fr) minmax(0,1fr); grid-template-rows:minmax(0,1fr) auto; gap:10px 12px; }
    .two-pane.v3-paired > .side-copy { grid-column:1 / -1; height:auto; min-height:0; display:grid; grid-template-columns:auto minmax(170px,.7fr) minmax(260px,1.5fr) minmax(250px,1.4fr); align-items:start; column-gap:12px; padding:8px 12px; }
    .two-pane.v3-paired > .side-copy .card-title { display:none; }
    .two-pane.v3-paired > .side-copy .badge { align-self:start; }
    .two-pane.v3-paired > .side-copy h3 { font-size:13px; line-height:1.2; }
    .two-pane.v3-paired > .side-copy p { font-size:11px; line-height:1.25; }
    .two-pane.v3-paired > .side-copy .fact-list { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:2px 9px; margin:0; }
    .two-pane.v3-paired > .side-copy .fact-list li { font-size:10px; line-height:1.2; }
    .two-pane.v3-paired > .side-copy .scope-note, .two-pane.v3-paired > .side-copy .provenance-panel { display:none; }
    .v3-attrition-card:not(.v3-source-style) { min-width:0; min-height:0; padding:12px 13px; gap:7px; }
    .v3-attrition-card:not(.v3-source-style) .card-title { margin:0; padding-bottom:4px; font-size:10px; border-color:#f97316; }
    /* Source-clone cards reuse V2's own bar geometry; only their metric and
       orange treatment change.  This keeps labels, tracks and values in the
       same horizontal positions as the blue distribution chart. */
    .v3-source-style .card-title { border-color:#f97316; }
    .v3-attrition-card:not(.v3-source-style) .v3-rate-list { display:flex; flex:1; flex-direction:column; justify-content:space-evenly; gap:4px; min-height:0; }
    /* The paired distribution/attrition slides deliberately keep short rate
       lists compact at the top, mirroring their source distribution chart.
       Their footer owns the remaining vertical space.  Do not generalize this
       rule: source-clone panels need their inherited full-height rhythm. */
    .two-pane.v3-paired .v3-attrition-card .v3-rate-list { flex:0 0 auto; justify-content:flex-start; gap:12px; }
    .v3-attrition-card:not(.v3-source-style) .v3-rate-row { display:grid; grid-template-columns:minmax(105px,1.05fr) minmax(110px,1.25fr) 87px; align-items:center; gap:7px; min-height:18px; }
    .v3-attrition-card:not(.v3-source-style) .v3-rate-label { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; text-align:right; color:var(--text-main); font-size:11px; line-height:1.08; }
    .v3-attrition-card:not(.v3-source-style) .v3-rate-track { height:11px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    .v3-rate-fill { height:100%; min-width:2px; border-radius:inherit; background:linear-gradient(90deg,#fb923c,#ea580c); }
    .v3-source-style .v3-rate-fill { background:linear-gradient(90deg,#fb923c,#ea580c) !important; }
    .v3-attrition-card:not(.v3-source-style) .v3-rate-value { color:var(--text-main); font-size:11px; font-weight:800; font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }
    .v3-attrition-card:not(.v3-source-style) .v3-rate-value small, .v3-source-style .v3-rate-value small { color:var(--text-muted); font-size:9px; font-weight:700; }
    .v3-attrition-card:not(.v3-source-style) .v3-attrition-footer { margin-top:auto; padding-top:6px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:10px; line-height:1.25; }
    .v3-no-estimate-card:not(.v3-source-style) { justify-content:center; align-items:flex-start; gap:10px; }
    .v3-no-estimate-card:not(.v3-source-style) p { max-width:840px; margin:0; color:var(--text-main); font-size:15px; line-height:1.4; }
    .v3-no-estimate-value { color:var(--text-muted); font-size:31px; font-weight:850; letter-spacing:-.02em; }
    .v3-dense-21:not(.v3-source-style) .v3-rate-list { gap:2px; }
    .v3-dense-21:not(.v3-source-style) .v3-rate-row { min-height:14px; grid-template-columns:minmax(115px,1.15fr) minmax(110px,1.25fr) 82px; gap:6px; }
    .v3-dense-21:not(.v3-source-style) .v3-rate-label, .v3-dense-21:not(.v3-source-style) .v3-rate-value { font-size:10px; }
    .v3-dense-21:not(.v3-source-style) .v3-rate-value small { font-size:8px; }
    .v3-dense-21:not(.v3-source-style) .v3-rate-track { height:8px; }
    .v3-dense-21:not(.v3-source-style) .v3-attrition-footer { font-size:9px; line-height:1.18; padding-top:4px; }
    [data-v3-layout="source-clone"] .v3-attrition-card { height:100%; }
    [data-v3-layout="source-clone"] .v3-no-estimate-card { height:100%; }
    @media (max-width:900px) {
      .two-pane.v3-paired { grid-template-columns:1fr; }
      .two-pane.v3-paired > .side-copy { grid-column:auto; display:flex; }
      .v3-heading-markers { display:none; }
    }
"""


PAIR_VIEWS: dict[str, tuple[str, int]] = {
    "gender": ("gender", 4),
    "engineeringvsnonengineering": ("engineering", 3),
    "rehire": ("rehire", 3),
    "managerchange": ("manager_change", 3),
}


ANALOG_LAYOUTS: dict[str, list[dict[str, Any]]] = {
    # One immediate companion per source slide.  Each entry follows the visible
    # source-panel order so the V2 grid, hierarchy and context card survive.
    "location": [
        {"metric": "country", "maximum_rows": 21, "extra_class": "v3-dense-21"},
    ],
    "officesiteandcity": [
        {"metric": "office_site", "maximum_rows": 22, "extra_class": "v3-dense-21"},
        {"metric": "office_site_city", "maximum_rows": 22, "extra_class": "v3-dense-21"},
    ],
    "jobfamily": [
        {"metric": "job_family", "maximum_rows": 21, "extra_class": "v3-dense-21"},
        {"metric": "job_family", "maximum_rows": 21, "extra_class": "v3-dense-21"},
    ],
    "region": [
        {"metric": "region", "maximum_rows": 4},
        {"metric": "region_country_split", "maximum_rows": 6},
        {"metric": "labor_market", "maximum_rows": 21, "extra_class": "v3-dense-21"},
    ],
    "remotehybridinofficestatus": [
        {"metric": "work_arrangement", "maximum_rows": 12, "extra_class": "v3-dense-21"},
        {"metric": "work_arrangement_binary", "maximum_rows": 2},
    ],
    "yearsofexperiencepriortoqualcomm": [
        {"metric": "prior_experience_years", "maximum_rows": 35, "extra_class": "v3-dense-21"},
    ],
    "companytenure": [
        {
            "metric": None,
            "title": "Tasa Voluntary · Service since original hire",
            "reason": (
                "La evidencia V3 congelada valida company_tenure desde la fecha vigente de "
                "hire / rehire; no infiere una tasa separada para el proxy de hire original."
            ),
        },
        {
            "metric": "company_tenure",
            "maximum_rows": 8,
            "title": "Tasa Voluntary · Service since latest hire / rehire",
        },
    ],
    "level": [
        {"metric": "level_grouped", "maximum_rows": 12},
        {"metric": "management_level", "maximum_rows": 10},
        {"metric": "job_level", "maximum_rows": 12, "extra_class": "v3-dense-21"},
    ],
    "compensationgrade": [
        {"metric": "compensation_grade", "maximum_rows": 35, "extra_class": "v3-dense-21"},
    ],
}


NO_ESTIMATE_BY_STAGE: list[tuple[str, str]] = [
    ("Applied to a job", "La fuente de aplicaciones no tiene una historia actual y un join temporal V3 aprobado para esta comparación."),
    ("Transfer within past year", "El slide V2 no define todavía la ventana móvil de 12 meses; el flag puntual no se sustituye por esa variable."),
    ("RTO comment", "Las respuestas QVoice no tienen un join temporal de workforce y outcome aprobado para calcular attrition."),
    ("Any QVoice comment", "Los temas de comentarios son agregados de texto; no existe un join temporal aprobado a attrition."),
    ("Non-respondents", "La proxy de no respuesta requiere roster de invitación y join temporal aprobado antes de medir attrition."),
    ("Intent to Stay", "La observabilidad de QVoice no prueba un join temporal ni una escala aprobada para esta tasa."),
    ("Career goals", "El item no tiene join temporal a la cohorte de attrition ni comparabilidad de versiones validada."),
    ("Average QVoice", "El compuesto es respondent-only; no se ha validado el join temporal a la población de attrition."),
    ("QVoice heartbeat", "La señal restringida no tiene una ruta aprobada de join a outcome para la comparación V3."),
    ("Standardized within region", "La normalización QVoice permanece respondent-only y no tiene join temporal aprobado a attrition."),
    ("External pull factors", "Las fuentes externas no tienen proveedor, contrato ni crosswalk temporal aprobado."),
    ("Time in role and level", "La definición de la carrera/clock de entrada aún no está aprobada para una tasa comparable."),
    ("Time since promotion", "La fecha almacenada no reconstruye de forma segura el último evento para cada snapshot; no se infiere duración."),
    ("Promotions by grade", "La trayectoria de promoción por grado requiere una derivación temporal específica antes de asociarla con attrition."),
    ("Current grade entry path", "La vía de entrada no es equivalente a contratación directa y requiere reglas temporales adicionales."),
    ("Org layers to CEO", "La tasa no se calcula hasta reconciliar el campo mostrado con la jerarquía reconstruida y su raíz gobernada."),
    ("Within-team compensation", "La señal es de manager/grupo comparable; no existe aún una asignación employee-snapshot aprobada para attrition."),
    ("Co-location with manager", "El proxy de office_site no se vuelve una tasa V3 sin el self-join temporal y política de ausencias aprobados."),
    ("Residential distance", "La distancia residencial es un proxy restringido y no se usa como tasa de attrition en V3."),
    ("Office-site relationship", "La relación con manager es un proxy almacenado; falta la derivación employee-snapshot para esta tasa."),
    ("High-risk manager", "El ratio agregado no es una etiqueta operativa ni una categoría employee-snapshot aprobada para la comparación."),
    ("High turnover", "La definición, umbral, membresía y ventana de equipo siguen siendo contextuales; no se inventa una tasa."),
    ("Above-average team turnover", "La señal es contextual y no equivale a una feature employee-snapshot aprobada para V3."),
    ("Manager leaving", "La exposición requiere una atribución histórica específica; V3 no la recalcula como proxy genérico."),
    ("Number of manager changes", "El conteo requiere la ventana, deduplicación y exclusiones de movilidad aprobadas antes de medir attrition."),
    ("Talent index", "El índice vigente tiene riesgo de leakage y no puede usarse para una tasa de attrition V3."),
    ("Major inflection", "Los cambios observados son proxies; no hay un taxonomy o calendario autorizado de inflexiones mayores."),
    ("ET fields", "Las referencias de jerarquía no definen todavía una clasificación ET para comparar attrition."),
    ("Commute distance", "El cálculo depende de localización residencial restringida y no se convierte en una tasa V3."),
]


EXISTING_ATTRITION_TITLES = (
    "¿Una salida inicial precede más salidas?",
    "Sensibilidad: equipos de 6+ personas",
    "Annual voluntary attrition by prior experience",
    "Comp ratio",
)


CANDIDATE_STATUS: dict[str, tuple[str, str]] = {
    "Applied to a job": ("no_estimable", "Fuente de aplicaciones sin historia actual y join temporal V3 aprobado."),
    "More than 3 job applications": ("no_estimable", "Fuente de aplicaciones sin historia actual y definición de conteo aprobada."),
    "Transfer within past year": ("no_estimable", "Falta la derivación aprobada de la ventana de 12 meses."),
    "Location": ("estimable", "Country, office_site y office_site·city con resultado agregado a seis meses."),
    "Within team compensation range": ("no_estimable", "Sin asignación employee-snapshot aprobada del indicador de grupo."),
    "Team turnover": ("existing_context", "V2 ya conserva una asociación histórica de equipo; no se sustituye su definición."),
    "More than 1 employee leaves in a year": ("existing_context", "V2 ya conserva la evidencia contextual de equipos."),
    "Job family": ("estimable", "job_family_group y job_family con resultado agregado a seis meses."),
    "Region": ("estimable", "Region, split de display y Labor Market con resultado agregado a seis meses."),
    "Gender": ("estimable_internal_only", "Categorías protegidas sólo en internal_analysis con controles de cohorte."),
    "Remote / hybrid / in office status": ("estimable", "Categorías almacenadas y vista binaria Onsite con resultado agregado a seis meses."),
    "Engineering vs. non-engineering": ("estimable", "Clasificación almacenada con resultado agregado a seis meses."),
    "Rehire": ("estimable", "Estado rehire reciente; se mantiene la advertencia de cambio de era fuente."),
    "Years of experience prior to Qualcomm": ("estimable", "Bandas históricas derivadas de prior_qc_work_years."),
    "Commute distance": ("no_estimable", "Fuente residencial restringida; no se calcula tasa V3."),
    "RTO/hybrid comment in QVoice": ("no_estimable", "Sin join temporal a outcome aprobado."),
    "Any comment on QVoice": ("no_estimable", "Sin join temporal a outcome aprobado."),
    "Non-respondents": ("no_estimable", "Proxy sin roster/join temporal aprobado."),
    "Intent to Stay items": ("no_estimable", "Sin join temporal y escala comparada aprobada."),
    "Career goals item": ("no_estimable", "Sin join temporal y escala comparada aprobada."),
    "Average of all QVoice items": ("no_estimable", "Compuesto respondent-only sin join temporal aprobado."),
    "Standardized / normalized within region": ("no_estimable", "Compuesto respondent-only sin join temporal aprobado."),
    "Tech industry unemployment data": ("no_estimable", "Fuente externa sin proveedor ni crosswalk aprobado."),
    "Draup data": ("no_estimable", "Fuente externa sin contrato, historia o join aprobado."),
    "LinkedIn scraping": ("no_estimable", "No se autoriza scraping ni identity matching."),
    "Position / time in level": ("no_estimable", "Falta definición temporal del clock de entrada."),
    "Company tenure": ("estimable", "Bandas de tenure desde max_hire_rehire_date, con alcance explícito."),
    "Time since last promotion": ("no_estimable", "No se reconstruye último evento de forma segura con el campo mostrado."),
    "Promoted vs. hired into level": ("no_estimable", "Faltan reglas temporales y de precedencia para la vía de entrada."),
    "Level": ("estimable", "level_grouped, management_level y job_level con resultado agregado a seis meses."),
    "Layers from CEO": ("no_estimable", "La jerarquía mostrada requiere reconciliación con raíz gobernada."),
    "Compensation grade": ("estimable", "Grados agregados con protección de cohortes; no se muestran valores de compensación."),
    "Comp ratio": ("existing_context", "V2 ya contiene la comparación histórica a seis meses; V3 la distingue visualmente."),
    "Co-location with manager": ("no_estimable", "Falta self-join temporal y política de normalización aprobada."),
    "Hours away from manager": ("no_estimable", "Sin fuente externa aprobada para horas o zona horaria."),
    "High risk manager": ("no_estimable", "No es una etiqueta gobernada para una tasa employee-snapshot."),
    "High turnover under this person": ("no_estimable", "Faltan umbral y definición temporal de equipo aprobados."),
    "Manager leaving": ("no_estimable", "La exposición requiere atribución histórica específica que V3 no aproxima."),
    "Manager change": ("estimable", "Flag de evento almacenado con resultado agregado a seis meses."),
    "Number of manager changes": ("no_estimable", "Faltan ventana, deduplicación y exclusiones de movilidad aprobadas."),
    "Talent index": ("no_estimable", "Índice con riesgo de leakage; excluido de V3."),
    "Major inflection points": ("no_estimable", "No existe taxonomía o calendario de inflexiones gobernado."),
    "ET fields": ("no_estimable", "Las referencias jerárquicas no definen la clasificación solicitada."),
}


def status_for_stage(title: str) -> str | None:
    title_normal = normal(title)
    for candidate, reason in NO_ESTIMATE_BY_STAGE:
        if normal(candidate) in title_normal:
            return reason
    return None


def render_cover() -> str:
    return """<div class="slide-stage" id="slide-X"><div class="slide-heading"><div>
      <h2 class="slide-title-text">Distribuciones y attrition de variables candidatas · V3</h2>
      <p class="slide-subtitle">Análisis interno · evidencia agregada · comparación descriptiva, no predicción individual</p></div>
      <div class="v3-heading-markers"><span class="v3-marker v3-marker-distribution">DISTRIBUCIÓN</span><span class="v3-marker v3-marker-attrition">ATTRITION · 6 MESES</span></div></div>
      <article class="card card-full"><div class="deck-hero"><div>
        <h1>Distribución<br/>y attrition</h1>
        <p>V3 conserva las distribuciones validadas de V2 y añade, sólo donde la definición y el join temporal lo permiten, la tasa histórica de salida voluntaria dentro de los seis meses posteriores a cada snapshot.</p>
        <div class="deck-tags"><span class="badge badge-info">43 variables candidatas</span><span class="badge badge-success">Cohortes y eventos: n ≥ 30</span><span class="badge badge-wip">Internal analysis</span></div>
        <div class="deck-stat-row"><div class="deck-stat"><strong>24</strong><span>snapshots maduros de historia</span></div><div class="deck-stat"><strong>6 m</strong><span>horizonte por tasa</span></div><div class="deck-stat"><strong>0</strong><span>predicciones individuales</span></div></div>
      </div></div></article></div>"""


def render_agenda(ranges: list[tuple[str, int, int]]) -> str:
    rows = "".join(
        f'<div class="agenda-item"><span class="agenda-num">Láminas {start}–{end}</span><strong>{esc(title)}</strong><span class="agenda-sep">—</span><span>Distribución vigente y, cuando es estimable, attrition voluntario a seis meses.</span></div>'
        for title, start, end in ranges
    )
    return f"""<div class="slide-stage" id="slide-X"><div class="slide-heading"><div>
      <h2 class="slide-title-text">Guía de lectura · V3</h2>
      <p class="slide-subtitle">Azul = distribución vigente; naranja = attrition voluntario durante los seis meses posteriores al snapshot.</p></div>
      <div class="v3-heading-markers"><span class="v3-marker v3-marker-distribution">DISTRIBUCIÓN</span><span class="v3-marker v3-marker-attrition">ATTRITION · 6 MESES</span></div></div>
      <article class="card card-full"><div class="card-title">Portafolio de variables</div><div class="agenda-vertical">{rows}</div>
        <div class="privacy-banner"><strong>Cómo leer lift:</strong> tasa del segmento ÷ baseline de la misma población; 1.00× significa igual al baseline. “No estimable” preserva el límite semántico o de privacidad: no es cero attrition ni un proxy.</div>
      </article></div>"""


def nav_markup(slides: list[Slide], ranges: list[tuple[str, int, int]]) -> str:
    groups: list[str] = []
    for group_index, (section, start, end) in enumerate(ranges):
        buttons = "\n".join(
            f'<button class="nav-pill{" pill-active" if index == 0 else ""}" data-slide="{index}">{index + 1}. {esc(slides[index].label)}</button>'
            for index in range(start - 1, end)
        )
        groups.append(
            f"""<details class="nav-section" data-section="{group_index + 1}"{" open" if group_index == 0 else ""}>
        <summary><span class="nav-section-title">{esc(section)}</span><span class="nav-section-range">{start}–{end}</span></summary>
        <div class="nav-section-slides">{buttons}</div>
      </details>"""
        )
    return """<div class="nav-ctrl" id="slide-nav"><div class="nav-tab">Slides</div><div class="nav-panel">
      <div class="nav-label">Navegación</div>""" + "\n".join(groups) + "\n</div></div>"


def inject_v3_css(document: str) -> str:
    marker = "    /* 13. CONTENT-SPECIFIC STYLES"
    position = document.find(marker)
    if position < 0:
        raise ValueError("La plantilla base no conserva el marcador de estilos específicos.")
    # V2 keeps a multi-line comment immediately after the section marker. An
    # insertion directly below that marker would land inside the comment and
    # can invalidate the inherited V2 content styles. Append V3's rules at
    # the end of the same style block instead.
    style_end = document.find("</style>", position)
    if style_end < 0:
        raise ValueError("La fuente V2 no contiene el cierre del bloque de estilos.")
    return document[:style_end] + "\n" + V3_CSS + "\n" + document[style_end:]


def candidate_queue() -> list[dict[str, Any]]:
    text = QUEUE.read_text(encoding="utf-8")
    rows = [
        {"order": int(order), "name": name, "slug": slug.strip()}
        for order, name, slug in re.findall(
            r'- \{order:\s*(\d+),\s*name:\s*"([^"]+)",\s*slug:\s*([^}]+)\}',
            text,
        )
    ]
    if len(rows) != 43:
        raise ValueError(f"La cola V3 debe contener exactamente 43 variables; recibió {len(rows)}.")
    missing = [row["name"] for row in rows if row["name"] not in CANDIDATE_STATUS]
    if missing:
        raise ValueError(f"Faltan decisiones V3 para: {missing}")
    return rows


def process_original_stages(
    original: list[str],
    grouped: dict[str, list[dict[str, Any]]],
) -> list[Slide]:
    result: list[Slide] = []
    for index, stage in enumerate(original):
        title = stage_title(stage)
        # V2's first two slides are replaced by the V3 cover and agenda.
        if index < 2:
            continue
        normalized_title = normal(title)
        section = source_section(title)

        if normalized_title == "gender":
            stage = restore_gender_internal_labels(stage)
        if normalized_title == "remotehybridinofficestatus":
            stage = sanitize_restricted_work_arrangement(stage)

        if normalized_title in PAIR_VIEWS:
            metric, max_rows = PAIR_VIEWS[normalized_title]
            card = attrition_card(title, metric, stage, grouped, max_rows)
            stage = add_paired_attrition(stage, card)
            stage = add_markers(stage, "DISTRIBUCIÓN", "ATTRITION · 6 MESES")
            result.append(Slide(title, stage, section, "paired_distribution_attrition"))
            continue

        if normalized_title in ANALOG_LAYOUTS:
            companion = clone_attrition_layout(stage, ANALOG_LAYOUTS[normalized_title], grouped)
            stage = add_markers(
                stage,
                "DISTRIBUCIÓN",
                "ATTRITION · 6 MESES →",
                "La lámina inmediata conserva esta misma estructura visual con tasas naranjas.",
            )
            result.append(Slide(title, stage, section, "distribution"))
            result.append(Slide(f"Attrition · {title}", companion, section, "attrition_companion"))
            continue

        if title in EXISTING_ATTRITION_TITLES:
            stage = add_markers(stage, "DISTRIBUCIÓN", "ATTRITION · 6 MESES", "Vista histórica ya presente en V2; V3 conserva su definición específica.")
            result.append(Slide(title, stage, section, "existing_attrition_context"))
            continue

        no_estimate_reason = status_for_stage(title)
        if no_estimate_reason:
            stage = add_markers(stage, "DISTRIBUCIÓN", "ATTRITION · 6 MESES · NO ESTIMABLE", no_estimate_reason)
            result.append(Slide(title, stage, section, "no_estimate"))
            continue

        # Existing support visuals that are neither a direct V3 distribution nor
        # an approved attrition comparison retain an explicit V2-evidence label.
        stage = add_markers(stage, "EVIDENCIA / DISTRIBUCIÓN V2", None)
        result.append(Slide(title, stage, section, "v2_context"))
    return result


def ranges_for(slides: list[Slide]) -> list[tuple[str, int, int]]:
    ranges: list[tuple[str, int, int]] = []
    if not slides:
        return ranges
    section = slides[0].section
    start = 1
    for index, slide in enumerate(slides[1:], start=2):
        if slide.section == section:
            continue
        ranges.append((section, start, index - 1))
        section = slide.section
        start = index
    ranges.append((section, start, len(slides)))
    return ranges


def renumber_stages(slides: list[Slide]) -> list[Slide]:
    numbered: list[Slide] = []
    for index, slide in enumerate(slides, start=1):
        replacement, replacements = re.subn(
            r'id="slide-(?:\d+|X)"',
            f'id="slide-{index}"',
            slide.html_text,
            count=1,
        )
        if replacements != 1:
            raise ValueError(f"La lámina {slide.label!r} no tiene un identificador slide reemplazable.")
        numbered.append(Slide(slide.label, replacement, slide.section, slide.kind))
    return numbered


def validate_output(document: str, slides: list[Slide], queue: list[dict[str, Any]]) -> None:
    stage_ids = re.findall(r'<div class="slide-stage"[^>]*\bid="(slide-\d+)"', document)
    nav_start = document.find('<div class="nav-ctrl" id="slide-nav">')
    nav_end = document.find('<div class="side-controls" id="theme-selector">', nav_start)
    if nav_start < 0 or nav_end < 0:
        raise ValueError("V3 no conserva los controles de navegación y tema requeridos.")
    nav_block = document[nav_start:nav_end]
    nav_ids = re.findall(r'<button class="nav-pill(?: pill-active)?" data-slide="(\d+)"', nav_block)
    expected_stage_ids = [f"slide-{number}" for number in range(1, len(slides) + 1)]
    if stage_ids != expected_stage_ids:
        raise ValueError("Los IDs de las láminas V3 no son consecutivos.")
    if [int(value) for value in nav_ids] != list(range(len(slides))):
        raise ValueError(f"Los pills de navegación V3 no son consecutivos: {nav_ids[:8]}… total={len(nav_ids)} esperado={len(slides)}.")
    if len(stage_ids) != len(nav_ids):
        raise ValueError("V3 no tiene el mismo número de láminas y pills de navegación.")
    if "slide-2" not in document or "Guía de lectura · V3" not in document:
        raise ValueError("La segunda lámina V3 debe ser la agenda.")
    if len(queue) != 43 or any(row["name"] not in CANDIDATE_STATUS for row in queue):
        raise ValueError("La cola de 43 variables V3 no quedó completa.")
    if "ATTRITION · 6 MESES" not in document or "DISTRIBUCIÓN" not in document:
        raise ValueError("Faltan los marcadores visuales de distribución/attrition de V3.")
    source_clone_count = len(
        re.findall(r'<div class="slide-stage"[^>]*data-v3-layout="source-clone"', document)
    )
    if source_clone_count != len(ANALOG_LAYOUTS):
        raise ValueError(
            "Las compañeras de attrition ya no conservan una relación uno-a-uno "
            f"con los {len(ANALOG_LAYOUTS)} layouts fuente: se encontraron {source_clone_count}."
        )
    if '<div class="v3-companion-grid">' in document:
        raise ValueError("V3 no debe volver a usar layouts genéricos para las compañeras multi-panel.")
    restricted_labels = ("Medical Accommodation", "Caregiving", "Return from LOA")
    if any(label.lower() in document.lower() for label in restricted_labels):
        raise ValueError("V3 incluye una etiqueta restringida de modalidad de trabajo.")
    if '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>' not in document:
        raise ValueError("V3 debe conservar los gráficos complejos de V2 y su dependencia permitida de Plotly.")


def build() -> None:
    if not V2.exists() or not V2_MANIFEST.exists() or not TEMPLATE.exists() or not EVIDENCE.exists():
        raise FileNotFoundError("Falta V2, su manifest, la plantilla base o la evidencia agregada de V3.")

    # Required by html-slide-generator: start the output path from the canonical
    # fullscreen template before V2's established content is layered into V3.
    OUT.mkdir(parents=True, exist_ok=True)
    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    shutil.copyfile(TEMPLATE, target_tmp)
    copied_template = target_tmp.read_text(encoding="utf-8")
    if '<div class="side-controls" id="theme-selector">' not in copied_template:
        raise ValueError("La plantilla fullscreen copiada no tiene el selector de temas requerido.")

    v2_before_hash = hashlib.sha256(V2.read_bytes()).hexdigest()
    v2_manifest_hash = hashlib.sha256(V2_MANIFEST.read_bytes()).hexdigest()
    source = V2.read_text(encoding="utf-8")
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("deliverable_mode") != "internal_analysis" or evidence.get("outcome") != "pass":
        raise ValueError("La evidencia V3 debe ser internal_analysis y outcome pass.")
    if evidence.get("row_count") != len(evidence.get("rows", [])):
        raise ValueError("La evidencia V3 no reconcilia su número de filas.")

    queue = candidate_queue()
    grouped = evidence_by_metric(evidence)
    prefix, original_stages, suffix = extract_stages(source)
    content = process_original_stages(original_stages, grouped)

    # Insert V3 cover and agenda ahead of the inherited/companion content.
    provisional = [
        Slide("Portada V3", render_cover(), "Portada y lectura", "cover"),
        Slide("Guía de lectura", "", "Portada y lectura", "agenda"),
        *content,
    ]
    first_ranges = ranges_for(provisional)
    provisional[1] = Slide(
        "Guía de lectura",
        render_agenda(first_ranges),
        "Portada y lectura",
        "agenda",
    )
    slides = renumber_stages(provisional)
    ranges = ranges_for(slides)

    document = prefix + "\n\n  " + "\n\n  ".join(slide.html_text for slide in slides) + "\n\n  " + suffix
    document = inject_v3_css(document)
    document, title_replacements = re.subn(
        r"<title>.*?</title>",
        "<title>Distribuciones y attrition de 43 variables candidatas · V3</title>",
        document,
        count=1,
        flags=re.S,
    )
    if title_replacements != 1:
        raise ValueError("No se pudo actualizar el título del documento V3.")

    nav_start = document.find('<div class="nav-ctrl" id="slide-nav">')
    right_marker = "\n\n\n  <!-- ================================================================\n       RIGHT EDGE"
    right_start = document.find(right_marker, nav_start)
    if nav_start < 0 or right_start < 0:
        raise ValueError("No se pudo sustituir la navegación agrupada de V3.")
    document = document[:nav_start] + nav_markup(slides, ranges) + document[right_start:]

    validate_output(document, slides, queue)
    target_tmp.write_text(document, encoding="utf-8")
    target_tmp.replace(TARGET)

    if hashlib.sha256(V2.read_bytes()).hexdigest() != v2_before_hash:
        raise ValueError("V2 cambió durante la generación de V3; se preserva y se debe revisar.")

    companion_titles = [slide.label for slide in slides if slide.kind == "attrition_companion"]
    manifest = {
        "version": 3,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "objective": (
            "Documentar la distribución vigente y la asociación histórica de attrition voluntario "
            "a seis meses por cohortes; no predecir renuncias individuales."
        ),
        "source_deck": {
            "path": str(V2.relative_to(ROOT)).replace("\\", "/"),
            "sha256": v2_before_hash,
            "source_manifest": str(V2_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
            "source_manifest_sha256": v2_manifest_hash,
            "preserved": True,
        },
        "base_template": str(TEMPLATE),
        "six_month_evidence": {
            "path": str(EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(EVIDENCE.read_bytes()).hexdigest(),
            "query": evidence.get("query"),
            "query_sha256": evidence.get("query_sha256"),
            "history": f"latest 24 mature snapshots: {MATURE_FIRST_SNAPSHOT} through {MATURE_LAST_SNAPSHOT}",
            "baseline_rate_percent": 2.8085,
            "publication_rule": evidence.get("publication_rule"),
        },
        "visual_rules": {
            "distribution_marker": "DISTRIBUCIÓN (azul)",
            "attrition_marker": "ATTRITION · 6 MESES (naranja)",
            "simple_layout": "Distribución y attrition lado a lado; contexto debajo.",
            "dense_layout": (
                "Cada lámina V2 con varios paneles recibe una sola compañera de attrition "
                "que conserva su grilla, columnas, jerarquía y tarjeta de contexto."
            ),
            "category_order": "Se preserva el orden de categorías visible en V2 cuando puede reconciliarse con la evidencia histórica.",
            "secondary_metric": "Lift vs. baseline de la misma población; 1.00× equivale al baseline.",
            "no_estimate": "No se calcula una tasa si la fuente, definición o join temporal no está aprobado.",
        },
        "slide_count": len(slides),
        "slides": [
            {
                "slide": index,
                "title": slide.label,
                "section": slide.section,
                "kind": slide.kind,
            }
            for index, slide in enumerate(slides, start=1)
        ],
        "attrition_companion_slides": companion_titles,
        "queue": [
            {
                **row,
                "status": CANDIDATE_STATUS[row["name"]][0],
                "decision": CANDIDATE_STATUS[row["name"]][1],
            }
            for row in queue
        ],
        "queue_completion": {
            "total_candidates": len(queue),
            "completed_review": len(queue),
            "estimable": sum(CANDIDATE_STATUS[row["name"]][0].startswith("estimable") for row in queue),
            "existing_six_month_context": sum(CANDIDATE_STATUS[row["name"]][0] == "existing_context" for row in queue),
            "no_estimate": sum(CANDIDATE_STATUS[row["name"]][0] == "no_estimable" for row in queue),
            "outcome": "complete",
        },
        "privacy": {
            "minimum_distinct_employee_cohort": 30,
            "minimum_employee_snapshot_exposure": 30,
            "minimum_voluntary_events": 30,
            "protected_categories": "Gender real labels allowed only in the declared internal_analysis artifact.",
            "prohibited": ["employee rows", "IDs", "names", "emails", "addresses", "free text", "exact compensation"],
        },
        "validation": {
            "v2_unchanged_sha256": v2_before_hash,
            "stage_count_equals_navigation_count": True,
            "queue_43_complete": True,
            "outcome": "pass",
        },
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(TARGET)
    print(MANIFEST)
    print(f"slides={len(slides)}; companions={len(companion_titles)}; queue=43")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construye el deck V3 de distribución y attrition.")
    parser.parse_args()
    build()
