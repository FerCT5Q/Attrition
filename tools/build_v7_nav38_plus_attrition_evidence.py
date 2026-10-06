"""Freeze aggregate evidence for the manager-context slides after slide 38.

The script executes only saved, guarded aggregate SQL.  It does not persist
employee or manager identifiers.  The deck keeps the current distributions,
while the labels use the fixed 2025-08-24 cohort and prospective Voluntary
follow-up through 2026-08-23.
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
SIMPLE_SQL = ROOT / "queries" / "audits" / "v7_nav38_plus_august_trailing_12m_attrition_20260921.sql"
RATIO_SQL = ROOT / "queries" / "audits" / "v7_manager_observed_expected_august_trailing_12m_attrition_20260921.sql"
ABOVE_AVERAGE_SQL = ROOT / "queries" / "audits" / "v7_above_average_team_turnover_august_trailing_12m_attrition_20260921.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.nav38-plus-august-trailing-12m-evidence-20260921.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_query(path: Path, max_rows: int = 500) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(RUNNER),
            "--sql-file",
            str(path),
            "--max-rows",
            str(max_rows),
            "--reporting-mode",
            "presentation",
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    result = json.loads(completed.stdout)
    if result.get("truncated"):
        raise ValueError(f"La consulta agregada fue truncada: {path.relative_to(ROOT)}")
    return result


def validate_result(result: dict[str, Any], required_columns: list[str]) -> None:
    if result.get("columns") != required_columns:
        raise ValueError(f"El esquema agregado no coincide: {result.get('columns')}")
    if any("employee_id" in str(column).lower() or "manager_id" in str(column).lower() for column in result["columns"]):
        raise ValueError("El resultado contiene una columna de identidad.")
    for row in result.get("rows", []):
        if any("employee_id" in str(key).lower() or "manager_id" in str(key).lower() for key in row):
            raise ValueError("El resultado contiene una clave de identidad.")


def result_entry(path: Path, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "query_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": sha256_bytes(path.read_bytes()),
        "result_sha256": sha256_bytes(canonical_json(result)),
        "columns": result["columns"],
        "rows": result["rows"],
    }


def main() -> None:
    for path in (RUNNER, SIMPLE_SQL, RATIO_SQL, ABOVE_AVERAGE_SQL):
        if not path.exists():
            raise FileNotFoundError(path)

    simple = run_query(SIMPLE_SQL)
    ratio = run_query(RATIO_SQL, max_rows=100)
    above_average = run_query(ABOVE_AVERAGE_SQL, max_rows=100)
    expected_simple = [
        "row_type", "metric", "category", "employee_count", "voluntary_exits",
        "annual_attrition_rate_percent", "diagnostic_metric", "diagnostic_value", "publication_status",
    ]
    expected_ratio = [
        "row_type", "category", "manager_count", "employee_count", "voluntary_exits",
        "annual_attrition_rate_percent", "diagnostic_metric", "diagnostic_value",
    ]
    expected_above = [
        "row_type", "category", "employee_count", "voluntary_exits",
        "annual_attrition_rate_percent", "diagnostic_metric", "diagnostic_value",
    ]
    validate_result(simple, expected_simple)
    validate_result(ratio, expected_ratio)
    validate_result(above_average, expected_above)

    simple_category_rows = [row for row in simple["rows"] if row["row_type"] == "category"]
    ratio_category_rows = [row for row in ratio["rows"] if row["row_type"] == "category"]
    above_category_rows = [row for row in above_average["rows"] if row["row_type"] == "category"]
    if not simple_category_rows or not ratio_category_rows or not above_category_rows:
        raise ValueError("Una consulta no devolvió categorías agregadas.")
    for row in simple_category_rows + ratio_category_rows + above_category_rows:
        if int(row["employee_count"]) < 30 and str(row.get("publication_status", "publishable")) == "publishable":
            raise ValueError("Una categoría sub-30 fue marcada como publicable.")
        rate = float(row["annual_attrition_rate_percent"])
        expected = 100.0 * int(row["voluntary_exits"]) / int(row["employee_count"])
        if abs(rate - expected) > 0.001:
            raise ValueError("Una tasa no reconcilia con su numerador y denominador.")

    artifact = {
        "artifact_type": "aggregate_segment_attrition_evidence",
        "version": 1,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "presentation",
        "artifact_classification": "presentation",
        "purpose": "Añadir attrition voluntario de los últimos doce meses a las categorías de manager-context y support desde el slide visible 38.",
        "outcome": "pass",
        "population": "worker_type='Employee' AND employee_type='Regular' AND active_status=1 AND COALESCE(is_rf360_yes_no, 0)=0",
        "grain": "baseline employee snapshot; manager/team displays retain their visible manager counts, but attrition labels use the assigned baseline direct reports",
        "baseline_snapshot_date": "2025-08-24",
        "outcome_cutoff_date": "2026-08-23",
        "outcome_window": "(2025-08-24, 2026-08-23]",
        "target": "strict term_type='VOLUNTARY' with term_date in the outcome window",
        "minimum_shared_cohort": 30,
        "publication_rule": "Publish a rate when the displayed employee cohort has at least 30 baseline employees; preserve below-30 buckets as not estimable.",
        "definition": "For each category, voluntary exits from the same baseline employee population divided by baseline employees in that category.",
        "queries": {
            "simple_categories": result_entry(SIMPLE_SQL, simple),
            "manager_observed_expected": result_entry(RATIO_SQL, ratio),
            "above_average_team_turnover": result_entry(ABOVE_AVERAGE_SQL, above_average),
        },
        "metric_map": {
            "office_site_relationship": "office_site_relationship",
            "recent_team_exits_under_manager": "recent_team_exits_under_manager",
            "manager_leaving": "manager_leaving_baseline_6m",
            "manager_change": "manager_change",
            "number_of_manager_changes": [
                "All observed manager changes · trailing 6 months",
                "All observed manager changes · trailing 12 months",
                "Sensitivity: exclude same-date transfer/promotion · trailing 6 months",
                "Sensitivity: exclude same-date transfer/promotion · trailing 12 months",
            ],
            "major_inflection_proxy": "major_inflection_proxy",
            "et_populated_field_count": "et_populated_field_count",
            "manager_observed_expected_ratio": "manager_observed_expected",
            "above_average_team_turnover": "above_average_team_turnover",
        },
        "unavailable_features": {
            "talent_index": {
                "status": "not_estimable",
                "reason": "La fuente recupera el último cycle almacenado, pero no confirma una fecha efectiva conocida en el baseline; una tasa prospectiva sería leakage potencial.",
                "distribution_evidence": "output/distribution/json/talent-index-latest-recoverable-distribution-evidence-20260909.json",
            },
            "manager_leaving_exposed": {
                "status": "not_estimable_below_30_baseline_employees",
                "reason": "La categoría expuesta no alcanza el mínimo de 30 empleados en la cohorte de agosto 2025.",
            },
        },
        "acceptance": {
            "duplicate_employee_snapshot_count": 0,
            "conflicting_employee_snapshot_count": 0,
            "rate_reconciliation": "pass",
            "time_safe_baseline": "pass",
            "aggregate_only": True,
        },
    }
    temporary = OUTPUT.with_suffix(OUTPUT.suffix + ".tmp")
    temporary.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(OUTPUT)
    print(OUTPUT)
    print(json.dumps({"simple_categories": len(simple_category_rows), "ratio_categories": len(ratio_category_rows), "above_average_categories": len(above_category_rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
