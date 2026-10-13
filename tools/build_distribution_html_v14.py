"""Añade la distribución BU L3 de Engineering a la V13 sin sobrescribirla."""

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
    from . import build_distribution_html_v13 as v13
except ImportError:
    import build_distribution_html_v13 as v13


ROOT = Path(__file__).resolve().parents[1]
SOURCE = v13.OUTPUT
SOURCE_MANIFEST = v13.MANIFEST
EVIDENCE = ROOT / "output/distribution/json/attrition-43-variable-distributions-v14-engineering-bu-l3-evidence-20261013.json"
AUTHORIZATION = ROOT / "config/bu_l3_internal_analysis_authorization_20261013.json"
COLOR_POLICY = ROOT / "config/attrition_color_policy_v8.json"
OUTPUT = ROOT / "output/distribution/attrition-43-variable-distributions-v14.html"
MANIFEST = ROOT / "output/distribution/json/attrition-43-variable-distributions-v14-manifest.json"
PREVIEW = ROOT / "output/preview/bu-l3-v14-20261013/slide-46.html"
TEMPLATE = v13.TEMPLATE

read_json = v13.read_json
require = v13.require
digest = v13.digest
relative = v13.relative
STAGE_RE = v13.v11.v10.v9.v8.STAGE_RE

CSS = v13.CSS.replace("#slide-bu-l3", "#slide-engineering-bu-l3").replace(
    "/* V12 · BU L3 distribution and annual attrition. */",
    "/* V14 · Engineering BU L3 distribution and annual attrition. */",
)


def render_stage(evidence: dict, policy: dict) -> str:
    summary = evidence["summary"]
    rows = evidence["categories"]
    reference_rate = Decimal(str(summary["annual_attrition_rate_percent"]))
    max_share = max(Decimal(str(row["current_share_percent"])) for row in rows)
    publishable = [row for row in rows if row["publication_status"] == "publishable"]
    directional = [row for row in rows if row["publication_status"] == "directional_voluntary_events_lt_30"]
    numeric_rows = publishable + directional
    stable_above = [
        row for row in publishable
        if v13.v11.v10.v9.v8.attrition_color_class(
            Decimal(str(row["annual_attrition_rate_percent"])), reference_rate, policy
        ) == "attr-high"
    ]
    unavailable = len(rows) - len(numeric_rows)
    top = rows[0]
    require(top["category_label"] == "Tech", "Tech debe ser la BU L3 principal de Engineering.")
    require(len(rows) == 16, "La cantidad de filas Engineering BU L3 cambio.")
    require(len(directional) == 7, "La cantidad de tasas Engineering direccionales cambio.")
    require(len(stable_above) == 2, "La cantidad de tasas Engineering estables sobre referencia cambio.")
    require(unavailable == 2, "La cantidad de tasas Engineering sin baseline cambio.")

    midpoint = (len(rows) + 1) // 2
    panels = v13.render_panel(rows[:midpoint], max_share, reference_rate, policy)
    panels += v13.render_panel(rows[midpoint:], max_share, reference_rate, policy)
    reference_label = v13.rate_text(reference_rate)
    protected_reference = f'<span data-v8-rate-precision="one-decimal">{reference_label}</span>'
    top_share = v13.rate_text(Decimal(str(top["current_share_percent"])))
    pooled_labels = int(summary["current_raw_bu_category_count"]) - (len(rows) - 1)
    title = (
        "Tech holds 52% of engineers; Central Eng and Data Center exceed the "
        f"{protected_reference} reference"
    )
    return f'''<div class="slide-stage" id="slide-engineering-bu-l3" data-v14-engineering-bu-l3="true" lang="en">
      <div class="slide-heading"><div><h2 class="slide-title-text">{title}</h2>
        <p class="slide-subtitle">Engineering population only · current distribution on 23 Aug 2026; annual voluntary attrition follows the 24 Aug 2025 cohort for 12 months</p>
      </div><span class="badge badge-info">Internal analysis</span></div>
      <article class="card card-full v12-bu-card">
        <div class="v12-bu-definition">
          <div><span class="v6-mini-label">Definition</span><strong>Effective-dated BU L3 assigned from each engineer's cost center.</strong></div>
          <div><span class="v6-mini-label">Population</span><strong>Active Regular employees, excluding RF360, with <code>eng_or_noneng = Engineering</code>.</strong></div>
        </div>
        <div class="v12-bu-kpis">
          <div class="v12-bu-kpi"><strong>{int(summary['current_distinct_employees']):,}</strong><span>engineers in the current distribution</span></div>
          <div class="v12-bu-kpi"><strong>{top_share}</strong><span>of engineers are mapped to Tech</span></div>
          <div class="v12-bu-kpi"><strong data-v8-rate-precision="one-decimal">{reference_label}</strong><span>overall annual voluntary attrition · {int(summary['voluntary_exit_count']):,} exits</span></div>
          <div class="v12-bu-kpi"><strong>{len(directional)}</strong><span>directional rates shown for internal analysis</span></div>
        </div>
        <div class="v12-bu-panels">{panels}</div>
        <div class="v12-bu-footer">
          <p class="v12-bu-source"><strong>Source:</strong> HRDA · <code>post_hire_monthly_worker_dtls</code> joined as-of to <code>d_department.ude_bu_reporting_l3</code>. Query executed 13 Oct 2026: <code>queries/audits/engineering_bu_l3_distribution_attrition_internal_20261013.sql</code>.</p>
          <p class="v12-bu-legend">Bars start at zero and are scaled to the largest BU L3. {pooled_labels} labels with current n&lt;30 are pooled. * Directional: fewer than 30 exits, shown for internal analysis. {unavailable} rates are gray because no comparable baseline exists. Color reference: {protected_reference}.</p>
        </div>
      </article>
    </div>'''


def add_navigation(deck: str) -> str:
    old = (
        '<span class="nav-section-range">45</span></summary><div class="nav-section-slides">'
        '<button class="nav-pill" data-slide="44">45. BU L3 distribution and attrition</button>'
        '</div></details>'
    )
    new = (
        '<span class="nav-section-range">45&ndash;46</span></summary><div class="nav-section-slides">'
        '<button class="nav-pill" data-slide="44">45. BU L3 distribution and attrition</button>'
        '<button class="nav-pill" data-slide="45">46. Engineering BU L3 distribution and attrition</button>'
        '</div></details>'
    )
    require(old in deck, "La navegacion final de V13 cambio.")
    return deck.replace(old, new, 1)


def write_preview(stage: str, deck_css: str) -> None:
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE, PREVIEW)
    template = PREVIEW.read_text(encoding="utf-8")
    template = re.sub(r'<style>.*?</style>', '<style>' + deck_css + '</style>', template, count=1, flags=re.S)
    template = re.sub(
        r'<div class="slide-stage" id="slide-1">.*?(?=<div class="nav-ctrl")',
        stage + '\n', template, count=1, flags=re.S,
    )
    template = template.replace('[Slide Title]', 'Engineering BU L3 distribution and attrition')
    template = template.replace('[First Slide Title]', 'Engineering BU L3 distribution and attrition')
    template = template.replace(
        'class="theme-light-classic">',
        'class="theme-light-classic" data-deliverable-mode="internal_analysis">',
        1,
    )
    template = template.replace(
        '</head>', '<meta name="deliverable-classification" content="internal_analysis" /></head>', 1
    )
    PREVIEW.write_text(template, encoding="utf-8")


def build() -> dict:
    source_manifest = read_json(SOURCE_MANIFEST)
    evidence = read_json(EVIDENCE)
    policy = read_json(COLOR_POLICY)
    require(digest(SOURCE) == source_manifest["output"]["deck_sha256"], "V13 no coincide con su manifest.")
    require(evidence["outcome"] == "pass", "La evidencia Engineering BU L3 no paso.")
    require(digest(ROOT / evidence["query"]["path"]) == evidence["query"]["sha256"], "Cambio el SQL Engineering BU L3.")
    require(digest(AUTHORIZATION) == evidence["authorization"]["sha256"], "Cambio la autorizacion interna BU L3.")

    source = SOURCE.read_text(encoding="utf-8")
    source_stages = list(STAGE_RE.finditer(source))
    require(len(source_stages) == 45, "V13 debe contener 45 slides.")
    stage = render_stage(evidence, policy)
    marker = '<div class="nav-ctrl" id="slide-nav">'
    require(marker in source, "No se encontro la navegacion de V13.")
    deck = source.replace(marker, stage + '\n\n' + marker, 1)
    deck = deck.replace('</style>', CSS + '\n</style>', 1)
    deck = add_navigation(deck)
    deck = deck.replace('Employee Characteristics and Attrition — V13', 'Employee Characteristics and Attrition — V14', 1)
    deck = deck.replace('Slides 24&ndash;45', 'Slides 24&ndash;46', 1)
    deck = deck.replace(
        'Contexto de aplicaciones, lugar de trabajo, QVoice, carrera, compensación, manager y BU L3.',
        'Contexto de aplicaciones, lugar de trabajo, QVoice, carrera, compensación, manager y BU L3 para total y Engineering.',
        1,
    )

    after_stages = list(STAGE_RE.finditer(deck))
    require(len(after_stages) == 46, "V14 debe contener 46 slides.")
    before = {match.group("id"): match.group("stage").strip() for match in source_stages}
    after = {match.group("id"): match.group("stage").strip() for match in after_stages}
    changed_existing = [stage_id for stage_id in before if before[stage_id] != after.get(stage_id)]
    require(changed_existing == ["slide-2"], "Solo el indice existente puede cambiar.")
    require("slide-engineering-bu-l3" in after, "Falta la slide Engineering BU L3.")

    if not OUTPUT.exists():
        shutil.copyfile(TEMPLATE, OUTPUT)
    OUTPUT.write_text(deck, encoding="utf-8")
    deck_css = re.search(r'<style>(.*?)</style>', deck, re.S).group(1)
    write_preview(stage, deck_css)
    static = {
        "deck": v13.v11.static_check(deck),
        "preview": v13.v11.static_check(PREVIEW.read_text(encoding="utf-8")),
    }

    ordered = copy.deepcopy(source_manifest["ordered_stages"])
    ordered.append({
        "slide_number": 46,
        "source_stage_id": "slide-engineering-bu-l3",
        "group": "Additional analysis · organization",
        "title": "Engineering BU L3 distribution and attrition",
    })
    reader_groups = copy.deepcopy(source_manifest["reader_groups"])
    reader_groups[-1]["range"] = "45–46"
    reader_groups[-1]["description"] = "Effective-dated BU L3 distribution and annual attrition for the total and Engineering populations"

    manifest = {
        "artifact_type": "internal_attrition_distribution_deck",
        "version": 14,
        "artifact_classification": "internal_analysis",
        "deliverable_mode": "internal_analysis",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "deck": relative(SOURCE), "deck_sha256": digest(SOURCE),
            "manifest": relative(SOURCE_MANIFEST), "manifest_sha256": digest(SOURCE_MANIFEST),
        },
        "output": {
            "deck": relative(OUTPUT), "deck_sha256": digest(OUTPUT),
            "visible_stage_count": 46, "navigation_count": 46,
        },
        "change": {
            "added_slide_number": 46,
            "added_stage_id": "slide-engineering-bu-l3",
            "changed_existing_stage_ids": changed_existing,
            "description": "Adds the same BU L3 distribution and annual attrition view filtered to eng_or_noneng = Engineering.",
            "language": "en",
            "language_authority": "Inherited from the user-approved V11 deck.",
            "data_changed": True,
            "v11_scope_changed": False,
        },
        "ordered_stages": ordered,
        "reader_groups": reader_groups,
        "prioritization_rule": source_manifest["prioritization_rule"],
        "authorization": source_manifest["authorization"],
        "engineering_bu_l3_evidence": {
            "path": relative(EVIDENCE), "sha256": digest(EVIDENCE),
            "query_path": evidence["query"]["path"], "query_sha256": evidence["query"]["sha256"],
            "execution_date": evidence["execution_date"], "outcome": evidence["outcome"],
        },
        "engineering_bu_l3_authorization": {
            "path": relative(AUTHORIZATION), "sha256": digest(AUTHORIZATION),
        },
        "color_policy": source_manifest["color_policy"],
        "preview": {"path": relative(PREVIEW), "sha256": digest(PREVIEW)},
        "static_validation": static,
        "privacy": {
            "aggregate_only": True,
            "employee_rows_persisted": False,
            "individual_identifiers_persisted": False,
            "minimum_visible_named_cohort": 30,
            "pooled_other_below_30_authorized": True,
            "directional_rate_event_threshold": 30,
            "small_bu_labels_pooled": True,
        },
        "score_v4_change": False,
        "outcome": "pass",
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = build()
    print(json.dumps({"deck": result["output"]["deck"], "added_slide": result["change"]["added_stage_id"], "outcome": result["outcome"]}))
