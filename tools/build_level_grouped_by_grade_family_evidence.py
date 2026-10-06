"""Freeze aggregate-only evidence for the Level-by-grade-family display.

The artifact is an exploratory display view.  ``level_grouped`` remains the
primary ordinal construct; the first-letter grade family is only a descriptive
proxy and does not replace the candidate variable or change its v4 score.
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
READONLY_QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
AUDIT_SQL = ROOT / "queries" / "audits" / "level_grouped_by_compensation_grade_family_20260911.sql"
DEFAULT_OUTPUT = ROOT / "output" / "distribution" / "json" / "level-grouped-by-grade-family-evidence-20260911.json"
SNAPSHOT_DATE = "2026-08-23"
MINIMUM_COHORT = 30
LEVEL_ORDER = (
    "VP & Above",
    "Sr Dir",
    "Princ/Directors",
    "Mgrs Corp",
    "Sr Staff & /Mgr",
    "Staff & /Mgr",
    "Senior & Lead",
    "Assoc & Int/Eng",
    "Support",
)
FAMILY_ORDER = ("M", "P", "R", "S", "T", "V / other grade families")
REQUIRED_METRICS = {
    "source_row_count",
    "eligible_employee_count",
    "duplicate_employee_snapshot_row_count",
    "missing_level_employee_count",
    "missing_grade_employee_count",
    "level_band_count",
    "raw_grade_family_count",
    "raw_matrix_cell_count",
    "raw_matrix_cells_below_minimum_count",
    "raw_matrix_employee_count",
    "duplicate_employee_snapshot_count",
    "employee_level_conflict_count",
    "employee_family_conflict_count",
    "employee_grade_conflict_count",
}
PROHIBITED_KEYS = {
    "employee_id",
    "employee_ids",
    "emp_name",
    "name",
    "email",
    "manager_employee_id",
    "manager_name",
    "raw_rows",
    "query_rows",
    "individual_rows",
}


def load_readonly_helper() -> Any:
    if not READONLY_QUERY_HELPER.exists():
        raise FileNotFoundError(READONLY_QUERY_HELPER)
    spec = importlib.util.spec_from_file_location("attrition_readonly_query_helper", READONLY_QUERY_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo cargar el helper read-only aprobado.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def hash_json(value: object) -> str:
    return sha256_bytes(
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    )


def integer(value: object, label: str) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} no es numérico.") from exc
    if not numeric.is_integer():
        raise ValueError(f"{label} debe ser entero.")
    return int(numeric)


def number(value: object, label: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} no es numérico.") from exc


def execute_audit() -> tuple[list[dict[str, Any]], str, str]:
    helper = load_readonly_helper()
    sql = AUDIT_SQL.read_text(encoding="utf-8")
    readonly_sql = helper.validate_readonly(sql)
    with helper.connect() as connection:
        connection.autocommit = True
        with connection.cursor(cursor_factory=helper.psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(readonly_sql)
            rows = [dict(row) for row in cursor.fetchall()]
    if not rows:
        raise ValueError("La auditoría no devolvió filas agregadas.")
    return rows, sha256_bytes(sql.encode("utf-8")), hash_json(rows)


def parse_rows(rows: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, str], list[dict[str, Any]], dict[str, int], dict[str, int]]:
    expected_columns = {
        "result_type",
        "level_label",
        "grade_family_display",
        "metric_name",
        "employee_count",
        "percentage",
        "metric_value",
        "observed_date",
    }
    metrics: dict[str, int] = {}
    dates: dict[str, str] = {}
    matrix: list[dict[str, Any]] = []
    level_totals: dict[str, int] = {}
    family_totals: dict[str, int] = {}
    for row in rows:
        if set(row) != expected_columns:
            raise ValueError(f"Contrato de columnas inesperado: {sorted(row)}")
        result_type = str(row["result_type"])
        if result_type == "distribution":
            if row["level_label"] is None or row["grade_family_display"] is None:
                raise ValueError("La matriz contiene una etiqueta nula.")
            count = integer(row["employee_count"], "distribution.employee_count")
            if count < 0:
                raise ValueError("La matriz contiene un conteo negativo.")
            matrix.append(
                {
                    "level": str(row["level_label"]),
                    "family": str(row["grade_family_display"]),
                    "employee_count": count,
                    "global_percentage": round(number(row["percentage"], "distribution.percentage"), 8),
                }
            )
        elif result_type in {"level_total", "family_total"}:
            label = row["level_label"] if result_type == "level_total" else row["grade_family_display"]
            if label is None or row["employee_count"] is None:
                raise ValueError(f"Fila {result_type} incompleta.")
            target = level_totals if result_type == "level_total" else family_totals
            key = str(label)
            if key in target:
                raise ValueError(f"Fila {result_type} duplicada: {key}.")
            target[key] = integer(row["employee_count"], f"{result_type}:{key}")
        elif result_type == "metric":
            metric = str(row["metric_name"])
            if metric in metrics or row["level_label"] is not None or row["grade_family_display"] is not None:
                raise ValueError(f"Métrica inválida o duplicada: {metric}.")
            if row["observed_date"] is not None:
                dates[metric] = str(row["observed_date"])
            elif row["metric_value"] is None:
                raise ValueError(f"La métrica {metric} no tiene valor.")
            else:
                metrics[metric] = integer(row["metric_value"], metric)
        else:
            raise ValueError(f"result_type no soportado: {result_type}.")
    if set(metrics) != REQUIRED_METRICS:
        raise ValueError(
            f"Contrato de métricas inválido; missing={sorted(REQUIRED_METRICS - set(metrics))}, "
            f"extra={sorted(set(metrics) - REQUIRED_METRICS)}."
        )
    if dates != {"min_snapshot": SNAPSHOT_DATE, "max_snapshot": SNAPSHOT_DATE}:
        raise ValueError(f"El rango de snapshots no coincide con {SNAPSHOT_DATE}: {dates}.")
    return metrics, dates, matrix, level_totals, family_totals


def validate_and_build(
    metrics: dict[str, int],
    dates: dict[str, str],
    matrix: list[dict[str, Any]],
    level_totals: dict[str, int],
    family_totals: dict[str, int],
    sql_sha256: str,
    result_sha256: str,
) -> dict[str, object]:
    if metrics["source_row_count"] != metrics["eligible_employee_count"]:
        raise ValueError("Las filas fuente no reconcilian con empleados distintos.")
    if metrics["duplicate_employee_snapshot_row_count"] != 0 or metrics["duplicate_employee_snapshot_count"] != 0:
        raise ValueError("El grano empleado-snapshot contiene duplicados.")
    if metrics["missing_level_employee_count"] != 0 or metrics["missing_grade_employee_count"] != 0:
        raise ValueError("La población visible contiene valores faltantes de Level o grade.")
    if any(metrics[key] != 0 for key in ("employee_level_conflict_count", "employee_family_conflict_count", "employee_grade_conflict_count")):
        raise ValueError("Existe un conflicto de mapping dentro del snapshot.")
    if metrics["level_band_count"] != len(LEVEL_ORDER) or set(level_totals) != set(LEVEL_ORDER):
        raise ValueError("El dominio de level_grouped no coincide con las nueve bandas esperadas.")
    if tuple(family_totals) != FAMILY_ORDER:
        raise ValueError("El dominio visible de familias no coincide con el contrato.")
    if metrics["raw_matrix_cells_below_minimum_count"] != 0:
        raise ValueError("Existe una celda de la matriz por debajo de n=30.")
    if any(count < MINIMUM_COHORT for count in level_totals.values()) or any(count < MINIMUM_COHORT for count in family_totals.values()):
        raise ValueError("Existe una banda o familia visible por debajo de n=30.")
    if any(int(row["employee_count"]) < MINIMUM_COHORT for row in matrix):
        raise ValueError("Existe una celda publicada por debajo de n=30.")
    if sum(level_totals.values()) != metrics["eligible_employee_count"]:
        raise ValueError("Las bandas de Level no reconcilian con el denominador.")
    if sum(family_totals.values()) != metrics["eligible_employee_count"]:
        raise ValueError("Las familias no reconcilian con el denominador.")
    if sum(int(row["employee_count"]) for row in matrix) != metrics["eligible_employee_count"]:
        raise ValueError("La matriz Level-familia no reconcilia con el denominador.")
    if metrics["raw_matrix_employee_count"] != metrics["eligible_employee_count"]:
        raise ValueError("La matriz agregada no reconcilia con la población elegible.")

    matrix_by_level: dict[str, list[dict[str, object]]] = {level: [] for level in LEVEL_ORDER}
    for row in matrix:
        level = str(row["level"])
        family = str(row["family"])
        if level not in matrix_by_level or family not in FAMILY_ORDER:
            raise ValueError(f"Etiqueta fuera del dominio visible: {level}/{family}.")
        matrix_by_level[level].append(
            {
                "family": family,
                "employee_count": int(row["employee_count"]),
                "percentage_within_level": round(100 * int(row["employee_count"]) / level_totals[level], 8),
            }
        )
    for level in LEVEL_ORDER:
        if sum(int(item["employee_count"]) for item in matrix_by_level[level]) != level_totals[level]:
            raise ValueError(f"La fila de matriz no reconcilia para {level}.")
        matrix_by_level[level].sort(key=lambda item: FAMILY_ORDER.index(str(item["family"])))

    evidence = {
        "artifact_type": "aggregate_display_evidence",
        "evidence_version": 1,
        "deliverable_mode": "internal_analysis",
        "variable": "Level grouped by grade family",
        "semantic_type": "grouped_mapping",
        "publication_status": "exploratory_display_only",
        "snapshot_date": SNAPSHOT_DATE,
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1",
        "grain": "Distinct employee snapshot",
        "score_v4_change": "none",
        "definition": {
            "primary_field": "level_grouped",
            "context_field": "compensation_grade",
            "family_proxy": "First alphabetic grade prefix, with V and the small unmapped tail pooled for privacy.",
            "interpretation": "The chart describes how the stored grade-family proxy is distributed within the stored Level bands; it does not infer a universal numeric ladder or an official track mapping.",
        },
        "rule_applied": {
            "level_order": list(LEVEL_ORDER),
            "family_order": list(FAMILY_ORDER),
            "family_mapping": "M, P, R, S and T remain visible prefixes; V and non-M/P/R/S/T prefixes are pooled as V / other grade families so every visible cell meets n >= 30.",
            "small_cell_rule": "No displayed Level-family cell, Level band or family total may be below n=30.",
            "denominator_rule": "All active Regular Employee rows in the exact 2026-08-23 snapshot; no compensation or RF360 filter is applied.",
        },
        "matrix": [
            {"level": level, "segments": matrix_by_level[level], "employee_count": level_totals[level]}
            for level in LEVEL_ORDER
        ],
        "level_totals": [
            {
                "level": level,
                "employee_count": level_totals[level],
                "percentage": round(100 * level_totals[level] / metrics["eligible_employee_count"], 8),
            }
            for level in LEVEL_ORDER
        ],
        "family_totals": [
            {
                "family": family,
                "employee_count": family_totals[family],
                "percentage": round(100 * family_totals[family] / metrics["eligible_employee_count"], 8),
            }
            for family in FAMILY_ORDER
        ],
        "metrics": metrics,
        "validations": {
            "exact_snapshot": dates["min_snapshot"] == SNAPSHOT_DATE and dates["max_snapshot"] == SNAPSHOT_DATE,
            "zero_duplicate_employee_snapshot": metrics["duplicate_employee_snapshot_count"] == 0 and metrics["duplicate_employee_snapshot_row_count"] == 0,
            "zero_employee_mapping_conflicts": all(metrics[key] == 0 for key in ("employee_level_conflict_count", "employee_family_conflict_count", "employee_grade_conflict_count")),
            "zero_level_missingness": metrics["missing_level_employee_count"] == 0,
            "zero_grade_missingness": metrics["missing_grade_employee_count"] == 0,
            "nine_level_bands": metrics["level_band_count"] == 9,
            "matrix_reconciliation": sum(int(row["employee_count"]) for row in matrix) == metrics["eligible_employee_count"],
            "level_reconciliation": sum(level_totals.values()) == metrics["eligible_employee_count"],
            "family_reconciliation": sum(family_totals.values()) == metrics["eligible_employee_count"],
            "all_visible_cells_n_ge_30": all(int(row["employee_count"]) >= MINIMUM_COHORT for row in matrix),
            "all_visible_bands_n_ge_30": all(count >= MINIMUM_COHORT for count in level_totals.values()),
            "all_visible_families_n_ge_30": all(count >= MINIMUM_COHORT for count in family_totals.values()),
            "no_future_snapshot": dates["max_snapshot"] <= SNAPSHOT_DATE,
        },
        "limitations": [
            "La familia de grade es un proxy descriptivo del prefijo almacenado; no existe un campo oficial track confirmado en esta vista.",
            "El sufijo numérico no se interpreta como escala transversal porque el mismo sufijo cambia de significado entre prefijos.",
            "La cola de prefijos no M/P/R/S/T se agrupa con V para preservar el umbral de privacidad; no se presenta como una familia oficial.",
        ],
        "provenance": {
            "audit": {
                "query_path": str(AUDIT_SQL.relative_to(ROOT)).replace("\\", "/"),
                "sql_sha256": sql_sha256,
                "result_sha256": result_sha256,
            }
        },
        "publication_rule": "Aggregate counts and percentages only; every displayed cell and total has n >= 30; no identities, IDs, names, exact compensation or employee rows are persisted.",
        "outcome": "pass",
        "generated_on": date.today().isoformat(),
    }
    ensure_no_prohibited_keys(evidence)
    return evidence


def ensure_no_prohibited_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in PROHIBITED_KEYS:
                raise ValueError(f"La evidencia intentó persistir una clave prohibida: {key!r}.")
            ensure_no_prohibited_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            ensure_no_prohibited_keys(nested)


def main() -> None:
    parser = argparse.ArgumentParser(description="Congela evidencia agregada de Level por familia de grade.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows, sql_sha256, result_sha256 = execute_audit()
    metrics, dates, matrix, level_totals, family_totals = parse_rows(rows)
    evidence = validate_and_build(metrics, dates, matrix, level_totals, family_totals, sql_sha256, result_sha256)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + ".tmp")
    temp.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(output)
    print(output)
    print(json.dumps({"eligible_employee_count": metrics["eligible_employee_count"], "matrix_cells": len(matrix), "outcome": evidence["outcome"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
