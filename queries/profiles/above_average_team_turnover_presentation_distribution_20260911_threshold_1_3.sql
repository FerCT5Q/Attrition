-- Claim: publish the latest snapshot's Above-average team turnover signal as
-- aggregate-only 0 / 1 / Unknown report counts plus the eligible-manager
-- benchmark.  No employee, manager, event, or rate-level identity is output.
--
-- The time-safe definition is identical to the v4 assessment: 18 prior,
-- consecutive closed monthly intervals; strict Voluntary employee-date events;
-- manager-at-start-of-interval attribution; average team >=4; >=2 exits; and
-- a six-month rate compared with 1.3 times the exposure-weighted benchmark.
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
), evaluation_snapshot AS (
  SELECT c.snapshot_date, c.fiscal_year, c.closure_sequence
  FROM closure_sequence AS c
  CROSS JOIN bounds AS b
  WHERE c.closure_sequence = b.max_sequence
    AND c.closure_sequence > 18
), scope_bounds AS (
  SELECT closure_sequence - 18 AS first_required_sequence,
    closure_sequence AS last_required_sequence
  FROM evaluation_snapshot
), base_exposure_raw AS (
  SELECT c.snapshot_date, c.closure_sequence, w.employee_id, w.manager_employee_id
  FROM closure_sequence AS c
  CROSS JOIN scope_bounds AS b
  INNER JOIN hrda.post_hire_monthly_worker_dtls AS w
    ON CAST(w.fis_mo_end_dt AS DATE) = c.snapshot_date
  WHERE c.closure_sequence BETWEEN b.first_required_sequence AND b.last_required_sequence
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.manager_employee_id IS NOT NULL
), base_exposure AS (
  SELECT snapshot_date, closure_sequence, employee_id, manager_employee_id
  FROM (
    SELECT b.snapshot_date, b.closure_sequence, b.employee_id, b.manager_employee_id,
      ROW_NUMBER() OVER (
        PARTITION BY b.closure_sequence, b.employee_id ORDER BY b.manager_employee_id
      ) AS row_rank
    FROM base_exposure_raw AS b
  ) AS deduplicated
  WHERE row_rank = 1
), intervals AS (
  SELECT s.closure_sequence AS interval_start_sequence, s.snapshot_date AS interval_start,
    n.snapshot_date AS interval_end
  FROM closure_sequence AS s
  CROSS JOIN scope_bounds AS b
  INNER JOIN closure_sequence AS n ON n.closure_sequence = s.closure_sequence + 1
  WHERE s.closure_sequence BETWEEN b.first_required_sequence AND b.last_required_sequence - 1
), voluntary_events AS (
  SELECT w.employee_id, CAST(w.term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN scope_bounds AS b
  INNER JOIN closure_sequence AS first_closure
    ON first_closure.closure_sequence = b.first_required_sequence
  INNER JOIN closure_sequence AS last_closure
    ON last_closure.closure_sequence = b.last_required_sequence
  WHERE CAST(w.term_date AS DATE) > first_closure.snapshot_date
    AND CAST(w.term_date AS DATE) <= last_closure.snapshot_date
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
  GROUP BY 1, 2
), event_attribution AS (
  SELECT i.interval_start_sequence, x.manager_employee_id, v.employee_id, v.term_date
  FROM intervals AS i
  INNER JOIN voluntary_events AS v
    ON v.term_date > i.interval_start
   AND v.term_date <= i.interval_end
  INNER JOIN base_exposure AS x
    ON x.closure_sequence = i.interval_start_sequence
   AND x.employee_id = v.employee_id
), manager_interval AS (
  SELECT x.closure_sequence, x.manager_employee_id,
    COUNT(*)::BIGINT AS team_size,
    COALESCE(e.voluntary_exit_count, 0)::BIGINT AS voluntary_exit_count
  FROM base_exposure AS x
  LEFT JOIN (
    SELECT interval_start_sequence, manager_employee_id, COUNT(*)::BIGINT AS voluntary_exit_count
    FROM event_attribution
    GROUP BY 1, 2
  ) AS e
    ON e.interval_start_sequence = x.closure_sequence
   AND e.manager_employee_id = x.manager_employee_id
  GROUP BY 1, 2, 4
), manager_rolling AS (
  SELECT m.closure_sequence, m.manager_employee_id,
    COUNT(*) OVER (
      PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence
      ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING
    )::BIGINT AS observed_interval_count,
    MIN(m.closure_sequence) OVER (
      PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence
      ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING
    )::BIGINT AS first_history_sequence,
    MAX(m.closure_sequence) OVER (
      PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence
      ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING
    )::BIGINT AS last_history_sequence,
    SUM(m.team_size) OVER (
      PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence
      ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING
    )::BIGINT AS historical_exposure,
    AVG(m.team_size::DECIMAL(20,6)) OVER (
      PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence
      ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING
    ) AS average_team_size,
    SUM(m.voluntary_exit_count) OVER (
      PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence
      ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING
    )::BIGINT AS voluntary_exit_count
  FROM manager_interval AS m
), manager_context AS (
  SELECT e.snapshot_date AS evaluation_date, e.closure_sequence,
    r.manager_employee_id, r.observed_interval_count, r.first_history_sequence,
    r.last_history_sequence, r.historical_exposure, r.average_team_size,
    r.voluntary_exit_count,
    CASE WHEN r.observed_interval_count = 18
           AND r.last_history_sequence - r.first_history_sequence = 17
           AND r.average_team_size >= 4
           AND r.voluntary_exit_count >= 2
           AND r.historical_exposure > 0
         THEN 1 ELSE 0 END AS manager_eligible,
    CASE WHEN r.historical_exposure > 0
         THEN r.voluntary_exit_count::DECIMAL(30,12) / r.historical_exposure * 6 END AS six_month_rate
  FROM evaluation_snapshot AS e
  INNER JOIN manager_rolling AS r
    ON r.closure_sequence = e.closure_sequence
), benchmarks AS (
  -- With 18 qualifying intervals for every eligible manager, weighting rates
  -- by average team size is exactly exits / exposure * 6.
  SELECT closure_sequence,
    SUM(voluntary_exit_count)::DECIMAL(30,12) / NULLIF(SUM(historical_exposure), 0) * 6
      AS weighted_benchmark_six_month_rate
  FROM manager_context
  WHERE manager_eligible = 1
  GROUP BY 1
), assigned_reports AS (
  SELECT e.snapshot_date,
    CASE
      WHEN c.manager_eligible = 1
       AND b.weighted_benchmark_six_month_rate IS NOT NULL
       AND c.six_month_rate >= b.weighted_benchmark_six_month_rate * 1.3 THEN '1'
      WHEN c.manager_eligible = 1
       AND b.weighted_benchmark_six_month_rate IS NOT NULL THEN '0'
      ELSE 'Unknown'
    END AS signal_value
  FROM evaluation_snapshot AS e
  INNER JOIN base_exposure AS x
    ON x.closure_sequence = e.closure_sequence
  LEFT JOIN manager_context AS c
    ON c.closure_sequence = e.closure_sequence
   AND c.manager_employee_id = x.manager_employee_id
  LEFT JOIN benchmarks AS b ON b.closure_sequence = e.closure_sequence
), distribution AS (
  SELECT signal_value, COUNT(*)::BIGINT AS employee_count
  FROM assigned_reports
  GROUP BY 1
), summary AS (
  SELECT e.snapshot_date,
    COUNT(a.signal_value)::BIGINT AS eligible_employees,
    SUM(CASE WHEN a.signal_value IN ('0', '1') THEN 1 ELSE 0 END)::BIGINT AS observable_employees,
    SUM(CASE WHEN a.signal_value = '1' THEN 1 ELSE 0 END)::BIGINT AS flagged_employees,
    SUM(CASE WHEN a.signal_value = 'Unknown' THEN 1 ELSE 0 END)::BIGINT AS unknown_employees,
    MAX(b.weighted_benchmark_six_month_rate) AS weighted_benchmark_six_month_rate
  FROM evaluation_snapshot AS e
  LEFT JOIN assigned_reports AS a ON a.snapshot_date = e.snapshot_date
  LEFT JOIN benchmarks AS b ON b.closure_sequence = e.closure_sequence
  GROUP BY 1
)
SELECT snapshot_date, row_type, signal_value, employee_count, eligible_employees,
  observable_employees, flagged_employees, unknown_employees,
  weighted_benchmark_six_month_rate, threshold_six_month_rate
FROM (
  SELECT s.snapshot_date, 'distribution'::VARCHAR(16) AS row_type,
    d.signal_value, d.employee_count,
    NULL::BIGINT AS eligible_employees, NULL::BIGINT AS observable_employees,
    NULL::BIGINT AS flagged_employees, NULL::BIGINT AS unknown_employees,
    NULL::DECIMAL(30,12) AS weighted_benchmark_six_month_rate,
    NULL::DECIMAL(30,12) AS threshold_six_month_rate,
    CASE d.signal_value WHEN '0' THEN 1 WHEN '1' THEN 2 ELSE 3 END AS row_sort
  FROM distribution AS d
  CROSS JOIN summary AS s
  UNION ALL
  SELECT snapshot_date, 'summary'::VARCHAR(16), NULL::VARCHAR(16), NULL::BIGINT,
    eligible_employees, observable_employees, flagged_employees, unknown_employees,
    weighted_benchmark_six_month_rate,
    weighted_benchmark_six_month_rate * 1.3,
    4
  FROM summary
) AS published
ORDER BY row_sort;
