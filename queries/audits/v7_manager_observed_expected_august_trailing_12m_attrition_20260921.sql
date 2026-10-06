/*
  Slide 39 internal stage: manager observed-to-expected ratio.

  The ratio is reconstructed from six complete historical intervals ending at
  the 2025-08-24 baseline.  Attrition labels are not manager attrition and do
  not use the manager-count denominator: each label is voluntary attrition of
  baseline direct reports assigned to managers in the displayed ratio band.
*/
WITH closure_dates AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  GROUP BY 1
), closure_sequence AS (
  SELECT snapshot_date,
         ROW_NUMBER() OVER (ORDER BY snapshot_date) AS closure_sequence
  FROM closure_dates
), baseline_close AS (
  SELECT closure_sequence, snapshot_date AS baseline_date
  FROM closure_sequence
  WHERE snapshot_date = DATE '2025-08-24'
), intervals AS (
  SELECT c.closure_sequence AS interval_sequence,
         LAG(c.snapshot_date) OVER (ORDER BY c.closure_sequence) AS interval_start,
         c.snapshot_date AS interval_end
  FROM closure_sequence c
  CROSS JOIN baseline_close b
  WHERE c.closure_sequence BETWEEN b.closure_sequence - 5 AND b.closure_sequence
), valid_intervals AS (
  SELECT interval_sequence, interval_start, interval_end
  FROM intervals WHERE interval_start IS NOT NULL
), exposure_raw AS (
  SELECT i.interval_sequence, i.interval_start, i.interval_end,
         CAST(w.employee_id AS BIGINT) AS employee_id,
         CAST(w.manager_employee_id AS BIGINT) AS manager_employee_id,
         COALESCE(NULLIF(TRIM(CAST(w.region AS VARCHAR(256))), ''), 'Unknown') AS region,
         COALESCE(NULLIF(TRIM(CAST(w.job_family AS VARCHAR(256))), ''), 'Unknown') AS job_family,
         COALESCE(NULLIF(TRIM(CAST(w.job_level_primary_position AS VARCHAR(256))), ''), 'Unknown') AS job_level,
         CASE
           WHEN w.max_hire_rehire_date IS NULL OR w.max_hire_rehire_date > w.fis_mo_end_dt THEN 'Unknown'
           WHEN DATEDIFF(month, w.max_hire_rehire_date, w.fis_mo_end_dt) < 12 THEN '<1 year'
           WHEN DATEDIFF(month, w.max_hire_rehire_date, w.fis_mo_end_dt) < 24 THEN '1-<2 years'
           WHEN DATEDIFF(month, w.max_hire_rehire_date, w.fis_mo_end_dt) < 60 THEN '2-<5 years'
           ELSE '5+ years'
         END AS tenure_band
  FROM valid_intervals i
  INNER JOIN hrda.post_hire_monthly_worker_dtls w
    ON CAST(w.fis_mo_end_dt AS DATE) = i.interval_start
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND COALESCE(w.is_rf360_yes_no, 0) = 0
    AND w.employee_id IS NOT NULL
    AND w.manager_employee_id IS NOT NULL
),
exposure AS (
  SELECT interval_sequence, interval_start, interval_end, employee_id,
         manager_employee_id, region, job_family, job_level, tenure_band
  FROM (
    SELECT e.interval_sequence, e.interval_start, e.interval_end, e.employee_id,
           e.manager_employee_id, e.region, e.job_family, e.job_level, e.tenure_band,
           ROW_NUMBER() OVER (PARTITION BY interval_sequence, employee_id ORDER BY manager_employee_id) AS row_rank
    FROM exposure_raw e
  ) d
  WHERE row_rank = 1
),
baseline_members_raw AS (
  SELECT CAST(w.employee_id AS BIGINT) AS employee_id,
         CAST(w.manager_employee_id AS BIGINT) AS manager_employee_id,
         COUNT(*) AS source_rows,
         COUNT(DISTINCT CAST(w.manager_employee_id AS VARCHAR(64))) AS manager_variants
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN baseline_close b
  WHERE CAST(w.fis_mo_end_dt AS DATE) = b.baseline_date
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND COALESCE(w.is_rf360_yes_no, 0) = 0
    AND w.employee_id IS NOT NULL
    AND w.manager_employee_id IS NOT NULL
  GROUP BY 1, 2
),
baseline_members AS (
  SELECT employee_id, manager_employee_id
  FROM baseline_members_raw WHERE source_rows = 1 AND manager_variants = 1
),
baseline_teams AS (
  SELECT manager_employee_id, COUNT(*) AS current_direct_reports
  FROM baseline_members GROUP BY 1
),
voluntary_events AS (
  SELECT CAST(w.employee_id AS BIGINT) AS employee_id,
         CAST(w.term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls w
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
    AND CAST(w.term_date AS DATE) > (SELECT MIN(interval_start) FROM valid_intervals)
    AND CAST(w.term_date AS DATE) <= (SELECT MAX(interval_end) FROM valid_intervals)
    AND w.employee_id IS NOT NULL
  GROUP BY 1, 2
),
event_attributions AS (
  SELECT v.employee_id, v.term_date, i.interval_sequence,
         e.manager_employee_id, e.region, e.job_family, e.job_level, e.tenure_band
  FROM voluntary_events v
  INNER JOIN valid_intervals i ON v.term_date > i.interval_start AND v.term_date <= i.interval_end
  INNER JOIN exposure e ON e.interval_sequence = i.interval_sequence AND e.employee_id = v.employee_id
),
exposure_by_stratum AS (
  SELECT interval_sequence, region, job_family, job_level, tenure_band, COUNT(*) AS employee_intervals
  FROM exposure GROUP BY 1, 2, 3, 4, 5
),
events_by_stratum AS (
  SELECT interval_sequence, region, job_family, job_level, tenure_band, COUNT(*) AS voluntary_events
  FROM event_attributions GROUP BY 1, 2, 3, 4, 5
),
global_rates AS (
  SELECT x.interval_sequence, x.employee_intervals,
         COALESCE(e.voluntary_events, 0) AS voluntary_events,
         COALESCE(e.voluntary_events, 0)::DECIMAL(20,10) / NULLIF(x.employee_intervals, 0) AS global_rate
  FROM (SELECT interval_sequence, COUNT(*) AS employee_intervals FROM exposure GROUP BY 1) x
  LEFT JOIN (SELECT interval_sequence, COUNT(*) AS voluntary_events FROM event_attributions GROUP BY 1) e
    ON e.interval_sequence = x.interval_sequence
),
stratum_rates AS (
  SELECT x.interval_sequence, x.region, x.job_family, x.job_level, x.tenure_band,
         x.employee_intervals, COALESCE(e.voluntary_events, 0) AS voluntary_events,
         g.global_rate,
         CASE WHEN x.employee_intervals >= 30
              THEN COALESCE(e.voluntary_events, 0)::DECIMAL(20,10) / NULLIF(x.employee_intervals, 0)
              ELSE g.global_rate END AS applied_rate
  FROM exposure_by_stratum x
  INNER JOIN global_rates g ON g.interval_sequence = x.interval_sequence
  LEFT JOIN events_by_stratum e
    ON e.interval_sequence = x.interval_sequence AND e.region = x.region
   AND e.job_family = x.job_family AND e.job_level = x.job_level AND e.tenure_band = x.tenure_band
),
manager_stratum_exposure AS (
  SELECT interval_sequence, manager_employee_id, region, job_family, job_level, tenure_band,
         COUNT(*) AS employee_intervals
  FROM exposure GROUP BY 1, 2, 3, 4, 5, 6
),
manager_expected AS (
  SELECT m.manager_employee_id,
         SUM(m.employee_intervals) AS employee_intervals,
         SUM(m.employee_intervals * r.applied_rate) AS expected_voluntary_exits
  FROM manager_stratum_exposure m
  INNER JOIN stratum_rates r
    ON r.interval_sequence = m.interval_sequence AND r.region = m.region
   AND r.job_family = m.job_family AND r.job_level = m.job_level AND r.tenure_band = m.tenure_band
  GROUP BY 1
),
manager_observed AS (
  SELECT manager_employee_id, COUNT(*) AS observed_voluntary_exits
  FROM event_attributions GROUP BY 1
),
global_prior AS (
  SELECT SUM(voluntary_events)::DECIMAL(20,10) / NULLIF(SUM(employee_intervals), 0) AS global_rate
  FROM global_rates
),
manager_scores AS (
  SELECT t.manager_employee_id, t.current_direct_reports,
         CASE WHEN e.employee_intervals IS NULL OR e.employee_intervals = 0
                    OR e.expected_voluntary_exits IS NULL OR g.global_rate IS NULL OR g.global_rate <= 0
              THEN NULL
              ELSE (COALESCE(o.observed_voluntary_exits, 0) + 60 * g.global_rate)
                   / NULLIF(e.expected_voluntary_exits + 60 * g.global_rate, 0)
         END AS smoothed_excess_ratio
  FROM baseline_teams t
  LEFT JOIN manager_expected e ON e.manager_employee_id = t.manager_employee_id
  LEFT JOIN manager_observed o ON o.manager_employee_id = t.manager_employee_id
  CROSS JOIN global_prior g
),
scored_managers AS (
  SELECT manager_employee_id, current_direct_reports,
         CASE WHEN smoothed_excess_ratio < 0.50 THEN '<0.5×'
              WHEN smoothed_excess_ratio < 1.00 THEN '0.5–<1.0×'
              WHEN smoothed_excess_ratio < 1.50 THEN '1.0–<1.5×'
              ELSE '≥1.5×' END AS score_band
  FROM manager_scores WHERE smoothed_excess_ratio IS NOT NULL
),
baseline_target AS (
  SELECT b.employee_id,
         CASE WHEN v.employee_id IS NULL THEN 0 ELSE 1 END AS voluntary_attrition_target
  FROM baseline_members b
  LEFT JOIN (SELECT DISTINCT employee_id FROM hrda.post_hire_monthly_worker_dtls w
             CROSS JOIN baseline_close p
             WHERE w.worker_type = 'Employee' AND w.employee_type = 'Regular'
               AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
               AND CAST(w.term_date AS DATE) > p.baseline_date
               AND CAST(w.term_date AS DATE) <= DATE '2026-08-23') v
    ON v.employee_id = b.employee_id
),
classified_reports AS (
  SELECT b.employee_id, s.score_band, t.voluntary_attrition_target
  FROM baseline_members b
  INNER JOIN scored_managers s ON s.manager_employee_id = b.manager_employee_id
  INNER JOIN baseline_target t ON t.employee_id = b.employee_id
),
category_metrics AS (
  SELECT score_band AS category,
         COUNT(DISTINCT employee_id) AS employee_count,
         SUM(voluntary_attrition_target) AS voluntary_exits,
         ROUND(100.0 * SUM(voluntary_attrition_target) / NULLIF(COUNT(DISTINCT employee_id), 0), 4) AS annual_attrition_rate_percent,
         COUNT(DISTINCT employee_id) AS direct_report_count
  FROM classified_reports GROUP BY 1
),
manager_counts AS (
  SELECT s.score_band AS category, COUNT(DISTINCT s.manager_employee_id) AS manager_count
  FROM scored_managers s GROUP BY 1
),
diagnostics AS (
  SELECT (SELECT COUNT(*) FROM baseline_members) AS baseline_employee_count,
         (SELECT COUNT(*) FROM scored_managers) AS scored_manager_count,
         (SELECT COUNT(*) FROM manager_scores WHERE smoothed_excess_ratio IS NULL) AS unscored_manager_count,
         (SELECT COUNT(*) FROM exposure) AS historical_employee_intervals,
         (SELECT COUNT(*) FROM valid_intervals) AS historical_interval_count
)
SELECT 'category' AS row_type, c.category, m.manager_count, c.employee_count,
       c.voluntary_exits, c.annual_attrition_rate_percent,
       CAST(NULL AS VARCHAR(64)) AS diagnostic_metric, CAST(NULL AS BIGINT) AS diagnostic_value
FROM category_metrics c INNER JOIN manager_counts m USING (category)
WHERE c.employee_count >= 30
UNION ALL SELECT 'diagnostic', NULL, NULL, NULL, NULL, NULL, 'baseline_employee_count', baseline_employee_count FROM diagnostics
UNION ALL SELECT 'diagnostic', NULL, NULL, NULL, NULL, NULL, 'scored_manager_count', scored_manager_count FROM diagnostics
UNION ALL SELECT 'diagnostic', NULL, NULL, NULL, NULL, NULL, 'unscored_manager_count', unscored_manager_count FROM diagnostics
UNION ALL SELECT 'diagnostic', NULL, NULL, NULL, NULL, NULL, 'historical_employee_intervals', historical_employee_intervals FROM diagnostics
UNION ALL SELECT 'diagnostic', NULL, NULL, NULL, NULL, NULL, 'historical_interval_count', historical_interval_count FROM diagnostics
ORDER BY row_type, category, diagnostic_metric;
