-- Aggregate-only size check for historical work-arrangement labels prefixed
-- with an ordinal such as "1." or "D.". It returns no employee or category
-- values. The purpose is to distinguish a short source-format change from a
-- material, persistent domain inconsistency.

WITH base AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    UPPER(NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), '')) AS category_value,
    employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
    AND NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), '') IS NOT NULL
),
classified AS (
  SELECT
    snapshot_date,
    employee_id,
    category_value,
    CASE
      WHEN REGEXP_INSTR(category_value, '^[A-Z0-9]+\\.\\s*') = 1 THEN 1
      ELSE 0
    END AS has_legacy_prefix
  FROM base
)
SELECT
  COUNT(*) AS populated_employee_snapshots,
  SUM(has_legacy_prefix) AS prefixed_employee_snapshots,
  ROUND(100.0 * SUM(has_legacy_prefix) / NULLIF(COUNT(*), 0), 4)
    AS prefixed_snapshot_percent,
  COUNT(DISTINCT CASE WHEN has_legacy_prefix = 1 THEN employee_id END)
    AS distinct_employees_ever_with_prefixed_label,
  COUNT(DISTINCT CASE WHEN has_legacy_prefix = 1 THEN category_value END)
    AS prefixed_raw_category_variants,
  MIN(CASE WHEN has_legacy_prefix = 1 THEN snapshot_date END)
    AS first_prefixed_snapshot_date,
  MAX(CASE WHEN has_legacy_prefix = 1 THEN snapshot_date END)
    AS last_prefixed_snapshot_date,
  COUNT(DISTINCT CASE WHEN has_legacy_prefix = 1 THEN snapshot_date END)
    AS prefixed_observed_months
FROM classified;
