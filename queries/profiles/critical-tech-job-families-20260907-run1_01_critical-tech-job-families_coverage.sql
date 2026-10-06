/*
  Critical Tech mapping coverage by monthly workforce snapshot.

  Claim:
    The approved Critical Tech mapping identifies a reproducible population
    at the employee-snapshot grain.

  Population:
    worker_type='Employee', employee_type='Regular', active_status=1.
  Grain:
    One aggregate row per fis_mo_end_dt.
  Acceptance rule:
    Each emitted date must have at least 30 eligible employees. Coverage is
    calculated after the exact normalized job_family join to critical_tech.
*/
WITH critical_map AS (
  SELECT
    TRIM(LOWER(extended_job_family)) AS family_key
  FROM hrda.critical_tech
  WHERE extended_job_family IS NOT NULL
    AND TRIM(extended_job_family) <> ''
  GROUP BY 1
),
scope AS (
  SELECT DISTINCT
    CAST(p.fis_mo_end_dt AS DATE) AS snapshot_date,
    p.fiscal_year,
    p.employee_id,
    p.job_family
  FROM hrda.post_hire_monthly_worker_dtls p
  INNER JOIN critical_map c
    ON TRIM(LOWER(p.job_family)) = c.family_key
  WHERE p.worker_type = 'Employee'
    AND p.employee_type = 'Regular'
    AND p.active_status = 1
    AND p.fis_mo_end_dt IS NOT NULL
),
monthly AS (
  SELECT
    snapshot_date,
    MAX(fiscal_year) AS fiscal_year,
    COUNT(*) AS eligible_employees,
    COUNT(CASE WHEN job_family IS NOT NULL AND TRIM(job_family) <> ''
               THEN 1 END) AS observable_employees
  FROM scope
  GROUP BY 1
)
SELECT
  snapshot_date,
  fiscal_year,
  eligible_employees,
  observable_employees,
  CAST(NULL AS INTEGER) AS event_employees,
  ROUND(
    100.0 * observable_employees / NULLIF(eligible_employees, 0),
    4
  ) AS coverage_percent,
  'Critical Tech exact job_family mapping' AS notes
FROM monthly
WHERE eligible_employees >= 30
ORDER BY snapshot_date;
