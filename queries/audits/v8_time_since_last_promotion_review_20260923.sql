/*
  Internal analysis | aggregate-only | V8 Time since last promotion review

  Claim
  -----
  The visual may show: (a) the latest valid promotion recorded in the current
  employment episode; and (b) aggregate level, stored time-in-role, and
  role-start-versus-hire/rehire context for people without a promotion recorded
  in that episode. A missing event is never labeled "never promoted".

  Population and grain
  -------------------
  One active Regular Employee at each of two snapshots: 2026-08-23 for the
  current distribution and 2025-08-24 for the annual voluntary-attrition
  baseline. employee_id is used only inside CTEs for aggregation.

  Outcome
  -------
  Strict VOLUNTARY termination in (2025-08-24, 2026-08-23].

  Acceptance rule, evaluated by the V8 evidence builder
  ------------------------------------------------------
  Required target snapshots have one non-conflicting employee row; promotion
  flags/dates are valid and known by their event snapshot; no selected event is
  before the current episode; all published subgroup totals reconcile; and no
  identity, individual date, title, or compensation value leaves this query.
*/
WITH parameters AS (
    SELECT
        DATE '2026-08-23' AS display_snapshot_date,
        DATE '2025-08-24' AS baseline_snapshot_date
),
target_snapshots AS (
    SELECT 'display' AS snapshot_scope, display_snapshot_date AS snapshot_date FROM parameters
    UNION ALL
    SELECT 'baseline' AS snapshot_scope, baseline_snapshot_date AS snapshot_date FROM parameters
),
snapshot_raw AS (
    SELECT
        t.snapshot_scope,
        t.snapshot_date,
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(w.max_hire_rehire_date AS DATE)) AS episode_start_date,
        MAX(CAST(w.time_in_job_profile_start_date AS DATE)) AS job_profile_start_date,
        MAX(w.time_in_role) AS time_in_role_years,
        MAX(NULLIF(TRIM(CAST(w.level_grouped AS VARCHAR(80))), '')) AS level_grouped,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(w.max_hire_rehire_date AS VARCHAR(32)), '<NULL>')) AS episode_start_variants,
        COUNT(DISTINCT COALESCE(CAST(w.time_in_job_profile_start_date AS VARCHAR(32)), '<NULL>')) AS job_profile_start_variants,
        COUNT(DISTINCT COALESCE(CAST(w.time_in_role AS VARCHAR(64)), '<NULL>')) AS time_in_role_variants,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.level_grouped AS VARCHAR(80))), ''), '<NULL>')) AS level_grouped_variants
    FROM hrda.post_hire_monthly_worker_dtls AS w
    INNER JOIN target_snapshots AS t
      ON CAST(w.fis_mo_end_dt AS DATE) = t.snapshot_date
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.employee_id IS NOT NULL
    GROUP BY 1, 2, 3
),
target_quality AS (
    SELECT
        snapshot_scope,
        COUNT(*) AS employee_count,
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
        SUM(CASE WHEN episode_start_variants > 1
                   OR job_profile_start_variants > 1
                   OR time_in_role_variants > 1
                   OR level_grouped_variants > 1
                 THEN 1 ELSE 0 END) AS conflicting_employee_snapshot_count,
        SUM(CASE WHEN episode_start_date IS NULL OR episode_start_date > snapshot_date THEN 1 ELSE 0 END) AS invalid_episode_start_count,
        SUM(CASE WHEN time_in_role_years IS NULL OR time_in_role_years < 0 THEN 1 ELSE 0 END) AS invalid_time_in_role_count,
        SUM(CASE WHEN job_profile_start_date IS NULL OR job_profile_start_date > snapshot_date THEN 1 ELSE 0 END) AS invalid_job_profile_start_count
    FROM snapshot_raw
    GROUP BY 1
),
observed_history AS (
    SELECT MIN(CAST(fis_mo_end_dt AS DATE)) AS observed_history_start_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
history_promotion_rows AS (
    SELECT
        CAST(h.employee_id AS BIGINT) AS employee_id,
        CAST(h.fis_mo_end_dt AS DATE) AS event_snapshot_date,
        h.is_promo,
        CAST(h.promotion_date AS DATE) AS promotion_date
    FROM hrda.post_hire_monthly_worker_dtls AS h
    INNER JOIN (SELECT DISTINCT employee_id FROM snapshot_raw) AS target_employee
      ON target_employee.employee_id = CAST(h.employee_id AS BIGINT)
    WHERE h.fis_mo_end_dt IS NOT NULL
      AND CAST(h.fis_mo_end_dt AS DATE) <= (SELECT display_snapshot_date FROM parameters)
),
promotion_quality AS (
    SELECT
        SUM(CASE WHEN is_promo IS NULL OR is_promo NOT IN (0, 1) THEN 1 ELSE 0 END) AS invalid_promo_flag_count,
        SUM(CASE WHEN is_promo = 1 AND promotion_date IS NULL THEN 1 ELSE 0 END) AS promo_flag_without_date_count,
        SUM(CASE WHEN promotion_date IS NOT NULL AND COALESCE(is_promo, 0) <> 1 THEN 1 ELSE 0 END) AS promotion_date_without_promo_flag_count,
        SUM(CASE WHEN promotion_date IS NOT NULL AND promotion_date > event_snapshot_date THEN 1 ELSE 0 END) AS promotion_date_after_event_snapshot_count,
        SUM(CASE WHEN promotion_date > (SELECT display_snapshot_date FROM parameters) THEN 1 ELSE 0 END) AS future_promotion_date_count
    FROM history_promotion_rows
),
valid_promotion_events AS (
    SELECT DISTINCT
        employee_id,
        promotion_date
    FROM history_promotion_rows
    WHERE is_promo = 1
      AND promotion_date IS NOT NULL
      AND promotion_date <= event_snapshot_date
      AND promotion_date <= (SELECT display_snapshot_date FROM parameters)
),
promotion_stats AS (
    SELECT
        s.snapshot_scope,
        s.snapshot_date,
        s.employee_id,
        s.episode_start_date,
        s.job_profile_start_date,
        s.time_in_role_years,
        s.level_grouped,
        MAX(CASE WHEN e.promotion_date >= s.episode_start_date THEN e.promotion_date END) AS latest_valid_promotion_date,
        SUM(CASE WHEN e.promotion_date < s.episode_start_date THEN 1 ELSE 0 END) AS pre_episode_event_count
    FROM snapshot_raw AS s
    LEFT JOIN valid_promotion_events AS e
      ON e.employee_id = s.employee_id
     AND e.promotion_date <= s.snapshot_date
    GROUP BY 1, 2, 3, 4, 5, 6, 7
),
classified AS (
    SELECT
        p.snapshot_scope,
        p.snapshot_date,
        p.employee_id,
        p.episode_start_date,
        p.job_profile_start_date,
        p.time_in_role_years,
        p.level_grouped,
        p.pre_episode_event_count,
        CASE
          WHEN p.latest_valid_promotion_date IS NULL
               AND p.episode_start_date < h.observed_history_start_date
            THEN 'History predates observed promotion events'
          WHEN p.latest_valid_promotion_date IS NULL
            THEN 'No promotion recorded in current episode'
          WHEN DATEADD(year, 1, p.latest_valid_promotion_date) > p.snapshot_date THEN '0–<1 year'
          WHEN DATEADD(year, 2, p.latest_valid_promotion_date) > p.snapshot_date THEN '1–<2 years'
          WHEN DATEADD(year, 3, p.latest_valid_promotion_date) > p.snapshot_date THEN '2–<3 years'
          WHEN DATEADD(year, 5, p.latest_valid_promotion_date) > p.snapshot_date THEN '3–<5 years'
          ELSE '5+ years'
        END AS time_since_promotion_band,
        CASE
          WHEN p.time_in_role_years IS NULL OR p.time_in_role_years < 0 THEN 'Not recorded'
          WHEN p.time_in_role_years < 1 THEN '<1 year'
          WHEN p.time_in_role_years < 2 THEN '1–<2 years'
          WHEN p.time_in_role_years < 3 THEN '2–<3 years'
          WHEN p.time_in_role_years < 5 THEN '3–<5 years'
          WHEN p.time_in_role_years < 10 THEN '5–<10 years'
          ELSE '10+ years'
        END AS time_in_role_band,
        CASE
          WHEN p.job_profile_start_date IS NULL OR p.episode_start_date IS NULL
               OR p.job_profile_start_date > p.snapshot_date OR p.episode_start_date > p.snapshot_date
            THEN 'Start date not usable'
          WHEN p.job_profile_start_date <= p.episode_start_date
            THEN 'Role began with current employment episode'
          ELSE 'Role began after current employment episode'
        END AS role_start_relation,
        CASE
          WHEN p.job_profile_start_date IS NULL OR p.episode_start_date IS NULL
               OR p.time_in_role_years IS NULL OR p.time_in_role_years < 0
               OR p.job_profile_start_date > p.snapshot_date OR p.episode_start_date > p.snapshot_date
            THEN 'Cannot compare'
          WHEN ABS(
                 p.time_in_role_years
                 - (DATEDIFF(day, GREATEST(p.job_profile_start_date, p.episode_start_date), p.snapshot_date) / 365.2425)
               ) <= 0.25
            THEN 'Within 3 months'
          WHEN ABS(
                 p.time_in_role_years
                 - (DATEDIFF(day, GREATEST(p.job_profile_start_date, p.episode_start_date), p.snapshot_date) / 365.2425)
               ) <= 1.00
            THEN '3–12 months apart'
          ELSE 'More than 12 months apart'
        END AS role_tenure_alignment
    FROM promotion_stats AS p
    CROSS JOIN observed_history AS h
),
voluntary_events AS (
    SELECT
        CAST(employee_id AS BIGINT) AS employee_id,
        CAST(term_date AS DATE) AS term_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND term_date IS NOT NULL
    GROUP BY 1, 2
),
baseline_with_outcome AS (
    SELECT
        c.snapshot_scope,
        c.snapshot_date,
        c.employee_id,
        c.episode_start_date,
        c.job_profile_start_date,
        c.time_in_role_years,
        c.level_grouped,
        c.pre_episode_event_count,
        c.time_since_promotion_band,
        c.time_in_role_band,
        c.role_start_relation,
        c.role_tenure_alignment,
        MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS annual_voluntary_exit
    FROM classified AS c
    LEFT JOIN voluntary_events AS v
      ON v.employee_id = c.employee_id
     AND v.term_date > c.snapshot_date
     -- Fixed annual outcome window: (2025-08-24, 2026-08-23].
     -- DATEADD(month, 12, 2025-08-24) would incorrectly include 2026-08-24.
     AND v.term_date <= (SELECT display_snapshot_date FROM parameters)
    WHERE c.snapshot_scope = 'baseline'
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
),
current_time_distribution AS (
    SELECT
        time_since_promotion_band AS category,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM classified
    WHERE snapshot_scope = 'display'
    GROUP BY 1
),
baseline_time_outcome AS (
    SELECT
        time_since_promotion_band AS category,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(DISTINCT CASE WHEN annual_voluntary_exit = 1 THEN employee_id END) AS voluntary_exits,
        ROUND(100.0 * COUNT(DISTINCT CASE WHEN annual_voluntary_exit = 1 THEN employee_id END) / NULLIF(COUNT(DISTINCT employee_id), 0), 4) AS annual_attrition_rate_percent
    FROM baseline_with_outcome
    GROUP BY 1
),
current_no_promo_level AS (
    SELECT
        COALESCE(level_grouped, 'Not recorded') AS category,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM classified
    WHERE snapshot_scope = 'display'
      AND time_since_promotion_band = 'No promotion recorded in current episode'
    GROUP BY 1
),
baseline_no_promo_level AS (
    SELECT
        COALESCE(level_grouped, 'Not recorded') AS category,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(DISTINCT CASE WHEN annual_voluntary_exit = 1 THEN employee_id END) AS voluntary_exits,
        ROUND(100.0 * COUNT(DISTINCT CASE WHEN annual_voluntary_exit = 1 THEN employee_id END) / NULLIF(COUNT(DISTINCT employee_id), 0), 4) AS annual_attrition_rate_percent
    FROM baseline_with_outcome
    WHERE time_since_promotion_band = 'No promotion recorded in current episode'
    GROUP BY 1
),
current_no_promo_role AS (
    SELECT
        time_in_role_band AS category,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM classified
    WHERE snapshot_scope = 'display'
      AND time_since_promotion_band = 'No promotion recorded in current episode'
    GROUP BY 1
),
baseline_no_promo_role AS (
    SELECT
        time_in_role_band AS category,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(DISTINCT CASE WHEN annual_voluntary_exit = 1 THEN employee_id END) AS voluntary_exits,
        ROUND(100.0 * COUNT(DISTINCT CASE WHEN annual_voluntary_exit = 1 THEN employee_id END) / NULLIF(COUNT(DISTINCT employee_id), 0), 4) AS annual_attrition_rate_percent
    FROM baseline_with_outcome
    WHERE time_since_promotion_band = 'No promotion recorded in current episode'
    GROUP BY 1
),
current_no_promo_relation AS (
    SELECT
        role_start_relation AS category,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM classified
    WHERE snapshot_scope = 'display'
      AND time_since_promotion_band = 'No promotion recorded in current episode'
    GROUP BY 1
),
current_no_promo_alignment AS (
    SELECT
        role_tenure_alignment AS category,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM classified
    WHERE snapshot_scope = 'display'
      AND time_since_promotion_band = 'No promotion recorded in current episode'
    GROUP BY 1
),
reconciliation AS (
    SELECT 'display_time_distribution_total' AS metric, SUM(employee_count)::BIGINT AS metric_value FROM current_time_distribution
    UNION ALL
    SELECT 'baseline_time_distribution_total', SUM(employee_count)::BIGINT FROM baseline_time_outcome
    UNION ALL
    SELECT 'display_no_promo_level_total', SUM(employee_count)::BIGINT FROM current_no_promo_level
    UNION ALL
    SELECT 'display_no_promo_role_total', SUM(employee_count)::BIGINT FROM current_no_promo_role
    UNION ALL
    SELECT 'display_no_promo_relation_total', SUM(employee_count)::BIGINT FROM current_no_promo_relation
    UNION ALL
    SELECT 'display_no_promo_alignment_total', SUM(employee_count)::BIGINT FROM current_no_promo_alignment
    UNION ALL
    SELECT 'display_no_promo_total', COUNT(DISTINCT employee_id)::BIGINT
    FROM classified
    WHERE snapshot_scope = 'display'
      AND time_since_promotion_band = 'No promotion recorded in current episode'
    UNION ALL
    SELECT 'baseline_no_promo_total', COUNT(DISTINCT employee_id)::BIGINT
    FROM baseline_with_outcome
    WHERE time_since_promotion_band = 'No promotion recorded in current episode'
    UNION ALL
    SELECT 'baseline_classified_row_count', COUNT(*)::BIGINT
    FROM baseline_with_outcome
    UNION ALL
    SELECT 'baseline_classified_distinct_employee_count', COUNT(DISTINCT employee_id)::BIGINT
    FROM baseline_with_outcome
    UNION ALL
    SELECT 'baseline_voluntary_exits_from_classified', COUNT(DISTINCT CASE WHEN annual_voluntary_exit = 1 THEN employee_id END)::BIGINT
    FROM baseline_with_outcome
    UNION ALL
    SELECT 'baseline_voluntary_exits_direct', COUNT(DISTINCT s.employee_id)::BIGINT
    FROM snapshot_raw AS s
    INNER JOIN voluntary_events AS v
      ON v.employee_id = s.employee_id
     AND v.term_date > s.snapshot_date
     AND v.term_date <= (SELECT display_snapshot_date FROM parameters)
    WHERE s.snapshot_scope = 'baseline'
    UNION ALL
    SELECT 'pre_episode_event_excluded_count', COALESCE(SUM(pre_episode_event_count), 0)::BIGINT
    FROM classified
),
diagnostics AS (
    SELECT snapshot_scope || '_employee_count' AS metric, employee_count::BIGINT AS metric_value FROM target_quality
    UNION ALL
    SELECT snapshot_scope || '_duplicate_employee_snapshot_count', duplicate_employee_snapshot_count::BIGINT FROM target_quality
    UNION ALL
    SELECT snapshot_scope || '_conflicting_employee_snapshot_count', conflicting_employee_snapshot_count::BIGINT FROM target_quality
    UNION ALL
    SELECT snapshot_scope || '_invalid_episode_start_count', invalid_episode_start_count::BIGINT FROM target_quality
    UNION ALL
    SELECT snapshot_scope || '_invalid_time_in_role_count', invalid_time_in_role_count::BIGINT FROM target_quality
    UNION ALL
    SELECT snapshot_scope || '_invalid_job_profile_start_count', invalid_job_profile_start_count::BIGINT FROM target_quality
    UNION ALL
    SELECT 'invalid_promo_flag_count', invalid_promo_flag_count::BIGINT FROM promotion_quality
    UNION ALL
    SELECT 'promo_flag_without_date_count', promo_flag_without_date_count::BIGINT FROM promotion_quality
    UNION ALL
    SELECT 'promotion_date_without_promo_flag_count', promotion_date_without_promo_flag_count::BIGINT FROM promotion_quality
    UNION ALL
    SELECT 'promotion_date_after_event_snapshot_count', promotion_date_after_event_snapshot_count::BIGINT FROM promotion_quality
    UNION ALL
    SELECT 'future_promotion_date_count', future_promotion_date_count::BIGINT FROM promotion_quality
)
SELECT
    'display_time_since_promotion' AS row_type,
    category,
    employee_count,
    CAST(NULL AS BIGINT) AS voluntary_exits,
    CAST(NULL AS DECIMAL(18,4)) AS annual_attrition_rate_percent,
    CAST(NULL AS VARCHAR(128)) AS metric,
    CAST(NULL AS BIGINT) AS metric_value
FROM current_time_distribution
UNION ALL
SELECT
    'baseline_time_since_promotion',
    category,
    employee_count,
    voluntary_exits,
    annual_attrition_rate_percent,
    CAST(NULL AS VARCHAR(128)),
    CAST(NULL AS BIGINT)
FROM baseline_time_outcome
UNION ALL
SELECT
    'display_no_promo_level',
    category,
    employee_count,
    CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)),
    CAST(NULL AS VARCHAR(128)),
    CAST(NULL AS BIGINT)
FROM current_no_promo_level
UNION ALL
SELECT
    'baseline_no_promo_level',
    category,
    employee_count,
    voluntary_exits,
    annual_attrition_rate_percent,
    CAST(NULL AS VARCHAR(128)),
    CAST(NULL AS BIGINT)
FROM baseline_no_promo_level
UNION ALL
SELECT
    'display_no_promo_role_time',
    category,
    employee_count,
    CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)),
    CAST(NULL AS VARCHAR(128)),
    CAST(NULL AS BIGINT)
FROM current_no_promo_role
UNION ALL
SELECT
    'baseline_no_promo_role_time',
    category,
    employee_count,
    voluntary_exits,
    annual_attrition_rate_percent,
    CAST(NULL AS VARCHAR(128)),
    CAST(NULL AS BIGINT)
FROM baseline_no_promo_role
UNION ALL
SELECT
    'display_no_promo_role_start_relation',
    category,
    employee_count,
    CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)),
    CAST(NULL AS VARCHAR(128)),
    CAST(NULL AS BIGINT)
FROM current_no_promo_relation
UNION ALL
SELECT
    'display_no_promo_role_tenure_alignment',
    category,
    employee_count,
    CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)),
    CAST(NULL AS VARCHAR(128)),
    CAST(NULL AS BIGINT)
FROM current_no_promo_alignment
UNION ALL
SELECT
    'diagnostic',
    CAST(NULL AS VARCHAR(128)),
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)),
    metric,
    metric_value
FROM diagnostics
UNION ALL
SELECT
    'reconciliation',
    CAST(NULL AS VARCHAR(128)),
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)),
    metric,
    metric_value
FROM reconciliation
ORDER BY row_type, category, metric;
