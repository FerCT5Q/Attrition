-- Claim: High risk manager is a continuous, time-safe six-fiscal-interval
-- observed/expected score at the latest complete close. It is an aggregate
-- contextual signal, not an individual performance label.
--
-- Each voluntary exit is placed in exactly one of the six intervals and uses
-- the employee's exposure, manager, and controls at that interval's start.
-- Expected exits control for interval, region, job family, job level, and
-- time-safe tenure band. Strata below 30 employee-intervals fall back to the
-- interval global rate; a 60 employee-interval prior smooths the ratio to one.
-- Results are aggregate-only and contain no manager or employee identifiers.

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
parameters AS (
  SELECT 30 AS minimum_stratum_exposure,
    60.0::DECIMAL(20,8) AS smoothing_employee_intervals
),
window_bounds AS (
  SELECT MIN(interval_start) AS window_start_exclusive,
    MAX(interval_end) AS cutoff_date,
    COUNT(*) AS interval_count
  FROM intervals
),
exposure_raw AS (
  SELECT i.interval_sequence, i.interval_start, i.interval_end,
    w.employee_id, w.manager_employee_id,
    COALESCE(NULLIF(TRIM(CAST(w.region AS VARCHAR(256))), ''), 'Unknown') AS region,
    COALESCE(NULLIF(TRIM(CAST(w.job_family AS VARCHAR(256))), ''), 'Unknown') AS job_family,
    COALESCE(NULLIF(TRIM(CAST(w.job_level_primary_position AS VARCHAR(256))), ''), 'Unknown') AS job_level,
    CASE
      WHEN COALESCE(
        CASE WHEN w.max_hire_rehire_date <= w.fis_mo_end_dt THEN w.max_hire_rehire_date END,
        CASE WHEN w.service_date <= w.fis_mo_end_dt THEN w.service_date END,
        CASE WHEN w.original_hire_date <= w.fis_mo_end_dt THEN w.original_hire_date END
      ) IS NULL THEN 'Unknown'
      WHEN DATEDIFF(month, COALESCE(
        CASE WHEN w.max_hire_rehire_date <= w.fis_mo_end_dt THEN w.max_hire_rehire_date END,
        CASE WHEN w.service_date <= w.fis_mo_end_dt THEN w.service_date END,
        CASE WHEN w.original_hire_date <= w.fis_mo_end_dt THEN w.original_hire_date END
      ), w.fis_mo_end_dt) < 12 THEN '<1 year'
      WHEN DATEDIFF(month, COALESCE(
        CASE WHEN w.max_hire_rehire_date <= w.fis_mo_end_dt THEN w.max_hire_rehire_date END,
        CASE WHEN w.service_date <= w.fis_mo_end_dt THEN w.service_date END,
        CASE WHEN w.original_hire_date <= w.fis_mo_end_dt THEN w.original_hire_date END
      ), w.fis_mo_end_dt) < 24 THEN '1-<2 years'
      WHEN DATEDIFF(month, COALESCE(
        CASE WHEN w.max_hire_rehire_date <= w.fis_mo_end_dt THEN w.max_hire_rehire_date END,
        CASE WHEN w.service_date <= w.fis_mo_end_dt THEN w.service_date END,
        CASE WHEN w.original_hire_date <= w.fis_mo_end_dt THEN w.original_hire_date END
      ), w.fis_mo_end_dt) < 60 THEN '2-<5 years'
      ELSE '5+ years'
    END AS tenure_band
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
    manager_employee_id, region, job_family, job_level, tenure_band
  FROM (
    SELECT e.interval_sequence, e.interval_start, e.interval_end, e.employee_id,
      e.manager_employee_id, e.region, e.job_family, e.job_level, e.tenure_band,
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
    i.interval_sequence
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
    x.manager_employee_id, x.region, x.job_family, x.job_level, x.tenure_band
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
exposure_by_stratum AS (
  SELECT interval_sequence, region, job_family, job_level, tenure_band,
    COUNT(*) AS employee_intervals
  FROM exposure
  GROUP BY 1, 2, 3, 4, 5
),
events_by_stratum AS (
  SELECT interval_sequence, region, job_family, job_level, tenure_band,
    COUNT(*) AS voluntary_events
  FROM event_attributions
  GROUP BY 1, 2, 3, 4, 5
),
global_rates AS (
  SELECT x.interval_sequence, x.employee_intervals,
    COALESCE(e.voluntary_events, 0) AS voluntary_events,
    COALESCE(e.voluntary_events, 0)::DECIMAL(20,10)
      / NULLIF(x.employee_intervals, 0) AS global_rate
  FROM (
    SELECT interval_sequence, COUNT(*) AS employee_intervals
    FROM exposure
    GROUP BY 1
  ) AS x
  LEFT JOIN (
    SELECT interval_sequence, COUNT(*) AS voluntary_events
    FROM event_attributions
    GROUP BY 1
  ) AS e ON e.interval_sequence = x.interval_sequence
),
stratum_rates AS (
  SELECT x.interval_sequence, x.region, x.job_family, x.job_level, x.tenure_band,
    x.employee_intervals, COALESCE(e.voluntary_events, 0) AS voluntary_events,
    g.global_rate,
    CASE WHEN x.employee_intervals >= p.minimum_stratum_exposure
      THEN COALESCE(e.voluntary_events, 0)::DECIMAL(20,10)
           / NULLIF(x.employee_intervals, 0)
      ELSE g.global_rate END AS applied_rate,
    CASE WHEN x.employee_intervals >= p.minimum_stratum_exposure THEN 0 ELSE 1 END AS global_fallback_used
  FROM exposure_by_stratum AS x
  INNER JOIN global_rates AS g ON g.interval_sequence = x.interval_sequence
  CROSS JOIN parameters AS p
  LEFT JOIN events_by_stratum AS e
    ON e.interval_sequence = x.interval_sequence
   AND e.region = x.region
   AND e.job_family = x.job_family
   AND e.job_level = x.job_level
   AND e.tenure_band = x.tenure_band
),
manager_stratum_exposure AS (
  SELECT interval_sequence, manager_employee_id, region, job_family, job_level,
    tenure_band, COUNT(*) AS employee_intervals
  FROM exposure
  GROUP BY 1, 2, 3, 4, 5, 6
),
manager_expected AS (
  SELECT m.manager_employee_id,
    SUM(m.employee_intervals) AS employee_intervals,
    SUM(m.employee_intervals * r.applied_rate) AS expected_voluntary_exits,
    SUM(CASE WHEN r.global_fallback_used = 1 THEN m.employee_intervals ELSE 0 END) AS fallback_employee_intervals
  FROM manager_stratum_exposure AS m
  INNER JOIN stratum_rates AS r
    ON r.interval_sequence = m.interval_sequence
   AND r.region = m.region
   AND r.job_family = m.job_family
   AND r.job_level = m.job_level
   AND r.tenure_band = m.tenure_band
  GROUP BY 1
),
manager_observed AS (
  SELECT manager_employee_id, COUNT(*) AS observed_voluntary_exits
  FROM event_attributions
  GROUP BY 1
),
global_prior AS (
  SELECT SUM(voluntary_events)::DECIMAL(20,10)
      / NULLIF(SUM(employee_intervals), 0) AS global_rate,
    SUM(voluntary_events) AS global_voluntary_event_count,
    SUM(employee_intervals) AS global_employee_intervals
  FROM global_rates
),
manager_scores AS (
  SELECT t.manager_employee_id, t.current_direct_reports,
    e.employee_intervals, e.expected_voluntary_exits,
    e.fallback_employee_intervals,
    COALESCE(o.observed_voluntary_exits, 0) AS observed_voluntary_exits,
    CASE
      WHEN e.employee_intervals IS NULL OR e.employee_intervals = 0
        OR e.expected_voluntary_exits IS NULL
        OR g.global_rate IS NULL OR g.global_rate <= 0
      THEN NULL
      ELSE (COALESCE(o.observed_voluntary_exits, 0)
            + p.smoothing_employee_intervals * g.global_rate)
          / NULLIF(e.expected_voluntary_exits
            + p.smoothing_employee_intervals * g.global_rate, 0)
    END AS smoothed_excess_ratio
  FROM current_teams AS t
  LEFT JOIN manager_expected AS e ON e.manager_employee_id = t.manager_employee_id
  LEFT JOIN manager_observed AS o ON o.manager_employee_id = t.manager_employee_id
  CROSS JOIN global_prior AS g
  CROSS JOIN parameters AS p
),
scored_managers AS (
  SELECT manager_employee_id, current_direct_reports, employee_intervals,
    expected_voluntary_exits, fallback_employee_intervals,
    observed_voluntary_exits, smoothed_excess_ratio,
    CASE WHEN smoothed_excess_ratio < 0.50 THEN '<0.50×'
      WHEN smoothed_excess_ratio < 1.00 THEN '0.50–<1.00×'
      WHEN smoothed_excess_ratio < 1.50 THEN '1.00–<1.50×'
      ELSE '≥1.50×' END AS score_band
  FROM manager_scores
  WHERE smoothed_excess_ratio IS NOT NULL
),
score_band_summary AS (
  SELECT score_band, COUNT(*) AS manager_count,
    SUM(current_direct_reports) AS employee_count,
    CAST(AVG(smoothed_excess_ratio) AS VARCHAR(32)) AS mean_smoothed_excess_ratio
  FROM scored_managers
  GROUP BY 1
),
score_band_reconciliation AS (
  SELECT COALESCE(SUM(manager_count), 0) AS banded_manager_count,
    COALESCE(SUM(employee_count), 0) AS banded_employee_count
  FROM score_band_summary
),
score_key_counts AS (
  SELECT manager_employee_id, COUNT(*) AS score_row_count
  FROM scored_managers
  GROUP BY 1
),
assignment_match_counts AS (
  SELECT m.employee_id, COUNT(*) AS assignment_match_count
  FROM current_members AS m
  LEFT JOIN manager_scores AS s ON s.manager_employee_id = m.manager_employee_id
  GROUP BY 1
),
assignment_summary AS (
  SELECT
    COUNT(*) AS current_manager_count,
    SUM(current_direct_reports) AS employees_with_current_manager,
    SUM(CASE WHEN smoothed_excess_ratio IS NOT NULL THEN 1 ELSE 0 END) AS scored_manager_count,
    COALESCE(SUM(CASE WHEN smoothed_excess_ratio IS NOT NULL THEN current_direct_reports ELSE 0 END), 0) AS employees_with_scored_manager,
    SUM(CASE WHEN smoothed_excess_ratio IS NULL THEN 1 ELSE 0 END) AS unknown_manager_count,
    COALESCE(SUM(CASE WHEN smoothed_excess_ratio IS NULL THEN current_direct_reports ELSE 0 END), 0) AS employees_unknown_history_count
  FROM manager_scores
),
audit_rows AS (
  SELECT 'audit' AS row_type, CAST(NULL AS INTEGER) AS interval_sequence,
    CAST(NULL AS DATE) AS interval_start, CAST(NULL AS DATE) AS interval_end,
    CAST(NULL AS VARCHAR(32)) AS score_band, CAST(NULL AS BIGINT) AS manager_count,
    CAST(NULL AS BIGINT) AS employee_count,
    CAST(NULL AS VARCHAR(32)) AS mean_smoothed_excess_ratio,
    'interval_count' AS metric, interval_count::DECIMAL(20,6) AS metric_value
  FROM window_bounds
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'closure_count', (interval_count + 1)::DECIMAL(20,6) FROM window_bounds
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'interval_overlap_or_gap_count', COALESCE(SUM(CASE WHEN prior_end <> interval_start THEN 1 ELSE 0 END), 0)::DECIMAL(20,6)
  FROM (
    SELECT interval_start, LAG(interval_end) OVER (ORDER BY interval_sequence) AS prior_end
    FROM intervals
  ) AS continuity
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'exposure_duplicate_rows', COALESCE(SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END), 0)::DECIMAL(20,6)
  FROM exposure_key_counts
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'current_member_duplicate_rows', COALESCE(SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END), 0)::DECIMAL(20,6)
  FROM current_member_key_counts
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'raw_event_duplicate_rows', COALESCE(SUM(source_row_count - 1), 0)::DECIMAL(20,6)
  FROM voluntary_event_sources
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'deduplicated_event_duplicate_count', 0.0::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'unique_voluntary_event_count', (SELECT COUNT(*) FROM voluntary_event_sources)::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'unique_attributed_event_count', COALESCE((SELECT COUNT(*) FROM event_attribution_key_counts WHERE attribution_match_count = 1), 0)::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'events_without_unique_interval', (SELECT COUNT(*) FROM voluntary_event_sources)::DECIMAL(20,6) - COALESCE((SELECT COUNT(*) FROM event_interval_key_counts WHERE interval_match_count = 1), 0)::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'events_with_multiple_intervals', COALESCE((SELECT COUNT(*) FROM event_interval_key_counts WHERE interval_match_count > 1), 0)::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'events_without_unique_exposure_attribution', (SELECT COUNT(*) FROM voluntary_event_sources)::DECIMAL(20,6) - COALESCE((SELECT COUNT(*) FROM event_attribution_key_counts WHERE attribution_match_count = 1), 0)::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'events_with_multiple_exposure_attributions', COALESCE((SELECT COUNT(*) FROM event_attribution_key_counts WHERE attribution_match_count > 1), 0)::DECIMAL(20,6)
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'global_voluntary_event_count', global_voluntary_event_count::DECIMAL(20,6) FROM global_prior
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'global_employee_intervals', global_employee_intervals::DECIMAL(20,6) FROM global_prior
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'global_rate_positive', CASE WHEN global_rate > 0 THEN 1 ELSE 0 END::DECIMAL(20,6) FROM global_prior
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'score_manager_duplicate_count', COALESCE(SUM(CASE WHEN score_row_count > 1 THEN 1 ELSE 0 END), 0)::DECIMAL(20,6) FROM score_key_counts
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'score_band_manager_reconciliation_failure', CASE WHEN b.banded_manager_count = s.scored_manager_count THEN 0 ELSE 1 END::DECIMAL(20,6)
  FROM score_band_reconciliation AS b CROSS JOIN assignment_summary AS s
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'score_band_employee_reconciliation_failure', CASE WHEN b.banded_employee_count = s.employees_with_scored_manager THEN 0 ELSE 1 END::DECIMAL(20,6)
  FROM score_band_reconciliation AS b CROSS JOIN assignment_summary AS s
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'employees_scored_exceed_current_manager_population', CASE WHEN employees_with_scored_manager <= employees_with_current_manager THEN 0 ELSE 1 END::DECIMAL(20,6)
  FROM assignment_summary
  UNION ALL SELECT 'audit', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'employee_score_multi_match_count', COALESCE(SUM(CASE WHEN assignment_match_count > 1 THEN 1 ELSE 0 END), 0)::DECIMAL(20,6)
  FROM assignment_match_counts
),
summary_rows AS (
  SELECT 'summary' AS row_type, CAST(NULL AS INTEGER) AS interval_sequence,
    CAST(NULL AS DATE) AS interval_start, CAST(NULL AS DATE) AS interval_end,
    CAST(NULL AS VARCHAR(32)) AS score_band, CAST(NULL AS BIGINT) AS manager_count,
    CAST(NULL AS BIGINT) AS employee_count, CAST(NULL AS VARCHAR(32)) AS mean_smoothed_excess_ratio,
    'current_manager_count' AS metric, current_manager_count::DECIMAL(20,6) AS metric_value FROM assignment_summary
  UNION ALL SELECT 'summary', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'employees_with_current_manager', employees_with_current_manager::DECIMAL(20,6) FROM assignment_summary
  UNION ALL SELECT 'summary', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'scored_manager_count', scored_manager_count::DECIMAL(20,6) FROM assignment_summary
  UNION ALL SELECT 'summary', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'employees_with_scored_manager', employees_with_scored_manager::DECIMAL(20,6) FROM assignment_summary
  UNION ALL SELECT 'summary', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'unknown_manager_count', unknown_manager_count::DECIMAL(20,6) FROM assignment_summary
  UNION ALL SELECT 'summary', NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'employees_unknown_history_count', employees_unknown_history_count::DECIMAL(20,6) FROM assignment_summary
)
SELECT 'interval' AS row_type, interval_sequence, interval_start, interval_end,
  CAST(NULL AS VARCHAR(32)) AS score_band, CAST(NULL AS BIGINT) AS manager_count,
  CAST(NULL AS BIGINT) AS employee_count, CAST(NULL AS VARCHAR(32)) AS mean_smoothed_excess_ratio,
  CAST(NULL AS VARCHAR(128)) AS metric, CAST(NULL AS DECIMAL(20,6)) AS metric_value
FROM intervals
UNION ALL
SELECT 'score_band', NULL, NULL, NULL, score_band, manager_count, employee_count,
  mean_smoothed_excess_ratio, CAST(NULL AS VARCHAR(128)), CAST(NULL AS DECIMAL(20,6))
FROM score_band_summary
UNION ALL
SELECT row_type, interval_sequence, interval_start, interval_end, score_band,
  manager_count, employee_count, mean_smoothed_excess_ratio, metric, metric_value
FROM summary_rows
UNION ALL
SELECT row_type, interval_sequence, interval_start, interval_end, score_band,
  manager_count, employee_count, mean_smoothed_excess_ratio, metric, metric_value
FROM audit_rows
ORDER BY row_type, interval_sequence, score_band, metric;
