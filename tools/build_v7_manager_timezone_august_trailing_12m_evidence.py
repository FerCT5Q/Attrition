"""Freeze August-to-August aggregate evidence for V7 manager-site proximity.

The query uses employee IDs only inside Redshift joins.  It writes and returns
aggregate category counts, exits, and rates; office-site values and employee
identifiers never leave the query.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from build_v7_manager_timezone_annual_attrition_evidence import ROOT, mapping_case, zone_maps


QUERY = ROOT / "queries" / "audits" / "v7_manager_timezone_august_trailing_12m_attrition_20260921.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.manager-timezone-august-trailing-12m-evidence-20260921.json"
BASELINE = "2025-08-24"
CUTOFF = "2026-08-23"
CATEGORIES = (
    "same_office_site",
    "different_site_up_to_4_hours",
    "different_site_more_than_4_hours",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def build_query(site_map: dict[str, str], city_map: dict[str, str]) -> str:
    baseline_employee_zone = "COALESCE(" + mapping_case("employee.city_site_key", site_map) + ", " + mapping_case("employee.city_country_key", city_map) + ")"
    baseline_manager_zone = "COALESCE(" + mapping_case("manager.city_site_key", site_map) + ", " + mapping_case("manager.city_country_key", city_map) + ")"
    current_employee_zone = "COALESCE(" + mapping_case("employee.city_site_key", site_map) + ", " + mapping_case("employee.city_country_key", city_map) + ")"
    current_manager_zone = "COALESCE(" + mapping_case("manager.city_site_key", site_map) + ", " + mapping_case("manager.city_country_key", city_map) + ")"
    return f"""/*
  Claim: V7 manager office-site proximity uses an August fiscal-close cohort.
  Baseline is {BASELINE}; outcome is strict VOLUNTARY termination in
  ({BASELINE}, {CUTOFF}]. The current distribution is measured at {CUTOFF}.
  This internal-analysis query returns aggregate categories only.
*/
WITH
baseline_source_rows AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    MAX(CAST(w.manager_employee_id AS BIGINT)) AS manager_employee_id,
    MAX(MD5(NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), '[^A-Z0-9]+', ''), ''))) AS city_site_key,
    MAX(CASE WHEN NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
              AND NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
             THEN MD5(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', '') || '|' || REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', '')) END) AS city_country_key,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT COALESCE(CAST(w.manager_employee_id AS VARCHAR(64)), '<NULL>')) AS manager_id_variants,
    COUNT(DISTINCT COALESCE(NULLIF(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), ''), '<NULL>')) AS office_site_variants,
    COUNT(DISTINCT COALESCE(NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') || '|' || NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), ''), '<NULL>')) AS city_country_variants
  FROM hrda.post_hire_monthly_worker_dtls AS w
  WHERE CAST(w.fis_mo_end_dt AS DATE) = DATE '{BASELINE}'
    AND w.worker_type = 'Employee' AND w.employee_type = 'Regular' AND w.active_status = 1 AND w.employee_id IS NOT NULL
  GROUP BY 1
),
current_source_rows AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    MAX(CAST(w.manager_employee_id AS BIGINT)) AS manager_employee_id,
    MAX(MD5(NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), '[^A-Z0-9]+', ''), ''))) AS city_site_key,
    MAX(CASE WHEN NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
              AND NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
             THEN MD5(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', '') || '|' || REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', '')) END) AS city_country_key,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT COALESCE(CAST(w.manager_employee_id AS VARCHAR(64)), '<NULL>')) AS manager_id_variants,
    COUNT(DISTINCT COALESCE(NULLIF(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), ''), '<NULL>')) AS office_site_variants,
    COUNT(DISTINCT COALESCE(NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') || '|' || NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), ''), '<NULL>')) AS city_country_variants
  FROM hrda.post_hire_monthly_worker_dtls AS w
  WHERE CAST(w.fis_mo_end_dt AS DATE) = DATE '{CUTOFF}'
    AND w.worker_type = 'Employee' AND w.employee_type = 'Regular' AND w.active_status = 1 AND w.employee_id IS NOT NULL
  GROUP BY 1
),
baseline_pairs AS (
  SELECT employee.employee_id, employee.city_site_key AS employee_site_key, manager.city_site_key AS manager_site_key,
         {baseline_employee_zone} AS employee_timezone_name, {baseline_manager_zone} AS manager_timezone_name
  FROM baseline_source_rows AS employee
  INNER JOIN baseline_source_rows AS manager ON manager.employee_id = employee.manager_employee_id
  WHERE employee.source_row_count = 1 AND employee.manager_id_variants = 1 AND employee.office_site_variants <= 1 AND employee.city_country_variants <= 1
    AND manager.source_row_count = 1 AND manager.manager_id_variants = 1 AND manager.office_site_variants <= 1 AND manager.city_country_variants <= 1
),
current_pairs AS (
  SELECT employee.employee_id, employee.city_site_key AS employee_site_key, manager.city_site_key AS manager_site_key,
         {current_employee_zone} AS employee_timezone_name, {current_manager_zone} AS manager_timezone_name
  FROM current_source_rows AS employee
  INNER JOIN current_source_rows AS manager ON manager.employee_id = employee.manager_employee_id
  WHERE employee.source_row_count = 1 AND employee.manager_id_variants = 1 AND employee.office_site_variants <= 1 AND employee.city_country_variants <= 1
    AND manager.source_row_count = 1 AND manager.manager_id_variants = 1 AND manager.office_site_variants <= 1 AND manager.city_country_variants <= 1
),
baseline_categories AS (
  SELECT employee_id, CASE
    WHEN employee_site_key IS NOT NULL AND employee_site_key = manager_site_key THEN 'same_office_site'
    WHEN employee_timezone_name IS NULL OR manager_timezone_name IS NULL THEN 'unmapped_time_zone_proxy'
    WHEN ABS(DATEDIFF(minute, CONVERT_TIMEZONE('UTC', employee_timezone_name, DATEADD(hour, 12, DATE '{BASELINE}')), CONVERT_TIMEZONE('UTC', manager_timezone_name, DATEADD(hour, 12, DATE '{BASELINE}')))) <= 240 THEN 'different_site_up_to_4_hours'
    ELSE 'different_site_more_than_4_hours' END AS category
  FROM baseline_pairs
),
current_categories AS (
  SELECT employee_id, CASE
    WHEN employee_site_key IS NOT NULL AND employee_site_key = manager_site_key THEN 'same_office_site'
    WHEN employee_timezone_name IS NULL OR manager_timezone_name IS NULL THEN 'unmapped_time_zone_proxy'
    WHEN ABS(DATEDIFF(minute, CONVERT_TIMEZONE('UTC', employee_timezone_name, DATEADD(hour, 12, DATE '{CUTOFF}')), CONVERT_TIMEZONE('UTC', manager_timezone_name, DATEADD(hour, 12, DATE '{CUTOFF}')))) <= 240 THEN 'different_site_up_to_4_hours'
    ELSE 'different_site_more_than_4_hours' END AS category
  FROM current_pairs
),
voluntary_events AS (
  SELECT CAST(employee_id AS BIGINT) AS employee_id, CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee' AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
    AND CAST(term_date AS DATE) > DATE '{BASELINE}' AND CAST(term_date AS DATE) <= DATE '{CUTOFF}'
  GROUP BY 1, 2
),
annual_metrics AS (
  SELECT baseline.category, COUNT(*) AS baseline_employee_count,
         SUM(CASE WHEN voluntary_events.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_exit_count,
         ROUND(100.0 * SUM(CASE WHEN voluntary_events.employee_id IS NOT NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS annual_voluntary_attrition_rate_percent
  FROM baseline_categories AS baseline
  LEFT JOIN voluntary_events ON voluntary_events.employee_id = baseline.employee_id
  WHERE baseline.category IN ('same_office_site', 'different_site_up_to_4_hours', 'different_site_more_than_4_hours')
  GROUP BY 1
),
current_distribution AS (
  SELECT category, COUNT(*) AS current_employee_count
  FROM current_categories GROUP BY 1
)
SELECT 'annual_attrition' AS row_type, category, baseline_employee_count AS employee_count, voluntary_exit_count,
       annual_voluntary_attrition_rate_percent AS attrition_rate_percent, CAST(NULL AS BIGINT) AS diagnostic_value
FROM annual_metrics
UNION ALL
SELECT 'current_distribution', category, current_employee_count, CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), CAST(NULL AS BIGINT)
FROM current_distribution
UNION ALL
SELECT 'diagnostic', 'baseline_duplicate_employee_source_count', CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), SUM(CASE WHEN source_row_count <> 1 THEN 1 ELSE 0 END)::BIGINT FROM baseline_source_rows
UNION ALL
SELECT 'diagnostic', 'current_duplicate_employee_source_count', CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), SUM(CASE WHEN source_row_count <> 1 THEN 1 ELSE 0 END)::BIGINT FROM current_source_rows
UNION ALL
SELECT 'diagnostic', 'baseline_pair_count', CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), COUNT(*)::BIGINT FROM baseline_categories
UNION ALL
SELECT 'diagnostic', 'current_pair_count', CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), COUNT(*)::BIGINT FROM current_categories
ORDER BY row_type, category;
"""


def main() -> None:
    site_map, city_map, catalog_diagnostics = zone_maps()
    QUERY.write_text(build_query(site_map, city_map), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-B", str(HELPER), "--sql-file", str(QUERY), "--max-rows", "20", "--reporting-mode", "internal_analysis"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    payload: dict[str, Any] = json.loads(completed.stdout)
    require(payload.get("truncated") is False, "The aggregate proximity query was truncated.")
    rows = payload.get("rows")
    require(isinstance(rows, list), "The aggregate proximity query returned no rows.")
    annual = {str(row["category"]): row for row in rows if row["row_type"] == "annual_attrition"}
    current = {str(row["category"]): row for row in rows if row["row_type"] == "current_distribution"}
    diagnostics = {str(row["category"]): int(row["diagnostic_value"]) for row in rows if row["row_type"] == "diagnostic"}
    require(set(annual) == set(CATEGORIES), "Annual proximity categories are incomplete.")
    require(set(current) == set(CATEGORIES) | {"unmapped_time_zone_proxy"}, "Current proximity distribution is incomplete.")
    require(diagnostics["baseline_duplicate_employee_source_count"] == 0 and diagnostics["current_duplicate_employee_source_count"] == 0, "A proximity snapshot has duplicate employee rows.")
    for row in annual.values():
        cohort, exits, rate = int(row["employee_count"]), int(row["voluntary_exit_count"]), float(row["attrition_rate_percent"])
        require(cohort >= 30 and 0 <= exits <= cohort and abs(rate - 100 * exits / cohort) < 0.00011, "An annual proximity rate does not reconcile.")
        row["publication_status"] = "publishable"
    evidence = {
        "artifact_type": "aggregate_segment_attrition_evidence",
        "version": 7,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "purpose": "Distribucion al cierre fiscal de agosto y attrition voluntaria trailing 12m para proximidad de sitio asignado con manager.",
        "outcome_contract": {
            "baseline_snapshot": BASELINE,
            "outcome_cutoff_date": CUTOFF,
            "target": "term_type='VOLUNTARY' con term_date en (baseline_snapshot, outcome_cutoff_date]",
            "label": "Annual voluntary attrition (12 months); not annualized",
            "time_zone_rule": "same stored office_site first; otherwise IANA UTC-offset difference of <=4 hours or >4 hours at each snapshot date",
        },
        "catalog_mapping": catalog_diagnostics,
        "query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": hashlib.sha256(QUERY.read_bytes()).hexdigest(),
        "annual_attrition": annual,
        "latest_distribution": current,
        "diagnostics": diagnostics,
        "acceptance_rule": "Each displayed baseline category has n>=30, no duplicate employee snapshot rows, and its rate reconciles exactly to voluntary exits / baseline cohort.",
        "outcome": "pass",
    }
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
