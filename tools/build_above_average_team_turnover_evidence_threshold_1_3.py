"""Freeze presentation-safe aggregate evidence for candidata 44.

The script reuses the published v4 source/reconciliation evidence, executes
the current 1.3 threshold audit and one presentation query, and freezes only
aggregate results. It never selects, persists, or prints employee or manager
identities, manager-level rates, or rankings.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT_RUN = ROOT / "output" / "assessments" / "above-average-team-turnover-v4-20260910-r13"
ASSESSMENT_EVIDENCE = (
    ASSESSMENT_RUN
    / "vars"
    / "01-above-average-team-turnover"
    / "evidence"
    / "query-results.json"
)
QUERY = ROOT / "queries" / "profiles" / "above_average_team_turnover_presentation_distribution_20260911_threshold_1_3.sql"
AUDIT_QUERY = ROOT / "queries" / "audits" / "above_average_team_turnover_18m_audit_20260911_threshold_1_3.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "above-average-team-turnover-evidence-20260911-threshold-1_3.json"
QUERY_HELPER = ROOT / "tools" / "read_only_redshift_query_helper.py"
MINIMUM_COHORT = 30

EXPECTED_COLUMNS = [
    "snapshot_date",
    "row_type",
    "signal_value",
    "employee_count",
    "eligible_employees",
    "observable_employees",
    "flagged_employees",
    "unknown_employees",
    "weighted_benchmark_six_month_rate",
    "threshold_six_month_rate",
]
AUDIT_EXPECTED_COLUMNS = [
    "evaluated_snapshot_count",
    "expected_interval_count",
    "minimum_eligible_interval_count",
    "minimum_eligible_average_team_size",
    "minimum_eligible_voluntary_exit_count",
    "duplicate_count",
    "conflicting_manager_count",
    "raw_voluntary_event_duplicate_rows",
    "voluntary_event_type_conflict_count",
    "event_multiple_interval_assignment_count",
    "event_multiple_manager_assignment_count",
    "future_event_usage_count",
    "eligible_count",
    "matched_count",
    "unmatched_count",
    "multi_match_count",
    "rule_implementation_failure_count",
    "benchmark_reconciliation_failure_count",
]
FORBIDDEN_COLUMNS = {
    "employee_id",
    "manager_employee_id",
    "manager_name",
    "employee_name",
    "emp_name",
    "name",
    "email",
    "term_date",
}


def load_json(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"El artefacto JSON debe ser un objeto: {path}")
    return document


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _assessment_row(document: dict[str, Any], suffix: str) -> dict[str, Any]:
    matches = [
        rows
        for key, rows in document.items()
        if str(key).replace("\\", "/").endswith(suffix)
    ]
    if len(matches) != 1 or not isinstance(matches[0], list) or len(matches[0]) != 1:
        raise ValueError(f"No existe una fila congelada única para {suffix}.")
    row = matches[0][0]
    if not isinstance(row, dict):
        raise ValueError(f"La fila congelada de {suffix} no es un objeto.")
    return row


def validate_assessment_evidence(
    document: dict[str, Any], audit_override: dict[str, Any] | None = None
) -> dict[str, dict[str, Any]]:
    """Require the executed v4 gates before reusing their aggregate evidence."""
    source = _assessment_row(document, "above_average_team_turnover_source_access_20260910.sql")
    audit = audit_override or _assessment_row(document, "above_average_team_turnover_18m_audit_20260910.sql")
    reconciliation = _assessment_row(
        document, "above_average_team_turnover_termination_reconciliation_20260910.sql"
    )
    if source.get("missing_items") != 0:
        raise ValueError("La auditoría de acceso de fuente no aprobó.")
    expected_audit = {
        "evaluated_snapshot_count": 6,
        "expected_interval_count": 18,
        "minimum_eligible_interval_count": 18,
        "minimum_eligible_voluntary_exit_count": 2,
        "duplicate_count": 0,
        "conflicting_manager_count": 0,
        "event_multiple_interval_assignment_count": 0,
        "event_multiple_manager_assignment_count": 0,
        "future_event_usage_count": 0,
        "unmatched_count": 0,
        "multi_match_count": 0,
        "rule_implementation_failure_count": 0,
        "benchmark_reconciliation_failure_count": 0,
    }
    for metric, expected in expected_audit.items():
        if audit.get(metric) != expected:
            raise ValueError(f"La auditoría v4 no aprobó {metric}={expected}.")
    if float(str(audit.get("minimum_eligible_average_team_size"))) < 4:
        raise ValueError("La auditoría v4 no confirmó tamaño medio de equipo >=4.")
    if reconciliation.get("reconciliation_executed") != 1:
        raise ValueError("La reconciliación con all_terminations no fue ejecutada.")
    return {"source": source, "audit": audit, "reconciliation": reconciliation}


def load_helper() -> Any:
    module_spec = importlib.util.spec_from_file_location(
        "above_average_team_turnover_readonly", QUERY_HELPER
    )
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el helper read-only: {QUERY_HELPER}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def execute_aggregate_query(
    sql: str, expected_columns: list[str] | None = None, query_label: str = "distribución"
) -> list[dict[str, Any]]:
    helper = load_helper()
    guarded_sql = helper.validate_readonly(sql)
    with helper.connect() as connection:
        connection.set_session(readonly=True, autocommit=True)
        with connection.cursor(cursor_factory=helper.psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(guarded_sql)
            if cursor.description is None:
                raise ValueError(f"La consulta {query_label} no devolvió columnas.")
            columns = [description.name for description in cursor.description]
            expected = expected_columns or EXPECTED_COLUMNS
            if columns != expected:
                raise ValueError(f"El esquema de {query_label} cambió: {columns}")
            if FORBIDDEN_COLUMNS.intersection({column.lower() for column in columns}):
                raise ValueError("La consulta intentó publicar una columna de identidad o evento.")
            rows = [dict(row) for row in cursor.fetchall()]
    return rows


def as_int(value: Any, field: str) -> int:
    if value is None:
        raise ValueError(f"Falta el conteo agregado {field}.")
    numeric = float(str(value))
    if not numeric.is_integer():
        raise ValueError(f"{field} debe ser un conteo entero.")
    return int(numeric)


def as_float(value: Any, field: str) -> float:
    if value is None:
        raise ValueError(f"Falta la tasa agregada {field}.")
    numeric = float(str(value))
    if numeric <= 0:
        raise ValueError(f"{field} debe ser positiva.")
    return numeric


def validate_distribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) != 4:
        raise ValueError("La evidencia debe tener tres buckets y un resumen agregado.")
    distributions = [row for row in rows if row.get("row_type") == "distribution"]
    summaries = [row for row in rows if row.get("row_type") == "summary"]
    if len(distributions) != 3 or len(summaries) != 1:
        raise ValueError("La evidencia no conserva el contrato de buckets y resumen.")
    by_signal = {str(row.get("signal_value")): row for row in distributions}
    if set(by_signal) != {"0", "1", "Unknown"}:
        raise ValueError("Los buckets publicados deben ser exactamente 0, 1 y Unknown.")
    counts = {signal: as_int(row.get("employee_count"), f"{signal}.employee_count") for signal, row in by_signal.items()}
    if any(count < MINIMUM_COHORT for count in counts.values()):
        raise ValueError(f"Cada bucket publicado debe cumplir n >= {MINIMUM_COHORT}.")
    summary = summaries[0]
    snapshot = str(summary.get("snapshot_date") or "")
    if not snapshot:
        raise ValueError("Falta el cierre de la distribución.")
    eligible = as_int(summary.get("eligible_employees"), "eligible_employees")
    observable = as_int(summary.get("observable_employees"), "observable_employees")
    flagged = as_int(summary.get("flagged_employees"), "flagged_employees")
    unknown = as_int(summary.get("unknown_employees"), "unknown_employees")
    benchmark = as_float(
        summary.get("weighted_benchmark_six_month_rate"),
        "weighted_benchmark_six_month_rate",
    )
    threshold = as_float(summary.get("threshold_six_month_rate"), "threshold_six_month_rate")
    if counts["0"] + counts["1"] + counts["Unknown"] != eligible:
        raise ValueError("Los buckets 0/1/Unknown no reconcilian con la población elegible.")
    if counts["0"] + counts["1"] != observable or counts["1"] != flagged or counts["Unknown"] != unknown:
        raise ValueError("Los conteos de observabilidad, flag o Unknown no reconcilian.")
    if abs(threshold - benchmark * 1.3) > 0.000000001:
        raise ValueError("El umbral publicado no reconcilia con benchmark * 1.3.")
    return {
        "snapshot_date": snapshot,
        "distribution": [
            {"signal": signal, "employee_count": counts[signal]}
            for signal in ("0", "1", "Unknown")
        ],
        "eligible_employees": eligible,
        "observable_employees": observable,
        "flagged_employees": flagged,
        "unknown_employees": unknown,
        "weighted_benchmark_six_month_rate": benchmark,
        "threshold_six_month_rate": threshold,
    }


def build_evidence(output: Path = OUTPUT) -> dict[str, Any]:
    if not ASSESSMENT_EVIDENCE.exists():
        raise FileNotFoundError(ASSESSMENT_EVIDENCE)
    if not QUERY.exists():
        raise FileNotFoundError(QUERY)
    if not AUDIT_QUERY.exists():
        raise FileNotFoundError(AUDIT_QUERY)
    assessment_document = load_json(ASSESSMENT_EVIDENCE)
    audit_sql = AUDIT_QUERY.read_text(encoding="utf-8")
    audit_rows = execute_aggregate_query(audit_sql, AUDIT_EXPECTED_COLUMNS, "auditoría v4")
    if len(audit_rows) != 1:
        raise ValueError("La auditoría v4 de 1.3 debe devolver una sola fila agregada.")
    assessment_gates = validate_assessment_evidence(assessment_document, audit_rows[0])
    sql = QUERY.read_text(encoding="utf-8")
    rows = execute_aggregate_query(sql)
    distribution = validate_distribution(rows)
    audit = assessment_gates["audit"]
    reconciliation = assessment_gates["reconciliation"]
    evidence = {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "presentation",
        "variable": "Above-average team turnover",
        "candidate_number": 44,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "source_assessment_run": ASSESSMENT_RUN.name,
        "population": "Empleados regulares activos con manager_employee_id en el cierre mensual t.",
        "grain": "Empleado-snapshot mensual; cálculo intermedio manager-snapshot agregado.",
        "definition": "1 si el manager vigente es elegible y su tasa histórica Voluntary equivalente a seis meses es >=1.3 veces el benchmark ponderado; 0 si es elegible y queda por debajo; Unknown en cualquier otro caso.",
        "window": "18 intervalos mensuales cerrados anteriores a t (19 cierres).",
        "event_scope": "term_type exactamente Voluntary; Voluntary Exception, involuntarias y nulos se excluyen.",
        "attribution": "Cada salida se atribuye al manager del empleado al inicio del intervalo mensual correspondiente.",
        "eligibility": {
            "required_consecutive_intervals": 18,
            "minimum_average_team_size": 4,
            "minimum_distinct_voluntary_exits": 2,
        },
        "benchmark": {
            "definition": "Salidas Voluntary de managers elegibles / exposición histórica elegible * 6; equivalente al promedio de tasas ponderado por tamaño medio de equipo.",
            "six_month_rate": distribution["weighted_benchmark_six_month_rate"],
            "flag_threshold_multiplier": 1.3,
            "flag_threshold_six_month_rate": distribution["threshold_six_month_rate"],
        },
        "latest_snapshot": distribution["snapshot_date"],
        "distribution": distribution["distribution"],
        "aggregate_counts": {
            key: distribution[key]
            for key in ("eligible_employees", "observable_employees", "flagged_employees", "unknown_employees")
        },
        "assessment_validation": {
            "source_missing_items": audit.get("missing_items", assessment_gates["source"].get("missing_items")),
            "snapshots_checked": audit["evaluated_snapshot_count"],
            "interval_count": audit["expected_interval_count"],
            "minimum_eligible_average_team_size": float(str(audit["minimum_eligible_average_team_size"])),
            "minimum_eligible_voluntary_exits": audit["minimum_eligible_voluntary_exit_count"],
            "duplicate_count": audit["duplicate_count"],
            "multiple_event_interval_assignments": audit["event_multiple_interval_assignment_count"],
            "multiple_event_manager_assignments": audit["event_multiple_manager_assignment_count"],
            "future_event_usage_count": audit["future_event_usage_count"],
            "unmatched_employee_assignments": audit["unmatched_count"],
            "multi_match_employee_assignments": audit["multi_match_count"],
            "rule_implementation_failure_count": audit["rule_implementation_failure_count"],
            "benchmark_reconciliation_failure_count": audit["benchmark_reconciliation_failure_count"],
        },
        "termination_source_reconciliation": {
            key: reconciliation[key]
            for key in (
                "primary_event_count",
                "all_terminations_event_count",
                "matched_event_count",
                "primary_only_event_count",
                "all_terminations_only_event_count",
                "discrepancy_count",
                "primary_match_rate_percent",
            )
        },
        "privacy": {
            "minimum_shared_cohort": MINIMUM_COHORT,
            "identifiers_persisted": False,
            "employee_rows_persisted": False,
            "manager_rates_persisted": False,
            "manager_rankings_persisted": False,
        },
        "interpretation_limit": "Señal asociativa y sensible de contexto de equipo; no es evaluación individual de managers, atribución causal ni feature productiva aprobada.",
        "definition_limit": "Definition permanece en 1: falta lineage aprobado de terminaciones y la reconciliación agregada con all_terminations conserva diferencias.",
        "provenance": {
            "assessment_evidence": str(ASSESSMENT_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "assessment_evidence_sha256": sha256_bytes(ASSESSMENT_EVIDENCE.read_bytes()),
            "presentation_query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
            "presentation_query_sha256": sha256_bytes(sql.encode("utf-8")),
            "presentation_result_sha256": sha256_bytes(
                json.dumps(rows, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
            ),
            "audit_query": str(AUDIT_QUERY.relative_to(ROOT)).replace("\\", "/"),
            "audit_query_sha256": sha256_bytes(audit_sql.encode("utf-8")),
            "audit_result_sha256": sha256_bytes(
                json.dumps(audit_rows, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
            ),
        },
        "outcome": "pass",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return evidence


if __name__ == "__main__":
    document = build_evidence()
    print(OUTPUT)
    print(
        "snapshot={snapshot}; eligible={eligible:,}; observable={observable:,}; "
        "flagged={flagged:,}; unknown={unknown:,}".format(
            snapshot=document["latest_snapshot"],
            eligible=document["aggregate_counts"]["eligible_employees"],
            observable=document["aggregate_counts"]["observable_employees"],
            flagged=document["aggregate_counts"]["flagged_employees"],
            unknown=document["aggregate_counts"]["unknown_employees"],
        )
    )
