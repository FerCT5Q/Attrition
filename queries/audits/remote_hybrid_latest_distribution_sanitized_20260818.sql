-- Aggregate-only, privacy-safe distribution of the latest work_arrangement
-- snapshot. Legacy prefixes are removed for display; labels that reveal a
-- sensitive personal reason and categories below the minimum cohort are
-- grouped rather than disclosed.

WITH latest_snapshot AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
base AS (
  SELECT
    employee_id,
    REGEXP_REPLACE(
      UPPER(NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), '')),
      '^[A-Z0-9]+\\.\\s*', ''
    ) AS canonical_category
  FROM hrda.post_hire_monthly_worker_dtls
  CROSS JOIN latest_snapshot l
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND CAST(fis_mo_end_dt AS DATE) = l.snapshot_date
    AND NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), '') IS NOT NULL
),
safe_groups AS (
  SELECT
    CASE
      WHEN canonical_category LIKE '%MEDICAL%'
        OR canonical_category LIKE '%CAREGIV%'
      THEN 'Sensitive / restricted reason'
      ELSE canonical_category
    END AS initial_group,
    employee_id
  FROM base
),
initial_counts AS (
  SELECT
    initial_group,
    COUNT(DISTINCT employee_id) AS employee_count
  FROM safe_groups
  GROUP BY initial_group
),
final_groups AS (
  SELECT
    CASE
      WHEN employee_count < 30
       AND initial_group <> 'Sensitive / restricted reason'
      THEN 'Other low-frequency categories (<30 employees)'
      ELSE initial_group
    END AS display_category,
    employee_count
  FROM initial_counts
),
distribution AS (
  SELECT
    display_category,
    SUM(employee_count) AS employee_count,
    COUNT(*) AS source_category_groups
  FROM final_groups
  GROUP BY display_category
),
totals AS (
  SELECT SUM(employee_count) AS total_employees FROM distribution
)
SELECT
  l.snapshot_date,
  d.display_category,
  d.employee_count,
  ROUND(100.0 * d.employee_count / NULLIF(t.total_employees, 0), 3)
    AS percent_of_populated_work_arrangement,
  d.source_category_groups
FROM distribution d
CROSS JOIN totals t
CROSS JOIN latest_snapshot l
ORDER BY d.employee_count DESC, d.display_category;
