"""Freeze and validate aggregate-only Talent Index distribution evidence.

The artifact supports one descriptive distribution slide.  It deliberately does
not validate the Talent Index formula, its official effective date, history, or
model suitability.
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
SQL_PATH = ROOT / "queries" / "profiles" / "talent_index_latest_recoverable_distribution_20260823.sql"
QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
DEFAULT_OUTPUT = ROOT / "output" / "distribution" / "json" / "talent-index-latest-recoverable-distribution-evidence-20260909.json"
SNAPSHOT_DATE = "2026-08-23"
MINIMUM_COHORT = 30
EXPECTED_COLUMNS = [
    "row_type",
    "metric",
    "band_order",
    "band_lower",
    "band_upper",
    "band_upper_inclusive",
    "employee_count",
    "percent_of_observable",
    "metric_value",
]
REQUIRED_SUMMARY_METRICS = {
    "eligible_employees",
    "join_matched_employees",
    "join_unmatched_employees",
    "observable_employees",
    "not_observable_employees",
    "no_stored_cycle_employees",
    "selected_null_safeguard_employees",
    "selected_conflict_safeguard_employees",
    "workforce_duplicate_source_rows",
    "workforce_duplicate_employee_keys",
    "selected_cycle_duplicate_source_rows",
    "selected_cycle_duplicate_employee_keys",
    "selected_output_duplicate_employee_keys",
    "out_of_range_employees",
    "in_range_employees",
    "minimum_stored_value",
    "maximum_stored_value",
    "first_quartile",
    "median_stored_value",
    "third_quartile",
    "interquartile_range",
    "published_band_employees",
    "selected_band_width",
}
IDENTITY_MARKERS = {
    "employee_id",
    "empl_id",
    "name",
    "email",
    "manager_name",
    "manager_employee_id",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def numeric(value: object, metric: str) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"La métrica {metric!r} no es numérica.") from exc


def count(value: object, metric: str) -> int:
    result = numeric(value, metric)
    if not result.is_integer():
        raise ValueError(f"La métrica {metric!r} debe ser un conteo entero.")
    return int(result)


def run_query() -> dict[str, Any]:
    if not SQL_PATH.exists():
        raise FileNotFoundError(SQL_PATH)
    if not QUERY_HELPER.exists():
        raise FileNotFoundError(QUERY_HELPER)
    command = [
        sys.executable,
        "-B",
        str(QUERY_HELPER),
        "--sql-file",
        str(SQL_PATH.relative_to(ROOT)),
        "--max-rows",
        "100",
        "--reporting-mode",
        "internal_analysis",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("El helper de Redshift no devolvió JSON válido.") from exc
    if not isinstance(result, dict):
        raise ValueError("El helper de Redshift no devolvió un objeto JSON.")
    return result


def label_for_band(lower: float, upper: float, upper_inclusive: int) -> str:
    def compact(value: float) -> str:
        return str(int(value)) if value.is_integer() else f"{value:g}"

    connector = "–" if upper_inclusive else "–<"
    return f"{compact(lower)}{connector}{compact(upper)}"


def validate(result: dict[str, Any]) -> tuple[dict[str, int | float], list[dict[str, int | float | str]], dict[str, Any]]:
    if result.get("columns") != EXPECTED_COLUMNS or result.get("truncated") is not False:
        raise ValueError("El resultado congelado no cumple el contrato agregado esperado.")
    rows = result.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("El resultado agregado no contiene filas.")
    if IDENTITY_MARKERS.intersection(result["columns"]):
        raise ValueError("El resultado contiene una columna de identidad prohibida.")
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(EXPECTED_COLUMNS):
            raise ValueError("Una fila no cumple el esquema agregado exacto.")
        if IDENTITY_MARKERS.intersection(row):
            raise ValueError("Una fila contiene una identidad prohibida.")

    summary: dict[str, int | float] = {}
    bands: list[dict[str, int | float | str]] = []
    for row in rows:
        row_type = row["row_type"]
        if row_type == "summary":
            metric = str(row["metric"])
            if metric in summary:
                raise ValueError(f"La métrica agregada {metric!r} está duplicada.")
            value = numeric(row["metric_value"], metric)
            summary[metric] = int(value) if value.is_integer() else value
        elif row_type == "band":
            lower = numeric(row["band_lower"], "band_lower")
            upper = numeric(row["band_upper"], "band_upper")
            inclusive = count(row["band_upper_inclusive"], "band_upper_inclusive")
            employee_count = count(row["employee_count"], "employee_count")
            percentage = numeric(row["percent_of_observable"], "percent_of_observable")
            band_order = count(row["band_order"], "band_order")
            bands.append(
                {
                    "band_order": band_order,
                    "lower_bound": lower,
                    "upper_bound": upper,
                    "upper_bound_inclusive": inclusive == 1,
                    "label": label_for_band(lower, upper, inclusive),
                    "employee_count": employee_count,
                    "percent_of_observable": round(percentage, 6),
                }
            )
        else:
            raise ValueError(f"Tipo de fila inesperado: {row_type!r}.")

    if set(summary) != REQUIRED_SUMMARY_METRICS:
        missing = sorted(REQUIRED_SUMMARY_METRICS - set(summary))
        extra = sorted(set(summary) - REQUIRED_SUMMARY_METRICS)
        raise ValueError(f"Las métricas del perfil no coinciden. Faltan={missing}; extra={extra}.")
    bands.sort(key=lambda item: int(item["band_order"]))
    if not bands:
        raise ValueError("No hay bandas publicables.")

    integer_metrics = REQUIRED_SUMMARY_METRICS - {
        "minimum_stored_value",
        "maximum_stored_value",
        "first_quartile",
        "median_stored_value",
        "third_quartile",
        "interquartile_range",
    }
    for metric in integer_metrics:
        if not isinstance(summary[metric], int):
            raise ValueError(f"La métrica {metric!r} debe ser un conteo entero.")

    eligible = int(summary["eligible_employees"])
    observable = int(summary["observable_employees"])
    not_observable = int(summary["not_observable_employees"])
    if eligible < MINIMUM_COHORT:
        raise ValueError("La población elegible no alcanza el mínimo de cohorte.")
    if int(summary["join_matched_employees"]) + int(summary["join_unmatched_employees"]) != eligible:
        raise ValueError("La reconciliación del join no cuadra con la población elegible.")
    if observable + not_observable != eligible:
        raise ValueError("Observable + no observable no cuadra con la población elegible.")
    if int(summary["no_stored_cycle_employees"]) != int(summary["join_unmatched_employees"]):
        raise ValueError("El diagnóstico de no ciclo almacenado no cuadra con los no-matches del join.")
    if int(summary["out_of_range_employees"]) != 0:
        raise ValueError("Hay valores recuperables fuera de la escala observada 0–100.")
    if int(summary["in_range_employees"]) != observable:
        raise ValueError("Los valores dentro de rango no reconcilian con los valores observables.")
    if int(summary["published_band_employees"]) != observable:
        raise ValueError("Las bandas publicadas no reconcilian con los valores observables.")
    for metric in (
        "workforce_duplicate_source_rows",
        "workforce_duplicate_employee_keys",
        "selected_cycle_duplicate_source_rows",
        "selected_cycle_duplicate_employee_keys",
        "selected_output_duplicate_employee_keys",
        "selected_conflict_safeguard_employees",
    ):
        if int(summary[metric]) != 0:
            raise ValueError(f"La validación de claves/ciclos falló: {metric} debe ser cero.")

    band_total = sum(int(band["employee_count"]) for band in bands)
    if band_total != observable:
        raise ValueError("La suma de las bandas no coincide con los valores observables.")
    selected_width = int(summary["selected_band_width"])
    if selected_width not in {10, 20, 50, 100}:
        raise ValueError("El ancho de banda elegido no pertenece a la regla determinística.")
    for expected_order, band in enumerate(bands):
        if int(band["band_order"]) != expected_order:
            raise ValueError("Las bandas no son contiguas ni están ordenadas.")
        if int(band["employee_count"]) < MINIMUM_COHORT:
            raise ValueError("Una banda publicada está por debajo del mínimo de cohorte.")
        lower = float(band["lower_bound"])
        upper = float(band["upper_bound"])
        if lower != expected_order * selected_width or upper != (expected_order + 1) * selected_width:
            raise ValueError("Una banda no respeta la fusión determinística de bandas adyacentes.")
        expected_pct = 100 * int(band["employee_count"]) / observable
        if abs(float(band["percent_of_observable"]) - expected_pct) > 0.00001:
            raise ValueError("Un porcentaje de banda no reconcilia con su conteo.")
    if float(bands[0]["lower_bound"]) != 0 or float(bands[-1]["upper_bound"]) != 100:
        raise ValueError("Las bandas no cubren la escala almacenada 0–100.")
    if bands[-1]["upper_bound_inclusive"] is not True:
        raise ValueError("La última banda debe incluir el máximo 100.")

    minimum = float(summary["minimum_stored_value"])
    q1 = float(summary["first_quartile"])
    median = float(summary["median_stored_value"])
    q3 = float(summary["third_quartile"])
    maximum = float(summary["maximum_stored_value"])
    if not (0 <= minimum <= q1 <= median <= q3 <= maximum <= 100):
        raise ValueError("Los estadísticos descriptivos no respetan la escala 0–100.")
    if abs(float(summary["interquartile_range"]) - (q3 - q1)) > 0.00001:
        raise ValueError("El IQR no reconcilia con Q3 menos Q1.")

    checks = {
        "minimum_shared_cohort": MINIMUM_COHORT,
        "minimum_published_band_count": min(int(band["employee_count"]) for band in bands),
        "band_count_sum": band_total,
        "observable_reconciliation": observable,
        "not_observable_reconciliation": not_observable,
        "eligible_reconciliation": eligible,
        "identifiers_persisted": False,
        "employee_rows_persisted": False,
        "out_of_range_employees": 0,
        "selected_conflict_employees": 0,
        "selected_cycle_duplicate_employee_keys": 0,
        "selected_output_duplicate_employee_keys": 0,
    }
    return summary, bands, checks


def build(output_path: Path) -> None:
    query_result = run_query()
    metrics, distribution, privacy_checks = validate(query_result)
    sql_bytes = SQL_PATH.read_bytes()
    artifact = {
        "schema_version": 1,
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "internal_analysis",
        "variable": "Talent index",
        "semantic_type": "precomputed_metric",
        "snapshot_date": SNAPSHOT_DATE,
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1 at the 2026-08-23 monthly snapshot",
        "grain": "Distinct active regular employee in the workforce snapshot; one selected stored cycle per employee",
        "selection_rule": "Select the highest stored cycle_number per employee. Keep its talent_index only when every selected-cycle source row is non-null and all selected-cycle rows agree on exactly one value; do not use technical timestamps as an effective date and do not fall back to an older cycle.",
        "distribution_rule": "Start with contiguous 10-point bands over 0–100. When a non-empty band is below n=30, deterministically select the first eligible adjacent-band width among 20, 50, then 100 points.",
        "query_path": str(SQL_PATH.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": sha256_bytes(sql_bytes),
        "execution_date": date.today().isoformat(),
        "acceptance_rule": "Observable + not observable = eligible; join matched + unmatched = eligible; one selected output value per employee; zero selected conflicts, duplicate keys, and out-of-range values; bands sum to observable values and every published band has n >= 30.",
        "metrics": metrics,
        "distribution": distribution,
        "privacy_checks": privacy_checks,
        "query_result": query_result,
        "query_result_sha256": sha256_bytes(canonical_json(query_result)),
        "limitations": [
            "This is the currently recoverable stored value for employees active on 2026-08-23.",
            "It does not prove that Talent Index was calculated, approved, or effective on that workforce date.",
            "It does not validate the formula, lineage, history, timing, or attrition-model suitability of the stored metric.",
        ],
        "outcome": "pass",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    print(output_path)
    print(f"observable={metrics['observable_employees']}")
    print(f"bands={len(distribution)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Congela evidencia agregada de distribución para Talent Index.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.output)
