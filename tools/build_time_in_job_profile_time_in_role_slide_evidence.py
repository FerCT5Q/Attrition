"""Freeze aggregate-only evidence for the Time in job profile / Time in role slide.

The revised slide retains current-snapshot distributions for two distinct
measures. It intentionally withholds annual attrition pills unless a measure
has three consecutive, high-coverage snapshots with complete 12-month follow-up.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_QUERY = ROOT / "queries" / "audits" / "20260918_time_in_job_profile_time_in_role_slide_evidence.sql"
COVERAGE_QUERY = ROOT / "queries" / "profiles" / "20260918_time_in_job_profile_time_in_role_coverage.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.time-in-job-profile-time-in-role-evidence-20260918.json"
)

METRICS = ("time_in_job_profile", "time_in_role")
BANDS = ("<1 year", "1–<2 years", "2–<3 years", "3–<5 years", "5–<10 years", "10+ years")
MIN_COHORT = 30
COVERAGE_THRESHOLD = 95.0
CONSECUTIVE_SNAPSHOTS_REQUIRED = 3


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run_query(query: Path, max_rows: int) -> dict[str, Any]:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "--sql-file",
            str(query),
            "--max-rows",
            str(max_rows),
            "--reporting-mode",
            "presentation",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


def one_year_before(value: str) -> date:
    parsed = date.fromisoformat(value)
    return parsed.replace(year=parsed.year - 1)


def longest_consecutive(rows: list[dict[str, Any]], metric: str, *, complete_followup_only: bool) -> int:
    latest = max(date.fromisoformat(str(row["snapshot_date"])) for row in rows)
    latest_complete_baseline = one_year_before(latest.isoformat())
    coverage_column = f"{metric}_coverage_percent"
    observable_column = f"{metric}_observable_employees"
    longest = 0
    current = 0
    for row in rows:
        snapshot = date.fromisoformat(str(row["snapshot_date"]))
        eligible = int(row["eligible_employees"])
        coverage = float(row[coverage_column])
        valid = (
            eligible >= MIN_COHORT
            and int(row["duplicate_employee_snapshot_count"]) == 0
            and int(row["conflicting_employee_snapshot_count"]) == 0
            and int(row[observable_column]) >= MIN_COHORT
            and coverage >= COVERAGE_THRESHOLD
        )
        if metric == "time_in_role":
            valid = valid and int(row["negative_time_in_role_count"]) == 0
        if complete_followup_only:
            valid = valid and snapshot <= latest_complete_baseline
        if valid:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def build_evidence(evidence_payload: dict[str, Any], coverage_payload: dict[str, Any]) -> dict[str, Any]:
    expected_evidence_columns = [
        "row_type",
        "metric",
        "category",
        "first_snapshot_date",
        "last_snapshot_date",
        "distinct_employee_count",
        "employee_snapshot_count",
        "voluntary_exits",
        "annual_attrition_rate_percent",
        "display_snapshot_date",
        "display_employee_count",
        "diagnostic_value",
    ]
    require(evidence_payload.get("columns") == expected_evidence_columns, "La consulta de la lámina devolvió columnas inesperadas.")
    require(evidence_payload.get("truncated") is False, "La consulta de la lámina fue truncada.")
    rows = evidence_payload.get("rows")
    require(isinstance(rows, list) and rows, "La consulta de la lámina no contiene filas.")

    display_rows = [row for row in rows if row.get("row_type") == "display_category"]
    annual_rows = [row for row in rows if row.get("row_type") == "annual_category"]
    diagnostic_rows = [row for row in rows if row.get("row_type") == "diagnostic"]
    require(len(diagnostic_rows) == 13, "Faltan diagnósticos de la lámina revisada.")
    diagnostics = {str(row["metric"]): int(row["diagnostic_value"]) for row in diagnostic_rows}
    for key in (
        "display_duplicate_employee_snapshot_count",
        "display_conflicting_employee_snapshot_count",
        "display_invalid_or_missing_job_profile_count",
        "display_invalid_or_missing_time_in_role_count",
    ):
        require(diagnostics.get(key) == 0, f"La distribución actual no supera la validación {key}.")
    require(diagnostics.get("display_employee_snapshot_count", 0) >= MIN_COHORT, "La distribución actual es menor al mínimo de cohorte.")
    require(diagnostics.get("history_snapshot_count") == 24, "La ventana anual debe tener 24 snapshots completos.")
    require(diagnostics.get("history_duplicate_employee_snapshot_count") == 0, "La cohorte histórica contiene duplicados employee-snapshot.")
    require(diagnostics.get("history_conflicting_employee_snapshot_count") == 0, "La cohorte histórica contiene conflictos employee-snapshot.")

    display_by_metric = {metric: [] for metric in METRICS}
    for row in display_rows:
        metric = str(row["metric"])
        require(metric in display_by_metric, f"Métrica inesperada en distribución: {metric}.")
        count = int(row["display_employee_count"])
        require(count >= MIN_COHORT, f"La banda {row['category']!r} de {metric} queda bajo n=30.")
        display_by_metric[metric].append(
            {
                "category": str(row["category"]),
                "snapshot_date": str(row["display_snapshot_date"]),
                "employee_count": count,
            }
        )
    for metric, metric_rows in display_by_metric.items():
        require(tuple(row["category"] for row in metric_rows) == tuple(sorted(BANDS)), f"La distribución {metric} tiene bandas inesperadas.")
        metric_rows.sort(key=lambda row: BANDS.index(row["category"]))

    expected_coverage_columns = [
        "snapshot_date",
        "eligible_employees",
        "duplicate_employee_snapshot_count",
        "conflicting_employee_snapshot_count",
        "time_in_job_profile_observable_employees",
        "time_in_job_profile_coverage_percent",
        "time_in_role_observable_employees",
        "time_in_role_coverage_percent",
        "negative_time_in_role_count",
    ]
    require(coverage_payload.get("columns") == expected_coverage_columns, "El perfil de cobertura devolvió columnas inesperadas.")
    require(coverage_payload.get("truncated") is False, "El perfil de cobertura fue truncado.")
    coverage_rows = coverage_payload.get("rows")
    require(isinstance(coverage_rows, list) and len(coverage_rows) >= 3, "No hay suficientes snapshots para el perfil de cobertura.")
    require(all(int(row["duplicate_employee_snapshot_count"]) == 0 for row in coverage_rows), "El perfil de cobertura contiene duplicados.")
    require(all(int(row["conflicting_employee_snapshot_count"]) == 0 for row in coverage_rows), "El perfil de cobertura contiene conflictos.")
    require(all(int(row["negative_time_in_role_count"]) == 0 for row in coverage_rows), "time_in_role contiene valores negativos.")

    coverage_summary: dict[str, dict[str, int | bool]] = {}
    for metric in METRICS:
        complete_followup_consecutive = longest_consecutive(coverage_rows, metric, complete_followup_only=True)
        total_consecutive = longest_consecutive(coverage_rows, metric, complete_followup_only=False)
        coverage_summary[metric] = {
            "max_consecutive_high_coverage_snapshots": total_consecutive,
            "max_consecutive_high_coverage_complete_followup_snapshots": complete_followup_consecutive,
            "annual_attrition_displayable": complete_followup_consecutive >= CONSECUTIVE_SNAPSHOTS_REQUIRED,
        }

    for row in annual_rows:
        metric = str(row["metric"])
        require(metric in METRICS, f"Métrica anual inesperada: {metric}.")
        exposure = int(row["employee_snapshot_count"])
        exits = int(row["voluntary_exits"])
        rate = float(row["annual_attrition_rate_percent"])
        require(exposure >= MIN_COHORT and MIN_COHORT <= exits <= exposure, "Una fila anual no satisface la regla de cohorte.")
        require(abs(rate - 100 * exits / exposure) < 0.00011, "Una tasa anual no reconcilia.")
        row["publication_status"] = (
            "publishable"
            if bool(coverage_summary[metric]["annual_attrition_displayable"])
            else "not_estimable_insufficient_longitudinal_coverage"
        )

    encoded = json.dumps({"display": display_by_metric, "annual": annual_rows}, ensure_ascii=False)
    for prohibited in ('"employee_id"', '"name"', '"email"', '"salary"', '"pay_value"'):
        require(prohibited not in encoded, f"La evidencia no puede persistir {prohibited}.")

    return {
        "artifact_type": "time_in_job_profile_time_in_role_slide_evidence",
        "version": 1,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "presentation",
        "purpose": "Actualizar la lámina para comparar sólo Time in job profile y Time in role con resultados agregados seguros.",
        "display_contract": {
            "population": "worker_type='Employee' AND employee_type='Regular' AND active_status=1",
            "grain": "employee_snapshot",
            "minimum_shared_cohort": MIN_COHORT,
            "display_snapshot_date": display_by_metric["time_in_role"][0]["snapshot_date"],
        },
        "annual_attrition_contract": {
            "target": "term_type='VOLUNTARY' con term_date en (snapshot_date, snapshot_date + 12 months]",
            "required_consecutive_high_coverage_complete_followup_snapshots": CONSECUTIVE_SNAPSHOTS_REQUIRED,
            "coverage_threshold_percent": COVERAGE_THRESHOLD,
            "publication_decision": "No mostrar tasas anuales cuando la cobertura longitudinal no satisface la regla.",
        },
        "query_provenance": {
            "evidence_sql": str(EVIDENCE_QUERY.relative_to(ROOT)).replace("\\", "/"),
            "evidence_sql_sha256": hashlib.sha256(EVIDENCE_QUERY.read_bytes()).hexdigest(),
            "coverage_sql": str(COVERAGE_QUERY.relative_to(ROOT)).replace("\\", "/"),
            "coverage_sql_sha256": hashlib.sha256(COVERAGE_QUERY.read_bytes()).hexdigest(),
        },
        "diagnostics": diagnostics,
        "coverage": coverage_summary,
        "display_rows": display_by_metric,
        "annual_rows": annual_rows,
        "outcome": "pass",
        "annual_attrition_status": "not_estimable_insufficient_longitudinal_coverage",
        "safe_display_rule": "La distribución actual se puede mostrar porque ambas medidas tienen cobertura completa en el snapshot actual, no presentan duplicados, conflictos ni valores negativos, y cada banda visible cumple n >= 30.",
        "annual_attrition_limitation": "No se muestran tasas anuales: Time in job profile no tiene tres snapshots completos con seguimiento y cobertura alta; Time in role sólo tiene uno.",
    }


def main() -> None:
    for path in (EVIDENCE_QUERY, COVERAGE_QUERY, HELPER):
        require(path.exists(), f"No existe el insumo requerido: {path}")
    evidence = build_evidence(run_query(EVIDENCE_QUERY, 100), run_query(COVERAGE_QUERY, 50))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    print(f"outcome={evidence['outcome']}; annual_attrition_status={evidence['annual_attrition_status']}")


if __name__ == "__main__":
    main()
