-- Claim: at the latest complete fiscal close, High turnover under this person
-- is a time-safe descriptive flag. A current manager's active regular direct
-- reports are assigned to 0, 1, or 2+ strict-Voluntary exits attributable to
-- that manager over the six complete fiscal intervals immediately before the
-- latest close. No manager without historical exposure is placed in bucket 0.
--
-- Reporting mode: presentation. Results are aggregate-only and do not expose
-- employee or manager identifiers. This query obtains its seven boundary
-- snapshots from the source rather than subtracting calendar months.

WITH closure_dates AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  GROUP BY 1
),
last_seven_closures AS (
  SELECT snapshot_date
  FROM (
    SELECT snapshot_date,
      ROW_NUMBER() OVER (ORDER BY snapshot_date DESC) AS reverse_sequence
    FROM closure_dates
  ) AS ranked
  WHERE reverse_sequence <= 7
),
interval_candidates AS (
  SELECT snapshot_date AS interval_end,
    LAG(snapshot_date) OVER (ORDER BY snapshot_date) AS interval_start
  FROM last_seven_closures
),
intervals AS (
  SELECT ROW_NUMBER() OVER (ORDER BY interval_end) AS interval_sequence,
    interval_start, interval_end
  FROM interval_candidates
  WHERE interval_start IS NOT NULL
),
window_bounds AS (
  SELECT MIN(interval_start) AS window_start_exclusive,
    MAX(interval_end) AS cutoff_date,
    COUNT(*) AS interval_count
  FROM intervals
),
exposure_raw AS (
  SELECT i.interval_sequence, i.interval_start, i.interval_end,
    w.employee_id, w.manager_employee_id
  FROM intervals AS i
  INNER JOIN hrda.post_hire_monthly_worker_dtls AS w
    ON CAST(w.fis_mo_end_dt AS DATE) = i.interval_start
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.manager_employee_id IS NOT NULL
),
exposure_key_counts AS (
  SELECT interval_sequence, employee_id, COUNT(*) AS row_count
  FROM exposure_raw
  GROUP BY 1, 2
),
exposure AS (
  SELECT interval_sequence, interval_start, interval_end, employee_id,
    manager_employee_id
  FROM (
    SELECT e.interval_sequence, e.interval_start, e.interval_end, e.employee_id,
      e.manager_employee_id,
      ROW_NUMBER() OVER (
        PARTITION BY e.interval_sequence, e.employee_id
        ORDER BY e.manager_employee_id
      ) AS row_rank
    FROM exposure_raw AS e
  ) AS deduplicated
  WHERE row_rank = 1
),
current_members_raw AS (
  SELECT w.employee_id, w.manager_employee_id
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN window_bounds AS b
  WHERE CAST(w.fis_mo_end_dt AS DATE) = b.cutoff_date
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.manager_employee_id IS NOT NULL
),
current_member_key_counts AS (
  SELECT employee_id, COUNT(*) AS row_count
  FROM current_members_raw
  GROUP BY 1
),
current_members AS (
  SELECT employee_id, manager_employee_id
  FROM (
    SELECT m.employee_id, m.manager_employee_id,
      ROW_NUMBER() OVER (
        PARTITION BY m.employee_id ORDER BY m.manager_employee_id
      ) AS row_rank
    FROM current_members_raw AS m
  ) AS deduplicated
  WHERE row_rank = 1
),
current_teams AS (
  SELECT manager_employee_id, COUNT(*) AS current_direct_reports
  FROM current_members
  GROUP BY 1
),
voluntary_event_sources AS (
  SELECT w.employee_id, CAST(w.term_date AS DATE) AS term_date,
    COUNT(*) AS source_row_count
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN window_bounds AS b
  WHERE CAST(w.term_date AS DATE) > b.window_start_exclusive
    AND CAST(w.term_date AS DATE) <= b.cutoff_date
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
  GROUP BY 1, 2
),
event_interval_matches AS (
  SELECT e.employee_id, e.term_date, e.source_row_count,
    i.interval_sequence, i.interval_start, i.interval_end
  FROM voluntary_event_sources AS e
  INNER JOIN intervals AS i
    ON e.term_date > i.interval_start
   AND e.term_date <= i.interval_end
),
event_interval_key_counts AS (
  SELECT employee_id, term_date, COUNT(*) AS interval_match_count
  FROM event_interval_matches
  GROUP BY 1, 2
),
event_attributions AS (
  SELECT e.employee_id, e.term_date, e.interval_sequence,
    x.manager_employee_id
  FROM event_interval_matches AS e
  INNER JOIN exposure AS x
    ON x.interval_sequence = e.interval_sequence
   AND x.employee_id = e.employee_id
),
event_attribution_key_counts AS (
  SELECT employee_id, term_date, COUNT(*) AS attribution_match_count
  FROM event_attributions
  GROUP BY 1, 2
),
manager_history AS (
  SELECT manager_employee_id,
    COUNT(*) AS employee_interval_exposure,
    COUNT(DISTINCT interval_sequence) AS intervals_with_exposure
  FROM exposure
  GROUP BY 1
),
manager_exit_counts AS (
  SELECT manager_employee_id,
    COUNT(*) AS voluntary_exit_count
  FROM event_attributions
  GROUP BY 1
),
manager_context AS (
  SELECT t.manager_employee_id, t.current_direct_reports,
    h.employee_interval_exposure, h.intervals_with_exposure,
    CASE WHEN h.manager_employee_id IS NULL THEN NULL
      ELSE COALESCE(e.voluntary_exit_count, 0) END AS voluntary_exit_count
  FROM current_teams AS t
  LEFT JOIN manager_history AS h ON h.manager_employee_id = t.manager_employee_id
  LEFT JOIN manager_exit_counts AS e ON e.manager_employee_id = t.manager_employee_id
),
bucketed_managers AS (
  SELECT manager_employee_id, current_direct_reports, voluntary_exit_count,
    CASE WHEN voluntary_exit_count >= 2 THEN '2+'
      ELSE CAST(voluntary_exit_count AS VARCHAR(8)) END AS exit_bucket
  FROM manager_context
  WHERE voluntary_exit_count IS NOT NULL
),
bucket_summary AS (
  SELECT exit_bucket,
    COUNT(*) AS manager_count,
    SUM(current_direct_reports) AS employee_count
  FROM bucketed_managers
  GROUP BY 1
),
summary_counts AS (
  SELECT
    COUNT(*) AS current_manager_count,
    SUM(current_direct_reports) AS employees_with_current_manager,
    SUM(CASE WHEN voluntary_exit_count IS NOT NULL THEN 1 ELSE 0 END) AS observable_manager_count,
    COALESCE(SUM(CASE WHEN voluntary_exit_count IS NOT NULL THEN current_direct_reports ELSE 0 END), 0) AS observable_employee_count,
    SUM(CASE WHEN voluntary_exit_count IS NULL THEN 1 ELSE 0 END) AS unknown_manager_count,
    COALESCE(SUM(CASE WHEN voluntary_exit_count IS NULL THEN current_direct_reports ELSE 0 END), 0) AS unknown_employee_count,
    COALESCE(SUM(CASE WHEN voluntary_exit_count >= 2 THEN current_direct_reports ELSE 0 END), 0) AS flagged_employee_count
  FROM manager_context
),
bucket_reconciliation AS (
  SELECT COALESCE(SUM(manager_count), 0) AS bucketed_manager_count,
    COALESCE(SUM(employee_count), 0) AS bucketed_employee_count
  FROM bucket_summary
),
employee_assignment_match_counts AS (
  SELECT m.employee_id, COUNT(*) AS assignment_match_count
  FROM current_members AS m
  LEFT JOIN manager_context AS c
    ON c.manager_employee_id = m.manager_employee_id
  GROUP BY 1
),
audit_rows AS (
  SELECT 'audit' AS row_type, CAST(NULL AS INTEGER) AS interval_sequence,
    CAST(NULL AS DATE) AS interval_start, CAST(NULL AS DATE) AS interval_end,
    CAST(NULL AS VARCHAR(32)) AS exit_bucket, CAST(NULL AS BIGINT) AS manager_count,
    CAST(NULL AS BIGINT) AS employee_count, 'interval_count' AS metric,
    interval_count::DECIMAL(20,6) AS metric_value
  FROM window_bounds
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'closure_count', (interval_count + 1)::DECIMAL(20,6) FROM window_bounds
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'interval_overlap_or_gap_count', COALESCE(SUM(CASE WHEN prior_end <> interval_start THEN 1 ELSE 0 END), 0)::DECIMAL(20,6)
  FROM (
    SELECT interval_start, LAG(interval_end) OVER (ORDER BY interval_sequence) AS prior_end
    FROM intervals
  ) AS continuity
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'exposure_duplicate_rows', COALESCE(SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END), 0)::DECIMAL(20,6)
  FROM exposure_key_counts
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'current_member_duplicate_rows', COALESCE(SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END), 0)::DECIMAL(20,6)
  FROM current_member_key_counts
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'raw_event_duplicate_rows', COALESCE(SUM(source_row_count - 1), 0)::DECIMAL(20,6)
  FROM voluntary_event_sources
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'deduplicated_event_duplicate_count', 0.0::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'unique_voluntary_event_count', (SELECT COUNT(*) FROM voluntary_event_sources)::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'unique_attributed_event_count', COALESCE((SELECT COUNT(*) FROM event_attribution_key_counts WHERE attribution_match_count = 1), 0)::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'events_without_unique_interval', (SELECT COUNT(*) FROM voluntary_event_sources)::DECIMAL(20,6) - COALESCE((SELECT COUNT(*) FROM event_interval_key_counts WHERE interval_match_count = 1), 0)::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'events_with_multiple_intervals', COALESCE((SELECT COUNT(*) FROM event_interval_key_counts WHERE interval_match_count > 1), 0)::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'events_without_unique_exposure_attribution', (SELECT COUNT(*) FROM voluntary_event_sources)::DECIMAL(20,6) - COALESCE((SELECT COUNT(*) FROM event_attribution_key_counts WHERE attribution_match_count = 1), 0)::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'events_with_multiple_exposure_attributions', COALESCE((SELECT COUNT(*) FROM event_attribution_key_counts WHERE attribution_match_count > 1), 0)::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'bucket_manager_reconciliation_failure', CASE WHEN b.bucketed_manager_count = s.observable_manager_count THEN 0 ELSE 1 END::DECIMAL(20,6)
  FROM bucket_reconciliation AS b CROSS JOIN summary_counts AS s
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'bucket_employee_reconciliation_failure', CASE WHEN b.bucketed_employee_count = s.observable_employee_count THEN 0 ELSE 1 END::DECIMAL(20,6)
  FROM bucket_reconciliation AS b CROSS JOIN summary_counts AS s
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'flagged_employee_exceeds_observable', CASE WHEN flagged_employee_count <= observable_employee_count THEN 0 ELSE 1 END::DECIMAL(20,6)
  FROM summary_counts
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL,
    'employee_assignment_multi_match_count', COALESCE(SUM(CASE WHEN assignment_match_count > 1 THEN 1 ELSE 0 END), 0)::DECIMAL(20,6)
  FROM employee_assignment_match_counts
),
summary_rows AS (
  SELECT 'summary' AS row_type, CAST(NULL AS INTEGER) AS interval_sequence,
    CAST(NULL AS DATE) AS interval_start, CAST(NULL AS DATE) AS interval_end,
    CAST(NULL AS VARCHAR(32)) AS exit_bucket, CAST(NULL AS BIGINT) AS manager_count,
    CAST(NULL AS BIGINT) AS employee_count, 'current_manager_count' AS metric,
    current_manager_count::DECIMAL(20,6) AS metric_value FROM summary_counts
  UNION ALL SELECT 'summary', NULL, NULL, NULL, NULL, NULL, NULL,
    'employees_with_current_manager', employees_with_current_manager::DECIMAL(20,6) FROM summary_counts
  UNION ALL SELECT 'summary', NULL, NULL, NULL, NULL, NULL, NULL,
    'observable_manager_count', observable_manager_count::DECIMAL(20,6) FROM summary_counts
  UNION ALL SELECT 'summary', NULL, NULL, NULL, NULL, NULL, NULL,
    'observable_employee_count', observable_employee_count::DECIMAL(20,6) FROM summary_counts
  UNION ALL SELECT 'summary', NULL, NULL, NULL, NULL, NULL, NULL,
    'unknown_manager_count', unknown_manager_count::DECIMAL(20,6) FROM summary_counts
  UNION ALL SELECT 'summary', NULL, NULL, NULL, NULL, NULL, NULL,
    'unknown_employee_count', unknown_employee_count::DECIMAL(20,6) FROM summary_counts
  UNION ALL SELECT 'summary', NULL, NULL, NULL, NULL, NULL, NULL,
    'flagged_employee_count', flagged_employee_count::DECIMAL(20,6) FROM summary_counts
)
SELECT 'interval' AS row_type, interval_sequence, interval_start, interval_end,
  CAST(NULL AS VARCHAR(32)) AS exit_bucket, CAST(NULL AS BIGINT) AS manager_count,
  CAST(NULL AS BIGINT) AS employee_count, CAST(NULL AS VARCHAR(128)) AS metric,
  CAST(NULL AS DECIMAL(20,6)) AS metric_value
FROM intervals
UNION ALL
SELECT 'bucket', NULL, NULL, NULL, exit_bucket, manager_count, employee_count,
  CAST(NULL AS VARCHAR(128)), CAST(NULL AS DECIMAL(20,6))
FROM bucket_summary
UNION ALL
SELECT row_type, interval_sequence, interval_start, interval_end, exit_bucket,
  manager_count, employee_count, metric, metric_value
FROM summary_rows
UNION ALL
SELECT row_type, interval_sequence, interval_start, interval_end, exit_bucket,
  manager_count, employee_count, metric, metric_value
FROM audit_rows
ORDER BY row_type, interval_sequence, exit_bucket, metric;
