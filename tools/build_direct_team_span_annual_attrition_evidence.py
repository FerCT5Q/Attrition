"""Freeze aggregate-only evidence for the V7 direct-team-span follow-up.

The direct-report span is recalculated from reporting relationships inside the
2025-08-24 snapshot.  Individual relationships, people, and managers remain
inside the database query; this script only writes validated aggregate bands.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SQL = ROOT / "queries" / "audits" / "direct_team_span_annual_attrition_20260923.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "direct-team-span-annual-attrition-evidence-20260923.json"
AUTHORIZATION_FILE = ROOT / "config" / "attrition_v7_internal_analysis_authorization_20260917.json"
READONLY_QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"

BASELINE_DATE = "2025-08-24"
OUTCOME_CUTOFF = "2026-08-23"
OUTCOME_WINDOW = "(2025-08-24, 2026-08-23]"
EXPECTED_BANDS = (("1-4", "1–4"), ("5-9", "5–9"), ("10-14", "10–14"), ("15-19", "15–19"), ("20-29", "20–29"), ("30+", "30+"))
EXPECTED_METRICS = {
    "baseline_employee_count",
    "eligible_employee_count",
    "unresolvable_manager_exclusion_count",
    "eligible_team_count",
    "baseline_voluntary_exits",
    "manager_assignment_conflict_count",
    "missing_manager_value_count",
    "manager_not_active_regular_snapshot_count",
}
EXPECTED_CONTRACT = {
    "baseline_employee_count": 45_003,
    "eligible_employee_count": 44_737,
    "unresolvable_manager_exclusion_count": 266,
    "baseline_voluntary_exits": 2_480,
    "manager_assignment_conflict_count": 0,
    "missing_manager_value_count": 1,
    "manager_not_active_regular_snapshot_count": 265,
}
EXPECTED_EXACT = {
    5: {"employee_count": 7_160, "team_count": 1_432, "voluntary_exits": 390, "annual_attrition_rate_percent": 5.446927374301675},
    20: {"employee_count": 80, "team_count": 4, "voluntary_exits": 7, "annual_attrition_rate_percent": 8.75},
}


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def hash_json(value: object) -> str:
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=True, default=str, separators=(",", ":")).encode("utf-8"))


def load_helper() -> Any:
    spec = importlib.util.spec_from_file_location("direct_team_span_readonly_helper", READONLY_QUERY_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load the approved read-only helper: {READONLY_QUERY_HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def execute_query() -> tuple[list[dict[str, Any]], str, str]:
    sql = AUDIT_SQL.read_text(encoding="utf-8")
    helper = load_helper()
    readonly_sql = helper.validate_readonly(sql)
    with helper.connect() as connection:
        connection.autocommit = True
        with connection.cursor(cursor_factory=helper.psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(readonly_sql)
            rows = [dict(row) for row in cursor.fetchall()]
    return rows, digest(sql.encode("utf-8")), hash_json(rows)


def integer(value: object, name: str) -> int:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc
    if not number.is_integer():
        raise ValueError(f"{name} must be an integer.")
    return int(number)


def parse_rows(rows: list[dict[str, Any]]) -> tuple[dict[str, int], list[dict[str, Any]], dict[int, dict[str, Any]]]:
    expected_columns = {
        "row_type", "metric", "span_band", "band_order", "direct_report_count",
        "employee_count", "team_count", "voluntary_exits", "annual_attrition_rate_percent",
    }
    metrics: dict[str, int] = {}
    bands: list[dict[str, Any]] = []
    exact: dict[int, dict[str, Any]] = {}
    for row in rows:
        if set(row) != expected_columns:
            raise ValueError(f"Unexpected aggregate result schema: {sorted(row)}")
        row_type = str(row["row_type"])
        if row_type == "metric":
            metric = str(row["metric"])
            if metric in metrics or metric not in EXPECTED_METRICS:
                raise ValueError(f"Unexpected or duplicated metric: {metric!r}")
            if metric == "eligible_team_count":
                metrics[metric] = integer(row["team_count"], metric)
            elif metric == "baseline_voluntary_exits":
                metrics[metric] = integer(row["voluntary_exits"], metric)
            else:
                metrics[metric] = integer(row["employee_count"], metric)
        elif row_type == "span_band":
            if str(row["metric"]) != "direct_team_span" or row["span_band"] is None:
                raise ValueError("Invalid direct-team span band row.")
            bands.append({
                "source_label": str(row["span_band"]),
                "band_order": integer(row["band_order"], "band_order"),
                "employee_count": integer(row["employee_count"], "employee_count"),
                "team_count": integer(row["team_count"], "team_count"),
                "voluntary_exits": integer(row["voluntary_exits"], "voluntary_exits"),
                "annual_attrition_rate_percent": float(row["annual_attrition_rate_percent"]),
            })
        elif row_type == "exact_span":
            span = integer(row["direct_report_count"], "direct_report_count")
            if span in exact or span not in EXPECTED_EXACT:
                raise ValueError(f"Unexpected or duplicated exact direct-team span: {span}")
            exact[span] = {
                "employee_count": integer(row["employee_count"], "exact employee_count"),
                "team_count": integer(row["team_count"], "exact team_count"),
                "voluntary_exits": integer(row["voluntary_exits"], "exact voluntary_exits"),
                "annual_attrition_rate_percent": float(row["annual_attrition_rate_percent"]),
            }
        else:
            raise ValueError(f"Unknown aggregate row type: {row_type!r}")
    if set(metrics) != EXPECTED_METRICS:
        raise ValueError(f"Metric contract mismatch: {sorted(set(metrics) ^ EXPECTED_METRICS)}")
    return metrics, bands, exact


def validate(metrics: dict[str, int], raw_bands: list[dict[str, Any]], exact: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    for name, expected in EXPECTED_CONTRACT.items():
        if metrics[name] != expected:
            raise ValueError(f"Acceptance contract failed for {name}: expected {expected:,}, received {metrics[name]:,}.")
    if metrics["baseline_employee_count"] != metrics["eligible_employee_count"] + metrics["unresolvable_manager_exclusion_count"]:
        raise ValueError("Coverage does not reconcile to the active regular baseline.")
    expected_labels = [source for source, _ in EXPECTED_BANDS]
    raw_bands.sort(key=lambda row: int(row["band_order"]))
    if [str(row["source_label"]) for row in raw_bands] != expected_labels:
        raise ValueError("The six configured span bands are incomplete or out of order.")
    rendered: list[dict[str, Any]] = []
    for row, (_, label) in zip(raw_bands, EXPECTED_BANDS):
        count = int(row["employee_count"])
        teams = int(row["team_count"])
        exits = int(row["voluntary_exits"])
        rate = float(row["annual_attrition_rate_percent"])
        if count < 30 or teams <= 0 or not 0 <= exits <= count:
            raise ValueError(f"Invalid display aggregate for span band {label}.")
        if not math.isclose(rate, 100 * exits / count, abs_tol=0.00011):
            raise ValueError(f"Annual attrition does not reconcile for span band {label}.")
        rendered.append({
            "label": label,
            "employee_count": count,
            "employee_share_percent": round(100 * count / metrics["eligible_employee_count"], 8),
            "team_count": teams,
            "voluntary_exits": exits,
            "annual_attrition_rate_percent": rate,
            "publication_status": "internal_analysis_authorized",
        })
    if sum(int(row["employee_count"]) for row in rendered) != metrics["eligible_employee_count"]:
        raise ValueError("Span-band employees do not reconcile to the eligible population.")
    if sum(int(row["team_count"]) for row in rendered) != metrics["eligible_team_count"]:
        raise ValueError("Span-band teams do not reconcile to the derived team universe.")
    if sum(int(row["voluntary_exits"]) for row in rendered) != metrics["baseline_voluntary_exits"]:
        raise ValueError("Span-band voluntary exits do not reconcile to the eligible baseline.")
    if set(exact) != set(EXPECTED_EXACT):
        raise ValueError("The exact-span comparison rows are incomplete.")
    for span, expected in EXPECTED_EXACT.items():
        actual = exact[span]
        for key in ("employee_count", "team_count", "voluntary_exits"):
            if actual[key] != expected[key]:
                raise ValueError(f"Exact span {span} failed {key}: expected {expected[key]:,}, received {actual[key]:,}.")
        if actual["employee_count"] != span * actual["team_count"]:
            raise ValueError(f"Exact span {span} does not reconcile employees to teams times direct reports.")
        if not math.isclose(actual["annual_attrition_rate_percent"], 100 * actual["voluntary_exits"] / actual["employee_count"], abs_tol=0.00011):
            raise ValueError(f"Exact span {span} attrition does not reconcile.")
        if not math.isclose(actual["annual_attrition_rate_percent"], expected["annual_attrition_rate_percent"], abs_tol=0.00011):
            raise ValueError(f"Exact span {span} attrition differs from the approved result.")
    return rendered


def ensure_safe(value: object) -> None:
    prohibited = {
        "employee_id", "manager_employee_id", "manager_name", "employee_name", "name",
        "email", "direct_report_employee_id", "team_manager_id",
    }
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in prohibited:
                raise ValueError(f"Restricted field persisted: {key!r}")
            ensure_safe(nested)
    elif isinstance(value, list):
        for nested in value:
            ensure_safe(nested)


def build_evidence() -> dict[str, object]:
    rows, sql_hash, result_hash = execute_query()
    metrics, raw_bands, exact = parse_rows(rows)
    bands = validate(metrics, raw_bands, exact)
    authorization = json.loads(AUTHORIZATION_FILE.read_text(encoding="utf-8"))
    if authorization.get("status") != "approved" or authorization.get("reporting_mode") != "internal_analysis":
        raise ValueError("The V7 internal-analysis authorization is not approved.")
    if not authorization.get("small_cell_exception", {}).get("allow_subthreshold_aggregate_buckets"):
        raise ValueError("The V7 authorization does not allow the needed small aggregate team count.")
    coverage_percent = 100 * metrics["eligible_employee_count"] / metrics["baseline_employee_count"]
    evidence: dict[str, object] = {
        "artifact_type": "aggregate_direct_team_span_attrition_evidence",
        "version": 1,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "artifact_classification": "internal_analysis",
        "variable": "Tamaño de equipo directo (span) reconstruido",
        "semantic_type": "hierarchy",
        "baseline_snapshot_date": BASELINE_DATE,
        "outcome_cutoff_date": OUTCOME_CUTOFF,
        "outcome_window": OUTCOME_WINDOW,
        "population": "Personas Employee, Regular y activas al snapshot base; el visual conserva solo relaciones cuyo manager se resuelve como Employee, Regular y activo en ese mismo snapshot.",
        "grain": "empleado del snapshot base",
        "definition": "El span de una persona es el número de empleados elegibles que reportan directamente a su manager en el mismo snapshot. Se recalcula desde la relación de reporting del snapshot; los campos almacenados de número de reportes no se usan como definición primaria. Attrition anual = terminaciones strict VOLUNTARY del mismo cohorte base en la ventana prospectiva divididas entre empleados base de la banda.",
        "coverage": {
            "baseline_employee_count": metrics["baseline_employee_count"],
            "eligible_employee_count": metrics["eligible_employee_count"],
            "eligible_percent": coverage_percent,
            "unresolvable_manager_exclusion_count": metrics["unresolvable_manager_exclusion_count"],
            "exclusion_treatment": "Exclusión de cobertura; no se muestra como banda de span.",
            "manager_assignment_conflict_count": metrics["manager_assignment_conflict_count"],
            "missing_manager_value_count": metrics["missing_manager_value_count"],
            "manager_not_active_regular_snapshot_count": metrics["manager_not_active_regular_snapshot_count"],
        },
        "bands": bands,
        "exact_span_comparison": {
            "five_direct_reports": {
                "direct_report_count": 5,
                **exact[5],
                "exploratory": False,
            },
            "twenty_direct_reports": {
                "direct_report_count": 20,
                **exact[20],
                "exploratory": True,
                "exploratory_reason": "Solo cuatro equipos contribuyen al valor exacto; la comparación es descriptiva y no causal.",
            },
        },
        "validation": {
            "question": "¿Cómo se distribuyen los empleados por el tamaño directo de su manager y cuál es su attrition voluntaria prospectiva de 12 meses?",
            "reason": "El tamaño del equipo puede describir el contexto de gestión, pero debe calcularse desde relaciones del snapshot y no desde un conteo almacenado cuya definición no fue confirmada.",
            "method": "Consulta agregada de solo lectura que deduplica la relación de reporting del 24-ago-2025, exige manager resoluble dentro de la población activa Regular, cuenta miembros directos por manager y enlaza solo salidas strict VOLUNTARY posteriores del mismo cohorte base.",
            "acceptance_rule": "La cobertura debe reconciliar 45,003 = 44,737 elegibles + 266 exclusiones; seis bandas deben sumar 44,737 empleados, 9,665 equipos y 2,480 salidas; tamaño exacto 5 debe ser 7,160 empleados / 1,432 equipos y tamaño exacto 20 debe ser 80 / 4; cada tasa debe reconciliar salidas / empleados.",
            "metrics": {
                "baseline_employee_count": metrics["baseline_employee_count"],
                "eligible_employee_count": metrics["eligible_employee_count"],
                "eligible_percent": coverage_percent,
                "coverage_exclusion_count": metrics["unresolvable_manager_exclusion_count"],
                "eligible_team_count": metrics["eligible_team_count"],
                "baseline_voluntary_exits": metrics["baseline_voluntary_exits"],
                "published_band_count": len(bands),
                "five_direct_reports_employee_count": exact[5]["employee_count"],
                "five_direct_reports_team_count": exact[5]["team_count"],
                "twenty_direct_reports_employee_count": exact[20]["employee_count"],
                "twenty_direct_reports_team_count": exact[20]["team_count"],
            },
            "result": "Las seis bandas reconcilian exactamente la población elegible y sus salidas. La cobertura alcanza 99.41%; las 266 relaciones no resolubles se excluyen del denominador y del gráfico. El tamaño exacto 20 reúne cuatro equipos, por lo que se mantiene como comparación exploratoria.",
            "conclusion": "El visual es descriptivo de distribución y attrition observada por banda; no prueba que el tamaño de equipo cause attrition.",
            "outcome": "pass",
        },
        "authorization": {
            "path": str(AUTHORIZATION_FILE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(AUTHORIZATION_FILE.read_bytes()),
            "authorization_id": authorization["authorization_id"],
            "authorized_audience": authorization["authorized_audience"],
            "small_cell_exception_applied": True,
        },
        "provenance": {
            "audit_sql": str(AUDIT_SQL.relative_to(ROOT)).replace("\\", "/"),
            "audit_sql_sha256": sql_hash,
            "aggregate_result_sha256": result_hash,
            "execution_date": date.today().isoformat(),
            "query_mode": "read_only_aggregate",
            "raw_aggregate_rows_persisted": False,
        },
        "privacy_checks": {
            "identity_fields_persisted": False,
            "employee_rows_persisted": False,
            "manager_rows_persisted": False,
            "names_persisted": False,
            "all_rows_aggregate_only": True,
            "small_team_count_authorized_for_internal_analysis": True,
        },
        "outcome": "pass",
    }
    ensure_safe(evidence)
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Build aggregate-only direct-team-span annual attrition evidence.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    evidence = build_evidence()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    coverage = evidence["coverage"]
    validation = evidence["validation"]
    print(f"Wrote aggregate-only evidence: {args.output}")
    print(
        "Baseline employees=" + f"{coverage['baseline_employee_count']:,}; "
        + "eligible=" + f"{coverage['eligible_employee_count']:,}; "
        + "voluntary exits=" + f"{validation['metrics']['baseline_voluntary_exits']:,}; bands={len(evidence['bands'])}"
    )


if __name__ == "__main__":
    main()
