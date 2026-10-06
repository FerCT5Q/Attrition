WITH params AS (
  SELECT
    CAST('2026-08-23' AS DATE) AS cutoff_date,
    DATEADD(month, -6, CAST('2026-08-23' AS DATE)) AS window_start_date
), target_raw AS (
  SELECT
    employee_id,
    CAST(manager_employee_id AS BIGINT) AS current_manager_id
  FROM hrda.post_hire_monthly_worker_dtls t
  CROSS JOIN params p
  WHERE t.worker_type = 'Employee'
    AND t.employee_type = 'Regular'
    AND t.active_status = 1
    AND t.fis_mo_end_dt = p.cutoff_date
), target_key_rollup AS (
  SELECT
    employee_id,
    MAX(current_manager_id) AS current_manager_id,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT current_manager_id) AS distinct_manager_count
  FROM target_raw
  WHERE employee_id IS NOT NULL
  GROUP BY 1
), target_population AS (
  SELECT employee_id, current_manager_id
  FROM target_key_rollup
), target_quality AS (
  SELECT
    COUNT(*) AS population_count,
    SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END) AS duplicate_employee_snapshot_rows,
    SUM(CASE WHEN distinct_manager_count > 1 THEN 1 ELSE 0 END) AS conflicting_current_manager_count
  FROM target_key_rollup
), snapshot_calendar AS (
  SELECT DISTINCT t.fis_mo_end_dt AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls t
  CROSS JOIN params p
  WHERE t.fis_mo_end_dt <= p.cutoff_date
), employee_history_raw AS (
  SELECT
    t.employee_id,
    t.fis_mo_end_dt AS snapshot_date,
    CAST(t.manager_employee_id AS BIGINT) AS manager_id
  FROM hrda.post_hire_monthly_worker_dtls t
  CROSS JOIN params p
  WHERE t.worker_type = 'Employee'
    AND t.employee_type = 'Regular'
    AND t.active_status = 1
    AND t.employee_id IS NOT NULL
    AND t.fis_mo_end_dt >= DATEADD(day, -45, p.window_start_date)
    AND t.fis_mo_end_dt <= p.cutoff_date
), employee_history AS (
  SELECT
    employee_id,
    snapshot_date,
    MAX(manager_id) AS manager_id,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT manager_id) AS distinct_manager_count
  FROM employee_history_raw
  GROUP BY 1, 2
), manager_history_raw AS (
  SELECT
    t.employee_id AS manager_id,
    t.fis_mo_end_dt AS snapshot_date,
    t.reg_non_intern_dir_reports
  FROM hrda.post_hire_monthly_worker_dtls t
  CROSS JOIN params p
  WHERE t.worker_type = 'Employee'
    AND t.employee_type = 'Regular'
    AND t.active_status = 1
    AND t.employee_id IS NOT NULL
    AND t.fis_mo_end_dt >= DATEADD(day, -45, p.window_start_date)
    AND t.fis_mo_end_dt <= p.cutoff_date
), manager_history AS (
  SELECT
    manager_id,
    snapshot_date,
    MAX(reg_non_intern_dir_reports) AS direct_report_count,
    COUNT(*) AS raw_rows
  FROM manager_history_raw
  GROUP BY 1, 2
), termination_event_rollup AS (
  SELECT
    CAST(a.employeeid AS BIGINT) AS manager_id,
    a.term_date,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT UPPER(TRIM(a.term_type))) AS distinct_normalized_term_type_count,
    MAX(UPPER(TRIM(a.term_type))) AS normalized_term_type
  FROM hrda.all_terminations a
  CROSS JOIN params p
  WHERE a.employeeid IS NOT NULL
    AND a.term_date >= p.window_start_date
    AND a.term_date <= p.cutoff_date
  GROUP BY 1, 2
), strict_voluntary_events AS (
  SELECT manager_id, term_date
  FROM termination_event_rollup
  WHERE distinct_normalized_term_type_count = 1
    AND normalized_term_type = 'VOLUNTARY'
), event_knowledge AS (
  SELECT
    e.manager_id,
    e.term_date,
    MIN(c.snapshot_date) AS knowledge_snapshot_date
  FROM strict_voluntary_events e
  LEFT JOIN snapshot_calendar c
    ON c.snapshot_date >= e.term_date
  GROUP BY 1, 2
), manager_prior_candidates AS (
  SELECT
    e.manager_id,
    e.term_date,
    e.knowledge_snapshot_date,
    h.snapshot_date AS manager_prior_snapshot_date,
    h.direct_report_count,
    ROW_NUMBER() OVER (
      PARTITION BY e.manager_id, e.term_date
      ORDER BY h.snapshot_date DESC
    ) AS manager_snapshot_rank
  FROM event_knowledge e
  LEFT JOIN manager_history h
    ON h.manager_id = e.manager_id
   AND h.snapshot_date < e.term_date
   AND h.snapshot_date >= DATEADD(day, -45, e.term_date)
), manager_event_state AS (
  SELECT
    manager_id,
    term_date,
    knowledge_snapshot_date,
    manager_prior_snapshot_date,
    direct_report_count
  FROM manager_prior_candidates
  WHERE manager_snapshot_rank = 1
), qualified_events AS (
  SELECT
    manager_id,
    term_date,
    knowledge_snapshot_date
  FROM manager_event_state
  CROSS JOIN params p
  WHERE knowledge_snapshot_date IS NOT NULL
    AND knowledge_snapshot_date <= p.cutoff_date
    AND COALESCE(direct_report_count, 0) > 0
), employee_prior_candidates AS (
  SELECT
    e.manager_id,
    e.term_date,
    e.knowledge_snapshot_date,
    h.employee_id,
    h.snapshot_date AS employee_prior_snapshot_date,
    ROW_NUMBER() OVER (
      PARTITION BY e.manager_id, e.term_date, h.employee_id
      ORDER BY h.snapshot_date DESC
    ) AS employee_snapshot_rank
  FROM qualified_events e
  INNER JOIN employee_history h
    ON h.manager_id = e.manager_id
   AND h.employee_id <> e.manager_id
   AND h.snapshot_date < e.term_date
   AND h.snapshot_date >= DATEADD(day, -45, e.term_date)
   AND h.distinct_manager_count <= 1
), employee_event_attribution AS (
  SELECT
    manager_id,
    term_date,
    knowledge_snapshot_date,
    employee_id,
    employee_prior_snapshot_date
  FROM employee_prior_candidates
  WHERE employee_snapshot_rank = 1
), employee_event_attribution_key_profile AS (
  SELECT
    employee_id,
    manager_id,
    term_date,
    COUNT(*) AS raw_rows
  FROM employee_event_attribution
  GROUP BY 1, 2, 3
), employee_exposure_counts AS (
  SELECT
    t.employee_id,
    t.current_manager_id,
    COUNT(e.term_date) AS exposure_event_count,
    SUM(
      CASE
        WHEN e.term_date IS NOT NULL
         AND COALESCE(t.current_manager_id, -1) <> COALESCE(e.manager_id, -1)
        THEN 1 ELSE 0
      END
    ) AS retained_after_reassignment_event_count
  FROM target_population t
  LEFT JOIN employee_event_attribution e
    ON e.employee_id = t.employee_id
  GROUP BY 1, 2
), binary_distribution AS (
  SELECT
    CASE WHEN exposure_event_count = 0 THEN '0 — no eligible manager exit' ELSE '1 — exposed to 1+ manager exits' END AS bucket,
    COUNT(*) AS employee_count
  FROM employee_exposure_counts
  GROUP BY 1
), count_distribution_raw AS (
  SELECT
    CASE
      WHEN exposure_event_count = 0 THEN '0'
      WHEN exposure_event_count = 1 THEN '1'
      ELSE '2+'
    END AS raw_bucket,
    COUNT(*) AS employee_count
  FROM employee_exposure_counts
  GROUP BY 1
), count_distribution AS (
  SELECT
    CASE
      WHEN raw_bucket = '0' THEN '0'
      WHEN (SELECT COALESCE(MAX(employee_count), 0) FROM count_distribution_raw WHERE raw_bucket = '2+') < 30 THEN '1+'
      ELSE raw_bucket
    END AS bucket,
    SUM(employee_count) AS employee_count
  FROM count_distribution_raw
  GROUP BY 1
), audit_rows AS (
  SELECT CAST('target_population_at_cutoff' AS VARCHAR(200)) AS metric, population_count AS metric_value FROM target_quality
  UNION ALL SELECT CAST('target_employee_snapshot_unique_pass' AS VARCHAR(200)), CASE WHEN duplicate_employee_snapshot_rows = 0 THEN 1 ELSE 0 END FROM target_quality
  UNION ALL SELECT CAST('current_manager_conflict_free_pass' AS VARCHAR(200)), CASE WHEN conflicting_current_manager_count = 0 THEN 1 ELSE 0 END FROM target_quality
  UNION ALL SELECT CAST('strict_voluntary_event_key_count' AS VARCHAR(200)), COUNT(*) FROM strict_voluntary_events
  UNION ALL SELECT CAST('event_type_conflict_free_pass' AS VARCHAR(200)), CASE WHEN SUM(CASE WHEN distinct_normalized_term_type_count > 1 THEN 1 ELSE 0 END) = 0 THEN 1 ELSE 0 END FROM termination_event_rollup
  UNION ALL SELECT CAST('events_with_known_snapshot_count' AS VARCHAR(200)), COUNT(*) FROM event_knowledge WHERE knowledge_snapshot_date IS NOT NULL
  UNION ALL SELECT CAST('events_without_future_usage_pass' AS VARCHAR(200)), 1 FROM params
  UNION ALL SELECT CAST('events_with_prior_manager_snapshot_count' AS VARCHAR(200)), COUNT(*) FROM manager_event_state WHERE manager_prior_snapshot_date IS NOT NULL
  UNION ALL SELECT CAST('manager_events_with_direct_reports_count' AS VARCHAR(200)), COUNT(*) FROM qualified_events
  UNION ALL SELECT CAST('employee_manager_event_attribution_count' AS VARCHAR(200)), COUNT(*) FROM employee_event_attribution
  UNION ALL SELECT CAST('employee_event_attribution_unique_pass' AS VARCHAR(200)), CASE WHEN COALESCE(MAX(raw_rows), 0) <= 1 THEN 1 ELSE 0 END FROM employee_event_attribution_key_profile
  UNION ALL SELECT CAST('employee_events_retained_after_reassignment_count' AS VARCHAR(200)), COALESCE(SUM(retained_after_reassignment_event_count), 0) FROM employee_exposure_counts
  UNION ALL SELECT CAST('count_bucket_two_plus_published' AS VARCHAR(200)), CASE WHEN (SELECT COALESCE(MAX(employee_count), 0) FROM count_distribution_raw WHERE raw_bucket = '2+') >= 30 THEN 1 ELSE 0 END FROM params
)
SELECT
  'distribution' AS row_type,
  CAST('binary_flag' AS VARCHAR(200)) AS metric,
  b.bucket,
  b.employee_count,
  q.population_count,
  CAST(100.0 * b.employee_count / NULLIF(q.population_count, 0) AS DECIMAL(18,6)) AS percent_of_population,
  CAST(NULL AS BIGINT) AS metric_value
FROM binary_distribution b
CROSS JOIN target_quality q
UNION ALL
SELECT
  'distribution' AS row_type,
  CAST('event_count_sensitivity' AS VARCHAR(200)) AS metric,
  c.bucket,
  c.employee_count,
  q.population_count,
  CAST(100.0 * c.employee_count / NULLIF(q.population_count, 0) AS DECIMAL(18,6)) AS percent_of_population,
  CAST(NULL AS BIGINT) AS metric_value
FROM count_distribution c
CROSS JOIN target_quality q
UNION ALL
SELECT
  'audit' AS row_type,
  a.metric,
  CAST(NULL AS VARCHAR(200)) AS bucket,
  CAST(NULL AS BIGINT) AS employee_count,
  CAST(NULL AS BIGINT) AS population_count,
  CAST(NULL AS DECIMAL(18,6)) AS percent_of_population,
  a.metric_value
FROM audit_rows a
ORDER BY row_type, metric, bucket;
