"""Build aggregate evidence for the employee-manager office-site time-zone proxy.

The script never persists raw HRDA office labels or employee identifiers.  It
maps only normalized MD5 keys to an already-approved public Qualcomm office
catalog, resolves the catalog coordinates to IANA zones locally, and sends a
read-only aggregate query to Redshift.  The generated SQL retains only hashes
and zone names, so it is auditable without exposing workforce records.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from timezonefinder import TimezoneFinder


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "output" / "distribution" / "json" / "qualcomm-office-locations-catalog-20260908.json"
QUERY = ROOT / "queries" / "audits" / "v7_manager_timezone_annual_attrition_20260918.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.manager-timezone-annual-attrition-evidence-20260918.json"

MIN_EXPOSURE = 30
MIN_EXITS = 30
DISPLAY_CATEGORIES = (
    "same_office_site",
    "different_site_up_to_4_hours",
    "different_site_more_than_4_hours",
)
COUNTRY_ALIASES = {
    "USA": ("USA", "UNITED STATES OF AMERICA", "UNITED STATES"),
    "PEOPLES REPUBLIC OF CHINA": ("PEOPLES REPUBLIC OF CHINA", "CHINA"),
    "SOUTH KOREA": ("SOUTH KOREA", "KOREA REPUBLIC OF", "REPUBLIC OF KOREA"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^A-Z0-9]+", "", text.upper())


def md5_normalized(value: object) -> str:
    return hashlib.md5(normalize(value).encode("utf-8")).hexdigest()


def md5_city_country(country: object, city: object) -> str:
    return hashlib.md5(f"{normalize(country)}|{normalize(city)}".encode("utf-8")).hexdigest()


def corrected_coordinates(office: dict[str, Any]) -> tuple[float, float] | None:
    """Return valid catalog coordinates; do not invent a replacement for bad data."""
    office_code = str(office.get("officeCode", "")).upper()
    latitude = float(office["latitude"])
    longitude = float(office["longitude"])
    if office_code == "TIJNA.Z":
        # The same official catalog contains the valid Tijuana coordinate in a
        # duplicate record. This is the documented correction used by commute.
        return (32.4373533, -117.0439505)
    # DAL.B has a catalog longitude copied from its latitude. Its resulting
    # coordinate points to Pakistan instead of Addison, TX, so leave it
    # intentionally unmapped rather than assigning an inferred zone.
    if office_code == "DAL.B":
        return None
    if -90 <= latitude <= 90 and -180 <= longitude <= 180:
        return (latitude, longitude)
    if -90 <= longitude <= 90 and -180 <= latitude <= 180:
        return (longitude, latitude)
    return None


def zone_maps() -> tuple[dict[str, str], dict[str, str], dict[str, int]]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    finder = TimezoneFinder(in_memory=True)
    site_candidates: dict[str, set[str]] = defaultdict(set)
    city_candidates: dict[str, set[str]] = defaultdict(set)
    invalid_coordinate_count = 0
    unresolved_timezone_count = 0

    for office in catalog:
        coordinates = corrected_coordinates(office)
        if coordinates is None:
            invalid_coordinate_count += 1
            continue
        latitude, longitude = coordinates
        timezone_name = finder.timezone_at(lng=longitude, lat=latitude)
        if timezone_name is None or not re.fullmatch(r"[A-Za-z0-9_+\-/]+", timezone_name):
            unresolved_timezone_count += 1
            continue
        for alias in (office.get("officeCode"), office.get("name")):
            if normalize(alias):
                site_candidates[md5_normalized(alias)].add(timezone_name)
        country_norm = normalize(office.get("country"))
        country_variants = COUNTRY_ALIASES.get(country_norm, (country_norm,))
        for country in country_variants:
            city_candidates[md5_city_country(country, office.get("locality"))].add(timezone_name)

    site_map = {key: next(iter(zones)) for key, zones in site_candidates.items() if len(zones) == 1}
    city_map = {key: next(iter(zones)) for key, zones in city_candidates.items() if len(zones) == 1}
    diagnostics = {
        "catalog_office_count": len(catalog),
        "site_key_count": len(site_map),
        "city_country_key_count": len(city_map),
        "ambiguous_site_key_count": sum(len(zones) > 1 for zones in site_candidates.values()),
        "ambiguous_city_country_key_count": sum(len(zones) > 1 for zones in city_candidates.values()),
        "invalid_coordinate_count": invalid_coordinate_count,
        "unresolved_timezone_count": unresolved_timezone_count,
    }
    require(site_map and city_map, "The office catalog did not produce usable time-zone maps.")
    return site_map, city_map, diagnostics


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def mapping_case(lookup_sql: str, mapping: dict[str, str]) -> str:
    """Render a local MD5-key map without a large Redshift UNION CTE."""
    clauses = [
        f"WHEN {sql_literal(key)} THEN {sql_literal(timezone_name)}"
        for key, timezone_name in sorted(mapping.items())
    ]
    return "CASE " + lookup_sql + "\n              " + "\n              ".join(clauses) + "\n              END"


def build_query(site_map: dict[str, str], city_map: dict[str, str]) -> str:
    historical_employee_zone = "COALESCE(" + mapping_case("employee.office_site_key", site_map) + ", " + mapping_case("employee.city_country_key", city_map) + ")"
    historical_manager_zone = "COALESCE(" + mapping_case("manager.office_site_key", site_map) + ", " + mapping_case("manager.city_country_key", city_map) + ")"
    latest_employee_zone = "COALESCE(" + mapping_case("employee.office_site_key", site_map) + ", " + mapping_case("employee.city_country_key", city_map) + ")"
    latest_manager_zone = "COALESCE(" + mapping_case("manager.office_site_key", site_map) + ", " + mapping_case("manager.city_country_key", city_map) + ")"
    return f"""/*
  V7 navigation slide 39 / technical stage 42: annual voluntary attrition for
  employee-manager assigned-office proximity by time-zone offset.

  Claim: an employee is classified from their stored office_site at each
  historical snapshot as (1) the same office site as their manager, (2) a
  different site with an IANA UTC-offset difference of <= 4 hours at 12:00 UTC
  on that snapshot date, or (3) a different site with a difference > 4 hours.
  The first category takes precedence. A pair whose sites cannot be reconciled
  to the public office catalog is kept as an aggregate unmapped diagnostic and
  never placed in one of the three display categories.

  The employee-manager join is same-snapshot. The outcome is strict voluntary
  termination in (snapshot_date, snapshot_date + 12 months]. The embedded
  office map contains only normalized MD5 keys and IANA zones; this SQL
  returns only aggregate counts and rates.
*/
WITH
source_bounds AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
all_snapshot_dates AS (
    SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date, MAX(fiscal_year) AS fiscal_year
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
      AND fiscal_year BETWEEN 2020 AND 2026
    GROUP BY 1
),
complete_snapshot_dates AS (
    SELECT dates.snapshot_date, dates.fiscal_year
    FROM all_snapshot_dates AS dates
    CROSS JOIN source_bounds AS bounds
    WHERE dates.snapshot_date <= DATEADD(month, -12, bounds.latest_snapshot_date)
),
fiscal_snapshot_coverage AS (
    SELECT
        dates.fiscal_year,
        COUNT(*) AS total_source_snapshots,
        SUM(CASE WHEN complete.snapshot_date IS NOT NULL THEN 1 ELSE 0 END) AS complete_followup_snapshots
    FROM all_snapshot_dates AS dates
    LEFT JOIN complete_snapshot_dates AS complete
      ON complete.snapshot_date = dates.snapshot_date
    GROUP BY 1
),
historical_source_rows AS (
    SELECT
        complete.snapshot_date,
        complete.fiscal_year,
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(w.manager_employee_id AS BIGINT)) AS manager_employee_id,
        MAX(MD5(NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), '[^A-Z0-9]+', ''), ''))) AS office_site_key,
        MAX(
            CASE
              WHEN NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
               AND NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
              THEN MD5(
                  REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', '')
                  || '|' ||
                  REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', '')
              )
            END
        ) AS city_country_key,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(w.manager_employee_id AS VARCHAR(64)), '<NULL>')) AS manager_id_variants,
        COUNT(DISTINCT COALESCE(NULLIF(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), ''), '<NULL>')) AS office_site_variants,
        COUNT(DISTINCT COALESCE(
            NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '')
            || '|' || NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), ''),
            '<NULL>'
        )) AS city_country_variants
    FROM hrda.post_hire_monthly_worker_dtls AS w
    INNER JOIN complete_snapshot_dates AS complete
      ON CAST(w.fis_mo_end_dt AS DATE) = complete.snapshot_date
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.employee_id IS NOT NULL
    GROUP BY 1, 2, 3
),
historical_source_quality AS (
    SELECT
        COUNT(*) AS active_employee_snapshot_count,
        COUNT(DISTINCT snapshot_date) AS snapshot_count,
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
        SUM(CASE WHEN manager_id_variants <> 1 THEN 1 ELSE 0 END) AS manager_conflict_or_missing_count,
        SUM(CASE WHEN office_site_variants > 1 OR city_country_variants > 1 THEN 1 ELSE 0 END) AS location_conflict_count
    FROM historical_source_rows
),
historical_pairs AS (
    SELECT
        employee.snapshot_date,
        employee.fiscal_year,
        employee.employee_id,
        employee.office_site_key AS employee_office_site_key,
        manager.office_site_key AS manager_office_site_key,
        {historical_employee_zone} AS employee_timezone_name,
        {historical_manager_zone} AS manager_timezone_name,
        CASE
          WHEN employee.office_site_key IS NOT NULL
           AND employee.office_site_key = manager.office_site_key
          THEN 1 ELSE 0
        END AS same_office_site
    FROM historical_source_rows AS employee
    INNER JOIN historical_source_rows AS manager
      ON manager.snapshot_date = employee.snapshot_date
     AND manager.employee_id = employee.manager_employee_id
    WHERE employee.source_row_count = 1
      AND employee.manager_id_variants = 1
      AND employee.office_site_variants <= 1
      AND employee.city_country_variants <= 1
      AND manager.source_row_count = 1
      AND manager.office_site_variants <= 1
      AND manager.city_country_variants <= 1
),
historical_categories AS (
    SELECT
        pair.snapshot_date,
        pair.fiscal_year,
        pair.employee_id,
        CASE
          WHEN pair.same_office_site = 1 THEN 'same_office_site'
          WHEN pair.employee_timezone_name IS NULL OR pair.manager_timezone_name IS NULL THEN 'unmapped_time_zone_proxy'
          WHEN ABS(DATEDIFF(
              minute,
              CONVERT_TIMEZONE('UTC', pair.employee_timezone_name, DATEADD(hour, 12, pair.snapshot_date)),
              CONVERT_TIMEZONE('UTC', pair.manager_timezone_name, DATEADD(hour, 12, pair.snapshot_date))
          )) <= 240 THEN 'different_site_up_to_4_hours'
          ELSE 'different_site_more_than_4_hours'
        END AS category
    FROM historical_pairs AS pair
),
voluntary_events AS (
    SELECT CAST(employee_id AS BIGINT) AS employee_id, CAST(term_date AS DATE) AS term_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND term_date IS NOT NULL
    GROUP BY 1, 2
),
historical_target_flags AS (
    SELECT
        category.snapshot_date,
        category.fiscal_year,
        category.employee_id,
        category.category,
        MAX(CASE WHEN event.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS annual_voluntary_attrition_target
    FROM historical_categories AS category
    LEFT JOIN voluntary_events AS event
      ON event.employee_id = category.employee_id
     AND event.term_date > category.snapshot_date
     AND event.term_date <= DATEADD(month, 12, category.snapshot_date)
    GROUP BY 1, 2, 3, 4
),
annual_category_metrics AS (
    SELECT
        fiscal_year,
        category,
        COUNT(DISTINCT employee_id) AS distinct_employee_count,
        COUNT(*) AS employee_snapshot_count,
        SUM(annual_voluntary_attrition_target) AS voluntary_exits,
        ROUND(100.0 * SUM(annual_voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS annual_attrition_rate_percent
    FROM historical_target_flags
    WHERE category IN ('same_office_site', 'different_site_up_to_4_hours', 'different_site_more_than_4_hours')
    GROUP BY 1, 2
),
annual_mapping_coverage AS (
    SELECT
        fiscal_year,
        CASE
          WHEN category IN ('same_office_site', 'different_site_up_to_4_hours', 'different_site_more_than_4_hours') THEN 'categorized_pairs'
          ELSE 'unmapped_pairs'
        END AS category,
        COUNT(DISTINCT employee_id) AS distinct_employee_count,
        COUNT(*) AS employee_snapshot_count
    FROM historical_target_flags
    GROUP BY 1, 2
),
latest_source_rows AS (
    SELECT
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(w.manager_employee_id AS BIGINT)) AS manager_employee_id,
        MAX(MD5(NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), '[^A-Z0-9]+', ''), ''))) AS office_site_key,
        MAX(
            CASE
              WHEN NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
               AND NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
              THEN MD5(
                  REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', '')
                  || '|' ||
                  REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', '')
              )
            END
        ) AS city_country_key,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(w.manager_employee_id AS VARCHAR(64)), '<NULL>')) AS manager_id_variants,
        COUNT(DISTINCT COALESCE(NULLIF(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), ''), '<NULL>')) AS office_site_variants,
        COUNT(DISTINCT COALESCE(
            NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '')
            || '|' || NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), ''),
            '<NULL>'
        )) AS city_country_variants
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN source_bounds AS bounds
    WHERE CAST(w.fis_mo_end_dt AS DATE) = bounds.latest_snapshot_date
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.employee_id IS NOT NULL
    GROUP BY 1
),
latest_pairs AS (
    SELECT
        employee.employee_id,
        employee.office_site_key AS employee_office_site_key,
        manager.office_site_key AS manager_office_site_key,
        {latest_employee_zone} AS employee_timezone_name,
        {latest_manager_zone} AS manager_timezone_name,
        CASE
          WHEN employee.office_site_key IS NOT NULL
           AND employee.office_site_key = manager.office_site_key
          THEN 1 ELSE 0
        END AS same_office_site
    FROM latest_source_rows AS employee
    INNER JOIN latest_source_rows AS manager
      ON manager.employee_id = employee.manager_employee_id
    WHERE employee.source_row_count = 1
      AND employee.manager_id_variants = 1
      AND employee.office_site_variants <= 1
      AND employee.city_country_variants <= 1
      AND manager.source_row_count = 1
      AND manager.office_site_variants <= 1
      AND manager.city_country_variants <= 1
),
latest_categories AS (
    SELECT
        pair.employee_id,
        CASE
          WHEN pair.same_office_site = 1 THEN 'same_office_site'
          WHEN pair.employee_timezone_name IS NULL OR pair.manager_timezone_name IS NULL THEN 'unmapped_time_zone_proxy'
          WHEN ABS(DATEDIFF(
              minute,
              CONVERT_TIMEZONE('UTC', pair.employee_timezone_name, DATEADD(hour, 12, bounds.latest_snapshot_date)),
              CONVERT_TIMEZONE('UTC', pair.manager_timezone_name, DATEADD(hour, 12, bounds.latest_snapshot_date))
          )) <= 240 THEN 'different_site_up_to_4_hours'
          ELSE 'different_site_more_than_4_hours'
        END AS category
    FROM latest_pairs AS pair
    CROSS JOIN source_bounds AS bounds
),
latest_distribution AS (
    SELECT
        category,
        COUNT(DISTINCT employee_id) AS distinct_employee_count,
        COUNT(*) AS employee_snapshot_count
    FROM latest_categories
    GROUP BY 1
)
SELECT
    'annual_attrition' AS row_type,
    'time_zone_proximity' AS metric,
    category,
    CAST(metrics.fiscal_year AS VARCHAR(32)) AS fiscal_year,
    distinct_employee_count,
    employee_snapshot_count,
    voluntary_exits,
    annual_attrition_rate_percent,
    coverage.total_source_snapshots,
    coverage.complete_followup_snapshots,
    CAST(NULL AS BIGINT) AS diagnostic_value
FROM annual_category_metrics AS metrics
INNER JOIN fiscal_snapshot_coverage AS coverage
  ON coverage.fiscal_year = metrics.fiscal_year
UNION ALL
SELECT
    'annual_mapping_coverage',
    'time_zone_proximity',
    category,
    CAST(metrics.fiscal_year AS VARCHAR(32)),
    distinct_employee_count,
    employee_snapshot_count,
    CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)),
    coverage.total_source_snapshots,
    coverage.complete_followup_snapshots,
    CAST(NULL AS BIGINT)
FROM annual_mapping_coverage AS metrics
INNER JOIN fiscal_snapshot_coverage AS coverage
  ON coverage.fiscal_year = metrics.fiscal_year
UNION ALL
SELECT
    'latest_distribution',
    'time_zone_proximity',
    category,
    CAST(NULL AS VARCHAR(32)),
    distinct_employee_count,
    employee_snapshot_count,
    CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)),
    CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT)
FROM latest_distribution
UNION ALL
SELECT
    'fiscal_coverage',
    'fiscal_year',
    CAST(fiscal_year AS VARCHAR(32)),
    CAST(fiscal_year AS VARCHAR(32)),
    CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)),
    total_source_snapshots, complete_followup_snapshots, CAST(NULL AS BIGINT)
FROM fiscal_snapshot_coverage
UNION ALL
SELECT
    'diagnostic',
    metric,
    CAST(NULL AS VARCHAR(32)), CAST(NULL AS VARCHAR(32)),
    CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)),
    CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), diagnostic_value
FROM (
    SELECT 'historical_snapshot_count' AS metric, snapshot_count::BIGINT AS diagnostic_value FROM historical_source_quality
    UNION ALL SELECT 'historical_active_employee_snapshot_count', active_employee_snapshot_count::BIGINT FROM historical_source_quality
    UNION ALL SELECT 'historical_duplicate_employee_snapshot_count', duplicate_employee_snapshot_count::BIGINT FROM historical_source_quality
    UNION ALL SELECT 'historical_manager_conflict_or_missing_count', manager_conflict_or_missing_count::BIGINT FROM historical_source_quality
    UNION ALL SELECT 'historical_location_conflict_count', location_conflict_count::BIGINT FROM historical_source_quality
    UNION ALL SELECT 'latest_eligible_employee_manager_pair_count', COUNT(*)::BIGINT FROM latest_categories
    UNION ALL SELECT 'latest_categorized_employee_manager_pair_count', COUNT(*)::BIGINT FROM latest_categories WHERE category IN ('same_office_site', 'different_site_up_to_4_hours', 'different_site_more_than_4_hours')
    UNION ALL SELECT 'latest_unmapped_employee_manager_pair_count', COUNT(*)::BIGINT FROM latest_categories WHERE category = 'unmapped_time_zone_proxy'
) AS diagnostics
ORDER BY row_type, fiscal_year, category, metric;
"""


def main() -> None:
    require(CATALOG.exists(), f"Missing office catalog: {CATALOG}")
    site_map, city_map, map_diagnostics = zone_maps()
    sql = build_query(site_map, city_map)
    QUERY.write_text(sql, encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "--sql-file",
            str(QUERY),
            "--max-rows",
            "250",
            "--reporting-mode",
            "internal_analysis",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    payload: dict[str, Any] = json.loads(completed.stdout)
    require(payload.get("truncated") is False, "The time-zone proximity query was truncated.")
    rows = payload.get("rows")
    require(isinstance(rows, list) and rows, "The time-zone proximity query returned no rows.")

    annual_rows = [row for row in rows if row.get("row_type") == "annual_attrition"]
    latest_rows = [row for row in rows if row.get("row_type") == "latest_distribution"]
    coverage_rows = [row for row in rows if row.get("row_type") == "fiscal_coverage"]
    annual_mapping_rows = [row for row in rows if row.get("row_type") == "annual_mapping_coverage"]
    diagnostics = {str(row["metric"]): int(row["diagnostic_value"]) for row in rows if row.get("row_type") == "diagnostic"}
    require(diagnostics.get("historical_duplicate_employee_snapshot_count") == 0, "Historical employee snapshots are duplicated.")
    require(diagnostics.get("historical_manager_conflict_or_missing_count") == 0, "Historical manager assignments are missing or conflicting.")
    require(diagnostics.get("historical_location_conflict_count") == 0, "Historical stored location values conflict within an employee snapshot.")
    require(
        diagnostics.get("latest_categorized_employee_manager_pair_count", 0)
        + diagnostics.get("latest_unmapped_employee_manager_pair_count", 0)
        == diagnostics.get("latest_eligible_employee_manager_pair_count", -1),
        "Latest mapping coverage does not reconcile to eligible employee-manager pairs.",
    )

    latest_categories = {str(row["category"]) for row in latest_rows}
    require(set(DISPLAY_CATEGORIES).issubset(latest_categories), "Latest distribution is missing a requested display category.")
    annual_by_year: dict[str, set[str]] = defaultdict(set)
    for row in annual_rows:
        year = str(row["fiscal_year"])
        annual_by_year[year].add(str(row["category"]))
        exposures = int(row["employee_snapshot_count"])
        exits = int(row["voluntary_exits"])
        rate = float(row["annual_attrition_rate_percent"])
        require(exposures > 0 and 0 <= exits <= exposures and 0 <= rate <= 100, "An annual time-zone rate does not reconcile.")
        row["publication_status"] = "publishable" if exposures >= MIN_EXPOSURE and exits >= MIN_EXITS else "not_estimable_below_aggregate_threshold"
    for year in map(str, range(2020, 2025)):
        require(annual_by_year.get(year) == set(DISPLAY_CATEGORIES), f"FY{year} is missing a requested time-zone category.")

    coverage = {str(row["category"]): row for row in coverage_rows}
    for year in map(str, range(2020, 2027)):
        require(year in coverage, f"Missing fiscal coverage for FY{year}.")
    for row in annual_rows:
        coverage_row = coverage[str(row["fiscal_year"])]
        row["total_source_snapshots"] = int(coverage_row["total_source_snapshots"])
        row["complete_followup_snapshots"] = int(coverage_row["complete_followup_snapshots"])
        row["complete_followup_fiscal_year"] = (
            row["total_source_snapshots"] == row["complete_followup_snapshots"]
        )

    latest_map = {str(row["category"]): row for row in latest_rows}
    evidence = {
        "artifact_type": "aggregate_segment_attrition_evidence",
        "version": 7,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "purpose": "Reemplazar la distancia residencial al manager por una distribucion de proximidad de sitio asignado y huso horario, con attrition anual voluntaria historica.",
        "outcome_contract": {
            "population": "active regular employee-manager pairs with a unique stored office_site at the employee snapshot",
            "grain": "employee_snapshot",
            "target": "term_type='VOLUNTARY' con term_date en (snapshot_date, snapshot_date + 12 months]",
            "time_zone_rule": "same stored office_site first; otherwise IANA UTC-offset difference at 12:00 UTC on snapshot date is <=4 hours or >4 hours",
            "minimum_employee_snapshot_exposure": MIN_EXPOSURE,
            "minimum_voluntary_exits": MIN_EXITS,
        },
        "definition": "Es un proxy de sitio de oficina asignado: no mide domicilio, presencia fisica, distancia de traslado ni colaboracion real.",
        "catalog": {
            "path": str(CATALOG.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
            "timezone_reference": "timezonefinder 9.0.0 / bundled IANA geographic boundary data",
            **map_diagnostics,
        },
        "query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": hashlib.sha256(QUERY.read_bytes()).hexdigest(),
        "diagnostics": diagnostics,
        "latest_distribution": latest_map,
        "annual_mapping_coverage": annual_mapping_rows,
        "fiscal_coverage": coverage,
        "rows": annual_rows,
        "publication_rule": "FY con seguimiento incompleto no publica una tasa anual; pares no mapeados se declaran como cobertura y no se asignan a una categoria de huso horario.",
        "outcome": "pass",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    print(
        "latest_eligible_pairs=" + str(diagnostics["latest_eligible_employee_manager_pair_count"])
        + "; latest_categorized_pairs=" + str(diagnostics["latest_categorized_employee_manager_pair_count"])
        + "; latest_unmapped_pairs=" + str(diagnostics["latest_unmapped_employee_manager_pair_count"])
        + "; outcome=pass"
    )


if __name__ == "__main__":
    main()
