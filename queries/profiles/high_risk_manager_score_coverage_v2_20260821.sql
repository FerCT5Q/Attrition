WITH target AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(fiscal_year AS VARCHAR(32)) AS fiscal_year,
    employee_id,
    manager_employee_id,
    region,
    job_family,
    job_level_primary_position,
    COALESCE(
      CASE WHEN max_hire_rehire_date <= fis_mo_end_dt THEN max_hire_rehire_date END,
      CASE WHEN service_date <= fis_mo_end_dt THEN service_date END,
      CASE WHEN original_hire_date <= fis_mo_end_dt THEN original_hire_date END
    ) AS tenure_start_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
), snapshot_calendar AS (
  SELECT
    snapshot_date,
    MAX(fiscal_year) AS fiscal_year,
    DENSE_RANK() OVER (ORDER BY snapshot_date) AS snapshot_seq
  FROM target
  GROUP BY snapshot_date
), voluntary_feed AS (
  SELECT
    MIN(term_date) AS first_voluntary_event_date,
    COUNT(*) AS voluntary_event_count
  FROM hrda.all_terminations
  WHERE term_date IS NOT NULL
    AND LOWER(TRIM(term_type)) IN ('voluntary', 'voluntary exception')
)
SELECT
  t.snapshot_date,
  MAX(c.fiscal_year) AS fiscal_year,
  COUNT(DISTINCT t.employee_id) AS eligible_employees,
  COUNT(DISTINCT CASE
    WHEN c.snapshot_seq >= 12
     AND f.voluntary_event_count > 0
     AND f.first_voluntary_event_date <= t.snapshot_date
     AND t.manager_employee_id IS NOT NULL
     AND NULLIF(TRIM(t.region), '') IS NOT NULL
     AND NULLIF(TRIM(t.job_family), '') IS NOT NULL
     AND NULLIF(TRIM(t.job_level_primary_position), '') IS NOT NULL
     AND t.tenure_start_date IS NOT NULL
    THEN t.employee_id
  END) AS observable_employees,
  CAST(NULL AS BIGINT) AS event_employees,
  'Coverage del score continuo. Los equipos pequenos o managers nuevos reciben shrinkage hacia el prior. Los minimos de exposicion solo controlan el flag secundario.' AS notes
FROM target t
INNER JOIN snapshot_calendar c
  ON c.snapshot_date = t.snapshot_date
CROSS JOIN voluntary_feed f
GROUP BY t.snapshot_date
ORDER BY t.snapshot_date;
