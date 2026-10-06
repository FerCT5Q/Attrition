"""Freeze aggregate historical voluntary-attrition evidence for Comp ratio.

The stored monthly ``compa_ratio`` is treated as a precomputed metric whose
formula/lineage remains pending.  This builder only publishes the two agreed
bands and aggregate six-month voluntary-attrition rates; it never persists
employee rows, identifiers, exact pay, or raw ratio values.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "audits" / "comp_ratio_voluntary_attrition_history_20260913.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "comp-ratio-voluntary-attrition-history-evidence-20260913.json"
READONLY_HELPER = ROOT / "tools" / "read_only_redshift_query_helper.py"
MINIMUM_COHORT = 30
GROUP_LABELS = ("<0.8 (incl. 0)", ">=0.8")
EXPECTED_COLUMNS = {
    "row_type",
    "snapshot_date",
    "group_label",
    "employee_snapshots",
    "voluntary_exit_snapshots",
    "voluntary_rate_percent",
    "eligible_employee_snapshots",
    "ratio_observed_employee_snapshots",
    "ratio_missing_employee_snapshots",
    "metric",
    "metric_value",
    "metric_date",
}
PROHIBITED_KEYS = {
    "employee_id",
    "employee_ids",
    "emp_name",
    "name",
    "email",
    "manager_employee_id",
    "manager_name",
    "term_date",
    "compa_ratio",
    "annual_base_pay",
    "base_pay_rate",
    "total_base_pay_amount",
    "fte_annual_base_pay",
    "raw_rows",
    "raw_query_rows",
    "query_rows",
    "source_rows",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def hash_json(value: object) -> str:
    return sha256_bytes(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    )


def numeric(value: object, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} debe ser numérico.") from exc
    if number < 0:
        raise ValueError(f"{label} no puede ser negativo.")
    return number


def numeric_int(value: object, label: str) -> int:
    number = numeric(value, label)
    if not number.is_integer():
        raise ValueError(f"{label} debe ser entero.")
    return int(number)


def ensure_no_sensitive_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in PROHIBITED_KEYS:
                raise ValueError(f"La evidencia contiene la clave restringida {key!r}.")
            ensure_no_sensitive_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            ensure_no_sensitive_keys(nested)


def load_readonly_helper() -> Any:
    spec = importlib.util.spec_from_file_location("attrition_readonly_helper", READONLY_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el helper read-only: {READONLY_HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def execute_query() -> tuple[list[dict[str, Any]], str, str]:
    sql = QUERY.read_text(encoding="utf-8")
    helper = load_readonly_helper()
    readonly_sql = helper.validate_readonly(sql)
    with helper.connect() as connection:
        connection.set_session(readonly=True)
        with connection.cursor(cursor_factory=helper.psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(readonly_sql)
            rows = [dict(row) for row in cursor.fetchall()]
    return rows, sha256_bytes(sql.encode("utf-8")), hash_json(rows)


def parse_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    series: list[dict[str, Any]] = []
    audit_metrics: dict[str, int | float] = {}
    audit_dates: dict[str, str] = {}
    for row in rows:
        if set(row) != EXPECTED_COLUMNS:
            raise ValueError("La consulta devolvió un esquema agregado inesperado.")
        row_type = str(row["row_type"])
        if row_type == "series":
            label = str(row["group_label"])
            if label not in GROUP_LABELS:
                raise ValueError(f"Grupo no aprobado: {label!r}.")
            series.append(
                {
                    "snapshot_date": str(row["snapshot_date"]),
                    "group_label": label,
                    "employee_snapshots": numeric_int(row["employee_snapshots"], "employee_snapshots"),
                    "voluntary_exit_snapshots": numeric_int(
                        row["voluntary_exit_snapshots"], "voluntary_exit_snapshots"
                    ),
                    "voluntary_rate_percent": round(
                        numeric(row["voluntary_rate_percent"], "voluntary_rate_percent"), 4
                    ),
                    "eligible_employee_snapshots": numeric_int(
                        row["eligible_employee_snapshots"], "eligible_employee_snapshots"
                    ),
                    "ratio_observed_employee_snapshots": numeric_int(
                        row["ratio_observed_employee_snapshots"],
                        "ratio_observed_employee_snapshots",
                    ),
                    "ratio_missing_employee_snapshots": numeric_int(
                        row["ratio_missing_employee_snapshots"],
                        "ratio_missing_employee_snapshots",
                    ),
                }
            )
        elif row_type == "audit":
            metric = str(row["metric"])
            if metric in audit_metrics or metric in audit_dates:
                raise ValueError(f"La métrica de auditoría está duplicada: {metric!r}.")
            if row["metric_value"] is not None:
                value = numeric(row["metric_value"], f"audit:{metric}")
                audit_metrics[metric] = int(value) if value.is_integer() else value
            elif row["metric_date"] is not None:
                audit_dates[metric] = str(row["metric_date"])
            else:
                raise ValueError(f"La métrica de auditoría no tiene valor: {metric!r}.")
        else:
            raise ValueError(f"row_type no reconocido: {row_type!r}.")
    if not series:
        raise ValueError("La consulta no devolvió puntos históricos.")
    return series, {"metrics": audit_metrics, "dates": audit_dates}


def pooled_comparison(series: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, dict[str, int]] = {
        label: {"employee_snapshots": 0, "voluntary_exit_snapshots": 0} for label in GROUP_LABELS
    }
    for row in series:
        bucket = groups[row["group_label"]]
        bucket["employee_snapshots"] += int(row["employee_snapshots"])
        bucket["voluntary_exit_snapshots"] += int(row["voluntary_exit_snapshots"])
    result: dict[str, Any] = {}
    for label, values in groups.items():
        rate = 100.0 * values["voluntary_exit_snapshots"] / values["employee_snapshots"]
        result[label] = {
            **values,
            "voluntary_rate_percent": round(rate, 4),
        }
    low_rate = float(result[GROUP_LABELS[0]]["voluntary_rate_percent"])
    high_rate = float(result[GROUP_LABELS[1]]["voluntary_rate_percent"])
    result["comparison"] = {
        "absolute_difference_percentage_points": round(low_rate - high_rate, 4),
        "relative_rate_ratio": round(low_rate / high_rate, 4) if high_rate else None,
        "denominator_definition": "Pooled employee-snapshot rows across complete monthly snapshots; the same employee may contribute to multiple snapshots.",
    }
    return result


def validate_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "presentation",
        "variable": "Comp ratio",
        "semantic_type": "precomputed_metric",
        "outcome": "pass",
    }
    for key, expected_value in expected.items():
        if evidence.get(key) != expected_value:
            raise ValueError(f"Contrato de evidencia inválido para {key}: {evidence.get(key)!r}.")
    series = evidence.get("series")
    if not isinstance(series, list) or not series:
        raise ValueError("La evidencia no contiene una serie histórica.")
    dates = sorted({str(row["snapshot_date"]) for row in series})
    if len(series) != len(dates) * 2:
        raise ValueError("Cada snapshot debe tener exactamente dos grupos.")
    for snapshot_date in dates:
        rows = [row for row in series if str(row["snapshot_date"]) == snapshot_date]
        if {row["group_label"] for row in rows} != set(GROUP_LABELS):
            raise ValueError(f"Falta un grupo en {snapshot_date}.")
        for row in rows:
            if int(row["employee_snapshots"]) < MINIMUM_COHORT:
                raise ValueError(f"Cohorte menor a n={MINIMUM_COHORT} en {snapshot_date}.")
            if int(row["voluntary_exit_snapshots"]) > int(row["employee_snapshots"]):
                raise ValueError(f"Eventos mayores al denominador en {snapshot_date}.")
            expected_rate = 100.0 * int(row["voluntary_exit_snapshots"]) / int(row["employee_snapshots"])
            if abs(float(row["voluntary_rate_percent"]) - expected_rate) > 0.01:
                raise ValueError(f"La tasa no reconcilia en {snapshot_date}, {row['group_label']}.")
    metrics = evidence.get("audit_metrics", {})
    required_zero_metrics = (
        "eligible_employee_snapshot_duplicate_rows",
        "conflicting_compa_ratio_employee_snapshots",
        "ratio_missing_employee_snapshots",
        "ratio_negative_employee_snapshots",
        "series_points_below_n30",
        "series_group_reconciliation_failures",
    )
    for metric in required_zero_metrics:
        if int(metrics.get(metric, -1)) != 0:
            raise ValueError(f"La regla de aceptación falló: {metric}={metrics.get(metric)!r}.")
    dates_metadata = evidence.get("audit_dates", {})
    if not dates_metadata.get("complete_followup_first_snapshot_date") or not dates_metadata.get(
        "complete_followup_last_snapshot_date"
    ):
        raise ValueError("Faltan los límites de seguimiento completo.")
    ensure_no_sensitive_keys(evidence)
    return evidence


def build_evidence(rows: list[dict[str, Any]], query_sha256: str, result_sha256: str) -> dict[str, Any]:
    series, audit = parse_rows(rows)
    metrics = audit["metrics"]
    if int(metrics.get("published_series_points", -1)) != len(series):
        raise ValueError("El conteo de puntos publicados no reconcilia con la serie.")
    if int(metrics.get("complete_snapshot_count", -1)) * 2 != len(series):
        raise ValueError("La serie no tiene dos grupos por snapshot completo.")
    evidence: dict[str, Any] = {
        "schema_version": 1,
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "presentation",
        "variable": "Comp ratio",
        "semantic_type": "precomputed_metric",
        "publication_status": "validated_historical_association",
        "generated_on": date.today().isoformat(),
        "query_path": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "population": "Empleados regulares activos en cada snapshot mensual, con compa_ratio poblado.",
        "grain": "Snapshot mensual de empleado; serie publicada por snapshot x grupo de compa_ratio.",
        "knowledge_boundary": "Sólo datos disponibles al cierre de cada snapshot; seguimiento completo de seis meses.",
        "outcome_definition": "Salida voluntaria estricta con term_date en (snapshot_date, snapshot_date + 6 meses].",
        "grouping": {
            "threshold": 0.8,
            "low_group": "<0.8 (incl. 0)",
            "high_group": ">=0.8",
            "zero_in_low_group": True,
            "formula_lineage_status": "pending",
        },
        "series": sorted(series, key=lambda row: (row["snapshot_date"], GROUP_LABELS.index(row["group_label"]))),
        "audit_metrics": metrics,
        "audit_dates": audit["dates"],
        "pooled_comparison": pooled_comparison(series),
        "acceptance_rule": "No duplicate employee-snapshot keys, no conflicting compa_ratio values, no missing or negative ratio values in the published population, every group-month n>=30, group totals reconcile to observed ratio rows, and all snapshots have six months of follow-up.",
        "interpretation_limit": "Asociación descriptiva del valor almacenado; no confirma que compa_ratio represente bajo salario relativo, no demuestra causalidad y no produce predicciones individuales.",
        "excluded_event_handling": "Ambiguous term-type keys and VOLUNTARY EXCEPTION keys are excluded from the strict VOLUNTARY outcome and retained only as aggregate diagnostics.",
        "provenance": {
            "query_sha256": query_sha256,
            "result_sha256": result_sha256,
            "raw_aggregate_rows_persisted": False,
        },
        "privacy_checks": {
            "identifiers_persisted": False,
            "employee_rows_persisted": False,
            "exact_compensation_persisted": False,
            "raw_compa_ratio_values_persisted": False,
            "all_displayed_cohorts_meet_minimum": True,
            "minimum_cohort": MINIMUM_COHORT,
        },
        "score_v4_change": "none",
        "outcome": "pass",
    }
    return validate_evidence(evidence)


def build_and_write(output: Path = OUTPUT) -> dict[str, Any]:
    rows, query_sha256, result_sha256 = execute_query()
    evidence = build_evidence(rows, query_sha256, result_sha256)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera evidencia agregada histórica de Comp ratio.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    document = build_and_write(args.output)
    comparison = document["pooled_comparison"]["comparison"]
    print(args.output)
    print(
        "snapshots={snapshots}; low_rate={low:.4f}%; high_rate={high:.4f}%; delta={delta:.4f} pp".format(
            snapshots=len({row["snapshot_date"] for row in document["series"]}),
            low=document["pooled_comparison"][GROUP_LABELS[0]]["voluntary_rate_percent"],
            high=document["pooled_comparison"][GROUP_LABELS[1]]["voluntary_rate_percent"],
            delta=comparison["absolute_difference_percentage_points"],
        )
    )
