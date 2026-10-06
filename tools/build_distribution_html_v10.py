"""Añade attrition de períodos parciales a la lámina 8, sin anualizarla."""
from __future__ import annotations

import copy
import hashlib
import html
import json
import re
import shutil
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path

import yaml

try:
    from . import build_distribution_html_v9 as v9
except ImportError:
    import build_distribution_html_v9 as v9

ROOT = Path(__file__).resolve().parents[1]
SOURCE = v9.OUTPUT
SOURCE_MANIFEST = v9.MANIFEST
OUTPUT = ROOT / "output/distribution/attrition-43-variable-distributions-v10.html"
MANIFEST = ROOT / "output/distribution/json/attrition-43-variable-distributions-v10-manifest.json"
EVIDENCE = ROOT / "output/distribution/json/attrition-43-variable-distributions-v10.acquisition-observed-period-evidence-20261005.json"
PLAN = ROOT / "config/analysis-plans/20261005-acquisition-observed-period-v1.yaml"
SQL = ROOT / "queries/audits/acquisition_observed_period_attrition_20261005.sql"
RUN = ROOT / "output/assessments/acquisition-observed-period-20261005"
RAW = RUN / "evidence/query-results.json"
PREVIEW = ROOT / "output/preview/acquisition-observed-period-20261005/slide-8.html"
TEMPLATE = v9.TEMPLATE
require = v9.acquisition.require
digest = v9.v8.digest
relative = v9.acquisition.relative_path
rate_text = v9.rate_text

CSS = """
    /* Períodos observados: misma fórmula y ventana explícita por adquisición. */
    #slide-acquisition .v8-acquisition-table tbody tr { height:32px; }
    #slide-acquisition .v8-acquisition-table tbody th,
    #slide-acquisition .v8-acquisition-table td { padding:3px 5px; }
    #slide-acquisition .v10-rate-cell { text-align:center; white-space:nowrap; }
    #slide-acquisition .v10-period { text-align:center; color:var(--acquisition-muted); line-height:1.05; }
    #slide-acquisition .v10-period > span { display:block; font-size:13px; font-weight:700; line-height:1.05; }
    #slide-acquisition .v10-period small { display:block; font-size:12px; line-height:1.05; margin-top:0; white-space:nowrap; }
    #slide-acquisition .v10-partial-rate { font-size:13px !important; }
    #slide-acquisition .v10-no-followup-note { display:inline-block; margin-left:6px; font-size:12px; color:var(--acquisition-muted); }
    #slide-acquisition .v8-acquisition-legend { line-height:1.25; }
    #slide-acquisition .v8-acquisition-table thead th { padding:5px; }
"""


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def number_text(value: object) -> str:
    value = Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return format(value, "f").rstrip("0").rstrip(".") if value != value.to_integral() else str(int(value))


def short_date(value: str) -> str:
    stamp = date.fromisoformat(value)
    months = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
    return f"{stamp.day} {months[stamp.month - 1]} {str(stamp.year)[2:]}"


def calculate_periods(rows: list[dict], plan: dict) -> list[dict]:
    require(plan["artifact_classification"] == "internal_analysis", "Se requiere modo interno.")
    auth = plan["authorization"]
    require(auth["allow_small_cohort_and_event_aggregates"] is True, "Falta autorización para cohortes pequeñas.")
    require(auth["individual_rows_or_identifiers"] is False and auth["operational_use_or_score_change"] is False,
            "La revisión sólo autoriza agregados descriptivos.")
    require(plan["annualization"] is False, "La tasa parcial no debe anualizarse.")
    require(len(rows) == len(plan["expected_current_counts"]) == len({r["category_label"] for r in rows}),
            "Las cinco categorías deben aparecer una sola vez.")
    calculated = []
    for raw in rows:
        row = copy.deepcopy(raw)
        label = row["category_label"]
        require(label in plan["expected_current_counts"], "Categoría no prevista.")
        require(row["current_employee_count"] == plan["expected_current_counts"][label], "Cambió la población actual.")
        require(row["start_snapshot_date"] == plan["expected_first_snapshots"][label], "Cambió el primer corte observable.")
        require(row["end_snapshot_date"] == plan["current_snapshot"], "Cambió el corte final.")
        start, end = date.fromisoformat(row["start_snapshot_date"]), date.fromisoformat(row["end_snapshot_date"])
        days = (end - start).days
        require(start > date(2025, 8, 24) and days == row["followup_days"] >= 0, "Período inválido.")
        base, exits = int(row["baseline_employee_count"]), int(row["voluntary_exit_count"])
        require(base > 0 and 0 <= exits <= base, "Numerador o denominador inválido.")
        require(exits == row["independent_voluntary_exit_count"], "No reconcilia el numerador independiente.")
        require(row["duplicate_baseline_excess_row_count"] == row["contradictory_baseline_employee_count"] == 0,
                "La cohorte inicial contiene duplicados o contradicciones.")
        require(row["raw_voluntary_event_row_count"] >= row["unique_employee_date_event_count"] >= exits + row["multiple_exit_employee_count"],
                "No reconcilia la deduplicación de eventos.")
        require(0 <= row["multiple_exit_employee_count"] <= exits, "Conteo de salidas múltiples inválido.")
        require(row["current_members_of_starting_cohort"] <= base, "La cohorte inicial aumentó retrospectivamente.")
        require(row["current_members_of_starting_cohort"] + row["current_employees_outside_starting_cohort"] == row["current_employee_count"],
                "No reconcilia la pertenencia actual a la cohorte inicial.")
        observable = days >= auth["minimum_followup_days"] and row["postbaseline_snapshot_count"] >= auth["minimum_postbaseline_snapshots"]
        if observable:
            require(row["rate_status"] == "partial_period", "Estado del período incoherente.")
            rate = Decimal(100 * exits) / Decimal(base)
            rational = Fraction(100 * exits, base)
            independent_rate = Decimal(rational.numerator) / Decimal(rational.denominator)
            require(abs(rate - independent_rate) < Decimal("1e-12"), "Falló el recálculo racional.")
            require(row["observed_attrition_rate_percent"] is not None and
                    abs(rate - Decimal(str(row["observed_attrition_rate_percent"]))) < Decimal("1e-12"),
                    "La tasa SQL no coincide con el recálculo.")
            row["observed_attrition_rate_percent"] = str(rate)
            row["display_rate"] = rate_text(rate) + "*"
        else:
            require(days == 0 and row["postbaseline_snapshot_count"] == 0 and exits == 0,
                    "El caso sin seguimiento requiere revisión.")
            require(row["rate_status"] == "no_followup" and row["observed_attrition_rate_percent"] is None,
                    "Cero seguimiento no permite una tasa, ni siquiera cero.")
            row["display_rate"] = "—"
        row["observed_months"] = str(Decimal(days) * Decimal(12) / Decimal("365.25"))
        row["display_months"] = number_text(row["observed_months"])
        row["color_state"] = "not_comparable"
        row["annualized"] = False
        row["outcome"] = "pass"
        calculated.append(row)
    return calculated


def observed_stage(source_stage: str, periods: list[dict]) -> str:
    by_label = {r["category_label"]: r for r in periods}
    rows_seen = []

    def revise_row(match: re.Match) -> str:
        label = html.unescape(match.group("label"))
        row = match.group(0)
        rows_seen.append(label)
        cell = re.search(r'<td>(?P<content><span class="v8-acquisition-rate\b.*?)</td></tr>$', row, re.S)
        require(cell is not None, "No se localizó la celda de attrition.")
        if label in by_label:
            period = by_label[label]
            start, end, days = period["start_snapshot_date"], period["end_snapshot_date"], period["followup_days"]
            months, kind = period["display_months"], period["rate_status"]
            base, exits = period["baseline_employee_count"], period["voluntary_exit_count"]
            if kind == "partial_period":
                tip = (f"{label}: {period['display_rate']} en {months} meses ({days} días), del {start} al {end}. "
                       f"{exits:,} salidas voluntarias únicas / {base:,} empleados de la cohorte del primer corte. "
                       "Tasa observada sin anualizar; las incorporaciones posteriores quedan fuera de esta cohorte.")
                classes = "v8-acquisition-rate v8-reference-unavailable v10-partial-rate"
                count_markup = f'<small class="v9-rate-counts">{exits:,} / {base:,}</small>'
            else:
                tip = f"{label}: primer corte {start}, con {base:,} empleados. No hay un corte posterior; attrition todavía no estimable."
                classes = "v8-acquisition-rate v8-reference-unavailable v10-no-followup"
                count_markup = '<small class="v10-no-followup-note">1 corte</small>'
            tip = html.escape(tip, quote=True)
            rate_markup = (f'<span class="{classes}" data-v8-rate-precision="one-decimal" '
                           f'title="{tip}" aria-label="{tip}">{period["display_rate"]}</span>{count_markup}')
        else:
            start, end, days, months, kind = "2025-08-24", "2026-08-23", 364, "12", "annual"
            rate_markup = cell.group("content")
        period_tip = html.escape(f"Del {start} al {end}; {days} días de seguimiento. Meses aproximados.", quote=True)
        period_cell = (f'<td class="v10-period" title="{period_tip}"><span data-v8-percent-precision="one-decimal">{months}</span>'
                       f'<small>{short_date(start)}</small></td>')
        revised = row[:cell.start()] + f'<td class="v10-rate-cell">{rate_markup}</td>{period_cell}</tr>'
        return revised.replace('><th scope="row">',
                               f' data-window-kind="{kind}" data-start-date="{start}" data-end-date="{end}"><th scope="row">', 1)

    stage = re.sub(r'<tr data-acquisition-label="(?P<label>[^"]+)">.*?</tr>', revise_row, source_stage, flags=re.S)
    require(len(rows_seen) == 11 and set(by_label) <= set(rows_seen), "Faltan categorías en la lámina.")
    stage = stage.replace('data-v9-internal-acquisition="true"', 'data-v9-internal-acquisition="true" data-v10-observed-periods="true"')
    stage = stage.replace("Análisis interno · 12 meses", "Análisis interno · períodos observados")
    stage = stage.replace("Quienes tienen adquisición registrada presentan menor attrition voluntaria anual",
                          "La comparación anual se complementa con tasas desde el primer corte disponible*")
    stage = stage.replace("Empleados actuales, proporción y attrition voluntaria anual por adquisición",
                          "Empleados actuales, attrition observada, meses de seguimiento y fecha inicial por adquisición")
    stage = re.sub(r'<colgroup>.*?</colgroup>',
                   '<colgroup><col style="width:23%"><col style="width:22%"><col style="width:10%">'
                   '<col style="width:10%"><col style="width:23%"><col style="width:12%"></colgroup>', stage, count=1, flags=re.S)
    stage = stage.replace('<th scope="col">Attrition anual<small>salidas / base</small></th>',
                          '<th scope="col">Attrition observada<small>salidas / base</small></th><th scope="col">Meses<small>inicio</small></th>')
    legend = ('<p class="v8-acquisition-legend"><strong>*</strong> Menos de 12 meses, desde el primer corte con empleados; tasas sin anualizar.<br>'
              '<strong>NAPS:</strong> cohorte inicial de 4 empleados; las incorporaciones posteriores quedan fuera.<br>'
              '<strong>— Moonshot:</strong> sólo tiene el primer corte; aún no hay seguimiento posterior.</p>')
    stage = re.sub(r'<p class="v8-acquisition-legend">.*?</p>', legend, stage, count=1, flags=re.S)
    stage = re.sub(r'(<div class="v8-acquisition-notes">\s*<p>).*?</p>',
                   r'\1<strong>Tasa observada:</strong> salidas voluntarias únicas / cohorte inicial; categoría fija al inicio indicado y fin al 23 ago 2026. Incluye RF360.</p>',
                   stage, count=1, flags=re.S)
    footer = ('<div class="v8-acquisition-notes v9-internal-source">'
              '<p data-v8-percent-precision="one-decimal">Color en tasas de 12 meses: referencia total 5.5%; adquisiciones 3.1%. Verde/naranja: al menos 20% y 0.5 puntos por debajo/encima; azul: dentro del rango. '
              'Gris: período parcial o sin seguimiento.</p>'
              '<p>Fuentes HRDA: acquisition_entry_distribution_attrition_20260929.sql (29 sep 2026); '
              'acquisition_observed_period_attrition_20261005.sql (5 oct 2026).</p></div>')
    stage = re.sub(r'<div class="v8-acquisition-notes v9-internal-source">.*?</div>', footer, stage, count=1, flags=re.S)
    require("Sin cohorte" not in stage and "Attrition anual<small>" not in stage, "Quedaron estados anteriores.")
    return stage


def freeze(path: Path) -> dict:
    target = RUN / "evidence" / path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        require(target.read_bytes() == path.read_bytes(), "Cambió un insumo congelado de esta ejecución.")
    else:
        shutil.copyfile(path, target)
    return {"path": relative(path), "sha256": digest(path), "frozen_path": relative(target)}


def write_preview(stage: str, css: str) -> None:
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE, PREVIEW)
    template = re.sub(r'<!--.*?-->', '', PREVIEW.read_text(encoding="utf-8"), flags=re.S)
    template = re.sub(r'<style>.*?</style>', '<style>' + css + '</style>', template, count=1, flags=re.S)
    template = re.sub(r'<div class="slide-stage" id="slide-1">.*?(?=<div class="nav-ctrl")', stage + '\n', template, count=1, flags=re.S)
    template = template.replace('lang="en"', 'lang="es"').replace('[Slide Title]', 'Adquisiciones y attrition · períodos observados')
    template = template.replace('[First Slide Title]', 'Adquisiciones y attrition')
    template = template.replace('class="theme-light-classic">', 'class="theme-light-classic" data-deliverable-mode="internal_analysis">')
    template = template.replace('</head>', '<meta name="deliverable-classification" content="internal_analysis" /></head>')
    for old, new in ((">Slides<", ">Diapositivas<"), (">Navigation<", ">Navegación<"), (">Theme<", ">Tema<"),
                     ("Light – Classic", "Claro clásico"), ("Light – Soft Blue", "Claro suave"), ("Dark – Royal", "Oscuro azul"), ("Dark – Carbon", "Oscuro carbón")):
        template = template.replace(old, new)
    PREVIEW.write_text(template, encoding="utf-8")


def build() -> dict:
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    raw = read_json(RAW)
    require(raw["artifact_classification"] == "internal_analysis" and not raw["truncated"], "Evidencia incompleta o de otro modo.")
    require(raw["query_path"] == relative(SQL) and raw["analysis_plan"] == relative(PLAN), "La consulta no corresponde al plan.")
    source_manifest = read_json(SOURCE_MANIFEST)
    require(digest(SOURCE) == source_manifest["output"]["deck_sha256"], "V9 difiere de su manifest.")
    require(digest(v9.EVIDENCE) == source_manifest["acquisition_entry_evidence"]["sha256"], "Cambió la evidencia anual de origen.")
    periods = calculate_periods(raw["rows"], plan)
    inputs = {"sql": freeze(SQL), "plan": freeze(PLAN), "raw_result": {"path": relative(RAW), "sha256": digest(RAW)}}
    authorization = {"authorization_id": plan["analysis_id"], "path": relative(PLAN), "sha256": digest(PLAN), **plan["authorization"]}
    evidence = {
        "artifact_classification": "internal_analysis", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "authorization": authorization, "method": {key: plan[key] for key in ("concept", "population", "grain", "formula", "duration", "annualization", "later_entrants")},
        "source": {"executed_at_utc": raw["executed_at_utc"], **inputs},
        "annual_evidence": {"path": relative(v9.EVIDENCE), "sha256": digest(v9.EVIDENCE)},
        "periods": periods, "validation": {"categories_checked": len(periods), "partial_rates": sum(r["rate_status"] == "partial_period" for r in periods),
        "no_followup": sum(r["rate_status"] == "no_followup" for r in periods), "independent_numerators_match": True,
        "calculation_method": "División Decimal y comprobación racional Fraction contra la proporción SQL.", "acceptance_rule": plan["validation_stories"][1]["acceptance_rule"],
        "outcome": "pass"}, "score_v4_change": False,
    }
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding="utf-8")
    ledger = {"artifact_classification": "internal_analysis", "executed_at_utc": raw["executed_at_utc"], **inputs,
              "result_rows_sha256": hashlib.sha256(json.dumps(raw["rows"], sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()).hexdigest(),
              "row_count": len(periods), "validation": evidence["validation"], "authorization": authorization,
              "outcome": "pass", "score_v4_change": False}
    (RUN / "evidence-ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    matches = list(v9.v8.STAGE_RE.finditer(source))
    target = next(m for m in matches if m.group("id") == "slide-acquisition")
    stage = observed_stage(target.group("stage"), periods)
    deck = source[:target.start()] + stage + '\n\n' + source[target.end():]
    deck = deck.replace('</style>', CSS + '\n</style>', 1).replace('Employee Characteristics and Attrition — V9', 'Employee Characteristics and Attrition — V10')
    before = {m.group("id"): m.group("stage").strip() for m in matches}
    after = {m.group("id"): m.group("stage").strip() for m in v9.v8.STAGE_RE.finditer(deck)}
    changed = [key for key in before if before[key] != after.get(key)]
    require(changed == ["slide-acquisition"] and len(after) == 44, "Sólo debe cambiar la lámina 8.")
    require([int(n) for n in re.findall(r'class="nav-pill[^\"]*" data-slide="(\d+)"', deck)] == list(range(44)), "Cambió la navegación.")
    if not OUTPUT.exists():
        shutil.copyfile(TEMPLATE, OUTPUT)
    OUTPUT.write_text(deck, encoding="utf-8")
    write_preview(stage, re.search(r'<style>(.*?)</style>', deck, re.S).group(1))
    manifest = {
        "artifact_type": "internal_attrition_distribution_deck", "version": 10, "artifact_classification": "internal_analysis", "deliverable_mode": "internal_analysis",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {"deck": relative(SOURCE), "deck_sha256": digest(SOURCE), "manifest": relative(SOURCE_MANIFEST), "manifest_sha256": digest(SOURCE_MANIFEST)},
        "output": {"deck": relative(OUTPUT), "deck_sha256": digest(OUTPUT), "visible_stage_count": 44, "navigation_count": 44},
        "ordered_stages": source_manifest["ordered_stages"], "reader_groups": source_manifest["reader_groups"], "prioritization_rule": source_manifest["prioritization_rule"],
        "change": {"slide_number": 8, "changed_stage_ids": changed, "unchanged_stage_count": 43, "description": "Tasas observadas desde el primer corte disponible, con asterisco y período explícito."},
        "authorization": authorization, "analysis_plan": inputs["plan"],
        "observed_period_evidence": {"path": relative(EVIDENCE), "sha256": digest(EVIDENCE), "validation": evidence["validation"]},
        "annual_evidence": evidence["annual_evidence"],
        "color_policy": {**source_manifest["color_policy"], "partial_period_state": "not_comparable"},
        "preview": {"path": relative(PREVIEW), "sha256": digest(PREVIEW)},
        "privacy": {"aggregate_only": True, "employee_rows_persisted": False, "individual_identifiers_persisted": False, "small_cohorts_and_events": "Autorizados en el plan para el solicitante y Julia."},
        "score_v4_change": False, "outcome": "pass",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding="utf-8")
    run_manifest = {"artifact_classification": "internal_analysis", "authorization": authorization, "inputs": inputs,
                    "evidence": manifest["observed_period_evidence"], "deck": manifest["output"],
                    "evidence_ledger": {"path": relative(RUN / "evidence-ledger.json"), "sha256": digest(RUN / "evidence-ledger.json")},
                    "outcome": "pass", "score_v4_change": False}
    (RUN / "manifest.json").write_text(json.dumps(run_manifest, ensure_ascii=False, indent=2) + '\n', encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = build()
    print(json.dumps({"deck": result["output"]["deck"], "outcome": result["outcome"], **result["observed_period_evidence"]["validation"]}, ensure_ascii=False))
