"""Build the active annual Voluntary attrition view for prior experience.

The script re-executes the frozen aggregate SQL through the guarded Attrition
Redshift helper, writes an aggregate evidence JSON, and inserts one new
Plotly-based slide into the reviewed v2 deck after an explicit baseline-hash
check.
"""

from __future__ import annotations

import copy
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "distribution"
V2_HTML = OUT / "attrition-43-variable-distributions-v2.html"
V2_MANIFEST = OUT / "json" / "attrition-43-variable-distributions-v2-manifest.json"
ACTIVE_HTML = OUT / "attrition-43-variable-distributions-v2.html"
ACTIVE_MANIFEST = OUT / "json" / "attrition-43-variable-distributions-v2-manifest.json"
EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.prior-experience-annual-attrition-evidence-20260911.json"
MAIN_SQL = ROOT / "queries" / "audits" / "prior_experience_annual_voluntary_attrition_20260911.sql"
GAP_SQL = ROOT / "queries" / "audits" / "prior_experience_annual_voluntary_attrition_gap_20260911.sql"
TEMPLATE = Path(r"C:\Users\fcarranz\.codex\skills\html-slide-generator\templates\fullscreen\base-fullscreen.html")
QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
CUTOFF = "2026-09-11"
MINIMUM_COHORT = 30
EXPECTED_BASELINE_HTML_SHA256 = "b60cbe5fb394408facafcde602e1816a8b6f0b286a4c559367b7c2b5edd05e8d"
EXPECTED_BASELINE_MANIFEST_SHA256 = "9b5f36066971cb3bb80847240ccb10dd07af985201275231f2ce671268820429"
BANDS = ["0", ">0–<1", "1–<3", "3–<5", "5–<10", "10–<15", "15+"]
BAND_ORDER = {band: index for index, band in enumerate(BANDS)}


def run_query(sql_path: Path) -> dict[str, Any]:
    command = [
        str(PYTHON),
        "-B",
        str(QUERY_HELPER),
        "--sql-file",
        str(sql_path),
        "--max-rows",
        "100",
        "--reporting-mode",
        "internal_analysis",
    ]
    completed = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def result_hash(result: dict[str, Any]) -> str:
    canonical = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(canonical)


def number(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = row.get(key)
    if value is None or value == "":
        return default
    return float(value)


def integer(row: dict[str, Any], key: str, default: int = 0) -> int:
    return int(round(number(row, key, default)))


def build_metrics(main_result: dict[str, Any], gap_result: dict[str, Any]) -> dict[str, Any]:
    rows = main_result["rows"]
    calendar = sorted((row for row in rows if row["row_type"] == "calendar"), key=lambda row: int(row["fiscal_year"]))
    band_rows = sorted(
        (row for row in rows if row["row_type"] == "band_year"),
        key=lambda row: (int(row["fiscal_year"]), BAND_ORDER.get(row["band_or_metric"], 999)),
    )
    reconciliation = sorted(
        (row for row in rows if row["row_type"] == "reconciliation"),
        key=lambda row: int(row["fiscal_year"]),
    )
    source_domain = next(row for row in rows if row["row_type"] == "source_domain")
    gap_rows = gap_result["rows"]

    years = [int(row["fiscal_year"]) for row in calendar]
    annual = []
    by_year_band: dict[int, dict[str, dict[str, Any]]] = {}
    for row in band_rows:
        year = int(row["fiscal_year"])
        by_year_band.setdefault(year, {})[row["band_or_metric"]] = row
        annual.append(
            {
                "fiscal_year": year,
                "band": row["band_or_metric"],
                "annual_voluntary_attrition_percent": number(row, "annual_voluntary_attrition_percent"),
                "voluntary_exit_events": integer(row, "voluntary_exit_events"),
                "average_monthly_headcount": number(row, "average_monthly_headcount"),
                "annual_distinct_employees": integer(row, "annual_distinct_employees"),
                "min_monthly_headcount": integer(row, "min_monthly_headcount"),
                "months_checked": integer(row, "months_checked"),
                "months_with_headcount": integer(row, "months_with_headcount"),
                "privacy_eligible": bool(integer(row, "privacy_eligible")),
            }
        )

    reconciliations = []
    for row in reconciliation:
        total = integer(row, "total_voluntary_events")
        attributed = integer(row, "attributed_voluntary_events")
        reconciliations.append(
            {
                "fiscal_year": int(row["fiscal_year"]),
                "total_voluntary_events": total,
                "attributed_voluntary_events": attributed,
                "unattributed_voluntary_events": integer(row, "unattributed_voluntary_events"),
                "sum_of_band_events": integer(row, "sum_of_band_events"),
                "sum_of_published_band_events": integer(row, "sum_of_published_band_events"),
                "attribution_coverage_percent": round(100.0 * attributed / total, 4) if total else None,
            }
        )

    gap_reasons = [
        {
            "fiscal_year": int(row["fiscal_year"]),
            "reason": row["metric"],
            "voluntary_events": integer(row, "voluntary_events"),
        }
        for row in gap_rows
        if row["row_type"] == "unresolved_reason"
    ]
    gap_domain = [
        {
            "fiscal_year": int(row["fiscal_year"]),
            "active_employee_snapshots": integer(row, "active_employee_snapshots"),
            "null_active_snapshots": integer(row, "null_active_snapshots"),
            "negative_active_snapshots": integer(row, "negative_active_snapshots"),
        }
        for row in gap_rows
        if row["row_type"] == "domain_by_year"
    ]

    all_cells_privacy_eligible = all(item["privacy_eligible"] for item in annual)
    calendar_pass = (
        len(years) == 5
        and integer(source_domain, "selected_period_count") == 60
        and integer(source_domain, "selected_snapshot_count") == 60
        and integer(source_domain, "selected_fiscal_year_count") == 5
        and integer(source_domain, "future_selected_periods") == 0
    )
    denominator_pass = all(
        item["months_checked"] == 12
        and item["months_with_headcount"] == 12
        and item["annual_distinct_employees"] >= MINIMUM_COHORT
        and item["min_monthly_headcount"] >= MINIMUM_COHORT
        for item in annual
    )
    band_quality_pass = integer(source_domain, "dates_with_duplicate_employee_rows") == 0
    exact_reconciliation = all(item["unattributed_voluntary_events"] == 0 for item in reconciliations)
    attribution_coverage = [item["attribution_coverage_percent"] for item in reconciliations if item["attribution_coverage_percent"] is not None]
    invalid_active_snapshots = integer(source_domain, "negative_value_rows") + integer(source_domain, "null_value_rows")
    overall_outcome = "pass" if calendar_pass and denominator_pass and band_quality_pass and exact_reconciliation and invalid_active_snapshots == 0 else "warning"

    return {
        "selected_fiscal_years": years,
        "calendar": [
            {
                "fiscal_year": int(row["fiscal_year"]),
                "snapshot_count": integer(row, "snapshot_count"),
                "fiscal_month_count": integer(row, "fiscal_month_count"),
                "min_fiscal_month": integer(row, "min_fiscal_month"),
                "max_fiscal_month": integer(row, "max_fiscal_month"),
                "first_period_begin": row["first_period_begin"],
                "last_snapshot_date": row["last_snapshot_date"],
            }
            for row in calendar
        ],
        "annual": annual,
        "reconciliation": reconciliations,
        "gap_reasons": gap_reasons,
        "gap_domain_by_year": gap_domain,
        "source_domain": {
            "dated_termination_events": integer(source_domain, "dated_termination_events"),
            "employees_with_missing_term_date": integer(source_domain, "employees_with_missing_term_date"),
            "voluntary_events": integer(source_domain, "voluntary_events"),
            "involuntary_events": integer(source_domain, "involuntary_events"),
            "voluntary_exception_events": integer(source_domain, "voluntary_exception_events"),
            "other_or_missing_type_events": integer(source_domain, "other_or_missing_type_events"),
            "all_employee_snapshot_dates_checked": integer(source_domain, "all_employee_snapshot_dates_checked"),
            "dates_with_duplicate_employee_rows": integer(source_domain, "dates_with_duplicate_employee_rows"),
            "negative_active_snapshot_rows": integer(source_domain, "negative_value_rows"),
            "null_active_snapshot_rows": integer(source_domain, "null_value_rows"),
            "selected_period_count": integer(source_domain, "selected_period_count"),
            "selected_snapshot_count": integer(source_domain, "selected_snapshot_count"),
            "selected_fiscal_year_count": integer(source_domain, "selected_fiscal_year_count"),
            "first_selected_snapshot": source_domain["first_selected_snapshot"],
            "last_selected_snapshot": source_domain["last_selected_snapshot"],
            "future_selected_periods": integer(source_domain, "future_selected_periods"),
        },
        "acceptance": {
            "calendar_complete": calendar_pass,
            "bands_mutually_exclusive_for_valid_values": band_quality_pass,
            "denominators_and_privacy": denominator_pass,
            "exact_event_reconciliation": exact_reconciliation,
            "invalid_or_missing_field_values_absent": invalid_active_snapshots == 0,
            "all_published_cells_n_ge_30": all_cells_privacy_eligible,
            "published_cell_count": len(annual),
            "suppressed_cell_count": sum(1 for item in annual if not item["privacy_eligible"]),
            "minimum_attribution_coverage_percent": min(attribution_coverage) if attribution_coverage else None,
        },
        "outcome": overall_outcome,
        "by_year_band": by_year_band,
    }


def slide_html(metrics: dict[str, Any]) -> str:
    years = metrics["selected_fiscal_years"]
    annual = metrics["annual"]
    coverage = {item["fiscal_year"]: item["attribution_coverage_percent"] for item in metrics["reconciliation"]}
    rates: dict[str, list[float | None]] = {str(year): [] for year in years}
    details: dict[str, list[list[Any]]] = {str(year): [] for year in years}
    by_key = {(item["fiscal_year"], item["band"]): item for item in annual}
    for year in years:
        for band in BANDS:
            item = by_key[(year, band)]
            rates[str(year)].append(item["annual_voluntary_attrition_percent"] if item["privacy_eligible"] else None)
            details[str(year)].append(
                [
                    item["voluntary_exit_events"],
                    item["average_monthly_headcount"],
                    item["annual_distinct_employees"],
                    coverage.get(year),
                ]
            )
    payload = {"years": years, "bands": BANDS, "rates": rates, "details": details}
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    coverage_values = [value for value in coverage.values() if value is not None]
    coverage_text = " · ".join(f"FY{year}: {coverage[year]:.1f}%" for year in years)
    invalid = metrics["source_domain"]["negative_active_snapshot_rows"] + metrics["source_domain"]["null_active_snapshot_rows"]

    return f'''  <div class="slide-stage" id="slide-17">
    <div class="slide-heading"><div><h2 class="slide-title-text">Annual voluntary attrition by prior experience</h2><p class="slide-subtitle">FY{years[0]}–FY{years[-1]} · asociación descriptiva · cinco años fiscales completos</p></div><span class="badge badge-warning">Asociación descriptiva</span></div>
    <div class="two-pane prior-experience-annual-layout">
      <article class="card chart-card prior-experience-annual-chart-card">
        <div class="card-title">Tasa anual de salida Voluntary por banda de experiencia almacenada</div>
        <div id="prior-experience-annual-chart" aria-label="Tasa anual de salida Voluntary por banda de experiencia previa"></div>
        <div class="chart-footer">Tasa = salidas Voluntary atribuidas a la última banda válida previa a la terminación ÷ headcount activo mensual promedio de la banda × 100. Las barras son tasas agregadas; el detalle emergente muestra eventos y denominadores.</div>
      </article>
      <article class="card side-copy prior-experience-annual-side">
        <div class="card-title">Definición y límites</div>
        <span class="badge badge-info">Agregado seguro para análisis interno</span>
        <h3>Las bandas de experiencia se mantienen fijas</h3>
        <p>Cada fila representa una banda almacenada de <code>prior_qc_work_years</code>. Los años no se reagruparon después de observar los resultados.</p>
        <ul class="fact-list">
          <li><strong>Bandas:</strong> 0 · &gt;0–&lt;1 · 1–&lt;3 · 3–&lt;5 · 5–&lt;10 · 10–&lt;15 · 15+</li>
          <li><strong>Población:</strong> Employee / Regular / Active en snapshots mensuales</li>
          <li><strong>Cobertura:</strong> 12 snapshots por año fiscal; n ≥ 30 por celda publicada</li>
          <li><strong>Eventos:</strong> Sólo <code>term_type=VOLUNTARY</code> con <code>term_date</code>; se excluyen Involuntary, Voluntary Exception y categorías inválidas</li>
          <li><strong>Atribución:</strong> {html.escape(coverage_text)}</li>
          <li><strong>Filas inválidas excluidas:</strong> {invalid:,} snapshots activos negativos o nulos</li>
        </ul>
        <p class="scope-note"><strong>Lectura:</strong> Las diferencias son descriptivas y asociativas. No demuestran causalidad, riesgo individual ni un score de modelo.</p>
        <section class="provenance-panel"><div class="provenance-title">Procedencia y alcance</div>
          <dl class="provenance-grid"><dt>Fuente</dt><dd>HRDA</dd><dt>Tabla</dt><dd>hrda.post_hire_monthly_worker_dtls</dd><dt>Grain</dt><dd>Headcount empleado-snapshot; atribución del evento de terminación</dd><dt>Campo</dt><dd>prior_qc_work_years</dd></dl>
          <p class="provenance-status"><strong>Importante:</strong> <code>prior_qc_work_years</code> es un campo almacenado; su lineage y fórmula de negocio aún requieren confirmación. Los eventos sin snapshot válido previo no se reasignan.</p>
        </section>
      </article>
    </div>
  </div>'''


def chart_css() -> str:
    return '''
    .prior-experience-annual-layout { grid-template-columns: minmax(0, 1.72fr) minmax(360px, .88fr); gap: 14px; }
    .prior-experience-annual-chart-card { padding: 12px 14px; gap: 6px; }
    #prior-experience-annual-chart { width: 100%; height: 555px; min-height: 555px; }
    .prior-experience-annual-chart-card .chart-footer { padding-top: 7px; font-size: 11px; line-height: 1.3; }
    .prior-experience-annual-side { padding: 14px 16px; gap: 7px; }
    .prior-experience-annual-side h3 { font-size: 18px; }
    .prior-experience-annual-side p { font-size: 13px; line-height: 1.35; }
    .prior-experience-annual-side .fact-list { gap: 5px; }
    .prior-experience-annual-side .fact-list li { font-size: 12px; line-height: 1.25; }
    .prior-experience-annual-side .provenance-panel { padding-top: 7px; }
    .prior-experience-annual-side .provenance-status { font-size: 10.5px; line-height: 1.25; }
'''


def chart_script(metrics: dict[str, Any]) -> str:
    payload = {"years": metrics["selected_fiscal_years"], "bands": BANDS}
    by_key = {(item["fiscal_year"], item["band"]): item for item in metrics["annual"]}
    payload["rates"] = {
        str(year): [
            by_key[(year, band)]["annual_voluntary_attrition_percent"]
            if by_key[(year, band)]["privacy_eligible"]
            else None
            for band in BANDS
        ]
        for year in metrics["selected_fiscal_years"]
    }
    coverage = {item["fiscal_year"]: item["attribution_coverage_percent"] for item in metrics["reconciliation"]}
    payload["details"] = {
        str(year): [
            [
                by_key[(year, band)]["voluntary_exit_events"],
                by_key[(year, band)]["average_monthly_headcount"],
                by_key[(year, band)]["annual_distinct_employees"],
                coverage.get(year),
            ]
            for band in BANDS
        ]
        for year in metrics["selected_fiscal_years"]
    }
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f'''  <script>
    (function () {{
      var priorExperienceAttritionPayload = {payload_json};

      function getThemeColors() {{
        var styles = getComputedStyle(document.body);
        return {{
          bg: styles.getPropertyValue('--bg-body').trim() || '#f4f5f8',
          surface: styles.getPropertyValue('--bg-surface').trim() || '#ffffff',
          text: styles.getPropertyValue('--text-main').trim() || '#0f172a',
          muted: styles.getPropertyValue('--text-muted').trim() || '#5b6478',
          accent: styles.getPropertyValue('--accent').trim() || '#2457ff',
          accent2: styles.getPropertyValue('--accent-2').trim() || '#3b82f6',
          border: styles.getPropertyValue('--border-subtle').trim() || 'rgba(15,23,42,0.08)',
          font: 'Aptos, Segoe UI, system-ui, sans-serif'
        }};
      }}

      function hexToRgb(value) {{
        var hex = String(value || '').trim().replace(/^#/, '');
        if (hex.length === 3) hex = hex.split('').map(function (part) {{ return part + part; }}).join('');
        if (!/^[0-9a-f]{{6}}$/i.test(hex)) return null;
        return [parseInt(hex.slice(0, 2), 16), parseInt(hex.slice(2, 4), 16), parseInt(hex.slice(4, 6), 16)];
      }}

      function blend(surface, accent, weight) {{
        var base = hexToRgb(surface), highlight = hexToRgb(accent);
        if (!base || !highlight) return accent;
        return 'rgb(' + base.map(function (value, index) {{ return Math.round(value + (highlight[index] - value) * weight); }}).join(',') + ')';
      }}

      function renderChart() {{
        var chart = document.getElementById('prior-experience-annual-chart');
        if (!chart || !window.Plotly) return;
        var theme = getThemeColors();
        var weights = [1.00, 0.82, 0.66, 0.50, 0.35];
        var traces = priorExperienceAttritionPayload.years.map(function (year, index) {{
          var values = priorExperienceAttritionPayload.rates[String(year)];
          var details = priorExperienceAttritionPayload.details[String(year)];
          return {{
            type: 'bar',
            orientation: 'h',
            name: 'FY' + year,
            y: priorExperienceAttritionPayload.bands,
            x: values,
            customdata: details,
            marker: {{ color: blend(theme.surface, index < 2 ? theme.accent : theme.accent2, weights[index]) }},
            text: values.map(function (value) {{ return value === null ? '' : value.toFixed(1) + '%'; }}),
            texttemplate: '%{{text}}',
            textposition: 'outside',
            textfont: {{ family: theme.font, size: 9, color: theme.text }},
            cliponaxis: false,
            hovertemplate: '<b>%{{y}}</b><br>FY' + year + '<br>Tasa: <b>%{{x:.2f}}%</b><br>Salidas Voluntary atribuidas: %{{customdata[0]:,}}<br>Headcount mensual promedio: %{{customdata[1]:,.1f}}<br>Empleados distintos en el año: %{{customdata[2]:,}}<br>Cobertura de atribución: %{{customdata[3]:.1f}}%<extra></extra>'
          }};
        }});
        Plotly.react(chart, traces, {{
          height: 555,
          barmode: 'group',
          bargap: 0.24,
          bargroupgap: 0.08,
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          font: {{ family: theme.font, color: theme.text }},
          margin: {{ t: 24, r: 72, b: 50, l: 86 }},
          legend: {{ orientation: 'h', x: 0, y: 1.08, font: {{ family: theme.font, size: 10, color: theme.text }}, bgcolor: 'rgba(0,0,0,0)' }},
          xaxis: {{ title: {{ text: 'Tasa de salida Voluntary anual (%)', font: {{ family: theme.font, size: 11, color: theme.muted }} }}, ticksuffix: '%', rangemode: 'tozero', fixedrange: true, gridcolor: theme.border, zerolinecolor: theme.border, tickfont: {{ family: theme.font, size: 10, color: theme.muted }} }},
          yaxis: {{ categoryorder: 'array', categoryarray: priorExperienceAttritionPayload.bands, autorange: 'reversed', fixedrange: true, tickfont: {{ family: theme.font, size: 11, color: theme.text }}, gridcolor: 'rgba(0,0,0,0)', zeroline: false }},
          hovermode: 'closest'
        }}, {{ responsive: false, displayModeBar: false }});
      }}

      renderChart();
      new MutationObserver(function (records) {{
        if (records.some(function (record) {{ return record.attributeName === 'class'; }})) renderChart();
      }}).observe(document.body, {{ attributes: true, attributeFilter: ['class'] }});
    }})();
  </script>
'''


def shift_stage_ids(document: str) -> str:
    # Keep the replacement explicit so it cannot alter numeric IDs in content.
    pattern = re.compile(r'(<div class="slide-stage" id="slide-)(\d+)(")')
    return pattern.sub(lambda match: f"{match.group(1)}{int(match.group(2)) + 1 if int(match.group(2)) >= 17 else int(match.group(2))}{match.group(3)}", document)


def shift_navigation(document: str) -> str:
    pattern = re.compile(r'(<button class="nav-pill(?: pill-active)?" data-slide=")(\d+)(">)(\d+)\. ([^<]*)(</button>)')

    def replace(match: re.Match[str]) -> str:
        slide_index = int(match.group(2))
        slide_number = int(match.group(4))
        if slide_index >= 16:
            slide_index += 1
            slide_number += 1
        return f"{match.group(1)}{slide_index}{match.group(3)}{slide_number}. {match.group(5)}{match.group(6)}"

    return pattern.sub(replace, document)


def add_navigation_button(document: str) -> str:
    old_button = '<button class="nav-pill" data-slide="15">16. Prior experience</button>'
    new_button = old_button + '\n          <button class="nav-pill" data-slide="16">17. Annual voluntary attrition by prior experience</button>'
    if old_button not in document:
        raise ValueError("The v2 navigation did not contain the expected prior-experience button.")
    return document.replace(old_button, new_button, 1)


def update_agenda(document: str) -> str:
    replacements = {
        "Slides 5–17": "Slides 5–18",
        "Slides 18–25": "Slides 19–26",
        "Slides 26–37": "Slides 27–38",
        "Slides 38–46": "Slides 39–47",
    }
    for old, new in replacements.items():
        document = document.replace(old, new)
    return document


def build_html(metrics: dict[str, Any]) -> str:
    if not V2_HTML.exists() or not V2_MANIFEST.exists():
        raise FileNotFoundError("The active v2 deck and manifest are required before integration.")
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"The required fullscreen template is missing: {TEMPLATE}")
    template_text = TEMPLATE.read_text(encoding="utf-8")
    for required in ("theme-light-classic", "theme-light-soft", "theme-dark-royal", "theme-dark-carbon", "showSlide(0)"):
        if required not in template_text:
            raise ValueError(f"The fullscreen template is missing required marker: {required}")

    document = V2_HTML.read_text(encoding="utf-8")
    if len(re.findall(r'<div class="slide-stage" id="slide-\d+"', document)) != 46:
        raise ValueError("The v2 deck must contain exactly 46 slide stages.")
    if len(re.findall(r'<button class="nav-pill(?: pill-active)?" data-slide="\d+">', document)) != 46:
        raise ValueError("The v2 deck must contain exactly 46 navigation pills.")

    document = shift_stage_ids(document)
    document = shift_navigation(document)
    document = add_navigation_button(document)
    document = update_agenda(document)

    marker = "    /* 13. CONTENT-SPECIFIC STYLES"
    if marker not in document:
        raise ValueError("The v2 deck is not based on the required content-specific style section.")
    document = document.replace(marker, chart_css() + "\n" + marker, 1)

    stage17 = slide_html(metrics)
    insertion_marker = '\n\n  <div class="slide-stage" id="slide-18"'
    if insertion_marker not in document:
        raise ValueError("The shifted v2 deck did not expose slide-18 as the insertion point.")
    document = document.replace(insertion_marker, "\n\n" + stage17 + insertion_marker, 1)

    document = document.replace("\n</body>", "\n" + chart_script(metrics) + "</body>", 1)
    if "https://cdn.plot.ly/plotly-2.27.0.min.js" not in document:
        document = document.replace("</style>", "</style>\n  <script src=\"https://cdn.plot.ly/plotly-2.27.0.min.js\"></script>", 1)

    stages = re.findall(r'<div class="slide-stage" id="(slide-\d+)"', document)
    nav = re.findall(r'<button class="nav-pill(?: pill-active)?" data-slide="(\d+)">', document)
    if stages != [f"slide-{index}" for index in range(1, 48)]:
        raise ValueError(f"Unexpected active stage IDs: {stages[:3]} ... {stages[-3:]}")
    if [int(value) for value in nav] != list(range(47)):
        raise ValueError(f"Unexpected active navigation indices: {nav[:3]} ... {nav[-3:]}")
    return document


def build_manifest(
    metrics: dict[str, Any],
    main_result: dict[str, Any],
    gap_result: dict[str, Any],
    baseline_html_sha256: str,
    baseline_manifest_sha256: str,
) -> dict[str, Any]:
    base = json.loads(V2_MANIFEST.read_text(encoding="utf-8"))
    manifest = copy.deepcopy(base)
    manifest["version"] = 2
    manifest["generated_on"] = CUTOFF
    manifest["slide_count"] = 47
    manifest["deliverable_mode"] = "internal_analysis"
    manifest["source_runs"] = list(manifest.get("source_runs", [])) + [
        "prior-experience-annual-voluntary-attrition-20260911"
    ]
    manifest["aggregate_evidence_builders"] = list(manifest.get("aggregate_evidence_builders", [])) + [
        "tools/build_prior_experience_annual_attrition.py"
    ]
    manifest["new_aggregate_audits"] = list(manifest.get("new_aggregate_audits", [])) + [
        "queries/audits/prior_experience_annual_voluntary_attrition_20260911.sql",
        "queries/audits/prior_experience_annual_voluntary_attrition_gap_20260911.sql",
    ]
    slides = []
    for item in manifest.get("slides", []):
        slide = copy.deepcopy(item)
        if int(slide["slide"]) >= 17:
            slide["slide"] = int(slide["slide"]) + 1
        slides.append(slide)
        if int(item["slide"]) == 16:
            slides.append({"slide": 17, "title": "Annual voluntary attrition by prior experience"})
    manifest["slides"] = slides
    manifest["frozen_evidence"]["prior_experience_annual_voluntary_attrition"] = {
        "evidence": EVIDENCE.relative_to(ROOT).as_posix(),
        "profile_or_audit_query": MAIN_SQL.relative_to(ROOT).as_posix(),
        "gap_audit_query": GAP_SQL.relative_to(ROOT).as_posix(),
        "query_sha256": sha256_bytes(MAIN_SQL.read_bytes()),
        "query_result_sha256": result_hash(main_result),
        "gap_query_sha256": sha256_bytes(GAP_SQL.read_bytes()),
        "gap_result_sha256": result_hash(gap_result),
        "execution_date": CUTOFF,
        "reporting_mode": "internal_analysis",
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1 for monthly headcount and pre-termination band history",
        "grain": "Band-year; average monthly active headcount denominator and Voluntary termination event numerator",
        "outcome": metrics["outcome"],
    }
    manifest["active_slide"] = {
        "slide": 17,
        "title": "Annual voluntary attrition by prior experience",
        "reporting_mode": "internal_analysis",
        "query": MAIN_SQL.relative_to(ROOT).as_posix(),
        "evidence": EVIDENCE.relative_to(ROOT).as_posix(),
        "outcome": metrics["outcome"],
        "interpretation": "Descriptive/asociativa; no causalidad ni predicción individual.",
        "field_lineage": "prior_qc_work_years es stored/precomputed; lineage pendiente.",
    }
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": 46,
        "output_slide_count": 47,
        "baseline_html_sha256": baseline_html_sha256,
        "baseline_manifest_sha256": baseline_manifest_sha256,
        "structural_change": "Inserted slide 17 and shifted legacy slides 17–46 to 18–47; legacy content payloads preserved.",
        "new_slide": 17,
        "legacy_payloads_preserved": True,
        "navigation_consecutive": True,
        "outcome": "pass",
    }
    return manifest


def main() -> None:
    main_result = run_query(MAIN_SQL)
    gap_result = run_query(GAP_SQL)
    metrics = build_metrics(main_result, gap_result)
    evidence = {
        "version": 2,
        "variable": "Years of experience prior to Qualcomm",
        "field": "prior_qc_work_years",
        "semantic_type": "precomputed_metric",
        "reporting_mode": "internal_analysis",
        "generated_on": CUTOFF,
        "executed_on": CUTOFF,
        "cutoff_date": CUTOFF,
        "query": MAIN_SQL.relative_to(ROOT).as_posix(),
        "query_sha256": sha256_bytes(MAIN_SQL.read_bytes()),
        "result_sha256": result_hash(main_result),
        "gap_query": GAP_SQL.relative_to(ROOT).as_posix(),
        "gap_query_sha256": sha256_bytes(GAP_SQL.read_bytes()),
        "gap_result_sha256": result_hash(gap_result),
        "population": "Empleados regulares activos para headcount e historia previa: worker_type='Employee'; employee_type='Regular'; active_status=1.",
        "grain": "Headcount mensual por banda; evento Voluntary atribuido a la última banda válida observada antes de term_date.",
        "formula": "Eventos distintos Voluntary atribuidos / promedio mensual de headcount activo de la banda × 100.",
        "band_definition": {
            "0": "prior_qc_work_years = 0",
            ">0–<1": "prior_qc_work_years > 0 AND prior_qc_work_years < 1",
            "1–<3": "prior_qc_work_years >= 1 AND prior_qc_work_years < 3",
            "3–<5": "prior_qc_work_years >= 3 AND prior_qc_work_years < 5",
            "5–<10": "prior_qc_work_years >= 5 AND prior_qc_work_years < 10",
            "10–<15": "prior_qc_work_years >= 10 AND prior_qc_work_years < 15",
            "15+": "prior_qc_work_years >= 15",
        },
        "acceptance_rule": "Cinco años fiscales completos; doce snapshots por año; bandas fijas y exhaustivas para valores válidos; sólo term_type=VOLUNTARY con term_date; cada celda publicada con annual_distinct_employees>=30 y min_monthly_headcount>=30; reconciliación de eventos documentada.",
        "metrics": metrics,
        "methods": {
            "calendar": "Calendario fiscal deduplicado y filtrado a fis_mo_end_dt <= 2026-09-11.",
            "bands": "CASE mutuamente excluyente sobre valores no nulos >= 0; nulos y negativos quedan fuera de las bandas.",
            "attribution": "ROW_NUMBER por employee_id + term_date sobre snapshots activos previos, ordenados de forma descendente.",
            "denominator": "Malla completa año-mes-banda con promedio, mínimo mensual y población distinta anual.",
        },
        "validation": {
            "calendar": "pass" if metrics["acceptance"]["calendar_complete"] else "fail",
            "bands_and_duplicates": "pass" if metrics["acceptance"]["bands_mutually_exclusive_for_valid_values"] else "warning",
            "denominator_and_privacy": "pass" if metrics["acceptance"]["denominators_and_privacy"] else "fail",
            "event_attribution": "pass" if metrics["acceptance"]["exact_event_reconciliation"] else "warning",
            "field_domain": "pass" if metrics["acceptance"]["invalid_or_missing_field_values_absent"] else "warning",
            "overall": metrics["outcome"],
        },
        "interpretation": "Evidencia descriptiva/asociativa para decidir la agrupación; no causalidad, no predicción individual y no score de riesgo.",
        "limitations": [
            "prior_qc_work_years es un campo almacenado; la fórmula, componentes, traslapes y redondeo requieren lineage autoritativo.",
            "Los eventos Voluntary sin snapshot activo válido previo no se reasignan; la cobertura de atribución varía por fiscal year.",
            "Los valores negativos activos se excluyen de las bandas y se documentan por separado.",
            "El corte fijo excluye el snapshot futuro 2026-09-27 y no incluye FY2026 parcial.",
        ],
        "outcome": metrics["outcome"],
    }

    baseline_html_sha256 = sha256_bytes(V2_HTML.read_bytes())
    baseline_manifest_sha256 = sha256_bytes(V2_MANIFEST.read_bytes())
    if baseline_html_sha256 != EXPECTED_BASELINE_HTML_SHA256 or baseline_manifest_sha256 != EXPECTED_BASELINE_MANIFEST_SHA256:
        raise RuntimeError(
            "La baseline v2 cambiÃ³ antes de la integraciÃ³n; se detiene la escritura. "
            f"HTML={baseline_html_sha256} manifest={baseline_manifest_sha256}"
        )
    active_html = build_html(metrics)
    active_manifest = build_manifest(
        metrics,
        main_result,
        gap_result,
        baseline_html_sha256,
        baseline_manifest_sha256,
    )
    OUT.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ACTIVE_HTML.write_text(active_html, encoding="utf-8")
    ACTIVE_MANIFEST.write_text(json.dumps(active_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(ACTIVE_HTML)
    print(EVIDENCE)
    print(ACTIVE_MANIFEST)
    print(json.dumps({"outcome": metrics["outcome"], "years": metrics["selected_fiscal_years"], "cells": len(metrics["annual"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
