"""Simplifica la lámina 8 y la presenta en inglés por instrucción del usuario."""
from __future__ import annotations

import copy
import html
import importlib.util
import json
import re
import shutil
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

try:
    from . import build_distribution_html_v10 as v10
except ImportError:
    import build_distribution_html_v10 as v10

ROOT = Path(__file__).resolve().parents[1]
SOURCE = v10.OUTPUT
SOURCE_MANIFEST = v10.MANIFEST
OUTPUT = ROOT / "output/distribution/attrition-43-variable-distributions-v11.html"
MANIFEST = ROOT / "output/distribution/json/attrition-43-variable-distributions-v11-manifest.json"
PREVIEW = ROOT / "output/preview/acquisition-simple-english-20261005/slide-8.html"
TEMPLATE = v10.TEMPLATE
read_json, require, digest, relative = v10.read_json, v10.require, v10.digest, v10.relative
rate_text = v10.rate_text

CSS = """
    /* Lámina 8: porcentajes y fechas, con una sola nota de lectura. */
    #slide-acquisition .v8-acquisition-card { gap:14px; }
    #slide-acquisition .v8-acquisition-table tbody tr { height:43px; }
    #slide-acquisition .v8-acquisition-table tbody th { font-size:14px; padding:4px 6px; }
    #slide-acquisition .v8-acquisition-table td { padding:4px 6px; }
    #slide-acquisition .v8-acquisition-table .v8-acquisition-rate { min-width:76px; font-size:15px; padding:4px 10px; }
    #slide-acquisition .v8-acquisition-table .v8-reference-unavailable { font-size:15px; }
    #slide-acquisition .v11-rate-date { display:block; margin-top:4px; color:var(--acquisition-muted); font-size:12px; font-weight:400; line-height:1.1; white-space:nowrap; }
    #slide-acquisition .v11-footer { display:flex; justify-content:space-between; align-items:center; gap:20px; padding-top:10px; border-top:1px solid var(--border-subtle); }
    #slide-acquisition .v11-footer p { margin:0; color:var(--acquisition-muted); font-size:12px; line-height:1.3; }
    #slide-acquisition .v11-source { flex-shrink:0; white-space:nowrap; }
    #slide-acquisition .v8-acquisition-rate-grid { margin-top:8px; margin-bottom:8px; }
"""


def english_date(value: str) -> str:
    value = date.fromisoformat(value)
    months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    return f"{value.day} {months[value.month - 1]} {value.year}"


def label_en(label: str) -> str:
    return {"Otras adquisiciones": "Other acquisitions"}.get(label, label)


def numeric_pill(text: str, classes: str, tooltip: str) -> str:
    escaped = html.escape(tooltip, quote=True)
    return (f'<span class="v8-acquisition-rate {classes}" data-v8-rate-precision="one-decimal" '
            f'title="{escaped}" aria-label="{escaped}">{html.escape(text)}</span>')


def render_stage(annual: dict, observed: dict, policy: dict) -> str:
    overall = annual["overall_distribution"]
    partials = {row["category_label"]: row for row in observed["periods"]}
    current_total = sum(row["current_employee_count"] for row in overall)
    acquired_count = overall[0]["current_employee_count"]
    overall_reference = Decimal(annual["color_references"]["overall_distribution"]["rate_percent"])
    acquired_reference = Decimal(annual["color_references"]["acquisition_panel"]["rate_percent"])
    current_labels = ("Acquisition recorded", "No acquisition recorded")
    mix, rates = [], []
    for row, label in zip(overall, current_labels):
        count = row["current_employee_count"]
        share = rate_text(Decimal(count) * 100 / current_total)
        value = Decimal(row["annual_attrition_rate_percent"])
        classes = v10.v9.v8.attrition_color_class(value, overall_reference, policy)
        mix.append(f'<div class="v8-acquisition-mix-item"><span class="v8-acquisition-mix-value" data-v8-percent-precision="one-decimal">{share}</span>'
                   f'<span class="v8-acquisition-label">{label}</span><small>{count:,} employees</small></div>')
        tip = (f"{label}: {rate_text(value)} voluntary attrition among employees present on 24 Aug 2025, "
               "followed through 23 Aug 2026. Acquisition status is fixed at the starting date.")
        rates.append(f'<div class="v8-acquisition-rate-card"><span class="v8-acquisition-label">{label}</span>'
                     + numeric_pill(rate_text(value), classes, tip) + '</div>')
    difference = Decimal(overall[1]["annual_attrition_rate_percent"]) - Decimal(overall[0]["annual_attrition_rate_percent"])
    max_count = max(row["current_employee_count"] for row in annual["top_acquisitions"])
    rows = []
    for row in annual["top_acquisitions"]:
        original_label = row["label"]
        label = label_en(original_label)
        count = row["current_employee_count"]
        date_markup = ""
        if original_label in partials:
            period = partials[original_label]
            kind, start = period["rate_status"], period["start_snapshot_date"]
            classes = "v8-reference-unavailable"
            text = period["display_rate"]
            if kind == "partial_period":
                tip = (f"{label}: {text} voluntary attrition over {period['display_months']} months, from the first available "
                       f"snapshot on {english_date(start)} through 23 Aug 2026. Not annualized; follows the starting group only.")
                if original_label == "NAPS":
                    tip += " The starting group contains only 4 employees; later arrivals are excluded."
            else:
                tip = f"{label}: data first appear on {english_date(start)}. No later snapshot is available to measure attrition."
            date_markup = f'<small class="v11-rate-date">From {english_date(start)}</small>'
        else:
            kind, start = "annual", "2025-08-24"
            value = Decimal(row["annual_attrition"]["annual_attrition_rate_percent"])
            text = rate_text(value)
            classes = v10.v9.v8.attrition_color_class(value, acquired_reference, policy)
            tip = (f"{label}: {text} voluntary attrition among employees present on 24 Aug 2025, followed through "
                   "23 Aug 2026. Color compares this annual rate with the 3.1% acquired-employee reference.")
        share = rate_text(Decimal(count) * 100 / acquired_count)
        bar_width = Decimal(count) * 100 / max_count
        rows.append(f'<tr data-acquisition-label="{html.escape(label, quote=True)}" data-window-kind="{kind}" '
                    f'data-start-date="{start}" data-end-date="2026-08-23"><th scope="row">{html.escape(label)}</th>'
                    f'<td><div class="v8-acquisition-track" aria-hidden="true"><div class="v8-acquisition-fill" style="width:{bar_width:.4f}%"></div></div></td>'
                    f'<td class="v8-acquisition-count">{count:,}</td><td class="v8-acquisition-share"><span data-v8-percent-precision="one-decimal">{share}</span></td>'
                    f'<td>{numeric_pill(text, classes, tip)}{date_markup}</td></tr>')
    composition = Decimal(acquired_count) * 100 / current_total
    return f'''<div class="slide-stage" id="slide-acquisition" lang="en" data-v11-simple-acquisition="true">
      <div class="slide-heading"><div><h2 class="slide-title-text">Acquisitions and attrition</h2>
        <p class="slide-subtitle">Lower 12-month attrition among employees with an acquisition recorded</p>
      </div><span class="badge badge-info">Internal analysis</span></div>
      <article class="card card-full v8-acquisition-card">
        <div class="v8-acquisition-layout">
          <div class="v8-acquisition-summary">
            <section class="v8-acquisition-panel" aria-labelledby="acquisition-workforce-title">
              <header><h3 id="acquisition-workforce-title">Current workforce</h3>
                <p class="v8-acquisition-context">23 Aug 2026 · {current_total:,} active regular employees</p></header>
              <div class="v8-acquisition-mix">{''.join(mix)}</div>
              <div class="v8-acquisition-composition" aria-hidden="true"><div class="v8-acquisition-composition-fill" style="width:{composition:.6f}%"></div></div>
            </section>
            <section class="v8-acquisition-panel" aria-labelledby="acquisition-attrition-title">
              <header><h3 id="acquisition-attrition-title">12-month voluntary attrition</h3>
                <p class="v8-acquisition-context">Employees present on 24 Aug 2025</p></header>
              <div class="v8-acquisition-rate-grid">{''.join(rates)}</div>
              <p class="v8-acquisition-takeaway"><span data-v8-percent-precision="one-decimal">{v10.number_text(difference)} percentage points lower</span>
                <small>Observed, unadjusted comparison.</small></p>
            </section>
          </div>
          <section class="v8-acquisition-panel v8-acquisition-details" aria-labelledby="acquisition-detail-title">
            <header><h3 id="acquisition-detail-title">Largest recorded acquisitions</h3>
              <p class="v8-acquisition-context">Current workforce · Top 10 + Other</p></header>
            <table class="v8-acquisition-table" aria-label="Current workforce and observed voluntary attrition by acquisition">
              <colgroup><col style="width:27%"><col style="width:26%"><col style="width:12%"><col style="width:11%"><col style="width:24%"></colgroup>
              <thead><tr><th scope="col">Acquisition</th><th scope="colgroup" colspan="2">Current employees</th><th scope="col">Share</th><th scope="col">Attrition</th></tr></thead>
              <tbody>{''.join(rows)}</tbody>
            </table>
          </section>
        </div>
        <div class="v11-footer">
          <p>* Less than 12 months; not annualized. NAPS: small starting cohort. — No follow-up yet.</p>
          <p class="v11-source" data-query-paths="queries/audits/acquisition_entry_distribution_attrition_20260929.sql;queries/audits/acquisition_observed_period_attrition_20261005.sql"
             title="HRDA aggregate evidence executed on 29 Sep 2026 and 5 Oct 2026.">Source: HRDA · Through 23 Aug 2026</p>
        </div>
      </article>
    </div>'''


def static_check(document: str) -> dict:
    """Aplica el idioma inglés solicitado sin cambiar el validador del skill."""
    path = ROOT / ".agents/skills/build-html-presentation/scripts/verify_deck.py"
    spec = importlib.util.spec_from_file_location("verify_deck_v11", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors, warnings = module.check(document, "internal_analysis")
    language_ok = bool(re.search(r'<html\b[^>]*lang="en"', document))
    internal_marker_ok = bool(re.search(r'<span class="badge badge-info">Internal analysis</span>', document))
    overrides = []
    for message, accepted in (
        ('El elemento <html> debe declarar lang="es".', language_ok),
        ('Entregable internal_analysis sin marca visible de «análisis interno».', internal_marker_ok),
    ):
        if message in errors and accepted:
            errors.remove(message)
            overrides.append({"legacy_check": message, "reason": "El usuario pidió explícitamente la presentación y la lámina 8 en inglés.", "outcome": "pass"})
    warnings = [message for message in warnings if not message.startswith("Etiqueta visible en inglés:")]
    require(language_ok and internal_marker_ok, "Faltan el idioma o la clasificación visibles solicitados.")
    require(not errors, "; ".join(errors))
    return {"errors": errors, "warnings": warnings, "user_language_overrides": overrides, "outcome": "pass"}


def write_preview(stage: str, css: str) -> None:
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE, PREVIEW)
    template = re.sub(r'<!--.*?-->', '', PREVIEW.read_text(encoding="utf-8"), flags=re.S)
    template = re.sub(r'<style>.*?</style>', '<style>' + css + '</style>', template, count=1, flags=re.S)
    template = re.sub(r'<div class="slide-stage" id="slide-1">.*?(?=<div class="nav-ctrl")', stage + '\n', template, count=1, flags=re.S)
    template = template.replace('[Slide Title]', 'Acquisitions and attrition').replace('[First Slide Title]', 'Acquisitions and attrition')
    template = template.replace('class="theme-light-classic">', 'class="theme-light-classic" data-deliverable-mode="internal_analysis">')
    template = template.replace('</head>', '<meta name="deliverable-classification" content="internal_analysis" /></head>')
    PREVIEW.write_text(template, encoding="utf-8")


def build() -> dict:
    source_manifest = read_json(SOURCE_MANIFEST)
    require(digest(SOURCE) == source_manifest["output"]["deck_sha256"], "V10 no coincide con su manifest.")
    require(digest(v10.EVIDENCE) == source_manifest["observed_period_evidence"]["sha256"], "Cambió la evidencia parcial.")
    require(digest(v10.v9.EVIDENCE) == source_manifest["annual_evidence"]["sha256"], "Cambió la evidencia anual.")
    annual, observed = read_json(v10.v9.EVIDENCE), read_json(v10.EVIDENCE)
    policy = read_json(v10.v9.v8.COLOR_POLICY)
    source = SOURCE.read_text(encoding="utf-8")
    matches = list(v10.v9.v8.STAGE_RE.finditer(source))
    target = next(match for match in matches if match.group("id") == "slide-acquisition")
    stage = render_stage(annual, observed, policy)
    require(not re.search(r'\b[\d,]+\s*/\s*[\d,]+\b', stage), "Quedaron fracciones de attrition en la lámina.")
    deck = source[:target.start()] + stage + '\n\n' + source[target.end():]
    deck = deck.replace('</style>', CSS + '\n</style>', 1)
    deck = deck.replace('<html lang="es">', '<html lang="en">', 1)
    deck = deck.replace('Employee Characteristics and Attrition — V10', 'Employee Characteristics and Attrition — V11')
    deck = deck.replace('8. Adquisiciones y attrition</button>', '8. Acquisitions and attrition</button>')
    for old, new in ((">Diapositivas<", ">Slides<"), (">Navegación<", ">Navigation<"), (">Tema<", ">Theme<"),
                     ("Claro clásico", "Light – Classic"), ("Claro suave", "Light – Soft Blue"), ("Oscuro azul", "Dark – Royal"), ("Oscuro carbón", "Dark – Carbon")):
        deck = deck.replace(old, new)
    before = {match.group("id"): match.group("stage").strip() for match in matches}
    after = {match.group("id"): match.group("stage").strip() for match in v10.v9.v8.STAGE_RE.finditer(deck)}
    changed = [key for key in before if before[key] != after.get(key)]
    require(changed == ["slide-acquisition"] and len(after) == 44, "La revisión sólo debe cambiar la lámina 8.")
    if not OUTPUT.exists():
        shutil.copyfile(TEMPLATE, OUTPUT)
    OUTPUT.write_text(deck, encoding="utf-8")
    write_preview(stage, re.search(r'<style>(.*?)</style>', deck, re.S).group(1))
    static = {"deck": static_check(deck), "preview": static_check(PREVIEW.read_text(encoding="utf-8"))}
    ordered = copy.deepcopy(source_manifest["ordered_stages"])
    ordered[7]["title"] = "Acquisitions and attrition"
    manifest = {
        "artifact_type": "internal_attrition_distribution_deck", "version": 11, "artifact_classification": "internal_analysis", "deliverable_mode": "internal_analysis",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {"deck": relative(SOURCE), "deck_sha256": digest(SOURCE), "manifest": relative(SOURCE_MANIFEST), "manifest_sha256": digest(SOURCE_MANIFEST)},
        "output": {"deck": relative(OUTPUT), "deck_sha256": digest(OUTPUT), "visible_stage_count": 44, "navigation_count": 44},
        "change": {"slide_number": 8, "changed_stage_ids": changed, "unchanged_stage_count": 43,
                   "description": "Lámina en inglés, sin fracciones ni columna de meses; fecha inicial discreta bajo las tasas parciales y una sola nota breve.",
                   "language": "en", "language_authority": "Instrucción explícita del usuario en esta conversación.", "data_changed": False},
        "ordered_stages": ordered, "reader_groups": source_manifest["reader_groups"], "prioritization_rule": source_manifest["prioritization_rule"],
        "authorization": source_manifest["authorization"], "observed_period_evidence": source_manifest["observed_period_evidence"],
        "annual_evidence": source_manifest["annual_evidence"], "color_policy": source_manifest["color_policy"],
        "preview": {"path": relative(PREVIEW), "sha256": digest(PREVIEW)}, "static_validation": static,
        "privacy": source_manifest["privacy"], "score_v4_change": False, "outcome": "pass",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = build()
    print(json.dumps({"deck": result["output"]["deck"], "changed_slides": result["change"]["changed_stage_ids"], "outcome": result["outcome"]}))
