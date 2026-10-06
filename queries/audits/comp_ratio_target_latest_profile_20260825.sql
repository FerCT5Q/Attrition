WITH eligible AS (
  SELECT
    employee_id,
    compa_ratio
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt = (
      SELECT MAX(fis_mo_end_dt)
      FROM hrda.post_hire_monthly_worker_dtls
      WHERE worker_type = 'Employee'
        AND employee_type = 'Regular'
        AND active_status = 1
        AND fis_mo_end_dt <= DATE '2026-08-25'
    )
), bands AS (
  SELECT
    CASE
      WHEN compa_ratio IS NULL THEN 'missing'
      WHEN compa_ratio <= 0 THEN 'nonpositive'
      WHEN compa_ratio < 0.8 THEN '< 0.8'
      WHEN compa_ratio < 0.9 THEN '0.8 to < 0.9'
      WHEN compa_ratio < 1.0 THEN '0.9 to < 1.0'
      WHEN compa_ratio < 1.1 THEN '1.0 to < 1.1'
      WHEN compa_ratio < 1.2 THEN '1.1 to < 1.2'
      WHEN compa_ratio <= 3.0 THEN '1.2 to <= 3.0'
      ELSE '> 3.0'
    END AS band_label,
    employee_id
  FROM eligible
), latest_date AS (
  SELECT MAX(fis_mo_end_dt) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt <= DATE '2026-08-25'
), summary AS (
  SELECT
    COUNT(*) AS eligible_rows,
    COUNT(DISTINCT employee_id) AS eligible_employees,
    COUNT(DISTINCT CASE WHEN band_label <> 'missing' THEN employee_id END) AS populated_employees,
    COUNT(DISTINCT CASE WHEN band_label = 'nonpositive' THEN employee_id END) AS nonpositive_employees,
    COUNT(DISTINCT CASE WHEN band_label = '> 3.0' THEN employee_id END) AS above_three_employees
  FROM bands
)
SELECT
  bands.band_label,
  latest_date.snapshot_date,
  COUNT(DISTINCT bands.employee_id) AS employee_count,
  COUNT(*) AS row_count,
  summary.eligible_rows,
  summary.eligible_employees,
  summary.populated_employees,
  summary.nonpositive_employees,
  summary.above_three_employees,
  ROUND(100.0 * summary.nonpositive_employees / NULLIF(summary.eligible_employees, 0), 2) AS nonpositive_employee_rate_percent,
  ROUND(100.0 * summary.above_three_employees / NULLIF(summary.eligible_employees, 0), 2) AS above_three_employee_rate_percent
FROM bands
CROSS JOIN summary
CROSS JOIN latest_date
GROUP BY
  bands.band_label,
  latest_date.snapshot_date,
  summary.eligible_rows,
  summary.eligible_employees,
  summary.populated_employees,
  summary.nonpositive_employees,
  summary.above_three_employees
HAVING COUNT(DISTINCT bands.employee_id) >= 30
ORDER BY MIN(
  CASE bands.band_label
    WHEN 'missing' THEN 0
    WHEN 'nonpositive' THEN 1
    WHEN '< 0.8' THEN 2
    WHEN '0.8 to < 0.9' THEN 3
    WHEN '0.9 to < 1.0' THEN 4
    WHEN '1.0 to < 1.1' THEN 5
    WHEN '1.1 to < 1.2' THEN 6
    WHEN '1.2 to <= 3.0' THEN 7
    ELSE 8
  END
);
