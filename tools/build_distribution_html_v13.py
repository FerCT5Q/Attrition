"""Agrega BU L3 interna con tasas direccionales sin modificar V11/V12."""
from __future__ import annotations

import copy
import html
import json
import re
import shutil
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

try:
    from . import build_distribution_html_v11 as v11
except ImportError:
    import build_distribution_html_v11 as v11


ROOT = Path(__file__).resolve().parents[1]
SOURCE = v11.OUTPUT
SOURCE_MANIFEST = v11.MANIFEST
EVIDENCE = (
    ROOT
    / "output/distribution/json/attrition-43-variable-distributions-v13-bu-l3-evidence-20261013.json"
)
COLOR_POLICY = ROOT / "config/attrition_color_policy_v8.json"
OUTPUT = ROOT / "output/distribution/attrition-43-variable-distributions-v13.html"
MANIFEST = ROOT / "output/distribution/json/attrition-43-variable-distributions-v13-manifest.json"
PREVIEW = ROOT / "output/preview/bu-l3-v13-20261013/slide-45.html"
TEMPLATE = v11.TEMPLATE

read_json = v11.read_json
require = v11.require
digest = v11.digest
relative = v11.relative


CSS = r"""
    /* V12 · BU L3 distribution and annual attrition. */
    #slide-bu-l3 .v12-bu-card { padding:12px 14px 9px; gap:8px; }
    #slide-bu-l3 .v12-bu-definition {
      display:grid; grid-template-columns:1fr 1fr; gap:8px;
    }
    #slide-bu-l3 .v12-bu-definition > div {
      background:var(--bg-surface-2); border:1px solid var(--border-subtle);
      border-radius:10px; padding:7px 10px; display:flex; gap:8px;
      align-items:baseline; font-size:13px; line-height:1.25;
    }
    #slide-bu-l3 .v12-bu-definition strong { font-size:13px; color:var(--text-main); }
    #slide-bu-l3 .v12-bu-kpis {
      display:grid; grid-template-columns:repeat(4, 1fr); gap:8px;
    }
    #slide-bu-l3 .v12-bu-kpi {
      background:color-mix(in oklab, var(--accent) 7%, var(--bg-surface));
      border:1px solid var(--border-subtle); border-radius:10px;
      padding:6px 10px; display:flex; align-items:baseline; gap:7px;
      min-height:42px;
    }
    #slide-bu-l3 .v12-bu-kpi strong {
      color:var(--accent); font-size:21px; line-height:1; font-variant-numeric:tabular-nums;
    }
    #slide-bu-l3 .v12-bu-kpi span { color:var(--text-muted); font-size:12px; line-height:1.2; }
    #slide-bu-l3 .v12-bu-panels {
      display:grid; grid-template-columns:1fr 1fr; gap:10px; min-height:0; flex:1;
    }
    #slide-bu-l3 .v12-bu-panel {
      min-height:0; border:1px solid var(--border-subtle); border-radius:12px;
      background:color-mix(in oklab, var(--bg-surface) 94%, transparent);
      overflow:hidden; display:flex; flex-direction:column;
    }
    #slide-bu-l3 .v12-bu-panel-head,
    #slide-bu-l3 .v12-bu-row {
      display:grid; grid-template-columns:145px 1fr 92px 94px; gap:7px; align-items:center;
    }
    #slide-bu-l3 .v12-bu-panel-head {
      min-height:28px; padding:4px 8px; background:var(--bg-surface-2);
      color:var(--text-muted); font-size:11px; font-weight:800;
      text-transform:uppercase; letter-spacing:.05em;
    }
    #slide-bu-l3 .v12-bu-panel-head span:nth-child(3),
    #slide-bu-l3 .v12-bu-panel-head span:nth-child(4) { text-align:right; }
    #slide-bu-l3 .v12-bu-row {
      min-height:31px; padding:3px 8px; border-top:1px solid var(--border-subtle);
    }
    #slide-bu-l3 .v12-bu-label {
      font-size:14px; line-height:1.1; font-weight:650; color:var(--text-main);
      overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
    }
    #slide-bu-l3 .v12-bu-track {
      height:8px; border-radius:999px; overflow:hidden; background:var(--bg-surface-3);
    }
    #slide-bu-l3 .v12-bu-fill {
      height:100%; min-width:1px; border-radius:999px;
      background:color-mix(in oklab, var(--accent) 28%, var(--text-muted));
    }
    #slide-bu-l3 .v12-bu-row.is-focus .v12-bu-fill { background:var(--accent); }
    #slide-bu-l3 .v12-bu-current {
      text-align:right; font-size:12px; line-height:1.08; color:var(--text-muted);
      font-variant-numeric:tabular-nums;
    }
    #slide-bu-l3 .v12-bu-current strong { display:block; font-size:14px; color:var(--text-main); }
    #slide-bu-l3 .v12-bu-rate {
      justify-self:end; min-width:82px; text-align:center; padding:3px 7px;
      border-radius:var(--radius-pill); font-size:12px; font-weight:800;
      font-variant-numeric:tabular-nums; border:1px solid var(--border-subtle);
    }
    #slide-bu-l3 .v12-bu-rate.attr-low {
      background:color-mix(in oklab, #22c55e 12%, transparent); color:#16a34a;
      border-color:color-mix(in oklab, #22c55e 28%, var(--border-subtle));
    }
    #slide-bu-l3 .v12-bu-rate.attr-mid {
      background:color-mix(in oklab, var(--accent) 11%, transparent); color:var(--accent);
      border-color:color-mix(in oklab, var(--accent) 25%, var(--border-subtle));
    }
    #slide-bu-l3 .v12-bu-rate.attr-high {
      background:color-mix(in oklab, #f97316 13%, transparent); color:#ea580c;
      border-color:color-mix(in oklab, #f97316 30%, var(--border-subtle));
    }
    #slide-bu-l3 .v12-bu-rate.v8-reference-unavailable {
      color:var(--text-muted); background:color-mix(in oklab, var(--text-muted) 9%, transparent);
    }
    #slide-bu-l3 .v12-bu-footer {
      display:flex; justify-content:space-between; align-items:flex-end; gap:16px;
      border-top:1px solid var(--border-subtle); padding-top:6px;
      color:var(--text-muted); font-size:11px; line-height:1.25;
    }
    #slide-bu-l3 .v12-bu-footer p { margin:0; }
    #slide-bu-l3 .v12-bu-source { max-width:790px; }
    #slide-bu-l3 .v12-bu-legend { text-align:right; max-width:540px; }
"""


def rate_text(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if rounded == rounded.to_integral():
        return f"{int(rounded)}%"
    return f"{rounded:.1f}%"


def share_text(value: Decimal) -> str:
    if value > 0 and value < Decimal("0.05"):
        return "&lt;0.1%"
    return html.escape(rate_text(value))


def render_row(row: dict, max_share: Decimal, reference_rate: Decimal, policy: dict) -> str:
    label = str(row["category_label"])
    share = Decimal(str(row["current_share_percent"]))
    width = Decimal("100") * share / max_share if max_share else Decimal("0")
    current_count = int(row["current_employee_count"])
    baseline_count = int(row["baseline_employee_count"])
    exits = int(row["voluntary_exit_count"])
    status = str(row["publication_status"])
    focus_class = " is-focus" if label == "Tech" else ""

    if status in {"publishable", "directional_voluntary_events_lt_30"}:
        rate = Decimal(str(row["annual_attrition_rate_percent"]))
        color_class = v11.v10.v9.v8.attrition_color_class(rate, reference_rate, policy)
        directional = status == "directional_voluntary_events_lt_30"
        visible_rate = rate_text(rate) + ("*" if directional else "")
        qualifier = " Directional internal estimate because it has fewer than 30 exits." if directional else ""
        tooltip = (
            f"{label}: {rate_text(rate)} annual voluntary attrition; baseline 24 Aug 2025 "
            f"n={baseline_count:,}; strict voluntary exits through 23 Aug 2026={exits:,}.{qualifier}"
        )
    else:
        color_class = "v8-reference-unavailable"
        visible_rate = "Not estimable"
        if baseline_count < 30:
            reason = f"baseline n={baseline_count:,}"
        else:
            reason = f"{exits:,} voluntary exits; at least 30 are required"
        tooltip = f"{label}: annual attrition not estimable ({reason})."

    return (
        f'<div class="v12-bu-row{focus_class}">' 
        f'<div class="v12-bu-label" title="{html.escape(label, quote=True)}">{html.escape(label)}</div>'
        f'<div class="v12-bu-track" aria-hidden="true"><div class="v12-bu-fill" style="width:{width:.4f}%"></div></div>'
        f'<div class="v12-bu-current"><strong>{share_text(share)}</strong>n={current_count:,}</div>'
        f'<span class="v12-bu-rate {color_class}" data-v8-rate-precision="one-decimal" '
        f'title="{html.escape(tooltip, quote=True)}" aria-label="{html.escape(tooltip, quote=True)}">'
        f'{html.escape(visible_rate)}</span></div>'
    )


def render_panel(rows: list[dict], max_share: Decimal, reference_rate: Decimal, policy: dict) -> str:
    body = "".join(render_row(row, max_share, reference_rate, policy) for row in rows)
    return (
        '<section class="v12-bu-panel">'
        '<div class="v12-bu-panel-head"><span>BU L3</span><span>Current distribution</span>'
        '<span>Share / n</span><span>12m attrition</span></div>'
        f'{body}</section>'
    )


def render_stage(evidence: dict, policy: dict) -> str:
    summary = evidence["summary"]
    rows = evidence["categories"]
    require(len(rows) == 24, "V13 espera 24 filas visibles de BU L3.")
    reference_rate = Decimal(str(summary["annual_attrition_rate_percent"]))
    max_share = max(Decimal(str(row["current_share_percent"])) for row in rows)
    publishable = [row for row in rows if row["publication_status"] == "publishable"]
    directional = [row for row in rows if row["publication_status"] == "directional_voluntary_events_lt_30"]
    numeric_rows = publishable + directional
    above = [
        row for row in publishable
        if v11.v10.v9.v8.attrition_color_class(
            Decimal(str(row["annual_attrition_rate_percent"])), reference_rate, policy
        ) == "attr-high"
    ]
    not_estimable = len(rows) - len(numeric_rows)
    top = rows[0]
    require(top["category_label"] == "Tech", "Tech debe ser la BU L3 de mayor headcount.")
    require(len(above) == 3, "La cantidad de BU L3 sobre la referencia cambio.")
    require(len(directional) == 12, "La cantidad de tasas direccionales cambio.")
    require(not_estimable == 1, "Solo Modular debe permanecer sin tasa estimable.")

    panels = render_panel(rows[:12], max_share, reference_rate, policy) + render_panel(
        rows[12:], max_share, reference_rate, policy
    )
    reference_label = rate_text(reference_rate)
    protected_reference = (
        f'<span data-v8-rate-precision="one-decimal">{reference_label}</span>'
    )
    title = (
        "Tech holds 44% of employees; three BU L3s with 30+ exits are above the "
        f"{protected_reference} reference"
    )
    return f'''<div class="slide-stage" id="slide-bu-l3" data-v12-bu-l3="true" lang="en">
      <div class="slide-heading"><div><h2 class="slide-title-text">{title}</h2>
        <p class="slide-subtitle">Current distribution on 23 Aug 2026; annual voluntary attrition follows the 24 Aug 2025 cohort for 12 months</p>
      </div><span class="badge badge-info">Internal analysis</span></div>
      <article class="card card-full v12-bu-card">
        <div class="v12-bu-definition">
          <div><span class="v6-mini-label">Definition</span><strong>Effective-dated BU L3 assigned from each employee's cost center.</strong></div>
          <div><span class="v6-mini-label">Population</span><strong>Active Regular employees, excluding RF360.</strong></div>
        </div>
        <div class="v12-bu-kpis">
          <div class="v12-bu-kpi"><strong>{int(summary['current_distinct_employees']):,}</strong><span>employees in the current distribution</span></div>
          <div class="v12-bu-kpi"><strong>{rate_text(Decimal(str(top['current_share_percent'])))}</strong><span>of employees are mapped to Tech</span></div>
          <div class="v12-bu-kpi"><strong data-v8-rate-precision="one-decimal">{reference_label}</strong><span>overall annual voluntary attrition · {int(summary['voluntary_exit_count']):,} exits</span></div>
          <div class="v12-bu-kpi"><strong>{len(directional)}</strong><span>directional rates shown for internal analysis</span></div>
        </div>
        <div class="v12-bu-panels">{panels}</div>
        <div class="v12-bu-footer">
          <p class="v12-bu-source"><strong>Source:</strong> HRDA · <code>post_hire_monthly_worker_dtls</code> joined as-of to <code>d_department.ude_bu_reporting_l3</code>. Query executed 13 Oct 2026: <code>queries/audits/bu_l3_distribution_attrition_internal_20261013.sql</code>.</p>
          <p class="v12-bu-legend">Bars start at zero and are scaled to the largest BU L3. Six labels with current n&lt;30 are pooled. * Directional: fewer than 30 exits, shown for internal analysis. {not_estimable} rate is gray because no comparable baseline exists. Color reference: {protected_reference}.</p>
        </div>
      </article>
    </div>'''


def add_navigation(deck: str) -> str:
    marker = '\n\n  <div class="side-controls"'
    require(marker in deck, "No se encontro el bloque de temas posterior a la navegacion.")
    navigation_end = deck.index(marker)
    navigation = deck[:navigation_end]
    require(navigation.endswith('</details></div></div>'), "El cierre de navegacion de V11 cambio.")
    addition = (
        '<details class="nav-section" data-section="10"><summary><span class="nav-section-title">'
        'Additional analysis · organization</span><span class="nav-section-range">45</span></summary>'
        '<div class="nav-section-slides"><button class="nav-pill" data-slide="44">'
        '45. BU L3 distribution and attrition</button></div></details>'
    )
    close = '</div></div>'
    navigation = navigation[:-len(close)] + addition + close
    return navigation + deck[navigation_end:]


def write_preview(stage: str, deck_css: str) -> None:
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE, PREVIEW)
    template = PREVIEW.read_text(encoding="utf-8")
    template = re.sub(r'<style>.*?</style>', '<style>' + deck_css + '</style>', template, count=1, flags=re.S)
    template = re.sub(
        r'<div class="slide-stage" id="slide-1">.*?(?=<div class="nav-ctrl")',
        stage + '\n', template, count=1, flags=re.S,
    )
    template = template.replace('[Slide Title]', 'BU L3 distribution and attrition')
    template = template.replace('[First Slide Title]', 'BU L3 distribution and attrition')
    template = template.replace('<html lang="en">', '<html lang="en">', 1)
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
    require(digest(SOURCE) == source_manifest["output"]["deck_sha256"], "V11 no coincide con su manifest.")
    require(evidence["outcome"] == "pass", "La evidencia BU L3 no paso.")
    require(digest(ROOT / evidence["query"]["path"]) == evidence["query"]["sha256"], "Cambio el SQL de BU L3.")

    source = SOURCE.read_text(encoding="utf-8")
    source_stages = list(v11.v10.v9.v8.STAGE_RE.finditer(source))
    require(len(source_stages) == 44, "V11 debe contener 44 slides.")
    stage = render_stage(evidence, policy)

    marker = '<div class="nav-ctrl" id="slide-nav">'
    require(marker in source, "No se encontro la navegacion de V11.")
    deck = source.replace(marker, stage + '\n\n' + marker, 1)
    deck = deck.replace('</style>', CSS + '\n</style>', 1)
    deck = add_navigation(deck)
    deck = deck.replace('Employee Characteristics and Attrition — V11', 'Employee Characteristics and Attrition — V13', 1)
    deck = deck.replace('Slides 24&ndash;44', 'Slides 24&ndash;45', 1)
    deck = deck.replace(
        'Contexto de aplicaciones, lugar de trabajo, QVoice, carrera, compensación y manager.',
        'Contexto de aplicaciones, lugar de trabajo, QVoice, carrera, compensación, manager y BU L3.',
        1,
    )

    after_stages = list(v11.v10.v9.v8.STAGE_RE.finditer(deck))
    require(len(after_stages) == 45, "V13 debe contener 45 slides.")
    before = {match.group("id"): match.group("stage").strip() for match in source_stages}
    after = {match.group("id"): match.group("stage").strip() for match in after_stages}
    changed_existing = [stage_id for stage_id in before if before[stage_id] != after.get(stage_id)]
    require(changed_existing == ["slide-2"], "Solo el indice existente puede cambiar.")
    require("slide-bu-l3" in after, "Falta la nueva slide BU L3.")

    if not OUTPUT.exists():
        shutil.copyfile(TEMPLATE, OUTPUT)
    OUTPUT.write_text(deck, encoding="utf-8")
    deck_css = re.search(r'<style>(.*?)</style>', deck, re.S).group(1)
    write_preview(stage, deck_css)

    static = {
        "deck": v11.static_check(deck),
        "preview": v11.static_check(PREVIEW.read_text(encoding="utf-8")),
    }
    ordered = copy.deepcopy(source_manifest["ordered_stages"])
    ordered.append(
        {
            "slide_number": 45,
            "source_stage_id": "slide-bu-l3",
            "group": "Additional analysis · organization",
            "title": "BU L3 distribution and attrition",
        }
    )
    reader_groups = copy.deepcopy(source_manifest["reader_groups"])
    reader_groups.append(
        {
            "title": "Additional analysis · organization",
            "range": "45",
            "description": "Effective-dated BU L3 distribution and annual attrition",
        }
    )
    manifest = {
        "artifact_type": "internal_attrition_distribution_deck",
        "version": 13,
        "artifact_classification": "internal_analysis",
        "deliverable_mode": "internal_analysis",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "deck": relative(SOURCE),
            "deck_sha256": digest(SOURCE),
            "manifest": relative(SOURCE_MANIFEST),
            "manifest_sha256": digest(SOURCE_MANIFEST),
        },
        "output": {
            "deck": relative(OUTPUT),
            "deck_sha256": digest(OUTPUT),
            "visible_stage_count": 45,
            "navigation_count": 45,
        },
        "change": {
            "added_slide_number": 45,
            "added_stage_id": "slide-bu-l3",
            "changed_existing_stage_ids": changed_existing,
            "description": "Adds the current BU L3 distribution and comparable annual voluntary attrition, including directional internal rates below 30 exits; updates the index and navigation only.",
            "language": "en",
            "language_authority": "Inherited from the user-approved V11 deck.",
            "data_changed": True,
            "v11_scope_changed": False,
        },
        "ordered_stages": ordered,
        "reader_groups": reader_groups,
        "prioritization_rule": source_manifest["prioritization_rule"],
        "authorization": source_manifest["authorization"],
        "bu_l3_evidence": {
            "path": relative(EVIDENCE),
            "sha256": digest(EVIDENCE),
            "query_path": evidence["query"]["path"],
            "query_sha256": evidence["query"]["sha256"],
            "execution_date": evidence["execution_date"],
            "outcome": evidence["outcome"],
        },
        "color_policy": {
            "path": relative(COLOR_POLICY),
            "sha256": digest(COLOR_POLICY),
            "reference": {
                "label": "BU L3 comparable baseline population",
                "eligible_baseline_count": int(evidence["summary"]["baseline_distinct_employees"]),
                "voluntary_exits": int(evidence["summary"]["voluntary_exit_count"]),
                "rate_percent": evidence["summary"]["annual_attrition_rate_percent"],
            },
        },
        "preview": {"path": relative(PREVIEW), "sha256": digest(PREVIEW)},
        "static_validation": static,
        "privacy": {
            "aggregate_only": True,
            "employee_rows_persisted": False,
            "individual_identifiers_persisted": False,
            "minimum_visible_cohort": 30,
            "minimum_events_for_rate": 0,
            "directional_rate_event_threshold": 30,
            "small_bu_labels_pooled": True,
            "bu_l3_exception_used": False,
            "directional_internal_rule_authority": "User explicitly authorized directional rates below 30 exits for this internal playbook on 2026-10-13.",
        },
        "score_v4_change": False,
        "outcome": "pass",
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = build()
    print(
        json.dumps(
            {
                "deck": result["output"]["deck"],
                "added_slide": result["change"]["added_stage_id"],
                "outcome": result["outcome"],
            }
        )
    )
