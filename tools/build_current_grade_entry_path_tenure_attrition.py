"""Construye la evidencia y la lamina focalizada de attrition por tenure.

El script ejecuta consultas agregadas con el helper read-only de HRDA, congela
los hashes de SQL y resultados, y agrega una sola lamina a la baseline v2. La
baseline se vuelve a validar antes de cualquier escritura para evitar mezclar
una version distinta del deck.
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
EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.current-grade-entry-path-tenure-attrition-evidence-20260911.json"
MAIN_SQL = ROOT / "queries" / "audits" / "current_grade_entry_path_tenure_attrition_20260911.sql"
GAP_SQL = ROOT / "queries" / "audits" / "current_grade_entry_path_tenure_attrition_gap_20260911.sql"
SOURCE_SQL = ROOT / "queries" / "audits" / "current_grade_entry_path_tenure_source_lineage_20260911.sql"
TEMPLATE = Path(r"C:\Users\fcarranz\.codex\skills\html-slide-generator\templates\fullscreen\base-fullscreen.html")
QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"

CUTOFF = "2026-09-11"
MINIMUM_COHORT = 30
YEARS = [2021, 2022, 2023, 2024, 2025]
PATH_PROMOTION = "promotion_confirmed_into_current_grade"
PATH_OBSERVED = "observed_entry_without_registered_promotion"
PATH_NOT_OBSERVABLE = "current_grade_entry_not_observable"
PATHS = [PATH_PROMOTION, PATH_OBSERVED]
BANDS_BY_PATH = {
    PATH_PROMOTION: ["<1", "1–<2", "2–<4", "4–<5", "≥5"],
    PATH_OBSERVED: ["<2", "2–<3", "3–<4", "≥4"],
}
# The active v2 deck already contains the user-owned Level-family insertion
# (47 -> 48 slides).  Keep that content and guard this focal update against
# the exact 48-slide baseline observed before the queries run.
EXPECTED_BASELINE_HTML_SHA256 = "e7438d7c120eb3b7e1b9446f82939d554fdd3657c29ef6c53e9d093abd6c41ee"
EXPECTED_BASELINE_MANIFEST_SHA256 = "4b424f5e6f6b2b16f8175396c33ecf87c1e29ac5cc48fab6a022fc318cacb65a"
EXPECTED_BASELINE_SLIDE_COUNT = 48
INSERT_AFTER_SLIDE = 27


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def result_hash(result: dict[str, Any]) -> str:
    canonical = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(canonical)


def run_query(sql_path: Path) -> dict[str, Any]:
    command = [
        str(PYTHON),
        "-B",
        str(QUERY_HELPER),
        "--sql-file",
        str(sql_path),
        "--max-rows",
        "200",
        "--reporting-mode",
        "presentation",
    ]
    completed = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    result = json.loads(completed.stdout)
    if result.get("truncated"):
        raise ValueError(f"La consulta agregada fue truncada: {sql_path}")
    return result


def integer(row: dict[str, Any], key: str, default: int = 0) -> int:
    value = row.get(key)
    if value is None or value == "":
        return default
    return int(round(float(value)))


def number(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = row.get(key)
    if value is None or value == "":
        return default
    return float(value)


def rows_from(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = result.get("rows")
    if not isinstance(rows, list):
        raise ValueError("El helper read-only no devolvio una lista de filas agregadas.")
    return rows


def rows_by_type(result: dict[str, Any], row_type: str) -> list[dict[str, Any]]:
    return [row for row in rows_from(result) if row.get("row_type") == row_type]


def metric_rows(gap_result: dict[str, Any], row_type: str, fiscal_year: int | None = None) -> list[dict[str, Any]]:
    rows = rows_by_type(gap_result, row_type)
    if fiscal_year is not None:
        rows = [row for row in rows if row.get("fiscal_year") == fiscal_year]
    return rows


def build_metrics(
    main_result: dict[str, Any],
    gap_result: dict[str, Any],
    source_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    main_rows = rows_from(main_result)
    calendars = {int(row["fiscal_year"]): row for row in main_rows if row.get("row_type") == "calendar"}
    band_rows = {
        (int(row["fiscal_year"]), row["entry_path"], row["tenure_band"]): row
        for row in main_rows
        if row.get("row_type") == "band_year"
    }
    reconciliations = {
        int(row["fiscal_year"]): row for row in main_rows if row.get("row_type") == "reconciliation"
    }
    source_domain_rows = [row for row in main_rows if row.get("row_type") == "source_domain"]
    if len(source_domain_rows) != 1:
        raise ValueError("La consulta principal debe devolver exactamente un row_type=source_domain.")
    source_domain = source_domain_rows[0]

    expected_keys = {(year, path, band) for year in YEARS for path in PATHS for band in BANDS_BY_PATH[path]}
    missing_keys = sorted(expected_keys - set(band_rows))
    if missing_keys:
        raise ValueError(f"La consulta principal no devolvio bandas fijas completas: {missing_keys[:4]}")
    if set(calendars) != set(YEARS) or set(reconciliations) != set(YEARS):
        raise ValueError("La consulta principal no devolvio exactamente FY2021-FY2025.")

    annual: list[dict[str, Any]] = []
    rates: dict[str, dict[str, list[float | None]]] = {path: {} for path in PATHS}
    details: dict[str, dict[str, list[list[Any]]]] = {path: {} for path in PATHS}
    for path in PATHS:
        for year in YEARS:
            values: list[float | None] = []
            detail_values: list[list[Any]] = []
            for band in BANDS_BY_PATH[path]:
                row = band_rows[(year, path, band)]
                privacy_eligible = bool(integer(row, "privacy_eligible"))
                item = {
                    "fiscal_year": year,
                    "entry_path": path,
                    "tenure_band": band,
                    "months_checked": integer(row, "months_checked"),
                    "months_with_headcount": integer(row, "months_with_headcount"),
                    "min_monthly_headcount": integer(row, "min_monthly_headcount"),
                    "max_monthly_headcount": integer(row, "max_monthly_headcount"),
                    "average_monthly_headcount": number(row, "average_monthly_headcount"),
                    "annual_distinct_employees": integer(row, "annual_distinct_employees"),
                    "voluntary_exit_events": integer(row, "voluntary_exit_events"),
                    "annual_voluntary_attrition_percent": number(row, "annual_voluntary_attrition_percent") if row.get("annual_voluntary_attrition_percent") is not None else None,
                    "privacy_eligible": privacy_eligible,
                }
                annual.append(item)
                values.append(item["annual_voluntary_attrition_percent"] if privacy_eligible else None)
                detail_values.append([
                    item["voluntary_exit_events"] if privacy_eligible else None,
                    item["average_monthly_headcount"] if privacy_eligible else None,
                    item["annual_distinct_employees"] if privacy_eligible else None,
                    item["months_checked"],
                    item["months_with_headcount"],
                ])
            rates[path][str(year)] = values
            details[path][str(year)] = detail_values

    reconciliation: list[dict[str, Any]] = []
    for year in YEARS:
        row = reconciliations[year]
        total = integer(row, "total_voluntary_events")
        attributed = integer(row, "attributed_voluntary_events")
        reconciliation.append(
            {
                "fiscal_year": year,
                "total_voluntary_events": total,
                "attributed_voluntary_events": attributed,
                "unattributed_voluntary_events": integer(row, "unattributed_voluntary_events"),
                "sum_of_band_events": integer(row, "sum_of_band_events"),
                "sum_of_published_band_events": integer(row, "sum_of_published_band_events"),
                "no_prior_active_valid_snapshot_events": integer(row, "no_prior_active_valid_snapshot_events"),
                "selected_not_observable_path_events": integer(row, "selected_not_observable_path_events"),
                "selected_missing_tenure_events": integer(row, "selected_missing_tenure_events"),
                "selected_invalid_tenure_band_events": integer(row, "selected_invalid_tenure_band_events"),
                "attribution_coverage_percent": round(100.0 * attributed / total, 4) if total else None,
            }
        )

    calendar = [
        {
            "fiscal_year": year,
            "snapshot_count": integer(calendars[year], "snapshot_count"),
            "fiscal_month_count": integer(calendars[year], "fiscal_month_count"),
            "min_fiscal_month": integer(calendars[year], "min_fiscal_month"),
            "max_fiscal_month": integer(calendars[year], "max_fiscal_month"),
            "first_period_begin": calendars[year].get("first_period_begin"),
            "last_snapshot_date": calendars[year].get("last_snapshot_date"),
        }
        for year in YEARS
    ]

    gap_snapshot_metrics: dict[int, dict[str, int]] = {}
    for year in YEARS:
        values = {
            row["metric"]: integer(row, "metric_value")
            for row in metric_rows(gap_result, "snapshot_quality", year)
            if row.get("entry_path") is None
        }
        gap_snapshot_metrics[year] = values

    gap_path_metrics: dict[int, dict[str, int]] = {}
    for year in YEARS:
        gap_path_metrics[year] = {
            str(row.get("entry_path")): integer(row, "metric_value")
            for row in metric_rows(gap_result, "snapshot_quality", year)
            if row.get("entry_path")
        }

    gap_event_metrics: dict[int, dict[str, int]] = {}
    for year in YEARS:
        gap_event_metrics[year] = {
            str(row["metric"]): integer(row, "metric_value")
            for row in metric_rows(gap_result, "event_reason", year)
        }

    domain_definition = sorted(
        (str(row.get("entry_path")), str(row.get("tenure_band")))
        for row in rows_by_type(gap_result, "domain_definition")
    )
    expected_domain = sorted((path, band) for path in PATHS for band in BANDS_BY_PATH[path])
    domain_fixed_pass = domain_definition == expected_domain

    source_candidates: list[dict[str, Any]] = []
    if source_result is not None:
        for row in rows_by_type(source_result, "source_summary"):
            source_candidates.append(
                {
                    "source_table": row.get("source_table"),
                    "min_snapshot_date": row.get("min_snapshot_date"),
                    "max_snapshot_date": row.get("max_snapshot_date"),
                    "snapshot_count": integer(row, "snapshot_count"),
                    "fy21_fy25_snapshot_count": integer(row, "fy21_fy25_snapshot_count"),
                    "fy21_fy25_active_regular_rows": integer(row, "fy21_fy25_active_regular_rows"),
                    "fy21_fy25_active_regular_profile_start_rows": integer(row, "fy21_fy25_active_regular_profile_start_rows"),
                }
            )

    calendar_pass = (
        len(calendar) == 5
        and all(item["snapshot_count"] == 12 and item["fiscal_month_count"] == 12 for item in calendar)
        and integer(source_domain, "selected_period_count") == 60
        and integer(source_domain, "selected_snapshot_count") == 60
        and integer(source_domain, "selected_fiscal_year_count") == 5
        and integer(source_domain, "future_selected_periods") == 0
    )
    source_quality_pass = (
        integer(source_domain, "source_duplicate_employee_snapshot_dates") == 0
        and integer(source_domain, "source_conflicting_employee_snapshot_dates") == 0
        and integer(source_domain, "target_active_conflicting_snapshot_count") == 0
        and integer(source_domain, "target_future_profile_start_count") == 0
    )
    band_privacy_pass = all(item["privacy_eligible"] for item in annual)
    event_reconciliation_pass = all(
        item["total_voluntary_events"] == item["attributed_voluntary_events"] + item["unattributed_voluntary_events"]
        and item["attributed_voluntary_events"] == item["sum_of_band_events"]
        for item in reconciliation
    )
    profile_coverage_pass = integer(source_domain, "target_missing_profile_start_count") == 0
    overall_outcome = (
        "pass"
        if calendar_pass and source_quality_pass and domain_fixed_pass and band_privacy_pass and event_reconciliation_pass and profile_coverage_pass
        else "warning"
    )

    return {
        "selected_fiscal_years": YEARS,
        "calendar": calendar,
        "annual": annual,
        "rates": rates,
        "details": details,
        "reconciliation": reconciliation,
        "source_domain": {
            "selected_period_count": integer(source_domain, "selected_period_count"),
            "selected_snapshot_count": integer(source_domain, "selected_snapshot_count"),
            "selected_fiscal_year_count": integer(source_domain, "selected_fiscal_year_count"),
            "future_selected_periods": integer(source_domain, "future_selected_periods"),
            "source_duplicate_employee_snapshot_dates": integer(source_domain, "source_duplicate_employee_snapshot_dates"),
            "source_conflicting_employee_snapshot_dates": integer(source_domain, "source_conflicting_employee_snapshot_dates"),
            "target_active_snapshot_count": integer(source_domain, "target_active_snapshot_count"),
            "target_active_conflicting_snapshot_count": integer(source_domain, "target_active_conflicting_snapshot_count"),
            "target_missing_grade_count": integer(source_domain, "target_missing_grade_count"),
            "target_missing_episode_start_count": integer(source_domain, "target_missing_episode_start_count"),
            "target_missing_profile_start_count": integer(source_domain, "target_missing_profile_start_count"),
            "target_future_profile_start_count": integer(source_domain, "target_future_profile_start_count"),
            "target_promotion_path_count": integer(source_domain, "target_promotion_path_count"),
            "target_observed_path_count": integer(source_domain, "target_observed_path_count"),
            "target_not_observable_path_count": integer(source_domain, "target_not_observable_path_count"),
            "target_invalid_tenure_count": integer(source_domain, "target_invalid_tenure_count"),
        },
        "gap_snapshot_metrics": gap_snapshot_metrics,
        "gap_path_metrics": gap_path_metrics,
        "gap_event_metrics": gap_event_metrics,
        "source_candidates": source_candidates,
        "acceptance": {
            "calendar_complete": calendar_pass,
            "source_quality_clean": source_quality_pass,
            "fixed_path_tenure_domain": domain_fixed_pass,
            "bands_mutually_exclusive_and_fixed": domain_fixed_pass,
            "profile_start_coverage": profile_coverage_pass,
            "denominators_and_privacy": band_privacy_pass,
            "event_reconciliation": event_reconciliation_pass,
            "published_band_count": sum(1 for item in annual if item["privacy_eligible"]),
            "expected_band_count": len(expected_domain),
            "minimum_shared_cohort": MINIMUM_COHORT,
        },
        "overall_outcome": overall_outcome,
    }


def _suppress_small(value: int | None) -> tuple[int | None, bool]:
    if value is None:
        return None, False
    if value < MINIMUM_COHORT:
        return None, True
    return value, False


def build_evidence(
    metrics: dict[str, Any],
    main_result: dict[str, Any],
    gap_result: dict[str, Any],
    source_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = metrics["source_domain"]
    reconciliations = []
    for item in metrics["reconciliation"]:
        safe_item = dict(item)
        for key in (
            "no_prior_active_valid_snapshot_events",
            "selected_not_observable_path_events",
            "selected_missing_tenure_events",
            "selected_invalid_tenure_band_events",
        ):
            safe_item[key], suppressed = _suppress_small(safe_item[key])
            if suppressed:
                safe_item[f"{key}_suppressed_below_n"] = MINIMUM_COHORT
        reconciliations.append(safe_item)

    distribution = []
    for item in metrics["annual"]:
        safe_item = {
            "fiscal_year": item["fiscal_year"],
            "entry_path": item["entry_path"],
            "tenure_band": item["tenure_band"],
            "months_checked": item["months_checked"],
            "months_with_headcount": item["months_with_headcount"],
            "privacy_eligible": item["privacy_eligible"],
        }
        if item["privacy_eligible"]:
            safe_item.update(
                {
                    "min_monthly_headcount": item["min_monthly_headcount"],
                    "annual_distinct_employees": item["annual_distinct_employees"],
                    "voluntary_exit_events": item["voluntary_exit_events"],
                    "average_monthly_headcount": item["average_monthly_headcount"],
                    "annual_voluntary_attrition_percent": item["annual_voluntary_attrition_percent"],
                }
            )
        else:
            safe_item["suppression_reason"] = "La celda no cumple los doce snapshots y la cohorte minima publicada."
        distribution.append(safe_item)

    gap_reason_totals: dict[str, int] = {}
    for by_year in metrics["gap_event_metrics"].values():
        for reason, value in by_year.items():
            gap_reason_totals[reason] = gap_reason_totals.get(reason, 0) + value

    source_lineage = {
        "main_source": "hrda.post_hire_monthly_worker_dtls",
        "candidate_tables_checked": [item["source_table"] for item in metrics["source_candidates"]],
        "candidate_profile_start_rows_fy21_fy25": {
            item["source_table"]: item["fy21_fy25_active_regular_profile_start_rows"]
            for item in metrics["source_candidates"]
        },
        "fallback_with_governed_lineage_available": False,
        "interpretation": "Las tablas antiguas tienen cero cobertura poblada del campo en FY2021-FY2025 y no se sustituyen sin lineage y reconciliacion aprobados.",
    }
    total_events = sum(item["total_voluntary_events"] for item in metrics["reconciliation"])
    total_attributed = sum(item["attributed_voluntary_events"] for item in metrics["reconciliation"])

    return {
        "version": 2,
        "variable": "Attrition Voluntary anual por via de entrada al grade y tenure",
        "semantic_type": "derived_feature",
        "reporting_mode": "presentation",
        "publication_status": "published" if metrics["overall_outcome"] == "pass" else "not_publishable",
        "generated_on": CUTOFF,
        "executed_on": CUTOFF,
        "cutoff_date": CUTOFF,
        "query": MAIN_SQL.relative_to(ROOT).as_posix(),
        "gap_query": GAP_SQL.relative_to(ROOT).as_posix(),
        "source_lineage_query": SOURCE_SQL.relative_to(ROOT).as_posix(),
        "provenance": {
            "query_sha256": sha256_bytes(MAIN_SQL.read_bytes()),
            "result_sha256": result_hash(main_result),
            "gap_query_sha256": sha256_bytes(GAP_SQL.read_bytes()),
            "gap_result_sha256": result_hash(gap_result),
            "source_lineage_query_sha256": sha256_bytes(SOURCE_SQL.read_bytes()),
            "source_lineage_result_sha256": result_hash(source_result) if source_result is not None else None,
        },
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1 en snapshots mensuales FY2021-FY2025.",
        "grain": "Empleado-snapshot mensual para headcount; evento Voluntary atribuido al ultimo snapshot activo valido anterior a term_date.",
        "knowledge_boundary": "Solo informacion disponible antes de term_date; no se usa el snapshot de terminacion ni informacion posterior.",
        "formula": "Salidas Voluntary atribuidas / promedio mensual de headcount activo de la banda x 100.",
        "entry_path_definition": {
            PATH_PROMOTION: "Ultima entrada observable al grade actual confirmada por is_promo=1 y promotion_date alineada temporalmente dentro del episodio vigente.",
            PATH_OBSERVED: "Ultima entrada observable al grade actual sin un evento que cumpla la confirmacion de promocion registrada.",
            PATH_NOT_OBSERVABLE: "No existe un cambio previo completo y observable al grade actual; se conserva como limitacion y no se grafica.",
        },
        "tenure_definition": {
            "adjusted_start": "GREATEST(time_in_job_profile_start_date, max_hire_rehire_date), limitado a snapshot_date.",
            PATH_PROMOTION: {band: f"tenure_years {band}" for band in BANDS_BY_PATH[PATH_PROMOTION]},
            PATH_OBSERVED: {band: f"tenure_years {band}" for band in BANDS_BY_PATH[PATH_OBSERVED]},
            "bands_are_fixed": True,
        },
        "calendar": metrics["calendar"],
        "distribution": distribution,
        "reconciliation": reconciliations,
        "source_lineage_reconciliation": source_lineage,
        "aggregate_metrics": {
            "target_active_snapshot_count": source["target_active_snapshot_count"],
            "target_missing_profile_start_count": source["target_missing_profile_start_count"],
            "target_promotion_path_count": source["target_promotion_path_count"],
            "target_observed_path_count": source["target_observed_path_count"],
            "target_not_observable_path_count": source["target_not_observable_path_count"],
            "voluntary_events_fy21_fy25": total_events,
            "attributed_voluntary_events_fy21_fy25": total_attributed,
            "unattributed_voluntary_events_fy21_fy25": total_events - total_attributed,
            "gap_reason_totals": gap_reason_totals,
            "published_band_count": metrics["acceptance"]["published_band_count"],
            "expected_band_count": metrics["acceptance"]["expected_band_count"],
        },
        "acceptance_rule": "Cinco anos fiscales completos con doce snapshots por ano; la via y el tenure deben pertenecer a un dominio fijo y exclusivo; cada tasa publicada requiere n distinto y minimo mensual >= 30; cada evento Voluntary reconcilia como atribuido o no atribuido; los eventos sin snapshot previo valido permanecen como warning.",
        "acceptance": metrics["acceptance"],
        "methods": {
            "entry_path": "LAG por empleado y snapshot, dentro de max_hire_rehire_date; se conserva la ultima entrada al grade actual.",
            "promotion_confirmation": "is_promo=1, promotion_date no futura, posterior al snapshot previo y no posterior al snapshot de entrada; el grade del snapshot del evento debe coincidir.",
            "tenure": "DATEDIFF(day) / 365.25 desde la fecha ajustada; bandas separadas por via y sin reagrupar segun resultados.",
            "event_attribution": "ROW_NUMBER por evento sobre snapshots activos validos anteriores a term_date, ordenados del mas reciente al mas antiguo.",
            "privacy": "Las celdas que no cumplen la cohorte minima se suprimen; no se guardan filas, IDs ni valores individuales.",
        },
        "validation": {
            "calendar": "pass" if metrics["acceptance"]["calendar_complete"] else "fail",
            "source_quality": "pass" if metrics["acceptance"]["source_quality_clean"] else "warning",
            "fixed_domain": "pass" if metrics["acceptance"]["fixed_path_tenure_domain"] else "fail",
            "profile_start_coverage": "pass" if metrics["acceptance"]["profile_start_coverage"] else "warning",
            "privacy": "pass" if metrics["acceptance"]["denominators_and_privacy"] else "warning",
            "event_reconciliation": "pass" if metrics["acceptance"]["event_reconciliation"] else "fail",
            "overall": metrics["overall_outcome"],
        },
        "warnings": [
            "time_in_job_profile_start_date esta vacio en toda la poblacion activa FY2021-FY2025; por ello no hay tenure publicable en la ventana.",
            "Los eventos Voluntary sin snapshot/path/tenure publicable no se reasignan y se conservan en la reconciliacion.",
            "current_grade_entry_not_observable puede reflejar historia incompleta o promociones no registradas; no se interpreta como contratacion directa ni como new hire.",
            "is_new_hire no se usa como clasificador principal de la via de entrada.",
        ],
        "limitations": [
            "Las tablas antiguas phdwd_* y phmwd_* fueron revisadas como candidatos tecnicos, pero no tienen cobertura poblada del campo en la ventana y no cuentan con lineage gobernado reconciliado.",
            "La via observada sin promocion registrada puede incluir historia incompleta o promociones no registradas.",
            "La asociacion es descriptiva; no demuestra causalidad, riesgo individual ni una politica de promociones.",
        ],
        "outcome": metrics["overall_outcome"],
    }


def _json_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def chart_css() -> str:
    return r'''
    .current-grade-entry-path-tenure-layout { display:grid; grid-template-columns:minmax(0,1.62fr) minmax(350px,.83fr); gap:14px; min-height:0; }
    .current-grade-entry-path-tenure-charts { display:grid; grid-template-rows:minmax(0,1fr) minmax(0,1fr); gap:10px; min-height:0; }
    .current-grade-entry-path-tenure-chart-card { padding:10px 12px; gap:4px; min-height:0; }
    .current-grade-entry-path-tenure-chart-card .card-title { font-size:10px; padding-bottom:4px; margin-bottom:0; }
    .current-grade-entry-path-tenure-chart { width:100%; height:270px; min-height:270px; }
    .current-grade-entry-path-tenure-chart-card .chart-footer { padding-top:4px; font-size:10px; line-height:1.2; }
    .current-grade-entry-path-tenure-side { padding:12px 14px; gap:6px; }
    .current-grade-entry-path-tenure-side h3 { font-size:17px; line-height:1.15; margin:0; }
    .current-grade-entry-path-tenure-side p { font-size:12px; line-height:1.28; margin:0; }
    .current-grade-entry-path-tenure-side .fact-list { gap:4px; }
    .current-grade-entry-path-tenure-side .fact-list li { font-size:11px; line-height:1.18; }
    .current-grade-entry-path-tenure-side .provenance-panel { padding-top:5px; }
    .current-grade-entry-path-tenure-side .provenance-status { font-size:10px; line-height:1.2; }
    .current-grade-entry-path-tenure-side .privacy-banner { padding:7px 9px; font-size:10.5px; line-height:1.2; }
'''


def slide_html(metrics: dict[str, Any]) -> str:
    source = metrics["source_domain"]
    total_events = sum(item["total_voluntary_events"] for item in metrics["reconciliation"])
    total_unattributed = sum(item["unattributed_voluntary_events"] for item in metrics["reconciliation"])
    total_not_observable = sum(metrics["gap_path_metrics"].get(year, {}).get(PATH_NOT_OBSERVABLE, 0) for year in YEARS)
    status_text = "Agregado publicable" if metrics["overall_outcome"] == "pass" else "Sin tasa publicable en FY2021–FY2025"
    status_class = "badge-success" if metrics["overall_outcome"] == "pass" else "badge-warning"
    profile_missing = source["target_missing_profile_start_count"]
    target_snapshots = source["target_active_snapshot_count"]
    coverage_text = " · ".join(
        f"FY{item['fiscal_year']}: {item['attribution_coverage_percent']:.1f}%"
        for item in metrics["reconciliation"]
        if item["attribution_coverage_percent"] is not None
    )
    if not coverage_text:
        coverage_text = "Sin eventos atribuidos a una banda publicable"
    return f'''  <div class="slide-stage" id="slide-28" data-evidence-run="current-grade-entry-path-tenure-attrition-20260911">
    <div class="slide-heading"><div><h2 class="slide-title-text">Attrition Voluntary anual por vía de entrada al grade y tenure</h2><p class="slide-subtitle">FY2021–FY2025 · cinco años fiscales completos · asociación descriptiva</p></div><span class="badge {status_class}">{status_text}</span></div>
    <div class="current-grade-entry-path-tenure-layout">
      <div class="current-grade-entry-path-tenure-charts">
        <article class="card chart-card current-grade-entry-path-tenure-chart-card">
          <div class="card-title">Promotion confirmed into current grade</div>
          <div id="current-grade-entry-path-tenure-promotion-chart" class="current-grade-entry-path-tenure-chart" aria-label="Attrition Voluntary anual por tenure con promoción confirmada al grade actual"></div>
          <div class="chart-footer">Bandas fijas: &lt;1 · 1–&lt;2 · 2–&lt;4 · 4–&lt;5 · ≥5 años. Las barras sólo aparecen cuando la celda cumple la regla de publicación.</div>
        </article>
        <article class="card chart-card current-grade-entry-path-tenure-chart-card">
          <div class="card-title">Observed entry without registered promotion</div>
          <div id="current-grade-entry-path-tenure-observed-chart" class="current-grade-entry-path-tenure-chart" aria-label="Attrition Voluntary anual por tenure con entrada observada sin promoción registrada"></div>
          <div class="chart-footer">Bandas fijas: &lt;2 · 2–&lt;3 · 3–&lt;4 · ≥4 años. Esta vía es un proxy observable, no una etiqueta de contratación.</div>
        </article>
      </div>
      <article class="card side-copy current-grade-entry-path-tenure-side">
        <div class="card-title">Pregunta, método y límites</div>
        <span class="badge {status_class}">{status_text}</span>
        <h3>La historia de tenure no está disponible en la ventana histórica</h3>
        <p>La vía se reconstruye en cada snapshot dentro del episodio vigente. Para cada salida Voluntary se conserva el último snapshot activo válido anterior a <code>term_date</code>.</p>
        <ul class="fact-list">
          <li><strong>Población:</strong> Employee / Regular / Active · empleado-snapshot mensual</li>
          <li><strong>Snapshots:</strong> 12 por año fiscal · FY2021–FY2025</li>
          <li><strong>Tenure:</strong> <code>GREATEST(time_in_job_profile_start_date, max_hire_rehire_date)</code></li>
          <li><strong>Cobertura del inicio de profile:</strong> {profile_missing:,} faltantes de {target_snapshots:,} snapshots activos</li>
          <li><strong>Eventos Voluntary:</strong> {total_events:,} en la ventana · {total_unattributed:,} sin banda publicable</li>
          <li><strong>Vía no observable:</strong> {total_not_observable:,} snapshots activos; no se grafica</li>
          <li><strong>Cohorte:</strong> n ≥ {MINIMUM_COHORT} y mínimo mensual ≥ {MINIMUM_COHORT}</li>
        </ul>
        <div class="privacy-banner"><strong>Lectura:</strong> {html.escape(coverage_text)}. Las diferencias serían descriptivas y asociativas; no implican causalidad ni riesgo individual.</div>
        <section class="provenance-panel"><div class="provenance-title">Procedencia y decisión</div>
          <dl class="provenance-grid"><dt>Fuente</dt><dd>HRDA</dd><dt>Tabla</dt><dd>hrda.post_hire_monthly_worker_dtls</dd><dt>Grain</dt><dd>Headcount mensual y evento Voluntary atribuido</dd><dt>Campos</dt><dd>compensation_grade · is_promo · promotion_date · time_in_job_profile_start_date · max_hire_rehire_date</dd></dl>
          <p class="provenance-status"><strong>Importante:</strong> <code>is_new_hire</code> no se usa como clasificador principal. “Observed entry without registered promotion” puede incluir historia incompleta o promociones no registradas; nunca se presenta como direct hire o new hire.</p>
        </section>
      </article>
    </div>
  </div>'''


def chart_script(metrics: dict[str, Any]) -> str:
    payload = {
        "years": metrics["selected_fiscal_years"],
        "bandsByPath": BANDS_BY_PATH,
        "rates": metrics["rates"],
        "details": metrics["details"],
        "outcome": metrics["overall_outcome"],
    }
    payload_json = _json_script(payload)
    return f'''  <script>
    (function () {{
      var currentGradeEntryPathTenurePayload = {payload_json};

      function getThemeColors() {{
        var styles = getComputedStyle(document.body);
        return {{
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

      function blend(first, second, weight) {{
        var base = hexToRgb(first), highlight = hexToRgb(second);
        if (!base || !highlight) return second;
        return 'rgb(' + base.map(function (value, index) {{ return Math.round(value + (highlight[index] - value) * weight); }}).join(',') + ')';
      }}

      function renderPathChart(path, elementId) {{
        var chart = document.getElementById(elementId);
        if (!chart) return;
        if (!window.Plotly) {{
          chart.innerHTML = '<div class="chart-note">Plotly no pudo cargarse; la evidencia agregada conserva el resultado completo.</div>';
          return;
        }}
        var theme = getThemeColors();
        var bands = currentGradeEntryPathTenurePayload.bandsByPath[path];
        var traces = currentGradeEntryPathTenurePayload.years.map(function (year, index) {{
          var values = currentGradeEntryPathTenurePayload.rates[path][String(year)];
          var details = currentGradeEntryPathTenurePayload.details[path][String(year)];
          return {{
            type: 'bar',
            orientation: 'h',
            name: 'FY' + year,
            y: bands,
            x: values,
            customdata: details,
            marker: {{ color: blend(theme.surface, index < 2 ? theme.accent : theme.accent2, 0.95 - (index * 0.12)), line: {{ color: theme.surface, width: 1 }} }},
            text: values.map(function (value) {{ return value === null ? '' : Number(value).toFixed(1) + '%'; }}),
            texttemplate: '%{{text}}',
            textposition: 'outside',
            textfont: {{ family: theme.font, size: 9, color: theme.text }},
            cliponaxis: false,
            hovertemplate: '<b>%{{y}}</b><br>FY' + year + '<br>Tasa: <b>%{{x:.2f}}%</b><br>Salidas Voluntary atribuidas: %{{customdata[0]}}<br>Headcount mensual promedio: %{{customdata[1]}}<br>Empleados distintos: %{{customdata[2]}}<br>Meses completos: %{{customdata[3]}} / %{{customdata[4]}}<extra></extra>'
          }};
        }});
        var hasPublishedRate = traces.some(function (trace) {{ return trace.x.some(function (value) {{ return value !== null; }}); }});
        Plotly.react(chart, traces, {{
          height: 270,
          barmode: 'group',
          bargap: 0.22,
          bargroupgap: 0.07,
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          font: {{ family: theme.font, color: theme.text }},
          margin: {{ t: 30, r: 70, b: 36, l: 62 }},
          showlegend: true,
          legend: {{ orientation: 'h', x: 0, y: 1.15, font: {{ family: theme.font, size: 9, color: theme.text }}, bgcolor: 'rgba(0,0,0,0)' }},
          annotations: hasPublishedRate ? [] : [{{ x: 0.5, y: 0.5, xref: 'paper', yref: 'paper', text: 'Sin tasas publicables: time_in_job_profile_start_date está vacío en FY2021–FY2025', showarrow: false, font: {{ family: theme.font, size: 11, color: theme.muted }}, align: 'center' }}],
          xaxis: {{ title: {{ text: 'Tasa Voluntary anual (%)', font: {{ family: theme.font, size: 10, color: theme.muted }} }}, ticksuffix: '%', rangemode: 'tozero', fixedrange: true, gridcolor: theme.border, zerolinecolor: theme.border, tickfont: {{ family: theme.font, size: 9, color: theme.muted }} }},
          yaxis: {{ categoryorder: 'array', categoryarray: bands, autorange: 'reversed', fixedrange: true, tickfont: {{ family: theme.font, size: 10, color: theme.text }}, gridcolor: 'rgba(0,0,0,0)', zeroline: false }},
          hovermode: 'closest'
        }}, {{ responsive: false, displayModeBar: false }});
      }}

      function renderCurrentGradeEntryPathTenureCharts() {{
        renderPathChart('promotion_confirmed_into_current_grade', 'current-grade-entry-path-tenure-promotion-chart');
        renderPathChart('observed_entry_without_registered_promotion', 'current-grade-entry-path-tenure-observed-chart');
      }}

      renderCurrentGradeEntryPathTenureCharts();
      document.querySelectorAll('#theme-selector [data-theme]').forEach(function (button) {{
        button.addEventListener('click', function () {{ window.requestAnimationFrame(renderCurrentGradeEntryPathTenureCharts); }});
      }});
    }})();
  </script>
'''


def stage_starts(document: str) -> list[re.Match[str]]:
    return list(re.finditer(r'<div class="slide-stage" id="slide-(\d+)"[^>]*>', document))


def stage_texts(document: str) -> dict[str, str]:
    starts = stage_starts(document)
    nav_position = document.find('<div class="nav-ctrl" id="slide-nav">')
    if nav_position < 0:
        raise ValueError("No se encontro el navegador lateral de la baseline.")
    result: dict[str, str] = {}
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else nav_position
        result[f"slide-{match.group(1)}"] = document[match.start():end].rstrip()
    return result


def slide_stage_hashes(document: str) -> dict[str, str]:
    return {stage_id: sha256_bytes(value.encode("utf-8")) for stage_id, value in stage_texts(document).items()}


def normalized_stage_texts(document: str) -> dict[str, str]:
    """Return stage payloads with only the ordinal stage id normalized."""
    return {
        stage_id: re.sub(r'id="slide-\d+"', 'id="slide-X"', value, count=1)
        for stage_id, value in stage_texts(document).items()
    }


def nav_pill_labels(document: str) -> list[str]:
    return re.findall(r'<button class="nav-pill(?: pill-active)?" data-slide="\d+">([^<]+)</button>', document)


def shift_stage_ids(document: str) -> str:
    pattern = re.compile(r'(<div class="slide-stage" id="slide-)(\d+)(")')

    def replace(match: re.Match[str]) -> str:
        number = int(match.group(2))
        return f"{match.group(1)}{number + 1 if number > INSERT_AFTER_SLIDE else number}{match.group(3)}"

    return pattern.sub(replace, document)


def shift_navigation(document: str) -> str:
    pattern = re.compile(r'(<button class="nav-pill(?: pill-active)?" data-slide=")(\d+)(">)(\d+)\. ([^<]*)(</button>)')

    def replace(match: re.Match[str]) -> str:
        index = int(match.group(2))
        number = int(match.group(4))
        if index >= INSERT_AFTER_SLIDE:
            index += 1
            number += 1
        return f"{match.group(1)}{index}{match.group(3)}{number}. {match.group(5)}{match.group(6)}"

    return pattern.sub(replace, document)


def update_ranges(document: str) -> str:
    """Shift displayed ranges at the same insertion boundary as stages."""
    threshold = INSERT_AFTER_SLIDE + 1
    document = re.sub(
        r"Slides (\d+)([–-])(\d+)",
        lambda match: (
            f"Slides {int(match.group(1)) + (1 if int(match.group(1)) >= threshold else 0)}"
            f"{match.group(2)}{int(match.group(3)) + (1 if int(match.group(3)) >= threshold else 0)}"
        ),
        document,
    )
    document = re.sub(
        r'(<span class="nav-section-range">)(\d+)([–-])(\d+)(</span>)',
        lambda match: (
            f"{match.group(1)}{int(match.group(2)) + (1 if int(match.group(2)) >= threshold else 0)}"
            f"{match.group(3)}{int(match.group(4)) + (1 if int(match.group(4)) >= threshold else 0)}{match.group(5)}"
        ),
        document,
    )
    return document


def insert_navigation_button(document: str) -> str:
    old = '<button class="nav-pill" data-slide="28">29. Company tenure</button>'
    new = '<button class="nav-pill" data-slide="27">28. Attrition Voluntary anual por vía de entrada al grade y tenure</button>\n          ' + old
    if old not in document:
        raise ValueError("No se encontro el boton desplazado de Company tenure.")
    return document.replace(old, new, 1)


def build_html(document: str, metrics: dict[str, Any]) -> str:
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Falta la plantilla fullscreen requerida: {TEMPLATE}")
    template_text = TEMPLATE.read_text(encoding="utf-8")
    for required in (
        "theme-light-classic",
        "theme-light-soft",
        "theme-dark-royal",
        "theme-dark-carbon",
        "showSlide(0)",
    ):
        if required not in template_text:
            raise ValueError(f"La plantilla fullscreen no contiene el marcador obligatorio {required!r}.")

    baseline_stages = stage_texts(document)
    baseline_count = len(baseline_stages)
    if list(baseline_stages) != [f"slide-{index}" for index in range(1, baseline_count + 1)]:
        raise ValueError("La baseline debe contener stages consecutivos.")
    baseline_nav = nav_pill_labels(document)
    if len(baseline_nav) != baseline_count:
        raise ValueError("La baseline no conserva el mismo numero de stages y botones de navegacion.")
    baseline_payloads = normalized_stage_texts(document)
    if "Years of experience prior to Qualcomm" not in baseline_stages["slide-16"]:
        raise ValueError("La baseline ya no contiene Years of experience prior to Qualcomm en slide 16.")
    if "Time in current job profile vs. current detailed level" not in baseline_stages["slide-27"]:
        raise ValueError("La baseline ya no contiene el slide 27 esperado.")

    document = shift_stage_ids(document)
    document = shift_navigation(document)
    document = update_ranges(document)
    document = insert_navigation_button(document)

    style_marker = "    /* 13. CONTENT-SPECIFIC STYLES"
    if style_marker not in document:
        raise ValueError("La baseline no contiene la seccion de estilos especificos requerida.")
    document = document.replace(style_marker, chart_css() + "\n" + style_marker, 1)

    insertion_marker = '<div class="slide-stage" id="slide-29"'
    if insertion_marker not in document:
        raise ValueError("No se encontro Company tenure desplazado a slide 29.")
    document = document.replace(insertion_marker, slide_html(metrics) + "\n\n  " + insertion_marker, 1)
    document = document.replace("\n</body>", "\n" + chart_script(metrics) + "</body>", 1)

    final_count = baseline_count + 1
    stage_ids = list(stage_texts(document))
    if stage_ids != [f"slide-{index}" for index in range(1, final_count + 1)]:
        raise ValueError(f"Stages finales inesperados: {stage_ids[:3]} ... {stage_ids[-3:]}")
    nav_values = [int(value) for value in re.findall(r'<button class="nav-pill(?: pill-active)?" data-slide="(\d+)">', document)]
    if nav_values != list(range(final_count)):
        raise ValueError(f"Navegacion final no consecutiva: {nav_values[:4]} ... {nav_values[-4:]}")
    final_stages = stage_texts(document)
    if final_stages["slide-27"] != baseline_stages["slide-27"]:
        raise ValueError("El stage 27 cambio durante la insercion focalizada.")
    if "Company tenure" not in final_stages["slide-29"]:
        raise ValueError("Company tenure no quedo en slide 29.")
    final_payloads = normalized_stage_texts(document)
    for stage_id, payload in baseline_payloads.items():
        old_number = int(stage_id.removeprefix("slide-"))
        # Slide 2 contains the agenda ranges, which must be renumbered with
        # the inserted slide and therefore is intentionally not byte-stable.
        if old_number == 2:
            continue
        new_number = old_number + 1 if old_number > INSERT_AFTER_SLIDE else old_number
        shifted_id = f"slide-{new_number}"
        if final_payloads.get(shifted_id) != payload:
            raise ValueError(f"El contenido existente cambio durante la insercion: {stage_id} -> {shifted_id}.")
    baseline_nav_titles = [re.sub(r"^\d+\.\s*", "", label) for label in baseline_nav]
    expected_nav_titles = (
        baseline_nav_titles[:INSERT_AFTER_SLIDE]
        + ["Attrition Voluntary anual por vía de entrada al grade y tenure"]
        + baseline_nav_titles[INSERT_AFTER_SLIDE:]
    )
    expected_nav = [f"{index + 1}. {title}" for index, title in enumerate(expected_nav_titles)]
    if nav_pill_labels(document) != expected_nav:
        raise ValueError("La navegacion final no conserva los labels existentes ni inserta la nueva lamina.")
    return document


def build_manifest(
    metrics: dict[str, Any],
    evidence: dict[str, Any],
    baseline_html_sha256: str,
    baseline_manifest_sha256: str,
    baseline_html: str,
) -> dict[str, Any]:
    manifest = copy.deepcopy(json.loads(V2_MANIFEST.read_text(encoding="utf-8")))
    baseline_slide_count = len(manifest.get("slides", []))
    if baseline_slide_count < INSERT_AFTER_SLIDE:
        raise ValueError("El manifest base no contiene la frontera de insercion esperada.")
    prior_validation = copy.deepcopy(manifest.get("slide_content_hash_validation", {}))
    manifest["version"] = 2
    manifest["generated_on"] = CUTOFF
    manifest["slide_count"] = baseline_slide_count + 1
    manifest["source_runs"] = list(dict.fromkeys(list(manifest.get("source_runs", [])) + ["current-grade-entry-path-tenure-attrition-20260911"]))
    manifest["aggregate_evidence_builders"] = list(dict.fromkeys(list(manifest.get("aggregate_evidence_builders", [])) + ["tools/build_current_grade_entry_path_tenure_attrition.py"]))
    manifest["new_aggregate_audits"] = list(dict.fromkeys(list(manifest.get("new_aggregate_audits", [])) + [
        "queries/audits/current_grade_entry_path_tenure_attrition_20260911.sql",
        "queries/audits/current_grade_entry_path_tenure_attrition_gap_20260911.sql",
        "queries/audits/current_grade_entry_path_tenure_source_lineage_20260911.sql",
    ]))

    slides: list[dict[str, Any]] = []
    for item in manifest.get("slides", []):
        slide = copy.deepcopy(item)
        if int(slide["slide"]) >= 28:
            slide["slide"] = int(slide["slide"]) + 1
        slides.append(slide)
        if int(item["slide"]) == 27:
            slides.append({"slide": 28, "title": "Attrition Voluntary anual por via de entrada al grade y tenure"})
    manifest["slides"] = slides

    frozen = manifest.setdefault("frozen_evidence", {})
    frozen["current_grade_entry_path_tenure_attrition"] = {
        "evidence": EVIDENCE.relative_to(ROOT).as_posix(),
        "query": MAIN_SQL.relative_to(ROOT).as_posix(),
        "gap_query": GAP_SQL.relative_to(ROOT).as_posix(),
        "source_lineage_query": SOURCE_SQL.relative_to(ROOT).as_posix(),
        "query_sha256": evidence["provenance"]["query_sha256"],
        "query_result_sha256": evidence["provenance"]["result_sha256"],
        "gap_query_sha256": evidence["provenance"]["gap_query_sha256"],
        "gap_result_sha256": evidence["provenance"]["gap_result_sha256"],
        "source_lineage_query_sha256": evidence["provenance"]["source_lineage_query_sha256"],
        "source_lineage_result_sha256": evidence["provenance"]["source_lineage_result_sha256"],
        "execution_date": CUTOFF,
        "reporting_mode": "presentation",
        "population": evidence["population"],
        "grain": evidence["grain"],
        "outcome": evidence["outcome"],
    }

    manifest["active_slide"] = {
        "slide": 28,
        "title": "Attrition Voluntary anual por via de entrada al grade y tenure",
        "reporting_mode": "presentation",
        "query": MAIN_SQL.relative_to(ROOT).as_posix(),
        "evidence": EVIDENCE.relative_to(ROOT).as_posix(),
        "outcome": evidence["outcome"],
        "interpretation": "Asociacion descriptiva; no causalidad, riesgo individual ni inferencia de contratacion.",
        "field_lineage": "La via se deriva de snapshots y eventos; time_in_job_profile_start_date no tiene cobertura FY2021-FY2025.",
    }
    baseline_stage_hash = slide_stage_hashes(baseline_html)["slide-27"]
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": baseline_slide_count,
        "output_slide_count": baseline_slide_count + 1,
        "baseline_html_sha256": baseline_html_sha256,
        "baseline_manifest_sha256": baseline_manifest_sha256,
        "structural_change": (
            f"Inserted slide 28 after slide 27; legacy stages 28–{baseline_slide_count} "
            f"shifted to 29–{baseline_slide_count + 1}; legacy stage payloads preserved."
        ),
        "new_slide": 28,
        "inserted_after_slide": 27,
        "shifted_legacy_slide_range": f"28–{baseline_slide_count} to 29–{baseline_slide_count + 1}",
        "baseline_slide_27_sha256": baseline_stage_hash,
        "legacy_payloads_preserved": True,
        "navigation_consecutive": True,
        "years_of_experience_stays_slide_16": True,
        "company_tenure_is_slide_29": True,
        "preexisting_structural_change": {
            "identified_by_title": prior_validation.get("identified_by_title"),
            "baseline_slide_count": prior_validation.get("baseline_slide_count"),
            "output_slide_count": prior_validation.get("output_slide_count"),
            "structural_change": prior_validation.get("structural_change"),
            "outcome": prior_validation.get("outcome"),
        },
        "outcome": "pass",
    }
    return manifest


def assert_baseline_hashes() -> tuple[str, str]:
    if not V2_HTML.exists() or not V2_MANIFEST.exists():
        raise FileNotFoundError("La baseline v2 y su manifest son obligatorios.")
    html_hash = sha256_bytes(V2_HTML.read_bytes())
    manifest_hash = sha256_bytes(V2_MANIFEST.read_bytes())
    if html_hash != EXPECTED_BASELINE_HTML_SHA256 or manifest_hash != EXPECTED_BASELINE_MANIFEST_SHA256:
        raise RuntimeError(
            "La baseline v2 cambio antes de la integracion; se detiene la escritura. "
            f"HTML={html_hash} manifest={manifest_hash}"
        )
    stage_count = len(stage_texts(V2_HTML.read_text(encoding="utf-8")))
    manifest_data = json.loads(V2_MANIFEST.read_text(encoding="utf-8"))
    if stage_count != EXPECTED_BASELINE_SLIDE_COUNT or len(manifest_data.get("slides", [])) != EXPECTED_BASELINE_SLIDE_COUNT:
        raise RuntimeError(
            "La baseline coincide en hash pero no en su inventario de 48 laminas; se detiene la escritura."
        )
    return html_hash, manifest_hash


def assert_no_legacy_references() -> None:
    # Match the version token, not valid compensation-grade labels.
    legacy_token = "v" + "3"
    legacy_marker = re.compile(rf"(?<![A-Za-z0-9]){legacy_token}(?![A-Za-z0-9])", re.IGNORECASE)
    paths = [MAIN_SQL, GAP_SQL, SOURCE_SQL, Path(__file__), ROOT / "docs" / "variables" / "current-grade-entry-path" / "README.md"]
    for path in paths:
        if path.exists() and legacy_marker.search(path.read_text(encoding="utf-8")):
            raise ValueError(f"Se encontro una referencia de version no permitida en {path}.")


def main() -> None:
    baseline_html_sha256, baseline_manifest_sha256 = assert_baseline_hashes()
    main_result = run_query(MAIN_SQL)
    gap_result = run_query(GAP_SQL)
    source_result = run_query(SOURCE_SQL)
    metrics = build_metrics(main_result, gap_result, source_result)
    evidence = build_evidence(metrics, main_result, gap_result, source_result)

    baseline_html_sha256_again, baseline_manifest_sha256_again = assert_baseline_hashes()
    if (baseline_html_sha256, baseline_manifest_sha256) != (baseline_html_sha256_again, baseline_manifest_sha256_again):
        raise RuntimeError("La baseline cambio mientras se ejecutaban las consultas; no se escribio ningun artefacto.")

    baseline_html = V2_HTML.read_text(encoding="utf-8")
    active_html = build_html(baseline_html, metrics)
    active_manifest = build_manifest(metrics, evidence, baseline_html_sha256, baseline_manifest_sha256, baseline_html)
    assert_no_legacy_references()
    evidence_text = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    manifest_text = json.dumps(active_manifest, ensure_ascii=False, indent=2) + "\n"
    legacy_token = "v" + "3"
    legacy_marker = re.compile(rf"(?<![A-Za-z0-9]){legacy_token}(?![A-Za-z0-9])", re.IGNORECASE)
    if legacy_marker.search(evidence_text) or legacy_marker.search(manifest_text) or legacy_marker.search(active_html):
        raise ValueError("El artefacto nuevo contiene una referencia de version no permitida.")

    OUT.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(evidence_text, encoding="utf-8")
    V2_HTML.write_text(active_html, encoding="utf-8")
    V2_MANIFEST.write_text(manifest_text, encoding="utf-8")
    final_slide_count = len(stage_texts(active_html))
    print(EVIDENCE)
    print(V2_HTML)
    print(V2_MANIFEST)
    print(json.dumps({"outcome": metrics["overall_outcome"], "slide_count": final_slide_count, "published_band_count": metrics["acceptance"]["published_band_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
