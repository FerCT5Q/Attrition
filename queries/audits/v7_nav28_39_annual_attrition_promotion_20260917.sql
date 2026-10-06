/*
  V7 navigation slides 30–32: annual voluntary attrition for the promotion
  visuals.  The historical category is rebuilt at each prediction snapshot;
  no current promotion state is used to classify a past exit.

  Categories
  ----------
  - time_since_last_promotion: latest valid observed promotion in the current
    employment episode, with explicit left-censored history states.
  - promotion_history_by_grade: 0 / 1 / 2+ valid recorded promotions, with
    an explicit partial-history state when the episode predates observed data.
  - current_grade_entry_path: confirmed promotion into the current grade,
    observed grade entry without a registered promotion, or not observable.

  Target: at least one strict VOLUNTARY termination in the 12 months after the
  monthly snapshot.  The query returns aggregate categories only.
*/
WITH source_bounds AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
complete_snapshot_dates AS (
    SELECT snapshot_date
    FROM (
        SELECT
            CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
            ROW_NUMBER() OVER (ORDER BY CAST(fis_mo_end_dt AS DATE) DESC) AS recency_rank
        FROM hrda.post_hire_monthly_worker_dtls
        CROSS JOIN source_bounds
        WHERE fis_mo_end_dt IS NOT NULL
          AND CAST(fis_mo_end_dt AS DATE) <= DATEADD(month, -12, latest_snapshot_date)
        GROUP BY 1
    ) ranked
    WHERE recency_rank <= 24
),
history_raw AS (
    SELECT
        CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(80))), '')) AS compensation_grade,
        MAX(CAST(w.max_hire_rehire_date AS DATE)) AS episode_start_date,
        MAX(COALESCE(w.is_promo, 0)) AS is_promo,
        MAX(CAST(w.promotion_date AS DATE)) AS promotion_date,
        MAX(COALESCE(w.active_status, 0)) AS active_status,
        MAX(CASE WHEN w.worker_type = 'Employee' AND w.employee_type = 'Regular' THEN 1 ELSE 0 END) AS regular_employee_flag,
        MAX(COALESCE(w.is_rf360_yes_no, 0)) AS is_rf360_yes_no,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(80))), ''), '<NULL>')) AS grade_variants,
        COUNT(DISTINCT COALESCE(CAST(w.max_hire_rehire_date AS VARCHAR(32)), '<NULL>')) AS episode_start_variants,
        COUNT(DISTINCT COALESCE(CAST(w.promotion_date AS VARCHAR(32)), '<NULL>')) AS promotion_date_variants,
        COUNT(DISTINCT COALESCE(CAST(w.is_promo AS VARCHAR(32)), '<NULL>')) AS promo_flag_variants
    FROM hrda.post_hire_monthly_worker_dtls AS w
    WHERE w.fis_mo_end_dt IS NOT NULL
      AND w.employee_id IS NOT NULL
    GROUP BY 1, 2
),
observed_history AS (
    SELECT MIN(snapshot_date) AS observed_history_start_date
    FROM history_raw
),
targets AS (
    SELECT
        h.snapshot_date,
        h.employee_id,
        h.compensation_grade,
        h.episode_start_date,
        h.source_row_count,
        h.grade_variants,
        h.episode_start_variants,
        h.promotion_date_variants,
        h.promo_flag_variants
    FROM history_raw AS h
    INNER JOIN complete_snapshot_dates AS d
      ON h.snapshot_date = d.snapshot_date
    WHERE h.regular_employee_flag = 1
      AND h.active_status = 1
),
target_quality AS (
    SELECT
        COUNT(*) AS target_employee_snapshot_count,
        COUNT(DISTINCT snapshot_date) AS target_snapshot_count,
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS target_duplicate_employee_snapshot_count,
        SUM(CASE WHEN grade_variants > 1
                   OR episode_start_variants > 1
                   OR promotion_date_variants > 1
                   OR promo_flag_variants > 1
                 THEN 1 ELSE 0 END) AS target_conflicting_employee_snapshot_count
    FROM targets
),
valid_promotion_events AS (
    SELECT DISTINCT
        h.employee_id,
        h.episode_start_date,
        h.promotion_date,
        h.snapshot_date AS event_snapshot_date,
        h.compensation_grade AS event_compensation_grade
    FROM history_raw AS h
    WHERE h.is_promo = 1
      AND h.promotion_date IS NOT NULL
      AND h.episode_start_date IS NOT NULL
      AND h.promotion_date >= h.episode_start_date
      AND h.promotion_date <= h.snapshot_date
),
target_promotion_stats AS (
    SELECT
        t.snapshot_date,
        t.employee_id,
        MAX(e.promotion_date) AS latest_valid_promotion_date,
        COUNT(DISTINCT e.promotion_date) AS recorded_promotion_count
    FROM targets AS t
    LEFT JOIN valid_promotion_events AS e
      ON e.employee_id = t.employee_id
     AND e.episode_start_date = t.episode_start_date
     AND e.promotion_date <= t.snapshot_date
    GROUP BY 1, 2
),
history_timeline AS (
    SELECT
        h.employee_id,
        h.episode_start_date,
        h.snapshot_date,
        h.compensation_grade,
        LAG(h.snapshot_date) OVER (
            PARTITION BY h.employee_id, h.episode_start_date
            ORDER BY h.snapshot_date
        ) AS previous_snapshot_date,
        LAG(h.compensation_grade) OVER (
            PARTITION BY h.employee_id, h.episode_start_date
            ORDER BY h.snapshot_date
        ) AS previous_snapshot_grade
    FROM history_raw AS h
    WHERE h.episode_start_date IS NOT NULL
),
grade_entry_events AS (
    SELECT
        employee_id,
        episode_start_date,
        compensation_grade AS entered_compensation_grade,
        snapshot_date AS entry_snapshot_date,
        previous_snapshot_date
    FROM history_timeline
    WHERE compensation_grade IS NOT NULL
      AND previous_snapshot_grade IS NOT NULL
      AND compensation_grade <> previous_snapshot_grade
),
target_entry_ranked AS (
    SELECT
        t.snapshot_date AS target_snapshot_date,
        t.employee_id,
        t.compensation_grade,
        t.episode_start_date,
        e.entry_snapshot_date,
        e.previous_snapshot_date,
        ROW_NUMBER() OVER (
            PARTITION BY t.snapshot_date, t.employee_id
            ORDER BY e.entry_snapshot_date DESC
        ) AS entry_recency_rank
    FROM targets AS t
    LEFT JOIN grade_entry_events AS e
      ON e.employee_id = t.employee_id
     AND e.episode_start_date = t.episode_start_date
     AND e.entered_compensation_grade = t.compensation_grade
     AND e.entry_snapshot_date <= t.snapshot_date
),
target_entry AS (
    SELECT
        target_snapshot_date,
        employee_id,
        compensation_grade,
        episode_start_date,
        entry_snapshot_date,
        previous_snapshot_date
    FROM target_entry_ranked
    WHERE entry_recency_rank = 1
),
target_entry_promotion AS (
    SELECT
        entry.target_snapshot_date,
        entry.employee_id,
        MAX(CASE WHEN event.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS promotion_confirmed
    FROM target_entry AS entry
    LEFT JOIN valid_promotion_events AS event
      ON event.employee_id = entry.employee_id
     AND event.episode_start_date = entry.episode_start_date
     AND event.event_compensation_grade = entry.compensation_grade
     AND event.promotion_date > entry.previous_snapshot_date
     AND event.promotion_date <= entry.entry_snapshot_date
    GROUP BY 1, 2
),
voluntary_events AS (
    SELECT CAST(employee_id AS BIGINT) AS employee_id, CAST(term_date AS DATE) AS term_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND term_date IS NOT NULL
    GROUP BY 1, 2
),
cohort AS (
    SELECT
        t.snapshot_date,
        t.employee_id,
        t.compensation_grade,
        t.episode_start_date,
        p.latest_valid_promotion_date,
        p.recorded_promotion_count,
        entry.entry_snapshot_date,
        COALESCE(entry_promo.promotion_confirmed, 0) AS promotion_confirmed,
        MAX(CASE WHEN voluntary.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS annual_voluntary_attrition_target
    FROM targets AS t
    INNER JOIN target_promotion_stats AS p
      ON p.snapshot_date = t.snapshot_date
     AND p.employee_id = t.employee_id
    LEFT JOIN target_entry AS entry
      ON entry.target_snapshot_date = t.snapshot_date
     AND entry.employee_id = t.employee_id
    LEFT JOIN target_entry_promotion AS entry_promo
      ON entry_promo.target_snapshot_date = t.snapshot_date
     AND entry_promo.employee_id = t.employee_id
    LEFT JOIN voluntary_events AS voluntary
      ON voluntary.employee_id = t.employee_id
     AND voluntary.term_date > t.snapshot_date
     AND voluntary.term_date <= DATEADD(month, 12, t.snapshot_date)
    GROUP BY
        t.snapshot_date, t.employee_id, t.compensation_grade, t.episode_start_date,
        p.latest_valid_promotion_date, p.recorded_promotion_count,
        entry.entry_snapshot_date, entry_promo.promotion_confirmed
),
classified AS (
    SELECT
        c.snapshot_date,
        c.employee_id,
        c.compensation_grade,
        c.annual_voluntary_attrition_target,
        CASE
          WHEN c.latest_valid_promotion_date IS NULL
               AND c.episode_start_date < observed.observed_history_start_date
            THEN 'History predates observed promotion events'
          WHEN c.latest_valid_promotion_date IS NULL THEN 'No promotion recorded in current episode'
          WHEN DATEADD(year, 1, c.latest_valid_promotion_date) > c.snapshot_date THEN '0–<1 year'
          WHEN DATEADD(year, 2, c.latest_valid_promotion_date) > c.snapshot_date THEN '1–<2 years'
          WHEN DATEADD(year, 3, c.latest_valid_promotion_date) > c.snapshot_date THEN '2–<3 years'
          WHEN DATEADD(year, 5, c.latest_valid_promotion_date) > c.snapshot_date THEN '3–<5 years'
          ELSE '5+ years'
        END AS time_since_promotion_band,
        CASE
          WHEN c.episode_start_date < observed.observed_history_start_date THEN 'partial_promotion_history'
          WHEN c.recorded_promotion_count = 0 THEN 'zero_recorded_promotions'
          WHEN c.recorded_promotion_count = 1 THEN 'one_recorded_promotion'
          ELSE 'two_or_more_recorded_promotions'
        END AS promotion_history_category,
        CASE
          WHEN c.entry_snapshot_date IS NULL THEN 'current_grade_entry_not_observable'
          WHEN c.promotion_confirmed = 1 THEN 'promotion_confirmed_into_current_grade'
          ELSE 'observed_entry_without_registered_promotion'
        END AS current_grade_entry_category
    FROM cohort AS c
    CROSS JOIN observed_history AS observed
),
category_rows AS (
    SELECT 'time_since_promotion' AS metric, time_since_promotion_band AS category, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified
    UNION ALL SELECT 'promotion_history_by_grade', compensation_grade || '|' || promotion_history_category, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified WHERE compensation_grade IS NOT NULL
    UNION ALL SELECT 'current_grade_entry_path', compensation_grade || '|' || current_grade_entry_category, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified WHERE compensation_grade IS NOT NULL
),
category_metrics AS (
    SELECT
        metric,
        category,
        MIN(snapshot_date) AS first_snapshot_date,
        MAX(snapshot_date) AS last_snapshot_date,
        COUNT(DISTINCT employee_id) AS distinct_employee_count,
        COUNT(*) AS employee_snapshot_count,
        SUM(annual_voluntary_attrition_target) AS voluntary_exits,
        ROUND(100.0 * SUM(annual_voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS annual_attrition_rate_percent
    FROM category_rows
    GROUP BY 1, 2
)
SELECT
    'category' AS row_type,
    metric,
    category,
    first_snapshot_date,
    last_snapshot_date,
    distinct_employee_count,
    employee_snapshot_count,
    voluntary_exits,
    annual_attrition_rate_percent,
    CAST(NULL AS BIGINT) AS diagnostic_value
FROM category_metrics
UNION ALL
SELECT
    'diagnostic', metric, CAST(NULL AS VARCHAR(256)),
    CAST(NULL AS DATE), CAST(NULL AS DATE), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), diagnostic_value
FROM (
    SELECT 'target_snapshot_count' AS metric, target_snapshot_count::BIGINT AS diagnostic_value FROM target_quality
    UNION ALL SELECT 'target_employee_snapshot_count', target_employee_snapshot_count::BIGINT FROM target_quality
    UNION ALL SELECT 'target_duplicate_employee_snapshot_count', target_duplicate_employee_snapshot_count::BIGINT FROM target_quality
    UNION ALL SELECT 'target_conflicting_employee_snapshot_count', target_conflicting_employee_snapshot_count::BIGINT FROM target_quality
    UNION ALL SELECT 'observed_history_start_year', EXTRACT(year FROM observed_history_start_date)::BIGINT FROM observed_history
) diagnostics
ORDER BY row_type, metric, category;
