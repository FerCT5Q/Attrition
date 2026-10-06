"""Freeze aggregate evidence for the alternative Region country-split display."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "queries" / "audits" / "region_major_country_split_display_20260909.sql"
OUTPUT_PATH = ROOT / "output" / "distribution" / "json" / "region-major-country-split-evidence-20260909.json"
QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
SNAPSHOT = "2026-08-23"
MINIMUM_COHORT = 30
EXPECTED_LABELS = {
    "India",
    "United States",
    "Americas excluding U.S.",
    "China",
    "APAC excluding China",
    "EMEA",
}
EXPECTED_ZERO_METRICS = {
    "employees_with_multiple_source_rows",
    "employees_with_conflicting_region_values",
    "employees_with_conflicting_country_values",
    "unclassified_region_employees",
    "united_states_outside_americas",
    "china_outside_apac",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    command = [
        sys.executable,
        "-B",
        str(QUERY_HELPER),
        "--sql-file",
        str(SQL_PATH),
        "--max-rows",
        "100",
        "--reporting-mode",
        "internal_analysis",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Region major-country display query failed:\n{completed.stderr.strip()}")
    result = json.loads(completed.stdout)
    require(not result.get("truncated"), "Region major-country evidence query was truncated.")
    rows = list(result.get("rows", []))

    population = [row for row in rows if row["result_type"] == "population"]
    require(len(population) == 1, "Expected one population row.")
    eligible = int(population[0]["employee_count"])
    require(eligible >= MINIMUM_COHORT, "Eligible population is below n >= 30.")

    display = sorted(
        [
            {
                "label": str(row["category"]),
                "employee_count": int(row["employee_count"]),
                "percentage": float(row["percentage"]),
                "sort_order": int(row["sort_order"]),
            }
            for row in rows
            if row["result_type"] == "major_country_split"
        ],
        key=lambda row: row["sort_order"],
    )
    require({row["label"] for row in display} == EXPECTED_LABELS, "Major-country display domain differs from the approved plan.")
    require(sum(row["employee_count"] for row in display) == eligible, "Major-country display does not reconcile to the population.")
    require(all(row["employee_count"] >= MINIMUM_COHORT for row in display), "A major-country display bucket is below n >= 30.")
    for row in display:
        expected_percentage = 100.0 * row["employee_count"] / eligible
        require(abs(row["percentage"] - expected_percentage) <= 0.01, "A major-country percentage does not reconcile to its count.")

    metrics = {
        str(row["category"]): int(row["employee_count"])
        for row in rows
        if row["result_type"] == "validation"
    }
    require(set(metrics) == EXPECTED_ZERO_METRICS | {"missing_country_employees"}, "Unexpected major-country validation metrics.")
    require(all(metrics[name] == 0 for name in EXPECTED_ZERO_METRICS), "Major-country grouping validation failed.")

    evidence = {
        "schema_version": 1,
        "artifact": "internal_analysis",
        "generated_on": date.today().isoformat(),
        "analysis_plan": "config/region_major_country_split_display_plan_v4_20260909.yaml",
        "query_path": str(SQL_PATH.relative_to(ROOT)).replace("\\", "/"),
        "snapshot": SNAPSHOT,
        "source_table": "hrda.post_hire_monthly_worker_dtls",
        "date_field": "fis_mo_end_dt",
        "population": "Active regular employees at the named monthly snapshot",
        "grain": "Distinct employee snapshot",
        "minimum_shared_cohort": MINIMUM_COHORT,
        "eligible_employees": eligible,
        "display": {"major_country_split": display},
        "acceptance_rule": "The six display-only buckets reconcile to the eligible population, each has n >= 30, source-row and Region/Country consistency checks equal zero, and United States/China appear only in their expected stored Region.",
        "audit_metrics": metrics,
        "sql_sha256": hashlib.sha256(SQL_PATH.read_bytes()).hexdigest(),
        "result_sha256": hashlib.sha256(json.dumps(rows, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "outcome": "pass",
    }
    OUTPUT_PATH.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
