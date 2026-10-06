"""Reemplaza solamente la lamina 30 de V7 con la historia por compensation track."""

from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v7.html"
EVIDENCE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.promotion-track-trailing-12m-evidence-20260918.json"
)
TOP_GRADE_EVIDENCE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.promotion-grade-top10-trailing-12m-evidence-20260918.json"
)
MANIFEST = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7-manifest.json"
REVISION_MANIFEST = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.promotion-track-trailing-12m-revision-20260918.json"
)
STYLE_MARKER = "/* slide-34: promotion and attrition by compensation track */"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def strip_scoped_css(value: str) -> str:
    marker_index = value.find(STYLE_MARKER)
    if marker_index < 0:
        return value
    start = value.rfind("\n", 0, marker_index)
    end = value.find("</style>", marker_index)
    require(start >= 0 and end >= 0, "No se pudo aislar el CSS acotado de la lamina 30.")
    return value[:start] + value[end:]


def format_date(value: str) -> str:
    parsed = datetime.strptime(value, "%Y-%m-%d")
    months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    return f"{months[parsed.month - 1]} {parsed.day}, {parsed.year}"


def stage_fragment(deck: str, stage_id: str = "slide-34") -> str:
    match = re.search(
        rf'(<div class="slide-stage" id="{re.escape(stage_id)}".*?)(?=\n\s*<div class="slide-stage"|\n\s*<script|\Z)',
        deck,
        flags=re.S,
    )
    require(match is not None, f"No se encontro {stage_id}.")
    return match.group(1)


def all_stage_fragments(deck: str) -> dict[str, str]:
    matches = re.findall(
        r'(<div class="slide-stage" id="([^"]+)".*?)(?=\n\s*<div class="slide-stage"|\n\s*<script|\Z)',
        deck,
        flags=re.S,
    )
    return {stage_id: fragment for fragment, stage_id in matches}


def build_row(row: dict[str, Any], attrition_class: str, *, dimension: str) -> str:
    label_key = "track" if dimension == "track" else "grade"
    label = html.escape(str(row[label_key]))
    label_type = "Track" if dimension == "track" else "Compensation grade"
    current_share = float(row["current_distribution_percent"])
    promotion_rate = float(row["promotion_rate_percent"])
    attrition_rate = float(row["attrition_rate_percent"])
    return (
        '<div class="track-story-row">'
        f'<div class="track-letter {"is-grade" if dimension == "grade" else ""}" aria-label="{label_type} {label}">{label}</div>'
        '<div class="track-story-cell track-story-distribution">'
        f'<div class="track-story-bar" aria-label="Current workforce share for {label_type.lower()} {label}: {current_share:.1f}%">'
        f'<span class="track-story-fill track-story-fill-distribution" style="width:{max(current_share, 1.2):.2f}%"></span></div>'
        f'<div class="track-story-value"><strong>{current_share:.1f}%</strong></div>'
        '</div>'
        '<div class="track-story-cell track-story-rate">'
        f'<div class="track-story-rate-value" aria-label="Promotion rate for {label_type.lower()} {label}: {promotion_rate:.1f}%">{promotion_rate:.1f}%</div>'
        '</div>'
        '<div class="track-story-cell track-story-rate">'
        f'<span class="v6-rate-pill {attrition_class}" aria-label="12-month voluntary attrition for {label_type.lower()} {label}: {attrition_rate:.1f}%">{attrition_rate:.1f}%</span>'
        '</div>'
        '</div>'
    )


def build_stage(evidence: dict[str, Any], top_grade_evidence: dict[str, Any]) -> str:
    rows = evidence["display_rows"]
    top_grade_rows = top_grade_evidence["top_grade_rows"]
    window = evidence["window"]
    assignment = evidence["exit_track_assignment"]
    attrition_rates = [float(row["attrition_rate_percent"]) for row in rows + top_grade_rows]
    lowest_attrition = min(attrition_rates)
    highest_attrition = max(attrition_rates)

    def rate_class(row: dict[str, Any]) -> str:
        rate = float(row["attrition_rate_percent"])
        if rate == lowest_attrition:
            return "attr-low"
        if rate == highest_attrition:
            return "attr-high"
        return "attr-mid"

    grouped_row_html = "".join(build_row(row, rate_class(row), dimension="track") for row in rows)
    top_grade_row_html = "".join(build_row(row, rate_class(row), dimension="grade") for row in top_grade_rows)
    snapshot = format_date(str(window["snapshot_date"]))
    start = format_date(str(window["start_exclusive"]))
    end = format_date(str(window["end_inclusive"]))
    return (
        '<div class="slide-stage" id="slide-34" data-evidence-run="promotion-track-trailing-12m-20260918">'
        '<div class="slide-heading"><div>'
        '<h2 class="slide-title-text">Promotion and attrition by pay track</h2>'
        f'<p class="slide-subtitle">Grouped pay tracks and exact grades - {snapshot} snapshot - trailing 12 months</p>'
        '</div><span class="badge badge-info">12 months through Aug 2026</span></div>'
        '<article class="card card-full track-story-card">'
        '<div class="track-story-panels">'
        '<section class="track-story-panel track-story-panel-grouped" role="table" aria-label="Grouped pay tracks with current workforce distribution, promotion rate and 12-month voluntary attrition">'
        '<div class="track-story-panel-title">Grouped pay tracks</div>'
        '<div class="track-story-grid">'
        '<div class="track-story-header" role="row">'
        '<div role="columnheader">Track</div><div role="columnheader">Current workforce</div>'
        '<div role="columnheader">Promotion rate</div><div role="columnheader">12-month attrition</div>'
        '</div>'
        + grouped_row_html
        + '</div></section>'
        '<section class="track-story-panel track-story-panel-top10" role="table" aria-label="Top 10 exact compensation grades with current workforce distribution, promotion rate and 12-month voluntary attrition">'
        '<div class="track-story-panel-title">Top 10 compensation grades</div>'
        '<div class="track-story-grid">'
        '<div class="track-story-header" role="row">'
        '<div role="columnheader">Grade</div><div role="columnheader">Current workforce</div>'
        '<div role="columnheader">Promotion rate</div><div role="columnheader">12-month attrition</div>'
        '</div>'
        + top_grade_row_html
        + '</div></section></div>'
        '<div class="track-story-notes">'
        '<p><strong>How to read it:</strong> The left panel groups pay grades by their first letter; M10, M20 and M30 appear as M. '
        'The right panel keeps grades exact and shows the ten largest current grades. '
        'Promotion rate reflects the latest annual review. '
        f'Attrition covers voluntary exits from {start} to {end}. Track assignment coverage: {float(assignment["coverage_percent"]):.2f}%. '
        'Categories with fewer than 30 employees or exits are not shown.</p>'
        '</div>'
        '<div class="v6-source-line"><strong>Source:</strong> HR data. Internal aggregate analysis; no employee-level or individual pay data is shown.</div>'
        '</article></div>'
    )


CSS = r'''

    /* slide-34: promotion and attrition by compensation track */
    #slide-34 .track-story-card { padding:12px 14px 9px; gap:8px; }
    #slide-34 .track-story-panels { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.24fr); gap:12px; min-height:0; }
    #slide-34 .track-story-panel { min-width:0; min-height:0; padding:9px 9px 8px; border:1px solid var(--border-subtle); border-radius:13px; background:color-mix(in oklab, var(--bg-surface) 96%, transparent); }
    #slide-34 .track-story-panel-title { padding:0 7px 7px; color:var(--text-main); font-size:11px; font-weight:850; letter-spacing:.02em; }
    #slide-34 .track-story-grid { display:flex; flex-direction:column; gap:4px; min-height:0; }
    #slide-34 .track-story-header, #slide-34 .track-story-row { display:grid; grid-template-columns:56px minmax(0,1fr) minmax(82px,.62fr) minmax(88px,.66fr); gap:8px; align-items:center; }
    #slide-34 .track-story-header { min-height:25px; padding:0 7px; color:var(--text-muted); font-size:9px; font-weight:850; letter-spacing:.045em; text-transform:uppercase; border-bottom:1px solid var(--border-subtle); }
    #slide-34 .track-story-row { min-height:44px; padding:5px 7px; border:1px solid var(--border-subtle); border-radius:10px; background:color-mix(in oklab, var(--bg-surface) 94%, transparent); }
    #slide-34 .track-story-panel-top10 .track-story-row { min-height:34px; padding:3px 6px; }
    #slide-34 .track-letter { width:42px; height:34px; border-radius:9px; display:grid; place-items:center; background:linear-gradient(135deg, var(--accent), var(--accent-2)); color:var(--text-invert); font-size:18px; font-weight:900; box-shadow:0 6px 14px color-mix(in oklab, var(--accent) 18%, transparent); }
    #slide-34 .track-letter.is-grade { width:52px; height:27px; border-radius:7px; font-size:13px; letter-spacing:.01em; }
    #slide-34 .track-story-cell { min-width:0; }
    #slide-34 .track-story-distribution { display:grid; grid-template-columns:minmax(80px,1fr) 54px; gap:8px; align-items:center; }
    #slide-34 .track-story-bar { height:10px; border-radius:999px; overflow:hidden; background:color-mix(in oklab, var(--text-muted) 13%, transparent); }
    #slide-34 .track-story-fill { display:block; height:100%; min-width:2px; border-radius:inherit; }
    #slide-34 .track-story-fill-distribution { background:linear-gradient(90deg, var(--accent), var(--accent-2)); }
    #slide-34 .track-story-value { display:flex; align-items:baseline; justify-content:flex-end; white-space:nowrap; font-variant-numeric:tabular-nums; }
    #slide-34 .track-story-value strong { font-size:14px; color:var(--text-main); }
    #slide-34 .track-story-rate { display:flex; align-items:center; justify-content:flex-start; min-height:25px; }
    #slide-34 .track-story-rate-value { font-size:14px; font-weight:850; color:var(--text-main); font-variant-numeric:tabular-nums; }
    #slide-34 .track-story-rate .v6-rate-pill { position:static; transform:none; display:inline-block; min-width:58px; padding:4px 5px; font-size:12px; line-height:1.05; text-align:center; }
    #slide-34 .track-story-panel-top10 .track-story-rate .v6-rate-pill { min-width:54px; padding:3px 4px; font-size:11px; }
    #slide-34 .track-story-notes { padding:6px 8px; border-radius:10px; background:var(--bg-surface-2); border:1px solid var(--border-subtle); }
    #slide-34 .track-story-notes p { margin:0; font-size:9.5px; line-height:1.25; color:var(--text-muted); }
    #slide-34 .track-story-notes strong { color:var(--text-main); }
'''


def main() -> None:
    for path in (DECK, EVIDENCE, TOP_GRADE_EVIDENCE, MANIFEST):
        require(path.exists(), f"No existe el insumo requerido: {path}")
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    top_grade_evidence = json.loads(TOP_GRADE_EVIDENCE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "La evidencia de compensation track no aprobo validaciones.")
    require(evidence.get("deliverable_mode") == "internal_analysis", "El modo de la evidencia no coincide con V7.")
    require(len(evidence.get("display_rows", [])) == 6, "La lamina espera seis tracks publicables.")
    require(top_grade_evidence.get("outcome") == "pass", "La evidencia Top 10 de compensation grades no aprobo validaciones.")
    require(top_grade_evidence.get("deliverable_mode") == "internal_analysis", "El modo de la evidencia Top 10 no coincide con V7.")
    require(len(top_grade_evidence.get("top_grade_rows", [])) == 10, "La lamina espera diez compensation grades exactos.")

    deck = DECK.read_text(encoding="utf-8")
    before_deck_sha = sha256_text(deck)
    before_stages = all_stage_fragments(deck)
    stage_count = len(before_stages)
    require(stage_count >= 30, "El deck V7 no contiene la lamina 30 esperada.")
    original_stage = stage_fragment(deck)
    replacement_stage = build_stage(evidence, top_grade_evidence)
    updated = deck.replace(original_stage, replacement_stage, 1)

    nav_pattern = re.compile(r'(<button class="nav-pill(?: pill-active)?" data-slide="28">).*?(</button>)', re.S)
    require(len(nav_pattern.findall(updated)) == 1, "No se encontro de forma unica la entrada de navegacion de la lamina 29.")
    updated = nav_pattern.sub(r'\g<1>29. Promotion and attrition by pay track\g<2>', updated, count=1)
    updated = strip_scoped_css(updated)
    require("</style>" in updated, "El deck no contiene el bloque principal de estilos.")
    updated = updated.replace("</style>", CSS + "\n</style>", 1)

    after_stages = all_stage_fragments(updated)
    require(set(after_stages) == set(before_stages), "El cambio altero el inventario de slides.")
    revised_stage = after_stages["slide-34"]
    before_normalized = deck.replace(original_stage, "__SLIDE_33__", 1)
    before_normalized = nav_pattern.sub(r'\g<1>__NAV_30__\g<2>', before_normalized, count=1)
    before_normalized = strip_scoped_css(before_normalized)
    before_normalized = re.sub(r"\n{2,}</style>", "\n</style>", before_normalized)
    after_normalized = updated.replace(revised_stage, "__SLIDE_33__", 1)
    after_normalized = nav_pattern.sub(r'\g<1>__NAV_30__\g<2>', after_normalized, count=1)
    after_normalized = strip_scoped_css(after_normalized)
    after_normalized = re.sub(r"\n{2,}</style>", "\n</style>", after_normalized)
    require(after_normalized == before_normalized, "La actualizacion modifico contenido fuera de la lamina 30, su navegacion o su CSS acotado.")
    require("promotion-grade-matrix" not in revised_stage, "La matriz anterior permanece en la lamina.")
    require(revised_stage.count('class="track-story-row"') == 16, "No se renderizaron las seis filas agrupadas y diez grades exactos esperados.")
    require(revised_stage.count("track-story-panel-top10") == 1, "Falta el panel Top 10 de compensation grades.")
    require("track-story-mini-bar" not in revised_stage, "Las mini-barras secundarias de tasas permanecen en la lamina.")
    require(revised_stage.count("v6-rate-pill attr-") == 16, "No se renderizaron los pills de attrition esperados.")
    require(revised_stage.count("track-story-rate-value") == 16, "No se renderizaron los porcentajes de promocion esperados.")
    require("2026-08-23" not in revised_stage, "La fecha ISO no debe aparecer en la narrativa visible.")
    require("latest annual review" in revised_stage and "99.96%" in revised_stage, "Faltan las definiciones clave de tasas o cobertura.")
    require("employee_id" not in revised_stage.lower(), "La lamina no puede exponer identificadores.")
    require(len(after_stages) == stage_count, "El deck final no conserva el inventario original de slides.")
    nav_values = [int(value) for value in re.findall(r'<button class="nav-pill(?: pill-active)?" data-slide="(\d+)">', updated)]
    require(nav_values == list(range(stage_count)), "La navegacion del deck dejo de ser contigua.")

    DECK.write_text(updated, encoding="utf-8")
    output_sha = sha256_bytes(DECK.read_bytes())
    evidence_sha = sha256_bytes(EVIDENCE.read_bytes())
    stage_sha = sha256_text(revised_stage)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    manifest["updated_slide_30"] = {
        "navigation_slide_number": 29,
        "stage_id": "slide-34",
        "title": "Promotion and attrition by pay track",
        "replaces": "Promotion history by current compensation grade",
        "visual": "Dos paneles comparables: seis filas de pay track agrupado por letra y diez compensation grades exactos ordenados por poblacion actual; cada fila conserva distribucion, promotion rate y attrition voluntaria trailing 12 months.",
        "window": evidence["window"],
        "definitions": evidence["definition"],
        "evidence": {
            "path": str(EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": evidence_sha,
            "query_provenance": evidence["query_provenance"],
        },
        "top_grade_evidence": {
            "path": str(TOP_GRADE_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_bytes(TOP_GRADE_EVIDENCE.read_bytes()),
            "query_provenance": top_grade_evidence["query_provenance"],
        },
        "privacy": evidence["privacy"],
        "exit_track_assignment": evidence["exit_track_assignment"],
        "stage_sha256": stage_sha,
        "outcome": "pass",
    }
    validation = manifest.setdefault("validation", {})
    validation.update(
        {
            "slides": stage_count,
            "navigation_items": stage_count,
            "slide_30_compensation_track_rows": 6,
            "slide_30_top10_compensation_grade_rows": 10,
            "slide_30_two_panel_layout": True,
            "slide_30_secondary_rate_bars_removed": True,
            "slide_30_attrition_color_pills": 6,
            "slide_30_old_grade_matrix_removed": True,
            "slide_30_august_cutoff_visible": True,
            "slide_30_evidence_outcome": "pass",
        }
    )
    manifest["output_deck"] = {
        "path": str(DECK.relative_to(ROOT)).replace("\\", "/"),
        "sha256": output_sha,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    revision = {
        "artifact_type": "slide_revision_manifest",
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "deck": str(DECK.relative_to(ROOT)).replace("\\", "/"),
        "deck_sha256_before": before_deck_sha,
        "deck_sha256_after": output_sha,
        "revised_slide": {"navigation_slide": 30, "stage_id": "slide-34"},
        "stage_sha256_before": sha256_text(original_stage),
        "stage_sha256_after": stage_sha,
        "evidence": {
            "path": str(EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": evidence_sha,
            "top_grade_path": str(TOP_GRADE_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "top_grade_sha256": sha256_bytes(TOP_GRADE_EVIDENCE.read_bytes()),
        },
        "non_target_stages_preserved": True,
        "slide_count": stage_count,
        "navigation_count": stage_count,
        "outcome": "pass",
    }
    REVISION_MANIFEST.write_text(json.dumps(revision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(DECK)
    print(MANIFEST)
    print(REVISION_MANIFEST)


if __name__ == "__main__":
    main()
