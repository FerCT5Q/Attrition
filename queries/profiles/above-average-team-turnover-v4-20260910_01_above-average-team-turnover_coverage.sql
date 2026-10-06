-- Claim: for each selected monthly snapshot t, the candidate yields 0, 1, or
-- Unknown without using events after t. This profile retains the most recent
-- 42 evaluable closures so Coverage, Missingness, and History are assessed from
-- aggregate observations. No employee or manager identifier is selected.
WITH closure_dates AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    MAX(fiscal_year) AS fiscal_year
  FROM hrda.post_hire_monthly_worker_dtls
  GROUP BY 1
), closure_sequence AS (
  SELECT snapshot_date, fiscal_year,
    ROW_NUMBER() OVER (ORDER BY snapshot_date) AS closure_sequence
  FROM closure_dates
), bounds AS (
  SELECT MAX(closure_sequence) AS max_sequence
  FROM closure_sequence
), evaluation_snapshots AS (
  SELECT c.snapshot_date, c.fiscal_year, c.closure_sequence
  FROM closure_sequence AS c
  CROSS JOIN bounds AS b
  WHERE c.closure_sequence > 18
    AND c.closure_sequence >= b.max_sequence - 41
), intervals AS (
  SELECT e.snapshot_date AS evaluation_date,
    e.closure_sequence AS evaluation_sequence,
    s.closure_sequence AS interval_start_sequence,
    s.snapshot_date AS interval_start,
    n.snapshot_date AS interval_end
  FROM evaluation_snapshots AS e
  INNER JOIN closure_sequence AS s
    ON s.closure_sequence BETWEEN e.closure_sequence - 18 AND e.closure_sequence - 1
  INNER JOIN closure_sequence AS n
    ON n.closure_sequence = s.closure_sequence + 1
), exposure_raw AS (
  SELECT i.evaluation_date, i.evaluation_sequence, i.interval_start_sequence,
    i.interval_start, i.interval_end, w.employee_id, w.manager_employee_id
  FROM intervals AS i
  INNER JOIN hrda.post_hire_monthly_worker_dtls AS w
    ON CAST(w.fis_mo_end_dt AS DATE) = i.interval_start
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.manager_employee_id IS NOT NULL
), exposure AS (
  SELECT evaluation_date, evaluation_sequence, interval_start_sequence,
    interval_start, interval_end, employee_id, manager_employee_id
  FROM (
    SELECT e.*,
      ROW_NUMBER() OVER (
        PARTITION BY e.evaluation_sequence, e.interval_start_sequence, e.employee_id
        ORDER BY e.manager_employee_id
      ) AS row_rank
    FROM exposure_raw AS e
  ) AS deduplicated
  WHERE row_rank = 1
), current_members AS (
  SELECT evaluation_date, evaluation_sequence, employee_id, manager_employee_id
  FROM (
    SELECT e.snapshot_date AS evaluation_date, e.closure_sequence AS evaluation_sequence,
      w.employee_id, w.manager_employee_id,
      ROW_NUMBER() OVER (
        PARTITION BY e.closure_sequence, w.employee_id
        ORDER BY w.manager_employee_id
      ) AS row_rank
    FROM evaluation_snapshots AS e
    INNER JOIN hrda.post_hire_monthly_worker_dtls AS w
      ON CAST(w.fis_mo_end_dt AS DATE) = e.snapshot_date
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.manager_employee_id IS NOT NULL
  ) AS deduplicated
  WHERE row_rank = 1
), current_teams AS (
  SELECT evaluation_date, evaluation_sequence, manager_employee_id,
    COUNT(*)::BIGINT AS current_direct_reports
  FROM current_members
  GROUP BY 1, 2, 3
), window_bounds AS (
  SELECT MIN(interval_start) AS minimum_interval_start,
    MAX(evaluation_date) AS maximum_evaluation_date
  FROM intervals
), voluntary_events AS (
  SELECT w.employee_id, CAST(w.term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN window_bounds AS b
  WHERE CAST(w.term_date AS DATE) > b.minimum_interval_start
    AND CAST(w.term_date AS DATE) <= b.maximum_evaluation_date
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
  GROUP BY 1, 2
), event_attribution AS (
  SELECT i.evaluation_date, i.evaluation_sequence, i.interval_start_sequence,
    x.manager_employee_id, v.employee_id, v.term_date
  FROM intervals AS i
  INNER JOIN voluntary_events AS v
    ON v.term_date > i.interval_start
   AND v.term_date <= i.interval_end
  INNER JOIN exposure AS x
    ON x.evaluation_sequence = i.evaluation_sequence
   AND x.interval_start_sequence = i.interval_start_sequence
   AND x.employee_id = v.employee_id
), manager_interval AS (
  SELECT evaluation_date, evaluation_sequence, interval_start_sequence,
    manager_employee_id, COUNT(*)::BIGINT AS team_size
  FROM exposure
  GROUP BY 1, 2, 3, 4
), manager_interval_events AS (
  SELECT evaluation_date, evaluation_sequence, interval_start_sequence,
    manager_employee_id, COUNT(*)::BIGINT AS voluntary_exit_count
  FROM event_attribution
  GROUP BY 1, 2, 3, 4
), manager_history AS (
  SELECT m.evaluation_date, m.evaluation_sequence, m.manager_employee_id,
    COUNT(*)::BIGINT AS observed_interval_count,
    SUM(m.team_size)::BIGINT AS historical_exposure,
    AVG(m.team_size::DECIMAL(20,6)) AS average_team_size,
    COALESCE(SUM(e.voluntary_exit_count), 0)::BIGINT AS voluntary_exit_count
  FROM manager_interval AS m
  LEFT JOIN manager_interval_events AS e
    ON e.evaluation_sequence = m.evaluation_sequence
   AND e.interval_start_sequence = m.interval_start_sequence
   AND e.manager_employee_id = m.manager_employee_id
  GROUP BY 1, 2, 3
), manager_rates AS (
  SELECT t.evaluation_date, t.evaluation_sequence, t.manager_employee_id,
    t.current_direct_reports, h.observed_interval_count, h.historical_exposure,
    h.average_team_size, h.voluntary_exit_count,
    CASE WHEN h.observed_interval_count = 18
           AND h.average_team_size >= 4
           AND h.voluntary_exit_count >= 2
           AND h.historical_exposure > 0
         THEN 1 ELSE 0 END AS manager_eligible,
    CASE WHEN h.historical_exposure > 0
         THEN h.voluntary_exit_count::DECIMAL(30,12) / h.historical_exposure * 6
         ELSE NULL END AS six_month_rate
  FROM current_teams AS t
  LEFT JOIN manager_history AS h
    ON h.evaluation_sequence = t.evaluation_sequence
   AND h.manager_employee_id = t.manager_employee_id
), benchmarks AS (
  SELECT evaluation_date, evaluation_sequence,
    COUNT(*)::BIGINT AS eligible_manager_count,
    SUM(voluntary_exit_count)::BIGINT AS eligible_voluntary_exits,
    SUM(historical_exposure)::BIGINT AS eligible_historical_exposure,
    SUM(six_month_rate * average_team_size)
      / NULLIF(SUM(average_team_size), 0) AS weighted_benchmark_six_month_rate
  FROM manager_rates
  WHERE manager_eligible = 1
  GROUP BY 1, 2
), assigned_reports AS (
  SELECT m.evaluation_date, m.evaluation_sequence, m.employee_id,
    CASE
      WHEN r.manager_eligible = 1
       AND b.weighted_benchmark_six_month_rate IS NOT NULL
       AND r.six_month_rate >= b.weighted_benchmark_six_month_rate * 1.4 THEN '1'
      WHEN r.manager_eligible = 1
       AND b.weighted_benchmark_six_month_rate IS NOT NULL THEN '0'
      ELSE 'Unknown'
    END AS signal_value
  FROM current_members AS m
  LEFT JOIN manager_rates AS r
    ON r.evaluation_sequence = m.evaluation_sequence
   AND r.manager_employee_id = m.manager_employee_id
  LEFT JOIN benchmarks AS b
    ON b.evaluation_sequence = m.evaluation_sequence
), profile AS (
  SELECT a.evaluation_date, e.fiscal_year,
    COUNT(*)::BIGINT AS eligible_employees,
    SUM(CASE WHEN a.signal_value IN ('0', '1') THEN 1 ELSE 0 END)::BIGINT AS observable_employees,
    SUM(CASE WHEN a.signal_value = '1' THEN 1 ELSE 0 END)::BIGINT AS event_employees,
    SUM(CASE WHEN a.signal_value = 'Unknown' THEN 1 ELSE 0 END)::BIGINT AS unknown_employees
  FROM assigned_reports AS a
  INNER JOIN evaluation_snapshots AS e
    ON e.evaluation_sequence = a.evaluation_sequence
  GROUP BY 1, 2
)
SELECT evaluation_date AS snapshot_date, fiscal_year, eligible_employees,
  observable_employees, event_employees,
  CONCAT('Unknown=', unknown_employees::VARCHAR(32),
    '; 18 intervals; avg team >=4; >=2 Voluntary exits; ratio >=1.4x benchmark.') AS notes
FROM profile
ORDER BY snapshot_date;
