"""Completa las tasas internas de adquisición sobre el deck V8 congelado."""
from __future__ import annotations

import copy
import html
import json
import re
import shutil
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

try:
    from . import build_acquisition_entry_evidence as acquisition
    from . import build_distribution_html_v8 as v8
except ImportError:
    import build_acquisition_entry_evidence as acquisition
    import build_distribution_html_v8 as v8

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/distribution/attrition-43-variable-distributions-v8.html"
SOURCE_MANIFEST = ROOT / "output/distribution/json/attrition-43-variable-distributions-v8-manifest.json"
OUTPUT = ROOT / "output/distribution/attrition-43-variable-distributions-v9.html"
MANIFEST = ROOT / "output/distribution/json/attrition-43-variable-distributions-v9-manifest.json"
EVIDENCE = ROOT / "output/distribution/json/attrition-43-variable-distributions-v9.acquisition-internal-attrition-evidence-20261005.json"
AUTHORIZATION = ROOT / "config/acquisition_attrition_internal_analysis_authorization_20261005.json"
PLAN = ROOT / "config/analysis-plans/20261005-acquisition-internal-attrition-v1.yaml"
PREVIEW = ROOT / "output/preview/acquisition-internal-20261005/slide-8.html"
TEMPLATE = Path(r"C:\Users\fcarranz\.codex\skills\html-slide-generator\templates\fullscreen\base-fullscreen.html")
CSS = """
    /* Revisión interna de la lámina 8: numerador y denominador visibles. */
    #slide-acquisition .v9-rate-counts { display:inline-block; margin-left:6px; font-size:12px; line-height:1.1; color:var(--acquisition-muted); white-space:nowrap; vertical-align:middle; }
    #slide-acquisition .v8-acquisition-table td { padding:4px 6px; }
    #slide-acquisition .v8-acquisition-table td:last-child { white-space:nowrap; }
    #slide-acquisition .v8-acquisition-table .v8-acquisition-rate { padding:3px 8px; min-width:64px; }
    #slide-acquisition .v8-acquisition-table tbody th { padding:4px 6px; }
    #slide-acquisition .v8-acquisition-table tbody tr { height:34px; }
    #slide-acquisition .v8-acquisition-table thead small { display:block; font-size:12px; margin-top:3px; }
    #slide-acquisition .v9-internal-source { font-size:12px; line-height:1.25; }
"""


def rate_text(value: object) -> str:
    return v8.fmt_pct_decimal(Decimal(str(value))).replace(".0%", "%")


def content_without_stage_language(stage: str) -> str:
    """Compara contenido sin confundir anotaciones de idioma con cambios de datos."""
    return re.sub(r'(<div class="slide-stage"[^>]*?)\s+lang="[^"]+"', r'\1', stage, count=1).strip()


def internal_stage(evidence: dict, policy: dict) -> str:
    acquisition.require(evidence["artifact_classification"] == "internal_analysis", "La lámina requiere evidencia interna autorizada.")
    acquisition.require(evidence.get("authorization", {}).get("authorization_id"), "Falta la autorización trazable.")
    view = copy.deepcopy(evidence)
    for row in view["top_acquisitions"]:
        if row["annual_attrition"]["publication_status"] == "internal_analysis_exception":
            row["annual_attrition"]["publication_status"] = "publishable"
    stage = v8.acquisition_stage(view)
    replacements = {
        'lang="en"': 'lang="es" data-v9-internal-acquisition="true"',
        "Acquisitions and attrition": "Adquisiciones y attrition",
        "Employees with an acquisition recorded show lower observed annual voluntary attrition": "Quienes tienen adquisición registrada presentan menor attrition voluntaria anual",
        "Annual attrition · 12 months": "Análisis interno · 12 meses",
        "No acquisition recorded": "Sin adquisición registrada",
        "Acquisition recorded": "Con adquisición registrada",
        "Other acquisitions": "Otras adquisiciones",
        "Current workforce": "Población actual",
        "active Regular employees": "empleados Regular activos",
        "Annual voluntary attrition": "Attrition voluntaria anual",
        "24 Aug 2025 cohort → 23 Aug 2026": "Cohorte del 24 ago 2025 → 23 ago 2026",
        "Baseline:": "Base:",
        "percentage points lower": "puntos porcentuales menos",
        "Unadjusted comparison; does not establish causality.": "Comparación sin ajuste; asociación descriptiva.",
        "Largest recorded acquisitions": "Principales adquisiciones registradas",
        "Top 10 + Other · shares of the": "Top 10 + Otras · proporción entre los",
        "employees with a record today": "empleados con registro actual",
        "Current acquisition headcount, share of recorded acquisitions, and annual voluntary attrition": "Empleados actuales, proporción y attrition voluntaria anual por adquisición",
        ">Acquisition</th>": ">Adquisición</th>",
        "Current employees": "Empleados actuales",
        ">Share</th>": ">Proporción</th>",
        ">Annual attrition</th>": ">Attrition anual<small>salidas / base</small></th>",
        ">No cohort</span>": ">Sin cohorte</span>",
        "No comparable annual cohort: no employees in this acquisition segment at the 24 Aug 2025 baseline.": "Sin cohorte anual: esta categoría no tenía empleados en la base del 24 ago 2025.",
        "<strong>No cohort:</strong> absent from the annual baseline.<br><strong>Suppressed:</strong> fewer than 30 voluntary exits.": "<strong>Sin cohorte:</strong> no había empleados en esa categoría al 24 ago 2025.<br>Se incluyen las tasas con menos de 30 salidas para esta revisión interna.",
        "<strong>Annual rate:</strong> unique voluntary exits / starting cohort. Acquisition status fixed at 24 Aug 2025; exits through 23 Aug 2026. RF360 included.": "<strong>Tasa anual:</strong> salidas voluntarias únicas / cohorte inicial. Categoría fija al 24 ago 2025; salidas hasta el 23 ago 2026. Incluye RF360.",
        "does not confirm hiring route. Baseline reconciliation pending:": "no confirma la vía de ingreso. Reconciliación basal pendiente:",
        " now vs ": " en esta evidencia frente a ",
        " previously.": " en evidencia previa.",
        "Annual voluntary attrition for ": "Attrition voluntaria anual de ",
        "voluntary exits / ": "salidas voluntarias / ",
        "employees at the 24 Aug 2025 baseline, followed through 23 Aug 2026.": "empleados en la base del 24 ago 2025, seguidos hasta el 23 ago 2026.",
        "23 Aug 2026": "23 ago 2026",
        "employees": "empleados",
    }
    for old, new in replacements.items():
        stage = stage.replace(old, new)
    stage = stage.replace("Attrition voluntaria anual for ", "Attrition voluntaria anual de ")

    by_label = {row["label"]: row for row in evidence["top_acquisitions"]}
    row_pattern = re.compile(r'(<tr data-acquisition-label="([^"]+)">.*?)(</tr>)', re.S)

    def add_counts(match: re.Match) -> str:
        row = by_label[html.unescape(match.group(2))]
        annual = row["annual_attrition"]
        body = match.group(1)
        if annual["baseline_employee_count"]:
            counts = f'{annual["voluntary_exit_count"]:,} / {annual["baseline_employee_count"]:,}'
            body = re.sub(r'</td>$', f'<small class="v9-rate-counts">{counts}</small></td>', body)
        return body + match.group(3)

    stage = row_pattern.sub(add_counts, stage)
    overall_reference = Decimal(evidence["color_references"]["overall_distribution"]["rate_percent"])
    acquired_reference = Decimal(evidence["color_references"]["acquisition_panel"]["rate_percent"])
    values = [(Decimal(row["annual_attrition_rate_percent"]), overall_reference) for row in evidence["overall_distribution"]]
    values += [(Decimal(row["annual_attrition"]["annual_attrition_rate_percent"]), acquired_reference)
               for row in evidence["top_acquisitions"] if row["annual_attrition"]["annual_attrition_rate_percent"] is not None]
    pills = list(v8.source_rate_pills(stage))
    acquisition.require(len(pills) == len(values), "El número de tasas visibles no coincide con la evidencia.")
    for pill, (value, reference) in reversed(list(zip(pills, values))):
        colored = pill.group(0).replace("attr-mid", v8.attrition_color_class(value, reference, policy))
        stage = stage[:pill.start()] + colored + stage[pill.end():]
    footer = (
        '<div class="v8-acquisition-notes v9-internal-source">'
        '<p>Referencia de color: población total '
        f'<span data-v8-percent-precision="one-decimal">{rate_text(overall_reference)}</span>; adquisiciones '
        f'<span data-v8-percent-precision="one-decimal">{rate_text(acquired_reference)}</span>. '
        'Verde/naranja: al menos 20% y 0.5 puntos por debajo/encima; azul: dentro del rango.</p>'
        '<p>Fuente: HRDA · <span title="queries/audits/acquisition_entry_distribution_attrition_20260929.sql">'
        'acquisition_entry_distribution_attrition_20260929.sql</span> · ejecución: 29 sep 2026 · recálculo: 5 oct 2026.</p></div>'
    )
    return stage.replace('</article>', footer + '</article>', 1)


def write_preview(stage: str, css: str) -> None:
    """Extrae sólo la lámina corregida a la plantilla canónica para validación."""
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE, PREVIEW)
    template = re.sub(r'<!--.*?-->', '', PREVIEW.read_text(encoding="utf-8"), flags=re.S)
    template = re.sub(r'<style>.*?</style>', '<style>' + css + '</style>', template, count=1, flags=re.S)
    template = re.sub(r'<div class="slide-stage" id="slide-1">.*?(?=<div class="nav-ctrl")', stage + '\n', template, count=1, flags=re.S)
    template = template.replace('lang="en"', 'lang="es"').replace('[Slide Title]', 'Adquisiciones y attrition · análisis interno')
    template = template.replace('[First Slide Title]', 'Adquisiciones y attrition')
    template = template.replace('class="theme-light-classic">', 'class="theme-light-classic" data-deliverable-mode="internal_analysis">')
    template = template.replace('</head>', '<meta name="deliverable-classification" content="internal_analysis" /></head>')
    for old, new in ((">Slides<", ">Diapositivas<"), (">Navigation<", ">Navegación<"), (">Theme<", ">Tema<"),
                     ("Light – Classic", "Claro clásico"), ("Light – Soft Blue", "Claro suave"), ("Dark – Royal", "Oscuro azul"), ("Dark – Carbon", "Oscuro carbón")):
        template = template.replace(old, new)
    PREVIEW.write_text(template, encoding="utf-8")


def build() -> dict:
    source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    acquisition.require(v8.digest(SOURCE) == source_manifest["output"]["deck_sha256"], "El V8 fuente no coincide con su manifest.")
    evidence = acquisition.build(EVIDENCE, authorization=AUTHORIZATION)
    source = SOURCE.read_text(encoding="utf-8")
    matches = list(v8.STAGE_RE.finditer(source))
    target = next(match for match in matches if match.group("id") == "slide-acquisition")
    policy = json.loads(v8.COLOR_POLICY.read_text(encoding="utf-8"))
    stage = internal_stage(evidence, policy)
    deck = source[:target.start()] + stage + '\n\n' + source[target.end():]
    deck = deck.replace('</style>', CSS + '\n</style>', 1)
    deck = deck.replace('Employee Characteristics and Attrition — V8', 'Employee Characteristics and Attrition — V9')
    deck = deck.replace('8. Acquisitions and attrition</button>', '8. Adquisiciones y attrition</button>')
    deck = deck.replace('</head>', '<meta name="deliverable-classification" content="internal_analysis" /></head>', 1)
    deck = deck.replace('<html lang="en">', '<html lang="es">', 1)

    def stage_language(match: re.Match) -> str:
        inherited = match.group(0)
        end = inherited.index('>')
        if 'lang=' in inherited[:end]:
            return inherited
        language = "es" if match.group("id") == "slide-2" else "en"
        return inherited[:end] + f' lang="{language}"' + inherited[end:]

    deck = v8.STAGE_RE.sub(stage_language, deck)
    for old, new in ((">Slides<", ">Diapositivas<"), (">Navigation<", ">Navegación<"), (">Theme<", ">Tema<"),
                     ("Light – Classic", "Claro clásico"), ("Light – Soft Blue", "Claro suave"), ("Dark – Royal", "Oscuro azul"), ("Dark – Carbon", "Oscuro carbón")):
        deck = deck.replace(old, new)
    previous_stages = {m.group("id"): content_without_stage_language(m.group("stage")) for m in matches}
    new_stages = {m.group("id"): content_without_stage_language(m.group("stage")) for m in v8.STAGE_RE.finditer(deck)}
    changed = [key for key in previous_stages if previous_stages[key] != new_stages.get(key)]
    acquisition.require(changed == ["slide-acquisition"], "La revisión debe cambiar sólo la lámina de adquisiciones.")
    navigation = [int(value) for value in re.findall(r'class="nav-pill[^\"]*" data-slide="(\d+)"', deck)]
    acquisition.require(len(new_stages) == 44 and navigation == list(range(44)), "La navegación debe conservar 44 láminas.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if not OUTPUT.exists():
        shutil.copyfile(TEMPLATE, OUTPUT)
    OUTPUT.write_text(deck, encoding="utf-8")
    css = re.search(r'<style>(.*?)</style>', deck, re.S).group(1)
    write_preview(stage, css)
    ordered_stages = copy.deepcopy(source_manifest["ordered_stages"])
    ordered_stages[7]["title"] = "Adquisiciones y attrition"
    manifest = {
        "artifact_type": "internal_attrition_distribution_deck", "version": 9,
        "artifact_classification": "internal_analysis", "deliverable_mode": "internal_analysis",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {"deck": acquisition.relative_path(SOURCE), "deck_sha256": v8.digest(SOURCE),
                   "manifest": acquisition.relative_path(SOURCE_MANIFEST), "manifest_sha256": v8.digest(SOURCE_MANIFEST)},
        "output": {"deck": acquisition.relative_path(OUTPUT), "deck_sha256": v8.digest(OUTPUT),
                   "visible_stage_count": 44, "navigation_count": 44},
        "ordered_stages": ordered_stages, "reader_groups": source_manifest["reader_groups"],
        "prioritization_rule": source_manifest["prioritization_rule"],
        "change": {"slide_number": 8, "stage_id": "slide-acquisition", "changed_stage_ids": changed,
                   "unchanged_stage_count": 43, "description": "Tasas internas completas con salidas/base y explicación de las categorías sin cohorte anual."},
        "authorization": evidence["authorization"],
        "analysis_plan": {"path": acquisition.relative_path(PLAN), "sha256": v8.digest(PLAN)},
        "acquisition_entry_evidence": {"path": acquisition.relative_path(EVIDENCE), "sha256": v8.digest(EVIDENCE),
                                       "artifact_classification": "internal_analysis", "recalculation": evidence["recalculation"]},
        "inherited_content": {"source_version": 8, "authorization_path": "config/attrition_v8_internal_analysis_authorization_20260923.json",
                              "language": "en", "revised_slide_language": "es", "explicit_stage_language_annotations": True,
                              "evidence_policy": "Las otras láminas conservan el contenido y las referencias del manifest V8; se declara su idioma y se localizan los controles."},
        "source_provenance": evidence["source_provenance"],
        "color_policy": {"path": acquisition.relative_path(v8.COLOR_POLICY), "sha256": v8.digest(v8.COLOR_POLICY),
                         "references": evidence["color_references"]},
        "preview": {"path": acquisition.relative_path(PREVIEW), "sha256": v8.digest(PREVIEW)},
        "privacy": evidence["privacy"], "score_v4_change": False, "outcome": "pass",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = build()
    print(json.dumps({"deck": result["output"]["deck"], "restored_rates": result["acquisition_entry_evidence"]["recalculation"]["metrics"]["restored_rates"], "outcome": result["outcome"]}, ensure_ascii=False))
