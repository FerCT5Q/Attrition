"""Freeze authorized internal aggregate evidence for V7 slide 26.

The two panels deliberately share the 2025-08-24 Regular, active, non-RF360
baseline and the same strict voluntary-outcome window.  A missing recorded
promotion is never labelled "never promoted": the lower panel is a restricted
role-tenure proxy, while all other no-event cases remain declared exclusions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
METADATA_QUERY = ROOT / "queries" / "audits" / "v7_time_since_last_promotion_comparable_cohorts_metadata_20260923.sql"
AUDIT_QUERY = ROOT / "queries" / "audits" / "v7_time_since_last_promotion_comparable_cohorts_20260923.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.time-since-last-promotion-comparable-cohorts-evidence-20260924.json"
AUTHORIZATION_FILE = ROOT / "config" / "attrition_v7_internal_analysis_authorization_20260917.json"

BASELINE_SNAPSHOT = "2025-08-24"
OUTCOME_CUTOFF = "2026-08-23"
MINIMUM_COHORT = 30
BANDS = ("0–<1 year", "1–<2 years", "2–<3 years", "3–<5 years", "5+ years")
COHORTS = ("recorded_promotion", "no_recorded_promotion_proxy")
FORBIDDEN_KEYS = {
    "employee_id",
    "employee_ids",
    "name",
    "emp_name",
    "manager_name",
    "manager_employee_id",
    "email",
    "term_date",
    "promotion_date",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def result_sha256(rows: list[dict[str, Any]]) -> str:
    return sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def as_int(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} debe ser un agregado entero.") from exc


def as_float(value: Any, field: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} debe ser un agregado numérico.") from exc


def run_query(path: Path) -> tuple[list[dict[str, Any]], str]:
    command = [sys.executable, "-B", str(QUERY_HELPER), "--sql-file", str(path), "--max-rows", "100"]
    completed = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8")
    payload = json.loads(completed.stdout)
    rows = payload.get("rows")
    require(payload.get("truncated") is False and isinstance(rows, list), f"La consulta {path.name} no devolvió un conjunto agregado completo.")
    return rows, result_sha256(rows)


def ensure_presentation_safe(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            require(key.lower() not in FORBIDDEN_KEYS, f"La evidencia contiene una clave restringida: {key}")
            ensure_presentation_safe(child)
    elif isinstance(value, list):
        for child in value:
            ensure_presentation_safe(child)


def load_internal_authorization() -> dict[str, Any]:
    authorization = json.loads(AUTHORIZATION_FILE.read_text(encoding="utf-8"))
    exception = authorization.get("small_cell_exception", {})
    controls = authorization.get("non_negotiable_controls", {})
    require(authorization.get("status") == "approved", "La autorización interna de V7 no está aprobada.")
    require(authorization.get("reporting_mode") == "internal_analysis", "La autorización interna de V7 no permite este modo de entrega.")
    require(exception.get("allow_subthreshold_aggregate_buckets") is True, "La autorización interna de V7 no permite mostrar celdas bajo n=30.")
    require(controls.get("aggregate_only") is True, "La autorización interna de V7 requiere resultados agregados.")
    for key in ("employee_rows_persisted", "employee_ids_persisted", "names_persisted", "emails_persisted"):
        require(controls.get(key) is False, f"La autorización interna de V7 tiene un control inválido: {key}.")
    return authorization


def validate_metadata(rows: list[dict[str, Any]]) -> None:
    expected = {
        "employee_id": "bigint",
        "fis_mo_end_dt": "date",
        "worker_type": "character varying",
        "employee_type": "character varying",
        "active_status": "integer",
        "is_rf360_yes_no": "integer",
        "is_promo": "integer",
        "promotion_date": "date",
        "max_hire_rehire_date": "date",
        "time_in_role": "numeric",
        "term_date": "date",
        "term_type": "character varying",
    }
    actual = {str(row.get("column_name")): str(row.get("data_type")) for row in rows}
    require(expected.items() <= actual.items(), "El preflight de metadatos no confirma todas las columnas y tipos requeridos.")


def metrics_and_rows(audit_rows: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    metrics: dict[str, int] = {}
    distributions: dict[str, list[dict[str, Any]]] = {cohort: [] for cohort in COHORTS}
    exclusions: list[dict[str, Any]] = []
    for row in audit_rows:
        row_type = str(row.get("row_type"))
        if row_type in {"diagnostic", "reconciliation"}:
            metric = str(row.get("metric"))
            require(metric and metric != "None" and metric not in metrics, f"Métrica inválida o duplicada: {metric}.")
            metrics[metric] = as_int(row.get("metric_value"), metric)
        elif row_type == "distribution":
            cohort = str(row.get("cohort_type"))
            require(cohort in distributions, f"Cohorte de distribución inesperada: {cohort}.")
            distributions[cohort].append(dict(row))
        elif row_type == "exclusion":
            exclusions.append(dict(row))
        else:
            raise ValueError(f"Tipo de fila inesperado: {row_type}.")
    return metrics, distributions, exclusions


def evidence_row(row: dict[str, Any], cohort_total: int) -> dict[str, Any]:
    employee_count = as_int(row.get("employee_count"), "employee_count")
    voluntary_exits = as_int(row.get("voluntary_exits"), "voluntary_exits")
    require(0 <= voluntary_exits <= employee_count, "Las salidas voluntarias no reconcilian con la cohorte.")
    label = str(row.get("category"))
    require(label in BANDS, f"Banda temporal inesperada: {label}.")
    rate = as_float(row.get("annual_attrition_rate_percent"), f"{label} annual_attrition_rate_percent")
    rendered = {
        "label": label,
        "employee_count": employee_count,
        "distribution_percent": round(100.0 * employee_count / cohort_total, 8),
        "voluntary_exits": voluntary_exits,
        "annual_attrition_rate_percent": rate,
    }
    if employee_count < MINIMUM_COHORT:
        rendered["publication_status"] = "internal_exploratory_small_cohort"
        rendered["display_note"] = "Authorized internal aggregate review only; descriptive result with n<30, not a stable attrition-rate estimate."
    else:
        rendered["publication_status"] = "publishable"
    return rendered


def build_evidence(
    metadata_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    authorization: dict[str, Any],
    *,
    execution_date: str | None = None,
) -> dict[str, Any]:
    validate_metadata(metadata_rows)
    metrics, distributions, exclusion_rows = metrics_and_rows(audit_rows)
    required_metrics = {
        "baseline_employee_count",
        "baseline_population_count",
        "baseline_duplicate_employee_snapshot_count",
        "baseline_conflicting_employee_snapshot_count",
        "invalid_episode_start_count",
        "negative_time_in_role_count",
        "rf360_included_count",
        "invalid_promo_flag_count",
        "promo_flag_without_date_count",
        "promotion_date_without_promo_flag_count",
        "promotion_date_after_event_snapshot_count",
        "future_promotion_date_count",
        "recorded_promotion_count",
        "no_recorded_promotion_proxy_count",
        "declared_exclusions_total",
        "recorded_promotion_band_total",
        "no_recorded_promotion_proxy_band_total",
        "baseline_voluntary_exits_from_classified",
        "baseline_voluntary_exits_direct",
        "rf360_excluded_count",
        "pre_episode_event_excluded_count",
    }
    require(required_metrics <= set(metrics), "La auditoría no devolvió todas las métricas de aceptación requeridas.")
    zero_metrics = (
        "baseline_duplicate_employee_snapshot_count",
        "baseline_conflicting_employee_snapshot_count",
        "invalid_episode_start_count",
        "negative_time_in_role_count",
        "rf360_included_count",
        "invalid_promo_flag_count",
        "promo_flag_without_date_count",
        "promotion_date_without_promo_flag_count",
        "promotion_date_after_event_snapshot_count",
        "future_promotion_date_count",
    )
    failed = [metric for metric in zero_metrics if metrics[metric] != 0]
    require(not failed, "No se aprobaron las salvaguardas de unicidad, validez o leakage: " + ", ".join(failed))
    require(metrics["baseline_employee_count"] == metrics["baseline_population_count"], "El denominador de baseline no reconcilia con la clasificación.")
    require(metrics["baseline_voluntary_exits_from_classified"] == metrics["baseline_voluntary_exits_direct"], "Las salidas voluntarias clasificadas no reconcilian con el conteo directo.")
    require(
        metrics["baseline_population_count"]
        == metrics["recorded_promotion_count"] + metrics["no_recorded_promotion_proxy_count"] + metrics["declared_exclusions_total"],
        "Población base != promoción registrada + proxy + exclusiones declaradas.",
    )
    excluded_counts = {str(row.get("category")): as_int(row.get("employee_count"), "exclusion employee_count") for row in exclusion_rows}
    require(sum(excluded_counts.values()) == metrics["declared_exclusions_total"], "El detalle de exclusiones no reconcilia con su total.")

    panels: dict[str, list[dict[str, Any]]] = {}
    for cohort in COHORTS:
        rows_by_band = {str(row.get("category")): row for row in distributions[cohort]}
        require(set(rows_by_band) == set(BANDS) and len(rows_by_band) == len(BANDS), f"Faltan o sobran bandas para {cohort}.")
        cohort_total = metrics[f"{cohort}_count"]
        require(cohort_total > 0, f"La cohorte {cohort} no tiene empleados.")
        require(sum(as_int(row.get("employee_count"), f"{cohort} employee_count") for row in rows_by_band.values()) == cohort_total, f"Las bandas de {cohort} no reconcilian con la cohorte.")
        require(metrics[f"{cohort}_band_total"] == cohort_total, f"El total de bandas de {cohort} no reconcilia.")
        rendered = [evidence_row(rows_by_band[band], cohort_total) for band in BANDS]
        panels[cohort] = rendered

    small_cohort_rows = [
        {"cohort": cohort, "label": row["label"], "employee_count": row["employee_count"]}
        for cohort, rows in panels.items()
        for row in rows
        if row["publication_status"] == "internal_exploratory_small_cohort"
    ]
    require(
        all(int(row["employee_count"]) < MINIMUM_COHORT for row in small_cohort_rows),
        "Una excepción interna de cohorte pequeña no cumple n<30.",
    )

    evidence = {
        "artifact_type": "aggregate_distribution_attrition_evidence",
        "version": 1,
        "artifact_classification": "internal_analysis",
        "deliverable_mode": "internal_analysis",
        "generated_on": execution_date or date.today().isoformat(),
        "purpose": "Rediseñar el slide 26 con dos distribuciones temporales independientes y comparables; no afirma que una ausencia de evento sea una ausencia histórica de promoción.",
        "outcome_contract": {
            "baseline_snapshot_date": BASELINE_SNAPSHOT,
            "outcome_window": f"({BASELINE_SNAPSHOT}, {OUTCOME_CUTOFF}]",
            "target": "term_type='VOLUNTARY' con term_date dentro de la ventana fija.",
            "population": "worker_type='Employee'; employee_type='Regular'; active_status=1; COALESCE(is_rf360_yes_no, 0)=0 al baseline.",
            "grain": "Empleado distinto clasificado al snapshot baseline.",
        },
        "definitions": {
            "recorded_promotion": "Última promotion_date válida registrada desde max_hire_rehire_date, conocida al baseline.",
            "no_recorded_promotion_proxy": "Sin promoción válida registrada desde el inicio del episodio, episodio iniciado dentro de historia observable y ROUND(time_in_role, 1) igual a la antigüedad calendario desde max_hire_rehire_date redondeada a una decimal.",
            "limitation": "El proxy no demuestra un historial laboral completo ni debe leerse como 'never promoted'.",
        },
        "authorization": {
            "path": str(AUTHORIZATION_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(AUTHORIZATION_FILE.read_bytes()),
            "authorization_id": authorization["authorization_id"],
            "authorized_audience": authorization["authorized_audience"],
            "small_cell_exception_applied": bool(small_cohort_rows),
            "interpretation": "The exception allows aggregate visibility only. A row below n=30 remains descriptive and is not a stable attrition-rate estimate.",
        },
        "recorded_promotion_distribution": panels["recorded_promotion"],
        "no_recorded_promotion_role_tenure_proxy_distribution": panels["no_recorded_promotion_proxy"],
        "cohort_totals": {
            "baseline_population": metrics["baseline_population_count"],
            "recorded_promotion": metrics["recorded_promotion_count"],
            "no_recorded_promotion_role_tenure_proxy": metrics["no_recorded_promotion_proxy_count"],
            "declared_exclusions": metrics["declared_exclusions_total"],
        },
        "declared_exclusions": [
            {"category": category, "employee_count": count}
            for category, count in sorted(excluded_counts.items())
        ],
        "validation": {
            "minimum_shared_cohort": MINIMUM_COHORT,
            "all_bands_meet_shared_minimum": not small_cohort_rows,
            "internal_exploratory_small_cohort_rows": small_cohort_rows,
            "baseline_reconciliation": "pass",
            "outcome_reconciliation": "pass",
            "snapshot_uniqueness": "pass",
            "valid_dates_and_nonnegative_time_in_role": "pass",
            "valid_promotion_events_and_no_future_leakage": "pass",
            "rf360_exclusion_applied": "pass",
            "metrics": metrics,
        },
        "outcome": "pass",
    }
    ensure_presentation_safe(evidence)
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera evidencia interna agregada para el slide 26 de promociones.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    require(QUERY_HELPER.exists() and METADATA_QUERY.exists() and AUDIT_QUERY.exists() and AUTHORIZATION_FILE.exists(), "Falta el helper read-only, una consulta requerida o la autorización interna.")
    authorization = load_internal_authorization()
    metadata_rows, metadata_hash = run_query(METADATA_QUERY)
    audit_rows, audit_hash = run_query(AUDIT_QUERY)
    evidence = build_evidence(metadata_rows, audit_rows, authorization)
    evidence["query_provenance"] = {
        "metadata_query": {
            "path": str(METADATA_QUERY.relative_to(ROOT)).replace("\\", "/"),
            "sql_sha256": sha256(METADATA_QUERY.read_bytes()),
            "result_sha256": metadata_hash,
        },
        "cohort_audit": {
            "path": str(AUDIT_QUERY.relative_to(ROOT)).replace("\\", "/"),
            "sql_sha256": sha256(AUDIT_QUERY.read_bytes()),
            "result_sha256": audit_hash,
        },
    }
    ensure_presentation_safe(evidence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    print(
        "baseline="
        + str(evidence["cohort_totals"]["baseline_population"])
        + "; recorded="
        + str(evidence["cohort_totals"]["recorded_promotion"])
        + "; proxy="
        + str(evidence["cohort_totals"]["no_recorded_promotion_role_tenure_proxy"])
        + "; outcome=pass"
    )


if __name__ == "__main__":
    main()
