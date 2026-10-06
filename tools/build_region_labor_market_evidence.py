"""Freeze validated aggregate evidence for the Region presentation slide."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "queries" / "audits" / "region_us_labor_market_display_snapshot_20260908.sql"
OUTPUT_PATH = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v2.region-labor-market-evidence-20260908.json"
QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
SNAPSHOT = "2026-08-23"
MINIMUM_COHORT = 30

EXPECTED_GLOBAL_GROUPS = {
    "India",
    "United States",
    "APAC",
    "EMEA",
    "Americas excluding U.S.",
}
EXPECTED_US_MARKETS = {
    "USA - Market 1",
    "USA - Market 2",
    "USA - Market 3",
}
EXPECTED_ZERO_METRICS = {
    "employees_with_multiple_source_rows",
    "employees_with_conflicting_region_values",
    "employees_with_conflicting_country_values",
    "employees_with_conflicting_labor_market_values",
    "unclassified_region_employees",
    "united_states_outside_americas",
    "india_outside_india_region",
    "united_states_missing_labor_market",
    "india_missing_labor_market",
    "global_missing_labor_market",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run_query() -> dict[str, Any]:
    command = [
        sys.executable,
        "-B",
        str(QUERY_HELPER),
        "--sql-file",
        str(SQL_PATH),
        "--max-rows",
        "100",
        "--reporting-mode",
        "presentation",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Region evidence query failed:\n{completed.stderr.strip()}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Region evidence query did not return JSON.") from exc
    require(not result.get("truncated"), "Region evidence query was truncated.")
    return result


def distributions(rows: list[dict[str, Any]], result_type: str) -> list[dict[str, Any]]:
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
    result = run_query()
    rows = list(result.get("rows", []))

    population_rows = [row for row in rows if row["result_type"] == "population"]
    require(len(population_rows) == 1, "Expected exactly one eligible-population result.")
    eligible_employees = int(population_rows[0]["employee_count"])
    require(eligible_employees >= MINIMUM_COHORT, "Eligible population is below the publication cohort threshold.")

    global_distribution = distributions(rows, "global_region")
    global_labor_market = distributions(rows, "global_labor_market")
    us_labor_market = distributions(rows, "us_labor_market")
    india_labor_market = distributions(rows, "india_labor_market")

    require(
        {item["label"] for item in global_distribution} == EXPECTED_GLOBAL_GROUPS,
        "Global Region display groups differ from the approved five-group display.",
    )
    require(
        sum(item["employee_count"] for item in global_distribution) == eligible_employees,
        "Global Region display groups do not reconcile to the eligible population.",
    )
    require(
        all(item["employee_count"] >= MINIMUM_COHORT for item in global_distribution),
        "A global Region display group is below n >= 30.",
    )

    global_counts = {item["label"]: item["employee_count"] for item in global_distribution}

    metadata = {
        str(row["category"]): int(row["employee_count"])
        for row in rows
        if row["result_type"] == "metadata"
    }
    require(
        set(metadata) == {"observed_source_categories"},
        "Region audit did not return the global Labor Market cardinality.",
    )
    labor_market_source_category_count = metadata["observed_source_categories"]
    require(labor_market_source_category_count >= 1, "Labor Market has no observed source categories.")
    expected_labor_market_display_count = min(labor_market_source_category_count, 20)
    if labor_market_source_category_count > 20:
        expected_labor_market_display_count += 1
        require(
            global_labor_market[-1]["label"] == "Other Labor Markets",
            "The Labor Market tail must be published as Other Labor Markets.",
        )
    require(
        len(global_labor_market) == expected_labor_market_display_count,
        "Labor Market display does not preserve the approved top-20-plus-Other policy.",
    )
    require(
        sum(item["employee_count"] for item in global_labor_market) == eligible_employees,
        "Labor Market display does not reconcile to the eligible population.",
    )
    require(
        all(item["employee_count"] >= MINIMUM_COHORT for item in global_labor_market),
        "A published Labor Market group is below n >= 30.",
    )

    require(
        {item["label"] for item in us_labor_market} == EXPECTED_US_MARKETS,
        "The U.S. Labor Market domain is not the approved three-market display.",
    )
    require(
        sum(item["employee_count"] for item in us_labor_market) == global_counts["United States"],
        "U.S. Labor Market groups do not reconcile to the United States total.",
    )
    require(
        all(item["employee_count"] >= MINIMUM_COHORT for item in us_labor_market),
        "A U.S. Labor Market group is below n >= 30.",
    )

    require(
        len(india_labor_market) == 1 and india_labor_market[0]["label"] == "IND",
        "India no longer has the single observed Labor Market value IND.",
    )
    require(
        india_labor_market[0]["employee_count"] == global_counts["India"],
        "India Labor Market does not reconcile to the India Region group.",
    )

    metrics = {
        str(row["category"]): int(row["employee_count"])
        for row in rows
        if row["result_type"] == "validation"
    }
    require(set(metrics) == EXPECTED_ZERO_METRICS, "Region audit did not return the expected validation metrics.")
    require(
        all(metrics[name] == 0 for name in EXPECTED_ZERO_METRICS),
        "Region display mapping or Labor Market coverage validation failed.",
    )

    sql_bytes = SQL_PATH.read_bytes()
    query_result_hash = hashlib.sha256(
        json.dumps(rows, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    evidence = {
        "schema_version": 1,
        "reporting_mode": "internal_analysis",
        "generated_on": date.today().isoformat(),
        "query_path": str(SQL_PATH.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": hashlib.sha256(sql_bytes).hexdigest(),
        "query_result_sha256": query_result_hash,
        "snapshot": SNAPSHOT,
        "source_table": "hrda.post_hire_monthly_worker_dtls",
        "date_field": "fis_mo_end_dt",
        "population": "Active regular employees at the named monthly snapshot",
        "eligible_employees": eligible_employees,
        "grain": "Distinct employee snapshot",
        "minimum_shared_cohort": MINIMUM_COHORT,
        "claim": (
            "The Region slide keeps region as its broad geographic field, separates the United States "
            "from AMERICAS for display, and shows the stored Labor Market distribution for all active regular employees. "
            "The three U.S. market values are validation context, not the scope of the Labor Market visual."
        ),
        "display": {
            "global_region": global_distribution,
            "global_labor_market": global_labor_market,
            "labor_market_source_category_count": labor_market_source_category_count,
        },
        "validation_context": {
            "united_states_labor_market": us_labor_market,
            "india_labor_market": india_labor_market,
        },
        "validation": {
            "acceptance_rule": (
                "The five global Region groups and the global top-20-plus-Other Labor Market display each reconcile "
                "to the active regular employee population; visible groups have n >= 30; the U.S. three-market and "
                "India IND observations reconcile as validation context; and snapshot-grain, mapping, and completeness "
                "violations equal zero."
            ),
            "metrics": metrics,
            "outcome": "pass",
        },
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
