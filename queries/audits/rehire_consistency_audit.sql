WITH raw_snapshots AS (
  SELECT
    employee_id,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    is_rehire,
    rehire_date,
    original_hire_date,
    max_hire_rehire_date,
    job_family,
    job_level_primary_position
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
employee_month AS (
  SELECT
    employee_id,
    snapshot_date,
    MAX(is_rehire) AS is_rehire,
    MAX(rehire_date) AS rehire_date,
    MAX(original_hire_date) AS original_hire_date,
    MAX(max_hire_rehire_date) AS max_hire_rehire_date,
    MAX(job_family) AS job_family,
    MAX(job_level_primary_position) AS job_level_primary_position,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT is_rehire) AS distinct_flag_values,
    COUNT(DISTINCT rehire_date) AS distinct_rehire_dates
  FROM raw_snapshots
  GROUP BY employee_id, snapshot_date
),
sequenced AS (
  SELECT
    employee_id,
    snapshot_date,
    is_rehire,
    rehire_date,
    original_hire_date,
    max_hire_rehire_date,
    job_family,
    job_level_primary_position,
    source_rows,
    distinct_flag_values,
    distinct_rehire_dates,
    LAG(is_rehire) OVER (
      PARTITION BY employee_id ORDER BY snapshot_date
    ) AS previous_is_rehire,
    LAG(rehire_date) OVER (
      PARTITION BY employee_id ORDER BY snapshot_date
    ) AS previous_rehire_date,
    LAG(snapshot_date) OVER (
      PARTITION BY employee_id ORDER BY snapshot_date
    ) AS previous_snapshot_date,
    LAG(job_family) OVER (
      PARTITION BY employee_id ORDER BY snapshot_date
    ) AS previous_job_family,
    LAG(job_level_primary_position) OVER (
      PARTITION BY employee_id ORDER BY snapshot_date
    ) AS previous_job_level
  FROM employee_month
)
SELECT
  snapshot_date,
  COUNT(*) AS eligible_employees,
  SUM(CASE WHEN is_rehire IS NULL THEN 1 ELSE 0 END) AS missing_flag_employees,
  SUM(CASE
    WHEN is_rehire IS NOT NULL AND is_rehire NOT IN (0, 1) THEN 1 ELSE 0
  END) AS invalid_flag_employees,
  SUM(CASE WHEN is_rehire = 1 THEN 1 ELSE 0 END) AS flagged_rehire_employees,
  SUM(CASE WHEN rehire_date IS NOT NULL THEN 1 ELSE 0 END) AS dated_rehire_employees,
  SUM(CASE
    WHEN is_rehire = 1 AND rehire_date IS NULL THEN 1 ELSE 0
  END) AS flagged_without_date_employees,
  SUM(CASE
    WHEN rehire_date IS NOT NULL AND COALESCE(is_rehire, 0) <> 1 THEN 1 ELSE 0
  END) AS date_without_flag_employees,
  SUM(CASE
    WHEN rehire_date > snapshot_date THEN 1 ELSE 0
  END) AS future_rehire_date_employees,
  SUM(CASE
    WHEN rehire_date < original_hire_date THEN 1 ELSE 0
  END) AS rehire_before_original_hire_employees,
  SUM(CASE
    WHEN is_rehire = 1
     AND rehire_date IS NOT NULL
     AND max_hire_rehire_date IS NOT NULL
     AND rehire_date <> max_hire_rehire_date
    THEN 1 ELSE 0
  END) AS rehire_vs_max_hire_mismatch_employees,
  SUM(CASE WHEN source_rows > 1 THEN 1 ELSE 0 END) AS duplicate_employee_months,
  SUM(CASE
    WHEN distinct_flag_values > 1 THEN 1 ELSE 0
  END) AS conflicting_flag_employee_months,
  SUM(CASE
    WHEN distinct_rehire_dates > 1 THEN 1 ELSE 0
  END) AS conflicting_date_employee_months,
  SUM(CASE
    WHEN previous_is_rehire = 1 AND is_rehire = 0 THEN 1 ELSE 0
  END) AS flag_one_to_zero_transitions,
  SUM(CASE
    WHEN previous_is_rehire = 0 AND is_rehire = 1 THEN 1 ELSE 0
  END) AS flag_zero_to_one_transitions,
  SUM(CASE
    WHEN previous_rehire_date IS NOT NULL
     AND rehire_date IS NOT NULL
     AND rehire_date < previous_rehire_date
    THEN 1 ELSE 0
  END) AS rehire_date_decreases,
  SUM(CASE
    WHEN previous_rehire_date IS NOT NULL
     AND rehire_date IS NOT NULL
     AND rehire_date > previous_rehire_date
    THEN 1 ELSE 0
  END) AS rehire_date_increases,
  SUM(CASE
    WHEN previous_snapshot_date IS NOT NULL
     AND COALESCE(previous_is_rehire, 0) = 0
     AND is_rehire = 1
    THEN 1 ELSE 0
  END) AS rehire_transitions_with_prior_snapshot,
  SUM(CASE
    WHEN previous_snapshot_date IS NOT NULL
     AND COALESCE(previous_is_rehire, 0) = 0
     AND is_rehire = 1
     AND previous_job_family IS NOT NULL
     AND job_family IS NOT NULL
     AND previous_job_family <> job_family
    THEN 1 ELSE 0
  END) AS rehire_with_job_family_change,
  SUM(CASE
    WHEN previous_snapshot_date IS NOT NULL
     AND COALESCE(previous_is_rehire, 0) = 0
     AND is_rehire = 1
     AND previous_job_level IS NOT NULL
     AND job_level_primary_position IS NOT NULL
     AND previous_job_level <> job_level_primary_position
    THEN 1 ELSE 0
  END) AS rehire_with_level_change,
  SUM(CASE
    WHEN previous_snapshot_date IS NOT NULL
     AND COALESCE(previous_is_rehire, 0) = 0
     AND is_rehire = 1
     AND previous_job_family IS NOT NULL
     AND job_family IS NOT NULL
     AND previous_job_level IS NOT NULL
     AND job_level_primary_position IS NOT NULL
     AND previous_job_family = job_family
     AND previous_job_level = job_level_primary_position
    THEN 1 ELSE 0
  END) AS rehire_with_neither_change
FROM sequenced
GROUP BY snapshot_date
HAVING COUNT(*) >= 30
ORDER BY snapshot_date
