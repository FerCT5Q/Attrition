"""Build aggregate annual-comparison evidence for slides 9 and 10.

The script delegates every Redshift call to the project's guarded read-only
helper. It retains only aggregate rows, aligns the annual results to the
existing six-month display calendar, and writes a frozen JSON artifact.
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
RUNNER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
ANNUAL_SQL = ROOT / "queries" / "audits" / "more_than_1_employee_leaves_team_12m_20260909.sql"
COVERAGE_SQL = ROOT / "queries" / "audits" / "more_than_1_employee_leaves_annual_window_coverage_20260909.sql"
PRIMARY_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v2.more-than-1-employee-leaves-evidence-20260908.json"
OUTPUT = ROOT / "output" / "distribution" / "json" / "more-than-1-employee-leaves-annual-evidence-20260909.json"
MINIMUM_COHORT = 30
SCOPES = ("all_teams", "teams_gt_5")
ATTRIBUTIONS = ("manager_at_evaluation", "manager_at_exit")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run_aggregate_query(path: Path, maximum_rows: int) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(RUNNER),
            "--sql-file",
            str(path),
            "--max-rows",
            str(maximum_rows),
            "--reporting-mode",
            "internal_analysis",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    payload = json.loads(completed.stdout)
    if payload.get("truncated"):
        raise ValueError(f"La consulta agregada fue truncada: {path.relative_to(ROOT)}")
    return payload


def numeric(value: Any) -> int | float:
    if isinstance(value, int | float):
        return value
    text = str(value)
    return float(text) if "." in text else int(text)


def primary_lookup(primary: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str, str], dict[str, Any]] = {}
    for scope in primary["scopes"]:
        scope_key = str(scope["key"])
        for attribution in ATTRIBUTIONS:
            for row in scope["monthly_series"][attribution]:
                key = (scope_key, attribution, str(row["snapshot_date"]))
                if key in lookup:
                    raise ValueError(f"Punto semestral duplicado: {key}")
                lookup[key] = row
    return lookup


def main() -> None:
    if not RUNNER.exists() or not ANNUAL_SQL.exists() or not COVERAGE_SQL.exists() or not PRIMARY_EVIDENCE.exists():
        raise FileNotFoundError("Falta un insumo para construir la evidencia anual de equipo.")

    annual_query = run_aggregate_query(ANNUAL_SQL, maximum_rows=500)
    coverage_query = run_aggregate_query(COVERAGE_SQL, maximum_rows=100)
    primary = json.loads(PRIMARY_EVIDENCE.read_text(encoding="utf-8"))
    if primary.get("outcome") != "pass" or int(primary.get("window_months", 0)) != 6:
        raise ValueError("La evidencia semestral primaria no es válida para alinear la comparación anual.")

    annual_rows = [row for row in annual_query["rows"] if row["row_type"] == "monthly_series"]
    annual_audit = {
        str(row["metric"]): numeric(row["metric_value"])
        for row in annual_query["rows"]
        if row["row_type"] == "audit"
    }
    coverage_rows = coverage_query["rows"]
    if len(coverage_rows) != int(primary["evaluation_snapshot_count"]):
        raise ValueError("La auditoría de cobertura no devuelve el mismo calendario primario de 40 snapshots.")

    primary_by_key = primary_lookup(primary)
    primary_dates = {key[2] for key in primary_by_key}
    if len(primary_dates) != int(primary["evaluation_snapshot_count"]):
        raise ValueError("La evidencia primaria tiene fechas mensuales inconsistentes entre scopes o atribuciones.")

    complete_dates = {
        str(row["snapshot_date"])
        for row in coverage_rows
        if int(row["has_complete_annual_window"]) == 1
    }
    for row in coverage_rows:
        is_complete = int(row["has_complete_annual_window"]) == 1
        if is_complete and (int(row["annual_snapshot_count"]) < 12 or int(row["observed_span_days"]) < 330):
            raise ValueError("La cobertura anual marcada como completa no cumple la regla declarada.")

    annual_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in annual_rows:
        key = (str(row["scope"]), str(row["attribution"]), str(row["snapshot_date"]))
        if key in annual_by_key:
            raise ValueError(f"Punto anual duplicado: {key}")
        annual_by_key[key] = row

    selected_dates = sorted(primary_dates & complete_dates)
    excluded_dates = sorted(primary_dates - complete_dates)
    expected_keys = {(scope, attribution, snapshot_date) for scope in SCOPES for attribution in ATTRIBUTIONS for snapshot_date in selected_dates}
    missing_annual_keys = expected_keys - set(annual_by_key)
    if missing_annual_keys:
        raise ValueError(f"Faltan puntos anuales completos para el calendario primario: {len(missing_annual_keys)}")

    annual_below_six_month_count = 0
    denominator_mismatch_count = 0
    scopes: list[dict[str, Any]] = []
    for scope_key in SCOPES:
        series_by_attribution: dict[str, list[dict[str, int | float | str]]] = {}
        for attribution in ATTRIBUTIONS:
            points: list[dict[str, int | float | str]] = []
            for snapshot_date in selected_dates:
                key = (scope_key, attribution, snapshot_date)
                annual = annual_by_key[key]
                primary_row = primary_by_key[key]
                annual_flagged = int(numeric(annual["flagged_employees"]))
                annual_observable = int(numeric(annual["observable_employees"]))
                primary_flagged = int(primary_row["flagged_employees"])
                primary_observable = int(primary_row["observable_employees"])
                if annual_observable < MINIMUM_COHORT or annual_flagged > annual_observable:
                    raise ValueError(f"Punto anual no publicable: {key}")
                if annual_observable != primary_observable:
                    denominator_mismatch_count += 1
                if annual_flagged < primary_flagged:
                    annual_below_six_month_count += 1
                points.append(
                    {
                        "snapshot_date": snapshot_date,
                        "flagged_employees": annual_flagged,
                        "observable_employees": annual_observable,
                        "employee_percent": float(numeric(annual["employee_percent"])),
                        "affected_teams": int(numeric(annual["affected_teams"])),
                    }
                )
            series_by_attribution[attribution] = points
        scopes.append({"key": scope_key, "monthly_series": series_by_attribution})

    expected_point_count = len(selected_dates) * len(SCOPES) * len(ATTRIBUTIONS)
    if int(annual_audit.get("monthly_series_numerator_over_denominator", -1)) != 0:
        raise ValueError("La auditoría anual contiene numeradores mayores que denominadores.")
    if int(annual_audit.get("monthly_series_denominator_below_30", -1)) != 0:
        raise ValueError("La auditoría anual contiene un denominador bajo n=30.")
    if int(annual_audit.get("membership_duplicate_rows", -1)) != 0:
        raise ValueError("La auditoría anual encontró employee-snapshots duplicados.")
    if denominator_mismatch_count != 0 or annual_below_six_month_count != 0:
        raise ValueError("La comparación anual no reconcilia con la serie semestral anidada.")
    if expected_point_count != 144 or len(selected_dates) != 36 or len(excluded_dates) != 4:
        raise ValueError("La cobertura anual no coincide con los 36 cortes completos esperados.")

    result_rows = {
        "annual_query_rows": annual_query["rows"],
        "coverage_query_rows": coverage_rows,
        "selected_dates": selected_dates,
    }
    evidence = {
        "schema_version": 1,
        "artifact": "internal_analysis",
        "generated_on": date.today().isoformat(),
        "query_path": str(ANNUAL_SQL.relative_to(ROOT)).replace("\\", "/"),
        "coverage_query_path": str(COVERAGE_SQL.relative_to(ROOT)).replace("\\", "/"),
        "analysis_plan": "config/more_than_1_employee_leaves_annual_distribution_plan_v4_20260909.yaml",
        "primary_evidence": str(PRIMARY_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "cutoff_date": "2026-08-23",
        "primary_window_months": 6,
        "annual_window_months": 12,
        "annual_window_rule": "(snapshot - 12 months, snapshot]",
        "annual_completeness_rule": ">=12 distinct monthly snapshots and >=330 observed days within the annual window",
        "included_term_type": "Voluntary",
        "population": "Distinct active regular employees with an observable direct manager at each evaluation snapshot",
        "grain": "Scope × attribution × monthly employee snapshot",
        "attribution": {
            "manager_at_evaluation": "Last non-null manager observed through the evaluation snapshot.",
            "manager_at_exit": "Last non-null manager observed through the termination date.",
        },
        "scopes": scopes,
        "comparison_calendar": {
            "primary_evaluation_snapshot_count": len(primary_dates),
            "annual_complete_snapshot_count": len(selected_dates),
            "annual_excluded_primary_snapshot_count": len(excluded_dates),
            "annual_first_snapshot": selected_dates[0],
            "annual_last_snapshot": selected_dates[-1],
            "excluded_primary_snapshot_dates": excluded_dates,
        },
        "audit_metrics": {
            **{key: int(value) if float(value).is_integer() else float(value) for key, value in annual_audit.items()},
            "published_annual_points": expected_point_count,
            "denominator_mismatch_vs_six_month": denominator_mismatch_count,
            "annual_below_six_month_count": annual_below_six_month_count,
        },
        "acceptance_rule": "36 annual dates aligned to the 40 primary six-month evaluation dates; each annual date has >=12 snapshots and >=330 observed days, every displayed denominator is >=30, annual flagged employees are >= nested six-month flagged employees, and no numerator exceeds its denominator.",
        "sql_sha256": sha256_file(ANNUAL_SQL),
        "coverage_sql_sha256": sha256_file(COVERAGE_SQL),
        "result_sha256": canonical_hash(result_rows),
        "outcome": "pass",
        "limitations": [
            "The annual panels are a descriptive sensitivity and do not replace the primary six-month feature.",
            "The first four six-month evaluation dates lack a complete annual history and are excluded from the annual panels.",
            "The measure is employee exposure to a team with two or more Voluntary exits; it is neither a manager ranking nor causal attribution.",
        ],
    }
    OUTPUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUTPUT)
    print(json.dumps(evidence["comparison_calendar"], ensure_ascii=False))
    print(json.dumps(evidence["audit_metrics"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
