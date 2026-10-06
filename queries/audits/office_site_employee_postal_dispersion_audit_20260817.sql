-- Aggregate-only test of the hypothesis that postal_code is an office-site ZIP.
-- It compares employee postal-code dispersion within the same normalized
-- office_site and monthly snapshot without returning employees, sites, or ZIPs.
--
-- Acceptance rule for an office-site ZIP candidate:
-- among office-site/month groups with at least two active regular employees and
-- a populated postal code, zero groups may contain more than one postal code.
-- A failure means this field cannot be used as an office_site -> ZIP mapping.

WITH base AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    UPPER(NULLIF(TRIM(CAST(office_site AS VARCHAR(256))), '')) AS office_site,
    NULLIF(TRIM(CAST(postal_code AS VARCHAR(256))), '') AS postal_code,
    employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
office_month AS (
  SELECT
    snapshot_date,
    office_site,
    COUNT(DISTINCT employee_id) AS employees_in_office_month,
    COUNT(DISTINCT postal_code) AS distinct_postal_codes,
    COUNT(DISTINCT CASE WHEN postal_code IS NOT NULL THEN employee_id END)
      AS employees_with_postal_code
  FROM base
  WHERE office_site IS NOT NULL
  GROUP BY 1, 2
),
eligible_groups AS (
  SELECT
    snapshot_date,
    office_site,
    employees_in_office_month,
    distinct_postal_codes,
    employees_with_postal_code
  FROM office_month
  WHERE employees_in_office_month >= 2
    AND employees_with_postal_code >= 2
)
SELECT
  COUNT(*) AS comparable_office_site_months,
  SUM(CASE WHEN distinct_postal_codes = 1 THEN 1 ELSE 0 END)
    AS office_site_months_with_one_postal_code,
  SUM(CASE WHEN distinct_postal_codes > 1 THEN 1 ELSE 0 END)
    AS office_site_months_with_multiple_postal_codes,
  ROUND(
    100.0 * SUM(CASE WHEN distinct_postal_codes > 1 THEN 1 ELSE 0 END)
      / NULLIF(COUNT(*), 0),
    4
  ) AS multiple_postal_code_group_percent,
  SUM(CASE WHEN distinct_postal_codes > 1 THEN employees_in_office_month ELSE 0 END)
    AS employee_snapshots_in_multiple_postal_groups,
  MAX(distinct_postal_codes) AS max_postal_codes_in_one_office_site_month
FROM eligible_groups;
