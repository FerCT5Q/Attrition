"""Freeze aggregate evidence for the pure-Region / global-Labor-Market display."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "queries" / "audits" / "region_labor_market_global_display_20260909.sql"
OUTPUT_PATH = ROOT / "output" / "distribution" / "json" / "region-labor-market-global-evidence-20260909.json"
QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
SNAPSHOT = "2026-08-23"
MINIMUM_COHORT = 30
EXPECTED_REGIONS = {"India", "Americas", "APAC", "EMEA"}
EXPECTED_ZERO_METRICS = {
    "employees_with_multiple_source_rows",
    "employees_with_conflicting_region_values",
    "employees_with_conflicting_labor_market_values",
    "unclassified_region_employees",
    "global_missing_labor_market",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def distribution(rows: list[dict[str, Any]], result_type: str) -> list[dict[str, Any]]:
    values = [
        {
            "label": str(row["category"]),
            "employee_count": int(row["employee_count"]),
            "percentage": float(row["percentage"]),
            "sort_order": int(row["sort_order"]),
        }
        for row in rows
        if row["result_type"] == result_type
    ]
    return sorted(values, key=lambda item: item["sort_order"])


def main() -> None:
    command = [
        sys.executable, "-B", str(QUERY_HELPER), "--sql-file", str(SQL_PATH),
        "--max-rows", "100", "--reporting-mode", "internal_analysis",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Region global evidence query failed:\n{completed.stderr.strip()}")
    result = json.loads(completed.stdout)
    require(not result.get("truncated"), "Region global evidence query was truncated.")
    rows = list(result.get("rows", []))

    population = [row for row in rows if row["result_type"] == "population"]
    require(len(population) == 1, "Expected one population row.")
    eligible = int(population[0]["employee_count"])
    require(eligible >= MINIMUM_COHORT, "Eligible population is below n >= 30.")
    region_rows = distribution(rows, "global_region")
    labor_market_rows = distribution(rows, "global_labor_market")
    require({row["label"] for row in region_rows} == EXPECTED_REGIONS, "Stored Region domain differs from the approved display.")
    require(sum(row["employee_count"] for row in region_rows) == eligible, "Region does not reconcile to the population.")
    require(all(row["employee_count"] >= MINIMUM_COHORT for row in region_rows), "A Region bucket is below n >= 30.")
    require(sum(row["employee_count"] for row in labor_market_rows) == eligible, "Labor Market does not reconcile to the population.")
    require(all(row["employee_count"] >= MINIMUM_COHORT for row in labor_market_rows), "A Labor Market bucket is below n >= 30.")
    metadata = {str(row["category"]): int(row["employee_count"]) for row in rows if row["result_type"] == "metadata"}
    source_categories = metadata.get("observed_source_categories", 0)
    require(source_categories >= 1, "Labor Market has no source categories.")
    expected_labor_rows = min(source_categories, 20) + (1 if source_categories > 20 else 0)
    require(len(labor_market_rows) == expected_labor_rows, "Labor Market does not preserve top 20 + Other.")
    if source_categories > 20:
        require(labor_market_rows[-1]["label"] == "Other Labor Markets", "Missing Other Labor Markets tail.")
    metrics = {str(row["category"]): int(row["employee_count"]) for row in rows if row["result_type"] == "validation"}
    require(set(metrics) == EXPECTED_ZERO_METRICS, "Unexpected Region validation metrics.")
    require(all(metrics[name] == 0 for name in EXPECTED_ZERO_METRICS), "Region mapping or coverage validation failed.")

    evidence = {
        "schema_version": 1,
        "artifact": "internal_analysis",
        "generated_on": date.today().isoformat(),
        "analysis_plan": "config/region_labor_market_global_display_plan_v4_20260909.yaml",
        "query_path": str(SQL_PATH.relative_to(ROOT)).replace("\\", "/"),
        "snapshot": SNAPSHOT,
        "source_table": "hrda.post_hire_monthly_worker_dtls",
        "date_field": "fis_mo_end_dt",
        "population": "Active regular employees at the named monthly snapshot",
        "grain": "Distinct employee snapshot",
        "minimum_shared_cohort": MINIMUM_COHORT,
        "eligible_employees": eligible,
        "display": {
            "global_region": region_rows,
            "global_labor_market": labor_market_rows,
            "labor_market_source_category_count": source_categories,
        },
        "acceptance_rule": "Stored Region categories and global top-20-plus-Other Labor Market reconcile to the eligible population; every displayed bucket has n >= 30; source-row, mapping, classification, and missing-Labor-Market checks equal zero.",
        "audit_metrics": metrics,
        "sql_sha256": hashlib.sha256(SQL_PATH.read_bytes()).hexdigest(),
        "result_sha256": hashlib.sha256(json.dumps(rows, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "outcome": "pass",
    }
    OUTPUT_PATH.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
