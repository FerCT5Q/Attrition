-- Co-location proxy: office_site versus office_site + city.
-- Deliverable mode: presentation. This returns fiscal-year aggregate counts
-- only; no employee, manager, office-site, or city values are returned.
--
-- Claim tested: a same-office_site employee-manager proxy may be too broad if
-- an office_site code is used across cities. The stricter comparison requires
-- equality of both normalized office_site and normalized city in the same
-- employee snapshot.
--
-- Acceptance rule (stated before execution):
--   1) both comparisons use an active regular employee-manager relationship at
--      the same monthly snapshot, with an unambiguous manager and source values;
--   2) each rate has its own explicit denominator (site-comparable or
--      site-and-city-comparable employee snapshots);
--   3) the count of office-site codes occurring in more than one city and the
--      resulting same-site/different-city pairs are reported; and
--   4) no physical-presence conclusion is drawn from either stored-field proxy.

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
),
employee_snapshot AS (
  SELECT
    snapshot_date,
    fiscal_year,
    employee_id,
    COUNT(*) AS employee_source_rows,
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
    COUNT(*) AS manager_source_rows,
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
    e.employee_id,
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
),
latest_snapshot AS (
  SELECT MAX(snapshot_date) AS snapshot_date
  FROM source_rows
),
latest_site_city_mapping AS (
  SELECT
    office_site_normalized,
    COUNT(DISTINCT city_normalized) AS city_count_for_office_site,
    COUNT(DISTINCT employee_id) AS employee_count
  FROM source_rows
  WHERE snapshot_date = (SELECT snapshot_date FROM latest_snapshot)
    AND office_site_normalized IS NOT NULL
    AND city_normalized IS NOT NULL
  GROUP BY office_site_normalized
),
mapping_summary AS (
  SELECT
    COUNT(*) AS office_site_codes_with_a_nonblank_city,
    SUM(CASE WHEN city_count_for_office_site > 1 THEN 1 ELSE 0 END)
      AS office_site_codes_used_in_multiple_cities,
    SUM(CASE WHEN city_count_for_office_site > 1 THEN employee_count ELSE 0 END)
      AS employees_assigned_to_office_site_codes_used_in_multiple_cities
  FROM latest_site_city_mapping
)
SELECT
  a.fiscal_year,
  a.snapshot_count,
  a.eligible_employee_snapshots,
  a.site_comparable_employee_snapshots,
  a.same_office_site_employee_snapshots,
  ROUND(100.0 * a.same_office_site_employee_snapshots
    / NULLIF(a.site_comparable_employee_snapshots, 0), 4)
    AS same_office_site_percent_of_site_comparable,
  a.site_city_comparable_employee_snapshots,
  a.same_office_site_and_city_employee_snapshots,
  ROUND(100.0 * a.same_office_site_and_city_employee_snapshots
    / NULLIF(a.site_city_comparable_employee_snapshots, 0), 4)
    AS same_office_site_and_city_percent_of_site_city_comparable,
  a.same_office_site_with_city_observed_employee_snapshots,
  a.same_office_site_different_city_employee_snapshots,
  ROUND(100.0 * a.same_office_site_different_city_employee_snapshots
    / NULLIF(a.same_office_site_with_city_observed_employee_snapshots, 0), 4)
    AS same_office_site_different_city_percent_when_site_and_city_observed,
  l.snapshot_date AS mapping_snapshot_date,
  m.office_site_codes_with_a_nonblank_city,
  m.office_site_codes_used_in_multiple_cities,
  m.employees_assigned_to_office_site_codes_used_in_multiple_cities
FROM annual a
CROSS JOIN latest_snapshot l
CROSS JOIN mapping_summary m
ORDER BY a.fiscal_year;
