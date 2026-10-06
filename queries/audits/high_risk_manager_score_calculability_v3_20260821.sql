WITH target AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
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
    DENSE_RANK() OVER (ORDER BY snapshot_date) AS snapshot_seq,
    DENSE_RANK() OVER (ORDER BY snapshot_date DESC) AS reverse_snapshot_seq
  FROM target
  GROUP BY snapshot_date
), base AS (
  SELECT
    t.snapshot_date,
    c.snapshot_seq,
    c.reverse_snapshot_seq,
    t.employee_id,
    t.manager_employee_id,
    t.region,
    t.job_family,
    t.job_level_primary_position,
    t.tenure_start_date
  FROM target t
  INNER JOIN snapshot_calendar c
    ON c.snapshot_date = t.snapshot_date
), latest AS (
  SELECT
    snapshot_date,
    snapshot_seq
  FROM snapshot_calendar
  WHERE reverse_snapshot_seq = 1
), current_employees AS (
  SELECT
    b.snapshot_date,
    b.snapshot_seq,
    b.reverse_snapshot_seq,
    b.employee_id,
    b.manager_employee_id,
    b.region,
    b.job_family,
    b.job_level_primary_position,
    b.tenure_start_date
  FROM base b
  INNER JOIN latest l
    ON l.snapshot_date = b.snapshot_date
), current_managers AS (
  SELECT DISTINCT manager_employee_id AS manager_id
  FROM current_employees
  WHERE manager_employee_id IS NOT NULL
), manager_exposure AS (
  SELECT
    b.manager_employee_id AS manager_id,
    COUNT(*) AS employee_months,
    COUNT(DISTINCT b.employee_id) AS distinct_reports
  FROM base b
  INNER JOIN latest l
    ON b.snapshot_seq BETWEEN l.snapshot_seq - 11 AND l.snapshot_seq
  INNER JOIN current_managers m
    ON m.manager_id = b.manager_employee_id
  GROUP BY b.manager_employee_id
), voluntary_feed AS (
  SELECT COUNT(*) AS global_voluntary_event_count
  FROM hrda.all_terminations a
  CROSS JOIN latest l
  WHERE a.term_date IS NOT NULL
    AND a.term_date <= l.snapshot_date
    AND LOWER(TRIM(a.term_type)) IN ('voluntary', 'voluntary exception')
), assignments AS (
  SELECT
    c.employee_id,
    CASE
      WHEN c.manager_employee_id IS NOT NULL
       AND NULLIF(TRIM(c.region), '') IS NOT NULL
       AND NULLIF(TRIM(c.job_family), '') IS NOT NULL
       AND NULLIF(TRIM(c.job_level_primary_position), '') IS NOT NULL
       AND c.tenure_start_date IS NOT NULL
      THEN 1 ELSE 0
    END AS inputs_complete,
    CASE WHEN e.manager_id IS NOT NULL AND e.employee_months > 0 THEN 1 ELSE 0 END AS exposure_available
  FROM current_employees c
  LEFT JOIN manager_exposure e
    ON e.manager_id = c.manager_employee_id
), manager_metrics AS (
  SELECT
    COUNT(*) AS manager_snapshot_count,
    COALESCE(SUM(CASE WHEN e.manager_id IS NULL OR e.employee_months = 0 THEN 1 ELSE 0 END), 0) AS manager_without_exposure_count,
    COALESCE(SUM(CASE WHEN e.manager_id IS NOT NULL AND e.employee_months > 0 THEN 1 ELSE 0 END), 0) AS scoreable_manager_count,
    COALESCE(SUM(CASE WHEN e.distinct_reports < 5 OR e.employee_months < 60 THEN 1 ELSE 0 END), 0) AS managers_requiring_strong_shrinkage_count
  FROM current_managers m
  LEFT JOIN manager_exposure e
    ON e.manager_id = m.manager_id
), employee_metrics AS (
  SELECT
    COUNT(*) AS eligible_count,
    COALESCE(SUM(inputs_complete), 0) AS complete_input_count,
    COALESCE(SUM(CASE WHEN inputs_complete = 0 THEN 1 ELSE 0 END), 0) AS incomplete_input_count,
    COALESCE(SUM(CASE WHEN inputs_complete = 1 AND exposure_available = 1 THEN 1 ELSE 0 END), 0) AS scoreable_employee_count,
    COALESCE(SUM(CASE WHEN inputs_complete = 1 AND exposure_available = 0 THEN 1 ELSE 0 END), 0) AS score_assignment_unmatched_count
  FROM assignments
)
SELECT
  'High risk manager' AS variable_name,
  e.eligible_count,
  e.complete_input_count,
  e.incomplete_input_count,
  e.scoreable_employee_count,
  e.score_assignment_unmatched_count,
  m.manager_snapshot_count,
  m.scoreable_manager_count,
  m.manager_without_exposure_count,
  m.managers_requiring_strong_shrinkage_count,
  f.global_voluntary_event_count,
  CASE WHEN f.global_voluntary_event_count > 0 THEN 1 ELSE 0 END AS global_prior_available
FROM employee_metrics e
CROSS JOIN manager_metrics m
CROSS JOIN voluntary_feed f;
