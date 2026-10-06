/*
  Aggregate evidence for the Top 10 exact compensation-grade panel.

  Snapshot: 2026-08-23. Attrition window: (2025-08-24, 2026-08-23].
  Current distribution: Employee + Regular + active_status=1 + no RF360.
  Promotion: promotion_yes_no='Yes' / eligible AR25 participants.
  Attrition: strict VOLUNTARY exits / average monthly headcount by exact grade.
  Output is aggregate-only and limited to the ten grades with the largest
  current employee counts.
*/
WITH bounds AS (
    SELECT DATE '2026-08-23' AS latest_snapshot_date,
           DATE '2025-08-24' AS baseline_snapshot_date
),
available_snapshot_dates AS (
    SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
window_dates AS (
    SELECT d.snapshot_date
    FROM available_snapshot_dates AS d
    CROSS JOIN bounds AS b
    WHERE d.snapshot_date > b.baseline_snapshot_date
      AND d.snapshot_date <= b.latest_snapshot_date
),
review_snapshot AS (
    SELECT MAX(d.snapshot_date) AS review_snapshot_date
    FROM available_snapshot_dates AS d
    WHERE EXTRACT(year FROM d.snapshot_date) = 2025
      AND EXTRACT(month FROM d.snapshot_date) = 11
),
monthly_grouped AS (
    SELECT
        CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
        w.employee_id,
        MAX(CASE WHEN w.worker_type = 'Employee' AND w.employee_type = 'Regular' THEN 1 ELSE 0 END) AS regular_employee_flag,
        MAX(COALESCE(w.active_status, 0)) AS active_status,
        MAX(COALESCE(w.is_rf360_yes_no, 0)) AS is_rf360_yes_no,
        MAX(UPPER(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(80))), ''))) AS grade_value,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(80))), ''), '<NULL>')) AS grade_variant_count
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN bounds AS b
    WHERE CAST(w.fis_mo_end_dt AS DATE) >= DATEADD(day, -45, b.baseline_snapshot_date)
      AND CAST(w.fis_mo_end_dt AS DATE) <= b.latest_snapshot_date
      AND w.employee_id IS NOT NULL
    GROUP BY 1, 2
),
monthly_active AS (
    SELECT snapshot_date, employee_id, source_row_count, grade_variant_count, grade_value
    FROM monthly_grouped
    WHERE regular_employee_flag = 1
      AND active_status = 1
      AND is_rf360_yes_no = 0
      AND grade_value IS NOT NULL
      AND REGEXP_INSTR(grade_value, '^[A-Z][0-9]') = 1
),
current_population AS (
    SELECT
        m.snapshot_date,
        m.employee_id,
        m.source_row_count,
        m.grade_variant_count,
        m.grade_value
    FROM monthly_active AS m
    CROSS JOIN bounds AS b
    WHERE m.snapshot_date = b.latest_snapshot_date
),
current_distribution AS (
    SELECT grade_value AS grade, COUNT(*)::BIGINT AS current_employee_count
    FROM current_population
    GROUP BY 1
),
current_total AS (
    SELECT COUNT(*)::BIGINT AS current_employee_count
    FROM current_population
),
window_population AS (
    SELECT
        m.snapshot_date,
        m.employee_id,
        m.source_row_count,
        m.grade_variant_count,
        m.grade_value
    FROM monthly_active AS m
    INNER JOIN window_dates AS d ON d.snapshot_date = m.snapshot_date
),
monthly_headcount AS (
    SELECT snapshot_date, grade_value AS grade, COUNT(*)::BIGINT AS monthly_headcount
    FROM window_population
    GROUP BY 1, 2
),
grade_exposure AS (
    SELECT
        grid.grade,
        AVG(COALESCE(h.monthly_headcount, 0)::DECIMAL(18,6)) AS average_monthly_headcount
    FROM (
        SELECT d.snapshot_date, g.grade
        FROM window_dates AS d
        CROSS JOIN (SELECT DISTINCT grade_value AS grade FROM window_population) AS g
    ) AS grid
    LEFT JOIN monthly_headcount AS h
      ON h.snapshot_date = grid.snapshot_date
     AND h.grade = grid.grade
    GROUP BY 1
),
review_raw AS (
    SELECT
        NULLIF(TRIM(CAST(ar.employee_id AS VARCHAR(80))), '') AS employee_key,
        UPPER(NULLIF(TRIM(CAST(ar.grade AS VARCHAR(80))), '')) AS grade_value,
        UPPER(NULLIF(TRIM(CAST(ar.promotion_yes_no AS VARCHAR(40))), '')) AS promotion_flag
    FROM hrda.annual_review_report AS ar
    WHERE UPPER(TRIM(CAST(ar.cycle_name AS VARCHAR(160)))) = 'AR25'
),
review_grouped AS (
    SELECT
        employee_key,
        MAX(grade_value) AS grade_value,
        MAX(CASE WHEN promotion_flag = 'YES' THEN 1 ELSE 0 END) AS promoted,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(grade_value, '<NULL>')) AS grade_variant_count,
        COUNT(DISTINCT COALESCE(promotion_flag, '<NULL>')) AS promotion_flag_variant_count
    FROM review_raw
    WHERE employee_key IS NOT NULL
    GROUP BY 1
),
review_joined AS (
    SELECT
        review.employee_key,
        review.grade_value,
        review.promoted,
        review.source_row_count,
        review.grade_variant_count,
        review.promotion_flag_variant_count,
        monthly.employee_id AS matched_employee_id,
        monthly.regular_employee_flag,
        monthly.active_status,
        monthly.is_rf360_yes_no
    FROM review_grouped AS review
    CROSS JOIN review_snapshot AS review_date
    LEFT JOIN monthly_grouped AS monthly
      ON CAST(monthly.employee_id AS VARCHAR(80)) = review.employee_key
     AND monthly.snapshot_date = review_date.review_snapshot_date
),
review_eligible AS (
    SELECT
        employee_key,
        grade_value,
        promoted,
        source_row_count,
        grade_variant_count,
        promotion_flag_variant_count,
        matched_employee_id,
        regular_employee_flag,
        active_status,
        is_rf360_yes_no
    FROM review_joined
    WHERE matched_employee_id IS NOT NULL
      AND regular_employee_flag = 1
      AND active_status = 1
      AND is_rf360_yes_no = 0
      AND grade_value IS NOT NULL
      AND REGEXP_INSTR(grade_value, '^[A-Z][0-9]') = 1
),
promotion_by_grade AS (
    SELECT
        grade_value AS grade,
        COUNT(*)::BIGINT AS promotion_participant_count,
        SUM(promoted)::BIGINT AS promoted_employee_count,
        ROUND(100.0 * SUM(promoted) / NULLIF(COUNT(*), 0), 4) AS promotion_rate_percent
    FROM review_eligible
    GROUP BY 1
),
voluntary_event_rows AS (
    SELECT
        w.employee_id,
        CAST(w.term_date AS DATE) AS term_date,
        UPPER(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(80))), '')) AS grade_value
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN bounds AS b
    WHERE w.employee_id IS NOT NULL
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND COALESCE(w.is_rf360_yes_no, 0) = 0
      AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND CAST(w.term_date AS DATE) > b.baseline_snapshot_date
      AND CAST(w.term_date AS DATE) <= b.latest_snapshot_date
),
voluntary_event_source AS (
    SELECT
        employee_id,
        term_date,
        MAX(grade_value) AS grade_value,
        COUNT(DISTINCT COALESCE(grade_value, '<NULL>')) AS grade_variant_count,
        CASE
            WHEN COUNT(DISTINCT COALESCE(grade_value, '<NULL>')) = 1
             AND MAX(grade_value) IS NOT NULL
             AND REGEXP_INSTR(MAX(grade_value), '^[A-Z][0-9]') = 1
              THEN MAX(grade_value)
            ELSE NULL
        END AS termination_grade
    FROM voluntary_event_rows
    GROUP BY 1, 2
),
voluntary_event_candidates AS (
    SELECT
        event.employee_id,
        event.term_date,
        history.grade_value AS prior_grade,
        event.termination_grade,
        history.snapshot_date,
        ROW_NUMBER() OVER (
            PARTITION BY event.employee_id, event.term_date
            ORDER BY history.snapshot_date DESC
        ) AS recency_rank
    FROM voluntary_event_source AS event
    LEFT JOIN monthly_active AS history
      ON history.employee_id = event.employee_id
     AND history.snapshot_date < event.term_date
     AND DATEDIFF(day, history.snapshot_date, event.term_date) BETWEEN 0 AND 45
),
voluntary_event_assignment AS (
    SELECT
        employee_id,
        term_date,
        COALESCE(prior_grade, termination_grade) AS grade
    FROM voluntary_event_candidates
    WHERE recency_rank = 1
),
attrition_by_grade AS (
    SELECT grade, COUNT(*)::BIGINT AS voluntary_exit_count
    FROM voluntary_event_assignment
    WHERE grade IS NOT NULL
    GROUP BY 1
),
all_grades AS (
    SELECT grade FROM current_distribution
    UNION SELECT grade FROM promotion_by_grade
    UNION SELECT grade FROM grade_exposure
    UNION SELECT grade FROM attrition_by_grade
),
grade_rows AS (
    SELECT
        grades.grade,
        COALESCE(current.current_employee_count, 0)::BIGINT AS current_employee_count,
        ROUND(100.0 * COALESCE(current.current_employee_count, 0) / NULLIF(total.current_employee_count, 0), 4) AS current_distribution_percent,
        COALESCE(promotion.promotion_participant_count, 0)::BIGINT AS promotion_participant_count,
        COALESCE(promotion.promoted_employee_count, 0)::BIGINT AS promoted_employee_count,
        CASE WHEN COALESCE(promotion.promotion_participant_count, 0) > 0 THEN promotion.promotion_rate_percent END AS promotion_rate_percent,
        COALESCE(exposure.average_monthly_headcount, 0)::DECIMAL(18,6) AS average_monthly_headcount,
        COALESCE(attrition.voluntary_exit_count, 0)::BIGINT AS voluntary_exit_count,
        CASE
            WHEN COALESCE(exposure.average_monthly_headcount, 0) > 0
              THEN ROUND(100.0 * COALESCE(attrition.voluntary_exit_count, 0) / exposure.average_monthly_headcount, 4)
        END AS attrition_rate_percent
    FROM all_grades AS grades
    CROSS JOIN current_total AS total
    LEFT JOIN current_distribution AS current ON current.grade = grades.grade
    LEFT JOIN promotion_by_grade AS promotion ON promotion.grade = grades.grade
    LEFT JOIN grade_exposure AS exposure ON exposure.grade = grades.grade
    LEFT JOIN attrition_by_grade AS attrition ON attrition.grade = grades.grade
),
ranked_top10 AS (
    SELECT
        rows.grade,
        rows.current_employee_count,
        rows.current_distribution_percent,
        rows.promotion_participant_count,
        rows.promoted_employee_count,
        rows.promotion_rate_percent,
        rows.average_monthly_headcount,
        rows.voluntary_exit_count,
        rows.attrition_rate_percent,
        ROW_NUMBER() OVER (ORDER BY current_employee_count DESC, grade) AS current_rank
    FROM grade_rows AS rows
    WHERE current_employee_count > 0
),
diagnostics AS (
    SELECT 'latest_snapshot_date' AS metric, CAST(latest_snapshot_date AS VARCHAR(64)) AS metric_value FROM bounds
    UNION ALL SELECT 'baseline_snapshot_date', CAST(baseline_snapshot_date AS VARCHAR(64)) FROM bounds
    UNION ALL SELECT 'window_snapshot_count', CAST(COUNT(*) AS VARCHAR(64)) FROM window_dates
    UNION ALL SELECT 'review_snapshot_date', CAST(review_snapshot_date AS VARCHAR(64)) FROM review_snapshot
    UNION ALL SELECT 'current_population_count', CAST(COUNT(*) AS VARCHAR(64)) FROM current_population
    UNION ALL SELECT 'current_missing_grade_count', CAST(COALESCE(SUM(CASE WHEN grade_value IS NULL THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM current_population
    UNION ALL SELECT 'current_duplicate_employee_count', CAST(COALESCE(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM current_population
    UNION ALL SELECT 'current_conflicting_grade_count', CAST(COALESCE(SUM(CASE WHEN grade_variant_count > 1 THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM current_population
    UNION ALL SELECT 'annual_review_scope_eligible_count', CAST(COUNT(*) AS VARCHAR(64)) FROM review_eligible
    UNION ALL SELECT 'annual_review_promoted_employee_count', CAST(COALESCE(SUM(promoted), 0) AS VARCHAR(64)) FROM review_eligible
    UNION ALL SELECT 'voluntary_event_count', CAST(COUNT(*) AS VARCHAR(64)) FROM voluntary_event_source
    UNION ALL SELECT 'voluntary_event_assigned_count', CAST(COUNT(*) AS VARCHAR(64)) FROM voluntary_event_assignment WHERE grade IS NOT NULL
    UNION ALL SELECT 'voluntary_event_unassigned_count', CAST(COUNT(*) AS VARCHAR(64)) FROM voluntary_event_assignment WHERE grade IS NULL
    UNION ALL SELECT 'top10_grade_count', CAST(COUNT(*) AS VARCHAR(64)) FROM ranked_top10 WHERE current_rank <= 10
)
SELECT
    'grade' AS row_type,
    grade,
    (SELECT latest_snapshot_date FROM bounds) AS snapshot_date,
    (SELECT baseline_snapshot_date FROM bounds) AS window_start_exclusive,
    (SELECT latest_snapshot_date FROM bounds) AS window_end_inclusive,
    current_employee_count,
    current_distribution_percent,
    promotion_participant_count,
    promoted_employee_count,
    promotion_rate_percent,
    average_monthly_headcount,
    voluntary_exit_count,
    attrition_rate_percent,
    current_rank,
    CAST(NULL AS VARCHAR(128)) AS diagnostic_metric,
    CAST(NULL AS VARCHAR(64)) AS diagnostic_value
FROM ranked_top10
WHERE current_rank <= 10
UNION ALL
SELECT
    'diagnostic', CAST(NULL AS VARCHAR(80)), CAST(NULL AS DATE), CAST(NULL AS DATE), CAST(NULL AS DATE),
    CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)), CAST(NULL AS DECIMAL(18,6)), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)),
    CAST(NULL AS BIGINT), metric, metric_value
FROM diagnostics
ORDER BY row_type DESC, current_rank, grade, diagnostic_metric;
