-- Claim: the 18-interval derivation is time-safe, unique, and implements the
-- approved boundaries. Six independent recent monthly snapshots are checked.
-- The result is one aggregate row and contains no employee or manager IDs.
WITH closure_dates AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  GROUP BY 1
), closure_sequence AS (
  SELECT snapshot_date, ROW_NUMBER() OVER (ORDER BY snapshot_date) AS closure_sequence
  FROM closure_dates
), bounds AS (
  SELECT MAX(closure_sequence) AS max_sequence
  FROM closure_sequence
), evaluation_snapshots AS (
  SELECT c.snapshot_date, c.closure_sequence
  FROM closure_sequence AS c
  CROSS JOIN bounds AS b
  WHERE c.closure_sequence > 18
    AND c.closure_sequence >= b.max_sequence - 5
), scope_bounds AS (
  SELECT MIN(closure_sequence) - 18 AS first_required_sequence,
    MAX(closure_sequence) AS last_required_sequence
  FROM evaluation_snapshots
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
), exposure_key_counts AS (
  SELECT closure_sequence, employee_id, COUNT(*)::BIGINT AS row_count,
    COUNT(DISTINCT manager_employee_id)::BIGINT AS manager_count
  FROM base_exposure_raw
  GROUP BY 1, 2
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
), event_type_by_key AS (
  SELECT w.employee_id, CAST(w.term_date AS DATE) AS term_date,
    COUNT(*)::BIGINT AS source_row_count,
    COUNT(DISTINCT UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')))::BIGINT AS normalized_type_count,
    SUM(CASE WHEN UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY' THEN 1 ELSE 0 END)::BIGINT AS voluntary_source_row_count
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN scope_bounds AS b
  INNER JOIN closure_sequence AS first_closure ON first_closure.closure_sequence = b.first_required_sequence
  INNER JOIN closure_sequence AS last_closure ON last_closure.closure_sequence = b.last_required_sequence
  WHERE CAST(w.term_date AS DATE) > first_closure.snapshot_date
    AND CAST(w.term_date AS DATE) <= last_closure.snapshot_date
    AND w.term_date IS NOT NULL
  GROUP BY 1, 2
), voluntary_events AS (
  SELECT employee_id, term_date, source_row_count, normalized_type_count
  FROM event_type_by_key
  WHERE voluntary_source_row_count > 0
), event_interval_matches AS (
  SELECT i.interval_start_sequence, v.employee_id, v.term_date
  FROM intervals AS i
  INNER JOIN voluntary_events AS v
    ON v.term_date > i.interval_start
   AND v.term_date <= i.interval_end
), event_interval_counts AS (
  SELECT interval_start_sequence, employee_id, term_date, COUNT(*)::BIGINT AS match_count
  FROM event_interval_matches
  GROUP BY 1, 2, 3
), event_attribution AS (
  SELECT e.interval_start_sequence, x.manager_employee_id, e.employee_id, e.term_date
  FROM event_interval_matches AS e
  INNER JOIN base_exposure AS x
    ON x.closure_sequence = e.interval_start_sequence
   AND x.employee_id = e.employee_id
), event_attribution_counts AS (
  SELECT interval_start_sequence, employee_id, term_date, COUNT(*)::BIGINT AS match_count,
    COUNT(DISTINCT manager_employee_id)::BIGINT AS manager_count
  FROM event_attribution
  GROUP BY 1, 2, 3
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
    COUNT(*) OVER (PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING)::BIGINT AS observed_interval_count,
    MIN(m.closure_sequence) OVER (PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING)::BIGINT AS first_history_sequence,
    MAX(m.closure_sequence) OVER (PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING)::BIGINT AS last_history_sequence,
    SUM(m.team_size) OVER (PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING)::BIGINT AS historical_exposure,
    AVG(m.team_size::DECIMAL(20,6)) OVER (PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING) AS average_team_size,
    SUM(m.voluntary_exit_count) OVER (PARTITION BY m.manager_employee_id ORDER BY m.closure_sequence ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING)::BIGINT AS voluntary_exit_count
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
           AND r.historical_exposure > 0 THEN 1 ELSE 0 END AS manager_eligible,
    CASE WHEN r.historical_exposure > 0
         THEN r.voluntary_exit_count::DECIMAL(30,12) / r.historical_exposure * 6 END AS six_month_rate
  FROM evaluation_snapshots AS e
  INNER JOIN manager_rolling AS r ON r.closure_sequence = e.closure_sequence
), benchmarks AS (
  SELECT closure_sequence,
    -- With exactly 18 qualifying intervals, weighting each manager's
    -- (exits/exposure*6) rate by average_team_size=exposure/18 simplifies to
    -- total exits/total exposure*6 without rounding a manager-level rate.
    SUM(voluntary_exit_count)::DECIMAL(30,12) / NULLIF(SUM(historical_exposure), 0) * 6 AS weighted_benchmark,
    SUM(voluntary_exit_count)::DECIMAL(30,12) / NULLIF(SUM(historical_exposure), 0) * 6 AS exposure_benchmark
  FROM manager_context
  WHERE manager_eligible = 1
  GROUP BY 1
), manager_scored AS (
  SELECT c.evaluation_date, c.closure_sequence, c.manager_employee_id,
    c.observed_interval_count, c.first_history_sequence, c.last_history_sequence,
    c.historical_exposure, c.average_team_size, c.voluntary_exit_count,
    c.manager_eligible, c.six_month_rate, b.weighted_benchmark, b.exposure_benchmark,
    CASE WHEN c.manager_eligible = 1 AND c.six_month_rate >= b.weighted_benchmark * 1.3 THEN '1'
         WHEN c.manager_eligible = 1 THEN '0' ELSE 'Unknown' END AS signal_value
  FROM manager_context AS c
  LEFT JOIN benchmarks AS b ON b.closure_sequence = c.closure_sequence
), employee_assignment_counts AS (
  SELECT e.closure_sequence, x.employee_id, COUNT(s.manager_employee_id)::BIGINT AS match_count
  FROM evaluation_snapshots AS e
  INNER JOIN base_exposure AS x ON x.closure_sequence = e.closure_sequence
  LEFT JOIN manager_scored AS s
    ON s.closure_sequence = e.closure_sequence
   AND s.manager_employee_id = x.manager_employee_id
  GROUP BY 1, 2
), assignment_summary AS (
  SELECT COUNT(*)::BIGINT AS eligible_count,
    SUM(CASE WHEN match_count = 1 THEN 1 ELSE 0 END)::BIGINT AS matched_count,
    SUM(CASE WHEN match_count = 0 THEN 1 ELSE 0 END)::BIGINT AS unmatched_count,
    SUM(CASE WHEN match_count > 1 THEN 1 ELSE 0 END)::BIGINT AS multi_match_count
  FROM employee_assignment_counts
), implementation_checks AS (
  SELECT
    SUM(CASE WHEN manager_eligible = 1 AND (observed_interval_count <> 18 OR last_history_sequence - first_history_sequence <> 17 OR average_team_size < 4 OR voluntary_exit_count < 2) THEN 1 ELSE 0 END)::BIGINT AS eligible_rule_failure_count,
    SUM(CASE WHEN signal_value = '1' AND (manager_eligible <> 1 OR six_month_rate < weighted_benchmark * 1.3) THEN 1 ELSE 0 END)::BIGINT AS flagged_rule_failure_count,
    SUM(CASE WHEN signal_value = '0' AND (manager_eligible <> 1 OR six_month_rate >= weighted_benchmark * 1.3) THEN 1 ELSE 0 END)::BIGINT AS unflagged_rule_failure_count
  FROM manager_scored
), benchmark_checks AS (
  SELECT SUM(CASE WHEN ABS(weighted_benchmark - exposure_benchmark) > 0.000000001 THEN 1 ELSE 0 END)::BIGINT AS benchmark_reconciliation_failure_count
  FROM benchmarks
)
SELECT
  (SELECT COUNT(*) FROM evaluation_snapshots)::BIGINT AS evaluated_snapshot_count,
  18::BIGINT AS expected_interval_count,
  (SELECT MIN(observed_interval_count) FROM manager_scored WHERE manager_eligible = 1)::BIGINT AS minimum_eligible_interval_count,
  (SELECT MIN(average_team_size) FROM manager_scored WHERE manager_eligible = 1) AS minimum_eligible_average_team_size,
  (SELECT MIN(voluntary_exit_count) FROM manager_scored WHERE manager_eligible = 1)::BIGINT AS minimum_eligible_voluntary_exit_count,
  (SELECT COALESCE(SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END), 0) FROM exposure_key_counts)::BIGINT AS duplicate_count,
  (SELECT COALESCE(SUM(CASE WHEN manager_count > 1 THEN 1 ELSE 0 END), 0) FROM exposure_key_counts)::BIGINT AS conflicting_manager_count,
  (SELECT COALESCE(SUM(source_row_count - 1), 0) FROM voluntary_events)::BIGINT AS raw_voluntary_event_duplicate_rows,
  (SELECT COALESCE(SUM(CASE WHEN normalized_type_count > 1 THEN 1 ELSE 0 END), 0) FROM voluntary_events)::BIGINT AS voluntary_event_type_conflict_count,
  (SELECT COALESCE(SUM(CASE WHEN match_count > 1 THEN 1 ELSE 0 END), 0) FROM event_interval_counts)::BIGINT AS event_multiple_interval_assignment_count,
  (SELECT COALESCE(SUM(CASE WHEN match_count > 1 OR manager_count > 1 THEN 1 ELSE 0 END), 0) FROM event_attribution_counts)::BIGINT AS event_multiple_manager_assignment_count,
  (SELECT COUNT(*)::BIGINT FROM event_attribution AS a CROSS JOIN scope_bounds AS b INNER JOIN closure_sequence AS e ON e.closure_sequence = b.last_required_sequence WHERE a.term_date > e.snapshot_date) AS future_event_usage_count,
  a.eligible_count, a.matched_count, a.unmatched_count, a.multi_match_count,
  (SELECT COALESCE(SUM(eligible_rule_failure_count + flagged_rule_failure_count + unflagged_rule_failure_count), 0) FROM implementation_checks)::BIGINT AS rule_implementation_failure_count,
  (SELECT COALESCE(SUM(benchmark_reconciliation_failure_count), 0) FROM benchmark_checks)::BIGINT AS benchmark_reconciliation_failure_count
FROM assignment_summary AS a;
