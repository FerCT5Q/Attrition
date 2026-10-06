"""Build aggregate 2026 YTD attrition labels for manager site/time-zone bands."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from build_v7_manager_timezone_annual_attrition_evidence import ROOT, mapping_case, zone_maps


QUERY = ROOT / "queries" / "audits" / "v7_manager_timezone_2026_ytd_attrition_20260918.sql"
KEY_PREFLIGHT_QUERY = ROOT / "queries" / "audits" / "v7_manager_timezone_2026_ytd_mapping-key-preflight_20260918.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.manager-timezone-2026-ytd-attrition-evidence-20260918.json"
CATEGORIES = (
    "same_office_site",
    "different_site_up_to_4_hours",
    "different_site_more_than_4_hours",
)
MIN_EXPOSURE = 30
MIN_EXITS = 30


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run_aggregate_query(query_path: Path, max_rows: int) -> dict[str, Any]:
    """Run a saved aggregate-only SQL artifact through the guarded helper."""
    try:
        completed = subprocess.run(
            [sys.executable, "-B", str(HELPER), "--sql-file", str(query_path), "--max-rows", str(max_rows), "--reporting-mode", "internal_analysis"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"La consulta agregada {query_path.name} fallo. stdout={exc.stdout!r}; stderr={exc.stderr!r}"
        ) from exc
    payload: dict[str, Any] = json.loads(completed.stdout)
    require(payload.get("truncated") is False, f"La consulta {query_path.name} fue truncada.")
    return payload


def build_mapping_key_preflight_query() -> str:
    """Return only aggregate, hashed keys needed to shrink the IANA map SQL."""
    return """/*
  Aggregate-only preflight for stage 42's 2026 YTD time-zone categories.
  It exposes no office label, worker identifier, manager identifier, or row.
  The normalized MD5 keys are used only in this local builder to select the
  matching IANA mappings from the approved public office catalog.
*/
WITH baseline AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS baseline_snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
      AND CAST(fis_mo_end_dt AS DATE) < DATE '2026-01-01'
)
SELECT
    b.baseline_snapshot_date,
    MD5(NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '')) AS office_site_key,
    CASE
      WHEN NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
       AND NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
      THEN MD5(
          REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', '')
          || '|' ||
          REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', '')
      )
    END AS city_country_key,
    COUNT(DISTINCT w.employee_id) AS employee_count
FROM hrda.post_hire_monthly_worker_dtls AS w
CROSS JOIN baseline AS b
WHERE CAST(w.fis_mo_end_dt AS DATE) = b.baseline_snapshot_date
  AND w.worker_type = 'Employee'
  AND w.employee_type = 'Regular'
  AND w.active_status = 1
  AND w.employee_id IS NOT NULL
GROUP BY 1, 2, 3
ORDER BY employee_count DESC;
"""


def utc_offset_minutes(timezone_name: str, baseline_snapshot_date: date) -> int:
    """Evaluate the catalog's IANA zone at 12:00 UTC on the baseline date."""
    instant = datetime.combine(baseline_snapshot_date, time(12), tzinfo=timezone.utc)
    offset = instant.astimezone(ZoneInfo(timezone_name)).utcoffset()
    require(offset is not None, f"Could not evaluate the UTC offset for {timezone_name!r}.")
    return int(offset.total_seconds() // 60)


def numeric_mapping_case(lookup_sql: str, mapping: dict[str, int]) -> str:
    if not mapping:
        return "CAST(NULL AS INTEGER)"
    clauses = [f"WHEN '{key}' THEN {minutes}" for key, minutes in sorted(mapping.items())]
    return "CASE " + lookup_sql + "\n              " + "\n              ".join(clauses) + "\n              END"


def build_query(site_map: dict[str, int], city_map: dict[str, int]) -> str:
    def map_or_null(lookup_sql: str, mapping: dict[str, int]) -> str:
        return numeric_mapping_case(lookup_sql, mapping)

    employee_zone = "COALESCE(" + map_or_null("pair.employee_office_site_key", site_map) + ", " + map_or_null("pair.employee_city_country_key", city_map) + ")"
    manager_zone = "COALESCE(" + map_or_null("pair.manager_office_site_key", site_map) + ", " + map_or_null("pair.manager_city_country_key", city_map) + ")"
    return f"""/*
  V7 navigation slide 39 / technical stage 42: 2026 YTD voluntary attrition
  by employee-manager assigned-office/time-zone proximity.

  Population is assigned at the last active monthly snapshot before calendar
  2026. Voluntary exits are calendar dates from 2026-01-01 through the latest
  available HRDA snapshot. This is explicitly YTD, not an annualized rate.
  The catalog map embeds only normalized MD5 office/city-country keys and
  integer UTC offsets calculated locally from IANA zones at the baseline date;
  the query returns aggregate counts and rates only.
*/
WITH source_bounds AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
baseline AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS baseline_snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
      AND CAST(fis_mo_end_dt AS DATE) < DATE '2026-01-01'
),
source_rows AS (
    SELECT
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(w.manager_employee_id AS BIGINT)) AS manager_employee_id,
        MAX(MD5(NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), '[^A-Z0-9]+', ''), ''))) AS office_site_key,
        MAX(CASE WHEN NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
                       AND NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
                 THEN MD5(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', '') || '|' || REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', '')) END) AS city_country_key,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(w.manager_employee_id AS VARCHAR(64)), '<NULL>')) AS manager_id_variants,
        COUNT(DISTINCT COALESCE(NULLIF(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), ''), '<NULL>')) AS office_site_variants,
        COUNT(DISTINCT COALESCE(NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') || '|' || NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), ''), '<NULL>')) AS city_country_variants
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN baseline AS b
    WHERE CAST(w.fis_mo_end_dt AS DATE) = b.baseline_snapshot_date
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.employee_id IS NOT NULL
    GROUP BY 1
),
pair_source AS (
    SELECT
        employee.employee_id,
        employee.office_site_key AS employee_office_site_key,
        employee.city_country_key AS employee_city_country_key,
        manager.office_site_key AS manager_office_site_key,
        manager.city_country_key AS manager_city_country_key
    FROM source_rows AS employee
    INNER JOIN source_rows AS manager
      ON manager.employee_id = employee.manager_employee_id
    WHERE employee.source_row_count = 1
      AND employee.manager_id_variants = 1
      AND employee.office_site_variants <= 1
      AND employee.city_country_variants <= 1
      AND manager.source_row_count = 1
      AND manager.office_site_variants <= 1
      AND manager.city_country_variants <= 1
),
pair_zones AS (
    SELECT
        pair.employee_id,
        pair.employee_office_site_key,
        pair.manager_office_site_key,
        {employee_zone} AS employee_utc_offset_minutes,
        {manager_zone} AS manager_utc_offset_minutes
    FROM pair_source AS pair
),
pair_categories AS (
    SELECT
        pair.employee_id,
        CASE
          WHEN pair.employee_office_site_key IS NOT NULL AND pair.employee_office_site_key = pair.manager_office_site_key THEN 'same_office_site'
          WHEN pair.employee_utc_offset_minutes IS NULL OR pair.manager_utc_offset_minutes IS NULL THEN 'unmapped_time_zone_proxy'
          WHEN ABS(pair.employee_utc_offset_minutes - pair.manager_utc_offset_minutes) <= 240 THEN 'different_site_up_to_4_hours'
          ELSE 'different_site_more_than_4_hours'
        END AS category
    FROM pair_zones AS pair
),
voluntary_events AS (
    SELECT CAST(employee_id AS BIGINT) AS employee_id, CAST(term_date AS DATE) AS term_date
    FROM hrda.post_hire_monthly_worker_dtls
    CROSS JOIN source_bounds AS bounds
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND CAST(term_date AS DATE) >= DATE '2026-01-01'
      AND CAST(term_date AS DATE) <= bounds.latest_snapshot_date
    GROUP BY 1, 2
),
target_flags AS (
    SELECT
        pair.employee_id,
        pair.category,
        MAX(CASE WHEN event.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS ytd_voluntary_attrition_target
    FROM pair_categories AS pair
    LEFT JOIN voluntary_events AS event
      ON event.employee_id = pair.employee_id
    GROUP BY 1, 2
),
category_metrics AS (
    SELECT
        category,
        COUNT(DISTINCT employee_id) AS employee_count,
        SUM(ytd_voluntary_attrition_target) AS voluntary_exits,
        ROUND(100.0 * SUM(ytd_voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS ytd_voluntary_attrition_rate_percent
    FROM target_flags
    WHERE category IN ('same_office_site', 'different_site_up_to_4_hours', 'different_site_more_than_4_hours')
    GROUP BY 1
)
SELECT
    'category' AS row_type,
    'time_zone_proximity' AS metric,
    category,
    b.baseline_snapshot_date,
    bounds.latest_snapshot_date AS outcome_end_date,
    employee_count,
    voluntary_exits,
    ytd_voluntary_attrition_rate_percent,
    CAST(NULL AS BIGINT) AS diagnostic_value
FROM category_metrics
CROSS JOIN baseline AS b
CROSS JOIN source_bounds AS bounds
UNION ALL
SELECT
    'diagnostic', metric, CAST(NULL AS VARCHAR(64)), b.baseline_snapshot_date, bounds.latest_snapshot_date,
    CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), diagnostic_value
FROM (
    SELECT 'eligible_employee_manager_pair_count' AS metric, COUNT(*)::BIGINT AS diagnostic_value FROM target_flags
    UNION ALL SELECT 'categorized_employee_manager_pair_count', COUNT(*)::BIGINT FROM target_flags WHERE category IN ('same_office_site', 'different_site_up_to_4_hours', 'different_site_more_than_4_hours')
    UNION ALL SELECT 'unmapped_employee_manager_pair_count', COUNT(*)::BIGINT FROM target_flags WHERE category = 'unmapped_time_zone_proxy'
    UNION ALL SELECT 'duplicate_employee_source_count', SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END)::BIGINT FROM source_rows
    UNION ALL SELECT 'location_conflict_count', SUM(CASE WHEN office_site_variants > 1 OR city_country_variants > 1 THEN 1 ELSE 0 END)::BIGINT FROM source_rows
) AS diagnostics
CROSS JOIN baseline AS b
CROSS JOIN source_bounds AS bounds
ORDER BY row_type, category, metric;
"""


def main() -> None:
    site_map, city_map, catalog_diagnostics = zone_maps()
    preflight_sql = build_mapping_key_preflight_query()
    KEY_PREFLIGHT_QUERY.write_text(preflight_sql, encoding="utf-8")
    preflight_payload = run_aggregate_query(KEY_PREFLIGHT_QUERY, max_rows=1000)
    preflight_rows = preflight_payload.get("rows")
    require(isinstance(preflight_rows, list) and preflight_rows, "The manager time-zone mapping preflight returned no aggregate keys.")
    baseline_dates = {str(row["baseline_snapshot_date"]) for row in preflight_rows}
    require(len(baseline_dates) == 1, "The manager time-zone mapping preflight has inconsistent baseline dates.")
    baseline_snapshot_date = date.fromisoformat(next(iter(baseline_dates)))
    observed_site_keys = {str(row["office_site_key"]) for row in preflight_rows if row.get("office_site_key")}
    observed_city_keys = {str(row["city_country_key"]) for row in preflight_rows if row.get("city_country_key")}
    observed_site_map = {
        key: utc_offset_minutes(zone, baseline_snapshot_date)
        for key, zone in site_map.items()
        if key in observed_site_keys
    }
    observed_city_map = {
        key: utc_offset_minutes(zone, baseline_snapshot_date)
        for key, zone in city_map.items()
        if key in observed_city_keys
    }
    require(observed_site_map or observed_city_map, "The manager time-zone mapping preflight found no catalog-mapped assigned locations.")
    catalog_diagnostics = {
        **catalog_diagnostics,
        "preflight_query": str(KEY_PREFLIGHT_QUERY.relative_to(ROOT)).replace("\\", "/"),
        "preflight_query_sha256": hashlib.sha256(KEY_PREFLIGHT_QUERY.read_bytes()).hexdigest(),
        "preflight_aggregate_key_rows": len(preflight_rows),
        "offset_evaluation_baseline_snapshot": baseline_snapshot_date.isoformat(),
        "offset_evaluation_method": "Python zoneinfo using IANA geographic data at 12:00 UTC on the baseline date; the SQL receives only integer UTC offsets.",
        "observed_site_key_count": len(observed_site_keys),
        "observed_city_country_key_count": len(observed_city_keys),
        "mapped_observed_site_key_count": len(observed_site_map),
        "mapped_observed_city_country_key_count": len(observed_city_map),
    }
    sql = build_query(observed_site_map, observed_city_map)
    QUERY.write_text(sql, encoding="utf-8")
    payload = run_aggregate_query(QUERY, max_rows=30)
    rows = payload.get("rows")
    require(isinstance(rows, list) and rows, "The 2026 YTD manager time-zone query returned no rows.")
    category_rows = [row for row in rows if row.get("row_type") == "category"]
    diagnostics = {str(row["metric"]): int(row["diagnostic_value"]) for row in rows if row.get("row_type") == "diagnostic"}
    require({str(row["category"]) for row in category_rows} == set(CATEGORIES), "The 2026 YTD categories are incomplete.")
    require(diagnostics.get("duplicate_employee_source_count") == 0, "2026 YTD baseline has duplicate employee snapshots.")
    require(diagnostics.get("location_conflict_count") == 0, "2026 YTD baseline has conflicting assigned locations.")
    require(
        diagnostics["categorized_employee_manager_pair_count"] + diagnostics["unmapped_employee_manager_pair_count"]
        == diagnostics["eligible_employee_manager_pair_count"],
        "2026 YTD mapping coverage does not reconcile.",
    )
    for row in category_rows:
        employees, exits, rate = int(row["employee_count"]), int(row["voluntary_exits"]), float(row["ytd_voluntary_attrition_rate_percent"])
        require(employees > 0 and 0 <= exits <= employees and abs(rate - 100 * exits / employees) < 0.00011, "A 2026 YTD rate does not reconcile.")
        row["publication_status"] = "publishable" if employees >= MIN_EXPOSURE and exits >= MIN_EXITS else "not_estimable_below_aggregate_threshold"
    baseline_dates = {str(row["baseline_snapshot_date"]) for row in category_rows}
    outcome_dates = {str(row["outcome_end_date"]) for row in category_rows}
    require(len(baseline_dates) == len(outcome_dates) == 1, "The 2026 YTD window is inconsistent.")
    evidence = {
        "artifact_type": "aggregate_segment_attrition_evidence",
        "version": 7,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "purpose": "Etiquetas compactas de attrition voluntaria 2026 YTD para las tres categorias de sitio asignado y huso horario del manager.",
        "outcome_contract": {
            "population": "active regular employee-manager pairs with a unique stored office_site at the last monthly snapshot before 2026",
            "grain": "employee_baseline_snapshot",
            "baseline_snapshot": next(iter(baseline_dates)),
            "target": "term_type='VOLUNTARY' con term_date desde 2026-01-01 hasta el ultimo snapshot disponible",
            "outcome_end_date": next(iter(outcome_dates)),
            "label": "2026 YTD voluntary attrition; not annualized",
            "time_zone_rule": "same stored office_site first; otherwise IANA UTC-offset difference at 12:00 UTC on baseline date is <=4 hours or >4 hours",
        },
        "query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": hashlib.sha256(QUERY.read_bytes()).hexdigest(),
        "catalog_mapping": catalog_diagnostics,
        "diagnostics": diagnostics,
        "rows": category_rows,
        "outcome": "pass",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    print("baseline=" + next(iter(baseline_dates)) + "; outcome_end=" + next(iter(outcome_dates)) + "; outcome=pass")


if __name__ == "__main__":
    main()
