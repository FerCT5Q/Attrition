/*
  Slide 41 internal stage: above-average team turnover.

  Reconstruct the approved 18-interval historical signal at the
  2025-08-24 baseline.  Attrition labels are prospective voluntary exits of
  baseline direct reports in the displayed 0 / 1 / Unknown signal category.
  Unknown is retained as a real category and is not treated as zero.
*/
WITH closure_dates AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls GROUP BY 1
), closure_sequence AS (
  SELECT snapshot_date, ROW_NUMBER() OVER (ORDER BY snapshot_date) AS closure_sequence
  FROM closure_dates
), evaluation_snapshot AS (
  SELECT closure_sequence, snapshot_date AS baseline_date
  FROM closure_sequence WHERE snapshot_date = DATE '2025-08-24'
), history_bounds AS (
  SELECT closure_sequence - 18 AS first_required_sequence,
         closure_sequence AS last_required_sequence
  FROM evaluation_snapshot
), base_exposure_raw AS (
  SELECT c.snapshot_date, c.closure_sequence,
         CAST(w.employee_id AS BIGINT) AS employee_id,
         CAST(w.manager_employee_id AS BIGINT) AS manager_employee_id
  FROM closure_sequence c
  CROSS JOIN history_bounds h
  INNER JOIN hrda.post_hire_monthly_worker_dtls w
    ON CAST(w.fis_mo_end_dt AS DATE) = c.snapshot_date
  WHERE c.closure_sequence BETWEEN h.first_required_sequence AND h.last_required_sequence
    AND w.worker_type = 'Employee' AND w.employee_type = 'Regular'
    AND w.active_status = 1 AND COALESCE(w.is_rf360_yes_no, 0) = 0
    AND w.employee_id IS NOT NULL AND w.manager_employee_id IS NOT NULL
),
base_exposure AS (
  SELECT snapshot_date, closure_sequence, employee_id, manager_employee_id
  FROM (
    SELECT b.snapshot_date, b.closure_sequence, b.employee_id, b.manager_employee_id,
           ROW_NUMBER() OVER (PARTITION BY b.closure_sequence, b.employee_id ORDER BY b.manager_employee_id) AS row_rank
    FROM base_exposure_raw b
  ) d WHERE row_rank = 1
),
intervals AS (
  SELECT s.closure_sequence AS interval_start_sequence,
         s.snapshot_date AS interval_start,
         n.snapshot_date AS interval_end
  FROM closure_sequence s
  CROSS JOIN history_bounds h
  INNER JOIN closure_sequence n ON n.closure_sequence = s.closure_sequence + 1
  WHERE s.closure_sequence BETWEEN h.first_required_sequence AND h.last_required_sequence - 1
),
voluntary_events AS (
  SELECT CAST(w.employee_id AS BIGINT) AS employee_id,
         CAST(w.term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN history_bounds h
  INNER JOIN closure_sequence first_c ON first_c.closure_sequence = h.first_required_sequence
  INNER JOIN closure_sequence last_c ON last_c.closure_sequence = h.last_required_sequence
  WHERE w.worker_type = 'Employee' AND w.employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
    AND CAST(w.term_date AS DATE) > first_c.snapshot_date
    AND CAST(w.term_date AS DATE) <= last_c.snapshot_date
    AND w.employee_id IS NOT NULL
  GROUP BY 1, 2
),
event_attribution AS (
  SELECT i.interval_start_sequence, x.manager_employee_id, v.employee_id, v.term_date
  FROM intervals i
  INNER JOIN voluntary_events v ON v.term_date > i.interval_start AND v.term_date <= i.interval_end
  INNER JOIN base_exposure x ON x.closure_sequence = i.interval_start_sequence AND x.employee_id = v.employee_id
),
manager_interval AS (
  SELECT x.closure_sequence, x.manager_employee_id,
         COUNT(*) AS team_size,
         COALESCE(e.voluntary_exit_count, 0) AS voluntary_exit_count
  FROM base_exposure x
  LEFT JOIN (
    SELECT interval_start_sequence, manager_employee_id, COUNT(*) AS voluntary_exit_count
    FROM event_attribution GROUP BY 1, 2
  ) e ON e.interval_start_sequence = x.closure_sequence AND e.manager_employee_id = x.manager_employee_id
  GROUP BY 1, 2, 4
),
manager_rolling AS (
  SELECT m.closure_sequence, m.manager_employee_id,
         COUNT(*) OVER (PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING) AS observed_interval_count,
         MIN(m.closure_sequence) OVER (PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING) AS first_history_sequence,
         MAX(m.closure_sequence) OVER (PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING) AS last_history_sequence,
         SUM(m.team_size) OVER (PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING) AS historical_exposure,
         AVG(m.team_size::DECIMAL(20,6)) OVER (PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING) AS average_team_size,
         SUM(m.voluntary_exit_count) OVER (PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING) AS voluntary_exit_count
  FROM manager_interval m
),
manager_context AS (
  SELECT e.closure_sequence, r.manager_employee_id, r.observed_interval_count,
         r.first_history_sequence, r.last_history_sequence, r.historical_exposure,
         r.average_team_size, r.voluntary_exit_count,
         CASE WHEN r.observed_interval_count = 18
                    AND r.last_history_sequence - r.first_history_sequence = 17
                    AND r.average_team_size >= 4
                    AND r.voluntary_exit_count >= 2
                    AND r.historical_exposure > 0 THEN 1 ELSE 0 END AS manager_eligible,
         CASE WHEN r.historical_exposure > 0
              THEN r.voluntary_exit_count::DECIMAL(30,12) / r.historical_exposure * 6 END AS six_month_rate
  FROM evaluation_snapshot e INNER JOIN manager_rolling r ON r.closure_sequence = e.closure_sequence
),
benchmarks AS (
  SELECT closure_sequence,
         SUM(voluntary_exit_count)::DECIMAL(30,12) / NULLIF(SUM(historical_exposure), 0) * 6 AS weighted_benchmark_six_month_rate
  FROM manager_context WHERE manager_eligible = 1 GROUP BY 1
),
assigned_reports AS (
  SELECT x.employee_id,
         CASE WHEN c.manager_eligible = 1 AND b.weighted_benchmark_six_month_rate IS NOT NULL
                    AND c.six_month_rate >= b.weighted_benchmark_six_month_rate * 1.3 THEN '1'
              WHEN c.manager_eligible = 1 AND b.weighted_benchmark_six_month_rate IS NOT NULL THEN '0'
              ELSE 'Unknown' END AS signal_value
  FROM evaluation_snapshot e
  INNER JOIN base_exposure x ON x.closure_sequence = e.closure_sequence
  LEFT JOIN manager_context c ON c.closure_sequence = e.closure_sequence AND c.manager_employee_id = x.manager_employee_id
  LEFT JOIN benchmarks b ON b.closure_sequence = e.closure_sequence
),
targets AS (
  SELECT DISTINCT CAST(w.employee_id AS BIGINT) AS employee_id
  FROM hrda.post_hire_monthly_worker_dtls w
  WHERE w.worker_type = 'Employee' AND w.employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
    AND CAST(w.term_date AS DATE) > DATE '2025-08-24'
    AND CAST(w.term_date AS DATE) <= DATE '2026-08-23'
),
category_metrics AS (
  SELECT a.signal_value AS category,
         COUNT(DISTINCT a.employee_id) AS employee_count,
         COUNT(DISTINCT CASE WHEN t.employee_id IS NOT NULL THEN a.employee_id END) AS voluntary_exits,
         ROUND(100.0 * COUNT(DISTINCT CASE WHEN t.employee_id IS NOT NULL THEN a.employee_id END) / NULLIF(COUNT(DISTINCT a.employee_id), 0), 4) AS annual_attrition_rate_percent
  FROM assigned_reports a LEFT JOIN targets t ON t.employee_id = a.employee_id
  GROUP BY 1
),
diagnostics AS (
  SELECT (SELECT COUNT(DISTINCT employee_id) FROM assigned_reports) AS baseline_employee_count,
         (SELECT COUNT(*) FROM manager_context WHERE manager_eligible = 1) AS eligible_manager_count,
         (SELECT COUNT(*) FROM manager_context WHERE manager_eligible = 0) AS ineligible_manager_count,
         (SELECT COUNT(*) FROM intervals) AS historical_interval_count
)
SELECT 'category' AS row_type, category, employee_count, voluntary_exits,
       annual_attrition_rate_percent, CAST(NULL AS VARCHAR(64)) AS diagnostic_metric,
       CAST(NULL AS BIGINT) AS diagnostic_value
FROM category_metrics WHERE employee_count >= 30
UNION ALL SELECT 'diagnostic', NULL, NULL, NULL, NULL, 'baseline_employee_count', baseline_employee_count FROM diagnostics
UNION ALL SELECT 'diagnostic', NULL, NULL, NULL, NULL, 'eligible_manager_count', eligible_manager_count FROM diagnostics
UNION ALL SELECT 'diagnostic', NULL, NULL, NULL, NULL, 'ineligible_manager_count', ineligible_manager_count FROM diagnostics
UNION ALL SELECT 'diagnostic', NULL, NULL, NULL, NULL, 'historical_interval_count', historical_interval_count FROM diagnostics
ORDER BY row_type, category, diagnostic_metric;
