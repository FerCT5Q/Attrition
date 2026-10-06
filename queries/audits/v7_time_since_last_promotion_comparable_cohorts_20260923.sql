/*
  Presentation | aggregate-only | Time since last promotion, comparable cohorts

  Fixed feature snapshot: 2025-08-24
  Fixed strict outcome: VOLUNTARY term_date in (2025-08-24, 2026-08-23]
  Population: active Regular Employees excluding RF360 at the feature snapshot.

  Claims and acceptance rules
  ---------------------------
  1. A latest promotion is valid only when is_promo=1, promotion_date is present,
     is not after the event snapshot or feature snapshot, and is on/after the
     employee's current max_hire_rehire_date.  No future row participates.
  2. The no-recorded-promotion proxy is eligible only when the employment
     episode begins within observable history, time_in_role is non-negative,
     and ROUND(time_in_role, 1) equals the calendar tenure from
     max_hire_rehire_date rounded to one decimal.  It is not a “never promoted”
     claim.
  3. The cohort must reconcile exactly to recorded-promotion, proxy, and
     explicitly declared exclusions; each published band must have n >= 30.

  Output contains only aggregate counts, rates and audit metrics. Employee IDs
  are used only within joins, grouping and distinct counts.
*/
WITH parameters AS (
    SELECT
        DATE '2025-08-24' AS baseline_snapshot_date,
        DATE '2026-08-23' AS outcome_cutoff_date
),
baseline_candidates AS (
    SELECT
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(COALESCE(w.is_rf360_yes_no, 0)) AS is_rf360_yes_no
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN parameters AS p
    WHERE CAST(w.fis_mo_end_dt AS DATE) = p.baseline_snapshot_date
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.employee_id IS NOT NULL
    GROUP BY 1
),
baseline_snapshot AS (
    SELECT
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(w.max_hire_rehire_date AS DATE)) AS episode_start_date,
        MAX(w.time_in_role) AS time_in_role_years,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(w.max_hire_rehire_date AS VARCHAR(32)), '<NULL>')) AS episode_start_variants,
        COUNT(DISTINCT COALESCE(CAST(w.time_in_role AS VARCHAR(64)), '<NULL>')) AS time_in_role_variants
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN parameters AS p
    WHERE CAST(w.fis_mo_end_dt AS DATE) = p.baseline_snapshot_date
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND COALESCE(w.is_rf360_yes_no, 0) = 0
      AND w.employee_id IS NOT NULL
    GROUP BY 1
),
baseline_quality AS (
    SELECT
        COUNT(*) AS baseline_employee_count,
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS baseline_duplicate_employee_snapshot_count,
        SUM(CASE WHEN episode_start_variants > 1 OR time_in_role_variants > 1 THEN 1 ELSE 0 END) AS baseline_conflicting_employee_snapshot_count,
        SUM(CASE WHEN episode_start_date IS NULL OR episode_start_date > p.baseline_snapshot_date THEN 1 ELSE 0 END) AS invalid_episode_start_count,
        SUM(CASE WHEN time_in_role_years IS NOT NULL AND time_in_role_years < 0 THEN 1 ELSE 0 END) AS negative_time_in_role_count,
        SUM(CASE WHEN COALESCE(c.is_rf360_yes_no, 0) <> 0 THEN 1 ELSE 0 END) AS rf360_included_count
    FROM baseline_snapshot AS b
    INNER JOIN baseline_candidates AS c
      ON c.employee_id = b.employee_id
    CROSS JOIN parameters AS p
),
observed_history AS (
    SELECT MIN(CAST(fis_mo_end_dt AS DATE)) AS observed_history_start_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
promotion_history AS (
    SELECT
        CAST(w.employee_id AS BIGINT) AS employee_id,
        CAST(w.fis_mo_end_dt AS DATE) AS event_snapshot_date,
        w.is_promo,
        CAST(w.promotion_date AS DATE) AS promotion_date
    FROM hrda.post_hire_monthly_worker_dtls AS w
    INNER JOIN baseline_snapshot AS b
      ON b.employee_id = CAST(w.employee_id AS BIGINT)
    CROSS JOIN parameters AS p
    WHERE w.fis_mo_end_dt IS NOT NULL
      AND CAST(w.fis_mo_end_dt AS DATE) <= p.baseline_snapshot_date
      AND COALESCE(w.is_rf360_yes_no, 0) = 0
),
promotion_quality AS (
    SELECT
        SUM(CASE WHEN is_promo IS NULL OR is_promo NOT IN (0, 1) THEN 1 ELSE 0 END) AS invalid_promo_flag_count,
        SUM(CASE WHEN is_promo = 1 AND promotion_date IS NULL THEN 1 ELSE 0 END) AS promo_flag_without_date_count,
        SUM(CASE WHEN promotion_date IS NOT NULL AND COALESCE(is_promo, 0) <> 1 THEN 1 ELSE 0 END) AS promotion_date_without_promo_flag_count,
        SUM(CASE WHEN promotion_date IS NOT NULL AND promotion_date > event_snapshot_date THEN 1 ELSE 0 END) AS promotion_date_after_event_snapshot_count,
        SUM(CASE WHEN promotion_date > p.baseline_snapshot_date THEN 1 ELSE 0 END) AS future_promotion_date_count
    FROM promotion_history
    CROSS JOIN parameters AS p
),
valid_promotion_events AS (
    SELECT DISTINCT
        employee_id,
        promotion_date
    FROM promotion_history AS h
    CROSS JOIN parameters AS p
    WHERE is_promo = 1
      AND promotion_date IS NOT NULL
      AND promotion_date <= event_snapshot_date
      AND promotion_date <= p.baseline_snapshot_date
),
promotion_assignment AS (
    SELECT
        b.employee_id,
        b.episode_start_date,
        b.time_in_role_years,
        MAX(CASE WHEN e.promotion_date >= b.episode_start_date THEN e.promotion_date END) AS latest_valid_promotion_date,
        SUM(CASE WHEN e.promotion_date < b.episode_start_date THEN 1 ELSE 0 END) AS pre_episode_event_excluded_count
    FROM baseline_snapshot AS b
    LEFT JOIN valid_promotion_events AS e
      ON e.employee_id = b.employee_id
    GROUP BY 1, 2, 3
),
classified AS (
    SELECT
        a.employee_id,
        a.episode_start_date,
        a.time_in_role_years,
        a.latest_valid_promotion_date,
        a.pre_episode_event_excluded_count,
        CASE
            WHEN a.latest_valid_promotion_date IS NOT NULL THEN 'recorded_promotion'
            WHEN a.episode_start_date IS NULL OR a.episode_start_date > p.baseline_snapshot_date THEN 'excluded_invalid_episode_start'
            WHEN a.episode_start_date < h.observed_history_start_date THEN 'excluded_history_before_observable'
            WHEN a.time_in_role_years IS NULL OR a.time_in_role_years < 0 THEN 'excluded_invalid_time_in_role'
            WHEN ROUND(a.time_in_role_years, 1) <> ROUND(DATEDIFF(day, a.episode_start_date, p.baseline_snapshot_date) / 365.2425, 1) THEN 'excluded_role_tenure_not_aligned'
            ELSE 'no_recorded_promotion_proxy'
        END AS cohort_type,
        CASE
            WHEN a.latest_valid_promotion_date IS NOT NULL THEN
                CASE
                    WHEN DATEADD(year, 1, a.latest_valid_promotion_date) > p.baseline_snapshot_date THEN '0–<1 year'
                    WHEN DATEADD(year, 2, a.latest_valid_promotion_date) > p.baseline_snapshot_date THEN '1–<2 years'
                    WHEN DATEADD(year, 3, a.latest_valid_promotion_date) > p.baseline_snapshot_date THEN '2–<3 years'
                    WHEN DATEADD(year, 5, a.latest_valid_promotion_date) > p.baseline_snapshot_date THEN '3–<5 years'
                    ELSE '5+ years'
                END
            WHEN a.episode_start_date IS NOT NULL
             AND a.episode_start_date <= p.baseline_snapshot_date THEN
                CASE
                    WHEN DATEADD(year, 1, a.episode_start_date) > p.baseline_snapshot_date THEN '0–<1 year'
                    WHEN DATEADD(year, 2, a.episode_start_date) > p.baseline_snapshot_date THEN '1–<2 years'
                    WHEN DATEADD(year, 3, a.episode_start_date) > p.baseline_snapshot_date THEN '2–<3 years'
                    WHEN DATEADD(year, 5, a.episode_start_date) > p.baseline_snapshot_date THEN '3–<5 years'
                    ELSE '5+ years'
                END
            ELSE NULL
        END AS time_band
    FROM promotion_assignment AS a
    CROSS JOIN observed_history AS h
    CROSS JOIN parameters AS p
),
voluntary_events AS (
    SELECT DISTINCT
        CAST(w.employee_id AS BIGINT) AS employee_id
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN parameters AS p
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND CAST(w.term_date AS DATE) > p.baseline_snapshot_date
      AND CAST(w.term_date AS DATE) <= p.outcome_cutoff_date
      AND w.employee_id IS NOT NULL
),
classified_with_outcome AS (
    SELECT
        c.employee_id,
        c.episode_start_date,
        c.time_in_role_years,
        c.latest_valid_promotion_date,
        c.pre_episode_event_excluded_count,
        c.cohort_type,
        c.time_band,
        CASE WHEN v.employee_id IS NULL THEN 0 ELSE 1 END AS annual_voluntary_exit
    FROM classified AS c
    LEFT JOIN voluntary_events AS v
      ON v.employee_id = c.employee_id
),
bands AS (
    SELECT 1 AS band_order, '0–<1 year' AS category
    UNION ALL SELECT 2, '1–<2 years'
    UNION ALL SELECT 3, '2–<3 years'
    UNION ALL SELECT 4, '3–<5 years'
    UNION ALL SELECT 5, '5+ years'
),
distribution AS (
    SELECT
        cohort_type,
        time_band AS category,
        COUNT(*) AS employee_count,
        SUM(annual_voluntary_exit) AS voluntary_exits,
        ROUND(100.0 * SUM(annual_voluntary_exit) / NULLIF(COUNT(*), 0), 4) AS annual_attrition_rate_percent
    FROM classified_with_outcome
    WHERE cohort_type IN ('recorded_promotion', 'no_recorded_promotion_proxy')
    GROUP BY 1, 2
),
display_distribution AS (
    SELECT
        c.cohort_type,
        b.band_order,
        b.category,
        COALESCE(d.employee_count, 0)::BIGINT AS employee_count,
        COALESCE(d.voluntary_exits, 0)::BIGINT AS voluntary_exits,
        d.annual_attrition_rate_percent
    FROM (SELECT DISTINCT cohort_type FROM distribution) AS c
    CROSS JOIN bands AS b
    LEFT JOIN distribution AS d
      ON d.cohort_type = c.cohort_type
     AND d.category = b.category
),
exclusions AS (
    SELECT
        cohort_type AS category,
        COUNT(*) AS employee_count,
        SUM(annual_voluntary_exit) AS voluntary_exits
    FROM classified_with_outcome
    WHERE cohort_type LIKE 'excluded_%'
    GROUP BY 1
),
reconciliation AS (
    SELECT 'baseline_population_count' AS metric, COUNT(*)::BIGINT AS metric_value FROM classified_with_outcome
    UNION ALL SELECT 'recorded_promotion_count', COUNT(*)::BIGINT FROM classified_with_outcome WHERE cohort_type = 'recorded_promotion'
    UNION ALL SELECT 'no_recorded_promotion_proxy_count', COUNT(*)::BIGINT FROM classified_with_outcome WHERE cohort_type = 'no_recorded_promotion_proxy'
    UNION ALL SELECT 'excluded_invalid_episode_start_count', COUNT(*)::BIGINT FROM classified_with_outcome WHERE cohort_type = 'excluded_invalid_episode_start'
    UNION ALL SELECT 'excluded_history_before_observable_count', COUNT(*)::BIGINT FROM classified_with_outcome WHERE cohort_type = 'excluded_history_before_observable'
    UNION ALL SELECT 'excluded_invalid_time_in_role_count', COUNT(*)::BIGINT FROM classified_with_outcome WHERE cohort_type = 'excluded_invalid_time_in_role'
    UNION ALL SELECT 'excluded_role_tenure_not_aligned_count', COUNT(*)::BIGINT FROM classified_with_outcome WHERE cohort_type = 'excluded_role_tenure_not_aligned'
    UNION ALL SELECT 'declared_exclusions_total', COUNT(*)::BIGINT FROM classified_with_outcome WHERE cohort_type LIKE 'excluded_%'
    UNION ALL SELECT 'recorded_promotion_band_total', COALESCE(SUM(employee_count), 0)::BIGINT FROM display_distribution WHERE cohort_type = 'recorded_promotion'
    UNION ALL SELECT 'no_recorded_promotion_proxy_band_total', COALESCE(SUM(employee_count), 0)::BIGINT FROM display_distribution WHERE cohort_type = 'no_recorded_promotion_proxy'
    UNION ALL SELECT 'baseline_voluntary_exits_from_classified', SUM(annual_voluntary_exit)::BIGINT FROM classified_with_outcome
    UNION ALL SELECT 'baseline_voluntary_exits_direct', COUNT(*)::BIGINT FROM baseline_snapshot AS b INNER JOIN voluntary_events AS v ON v.employee_id = b.employee_id
    UNION ALL SELECT 'pre_episode_event_excluded_count', COALESCE(SUM(pre_episode_event_excluded_count), 0)::BIGINT FROM classified
    UNION ALL SELECT 'rf360_excluded_count', COUNT(*)::BIGINT FROM baseline_candidates WHERE COALESCE(is_rf360_yes_no, 0) <> 0
),
diagnostics AS (
    SELECT 'baseline_employee_count' AS metric, baseline_employee_count::BIGINT AS metric_value FROM baseline_quality
    UNION ALL SELECT 'baseline_duplicate_employee_snapshot_count', baseline_duplicate_employee_snapshot_count::BIGINT FROM baseline_quality
    UNION ALL SELECT 'baseline_conflicting_employee_snapshot_count', baseline_conflicting_employee_snapshot_count::BIGINT FROM baseline_quality
    UNION ALL SELECT 'invalid_episode_start_count', invalid_episode_start_count::BIGINT FROM baseline_quality
    UNION ALL SELECT 'negative_time_in_role_count', negative_time_in_role_count::BIGINT FROM baseline_quality
    UNION ALL SELECT 'rf360_included_count', rf360_included_count::BIGINT FROM baseline_quality
    UNION ALL SELECT 'invalid_promo_flag_count', invalid_promo_flag_count::BIGINT FROM promotion_quality
    UNION ALL SELECT 'promo_flag_without_date_count', promo_flag_without_date_count::BIGINT FROM promotion_quality
    UNION ALL SELECT 'promotion_date_without_promo_flag_count', promotion_date_without_promo_flag_count::BIGINT FROM promotion_quality
    UNION ALL SELECT 'promotion_date_after_event_snapshot_count', promotion_date_after_event_snapshot_count::BIGINT FROM promotion_quality
    UNION ALL SELECT 'future_promotion_date_count', future_promotion_date_count::BIGINT FROM promotion_quality
)
SELECT
    'distribution' AS row_type,
    cohort_type,
    category,
    band_order,
    employee_count,
    voluntary_exits,
    annual_attrition_rate_percent,
    CAST(NULL AS VARCHAR(128)) AS metric,
    CAST(NULL AS BIGINT) AS metric_value
FROM display_distribution
UNION ALL
SELECT
    'exclusion',
    CAST(NULL AS VARCHAR(128)),
    category,
    CAST(NULL AS INTEGER),
    employee_count,
    voluntary_exits,
    CAST(NULL AS DECIMAL(18,4)),
    CAST(NULL AS VARCHAR(128)),
    CAST(NULL AS BIGINT)
FROM exclusions
UNION ALL
SELECT
    'diagnostic',
    CAST(NULL AS VARCHAR(128)),
    CAST(NULL AS VARCHAR(128)),
    CAST(NULL AS INTEGER),
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
    CAST(NULL AS VARCHAR(128)),
    CAST(NULL AS INTEGER),
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)),
    metric,
    metric_value
FROM reconciliation
ORDER BY row_type, cohort_type, band_order, category, metric;
