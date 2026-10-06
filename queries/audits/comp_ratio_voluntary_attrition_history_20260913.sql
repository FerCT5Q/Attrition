-- Claim: the stored compa_ratio separates historical voluntary-attrition
-- prevalence into two descriptive cohorts at the 0.8 threshold.
--
-- Reporting mode: presentation. This query returns aggregate rows only.
-- Population: active regular employees in monthly snapshots.
-- Grain: employee-snapshot for the calculation; snapshot-month x ratio-group
-- for the published series.
-- Outcome: strict VOLUNTARY term_date in (snapshot_date, snapshot_date + 6m].
-- Grouping: compa_ratio < 0.8 (including zero) versus compa_ratio >= 0.8.
-- The formula/lineage of the stored monthly compa_ratio is not asserted here.

WITH source_bounds AS (
  SELECT
    MIN(CAST(fis_mo_end_dt AS DATE)) AS source_first_snapshot_date,
    MAX(CAST(fis_mo_end_dt AS DATE)) AS source_max_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
), closure_dates AS (
  SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
), complete_snapshots AS (
  SELECT c.snapshot_date
  FROM closure_dates AS c
  CROSS JOIN source_bounds AS b
  WHERE c.snapshot_date <= DATEADD(month, -6, b.source_max_snapshot_date)
), eligible_raw AS (
  SELECT
    CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
    w.employee_id,
    w.compa_ratio
  FROM hrda.post_hire_monthly_worker_dtls AS w
  INNER JOIN complete_snapshots AS c
    ON c.snapshot_date = CAST(w.fis_mo_end_dt AS DATE)
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
), eligible_key_quality AS (
  SELECT
    snapshot_date,
    employee_id,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT compa_ratio) AS distinct_compa_ratio_values
  FROM eligible_raw
  GROUP BY 1, 2
), eligible AS (
  SELECT snapshot_date, employee_id, compa_ratio
  FROM (
    SELECT
      e.snapshot_date,
      e.employee_id,
      e.compa_ratio,
      ROW_NUMBER() OVER (
        PARTITION BY e.snapshot_date, e.employee_id
        ORDER BY CASE WHEN e.compa_ratio IS NULL THEN 1 ELSE 0 END,
                 e.compa_ratio
      ) AS row_rank
    FROM eligible_raw AS e
  ) AS ranked
  WHERE row_rank = 1
), snapshot_summary AS (
  SELECT
    snapshot_date,
    COUNT(*) AS eligible_employee_snapshots,
    COUNT(CASE WHEN compa_ratio IS NOT NULL THEN 1 END) AS ratio_observed_employee_snapshots,
    COUNT(CASE WHEN compa_ratio IS NULL THEN 1 END) AS ratio_missing_employee_snapshots
  FROM eligible
  GROUP BY 1
), ratio_groups AS (
  SELECT
    snapshot_date,
    employee_id,
    compa_ratio,
    CASE
      WHEN compa_ratio < 0.8 THEN '<0.8 (incl. 0)'
      WHEN compa_ratio >= 0.8 THEN '>=0.8'
    END AS group_label
  FROM eligible
  WHERE compa_ratio IS NOT NULL
), termination_raw AS (
  SELECT
    w.employee_id,
    CAST(w.term_date AS DATE) AS term_date,
    UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')) AS normalized_term_type
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN source_bounds AS b
  WHERE w.employee_id IS NOT NULL
    AND w.term_date IS NOT NULL
    AND CAST(w.term_date AS DATE) > (SELECT MIN(snapshot_date) FROM complete_snapshots)
    AND CAST(w.term_date AS DATE) <= b.source_max_snapshot_date
), termination_key_quality AS (
  SELECT
    employee_id,
    term_date,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT normalized_term_type) AS distinct_term_type_count,
    MAX(normalized_term_type) AS normalized_term_type,
    SUM(CASE WHEN normalized_term_type = 'VOLUNTARY' THEN 1 ELSE 0 END) AS voluntary_source_rows,
    SUM(CASE WHEN normalized_term_type = 'VOLUNTARY EXCEPTION' THEN 1 ELSE 0 END) AS voluntary_exception_source_rows
  FROM termination_raw
  GROUP BY 1, 2
), voluntary_events AS (
  SELECT employee_id, term_date
  FROM termination_key_quality
  WHERE distinct_term_type_count = 1
    AND normalized_term_type = 'VOLUNTARY'
), series_counts AS (
  SELECT
    g.snapshot_date,
    g.group_label,
    COUNT(DISTINCT g.employee_id) AS employee_snapshots,
    COUNT(DISTINCT CASE WHEN e.employee_id IS NOT NULL THEN g.employee_id END) AS voluntary_exit_snapshots
  FROM ratio_groups AS g
  LEFT JOIN voluntary_events AS e
    ON e.employee_id = g.employee_id
   AND e.term_date > g.snapshot_date
   AND e.term_date <= DATEADD(month, 6, g.snapshot_date)
  GROUP BY 1, 2
), series AS (
  SELECT
    s.snapshot_date,
    s.group_label,
    s.employee_snapshots,
    s.voluntary_exit_snapshots,
    ROUND(
      100.0 * s.voluntary_exit_snapshots / NULLIF(s.employee_snapshots, 0),
      4
    ) AS voluntary_rate_percent,
    p.eligible_employee_snapshots,
    p.ratio_observed_employee_snapshots,
    p.ratio_missing_employee_snapshots
  FROM series_counts AS s
  INNER JOIN snapshot_summary AS p
    ON p.snapshot_date = s.snapshot_date
), quality_metrics AS (
  SELECT
    'source_first_snapshot_date' AS metric,
    CAST(NULL AS DECIMAL(20, 6)) AS metric_value,
    b.source_first_snapshot_date AS metric_date
  FROM source_bounds AS b
  UNION ALL
  SELECT 'source_max_snapshot_date', NULL, b.source_max_snapshot_date
  FROM source_bounds AS b
  UNION ALL
  SELECT 'complete_followup_first_snapshot_date', NULL, MIN(snapshot_date)
  FROM complete_snapshots
  UNION ALL
  SELECT 'complete_followup_last_snapshot_date', NULL, MAX(snapshot_date)
  FROM complete_snapshots
  UNION ALL
  SELECT 'complete_snapshot_count', COUNT(*)::DECIMAL(20, 6), NULL
  FROM complete_snapshots
  UNION ALL
  SELECT 'eligible_employee_snapshot_rows', COUNT(*)::DECIMAL(20, 6), NULL
  FROM eligible
  UNION ALL
  SELECT 'eligible_employee_snapshot_duplicate_rows',
    COALESCE(SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END), 0)::DECIMAL(20, 6), NULL
  FROM eligible_key_quality
  UNION ALL
  SELECT 'conflicting_compa_ratio_employee_snapshots',
    COALESCE(SUM(CASE WHEN distinct_compa_ratio_values > 1 THEN 1 ELSE 0 END), 0)::DECIMAL(20, 6), NULL
  FROM eligible_key_quality
  UNION ALL
  SELECT 'ratio_observed_employee_snapshots',
    COALESCE(SUM(ratio_observed_employee_snapshots), 0)::DECIMAL(20, 6), NULL
  FROM snapshot_summary
  UNION ALL
  SELECT 'ratio_missing_employee_snapshots',
    COALESCE(SUM(ratio_missing_employee_snapshots), 0)::DECIMAL(20, 6), NULL
  FROM snapshot_summary
  UNION ALL
  SELECT 'ratio_zero_employee_snapshots',
    COALESCE(SUM(CASE WHEN compa_ratio = 0 THEN 1 ELSE 0 END), 0)::DECIMAL(20, 6), NULL
  FROM eligible
  UNION ALL
  SELECT 'ratio_negative_employee_snapshots',
    COALESCE(SUM(CASE WHEN compa_ratio < 0 THEN 1 ELSE 0 END), 0)::DECIMAL(20, 6), NULL
  FROM eligible
  UNION ALL
  SELECT 'termination_event_keys', COUNT(*)::DECIMAL(20, 6), NULL
  FROM termination_key_quality
  UNION ALL
  SELECT 'ambiguous_termination_event_keys',
    COALESCE(SUM(CASE WHEN distinct_term_type_count > 1 THEN 1 ELSE 0 END), 0)::DECIMAL(20, 6), NULL
  FROM termination_key_quality
  UNION ALL
  SELECT 'strict_voluntary_event_keys', COUNT(*)::DECIMAL(20, 6), NULL
  FROM voluntary_events
  UNION ALL
  SELECT 'voluntary_exception_event_keys',
    COALESCE(SUM(CASE WHEN normalized_term_type = 'VOLUNTARY EXCEPTION' THEN 1 ELSE 0 END), 0)::DECIMAL(20, 6), NULL
  FROM termination_key_quality
  UNION ALL
  SELECT 'published_series_points', COUNT(*)::DECIMAL(20, 6), NULL
  FROM series
  UNION ALL
  SELECT 'series_points_below_n30',
    COALESCE(SUM(CASE WHEN employee_snapshots < 30 THEN 1 ELSE 0 END), 0)::DECIMAL(20, 6), NULL
  FROM series
  UNION ALL
  SELECT 'series_group_reconciliation_failures',
    COALESCE(SUM(CASE WHEN group_sum <> ratio_observed_employee_snapshots THEN 1 ELSE 0 END), 0)::DECIMAL(20, 6), NULL
  FROM (
    SELECT
      p.snapshot_date,
      p.ratio_observed_employee_snapshots,
      COALESCE(SUM(s.employee_snapshots), 0) AS group_sum
    FROM snapshot_summary AS p
    LEFT JOIN series AS s ON s.snapshot_date = p.snapshot_date
    GROUP BY 1, 2
  ) AS reconciled
), audit_rows AS (
  SELECT
    'audit' AS row_type,
    CAST(NULL AS DATE) AS snapshot_date,
    CAST(NULL AS VARCHAR(64)) AS group_label,
    CAST(NULL AS BIGINT) AS employee_snapshots,
    CAST(NULL AS BIGINT) AS voluntary_exit_snapshots,
    CAST(NULL AS DECIMAL(20, 6)) AS voluntary_rate_percent,
    CAST(NULL AS BIGINT) AS eligible_employee_snapshots,
    CAST(NULL AS BIGINT) AS ratio_observed_employee_snapshots,
    CAST(NULL AS BIGINT) AS ratio_missing_employee_snapshots,
    metric,
    metric_value,
    metric_date
  FROM quality_metrics
)
SELECT
  'series' AS row_type,
  snapshot_date,
  group_label,
  employee_snapshots,
  voluntary_exit_snapshots,
  voluntary_rate_percent,
  eligible_employee_snapshots,
  ratio_observed_employee_snapshots,
  ratio_missing_employee_snapshots,
  CAST(NULL AS VARCHAR(128)) AS metric,
  CAST(NULL AS DECIMAL(20, 6)) AS metric_value,
  CAST(NULL AS DATE) AS metric_date
FROM series
UNION ALL
SELECT
  row_type,
  snapshot_date,
  group_label,
  employee_snapshots,
  voluntary_exit_snapshots,
  voluntary_rate_percent,
  eligible_employee_snapshots,
  ratio_observed_employee_snapshots,
  ratio_missing_employee_snapshots,
  metric,
  metric_value,
  metric_date
FROM audit_rows
ORDER BY row_type, snapshot_date, group_label, metric;
