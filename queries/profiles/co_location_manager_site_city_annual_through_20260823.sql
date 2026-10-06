-- Annual presentation profile for the two manager-location proxies.
-- Scope is fixed to the existing deck cutoff (2026-08-23), so the new
-- office_site + city trend is directly comparable with the retained
-- office_site trend. Aggregate-only; no identities or location labels return.
--
-- Definitions:
--   site proxy: employee and active regular manager have the same normalized
--     nonblank office_site at the same employee snapshot.
--   stricter proxy: both also have the same normalized nonblank city.
-- A proxy is not a measure of physical presence or distance.

WITH source_rows AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(fiscal_year AS VARCHAR(32)) AS fiscal_year,
    CAST(employee_id AS BIGINT) AS employee_id,
    CAST(manager_employee_id AS BIGINT) AS manager_employee_id,
    NULLIF(UPPER(TRIM(office_site)), '') AS office_site_normalized,
    NULLIF(UPPER(TRIM(city)), '') AS city_normalized
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) <= DATE '2026-08-23'
),
employee_snapshot AS (
  SELECT
    snapshot_date,
    fiscal_year,
    employee_id,
    COUNT(DISTINCT manager_employee_id) AS manager_id_count,
    MAX(manager_employee_id) AS manager_employee_id,
    COUNT(DISTINCT office_site_normalized) AS employee_site_value_count,
    MAX(office_site_normalized) AS employee_site_normalized,
    COUNT(DISTINCT city_normalized) AS employee_city_value_count,
    MAX(city_normalized) AS employee_city_normalized
  FROM source_rows
  GROUP BY snapshot_date, fiscal_year, employee_id
),
manager_snapshot AS (
  SELECT
    snapshot_date,
    employee_id,
    COUNT(DISTINCT office_site_normalized) AS manager_site_value_count,
    MAX(office_site_normalized) AS manager_site_normalized,
    COUNT(DISTINCT city_normalized) AS manager_city_value_count,
    MAX(city_normalized) AS manager_city_normalized
  FROM source_rows
  GROUP BY snapshot_date, employee_id
),
pairs AS (
  SELECT
    e.snapshot_date,
    e.fiscal_year,
    CASE
      WHEN e.manager_id_count = 1
       AND e.employee_site_value_count <= 1
       AND e.employee_site_normalized IS NOT NULL
       AND m.employee_id IS NOT NULL
       AND m.manager_site_value_count = 1
       AND m.manager_site_normalized IS NOT NULL
      THEN 1 ELSE 0
    END AS site_comparable,
    CASE
      WHEN e.manager_id_count = 1
       AND e.employee_site_value_count <= 1
       AND e.employee_site_normalized IS NOT NULL
       AND m.employee_id IS NOT NULL
       AND m.manager_site_value_count = 1
       AND m.manager_site_normalized IS NOT NULL
       AND e.employee_site_normalized = m.manager_site_normalized
      THEN 1 ELSE 0
    END AS same_office_site,
    CASE
      WHEN e.manager_id_count = 1
       AND e.employee_site_value_count <= 1
       AND e.employee_site_normalized IS NOT NULL
       AND m.employee_id IS NOT NULL
       AND m.manager_site_value_count = 1
       AND m.manager_site_normalized IS NOT NULL
       AND e.employee_city_value_count <= 1
       AND e.employee_city_normalized IS NOT NULL
       AND m.manager_city_value_count = 1
       AND m.manager_city_normalized IS NOT NULL
      THEN 1 ELSE 0
    END AS site_city_comparable,
    CASE
      WHEN e.manager_id_count = 1
       AND e.employee_site_value_count <= 1
       AND e.employee_site_normalized IS NOT NULL
       AND m.employee_id IS NOT NULL
       AND m.manager_site_value_count = 1
       AND m.manager_site_normalized IS NOT NULL
       AND e.employee_city_value_count <= 1
       AND e.employee_city_normalized IS NOT NULL
       AND m.manager_city_value_count = 1
       AND m.manager_city_normalized IS NOT NULL
       AND e.employee_site_normalized = m.manager_site_normalized
       AND e.employee_city_normalized = m.manager_city_normalized
      THEN 1 ELSE 0
    END AS same_office_site_and_city,
    CASE
      WHEN e.manager_id_count = 1
       AND e.employee_site_value_count <= 1
       AND e.employee_site_normalized IS NOT NULL
       AND m.employee_id IS NOT NULL
       AND m.manager_site_value_count = 1
       AND m.manager_site_normalized IS NOT NULL
       AND e.employee_city_value_count <= 1
       AND e.employee_city_normalized IS NOT NULL
       AND m.manager_city_value_count = 1
       AND m.manager_city_normalized IS NOT NULL
       AND e.employee_site_normalized = m.manager_site_normalized
       AND e.employee_city_normalized <> m.manager_city_normalized
      THEN 1 ELSE 0
    END AS same_office_site_different_city
  FROM employee_snapshot e
  LEFT JOIN manager_snapshot m
    ON e.snapshot_date = m.snapshot_date
   AND e.manager_employee_id = m.employee_id
),
annual AS (
  SELECT
    fiscal_year,
    COUNT(DISTINCT snapshot_date) AS snapshot_count,
    COUNT(*) AS eligible_employee_snapshots,
    SUM(site_comparable) AS site_comparable_employee_snapshots,
    SUM(same_office_site) AS same_office_site_employee_snapshots,
    SUM(site_city_comparable) AS site_city_comparable_employee_snapshots,
    SUM(same_office_site_and_city) AS same_office_site_and_city_employee_snapshots,
    SUM(CASE WHEN site_city_comparable = 1 AND same_office_site = 1 THEN 1 ELSE 0 END)
      AS same_office_site_with_city_observed_employee_snapshots,
    SUM(same_office_site_different_city) AS same_office_site_different_city_employee_snapshots
  FROM pairs
  GROUP BY fiscal_year
)
SELECT
  fiscal_year,
  snapshot_count,
  eligible_employee_snapshots,
  site_comparable_employee_snapshots,
  same_office_site_employee_snapshots,
  ROUND(100.0 * same_office_site_employee_snapshots
    / NULLIF(site_comparable_employee_snapshots, 0), 4)
    AS same_office_site_percent_of_site_comparable,
  site_city_comparable_employee_snapshots,
  same_office_site_and_city_employee_snapshots,
  ROUND(100.0 * same_office_site_and_city_employee_snapshots
    / NULLIF(site_city_comparable_employee_snapshots, 0), 4)
    AS same_office_site_and_city_percent_of_site_city_comparable,
  same_office_site_with_city_observed_employee_snapshots,
  same_office_site_different_city_employee_snapshots,
  ROUND(100.0 * same_office_site_different_city_employee_snapshots
    / NULLIF(same_office_site_with_city_observed_employee_snapshots, 0), 4)
    AS same_office_site_different_city_percent_when_site_and_city_observed
FROM annual
ORDER BY fiscal_year;
